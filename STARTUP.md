# Tide v1 Services Startup Guide

This document explains how to set up, run, and test the Tide Concept Graph and Trend Intelligence pipeline.

---

## 1. Quick Start Orchestrator

We have created an interactive orchestrator script [run_pipeline.py](file:///d:/Work/Delpat/projects/Tide/run_pipeline.py) in the root directory that starts both services, verifies they are ready, seeds the database, and offers to run tests or ingest live data.

To start everything automatically, open a terminal in the root directory and run:

```bash
python run_pipeline.py
```

### What the script does:
1. **Starts the Embedding Service** on port `8001` and monitors the logs until the `nomic-embed-text-v1.5` model is ready.
2. **Starts the Ingest Service** on port `8002` and waits for it to initialize the database pool.
3. **Seeds the Database** automatically using [bootstrap_seeds.py](file:///d:/Work/Delpat/projects/Tide/src/jobs/bootstrap_seeds.py).
4. **Presents an Interactive Menu**:
   - **Option 1**: Run the integration tests (`tests/test_ingest.py`) to verify post mapping, EMA centroid updates, and co-occurrence edges.
   - **Option 2**: Run live scrapers (`arxiv`, `hackernews`, `github`, `stackoverflow`) to crawl and ingest real-time data into the Supabase database.
   - **Option 3**: Run scraper unit tests (`tests/test_scrapers.py`) to verify external API fetch and normalization logic.
   - **Option 4**: Leave the services running in the background.

---

## 2. Manual Startup Method

If you prefer to run services manually in separate terminals:

### Step A: Start Embedding Service
```bash
python -m src.embedding.main
```
*Port:* `8001`  
*Logs should end with:* `Application startup complete.`

### Step B: Start Ingest Service
```bash
python -m src.ingest.main
```
*Port:* `8002`  
*Logs should end with:* `Application startup complete.`

### Step C: Seed the Database
```bash
python -m src.jobs.bootstrap_seeds
```

---

## 3. Ingesting Actual Live Data

To manually trigger a live crawl and ingest real data into the running services:

```bash
python -c "import asyncio; from src.scrapers import run_all_scrapers; asyncio.run(run_all_scrapers())"
```

This will run all enabled scrapers concurrently. The scrapers will fetch posts from their respective APIs, normalize them into `PostIngestRequest` models, and call `POST http://127.0.0.1:8002/ingest`.
