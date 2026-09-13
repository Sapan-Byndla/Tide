"""TIDE Intelligence Processing — raw posts into structured knowledge.

Responsibility
--------------
Convert collected :class:`contracts.models.RawPost` objects into normalized data,
entities, concepts, embeddings, relationships, and metrics — the inputs the
concept graph is built from.

Boundaries
----------
* Consumes raw posts (from scrapers) and produces domain objects for the graph.
* Depends on ports only: ``PostNormalizer``, ``EmbeddingProvider``. It never
  reaches into a scraper or the graph's storage directly.
* Contains no LLM calls that require a specific vendor; embeddings go through the
  replaceable ``EmbeddingProvider`` port.

Structure
---------
* ``intelligence.pipeline`` — the (Phase 0 stub) orchestration of
  normalize → extract → embed → relate.

Phase 0 status: pipeline contract/skeleton only; no extraction models are run.
"""

from __future__ import annotations

from intelligence.pipeline import IntelligencePipeline

__all__ = ["IntelligencePipeline"]
