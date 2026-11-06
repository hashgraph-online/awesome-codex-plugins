"""JSON Schema validation for datasheet extraction results, shared by merge_results.py and
validate_extraction_result.py.

jsonschema and referencing are optional packages: they are imported when validation runs, and a
RuntimeError names them when they are missing.
"""

from __future__ import annotations

import json
from pathlib import Path

SCHEMA_DIR = Path(__file__).resolve().parents[1] / "schemas"

_MISSING = ("full schema validation needs the optional packages jsonschema and referencing "
            "(pip install jsonschema referencing)")


def schema_registry() -> "Registry":
    """Build a referencing Registry so $ref between local schemas resolves."""
    try:
        from referencing import Registry, Resource
    except ImportError as exc:
        raise RuntimeError(_MISSING) from exc
    registry = Registry()
    for schema_path in SCHEMA_DIR.glob("*.schema.json"):
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        uri = schema.get("$id")
        if uri:
            registry = registry.with_resource(uri, Resource.from_contents(schema))
    return registry


def validate_against_schema(data, schema: dict) -> str | None:
    """Return the first error as '<path>: <message>' (errors sorted by path), or None when *data* is valid."""
    try:
        from jsonschema import Draft202012Validator
    except ImportError as exc:
        raise RuntimeError(_MISSING) from exc
    registry = schema_registry()
    validator = Draft202012Validator(schema, registry=registry)
    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path))
    if not errors:
        return None
    e0 = errors[0]
    path = "/".join(str(p) for p in e0.absolute_path) or "<root>"
    return f"{path}: {e0.message}"
