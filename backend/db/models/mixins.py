"""Shared column mixins and small helpers for ORM models."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column


def uuid_pk() -> Mapped[uuid.UUID]:
    """A client-side-defaulted UUID primary key column.

    Client-side ``uuid4`` (not a DB sequence) keeps identifiers stable and
    independent of DB-generated values, and lets callers pass deterministic
    UUIDs (e.g. ``uuid5``) for reproducible seed/demo data.
    """
    return mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


def jsonb_dict(column_name: str | None = None) -> Mapped[dict]:
    """A non-null JSONB object column defaulting to ``{}``."""
    if column_name is None:
        return mapped_column(
            JSONB(), nullable=False, default=dict, server_default=text("'{}'::jsonb")
        )
    return mapped_column(
        column_name, JSONB(), nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )


def jsonb_list(column_name: str | None = None) -> Mapped[list]:
    """A non-null JSONB array column defaulting to ``[]``."""
    if column_name is None:
        return mapped_column(
            JSONB(), nullable=False, default=list, server_default=text("'[]'::jsonb")
        )
    return mapped_column(
        column_name, JSONB(), nullable=False, default=list, server_default=text("'[]'::jsonb")
    )


class TimestampMixin:
    """Adds ``created_at`` / ``updated_at`` managed by the database."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
