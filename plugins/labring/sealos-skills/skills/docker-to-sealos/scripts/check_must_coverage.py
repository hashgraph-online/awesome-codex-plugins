#!/usr/bin/env python3
"""Validate coverage mapping between SKILL MUST bullets and enforcement rules."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List, Mapping, Sequence, Set, Tuple

import yaml


MUST_SECTION_START = "## MUST Rules (Condensed)"
MUST_SECTION_END = "## Validation Commands"
ALLOWED_ENFORCEMENT_TYPES = {"rule", "manual"}


def normalize_line(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def extract_must_bullets(skill_text: str) -> List[str]:
    if MUST_SECTION_START not in skill_text or MUST_SECTION_END not in skill_text:
        raise ValueError("unable to locate MUST section boundaries in SKILL.md")

    start = skill_text.index(MUST_SECTION_START)
    end = skill_text.index(MUST_SECTION_END, start)
    section = skill_text[start:end]

    bullets: List[str] = []
    for raw_line in section.splitlines():
        match = re.match(r"^\s*-\s+(.+?)\s*$", raw_line)
        if match is None:
            continue
        bullet = normalize_line(match.group(1))
        if not bullet or bullet.endswith(":"):
            continue
        bullets.append(bullet)

    return bullets


def load_rule_ids(rules_file: Path) -> Set[str]:
    data = yaml.safe_load(rules_file.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("rules"), list):
        raise ValueError(f"invalid rules registry format: {rules_file}")

    ids: Set[str] = set()
    for item in data["rules"]:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str):
            raise ValueError(f"invalid rule entry in registry: {item!r}")
        ids.add(item["id"])
    return ids


def load_must_mapping(mapping_file: Path) -> Dict[str, Mapping[str, str]]:
    data = yaml.safe_load(mapping_file.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("must_rules"), list):
        raise ValueError(f"invalid must-rules mapping format: {mapping_file}")

    entries: Dict[str, Mapping[str, str]] = {}
    for item in data["must_rules"]:
        if not isinstance(item, dict):
            raise ValueError(f"invalid must-rules entry: {item!r}")

        must = item.get("must")
        enforcement = item.get("enforcement")
        if not isinstance(must, str) or not isinstance(enforcement, dict):
            raise ValueError(f"invalid must-rules entry: {item!r}")

        must_key = normalize_line(must)
        if must_key in entries:
            raise ValueError(f"duplicate must mapping entry: {must}")

        enforcement_type = enforcement.get("type")
        target = enforcement.get("target")
        note = enforcement.get("note")

        if enforcement_type not in ALLOWED_ENFORCEMENT_TYPES:
            allowed = ", ".join(sorted(ALLOWED_ENFORCEMENT_TYPES))
            raise ValueError(f"invalid enforcement type for must entry {must!r}: {enforcement_type!r} (allowed: {allowed})")
        if enforcement_type == "rule" and not isinstance(target, str):
            raise ValueError(f"rule enforcement must define string target for must entry: {must!r}")
        if enforcement_type == "manual" and not isinstance(note, str):
            raise ValueError(f"manual enforcement must define note for must entry: {must!r}")

        entries[must_key] = {
            "type": enforcement_type,
            "target": str(target) if isinstance(target, str) else "",
            "note": str(note) if isinstance(note, str) else "",
        }

    return entries


def validate_must_coverage(skill_file: Path, mapping_file: Path, rules_file: Path) -> List[str]:
    errors: List[str] = []

    bullets = extract_must_bullets(skill_file.read_text(encoding="utf-8"))
    bullet_keys = [normalize_line(item) for item in bullets]
    mapping = load_must_mapping(mapping_file)
    rule_ids = load_rule_ids(rules_file)

    missing = [item for item in bullet_keys if item not in mapping]
    extras = [item for item in mapping.keys() if item not in set(bullet_keys)]

    if missing:
        errors.append("missing MUST mappings:")
        errors.extend([f"  - {item}" for item in missing])

    if extras:
        errors.append("stale MUST mappings (not found in SKILL.md MUST section):")
        errors.extend([f"  - {item}" for item in extras])

    for must_text, enforcement in mapping.items():
        if enforcement["type"] != "rule":
            continue
        target = enforcement["target"]
        if target not in rule_ids:
            errors.append(f"rule mapping points to undefined rule id: {target} (must: {must_text})")

    return errors


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate MUST bullet coverage mapping")
    parser.add_argument("--skill", default="SKILL.md", help="Path to SKILL.md")
    parser.add_argument(
        "--mapping",
        default="references/must-rules-map.yaml",
        help="Path to MUST coverage mapping file",
    )
    parser.add_argument(
        "--rules-file",
        default="references/rules-registry.yaml",
        help="Path to machine-readable rules registry",
    )
    return parser.parse_args(argv)


def resolve_path(value: str, base: Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return (base / path).resolve()


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    skill_file = Path(args.skill).resolve()
    skill_root = skill_file.parent
    mapping_file = resolve_path(args.mapping, skill_root)
    rules_file = resolve_path(args.rules_file, skill_root)

    for required in (skill_file, mapping_file, rules_file):
        if not required.exists():
            print(f"ERROR: file not found: {required}")
            return 2

    try:
        errors = validate_must_coverage(skill_file, mapping_file, rules_file)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 2

    if errors:
        print("MUST coverage check failed:")
        for err in errors:
            print(f"- {err}")
        return 1

    print("MUST coverage check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
