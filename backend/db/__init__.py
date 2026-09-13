"""Database wiring for the backend host.

Exposes the declarative ``Base`` and lazy session helpers. Concrete ORM models
and the PostgreSQL/pgvector adapters for the graph & vector ports arrive in later
phases. Nothing here connects at import time.
"""

from __future__ import annotations

from backend.db.base import Base
from backend.db.session import get_engine, get_sessionmaker, session_scope

__all__ = ["Base", "get_engine", "get_sessionmaker", "session_scope"]
