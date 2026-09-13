"""CLI: load deterministic development/demo data into the database (idempotent).

Usage:
    python -m scripts.load_demo
"""

from __future__ import annotations

from backend.core.config import get_settings
from backend.core.logging import configure_logging
from backend.db.demo import load_demo_data
from backend.db.session import session_scope


def main() -> int:
    settings = get_settings()
    configure_logging(level=settings.log_level, json_logs=settings.log_json)
    with session_scope() as session:
        summary = load_demo_data(session)
    print("Demo data loaded:", summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
