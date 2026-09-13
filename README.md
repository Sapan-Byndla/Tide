# TIDE

**Concept Graph and Trend Intelligence System.**

TIDE collects posts from many sources, turns them into a persistent **concept
graph** (concepts, entities, relationships, evidence, metrics, temporal
signals), and runs an **AI Crawler / Trend Analyst** that traverses that graph —
forming hypotheses, weighing evidence, making predictions, and generating trend
intelligence. The AI Crawler is *not* a scraper: it reasons over internal state,
never scraping external platforms directly.

> ⚠️ **This repository is at Phase 1** — architecture (Phase 0) + the persistent
> **data foundation** (Phase 1): PostgreSQL schema & migrations, curated-seed
> importer, pgvector-ready embeddings, agent-memory tables, and a Cloudflare R2
> object-storage adapter. No scraping, embedding generation, AI reasoning, or
> dashboard is implemented yet. See [`docs/phases.md`](docs/phases.md).

## The four systems

1. **Scrapers** — source-specific data collection (`scrapers/`).
2. **Intelligence processing** — normalize posts → entities, concepts,
   embeddings, relationships, metrics (`intelligence/`).
3. **Concept graph** — the persistent knowledge substrate (`graph/`).
4. **AI Crawler / Trend Analyst** — reads the graph and produces intelligence
   (`agent/`).

## Architecture in one picture

Ports-and-adapters: a dependency-free `contracts/` core (domain models + abstract
interfaces) that every subsystem depends on, so implementations swap without
rewrites. Full diagram and explanation in
[`docs/architecture.md`](docs/architecture.md).

## Repository layout

```
contracts/       Shared domain models + abstract ports (the stable core)
scrapers/        Source-specific collection (base machinery + sources + registry)
intelligence/    Raw posts -> normalized data, entities, concepts, embeddings
graph/           Concept graph persistence & traversal (+ in-memory reference impl)
agent/           AI Crawler / Trend Analyst (conceptual lifecycle)
workers/         Historical bootstrap & daily collection workflows
backend/         FastAPI host + data foundation (composition root)
  ├─ db/models/  SQLAlchemy ORM: sources, seeds, posts, concepts, graph, agent, ...
  ├─ db/demo.py  Deterministic development/demo data
  ├─ migrations/ Alembic migrations (empty DB -> full schema)
  └─ seeds/      seed_list.yaml loader, validator, deterministic-id importer
storage/         Object-storage adapters (memory / filesystem / Cloudflare R2)
scripts/         CLI entrypoints (import_seeds, load_demo)
frontend/        Next.js + TypeScript app (dashboard comes later)
tests/           pytest suite (pure + database-backed)
docs/            Architecture, data model, storage, seeds-vs-concepts, agent memory
infrastructure/  Docker images, Postgres init, example seed list
seed_list.yaml   Curated seed configuration (the beachhead)
```

> **Structure note:** the brief suggested a top-level `backend/` plus subsystem
> dirs. We added one documented package — `contracts/` — to hold the shared ports
> and domain models. This enforces a clean dependency direction (subsystems →
> `contracts`, never the reverse) and is *not* a catch-all utils module: it
> contains only interfaces and domain types. Rationale in
> [`docs/architecture.md`](docs/architecture.md).

## Quick start

```bash
cp .env.example .env

# Backend (native)
make install      # create .venv + install (editable, dev deps)
make dev          # http://localhost:8000/health  and  /docs

# Database foundation (Phase 1)
make db-up        # start local PostgreSQL + pgvector (docker)
make migrate      # empty DB -> full schema (migrations only)
make import-seeds # load curated seed_list.yaml (idempotent)
make load-demo    # load deterministic demo data
# ...or all three at once:
make db-bootstrap

# Tests. Pure tests always run; DB tests skip unless a DEDICATED, local
# disposable test DB is set (never point this at a real/remote database):
make test                              # pure tests only (DB tests skip)
make db-up-test && make test-db        # full suite against local Postgres :55432

# Frontend
make frontend-install && make frontend-dev  # http://localhost:3000

# Or the full environment (Postgres + pgvector + Redis + backend + frontend)
make up
```

Full instructions: [`docs/local-development.md`](docs/local-development.md).
Configuration: [`docs/environment.md`](docs/environment.md).

## Tech stack

- **Backend:** Python 3.11+, FastAPI, SQLAlchemy 2, Alembic, Pydantic, structlog
- **Frontend:** Next.js, TypeScript, React
- **Testing:** pytest (backend), Vitest (frontend)
- **Data (later phases):** PostgreSQL + pgvector, Cloudflare R2, Redis
- **Dev env:** Docker + Docker Compose, Makefile

No paid AI provider is assumed or required — the `LLMProvider` and
`EmbeddingProvider` ports keep model choice fully replaceable.

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) and [`docs/`](docs/README.md).
