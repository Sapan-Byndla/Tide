"""Backend core: cross-cutting concerns for the API host.

Holds configuration (:mod:`backend.core.config`) and structured logging
(:mod:`backend.core.logging`). Deliberately small — this is *not* a general
utilities dumping ground. Anything domain-specific belongs to a subsystem;
anything shared and domain-neutral belongs in ``contracts``.
"""

from __future__ import annotations

from backend.core.config import Settings, get_settings
from backend.core.logging import configure_logging, get_logger

__all__ = ["Settings", "configure_logging", "get_logger", "get_settings"]
