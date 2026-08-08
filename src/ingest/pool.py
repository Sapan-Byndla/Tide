import logging
from datetime import datetime, timedelta, timezone
from typing import List, Set, Dict, Any, Tuple
import numpy as np
import asyncpg
from src.config import config
from src.shared.utils import tokenize, cosine_similarity
from src.shared.models import ConceptModel

logger = logging.getLogger("tide.ingest.pool")

def extract_distinctive_tokens(title: str, body: str) -> List[str]:
    """
    Extracts tokens from a post that are likely distinctive.
    In v1, we extract non-stopword tokens of length >= 4, excluding digits.
    """
    from src.ingest.phrases import STOPWORDS
    tokens = tokenize(f"{title} {body or ''}", min_length=4)
    distinctive = []
    for t in tokens:
        # Exclude digits and basic stopwords
        if not t.isdigit() and t not in STOPWORDS:
            distinctive.append(t)
    return list(set(distinctive))

async def add_to_pending_pool(conn: asyncpg.Connection, post_id: int, nearest_sim: float, distinctive_tokens: List[str]):
    """Inserts a post into the pending pool for future concept clustering."""
    logger.info(f"Adding post {post_id} to pending pool (nearest_sim: {nearest_sim:.4f})")
    query = """
        INSERT INTO pending_pool (post_id, added_at, nearest_sim, distinctive_tokens)
        VALUES ($1, NOW(), $2, $3)
        ON CONFLICT (post_id) DO UPDATE
        SET nearest_sim = EXCLUDED.nearest_sim, distinctive_tokens = EXCLUDED.distinctive_tokens
    """
    await conn.execute(query, post_id, nearest_sim, distinctive_tokens)

async def clean_expired_pending_pool(conn: asyncpg.Connection):
    """Evicts posts that have been in the pending pool longer than TTL."""
    ttl_days = config.pending_ttl_days
    cutoff = datetime.now(timezone.utc) - timedelta(days=ttl_days)
    logger.info(f"Evicting pending pool posts older than {ttl_days} days (cutoff: {cutoff.isoformat()})...")
    
    query = "DELETE FROM pending_pool WHERE added_at < $1"
    deleted = await conn.execute(query, cutoff)
    logger.info(f"Evicted posts from pending pool: {deleted}")

async def run_pending_pool_clustering(conn: asyncpg.Connection):
    """
    Background clustering job.
    Retrieves all pending pool posts, computes pairwise similarity,
    constructs a graph, detects connected components, and graduates components into new Concepts.
    """
    logger.info("Running pending pool clustering analysis...")
    
    # Clean expired first
    await clean_expired_pending_pool(conn)
    
    # 1. Fetch pending pool posts + their embeddings
    query = """
        SELECT p.id as post_id, p.title, p.body, p.embedding, pp.distinctive_tokens
        FROM pending_pool pp
        JOIN posts p ON pp.post_id = p.id
    """
    rows = await conn.fetch(query)
    if len(rows) < config.pending_min_component_size:
        logger.info(f"Insufficient posts in pending pool ({len(rows)}), skipping clustering.")
        return
        
    logger.info(f"Analyzing {len(rows)} pending posts...")
    
    # Parse records
    posts = []
    for r in rows:
        # Convert binary vector to python list
        vector_bytes = r["embedding"]
        # In asyncpg, vector(768) is mapped to float list by pgvector client if registered,
        # otherwise we handle it.
        embedding = list(vector_bytes) if isinstance(vector_bytes, (list, tuple)) else []
        posts.append({
            "post_id": r["post_id"],
            "title": r["title"],
            "body": r["body"],
            "embedding": embedding,
            "distinctive_tokens": set(r["distinctive_tokens"] or [])
        })

    # 2. Construct similarity graph
    import igraph as ig
    
    g = ig.Graph(directed=False)
    g.add_vertices(len(posts))
    
    # Add attributes
    for idx, p in enumerate(posts):
        g.vs[idx]["post_id"] = p["post_id"]
        g.vs[idx]["title"] = p["title"]
        g.vs[idx]["tokens"] = p["distinctive_tokens"]
        
    edges_to_add = []
    threshold = config.pending_similarity_threshold
    
    # Compute pairwise similarity
    for i in range(len(posts)):
        for j in range(i + 1, len(posts)):
            p1, p2 = posts[i], posts[j]
            # Check lexical overlap (at least 1 shared distinctive token)
            shared_tokens = p1["distinctive_tokens"].intersection(p2["distinctive_tokens"])
            if not shared_tokens:
                continue
                
            # Check semantic similarity
            sim = cosine_similarity(p1["embedding"], p2["embedding"])
            if sim >= threshold:
                edges_to_add.append((i, j))
                
    g.add_edges(edges_to_add)
    logger.info(f"Graph constructed with {len(posts)} nodes and {len(edges_to_add)} similarity edges.")
    
    # 3. Find connected components
    components = g.connected_components()
    new_concepts_created = 0
    
    for comp in components:
        if len(comp) < config.pending_min_component_size:
            continue
            
        # We found a graduation candidate!
        comp_posts = [posts[idx] for idx in comp]
        logger.info(f"Found clustering component of size {len(comp)}!")
        
        # Determine concept label, centroid, and aliases
        # A. Centroid (average embedding)
        embeddings = np.array([p["embedding"] for p in comp_posts])
        mean_embedding = np.mean(embeddings, axis=0)
        # Normalize
        norm = np.linalg.norm(mean_embedding)
        centroid = (mean_embedding / norm).tolist() if norm > 0 else mean_embedding.tolist()
        
        # B. Distinctive tokens / label
        all_tokens: Dict[str, int] = {}
        for p in comp_posts:
            for token in p["distinctive_tokens"]:
                all_tokens[token] = all_tokens.get(token, 0) + 1
                
        # Sort tokens by frequency
        sorted_tokens = sorted(all_tokens.items(), key=lambda x: x[1], reverse=True)
        top_token = sorted_tokens[0][0] if sorted_tokens else "unlabeled-concept"
        aliases = [t[0] for t in sorted_tokens[:5]]
        
        # Slugify label
        canonical_label = top_token.lower().replace(" ", "-").strip()
        
        # Check if concept already exists (to avoid duplicate slug)
        exists = await conn.fetchval("SELECT id FROM concepts WHERE canonical_label = $1", canonical_label)
        if exists:
            # Append a suffix or pick the next token
            canonical_label = f"{canonical_label}-{int(datetime.now().timestamp())}"
            
        logger.info(f"Graduating cluster into new Concept: '{canonical_label}'")
        
        # Create Concept
        async with conn.transaction():
            concept_id = await conn.fetchval(
                """
                INSERT INTO concepts (canonical_label, aliases, embedding, status, created_at, post_count)
                VALUES ($1, $2, $3, 'active', NOW(), $4)
                RETURNING id
                """,
                canonical_label, aliases, centroid, len(comp_posts)
            )
            
            # Link posts and remove from pending pool
            for p in comp_posts:
                post_id = p["post_id"]
                # Calculate similarity to centroid
                sim = cosine_similarity(p["embedding"], centroid)
                
                # Insert post_concept link
                await conn.execute(
                    """
                    INSERT INTO post_concepts (post_id, concept_id, similarity, linked_at, link_source)
                    VALUES ($1, $2, $3, NOW(), 'embedding')
                    ON CONFLICT (post_id, concept_id) DO NOTHING
                    """,
                    post_id, concept_id, sim
                )
                
                # Delete from pending pool
                await conn.execute("DELETE FROM pending_pool WHERE post_id = $1", post_id)
                
        new_concepts_created += 1
        
    logger.info(f"Completed pending pool clustering. Created {new_concepts_created} new concepts.")
