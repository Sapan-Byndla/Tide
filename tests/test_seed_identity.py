"""Deterministic, stable seed/source identifiers."""

from __future__ import annotations

from backend.seeds.identity import seed_key, seed_uuid, slugify, source_uuid


def test_slugify_is_stable_and_safe() -> None:
    assert slugify("MachineLearning") == "machinelearning"
    assert slugify("cs.AI") == "cs.ai"
    assert slugify("google-cloud") == "google-cloud"
    assert slugify("Front Page") == "front_page"


def test_seed_key_format() -> None:
    assert seed_key("topic", None, "llms") == "topic:llms"
    assert seed_key("community", "reddit", "MachineLearning") == "reddit:community:machinelearning"
    assert seed_key("category", "arxiv", "cs.AI") == "arxiv:category:cs.ai"


def test_seed_uuid_is_deterministic() -> None:
    a = seed_uuid("topic:llms")
    b = seed_uuid("topic:llms")
    c = seed_uuid("topic:rag")
    assert a == b
    assert a != c
    # Not dependent on wall clock / db: same input -> same output across calls.
    assert str(a) == str(seed_uuid("topic:llms"))


def test_source_uuid_is_deterministic() -> None:
    assert source_uuid("reddit") == source_uuid("reddit")
    assert source_uuid("reddit") != source_uuid("github")
