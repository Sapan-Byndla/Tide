"""LLM provider contract.

The LLM is a **stateless reasoning engine** used by the AI Crawler. It is
explicitly NOT persistent memory: nothing durable is stored in the model or its
context window. Persistent memory belongs to the data layer (see
``contracts.memory``).

The provider is replaceable with NO lock-in to any paid vendor — local models,
self-hosted, or hosted APIs must all be able to satisfy this interface.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field


@dataclass(frozen=True)
class LLMMessage:
    """A single chat message."""

    role: str  # "system" | "user" | "assistant" | "tool"
    content: str


@dataclass(frozen=True)
class LLMResponse:
    """A non-streaming completion result."""

    text: str
    model: str
    usage: dict[str, int] = field(default_factory=dict)
    metadata: dict[str, object] = field(default_factory=dict)


class LLMProvider(ABC):
    """Provider-agnostic text generation."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider identifier (e.g. ``"noop"``, ``"local"``)."""

    @property
    @abstractmethod
    def model(self) -> str:
        """Active model identifier."""

    @abstractmethod
    async def complete(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.0,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        """Return a single completion for the given messages."""

    @abstractmethod
    async def stream(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.0,
        max_tokens: int | None = None,
    ) -> AsyncIterator[str]:
        """Yield completion text incrementally."""
