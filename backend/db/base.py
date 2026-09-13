"""SQLAlchemy declarative base.

Defines the metadata/registry that ORM models will attach to in later phases.
Importing this module opens no connection and creates no tables. There are no
application tables in Phase 0 — this is the anchor Alembic autogeneration and
future models build on.
"""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Common base for all TIDE ORM models (none defined yet in Phase 0)."""

    pass
