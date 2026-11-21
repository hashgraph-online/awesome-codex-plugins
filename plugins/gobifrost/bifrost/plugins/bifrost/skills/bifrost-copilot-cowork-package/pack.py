#!/usr/bin/env python3
"""Package a Bifrost agent as a Microsoft 365 Copilot Cowork plugin .zip.

Reads agent metadata via `bifrost agents get`, emits a devPreview
manifest.json + skills/<name>/SKILL.md + placeholder icons, zips it.

Usage:
    pack.py <agent-name-or-id> [--out DIR] [--auth TYPE] [--ref-id ID]
            [--bifrost-host HOST] [--app-id GUID]
"""
from __future__ import annotations

import argparse
import json
import re
import struct
import subprocess
import sys
import os
import shutil
import tempfile
import urllib.parse
import uuid
import zipfile
import zlib
from pathlib import Path


COWORK_NAMESPACE = uuid.UUID("6ba7b812-9dad-11d1-80b4-00c04fd430c8")

JUNK_NAMES = {".DS_Store", "Thumbs.db", "desktop.ini", ".AppleDouble", ".Spotlight-V100", ".Trashes"}


def is_junk(path: Path) -> bool:
    return path.name in JUNK_NAMES or path.name.startswith("._") or any(
        part in JUNK_NAMES for part in path.parts
    )


def kebab(s: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    s = re.sub(r"-+", "-", s)
    return s or "agent"


def reverse_dns(name: str) -> str:
    return f"com.bifrost.{kebab(name).replace('-', '')}"


def get_bifrost_host() -> str:
    """Resolve the Bifrost API host the CLI is currently pointed at."""
    env = os.environ.get("BIFROST_API_URL")
    if env:
        return urllib.parse.urlparse(env).hostname or env
    out = subprocess.run(
        ["bifrost", "auth", "list"], check=True, capture_output=True, text=True,
    ).stdout
    for line in out.splitlines():
        if "(current" in line:
            url = line.strip().split()[0]
            return urllib.parse.urlparse(url).hostname or url
    raise RuntimeError(
        "Could not determine the current Bifrost host from `bifrost auth list`. "
        "Pass --bifrost-host explicitly or set BIFROST_API_URL."
    )


def get_agent(ref: str) -> dict:
    out = subprocess.run(
        ["bifrost", "agents", "get", ref, "--json"],
        check=True, capture_output=True, text=True,
    )
    return json.loads(out.stdout)


def render_icon(src: Path, size: int, dest: Path) -> None:
    """Rasterize/resize any ImageMagick-readable file (PNG, SVG, JPG, …) to a square PNG."""
    if not src.exists():
        raise RuntimeError(f"Icon source not found: {src}")
    subprocess.run(
        [
            "convert", "-background", "none", str(src),
            "-resize", f"{size}x{size}",
            "-gravity", "center",
            "-extent", f"{size}x{size}",
            str(dest),
        ],
        check=True, capture_output=True,
    )


def solid_png(size: int, rgb: tuple[int, int, int]) -> bytes:
    """Minimal valid PNG, solid color, no deps."""
    def chunk(tag: bytes, data: bytes) -> bytes:
        crc = zlib.crc32(tag + data)
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc)

    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0)  # 8-bit RGB
    row = b"\x00" + bytes(rgb) * size
    raw = row * size
    idat = zlib.compress(raw, 9)
    return sig + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")


def load_skill_source(path: Path) -> tuple[Path, str, str, Path | None]:
    """Resolve a SKILL.md source (folder, .zip, or .skill) to (skill_dir, name, description, tmp_cleanup).

    Returns the directory containing SKILL.md (with companion files alongside),
    the `name:` from frontmatter, the `description:` from frontmatter, and an
    optional tmpdir handle for the caller to clean up.
    """
    cleanup: Path | None = None
    if path.is_file() and zipfile.is_zipfile(path):
        tmp = Path(tempfile.mkdtemp(prefix="copilot-skill-src-"))
        cleanup = tmp
        with zipfile.ZipFile(path) as z:
            z.extractall(tmp)
        # Look for a single top-level folder containing SKILL.md.
        candidates = [p.parent for p in tmp.rglob("SKILL.md")]
        if not candidates:
            raise RuntimeError(f"No SKILL.md found inside {path}")
        skill_dir = candidates[0]
    elif path.is_dir():
        if (path / "SKILL.md").exists():
            skill_dir = path
        else:
            candidates = [p.parent for p in path.rglob("SKILL.md")]
            if not candidates:
                raise RuntimeError(f"No SKILL.md found under {path}")
            skill_dir = candidates[0]
    else:
        raise RuntimeError(f"--skill-source must be a folder, .zip, or .skill: {path}")

    text = (skill_dir / "SKILL.md").read_text()
    if not text.startswith("---"):
        raise RuntimeError(f"SKILL.md missing YAML frontmatter: {skill_dir/'SKILL.md'}")
    _, fm, _ = text.split("---", 2)
    name = ""
    desc = ""
    in_desc = False
    desc_lines: list[str] = []
    for line in fm.splitlines():
        if line.startswith("name:"):
            name = line.split(":", 1)[1].strip()
            in_desc = False
        elif line.startswith("description:"):
            tail = line.split(":", 1)[1].strip()
            if tail in ("", "|", ">", "|-", ">-"):
                in_desc = True
            else:
                desc = tail
                in_desc = False
        elif in_desc:
            if line and not line.startswith(" ") and not line.startswith("\t"):
                in_desc = False
            else:
                desc_lines.append(line.strip())
    if desc_lines:
        desc = " ".join(l for l in desc_lines if l)
    if not name:
        raise RuntimeError("SKILL.md frontmatter missing `name:`")
    return skill_dir, name, desc, cleanup


def build_skill_md(agent: dict, skill_name: str) -> str:
    desc = (agent.get("description") or "").strip().replace("\n", " ")
    if len(desc) > 1000:
        desc = desc[:1000].rsplit(" ", 1)[0] + "..."
    if not desc:
        desc = f"Use when the user wants to invoke the {agent['name']} agent."
    elif not desc.lower().startswith("use when"):
        desc = f"Use when: {desc}"

    prompt = (agent.get("system_prompt") or "").strip()
    if not prompt:
        prompt = f"# {agent['name']}\n\nNo system prompt configured."

    frontmatter = (
        "---\n"
        f"name: {skill_name}\n"
        f"description: |\n"
        + "".join(f"  {line}\n" for line in desc.splitlines() or [desc])
        + "metadata:\n"
        f"  author: Bifrost\n"
        f"  agent_id: {agent['id']}\n"
        f"  version: \"1.0\"\n"
        "---\n\n"
    )
    return frontmatter + prompt + "\n"


def next_version(out_root: Path, skill_name: str) -> str:
    """Auto-bump patch version per skill_name. Persists alongside the zip."""
    state_file = out_root / f".{skill_name}.version"
    if state_file.exists():
        parts = state_file.read_text().strip().split(".")
        major, minor, patch = (int(p) for p in parts)
        patch += 1
    else:
        major, minor, patch = 1, 0, 0
    version = f"{major}.{minor}.{patch}"
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(version)
    return version


def build_manifest(agent: dict, skill_name: str, app_id: str,
                   mcp_url: str, auth_type: str, ref_id: str | None,
                   version: str,
                   display_name: str | None = None,
                   description: str | None = None) -> dict:
    name = display_name or agent["name"]
    desc_full = description or agent.get("description") or name
    short_desc = desc_full.split(".")[0][:80]
    auth_block: dict = {"type": auth_type}
    if auth_type != "None":
        auth_block["referenceId"] = ref_id or f"{kebab(name)}-auth"

    return {
        "$schema": "https://developer.microsoft.com/json-schemas/teams/vDevPreview/MicrosoftTeams.schema.json",
        "manifestVersion": "devPreview",
        "version": version,
        "id": app_id,
        "packageName": reverse_dns(name),
        "developer": {
            "name": "Bifrost",
            "websiteUrl": "https://gobifrost.com",
            "privacyUrl": "https://gobifrost.com/privacy",
            "termsOfUseUrl": "https://gobifrost.com/terms",
        },
        "name": {"short": name[:30], "full": name[:100]},
        "description": {
            "short": short_desc,
            "full": desc_full[:4000],
        },
        "icons": {"color": "color.png", "outline": "outline.png"},
        "accentColor": "#4F46E5",
        "agentSkills": [{"folder": f"./skills/{skill_name}"}],
        "agentConnectors": [{
            "id": f"{kebab(name)}-mcp",
            "displayName": f"{name} MCP",
            "description": f"Remote MCP server backing the {name} agent.",
            "toolSource": {
                "remoteMcpServer": {
                    "mcpServerUrl": mcp_url,
                    "authorization": auth_block,
                }
            },
        }],
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("ref", help="Agent name or UUID")
    p.add_argument("--out", default=".", help="Output directory")
    p.add_argument("--auth", default="OAuthPluginVault",
                   choices=["None", "OAuthPluginVault", "ApiKeyPluginVault", "DynamicClientRegistration"])
    p.add_argument("--ref-id", default=None, help="Token vault referenceId (required unless --auth None)")
    p.add_argument("--bifrost-host", default=None,
                   help="Bifrost MCP host (default: resolved from `bifrost auth list`)")
    p.add_argument("--app-id", default=None, help="Override M365 app GUID")
    p.add_argument("--icon", default=None,
                   help="Path to color icon source (PNG, SVG, JPG — anything ImageMagick reads). "
                        "Auto-resized to 192x192. Defaults to a solid-color placeholder.")
    p.add_argument("--outline-icon", default=None,
                   help="Path to outline icon source. Auto-resized to 32x32. "
                        "Defaults to a solid-color placeholder.")
    p.add_argument("--skill-source", default=None,
                   help="Path to existing skill folder, .zip, or .skill bundle. "
                        "If set, its SKILL.md + companion files are used verbatim "
                        "instead of building SKILL.md from agent.system_prompt.")
    args = p.parse_args()

    agent = get_agent(args.ref)
    app_id = args.app_id or str(uuid.uuid5(COWORK_NAMESPACE, agent["id"]))
    host = args.bifrost_host or get_bifrost_host()
    mcp_url = f"https://{host}/mcp/{agent['id']}"

    src_cleanup: Path | None = None
    src_skill_dir: Path | None = None
    src_name = src_desc = None
    if args.skill_source:
        src_skill_dir, src_name, src_desc, src_cleanup = load_skill_source(
            Path(args.skill_source).expanduser().resolve()
        )
        skill_name = src_name
    else:
        skill_name = kebab(agent["name"])

    icon_src = Path(args.icon).expanduser().resolve() if args.icon else None
    outline_src = Path(args.outline_icon).expanduser().resolve() if args.outline_icon else None
    for label, p in (("--icon", icon_src), ("--outline-icon", outline_src)):
        if p and not p.exists():
            raise RuntimeError(f"{label} not found: {p}")

    out_root = Path(args.out).resolve()
    out_root.mkdir(parents=True, exist_ok=True)
    pkg_dir = out_root / f"{skill_name}-cowork"
    # If an icon source lives inside the staging dir we're about to wipe, stash it first.
    stash_dir: Path | None = None
    for var_name in ("icon_src", "outline_src"):
        p = locals()[var_name]
        if p and pkg_dir in p.parents:
            if stash_dir is None:
                stash_dir = Path(tempfile.mkdtemp(prefix="copilot-skill-stash-"))
            new = stash_dir / p.name
            shutil.copy2(p, new)
            if var_name == "icon_src":
                icon_src = new
            else:
                outline_src = new
    if pkg_dir.exists():
        shutil.rmtree(pkg_dir)
    skills_dir = pkg_dir / "skills" / skill_name
    skills_dir.mkdir(parents=True, exist_ok=True)

    version = next_version(out_root, skill_name)
    manifest = build_manifest(
        agent, skill_name, app_id, mcp_url, args.auth, args.ref_id,
        version=version,
        display_name=agent["name"],
        description=src_desc or agent.get("description"),
    )
    (pkg_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))

    if src_skill_dir:
        for entry in src_skill_dir.rglob("*"):
            if entry.is_file() and not is_junk(entry):
                dest = skills_dir / entry.relative_to(src_skill_dir)
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(entry, dest)
    else:
        (skills_dir / "SKILL.md").write_text(build_skill_md(agent, skill_name))

    if icon_src:
        render_icon(icon_src, 192, pkg_dir / "color.png")
    else:
        (pkg_dir / "color.png").write_bytes(solid_png(192, (79, 70, 229)))
    if outline_src:
        render_icon(outline_src, 32, pkg_dir / "outline.png")
    else:
        (pkg_dir / "outline.png").write_bytes(solid_png(32, (255, 255, 255)))

    if src_cleanup:
        shutil.rmtree(src_cleanup, ignore_errors=True)
    if stash_dir:
        shutil.rmtree(stash_dir, ignore_errors=True)

    zip_path = out_root / f"{skill_name}-cowork.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(pkg_dir.rglob("*")):
            if f.is_file() and not is_junk(f):
                z.write(f, f.relative_to(pkg_dir))

    result = {
        "zip": str(zip_path),
        "package_dir": str(pkg_dir),
        "app_id": app_id,
        "version": version,
        "mcp_url": mcp_url,
        "skill_name": skill_name,
        "auth_type": args.auth,
        "ref_id": args.ref_id,
    }
    print(json.dumps(result, indent=2))

    needs_auth = args.auth != "None" and not args.ref_id
    tldr = f"""
--- Upload to Copilot Cowork (TL;DR) ---

1. Frontier preview: tenant must be enrolled in the Frontier program
   (Microsoft 365 Admin Center → Copilot → Settings → Frontier).

2. Auth setup ({args.auth}):
{'   - Register an OAuth client for the Bifrost MCP endpoint in the' if args.auth == 'OAuthPluginVault' else '   - Create the API key entry in the' if args.auth == 'ApiKeyPluginVault' else '   - No auth setup required.'}
{'     Microsoft Enterprise Token Store, then re-run this script with' if needs_auth else ''}
{f'     --ref-id <token-vault-id> (current placeholder: {kebab(agent["name"])}-auth)' if needs_auth else ''}

3. Sideload the package (verified May 2026):
   admin.microsoft.com → Manage Apps → Upload custom app → Upload
   "{zip_path.name}".
   Then deploy: Copilot → Agents → All agents → find the plugin →
   Deploy to → Entire organization or Specific users/groups → Deploy.

4. Verify in Cowork → Added Plugins → plugin should show
   "Managed by your organization". Users enable/disable per device
   via Sources & Skills.

5. Replace placeholder icons (color.png 192×192, outline.png 32×32)
   before submitting to the Microsoft 365 App Store via Partner Center.

MCP endpoint Microsoft will call:
   {mcp_url}
   (must be reachable from the public internet — Netbird-fronted hosts will NOT
    work. If the resolved host is internal-only, re-run with --bifrost-host
    pointing at a publicly-reachable Bifrost instance.)
""".rstrip()
    print(tldr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
