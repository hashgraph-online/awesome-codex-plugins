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

import html
import io
import json
import os
import re
import subprocess
import sys
import zipfile
from pathlib import Path, PurePosixPath
from urllib.parse import quote, unquote, urlsplit, urlunsplit
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
    r"([^/]+)/([^/?#)]+)(?:/tree/([^?#)]+?))?/?(?:[?#][^)]*)?)\)\s*[-\u2013]\s*(.+)",
    re.MULTILINE,
)


def normalize_github_repo_url(url: str) -> str:
    """Normalize GitHub URLs so trailing-slash edits are not new listings."""

    parsed = urlsplit(url)
    path_parts = parsed.path.rstrip("/").split("/")
    if len(path_parts) >= 3 and path_parts[0] == "":
        path_parts[1] = path_parts[1].lower()
        repo = path_parts[2]
        if repo.lower().endswith(".git"):
            repo = repo[:-4]
        path_parts[2] = repo.lower()
    path = "/".join(path_parts)
    return urlunsplit(
        # GitHub view/query fragments never identify another source plugin.
        (parsed.scheme.lower(), parsed.netloc.lower(), path, "", "")
    )


def community_plugin_keys(readme: str) -> set[tuple[str, str]]:
    """Return (repository URL, entry name) keys for Community Plugins."""
    keys: set[tuple[str, str]] = set()
    in_community_plugins = False

    for line in readme.splitlines():
        heading = re.match(r"^(#{1,6})\s+(.+?)\s*#*\s*$", line)
        if heading:
            heading_level = len(heading.group(1))
            if heading_level <= 2:
                in_community_plugins = (
                    heading_level == 2
                    and heading.group(2).strip().casefold() == "community plugins"
                )
            continue
        if in_community_plugins:
            match = README_ENTRY_RE.match(line.strip())
            if match:
                keys.add((
                    normalize_github_repo_url(match.group(2)),
                    " ".join(match.group(1).split()).casefold(),
                ))

    return keys


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


def fetch_repo_archive(owner: str, repo: str, source_ref: str | None = None) -> zipfile.ZipFile:
    """Download the default-branch or explicitly linked branch archive."""
    archive_ref = f"refs/heads/{quote(source_ref, safe='/')}" if source_ref else "HEAD"
    url = f"https://github.com/{owner}/{repo}/archive/{archive_ref}.zip"
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
        return zipfile.ZipFile(io.BytesIO(response.read()))


def find_plugin_root(
    archive: zipfile.ZipFile, display_name: str | None = None,
    require_named_match: bool = False,
) -> PurePosixPath | None:
    """Select a specific nested manifest when a README entry names one bundle."""
    names = sorted(
        (
            n for n in archive.namelist()
            if n.endswith("/.codex-plugin/plugin.json")
            and not PurePosixPath(n).is_absolute()
            and ".." not in PurePosixPath(n).parts
            and "\\" not in n
        ),
        key=len,
    )
    if not names:
        return None
    if len(names) == 1 and not require_named_match:
        return PurePosixPath(names[0]).parent.parent
    if not display_name:
        # Preserve legacy behavior for callers without a README display name.
        return PurePosixPath(names[0]).parent.parent

    expected = re.sub(r"[\W_]+", "", display_name.casefold())
    if not expected:
        return None
    matches: list[PurePosixPath] = []
    for name in names:
        root = PurePosixPath(name).parent.parent
        try:
            manifest = json.loads(archive.read(name).decode("utf-8"))
        except (ValueError, UnicodeError, KeyError, zipfile.BadZipFile, EOFError):
            # A corrupt or truncated *different* member must not crash
            # selection of the independently named plugin.
            continue
        if not isinstance(manifest, dict):
            continue
        interface = manifest.get("interface")
        display = interface.get("displayName") if isinstance(interface, dict) else None
        for candidate in (manifest.get("name"), display, root.name):
            if re.sub(r"[\W_]+", "", str(candidate or "").casefold()) == expected:
                matches.append(root)
                break
    # Do not silently validate the first unrelated bundle on a mismatched name.
    return matches[0] if len(matches) == 1 else None


_UNREADABLE_MANIFEST = object()


def load_manifest_from_archive(
    archive: zipfile.ZipFile, plugin_root: PurePosixPath
) -> object:
    """Return decoded JSON, or a distinct sentinel for missing/invalid JSON."""
    manifest_name = plugin_root.joinpath(".codex-plugin", "plugin.json").as_posix()
    try:
        return json.loads(archive.read(manifest_name).decode("utf-8"))
    except (KeyError, UnicodeDecodeError, json.JSONDecodeError, zipfile.BadZipFile, EOFError):
        return _UNREADABLE_MANIFEST


# ---------------------------------------------------------------------------
# Validation logic (shared between local and remote)
# ---------------------------------------------------------------------------


def validate_manifest_fields(manifest: object) -> list[str]:
    """Validate manifest fields, including an invalid JSON root shape."""
    errors: list[str] = []
    if not isinstance(manifest, dict):
        return ["plugin.json must contain a JSON object"]

    for field in REQUIRED_MANIFEST_FIELDS:
        val = manifest.get(field)
        if val is None or (isinstance(val, str) and not val.strip()):
            errors.append(f"Missing or empty required field: {field}")
        elif not isinstance(val, str):
            errors.append(f"Required field '{field}' must be a string")

    interface = manifest.get("interface")
    if not isinstance(interface, dict):
        errors.append("Missing or invalid 'interface' object in plugin.json")
        return errors

    for field in REQUIRED_INTERFACE_FIELDS:
        val = interface.get(field)
        if val is None or (isinstance(val, str) and not val.strip()):
            errors.append(f"Missing or empty interface.{field}")
        elif not isinstance(val, str):
            errors.append(f"interface.{field} must be a string")

    version = manifest.get("version", "")
    if version and not re.match(r"^\d+\.\d+\.\d+", str(version)):
        errors.append(f"Version '{version}' does not follow semver (expected MAJOR.MINOR.PATCH)")

    name = manifest.get("name", "")
    if name and re.search(r"[A-Z\s]", str(name)):
        errors.append(f"Plugin name '{name}' should be lowercase and slug-safe (no spaces or uppercase)")

    return errors




def normalize_icon_relative_path(raw_icon: str) -> str | None:
    """Keep declared icon paths inside their own plugin, on all platforms."""
    icon_rel = raw_icon[2:] if raw_icon.startswith("./") else raw_icon
    if icon_rel.startswith("/"):
        icon_rel = icon_rel[1:]  # Existing root-relative manifest convention.
    if not icon_rel or "\\" in icon_rel or ":" in icon_rel:
        return None
    relative = PurePosixPath(icon_rel)
    if relative.is_absolute() or ".." in relative.parts or not relative.parts:
        return None
    return relative.as_posix()


def validate_icon_bytes(icon_rel: str, icon_data: bytes) -> list[str]:
    """Apply the same icon checks to local files and remote source archives."""
    errors: list[str] = []
    suffix = PurePosixPath(icon_rel).suffix.lower()
    if suffix not in ICON_EXTENSIONS:
        errors.append(f"Icon has unsupported format '{suffix}'. Use SVG (preferred) or PNG.")
    if len(icon_data) > MAX_ICON_SIZE_BYTES:
        errors.append(f"Icon is {len(icon_data) / 1024:.1f}KB, exceeds 50KB limit.")
    if suffix == ".svg":
        content = icon_data.decode("utf-8", errors="replace")
        # SVG/XML character references can conceal embedded image data URIs.
        content = html.unescape(content)
        # Only flag image data URIs used as resources, not harmless prose.
        resource_uri = re.search(
            r"(?:\b(?:xlink:)?href|\bsrc)\s*=\s*['\"]\s*data:image/"
            r"|url\(\s*['\"]?\s*data:image/",
            content,
            re.IGNORECASE,
        )
        if resource_uri:
            errors.append("SVG icon contains embedded base64 raster data.")
        if "TODO" in content or "PLACEHOLDER" in content:
            errors.append("SVG icon contains TODO/PLACEHOLDER text.")
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
    # Treat directory-shaped and escaping symlink manifests as contributor
    # errors instead of reading outside the bundle or raising a traceback.
    if (
        not manifest_path.is_file()
        or not manifest_path.resolve().is_relative_to(plugin_dir.resolve())
    ):
        errors.append(f"plugin.json must be a regular file within {rel_path}")
        return errors, warnings

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        errors.append(f"plugin.json is not valid JSON: {e}")
        return errors, warnings

    errors.extend(validate_manifest_fields(manifest))
    # The manifest-field validator has already recorded these errors. Do not
    # attempt interface/icon lookup on malformed JSON object shapes.
    if not isinstance(manifest, dict) or not isinstance(manifest.get("interface"), dict):
        return errors, warnings

    # Validate icon locally
    interface = manifest.get("interface", {})
    composer_icon = str(interface.get("composerIcon", "")).strip()
    if composer_icon:
        icon_rel = normalize_icon_relative_path(composer_icon)
        if icon_rel is None:
            errors.append("composerIcon must be a safe plugin-relative path")
        else:
            icon_path = plugin_dir / icon_rel
            if not icon_path.resolve().is_relative_to(plugin_dir.resolve()):
                errors.append("composerIcon must stay within its plugin bundle")
            elif not icon_path.is_file():
                # Directory-shaped icon paths must report a contributor error,
                # not crash the validation job with IsADirectoryError.
                errors.append(f"Icon file not found or not a regular file: {icon_rel} (resolved to {icon_path.relative_to(REPO_ROOT)})")
            else:
                errors.extend(validate_icon_bytes(icon_rel, icon_path.read_bytes()))

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


def validate_remote_repo(
    owner: str, repo: str, source_ref: str | None = None,
    display_name: str | None = None,
    require_named_match: bool = False,
) -> tuple[list[str], list[str]]:
    """Fetch and validate a plugin from its source GitHub repo.

    Returns (errors, warnings).
    """
    errors: list[str] = []
    warnings: list[str] = []

    try:
        archive = fetch_repo_archive(owner, repo, source_ref)
    except Exception as e:
        return ([f"Failed to fetch source repo https://github.com/{owner}/{repo}: {e}"], [])

    plugin_root = find_plugin_root(archive, display_name, require_named_match)
    if plugin_root is None:
        detail = (
            f"a uniquely matching manifest for '{display_name}'"
            if display_name else ".codex-plugin/plugin.json"
        )
        errors.append(f"Source repo https://github.com/{owner}/{repo} does not contain {detail}")
        return errors, warnings

    manifest = load_manifest_from_archive(archive, plugin_root)
    if manifest is _UNREADABLE_MANIFEST:
        errors.append("Could not read valid plugin.json from source repo")
        return errors, warnings

    errors.extend(validate_manifest_fields(manifest))
    if not isinstance(manifest, dict) or not isinstance(manifest.get("interface"), dict):
        return errors, warnings

    # Check icon exists in the archive
    interface = manifest.get("interface", {})
    composer_icon = str(interface.get("composerIcon", "")).strip()
    if composer_icon:
        icon_rel = normalize_icon_relative_path(composer_icon)
        if icon_rel is None:
            errors.append("composerIcon must be a safe plugin-relative path")
        else:
            icon_archive_path = plugin_root.joinpath(PurePosixPath(icon_rel)).as_posix()
            try:
                # A source archive can compress an oversized image to very few
                # bytes. Reject it by ZIP metadata before expanding the member.
                icon_info = archive.getinfo(icon_archive_path)
                if icon_info.file_size > MAX_ICON_SIZE_BYTES:
                    errors.append(
                        f"Icon is {icon_info.file_size / 1024:.1f}KB, exceeds 50KB limit."
                    )
                else:
                    errors.extend(validate_icon_bytes(icon_rel, archive.read(icon_archive_path)))
            except KeyError:
                errors.append(
                    f"Icon file not found in source repo at: {icon_rel} "
                    f"(referenced by composerIcon in plugin.json)"
                )
            except (zipfile.BadZipFile, EOFError) as exc:
                # A broken ZIP member should yield an actionable contributor
                # diagnostic instead of aborting validation with a traceback.
                errors.append(f"Could not read source icon {icon_rel}: corrupt archive member ({type(exc).__name__})")

    return errors, warnings


# ---------------------------------------------------------------------------
# Changed file detection
# ---------------------------------------------------------------------------


def get_changed_plugin_dirs(base_ref: str) -> list[Path]:
    """Find plugin directories that were added or modified in this branch."""
    output = git("diff", "--merge-base", "--no-renames", "--name-only", "--diff-filter=ACMRD", base_ref, "HEAD", "--", "plugins/")
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

        # A removed manifest must still reach local validation, even when
        # the entire bundle has disappeared from the contributor branch.
        # --no-renames keeps a moved manifest visible as a deletion too.
        if relative.parts[-2:] == (".codex-plugin", "plugin.json") and not file_path.is_file():
            changed_dirs.add(file_path.parent.parent)
            continue

        current = file_path if file_path.is_dir() else file_path.parent
        while current != PLUGINS_DIR and PLUGINS_DIR in current.parents:
            if (current / ".codex-plugin" / "plugin.json").exists():
                changed_dirs.add(current)
                break
            current = current.parent

    return sorted(changed_dirs)


def get_new_readme_entries(base_ref: str) -> list[dict[str, str]]:
    """Find new Community Plugins entries added to README.md in this PR.

    Returns list of dicts with keys: display_name, url, owner, repo, description.
    """
    # Get the diff of README.md
    diff = git("diff", "--merge-base", base_ref, "HEAD", "--", "README.md")
    if not diff:
        return []

    # Only the Community Plugins section contains Codex plugin listings.
    # Other sections such as Related Projects can link to non-plugin projects.
    # Diff and duplicate detection must compare against the SAME common ancestor.
    # Reading the moving base-branch tip can hide a listing added on both branches.
    merge_base = git("merge-base", base_ref, "HEAD")
    if not merge_base:
        raise RuntimeError(f"Cannot find merge base for README validation: {base_ref}")
    base_readme = git("show", f"{merge_base}:README.md")
    if not base_readme:
        raise RuntimeError(f"Cannot read README at merge base {merge_base}")
    current_readme = README_PATH.read_text(encoding="utf-8") if README_PATH.exists() else ""
    base_keys = community_plugin_keys(base_readme)
    current_keys = community_plugin_keys(current_readme)

    # Extract added lines matching the plugin entry pattern
    new_entries: list[dict[str, str]] = []
    seen_keys: set[tuple[str, str]] = set()

    for line in diff.splitlines():
        if not line.startswith("+") or line.startswith("+++"):
            continue
        content = line[1:]  # strip the leading +
        match = README_ENTRY_RE.match(content.strip())
        if not match:
            continue
        display_name, url, owner, repo = match.group(1), match.group(2), match.group(3), match.group(4)
        source_ref = unquote(match.group(5)) if match.group(5) else None
        semantic_key = (
            normalize_github_repo_url(url),
            " ".join(display_name.split()).casefold(),
        )
        if semantic_key not in current_keys or semantic_key in seen_keys or semantic_key in base_keys:
            continue
        seen_keys.add(semantic_key)
        new_entries.append({
            "display_name": display_name,
            "url": url,
            "owner": owner,
            "repo": repo,
            "description": match.group(6),
            "source_ref": source_ref,
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
        print(f"ERROR: Base ref '{base_arg}' not found; validation cannot run")
        sys.exit(1)

    # A PR may be behind main. Comparing both tips mislabels newer base
    # changes as changes from the PR; compare only its own branch commits.
    if not git("merge-base", base_arg, "HEAD"):
        print(f"ERROR: No merge base between '{base_arg}' and HEAD")
        sys.exit(1)

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
        # A shared repository with multiple named catalog entries must not
        # pass validation by silently selecting its only unrelated manifest.
        source_counts: dict[str, int] = {}
        for source_url, _name in community_plugin_keys(README_PATH.read_text(encoding="utf-8")):
            parts = urlsplit(source_url).path.strip("/").split("/")
            if len(parts) >= 2:
                source_key = f"{parts[0].casefold()}/{parts[1].casefold()}"
                source_counts[source_key] = source_counts.get(source_key, 0) + 1
        for entry in new_entries:
            owner, repo = entry["owner"], entry["repo"]
            label = f"{entry['display_name']} ({owner}/{repo})"

            # An existing mirrored umbrella must not skip source validation
            # for a second independently named plugin in the same repository.
            source_key = f"{owner.casefold()}/{repo.casefold()}"
            local_dir = PLUGINS_DIR / owner / repo
            if (
                source_counts.get(source_key, 0) == 1
                and not entry.get("source_ref")
                and (local_dir / ".codex-plugin" / "plugin.json").is_file()
            ):
                print(f"  SKIP: {label} (single existing local bundle)")
                continue

            print(f"  Fetching {owner}/{repo}...")
            errors, warnings = validate_remote_repo(
                owner, repo, entry.get("source_ref"), entry["display_name"],
                require_named_match=source_counts.get(source_key, 0) > 1,
            )

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
