#!/usr/bin/env python3
"""Consistency checker CLI for docker-to-sealos skill documents."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional, Sequence

from check_consistency_parser import resolve_path
from check_consistency_rule_registry import REGISTERED_RULES
from check_consistency_runner import run_checks


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate docker-to-sealos doc consistency")
    parser.add_argument("--skill", default="SKILL.md", help="Path to SKILL.md")
    parser.add_argument("--references", default="references", help="Path to references directory")
    parser.add_argument(
        "--rules-file",
        default="references/rules-registry.yaml",
        help="Path to machine-readable rules registry",
    )
    parser.add_argument("--only", default="", help="Comma-separated rule IDs to run")
    parser.add_argument(
        "--artifacts",
        default="",
        help=(
            "Comma-separated additional files/directories to scan. "
            "Use this to validate generated manifests such as template/<app>/index.yaml"
        ),
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)

    skill_path = Path(args.skill).resolve()
    if not skill_path.exists():
        print(f"ERROR: skill file not found: {skill_path}")
        return 2

    skill_root = skill_path.parent
    references_dir = resolve_path(args.references, skill_root)
    rules_file = resolve_path(args.rules_file, skill_root)

    if not references_dir.exists():
        print(f"ERROR: references directory not found: {references_dir}")
        return 2
    if not rules_file.exists():
        print(f"ERROR: rules registry not found: {rules_file}")
        return 2

    only_rules = [item.strip() for item in args.only.split(",") if item.strip()]
    additional_include_paths = [item.strip() for item in args.artifacts.split(",") if item.strip()]

    try:
        violations = run_checks(
            skill_path=skill_path,
            references_dir=references_dir,
            registry_path=rules_file,
            only_rules=only_rules or None,
            additional_include_paths=additional_include_paths or None,
        )
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 2

    if violations:
        print("Consistency check failed with the following issues:")
        for item in violations:
            print(f"- [{item.rule_id}/{item.severity}] {item.path}:{item.line}: {item.message}")
        return 1

    total = len(only_rules) if only_rules else len(REGISTERED_RULES)
    print(f"Consistency check passed ({total} rules).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
