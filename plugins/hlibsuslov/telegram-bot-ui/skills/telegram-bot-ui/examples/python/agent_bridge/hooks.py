"""Adapters from coding-agent hooks to bridge operations.

Verified on 2026-11-15 from the official docs:

Claude Code (https://code.claude.com/docs/en/hooks)
* Hooks live in settings.json under "hooks" -> event -> [{matcher?, hooks:
  [{type: "command", command, timeout?}]}]. A command hook gets one JSON
  object on stdin with common fields (session_id, transcript_path, cwd,
  permission_mode, hook_event_name).
* Notification: + `message`, optional `title`, `notification_type`
  (matchers e.g. permission_prompt, idle_prompt). Exit code ignored; can't
  block.
* Stop: + `stop_hook_active`, `last_assistant_message`, `background_tasks`,
  `session_crons`. Exit 2 / {"decision": "block"} keeps Claude working -
  this adapter never blocks.
* PermissionRequest: + `tool_name`, `tool_input`; it may answer with
  {"hookSpecificOutput": {"hookEventName": "PermissionRequest",
  "decision": {"behavior": "allow" | "deny", "message"?}}}. Deny rules still
  win over "allow". No decision -> the normal permission flow.
* Default command-hook timeout: 600 s. Keep the approval TTL below the hook's
  `timeout`, or the hook is cancelled and its output discarded.

Codex (https://learn.chatgpt.com/docs/hooks, config reference)
* hooks.json (~/.codex/hooks.json or <repo>/.codex/hooks.json) or inline
  [hooks] in config.toml; `features.hooks` enables them; non-managed hooks must
  be reviewed and trusted (/hooks) before they run.
* Events include PreToolUse, PermissionRequest, PostToolUse, Stop, ...
  Common stdin fields include session_id, transcript_path, cwd,
  hook_event_name, model. Stop adds turn_id, stop_hook_active,
  last_assistant_message and "expects JSON on stdout when it exits 0".
* PermissionRequest answers with the same hookSpecificOutput.decision shape;
  any deny wins; no decision -> the normal approval flow.
* `notify` (config.toml, array<string>) runs a program that "receives a JSON
  payload from Codex". The payload's field names were NOT verified on
  2026-11-15; `codex_notify_text` reads them defensively.
"""
from __future__ import annotations

import os
import unicodedata
from typing import Any

MAX_SUMMARY = 600
MAX_DETAILS = 3000


def _visible(text: str) -> str:
    """Show invisible format characters (bidi overrides, zero-width) as escapes so the
    operator sees what will actually run, not a reordered or hidden version."""
    return "".join(f"\\u{ord(ch):04x}" if unicodedata.category(ch) == "Cf" else ch for ch in str(text))


def _project(payload: dict[str, Any]) -> str:
    return os.path.basename(str(payload.get("cwd") or "").rstrip("/\\")) or "session"


def _clip(text: str, n: int = MAX_SUMMARY) -> str:
    text = " ".join(str(text).split()) if "\n" not in str(text) else str(text).strip()
    return text if len(text) <= n else text[: n - 1] + "…"


def notification_text(payload: dict[str, Any]) -> str:
    title = payload.get("title") or "Needs your attention"
    return f"{title} — {_project(payload)}\n{_clip(payload.get('message') or '')}".strip()


def stop_text(payload: dict[str, Any]) -> str | None:
    if payload.get("stop_hook_active"):
        return None                 # already continuing because of a stop hook: don't spam
    last = payload.get("last_assistant_message") or "(no final message)"
    tasks = payload.get("background_tasks") or []
    tail = f"\n{len(tasks)} background task(s) still running." if tasks else ""
    return f"Turn finished — {_project(payload)}\n{_clip(last)}{tail}"


def permission_summary(payload: dict[str, Any]) -> tuple[str, str]:
    tool = str(payload.get("tool_name") or "tool")
    inp = payload.get("tool_input") or {}
    what = _visible(inp.get("command") or inp.get("file_path") or inp.get("url") or "")
    desc = _visible(inp.get("description") or "")
    summary = f"{tool} in {_project(payload)}: {_clip(what, 300)}" + (f"\n{_clip(desc, 200)}" if desc else "")
    details = _clip(_visible(str(inp)), MAX_DETAILS)
    return summary, details


def permission_reviewable(payload: dict[str, Any]) -> bool:
    """False when the full request does not fit the Details view: approving a request
    whose tail the operator never saw is not an approval, so it goes back to the
    host's local prompt instead of Telegram."""
    return len(_visible(str(payload.get("tool_input") or {}))) <= MAX_DETAILS


def permission_output(decision: str | None, reason: str | None = None) -> dict[str, Any]:
    """Claude Code and Codex share this shape. None -> {} = no decision."""
    if decision not in ("allow", "deny"):
        return {}
    d: dict[str, Any] = {"behavior": decision}
    if decision == "deny" and reason:
        d["message"] = reason
    return {"hookSpecificOutput": {"hookEventName": "PermissionRequest", "decision": d}}


def codex_notify_text(payload: dict[str, Any]) -> str:
    """Defensive reader for Codex `notify` (field names unverified)."""
    kind = payload.get("type") or "notification"
    last = payload.get("last-assistant-message") or payload.get("last_assistant_message") or ""
    return f"Codex: {kind}\n{_clip(last)}".strip()


__all__ = ["notification_text", "stop_text", "permission_summary", "permission_reviewable",
           "permission_output", "codex_notify_text"]
