"""pgvector-ready embeddings table.

Phase intent: prepare the database for semantic vectors WITHOUT choosing a model
or dimension and WITHOUT generating anything.

* The ``embedding`` column uses pgvector's ``vector`` type with **no fixed
  dimension** — a dimensionless ``vector`` column accepts any length, so the
  embedding model (and its dimensionality) can be decided in a later phase.
* ``provider`` / ``model`` / ``dim`` record provenance per row once vectors exist.

No index is created on the vector column yet: the right ANN index (ivfflat vs
hnsw) and its parameters depend on the chosen model and data scale, which are
future decisions.
"""

from __future__ import annotations

import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.db.base import Base
from backend.db.models.mixins import TimestampMixin, jsonb_dict, uuid_pk


class Embedding(Base, TimestampMixin):
    """A semantic vector attached to some owner (post, concept, entity, ...)."""

    __tablename__ = "embeddings"
    __table_args__ = (
        UniqueConstraint("owner_type", "owner_id", "model", name="uq_embeddings_owner_model"),
        Index("ix_embeddings_owner", "owner_type", "owner_id"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    owner_type: Mapped[str] = mapped_column(String(32), nullable=False)
    owner_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    model: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    dim: Mapped[int | None] = mapped_column(Integer, nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # Dimensionless pgvector column — dimension NOT hard-coded in this phase.
    embedding: Mapped[list[float] | None] = mapped_column(Vector(), nullable=True)
    meta: Mapped[dict] = jsonb_dict("metadata")
