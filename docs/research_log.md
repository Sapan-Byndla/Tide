# Tide Research Log

This file records key decisions, model parameter tunings, threshold adjustments, and experimental results for the Tide Concept Graph and Trend Intelligence System.

## [2026-06-16] - Project Initialization & Scaffolding

### Context
Initializing version 1.0 of the Tide project. The design uses Python as the implementation language and focuses on version 1 core requirements.

### Decisions
1. **Database Backend**: Selected **Supabase Postgres** instead of a local Postgres container to leverage hosting, ease of scale, and integration capabilities while preserving `pgvector` usage.
2. **Directory Layout**: Organized a modular project containing three FastAPI services (`embedding`, `ingest`, `read_api`), dynamic scrapers (`scrapers/`), background jobs (`jobs/`), and shared models/utilities (`shared/`).
3. **Configuration**: Created `config.yaml` to hold all system parameters (Operating Principle 8.2).

### Initial Configuration Parameters
- **Embedding similarity threshold**: `0.55` (Part 3 Ingest linking, Part 5 Pending Pool clustering).
- **EMA alpha**: `0.05` for concept centroid adjustment.
- **Min component size**: `3` posts with a shared distinctive token to form a concept.
- **Pending Pool TTL**: `14` days.
- **Edge recency decay lambda**: `0.02` per day for weekly Leiden weights.
- **Phrase watch thresholds**: `count_last_7d >= 5`, `source_count >= 2`, and `7d count > 3 * prior 7d count`.
- **Phrase graduation thresholds**: `count_last_7d >= 10` and at least `3` posts containing the phrase in the title.
- **Noise threshold**: Phrase appearing in `< 2` sources for `30` days.
- **Concept merge threshold**: Centroid similarity `>= 0.85` and sharing `>= 30%` of last 30 days post ids.
