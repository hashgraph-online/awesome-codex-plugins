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
and appends the write-batch result contract. Both invokers therefore produce
byte-identical text for the same prior-changes log (each leg appends a
summary per finished batch and a failure line per failed one, fix round 15;
a native host words a failure's reason itself): it calls the scheduler's own
:func:`utils.write_batch_scheduler.bind_prior_changes` and
:func:`utils.write_batch_scheduler.with_result_contract`, and
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
prompt text itself instead, and nothing else. After a commit review
(plans/review-commits.md §2.7) an apply-code-fixes batch whose fix files
changed since the apply guard decided gets no prompt at all: one
``[COMMIT_FIXES_STALE]`` line replaces the markers (in both modes), the batch
is already recorded, and the exit is 0 (:func:`commit_stale_check`); a batch
that passes has the watched set's disk ids recorded as its prompt is bound,
which its ``util batch-done`` compares with (:func:`commit_bind`). Exit 3 names the problem: no
``write_tasks.json`` (run the phase's orchestrator first), an unknown task id
(the known ids are listed), a human task (it never dispatches) or a prompt
without the token (a producer bug, the scheduler's own refusal).

The prior-changes log is the plan dir's ``prior_changes.jsonl`` — the parent
of the phase dir, where the executor leg appends — scoped to this phase as
the scheduler scopes it; the instructions' ``util prior-changes append`` step
names the same directory.

Import is side-effect free: argparse and all I/O live inside :func:`main`.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from . import known_checks as _known_checks
    from . import prior_changes as _prior_changes
    from . import prompt_files as _prompt_files
    from .git_utils import (
        find_git_entry_root, pin_repo_root, worktree_file_stats, worktree_fingerprint,
    )
    from .metrics import (
        _read_state, _write_state, mark_failed_in_progress, state_file_lock,
        withdraw_from_progress_in_state,
    )
    from .state_manager import (
        PROCESSED_LEG_NATIVE, record_batch_items_in_state, update_task_status_in_state,
    )
    from .stream_bootstrap import bootstrap_streams
    from .subagent_executor import ExecutorError, ResultRejected
    from .subagent_tasks import (
        PHASE_BY_WRITE_KIND, TASKS_SCHEMA_VERSION, declared_file_set,
    )
    from .write_batch_scheduler import (
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
        DISPATCHED_PROMPTS_SUBDIR,
        OWN_RUN_CONTEXT_PHASES,
        SWEEP_MAX_FILES,
        accepted_upstream_checks,
        bind_prior_changes,
        decomposition_graph,
        dispatched_prompt_path,
        is_check_task,
        last_phase_end,
        rerunnable_checks,
        upstream_held_check,
        with_result_contract,
    )
    from .write_phase_bridge import WRITE_TASK_FILENAME
    from .write_safety import (
        PolicyViolation, WritePolicy, policy_allow_clause, policy_outside_note,
        relative_to_root,
    )
except ImportError:  # pragma: no cover - direct script invocation
    from utils import known_checks as _known_checks  # type: ignore
    from utils import prior_changes as _prior_changes  # type: ignore
    from utils import prompt_files as _prompt_files  # type: ignore
    from utils.git_utils import (  # type: ignore
        find_git_entry_root, pin_repo_root, worktree_file_stats, worktree_fingerprint,
    )
    from utils.metrics import (  # type: ignore
        _read_state, _write_state, mark_failed_in_progress, state_file_lock,
        withdraw_from_progress_in_state,
    )
    from utils.state_manager import (  # type: ignore
        PROCESSED_LEG_NATIVE, record_batch_items_in_state, update_task_status_in_state,
    )
    from utils.stream_bootstrap import bootstrap_streams  # type: ignore
    from utils.subagent_executor import ExecutorError, ResultRejected  # type: ignore
    from utils.subagent_tasks import (  # type: ignore
        PHASE_BY_WRITE_KIND, TASKS_SCHEMA_VERSION, declared_file_set,
    )
    from utils.write_batch_scheduler import (  # type: ignore
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
        DISPATCHED_PROMPTS_SUBDIR,
        OWN_RUN_CONTEXT_PHASES,
        SWEEP_MAX_FILES,
        accepted_upstream_checks,
        bind_prior_changes,
        decomposition_graph,
        dispatched_prompt_path,
        is_check_task,
        last_phase_end,
        rerunnable_checks,
        upstream_held_check,
        with_result_contract,
    )
    from utils.write_phase_bridge import WRITE_TASK_FILENAME  # type: ignore
    from utils.write_safety import (  # type: ignore
        PolicyViolation, WritePolicy, policy_allow_clause, policy_outside_note,
        relative_to_root,
    )


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
        # Fix round 22: the entries the render bound, this run's own.
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


def _accepted_checks(
    phase_dir: Path, document: Dict[str, Any], task_id: str,
) -> List[Tuple[str, str, List[str]]]:
    """The checks upstream of an implement task whose findings the user
    accepted (``write_batch_scheduler.accepted_upstream_checks``), from the
    plan dir's ``state.json`` as it is now — what the executor leg reads at
    dispatch (fix round 14). ``[]`` for any other kind, or a state that
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
    ``state.json`` as it is now — what the executor leg binds at dispatch
    (fix round 20). ``""`` for every other kind; advisory, never a refusal."""
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

    Fix round 13 (the check-gate fixture): ``driver.write_paths`` refuses a
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
    """The declared files the policy refuses for *task_id* (fix round 20: the
    way forward names them), or ``[]``."""
    return [str(getattr(hit, "path", hit)) for hit in policy_refused_hits(phase_dir, task_id)]


def policy_refused_hits(phase_dir: Path, task_id: str) -> List[Any]:
    """Each declared file the policy refuses for *task_id*, with its rule
    (``write_safety.PolicyHit``; fix round 21: the way forward is worded
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
    (its ``hits`` word the way forward, fix round 21)."""
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
        # As declared (fix round 21): a file outside the repository is named
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
    task out (fix round 14: a task the policy refuses is recorded failed and
    left out of the batches, as the executor refuses it before dispatch).
    *anchor_dir* is any directory inside the repository (the phase dir, or
    the plan's output folder before the phase dir exists).
    """
    violation = policy_violation_for(task, plan_file=plan_file, anchor_dir=anchor_dir)
    return violation.message if violation is not None else None


#: The pre-rename spelling.
_policy_violation_for = policy_violation_for


# ---------------------------------------------------------------------------
# The commit re-check (plans/review-commits.md §2.7)
# ---------------------------------------------------------------------------
#
# "Every batch is re-checked immediately before it is dispatched": a batch
# can start long after the apply guard decided (after judging, the batches
# ahead of it, a stop, a `--resume`), so before this command binds the prompt
# the host is about to hand a subagent, every fix file the batch declares is
# held to the content the guard saved for it — the executor's
# `WriteBatchScheduler._commit_recheck`, through the same shared helpers. A
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
    with state_file_lock(target):
        state = _read_state(target)
        guard = commit_guard_of(state, kind) if isinstance(state, dict) else None
        if guard is None:
            return None
        commit_apply.mark_stale(guard, groups, failing, cwd=root)
        commit_apply.save_guard(target, guard)
        # What save_guard wrote, then this batch's record over it.
        state = _read_state(target)
        update_task_status_in_state(state, task_id, "failed", reason)
        # Every item `failed`, as `util batch-done --status failed` records
        # them: a native `--resume` hands them out again, and the guard's
        # saved skips take the skipped ones out (and count them) there.
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
        _write_state(target, state)
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
    """Record the watched set's disk ids as *task_id*'s prompt is bound
    (plans/review-commits.md §2.7, "Every observed write, after each batch"),
    so its ``util batch-done`` counts only a change made while the batch ran:
    ``commit_apply.bind_watched``, saved in the guard under
    ``state_file_lock``. The executor reads the same ids just before it
    dispatches a batch (``WriteBatchScheduler._commit_watch_begin``); here
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
        with state_file_lock(target):
            state = _read_state(target)
            guard = commit_guard_of(state, kind) if isinstance(state, dict) else None
            # Nothing watched: the saved ids (none) are the same comparison.
            if guard is None or not commit_apply.watched_ids(guard):
                return False
            commit_apply.bind_watched(guard, task_id, cwd=root)
            _write_state(target, state)
        return True
    except Exception:  # noqa: BLE001 - batch-done then compares with the saved ids
        return False


def held_by_check(phase_dir: Path, task_id: str) -> Optional[Tuple[str, List[str]]]:
    """``(check id, its findings)`` when a check with findings holds *task_id*.

    Fix round 11: on the native leg the host dispatches each task itself, so
    the plugin's hold on the tasks that depend on a check that reported
    problems (the executor leg's ``WriteBatchScheduler._block_dependents_of_checks``)
    is enforced here, where the host gets each task's prompt. The held
    checks are ``state.json``'s (``write_batch_scheduler.rerunnable_checks``:
    findings on record, recorded completed, not accepted with
    ``--human-task <id>=done``); the graph is ``write_tasks.json``'s
    ``depends_on`` plus ``state.json``'s recorded decomposition
    (``write_batch_scheduler.decomposition_graph``, fix round 12: a
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

    Fix round 7 (racing re-run 3, Claude Code apply-code-fixes): the host
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
    # Fix round 22: a phase whose prompts carry only this run's batches
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

    Fix round 17: the host's subagents can write the phase dir, and this
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
# The check guard (fix round 13)
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
    try:
        from .check_tree import check_tree_exclusions
    except ImportError:  # pragma: no cover - direct script invocation
        from utils.check_tree import check_tree_exclusions

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
    ``WriteBatchScheduler._tree_fingerprint`` uses (workflow artifacts and
    ``.multi-llm/``, keeping colocated code), so both legs mean the same thing by "the
    files changed". The native leg stamps it on a check with findings
    (``util batch-done``, re-stamped by ``util finalize-tracking`` with the
    tree the run left) and compares it on ``--resume`` before handing the
    check out again (fix round 14). ``None`` when the repository cannot be
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
    # prompt and the check's tree record are written to this directory or
    # not at all (fix round 17).
    try:
        pin: Optional[_prompt_files.PhasePin] = phase_dir_pin(Path(args.phase_dir))
        pin_problem: Optional[OSError] = None
    except OSError as exc:
        pin, pin_problem = None, exc
    # plans/review-commits.md §2.7: re-checked before the prompt is bound; a
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
        # Fix round 21: worded per rule (a deny hit names the deny rule to
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

    # Advisory, on stderr so `--stdout` stays the prompt text alone.
    for line in ordering_warnings(Path(args.phase_dir), args.task_id):
        print(line, file=sys.stderr)

    if is_check_task(str(info.get("kind") or ""), _task):
        # What `util batch-done` holds this check to: it changes no file.
        if pin is not None:
            record_check_tree(Path(args.phase_dir), args.task_id, pin)
        else:
            discard_check_tree(Path(args.phase_dir), args.task_id)

    # plans/review-commits.md §2.7: the watched set as this batch is handed
    # out, what its `util batch-done` compares with. No-op without a guard.
    commit_bind(Path(args.phase_dir), args.task_id)

    if args.stdout:
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
            if pin is None:
                raise pin_problem or OSError(f"{args.phase_dir} cannot be opened")
            with _prompt_files.PromptFolder.open(pin) as folder:
                folder.write(target.name, text)
    except OSError as exc:
        print(f"ERROR: cannot write {target}: {exc}", file=sys.stderr)
        return 1
    lines = text.count("\n") + (0 if text.endswith("\n") else 1)
    print(f"{MARKER_PATH} {target}")
    print(f"{MARKER_LINES} {lines}")
    print(
        f"{MARKER_CONTEXT} {info['context_entries']} prior-batch entries bound "
        f"({info['phase']}, from {Path(info['output_dir']) / _prior_changes.FILENAME})"
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main(sys.argv[1:]))
