"""Post → concept / post → entity evidence associations.

These let future processing assert "this post mentions this concept/entity" while
keeping every association traceable to a specific source post. The extraction
algorithm is NOT implemented in this phase — only the structure to record its
output (with confidence and method/model provenance).
"""

from __future__ import annotations

import uuid

from sqlalchemy import Float, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.db.base import Base
from backend.db.models.mixins import TimestampMixin, jsonb_dict, uuid_pk


class PostConcept(Base, TimestampMixin):
    """Evidence that a post supports/mentions a concept."""

    __tablename__ = "post_concepts"
    __table_args__ = (
        UniqueConstraint(
            "post_id", "concept_id", "extraction_method", name="uq_post_concepts_assoc"
        ),
        Index("ix_post_concepts_concept_id", "concept_id"),
        Index("ix_post_concepts_post_id", "post_id"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    post_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("posts.id", ondelete="CASCADE"), nullable=False
    )
    concept_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False
    )
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    extraction_method: Mapped[str] = mapped_column(
        String(64), nullable=False, default="unspecified"
    )
    extraction_model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    meta: Mapped[dict] = jsonb_dict("metadata")


class PostEntity(Base, TimestampMixin):
    """Evidence that a post references an entity."""

    __tablename__ = "post_entities"
    __table_args__ = (
        UniqueConstraint(
            "post_id", "entity_id", "extraction_method", name="uq_post_entities_assoc"
        ),
        Index("ix_post_entities_entity_id", "entity_id"),
        Index("ix_post_entities_post_id", "post_id"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    post_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("posts.id", ondelete="CASCADE"), nullable=False
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("entities.id", ondelete="CASCADE"), nullable=False
    )
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    extraction_method: Mapped[str] = mapped_column(
        String(64), nullable=False, default="unspecified"
    )
    extraction_model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    meta: Mapped[dict] = jsonb_dict("metadata")
