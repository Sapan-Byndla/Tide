"""Historical observations for concepts, entities, and graph edges.

Stores the RAW counts from which future trend signals are calculated — TIDE's
final trend formula is deliberately NOT hard-coded here. Derived quantities
(growth, growth rate, velocity) are computed later from these observations, not
stored.

A unique constraint on ``(subject_type, subject_id, granularity, bucket_start)``
prevents duplicate time-bucket observations.
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
from backend.db.models.enums import Granularity, SubjectType, values
from backend.db.models.mixins import TimestampMixin, jsonb_dict, uuid_pk

_SUBJECT_TYPES = "', '".join(values(SubjectType))
_GRANULARITIES = "', '".join(values(Granularity))


class TimeSeriesObservation(Base, TimestampMixin):
    """One time-bucketed observation of raw metrics for a graph subject."""

    __tablename__ = "time_series_observations"
    __table_args__ = (
        CheckConstraint(f"subject_type IN ('{_SUBJECT_TYPES}')", name="ck_tso_subject_type"),
        CheckConstraint(f"granularity IN ('{_GRANULARITIES}')", name="ck_tso_granularity"),
        UniqueConstraint(
            "subject_type",
            "subject_id",
            "granularity",
            "bucket_start",
            name="uq_tso_bucket",
        ),
        Index("ix_tso_subject", "subject_type", "subject_id", "bucket_start"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    subject_type: Mapped[str] = mapped_column(String(16), nullable=False)
    subject_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    granularity: Mapped[str] = mapped_column(String(16), nullable=False)
    bucket_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Raw inputs only (no derived trend math):
    mention_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    unique_authors: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    engagement_sum: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    source_diversity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # Extensible bucket for additional raw counters without a migration.
    metrics: Mapped[dict] = jsonb_dict()
