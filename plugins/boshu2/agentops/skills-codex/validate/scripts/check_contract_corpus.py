#!/usr/bin/env python3
"""Run the shared verdict-contract golden corpus through the Python validator
and (when jsonschema is available) the canonical JSON schema.

The same cases run through the Go reader (cli/internal/verdictcheck
TestGoldenCorpus). Any disagreement between the three implementations is a
contract fork and must fail CI.

Exit 0: every case matches its expected outcome.
Exit 1: at least one implementation disagrees with the corpus.
"""
from __future__ import annotations

import importlib.util
import json
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
CASES = ROOT / "tests" / "fixtures" / "verdict-contract" / "cases"
SCHEMA = ROOT / "schemas" / "verdict.v2.schema.json"


def load_validate_module():
    path = pathlib.Path(__file__).with_name("validate.py")
    spec = importlib.util.spec_from_file_location("validate_corpus_subject", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict:
    """object_pairs_hook that fails closed on a duplicate key at any depth.

    Python's default json decode is last-wins (like Go's map decode), so a
    duplicated key would silently hide the real value and let a payload bind a
    digest its bytes never canonicalize to. The Go reader
    (cli/internal/verdictcheck) rejects the same class; this keeps the Python
    leg of the cross-language corpus in agreement.
    """
    seen: set[str] = set()
    for key, _ in pairs:
        if key in seen:
            raise ValueError(f"duplicate key: {key}")
        seen.add(key)
    return dict(pairs)


def python_verdict(module, case) -> tuple[bool, str]:
    raw = case.get("raw")
    if raw is not None:
        # The Python storage layer parses exactly one JSON document; simulate
        # its read of a payload with trailing data, and fail closed on any
        # duplicate key (mirrors the Go reader).
        try:
            decoder = json.JSONDecoder(object_pairs_hook=_reject_duplicate_keys)
            value, end = decoder.raw_decode(raw)
            if raw[end:].strip():
                return False, "trailing data"
            artifact = value
        except json.JSONDecodeError as exc:
            return False, f"parse: {exc}"
        except ValueError as exc:
            return False, str(exc)
    else:
        artifact = case["artifact"]
    try:
        module.validate_verdict_v2(artifact)
    except Exception as exc:  # ContractError or shape errors
        return False, str(exc)
    # Filename binding: stored artifacts are addressed by artifact_digest.
    if artifact.get("artifact_digest") != case["filename_digest"]:
        return False, "artifact_digest does not match filename"
    return True, ""


def schema_verdict(validator, case) -> tuple[bool, str]:
    raw = case.get("raw")
    if raw is not None:
        try:
            decoder = json.JSONDecoder()
            value, end = decoder.raw_decode(raw)
            if raw[end:].strip():
                return False, "trailing data"
        except json.JSONDecodeError as exc:
            return False, f"parse: {exc}"
        artifact = value
    else:
        artifact = case["artifact"]
    errors = sorted(validator.iter_errors(artifact), key=lambda e: e.json_path)
    if errors:
        return False, errors[0].message
    return True, ""


def main() -> int:
    module = load_validate_module()

    require_schema = os.environ.get("CONTRACT_CORPUS_REQUIRE_SCHEMA") == "1"
    validator = None
    try:
        import jsonschema

        schema = json.loads(SCHEMA.read_text())
        validator = jsonschema.Draft202012Validator(schema)
    except ImportError:
        if require_schema:
            print("check-contract-corpus: FAIL — jsonschema unavailable but the "
                  "schema leg is required (CONTRACT_CORPUS_REQUIRE_SCHEMA=1)", file=sys.stderr)
            return 1
        print("check-contract-corpus: jsonschema unavailable — schema leg skipped", file=sys.stderr)

    failures = []
    cases = sorted(CASES.glob("*.json"))
    if len(cases) < 10:
        print(f"check-contract-corpus: FAIL — suspiciously small corpus ({len(cases)} cases)")
        return 1
    for path in cases:
        case = json.loads(path.read_text())
        expected_valid = case["expected"] == "valid"

        ok, reason = python_verdict(module, case)
        if ok != expected_valid:
            failures.append(f"{case['name']}: python validator said {'valid' if ok else 'invalid'} "
                            f"({reason or 'no error'}), corpus expects {case['expected']}")

        if validator is not None:
            ok, reason = schema_verdict(validator, case)
            if expected_valid and not ok:
                failures.append(f"{case['name']}: schema rejected a valid case: {reason}")
            if not expected_valid and ok and not case.get("schema_lenient"):
                failures.append(f"{case['name']}: schema accepted an invalid case "
                                f"(mark schema_lenient only when JSON Schema cannot express the rule)")

    if failures:
        print("check-contract-corpus: FAIL — contract implementations disagree:")
        for failure in failures:
            print(f"  {failure}")
        return 1
    legs = "python+schema" if validator is not None else "python"
    print(f"check-contract-corpus: PASS ({len(cases)} cases, {legs})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
