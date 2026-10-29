#!/usr/bin/env python3
"""Check workflow prerequisites before proceeding to next phase.

This script owns D6 rows **5** (the generate-tasks gate), **6** (the implement
gate) and **13** (``review-tasks`` against a plan with no task list). It is the
only owner: the gate logic is not reimplemented in markdown and no thin
orchestrator wraps it, because the *check* was already a script.

D6a — consent to run unattended is not consent to stale input. Tasks generated
from, or an implementation run against, a plan whose HIGH-importance review
suggestions were never applied silently poisons every downstream phase, and a
warning printed into a headless log nobody reads *is* that failure mode. So
``--yes`` alone never skips these gates:

* **Inside the full workflow** — :func:`ensure_prerequisites` auto-runs the
  missing apply phase **once**, then re-checks. The gate is *satisfied*, not
  bypassed; a second unmet re-check is exit 3, never a retry loop.
* **Standalone** — exit 3 with one message naming both fixes (apply first, or
  re-run with ``--skip-prerequisites``), absolute paths, D5a-shaped commands.
* **``--skip-prerequisites``** — a separate, explicit flag ``--yes`` never
  implies. Loud but non-fatal: it prints ``[PREREQUISITE_SKIPPED]``, records the
  skip through the same ``--skip``/``--reason`` state path, and is therefore
  always attributable afterwards (``status``, the implementation summary and any
  later review can all see it).

**Nothing is produced before the gate**: rows 5/6 are preflight, so an unmet
prerequisite writes no tasks into the plan file, no phase dir and no
``state.json`` mutation — there is no "generated but not applied" middle state to
clean up.

Streams: **stdout stays pure JSON** in every path (its callers ``json.loads`` the
whole of it, and ``status --view workflow`` is byte-identical to
``--status --json``); the human-readable ``[PREREQUISITE_*]`` blocks go to stderr
and travel inside the JSON as ``message``. The orchestrators that already print
prose markers on stdout (``implement_orchestrator.py``) print theirs there.
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

# Add parent dir to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.stream_bootstrap import bootstrap_streams
from utils.cli_common import (
    EXIT_NEEDS_HUMAN,
    EXIT_OK,
    build_parent_parser,
    dispatcher_command,
)

# One table owns the phase vocabulary: the dispatcher resolves a `--mode`/
# `--phase` word against the same rows (`modes.py`), so `review-code` (the mode
# word) and `code-review` (the phase name) can never drift apart per host.
from modes import PREREQUISITE_PHASES, phase_from_selector, resolve as resolve_mode
from utils import unattended as unattended_mod
from utils.state_manager import StateManager
from utils.output_handler import get_output_dir

PHASE_PREREQUISITES = {
    "apply-suggestions": ["review-plan"],
    "generate-tasks": ["apply-suggestions"],
    "review-tasks": ["generate-tasks"],
    "apply-task-suggestions": ["review-tasks"],
    "implement": ["apply-suggestions", "generate-tasks"],
    "apply-code-fixes": ["code-review"],
}

OPTIONAL_PHASES = {"review-tasks", "apply-task-suggestions"}

#: Each apply phase's own write-batch ids in ``state.json``'s ``task_status``
#: map (``utils/write_phase_bridge.py``: ``apply-batch-N``,
#: ``apply-task-batch-N``, ``apply-fix-batch-N``). That map is one flat
#: namespace shared by every write kind, so an id is matched whole — the way
#: ``StateManager.implementation_task_statuses`` matches implement's ``T###`` —
#: and an ``apply-batch-N`` never counts for apply-task-suggestions.
APPLY_BATCH_ID_PATTERNS: Dict[str, "re.Pattern"] = {
    "apply-suggestions": re.compile(r"^apply-batch-[0-9]+$"),
    "apply-task-suggestions": re.compile(r"^apply-task-batch-[0-9]+$"),
    "apply-code-fixes": re.compile(r"^apply-fix-batch-[0-9]+$"),
}

#: ``get_workflow_status``'s two recorded-and-done words: every walk over its
#: ``phases`` map (``suggested_next`` here, ``utils/next_phase.py`` there)
#: treats any other status — ``pending`` *and* ``in_progress`` — as open.
DONE_STATUSES = ("completed", "skipped")


def _grouped_has_suggestions(path: Path) -> bool:
    """Whether a ``grouped.json`` carries anything to apply (v1 list or v2 envelope).

    The one predicate both ``full`` (``step_apply_code_fixes``) and
    :func:`get_workflow_status` ask of ``code-review/grouped.json``, so the two
    cannot disagree about whether a review left anything to fix. True when any
    group has a non-empty ``suggestions`` list, whatever its validation verdict;
    false for a missing or unreadable file. It reads no ``validation.json``,
    ``issues.json`` or user selection, so a review whose groups were all judged
    invalid or all deselected still counts as having findings.
    """
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return False
    if isinstance(data, dict) and "groups" in data:
        groups = data["groups"]
    elif isinstance(data, list):
        groups = data
    else:
        return False
    if not isinstance(groups, list):
        return False
    return any(
        isinstance(group, dict) and group.get("suggestions") for group in groups
    )


def _parse_timestamp(value) -> Optional[datetime]:
    """An ISO timestamp from ``state.json`` as a naive local datetime, or None."""
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone().replace(tzinfo=None)
    return parsed


def _latest_phase_activity(state: StateManager, phase: str) -> Optional[datetime]:
    """The newest time ``state.json`` records for one of ``phase``'s own runs.

    ``task_status`` carries no time, so a write batch is dated through the two
    records the scheduler writes beside it: ``metrics_progress.{phase}.started_at``
    (stamped before a run's first dispatch, popped only when the phase is marked
    completed) and each ``metrics.{phase}`` entry's ``timestamp`` (saved with
    the batch's status) — plus ``phases_started.{phase}``, the native leg's
    own record of a run handed to the host (re-stamped on every emit). None
    when none holds a readable time.
    """
    stamps = [_parse_timestamp(state.phase_started_at(phase))]
    progress = state.state.get("metrics_progress")
    if isinstance(progress, dict) and isinstance(progress.get(phase), dict):
        stamps.append(_parse_timestamp(progress[phase].get("started_at")))
    metrics = state.state.get("metrics")
    entries = metrics.get(phase) if isinstance(metrics, dict) else None
    if isinstance(entries, list):
        stamps.extend(
            _parse_timestamp(entry.get("timestamp"))
            for entry in entries if isinstance(entry, dict)
        )
    stamps = [stamp for stamp in stamps if stamp is not None]
    return max(stamps) if stamps else None


#: The phases whose completion writes the task list implement runs.
TASK_LIST_PHASES = ("generate-tasks", "apply-task-suggestions")


def implement_records_predate_task_list(state: StateManager) -> bool:
    """Whether implement's recorded task statuses belong to an earlier task list.

    Nothing clears ``task_status`` when generate-tasks or apply-task-suggestions
    writes a new ``tasks.md``, so an id an earlier implement recorded may name
    another task now. The records are an earlier list's when implement's
    latest dated run (:func:`_latest_phase_activity`) is older than the latest
    completion of either phase. False whenever either time is missing (absence
    of a date is not staleness), the rule :func:`_apply_batches_predate_review`
    applies to apply batches.
    """
    last_run = _latest_phase_activity(state, "implement")
    if last_run is None:
        return False
    completed = state.state.get("phases_completed") or {}
    for phase in TASK_LIST_PHASES:
        produced = _parse_timestamp(completed.get(phase))
        if produced is not None and produced > last_run:
            return True
    return False


def _apply_batches_predate_review(state: StateManager, phase: str) -> bool:
    """Whether an apply phase's recorded batches belong to an earlier review.

    Nothing clears ``task_status`` when a review is re-run (``review-code
    --force``, ``review-plan --force``), so batch ids left by a partly applied
    cycle outlive the review that produced them. They are that cycle's when the
    phase's latest recorded run (:func:`_latest_phase_activity`) is older than
    its review's latest completion — each apply phase's one prerequisite is the
    review it applies. False whenever either time is missing, which keeps the
    mark for a state with no dated run (absence of a date is not staleness).
    A review completion re-stamped without new findings (``--reaggregate``)
    reads the same way; the cost is a bare command instead of ``--resume``,
    and the scheduler still skips a batch whose result and inputs match.

    A review that is not ``completed`` has no cycle for the batches to belong
    to, so they are an earlier one's: True. (Adversarial review, 2026-10-02:
    this returned False for a code-review read as pending because it predated
    implement's latest completion, so the batches of the cycle it had produced
    marked apply-code-fixes ``in_progress`` and ``next-command`` offered the
    ``--resume`` that replays that cycle's recorded decisions.)
    """
    review = PHASE_PREREQUISITES[phase][0]
    # Read as `get_workflow_status`'s first loop reads the review — its status
    # from `is_phase_completed`, its stamp the raw `phases_completed` entry —
    # so a caller holding no `phases` map gets the answer `status` prints.
    if not state.is_phase_completed(review):
        return True
    completed = state.state.get("phases_completed") or {}
    reviewed_at = _parse_timestamp(completed.get(review))
    last_run = _latest_phase_activity(state, phase)
    if reviewed_at is None or last_run is None:
        return False
    return last_run < reviewed_at


def apply_phase_in_progress(state: StateManager, phase: str) -> bool:
    """Whether apply phase *phase* has progress of the review on record.

    ``get_workflow_status``'s rule for marking an apply phase ``in_progress``
    (the one status the next-step builder spells with ``--resume``), as one
    predicate, so ``status``, ``next-command``, the ``--blocked`` delegation
    and a composite deciding whether to infer ``--resume`` cannot disagree.
    Progress is a started record (:meth:`StateManager.is_phase_started`, the
    native leg's emit) or one of the phase's own write-batch ids
    (:data:`APPLY_BATCH_ID_PATTERNS`, both legs) recorded ``completed``. It
    is discarded when it belongs to an earlier review cycle or the review is
    not ``completed`` (:func:`_apply_batches_predate_review`).

    *state* is the :class:`StateManager` ``get_workflow_status`` holds, not
    its raw dict: the started record and the staleness of a code review are
    its methods' answers. *phase* is an apply phase's word in ``state.json``
    (``apply-suggestions``, ``apply-task-suggestions``, ``apply-code-fixes``);
    any other word raises ``KeyError``. It does not ask whether *phase*
    itself is completed or skipped: ``status`` checks that first
    (``DONE_STATUSES``), and a caller that needs it asks the same.
    """
    pattern = APPLY_BATCH_ID_PATTERNS[phase]
    has_progress = state.is_phase_started(phase) or any(
        pattern.match(task_id) and status == "completed"
        for task_id, status in state.get_all_task_statuses().items()
    )
    return has_progress and not _apply_batches_predate_review(state, phase)


def check_phase_prerequisite(state: StateManager, required_phase: str) -> dict:
    """Check if a required phase has been completed or skipped."""
    if state.is_phase_completed(required_phase):
        return {"met": True, "reason": f"{required_phase} completed"}
    if state.is_phase_skipped(required_phase):
        return {"met": True, "reason": f"{required_phase} skipped"}
    return {"met": False, "reason": f"{required_phase} not yet run"}


def check_apply_suggestions_prerequisite(state: StateManager, plan_dir: Path) -> dict:
    """
    Check if apply-suggestions phase should run before proceeding.

    Returns:
        Dict with 'met' boolean and details
    """
    review_plan_dir = plan_dir / "review-plan"
    validation_path = review_plan_dir / "validation.json"

    # No review-plan run → no prerequisite
    if not validation_path.exists():
        return {"met": True, "reason": "No review-plan results to apply"}

    # Check if apply-suggestions completed or skipped
    if state.is_phase_completed("apply-suggestions"):
        return {"met": True, "reason": "Apply-suggestions phase completed"}
    if state.is_phase_skipped("apply-suggestions"):
        reason = state.get_phase_skip_reason("apply-suggestions") or "Explicitly skipped"
        return {"met": True, "reason": f"Apply-suggestions skipped: {reason}"}

    # Count valid suggestions that would be applied
    try:
        with open(validation_path, 'r', encoding='utf-8') as f:
            validation = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {"met": True, "reason": "Could not read validation results"}

    valid_count = 0
    importance_breakdown = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}

    # Handle both v1 (flat dict keyed by group_id) and v2 (envelope with
    # metadata + groups list) validation formats.
    if isinstance(validation, dict) and "groups" in validation:
        # v2 envelope format
        validation_entries = validation["groups"]
    elif isinstance(validation, dict):
        # v1 flat dict format: convert values to a list
        validation_entries = list(validation.values())
    else:
        validation_entries = []

    for entry in validation_entries:
        if not isinstance(entry, dict):
            continue
        if entry.get("status") == "valid":
            valid_count += 1
            importance = entry.get("importance", "MEDIUM")
            if importance in importance_breakdown:
                importance_breakdown[importance] += 1

    if valid_count == 0:
        # `open_count` is what `get_workflow_status` keys the
        # `skipped (no valid findings)` mark on (plans/next-phase-command.md
        # §2.1): the groups whose verdict is anything but `invalid`. This return
        # is too wide to mean "nothing to apply" on its own — a review whose
        # only groups are `needs-human-decision` lands here too, and
        # apply-suggestions presents those, so skipping it would hide decisions
        # the user still owes. Only this return carries the field; the other
        # met returns (no or unreadable `validation.json`) mark nothing.
        open_count = sum(
            1 for entry in validation_entries
            if isinstance(entry, dict) and entry.get("status") != "invalid"
        )
        return {
            "met": True,
            "reason": "No valid suggestions to apply",
            "open_count": open_count,
        }

    # Prerequisite NOT met - has unapplied suggestions
    return {
        "met": False,
        "reason": f"Review-plan found {valid_count} valid suggestions not yet applied",
        "valid_count": valid_count,
        "importance_breakdown": importance_breakdown
    }


def check_apply_task_suggestions_prerequisite(state: StateManager, plan_dir: Path) -> dict:
    """
    Check if apply-task-suggestions phase should run before proceeding.

    Counts actionable task suggestions from review-tasks/grouped.json and
    surfaces them in the result. This enables the --implement soft prompt
    for unapplied task suggestions.

    Returns:
        Dict with 'met' boolean and details including actionable_count
    """
    review_tasks_dir = plan_dir / "review-tasks"
    grouped_path = review_tasks_dir / "grouped.json"
    validation_path = review_tasks_dir / "validation.json"

    # If review-tasks was skipped, apply-task-suggestions is skipped too. A
    # review that was skipped and LATER completed is completed (completed wins,
    # as in get_workflow_status): mark_phase_completed leaves the old skip record.
    if state.is_phase_skipped("review-tasks") and not state.is_phase_completed("review-tasks"):
        return {"met": True, "reason": "skipped (prerequisite skipped)"}

    # If review-tasks hasn't run yet (no grouped.json), nothing to do
    if not grouped_path.exists():
        return {"met": True, "reason": "No review-tasks results to apply"}

    # Check if apply-task-suggestions already completed or skipped
    if state.is_phase_completed("apply-task-suggestions"):
        return {"met": True, "reason": "Apply-task-suggestions phase completed"}
    if state.is_phase_skipped("apply-task-suggestions"):
        reason = state.get_phase_skip_reason("apply-task-suggestions") or "Explicitly skipped"
        return {"met": True, "reason": f"Apply-task-suggestions skipped: {reason}"}

    # Defensive fallback: check state["phases"] dict (written by orchestrator output
    # but not yet migrated to phases_completed by --mark-completed)
    phase_info = state.state.get("phases", {}).get("apply-task-suggestions", {})
    if phase_info.get("status") == "completed":
        return {"met": True, "reason": "Apply-task-suggestions phase completed (from phases metadata)"}

    # Load grouped.json and count actionable suggestions
    try:
        with open(grouped_path, 'r', encoding='utf-8') as f:
            grouped_data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {"met": True, "reason": "Could not read grouped results"}

    # Handle both v1 (bare list) and v2 (envelope with format_version) formats
    if isinstance(grouped_data, dict) and "groups" in grouped_data:
        groups = grouped_data["groups"]
    elif isinstance(grouped_data, list):
        groups = grouped_data
    else:
        return {"met": True, "reason": "No actionable task suggestions found"}

    # The notice and validation both count groups. Without usable verdicts,
    # duplicate suggestions inside one group must not inflate that count.
    total_groups = sum(bool(group.get("suggestions")) for group in groups)

    if total_groups == 0:
        return {"met": True, "reason": "skipped (no findings)", "actionable_count": 0}

    # Cross-reference with validation.json if available to count valid ones
    actionable_count = total_groups
    counted_valid = False
    importance_breakdown = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}

    if validation_path.exists():
        try:
            with open(validation_path, 'r', encoding='utf-8') as f:
                validation = json.load(f)

            # Handle both v1 (flat dict keyed by group_id) and v2 (envelope
            # with metadata + groups list) validation formats.
            if isinstance(validation, dict) and "groups" in validation:
                # v2 envelope format
                validation_groups = validation["groups"]
            elif isinstance(validation, dict):
                # v1 flat dict format: convert values to a list
                validation_groups = list(validation.values())
            else:
                validation_groups = []

            # Count valid suggestions from validation results
            valid_count = 0
            for entry in validation_groups:
                if not isinstance(entry, dict):
                    continue
                if entry.get("status") == "valid":
                    valid_count += 1
                    importance = entry.get("importance", "MEDIUM")
                    if importance in importance_breakdown:
                        importance_breakdown[importance] += 1

            if valid_count > 0:
                actionable_count = valid_count
                counted_valid = True
            # If validation exists but nothing is valid, still count all groups
            # as actionable (user may override validation)
        except (json.JSONDecodeError, OSError):
            pass

    # Prerequisite NOT met - has unapplied task suggestions
    # `actionable_count` counts valid groups, or all nonempty groups when no
    # usable valid verdict exists, never suggestions inside a group. A group
    # holds one or more suggestions, so "N unapplied task suggestions" reads as
    # a suggestion count when it is actually a group count — measured
    # 2026-09-16, a run with 17 valid groups (holding 26 suggestions between
    # them) reported "17 unapplied task suggestions".
    return {
        "met": False,
        "reason": f"review-tasks produced {actionable_count} unapplied task suggestion groups",
        "actionable_count": actionable_count,
        # Whether that count is of groups validation judged valid (fix round
        # 18: the next-step notice says so when it is).
        "counted_valid": counted_valid,
        "importance_breakdown": importance_breakdown
    }


def build_prompt(mode: str, missing: list) -> dict:
    """Build prompt for user interaction based on missing prerequisites."""
    if not missing:
        return None

    # Handle apply-suggestions prerequisite
    for m in missing:
        if m.get("phase") == "apply-suggestions":
            valid_count = m.get("valid_count", 0)
            breakdown = m.get("importance_breakdown", {})

            details = []
            for level in ["HIGH", "MEDIUM", "LOW"]:
                if breakdown.get(level, 0) > 0:
                    details.append(f"{breakdown[level]} {level}")

            detail_str = ", ".join(details) if details else f"{valid_count} suggestions"

            return {
                "question": f"Review found {valid_count} suggestions ({detail_str}). Apply them before {mode}?",
                "options": [
                    {"label": "Apply suggestions first (Recommended)", "action": "run_apply_suggestions"},
                    {"label": "Skip suggestions, proceed", "action": "skip_and_continue"},
                    {"label": "Cancel", "action": "abort"}
                ]
            }

    # Handle apply-task-suggestions prerequisite
    for m in missing:
        if m.get("phase") == "apply-task-suggestions":
            actionable_count = m.get("actionable_count", 0)
            breakdown = m.get("importance_breakdown", {})

            details = []
            for level in ["HIGH", "MEDIUM", "LOW"]:
                if breakdown.get(level, 0) > 0:
                    details.append(f"{breakdown[level]} {level}")

            detail_str = ", ".join(details) if details else f"{actionable_count} task suggestions"

            return {
                "question": f"There are {actionable_count} unapplied task suggestions from review-tasks ({detail_str}). Apply them first?",
                "options": [
                    {"label": "Apply task suggestions first (Recommended)", "action": "run_apply_task_suggestions"},
                    {"label": "Skip task suggestions, proceed", "action": "skip_and_continue"},
                    {"label": "Cancel", "action": "abort"}
                ]
            }

    return None


# ---------------------------------------------------------------------------
# D6a — the gates, and the three branches they resolve to
# ---------------------------------------------------------------------------

UNMET_MARKER = "[PREREQUISITE_UNMET]"
SKIPPED_MARKER = "[PREREQUISITE_SKIPPED]"
SKIPPED_UPSTREAM_MARKER = "[PREREQUISITE_SKIPPED_UPSTREAM"

#: The reason string recorded for an explicit ``--skip-prerequisites``. Quoted
#: verbatim by the downstream ``[PREREQUISITE_SKIPPED_UPSTREAM …]`` notice, so a
#: later phase can say *why* it is building on unapplied review output.
SKIP_PREREQUISITES_REASON = "explicit --skip-prerequisites"

#: The prerequisites ``--skip-prerequisites`` may skip: the ones whose output is
#: *advice* (review suggestions someone chose not to apply). A missing
#: ``generate-tasks`` is not skippable — a plan with no task list has nothing to
#: implement or review, which is row 13's "not a repair this mode may make".
SKIPPABLE_PREREQUISITES: Tuple[str, ...] = (
    "apply-suggestions", "apply-task-suggestions",
)

#: The prerequisites that are a *review* phase rather than an apply phase
#: (``apply-suggestions`` needs ``review-plan``, ``apply-code-fixes`` needs
#: ``code-review``, ``apply-task-suggestions`` needs ``review-tasks``). Nothing
#: has been *produced* yet in this case, so there are no unapplied suggestions to
#: name and no artifact to point at — and, being outside
#: ``SKIPPABLE_PREREQUISITES``, nothing ``--skip-prerequisites`` may skip either.
REVIEW_PREREQUISITES: Tuple[str, ...] = (
    "review-plan", "review-tasks", "code-review",
)

#: Mode -> the D6 row it is gated by, so one table owns the mapping.
GATE_ROW: Dict[str, int] = {
    "generate-tasks": 5,
    "implement": 6,
    "review-tasks": 13,
}


def collect_missing(state: StateManager, plan_dir: Path, mode: str) -> List[dict]:
    """Every unmet hard prerequisite of *mode*, in workflow order."""
    missing: List[dict] = []
    for required_phase in PHASE_PREREQUISITES.get(mode, []):
        # Use specialized check for apply-suggestions (has detailed suggestion counting)
        if required_phase == "apply-suggestions":
            apply_check = check_apply_suggestions_prerequisite(state, plan_dir)
            if not apply_check["met"]:
                missing.append({
                    "phase": "apply-suggestions",
                    "reason": apply_check["reason"],
                    "valid_count": apply_check.get("valid_count", 0),
                    "importance_breakdown": apply_check.get("importance_breakdown", {}),
                })
        else:
            # Use generic state-based check for other phases
            phase_check = check_phase_prerequisite(state, required_phase)
            if not phase_check["met"]:
                missing.append({
                    "phase": required_phase,
                    "reason": phase_check["reason"],
                })
    return missing


def _mode_word(phase: str) -> str:
    """The dispatcher word for *phase*.

    Mode word and phase name differ for exactly one row (mode ``review-code``,
    phase ``code-review``), so a command is rendered from the table rather than
    from the phase name a prerequisite entry happens to carry.
    """
    mode = resolve_mode(phase)
    return mode.name if mode is not None else phase


def _breakdown_text(entry: dict) -> str:
    """``7 HIGH / 3 MEDIUM`` from an importance breakdown, else a plain count."""
    breakdown = entry.get("importance_breakdown") or {}
    parts = [
        f"{breakdown[level]} {level}"
        for level in ("HIGH", "MEDIUM", "LOW")
        if breakdown.get(level, 0) > 0
    ]
    if parts:
        return " / ".join(parts)
    count = entry.get("valid_count") or entry.get("actionable_count") or 0
    return f"{count}" if count else "unapplied"


def build_unmet_message(
    mode: str, plan_path: Path, plan_dir: Path, missing: Sequence[dict]
) -> str:
    """The one blocking message, both fixes named, absolute paths, D5a commands.

    This is a *blocking* message, not a warning: a warning in a headless log
    nobody reads is the failure mode, not the mitigation.
    """
    plan_abs = str(Path(plan_path).resolve())
    lines: List[str] = []
    for entry in missing:
        phase = entry.get("phase", "")
        if phase == "generate-tasks":
            # Row 13 (and implement's tasks prerequisite): the answer is
            # out-of-band — generate the tasks, then re-run. There is no
            # `--skip-prerequisites` option here on purpose.
            lines += [
                f"{UNMET_MARKER} {mode}: no task list has been generated for "
                f"{plan_abs}.",
                "  1) Generate the tasks first — "
                + dispatcher_command("generate-tasks", plan_abs, "--yes"),
                "     then re-run              — "
                + dispatcher_command(mode, plan_abs, "--yes"),
            ]
            continue
        if phase in REVIEW_PREREQUISITES:
            # The unmet prerequisite is the *review itself*: nothing has been
            # produced, so there is no `validation.json` to cite and no
            # "suggestions were not applied" to count. There is no
            # `--skip-prerequisites` option here either — `ensure_prerequisites`
            # refuses it for anything outside SKIPPABLE_PREREQUISITES, so
            # printing it would be a command the agent copies and gets exit 3 on.
            lines += [
                f"{UNMET_MARKER} {mode}: {phase} has not been run for "
                f"{plan_abs}.",
                "  1) Run it first — "
                + dispatcher_command(_mode_word(phase), plan_abs, "--yes"),
                "     then re-run  — "
                + dispatcher_command(_mode_word(mode), plan_abs, "--yes"),
            ]
            continue
        source = str((Path(plan_dir) / "review-plan" / "validation.json").resolve()) \
            if phase == "apply-suggestions" \
            else str((Path(plan_dir) / "review-tasks" / "validation.json").resolve())
        lines += [
            f"{UNMET_MARKER} {mode}: {_breakdown_text(entry)} suggestions in "
            f"{source} have not been applied.",
            "  1) Apply them first — "
            + dispatcher_command(phase, plan_abs, "--yes"),
            "     then re-run      — "
            + dispatcher_command(mode, plan_abs, "--yes"),
            "  2) Proceed on unapplied review output (recorded) —",
            "     "
            + dispatcher_command(mode, plan_abs, "--yes", "--skip-prerequisites"),
        ]
    return "\n".join(lines)


def upstream_skip_notices(state: StateManager) -> List[str]:
    """``[PREREQUISITE_SKIPPED_UPSTREAM …]`` lines for skips already recorded.

    A mode gates on **its own** prerequisite only. It does not re-litigate how the
    artifact it consumes was produced: if an earlier phase ran under
    ``--skip-prerequisites``, consent was already given explicitly, and re-asking
    would make the recorded skip meaningless. So the recorded skip surfaces as a
    single line quoting the reason, and the run proceeds.

    Completed wins over skipped: ``mark_phase_completed`` does not clear an
    earlier skip record, so a phase that was skipped and later completed has
    both on file and gets no notice.
    """
    notices: List[str] = []
    for phase in SKIPPABLE_PREREQUISITES:
        if not state.is_phase_skipped(phase) or state.is_phase_completed(phase):
            continue
        reason = state.get_phase_skip_reason(phase) or ""
        if SKIP_PREREQUISITES_REASON not in reason:
            continue
        notices.append(f"{SKIPPED_UPSTREAM_MARKER} {phase}: {reason}]")
    return notices


def record_prerequisite_skip(
    state: StateManager, phase: str, *, reason: str
) -> None:
    """Mark *phase* skipped through the same state path ``--skip`` uses."""
    state.mark_phase_skipped(phase, reason=reason)
    state.save()


@dataclass
class PrereqOutcome:
    """What :func:`ensure_prerequisites` decided.

    Attributes:
        met: True when the mode may proceed.
        exit_code: 0 when it may proceed, 3 when a human is needed. Never 2 —
            "needs a human" and "already done" must stay distinguishable.
        missing: The unmet prerequisite entries (empty when met).
        message: The verbatim ``[PREREQUISITE_UNMET]`` block, when blocking.
        auto_ran: Phases whose apply step this call ran (at most one per phase
            per run).
        skipped: Phases recorded as skipped by ``--skip-prerequisites``.
        notices: ``[PREREQUISITE_SKIPPED*]`` lines the caller should print.
    """

    met: bool
    exit_code: int = EXIT_OK
    missing: List[dict] = field(default_factory=list)
    message: Optional[str] = None
    auto_ran: Tuple[str, ...] = ()
    skipped: Tuple[str, ...] = ()
    notices: List[str] = field(default_factory=list)


def ensure_prerequisites(
    plan_file,
    mode: str,
    *,
    unattended: bool = False,
    in_workflow: bool = False,
    skip_prerequisites: bool = False,
    apply_runner: Optional[Callable[[str], int]] = None,
    state: Optional[StateManager] = None,
) -> PrereqOutcome:
    """Resolve rows 5/6/13 for *mode* without ever rendering a question.

    The three D6a branches, in the order they are tried:

    1. ``--skip-prerequisites`` — record the skip through the existing ``--skip``
       path, emit ``[PREREQUISITE_SKIPPED]``, proceed with the mode's normal exit
       code. The only path on which an artifact may be built from unapplied
       review output, and always attributable afterwards.
    2. *Inside the workflow* (``in_workflow`` with an ``apply_runner``) — run the
       missing apply phase **once**, then re-check. If the apply phase exits
       non-zero, or exits 0 but the re-check still reports the prerequisite unmet
       (e.g. items left ``needs-human-decision`` that ``--agent-decide`` could
       not resolve), stop with exit 3 naming the unresolved items. The auto-run is
       attempted at most once per phase per run: a second unmet re-check is exit
       3, not a retry.
    3. Otherwise — exit 3 (unattended) or the legacy prompt payload (attended,
       where a rendered gate is still legal).

    ``apply_runner`` is injected because applying suggestions needs the driving
    agent's subagent channel (``apply_suggestions_orchestrator.py`` emits
    instructions rather than editing the plan itself). It is called as
    ``apply_runner(phase) -> exit_code``. ``full_workflow_orchestrator.py`` is the
    caller that supplies it (for row 5 through ``generate_tasks_orchestrator`` and
    for row 6 before dispatching ``implement``), and it bounds the runner to one
    auto-run per phase per *run* — this function bounds it to one per *call*. With
    no runner supplied, ``in_workflow`` behaves exactly like standalone, so nothing
    can silently proceed on stale input.

    Never mutates state on the blocking path (rows 5/6 are preflight), and never
    prints: the caller owns its own streams.
    """
    plan_path = Path(plan_file).resolve()
    plan_dir = get_output_dir(plan_path)
    state = state if state is not None else StateManager(plan_path)

    missing = collect_missing(state, plan_dir, mode)
    notices = upstream_skip_notices(state)
    if not missing:
        return PrereqOutcome(met=True, notices=notices)

    if skip_prerequisites:
        unskippable = [
            m["phase"] for m in missing
            if m.get("phase") not in SKIPPABLE_PREREQUISITES
        ]
        if unskippable:
            return PrereqOutcome(
                met=False,
                exit_code=EXIT_NEEDS_HUMAN,
                missing=missing,
                message=(
                    f"ERROR: --skip-prerequisites cannot skip "
                    f"{', '.join(unskippable)} for {mode}: that phase's output is "
                    "the input, not advice about it.\n"
                    + build_unmet_message(mode, plan_path, plan_dir, missing)
                ),
                notices=notices,
            )
        skipped: List[str] = []
        for entry in missing:
            phase = entry["phase"]
            record_prerequisite_skip(state, phase, reason=SKIP_PREREQUISITES_REASON)
            skipped.append(phase)
            notices.append(
                f"{SKIPPED_MARKER} {mode}: {_breakdown_text(entry)} unapplied "
                f"{phase} suggestions (reason: {SKIP_PREREQUISITES_REASON})"
            )
        return PrereqOutcome(
            met=True, missing=[], skipped=tuple(skipped), notices=notices
        )

    if in_workflow and apply_runner is not None:
        auto_ran: List[str] = []
        for entry in missing:
            phase = entry["phase"]
            if phase not in SKIPPABLE_PREREQUISITES:
                continue
            code = apply_runner(phase)
            auto_ran.append(phase)
            if code != EXIT_OK:
                return PrereqOutcome(
                    met=False,
                    exit_code=EXIT_NEEDS_HUMAN,
                    missing=missing,
                    message=(
                        f"{UNMET_MARKER} {mode}: the auto-run of {phase} exited "
                        f"{code}, so the prerequisite is still unmet and nothing "
                        "downstream ran.\n"
                        + build_unmet_message(mode, plan_path, plan_dir, missing)
                    ),
                    auto_ran=tuple(auto_ran),
                    notices=notices,
                )
        # One re-check, never a loop.
        state = StateManager(plan_path)
        remaining = collect_missing(state, plan_dir, mode)
        if not remaining:
            return PrereqOutcome(
                met=True, auto_ran=tuple(auto_ran),
                notices=upstream_skip_notices(state),
            )
        reasons = "; ".join(m.get("reason", "") for m in remaining)
        if auto_ran:
            headline = (
                f"{UNMET_MARKER} {mode}: the apply phase ran once and the "
                f"re-check still reports the prerequisite unmet ({reasons}). "
                "Stopping here rather than retrying."
            )
        else:
            # Nothing was auto-run: every missing prerequisite is outside
            # SKIPPABLE_PREREQUISITES, so the loop above skipped it. Claiming an
            # apply phase ran would send a reader debugging a phase that never
            # executed. Exit 3 is still the right answer — the gate is unmet and
            # the workflow may not repair it on its own.
            unrunnable = ", ".join(m.get("phase", "") for m in remaining)
            headline = (
                f"{UNMET_MARKER} {mode}: nothing was auto-run — {unrunnable} is "
                f"not a prerequisite the workflow may satisfy on its own "
                f"({reasons}). Stopping here."
            )
        return PrereqOutcome(
            met=False,
            exit_code=EXIT_NEEDS_HUMAN,
            missing=remaining,
            message=(
                headline + "\n"
                + build_unmet_message(mode, plan_path, plan_dir, remaining)
            ),
            auto_ran=tuple(auto_ran),
            notices=notices,
        )

    message = build_unmet_message(mode, plan_path, plan_dir, missing)
    return PrereqOutcome(
        met=False,
        exit_code=EXIT_NEEDS_HUMAN if unattended else EXIT_OK,
        missing=missing,
        message=message,
        notices=notices,
    )


#: The write phases codex's own sandbox cannot serve once it fails to start on
#: this machine: their scope is ``repo-wide``, which the plugin's Landlock jail
#: takes since plan step 3b (2026-10-02) — so they are refused at dispatch
#: (``sandbox_unavailable``) only where that rung is unusable too, which is
#: what :func:`repo_wide_sandbox_warning` asks the dispatch's own decision.
REPO_WIDE_WRITE_PHASES = ("implement", "apply-code-fixes")

#: The remedy sentence of that refusal. ``subagent_executor.F6_LEAD`` is the
#: text this repeats with ``{key}`` filled; ``status`` must stay sub-second, so
#: it is not imported here (that module is heavy) and
#: ``TestEarlySandboxWarning`` pins the two together instead.
REPO_WIDE_REMEDY = (
    "To run this now, set `driver.subagent_runner` to a runner that is not "
    "Codex (for example `claude-code:<model>`) in `.multi-llm/providers.yaml`."
)


def repo_wide_sandbox_warning(
    plan_path: Path, plan_dir: Path, *, host_id: Optional[str] = None
) -> Optional[str]:
    """The early warning that implement / apply-code-fixes will be refused.

    On a machine where codex's own sandbox cannot start, a repo-wide write
    dispatch refuses at batch 0 (``sandbox_unavailable``) unless the plugin's
    Landlock jail takes it (plan step 3b, 2026-10-02) — and the user used to
    learn that at phase 6, about 20 minutes in (Codex racing run, 2026-10-02).
    This says so at ``init``, in ``status`` before any phase has run, and on
    the next-step block, from the SAME decision the dispatch takes
    (:func:`utils.subagent_executor.repo_wide_write_refusal`: the adapter's
    model-free probes through the shared probe cache — cheap, no model), never
    from a guess: with the jail usable the warning stays silent, and it fires
    whenever Landlock is unavailable, the rung probe fails, the step-3 opt-in
    is off or the policy word keeps the rung off. The resolved runner is the
    one the dispatch resolves; a runner that is not codex has no sandbox
    probe and draws nothing with nothing spawned. None when the config cannot
    be read, because a warning that may be wrong is worse than none.

    *host_id* is the host the runner is resolved for, and it must be the one
    the dispatch resolves: the ladder's ``session`` rung (the codex / opencode
    session's own model, where the refusal lands) exists only for a host whose
    entry names a ``session_runner_provider``. The reader's ``--host`` is
    that host, and the servers declare it nowhere else — no server, shim or
    surface exports ``$MULTI_LLM_HOST`` — so the fallback is the argv scan the
    executor uses (``resolve_host_id(sys.argv[1:])``), never the bare
    environment read. (Adversarial review, 2026-10-02: resolved against the
    claude-code entry, ``codex:<session model>`` fell to ``claude-code:sonnet``
    and the warning never fired on either tool route while the dispatch
    refused.)
    """
    try:
        from utils import host_capabilities
        from utils.provider_registry import resolve_subagent_runner
        from utils.subagent_executor import repo_wide_write_refusal

        if host_id is None:
            host_id = host_capabilities.resolve_host_id(sys.argv[1:])
        spec, _layer = resolve_subagent_runner(
            "full", anchor=str(plan_path), host_id=host_id,
        )
        refusal = repo_wide_write_refusal(
            spec, anchor=str(plan_path), output_dir=str(plan_dir),
        )
    except Exception:  # noqa: BLE001 - advisory: status never fails on it
        return None
    if refusal is None:
        return None
    return render_repo_wide_warning(spec, refusal)


def render_repo_wide_warning(spec: str, refusal: str) -> str:
    """The warning line: the phases, the runner, the dispatch's own reason
    (its F6 lead and its closing "Nothing was dispatched." moved aside) and
    the remedy last, so the line ends with what to do."""
    body = refusal.strip()
    if body.startswith(REPO_WIDE_REMEDY):
        body = body[len(REPO_WIDE_REMEDY):].strip()
    for prefix in ("Refusing to dispatch: ",):
        if body.startswith(prefix):
            body = body[len(prefix):]
    tail = "Nothing was dispatched."
    if body.endswith(tail):
        body = body[: -len(tail)].strip()
    return (
        f"{' and '.join(REPO_WIDE_WRITE_PHASES)} will be refused on this "
        f"machine for driver.subagent_runner {spec!r}: {body} {REPO_WIDE_REMEDY}"
    )


def _suggested_next(phases: Dict[str, dict], order: List[str]) -> Optional[str]:
    """The phase to run next, from where the workflow really is (fix round 14).

    Picked once, after every post-loop mark in :func:`get_workflow_status`,
    over the required (non-optional) phases, in two steps:

    1. a required phase that was started and not finished — ``in_progress``,
       a seeded task list (``tasks_total``) or a ``stale`` completion — is
       the suggestion: resuming it comes first, as the next-step builder's
       walk says (``next_phase.next_phase_commands``);
    2. otherwise the first open required phase after the furthest phase on
       record as completed, never one before it: starting mid-workflow never
       sends the user back, and with nothing open after it there is no
       suggestion. A skip does not move the position (a skip marked because a
       review was skipped or found nothing sits after phases that may not
       have run), and a plan with nothing completed starts at the first open
       required phase.

    Before this the suggestion was the first open required phase in table
    order, so a plan whose review-plan never ran read "suggested next:
    review-plan" beside an implement stopped at 4/7, and again after
    implement completed (racing re-run 5, the stop-path fixture).
    """
    required = [phase for phase in order if phase not in OPTIONAL_PHASES]

    def is_open(phase: str) -> bool:
        return phases[phase]["status"] not in DONE_STATUSES

    for phase in required:
        info = phases[phase]
        if is_open(phase) and (
            info["status"] == "in_progress" or info.get("tasks_total")
            or info.get("stale")
        ):
            return phase
    furthest = max(
        (index for index, phase in enumerate(order)
         if phases[phase]["status"] == "completed"),
        default=-1,
    )
    return next(
        (phase for phase in order[furthest + 1:]
         if phase in required and is_open(phase)),
        None,
    )


def unapplied_task_groups_notice(
    count: int, *, valid: bool, in_progress: bool = False,
) -> str:
    """The notice for task suggestion groups review-tasks left unapplied.

    It is also the ``why`` of the optional ``--apply-task-suggestions`` step
    the next-step command offers before ``--implement`` (``next_phase``), so
    it names how many groups are waiting and what going straight to
    implement does with them (fix round 18, live run 7 #11: 11, 9 and 7
    valid groups sat unapplied while the next step read ``--implement``).

    *in_progress*: a run of the phase started and did not finish, so its
    command is a ``--resume`` that applies only what that run has not; the
    count is then review-tasks' and the notice says so (fix round 19: it
    said all N were unapplied beside that ``--resume``).
    """
    kind = "valid task suggestion" if valid else "task suggestion"
    noun = "group" if count == 1 else "groups"
    them = "it" if count == 1 else "them"
    changes = "that change" if count == 1 else f"those {count} changes"
    if in_progress:
        return (
            f"review-tasks left {count} {kind} {noun} to apply, and a run of "
            f"--apply-task-suggestions started on {them} and has not finished. "
            "Run --apply-task-suggestions --resume first to apply what that "
            "run has not applied yet; going straight to --implement skips "
            "what is left, and implement then works from the task list as it "
            "stands."
        )
    return (
        f"review-tasks left {count} {kind} {noun} unapplied. Run "
        f"--apply-task-suggestions first to apply {them} to the task list; going "
        f"straight to --implement skips {them}, and implement then works from "
        f"the task list as it stands, without {changes}."
    )


def get_workflow_status(
    state: StateManager, plan_path: Path, plan_dir: Path,
    *, host_id: Optional[str] = None,
) -> dict:
    """Get current workflow state for all phases.

    The first loop reads what ``state.json`` recorded. The post-loop branches
    then mark what the recorded state implies but nothing wrote: an apply phase
    whose review left nothing to apply is ``skipped`` (``apply-suggestions``,
    ``apply-task-suggestions``, ``apply-code-fixes``), and a write phase with
    some of its own batches or tasks recorded ``completed`` is ``in_progress``
    (for an apply phase, unless its last dated run predates its review's latest
    completion).
    ``suggested_next`` is picked once, after every one of those changes, so it
    can never name a phase this payload shows as skipped
    (plans/next-phase-command.md §2.1). A skip ``full`` recorded itself is read
    by the first loop and keeps ``full``'s own reason.

    *host_id* is the reader's host (its ``--host``), handed to
    :func:`repo_wide_sandbox_warning`; None scans ``sys.argv`` as the executor
    does.
    """
    ALL_PHASES = list(PREREQUISITE_PHASES)

    phases = {}

    for phase in ALL_PHASES:
        if state.is_phase_completed(phase):
            timestamp = state.state.get("phases_completed", {}).get(phase, "")
            phases[phase] = {"status": "completed", "timestamp": timestamp}
        elif state.is_phase_skipped(phase):
            skip_info = state.state.get("phases_skipped", {}).get(phase, {})
            phases[phase] = {
                "status": "skipped",
                "reason": skip_info.get("reason", ""),
                "timestamp": skip_info.get("skipped_at", "")
            }
        elif state.phase_completion_is_stale(phase):
            # Recorded completed, but before implement's latest completion
            # (`StateManager.phase_completion_is_stale`): pending, and said
            # so. `status`'s run view used to read the done run under it as
            # "not yet marked completed" and offer its `--reaggregate`, which
            # re-stamps the stale review (adversarial review, 2026-10-02).
            phases[phase] = {
                "status": "pending",
                "stale": True,
                "completed_at": state.state.get("phases_completed", {}).get(phase, ""),
                "implemented_at": state.state.get("phases_completed", {}).get("implement", ""),
            }
        else:
            phases[phase] = {"status": "pending"}
            if phase in OPTIONAL_PHASES:
                phases[phase]["optional"] = True

    # apply-suggestions: a completed review-plan whose every group was judged
    # `invalid` left nothing to apply. Keyed on `open_count`, never on the
    # reason text, and only that one return carries it: no `validation.json`,
    # an unreadable one, or a review whose only groups are
    # `needs-human-decision` (which apply-suggestions presents) marks nothing.
    if (phases["apply-suggestions"]["status"] == "pending"
            and phases["review-plan"]["status"] == "completed"):
        plan_check = check_apply_suggestions_prerequisite(state, plan_dir)
        if plan_check.get("open_count") == 0:
            phases["apply-suggestions"]["status"] = "skipped"
            phases["apply-suggestions"]["reason"] = "skipped (no valid findings)"

    # For apply-task-suggestions phase, determine skip reason from review-tasks state.
    # Cache the prerequisite check result to avoid redundant I/O (used again in notices below).
    cached_task_check = None
    if phases["apply-task-suggestions"]["status"] == "pending":
        if phases["review-tasks"]["status"] == "skipped":
            phases["apply-task-suggestions"]["status"] = "skipped"
            phases["apply-task-suggestions"]["reason"] = "skipped (prerequisite skipped)"
        elif phases["review-tasks"]["status"] == "completed":
            # Check if review-tasks produced actionable findings
            cached_task_check = check_apply_task_suggestions_prerequisite(state, plan_dir)
            if cached_task_check.get("reason") == "skipped (no findings)":
                phases["apply-task-suggestions"]["status"] = "skipped"
                phases["apply-task-suggestions"]["reason"] = "skipped (no findings)"

    # apply-code-fixes: the same two checks, in the same order — the review's
    # own status before any file. A skipped code-review reads nothing (a
    # `grouped.json` left over from an earlier review cannot count), a
    # completed one asks the predicate `full`'s `step_apply_code_fixes` asks,
    # and one that is neither (not run, failed, stopped mid-run) marks nothing.
    if phases["apply-code-fixes"]["status"] == "pending":
        if phases["code-review"]["status"] == "skipped":
            phases["apply-code-fixes"]["status"] = "skipped"
            phases["apply-code-fixes"]["reason"] = "skipped (prerequisite skipped)"
        elif phases["code-review"]["status"] == "completed":
            if not _grouped_has_suggestions(plan_dir / "code-review" / "grouped.json"):
                phases["apply-code-fixes"]["status"] = "skipped"
                phases["apply-code-fixes"]["reason"] = "skipped (no findings)"

    # For implement phase, add task progress. `implementation_task_statuses`
    # (not `get_all_task_statuses`) filters `task_status` to the T### ids the
    # task decomposer owns — the same flat map also carries apply-suggestions/
    # apply-code-fixes/apply-task-suggestions write-batch ids, which are not
    # implement tasks and must never inflate this count.
    if phases["implement"]["status"] in ["pending", "in_progress"]:
        task_status = state.implementation_task_statuses()
        # The denominator is the decomposition implement ran last
        # (`implement_task_ids`, recorded on both legs), not the statuses
        # recorded so far: the native leg records a task only once it ran, so
        # a mid-run `status` on a 10-task plan read `6/6 tasks` where the
        # executor leg, which seeds every task `pending`, read `8/13`
        # (racing re-run 3, fix round 7). A state with no such record keeps
        # the old count, and one with no task recorded and no started record
        # (an `implement --dry-run`) still shows none: a count is what the
        # next-step walk reads as "implement was started".
        current = state.get("implement_task_ids")
        if (isinstance(current, list) and current
                and (task_status or state.is_phase_started("implement"))):
            task_status = {
                str(task_id): task_status.get(str(task_id), "pending")
                for task_id in current
            }
        if task_status:
            tasks_done = sum(1 for s in task_status.values() if s == "completed")
            tasks_total = len(task_status)
            phases["implement"]["tasks_done"] = tasks_done
            phases["implement"]["tasks_total"] = tasks_total
            # Any completed task is progress a bare `--implement` would redo:
            # it re-dispatches every task (`format_batches_for_output` filters
            # only under `--resume`). `done == total` with the phase unmarked
            # is a run whose finalize failed (`driver.verify_command` non-zero,
            # or killed before `mark_phase_completed`); `--resume` dispatches
            # nothing and re-runs the check it owes. Until the adversarial
            # review (2026-10-02) that state read `pending` and the earlier-
            # phase rule routed a later phase's answer to the bare command.
            if tasks_done > 0:
                phases["implement"]["status"] = "in_progress"
        # The native leg's own record (`StateManager.mark_phase_started`): the
        # orchestrator handed the batches to the host and nothing has
        # completed the phase since. A host that died before its first task
        # recorded leaves exactly this and no completed task, and the phase
        # must still read `in_progress` so `--resume` is offered.
        if state.is_phase_started("implement"):
            phases["implement"]["status"] = "in_progress"
            phases["implement"]["started_at"] = state.phase_started_at("implement")

    # The implement tasks the run deferred (a human task, and the dependents
    # `skip-dependents` skipped with it): read from `task_status`, never by
    # re-parsing tasks.md. A workflow that completes with these still owed is
    # complete for the plugin and not for the user, so the next-step builder
    # names them on its `complete` answer and `status` on its trailer line
    # (2026-10-04: `[WORKFLOW_COMPLETE]` said nothing about T011/T012).
    deferred = state.deferred_implementation_tasks()
    if deferred:
        phases["implement"]["manual_tasks"] = deferred
        # The ones `--human-task <id>=done` answers (fix round 16): not a code
        # task skipped with a manual one, which the resume then runs. Fix
        # round 28: and only the ones the user can do now.
        phases["implement"]["manual_close_ids"] = state.manual_tasks_to_close(deferred)
        gates = state.manual_task_gates(deferred)
        if gates is not None:
            # Fix round 28 (live run 12, Codex racing 06): the code tasks
            # each of those waits on, so no note says that nothing waits;
            # a later manual task names the code it comes after; and, while
            # implement is not finished, whether a resume can run nothing
            # until one is recorded done (`manual_gate`).
            if gates["waiting"]:
                phases["implement"]["manual_waiting"] = gates["waiting"]
            for entry in deferred:
                after = gates["after"].get(str(entry.get("id")))
                if after:
                    entry["after"] = list(after)
            if (gates["gated"] and gates["waiting"]
                    and phases["implement"]["status"] not in DONE_STATUSES):
                phases["implement"]["manual_gate"] = True
    # The implement check tasks whose check ran and reported problems
    # (`task_check_findings`, written by both write legs from the reply's
    # structured `check`): racing re-run 4 recorded T007 VERIFIED with two
    # html-validate problems that nothing surfaced. `status` names them on
    # its trailer until review-code, which is given them, has run.
    check_findings = state.implementation_check_findings()
    if check_findings:
        phases["implement"]["check_findings"] = check_findings
    # And the code tasks whose own check failed after their edits
    # (`task_batch_check`, fix round 15): kept edits, nothing held back.
    batch_checks = state.implementation_batch_check_findings()
    if batch_checks:
        phases["implement"]["batch_check_findings"] = batch_checks
    # And the code tasks whose own check reported again only what the user
    # accepted for a check (`task_batch_check_accepted`, fix round 23).
    accepted_reruns = state.implementation_batch_check_accepted()
    if accepted_reruns:
        phases["implement"]["batch_check_accepted"] = accepted_reruns
    # And those whose own check reported only what a check task of the run
    # reported (`task_batch_check_repeats`, fix round 28).
    repeats = state.implementation_batch_check_repeats()
    if repeats:
        phases["implement"]["batch_check_repeats"] = repeats

    notices = []

    # An apply phase with some of its own write batches recorded `completed`
    # — or with a started record, the native leg's note that its batches were
    # handed to the host (`StateManager.mark_phase_started`) — has progress
    # on record: it is `in_progress`, not `pending`, so a command for it
    # carries `--resume` (a bare re-invocation starts the phase over).
    # It records itself completed only once every batch verified
    # (`write_batch_scheduler._finalize`, or the host's `--mark-completed`),
    # and a phase this payload already shows as completed or skipped is left
    # alone. Batches whose phase last ran before its review last completed
    # are an earlier cycle's and mark nothing: `--resume` there would replay
    # that cycle's recorded decisions against the new review's findings. The
    # started record is dated the same way (`_latest_phase_activity`), so an
    # abandoned run from before a review re-run marks nothing either. The
    # rule is `apply_phase_in_progress`, which the composites' inferred
    # `--resume` asks as well.
    for phase in APPLY_BATCH_ID_PATTERNS:
        if phases[phase]["status"] in DONE_STATUSES:
            continue
        if apply_phase_in_progress(state, phase):
            phases[phase]["status"] = "in_progress"
            started_at = state.phase_started_at(phase)
            if started_at:
                phases[phase]["started_at"] = started_at

    # Check for unapplied task suggestions (reuse cached result from above —
    # cached_task_check is always set when review-tasks is completed, so no
    # redundant I/O call is needed here). Read after the loop above, so a
    # run of the phase that started and did not finish is worded as the
    # resume its command is (fix round 19: the count of every valid group
    # sat beside a `--resume` that applies only what is left).
    if (phases["apply-task-suggestions"]["status"] in ("pending", "in_progress")
            and phases["review-tasks"]["status"] == "completed"
            and cached_task_check is not None):
        actionable_count = cached_task_check.get("actionable_count", 0)
        if actionable_count > 0 and not cached_task_check["met"]:
            # F9.5: `actionable_count` is a count of valid GROUPS (see the
            # matching comment on `check_apply_task_suggestions_prerequisite`),
            # so this notice must not call it "suggestions" either.
            notice = unapplied_task_groups_notice(
                actionable_count, valid=bool(cached_task_check.get("counted_valid")),
                in_progress=phases["apply-task-suggestions"]["status"] == "in_progress")
            notices.append(notice)
            # Also on the entry of the phase it concerns, so a reader that
            # needs "which phase is this notice about" (the next-phase
            # builder's `optional_before[].why`) reads a key instead of
            # parsing prose. `notices` itself is unchanged, so `status`
            # output stays the same.
            phases["apply-task-suggestions"]["notice"] = notice

    suggested_next = _suggested_next(phases, ALL_PHASES)

    # Early warning for the two repo-wide write phases (see
    # `repo_wide_sandbox_warning`; the dispatch's own decision, probed once
    # per process): on each open entry it concerns, and once in `notices`,
    # which is what `status` and a terminal poll's `notice` carry.
    open_write_phases = [
        phase for phase in REPO_WIDE_WRITE_PHASES
        if phases[phase]["status"] not in DONE_STATUSES
    ]
    if open_write_phases:
        warning = repo_wide_sandbox_warning(plan_path, plan_dir, host_id=host_id)
        if warning:
            for phase in open_write_phases:
                phases[phase]["warning"] = warning
            notices.append(warning)

    result = {
        "plan": str(plan_path),
        "phases": phases,
        "suggested_next": suggested_next,
        "hint": "Run /clear before starting the next phase for best performance"
    }

    if notices:
        result["notices"] = notices

    return result


def main(argv=None) -> int:
    bootstrap_streams()
    parser = argparse.ArgumentParser(
        description="Check workflow prerequisites",
        parents=[build_parent_parser()],
    )
    parser.add_argument("--plan-file", required=True, help="Path to plan file")
    parser.add_argument("--status", action="store_true",
                        help="Show current workflow state")
    parser.add_argument("--mode", "--phase", required=False,
                        help="Mode word or phase name to check prerequisites "
                             "for (either vocabulary: e.g. review-code or "
                             "code-review). One of: "
                             + ", ".join(PREREQUISITE_PHASES))
    parser.add_argument("--skip", action="store_true",
                        help="Mark the phase as skipped (requires --mode and --reason)")
    parser.add_argument("--reason", type=str, default="",
                        help="Reason for skipping the phase (used with --skip)")
    args = parser.parse_args(argv)

    # `--mode`/`--phase` takes either vocabulary and resolves through the one
    # table that owns both (`modes.py`), so `review-code` (the mode word) and
    # `code-review` (the phase name) select the same gate and cannot drift. An
    # unresolvable word is exit **3** ("this run needs a human"), not argparse's
    # exit 2, which this skill reserves for "nothing to do / already complete".
    # The message goes to stderr so stdout stays pure JSON.
    if args.mode:
        resolved_phase = phase_from_selector(args.mode)
        if resolved_phase not in PREREQUISITE_PHASES:
            print(
                f"ERROR: unknown phase or mode '{args.mode}'. Valid phases: "
                + ", ".join(PREREQUISITE_PHASES),
                file=sys.stderr,
            )
            return EXIT_NEEDS_HUMAN
        args.mode = resolved_phase

    plan_path = Path(args.plan_file).resolve()

    # Handle --status mode
    if args.status:
        if not plan_path.exists():
            result = {"error": f"Plan file not found: {plan_path}"}
            print(json.dumps(result, indent=2))
            sys.exit(1)

        plan_dir = get_output_dir(plan_path)
        state = StateManager(plan_path, read_only=True)
        from utils import host_capabilities
        result = get_workflow_status(
            state, plan_path, plan_dir,
            host_id=host_capabilities.resolve_host_id(explicit=args.host),
        )
        print(json.dumps(result, indent=2))
        sys.exit(0)

    # Validate --mode is provided when not using --status
    if not args.mode:
        print("ERROR: --mode is required unless using --status")
        sys.exit(1)

    # Handle --skip mode: mark a phase as skipped in state
    if args.skip:
        if not args.reason:
            print("ERROR: --reason is required when using --skip")
            sys.exit(1)
        if not plan_path.exists():
            print(f"ERROR: Plan file not found: {plan_path}")
            sys.exit(1)
        state = StateManager(plan_path)
        record_prerequisite_skip(state, args.mode, reason=args.reason)
        result = {
            "skipped": True,
            "mode": args.mode,
            "reason": args.reason,
        }
        print(json.dumps(result, indent=2))
        sys.exit(0)

    if not plan_path.exists():
        result = {
            "prerequisites_met": False,
            "mode": args.mode,
            "error": f"Plan file not found: {plan_path}"
        }
        print(json.dumps(result, indent=2))
        sys.exit(1)

    plan_dir = get_output_dir(plan_path)
    state = StateManager(plan_path)

    # D6a. `--yes` decides how an unmet gate *ends* (exit 3 instead of a rendered
    # question); `--skip-prerequisites` is the separate, explicit escape `--yes`
    # never implies. Attended runs keep today's payload byte-for-byte.
    unattended = bool(getattr(args, "yes", False))
    outcome = ensure_prerequisites(
        plan_path,
        args.mode,
        unattended=unattended,
        skip_prerequisites=bool(getattr(args, "skip_prerequisites", False)),
        state=state,
    )
    missing = outcome.missing

    # Build result — compute prerequisites_met from hard prerequisites only
    result = {
        "prerequisites_met": len(missing) == 0,
        "mode": args.mode,
        "missing": missing
    }
    if outcome.skipped:
        result["skipped_prerequisites"] = list(outcome.skipped)
        result["skip_reason"] = SKIP_PREREQUISITES_REASON
    if outcome.notices:
        result["notices"] = list(outcome.notices)
        for notice in outcome.notices:
            print(notice, file=sys.stderr)
    if outcome.message is not None:
        # stdout stays pure JSON for every caller that json.loads() it; the
        # verbatim block goes to stderr and travels here as `message`.
        result["message"] = outcome.message
        result["gate_row"] = GATE_ROW.get(args.mode)
        print(outcome.message, file=sys.stderr)
    if outcome.exit_code == EXIT_NEEDS_HUMAN:
        result["state"] = "needs-human"
        result["exit"] = EXIT_NEEDS_HUMAN
        unattended_mod.mark_needs_human(args.mode)
        print(json.dumps(result, indent=2))
        return EXIT_NEEDS_HUMAN

    # For implement mode, also check for unapplied task suggestions (soft advisory)
    # apply-task-suggestions is NOT a hard prerequisite for implement, but we
    # surface it as an advisory prompt so users can apply task review findings first.
    # Advisories are appended AFTER prerequisites_met is computed so they don't
    # turn a soft prompt into a hard failure.
    advisories = []
    if args.mode == "implement":
        task_check = check_apply_task_suggestions_prerequisite(state, plan_dir)
        if not task_check["met"]:
            advisories.append({
                "phase": "apply-task-suggestions",
                "reason": task_check["reason"],
                "actionable_count": task_check.get("actionable_count", 0),
                "importance_breakdown": task_check.get("importance_breakdown", {})
            })

    if advisories:
        result["advisories"] = advisories

    # Add prompt if there are missing prerequisites that need user input.
    # Check hard prerequisites first; only fall back to advisory prompt if no
    # hard prerequisite prompt exists. Advisory prompts are tagged so callers
    # can distinguish them from blocking prerequisite prompts.
    #
    # D6b: under `--yes` **no prompt object is emitted at all** — not an empty
    # one, not a "resolved" one. A payload the caller could render is a question
    # waiting to happen, so the resolution travels as `resolution` instead. Row 7
    # (the task-suggestion advisory) auto-resolves to "skip, phase recorded
    # skipped"; the recording belongs to the phase that owns it
    # (`implement_orchestrator.py`), not to this read-only check.
    if unattended:
        resolutions = []
        if advisories:
            resolutions.append({
                "site": unattended_mod.row(7).site_id,
                "decision": "skip the task-suggestion advisory and proceed",
            })
        if resolutions:
            result["resolutions"] = resolutions
    else:
        prompt = build_prompt(args.mode, missing)
        if prompt:
            result["prompt"] = prompt
        elif advisories:
            advisory_prompt = build_prompt(args.mode, advisories)
            if advisory_prompt:
                advisory_prompt["advisory"] = True
                result["prompt"] = advisory_prompt

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
