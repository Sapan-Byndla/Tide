"""Load, validate, and flatten ``seed_list.yaml`` into importable seed specs.

Responsibilities:

* parse the YAML into a permissive Pydantic model (structural validation),
* surface warnings for smells that should NOT crash the import (alias collisions,
  duplicate list values, unknown source platforms),
* flatten the curated file into a normalized list of ``SeedSpec`` / ``SourceSpec``
  with stable deterministic keys.

It never mutates the source file and never touches the database.
"""

from __future__ import annotations

import collections
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, ValidationError

from backend.db.models.enums import SeedType
from backend.seeds.identity import seed_key

# ---- known source catalog & field→seed-type mapping (extensible) ---------- #
SOURCE_CATALOG: dict[str, tuple[str, str]] = {
    "reddit": ("Reddit", "social"),
    "hacker_news": ("Hacker News", "aggregator"),
    "stack_overflow": ("Stack Overflow", "qa"),
    "github": ("GitHub", "code"),
    "arxiv": ("arXiv", "academic"),
    "rss": ("RSS Feeds", "rss"),
}

SOURCE_FIELD_SEED_TYPE: dict[tuple[str, str], SeedType] = {
    ("reddit", "subreddits"): SeedType.COMMUNITY,
    ("hacker_news", "feeds"): SeedType.CHANNEL,
    ("stack_overflow", "tags"): SeedType.TAG,
    ("github", "topics"): SeedType.TAG,
    ("arxiv", "categories"): SeedType.CATEGORY,
    ("rss", "feeds"): SeedType.RSS_FEED,
}

DEFAULT_PRIORITY = 100


# ---- parsed-file Pydantic models ------------------------------------------ #
class TopicIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    aliases: list[str] = []


class RssFeedIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    url: str


class SeedFile(BaseModel):
    # ``extra="allow"`` tolerates the domain/collection/policy blocks we don't
    # model strictly; topics are validated strictly via TopicIn.
    model_config = ConfigDict(extra="allow")

    version: int
    topics: list[TopicIn] = []
    sources: dict[str, Any] = {}


# ---- normalized outputs --------------------------------------------------- #
@dataclass(frozen=True)
class SourceSpec:
    source_key: str
    display_name: str
    source_type: str


@dataclass(frozen=True)
class SeedSpec:
    key: str
    name: str
    seed_type: str
    source_key: str | None
    canonical_value: str
    aliases: tuple[str, ...] = ()
    priority: int = DEFAULT_PRIORITY
    config: tuple[tuple[str, Any], ...] = ()  # frozen; convert to dict on use

    def config_dict(self) -> dict[str, Any]:
        return dict(self.config)


@dataclass
class ValidationResult:
    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class FlattenResult:
    version: int
    sources: list[SourceSpec]
    seeds: list[SeedSpec]
    warnings: list[str] = field(default_factory=list)


def load_seed_file(path: str | Path) -> SeedFile:
    """Parse and structurally validate the YAML file. Raises on malformed input."""
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("seed_list.yaml must be a mapping at the top level")
    return SeedFile.model_validate(raw)


def validate_seed_file(path: str | Path) -> ValidationResult:
    """Validate structure and report warnings without importing anything."""
    result = ValidationResult(ok=True)
    try:
        parsed = load_seed_file(path)
    except (ValidationError, ValueError, yaml.YAMLError) as exc:
        return ValidationResult(ok=False, errors=[str(exc)])

    ids = [t.id for t in parsed.topics]
    names = [t.name for t in parsed.topics]
    for dup in (k for k, c in collections.Counter(ids).items() if c > 1):
        result.errors.append(f"duplicate topic id: {dup!r}")
    for dup in (k for k, c in collections.Counter(names).items() if c > 1):
        result.errors.append(f"duplicate topic name: {dup!r}")

    # Alias collisions (warnings, not errors).
    name_owner = {t.name.lower(): t.id for t in parsed.topics}
    for topic in parsed.topics:
        for alias in topic.aliases:
            a = alias.lower()
            owner = name_owner.get(a)
            if owner is None:
                continue
            if owner == topic.id:
                result.warnings.append(
                    f"topic {topic.id!r} lists alias {alias!r} equal to its own name (redundant)"
                )
            else:
                result.warnings.append(
                    f"alias {alias!r} on topic {topic.id!r} collides with canonical name "
                    f"of topic {owner!r}"
                )

    # Structural warnings from flattening (unknown platforms, duplicate values).
    result.warnings.extend(flatten_seed_file(parsed).warnings)
    result.ok = not result.errors
    return result


def flatten_seed_file(parsed: SeedFile) -> FlattenResult:
    """Flatten the parsed file into normalized source/seed specs."""
    warnings: list[str] = []
    sources: dict[str, SourceSpec] = {}
    seeds: list[SeedSpec] = []

    # Topics → global conceptual seeds (no source).
    for topic in parsed.topics:
        seeds.append(
            SeedSpec(
                key=seed_key(SeedType.TOPIC.value, None, topic.id),
                name=topic.name,
                seed_type=SeedType.TOPIC.value,
                source_key=None,
                canonical_value=topic.id,
                aliases=tuple(topic.aliases),
            )
        )

    # Source-specific seeds.
    for platform, cfg in parsed.sources.items():
        display, stype = SOURCE_CATALOG.get(platform, (platform.replace("_", " ").title(), "other"))
        if platform not in SOURCE_CATALOG:
            warnings.append(f"unknown source platform {platform!r} (imported as type 'other')")
        sources[platform] = SourceSpec(platform, display, stype)

        if not isinstance(cfg, dict):
            warnings.append(f"source {platform!r} config is not a mapping; skipped")
            continue

        for fieldname, values in cfg.items():
            mapped_type = SOURCE_FIELD_SEED_TYPE.get((platform, fieldname))
            seed_type = (mapped_type or SeedType.SOURCE_TARGET).value
            if mapped_type is None:
                warnings.append(
                    f"unknown source field {platform}.{fieldname!r} "
                    f"(imported as seed_type 'source_target')"
                )
            if not isinstance(values, list):
                warnings.append(f"{platform}.{fieldname} is not a list; skipped")
                continue

            seen: set[str] = set()
            for value in values:
                spec = _seed_from_source_value(platform, seed_type, value, warnings)
                if spec is None:
                    continue
                if spec.canonical_value.lower() in seen:
                    warnings.append(
                        f"duplicate value {spec.canonical_value!r} in {platform}.{fieldname}"
                    )
                    continue
                seen.add(spec.canonical_value.lower())
                seeds.append(spec)

    return FlattenResult(
        version=parsed.version,
        sources=list(sources.values()),
        seeds=seeds,
        warnings=warnings,
    )


def _seed_from_source_value(
    platform: str, seed_type: str, value: Any, warnings: list[str]
) -> SeedSpec | None:
    """Build a SeedSpec from one entry of a source field."""
    if seed_type == SeedType.RSS_FEED.value:
        try:
            feed = RssFeedIn.model_validate(value)
        except ValidationError:
            warnings.append(f"invalid rss feed entry in {platform!r}: {value!r}")
            return None
        return SeedSpec(
            key=seed_key(seed_type, platform, feed.name),
            name=feed.name,
            seed_type=seed_type,
            source_key=platform,
            canonical_value=feed.url,
            config=(("url", feed.url),),
        )

    if not isinstance(value, str):
        warnings.append(f"expected string value in {platform!r}, got {value!r}; skipped")
        return None

    return SeedSpec(
        key=seed_key(seed_type, platform, value),
        name=value,
        seed_type=seed_type,
        source_key=platform,
        canonical_value=value,
    )
