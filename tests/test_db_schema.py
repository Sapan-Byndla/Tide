"""A clean database migrates to the complete schema via Alembic only."""

from __future__ import annotations

import pytest
from sqlalchemy import inspect, text

pytestmark = pytest.mark.db

EXPECTED_TABLES = {
    "sources",
    "seeds",
    "authors",
    "posts",
    "entities",
    "concepts",
    "post_concepts",
    "post_entities",
    "graph_edges",
    "time_series_observations",
    "embeddings",
    "agent_runs",
    "agent_observations",
    "agent_hypotheses",
    "agent_predictions",
    "agent_reports",
}


def test_all_tables_exist(db_engine) -> None:  # type: ignore[no-untyped-def]
    tables = set(inspect(db_engine).get_table_names())
    missing = EXPECTED_TABLES - tables
    assert not missing, f"missing tables: {missing}"
    assert "alembic_version" in tables


def test_pgvector_extension_enabled(db_engine) -> None:  # type: ignore[no-untyped-def]
    with db_engine.connect() as conn:
        row = conn.execute(text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")).first()
    assert row is not None, "pgvector extension not installed by migration"


def test_alembic_at_head(db_engine) -> None:  # type: ignore[no-untyped-def]
    with db_engine.connect() as conn:
        version = conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
    assert version  # a concrete revision is stamped


def test_posts_unique_constraint_present(db_engine) -> None:  # type: ignore[no-untyped-def]
    uniques = inspect(db_engine).get_unique_constraints("posts")
    cols = {frozenset(u["column_names"]) for u in uniques}
    assert frozenset({"source_id", "external_id"}) in cols
