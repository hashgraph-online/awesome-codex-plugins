"""Read portable Agent Plugins and legacy Codex package manifests."""

import json
import stat
from pathlib import PurePosixPath

PORTABLE_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
LEGACY_MANIFEST = ".codex-plugin/plugin.json"
CANONICAL_FIELDS = {
    "$schema", "name", "version", "description", "author", "homepage",
    "repository", "license", "keywords", "extensions", "skills", "mcpServers",
}
OPENAI_FIELDS = {
    "interface", "hooks", "apps", "app", "appConfig", "onboardingSkill",
    "review", "publication", "requires_local_executor",
}


def is_portable_manifest(value):
    return isinstance(value, dict) and value.get("$schema") == PORTABLE_SCHEMA


def compatibility_manifest(effective):
    """Keep directory metadata in its Codex overlay namespace."""
    result = dict(effective)
    extra = {key: result.pop(key) for key in ("onboardingSkill", "review", "publication") if key in result}
    if extra:
        result["extensions"] = {"com.openai": extra}
    return result


def load_package_manifest(read_file, exists):
    """Return effective Codex metadata and whether the root is portable.

    Root identity/components are canonical. An inline OpenAI object replaces
    the compatibility overlay, including when the object is empty.
    """
    root = None
    if exists("plugin.json"):
        contents = read_file("plugin.json")
        try:
            root = json.loads(contents)
        except (ValueError, UnicodeDecodeError, RecursionError):
            # An unrecognized root file does not replace a valid legacy package.
            pass
    if not is_portable_manifest(root):
        return json.loads(read_file(LEGACY_MANIFEST)), False

    extensions = root.get("extensions", {})
    if not isinstance(extensions, dict):
        raise ValueError("Portable extensions must contain a JSON object")
    if "com.openai" in extensions:
        overlay = extensions["com.openai"]
    else:
        overlay = json.loads(read_file(LEGACY_MANIFEST)) if exists(LEGACY_MANIFEST) else {}
    if not isinstance(overlay, dict):
        raise ValueError("OpenAI extension must contain a JSON object")
    if "com.openai" not in extensions:
        legacy_extensions = overlay.get("extensions", {})
        if not isinstance(legacy_extensions, dict):
            raise ValueError("Legacy extensions must contain a JSON object")
        legacy_openai = legacy_extensions.get("com.openai", {})
        if not isinstance(legacy_openai, dict):
            raise ValueError("Legacy OpenAI extension must contain a JSON object")
        overlay = dict(overlay)
        for key in ("onboardingSkill", "review", "publication"):
            if key in legacy_openai:
                overlay[key] = legacy_openai[key]

    excluded = {"$schema", "extensions", "skills", "mcpServers"} | OPENAI_FIELDS
    effective = {key: value for key, value in root.items() if key not in excluded}
    effective.update({key: value for key, value in overlay.items() if key not in CANONICAL_FIELDS})
    if exists("skills/"):
        effective["skills"] = "./skills/"
    if exists("mcp.json"):
        effective["mcpServers"] = "./mcp.json"
    if "hooks" not in effective and exists("hooks/hooks.json"):
        effective["hooks"] = "./hooks/hooks.json"
    return effective, True


def archive_package_manifest(archive, root):
    names = set(archive.namelist())

    def exists(relative):
        path = root.joinpath(relative).as_posix()
        return path in names or any(name.startswith(path.rstrip("/") + "/") for name in names)

    def read_file(relative):
        path = root.joinpath(relative).as_posix()
        info = archive.getinfo(path)
        if info.is_dir() or stat.S_ISLNK(info.external_attr >> 16):
            raise ValueError("plugin.json must be a regular file within its bundle")
        return archive.read(path)

    return load_package_manifest(read_file, exists)


def package_roots(archive):
    roots = set()
    for name in archive.namelist():
        path = PurePosixPath(name)
        if path.is_absolute() or ".." in path.parts:
            continue
        if name.endswith("/" + LEGACY_MANIFEST):
            roots.add(path.parent.parent)
        elif path.name == "plugin.json":
            try:
                info = archive.getinfo(name)
                if not info.is_dir() and not stat.S_ISLNK(info.external_attr >> 16) and is_portable_manifest(json.loads(archive.read(name))):
                    roots.add(path.parent)
            except (ValueError, UnicodeDecodeError, RecursionError):
                continue
    return sorted(roots, key=lambda root: (len(root.as_posix()), root.as_posix()))
