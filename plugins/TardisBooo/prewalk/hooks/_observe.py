"""Read-only runtime evidence adapter for hookless collaboration spawns.

Never accepts caller-supplied agent IDs, model assertions or completion text.
Only the plugin state is changed; Codex journals/configuration stay untouched.
This is post-launch observation, not a substitute for pre-launch enforcement.
"""
from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path

import _common
import prewalk_engine as core


def _events(path):
    if path.stat().st_size > 64 * 1024 * 1024:
        raise ValueError("runtime journal exceeds observation limit")
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                # A journal may be concurrently appending its final line.
                raise ValueError("runtime journal is incomplete; retry observation later")


def _time(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def observe(store, sid):
    loaded = core.load_v4_state(store, sid)
    state = loaded.state
    if state is None or state.phase not in ("handoff_requested", "executor_running"):
        return loaded.message or "No pending native route to observe."
    try:
        return _observe(store, sid, state)
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        return f"Prewalk observation unresolved; state retained; do not respawn: {exc}"


def _observe(store, sid, state):
    sessions = Path(_common.codex_home()) / "sessions"
    # Exact identity lookup, never a newest-session heuristic or caller path.
    roots = list(sessions.rglob(f"*-{sid}.jsonl"))
    if len(roots) != 1:
        raise ValueError("expected one journal for the exact root session")
    root_events = list(_events(roots[0]))
    meta = root_events[0]
    if meta.get("type") != "session_meta" or meta["payload"].get("id") != sid:
        raise ValueError("root journal identity mismatch")
    if core.workspace_identity(meta["payload"].get("cwd", "")) != state.workspace_id:
        raise ValueError("root journal workspace differs from the armed run")
    calls, outputs = [], {}
    for event in root_events:
        payload = event.get("payload", {})
        if event.get("type") != "response_item":
            continue
        if payload.get("type") == "function_call" and payload.get("name") == "spawn_agent" and payload.get("namespace") == "collaboration":
            args = json.loads(payload.get("arguments", "{}"))
            if args.get("task_name") == state.route_task_name:
                if _time(event["timestamp"]) < _time(state.route_requested_at):
                    raise ValueError("spawn predates this route")
                calls.append((payload["call_id"], args))
        if payload.get("type") == "function_call_output":
            outputs.setdefault(payload.get("call_id"), []).append(payload.get("output"))
    if len(calls) != 1:
        raise ValueError("expected exactly one matching collaboration spawn")
    call_id, args = calls[0]
    message = args.get("message", "")
    if not isinstance(message, str) or not message:
        raise ValueError("spawn message missing")
    # Some runtimes encrypt message bodies at rest. Do not decrypt them or
    # pretend exact packet equality was proven in that case. Identity still
    # requires the unique runtime call/result/parent/child chain below.
    if not message.startswith("gAAAAA") and message != core.codex_route_message(state):
        raise ValueError("plaintext spawn packet differs from the durable route")
    if args.get("model") != state.executor_model or args.get("fork_turns") != "none":
        raise ValueError("observed spawn model/fresh-context mismatch")
    if state.effort_routing_proven and args.get("reasoning_effort") != state.executor_effort:
        raise ValueError("observed spawn effort mismatch")
    responses = outputs.get(call_id, [])
    if len(responses) != 1:
        raise ValueError("spawn result missing or ambiguous")
    response = json.loads(responses[0])
    agent_path = response.get("task_name", "")
    if not agent_path.startswith("/root/") or agent_path.rsplit("/", 1)[-1] != state.route_task_name:
        raise ValueError("spawn did not return the expected canonical task path")
    candidates = []
    for path in sessions.rglob("*.jsonl"):
        with path.open(encoding="utf-8") as stream:
            first = json.loads(stream.readline())
        info = first.get("payload", {})
        source = info.get("source", {})
        spawn = source.get("subagent", {}).get("thread_spawn", {}) if isinstance(source, dict) else {}
        if spawn.get("parent_thread_id") == sid and spawn.get("agent_path") == agent_path:
            if first.get("type") != "session_meta" or _time(first["timestamp"]) < _time(state.route_requested_at):
                raise ValueError("child journal metadata is stale or invalid")
            candidates.append((path, info))
    if len(candidates) != 1:
        raise ValueError("expected one child journal with matching parent and task path")
    path, info = candidates[0]
    child_id = info.get("id", "")
    if not child_id or info.get("cwd") != meta["payload"].get("cwd"):
        raise ValueError("child identity/workspace mismatch")
    events = list(_events(path))
    contexts = [e["payload"] for e in events if e.get("type") == "turn_context"]
    if not contexts or any(c.get("model") != state.executor_model for c in contexts):
        raise ValueError("child runtime model not proven or changed")
    if state.effort_routing_proven and any(c.get("effort") != state.executor_effort for c in contexts):
        raise ValueError("child runtime effort not proven or changed")
    if state.route_tool_use_id and state.route_tool_use_id != call_id:
        raise ValueError("route already belongs to another call")
    if state.executor_agent_id and state.executor_agent_id != child_id:
        raise ValueError("route already belongs to another executor")
    if state.phase == "handoff_requested":
        core.apply_v4_transition(
            store, sid, expected_phases=["handoff_requested"], target_phase="executor_running",
            event_id=f"journal-bind:{call_id}:{child_id}",
            updates={"route_tool_use_id": call_id, "executor_agent_id": child_id,
                     "executor_started_at": events[0]["timestamp"], "launch_acknowledged": True})
    lifecycle = [e for e in events if e.get("type") == "event_msg" and
                 e.get("payload", {}).get("type") in ("task_started", "task_complete", "turn_aborted")]
    if not lifecycle or lifecycle[-1]["payload"]["type"] == "task_started":
        return f"Prewalk observed executor_running: {child_id}; no terminal result yet. Do not respawn."
    terminal = lifecycle[-1]
    payload = terminal["payload"]
    result = payload.get("last_agent_message", "") if payload["type"] == "task_complete" else "PREWALK_INCOMPLETE: runtime turn aborted"
    decision = core.finish_v4_executor(store, sid, agent_id=child_id, result=result,
                                     event_id=f"journal-stop:{child_id}:{terminal.get('ordinal', terminal['timestamp'])}")
    return f"Observed child {child_id}: {decision.message}"
