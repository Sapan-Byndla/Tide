"""Demo data loads deterministically and is idempotent."""

from __future__ import annotations

import pytest
from backend.db.demo import load_demo_data
from backend.db.models.catalog import Source
from backend.db.models.knowledge import Concept
from sqlalchemy import func, select

pytestmark = pytest.mark.db


def _count(session, model) -> int:  # type: ignore[no-untyped-def]
    return session.execute(select(func.count()).select_from(model)).scalar_one()


def test_demo_data_loads(db_session) -> None:  # type: ignore[no-untyped-def]
    summary = load_demo_data(db_session)
    assert summary["concepts"] == 2
    # A DISCOVERED concept with no seed exists, and everything is marked demo.
    discovered = (
        db_session.execute(
            select(Concept).where(Concept.origin == "discovered", Concept.seed_id.is_(None))
        )
        .scalars()
        .all()
    )
    assert any(c.meta.get("demo") for c in discovered)
    # Demo sources use distinct demo_* keys.
    demo_sources = (
        db_session.execute(select(Source).where(Source.source_key.like("demo_%"))).scalars().all()
    )
    assert len(demo_sources) == 2


def test_demo_data_is_idempotent(db_session) -> None:  # type: ignore[no-untyped-def]
    load_demo_data(db_session)
    concepts_after_first = _count(db_session, Concept)
    load_demo_data(db_session)
    assert _count(db_session, Concept) == concepts_after_first
