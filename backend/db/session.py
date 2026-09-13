"""Lazy database engine / session management.

The engine is created lazily and cached, so importing this module — or starting
the API, or running most tests — never requires a live PostgreSQL. A connection
is only attempted when a caller actually asks for a session, which no Phase 0
code path does.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.core.config import get_settings


@lru_cache
def get_engine() -> Engine:
    """Create (once) and return the SQLAlchemy engine.

    ``pool_pre_ping`` guards against stale connections. ``future=True`` selects
    SQLAlchemy 2.0 semantics. No connection is opened until first use.
    """
    settings = get_settings()
    return create_engine(
        settings.sqlalchemy_url,
        pool_pre_ping=True,
        future=True,
    )


@lru_cache
def get_sessionmaker() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), autoflush=False, expire_on_commit=False)


@contextmanager
def session_scope() -> Iterator[Session]:
    """Transactional session context manager.

    Usage (later phases)::

        with session_scope() as session:
            session.add(obj)
    """
    session = get_sessionmaker()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
