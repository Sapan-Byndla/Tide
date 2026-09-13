"""Embedding provider contract.

Embeddings power semantic retrieval (pgvector) and the agent's semantic memory.
The provider is replaceable — local model, hosted API, or a no-op stub — with no
lock-in to any paid vendor.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from contracts.models import EmbeddingVector


class EmbeddingProvider(ABC):
    """Produces dense vectors for text."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider identifier (e.g. ``"noop"``, ``"local"``)."""

    @property
    @abstractmethod
    def model(self) -> str:
        """Model identifier used for provenance on stored vectors."""

    @property
    @abstractmethod
    def dim(self) -> int:
        """Dimensionality of the vectors this provider produces."""

    @abstractmethod
    async def embed(self, subject_id: str, text: str) -> EmbeddingVector:
        """Embed a single piece of text."""

    @abstractmethod
    async def embed_batch(self, items: Sequence[tuple[str, str]]) -> list[EmbeddingVector]:
        """Embed a batch of ``(subject_id, text)`` pairs."""
