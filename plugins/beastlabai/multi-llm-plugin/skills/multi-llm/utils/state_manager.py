"""State manager for persisting implementation state across sessions."""

import hashlib
import json
import logging
import os
import re
import unicodedata
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from .clock import parse_local
from .git_utils import GitError, get_branch_name, get_project_root_from_dir, head_or_empty_tree
from .judge_vocab import upgrade_legacy
from .schema_validator import validate_state_file
from . import state_file as _state_file
from . import task_ledger as _task_ledger
from .unattended import NeedsHuman
from .output_handler import get_output_dir

logger = logging.getLogger(__name__)

# --- Constants ---
ID_ALGO_VERSION = 1
CURRENT_FORMAT_VERSION = 2

#: The phases that judge implement's output. A completion of one of them that
#: predates implement's latest completion reviewed (or fixed) an earlier
#: state of the code: typically the empty repository a review was run against
#: before implement existed, or code implement has since rewritten.
PHASES_STALED_BY_IMPLEMENT = ("code-review", "apply-code-fixes")


def _parse_completion_time(value) -> Optional[datetime]:
    """An ISO timestamp as a naive local datetime, or None.

    The one reading of a stamp, whatever wrote it: ``state.json``'s phase
    and metrics stamps, a write report's ``written_at``, an audit record, a
    snapshot manifest. A stamp with a UTC offset is converted to local time,
    so it compares with a naive local one as the same instant.
    """
    if not isinstance(value, str) or not value:
        return None
    try:
        return parse_local(value)
    except ValueError:
        return None


def predates_review(
    stamped: Optional[datetime], reviewed_at: Optional[datetime], *,
    whole_seconds: bool = False, undated_predates: bool = False,
) -> bool:
    """Whether a record dated *stamped* belongs to an earlier review cycle.

    The review-cycle rule: a record older than the review's latest
    completion (*reviewed_at*) is an earlier cycle's. Strictly older, so a
    record stamped at the completion's instant is this cycle's. A missing
    date on either side keeps the record: absence of a date is not
    staleness. Both datetimes are naive local times, as
    :func:`_parse_completion_time` reads them.

    *whole_seconds* is for records stamped to the second (the audit log, a
    pre-batch snapshot's manifest): the completion is truncated to its
    second first, so a record in the review's own second is this cycle's.

    *undated_predates* reads a record with no date as an earlier cycle's
    when the review has one. Only a pre-batch snapshot takes it
    (``write_safety.TaskSnapshot.taken_before``): the manifests without a
    date predate the field, and a rollback point of unknown age is set
    aside rather than trusted. See docs/development/write-scheduler.md.
    """
    if reviewed_at is None:
        return False
    if stamped is None:
        return undated_predates
    if whole_seconds:
        reviewed_at = reviewed_at.replace(microsecond=0)
    return stamped < reviewed_at


def stamp_or_mtime(value: Any, path: Any) -> Optional[datetime]:
    """*value* read as a stamp, else *path*'s modification time, else None.

    How a file that carries its own date is dated (``write_batch_report.json``
    and its ``written_at``): the stamp when it parses, the file's mtime when
    the stamp is missing or unreadable.
    """
    parsed = _parse_completion_time(value)
    if parsed is not None:
        return parsed
    try:
        return datetime.fromtimestamp(os.stat(path).st_mtime)
    except OSError:
        return None


def mark_phase_started_in_state(state: Dict[str, Any], phase: str) -> None:
    """Record *phase* as handed out and not yet finished (``phases_started``).

    The native leg's record: a write phase's orchestrator writes this when it
    emits its batch document, and the host's closing step
    (``--mark-completed``, ``util finalize-tracking --mark-completed``) turns
    it into a completion. Until 2026-10-05 ``apply-suggestions`` and
    ``implement`` recorded themselves *completed* at that emit site, so
    ``status``, the next-step builder and the completed-phase guard read a
    phase as done while the host was still applying its batches — or after it
    had died halfway (racing re-run, 2026-10-04: implement stamped 10:43:30,
    six minutes before its last task). ``get_workflow_status`` reads this map
    as ``in_progress``, the one status that spells ``--resume``. Re-stamped on
    every emit (a ``--resume`` is a new run of the same phase), popped by
    :func:`mark_phase_completed_in_state` and by a skip. An EARLIER completion
    of the same phase (a previous review cycle's, or the implement run this
    one repeats) is left in ``phases_completed`` untouched — nothing rewrites
    history — and the two stamps decide: :meth:`StateManager.is_phase_started`
    and :meth:`StateManager.is_phase_completed` read the newer record as the
    phase's state (reviewer repro, 2026-10-05: a cycle-2 native re-run read
    ``completed`` on cycle 1's stamp, mid-loop).
    """
    started = state.get("phases_started")
    if not isinstance(started, dict):
        started = {}
        state["phases_started"] = started
    started[phase] = datetime.now().isoformat()


def mark_phase_completed_in_state(state: Dict[str, Any], phase: str) -> None:
    """``StateManager.mark_phase_completed``'s mutation on a raw state dict.

    Module-level, like :func:`compute_plan_hash`, for the file-level writers
    (``finalize_tracking``) that must not build a ``StateManager`` over a plan
    the native leg has just edited. The started record is cleared in the same
    write, so a phase is never both.
    """
    if "phases_completed" not in state:
        state["phases_completed"] = {}
    state["phases_completed"][phase] = datetime.now().isoformat()
    _pop_phase_started(state, phase)


def _pop_phase_started(state: Dict[str, Any], phase: str) -> None:
    """Drop *phase*'s started record, and the map once it is empty.

    A run that recorded a phase started and then
    completed it left ``phases_started: {}`` behind, so a plain first
    implement on the executor leg wrote a key that says nothing.
    """
    started = state.get("phases_started")
    if isinstance(started, dict):
        started.pop(phase, None)
        if not started:
            del state["phases_started"]


#: ``state.json``'s record of the ``--human-task <id>=done|skip`` answers
#: (``implement_orchestrator`` writes it; ``retry`` is never recorded).
HUMAN_TASK_DECISIONS_KEY = "human_task_decisions"

#: The reasons a ``done`` answer writes (``task_ledger``'s words).
_ACCEPTED_REASON_PREFIX = _task_ledger.ACCEPTED_REASON_PREFIX
_COMPLETED_MANUAL_REASON = _task_ledger.COMPLETED_MANUAL_REASON


def _answer_produced(action: str, status: str, reason: Optional[str]) -> bool:
    """Whether *status*/*reason* is what the answer *action* itself writes."""
    if action == "done":
        text = str(reason or "")
        return status == "completed" and (
            text.startswith(_ACCEPTED_REASON_PREFIX)
            or text == _COMPLETED_MANUAL_REASON
        )
    if action == "skip":
        return status == "skipped"
    return False


def _consume_answer(
    state: Dict[str, Any], task_id: str, previous: Optional[str],
    status: str, reason: Optional[str],
) -> None:
    """Drop *task_id*'s recorded ``--human-task`` answer once its task moved on.

    An answer answers one stop: it is
    applied when the run that recorded it resolves its plan, and the status
    it writes keeps it (an accepted ``completed``, an answered ``skipped``).
    Any other status written for the task afterwards — it ran again (a
    ``--task`` re-run, a ``retry``, a resume that unskipped it) and finished,
    failed or was handed out again — is a new stop the answer never saw, so
    the answer is dropped: a recorded ``done`` used to accept a check's NEW
    findings, and a task's new failure, on a later plain ``--resume`` with no
    ``[HUMAN_TASK_ANSWERED]`` line, and a recorded ``skip`` skipped a task
    the user had just run again. ``pending`` on a task that had no status or
    was already ``pending`` is not an outcome (a seed, a held task's reason),
    so an answer recorded before its task's first status survives it.
    """
    recorded = state.get(HUMAN_TASK_DECISIONS_KEY)
    if not isinstance(recorded, dict) or task_id not in recorded:
        return
    if status == "pending" and previous in (None, "pending"):
        return
    if _answer_produced(str(recorded.get(task_id) or ""), status, reason):
        return
    kept = {key: value for key, value in recorded.items() if key != task_id}
    if kept:
        state[HUMAN_TASK_DECISIONS_KEY] = kept
    else:
        state.pop(HUMAN_TASK_DECISIONS_KEY, None)


def update_task_status_in_state(
    state: Dict[str, Any], task_id: str, status: str, reason: Optional[str] = None
) -> None:
    """``StateManager.update_task_status``'s mutation on a raw state dict.

    Module-level for the same reason :func:`mark_phase_completed_in_state`
    is: the native write leg's per-batch record (``util batch-done``) edits
    ``state.json`` as a file, mid-loop, and must not build a ``StateManager``
    over a plan the batch just edited. Both legs write every task status
    here, which is what lets it retire a ``--human-task`` answer the task
    has moved past (:func:`_consume_answer`).
    """
    if "task_status" not in state:
        state["task_status"] = {}
    previous = state["task_status"].get(task_id)
    _consume_answer(state, task_id, previous, status, reason)
    state["task_status"][task_id] = status
    if reason is not None:
        if "task_status_reasons" not in state:
            state["task_status_reasons"] = {}
        state["task_status_reasons"][task_id] = reason
    elif isinstance(state.get("task_status_reasons"), dict):
        # A reason describes the status it was written with: a status written
        # without one drops it. A task accepted after failing (`accepted —`)
        # and later run to completion kept the old reason, and a resume read
        # it back as an accepted failure.
        state["task_status_reasons"].pop(task_id, None)


#: ``state.json``'s map of what an implement check task found:
#: ``{task_id: [finding, ...]}``, present only while some task has findings.
TASK_CHECK_FINDINGS_KEY = "task_check_findings"

#: ``state.json``'s record of the decomposition implement ran last, as a
#: graph: ``{task_id: [the ids it depends on]}`` for EVERY task of it
#: (:meth:`StateManager.record_task_titles`). A ``--resume`` materializes only
#: the unfinished tasks, so a walk over ``write_tasks.json`` alone lost every
#: edge through a finished one: a check's findings held back T004 but not
#: T006, whose chain to the check ran through a manual task answered done.
#: ``check_records.decomposition_graph`` reads it.
IMPLEMENT_TASK_GRAPH_KEY = "implement_task_depends_on"


def manual_task_gates(
    graph: Mapping[str, Sequence[str]],
    *,
    human_ids: Iterable[str],
    done: Iterable[str],
    owed: Iterable[str],
    dropped: Iterable[str] = (),
) -> Dict[str, Any]:
    """Which owed manual tasks the user can do now, and what waits on them.

    T010, a manual task every
    code task depended on, was deferred under ``--yes``; implement ran
    nothing, reported done, said "No later phase waits for these manual
    tasks" and offered a command recording T008, T009 and T010 done at once,
    while T008 and T009 depend on code nothing had run yet. Pure, over the
    decomposition *graph* (``{task: [the ids it depends on]}``):

    * *done*: the tasks on record ``completed`` (a code task that ran or was
      accepted, a manual task answered done);
    * *owed*: the manual tasks left for the user (deferred, not done);
    * *dropped*: the tasks skipped at the user's request and the ones skipped
      with them, which nobody runs.

    Returns ``{"closable", "waiting", "after", "gated"}``:

    * ``closable``: the owed manual tasks whose own dependencies are done, or
      are closable manual tasks themselves: the ones a ``--human-task
      <id>=done`` can honestly record now;
    * ``waiting``: ``{closable id: [code ids]}``, the code tasks not done that
      wait on it and that a resume runs once the closable tasks are recorded
      done (each of their other dependencies done, closable, or such a task);
    * ``after``: ``{owed id not closable: [code ids]}``, the code tasks not
      done that it comes after;
    * ``gated``: some code task is not done, and every one that is not waits,
      directly or through other tasks, on a manual task not done — so a
      resume runs nothing until one is recorded done.
    """
    human = {str(task_id) for task_id in human_ids}
    finished = {str(task_id) for task_id in done}
    owed_ids = {str(task_id) for task_id in owed} - finished
    gone = {str(task_id) for task_id in dropped} - finished
    deps: Dict[str, List[str]] = {
        str(task_id): [str(dep) for dep in (values or []) if dep]
        for task_id, values in graph.items()
    }

    def open_deps(task_id: str) -> List[str]:
        return [
            dep for dep in deps.get(task_id, ())
            if dep not in finished and dep not in gone
        ]

    blockers_memo: Dict[str, frozenset] = {}

    def blockers(task_id: str, path: frozenset = frozenset()) -> frozenset:
        """The manual tasks not done that *task_id* waits on, transitively."""
        if task_id in blockers_memo:
            return blockers_memo[task_id]
        if task_id in path:  # a cycle: tasks.md never has one; stay finite
            return frozenset()
        found: set = set()
        for dep in open_deps(task_id):
            if dep in human:
                found.add(dep)
            found |= blockers(dep, path | {task_id})
        blockers_memo[task_id] = frozenset(found)
        return blockers_memo[task_id]

    code_after_memo: Dict[str, frozenset] = {}

    def code_after(task_id: str, path: frozenset = frozenset()) -> frozenset:
        """The code tasks not done that *task_id* comes after, transitively."""
        if task_id in code_after_memo:
            return code_after_memo[task_id]
        if task_id in path:
            return frozenset()
        found: set = set()
        for dep in open_deps(task_id):
            if dep not in human:
                found.add(dep)
            found |= code_after(dep, path | {task_id})
        code_after_memo[task_id] = frozenset(found)
        return code_after_memo[task_id]

    closable = sorted(m for m in owed_ids if not code_after(m))
    closable_set = set(closable)
    pending_code = sorted(
        task_id for task_id in deps
        if task_id not in human and task_id not in finished and task_id not in gone
    )

    released_memo: Dict[str, bool] = {}

    def released(task_id: str, path: frozenset = frozenset()) -> bool:
        """Whether a resume runs *task_id* once the closable tasks are done."""
        if task_id in released_memo:
            return released_memo[task_id]
        if task_id in path:
            return False
        ok = all(
            dep in closable_set
            or (dep not in human and released(dep, path | {task_id}))
            for dep in open_deps(task_id)
        )
        released_memo[task_id] = ok
        return ok

    waiting: Dict[str, List[str]] = {}
    for task_id in pending_code:
        held = blockers(task_id)
        if not held or not released(task_id):
            continue
        for manual in sorted(held & closable_set):
            waiting.setdefault(manual, []).append(task_id)
    after = {
        manual: sorted(code_after(manual))
        for manual in sorted(owed_ids - closable_set)
        if code_after(manual)
    }
    gated = bool(pending_code) and all(blockers(task_id) for task_id in pending_code)
    return {
        "closable": closable,
        "waiting": waiting,
        "after": after,
        "gated": gated,
    }


def _set_task_entry(
    state: Dict[str, Any], key: str, task_id: str, value: Any,
) -> None:
    """Set *task_id*'s entry of the per-task map *key* to *value*, or drop
    the entry when *value* is empty; the key is dropped when the map empties.

    The one body of the ``set_task_*_in_state`` map writers: each normalizes
    its value and calls this. The map is replaced by a fresh copy, never
    edited in place; a recorded *key* that is not a map counts as an empty
    one. These writers edit a raw dict and journal nothing: their writes go
    with the journaled record of the same task
    (docs/development/write-scheduler.md, "How a save knows its own changes").
    """
    recorded = state.get(key)
    current = dict(recorded) if isinstance(recorded, dict) else {}
    if value:
        current[str(task_id)] = value
    else:
        current.pop(str(task_id), None)
    if current:
        state[key] = current
    else:
        state.pop(key, None)


def _set_task_member(
    state: Dict[str, Any], key: str, task_id: str, member: bool,
) -> None:
    """Add *task_id* to (or remove it from) the per-task list *key*, kept as
    sorted distinct ids; the key is dropped when the list empties. The list
    twin of :func:`_set_task_entry`."""
    recorded = state.get(key)
    current = {str(t) for t in recorded} if isinstance(recorded, list) else set()
    if member:
        current.add(str(task_id))
    else:
        current.discard(str(task_id))
    if current:
        state[key] = sorted(current)
    else:
        state.pop(key, None)


def set_task_check_findings_in_state(
    state: Dict[str, Any], task_id: str, findings: Optional[Iterable[str]],
) -> None:
    """Record (or, with no findings, clear) *task_id*'s check findings.

    Written by both write legs after an implement task is recorded — the
    executor's scheduler and ``util batch-done`` — from the reply's structured
    ``check`` object (racing re-run 4, 2026-10-05: T007's two html-validate
    problems lived only in the runner's notes). ``status``, the workflow's
    closing notice and review-code's implementation record read it. The key
    is dropped when the map empties, so a plan with no findings gains none.
    """
    kept = [str(item) for item in (findings or []) if str(item).strip()]
    _set_task_entry(state, TASK_CHECK_FINDINGS_KEY, task_id, kept)


#: ``state.json``'s map of what the checks an implement task ran on its OWN
#: edits reported when one failed: ``{task_id: [finding, ...]}``, present only
#: while some task's own check fails. Never
#: :data:`TASK_CHECK_FINDINGS_KEY`: a code task whose own test fails keeps its
#: edits and holds nothing back, where a check task's findings hold its
#: dependents. Written by both legs (``util batch-done --own-check findings`` on a
#: task that declares files, the scheduler from ``TaskOutcome.batch_check``);
#: ``status`` and review-code's implementation record read it.
TASK_BATCH_CHECK_KEY = "task_batch_check"


def set_task_batch_check_in_state(
    state: Dict[str, Any], task_id: str, findings: Optional[Iterable[str]],
) -> None:
    """Record (or, with no findings, clear) *task_id*'s failing own check;
    the key is dropped when the map empties. Clearing it clears the task's
    :data:`TASK_OWN_TEXT_KEY` entry too."""
    kept = [str(item) for item in (findings or []) if str(item).strip()]
    if not kept:
        # The words kept beside a failing own check go with it.
        set_task_own_text_in_state(state, task_id, None)
    _set_task_entry(state, TASK_BATCH_CHECK_KEY, task_id, kept)


#: ``state.json``'s map of what an implement task with a failing own check
#: (:data:`TASK_BATCH_CHECK_KEY`) itself says — its title, ``## Task``
#: section and acceptance criteria (``check_records.task_own_text``)
#: — ``{task_id: text}``, present only while some such task has one. A check task that reports the
#: same finding in a later run (a ``--resume`` materializes only what it
#: hands out) reads it to judge whether the check is the task's own job
#: (``task_owns_the_check``) before recording the task's finding as a
#: repeat of the check's (``move_check_repeats_in_state``): never from its
#: title alone. Written by both legs beside the failing own check (``util
#: batch-done``, the scheduler); clearing the task's failing own check
#: clears it.
TASK_OWN_TEXT_KEY = "task_own_text"


def set_task_own_text_in_state(
    state: Dict[str, Any], task_id: str, text: Optional[str],
) -> None:
    """Record *task_id*'s own text while it has a failing own check on
    record (:data:`TASK_BATCH_CHECK_KEY`), else drop it; the key is dropped
    when the map empties."""
    failing = state.get(TASK_BATCH_CHECK_KEY)
    value = str(text or "").strip()
    if not (isinstance(failing, dict) and failing.get(str(task_id))):
        value = ""
    _set_task_entry(state, TASK_OWN_TEXT_KEY, task_id, value)


#: ``state.json``'s map of an implement task's own words about the checks it
#: ran on its edits (its reply's ``check.note``): ``{task_id: note}``,
#: present only while some task has one (live run 12: the
#: released T007 wrote "(known problem the user accepted in T002)" into its
#: finding, which the strict match then read as its own failure). Recorded
#: and shown, never read as a finding or matched on. Written by both legs
#: (``util batch-done --note``, the scheduler from
#: ``TaskOutcome.batch_check_note``); every other record of the task clears
#: it.
TASK_OWN_CHECK_NOTE_KEY = "task_own_check_note"


def set_task_own_check_note_in_state(
    state: Dict[str, Any], task_id: str, note: Optional[str],
) -> None:
    """Record (or, with no note, clear) *task_id*'s own-check note; the key
    is dropped when the map empties."""
    _set_task_entry(
        state, TASK_OWN_CHECK_NOTE_KEY, task_id, str(note or "").strip())


#: ``state.json``'s list of the implement tasks whose last record carried a
#: report of their OWN checks (passed, failing, or repeating only accepted
#: findings), sorted, present only while some task has one. Written by both legs (``util batch-done
#: --own-check``, the scheduler from ``TaskOutcome.batch_check``); every
#: other record of the task clears it; the tests line reads it
#: (``verification_lines.implement_checks_ran``).
TASK_OWN_CHECK_RAN_KEY = "task_own_check_ran"


def set_task_own_check_ran_in_state(
    state: Dict[str, Any], task_id: str, ran: bool,
) -> None:
    """Record (or clear) that *task_id*'s own check reported; the key is
    dropped when the list empties."""
    _set_task_member(state, TASK_OWN_CHECK_RAN_KEY, task_id, bool(ran))


#: ``state.json``'s map of what an implement task's own check reported again
#: of findings the user accepted for a check (``--human-task <check>=done``),
#: by check: ``{task_id: {check_id: [finding, ...]}}``, present only while
#: some task has one (round 22 kept them only in the result
#: row and the printed line, so ``status`` showed the task as plainly
#: ``completed``). Beside :data:`TASK_BATCH_CHECK_KEY`, never in it: they
#: are not the task's own failure. Written by both legs
#: (``check_records.split_accepted_findings``: the scheduler and
#: ``util batch-done --own-check findings``); every other record of the task
#: clears it; ``status`` reads it through
#: :meth:`StateManager.implementation_batch_check_accepted`.
TASK_BATCH_CHECK_ACCEPTED_KEY = "task_batch_check_accepted"


def set_task_batch_check_accepted_in_state(
    state: Dict[str, Any], task_id: str,
    matched: Optional[Mapping[str, Iterable[str]]],
) -> None:
    """Record (or, with nothing matched, clear) what *task_id*'s own check
    reported again of the accepted findings, by check id; the key is dropped
    when the map empties."""
    _set_by_check_in_state(state, TASK_BATCH_CHECK_ACCEPTED_KEY, task_id, matched)


#: ``state.json``'s map of what an implement task's own check reported that
#: is the same finding a check task of the run reported (the strict
#: comparison of ``check_records.split_accepted_findings``), by that
#: check: ``{task_id: {check_id: [finding, ...]}}``, present only while some
#: task has one. Beside
#: :data:`TASK_BATCH_CHECK_KEY`, never in it: T002's own record covers the
#: finding. Written by both legs (``check_records.repeated_findings_for``:
#: the scheduler and ``util batch-done``, when the code task's record comes
#: second and when the check's does); every other record of the task clears
#: it; ``status`` reads it through
#: :meth:`StateManager.implementation_batch_check_repeats`.
TASK_BATCH_CHECK_REPEATS_KEY = "task_batch_check_repeats"


def set_task_batch_check_repeats_in_state(
    state: Dict[str, Any], task_id: str,
    matched: Optional[Mapping[str, Iterable[str]]],
) -> None:
    """Record (or, with nothing matched, clear) what *task_id*'s own check
    reported that a check task of the run reported too, by check id; the
    key is dropped when the map empties."""
    _set_by_check_in_state(state, TASK_BATCH_CHECK_REPEATS_KEY, task_id, matched)


def _set_by_check_in_state(
    state: Dict[str, Any], key: str, task_id: str,
    matched: Optional[Mapping[str, Iterable[str]]],
) -> None:
    """One ``{task_id: {check_id: [finding, ...]}}`` map's writer."""
    kept = {
        str(check_id): [str(item) for item in (findings or []) if str(item).strip()]
        for check_id, findings in sorted((matched or {}).items())
    }
    kept = {check_id: findings for check_id, findings in kept.items() if findings}
    _set_task_entry(state, key, task_id, kept)


#: ``task id -> tree fingerprint`` for each check with findings on the native
#: leg: the files git saw when the run that recorded the
#: findings ended (``write_prompt.check_tree_fingerprint``). A native
#: ``--resume`` hands the check out again only when the tree moved since —
#: the executor keeps the same stamp on the check's verdict
#: (``verdict.tree_fingerprint``).
TASK_CHECK_TREES_KEY = "task_check_trees"


def set_task_check_tree_in_state(
    state: Dict[str, Any], task_id: str, fingerprint: Optional[str],
) -> None:
    """Record (or, with ``None``, drop) *task_id*'s check tree stamp; the key
    is dropped when the map empties."""
    _set_task_entry(
        state, TASK_CHECK_TREES_KEY, task_id,
        str(fingerprint) if fingerprint else None)


#: The per-task keys that hold an implement task's verdict: what its last
#: record said about checks (a check's findings and tree stamp, the task's
#: own check, its words, what it repeated). A run that hands the task out
#: again clears them all (:func:`clear_task_verdict`), so an earlier run's
#: verdict never shows on the rerun. A new per-task key goes here or in the
#: test's not-a-verdict list (``tests/test_task_verdict_keys.py``).
TASK_VERDICT_KEYS: Tuple[str, ...] = (
    TASK_CHECK_FINDINGS_KEY,
    TASK_CHECK_TREES_KEY,
    TASK_BATCH_CHECK_KEY,
    TASK_OWN_TEXT_KEY,
    TASK_BATCH_CHECK_ACCEPTED_KEY,
    TASK_BATCH_CHECK_REPEATS_KEY,
    TASK_OWN_CHECK_RAN_KEY,
    TASK_OWN_CHECK_NOTE_KEY,
)


def clear_task_verdict(state: Dict[str, Any], task_id: str) -> None:
    """Drop *task_id*'s entry from every :data:`TASK_VERDICT_KEYS` map and
    list on a raw state dict, each key dropped when it empties: what each
    ``set_task_*_in_state`` writer does when given nothing. Journals nothing;
    the caller stamps the task's reset (:func:`mark_tasks_reset_in_state`)
    or writes its status beside it."""
    for key in TASK_VERDICT_KEYS:
        if key in _TASK_RECORD_LISTS:
            _set_task_member(state, key, task_id, False)
        else:
            _set_task_entry(state, key, task_id, None)


#: ``task id -> when a run that hands the implement task out again set its
#: earlier record aside``: a start-over (``--fresh``, or a
#: plain run after a finished implement) for every code task, an explicit
#: ``--task`` rerun for the one it names. The task is ``pending`` again, but
#: the prior-changes log still holds the line its earlier run wrote, and a
#: native ``--resume`` refuses a task the log holds and no status records
#: (``batch_done.unrecorded_logged_batches``): a line no newer than this stamp
#: is the earlier run's, not one this run left unrecorded.
TASK_RESET_AT_KEY = "implement_task_reset_at"


def mark_tasks_reset_in_state(state: Dict[str, Any], task_ids: Iterable[str]) -> None:
    """Stamp *task_ids* in :data:`TASK_RESET_AT_KEY` with the current time."""
    ids = [str(task_id) for task_id in task_ids if str(task_id)]
    if not ids:
        return
    recorded = state.get(TASK_RESET_AT_KEY)
    current = dict(recorded) if isinstance(recorded, dict) else {}
    now = datetime.now().isoformat()
    for task_id in ids:
        current[task_id] = now
    state[TASK_RESET_AT_KEY] = current


def mark_item_processed_in_state(
    state: Dict[str, Any],
    phase: str,
    item_id: str,
    status: str,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """``StateManager.mark_item_processed``'s mutation on a raw state dict.

    ``processed_<phase>`` is the map the apply base's ``--resume`` filters
    its merged groups on (``apply_orchestrator_base`` step 23), keyed by the
    group id a batch's ``expected_ids`` carry; ``phase`` is the base's own
    ``phase_name`` (the phase DIR word — ``apply-fixes`` for apply-code-fixes).
    """
    key = f"processed_{phase}"
    if key not in state or not isinstance(state[key], dict):
        state[key] = {}
    state[key][item_id] = {
        "status": status,
        "details": details or {},
        "timestamp": datetime.now().isoformat(),
    }


#: ``details.leg`` of a ``processed_<phase>`` record: which
#: leg wrote it — the write executor's scheduler, or ``util batch-done`` for
#: the native host.
PROCESSED_LEG_EXECUTOR = "executor"
PROCESSED_LEG_NATIVE = "native"


def record_batch_items_in_state(
    state: Dict[str, Any],
    phase: str,
    task: Dict[str, Any],
    *,
    completed: bool,
    leg: str,
    declined: Optional[Dict[str, str]] = None,
    skipped: Optional[Dict[str, str]] = None,
    no_op: bool = False,
) -> List[str]:
    """Record every item of an apply batch in ``processed_<phase>``; the ids.

    One shape on both legs. Each of *task*'s ``expected_ids`` gets
    ``{status, details: {task_id, prior_changes_id, grouped_sha256, leg,
    reason?}, timestamp}``: ``declined`` / ``skipped`` with its reason
    (never ``applied``), else ``applied`` — ``no-op`` for a batch the
    executor read as changing nothing; the native leg has no such reading
    and records a verified no-op ``applied`` (documented, no
    reader tells the two apart) — for a finished batch, and ``failed``
    for every item of a batch that did not finish, which keeps it in a
    ``--resume``'s work set. ``grouped_sha256`` is the review the batch
    applies (its task's ``inputs``), so a later review's run can tell this
    cycle's records from its own (:func:`processed_record_counts`).
    """
    inputs = task.get("inputs") if isinstance(task.get("inputs"), dict) else {}
    details = {
        "task_id": str(task.get("task_id") or ""),
        "prior_changes_id": str(task.get("prior_changes_id") or ""),
        "grouped_sha256": str(inputs.get("grouped_sha256") or ""),
        "leg": leg,
    }
    declined = declined or {}
    skipped = skipped or {}
    items: List[str] = []
    for item_id in task.get("expected_ids") or []:
        item_id = str(item_id)
        if not item_id:
            continue
        if not completed:
            mark_item_processed_in_state(state, phase, item_id, "failed", dict(details))
        elif item_id in declined:
            mark_item_processed_in_state(
                state, phase, item_id, "declined",
                {**details, "reason": str(declined[item_id])})
        elif item_id in skipped:
            mark_item_processed_in_state(
                state, phase, item_id, "skipped",
                {**details, "reason": str(skipped[item_id])})
        else:
            mark_item_processed_in_state(
                state, phase, item_id, "no-op" if no_op else "applied", dict(details))
        items.append(item_id)
    return items


def processed_record_counts(
    record: Any, *, review_stamp: str = "", executor_leg: bool = False,
) -> bool:
    """Whether a ``processed_<phase>`` record keeps its item out of a
    ``--resume``'s work set (``apply_orchestrator_base`` step 23).

    Not a ``failed`` one (that batch is dispatched again, on both legs). Not
    a ``declined`` or ``skipped`` one stamped with another review than
    *review_stamp* (the current ``grouped.json``'s hash): an item an earlier
    review's batch did not apply, which a later review reports again, is
    offered again — as the executor leg offers it in the
    batch the later review makes — and never counted as applied. An
    ``applied`` record counts whatever review it names, so a native
    ``--resume`` never hands an applied item out twice. A record with no
    stamp counts, as before: absence of a stamp is not staleness. And on
    the executor leg (*executor_leg*) not one the executor wrote: the
    scheduler keeps that batch from its own result file under its own id,
    so dropping its items here would renumber the batches a stop's
    ``--human-task <batch>=skip`` names; a record the native host wrote
    still counts there, since no result file stands behind it.
    """
    if not isinstance(record, dict) or record.get("status") == "failed":
        return False
    details = record.get("details") if isinstance(record.get("details"), dict) else {}
    stamp = str(details.get("grouped_sha256") or "")
    if (review_stamp and stamp and stamp != review_stamp
            and record.get("status") in ("declined", "skipped")):
        return False
    if executor_leg and details.get("leg") == PROCESSED_LEG_EXECUTOR:
        return False
    return True


def compute_plan_hash(plan_path: Path) -> str:
    """Hash a plan's content the way ``state.json``'s ``plan_hash`` records it.

    Module-level so a *file-level* state writer — `finalize_tracking`, which
    edits the plan on the native leg — can re-stamp the field after its own
    edit without building a `StateManager` (which would read that edit as a
    human editing the plan and set `plan_changed`).
    """
    if plan_path.exists():
        content = plan_path.read_text(encoding="utf-8")
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    return ""


# --- Canonicalization & ID Generation ---

def canonicalize_hash_input(value) -> str:
    """Canonicalize a string for hash input.

    1. None/missing → ""
    2. Unicode NFC normalization
    3. Whitespace collapse (all runs → single space, strip)
    4. No case folding (casing preserved)
    """
    if value is None:
        return ""
    value = str(value)
    value = unicodedata.normalize("NFC", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def generate_group_id(group: Dict[str, Any], discriminator: int = 0) -> str:
    """
    Generate a stable identifier for a group based on its content.

    Uses theme + normalized suggestions + reference fields to create
    a hash that remains stable across re-runs.

    Args:
        group: A group dictionary with theme, suggestions, etc.
        discriminator: ``stamp_stable_ids``'s collision counter; ``0`` (the
            plain content hash) for every caller that computes an id to *join*
            on. Neither ``file`` nor ``line_range`` is hashed, so two
            word-identical findings in two files — which the grouper keeps
            apart on purpose — are two groups with one content hash; the
            counter is what tells them apart once stamped.

    Returns:
        A 16-character hex string identifier
    """
    # Extract stable identifying fields. The theme enters the hash at the
    # 50-character cut the grouper used to apply when it *built* themes: every
    # group persisted before 2026-09-13 carries a theme of at most 50 characters
    # (so this is the identity on it), and a theme built since — cut at a word
    # boundary within 60, with an ellipsis — hashes to what the old cut would
    # have produced. A theme is display text; a display change is not an
    # identity change, and the container goldens bake these ids in.
    theme = str(group.get("theme", ""))[:50]
    suggestions = group.get("suggestions", group.get("issues", []))

    # Normalize suggestions for hashing
    normalized = []
    for s in suggestions:
        normalized.append({
            "type": s.get("type", ""),
            "section": s.get("section", s.get("reference", "")),
            "details": str(s.get("details", s.get("desc", "")))[:200],  # Truncate for stability
        })

    payload: Dict[str, Any] = {"theme": theme, "suggestions": normalized}
    if discriminator:
        payload["discriminator"] = f"-{discriminator}"
    content = json.dumps(payload, sort_keys=True)
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def generate_suggestion_id(suggestion: Dict[str, Any], discriminator: int = 0) -> str:
    """Generate a stable 16-char hex hash for a suggestion.

    Uses title + type + full description + reference (parent group excluded
    for stability across regrouping). ``discriminator`` is the collision
    counter ``stamp_stable_ids`` applies (``0`` hashes the plain content; a
    non-zero value produces byte-for-byte the rehash it always stamped).
    """
    fields = {
        "v": ID_ALGO_VERSION,
        "title": canonicalize_hash_input(suggestion.get("title", "")),
        "type": canonicalize_hash_input(suggestion.get("type", "")),
        "description": canonicalize_hash_input(
            suggestion.get("details", suggestion.get("desc", suggestion.get("description", "")))
        ),
        "reference": canonicalize_hash_input(
            suggestion.get("reference", suggestion.get("section", ""))
        ),
    }
    if discriminator:
        fields["discriminator"] = f"-{discriminator}"
    content = json.dumps(fields, sort_keys=True)
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def group_id_short(group_id_16: str) -> str:
    """Truncate a 16-char group/suggestion hash to 8 chars for display."""
    return group_id_16[:8]


def _anchor(suggestion: Dict[str, Any]) -> Tuple[str, str]:
    """The (file, line_range) a code-review finding is pinned to; empty for a
    plan suggestion. This is exactly what the identity hash leaves out."""
    return (
        str(suggestion.get("file", "") or ""),
        str(suggestion.get("line_range", suggestion.get("line", "")) or ""),
    )


def match_issues_to_suggestions(
    issues: List[Dict[str, Any]],
    groups: List[Dict[str, Any]],
) -> Dict[int, Tuple[int, int]]:
    """Map each 1-based issue to the ``(group_index, suggestion_index)``
    (both 1-based) that holds it in *groups*.

    The join key is the content hash ``generate_suggestion_id`` computes — the
    one key an ``issues.json`` entry (written before stamping, so it carries no
    ``suggestion_hash``) and a ``grouped.json`` member share. Same-hash
    duplicates — one reviewer's word-identical finding in two files, which the
    grouper keeps as two groups — are told apart by the stamped hash when the
    issue carries one, else by ``file`` and ``line_range``, else by order of
    occurrence; each grouped location is consumed once, so the discriminated
    second suggestion is reached rather than the first location twice. An
    issue with no free location is left out of the map (never guessed).
    """
    locations: Dict[str, List[Tuple[Tuple[int, int], Dict[str, Any]]]] = {}
    for g_idx, group in enumerate(groups, 1):
        members = group.get("suggestions", group.get("issues", []))
        for s_idx, sugg in enumerate(members, 1):
            if isinstance(sugg, dict):
                locations.setdefault(generate_suggestion_id(sugg), []).append(
                    ((g_idx, s_idx), sugg)
                )

    mapping: Dict[int, Tuple[int, int]] = {}
    consumed: set = set()
    for issue_num, issue in enumerate(issues, 1):
        if not isinstance(issue, dict):
            continue
        pool = [
            (loc, sugg) for loc, sugg in locations.get(generate_suggestion_id(issue), [])
            if loc not in consumed
        ]
        if not pool:
            continue
        chosen: Optional[Tuple[int, int]] = None
        stamped = issue.get("suggestion_hash")
        if stamped:
            chosen = next(
                (loc for loc, sugg in pool if sugg.get("suggestion_hash") == stamped),
                None,
            )
        if chosen is None and len(pool) > 1:
            want = _anchor(issue)
            chosen = next((loc for loc, sugg in pool if _anchor(sugg) == want), None)
            if chosen is None:
                chosen = next(
                    (loc for loc, sugg in pool if _anchor(sugg)[0] == want[0]), None
                )
        if chosen is None:
            chosen = pool[0][0]
        consumed.add(chosen)
        mapping[issue_num] = chosen
    return mapping


def stamp_stable_ids(groups: List[Dict[str, Any]]) -> None:
    """Idempotently stamp group_hash, suggestion_hash, display_label, display_hash
    on each group and its suggestions. Includes collision detection with
    deterministic rehashing.

    Mutates groups in-place.
    """
    # Collect all canonical hashes for collision detection. Groups and
    # suggestions are two namespaces (a group may legitimately share a hash
    # with a suggestion), so each collides only with its own kind.
    all_hashes: Dict[str, Tuple[str, int, int]] = {}  # hash -> (type, g_idx, s_idx)

    def _discriminated(kind: str, label: str, hash_of) -> str:
        """The first of ``hash_of(0)``, ``hash_of(1)``, … not yet stamped on
        a *kind*. Deterministic: the n-th same-content item in stamping order
        always gets discriminator n-1, so a re-stamp of the same groups
        reproduces every id.

        No fixed cap: any number of models may return the same suggestion,
        and one boilerplate finding may land in any number of files. Each
        discriminator hashes to a new value and at most ``len(all_hashes)``
        are taken, so a free one turns up within that many steps; running
        past it means the truncated hash itself repeated."""
        limit = len(all_hashes)
        discriminator = 0
        candidate = hash_of(discriminator)
        while candidate in all_hashes and all_hashes[candidate][0] == kind:
            discriminator += 1
            if discriminator > limit:
                raise ValueError(
                    f"Cannot resolve hash collision for {kind} {label} "
                    f"after {limit} attempts"
                )
            candidate = hash_of(discriminator)
        return candidate

    for g_idx, group in enumerate(groups):
        g_num = g_idx + 1
        # Group hash, with the same collision loop the suggestions get. The
        # content hash reads neither `file` nor `line_range`, and the grouper
        # never merges across files, so one reviewer's boilerplate finding in
        # two files used to become two groups under ONE `group_hash` — every
        # consumer that filters by that hash (an apply-phase skip, an
        # `invalid` mark, a human decision) then hit both groups at once.
        ghash = _discriminated(
            "group", f"G{g_num}", lambda d, group=group: generate_group_id(group, d)
        )
        all_hashes[ghash] = ("group", g_idx, -1)
        group["group_hash"] = ghash
        group["display_label"] = f"G{g_num}"

        suggestions = group.get("suggestions", group.get("issues", []))
        for s_idx, sugg in enumerate(suggestions):
            s_num = s_idx + 1
            shash = _discriminated(
                "suggestion", f"G{g_num}S{s_num}",
                lambda d, sugg=sugg: generate_suggestion_id(sugg, d),
            )
            all_hashes[shash] = ("suggestion", g_idx, s_idx)
            sugg["suggestion_hash"] = shash
            sugg["display_label"] = f"G{g_num}S{s_num}"

    # Now compute display hashes (8-char prefix, extended on collision)
    _assign_display_hashes(groups)


def stamped_group_id(group: Any) -> str:
    """The id to file a record about *group* under: the ``group_hash``
    :func:`stamp_stable_ids` stamped, else the plain content hash.

    Never recompute :func:`generate_group_id` for this: same-content groups
    share the plain hash, so every one of them would get the first one's id
    (docs/development/review-results.md, "Stable group IDs")."""
    data = group.to_dict() if hasattr(group, "to_dict") else group
    return str(data.get("group_hash") or "") or generate_group_id(data)


def group_join_ids(groups: Sequence[Any]) -> List[Tuple[str, ...]]:
    """For each of *groups*, the ids a record about it may be filed under.

    The stamped ``group_hash``, and the plain content hash when it differs
    (the key records were filed under before every writer used the stamp),
    but each only when it names this one group: same-content groups share
    the plain hash, so a record under it cannot say which of them it meant.
    The first of them keeps it as its stamp; the rest are not joined on it
    (docs/development/review-results.md, "Stable group IDs")."""
    dicts = [g.to_dict() if hasattr(g, "to_dict") else g for g in groups]
    stamped = [str(d.get("group_hash") or "") for d in dicts]
    plain = [generate_group_id(d) for d in dicts]
    by_stamp: Dict[str, set] = {}
    by_any: Dict[str, set] = {}
    for index, (stamp, content) in enumerate(zip(stamped, plain)):
        if stamp:
            by_stamp.setdefault(stamp, set()).add(index)
            by_any.setdefault(stamp, set()).add(index)
        by_any.setdefault(content, set()).add(index)
    ids: List[Tuple[str, ...]] = []
    for index, (stamp, content) in enumerate(zip(stamped, plain)):
        keys: Tuple[str, ...] = ()
        if stamp and by_stamp[stamp] == {index}:
            keys += (stamp,)
        if content != stamp and by_any[content] == {index}:
            keys += (content,)
        ids.append(keys)
    return ids


def records_by_unique_id(
    records: Iterable[Any], *id_keys: str,
) -> Dict[str, Dict[str, Any]]:
    """``{id: record}`` over *records*, the id read from the first of
    *id_keys* a record carries. An id more than one record carries is left
    out: it cannot say which group each record was about (a validation file
    written before verdicts carried the stamped id gives every same-content
    group the first one's id)."""
    found: Dict[str, Dict[str, Any]] = {}
    shared: set = set()
    for record in records:
        if not isinstance(record, Mapping):
            continue
        rid = next((str(record[k]) for k in id_keys if record.get(k)), "")
        if rid in found:
            shared.add(rid)
        elif rid:
            found[rid] = record  # type: ignore[assignment]
    return {rid: record for rid, record in found.items() if rid not in shared}


def _assign_display_hashes(groups: List[Dict[str, Any]]) -> None:
    """Assign display_hash fields, extending from 8 to 10+ chars on prefix collision."""
    # Collect all canonical hashes and their locations
    entries: List[Tuple[str, str, Dict]] = []  # (canonical_hash, type, obj_ref)

    for group in groups:
        ghash = group.get("group_hash", "")
        if ghash:
            entries.append((ghash, "group", group))
        for sugg in group.get("suggestions", group.get("issues", [])):
            shash = sugg.get("suggestion_hash", "")
            if shash:
                entries.append((shash, "suggestion", sugg))

    # Group by 8-char prefix to detect collisions
    prefix_len = 8
    while prefix_len <= 16:
        prefix_groups: Dict[str, List[Tuple[str, str, Dict]]] = {}
        for canonical, etype, obj in entries:
            prefix = canonical[:prefix_len]
            if prefix not in prefix_groups:
                prefix_groups[prefix] = []
            prefix_groups[prefix].append((canonical, etype, obj))

        # Check for collisions (different canonical hashes sharing same prefix)
        has_collision = False
        for prefix, items in prefix_groups.items():
            unique_canonicals = set(canonical for canonical, _, _ in items)
            if len(unique_canonicals) > 1:
                has_collision = True
                break

        if not has_collision or prefix_len >= 16:
            break
        prefix_len += 2  # Extend by 2 chars at a time

    # Assign display hashes
    for canonical, etype, obj in entries:
        obj["display_hash"] = canonical[:prefix_len]


# --- Format Version Helpers ---

def get_format_version(data: dict) -> int:
    """Return format version of a loaded JSON file. Missing field = v1.

    NOT used for state.json — use get_state_schema_version() instead.
    """
    return data.get("format_version", 1)


def get_state_schema_version(data: dict) -> str:
    """Return schema version of state.json. Missing field = '1.0'."""
    return data.get("schema_version", "1.0")


def extract_versioned_payload(data, payload_key: str):
    """Extract payload from a versioned JSON envelope.

    Handles both v1 (bare payload, e.g., a raw list) and v2 (dict with
    format_version + payload_key). Returns (format_version, payload).
    """
    if isinstance(data, list):
        return (1, data)
    if isinstance(data, dict) and payload_key in data:
        return (get_format_version(data), data[payload_key])
    raise ValueError(f"Unexpected format: expected list or dict with '{payload_key}' key")


def load_groups_payload(data) -> List[Dict[str, Any]]:
    """Load groups from either v1 bare array or v2 envelope. Returns groups list."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "groups" in data:
        return data["groups"]
    raise ValueError("Unexpected grouped.json format: expected list or dict with 'groups' key")


def save_groups_payload(groups: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Wrap groups in v2 envelope for writing."""
    return {"format_version": CURRENT_FORMAT_VERSION, "groups": groups}


def handle_plan_hash_change(
    old_decisions: Dict[str, Any],
    old_groups: List[Dict[str, Any]],
    new_groups: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Remap decisions when plan content changes.

    Args:
        old_decisions: Previous human decisions keyed by group_id
        old_groups: Previous groups
        new_groups: Current groups after plan change

    Returns:
        Remapped decisions, dropping any that no longer match
    """
    # Build map of old group_ids to decisions
    old_id_to_decision = {}
    for old_group in old_groups:
        gid = generate_group_id(old_group)
        if gid in old_decisions:
            old_id_to_decision[gid] = old_decisions[gid]

    # Match new groups to old decisions
    remapped = {}
    for new_group in new_groups:
        new_gid = generate_group_id(new_group)
        if new_gid in old_id_to_decision:
            remapped[new_gid] = old_id_to_decision[new_gid].copy()
            remapped[new_gid]["remapped"] = True

    return remapped


#: ``state.json``'s record of the explicit resets: ``{key: when it was last
#: reset}`` for a top-level key a ``clear_*`` method or
#: :meth:`StateManager.clear_key` dropped (``--fresh`` calls them), and
#: ``{"*": when}`` (:data:`DOCUMENT_RESET`) for :meth:`StateManager.reset`.
#: :meth:`StateManager.save`'s merge reads it: what was reset since a writer
#: loaded the file is the resetter's, so that writer's stale view cannot
#: bring back what the reset dropped (docs/development/write-scheduler.md,
#: "Merge units").
STATE_RESETS_KEY = "state_resets"

#: The :data:`STATE_RESETS_KEY` entry :meth:`StateManager.reset` stamps: the
#: whole document was reset.
DOCUMENT_RESET = "*"

#: Twins of ``known_checks.APPLY_FIX_BATCH_CHECKS_KEY``,
#: ``scope_policy.STATE_KEY`` and ``scope_policy_runs.RUNS_KEY``, restated so
#: this low-level module imports none of them (a test pins the three).
_APPLY_FIX_BATCH_CHECKS_KEY = "apply_fix_batch_checks"
_SCOPE_POLICY_KEY = "scope_policy"
_SCOPE_POLICY_RUNS_KEY = "scope_policy_runs"

#: The per-task maps (``{task_id: value}``) one task's record spans: its
#: status and the reason, findings, check records, reset stamp, recorded
#: ``--human-task`` answer and dependency override written with it, and an
#: apply-code-fixes batch's check report. :meth:`StateManager.save` merges a
#: task's record as one unit.
_TASK_RECORD_MAPS: Tuple[str, ...] = (
    "task_status", "task_status_reasons", TASK_CHECK_FINDINGS_KEY,
    TASK_BATCH_CHECK_KEY, TASK_OWN_TEXT_KEY, TASK_OWN_CHECK_NOTE_KEY,
    TASK_BATCH_CHECK_ACCEPTED_KEY, TASK_BATCH_CHECK_REPEATS_KEY,
    TASK_CHECK_TREES_KEY, TASK_RESET_AT_KEY, HUMAN_TASK_DECISIONS_KEY,
    "dependency_overrides", _APPLY_FIX_BATCH_CHECKS_KEY,
)

#: The per-task lists (sorted task ids) whose membership is part of a task's
#: record.
_TASK_RECORD_LISTS: Tuple[str, ...] = (TASK_OWN_CHECK_RAN_KEY,)

#: The per-phase maps one phase's record spans (a start, a completion, a skip).
_PHASE_RECORD_MAPS: Tuple[str, ...] = (
    "phases_completed", "phases_started", "phases_skipped",
)

#: The keys :meth:`StateManager.record_task_titles` writes together: one
#: decomposition, merged as one unit.
_DECOMPOSITION_KEYS: Tuple[str, ...] = (
    "task_titles", "implement_task_ids", "implement_human_task_ids",
    IMPLEMENT_TASK_GRAPH_KEY,
)

#: The keys the plan-change check writes together: the hash of the plan as
#: last seen and the flag a human edit since then raised. One unit, so the
#: hash a writer records always travels with its own flag.
_PLAN_CHANGE_KEYS: Tuple[str, ...] = ("plan_hash", "plan_changed")

#: The journal unit of a plan edit the load detected (``("plan",)`` is a
#: mutator's write of the pair): this manager's unless the file already
#: records the hash it detected.
_PLAN_DETECTED: Tuple[str, ...] = ("plan", "detected")

#: Maps merged entry by entry, each entry whole (``metrics_left_out`` and
#: ``metrics_set_aside`` are ``metrics.LEFT_OUT_KEY`` and ``SET_ASIDE_KEY``;
#: ``scope_policy`` is keyed by review phase, ``scope_policy_runs`` by mode).
_ENTRY_MAPS: Tuple[str, ...] = (
    "metrics_progress", "metrics_left_out", "metrics_set_aside",
    _SCOPE_POLICY_KEY, _SCOPE_POLICY_RUNS_KEY,
)

#: The per-phase map of the judge's raw verdicts
#: (``human_decisions._persist_ingested_verdicts``), keyed by group id.
_VERDICTS_PREFIX = "human_decision_verdicts_"

#: Prefixes of the per-phase item maps (``processed_<phase>``,
#: ``human_decisions_<phase>``, ``human_decision_verdicts_<phase>``), merged
#: item by item, each item whole.
_ENTRY_MAP_PREFIXES: Tuple[str, ...] = (
    "processed_", "human_decisions_", _VERDICTS_PREFIX,
)

#: A key or entry one side of the merge does not have.
_ABSENT = object()


def _unit_of_key(key: str) -> Optional[Tuple[str, ...]]:
    """The journal unit a write of the whole top-level *key* is
    (:meth:`StateManager.set`), or ``None`` for a key merged in finer units,
    whose changes the value comparison finds entry by entry."""
    if key in _DECOMPOSITION_KEYS:
        return ("decomposition",)
    if key in _PLAN_CHANGE_KEYS:
        return ("plan",)
    if (key in _TASK_RECORD_MAPS or key in _TASK_RECORD_LISTS
            or key in _PHASE_RECORD_MAPS or key in _ENTRY_MAPS
            or key.startswith(_ENTRY_MAP_PREFIXES)
            or key in ("metrics", "tracked_files", STATE_RESETS_KEY)):
        return None
    return ("key", key)


def _table(document: Dict[str, Any], key: str) -> Dict[str, Any]:
    """*document*'s map at *key*, ``{}`` when it is absent or not a map."""
    value = document.get(key)
    return value if isinstance(value, dict) else {}


def _members(document: Dict[str, Any], key: str) -> set:
    """*document*'s list at *key* as a set of ids, empty when absent."""
    value = document.get(key)
    return {str(item) for item in value} if isinstance(value, list) else set()


def _put(document: Dict[str, Any], key: str, value: Any) -> None:
    """Set ``document[key]`` to *value*, or drop it for :data:`_ABSENT`.

    The merge's only write: it replaces a top-level value of the candidate
    document and never edits one in place, since the candidate shares its
    values with ``StateManager.state`` until the write succeeds.
    """
    if value is _ABSENT:
        document.pop(key, None)
    else:
        document[key] = value


def _adopt(container: Dict[str, Any], key: str, value: Any) -> None:
    """Set ``container[key]`` to *value* (drop it for :data:`_ABSENT`).

    A map or list already there is updated in place, so a reference a caller
    holds into ``StateManager.state`` stays the saved one.
    """
    if value is _ABSENT:
        container.pop(key, None)
        return
    current = container.get(key, _ABSENT)
    if current is value:
        return
    if isinstance(current, dict) and isinstance(value, dict):
        current.clear()
        current.update(value)
    elif isinstance(current, list) and isinstance(value, list):
        current[:] = value
    else:
        container[key] = value


def _adopt_document(target: Dict[str, Any], document: Dict[str, Any]) -> None:
    """Make *target* hold *document*'s top-level values, in place (:func:`_adopt`)."""
    for key in [key for key in target if key not in document]:
        del target[key]
    for key, value in document.items():
        _adopt(target, key, value)


def _place(
    base: Dict[str, Any], mine: Dict[str, Any], theirs: Dict[str, Any],
    key: str, value: Any, had_mine: bool,
) -> None:
    """Write a merged map or list back into *mine*. An empty one stays only
    where this manager has it and the file kept it (or never had it): the
    writers drop an emptied map, and a merge must not invent one."""
    if not value and not (had_mine and (key in theirs or key not in base)):
        mine.pop(key, None)
    else:
        _put(mine, key, value)


def _merge_whole(
    base: Dict[str, Any], mine: Dict[str, Any], theirs: Dict[str, Any],
    keys: Sequence[str], touched: bool = False,
) -> None:
    """Merge *keys* as one unit: the file's values unless this manager
    changed one of them (or wrote the unit, *touched*), then this
    manager's, all of them."""
    if touched or not keys:
        return
    sides = [tuple(d.get(key, _ABSENT) for key in keys) for d in (base, mine, theirs)]
    if sides[1] == sides[0] and sides[2] != sides[1]:
        for key, value in zip(keys, sides[2]):
            _put(mine, key, value)


def _merge_records(
    base: Dict[str, Any], mine: Dict[str, Any], theirs: Dict[str, Any],
    maps: Sequence[str], lists: Sequence[str] = (), reset_map: Optional[str] = None,
    touched: Iterable[str] = (),
) -> None:
    """Merge the records keyed by id across *maps* (and membership of
    *lists*), each record one unit.

    A record this manager neither wrote (*touched*: the ids its mutators
    wrote) nor left different from how it found it is the file's; any other
    is its own, every field of it, whatever the file's writer did to it.
    With *reset_map*, a record whose stamp there the file's writer changed
    and this manager did not (a start-over or ``--task`` rerun since this
    manager loaded) is the file's whatever this manager did: its view of the
    record predates the reset.
    """
    sides = (base, mine, theirs)
    wrote = {str(record_id) for record_id in touched}
    had = {name: name in mine for name in (*maps, *lists)}
    tables = {name: [_table(d, name) for d in sides] for name in maps}
    members = {name: [_members(d, name) for d in sides] for name in lists}
    # Only a record the file and this manager disagree on can change.
    ids: Dict[str, None] = {}
    for name in maps:
        own, file = tables[name][1], tables[name][2]
        if own != file:
            ids.update(dict.fromkeys(
                record_id for record_id in dict.fromkeys([*own, *file])
                if own.get(record_id, _ABSENT) != file.get(record_id, _ABSENT)))
    for name in lists:
        ids.update(dict.fromkeys(sorted(members[name][1] ^ members[name][2])))

    def record(side: int, record_id: str) -> Tuple[Any, ...]:
        return (
            tuple(tables[name][side].get(record_id, _ABSENT) for name in maps)
            + tuple(record_id in members[name][side] for name in lists)
        )

    taken = []
    for record_id in ids:
        was, own, file = (record(side, record_id) for side in range(3))
        if reset_map is not None:
            stamps = [tables[reset_map][side].get(record_id, _ABSENT) for side in range(3)]
            if stamps[2] != stamps[0] and stamps[1] == stamps[0]:
                taken.append(record_id)
                continue
        if own == was and record_id not in wrote:
            taken.append(record_id)
    if not taken:
        return
    for name in maps:
        target = dict(tables[name][1])
        for record_id in taken:
            value = tables[name][2].get(record_id, _ABSENT)
            if value is _ABSENT:
                target.pop(record_id, None)
            else:
                target[record_id] = value
        _place(base, mine, theirs, name, target, had[name])
    for name in lists:
        kept = set(members[name][1])
        for record_id in taken:
            if record_id in members[name][2]:
                kept.add(record_id)
            else:
                kept.discard(record_id)
        _place(base, mine, theirs, name, sorted(kept), had[name])


def _merge_metric_list(phase: str, was: Any, own: Any, file: Any) -> Any:
    """One phase's ``metrics`` list after both writers changed it.

    ``record_metric_in_state`` only ever appends an entry or replaces one in
    place, so index *i* of each side is the same record as the baseline's
    *i*. An entry this manager replaced replaces the file's when the file
    still holds the baseline's; every other entry this manager added or
    replaced is added by the identity rule (``metrics.merge_recorded_metric``):
    a second record of one event collapses into the file's. A list that does
    not have that shape is this manager's.
    """
    # Imported here to keep full_workflow_orchestrator, which loads this module, light.
    from . import metrics as _metrics

    before = [] if was is _ABSENT else was
    if not (isinstance(before, list) and isinstance(own, list)
            and isinstance(file, list)
            and len(own) >= len(before) and len(file) >= len(before)):
        return own
    merged = list(file)
    added = []
    for index, entry in enumerate(own):
        if index < len(before):
            if entry == before[index]:
                continue
            if merged[index] == before[index]:
                merged[index] = entry
                continue
        added.append(entry)
    for entry in added:
        _metrics.merge_recorded_metric(merged, phase, entry)
    return merged


def _merge_metrics(
    base: Dict[str, Any], mine: Dict[str, Any], theirs: Dict[str, Any], key: str,
) -> None:
    """Merge ``metrics`` phase by phase (:func:`_merge_metric_list` where
    both writers changed a phase's list, else whichever did)."""
    if not all(isinstance(d.get(key, {}), dict) for d in (base, mine, theirs)):
        _merge_whole(base, mine, theirs, (key,))
        return
    had = key in mine
    was, own, file = (_table(d, key) for d in (base, mine, theirs))
    if file == was:
        return
    target = dict(own)
    for phase in dict.fromkeys([*own, *file, *was]):
        before, mine_list, their_list = (
            t.get(phase, _ABSENT) for t in (was, own, file))
        # Both writers' lists equal is no reason to skip the identity rule
        # when both changed it: two managers that recorded one event with the
        # same timestamp (Windows' clock ticks every ~16 ms, so two quick
        # records share one) made the same change twice, and that second
        # record collapses, with its `[METRICS_DUPLICATE]` line, as one whose
        # timestamp differs does.
        if their_list == before:
            continue
        if mine_list == before:
            _put(target, phase, their_list)
        elif mine_list is not _ABSENT and their_list is not _ABSENT:
            target[phase] = _merge_metric_list(phase, before, mine_list, their_list)
    _place(base, mine, theirs, key, target, had)


def _by_path(value: Any) -> Optional[Dict[str, Any]]:
    """A ``tracked_files`` list keyed by path; ``None`` when it is not one
    entry per path."""
    if value is _ABSENT:
        return {}
    if not isinstance(value, list):
        return None
    keyed: Dict[str, Any] = {}
    for entry in value:
        path = entry.get("path") if isinstance(entry, dict) else None
        if not isinstance(path, str) or path in keyed:
            return None
        keyed[path] = entry
    return keyed


def _merge_tracked_files(
    base: Dict[str, Any], mine: Dict[str, Any], theirs: Dict[str, Any], key: str,
    touched: Iterable[str] = (),
) -> None:
    """Merge ``tracked_files`` path by path, each entry whole, when both
    writers changed it (else whichever did); an entry this manager wrote
    (*touched*, :meth:`StateManager.track_file`) is its own. A list that is
    not one entry per path is this manager's."""
    wrote = set(touched)
    was, own, file = (d.get(key, _ABSENT) for d in (base, mine, theirs))
    if file == own or file == was:
        return
    if own == was and not wrote:
        _put(mine, key, file)
        return
    keyed = [_by_path(value) for value in (was, own, file)]
    if any(table is None for table in keyed):
        return
    before, mine_paths, their_paths = keyed
    merged = []
    for path in dict.fromkeys([*mine_paths, *their_paths]):
        entry = mine_paths.get(path, _ABSENT)
        if path not in wrote and entry == before.get(path, _ABSENT):
            entry = their_paths.get(path, _ABSENT)
        if entry is not _ABSENT:
            merged.append(entry)
    _put(mine, key, merged)


def _merge_state_into(
    base: Dict[str, Any], mine: Dict[str, Any], theirs: Dict[str, Any],
    touched: Iterable[Tuple[str, ...]] = (),
) -> None:
    """:meth:`StateManager.save`'s merge of the file (*theirs*) into *mine*.

    *mine* is a shallow copy of the saving manager's ``state``: the merge
    replaces its top-level values (:func:`_put`) and edits none in place.
    *base* is the file as that manager last read or wrote it, and *touched*
    its journal: the units its mutators wrote since (``("task", id)``,
    ``("phase", name)``, ``("entry", key, id)``, ``("tracked", path)``,
    ``("decomposition",)``, ``("plan",)``, ``("key", key)``). A unit counts
    as this manager's change when it is in the journal or differs from
    *base*; the units are listed in ``save()``'s docstring.
    """
    journal = list(touched)
    stamps = [_table(d, STATE_RESETS_KEY) for d in (base, mine, theirs)]
    document = [s.get(DOCUMENT_RESET, _ABSENT) for s in stamps]
    if document[1] != document[0]:
        return  # this manager reset the whole document: it is its own
    if document[2] != document[0]:
        # Another writer reset the whole document since this manager loaded.
        mine.clear()
        mine.update(theirs)
        return

    done = {STATE_RESETS_KEY}
    for key in dict.fromkeys([*stamps[1], *stamps[2]]):
        if key == DOCUMENT_RESET:
            continue
        before, own, file = (s.get(key, _ABSENT) for s in stamps)
        if own != before:
            done.add(key)
        elif file != before:
            _put(mine, key, theirs.get(key, _ABSENT))
            done.add(key)
    _merge_records(base, mine, theirs, (STATE_RESETS_KEY,))

    def wrote(kind: str, *within: str) -> List[str]:
        size = len(within)
        return [unit[1 + size] for unit in journal
                if len(unit) == 2 + size and unit[0] == kind
                and tuple(unit[1:1 + size]) == within]

    task_maps = [name for name in _TASK_RECORD_MAPS if name not in done]
    task_lists = [name for name in _TASK_RECORD_LISTS if name not in done]
    _merge_records(
        base, mine, theirs, task_maps, task_lists,
        reset_map=TASK_RESET_AT_KEY if TASK_RESET_AT_KEY in task_maps else None,
        touched=wrote("task"))
    phase_maps = [name for name in _PHASE_RECORD_MAPS if name not in done]
    _merge_records(base, mine, theirs, phase_maps, touched=wrote("phase"))
    decomposition = [name for name in _DECOMPOSITION_KEYS if name not in done]
    _merge_whole(base, mine, theirs, decomposition,
                 touched=("decomposition",) in journal)
    plan_change = [name for name in _PLAN_CHANGE_KEYS if name not in done]
    if ("plan",) not in journal and _PLAN_DETECTED in journal and plan_change:
        # Only this manager's load found the edit. A file that records the
        # hash it found was written by someone who saw that same plan: the
        # flag beside it there (raised, or consumed) is the newer word.
        if theirs.get("plan_hash", _ABSENT) == mine.get("plan_hash", _ABSENT):
            for name in plan_change:
                _put(mine, name, theirs.get(name, _ABSENT))
    else:
        _merge_whole(base, mine, theirs, plan_change, touched=("plan",) in journal)
    done.update(task_maps, task_lists, phase_maps, decomposition, plan_change)

    for key in dict.fromkeys([*mine, *theirs, *base]):
        if key in done:
            continue
        if key in _ENTRY_MAPS or key.startswith(_ENTRY_MAP_PREFIXES):
            if all(isinstance(d.get(key, {}), dict) for d in (base, mine, theirs)):
                _merge_records(base, mine, theirs, (key,), touched=wrote("entry", key))
            else:
                _merge_whole(base, mine, theirs, (key,))
        elif key == "metrics":
            _merge_metrics(base, mine, theirs, key)
        elif key == "tracked_files":
            _merge_tracked_files(base, mine, theirs, key, touched=wrote("tracked"))
        else:
            _merge_whole(base, mine, theirs, (key,), touched=("key", key) in journal)


def _parse_state_text(text: Optional[str]) -> Optional[Dict[str, Any]]:
    """*text* as a state document, judge names upgraded (``upgrade_legacy``,
    as every read of the file upgrades them); ``None`` for no text, text
    that is not JSON, or JSON that is not an object."""
    if text is None:
        return None
    try:
        document = upgrade_legacy(json.loads(text))
    except ValueError:
        return None
    return document if isinstance(document, dict) else None


class StateManager:
    """Manages persistent state for multi-LLM skill sessions."""

    SCHEMA_VERSION = "2.0"

    def __init__(
        self,
        plan_path: Path,
        state_dir: Optional[Path] = None,
        *,
        read_only: bool = False,
    ):
        """
        Initialize state manager.

        Args:
            plan_path: Path to the plan being implemented
            state_dir: Deprecated, ignored. State now stored in plan directory.
            read_only: Load for reading only, and never touch the file: no
                old-location move, no judge-name write-back (the upgrade
                still applies in memory), and ``save()`` raises. For the
                commands that only report (``status``, ``util next-command``,
                ``--status``), which a host polls while another process may
                be writing ``state.json``.
        """
        self.plan_path = Path(plan_path).resolve()
        self.read_only = read_only

        # State file lives in the plan's output directory
        self.plan_dir = get_output_dir(self.plan_path)
        self.state_file = self.plan_dir / "state.json"

        self.state: Dict[str, Any] = {}
        #: ``state.json``'s text as this manager last read or wrote it
        #: (``None`` for none). The document it holds (:meth:`_baseline`) is
        #: what :meth:`save` compares ``state`` with to find the changes no
        #: mutator journaled (a caller editing ``state`` directly); a file
        #: still holding exactly this text has no other writer's change to
        #: merge.
        self._baseline_text: Optional[str] = None
        self._baseline_document: Optional[Dict[str, Any]] = None
        #: The journal: the merge units this manager's mutators wrote since
        #: it last read or wrote the file (:func:`_merge_state_into` names
        #: their shapes). :meth:`save` keeps a journaled unit as this manager
        #: has it even when its value equals the baseline's, since a write
        #: that repeats the recorded value is still a write.
        self._touched: set = set()
        if not read_only:
            self._migrate_from_old_location()  # Check for old state file
        self._load_or_create()

    def _migrate_from_old_location(self) -> None:
        """Migrate state file from old hash-based location if it exists.

        Copy, then delete, rather than a rename: the old location is in the
        skill's folder, often on another filesystem. The old file's bytes
        are written as they are, by ``state_file``'s writer (``write_bytes``:
        owner-only, through the output folder held below the plan's
        directory, docs/development/write-safety.md#plan-output-containment),
        under the state lock from the check that ``state.json`` is absent to
        the old file's removal. The old file is removed only once that write
        succeeded, and kept on any failure, a refused write included.

        Note: Migration is silent unless verbose/debug logging is enabled.
        """
        old_state_dir = Path(__file__).parent.parent / "state"
        path_hash = hashlib.sha256(str(self.plan_path).encode()).hexdigest()[:16]
        old_state_file = old_state_dir / f"{path_hash}.json"

        if not old_state_file.exists() or self.state_file.exists():
            return
        try:
            # The lock lives beside the file, so its folder is made first.
            self.plan_dir.mkdir(parents=True, exist_ok=True)
            with _state_file.locked(self.state_file):
                if self.state_file.exists():
                    return  # another process wrote it meanwhile
                data = old_state_file.read_bytes()
                # Validate JSON is parseable before migrating
                json.loads(data.decode("utf-8"))
                _state_file.write_bytes(self.state_file, data)
                os.unlink(old_state_file)
            logger.debug(f"Migrated state file to: {self.state_file}")
        except (json.JSONDecodeError, UnicodeDecodeError, OSError) as e:
            # Log warning but continue - old state may be corrupt (bad JSON or
            # bad UTF-8) or inaccessible
            logger.warning(f"Failed to migrate state from {old_state_file}: {e}")
            # Don't delete old file on failure - let user investigate

    def _compute_plan_path_hash(self) -> str:
        """Compute hash of plan PATH for state file naming (stable across content edits)."""
        path_str = str(self.plan_path)
        return hashlib.sha256(path_str.encode()).hexdigest()[:16]

    def _compute_plan_hash(self) -> str:
        """Compute hash of plan content for change detection."""
        return compute_plan_hash(self.plan_path)

    def _create_initial_state(self) -> Dict[str, Any]:
        """Create initial state structure."""
        return {
            "schema_version": self.SCHEMA_VERSION,
            "plan_path": str(self.plan_path),
            "plan_hash": self._compute_plan_hash(),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            # The diff base code review and apply-code-fixes fall back to.
            # Before the first commit it is the empty tree (every file is
            # new), not a refusal: a new state used to raise `GitError` here,
            # and with it every mode on a plain `git init`. Outside a
            # repository there is none to record (`_head_at_start`).
            "head_at_start": self._head_at_start(),
            "branch_name": get_branch_name() or "unknown",
            "review_phase_completed": False,
            "tracked_files": [],
            "task_status": {},
            "phases_completed": {},
            "phases_skipped": {},
        }

    def _head_at_start(self) -> str:
        """The commit a new state starts from (``git_utils.head_or_empty_tree``,
        run where every git call of the run is: the current directory).

        Outside a git repository this raises ``unattended.NeedsHuman`` (exit 3,
        its message printed alone) instead of the ``GitError`` traceback: every
        workflow phase diffs against this commit or records git state, so the
        run cannot start, and the user only has to make the project a
        repository. Any other git failure (a broken ref) is raised as it is."""
        try:
            return head_or_empty_tree()
        except GitError:
            if get_project_root_from_dir() is not None:
                raise
            raise NeedsHuman(
                f"ERROR: {os.getcwd()} is not inside a git repository, so no "
                f"workflow state could be started for {self.plan_path}: every phase "
                f"records the commit the run starts from and diffs against it. Run "
                f"the command from inside the project's repository, or make the "
                f"project one (`git init`; a first commit is optional), then run it "
                f"again."
            ) from None

    def _load_or_create(self) -> None:
        """Load existing state or create new one."""
        if self.state_file.exists():
            try:
                self.state, read_text = self._read_upgraded_text()
                if not isinstance(self.state, dict):
                    # Parsed, but not a state (`[]`, a number): read as an
                    # unparseable one is, rather than failing on `.get`
                    # below (`record_commit_range` documents replacing it).
                    raise json.JSONDecodeError("state.json is not a JSON object", "", 0)
                # The file as read, before the plan-change check below, so a
                # flag it sets is this manager's change and the save carries it.
                self._remember_baseline(read_text)

                # Check for plan changes. Deliberately set-only: the flag is
                # cleared by whoever CONSUMES it, never by a bare load.
                # Setting it also re-stamps `plan_hash`, so the very next load
                # finds the hash agreeing — and a clear-on-agreement branch
                # therefore erased a genuine human edit as soon as any
                # intermediate process loaded and saved between the edit and
                # `implement --resume` (`full`'s `_record_progress` does
                # exactly that before every step; so do `review-tasks` and
                # `check_workflow_prerequisites`). Stale residue is kept out
                # at the other end instead, by every plugin-made plan edit
                # re-stamping the hash through `refresh_plan_hash()` (F1,
                # audited 2026-09-16).
                current_hash = self._compute_plan_hash()
                if self.state.get("plan_hash") != current_hash:
                    self.state["plan_hash"] = current_hash
                    self.state["plan_changed"] = True
                    # Journaled: the save writes the detected hash with its
                    # flag, also over an older flag another writer consumed
                    # meanwhile (docs/development/write-scheduler.md, "Merge
                    # units").
                    self._touch(*_PLAN_DETECTED)

            except json.JSONDecodeError:
                self.state = self._create_initial_state()
        else:
            self.state = self._create_initial_state()

    def _read_upgraded(self) -> Any:
        """``state.json`` with every legacy judge spelling upgraded.

        A run started before the judge rename recorded its decisions as
        ``claude_auto_decide*``; they are read as the host-neutral names, so
        ``--resume`` crosses the upgrade. An upgrade that changed something is
        also written back at once, because a load is not always followed by a
        save — a native-leg ``--resume`` of an apply phase saves nothing until
        the host's ``--mark-completed`` — and the host reads this file raw,
        filtering ``human_decisions_{phase}`` on the new names, for its
        "Decided by the judge agent" section. Not under
        ``read_only``, and never when nothing changed.

        Raises what ``open``/``json.loads`` raise; a failed write-back does not.
        """
        return self._read_upgraded_text()[0]

    def _read_upgraded_text(self) -> Tuple[Any, str]:
        """:meth:`_read_upgraded`, and the text it read."""
        with open(self.state_file, "r", encoding="utf-8") as f:
            text = f.read()
        loaded = upgrade_legacy(json.loads(text))
        if (not self.read_only and isinstance(loaded, dict)
                and loaded != json.loads(text)):
            self._write_back_upgrade(loaded, text)
        return loaded, text

    def _remember_baseline(self, text: Optional[str]) -> None:
        """Take *text* (``None``: no file) as the file this manager last read
        or wrote."""
        self._baseline_text = text
        self._baseline_document = None

    def _baseline(self) -> Dict[str, Any]:
        """The document :attr:`_baseline_text` holds, judge names upgraded
        as every read upgrades them; ``{}`` for none."""
        if self._baseline_document is None:
            parsed = _parse_state_text(self._baseline_text)
            self._baseline_document = parsed if parsed is not None else {}
        return self._baseline_document

    def _write_back_upgrade(self, document: Dict[str, Any], read_text: str) -> None:
        """Persist the judge-name upgrade of *read_text*, and only that.

        The document is written as loaded — no ``updated_at`` stamp, no
        plan-change flag — so the write renames keys and values and changes
        nothing else. Skipped when the file no longer holds *read_text*:
        another process saved in between, and its file is the newer one.
        The native writers' shared lock covers both comparison and replacement
        so a completion cannot land between them and then be overwritten.
        """
        # Imported here to keep full_workflow_orchestrator, which loads this module, light.
        from .metrics import state_file_lock

        try:
            with state_file_lock(self.state_file):
                with open(self.state_file, "r", encoding="utf-8") as f:
                    if f.read() != read_text:
                        return
                self._write_atomic(document)
        except OSError as exc:
            # The in-memory upgrade still holds, and every Python reader maps
            # the old names; the host's raw read is the only one that misses.
            logger.warning(
                "Could not write the judge-name upgrade back to %s: %s",
                self.state_file, exc,
            )

    def _validate_state(self, state: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate state against schema.

        Args:
            state: State dictionary to validate

        Returns:
            Tuple of (is_valid, error_messages)
        """
        try:
            is_valid, errors = validate_state_file(state)
            return is_valid, errors
        except Exception as e:
            # If schema validation fails, log but allow save
            # (schema might not exist yet or validation might be unavailable)
            return True, [str(e)]

    def save(self) -> None:
        """Merge this manager's changes into ``state.json`` and write it.

        Under ``metrics.state_file_lock``, the lock every raw writer of the
        file holds, the file is read again and only what this manager changed
        since it last read or wrote the file is applied over it
        (:func:`_merge_state_into`). The merge builds a candidate document
        and leaves ``state`` alone; ``state`` adopts the candidate only once
        it is written, so a failed write leaves ``state``, the baseline and
        the journal as they were, and a retry merges afresh. The merge works
        in units, never field by field inside one:

        - **A task's record**: its entry in every map of
          :data:`_TASK_RECORD_MAPS` (status, reason, findings, check
          records, reset stamp, ``--human-task`` answer, dependency
          override, an apply batch's check report) and its membership of
          :data:`_TASK_RECORD_LISTS`.
        - **A phase's record**: its entries in ``phases_completed``,
          ``phases_started`` and ``phases_skipped``.
        - **An entry's record**: one entry of a ``processed_<phase>``,
          ``human_decisions_<phase>`` or ``human_decision_verdicts_<phase>``
          map, of ``metrics_progress``, ``metrics_left_out`` or
          ``metrics_set_aside``, of ``scope_policy`` (by review phase) or of
          ``scope_policy_runs`` (by mode).
        - **The decomposition**: :data:`_DECOMPOSITION_KEYS`, together.
        - **The plan-change record**: ``plan_hash`` and ``plan_changed``,
          together. An edit this manager's load detected is its change
          unless the file already records the hash it detected (whoever
          wrote that saw the same plan, so the flag there stands).
        - **Lists**: ``metrics`` phase by phase, entry by entry, by
          ``record_metric_in_state``'s identity rule (two records of one
          event are one entry); ``tracked_files`` entry by entry, by path.
        - **Every other top-level key**: one value.

        A unit is this manager's change when one of its mutators wrote it
        (the journal: ``update_task_status``, ``mark_phase_completed``,
        ``set_metrics_left_out``, ``set`` of a whole-value key, the load's
        plan-change check, :meth:`journal_entry` for the scope-policy
        records, ...; a write that repeats the recorded value counts) or
        when its value differs from the baseline (the fallback, for a
        caller that edits ``state`` directly or
        through a raw-dict helper: such a write that repeats the recorded
        value is not seen). This manager's changes are its own, whole,
        whatever the other writer did to them; every other unit is the
        file's, so a record another writer made meanwhile is kept. Explicit
        resets are authoritative: a key a
        ``clear_*`` method or :meth:`clear_key` dropped is this manager's
        whole (another writer's additions to it included), and a key
        another writer reset since this manager loaded
        (:data:`STATE_RESETS_KEY`) is the file's, so this manager's stale
        view cannot bring it back. :meth:`reset` does the same for the
        whole document. A task the file's writer reset
        (``implement_task_reset_at``, a start-over or a ``--task`` rerun) is
        the file's the same way, unless this manager reset it too. An
        absent, unreadable or non-object file is written whole. Written by
        temp file + ``os.replace``.

        The state lock is the innermost lock: a caller may hold its own
        (the scheduler's ``_effects_lock``), but nothing is taken while this
        one is held. A lock not free within ``state_file.STATE_LOCK_TIMEOUT_S``
        raises ``StateLockTimeout`` with nothing written; the changes stay in
        memory for the next ``save()``.

        Raises:
            IOError: If the save operation fails, ``StateLockTimeout`` included
            RuntimeError: On a ``read_only`` manager
        """
        if self.read_only:
            raise RuntimeError(
                f"read-only StateManager for {self.plan_path} cannot save"
            )
        # Imported here to keep full_workflow_orchestrator, which loads this module, light.
        from .metrics import state_file_lock

        candidate = dict(self.state)
        # The lock lives beside the file; a folder that does not exist yet
        # has nothing to lock, so it is made first.
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with state_file_lock(self.state_file):
            on_disk = self._read_current_text()
            # A file still holding the text this manager last read or wrote
            # has nothing of another writer's to merge.
            current = (
                _parse_state_text(on_disk)
                if on_disk is not None and on_disk != self._baseline_text else None
            )
            if current is not None:
                _merge_state_into(self._baseline(), candidate, current, self._touched)
            candidate["updated_at"] = datetime.now().isoformat()
            written = self._write_atomic(candidate)
        _adopt_document(self.state, candidate)
        self._remember_baseline(written)
        self._touched = set()

        is_valid, errors = self._validate_state(self.state)
        if not is_valid:
            # Log validation errors; the save has gone ahead
            warnings.warn(f"State validation warnings: {errors}")

    def _read_current_text(self) -> Optional[str]:
        """``state.json``'s text as it is now, for :meth:`save`; ``None`` when
        it is absent or unreadable."""
        try:
            with open(self.state_file, "r", encoding="utf-8") as f:
                return f.read()
        except (OSError, ValueError):
            return None

    def _write_atomic(self, document: Dict[str, Any]) -> str:
        """Write *document* to ``state.json`` (``state_file.write_document``:
        temp file and ``os.replace``). Returns the JSON text written.

        Raises:
            IOError: If the write fails
        """
        try:
            return _state_file.write_document(self.state_file, document)
        except Exception as e:
            raise IOError(f"Failed to save state: {e}") from e

    def reload(self) -> None:
        """Re-read ``state.json`` from disk, replacing the in-memory dict.

        **Every unsaved in-memory change is discarded** — a caller with pending
        edits must ``save()`` first. ``save()`` merges, so another writer's
        work (``finalize_tracking.py``'s ``tracked_files``) survives the next
        save either way; this makes ``state`` show it at once, and it is what
        a caller wants after a file-level helper changed a value this object
        has also changed, where the merge would keep this object's value.

        Unlike construction, this does not re-run the plan-change detection:
        `plan_changed` answers "did a human edit the plan since the last
        session", which is a question about the session, not about a re-read
        mid-run (a write phase edits the plan itself).
        """
        if not self.state_file.exists():
            return
        try:
            loaded, read_text = self._read_upgraded_text()
        except (json.JSONDecodeError, OSError):
            # A corrupt or unreadable file is not worth losing the dict we hold:
            # the next `save()` rewrites it wholesale anyway.
            return
        if isinstance(loaded, dict):
            self.state = loaded
            self._remember_baseline(read_text)
            self._touched = set()

    def get(self, key: str, default: Any = None) -> Any:
        """Get a state value."""
        return self.state.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a state value.

        A key merged as one value is journaled (:meth:`save` keeps it as set
        here, even when the value repeats the recorded one); a key merged in
        finer units (a task map, ``tracked_files``, ...) is compared entry
        by entry instead, so an entry set to the value it had is not seen as
        written: record those through their family's mutator
        (:meth:`record_human_task_answers`, :meth:`set_metrics_left_out`,
        ...), which journals the entries it writes.
        """
        self.state[key] = value
        unit = _unit_of_key(key)
        if unit is not None:
            self._touch(*unit)

    def _touch(self, *unit: str) -> None:
        """Journal *unit* as written by this manager (see :attr:`_touched`)."""
        self._touched.add(tuple(str(part) for part in unit))

    def journal_entry(self, key: str, entry_id: str) -> None:
        """Journal entry *entry_id* of the map *key* as written by this manager.

        For a module that writes its own record into :attr:`state` with a
        raw-dict helper (the scope-policy writers of ``scope_policy``,
        ``scope_apply`` and ``scope_policy_runs``): :meth:`save` then keeps
        that entry as this manager has it, whole, even when the write
        repeated the recorded value. Journal only an entry the helper
        wrote; one it left alone stays the file's.

        *key* must be a map merged entry by entry (:data:`_ENTRY_MAPS`, or a
        key with one of :data:`_ENTRY_MAP_PREFIXES`); any other key raises
        ``ValueError``, since the merge would ignore the unit
        (docs/development/write-scheduler.md, "Merge units").
        """
        if key not in _ENTRY_MAPS and not key.startswith(_ENTRY_MAP_PREFIXES):
            raise ValueError(f"{key!r} is not a map merged entry by entry")
        self._touch("entry", key, entry_id)

    # --- Metrics (in-memory; see utils/metrics.py for the file-level CLI) ---

    def start_metrics_phase(self, phase: str, total_batches: int) -> None:
        """Stamp ``metrics_progress.{phase}`` so ETAs have a baseline.

        The in-memory twin of ``metrics.start_phase``. Routing metrics through
        this object rather than through ``metrics.py``'s own reader/writer is
        what stops the two racing on ``state.json`` — see :meth:`reload`.
        """
        # Imported here to keep full_workflow_orchestrator, which loads this module, light.
        from . import metrics as _metrics

        _metrics.start_phase_in_state(self.state, phase, int(total_batches))
        self._touch("entry", "metrics_progress", phase)

    def finish_metrics_phase(
        self, phase: str
    ) -> Optional[Tuple[Optional[int], str]]:
        """The in-memory twin of ``metrics.finish_phase``.

        Returns ``(elapsed_ms, line)`` — the closing ``[ETA] … phase complete``
        line is handed back rather than printed, the way :meth:`record_metric`
        already hands back its own, so the scheduler can route it to the phase
        log the rest of that run's ETA lines went to (F7).
        """
        # Imported here to keep full_workflow_orchestrator, which loads this module, light.
        from . import metrics as _metrics

        started = phase in (self.state.get("metrics_progress") or {})
        finished = _metrics.finish_phase_in_state(self.state, phase)
        if finished is not None:
            # What the helper cleared is this manager's write: the phase's
            # left-out and set-aside tasks, and its progress entry when it
            # had one (a run that dispatched nothing has none to clear).
            keys = [_metrics.LEFT_OUT_KEY, _metrics.SET_ASIDE_KEY]
            if started:
                keys.append("metrics_progress")
            for key in keys:
                self._touch("entry", key, phase)
        return finished

    def set_metrics_left_out(self, phase: str, tasks: Mapping[str, str]) -> None:
        """Replace *phase*'s left-out tasks (``metrics.LEFT_OUT_KEY``; ``{}``
        clears them), journaled: a replacement that repeats the recorded
        tasks, or clears tasks this manager never saw, is still this
        manager's write."""
        # Imported here to keep full_workflow_orchestrator, which loads this module, light.
        from . import metrics as _metrics

        _metrics.set_left_out_in_state(self.state, phase, tasks)
        self._touch("entry", _metrics.LEFT_OUT_KEY, phase)

    def set_metrics_set_aside(self, phase: str, tasks: Mapping[str, str]) -> None:
        """Replace *phase*'s set-aside tasks (``metrics.SET_ASIDE_KEY``;
        ``{}`` clears them), journaled as :meth:`set_metrics_left_out` is."""
        # Imported here to keep full_workflow_orchestrator, which loads this module, light.
        from . import metrics as _metrics

        _metrics.set_set_aside_in_state(self.state, phase, tasks)
        self._touch("entry", _metrics.SET_ASIDE_KEY, phase)

    def set_metrics_total(self, phase: str, total: int) -> bool:
        """Re-stamp ``metrics_progress.{phase}.total_batches`` to *total*, the
        total the run's ``[ETA]`` lines count over, journaled. ``False``, and
        nothing written, when the phase has no progress entry."""
        progress = (self.state.get("metrics_progress") or {}).get(phase)
        if not isinstance(progress, dict):
            return False
        progress["total_batches"] = total
        self._touch("entry", "metrics_progress", phase)
        return True

    def record_metric(self, phase: str, label: str, **kwargs: Any) -> Optional[str]:
        """Append one ``metrics.{phase}`` entry in memory; ``save()`` persists it.

        The in-memory twin of ``metrics.record_metric``; returns the rendered
        ``[ETA]`` line (or None) for the caller to place, and prints nothing.
        """
        # Imported here to keep full_workflow_orchestrator, which loads this module, light.
        from . import metrics as _metrics

        return _metrics.record_metric_in_state(self.state, phase, label, **kwargs)

    def update_task_status(self, task_id: str, status: str, reason: Optional[str] = None) -> None:
        """Update status of a task.

        Args:
            task_id: Task identifier
            status: New status value
            reason: Optional reason for the status change (e.g., why a task was skipped)
        """
        update_task_status_in_state(self.state, task_id, status, reason)
        self._touch("task", task_id)

    def get_task_status(self, task_id: str) -> Optional[str]:
        """Get status of a task."""
        return self.state.get("task_status", {}).get(task_id)

    def get_task_status_reason(self, task_id: str) -> Optional[str]:
        """Get the reason for a task's current status."""
        return self.state.get("task_status_reasons", {}).get(task_id)

    def get_all_task_statuses(self) -> Dict[str, str]:
        """Get all task statuses."""
        return self.state.get("task_status", {}).copy()

    #: The id shape every task the task decomposer generates carries — mirrors
    #: ``utils.task_decomposer.TASK_ID_PATTERN``. Restated here rather than
    #: imported so this low-level module stays free of a dependency on the
    #: (much heavier) decomposer; if that pattern ever changes, this one has to
    #: follow. ``task_status`` is one flat map shared by every write-batch
    #: scheduler: implement's own decomposed tasks AND the batch ids the
    #: apply-suggestions / apply-code-fixes / apply-task-suggestions phases
    #: assign their write batches (``apply-batch-N``, ``apply-fix-batch-N``,
    #: ``apply-task-batch-N`` — see ``utils.write_phase_bridge``). Only the
    #: decomposer's own ids look like ``T###``.
    _IMPLEMENT_TASK_ID_PATTERN = re.compile(r"^T[0-9]{3}$")

    def implementation_task_statuses(self) -> Dict[str, str]:
        """Task statuses that belong to the implement phase's own task graph.

        A caller reporting implement's progress (``check_workflow_prerequisites``,
        or anything else) must not count another phase's write-batch ids as
        implement tasks — see :attr:`_IMPLEMENT_TASK_ID_PATTERN`.
        """
        return {
            task_id: status
            for task_id, status in self.state.get("task_status", {}).items()
            if self._IMPLEMENT_TASK_ID_PATTERN.match(task_id)
        }

    def record_task_titles(
        self, titles: Dict[str, str], *, human_ids: Optional[Iterable[str]] = None,
        depends_on: Optional[Dict[str, Iterable[str]]] = None,
    ) -> bool:
        """Remember each implement task's title by id, under ``task_titles``.

        ``implement`` records them when it decomposes the task list, on both
        legs, so a deferred task can be named later by what it is and not only
        by its id. *titles* is that whole decomposition:
        the titles merge, but its id set REPLACES ``implement_task_ids``, which
        is what :meth:`deferred_implementation_tasks` scopes to — nothing
        resets ``task_status`` on a fresh implement, so an id an earlier
        decomposition skipped stays ``skipped`` after tasks.md is regenerated
        (adversarial review, 2026-10-05). *human_ids*, when given, are that
        decomposition's manual tasks and REPLACE ``implement_human_task_ids``
        the same way — the key is absent when there are none, so a plan with
        no manual task gains no key (the backstop in
        :meth:`deferred_implementation_tasks`). *depends_on*, when given, is
        that decomposition's graph (every task's ``depends_on``, each list
        stored sorted and de-duplicated) and REPLACES
        :data:`IMPLEMENT_TASK_GRAPH_KEY`. Returns whether
        anything changed; the caller saves.
        """
        recorded = dict(self.state.get("task_titles") or {})
        merged = {**recorded, **{str(k): str(v) for k, v in titles.items() if k}}
        current = sorted(str(k) for k in titles if k)
        human = (
            None if human_ids is None
            else sorted(str(k) for k in human_ids if k) or None
        )
        human_changed = (
            human_ids is not None
            and self.state.get("implement_human_task_ids") != human
        )
        # Each list sorted and de-duplicated, so the record
        # does not depend on the order tasks.md lists a task's dependencies.
        graph = (
            None if depends_on is None
            else {
                str(task_id): sorted({str(dep) for dep in (deps or []) if dep})
                for task_id, deps in sorted(depends_on.items()) if task_id
            }
        )
        graph_changed = (
            graph is not None
            and self.state.get(IMPLEMENT_TASK_GRAPH_KEY) != graph
        )
        if (
            merged == recorded
            and self.state.get("implement_task_ids") == current
            and not human_changed
            and not graph_changed
        ):
            return False
        self.state["task_titles"] = merged
        self.state["implement_task_ids"] = current
        if human is not None:
            self.state["implement_human_task_ids"] = human
        elif human_ids is not None:
            self.state.pop("implement_human_task_ids", None)
        if graph is not None:
            self.state[IMPLEMENT_TASK_GRAPH_KEY] = graph
        self._touch("decomposition")
        return True

    #: The recorded reasons of a task the USER declined (a pause-and-ask
    #: "Skip", a ``--human-task <id>=skip`` answer): a decision, not a
    #: deferral, so the task is not owed as manual work, and neither is a
    #: dependent skipped with it (``task_ledger.is_declined_reason``).
    _USER_DECLINED_REASON = _task_ledger.USER_DECLINED_REASON
    _ANSWERED_SKIP_PREFIX = _task_ledger.ANSWERED_SKIP_PREFIX

    #: The recorded reason of a dependent the transitive skip walk took with
    #: its parent (both legs spell it ``skipped — depends on skipped task
    #: {parent_id} ({parent_title})``); owed exactly when the parent is.
    _DEPENDS_ON_SKIPPED = re.compile(r"^skipped — depends on skipped task (T[0-9]{3})\b")

    def _skip_parent(self, task_id: str) -> Optional[str]:
        """The skipped task *task_id*'s recorded skip reason names
        (:attr:`_DEPENDS_ON_SKIPPED`), or ``None``: one link of the skip
        chain ``task_ledger`` walks."""
        reasons = self.state.get("task_status_reasons") or {}
        match = self._DEPENDS_ON_SKIPPED.match(str(reasons.get(task_id) or ""))
        return match.group(1) if match else None

    def _deferred_to_user(self, task_id: str) -> bool:
        """Whether *task_id*'s skip leaves the task for the user to do.

        A deferral (a human task under a skip strategy, ``deferred — …``) and
        a dependent of one are owed; a pause-and-ask "Skip", a failed code
        task answered ``--human-task <id>=skip``, and a dependent of either
        are not (``task_ledger.chain_declined``). A reason this does not
        recognise — none recorded, a state written before reasons were —
        stays owed, as every skip used to be.
        """
        reasons = self.state.get("task_status_reasons") or {}
        return not _task_ledger.chain_declined(
            task_id, self._skip_parent, lambda current: reasons.get(current))

    def deferral_root(self, task_id: str) -> Optional[str]:
        """The task a dependent skipped with a deferral waits on: the end of
        its ``skipped — depends on skipped task …`` chain (the manual task),
        or ``None`` when *task_id* was not skipped as a dependent.

        Such a task is a code task (or a check) the run did not
        do, not manual work. It runs on the resume that records its manual
        task done (``--human-task <id>=done``), so every surface names it
        apart: ``waits_on`` on its :meth:`deferred_implementation_tasks`
        entry, "skipped (depends on manual T005)" on ``status``.
        """
        return _task_ledger.skip_chain_root(task_id, self._skip_parent)

    def deferred_implementation_tasks(self) -> List[Dict[str, Optional[str]]]:
        """The implement tasks the run left for the user, as ``{id, title}``, by id.

        Read from ``task_status`` (both legs record a deferred human task, and
        a dependent ``skip-dependents`` skipped with it, as ``skipped``), never
        by re-parsing tasks.md: what the run deferred is what state says it
        deferred. Scoped to the decomposition ``implement`` recorded last
        (``implement_task_ids``, when there is one) and to the skips that are
        deferrals (:meth:`_deferred_to_user`), since 2026-10-05: an earlier
        cycle's skip and a task the user declined are not owed. ``title`` is
        ``None`` when ``task_titles`` has no entry (a state written before
        titles were recorded). A task skipped because it depends on a
        deferral also carries ``waits_on``, the deferred task it waits on
        (:meth:`deferral_root`): implement runs it once that
        one is recorded done.
        """
        titles = self.state.get("task_titles") or {}
        current = self.state.get("implement_task_ids")
        scope = set(current) if isinstance(current, list) else None
        statuses = self.implementation_task_statuses()
        owed = {
            task_id for task_id, status in statuses.items()
            if status == "skipped" and self._deferred_to_user(task_id)
        }
        # The backstop: implement is on record as completed and
        # a manual task of its decomposition has no answer at all — neither
        # `completed` (done) nor a recorded skip. Nobody did it, so it is
        # owed: a host that resolved the strategy itself and recorded nothing
        # must never turn a deferred task into a clean `[WORKFLOW_COMPLETE]`.
        if self.is_phase_completed("implement"):
            for task_id in self.state.get("implement_human_task_ids") or []:
                if statuses.get(task_id) not in ("completed", "skipped"):
                    owed.add(str(task_id))
        out: List[Dict[str, Optional[str]]] = []
        for task_id in sorted(owed):
            if scope is not None and task_id not in scope:
                continue
            entry: Dict[str, Optional[str]] = {
                "id": task_id, "title": titles.get(task_id) or None,
            }
            root = self.deferral_root(task_id)
            if root is not None and root != task_id:
                entry["waits_on"] = root
            out.append(entry)
        return out

    def manual_tasks_to_close(self, deferred: Sequence[Dict[str, Any]]) -> List[str]:
        """The ids of *deferred* (:meth:`deferred_implementation_tasks`) that a
        ``--human-task <id>=done`` closes: the manual tasks themselves.

        The how-to-close note answered every deferred id, so a
        code task ``skip-dependents`` skipped with a manual task got
        ``--human-task <id>=done`` too, which implement refuses (a code task is
        answerable only once it failed); it runs on that same resume once its
        manual task is done. A state with no ``implement_human_task_ids`` (one
        written) keeps every id, as before.
        """
        ids = [str(entry.get("id")) for entry in deferred
               if isinstance(entry, dict) and entry.get("id")]
        human = self.state.get("implement_human_task_ids")
        if not isinstance(human, list):
            return ids
        manual = {str(task_id) for task_id in human}
        # Only the ones the user
        # can do now. T008 and T009 depend on code nothing had run yet, and
        # the command recorded them done beside T010.
        gates = self.manual_task_gates(deferred)
        closable = set(gates["closable"]) if gates is not None else manual
        return [task_id for task_id in ids if task_id in manual and task_id in closable]

    def manual_task_gates(
        self, deferred: Optional[Sequence[Dict[str, Any]]] = None,
    ) -> Optional[Dict[str, Any]]:
        """:func:`manual_task_gates` over this state's record of implement's
        decomposition (``IMPLEMENT_TASK_GRAPH_KEY``), or ``None`` for a state
        written before that graph or the manual task ids were recorded.

        *deferred* is :meth:`deferred_implementation_tasks` when the caller
        already has it. Done is a task on record ``completed``; owed, a manual
        task of *deferred*; dropped, a task skipped that is not owed (the
        user's own skip and the tasks skipped with it)."""
        graph = self.state.get(IMPLEMENT_TASK_GRAPH_KEY)
        human = self.state.get("implement_human_task_ids")
        if not isinstance(graph, dict) or not isinstance(human, list):
            return None
        if deferred is None:
            deferred = self.deferred_implementation_tasks()
        statuses = self.implementation_task_statuses()
        current = self.state.get("implement_task_ids")
        scope = set(current) if isinstance(current, list) else set(graph)
        manual = {str(task_id) for task_id in human}
        owed = [
            str(entry.get("id")) for entry in deferred
            if isinstance(entry, dict) and str(entry.get("id")) in manual
        ]
        return manual_task_gates(
            {task_id: deps for task_id, deps in graph.items() if task_id in scope},
            human_ids=manual,
            done=[task_id for task_id, status in statuses.items() if status == "completed"],
            owed=owed,
            dropped=[
                task_id for task_id, status in statuses.items()
                if status == "skipped" and not self._deferred_to_user(task_id)
            ],
        )

    def implementation_check_findings(self) -> List[Dict[str, Any]]:
        """The implement check tasks whose check reported problems, by id.

        ``[{id, title, findings}]`` from :data:`TASK_CHECK_FINDINGS_KEY`, for
        tasks recorded ``completed`` (a check with findings is a completed
        task; a later failure or re-run clears its entry) or ``skipped`` (the
        user answered ``--human-task <id>=skip`` to a check with findings: the
        problems are still in the code) and scoped to the
        decomposition implement ran last, as
        :meth:`deferred_implementation_tasks` is.
        """
        recorded = self.state.get(TASK_CHECK_FINDINGS_KEY)
        if not isinstance(recorded, dict) or not recorded:
            return []
        titles = self.state.get("task_titles") or {}
        current = self.state.get("implement_task_ids")
        scope = set(current) if isinstance(current, list) else None
        statuses = self.implementation_task_statuses()
        out: List[Dict[str, Any]] = []
        for task_id in sorted(recorded):
            findings = recorded.get(task_id)
            if not isinstance(findings, list) or not findings:
                continue
            if statuses.get(task_id) not in ("completed", "skipped"):
                continue
            if scope is not None and task_id not in scope:
                continue
            out.append({
                "id": task_id,
                "title": titles.get(task_id) or None,
                "findings": [str(item) for item in findings],
            })
        return out

    def implementation_batch_check_findings(self) -> List[Dict[str, Any]]:
        """The implement tasks whose own check failed after their edits.

        ``[{id, title, findings}]`` from :data:`TASK_BATCH_CHECK_KEY`, for
        tasks recorded ``completed`` (a later record of the task clears its
        entry) and scoped to the decomposition implement ran last, as
        :meth:`implementation_check_findings` is.
        """
        recorded = self.state.get(TASK_BATCH_CHECK_KEY)
        if not isinstance(recorded, dict) or not recorded:
            return []
        titles = self.state.get("task_titles") or {}
        current = self.state.get("implement_task_ids")
        scope = set(current) if isinstance(current, list) else None
        statuses = self.implementation_task_statuses()
        out: List[Dict[str, Any]] = []
        for task_id in sorted(recorded):
            findings = recorded.get(task_id)
            if not isinstance(findings, list) or not findings:
                continue
            if statuses.get(task_id) != "completed":
                continue
            if scope is not None and task_id not in scope:
                continue
            out.append({
                "id": task_id,
                "title": titles.get(task_id) or None,
                "findings": [str(item) for item in findings],
            })
        return out

    def implementation_batch_check_accepted(self) -> List[Dict[str, Any]]:
        """The implement tasks whose own check reported again only what the
        user accepted for a check.

        ``[{id, title, checks: {check_id: findings}}]`` from
        :data:`TASK_BATCH_CHECK_ACCEPTED_KEY`, for tasks recorded
        ``completed`` and scoped to the decomposition implement ran last, as
        :meth:`implementation_batch_check_findings` is.
        """
        return self._implementation_batch_check_by_check(TASK_BATCH_CHECK_ACCEPTED_KEY)

    def implementation_batch_check_repeats(self) -> List[Dict[str, Any]]:
        """The implement tasks whose own check reported only what a check
        task of the run reported: ``[{id, title, checks:
        {check_id: findings}}]`` from :data:`TASK_BATCH_CHECK_REPEATS_KEY`,
        by :meth:`implementation_batch_check_accepted`'s rule."""
        return self._implementation_batch_check_by_check(TASK_BATCH_CHECK_REPEATS_KEY)

    def _implementation_batch_check_by_check(self, key: str) -> List[Dict[str, Any]]:
        """``[{id, title, checks}]`` from a ``{task: {check: findings}}`` map
        of state.json, for tasks recorded ``completed`` and scoped to the
        decomposition implement ran last."""
        recorded = self.state.get(key)
        if not isinstance(recorded, dict) or not recorded:
            return []
        titles = self.state.get("task_titles") or {}
        current = self.state.get("implement_task_ids")
        scope = set(current) if isinstance(current, list) else None
        statuses = self.implementation_task_statuses()
        out: List[Dict[str, Any]] = []
        for task_id in sorted(recorded):
            checks = recorded.get(task_id)
            if not isinstance(checks, dict):
                continue
            kept = {
                str(check_id): [str(item) for item in findings]
                for check_id, findings in sorted(checks.items())
                if isinstance(findings, list) and findings
            }
            if not kept or statuses.get(task_id) != "completed":
                continue
            if scope is not None and task_id not in scope:
                continue
            out.append({
                "id": task_id,
                "title": titles.get(task_id) or None,
                "checks": kept,
            })
        return out

    def track_file(self, path: str, action: str, task_id: str) -> None:
        """
        Track a file modification.

        Args:
            path: File path
            action: Action performed (created, modified, deleted)
            task_id: ID of the task that modified this file
        """
        if "tracked_files" not in self.state:
            self.state["tracked_files"] = []
        self._touch("tracked", path)

        # Check if file already tracked
        for entry in self.state["tracked_files"]:
            if entry["path"] == path:
                entry["action"] = action
                entry["task_id"] = task_id
                return

        self.state["tracked_files"].append({
            "path": path,
            "action": action,
            "task_id": task_id,
        })

    def get_tracked_files(self) -> List[Dict[str, Any]]:
        """Get list of tracked files."""
        return self.state.get("tracked_files", [])

    def get_files_by_task(self, task_id: str) -> List[str]:
        """Get files modified by a specific task."""
        return [
            entry["path"]
            for entry in self.state.get("tracked_files", [])
            if entry.get("task_id") == task_id
        ]

    def mark_review_phase_completed(self) -> None:
        """Mark the plan review phase as completed."""
        self.state["review_phase_completed"] = True
        self._touch("key", "review_phase_completed")

    def is_review_phase_completed(self) -> bool:
        """Check if the plan review phase is completed."""
        return self.state.get("review_phase_completed", False)

    # --- Phase Completion Tracking ---

    def mark_phase_completed(self, phase: str) -> None:
        """
        Mark a workflow phase as completed.

        Args:
            phase: Phase name (review-plan, apply-suggestions, generate-tasks,
                   implement, review-code, apply-code-fixes)
        """
        mark_phase_completed_in_state(self.state, phase)
        self._touch("phase", phase)
        # `review_phase_completed` predates this general map and nothing ever
        # set it (F11): a fully completed review-plan phase left it `False`
        # forever, contradicting `phases_completed["review-plan"]` in the same
        # file. `mark_review_phase_completed()`'s own docstring is "the *plan*
        # review phase", so this is the one phase name that flips it.
        if phase == "review-plan":
            self.mark_review_phase_completed()

    def mark_phase_started(self, phase: str) -> None:
        """Record *phase* handed to an invoker and not yet finished.

        See :func:`mark_phase_started_in_state`. The write phases' native
        emit path calls this where it used to call (or not call)
        :meth:`mark_phase_completed`; the executor leg never does, because
        ``WriteBatchScheduler._finalize`` completes the phase in the same
        process.
        """
        mark_phase_started_in_state(self.state, phase)
        self._touch("phase", phase)

    def is_phase_started(self, phase: str) -> bool:
        """Whether *phase*'s newest record is a start, not a completion.

        A started record beside no completion is a start. Beside one, the
        stamps decide: a start newer than the completion is a re-run of a
        phase that finished once before (a second review cycle, an implement
        repeated), and the phase is mid-loop again; a start older than the
        completion is the run that completion closed, and is ignored. A
        stamp that does not parse keeps the completion (absence of a date
        is not a re-run).
        """
        started_at = _parse_completion_time(self.phase_started_at(phase))
        if started_at is None:
            return False
        completed_at = self.state.get("phases_completed", {}).get(phase)
        if completed_at is None:
            return True
        completed = _parse_completion_time(completed_at)
        return completed is not None and started_at > completed

    def phase_started_at(self, phase: str) -> Optional[str]:
        """The ISO timestamp *phase* was recorded started, or None."""
        started = self.state.get("phases_started")
        if not isinstance(started, dict):
            return None
        value = started.get(phase)
        return value if isinstance(value, str) else None

    def phase_completion_is_stale(self, phase: str) -> bool:
        """Whether *phase*'s recorded completion predates implement's.

        Only the two phases that judge implement's output are ever stale
        (:data:`PHASES_STALED_BY_IMPLEMENT`), and only when both timestamps
        parse: a missing or unreadable date keeps the completion, since the
        absence of a date is not staleness (the rule
        ``check_workflow_prerequisites._apply_batches_predate_review`` applies
        to apply batches after a review re-run).
        """
        if phase not in PHASES_STALED_BY_IMPLEMENT:
            return False
        completed = self.state.get("phases_completed", {})
        recorded = _parse_completion_time(completed.get(phase))
        implemented = _parse_completion_time(completed.get("implement"))
        if recorded is None or implemented is None:
            return False
        return recorded < implemented

    def is_phase_completed(self, phase: str) -> bool:
        """
        Check if a workflow phase is completed.

        A ``code-review`` or ``apply-code-fixes`` completion recorded before
        implement's latest completion is not one (see
        :meth:`phase_completion_is_stale`), and neither is a completion older
        than the phase's own started record (see :meth:`is_phase_started`):
        the raw record stays in ``phases_completed``, but every reader — the
        next-step builder, the completed-phase guard, ``status`` — sees the
        phase as pending (or ``in_progress``) again.

        Args:
            phase: Phase name to check

        Returns:
            True if the phase has been marked as completed
        """
        if phase not in self.state.get("phases_completed", {}):
            return False
        if self.is_phase_started(phase):
            # A start newer than the completion: the phase is running again
            # (its re-run's emit), and its old completion is not its state.
            return False
        return not self.phase_completion_is_stale(phase)

    def mark_phase_skipped(self, phase: str, reason: str) -> None:
        """
        Mark a workflow phase as explicitly skipped.

        Args:
            phase: Phase name (e.g., apply-suggestions)
            reason: Reason for skipping (e.g., "User chose to skip")
        """
        if "phases_skipped" not in self.state:
            self.state["phases_skipped"] = {}
        self.state["phases_skipped"][phase] = {
            "skipped_at": datetime.now().isoformat(),
            "reason": reason
        }
        # An explicit skip ends a run the host abandoned: a started record
        # left beside it would keep offering `--resume` for a phase the user
        # chose not to finish.
        _pop_phase_started(self.state, phase)
        self._touch("phase", phase)

    def reopen_phase(self, phase: str) -> bool:
        """Drop *phase*'s completion, so the phase reads as owing work again
        (``--force``, a review round handed out for validation again).

        Journaled as a write of the phase's record: the next :meth:`save`
        keeps the phase as this manager has it, so a completion another
        writer recorded after this manager loaded is dropped too, while
        every other phase's record is the file's. Returns whether this
        manager's view had a completion to drop; the caller saves.
        """
        completed = self.state.get("phases_completed")
        removed = isinstance(completed, dict) and completed.pop(phase, None) is not None
        self._touch("phase", phase)
        return removed

    def is_phase_skipped(self, phase: str) -> bool:
        """
        Check if a workflow phase was explicitly skipped.

        Args:
            phase: Phase name to check

        Returns:
            True if the phase has been marked as skipped
        """
        return phase in self.state.get("phases_skipped", {})

    def get_phase_skip_reason(self, phase: str) -> Optional[str]:
        """
        Get the reason a phase was skipped.

        Args:
            phase: Phase name

        Returns:
            Reason string if phase was skipped, None otherwise
        """
        skip_info = self.state.get("phases_skipped", {}).get(phase)
        return skip_info.get("reason") if skip_info else None

    def completion_predates(self, apply: str, review: str) -> bool:
        """Whether every record of phase *apply* predates *review*'s completion.

        Both are phase words (``state.json``'s keys: ``code-review``, never
        the mode word ``review-code``). The apply's records are its
        ``phases_completed`` stamp and its skip's ``skipped_at``; the NEWER of
        the two is compared, strictly, with ``phases_completed[review]``. Not
        the precedence ``full``'s ``_recorded`` reads (completed wins): both
        records can be on file at once (:meth:`mark_phase_completed` leaves
        an older skip in place), and an earlier cycle's completion must not
        hide a skip written after this review. True means the review ran
        again after the apply last finished, so its findings are not applied
        yet.

        Every stamp goes through :func:`_parse_completion_time`, the one
        reading of a stamp, so a stamp with a UTC offset and a naive local
        one compare as instants.

        False whenever a date does not parse (an unparseable review stamp, a
        completion that is not a string, a skip that is not a dict or has no
        parseable ``skipped_at``): absence of a date is not staleness, the
        rule :meth:`phase_completion_is_stale` follows, so the apply stays
        done. An apply stamp equal to the review's keeps it done too. False
        as well when *apply* has neither record: nothing on file predates
        anything, and "never recorded" is the caller's own case (the apply
        has not run), not this one.
        """
        completed = self.state.get("phases_completed")
        completed = completed if isinstance(completed, dict) else {}
        reviewed_at = _parse_completion_time(completed.get(review))
        if reviewed_at is None:
            return False
        stamps: List[datetime] = []
        if apply in completed:
            stamp = _parse_completion_time(completed[apply])
            if stamp is None:
                return False
            stamps.append(stamp)
        skipped = self.state.get("phases_skipped")
        if isinstance(skipped, dict) and apply in skipped:
            record = skipped[apply]
            stamp = (
                _parse_completion_time(record.get("skipped_at"))
                if isinstance(record, dict) else None
            )
            if stamp is None:
                return False
            stamps.append(stamp)
        return bool(stamps) and predates_review(max(stamps), reviewed_at)

    def has_plan_changed(self) -> bool:
        """Check if plan has changed since last run."""
        return self.state.get("plan_changed", False)

    def clear_plan_changed_flag(self) -> None:
        """Clear the plan changed flag (the flag consumed).

        Journaled with ``plan_hash`` as one unit: the save writes this
        manager's hash beside the cleared flag, so a newer edit another
        writer detected meanwhile is found again by the next load rather
        than recorded as consumed.
        """
        self.state.pop("plan_changed", None)
        self._touch("plan")

    def refresh_plan_hash(self) -> None:
        """Re-stamp ``plan_hash`` to the plan's current on-disk content.

        `_load_or_create` hashes the plan once, at construction — before an
        apply-suggestions/apply-task-suggestions/apply-code-fixes/implement run
        makes its own edits. Without this, a run's `save()` persists that stale
        hash, and the *next* `StateManager` built on this plan sees its own
        edit as a human editing the plan mid-workflow (F5, audited 2026-09-16):
        `plan_changed` goes `True` and `implement_orchestrator.py` prints
        "Plan has changed since last session" for a change the plugin made.
        Call this once, after the run's writes are done, so the stamped hash
        matches what is actually on disk and `plan_changed` has nothing left
        to report.
        """
        self.state["plan_hash"] = self._compute_plan_hash()
        self.clear_plan_changed_flag()

    def record_commit_range(
        self, fields: Mapping[str, Any], *, refresh_plan_hash: bool = False,
        clear_phases: Sequence[str] = (),
    ) -> None:
        """Replace only the given ``commit_range`` fields, and save.

        The one writer of a commit front door's record: step 6 of ``--review-commits``,
        ``--apply-commit-fixes``, ``--improve-commits`` and ``util
        commit-brief``, and a detached worker applying its launch's stage. A new
        brief passes every field; an existing one passes what this entry
        decided (a fresh ``resolved_at`` always, a rewritten header's
        identity fields), so ``phrase``, ``window``, ``reviewed_header_sha256``
        and ``guard``, which no front door passes, keep their recorded values.

        Loaded fresh from disk, updated and saved under ``state_file_lock``,
        so a concurrent locked writer of the same file (``util batch-done``,
        ``util metrics``) neither loses its record nor drops this one. That
        replaces this instance's in-memory state with the file's. With no file
        yet, the ordinary initial state is built (``plan_hash``,
        ``head_at_start``, ``branch_name``, …); an unparseable or non-object
        file is replaced by one, which then carries the record.
        *refresh_plan_hash* re-stamps ``plan_hash`` in the same save, for a
        header the plugin rewrote (never a human ``plan_changed``).
        *clear_phases* are popped from ``phases_completed`` in the same save:
        a restart's archived round (``["code-review"]``) stops reading as a
        completed review the moment it is recorded, whether or not the
        restarted phase ever runs.
        """
        if self.read_only:
            raise RuntimeError(
                f"read-only StateManager for {self.plan_path} cannot record commit_range"
            )
        # Imported here to keep full_workflow_orchestrator, which loads this module, light.
        from .metrics import state_file_lock

        # The lock lives beside the file; a folder that does not exist yet has
        # nothing to lock, so it is made first.
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with state_file_lock(self.state_file):
            loaded: Any = None
            read_text: Optional[str] = None
            if self.state_file.exists():
                try:
                    loaded, read_text = self._read_upgraded_text()
                except (OSError, ValueError):
                    loaded = None
            if isinstance(loaded, dict):
                self._remember_baseline(read_text)
            else:
                loaded = self._create_initial_state()
                self._remember_baseline(None)
            self.state = loaded
            self._touched = set()
            record = self.state.get("commit_range")
            merged: Dict[str, Any] = dict(record) if isinstance(record, Mapping) else {}
            merged.update(json.loads(json.dumps(dict(fields))))
            if fields or isinstance(record, Mapping):
                # A clear-only call (no fields) never invents an empty record.
                self.state["commit_range"] = merged
            phases = self.state.get("phases_completed")
            if clear_phases and isinstance(phases, dict):
                for phase in clear_phases:
                    phases.pop(phase, None)
            if refresh_plan_hash:
                self.refresh_plan_hash()
            self.save()

    def get_session_summary(self) -> Dict[str, Any]:
        """Get a summary of the current session state."""
        task_statuses = self.state.get("task_status", {})
        status_counts = {}
        for status in task_statuses.values():
            status_counts[status] = status_counts.get(status, 0) + 1

        return {
            "plan_path": self.state.get("plan_path"),
            "created_at": self.state.get("created_at"),
            "updated_at": self.state.get("updated_at"),
            "branch": self.state.get("branch_name"),
            "review_phase_completed": self.state.get("review_phase_completed", False),
            "total_tasks": len(task_statuses),
            "status_counts": status_counts,
            "files_tracked": len(self.state.get("tracked_files", [])),
        }

    def reset(self) -> None:
        """Reset state to initial values (preserves plan reference).

        An explicit reset of the whole document, stamped
        :data:`DOCUMENT_RESET` in :data:`STATE_RESETS_KEY`: the next
        :meth:`save` writes this manager's document whole, so a record
        another writer made meanwhile does not survive it, and a writer that
        loaded the file before it takes the reset document (its own changes
        included: they predate the reset) rather than bringing anything back.
        """
        self.state = self._create_initial_state()
        self.state[STATE_RESETS_KEY] = {DOCUMENT_RESET: datetime.now().isoformat()}
        self._touched = set()

    def delete(self) -> None:
        """Delete the state file, under the state lock and through its folder
        held below the plan's directory (``state_file.remove_document``)."""
        with _state_file.locked(self.state_file):
            if self.state_file.exists():
                _state_file.remove_document(self.state_file)
        self._remember_baseline(None)

    # --- Human Task Strategy ---

    def save_human_task_strategy(self, strategy: str) -> None:
        """Persist the chosen human task handling strategy.

        Args:
            strategy: One of "pause-and-ask", "skip-continue", "skip-dependents", "cancel"
        """
        self.state["human_task_strategy"] = strategy
        self._touch("key", "human_task_strategy")

    def get_human_task_strategy(self) -> Optional[str]:
        """Get the previously chosen human task handling strategy.

        Returns:
            Strategy string if set, None otherwise (user should be re-prompted)
        """
        return self.state.get("human_task_strategy")

    def record_human_task_answers(self, answers: Mapping[str, str]) -> None:
        """Record the user's ``--human-task`` answers (``{task_id: action}``)
        over the answers already recorded.

        Each answered task's record is journaled, so an answer that repeats
        the recorded one is still this manager's write: a writer that
        consumed the earlier answer meanwhile does not take the repeated one
        with it. The map is written even when *answers* is empty.
        """
        recorded = self.state.get(HUMAN_TASK_DECISIONS_KEY)
        recorded = dict(recorded) if isinstance(recorded, dict) else {}
        recorded.update({str(task_id): action for task_id, action in answers.items()})
        self.state[HUMAN_TASK_DECISIONS_KEY] = recorded
        for task_id in answers:
            self._touch("task", task_id)

    # --- Dependency Override Tracking ---

    def record_dependency_override(self, task_id: str, overridden_deps: List[str]) -> None:
        """Record that a task's human-task dependencies were overridden.

        Used with "skip-continue" strategy where human task dependencies are
        treated as satisfied even though the human tasks were skipped.

        Args:
            task_id: The task whose dependencies were overridden
            overridden_deps: List of human task IDs that were skipped but treated as satisfied
        """
        if "dependency_overrides" not in self.state:
            self.state["dependency_overrides"] = {}
        self.state["dependency_overrides"][task_id] = {
            "overridden_deps": overridden_deps,
            "timestamp": datetime.now().isoformat(),
        }
        self._touch("task", task_id)

    def get_dependency_overrides(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get dependency override info for a task."""
        return self.state.get("dependency_overrides", {}).get(task_id)

    def get_all_dependency_overrides(self) -> Dict[str, Dict[str, Any]]:
        """Get all dependency overrides."""
        return self.state.get("dependency_overrides", {}).copy()

    # --- Human Decision Tracking ---

    def record_human_decision(
        self,
        phase: str,
        group_id: str,
        decision: str,
        reason: Optional[str] = None,
        batch_context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Record a human decision for a validation item.

        This allows resuming interrupted sessions without re-asking
        the same questions.

        Args:
            phase: Phase identifier (e.g., "apply-suggestions", "apply-fixes")
            group_id: Stable hash-based identifier (from generate_group_id())
            decision: Decision made ("approved", "skipped", "deferred")
            reason: Optional reason for the decision
            batch_context: Optional batch context for batch decisions
        """
        key = f"human_decisions_{phase}"
        if key not in self.state:
            self.state[key] = {}

        decision_record = {
            "decision": decision,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        }
        if batch_context:
            decision_record["batch_context"] = batch_context

        self.state[key][group_id] = decision_record
        self._touch("entry", key, group_id)

    def get_human_decision(self, phase: str, group_id: str) -> Optional[Dict[str, Any]]:
        """Get previously recorded human decision for an item."""
        key = f"human_decisions_{phase}"
        decisions = self.state.get(key, {})
        return decisions.get(group_id)

    def get_all_human_decisions(self, phase: str) -> Dict[str, Dict[str, Any]]:
        """Get all recorded human decisions for a phase."""
        key = f"human_decisions_{phase}"
        return self.state.get(key, {}).copy()

    def record_judge_verdicts(
        self, phase: str, verdicts: Mapping[str, Mapping[str, Any]],
        unresolved: Sequence[str] = (),
    ) -> None:
        """Store the judge's raw verdicts (``{group_id: verdict}``) in
        ``human_decision_verdicts_<phase>``, and the groups it left
        unresolved, when any, in ``human_decision_unresolved_<phase>``.

        Each verdict is journaled as its group's entry and the unresolved
        list as one value, so a verdict that repeats the stored one is still
        this manager's write.
        """
        key = f"{_VERDICTS_PREFIX}{phase}"
        stored = self.state.get(key)
        if not isinstance(stored, dict):
            stored = self.state[key] = {}
        for group_id, verdict in verdicts.items():
            stored[group_id] = dict(verdict)
            self._touch("entry", key, group_id)
        if unresolved:
            unresolved_key = f"human_decision_unresolved_{phase}"
            self.state[unresolved_key] = list(unresolved)
            self._touch("key", unresolved_key)

    def clear_human_decisions(self, phase: str) -> None:
        """Clear all human decisions for a phase (for fresh start); an
        explicit reset (:meth:`clear_key`)."""
        self.clear_key(f"human_decisions_{phase}")

    # --- Processing Progress Tracking ---

    def record_processing_progress(
        self,
        phase: str,
        total_items: int,
        processed_items: int,
        current_batch: int,
        total_batches: int
    ) -> None:
        """
        Record processing progress for resume capability.

        Args:
            phase: Phase identifier (e.g., "apply-suggestions", "apply-fixes")
            total_items: Total number of items to process
            processed_items: Number of items processed so far
            current_batch: Current batch number (0-indexed)
            total_batches: Total number of batches
        """
        key = f"progress_{phase}"
        self.state[key] = {
            "total_items": total_items,
            "processed_items": processed_items,
            "current_batch": current_batch,
            "total_batches": total_batches,
            "last_updated": datetime.now().isoformat()
        }
        self._touch("key", key)

    def get_processing_progress(self, phase: str) -> Optional[Dict[str, Any]]:
        """Get processing progress for resume."""
        key = f"progress_{phase}"
        return self.state.get(key)

    # --- Processed Item Tracking ---

    def mark_item_processed(
        self,
        phase: str,
        group_id: str,
        status: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Mark an individual item as processed.

        Args:
            phase: Phase identifier (e.g., "apply-suggestions", "apply-fixes")
            group_id: Stable hash-based identifier (from generate_group_id())
            status: Processing status ("applied", "skipped", "failed")
            details: Optional details about the processing
        """
        mark_item_processed_in_state(self.state, phase, group_id, status, details)
        self._touch("entry", f"processed_{phase}", group_id)

    def get_processed_items(self, phase: str) -> Dict[str, Dict[str, Any]]:
        """Get all processed items for a phase."""
        key = f"processed_{phase}"
        return self.state.get(key, {}).copy()

    def is_item_processed(self, phase: str, group_id: str) -> bool:
        """Check if an item has already been processed."""
        key = f"processed_{phase}"
        return group_id in self.state.get(key, {})

    def clear_processed_items(self, phase: str) -> None:
        """Clear all processed items for a phase (for fresh start); an
        explicit reset (:meth:`clear_key`)."""
        self.clear_key(f"processed_{phase}")

    def clear_processing_progress(self, phase: str) -> None:
        """Clear processing progress for a phase; an explicit reset
        (:meth:`clear_key`)."""
        self.clear_key(f"progress_{phase}")

    def clear_key(self, key: str) -> None:
        """Drop top-level *key* as an explicit reset (``--fresh``).

        Stamped in :data:`STATE_RESETS_KEY`, so :meth:`save` keeps the key as
        this manager has it: whatever another writer added to it meanwhile is
        dropped with the rest, and a writer that loaded the file before the
        reset cannot bring any of it back with its own save.
        """
        self.state.pop(key, None)
        stamps = self.state.get(STATE_RESETS_KEY)
        stamps = dict(stamps) if isinstance(stamps, dict) else {}
        stamps[key] = datetime.now().isoformat()
        self.state[STATE_RESETS_KEY] = stamps


def get_or_create_state(plan_path: Path, state_dir: Optional[Path] = None) -> StateManager:
    """
    Convenience function to get or create state for a plan.

    Args:
        plan_path: Path to the plan file
        state_dir: Deprecated, ignored. State now stored in plan directory.

    Returns:
        StateManager instance
    """
    return StateManager(plan_path)


def list_active_sessions(plans_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    List all active implementation sessions.

    Args:
        plans_dir: Directory containing plan files (searches for state.json in subdirs)

    Returns:
        List of session summaries with plan_path, status, and metadata
    """
    if plans_dir is None:
        plans_dir = Path('plans')

    sessions = []

    if not plans_dir.exists():
        return sessions

    # Search for state.json files in plan directories
    # e.g., plans/*/state.json
    for state_file in plans_dir.glob('*/state.json'):
        try:
            with open(state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
            sessions.append({
                'plan_path': state_file.parent.parent / f"{state_file.parent.name}.md",
                'state_file': state_file,
                'status': state.get('status', 'unknown'),
                'current_phase': state.get('current_phase'),
                'last_updated': state.get('updated_at'),
                'branch': state.get('branch_name'),
                'task_count': len(state.get('task_status', {})),
            })
        except (json.JSONDecodeError, OSError) as e:
            # Skip malformed or inaccessible state files
            logger.warning(f"Could not read state file {state_file}: {e}")
            continue

    return sorted(sessions, key=lambda s: s.get("last_updated", ""), reverse=True)
