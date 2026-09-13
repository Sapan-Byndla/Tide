# Storage Architecture

TIDE's storage is now partially **implemented** (Phase 1): PostgreSQL is the
system of record, pgvector is prepared for semantic vectors, and object storage
(Cloudflare R2) has a working adapter behind the `ObjectStorage` port.

## Stores and roles

| Store | Technology | Port / model | Status | Holds |
| --- | --- | --- | --- | --- |
| Structured data | **PostgreSQL** | SQLAlchemy ORM (`backend/db/models/`) | ✅ implemented | Sources, seeds, authors, posts, concepts, entities, evidence, graph edges, time series, agent memory. |
| Semantic vectors | **pgvector** | `embeddings` table (dimensionless `vector`) | ✅ prepared | Embeddings (none generated yet; model/dim chosen later). |
| Raw / large payloads | **Cloudflare R2** (S3-compatible) | `contracts.ObjectStorage` → `storage/r2.py` | ✅ adapter implemented | Raw scraper payloads, archives, snapshots, failed items. |
| Queue / cache | **Redis** | — | ⏸ deferred | Nothing depends on it yet. |

## Post storage strategy (important)

The **full raw payload is never stored in PostgreSQL.** Postgres stores the
*normalized* post plus a reference:

```
posts.raw_payload_uri  ──▶  r2://<bucket>/raw/<source>/<YYYY>/<MM>/<DD>/<id>.json
```

This keeps the database queryable and lean for high-volume ingestion while the
original payload is retained in object storage for audit, debugging, and
reprocessing. Different sources may have different payload shapes, so the object
`ext` is explicit, never assumed.

## Object storage adapters

All implement the async `contracts.ObjectStorage` contract (`put`/`get`/`exists`/
`delete`/`list_prefix`) and are selected by `TIDE_STORAGE_BACKEND`:

* **`memory`** (`storage/memory.py`) — in-process; default for local dev & tests.
* **`filesystem`** (`storage/filesystem.py`) — durable local directory.
* **`r2`** (`storage/r2.py`) — Cloudflare R2 via boto3 (S3-compatible). Credentials
  come only from `R2_*` env vars; the boto3 client is injectable so the adapter is
  tested through its abstraction with no network.

Use `storage.factory.get_object_storage(settings)` to construct the configured
adapter, and `storage.keys` for stable keys:

```
raw/<source>/<YYYY>/<MM>/<DD>/<identifier>.<ext>
archives/<source>/<YYYY>/<MM>/<DD>/<identifier>.<ext>
failed/<source>/<YYYY>/<MM>/<DD>/<identifier>.<ext>
snapshots/<name>/<YYYY>/<MM>/<DD>/<identifier>.<ext>
```

## Migrations & reproducibility

* ORM models attach to `backend/db/base.py:Base`; `backend/db/models/` registers
  them all.
* **Alembic** migrations reproduce the entire schema from empty
  (`make migrate`), including `CREATE EXTENSION IF NOT EXISTS vector`. The DB URL
  is injected from settings — never stored in `alembic.ini`.
* The engine/session (`backend/db/session.py`) stays lazy: importing it or
  starting the API opens no connection.

## Local vs production

* **Local:** disposable PostgreSQL via `docker compose up -d postgres`
  (pgvector image), object storage `memory` or `filesystem`. No real credentials.
* **Production:** Supabase PostgreSQL (same schema, same migrations) + Cloudflare
  R2. See [supabase-r2-setup.md](supabase-r2-setup.md) for the manual steps.
