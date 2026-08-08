import logging
from typing import List, Optional
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, HTTPException, Query, status
import asyncpg
import httpx
from src.config import config
from src.database import get_db_connection, init_db_pool, close_db_pool
from src.shared.utils import setup_logging

logger = setup_logging("tide.read_api")

app = FastAPI(
    title="Tide Read API",
    description="FastAPI service exposing trend, concept, neighborhood, search, and structured observation endpoints.",
    version="1.0"
)

@app.on_event("startup")
async def startup():
    logger.info("Starting Read API and database pool...")
    await init_db_pool()

@app.on_event("shutdown")
async def shutdown():
    logger.info("Stopping Read API...")
    await close_db_pool()

async def get_query_embedding(text: str) -> list[float]:
    """Helper to query the embedding service with type='query'."""
    url = f"http://{config.embedding_host}:{config.embedding_port}/embed"
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.post(url, json={"texts": [text], "type": "query"})
            if resp.status_code != 200:
                raise HTTPException(status_code=500, detail=f"Embedding service error: {resp.text}")
            return resp.json()["embeddings"][0]
        except Exception as e:
            logger.error(f"Failed to communicate with embedding service: {e}")
            raise HTTPException(status_code=503, detail="Embedding service unavailable")

@app.get("/trends/new")
async def get_new_trends(days: int = 14, limit: int = 20):
    """Concepts created recently with growing evidence."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    query = """
        SELECT id, canonical_label, aliases, status, created_at, post_count
        FROM concepts
        WHERE created_at >= $1 AND status = 'active'
        ORDER BY post_count DESC, created_at DESC
        LIMIT $2
    """
    async with get_db_connection() as conn:
        rows = await conn.fetch(query, cutoff, limit)
        return [dict(r) for r in rows]

@app.get("/trends/growing")
async def get_growing_trends(window: int = 7, limit: int = 20):
    """Concepts where post count in the last `window` days is at least double that of the prior `window` days."""
    cutoff_recent = datetime.now(timezone.utc) - timedelta(days=window)
    cutoff_prior = datetime.now(timezone.utc) - timedelta(days=window * 2)
    
    query = """
        WITH recent_stats AS (
            SELECT concept_id, SUM(post_count) as recent_count
            FROM concept_evidence_daily
            WHERE day >= $1::date
            GROUP BY concept_id
        ),
        prior_stats AS (
            SELECT concept_id, SUM(post_count) as prior_count
            FROM concept_evidence_daily
            WHERE day >= $2::date AND day < $1::date
            GROUP BY concept_id
        )
        SELECT c.id, c.canonical_label, c.post_count,
               COALESCE(r.recent_count, 0) as count_recent,
               COALESCE(p.prior_count, 0) as count_prior,
               CASE 
                 WHEN COALESCE(p.prior_count, 0) = 0 THEN COALESCE(r.recent_count, 0)::float
                 ELSE (COALESCE(r.recent_count, 0)::float / p.prior_count::float)
               END as growth_ratio
        FROM concepts c
        JOIN recent_stats r ON c.id = r.concept_id
        LEFT JOIN prior_stats p ON c.id = p.concept_id
        WHERE c.status = 'active' AND COALESCE(r.recent_count, 0) >= 5
          AND COALESCE(r.recent_count, 0) > 2 * COALESCE(p.prior_count, 0)
        ORDER BY growth_ratio DESC, c.post_count DESC
        LIMIT $3
    """
    async with get_db_connection() as conn:
        rows = await conn.fetch(query, cutoff_recent.date(), cutoff_prior.date(), limit)
        return [dict(r) for r in rows]

@app.get("/trends/declining")
async def get_declining_trends(window: int = 14, limit: int = 20):
    """Concepts trending down (recent activity substantially lower than prior activity)."""
    cutoff_recent = datetime.now(timezone.utc) - timedelta(days=window)
    cutoff_prior = datetime.now(timezone.utc) - timedelta(days=window * 2)
    
    query = """
        WITH recent_stats AS (
            SELECT concept_id, SUM(post_count) as recent_count
            FROM concept_evidence_daily
            WHERE day >= $1::date
            GROUP BY concept_id
        ),
        prior_stats AS (
            SELECT concept_id, SUM(post_count) as prior_count
            FROM concept_evidence_daily
            WHERE day >= $2::date AND day < $1::date
            GROUP BY concept_id
        )
        SELECT c.id, c.canonical_label, c.post_count,
               COALESCE(r.recent_count, 0) as count_recent,
               COALESCE(p.prior_count, 0) as count_prior
        FROM concepts c
        JOIN prior_stats p ON c.id = p.concept_id
        LEFT JOIN recent_stats r ON c.id = r.concept_id
        WHERE c.status = 'active' AND COALESCE(p.prior_count, 0) >= 5
          AND COALESCE(r.recent_count, 0) < 0.5 * COALESCE(p.prior_count, 0)
        ORDER BY count_prior DESC
        LIMIT $3
    """
    async with get_db_connection() as conn:
        rows = await conn.fetch(query, cutoff_recent.date(), cutoff_prior.date(), limit)
        return [dict(r) for r in rows]

@app.get("/trends/bridges")
async def get_bridge_edges(days: int = 30, limit: int = 20):
    """Edges that cross community boundaries recently."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    query = """
        SELECT ce.concept_a, ce.concept_b, ce.co_count, ce.pmi, ce.last_seen_at,
               c1.canonical_label as label_a, c1.community_id as community_a,
               c2.canonical_label as label_b, c2.community_id as community_b
        FROM concept_edges ce
        JOIN concepts c1 ON ce.concept_a = c1.id
        JOIN concepts c2 ON ce.concept_b = c2.id
        WHERE ce.cross_community = TRUE AND ce.last_seen_at >= $1
        ORDER BY ce.co_count DESC, ce.pmi DESC
        LIMIT $2
    """
    async with get_db_connection() as conn:
        rows = await conn.fetch(query, cutoff, limit)
        return [dict(r) for r in rows]

@app.get("/watch/phrases")
async def get_watch_phrases(limit: int = 50):
    """Retrieves current phrases under status='watching'."""
    query = """
        SELECT phrase, day, post_count, source_count, status
        FROM phrase_stats_daily
        WHERE status = 'watching'
        ORDER BY day DESC, post_count DESC
        LIMIT $1
    """
    async with get_db_connection() as conn:
        rows = await conn.fetch(query, limit)
        return [dict(r) for r in rows]

@app.get("/concepts/{concept_id}")
async def get_concept_details(concept_id: int):
    """Retrieves full details for a concept, including its recent posts."""
    async with get_db_connection() as conn:
        concept = await conn.fetchrow(
            "SELECT id, canonical_label, aliases, status, created_at, last_evidence_at, community_id, post_count FROM concepts WHERE id = $1",
            concept_id
        )
        if not concept:
            raise HTTPException(status_code=404, detail="Concept not found")
            
        time_series = await conn.fetch(
            "SELECT day, post_count, source_breakdown, avg_engagement FROM concept_evidence_daily WHERE concept_id = $1 ORDER BY day DESC LIMIT 30",
            concept_id
        )
        
        top_posts = await conn.fetch(
            """
            SELECT p.id, p.source, p.title, p.url, p.published_at, pc.similarity
            FROM post_concepts pc
            JOIN posts p ON pc.post_id = p.id
            WHERE pc.concept_id = $1
            ORDER BY pc.similarity DESC, p.published_at DESC
            LIMIT 10
            """,
            concept_id
        )
        
        return {
            "concept": dict(concept),
            "time_series": [dict(ts) for ts in time_series],
            "top_posts": [dict(tp) for tp in top_posts]
        }

@app.get("/concepts/{concept_id}/neighbors")
async def get_concept_neighbors(concept_id: int, limit: int = 20):
    """Retrieves graph neighbors of a concept ranked by edge weight co_count."""
    query = """
        SELECT ce.co_count, ce.pmi, ce.cross_community,
               CASE 
                 WHEN ce.concept_a = $1 THEN c_b.id
                 ELSE c_a.id
               END as neighbor_id,
               CASE 
                 WHEN ce.concept_a = $1 THEN c_b.canonical_label
                 ELSE c_a.canonical_label
               END as neighbor_label
        FROM concept_edges ce
        JOIN concepts c_a ON ce.concept_a = c_a.id
        JOIN concepts c_b ON ce.concept_b = c_b.id
        WHERE ce.concept_a = $1 OR ce.concept_b = $1
        ORDER BY ce.co_count DESC, ce.pmi DESC
        LIMIT $2
    """
    async with get_db_connection() as conn:
        rows = await conn.fetch(query, concept_id, limit)
        return [dict(r) for r in rows]

@app.get("/search")
async def search_concepts(q: str, limit: int = 10):
    """Semantic search returning concepts ranked by cosine similarity to query string."""
    query_vector = await get_query_embedding(q)
    
    # Ordering by <=> (cosine distance)
    query = """
        SELECT id, canonical_label, aliases, status, post_count,
               (1 - (embedding <=> $1)) as similarity
        FROM concepts
        WHERE status = 'active'
        ORDER BY embedding <=> $1
        LIMIT $2
    """
    async with get_db_connection() as conn:
        rows = await conn.fetch(query, query_vector, limit)
        return [dict(r) for r in rows]

@app.get("/observe")
async def observe_concept(concept_id: int, days: int = 30, depth: int = 1):
    """
    Structured observation block designed to be consumed directly by an LLM context window.
    Contains summary, time series, top posts, and community neighbors.
    """
    async with get_db_connection() as conn:
        concept = await conn.fetchrow(
            "SELECT id, canonical_label, aliases, community_id, post_count FROM concepts WHERE id = $1",
            concept_id
        )
        if not concept:
            raise HTTPException(status_code=404, detail="Concept not found")
            
        time_series_rows = await conn.fetch(
            "SELECT day, post_count FROM concept_evidence_daily WHERE concept_id = $1 AND day >= CURRENT_DATE - $2::int ORDER BY day ASC",
            concept_id, days
        )
        
        top_posts_rows = await conn.fetch(
            """
            SELECT p.title, p.source, p.url, p.published_at
            FROM post_concepts pc
            JOIN posts p ON pc.post_id = p.id
            WHERE pc.concept_id = $1
            ORDER BY pc.similarity DESC, p.published_at DESC
            LIMIT 5
            """,
            concept_id
        )
        
        neighbors_rows = await conn.fetch(
            """
            SELECT ce.co_count,
                   CASE WHEN ce.concept_a = $1 THEN c_b.canonical_label ELSE c_a.canonical_label END as neighbor_label,
                   CASE WHEN ce.concept_a = $1 THEN c_b.community_id ELSE c_a.community_id END as neighbor_community
            FROM concept_edges ce
            JOIN concepts c_a ON ce.concept_a = c_a.id
            JOIN concepts c_b ON ce.concept_b = c_b.id
            WHERE ce.concept_a = $1 OR ce.concept_b = $1
            ORDER BY ce.co_count DESC
            LIMIT 5
            """,
            concept_id
        )
        
        # Build structured text block
        lines = [
            f"=== CONCEPT OBSERVATION BLOCK: {concept['canonical_label'].upper()} ===",
            f"Concept ID: {concept['id']}",
            f"Aliases: {', '.join(concept['aliases'] or [])}",
            f"Community ID: {concept['community_id']}",
            f"Total Post Evidence Count: {concept['post_count']}",
            "\n--- Activity Log (Last 30 Days) ---"
        ]
        
        for ts in time_series_rows:
            lines.append(f"Date: {ts['day']} | Posts: {ts['post_count']}")
            
        lines.append("\n--- Top Evidence Posts ---")
        for p in top_posts_rows:
            lines.append(f"- [{p['source'].upper()}] {p['title']} ({p['published_at'].date()}) - URL: {p['url']}")
            
        lines.append("\n--- Primary Graph Neighbors ---")
        for n in neighbors_rows:
            lines.append(f"- Neighbor: {n['neighbor_label']} (Community: {n['neighbor_community']}) | Co-occurrence: {n['co_count']}")
            
        lines.append("=== END OF OBSERVATION BLOCK ===")
        
        return {
            "concept_id": concept_id,
            "canonical_label": concept["canonical_label"],
            "observation_block": "\n".join(lines)
        }
