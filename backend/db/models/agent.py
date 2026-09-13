"""Persistent data model for the future AI Crawler / Trend Analyst.

Memory is structured, NOT a single giant transcript. Each concern is its own
table so it can be queried, evaluated, and traced:

* ``agent_runs``        — one execution/session of the analyst.
* ``agent_observations``— something determined from graph/data inspection.
* ``agent_hypotheses``  — an explicit belief explaining an observed pattern.
* ``agent_predictions`` — a future-oriented, later-evaluable claim.
* ``agent_reports``     — a persisted intelligence output.

The reasoning loop itself is NOT implemented in this phase.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base
from backend.db.models.enums import AgentRunStatus, PredictionOutcome, values
from backend.db.models.mixins import TimestampMixin, jsonb_dict, jsonb_list, uuid_pk

_RUN_STATUSES = "', '".join(values(AgentRunStatus))
_PREDICTION_OUTCOMES = "', '".join(values(PredictionOutcome))


class AgentRun(Base, TimestampMixin):
    """A single execution/session of the Trend Analyst."""

    __tablename__ = "agent_runs"
    __table_args__ = (
        CheckConstraint(f"status IN ('{_RUN_STATUSES}')", name="ck_agent_runs_status"),
        Index("ix_agent_runs_status", "status"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    trigger: Mapped[str | None] = mapped_column(String(64), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    config: Mapped[dict] = jsonb_dict()
    stats: Mapped[dict] = jsonb_dict()
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    observations: Mapped[list[AgentObservation]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )
    hypotheses: Mapped[list[AgentHypothesis]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )
    predictions: Mapped[list[AgentPrediction]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )
    reports: Mapped[list[AgentReport]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )


class AgentObservation(Base, TimestampMixin):
    """Something the agent determined from inspecting the graph/data."""

    __tablename__ = "agent_observations"
    __table_args__ = (Index("ix_agent_observations_run_id", "run_id"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    run_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False
    )
    observation_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    subject_type: Mapped[str | None] = mapped_column(String(16), nullable=True)
    subject_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    data: Mapped[dict] = jsonb_dict()

    run: Mapped[AgentRun] = relationship(back_populates="observations")


class AgentHypothesis(Base, TimestampMixin):
    """An explicit belief explaining an observed pattern."""

    __tablename__ = "agent_hypotheses"
    __table_args__ = (Index("ix_agent_hypotheses_run_id", "run_id"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    run_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False
    )
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="proposed")
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    supporting_evidence: Mapped[list] = jsonb_list()
    contradicting_evidence: Mapped[list] = jsonb_list()
    meta: Mapped[dict] = jsonb_dict("metadata")

    run: Mapped[AgentRun] = relationship(back_populates="hypotheses")
    predictions: Mapped[list[AgentPrediction]] = relationship(back_populates="hypothesis")


class AgentPrediction(Base, TimestampMixin):
    """A future-oriented claim designed to be evaluated later.

    Carries everything needed to eventually measure whether TIDE's analyst is
    actually correct: the predicted statement, when it was made (``created_at``),
    when it should be judged (``evaluation_at``), the confidence, the resolved
    ``status`` (outcome), the ``actual_outcome``, and free-form
    ``evaluation_metadata``.
    """

    __tablename__ = "agent_predictions"
    __table_args__ = (
        CheckConstraint(
            f"status IN ('{_PREDICTION_OUTCOMES}')", name="ck_agent_predictions_status"
        ),
        Index("ix_agent_predictions_run_id", "run_id"),
        Index("ix_agent_predictions_status", "status"),
        Index("ix_agent_predictions_evaluation_at", "evaluation_at"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    run_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False
    )
    hypothesis_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("agent_hypotheses.id", ondelete="SET NULL"),
        nullable=True,
    )
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    horizon: Mapped[str | None] = mapped_column(String(64), nullable=True)
    evaluation_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    actual_outcome: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    evaluation_metadata: Mapped[dict] = jsonb_dict()

    run: Mapped[AgentRun] = relationship(back_populates="predictions")
    hypothesis: Mapped[AgentHypothesis | None] = relationship(back_populates="predictions")


class AgentReport(Base, TimestampMixin):
    """A persisted intelligence output."""

    __tablename__ = "agent_reports"
    __table_args__ = (Index("ix_agent_reports_run_id", "run_id"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    run_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    concept_ids: Mapped[list] = jsonb_list()
    entity_ids: Mapped[list] = jsonb_list()
    prediction_ids: Mapped[list] = jsonb_list()
    generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    meta: Mapped[dict] = jsonb_dict("metadata")

    run: Mapped[AgentRun] = relationship(back_populates="reports")
