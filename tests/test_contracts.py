"""The abstract contracts exist, are abstract, and are implementable.

We assert both that the ports cannot be instantiated directly (they are true
ABCs with abstract methods) and that a trivial concrete implementation can
satisfy them — proving the interfaces are coherent for later phases.
"""

from __future__ import annotations

import inspect

import pytest
from contracts import (
    AgentMemory,
    BaseScraper,
    DailyScraper,
    EmbeddingProvider,
    GraphRepository,
    HistoricalScraper,
    LLMProvider,
    ObjectStorage,
    PostNormalizer,
    TrendAnalyzer,
    VectorRepository,
)

PORTS = [
    AgentMemory,
    BaseScraper,
    DailyScraper,
    EmbeddingProvider,
    GraphRepository,
    HistoricalScraper,
    LLMProvider,
    ObjectStorage,
    PostNormalizer,
    TrendAnalyzer,
    VectorRepository,
]


@pytest.mark.parametrize("port", PORTS, ids=lambda p: p.__name__)
def test_ports_are_abstract(port: type) -> None:
    assert inspect.isabstract(port), f"{port.__name__} should have abstract methods"
    with pytest.raises(TypeError):
        port()  # type: ignore[abstract,call-arg]


def test_inmemory_adapters_satisfy_ports() -> None:
    from graph.repositories import InMemoryGraphRepository, InMemoryVectorRepository

    assert isinstance(InMemoryGraphRepository(), GraphRepository)
    assert isinstance(InMemoryVectorRepository(), VectorRepository)
