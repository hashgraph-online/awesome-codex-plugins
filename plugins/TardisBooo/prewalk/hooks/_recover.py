"""Explicit recovery of a planning run from its own durable final packet.

The source store and native journal are never rewritten. Listing candidates is
read-only; committing requires an exact ordinal, never a newest-thread guess.
"""
import hashlib
import json
from pathlib import Path

import _common
import prewalk_engine as core
from prewalk_engine.checkpoint import packet_todos, packet_verification
from prewalk_engine.protocol import missing_packet_headings, validate_todo_list
from prewalk_engine.store import _store_lock, _read_all_with_status, _write_all, utc_timestamp


def recover(sid, ordinal=None):
    workspace = Path(_common.workspace_root()).resolve()
    source = Path(_common.store_file())
    raw = json.loads(source.read_text(encoding="utf-8")).get(sid)
    state = core.V4State.from_dict(raw)
    core.validate_v4_state(state)
    if state.phase != "planning":
        raise ValueError("recovery only accepts planning; pending executors must be reconciled")
    from _observe import _events, _time
    paths = list((Path(_common.codex_home()) / "sessions").rglob(f"*-{sid}.jsonl"))
    if len(paths) != 1:
        raise ValueError("recovery requires exactly one journal for this session")
    events = list(_events(paths[0]))
    metadata = events[0].get("payload", {})
    if metadata.get("id") != sid or core.workspace_identity(metadata.get("cwd", "")) != core.workspace_identity(workspace):
        raise ValueError("journal session/workspace mismatch")
    candidates = []
    for index, event in enumerate(events):
        payload = event.get("payload", {})
        if event.get("type") != "response_item" or payload.get("type") != "message" or payload.get("role") != "assistant":
            continue
        if (payload.get("channel") or payload.get("phase")) not in ("final", "final_answer") or _time(event["timestamp"]) < _time(state.created_at):
            continue
        packet = "\n".join(part.get("text", "") for part in payload.get("content", []) if isinstance(part, dict))
        todos = packet_todos(packet)
        if not todos or validate_todo_list(todos, state.max_todos) or todos[0].status != "completed":
            continue
        if missing_packet_headings(packet) or not any(packet_verification(packet)):
            continue
        if not any(todo.status != "completed" for todo in todos):
            continue
        candidates.append({"ordinal": event.get("ordinal", index), "timestamp": event["timestamp"],
                           "sha256": hashlib.sha256(packet.encode("utf-8")).hexdigest(), "packet": packet})
    if ordinal is None:
        print(json.dumps({"status": "recovery_candidates", "source": str(source),
                          "workspace": str(workspace), "candidates": [
                              {k: v for k, v in c.items() if k != "packet"} for c in candidates]}))
        return 0
    selected = [c for c in candidates if str(c["ordinal"]) == str(ordinal)]
    if len(selected) != 1:
        raise ValueError("selected ordinal is not a unique valid final checkpoint")
    packet = selected[0]["packet"]
    target = workspace / ".prewalk/state.json"
    if source.resolve() != target.resolve():
        state.workspace_id = core.workspace_identity(workspace)
        state.updated_at = state.last_event_at = utc_timestamp()
        state.revision += 1
        state.processed_event_ids.append(f"explicit-recovery:{selected[0]['sha256']}")
        core.validate_v4_state(state)
        with _store_lock(target):
            data, status = _read_all_with_status(target)
            if status == "corrupt_store" or sid in data:
                raise ValueError("recovery destination already contains state; not overwritten")
            data[sid] = state.to_dict()
            _write_all(target, data)
    result = core.capture_v4_checkpoint(target, sid, packet=packet, todos=packet_todos(packet))
    if result.status != "checkpoint_ready":
        raise ValueError(result.message)
    _common.audit("recovery", "checkpoint_ready", ordinal=ordinal, source=str(source))
    print(json.dumps({"status": result.status, "packet_sha256": selected[0]["sha256"],
                      "store": str(target), "next": "await_user_review"}))
    return 0
