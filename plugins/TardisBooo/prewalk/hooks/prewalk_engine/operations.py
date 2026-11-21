"""Operational queries: staleness, retry, reconcile, and status rendering.

These are the "operator console" functions behind ``pw-status``,
``pw-retry``, and ``pw-reconcile``. Their shared posture: **never guess about
a possibly-running agent.**

* :func:`detect_v4_stale` only *labels* an overdue route; it never clears or
  stops anything, because killing an unknown agent is exactly how finished
  work gets lost.
* :func:`reconcile_v4_route` demands explicit liveness proof — a native agent
  list, or the human accepting responsibility — before it will touch an
  ambiguous route.
* :func:`prepare_v4_retry` re-arms only a *proven* incomplete route, keeping
  task 1 and the exact packet, and refuses whenever an executor may still be
  alive.

:func:`format_v4_status` renders a safe summary: the token appears only as a
sha256 prefix, the packet never appears at all.
"""

from __future__ import annotations

import hashlib
import os

from .records import (
    V4CheckpointResult,
    _parse_v4_timestamp,
    _v4_content_event_id,
    apply_v4_transition,
    load_v4_state,
)
from .store import clear_state, has_record, utc_timestamp


def detect_v4_stale(
    store_file: str | os.PathLike[str],
    root_session_id: str,
    *,
    now: str | None = None,
    timeout_seconds: int = 24 * 60 * 60,
    workspace_id: str = "",
) -> V4CheckpointResult:
    """Mark an overdue ambiguous route stale without clearing or stopping it."""
    loaded = load_v4_state(store_file, root_session_id, workspace_id=workspace_id)
    state = loaded.state
    if state is None:
        return V4CheckpointResult(loaded.status, loaded.message)
    if state.phase == "stale":
        return V4CheckpointResult("stale", state.last_error, state)
    if state.phase not in ("handoff_requested", "executor_running"):
        return V4CheckpointResult(state.phase, "No active route can become stale.", state)
    if timeout_seconds < 1:
        return V4CheckpointResult(
            "invalid_timeout", "The stale timeout must be positive.", state
        )
    checked_at = now or utc_timestamp()
    checked = _parse_v4_timestamp(checked_at, "stale check time")
    reference_name = (
        "executor_started_at" if state.phase == "executor_running" else "route_requested_at"
    )
    reference_value = getattr(state, reference_name)
    reference = _parse_v4_timestamp(reference_value, reference_name)
    elapsed = (checked - reference).total_seconds()
    if elapsed < timeout_seconds:
        return V4CheckpointResult(
            "active", f"Route liveness is not stale ({int(max(elapsed, 0))}s elapsed).", state
        )
    reason = (
        f"No matching native lifecycle event was observed for {int(elapsed)}s; "
        "executor liveness is unknown and no agent was stopped or cleared."
    )
    stale = apply_v4_transition(
        store_file,
        root_session_id,
        expected_phases=[state.phase],
        target_phase="stale",
        event_id=_v4_content_event_id(
            "route-stale", root_session_id, state.route_attempt, reference_value, timeout_seconds
        ),
        now=checked_at,
        updates={"last_error": reason},
    )
    return V4CheckpointResult("stale", reason, stale)


def prepare_v4_retry(
    store_file: str | os.PathLike[str], root_session_id: str
) -> V4CheckpointResult:
    """Reset only a proven-incomplete route while retaining task 1 and its packet.

    Every phase that could still have a live executor refuses; only
    ``incomplete`` — which by construction means the route already ended —
    may mint a fresh one.
    """
    loaded = load_v4_state(store_file, root_session_id)
    state = loaded.state
    if state is None:
        return V4CheckpointResult(loaded.status, loaded.message)
    if state.phase == "checkpoint_ready":
        return V4CheckpointResult("checkpoint_ready", "Prewalk retry is already prepared.", state)
    if state.phase == "handoff_requested":
        return V4CheckpointResult(
            "handoff_requested",
            "A route is already pending; reuse it rather than creating another executor.",
            state,
        )
    if state.phase in ("executor_running", "stale"):
        return V4CheckpointResult(
            "agent_may_be_running",
            "Prewalk will not retry while an executor may still be running; run pw-reconcile first.",
            state,
        )
    if state.phase != "incomplete":
        return V4CheckpointResult(
            "not_retryable", f"Prewalk cannot retry from {state.phase}.", state
        )
    prepared = apply_v4_transition(
        store_file,
        root_session_id,
        expected_phases=["incomplete"],
        target_phase="checkpoint_ready",
        event_id=f"route-retry:{root_session_id}:{state.route_attempt}:{state.revision}",
        updates={
            "route_token": "",
            "route_task_name": "",
            "route_tool_use_id": "",
            "executor_agent_id": "",
            "route_requested_at": "",
            "executor_started_at": "",
            "launch_acknowledged": False,
            "model_routing_proven": False,
            "effort_routing_proven": False,
            "last_error": "",
        },
    )
    return V4CheckpointResult(
        "checkpoint_ready",
        "Prewalk retained task 1 and the exact packet; request one new executor route.",
        prepared,
    )


def reconcile_v4_route(
    store_file: str | os.PathLike[str],
    root_session_id: str,
    *,
    confirmed_not_running: bool,
    detail: str = "",
) -> V4CheckpointResult:
    """Resolve an ambiguous route only after explicit external liveness proof."""
    loaded = load_v4_state(store_file, root_session_id)
    state = loaded.state
    if state is None:
        return V4CheckpointResult(loaded.status, loaded.message)
    if state.phase == "incomplete":
        return V4CheckpointResult(
            "incomplete", "Prewalk route is already reconciled; run pw-retry.", state
        )
    if state.phase not in ("handoff_requested", "executor_running", "stale"):
        return V4CheckpointResult(
            "not_ambiguous", f"Prewalk has no ambiguous route to reconcile ({state.phase}).", state
        )
    if not confirmed_not_running:
        return V4CheckpointResult(
            "confirmation_required",
            "Confirm through the native runtime or explicit user acknowledgement that the bound "
            "agent is not running. Prewalk did not change state or terminate an agent.",
            state,
        )
    reason = detail.strip() or "native runtime confirmed the prior executor is not running"
    incomplete = apply_v4_transition(
        store_file,
        root_session_id,
        expected_phases=[state.phase],
        target_phase="incomplete",
        event_id=_v4_content_event_id(
            "route-reconciled", root_session_id, state.route_attempt, state.executor_agent_id, reason
        ),
        updates={"last_error": reason},
    )
    return V4CheckpointResult(
        "incomplete",
        "Prewalk retained the checkpoint and marked the prior route incomplete; run pw-retry.",
        incomplete,
    )


# --- Status rendering -----------------------------------------------------------


def _v4_command(host: str, name: str) -> str:
    """Render a skill reference in the host's own syntax ($prewalk vs /prewalk)."""
    return f"/prewalk:{name}" if host == "claude" else f"$prewalk:{name}"


def _short_status_text(value: str, limit: int = 180) -> str:
    """Collapse whitespace and clamp to a terminal-friendly width."""
    compact = " ".join((value or "").split())
    return compact if len(compact) <= limit else compact[: limit - 3] + "..."


def format_v4_status(loaded, *, host: str = "codex") -> str:
    """Format one safe operational view without exposing packet or route token."""
    state = loaded.state
    if state is None:
        next_name = loaded.next_command or "prewalk"
        message = loaded.message or "No armed run exists for this root session."
        return (
            "prewalk v4: idle\n"
            f"  state: {loaded.status}; detail: {_short_status_text(message)}\n"
            f"  next: {_v4_command(host, next_name)}"
        )

    token_summary = (
        "sha256:" + hashlib.sha256(state.route_token.encode("utf-8")).hexdigest()[:10]
        if state.route_token else "none"
    )
    if state.verification_evidence:
        evidence = f"verified ({len(state.verification_evidence)} item(s))"
    elif state.verification_warning:
        evidence = "warning: " + _short_status_text(state.verification_warning)
    else:
        evidence = "not captured"
    remaining = [todo for todo in state.todos if todo.open]
    remaining_text = "; ".join(
        f"{todo.id or index + 1}:{_short_status_text(todo.content, 80)}"
        for index, todo in enumerate(remaining)
    ) or "none"
    next_name = {
        "planning": "pw-status",
        "checkpoint_ready": "pw-go",
        "handoff_requested": "pw-go" if not state.route_tool_use_id else "pw-status",
        "executor_running": "pw-status",
        "incomplete": "pw-retry",
        "stale": "pw-reconcile",
    }[state.phase]
    actions = {
        "planning": "continue task 1 and root Stop; disarm=pw-off",
        "checkpoint_ready": "route=pw-go; revise=pw-revise; disarm=pw-off",
        "handoff_requested": "reuse pending route; reconcile only after interruption; disarm=pw-off",
        "executor_running": "wait; reconcile only after proving agent stopped; disarm does not stop it",
        "incomplete": "retry=pw-retry; revise=pw-revise; disarm=pw-off",
        "stale": "reconcile=pw-reconcile after liveness proof; disarm does not stop it",
    }[state.phase]
    return (
        f"prewalk v4: {state.phase} [{state.preset}]\n"
        f"  host: {state.host}; workspace: {state.workspace_id}\n"
        f"  executor: model={state.executor_model or 'none'}; effort="
        f"{state.executor_effort or 'host-default'}; handoff={state.handoff_mode}; "
        f"routing_proven={'yes' if state.model_routing_proven else 'no'}\n"
        f"  evidence: {evidence}\n"
        f"  route: attempt={state.route_attempt}; token={token_summary}; task="
        f"{'set' if state.route_task_name else 'none'}; tool={state.route_tool_use_id or 'none'}; "
        f"launch_ack={'yes' if state.launch_acknowledged else 'no'}\n"
        f"  bound_agent: {state.executor_agent_id or 'none'}\n"
        f"  timestamps: created={state.created_at}; checkpoint={state.checkpoint_at or 'none'}; "
        f"route={state.route_requested_at or 'none'}; executor={state.executor_started_at or 'none'}; "
        f"last_event={state.last_event_at}\n"
        f"  remaining({len(remaining)}): {remaining_text}\n"
        f"  last_error: {_short_status_text(state.last_error) or 'none'}\n"
        f"  actions: {actions}\n"
        f"  next: {_v4_command(state.host, next_name)}"
    )


def describe(store_file: str | os.PathLike[str], session_id: str) -> str:
    """Render the status of one root session (v4 view, legacy-free)."""
    loaded = load_v4_state(store_file, session_id)
    host = loaded.state.host if loaded.state is not None else "codex"
    return format_v4_status(loaded, host=host)


def disarm(store_file: str | os.PathLike[str], session_id: str) -> str:
    """Clear this session's record; touch nothing else."""
    if not has_record(store_file, session_id):
        return "prewalk was not armed for this session."
    clear_state(store_file, session_id)
    return (
        "prewalk disarmed. State was cleared explicitly; no agent was stopped and "
        "the workspace, todos, and active root model were unchanged."
    )
