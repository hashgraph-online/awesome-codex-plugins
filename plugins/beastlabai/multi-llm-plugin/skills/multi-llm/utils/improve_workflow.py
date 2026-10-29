"""``--improve-plan``, ``--improve-code`` and ``--improve-commits``: one review, then its apply, unattended.

Each composite runs two phases that already exist, in the order its ``modes.py``
row's ``sequence`` names them: ``review-plan`` then ``apply-suggestions``, or
``review-code`` then ``apply-code-fixes``. Two legs run them. The executor leg
(the tool routes, any call with ``--exec-subagents``) is :class:`ImproveWorkflow`,
``full``'s state machine with the composite's own identity, steps and flags.
The native leg (Claude Code and the file shims) is an instruction core that
loads each phase's core in turn, planned by ``util improve-steps``.

Which composites exist, which of them takes a review scope and which step
method runs each word are read off the mode table (each composite row's
``sequence``), never listed here, so a composite is added by adding its row.
``improve-commits`` is ``improve-code``'s sequence behind a commit front door
(plans/review-commits.md §2.8): its front door resolves the range, writes the
commit brief that stands in for the plan, and hands :func:`entry_point`
``--plan-file <brief> --base-ref <base> --head-ref <head>``. Everything that
differs for it keys on the row's range positional (:func:`pins_commit_range`)
or on the brief's ``commit_range`` record, never on its name.

Every rule both legs follow lives here, once, as a function of the mode word,
the parsed flags and :class:`Records`, the state read once before step 1:

* :func:`skip_reason` decides whether a step runs (§2.3 of the plan);
* :func:`step_flags` decides the flags it gets (§2.2);
* :func:`continuation_flags` is the command a stop names (row 14);
* :func:`plan_steps` is the per-step plan with its reasons, for the planner.

The executor never reads the reasons, only :func:`skip_reason`'s answer, so
the two legs cannot plan one state two ways. :func:`read_records` is the one
reader of that state, and it refuses a ``state.json`` it cannot read
(:class:`StateReadError`) rather than plan from nothing.

Every message a composite prints is filled from its mode row, never typed per
mode, so a third composite gets them by adding a row.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Optional, Sequence, Tuple, Union

import check_workflow_prerequisites as prereq
import full_workflow_orchestrator as fwo
import modes as mode_table

from . import detach, process_control, status_file
from . import unattended as unattended_mod
from .cli_common import (
    AGENT_DECIDE_FLAG,
    EXIT_ERROR,
    EXIT_NEEDS_HUMAN,
    EXIT_NOTHING_TO_DO,
    LEGACY_AGENT_DECIDE_FLAGS,
    add_notice,
    build_parent_parser,
    dispatcher_prefix,
)
from .output_handler import (
    PHASE_DIRECTORIES,
    get_phase_dir,
    output_dir_path,
    phase_dir_path,
)
from .state_manager import StateManager, _parse_completion_time

#: The step word of review-plan's advisory consolidation pass. Not a mode and
#: not in any ``sequence``: it is ``review-plan --consolidate``, run between the
#: review and the apply when the review recommends it (row 4).
CONSOLIDATE = "consolidate"

#: The reviews that have a consolidation pass (``supports_consolidation`` is
#: true only in ``review_plan_orchestrator``).
_CONSOLIDATING_REVIEWS = ("review-plan",)


def _is_review_then_apply(row: "mode_table.Mode") -> bool:
    """A composite of two steps, a review then the apply of its findings.

    ``full`` is a composite too, but it runs the whole workflow through its own
    driver (``runs_workflow``), so it is never one of these.
    """
    return row.is_composite and not row.runs_workflow and len(row.sequence) == 2


#: Every review-then-apply composite row, in table order: ``improve-plan``,
#: ``improve-code``, ``improve-commits``. Read off the table, so a composite is
#: added by adding its row; ``util improve-steps``' ``--mode`` choices are
#: these rows' names.
COMPOSITE_ROWS: Tuple["mode_table.Mode", ...] = tuple(
    row for row in mode_table.MODES if _is_review_then_apply(row)
)


def _derive_scoped_review() -> str:
    """The review that takes a scope (``--files``/``--files-from``/``--base-ref``).

    review-code's: the review of the code the workflow ends on, i.e. the first
    step of every composite whose apply is the workflow's last phase (the last
    word of the ``runs_workflow`` row's ``sequence``, ``apply-code-fixes``).
    improve-code and improve-commits both run it first, so both are scoped
    composites; improve-plan's review takes no scope. Exactly one review may
    answer, so a row that broke the pairing fails at import, not in a run.
    """
    workflow = next(row for row in mode_table.MODES if row.runs_workflow)
    reviews = {
        row.sequence[0] for row in COMPOSITE_ROWS
        if row.sequence[-1] == workflow.sequence[-1]
    }
    if len(reviews) != 1:  # pragma: no cover - table-guarded
        raise RuntimeError(f"no single scoped review in the mode table: {sorted(reviews)}")
    return reviews.pop()


#: The review that takes a scope (``--files``/``--files-from``/``--base-ref``):
#: ``review-code``, derived from the table (:func:`_derive_scoped_review`).
_SCOPED_REVIEW = _derive_scoped_review()

#: Which inherited ``FullWorkflow`` step runs each sequence word: ``step_`` and
#: the word in snake case, for every word of every composite's ``sequence``
#: (``review-code`` → ``step_review_code``). A word with no such method fails
#: the step build, and ``tests/test_improve_commits.py`` holds every entry to
#: one.
_STEP_METHODS: Dict[str, str] = {
    word: "step_" + word.replace("-", "_")
    for row in COMPOSITE_ROWS for word in row.sequence
}

#: ``detach.classify_run`` verdicts that mean a run is still writing its dir.
_LIVE_VERDICTS = (detach.VERDICT_STARTING, detach.VERDICT_RUNNING, detach.VERDICT_STALE)

#: How many times a step tries its phase dir's lock, and how far apart, before
#: the live-run refusal (about 100 ms in all). ``detach.classify_run`` probes
#: every phase dir's lock on each ``status`` poll by taking and dropping it, so
#: one refusal can be a probe, not a run.
STEP_LOCK_ATTEMPTS = 5
STEP_LOCK_RETRY_S = 0.025

#: The decisions :func:`plan_steps` gives a step.
RUN = "run"
SKIP = "skip"
AFTER_REVIEW = "after-review"


# ---------------------------------------------------------------------------
# The row
# ---------------------------------------------------------------------------

def _row(mode: str) -> "mode_table.Mode":
    """The composite row for *mode*: a review, then the apply of its findings.

    ``full`` is a composite too, but it runs the whole workflow through its own
    driver, so it is refused here rather than half-planned.
    """
    row = mode_table.resolve(str(mode))
    if row is None or not _is_review_then_apply(row):
        raise ValueError(f"{mode!r} is not a review-then-apply composite mode")
    return row


def _reviews_code(mode: str) -> bool:
    """Whether *mode*'s review takes a scope (its first step is review-code)."""
    return _row(mode).sequence[0] == _SCOPED_REVIEW


def pins_commit_range(mode: str) -> bool:
    """Whether a commit front door pins *mode*'s range (``improve-commits``).

    Read off the row: its positional is a range (``modes.POS_REVS``), not a
    plan, so its front door resolves the range, records ``commit_range`` in the
    brief's ``state.json`` and synthesises ``--plan-file``, ``--base-ref`` and
    ``--head-ref`` on every call, a resume included (plans/review-commits.md
    §2.1). Those three are therefore never the user's: no continuation
    carries them, and the user reads the steps as the commit modes
    (``commit_spelling.step_word`` keys on the same positional).
    """
    return tuple(_row(mode).positionals) == (mode_table.POS_REVS,)


def _step_word(mode: str, word: str) -> str:
    """A sequence word as a line the user reads spells it: the commit mode on a
    composite whose range a front door pins (``review-code`` →
    ``review-commits``), else the word itself (``commit_spelling.step_word``,
    the row-keyed mapping of plans/review-commits.md §2.8)."""
    from .commit_spelling import step_word

    return step_word(_row(mode).name, word)


def step_indices(mode: str) -> List[Tuple[str, str]]:
    """``(index, step word)`` for every step *mode* runs, in order.

    The ``sequence`` words, numbered ``1`` and ``2``, with review-plan's
    consolidation pass between them as ``1b``. The executor's steps and the
    planner's step blocks are both built from this one list.
    """
    review, apply = _row(mode).sequence
    steps = [("1", review)]
    if review in _CONSOLIDATING_REVIEWS:
        steps.append(("1b", CONSOLIDATE))
    steps.append(("2", apply))
    return steps


def review_phase_for(apply_step: str) -> str:
    """The ``state.json`` phase word of the review whose findings *apply_step* applies.

    Mode word, then phase word, then write kind, then the scheduler's review
    pairing, so the pair is never typed a second time. Reading the scheduler's
    map with the mode word raises ``KeyError``, and asking
    ``is_phase_completed("review-code")`` reads false forever (the phase word is
    ``code-review``); this one lookup is how neither mistake is made. Kept here
    rather than in ``state_manager``, which ``write_batch_scheduler`` imports.
    """
    from .subagent_tasks import WRITE_KIND_BY_PHASE
    from .write_batch_scheduler import REVIEW_PHASE_BY_WRITE_KIND

    phase = mode_table.phase_for(apply_step)
    return REVIEW_PHASE_BY_WRITE_KIND[WRITE_KIND_BY_PHASE[phase]]


# ---------------------------------------------------------------------------
# Records: the state, read once before step 1
# ---------------------------------------------------------------------------

class StateReadError(Exception):
    """A ``state.json`` the composite cannot plan from.

    Read through ``StateManager`` as it is, such a file goes one of two wrong
    ways: text that is not JSON becomes a fresh initial state, so every step
    would plan as ``run`` and the driver's first progress save would overwrite
    every record in it; a value of the wrong shape raises ``AttributeError``
    at the first ``.get``. So the file is read here first, and refused.
    """

    def __init__(self, path: Union[str, Path], detail: str):
        super().__init__(f"{path}: {detail}")
        self.path = str(path)
        self.detail = detail


def _json_kind(value: Any) -> str:
    """How an error names a JSON value's type: ``a list``, ``a string``, …"""
    if isinstance(value, bool):
        return "a boolean"
    if isinstance(value, (int, float)):
        return "a number"
    if isinstance(value, str):
        return "a string"
    if isinstance(value, list):
        return "a list"
    if value is None:
        return "null"
    return "an object"


#: The top-level keys :func:`read_records` reads as objects, through
#: ``StateManager`` and ``check_workflow_prerequisites.apply_phase_in_progress``.
#: Fable review 2026-10-09: only the first two were checked, so a ``task_status``
#: list passed and then raised at ``get_all_task_statuses().items()``, a
#: traceback at exit 1 on both legs. The other three are read defensively
#: today, but the steps that run next write into them as objects.
STATE_OBJECT_KEYS = (
    "phases_completed",
    "phases_skipped",
    "phases_started",
    "task_status",
    "metrics_progress",
    "metrics",
)


def read_state_document(path: Union[str, Path]) -> Optional[Dict[str, Any]]:
    """``state.json`` as a dict, ``None`` when there is no file, else :class:`StateReadError`.

    A missing file is no records: nothing has run yet. A missing key of
    :data:`STATE_OBJECT_KEYS` reads as empty, as ``StateManager`` reads it; a
    present one that is not an object is refused. A date that does not parse
    is not an error either: :meth:`StateManager.completion_predates` keeps
    such an apply done.
    """
    path = Path(path)
    try:
        raw = path.read_bytes()
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise StateReadError(path, str(exc)) from exc
    try:
        document = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise StateReadError(path, str(exc)) from exc
    if not isinstance(document, dict):
        raise StateReadError(
            path, f"the top-level value is {_json_kind(document)}, not an object"
        )
    for key in STATE_OBJECT_KEYS:
        if key in document and not isinstance(document[key], dict):
            raise StateReadError(
                path, f"{key} is {_json_kind(document[key])}, not an object"
            )
    return document


@dataclass(frozen=True)
class Records:
    """What both legs plan from: ``state.json`` and the review's files, read once.

    Read before step 1 (:func:`read_records`) and never again in that process,
    so the apply step's answer after step 1 has run is the one the planner
    printed. Every field has a default, so a test builds the state it means
    without a plan on disk.

    Attributes:
        mode: The composite's mode word.
        review_completed: ``is_phase_completed`` of the review's phase word,
            so a code review older than the latest implement reads ``False``.
        review_completed_at: ``phases_completed[review]`` as recorded, for
            ``[ALREADY_COMPLETE]``; ``None`` when there is none.
        review_on_record: Whether ``phases_completed`` holds the review at all,
            stale or not. review-code's leftover-``validation.json`` ``--force``
            is for a review with none.
        review_skipped: Whether ``phases_skipped`` holds the review.
        review_stale: ``phase_completion_is_stale`` of the review: a code
            review completed before the latest implement.
        review_started: Whether the review's phase dir holds a ``.status.json``,
            which every fan-out writes when it starts (display only).
        leftover_validation: Whether ``{review dir}/validation.json`` is on
            disk (a retired ``validation.<stamp>.stale.json`` does not count).
        leftover_results: improve-code and improve-commits only: per-model
            result files in the code review's dir with no ``grouped.json``
            beside them, what a fan-out stopped before grouping leaves
            (``code_review_orchestrator.leftover_model_results``). review-code
            refuses a plain re-run over them (exit 3), so the step resumes with
            ``--force``.
        apply_started: ``is_phase_started`` of the apply: a start newer than
            its completion, or with none beside it.
        apply_word: ``completed`` or ``skipped``, the word of the apply's
            newer record; ``None`` when it has neither.
        apply_word_at: That same record's stamp, as recorded.
        apply_predates_review: ``completion_predates(apply, review)``.
        apply_in_progress: ``apply_phase_in_progress``: progress of the review
            on record, the inferred ``--resume``'s condition.
        requested_scope: The typed ``--files``/``--files-from`` scope, made
            repo-relative by the phase's own reader; ``None`` when no scope flag
            is typed, and for ``--files-from -``, which is never read here.
        recorded_scope: ``review_scope_files``, cleaned as
            ``resolve_review_scope`` cleans it; ``None`` for the default scope.
        recorded_base_ref: The ``base_ref`` of ``code-review/review-scope.md``;
            ``None`` when that manifest is missing, unreadable or empty.
        consolidation_skip: improve-plan only: why the consolidation pass would
            not run on the review files on disk now
            (``full_workflow_orchestrator.consolidation_skip_reason``), ``None``
            when it would.
        header_changed: A composite whose range a front door pins
            (:func:`pins_commit_range`) only: the brief's
            ``commit_range.header_sha256`` differs from the
            ``reviewed_header_sha256`` the review on record answered (a changed
            ``--focus`` or context plan, plans/review-commits.md §2.4), so the
            review starts a new round, as under ``--force``. ``False`` when no
            round has started yet (no ``reviewed_header_sha256``), and on every
            other composite.
    """

    mode: str
    review_completed: bool = False
    review_completed_at: Optional[str] = None
    review_on_record: bool = False
    review_skipped: bool = False
    review_stale: bool = False
    review_started: bool = False
    leftover_validation: bool = False
    leftover_results: bool = False
    apply_started: bool = False
    apply_word: Optional[str] = None
    apply_word_at: Optional[str] = None
    apply_predates_review: bool = False
    apply_in_progress: bool = False
    requested_scope: Optional[Tuple[str, ...]] = None
    recorded_scope: Optional[Tuple[str, ...]] = None
    recorded_base_ref: Optional[str] = None
    consolidation_skip: Optional[str] = None
    header_changed: bool = False


def _header_changed(mode: str, document: Dict[str, Any]) -> bool:
    """:attr:`Records.header_changed` from the ``state.json`` document.

    Read only on a composite whose range a front door pins, so improve-plan
    and improve-code plan exactly as they did, on a commit brief too.
    """
    if not pins_commit_range(mode):
        return False
    record = document.get("commit_range")
    if not isinstance(record, dict):
        return False
    reviewed = record.get("reviewed_header_sha256")
    if not isinstance(reviewed, str) or not reviewed:
        return False
    return record.get("header_sha256") != reviewed


def _stamp_text(value: Any) -> str:
    """A recorded stamp as printed: the string itself, or ``(no date)``."""
    return value if isinstance(value, str) and value else "(no date)"


def _newer_apply_record(
    completed: Dict[str, Any], skipped: Dict[str, Any], phase: str
) -> Tuple[Optional[str], Optional[str]]:
    """``(word, stamp)`` of *phase*'s newer record, or ``(None, None)``.

    Both records can be on file at once (``mark_phase_completed`` leaves an
    older skip in place), and the newer one is the state the run is in: an
    apply skipped after an earlier cycle's completion is skipped. When either
    date does not parse, ``_recorded``'s precedence decides (completed wins).
    """
    has_completion = phase in completed
    record = skipped.get(phase)
    has_skip = phase in skipped
    skipped_at = record.get("skipped_at") if isinstance(record, dict) else None
    if has_completion and has_skip:
        done = _parse_completion_time(completed[phase])
        passed = _parse_completion_time(skipped_at)
        if done is not None and passed is not None and passed > done:
            return "skipped", _stamp_text(skipped_at)
        return "completed", _stamp_text(completed[phase])
    if has_completion:
        return "completed", _stamp_text(completed[phase])
    if has_skip:
        return "skipped", _stamp_text(skipped_at)
    return None, None


def _requested_scope(
    mode: str, plan: Path, args: argparse.Namespace
) -> Optional[Tuple[str, ...]]:
    """The typed scope, through review-code's own reader and root; or ``None``.

    The same repo-relative, de-duplicated list the phase will record, so a
    comparison with ``review_scope_files`` compares like with like. Raises the
    phase's ``ScopeFilesError`` for a scope it cannot read. ``--files-from -``
    is never read: the phase is stdin's only reader, and a list read here for
    the comparison would be gone when the phase reads it. Its ``--files``
    beside it are still checked, so a path outside the repository fails
    before any step.
    """
    if not _reviews_code(mode):
        return None
    files = [item for item in (getattr(args, "files", None) or []) if item is not None]
    files_from = getattr(args, "files_from", None)
    if not files and files_from is None:
        return None
    import code_review_orchestrator as review_code

    from .git_utils import get_project_root

    root = review_code.review_git_root(get_project_root(str(plan))) or os.getcwd()
    if files_from == "-":
        if files:
            review_code.read_scope_files_flags(
                argparse.Namespace(files=files, files_from=None, detach=False), root
            )
        return None
    return tuple(review_code.read_scope_files_flags(args, root) or ())


def _recorded_base_ref(mode: str, plan: Path) -> Optional[str]:
    """The ref the code review on record diffed against, from its manifest."""
    if not _reviews_code(mode):
        return None
    from .git_utils import REVIEW_SCOPE_FILENAME, read_review_scope

    review_dir = phase_dir_path(plan, _row(mode).sequence_phases[0])
    header = read_review_scope(review_dir / REVIEW_SCOPE_FILENAME)
    return (header.base_ref or None) if header is not None else None


def _leftover_results(mode: str, review_dir: Path) -> bool:
    """:attr:`Records.leftover_results`: per-model files, no ``grouped.json``.

    Fable review, finding 1 (2026-10-27): a fan-out stopped before grouping (on
    Claude Code, at the background launch's time limit) leaves only per-model
    files. ``--resume`` handed the review step ``--yes`` alone, review-code's
    partial-completion guard refused it (exit 3, "Run: --reaggregate"), and the
    composite's stop named ``[IMPROVE_RERUN]`` again: a loop. review-plan has no
    such guard and resumes a plain re-run, so only the code review reads this.
    """
    if not _reviews_code(mode) or (review_dir / "grouped.json").exists():
        return False
    import code_review_orchestrator as review_code

    return bool(review_code.leftover_model_results(review_dir))


def read_records(
    mode: str, plan_path: Union[str, Path], args: argparse.Namespace
) -> Records:
    """The one reader of what both legs plan from.

    ``state.json`` first, before the typed scope, the phase dirs or any
    ``StateManager``: a file it cannot read raises :class:`StateReadError` and
    nothing else is read. Then the typed scope, which raises review-code's
    ``ScopeFilesError`` (improve-code only). Reads only: nothing is created,
    the output dir included, so ``util improve-steps`` stays read-only.
    """
    row = _row(mode)
    review_phase, apply_phase = row.sequence_phases
    plan = Path(os.path.abspath(str(plan_path))).resolve()
    plan_dir = output_dir_path(plan)
    document = read_state_document(plan_dir / "state.json")
    requested = _requested_scope(row.name, plan, args)
    review_dir = phase_dir_path(plan, review_phase)
    on_disk = dict(
        mode=row.name,
        review_started=os.path.isfile(status_file.status_path(str(review_dir))),
        leftover_validation=(review_dir / "validation.json").is_file(),
        leftover_results=_leftover_results(row.name, review_dir),
        requested_scope=requested,
        recorded_base_ref=_recorded_base_ref(row.name, plan),
        consolidation_skip=(
            fwo.consolidation_skip_reason(plan_dir)
            if row.sequence[0] in _CONSOLIDATING_REVIEWS else None
        ),
    )
    if document is None:
        return Records(**on_disk)

    state = StateManager(plan, read_only=True)
    paired = review_phase_for(row.sequence[-1])
    completed = state.state.get("phases_completed") or {}
    skipped = state.state.get("phases_skipped") or {}
    apply_word, apply_word_at = _newer_apply_record(completed, skipped, apply_phase)
    recorded_scope = None
    if _reviews_code(row.name):
        from code_review_orchestrator import REVIEW_SCOPE_FILES_KEY

        recorded = state.get(REVIEW_SCOPE_FILES_KEY)
        if isinstance(recorded, list):
            cleaned = tuple(dict.fromkeys(
                item for item in recorded if isinstance(item, str) and item.strip()
            ))
            recorded_scope = cleaned or None
    return Records(
        **on_disk,
        review_completed=state.is_phase_completed(review_phase),
        review_completed_at=(
            _stamp_text(completed[review_phase]) if review_phase in completed else None
        ),
        review_on_record=review_phase in completed,
        review_skipped=review_phase in skipped,
        review_stale=state.phase_completion_is_stale(review_phase),
        apply_started=state.is_phase_started(apply_phase),
        apply_word=apply_word,
        apply_word_at=apply_word_at,
        apply_predates_review=state.completion_predates(apply_phase, paired),
        apply_in_progress=prereq.apply_phase_in_progress(state, apply_phase),
        recorded_scope=recorded_scope,
        header_changed=_header_changed(row.name, document),
    )


# ---------------------------------------------------------------------------
# The rules: pure, and shared by both legs
# ---------------------------------------------------------------------------

def scope_flags_typed(args: argparse.Namespace) -> bool:
    """Whether ``--files`` or ``--files-from`` was typed (``--base-ref`` is not scope)."""
    return bool(getattr(args, "files", None)) or getattr(args, "files_from", None) is not None


def new_round(args: argparse.Namespace, records: Records) -> bool:
    """Whether the review starts a new round: ``--force``, or a changed commit brief.

    :attr:`Records.header_changed` is the commit-brief half (improve-commits):
    the header the review on record answered is not the brief's now, which is
    what the front door's restart passes ``--force`` for, so the native leg
    (which never meets the front door) and a re-run after a restart that was
    cut off before its round began both start the round too. It is never
    true on improve-plan or improve-code.
    """
    return bool(getattr(args, "force", False)) or records.header_changed


def scope_changed(mode: str, args: argparse.Namespace, records: Records) -> bool:
    """A completed code review whose recorded scope differs from the typed one.

    Compared as sets: ``order_review_paths`` sets the review order, so the order
    typed changes nothing. No scope on record is the default scope, which any
    typed list differs from. Never on a new round (:func:`new_round`), where
    nothing is compared, and never for ``--files-from -``, which is not read.
    """
    if not _reviews_code(mode) or new_round(args, records):
        return False
    if not records.review_completed or records.requested_scope is None:
        return False
    return set(records.requested_scope) != set(records.recorded_scope or ())


def skip_reason(
    mode: str, step: str, args: argparse.Namespace, records: Records
) -> Optional[str]:
    """``completed`` or ``skipped`` to pass over *step*, or ``None`` to run it.

    *step* is a word of the mode's ``sequence``. Pure: it reads ``--force``
    and *records* and nothing else.

    A review runs unless it is completed, the round is not new
    (:func:`new_round`: ``--force``, or a changed commit brief), and (code
    review) no typed scope differs from the one on record. A review on record
    only as skipped therefore runs, unlike under ``full``: its skip holds no
    findings, and the command's first half is that review.

    An apply runs when, in this order: its review runs (that review will be
    newer than any apply record, so neither leg reads ``state.json`` again
    after step 1); it is started and not finished; it has neither record; or
    every record of it predates the review. Otherwise it is passed over with
    the word of its newer record.
    """
    review, apply = _row(mode).sequence
    if step == review:
        if not records.review_completed or new_round(args, records):
            return None
        if scope_changed(mode, args, records):
            return None
        return "completed"
    if step == apply:
        if skip_reason(mode, review, args, records) is None:
            return None
        if records.apply_started or records.apply_word is None:
            return None
        if records.apply_predates_review:
            return None
        return records.apply_word
    raise ValueError(f"{step!r} is not a step of {mode}'s sequence")


def nothing_to_do(mode: str, args: argparse.Namespace, records: Records) -> bool:
    """Whether :func:`skip_reason` passes over every step of ``sequence``.

    The consolidation pass is not in ``sequence`` and never counts: a finished
    run exits 2 even with a recommendation still open.
    """
    return all(
        skip_reason(mode, word, args, records) for word in _row(mode).sequence
    )


def review_runs(mode: str, args: argparse.Namespace, records: Records) -> bool:
    """Whether step 1 runs: the condition every apply-side flag branches on."""
    return skip_reason(mode, _row(mode).sequence[0], args, records) is None


def step_flags(
    mode: str, step: str, args: argparse.Namespace, records: Records
) -> List[str]:
    """The flags after the plan that *step* gets, on both legs; pure.

    *step* is a word of ``sequence``, or :data:`CONSOLIDATE`. Never a flag of
    the cross-cutting tail (:func:`cross_cutting_flags`), never ``--detach``
    or an ``--internal-*`` token, and never ``--interactive``.

    review: ``--yes``; ``--models …``, else ``--quick``; ``--force
    --rerun-all`` on a new round (:func:`new_round`). review-code also gets
    the typed ``--files`` (in the order typed), ``--files-from``,
    ``--base-ref`` and ``--head-ref`` (the last only ever the front door's,
    on improve-commits); ``--force`` alone for a changed scope, over a
    ``validation.json`` with no completion on record (its secondary guard
    would otherwise auto-heal the earlier round's results), or over
    per-model results with no ``grouped.json`` (:attr:`Records.leftover_results`:
    the guard would refuse the re-run, and ``--force`` resumes it, each kept
    file a ``[SKIP]``); and, with no
    scope flag typed, the recorded ``review_scope_files`` when it resumes an
    unfinished review. A stale code review gets no force: it forces itself.

    consolidation: ``--consolidate --yes``.

    apply: ``--yes --agent-decide --no-confirm``; ``--resume`` only when step
    1 is passed over, typed or inferred from the apply in progress (after a
    review that ran, the apply starts a new cycle); never ``--force`` or
    ``--fresh``. apply-code-fixes also gets ``--base-ref``: the typed one, else,
    when step 1 is passed over, the one the code review on record used. The
    improve-commits front door passes its pinned base (the empty-tree id on a
    root range) on every call, and ``util improve-steps`` sets the same from
    ``commit_range``, so on that composite the first branch always answers
    (plans/review-commits.md §2.8); the rule itself names no mode.
    """
    row = _row(mode)
    review, apply = row.sequence
    fresh_round = new_round(args, records)
    if step == CONSOLIDATE and review in _CONSOLIDATING_REVIEWS:
        return ["--consolidate", "--yes"]
    if step == review:
        flags = ["--yes"]
        if getattr(args, "models", None):
            flags += ["--models", *args.models]
        elif getattr(args, "quick", False):
            flags += ["--quick"]
        if fresh_round:
            flags += ["--force", "--rerun-all"]
        if review != _SCOPED_REVIEW:
            return flags
        if not fresh_round and (
            scope_changed(mode, args, records)
            or (records.leftover_validation and not records.review_on_record)
            or (records.leftover_results and not records.review_on_record)
        ):
            flags += ["--force"]
        for path in getattr(args, "files", None) or []:
            flags += ["--files", path]
        if getattr(args, "files_from", None) is not None:
            flags += ["--files-from", args.files_from]
        if (
            not scope_flags_typed(args)
            and not fresh_round
            and not records.review_stale
            and records.recorded_scope
            and skip_reason(mode, review, args, records) is None
        ):
            for path in records.recorded_scope:
                flags += ["--files", path]
        if getattr(args, "base_ref", None):
            flags += ["--base-ref", args.base_ref]
        if getattr(args, "head_ref", None):
            flags += ["--head-ref", args.head_ref]
        return flags
    if step == apply:
        flags = ["--yes", AGENT_DECIDE_FLAG, "--no-confirm"]
        passed_over = not review_runs(mode, args, records)
        if passed_over and (getattr(args, "resume", False) or records.apply_in_progress):
            flags += ["--resume"]
        if review == _SCOPED_REVIEW:
            if getattr(args, "base_ref", None):
                flags += ["--base-ref", args.base_ref]
            elif passed_over and records.recorded_base_ref:
                flags += ["--base-ref", records.recorded_base_ref]
        return flags
    raise ValueError(f"no step_flags for step {step!r} of {mode}")


def cross_cutting_flags(args: argparse.Namespace, *, include_host: bool = True) -> List[str]:
    """The tail every step gets: ``--host <id>``, ``--exec-subagents``, ``--dry-run-subagents``.

    A closed list, in ``full``'s ``common_flags`` order, and built here rather
    than through ``common_flags``, which also emits ``--yes`` (``step_flags``
    owns it, once), ``--interactive`` (refused before any step) and
    ``--skip-prerequisites`` (no phase of either sequence has a gate that reads
    it). The native leg's flags lines leave the ``--host`` pair out
    (``include_host=False``): the phase core's launch step takes it from the
    host's dispatcher command.
    """
    flags: List[str] = []
    if include_host and getattr(args, "host", None):
        flags += ["--host", str(args.host)]
    if getattr(args, "exec_subagents", False):
        flags += ["--exec-subagents"]
    if getattr(args, "dry_run_subagents", False):
        flags += ["--dry-run-subagents"]
    return flags


def continuation_flags(mode: str, args: argparse.Namespace) -> List[str]:
    """The flags after the plan in the command a stop names (D6 row 14).

    The selectors the user typed (``--models``, ``--quick``, and for
    improve-code ``--files``, ``--files-from``, ``--base-ref``), never
    ``--force``, which would start another round, then ``--resume`` once. No
    ``--yes`` (implied) and no cross-cutting flag (a route re-adds its own).
    The recorded ``review_scope_files`` is never carried: the resumed run reads
    the record again.

    ``--files-from -`` is left out (a ``--files-from <file>`` stays): the
    printed command carries no stdin, so typed in a shell it would wait on a
    list it never mentions, and on a route that composes ``--detach`` a
    review it runs refuses ``-`` (:func:`files_from_stdin_refused`).
    :func:`continuation_stdin_note` is the line that says so.

    On a composite whose range a front door pins (:func:`pins_commit_range`,
    improve-commits) the parsed ``--base-ref`` and ``--head-ref`` are the
    front door's, never typed (it refuses typed ones, so a command holding
    one would fail), and are left out; the range itself is the command's
    positional, which :func:`continuation_args` spells as the pinned range.
    ``--focus`` and ``--context-plan`` never reach this parser: the brief
    inherits them (plans/review-commits.md §2.8, "The continuation").
    """
    flags: List[str] = []
    if getattr(args, "models", None):
        flags += ["--models", *args.models]
    if getattr(args, "quick", False):
        flags += ["--quick"]
    if _reviews_code(mode):
        for path in getattr(args, "files", None) or []:
            flags += ["--files", path]
        files_from = getattr(args, "files_from", None)
        if files_from is not None and files_from != "-":
            flags += ["--files-from", files_from]
        if getattr(args, "base_ref", None) and not pins_commit_range(mode):
            flags += ["--base-ref", args.base_ref]
    flags.append("--resume")
    return flags


def continuation_args(
    mode: str,
    plan: Union[str, Path],
    args: argparse.Namespace,
    *,
    plan_arg: Optional[Union[str, Path]] = None,
) -> Tuple[str, List[str]]:
    """``(mode word, [plan or range, *flags])``: the continuation as a command.

    *plan* is the plan (or commit brief) path, read for its ``commit_range``;
    *plan_arg* is how the command spells it (default *plan*). The flags are
    :func:`continuation_flags`. On a composite whose range a front door pins,
    the brief's ``commit_range`` turns the positional into the pinned
    ``<base12>..<head12>`` (the brief, as spelled, for a root range) and drops
    every flag a front door owns, through ``commit_spelling.spell_args``, the
    one owner of that mapping: so the row-14 stop, ``[IMPROVE_RERUN]`` and a
    detached run's resume line read ``--improve-commits <base12>..<head12>
    --resume`` plus the typed selectors. With no ``commit_range`` yet (a new
    brief whose stage a worker has not applied) the brief path stands as the
    range, which the front door also takes. Every other composite comes back
    as ``(mode, [plan_arg, *flags])``, unchanged.
    """
    from . import commit_spelling

    flags = continuation_flags(mode, args)
    shown = plan if plan_arg is None else plan_arg
    view = (
        commit_spelling.commit_view(plan, plan=shown)
        if pins_commit_range(mode) else None
    )
    return commit_spelling.spell_args(_row(mode).name, shown, flags, view)


def continuation_command(
    mode: str,
    plan: Union[str, Path],
    args: argparse.Namespace,
    *,
    base: Optional[Path] = None,
) -> str:
    """:func:`continuation_args` as the dispatcher command a stop names."""
    from .cli_common import dispatcher_command

    word, rest = continuation_args(mode, plan, args)
    return dispatcher_command(word, *rest, base=base)


def continuation_stdin_note(mode: str, args: argparse.Namespace) -> Optional[str]:
    """The line under a continuation that left ``--files-from -`` out, or ``None``.

    ``None`` unless *mode* reviews code and ``-`` was typed. A stop in the
    review prints it under the row-14 command, which runs the review again.
    """
    if not _reviews_code(mode) or getattr(args, "files_from", None) != "-":
        return None
    return (
        f"NOTE: {_row(mode).name}'s command above leaves out --files-from -, "
        "which reads stdin: to review that list, pipe it into the command again "
        "with --files-from - added, or pass the files with --files."
    )


class ContinuationError(ValueError):
    """A run record's ``replay_flags`` that the composite's parser rejects."""


def recorded_continuation(mode: str, replay_flags: Optional[Sequence[str]]) -> List[str]:
    """:func:`continuation_flags` of a run record's ``replay_flags``.

    Parsed with the composite's own parser, so the continuation of a detached
    run is the row-14 command its worker printed. ``--resume`` alone when there
    is no record (a foreground run writes none). Raises
    :class:`ContinuationError` when the recorded flags do not parse, and prints
    nothing.
    """
    if not replay_flags:
        return ["--resume"]
    args = build_parser(mode, raising=True).parse_args(
        ["--plan-file", "-", *[str(flag) for flag in replay_flags]]
    )
    return continuation_flags(mode, args)


def files_from_stdin_refused(
    args: argparse.Namespace, review_runs: bool, detached: bool
) -> bool:
    """Whether ``--files-from -`` must be refused: the review runs and cannot read stdin.

    The phase's own guard refuses ``-`` only on its own ``--detach``, which no
    composite forwards, so an inner review-code in a detached worker would read
    ``DEVNULL`` and review nothing, or only the ``--files`` beside it. *detached*
    is the executor's ``--detach`` (the invoker) or ``--internal-worker`` (the
    worker), and always true for ``util improve-steps``, whose phases never get
    the user's stdin. A review that is passed over never reads it.
    """
    return getattr(args, "files_from", None) == "-" and review_runs and detached


# ---------------------------------------------------------------------------
# The per-step plan, for the planner (both legs decide through skip_reason)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class StepPlan:
    """One step of the plan ``util improve-steps`` prints.

    Attributes:
        index: ``"1"``, ``"1b"`` or ``"2"``.
        step: The mode word, or :data:`CONSOLIDATE` for ``1b``.
        decision: ``run`` or ``skip``, from :func:`skip_reason` alone; ``1b``
            reads ``run``, ``skip`` or ``after-review``.
        reason: The text in the line's parentheses, or ``None`` (a ``1b`` that
            reads ``run``).
        fresh: Whether the step is a review that must start over
            (``[IMPROVE_STEP_FRESH]``): a new round (``--force`` or a changed
            commit brief), a stale code review, a changed scope, or a leftover
            ``validation.json``.
        flags: :func:`step_flags`; the caller appends its cross-cutting tail.
    """

    index: str
    step: str
    decision: str
    reason: Optional[str]
    fresh: bool
    flags: Tuple[str, ...]


def _review_reason(mode: str, args: argparse.Namespace, records: Records) -> str:
    """Why step 1 runs, in the planner's words."""
    if getattr(args, "force", False):
        return "new round, --force"
    if records.header_changed:
        return "commit brief changed"
    if scope_changed(mode, args, records):
        return "review scope changed"
    if records.review_stale:
        return "reviewed before the latest implement"
    if records.review_skipped and not records.review_on_record:
        return "on record only as skipped"
    if (records.review_on_record or records.review_started
            or records.leftover_validation or records.leftover_results):
        return "review unfinished"
    return "not reviewed yet"


def _apply_reason(mode: str, args: argparse.Namespace, records: Records) -> str:
    """Why step 2 runs, in :func:`skip_reason`'s order."""
    if review_runs(mode, args, records):
        return "review not applied yet"
    if records.apply_started:
        return "apply in progress for this review"
    if records.apply_word is None:
        return "review not applied yet"
    return "review newer than the last apply"


def _skip_text(word: str, stamp: Optional[str]) -> str:
    return f"{word} {stamp or '(no date)'}"


def plan_steps(mode: str, args: argparse.Namespace, records: Records) -> List[StepPlan]:
    """The plan for every step, in order; the executor runs the same decisions.

    ``run`` or ``skip`` comes from :func:`skip_reason` and nothing else; the
    reasons are display. ``1b`` (improve-plan) answers from the review files on
    disk when step 1 is passed over, and reads ``after-review`` when it runs,
    because the files it would read are the previous round's until the review
    rewrites them. Under ``[ALREADY_COMPLETE]`` (every step passed over) there
    is no ``1b``.
    """
    row = _row(mode)
    review, apply = row.sequence
    finished = nothing_to_do(mode, args, records)
    plans: List[StepPlan] = []
    for index, word in step_indices(mode):
        flags = tuple(step_flags(mode, word, args, records))
        if word == CONSOLIDATE:
            if finished:
                continue
            if review_runs(mode, args, records):
                plans.append(StepPlan(index, word, AFTER_REVIEW,
                                      "runs if the review recommends it", False, flags))
            elif records.consolidation_skip:
                plans.append(StepPlan(index, word, SKIP, records.consolidation_skip,
                                      False, flags))
            else:
                plans.append(StepPlan(index, word, RUN, None, False, flags))
            continue
        said = skip_reason(mode, word, args, records)
        if word == review:
            if said:
                plans.append(StepPlan(index, word, SKIP,
                                      _skip_text(said, records.review_completed_at),
                                      False, flags))
            else:
                fresh = bool(
                    new_round(args, records)
                    or records.review_stale
                    or scope_changed(mode, args, records)
                    or records.leftover_validation
                )
                plans.append(StepPlan(index, word, RUN,
                                      _review_reason(mode, args, records), fresh, flags))
        else:
            if said:
                plans.append(StepPlan(index, word, SKIP,
                                      _skip_text(said, records.apply_word_at),
                                      False, flags))
            else:
                plans.append(StepPlan(index, word, RUN,
                                      _apply_reason(mode, args, records), False, flags))
    return plans


# ---------------------------------------------------------------------------
# Messages: one template each, filled from the mode row
# ---------------------------------------------------------------------------

def _display_path(path: Union[str, Path]) -> str:
    """*path* relative to the cwd when it lies under it (``/``-separated on
    every platform), else as given."""
    try:
        shown = os.path.relpath(str(path))
    except ValueError:  # Windows: another drive than the cwd's
        return str(path)
    if shown == os.pardir or shown.startswith(os.pardir + os.sep):
        return str(path)
    return shown.replace(os.sep, "/")


def _display_dir(path: Union[str, Path]) -> str:
    """:func:`_display_path` of a directory, closed by the separator it is spelled with."""
    shown = _display_path(path)
    sep = os.sep if os.path.isabs(shown) else "/"
    return shown.rstrip(sep) + sep


def interactive_refusal(mode: str) -> str:
    """The one-line ``--interactive`` refusal, naming the two phases to run instead.

    Each phase as the user types it (:func:`_step_word`): improve-commits names
    ``--review-commits`` and ``--apply-commit-fixes``. Built from the row at
    parse time, before any state is read, which is why the mapping is keyed on
    the row and not on a ``commit_range``.
    """
    row = _row(mode)
    first, second = (_step_word(row.name, word) for word in row.sequence)
    return (
        f"ERROR: {row.name} runs unattended and does not take --interactive (-i). "
        f"Run --{first} --interactive, then --{second}."
    )


def already_complete_line(mode: str, args: argparse.Namespace, records: Records) -> str:
    """``[ALREADY_COMPLETE]``: each step's word from :func:`skip_reason`, its stamp from that record.

    Only meaningful when :func:`nothing_to_do` holds. An apply on record only as
    skipped prints ``skipped`` and its ``skipped_at``, never ``completed``.
    Each step is named as the user types it (:func:`_step_word`).
    """
    row = _row(mode)
    review, apply = row.sequence
    parts = []
    for word in row.sequence:
        said = skip_reason(mode, word, args, records)
        stamp = records.review_completed_at if word == review else records.apply_word_at
        parts.append(f"{_step_word(row.name, word)} {said} {stamp or '(no date)'}")
    return (
        f"[ALREADY_COMPLETE] {row.name}: {', '.join(parts)}; nothing to do. "
        f"--force runs {_step_word(row.name, review)} again."
    )


def scope_changed_line(mode: str, records: Records) -> str:
    """``[IMPROVE_SCOPE_CHANGED]``: the scope on record, and the one typed."""
    recorded = records.recorded_scope
    if recorded:
        from code_review_orchestrator import REVIEW_SCOPE_FILES_KEY

        then = (
            f"{len(recorded)} files given with --files "
            f"(state.json {REVIEW_SCOPE_FILES_KEY})"
        )
    else:
        then = (
            "the default scope (tracked_files, else the git diff; no "
            "review_scope_files recorded)"
        )
    return (
        f"[IMPROVE_SCOPE_CHANGED] {_row(mode).name}: the code review on record "
        f"reviewed {then}; this run asks for {len(records.requested_scope or ())} "
        f"files (--files/--files-from). Reviewing again (as --force)."
    )


def files_from_stdin_note(mode: str) -> str:
    """The ``NOTE:`` for ``--files-from -`` on a completed code review."""
    return (
        f"NOTE: {_row(mode).name} does not compare --files-from - with the scope "
        "on record; the completed code review stands. Pass the list with --files "
        "or --files-from <file>, or add --force, to review it."
    )


def scope_notices(mode: str, args: argparse.Namespace, records: Records) -> List[str]:
    """The lines both legs print before step 1 about the code review's scope."""
    notices: List[str] = []
    if scope_changed(mode, args, records):
        notices.append(scope_changed_line(mode, records))
    if (
        _reviews_code(mode)
        and getattr(args, "files_from", None) == "-"
        and not review_runs(mode, args, records)
    ):
        notices.append(files_from_stdin_note(mode))
    return notices


def files_from_stdin_refusal() -> str:
    """The ``ERROR:`` line review-code prints for ``-`` under ``--detach``."""
    from code_review_orchestrator import FILES_FROM_STDIN_DETACHED

    return f"ERROR: {FILES_FROM_STDIN_DETACHED}"


def is_scope_files_error(exc: BaseException) -> bool:
    """Whether *exc* is review-code's ``ScopeFilesError`` (imported only to ask)."""
    if not isinstance(exc, ValueError):
        return False
    from code_review_orchestrator import ScopeFilesError

    return isinstance(exc, ScopeFilesError)


def scope_error_line(exc: BaseException) -> str:
    """The ``ERROR:`` line review-code prints for a scope it cannot read."""
    return f"ERROR: {exc}"


def state_read_error_line(mode: str, exc: StateReadError) -> str:
    """The one line a ``state.json`` that cannot be read is refused with."""
    return (
        f"ERROR: {_row(mode).name}: cannot read {_display_path(exc.path)} "
        f"({exc.detail}); nothing was run. Repair the file, or move it aside to "
        "start the plan's records over, then run the command again."
    )


# ---------------------------------------------------------------------------
# A live run is refused, never joined (§2.5)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class LiveOwner:
    """A live run that owns a dir the composite would write."""

    directory: str
    holder: str
    pid: Any
    verdict: str
    heartbeat_age_s: Optional[float]
    status_command: str
    abort_command: Optional[str]


def owned_dirs(mode: str, plan_file: Union[str, Path]) -> List[Tuple[str, Path]]:
    """``(phase word, dir)`` for every dir *mode* writes, in the order checked.

    The phase dirs of its ``sequence``, mapped through ``PHASE_DIRECTORIES`` as
    the detach walk maps them (``apply-code-fixes`` → ``apply-fixes/``), then
    ``full/``, which drives the same phase dirs in-process, then the
    composite's own run dir. Computed, never created.
    """
    row = _row(mode)
    out = output_dir_path(Path(os.path.abspath(str(plan_file))))
    pairs = [
        (phase, out / PHASE_DIRECTORIES.get(phase, phase))
        for phase in row.sequence_phases
    ]
    full = mode_table.resolve("full")
    pairs.append((full.phase, out / full.phase))
    pairs.append((row.phase, out / row.phase))
    return pairs


def _age_of(run: Dict[str, Any]) -> Optional[float]:
    return detach.heartbeat_age(run) if run else None


#: Phase-dir locks this process already holds for the composite it runs, by
#: lock path (:func:`_held_key`). Set only inside :func:`holding`: the
#: improve-commits front door's code-review lock, which it holds through
#: :func:`entry_point` (plans/review-commits.md §2.1, "It holds the lock
#: through the fronted phase's main").
_HELD_LOCKS: Dict[str, process_control.PhaseLock] = {}


def _held_key(directory: Union[str, Path]) -> str:
    return os.path.normcase(os.path.realpath(detach.lock_path(str(directory))))


def _held_lock(directory: Union[str, Path]) -> Optional[process_control.PhaseLock]:
    """The lock :func:`holding` handed over for *directory*, while still held."""
    lock = _HELD_LOCKS.get(_held_key(directory))
    return lock if lock is not None and lock.held else None


@contextlib.contextmanager
def holding(directory: Union[str, Path],
            lock: process_control.PhaseLock) -> Iterator[process_control.PhaseLock]:
    """Run the composite with *lock*, which this process holds on *directory*.

    For the block, :func:`_inspect` (so :func:`preflight`'s live-owner check)
    does not count that lock as another run's, and
    :meth:`ImproveWorkflow.run_mode` runs the step whose dir it is under it
    instead of taking it again (the OS lock refuses this process a second
    take on another descriptor), and leaves it held. So the round stays owned
    from the front door's steps 4 to 6 through the apply step that reads it,
    and no other invocation rewrites or archives it in between. The caller
    releases the lock.
    """
    key = _held_key(directory)
    previous = _HELD_LOCKS.get(key)
    _HELD_LOCKS[key] = lock
    try:
        yield lock
    finally:
        if previous is None:
            _HELD_LOCKS.pop(key, None)
        else:
            _HELD_LOCKS[key] = previous


def _inspect(
    plan_file: str, phase: str, directory: Path, *, own_run_id: Optional[str] = None
) -> Optional[LiveOwner]:
    """Who owns *directory*, if anyone: a live ``run`` record, or a held lock.

    ``classify_run`` with ``close_out=False`` writes nothing and creates no
    lock file. A dead holder owns nothing: its verdict is ``failed``, and the
    OS dropped its lock. A step lock held by *own_run_id* (this composite's own
    detached run, which a ``--detach`` launch answers for itself) is skipped,
    and so is a lock this process holds for the composite (:func:`holding`).
    """
    if not directory.is_dir():
        return None
    view = detach.classify_run(str(directory), close_out=False)
    verdict = view.get("verdict")
    run = view.get("run") if isinstance(view.get("run"), dict) else {}
    if verdict in _LIVE_VERDICTS:
        run_id = run.get("run_id")
        return LiveOwner(
            directory=str(directory),
            holder=f"run {run_id}" if run_id else "an unrecorded run",
            pid=run.get("pid"),
            verdict=str(verdict),
            heartbeat_age_s=view.get("heartbeat_age_s"),
            status_command=detach.status_command_for(
                plan_file, phase=view.get("phase") or phase, run_id=run_id,
                host=run.get("host"),
            ),
            abort_command=(
                detach.abort_command_for(plan_file, run_id=run_id) if run_id else None
            ),
        )
    if not view.get("lock_held"):
        return None
    if _held_lock(directory) is not None:
        return None
    payload = process_control.read_lock_holder(detach.lock_path(str(directory))) or {}
    run_id = payload.get("run_id")
    if own_run_id and run_id == own_run_id:
        return None
    # A step lock a detached composite holds names its run, whose run dir
    # carries the heartbeat and is the dir its status command watches. One
    # that names no run is a foreground composite in another shell: the `run`
    # record in its run dir is some earlier detached run's, which must not
    # lend it a heartbeat, a host or a poll of a finished run (Fable review
    # 2026-10-09). Its poll watches the locked step's own dir, where the
    # in-process phase writes its progress.
    run_phase = payload.get("run_phase")
    owner_run: Dict[str, Any] = {}
    if run_id and run_phase:
        watched = run_phase
        record = status_file.read_run(str(directory.parent / run_phase))
        if record.get("run_id") == run_id:
            owner_run = record
    else:
        watched = view.get("phase") or phase
    return LiveOwner(
        directory=str(directory),
        holder=(
            f"run {run_id}" if run_id
            else str(payload.get("holder") or "an unrecorded holder")
        ),
        pid=payload.get("pid"),
        verdict=process_control.holder_verdict(payload or None),
        heartbeat_age_s=_age_of(owner_run),
        status_command=detach.status_command_for(
            plan_file, phase=watched, run_id=run_id, host=owner_run.get("host"),
        ),
        abort_command=(
            detach.abort_command_for(plan_file, run_id=run_id) if run_id else None
        ),
    )


def live_owner(
    mode: str, plan_file: Union[str, Path], *, skip_own_run_dir: bool
) -> Optional[LiveOwner]:
    """The first live run that owns a dir *mode* writes, or ``None``; read-only.

    Nothing the composite does otherwise would see one: its steps run in-process
    with no ``--detach``, so no phase's ``maybe_detach`` ever reads its dir's
    owner, and two writers would share one ``.status.json``, its per-model
    results, ``grouped.json`` and ``validation.json``. ``--force`` and
    ``--resume`` change nothing here.

    *skip_own_run_dir* is for a ``--detach --if-not-running`` invocation,
    which ``launch`` answers by re-attaching to the composite's own live run,
    and for the worker, which holds that dir. Either then also passes over a
    step lock its own detached run holds. Every other invocation is refused
    by its own live run like any other owner: a plain ``--detach`` used to
    skip it too, and with ``--force`` fell through to ``launch``'s take-over of
    a worker mid-step (Fable review 2026-10-09).
    """
    row = _row(mode)
    plan_text = str(plan_file)
    own_run_id: Optional[str] = None
    if skip_own_run_dir:
        active = detach.active_run()
        if active is not None:
            own_run_id = active.run_id
        else:
            own_dir = owned_dirs(mode, plan_file)[-1][1]
            if own_dir.is_dir():
                view = detach.classify_run(str(own_dir), close_out=False)
                if view.get("verdict") in _LIVE_VERDICTS:
                    own_run_id = (view.get("run") or {}).get("run_id")
    for phase, directory in owned_dirs(mode, plan_file):
        if skip_own_run_dir and phase == row.phase:
            continue
        owner = _inspect(plan_text, phase, directory, own_run_id=own_run_id)
        if owner is not None:
            return owner
    return None


def live_owner_refusal(mode: str, owner: LiveOwner) -> str:
    """The refusal a live owner gets: who it is, and how to watch or abort it."""
    age = owner.heartbeat_age_s
    lines = [
        f"ERROR: {_row(mode).name}: a live run owns "
        f"{_display_dir(owner.directory)} "
        f"({owner.holder}, pid {owner.pid or 'unrecorded'}, {owner.verdict}, "
        f"last heartbeat {'never' if age is None else f'{age:.0f}s ago'}). Two "
        "runs must not write one phase dir, so nothing was started.",
        f"       Watch it: {owner.status_command}",
    ]
    if owner.abort_command:
        lines.append(f"       Abort it: {owner.abort_command}")
    lines.append(
        "       Then run this command again; it continues from what that run leaves."
    )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Arguments
# ---------------------------------------------------------------------------

class _RaisingParser(argparse.ArgumentParser):
    """A parser that raises instead of printing and exiting (a recorded replay)."""

    def error(self, message: str):  # type: ignore[override]
        raise ContinuationError(message)

    def exit(self, status: int = 0, message: Optional[str] = None):  # type: ignore[override]
        raise ContinuationError(message or f"the parser exited {status}")


def build_parser(mode: str, *, raising: bool = False) -> argparse.ArgumentParser:
    """The composite's own parser: the parent's cross-cutting flags, plus its own.

    ``--agent-decide`` (and its legacy spellings) and ``--no-confirm`` are
    accepted and change nothing: the apply step always gets them. No
    ``--consolidate`` and no ``--review-tasks``: the namespace carries both as
    ``False`` (``set_defaults``), the two attributes ``FullWorkflow``'s
    inherited steps read without a default.

    A composite whose range a front door pins (:func:`pins_commit_range`,
    improve-commits) also takes ``--head-ref`` and the hidden
    ``--commit-stage``: only its front door passes them, with ``--plan-file``
    and ``--base-ref`` (plans/review-commits.md §2.5, "Which parsers take
    ``--head-ref``"). On improve-code ``--head-ref`` stays argparse's usage
    error. ``--focus`` and ``--context-plan`` are the front door's and never
    reach this parser. Its help names the steps as the commit modes.
    """
    row = _row(mode)
    review, apply = row.sequence
    scoped = review == _SCOPED_REVIEW
    pinned = pins_commit_range(row.name)
    run = dispatcher_prefix()
    if pinned:
        shown_review, shown_apply = (_step_word(row.name, word) for word in row.sequence)
        lines = [
            "",
            f"Runs {shown_review}, then {shown_apply}, both unattended, on the commit",
            "brief the front door writes for the range:",
            f"  {shown_review}: --yes, plus --models or --quick when given, and the",
            "    scope flags --files and --files-from; the range's --base-ref and",
            "    --head-ref come from the front door",
            f"  {shown_apply}: --yes --agent-decide --no-confirm, plus the range's base",
            "",
            "Re-running continues where the last run stopped; a finished run exits 2",
            "with [ALREADY_COMPLETE]. --force, or another --focus or --context-plan,",
            "starts a new review round.",
            "",
            "Examples:",
            f"  {run} {row.name}",
            f"  {run} {row.name} last 2 commits --quick",
            f"  {run} {row.name} main...HEAD --files src/app.py",
            f"  {run} {row.name} last 2 commits --force",
        ]
    else:
        plan = "plans/my-plan.md"
        lines = [
            "",
            f"Runs {review}, then {apply}, both unattended:",
            f"  {review}: --yes, plus --models or --quick when given"
            + (",\n    and the scope flags --files, --files-from and --base-ref"
               if scoped else ""),
        ]
        if review in _CONSOLIDATING_REVIEWS:
            lines.append("  consolidation: when the review recommends it (--consolidate --yes)")
        lines.append(
            f"  {apply}: --yes --agent-decide --no-confirm"
            + (", plus --base-ref" if scoped else "")
        )
        lines += [
            "",
            "Re-running continues where the last run stopped; a finished run exits 2",
            "with [ALREADY_COMPLETE]. --force starts a new review round.",
            "",
            "Examples:",
            f"  {run} {row.name} {plan}",
            f"  {run} {row.name} {plan} --quick",
        ]
        if scoped:
            lines.append(f"  {run} {row.name} {plan} --files src/app.py --base-ref HEAD~1")
        lines.append(f"  {run} {row.name} {plan} --force")
    parser_class = _RaisingParser if raising else argparse.ArgumentParser
    parser = parser_class(
        prog=f"{row.target_module}.py",
        description=row.summary,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        parents=[build_parent_parser()],
        epilog="\n".join(lines) + "\n",
    )
    parser.add_argument(
        "--plan-file", required=True,
        help=("The commit brief (the front door passes it)" if pinned
              else "Path to the plan markdown file"),
    )
    parser.add_argument(
        "--models",
        nargs="+",
        default=None,
        metavar="PROVIDER:MODEL",
        help=f"Models for the {review} fan-out (D6 row 2). Wins over --quick. "
             f"Omit both to use the {review} phase's own default list.",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help=f"Use the quick model set for the {review} fan-out (D6 row 2).",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help=f"Continue a stopped run. Re-running without it continues too; "
             f"it is forwarded to {apply} only when the review is not re-run.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help=f"Start a new review round: {review} again with every model "
             f"(--force --rerun-all), then {apply} of its findings.",
    )
    if scoped:
        parser.add_argument(
            "--files",
            action="append",
            default=[],
            metavar="PATH",
            help="Review exactly these files (repeatable), as review-code "
                 "--files. A completed review of another scope is reviewed again.",
        )
        parser.add_argument(
            "--files-from",
            metavar="FILE",
            default=None,
            help='Like --files, one path per line read from FILE ("-" for stdin, '
                 "foreground only).",
        )
        parser.add_argument(
            "--base-ref",
            type=str,
            default=None,
            help=("The range's base, which the front door passes on every call "
                  "(the empty-tree id for a range from the root commit): the "
                  "review's diff base and the apply's." if pinned else
                  "Git ref the review diffs against, and the apply's diff context. "
                  "An apply-only re-run without it reuses the review's own ref."),
        )
    if pinned:
        parser.add_argument(
            "--head-ref",
            type=str,
            default=None,
            help="The range's head, which the front door passes on every call: "
                 "the commit the review reads (review-code --head-ref).",
        )
    parser.add_argument(
        AGENT_DECIDE_FLAG,
        *LEGACY_AGENT_DECIDE_FLAGS,
        dest="agent_decide",
        action="store_true",
        help=f"Accepted and implied: the judge agent decides every "
             f"needs-human-decision item {apply} meets.",
    )
    parser.add_argument(
        "--no-confirm",
        action="store_true",
        help="Accepted and implied: nothing is confirmed in an unattended run.",
    )
    if pinned:
        # The front door's `--detach` stage (plans/review-commits.md §2.1),
        # applied by the composite's worker right after its run-dir lock.
        parser.add_argument("--commit-stage", dest="commit_stage", default=None,
                            help=argparse.SUPPRESS)
    parser.set_defaults(consolidate=False, review_tasks=False)
    return parser


def parse_args(mode: str, argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    """Parse *argv* with *mode*'s parser (the thin orchestrators' ``parse_args``)."""
    return build_parser(mode).parse_args(list(argv) if argv is not None else None)


# ---------------------------------------------------------------------------
# The executor leg
# ---------------------------------------------------------------------------

class _Finished:
    """:func:`preflight`'s answer when every step would be passed over."""

    def __repr__(self) -> str:
        return "FINISHED"


#: Every step of ``sequence`` is passed over: print ``[ALREADY_COMPLETE]``, exit 2.
FINISHED = _Finished()


def preflight(
    mode: str,
    plan_path: Union[str, Path],
    args: argparse.Namespace,
    records: Callable[[], Records],
    *,
    skip_own_run_dir: bool,
    detached: bool,
) -> Union[None, int, _Finished]:
    """The checks before any step, in the order both legs make them.

    A live owner first (exit 3): a live run's records are still moving, so no
    answer read from them stands. Then *records* (a ``state.json`` that cannot
    be read is exit 3, a scope that cannot be read exit 1) and nothing to do
    (:data:`FINISHED`). Then ``--files-from -`` for a review that runs and
    cannot read the caller's stdin (exit 1). ``None`` to go on.

    The entry point asks it before its detach boundary and before it builds
    the workflow; a detached worker's :meth:`ImproveWorkflow.run` asks it again
    as the backstop. Each refusal prints its own line and writes nothing.
    """
    owner = live_owner(mode, plan_path, skip_own_run_dir=skip_own_run_dir)
    if owner is not None:
        return unattended_mod.fail_closed(live_owner_refusal(mode, owner))
    try:
        finished = nothing_to_do(mode, args, records())
    except StateReadError as exc:
        return unattended_mod.fail_closed(state_read_error_line(mode, exc))
    except ValueError as exc:
        if not is_scope_files_error(exc):
            raise
        print(scope_error_line(exc), file=sys.stderr)
        return EXIT_ERROR
    if finished:
        return FINISHED
    if files_from_stdin_refused(args, review_runs(mode, args, records()), detached):
        print(files_from_stdin_refusal(), file=sys.stderr)
        return EXIT_ERROR
    return None


class ImproveWorkflow(fwo.FullWorkflow):
    """``full``'s state machine, as one review-then-apply composite.

    Built from the mode row: its run dir, progress record, row-14 command and
    report are the composite's, never ``full``'s. It always runs unattended, so
    every inherited branch on ``self.unattended`` takes its unattended side,
    and ``--yes`` reaches each phase once, from :func:`step_flags`. It reads
    :class:`Records` once per process, at the first question, and answers every
    later one from that read; *records* hands it a read the entry point already
    made, and *checked* says that read already passed :func:`preflight`.
    """

    def __init__(
        self,
        args: argparse.Namespace,
        mode: str,
        *,
        records: Optional[Records] = None,
        checked: bool = False,
    ):
        self.row = _row(mode)
        args.yes = True
        super().__init__(args)
        self.unattended = True
        self.MODE_NAME = self.row.name
        self.RUN_DIR_PHASE = self.row.phase
        self.STATE_KEY = self.row.name.replace("-", "_")
        self.REPORT_TITLE = f"{self.row.name.replace('-', ' ').title()} Summary"
        self._records: Optional[Records] = records
        self._checked = checked
        self._announced = False

    # -- what both legs plan from -----------------------------------------
    @property
    def records(self) -> Records:
        if self._records is None:
            self._records = read_records(self.row.name, self.plan_path, self.args)
        return self._records

    def review_runs(self) -> bool:
        return review_runs(self.row.name, self.args, self.records)

    # -- the hooks -----------------------------------------------------------
    def steps(self) -> List[fwo.Step]:
        """One step per :func:`step_indices` entry.

        Its label (``Step 2: apply-code-fixes``) is what the run's log, its
        summary and the row-14 stop name, so it spells the word as the user
        types it (:func:`_step_word`: ``Step 2: apply-commit-fixes`` on
        improve-commits). The phase word and the step method stay the phase's.
        """
        steps = []
        for index, word in step_indices(self.row.name):
            if word == CONSOLIDATE:
                steps.append(fwo.Step("", f"Step {index}: consolidation",
                                      self.step_consolidate, skippable=False))
            else:
                steps.append(fwo.Step(
                    mode_table.phase_for(word),
                    f"Step {index}: {_step_word(self.row.name, word)}",
                    getattr(self, _STEP_METHODS[word]),
                ))
        return steps

    def step_argv(self, step: str) -> List[str]:
        return step_flags(self.row.name, step, self.args, self.records) + (
            cross_cutting_flags(self.args)
        )

    def skip_reason(self, step: fwo.Step) -> Optional[str]:
        word = dict(zip(self.row.sequence_phases, self.row.sequence)).get(step.phase)
        if word is None:
            return None
        return skip_reason(self.row.name, word, self.args, self.records)

    def nothing_to_do(self) -> bool:
        return nothing_to_do(self.row.name, self.args, self.records)

    def resume_flags(self) -> List[str]:
        """:func:`continuation_flags`: never a flag the front door synthesised."""
        return continuation_flags(self.row.name, self.args)

    def resume_command(self) -> str:
        """The row-14 command in the composite's own spelling (:func:`continuation_command`).

        For improve-plan and improve-code it is ``full``'s own command,
        ``dispatcher_command(MODE_NAME, plan, *resume_flags())``. For
        improve-commits the plan argument is the pinned range read from the
        brief's ``commit_range`` (``--improve-commits <base12>..<head12>
        --resume``), never the brief path the front door handed this run.
        """
        return continuation_command(self.row.name, self.plan_path, self.args)

    def _phase_failed(self, step: fwo.Step, detail: str, code: Optional[int]) -> int:
        """``full``'s row-14 stop, then :func:`continuation_stdin_note` for a stop in the review.

        Only there: the command it names runs the review again, which a stop
        in the apply's does not. The step it names is :meth:`steps`' label, so
        an improve-commits stop names ``apply-commit-fixes``; the command is
        built by ``FullWorkflow._phase_failed`` from :meth:`resume_flags`,
        which carries none of the front door's flags, and the commit spelling
        of its plan argument is that method's hook (plans/review-commits.md
        §2.8); :meth:`resume_command` is the command it must come to.
        """
        exit_code = super()._phase_failed(step, detail, code)
        if step.phase == self.row.sequence_phases[0]:
            note = continuation_stdin_note(self.row.name, self.args)
            if note:
                print(f"       {note}", file=sys.stderr)
        return exit_code

    def step_apply_code_fixes(self) -> Tuple[str, str, Optional[int]]:
        """Run the phase, with neither of ``full``'s two pre-checks.

        A review :func:`skip_reason` passed over is completed by definition, so
        the skipped-review check cannot fire. The zero-findings shortcut writes
        a skip through ``_record_skip``, which refreshes nothing over an earlier
        cycle's completion: a ``--force`` round with no findings would leave the
        old completion newest, and every re-run would run the apply again and
        never exit 2. The phase records its own outcome instead.
        """
        code = self.run_mode("apply-code-fixes", self.step_argv("apply-code-fixes"))
        return self._verify("apply-code-fixes", code)

    # -- the step lock ---------------------------------------------------------
    def _step_lock_payload(self, mode_word: str) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "holder": f"{self.row.name} step {mode_word}",
            "mode": self.row.name,
            "step": mode_word,
            "run_phase": self.row.phase,
            "pid": os.getpid(),
            "process_start_time": process_control.process_start_time(os.getpid()),
            "acquired_at": datetime.now().isoformat(),
        }
        active = detach.active_run()
        if active is not None:
            payload["run_id"] = active.run_id
        return payload

    def run_mode(self, mode_word: str, extra: Sequence[str]) -> int:
        """Run the phase in-process, holding its phase dir's lock for the step.

        The phase runs without ``--internal-worker``, so it never takes that
        lock itself, and without it a standalone ``--detach`` launch of the
        same phase would start a second writer in the dir. Taken non-blocking,
        as a foreground ``ask`` takes its question dir's, and released when the
        phase returns; the OS drops it if this process dies. A refusal is
        tried :data:`STEP_LOCK_ATTEMPTS` times, :data:`STEP_LOCK_RETRY_S`
        apart, because every ``status`` poll probes each phase dir's lock by
        taking and dropping it (``process_control.lock_is_free``). A lock it
        still cannot take (a run launched after the composite's own check)
        stops the step with the live-run refusal and exit 3.

        A dir whose lock this process already holds for the composite (the
        improve-commits front door's code-review lock, :func:`holding`) runs
        its step under that lock, which stays held when the step returns.
        """
        phase = mode_table.phase_for(mode_word) or mode_word
        step_dir = get_phase_dir(self.plan_path, phase)
        if _held_lock(step_dir) is not None:
            return super().run_mode(mode_word, extra)
        lock = process_control.PhaseLock(detach.lock_path(str(step_dir)))
        payload = self._step_lock_payload(mode_word)
        refused: Optional[process_control.LockUnavailable] = None
        for attempt in range(STEP_LOCK_ATTEMPTS):
            if attempt:
                time.sleep(STEP_LOCK_RETRY_S)
            try:
                lock.acquire(payload)
            except process_control.LockUnavailable as exc:
                refused = exc
                continue
            refused = None
            break
        if refused is not None:
            owner = _inspect(str(self.plan_path), phase, step_dir) or LiveOwner(
                directory=str(step_dir),
                holder=str(refused.holder.get("holder") or "an unrecorded holder"),
                pid=refused.holder.get("pid"),
                verdict=process_control.holder_verdict(refused.holder or None),
                heartbeat_age_s=None,
                status_command=detach.status_command_for(
                    str(self.plan_path), phase=phase
                ),
                abort_command=None,
            )
            print(live_owner_refusal(self.row.name, owner), file=sys.stderr)
            return EXIT_NEEDS_HUMAN
        try:
            return super().run_mode(mode_word, extra)
        finally:
            lock.release()

    # -- the checks before any step -------------------------------------------
    def announce(self) -> None:
        """Print the scope lines once, before step 1 or ``[ALREADY_COMPLETE]``."""
        if self._announced:
            return
        self._announced = True
        for line in scope_notices(self.row.name, self.args, self.records):
            print(line)

    def already_complete(self) -> int:
        """``[ALREADY_COMPLETE]`` and the summary, exit 2."""
        self.announce()
        line = already_complete_line(self.row.name, self.args, self.records)
        print(line)
        add_notice(line)
        self.print_report()
        return EXIT_NOTHING_TO_DO

    def run(self) -> int:
        """The backstops, then ``full``'s loop over this composite's steps.

        A detached worker reaches here without the entry point's checks (it
        must claim its run dir first), and the state can have moved since the
        invoker made them: a standalone apply finished, or a newer implement
        left the code review stale. So it asks them here, skipping the run dir
        it holds.
        """
        if not self._checked:
            worker = bool(getattr(self.args, "internal_worker", False))
            outcome = preflight(
                self.row.name, self.plan_path, self.args, lambda: self.records,
                skip_own_run_dir=worker, detached=worker,
            )
            if outcome is FINISHED:
                return self.already_complete()
            if outcome is not None:
                return outcome
            self._checked = True
        self.announce()
        return super().run()

    # -- the report --------------------------------------------------------------
    def report_artifacts(self) -> List[str]:
        """The review's report, the apply's summary, and what the apply wrote.

        Only the files that exist. improve-plan's write target is the plan;
        improve-code's are the files the apply's own batches changed
        (:meth:`_applied_paths`).
        """
        review_dir, apply_dir = (
            self.plan_dir / PHASE_DIRECTORIES.get(phase, phase)
            for phase in self.row.sequence_phases
        )
        candidates = [review_dir / "report.html"]
        if self.row.sequence[0] in _CONSOLIDATING_REVIEWS:
            candidates.append(review_dir / "consolidated-report.md")
        candidates.append(apply_dir / "summary.md")
        if _reviews_code(self.row.name):
            candidates += self._applied_paths(apply_dir)
        else:
            candidates.append(self.plan_path)
        seen: List[str] = []
        for path in candidates:
            if path.exists() and str(path) not in seen:
                seen.append(str(path))
        return seen

    def _applied_paths(self, apply_dir: Path) -> List[Path]:
        """The files the apply's own batches changed, as paths.

        The ``files_touched`` of every ``ok`` or partly applied row of the
        apply's ``write_batch_report.json``: the set the apply hands back as
        its own ``touched_file_{n}`` (``ApplyOrchestratorBase._touched_files``),
        earlier runs of this review cycle's rows included. Never
        ``tracked_files``: that list also holds implement's entries (label
        ``implementation``), so the summary, and the artifacts on the result
        line, named every file implement created or edited as what this
        unattended run wrote, the ones the apply never touched included; and
        the apply's own census label alone would leave out a file implement
        recorded first that the apply then edited.

        A report written before the review's latest completion is an earlier
        cycle's and names nothing, the scheduler's own rule
        (``_earlier_report_rows``); a missing date on either side keeps it. A
        missing or unreadable report names nothing, so an apply with nothing
        to fix lists no file it did not write.

        ``state.json`` is read through a read-only ``StateManager``, not
        ``self.state``: its load writes the judge-name upgrade back (and
        takes ``.state.lock``) when an old run left a ``claude_*`` spelling,
        and this report is also what a finished run's exit 2 prints, which
        writes nothing (§2.3, §2.4; Fable review 2026-10-09).
        """
        from .git_utils import get_project_root
        from .retry_ladder import STATUS_OK
        from .subagent_executor import WRITE_PARTIAL
        from .write_batch_scheduler import WRITE_BATCH_REPORT_FILENAME

        report_path = apply_dir / WRITE_BATCH_REPORT_FILENAME
        try:
            report = json.loads(report_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return []
        rows = report.get("tasks") if isinstance(report, dict) else None
        if not isinstance(rows, list):
            return []
        written_at = _parse_completion_time(report.get("written_at"))
        if written_at is None:
            try:
                written_at = datetime.fromtimestamp(report_path.stat().st_mtime)
            except OSError:
                written_at = None
        try:
            completed = StateManager(self.plan_path, read_only=True).get(
                "phases_completed")
        except Exception:  # noqa: BLE001 - a report never fails a run
            completed = None
        reviewed_at = (
            _parse_completion_time(
                completed.get(review_phase_for(self.row.sequence[1])))
            if isinstance(completed, dict) else None
        )
        if written_at is not None and reviewed_at is not None \
                and written_at < reviewed_at:
            return []
        root = Path(get_project_root(str(self.plan_path)) or os.getcwd())
        paths: List[Path] = []
        for row in rows:
            if not isinstance(row, dict) or not (
                row.get("status") == STATUS_OK
                or row.get("write_outcome") == WRITE_PARTIAL
            ):
                continue
            touched = row.get("files_touched")
            for name in touched if isinstance(touched, list) else []:
                if isinstance(name, str) and name:
                    path = root / name
                    if path not in paths:
                        paths.append(path)
        return paths


# ---------------------------------------------------------------------------
# The entry point both thin orchestrators call
# ---------------------------------------------------------------------------

def entry_point(mode: str, argv: Optional[Sequence[str]] = None) -> int:
    """``improve_plan_orchestrator.main`` / ``improve_code_orchestrator.main``,
    and the fronted main of the improve-commits front door
    (``utils/commit_review.py``), which calls it with ``--plan-file <brief>
    --base-ref <base> --head-ref <head>`` recorded as ``improve-commits``.

    In order: parse; refuse ``--interactive`` (before the workflow sets
    ``--yes``, so the user never meets a conflict with a flag they did not
    type); the plan exists; then, before the detach boundary, a live owner
    (exit 3), nothing to do (exit 2 with ``[ALREADY_COMPLETE]``, so a tool
    route's ``--detach`` re-run launches no worker whose only act is to exit
    2), a ``state.json`` that cannot be read (exit 3), a scope that cannot be
    read or ``--files-from -`` for a detached review (exit 1); then
    ``maybe_detach`` on the composite's run dir, as ``full`` does; then
    :meth:`ImproveWorkflow.run`. A worker skips the pre-boundary checks: it
    must claim its run dir before it ends, and its ``run()`` asks them again.

    The checks run before the workflow is built, because building it creates
    the plan's output dir: a refusal leaves nothing behind. The thin
    orchestrator's ``main`` has already bootstrapped the streams.
    """
    args = parse_args(mode, argv)
    if getattr(args, "interactive", False):
        return unattended_mod.fail_closed(interactive_refusal(mode))

    plan_path = Path(os.path.abspath(args.plan_file))
    if not plan_path.is_file():
        label = "Commit brief" if pins_commit_range(mode) else "Plan file"
        print(f"ERROR: {label} not found: {args.plan_file}", file=sys.stderr)
        print(f"       Resolved path: {plan_path}", file=sys.stderr)
        return EXIT_ERROR

    read: Dict[str, Records] = {}

    def records() -> Records:
        if "records" not in read:
            read["records"] = read_records(mode, plan_path, args)
        return read["records"]

    checked = False
    if not getattr(args, "internal_worker", False):
        detaching = bool(getattr(args, "detach", False))
        # Only a re-attach is `launch`'s to answer for the composite's own live
        # run. While every `--detach` skipped it, `--detach --force` reached
        # `launch`'s take-over of a worker still writing a step dir; `--force`
        # and `--resume` change nothing here (§2.5, Fable review 2026-10-09).
        reattaching = detaching and bool(getattr(args, "if_not_running", False))
        outcome = preflight(
            mode, plan_path, args, records,
            skip_own_run_dir=reattaching, detached=detaching,
        )
        if outcome is FINISHED:
            return ImproveWorkflow(args, mode, records=records()).already_complete()
        if outcome is not None:
            return outcome
        checked = True

    workflow = ImproveWorkflow(
        args, mode, records=read.get("records"), checked=checked
    )

    from .review_orchestrator_base import maybe_detach

    detached = maybe_detach(
        args=args,
        mode=workflow.MODE_NAME,
        phase_dir=str(workflow.run_dir),
        plan_file=str(plan_path),
        phase=workflow.RUN_DIR_PHASE,
    )
    if detached is not None:
        return detached
    return workflow.run()
