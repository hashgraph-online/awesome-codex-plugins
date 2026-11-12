#!/usr/bin/env python3
"""``util write-prompt``: one write batch's prompt, bound and ready to dispatch.

The native leg of the four write phases (apply-suggestions,
apply-task-suggestions, apply-code-fixes, implement) hands its batches to the
host, which spawns one subagent per batch. The batch prompts live inside
``orchestrator_output.json`` / ``implementation_tasks_*.json`` and carry a
literal ``{prior_changes_context}`` token the host had to bind itself, from a
``util prior-changes read`` it ran first. Measured on the 2026-10-04 Claude
Code racing re-run: every Task subagent spent three to six tool calls guessing
the JSON shape (``tasks``, ``ts``, ``batches[].tasks[]``) to find its prompt,
and in two phases a subagent skipped the prior changes or read ``tasks.md``
instead of the prompt. Review validation already had ready ``*.prompt.txt``
files; the write phases had none.

This command is that file for a write batch. The orchestrator materializes
``{phase}/write_tasks.json`` on the native leg too (the executor's own task
file, through the same ``utils/write_phase_bridge``), and for one task id
this binds the prompt **late** — against the prior-changes log as it is on
disk at that moment, so it reflects exactly the batches already finished —
and wraps it in the write-batch result contract (fixed blocks first, the
batch's ids last: docs/development/write-scheduler.md "Prompt order").
Both invokers therefore produce byte-identical text for the same
prior-changes log (each leg appends a
summary per finished batch and a failure line per failed one;
a native host words a failure's reason itself): it calls the scheduler's own
:func:`utils.batch_prompt.bind_prior_changes` and
:func:`utils.batch_prompt.with_result_contract`, and
``tests/test_write_prompt.py`` pins the two renderings against each other.

Usage::

    multi_llm.py util write-prompt --phase-dir <dir> --task-id <id> [--output PATH]
    multi_llm.py util write-prompt --phase-dir <dir> --task-id <id> --stdout

By default the prompt is written to ``{phase_dir}/prompts/{task_id}.prompt.txt``
(over-written on every call: a ``--resume`` rebinds it) and three marker lines
go to stdout — ``[WRITE_PROMPT] <path>``, ``[WRITE_PROMPT_LINES] <n>`` and
``[WRITE_PROMPT_CONTEXT] <entries> prior-batch entries bound`` — so the host
can hand the subagent "read this file in full and follow it", the contract
the review phases' ``prompt_path`` already uses. ``--stdout`` prints the
prompt text itself instead, and nothing else. For the two shared-artifact
phases it also takes the batch's pre-batch snapshot (kept when the same batch
is bound again) and prints ``[WRITE_SNAPSHOT] <path>`` and
``[WRITE_ARTIFACT] <path>`` after the three markers (on stderr under
``--stdout``): :func:`prepare_batch_snapshot`. After a commit review
 an apply-code-fixes batch whose fix files
changed since the apply guard decided gets no prompt at all: one
``[COMMIT_FIXES_STALE]`` line replaces the markers (in both modes), the batch
is already recorded, and the exit is 0 (:func:`commit_stale_check`); a batch
that passes has the watched set's disk ids recorded as its prompt is bound,
which its ``util batch-done`` compares with (:func:`commit_bind`). Exit 3 names the problem: no
``write_tasks.json`` (run the phase's orchestrator first), an unknown task id
(the known ids are listed), a human task (it never dispatches), a prompt
without the token (a producer bug, the scheduler's own refusal) or a
shared-artifact batch whose snapshot cannot be taken or kept (a repository
git cannot pin, no artifact, an earlier batch of the run not recorded yet, the
slot's evidence damaged or its bound baseline altered, the slot bound to another batch of the
run that is not recorded, another call holding the slot, a slot lock its file
system cannot take). A phase dir that is a link is refused with exit 1 before
anything is read through it or written.

The prior-changes log is the plan dir's ``prior_changes.jsonl`` — the parent
of the phase dir, where the executor leg appends — scoped to this phase as
the scheduler scopes it; the instructions' ``util prior-changes append`` step
names the same directory.

Import is side-effect free: argparse and all I/O live inside :func:`main`.
"""

from __future__ import annotations

import argparse
import errno
import hashlib
import json
import os
import re
import secrets
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from . import known_checks as _known_checks
from .clock import parse_iso
from . import process_control as _process_control
from . import prior_changes as _prior_changes
from . import prompt_files as _prompt_files
from . import review_round as _review_round
from .git_utils import (
    find_git_entry_root, pin_repo_root, worktree_file_stats, worktree_fingerprint,
)
from .metrics import (
    METRICS_TEMP_PREFIX, _read_state, mark_failed_in_progress, state_file_lock,
    withdraw_from_progress_in_state,
)
from .state_file import StateDocumentError
from .state_file import update as update_state
from .state_manager import (
    PROCESSED_LEG_NATIVE, record_batch_items_in_state, update_task_status_in_state,
)
from .stream_bootstrap import bootstrap_streams
from .task_outcome import ExecutorError, ResultRejected
from .subagent_tasks import (
    APPLY_WRITE_KINDS, PHASE_BY_WRITE_KIND, TASKS_SCHEMA_VERSION, declared_file_set,
)
from .write_batch_scheduler import SWEEP_MAX_FILES
from .commit_write_guard import (
    COMMIT_GUARD_KIND,
    batch_fixes_for,
    commit_group_files,
    commit_guard_of,
    commit_head7,
    commit_recheck_failing,
    commit_stale_line,
    commit_stale_reason,
    commit_stale_split,
    load_commit_apply,
    load_orchestrator_batches,
)
from .check_records import (
    accepted_upstream_checks,
    decomposition_graph,
    rerunnable_checks,
    upstream_held_check,
)
from .batch_prompt import (
    DISPATCHED_PROMPTS_SUBDIR,
    OWN_RUN_CONTEXT_PHASES,
    bind_prior_changes,
    dispatched_prompt_path,
    is_check_task,
    last_phase_end,
    with_result_contract,
)
from .write_phase_bridge import NATIVE_RUN_KEY, REVIEW_ROUND_KEY, WRITE_TASK_FILENAME
from .write_safety import (
    PolicyViolation, WritePolicy, policy_allow_clause, policy_outside_note,
)
from . import scope_apply as _scope
from .check_tree import check_tree_exclusions


__all__ = [
    "MARKER_REFUSED",
    "PROMPTS_SUBDIR",
    "check_tree_fingerprint",
    "commit_bind",
    "commit_stale_check",
    "policy_refusal",
    "policy_refusal_for",
    "policy_refused_hits",
    "policy_refused_paths",
    "policy_violation_for",
    "WritePromptError",
    "check_tree_path",
    "changed_since_bound",
    "discard_check_tree",
    "record_check_tree",
    "held_by_check",
    "load_write_task",
    "ordering_warnings",
    "render_write_prompt",
    "default_output_path",
    "phase_dir_pin",
    "MARKER_SNAPSHOT",
    "MARKER_ARTIFACT",
    "SNAPSHOT_ROLES",
    "BatchSnapshot",
    "snapshot_slot",
    "snapshot_copy_name",
    "snapshot_binding_name",
    "prepare_batch_snapshot",
    "superseded_round_refusal",
    "superseded_round_text",
    "round_superseded",
    "completion_stamp",
    "record_completion_stamp",
    "main",
]

#: Where the bound prompt files land, under the phase dir: the scheduler's
#: own constant, since the executor leg keeps its dispatched prompts there too.
PROMPTS_SUBDIR = DISPATCHED_PROMPTS_SUBDIR

#: The marker lines a host reads (``--stdout`` prints none of them).
MARKER_PATH = "[WRITE_PROMPT]"
MARKER_LINES = "[WRITE_PROMPT_LINES]"
MARKER_CONTEXT = "[WRITE_PROMPT_CONTEXT]"


class WritePromptError(Exception):
    """A refusal: exit 3 ("needs a human", D6) with one message."""

    exit_code = 3


def _read_document(phase_dir: Path) -> Dict[str, Any]:
    path = phase_dir / WRITE_TASK_FILENAME
    if not path.is_file():
        raise WritePromptError(
            f"No {WRITE_TASK_FILENAME} under {phase_dir}: the phase's "
            f"orchestrator writes it when it emits its batches, so run the "
            f"phase (or re-run it with --resume) before asking for a batch "
            f"prompt."
        )
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise WritePromptError(f"Cannot read {path}: {exc}") from exc
    if not isinstance(document, dict):
        raise WritePromptError(f"{path} is not a JSON object.")
    version = document.get("tasks_schema_version")
    if version != TASKS_SCHEMA_VERSION:
        raise WritePromptError(
            f"{path} carries tasks_schema_version {version!r}, not "
            f"{TASKS_SCHEMA_VERSION}: re-run the phase's orchestrator to "
            f"re-materialize it."
        )
    return document


def load_write_task(phase_dir: Path, task_id: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """``(document, task)`` for *task_id* from the phase dir's task file."""
    document = _read_document(phase_dir)
    tasks = document.get("batches") or document.get("tasks") or []
    known: List[str] = []
    for task in tasks:
        if not isinstance(task, dict):
            continue
        tid = str(task.get("task_id") or "")
        known.append(tid)
        if tid == task_id:
            return document, task
    raise WritePromptError(
        f"No task {task_id!r} in {phase_dir / WRITE_TASK_FILENAME}. Known "
        f"task ids, in dispatch order: {', '.join(known) or '(none)'}."
    )


def _phase_word(document: Dict[str, Any]) -> Optional[str]:
    phase = document.get("phase")
    if isinstance(phase, str) and phase:
        return phase
    kind = document.get("kind")
    return PHASE_BY_WRITE_KIND.get(str(kind or ""))


def render_write_prompt(
    phase_dir: Path, task_id: str
) -> Tuple[str, Dict[str, Any], Dict[str, Any]]:
    """The bound prompt text plus ``(task, info)``.

    ``info`` carries ``kind``, ``phase``, ``output_dir`` (the log's dir) and
    ``context_entries`` (how many of this phase's prior-batch entries the
    render could see). The prompt is exactly
    ``with_result_contract(kind, task, bind_prior_changes(task, …))`` — the
    executor leg's dispatch text for the same task and the same log.
    """
    phase_dir = Path(os.path.abspath(str(phase_dir)))
    document, task = load_write_task(phase_dir, task_id)
    kind = str(document.get("kind") or "")
    if kind not in PHASE_BY_WRITE_KIND:
        raise WritePromptError(
            f"{phase_dir / WRITE_TASK_FILENAME} is a {kind!r} task file, not a "
            f"write phase's (known: {', '.join(PHASE_BY_WRITE_KIND)})."
        )
    if task.get("is_human") or str(task.get("executor_role") or "") == "human":
        raise WritePromptError(
            f"Task {task_id} is a human task: it never dispatches to a "
            f"subagent, so there is no prompt to bind. Record its answer "
            f"through the phase's human-task strategy instead."
        )
    phase = _phase_word(document)
    # The log lives in the plan dir — the phase dir's parent, where the
    # executor leg's `WriteBatchScheduler` (output_dir=<plan dir>) appends.
    output_dir = str(phase_dir.parent)
    # The scope policy's stale-task check, the executor dispatch's twin: a task materialized under
    # another policy, baseline or binding than the round's effective one is
    # refused before any prompt exists. A task without scope metadata never
    # blocks an `expand` round.
    if kind in APPLY_WRITE_KINDS:
        refusal = _scope_refusal(task, output_dir, phase)
        if refusal:
            raise WritePromptError(refusal)
    try:
        bound = bind_prior_changes(
            task, output_dir=output_dir, phase=phase,
            accepted_checks=_accepted_checks(phase_dir, document, task_id),
        )
    except ResultRejected as exc:
        raise WritePromptError(str(getattr(exc, "message", exc))) from exc
    text = with_result_contract(
        kind, task, bound,
        checks_section=_known_checks_section(phase_dir, document, task_id),
    )
    scoped = _prior_changes.canonical_phase(phase)
    if scoped in OWN_RUN_CONTEXT_PHASES:
        # The entries the render bound, this run's own.
        entries = _prior_changes.run_entries(
            output_dir, phase,
            last_phase_end(
                _known_checks.read_state(output_dir), phase,
                _known_checks.review_stamp(task),
            ),
        )
    else:
        entries = [
            entry for entry in _prior_changes.entries(output_dir)
            if _prior_changes.canonical_phase(entry.get("phase")) == scoped
        ]
    info = {
        "kind": kind,
        "phase": phase,
        "output_dir": output_dir,
        "context_entries": len(entries),
    }
    return text, task, info


def _scope_refusal(task: Dict[str, Any], output_dir: str, phase: Optional[str]) -> Optional[str]:
    """``scope_apply.stale_task_refusal`` against the plan dir's ``state.json``."""
    state = _known_checks.read_state(output_dir)
    policy, baseline = _scope.effective_from_state(
        state if isinstance(state, dict) else {}, str(phase or ""))
    return _scope.stale_task_refusal(task, policy, baseline)


def _accepted_checks(
    phase_dir: Path, document: Dict[str, Any], task_id: str,
) -> List[Tuple[str, str, List[str]]]:
    """The checks upstream of an implement task whose findings the user
    accepted (``check_records.accepted_upstream_checks``), from the
    plan dir's ``state.json`` as it is now — what the executor leg reads at
    dispatch. ``[]`` for any other kind, or a state that
    cannot be read: the note is advisory and never a refusal."""
    if str(document.get("kind") or "") != "implement":
        return []
    try:
        state = json.loads((phase_dir.parent / "state.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    if not isinstance(state, dict):
        return []
    return accepted_upstream_checks(
        document.get("batches") or document.get("tasks") or [], task_id, state,
    )


def _known_checks_section(
    phase_dir: Path, document: Dict[str, Any], task_id: str,
) -> str:
    """An apply-code-fixes batch's list of the repository's known check
    commands and the earlier batches whose own check failed
    (:func:`known_checks.known_checks_section`), from the plan dir's
    ``state.json`` as it is now — what the executor leg binds at dispatch. ``""`` for
    every other kind; advisory, never a refusal."""
    if str(document.get("kind") or "") != "apply_code_fixes":
        return ""
    try:
        state = _known_checks.read_state(phase_dir.parent)
        checks = _known_checks.known_check_commands(
            phase_dir.parent, plan_file=str(document.get("plan_file") or "") or None,
            state=state,
        )
        earlier = _known_checks.earlier_batch_check_failures(
            state, document.get("batches") or document.get("tasks") or [], task_id,
        )
        return _known_checks.known_checks_section(checks, earlier)
    except Exception:  # noqa: BLE001 - advisory: the prompt is still written
        return ""


#: The warning a prompt bound out of order prints (stderr; never a refusal).
MARKER_ORDER = "[WRITE_PROMPT_ORDER]"

#: The refusal for a task a check with findings holds back (stderr, exit 3).
MARKER_BLOCKED = "[WRITE_PROMPT_BLOCKED]"

#: The refusal for a task the write policy forbids (stderr, exit 3).
MARKER_REFUSED = "[WRITE_PROMPT_REFUSED]"


def policy_refusal(phase_dir: Path, task_id: str) -> Optional[str]:
    """The executor's pre-dispatch write-policy check, for the native leg.

    ``driver.write_paths`` refuses a
    task whose declared files it does not allow before the executor starts
    a runner, and the native leg handed the same task to the host to run.
    The same check, on the same declared set (``declared_file_set``) against
    the same merged policy (``WritePolicy.load``, anchored on the task
    file's plan); the refusal's text, or ``None`` when the policy allows the
    task or cannot be read (the prompt step is never refused on a guess).
    """
    phase_dir = Path(os.path.abspath(str(phase_dir)))
    try:
        document, task = load_write_task(phase_dir, task_id)
    except Exception:  # noqa: BLE001 - never refuse on a task file that cannot be read
        return None
    return policy_refusal_for(
        task, plan_file=str(document.get("plan_file") or "") or None,
        anchor_dir=phase_dir,
    )


def policy_refused_paths(phase_dir: Path, task_id: str) -> List[str]:
    """The declared files the policy refuses for *task_id* (the
    way forward names them), or ``[]``."""
    return [str(getattr(hit, "path", hit)) for hit in policy_refused_hits(phase_dir, task_id)]


def policy_refused_hits(phase_dir: Path, task_id: str) -> List[Any]:
    """Each declared file the policy refuses for *task_id*, with its rule
    (``write_safety.PolicyHit``;: the way forward is worded
    from it), or ``[]``."""
    phase_dir = Path(os.path.abspath(str(phase_dir)))
    try:
        document, task = load_write_task(phase_dir, task_id)
    except Exception:  # noqa: BLE001 - only a wording input
        return []
    violation = policy_violation_for(
        task, plan_file=str(document.get("plan_file") or "") or None,
        anchor_dir=phase_dir,
    )
    return list(violation.hits) if violation is not None else []


def policy_violation_for(
    task: Dict[str, Any], *, plan_file: Optional[str], anchor_dir: Path,
) -> Optional[PolicyViolation]:
    """The policy check :func:`policy_refusal_for` makes, its exception kept
    (its ``hits`` word the way forward)."""
    try:
        declared = declared_file_set(task)
        if not declared:
            return None
        anchor = Path(os.path.abspath(str(anchor_dir)))
        while not anchor.exists() and anchor.parent != anchor:
            anchor = anchor.parent
        root, problem = pin_repo_root(str(anchor))
        if root is None or problem:
            return None
        policy = WritePolicy.load(root, anchor=plan_file)
        # As declared: a file outside the repository is named
        # as the task wrote it, not by its resolved absolute path.
        policy.check(declared, when="pre-dispatch")
    except PolicyViolation as exc:
        return exc
    except Exception:  # noqa: BLE001 - never refuse on a policy that cannot be read
        return None
    return None


def policy_refusal_for(
    task: Dict[str, Any], *, plan_file: Optional[str], anchor_dir: Path,
) -> Optional[str]:
    """:func:`policy_refusal` for a materialized write task in hand.

    What the native implement emit asks of every task before it hands the
    task out (a task the policy refuses is recorded failed and
    left out of the batches, as the executor refuses it before dispatch).
    *anchor_dir* is any directory inside the repository (the phase dir, or
    the plan's output folder before the phase dir exists).
    """
    violation = policy_violation_for(task, plan_file=plan_file, anchor_dir=anchor_dir)
    return violation.message if violation is not None else None


#: The pre-rename spelling.
_policy_violation_for = policy_violation_for


# ---------------------------------------------------------------------------
# The commit re-check
# ---------------------------------------------------------------------------
#
# "Every batch is re-checked immediately before it is dispatched": a batch
# can start long after the apply guard decided (after judging, the batches
# ahead of it, a stop, a `--resume`), so before this command binds the prompt
# the host is about to hand a subagent, every fix file the batch declares is
# held to the content the guard saved for it — the executor's
# `CommitGuardLeg.recheck`, through the same shared helpers. A
# batch that fails gets no prompt: `[COMMIT_FIXES_STALE]` is printed in place
# of `[WRITE_PROMPT]`, its outcome is recorded in `state.json` with the keys
# `util batch-done` writes, and the host goes on to the next batch. No-op
# without a guard (the state's pinned record carries none).


def commit_stale_check(phase_dir: Path, task_id: str) -> Optional[List[str]]:
    """The lines to print in place of the prompt markers when *task_id*
    fails the commit re-check, after recording it; ``None`` when it passes,
    when there is no guard, or when the task file, the state or the
    repository cannot be read (the render then reports those as before).

    The batch's fix files are every file its groups' fixes name in the
    phase's ``orchestrator_output.json`` (their ``files``), beside its
    primary file. On a failure the groups that name a failing file are
    skipped (``commit_apply.mark_stale``, saved back with
    ``commit_apply.save_guard`` under ``state_file_lock``), the batch is
    recorded ``failed`` with ``held back: batched with <file>`` when other
    groups remain (else with the skip itself) and its items ``failed`` in
    ``processed_<phase>``, as the executor records them, and it leaves the
    run's ``[ETA]`` total as a task refused before dispatch does.
    """
    phase_dir = Path(os.path.abspath(str(phase_dir)))
    try:
        document, task = load_write_task(phase_dir, task_id)
    except Exception:  # noqa: BLE001 - the render names the problem
        return None
    kind = str(document.get("kind") or "")
    if kind != COMMIT_GUARD_KIND:
        return None
    if task.get("is_human") or str(task.get("executor_role") or "") == "human":
        return None
    target = phase_dir.parent / "state.json"
    try:
        state = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    guard = commit_guard_of(state, kind)
    if guard is None:
        return None
    try:
        root, problem = pin_repo_root(str(phase_dir))
    except Exception:  # noqa: BLE001 - never refuse on a guess
        return None
    if root is None or problem:
        return None
    commit_apply = load_commit_apply()
    groups = commit_group_files(
        task, repo_root=root,
        fixes=batch_fixes_for(task, load_orchestrator_batches(phase_dir)),
    )
    failing = commit_recheck_failing(guard, groups, repo_root=root, commit_apply=commit_apply)
    if not failing:
        return None
    skipped, held = commit_stale_split(groups, failing)
    reason = commit_stale_reason(failing, guard, held=bool(held))
    phase = PHASE_BY_WRITE_KIND.get(kind, kind)
    # One state lock across the guard's save and the batch's record.
    with state_file_lock(target):
        try:
            state = _read_state(target)
        except StateDocumentError:
            return None
        guard = commit_guard_of(state, kind)
        if guard is None:
            return None
        commit_apply.mark_stale(guard, groups, failing, cwd=root)
        commit_apply.save_guard(target, guard)
        # What save_guard wrote, then this batch's record over it.
        with update_state(target, temp_prefix=METRICS_TEMP_PREFIX) as state:
            update_task_status_in_state(state, task_id, "failed", reason)
            # Every item `failed`, as `util batch-done --status failed`
            # records them: a native `--resume` hands them out again, and the
            # guard's saved skips take the skipped ones out (and count them)
            # there.
            record_batch_items_in_state(
                state, phase_dir.name, task, completed=False, leg=PROCESSED_LEG_NATIVE,
            )
            # No subagent ran: out of the `[ETA]` total, never "run stopped".
            mark_failed_in_progress(state, phase, task_id, failed=False)
            withdraw_from_progress_in_state(state, phase, [task_id], task_id)
            # Any earlier record of this batch's own check no longer stands.
            _known_checks.set_batch_check_report_in_state(
                state, task_id,
                prior_changes_id=str(task.get("prior_changes_id") or ""),
                grouped_sha256=_known_checks.review_stamp(task),
                findings=None, listed=None, note=None,
            )
            state["updated_at"] = datetime.now().isoformat()
    line = commit_stale_line(
        task_id, failing, guard,
        marker=getattr(commit_apply, "STALE_MARKER", "[COMMIT_FIXES_STALE]"),
    )
    what = [f"{len(skipped)} fix(es) skipped"] if skipped else []
    if held:
        what.append(
            f"{len(held)} held back for a --resume, which applies "
            f"{'it' if len(held) == 1 else 'them'} in a new batch"
        )
    return [
        f"{line} — not dispatched, and already recorded ({', '.join(what)}): "
        f"write no prompt, hand {task_id} to no subagent, record nothing for "
        f"it, and go on to the next batch. List the skipped fixes in the "
        f"phase's summary.md as skipped, file changed since reviewed commit "
        f"{commit_head7(guard)}."
    ]


def commit_bind(phase_dir: Path, task_id: str) -> bool:
    """Record the watched set's disk ids as *task_id*'s prompt is bound,
    so its ``util batch-done`` counts only a change made while the batch ran:
    ``commit_apply.bind_watched``, saved in the guard under
    ``state_file_lock``. The executor reads the same ids just before it
    dispatches a batch (``CommitGuardLeg.watch_begin``); here
    the bind is the last moment before the host hands the prompt over.

    True when recorded. Without a guard, for another kind, a human task, or
    a state or repository that cannot be read, nothing is written and
    ``util batch-done`` compares with the ids the guard saved, as before.
    Never raises."""
    phase_dir = Path(os.path.abspath(str(phase_dir)))
    try:
        document, task = load_write_task(phase_dir, task_id)
        kind = str(document.get("kind") or "")
        if kind != COMMIT_GUARD_KIND:
            return False
        if task.get("is_human") or str(task.get("executor_role") or "") == "human":
            return False
        target = phase_dir.parent / "state.json"
        if commit_guard_of(json.loads(target.read_text(encoding="utf-8")), kind) is None:
            return False
        root, problem = pin_repo_root(str(phase_dir))
        if root is None or problem:
            return False
        commit_apply = load_commit_apply()
        with update_state(target, temp_prefix=METRICS_TEMP_PREFIX) as state:
            guard = commit_guard_of(state, kind)
            # Nothing watched: the saved ids (none) are the same comparison.
            if guard is None or not commit_apply.watched_ids(guard):
                return False
            commit_apply.bind_watched(guard, task_id, cwd=root)
        return True
    except Exception:  # noqa: BLE001 - batch-done then compares with the saved ids
        return False


def held_by_check(phase_dir: Path, task_id: str) -> Optional[Tuple[str, List[str]]]:
    """``(check id, its findings)`` when a check with findings holds *task_id*.

    On the native leg the host dispatches each task itself, so
    the plugin's hold on the tasks that depend on a check that reported
    problems (the executor leg's ``CheckHolds.block_dependents_of_checks``)
    is enforced here, where the host gets each task's prompt. The held
    checks are ``state.json``'s (``check_records.rerunnable_checks``:
    findings on record, recorded completed, not accepted with
    ``--human-task <id>=done``); the graph is ``write_tasks.json``'s
    ``depends_on`` plus ``state.json``'s recorded decomposition
    (``check_records.decomposition_graph``: a
    ``--resume`` leaves a finished task out of the file, and a chain through
    it used to end there). ``None`` for an implement task nothing holds, any other
    kind, or a state or task file that cannot be read (the prompt step is
    never refused on a guess).
    """
    phase_dir = Path(os.path.abspath(str(phase_dir)))
    try:
        document, _task = load_write_task(phase_dir, task_id)
        if str(document.get("kind") or "") != "implement":
            return None
        state = json.loads((phase_dir.parent / "state.json").read_text(encoding="utf-8"))
    except (WritePromptError, OSError, ValueError):
        return None
    if not isinstance(state, dict):
        return None
    tasks = decomposition_graph(
        document.get("batches") or document.get("tasks") or [], state,
    )
    check_id = upstream_held_check(tasks, task_id, rerunnable_checks(state))
    if check_id is None:
        return None
    findings = (state.get("task_check_findings") or {}).get(check_id) or []
    return check_id, [str(item) for item in findings]


def ordering_warnings(phase_dir: Path, task_id: str) -> List[str]:
    """What this prompt is missing because an earlier batch is not logged yet.

    The host
    recorded batch 0 with ``util batch-done``, bound batch 1's prompt, and
    only then appended batch 0's summary — so batch 1's prompt went out
    without it, and the host had to notice, re-bind batch 1 and re-bind
    batch 2. For every task of an EARLIER batch in ``write_tasks.json``
    (same-batch siblings may legitimately run together) whose
    ``prior_changes_id`` this phase's log does not hold yet, one line: it is
    recorded finished but not appended (the case above), or it has no record
    at all. A task recorded ``skipped`` and a human task are never in the
    log and are passed over. Advisory only — the prompt is still written,
    so a ``--resume`` (whose document holds only the unfinished tasks) and a
    host skipping a failed task's dependents are never refused. Nothing is
    said when the plan dir has no ``state.json`` or either file is
    unreadable.
    """
    phase_dir = Path(os.path.abspath(str(phase_dir)))
    try:
        document, task = load_write_task(phase_dir, task_id)
        state = json.loads((phase_dir.parent / "state.json").read_text(encoding="utf-8"))
        own_index = int(task.get("batch_index"))
    except (WritePromptError, OSError, ValueError, TypeError):
        return []
    if not isinstance(state, dict):
        return []
    statuses = state.get("task_status") or {}
    phase = _phase_word(document)
    scoped = _prior_changes.canonical_phase(phase)
    # A phase whose prompts carry only this run's batches
    # counts only this run's entries as logged, as the render binds them.
    logged = {
        str(entry.get("id") or "")
        for entry in (
            _prior_changes.run_entries(
                str(phase_dir.parent), phase,
                last_phase_end(state, phase, _known_checks.review_stamp(task)))
            if scoped in OWN_RUN_CONTEXT_PHASES
            else _prior_changes.entries(str(phase_dir.parent))
        )
        if _prior_changes.canonical_phase(entry.get("phase")) == scoped
    }
    lines: List[str] = []
    for earlier in document.get("batches") or document.get("tasks") or []:
        if not isinstance(earlier, dict):
            continue
        try:
            index = int(earlier.get("batch_index"))
        except (TypeError, ValueError):
            continue
        if index >= own_index:
            continue
        if earlier.get("is_human") or str(earlier.get("executor_role") or "") == "human":
            continue
        earlier_id = str(earlier.get("task_id") or "")
        entry_id = str(earlier.get("prior_changes_id") or "")
        status = statuses.get(earlier_id)
        if not entry_id or entry_id in logged or status == "skipped":
            continue
        if status in ("completed", "failed"):
            lines.append(
                f"{MARKER_ORDER} {earlier_id} is recorded {status}, but its "
                f"summary is not in the prior-changes log yet, so this prompt "
                f"does not carry it. Run its `util prior-changes append` "
                f"(--id {entry_id}), then run this `util write-prompt` again."
            )
        else:
            lines.append(
                f"{MARKER_ORDER} {earlier_id}, an earlier batch, has no "
                f"`util batch-done` record and no prior-changes entry yet, so "
                f"this prompt does not carry it. If it has not finished, finish, "
                f"record and append it first, then run this `util write-prompt` "
                f"again."
            )
    return lines


def default_output_path(phase_dir: Path, task_id: str) -> Path:
    """``{phase_dir}/prompts/{task_id}.prompt.txt``, the file the executor leg
    keeps for the same task (:func:`dispatched_prompt_path`). The path to
    print; the file is written through :func:`phase_dir_pin`."""
    return Path(dispatched_prompt_path(str(phase_dir), task_id))


def phase_dir_pin(phase_dir: Path, *, identity: bool = True) -> "_prompt_files.PhasePin":
    """Where this command writes under the phase dir, without following a link.

    The host's subagents can write the phase dir, and this
    command wrote ``prompts/<id>.prompt.txt`` by path — through a ``prompts``
    link, a link planted at the file's own name (which overwrote the file it
    named), or a phase dir replaced by one. The walk starts at the repository
    holding the phase dir's parent (that parent itself when no repository
    does) and opens every component below it, the phase dir included,
    without following a link (:mod:`utils.prompt_files`). With ``identity``
    the phase dir it reaches now is pinned, so a write later in the same
    call reaches the same directory or is refused. Raises ``OSError``.
    """
    given = os.path.abspath(str(phase_dir))
    parent = os.path.realpath(os.path.dirname(given))
    root = find_git_entry_root(parent) or parent
    relative = os.path.relpath(parent, root)
    parts = tuple(
        part for part in relative.split(os.sep) if part and part != os.curdir
    ) + (os.path.basename(given),)
    pin = _prompt_files.PhasePin(root=root, parts=parts)
    return _prompt_files.identify(pin) if identity else pin


# ---------------------------------------------------------------------------
# The check guard
# ---------------------------------------------------------------------------
#
# A check task declares no files: it promised to change nothing. On the
# executor leg the post-run sweep holds it to that (any path it moved is a
# partial application); on the native leg the host records it, and `util
# batch-done --status completed --check findings` verified nothing about the
# tree, so a host following a `failed` reply that listed findings after its
# subagent edited a file recorded check-findings and the edit rode along. The
# guard: `util write-prompt` records the files git sees (size and mtime, the
# plugin's own trees left out) when it binds a check's prompt, and `util
# batch-done` refuses to record that check `completed` while a file changed
# since then that no other task of the phase declares (a task running beside
# it may change its own files). One record verifies one dispatch: any record
# of the check consumes it.

#: The suffix of a check's bind-time tree record, beside its prompt file.
TREE_RECORD_SUFFIX = ".tree.json"


def check_tree_path(phase_dir: Path, task_id: str) -> Path:
    """``{phase_dir}/prompts/{task_id}.tree.json``."""
    return default_output_path(phase_dir, task_id).with_name(
        f"{task_id}{TREE_RECORD_SUFFIX}"
    )


def _tree_exclusions(phase_dir: Path, repo_root: str) -> List[str]:
    """The precise workflow-artifact exclusions shared with the executor."""

    return check_tree_exclusions(phase_dir, repo_root)


def _tree_now(phase_dir: Path) -> Optional[Tuple[str, Dict[str, List[int]]]]:
    """``(repo root, path -> [size, mtime_ns])``, or ``None`` when the
    repository cannot be pinned or read, or holds more files than the
    executor's sweep looks at (:data:`SWEEP_MAX_FILES`)."""
    phase_dir = Path(os.path.abspath(str(phase_dir)))
    try:
        root, problem = pin_repo_root(str(phase_dir))
    except Exception:  # noqa: BLE001 - the guard is never a crash
        return None
    if root is None or problem:
        return None
    stats = worktree_file_stats(root, exclude_prefixes=_tree_exclusions(phase_dir, root))
    if stats is None or len(stats) > SWEEP_MAX_FILES:
        return None
    return root, {path: [size, mtime] for path, (size, mtime) in stats.items()}


def check_tree_fingerprint(phase_dir: Path) -> Optional[str]:
    """One digest of the files git sees, the plugin's own trees left out.

    ``git_utils.worktree_fingerprint`` with the exclusions the executor's
    ``CheckHolds.tree_fingerprint`` uses (workflow artifacts and
    ``.multi-llm/``, keeping colocated code), so both legs mean the same thing by "the
    files changed". The native leg stamps it on a check with findings
    (``util batch-done``, re-stamped by ``util finalize-tracking`` with the
    tree the run left) and compares it on ``--resume`` before handing the
    check out again. ``None`` when the repository cannot be
    pinned or read: a caller then runs the check again rather than guess.
    """
    anchor = Path(os.path.abspath(str(phase_dir)))
    while not anchor.exists() and anchor.parent != anchor:
        anchor = anchor.parent
    try:
        root, problem = pin_repo_root(str(anchor))
    except Exception:  # noqa: BLE001 - the guard is never a crash
        return None
    if root is None or problem:
        return None
    try:
        return worktree_fingerprint(
            root,
            exclude_prefixes=_tree_exclusions(
                Path(os.path.abspath(str(phase_dir))), root,
            ),
        )
    except Exception:  # noqa: BLE001 - advisory
        return None


def record_check_tree(
    phase_dir: Path, task_id: str,
    pin: Optional["_prompt_files.PhasePin"] = None,
) -> Optional[Path]:
    """Record the tree a check task's prompt is bound against; the path, or
    ``None`` when the tree cannot be read (an earlier record is removed then,
    so it never verifies this dispatch). Written like the prompt, never
    through a link (:func:`phase_dir_pin`, or the caller's ``pin``)."""
    target = check_tree_path(phase_dir, task_id)
    taken = _tree_now(phase_dir)
    if taken is None:
        discard_check_tree(phase_dir, task_id, pin)
        return None
    root, files = taken
    try:
        with _prompt_files.PromptFolder.open(
            pin or phase_dir_pin(phase_dir, identity=False)
        ) as folder:
            folder.write(target.name, json.dumps({
                "task_id": task_id, "repo_root": root, "files": files,
            }))
    except OSError:
        discard_check_tree(phase_dir, task_id, pin)
        return None
    return target


def discard_check_tree(
    phase_dir: Path, task_id: str,
    pin: Optional["_prompt_files.PhasePin"] = None,
) -> None:
    """Remove a check's bind-time record (a record of the check consumed it):
    the entry itself, never a file a link names or one reached through a
    linked folder."""
    try:
        with _prompt_files.PromptFolder.open(
            pin or phase_dir_pin(phase_dir, identity=False), create=False,
        ) as folder:
            folder.remove(check_tree_path(phase_dir, task_id).name)
    except OSError:
        pass


def _repo_relative(path: str, repo_root: str) -> str:
    text = str(path).strip().replace(os.sep, "/")
    if os.path.isabs(text):
        try:
            text = os.path.relpath(text, repo_root).replace(os.sep, "/")
        except ValueError:  # pragma: no cover - another drive on Windows
            return text
    while text.startswith("./"):
        text = text[2:]
    return text


def changed_since_bound(
    phase_dir: Path, task_id: str, tasks: List[Dict[str, Any]],
) -> Optional[List[str]]:
    """The files that changed since *task_id*'s prompt was bound and that no
    other task of *tasks* declares, sorted; ``None`` when there is no record
    to compare (the prompt was not bound through ``util write-prompt``, or
    the tree could not be read then or now): the guard never refuses on a
    guess."""
    record_path = check_tree_path(phase_dir, task_id)
    try:
        record = json.loads(record_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(record, dict) or not isinstance(record.get("files"), dict):
        return None
    taken = _tree_now(phase_dir)
    if taken is None or taken[0] != record.get("repo_root"):
        return None
    root, after = taken
    before = record["files"]
    others = {
        _repo_relative(path, root)
        for task in tasks if isinstance(task, dict)
        and str(task.get("task_id") or "") != task_id
        for path in declared_file_set(task)
    }
    return sorted(
        path for path in set(before) | set(after)
        if before.get(path) != after.get(path) and path not in others
    )


# ---------------------------------------------------------------------------
# The pre-batch snapshot of a shared-artifact batch
# ---------------------------------------------------------------------------
#
# On the native leg the host verifies an apply-suggestions or
# apply-task-suggestions batch by a byte diff of its one artifact (the plan,
# the tasks file) against a copy taken before the subagent ran: the artifact
# is often untracked, and git's diffs ignore untracked files. This command
# takes that copy as it binds the prompt. The copy serves that diff and a
# human who puts the file back by hand; it lies in the repository, which the
# batch's subagent can write, so its checksums catch an accidental change and
# prove nothing against a subagent (no command restores from it). The rules,
# docs/development/write-safety.md:
#
# * One slot per phase dir and artifact, `<slot>` =
#   `batch_snapshot_<plan|tasks>_<plan stem>-<key>` in `<repo root>/.multi-llm/tmp`,
#   the root taken from the pin, never found again through the phase path; for a
#   phase dir no repository holds, in its own `snapshots/` folder, reached
#   through the pin like `prompts/`, whatever the working directory.
# * A generation is a copy `<slot>.<sha12>.md` and the binding
#   `<slot>.binding.json` naming it. The binding is renamed into place last:
#   it is the commit point, and the previous generation's copy goes only after.
# * Every call that reads, checks, takes or publishes a slot holds `<slot>.lock`;
#   a lock the file system cannot take at all is refused as such, never
#   reported as another call holding it.
# * The binding names one batch of one run (the sha256 of `write_tasks.json`)
#   and carries a random generation id. The same batch bound again keeps it;
#   another batch of the run replaces it only once the bound batch has a
#   `util batch-done` record carrying that generation; a new emit of the phase
#   replaces it. A binding with any field missing or malformed, a binding or
#   copy that cannot be read, and copies no binding names are refused, never
#   read as a new slot.
# * A batch is bound only once every earlier batch of its run has a record
#   carrying the run, so two batches never wait on each other.
# * Records are told apart by these identities, which `util batch-done` keeps
#   beside the batch's status (:func:`completion_stamp`), never by comparing
#   clock times.

#: The marker lines naming the snapshot and the file it copies.
MARKER_SNAPSHOT = "[WRITE_SNAPSHOT]"
MARKER_ARTIFACT = "[WRITE_ARTIFACT]"

#: The word in each shared-artifact kind's snapshot name.
SNAPSHOT_ROLES = {"apply_suggestions": "plan", "apply_task_suggestions": "tasks"}

#: The self-ignoring workspace temp dir, under the repository root.
WORKSPACE_TMP = (".multi-llm", "tmp")

#: The folder of a phase dir no repository holds where its slots live.
PHASE_SNAPSHOTS = "snapshots"

#: The binding's and the lock's names beside a slot's copies.
SNAPSHOT_BINDING_SUFFIX = ".binding.json"
SNAPSHOT_LOCK_SUFFIX = ".lock"
SNAPSHOT_BINDING_VERSION = 3

#: How long a call waits for another call holding the slot's lock (seconds).
SNAPSHOT_LOCK_TIMEOUT_S = 10.0

#: The binding keys that say which batch a baseline belongs to.
BINDING_IDENTITY = (
    "task_id", "run", "phase_dir", "phase_identity", "artifact", "expected_ids",
)

#: The task statuses that record a finished batch.
_RECORDED_STATUSES = ("completed", "failed", "skipped")

#: Hex digits of the slot key and of a copy's generation in its name.
_NAME_HEX = 12

#: Hex digits of a binding's ``generation`` id.
_GENERATION_HEX = 32

#: Where ``util batch-done`` keeps a shared-artifact batch's
#: :func:`completion_stamp` in ``state.json``:
#: ``{<phase dir word>: {<task id>: {run, snapshot_generation}}}``.
SNAPSHOT_RECORDS_KEY = "batch_snapshot_records"
RECORD_RUN_KEY = "run"
RECORD_GENERATION_KEY = "snapshot_generation"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def snapshot_slot(kind: str, plan_stem: str, phase_dir: str, artifact: str) -> str:
    """``batch_snapshot_<plan|tasks>_<plan stem>-<key>``, *key* the first hex
    digits of the sha256 of the pinned phase dir and the artifact's absolute
    path: two plans of one name in different folders never share a slot."""
    key = _sha256(f"{phase_dir}\0{artifact}".encode("utf-8", "surrogateescape"))
    return f"batch_snapshot_{SNAPSHOT_ROLES[kind]}_{plan_stem}-{key[:_NAME_HEX]}"


def snapshot_copy_name(slot: str, sha256: str) -> str:
    """``<slot>.<sha12>.md``: one generation's copy."""
    return f"{slot}.{sha256[:_NAME_HEX]}.md"


def snapshot_binding_name(slot: str) -> str:
    """``<slot>.binding.json``: the generation's commit point."""
    return slot + SNAPSHOT_BINDING_SUFFIX


def _plan_stem(phase_dir: Path, kind: str, artifact: Path) -> str:
    """The plan file's name without its extension: the artifact's own for
    apply-suggestions (the plan is its artifact), else the plan ``state.json``
    records, else the plan's output folder (named after the plan)."""
    if kind == "apply_suggestions":
        return artifact.stem
    plan = _known_checks.read_state(phase_dir.parent).get("plan_path")
    if isinstance(plan, str) and plan.strip():
        return Path(plan).stem
    return phase_dir.parent.name


#: The review phase dirs whose verdicts the apply phases' batches carry.
_REVIEW_DIRS = ("review-plan", "review-tasks", "code-review")


def superseded_round_text(
    task_id: str, review: str, recorded: str, current: Optional[str], *,
    native: bool = True,
) -> str:
    """The refusal of *task_id*, whose verdicts came from review round
    *recorded* while *review*'s checkpoint records *current*: the native
    loop's (:func:`superseded_round_refusal`) and, without *native*, the
    executor's before each batch (``SchedulerOptions.before_batch``)."""
    stop = (
        f" Do not dispatch {task_id} and record nothing for it; stop the loop "
        f"here and close the phase without --mark-completed." if native else ""
    )
    return (
        f"{task_id} is not handed out: this phase's batches were built from the "
        f"verdicts of review round {recorded}, and {review}'s .status.json now "
        f"records another round, {current}: a later run of the review started "
        f"it. The batch would apply a review the phase has since replaced.{stop} "
        f"Way forward: once that round is complete (`status`; if it stopped, run "
        f"the review again with --force), run this phase again, which builds its "
        f"batches from that round's verdicts. Nothing was written for {task_id}."
    )


def round_superseded(review_dir: Path, recorded: Optional[str]) -> Optional[str]:
    """The round *review_dir*'s checkpoint records now, when it is another
    than *recorded*; ``None`` when it is the same, or either has no id (which
    proves nothing, as before round ids)."""
    current = _review_round.current_round(review_dir)
    if _review_round.ownership(current, recorded) != _review_round.STALE:
        return None
    return current


def superseded_round_refusal(pin: "_prompt_files.PhasePin", task_id: str) -> Optional[str]:
    """Why *task_id* is not handed out because its verdicts' review round was
    superseded, or ``None``.

    A native apply emit records the review round its verdicts came from in
    ``write_tasks.json`` (``native_run.review_round``). Once that review's
    ``.status.json`` records another round (a later run of the review started
    it), the batches would apply a review the phase has since replaced. A
    file or checkpoint with no round id proves nothing, as before round ids
    (docs/development/review-results.md, "Round identity"). Whatever cannot
    be read here is left to the render, which names it."""
    try:
        document = json.loads(_prompt_files.read_in_phase_dir(pin, WRITE_TASK_FILENAME))
    except (OSError, ValueError):
        return None
    run = document.get(NATIVE_RUN_KEY) if isinstance(document, dict) else None
    entry = run.get(REVIEW_ROUND_KEY) if isinstance(run, dict) else None
    if not isinstance(entry, dict):
        return None
    review, recorded = entry.get("review"), _review_round.valid_round(entry.get("round_id"))
    if review not in _REVIEW_DIRS or recorded is None:
        return None
    current = round_superseded(Path(pin.path).parent / str(review), recorded)
    if current is None:
        return None
    return superseded_round_text(task_id, str(review), recorded, current)


@dataclass(frozen=True)
class _SlotHome:
    """Where a slot's copies, binding and lock live: the folder *folder* below
    the pinned directory *pin*, reached without following a link. *root* is
    what the binding records and a relative declaration is read against;
    *workspace* marks the repository's self-ignoring workspace temp dir."""

    pin: "_prompt_files.PhasePin"
    folder: str
    root: str
    workspace: bool

    @property
    def path(self) -> str:
        return os.path.join(self.pin.path, self.folder)

    def open(self, *, create: bool) -> "_prompt_files.PromptFolder":
        """The folder, created (the workspace temp dir self-ignoring) when
        *create*. Raises ``OSError`` when a component is a link or a file, or
        (*create* off) when it does not exist."""
        if self.workspace and create:
            try:
                os.mkdir(self.pin.path)
            except FileExistsError:
                pass  # a link there is refused by the walk below
        folder = _prompt_files.PromptFolder.open(self.pin, create=create, folder=self.folder)
        if self.workspace and create:
            try:
                if ".gitignore" not in folder.names():
                    folder.write(".gitignore", "*\n")
            except BaseException:
                folder.close()
                raise
        return folder


def _snapshot_home(pin: "_prompt_files.PhasePin", task_id: str) -> _SlotHome:
    """Where the pinned phase dir's slots live. In a repository: its root's
    ``.multi-llm/tmp``, the root taken from the pin, where ``pin_repo_root``
    must agree with it (refused otherwise, as a git redirect or a disagreeing
    ``core.worktree`` is). In no repository: the phase dir's own
    :data:`PHASE_SNAPSHOTS` folder, fixed by the pin, so every bind, record
    and resume of the run reaches the one slot and one lock from any working
    directory (docs/development/write-safety.md, "The native leg's per-batch
    snapshot")."""
    if find_git_entry_root(pin.root) is None:
        return _SlotHome(pin, PHASE_SNAPSHOTS, pin.root, workspace=False)
    root, problem = pin_repo_root(pin.root)
    if problem or root is None or os.path.realpath(root) != os.path.realpath(pin.root):
        raise WritePromptError(
            f"Cannot take {task_id}'s pre-batch snapshot: "
            f"{problem or f'{pin.path} now lies in the repository {root}, not where it was pinned ({pin.root})'}. "
            f"{task_id} was not handed out."
        )
    return _SlotHome(
        _prompt_files.PhasePin(root=root, parts=WORKSPACE_TMP[:1]), WORKSPACE_TMP[1],
        root, workspace=True,
    )


def _read_run(pin: "_prompt_files.PhasePin") -> Tuple[str, Dict[str, Any]]:
    """``(run, document)``: the pinned phase dir's ``write_tasks.json``, read
    without following a link (``OSError`` for a phase dir swapped since), and
    its sha256 — the run its batches belong to, since only the phase's emit
    writes it (a native emit stamps its time)."""
    raw = _prompt_files.read_in_phase_dir(pin, WRITE_TASK_FILENAME)
    try:
        document = json.loads(raw)
    except ValueError as exc:
        raise WritePromptError(
            f"{Path(pin.path) / WRITE_TASK_FILENAME} is not JSON ({exc})") from exc
    if not isinstance(document, dict):
        raise WritePromptError(
            f"{Path(pin.path) / WRITE_TASK_FILENAME} is not a JSON object")
    return _sha256(raw), document


def _read_plan_state(phase_dir: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """``(state, None)``: the plan dir's ``state.json``; ``(None, why)`` when
    it is missing, unreadable or not an object — evidence that cannot say
    whether a batch was recorded, never read as "nothing recorded"."""
    path = Path(phase_dir).parent / "state.json"
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None, f"{path} does not exist"
    except (OSError, ValueError) as exc:
        return None, f"{path} cannot be read ({exc})"
    if not isinstance(state, dict) or not isinstance(state.get("task_status", {}), dict):
        return None, f"{path} is not a state file (no task_status object)"
    return state, None


def _parse_stamp(value: Any) -> Optional[datetime]:
    try:
        return parse_iso(str(value))
    except (TypeError, ValueError):
        return None


def _recorded_with(
    state: Dict[str, Any], phase_word: str, task_id: str, key: str, value: str,
) -> bool:
    """Whether ``state.json`` holds *task_id*'s ``util batch-done`` record
    stamped ``key == value``: a recorded ``task_status`` and, written beside
    it in the same locked write, the :func:`completion_stamp` under
    :data:`SNAPSHOT_RECORDS_KEY`. ``task_status`` is one map for every run
    of the phase, and a ``--resume`` numbers its batches afresh, so a status
    alone can be an earlier run's; the stamp is an identity, so a clock set
    back or forward cannot hide a record or pass an old one off."""
    if (state.get("task_status") or {}).get(task_id) not in _RECORDED_STATUSES:
        return False
    entry = _stamp_of(state, phase_word, task_id)
    return entry is not None and entry.get(key) == value


def _stamp_of(
    state: Dict[str, Any], phase_word: str, task_id: str,
) -> Optional[Dict[str, Any]]:
    """*task_id*'s :func:`completion_stamp` as ``state.json`` keeps it under
    :data:`SNAPSHOT_RECORDS_KEY`, or ``None`` when there is none."""
    records = state.get(SNAPSHOT_RECORDS_KEY)
    phase = records.get(phase_word) if isinstance(records, dict) else None
    entry = phase.get(task_id) if isinstance(phase, dict) else None
    return entry if isinstance(entry, dict) else None


def _batch_index(task: Dict[str, Any]) -> Optional[int]:
    try:
        return int(task.get("batch_index"))
    except (TypeError, ValueError):
        return None


def _order_refusal(
    pin: "_prompt_files.PhasePin", document: Dict[str, Any], task: Dict[str, Any],
    task_id: str, run: str, bound_in_run: Callable[[str], bool],
) -> Optional[str]:
    """Why *task_id* cannot be bound before an earlier batch of its run, or
    ``None``. The batches of a shared-artifact phase edit one file one at a
    time, in order, and the slot holds one baseline: a later batch bound
    first would wait for the earlier one while the earlier one waited for it.
    An earlier batch counts once its record carries *run*, the sha256 of the
    ``write_tasks.json`` it was made under.

    A recorded status with no stamp at all was made by a plugin version that
    kept none, for a loop begun before the upgrade or for an earlier run.
    Which one cannot be told, so that refusal names both ways forward,
    ``--resume`` among them, unless the slot's binding names that batch of
    this run (*bound_in_run*): this version bound it, so a record of it made
    since would carry a stamp, and the general refusal applies."""
    own = _batch_index(task)
    if own is None:
        return None
    earlier = []
    for batch in document.get("batches") or document.get("tasks") or []:
        if not isinstance(batch, dict) or batch.get("is_human"):
            continue
        if str(batch.get("executor_role") or "") == "human":
            continue
        index = _batch_index(batch)
        if index is not None and index < own:
            earlier.append(batch)
    if not earlier:
        return None
    ids = [str(batch.get("task_id") or "") for batch in earlier]
    state, problem = _read_plan_state(pin.path)
    if state is None:
        return (
            f"{task_id} cannot be bound: whether the batches before it "
            f"({', '.join(ids)}) have their `util batch-done` records cannot be "
            f"told, because {problem}. Nothing was written and {task_id} was not "
            f"handed out. Put state.json back, or re-run the phase's "
            f"orchestrator with --resume, then run this command again."
        )
    phase_word = Path(pin.path).name
    for batch_id in ids:
        if not _recorded_with(state, phase_word, batch_id, RECORD_RUN_KEY, run):
            status = (state.get("task_status") or {}).get(batch_id)
            if (status in _RECORDED_STATUSES
                    and _stamp_of(state, phase_word, batch_id) is None
                    and not bound_in_run(batch_id)):
                return (
                    f"{task_id} cannot be bound yet: {batch_id}, an earlier "
                    f"batch, is recorded {status} in state.json, but its record "
                    f"carries no run stamp ({SNAPSHOT_RECORDS_KEY}): a plugin "
                    f"version that kept none made it, so nothing says it is "
                    f"this run's record and not an earlier run's (a --resume "
                    f"numbers its batches afresh). If this loop has not run "
                    f"{batch_id}, run it first — bind it with this command, "
                    f"then the loop's steps for it. If it has (the loop began "
                    f"before the upgrade), or that cannot be told, re-run the "
                    f"phase's orchestrator with --resume: it skips every item "
                    f"already recorded and emits the rest as a new run; then "
                    f"continue the loop with that run's first batch. Nothing "
                    f"was written and {task_id} was not handed out."
                )
            return (
                f"{task_id} cannot be bound yet: {batch_id}, an earlier batch of "
                f"this run, has no `util batch-done` record from this run. The "
                f"batches run one at a time, in order, and {task_id}'s pre-batch "
                f"snapshot would take the place of the one {batch_id} is checked "
                f"against. Run {batch_id} first — bind it with this command, then "
                f"the loop's steps for it — or, if it already ran, verify it and "
                f"record it with util batch-done; then run this command again. "
                f"Nothing was written and {task_id} was not handed out."
            )
    return None


def _slot_bound_to(
    home: _SlotHome, slot: str, identity: Dict[str, Any], batch_id: str, run: str,
) -> bool:
    """Whether *slot*'s binding names *batch_id* of *run*. Read without the
    slot's lock, as :func:`completion_stamp` reads it: a binding is only ever
    replaced whole. ``False`` for anything that cannot be read."""
    try:
        folder = home.open(create=False)
    except OSError:
        return False
    try:
        bound = _read_slot(folder, slot, identity).binding
    except OSError:
        bound = None
    finally:
        folder.close()
    return bound is not None and bound["task_id"] == batch_id and bound["run"] == run


@dataclass
class _SlotNow:
    """A slot as it is on disk: its binding (``None`` when there is none or
    it is damaged), the bytes of the copy the binding names (``None`` when
    that copy is gone or unreadable), every copy of the slot, and why the
    binding cannot be used."""

    binding: Optional[Dict[str, Any]]
    held: Optional[bytes]
    copies: List[str]
    damage: Optional[str]


def _is_hex(value: Any, length: int) -> bool:
    return (isinstance(value, str) and len(value) == length
            and not value.strip("0123456789abcdef"))


def _binding_problem(binding: Any, slot: str, identity: Dict[str, Any]) -> Optional[str]:
    """Why *binding* is not one this command wrote for *slot*, or ``None``.
    Every field the transitions read is checked for presence and shape
    first: a binding missing one is damaged evidence, never another run's."""
    if not isinstance(binding, dict):
        return "is not a JSON object"
    if binding.get("version") != SNAPSHOT_BINDING_VERSION:
        return f"is not a version {SNAPSHOT_BINDING_VERSION} binding"
    for key in ("task_id", "phase_dir", "artifact", "copy", "taken_at"):
        if not isinstance(binding.get(key), str) or not binding[key]:
            return f"has no {key}"
    for key, length in (("run", 64), ("sha256", 64), ("generation", _GENERATION_HEX)):
        if not _is_hex(binding.get(key), length):
            return f"has no {key}"
    ids = binding.get("expected_ids")
    if not isinstance(ids, list) or not all(isinstance(item, str) for item in ids):
        return "has no expected_ids"
    phase_identity = binding.get("phase_identity")
    if (not isinstance(phase_identity, list) or len(phase_identity) != 2
            or not all(type(part) is int for part in phase_identity)):
        return "has no phase_identity"
    if binding["copy"] != snapshot_copy_name(slot, binding["sha256"]):
        return f"names {binding['copy']!r}, not a copy of its own slot"
    if binding["phase_dir"] != identity["phase_dir"] or binding["artifact"] != identity["artifact"]:
        return "names another phase dir or file than the one its slot is for"
    if _parse_stamp(binding["taken_at"]) is None:
        return "has no time it was taken"
    return None


def _same_batch(binding: Dict[str, Any], identity: Dict[str, Any]) -> bool:
    """Whether a checked binding names the batch *identity* describes."""
    return all(binding.get(key) == identity[key] for key in BINDING_IDENTITY)


def _read_slot(
    folder: "_prompt_files.PromptFolder", slot: str, identity: Dict[str, Any],
) -> _SlotNow:
    """The slot as it is now (no link followed at any name)."""
    names = folder.names()
    copy_name = re.compile(re.escape(slot) + r"\.[0-9a-f]{%d}\.md" % _NAME_HEX)
    copies = sorted(name for name in names if copy_name.fullmatch(name))
    binding_name = snapshot_binding_name(slot)
    shown = os.path.join(folder.path, binding_name)
    if binding_name not in names:
        return _SlotNow(None, None, copies, None)
    try:
        raw = folder.read_bytes(binding_name)
    except FileNotFoundError:
        return _SlotNow(None, None, copies, None)
    except OSError as exc:
        return _SlotNow(None, None, copies, f"{shown} cannot be read ({exc})")
    try:
        binding: Any = json.loads(raw)
    except ValueError as exc:
        return _SlotNow(None, None, copies, f"{shown} is not JSON ({exc})")
    problem = _binding_problem(binding, slot, identity)
    if problem:
        return _SlotNow(None, None, copies, f"{shown} {problem}")
    try:
        held: Optional[bytes] = folder.read_bytes(binding["copy"])
    except OSError:
        held = None
    return _SlotNow(binding, held, copies, None)


@dataclass
class BatchSnapshot:
    """One shared-artifact batch's pre-batch snapshot: the slot, the file it
    copies, its binding and its bytes, with the slot's lock held until
    :meth:`release`. ``kept`` when the batch was bound before and its
    generation stays; else :meth:`commit` publishes a new one, after which
    the copies in ``obsolete`` (the previous generation's, and any no
    binding named) are removed."""

    root: str
    slot: str
    artifact: Path
    binding: Dict[str, Any]
    data: bytes
    place: str = ""
    kept: bool = False
    previous: Optional[str] = None
    obsolete: Tuple[str, ...] = ()
    folder: Optional["_prompt_files.PromptFolder"] = field(default=None, repr=False)
    lock: Optional[int] = field(default=None, repr=False)

    @property
    def path(self) -> Path:
        """The generation's copy, in the slot's home (:class:`_SlotHome`)."""
        return Path(self.place, str(self.binding["copy"]))

    def commit(self) -> None:
        """Publish the generation: the copy, then the binding naming it, each
        a new file renamed into place (never through a link). A failure
        leaves the previous generation whole. Nothing for a kept one."""
        if self.kept:
            return
        if self.folder is None:
            raise OSError(f"the slot {self.slot} is not open")
        name = str(self.binding["copy"])
        self.folder.write_bytes(name, self.data)
        try:
            self.folder.write(
                snapshot_binding_name(self.slot), json.dumps(self.binding, indent=2) + "\n")
        except BaseException:
            if name != self.previous:
                self._remove(name)
            raise
        for old in sorted({*self.obsolete, *(self.previous,)} - {None, name}):
            self._remove(str(old))

    def _remove(self, name: str) -> None:
        try:
            if self.folder is not None:
                self.folder.remove(name)
        except OSError:
            pass  # a leftover copy no binding names: the next call refuses it

    def release(self) -> None:
        """Drop the slot's lock and close it. Idempotent."""
        lock, self.lock = self.lock, None
        if lock is not None:
            _process_control.release_fd_lock(lock)
            try:
                os.close(lock)
            except OSError:
                pass
        folder, self.folder = self.folder, None
        if folder is not None:
            folder.close()


def _batch_identity(
    pin: "_prompt_files.PhasePin", task: Dict[str, Any], task_id: str, kind: str,
    run: str,
) -> Tuple[_SlotHome, Path, str, Dict[str, Any]]:
    """``(home, artifact, slot, identity)`` of a shared-artifact batch in the
    pinned phase dir (:func:`_snapshot_home`)."""
    phase_dir = Path(pin.path)
    declared = declared_file_set(task)
    if len(declared) != 1:
        raise WritePromptError(
            f"Task {task_id} declares {len(declared)} files, not its one "
            f"artifact, so it has no pre-batch snapshot: re-run the phase's "
            f"orchestrator to re-materialize {WRITE_TASK_FILENAME}."
        )
    home = _snapshot_home(pin, task_id)
    artifact = Path(declared[0])
    if not artifact.is_absolute():
        artifact = Path(home.root) / artifact
    artifact = Path(os.path.normpath(str(artifact)))
    phase_identity = pin.identity or _prompt_files.identify(pin).identity
    identity = {
        "task_id": task_id,
        "run": run,
        "phase_dir": pin.path,
        "phase_identity": [int(part) for part in phase_identity or ()],
        "artifact": str(artifact),
        "expected_ids": [str(item) for item in task.get("expected_ids") or []],
    }
    slot = snapshot_slot(kind, _plan_stem(phase_dir, kind, artifact), pin.path, str(artifact))
    return home, artifact, slot, identity


def _take_slot_lock(
    folder: "_prompt_files.PromptFolder", slot: str, task_id: str,
) -> int:
    lock = folder.open_lock(slot + SNAPSHOT_LOCK_SUFFIX)
    shown = os.path.join(folder.path, slot + SNAPSHOT_LOCK_SUFFIX)
    try:
        taken = _process_control.wait_for_fd_lock(lock, timeout_s=SNAPSHOT_LOCK_TIMEOUT_S)
    except OSError as exc:
        os.close(lock)
        cause = exc.strerror or str(exc)
        name = errno.errorcode.get(exc.errno or 0)
        raise WritePromptError(
            f"Cannot lock {shown}: {cause}{f' ({name})' if name else ''}. No other "
            f"call holds it: the lock cannot be taken there at all, so running "
            f"this command again gives the same answer. A file system without "
            f"file locks (some network or FUSE mounts) answers this way: run "
            f"multi-llm from a checkout on a local disk. Nothing was written and "
            f"{task_id} was not handed out."
        ) from exc
    if taken:
        return lock
    os.close(lock)
    raise WritePromptError(
        f"Another `util write-prompt` holds {shown}: it is binding a batch of "
        f"this phase now and did not finish within {SNAPSHOT_LOCK_TIMEOUT_S:g} s. "
        f"Let it finish, then run this command again. Nothing was written and "
        f"{task_id} was not handed out."
    )


def _way_out(artifact: Path, files: List[str], task_id: str) -> str:
    listed = ", ".join(files) if files else "none"
    return (
        f"Nothing was written and {task_id} was not handed out. Way out, for a "
        f"human: if a batch of this phase stopped half-applied, compare {artifact} "
        f"with the copies ({listed}) and put the right bytes back by hand; then "
        f"delete those files and run this command again (with no binding and no "
        f"copy left, it takes a new snapshot)."
    )


def prepare_batch_snapshot(
    pin: "_prompt_files.PhasePin", kind: str, task: Dict[str, Any],
) -> Optional[BatchSnapshot]:
    """The pre-batch snapshot a shared-artifact batch is handed out with,
    its slot's lock held (the caller releases it).

    ``None`` for a kind that has none (apply-code-fixes and implement are
    checked otherwise). The batch bound again (the same binding identity):
    its generation, ``kept``, once its copy still hashes to the binding.
    Another batch: a copy of the artifact, read now under the lock and
    published by :meth:`BatchSnapshot.commit` after the prompt. Raises
    :class:`WritePromptError` (exit 3, nothing written) when the repository
    holding the phase dir cannot be pinned, an earlier batch of the run is
    not recorded yet, the slot
    is held by another call for too long or its lock cannot be taken on its
    file system at all, its evidence is damaged (a binding that cannot be
    read or misses a field, copies no binding names, a state file that cannot
    say whether the bound batch was recorded), the bound baseline of this
    batch was altered or removed, it belongs to another batch of this run
    with no record made for it, or the artifact cannot be read;
    ``OSError`` when the phase dir or the temp dir is a link.
    """
    if kind not in SNAPSHOT_ROLES:
        return None
    task_id = str(task.get("task_id") or "")
    run, document = _read_run(pin)
    home, artifact, slot, identity = _batch_identity(pin, task, task_id, kind, run)
    refused = _order_refusal(
        pin, document, task, task_id, run,
        lambda batch_id: _slot_bound_to(home, slot, identity, batch_id, run),
    )
    if refused:
        raise WritePromptError(refused)
    folder = home.open(create=True)
    lock: Optional[int] = None
    try:
        lock = _take_slot_lock(folder, slot, task_id)
        snapshot = _decide(pin, folder, home.root, slot, artifact, identity, kind, task_id)
    except BaseException:
        if lock is not None:
            _process_control.release_fd_lock(lock)
            os.close(lock)
        folder.close()
        raise
    snapshot.folder, snapshot.lock = folder, lock
    return snapshot


def _decide(
    pin: "_prompt_files.PhasePin", folder: "_prompt_files.PromptFolder", root: str,
    slot: str, artifact: Path, identity: Dict[str, Any], kind: str, task_id: str,
) -> BatchSnapshot:
    """The slot's transition for *task_id*, under the slot's lock."""
    now = _read_slot(folder, slot, identity)
    shown = [os.path.join(folder.path, name) for name in now.copies]
    binding_path = os.path.join(folder.path, snapshot_binding_name(slot))
    if now.damage:
        raise WritePromptError(
            f"{now.damage}, so nothing says whose pre-batch baseline the slot "
            f"holds, and binding {task_id} would replace it. "
            + _way_out(artifact, [binding_path, *shown], task_id))
    bound = now.binding
    previous: Optional[str] = None
    if bound is None:
        if now.copies:
            raise WritePromptError(
                f"{', '.join(shown)} lie in {folder.path} with no binding naming "
                f"them (it was deleted, or a write was cut short), so nothing says "
                f"whose pre-batch baseline they hold, and binding {task_id} would "
                f"replace it. " + _way_out(artifact, shown, task_id))
    elif _same_batch(bound, identity):
        held = now.held
        if held is None or _sha256(held) != bound["sha256"]:
            state = "it is gone" if held is None else (
                f"recorded {bound['sha256'][:12]}, now {_sha256(held)[:12]}")
            raise WritePromptError(
                f"{task_id} was bound before, and its pre-batch snapshot "
                f"{os.path.join(folder.path, bound['copy'])} no longer holds the "
                f"bytes it was taken with ({state}). A new copy of {artifact} "
                f"could carry {task_id}'s own edits, so none is taken. "
                + _way_out(artifact, [binding_path, *shown], task_id))
        return BatchSnapshot(root, slot, artifact, bound, held, place=folder.path, kept=True)
    elif bound["run"] == identity["run"] and bound.get("phase_identity") == identity["phase_identity"]:
        # Another batch of this run: replaced once that batch is recorded.
        earlier = bound["task_id"]
        state, problem = _read_plan_state(pin.path)
        if state is None:
            raise WritePromptError(
                f"{binding_path} holds the pre-batch baseline of {earlier}, bound "
                f"earlier in this run, and whether {earlier} has its `util "
                f"batch-done` record cannot be told, because {problem}; binding "
                f"{task_id} would replace that baseline. Nothing was written and "
                f"{task_id} was not handed out. Put state.json back, or re-run the "
                f"phase's orchestrator with --resume (a new run takes a new "
                f"snapshot), then run this command again."
            )
        if not _recorded_with(
            state, Path(pin.path).name, earlier,
            RECORD_GENERATION_KEY, bound["generation"],
        ):
            raise WritePromptError(
                f"{os.path.join(folder.path, bound['copy'])} is the pre-batch "
                f"snapshot of {earlier}, bound earlier in this run, and {earlier} "
                f"has no `util batch-done` record made for this snapshot (one "
                f"carrying its generation, {bound['generation'][:12]}): binding "
                f"{task_id} would replace its baseline. Finish {earlier} first — verify it "
                f"against that snapshot and record it with util batch-done — or, "
                f"after a partial application, stop the loop there (the snapshot "
                f"holds {earlier}'s pre-batch bytes to compare with, or to copy "
                f"back by hand). {task_id} was not handed out and the snapshot is "
                f"unchanged."
            )
        previous = bound["copy"]
    else:
        # A new emit of the phase (a --resume, a re-run): a new run.
        previous = bound["copy"]
    try:
        data = artifact.read_bytes()
    except OSError as exc:
        raise WritePromptError(
            f"Cannot read {artifact}, the file {task_id} edits, to take its "
            f"pre-batch snapshot: {exc}. {task_id} was not handed out."
        ) from exc
    digest = _sha256(data)
    binding = {
        "version": SNAPSHOT_BINDING_VERSION,
        "kind": kind,
        **identity,
        "root": root,
        "copy": snapshot_copy_name(slot, digest),
        "sha256": digest,
        "size": len(data),
        "generation": secrets.token_hex(_GENERATION_HEX // 2),
        "taken_at": datetime.now().isoformat(timespec="microseconds"),
    }
    return BatchSnapshot(
        root, slot, artifact, binding, data, place=folder.path,
        previous=previous, obsolete=tuple(now.copies),
    )


def completion_stamp(phase_dir: Path, kind: str, task: Dict[str, Any]) -> Dict[str, str]:
    """What ``util batch-done`` records beside a shared-artifact batch's
    status (:func:`record_completion_stamp`), so this command can tell whose
    record it is without comparing clocks: ``run`` (:data:`RECORD_RUN_KEY`), the sha256 of
    ``write_tasks.json`` now, and — when the slot's binding names this very
    batch — ``snapshot_generation`` (:data:`RECORD_GENERATION_KEY`), the
    binding's generation. Empty for another kind. Read without the slot's
    lock: a binding is only ever replaced whole, and not before this batch
    has a record. Whatever cannot be read is left out, never an error: a
    record without a stamp counts for nothing here, and the refusal that
    follows names the files."""
    if kind not in SNAPSHOT_ROLES:
        return {}
    task_id = str(task.get("task_id") or "")
    try:
        pin = phase_dir_pin(Path(phase_dir))
        run, _document = _read_run(pin)
    except (OSError, WritePromptError):
        return {}
    stamp = {RECORD_RUN_KEY: run}
    try:
        home, _artifact, slot, identity = _batch_identity(pin, task, task_id, kind, run)
        folder = home.open(create=False)
    except (OSError, WritePromptError):
        return stamp
    try:
        bound = _read_slot(folder, slot, identity).binding
    except OSError:
        bound = None
    finally:
        folder.close()
    if bound is not None and _same_batch(bound, identity):
        stamp[RECORD_GENERATION_KEY] = bound["generation"]
    return stamp


def record_completion_stamp(
    state: Dict[str, Any], phase_word: str, task_id: str, stamp: Dict[str, str],
) -> None:
    """Keep *stamp* (:func:`completion_stamp`) as *task_id*'s under
    :data:`SNAPSHOT_RECORDS_KEY` in a raw ``state.json`` dict, replacing an
    earlier one; nothing for an empty stamp (another kind)."""
    if not stamp:
        return
    records = state.get(SNAPSHOT_RECORDS_KEY)
    if not isinstance(records, dict):
        records = state[SNAPSHOT_RECORDS_KEY] = {}
    phase = records.get(phase_word)
    if not isinstance(phase, dict):
        phase = records[phase_word] = {}
    phase[task_id] = dict(stamp)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="multi_llm.py util write-prompt",
        description=(
            "Print or write one write batch's prompt, with the prior-batch "
            "context bound from the log as it is now and the write-batch "
            "result contract appended — the text the executor leg would "
            "dispatch for the same task."
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
    where = parser.add_mutually_exclusive_group()
    where.add_argument(
        "--output", default=None, metavar="PATH",
        help=f"Write the prompt here instead of {PROMPTS_SUBDIR}/<task-id>.prompt.txt "
             f"under the phase dir.",
    )
    where.add_argument(
        "--stdout", action="store_true",
        help="Print the prompt text itself and nothing else.",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    bootstrap_streams()
    parser = _build_parser()
    args = parser.parse_args(argv)
    # The phase dir as it is now, before anything is read from it: the
    # prompt, the check's tree record and the pre-batch snapshot are written
    # for this directory or not at all, so a phase dir that is
    # a link or not a directory is refused here, before any side effect.
    try:
        pin = phase_dir_pin(Path(args.phase_dir))
    except OSError as exc:
        if isinstance(exc, FileNotFoundError):
            # No phase dir yet: the render names what is missing.
            try:
                render_write_prompt(Path(args.phase_dir), args.task_id)
            except (WritePromptError, ExecutorError) as missing:
                message = getattr(missing, "message", None) or str(missing)
                print(f"ERROR: {message}", file=sys.stderr)
                return int(getattr(missing, "exit_code", 3) or 3)
        print(
            f"ERROR: cannot use the phase dir {args.phase_dir}: {exc}. Nothing "
            f"was written and {args.task_id} was not handed out.",
            file=sys.stderr,
        )
        return 1
    # Before anything is recorded for the batch: a batch whose verdicts'
    # review round was superseded is not handed out.
    superseded = superseded_round_refusal(pin, args.task_id)
    if superseded is not None:
        print(f"ERROR: {superseded}", file=sys.stderr)
        return 3
    # Re-checked before the prompt is bound; a
    # batch whose fix files changed since the apply guard decided gets none.
    stale = commit_stale_check(Path(args.phase_dir), args.task_id)
    if stale is not None:
        for line in stale:
            print(line)
        return 0
    try:
        text, _task, info = render_write_prompt(Path(args.phase_dir), args.task_id)
    except (WritePromptError, ExecutorError) as exc:
        message = getattr(exc, "message", None) or str(exc)
        print(f"ERROR: {message}", file=sys.stderr)
        return int(getattr(exc, "exit_code", 3) or 3)

    held = held_by_check(Path(args.phase_dir), args.task_id)
    if held is not None:
        check_id, findings = held
        shown = ""
        if findings:
            more = f" (+{len(findings) - 1} more)" if len(findings) > 1 else ""
            shown = f": {findings[0]}{more}"
        print(
            f"{MARKER_BLOCKED} {args.task_id} depends on {check_id}, whose check "
            f"reported problems{shown}. Do not dispatch {args.task_id} and record "
            f"nothing for it: it stays pending. Finish the tasks that do not "
            f"depend on {check_id}, close the phase without --mark-completed, "
            f"and report the way forward: fix what {check_id} reported and "
            f"re-run implement with --resume (the check runs again), or accept "
            f"its findings with --resume --human-task {check_id}=done (the held "
            f"tasks then run, told that the findings were accepted).",
            file=sys.stderr,
        )
        return 3

    refused = policy_refusal(Path(args.phase_dir), args.task_id)
    if refused is not None:
        task_id = args.task_id
        hits = policy_refused_hits(Path(args.phase_dir), task_id)
        implement = info.get("kind") == "implement"
        # Worded per rule (a deny hit names the deny rule to
        # narrow), and, for a file outside the repository, the skip alone.
        clause = policy_allow_clause(hits)
        skip = (
            f"skip {task_id} with --resume --human-task {task_id}=skip "
            f"({task_id} and the tasks after it stay undone)"
        )
        if clause is None:
            note = policy_outside_note(hits)
            forward = (
                f", skip the tasks that depend on it, run the others, close "
                f"the phase without --mark-completed, and report the way "
                f"forward as the user's call, in these words: {note}; "
                f"{skip}."
                if implement else
                f", stop, and report that {note}."
            )
        else:
            forward = (
                f", skip the tasks that depend on it, run the others, close "
                f"the phase without --mark-completed, and report both ways "
                f"forward as the user's call, in these words: {clause}, then "
                f"re-run implement with --resume; if not, {skip}."
                if implement else
                f", stop, and report the way forward as the user's call, in "
                f"these words: {clause}, then re-run this phase with --resume."
            )
        print(
            f"{MARKER_REFUSED} {task_id} is refused before dispatch: {refused} "
            f"Do not dispatch {task_id}. Record it with util batch-done "
            f"--phase-dir \"{os.path.abspath(args.phase_dir)}\" --task-id {task_id} "
            f"--status failed --reason \"refused before dispatch: the write "
            f"policy (driver.write_paths) does not allow a file it declares\""
            + forward + " Never change driver.write_paths yourself.",
            file=sys.stderr,
        )
        return 3

    # A shared-artifact batch's pre-batch snapshot: its refusals come after
    # every other one and before anything is recorded for the batch; the
    # slot's lock is held until the call ends, and a new generation is
    # published once the prompt is.
    try:
        snapshot = prepare_batch_snapshot(pin, str(info.get("kind") or ""), _task)
    except WritePromptError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return exc.exit_code
    except OSError as exc:
        print(f"ERROR: cannot take the pre-batch snapshot: {exc}", file=sys.stderr)
        return 1
    try:
        # Advisory, on stderr so `--stdout` stays the prompt text alone.
        for line in ordering_warnings(Path(args.phase_dir), args.task_id):
            print(line, file=sys.stderr)
        return _hand_out(args, pin, text, info, _task, snapshot)
    finally:
        if snapshot is not None:
            snapshot.release()


def _hand_out(
    args: argparse.Namespace, pin: "_prompt_files.PhasePin", text: str,
    info: Dict[str, Any], task: Dict[str, Any], snapshot: Optional[BatchSnapshot],
) -> int:
    """Record what the batch is held to, publish its prompt and its
    snapshot, and print the markers that hand it out."""
    snapshot_lines = [] if snapshot is None else [
        f"{MARKER_SNAPSHOT} {snapshot.path}", f"{MARKER_ARTIFACT} {snapshot.artifact}",
    ]

    def committed() -> bool:
        """The new generation published, before the markers hand the batch out."""
        if snapshot is None:
            return True
        try:
            snapshot.commit()
        except OSError as exc:
            print(
                f"ERROR: cannot write the pre-batch snapshot {snapshot.path}: "
                f"{exc}. The previous one is unchanged and {args.task_id} was "
                f"not handed out.",
                file=sys.stderr,
            )
            return False
        return True

    if is_check_task(str(info.get("kind") or ""), task):
        # What `util batch-done` holds this check to: it changes no file.
        record_check_tree(Path(args.phase_dir), args.task_id, pin)

    # The watched set as this batch is handed
    # out, what its `util batch-done` compares with. No-op without a guard.
    commit_bind(Path(args.phase_dir), args.task_id)

    if args.stdout:
        # The prompt text alone on stdout; the snapshot's markers beside it.
        if not committed():
            return 1
        for line in snapshot_lines:
            print(line, file=sys.stderr)
        sys.stdout.write(text)
        sys.stdout.flush()
        return 0

    target = Path(args.output) if args.output else default_output_path(
        Path(args.phase_dir), args.task_id
    )
    try:
        if args.output:
            # A path the caller named: written where it says.
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")
        else:
            with _prompt_files.PromptFolder.open(pin) as folder:
                folder.write(target.name, text)
    except OSError as exc:
        # The previous generation of the snapshot is left as it was.
        print(f"ERROR: cannot write {target}: {exc}", file=sys.stderr)
        return 1
    if not committed():
        return 1
    lines = text.count("\n") + (0 if text.endswith("\n") else 1)
    print(f"{MARKER_PATH} {target}")
    print(f"{MARKER_LINES} {lines}")
    print(
        f"{MARKER_CONTEXT} {info['context_entries']} prior-batch entries bound "
        f"({info['phase']}, from {Path(info['output_dir']) / _prior_changes.FILENAME})"
    )
    for line in snapshot_lines:
        print(line)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main(sys.argv[1:]))
