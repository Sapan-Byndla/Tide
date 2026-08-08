import sys
import os
import time
import requests
from datetime import datetime, timezone
import numpy as np

# Adjust path to import from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database import get_sync_connection
from src.shared.utils import cosine_similarity

def get_concept_data(canonical_label):
    with get_sync_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, canonical_label, post_count, embedding FROM concepts WHERE canonical_label = %s",
                (canonical_label,)
            )
            res = cur.fetchone()
            if res:
                return {
                    "id": res[0],
                    "canonical_label": res[1],
                    "post_count": res[2],
                    "embedding": res[3]
                }
            return None

def get_post_concept_links(post_id):
    with get_sync_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT concept_id, similarity, link_source FROM post_concepts WHERE post_id = %s",
                (post_id,)
            )
            return cur.fetchall()

def get_edge(concept_a, concept_b):
    c1, c2 = sorted([concept_a, concept_b])
    with get_sync_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT co_count FROM concept_edges WHERE concept_a = %s AND concept_b = %s",
                (c1, c2)
            )
            res = cur.fetchone()
            return res[0] if res else 0

def test_pipeline():
    print("Starting pipeline ingestion tests...")
    
    # 1. Fetch baseline data for Postgresql and Supabase
    pg_baseline = get_concept_data("postgresql")
    sb_baseline = get_concept_data("supabase")
    
    if not pg_baseline:
        print("Error: Could not find 'postgresql' seed concept. Run bootstrap_seeds.py first.")
        return
    if not sb_baseline:
        print("Error: Could not find 'supabase' seed concept. Run bootstrap_seeds.py first.")
        return
        
    print(f"PostgreSQL baseline post_count: {pg_baseline['post_count']}")
    print(f"Supabase baseline post_count: {sb_baseline['post_count']}")
    
    # 2. Ingest first post (designed to match postgresql)
    ingest_url = "http://127.0.0.1:8002/ingest"
    timestamp = datetime.now(timezone.utc).isoformat()
    unique_id = f"test_post_{int(time.time())}_1"
    
    post_payload_1 = {
        "source": "test_verification",
        "source_id": unique_id,
        "title": "Configuring PostgreSQL Database Pools for Python Web Services",
        "body": "This article discusses the details of managing connection pools for a PostgreSQL database, including adjusting the max pool size, timeout values, and using asyncpg for asynchronous operations in production setups.",
        "url": "https://example.com/test-post-1",
        "canonical_url": "https://example.com/test-post-1",
        "published_at": timestamp,
        "engagement": {"views": 100, "likes": 10},
        "native_tags": ["postgresql", "database"]
    }
    
    print(f"Sending Post 1 to /ingest (source_id: {unique_id})...")
    resp1 = requests.post(ingest_url, json=post_payload_1)
    print(f"Response: {resp1.status_code} | {resp1.text}")
    assert resp1.status_code == 201, "Expected 201 Created"
    
    resp_data_1 = resp1.json()
    assert resp_data_1["status"] == "success"
    post_id_1 = resp_data_1["post_id"]
    
    # Wait a moment for async DB operations to complete
    time.sleep(1)
    
    # 3. Verify concept matching and EMA updates
    pg_after = get_concept_data("postgresql")
    print(f"PostgreSQL post_count after ingest: {pg_after['post_count']}")
    assert pg_after["post_count"] == pg_baseline["post_count"] + 1, "Expected postgresql post_count to increment by 1"
    
    # Verify centroid updated via EMA
    # Extract floats from the pgvector structure or parse string
    # asyncpg and psycopg2 might return list of floats directly, or pgvector type
    # If it is a string representation (e.g. '[0.1, 0.2,...]'), we parse it
    def parse_emb(emb):
        if isinstance(emb, str):
            return [float(x) for x in emb.strip('[]').split(',')]
        return list(emb)
        
    baseline_emb = parse_emb(pg_baseline["embedding"])
    after_emb = parse_emb(pg_after["embedding"])
    emb_similarity = cosine_similarity(baseline_emb, after_emb)
    print(f"Cosine similarity between baseline and updated PostgreSQL centroid: {emb_similarity:.6f}")
    assert emb_similarity < 0.999999, "Expected updated centroid embedding to differ from baseline (EMA update)"
    assert emb_similarity > 0.9, "Expected updated centroid embedding to still be highly similar to baseline"
    
    # Verify post concept links
    links_1 = get_post_concept_links(post_id_1)
    print(f"Post 1 linked concepts: {links_1}")
    assert len(links_1) > 0, "Expected at least one link"
    
    # 4. Ingest second post targeting both postgresql and supabase to test co-occurrence edge
    unique_id_2 = f"test_post_{int(time.time())}_2"
    post_payload_2 = {
        "source": "test_verification",
        "source_id": unique_id_2,
        "title": "Migrating Supabase Backend with Custom PostgreSQL Triggers",
        "body": "A guide on using Supabase's hosted PostgreSQL database with complex functions, triggers, and configuring them securely using migrations.",
        "url": "https://example.com/test-post-2",
        "canonical_url": "https://example.com/test-post-2",
        "published_at": timestamp,
        "engagement": {"views": 150, "likes": 25},
        "native_tags": ["postgresql", "supabase"]
    }
    
    # Get initial edge count
    edge_baseline = get_edge(pg_baseline["id"], sb_baseline["id"])
    print(f"Co-occurrence edge count baseline: {edge_baseline}")
    
    print(f"Sending Post 2 to /ingest (source_id: {unique_id_2})...")
    resp2 = requests.post(ingest_url, json=post_payload_2)
    print(f"Response: {resp2.status_code} | {resp2.text}")
    assert resp2.status_code == 201, "Expected 201 Created"
    
    time.sleep(1)
    
    # Verify edge incremented
    edge_after = get_edge(pg_baseline["id"], sb_baseline["id"])
    print(f"Co-occurrence edge count after Post 2: {edge_after}")
    assert edge_after == edge_baseline + 1, f"Expected co-occurrence count to increment by 1, went from {edge_baseline} to {edge_after}"
    
    print("\nALL PIPELINE INGESTION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    try:
        test_pipeline()
    except AssertionError as e:
        print(f"Assertion failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Test crashed with error: {e}")
        sys.exit(1)
