"""Frozen protocol layer: names, limits, and todo-list rules.

Everything in this module is part of the *contract* between the planner, the
executor, the host adapters, and the on-disk state file:

* phase names are persisted verbatim inside ``prewalk-state.json``;
* packet headings are matched inside assistant messages;
* todo-list rules decide whether a Stop checkpoint is accepted;
* retry limits decide when the adapters stop blocking and start trusting the
  human.

Change any string here and old state files or in-flight sessions will
misinterpret each other — treat additions as the only safe evolution.

The module deliberately has no dependencies outside the standard library (and
no imports from sibling modules), so every other layer can sit on top of it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

# --- Release identity -------------------------------------------------------

VERSION = "1.0.9"

# --- Tuning defaults --------------------------------------------------------

DEFAULT_MAX_TODOS = 12
DEFAULT_PRESET = "code-value"

#: How a preset may ask the host to perform the handoff. ``auto`` lets the
#: router pick the strongest native mechanism, ``spawn`` demands a subagent,
#: and ``manual-model`` is the explicit human-driven fallback.
HANDOFF_MODES = ("auto", "spawn", "manual-model")

# --- Legacy (0.3.x) phase vocabulary ----------------------------------------
#
# The 0.3 event machine is still shipped for compatibility with old installs;
# its records are auto-reset by the v4 loader, but the vocabulary is kept so
# the reset path can recognize what it is discarding.

IDLE = "idle"
FRONTIER = "frontier"
PAUSED = "paused"
READY = "ready"  # first edit observed, checkpoint not yet valid
HANDOFF_REQUESTED = "handoff_requested"
EXECUTOR = "executor"
RESTORING = "restoring"

# --- V4 durable phases ------------------------------------------------------

V4_SCHEMA_VERSION = 4

V4_PLANNING = "planning"
V4_CHECKPOINT_READY = "checkpoint_ready"
V4_HANDOFF_REQUESTED = "handoff_requested"
V4_EXECUTOR_RUNNING = "executor_running"
V4_INCOMPLETE = "incomplete"
V4_STALE = "stale"

#: ``idle`` is *not* a stored phase — it is the absence of a record.
V4_PHASES = {
    V4_PLANNING,
    V4_CHECKPOINT_READY,
    V4_HANDOFF_REQUESTED,
    V4_EXECUTOR_RUNNING,
    V4_INCOMPLETE,
    V4_STALE,
}

#: Every phase that proves a durable checkpoint exists beneath it.
V4_CHECKPOINT_PHASES = V4_PHASES - {V4_PLANNING}

#: Every phase that owns route identity (token / task name / attempt).
V4_ROUTE_PHASES = {
    V4_HANDOFF_REQUESTED,
    V4_EXECUTOR_RUNNING,
    V4_INCOMPLETE,
    V4_STALE,
}

#: The eight packet headings a root Stop message must contain, in order.
V4_PACKET_HEADINGS = (
    "Goal",
    "Files Read",
    "Constraints And Existing Patterns",
    "Full Todo List",
    "Task 1 Changes",
    "Verification Already Run",
    "Remaining Work",
    "Risks / Do Not Repeat",
)

#: Codex ``spawn_agent.fork_turns``: ``"all"`` lets the executor inherit the
#: planner's whole trajectory (the mechanism the technique is named after);
#: ``"none"`` hands off a fresh context carrying only the packet (the
#: behaviour this project inherited from its 0.4.x ancestor).
V4_FORK_MODES = ("all", "none")

#: A rejected Stop checkpoint stays recoverable for this many retries before
#: the adapter gives up blocking and surfaces the problem to the human.
V4_CHECKPOINT_RETRY_LIMIT = 3

#: Planner file-mutation budget (in edits, not turns). The first value is
#: where the nudge starts; the second is the "wrap up now" escalation; past
#: the hard limit every further edit draws the strongest wording.
V4_PLANNER_NUDGE_AT = (6, 10)
V4_PLANNER_MUTATION_LIMIT = 12

#: An ambiguous route becomes ``stale`` after a day without lifecycle news.
V4_DEFAULT_STALE_SECONDS = 24 * 60 * 60

# --- Pause-marker detection ---------------------------------------------------
#
# A todo counts as the legacy handoff marker when its content begins with the
# pause emoji (U+23F8, with or without the U+FE0F variation selector) or a
# case-sensitive "PAUSE" / "[PAUSE]" anchored at the very start. This mirrors
# opencode-prewalk's isPauseTodo exactly so shared habits keep working.

_PAUSE_RE = re.compile(r"^\[?PAUSE\b")


def is_pause_todo(content: str | None) -> bool:
    """Return True when a todo's content is the legacy pause marker."""
    stripped = (content or "").replace("️", "").lstrip()
    if stripped.startswith("⏸"):  # ⏸
        return True
    return bool(_PAUSE_RE.search(stripped))


def _status_open(status: str | None) -> bool:
    """A todo is remaining work unless completed or cancelled."""
    return status not in ("completed", "cancelled")


@dataclass
class Todo:
    """One normalized todo item, identical on every host."""

    id: str = ""
    content: str = ""
    status: str = ""  # pending | in_progress | completed | cancelled

    @property
    def is_pause(self) -> bool:
        return is_pause_todo(self.content)

    @property
    def open(self) -> bool:
        return _status_open(self.status) and not self.is_pause


def count_remaining(todos: Iterable[Todo]) -> int:
    """Count real, unfinished todos (the pause marker never counts)."""
    return sum(1 for todo in todos if todo.open)


# A todo carries a validation checkpoint when its content mentions one of
# these words — the "verify before you mark complete" rule.
_VERIFY_RE = re.compile(r"\b(?:verify|validate|test|build|check|inspect|confirm|lint)\b", re.I)


def validate_todo_list(todos: list[Todo], cap: int = DEFAULT_MAX_TODOS) -> str | None:
    """Check a todo list against the prewalk planning rules.

    Returns an error string suitable for the model, or None when the list is
    acceptable: non-empty, within ``cap`` items, each with an id plus
    actionable content that mentions a validation checkpoint, and a valid
    status. Pause markers are exempt from the checkpoint-word requirement.
    """
    real = [todo for todo in todos if not todo.is_pause]
    if not real:
        return "Prewalk requires a non-empty todo list before editing."
    if len(real) > cap:
        return f"Prewalk requires at most {cap} todo items; consolidate the plan and retry."
    for index, todo in enumerate(real, 1):
        if not (todo.id or "").strip() or not (todo.content or "").strip():
            return f"Prewalk todo item {index} needs both an id and actionable content."
        if not _VERIFY_RE.search(todo.content or ""):
            return f"Prewalk todo item {index} must include a validation checkpoint (test/build/verify/check)."
        if (todo.status or "") not in ("", "pending", "in_progress", "completed", "cancelled"):
            return f"Prewalk todo item {index} has an invalid status."
    return None


def validate_checkpoint(todos: list[Todo], cap: int = DEFAULT_MAX_TODOS) -> str | None:
    """Check the legacy handoff invariant expressed by a full todo snapshot."""
    error = validate_todo_list(todos, cap)
    if error:
        return error
    real = [todo for todo in todos if not todo.is_pause]
    if real[0].status != "completed":
        return "Prewalk task #1 must be completed and verified before the PAUSE checkpoint."
    if not any(todo.is_pause for todo in todos):
        return "Prewalk requires a PAUSE checkpoint todo before handoff."
    return None


def missing_packet_headings(packet: str) -> list[str]:
    """List required packet headings absent from a Stop message.

    A heading matches as a markdown heading or a bare line, optionally ending
    with a colon — the planner may format the packet either way.
    """
    missing: list[str] = []
    for heading in V4_PACKET_HEADINGS:
        pattern = rf"(?mi)^\s*(?:#{{1,6}}\s*)?{re.escape(heading)}\s*:?(?:\s+.*)?$"
        if not re.search(pattern, packet or ""):
            missing.append(heading)
    return missing
