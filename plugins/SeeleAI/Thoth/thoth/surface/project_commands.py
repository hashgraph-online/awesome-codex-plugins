"""Project lifecycle public commands: init, sync, extend, hook."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from thoth.init.render import parse_config
from thoth.init.service import initialize_project, preview_project_migration, sync_project_layer
from thoth.projections import sync_repository_surfaces
from thoth.surface.envelope import output_refs, print_envelope
from thoth.surface.hooks import run_host_hook


def _normalize_preview_apply(args, flag_name: str, parser, command_name: str) -> None:
    action = getattr(args, flag_name, False)
    if action in {"preview", "apply"}:
        setattr(args, action, True)
    if getattr(args, "preview", False) and getattr(args, "apply", False):
        parser.exit(2, f"thoth: error: {command_name} accepts only one of preview or apply.\n")


def run_extend_tests(changed: list[str]) -> tuple[int, str]:
    tests_dir = Path(__file__).resolve().parents[2] / "tests"
    result = subprocess.run([sys.executable, "-m", "pytest", str(tests_dir), "-v", "--tb=short"], capture_output=True, text=True, timeout=120, cwd=str(Path(__file__).resolve().parents[2]))
    pieces: list[str] = []
    if changed:
        pieces.append("Changed files:\n" + "\n".join(f"- {item}" for item in changed))
    if result.stdout.strip():
        pieces.append(result.stdout.strip())
    if result.stderr.strip():
        pieces.append(result.stderr.strip())
    return (0 if result.returncode in {0, 5} else result.returncode), "\n\n".join(piece for piece in pieces if piece)


def handle_init(args, parser, *, project_root: Path) -> int:
    _normalize_preview_apply(args, "migrate", parser, "init --migrate")
    config = parse_config(args.config_json) if getattr(args, "config_json", None) else {}
    if getattr(args, "sync", False):
        result = sync_project_layer(project_root)
        print_envelope(command="init", status="ok", summary="Project sync completed", body={"result": result}, refs=output_refs(project_root / ".thoth" / "docs" / "object-graph-summary.json", project_root / ".thoth" / "derived" / "codex-hooks.json"))
        return 0
    if getattr(args, "migrate", False) and not getattr(args, "apply", False):
        result = preview_project_migration(config, project_root)
        print_envelope(command="init", status="ok", summary=f"Migration preview written for {project_root}", body={"result": result}, refs=output_refs(project_root / ".thoth" / "migrations" / result["migration_id"] / "preview.json"))
        return 0
    result = initialize_project(config, project_root)
    claude_permissions = result.get("claude_permissions") if isinstance(result.get("claude_permissions"), dict) else {}
    sources = claude_permissions.get("sources") if isinstance(claude_permissions.get("sources"), list) else []
    permission_guidance = (
        f"Claude bridge permission: ready via {sources[0]}"
        if sources
        else "Claude bridge permission: missing"
    )
    print_envelope(command="init", status="ok", summary=f"Initialized Thoth project at {project_root}; {permission_guidance}", body={"result": result, "permission_guidance": permission_guidance}, refs=output_refs(project_root / ".thoth" / "objects" / "project" / "project.json", project_root / ".thoth" / "docs" / "agent-entry.md", project_root / ".thoth" / "derived" / "codex-hooks.json"), checks=[{"name": "migration_id", "ok": bool(result.get("migration_id")), "detail": str(result.get("migration_id"))}])
    return 0


def handle_sync(args, parser, *, project_root: Path) -> int:
    result = sync_project_layer(project_root)
    written = sync_repository_surfaces(Path(__file__).resolve().parents[2])
    print_envelope(command="sync", status="ok", summary="Sync completed", body={"result": result, "repository_surfaces": [str(path) for path in written]}, refs=output_refs(project_root / ".thoth" / "docs" / "object-graph-summary.json", project_root / ".thoth" / "derived" / "codex-hooks.json"))
    return 0


def handle_hook(args, parser, *, project_root: Path) -> int:
    result = run_host_hook(host=args.host, event=args.event, project_root=project_root)
    if result.stdout:
        print(result.stdout, end="")
    return result.exit_code


def handle_extend(args, parser, *, project_root: Path) -> int:
    changed = getattr(args, "changed", []) or []
    returncode, text = run_extend_tests(changed)
    print_envelope(command="extend", status="ok" if returncode == 0 else "failed", summary="Extend completed" if returncode == 0 else "Extend failed", body={"changed": changed, "output": text}, checks=[{"name": "plugin_tests", "ok": returncode == 0}])
    return returncode
