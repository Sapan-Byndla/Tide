"""Enumerations shared across every TIDE subsystem.

These are stable vocabulary types referenced by domain models and interfaces.
Keeping them dependency-free means every subsystem can import them without
pulling in framework or infrastructure code.
"""

from __future__ import annotations

from enum import StrEnum


class SourceType(StrEnum):
    """The kind of external source a scraper collects from."""

    RSS = "rss"
    FORUM = "forum"
    SOCIAL = "social"
    NEWS = "news"
    BLOG = "blog"
    OTHER = "other"


class CollectionMode(StrEnum):
    """Which of the two fundamentally separate collection workflows is running."""

    HISTORICAL_BOOTSTRAP = "historical_bootstrap"
    DAILY = "daily"


class PostStatus(StrEnum):
    """Lifecycle status of a raw post as it moves through the pipeline."""

    COLLECTED = "collected"
    NORMALIZED = "normalized"
    PROCESSED = "processed"
    FAILED = "failed"


class CheckpointStatus(StrEnum):
    """State of a resumable collection checkpoint."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class EntityType(StrEnum):
    """Coarse classification of an extracted entity."""

    PERSON = "person"
    ORGANIZATION = "organization"
    PRODUCT = "product"
    TECHNOLOGY = "technology"
    LOCATION = "location"
    EVENT = "event"
    TOPIC = "topic"
    OTHER = "other"


class RelationshipType(StrEnum):
    """Edge semantics in the concept graph."""

    MENTIONS = "mentions"
    RELATED_TO = "related_to"
    PART_OF = "part_of"
    CAUSES = "causes"
    PRECEDES = "precedes"
    CONTRASTS_WITH = "contrasts_with"
    DERIVED_FROM = "derived_from"


class MemoryClass(StrEnum):
    """The five persistent memory classes of the AI Crawler.

    The underlying LLM is NOT a memory class — persistent memory lives in the
    application data layer, never in model weights or a context window.
    """

    EPISODIC = "episodic"  # what the agent observed and did
    SEMANTIC = "semantic"  # concepts, entities, relationships, embeddings
    HYPOTHESIS = "hypothesis"  # beliefs and supporting/contradicting evidence
    PREDICTIVE = "predictive"  # predictions and later outcomes
    REPORT = "report"  # historical trend analyses and conclusions


class HypothesisStatus(StrEnum):
    """Lifecycle of an agent hypothesis as evidence accumulates."""

    PROPOSED = "proposed"
    SUPPORTED = "supported"
    CONTESTED = "contested"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"


class PredictionOutcome(StrEnum):
    """Resolution of a prediction once the outcome window closes."""

    PENDING = "pending"
    CORRECT = "correct"
    INCORRECT = "incorrect"
    PARTIAL = "partial"
    UNRESOLVED = "unresolved"


class TrendDirection(StrEnum):
    """Direction of a temporal signal on a concept or entity."""

    RISING = "rising"
    FALLING = "falling"
    STABLE = "stable"
    VOLATILE = "volatile"
