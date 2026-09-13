"""Idempotent importer: ``seed_list.yaml`` → database.

Guarantees:

* **Idempotent** — running twice with an unchanged file changes nothing.
* **Stable IDs** — rows are keyed by deterministic ``key``/``uuid5`` (see
  ``identity``), so re-import updates the same rows.
* **Config-vs-data separation** — updates curated ``seeds``/``sources`` only. It
  NEVER creates or deletes ``concepts``/``entities`` (discovered knowledge).
* **Non-destructive** — a seed removed from the file is *deactivated*
  (``enabled=False``), never deleted, so history and any linked graph knowledge
  survive.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.core.logging import get_logger
from backend.db.models.catalog import Seed, Source
from backend.db.models.enums import SeedOrigin
from backend.seeds.identity import seed_uuid, source_uuid
from backend.seeds.loader import (
    SeedSpec,
    SourceSpec,
    flatten_seed_file,
    load_seed_file,
    validate_seed_file,
)

log = get_logger("tide.seeds.importer")


class SeedImportError(RuntimeError):
    """Raised when the seed file is invalid and cannot be imported."""


@dataclass
class ImportReport:
    sources_created: int = 0
    sources_updated: int = 0
    seeds_created: int = 0
    seeds_updated: int = 0
    seeds_unchanged: int = 0
    seeds_deactivated: int = 0
    warnings: list[str] = field(default_factory=list)

    @property
    def total_seeds(self) -> int:
        return self.seeds_created + self.seeds_updated + self.seeds_unchanged


def import_seeds(
    session: Session,
    path: str,
    *,
    deactivate_missing: bool = True,
) -> ImportReport:
    """Import (or re-import) the curated seed file into the database."""
    validation = validate_seed_file(path)
    if not validation.ok:
        raise SeedImportError("; ".join(validation.errors))

    parsed = load_seed_file(path)
    flat = flatten_seed_file(parsed)
    report = ImportReport(warnings=list(flat.warnings))
    now = datetime.now(UTC)

    source_ids = _upsert_sources(session, flat.sources, report)
    _upsert_seeds(session, flat.seeds, source_ids, flat.version, now, report)

    if deactivate_missing:
        _deactivate_missing(session, {s.key for s in flat.seeds}, report)

    session.flush()
    for w in report.warnings:
        log.warning("seed.import.warning", detail=w)
    log.info(
        "seed.import.done",
        seeds_created=report.seeds_created,
        seeds_updated=report.seeds_updated,
        seeds_unchanged=report.seeds_unchanged,
        seeds_deactivated=report.seeds_deactivated,
    )
    return report


def _upsert_sources(
    session: Session, specs: list[SourceSpec], report: ImportReport
) -> dict[str, uuid.UUID]:
    existing = {s.source_key: s for s in session.execute(select(Source)).scalars()}
    source_ids: dict[str, uuid.UUID] = {}
    for spec in specs:
        row = existing.get(spec.source_key)
        if row is None:
            row = Source(
                id=source_uuid(spec.source_key),
                source_key=spec.source_key,
                display_name=spec.display_name,
                source_type=spec.source_type,
                enabled=True,
            )
            session.add(row)
            report.sources_created += 1
        else:
            if (row.display_name, row.source_type) != (spec.display_name, spec.source_type):
                row.display_name = spec.display_name
                row.source_type = spec.source_type
                report.sources_updated += 1
        source_ids[spec.source_key] = source_uuid(spec.source_key)
    return source_ids


def _upsert_seeds(
    session: Session,
    specs: list[SeedSpec],
    source_ids: dict[str, uuid.UUID],
    version: int,
    now: datetime,
    report: ImportReport,
) -> None:
    existing = {s.key: s for s in session.execute(select(Seed)).scalars()}
    for spec in specs:
        source_id = source_ids.get(spec.source_key) if spec.source_key else None
        aliases = list(spec.aliases)
        config = spec.config_dict()
        row = existing.get(spec.key)
        if row is None:
            session.add(
                Seed(
                    id=seed_uuid(spec.key),
                    key=spec.key,
                    name=spec.name,
                    seed_type=spec.seed_type,
                    source_id=source_id,
                    canonical_value=spec.canonical_value,
                    aliases=aliases,
                    priority=spec.priority,
                    enabled=True,
                    config=config,
                    origin=SeedOrigin.SEED_LIST_YAML.value,
                    source_config_version=version,
                    imported_at=now,
                )
            )
            report.seeds_created += 1
            continue

        changed = (
            row.name != spec.name
            or row.seed_type != spec.seed_type
            or row.source_id != source_id
            or row.canonical_value != spec.canonical_value
            or row.aliases != aliases
            or row.priority != spec.priority
            or row.config != config
            or not row.enabled
        )
        if changed:
            row.name = spec.name
            row.seed_type = spec.seed_type
            row.source_id = source_id
            row.canonical_value = spec.canonical_value
            row.aliases = aliases
            row.priority = spec.priority
            row.config = config
            row.enabled = True
            row.source_config_version = version
            row.imported_at = now
            report.seeds_updated += 1
        else:
            report.seeds_unchanged += 1


def _deactivate_missing(session: Session, current_keys: set[str], report: ImportReport) -> None:
    stmt = select(Seed).where(Seed.origin == SeedOrigin.SEED_LIST_YAML.value)
    for row in session.execute(stmt).scalars():
        if row.key in current_keys or not row.enabled:
            continue
        row.enabled = False
        cfg = dict(row.config or {})
        cfg["removed_from_seed_list"] = True
        row.config = cfg
        report.seeds_deactivated += 1
