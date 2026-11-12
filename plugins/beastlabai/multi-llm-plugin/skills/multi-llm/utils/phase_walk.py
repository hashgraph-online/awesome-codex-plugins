"""The workflow's "what is next" rule: one walk over the phase order.

``modes.PREREQUISITE_PHASES`` owns the phase vocabulary and order; this module
owns the rule over them. Its readers each ask it a different question of the
same ``phases`` map (``check_workflow_prerequisites.get_workflow_status``'s
payload, one ``{"status": ...}`` entry per phase):

* ``get_workflow_status`` asks :func:`next_step` with no start for the
  payload's ``suggested_next``;
* ``utils/next_phase.next_phase_commands`` asks it from the phase a run just
  finished (or ``util next-command --after``'s);
* ``utils/next_phase.gate_resume_suggested`` asks :func:`comes_after` whether
  the suggestion lies past ``implement``.

Pure: no I/O and no skill imports, so a walk is tested with a dict alone. The
order is a parameter, and every caller passes ``modes.PREREQUISITE_PHASES``.
See docs/development/status.md for the contract the walk keeps with ``status``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional, Sequence

#: The phases that never keep a workflow open: offered before the next required
#: phase, never suggested themselves.
OPTIONAL_PHASES = {"review-tasks", "apply-task-suggestions"}

#: ``get_workflow_status``'s two recorded-and-done words. Every other status,
#: ``pending`` *and* ``in_progress``, is open.
DONE_STATUSES = ("completed", "skipped")

#: :attr:`Step.kind` values.
#: The start itself is ``in_progress``: resuming it is the answer.
RESUME = "resume"
#: A required phase before the start (or, with no start, anywhere) was started
#: and not finished (:func:`is_started`).
STARTED = "started"
#: The start's completion is stale (recorded before implement's latest).
STALE = "stale"
#: The first open required phase after the start, or after the furthest
#: completed phase when there is no start.
NEXT = "next"
#: Nothing required is left open.
COMPLETE = "complete"


@dataclass(frozen=True)
class Step:
    """What :func:`next_step` found: the phase (``None`` when complete) and
    which rule found it (one of the kind constants above)."""

    phase: Optional[str]
    kind: str


def entry_of(phases: Mapping[str, Any], phase: str) -> Mapping[str, Any]:
    """*phase*'s entry, ``{}`` when the map has none."""
    return phases.get(phase) or {}


def is_open(entry: Mapping[str, Any]) -> bool:
    """Not recorded done: ``pending``, ``in_progress``, or no status at all."""
    return entry.get("status") not in DONE_STATUSES


def is_started(entry: Mapping[str, Any]) -> bool:
    """Started and not finished: open, and ``in_progress``, with a seeded task
    list (``tasks_total``, an implement that stopped) or a ``stale``
    completion (it ran to the end once). Resuming such a phase comes before
    anything after it."""
    return is_open(entry) and bool(
        entry.get("status") == "in_progress"
        or entry.get("tasks_total")
        or entry.get("stale")
    )


def is_required(phase: str) -> bool:
    """Whether *phase* keeps the workflow open (it is not optional)."""
    return phase not in OPTIONAL_PHASES


def first_started(phases: Mapping[str, Any], span: Sequence[str]) -> Optional[str]:
    """The first required phase in *span* that :func:`is_started`."""
    return next(
        (phase for phase in span
         if is_required(phase) and is_started(entry_of(phases, phase))),
        None,
    )


def first_open(phases: Mapping[str, Any], span: Sequence[str]) -> Optional[str]:
    """The first required phase in *span* that :func:`is_open`."""
    return next(
        (phase for phase in span
         if is_required(phase) and is_open(entry_of(phases, phase))),
        None,
    )


def furthest_completed(phases: Mapping[str, Any], order: Sequence[str]) -> int:
    """The index in *order* of the last phase recorded ``completed``, else -1.
    A skip does not count: a skip marked because a review was skipped or
    found nothing sits after phases that may not have run."""
    return max(
        (index for index, phase in enumerate(order)
         if entry_of(phases, phase).get("status") == "completed"),
        default=-1,
    )


def comes_after(order: Sequence[str], phase: str, other: str) -> bool:
    """Whether *phase* lies after *other* in *order*; ``False`` when either is
    not in it."""
    if phase not in order or other not in order:
        return False
    return order.index(phase) > order.index(other)


def next_step(
    phases: Mapping[str, Any],
    order: Sequence[str],
    after: Optional[str] = None,
) -> Step:
    """The phase to run next, and the rule that picked it.

    With no *after* (the payload's ``suggested_next``):

    1. a required phase that was started and not finished
       (:func:`is_started`) is the answer (``STARTED``);
    2. otherwise the first open required phase after the furthest phase on
       record as completed (``NEXT``), never one before it: starting
       mid-workflow never sends the user back, and a plan with nothing
       completed starts at the first open required phase.

    From *after* (the phase a run finished, or ``--after``'s):

    1. *after* itself ``in_progress`` is resumed (``RESUME``);
    2. a required phase **before** it that was started and not finished
       comes first (``STARTED``), so the next step and ``suggested_next``
       never disagree; a phase never begun before a standalone start stays
       skipped over;
    3. a stale *after* is its own answer (``STALE``);
    4. otherwise the first open required phase after it (``NEXT``).

    Either way, nothing open is ``COMPLETE`` with no phase: an optional phase
    never keeps a workflow open. A gate on whether *after* is on record is
    the caller's (``next_phase_commands`` applies it after ``RESUME``).
    """
    if after is None:
        started = first_started(phases, order)
        if started is not None:
            return Step(started, STARTED)
        upcoming = first_open(phases, order[furthest_completed(phases, order) + 1:])
    else:
        entry = entry_of(phases, after)
        if entry.get("status") == "in_progress":
            return Step(after, RESUME)
        index = order.index(after)
        started = first_started(phases, order[:index])
        if started is not None:
            return Step(started, STARTED)
        if entry.get("stale"):
            return Step(after, STALE)
        upcoming = first_open(phases, order[index + 1:])
    if upcoming is None:
        return Step(None, COMPLETE)
    return Step(upcoming, NEXT)
