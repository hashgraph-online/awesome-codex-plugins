#!/usr/bin/env python3
"""Phase 3a — Diff a harness sanity vector against an extraction JSON.

Used by the harness 4-check acceptance gate (check #4). Pure function: no
LLM, no state, no network. Loads YAML vector, walks per-field expected
values, resolves dotted paths against extraction JSON, compares within
declared tolerance.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml


DEFAULT_TOLERANCE_PCT = 5.0


def _resolve_path(extraction: dict, dotted: str):
    """Resolve a dotted path. Each segment is a dict key.

    Lists at the terminal position are unwrapped via `_spec_value_pick`;
    intermediate list indices are NOT supported (e.g., 'regulator.vin_range[0].max').
    Phase 3a operates on single-condition SpecValue lists; multi-condition
    indexing is deferred to v1.5.
    """
    cur = extraction
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def _spec_value_pick(value, key: str):
    """SpecValue lists carry [{min, typ, max, unit, ...}]. Scalars are used as-is.

    For list values, we pick the first element's `key` (Phase 3a is single-condition).
    For scalar values (int/float/bool/str), only the `typ` key has meaning — the
    scalar IS the typical value, with no min/max/unit. This lets sanity vectors
    write `expected: {typ: 5}` for plain scalar fields like `package.pin_count`.
    """
    if isinstance(value, list) and value:
        return value[0].get(key) if isinstance(value[0], dict) else None
    if isinstance(value, dict):
        return value.get(key)
    if isinstance(value, (int, float, bool, str)):
        return value if key == "typ" else None
    return None


def _within_tolerance(actual: float, expected: float, tol_pct: float) -> bool:
    if expected == 0:
        return abs(actual) <= tol_pct / 100.0
    return abs((actual - expected) / expected) * 100.0 <= tol_pct


def _check_numeric_spec(actual_value, expected: dict, tol_pct: float) -> tuple[bool, str | None, dict]:
    """`expected` like {min: 4.5, typ: null, max: 40, unit: 'V'}.
    Each populated key (min/typ/max) must match within tolerance.
    Unit must match exactly (string compare).
    Returns (pass, reason, debug_dict).
    """
    debug = {"checked": [], "actual": {}}
    if actual_value is None:
        return False, "missing in extraction", debug

    if "unit" in expected:
        actual_unit = _spec_value_pick(actual_value, "unit")
        debug["actual"]["unit"] = actual_unit
        if actual_unit != expected["unit"]:
            return False, f"unit mismatch: expected {expected['unit']!r}, got {actual_unit!r}", debug

    for key in ("min", "typ", "max"):
        if key not in expected or expected[key] is None:
            continue
        actual_n = _spec_value_pick(actual_value, key)
        debug["actual"][key] = actual_n
        if actual_n is None:
            return False, f"{key} missing", debug
        try:
            actual_f = float(actual_n)
            exp_f = float(expected[key])
        except (TypeError, ValueError):
            return False, f"{key} not numeric (actual={actual_n!r}, expected={expected[key]!r})", debug
        if not _within_tolerance(actual_f, exp_f, tol_pct):
            return False, f"{key}={actual_f} outside ±{tol_pct}% of {exp_f}", debug
        debug["checked"].append(key)
    return True, None, debug


def _check_enum(actual_value, expected_enum) -> tuple[bool, str | None]:
    """`expected_enum` is either a scalar string or a list of strings."""
    allowed = expected_enum if isinstance(expected_enum, list) else [expected_enum]
    if actual_value in allowed:
        return True, None
    return False, f"expected one of {allowed}, got {actual_value!r}"


def diff(vector: dict, extraction: dict) -> dict:
    fields_out = []
    for f in vector.get("fields", []):
        path = f["path"]
        actual = _resolve_path(extraction, path)
        entry = {"path": path, "expected": None, "actual": None, "pass": False, "reason": None}
        if "expected_enum" in f:
            entry["expected"] = f["expected_enum"]
            entry["actual"] = actual if not isinstance(actual, dict) else _spec_value_pick(actual, "value")
            if actual is None:
                entry["pass"] = False
                entry["reason"] = "missing in extraction"
            else:
                ok, why = _check_enum(actual, f["expected_enum"])
                entry["pass"] = ok
                entry["reason"] = why
        elif "expected" in f:
            tol = float(f.get("tolerance_pct", DEFAULT_TOLERANCE_PCT))
            entry["expected"] = f["expected"]
            ok, why, dbg = _check_numeric_spec(actual, f["expected"], tol)
            entry["pass"] = ok
            entry["reason"] = why
            entry["actual"] = dbg["actual"]
            entry["tolerance_pct"] = tol
        else:
            entry["reason"] = "vector field has neither expected nor expected_enum"
        if "page" in f:
            entry["expected_page"] = f["page"]
        fields_out.append(entry)
    passed = sum(1 for x in fields_out if x["pass"])
    failed = len(fields_out) - passed
    return {
        "schema_version": "1.0",
        "mpn": vector.get("mpn"),
        "fields": fields_out,
        "summary": {"total": len(fields_out), "passed": passed, "failed": failed},
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Diff a sanity vector against an extraction JSON.")
    ap.add_argument("vector_path", type=Path)
    ap.add_argument("extraction_path", type=Path)
    args = ap.parse_args(argv)

    vector = yaml.safe_load(args.vector_path.read_text())
    extraction = json.loads(args.extraction_path.read_text())
    report = diff(vector, extraction)
    print(json.dumps(report, indent=2, default=str))
    return 0 if report["summary"]["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
