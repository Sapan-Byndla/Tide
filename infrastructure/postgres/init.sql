-- TIDE local PostgreSQL initialization.
--
-- Runs once when the local dev database container is first created. It ONLY
-- enables the pgvector extension so later phases can store embeddings. It does
-- NOT create any application schema or tables — those are owned by Alembic
-- migrations, which are introduced in a later phase.
--
-- This file is for LOCAL DEVELOPMENT convenience only. No production database is
-- provisioned in Phase 0.

CREATE EXTENSION IF NOT EXISTS vector;
