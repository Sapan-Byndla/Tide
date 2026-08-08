# Tide Development Backlog & Task Breakdown

This document breaks down the Tide implementation tasks into grounded, real, and actionable steps organized by the phases defined in the Project Blueprint.

---

## Phase v1: Concept Graph Core (Beachhead)

Goal: Stand up the core graph database, local embedding model, ingest pipeline, phrase tracking, background Leiden/UMAP layouts, and public read APIs.

### Part 1: Database Setup & Schema
- [x] Provision Supabase PostgreSQL instance (Postgres 16 + pgvector)
- [x] Write idempotent [db/db_init.sql](../db/db_init.sql) script
- [x] Run schema initialization and verify pgvector functions and HNSW indices
- [x] Configure local [.env](../.env) with connection details (kept out of Git)

### Part 2: Local Embedding Service (`src/embedding/`)
- [x] Install `sentence-transformers` and download `nomic-embed-text-v1.5`
- [x] Test local FastAPI server on `http://127.0.0.1:8001`
- [x] Verify query vs document prefixes ("search_query: " and "search_document: ")
- [x] Implement batching constraints (max 64 texts)
- [x] Run benchmark to verify latencies under 2s for a batch of 32 documents

### Part 3: Ingest Service & Concept Linking (`src/ingest/`)
- [ ] Set up curated seed list of 25 concepts in the database (owned by Project Lead)
- [ ] Verify `POST /ingest` endpoint handles incoming normalized post structures
- [ ] Retrieve embeddings, compute cosine distance, and link to active concepts (threshold >= 0.55)
- [ ] Implement Centroid Update via EMA (Exponential Moving Average, alpha = 0.05) and vector renormalization
- [ ] Implement Native-Tag alias linking
- [ ] Write co-occurrence edge updates to `concept_edges`

### Part 4: Phrase Extraction (`src/ingest/phrases.py`)
- [ ] Verify bigram/trigram tokenization from post titles and bodies
- [ ] Refine stopword list and add custom generic tech terms to `GENERIC_DENYLIST`
- [ ] Save extracted observations to `phrase_observations`

### Part 5: Pending Pool & Concept Creation (`src/ingest/pool.py`)
- [ ] Insert posts that fail to link above 0.55 into `pending_pool`
- [ ] Implement token frequency counters to extract "distinctive tokens" (tokens rare in the global corpus)
- [ ] Implement background clustering loop:
  - Construct similarity graphs of pending posts using `python-igraph`
  - Retrieve connected components (mutual similarity >= 0.55 sharing >= 1 distinctive token)
  - Create new concepts for components of size >= 3
  - Migrate linked posts out of pending pool and update edges

### Part 6: Daily Rollups (`src/jobs/daily_rollups.py`)
- [ ] Schedule `daily_rollups.py` via cron
- [ ] Verify idempotent counts for daily concept evidence (`concept_evidence_daily`)
- [ ] Verify daily edge growth rollup (`concept_edges_daily`)
- [ ] Verify daily phrase stats tracking (`phrase_stats_daily`)

### Part 7: Phrase Graduation (`src/jobs/phrase_graduation.py`)
- [ ] Analyze phrase frequencies to qualify watch list candidates:
  - Last 7 days count >= 5
  - Source count >= 2
  - Growth velocity > 3x compared to prior 7 days
- [ ] Graduate phrases to full concepts when count >= 10 and title appearances >= 3
- [ ] Evict watch list noise (phrases appearing in < 2 sources for 30 days)

### Part 8: Community Detection & Graph UMAP (`src/jobs/community_detection.py`)
- [ ] Implement weekly Leiden clustering partitioner using `leidenalg`
- [ ] Compute recency-decay edge weights: `co_count * exp(-0.02 * age_days)`
- [ ] Run Leiden to set concept `community_id` and flag `cross_community` edges
- [ ] Implement UMAP layout generation to project concepts into 2D coordinates
- [ ] Persist coordinates to `concept_layout` table

### Part 9: Read API (`src/read_api/`)
- [ ] Test the FastAPI Read endpoints:
  - `GET /trends/new`: recently created active concepts
  - `GET /trends/growing`: concepts where 7d activity is double prior 7d activity
  - `GET /trends/declining`: inactive concepts
  - `GET /trends/bridges`: cross-community active edges
  - `GET /watch/phrases`: current emerging phrase watchlist
  - `GET /concepts/{id}`: concept details, time series, and recent evidence posts
  - `GET /concepts/{id}/neighbors`: neighbors ordered by co-occurrence weight
  - `GET /search`: query embedding similarity search
  - `GET /observe`: structured text dump for direct consumption by an LLM prompt

### Part 10: Concept Maintenance (Late v1 / v2)
- [ ] Implement weekly merges for concepts with centroid similarity >= 0.85 sharing >= 30% of post evidence
- [ ] Implement weekly concept splits using sub-clustering (HDBSCAN)
- [ ] Implement concept lineage/ancestry mapping (`concepts.succeeds` array)

---

## Phase v2: Active Perception Layer

Goal: Enable the graph database to guide its own crawlers and host a continuous language model perception loop.

### Part 11: Goal-Directed Crawler
- [ ] Build feedback crawlers dispatched dynamically based on graph properties:
  - Regions of high uncertainty (high distance nodes)
  - Emerging watch phrases with low source diversity
  - Rapidly growing concept bridges
- [ ] Maintain an exploration budget (10-20%) for random crawls

### Part 12: LLM Perception Layer
- [ ] Implement continuous agentic loop query engine using `/observe`
- [ ] Build a persistent observer notebook (vector memory / markdown file) where the agent records hypotheses, alerts, and trend reports
- [ ] Expose an observation summary stream for external downstream consumption

### Part 13: Evaluation Harness & Benchmark
- [ ] Package a frozen 30-day crawled posts dataset
- [ ] Curate a retrospectively-labeled trend benchmark (using news feeds, GitHub, and major ecosystem reports)
- [ ] Implement metrics evaluation:
  - Recall @ K
  - Precision @ K
  - Time-to-detection
  - Concept fragmentation rate
- [ ] Implement ablation scripts to evaluate individual detection pathways (Embedding clustering vs Phrase tracking vs Native-tag aggregation)

---

## Phase v3: Generalization

Goal: Verify domain-portability of the TIDE perception architecture.

- [ ] Select a second target domain (e.g., Clinical Trials, Medical Ontologies, or Financial Markets)
- [ ] Re-configure scrapers for the new target domain
- [ ] Run end-to-end evaluations on the second domain using the Phase v2 harness
