"""Trend analyzer contract — the AI Crawler's reasoning surface.

The AI Crawler is NOT a scraper. It reads and traverses the concept graph,
retrieves historical evidence and relevant posts, detects anomalies and emerging
patterns, forms and revises hypotheses, updates confidence, makes predictions,
persists memory, and generates trend intelligence.

This interface collaborates with (never bypasses):

* :class:`contracts.graph.GraphRepository`   — to traverse the graph
* :class:`contracts.vector.VectorRepository` — to retrieve relevant evidence
* :class:`contracts.memory.AgentMemory`       — to read/write persistent memory
* :class:`contracts.llm.LLMProvider`          — as a stateless reasoning engine
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from contracts.models import (
    Hypothesis,
    Prediction,
    ScrapeWindow,
    TrendReport,
    TrendSignal,
)


class TrendAnalyzer(ABC):
    """Contract for the trend-intelligence agent (implemented in later phases)."""

    @abstractmethod
    async def detect_signals(self, window: ScrapeWindow) -> Sequence[TrendSignal]:
        """Scan the graph over ``window`` for anomalies / emerging patterns."""

    @abstractmethod
    async def form_hypotheses(self, signals: Sequence[TrendSignal]) -> Sequence[Hypothesis]:
        """Turn detected signals into candidate hypotheses."""

    @abstractmethod
    async def evaluate_hypothesis(self, hypothesis: Hypothesis) -> Hypothesis:
        """Gather evidence and update a hypothesis's status and confidence."""

    @abstractmethod
    async def predict(self, hypothesis: Hypothesis) -> Prediction:
        """Produce a forward-looking prediction from a hypothesis."""

    @abstractmethod
    async def generate_report(self, window: ScrapeWindow) -> TrendReport:
        """Synthesize current intelligence into a trend report."""
