"""Dataclass -> JSON Schema Draft 2020-12 converter.

Zero external dependencies. Walks dataclass fields and emits a schema
suitable for both human reference (--schema flag) and runtime validation.

Rules:
    - Every field must carry metadata={"description": "..."} — we refuse
      to emit schema for undocumented fields (forces descriptions to live
      next to the type declaration, not in a sidecar markdown file).
    - Fields with no default value are required; fields with a default
      (including default=None or default_factory) are optional.
    - Optional[T] / T | None renders as {"anyOf": [<T>, {"type": "null"}]}.
    - Nested dataclasses render as inline object schemas (no $defs/$ref
      for v1.4; revisit if schemas grow cyclic or enormous).
    - list[T] -> {"type": "array", "items": <T>}
    - dict[str, T] -> {"type": "object", "additionalProperties": <T>}
    - bare dict / dict[str, Any] -> {"type": "object"} (no constraints)
    - bare list -> {"type": "array"} (no item constraints)
    - field(metadata={"const": <value>}) adds "const": <value> to the
      emitted schema fragment — useful for discriminator fields like
      analyzer_type or schema_version that must carry a fixed value.
    - field(metadata={"json_name": "<key>"}) renames the emitted JSON
      property to <key> (used for underscore-prefixed keys like
      "_redirected_from" that don't fit Python identifier rules).
"""
from __future__ import annotations

import dataclasses
import json
import sys
import types
import typing
from dataclasses import MISSING, fields, is_dataclass

_SCHEMA_URI = "https://json-schema.org/draft/2020-12/schema"


def dataclass_to_json_schema(cls: type) -> dict:
    """Top-level entry. Produces a complete Draft 2020-12 schema document."""
    if not is_dataclass(cls):
        raise TypeError(f"{cls!r} is not a dataclass")
    body = _object_schema_for(cls)
    body["$schema"] = _SCHEMA_URI
    body["title"] = cls.__name__
    return body


def _object_schema_for(cls: type) -> dict:
    """Internal: emit an object schema body for a dataclass."""
    hints = typing.get_type_hints(cls)
    props: dict[str, dict] = {}
    required: list[str] = []
    for f in fields(cls):
        meta = f.metadata or {}
        if "description" not in meta:
            raise ValueError(
                f"{cls.__name__}.{f.name}: missing description metadata. "
                f"Use dataclasses.field(metadata={{'description': '...'}}) "
                f"on every envelope field."
            )
        try:
            field_schema = _type_to_schema(hints[f.name])
        except TypeError as e:
            raise TypeError(
                f"{cls.__name__}.{f.name}: {e}"
            ) from e
        field_schema["description"] = meta["description"]
        if "const" in meta:
            field_schema["const"] = meta["const"]
        json_key = meta.get("json_name", f.name)
        props[json_key] = field_schema
        if f.default is MISSING and f.default_factory is MISSING:
            required.append(json_key)
    out = {"type": "object", "properties": props, "required": required}
    return out


def _type_to_schema(tp) -> dict:
    """Map a Python type annotation to a JSON Schema fragment."""
    origin = typing.get_origin(tp)
    args = typing.get_args(tp)

    # Handle Optional[T] / T | None / Union[T, None]
    if origin is typing.Union or (origin is not None and _is_union_type(origin)):
        non_none = [a for a in args if a is not type(None)]
        if len(non_none) == 1 and len(args) == 2:
            inner = _type_to_schema(non_none[0])
            return {"anyOf": [inner, {"type": "null"}]}
        # General union — union of schemas
        return {"anyOf": [_type_to_schema(a) for a in args]}

    # list[T], List[T]
    if origin in (list, typing.List):
        if args:
            return {"type": "array", "items": _type_to_schema(args[0])}
        return {"type": "array"}

    # dict[str, T], Dict[str, T]
    if origin in (dict, typing.Dict):
        if args and len(args) == 2:
            # Only dict[str, X] is meaningful for JSON.
            return {
                "type": "object",
                "additionalProperties": _type_to_schema(args[1]),
            }
        return {"type": "object"}

    # Bare collection types
    if tp in (list, typing.List):
        return {"type": "array"}
    if tp in (dict, typing.Dict):
        return {"type": "object"}

    # Primitives
    if tp is int:
        return {"type": "integer"}
    if tp is float:
        return {"type": "number"}
    if tp is str:
        return {"type": "string"}
    if tp is bool:
        return {"type": "boolean"}
    if tp is type(None):
        return {"type": "null"}

    # typing.Any / object -> unconstrained
    if tp is typing.Any or tp is object:
        return {}

    # Nested dataclass
    if is_dataclass(tp):
        return _object_schema_for(tp)

    raise TypeError(f"Cannot convert {tp!r} to JSON Schema")


def _is_union_type(origin) -> bool:
    """True for PEP 604 'X | Y' unions (Python 3.10+)."""
    return origin is types.UnionType


def emit_schema(cls: type) -> None:
    """CLI helper: print dataclass schema as JSON to stdout, exit 0."""
    print(json.dumps(dataclass_to_json_schema(cls), indent=2))
    sys.exit(0)
