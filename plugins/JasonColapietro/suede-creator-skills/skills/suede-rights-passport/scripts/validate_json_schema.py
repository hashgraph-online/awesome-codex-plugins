#!/usr/bin/env python3
"""Dependency-free validator for the JSON Schema keywords used by this skill.

This module executes the bundled Draft 2020-12 schema rather than maintaining a
second hand-written shape contract. It intentionally supports the complete
keyword subset present in `assets/suede-intake.schema.json`; adding another
schema keyword requires adding support here and a regression test.
"""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any


SUPPORTED_KEYWORDS = {
    "$schema",
    "$id",
    "$defs",
    "$ref",
    "title",
    "description",
    "type",
    "additionalProperties",
    "required",
    "properties",
    "items",
    "const",
    "enum",
    "pattern",
    "minLength",
    "minimum",
    "maximum",
    "format",
}


def _pointer(root: dict[str, Any], reference: str) -> dict[str, Any]:
    if not reference.startswith("#/"):
        raise ValueError(f"Only local JSON Schema references are supported: {reference}")
    value: Any = root
    for raw_part in reference[2:].split("/"):
        part = raw_part.replace("~1", "/").replace("~0", "~")
        if not isinstance(value, dict) or part not in value:
            raise ValueError(f"Unresolvable JSON Schema reference: {reference}")
        value = value[part]
    if not isinstance(value, dict):
        raise ValueError(f"JSON Schema reference does not resolve to an object: {reference}")
    return value


def _is_type(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    raise ValueError(f"Unsupported JSON Schema type: {expected}")


def _validate_format(value: str, format_name: str) -> bool:
    try:
        if format_name == "date":
            date.fromisoformat(value)
            return True
        if format_name == "date-time":
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed.tzinfo is not None
    except ValueError:
        return False
    raise ValueError(f"Unsupported JSON Schema format: {format_name}")


def _join(path: str, child: str | int) -> str:
    return f"{path}/{child}" if path else f"/{child}"


def assert_supported_schema(schema: dict[str, Any], path: str = "#") -> None:
    """Fail closed if the published schema introduces an unsupported keyword."""
    unsupported = sorted(set(schema) - SUPPORTED_KEYWORDS)
    if unsupported:
        raise ValueError(f"{path}: unsupported JSON Schema keyword(s): {', '.join(unsupported)}")
    for container_key in ("$defs", "properties"):
        container = schema.get(container_key, {})
        if not isinstance(container, dict):
            raise ValueError(f"{path}/{container_key}: must be an object")
        for name, child in container.items():
            if not isinstance(child, dict):
                raise ValueError(f"{path}/{container_key}/{name}: must be an object")
            assert_supported_schema(child, f"{path}/{container_key}/{name}")
    if "items" in schema:
        child = schema["items"]
        if not isinstance(child, dict):
            raise ValueError(f"{path}/items: must be an object")
        assert_supported_schema(child, f"{path}/items")


def validate_instance(
    instance: Any,
    schema: dict[str, Any],
    *,
    root_schema: dict[str, Any] | None = None,
    path: str = "",
) -> list[str]:
    """Return human-readable schema violations for one JSON value."""
    root = root_schema or schema
    unsupported = sorted(set(schema) - SUPPORTED_KEYWORDS)
    if unsupported:
        raise ValueError(f"Unsupported JSON Schema keyword(s): {', '.join(unsupported)}")
    if "$ref" in schema:
        target = _pointer(root, str(schema["$ref"]))
        return validate_instance(instance, target, root_schema=root, path=path)

    label = path or "/"
    errors: list[str] = []
    expected = schema.get("type")
    if expected is not None:
        allowed_types = expected if isinstance(expected, list) else [expected]
        if not any(_is_type(instance, str(type_name)) for type_name in allowed_types):
            errors.append(f"{label}: expected type {' or '.join(map(str, allowed_types))}")
            return errors

    if "const" in schema and instance != schema["const"]:
        errors.append(f"{label}: must equal {schema['const']!r}")
    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{label}: value is not in the allowed enum")

    if isinstance(instance, str):
        if len(instance) < int(schema.get("minLength", 0)):
            errors.append(f"{label}: string is shorter than minLength {schema['minLength']}")
        if "pattern" in schema and re.search(str(schema["pattern"]), instance) is None:
            errors.append(f"{label}: string does not match pattern {schema['pattern']!r}")
        if "format" in schema and not _validate_format(instance, str(schema["format"])):
            errors.append(f"{label}: string is not a valid {schema['format']}")

    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            errors.append(f"{label}: number is below minimum {schema['minimum']}")
        if "maximum" in schema and instance > schema["maximum"]:
            errors.append(f"{label}: number is above maximum {schema['maximum']}")

    if isinstance(instance, dict):
        required = schema.get("required", [])
        for key in required:
            if key not in instance:
                errors.append(f"{_join(path, key)}: required property is missing")
        properties = schema.get("properties", {})
        if not isinstance(properties, dict):
            raise ValueError(f"{label}: schema properties must be an object")
        for key, value in instance.items():
            if key in properties:
                child_schema = properties[key]
                if not isinstance(child_schema, dict):
                    raise ValueError(f"{label}: schema for property {key!r} must be an object")
                errors += validate_instance(
                    value, child_schema, root_schema=root, path=_join(path, key)
                )
            elif schema.get("additionalProperties") is False:
                errors.append(f"{_join(path, key)}: additional property is not allowed")

    if isinstance(instance, list) and "items" in schema:
        item_schema = schema["items"]
        if not isinstance(item_schema, dict):
            raise ValueError(f"{label}: schema items must be an object")
        for index, value in enumerate(instance):
            errors += validate_instance(
                value, item_schema, root_schema=root, path=_join(path, index)
            )
    return errors
