"""Concept graph repository contract.

The concept graph is the persistent representation of concepts, entities,
relationships, temporal signals, evidence, and metrics.

Architectural decision: the graph initially lives in **PostgreSQL** (nodes and
edges as relational tables), NOT a dedicated graph database. This interface hides
that choice so a graph-native backend could replace it later without touching
callers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from contracts.models import (
    Concept,
    Entity,
    Evidence,
    Metric,
    Relationship,
    TrendSignal,
)


class GraphRepository(ABC):
    """Persistence and traversal contract for the concept graph."""

    # ---- node upserts ----
    @abstractmethod
    async def upsert_entity(self, entity: Entity) -> Entity:
        """Insert or update an entity node."""

    @abstractmethod
    async def upsert_concept(self, concept: Concept) -> Concept:
        """Insert or update a concept node."""

    @abstractmethod
    async def upsert_relationship(self, relationship: Relationship) -> Relationship:
        """Insert or update a directed edge."""

    # ---- attachments ----
    @abstractmethod
    async def add_evidence(self, evidence: Evidence) -> Evidence:
        """Attach supporting evidence to a node/edge."""

    @abstractmethod
    async def record_metric(self, metric: Metric) -> None:
        """Record a time-stamped metric for a node."""

    @abstractmethod
    async def record_signal(self, signal: TrendSignal) -> None:
        """Record a temporal trend signal for a node."""

    # ---- reads / traversal (used by the AI Crawler) ----
    @abstractmethod
    async def get_concept(self, concept_id: str) -> Concept | None:
        """Fetch a concept by id."""

    @abstractmethod
    async def neighbors(self, node_id: str, depth: int = 1) -> Sequence[Relationship]:
        """Return edges reachable from ``node_id`` up to ``depth`` hops."""

    @abstractmethod
    async def evidence_for(self, subject_id: str) -> Sequence[Evidence]:
        """Return evidence attached to a node/edge."""
