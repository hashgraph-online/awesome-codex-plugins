#!/usr/bin/env python3
"""Codex PostToolUse hook that persists complete real-work plan snapshots.

Runs on the plan/todo tools (``update_plan`` / ``todo``). Only full list
snapshots are recorded — a single-task mutation is not a plan. An invalid
snapshot (wrong shape, over the cap, missing verification criteria) is
echoed back to the model as additionalContext immediately, so the planner
fixes its todo list on the next step instead of failing the Stop checkpoint
much later.
"""

from __future__ import annotations

import _engine  # noqa: F401  (locates prewalk_engine)
import _common  # type: ignore[import-not-found]
import prewalk_engine as core  # noqa: E402


def main() -> int:
    payload = _common.read_input()
    if not _common.normalize_edit_success(payload):
        return 0
    sid = _common.session_id(payload)
    store = _common.existing_store()
    if store is None:
        return 0
    loaded = core.load_v4_state(store, sid)
    if loaded.state is None or loaded.state.phase != core.V4_PLANNING:
        return 0

    if not loaded.state.plan_seen:
        core.apply_v4_transition(store, sid, expected_phases=["planning"],
                                 target_phase="planning", event_id="codex-plan-seen",
                                 updates={"plan_seen": True})

    todos = _common.normalize_todos(payload)
    if not todos or not _common.has_complete_todo_snapshot(payload):
        return 0

    result = core.record_v4_todos(store, sid, todos)
    if result.status == "invalid_todos":
        # additionalContext reaches the model (systemMessage does not); the
        # planner can fix the todo list on its next step instead of failing
        # the Stop checkpoint later.
        _common.emit(core.HookAction(
            additional_context=f"prewalk todo check: {result.message}",
            system_message="prewalk: todo snapshot rejected; correction requested.",
        ), event="PostToolUse")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
