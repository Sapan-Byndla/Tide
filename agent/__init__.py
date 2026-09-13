"""TIDE AI Crawler / Trend Analyst.

Responsibility
--------------
Read and traverse the concept graph, retrieve historical evidence and relevant
posts, detect anomalies and emerging patterns, form and revise hypotheses, update
confidence, make predictions, persist memory, and generate trend intelligence.

The AI Crawler is NOT a scraper
-------------------------------
It never contacts external platforms. It operates entirely on internal state via
ports: ``GraphRepository``, ``VectorRepository``, ``AgentMemory``, and a
stateless ``LLMProvider``. Any external data it uses was collected earlier by the
scrapers and processed by the intelligence subsystem.

Persistent memory lives in the data layer, never in the LLM (see
``agent.memory`` conceptual notes and ``contracts.memory``).

Structure
---------
* ``agent.lifecycle`` — documents/skeletons the observe → hypothesize → evaluate
  → predict → report loop.

Phase 0 status: conceptual lifecycle + contracts only. No reasoning is performed
and no model is loaded.
"""

from __future__ import annotations

from agent.lifecycle import AgentLifecycle

__all__ = ["AgentLifecycle"]
