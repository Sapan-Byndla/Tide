import sys
import argparse
import logging
from datetime import datetime, timedelta, date
import json
from src.database import get_sync_cursor
from src.shared.utils import setup_logging

logger = setup_logging("tide.jobs.daily_rollups")

def run_rollups(target_date: date):
    logger.info(f"Running daily rollups for date: {target_date}...")
    
    # Format dates for SQL queries
    day_str = target_date.strftime("%Y-%m-%d")
    next_day_str = (target_date + timedelta(days=1)).strftime("%Y-%m-%d")
    
    with get_sync_cursor() as cur:
        # --- 1. Concept Evidence Daily Rollup ---
        logger.info("Computing concept evidence daily rollup...")
        # Clear existing data for idempotency
        cur.execute(
            "DELETE FROM concept_evidence_daily WHERE day = %s",
            (target_date,)
        )
        
        # Aggregate evidence
        cur.execute(
            """
            INSERT INTO concept_evidence_daily (concept_id, day, post_count, source_breakdown, avg_engagement)
            SELECT 
                pc.concept_id,
                %s::date as day,
                COUNT(DISTINCT pc.post_id) as post_count,
                jsonb_object_agg(COALESCE(p.source, 'unknown'), sub.src_count) as source_breakdown,
                COALESCE(AVG(COALESCE((p.engagement->>'raw_engagement')::real, 0.0)), 0.0) as avg_engagement
            FROM post_concepts pc
            JOIN posts p ON pc.post_id = p.id
            JOIN (
                # Subquery to count posts per source and concept for the day
                SELECT pc2.concept_id, p2.source, COUNT(p2.id) as src_count
                FROM post_concepts pc2
                JOIN posts p2 ON pc2.post_id = p2.id
                WHERE p2.published_at >= %s::timestamptz AND p2.published_at < %s::timestamptz
                GROUP BY pc2.concept_id, p2.source
            ) sub ON pc.concept_id = sub.concept_id AND p.source = sub.source
            WHERE p.published_at >= %s::timestamptz AND p.published_at < %s::timestamptz
            GROUP BY pc.concept_id
            """,
            (day_str, day_str, next_day_str, day_str, next_day_str)
        )
        logger.info(f"Concept evidence rollup completed. Rows inserted: {cur.rowcount}")

        # --- 2. Concept Edges Daily Rollup ---
        logger.info("Computing concept edges daily rollup...")
        cur.execute(
            "DELETE FROM concept_edges_daily WHERE day = %s",
            (target_date,)
        )
        
        cur.execute(
            """
            INSERT INTO concept_edges_daily (concept_a, concept_b, day, new_co_count)
            SELECT 
                LEAST(pc1.concept_id, pc2.concept_id) as concept_a,
                GREATEST(pc1.concept_id, pc2.concept_id) as concept_b,
                %s::date as day,
                COUNT(DISTINCT pc1.post_id) as new_co_count
            FROM post_concepts pc1
            JOIN post_concepts pc2 ON pc1.post_id = pc2.post_id AND pc1.concept_id < pc2.concept_id
            JOIN posts p ON pc1.post_id = p.id
            WHERE p.published_at >= %s::timestamptz AND p.published_at < %s::timestamptz
            GROUP BY LEAST(pc1.concept_id, pc2.concept_id), GREATEST(pc1.concept_id, pc2.concept_id)
            """,
            (day_str, day_str, next_day_str)
        )
        logger.info(f"Concept edges daily rollup completed. Rows inserted: {cur.rowcount}")

        # --- 3. Phrase Stats Daily Rollup ---
        logger.info("Computing phrase stats daily rollup...")
        cur.execute(
            "DELETE FROM phrase_stats_daily WHERE day = %s",
            (target_date,)
        )
        
        cur.execute(
            """
            INSERT INTO phrase_stats_daily (phrase, day, post_count, source_count, co_concept_ids, status)
            SELECT 
                po.phrase,
                %s::date as day,
                COUNT(DISTINCT po.post_id) as post_count,
                COUNT(DISTINCT po.source) as source_count,
                COALESCE(array_agg(DISTINCT pc.concept_id) FILTER (WHERE pc.concept_id IS NOT NULL), '{}'::bigint[]) as co_concept_ids,
                'watching' as status
            FROM phrase_observations po
            LEFT JOIN post_concepts pc ON po.post_id = pc.post_id
            WHERE po.observed_at >= %s::timestamptz AND po.observed_at < %s::timestamptz
            GROUP BY po.phrase
            """,
            (day_str, day_str, next_day_str)
        )
        logger.info(f"Phrase stats daily rollup completed. Rows inserted: {cur.rowcount}")
        
    logger.info(f"Daily rollups run successfully for {day_str}.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tide daily rollups aggregator job")
    parser.add_argument(
        "--date", 
        type=str, 
        help="Date to aggregate in YYYY-MM-DD format (defaults to yesterday)"
    )
    args = parser.parse_args()
    
    if args.date:
        target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
    else:
        target_date = (datetime.now() - timedelta(days=1)).date()
        
    try:
        run_rollups(target_date)
    except Exception as e:
        logger.error(f"Job failed: {e}")
        sys.exit(1)
