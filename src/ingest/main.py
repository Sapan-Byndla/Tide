import numpy as np
import json
import logging
import httpx
from fastapi import FastAPI, HTTPException, status
import asyncpg
from pgvector.asyncpg import register_vector
from src.config import config
from src.database import get_db_connection, init_db_pool, close_db_pool
from src.shared.models import PostIngestRequest
from src.shared.utils import setup_logging, cosine_similarity
from src.ingest.phrases import extract_phrases, record_phrase_observations
from src.ingest.pool import add_to_pending_pool, extract_distinctive_tokens

logger = setup_logging("tide.ingest")

app = FastAPI(
    title="Tide Ingestion Service",
    description="FastAPI ingestion pipeline that receives crawled posts, computes embeddings, links concepts, extracts phrases, and updates graph edges.",
    version="1.0"
)

@app.on_event("startup")
async def startup():
    logger.info("Starting ingest service and initializing DB pool...")
    await init_db_pool()
    # Register vector type for asyncpg
    async with get_db_connection() as conn:
        try:
            await register_vector(conn)
        except Exception as e:
            logger.warning(f"Could not register pgvector type with asyncpg: {e}. If extension is not yet initialized, run db_init.sql first.")

@app.on_event("shutdown")
async def shutdown():
    logger.info("Stopping ingest service...")
    await close_db_pool()

async def get_embedding_from_service(text: str) -> list[float]:
    """Calls the local embedding service to get a 768-dimension vector."""
    url = f"http://{config.embedding_host}:{config.embedding_port}/embed"
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.post(url, json={"texts": [text], "type": "document"})
            if resp.status_code != 200:
                raise HTTPException(status_code=500, detail=f"Embedding service error: {resp.text}")
            data = resp.json()
            return data["embeddings"][0]
        except Exception as e:
            logger.error(f"Failed to communicate with embedding service: {e}")
            raise HTTPException(status_code=503, detail="Embedding service unavailable")

@app.post("/ingest", status_code=status.HTTP_201_CREATED)
async def ingest_post(post_req: PostIngestRequest):
    logger.info(f"Received ingest request: {post_req.source} | {post_req.source_id}")
    
    async with get_db_connection() as conn:
        # 1. Check for duplicates
        duplicate = await conn.fetchval(
            "SELECT id FROM posts WHERE source = $1 AND source_id = $2",
            post_req.source, post_req.source_id
        )
        if duplicate:
            logger.info(f"Duplicate post ignored: {post_req.source}/{post_req.source_id}")
            return {"status": "ignored", "reason": "duplicate", "post_id": duplicate}

        # 2. Get embedding for the post (title + body)
        combined_text = f"{post_req.title}\n{post_req.body or ''}"
        embedding = await get_embedding_from_service(combined_text)

        # 3. Insert Post into Database
        async with conn.transaction():
            post_id = await conn.fetchval(
                """
                INSERT INTO posts (source, source_id, title, body, url, canonical_url, published_at, fetched_at, engagement, native_tags, embedding)
                VALUES ($1, $2, $3, $4, $5, $6, $7, NOW(), $8::jsonb, $9, $10)
                RETURNING id
                """,
                post_req.source, post_req.source_id, post_req.title, post_req.body,
                post_req.url, post_req.canonical_url, post_req.published_at,
                json.dumps(post_req.engagement), post_req.native_tags, embedding
            )
            
            # 4. Phrase extraction and observation logging
            phrases = extract_phrases(post_req.title, post_req.body or "")
            await record_phrase_observations(conn, post_id, post_req.source, phrases)

            # 5. Concept Linkage
            # Step A: Link by Embedding similarity
            # Fetch all active concepts (or top 100 closest, using vector <-> operator for cosine distance)
            # pgvector distance operator <=> is cosine distance (1 - cosine similarity)
            # So order by (embedding <=> $1) limit 10
            concept_rows = await conn.fetch(
                """
                SELECT id, canonical_label, embedding, post_count
                FROM concepts
                WHERE status = 'active'
                ORDER BY embedding <=> $1
                LIMIT 10
                """,
                embedding
            )

            linked_concept_ids = set()
            max_sim_found = 0.0
            sim_threshold = config.ingest_similarity_threshold

            matching_concepts = []
            for cr in concept_rows:
                concept_id = cr["id"]
                concept_emb = list(cr["embedding"])
                
                # Compute actual cosine similarity
                sim = cosine_similarity(embedding, concept_emb)
                if sim > max_sim_found:
                    max_sim_found = sim
                
                if sim >= sim_threshold:
                    matching_concepts.append({
                        "id": concept_id,
                        "embedding": concept_emb,
                        "similarity": sim
                    })

            # Sort matching concepts by ID ascending to prevent database deadlocks on concurrent updates!
            matching_concepts.sort(key=lambda x: x["id"])

            for mc in matching_concepts:
                concept_id = mc["id"]
                concept_emb = mc["embedding"]
                sim = mc["similarity"]
                linked_concept_ids.add(concept_id)
                
                # Create Link
                await conn.execute(
                    """
                    INSERT INTO post_concepts (post_id, concept_id, similarity, linked_at, link_source)
                    VALUES ($1, $2, $3, NOW(), 'embedding')
                    ON CONFLICT (post_id, concept_id) DO NOTHING
                    """,
                    post_id, concept_id, sim
                )

                # Update Centroid via EMA (Exponential Moving Average)
                # new_centroid = (1 - alpha) * old_centroid + alpha * post_embedding
                alpha = config.ema_alpha
                old_centroid = np.array(concept_emb)
                new_centroid = (1 - alpha) * old_centroid + alpha * np.array(embedding)
                
                # Renormalize to unit length
                norm = np.linalg.norm(new_centroid)
                if norm > 0:
                    new_centroid = new_centroid / norm
                new_centroid_list = new_centroid.tolist()

                await conn.execute(
                    """
                    UPDATE concepts
                    SET embedding = $1, post_count = post_count + 1, last_evidence_at = NOW()
                    WHERE id = $2
                    """,
                    new_centroid_list, concept_id
                )

            # Step B: Link by Native Tag match against aliases
            if post_req.native_tags:
                matched_rows = await conn.fetch(
                    """
                    SELECT id FROM concepts
                    WHERE status = 'active' AND aliases && $1
                    """,
                    post_req.native_tags
                )
                for mr in matched_rows:
                    concept_id = mr["id"]
                    if concept_id not in linked_concept_ids:
                        linked_concept_ids.add(concept_id)
                        await conn.execute(
                            """
                            INSERT INTO post_concepts (post_id, concept_id, similarity, linked_at, link_source)
                            VALUES ($1, $2, 1.0, NOW(), 'native_tag')
                            ON CONFLICT (post_id, concept_id) DO NOTHING
                            """,
                            post_id, concept_id
                        )
                        await conn.execute(
                            """
                            UPDATE concepts
                            SET post_count = post_count + 1, last_evidence_at = NOW()
                            WHERE id = $1
                            """,
                            concept_id
                        )

            # 6. Update Concept Edges (co-occurrence)
            # If the post linked to multiple concepts, create/increment undirected edges
            linked_ids_sorted = sorted(list(linked_concept_ids))
            for i in range(len(linked_ids_sorted)):
                for j in range(i + 1, len(linked_ids_sorted)):
                    concept_a = linked_ids_sorted[i]
                    concept_b = linked_ids_sorted[j]
                    
                    await conn.execute(
                        """
                        INSERT INTO concept_edges (concept_a, concept_b, co_count, first_seen_at, last_seen_at)
                        VALUES ($1, $2, 1, NOW(), NOW())
                        ON CONFLICT (concept_a, concept_b) DO UPDATE
                        SET co_count = concept_edges.co_count + 1, last_seen_at = EXCLUDED.last_seen_at
                        """,
                        concept_a, concept_b
                    )

            # 7. Add to Pending Pool if no concepts matched
            if not linked_concept_ids:
                distinctive_tokens = extract_distinctive_tokens(post_req.title, post_req.body)
                await add_to_pending_pool(conn, post_id, max_sim_found, distinctive_tokens)

        logger.info(f"Post {post_id} ingested. Linked to {len(linked_concept_ids)} concepts.")
        return {
            "status": "success",
            "post_id": post_id,
            "linked_concepts_count": len(linked_concept_ids),
            "linked_concepts": list(linked_concept_ids)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.ingest.main:app",
        host=config.ingest_host,
        port=config.ingest_port,
        reload=True
    )
