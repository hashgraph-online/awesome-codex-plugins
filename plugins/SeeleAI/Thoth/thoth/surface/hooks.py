"""Host hook helpers for Claude Code and Codex surfaces.

Hooks are intentionally advisory. They may emit context, append observability
events, and refresh heartbeats, but they must not become correctness-critical
runtime authority.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from thoth.objects import Store, slugify
from thoth.run.io import _read_json
from thoth.run.model import utc_now
from thoth.run.service import list_active_runs


@dataclass
class HookResult:
    exit_code: int = 0
    stdout: str = ""


def _read_hook_input() -> dict[str, Any]:
    if sys.stdin.isatty():
        return {}
    raw = sys.stdin.read().strip()
    if not raw:
        return {}
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _is_thoth_project(project_root: Path) -> bool:
    return (project_root / ".thoth" / "objects" / "project" / "project.json").exists()


def _load_project_name(project_root: Path) -> str:
    manifest = _read_json(project_root / ".thoth" / "objects" / "project" / "project.json")
    payload = manifest.get("payload") if isinstance(manifest.get("payload"), dict) else {}
    name = payload.get("project", {}).get("name") if isinstance(payload.get("project"), dict) else None
    if isinstance(name, str) and name.strip():
        return name.strip()
    return ""


def _append_project_note(project_root: Path, payload: dict[str, Any]) -> None:
    store = Store(project_root)
    store.ensure_tree()
    event = str(payload.get("event") or "hook")
    discussion_id = f"HOOK-{utc_now().replace(':', '').replace('-', '')}-{slugify(event)[:20]}"
    store.create(
        kind="discussion",
        object_id=discussion_id,
        status="inquiring",
        title=f"Hook {event}",
        summary=f"Host hook event {event}",
        source=f"hook:{payload.get('host') or 'unknown'}",
        payload={
            "messages": [{"role": "system", "content": json.dumps(payload, ensure_ascii=False), "created_at": utc_now()}],
            "facts": [{"type": "hook", **payload}],
            "constraints": [],
            "decisions": [],
            "open_questions": [],
            "closure_summary": None,
        },
    )


def _truncate(value: str, *, limit: int = 160) -> str:
    if len(value) <= limit:
        return value
    return value[: limit - 3].rstrip() + "..."


def _lightweight_issues(project_root: Path) -> list[str]:
    issues: list[str] = []
    if not (project_root / ".thoth" / "objects" / "project" / "project.json").exists():
        issues.append("missing .thoth/objects/project/project.json")
    if (project_root / ".agent-os").exists() and not (project_root / ".agent-os" / "project-index.md").exists():
        issues.append("missing .agent-os/project-index.md")
    return issues


def _session_start_context(project_root: Path, *, host: str, hook_input: dict[str, Any]) -> str:
    project_name = _load_project_name(project_root) or project_root.name
    active_runs = list_active_runs(project_root)
    source = (
        hook_input.get("source")
        or hook_input.get("reason")
        or hook_input.get("hook_event_name")
        or "startup"
    )
    if active_runs:
        run_summary = "; ".join(
            f"{row['run_id']} [{row.get('kind')}] {row.get('status')}/{row.get('phase')} {row.get('progress_pct')}%"
            for row in active_runs[:3]
        )
        return (
            f"Thoth project detected: {project_name}. Session source: {source}. "
            f"Active durable runs: {run_summary}. "
            "Prefer status/attach or explicit takeover before starting parallel work. "
            "The .thoth ledger remains the only authority; hooks are advisory."
        )
    return (
        f"Thoth project detected: {project_name}. Session source: {source}. "
        "No active durable runs were found. "
        f"Use {'/thoth:status' if host == 'claude' else '$thoth status'} before starting new work if runtime state matters. "
        "The .thoth ledger remains the only authority; hooks are advisory."
    )


def _json_hook_output(
    event_name: str | None = None,
    *,
    additional_context: str | None = None,
    system_message: str | None = None,
) -> str:
    payload: dict[str, Any] = {}
    if event_name is not None:
        payload["hookSpecificOutput"] = {"hookEventName": event_name}
    if additional_context:
        payload["hookSpecificOutput"]["additionalContext"] = additional_context
    if system_message:
        payload["systemMessage"] = system_message
    return json.dumps(payload, ensure_ascii=False)


def run_host_hook(*, host: str, event: str, project_root: Path) -> HookResult:
    root = project_root.resolve()
    hook_input = _read_hook_input()

    if not _is_thoth_project(root):
        if host == "claude" and event == "start":
            return HookResult(stdout="No Thoth project. Run /thoth:init to set up.\n")
        return HookResult()

    active_runs = list_active_runs(root)
    _append_project_note(
        root,
        {
            "host": host,
            "event": event,
            "session_id": hook_input.get("session_id"),
            "source": hook_input.get("source") or hook_input.get("reason"),
            "active_run_ids": [row["run_id"] for row in active_runs],
            "last_assistant_message": _truncate(str(hook_input.get("last_assistant_message", ""))) if hook_input.get("last_assistant_message") else "",
        },
    )

    if event == "start":
        context = _session_start_context(root, host=host, hook_input=hook_input)
        return HookResult(stdout=_json_hook_output("SessionStart", additional_context=context) + "\n")

    issues = _lightweight_issues(root)
    if host == "codex" and event == "stop":
        system_message = None
        if issues:
            system_message = (
                "Thoth observed lightweight project issues: "
                + ", ".join(issues)
                + ". Run $thoth doctor if the runtime looks unhealthy."
            )
        return HookResult(
            stdout=_json_hook_output(
                None,
                system_message=system_message,
            )
            + "\n"
        )

    if host == "claude" and event == "end":
        active_count = len(active_runs)
        return HookResult(
            stdout=(
                f"Thoth SessionEnd: {max(0, 2 - len(issues))} lightweight checks passed, "
                f"{len(issues)} issue(s), {active_count} active durable run(s) observed.\n"
            )
        )

    return HookResult()
