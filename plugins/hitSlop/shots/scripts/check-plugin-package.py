#!/usr/bin/env python3
"""Validate the Shots plugin package metadata without external dependencies."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT_REQUIRED = [
    ".codex-plugin/plugin.json",
    ".agents/plugins/marketplace.json",
    ".mcp.json",
    "mcp.json",
    "server.json",
    "README.md",
    "SECURITY.md",
    "LICENSE",
    ".codexignore",
]

TODO_MARKER = "[" + "TODO"
TODO_COLON = "TO" + "DO:"


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def load_json(root: Path, relative: str) -> dict:
    path = root / relative
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"{relative} is not valid JSON: {exc}")


def assert_relative_file(root: Path, owner: str, value: str, *, png_only: bool = False) -> None:
    if not value.startswith("./"):
        fail(f"{owner} must use a ./-prefixed relative path: {value}")
    candidate = (root / value[2:]).resolve()
    if root.resolve() not in candidate.parents:
        fail(f"{owner} escapes the plugin root: {value}")
    if not candidate.is_file():
        fail(f"{owner} points at a missing file: {value}")
    if png_only and candidate.suffix.lower() != ".png":
        fail(f"{owner} must point at a PNG file: {value}")


def validate_plugin_manifest(root: Path) -> None:
    manifest = load_json(root, ".codex-plugin/plugin.json")
    for key in ["name", "version", "description", "repository", "license", "skills", "mcpServers"]:
        if not manifest.get(key):
            fail(f"plugin.json missing required field: {key}")
    if manifest["name"] != "shots":
        fail("plugin.json name must remain shots")
    if not re.fullmatch(r"\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?", manifest["version"]):
        fail("plugin.json version must be strict semver")
    if manifest["repository"] != "https://github.com/hitSlop/shots":
        fail("plugin.json repository must point to the public GitHub repo")
    if manifest["mcpServers"] != "./.mcp.json":
        fail("plugin.json mcpServers must point to ./.mcp.json")
    if manifest["skills"] != "./skills/":
        fail("plugin.json skills must point to ./skills/")

    author = manifest.get("author") or {}
    if not author.get("name"):
        fail("plugin.json author.name is required")

    interface = manifest.get("interface") or {}
    for key in ["displayName", "shortDescription", "longDescription", "developerName", "category", "composerIcon", "logo"]:
        if not interface.get(key):
            fail(f"plugin.json interface missing required field: {key}")
    for key in ["websiteURL", "privacyPolicyURL", "termsOfServiceURL"]:
        value = interface.get(key)
        if value and not value.startswith("https://"):
            fail(f"plugin.json interface.{key} must be an https URL")
    assert_relative_file(root, "interface.composerIcon", interface["composerIcon"])
    assert_relative_file(root, "interface.logo", interface["logo"])
    for screenshot in interface.get("screenshots", []):
        assert_relative_file(root, "interface.screenshots[]", screenshot, png_only=True)


def validate_mcp_configs(root: Path) -> None:
    for relative in [".mcp.json", "mcp.json"]:
        config = load_json(root, relative)
        server = (config.get("mcpServers") or {}).get("shots")
        if not server:
            fail(f"{relative} must define mcpServers.shots")
        if server.get("type") != "http":
            fail(f"{relative} mcpServers.shots.type must be http")
        if server.get("url") != "https://shots.run/api/mcp":
            fail(f"{relative} mcpServers.shots.url must be https://shots.run/api/mcp")


def validate_marketplace(root: Path) -> None:
    marketplace = load_json(root, ".agents/plugins/marketplace.json")
    if marketplace.get("name") != "shots":
        fail("marketplace name must be shots")
    plugins = marketplace.get("plugins")
    if not isinstance(plugins, list) or len(plugins) != 1:
        fail("marketplace must contain exactly one plugin entry")
    entry = plugins[0]
    if entry.get("name") != "shots":
        fail("marketplace plugin entry must be shots")
    source = entry.get("source") or {}
    if source.get("source") != "local" or source.get("path") != "./":
        fail("marketplace source must point to the local plugin root")
    policy = entry.get("policy") or {}
    if policy.get("installation") != "AVAILABLE" or policy.get("authentication") != "ON_INSTALL":
        fail("marketplace policy must be AVAILABLE/ON_INSTALL")
    if entry.get("category") != "Design":
        fail("marketplace category must be Design")


def validate_server_json(root: Path) -> None:
    server = load_json(root, "server.json")
    if server.get("$schema") != "https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json":
        fail("server.json must use the 2025-12-11 MCP Registry schema")
    if server.get("name") != "run.shots/shots":
        fail("server.json name must be run.shots/shots")
    if len(server.get("description", "")) > 100:
        fail("server.json description must be 100 characters or less")
    remotes = server.get("remotes")
    if not isinstance(remotes, list) or remotes != [{"type": "streamable-http", "url": "https://shots.run/api/mcp"}]:
        fail("server.json must expose the hosted streamable-http MCP endpoint")
    repository = server.get("repository") or {}
    if repository.get("url") != "https://github.com/hitSlop/shots" or repository.get("source") != "github":
        fail("server.json repository metadata is incorrect")


def validate_skill_references(root: Path) -> None:
    skill = root / "skills/shots/SKILL.md"
    if not skill.is_file():
        fail("skills/shots/SKILL.md is missing")
    text = skill.read_text(encoding="utf-8")
    if TODO_MARKER in text or TODO_COLON in text:
        fail("SKILL.md contains TODO placeholders")
    for reference in [
        "create.md",
        "prompting.md",
        "inspiration.md",
        "strategy.md",
        "icons.md",
        "revise.md",
        "translate.md",
        "scrape.md",
    ]:
        if not (root / "skills/shots/reference" / reference).is_file():
            fail(f"missing skill reference: {reference}")
    if not (root / "scripts/upload-asset.mjs").is_file():
        fail("missing upload helper script")


def validate_repo_hygiene(root: Path) -> None:
    for relative in ROOT_REQUIRED:
        if not (root / relative).exists():
            fail(f"missing required file: {relative}")
    ds_store_files = [path for path in root.rglob(".DS_Store") if ".git" not in path.parts]
    if ds_store_files:
        names = ", ".join(str(path.relative_to(root)) for path in ds_store_files)
        fail(f"remove .DS_Store files before publishing: {names}")
    for path in root.rglob("*"):
        if ".git" in path.parts or not path.is_file():
            continue
        if path.suffix.lower() in {".png", ".jpg", ".jpeg"}:
            continue
        data = path.read_text(encoding="utf-8", errors="ignore")
        if TODO_MARKER + ":" in data:
            fail(f"placeholder found in {path.relative_to(root)}")


def main() -> None:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    validate_repo_hygiene(root)
    validate_plugin_manifest(root)
    validate_mcp_configs(root)
    validate_marketplace(root)
    validate_server_json(root)
    validate_skill_references(root)
    print("Shots plugin package checks passed.")


if __name__ == "__main__":
    main()
