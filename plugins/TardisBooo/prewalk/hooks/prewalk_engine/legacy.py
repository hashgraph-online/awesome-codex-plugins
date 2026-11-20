"""The 0.3 event machine, kept for compatibility — not the active workflow.

Before the durable-checkpoint redesign, prewalk drove its phases from todo
updates: a model-authored "⏸️ PAUSE" todo was the checkpoint, the packet
lived only in conversation context, and handoff state was a handful of
boolean flags. That design is superseded — the v4 machine in
:mod:`records`/:mod:`checkpoint`/:mod:`routing` owns every live run — but the
event handlers are preserved verbatim so old tooling that still calls them
behaves exactly as the 0.3 release did, and the regression suite can keep
proving the old machine's semantics on top of the shared store.

Nothing in the host adapters imports this module.
"""

from __future__ import annotations

import os
import secrets
from typing import Callable

from .prompts import (
    FAST_HANDOFF_HINT,
    HANDOFF_NOTE,
    HANDOFF_PACKET_TEMPLATE,
    HookAction,
    NO_HANDOFF_NEEDED,
    ONE_LEFT_HINT,
    PAUSED_HINT,
)
from .protocol import (
    DEFAULT_MAX_TODOS,
    EXECUTOR,
    FRONTIER,
    HANDOFF_REQUESTED,
    IDLE,
    PAUSED,
    Todo,
    count_remaining,
    validate_checkpoint,
    validate_todo_list,
)
from .records import PrewalkState
from .store import clear_state, load_state, save_state


def start_run(store_file: str | os.PathLike[str], session_id: str, preset,
              auto_swap: bool, turn: int = 0) -> PrewalkState:
    """Arm a new legacy run for this session (replaces any existing one)."""
    state = PrewalkState(
        session_id=session_id,
        phase=FRONTIER,
        preset=preset.name,
        max_todos=preset.max_todos,
        auto_swap=auto_swap,
        original_model=preset.planner_model,
        executor_model=preset.executor_model,
        planner_thinking=preset.planner_thinking,
        executor_thinking=preset.executor_thinking,
        handoff_mode=preset.handoff_mode,
        require_model_routing=preset.require_model_routing,
        created_turn=turn,
    )
    save_state(store_file, state)
    return state


def on_todos_changed(
    store_file: str | os.PathLike[str],
    session_id: str,
    todos: list[Todo],
    *,
    on_swap: Callable[[PrewalkState], None] | None = None,
) -> HookAction | None:
    """React to a todo-list update; drives the frontier→paused→executor machine.

    Returns a HookAction for the adapter to render, or None when the legacy
    machine has nothing to say. ``on_swap`` (if provided and auto_swap is
    set) is the host hook that would actually perform a model switch — kept
    out of the engine so it stays host-agnostic.
    """
    state = load_state(store_file, session_id)
    if state is None or state.phase == IDLE:
        return None
    if not todos:
        return None

    pause_present = any(todo.is_pause for todo in todos)
    if pause_present:
        state.pause_seen = True
    if state.phase == FRONTIER:
        state.frontier_todos_ever_seen = True
    remaining = count_remaining(todos)
    state.todos_remaining = remaining

    # Executor completion: all real todos done. The active root model never
    # changed.
    if state.phase == EXECUTOR:
        if remaining == 0:
            clear_state(store_file, session_id)
            return HookAction(
                system_message="prewalk: all todos completed; the active root session was unchanged.",
            )
        save_state(store_file, state)
        return None

    # Below: frontier / paused checkpoint logic — only meaningful when the
    # pause marker is part of this update.
    if not pause_present:
        save_state(store_file, state)
        return None

    checkpoint_error = validate_checkpoint(todos, cap=_preset_cap(state, len(todos)))
    if checkpoint_error:
        state.checkpoint_warning = checkpoint_error
        save_state(store_file, state)
        return HookAction(system_message="prewalk: checkpoint rejected — " + checkpoint_error)

    if remaining == 0:
        clear_state(store_file, session_id)
        return HookAction(system_message=NO_HANDOFF_NEEDED)
    if remaining == 1:
        # One todo left is not worth a model swap. Disarm the paused path but
        # keep completion detection armed.
        state.phase = EXECUTOR
        save_state(store_file, state)
        return HookAction(system_message=ONE_LEFT_HINT)

    state.phase = PAUSED
    state.checkpoint_evidence = "observed-edit" if state.first_edit_landed else "todo-only"
    state.checkpoint_warning = "" if state.first_edit_landed else (
        "The host did not observe task #1's edit. Review its diff and verification before handoff."
    )
    save_state(store_file, state)
    hint = FAST_HANDOFF_HINT if state.auto_swap else PAUSED_HINT
    if state.checkpoint_warning:
        hint += " Warning: " + state.checkpoint_warning
    return HookAction(additional_context=FAST_HANDOFF_HINT if state.auto_swap else "", system_message=hint)


def _preset_cap(state: PrewalkState, fallback: int) -> int:
    # max_todos was not persisted before v0.3; a conservative default keeps
    # old state files readable while new runs use the configured cap.
    return int(getattr(state, "max_todos", 0) or DEFAULT_MAX_TODOS or fallback)


def on_pw_go(store_file: str | os.PathLike[str], session_id: str, *, host: str = "claude") -> HookAction:
    """``/pw-go`` was invoked — the user confirms the handoff.

    Valid in the frontier or paused phase (the run is armed and the frontier
    has done its part). The two hosts hand off by different mechanisms, so
    the action line differs:

    - ``host="claude"``: the model spawns ONE Task; the PreToolUse router
      hook rewrites that spawn onto the executor model automatically.
    - ``host="codex"``: no hook can rewrite a Codex tool call, so the model
      itself calls native ``spawn_agent`` with explicit model and
      fork-turn parameters.

    Returns a no-checkpoint message when nothing is armed.
    """
    state = load_state(store_file, session_id)
    if state is None:
        return HookAction(
            additional_context=(
                "There is no active prewalk checkpoint in this session. Reply with a single line "
                "saying so and end your turn — do not touch the todo list or any file."
            )
        )
    if state.handoff_done or state.phase == EXECUTOR:
        return HookAction(
            additional_context=(
                "Prewalk already handed off to the executor. Continue the remaining work in the "
                "executor subagent; do not spawn another handoff."
            )
        )
    if state.phase == HANDOFF_REQUESTED:
        return HookAction(
            additional_context=(
                "A prewalk handoff is already pending confirmation. Confirm it after a successful spawn, "
                "or mark it failed so the checkpoint becomes retryable."
            )
        )
    if state.phase != PAUSED:
        return HookAction(
            additional_context=(
                "There is no active prewalk checkpoint in this session. Reply with a single line "
                "saying so and end your turn — do not touch the todo list or any file."
            )
        )
    state.phase = HANDOFF_REQUESTED
    state.handoff_host = host
    state.handoff_attempts += 1
    state.handoff_routed = False
    state.handoff_token = secrets.token_urlsafe(24) if host == "claude" else ""
    state.handoff_tool_use_id = ""
    state.executor_agent_id = ""
    state.handoff_launch_acknowledged = False
    state.last_handoff_error = ""
    save_state(store_file, state)

    if host == "codex" and state.handoff_mode == "manual-model":
        action_line = (
            f"ACTION: do not spawn a subagent. Ask the user to run `/model {state.executor_model}`"
            + (f" with thinking `{state.executor_thinking}`" if state.executor_thinking else "")
            + ", then run the `pw-resume` skill. Only `pw-resume` confirms the handoff."
        )
        sysmsg = f"prewalk: manual model handoff requested for {state.executor_model}."
    elif host == "codex":
        task_name = f"prewalk_executor_{state.handoff_attempts}"
        action_line = (
            f"ACTION: inspect the native `spawn_agent` schema, then call it exactly once with "
            f"`task_name=\"{task_name}\"`, the structured Handoff Packet as `message`, "
            f"`fork_turns=\"all\"`, and `model=\"{state.executor_model}\"`. "
            + (f"Include `reasoning_effort=\"{state.executor_thinking}\"` only if the schema supports it. "
               if state.executor_thinking else "")
            + "After the tool returns success, run `_pw.py confirm`; if it fails, run `_pw.py fail <reason>`. "
            + (f"Because `require_model_routing` is true, do not spawn without a model parameter; use the "
               f"manual `/model {state.executor_model}` + `pw-resume` fallback instead."
               if state.require_model_routing else
               "If model routing is unavailable, spawning on the runtime-selected model is allowed by this preset.")
        )
        sysmsg = f"prewalk: capability-safe handoff requested for {state.executor_model}."
    else:
        action_line = (
            f"ACTION: spawn ONE Task whose prompt contains the structured Handoff Packet and this exact "
            f"line: `PREWALK_HANDOFF_TOKEN: {state.handoff_token}`. The prewalk hook will route it onto "
            f"{state.executor_model}. Agent PostToolUse only acknowledges launch; the bound SubagentStop "
            f"event records the final marker. Do not switch models yourself or do the remaining edits here."
        )
        sysmsg = f"prewalk: handoff requested — spawn a Task for the remaining work (executor {state.executor_model})."
    return HookAction(
        additional_context=f"{HANDOFF_NOTE}\n\nRequired packet:\n{HANDOFF_PACKET_TEMPLATE}\n\n{action_line}",
        system_message=sysmsg,
    )


def on_handoff_confirm(store_file: str | os.PathLike[str], session_id: str) -> HookAction:
    """A spawn succeeded — enter the executor phase under the legacy machine."""
    state = load_state(store_file, session_id)
    if state is None or state.phase != HANDOFF_REQUESTED:
        return HookAction(additional_context="No pending prewalk handoff can be confirmed.")
    state.phase = EXECUTOR
    state.handoff_done = True
    state.handoff_routed = True
    state.last_handoff_error = ""
    save_state(store_file, state)
    return HookAction(system_message=f"prewalk: handoff confirmed on {state.executor_model}.")


def on_handoff_launch_ack(
    store_file: str | os.PathLike[str], session_id: str, tool_use_id: str
) -> HookAction | None:
    """Record success of the exact routed Agent call without treating it as completion."""
    state = load_state(store_file, session_id)
    if (
        state is None
        or state.phase not in (HANDOFF_REQUESTED, EXECUTOR)
        or not state.handoff_routed
        or not tool_use_id
        or tool_use_id != state.handoff_tool_use_id
    ):
        return None
    if state.handoff_launch_acknowledged:
        return None
    state.handoff_launch_acknowledged = True
    save_state(store_file, state)
    return HookAction(system_message="prewalk: executor launch acknowledged; waiting for its lifecycle result.")


def on_executor_started(
    store_file: str | os.PathLike[str], session_id: str, agent_id: str
) -> HookAction | None:
    """Bind the one routed Claude executor and enter the executor phase."""
    state = load_state(store_file, session_id)
    if (
        state is None
        or state.phase not in (HANDOFF_REQUESTED, EXECUTOR)
        or not state.handoff_routed
        or not state.handoff_tool_use_id
        or not agent_id
    ):
        return None
    if state.executor_agent_id:
        return None
    state.executor_agent_id = agent_id
    state.phase = EXECUTOR
    state.handoff_done = True
    state.last_handoff_error = ""
    save_state(store_file, state)
    return HookAction(system_message=f"prewalk: executor {agent_id} started on {state.executor_model}.")


def on_handoff_failed(
    store_file: str | os.PathLike[str], session_id: str, reason: str = "handoff failed"
) -> HookAction:
    """A spawn failed or was denied — restore the paused checkpoint."""
    state = load_state(store_file, session_id)
    if state is None or state.phase != HANDOFF_REQUESTED:
        return HookAction(additional_context="No pending prewalk handoff can be failed.")
    state.phase = PAUSED
    state.handoff_done = False
    state.handoff_routed = False
    state.handoff_token = ""
    state.handoff_tool_use_id = ""
    state.executor_agent_id = ""
    state.handoff_launch_acknowledged = False
    state.last_handoff_error = reason.strip() or "handoff failed"
    save_state(store_file, state)
    return HookAction(system_message="prewalk: handoff failed; checkpoint restored and `/pw-go` is retryable.")


def on_executor_result(
    store_file: str | os.PathLike[str], session_id: str, *, complete: bool, detail: str = ""
) -> HookAction:
    """The routed executor stopped — clear on complete, restore on incomplete."""
    state = load_state(store_file, session_id)
    if state is None:
        return HookAction(additional_context="No active prewalk executor run was found.")
    if state.phase != EXECUTOR:
        return HookAction(additional_context="Prewalk cannot record an executor result before handoff confirmation.")
    if complete:
        clear_state(store_file, session_id)
        return HookAction(
            system_message="prewalk: executor completed all work; the active root session was unchanged."
        )
    state.phase = PAUSED
    state.handoff_done = False
    state.handoff_routed = False
    state.handoff_token = ""
    state.handoff_tool_use_id = ""
    state.executor_agent_id = ""
    state.handoff_launch_acknowledged = False
    state.last_handoff_error = detail.strip() or "executor stopped with work remaining"
    save_state(store_file, state)
    return HookAction(system_message="prewalk: executor incomplete; checkpoint restored for `/pw-go` or `/pw-revise`.")


def on_pw_revise(store_file: str | os.PathLike[str], session_id: str, revision: str) -> HookAction:
    """``/pw-revise <changes>`` — keep the frontier model, fold the revision in."""
    state = load_state(store_file, session_id)
    if state is None or state.phase != PAUSED:
        return HookAction(
            additional_context=(
                "There is no active prewalk checkpoint to revise. Reply with a single line saying so "
                "and end your turn."
            )
        )
    # Stay paused; the frontier agent re-adds the ⏸️ checkpoint after revising.
    state.last_handoff_error = ""
    save_state(store_file, state)
    return HookAction(
        additional_context=(
            f"PREWALK REVISION: update the plan accordingly: {revision or '(no detail given)'}. "
            "Re-explore only what the revision affects, fix the todo list, re-verify task #1 if it "
            "changed, then re-add the `⏸️ PAUSE` checkpoint todo and stop again for confirmation."
        ),
        system_message="prewalk: plan revised on the frontier — review and `/pw-go` when ready.",
    )


def on_edit_attempt(
    store_file: str | os.PathLike[str],
    session_id: str,
    todos: list[Todo],
    cap: int = DEFAULT_MAX_TODOS,
) -> HookAction:
    """PreToolUse gate on an edit tool under the legacy machine.

    Blocks edits during the frontier phase until a valid capped todo list
    exists; disarms after a second violation rather than blocking forever.
    """
    state = load_state(store_file, session_id)
    if state is None or state.phase != FRONTIER:
        return HookAction()  # not arming — allow

    error = validate_todo_list(todos, cap)
    if error is None:
        return HookAction()  # valid todo list present — allow

    state.blocked_edits += 1
    if state.blocked_edits < 2:
        save_state(store_file, state)
        return HookAction(
            proceed=False,
            block_reason=error + " Create the todo list (with a validation checkpoint on every item) "
                               "before editing.",
        )
    # Second violation: restore + disarm to avoid a loop.
    clear_state(store_file, session_id)
    return HookAction(
        proceed=False,
        block_reason=(
            "Prewalk disarmed after a second edit attempt without the required todo list. Create a "
            "valid todo list and re-run `/prewalk` if you still want the handoff."
        ),
    )


def on_turn_end(store_file: str | os.PathLike[str], session_id: str) -> HookAction | None:
    """Stop hook under the legacy machine.

    If the frontier finished without ever emitting a todo list, this is the
    trivial path — close cleanly. If it emitted todos but never the ⏸️
    checkpoint, warn once and close (anomaly). Otherwise no-op: the paused
    checkpoint is driven by todo updates, handled elsewhere.
    """
    state = load_state(store_file, session_id)
    if state is None:
        return None
    if state.phase == FRONTIER and not state.frontier_todos_ever_seen:
        clear_state(store_file, session_id)
        return HookAction(system_message="prewalk: trivial task — protocol not engaged.")
    if state.phase == FRONTIER and state.frontier_todos_ever_seen and not state.pause_seen:
        clear_state(store_file, session_id)
        return HookAction(
            system_message="prewalk: checkpoint todo (⏸️ PAUSE) not detected — check the todo format.",
        )
    return None


def on_fast_handoff(
    store_file: str | os.PathLike[str], session_id: str, *, host: str
) -> HookAction | None:
    """Request one automatic handoff from a validated fast-mode checkpoint."""
    state = load_state(store_file, session_id)
    if state is None or state.phase != PAUSED or not state.auto_swap:
        return None
    requested = on_pw_go(store_file, session_id, host=host)
    return HookAction(
        proceed=False,
        block_reason=requested.additional_context,
        system_message=requested.system_message,
    )
