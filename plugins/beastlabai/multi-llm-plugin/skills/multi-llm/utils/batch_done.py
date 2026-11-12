#!/usr/bin/env python3
"""``util batch-done``: the native write leg's per-batch progress record.

The four write phases' native leg hands its batches to the host, which
applies them one at a time. Until 2026-10-05 nothing on that leg recorded
which batches had finished: the orchestrator recorded the phase *started*
at emit, ``util next-command`` offered ``--<mode> <plan> --resume`` for it,
and that ``--resume`` — filtering on a ``processed_<phase>`` map nothing had
ever written — printed ``[resume] 0 already processed`` and re-emitted every
batch under the same ``prior_changes_id``, so a host following the offered
command re-applied batches to an already-edited plan (reviewer repro,).

This command is the record. The host runs it once per batch, right after
it verified the batch's outcome and before it appends the batch's summary
to the prior-changes log, and it writes the same ``state.json`` keys the
executor leg's ``WriteBatchScheduler`` writes for the same batch, through
the writer both legs share (:func:`write_record.record_batch_facts`):

* ``task_status[<task id>]`` = ``completed`` | ``failed`` (plus
  ``task_status_reasons`` when ``--reason`` is given) — what
  ``check_workflow_prerequisites`` reads as the phase's progress and what
  ``implement --resume`` filters its tasks on;
* for the three apply kinds, ``processed_<phase dir word>[<member id>]`` for
  every id in the task's ``expected_ids`` (``applied`` | ``declined`` |
  ``skipped`` | ``failed``, :func:`state_manager.record_batch_items_in_state`,
  the scheduler's own writer) — the map
  ``ApplyOrchestratorBase`` step 23 drops groups on under ``--resume``.
  A ``failed`` record keeps the batch eligible for re-dispatch, as the
  executor leg re-dispatches a failed batch;
* for the two shared-artifact kinds, ``batch_snapshot_records[<phase dir
  word>][<task id>]``: ``run`` and, when the batch's pre-batch snapshot is
  bound to it, ``snapshot_generation`` (:func:`write_prompt.completion_stamp`);
* for the two code kinds (``implement``, ``apply_code_fixes``),
  ``tracked_files`` from the dirty-tree census, as the scheduler records it
  after each batch (:func:`_tracked_after_batch`).

It edits ``state.json`` as a file (read, mutate through the state manager's
module-level helpers, atomic replace) in one ``state_file.update``, under
the state lock — the host may record same-batch tasks in parallel — never through a
``StateManager`` —
which would read the plan the batch just edited as a human's mid-workflow
edit — and preserves every other key: the host's closing ``--mark-completed``
re-reads the same file.

:func:`unrecorded_logged_batches` is the other half, shared by both native
emit paths (``apply_orchestrator_base``, ``implement_orchestrator``): on a
native ``--resume``, a batch about to be emitted whose ``prior_changes_id``
already has an entry in this phase's log and which no record says finished
is one a host applied without recording. Re-emitting it would apply it
twice, so the resume is refused (exit 3) naming the batch, this command and
``--fresh``.

Usage::

    multi_llm.py util batch-done --phase-dir <dir> --task-id <id> \\
        --status completed|failed [--reason TEXT] [--partial] [--state-file PATH] \\
        [--check passed|findings|could-not-run [--finding TEXT ...]] \\
        [--own-check passed|findings|none [--finding TEXT ...]]

``--check`` is a check task's structured result (an implement task that
declares no files; its reply's ``check`` object): ``findings`` records each
``--finding`` in ``state.json``'s ``task_check_findings`` beside a
``completed`` status, which ``status``, the result notice and review-code's
implementation record read (racing re-run 4, 2026-10-05). It also holds back
the tasks that depend on the check: each one with no record
yet is recorded ``pending`` with ``not run — upstream check <id> reported
problems``, the ``[CHECK_BLOCKED]`` line names them, ``util write-prompt``
refuses them, and ``util finalize-tracking --mark-completed`` refuses while
one is left — the plugin's enforcement of what the instructions tell the
host, as the executor leg enforces it in its loop. Any later record of the
check (``--check passed``, ``--status failed``) releases them.
``could-not-run`` is a check whose reply said
``check.could_not_run: true``: recorded ``--status failed`` (its reason
defaults to saying so), never as findings; a ``failed`` reply that lists
findings without it ran, and is recorded ``--status completed --check
findings``. A batch that edits code (implement's tasks that declare files,
apply-code-fixes' batches) records the checks it ran on its
own edits with ``--own-check passed|findings``: a failing one prints a
``[BATCH_CHECK_FAILED]`` line telling the host to list it in summary.md and
report it, and holds nothing back; ``--own-check none`` is a
reply whose ``check`` says it ran no check, recorded as no check. Which of the
three a reply's ``check`` is, is one rule on both legs, stated in
``references/own-check.md``. A ``completed`` record of such a batch
given no ``--own-check`` (of a check task, no ``--check``) prints
``[OWN_CHECK_NOT_RECORDED]`` (``[CHECK_NOT_RECORDED]``) naming the call that
records the result with the same flags; beside a recorded
``--listed-check`` it asks only for the reply's ``passed``/``findings`` and
never offers a pass beside a listed failure; advisory, and
nothing is recorded in its place. ``--check`` on such a batch is refused,
naming the ``--own-check`` call, and
``--own-check`` on a check task is refused naming ``--check``: the two words
are two kinds of task, and the plugin says which one the host has. An
implement task's ``--finding`` that only repeats what the user accepted for
a check (``--human-task <check>=done``; ``split_accepted_findings``) is printed as
``[BATCH_CHECK_ACCEPTED]`` and never recorded as the
task's own failing check; anything else it reports still is.

After a commit review an apply-code-fixes ``--status completed`` record re-hashes the
apply guard's protected set first, against the ids ``util write-prompt``
read when it bound the batch's prompt (the batch's own window, as on the
executor): a batch that changed a protected path is refused with exit 3 and
``[COMMIT_PROTECTED_WRITE] <task id>: <paths>`` naming the copies the guard
kept (``apply-fixes/protected/``) as the way back when they hold what the
path held before the batch, and nothing is recorded. A record whose
repository root ``git_utils.pin_repo_root`` cannot pin (a ``GIT_DIR`` or
``GIT_WORK_TREE`` in the environment, a disagreeing ``core.worktree``, no
``.git`` entry above the phase dir) is refused with exit 3 too, nothing
recorded: the check cannot run without it. Otherwise the batch's own fix files are
re-pinned to the bytes it left, so a later batch on them passes ``util
write-prompt``'s re-check by their sha256 (:func:`_commit_completion`).
Without a guard nothing of this runs.

Import is side-effect free: argparse and all I/O live inside :func:`main`.
"""

from __future__ import annotations

import argparse
import os
import shlex
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from . import known_checks as _known_checks
from . import prior_changes as _prior_changes
from .metrics import (
    METRICS_TEMP_PREFIX, mark_failed_in_progress, restore_to_progress_in_state,
    withdraw_from_progress_in_state,
)
from .state_file import StateDocumentError
from .state_file import update as update_state
from .state_manager import (
    PROCESSED_LEG_NATIVE,
    TASK_RESET_AT_KEY,
    _parse_completion_time,
    update_task_status_in_state,
)
from .git_utils import pin_repo_root
from .stream_bootstrap import bootstrap_streams
from .batch_reply import (
    CHECK_NOTE_MAX_CHARS,
    DECLINED_SECTION_HEADING,
    SKIPPED_SECTION_HEADING,
    check_findings_from,
    declined_reason,
)
from .write_safety import file_sha256
from .text_clip import clip, with_closing_mark
from .subagent_tasks import APPLY_WRITE_KINDS, PHASE_BY_WRITE_KIND, snapshot_file_set
from .write_phase_bridge import WRITE_TASK_FILENAME
from .commit_write_guard import (
    batch_fixes_for,
    commit_group_files,
    commit_guard_of,
    commit_head7,
    load_commit_apply,
    load_orchestrator_batches,
)
from .check_records import (
    check_findings_line,
    accepted_findings_for,
    accepted_findings_with_words_added,
    batch_check_accepted_line,
    batch_check_line,
    batch_check_repeated_line,
    repeated_findings_for,
    BLOCKED_BY_CHECK_PREFIX,
    blocked_by_check_reason,
    decomposition_graph,
    rerunnable_checks,
    split_accepted_findings,
    split_repeated_findings,
    transitive_dependents,
    upstream_held_check,
    words_added_to,
)
from .stop_answers import HALF_APPLIED_PREFIX
from .batch_prompt import (
    CODE_WRITE_KINDS,
    is_check_task,
)
from .write_record import BatchFacts, record_batch_facts
from .write_prompt import (
    MARKER_SNAPSHOT, SNAPSHOT_ROLES, WritePromptError, changed_since_bound,
    check_tree_fingerprint, completion_stamp, discard_check_tree,
    load_write_task, record_completion_stamp,
)
from .write_verify import load_finalize_tracking


__all__ = [
    "FINDING_RESTATE_MARKER",
    "BATCH_DECLINED_MARKER",
    "BATCH_SKIPPED_MARKER",
    "CHECK_BLOCKED_MARKER",
    "CHECK_NOT_RECORDED_MARKER",
    "CHECK_RESULTS",
    "MARKER",
    "OWN_CHECK_NOT_RECORDED_MARKER",
    "ProtectedWriteRefused",
    "RESUME_REFUSED_MARKER",
    "STATUSES",
    "record_batch",
    "unrecorded_logged_batches",
    "resume_refusal_lines",
    "main",
]

#: The one stdout line a successful record prints.
MARKER = "[BATCH_DONE]"

#: The line naming the tasks a check with findings holds back (stdout).
CHECK_BLOCKED_MARKER = "[CHECK_BLOCKED]"

#: A ``completed`` record of a task that edits files given no
#: ``--own-check``, and of a check task given no ``--check``, draws one line
#: naming the call to record the result with. Advisory: the record stands,
#: and no result the host did not pass is recorded.
OWN_CHECK_NOT_RECORDED_MARKER = "[OWN_CHECK_NOT_RECORDED]"
CHECK_NOT_RECORDED_MARKER = "[CHECK_NOT_RECORDED]"

#: One line per item an apply batch declined with a reason
#: (``--declined``), and per item the user chose to skip when the batch was
#: kept as it stood (``--skipped``) — both recorded, neither applied.
BATCH_DECLINED_MARKER = "[BATCH_DECLINED]"
BATCH_SKIPPED_MARKER = "[BATCH_SKIPPED]"

#: The reason ``--skipped`` records for an item.
SKIPPED_REASON = (
    "skipped at your request: the batch did not report it applied, and you "
    "chose to keep the batch as it stood"
)

#: The first line of a refused native ``--resume`` (stderr).
RESUME_REFUSED_MARKER = "[RESUME_REFUSED]"

#: The two outcomes the host records; the scheduler's own two words.
STATUSES = ("completed", "failed")

#: ``task_status`` values that say a task's outcome was recorded. Anything
#: else (absent, or the ``pending`` the executor seeds / a cancelled run
#: leaves) is "no record".
_RECORDED_TASK_STATUSES = frozenset({"completed", "failed", "skipped"})

#: ``--check``'s words: what a check task's reply said in its ``check``
#: object (``passed: true`` and no finding, problems found, or — ``could_not_run: true``).
CHECK_RESULTS = ("passed", "findings", "could-not-run")

#: ``--own-check``'s words: what a code batch's reply said in its ``check``
#: object about the checks it ran on its own edits. A code
#: batch has no ``could-not-run``: a check of its own that could not run is
#: one of its findings. ``none``: its ``check`` says it ran no
#: check (an empty ``ran``, ``batch_reply.ran_no_check``) — recorded as
#: no check, never as a pass, as the executor reads the same reply. Only when it also
#: names no finding and does not say it failed
#: (``references/own-check.md``, the rules the native host maps a reply by).
OWN_CHECK_RESULTS = ("passed", "findings", "none")
#: The ``--own-check`` word for a reply that ran no check.
OWN_CHECK_NONE = "none"
#: Where the one rule that maps a reply's ``check`` to ``--own-check`` is
#: stated, as every nudge below names it, and when it is
#: ``none``: the executor's ``batch_check_findings`` follows the same rules.
OWN_CHECK_RULES = "the rules in references/own-check.md"
OWN_CHECK_NONE_WHEN = (
    "when it names no finding, does not say it failed and ran nothing (an "
    "empty `ran`, every entry \"not run\", or only the result shape's "
    "placeholder)"
)

#: The reason ``--check could-not-run`` records when ``--reason`` gives none.
COULD_NOT_RUN_REASON = (
    "its check could not run (the reply said check.could_not_run); fix the "
    "cause and run implement with --resume"
)


class ProtectedWriteRefused(WritePromptError):
    """A ``--status completed`` record refused because the batch changed a
    path the commit review protects: exit 3, *lines* printed to stdout, nothing
    recorded."""

    def __init__(self, lines: List[str]) -> None:
        super().__init__("\n".join(lines))
        self.lines = list(lines)


def _protected_write_lines(
    phase_dir: Path, task_id: str, written: List[str], guard: Dict[str, Any],
    marker: str, *, before: Optional[Dict[str, Optional[str]]] = None,
    copy_held: Optional[Any] = None,
) -> List[str]:
    """``[COMMIT_PROTECTED_WRITE] <task id>: <paths>``, then the way back:
    the copy the guard kept of each file (``protected_copies``) when that
    copy is what the file held before the batch, or, for one absent then,
    its deletion; else "by hand".

    *before* is each path's id before the batch (its bind-time id, else the
    one the guard saved). *copy_held* (``commit_apply.copy_holding``, given
    ``(path, id)``) says whether the guard's copy holds that id; without it
    the copy is taken to hold the saved id, as it was when it was taken."""
    head7 = commit_head7(guard)
    protected = guard.get("protected") if isinstance(guard.get("protected"), dict) else {}
    copies = str(guard.get("protected_copies") or "").rstrip("/")
    # The context plan is watched beside the protected set when it is not in
    # it (`commit_apply.watched_ids`), saved under its own key, and so is
    # each in-repository target of a symlinked one (`context_plan_targets`).
    plan = guard.get("context_plan")
    targets = guard.get("context_plan_targets")
    targets = targets if isinstance(targets, dict) else {}
    plans = [path for path in written if path not in protected
             and ((isinstance(plan, str) and path == plan) or path in targets)]
    one = len(written) == 1
    back: List[str] = []
    for path in written:
        if path not in plans:
            saved = protected.get(path)
        else:
            saved = guard.get("context_plan_id") if path == plan else targets.get(path)
        was = before[path] if before is not None and path in before else saved
        if was is None:
            back.append(f"delete {path} (it did not exist before the batch)")
        elif copies and was not in ("directory", "unreadable") \
                and not str(was).startswith("special:") \
                and (copy_held(path, was) if copy_held is not None else was == saved):
            # A file's bytes (or a symlink) were copied when it was protected
            # (`commit_apply.copy_protected`); a directory never is, and a
            # copy older than an edit made since is never offered.
            back.append(f"copy {copies}/{path} back over {path}")
        else:
            back.append(f"put {path} back as it was before the batch, by hand")
    others = [path for path in written if path not in plans]
    if not plans:
        why = (
            f"{', '.join(written)} changed since "
            f"reviewed commit {head7}, so this apply never writes "
            f"{'it' if one else 'them'} (the commit review's protected set), and "
        )
    else:
        through = (f" (through the symlink {plan})"
                   if any(path != plan for path in plans) else "")
        why = (
            (f"{', '.join(others)} changed since reviewed commit {head7} (the "
             f"commit review's protected set), and " if others else "")
            + f"{', '.join(plans)} {'is' if len(plans) == 1 else 'are'} the "
            f"context plan this review checks the commits against{through}, "
            f"read-only in this review, so this apply never writes "
            f"{'it' if one else 'them'}, and "
        )
    return [
        f"{marker} {task_id}: {', '.join(written)}",
        f"{task_id} was not recorded: {why}"
        f"{'it' if one else 'they'} changed while the batch ran. Stop the loop "
        f"here, as for a partial application. The way back is the copy the "
        f"guard kept: {'; '.join(back)} (unless the change is your own, made "
        f"while the batch ran). Then record the batch with util batch-done "
        f"--phase-dir \"{phase_dir}\" --task-id {task_id} --status failed "
        f"--partial --reason \"it wrote {', '.join(written)}, protected since "
        f"reviewed commit {head7}\", list it in the phase's summary.md as "
        f"failed, and report that its fix needs a protected file changed: the "
        f"user makes that change by hand, or reviews a range that ends at HEAD"
        + (" (the context plan: or reviews again with --context-plan \"\")"
           if plans else "")
        + ".",
    ]


def _unpinned_root_refusal(
    phase_dir: Path, task_id: str, guard: Dict[str, Any], problem: Optional[str],
) -> str:
    """Why a guarded ``--status completed`` record is refused when
    ``git_utils.pin_repo_root`` pins no repository root: the protected-set
    check runs against that root, so without it the batch's writes
    cannot be checked, and *problem* (or the missing ``.git`` entry) is named
    with the way forward."""
    cause = problem or (
        f"no .git entry was found above {phase_dir}, so no repository holds it"
    )
    return (
        f"{task_id} was not recorded: a completed batch of this apply is "
        f"recorded only after the paths protected since reviewed commit "
        f"{commit_head7(guard)} (the commit review's protected set) are "
        f"re-hashed, and that needs the repository root, which cannot be "
        f"pinned: {cause}. Stop the loop here, as for a partial application. "
        f"Put that right (the batch may have made the change itself), then run "
        f"this util batch-done call again: it checks the protected set then and "
        f"records the batch only when none of it changed while the batch ran. "
        f"If it cannot be put right, record the batch with util batch-done "
        f"--phase-dir \"{phase_dir}\" --task-id {task_id} --status failed "
        f"--partial --reason \"its writes could not be checked against the "
        f"protected set\" and report it."
    )


def _commit_completion(
    state: Dict[str, Any], phase_dir: Path, task_id: str, task: Dict[str, Any],
    kind: str,
) -> None:
    """A ``--status completed`` record's half of the commit write policy, on the state dict
about to be written; no-op without a guard.

    The protected set's (and the context plan's, ``commit_apply.
    watched_ids``) current blob ids are compared with the ones ``util
    write-prompt`` read when it bound this batch's prompt
    (``commit_apply.bound_baseline``; the saved ones for a path it did not
    read, or when the prompt was not bound through it), so only a change
    made while the batch ran counts, as on the executor: a user's edit
    between batches, or between a stop and its ``--resume``, is theirs
    (``commit_apply.protected_violations``). A changed one raises
    :class:`ProtectedWriteRefused` before anything is recorded, the bind
    record kept for a retry. Otherwise the record is consumed and the
    batch's own fix files that have an expectation (its primary file and
    every file its fixes name in the phase's ``orchestrator_output.json``)
    are hashed and re-pinned to the bytes it left
    (``commit_apply.repin_after_batch``, which takes only those that changed
    since ``head`` or since their last batch), in the guard this record then
    writes under ``state_file_lock``. Only its own files: a
    file another batch declares that moved meanwhile (an edit made while
    this batch ran) keeps its expectation, so its batch's ``util
    write-prompt`` still stops it.

    The check needs the repository root ``git_utils.pin_repo_root`` pins.
    When it cannot pin one (it raises, names a redirect such as a
    ``GIT_DIR`` or a ``core.worktree`` a batch planted, or finds no ``.git``
    entry above the phase dir), the record is refused with
    :class:`WritePromptError` before anything is recorded, the bind record
    kept for the retry once the cause is put right: a guarded completion is
    never taken on trust.
    """
    guard = commit_guard_of(state, kind)
    if guard is None:
        return
    try:
        root, problem = pin_repo_root(str(phase_dir))
    except Exception as exc:  # noqa: BLE001 - refused below, never skipped
        root, problem = None, f"pinning it failed ({type(exc).__name__}: {exc})"
    if root is None or problem:
        raise WritePromptError(_unpinned_root_refusal(phase_dir, task_id, guard, problem))
    commit_apply = load_commit_apply()
    baseline = commit_apply.bound_baseline(guard, task_id)
    written = [
        str(path) for path in
        commit_apply.protected_violations(guard, cwd=root, baseline=baseline) or ()
    ]
    if written:
        watched = commit_apply.watched_ids(guard)
        raise ProtectedWriteRefused(_protected_write_lines(
            phase_dir, task_id, written, guard,
            getattr(commit_apply, "PROTECTED_MARKER", "[COMMIT_PROTECTED_WRITE]"),
            before={path: (baseline[path] if baseline is not None and path in baseline
                           else watched.get(path)) for path in written},
            copy_held=lambda path, was: commit_apply.copy_holding(
                guard, path, was, cwd=root) is not None,
        ))
    commit_apply.drop_bound(guard, task_id)
    expect = guard.get("expect")
    if not isinstance(expect, dict):
        return
    groups = commit_group_files(
        task, repo_root=root,
        fixes=batch_fixes_for(task, load_orchestrator_batches(phase_dir)),
    )
    own = {path for files in groups.values() for path in files}
    hashed = {
        path: file_sha256(os.path.join(root, path))
        for path in sorted(own) if path in expect
    }
    if hashed:
        commit_apply.repin_after_batch(guard, task_id, hashed, cwd=root)


def _commit_release(state: Dict[str, Any], task_id: str, kind: str) -> None:
    """A record other than ``completed`` consumes the batch's bind-time ids
    (``commit_apply.drop_bound``) in the guard this record then writes: one
    bind verifies one dispatch. No-op without a guard."""
    guard = commit_guard_of(state, kind)
    if guard is None:
        return
    load_commit_apply().drop_bound(guard, task_id)


def _processed_phase_word(phase_dir: Path) -> str:
    """The key suffix of ``processed_<…>``: the phase DIR word.

    ``ApplyOrchestratorBase`` keys the map on its ``phase_name``, which is
    the directory it writes under (``apply-fixes`` for apply-code-fixes,
    whose mode word the task file carries instead).
    """
    return phase_dir.name


def _tracked_after_batch(
    state: Dict[str, Any], target: Path, kind: str,
) -> Optional[List[Dict[str, str]]]:
    """``tracked_files`` after a code phase's batch, or ``None`` to leave it.

    The native leg's counterpart of the scheduler's per-batch record: a host
    that stops part-way, before the closing ``util finalize-tracking``, has
    still recorded what its finished batches changed, so review-code does
    not review what an earlier phase left there. The census alone — this command is
    given no file list; the
    closing ``finalize-tracking --touched …`` adds the verified files — and
    only for the two code kinds: the plan and the task list the planning
    phases edit are never tracked. Never fatal: the batch record is this
    command's job.
    """
    if kind not in CODE_WRITE_KINDS:
        return None
    finalize_tracking = load_finalize_tracking()
    if finalize_tracking is None:
        return None
    try:
        return finalize_tracking.phase_tracked_files(
            state, [], state_path=target, phase=PHASE_BY_WRITE_KIND[kind],
            say=lambda line: None,
        )
    except Exception:  # noqa: BLE001 - bookkeeping must not fail the record
        return None


def record_batch(
    phase_dir: Path,
    task_id: str,
    status: str,
    *,
    reason: Optional[str] = None,
    state_file: Optional[Path] = None,
    check: Optional[str] = None,
    findings: Optional[List[str]] = None,
    own_check: Optional[str] = None,
    declined: Optional[List[str]] = None,
    skipped: Optional[List[str]] = None,
    listed: Optional[List[str]] = None,
    partial: bool = False,
    note: Optional[str] = None,
) -> Dict[str, Any]:
    """Record *task_id*'s outcome; the ``{task_id, status, items, state_file,
    check_findings}`` written.

    *note* (``--note``) is a code batch's own words about the
    checks it ran (its reply's ``check.note``): recorded beside its own
    check (``task_own_check_note`` for an implement task, the
    ``apply_fix_batch_checks`` entry for an apply-code-fixes batch) and
    shown on its ``[BATCH_CHECK_*]`` line, never read as a finding. Only
    with ``--own-check``.

    *partial* (``--partial``) is a ``failed`` task whose
    subagent changed files before it failed: the executor's partial
    application. Its reason is recorded opening with
    ``stop_answers.HALF_APPLIED_PREFIX``, so the native stop offers
    no ``--human-task`` answer for it until the half-applied state is
    inspected (``native_stop_answers``), as the executor's stop offers none.
    Only with ``--status failed``.

    *listed* (``<command>=passed|failed|not run`` each) is an
    apply-code-fixes batch's reply's ``check.listed``: what it says each
    known check its prompt listed did. Recorded with its own check in
    ``state.json``'s ``apply_fix_batch_checks`` (the next batch's prompt and
    the tests-not-run line read it); a command it lists as failed is a
    failing check like a ``--finding``. An entry that cannot be read is left
    out and named (``listed_ignored``), never a refusal.

    *declined* (``<id>=<reason>`` each) and *skipped* (ids) are an apply
    batch's items it did not apply: the items its reply
    declined with a reason, and the items the user chose to skip when a
    batch whose reply left them out was kept as it stood. Each is recorded in
    ``processed_<phase>`` as ``declined`` / ``skipped`` with its reason —
    never ``applied`` — so a ``--resume`` does not hand it out again and
    every reader can name it. Only with ``--status completed``, only for an
    item of this batch, and never for ``implement`` (a task its subagent
    will not do is ``--status failed``).

    *check* / *findings* are a check task's structured result (its reply's
    ``check`` object, racing re-run 4): ``findings`` records them in
    ``state.json``'s ``task_check_findings`` beside a ``completed`` status,
    as the executor leg does; every other record of an implement task clears
    that task's entry. *own_check* / *findings* are a code batch's report of
    the checks it ran on its own edits: a failing one is recorded beside the status
    (``task_batch_check``) and holds nothing back. A ``completed`` record of
    either kind given neither is returned as ``check_not_recorded``
    (``"own-check"`` / ``"check"``), which :func:`main` names
    with the call to make; nothing is recorded in its place.

    Raises :class:`WritePromptError` (exit 3) for a missing task file, an
    unknown id, a human task, a status outside :data:`STATUSES`, or a check
    result that does not fit the task or the status — ``--check`` on a task
    that is not a check task included, naming the call to make instead.
    Nothing is recorded on a refusal.
    """
    if status not in STATUSES:
        raise WritePromptError(
            f"--status must be one of {', '.join(STATUSES)}, not {status!r}."
        )
    if partial and status != "failed":
        raise WritePromptError(
            "--partial is recorded only with --status failed: it says the "
            "task failed after its subagent changed files (its edits are "
            "half-applied). A task whose edits are verified on disk is "
            "--status completed, without --partial. Nothing was recorded."
        )
    if check is not None and check not in CHECK_RESULTS:
        raise WritePromptError(
            f"--check must be one of {', '.join(CHECK_RESULTS)}, not {check!r}."
        )
    if own_check is not None and own_check not in OWN_CHECK_RESULTS:
        raise WritePromptError(
            f"--own-check must be one of {', '.join(OWN_CHECK_RESULTS)}, not "
            f"{own_check!r}."
        )
    if check is not None and own_check is not None:
        raise WritePromptError(
            "Pass --check or --own-check, not both: --check records a check "
            "task's verdict (an implement task that declares no files), "
            "--own-check the checks a task that edits files ran on its own "
            "edits. Nothing was recorded."
        )
    if str(note or "").strip() and own_check is None:
        raise WritePromptError(
            "--note is recorded only with --own-check (a task that edits "
            "files): it is that task's own words about the checks it ran, "
            "from its reply's check.note. Pass it beside --own-check, or "
            "leave it out. Nothing was recorded."
        )
    note = clip(note, CHECK_NOTE_MAX_CHARS) if str(note or "").strip() else None
    if findings and check != "findings" and own_check != "findings":
        raise WritePromptError(
            "--finding is recorded only with --check findings (a check task) "
            "or --own-check findings (a task that edits files): pass one of "
            "them and one --finding per problem the check reported."
        )
    if own_check == "findings" and status != "completed":
        raise WritePromptError(
            "--own-check findings is recorded with --status completed: the "
            "task's edits are kept and the check it ran on them is reported "
            "as failing. A task that failed is recorded --status failed "
            "(with --reason), without --own-check. Nothing was recorded."
        )
    if check == "findings" and status != "completed":
        raise WritePromptError(
            "A check that ran and reported problems is recorded "
            "--status completed with --check findings, also when its reply "
            "said \"status\": \"failed\" but listed findings and did not say "
            "\"could_not_run\": true: the tasks that do not depend on it go "
            "on and review-code is told about the findings. Use --status "
            "failed --check could-not-run for a check whose reply said "
            "\"could_not_run\": true, and --status failed (without --check) "
            "for one that failed listing no finding or whose subagent changed "
            "a file."
        )
    if check == "could-not-run" and status != "failed":
        raise WritePromptError(
            "A check that could not run is recorded --status failed with "
            "--check could-not-run: it says nothing about the code, so it is "
            "never a pass or a finding, and implement stops on it."
        )
    phase_dir = Path(phase_dir).resolve()
    document, task = load_write_task(phase_dir, task_id)
    kind = str(document.get("kind") or "")
    if kind not in PHASE_BY_WRITE_KIND:
        raise WritePromptError(
            f"{phase_dir / WRITE_TASK_FILENAME} is a {kind!r} task file, not a "
            f"write phase's (known: {', '.join(PHASE_BY_WRITE_KIND)})."
        )
    not_applied = _not_applied_items(task_id, task, kind, status, declined, skipped)
    if task.get("is_human") or str(task.get("executor_role") or "") == "human":
        raise WritePromptError(
            f"Task {task_id} is a human task: it never dispatches to a "
            f"subagent, so there is no batch outcome to record. Answer it "
            f"through the phase's human-task strategy instead."
        )
    checking = is_check_task(kind, task)
    flag = "--check" if check is not None else "--own-check"
    if (check is not None or own_check is not None) and kind not in CODE_WRITE_KINDS:
        raise WritePromptError(
            f"Task {task_id} edits the plan or the task list, not code, "
            f"so it has no check result: record it without {flag}. Nothing "
            f"was recorded."
        )
    if check is not None and not checking:
        # `--check passed`
        # was accepted for T008, which declares index.html, and the host's
        # summary called the code task `Verified`. A code batch's own checks
        # are `--own-check`.
        raise WritePromptError(
            _not_a_check_task_message(phase_dir, task_id, task, kind, status)
        )
    if own_check is not None and checking:
        raise WritePromptError(
            f"{task_id} declares no files, so it is a check task: its reply's "
            f"`check` is its verdict. Record it with --check instead of "
            f"--own-check: util batch-done --phase-dir \"{phase_dir}\" "
            f"--task-id {task_id} --status completed --check passed (or "
            f"--check findings with one --finding per problem, or --status "
            f"failed --check could-not-run when its check could not run). "
            f"Nothing was recorded."
        )
    if checking and status == "completed":
        changed = changed_since_bound(
            phase_dir, task_id,
            [t for t in (document.get("batches") or document.get("tasks") or [])
             if isinstance(t, dict)],
        )
        if changed:
            raise WritePromptError(_changed_a_file_message(phase_dir, task_id, changed))
    check_findings: Optional[List[str]] = None
    batch_check: Optional[List[str]] = None
    if partial:
        # The executor's partial application, on record.
        reason = HALF_APPLIED_PREFIX + (
            str(reason or "").strip()
            or "its subagent failed after changing some of its files"
        )
    if check == "could-not-run":
        reason = reason or COULD_NOT_RUN_REASON
    elif check is not None:
        check_findings = check_findings_from({
            "check": {"passed": check == "passed", "findings": list(findings or [])}
        }) or []
    elif own_check is not None and own_check != OWN_CHECK_NONE:
        # A code batch's own check: reported, never a hold.
        batch_check = check_findings_from({
            "check": {"passed": own_check == "passed", "findings": list(findings or [])}
        }) or []
    listed_outcomes, listed_ignored = _listed_checks(listed)
    if listed_outcomes and kind != "apply_code_fixes":
        # Only an apply-code-fixes batch is told the known checks.
        listed_ignored += [f"{c}={w}" for c, w in listed_outcomes.items()]
        listed_outcomes = {}
    if listed_outcomes and status == "completed":
        # A known check the reply lists as failed is a failing
        # check on every surface, as the executor reads it.
        batch_check = _known_checks.with_listed_failures(batch_check, listed_outcomes)
    # The tree a check with findings leaves: a native
    # `--resume` hands the check out again only once the files moved since,
    # as the executor does from its verdict's stamp. `util finalize-tracking`
    # re-stamps it with the tree the run ends on.
    tree = check_tree_fingerprint(phase_dir) if check_findings else None
    # A shared-artifact batch's record names its run and its pre-batch
    # snapshot's generation: what the next `util write-prompt` checks instead
    # of clock times (docs/development/write-safety.md).
    stamp = completion_stamp(phase_dir, kind, task)
    target = Path(state_file) if state_file else phase_dir.parent / "state.json"
    if not target.is_file():
        raise WritePromptError(
            f"No state file at {target}: the phase's orchestrator writes it "
            f"when it emits its batches (pass --state-file if it lives elsewhere)."
        )
    # One lock from the read to the write: the host may record
    # same-batch tasks in parallel, and the census below takes seconds, so an
    # unlocked pair read the same file and the second write dropped the
    # first one's `task_status`. `update` holds the state lock throughout.
    def not_an_object(exc: StateDocumentError) -> WritePromptError:
        return WritePromptError(f"{target} is not a JSON object ({exc.detail}).")

    with update_state(target, temp_prefix=METRICS_TEMP_PREFIX,
                      on_invalid=not_an_object) as state:
        if status == "completed":
            # A batch that wrote a protected
            # path, or whose repository root cannot be pinned for that
            # check, is refused (nothing recorded); else its fix files are
            # re-pinned. No-op without an apply guard.
            _commit_completion(state, phase_dir, task_id, task, kind)
        else:
            # Any record of the batch consumes its bind-time ids.
            _commit_release(state, task_id, kind)

        record_completion_stamp(state, _processed_phase_word(phase_dir), task_id, stamp)
        accepted_again: Dict[str, List[str]] = {}
        echoed: Dict[str, List[str]] = {}
        restate: Optional[Dict[str, Any]] = None
        phase_tasks = [
            t for t in (document.get("batches") or document.get("tasks") or [])
            if isinstance(t, dict)
        ]
        if kind == "implement" and batch_check:
            # What only repeats findings the user accepted for
            # a check is that check's, never this task's own failure (the
            # executor's reading, `split_accepted_findings`). Only the checks this task
            # was told were accepted, and none
            # whose failure is its own job (`accepted_findings_for`).
            accepted = accepted_findings_for(phase_tasks, task, state)
            reported = list(batch_check)
            own, accepted_again = split_accepted_findings(batch_check, accepted)
            if accepted_again:
                batch_check = own
            # And what is the same finding a check task of the
            # run already reported is that check's (`repeated_findings_for`).
            own, echoed = split_repeated_findings(
                own, repeated_findings_for(phase_tasks, task, state))
            if echoed:
                batch_check = own
            # A finding that holds an accepted one word for
            # word with words added stays the task's own; the host is told
            # how to record it again restated (`main`), never told it is
            # accepted.
            flagged = accepted_findings_with_words_added(own, accepted)
            if flagged:
                swap = {finding: accepted_text for finding, _c, accepted_text in flagged}
                added = [words_added_to(finding, text) for finding, _c, text in flagged]
                restate = {
                    "flagged": flagged,
                    "findings": [swap.get(finding, finding) for finding in reported],
                    "note": clip("; ".join(
                        part for part in [note or "", *added] if part), CHECK_NOTE_MAX_CHARS),
                }
        # The record the executor's scheduler writes for the same outcome,
        # through the same writer (`write_record`).
        record = record_batch_facts(state, task, BatchFacts(
            task_id=task_id, kind=kind, status=status, reason=reason,
            leg=PROCESSED_LEG_NATIVE, processed_phase=_processed_phase_word(phase_dir),
            check_findings=check_findings, check_tree=tree, batch_check=batch_check,
            own_check_ran=own_check not in (None, OWN_CHECK_NONE),
            batch_check_accepted=accepted_again, batch_check_repeats=echoed,
            note=note, listed=listed_outcomes,
            declined={i: why for i, (w, why) in not_applied.items() if w == "declined"},
            skipped={i: why for i, (w, why) in not_applied.items() if w == "skipped"},
        ), tasks=phase_tasks)
        blocked: List[str] = []
        if kind == "implement":
            blocked = _hold_or_release_dependents(
                state, document, task_id, held=bool(check_findings),
            )
        # Every write kind, so a
        # native apply batch recorded failed closes its run on "run
        # stopped", as the executor's does, and one refused before dispatch
        # leaves its total.
        _settle_eta_total(state, document, task_id, status, reason, blocked)
        tracked = _tracked_after_batch(state, target, kind)
        if tracked is not None:
            state["tracked_files"] = tracked
        state["updated_at"] = datetime.now().isoformat()
    if checking:
        # One record verifies one dispatch: a later record of this check
        # without a new `util write-prompt` has nothing to compare against.
        discard_check_tree(phase_dir, task_id)
    # A code kind's `completed` record given no check result
    # at all. Named by `main`; never filled in here.
    result_left_out = (
        ("check" if checking else "own-check")
        if status == "completed" and kind in CODE_WRITE_KINDS
        and check is None and own_check is None
        else None
    )
    return {
        "task_id": task_id, "status": status, "items": record.items,
        "state_file": str(target), "check_findings": check_findings or [],
        "batch_check": batch_check or [],
        "batch_check_accepted": accepted_again,
        "blocked": blocked,
        "declined": {
            item: why for item, (word, why) in not_applied.items()
            if word == "declined"
        },
        "skipped": {
            item: why for item, (word, why) in not_applied.items()
            if word == "skipped"
        },
        "listed": listed_outcomes,
        "listed_ignored": listed_ignored,
        "partial": bool(partial),
        "check_not_recorded": result_left_out,
        "note": note,
        "restate": restate,
        "batch_check_repeats": echoed,
        "repeats_moved": {
            moved_id: merged for moved_id, (_own, merged) in record.repeats_moved.items()
        },
    }


def _listed_checks(values: Optional[List[str]]) -> Tuple[Dict[str, str], List[str]]:
    """``({command: outcome}, ignored)`` from ``--listed-check`` values
    (``<command>=<outcome>``, split at the last ``=`` since a command may hold
    one); an entry with no ``=`` or an outcome that cannot be read is
    ignored, never guessed."""
    raw: Dict[str, Any] = {}
    ignored: List[str] = []
    for value in values or []:
        command, sep, word = str(value).rpartition("=")
        if not sep or not command.strip():
            ignored.append(str(value))
            continue
        raw[command] = word
    outcomes = _known_checks.listed_check_outcomes(raw)
    for command, word in raw.items():
        if _known_checks.normalized(command) not in outcomes:
            ignored.append(f"{command}={word}")
    return outcomes, ignored


def _record_again_call(args: argparse.Namespace, result_flag: str) -> str:
    """The ``util batch-done`` call that records *args*' task again with
    *result_flag* added, every other flag as it was given: a record without
    its ``--declined`` would record the declined item applied."""
    parts = [
        f"util batch-done --phase-dir \"{Path(args.phase_dir).resolve()}\"",
        f"--task-id {shlex.quote(str(args.task_id))}",
        f"--status {args.status}",
    ]
    if args.reason:
        parts.append(f"--reason {shlex.quote(args.reason)}")
    if args.state_file:
        parts.append(f"--state-file {shlex.quote(args.state_file)}")
    for flag, values in (
        ("--declined", args.declined), ("--skipped", args.skipped),
        ("--listed-check", args.listed_check),
    ):
        parts.extend(f"{flag} {shlex.quote(str(value))}" for value in values or [])
    parts.append(result_flag)
    return " ".join(parts)


#: The line ``util batch-done`` prints for a finding that holds a finding
#: the user accepted, word for word, with words added.
FINDING_RESTATE_MARKER = "[FINDING_RESTATE]"


def finding_restate_line(
    args: argparse.Namespace, task_id: str, restate: Dict[str, Any],
) -> str:
    """The :data:`FINDING_RESTATE_MARKER` line (live run 12:
    Claude Code's host recorded T007's "… (known problem the user accepted
    in T002)" as written, and the strict match read it as T007's own
    failure). It names each such finding and the accepted finding it holds,
    says it is recorded as the task's own failure, and gives the one call
    that records the task again with the accepted finding alone and the
    added words as its ``--note`` — for the host to run only when those
    words are its subagent's comment. The plugin never records it as
    accepted itself (``check_records.accepted_findings_with_words_added``).
    It says plainly that a
    note is a comment, never a failure, so a failure the added words report
    stays a finding."""
    flagged = list(restate.get("flagged") or [])
    named = "; ".join(
        f"its finding \"{clip(finding, 160)}\" holds the finding the user "
        f"accepted for {check_id} word for word, with words added"
        for finding, check_id, _accepted in flagged
    )
    flags = "--own-check findings " + " ".join(
        f"--finding {shlex.quote(str(finding))}"
        for finding in restate.get("findings") or []
    )
    if restate.get("note"):
        flags += f" --note {shlex.quote(str(restate['note']))}"
    return (
        f"{FINDING_RESTATE_MARKER} {task_id}: {named}, so it is recorded as "
        f"{task_id}'s own failure. If those added words are its subagent's "
        f"comment, record {task_id} again with the accepted finding alone and "
        f"the words as its note: {_record_again_call(args, flags)} (that "
        f"record replaces this one, and the line it prints is the one to "
        f"follow). A note is a comment, never a failure: nothing in it is "
        f"ever read as one. If the added words report something the check "
        f"printed beyond the accepted finding (another value, test or line), "
        f"leave the record as it is, so that failure stays a finding."
    )


def check_not_recorded_line(
    args: argparse.Namespace, which: str, listed: Optional[Dict[str, str]] = None,
) -> str:
    """The line a ``completed`` record given no check result prints:
``[OWN_CHECK_NOT_RECORDED]`` for a task that edits files,
    ``[CHECK_NOT_RECORDED]`` for a check task, each naming the call that
    records the result its reply reported.

    *listed* is what the record did carry of an apply-code-fixes batch's
    ``check.listed`` (``{command: outcome}``). Those are on record, so the line
    asks only for the rest of the reply's ``check``, its ``passed`` and
    ``findings``, and never offers ``--own-check passed`` beside a listed
    failure (review: the same call printed
    ``[BATCH_CHECK_FAILED]`` and then suggested recording a pass). The line is
    kept rather than dropped there, because the runbook records both and a
    failing check outside the known list is named only in ``findings``.
    """
    task_id = args.task_id
    if which == "check":
        return (
            f"{CHECK_NOT_RECORDED_MARKER} {task_id} is a check task (it "
            f"declares no files) and was recorded completed without --check, "
            f"so its verdict is not on record. Record it again now from its "
            f"reply's `check`: {_record_again_call(args, '--check passed')} "
            f"when it says \"passed\": true with no findings, or the same call "
            f"with --check findings and one --finding per problem; a `check` "
            f"that says \"could_not_run\": true is recorded --status failed "
            f"--check could-not-run instead."
        )
    if listed:
        on_record = clip("; ".join(f"{command} {word}" for command, word in listed.items()), 300)
        head = (
            f"{OWN_CHECK_NOT_RECORDED_MARKER} {task_id} edits files and was "
            f"recorded completed with its listed checks ({on_record}) but "
            f"without --own-check, so the rest of its reply's `check`, its "
            f"\"passed\" and \"findings\", is not on record."
        )
        if _known_checks.LISTED_FAILED in listed.values():
            return (
                f"{head} A listed check failed, so its check fails whatever "
                f"\"passed\" says: if its \"findings\" name a failing check, "
                f"record it again now with them: "
                f"{_record_again_call(args, '--own-check findings')} and one "
                f"--finding per entry. Leave the record as it is when they "
                f"name none."
            )
        return (
            f"{head} Record it again now with the result {OWN_CHECK_RULES} "
            f"give for its `check`: {_record_again_call(args, '--own-check passed')} "
            f"for a pass, the same call with --own-check findings and one "
            f"--finding per failing check, or with --own-check none "
            f"{OWN_CHECK_NONE_WHEN}."
        )
    return (
        f"{OWN_CHECK_NOT_RECORDED_MARKER} {task_id} edits files and was "
        f"recorded completed without --own-check, so the checks its subagent "
        f"ran on its own edits are not on record. If its reply carries a "
        f"`check` object, record it again now with the result {OWN_CHECK_RULES} "
        f"give for it: {_record_again_call(args, '--own-check passed')} for a "
        f"pass, the same call with --own-check findings and one --finding per "
        f"failing check, or with --own-check none {OWN_CHECK_NONE_WHEN}. Leave "
        f"the record as it is only when the reply carries no `check`."
    )


def _not_a_check_task_message(
    phase_dir: Path, task_id: str, task: Dict[str, Any], kind: str, status: str,
) -> str:
    """The refusal of ``--check`` for a task that edits code:
    what the task is, and the call that records it."""
    files = snapshot_file_set(task)
    shown = ", ".join(files[:5]) + (f" (+{len(files) - 5} more)" if len(files) > 5 else "")
    what = (
        f"{task_id} declares files ({shown}), so it is a code task, not a "
        f"check task (a check task is an implement task that declares no "
        f"files)" if kind == "implement" and shown else
        f"{task_id} is an apply-code-fixes batch, so it is a code task, not a "
        f"check task (a check task is an implement task that declares no "
        f"files)" if kind != "implement" else
        f"{task_id} is a code task, not a check task"
    )
    call = f"util batch-done --phase-dir \"{phase_dir}\" --task-id {task_id}"
    if status == "completed":
        instead = (
            f"Record the checks its subagent ran on its own edits with "
            f"--own-check instead, as {OWN_CHECK_RULES} read its reply's "
            f"`check`: {call} --status completed --own-check passed for a "
            f"pass, or --own-check findings with one --finding per failing "
            f"check, or --own-check none {OWN_CHECK_NONE_WHEN}; leave "
            f"--own-check out when its reply carries no `check`."
        )
    else:
        instead = (
            f"A code task that failed is recorded without a check result: "
            f"{call} --status failed --reason \"<why it failed>\"."
        )
    return (
        f"{what}, and --check records only a check task's verdict. {instead} "
        f"Nothing was recorded."
    )


def _not_applied_items(
    task_id: str,
    task: Dict[str, Any],
    kind: str,
    status: str,
    declined: Optional[List[str]],
    skipped: Optional[List[str]],
) -> Dict[str, Tuple[str, str]]:
    """``{item id: ("declined" | "skipped", reason)}`` from ``--declined`` /
    ``--skipped``, checked against the batch; raises
    :class:`WritePromptError` naming the problem."""
    if not declined and not skipped:
        return {}
    if kind not in APPLY_WRITE_KINDS:
        raise WritePromptError(
            f"Task {task_id} is an implement task: a task its subagent will not "
            f"do is recorded --status failed --reason \"<why>\", for the user "
            f"to answer with --human-task {task_id}=skip|done. --declined and "
            f"--skipped are for an apply batch's items."
        )
    if status != "completed":
        raise WritePromptError(
            "--declined and --skipped record the items a finished batch did not "
            "apply: pass them with --status completed."
        )
    expected = [str(i) for i in (task.get("expected_ids") or [])]
    out: Dict[str, Tuple[str, str]] = {}
    for value in declined or []:
        item, sep, why = str(value).partition("=")
        item, why = item.strip(), declined_reason(why)
        if not sep or not item or not why:
            raise WritePromptError(
                f"--declined expects <id>=<the reason the batch gave>, got "
                f"{value!r}: a decline without its reason is not recorded."
            )
        out[item] = ("declined", why)
    for value in skipped or []:
        item = str(value).strip()
        if item in out:
            raise WritePromptError(
                f"{item} is given to both --declined and --skipped: record it once."
            )
        out[item] = ("skipped", SKIPPED_REASON)
    unknown = [item for item in out if item not in expected]
    if unknown:
        raise WritePromptError(
            f"{', '.join(unknown)} {'is' if len(unknown) == 1 else 'are'} not an "
            f"item of {task_id} (its items: {', '.join(expected) or 'none'})."
        )
    if (
        any(word == "skipped" for word, _why in out.values())
        and all(item in out for item in expected)
    ):
        # `--skipped` keeps
        # what a batch applied, as the executor's `=skip` does, and that
        # answer is offered only for a report that attests an item applied.
        raise WritePromptError(
            f"--skipped keeps what {task_id} applied and goes on without the "
            f"items its report left out, but here every item of {task_id} is "
            f"declined or skipped, so by its report it applied nothing to "
            f"keep. Stop the loop as for a partial application: "
            f"{_native_undo(kind)}; fix the cause, then resume, and "
            f"{task_id} is handed out again."
        )
    return out


#: What a native apply batch edits, by kind, in the apply instructions' words.
_NATIVE_TARGETS = {"apply_suggestions": "the plan", "apply_task_suggestions": "tasks.md"}


def _native_undo(kind: str) -> str:
    """How a human puts back what a native apply batch changed, worded as the
    apply instructions' partial-application step words it: the native loop
    has no ``pre_batch/`` slot, so ``util restore-batch`` (the executor's
    rollback) finds nothing of its batches (docs/development/write-safety.md,
    "The native leg's per-batch snapshot")."""
    if kind in SNAPSHOT_ROLES:
        target = _NATIVE_TARGETS.get(kind, "the file")
        return (
            f"if the batch changed {target}, copy it back by hand from the "
            f"pre-batch snapshot util write-prompt printed as {MARKER_SNAPSHOT} "
            f"(read the diff first: the batch's subagent could write that copy "
            f"too); util restore-batch holds nothing of a native batch's"
        )
    return (
        "if the batch changed files, undo them by hand: this loop takes no "
        "snapshot of them, so util restore-batch holds nothing of the batch's, "
        "and `git diff -- <the batch's files>` shows its edits, together with "
        "any earlier batch's uncommitted edits to the same files"
    )


def _changed_a_file_message(phase_dir: Path, task_id: str, changed: List[str]) -> str:
    """The refusal of a ``completed`` record for a check that changed files."""
    shown = ", ".join(changed[:10]) + (
        f" (+{len(changed) - 10} more)" if len(changed) > 10 else ""
    )
    return (
        f"{task_id} is a check task (it declares no files), and since its "
        f"prompt was bound with util write-prompt these files changed, which "
        f"no other task in {WRITE_TASK_FILENAME} declares: {shown}. A check "
        f"whose subagent changed a file did not only check, so it is not "
        f"recorded completed (passed or findings): record it --status failed "
        f"--reason \"its subagent changed {changed[0]}\" and keep or undo the "
        f"change. If something other than its subagent changed them (you, or "
        f"a task running beside it), bind its prompt again with util "
        f"write-prompt --phase-dir \"{phase_dir}\" --task-id {task_id} and run "
        f"the check again. Nothing was recorded."
    )


#: How a ``--reason`` starts when ``util write-prompt`` refused the task, so
#: no subagent ran it (``[WRITE_PROMPT_REFUSED]`` prints the record to make).
REFUSED_BEFORE_DISPATCH_REASON = "refused before dispatch"


def _settle_eta_total(
    state: Dict[str, Any], document: Dict[str, Any], task_id: str,
    status: str, reason: Optional[str], held: List[str],
) -> None:
    """Take out of this run's ``[ETA]`` total the handed-out tasks this record
    keeps from being dispatched.

    The native emit's ``tasks_to_dispatch`` — what the host passes as
    ``--total-batches``, one ``util metrics record`` per task it dispatches —
    counts every task in the batches, a task waiting on a check's verdict
    included. A record that settles one of them as never dispatched in this
    run takes it out (``metrics.withdraw_from_progress_in_state``):

    * the tasks a check with findings holds (*held*, the ``[CHECK_BLOCKED]``
      list);
    * after a ``failed`` record, every task that depends on it and has no
      record yet — the host skips them (``instructions/implement.md`` step
      6) — and the task itself when ``util write-prompt`` refused it, since
      no subagent ran.

    Every write kind: an apply batch has no dependents and
    no check, so its record only marks it failed (its run closes on "run
    stopped") or, refused before dispatch, takes it out of the total.

    Only tasks of this phase's ``write_tasks.json`` (what was handed out) and
    never a manual task (``tasks_to_dispatch`` does not count one). A record
    of the same task again first puts back what its earlier record took out,
    then keeps out each of those that another cause still holds
    (:func:`_still_kept_out`). Nothing happens when the host never ran
    ``util metrics start``.
    """
    phase = PHASE_BY_WRITE_KIND.get(str(document.get("kind") or ""), "implement")
    back = restore_to_progress_in_state(state, phase, task_id)
    handed = {
        str(task.get("task_id") or ""): task
        for task in (document.get("batches") or document.get("tasks") or [])
        if isinstance(task, dict)
    }

    def manual(task: Dict[str, Any]) -> bool:
        return bool(task.get("is_human")) or str(task.get("executor_role") or "") == "human"

    out = [t for t in held if t in handed and not manual(handed[t])]
    refused = status == "failed" and str(reason or "").strip().lower().startswith(
        REFUSED_BEFORE_DISPATCH_REASON)
    # A task that ran and failed stops the run short of its
    # phase, so its closing `[ETA]` line says "run stopped", as the
    # executor's does; a refused one is withdrawn below instead.
    mark_failed_in_progress(
        state, phase, task_id, failed=status == "failed" and not refused)
    if refused:
        out.append(task_id)
    if status == "failed" and phase == "implement":
        statuses = state.get("task_status") or {}
        graph = decomposition_graph(list(handed.values()), state)
        for dependent in transitive_dependents(graph, task_id):
            task = handed.get(dependent)
            if task is None or manual(task):
                continue
            if statuses.get(dependent) in (None, "pending"):
                out.append(dependent)
    withdraw_from_progress_in_state(state, phase, out, task_id)
    for dependent, cause in _still_kept_out(state, handed, back):
        withdraw_from_progress_in_state(state, phase, [dependent], cause)


def _still_kept_out(
    state: Dict[str, Any], handed: Dict[str, Dict[str, Any]], back: List[str],
) -> List[Tuple[str, str]]:
    """``(task, cause)`` for each task in *back* — put back in the total as
    the record that took it out was replaced — that another cause still
    keeps from being dispatched: a check with findings upstream of it
    (``rerunnable_checks``), else a failed task upstream of it, while it has
    no record of its own.

    ``withdrawn`` keeps one cause per
    task, so a task taken out after a failed T003 was skipped when check
    T002 then held it ("already out"); T003 retried and recorded completed
    put it back although T002's findings still held it, and the native
    ``[ETA]`` line ended "N/N+1" again. The other way round, T002 passing
    put back a task T003's failure still kept out.
    """
    if not back:
        return []
    statuses = state.get("task_status") or {}
    graph = decomposition_graph(list(handed.values()), state)
    checks = rerunnable_checks(state)
    failed = sorted(str(t) for t, status in statuses.items() if status == "failed")
    kept: List[Tuple[str, str]] = []
    for task_id in back:
        if statuses.get(task_id) not in (None, "pending"):
            continue
        cause = (
            upstream_held_check(graph, task_id, checks)
            or upstream_held_check(graph, task_id, failed)
        )
        if cause:
            kept.append((task_id, cause))
    return kept


def _hold_or_release_dependents(
    state: Dict[str, Any], document: Dict[str, Any], task_id: str, *, held: bool,
) -> List[str]:
    """Record (or release) the tasks a check with findings holds back.

    *held*: the check was just recorded with findings, so every transitive
    dependent with no status yet, or a ``pending`` one, is recorded
    ``pending`` with :func:`blocked_by_check_reason` — the reason the
    executor leg writes for the same tasks. Otherwise each dependent still
    ``pending`` under this check's reason loses it: the check passed, failed
    or was recorded again, and is no longer why it waits — unless another
    check with findings is still upstream of it, whose reason it then
    carries (with two checks holding D, recording the first
    passed cleared D's reason while the second's findings stood). The walk
    is over the whole decomposition (``check_records.decomposition_graph``:
    the task file plus ``state.json``'s recorded graph), not only the tasks
    a resume put in the file. Returns the tasks held (empty
    on a release).
    """
    tasks = decomposition_graph(
        document.get("batches") or document.get("tasks") or [], state,
    )
    by_id = {
        str(t.get("task_id") or ""): t for t in tasks if isinstance(t, dict)
    }
    statuses = state.get("task_status") or {}
    reasons = state.get("task_status_reasons") or {}
    mine = f"{BLOCKED_BY_CHECK_PREFIX}{task_id} "
    still_held = [] if held else [c for c in rerunnable_checks(state) if c != task_id]
    held_ids: List[str] = []
    for dependent in transitive_dependents(tasks, task_id):
        task = by_id.get(dependent, {})
        if task.get("is_human") or str(task.get("executor_role") or "") == "human":
            continue
        status = statuses.get(dependent)
        if held:
            if status in (None, "pending"):
                update_task_status_in_state(
                    state, dependent, "pending", blocked_by_check_reason(task_id),
                )
                held_ids.append(dependent)
        elif status == "pending" and str(reasons.get(dependent) or "").startswith(mine):
            other = upstream_held_check(tasks, dependent, still_held)
            update_task_status_in_state(
                state, dependent, "pending",
                blocked_by_check_reason(other) if other else None,
            )
    return held_ids


def _logged_ids(output_dir: str, phase: Optional[str]) -> set:
    return set(_logged_at(output_dir, phase))


def _logged_at(output_dir: str, phase: Optional[str]) -> Dict[str, Optional[str]]:
    """``{entry id: timestamp of its newest line}`` in this phase's log."""
    scoped = _prior_changes.canonical_phase(phase)
    return {
        str(entry.get("id") or ""): entry.get("timestamp")
        for entry in _prior_changes.entries(output_dir)
        if _prior_changes.canonical_phase(entry.get("phase")) == scoped
    }


def _logged_before_reset(logged_at: Any, reset_at: Any) -> bool:
    """Whether a log line was written no later than its task's reset.

    False when either time is missing or unreadable: the line then counts as
    this run's, which keeps the refusal (absence of a date is not a reset).
    """
    logged = _parse_completion_time(logged_at)
    reset = _parse_completion_time(reset_at)
    return logged is not None and reset is not None and logged <= reset


def unrecorded_logged_batches(
    tasks: Iterable[Dict[str, Any]],
    *,
    output_dir: str,
    phase: str,
    state: Dict[str, Any],
    processed_phase: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """The tasks a native ``--resume`` must not re-emit: logged, never recorded.

    *tasks* are the batches the emit path is about to hand out (already
    filtered by the phase's own resume rule); *phase* is the log's phase
    word (``prior_changes.canonical_phase`` folds ``apply-code-fixes`` and
    ``apply-fixes`` together); *processed_phase* is the ``processed_<…>``
    suffix for an apply kind (defaults to *phase*); *state* is the raw
    ``state.json`` dict.

    A task is recorded when ``task_status`` holds a terminal word for its id
    or, for an apply kind, when any of its ``expected_ids`` is in the
    processed map (``failed`` included: that record keeps the batch eligible
    and says the log's failure entry is accounted for). A log line no newer
    than the task's ``state_manager.TASK_RESET_AT_KEY`` stamp is the run's
    before a start-over or a ``--task`` rerun handed the task out again, and
    does not count. A line the run since wrote with the same
    summary is not appended again (``prior_changes.append``), so such a task
    is handed out again rather than refused.
    """
    logged = _logged_at(output_dir, phase)
    if not logged:
        return []
    task_status = state.get("task_status") or {}
    processed = state.get(f"processed_{processed_phase or phase}") or {}
    reset_at = state.get(TASK_RESET_AT_KEY)
    reset_at = reset_at if isinstance(reset_at, dict) else {}
    unrecorded: List[Dict[str, Any]] = []
    for task in tasks:
        if not isinstance(task, dict):
            continue
        if task.get("is_human") or str(task.get("executor_role") or "") == "human":
            continue
        entry_id = str(task.get("prior_changes_id") or "")
        if not entry_id or entry_id not in logged:
            continue
        task_id = str(task.get("task_id") or "")
        if task_status.get(task_id) in _RECORDED_TASK_STATUSES:
            continue
        if any(str(i) in processed for i in (task.get("expected_ids") or [])):
            continue
        if _logged_before_reset(logged[entry_id], reset_at.get(task_id)):
            # An earlier run's line, for a task a start-over
            # or a `--task` rerun handed out again since — not one this run
            # applied and left unrecorded.
            continue
        unrecorded.append(task)
    return unrecorded


def resume_refusal_lines(
    unrecorded: List[Dict[str, Any]], *, phase_dir: str, mode_word: str,
) -> List[str]:
    """The stderr block a refused native ``--resume`` prints."""
    lines = [
        f"{RESUME_REFUSED_MARKER} --resume would re-emit {len(unrecorded)} "
        f"batch(es) the prior-changes log says already ran, but no progress "
        f"record says they finished — re-applying them would edit the target "
        f"twice:",
    ]
    for task in unrecorded:
        lines.append(
            f"  - {task.get('task_id')} ({task.get('prior_changes_id')}): "
            f"{task.get('task_title') or ''}".rstrip()
        )
    lines.append(
        "Record each one as the host left it, then re-run with --resume:"
    )
    for task in unrecorded:
        lines.append(
            f"  multi_llm.py util batch-done --phase-dir \"{phase_dir}\" "
            f"--task-id {task.get('task_id')} --status completed|failed"
        )
    lines.append(
        f"Or restore the target to its pre-run bytes and start the phase over "
        f"with `{mode_word} <plan> --fresh`."
    )
    return lines


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="multi_llm.py util batch-done",
        description=(
            "Record one write batch's outcome in state.json — the native "
            "leg's counterpart of the executor's per-batch status write, "
            "and what a later --resume skips or retries."
        ),
    )
    parser.add_argument(
        "--phase-dir", required=True,
        help="The phase directory holding write_tasks.json (e.g. "
             "plans/my-plan/apply-suggestions, plans/my-plan/implement).",
    )
    parser.add_argument(
        "--task-id", required=True,
        help="The task id from write_tasks.json (apply-batch-0, "
             "apply-task-batch-0, apply-fix-batch-0, T001, ...).",
    )
    parser.add_argument(
        "--status", required=True, choices=STATUSES,
        help="completed: the batch's edits verified on disk (or a verified "
             "no-op); failed: the subagent failed and the target is unchanged.",
    )
    parser.add_argument(
        "--reason", default=None,
        help="One line on why a failed batch failed (recorded beside the status).",
    )
    parser.add_argument(
        "--state-file", default=None, metavar="PATH",
        help="The plan's state.json; default: <phase-dir>/../state.json.",
    )
    parser.add_argument(
        "--check", default=None, choices=CHECK_RESULTS,
        help="For a check task (an implement task that declares no files) "
             "only: its reply's check result — passed, findings (the check "
             "ran and reported problems; recorded with --status completed), "
             "or could-not-run (its check said could_not_run: true; recorded "
             "with --status failed). A task that edits files takes "
             "--own-check instead.",
    )
    parser.add_argument(
        "--own-check", default=None, choices=OWN_CHECK_RESULTS, dest="own_check",
        help="For a task that edits files (an implement task that declares "
             "files, an apply-code-fixes batch): the checks its subagent ran "
             "on its own edits, from its reply's check object as the rules "
             "in references/own-check.md read it — passed, findings (one "
             "--finding per failing check, with --status completed), or none "
             "(it names no finding, does not say it failed and ran nothing). "
             "Never --check on such a task.",
    )
    parser.add_argument(
        "--finding", action="append", default=None, metavar="TEXT",
        help="One problem a check reported (repeatable; with --check findings "
             "or --own-check findings), exactly as the reply wrote it.",
    )
    parser.add_argument(
        "--note", default=None, metavar="TEXT",
        help="With --own-check: the reply's check.note, its own words about "
             "the checks it ran. Recorded and shown beside them, never read "
             "as a finding.",
    )
    parser.add_argument(
        "--declined", action="append", default=None, metavar="ID=REASON",
        help="An apply batch's item its reply declined, with the reason it "
             "gave (repeatable; with --status completed): recorded as not "
             "applied, never as applied.",
    )
    parser.add_argument(
        "--listed-check", action="append", default=None, dest="listed_check",
        metavar="COMMAND=OUTCOME",
        help="For an apply-code-fixes batch: one entry of its reply's "
             "check.listed, the command as the reply wrote it and what it "
             "says that check did — passed, failed or not run (repeatable).",
    )
    parser.add_argument(
        "--partial", action="store_true", default=False,
        help="With --status failed: the task's subagent changed files before "
             "it failed, so its edits are half-applied. The stop then offers "
             "no --human-task answer for it until they are inspected.",
    )
    parser.add_argument(
        "--skipped", action="append", default=None, metavar="ID",
        help="An apply batch's item its reply left out of both ids and "
             "declined, which the user chose to skip, keeping the batch as it "
             "stood (repeatable; with --status completed): recorded as not "
             "applied, skipped at the user's request.",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    bootstrap_streams()
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        written = record_batch(
            Path(args.phase_dir), args.task_id, args.status,
            reason=args.reason,
            state_file=Path(args.state_file) if args.state_file else None,
            check=args.check,
            findings=args.finding,
            own_check=args.own_check,
            declined=args.declined,
            skipped=args.skipped,
            listed=args.listed_check,
            partial=args.partial,
            note=args.note,
        )
    except ProtectedWriteRefused as exc:
        # The marker and its way back go to stdout, where the host reads
        # every other line of the loop's.
        for line in exc.lines:
            print(line)
        return int(getattr(exc, "exit_code", 3) or 3)
    except WritePromptError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return int(getattr(exc, "exit_code", 3) or 3)
    except OSError as exc:
        print(f"ERROR: cannot update state file: {exc}", file=sys.stderr)
        return 1
    items = written["items"]
    suffix = f" ({len(items)} item(s) recorded)" if items else ""
    found = written.get("check_findings") or []
    if found:
        suffix += f" ({len(found)} check finding(s) recorded)"
    print(f"{MARKER} {written['task_id']} {written['status']}{suffix}")
    if found:
        # The executor's own line, which
        # this leg's host would otherwise never see (no run log here).
        print(check_findings_line(written["task_id"], found))
    if written.get("partial"):
        # The executor's partial-application stop, in words.
        task_id = written["task_id"]
        print(
            f"{task_id}'s edits are half-applied. List it in the phase's "
            f"summary.md as failed with its edits half-applied, naming the "
            f"files its subagent changed, and say in your report that the "
            f"user inspects them (keeps or undoes them) and fixes the cause "
            f"before the --resume, which dispatches {task_id} again on top of "
            f"what is there; the stop offers no --human-task answer for "
            f"{task_id}."
        )
    accepted_again = written.get("batch_check_accepted") or {}
    if accepted_again:
        # Reported again, never the task's own failure.
        task_id = written["task_id"]
        print(
            f"{batch_check_accepted_line(task_id, accepted_again, note=written.get('note'))}. List it in "
            f"the phase's summary.md under ## Check Findings, beside "
            f"{', '.join(accepted_again)}'s accepted findings, as {task_id} "
            f"running that check again: it does not make the phase unclean and "
            f"is not a check of {task_id}'s that fails."
        )
    echoed = written.get("batch_check_repeats") or {}
    if echoed:
        # A check task's finding, never this task's own.
        task_id = written["task_id"]
        print(
            f"{batch_check_repeated_line(task_id, echoed, note=written.get('note'))}. "
            f"List it in the phase's summary.md under ## Check Findings, beside "
            f"{', '.join(echoed)}'s findings, as {task_id} running that check "
            f"too: it is not a check of {task_id}'s that fails."
        )
    for moved_id, merged in (written.get("repeats_moved") or {}).items():
        # The code task recorded first; this check now owns it.
        print(
            f"{batch_check_repeated_line(moved_id, merged)}. Recorded again now "
            f"that {written['task_id']} reported it: the [BATCH_CHECK_FAILED] "
            f"line {moved_id}'s record printed for it no longer stands. List "
            f"{moved_id} in summary.md under {written['task_id']}'s findings, "
            f"not as a check of {moved_id}'s that fails."
        )
    failing = written.get("batch_check") or []
    restate = written.get("restate")
    if failing:
        # The native leg's counterpart of the executor's line.
        print(
            f"{batch_check_line(written['task_id'], failing, note=written.get('note'))}. The edits are "
            f"kept. List it under "
            f"## Check Findings in the phase's summary.md, and say in your "
            f"final report that this check fails: never report the phase as a "
            f"clean success."
        )
    if restate:
        # What to run when the added words are a comment;
        # the plugin never records such a finding as accepted itself.
        print(finding_restate_line(args, written["task_id"], restate))
    ignored = written.get("listed_ignored") or []
    if ignored:
        print(
            f"[batch-done] --listed-check not recorded (expected "
            f"<command>=passed|failed|not run, on an apply-code-fixes batch): "
            f"{clip('; '.join(ignored), 400)}",
            file=sys.stderr,
        )
    for item, why in (written.get("declined") or {}).items():
        # Never applied, and never silent. In its
        # own summary.md section, never under an applied heading. The record keeps the
        # reason's closing stop;: this
        # line adds one only where the reason has no mark of its own.
        print(
            f"{BATCH_DECLINED_MARKER} {written['task_id']} {item}: not applied, "
            f"the batch declined it — {with_closing_mark(why)} List it in "
            f"the phase's summary.md "
            f"under \"## {DECLINED_SECTION_HEADING}\", with its id and this "
            f"reason, never under the applied ones, and name it in your report; "
            f"never count it as applied."
        )
    for item, why in (written.get("skipped") or {}).items():
        print(
            f"{BATCH_SKIPPED_MARKER} {written['task_id']} {item}: not applied, "
            f"{with_closing_mark(why)} List it in the phase's summary.md under \"## "
            f"{SKIPPED_SECTION_HEADING}\", with its id, never under the applied "
            f"ones, and name it in your report."
        )
    blocked = written.get("blocked") or []
    if blocked:
        task_id = written["task_id"]
        print(
            f"{CHECK_BLOCKED_MARKER} {', '.join(blocked)} "
            f"{'depends' if len(blocked) == 1 else 'depend'} on {task_id}, "
            f"whose check reported problems: do not dispatch them (their "
            f"`util write-prompt` refuses) and record nothing for them — they "
            f"stay pending. Run the tasks that do not depend on {task_id}, then "
            f"close the phase without --mark-completed and report the way "
            f"forward: fix what {task_id} reported and re-run implement with "
            f"--resume (the check runs again), or accept its findings with "
            f"--resume --human-task {task_id}=done (they then run, told that "
            f"the findings were accepted), or leave it and them "
            f"undone with --resume --human-task {task_id}=skip."
        )
    which = written.get("check_not_recorded")
    if which:
        # Advisory, so the host records it in the same turn.
        print(check_not_recorded_line(args, which, written.get("listed")))
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main(sys.argv[1:]))
