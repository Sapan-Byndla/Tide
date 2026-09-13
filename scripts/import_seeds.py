"""CLI: import the curated seed_list.yaml into the database (idempotent).

Usage:
    python -m scripts.import_seeds [path/to/seed_list.yaml]
"""

from __future__ import annotations

import sys

from backend.core.config import get_settings
from backend.core.logging import configure_logging
from backend.db.session import session_scope
from backend.seeds.importer import import_seeds


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    settings = get_settings()
    configure_logging(level=settings.log_level, json_logs=settings.log_json)
    path = argv[0] if argv else settings.seed_list_path

    with session_scope() as session:
        report = import_seeds(session, path)

    print(
        f"Seed import complete from {path!r}:\n"
        f"  sources: +{report.sources_created} created, {report.sources_updated} updated\n"
        f"  seeds:   +{report.seeds_created} created, {report.seeds_updated} updated, "
        f"{report.seeds_unchanged} unchanged, {report.seeds_deactivated} deactivated\n"
        f"  warnings: {len(report.warnings)}"
    )
    for w in report.warnings:
        print(f"    - {w}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
