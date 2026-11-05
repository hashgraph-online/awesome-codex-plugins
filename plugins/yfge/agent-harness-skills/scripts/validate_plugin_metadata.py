#!/usr/bin/env python3
"""Validate plugin and extension packaging metadata."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import re
import sys
from typing import Any
from urllib.parse import urlparse


PLUGIN_NAME = "agent-harness-skills"
SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\."
    r"(0|[1-9]\d*)\."
    r"(0|[1-9]\d*)"
    r"(?:-(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*)(?:\."
    r"(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*))*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)
HEX_COLOR_RE = re.compile(r"^#[0-9A-F]{6}$", re.IGNORECASE)

CODEX_KEYS = {
    "id",
    "name",
    "version",
    "description",
    "skills",
    "apps",
    "mcpServers",
    "interface",
    "author",
    "homepage",
    "repository",
    "license",
    "keywords",
}
CODEX_INTERFACE_KEYS = {
    "displayName",
    "shortDescription",
    "longDescription",
    "developerName",
    "category",
    "capabilities",
    "websiteURL",
    "privacyPolicyURL",
    "termsOfServiceURL",
    "brandColor",
    "composerIcon",
    "logo",
    "screenshots",
    "defaultPrompt",
    "default_prompt",
}


@dataclass(frozen=True)
class MetadataIssue:
    path: Path
    message: str


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json_object(path: Path) -> tuple[dict[str, Any] | None, list[MetadataIssue]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None, [MetadataIssue(path, "missing JSON file")]
    except json.JSONDecodeError as exc:
        return None, [MetadataIssue(path, f"invalid JSON: {exc}")]

    if not isinstance(payload, dict):
        return None, [MetadataIssue(path, "must contain a JSON object")]
    return payload, []


def require_string(
    payload: dict[str, Any],
    key: str,
    path: Path,
    issues: list[MetadataIssue],
    *,
    prefix: str | None = None,
) -> str | None:
    value = payload.get(key)
    field = f"{prefix}.{key}" if prefix else key
    if not isinstance(value, str) or not value.strip():
        issues.append(MetadataIssue(path, f"`{field}` must be a non-empty string"))
        return None
    return value


def validate_same_value(
    payload: dict[str, Any],
    key: str,
    expected: str,
    path: Path,
    issues: list[MetadataIssue],
) -> None:
    value = require_string(payload, key, path, issues)
    if value is not None and value != expected:
        issues.append(MetadataIssue(path, f"`{key}` must be `{expected}`"))


def validate_https_url(
    payload: dict[str, Any],
    key: str,
    path: Path,
    issues: list[MetadataIssue],
    *,
    prefix: str | None = None,
) -> None:
    value = payload.get(key)
    if value is None:
        return
    field = f"{prefix}.{key}" if prefix else key
    if not isinstance(value, str) or not value.strip():
        issues.append(MetadataIssue(path, f"`{field}` must be a non-empty HTTPS URL"))
        return
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc:
        issues.append(MetadataIssue(path, f"`{field}` must be an HTTPS URL"))


def resolve_relative_path(root: Path, raw_path: str) -> Path:
    return (root / raw_path).resolve()


def validate_local_path(
    root: Path,
    payload: dict[str, Any],
    key: str,
    path: Path,
    issues: list[MetadataIssue],
    *,
    kind: str,
) -> Path | None:
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        issues.append(MetadataIssue(path, f"`{key}` must be a non-empty relative path"))
        return None
    candidate = Path(value)
    if candidate.is_absolute():
        issues.append(MetadataIssue(path, f"`{key}` must be relative to the repository root"))
        return None

    resolved = resolve_relative_path(root, value)
    try:
        resolved.relative_to(root.resolve())
    except ValueError:
        issues.append(MetadataIssue(path, f"`{key}` must stay inside the repository root"))
        return None

    if kind == "dir" and not resolved.is_dir():
        issues.append(MetadataIssue(path, f"`{key}` target is not a directory: {value}"))
    if kind == "file" and not resolved.is_file():
        issues.append(MetadataIssue(path, f"`{key}` target is not a file: {value}"))
    return resolved


def validate_codex_manifest(root: Path, issues: list[MetadataIssue]) -> dict[str, Any] | None:
    path = root / ".codex-plugin" / "plugin.json"
    payload, load_issues = load_json_object(path)
    issues.extend(load_issues)
    if payload is None:
        return None

    for key in sorted(set(payload) - CODEX_KEYS):
        issues.append(MetadataIssue(path, f"unsupported Codex manifest field `{key}`"))

    validate_same_value(payload, "id", PLUGIN_NAME, path, issues)
    validate_same_value(payload, "name", PLUGIN_NAME, path, issues)
    version = require_string(payload, "version", path, issues)
    if version is not None and SEMVER_RE.fullmatch(version) is None:
        issues.append(MetadataIssue(path, "`version` must be strict semver"))
    require_string(payload, "description", path, issues)
    require_string(payload, "license", path, issues)
    validate_https_url(payload, "homepage", path, issues)
    validate_https_url(payload, "repository", path, issues)

    author = payload.get("author")
    if not isinstance(author, dict):
        issues.append(MetadataIssue(path, "`author` must be an object"))
    else:
        require_string(author, "name", path, issues, prefix="author")

    skills_dir = validate_local_path(root, payload, "skills", path, issues, kind="dir")
    if skills_dir is None:
        issues.append(MetadataIssue(path, "`skills` must point at the packaged skills directory"))
    else:
        skill_files = sorted(skills_dir.glob("*/SKILL.md"))
        if not skill_files:
            issues.append(MetadataIssue(path, "`skills` directory must contain skill folders"))

    validate_local_path(root, payload, "apps", path, issues, kind="file")
    validate_local_path(root, payload, "mcpServers", path, issues, kind="file")

    interface = payload.get("interface")
    if not isinstance(interface, dict):
        issues.append(MetadataIssue(path, "`interface` must be an object"))
        return payload

    for key in sorted(set(interface) - CODEX_INTERFACE_KEYS):
        issues.append(MetadataIssue(path, f"unsupported Codex interface field `{key}`"))
    for key in (
        "displayName",
        "shortDescription",
        "longDescription",
        "developerName",
        "category",
    ):
        require_string(interface, key, path, issues, prefix="interface")
    if "defaultPrompt" not in interface and "default_prompt" not in interface:
        issues.append(MetadataIssue(path, "`interface.defaultPrompt` is required"))
    capabilities = interface.get("capabilities")
    if not isinstance(capabilities, list) or not all(
        isinstance(value, str) and value.strip() for value in capabilities
    ):
        issues.append(MetadataIssue(path, "`interface.capabilities` must be an array of strings"))

    for key in ("websiteURL", "privacyPolicyURL", "termsOfServiceURL"):
        validate_https_url(interface, key, path, issues, prefix="interface")
    brand_color = interface.get("brandColor")
    if brand_color is not None and (
        not isinstance(brand_color, str) or HEX_COLOR_RE.fullmatch(brand_color) is None
    ):
        issues.append(MetadataIssue(path, "`interface.brandColor` must use #RRGGBB"))

    for key in ("composerIcon", "logo"):
        validate_local_path(root, interface, key, path, issues, kind="file")
    screenshots = interface.get("screenshots", [])
    if not isinstance(screenshots, list):
        issues.append(MetadataIssue(path, "`interface.screenshots` must be an array"))
    else:
        for index, raw_path in enumerate(screenshots):
            if not isinstance(raw_path, str):
                issues.append(
                    MetadataIssue(path, f"`interface.screenshots[{index}]` must be a path")
                )
                continue
            validate_local_path(
                root,
                {f"screenshots[{index}]": raw_path},
                f"screenshots[{index}]",
                path,
                issues,
                kind="file",
            )

    return payload


def validate_cursor_manifest(root: Path, codex: dict[str, Any], issues: list[MetadataIssue]) -> None:
    path = root / ".cursor-plugin" / "plugin.json"
    payload, load_issues = load_json_object(path)
    issues.extend(load_issues)
    if payload is None:
        return

    validate_same_value(payload, "name", PLUGIN_NAME, path, issues)
    validate_same_value(payload, "version", str(codex.get("version", "")), path, issues)
    require_string(payload, "displayName", path, issues)
    require_string(payload, "description", path, issues)
    validate_local_path(root, payload, "skills", path, issues, kind="dir")


def validate_claude_manifest(root: Path, codex: dict[str, Any], issues: list[MetadataIssue]) -> None:
    path = root / ".claude-plugin" / "plugin.json"
    payload, load_issues = load_json_object(path)
    issues.extend(load_issues)
    if payload is None:
        return

    validate_same_value(payload, "name", PLUGIN_NAME, path, issues)
    validate_same_value(payload, "version", str(codex.get("version", "")), path, issues)
    require_string(payload, "description", path, issues)
    require_string(payload, "license", path, issues)


def validate_gemini_manifest(root: Path, codex: dict[str, Any], issues: list[MetadataIssue]) -> None:
    path = root / "gemini-extension.json"
    payload, load_issues = load_json_object(path)
    issues.extend(load_issues)
    if payload is None:
        return

    validate_same_value(payload, "name", PLUGIN_NAME, path, issues)
    validate_same_value(payload, "version", str(codex.get("version", "")), path, issues)
    require_string(payload, "description", path, issues)
    validate_local_path(root, payload, "contextFileName", path, issues, kind="file")


def validate_package_manifest(root: Path, codex: dict[str, Any], issues: list[MetadataIssue]) -> None:
    path = root / "package.json"
    payload, load_issues = load_json_object(path)
    issues.extend(load_issues)
    if payload is None:
        return

    validate_same_value(payload, "name", PLUGIN_NAME, path, issues)
    validate_same_value(payload, "version", str(codex.get("version", "")), path, issues)
    require_string(payload, "description", path, issues)
    validate_local_path(root, payload, "main", path, issues, kind="file")


def validate_metadata(root: Path) -> list[MetadataIssue]:
    issues: list[MetadataIssue] = []
    codex = validate_codex_manifest(root, issues)
    if codex is None:
        return issues

    validate_cursor_manifest(root, codex, issues)
    validate_claude_manifest(root, codex, issues)
    validate_gemini_manifest(root, codex, issues)
    validate_package_manifest(root, codex, issues)
    return issues


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate repository plugin metadata.")
    parser.add_argument(
        "root",
        nargs="?",
        default=str(repo_root()),
        help="Repository root to validate. Defaults to this script's repository.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root).expanduser().resolve()
    issues = validate_metadata(root)
    if issues:
        print("Plugin metadata validation FAILED:", file=sys.stderr)
        for issue in issues:
            print(f"  error: {issue.path}: {issue.message}", file=sys.stderr)
        return 1

    print("Plugin metadata validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
