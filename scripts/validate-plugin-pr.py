#!/usr/bin/env python3
"""Validate plugin submissions in PRs.

Checks that new or modified plugin bundles conform to the contribution spec:
- plugin.json exists and contains required fields
- composerIcon points to an existing file
- README entry exists for the plugin
- Plugin bundle files are present under plugins/<owner>/<repo>/

Usage:
    python3 scripts/validate-plugin-pr.py [--base-ref <ref>]

If --base-ref is not provided, defaults to origin/main.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
PLUGINS_DIR = REPO_ROOT / "plugins"
README_PATH = REPO_ROOT / "README.md"

REQUIRED_MANIFEST_FIELDS = ["name", "version", "description", "repository", "license"]
REQUIRED_INTERFACE_FIELDS = ["displayName", "shortDescription", "composerIcon"]
ICON_EXTENSIONS = {".svg", ".png", ".jpg", ".jpeg", ".webp", ".ico"}
MAX_ICON_SIZE_BYTES = 50 * 1024  # 50KB


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT)] + list(args),
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def get_changed_plugin_dirs(base_ref: str) -> list[Path]:
    """Find plugin directories that were added or modified in this branch."""
    output = git("diff", "--name-only", "--diff-filter=ACMR", base_ref, "--", "plugins/")
    if not output:
        return []

    changed_dirs: set[Path] = set()
    for line in output.splitlines():
        file_path = REPO_ROOT / line
        # Walk up to find the plugins/<owner>/<repo> root
        parts = file_path.relative_to(REPO_ROOT).parts
        if len(parts) >= 3 and parts[0] == "plugins":
            changed_dirs.add(REPO_ROOT / "plugins" / parts[1] / parts[2])

    return sorted(changed_dirs)


def validate_manifest(plugin_dir: Path) -> list[str]:
    """Validate the plugin.json manifest."""
    errors: list[str] = []
    manifest_path = plugin_dir / ".codex-plugin" / "plugin.json"

    if not manifest_path.exists():
        errors.append(f"Missing .codex-plugin/plugin.json")
        return errors

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        errors.append(f"plugin.json is not valid JSON: {e}")
        return errors

    if not isinstance(manifest, dict):
        errors.append("plugin.json root must be a JSON object")
        return errors

    for field in REQUIRED_MANIFEST_FIELDS:
        val = manifest.get(field)
        if val is None or (isinstance(val, str) and not val.strip()):
            errors.append(f"Missing or empty required field: {field}")

    # Validate interface block
    interface = manifest.get("interface")
    if not isinstance(interface, dict):
        errors.append("Missing or invalid 'interface' object in plugin.json")
        return errors

    for field in REQUIRED_INTERFACE_FIELDS:
        val = interface.get(field)
        if val is None or (isinstance(val, str) and not val.strip()):
            errors.append(f"Missing or empty interface.{field}")

    # Validate version is semver-ish
    version = manifest.get("version", "")
    if version and not re.match(r"^\d+\.\d+\.\d+", str(version)):
        errors.append(f"Version '{version}' does not follow semver (expected MAJOR.MINOR.PATCH)")

    # Validate name is lowercase/slug-safe
    name = manifest.get("name", "")
    if name and re.search(r"[A-Z\s]", str(name)):
        errors.append(f"Plugin name '{name}' should be lowercase and slug-safe (no spaces or uppercase)")

    return errors


def validate_icon(plugin_dir: Path) -> list[str]:
    """Validate that the icon referenced in plugin.json exists and meets requirements."""
    errors: list[str] = []
    manifest_path = plugin_dir / ".codex-plugin" / "plugin.json"

    if not manifest_path.exists():
        return [".codex-plugin/plugin.json does not exist, cannot validate icon"]

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return ["Cannot validate icon: plugin.json is not valid JSON"]

    interface = manifest.get("interface", {})
    composer_icon = interface.get("composerIcon", "")

    if not composer_icon or not str(composer_icon).strip():
        return ["Missing 'composerIcon' in plugin.json interface section"]

    # Resolve the icon path relative to plugin root
    icon_rel = str(composer_icon).strip()
    if icon_rel.startswith("./"):
        icon_rel = icon_rel[2:]
    elif icon_rel.startswith("/"):
        icon_rel = icon_rel[1:]

    icon_path = plugin_dir / icon_rel

    if not icon_path.exists():
        errors.append(f"Icon file not found: {icon_rel} (resolved to {icon_path})")
        errors.append(f"  Expected at: {icon_path.relative_to(REPO_ROOT)}")
        return errors

    # Check extension
    suffix = icon_path.suffix.lower()
    if suffix not in ICON_EXTENSIONS:
        errors.append(f"Icon has unsupported format '{suffix}'. Use SVG (preferred) or PNG.")

    # Check file size
    size = icon_path.stat().st_size
    if size > MAX_ICON_SIZE_BYTES:
        errors.append(f"Icon is {size / 1024:.1f}KB, exceeds 50KB limit. Optimize your SVG or use a smaller image.")

    if suffix == ".svg":
        content = icon_path.read_text(encoding="utf-8", errors="replace")
        # Check for embedded raster images (common anti-pattern)
        if "data:image/" in content or "base64" in content:
            errors.append("SVG icon contains embedded base64 raster data. Use vector paths instead.")
        # Check for placeholder text
        if "TODO" in content or "PLACEHOLDER" in content:
            errors.append("SVG icon contains TODO/PLACEHOLDER text. Replace with actual icon design.")

    return errors


def validate_readme_entry(plugin_dir: Path) -> list[str]:
    """Validate that a README.md entry exists for this plugin."""
    errors: list[str] = []

    if not README_PATH.exists():
        return ["README.md not found"]

    manifest_path = plugin_dir / ".codex-plugin" / "plugin.json"
    if not manifest_path.exists():
        return []

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []

    # Extract owner/repo from path
    parts = plugin_dir.relative_to(REPO_ROOT).parts
    if len(parts) < 3:
        return []
    owner, repo = parts[1], parts[2]

    readme_content = README_PATH.read_text(encoding="utf-8")

    # Check for a link to the repo
    repo_pattern = rf"\[([^\]]+)\]\(https://github\.com/{re.escape(owner)}/{re.escape(repo)}\)"
    if not re.search(repo_pattern, readme_content):
        errors.append(f"No README.md entry found linking to https://github.com/{owner}/{repo}")

    return errors


def validate_plugin_dir(plugin_dir: Path) -> tuple[list[str], list[str]]:
    """Validate a single plugin directory. Returns (errors, warnings)."""
    errors: list[str] = []
    warnings: list[str] = []

    rel_path = plugin_dir.relative_to(REPO_ROOT)

    # Check that the directory actually exists
    if not plugin_dir.is_dir():
        errors.append(f"Plugin directory does not exist: {rel_path}")
        return errors, warnings

    # Check for bare minimum structure
    codex_plugin_dir = plugin_dir / ".codex-plugin"
    if not codex_plugin_dir.exists():
        errors.append(f"Missing .codex-plugin/ directory in {rel_path}")

    # Validate manifest
    errors.extend(validate_manifest(plugin_dir))

    # Validate icon
    errors.extend(validate_icon(plugin_dir))

    # Validate README entry
    readme_errors = validate_readme_entry(plugin_dir)
    for err in readme_errors:
        warnings.append(err)  # README entry missing is a warning, not a hard block

    # Check for .codexignore (recommended but optional)
    if not (plugin_dir / ".codexignore").exists():
        warnings.append("No .codexignore file found (recommended)")

    return errors, warnings


def main() -> None:
    base_ref = "--base-ref"
    base_arg = None
    for i, arg in enumerate(sys.argv):
        if arg == base_ref and i + 1 < len(sys.argv):
            base_arg = sys.argv[i + 1]

    if not base_arg:
        # Try to detect base ref from CI or git
        if os.environ.get("GITHUB_BASE_REF"):
            base_arg = f"origin/{os.environ['GITHUB_BASE_REF']}"
        else:
            base_arg = "origin/main"

    # Verify base ref exists
    rev_parse = git("rev-parse", "--verify", base_arg)
    if not rev_parse:
        print(f"WARNING: Base ref '{base_arg}' not found, skipping validation")
        print("  (This is normal for the first commit on a new branch without CI)")
        sys.exit(0)

    changed_dirs = get_changed_plugin_dirs(base_arg)

    if not changed_dirs:
        print("No plugin directories changed. Nothing to validate.")
        sys.exit(0)

    print(f"Validating {len(changed_dirs)} changed plugin directory(ies)...\n")

    total_errors = 0
    total_warnings = 0
    has_failures = False

    for plugin_dir in changed_dirs:
        rel = plugin_dir.relative_to(REPO_ROOT)
        errors, warnings = validate_plugin_dir(plugin_dir)

        if not errors and not warnings:
            print(f"  PASS: {rel}")
            continue

        if errors:
            has_failures = True
            total_errors += len(errors)
            print(f"  FAIL: {rel} ({len(errors)} error(s), {len(warnings)} warning(s))")
            for err in errors:
                print(f"    x {err}")

        if warnings:
            total_warnings += len(warnings)
            for warn in warnings:
                print(f"    ! {warn}")

        print()

    if has_failures:
        print(f"Validation failed: {total_errors} error(s), {total_warnings} warning(s)")
        sys.exit(1)
    elif total_warnings:
        print(f"Validation passed with warnings: {total_warnings} warning(s)")
        sys.exit(0)
    else:
        print(f"All {len(changed_dirs)} plugin(s) passed validation.")
        sys.exit(0)


if __name__ == "__main__":
    main()
