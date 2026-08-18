"""Stdlib-only mini JSON Schema validator for Layer 2 review_annotations.

Scope is intentionally narrow: this module exists so the kicad-happy
plugin does not need to take a hard runtime dependency on the
third-party `jsonschema` package just to validate the small Layer 2
review schema. The datasheets skill still uses the real `jsonschema`
package because its schemas use `$ref` for cross-schema composition,
which is not trivial to inline.

Supported Draft 2020-12 keywords (the set actually used by
`skills/kicad/review/schemas/review_annotations.schema.json`):
  type, required, additionalProperties (boolean form only),
  properties, const, enum, items (single subschema form only),
  minLength, maxLength, minItems, maxItems, format (informational).

Deliberately NOT supported (raise/yield "unsupported keyword" if
encountered): $ref, $defs, oneOf, anyOf, allOf, not, if/then/else,
dependentSchemas, dependentRequired, contains, propertyNames, pattern,
patternProperties, prefixItems, contentSchema, format ENFORCEMENT
(matches jsonschema's default permissive behavior — format strings
are accepted as informational unless an explicit checker is wired).

If a Layer 2 schema grows beyond this surface, switch the offending
consumer back to the real `jsonschema` package — DO NOT silently
extend this validator and risk diverging from spec. Loud failure on
unsupported keywords is by design.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Iterator


class ValidationError(Exception):
    """Mirrors the surface of `jsonschema.exceptions.ValidationError`.

    Exposes `.message` (str), `.path` and `.absolute_path` (list) so
    callers that consumed jsonschema's error objects continue to work
    without changes.
    """

    def __init__(self, message: str, path: tuple = ()):
        self.message = message
        self.path = list(path)
        self.absolute_path = list(path)
        if path:
            full = f"at /{'/'.join(str(p) for p in path)}: {message}"
        else:
            full = message
        super().__init__(full)


_TYPE_PY = {
    "string": str,
    "number": (int, float),
    "integer": int,
    "boolean": bool,
    "array": list,
    "object": dict,
    "null": type(None),
}

_SUPPORTED_KEYWORDS = frozenset({
    "$schema", "$id", "title", "description",
    "type", "required", "additionalProperties", "properties",
    "const", "enum", "items",
    "minLength", "maxLength", "minItems", "maxItems",
    "format",
})


def _check_format(value: str, fmt: str) -> bool:
    """Format check is informational. Returns True for unknown formats
    (matches jsonschema default behavior — format is opt-in via a
    FORMAT_CHECKER). Date-time is checked because it's the only format
    the Layer 2 schema actually uses, and silent acceptance of garbage
    timestamps would defeat the schema's purpose."""
    if fmt == "date-time":
        try:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
            return True
        except (ValueError, TypeError):
            return False
    return True


def iter_errors(instance: Any, schema: dict, path: tuple = ()) -> Iterator[ValidationError]:
    """Yield one ValidationError per violation. Mirrors
    `Draft202012Validator(schema).iter_errors(instance)`."""
    if not isinstance(schema, dict):
        return

    unsupported = set(schema.keys()) - _SUPPORTED_KEYWORDS
    if unsupported:
        yield ValidationError(
            f"unsupported schema keyword(s) for mini-validator: {sorted(unsupported)} "
            f"— if you need these, switch this consumer back to the real jsonschema package",
            path,
        )
        return

    if "const" in schema and instance != schema["const"]:
        yield ValidationError(
            f"{instance!r} is not equal to const {schema['const']!r}", path,
        )

    if "enum" in schema and instance not in schema["enum"]:
        yield ValidationError(
            f"{instance!r} is not one of {schema['enum']}", path,
        )

    if "type" in schema:
        t = schema["type"]
        expected = _TYPE_PY.get(t)
        if expected is None:
            yield ValidationError(f"unsupported type {t!r}", path)
        elif t in ("integer", "number") and isinstance(instance, bool):
            yield ValidationError(f"{instance!r} is not of type {t!r}", path)
        elif not isinstance(instance, expected):
            yield ValidationError(f"{instance!r} is not of type {t!r}", path)

    if isinstance(instance, str):
        if "minLength" in schema and len(instance) < schema["minLength"]:
            yield ValidationError(
                f"string of length {len(instance)} shorter than minLength {schema['minLength']}",
                path,
            )
        if "maxLength" in schema and len(instance) > schema["maxLength"]:
            yield ValidationError(
                f"string of length {len(instance)} longer than maxLength {schema['maxLength']}",
                path,
            )
        if "format" in schema and not _check_format(instance, schema["format"]):
            yield ValidationError(
                f"{instance!r} is not a valid {schema['format']!r}", path,
            )

    if isinstance(instance, list):
        if "minItems" in schema and len(instance) < schema["minItems"]:
            yield ValidationError(
                f"array has {len(instance)} items, minItems {schema['minItems']}", path,
            )
        if "maxItems" in schema and len(instance) > schema["maxItems"]:
            yield ValidationError(
                f"array has {len(instance)} items, maxItems {schema['maxItems']}", path,
            )
        if "items" in schema:
            for i, item in enumerate(instance):
                yield from iter_errors(item, schema["items"], path + (i,))

    if isinstance(instance, dict):
        if "required" in schema:
            for req in schema["required"]:
                if req not in instance:
                    yield ValidationError(
                        f"required property {req!r} missing", path,
                    )
        properties = schema.get("properties", {})
        additional = schema.get("additionalProperties", True)
        for k, v in instance.items():
            if k in properties:
                yield from iter_errors(v, properties[k], path + (k,))
            elif additional is False:
                yield ValidationError(
                    f"additional property {k!r} is not allowed", path,
                )


def validate(instance: Any, schema: dict) -> None:
    """Raise the first ValidationError, if any. Mirrors
    `Draft202012Validator(schema).validate(instance)`."""
    for err in iter_errors(instance, schema):
        raise err
