# Environment Variables

All configuration comes from environment variables (12-factor). Copy
`.env.example` to `.env` and adjust. **Never commit `.env` or any secret** —
`.env` is git-ignored, secret values are never printed, and the DB URL is injected
into Alembic at runtime rather than stored in `alembic.ini`.

Most TIDE settings use the **`TIDE_` prefix** (`backend/core/config.py:Settings`).
A few conventional, well-known variables are read **without** the prefix via
aliases: `DATABASE_URL`, the `SUPABASE_*` keys, and the `R2_*` keys.

> In local development and tests, no value here contacts a managed service:
> object storage defaults to in-memory, and the database is a disposable local
> container.

## Application

| Variable | Default | Meaning |
| --- | --- | --- |
| `TIDE_ENV` | `local` | `local`/`test`/`staging`/`production`. |
| `TIDE_DEBUG` | `true` | Debug mode. |
| `TIDE_LOG_LEVEL` | `INFO` | Log level. |
| `TIDE_LOG_JSON` | `false` | JSON logs vs. console. |
| `TIDE_API_HOST` / `TIDE_API_PORT` | `0.0.0.0` / `8000` | API bind. |

## PostgreSQL (system of record)

| Variable | Default | Meaning |
| --- | --- | --- |
| `DATABASE_URL` | *(composed)* | Full SQLAlchemy URL (unprefixed). Takes precedence; falls back to `TIDE_DATABASE_URL`, then to the parts below. |
| `TIDE_POSTGRES_HOST` | `localhost` | DB host (compose overrides to `postgres`). |
| `TIDE_POSTGRES_PORT` | `5432` | DB port. |
| `TIDE_POSTGRES_USER` | `tide` | DB user. |
| `TIDE_POSTGRES_PASSWORD` | `tide_local_password` | DB password (local only). |
| `TIDE_POSTGRES_DB` | `tide` | DB name. |

## Supabase (staging/prod; secrets)

| Variable | Default | Meaning |
| --- | --- | --- |
| `SUPABASE_URL` | *(empty)* | Supabase project URL. |
| `SUPABASE_ANON_KEY` | *(empty)* | Anonymous key (secret). |
| `SUPABASE_SERVICE_ROLE_KEY` | *(empty)* | Service-role key (secret). |

## Object storage

| Variable | Default | Meaning |
| --- | --- | --- |
| `TIDE_STORAGE_BACKEND` | `memory` | `memory`/`filesystem`/`r2`. |
| `TIDE_FILESYSTEM_STORAGE_PATH` | `.tide/objectstore` | Base dir for the filesystem backend. |
| `R2_ENDPOINT_URL` | *(empty)* | R2 S3 endpoint. |
| `R2_ACCESS_KEY_ID` | *(empty)* | Access key (secret). |
| `R2_SECRET_ACCESS_KEY` | *(empty)* | Secret key (secret). |
| `R2_BUCKET_NAME` | *(empty)* | Bucket name. |
| `R2_REGION` | `auto` | Region. |

## Redis / providers / seeds

| Variable | Default | Meaning |
| --- | --- | --- |
| `TIDE_REDIS_URL` | `redis://localhost:6379/0` | Optional queue/cache. |
| `TIDE_EMBEDDING_PROVIDER` / `TIDE_EMBEDDING_MODEL` | `noop` / `none` | Embedding backend (model + **dimension** chosen in a later phase). |
| `TIDE_LLM_PROVIDER` / `TIDE_LLM_MODEL` / `TIDE_LLM_API_KEY` | `noop` / `none` / *(empty)* | LLM backend (replaceable; no lock-in). |
| `TIDE_SEED_LIST_PATH` | `seed_list.yaml` | Curated seed file. |
| `TIDE_HISTORICAL_LOOKBACK_DAYS` | `60` | ~2 months of history. |

## Frontend

| Variable | Default | Meaning |
| --- | --- | --- |
| `NEXT_PUBLIC_API_BASE_URL` | `http://localhost:8000` | Backend base URL for the browser. |

## Tests

| Variable | Default | Meaning |
| --- | --- | --- |
| `TIDE_TEST_DATABASE_URL` | *(falls back to `DATABASE_URL`)* | Disposable Postgres for DB tests; DB tests skip if unset/unreachable. |
