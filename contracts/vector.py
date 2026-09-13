"""Vector repository contract.

Semantic retrieval store for embeddings. Backed by pgvector initially (living in
the same PostgreSQL instance as the graph), but the interface admits any
approximate-nearest-neighbour backend later.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass

from contracts.models import EmbeddingVector


@dataclass(frozen=True)
class VectorMatch:
    """A single nearest-neighbour search result."""

    subject_id: str
    score: float


class VectorRepository(ABC):
    """Stores embedding vectors and answers similarity queries."""

    @abstractmethod
    async def upsert(self, vector: EmbeddingVector) -> None:
        """Insert or update a single vector keyed by ``subject_id``."""

    @abstractmethod
    async def upsert_many(self, vectors: Sequence[EmbeddingVector]) -> None:
        """Batch upsert."""

    @abstractmethod
    async def query(self, embedding: Sequence[float], top_k: int = 10) -> list[VectorMatch]:
        """Return the ``top_k`` most similar stored vectors."""

    @abstractmethod
    async def delete(self, subject_id: str) -> None:
        """Remove a vector by subject id."""
