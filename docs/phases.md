# Planned Phase Boundaries

TIDE is built in phases. **This repository is Phase 0 only.** Later phases
implement into the contracts and structure established here.

## Phase 0 — Foundation (this phase) ✅

Architecture, repo structure, conventions, interfaces, docs, testing foundation,
configuration system, and a runnable local environment.

**Delivered:** subsystem packages with clear responsibilities; the `contracts/`
ports (`BaseScraper`, `HistoricalScraper`, `DailyScraper`, `PostNormalizer`,
`EmbeddingProvider`, `GraphRepository`, `VectorRepository`, `ObjectStorage`,
`TrendAnalyzer`, `AgentMemory`, `LLMProvider`); domain models; FastAPI host with
`/health`; structured logging; typed settings; Alembic scaffold; in-memory
reference graph/vector adapters; docker-compose dev env; docs; test suite.

**Explicitly NOT in Phase 0:**
- ❌ Real scrapers / any website access
- ❌ Intelligence extraction models / embeddings
- ❌ AI Crawler reasoning / trend analysis
- ❌ Final graph algorithms
- ❌ Frontend dashboard
- ❌ External API integrations, production credentials, R2 bucket, Supabase schemas
- ❌ Downloaded/large AI models
- ❌ Any lock-in to a paid AI provider

## Phase 1 — Data foundation ✅ (current)

The persistent system of record, built to receive later phases:

**Delivered:**
- Full PostgreSQL schema via Alembic migrations (empty DB → complete schema),
  incl. `CREATE EXTENSION vector`.
- Curated configuration tables (`sources`, `seeds`) kept **distinct** from
  discovered knowledge (`concepts`, `entities`); temporal `graph_edges`;
  `time_series_observations` (raw metrics only); pgvector-ready dimensionless
  `embeddings`; agent-memory tables (`agent_runs/observations/hypotheses/
  predictions/reports`) with prediction-evaluation fields.
- Idempotent `seed_list.yaml` importer with deterministic, stable seed IDs;
  non-destructive removal (deactivate, never delete).
- Cloudflare R2 object-storage adapter behind `contracts.ObjectStorage`, plus
  in-memory & filesystem adapters; posts store a `raw_payload_uri` reference, not
  the raw payload.
- Deterministic demo data; broad test suite; docs.

**Still NOT in Phase 1:** scraping/collection execution, schedulers, embedding
generation, model downloads, LLM calls, the AI Crawler, trend detection, the
dashboard, a dedicated graph DB, and any automatic mutation of `seed_list.yaml`.

## Phase 2 — Collection

Concrete scrapers in `scrapers/sources/`; the shared machinery in
`scrapers/base/` (rate limiting, checkpoint persistence, dedup); working
historical bootstrap and daily collection workflows writing posts + raw payloads.

## Phase 3 — Intelligence & graph persistence

`PostNormalizer` implementations; entity/concept extraction; an
`EmbeddingProvider` (model + dimension chosen here); repository adapters that map
domain models onto the Phase 1 tables; population of the graph and time series.

## Phase 4 — AI Crawler

`TrendAnalyzer` and the observe→hypothesize→evaluate→predict→report loop writing
to the Phase 1 agent-memory tables; a replaceable `LLMProvider` adapter;
prediction evaluation.

## Phase 5 — Dashboard & delivery

Frontend trend-intelligence dashboard; backend read APIs over the graph and
reports; production deployment and hardening.

---

Phase boundaries are enforced by the ports: each later phase supplies adapters
for interfaces that already exist, so no phase requires rewriting a previous one.
