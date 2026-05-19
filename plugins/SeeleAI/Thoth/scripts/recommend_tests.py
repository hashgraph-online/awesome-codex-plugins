#!/usr/bin/env python3
"""Recommend targeted pytest and selftest commands from changed paths."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from thoth.test_targets import (
    build_pytest_command,
    build_selftest_command,
    recommended_selftest_cases_for_paths,
    recommended_targets_for_paths,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Recommend targeted pytest targets and atomic selftest cases for changed Thoth paths."
    )
    parser.add_argument("paths", nargs="+", help="Changed repo-relative or absolute paths.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of human-readable text.")
    args = parser.parse_args(argv)

    normalized_paths = [str(Path(path)) for path in args.paths]
    target_ids = recommended_targets_for_paths(normalized_paths)
    selftest_cases = recommended_selftest_cases_for_paths(normalized_paths)
    payload = {
        "paths": normalized_paths,
        "recommended_targets": target_ids,
        "pytest_command": build_pytest_command(target_ids),
        "recommended_selftest_cases": selftest_cases,
        "selftest_command": build_selftest_command(selftest_cases),
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print("Paths:")
    for path in normalized_paths:
        print(f"- {path}")
    print("")
    if target_ids:
        print("Recommended pytest targets:")
        for target_id in target_ids:
            print(f"- {target_id}")
        print("")
        print("Pytest command:")
        print(payload["pytest_command"])
    else:
        print("Recommended pytest targets:")
        print("- none matched the manifest")
    print("")
    if selftest_cases:
        print("Recommended selftest cases:")
        for case_id in selftest_cases:
            print(f"- {case_id}")
        print("")
        print("Selftest command:")
        print(payload["selftest_command"])
    else:
        print("Recommended selftest cases:")
        print("- none matched the manifest")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
