"""Validation of the real seed_list.yaml and the loader's warning behavior."""

from __future__ import annotations

from pathlib import Path

from backend.seeds.loader import (
    SeedType,
    flatten_seed_file,
    load_seed_file,
    validate_seed_file,
)

ROOT = Path(__file__).resolve().parents[1]
SEED_LIST = ROOT / "seed_list.yaml"


def test_real_seed_list_validates() -> None:
    result = validate_seed_file(SEED_LIST)
    assert result.ok, result.errors
    assert result.errors == []


def test_real_seed_list_flattens_topics_and_sources() -> None:
    parsed = load_seed_file(SEED_LIST)
    flat = flatten_seed_file(parsed)

    topics = [s for s in flat.seeds if s.seed_type == SeedType.TOPIC.value]
    assert len(topics) == len(parsed.topics)  # every topic became a seed
    assert len(topics) > 100  # the curated list is large

    source_keys = {s.source_key for s in flat.sources}
    assert {"reddit", "hacker_news", "stack_overflow", "github", "arxiv", "rss"} <= source_keys

    # Source-specific seeds carry a source and the right type.
    reddit_seeds = [s for s in flat.seeds if s.source_key == "reddit"]
    assert reddit_seeds and all(s.seed_type == SeedType.COMMUNITY.value for s in reddit_seeds)
    rss_seeds = [s for s in flat.seeds if s.seed_type == SeedType.RSS_FEED.value]
    assert rss_seeds and all(s.canonical_value.startswith("http") for s in rss_seeds)


def test_alias_collision_is_reported_as_warning_not_error() -> None:
    # 'AI benchmarks' is an alias of `ai_evals` but equals the canonical name of
    # the distinct topic `ai_benchmarks`. This must be a warning, not an error.
    result = validate_seed_file(SEED_LIST)
    assert result.ok
    assert any("ai_benchmarks" in w and "collides" in w for w in result.warnings)


def test_duplicate_topic_id_is_an_error(tmp_path: Path) -> None:
    bad = tmp_path / "seeds.yaml"
    bad.write_text(
        "version: 1\ntopics:\n  - id: dup\n    name: One\n  - id: dup\n    name: Two\n",
        encoding="utf-8",
    )
    result = validate_seed_file(bad)
    assert not result.ok
    assert any("duplicate topic id" in e for e in result.errors)


def test_malformed_file_is_an_error(tmp_path: Path) -> None:
    bad = tmp_path / "seeds.yaml"
    bad.write_text("version: 1\ntopics:\n  - id: x\n", encoding="utf-8")  # missing name
    result = validate_seed_file(bad)
    assert not result.ok
    assert result.errors


def test_unknown_source_platform_warns(tmp_path: Path) -> None:
    f = tmp_path / "seeds.yaml"
    f.write_text(
        "version: 1\ntopics: []\nsources:\n  mastodon:\n    accounts:\n      - someone\n",
        encoding="utf-8",
    )
    result = validate_seed_file(f)
    assert result.ok  # unknown platform is tolerated
    assert any("mastodon" in w for w in result.warnings)
