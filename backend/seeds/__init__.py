"""Curated seed configuration: load, validate, and import ``seed_list.yaml``.

This package turns the curated configuration file into the database's runtime
representation. It writes ONLY curated tables (``sources``, ``seeds``) and never
mutates discovered knowledge (``concepts``/``entities``) — nor does it push
discovered concepts back into the seed file.
"""

from __future__ import annotations

from backend.seeds.importer import ImportReport, SeedImportError, import_seeds
from backend.seeds.loader import (
    ValidationResult,
    flatten_seed_file,
    load_seed_file,
    validate_seed_file,
)

__all__ = [
    "ImportReport",
    "SeedImportError",
    "ValidationResult",
    "flatten_seed_file",
    "import_seeds",
    "load_seed_file",
    "validate_seed_file",
]
