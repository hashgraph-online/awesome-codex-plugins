"""Standalone CLI to validate a review_annotations.json file.

Exit codes:
  0 — valid
  1 — schema invalid
  2 — I/O / argument error

JSON output format (with --json):
  {"valid": bool, "errors": [<str>, ...], "review_path": "..."}
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCHEMA_PATH = (Path(__file__).resolve().parents[1] / "schemas"
                / "review_annotations.schema.json")


def main():
    p = argparse.ArgumentParser(description="Validate review_annotations.json against schema.")
    p.add_argument("--review", required=True, type=Path)
    p.add_argument("--json", dest="emit_json", action="store_true")
    args = p.parse_args()

    try:
        review = json.loads(args.review.read_text())
    except FileNotFoundError:
        msg = f"review file not found: {args.review}"
        if args.emit_json:
            print(json.dumps({"valid": False, "errors": [msg],
                                "review_path": str(args.review)}))
        else:
            print(msg, file=sys.stderr)
        return 2
    except json.JSONDecodeError as e:
        msg = f"review JSON malformed: {e}"
        if args.emit_json:
            print(json.dumps({"valid": False, "errors": [msg],
                                "review_path": str(args.review)}))
        else:
            print(msg, file=sys.stderr)
        return 2

    # Stdlib-only mini-validator (audit C2). Matches jsonschema's
    # iter_errors() surface for backward-compat with the prior consumer.
    from _mini_jsonschema import iter_errors

    schema = json.loads(SCHEMA_PATH.read_text())
    errors = sorted(iter_errors(review, schema),
                     key=lambda e: list(e.path))
    error_msgs = [f"{'/'.join(str(p) for p in e.path)}: {e.message}" for e in errors]

    if args.emit_json:
        print(json.dumps({
            "valid": len(errors) == 0,
            "errors": error_msgs,
            "review_path": str(args.review),
        }, indent=2))
    else:
        if errors:
            for msg in error_msgs:
                print(f"  {msg}", file=sys.stderr)
        else:
            print(f"valid: {args.review}")
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
