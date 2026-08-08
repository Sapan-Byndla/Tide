import sys
import logging
import math
from datetime import datetime, timezone
import numpy as np
import igraph as ig
import leidenalg as la
import umap
from src.config import config
from src.database import get_sync_connection, get_sync_cursor
from src.shared.utils import setup_logging

logger = setup_logging("tide.jobs.community_detection")

def run_community_detection():
    logger.info("Starting weekly community detection (Leiden) and layout (UMAP) job...")
    
    with get_sync_connection() as conn:
        # 1. Fetch active concepts and their embeddings
        with conn.cursor() as cur:
            cur.execute("SELECT id, embedding FROM concepts WHERE status = 'active'")
            concepts = cur.fetchall()
            
            if not concepts:
                logger.warning("No concepts found in database. Skipping.")
                return
                
            concept_ids = [c[0] for c in concepts]
            embeddings = [list(c[1]) for c in concepts]
            
            id_to_index = {c_id: idx for idx, c_id in enumerate(concept_ids)}

            # 2. Fetch edges with co_count >= min_edge_co_count
            min_co = config.community_min_edge_co_count
            cur.execute(
                """
                SELECT concept_a, concept_b, co_count, last_seen_at
                FROM concept_edges
                WHERE co_count >= %s
                """,
                (min_co,)
            )
            edges = cur.fetchall()

        if not edges:
            logger.warning("No qualifying edges found. Skipping community detection.")
            return

        logger.info(f"Loaded {len(concepts)} concepts and {len(edges)} edges.")

        # 3. Construct igraph representation
        g = ig.Graph(directed=False)
        g.add_vertices(len(concepts))
        
        # Add attributes
        for idx, c_id in enumerate(concept_ids):
            g.vs[idx]["db_id"] = c_id
            
        edge_list = []
        edge_weights = []
        now = datetime.now(timezone.utc)
        decay_lambda = config.community_recency_decay_lambda
        
        for c_a, c_b, co_count, last_seen_at in edges:
            if c_a not in id_to_index or c_b not in id_to_index:
                continue
            idx_a = id_to_index[c_a]
            idx_b = id_to_index[c_b]
            
            # Recency factor exp(-lambda * age_days)
            age_days = (now - last_seen_at).days
            recency_factor = math.exp(-decay_lambda * max(0, age_days))
            weight = co_count * recency_factor
            
            edge_list.append((idx_a, idx_b))
            edge_weights.append(weight)

        g.add_edges(edge_list)
        g.es["weight"] = edge_weights
        
        # 4. Run Leiden Community Detection
        logger.info("Executing Leiden community detection algorithm...")
        # Use Significance or Modularity Vertex Partition
        partition = la.find_partition(g, la.ModularityVertexPartition, weights=g.es["weight"])
        
        logger.info(f"Leiden detection completed. Found {len(partition)} communities.")

        # Update concept community assignments
        community_assignments = {}
        for community_idx, nodes in enumerate(partition):
            for node_idx in nodes:
                db_id = g.vs[node_idx]["db_id"]
                community_assignments[db_id] = community_idx

        # 5. Run UMAP for layout coordinates
        # Ensure we have enough concepts to run UMAP (typically requires n_neighbors < count)
        logger.info("Running UMAP dimensionality reduction for 2D layout...")
        layout_coordinates = {}
        
        if len(embeddings) >= 5:
            emb_matrix = np.array(embeddings)
            # Configure UMAP parameters (2 dimensions)
            reducer = umap.UMAP(
                n_neighbors=min(15, len(embeddings) - 1),
                min_dist=0.1,
                n_components=2,
                random_state=42
            )
            coords = reducer.fit_transform(emb_matrix)
            for idx, c_id in enumerate(concept_ids):
                layout_coordinates[c_id] = (float(coords[idx][0]), float(coords[idx][1]))
        else:
            logger.info("Too few concepts to run UMAP. Assigning dummy coordinates.")
            for idx, c_id in enumerate(concept_ids):
                layout_coordinates[c_id] = (float(idx), float(idx))

        # 6. Save results to the database
        logger.info("Updating database with communities and layouts...")
        with conn.cursor() as cur:
            # We will save layout coordinates directly into a concept layout table,
            # or dynamically add columns, or just write them to a concept_layout table.
            # Let's create the concept_layout table if it does not exist
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS concept_layout (
                    concept_id BIGINT PRIMARY KEY REFERENCES concepts(id) ON DELETE CASCADE,
                    x REAL NOT NULL,
                    y REAL NOT NULL,
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                )
                """
            )
            
            for c_id in concept_ids:
                comm_id = community_assignments.get(c_id, -1)
                x, y = layout_coordinates.get(c_id, (0.0, 0.0))
                
                # Update concepts table community_id and community_version
                cur.execute(
                    """
                    UPDATE concepts
                    SET community_id = %s, community_version = community_version + 1
                    WHERE id = %s
                    """,
                    (comm_id, c_id)
                )
                
                # Insert/Update coordinates
                cur.execute(
                    """
                    INSERT INTO concept_layout (concept_id, x, y, updated_at)
                    VALUES (%s, %s, %s, NOW())
                    ON CONFLICT (concept_id) DO UPDATE
                    SET x = EXCLUDED.x, y = EXCLUDED.y, updated_at = EXCLUDED.updated_at
                    """,
                    (c_id, x, y)
                )

            # 7. Update cross-community flags on edges
            # For each edge, if the endpoints belong to different communities, cross_community = TRUE
            logger.info("Flagging cross-community edges...")
            cur.execute("UPDATE concept_edges SET cross_community = FALSE")
            
            # Fetch all edges and verify communities
            cur.execute(
                """
                SELECT ce.concept_a, ce.concept_b, c1.community_id, c2.community_id
                FROM concept_edges ce
                JOIN concepts c1 ON ce.concept_a = c1.id
                JOIN concepts c2 ON ce.concept_b = c2.id
                """
            )
            edges_to_update = cur.fetchall()
            
            cross_edges = []
            for c_a, c_b, comm_a, comm_b in edges_to_update:
                if comm_a is not None and comm_b is not None and comm_a != comm_b:
                    cross_edges.append((c_a, c_b))
                    
            if cross_edges:
                cur.executemany(
                    """
                    UPDATE concept_edges
                    SET cross_community = TRUE
                    WHERE concept_a = %s AND concept_b = %s
                    """,
                    cross_edges
                )
            
            conn.commit()
            logger.info(f"Database updates complete. Flagged {len(cross_edges)} cross-community edges.")

if __name__ == "__main__":
    try:
        run_community_detection()
    except Exception as e:
        logger.error(f"Job failed: {e}")
        sys.exit(1)
