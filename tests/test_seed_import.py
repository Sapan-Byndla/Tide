"""Seed importer: creation, idempotency, deterministic IDs, non-destructive removal."""

from __future__ import annotations

from pathlib import Path

import pytest
from backend.db.models.catalog import Seed, Source
from backend.seeds.identity import seed_uuid
from backend.seeds.importer import import_seeds
from sqlalchemy import func, select

pytestmark = pytest.mark.db

ROOT = Path(__file__).resolve().parents[1]
SEED_LIST = str(ROOT / "seed_list.yaml")


def _count(session, model) -> int:  # type: ignore[no-untyped-def]
    return session.execute(select(func.count()).select_from(model)).scalar_one()


def test_import_creates_sources_and_seeds(db_session) -> None:  # type: ignore[no-untyped-def]
    report = import_seeds(db_session, SEED_LIST)
    assert report.seeds_created > 100
    assert report.sources_created >= 6
    assert _count(db_session, Seed) == report.seeds_created
    assert _count(db_session, Source) >= 6


def test_import_is_idempotent(db_session) -> None:  # type: ignore[no-untyped-def]
    first = import_seeds(db_session, SEED_LIST)
    total = _count(db_session, Seed)

    second = import_seeds(db_session, SEED_LIST)
    assert second.seeds_created == 0
    assert second.seeds_updated == 0
    assert second.seeds_unchanged == first.seeds_created
    assert _count(db_session, Seed) == total  # no duplicates


def test_seed_ids_are_deterministic(db_session) -> None:  # type: ignore[no-untyped-def]
    import_seeds(db_session, SEED_LIST)
    row = db_session.execute(select(Seed).where(Seed.key == "topic:llms")).scalar_one()
    assert row.id == seed_uuid("topic:llms")
    assert row.origin == "seed_list.yaml"
    assert row.source_id is None  # topics are global (no source)


def test_removed_seed_is_deactivated_not_deleted(db_session, tmp_path) -> None:  # type: ignore[no-untyped-def]
    import_seeds(db_session, SEED_LIST)
    total_before = _count(db_session, Seed)

    smaller = tmp_path / "seeds.yaml"
    smaller.write_text(
        "version: 2\ntopics:\n  - id: llms\n    name: Large Language Models\n",
        encoding="utf-8",
    )
    report = import_seeds(db_session, str(smaller), deactivate_missing=True)

    # Nothing deleted; the vanished seeds are disabled instead.
    assert _count(db_session, Seed) == total_before
    assert report.seeds_deactivated > 0
    rag = db_session.execute(select(Seed).where(Seed.key == "topic:rag")).scalar_one()
    assert rag.enabled is False
    assert rag.config.get("removed_from_seed_list") is True
    # The surviving seed stays enabled.
    llms = db_session.execute(select(Seed).where(Seed.key == "topic:llms")).scalar_one()
    assert llms.enabled is True
