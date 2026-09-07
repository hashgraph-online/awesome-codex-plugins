#!/usr/bin/env python3
"""Validate a private Han Hu style-calibration corpus and lint a draft conservatively."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def load_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"expected a JSON object in {path}")
    return data


def validate_corpus(root: Path) -> list[str]:
    errors: list[str] = []
    for required in ("calibration-profile.md", "corpus-index.json"):
        if not (root / required).is_file():
            errors.append(f"missing required corpus file: {required}")
    if errors:
        return errors

    try:
        index = load_json(root / "corpus-index.json")
    except ValueError as exc:
        return [str(exc)]

    cases = index.get("cases")
    if not isinstance(cases, list) or not cases:
        return ["corpus-index.json must contain a non-empty cases list"]
    for case in cases:
        if not isinstance(case, dict) or not case.get("id"):
            errors.append("every case needs a non-empty id")
            continue
        relative = case.get("relative_case_path")
        if not isinstance(relative, str) or not relative:
            errors.append(f"case {case['id']} is missing relative_case_path")
        elif not (root / relative).is_dir():
            errors.append(f"case {case['id']} points to a missing directory: {relative}")
        items = case.get("items")
        if not isinstance(items, list) or not items:
            errors.append(f"case {case['id']} must contain at least one item")
        elif any(not isinstance(item, dict) or not item.get("id") or not item.get("status") for item in items):
            errors.append(f"case {case['id']} has an item missing id or status")
    return errors


def lint_draft(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    findings: list[str] = []
    checks = [
        (r"\bpanel\b", "avoid 'panel'; use a direct subfigure reference such as Fig. 6a"),
        (r"Fig\.\s*\d+\([a-z]\)", "use Fig. 6a rather than Fig. 6(a)"),
        (r"\bproves?\b", "review whether proof-level wording is supported"),
        (r"\bnovel\b", "review whether novelty wording names a specific verified gap"),
    ]
    for pattern, message in checks:
        count = len(re.findall(pattern, text, flags=re.IGNORECASE))
        if count:
            findings.append(f"{path.name}: {count} occurrence(s): {message}")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("corpus_root", type=Path)
    parser.add_argument("--draft", type=Path, help="optional Markdown or text draft for conservative linting")
    parser.add_argument("--strict", action="store_true", help="return nonzero when the draft lint reports findings")
    args = parser.parse_args()

    errors = validate_corpus(args.corpus_root)
    if errors:
        print("Style-calibration corpus audit failed:")
        print("\n".join(f"- {item}" for item in errors))
        return 1
    print("Style-calibration corpus audit passed.")

    if args.draft:
        findings = lint_draft(args.draft)
        if findings:
            print("Draft style checks:")
            print("\n".join(f"- {item}" for item in findings))
            return 1 if args.strict else 0
        print("Draft style checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
