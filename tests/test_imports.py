"""Every subsystem package imports cleanly with no side effects."""

from __future__ import annotations

import importlib

import pytest

SUBSYSTEMS = [
    "contracts",
    "contracts.enums",
    "contracts.models",
    "scrapers",
    "scrapers.registry",
    "scrapers.sources",
    "intelligence",
    "intelligence.pipeline",
    "graph",
    "graph.repositories",
    "agent",
    "agent.lifecycle",
    "workers",
    "workers.bootstrap",
    "workers.daily",
    "backend",
    "backend.core.config",
    "backend.core.logging",
    "backend.main",
    "backend.db",
]


@pytest.mark.parametrize("module_name", SUBSYSTEMS)
def test_module_imports(module_name: str) -> None:
    assert importlib.import_module(module_name) is not None
