"""ORM models for TIDE's persistent data foundation.

Importing this package registers every table on ``backend.db.base.Base.metadata``
so Alembic autogeneration and ``create_all`` see the full schema. Models are
grouped by concern:

* ``catalog``    — Source, Seed              (curated configuration)
* ``content``    — Author, Post              (collected content)
* ``knowledge``  — Entity, Concept           (discovered knowledge)
* ``evidence``   — PostConcept, PostEntity   (post→node associations)
* ``graph``      — GraphEdge                 (temporal relationships)
* ``timeseries`` — TimeSeriesObservation     (raw historical metrics)
* ``embeddings`` — Embedding                 (pgvector-ready vectors)
* ``agent``      — AgentRun/Observation/Hypothesis/Prediction/Report
"""

from __future__ import annotations

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
from backend.db.models.evidence import PostConcept, PostEntity
from backend.db.models.graph import GraphEdge
from backend.db.models.knowledge import Concept, Entity
from backend.db.models.timeseries import TimeSeriesObservation

__all__ = [
    "AgentHypothesis",
    "AgentObservation",
    "AgentPrediction",
    "AgentReport",
    "AgentRun",
    "Author",
    "Concept",
    "Embedding",
    "Entity",
    "GraphEdge",
    "Post",
    "PostConcept",
    "PostEntity",
    "Seed",
    "Source",
    "TimeSeriesObservation",
]
