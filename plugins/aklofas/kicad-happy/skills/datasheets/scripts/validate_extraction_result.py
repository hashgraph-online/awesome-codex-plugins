#!/usr/bin/env python3
"""Phase 3a — Validate a single per-task extraction result against its schema.

Wraps the inline per-task validator that `merge_results.py` runs at extract
time, exposed as a standalone CLI for the harness 4-check acceptance gate
(Check 1).

Input: a wrapped result file
    {task_id, schema_version, status, extracted_at, model_tier, model_id, data}

The `data` field is validated against `skills/datasheets/schemas/<task-type>.schema.json`.

Exit codes:
    0  data validates and status == "complete"
    1  schema validation failed, status != "complete", or unreadable result
    2  CLI / I/O error (missing schema, missing file, bad JSON in result wrapper)

Designed for `--task-type` to be any task name backed by a sibling
`<name>.schema.json` — Phase 3b's mcu/opamp/transistor/diode/crystal will work
without code changes.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource


REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_DIR = REPO_ROOT / "skills/datasheets/schemas"


def _build_registry() -> Registry:
    registry = Registry()
    for schema_path in SCHEMA_DIR.glob("*.schema.json"):
        schema = json.loads(schema_path.read_text())
        uri = schema.get("$id")
        if uri:
            registry = registry.with_resource(uri, Resource.from_contents(schema))
    return registry


def _validate(data, schema: dict) -> "str | None":
    registry = _build_registry()
    validator = Draft202012Validator(schema, registry=registry)
    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path))
    if not errors:
        return None
    e0 = errors[0]
    path = "/".join(str(p) for p in e0.absolute_path) or "<root>"
    return f"{path}: {e0.message}"


def _resolve_schema(task_type: str) -> Path:
    return SCHEMA_DIR / f"{task_type}.schema.json"


def validate_result(result_file: Path, task_type: str) -> "tuple[int, str]":
    """Return (exit_code, message). exit_code semantics match module docstring."""
    schema_path = _resolve_schema(task_type)
    if not schema_path.exists():
        return 2, f"schema not found for task-type {task_type!r}: {schema_path}"

    if not result_file.exists():
        return 2, f"result file not found: {result_file}"

    try:
        wrapper = json.loads(result_file.read_text())
    except json.JSONDecodeError as exc:
        return 2, f"result file is not valid JSON: {exc}"

    status = wrapper.get("status")
    if status != "complete":
        err = wrapper.get("error") or "no error message provided"
        return 1, f"result status is {status!r} (expected 'complete'): {err}"

    if "data" not in wrapper:
        return 1, "result wrapper has no 'data' field"

    schema = json.loads(schema_path.read_text())
    err = _validate(wrapper["data"], schema)
    if err:
        return 1, f"schema validation: {err}"

    return 0, f"valid: {result_file.name} matches {schema_path.name}"


def main(argv: "list[str] | None" = None) -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Validate a single per-task extraction result against its declared schema. "
            "Used by the harness 4-check gate (Check 1)."
        ),
    )
    ap.add_argument(
        "--result-file",
        type=Path,
        required=True,
        help="path to <mpn>.<task_id>.result.json",
    )
    ap.add_argument(
        "--task-type",
        required=True,
        help="task name; resolves to skills/datasheets/schemas/<task-type>.schema.json",
    )
    ap.add_argument(
        "--json",
        dest="emit_json",
        action="store_true",
        help="emit a JSON summary to stdout instead of human text",
    )
    args = ap.parse_args(argv)

    code, message = validate_result(args.result_file, args.task_type)

    if args.emit_json:
        json.dump(
            {
                "valid": code == 0,
                "exit_code": code,
                "message": message,
                "result_file": str(args.result_file),
                "task_type": args.task_type,
            },
            sys.stdout,
            indent=2,
        )
        sys.stdout.write("\n")
    else:
        stream = sys.stdout if code == 0 else sys.stderr
        print(message, file=stream)

    return code


if __name__ == "__main__":
    sys.exit(main())
