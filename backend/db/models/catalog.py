"""Curated configuration: the source registry and the seed catalog.

These two tables hold *curated configuration* — the human-maintained beachhead.
They are deliberately distinct from the *discovered knowledge* tables
(``concepts``, ``entities``): removing a seed here must never delete graph
knowledge. See ``knowledge.py`` and ``docs/seeds-vs-concepts.md``.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base
from backend.db.models.mixins import TimestampMixin, jsonb_dict, jsonb_list, uuid_pk


class Source(Base, TimestampMixin):
    """A collection platform (reddit, x, youtube, github, arxiv, rss, ...).

    Normalized so future platforms are added as rows, not new tables.
    """

    __tablename__ = "sources"

    id: Mapped[uuid.UUID] = uuid_pk()
    source_key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(128), nullable=False)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    meta: Mapped[dict] = jsonb_dict("metadata")

    seeds: Mapped[list[Seed]] = relationship(back_populates="source")


class Seed(Base, TimestampMixin):
    """A single curated seed (topic or source-specific target).

    ``key`` is a stable, deterministic identifier derived from the seed's
    identity (never a DB sequence), so re-importing ``seed_list.yaml`` updates the
    same rows. ``source_id`` is NULL for globally-conceptual topic seeds.
    """

    __tablename__ = "seeds"
    __table_args__ = (
        Index("ix_seeds_seed_type", "seed_type"),
        Index("ix_seeds_source_id", "source_id"),
        Index("ix_seeds_enabled", "enabled"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    key: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    seed_type: Mapped[str] = mapped_column(String(32), nullable=False)
    source_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("sources.id", ondelete="SET NULL"), nullable=True
    )
    canonical_value: Mapped[str] = mapped_column(String(512), nullable=False)
    aliases: Mapped[list] = jsonb_list()
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    config: Mapped[dict] = jsonb_dict()
    origin: Mapped[str] = mapped_column(String(32), nullable=False, default="seed_list.yaml")
    source_config_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    imported_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    source: Mapped[Source | None] = relationship(back_populates="seeds")
