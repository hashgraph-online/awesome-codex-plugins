#!/usr/bin/env python3
"""Codex PostToolUse mutation observer — the planner's edit budget.

This deliberately replaces the old edit *gate* (which blocked edits until a
todo list existed and disarmed on the second violation — a design that just
taught models to bypass prewalk). The frontier stays free to explore and
edit; the observer only counts successful file mutations during planning and
escalates:

* 6 edits — a nudge: finish verifying task #1 and wrap up;
* 12 edits — the limit: stop editing, write the checkpoint packet now.

Both messages travel as additionalContext (model-visible), never as a block.

Note: Codex hooks only intercept simple shell calls and the file-edit tools
(``apply_patch``), not WebSearch or complex pipelines — which is fine,
because the budget cares exactly about the file-edit surface.
"""

from __future__ import annotations

import _engine  # noqa: F401  (locates prewalk_engine)
import _common  # type: ignore[import-not-found]
import prewalk_engine as core  # noqa: E402


def main() -> int:
    payload = _common.read_input()
    sid = _common.session_id(payload)
    store = _common.existing_store()
    if store is None:
        return 0
    loaded = core.load_v4_state(store, sid)
    if loaded.state is None or loaded.state.phase != core.V4_PLANNING:
        return 0
    if not _common.normalize_mutation_success(payload):
        return 0
    _, nudge = core.note_v4_planner_mutation(store, sid)
    if loaded.state.fast_mode and loaded.state.plan_seen and not loaded.state.fast_gate_open:
        core.apply_v4_transition(store, sid, expected_phases=["planning"],
                                 target_phase="planning", event_id="codex-fast-gate",
                                 updates={"fast_gate_open": True})
        nudge = (
            "Prewalk fast gate opened: a saved plan was followed by a successful write. "
            "Finish verification of this first task, save the handoff packet and submit it "
            "with _pw.py checkpoint. After the durable receipt says next=pw-go, follow "
            "$prewalk:pw-go now. Do not implement the remaining tasks in the planner."
        )
    if nudge:
        _common.emit(core.HookAction(
            additional_context=nudge,
            system_message="prewalk: planner budget nudge.",
        ), event="PostToolUse")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
