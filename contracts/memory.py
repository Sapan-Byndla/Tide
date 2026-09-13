"""AI Crawler persistent memory contract.

The AI Crawler has five persistent memory classes (see
:class:`contracts.enums.MemoryClass`):

* episodic   — what the agent observed and did
* semantic   — concepts, entities, relationships, embeddings
* hypothesis — beliefs and supporting/contradicting evidence
* predictive — predictions and later outcomes
* report     — historical trend analyses and conclusions

All of these live in the application data layer. The LLM is never treated as
memory. This interface is the single door through which the agent reads and
writes durable state.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from contracts.enums import MemoryClass
from contracts.models import MemoryRecord


class AgentMemory(ABC):
    """Read/write access to the agent's persistent memory stores."""

    @abstractmethod
    async def remember(self, record: MemoryRecord) -> MemoryRecord:
        """Persist a memory record into the store for its ``memory_class``."""

    @abstractmethod
    async def get(self, memory_class: MemoryClass, record_id: str) -> MemoryRecord | None:
        """Fetch a single record by id from a given memory class."""

    @abstractmethod
    async def recent(self, memory_class: MemoryClass, limit: int = 50) -> Sequence[MemoryRecord]:
        """Return the most recent records for a memory class."""

    @abstractmethod
    async def search(
        self,
        memory_class: MemoryClass,
        query: str,
        top_k: int = 10,
    ) -> Sequence[MemoryRecord]:
        """Semantic/keyword search within a memory class.

        Semantic search will delegate to a :class:`VectorRepository` in later
        phases; the contract does not mandate the retrieval mechanism.
        """
