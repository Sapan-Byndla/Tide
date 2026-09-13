"""TIDE shared contracts — the stable core of the architecture.

This package holds two dependency-free things every other subsystem agrees on:

1. **Domain models** (:mod:`contracts.models`, :mod:`contracts.enums`) — the
   canonical shape of a Post, Concept, Hypothesis, etc.
2. **Ports** (abstract interfaces) — ``BaseScraper``, ``PostNormalizer``,
   ``EmbeddingProvider``, ``GraphRepository``, ``VectorRepository``,
   ``ObjectStorage``, ``TrendAnalyzer``, ``AgentMemory``, ``LLMProvider``.

Nothing here imports a web framework, a database driver, or an LLM SDK. Concrete
adapters live in the subsystem packages (``scrapers``, ``intelligence``,
``graph``, ``agent``) and depend on this package — never the other way around.
This is the ports-and-adapters (hexagonal) boundary that lets implementations be
swapped without rewriting callers.
"""

from __future__ import annotations

from contracts.analyzer import TrendAnalyzer
from contracts.embeddings import EmbeddingProvider
from contracts.graph import GraphRepository
from contracts.llm import LLMMessage, LLMProvider, LLMResponse
from contracts.memory import AgentMemory
from contracts.normalizer import PostNormalizer
from contracts.scrapers import BaseScraper, DailyScraper, HistoricalScraper
from contracts.storage import ObjectStorage
from contracts.vector import VectorMatch, VectorRepository

__all__ = [
    "AgentMemory",
    "BaseScraper",
    "DailyScraper",
    "EmbeddingProvider",
    "GraphRepository",
    "HistoricalScraper",
    "LLMMessage",
    "LLMProvider",
    "LLMResponse",
    "ObjectStorage",
    "PostNormalizer",
    "TrendAnalyzer",
    "VectorMatch",
    "VectorRepository",
]
