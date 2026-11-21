"""Token-bound handoff routes for both hosts.

A *route* is one handoff attempt's worth of secret identity: a one-time
token, a deterministic task name, at most one tool-use id, and at most one
bound agent id. The functions here are the only writers of that identity, and
every one of them follows the same discipline:

* **Token first.** Nothing routes until :func:`request_claude_handoff` or
  :func:`request_codex_handoff` has proven the host's capability and minted a
  fresh ``secrets.token_urlsafe`` token.
* **Exact-match only.** A hook event advances the route when its identities
  match the record *exactly*; foreign, nested, parallel, and replayed events
  are no-ops. Reusing a spent token is denied, not ignored.
* **Failure retains the checkpoint.** Every failure path lands in
  ``incomplete`` with the packet intact, so ``pw-retry`` can mint exactly one
  new route without redoing task 1.

The two hosts differ in *mechanism*, which is the whole point of having
adapters: Codex validates the model's own ``spawn_agent`` call (no rewrite
possible), while Claude's PreToolUse hook rewrites the prompt/type/model of
one token-bearing Agent call via ``updatedInput``.
"""

from __future__ import annotations

import re
import secrets
from typing import Any, Iterable

from .capabilities import evaluate_capabilities, format_capability_report
from .presets import Preset
from .prompts import FORK_HANDOFF_NOTE, HANDOFF_NOTE
from .records import (
    V4CheckpointResult,
    V4RouteDecision,
    V4State,
    _v4_content_event_id,
    apply_v4_transition,
    load_v4_state,
)
from .store import clear_state, utc_timestamp


def _safe_task_suffix(token: str) -> str:
    """Return a stable Codex task-name fragment accepted by strict schemas."""
    return re.sub(r"[^a-z0-9_]", "_", token.lower())[:8]

CODEX_EXECUTOR_INSTRUCTIONS = (
    "Continue only the remaining todos from the persisted packet. Do not repeat task #1 or restart "
    "planning. Mark one todo in progress at a time, run its stated verification, and finish with "
    "exactly PREWALK_COMPLETE when all work is verified, or PREWALK_INCOMPLETE: <reason>."
)

CLAUDE_EXECUTOR_INSTRUCTIONS = CODEX_EXECUTOR_INSTRUCTIONS

#: The plugin-scoped subagent name the Claude router rewrites calls into,
#: plus its unscoped twin (loose installs cannot namespace).
CLAUDE_EXECUTOR_AGENT = "prewalk:prewalk-executor"
CLAUDE_EXECUTOR_LIFECYCLE_TYPES = {CLAUDE_EXECUTOR_AGENT, "prewalk-executor"}


def claude_route_message(state: V4State) -> str:
    """The canonical fresh-context prompt installed by Claude's hook."""
    return (
        f"PREWALK_HANDOFF_TOKEN: {state.route_token}\n\n"
        f"{HANDOFF_NOTE}\n\n{state.packet}\n\n## Executor Contract\n"
        f"{CLAUDE_EXECUTOR_INSTRUCTIONS}"
    )


def claude_route_instruction(state: V4State) -> str:
    """Tell the root model how to make the one token-bearing Agent call."""
    return (
        "spawn ONE Task/Agent now. Use the complete text between "
        "PREWALK_MESSAGE_BEGIN and PREWALK_MESSAGE_END as its prompt. Do not set or "
        "change the subagent type or model; the PreToolUse hook owns both.\n"
        f"PREWALK_TASK_NAME: {state.route_task_name}\n"
        "PREWALK_MESSAGE_BEGIN\n"
        f"{claude_route_message(state)}\n"
        "PREWALK_MESSAGE_END"
    )


def request_claude_handoff(
    store_file: str | os.PathLike[str],
    root_session_id: str,
    *,
    environment: dict[str, str] | None = None,
) -> V4CheckpointResult:
    """Create one token-bound Claude route after proving hook model routing.

    Re-asking while a route is pending replays the same instruction (the
    token is not re-minted), so a flaky terminal or a repeated slash command
    cannot orphan a route.
    """
    loaded = load_v4_state(store_file, root_session_id)
    state = loaded.state
    if state is None:
        return V4CheckpointResult(loaded.status, loaded.message)
    if state.phase == "handoff_requested":
        return V4CheckpointResult(
            "handoff_requested", claude_route_instruction(state), state
        )
    if state.phase != "checkpoint_ready":
        return V4CheckpointResult(
            "not_ready", f"Prewalk has no checkpoint ready for Claude routing ({state.phase}).", state
        )
    preset = Preset(
        state.preset,
        state.executor_model,
        executor_effort=state.executor_effort,
        require_model_routing=state.require_model_routing,
    )
    capability = evaluate_capabilities(
        preset, "claude", environment=environment or {}
    )
    if not capability.routing_allowed:
        return V4CheckpointResult(
            "unsupported_route",
            format_capability_report(capability)
            + "\nPrewalk retained the checkpoint; do not spawn an unpinned executor.",
            state,
        )

    token = secrets.token_urlsafe(24)
    attempt = state.route_attempt + 1
    timestamp = utc_timestamp()
    requested = apply_v4_transition(
        store_file,
        root_session_id,
        expected_phases=["checkpoint_ready"],
        target_phase="handoff_requested",
        event_id=f"claude-route:{root_session_id}:{token}",
        now=timestamp,
        updates={
            "route_token": token,
            "route_task_name": f"prewalk_executor_{attempt}_{_safe_task_suffix(token)}",
            "route_attempt": attempt,
            "route_requested_at": timestamp,
            "model_routing_proven": True,
            "effort_routing_proven": False,
            "route_tool_use_id": "",
            "executor_agent_id": "",
            "executor_started_at": "",
            "launch_acknowledged": False,
            "last_error": "",
        },
    )
    return V4CheckpointResult(
        "handoff_requested", claude_route_instruction(requested), requested
    )


def codex_route_message(state: V4State) -> str:
    """The one canonical executor instruction for the Codex route.

    ``fork_turns="all"``: the executor inherits the planner's whole
    trajectory, so the message is a short phase-2 note — the packet is not
    repeated. ``fork_turns="none"``: a fresh-context executor gets the full
    packet as before.
    """
    return (
        f"PREWALK_ROUTE_TOKEN: {state.route_token}\n\n"
        f"{HANDOFF_NOTE}\n\n{state.packet}\n\n## Executor Contract\n"
        f"{CODEX_EXECUTOR_INSTRUCTIONS}"
    )


def request_codex_handoff(
    store_file: str | os.PathLike[str],
    root_session_id: str,
    *,
    schema_fields: Iterable[str],
) -> V4CheckpointResult:
    """Create one token-bound Codex route after checking the live tool schema.

    The schema field names are the *only* accepted proof of model routing;
    presets and documentation do not count. A manual-model preset never
    routes through the spawn path at all.
    """
    loaded = load_v4_state(store_file, root_session_id)
    state = loaded.state
    if state is None:
        return V4CheckpointResult(loaded.status, loaded.message)
    if state.phase == "handoff_requested":
        return V4CheckpointResult(
            "handoff_requested", codex_route_message(state), state
        )
    if state.phase != "checkpoint_ready":
        return V4CheckpointResult(
            "not_ready", f"Prewalk has no checkpoint ready for Codex routing ({state.phase})."
            + (f" Last checkpoint error: {state.last_error}" if state.last_error else ""), state
        )
    if state.handoff_mode == "manual-model":
        return V4CheckpointResult(
            "manual_required",
            "This preset requires an explicit manual model switch. The checkpoint remains durable; "
            "switch to the executor model and run pw-resume.",
            state,
        )
    fields = set(schema_fields)
    preset = Preset(
        state.preset,
        state.executor_model,
        executor_effort=state.executor_effort,
        require_model_routing=state.require_model_routing,
    )
    capability = evaluate_capabilities(preset, "codex", schema_fields=fields)
    if not capability.routing_allowed:
        return V4CheckpointResult(
            "unsupported_route",
            format_capability_report(capability)
            + "\nPrewalk retained the checkpoint; do not spawn an unpinned executor.",
            state,
        )
    legacy_schema = {"task_name", "message", "fork_turns"}.issubset(fields)
    fork_context_schema = {"message", "fork_context"}.issubset(fields)
    if not legacy_schema and not fork_context_schema:
        return V4CheckpointResult(
            "unsupported_route",
            "The live spawn_agent schema must expose message plus either "
            "task_name/fork_turns or fork_context.",
            state,
        )

    token = secrets.token_urlsafe(24)
    attempt = state.route_attempt + 1
    task_name = f"prewalk_executor_{attempt}_{_safe_task_suffix(token)}"
    timestamp = utc_timestamp()
    requested = apply_v4_transition(
        store_file,
        root_session_id,
        expected_phases=["checkpoint_ready"],
        target_phase="handoff_requested",
        event_id=f"codex-route:{root_session_id}:{token}",
        now=timestamp,
        updates={
            "route_token": token,
            "route_task_name": task_name,
            "route_attempt": attempt,
            "route_requested_at": timestamp,
            "model_routing_proven": "model" in fields,
            "effort_routing_proven": bool(
                state.executor_effort and "reasoning_effort" in fields
            ),
            "route_tool_use_id": "",
            "executor_agent_id": "",
            "executor_started_at": "",
            "launch_acknowledged": False,
            "last_error": "",
        },
    )
    return V4CheckpointResult(
        "handoff_requested", codex_route_message(requested), requested
    )


def resume_codex_manual(
    store_file: str | os.PathLike[str], root_session_id: str
) -> V4CheckpointResult:
    """Explicit compatibility route after the user manually changes the root model.

    The root thread itself becomes the executor under a synthetic
    ``manual-root:<session>`` agent id; :func:`finish_codex_manual` is the
    only legal way to close it.
    """
    loaded = load_v4_state(store_file, root_session_id)
    state = loaded.state
    if state is None:
        return V4CheckpointResult(loaded.status, loaded.message)
    if state.phase != "checkpoint_ready":
        return V4CheckpointResult(
            "not_ready", f"Prewalk has no checkpoint ready for manual resume ({state.phase}).", state
        )
    token = secrets.token_urlsafe(24)
    timestamp = utc_timestamp()
    running = apply_v4_transition(
        store_file,
        root_session_id,
        expected_phases=["checkpoint_ready"],
        target_phase="executor_running",
        event_id=f"codex-manual-resume:{root_session_id}:{token}",
        now=timestamp,
        updates={
            "route_token": token,
            "route_task_name": f"manual_root_{_safe_task_suffix(token)}",
            "route_attempt": state.route_attempt + 1,
            "route_requested_at": timestamp,
            "executor_agent_id": f"manual-root:{root_session_id}",
            "executor_started_at": timestamp,
            "launch_acknowledged": True,
            "last_error": "",
        },
    )
    return V4CheckpointResult(
        "executor_running",
        f"{HANDOFF_NOTE}\n\n{running.packet}\n\n## Executor Contract\n"
        f"{CODEX_EXECUTOR_INSTRUCTIONS}\n\n"
        "This is the explicit manual-root fallback. Run pw-complete or pw-incomplete when finished.",
        running,
    )


def finish_codex_manual(
    store_file: str | os.PathLike[str],
    root_session_id: str,
    *,
    complete: bool,
    detail: str = "",
) -> V4CheckpointResult:
    """Close an explicit manual-root run started by :func:`resume_codex_manual`."""
    loaded = load_v4_state(store_file, root_session_id)
    state = loaded.state
    if (
        state is None
        or state.phase != "executor_running"
        or state.executor_agent_id != f"manual-root:{root_session_id}"
    ):
        return V4CheckpointResult(
            "not_manual", "No explicit manual-root Prewalk executor is active.", state
        )
    if complete:
        clear_state(store_file, root_session_id)
        return V4CheckpointResult("complete", "prewalk: manual executor completed all work.")
    reason = detail.strip() or "manual executor stopped with work remaining"
    incomplete = apply_v4_transition(
        store_file,
        root_session_id,
        expected_phases=["executor_running"],
        target_phase="incomplete",
        event_id=_v4_content_event_id("codex-manual-incomplete", root_session_id, reason),
        updates={"last_error": reason},
    )
    return V4CheckpointResult("incomplete", reason, incomplete)


# --- Shared route helpers -----------------------------------------------------


def _claude_agent_intended(state: V4State, tool_input: dict[str, Any]) -> bool:
    """The prompt carries the route token as its own exact line."""
    prompt = str(tool_input.get("prompt") or tool_input.get("description") or "")
    return bool(
        state.route_token
        and f"PREWALK_HANDOFF_TOKEN: {state.route_token}" in prompt.splitlines()
    )


def _codex_spawn_intended(state: V4State, tool_input: dict[str, Any]) -> bool:
    """The spawn names this route's task or carries its token."""
    task_name = str(tool_input.get("task_name") or "")
    message = str(tool_input.get("message") or "")
    return (
        task_name == state.route_task_name
        or state.route_token in task_name
        or state.route_token in message
    )


def _fail_v4_route(
    store_file: str | os.PathLike[str],
    root_session_id: str,
    state: V4State,
    *,
    reason: str,
    event_id: str,
) -> V4RouteDecision:
    """Move a route to ``incomplete``, retaining its checkpoint for retry."""
    failed = apply_v4_transition(
        store_file,
        root_session_id,
        expected_phases=[state.phase],
        target_phase="incomplete",
        event_id=event_id,
        updates={"last_error": reason.strip() or "executor route failed"},
    )
    return V4RouteDecision(True, False, failed.last_error, failed)


# --- Claude route lifecycle -----------------------------------------------------


def validate_claude_agent_call(
    store_file: str | os.PathLike[str],
    root_session_id: str,
    tool_input: dict[str, Any],
    *,
    tool_use_id: str,
    environment: dict[str, str] | None = None,
) -> V4RouteDecision:
    """Rewrite only the token-bearing root Agent call and persist its tool id.

    Unrelated Agent calls pass through untouched. A token-bearing call that
    arrives in the wrong phase is *denied* (the token is single-use); a call
    without a tool-use id fails the route, because the router could never
    match its result events later.
    """
    loaded = load_v4_state(store_file, root_session_id)
    state = loaded.state
    if state is None:
        return V4RouteDecision(False, True, state=state)
    if state.phase != "handoff_requested":
        if state.route_token and _claude_agent_intended(state, tool_input):
            return V4RouteDecision(
                True, False, f"Prewalk route is {state.phase}; do not reuse its token.", state
            )
        return V4RouteDecision(False, True, state=state)
    if not _claude_agent_intended(state, tool_input):
        return V4RouteDecision(False, True, state=state)
    if state.route_tool_use_id:
        if tool_use_id == state.route_tool_use_id:
            updated = dict(tool_input)
            updated.update(
                prompt=claude_route_message(state),
                subagent_type=CLAUDE_EXECUTOR_AGENT,
                model=state.executor_model,
            )
            return V4RouteDecision(
                True, True, "Prewalk Agent route was already accepted.", state, updated
            )
        return V4RouteDecision(
            True, False, "The pending Prewalk route is already claimed by another Agent call.", state
        )
    if not tool_use_id.strip():
        return _fail_v4_route(
            store_file,
            root_session_id,
            state,
            reason="Prewalk cannot safely route an Agent call without tool_use_id.",
            event_id=_v4_content_event_id("claude-agent-no-tool-id", root_session_id, tool_input),
        )
    preset = Preset(
        state.preset,
        state.executor_model,
        executor_effort=state.executor_effort,
        require_model_routing=state.require_model_routing,
    )
    capability = evaluate_capabilities(
        preset, "claude", environment=environment or {}
    )
    if not capability.routing_allowed:
        reason = format_capability_report(capability)
        return _fail_v4_route(
            store_file,
            root_session_id,
            state,
            reason=reason,
            event_id=f"claude-agent-route-conflict:{tool_use_id}",
        )

    updated = dict(tool_input)
    updated.update(
        prompt=claude_route_message(state),
        subagent_type=CLAUDE_EXECUTOR_AGENT,
        model=state.executor_model,
    )
    accepted = apply_v4_transition(
        store_file,
        root_session_id,
        expected_phases=["handoff_requested"],
        target_phase="handoff_requested",
        event_id=f"claude-agent-pre:{tool_use_id}",
        updates={"route_tool_use_id": tool_use_id},
    )
    return V4RouteDecision(
        True, True, "Prewalk routed the exact token-bearing Agent call.", accepted, updated
    )


def bind_claude_executor(
    store_file: str | os.PathLike[str],
    root_session_id: str,
    *,
    agent_id: str,
    agent_type: str,
) -> V4RouteDecision:
    """Bind the first exact scoped SubagentStart after the accepted Agent call."""
    loaded = load_v4_state(store_file, root_session_id)
    state = loaded.state
    if state is None or agent_type not in CLAUDE_EXECUTOR_LIFECYCLE_TYPES:
        return V4RouteDecision(False, True, state=state)
    if state.phase == "executor_running" and agent_id == state.executor_agent_id:
        return V4RouteDecision(True, True, "Prewalk executor was already bound.", state)
    if state.phase != "handoff_requested" or not state.route_tool_use_id:
        return V4RouteDecision(False, True, state=state)
    if not agent_id.strip():
        return _fail_v4_route(
            store_file,
            root_session_id,
            state,
            reason="SubagentStart did not provide an executor agent identity.",
            event_id=f"claude-subagent-start-missing:{state.route_tool_use_id}",
        )
    timestamp = utc_timestamp()
    running = apply_v4_transition(
        store_file,
        root_session_id,
        expected_phases=["handoff_requested"],
        target_phase="executor_running",
        event_id=f"claude-subagent-start:{state.route_tool_use_id}:{agent_id}",
        now=timestamp,
        updates={"executor_agent_id": agent_id, "executor_started_at": timestamp},
    )
    return V4RouteDecision(True, True, f"Prewalk bound executor {agent_id}.", running)


def acknowledge_claude_agent_call(
    store_file: str | os.PathLike[str],
    root_session_id: str,
    *,
    tool_use_id: str,
) -> V4RouteDecision:
    """Record Agent PostToolUse as launch acknowledgement, never completion.

    A successful Task tool result only proves the agent *started*; the run's
    result stays owned by the bound executor's SubagentStop marker.
    """
    loaded = load_v4_state(store_file, root_session_id)
    state = loaded.state
    if (
        state is None
        or state.phase not in ("handoff_requested", "executor_running")
        or not tool_use_id
        or tool_use_id != state.route_tool_use_id
    ):
        return V4RouteDecision(False, True, state=state)
    if state.launch_acknowledged:
        return V4RouteDecision(True, True, "Prewalk launch was already acknowledged.", state)
    acknowledged = apply_v4_transition(
        store_file,
        root_session_id,
        expected_phases=[state.phase],
        target_phase=state.phase,
        event_id=f"claude-agent-post:{tool_use_id}",
        updates={"launch_acknowledged": True},
    )
    return V4RouteDecision(
        True, True, "prewalk: Agent launch acknowledged; waiting for bound SubagentStop.", acknowledged
    )


def fail_claude_agent_call(
    store_file: str | os.PathLike[str],
    root_session_id: str,
    *,
    tool_use_id: str,
    reason: str,
) -> V4RouteDecision:
    """Retain a retryable checkpoint after exact Agent denial or launch failure."""
    loaded = load_v4_state(store_file, root_session_id)
    state = loaded.state
    if (
        state is None
        or state.phase not in ("handoff_requested", "executor_running")
        or not tool_use_id
        or tool_use_id != state.route_tool_use_id
    ):
        return V4RouteDecision(False, True, state=state)
    normalized = reason.strip() or "executor Agent failed or was rejected"
    return _fail_v4_route(
        store_file,
        root_session_id,
        state,
        reason=normalized,
        event_id=_v4_content_event_id("claude-agent-failed", root_session_id, tool_use_id, normalized),
    )


# --- Codex route lifecycle -----------------------------------------------------


def validate_codex_spawn(
    store_file: str | os.PathLike[str],
    root_session_id: str,
    tool_input: dict[str, Any],
    *,
    tool_use_id: str,
) -> V4RouteDecision:
    """Validate and bind the exact pending Codex spawn request before execution.

    Codex hooks cannot rewrite a tool call, so validation is strict: the task
    name, the message, ``fork_turns``, the model, and (when proven) the
    effort must match the minted route character for character. Any mismatch
    denies the spawn and marks the route ``incomplete`` for ``pw-retry``.
    """
    loaded = load_v4_state(store_file, root_session_id)
    state = loaded.state
    if state is None:
        return V4RouteDecision(False, True, state=state)
    if state.phase != "handoff_requested":
        if state.route_token and _codex_spawn_intended(state, tool_input):
            return V4RouteDecision(
                True,
                False,
                f"Prewalk route is {state.phase}; do not reuse its token or spawn request.",
                state,
            )
        return V4RouteDecision(False, True, state=state)
    if not _codex_spawn_intended(state, tool_input):
        return V4RouteDecision(False, True, state=state)

    errors: list[str] = []
    expected_message = codex_route_message(state)
    if str(tool_input.get("message") or "") != expected_message:
        errors.append("message is not the exact persisted Prewalk route message")
    if "fork_context" in tool_input:
        # Current Codex forbids model/reasoning overrides with full-history
        # forks. A pinned executor receives the durable packet in the message.
        expected_fork_context = False if state.model_routing_proven else state.fork_turns == "all"
        if tool_input.get("fork_context") is not expected_fork_context:
            errors.append(f"fork_context must be {str(expected_fork_context).lower()}")
        if "task_name" in tool_input or "fork_turns" in tool_input:
            errors.append("fork_context schema must not include task_name or fork_turns")
    else:
        if str(tool_input.get("task_name") or "") != state.route_task_name:
            errors.append("task_name does not match the pending Prewalk route")
        # Codex also rejects model/reasoning overrides with a full-history
        # legacy fork. Keep the durable preset unchanged, but route a pinned
        # executor with a fresh context because the complete packet is in the
        # message.
        expected_fork_turns = "none" if state.model_routing_proven else state.fork_turns
        if tool_input.get("fork_turns") != expected_fork_turns:
            errors.append(f'fork_turns must be "{expected_fork_turns}"')
    if state.model_routing_proven and tool_input.get("model") != state.executor_model:
        errors.append("model does not match the configured executor")
    if state.require_model_routing and not state.model_routing_proven:
        errors.append("required executor model routing was not proven")
    if state.effort_routing_proven:
        if tool_input.get("reasoning_effort") != state.executor_effort:
            errors.append("reasoning_effort does not match the configured executor effort")
    elif "reasoning_effort" in tool_input:
        errors.append("reasoning_effort was not exposed by the live schema")
    if not tool_use_id.strip():
        errors.append("spawn hook payload has no tool_use_id")

    if errors:
        timestamp = utc_timestamp()
        failed = apply_v4_transition(
            store_file,
            root_session_id,
            expected_phases=["handoff_requested"],
            target_phase="incomplete",
            event_id=_v4_content_event_id("codex-spawn-denied", root_session_id, errors, tool_input),
            now=timestamp,
            updates={"last_error": "; ".join(errors)},
        )
        return V4RouteDecision(True, False, failed.last_error, failed)

    accepted = apply_v4_transition(
        store_file,
        root_session_id,
        expected_phases=["handoff_requested"],
        target_phase="handoff_requested",
        event_id=f"codex-spawn-pre:{tool_use_id}",
        updates={"route_tool_use_id": tool_use_id},
    )
    return V4RouteDecision(True, True, "Prewalk accepted the exact executor spawn.", accepted)


def bind_codex_executor(
    store_file: str | os.PathLike[str],
    root_session_id: str,
    *,
    tool_use_id: str,
    agent_id: str,
    success: bool,
    detail: str = "",
) -> V4RouteDecision:
    """Bind only the agent returned by the exact accepted spawn tool call."""
    loaded = load_v4_state(store_file, root_session_id)
    state = loaded.state
    if state is None:
        return V4RouteDecision(False, True, state=state)
    if state.phase == "executor_running" and (
        tool_use_id == state.route_tool_use_id and agent_id == state.executor_agent_id
    ):
        return V4RouteDecision(True, True, "Prewalk executor was already bound.", state)
    if state.phase != "handoff_requested":
        return V4RouteDecision(False, True, state=state)
    if not tool_use_id or tool_use_id != state.route_tool_use_id:
        return V4RouteDecision(False, True, state=state)
    timestamp = utc_timestamp()
    if not success or not agent_id.strip():
        error = detail.strip() or "spawn_agent did not return a usable agent identity"
        failed = apply_v4_transition(
            store_file,
            root_session_id,
            expected_phases=["handoff_requested"],
            target_phase="incomplete",
            event_id=f"codex-spawn-post-failed:{tool_use_id}",
            now=timestamp,
            updates={"last_error": error},
        )
        return V4RouteDecision(True, False, error, failed)
    running = apply_v4_transition(
        store_file,
        root_session_id,
        expected_phases=["handoff_requested"],
        target_phase="executor_running",
        event_id=f"codex-spawn-post:{tool_use_id}:{agent_id}",
        now=timestamp,
        updates={
            "executor_agent_id": agent_id,
            "executor_started_at": timestamp,
            "launch_acknowledged": True,
        },
    )
    return V4RouteDecision(True, True, f"Prewalk bound executor {agent_id}.", running)


# --- Shared result handling -----------------------------------------------------


def finish_v4_executor(
    store_file: str | os.PathLike[str],
    root_session_id: str,
    *,
    agent_id: str,
    result: str,
    event_id: str,
) -> V4RouteDecision:
    """Accept a final marker only from the executor identity bound to this root.

    The marker is the last non-empty line of the executor's stop message and
    must be exactly ``PREWALK_COMPLETE`` or ``PREWALK_INCOMPLETE: <reason>``.
    Completion deletes the record; anything else retains the checkpoint.
    """
    loaded = load_v4_state(store_file, root_session_id)
    state = loaded.state
    if state is None:
        return V4RouteDecision(False, True, state=state)
    if state.phase == "incomplete" and agent_id == state.executor_agent_id:
        return V4RouteDecision(True, False, state.last_error, state)
    if state.phase != "executor_running":
        return V4RouteDecision(False, True, state=state)
    if not agent_id or agent_id != state.executor_agent_id:
        return V4RouteDecision(False, True, state=state)
    final_line = next((line.strip() for line in reversed(result.splitlines()) if line.strip()), "")
    if final_line == "PREWALK_COMPLETE":
        clear_state(store_file, root_session_id)
        return V4RouteDecision(True, True, "prewalk: executor completed all work.")
    reason = (
        final_line.partition(":")[2].strip()
        if final_line.startswith("PREWALK_INCOMPLETE:")
        else "bound executor stopped without a valid final marker"
    )
    incomplete = apply_v4_transition(
        store_file,
        root_session_id,
        expected_phases=["executor_running"],
        target_phase="incomplete",
        event_id=event_id or _v4_content_event_id("executor-stop", root_session_id, agent_id, result),
        updates={"last_error": reason or "executor reported incomplete work"},
    )
    return V4RouteDecision(True, False, incomplete.last_error, incomplete)


def interrupt_v4_executor(
    store_file: str | os.PathLike[str],
    root_session_id: str,
    *,
    reason: str,
    event_id: str = "",
) -> V4RouteDecision:
    """Recover a bound route when the host explicitly reports root interruption.

    Anything that is not recognizably an interrupt/cancel/abort report is
    ignored — a generic stop reason must not silently consume a route.
    """
    loaded = load_v4_state(store_file, root_session_id)
    state = loaded.state
    if state is None or state.phase != "executor_running":
        return V4RouteDecision(False, True, state=state)
    normalized = reason.strip()
    if not re.search(r"\b(?:interrupt(?:ed|ion)?|cancel(?:led|ed|ation)?|abort(?:ed)?)\b", normalized, re.I):
        return V4RouteDecision(False, True, state=state)
    incomplete = apply_v4_transition(
        store_file,
        root_session_id,
        expected_phases=["executor_running"],
        target_phase="incomplete",
        event_id=event_id or _v4_content_event_id("codex-interrupted", root_session_id, normalized),
        updates={"last_error": normalized or "executor was interrupted"},
    )
    return V4RouteDecision(True, False, incomplete.last_error, incomplete)
