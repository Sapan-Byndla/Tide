"""Constraints and relationships across the schema (uniqueness, FKs, checks)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from backend.db.models.catalog import Source
from backend.db.models.content import Author, Post
from backend.db.models.graph import GraphEdge
from backend.db.models.timeseries import TimeSeriesObservation
from sqlalchemy.exc import IntegrityError

pytestmark = pytest.mark.db

NOW = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)


def _source(db_session, key: str = "reddit") -> Source:  # type: ignore[no-untyped-def]
    src = Source(id=uuid.uuid4(), source_key=key, display_name=key, source_type="social")
    db_session.add(src)
    db_session.flush()
    return src


def test_source_key_is_unique(db_session) -> None:  # type: ignore[no-untyped-def]
    _source(db_session, "reddit")
    db_session.add(Source(id=uuid.uuid4(), source_key="reddit", display_name="x", source_type="s"))
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_post_source_external_is_unique_idempotent_ingestion(db_session) -> None:  # type: ignore[no-untyped-def]
    src = _source(db_session)
    db_session.add(Post(id=uuid.uuid4(), source_id=src.id, external_id="abc"))
    db_session.flush()
    db_session.add(Post(id=uuid.uuid4(), source_id=src.id, external_id="abc"))
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_post_requires_valid_source_fk(db_session) -> None:  # type: ignore[no-untyped-def]
    db_session.add(Post(id=uuid.uuid4(), source_id=uuid.uuid4(), external_id="x"))
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_author_source_external_is_unique(db_session) -> None:  # type: ignore[no-untyped-def]
    src = _source(db_session)
    db_session.add(Author(id=uuid.uuid4(), source_id=src.id, external_author_id="u1"))
    db_session.flush()
    db_session.add(Author(id=uuid.uuid4(), source_id=src.id, external_author_id="u1"))
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_timeseries_bucket_is_unique(db_session) -> None:  # type: ignore[no-untyped-def]
    subject = uuid.uuid4()
    kw = {
        "subject_type": "concept",
        "subject_id": subject,
        "granularity": "day",
        "bucket_start": NOW,
    }
    db_session.add(TimeSeriesObservation(id=uuid.uuid4(), **kw))
    db_session.flush()
    db_session.add(TimeSeriesObservation(id=uuid.uuid4(), **kw))
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_graph_edge_node_type_check_constraint(db_session) -> None:  # type: ignore[no-untyped-def]
    db_session.add(
        GraphEdge(
            id=uuid.uuid4(),
            source_node_type="banana",
            source_node_id=uuid.uuid4(),
            target_node_type="concept",
            target_node_id=uuid.uuid4(),
            relationship_type="related_to",
        )
    )
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_timeseries_granularity_check_constraint(db_session) -> None:  # type: ignore[no-untyped-def]
    db_session.add(
        TimeSeriesObservation(
            id=uuid.uuid4(),
            subject_type="concept",
            subject_id=uuid.uuid4(),
            granularity="fortnight",
            bucket_start=NOW,
        )
    )
    with pytest.raises(IntegrityError):
        db_session.flush()
