#!/usr/bin/env python3
"""
Implementation orchestrator: prepares a plan's tasks for the driving agent.

This orchestrator takes a plan file, decomposes it into tasks, organizes them
into dependency-respecting batches, and either outputs JSON for the driving
agent to execute with its own subagents (the native leg) or schedules the
batches itself through the write executor (``--exec-subagents``).

Usage:
    uv run --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" implement plans/my-plan.md [--output tasks.json]
"""

import argparse
import hashlib
import io
import json
import logging
import os
import stat as _stat
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from types import SimpleNamespace
from typing import (
    Any, Callable, Collection, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple,
)

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.git_utils import get_modified_files, get_staged_files, head_or_empty_tree
from utils.output_handler import get_output_paths, get_relative_output_path
from utils.prompt_loader import load_prompt
from utils.state_manager import StateManager, get_or_create_state
from utils.task_decomposer import Task, TaskDecomposer, TaskStatus
from utils import metrics as metrics_mod
from utils.stream_bootstrap import bootstrap_streams
from utils.text_clip import clip, join_clauses
from utils.cli_common import (
    EXIT_NEEDS_HUMAN,
    add_scope_policy_argument,
    build_parent_parser,
    dispatcher_command,
    record_artifacts,
    record_error,
    record_notice,
    typed_plan_for,
)
from utils.output_handler import get_phase_dir, get_output_dir, phase_dir_path
from utils.tasks_file import (
    TasksFileAmbiguous,
    TasksFileMissing,
    TasksFileRefused,
    read_task_list,
)
from utils.state_manager import (
    mark_tasks_reset_in_state,
    clear_task_verdict,
    TASK_BATCH_CHECK_KEY,
    TASK_CHECK_FINDINGS_KEY,
    TASK_CHECK_TREES_KEY,
    set_task_check_tree_in_state,
)
from utils.git_utils import get_project_root
from utils.provider_registry import set_run_anchor
from utils import scope_policy_runs
from utils import unattended as unattended_mod
from utils.unattended import (
    HUMAN_TASK_STRATEGIES,
    UNATTENDED_HUMAN_TASK_STRATEGY,
    NeedsHuman,
    parse_human_task_decisions,
)
from check_workflow_prerequisites import (
    SKIPPED_MARKER,
    SKIP_PREREQUISITES_REASON,
    build_unmet_message,
    check_apply_suggestions_prerequisite as _shared_apply_suggestions_prerequisite,
    check_apply_task_suggestions_prerequisite,
    implement_records_predate_task_list,
    record_prerequisite_skip,
    upstream_skip_notices,
)
from utils import review_orchestrator_base
from utils import prior_changes as _prior_changes
from utils import prompt_files
from utils import host_capabilities as _hosts
from utils import manual_tasks as _manual
from utils import routes as _routes
from utils import detach as _detach
from utils import next_phase_words as _words
from utils import write_safety as _write_safety
from utils import write_batch_scheduler
from utils import write_phase_bridge
from utils.check_records import (
    rerunnable_checks,
    unlanded_on_record,
    decomposition_graph,
    write_result_notice,
    blocked_by_check_reason,
    transitive_dependents,
)
from utils.subagent_tasks import implement_output_name
from utils.write_safety import (
    TaskSnapshot,
    WriteSafetyError,
    policy_allow_clause,
    policy_skip_clause,
)
from utils.batch_prompt import DISPATCHED_PROMPTS_SUBDIR, is_check_task, dispatch_line
from utils.human_task_plan import (
    plan_manual_gates,
    manual_gate_head,
    manual_gate_way_on,
    mark_no_longer_skipped,
    resolve_human_task_plan,
    answered_done_label,
    answered_done_on_record,
    set_aside_by_plan,
    persist_human_task_plan,
)
from utils.batch_ledger import touched_files
from utils.write_batch_scheduler import SchedulerOptions
from utils.write_prompt import check_tree_fingerprint, policy_violation_for
from utils.stop_answers import executor_check_stamp, NATIVE_REFUSED_PREFIX
from utils.task_ledger import KEPT_WITH_FINDINGS_LABEL, kept_named
from utils.batch_done import resume_refusal_lines, unrecorded_logged_batches
from utils.host_capabilities import resolve_host_id
from utils.manual_tasks import after_code_note

logger = logging.getLogger(__name__)


def _unlanded_on_record(plan_path: Path, state: Any) -> List[str]:
    """``check_records.unlanded_on_record`` for this plan, each id
    named on stdout with why it runs again."""

    phase_dir = get_phase_dir(plan_path, "implement")
    unlanded = unlanded_on_record(str(phase_dir), state.state)
    for task_id in unlanded:
        print(
            f"[resume] {task_id} runs again: an earlier run recorded it done, "
            f"but its result file says its change never landed (the reply "
            f"said applied and no file changed)."
        )
    return unlanded


def check_apply_suggestions_prerequisite(state, plan_dir: Path) -> dict:
    """Row 6: whether apply-suggestions still owes work before implement runs.

    The gate is ``check_workflow_prerequisites``'s (D6a: the gates live there,
    never in a thin orchestrator copy), which reads every ``validation.json``
    shape and returns the ``valid_count``/``importance_breakdown`` the unmet
    block below renders. The copy this used to be read only the v1 flat dict
    and crashed on the v2 envelope (``validation.values()`` handed it an int)
    whenever the gate was actually reached.
    """
    return _shared_apply_suggestions_prerequisite(state, plan_dir)


def resolve_human_task_strategy(
    state,
    human_task_ids: List[str],
    *,
    force_strategy: Optional[str],
    unattended: bool,
    resume: bool,
) -> Optional[str]:
    """Resolve D6 row 8 — how tasks needing a human are handled.

    Resolution order, unchanged from ``instructions/implement.md`` except that the
    fourth rung is no longer a prompt:

    1. ``--force-strategy`` — an explicit flag always wins.
    2. ``--resume`` with a saved ``human_task_strategy`` in ``state.json``.
    3. ``--yes`` → :data:`UNATTENDED_HUMAN_TASK_STRATEGY` (``skip-dependents``).
       An unattended run cannot perform manual steps, so code tasks depending on
       them cannot be assumed valid — ``skip-continue`` would run them anyway.
    4. Neither → ``None``: the driving agent renders the gate (attended only).

    Whatever is resolved is persisted exactly as ``--force-strategy`` does, so
    ``--resume`` stays stable and never re-asks.
    """
    if not human_task_ids:
        return None
    strategy: Optional[str] = None
    if force_strategy:
        strategy = force_strategy
    elif resume and state.get("human_task_strategy"):
        strategy = state.get("human_task_strategy")
    elif unattended:
        strategy = UNATTENDED_HUMAN_TASK_STRATEGY
    if strategy is None:
        return None
    if state.get("human_task_strategy") != strategy:
        state.set("human_task_strategy", strategy)
        state.save()
    return strategy


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Prepare implementation tasks from a plan file for the driving agent to execute",
        parents=[build_parent_parser()],
    )

    parser.add_argument(
        '--plan-file',
        required=True,
        help='Path to the implementation plan markdown file'
    )

    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Output path for tasks JSON (default: '
             '<git-root>/.multi-llm/tmp/'
             'implementation_tasks_{plan_stem}_{hash8}.json, where {hash8} '
             'is a stable hash of the repo-relative plan path; resolved '
             'from the plan file after argument parsing)'
    )

    parser.add_argument(
        '--resume',
        action='store_true',
        help='Resume from previous session state (skip completed tasks)'
    )

    parser.add_argument(
        '--fresh',
        action='store_true',
        help='Start over: dispatch every task again, setting aside what '
             'earlier runs of this implement recorded for each task (a later '
             '--resume keeps only what this run finishes). Without it, a run '
             'on an implement that started and did not finish continues it '
             'as --resume; one that finished starts over either way. --resume '
             'wins over --fresh.'
    )

    parser.add_argument(
        '--task',
        type=str,
        help='Output only a specific task ID'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show task summary without writing output file'
    )

    # --- D5a decision flags (the non-interactive answer to D6 rows 7, 8, 9) ---
    # Documented in instructions/implement.md long before this parser accepted
    # them: the strategy prompt and the per-task pause were markdown-only, which
    # meant the *only* way to answer them was to be a human at a terminal. Every
    # gate now has a flag whose values enumerate exactly the options the question
    # rendered — `choices` validates them, and an empty/unknown value is exit 3.
    parser.add_argument(
        '--no-confirm',
        action='store_true',
        help='Skip the task-suggestion advisory prompt (D6 row 7): record '
             'apply-task-suggestions as skipped and proceed. Implied by --yes.'
    )
    parser.add_argument(
        '--force-strategy',
        choices=list(HUMAN_TASK_STRATEGIES),
        default=None,
        help='Answer the human-task strategy gate (D6 row 8) without a prompt '
             'and persist it to state.json, so --resume stays stable. Under '
             '--yes the default is skip-dependents; pause-and-ask together with '
             '--yes is exit 3.'
    )
    parser.add_argument(
        '--human-task',
        action='append',
        default=None,
        metavar='ID=done|skip|retry',
        help='Answer one human task (D6 row 9), repeatable: --human-task '
             'T004=done. Turns the pause-and-ask pause into a process boundary '
             'instead of a blocked stdin. Under skip-dependents (the --yes '
             'default), T004=skip says you will not do that manual task: it '
             'and the tasks after it are skipped at your request, never owed '
             '(under skip-continue the code after it still runs). With '
             '--resume it also answers a code '
             'task the last run recorded failed (a check that failed), or a '
             'check whose findings hold back the tasks after it: done treats '
             'it as satisfied and runs the tasks after it, skip leaves it and '
             'its dependents undone, retry runs a check again even though '
             'nothing in the repository changed since it ran.'
    )
    add_scope_policy_argument(parser, role="implement")

    return parser.parse_args(argv)


def _plan_path_hash(plan_path: Path, project_root: str) -> str:
    """Stable 8-hex-char hash of the repo-relative plan path.

    Hashes the POSIX form of the plan path relative to ``project_root`` so
    the value is identical on every OS regardless of separator style. Falls
    back to the absolute POSIX path when the plan does not sit under the
    detected root (e.g. symlinked layouts) — still deterministic per plan
    location, which is all the filename needs.
    """
    try:
        key = plan_path.resolve().relative_to(
            Path(project_root).resolve()
        ).as_posix()
    except ValueError:
        key = plan_path.resolve().as_posix()
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:8]


def resolve_default_output(plan_path: Path) -> str:
    """Resolve the default --output path anchored at the git project root.

    The default lives inside the repo workspace
    (``<git-root>/.multi-llm/tmp/implementation_tasks_{plan_stem}_{hash8}.json``)
    so the Bash side and harness Read/Write tools resolve the same file on
    every OS. ``{hash8}`` is :func:`_plan_path_hash` of the repo-relative
    plan path: the stem alone is not unique (``plans/api/index.md`` and
    ``plans/ui/index.md`` share ``index``), and without the hash concurrent
    runs on same-stem plans would clobber each other's task JSON. The
    orchestrator is the single source of truth for this name — it prints the
    resolved path on its ``Output file:`` summary line, and
    ``instructions/implement.md`` directs Claude to read that printed path
    rather than reconstructing it (a Bash-side reimplementation of the hash
    would be a byte-identical dual-computation hazard). Never fall back to
    the system temp dir (``tempfile.gettempdir()``): on Git for Windows the
    MSYS ``/tmp`` and the native temp dir are different directories, which is
    exactly the boundary hazard this default avoids.

    Args:
        plan_path: Resolved path to the plan file (used for git-root
            detection, the ``{plan_stem}`` filename part, and the
            ``{hash8}`` disambiguator).

    Returns:
        Absolute output path as a string.

    Exits:
        With status 1 when the plan file is not inside a git work tree.
    """
    project_root = get_project_root(str(plan_path))
    if not project_root:
        print("ERROR: multi-llm requires running inside a git repository")
        print("       (the default --output path is anchored at the git root; "
              "run from within a repository or pass --output explicitly)")
        sys.exit(1)
    file_hash = _plan_path_hash(plan_path, project_root)
    return str(
        Path(project_root) / ".multi-llm" / "tmp"
        / f"implementation_tasks_{plan_path.stem}_{file_hash}.json"
    )


def _write_temp_dir_gitignore(directory: Path) -> None:
    """Make ``.multi-llm/tmp/`` self-ignoring by writing ``.gitignore`` (``*``).

    Only applies when ``directory`` actually is a ``.multi-llm/tmp`` dir (a
    user-supplied ``--output`` elsewhere must not receive a stray ignore-all
    file). Keeps transient run artifacts out of ``git status`` regardless of
    whether the consuming repo ever ran ``--init --gitignore``.
    """
    if directory.name == "tmp" and directory.parent.name == ".multi-llm":
        gitignore_path = directory / ".gitignore"
        if not gitignore_path.exists():
            gitignore_path.write_text("*\n", encoding="utf-8")


def record_pre_existing_changes(state: StateManager) -> None:
    """
    Record files already modified before implementation starts.

    This captures all uncommitted changes (staged and unstaged) present in the
    working tree at implementation startup. These are later subtracted from
    the final changed files to isolate only changes made during implementation.

    Args:
        state: StateManager instance to store the pre-existing changes
    """
    # Only record if not already recorded (avoid overwriting on --resume) —
    # by implement. `head_before_implement` is recorded right after this on
    # implement's first run, so a baseline without it was left by a planning
    # phase (apply-suggestions records one at its own start), before that
    # phase edited the plan: kept, it counted the plan edit as implement's
    # change. Implement's first run takes its own.
    if state.get("pre_existing_changes") is not None:
        if state.get("head_before_implement") is not None:
            print(f"Pre-existing changes already recorded ({len(state.get('pre_existing_changes', []))} paths)")
            return
        print(
            f"Replacing the dirty-tree baseline an earlier phase recorded "
            f"({len(state.get('pre_existing_changes') or [])} paths) with "
            f"implement's own"
        )

    # Get all modified files (staged and unstaged)
    # Filter empty strings before set union for robustness
    census_failed = False
    try:
        unstaged = set(f for f in get_modified_files() if f)
        staged = set(f for f in get_staged_files() if f)
        pre_existing = unstaged | staged
    except Exception as e:
        # Only a failed census records an empty baseline. A failed save below
        # (`StateLockTimeout` included) propagates with the baseline it was
        # saving still set: an empty one would count the user's dirty files
        # as implement's changes.
        print(f"Warning: Could not record pre-existing changes: {e}")
        pre_existing = set()
        census_failed = True

    # Sorted, as the apply phases record theirs: `state.json` must not
    # change with the set's per-process order (17 bundles of one
    # container run held 17 orders of the same 5 paths).
    state.set("pre_existing_changes", sorted(pre_existing))
    state.save()

    if census_failed:
        return
    if pre_existing:
        print(f"Recorded {len(pre_existing)} pre-existing changed paths")
    else:
        print("No pre-existing changes to record")


def load_implementation_prompt() -> str:
    """Load the implementation task prompt template."""
    try:
        return load_prompt("implementation_task.txt")
    except FileNotFoundError:
        # Fallback prompt template
        return """## Task: {task_title}

### Description
{task_description}

### Files to Consider
{relevant_files}

### Files to Create/Modify
{output_files}

### Changes Applied in Prior Batches
{{prior_changes_context}}

### Instructions
1. Implement the task as described
2. Follow existing code patterns and conventions
3. Write clean, maintainable code
4. Add appropriate error handling
5. Do NOT make git commits - the orchestrator handles git state

### Output
After implementation, describe what you did and any issues encountered.
"""


#: The one sentence that says whose job these criteria are. A plan's criteria are
#: routinely written as *manual* verification steps ("serving the repo root with
#: a local `http.server` and opening http://localhost:8000/ renders …"), and
#: pasted in unannotated a runner reads them as its own checklist: measured
#: 2026-09-16, a write subagent spent 10 of an 11-minute task driving headless
#: Chrome against a server it had started, left the server orphaned, and then
#: `killall -9 … python3`'d the detached orchestrator that dispatched it (F2).
#: Task-level manual work is already routed away from every dispatcher by
#: `executor_role == "human"`; criteria have no such marker, so they get a frame.
ACCEPTANCE_CRITERIA_FRAMING = (
    "How a human will verify the finished feature after this phase — implement "
    "so these would pass; do not attempt the browser or manual steps yourself."
)


def _checklist_bullets(criteria: List[str]) -> Tuple[List[str], int]:
    """Valid, length-capped ``- [ ] ...`` bullet lines, plus the overflow count.

    The shared core of the agent-facing acceptance-criteria section and the
    human-task checklist (N4) — both bound the same way, so the cap lives
    once.
    """
    MAX_CRITERIA = 10
    MAX_CRITERION_CHARS = 200

    # Filter out empty/whitespace-only strings
    valid = [c.strip() for c in criteria if isinstance(c, str) and c.strip()]
    overflow = max(len(valid) - MAX_CRITERIA, 0)
    items = valid[:MAX_CRITERIA]

    bullets = []
    for item in items:
        if len(item) > MAX_CRITERION_CHARS:
            item = item[:MAX_CRITERION_CHARS - 3] + "..."
        bullets.append(f"- [ ] {item}")
    return bullets, overflow


def _build_acceptance_criteria_section(criteria: List[str]) -> str:
    """Build the acceptance criteria section from a list of criteria.

    Args:
        criteria: List of acceptance criteria strings.

    Returns:
        Formatted section string, or empty string if no valid criteria.
    """
    bullets, overflow = _checklist_bullets(criteria)
    if not bullets:
        return ""

    lines = ["## Acceptance Criteria", ACCEPTANCE_CRITERIA_FRAMING, "", *bullets]

    if overflow > 0:
        lines.append(f"_(+{overflow} more criteria; see full plan)_")

    return "\n".join(lines) + "\n"


#: Rendered instead of the write-subagent template for a task whose
#: ``executor_role`` is ``"human"`` (N4, 2026-09-16). The standard template's
#: ``ACCEPTANCE_CRITERIA_FRAMING`` sentence ("do not attempt the browser or
#: manual steps yourself") and its terminal "Proceed with the implementation."
#: are both written for a write subagent, and directly contradict a task whose
#: whole job *is* the browser/manual work the framing forbids — a materialized
#: T014 once read both in the same file. (The process-safety rules the
#: template's ``## Constraints`` block once carried live only in
#: ``BatchPromptBuilder.with_result_contract`` now, appended per dispatch and never rendered
#: for a human task.)
#: Nothing dispatches a human task (``executor_role == "human"`` routes
#: around every invoker), so there is no runner to instruct: the rendered
#: entry exists only for the person who has to do the work by hand.
HUMAN_TASK_DEFERRAL_LINE = "This task is deferred to a human; nothing dispatches it."


def build_human_task_prompt(task: Task) -> str:
    """The task plus its checklist, for a task nothing ever dispatches.

    Deliberately not :func:`build_task_prompt`'s template — see
    ``HUMAN_TASK_DEFERRAL_LINE`` for why the omissions matter.
    """
    lines = ["## Task", f"Title: {task.title}", f"Description: {task.description}", ""]

    bullets, overflow = _checklist_bullets(task.acceptance_criteria or [])
    if bullets:
        lines.append("## Checklist")
        lines.extend(bullets)
        if overflow > 0:
            lines.append(f"_(+{overflow} more criteria; see full plan)_")
        lines.append("")

    lines.append(HUMAN_TASK_DEFERRAL_LINE)
    return "\n".join(lines)


def _build_dependency_section(
    task: Task,
    all_tasks: Optional[Dict[str, Task]],
) -> str:
    """Build the preceding tasks section from dependency information.

    Args:
        task: The current task being rendered.
        all_tasks: Dictionary of all tasks keyed by ID, or None.

    Returns:
        Formatted section string, or empty string if no dependencies.
    """
    MAX_DEPS = 5
    MAX_SUMMARY_CHARS = 300

    if not task.depends_on or all_tasks is None:
        return ""

    visited: set = set()
    summaries: List[str] = []

    for dep_id in sorted(task.depends_on):
        # Circular dependency guard: skip if this task's own ID appears
        if dep_id == task.id:
            logger.warning(
                "Circular dependency: task %s depends on itself; skipping",
                task.id,
            )
            continue

        # Skip duplicates
        if dep_id in visited:
            logger.warning(
                "Duplicate dependency %s in task %s; skipping",
                dep_id,
                task.id,
            )
            continue
        visited.add(dep_id)

        dep_task = all_tasks.get(dep_id)
        if dep_task is None:
            logger.warning(
                "Dependency %s not found in all_tasks for task %s; skipping",
                dep_id,
                task.id,
            )
            continue

        # Build summary: title + first line of description
        summary = f"**{dep_id}: {dep_task.title}**"
        if dep_task.description:
            first_line = dep_task.description.split("\n")[0].strip()
            if first_line:
                summary += f" - {first_line}"

        if len(summary) > MAX_SUMMARY_CHARS:
            summary = summary[:MAX_SUMMARY_CHARS - 3] + "..."

        summaries.append(summary)

        if len(summaries) >= MAX_DEPS:
            break

    if not summaries:
        return ""

    lines = ["## Preceding Tasks (already completed)"]
    for s in summaries:
        lines.append(f"- {s}")

    # Count overflow: total unique valid deps minus what we rendered
    total_valid = 0
    seen: set = set()
    for dep_id in task.depends_on:
        if dep_id == task.id or dep_id in seen:
            continue
        seen.add(dep_id)
        if all_tasks.get(dep_id) is not None:
            total_valid += 1
    overflow = total_valid - len(summaries)
    if overflow > 0:
        lines.append(f"_(+{overflow} more preceding tasks; see full plan)_")

    return "\n".join(lines) + "\n"


def _enforce_char_budget(
    acceptance_section: str,
    dependency_section: str,
    budget: int = 2000,
) -> tuple[str, str]:
    """Enforce a combined character budget on the two sections.

    Truncates dependency section first, then acceptance criteria section.

    Args:
        acceptance_section: Rendered acceptance criteria section.
        dependency_section: Rendered dependency section.
        budget: Maximum combined character count.

    Returns:
        Tuple of (acceptance_section, dependency_section) possibly truncated.
    """
    combined = len(acceptance_section) + len(dependency_section)
    if combined <= budget:
        return acceptance_section, dependency_section

    # Truncate dependency section first
    if dependency_section and len(dependency_section) > budget - len(acceptance_section):
        allowed = max(0, budget - len(acceptance_section))
        if allowed < 50:
            # Not enough room for any meaningful dependency info
            dependency_section = ""
        else:
            dependency_section = dependency_section[:allowed - 30] + "\n_(truncated)_\n"

    # If still over budget, truncate acceptance criteria
    combined = len(acceptance_section) + len(dependency_section)
    if combined > budget:
        allowed = max(0, budget - len(dependency_section))
        if allowed < 50:
            acceptance_section = ""
        else:
            acceptance_section = acceptance_section[:allowed - 30] + "\n_(truncated)_\n"

    return acceptance_section, dependency_section


def build_task_prompt(
    task: Task,
    plan_preamble: str = "",
    plan_path: str = "",
    all_tasks: Optional[Dict[str, Task]] = None,
) -> str:
    """Build the full prompt for a task.

    Args:
        task: The task to build a prompt for.
        plan_preamble: Plan context preamble text.
        plan_path: Path to the plan file.
        all_tasks: Optional dictionary of all tasks for dependency context.

    Returns:
        Formatted prompt string.
    """
    prompt_template = load_implementation_prompt()

    # Combine output files from task
    output_files = task.files_to_create + task.files_to_modify

    # Build acceptance criteria section
    acceptance_criteria_section = _build_acceptance_criteria_section(
        task.acceptance_criteria if task.acceptance_criteria else []
    )

    # Build dependency section
    dependency_section = _build_dependency_section(task, all_tasks)

    # Enforce combined budget
    acceptance_criteria_section, dependency_section = _enforce_char_budget(
        acceptance_criteria_section, dependency_section
    )

    # Use safe format that handles missing keys gracefully
    return prompt_template.format(
        task_title=task.title,
        task_description=task.description,
        relevant_files="\n".join(f"- {f}" for f in task.files_to_modify) if task.files_to_modify else "- Explore codebase as needed",
        output_files="\n".join(f"- {f}" for f in output_files) if output_files else "- Files as needed for the task",
        plan_preamble=plan_preamble if plan_preamble else "See the full plan below for context.",
        plan_path=plan_path if plan_path else "(plan path not available)",
        acceptance_criteria_section=acceptance_criteria_section,
        dependency_section=dependency_section,
    )


def format_task_for_output(
    task: Task,
    plan_preamble: str = "",
    plan_path: str = "",
    all_tasks: Optional[Dict[str, Task]] = None,
) -> Dict[str, Any]:
    """Format a task for JSON output."""
    is_human = task.executor_role == "human"
    # A human task is never dispatched (N4): its entry is the checklist a
    # person reads, not a write-subagent prompt, so it skips the template
    # that would tell them not to do the exact work this task asks for.
    prompt = (
        build_human_task_prompt(task)
        if is_human
        else build_task_prompt(task, plan_preamble, plan_path, all_tasks=all_tasks)
    )
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "prompt": prompt,
        # D2h: `executor_role` is what every reader branches on; `subagent_type`
        # rides along as optional Claude-only metadata for hosts whose native
        # Task tool requires the parameter.
        "executor_role": task.executor_role,
        "subagent_type": task.subagent_type,
        "is_human": is_human,
        "depends_on": task.depends_on,
        "files_to_modify": task.files_to_modify,
        "files_to_create": task.files_to_create,
        "complexity": task.estimated_complexity,
        "status": task.status.value,
    }


def _apply_scope_guidance(output_data: Dict[str, Any], policy: str) -> None:
    """Add the preserve block to every code task's prompt in *output_data* (in place).

    ``scope_policy_runs.implementation_guidance`` is empty under ``expand``, so
    a default run's prompts stay byte for byte what they were. A human task's
    checklist is no model prompt and is left alone.
    """
    block = scope_policy_runs.implementation_guidance(policy)
    if not block:
        return
    for batch in output_data.get("batches") or []:
        for task in batch.get("tasks") or []:
            if task.get("is_human") or not isinstance(task.get("prompt"), str):
                continue
            task["prompt"] = scope_policy_runs.with_guidance(task["prompt"], block)


def format_batches_for_output(
    batches: List[List[Task]],
    skip_completed: bool = False,
    plan_preamble: str = "",
    plan_path: str = "",
    all_tasks: Optional[Dict[str, Task]] = None,
    rerun_ids: Optional[Sequence[str]] = None,
) -> List[Dict[str, Any]]:
    """Format task batches for JSON output.

    ``skip_completed`` (i.e. ``--resume``) keeps only work that is still
    outstanding — ``pending``, ``failed`` or ``in_progress``, never a task the
    last run recorded ``completed`` — **plus every human task that is not
    itself done**. A deferred
    human task is recorded ``skipped``, not ``pending``, so a plain PENDING
    filter dropped it from the resumed run entirely: the scheduler never saw it,
    ``resolve_human_task_plan`` had no human id to resolve, and the resumed
    phase's ``write_batch_report.json`` reported ``skipped_tasks: {}`` while its
    ``summary.md`` lost the ``## Manual Tasks (Deferred)`` section that is the
    only place the finished run tells the reader what is still owed by hand. A human
    task is never dispatched by either invoker,
    so carrying it through costs the resume nothing.

    A **skipped code task** rides along for the same reason: a
    dependent skipped with a deferred manual task, or a failed task answered
    ``--human-task <id>=skip`` and its dependents, is ``skipped`` too, and
    dropping it put it in no bucket of the resumed run's account — the
    summary read ``5 — 4 done, 1 deferred manual`` for a six-task plan, the
    stop block's "that is every one of the N task(s)" was false, and
    ``write_batch_report.json``'s ``skipped_tasks`` lost the chain. The
    scheduler re-resolves the same plan from the recorded strategy and
    answers, so the task is skipped again, never dispatched.

    *rerun_ids* (``check_records.rerunnable_checks``) are ``completed``
    check tasks whose findings hold back the tasks after them, kept as well
    Dropped, the check could never run again and the tasks
    it held never ran. The executor runs it again only when the files
    changed (or on ``--human-task <id>=retry``); a native host runs it again.
    """
    output_batches = []
    rerun = {str(task_id) for task_id in (rerun_ids or ())}

    for batch_idx, batch in enumerate(batches):
        # Filter tasks if skipping completed
        tasks_to_include = batch
        if skip_completed:
            # PENDING alone dropped the task the last run recorded `failed`: a
            # clean failure or partial application stops the loop at exit 3
            # promising "--resume re-dispatches this batch", and the resumed
            # run then never materialized it, ran the rest and stamped the
            # phase completed with that task undone.
            # IN_PROGRESS is a run killed mid-dispatch — the same debt.
            tasks_to_include = [
                t for t in batch
                if t.status in (TaskStatus.PENDING, TaskStatus.FAILED,
                                TaskStatus.IN_PROGRESS, TaskStatus.SKIPPED)
                or (t.executor_role == "human"
                    and t.status != TaskStatus.COMPLETED)
                or t.id in rerun
            ]

        if not tasks_to_include:
            continue

        entries = [
            format_task_for_output(t, plan_preamble, plan_path, all_tasks=all_tasks)
            for t in tasks_to_include
        ]
        for entry in entries:
            if entry.get("id") in rerun:
                # Handed out to run again: never `completed` in the JSON a
                # native host reads, or it would pass the check over.
                entry["status"] = TaskStatus.PENDING.value
        output_batches.append({
            "batch_index": batch_idx,
            "can_parallelize": len(tasks_to_include) > 1,
            "tasks": entries,
        })

    return output_batches


def maybe_detach_implement_phase(
    args: argparse.Namespace, *, plan_path: Path
) -> Optional[int]:
    """The one detach boundary ``implement`` crosses (D4), or ``None``.

    Deliberately *outside* the ``--exec-subagents`` gate, exactly as the apply
    phases separate ``maybe_detach_write_phase`` from ``run_write_executor``:
    ``modes.py`` registers ``implement`` with ``supports_detach=True``, so the
    dispatcher accepts ``--detach`` for every implement invocation, not only the
    executor-backed one. Leaving the check under the gate made
    ``implement <plan> --detach --yes`` run in the foreground with no worker, no
    ``.status.json`` and no ``[DETACHED_RUN]`` handshake — a flag that silently
    does nothing, which is what the dispatcher's own ``supports_detach`` refusal
    exists to prevent, and a host polling ``status`` would wait forever for a run
    that was never recorded.

    It sits after every pre-flight — plan loaded, prerequisites gated, tasks
    decomposed, human-task strategy resolved, task JSON written — and before any
    child is dispatched, so a bad flag fails on the caller's terminal with no
    child and no log.

    Returns ``None`` to keep running in this process (the ordinary foreground run,
    and also the detached worker once it owns the phase dir) or an exit code the
    caller must return immediately (the invoker, after forking; or a launch
    failure).
    """
    if not (getattr(args, "detach", False)
            or getattr(args, "internal_worker", False)):
        # The foreground run replaces a damaged checkpoint (utils/detach.py,
        # `settle_foreground_checkpoint`; the worker does it in `RunHandle.start`).
        _detach.settle_foreground_checkpoint(
            str(phase_dir_path(plan_path, "implement")), phase="implement")
        return None

    phase_dir = str(get_phase_dir(plan_path, "implement"))
    Path(phase_dir).mkdir(parents=True, exist_ok=True)
    return review_orchestrator_base.maybe_detach(
        args=args, mode="implement", phase_dir=phase_dir,
        plan_file=str(plan_path.absolute()), phase="implement",
    )


def _applicable_task_decisions(
    recorded: Mapping[str, str],
    statuses: Mapping[str, str],
    held_by: Collection[str],
    human_task_ids: Collection[str],
    this_run: Mapping[str, str],
    *,
    rerun_task: Optional[str] = None,
) -> Dict[str, str]:
    """The ``--human-task`` answers the scheduler applies this run.

    *recorded* is ``state.json``'s ``human_task_decisions``, *statuses* its
    ``task_status`` and *held_by* the checks whose findings hold back the tasks
    after them (``rerunnable_checks``); :func:`_applicable_from_state` reads
    the three from a :class:`StateManager`.

    Every recorded answer for a human task (they persist, so ``--resume``
    never re-asks), plus this run's ``retry`` answers (one-shot, never
    recorded) and a recorded ``done``/``skip`` for a code task only while
    the state still says that task ``failed`` — or, for ``skip``, ``skipped``:
    the answer that skipped it is what keeps it skipped on the next resume,
    now that a skipped code task is materialized again. Once
    it ran again or was accepted, a stale answer must not mark it done
    behind the user's back — and once its task has a status the answer did
    not write, it is gone from the record (``state_manager._consume_answer``).

    *rerun_task* is ``--task <id>``: the user asked to run that code task,
    so an answer an earlier run recorded for it does not apply (a recorded
    ``skip`` used to leave ``--task`` nothing to hand out);
    the status its run writes retires the answer.
    """
    recorded = dict(recorded)
    if rerun_task and rerun_task not in human_task_ids and rerun_task not in this_run:
        recorded.pop(rerun_task, None)
    decisions: Dict[str, str] = {}
    # A check whose findings hold back the tasks after it is answered like a
    # failed task, until the answer is taken.
    held_by = set(held_by)
    for task_id, action in recorded.items():
        status = statuses.get(task_id)
        if task_id in human_task_ids:
            decisions[task_id] = action
        elif (
            status == "failed" or task_id in held_by
            or (action == "skip" and status == "skipped")
        ):
            decisions[task_id] = action
    for task_id, action in this_run.items():
        if action == "retry" and task_id not in human_task_ids:
            decisions[task_id] = action
    return decisions


def _applicable_from_state(
    state: StateManager,
    human_task_ids: Collection[str],
    this_run: Mapping[str, str],
    *,
    rerun_task: Optional[str] = None,
) -> Dict[str, str]:
    """:func:`_applicable_task_decisions` over what *state* records."""
    return _applicable_task_decisions(
        dict(state.get("human_task_decisions") or {}),
        state.get_all_task_statuses(),
        rerunnable_checks(state.state),
        human_task_ids, this_run, rerun_task=rerun_task,
    )


def _prepare_selected_task(
    task: Task, state: StateManager, plan_path: Path, *, dry_run: bool,
) -> None:
    """Hand an explicit code-task rerun out pending on either write leg.

    A completed task starts a new attempt, so its successful result and old
    rollback point are retained aside rather than reused. This also makes
    an interrupted native handoff resumable by the executor without trusting
    the previous run's result. A failed task keeps its original snapshot:
    retrying partial work must still be able to restore its first baseline.
    """
    if task.executor_role == "human":
        return
    task.status = TaskStatus.PENDING
    if dry_run:
        return
    if state.get_task_status(task.id) == TaskStatus.COMPLETED.value:
        phase_dir = get_phase_dir(plan_path, "implement")
        stamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
        snapshot = TaskSnapshot.load(
            str(phase_dir), task.id,
            expected_root=_write_safety.resolve_repo_root(str(plan_path)),
        )
        if snapshot is not None:
            directory = Path(snapshot.directory)
            directory.rename(directory.with_name(f"{directory.name}.rerun-{stamp}"))
        result = phase_dir / implement_output_name(task.id)
        if result.exists():
            result.rename(result.with_name(f"{result.name}.rerun-{stamp}"))
    state.update_task_status(task.id, TaskStatus.PENDING.value)
    # A fresh result replaces these; until then the old verdict is not the
    # selected attempt's verdict, including after a host dies mid-handoff.
    clear_task_verdict(state.state, task.id)
    # The log line its earlier run wrote is not this rerun's
    # (`batch_done.unrecorded_logged_batches`): a host gone before its
    # `batch-done` left T001 refused on the next plain emit.
    mark_tasks_reset_in_state(state.state, [task.id])
    state.mark_phase_started("implement")
    state.save()


def _start_over(
    state: StateManager, plan_path: Path, tasks: Iterable[Task],
) -> None:
    """Set aside what earlier runs recorded for each code task, and record
    implement started.

    A start-over (``--fresh``, or a plain run on an implement that finished)
    hands every task out again. It used to leave the earlier run's records in
    place: a task this run did not reach before it stopped still read
    ``completed``, beside its result file and pre-batch snapshot, so a later
    ``--resume`` (typed, or a plain run continuing this one) kept it on the
    evidence of a run before; and the executor leg, which never recorded
    implement started, let the next plain run start over yet again once an
    implement had finished. For every code task of the decomposition (a
    manual task's answer stands):

    * its status, including a code task skipped at the user's request or
      with another task, goes back to ``pending`` without a reason — a recorded
      ``--human-task`` answer for it goes with it
      (``state_manager._consume_answer``) — and its verdict (check findings,
      check tree stamp, own-check records: ``state_manager.TASK_VERDICT_KEYS``)
      is dropped;
    * its result file is kept as ``<name>.rerun-<stamp>`` and its pre-batch
      snapshot set aside beside its slot (``TaskSnapshot.set_aside``, what
      the executor's own start-over does to a slot it dispatches into),
      never deleted;
    * its reset is stamped (``state_manager.TASK_RESET_AT_KEY``), so a native
      ``--resume`` does not read the earlier run's prior-changes line as one
      this run left unrecorded.

    The prompts kept in ``{phase}/prompts/`` are removed
    (:func:`_remove_kept_prompts`), and implement is recorded started on both
    legs, as the native emit records it.

    A first implement has nothing to set aside, and this writes nothing then
    See
    :func:`_has_earlier_implement_records`.
    """

    phase_dir = get_phase_dir(plan_path, "implement")
    stamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    code_ids = [
        str(task.id) for task in tasks
        if getattr(task, "executor_role", "") != "human"
    ]
    try:
        repo_root: Optional[str] = _write_safety.resolve_repo_root(str(plan_path))
    except WriteSafetyError as exc:
        repo_root = None
        print(
            f"WARNING: start over: the pre-batch snapshots are left in place: "
            f"{exc.message}", file=sys.stderr,
        )
    if not _has_earlier_implement_records(state, phase_dir, code_ids, repo_root):
        return
    set_aside: List[str] = []
    for task_id in code_ids:
        touched = False
        result = phase_dir / implement_output_name(task_id)
        if result.exists() or result.is_symlink():
            result.rename(result.with_name(f"{result.name}.rerun-{stamp}"))
            touched = True
        if repo_root is not None:
            try:
                snapshot = TaskSnapshot.load(
                    str(phase_dir), task_id, expected_root=repo_root)
                if snapshot is not None and snapshot.set_aside():
                    touched = True
            except (WriteSafetyError, OSError) as exc:
                print(
                    f"WARNING: start over: {task_id}'s pre-batch snapshot is "
                    f"left in place: {getattr(exc, 'message', exc)}",
                    file=sys.stderr,
                )
        status = state.get_task_status(task_id)
        if status not in (None, TaskStatus.PENDING.value):
            touched = True
            state.update_task_status(task_id, TaskStatus.PENDING.value)
        elif status == TaskStatus.PENDING.value and state.get_task_status_reason(task_id):
            # A reason an earlier run gave it (held behind a check) is not
            # this run's.
            state.update_task_status(task_id, TaskStatus.PENDING.value)
        clear_task_verdict(state.state, task_id)
        if touched:
            set_aside.append(task_id)
    mark_tasks_reset_in_state(state.state, code_ids)
    removed = _remove_kept_prompts(phase_dir)
    state.mark_phase_started("implement")
    state.save()
    if set_aside:
        named = ", ".join(set_aside[:8]) + (", …" if len(set_aside) > 8 else "")
        print(
            f"start over: this run hands every task out again, so what an "
            f"earlier run recorded for {named} is set aside (each is pending "
            f"again; a result file is kept as <its name>.rerun-{stamp} and a "
            f"pre-batch snapshot beside its slot), and a later --resume keeps "
            f"only what this run finishes."
        )
    if removed:
        print(
            f"start over: removed {removed} prompt file(s) an earlier run kept "
            f"in {phase_dir}/prompts/."
        )


def _has_earlier_implement_records(
    state: StateManager, phase_dir: Path, code_ids: Sequence[str],
    repo_root: Optional[str],
) -> bool:
    """Whether an earlier implement left anything a start-over sets aside.

    Read-only, and the same records :func:`_start_over` acts on: a status
    other than ``pending`` without a reason, a check finding, check tree
    stamp or own-check finding, a result file, a pre-batch snapshot, for any
    code task in *code_ids*; a line the prior-changes log holds for one of
    them under implement; a kept prompt. Absent all of these the run is the
    plan's first implement, and starting it over would only stamp resets and
    a started record for work that never ran. A
    snapshot that cannot be read counts as a record, so the start-over that
    would warn about it still runs.
    """

    ids = set(code_ids)
    for task_id in code_ids:
        status = state.get_task_status(task_id)
        if status not in (None, TaskStatus.PENDING.value) or (
            status == TaskStatus.PENDING.value
            and state.get_task_status_reason(task_id)
        ):
            return True
    for key in (TASK_CHECK_FINDINGS_KEY, TASK_CHECK_TREES_KEY, TASK_BATCH_CHECK_KEY):
        recorded = state.get(key)
        if isinstance(recorded, dict) and ids & {str(k) for k in recorded}:
            return True
    for task_id in code_ids:
        result = phase_dir / implement_output_name(task_id)
        if result.exists() or result.is_symlink():
            return True
        if repo_root is not None:
            try:
                if TaskSnapshot.load(
                    str(phase_dir), task_id, expected_root=repo_root,
                ) is not None:
                    return True
            except (WriteSafetyError, OSError):
                return True
    try:
        logged = _prior_changes.entries(str(phase_dir.parent))
    except Exception:  # noqa: BLE001 - an unreadable log is a record
        return True
    implement = _prior_changes.canonical_phase("implement")
    if any(
        _prior_changes.canonical_phase(entry.get("phase")) == implement
        and str(entry.get("id") or "") in ids
        for entry in logged
    ):
        return True
    prompts = phase_dir / DISPATCHED_PROMPTS_SUBDIR
    try:
        return prompts.is_dir() and any(
            name.endswith(".prompt.txt") for name in os.listdir(prompts)
        )
    except OSError:
        return True


def _remove_kept_prompts(phase_dir: Path) -> int:
    """Remove the ``*.prompt.txt`` files in ``{phase}/prompts/``; how many.

    The batch prompts each dispatch keeps (``<id>.prompt.txt``, and
    ``<id>.attempt-<n>.prompt.txt`` for a re-ask) are one run's: after a
    start-over, a task the new run refuses before dispatch must have none. Anything else
    in the folder — a
    check's ``<id>.tree.json``, which the native leg binds there — stays.

    A jailed repo-wide batch can write the phase dir, so nothing here
    follows a link: the phase dir and ``prompts/`` are opened
    ``O_DIRECTORY | O_NOFOLLOW`` (a symlink there removes nothing), each name
    is checked with ``lstat`` relative to that descriptor and removed only
    when it is a regular file, by ``unlink(dir_fd=…)``. A platform without
    ``dir_fd`` (Windows, where no jail runs) holds handles instead
    (:func:`_remove_kept_prompts_windows`); it used to remove nothing, so a
    start-over there kept every earlier prompt (Windows port, round seven).
    """

    nofollow = getattr(os, "O_NOFOLLOW", 0)
    directory = getattr(os, "O_DIRECTORY", 0)
    if not nofollow or not directory or os.unlink not in os.supports_dir_fd:
        # Windows only: there no jail runs, so a path walk is as safe as the
        # descriptors. A POSIX build without them keeps removing nothing — it
        # may be under one, and a path is what a jailed write can swap.
        return _remove_kept_prompts_windows(phase_dir) if os.name == "nt" else 0

    flags = os.O_RDONLY | directory | nofollow
    try:
        phase_fd = os.open(str(phase_dir), flags)
    except OSError:
        return 0
    try:
        try:
            folder_fd = os.open(DISPATCHED_PROMPTS_SUBDIR, flags, dir_fd=phase_fd)
        except OSError:
            return 0
    finally:
        os.close(phase_fd)
    removed = 0
    try:
        for name in os.listdir(folder_fd):
            if not name.endswith(".prompt.txt"):
                continue
            try:
                info = os.stat(name, dir_fd=folder_fd, follow_symlinks=False)
                if not _stat.S_ISREG(info.st_mode):
                    continue
                os.unlink(name, dir_fd=folder_fd)
            except OSError:
                continue
            removed += 1
    finally:
        os.close(folder_fd)
    return removed


def _remove_kept_prompts_windows(phase_dir: Path) -> int:
    """:func:`_remove_kept_prompts` on Windows: through handles held open for
    the whole walk (``utils.prompt_files.remove_held``), so no folder can be
    swapped for a junction between a check and a removal, and a folder that
    OneDrive or a ProjFS checkout tagged is walked rather than taken for a
    link (round-8 review). The path walk is what is left where that walk
    cannot be made at all (the calls cannot be loaded, a folder cannot be
    opened, a volume without a drive letter)."""

    removed = prompt_files.remove_held(
        str(phase_dir), lambda name: name.endswith(".prompt.txt"),
    )
    return _remove_kept_prompts_by_path(phase_dir) if removed is None else removed


def _remove_kept_prompts_by_path(phase_dir: Path) -> int:
    """:func:`_remove_kept_prompts_windows` where its calls cannot be loaded,
    the way ``utils.prompt_files`` writes there: the phase dir and
    ``prompts/`` are ``lstat``-checked and a link or a junction there removes
    nothing, each name is ``lstat``-checked and removed only when it is a
    regular file. Nothing is held between a check and its removal. Best-effort,
    like the descriptor walk."""

    reparse = getattr(_stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    folder = os.path.join(str(phase_dir), DISPATCHED_PROMPTS_SUBDIR)
    try:
        for shown in (str(phase_dir), folder):
            info = os.lstat(shown)
            if (
                not _stat.S_ISDIR(info.st_mode)
                or getattr(info, "st_file_attributes", 0) & reparse
            ):
                return 0
        names = os.listdir(folder)
    except OSError:
        return 0
    removed = 0
    for name in names:
        if not name.endswith(".prompt.txt"):
            continue
        path = os.path.join(folder, name)
        try:
            if not _stat.S_ISREG(os.lstat(path).st_mode):
                continue
            os.unlink(path)
        except OSError:
            continue
        removed += 1
    return removed


def _manual_close_note(
    args: argparse.Namespace, plan_arg: str, task_ids: Sequence[str],
    *, waiting: int = 0,
) -> Optional[str]:
    """``next_phase.manual_close_note`` for *task_ids*, in this host's own
    command spelling (the template the result line's ``user_next_step``
    uses); ``None`` when nothing can be spelled. *waiting*: how many code
    tasks wait on them."""

    try:
        host_id = _hosts.resolve_host_id(explicit=getattr(args, "host", None))
        template = _hosts.next_command_template(
            host_id, _routes.resolve_route(host_id, stderr=io.StringIO()))
        return _manual.manual_close_note(
            _manual.close_command(template, plan_arg, task_ids), len(task_ids),
            waiting=waiting)
    except Exception:  # noqa: BLE001 - advisory: the deferred list still stands
        return None


def _native_manual_gates(
    plan: Any, output_data: Dict[str, Any], state: StateManager,
) -> Optional[Dict[str, Any]]:
    """``human_task_plan.plan_manual_gates`` over the native handoff's
    tasks, the recorded decomposition and ``state.json`` as it stands (the
    emit has not persisted *plan* yet); ``None`` when it cannot be read.

    A code task this emit hands out is not done yet. It used to count as done, so the
    note named a manual task
    that comes after it as one the user can do, and the host copied that
    note into summary.md even when the task then failed, while ``status``
    and ``util next-command`` said the manual task comes after it. Such a
    manual task is ``after`` here: the emit lists it with what it comes
    after, and the report's lookup, made once the batches are recorded,
    gives its command."""
    try:
        entries = [
            task for batch in output_data.get("batches") or []
            for task in batch.get("tasks") or []
        ]
        nodes = [
            {
                "task_id": str(task.get("id") or ""),
                "depends_on": list(task.get("depends_on") or []),
                "executor_role": task.get("executor_role"),
                "is_human": task.get("is_human"),
            }
            for task in entries
        ]
        return plan_manual_gates(
            plan, decomposition_graph(nodes, state.state),
            dict(state.get_all_task_statuses()))
    except Exception:  # noqa: BLE001 - advisory wording, never fatal
        return None


def _native_manual_gate_stop(
    plan: Any, output_data: Dict[str, Any], state: StateManager,
) -> Optional[Tuple[List[str], str, str]]:
    """``(lines, headline, closing [ETA] line)`` of a native emit that hands
    out nothing because every code task left waits on a manual task not
    recorded done, one the user can do now among them; ``None`` otherwise. The words
    are the executor stop's."""
    gates = _native_manual_gates(plan, output_data, state)
    if not gates or not gates.get("gated") or not gates.get("waiting"):
        return None

    titles = dict(state.get("task_titles") or {})
    waiting = {k: list(v) for k, v in sorted(gates["waiting"].items()) if v}
    gating = sorted(waiting)
    held = sorted({code for codes in waiting.values() for code in codes})

    def label(task_id: str) -> str:
        title = titles.get(task_id)
        return f" ({clip(str(title), 80)})" if title else ""

    it = "it" if len(gating) == 1 else "them"
    head = manual_gate_head("implement", {t: label(t) for t in gating}, waiting)
    headline = f"{head}. {manual_gate_way_on(gating)}"
    # The: the line the report relays says what stopped
    # and why, as the tool routes' line beside the section does; the way on
    # is the section's resume alone (the result line's `error` keeps it).
    lines = [
        f"[MANUAL_GATE] {head}.",
    ]
    for task_id in gating:
        codes = waiting[task_id]
        lines.append(
            f"  {task_id}{label(task_id)}: {len(codes)} code task(s) wait on it "
            f"({', '.join(codes)})")
    lines.append(
        "Nothing is handed out, and implement is not finished: spawn no "
        "subagent, write no implementation summary and run no `util metrics` "
        "or `util finalize-tracking`. Report the deferred tasks above, then end "
        "the report with the section `util next-command` prints: the resume "
        "that records the manual task done, which runs the code tasks waiting "
        "on it, and the answer that skips them if the user will not do it.")
    eta = metrics_mod.closing_line(
        "implement", done=0, total=0,
        why=(f"{', '.join(gating)} left for you (manual); {len(held)} code "
             f"task(s) wait on {it}"))
    return lines, headline, eta


def _refuse_answer(message: str) -> int:
    """Refuse a ``--human-task`` answer: exit 3, the message on stderr and,
    whole, as the result line's ``error`` (a refused answer printed its reason on stderr
    alone, and the tool routes
    said the result line named no error)."""
    record_error(message.replace("ERROR: ", "", 1))
    return unattended_mod.fail_closed(
        message, site_id=unattended_mod.row(9).site_id,
    )


def _stop_user_commands(args: argparse.Namespace) -> Dict[str, str]:
    """The way forward after a stop, in this host's own command spelling.

    Built from the host's ``next_command`` template the way the result line's
    ``user_next_step`` and ``resume_command`` are (``next_phase_words.phase_command``),
    with the plan as the user typed it (the run record's ``plan_arg``, else
    the ``--plan-file`` value). Empty when nothing can be spelled (no template
    for this host and route): the stop message then names the flags.
    """
    try:
        host_id = _hosts.resolve_host_id(explicit=getattr(args, "host", None))
        route = _routes.resolve_route(host_id)
        handle = _detach.active_run()
        plan_arg = (
            (handle.plan_arg if handle is not None else None)
            or os.environ.get(_detach.PLAN_ARG_ENV)
            or str(args.plan_file)
        )

        def command(mode: str, *flags: str) -> str:
            return _words.phase_command(plan_arg, host_id, route, mode, *flags)

        return {
            "resume": command("implement", "--resume"),
            "review": command("review-code"),
            "fix": command("apply-code-fixes"),
            "accept": command("implement", "--resume", "--human-task", "{task_id}=done"),
            "skip": command("implement", "--resume", "--human-task", "{task_id}=skip"),
            "retry": command("implement", "--resume", "--human-task", "{task_id}=retry"),
            # One resume carrying several answers (a stop that
            # needs a check's findings accepted and a refused task skipped).
            "answers": command("implement", "--resume", "{answers}"),
        }
    except Exception:  # noqa: BLE001 - advisory: the flags are named instead
        return {}


def _seed_pending_task_statuses(state: StateManager, tasks: List[Dict[str, Any]]) -> None:
    """F5: give every materialized task a ``pending`` status before dispatch.

    ``WriteBatchScheduler`` only calls ``state.update_task_status`` when a task
    finishes or is skipped (``write_batch_scheduler.py:1864,2129``) — nothing
    seeds the map before the loop starts. On a 14-task plan that made
    ``check_workflow_prerequisites``' denominator (``len(task_status)``) read
    "tasks recorded so far" instead of "tasks in the plan": a workflow snapshot
    taken mid-run showed ``(1/2 tasks)`` and later ``(6/7 tasks)`` on the same
    14-task implement phase. Only a task with no status yet is touched — a
    ``--resume`` restores completed/failed/skipped statuses from disk before
    this runs, and re-marking one of those ``pending`` would erase it.
    """
    seeded = False
    for task in tasks:
        task_id = str(task.get("task_id") or "")
        if task_id and state.get_task_status(task_id) is None:
            state.update_task_status(task_id, TaskStatus.PENDING.value)
            seeded = True
    if seeded:
        state.save()


def _record_implement_write_artifacts(
    *,
    phase_dir: str,
    output_dir: str,
    task_file: str,
    plan_file: str,
    result: Any,
) -> None:
    """Hand back the files this phase produced (F7).

    ``implement`` never goes through ``ApplyOrchestratorBase`` — this function
    drives ``WriteBatchScheduler`` directly — so it never got that base's
    ``record_write_artifacts``: a fully completed detached run's result line
    said ``"artifacts": []`` and ``status`` had no ``output_files:`` block,
    unlike every apply phase. This mirrors ``ApplyPhaseReport.
    record_write_artifacts``'s shape (same two channels: ``record_output_files``
    feeds ``.status.json`` for ``status``, ``record_artifacts`` feeds the
    terminal ``MULTI_LLM_RESULT`` line) for the files implement itself writes,
    plus the file(s) the write executor actually verified changed
    (``files_touched`` on every ``ok`` outcome — e.g. ``index.html``), never the
    runner's own claim. Every path is existence-guarded, so a stopped run names
    only what it produced.

    ``files_touched`` entries are the pinned-repo-root-relative paths
    ``TaskSnapshot.changed()`` records (D3f/D3h), not paths relative to this
    process's own cwd — a host can invoke ``implement`` from anywhere, and
    checking existence against the wrong root would silently drop every touched
    file. Resolved against the same ``write_safety.resolve_repo_root`` anchor
    the scheduler itself pins the write path to, never the process cwd.
    """
    paths: Dict[str, str] = {"write_tasks": task_file}
    report_path = getattr(result, "report_path", None)
    paths["write_batch_report"] = report_path or os.path.join(
        phase_dir, "write_batch_report.json"
    )
    # The executor's own per-dispatch report (BatchReport.write(), F9/D3i) —
    # `implement` is not one of the kinds that shares a phase dir
    # (KINDS_SHARING_A_WRITE_PHASE_DIR), so its filename is the bare one.
    paths["subagent_batch_report"] = os.path.join(
        phase_dir, "subagent_batch_report.json"
    )
    paths["prior_changes"] = os.path.join(output_dir, "prior_changes.jsonl")
    summary_file = getattr(result, "summary_file", None)
    paths["summary"] = summary_file or os.path.join(phase_dir, "summary.md")

    repo_root = _write_safety.repo_root_for_report(plan_file)

    touched = touched_files(getattr(result, "outcomes", None) or [], include_partial=False)
    for index, touched_path in enumerate(touched, start=1):
        # The report's `/`-spelled relative path, joined natively: on Windows a
        # bare join gave `C:\repo\src/main.py`, a second spelling of the file.
        resolved = (
            touched_path if os.path.isabs(touched_path)
            else os.path.join(repo_root, os.path.normpath(touched_path))
        )
        paths[f"touched_file_{index}"] = resolved

    _detach.record_output_files(phase_dir, **paths)
    record_artifacts(path for path in paths.values() if path and os.path.exists(path))


def check_findings_notice(found: Dict[str, List[str]]) -> str:
    """The result line's ``notice`` for check tasks that reported problems.

    Bounded: one line a host relays, naming each task, how many problems its
    check reported and the first of them, and where the rest are.
    """
    parts = []
    for task_id, findings in found.items():
        first = findings[0] if findings else ""
        more = f" (+{len(findings) - 1} more)" if len(findings) > 1 else ""
        parts.append(f"{task_id}: {clip(first, 160)}{more}")
    return clip(
        "check findings (review-code is told about them; all listed in "
        "implement/summary.md): "
        + join_clauses(parts), 900)


def run_implement_write_phase(
    args: argparse.Namespace,
    *,
    plan_path: Path,
    state: StateManager,
    output_data: Dict[str, Any],
    human_task_strategy: Optional[str],
    human_task_decisions: Dict[str, str],
    tasks_file: Optional[Path] = None,
) -> Optional[int]:
    """Schedule the implement batches through the write executor, or decline (D3n).

    Returns ``None`` when neither ``--exec-subagents`` nor
    ``--dry-run-subagents`` was passed, so the caller falls through to today's
    "emit task JSON, let the driving agent run it" path unchanged. That is the
    additivity guarantee: with the flag off, nothing in this function runs.

    When it does run it owns the whole phase: ``batch_index`` ordering with
    verification gating the next dispatch, the resolved human-task strategy, the
    per-batch snapshot/classify/append/record cycle, and finalization
    (``mark_phase_completed`` + ``finalize_tracking`` + the implementation summary
    + the plan-side reference). Its exit code is the phase's.

    The detach boundary is **not** here: it is
    :func:`maybe_detach_implement_phase`, which the caller crosses just above this
    call so ``--detach`` works on every implement invocation rather than only the
    executor-backed one.

    ``tasks_file`` (F15) is the external ``tasks/tasks.md`` this run's prompts
    were actually parsed from, when the plan carries a ``TASKS_FILE`` marker —
    ``None`` for the legacy embedded-task format. Threaded into the two
    materializer calls so ``write_tasks.json`` records ``inputs.tasks_sha256``
    the way ``review-tasks`` and ``apply-task-suggestions`` already do, and a
    hand-edited tasks file invalidates a stored ``write_tasks.json`` on
    ``--resume`` the same way an edited plan does.
    """
    if not (getattr(args, "exec_subagents", False)
            or getattr(args, "dry_run_subagents", False)):
        return None

    phase_dir = str(get_phase_dir(plan_path, "implement"))
    Path(phase_dir).mkdir(parents=True, exist_ok=True)
    plan_file = str(plan_path.absolute())
    output_dir = str(get_output_dir(plan_path))
    tasks_file_str = str(tasks_file) if tasks_file else None

    tasks = write_phase_bridge.materialize_write_tasks(
        kind="implement",
        batches=output_data.get("batches") or [],
        phase_dir=phase_dir,
        plan_file=plan_file,
        tasks_file=tasks_file_str,
    )
    task_file = write_phase_bridge.write_task_file_for_phase(
        kind="implement", tasks=tasks, phase_dir=phase_dir, plan_file=plan_file,
        tasks_file=tasks_file_str,
    )
    print(f"[write-subagents] materialized {len(tasks)} implement task(s): {task_file}")

    # F5: seed before the scheduler loop starts, not inside it — see the
    # function's own docstring.
    _seed_pending_task_statuses(state, tasks)

    try:
        scheduler = write_batch_scheduler.WriteBatchScheduler(SchedulerOptions(
            tasks=tasks,
            phase_dir=phase_dir,
            kind="implement",
            output_dir=output_dir,
            state=state,
            plan_file=plan_file,
            summary_file=output_data.get("summary_file"),
            summary_file_relative=output_data.get("summary_file_relative"),
            anchor=plan_file,
            resume=bool(getattr(args, "resume", False)),
            dry_run=bool(getattr(args, "dry_run_subagents", False)),
            human_task_strategy=human_task_strategy,
            human_task_decisions=human_task_decisions,
            user_commands=_stop_user_commands(args),
        ))
    except _write_safety.WriteSafetyError as exc:
        # A repository root that cannot be pinned (a planted `core.worktree`,
        # review fixes 2026-10-05) is exit 3 with the resolver's own words.
        print(f"ERROR: {exc.message}", file=sys.stderr)
        return int(getattr(exc, "exit_code", 3) or 3)
    result = scheduler.run()
    for line in result.messages:
        print(line, file=sys.stderr if result.exit_code else sys.stdout)
    stop = getattr(result, "stop", None) or {}
    if stop.get("headline"):
        # The result line's `error`: the one line the hosts relay as "the
        # last line it left", and the detached close-out's `run.error`.
        record_error(stop["headline"])
    found = result.check_findings() if hasattr(result, "check_findings") else {}
    notice = [check_findings_notice(found)] if found else []
    # A task whose own check failed after its edits, and a run
    # nothing verified, are on the same line.
    extra = write_result_notice(result) if hasattr(result, "report_rows") else None
    if extra:
        notice.append(extra)
    if notice:
        # Racing re-run 4: a check task's problems were on no
        # surface a host reads. The result line's `notice` carries them,
        # beside the `[CHECK_FINDINGS]` lines above.
        # Joined so a clause gives up its
        # closing stop to the separator, never ".;".
        record_notice(join_clauses(notice))
    if result.report_path:
        print(f"[write-subagents] report: {result.report_path}")
    if result.summary_file:
        print(f"[write-subagents] implementation summary: {result.summary_file}")
    _record_implement_write_artifacts(
        phase_dir=phase_dir, output_dir=output_dir, task_file=task_file,
        plan_file=plan_file, result=result,
    )
    return result.exit_code


def _materialize_native_write_tasks(
    plan_path: Path, output_data: Dict[str, Any], *, tasks_file: Optional[Path],
    host: Optional[str] = None,
) -> Tuple[str, List[Dict[str, Any]]]:
    """Write ``{phase}/write_tasks.json`` for the native leg; its path and tasks.

    The same two bridge calls :func:`run_implement_write_phase` makes, with
    the same inputs, so the file a native host's ``util write-prompt`` reads
    is the one the executor leg would have dispatched from. Stamped native
    with *host*, so ``status`` shows this run rather than an
    earlier executor run's ``.status.json``.
    """

    phase_dir = str(get_phase_dir(plan_path, "implement"))
    plan_file = str(plan_path.absolute())
    tasks_file_str = str(tasks_file) if tasks_file else None
    tasks = write_phase_bridge.materialize_write_tasks(
        kind="implement",
        batches=output_data.get("batches") or [],
        phase_dir=phase_dir,
        plan_file=plan_file,
        tasks_file=tasks_file_str,
    )
    path = write_phase_bridge.write_task_file_for_phase(
        kind="implement", tasks=tasks, phase_dir=phase_dir, plan_file=plan_file,
        tasks_file=tasks_file_str, native_host=host or "claude-code",
    )
    return path, tasks


def _native_human_task_plan(
    output_data: Dict[str, Any],
    *,
    strategy: Optional[str],
    decisions: Dict[str, str],
    on_record: Optional[Any] = None,
    recorded_statuses: Optional[Dict[str, str]] = None,
    check_findings_ids: Optional[Sequence[str]] = None,
    state_record: Optional[Dict[str, Any]] = None,
):
    """Resolve the human-task plan over the native leg's batches; annotate them.

    The same ``resolve_human_task_plan`` the executor runs over the same
    tasks. Every task the plan skips (a deferred manual task, and under
    ``skip-dependents`` each task that depends on one) gets
    ``status: "skipped"`` and its ``skip_reason`` in the task JSON, a manual
    task answered ``done`` gets ``status: "completed"``, and the JSON gains a
    top-level ``skipped_tasks`` map: the host reads that it must not
    dispatch them instead of re-deriving the walk. With no strategy yet (an
    attended run, before the host asks) nothing is skipped.

    A failed code task the user accepted (``--human-task <id>=done`` on a
    resume) is **taken out of the batches**, exactly as a completed task is,
    and named in a top-level ``accepted_tasks`` map with its reason: a task
    left in the batches is one the host dispatches, and until
    the native leg recorded the acceptance in ``state.json`` while handing
    the task out again as ``failed`` — whose ``util batch-done`` then
    overwrote the acceptance (reviewer repro, 2026-10-05).

    *on_record* is ``human_task_plan.answered_done_on_record``'s
    ``(accepted, completed_manual)`` for the tasks this emit did not
    materialize: an answer an earlier run recorded keeps its place in
    ``accepted_tasks``, and a manual task answered ``done`` is named in a
    top-level ``completed_manual_tasks`` list, on every later resume too
    (both dropped out once the task was recorded completed).

    A task *recorded_statuses* (``state.json``'s ``task_status``) says
    ``skipped`` that this plan no longer skips — ``--resume --force-strategy
    skip-continue`` after a ``skip-dependents`` run — is handed out
    ``pending`` and recorded so (``human_task_plan.mark_no_longer_skipped``),
    never left ``skipped`` for the host to pass over.
    """

    batches = output_data.get("batches") or []
    check_findings_ids = list(check_findings_ids or ())
    entries = [task for batch in batches for task in batch.get("tasks") or []]
    nodes = [
        {
            "task_id": task.get("id"),
            "task_title": task.get("title"),
            "executor_role": task.get("executor_role"),
            "is_human": task.get("is_human"),
            "depends_on": list(task.get("depends_on") or []),
        }
        for task in entries
    ]
    plan = resolve_human_task_plan(
        nodes,
        strategy=strategy,
        decisions=decisions,
        check_findings_ids=check_findings_ids,
        # The whole decomposition: a resume's batches lack
        # the finished tasks a skip's walk must go through.
        graph=decomposition_graph(nodes, state_record),
    )
    for task in entries:
        task_id = str(task.get("id") or "")
        if task_id in plan.skipped:
            task["status"] = TaskStatus.SKIPPED.value
            task["skip_reason"] = plan.skipped[task_id]
        elif task_id in plan.completed:
            task["status"] = TaskStatus.COMPLETED.value
    unskipped = set(mark_no_longer_skipped(
        plan,
        [str(task.get("id") or "") for task in entries],
        {
            **(recorded_statuses or {}),
            **{
                str(task.get("id") or ""): task.get("status")
                for task in entries if task.get("status") == TaskStatus.SKIPPED.value
            },
        },
    ))
    for task in entries:
        if str(task.get("id") or "") in unskipped:
            task["status"] = TaskStatus.PENDING.value
            task.pop("skip_reason", None)
    if on_record:
        accepted, completed_manual = on_record
        for task_id, reason in accepted.items():
            plan.accepted.setdefault(task_id, reason)
        for task_id in completed_manual:
            if task_id not in plan.completed:
                plan.completed.append(task_id)
    if plan.skipped:
        output_data["skipped_tasks"] = dict(sorted(plan.skipped.items()))
    if plan.completed:
        output_data["completed_manual_tasks"] = sorted(plan.completed)
    if plan.accepted:
        kept = []
        for batch in batches:
            batch["tasks"] = [
                task for task in batch.get("tasks") or []
                if str(task.get("id") or "") not in plan.accepted
            ]
            if batch["tasks"]:
                batch["can_parallelize"] = len(batch["tasks"]) > 1
                kept.append(batch)
        output_data["batches"] = kept
        output_data["accepted_tasks"] = dict(sorted(plan.accepted.items()))
        if "pending_tasks" in output_data:
            output_data["pending_tasks"] = sum(len(b["tasks"]) for b in kept)
    return plan


def _native_check_reruns(
    state: StateManager,
    plan_path: Path,
    checks: Sequence[str],
    decisions: Dict[str, str],
) -> Tuple[List[str], Dict[str, List[str]]]:
    """``(checks handed out again, checks kept)`` for a native ``--resume``.

    The native leg handed every
    check whose findings hold tasks back out again on every ``--resume``, so a
    resume the user changed nothing for spent a new subagent (~23k tokens) on
    the same findings — the executor refuses that run
    (``CheckHolds.check_findings_rerun``). A check is kept — not in
    the batches, its findings standing, the tasks after it held — when the
    files git sees are the ones its stamp recorded
    (``state.json``'s ``task_check_trees``: ``util batch-done`` stamps it,
    ``util finalize-tracking`` re-stamps it with the tree the run left), and
    no answer applies to it this run: ``retry`` runs it anyway, and a
    ``done``/``skip`` answer is resolved by the human-task plan as before.
    A check handed out again because the files changed (or with no stamp to
    compare) loses its stamp, so a run that never re-runs it cannot re-stamp
    it as checked. The kept map is ``check id -> its findings``.

    A check whose findings the ``--exec-subagents`` leg recorded has no
    ``task_check_trees`` stamp: the executor stamps its verdict instead
    (:func:`_executor_check_stamp`), which is read when the state holds none
    (an executor stop resumed natively handed the check out
    again on unchanged files). A check kept on that stamp adopts it, so the
    native run's closing ``util finalize-tracking`` re-stamps it like its own.
    """

    stamps = state.get(TASK_CHECK_TREES_KEY) or {}
    if not isinstance(stamps, dict):
        stamps = {}
    findings_on_record = state.get("task_check_findings") or {}
    current: Optional[str] = None
    measured = False
    rerun: List[str] = []
    kept: Dict[str, List[str]] = {}
    for check_id in checks:
        answer = decisions.get(check_id)
        if answer in ("done", "skip"):
            rerun.append(check_id)
            continue
        recorded = stamps.get(check_id)
        adopted = False
        if not recorded and answer != "retry":
            recorded = _executor_check_stamp(
                plan_path, check_id, findings_on_record.get(check_id),
            )
            adopted = bool(recorded)
        if answer != "retry" and recorded:
            if not measured:
                current = check_tree_fingerprint(get_phase_dir(plan_path, "implement"))
                measured = True
            if current is not None and current == recorded:
                kept[check_id] = [
                    str(item) for item in (findings_on_record.get(check_id) or [])
                ]
                if adopted:
                    set_task_check_tree_in_state(state.state, check_id, recorded)
                continue
        rerun.append(check_id)
        set_task_check_tree_in_state(state.state, check_id, None)
    return rerun, kept


def _executor_check_stamp(
    plan_path: Path, check_id: str, findings: Any,
) -> Optional[str]:
    """The tree the ``--exec-subagents`` leg stamped on *check_id*'s verdict.

    ``verdict.tree_fingerprint`` of ``{phase}/implement_batch_<id>.json``
    (``WriteBatchScheduler._stamp_verdict``, re-stamped with the tree the run
    left by its ``CheckHolds.restamp_check_trees``), the same digest
    ``write_prompt.check_tree_fingerprint`` takes. Only a verdict that is an
    ``ok`` check with findings, and the very findings ``state.json`` holds
    (*findings*), so a stamp is never read off another run of the check than
    the one on record. ``None`` otherwise.
    """
    # One reader for both the resume and its why (`stop_answers.check_kept_on_resume`).
    return executor_check_stamp(
        get_phase_dir(plan_path, "implement"), check_id, findings)


def _native_withheld(
    output_data: Dict[str, Any],
    state: StateManager,
    plan_path: Path,
    *,
    kept_checks: Dict[str, List[str]],
    tasks_file: Optional[Path],
) -> Dict[str, Dict[str, str]]:
    """Take out of the native handoff's batches every task the host must not
    dispatch; what was taken out, by bucket.

    T005 and T006,
    skipped by ``--human-task T005=skip``, were in ``skipped_tasks`` and the
    prose said "do not dispatch", yet they sat in ``batches`` 3 and 4, and the
    emit counted "4 task(s) to dispatch" beside "Pending tasks: 3". The
    batches now hold only what the host dispatches (and a manual task still
    waiting for its answer), so a host that walks them cannot run one of
    these:

    * a task the human-task plan skipped, and a manual task answered
      ``done`` (named in ``skipped_tasks`` / ``completed_manual_tasks``);
    * ``held``: each task that depends on a check this resume keeps
      (:func:`_native_check_reruns`), with the reason ``util batch-done``
      recorded for it;
    * ``refused``: a task ``driver.write_paths`` does not allow, recorded
      ``failed`` in ``state.json`` with its reason, as the executor refuses it
      before dispatch (``--human-task <id>=done|skip|retry`` answers it, and a
      ``--resume`` checks it again) — ``util write-prompt`` refused it before,
      after the host had already been handed it;
    * ``not_run``: each task that depends on a refused one.

    ``pending_tasks`` is recounted from what is left.
    """

    batches = output_data.get("batches") or []
    entries = [task for batch in batches for task in batch.get("tasks") or []]
    nodes = [
        {
            "task_id": str(task.get("id") or ""),
            "depends_on": list(task.get("depends_on") or []),
            "executor_role": task.get("executor_role"),
            "is_human": task.get("is_human"),
        }
        for task in entries
    ]
    graph = decomposition_graph(nodes, state.state)
    gone: set = {
        str(task.get("id") or "") for task in entries
        if task.get("status") in (TaskStatus.SKIPPED.value, TaskStatus.COMPLETED.value)
    }
    human = {
        str(task.get("id") or "") for task in entries
        if task.get("is_human") or task.get("executor_role") == "human"
    }
    present = {str(task.get("id") or "") for task in entries}

    held: Dict[str, str] = {}
    held_by: Dict[str, str] = {}
    # An explicit selection can omit its upstream check altogether. Its
    # recorded findings still hold; a check present in these batches can
    # instead run before its dependent and release the hold normally.
    held_checks = set(kept_checks) | (
        set(rerunnable_checks(state.state)) - present
        - set(output_data.get("accepted_tasks") or {})
    )
    for check_id in sorted(held_checks):
        for dependent in transitive_dependents(graph, check_id):
            if dependent in present and dependent not in gone | human:
                held.setdefault(dependent, blocked_by_check_reason(check_id))
                held_by.setdefault(dependent, check_id)

    refused: Dict[str, str] = {}
    not_run: Dict[str, str] = {}
    candidates = [
        task for task in entries
        if str(task.get("id") or "") not in gone | human | set(held)
    ]
    if candidates:
        try:
            phase_dir = get_phase_dir(plan_path, "implement")
            write_tasks = write_phase_bridge.materialize_write_tasks(
                kind="implement",
                batches=[{"batch_index": 0, "can_parallelize": False, "tasks": candidates}],
                phase_dir=str(phase_dir),
                plan_file=str(plan_path.absolute()),
                tasks_file=str(tasks_file) if tasks_file else None,
            )
        except Exception:  # noqa: BLE001 - never refuse on a guess
            write_tasks = []
        for write_task in write_tasks:
            task_id = str(write_task.get("task_id") or "")
            violation = policy_violation_for(
                write_task, plan_file=str(plan_path.absolute()),
                anchor_dir=get_phase_dir(plan_path, "implement"),
            )
            if violation is None:
                continue
            message = violation.message
            # The refusal ends with allowing
            # the file as the user's call (`write_safety.policy_allow_clause`);
            # beside it, the skip answer, in the executor stop's words. Per rule, and
            # the skip alone for a file outside the
            # repository, which no policy change can allow.
            skip = policy_skip_clause(
                task_id, alone=policy_allow_clause(violation.hits) is None)
            refused[task_id] = (
                f"{NATIVE_REFUSED_PREFIX}{message} {skip[0].upper()}{skip[1:]}."
            )
        for task_id in sorted(refused):
            state.update_task_status(task_id, "failed", reason=refused[task_id])
            for dependent in transitive_dependents(graph, task_id):
                if (dependent in present and dependent not in gone | human
                        and dependent not in held and dependent not in refused):
                    not_run.setdefault(
                        dependent,
                        f"not run — depends on {task_id}, which was refused "
                        f"before dispatch (the write policy does not allow a "
                        f"file it declares)",
                    )

    withheld = gone | set(held) | set(refused) | set(not_run)
    kept_batches = []
    for batch in batches:
        batch["tasks"] = [
            task for task in batch.get("tasks") or []
            if str(task.get("id") or "") not in withheld
        ]
        if batch["tasks"]:
            batch["can_parallelize"] = len(batch["tasks"]) > 1
            kept_batches.append(batch)
    output_data["batches"] = kept_batches
    if "pending_tasks" in output_data:
        output_data["pending_tasks"] = sum(len(b["tasks"]) for b in kept_batches)
    waiting = _waiting_on_checks(kept_batches, graph)
    if waiting:
        output_data["waiting_on_checks"] = {
            task_id: (
                f"waits on check {', '.join(checks)}: dispatch it only after "
                f"{' and '.join(checks)} {'is' if len(checks) == 1 else 'are'} "
                f"recorded with `--check passed`; if "
                f"{' or '.join(checks)} reports problems, `util batch-done` "
                f"prints [CHECK_BLOCKED] for it and it is not run"
            )
            for task_id, checks in sorted(waiting.items())
        }
    if kept_checks:
        output_data["not_rerun_checks"] = {
            check_id: (
                "not run again — nothing in the repository changed since its "
                "check reported problems"
                + (f": {'; '.join(findings)}" if findings else "")
            )
            for check_id, findings in sorted(kept_checks.items())
        }
    if held:
        output_data["held_tasks"] = dict(sorted(held.items()))
    if refused:
        output_data["refused_tasks"] = dict(sorted(refused.items()))
    if not_run:
        output_data["not_run_tasks"] = dict(sorted(not_run.items()))
    # What the host's `util metrics finish`
    # names on its closing `[ETA]` line, as the executor's closing line
    # names the same tasks — also when this emit hands out nothing and the
    # host runs no `util metrics start`. Replaced by every native emit.
    left: Dict[str, str] = {}
    left.update({task_id: metrics_mod.LEFT_NOT_RUN for task_id in not_run})
    left.update({
        task_id: metrics_mod.left_out_check(check_id)
        for task_id, check_id in held_by.items()
    })
    left.update({task_id: metrics_mod.LEFT_REFUSED for task_id in refused})
    state.set_metrics_left_out("implement", left)
    return {"held": held, "refused": refused, "not_run": not_run}


def _started_and_unfinished(state: StateManager, task_ids: Iterable[str]) -> List[str]:
    """The tasks a run without ``--resume`` keeps: those an earlier run of an
    implement that started and did not finish recorded ``completed``.

    Empty — the run starts over, as it always did — when implement finished,
    when nothing of this decomposition was finished, or when generate-tasks or
    apply-task-suggestions wrote the task list after implement's last run,
    whose ids may name other tasks now (nothing clears ``task_status``).
    """
    if state.is_phase_completed("implement"):
        return []
    statuses = state.implementation_task_statuses()
    kept = sorted(str(t) for t in task_ids if statuses.get(str(t)) == "completed")
    if not kept or implement_records_predate_task_list(state):
        return []
    return kept


def _kept_labels(state: StateManager, plan: Any = None) -> Dict[str, str]:
    """How each task answered ``--human-task <id>=done`` reads in a kept
    list — "accepted with its check findings", "accepted after failing",
    "completed by hand" — from *plan* (this run's human-task plan) and the
    answers on record, in the words the executor's ``resume: kept`` line and
    summary.md use (``human_task_plan.answered_done_label``); and a
    check whose findings stand, not accepted, as
    ``task_ledger.KEPT_WITH_FINDINGS_LABEL``."""

    accepted, completed = answered_done_on_record(state)
    accepted = dict(accepted)
    completed = list(completed)
    retried = set()
    if plan is not None:
        accepted.update(getattr(plan, "accepted", None) or {})
        completed += list(getattr(plan, "completed", None) or [])
        retried = set(getattr(plan, "retry", None) or ())
    view = SimpleNamespace(accepted=accepted)
    labels = {
        task_id: KEPT_WITH_FINDINGS_LABEL
        for task_id in rerunnable_checks(state)
        if task_id not in retried
    }
    labels.update({
        task_id: answered_done_label(view, task_id)
        for task_id in list(accepted) + completed
    })
    return labels


def _kept_named(kept: Sequence[str], labels: Dict[str, str]) -> str:
    """The kept tasks as a resume line names them: the plain ones first (at
    most eight), then each labelled one with what it is
    (``task_ledger.kept_named``, the executor's and the progress
    line's words too)."""

    return kept_named(kept, labels)


def _continued_line(kept: Sequence[str], labels: Optional[Dict[str, str]] = None) -> str:
    """The one line a continued run prints."""
    named = _kept_named(kept, labels or {})
    return (
        "resume: implement started earlier and did not finish, so this run "
        f"continues it as --resume: kept {len(kept)} task(s) an earlier run "
        f"finished ({named}) and runs what is left. To run every task again "
        "instead, add --fresh."
    )


def _native_kept_line(
    state: StateManager, task_ids: Iterable[str], output_data: Dict[str, Any],
    plan: Any = None,
) -> Optional[str]:
    """The ``resume: kept …`` line of a native ``--resume`` typed by the user,
    or ``None`` when it keeps nothing.

    Only the
    plain ``--implement`` that continues a started run said what it kept, so
    on the native leg an explicit ``--resume`` never showed "T002 (accepted
    with its check findings)", which both tool routes print (the executor's
    ``[write-subagents] resume: kept …`` line). Kept: every task of the
    decomposition an earlier run recorded ``completed``, or this run's
    answers record done, that this emit does not hand out again.
    """
    handed = {
        str(task.get("id") or "")
        for batch in output_data.get("batches") or []
        for task in batch.get("tasks") or []
    }
    statuses = state.implementation_task_statuses()
    answered = set(getattr(plan, "accepted", None) or {}) | set(
        getattr(plan, "completed", None) or []
    )
    kept = [
        str(task_id) for task_id in task_ids
        if (statuses.get(str(task_id)) == "completed" or str(task_id) in answered)
        and str(task_id) not in handed
    ]
    if not kept:
        return None
    named = _kept_named(kept, _kept_labels(state, plan))
    return f"resume: kept {len(kept)} task(s) an earlier run finished ({named})."


def _waiting_on_checks(
    batches: Sequence[Dict[str, Any]], graph: Sequence[Dict[str, Any]],
) -> Dict[str, List[str]]:
    """Each handed-out task that depends, directly or through another task,
    on a check task handed out in the same batches: ``{task id: [check ids]}``.

    T007 sat in the first
    emit's batches beside T004 although it depends on check T002, whose
    verdict nobody knows until T002 runs — rightly, since a pass releases it,
    but nothing said so, and the counts read as one more task than ran. Its
    hold is decided by ``util batch-done --check findings`` (``[CHECK_BLOCKED]``)
    and ``util write-prompt`` (``[WRITE_PROMPT_BLOCKED]``); this only names it
    in advance. A manual task waits on nothing (no subagent runs it).
    """

    entries = [task for batch in batches for task in batch.get("tasks") or []]

    def manual(task: Dict[str, Any]) -> bool:
        return bool(task.get("is_human")) or task.get("executor_role") == "human"

    present = {str(task.get("id") or ""): task for task in entries}
    checks = sorted(
        task_id for task_id, task in present.items()
        if not manual(task) and is_check_task("implement", task)
    )
    waiting: Dict[str, List[str]] = {}
    for check_id in checks:
        for dependent in transitive_dependents(graph, check_id):
            task = present.get(dependent)
            if task is not None and not manual(task):
                waiting.setdefault(dependent, []).append(check_id)
    return waiting


def _handoff_counts(output_data: Dict[str, Any]) -> Dict[str, int]:
    """Every count the emit prints and hands over, read off one source: the
    batches as handed out."""
    batches = output_data.get("batches") or []
    entries = [t for b in batches for t in b.get("tasks") or []]
    manual = sum(
        1 for t in entries if t.get("executor_role") == "human" or t.get("is_human")
    )
    return {
        "batches": len(batches),
        "tasks": len(entries),
        "manual": manual,
        "dispatch": len(entries) - manual,
    }


def _dispatch_line(output_data: Dict[str, Any]) -> str:
    """``Organized into N execution batches: X task(s) to dispatch …``,
    counted from the batches as handed out (the native emit and ``--dry-run``;
    the executor's run prints its own, ``WriteBatchScheduler._dispatch_preview``,
    in the same words)."""

    counts = _handoff_counts(output_data)
    return dispatch_line(
        counts["batches"], counts["dispatch"], manual=counts["manual"],
        waiting=list(output_data.get("waiting_on_checks") or {}),
    )


def _refuse_unrecorded_native_resume(
    tasks: List[Dict[str, Any]], *, plan_path: Path, state: StateManager, resume: bool,
) -> bool:
    """Print the refusal block and return True when a native ``--resume`` must stop.

    A task about to be handed out again whose id the implement log already
    holds, with no ``task_status`` record (``util batch-done``) saying it
    finished or failed, is one the host ran without recording: re-emitting
    it would run it twice. See :func:`utils.batch_done.unrecorded_logged_batches`.
    """
    if not resume or not tasks:
        return False

    output_dir = str(get_output_dir(plan_path))
    unrecorded = unrecorded_logged_batches(
        tasks, output_dir=output_dir, phase="implement", state=state.state,
    )
    if not unrecorded:
        return False
    phase_dir = str(get_phase_dir(plan_path, "implement"))
    for line in resume_refusal_lines(unrecorded, phase_dir=phase_dir, mode_word="implement"):
        print(line, file=sys.stderr)
    return True


def _prerequisite_unmet(
    plan_path: Path, plan_dir: Path, missing: List[Dict[str, Any]],
) -> int:
    """Print the ``[PREREQUISITE_UNMET]`` stop for *missing*; exit 3."""
    print(build_unmet_message("implement", plan_path, plan_dir, missing))
    unattended_mod.mark_needs_human("implement")
    print(json.dumps({
        "marker": "PREREQUISITE_UNMET",
        "mode": "implement",
        "state": "needs-human",
        "exit": EXIT_NEEDS_HUMAN,
        "missing": missing,
    }, indent=2))
    return EXIT_NEEDS_HUMAN


def _stop_on_unreadable_task_list(plan_path: Path, unreadable: Exception) -> int:
    """Exit 3 for a ``TASKS_FILE`` marker implement cannot follow.

    *unreadable* is the :class:`TasksFileMissing` (no such file),
    :class:`TasksFileAmbiguous` (markers naming different files) or
    :class:`TasksFileRefused` (outside the plan's directory) that
    ``read_task_list`` raised. Each prints the ``TASKS_FILE_MISSING`` block.
    """
    raw = getattr(unreadable, "raw_path", "")
    regenerate = dispatcher_command("generate-tasks", plan_path.absolute(), "--yes")
    if isinstance(unreadable, TasksFileAmbiguous):
        named = plan_path.parent / raw
        listed = "\n".join(
            f"         <!-- TASKS_FILE: {path} -->" for path in unreadable.raw_paths
        )
        print(
            "ERROR: the plan carries TASKS_FILE markers naming different task "
            f"lists:\n{listed}\n"
            "       Nothing was implemented. Keep the one that names this plan's "
            "task list (a marker quoted as code does not count), or regenerate "
            "it — " + regenerate
            + "\n       then re-run this command. (Following either one would "
            "risk implementing a stale or pasted task list.)"
        )
        reason = "Plan carries TASKS_FILE markers naming different task lists"
    elif isinstance(unreadable, TasksFileRefused):
        named = plan_path.parent / raw
        print(
            f"ERROR: the plan's <!-- TASKS_FILE: {raw} --> marker names a task "
            f"list outside the plan's directory ({unreadable.reason}).\n"
            f"       Nothing was implemented. Point the marker at the task list "
            f"in {plan_path.parent}, or regenerate it — " + regenerate
            + "\n       then re-run this command. (Parsing the plan itself "
            "instead would invent a task list from its prose.)"
        )
        reason = "Plan names a TASKS_FILE outside the plan's directory"
    else:
        named = unreadable.path
        print(
            f"ERROR: the plan's <!-- TASKS_FILE: {raw} --> marker "
            f"names a task list that does not exist:\n"
            f"       {named}\n"
            f"       Nothing was implemented. Regenerate the task list — "
            + regenerate
            + "\n       then re-run this command. (Parsing the plan itself "
            "instead would invent a task list from its prose, which every "
            "later phase would treat as ground truth.)"
        )
        reason = "Plan names a TASKS_FILE that does not exist"
    unattended_mod.mark_needs_human("implement")
    print(json.dumps({
        "marker": "TASKS_FILE_MISSING",
        "mode": "implement",
        "state": "needs-human",
        "exit": EXIT_NEEDS_HUMAN,
        "tasks_file": str(named),
        "reason": reason,
    }, indent=2))
    return EXIT_NEEDS_HUMAN


# ---------------------------------------------------------------------------
# The decisions `main` takes, as pure functions: no file, no print, no state.
# Each one is a table in tests/test_implement_decisions.py, one named row per
# case; read the table before changing a rule here.
# ---------------------------------------------------------------------------


class GateAction(str, Enum):
    """How a prerequisite gate of ``implement`` ends (D6 rows 6 and 14)."""

    #: Met: the run goes on.
    PROCEED = "proceed"
    #: ``--skip-prerequisites`` over unapplied advice: recorded, said, goes on.
    RECORD_SKIP = "record-skip"
    #: ``--yes`` (or a skip the flag cannot make): ``[PREREQUISITE_UNMET]``, exit 3.
    NEEDS_HUMAN = "needs-human"
    #: Attended: the marker the driving agent acts on, exit 0.
    MARKER_EXIT_0 = "marker-exit-0"


@dataclass(frozen=True)
class ApplyGate:
    """:func:`decide_apply_gate`'s answer.

    *missing* is the ``[PREREQUISITE_UNMET]`` payload's list (one entry);
    *refused_skip* says ``--skip-prerequisites`` was typed over a scope
    blocker, which only the user can lift.
    """

    action: GateAction
    gate_phase: str = "apply-suggestions"
    missing: List[Dict[str, Any]] = field(default_factory=list)
    refused_skip: bool = False


def decide_apply_gate(
    apply_check: Mapping[str, Any],
    task_gate: Optional[Mapping[str, Any]],
    *,
    skip_prerequisites: bool,
    unattended: bool,
) -> ApplyGate:
    """D6 row 6: the unapplied-suggestions gate, before anything is written.

    *apply_check* is ``check_apply_suggestions_prerequisite``; *task_gate* is
    ``check_apply_task_suggestions_prerequisite``, read only once *apply_check*
    is met (``None`` otherwise). A scope blocker recorded by
    apply-task-suggestions is a gate here too, never the row-7 advisory: the
    task list's accepted goal is not complete, and implement builds on it.
    Three endings, no fourth: ``--skip-prerequisites`` records the skip, ``--yes``
    stops with exit 3, neither prints the ``[PREREQUISITE_CHECK]`` marker. A
    scope blocker is the user's scope decision, not unapplied advice, so
    ``--skip-prerequisites`` cannot record a skip over it.
    """
    check, gate_phase = apply_check, "apply-suggestions"
    if check["met"] and task_gate is not None and task_gate.get("scope_blocked"):
        check, gate_phase = task_gate, "apply-task-suggestions"
    if check["met"]:
        return ApplyGate(GateAction.PROCEED, gate_phase)
    scope_blocked = bool(check.get("scope_blocked"))
    missing = [{
        "phase": gate_phase,
        "reason": check["reason"],
        "valid_count": check.get("valid_count", 0),
        "importance_breakdown": check.get("importance_breakdown", {}),
        **({"scope_blocked": True} if scope_blocked else {}),
    }]
    if skip_prerequisites and not scope_blocked:
        action = GateAction.RECORD_SKIP
    elif unattended or skip_prerequisites:
        action = GateAction.NEEDS_HUMAN
    else:
        action = GateAction.MARKER_EXIT_0
    return ApplyGate(
        action, gate_phase, missing,
        refused_skip=bool(skip_prerequisites and scope_blocked),
    )


def decide_tasks_missing(*, generate_tasks_completed: bool, unattended: bool) -> GateAction:
    """No task list yet: the same rule as the row-6 gate.

    Attended, the ``[TASKS_MISSING]`` marker and exit 0: the driving agent
    reads it and runs generate-tasks itself. Under ``--yes`` there is no agent
    to read a marker, and exit 0 would report a run that implemented nothing
    as done, so it is exit 3 naming the generate-tasks re-invocation.
    """
    if generate_tasks_completed:
        return GateAction.PROCEED
    return GateAction.NEEDS_HUMAN if unattended else GateAction.MARKER_EXIT_0


@dataclass(frozen=True)
class RunMode:
    """Whether this run resumes, and whether it starts over.

    *resume*: it restores the recorded statuses and hands out only what is
    left (typed ``--resume``, or a started run it continues). *resume_typed*:
    the user typed ``--resume``, which a code task's ``--human-task`` answer
    needs. *start_over*: it hands every task out again, so what earlier runs
    recorded is set aside first (``_start_over``). *continued_ids*: the tasks
    an unfinished earlier run finished, which a run continuing it keeps.
    """

    resume: bool
    resume_typed: bool
    start_over: bool
    continued_ids: Tuple[str, ...] = ()


def decide_run_mode(
    *,
    resume: bool,
    task: Optional[str],
    fresh: bool,
    dry_run: bool,
    dry_run_subagents: bool,
    started_unfinished: Callable[[], Sequence[str]],
) -> RunMode:
    """Resume, continue, or start over (docs/development/host-reporting.md).

    A run without ``--resume`` on an implement that started and did not
    finish continues it: *started_unfinished* names what an earlier run of it
    finished, and is asked only when nothing typed decides (``--resume``,
    ``--task``, ``--fresh``). Starting over is ``--fresh``; a finished
    implement starts over without it; ``--task`` reruns what it names. Any
    run that is no resume, no ``--task`` rerun and no dry run starts over.
    """
    resume_typed = bool(resume)
    continued: Tuple[str, ...] = ()
    if not resume and not task and not fresh:
        continued = tuple(started_unfinished())
    resumes = resume_typed or bool(continued)
    start_over = not (resumes or task or dry_run or dry_run_subagents)
    return RunMode(
        resume=resumes, resume_typed=resume_typed, start_over=start_over,
        continued_ids=continued,
    )


def refuse_human_answers(
    answers: Mapping[str, str],
    *,
    known_ids: Collection[str],
    human_ids: Sequence[str],
    failed_or_held: Collection[str],
    resume_typed: bool,
) -> Optional[str]:
    """The refusal of this run's ``--human-task`` answers, or ``None``.

    A human task is answered ``done`` or ``skip``. A code task is answerable
    only on a typed ``--resume`` and only once it failed or its check reported
    findings that hold back the tasks after it (*failed_or_held*): ``done``
    accepts, ``skip`` leaves it and its dependents undone, ``retry`` runs it
    again. Refusals are checked in this order: an id not in the plan, a code
    task without ``--resume``, a code task that did not fail, a human task
    answered ``retry``.
    """
    unknown = [tid for tid in answers if tid not in known_ids]
    if unknown:
        return (
            "ERROR: --human-task names task(s) that are not in this plan: "
            f"{', '.join(sorted(unknown))}.\n"
            f"       Human tasks in this plan: "
            f"{', '.join(human_ids) or 'none'}"
        )
    not_human = [tid for tid in answers if tid not in human_ids]
    if not_human and not resume_typed:
        return (
            "ERROR: --human-task answers a code task only with --resume, "
            "after a run recorded it failed or its check reported "
            "problems; these are code tasks: "
            f"{', '.join(sorted(not_human))}."
        )
    unanswerable = sorted(set(not_human) - set(failed_or_held))
    if unanswerable:
        return (
            "ERROR: --human-task answers a human task, a code task the "
            "last run recorded failed, or a check whose findings hold "
            "back the tasks after it; these are code tasks that did not "
            f"fail: {', '.join(unanswerable)}."
        )
    retried_human = sorted(
        tid for tid, action in answers.items()
        if action == "retry" and tid in human_ids
    )
    if retried_human:
        return (
            "ERROR: --human-task <id>=retry re-runs a failed code task; a "
            f"human task is answered done or skip: {', '.join(retried_human)}."
        )
    return None


class StartOver(str, Enum):
    """Where a start-over sets aside earlier records (``_start_over``)."""

    #: The native leg: before the emit reads the records.
    BEFORE_EMIT = "before-emit"
    #: The executor leg: past the detach boundary, in the process that owns
    #: the phase dir.
    AFTER_DETACH = "after-detach"
    NEVER = "never"


def start_over_when(
    *, start_over: bool, executor_backed: bool, detach: bool, internal_worker: bool,
) -> StartOver:
    """When this run sets aside what earlier runs recorded, if it does.

    Never in a ``--detach`` launcher, which may be re-attaching to a live run;
    its worker (``--internal-worker``) does it instead. The executor leg's
    launcher stops at the detach boundary before :attr:`StartOver.AFTER_DETACH`
    anyway.
    """
    if not start_over or (detach and not internal_worker):
        return StartOver.NEVER
    return StartOver.AFTER_DETACH if executor_backed else StartOver.BEFORE_EMIT


def native_gate_applies(
    *,
    withheld: Optional[Mapping[str, Mapping[str, Any]]],
    rerun_task: bool,
    has_human_plan: bool,
    kept_checks: bool,
    tasks_to_dispatch: int,
    implement_completed: bool,
) -> bool:
    """Whether a native emit stops on a manual task (``_native_manual_gate_stop``).

    Only on the native leg (*withheld*, ``_native_withheld``'s lists, is
    ``None`` on the executor leg), not for a ``--task`` rerun, and only when
    the emit hands out nothing: no task withheld, no check kept, nothing to
    dispatch, on an implement not completed. Whether a manual task is what
    every code task left waits on is the stop's own question.
    """
    return bool(
        withheld is not None
        and not rerun_task
        and has_human_plan
        and not any(withheld[key] for key in withheld)
        and not kept_checks
        and not tasks_to_dispatch
        and not implement_completed
    )


#: The heading of a native emit's closing steps, in the neutral host wording
#: ``instructions/`` uses.
NATIVE_STEPS_HEADING = "The driving agent should now:"


def closing_steps(*, closes: bool, stopped_short: bool, summary_file: str) -> List[str]:
    """The lines that end a native emit: what the driving agent does next.

    *closes*: the emit only records answers on a completed implement
    (``_closes_a_completed_implement``), so it asks for no summary and no
    close, and the phase stays completed. *stopped_short*: tasks listed above
    did not run, so the phase closes without ``--mark-completed``.
    """
    if closes:
        return [
            "\nNothing is left to run: implement stays completed. The answers "
            "above are recorded in state.json; there is no batch to execute and "
            "no phase to close.",
            f"\n{NATIVE_STEPS_HEADING}",
            "  1. Report the answers recorded above; spawn no subagent, write no "
            "implementation summary (the completed run's summary.md stays as it "
            "is) and run no `util finalize-tracking`",
            "  2. End the report with the command `util next-command` prints",
        ]
    lines = [
        f"\n{NATIVE_STEPS_HEADING}",
        "  1. Read the output JSON file",
        "  2. Execute each batch sequentially (batches have dependencies)",
        "  3. Tasks within a batch can run in parallel",
        "  4. Update the state file after each task completes",
        "  5. After all tasks complete, generate the implementation summary",
        f"     Summary file: {summary_file}",
    ]
    if stopped_short:
        lines.append(
            "  6. Close the phase with `util finalize-tracking` without "
            "--mark-completed (tasks listed above did not run), then end the "
            "report with the commands `util next-command` prints"
        )
    else:
        # The emit cannot know how the run ends: a check that records
        # findings holds tasks back mid-run.
        lines.append(
            "  6. Close the phase with `util finalize-tracking … --mark-completed` "
            "once every task ran; after a [CHECK_BLOCKED] line, a failed task or "
            "a stop, run it without --mark-completed and end the report with "
            "the commands `util next-command` prints"
        )
    return lines


# ---------------------------------------------------------------------------
# `main`, in stages. Each stage takes the run and returns ``None`` to go on, or
# the exit code to stop with (0, 1 or 3, as AGENTS.md defines them; `multi_llm`
# and `full` read a returned code exactly as they read a `sys.exit`). A
# detached worker re-enters `main` and runs every stage again, so each stage
# must be safe to run a second time over what the first run recorded.
# ---------------------------------------------------------------------------


@dataclass
class ImplementRun:
    """What one ``implement`` invocation knows, filled in stage by stage.

    A field keeps its default until the stage that sets it has run:
    :func:`open_run` sets the plan and the state, :func:`load_task_list` the
    decomposition, :func:`apply_run_mode` the :class:`RunMode`,
    :func:`build_handoff` the task JSON, :func:`prepare_native_emit` the
    native leg's plan of what it withholds.
    """

    args: argparse.Namespace
    #: ``--yes``: D6b makes unattended a flag, never a guess from a TTY or ``CI``.
    unattended: bool
    #: This run's ``--human-task`` answers, validated before anything is read.
    human_task_decisions: Dict[str, str] = field(default_factory=dict)
    plan_path: Path = Path()
    plan_content: str = ""
    state: Optional[StateManager] = None
    plan_preamble: str = ""
    plan_dir: Path = Path()
    #: D6 decisions taken before this process owns the phase dir, written by
    #: :func:`cross_detach_boundary` once it does.
    pending_resolutions: List[Tuple[str, str]] = field(default_factory=list)
    #: The external task list the prompts are built from (F15), so
    #: ``write_tasks.json`` records ``inputs.tasks_sha256``; ``None`` for the
    #: legacy embedded-task format.
    tasks_file: Optional[Path] = None
    decomposer: Optional[TaskDecomposer] = None
    tasks: List[Task] = field(default_factory=list)
    mode: RunMode = RunMode(resume=False, resume_typed=False, start_over=False)
    human_task_ids: List[str] = field(default_factory=list)
    human_task_strategy: Optional[str] = None
    scope_policy: str = ""
    #: The Python executor schedules the batches itself; otherwise the host
    #: does (the native leg).
    executor_backed: bool = False
    #: A check whose findings stand is handed out again on a native resume
    #: only once the files moved; the executor decides at dispatch.
    kept_checks: Dict[str, List[str]] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    start_over_at: StartOver = StartOver.NEVER
    #: The answers both legs apply this run (:func:`_applicable_task_decisions`).
    applicable_decisions: Dict[str, str] = field(default_factory=dict)
    native_human_plan: Any = None
    #: What each later manual task comes after, for its deferred-list line.
    native_after: Dict[str, List[str]] = field(default_factory=dict)
    native_withheld: Optional[Dict[str, Dict[str, str]]] = None
    native_gate: Optional[Tuple[List[str], str, str]] = None
    #: The emit only records answers on a completed implement.
    closes: bool = False

    @property
    def output_path(self) -> Path:
        return Path(self.args.output)


def check_answers_flags(run: ImplementRun) -> Optional[int]:
    """D6 rows 9 and 15: refuse a bad ``--human-task`` value or
    ``--force-strategy pause-and-ask`` under ``--yes`` before anything is
    read, so a bad value is exit 3 at parse time rather than a silent
    default halfway through a batch."""
    args = run.args
    try:
        run.human_task_decisions = parse_human_task_decisions(args.human_task)
    except NeedsHuman as exc:
        return unattended_mod.fail_closed(exc.message, site_id=exc.site)
    if run.unattended and args.force_strategy == "pause-and-ask":
        # The dispatcher already rejects this combination at parse time; this is
        # the same refusal for a direct invocation, so neither route can hang.
        return unattended_mod.fail_closed(
            "ERROR: --force-strategy pause-and-ask requires a human at the "
            "per-task gate, which --yes forbids. Pass a non-interactive strategy "
            f"(e.g. {UNATTENDED_HUMAN_TASK_STRATEGY}) or drop --yes.",
            site_id=unattended_mod.row(9).site_id,
        )
    return None


def open_run(run: ImplementRun) -> Optional[int]:
    """Resolve the plan, anchor the run, and read (never write) its state."""
    args = run.args
    # Resolved to an absolute path first: `uv --directory` changes the cwd.
    plan_path = run.plan_path = Path(args.plan_file).resolve()
    if not plan_path.exists():
        print(f"ERROR: Plan file not found: {args.plan_file}")
        print(f"       Resolved path: {plan_path}")
        return 1

    # The anchor capture point — absolute, before anything can chdir
    # and before any provider read that decides routing.
    set_run_anchor(str(plan_path))

    # The default --output depends on the git root and the plan stem, so it
    # cannot be a static argparse default.
    if args.output is None:
        args.output = resolve_default_output(plan_path)

    run.plan_content = plan_path.read_text(encoding="utf-8")
    print(f"Loaded plan: {plan_path}")

    # Constructing the state only *reads* (or synthesizes in memory) the
    # document: the first `save()` waits until the row-6 gate has cleared
    # (`run_prerequisite_gates`), so an unmet gate leaves nothing behind.
    run.state = get_or_create_state(plan_path)
    print(f"State file: {run.state.state_file}")

    # The plan preamble goes into every task prompt.
    run.plan_preamble = run.state.get("plan_preamble") or ""
    run.plan_dir = get_output_dir(plan_path)
    return None


def run_prerequisite_gates(run: ImplementRun) -> Optional[int]:
    """D6 rows 6, 7 and 14 (:func:`decide_apply_gate`,
    :func:`decide_tasks_missing`), and the run's first ``state.save()``.

    Nothing is produced before the row-6 gate clears: no phase dir, no tasks,
    no state.json mutation, so an unmet gate leaves no half-generated
    artifact.
    """
    args, state, plan_path, plan_dir = run.args, run.state, run.plan_path, run.plan_dir

    # A recorded upstream `--skip-prerequisites` is reported once and never
    # re-litigated: consent was already given explicitly, and re-asking would make
    # the recorded skip meaningless (D6a).
    for notice in upstream_skip_notices(state):
        print(notice)

    apply_check = check_apply_suggestions_prerequisite(state, plan_dir)
    gate = decide_apply_gate(
        apply_check,
        (check_apply_task_suggestions_prerequisite(state, plan_dir)
         if apply_check["met"] else None),
        skip_prerequisites=bool(args.skip_prerequisites),
        unattended=run.unattended,
    )
    if gate.action is GateAction.RECORD_SKIP:
        record_prerequisite_skip(
            state, "apply-suggestions", reason=SKIP_PREREQUISITES_REASON
        )
        print(
            f"{SKIPPED_MARKER} implement: "
            f"{gate.missing[0]['valid_count']} unapplied apply-suggestions "
            f"suggestions (reason: {SKIP_PREREQUISITES_REASON})"
        )
    elif gate.action is GateAction.NEEDS_HUMAN:
        if gate.refused_skip:
            print(
                f"ERROR: --skip-prerequisites cannot skip {gate.gate_phase} for "
                f"implement: it stopped on a scope blocker, a scope decision "
                f"only the user can make."
            )
        return _prerequisite_unmet(plan_path, plan_dir, gate.missing)
    elif gate.action is GateAction.MARKER_EXIT_0:
        prereq_info = {
            "marker": "PREREQUISITE_CHECK",
            "phase": gate.gate_phase,
            "reason": gate.missing[0]["reason"],
            "valid_count": gate.missing[0]["valid_count"],
        }
        print("[PREREQUISITE_CHECK]")
        print(json.dumps(prereq_info, indent=2))
        return 0

    # The gate is cleared (or explicitly skipped, which recorded its own save):
    # only now does this run own a state.json on disk.
    state.save()

    _advise_on_task_suggestions(run)

    tasks_gate = decide_tasks_missing(
        generate_tasks_completed=state.is_phase_completed("generate-tasks"),
        unattended=run.unattended,
    )
    if tasks_gate is not GateAction.PROCEED:
        print("[TASKS_MISSING]")
        print(json.dumps({"marker": "TASKS_MISSING", "reason": "No implementation tasks found"}))
        if tasks_gate is GateAction.NEEDS_HUMAN:
            return _prerequisite_unmet(plan_path, plan_dir, [{
                "phase": "generate-tasks",
                "reason": "No implementation tasks found",
            }])
        return 0
    return None


def _advise_on_task_suggestions(run: ImplementRun) -> None:
    """D6 row 7: unapplied task suggestions are an advisory that never blocks.

    Under ``--yes``/``--no-confirm`` the advisory resolves to "skip", and the
    phase is *recorded* skipped here rather than left for the agent to
    remember: an auto-selection nobody can see afterwards is
    indistinguishable from a silent degradation. The decision is buffered in
    ``pending_resolutions`` until this process owns the phase dir.
    """
    args, state = run.args, run.state
    task_skip_reason = "auto-skipped by --yes/--no-confirm (D6 row 7)"
    task_skip_decision = "skipped; apply-task-suggestions recorded as skipped"
    # The detached launcher may already have saved this choice. Its worker
    # then sees the prerequisite as met, but must still report the choice that
    # lets this run proceed. Explicit human skips keep their existing notice.
    if (run.unattended or args.no_confirm) and (
        state.get_phase_skip_reason("apply-task-suggestions") == task_skip_reason
    ):
        run.pending_resolutions.append((unattended_mod.row(7).site_id, task_skip_decision))

    task_suggestions_check = check_apply_task_suggestions_prerequisite(state, run.plan_dir)
    if task_suggestions_check["met"]:
        return
    advisory_info = {
        "marker": "TASK_SUGGESTIONS_ADVISORY",
        "phase": "apply-task-suggestions",
        "reason": task_suggestions_check["reason"],
        "actionable_count": task_suggestions_check.get("actionable_count", 0),
        "importance_breakdown": task_suggestions_check.get("importance_breakdown", {})
    }
    print("[TASK_SUGGESTIONS_ADVISORY]")
    print(json.dumps(advisory_info, indent=2))
    if run.unattended or args.no_confirm:
        record_prerequisite_skip(
            state,
            "apply-task-suggestions",
            reason=task_skip_reason,
        )
        unattended_mod.record_resolution(
            None,
            unattended_mod.row(7).site_id,
            task_skip_decision,
        )
        run.pending_resolutions.append((unattended_mod.row(7).site_id, task_skip_decision))


def load_task_list(run: ImplementRun) -> Optional[int]:
    """Read the task list, take the pre-implement baselines, and decompose it.

    The task list is the file the plan's TASKS_FILE marker names, the default
    task list without a marker, or the plan itself only when it has neither
    (the legacy embedded-task format; ``tasks_file.read_task_list``).
    A marker naming no file, or a path outside the plan's directory, stops
    here: parsing the plan instead would invent tasks from its prose
    (docs/development/workflows.md, "Task generation").
    """
    args, state, plan_path = run.args, run.state, run.plan_path
    try:
        task_list = read_task_list(plan_path, run.plan_content)
    except (TasksFileMissing, TasksFileRefused) as unreadable:
        return _stop_on_unreadable_task_list(plan_path, unreadable)
    if task_list.path is not None:
        print(f"Loading tasks from: {task_list.path}")
    run.tasks_file = task_list.path

    # Record pre-existing changes (before implementation modifies anything)
    record_pre_existing_changes(state)

    # Record HEAD before implementation so code-review diffs exclude pre-impl
    # commits. Before the first commit that is the empty tree: everything
    # implement leaves is new, and a resume must not mistake the missing value
    # for a first run (`record_pre_existing_changes` re-takes its baseline then).
    if state.get("head_before_implement") is None:
        try:
            state.set("head_before_implement", head_or_empty_tree())
            state.save()
        except Exception as e:
            print(f"Warning: Could not record head_before_implement: {e}")

    # Check for plan changes
    if state.has_plan_changed() and args.resume:
        print("WARNING: Plan has changed since last session")
        state.clear_plan_changed_flag()

    run.decomposer = TaskDecomposer()
    run.tasks = run.decomposer.parse_plan(task_list.text)
    print(f"Found {len(run.tasks)} tasks")
    # Both legs pass here, so a task the run defers (a human task, or a
    # dependent `skip-dependents` skips with it) can be named by its title
    # once the workflow completes, not only by its id: `persist_human_task_plan`
    # records the `skipped` status and its reason but no title, and
    # `[MANUAL_TASK]` reads the title from here.
    # The manual tasks ride along (`implement_human_task_ids`), so a finished
    # implement whose manual task nobody answered still names it as owed.
    # So does the whole graph: a resume materializes only the unfinished
    # tasks, and the hold a check with findings puts on the tasks after it
    # must still reach a task whose chain runs through a finished one.
    if state.record_task_titles(
        {task.id: task.title for task in run.tasks},
        human_ids=[
            task.id for task in run.tasks
            if getattr(task, "executor_role", "") == "human"
        ],
        depends_on={task.id: list(task.depends_on or []) for task in run.tasks},
    ):
        state.save()
    return None


def apply_run_mode(run: ImplementRun) -> Optional[int]:
    """Resume, continue or start over (:func:`decide_run_mode`), and restore
    the recorded statuses of a run that resumes."""
    args, state, decomposer = run.args, run.state, run.decomposer
    run.mode = decide_run_mode(
        resume=bool(args.resume),
        task=args.task,
        fresh=bool(getattr(args, "fresh", False)),
        dry_run=bool(args.dry_run),
        dry_run_subagents=bool(getattr(args, "dry_run_subagents", False)),
        started_unfinished=lambda: _started_and_unfinished(state, decomposer.tasks),
    )
    if run.mode.continued_ids:
        # A continued run is `--resume` for every later reader of `args`
        # too: `run_implement_write_phase` hands it to the scheduler.
        args.resume = True
        print(_continued_line(run.mode.continued_ids, _kept_labels(state)))
        if state.has_plan_changed():
            print("WARNING: Plan has changed since last session")
            state.clear_plan_changed_flag()

    if run.mode.resume:
        for task_id, status in state.get_all_task_statuses().items():
            if task_id in decomposer.tasks:
                decomposer.update_task_status(task_id, TaskStatus(status))
        print("Restored previous session state")
    return None


def record_human_answers(run: ImplementRun) -> Optional[int]:
    """D6 rows 8 and 9: resolve the human-task strategy and record this run's
    ``--human-task`` answers (:func:`refuse_human_answers`); never prompt."""
    args, state = run.args, run.state
    human_task_ids = run.human_task_ids = [
        task.id for task in run.decomposer.tasks.values()
        if getattr(task, "executor_role", "") == "human"
    ]
    run.human_task_strategy = resolve_human_task_strategy(
        state,
        human_task_ids,
        force_strategy=args.force_strategy,
        unattended=run.unattended,
        resume=run.mode.resume,
    )
    # F8: no run handle is claimed before the detach boundary, so recording
    # against the phase dir here would be a silent no-op
    # (`run_record.record_resolution` only writes when `_ACTIVE` names that phase
    # dir). The decision is buffered, as `ApplyOrchestratorBase._record_resolution`
    # / `_flush_resolutions` do, and replayed past the boundary.
    if (human_task_ids and run.human_task_strategy and run.unattended
            and not args.force_strategy):
        decision = f"{run.human_task_strategy} for {len(human_task_ids)} human task(s)"
        unattended_mod.record_resolution(None, unattended_mod.row(8).site_id, decision)
        run.pending_resolutions.append((unattended_mod.row(8).site_id, decision))

    answers = run.human_task_decisions
    if not answers:
        return None
    # Row 9's answer channel: a per-task decision arrives as a flag, is
    # recorded in state.json, and is handed to the driving agent in the task
    # JSON so the pause is a process boundary rather than a blocked stdin.
    held_by = set(rerunnable_checks(state.state))
    refusal = refuse_human_answers(
        answers,
        known_ids=run.decomposer.tasks,
        human_ids=human_task_ids,
        failed_or_held={
            tid for tid in answers
            if state.get_task_status(tid) == "failed" or tid in held_by
        },
        resume_typed=run.mode.resume_typed,
    )
    if refusal is not None:
        return _refuse_answer(refusal)
    state.record_human_task_answers({
        tid: action for tid, action in answers.items()
        if action != "retry"  # one-shot: never carried into a later run
    })
    state.save()
    for task_id, action in sorted(answers.items()):
        print(f"[HUMAN_TASK_ANSWERED] {task_id}={action}")
    return None


def resolve_scope(run: ImplementRun) -> Optional[int]:
    """D6 row 16: the scope policy this run's prompts follow.

    The typed ``--scope-policy``, else this implement run's live recorded
    choice, else expand. A typed one is kept, so the resume that never
    repeats the flag (``--resume --human-task …``) renders the same prompts.
    ``--fresh`` starts the implementation over: a new run, which never
    inherits an earlier run's recorded choice (as under ``full --force``).
    """
    args, state = run.args, run.state
    scope_choice = scope_policy_runs.resolve_run_choice(
        getattr(args, "scope_policy", None), state.state, "implement",
        new_run=bool(getattr(args, "fresh", False)))
    dry_run = args.dry_run or getattr(args, "dry_run_subagents", False)
    run.scope_policy, _source, scope_decision = scope_policy_runs.open_run(
        None if dry_run else state, "implement", scope_choice,
        phase_dir=None, unattended=run.unattended,
    )
    if scope_decision:
        run.pending_resolutions.append((scope_policy_runs.SITE_ID, scope_decision))
    return None


def _base_handoff(
    plan_path: Path, state: StateManager, total: int, batches: List[Dict[str, Any]],
    *, pending: Optional[int] = None,
) -> Dict[str, Any]:
    """The handoff JSON's fixed keys: the plan, task list, summary and state
    paths (the task list and the summary also plan-relative, in their
    phase-based subdirectories), the time, the counts and the batches.
    *pending* counts the tasks the batches hold; a ``--task`` rerun has none."""
    data: Dict[str, Any] = {
        "plan_file": str(plan_path.absolute()),
        "tasks_file": str(get_output_paths(plan_path, "tasks", phase='tasks')),
        "summary_file": str(
            get_output_paths(plan_path, "implementation_summary", phase='implement')),
        "tasks_file_relative": get_relative_output_path(plan_path, "tasks", phase='tasks'),
        "summary_file_relative": get_relative_output_path(
            plan_path, "implementation_summary", phase='implement'),
        "state_file": str(state.state_file),
        "generated_at": datetime.now().isoformat(),
        "total_tasks": total,
    }
    if pending is not None:
        data["pending_tasks"] = pending
    data["batches"] = batches
    return data


def build_handoff(run: ImplementRun) -> Optional[int]:
    """The task JSON both legs build their batches from (``run.output_data``):
    the one task ``--task`` names, else every batch still to run."""
    args, state, plan_path, decomposer = run.args, run.state, run.plan_path, run.decomposer
    run.executor_backed = bool(
        getattr(args, "exec_subagents", False)
        or getattr(args, "dry_run_subagents", False)
    )
    if args.task:
        task = decomposer.get_task(args.task)
        if not task:
            print(f"ERROR: Task not found: {args.task}")
            return 1
        if run.human_task_decisions.get(task.id) not in ("done", "skip"):
            _prepare_selected_task(
                task, state, plan_path,
                dry_run=bool(args.dry_run or getattr(args, "dry_run_subagents", False)),
            )
        output_data = _base_handoff(plan_path, state, 1, [{
            "batch_index": 0,
            "can_parallelize": False,
            "tasks": [format_task_for_output(
                task, run.plan_preamble, str(plan_path.absolute()),
                all_tasks=decomposer.tasks)],
        }])
    else:
        output_batches = _batches_to_hand_out(run)
        # The result line counts what dispatches ("0/13 batches"), and a manual
        # task is a graph node that dispatches nothing, so the native leg prints
        # this line once it has taken out what the host must not dispatch
        # (`_native_withheld`), so it agrees with "Pending tasks". Both legs
        # count the batches handed out, never the decomposition's layers; the
        # executor leg's line is the scheduler's, printed once it knows what
        # its run dispatches.
        if args.dry_run:
            print(_dispatch_line({"batches": output_batches}))
        output_data = _base_handoff(
            plan_path, state, len(run.tasks), output_batches,
            pending=sum(len(b["tasks"]) for b in output_batches),
        )

    # The plan as the user typed it, for the closing `util finalize-tracking
    # --plan-file` (the host used to copy the absolute `plan_file`).
    output_data["plan_arg"] = typed_plan_for(plan_path)

    # Under preserve every code task's prompt says not to go beyond it; both
    # legs build their batches from these prompts. Nothing changes under expand.
    _apply_scope_guidance(output_data, run.scope_policy)

    # The resolved answers travel with the tasks, so the invoker copies a
    # decision instead of composing one (D5a).
    if run.human_task_ids:
        output_data["human_tasks"] = list(run.human_task_ids)
        output_data["human_task_strategy"] = run.human_task_strategy
        if run.human_task_decisions:
            output_data["human_task_decisions"] = dict(
                state.get("human_task_decisions") or {}
            )
    run.output_data = output_data
    return None


def _batches_to_hand_out(run: ImplementRun) -> List[Dict[str, Any]]:
    """Every batch still to run, as the handoff lists them. A resume skips
    finished tasks but hands out again a check whose findings stand (on the
    native leg only once the files moved: ``_native_check_reruns``) and a
    task recorded done whose change never landed."""
    state, plan_path = run.state, run.plan_path
    batches = run.decomposer.get_parallel_batches()
    rerun_ids = rerunnable_checks(state.state) if run.mode.resume else None
    if rerun_ids and not run.executor_backed:
        rerun_ids, run.kept_checks = _native_check_reruns(
            state, plan_path, rerun_ids,
            _applicable_from_state(state, run.human_task_ids, run.human_task_decisions),
        )
    if run.mode.resume:
        unlanded = _unlanded_on_record(plan_path, state)
        if unlanded:
            rerun_ids = sorted(set(rerun_ids or []) | set(unlanded))
    return format_batches_for_output(
        batches, skip_completed=run.mode.resume, plan_preamble=run.plan_preamble,
        plan_path=str(plan_path.absolute()), all_tasks=run.decomposer.tasks,
        rerun_ids=rerun_ids,
    )


def print_dry_run(run: ImplementRun) -> Optional[int]:
    """``--dry-run``: print the task summary and stop with exit 0, before
    anything is written for the host."""
    if not run.args.dry_run:
        return None
    print("\n" + "=" * 60)
    print("Task Summary (Dry Run)")
    print("=" * 60)
    summary = run.decomposer.get_progress_summary()
    print(f"Total tasks: {summary['total']}")
    print(f"Completed: {summary['by_status']['completed']}")
    print(f"Pending: {summary['by_status']['pending']}")
    print(f"Failed: {summary['by_status']['failed']}")
    print(f"\nBatches: {len(run.output_data['batches'])}")

    for batch in run.output_data["batches"]:
        print(f"\n  Batch {batch['batch_index']}:")
        for task in batch["tasks"]:
            print(f"    - {task['id']}: {task['title']} ({task['executor_role']})")

    print(f"\nWould write to: {run.args.output}")
    return 0


def _write_native_handoff(run: ImplementRun) -> None:
    """Write the task JSON for its one reader, the native leg's driving agent,
    which the ``Output file:`` line hands it. The write executor reads
    ``write_tasks.json`` in the phase dir instead, so an ``--exec-subagents``
    run never creates ``.multi-llm/tmp/``. ``--detach`` without the executor
    still writes it: the worker re-enters ``main`` and reaches this itself."""
    output_path = run.output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    _write_temp_dir_gitignore(output_path.parent)
    output_path.write_text(json.dumps(run.output_data, indent=2), encoding="utf-8")


def prepare_native_emit(run: ImplementRun) -> Optional[int]:
    """The start-over (:func:`start_over_when`), the answers this run applies,
    and on the native leg everything its emit decides before the detach
    boundary: the human-task plan, what it withholds, the task JSON, and
    whether the emit stops on a manual task (:func:`native_gate_applies`)."""
    args, state, plan_path, output_data = run.args, run.state, run.plan_path, run.output_data
    run.start_over_at = start_over_when(
        start_over=run.mode.start_over,
        executor_backed=run.executor_backed,
        detach=bool(getattr(args, "detach", False)),
        internal_worker=bool(getattr(args, "internal_worker", False)),
    )
    if run.start_over_at is StartOver.BEFORE_EMIT:
        _start_over(state, plan_path, run.decomposer.tasks.values())

    # The answers both legs apply this run: every human task's, and a code
    # task's only while it still applies (`_applicable_task_decisions`).
    run.applicable_decisions = _applicable_from_state(
        state, run.human_task_ids, run.human_task_decisions,
        rerun_task=str(args.task) if args.task else None,
    )
    if run.executor_backed:
        return None

    _plan_native_human_tasks(run)
    run.native_withheld = _native_withheld(
        output_data, state, plan_path,
        kept_checks=run.kept_checks, tasks_file=run.tasks_file,
    )
    # The tasks the plan set aside, which the host's N/N `[ETA]` line names,
    # as the executor's does. Replaced by every native emit.
    state.set_metrics_set_aside(
        "implement", set_aside_by_plan(run.native_human_plan, run.human_task_ids),
    )
    output_data["tasks_to_dispatch"] = _handoff_counts(output_data)["dispatch"]
    if not args.task:
        print(_dispatch_line(output_data))
    _write_native_handoff(run)
    # An emit that hands out nothing because every code task left waits on a
    # manual task not recorded done is a stop for the user, as on the
    # executor leg.
    if native_gate_applies(
        withheld=run.native_withheld,
        rerun_task=bool(args.task),
        has_human_plan=run.native_human_plan is not None,
        kept_checks=bool(run.kept_checks),
        tasks_to_dispatch=output_data["tasks_to_dispatch"],
        implement_completed=state.is_phase_completed("implement"),
    ):
        run.native_gate = _native_manual_gate_stop(run.native_human_plan, output_data, state)
    return None


def _plan_native_human_tasks(run: ImplementRun) -> None:
    """The native leg's human-task plan (``run.native_human_plan``).

    Resolved here, from the strategy and the answers already held, exactly as
    the executor resolves it before its first batch, so the skips are in the
    task JSON the host reads and are written to state.json by
    :func:`record_emit`, not left for the host to record. Also with no manual
    task in the plan whenever an answer applies: a failed code task's
    ``done``/``skip`` must change what this leg hands out.
    """
    args, state, output_data = run.args, run.state, run.output_data

    answered_on_record = answered_done_on_record(
        state,
        exclude=[
            str(task.get("id") or "")
            for batch in output_data.get("batches") or []
            for task in batch.get("tasks") or []
        ],
    )
    if not (run.human_task_ids or run.applicable_decisions or any(answered_on_record)):
        return
    plan = run.native_human_plan = _native_human_task_plan(
        output_data,
        strategy=run.human_task_strategy,
        decisions=run.applicable_decisions,
        on_record=answered_on_record,
        recorded_statuses=state.get_all_task_statuses(),
        check_findings_ids=rerunnable_checks(state.state),
        state_record=state.state,
    )
    # How to record the deferred manual tasks done, in this host's spelling,
    # for the host's summary and report. The manual tasks only: a code task
    # skipped with one runs on that resume.
    manual_ids = sorted(
        set(plan.deferred()) & {str(t) for t in run.human_task_ids}
    )
    # Only the manual tasks the user can do now, and the note says what waits
    # on them.
    native_gates = _native_manual_gates(plan, output_data, state)
    waiting = 0
    if native_gates is not None:
        # What each later manual task comes after, for its line in the
        # deferred list.
        run.native_after = dict(native_gates.get("after") or {})
        manual_ids = [t for t in manual_ids if t in native_gates["closable"]]
        waiting = len({
            code for task_id in manual_ids
            for code in native_gates["waiting"].get(task_id, ())
        })
    note = (
        _manual_close_note(
            args, str(output_data["plan_arg"]), manual_ids, waiting=waiting)
        if manual_ids else None
    )
    if note:
        output_data["manual_tasks_note"] = note


def cross_detach_boundary(run: ImplementRun) -> Optional[int]:
    """The detach boundary (D4), then the D6 decisions buffered before it.

    Crossed before the write executor and independently of it: ``implement``
    is registered ``supports_detach=True``, so ``--detach`` must produce a
    worker and a ``.status.json`` whether or not ``--exec-subagents`` was
    passed. Past it this process owns the phase dir (the foreground run, or
    the detached worker once it has claimed it), so the buffered decisions
    are written where ``status`` reads them (``run.resolutions``). Quietly:
    the marker line already printed at the decision site, and printing it
    twice would make one decision read as two.
    """
    detached = maybe_detach_implement_phase(run.args, plan_path=run.plan_path)
    if detached is not None:
        return detached
    if run.pending_resolutions:
        resolutions_phase_dir = str(get_phase_dir(run.plan_path, "implement"))
        for site_id, decision in run.pending_resolutions:
            unattended_mod.record_resolution(
                resolutions_phase_dir, site_id, decision, quiet=True
            )
    return None


def run_executor_leg(run: ImplementRun) -> Optional[int]:
    """The write executor (D3n) schedules the batches in this process;
    ``None`` on the native leg, which goes on to :func:`emit_native`.

    Its start-over comes here, past the detach boundary. The reset consumes
    earlier code-task answers, including skips, so the answers are resolved
    again from the state it leaves, as the native leg does after its reset.
    """
    if run.start_over_at is StartOver.AFTER_DETACH:
        _start_over(run.state, run.plan_path, run.decomposer.tasks.values())
        run.applicable_decisions = _applicable_from_state(
            run.state, run.human_task_ids, run.human_task_decisions,
        )
    return run_implement_write_phase(
        run.args,
        plan_path=run.plan_path,
        state=run.state,
        output_data=run.output_data,
        human_task_strategy=run.human_task_strategy,
        human_task_decisions=run.applicable_decisions,
        tasks_file=run.tasks_file,
    )


def emit_native(run: ImplementRun) -> Optional[int]:
    """The native leg's emit: ``write_tasks.json``, the report the driving
    agent reads (:func:`render_native_report`), and its closing steps
    (:func:`closing_steps`), or the stop on a manual task."""
    args, state, plan_path = run.args, run.state, run.plan_path
    # The same `write_tasks.json` the executor leg materializes, so the host's
    # per-task `util write-prompt` binds each task's prior-changes context from
    # the same seam instead of the host fishing the prompt out of the handoff
    # JSON and substituting the token by hand.
    try:
        write_task_file, native_tasks = _materialize_native_write_tasks(
            plan_path, run.output_data, tasks_file=run.tasks_file,
            host=resolve_host_id(explicit=getattr(args, "host", None)),
        )
    except Exception as exc:  # noqa: BLE001 - the handoff JSON is still usable
        print(f"WARNING: write_tasks.json not written: {exc}", file=sys.stderr)
    else:
        print(f"[WRITE_TASKS_FILE] {write_task_file}", file=sys.stderr)
        # A native `--resume` promises to skip what already ran: a task the
        # implement log already holds and no record says finished is refused
        # rather than handed out a second time.
        if _refuse_unrecorded_native_resume(
            native_tasks, plan_path=plan_path, state=state,
            resume=bool(run.mode.resume and not args.task),
        ):
            return 3

    # An explicit native `--resume` says what it kept, as the continued run
    # and the executor leg's scheduler do.
    if run.mode.resume_typed and not args.task:
        kept_line = _native_kept_line(
            state, run.decomposer.tasks, run.output_data, run.native_human_plan,
        )
        if kept_line:
            print(kept_line)

    for line in render_native_report(run):
        print(line)
    if run.native_gate is not None:
        return _stop_on_native_gate(run)

    # A resume of a completed implement that only records answers
    # (`--human-task T007=done` closing a deferred manual task) hands out
    # nothing to run: it does not reopen the phase, and asks for no summary
    # and no close (`closing_steps`).
    run.closes = not args.task and _closes_a_completed_implement(state, run.output_data)
    for line in closing_steps(
        closes=run.closes, stopped_short=_stopped_short(run),
        summary_file=run.output_data["summary_file"],
    ):
        print(line)
    return None


def _stopped_short(run: ImplementRun) -> bool:
    """Tasks the native emit lists as withheld, or a check kept with its
    findings, will not run: the phase closes without ``--mark-completed``."""
    withheld = run.native_withheld
    return withheld is not None and bool(
        run.kept_checks or any(withheld[key] for key in withheld)
    )


def _stop_on_native_gate(run: ImplementRun) -> int:
    """The native emit's stop on a manual task: its block, its closing
    ``[ETA]`` line, and the records a resume reads — the plan's deferrals
    and implement started (never completed), so ``util next-command``
    answers its resume. Exit 3."""
    state = run.state
    lines, headline, eta_line = run.native_gate
    print(eta_line)
    for line in lines:
        print(line)
    state.set_metrics_left_out("implement", {})
    state.set_metrics_set_aside("implement", {})

    persist_human_task_plan(state, run.native_human_plan)
    state.mark_phase_started("implement")
    state.save()
    record_error(headline)
    return 3


def render_native_report(run: ImplementRun) -> List[str]:
    """The native emit's report to the driving agent, as lines: the summary
    block, then what the human-task plan and ``_native_withheld`` keep out of
    the batches, each list with what the host does about it. Reads the run
    and the state in memory only; writes nothing."""
    state, output_data = run.state, run.output_data
    titles = dict(state.get("task_titles") or {})

    def named(task_id: str) -> str:
        title = titles.get(task_id)
        return f"{task_id}{' ' + title if title else ''}"

    lines = [
        "\n" + "=" * 60,
        "Tasks Prepared for the Driving Agent",
        "=" * 60,
        f"Output file: {run.output_path}",
        f"State file: {state.state_file}",
        f"Total tasks: {output_data['total_tasks']}",
        f"Pending tasks: {output_data.get('pending_tasks', output_data['total_tasks'])}",
        f"Batches: {len(output_data['batches'])}",
    ]
    if "tasks_to_dispatch" in output_data and run.native_gate is None:
        # The one number the host passes to `util metrics`, in the [ETA]
        # line's unit: one record per task dispatched, and `util batch-done`
        # takes a task out of it once a record keeps that task from running.
        dispatch = output_data["tasks_to_dispatch"]
        lines.append(
            f"Tasks to dispatch: {dispatch} (pass --total-batches {dispatch} to "
            f"`util metrics start` and `util metrics record`; the [ETA] line "
            f"counts tasks, not batches, and leaves out a task that a "
            f"`util batch-done` record keeps from running)"
        )
    if run.native_human_plan is not None:
        lines += _human_plan_lines(run, named)
    if run.native_withheld is not None:
        lines += _withheld_lines(run, named)
    return lines


def _human_plan_lines(run: ImplementRun, named: Callable[[str], str]) -> List[str]:
    """:func:`render_native_report`'s lists from the human-task plan:
    deferred, skipped at the user's request, accepted, completed by hand."""
    plan, output_data = run.native_human_plan, run.output_data
    lines: List[str] = []
    deferred = plan.deferred()
    declined = plan.declined()
    if deferred and run.native_gate is not None:
        # Nothing runs and no summary is written; the report's closing
        # section gives the resume that records the manual task done, so no
        # note repeats its command here.
        lines.append(
            "Deferred tasks (recorded skipped in state.json; do not "
            "dispatch them; name them in your report):"
        )
        for task_id, reason in sorted(deferred.items()):
            lines.append(f"  {named(task_id)}: {reason}")
    elif deferred:
        note = output_data.get("manual_tasks_note")
        lines.append(
            "Deferred tasks (recorded skipped in state.json; do not "
            "dispatch them, and list them in the summary's Manual Tasks "
            "(Deferred) section"
            + (", with the text of the [MANUAL_TASK_NOTE] line below the "
               "list under it, verbatim; give that text in your report "
               "too" if note else "")
            + "):"
        )

        for task_id, reason in sorted(deferred.items()):
            # A manual task after code this emit hands out says so; the
            # report's lookup gives its command.
            after = run.native_after.get(task_id)
            lines.append(f"  {named(task_id)}: {reason}"
                         + (f" {after_code_note(after)}" if after else ""))
        if note:
            lines.append(f"[MANUAL_TASK_NOTE] {note}")
    if declined:
        # Not owed: the workflow's `[MANUAL_TASK]` lines leave these out, so
        # a summary that filed them under Manual Tasks (Deferred) would
        # disagree with `[WORKFLOW_COMPLETE]`.
        lines.append(
            "Skipped at your request (recorded skipped in state.json; do "
            "not dispatch them, and list them in the summary under a "
            "separate 'Skipped at your request' heading, not under Manual "
            "Tasks (Deferred) — they are not owed):"
        )
        for task_id, reason in sorted(declined.items()):
            lines.append(f"  {named(task_id)}: {reason}")
    if plan.accepted:
        # A check whose findings the user accepted never failed, so the words
        # are the executor's (`answered_done_label`), never "accepted after
        # failing" for every one.
        labels = {
            task_id: answered_done_label(plan, task_id)
            for task_id in plan.accepted
        }
        kinds = sorted(set(labels.values()))
        heading = (
            kinds[0][:1].upper() + kinds[0][1:] if len(kinds) == 1
            else "Accepted on your answer"
        ).replace("its check findings", "their check findings")
        lines.append(
            f"{heading} (recorded completed in state.json; not in the "
            f"batches, do not dispatch or record them; list them in the "
            + (
                f"summary as {kinds[0].replace('its check findings', 'their check findings')}):"
                if len(kinds) == 1 else
                "summary with the words in brackets after each id):"
            )
        )
        for task_id, reason in sorted(plan.accepted.items()):
            label = f" ({labels[task_id]})" if len(kinds) > 1 else ""
            lines.append(f"  {named(task_id)}{label}: {reason}")
    if plan.completed:
        lines.append(
            "Completed by hand (manual tasks recorded completed in "
            "state.json; do not dispatch or record them; list them in the "
            "summary as completed by hand):"
        )
        for task_id in sorted(plan.completed):
            lines.append(f"  {named(task_id)}: answered --human-task {task_id}=done")
    return lines


def _withheld_lines(run: ImplementRun, named: Callable[[str], str]) -> List[str]:
    """:func:`render_native_report`'s lists of what ``_native_withheld`` keeps
    out of the batches, and the line for an emit with nothing to dispatch."""
    withheld, output_data = run.native_withheld, run.output_data
    lines: List[str] = []
    for check_id, findings in sorted(run.kept_checks.items()):
        waiting = sorted(
            task_id for task_id, reason in withheld["held"].items()
            if reason.startswith(f"not run — upstream check {check_id} ")
        )
        lines.append(
            f"[CHECK_NOT_RERUN] {check_id} is not run again: nothing in the "
            f"repository changed since its check reported problems, so it "
            f"would report the same"
            + (f" ({clip('; '.join(findings), 300)})" if findings else "")
            + ". Its findings stand"
            + (
                f", and {', '.join(waiting)} "
                f"{'stays' if len(waiting) == 1 else 'stay'} held behind it"
                if waiting else ""
            )
            + "."
        )
    if withheld["held"]:
        lines.append(
            "Held back by a check with findings (pending in state.json; not "
            "in the batches, do not dispatch or record them; list them in "
            "the summary as not run):"
        )
        for task_id, reason in sorted(withheld["held"].items()):
            lines.append(f"  {named(task_id)}: {reason}")
    if withheld["refused"]:
        lines.append(
            "Refused before dispatch (recorded failed in state.json; not in "
            "the batches, do not dispatch or record them; list them in the "
            "summary as failed, refused before dispatch; in your report give "
            "each one's way forward as its line words it, the user's call, "
            "and never change driver.write_paths yourself):"
        )
        for task_id, reason in sorted(withheld["refused"].items()):
            lines.append(f"  {named(task_id)}: {reason}")
    if withheld["not_run"]:
        lines.append(
            "Not run because a task they depend on was refused (not in the "
            "batches, do not dispatch or record them; list them in the "
            "summary as not run):"
        )
        for task_id, reason in sorted(withheld["not_run"].items()):
            lines.append(f"  {named(task_id)}: {reason}")
    if output_data.get("waiting_on_checks"):
        lines.append(
            "Waiting on a check's verdict (in the batches after the check "
            "they depend on; if the check reports problems, do not dispatch "
            "them — they stay pending and the phase closes without "
            "--mark-completed):"
        )
        for task_id, reason in sorted(output_data["waiting_on_checks"].items()):
            lines.append(f"  {named(task_id)}: {reason}")
    if not output_data["batches"] and run.native_gate is None:
        lines.append(
            "Nothing to dispatch: every task is done, skipped, accepted or "
            "listed above. Do not spawn a subagent; still run step 7's "
            "`util metrics finish`, which prints this run's closing [ETA] "
            "line (no `util metrics start` is needed)."
        )
    return lines


def record_emit(run: ImplementRun) -> Optional[int]:
    """Record the native emit in state.json.

    The batches are now the host's to run, so the phase is recorded
    *started*, never completed: completion is the instruction's closing
    ``util finalize-tracking --plan-file … --mark-completed``, which runs
    only after every task, the verify step and the summary. An emit that
    only records answers on a completed implement leaves it completed.
    The human-task plan is written as the executor's ``_persist_human_plan``
    writes it before its first batch: the deferred manual tasks (and the
    dependents skipped with them) as ``skipped`` with their reasons, a
    ``done`` answer as completed, the skip-continue overrides.
    """
    state = run.state
    if run.native_human_plan is not None:
        persist_human_task_plan(state, run.native_human_plan)
    if not run.closes:
        state.mark_phase_started("implement")
    state.save()
    return None


def main(argv: Optional[List[str]] = None) -> int:
    """Run ``implement``: each stage in order, until one returns an exit code.

    The stages are in the order the invariants need: nothing is saved before
    the row-6 gate clears (:func:`run_prerequisite_gates`); the native leg's
    start-over runs before its emit reads the records and the executor leg's
    past the detach boundary (:func:`start_over_when`); the buffered D6
    decisions are written only once this process owns the phase dir
    (:func:`cross_detach_boundary`).
    """
    bootstrap_streams()
    args = parse_args(argv)
    run = ImplementRun(args=args, unattended=bool(getattr(args, "yes", False)))
    stages = (
        check_answers_flags,
        open_run,
        run_prerequisite_gates,
        load_task_list,
        apply_run_mode,
        record_human_answers,
        resolve_scope,
        build_handoff,
        print_dry_run,
        prepare_native_emit,
        cross_detach_boundary,
        run_executor_leg,
        emit_native,
        record_emit,
    )
    for stage in stages:
        code = stage(run)
        if code is not None:
            return code
    return 0


def _closes_a_completed_implement(state: StateManager, output_data: Dict[str, Any]) -> bool:
    """Whether this native emit only answers tasks of an implement already done.

    True when ``implement`` is on record completed and the handoff holds no
    code task left to run — every task it lists is a manual one or already
    ``completed``/``skipped``. Never asked for ``--task``,
    which hands one task out to be run again whatever its status.
    """
    if not state.is_phase_completed("implement"):
        return False
    for batch in output_data.get("batches") or []:
        for task in batch.get("tasks") or []:
            if task.get("executor_role") == "human" or task.get("is_human"):
                continue
            if task.get("status") not in ("completed", "skipped"):
                return False
    return True


if __name__ == "__main__":
    from utils import process_control

    # A process entry of its own: provider children must stay this process's.
    process_control.restore_sigchld_default()
    sys.exit(main(sys.argv[1:]))
