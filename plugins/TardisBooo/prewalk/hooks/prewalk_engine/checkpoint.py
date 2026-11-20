"""Checkpoint capture: turning one root Stop into a durable handoff.

The root ``Stop`` event is the only place where ``planning`` may become
``checkpoint_ready``. :func:`capture_v4_checkpoint` decides that question in
one pass:

* missing packets retain the planning run; absence of a plan is not proof
  of completion. Nearly-done plans (0/1 items left) finish in the root;
* todo-shape violations and missing packet headings are *rejections*: the
  caller counts them (:func:`note_v4_checkpoint_reject`) and blocks the Stop
  so the planner can repair its checkpoint in the same turn;
* an accepted Stop persists the **exact** assistant message, the normalized
  todos, and the evidence parsed from the packet — recovery never re-reads
  the transcript, so compaction cannot corrupt a run.

The two counters at the bottom enforce the planner's *budget* in edits:
:func:`note_v4_planner_mutation` nudges a frontier model that keeps editing
after its phase should have ended, escalating to a hard wrap-up demand.
"""

from __future__ import annotations

import os
import re
from dataclasses import asdict

from .prompts import HANDOFF_NOTE, NO_HANDOFF_NEEDED, ONE_LEFT_HINT
from .protocol import (
    Todo,
    V4_CHECKPOINT_RETRY_LIMIT,
    V4_PACKET_HEADINGS,
    V4_PLANNER_MUTATION_LIMIT,
    V4_PLANNER_NUDGE_AT,
    count_remaining,
    missing_packet_headings,
    validate_todo_list,
)
from .records import (
    V4CheckpointResult,
    V4StateError,
    _v4_content_event_id,
    apply_v4_transition,
    load_v4_state,
)
from .store import clear_state, utc_timestamp


def _packet_section(packet: str, heading: str) -> str:
    """Extract one heading's raw text from a packet (empty string if absent)."""
    heading_names = "|".join(re.escape(item) for item in V4_PACKET_HEADINGS)
    match = re.search(
        rf"(?mis)^\s*(?:#{{1,6}}\s*)?{re.escape(heading)}\s*:?\s*(.*?)"
        rf"(?=^\s*(?:#{{1,6}}\s*)?(?:{heading_names})\s*:?(?:\s|$)|\Z)",
        packet,
    )
    return match.group(1).strip() if match else ""


_PACKET_TODO_RE = re.compile(
    r"^\s*(?:(\d+)[.)]|[-*+])\s+\[([ xX])\]\s+(.+?)\s*$"
)


def packet_todos(packet: str) -> list[Todo]:
    """Parse a strict Markdown checklist from the packet's todo section.

    Newer Codex surfaces do not always expose a dedicated plan/todo tool to
    hooks. In that case the exact Stop packet is the only durable todo
    snapshot available. Accept only a section made entirely of numbered or
    bulleted Markdown checkboxes; any prose or malformed line fails closed.
    The normal todo validator still enforces IDs, verification criteria,
    statuses, caps, and the completed-first-task invariant.
    """
    section = _packet_section(packet, "Full Todo List")
    lines = [line for line in section.splitlines() if line.strip()]
    if not lines:
        return []
    todos: list[Todo] = []
    for index, line in enumerate(lines, 1):
        match = _PACKET_TODO_RE.match(line)
        if not match:
            return []
        item_id, checked, content = match.groups()
        todos.append(Todo(
            id=item_id or str(index),
            content=content,
            status="completed" if checked.lower() == "x" else "pending",
        ))
    return todos


# Phrases in the verification section that mean "I could not verify" — the
# packet then records an explicit warning instead of fabricated evidence.
_VERIFICATION_WARNING_RE = re.compile(
    r"\b(?:warning|not run|not available|unavailable|unable to|could not|no (?:test|check|verification))\b",
    re.I,
)


def packet_verification(packet: str) -> tuple[list[str], str]:
    """Return exact verification evidence, or an explicit warning, from a packet.

    Exactly one of the two return values is non-empty: a warning phrase in the
    "Verification Already Run" section demotes the whole section to a warning,
    and a warning is never upgraded into evidence.
    """
    section = _packet_section(packet, "Verification Already Run")
    if not section:
        return [], ""
    if _VERIFICATION_WARNING_RE.search(section):
        return [], section
    evidence = [line.strip(" -*\t") for line in section.splitlines() if line.strip(" -*\t")]
    return evidence, ""


def record_v4_todos(
    store_file: str | os.PathLike[str],
    root_session_id: str,
    todos: list[Todo],
    *,
    event_id: str = "",
) -> V4CheckpointResult:
    """Persist a complete real-work snapshot without creating a checkpoint.

    Runs only during ``planning``; later phases keep the checkpoint snapshot
    that already exists. An unchanged snapshot replays as the same
    content-derived event id, so repeated todo updates are idempotent.
    """
    loaded = load_v4_state(store_file, root_session_id)
    if loaded.state is None or loaded.state.phase != "planning":
        return V4CheckpointResult(loaded.status, loaded.message, loaded.state)
    if any(todo.is_pause for todo in todos):
        return V4CheckpointResult(
            "invalid_todos", "Prewalk v4 plans contain real work only; remove the PAUSE todo."
        )
    error = validate_todo_list(todos, loaded.state.max_todos)
    if error:
        return V4CheckpointResult("invalid_todos", error)
    transition_id = event_id.strip() or _v4_content_event_id(
        "todos", root_session_id, [asdict(todo) for todo in todos]
    )
    state = apply_v4_transition(
        store_file,
        root_session_id,
        expected_phases=["planning"],
        target_phase="planning",
        event_id=transition_id,
        updates={"todos": todos},
    )
    return V4CheckpointResult("recorded", "Prewalk recorded the real todo snapshot.", state)


def capture_v4_checkpoint(
    store_file: str | os.PathLike[str],
    root_session_id: str,
    *,
    packet: str,
    todos: list[Todo] | None = None,
    event_id: str = "",
    now: str | None = None,
) -> V4CheckpointResult:
    """Validate one root Stop event and durably capture its exact assistant packet.

    Statuses the adapter should treat as *rejections* (block the Stop, let the
    planner repair): ``missing_todos`` (packet started but no snapshot),
    ``invalid_todos``, ``incomplete_task_one``, ``invalid_packet``,
    ``missing_evidence``. ``awaiting_packet`` preserves the run without
    blocking Stop. ``complete`` and ``one_remaining`` finish in the root.
    Success is ``checkpoint_ready``.
    """
    loaded = load_v4_state(store_file, root_session_id)
    state = loaded.state
    if state is None:
        return V4CheckpointResult(loaded.status, loaded.message)
    if state.phase == "checkpoint_ready":
        return V4CheckpointResult("checkpoint_ready", "Prewalk checkpoint is already ready.", state)
    if state.phase != "planning":
        return V4CheckpointResult(
            "not_planning", f"Prewalk cannot capture a checkpoint from {state.phase}.", state
        )

    snapshot = list(todos) if todos else list(state.todos)
    if not snapshot:
        snapshot = packet_todos(packet)
    if not snapshot:
        # A malformed packet is rejected. An ordinary reply (including a
        # failed pw-go response) is not evidence that work is complete.
        if packet.strip() and len(missing_packet_headings(packet)) < len(V4_PACKET_HEADINGS):
            return V4CheckpointResult(
                "missing_todos",
                "Prewalk cannot capture a handoff packet without a complete real todo snapshot.",
            )
        return V4CheckpointResult(
            "awaiting_packet",
            "Prewalk planning state retained: no checkpoint packet was supplied. "
            "Emit the structured handoff packet, or use pw-off to explicitly end the run.",
            state,
        )
    if any(todo.is_pause for todo in snapshot):
        return V4CheckpointResult(
            "invalid_todos", "Prewalk v4 plans contain real work only; remove the PAUSE todo."
        )
    error = validate_todo_list(snapshot, state.max_todos)
    if error:
        return V4CheckpointResult("invalid_todos", error)
    if snapshot[0].status != "completed":
        return V4CheckpointResult(
            "incomplete_task_one", "Prewalk task #1 must be completed before checkpoint capture."
        )
    remaining = count_remaining(snapshot)
    if remaining == 0:
        clear_state(store_file, root_session_id)
        return V4CheckpointResult("complete", NO_HANDOFF_NEEDED)
    if remaining == 1 and state.host != "codex":
        clear_state(store_file, root_session_id)
        return V4CheckpointResult("one_remaining", ONE_LEFT_HINT)

    missing = missing_packet_headings(packet)
    if missing:
        return V4CheckpointResult(
            "invalid_packet", "Prewalk checkpoint packet is missing headings: " + ", ".join(missing)
        )
    evidence, warning = packet_verification(packet)
    if not evidence and not warning:
        return V4CheckpointResult(
            "missing_evidence",
            "Prewalk checkpoint requires verification evidence or an explicit verification warning.",
        )
    timestamp = now or utc_timestamp()
    transition_id = event_id.strip() or _v4_content_event_id(
        "root-stop", root_session_id, [asdict(todo) for todo in snapshot], packet
    )
    try:
        checkpoint = apply_v4_transition(
            store_file,
            root_session_id,
            expected_phases=["planning"],
            target_phase="checkpoint_ready",
            event_id=transition_id,
            now=timestamp,
            updates={
                "todos": snapshot,
                "packet": packet,
                "verification_evidence": evidence,
                "verification_warning": warning,
                "checkpoint_at": timestamp,
                "last_error": "",
            },
        )
    except V4StateError as exc:
        return V4CheckpointResult("invalid_checkpoint", str(exc))
    return V4CheckpointResult(
        "checkpoint_ready",
        "prewalk: checkpoint ready; run `pw-go` to hand off or `pw-revise` to revise.",
        checkpoint,
    )


def note_v4_checkpoint_reject(
    store_file: str | os.PathLike[str], root_session_id: str, *, reason: str
) -> tuple[int, bool]:
    """Count one rejected Stop checkpoint; return (count, model_should_retry).

    A rejected checkpoint stays recoverable only while the planner is still
    the active phase. The adapter blocks the Stop with the reason so the model
    can emit a corrected packet instead of dying silently; after
    :data:`V4_CHECKPOINT_RETRY_LIMIT` rejections the caller stops blocking and
    leaves the verdict to the human.
    """
    loaded = load_v4_state(store_file, root_session_id)
    state = loaded.state
    if state is None or state.phase != "planning":
        return 0, False
    counted = apply_v4_transition(
        store_file,
        root_session_id,
        expected_phases=["planning"],
        target_phase="planning",
        event_id=_v4_content_event_id(
            "checkpoint-reject", root_session_id, state.checkpoint_rejects + 1, reason
        ),
        updates={"checkpoint_rejects": state.checkpoint_rejects + 1, "last_error": reason},
    )
    return counted.checkpoint_rejects, counted.checkpoint_rejects < V4_CHECKPOINT_RETRY_LIMIT


def note_v4_planner_mutation(
    store_file: str | os.PathLike[str], root_session_id: str
) -> tuple[int, str]:
    """Count one planner file mutation; return (count, nudge_text_or_empty).

    The frontier budget is expressed as edits, not turns: a planner still
    mutating files after the first verified task is off-protocol and gets an
    escalating nudge to wrap up and stop with the checkpoint packet.
    """
    loaded = load_v4_state(store_file, root_session_id)
    state = loaded.state
    if state is None or state.phase != "planning":
        return 0, ""
    counted = apply_v4_transition(
        store_file,
        root_session_id,
        expected_phases=["planning"],
        target_phase="planning",
        event_id=_v4_content_event_id(
            "planner-mutation", root_session_id, state.planner_mutations + 1
        ),
        updates={"planner_mutations": state.planner_mutations + 1},
    )
    count = counted.planner_mutations
    if count == V4_PLANNER_NUDGE_AT[0]:
        nudge = (
            "Prewalk budget note: you are deep into phase 1. Finish verifying task #1, "
            "then stop with the structured Handoff Packet — do not start task #2."
        )
    elif count >= V4_PLANNER_MUTATION_LIMIT:
        nudge = (
            "Prewalk budget limit reached: stop making further edits. Write the final "
            "structured Handoff Packet now and stop; the executor continues from the todo list."
        )
    else:
        nudge = ""
    return count, nudge


def v4_handoff_context(
    store_file: str | os.PathLike[str], root_session_id: str
) -> V4CheckpointResult:
    """Load the durable packet used by host-specific routing after resume."""
    loaded = load_v4_state(store_file, root_session_id)
    state = loaded.state
    if state is None:
        return V4CheckpointResult(loaded.status, loaded.message)
    if state.phase != "checkpoint_ready":
        return V4CheckpointResult(
            "not_ready", f"Prewalk has no checkpoint ready for handoff ({state.phase}).", state
        )
    return V4CheckpointResult(
        "checkpoint_ready", f"{HANDOFF_NOTE}\n\n{state.packet}", state
    )


def revise_v4_checkpoint(
    store_file: str | os.PathLike[str], root_session_id: str, revision: str
) -> V4CheckpointResult:
    """Return a durable checkpoint to planning for explicit or Stop replacement.

    Revision wipes the captured packet and every route identity but keeps the
    todo snapshot (task 1 stays done); the frontier re-plans only what the
    revision touches and stops with a fresh packet.
    """
    loaded = load_v4_state(store_file, root_session_id)
    state = loaded.state
    if state is None:
        return V4CheckpointResult(loaded.status, loaded.message)
    if state.phase not in ("checkpoint_ready", "incomplete"):
        return V4CheckpointResult(
            "not_ready", f"Prewalk has no checkpoint ready to revise ({state.phase}).", state
        )
    event_id = _v4_content_event_id(
        "revise", root_session_id, state.revision, revision.strip()
    )
    revised = apply_v4_transition(
        store_file,
        root_session_id,
        expected_phases=["checkpoint_ready", "incomplete"],
        target_phase="planning",
        event_id=event_id,
        updates={
            "packet": "",
            "fast_mode": False if state.host == "codex" else state.fast_mode,
            "plan_seen": False,
            "fast_gate_open": False,
            "verification_evidence": [],
            "verification_warning": "",
            "checkpoint_at": "",
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
    instruction = (
        f"PREWALK REVISION: update the plan accordingly: {revision.strip() or '(no detail given)'}. "
        "Re-explore only what the revision affects, update only real work in the todo list, "
        "re-verify task #1 if it changed, then stop with a replacement structured Handoff Packet."
    )
    return V4CheckpointResult("planning", instruction, revised)
