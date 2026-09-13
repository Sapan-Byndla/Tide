"""In-memory reference adapters for the graph & vector ports.

These are NOT the production stores. They are dependency-free reference
implementations that:

* prove the ``GraphRepository`` / ``VectorRepository`` contracts are satisfiable,
* give tests and local development something real to run against, and
* document expected semantics (upsert-by-id, cosine similarity ordering).

The PostgreSQL/pgvector adapters that replace these arrive in a later phase and
plug into the exact same ports.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

from contracts.graph import GraphRepository
from contracts.models import (
    Concept,
    EmbeddingVector,
    Entity,
    Evidence,
    Metric,
    Relationship,
    TrendSignal,
)
from contracts.vector import VectorMatch, VectorRepository


class InMemoryGraphRepository(GraphRepository):
    """Dict-backed graph store for tests and local runs."""

    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.concepts: dict[str, Concept] = {}
        self.relationships: dict[str, Relationship] = {}
        self.evidence: list[Evidence] = []
        self.metrics: list[Metric] = []
        self.signals: list[TrendSignal] = []

    async def upsert_entity(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    async def upsert_concept(self, concept: Concept) -> Concept:
        self.concepts[concept.id] = concept
        return concept

    async def upsert_relationship(self, relationship: Relationship) -> Relationship:
        self.relationships[relationship.id] = relationship
        return relationship

    async def add_evidence(self, evidence: Evidence) -> Evidence:
        self.evidence.append(evidence)
        return evidence

    async def record_metric(self, metric: Metric) -> None:
        self.metrics.append(metric)

    async def record_signal(self, signal: TrendSignal) -> None:
        self.signals.append(signal)

    async def get_concept(self, concept_id: str) -> Concept | None:
        return self.concepts.get(concept_id)

    async def neighbors(self, node_id: str, depth: int = 1) -> Sequence[Relationship]:
        # Phase 0: single-hop only; multi-hop traversal lands with the SQL adapter.
        return [
            rel
            for rel in self.relationships.values()
            if rel.source_node_id == node_id or rel.target_node_id == node_id
        ]

    async def evidence_for(self, subject_id: str) -> Sequence[Evidence]:
        return [ev for ev in self.evidence if ev.subject_id == subject_id]


class InMemoryVectorRepository(VectorRepository):
    """Dict-backed vector store using exact cosine similarity."""

    def __init__(self) -> None:
        self._vectors: dict[str, EmbeddingVector] = {}

    async def upsert(self, vector: EmbeddingVector) -> None:
        self._vectors[vector.subject_id] = vector

    async def upsert_many(self, vectors: Sequence[EmbeddingVector]) -> None:
        for vector in vectors:
            self._vectors[vector.subject_id] = vector

    async def query(self, embedding: Sequence[float], top_k: int = 10) -> list[VectorMatch]:
        scored = [
            VectorMatch(subject_id=sid, score=_cosine(embedding, vec.values))
            for sid, vec in self._vectors.items()
        ]
        scored.sort(key=lambda m: m.score, reverse=True)
        return scored[:top_k]

    async def delete(self, subject_id: str) -> None:
        self._vectors.pop(subject_id, None)


def _cosine(a: Sequence[float], b: Sequence[float]) -> float:
    """Cosine similarity; returns 0.0 for mismatched or zero vectors."""
    if len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)
