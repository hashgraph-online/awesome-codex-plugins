#!/usr/bin/env python3
"""Regenerate compatibility metadata and the curated Codex marketplace from README.

Usage:
    python3 scripts/generate_plugins_json.py

This script keeps three artifacts aligned:

- plugins.json compatibility output for legacy tooling
- .agents/plugins/marketplace.json for Codex repo marketplace installs
- mirrored installable plugin bundles under plugins/<owner>/<repo>/
"""

from __future__ import annotations

import datetime
import io
import json
import re
import shutil
import sys
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath

README = Path(__file__).parent.parent / "README.md"
OUTPUT = Path(__file__).parent.parent / "plugins.json"
MARKETPLACE_OUTPUT = Path(__file__).parent.parent / ".agents" / "plugins" / "marketplace.json"
PLUGINS_ROOT = Path(__file__).parent.parent / "plugins"
REQUEST_TIMEOUT_SECONDS = 60
MAX_RETRIES = 3
USER_AGENT = "awesome-codex-plugins-generator"
RAW_DEFAULT_BRANCH_REF = "HEAD"
OPTIONAL_PLUGIN_FILES = (
    "README.md",
    "NOTICE.md",
    "SECURITY.md",
    "LICENSE",
    "LICENSE.md",
    "LICENSE.txt",
    "pyproject.toml",
    "package.json",
    "pnpm-lock.yaml",
    "package-lock.json",
    "yarn.lock",
    ".codexignore",
    ".agents/plugins/marketplace.json",
    "SKILL.md",
    ".github/dependabot.yml",
    "codex.mcp.json",
    ".mcp.json",
  )
METADATA_ONLY_MIRROR_REPOS = {
    # EOC's repo-root Codex plugin references a large skills/commands catalog.
    # Keep the directory mirror installable as marketplace metadata without
    # copying the full upstream repository or leaving broken local references.
    "mturac/everything-openai-codex",
}
EXTRA_MIRROR_PATHS = {
    # BurpSuite MCP Bridge needs its Python MCP runtime and Burp extension JARs
    # mirrored with the plugin manifest so marketplace installs are usable.
    "6jeffr3y/burpsuite-mcp-bridge": ("wsl-mcp", "burp-plugin"),
    # debt-ops's manifest points hooks at hooks/hooks.json; the hook commands
    # invoke sibling Python scripts in the same hooks/ directory at runtime.
    "bcanfield/agentic-tech-debt": ("hooks",),
    # VidSeeds.ai ships a root registry fallback skill plus Dependabot metadata
    # that HOL Guard uses when scoring the mirrored marketplace bundle.
    "CarrotGamesStudios/vidseeds-mcp": ("SKILL.md", ".github/dependabot.yml"),
    # Staff Engineer Mode exposes one router skill and loads routed specialist
    # files from a top-level specialists/ directory at runtime.
    "sirmarkz/staff-engineer-mode": ("specialists",),
}


def normalize_relative_path(value: str) -> str:
    # Normalize backslashes to forward slashes
    value = value.replace("\\", "/")
    # Strip only a leading '/' or './' prefix, preserving dot-prefixed filenames like ".mcp.json"
    if value.startswith('/'):
        value = value[1:]
    if value.startswith('./'):
        value = value[2:]
    return value


def parse_plugins(readme_path: Path) -> list[dict[str, str]]:
    lines = readme_path.read_text(encoding="utf-8").splitlines()

    start = None
    end = None
    for index, line in enumerate(lines):
        if line.strip() == "## Community Plugins":
            start = index + 1
        if start is not None and line.strip().startswith("## ") and line.strip() != "## Community Plugins":
            end = index
            break

    if start is None:
        raise ValueError("Could not find Community Plugins section")
    if end is None:
        end = len(lines)

    section = lines[start:end]
    plugins: list[dict[str, str]] = []
    current_category = "Uncategorized"
    seen: set[str] = set()

    for line in section:
        category_match = re.match(r"^### (.+)", line.strip())
        if category_match:
            current_category = category_match.group(1)
            continue

        plugin_match = re.match(
            r"^- \[([^\]]+)\]\((https://github\.com/([^/]+)/([^)#]+?))(?:#readme)?\)\s*[-–]\s*(.+)",
            line.strip(),
        )
        if not plugin_match:
            continue

        owner, repo = plugin_match.group(3), plugin_match.group(4)
        repo = repo.removesuffix(".git")
        key = f"{owner}/{repo}/{plugin_match.group(1)}"
        if key in seen:
            continue
        seen.add(key)
        plugins.append(
            {
                "name": plugin_match.group(1),
                "url": plugin_match.group(2),
                "owner": owner,
                "repo": repo,
                "description": plugin_match.group(5).strip(),
                "category": current_category,
                "source": "awesome-codex-plugins",
                "install_url": f"https://raw.githubusercontent.com/{owner}/{repo}/{RAW_DEFAULT_BRANCH_REF}/.codex-plugin/plugin.json",
            }
        )

    repo_counts: dict[str, int] = {}
    for plugin in plugins:
        owner_repo = f"{plugin['owner']}/{plugin['repo']}"
        repo_counts[owner_repo] = repo_counts.get(owner_repo, 0) + 1

    for plugin in plugins:
        owner_repo = f"{plugin['owner']}/{plugin['repo']}"
        if repo_counts[owner_repo] > 1:
            plugin["_mirror_subpath"] = "true"

    return plugins


def fetch_repo_archive(owner: str, repo: str) -> zipfile.ZipFile:
    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            request = urllib.request.Request(
                f"https://github.com/{owner}/{repo}/archive/HEAD.zip",
                headers={"User-Agent": USER_AGENT},
            )
            with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
                return zipfile.ZipFile(io.BytesIO(response.read()))
        except Exception as e:
            last_error = e
            if attempt < MAX_RETRIES - 1:
                import time
                time.sleep(2 ** attempt)  # exponential backoff
    raise last_error


def normalize_match_key(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value or "").lower())


def find_plugin_roots(names: set[str]) -> list[PurePosixPath]:
    return [
        PurePosixPath(name).parent.parent
        for name in sorted(names)
        if name.endswith("/.codex-plugin/plugin.json")
    ]


def resolve_plugin_root(archive: zipfile.ZipFile, names: set[str], plugin: dict[str, str]) -> PurePosixPath:
    roots = find_plugin_roots(names)
    if not roots:
        raise ValueError("Archive does not contain .codex-plugin/plugin.json")
    if len(roots) == 1:
        return roots[0]

    expected = normalize_match_key(plugin["name"])
    for root in roots:
        manifest = load_manifest(archive, root)
        interface = manifest.get("interface", {})
        candidates = [
            manifest.get("name"),
            root.name,
            plugin_root_relative_path(root).split("/")[-1],
        ]
        if isinstance(interface, dict):
            candidates.extend([interface.get("displayName"), interface.get("shortDescription")])
        if any(normalize_match_key(candidate) == expected for candidate in candidates):
            return root

    return roots[0]


def load_manifest(archive: zipfile.ZipFile, plugin_root: PurePosixPath) -> dict[str, object]:
    manifest_name = plugin_root.joinpath(".codex-plugin", "plugin.json").as_posix()
    return json.loads(archive.read(manifest_name).decode("utf-8"))


def plugin_root_relative_path(plugin_root: PurePosixPath) -> str:
    repo_relative_parts = plugin_root.parts[1:]
    return PurePosixPath(*repo_relative_parts).as_posix() if repo_relative_parts else ""


def build_raw_manifest_url(plugin: dict[str, str], plugin_root_relative: str) -> str:
    manifest_path = ".codex-plugin/plugin.json"
    if plugin_root_relative:
        manifest_path = f"{plugin_root_relative}/{manifest_path}"
    return (
        f"https://raw.githubusercontent.com/{plugin['owner']}/{plugin['repo']}/"
        f"{RAW_DEFAULT_BRANCH_REF}/{manifest_path}"
    )


def add_recursive_selection(
    selected: set[str],
    all_names: set[str],
    plugin_root: PurePosixPath,
    relative_path: str,
) -> None:
    normalized = normalize_relative_path(relative_path)
    if not normalized:
        return
    archive_prefix = plugin_root.joinpath(PurePosixPath(normalized)).as_posix()
    if archive_prefix in all_names:
        selected.add(normalized)
    prefix_with_slash = f"{archive_prefix}/"
    for name in all_names:
        if name.startswith(prefix_with_slash):
            relative_name = PurePosixPath(name).relative_to(plugin_root).as_posix()
            selected.add(relative_name)


def collect_selected_paths(
    manifest: dict[str, object],
    all_names: set[str],
    plugin_root: PurePosixPath,
    plugin: dict[str, str],
) -> set[str]:
    selected = {".codex-plugin/plugin.json"}

    for optional_name in OPTIONAL_PLUGIN_FILES:
        candidate = plugin_root.joinpath(optional_name).as_posix()
        if candidate in all_names:
            selected.add(optional_name)

    for key in ("skills", "scripts", "mcpServers", "apps", "app", "appConfig", "hooks"):
        value = manifest.get(key)
        if isinstance(value, str):
            add_recursive_selection(selected, all_names, plugin_root, value)

    interface = manifest.get("interface")
    if isinstance(interface, dict):
        for key in ("composerIcon", "logo"):
            value = interface.get(key)
            if isinstance(value, str):
                add_recursive_selection(selected, all_names, plugin_root, value)
        screenshots = interface.get("screenshots")
        if isinstance(screenshots, list):
            for screenshot in screenshots:
                if isinstance(screenshot, str):
                    add_recursive_selection(selected, all_names, plugin_root, screenshot)

    for extra_path in EXTRA_MIRROR_PATHS.get(f"{plugin['owner']}/{plugin['repo']}", ()):
        add_recursive_selection(selected, all_names, plugin_root, extra_path)

    return selected


def is_metadata_only_mirror(plugin: dict[str, str]) -> bool:
    return f"{plugin['owner']}/{plugin['repo']}" in METADATA_ONLY_MIRROR_REPOS


def collect_metadata_only_paths(
    manifest: dict[str, object],
    all_names: set[str],
    plugin_root: PurePosixPath,
) -> set[str]:
    selected = {".codex-plugin/plugin.json"}

    for optional_name in ("LICENSE", "LICENSE.md", "LICENSE.txt", ".codexignore"):
        candidate = plugin_root.joinpath(optional_name).as_posix()
        if candidate in all_names:
            selected.add(optional_name)

    interface = manifest.get("interface")
    if isinstance(interface, dict):
        for key in ("composerIcon", "logo"):
            value = interface.get(key)
            if isinstance(value, str):
                add_recursive_selection(selected, all_names, plugin_root, value)

    return selected


def sanitize_metadata_only_manifest(manifest: dict[str, object], plugin: dict[str, str]) -> dict[str, object]:
    sanitized = json.loads(json.dumps(manifest))

    for key in ("skills", "commands", "hooks", "apps", "app", "appConfig"):
        sanitized.pop(key, None)

    if f"{plugin['owner']}/{plugin['repo']}" == "mturac/everything-openai-codex":
        repo_url = "https://github.com/mturac/everything-openai-codex"
        sanitized["description"] = (
            "Open-source Codex workflow collection with install profiles, repo "
            "conventions, validation checks, and documentation."
        )
        sanitized["author"] = {
            "name": "Mehmet Turac",
            "url": "https://github.com/mturac",
        }
        sanitized["homepage"] = repo_url

        interface = sanitized.setdefault("interface", {})
        if isinstance(interface, dict):
            interface["shortDescription"] = (
                "Codex workflow collection with install profiles, repo conventions, "
                "validation checks, and documentation."
            )
            interface["longDescription"] = (
                "Everything OpenAI Codex (EOC) is a community-maintained Codex "
                "workflow collection. The upstream repository contains the full "
                "documentation, install profiles, skills, commands, and validation material."
            )
            interface["developerName"] = "Mehmet Turac"
            interface["category"] = "Coding"
            interface["websiteURL"] = repo_url

    return sanitized


def mirror_plugin_bundle(plugin: dict[str, str]) -> tuple[dict[str, object], str, str]:
    owner_repo = f"{plugin['owner']}/{plugin['repo']}"
    try:
        archive = fetch_repo_archive(plugin["owner"], plugin["repo"])
    except Exception as e:
        raise ValueError(f"Failed to fetch {owner_repo}: {e}") from e
    names = {name for name in archive.namelist() if not name.endswith("/")}
    try:
        plugin_root = resolve_plugin_root(archive, names, plugin)
    except ValueError:
        raise ValueError(f"Archive for {owner_repo} does not contain a matching .codex-plugin/plugin.json") from None
    manifest = load_manifest(archive, plugin_root)
    metadata_only = is_metadata_only_mirror(plugin)
    selected_paths = (
        collect_metadata_only_paths(manifest, names, plugin_root)
        if metadata_only
        else collect_selected_paths(manifest, names, plugin_root, plugin)
    )
    mirrored_manifest = sanitize_metadata_only_manifest(manifest, plugin) if metadata_only else manifest

    plugin_root_relative = plugin_root_relative_path(plugin_root)
    use_subpath = plugin.get("_mirror_subpath") == "true"
    destination_root = PLUGINS_ROOT / plugin["owner"] / plugin["repo"]
    if use_subpath and plugin_root_relative:
        destination_root = destination_root / PurePosixPath(plugin_root_relative)
    # Clear destination to avoid stale files from previous runs (Thread 2 fix)
    if destination_root.exists():
        shutil.rmtree(destination_root)
    destination_root.mkdir(parents=True, exist_ok=True)

    for relative_path in sorted(selected_paths):
        archive_name = plugin_root.joinpath(PurePosixPath(relative_path)).as_posix()
        destination_path = destination_root / PurePosixPath(relative_path)
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        if relative_path == ".codex-plugin/plugin.json":
            destination_path.write_text(
                json.dumps(mirrored_manifest, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
        else:
            destination_path.write_bytes(archive.read(archive_name))

    marketplace_path = f"./plugins/{plugin['owner']}/{plugin['repo']}"
    if use_subpath and plugin_root_relative:
        marketplace_path = f"{marketplace_path}/{plugin_root_relative}"

    return mirrored_manifest, marketplace_path, plugin_root_relative


def build_marketplace_entry(
    plugin: dict[str, str],
    manifest: dict[str, object],
    marketplace_path: str,
    icon_path: str | None = None,
) -> dict[str, object]:
    manifest_name = str(manifest.get("name") or "").strip() or plugin["repo"]
    interface = manifest.get("interface", {})
    display_name = plugin["name"]  # from README, human-readable
    description = plugin.get("description", "").strip()
    if not description:
        description = str(interface.get("shortDescription") or interface.get("longDescription") or "").strip()

    entry: dict[str, object] = {
        "name": manifest_name,
        "displayName": display_name,
        "source": {
            "source": "local",
            "path": marketplace_path,
        },
        "policy": {
            "installation": "AVAILABLE",
            "authentication": "ON_INSTALL",
        },
        "category": plugin["category"],
    }
    if description:
        entry["description"] = description
    if icon_path:
        entry["icon"] = icon_path

    return entry


def write_json(path: Path, data: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    plugins = parse_plugins(README)
    mirrored_entries: list[dict[str, object]] = []
    skipped: list[str] = []
    for plugin in plugins:
        owner_repo = f"{plugin['owner']}/{plugin['repo']}"
        try:
            manifest, marketplace_path, plugin_root_relative = mirror_plugin_bundle(plugin)
        except Exception as e:
            print(f"WARNING: Skipping {owner_repo} — {e}", file=sys.stderr)
            skipped.append(owner_repo)
            continue
        plugin["install_url"] = build_raw_manifest_url(plugin, plugin_root_relative)

        # Determine icon path if available and actually mirrored
        icon_path: str | None = None
        interface = manifest.get("interface", {})
        if isinstance(interface, dict):
            composer_icon = interface.get("composerIcon") or interface.get("logo")
            if isinstance(composer_icon, str) and composer_icon.strip():
                # Thread 1 fix: reject placeholder values like "[TODO: ./assets/icon.png]"
                stripped = composer_icon.strip()
                if not (stripped.startswith('[') and ('TODO' in stripped or 'PLACEHOLDER' in stripped)):
                    # Properly strip leading "./" or "/" only, preserving dot-prefixed filenames like ".mcp.json"
                    rel = composer_icon
                    if rel.startswith('./'):
                        rel = rel[2:]
                    elif rel.startswith('/'):
                        rel = rel[1:]
                    candidate = f"{marketplace_path}/{rel}"
                    # Verify the file exists in the mirrored plugin directory
                    local_root = PLUGINS_ROOT / plugin["owner"] / plugin["repo"]
                    if plugin.get("_mirror_subpath") == "true" and plugin_root_relative:
                        local_root = local_root / PurePosixPath(plugin_root_relative)
                    abs_path = local_root / rel
                    if abs_path.exists():
                        icon_path = candidate

        mirrored_entries.append(build_marketplace_entry(plugin, manifest, marketplace_path, icon_path))

    # Filter out skipped plugins from public plugin list so counts stay accurate
    ok_plugins = [p for p in plugins if f"{p['owner']}/{p['repo']}" not in skipped]

    marketplace = {
        "name": "awesome-codex-plugins",
        "interface": {
            "displayName": "Awesome Codex Plugins",
        },
        "plugins": mirrored_entries,
    }
    public_plugins = [
        {key: value for key, value in plugin.items() if not key.startswith("_")}
        for plugin in ok_plugins
    ]
    plugins_json = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "name": "awesome-codex-plugins",
        "version": "1.0.0",
        "last_updated": datetime.date.today().isoformat(),
        "total": len(ok_plugins),
        "categories": sorted({plugin["category"] for plugin in ok_plugins}),
        "plugins": public_plugins,
    }

    write_json(MARKETPLACE_OUTPUT, marketplace)
    write_json(OUTPUT, plugins_json)
    print(f"Wrote {len(ok_plugins)} plugins to {OUTPUT}")
    if skipped:
        print(f"Skipped {len(skipped)} broken upstream(s): {', '.join(skipped)}", file=sys.stderr)
    print(f"Wrote curated marketplace to {MARKETPLACE_OUTPUT}")


if __name__ == "__main__":
    main()
