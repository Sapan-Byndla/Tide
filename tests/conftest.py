"""Shared pytest fixtures.

Tests run with ``TIDE_ENV=test``. Pure tests (config, seed validation, object
storage) need no database. Database tests use the ``db_session`` fixture, which
targets a *disposable* local PostgreSQL and is skipped automatically when no
database URL is available.

The ``db_engine`` fixture demonstrates completion criterion #2 directly: it drops
the schema and brings a CLEAN database up to the full TIDE schema using Alembic
migrations only (no ``create_all``).
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

import pytest

os.environ.setdefault("TIDE_ENV", "test")

ROOT = Path(__file__).resolve().parents[1]
SEED_LIST = ROOT / "seed_list.yaml"


@pytest.fixture(autouse=True)
def _reset_settings_cache() -> Iterator[None]:
    from backend.core.config import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


# --------------------------------------------------------------------------- #
# Phase 0 app fixtures
# --------------------------------------------------------------------------- #
@pytest.fixture
def app():  # type: ignore[no-untyped-def]
    from backend.main import create_app

    return create_app()


@pytest.fixture
def client(app):  # type: ignore[no-untyped-def]
    from fastapi.testclient import TestClient

    with TestClient(app) as test_client:
        yield test_client


# --------------------------------------------------------------------------- #
# Phase 1 database fixtures
# --------------------------------------------------------------------------- #
_LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1", "postgres"}


def _test_db_url() -> str | None:
    """The DEDICATED test database URL.

    Intentionally does NOT fall back to ``DATABASE_URL``: that variable may point
    at a real/remote database (e.g. Supabase), and the DB fixtures run
    destructive DDL (``DROP SCHEMA``). DB tests require an explicit, disposable
    ``TIDE_TEST_DATABASE_URL``.
    """
    return os.environ.get("TIDE_TEST_DATABASE_URL")


def _assert_local(url: str) -> None:
    """Refuse to run destructive DDL against a non-local host (safety guard)."""
    from urllib.parse import urlparse

    host = (urlparse(url).hostname or "").lower()
    if host not in _LOCAL_HOSTS and not os.environ.get("TIDE_TEST_ALLOW_REMOTE"):
        pytest.skip(
            f"refusing destructive test DDL against non-local host {host!r}; "
            "set TIDE_TEST_DATABASE_URL to a local database "
            "(or TIDE_TEST_ALLOW_REMOTE=1 to override)"
        )


@pytest.fixture(scope="session")
def db_engine():  # type: ignore[no-untyped-def]
    """A DISPOSABLE local PostgreSQL engine with the FULL schema via migrations.

    Skips the whole DB test suite unless a dedicated, local test database is
    configured (see ``_test_db_url`` / ``_assert_local``).
    """
    from sqlalchemy import create_engine, text
    from sqlalchemy.exc import OperationalError

    url = _test_db_url()
    if not url:
        pytest.skip("TIDE_TEST_DATABASE_URL not set; skipping DB tests (safety)")
    _assert_local(url)

    # Ensure settings (and Alembic env) resolve to THIS url — overriding any
    # DATABASE_URL from the environment/.env so migrations never hit a remote DB.
    os.environ["DATABASE_URL"] = url
    from backend.core.config import get_settings

    get_settings.cache_clear()

    engine = create_engine(url, future=True)
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except OperationalError:
        pytest.skip(f"cannot connect to test database at {url!r}; skipping DB tests")

    # CLEAN database -> full schema using migrations only.
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))

    from alembic import command
    from alembic.config import Config

    cfg = Config(str(ROOT / "alembic.ini"))
    command.upgrade(cfg, "head")

    yield engine
    engine.dispose()


@pytest.fixture
def db_session(db_engine):  # type: ignore[no-untyped-def]
    """A function-scoped session wrapped in a transaction rolled back after use."""
    from sqlalchemy.orm import Session

    connection = db_engine.connect()
    outer = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        outer.rollback()
        connection.close()
