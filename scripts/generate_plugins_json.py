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
import unicodedata
import json
import re
import shutil
import stat
import sys
import urllib.request
import zipfile
import zlib
from pathlib import Path, PurePosixPath
from urllib.parse import quote, unquote

README = Path(__file__).parent.parent / "README.md"
OUTPUT = Path(__file__).parent.parent / "plugins.json"
MARKETPLACE_OUTPUT = Path(__file__).parent.parent / ".agents" / "plugins" / "marketplace.json"
PLUGINS_ROOT = Path(__file__).parent.parent / "plugins"
RETIRED_BUNDLE_IDENTITIES = {("samuelbushi", "uizze"), ("waynehamadi", "datacircle-plugin")}
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
    # Workflow MCP bootstrap loads the sibling control-plane runtime; its MCP
    # App also reads assets/sidebar-icon.svg and Skills reference helper scripts.
    "TohmaN233/codex-agents-workflow": ("control-plane", "scripts", "assets"),
    # debt-ops's manifest points hooks at hooks/hooks.json; the hook commands
    # invoke sibling Python scripts in the same hooks/ directory at runtime.
    "bcanfield/agentic-tech-debt": ("hooks",),
    # Codex Attachment Manager's .mcp.json starts ./scripts/launch with
    # ./src/plugin-server.ts; the MCP server, engine and panel all live in src/.
    "chipfighter/codex-attachment-manager": ("scripts", "src"),
    "chipfighter/context-attachment-manager": ("scripts", "src"),
    # Cohesivity's .mcp.json starts its local stdio server from
    # ./mcp/project-bootstrap.mjs, which no manifest field references.
    "cohesivity-org/cohesivity-plugin": ("mcp",),
    # Espresso inline manifest hooks run src/hooks/*.js, which load the
    # bundled Ponytail runtime from the top-level hooks/ directory.
    "mirkobozzetto/espresso": ("src", "hooks"),
    # Staff Engineer Mode exposes one router skill and loads routed specialist
    # files from a top-level specialists/ directory at runtime.
    "sirmarkz/staff-engineer-mode": ("specialists",),
    # ZCode Bridge's .mcp.json starts dist/bridge.mjs, which launches the worker
    # and setup hook from sibling directories; preserve the complete runtime.
    "Sandyzzx/codex-zcode-bridge": (
        "dist",
        "hooks",
        "licenses",
        "mcp.json",
        "NOTICE",
        "plugin.json",
        "worker",
    ),
}


EXTRA_MIRROR_PATHS_BY_ID = {
    repo.casefold(): paths for repo, paths in EXTRA_MIRROR_PATHS.items()
}


def normalize_relative_path(value: str) -> str:
    """Accept bundle-relative paths only, never archive traversal targets."""
    value = value.replace("\\", "/")
    # Manifest paths are untrusted source data. An absolute/parent path could
    # otherwise select a ZIP member outside this bundle and write it outside
    # the destination during mirroring. Keep dot-prefixed files intact.
    # A colon can denote a drive or alternate data stream on Windows even
    # when the same spelling looks relative to PurePosixPath on Linux.
    if value.startswith("/") or ":" in value or any(
        ord(char) < 32 or ord(char) == 127 for char in value
    ):
        return ""
    while value.startswith("./"):
        value = value[2:]
    # A manifest's "." would otherwise recursively mirror the entire source
    # root, including files never declared as installable bundle assets.
    if value in {"", "."} or ".." in PurePosixPath(value).parts:
        return ""
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
    local_plugins: list[dict[str, str]] = []
    current_category = "Uncategorized"
    seen: set[tuple[str, str, str, str]] = set()
    canonical_repos: dict[tuple[str, str], tuple[str, str]] = {}

    for line in section:
        category_match = re.match(r"^### (.+)", line.strip())
        if category_match:
            current_category = category_match.group(1)
            continue

        plugin_match = re.match(
            r"^- \[([^\]]+)\]\((https://github\.com/([^/]+)/([^/?#)]+)"
            r"(?:/tree/([^?#)]+?))?/?)(?:#readme)?\)\s*[-–]\s*(.+)",
            line.strip(),
        )
        if not plugin_match:
            local_match = re.fullmatch(
                r"- \[([^\]]+)\]\(\./plugins/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)/?\)\s*[-–]\s*(.+)",
                line.strip(),
            )
            if local_match:
                local_plugins.append({
                    "owner": local_match.group(2),
                    "repo": local_match.group(3),
                    "_local_bundle": "true",
                })
            elif line.strip().startswith("- "):
                raise ValueError(f"Unrecognized Community Plugins entry: {line.strip()}")
            continue

        owner, repo = plugin_match.group(3), plugin_match.group(4)
        repo = repo.removesuffix(".git")
        # GitHub repository identities are case-insensitive, but local mirror
        # paths are not. Reuse the first source spelling for every bundle.
        identity = (owner.casefold(), repo.casefold())
        owner, repo = canonical_repos.setdefault(identity, (owner, repo))
        source_ref = unquote(plugin_match.group(5)) if plugin_match.group(5) else None
        # Alias spelling/casing must not mirror the same upstream manifest twice.
        # Keep source_ref distinct because two branches may hold different bundles.
        display_name = plugin_match.group(1)
        canonical_name = normalize_match_key(display_name) or display_name.strip().casefold()
        key = (owner.casefold(), repo.casefold(), source_ref or "", canonical_name)
        if key in seen:
            continue
        seen.add(key)
        plugin = {
            "name": plugin_match.group(1),
            "url": plugin_match.group(2),
            "owner": owner,
            "repo": repo,
            "description": plugin_match.group(6).strip(),
            "category": current_category,
            "source": "awesome-codex-plugins",
            "install_url": build_raw_manifest_url(
                {"owner": owner, "repo": repo, "source_ref": source_ref or ""}, ""
            ),
        }
        if source_ref:
            plugin["source_ref"] = source_ref
        plugins.append(plugin)

    repo_counts: dict[str, int] = {}
    for plugin in plugins:
        owner_repo = f"{plugin['owner']}/{plugin['repo']}".casefold()
        repo_counts[owner_repo] = repo_counts.get(owner_repo, 0) + 1

    for plugin in plugins:
        owner_repo = f"{plugin['owner']}/{plugin['repo']}".casefold()
        if repo_counts[owner_repo] > 1:
            plugin["_mirror_subpath"] = "true"

    return plugins + local_plugins


def fetch_repo_archive(owner: str, repo: str, source_ref: str | None = None) -> zipfile.ZipFile:
    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            archive_ref = (
                f"refs/heads/{quote(source_ref, safe='/')}" if source_ref else "HEAD"
            )
            request = urllib.request.Request(
                f"https://github.com/{owner}/{repo}/archive/{archive_ref}.zip",
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
    return re.sub(r"[\W_]+", "", str(value or "").casefold())


def find_plugin_roots(names: set[str]) -> list[PurePosixPath]:
    return [
        PurePosixPath(name).parent.parent
        for name in sorted(names)
        if name.endswith("/.codex-plugin/plugin.json")
        and normalize_relative_path(name) == name
        and ".." not in PurePosixPath(name).parts
    ]


def resolve_plugin_root(archive: zipfile.ZipFile, names: set[str], plugin: dict[str, str]) -> PurePosixPath:
    roots = find_plugin_roots(names)
    if not roots:
        raise ValueError("Archive does not contain .codex-plugin/plugin.json")
    if len(roots) == 1 and plugin.get("_mirror_subpath") != "true":
        return roots[0]

    expected = normalize_match_key(plugin["name"])
    if not expected and plugin.get("_mirror_subpath") == "true":
        raise ValueError(f"No uniquely matching nested manifest for {plugin['name']!r}")
    matching_roots: list[PurePosixPath] = []
    for root in roots:
        try:
            manifest = load_manifest(archive, root)
        except (ValueError, UnicodeError, KeyError, zipfile.BadZipFile, EOFError, zlib.error, RecursionError):
            # A malformed or excessively deep sibling manifest must not
            # prevent selection of an independently valid named bundle.
            # The corrupt sibling still fails the unique-name gate.
            continue
        if not isinstance(manifest, dict):
            continue
        # Every separate Codex marketplace entry needs its own canonical
        # source manifest identity. Matching only a display label from a
        # nameless manifest would publish duplicate repository-name IDs.
        if plugin.get("_mirror_subpath") == "true" and not (
            isinstance(manifest.get("name"), str)
            and manifest["name"].strip()
        ):
            continue
        interface = manifest.get("interface", {})
        if plugin.get("_mirror_subpath") == "true":
            # Folder names alone do not prove a separately publishable plugin.
            # Match the source manifest's declared name or display name.
            candidates = [manifest.get("name")]
        else:
            # Retain legacy single-repository umbrella matching behavior.
            candidates = [
                manifest.get("name"),
                root.name,
                plugin_root_relative_path(root).split("/")[-1],
            ]
        if isinstance(interface, dict):
            # The short description is prose, not a unique source identity.
            candidates.append(interface.get("displayName"))
        if any(normalize_match_key(candidate) == expected for candidate in candidates):
            matching_roots.append(root)

    if len(matching_roots) == 1:
        return matching_roots[0]
    if plugin.get("_mirror_subpath") == "true":
        # Distinct README entries sharing one repo must never silently mirror
        # the first unrelated manifest (or an ambiguous duplicate name).
        raise ValueError(f"No uniquely matching nested manifest for {plugin['name']!r}")
    # Preserve legacy one-entry umbrella listings until individually converted.
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
        # Nested ZIP paths may contain spaces, URL delimiters, or Unicode.
        # Quote source bytes so the public raw install URL names the verified
        # source manifest instead of a truncated or invalid request target.
        manifest_path = f"{quote(plugin_root_relative, safe='/')}/{manifest_path}"
    source_ref = plugin.get("source_ref")
    raw_ref = quote(source_ref, safe="/") if source_ref else RAW_DEFAULT_BRANCH_REF
    return (
        f"https://raw.githubusercontent.com/{plugin['owner']}/{plugin['repo']}/"
        f"{raw_ref}/{manifest_path}"
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
            # A malicious archive could include e.g. skills/../../other.
            # Never copy such a member outside the mirrored plugin root.
            if normalize_relative_path(relative_name) == relative_name:
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

    source_id = f"{plugin['owner']}/{plugin['repo']}".casefold()
    for extra_path in EXTRA_MIRROR_PATHS_BY_ID.get(source_id, ()):
        add_recursive_selection(selected, all_names, plugin_root, extra_path)

    return selected


def is_metadata_only_mirror(plugin: dict[str, str]) -> bool:
    return f"{plugin['owner']}/{plugin['repo']}".casefold() in METADATA_ONLY_MIRROR_REPOS


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

    if f"{plugin['owner']}/{plugin['repo']}".casefold() == "mturac/everything-openai-codex":
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


def require_safe_mirror_destination(root: Path, destination: Path) -> None:
    """Refuse output traversal and symlinked ancestors before any deletion."""
    if root.is_symlink():
        raise ValueError("Generated plugins root must not be a symlink")
    try:
        parts = destination.relative_to(root).parts
    except ValueError as exc:
        raise ValueError("Mirror destination is outside generated plugins root") from exc
    current = root
    for part in parts:
        if part in {".", ".."} or ":" in part:
            raise ValueError("Mirrored bundle path contains traversal or drive syntax")
        current = current / part
        if current.is_symlink():
            raise ValueError(f"Mirrored bundle path must not follow a symlink: {current}")


def mirror_plugin_bundle(plugin: dict[str, str]) -> tuple[dict[str, object], str, str]:
    owner_repo = f"{plugin['owner']}/{plugin['repo']}"
    try:
        archive = fetch_repo_archive(
            plugin["owner"], plugin["repo"], plugin.get("source_ref")
        )
    except Exception as e:
        raise ValueError(f"Failed to fetch {owner_repo}: {e}") from e
    names = {name for name in archive.namelist() if not name.endswith("/")}
    try:
        plugin_root = resolve_plugin_root(archive, names, plugin)
    except ValueError:
        raise ValueError(f"Archive for {owner_repo} does not contain a matching .codex-plugin/plugin.json") from None
    manifest = load_manifest(archive, plugin_root)
    # A malformed source manifest must fail before the previous valid bundle
    # is deleted. Later marketplace formatting assumes an object interface.
    if not isinstance(manifest, dict) or not isinstance(
        manifest.get("interface", {}), dict
    ):
        raise ValueError("Source plugin manifest must have an object root and interface")
    metadata_only = is_metadata_only_mirror(plugin)
    selected_paths = (
        collect_metadata_only_paths(manifest, names, plugin_root)
        if metadata_only
        else collect_selected_paths(manifest, names, plugin_root, plugin)
    )
    mirrored_manifest = sanitize_metadata_only_manifest(manifest, plugin) if metadata_only else manifest

    # Duplicate entries can have order-dependent contents between ZIP readers.
    # Reject ambiguity in any selected member before replacing an installation.
    # Case-distinct ZIP paths can overwrite on Windows/macOS even if their
    # raw archive names differ. Reject before replacing a working bundle.
    folded_paths: dict[str, str] = {}
    for relative_path in sorted(selected_paths):
        folded = unicodedata.normalize("NFC", relative_path).casefold()
        previous = folded_paths.get(folded)
        if previous is not None and previous != relative_path:
            raise ValueError(
                f"Case-insensitive selected archive path collision: {previous!r} / {relative_path!r}"
            )
        folded_paths[folded] = relative_path

    selected_archive_names = {
        plugin_root.joinpath(PurePosixPath(path)).as_posix()
        for path in selected_paths
    }
    seen_selected_names: set[str] = set()
    for member in archive.infolist():
        if member.filename in selected_archive_names:
            if member.filename in seen_selected_names:
                raise ValueError(f"Duplicate selected ZIP member: {member.filename!r}")
            seen_selected_names.add(member.filename)

    # Preflight selected ZIP members before deleting a previously working mirror.
    # A corrupt source archive must not leave its old installation wiped.
    for relative_path in selected_paths:
        part = PurePosixPath(relative_path)
        if (part.is_absolute() or ".." in part.parts
            or "\\" in relative_path or ":" in relative_path):
            raise ValueError(f"Unsafe mirrored archive path: {relative_path!r}")
        archive_name = plugin_root.joinpath(part).as_posix()
        info = archive.getinfo(archive_name)
        # Git stores symlink entries as link-target text in ZIP archives.
        # Copying that text as a regular file creates a broken runnable
        # plugin; following its target could escape the selected bundle.
        if info.create_system == 3 and stat.S_ISLNK(info.external_attr >> 16):
            raise ValueError(f"Selected source file is a symlink: {relative_path!r}")
        with archive.open(archive_name) as member:
            while member.read(1024 * 1024):
                pass

    plugin_root_relative = plugin_root_relative_path(plugin_root)
    use_subpath = plugin.get("_mirror_subpath") == "true"
    destination_root = PLUGINS_ROOT / plugin["owner"] / plugin["repo"]
    if use_subpath and plugin_root_relative:
        destination_root = destination_root / PurePosixPath(plugin_root_relative)
    # Do not delete or overwrite files through a repository-controlled path
    # that resolves to another directory (including an existing symlink).
    require_safe_mirror_destination(PLUGINS_ROOT, destination_root)
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



def verified_mirrored_icon_path(
    icon_reference: str, local_root: Path, marketplace_path: str
) -> str | None:
    """Use only a regular icon file beneath the actual mirrored bundle."""
    if icon_reference.startswith("[") and (
        "TODO" in icon_reference or "PLACEHOLDER" in icon_reference
    ):
        return None
    rel = normalize_relative_path(icon_reference)
    if not rel:
        return None
    root = local_root.resolve()
    candidate = (root / rel).resolve()
    if not candidate.is_relative_to(root) or not candidate.is_file():
        return None
    return f"{marketplace_path}/{rel}"


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


def prune_unlisted_bundles(root: Path, plugins: list[dict[str, str]]) -> list[str]:
    """Remove only explicitly reviewed retirements that are absent from README.

    Omission from the parsed catalog never authorizes another retirement.
    Keep listed repositories even if this run cannot fetch them, and preflight
    the two-level tree for symlinks before deleting any approved bundle.
    """
    if not plugins:
        raise ValueError("Refusing bundle cleanup from an empty parsed README; explicit maintainer retirement is required")
    retained = {(plugin["owner"].casefold(), plugin["repo"].casefold()) for plugin in plugins}
    removed: list[str] = []
    if root.is_symlink():
        raise ValueError("Generated plugins root must not be a symlink")
    if not root.exists():
        return removed
    # Preflight the entire tree before retiring anything. A later invalid
    # directory must not leave an earlier bundle partially retired.
    retired: list[Path] = []
    for owner in sorted(root.iterdir()):
        if owner.is_symlink():
            raise ValueError(f"Generated owner directory must not be a symlink: {owner}")
        if not owner.is_dir():
            continue
        for repo in sorted(owner.iterdir()):
            if repo.is_symlink():
                raise ValueError(f"Generated repo directory must not be a symlink: {repo}")
            identity = (owner.name.casefold(), repo.name.casefold())
            if repo.is_dir() and identity in RETIRED_BUNDLE_IDENTITIES and identity not in retained:
                retired.append(repo)
    for repo in retired:
        shutil.rmtree(repo)
        removed.append(f"{repo.parent.name}/{repo.name}")
    return removed


def main() -> None:
    plugins = parse_plugins(README)
    for owner_repo in prune_unlisted_bundles(PLUGINS_ROOT, plugins):
        print(f"Removed reviewed retired bundle {owner_repo}")
    # Local README links are retention-only; never fetch them from GitHub.
    plugins = [plugin for plugin in plugins if plugin.get("_local_bundle") != "true"]
    mirrored_entries: list[dict[str, object]] = []
    # Track individual successful bundle records. One failed sibling in a
    # multi-plugin repository must not erase another successfully mirrored one.
    mirrored_plugins: list[dict[str, str]] = []
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

        # Source manifest paths must never escape the actual mirrored bundle.
        # Merely checking a constructed path's existence could publish a
        # traversal reference to an unrelated local file or directory.
        icon_path: str | None = None
        interface = manifest.get("interface", {})
        if isinstance(interface, dict):
            composer_icon = interface.get("composerIcon") or interface.get("logo")
            if isinstance(composer_icon, str) and composer_icon.strip():
                local_root = PLUGINS_ROOT / plugin["owner"] / plugin["repo"]
                if plugin.get("_mirror_subpath") == "true" and plugin_root_relative:
                    local_root = local_root / PurePosixPath(plugin_root_relative)
                icon_path = verified_mirrored_icon_path(
                    composer_icon, local_root, marketplace_path
                )

        mirrored_entries.append(build_marketplace_entry(plugin, manifest, marketplace_path, icon_path))
        mirrored_plugins.append(plugin)

    # Only individually successful records are public. A failed nested bundle
    # cannot invalidate a distinct successfully mirrored sibling from the same repo.
    ok_plugins = mirrored_plugins

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
