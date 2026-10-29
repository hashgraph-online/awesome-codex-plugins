"""State manager for persisting implementation state across sessions."""

import hashlib
import json
import logging
import os
import re
import shutil
import tempfile
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from .git_utils import get_branch_name, head_or_empty_tree
from .judge_vocab import upgrade_legacy
from .schema_validator import validate_state_file

logger = logging.getLogger(__name__)

# --- Constants ---
ID_ALGO_VERSION = 1
CURRENT_FORMAT_VERSION = 2

#: The phases that judge implement's output. A completion of one of them that
#: predates implement's latest completion reviewed (or fixed) an earlier
#: state of the code: typically the empty repository a review was run against
#: before implement existed, or code implement has since rewritten
#: (2026-10-02, Codex racing run: a plain `--review-code` was refused as
#: already done, and implement's next step pointed at `--apply-code-fixes` on
#: that stale review).
PHASES_STALED_BY_IMPLEMENT = ("code-review", "apply-code-fixes")


def _parse_completion_time(value) -> Optional[datetime]:
    """A ``phases_completed`` timestamp as a naive local datetime, or None."""
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone().replace(tzinfo=None)
    return parsed


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

    Fix round 18 (run 7 #9): a run that recorded a phase started and then
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

#: Twins of ``write_batch_scheduler.ACCEPTED_REASON_PREFIX`` and
#: ``COMPLETED_MANUAL_REASON``: the reasons a ``done`` answer writes. Restated
#: here so this low-level module imports nothing from the scheduler.
_ACCEPTED_REASON_PREFIX = "accepted — "
_COMPLETED_MANUAL_REASON = "answered --human-task <id>=done"


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

    An answer answers one stop (fix round 15, review of round 14): it is
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
        # it back as an accepted failure (fix round 9).
        state["task_status_reasons"].pop(task_id, None)


#: ``state.json``'s map of what an implement check task found:
#: ``{task_id: [finding, ...]}``, present only while some task has findings.
TASK_CHECK_FINDINGS_KEY = "task_check_findings"

#: ``state.json``'s record of the decomposition implement ran last, as a
#: graph: ``{task_id: [the ids it depends on]}`` for EVERY task of it
#: (:meth:`StateManager.record_task_titles`). A ``--resume`` materializes only
#: the unfinished tasks, so a walk over ``write_tasks.json`` alone lost every
#: edge through a finished one: a check's findings held back T004 but not
#: T006, whose chain to the check ran through a manual task answered done
#: (fix round 12). ``write_batch_scheduler.decomposition_graph`` reads it.
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

    Fix round 28 (live run 12, Codex racing 06): T010, a manual task every
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
    recorded = state.get(TASK_CHECK_FINDINGS_KEY)
    current = dict(recorded) if isinstance(recorded, dict) else {}
    kept = [str(item) for item in (findings or []) if str(item).strip()]
    if kept:
        current[str(task_id)] = kept
    else:
        current.pop(str(task_id), None)
    if current:
        state[TASK_CHECK_FINDINGS_KEY] = current
    else:
        state.pop(TASK_CHECK_FINDINGS_KEY, None)


#: ``state.json``'s map of what the checks an implement task ran on its OWN
#: edits reported when one failed: ``{task_id: [finding, ...]}``, present only
#: while some task's own check fails (fix round 15). Never
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
    the key is dropped when the map empties."""
    recorded = state.get(TASK_BATCH_CHECK_KEY)
    current = dict(recorded) if isinstance(recorded, dict) else {}
    kept = [str(item) for item in (findings or []) if str(item).strip()]
    if kept:
        current[str(task_id)] = kept
    else:
        current.pop(str(task_id), None)
        # Fix round 29: the words kept beside a failing own check go with it.
        set_task_own_text_in_state(state, task_id, None)
    if current:
        state[TASK_BATCH_CHECK_KEY] = current
    else:
        state.pop(TASK_BATCH_CHECK_KEY, None)


#: ``state.json``'s map of what an implement task with a failing own check
#: (:data:`TASK_BATCH_CHECK_KEY`) itself says — its title, ``## Task``
#: section and acceptance criteria (``write_batch_scheduler.task_own_text``)
#: — ``{task_id: text}``, present only while some such task has one (fix
#: round 29, review of round 28, checks #1). A check task that reports the
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
    recorded = state.get(TASK_OWN_TEXT_KEY)
    current = dict(recorded) if isinstance(recorded, dict) else {}
    failing = state.get(TASK_BATCH_CHECK_KEY)
    value = str(text or "").strip()
    if value and isinstance(failing, dict) and failing.get(str(task_id)):
        current[str(task_id)] = value
    else:
        current.pop(str(task_id), None)
    if current:
        state[TASK_OWN_TEXT_KEY] = current
    else:
        state.pop(TASK_OWN_TEXT_KEY, None)


#: ``state.json``'s map of an implement task's own words about the checks it
#: ran on its edits (its reply's ``check.note``): ``{task_id: note}``,
#: present only while some task has one (fix round 28, live run 12: the
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
    recorded = state.get(TASK_OWN_CHECK_NOTE_KEY)
    current = dict(recorded) if isinstance(recorded, dict) else {}
    text = str(note or "").strip()
    if text:
        current[str(task_id)] = text
    else:
        current.pop(str(task_id), None)
    if current:
        state[TASK_OWN_CHECK_NOTE_KEY] = current
    else:
        state.pop(TASK_OWN_CHECK_NOTE_KEY, None)


#: ``state.json``'s list of the implement tasks whose last record carried a
#: report of their OWN checks (passed, failing, or repeating only accepted
#: findings), sorted, present only while some task has one (fix round 24,
#: live run 10: every racing task ran ``npm test`` and passed, and the tests
#: line still said that nothing had run the repository's tests — a passing
#: own check was recorded nowhere). Written by both legs (``util batch-done
#: --own-check``, the scheduler from ``TaskOutcome.batch_check``); every
#: other record of the task clears it; the tests line reads it
#: (``write_batch_scheduler.implement_checks_ran``).
TASK_OWN_CHECK_RAN_KEY = "task_own_check_ran"


def set_task_own_check_ran_in_state(
    state: Dict[str, Any], task_id: str, ran: bool,
) -> None:
    """Record (or clear) that *task_id*'s own check reported; the key is
    dropped when the list empties."""
    recorded = state.get(TASK_OWN_CHECK_RAN_KEY)
    current = {str(t) for t in recorded} if isinstance(recorded, list) else set()
    if ran:
        current.add(str(task_id))
    else:
        current.discard(str(task_id))
    if current:
        state[TASK_OWN_CHECK_RAN_KEY] = sorted(current)
    else:
        state.pop(TASK_OWN_CHECK_RAN_KEY, None)


#: ``state.json``'s map of what an implement task's own check reported again
#: of findings the user accepted for a check (``--human-task <check>=done``),
#: by check: ``{task_id: {check_id: [finding, ...]}}``, present only while
#: some task has one (fix round 23: round 22 kept them only in the result
#: row and the printed line, so ``status`` showed the task as plainly
#: ``completed``). Beside :data:`TASK_BATCH_CHECK_KEY`, never in it: they
#: are not the task's own failure. Written by both legs
#: (``write_batch_scheduler.split_accepted_findings``: the scheduler and
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
#: comparison of ``write_batch_scheduler.split_accepted_findings``), by that
#: check: ``{task_id: {check_id: [finding, ...]}}``, present only while some
#: task has one (fix round 28, live run 12 OpenCode accept 01: T001 ran
#: T002's release check and was recorded as failing it). Beside
#: :data:`TASK_BATCH_CHECK_KEY`, never in it: T002's own record covers the
#: finding. Written by both legs (``write_batch_scheduler.repeated_findings_for``:
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
    recorded = state.get(key)
    current = dict(recorded) if isinstance(recorded, dict) else {}
    kept = {
        str(check_id): [str(item) for item in (findings or []) if str(item).strip()]
        for check_id, findings in sorted((matched or {}).items())
    }
    kept = {check_id: findings for check_id, findings in kept.items() if findings}
    if kept:
        current[str(task_id)] = kept
    else:
        current.pop(str(task_id), None)
    if current:
        state[key] = current
    else:
        state.pop(key, None)


#: ``task id -> tree fingerprint`` for each check with findings on the native
#: leg (fix round 14): the files git saw when the run that recorded the
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
    recorded = state.get(TASK_CHECK_TREES_KEY)
    current = dict(recorded) if isinstance(recorded, dict) else {}
    if fingerprint:
        current[str(task_id)] = str(fingerprint)
    else:
        current.pop(str(task_id), None)
    if current:
        state[TASK_CHECK_TREES_KEY] = current
    else:
        state.pop(TASK_CHECK_TREES_KEY, None)


#: ``task id -> when a run that hands the implement task out again set its
#: earlier record aside`` (fix round 17): a start-over (``--fresh``, or a
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


#: ``details.leg`` of a ``processed_<phase>`` record (fix round 22): which
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

    One shape on both legs (fix round 22, live run 9: the executor leg wrote
    no record at all, so ``state.json`` named a declined fix on Claude Code
    and nowhere on Codex or OpenCode). Each of *task*'s ``expected_ids`` gets
    ``{status, details: {task_id, prior_changes_id, grouped_sha256, leg,
    reason?}, timestamp}``: ``declined`` / ``skipped`` with its reason
    (never ``applied``), else ``applied`` — ``no-op`` for a batch the
    executor read as changing nothing; the native leg has no such reading
    and records a verified no-op ``applied`` (fix round 23: documented, no
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
    offered again (fix round 22) — as the executor leg offers it in the
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
        reproduces every id."""
        discriminator = 0
        candidate = hash_of(discriminator)
        while candidate in all_hashes and all_hashes[candidate][0] == kind:
            discriminator += 1
            if discriminator > 10:
                raise ValueError(
                    f"Cannot resolve hash collision for {kind} {label} "
                    f"after 10 attempts"
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
            "group", f"G{g_num}", lambda d: generate_group_id(group, d)
        )
        all_hashes[ghash] = ("group", g_idx, -1)
        group["group_hash"] = ghash
        group["display_label"] = f"G{g_num}"

        suggestions = group.get("suggestions", group.get("issues", []))
        for s_idx, sugg in enumerate(suggestions):
            s_num = s_idx + 1
            shash = _discriminated(
                "suggestion", f"G{g_num}S{s_num}",
                lambda d: generate_suggestion_id(sugg, d),
            )
            all_hashes[shash] = ("suggestion", g_idx, s_idx)
            sugg["suggestion_hash"] = shash
            sugg["display_label"] = f"G{g_num}S{s_num}"

    # Now compute display hashes (8-char prefix, extended on collision)
    _assign_display_hashes(groups)


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
        from .output_handler import get_output_dir
        self.plan_dir = get_output_dir(self.plan_path)
        self.state_file = self.plan_dir / "state.json"

        self.state: Dict[str, Any] = {}
        if not read_only:
            self._migrate_from_old_location()  # Check for old state file
        self._load_or_create()

    def _migrate_from_old_location(self) -> None:
        """Migrate state file from old hash-based location if it exists.

        Note: Migration is silent unless verbose/debug logging is enabled.
        Uses copy+delete instead of rename for cross-filesystem compatibility.
        """
        old_state_dir = Path(__file__).parent.parent / "state"
        path_hash = hashlib.sha256(str(self.plan_path).encode()).hexdigest()[:16]
        old_state_file = old_state_dir / f"{path_hash}.json"

        if old_state_file.exists() and not self.state_file.exists():
            try:
                # Validate JSON is parseable before migrating
                with open(old_state_file, 'r', encoding='utf-8') as f:
                    json.load(f)

                # Use copy+delete instead of rename (works across filesystems)
                self.plan_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(old_state_file, self.state_file)

                # Verify copy succeeded before deleting old file
                if self.state_file.exists():
                    os.unlink(old_state_file)
                    logger.debug(f"Migrated state file to: {self.state_file}")

            except (json.JSONDecodeError, OSError) as e:
                # Log warning but continue - old state may be corrupt or inaccessible
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
            # and with it every mode on a plain `git init`.
            "head_at_start": head_or_empty_tree(),
            "branch_name": get_branch_name() or "unknown",
            "review_phase_completed": False,
            "tracked_files": [],
            "task_status": {},
            "phases_completed": {},
            "phases_skipped": {},
        }

    def _load_or_create(self) -> None:
        """Load existing state or create new one."""
        if self.state_file.exists():
            try:
                self.state = self._read_upgraded()
                if not isinstance(self.state, dict):
                    # Parsed, but not a state (`[]`, a number): read as an
                    # unparseable one is, rather than failing on `.get`
                    # below (`record_commit_range` documents replacing it).
                    raise json.JSONDecodeError("state.json is not a JSON object", "", 0)

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
        "Decided by the judge agent" section (review 2026-10-02). Not under
        ``read_only``, and never when nothing changed.

        Raises what ``open``/``json.loads`` raise; a failed write-back does not.
        """
        with open(self.state_file, "r", encoding="utf-8") as f:
            text = f.read()
        loaded = upgrade_legacy(json.loads(text))
        if (not self.read_only and isinstance(loaded, dict)
                and loaded != json.loads(text)):
            self._write_back_upgrade(loaded, text)
        return loaded

    def _write_back_upgrade(self, document: Dict[str, Any], read_text: str) -> None:
        """Persist the judge-name upgrade of *read_text*, and only that.

        The document is written as loaded — no ``updated_at`` stamp, no
        plan-change flag — so the write renames keys and values and changes
        nothing else. Skipped when the file no longer holds *read_text*:
        another process saved in between, and its file is the newer one.
        The native writers' shared lock covers both comparison and replacement
        so a completion cannot land between them and then be overwritten.
        """
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
        """
        Save current state to file with atomic writes.

        Uses write-to-temp + atomic rename pattern to prevent corruption
        if the save operation is interrupted.

        Raises:
            IOError: If the save operation fails
            RuntimeError: On a ``read_only`` manager
        """
        if self.read_only:
            raise RuntimeError(
                f"read-only StateManager for {self.plan_path} cannot save"
            )
        self.state["updated_at"] = datetime.now().isoformat()

        # Validate state before saving
        is_valid, errors = self._validate_state(self.state)
        if not is_valid:
            # Log validation errors but allow save to proceed
            import warnings
            warnings.warn(f"State validation warnings: {errors}")

        self._write_atomic(self.state)

    def _write_atomic(self, document: Dict[str, Any]) -> None:
        """Write *document* to ``state.json`` via a temp file and ``os.replace``.

        Raises:
            IOError: If the write fails
        """
        # Write to temp file first, then atomically rename
        temp_fd = None
        temp_path = None
        try:
            # Create a temp file in the same directory as the target
            # Use state_file.parent since state is now plan-local
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            temp_fd, temp_path = tempfile.mkstemp(
                dir=str(self.state_file.parent),
                suffix='.tmp',
                prefix='.state_'
            )

            # Write state to temp file
            with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
                json.dump(document, f, indent=2)
            temp_fd = None  # fdopen closes the file descriptor

            # Atomically rename temp file to target location
            os.replace(temp_path, str(self.state_file))
            temp_path = None  # File has been moved

        except Exception as e:
            # Clean up temp file if something went wrong
            if temp_fd is not None:
                try:
                    os.close(temp_fd)
                except OSError:
                    pass
            if temp_path is not None and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass
            raise IOError(f"Failed to save state: {e}") from e

    def reload(self) -> None:
        """Re-read ``state.json`` from disk, replacing the in-memory dict.

        **Every unsaved in-memory change is discarded** — a caller with pending
        edits must ``save()`` first. This exists for the one legitimate case of
        a second writer: a file-level helper such as ``finalize_tracking.py``
        reads ``state.json``, adds to it and writes it back, while ``save()``
        dumps this object's dict wholesale and never merges. Whoever saves last
        wins, and until 2026-09-16 that was `_finalize`'s closing `save()`,
        which erased the `tracked_files` `finalize_tracking` had just computed —
        an implement run that wrote `index.html` finalized with the two stale
        entries earlier phases had left, and `review-code` would have reviewed
        those (F3). Calling this straight after the external writer makes the
        later `save()` carry its work instead of overwriting it.

        Unlike construction, this does not re-run the plan-change detection:
        `plan_changed` answers "did a human edit the plan since the last
        session", which is a question about the session, not about a re-read
        mid-run (a write phase edits the plan itself).
        """
        if not self.state_file.exists():
            return
        try:
            loaded = self._read_upgraded()
        except (json.JSONDecodeError, OSError):
            # A corrupt or unreadable file is not worth losing the dict we hold:
            # the next `save()` rewrites it wholesale anyway.
            return
        if isinstance(loaded, dict):
            self.state = loaded

    def get(self, key: str, default: Any = None) -> Any:
        """Get a state value."""
        return self.state.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a state value."""
        self.state[key] = value

    # --- Metrics (in-memory; see utils/metrics.py for the file-level CLI) ---

    def start_metrics_phase(self, phase: str, total_batches: int) -> None:
        """Stamp ``metrics_progress.{phase}`` so ETAs have a baseline.

        The in-memory twin of ``metrics.start_phase``. Routing metrics through
        this object rather than through ``metrics.py``'s own reader/writer is
        what stops the two racing on ``state.json`` — see :meth:`reload`.
        """
        from . import metrics as _metrics

        _metrics.start_phase_in_state(self.state, phase, int(total_batches))

    def finish_metrics_phase(
        self, phase: str
    ) -> Optional[Tuple[Optional[int], str]]:
        """The in-memory twin of ``metrics.finish_phase``.

        Returns ``(elapsed_ms, line)`` — the closing ``[ETA] … phase complete``
        line is handed back rather than printed, the way :meth:`record_metric`
        already hands back its own, so the scheduler can route it to the phase
        log the rest of that run's ETA lines went to (F7).
        """
        from . import metrics as _metrics

        if phase not in (self.state.get("metrics_progress") or {}):
            return None
        return _metrics.finish_phase_in_state(self.state, phase)

    def record_metric(self, phase: str, label: str, **kwargs: Any) -> Optional[str]:
        """Append one ``metrics.{phase}`` entry in memory; ``save()`` persists it.

        The in-memory twin of ``metrics.record_metric``; returns the rendered
        ``[ETA]`` line (or None) for the caller to place, and prints nothing.
        """
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
        by its id (2026-10-04: a complete workflow said nothing about the two
        manual tasks it left the user). *titles* is that whole decomposition:
        the titles merge, but its id set REPLACES ``implement_task_ids``, which
        is what :meth:`deferred_implementation_tasks` scopes to — nothing
        resets ``task_status`` on a fresh implement, so an id an earlier
        decomposition skipped stays ``skipped`` after tasks.md is regenerated
        (adversarial review, 2026-10-05). *human_ids*, when given, are that
        decomposition's manual tasks and REPLACE ``implement_human_task_ids``
        the same way — the key is absent when there are none, so a plan with
        no manual task gains no key (fix round 7: the backstop in
        :meth:`deferred_implementation_tasks`). *depends_on*, when given, is
        that decomposition's graph (every task's ``depends_on``, each list
        stored sorted and de-duplicated) and REPLACES
        :data:`IMPLEMENT_TASK_GRAPH_KEY` (fix round 12). Returns whether
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
        # Each list sorted and de-duplicated (fix round 13), so the record
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
        return True

    #: The recorded reason of an implement task the USER declined at
    #: pause-and-ask (``write_batch_scheduler.resolve_human_task_plan``, and
    #: the same words ``instructions/implement.md`` gives the native host). A
    #: decision, not a deferral: the task is not left for them to do.
    _USER_DECLINED_REASON = "skipped by user during pause-and-ask"

    #: The recorded reason's prefix for a failed code task the user answered
    #: ``--human-task <id>=skip`` (``write_batch_scheduler.ANSWERED_SKIP_PREFIX``
    #: spells it). A decision too: the user gave the task up, so it is not
    #: owed as manual work, and neither is a dependent skipped with it.
    _ANSWERED_SKIP_PREFIX = "skipped — you answered --human-task "

    #: The recorded reason of a dependent the transitive skip walk took with
    #: its parent (both legs spell it ``skipped — depends on skipped task
    #: {parent_id} ({parent_title})``); owed exactly when the parent is.
    _DEPENDS_ON_SKIPPED = re.compile(r"^skipped — depends on skipped task (T[0-9]{3})\b")

    def _deferred_to_user(self, task_id: str, seen: Optional[set] = None) -> bool:
        """Whether *task_id*'s skip leaves the task for the user to do.

        A deferral (a human task under a skip strategy, ``deferred — …``) and
        a dependent of one are owed; a pause-and-ask "Skip", a failed code
        task answered ``--human-task <id>=skip``, and a dependent of either
        are not. A reason this does not recognise — none recorded, a state
        written before reasons were — stays owed, as every skip used to be.
        """
        reason = str((self.state.get("task_status_reasons") or {}).get(task_id) or "")
        if reason.startswith((self._USER_DECLINED_REASON, self._ANSWERED_SKIP_PREFIX)):
            return False
        match = self._DEPENDS_ON_SKIPPED.match(reason)
        seen = set() if seen is None else seen
        if match is None or task_id in seen:
            return True
        seen.add(task_id)
        return self._deferred_to_user(match.group(1), seen)

    def deferral_root(self, task_id: str) -> Optional[str]:
        """The task a dependent skipped with a deferral waits on: the end of
        its ``skipped — depends on skipped task …`` chain (the manual task),
        or ``None`` when *task_id* was not skipped as a dependent.

        Fix round 17: such a task is a code task (or a check) the run did not
        do, not manual work. It runs on the resume that records its manual
        task done (``--human-task <id>=done``), so every surface names it
        apart: ``waits_on`` on its :meth:`deferred_implementation_tasks`
        entry, "skipped (depends on manual T005)" on ``status``.
        """
        reasons = self.state.get("task_status_reasons") or {}
        root: Optional[str] = None
        current = task_id
        seen: set = set()
        while current not in seen:
            seen.add(current)
            match = self._DEPENDS_ON_SKIPPED.match(str(reasons.get(current) or ""))
            if match is None:
                break
            root = current = match.group(1)
        return root

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
        (:meth:`deferral_root`, fix round 17): implement runs it once that
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
        # The backstop (fix round 7): implement is on record as completed and
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

        Fix round 16: the how-to-close note answered every deferred id, so a
        code task ``skip-dependents`` skipped with a manual task got
        ``--human-task <id>=done`` too, which implement refuses (a code task is
        answerable only once it failed); it runs on that same resume once its
        manual task is done. A state with no ``implement_human_task_ids`` (one
        written before fix round 7) keeps every id, as before.
        """
        ids = [str(entry.get("id")) for entry in deferred
               if isinstance(entry, dict) and entry.get("id")]
        human = self.state.get("implement_human_task_ids")
        if not isinstance(human, list):
            return ids
        manual = {str(task_id) for task_id in human}
        # Fix round 28 (live run 12, Codex racing 06): only the ones the user
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
        problems are still in the code, fix round 11) and scoped to the
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
        :meth:`implementation_check_findings` is (fix round 15).
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
        user accepted for a check (fix round 23).

        ``[{id, title, checks: {check_id: findings}}]`` from
        :data:`TASK_BATCH_CHECK_ACCEPTED_KEY`, for tasks recorded
        ``completed`` and scoped to the decomposition implement ran last, as
        :meth:`implementation_batch_check_findings` is.
        """
        return self._implementation_batch_check_by_check(TASK_BATCH_CHECK_ACCEPTED_KEY)

    def implementation_batch_check_repeats(self) -> List[Dict[str, Any]]:
        """The implement tasks whose own check reported only what a check
        task of the run reported (fix round 28): ``[{id, title, checks:
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

        Every stamp goes through :func:`_parse_completion_time`, the reading
        ``phase_completion_is_stale`` and ``is_phase_started`` give a stamp
        (``write_batch_scheduler._parse_local_timestamp`` and
        ``check_workflow_prerequisites._parse_timestamp`` are its copies), so
        a stamp with a UTC offset and a naive local one compare as instants.

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
        return bool(stamps) and max(stamps) < reviewed_at

    def has_plan_changed(self) -> bool:
        """Check if plan has changed since last run."""
        return self.state.get("plan_changed", False)

    def clear_plan_changed_flag(self) -> None:
        """Clear the plan changed flag."""
        self.state.pop("plan_changed", None)

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

        The one writer of a commit front door's record (plans/review-commits.md
        §2.1, "Who writes ``commit_range``"): step 6 of ``--review-commits``,
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
        restarted phase ever runs (§2.7, "Not candidates").
        """
        if self.read_only:
            raise RuntimeError(
                f"read-only StateManager for {self.plan_path} cannot record commit_range"
            )
        from .metrics import state_file_lock

        # The lock lives beside the file; a folder that does not exist yet has
        # nothing to lock, so it is made first.
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with state_file_lock(self.state_file):
            loaded: Any = None
            if self.state_file.exists():
                try:
                    loaded = self._read_upgraded()
                except (OSError, ValueError):
                    loaded = None
            if not isinstance(loaded, dict):
                loaded = self._create_initial_state()
            self.state = loaded
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
        """Reset state to initial values (preserves plan reference)."""
        self.state = self._create_initial_state()

    def delete(self) -> None:
        """Delete the state file."""
        if self.state_file.exists():
            self.state_file.unlink()

    # --- Human Task Strategy ---

    def save_human_task_strategy(self, strategy: str) -> None:
        """Persist the chosen human task handling strategy.

        Args:
            strategy: One of "pause-and-ask", "skip-continue", "skip-dependents", "cancel"
        """
        self.state["human_task_strategy"] = strategy

    def get_human_task_strategy(self) -> Optional[str]:
        """Get the previously chosen human task handling strategy.

        Returns:
            Strategy string if set, None otherwise (user should be re-prompted)
        """
        return self.state.get("human_task_strategy")

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

    def get_human_decision(self, phase: str, group_id: str) -> Optional[Dict[str, Any]]:
        """Get previously recorded human decision for an item."""
        key = f"human_decisions_{phase}"
        decisions = self.state.get(key, {})
        return decisions.get(group_id)

    def get_all_human_decisions(self, phase: str) -> Dict[str, Dict[str, Any]]:
        """Get all recorded human decisions for a phase."""
        key = f"human_decisions_{phase}"
        return self.state.get(key, {}).copy()

    def clear_human_decisions(self, phase: str) -> None:
        """Clear all human decisions for a phase (for fresh start)."""
        key = f"human_decisions_{phase}"
        self.state.pop(key, None)

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

    def get_processed_items(self, phase: str) -> Dict[str, Dict[str, Any]]:
        """Get all processed items for a phase."""
        key = f"processed_{phase}"
        return self.state.get(key, {}).copy()

    def is_item_processed(self, phase: str, group_id: str) -> bool:
        """Check if an item has already been processed."""
        key = f"processed_{phase}"
        return group_id in self.state.get(key, {})

    def clear_processed_items(self, phase: str) -> None:
        """Clear all processed items for a phase (for fresh start)."""
        key = f"processed_{phase}"
        self.state.pop(key, None)

    def clear_processing_progress(self, phase: str) -> None:
        """Clear processing progress for a phase."""
        key = f"progress_{phase}"
        self.state.pop(key, None)


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
