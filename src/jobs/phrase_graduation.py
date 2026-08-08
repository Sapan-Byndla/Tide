import sys
import logging
from datetime import datetime, timedelta
import numpy as np
from src.config import config
from src.database import get_sync_cursor, get_sync_connection
from src.shared.utils import setup_logging, cosine_similarity

logger = setup_logging("tide.jobs.phrase_graduation")

def run_phrase_graduation():
    logger.info("Starting phrase graduation and watch list evaluation job...")
    
    # Dates setup
    today = datetime.now().date()
    seven_days_ago = today - timedelta(days=7)
    fourteen_days_ago = today - timedelta(days=14)
    thirty_days_ago = today - timedelta(days=30)
    
    with get_sync_connection() as conn:
        with conn.cursor() as cur:
            # 1. First, mark older inactive low-source phrases as noise
            logger.info("Filtering noisy phrases...")
            cur.execute(
                """
                UPDATE phrase_stats_daily
                SET status = 'noise'
                WHERE status = 'watching' 
                  AND day <= %s 
                  AND source_count < %s
                """,
                (thirty_days_ago, config.phrase_grad_min_source_count)
            )
            logger.info(f"Marked {cur.rowcount} low-source phrases as noise.")

            # 2. Query candidates under status 'watching' in the last 7 days
            logger.info("Analyzing potential watch and graduation candidates...")
            cur.execute(
                """
                SELECT 
                    phrase,
                    SUM(post_count) as total_posts_7d,
                    SUM(source_count) as total_sources_7d,
                    array_agg(DISTINCT co_concept_ids) as nested_concepts
                FROM phrase_stats_daily
                WHERE status = 'watching' AND day >= %s
                GROUP BY phrase
                """,
                (seven_days_ago,)
            )
            recent_phrases = cur.fetchall()
            
            # For each phrase, we need to compare its frequency in the last 7 days vs prior 7 days (prior_7d)
            for row in recent_phrases:
                phrase = row[0]
                count_last_7d = row[1]
                sources_7d = row[2]
                
                # Flatten nested array of arrays
                flat_concepts = set()
                for arr in row[3]:
                    if arr:
                        flat_concepts.update(arr)
                
                # Fetch count from the prior 7 days (from day -14 to day -7)
                cur.execute(
                    """
                    SELECT COALESCE(SUM(post_count), 0)
                    FROM phrase_stats_daily
                    WHERE phrase = %s AND day >= %s AND day < %s
                    """,
                    (phrase, fourteen_days_ago, seven_days_ago)
                )
                count_prior_7d = cur.fetchone()[0]
                
                # Calculate velocity
                velocity_multiplier = config.phrase_grad_velocity_multiplier
                meets_watch_criteria = (
                    count_last_7d >= config.phrase_grad_min_count_7d and
                    sources_7d >= config.phrase_grad_min_source_count and
                    (count_prior_7d == 0 or count_last_7d > velocity_multiplier * count_prior_7d)
                )
                
                if not meets_watch_criteria:
                    continue
                    
                # We meet watch criteria. Now check if we can graduate it to a concept.
                # Graduation requirements: total count >= 10 and appears in title of >= 3 posts.
                # Let's count how many posts with this phrase in the last 7 days have it in the title.
                cur.execute(
                    """
                    SELECT COUNT(p.id)
                    FROM phrase_observations po
                    JOIN posts p ON po.post_id = p.id
                    WHERE po.phrase = %s 
                      AND po.observed_at >= %s
                      AND p.title ILIKE %s
                    """,
                    (phrase, seven_days_ago, f"%{phrase}%")
                )
                title_appearances = cur.fetchone()[0]
                
                meets_grad_criteria = (
                    count_last_7d >= config.phrase_grad_graduate_count_7d and
                    title_appearances >= config.phrase_grad_min_title_appearances
                )
                
                if meets_grad_criteria:
                    logger.info(f"Phrase '{phrase}' matches GRADUATION requirements (Count: {count_last_7d}, Title count: {title_appearances}).")
                    graduate_phrase_to_concept(conn, phrase, seven_days_ago)
                else:
                    logger.info(f"Phrase '{phrase}' qualified as WATCH signal (Count: {count_last_7d}, Prior count: {count_prior_7d}).")
                    # Update status to 'watching' across stats rows for this phrase
                    # (In v1, status 'watching' is default, but we can log or record it)

def graduate_phrase_to_concept(conn, phrase: str, since_date):
    """Graduates a phrase into a new Concept by aggregating posts that contain it."""
    with conn.cursor() as cur:
        # 1. Fetch posts and embeddings that have this phrase
        cur.execute(
            """
            SELECT p.id, p.embedding
            FROM phrase_observations po
            JOIN posts p ON po.post_id = p.id
            WHERE po.phrase = %s AND po.observed_at >= %s
            """,
            (phrase, since_date)
        )
        post_rows = cur.fetchall()
        if not post_rows:
            return
            
        post_ids = [r[0] for r in post_rows]
        embeddings = [list(r[1]) for r in post_rows if r[1] is not None]
        
        if len(embeddings) < 3:
            logger.warning(f"Insufficient embeddings ({len(embeddings)}) to graduate '{phrase}', skipping.")
            return

        # 2. Compute Centroid
        mean_emb = np.mean(np.array(embeddings), axis=0)
        norm = np.linalg.norm(mean_emb)
        centroid = (mean_emb / norm).tolist() if norm > 0 else mean_emb.tolist()
        
        # 3. Create Concept Slug
        canonical_label = phrase.lower().replace(" ", "-").strip()
        
        # 4. Insert Concept
        logger.info(f"Saving graduated concept '{canonical_label}'...")
        cur.execute(
            """
            INSERT INTO concepts (canonical_label, aliases, embedding, status, created_at, post_count)
            VALUES (%s, %s, %s, 'active', NOW(), %s)
            ON CONFLICT (canonical_label) DO NOTHING
            RETURNING id
            """,
            (canonical_label, [phrase], centroid, len(post_ids))
        )
        result = cur.fetchone()
        if not result:
            logger.warning(f"Concept '{canonical_label}' already exists.")
            return
        concept_id = result[0]
        
        # 5. Link posts to the new Concept
        for idx, post_id in enumerate(post_ids):
            # Fetch similarity
            sim = cosine_similarity(embeddings[idx], centroid) if idx < len(embeddings) else 1.0
            cur.execute(
                """
                INSERT INTO post_concepts (post_id, concept_id, similarity, linked_at, link_source)
                VALUES (%s, %s, %s, NOW(), 'phrase')
                ON CONFLICT (post_id, concept_id) DO NOTHING
                """,
                (post_id, concept_id, sim)
            )
            
        # 6. Update phrase stats daily status to 'graduated'
        cur.execute(
            """
            UPDATE phrase_stats_daily
            SET status = 'graduated'
            WHERE phrase = %s
            """,
            (phrase,)
        )
        
        logger.info(f"Successfully graduated phrase '{phrase}' to concept ID {concept_id}.")

if __name__ == "__main__":
    try:
        run_phrase_graduation()
    except Exception as e:
        logger.error(f"Job failed: {e}")
        sys.exit(1)
