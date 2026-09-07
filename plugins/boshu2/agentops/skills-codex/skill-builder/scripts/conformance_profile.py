#!/usr/bin/env python3
"""Load and evaluate the canonical AgentOps skill-conformance profile."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

import yaml

PROFILE_RELATIVE_PATH = Path(
    "skills/skill-builder/references/skill-conformance-profiles.yaml"
)
KNOWN_SEVERITIES = {"WARN", "FAIL"}
KNOWN_TRIGGER_FORMS = {"inline-marker", "block-marker", "metadata-list"}
REQUIRED_RULE_IDS = (
    "description-has-triggers",
    "constraints-frontloaded",
    "rationale-present",
    "verification-checkpoints",
    "output-spec-explicit",
    "quality-rubric",
    "references-modularization",
    "trigger-clarity",
)
KNOWN_EXTERNAL_CONTENT_POLICIES = {"observe-structure-only"}
REQUIRED_PROHIBITED_COPY_CATEGORIES = {
    "prose",
    "prompts",
    "scripts",
    "examples",
    "names",
}
REQUIRED_PROTECTED_FRONTMATTER_FIELDS = {"description"}


class ProfileError(ValueError):
    """Raised when the conformance profile is missing or malformed."""


def _mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ProfileError(f"profile configuration error: {label} must be a mapping")
    return value


def _string_list(value: Any, label: str) -> list[str]:
    if not isinstance(value, list) or not value or not all(isinstance(v, str) for v in value):
        raise ProfileError(
            f"profile configuration error: {label} must be a non-empty string list"
        )
    return value


def _positive_int(value: Any, label: str) -> int:
    if not isinstance(value, int) or value < 1:
        raise ProfileError(f"profile configuration error: {label} must be positive")
    return value


def load_profile(repo_root: Path, profile_id: str | None = None) -> dict[str, Any]:
    """Load and fully validate one profile from the authoritative YAML file."""
    path = repo_root / PROFILE_RELATIVE_PATH
    if not path.is_file():
        raise ProfileError(f"profile configuration missing: {path}")
    try:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ProfileError(f"profile configuration error in {path}: {exc}") from exc

    document = _mapping(document, "document")
    profiles = _mapping(document.get("profiles"), "profiles")
    selected = profile_id or document.get("default_profile")
    if not isinstance(selected, str) or not selected:
        raise ProfileError("profile configuration error: default_profile must be a string")
    if selected not in profiles:
        raise ProfileError(f"profile configuration error: unknown profile {selected!r}")
    profile = _mapping(profiles[selected], f"profiles.{selected}")
    if profile.get("id") != selected:
        raise ProfileError(
            f"profile configuration error: profile id must equal selected id {selected!r}"
        )

    limit = profile.get("kernel_max_lines")
    if not isinstance(limit, int) or limit < 1:
        raise ProfileError("profile configuration error: kernel_max_lines must be positive")

    trigger = _mapping(profile.get("trigger_forms"), "trigger_forms")
    accepted = _string_list(trigger.get("accepted"), "trigger_forms.accepted")
    unknown_forms = sorted(set(accepted) - KNOWN_TRIGGER_FORMS)
    if unknown_forms:
        raise ProfileError(
            f"profile configuration error: unknown trigger form(s): {', '.join(unknown_forms)}"
        )
    _string_list(trigger.get("description_markers"), "trigger_forms.description_markers")
    minimum = trigger.get("metadata_list_min_items")
    if not isinstance(minimum, int) or minimum < 1:
        raise ProfileError(
            "profile configuration error: metadata_list_min_items must be positive"
        )

    output = _mapping(profile.get("output_contract"), "output_contract")
    _string_list(output.get("section_headings"), "output_contract.section_headings")
    components = _mapping(
        output.get("required_components"), "output_contract.required_components"
    )
    if not components:
        raise ProfileError(
            "profile configuration error: output_contract.required_components is empty"
        )
    for component_id, component in components.items():
        if not isinstance(component_id, str):
            raise ProfileError("profile configuration error: component id must be a string")
        component = _mapping(component, f"output component {component_id}")
        _string_list(component.get("markers"), f"output component {component_id}.markers")

    clean_room = _mapping(profile.get("clean_room"), "clean_room")
    if clean_room.get("enabled") is not True:
        raise ProfileError("profile configuration error: clean_room.enabled must be true")
    policy = clean_room.get("external_content_policy")
    if policy not in KNOWN_EXTERNAL_CONTENT_POLICIES:
        raise ProfileError(
            "profile configuration error: clean_room.external_content_policy "
            f"must be one of {sorted(KNOWN_EXTERNAL_CONTENT_POLICIES)}, got {policy!r}"
        )
    categories = _string_list(
        clean_room.get("prohibited_copy_categories"),
        "clean_room.prohibited_copy_categories",
    )
    if len(categories) != len(set(categories)):
        raise ProfileError(
            "profile configuration error: clean_room.prohibited_copy_categories "
            "contains duplicates"
        )
    if set(categories) != REQUIRED_PROHIBITED_COPY_CATEGORIES:
        missing = sorted(REQUIRED_PROHIBITED_COPY_CATEGORIES - set(categories))
        unknown = sorted(set(categories) - REQUIRED_PROHIBITED_COPY_CATEGORIES)
        raise ProfileError(
            "profile configuration error: clean_room.prohibited_copy_categories "
            f"must name the exact known categories (missing={missing}, unknown={unknown})"
        )
    copy_detection = _mapping(clean_room.get("copy_detection"), "clean_room.copy_detection")
    _positive_int(
        copy_detection.get("minimum_fragment_characters"),
        "clean_room.copy_detection.minimum_fragment_characters",
    )
    _positive_int(
        copy_detection.get("minimum_name_characters"),
        "clean_room.copy_detection.minimum_name_characters",
    )
    protected_fields = _string_list(
        copy_detection.get("protected_frontmatter_fields"),
        "clean_room.copy_detection.protected_frontmatter_fields",
    )
    if len(protected_fields) != len(set(protected_fields)):
        raise ProfileError(
            "profile configuration error: "
            "clean_room.copy_detection.protected_frontmatter_fields contains duplicates"
        )
    if set(protected_fields) != REQUIRED_PROTECTED_FRONTMATTER_FIELDS:
        missing = sorted(REQUIRED_PROTECTED_FRONTMATTER_FIELDS - set(protected_fields))
        unknown = sorted(set(protected_fields) - REQUIRED_PROTECTED_FRONTMATTER_FIELDS)
        raise ProfileError(
            "profile configuration error: "
            "clean_room.copy_detection.protected_frontmatter_fields must name the "
            f"exact known fields (missing={missing}, unknown={unknown})"
        )
    _string_list(
        copy_detection.get("ignored_exact_lines"),
        "clean_room.copy_detection.ignored_exact_lines",
    )
    _string_list(
        copy_detection.get("ignored_line_prefixes"),
        "clean_room.copy_detection.ignored_line_prefixes",
    )

    rule_order = _string_list(profile.get("rule_order"), "rule_order")
    if len(rule_order) != len(set(rule_order)):
        raise ProfileError("profile configuration error: rule_order contains duplicates")
    rules = _mapping(profile.get("rules"), "rules")
    if set(rule_order) != set(rules):
        missing = sorted(set(rule_order) - set(rules))
        extra = sorted(set(rules) - set(rule_order))
        raise ProfileError(
            "profile configuration error: rule_order/rules mismatch "
            f"(missing={missing}, extra={extra})"
        )
    known_rules = set(REQUIRED_RULE_IDS)
    actual_rules = set(rules)
    if actual_rules != known_rules:
        missing = sorted(known_rules - actual_rules)
        unknown = sorted(actual_rules - known_rules)
        raise ProfileError(
            "profile configuration error: profile must declare the exact known rule IDs "
            f"(missing={missing}, unknown={unknown})"
        )
    if rule_order != list(REQUIRED_RULE_IDS):
        raise ProfileError(
            "profile configuration error: rule_order must use the canonical known rule "
            f"order {list(REQUIRED_RULE_IDS)}"
        )
    for rule_id in rule_order:
        rule = _mapping(rules[rule_id], f"rules.{rule_id}")
        severity = rule.get("severity")
        if severity not in KNOWN_SEVERITIES:
            raise ProfileError(
                f"profile configuration error: rule {rule_id} has unknown severity {severity!r}"
            )
        if "accepted_forms" in rule:
            forms = _string_list(
                rule["accepted_forms"], f"rules.{rule_id}.accepted_forms"
            )
            unknown = sorted(set(forms) - set(accepted))
            if unknown:
                raise ProfileError(
                    f"profile configuration error: rule {rule_id} names unknown forms {unknown}"
                )
    return profile


def split_frontmatter(text: str) -> tuple[str, str]:
    """Return raw YAML frontmatter and Markdown body."""
    if not text.startswith("---\n"):
        return "", text
    parts = text.split("\n---", 1)
    if len(parts) != 2:
        return "", text
    return parts[0][4:], parts[1].lstrip("-\n")


def _frontmatter_mapping(text: str) -> tuple[str, dict[str, Any]]:
    raw, _ = split_frontmatter(text)
    try:
        payload = yaml.safe_load(raw) if raw else {}
    except yaml.YAMLError as exc:
        raise ProfileError(f"skill frontmatter configuration error: {exc}") from exc
    return raw, _mapping(payload, "skill frontmatter")


def trigger_forms(text: str, profile: dict[str, Any]) -> list[str]:
    """Return accepted trigger form IDs found only in frontmatter semantics."""
    raw, frontmatter = _frontmatter_mapping(text)
    trigger = profile["trigger_forms"]
    markers = trigger["description_markers"]
    description = frontmatter.get("description", "")
    description = description if isinstance(description, str) else ""
    has_marker = any(marker.casefold() in description.casefold() for marker in markers)
    scalar = re.search(r"^description:\s*([|>])", raw, re.MULTILINE)

    found: set[str] = set()
    if has_marker:
        found.add("block-marker" if scalar else "inline-marker")
    metadata = frontmatter.get("metadata")
    trigger_list = metadata.get("triggers") if isinstance(metadata, dict) else None
    if isinstance(trigger_list, list) and len(trigger_list) >= trigger["metadata_list_min_items"]:
        found.add("metadata-list")
    return [form for form in trigger["accepted"] if form in found]


def output_component_results(text: str, profile: dict[str, Any]) -> dict[str, bool]:
    """Evaluate every required executable-handoff component in one output section."""
    _, body = split_frontmatter(text)
    headings = {heading.casefold() for heading in profile["output_contract"]["section_headings"]}
    section_lines: list[str] = []
    capturing = False
    for line in body.splitlines():
        heading = re.match(r"^##\s+(.+?)\s*$", line)
        if heading:
            normalized = heading.group(1).strip().casefold()
            if capturing:
                break
            capturing = normalized in headings
            continue
        if capturing:
            section_lines.append(line)
    section = "\n".join(section_lines).casefold()
    results: dict[str, bool] = {}
    for component_id, component in profile["output_contract"]["required_components"].items():
        results[component_id] = any(
            marker.casefold() in section for marker in component["markers"]
        )
    return results


def evaluation(skill_md: Path, profile: dict[str, Any]) -> dict[str, Any]:
    """Evaluate shared trigger, boundary, and output semantics for one skill."""
    try:
        text = skill_md.read_text(encoding="utf-8")
    except OSError as exc:
        raise ProfileError(f"skill read error: {skill_md}: {exc}") from exc
    _, frontmatter = _frontmatter_mapping(text)
    forms = trigger_forms(text, profile)
    components = output_component_results(text, profile)
    declared_output = frontmatter.get("output_contract")
    has_declared_output = (
        isinstance(declared_output, str) and bool(declared_output.strip())
    ) or (isinstance(declared_output, (dict, list)) and bool(declared_output))
    return {
        "profile_id": profile["id"],
        "kernel_max_lines": profile["kernel_max_lines"],
        "line_count": len(text.splitlines()),
        "trigger_forms": forms,
        "output_components": components,
        "output_complete": has_declared_output or all(components.values()),
    }


def clean_room_copies(
    external_source: Path, generated_dirs: list[Path], profile: dict[str, Any]
) -> list[str]:
    """Return external content copied into generated output under profile policy."""
    try:
        source = external_source.read_text(encoding="utf-8")
        generated = "\n".join(
            path.read_text(encoding="utf-8", errors="replace")
            for root in generated_dirs
            for path in root.rglob("*")
            if path.is_file()
        )
    except OSError as exc:
        raise ProfileError(f"clean-room verification read error: {exc}") from exc

    raw_frontmatter, body = split_frontmatter(source)
    try:
        source_metadata = yaml.safe_load(raw_frontmatter) if raw_frontmatter else {}
    except yaml.YAMLError as exc:
        raise ProfileError(f"external skill frontmatter error: {exc}") from exc
    source_metadata = _mapping(source_metadata, "external skill frontmatter")

    clean_room = profile["clean_room"]
    policy = clean_room["external_content_policy"]
    if policy != "observe-structure-only":
        raise ProfileError(
            f"profile configuration error: unsupported external_content_policy {policy!r}"
        )
    categories = set(clean_room["prohibited_copy_categories"])
    detection = clean_room["copy_detection"]
    minimum_fragment = detection["minimum_fragment_characters"]
    ignored_exact = set(detection["ignored_exact_lines"])
    ignored_prefixes = tuple(detection["ignored_line_prefixes"])
    generated_folded = generated.casefold()
    generated_normalized = " ".join(generated.split()).casefold()
    copied: list[str] = []

    if categories & {"prose", "prompts", "scripts", "examples"}:
        protected = {
            line.strip()
            for line in body.splitlines()
            if len(line.strip()) >= minimum_fragment
            and line.strip() not in ignored_exact
            and not line.lstrip().startswith(ignored_prefixes)
        }
        copied.extend(line for line in protected if line.casefold() in generated_folded)

        for field in detection["protected_frontmatter_fields"]:
            value = source_metadata.get(field)
            if not isinstance(value, str):
                continue
            normalized = " ".join(value.split())
            if (
                len(normalized) >= minimum_fragment
                and normalized.casefold() in generated_normalized
            ):
                copied.append(normalized)

    if "names" in categories:
        external_name = source_metadata.get("name", "")
        if (
            isinstance(external_name, str)
            and len(external_name.strip()) >= detection["minimum_name_characters"]
            and external_name.strip().casefold() in generated_folded
        ):
            copied.append(external_name.strip())
    return sorted(set(copied))


def emit_audit_tsv(skill_md: Path, profile: dict[str, Any]) -> None:
    """Emit shell-safe, validated profile/evaluation data for audit.sh."""
    result = evaluation(skill_md, profile)
    print(f"profile_id\t{result['profile_id']}")
    print(f"kernel_max_lines\t{result['kernel_max_lines']}")
    print(f"line_count\t{result['line_count']}")
    print(f"trigger_forms\t{','.join(result['trigger_forms'])}")
    print(f"output_complete\t{str(result['output_complete']).lower()}")
    for component_id, present in result["output_components"].items():
        print(f"output_component\t{component_id}\t{str(present).lower()}")
    for rule_id in profile["rule_order"]:
        rule = profile["rules"][rule_id]
        accepted = ",".join(rule.get("accepted_forms", []))
        print(f"rule\t{rule_id}\t{rule['severity']}\t{accepted}")


def main(argv: list[str] | None = None) -> int:
    """Validate a profile and optionally emit evaluation data for audit.sh."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--profile-id", default=None)
    parser.add_argument("--audit-tsv", type=Path)
    parser.add_argument("--verify-clean-room", type=Path, metavar="EXTERNAL_SKILL_MD")
    parser.add_argument("--generated-dir", type=Path, action="append", default=[])
    args = parser.parse_args(argv)
    try:
        profile = load_profile(args.repo_root, args.profile_id)
        if args.audit_tsv and args.verify_clean_room:
            raise ProfileError(
                "profile configuration error: choose one of --audit-tsv or --verify-clean-room"
            )
        if args.verify_clean_room:
            if not args.generated_dir:
                raise ProfileError(
                    "profile configuration error: --verify-clean-room requires --generated-dir"
                )
            copied = clean_room_copies(args.verify_clean_room, args.generated_dir, profile)
            if copied:
                raise ProfileError(
                    f"clean-room violation under profile {profile['id']}: copied external "
                    f"content: {copied[0]}"
                )
            print(profile["id"])
        elif args.audit_tsv:
            emit_audit_tsv(args.audit_tsv, profile)
        else:
            print(profile["id"])
    except ProfileError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
