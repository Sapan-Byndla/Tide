"""Discovered knowledge: entities and concepts.

These tables are the *expanding knowledge representation*. They are separate from
the curated ``seeds`` table on purpose:

* A **concept** may be ``DISCOVERED`` — present here but never in ``seed_list.yaml``
  (``origin='discovered'``, ``seed_id=NULL``). The seed list is a beachhead, not
  a hard allow-list.
* When a concept *does* originate from a curated seed, ``seed_id`` records that
  provenance — WITHOUT collapsing the two tables into one.

Nothing here is created by the seed importer; concepts/entities are produced by
future processing phases. Removing a seed never deletes rows here.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.db.base import Base
from backend.db.models.mixins import TimestampMixin, jsonb_dict, jsonb_list, uuid_pk


class Entity(Base, TimestampMixin):
    """A concrete named thing (person, org, product, technology, platform, ...).

    Entity types are an open vocabulary (string): discovered entities are not
    restricted to today's seed list.
    """

    __tablename__ = "entities"
    __table_args__ = (
        Index("ix_entities_entity_type", "entity_type"),
        Index("ix_entities_status", "status"),
        Index("ix_entities_canonical_name", "canonical_name"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    key: Mapped[str | None] = mapped_column(String(200), unique=True, nullable=True)
    canonical_name: Mapped[str] = mapped_column(String(512), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    aliases: Mapped[list] = jsonb_list()
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    first_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    meta: Mapped[dict] = jsonb_dict("metadata")


class Concept(Base, TimestampMixin):
    """An abstract idea/theme in the knowledge graph.

    ``origin`` + nullable ``seed_id`` distinguish curated-derived from discovered
    concepts without merging the seed and concept tables.
    """

    __tablename__ = "concepts"
    __table_args__ = (
        Index("ix_concepts_status", "status"),
        Index("ix_concepts_concept_type", "concept_type"),
        Index("ix_concepts_seed_id", "seed_id"),
        Index("ix_concepts_canonical_name", "canonical_name"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    key: Mapped[str | None] = mapped_column(String(200), unique=True, nullable=True)
    canonical_name: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    concept_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    aliases: Mapped[list] = jsonb_list()
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="discovered")
    origin: Mapped[str] = mapped_column(String(32), nullable=False, default="discovered")
    # Provenance link when a concept came from a curated seed. NULL for discovered
    # concepts. ondelete=SET NULL so removing a seed never deletes the concept.
    seed_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("seeds.id", ondelete="SET NULL"), nullable=True
    )
    first_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    meta: Mapped[dict] = jsonb_dict("metadata")
