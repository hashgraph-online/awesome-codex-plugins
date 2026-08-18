#!/usr/bin/env python3
"""Install Skill Routing Kit into a local Codex home."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import shutil
import sys
from datetime import datetime
from pathlib import Path


BEGIN_MARKER = "<!-- BEGIN Skill Routing Kit -->"
END_MARKER = "<!-- END Skill Routing Kit -->"
PLUGIN_DIR_NAME = "skill-routing-kit"
DEFAULT_MARKETPLACE_NAME = "personal"
SKIP_DIRS = {".git", "__pycache__", ".pytest_cache"}
SKIP_SUFFIXES = {".pyc", ".pyo"}


def default_codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME", "~/.codex")).expanduser()


def default_target() -> Path:
    return Path.home() / "plugins" / PLUGIN_DIR_NAME


def default_marketplace_path() -> Path:
    return Path.home() / ".agents" / "plugins" / "marketplace.json"


def default_agents_path() -> Path:
    return default_codex_home() / "AGENTS.md"


def repo_root() -> Path:
    root = Path(__file__).resolve().parents[1]
    manifest = root / ".codex-plugin" / "plugin.json"
    if not manifest.exists():
        raise SystemExit(f"Cannot find plugin manifest at {manifest}")
    return root


def should_skip(path: Path) -> bool:
    if any(part in SKIP_DIRS for part in path.parts):
        return True
    return path.suffix in SKIP_SUFFIXES


def copy_plugin(source: Path, target: Path) -> None:
    if target.exists():
        backup_root = target.parent / ".backups"
        backup_root.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_path = backup_root / f"{target.name}-{stamp}"
        shutil.move(str(target), str(backup_path))
        print(f"Backed up existing plugin to: {backup_path}")

    target.mkdir(parents=True, exist_ok=True)

    for item in source.rglob("*"):
        relative = item.relative_to(source)
        if should_skip(relative):
            continue
        destination = target / relative
        if item.is_dir():
            destination.mkdir(parents=True, exist_ok=True)
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, destination)


def install_agents_snippet(snippet_path: Path, agents_path: Path) -> str:
    snippet = snippet_path.read_text(encoding="utf-8")
    agents_path.parent.mkdir(parents=True, exist_ok=True)

    if agents_path.exists():
        current = agents_path.read_text(encoding="utf-8")
    else:
        current = ""

    if BEGIN_MARKER in current and END_MARKER in current:
        before = current.split(BEGIN_MARKER, 1)[0].rstrip()
        after = current.split(END_MARKER, 1)[1].lstrip()
        updated = f"{before}\n\n{snippet.rstrip()}\n\n{after}".strip() + "\n"
        action = "Updated"
    else:
        separator = "\n\n" if current.strip() else ""
        updated = f"{current.rstrip()}{separator}{snippet.rstrip()}\n"
        action = "Added"

    agents_path.write_text(updated, encoding="utf-8")
    return action


def marketplace_display_name(name: str) -> str:
    return " ".join(part.capitalize() for part in name.replace("_", "-").split("-") if part)


def build_marketplace_entry() -> dict[str, object]:
    return {
        "name": PLUGIN_DIR_NAME,
        "source": {
            "source": "local",
            "path": f"./plugins/{PLUGIN_DIR_NAME}",
        },
        "policy": {
            "installation": "AVAILABLE",
            "authentication": "ON_INSTALL",
        },
        "category": "Productivity",
    }


def load_or_create_marketplace(marketplace_path: Path, marketplace_name: str) -> dict[str, object]:
    if marketplace_path.exists():
        payload = json.loads(marketplace_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise SystemExit(f"{marketplace_path} must contain a JSON object.")
        return payload

    return {
        "name": marketplace_name,
        "interface": {
            "displayName": marketplace_display_name(marketplace_name),
        },
        "plugins": [],
    }


def update_marketplace_json(marketplace_path: Path, marketplace_name: str) -> tuple[str, str]:
    marketplace_path.parent.mkdir(parents=True, exist_ok=True)
    payload = load_or_create_marketplace(marketplace_path, marketplace_name)

    existing_name = payload.get("name")
    if not isinstance(existing_name, str) or not existing_name.strip():
        raise SystemExit(f"{marketplace_path} must contain a non-empty string 'name'.")
    marketplace_name = existing_name.strip()

    interface = payload.setdefault("interface", {})
    if not isinstance(interface, dict):
        raise SystemExit(f"{marketplace_path} field 'interface' must be an object.")
    interface.setdefault("displayName", marketplace_display_name(marketplace_name))

    plugins = payload.setdefault("plugins", [])
    if not isinstance(plugins, list):
        raise SystemExit(f"{marketplace_path} field 'plugins' must be an array.")

    entry = build_marketplace_entry()
    action = "Added"
    for index, current in enumerate(plugins):
        if isinstance(current, dict) and current.get("name") == PLUGIN_DIR_NAME:
            plugins[index] = entry
            action = "Updated"
            break
    else:
        plugins.append(entry)

    marketplace_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return action, marketplace_name


def run_codex_plugin_add(marketplace_name: str) -> None:
    if shutil.which("codex") is None:
        raise SystemExit(
            "codex CLI not found. Marketplace entry was written, but automatic plugin "
            f"activation was skipped. Run later: codex plugin add {PLUGIN_DIR_NAME}@{marketplace_name}"
        )

    command = ["codex", "plugin", "add", f"{PLUGIN_DIR_NAME}@{marketplace_name}"]
    result = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.stdout.strip():
        print(result.stdout.strip())
    if result.stderr.strip():
        print(result.stderr.strip(), file=sys.stderr)
    if result.returncode != 0:
        raise SystemExit(
            f"codex plugin add failed with exit code {result.returncode}. "
            f"Run manually after fixing the issue: {' '.join(command)}"
        )


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Install Skill Routing Kit without manually creating directories."
    )
    parser.add_argument(
        "--target",
        type=Path,
        default=default_target(),
        help="Plugin source directory. Default: ~/plugins/skill-routing-kit.",
    )
    parser.add_argument(
        "--marketplace",
        type=Path,
        default=default_marketplace_path(),
        help="Codex marketplace.json path. Default: ~/.agents/plugins/marketplace.json.",
    )
    parser.add_argument(
        "--marketplace-name",
        default=DEFAULT_MARKETPLACE_NAME,
        help="Marketplace name to use when creating a new marketplace.json. Default: personal.",
    )
    parser.add_argument(
        "--skip-marketplace",
        action="store_true",
        help="Install files only; do not create or update marketplace.json.",
    )
    parser.add_argument(
        "--codex-add",
        action="store_true",
        help="After updating marketplace.json, run `codex plugin add skill-routing-kit@<marketplace>`.",
    )
    parser.add_argument(
        "--install-agents",
        action="store_true",
        help="Also install the routing guard snippet into an AGENTS.md file.",
    )
    parser.add_argument(
        "--agents",
        type=Path,
        default=default_agents_path(),
        help="AGENTS.md path used with --install-agents. Default: $CODEX_HOME/AGENTS.md or ~/.codex/AGENTS.md.",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    source = repo_root()
    target = args.target.expanduser().resolve()

    if source.resolve() == target:
        print(f"Skill Routing Kit is already at: {target}")
    else:
        try:
            target.relative_to(source)
        except ValueError:
            pass
        else:
            raise SystemExit("Install target cannot be inside the repository being installed.")
        copy_plugin(source, target)
        print(f"Installed Skill Routing Kit to: {target}")

    if args.install_agents:
        snippet_path = target / "assets" / "agents-routing-snippet.md"
        action = install_agents_snippet(snippet_path, args.agents.expanduser().resolve())
        print(f"{action} routing guard in: {args.agents.expanduser().resolve()}")
    else:
        print("Routing guard not installed. Add --install-agents to enable it automatically.")

    marketplace_name = args.marketplace_name
    if args.skip_marketplace:
        print("Marketplace entry not updated. Omit --skip-marketplace to make the plugin discoverable.")
    else:
        marketplace_path = args.marketplace.expanduser().resolve()
        action, marketplace_name = update_marketplace_json(marketplace_path, marketplace_name)
        print(
            f"{action} marketplace entry in: {marketplace_path} "
            f"({PLUGIN_DIR_NAME}@{marketplace_name})"
        )

    if args.codex_add:
        if args.skip_marketplace:
            raise SystemExit("--codex-add requires marketplace registration. Remove --skip-marketplace.")
        run_codex_plugin_add(marketplace_name)
    elif not args.skip_marketplace:
        print(f"To activate through Codex CLI, run: codex plugin add {PLUGIN_DIR_NAME}@{marketplace_name}")

    print("Restart Codex or reload plugins if the new plugin does not appear immediately.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
