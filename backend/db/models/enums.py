"""Application-level enumerations for the persistence layer.

Design choice — extensible vocabularies are stored as ``String`` columns, not
Postgres ``ENUM`` types. TIDE must discover new concepts, entities, relationship
types, and even new seed/source types over time (the seed list is a *beachhead*,
not a fixed vocabulary). Native ENUMs would force an ``ALTER TYPE`` migration for
every new value, so open vocabularies use plain strings validated by these
enums at the application boundary.

Genuinely *closed* sets (graph node kinds, time-series granularity, run status,
prediction outcome) DO get CHECK constraints in the models — see each model.
"""

from __future__ import annotations

from enum import StrEnum

# Re-export the closed-set enums already defined in the contracts layer so the
# persistence layer and the domain layer agree on the same vocabulary.
from contracts.enums import (
    HypothesisStatus,
    PredictionOutcome,
)

__all__ = [
    "AgentRunStatus",
    "ConceptOrigin",
    "ConceptStatus",
    "EntityStatus",
    "Granularity",
    "HypothesisStatus",
    "NodeType",
    "OwnerType",
    "PredictionOutcome",
    "SeedOrigin",
    "SeedType",
    "SubjectType",
]


class SeedType(StrEnum):
    """Category of a curated seed. Open vocabulary (stored as string).

    Deliberately platform-agnostic: reddit subreddits and future Discord servers
    are both ``COMMUNITY``; SO tags and GitHub topics are both ``TAG``. New source
    types add a value here without any schema migration.
    """

    TOPIC = "topic"  # global conceptual seed, no source
    KEYWORD = "keyword"
    COMMUNITY = "community"  # subreddit, forum, server
    ACCOUNT = "account"  # x/youtube/github account
    CHANNEL = "channel"  # youtube channel, HN feed
    RSS_FEED = "rss_feed"
    TAG = "tag"  # SO tag, GitHub topic
    CATEGORY = "category"  # arxiv category
    SOURCE_TARGET = "source_target"  # generic future catch-all


class SeedOrigin(StrEnum):
    """Where a seed record came from."""

    SEED_LIST_YAML = "seed_list.yaml"
    MANUAL = "manual"
    PROMOTED = "promoted"  # future: promoted from a discovered concept


class ConceptOrigin(StrEnum):
    """Provenance of a concept node (curated vs discovered)."""

    DISCOVERED = "discovered"  # found by processing; NOT in the seed list
    SEED_LIST_YAML = "seed_list.yaml"  # derived from a curated seed
    MANUAL = "manual"


class ConceptStatus(StrEnum):
    """Lifecycle of a concept in the knowledge graph."""

    DISCOVERED = "discovered"
    CANDIDATE = "candidate"
    ACTIVE = "active"
    ARCHIVED = "archived"
    MERGED = "merged"


class EntityStatus(StrEnum):
    """Lifecycle of an entity in the knowledge graph."""

    DISCOVERED = "discovered"
    ACTIVE = "active"
    ARCHIVED = "archived"
    MERGED = "merged"


class NodeType(StrEnum):
    """Kinds of node a graph edge or observation can reference. CLOSED set."""

    CONCEPT = "concept"
    ENTITY = "entity"


class SubjectType(StrEnum):
    """What a time-series observation is about. CLOSED set."""

    CONCEPT = "concept"
    ENTITY = "entity"
    EDGE = "edge"


class Granularity(StrEnum):
    """Time-bucket size for observations. CLOSED set."""

    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


class OwnerType(StrEnum):
    """What an embedding vector belongs to. Open vocabulary."""

    POST = "post"
    CONCEPT = "concept"
    ENTITY = "entity"


class AgentRunStatus(StrEnum):
    """Lifecycle of an AI Crawler run. CLOSED set."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


def values(enum_cls: type[StrEnum]) -> list[str]:
    """Return the string values of an enum (used to build CHECK constraints)."""
    return [member.value for member in enum_cls]
