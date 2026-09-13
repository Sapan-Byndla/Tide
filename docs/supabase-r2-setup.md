# Manual Supabase / R2 Setup (Staging & Production)

**None of this is required for local development or tests** — TIDE runs fully
locally with a disposable PostgreSQL container and in-memory object storage.
These steps apply only when deploying against managed services.

## PostgreSQL (Supabase or any managed Postgres)

1. Create the database / project. Note the connection string.
2. Ensure the **pgvector** extension is available. The migration runs
   `CREATE EXTENSION IF NOT EXISTS vector;` — on Supabase, enable the `vector`
   extension (Dashboard → Database → Extensions) if your role can't create it.
3. Set `DATABASE_URL` to the connection string (use the `postgresql+psycopg://`
   scheme). Optionally set `SUPABASE_URL` / `SUPABASE_ANON_KEY` /
   `SUPABASE_SERVICE_ROLE_KEY` if client SDK access is needed later.
4. Apply the schema **with migrations only** — no manual table creation:
   ```bash
   alembic upgrade head   # or: make migrate
   ```
5. (Optional) Populate curated seeds: `python -m scripts.import_seeds`.

> You never click "create table" in the Supabase UI. The schema is 100%
> reproducible from version-controlled migrations.

## Cloudflare R2

1. Create an R2 bucket (e.g. `tide-raw`).
2. Create an API token / access key pair scoped to that bucket.
3. Set the environment variables (secrets — never commit them):
   ```
   TIDE_STORAGE_BACKEND=r2
   R2_ENDPOINT_URL=https://<accountid>.r2.cloudflarestorage.com
   R2_ACCESS_KEY_ID=...
   R2_SECRET_ACCESS_KEY=...
   R2_BUCKET_NAME=tide-raw
   R2_REGION=auto
   ```
4. The `R2ObjectStorage` adapter (`storage/r2.py`) is selected automatically by
   the factory. Missing config fails fast with a clear error (and never prints the
   secret values).

## Checklist

- [ ] `DATABASE_URL` set and reachable
- [ ] `vector` extension enabled
- [ ] `alembic upgrade head` applied
- [ ] (optional) seeds imported
- [ ] R2 bucket + credentials set, `TIDE_STORAGE_BACKEND=r2`
