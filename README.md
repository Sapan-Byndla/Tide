# TIDE: Concept Graph and Trend Intelligence System

Tide is an active perception system that continuously watches a domain of discourse, builds a persistent concept graph of the domain, and exposes this graph to language models as a structured perceptual substrate.

This is **Version 1.0 (Beachhead)** targeting the global technical ecosystem (AI, LLMs, infrastructure, and adjacent developer tools).

## Project Structure

- `src/scrapers/`: Modular crawling clients fetching from GitHub, arXiv, Hacker News, StackOverflow, and NewsAPI.
- `src/embedding/`: Local FastAPI embedding service running `nomic-embed-text-v1.5` on CPU.
- `src/ingest/`: Pipeline service executing semantic linking, phrase extraction, co-occurrence edge creation, and pending pool component clustering.
- `src/read_api/`: FastAPI server delivering trend metrics, semantic concept searches, and LLM structured observation blocks.
- `src/jobs/`: Daily rollups, phrase watch evaluations, and weekly Leiden community modularity/UMAP calculations.
- `db/db_init.sql`: Idempotent database schema definitions for Supabase Postgres + `pgvector`.
- `docs/tasks_by_phases.md`: Actionable task backlog tracking Phase v1, v2, and v3 development.

## Setup Instructions

1. **Database Schema**: Setup your Supabase Postgres database (ensure `pgvector` is available) and run `db/db_init.sql`.
2. **Environment Variable Configuration**: Create a `.env` file in the project root:
   ```env
   TIDE_DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT-ID].supabase.co:5432/postgres
   ```
3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Run Backend Services**:
   Start the services:
   ```bash
   python src/embedding/main.py
   python src/ingest/main.py
   python src/read_api/main.py
   ```
