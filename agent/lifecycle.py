"""AI Crawler conceptual lifecycle (Phase 0 skeleton).

This module names and orders the stages of the trend-analysis loop and declares
the ports each stage depends on. It performs no reasoning in Phase 0 — every
stage raises ``NotImplementedError``. Its value now is to pin down the
collaboration boundaries so later phases implement into a known shape.

Lifecycle
---------
1. **Observe**    — traverse the graph over a window; pull relevant evidence
   (``GraphRepository`` + ``VectorRepository``); log to episodic memory.
2. **Hypothesize** — turn anomalies/signals into hypotheses (``TrendAnalyzer``);
   store in hypothesis memory.
3. **Evaluate**   — gather supporting/contradicting evidence; update confidence.
4. **Predict**    — emit predictions with a resolution horizon; store in
   predictive memory.
5. **Report**     — synthesize a trend report; store in report memory.

The ``LLMProvider`` is used only as a stateless reasoning engine within stages;
durable state always goes through ``AgentMemory`` / the graph.
"""

from __future__ import annotations

from contracts.analyzer import TrendAnalyzer
from contracts.graph import GraphRepository
from contracts.llm import LLMProvider
from contracts.memory import AgentMemory
from contracts.models import ScrapeWindow, TrendReport
from contracts.vector import VectorRepository


class AgentLifecycle:
    """Wires the AI Crawler's dependencies; runs its loop (in later phases)."""

    def __init__(
        self,
        analyzer: TrendAnalyzer,
        graph: GraphRepository,
        vectors: VectorRepository,
        memory: AgentMemory,
        llm: LLMProvider,
    ) -> None:
        self._analyzer = analyzer
        self._graph = graph
        self._vectors = vectors
        self._memory = memory
        self._llm = llm

    async def run_cycle(self, window: ScrapeWindow) -> TrendReport:
        """Execute one observe→hypothesize→evaluate→predict→report cycle.

        Not implemented in Phase 0 — the trend-analysis agent is explicitly out of
        scope for this phase.
        """
        raise NotImplementedError(
            "AI Crawler reasoning is implemented in a later phase, not Phase 0."
        )
