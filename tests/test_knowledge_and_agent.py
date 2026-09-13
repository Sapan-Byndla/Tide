"""Discovered knowledge is independent of seeds; graph is temporal; agent memory works."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from backend.db.models.agent import (
    AgentHypothesis,
    AgentPrediction,
    AgentRun,
)
from backend.db.models.graph import GraphEdge
from backend.db.models.knowledge import Concept, Entity

pytestmark = pytest.mark.db

NOW = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)


def test_concept_can_be_discovered_without_a_seed(db_session) -> None:  # type: ignore[no-untyped-def]
    c = Concept(
        id=uuid.uuid4(),
        canonical_name="agentic memory",
        origin="discovered",
        seed_id=None,
        status="discovered",
    )
    db_session.add(c)
    db_session.flush()
    fetched = db_session.get(Concept, c.id)
    assert fetched is not None
    assert fetched.seed_id is None
    assert fetched.origin == "discovered"


def test_entity_is_independent_of_seed_list(db_session) -> None:  # type: ignore[no-untyped-def]
    e = Entity(id=uuid.uuid4(), canonical_name="OpenAI", entity_type="organization")
    db_session.add(e)
    db_session.flush()
    assert db_session.get(Entity, e.id) is not None


def test_graph_edge_is_temporal(db_session) -> None:  # type: ignore[no-untyped-def]
    a, b = uuid.uuid4(), uuid.uuid4()
    edge = GraphEdge(
        id=uuid.uuid4(),
        source_node_type="concept",
        source_node_id=a,
        target_node_type="concept",
        target_node_id=b,
        relationship_type="related_to",
        weight=0.4,
        evidence_count=2,
        first_observed_at=NOW,
        last_observed_at=datetime(2026, 7, 5, tzinfo=UTC),
    )
    db_session.add(edge)
    db_session.flush()
    got = db_session.get(GraphEdge, edge.id)
    assert got.first_observed_at is not None
    assert got.last_observed_at > got.first_observed_at


def test_agent_memory_records_and_prediction_evaluation_fields(db_session) -> None:  # type: ignore[no-untyped-def]
    run = AgentRun(id=uuid.uuid4(), status="completed", trigger="test")
    db_session.add(run)
    db_session.flush()

    hyp = AgentHypothesis(
        id=uuid.uuid4(),
        run_id=run.id,
        statement="X will rise",
        status="proposed",
        confidence=0.6,
    )
    db_session.add(hyp)
    db_session.flush()

    pred = AgentPrediction(
        id=uuid.uuid4(),
        run_id=run.id,
        hypothesis_id=hyp.id,
        statement="X doubles in 30 days",
        confidence=0.6,
        evaluation_at=datetime(2026, 8, 1, tzinfo=UTC),
        status="pending",
    )
    db_session.add(pred)
    db_session.flush()

    # Prediction is designed to be evaluated later: resolve it.
    pred.status = "correct"
    pred.actual_outcome = "doubled on day 21"
    pred.resolved_at = datetime(2026, 7, 22, tzinfo=UTC)
    pred.evaluation_metadata = {"method": "manual"}
    db_session.flush()

    stored = db_session.get(AgentPrediction, pred.id)
    assert stored.status == "correct"
    assert stored.actual_outcome == "doubled on day 21"
    assert stored.resolved_at is not None
    # Relationship wiring holds.
    assert stored.run_id == run.id
    assert stored.hypothesis_id == hyp.id
    assert db_session.get(AgentRun, run.id).predictions[0].id == pred.id


def test_prediction_status_check_constraint(db_session) -> None:  # type: ignore[no-untyped-def]
    from sqlalchemy.exc import IntegrityError

    run = AgentRun(id=uuid.uuid4(), status="completed")
    db_session.add(run)
    db_session.flush()
    db_session.add(
        AgentPrediction(
            id=uuid.uuid4(),
            run_id=run.id,
            statement="bad",
            status="maybe",
        )
    )
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_run_status_check_constraint(db_session) -> None:  # type: ignore[no-untyped-def]
    from sqlalchemy.exc import IntegrityError

    db_session.add(AgentRun(id=uuid.uuid4(), status="not_a_status"))
    with pytest.raises(IntegrityError):
        db_session.flush()
