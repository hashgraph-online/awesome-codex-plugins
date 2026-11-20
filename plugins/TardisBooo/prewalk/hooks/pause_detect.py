#!/usr/bin/env python3
"""Codex root Stop hook: validate and durably capture the v4 checkpoint.

Two jobs, in order:

1. If the host reports an interruption of the bound executor, recover the
   route to ``incomplete`` (retryable) instead of leaving it dangling.
2. Otherwise run the checkpoint capture. A *valid* checkpoint under fast
   mode immediately blocks the Stop and asks the model to execute the
   handoff route; a *malformed* one is rejected with a bounded number of
   blocking retries so the planner can repair its packet in-session; a
   finished-or-trivial plan ends the run without a handoff.
"""

from __future__ import annotations

import hashlib

import _engine  # noqa: F401  (locates prewalk_engine — must precede the import below)
import _common  # type: ignore[import-not-found]
import prewalk_engine as core  # noqa: E402


def main() -> int:
    payload = _common.read_input()
    event = str(payload.get("hook_event_name") or "Stop")
    sid = _common.session_id(payload)
    store = _common.existing_store()
    if store is None:
        return 0

    if event != "Stop":
        return 0

    todos = _common.normalize_todos(payload)
    if not sid:
        _common.emit(core.HookAction(system_message="prewalk: Stop ignored: missing or conflicting session identity"), event="Stop")
        return 0
    reason = str(payload.get("reason") or payload.get("stop_reason") or payload.get("stopReason") or "")
    interrupted = core.interrupt_v4_executor(
        store,
        sid,
        reason=reason,
        event_id=str(payload.get("event_id") or payload.get("eventId") or ""),
    )
    if interrupted.handled:
        _common.emit(core.HookAction(system_message=interrupted.message), event="Stop")
        return 0
    active = core.load_v4_state(store, sid).state
    if active:
        _common.audit("Stop", "received", phase=active.phase)
    if active and active.phase in ("handoff_requested", "executor_running"):
        from _observe import observe
        _common.emit(core.HookAction(system_message=observe(store, sid)), event="Stop")
        return 0
    packet = str(
        payload.get("last_assistant_message")
        or payload.get("lastAssistantMessage")
        or ""
    )
    event_id = str(payload.get("event_id") or payload.get("eventId") or "")
    result = core.capture_v4_checkpoint(
        store, sid, packet=packet, todos=todos or None, event_id=event_id
    )
    if active:
        _common.audit("checkpoint", result.status, packet_chars=len(packet),
                      packet_sha256=hashlib.sha256(packet.encode("utf-8")).hexdigest())
    if result.message:
        if (
            result.status == "checkpoint_ready"
            and result.state is not None
            and result.state.fast_mode
        ):
            core.apply_v4_transition(
                store,
                sid,
                expected_phases=[core.V4_CHECKPOINT_READY],
                target_phase=core.V4_CHECKPOINT_READY,
                event_id=f"codex-fast-continuation:{event_id or result.state.revision}",
                updates={"fast_mode": False},
            )
            _common.emit(core.HookAction(
                proceed=False,
                block_reason=(
                    "Prewalk fast checkpoint is durable. Inspect the live spawn_agent schema, "
                    "then run $prewalk:pw-go and execute its exact token-bound route now."
                ),
                system_message=result.message,
            ), event="Stop")
            return 0
        if result.status in (
            "missing_todos",
            "invalid_todos",
            "incomplete_task_one",
            "invalid_packet",
            "missing_evidence",
        ):
            # A malformed checkpoint is recoverable: block the Stop with the
            # reason so the planner emits a corrected packet (bounded retries),
            # instead of dying with a user-only system message.
            loaded = core.load_v4_state(store, sid)
            source = "event" if todos else "state" if loaded.state and loaded.state.todos else "packet"
            diagnostic = (
                f"{result.message} [source={source}; packet_chars={len(packet)}; "
                f"packet_sha256={hashlib.sha256(packet.encode('utf-8')).hexdigest()}]"
            )
            count, retry = core.note_v4_checkpoint_reject(store, sid, reason=diagnostic)
            if retry:
                _common.emit(core.HookAction(
                    proceed=False,
                    block_reason=(
                        f"Your Prewalk checkpoint was rejected: {result.message} "
                        "Fix it now (todo list and/or final packet), then stop again."
                    ),
                    system_message=f"prewalk: checkpoint rejected ({count}/"
                    f"{core.V4_CHECKPOINT_RETRY_LIMIT}); model asked to correct it.",
                ), event="Stop")
                return 0
        _common.emit(core.HookAction(system_message=result.message), event="Stop")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as exc:
        _common.emit(core.HookAction(system_message=f"prewalk: Stop processing failed: {exc}"), event="Stop")
        raise SystemExit(1)
