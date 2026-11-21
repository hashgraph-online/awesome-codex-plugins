#!/usr/bin/env python3
"""Codex native spawn and SubagentStop adapter for token-bound v4 routes.

One script serves the three events registered in ``hooks.json``:

* **PreToolUse** on ``spawn_agent`` — validate the model's spawn against the
  minted route (exact task name, exact message, correct ``fork_turns``,
  configured model and effort) and deny mismatches before execution;
* **PostToolUse** on ``spawn_agent`` — bind the agent id the runtime
  actually returned to this exact tool call, or fail the route when the
  spawn produced no usable identity;
* **SubagentStop** — consume the final marker, but only from the bound
  agent; every other stop event is a no-op.
"""

from __future__ import annotations

from typing import Any

import _engine  # noqa: F401  (locates prewalk_engine)
import _common  # type: ignore[import-not-found]
import prewalk_engine as core  # noqa: E402


def _part(payload: dict, snake: str, camel: str):
    return payload[snake] if snake in payload else payload.get(camel)


def _tool_name(payload: dict) -> str:
    raw = str(payload.get("tool_name") or payload.get("toolName") or "")
    normalized = raw.rsplit(".", 1)[-1].lower()
    return "spawn_agent" if normalized.endswith("__spawn_agent") else normalized


def _find_agent_id(value: Any) -> str:
    """Dig an agent/thread id out of an arbitrary response envelope."""
    if isinstance(value, list):
        for item in value:
            found = _find_agent_id(item)
            if found:
                return found
        return ""
    if not isinstance(value, dict):
        return ""
    for key in ("agent_id", "agentId", "agent_thread_id", "agentThreadId", "thread_id", "threadId"):
        if value.get(key):
            return str(value[key]).strip()
    for key in ("result", "output", "data", "structured_content", "structuredContent"):
        found = _find_agent_id(value.get(key))
        if found:
            return found
    for nested in value.values():
        found = _find_agent_id(nested)
        if found:
            return found
    return ""


def main() -> int:
    payload = _common.read_input()
    sid = _common.session_id(payload)
    if not sid:
        return 0
    event = str(payload.get("hook_event_name") or payload.get("hookEventName") or "")
    store = _common.existing_store()
    if store is None:
        return 0

    if event == "PreToolUse" and _tool_name(payload) == "spawn_agent":
        tool_input = _part(payload, "tool_input", "toolInput")
        decision = core.validate_codex_spawn(
            store,
            sid,
            tool_input if isinstance(tool_input, dict) else {},
            tool_use_id=str(_part(payload, "tool_use_id", "toolUseId") or ""),
        )
        if decision.handled and not decision.allowed:
            _common.emit(
                core.HookAction(proceed=False, block_reason=decision.message),
                event="PreToolUse",
                deny_as_permission=True,
            )
        return 0

    if event == "PostToolUse" and _tool_name(payload) == "spawn_agent":
        response = _part(payload, "tool_response", "toolResponse")
        success = response is not None and not _common.has_explicit_failure(response)
        decision = core.bind_codex_executor(
            store,
            sid,
            tool_use_id=str(_part(payload, "tool_use_id", "toolUseId") or ""),
            agent_id=_find_agent_id(response),
            success=success,
            detail="spawn_agent failed or returned no agent identity",
        )
        if decision.handled:
            _common.emit(core.HookAction(system_message=decision.message), event="PostToolUse")
        return 0

    if event == "SubagentStop":
        agent_id = _find_agent_id(payload)
        result = str(
            _part(payload, "last_assistant_message", "lastAssistantMessage")
            or payload.get("result")
            or payload.get("message")
            or ""
        )
        decision = core.finish_v4_executor(
            store,
            sid,
            agent_id=agent_id,
            result=result,
            event_id=str(payload.get("event_id") or payload.get("eventId") or ""),
        )
        if decision.handled:
            _common.emit(core.HookAction(system_message=decision.message), event="SubagentStop")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
