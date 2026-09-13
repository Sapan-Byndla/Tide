"""The relational foundation for TIDE's concept/entity graph.

Edges are polymorphic (a node is a concept OR an entity), so nodes are referenced
by ``(node_type, node_id)`` rather than a single FK — the standard relational
pattern for a heterogeneous graph. ``node_type`` is constrained by CHECK.

The graph is TEMPORAL. Each edge records ``first_observed_at`` / ``last_observed_at``
plus a running ``weight`` and ``evidence_count``; and — crucially — the
``time_series_observations`` table (see ``timeseries.py``) can record ``EDGE``
subjects, so "A became increasingly associated with B over time" is representable
as a series of edge-weight observations. No scoring algorithm is implemented here.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.db.base import Base
from backend.db.models.enums import NodeType, values
from backend.db.models.mixins import TimestampMixin, jsonb_dict, uuid_pk

_NODE_TYPES = "', '".join(values(NodeType))


class GraphEdge(Base, TimestampMixin):
    """A directed, temporal relationship between two graph nodes."""

    __tablename__ = "graph_edges"
    __table_args__ = (
        CheckConstraint(
            f"source_node_type IN ('{_NODE_TYPES}')", name="ck_graph_edges_source_node_type"
        ),
        CheckConstraint(
            f"target_node_type IN ('{_NODE_TYPES}')", name="ck_graph_edges_target_node_type"
        ),
        UniqueConstraint(
            "source_node_type",
            "source_node_id",
            "target_node_type",
            "target_node_id",
            "relationship_type",
            name="uq_graph_edges_edge",
        ),
        Index("ix_graph_edges_source", "source_node_type", "source_node_id"),
        Index("ix_graph_edges_target", "target_node_type", "target_node_id"),
        Index("ix_graph_edges_relationship_type", "relationship_type"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    source_node_type: Mapped[str] = mapped_column(String(16), nullable=False)
    source_node_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    target_node_type: Mapped[str] = mapped_column(String(16), nullable=False)
    target_node_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    relationship_type: Mapped[str] = mapped_column(String(64), nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    evidence_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    first_observed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_observed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    meta: Mapped[dict] = jsonb_dict("metadata")
