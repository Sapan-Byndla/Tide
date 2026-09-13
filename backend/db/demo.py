"""Deterministic development/demo data.

This is DEVELOPMENT DATA, not the curated seed list. Every row is:

* deterministic — fixed ``uuid5`` ids, fixed timestamps (no wall clock),
* idempotent    — loaded via "insert if missing" so re-running never duplicates,
* clearly marked — ``meta['demo'] = True`` and ``[DEMO]`` in human-readable names,
* distinct      — demo sources use ``demo_*`` keys so they never collide with
  sources created by importing the real ``seed_list.yaml``.

It exercises every table so developers have something realistic to query.
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session
from storage.keys import build_raw_key

from backend.db.base import Base
from backend.db.models.agent import (
    AgentHypothesis,
    AgentObservation,
    AgentPrediction,
    AgentReport,
    AgentRun,
)
from backend.db.models.catalog import Seed, Source
from backend.db.models.content import Author, Post
from backend.db.models.embeddings import Embedding
from backend.db.models.enums import (
    ConceptOrigin,
    Granularity,
    NodeType,
    SubjectType,
)
from backend.db.models.evidence import PostConcept, PostEntity
from backend.db.models.graph import GraphEdge
from backend.db.models.knowledge import Concept, Entity
from backend.db.models.timeseries import TimeSeriesObservation
from backend.seeds.identity import TIDE_NAMESPACE

DEMO_FLAG = {"demo": True}


def demo_uuid(slug: str) -> uuid.UUID:
    """Deterministic id for a demo row."""
    return uuid.uuid5(TIDE_NAMESPACE, f"demo:{slug}")


def _dt(y: int, m: int, d: int) -> datetime:
    return datetime(y, m, d, 12, 0, 0, tzinfo=UTC)


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _ensure(session: Session, model: type[Base], obj_id: uuid.UUID, obj: Base) -> Base:
    """Insert ``obj`` only if a row with ``obj_id`` doesn't already exist.

    Flushes immediately so inserts follow this module's dependency order. Evidence
    and graph rows reference nodes by raw id (no ORM relationship to order the
    unit-of-work), and the app session uses ``autoflush=False``, so an explicit
    flush here is what guarantees parents exist before children.
    """
    existing = session.get(model, obj_id)
    if existing is not None:
        return existing
    session.add(obj)
    session.flush()
    return obj


def load_demo_data(session: Session) -> dict[str, Any]:
    """Load the full demo dataset. Returns a small summary. Idempotent."""
    # ---- sources (distinct demo_* keys) ----
    src_reddit = demo_uuid("source:demo_reddit")
    src_hn = demo_uuid("source:demo_hn")
    _ensure(
        session,
        Source,
        src_reddit,
        Source(
            id=src_reddit,
            source_key="demo_reddit",
            display_name="[DEMO] Reddit",
            source_type="social",
            enabled=True,
            meta=DEMO_FLAG,
        ),
    )
    _ensure(
        session,
        Source,
        src_hn,
        Source(
            id=src_hn,
            source_key="demo_hn",
            display_name="[DEMO] Hacker News",
            source_type="aggregator",
            enabled=True,
            meta=DEMO_FLAG,
        ),
    )

    # ---- a demo seed (origin manual; NOT from seed_list.yaml) ----
    seed_id = demo_uuid("seed:ai-agents")
    _ensure(
        session,
        Seed,
        seed_id,
        Seed(
            id=seed_id,
            key="demo:topic:ai-agents",
            name="[DEMO] AI Agents",
            seed_type="topic",
            source_id=None,
            canonical_value="demo_ai_agents",
            aliases=["agentic AI"],
            priority=100,
            enabled=True,
            origin="manual",
            config=DEMO_FLAG,
        ),
    )

    # ---- authors ----
    author_a = demo_uuid("author:a")
    author_b = demo_uuid("author:b")
    _ensure(
        session,
        Author,
        author_a,
        Author(
            id=author_a,
            source_id=src_reddit,
            external_author_id="u_alice",
            username="alice",
            display_name="[DEMO] Alice",
            meta=DEMO_FLAG,
        ),
    )
    _ensure(
        session,
        Author,
        author_b,
        Author(
            id=author_b,
            source_id=src_hn,
            external_author_id="hn_bob",
            username="bob",
            display_name="[DEMO] Bob",
            meta=DEMO_FLAG,
        ),
    )

    # ---- posts (raw payload lives in object storage; DB stores a reference) ----
    posts = [
        (
            "post:1",
            src_reddit,
            author_a,
            "ext_r_1",
            "Agentic memory is the next frontier",
            _dt(2026, 7, 1),
        ),
        (
            "post:2",
            src_reddit,
            author_a,
            "ext_r_2",
            "Comparing vector databases for RAG",
            _dt(2026, 7, 3),
        ),
        ("post:3", src_hn, author_b, "ext_hn_1", "Show HN: a computer-use agent", _dt(2026, 7, 5)),
    ]
    post_ids: dict[str, uuid.UUID] = {}
    for slug, source_id, author_id, ext, text, published in posts:
        pid = demo_uuid(slug)
        post_ids[slug] = pid
        source_key = "demo_reddit" if source_id == src_reddit else "demo_hn"
        _ensure(
            session,
            Post,
            pid,
            Post(
                id=pid,
                source_id=source_id,
                external_id=ext,
                author_id=author_id,
                title=text,
                content=f"{text}. (demo body)",
                url=f"https://example.test/{ext}",
                published_at=published,
                collected_at=published,
                language="en",
                content_hash=_sha(text),
                engagement={"score": 42, "comments": 7, "demo": True},
                raw_payload_uri=f"r2://tide-raw/{build_raw_key(source_key, published, ext)}",
                meta=DEMO_FLAG,
            ),
        )

    # ---- concepts: one DISCOVERED (not in seed list), one curated-derived ----
    concept_discovered = demo_uuid("concept:agentic-memory")
    concept_curated = demo_uuid("concept:ai-agents")
    _ensure(
        session,
        Concept,
        concept_discovered,
        Concept(
            id=concept_discovered,
            key="demo:concept:agentic-memory",
            canonical_name="[DEMO] Agentic Memory",
            concept_type="topic",
            aliases=["agent memory"],
            status="discovered",
            origin=ConceptOrigin.DISCOVERED.value,
            seed_id=None,
            first_seen_at=_dt(2026, 7, 1),
            last_seen_at=_dt(2026, 7, 5),
            meta=DEMO_FLAG,
        ),
    )
    _ensure(
        session,
        Concept,
        concept_curated,
        Concept(
            id=concept_curated,
            key="demo:concept:ai-agents",
            canonical_name="[DEMO] AI Agents",
            concept_type="topic",
            status="active",
            origin=ConceptOrigin.SEED_LIST_YAML.value,
            seed_id=seed_id,
            first_seen_at=_dt(2026, 7, 1),
            last_seen_at=_dt(2026, 7, 5),
            meta=DEMO_FLAG,
        ),
    )

    # ---- entities (discovered) ----
    entity_openai = demo_uuid("entity:openai")
    entity_pg = demo_uuid("entity:postgresql")
    _ensure(
        session,
        Entity,
        entity_openai,
        Entity(
            id=entity_openai,
            key="demo:entity:openai",
            canonical_name="[DEMO] OpenAI",
            entity_type="organization",
            status="active",
            meta=DEMO_FLAG,
        ),
    )
    _ensure(
        session,
        Entity,
        entity_pg,
        Entity(
            id=entity_pg,
            key="demo:entity:postgresql",
            canonical_name="[DEMO] PostgreSQL",
            entity_type="technology",
            status="active",
            meta=DEMO_FLAG,
        ),
    )

    # ---- evidence: post → concept / post → entity ----
    _ensure(
        session,
        PostConcept,
        demo_uuid("pc:1"),
        PostConcept(
            id=demo_uuid("pc:1"),
            post_id=post_ids["post:1"],
            concept_id=concept_discovered,
            confidence=0.92,
            extraction_method="demo",
            extraction_model="none",
            meta=DEMO_FLAG,
        ),
    )
    _ensure(
        session,
        PostEntity,
        demo_uuid("pe:1"),
        PostEntity(
            id=demo_uuid("pe:1"),
            post_id=post_ids["post:2"],
            entity_id=entity_pg,
            confidence=0.81,
            extraction_method="demo",
            extraction_model="none",
            meta=DEMO_FLAG,
        ),
    )

    # ---- graph edges (temporal): concept→concept, concept→entity, entity→entity ----
    _ensure(
        session,
        GraphEdge,
        demo_uuid("edge:cc"),
        GraphEdge(
            id=demo_uuid("edge:cc"),
            source_node_type=NodeType.CONCEPT.value,
            source_node_id=concept_curated,
            target_node_type=NodeType.CONCEPT.value,
            target_node_id=concept_discovered,
            relationship_type="related_to",
            weight=0.7,
            confidence=0.8,
            evidence_count=3,
            first_observed_at=_dt(2026, 7, 1),
            last_observed_at=_dt(2026, 7, 5),
            meta=DEMO_FLAG,
        ),
    )
    _ensure(
        session,
        GraphEdge,
        demo_uuid("edge:ce"),
        GraphEdge(
            id=demo_uuid("edge:ce"),
            source_node_type=NodeType.CONCEPT.value,
            source_node_id=concept_discovered,
            target_node_type=NodeType.ENTITY.value,
            target_node_id=entity_openai,
            relationship_type="mentions",
            weight=0.5,
            confidence=0.6,
            evidence_count=1,
            first_observed_at=_dt(2026, 7, 2),
            last_observed_at=_dt(2026, 7, 5),
            meta=DEMO_FLAG,
        ),
    )
    _ensure(
        session,
        GraphEdge,
        demo_uuid("edge:ee"),
        GraphEdge(
            id=demo_uuid("edge:ee"),
            source_node_type=NodeType.ENTITY.value,
            source_node_id=entity_openai,
            target_node_type=NodeType.ENTITY.value,
            target_node_id=entity_pg,
            relationship_type="related_to",
            weight=0.3,
            confidence=0.5,
            evidence_count=1,
            first_observed_at=_dt(2026, 7, 3),
            last_observed_at=_dt(2026, 7, 5),
            meta=DEMO_FLAG,
        ),
    )

    # ---- time series: rising mentions for a concept + rising edge weight ----
    for i, day in enumerate((1, 2, 3, 4, 5)):
        _ensure(
            session,
            TimeSeriesObservation,
            demo_uuid(f"tso:concept:{day}"),
            TimeSeriesObservation(
                id=demo_uuid(f"tso:concept:{day}"),
                subject_type=SubjectType.CONCEPT.value,
                subject_id=concept_discovered,
                granularity=Granularity.DAY.value,
                bucket_start=_dt(2026, 7, day),
                mention_count=2 + i * 3,
                unique_authors=1 + i,
                engagement_sum=10.0 * (i + 1),
                source_diversity=1 + (i % 2),
                metrics={"demo": True},
            ),
        )
    for i, day in enumerate((1, 3, 5)):
        _ensure(
            session,
            TimeSeriesObservation,
            demo_uuid(f"tso:edge:{day}"),
            TimeSeriesObservation(
                id=demo_uuid(f"tso:edge:{day}"),
                subject_type=SubjectType.EDGE.value,
                subject_id=demo_uuid("edge:cc"),
                granularity=Granularity.DAY.value,
                bucket_start=_dt(2026, 7, day),
                mention_count=1 + i,
                unique_authors=1 + i,
                engagement_sum=5.0 * (i + 1),
                source_diversity=1,
                metrics={"edge_weight": 0.3 + 0.2 * i, "demo": True},
            ),
        )

    # ---- an embedding row (placeholder; NO vector generated, dim/model unset) ----
    _ensure(
        session,
        Embedding,
        demo_uuid("emb:concept"),
        Embedding(
            id=demo_uuid("emb:concept"),
            owner_type="concept",
            owner_id=concept_discovered,
            provider=None,
            model="",
            dim=None,
            embedding=None,
            meta=DEMO_FLAG,
        ),
    )

    # ---- agent memory: run → observation, hypothesis, prediction, report ----
    run_id = demo_uuid("agent:run")
    _ensure(
        session,
        AgentRun,
        run_id,
        AgentRun(
            id=run_id,
            status="completed",
            trigger="demo",
            started_at=_dt(2026, 7, 5),
            finished_at=_dt(2026, 7, 5),
            config={"demo": True},
            stats={"observations": 1},
            notes="[DEMO] run",
        ),
    )
    _ensure(
        session,
        AgentObservation,
        demo_uuid("agent:obs"),
        AgentObservation(
            id=demo_uuid("agent:obs"),
            run_id=run_id,
            observation_type="trend_candidate",
            subject_type=SubjectType.CONCEPT.value,
            subject_id=concept_discovered,
            summary="[DEMO] mentions of agentic memory are rising",
            confidence=0.7,
            data={"demo": True},
        ),
    )
    hyp_id = demo_uuid("agent:hyp")
    _ensure(
        session,
        AgentHypothesis,
        hyp_id,
        AgentHypothesis(
            id=hyp_id,
            run_id=run_id,
            statement="[DEMO] Agentic memory will become a top-discussed subtopic of AI agents",
            status="proposed",
            confidence=0.6,
            rationale="rising mentions + new posts",
            supporting_evidence=[str(post_ids["post:1"])],
            meta=DEMO_FLAG,
        ),
    )
    _ensure(
        session,
        AgentPrediction,
        demo_uuid("agent:pred"),
        AgentPrediction(
            id=demo_uuid("agent:pred"),
            run_id=run_id,
            hypothesis_id=hyp_id,
            statement="[DEMO] agentic memory mentions will double within 30 days",
            confidence=0.6,
            horizon="30d",
            evaluation_at=_dt(2026, 8, 4),
            status="pending",
            evaluation_metadata={"demo": True},
        ),
    )
    _ensure(
        session,
        AgentReport,
        demo_uuid("agent:report"),
        AgentReport(
            id=demo_uuid("agent:report"),
            run_id=run_id,
            title="[DEMO] Weekly AI agents trend brief",
            summary="agentic memory is emerging",
            body="Full demo report body.",
            concept_ids=[str(concept_discovered)],
            prediction_ids=[str(demo_uuid("agent:pred"))],
            generated_at=_dt(2026, 7, 5),
            meta=DEMO_FLAG,
        ),
    )

    session.flush()
    return {
        "sources": 2,
        "seeds": 1,
        "authors": 2,
        "posts": len(posts),
        "concepts": 2,
        "entities": 2,
        "graph_edges": 3,
        "agent_runs": 1,
    }
