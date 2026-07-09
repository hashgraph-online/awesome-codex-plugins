#!/usr/bin/env python3
"""Validate plugin submissions in PRs.

Two validation paths:

1. Bundle diff path (plugins/** changed):
   Validates committed plugin bundles against the contribution spec:
   - plugin.json exists and contains required fields
   - composerIcon points to an existing file
   - README entry exists for the plugin

2. README-entry path (README.md changed, no bundle):
   For new README entries that don't have a matching local bundle yet,
   fetches the source repo archive and validates plugin.json and icon
   presence there. This is the normal contributor flow: they add a
   README line, the generator mirrors the bundle later.

Usage:
    python3 scripts/validate-plugin-pr.py [--base-ref <ref>]

If --base-ref is not provided, defaults to origin/main.
"""

from __future__ import annotations

import io
import json
import os
import re
import subprocess
import sys
import zipfile
from pathlib import Path, PurePosixPath
from urllib.request import Request, urlopen

REPO_ROOT = Path(__file__).parent.parent
PLUGINS_DIR = REPO_ROOT / "plugins"
README_PATH = REPO_ROOT / "README.md"

REQUIRED_MANIFEST_FIELDS = ["name", "version", "description", "repository", "license"]
REQUIRED_INTERFACE_FIELDS = ["displayName", "shortDescription", "composerIcon"]
ICON_EXTENSIONS = {".svg", ".png", ".jpg", ".jpeg", ".webp", ".ico"}
MAX_ICON_SIZE_BYTES = 50 * 1024  # 50KB
REQUEST_TIMEOUT_SECONDS = 60
USER_AGENT = "awesome-codex-plugins-validator"

# Regex for README plugin entries
README_ENTRY_RE = re.compile(
    r"^- \[([^\]]+)\]\((https://github\.com/"
    r"([^/]+)/([^)#]+?))(?:[?#][^)]*)?\)\s*[-\u2013]\s*(.+)",
    re.MULTILINE,
)


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT)] + list(args),
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


# ---------------------------------------------------------------------------
# Helpers for fetching source repo archives
# ---------------------------------------------------------------------------


def fetch_repo_archive(owner: str, repo: str) -> zipfile.ZipFile:
    """Download the HEAD.zip archive for owner/repo."""
    url = f"https://github.com/{owner}/{repo}/archive/HEAD.zip"
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
        return zipfile.ZipFile(io.BytesIO(response.read()))


def find_plugin_root(archive: zipfile.ZipFile) -> PurePosixPath | None:
    """Find the directory containing .codex-plugin/plugin.json in the archive."""
    names = [n for n in archive.namelist() if n.endswith("/.codex-plugin/plugin.json")]
    if not names:
        return None
    # If multiple, prefer root-level (shortest path)
    names.sort(key=len)
    return PurePosixPath(names[0]).parent.parent


def load_manifest_from_archive(
    archive: zipfile.ZipFile, plugin_root: PurePosixPath
) -> dict | None:
    """Load plugin.json from the archive at the given root."""
    manifest_name = plugin_root.joinpath(".codex-plugin", "plugin.json").as_posix()
    try:
        return json.loads(archive.read(manifest_name).decode("utf-8"))
    except (KeyError, json.JSONDecodeError):
        return None


# ---------------------------------------------------------------------------
# Validation logic (shared between local and remote)
# ---------------------------------------------------------------------------


def validate_manifest_fields(manifest: dict) -> list[str]:
    """Validate manifest fields. Works for both local and fetched manifests."""
    errors: list[str] = []

    for field in REQUIRED_MANIFEST_FIELDS:
        val = manifest.get(field)
        if val is None or (isinstance(val, str) and not val.strip()):
            errors.append(f"Missing or empty required field: {field}")

    interface = manifest.get("interface")
    if not isinstance(interface, dict):
        errors.append("Missing or invalid 'interface' object in plugin.json")
        return errors

    for field in REQUIRED_INTERFACE_FIELDS:
        val = interface.get(field)
        if val is None or (isinstance(val, str) and not val.strip()):
            errors.append(f"Missing or empty interface.{field}")

    version = manifest.get("version", "")
    if version and not re.match(r"^\d+\.\d+\.\d+", str(version)):
        errors.append(f"Version '{version}' does not follow semver (expected MAJOR.MINOR.PATCH)")

    name = manifest.get("name", "")
    if name and re.search(r"[A-Z\s]", str(name)):
        errors.append(f"Plugin name '{name}' should be lowercase and slug-safe (no spaces or uppercase)")

    return errors


def validate_local_bundle(plugin_dir: Path) -> tuple[list[str], list[str]]:
    """Validate a committed plugin directory. Returns (errors, warnings)."""
    errors: list[str] = []
    warnings: list[str] = []

    rel_path = plugin_dir.relative_to(REPO_ROOT)

    if not plugin_dir.is_dir():
        errors.append(f"Plugin directory does not exist: {rel_path}")
        return errors, warnings

    manifest_path = plugin_dir / ".codex-plugin" / "plugin.json"
    if not manifest_path.exists():
        errors.append(f"Missing .codex-plugin/plugin.json in {rel_path}")
        return errors, warnings

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        errors.append(f"plugin.json is not valid JSON: {e}")
        return errors, warnings

    errors.extend(validate_manifest_fields(manifest))

    # Validate icon locally
    interface = manifest.get("interface", {})
    composer_icon = str(interface.get("composerIcon", "")).strip()
    if composer_icon:
        icon_rel = composer_icon
        if icon_rel.startswith("./"):
            icon_rel = icon_rel[2:]
        elif icon_rel.startswith("/"):
            icon_rel = icon_rel[1:]
        icon_path = plugin_dir / icon_rel
        if not icon_path.exists():
            errors.append(f"Icon file not found: {icon_rel} (resolved to {icon_path.relative_to(REPO_ROOT)})")
        else:
            suffix = icon_path.suffix.lower()
            if suffix not in ICON_EXTENSIONS:
                errors.append(f"Icon has unsupported format '{suffix}'. Use SVG (preferred) or PNG.")
            size = icon_path.stat().st_size
            if size > MAX_ICON_SIZE_BYTES:
                errors.append(f"Icon is {size / 1024:.1f}KB, exceeds 50KB limit.")
            if suffix == ".svg":
                content = icon_path.read_text(encoding="utf-8", errors="replace")
                if "data:image/" in content or "base64" in content:
                    errors.append("SVG icon contains embedded base64 raster data.")
                if "TODO" in content or "PLACEHOLDER" in content:
                    errors.append("SVG icon contains TODO/PLACEHOLDER text.")

    # README entry check (warning only)
    parts = plugin_dir.relative_to(REPO_ROOT).parts
    if len(parts) >= 3:
        owner, repo_dir = parts[1], parts[2]
        readme_content = README_PATH.read_text(encoding="utf-8") if README_PATH.exists() else ""
        repo_pattern = rf"\[([^\]]+)\]\(https://github\.com/{re.escape(owner)}/{re.escape(repo_dir)}\)"
        if not re.search(repo_pattern, readme_content):
            warnings.append(f"No README.md entry found linking to https://github.com/{owner}/{repo_dir}")

    if not (plugin_dir / ".codexignore").exists():
        warnings.append("No .codexignore file found (recommended)")

    return errors, warnings


def validate_remote_repo(owner: str, repo: str) -> tuple[list[str], list[str]]:
    """Fetch and validate a plugin from its source GitHub repo.

    Returns (errors, warnings).
    """
    errors: list[str] = []
    warnings: list[str] = []

    try:
        archive = fetch_repo_archive(owner, repo)
    except Exception as e:
        return ([f"Failed to fetch source repo https://github.com/{owner}/{repo}: {e}"], [])

    plugin_root = find_plugin_root(archive)
    if plugin_root is None:
        errors.append(
            f"Source repo https://github.com/{owner}/{repo} does not contain "
            f".codex-plugin/plugin.json"
        )
        return errors, warnings

    manifest = load_manifest_from_archive(archive, plugin_root)
    if manifest is None:
        errors.append("Could not read valid plugin.json from source repo")
        return errors, warnings

    errors.extend(validate_manifest_fields(manifest))

    # Check icon exists in the archive
    interface = manifest.get("interface", {})
    composer_icon = str(interface.get("composerIcon", "")).strip()
    if composer_icon:
        icon_rel = composer_icon
        if icon_rel.startswith("./"):
            icon_rel = icon_rel[2:]
        elif icon_rel.startswith("/"):
            icon_rel = icon_rel[1:]
        icon_archive_path = plugin_root.joinpath(PurePosixPath(icon_rel)).as_posix()
        try:
            icon_data = archive.read(icon_archive_path)
            if len(icon_data) > MAX_ICON_SIZE_BYTES:
                errors.append(f"Icon is {len(icon_data) / 1024:.1f}KB, exceeds 50KB limit.")
        except KeyError:
            errors.append(
                f"Icon file not found in source repo at: {icon_rel} "
                f"(referenced by composerIcon in plugin.json)"
            )

    return errors, warnings


# ---------------------------------------------------------------------------
# Changed file detection
# ---------------------------------------------------------------------------


def get_changed_plugin_dirs(base_ref: str) -> list[Path]:
    """Find plugin directories that were added or modified in this branch."""
    output = git("diff", "--name-only", "--diff-filter=ACMR", base_ref, "--", "plugins/")
    if not output:
        return []

    changed_dirs: set[Path] = set()
    for line in output.splitlines():
        file_path = REPO_ROOT / line
        try:
            relative = file_path.relative_to(REPO_ROOT)
        except ValueError:
            continue

        if len(relative.parts) < 3 or relative.parts[0] != "plugins":
            continue

        current = file_path if file_path.is_dir() else file_path.parent
        while current != PLUGINS_DIR and PLUGINS_DIR in current.parents:
            if (current / ".codex-plugin" / "plugin.json").exists():
                changed_dirs.add(current)
                break
            current = current.parent

    return sorted(changed_dirs)


def get_new_readme_entries(base_ref: str) -> list[dict[str, str]]:
    """Find new plugin entries added to README.md in this PR.

    Returns list of dicts with keys: display_name, url, owner, repo, description.
    """
    # Get the diff of README.md
    diff = git("diff", base_ref, "--", "README.md")
    if not diff:
        return []

    # Get the base version of README to detect only truly new URLs
    base_readme = git("show", f"{base_ref}:README.md")
    base_urls = set()
    if base_readme:
        base_urls = {m.group(2) for m in README_ENTRY_RE.finditer(base_readme)}

    # Extract added lines matching the plugin entry pattern
    new_entries: list[dict[str, str]] = []
    seen_urls: set[str] = set()

    for line in diff.splitlines():
        if not line.startswith("+") or line.startswith("+++"):
            continue
        content = line[1:]  # strip the leading +
        match = README_ENTRY_RE.match(content.strip())
        if not match:
            continue
        display_name, url, owner, repo = match.group(1), match.group(2), match.group(3), match.group(4)
        if url in seen_urls or url in base_urls:
            continue
        seen_urls.add(url)
        new_entries.append({
            "display_name": display_name,
            "url": url,
            "owner": owner,
            "repo": repo,
            "description": match.group(5),
        })

    return new_entries


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    base_ref = "--base-ref"
    base_arg = None
    for i, arg in enumerate(sys.argv):
        if arg == base_ref and i + 1 < len(sys.argv):
            base_arg = sys.argv[i + 1]

    if not base_arg:
        if os.environ.get("GITHUB_BASE_REF"):
            base_arg = f"origin/{os.environ['GITHUB_BASE_REF']}"
        else:
            base_arg = "origin/main"

    rev_parse = git("rev-parse", "--verify", base_arg)
    if not rev_parse:
        print(f"WARNING: Base ref '{base_arg}' not found, skipping validation")
        print("  (This is normal for the first commit on a new branch without CI)")
        sys.exit(0)

    has_failures = False
    total_errors = 0
    total_warnings = 0

    # --- Path 1: Validate committed bundles ---
    changed_dirs = get_changed_plugin_dirs(base_arg)

    if changed_dirs:
        print(f"Validating {len(changed_dirs)} changed plugin bundle(s)...\n")
        for plugin_dir in changed_dirs:
            rel = plugin_dir.relative_to(REPO_ROOT)
            errors, warnings = validate_local_bundle(plugin_dir)

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
    else:
        print("No plugin bundle directories changed.")

    # --- Path 2: Validate new README entries against source repos ---
    new_entries = get_new_readme_entries(base_arg)

    if new_entries:
        print(f"\nValidating {len(new_entries)} new README entry(ies) against source repos...\n")
        for entry in new_entries:
            owner, repo = entry["owner"], entry["repo"]
            label = f"{entry['display_name']} ({owner}/{repo})"

            # Check if a local bundle already exists (generator may have run)
            local_dir = PLUGINS_DIR / owner / repo
            if local_dir.exists() and (local_dir / ".codex-plugin" / "plugin.json").exists():
                print(f"  SKIP: {label} (local bundle exists, validated above)")
                continue

            print(f"  Fetching {owner}/{repo}...")
            errors, warnings = validate_remote_repo(owner, repo)

            if not errors:
                print(f"  PASS: {label}")
            else:
                has_failures = True
                total_errors += len(errors)
                print(f"  FAIL: {label} ({len(errors)} error(s))")
                for err in errors:
                    print(f"    x {err}")

            if warnings:
                total_warnings += len(warnings)
                for warn in warnings:
                    print(f"    ! {warn}")
            print()

    if not changed_dirs and not new_entries:
        print("No plugin directories or README entries changed. Nothing to validate.")
        sys.exit(0)

    if has_failures:
        print(f"\nValidation failed: {total_errors} error(s), {total_warnings} warning(s)")
        sys.exit(1)
    elif total_warnings:
        print(f"\nValidation passed with warnings: {total_warnings} warning(s)")
        sys.exit(0)
    else:
        print(f"\nAll checks passed.")
        sys.exit(0)


if __name__ == "__main__":
    main()
