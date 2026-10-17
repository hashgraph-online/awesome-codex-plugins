"""Generic dict ↔ dataclass codec for the datasheet types.

Reflects over type hints. Handles:
    - dataclass fields of dataclass types (recursive)
    - Optional[T] (`T | None`)
    - list[T] (recursive on T)
    - dict[str, T] (recursive on T)
    - The Pinout wrapper class (special-cased — not a dataclass)
    - Primitive types (str, int, float, bool) — passthrough

Rules:
    - Required fields (no default) raise KeyError on from_dict if absent.
    - Optional fields default to None on from_dict if absent.
    - to_dict walks the dataclass fields and emits a plain dict with the
      same keys as the declared field names.
    - Pinout special case: serializes as a bare list (matches the JSON
      schema's root-array shape for pinout.schema.json).

Stdlib only.
"""
from __future__ import annotations

import types as _types
import typing
from dataclasses import MISSING, fields, is_dataclass


def from_dict(cls, data):
    """Construct an instance of `cls` from a dict (or list for Pinout).

    Recurses through nested dataclasses, lists, and dicts.
    """
    # Pinout is a non-dataclass wrapper around list[Pin] — handled first.
    if _is_pinout(cls):
        return _pinout_from_list(cls, data)

    if not is_dataclass(cls):
        # Primitives pass through unchanged. The caller decides what to do
        # with mismatched types (e.g. int where float was expected).
        return data

    if data is None:
        return None

    hints = typing.get_type_hints(cls)
    kwargs = {}
    for f in fields(cls):
        hint = hints[f.name]
        if f.name in data:
            kwargs[f.name] = _from_value(hint, data[f.name])
        elif f.default is MISSING and f.default_factory is MISSING:
            raise KeyError(
                f"{cls.__name__}: required field {f.name!r} missing from input dict"
            )
        # else: optional field, let the default apply
    return cls(**kwargs)


def to_dict(obj):
    """Convert a dataclass instance (or Pinout) back to a plain dict.

    Inverse of from_dict. Emits None for optional fields that are None,
    UNLESS the field declares metadata={"omit_if_none": True} — those
    fields are omitted entirely when their value is None. Used on
    DatasheetFacts category siblings (regulator, future mcu/opamp/...)
    so "absent" is the canonical signal for "no category" and the JSON
    cache doesn't carry null placeholders for inactive categories.
    """
    if obj is None:
        return None
    if _is_pinout_instance(obj):
        return [to_dict(p) for p in obj.pins]
    if is_dataclass(obj) and not isinstance(obj, type):
        out = {}
        for f in fields(obj):
            value = getattr(obj, f.name)
            if value is None and (f.metadata or {}).get("omit_if_none"):
                continue
            out[f.name] = _to_value(value)
        return out
    return obj


# --- internal helpers ------------------------------------------------------

def _from_value(hint, value):
    """Recursively convert a value matching `hint` (a type annotation)."""
    if value is None:
        return None

    origin = typing.get_origin(hint)
    args = typing.get_args(hint)

    # Optional[T] / T | None
    if origin is typing.Union or origin is _types.UnionType:
        non_none = [a for a in args if a is not type(None)]
        if len(non_none) == 1:
            return _from_value(non_none[0], value)
        # Multi-arm unions not used in the datasheet types.
        return value

    # list[T]
    if origin is list:
        (item_type,) = args
        if not isinstance(value, list):
            raise TypeError(
                f"Expected list for {hint!r}, got {type(value).__name__}: {value!r}"
            )
        return [_from_value(item_type, item) for item in value]

    # dict[str, T]
    if origin is dict:
        _, value_type = args
        if not isinstance(value, dict):
            raise TypeError(
                f"Expected dict for {hint!r}, got {type(value).__name__}: {value!r}"
            )
        return {k: _from_value(value_type, v) for k, v in value.items()}

    # Dataclass or Pinout
    if is_dataclass(hint) or _is_pinout(hint):
        return from_dict(hint, value)

    # Primitive.
    return value


def _to_value(value):
    """Serialize a single value — recurse for dataclasses, lists, dicts."""
    if value is None:
        return None
    if _is_pinout_instance(value):
        return [to_dict(p) for p in value.pins]
    if is_dataclass(value) and not isinstance(value, type):
        return to_dict(value)
    if isinstance(value, list):
        return [_to_value(v) for v in value]
    if isinstance(value, dict):
        return {k: _to_value(v) for k, v in value.items()}
    return value


def _is_pinout(cls) -> bool:
    """True if cls is the Pinout wrapper class.

    Import is lazy to break the datasheet_types.pinout ↔ datasheet_types.codec cycle.
    """
    try:
        from .pinout import Pinout
    except ImportError:
        return False
    return isinstance(cls, type) and issubclass(cls, Pinout)


def _is_pinout_instance(obj) -> bool:
    try:
        from .pinout import Pinout
    except ImportError:
        return False
    return isinstance(obj, Pinout)


def _pinout_from_list(cls, data):
    """Build a Pinout from a list of Pin dicts."""
    from .pinout import Pin  # avoids circular import at module top

    if data is None:
        return None
    if not isinstance(data, list):
        raise TypeError(
            f"Pinout expects a list of Pin dicts at the JSON root; got {type(data).__name__}"
        )
    pins = [from_dict(Pin, p) for p in data]
    return cls(pins=pins)
