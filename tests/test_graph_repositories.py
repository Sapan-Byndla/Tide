"""In-memory reference adapters behave per the port contracts."""

from __future__ import annotations

import pytest
from contracts.models import Concept, EmbeddingVector
from graph.repositories import InMemoryGraphRepository, InMemoryVectorRepository

# `asyncio_mode = auto` (pyproject) runs async tests without explicit marks, so
# no module-level asyncio mark is needed (it would also leak onto sync tests).


async def test_graph_upsert_and_get_concept() -> None:
    repo = InMemoryGraphRepository()
    concept = Concept(id="c1", label="edge computing")
    await repo.upsert_concept(concept)
    fetched = await repo.get_concept("c1")
    assert fetched is not None
    assert fetched.label == "edge computing"


async def test_vector_query_orders_by_similarity() -> None:
    repo = InMemoryVectorRepository()
    await repo.upsert(
        EmbeddingVector(subject_id="a", provider="noop", model="m", dim=2, values=[1.0, 0.0])
    )
    await repo.upsert(
        EmbeddingVector(subject_id="b", provider="noop", model="m", dim=2, values=[0.0, 1.0])
    )

    results = await repo.query([1.0, 0.0], top_k=2)
    assert results[0].subject_id == "a"
    assert results[0].score >= results[1].score


def test_embedding_dim_mismatch_is_rejected() -> None:
    with pytest.raises(ValueError):
        EmbeddingVector(subject_id="x", provider="noop", model="m", dim=3, values=[1.0, 2.0])
