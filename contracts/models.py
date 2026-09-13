"""Domain models shared across TIDE subsystems.

These are transport/domain objects (Pydantic models) — deliberately decoupled
from any persistence framework. Database (SQLAlchemy) models and API schemas in
later phases will map *to and from* these, but these remain the canonical shape
of a "Post", "Concept", "Hypothesis", etc. that every subsystem agrees on.

Nothing here talks to a database, a network, or an LLM. That separation is what
lets the graph live in PostgreSQL now and somewhere else later without touching
the domain vocabulary.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from contracts.enums import (
    CheckpointStatus,
    CollectionMode,
    EntityType,
    HypothesisStatus,
    MemoryClass,
    PostStatus,
    PredictionOutcome,
    RelationshipType,
    SourceType,
    TrendDirection,
)


class _Base(BaseModel):
    """Shared config for all domain models."""

    model_config = ConfigDict(extra="forbid", frozen=False)


# --------------------------------------------------------------------------- #
# Collection / scraping
# --------------------------------------------------------------------------- #
class SeedSource(_Base):
    """A single configured source in the seed list."""

    id: str
    name: str
    source_type: SourceType
    url: str
    enabled: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class ScrapeWindow(_Base):
    """A bounded time range a collection job is responsible for.

    Daily collection and historical bootstrap both operate over windows; this is
    what makes jobs replayable for a specific date or period.
    """

    start: datetime
    end: datetime
    mode: CollectionMode


class RawPost(_Base):
    """A post exactly as collected from a source, before normalization.

    Large payloads (full HTML, attachments) are referenced by `payload_ref`
    (an object-storage key) rather than inlined.
    """

    source_id: str
    source_type: SourceType
    external_id: str
    url: str | None = None
    collected_at: datetime
    published_at: datetime | None = None
    title: str | None = None
    body: str | None = None
    payload_ref: str | None = None
    status: PostStatus = PostStatus.COLLECTED
    raw: dict[str, Any] = Field(default_factory=dict)

    @property
    def dedup_key(self) -> str:
        """Stable identity used for idempotent, deduplicating collection."""
        return f"{self.source_id}:{self.external_id}"


class NormalizedPost(_Base):
    """A post after normalization into a common schema."""

    dedup_key: str
    source_id: str
    source_type: SourceType
    url: str | None = None
    published_at: datetime | None = None
    language: str | None = None
    title: str | None = None
    text: str
    tokens: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CollectionCheckpoint(_Base):
    """Resumable checkpoint for a source within a collection run."""

    run_id: str
    source_id: str
    mode: CollectionMode
    window: ScrapeWindow
    cursor: str | None = None
    collected_count: int = 0
    status: CheckpointStatus = CheckpointStatus.PENDING
    updated_at: datetime | None = None


# --------------------------------------------------------------------------- #
# Concept graph
# --------------------------------------------------------------------------- #
class Entity(_Base):
    """A concrete named thing extracted from posts."""

    id: str
    name: str
    entity_type: EntityType
    aliases: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Concept(_Base):
    """An abstract idea/theme that entities and posts relate to.

    Concepts are graph nodes carrying temporal signal; they are the primary unit
    the AI Crawler reasons over.
    """

    id: str
    label: str
    description: str | None = None
    entity_ids: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Relationship(_Base):
    """A directed edge between two graph nodes (concepts and/or entities)."""

    id: str
    source_node_id: str
    target_node_id: str
    relationship_type: RelationshipType
    weight: float = 1.0
    metadata: dict[str, Any] = Field(default_factory=dict)


class Evidence(_Base):
    """A pointer from a graph claim back to the post(s) that support it."""

    id: str
    subject_id: str  # concept/entity/relationship this supports
    post_dedup_key: str
    excerpt: str | None = None
    weight: float = 1.0
    observed_at: datetime | None = None


class Metric(_Base):
    """A named numeric measurement attached to a node at a point in time."""

    subject_id: str
    name: str
    value: float
    observed_at: datetime


class TrendSignal(_Base):
    """A temporal signal describing how a concept/entity is moving."""

    subject_id: str
    direction: TrendDirection
    magnitude: float
    window: ScrapeWindow
    metadata: dict[str, Any] = Field(default_factory=dict)


# --------------------------------------------------------------------------- #
# AI Crawler memory & outputs
# --------------------------------------------------------------------------- #
class MemoryRecord(_Base):
    """A single unit of the AI Crawler's persistent memory.

    `memory_class` selects which store this belongs to. Persistent memory lives
    in the data layer — never inside the LLM.
    """

    id: str
    memory_class: MemoryClass
    created_at: datetime
    content: dict[str, Any]
    embedding_ref: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Hypothesis(_Base):
    """A belief the agent forms and revises as evidence accumulates."""

    id: str
    statement: str
    status: HypothesisStatus = HypothesisStatus.PROPOSED
    confidence: float = 0.0
    supporting_evidence_ids: list[str] = Field(default_factory=list)
    contradicting_evidence_ids: list[str] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class Prediction(_Base):
    """A forward-looking claim with a resolution window and later outcome."""

    id: str
    hypothesis_id: str | None = None
    statement: str
    confidence: float = 0.0
    horizon: ScrapeWindow
    outcome: PredictionOutcome = PredictionOutcome.PENDING
    created_at: datetime | None = None
    resolved_at: datetime | None = None


class TrendReport(_Base):
    """A generated trend-intelligence report (report memory)."""

    id: str
    title: str
    summary: str
    concept_ids: list[str] = Field(default_factory=list)
    hypothesis_ids: list[str] = Field(default_factory=list)
    prediction_ids: list[str] = Field(default_factory=list)
    generated_at: datetime | None = None
    body: str | None = None


# --------------------------------------------------------------------------- #
# Embeddings
# --------------------------------------------------------------------------- #
class EmbeddingVector(_Base):
    """A dense vector plus provenance for storage in a vector repository."""

    subject_id: str
    provider: str
    model: str
    dim: int
    values: list[float]

    def model_post_init(self, _context: object) -> None:
        if len(self.values) != self.dim:
            raise ValueError(f"embedding length {len(self.values)} does not match dim {self.dim}")
