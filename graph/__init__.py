"""TIDE Concept Graph — persistent representation of what TIDE knows.

Responsibility
--------------
Own the persistence and traversal of concepts, entities, relationships, temporal
signals, evidence, and metrics. This is the substrate the AI Crawler reads.

Key architectural decision
---------------------------
The graph lives in **PostgreSQL** (relational node/edge tables), NOT a dedicated
graph database, and semantic vectors live alongside it in **pgvector**. Callers
depend only on the ``GraphRepository`` and ``VectorRepository`` ports, so the
backing store can change later without touching the intelligence or agent
subsystems.

Structure
---------
* ``graph.repositories`` — Phase 0 in-memory reference adapters implementing the
  ports (useful for tests and local runs before Postgres is wired in).

Phase 0 status: interfaces plus an in-memory reference implementation. No SQL
schema or migration is created for graph tables yet.
"""

from __future__ import annotations

from graph.repositories import InMemoryGraphRepository, InMemoryVectorRepository

__all__ = ["InMemoryGraphRepository", "InMemoryVectorRepository"]
