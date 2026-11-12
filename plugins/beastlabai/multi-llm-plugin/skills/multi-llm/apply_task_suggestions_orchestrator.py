#!/usr/bin/env python3
"""
Orchestrator for applying validated task suggestions to a tasks.md file.

This script reads validation results from a task review and outputs
the list of suggestions that should be applied. The actual application
is handled by Claude Code using Task subagents sequentially.

Usage:
    uv run --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" apply-task-suggestions plans/my-plan.md [options]
"""

import contextlib
import io
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.stream_bootstrap import bootstrap_streams
from utils.apply_orchestrator_base import (
    OrchestratorError, build_common_arg_parser, target_backup_name,
)
from utils.apply_suggestion_phase import SuggestionApplyPhase
from utils.cli_common import dispatcher_prefix
from utils.apply_output_helpers import (
    build_skipped_output,
    write_and_emit_output,
)
from utils.state_manager import StateManager
from utils.suggestion_batcher import (
    PRIOR_BATCHES_SECTION,
    SuggestionBatch,
    format_suggestion_block,
)
from utils.tasks_file import find_tasks_file
from utils.tasks_graph_check import tasks_graph_warnings


class ApplyTaskSuggestionsOrchestrator(SuggestionApplyPhase):
    """Thin subclass for the apply-task-suggestions phase."""

    phase_name = "apply-task-suggestions"
    review_subdir = "review-tasks"
    item_noun = "task suggestion"
    supports_revalidation = False
    supports_skip_flag = True
    guard_double_nesting = False
    # One shared artifact (the tasks file), so batches are strictly sequential.
    write_kind = "apply_task_suggestions"
    phase_dir_key = "apply_task_suggestions_dir"
    summary_title = "TASK SUGGESTIONS TO APPLY (BATCHED)"

    # Instance state populated by pre_validate_hook
    tasks_file: str = ""

    def write_phase_artifact(self) -> str:
        """The tasks file, not the plan: that is what these batches edit (D3h)."""
        return self.tasks_file or self.plan_path

    def _completed_target_label(self) -> Optional[str]:
        """The task list, found as ``pre_validate_hook`` finds it: the
        ``--mark-completed`` call runs before that hook, and without it
        ``write_phase_artifact`` would name the plan (fix round 26)."""
        if not self.tasks_file:
            try:
                with contextlib.redirect_stderr(io.StringIO()):
                    self.tasks_file = find_tasks_file(self.plan_path)
            except (OSError, ValueError):
                return None
        return super()._completed_target_label()

    def write_target_backup(self) -> Optional[str]:
        """Already taken, under the name this phase's own output publishes.

        `_target_output_fields` copies tasks.md to `{phase}/tasks-backup.md` before
        any batch runs (kept across a resume, so it still holds the pre-phase
        bytes) and hands the path back as `tasks_file_backup`, which
        `instructions/apply-task-suggestions.md` tells the agent to preserve. A
        second copy named `backup.md` would be the same bytes under a name
        nothing references, so the base's snapshot is answered rather than run.
        """
        path = os.path.join(self.out_dir, self.phase_name, target_backup_name(self.phase_name))
        return path if os.path.isfile(path) else None

    # ----------------------------------------------------------------
    # Argument parser
    # ----------------------------------------------------------------

    def consistency_warnings(self) -> List[str]:
        """The task graph of ``tasks.md`` as the batches left it (issue 10)."""
        try:
            with open(self.tasks_file, "r", encoding="utf-8") as handle:
                return tasks_graph_warnings(handle.read())
        except (OSError, UnicodeDecodeError):
            return []

    @classmethod
    def parse_args(cls, argv=None):
        """Build and parse CLI arguments for apply-task-suggestions."""
        # Printed commands, so resolved from `__file__` and never a skill-dir
        # placeholder (see review_plan_orchestrator.parse_args for why).
        run = dispatcher_prefix()
        parser = build_common_arg_parser(
            description="Prepare validated task suggestions for application to tasks.md",
            epilog=f"""
This orchestrator outputs a JSON list of task suggestions to apply.
The actual application is handled by Claude Code using Task subagents.

Example:
  {run} apply-task-suggestions plans/my-plan.md

Bulk Approval Examples:
  # Auto-approve all LOW importance items
  {run} apply-task-suggestions plans/my-plan.md --approve-all-low

  # Skip all items requiring human review
  {run} apply-task-suggestions plans/my-plan.md --skip-all-human
        """,
            include_skip=True,
            include_output_format=True,
            include_mark_completed=True,
        )
        return parser.parse_args(argv)

    # ----------------------------------------------------------------
    # Hooks
    # ----------------------------------------------------------------

    def pre_validate_hook(self) -> None:
        """Discover tasks_file and check prerequisite phases."""
        # Find tasks file
        try:
            self.tasks_file = find_tasks_file(self.plan_path)
        except FileNotFoundError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            raise OrchestratorError(str(e), exit_code=1) from e
        except ValueError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            raise OrchestratorError(str(e), exit_code=1) from e

        print(f"Tasks file: {self.tasks_file}", file=sys.stderr)

        # Batch prompts no longer embed a snapshot of this file (F7): all 11
        # batches used to carry the identical header/dependency-graph excerpt
        # frozen at this point, which was exactly what each batch's own
        # instructions told it to regenerate — by the last few batches the
        # "reference" text was stale. Each prompt now just tells the runner to
        # read the live file first, so there is nothing left to read here.

        # Prerequisite check: review-tasks must be completed or skipped
        state = StateManager(Path(self.plan_path))
        if not state.is_phase_completed("review-tasks") and not state.is_phase_skipped("review-tasks"):
            print("ERROR: review-tasks phase has not been completed.", file=sys.stderr)
            print("       Run --review-tasks first before applying task suggestions.", file=sys.stderr)
            raise OrchestratorError(
                "review-tasks phase has not been completed", exit_code=1
            )

    def handle_no_items_early_exit(self) -> None:
        """Write empty output and mark phase skipped when no items remain."""
        # Determine skip reason
        if self.user_skipped_items:
            skip_reason = "all suggestions skipped by user"
            skip_message = "All task suggestions were skipped by user selections"
        else:
            skip_reason = "no actionable findings from review-tasks"
            skip_message = "No actionable task suggestions remain after filtering"

        # Dry runs stay read-only: both of them, `write_target_backup`'s
        # two-flag rule, since a `--dry-run-subagents` preflight that recorded
        # the skip would have a later real run read the phase skipped (the
        # apply-code-fixes twin of this exit, Fable review 2026-10-09).
        dry = getattr(self.args, "dry_run", False) or getattr(
            self.args, "dry_run_subagents", False
        )
        if not dry and self.state is not None:
            self.state.mark_phase_skipped(self.phase_name, skip_reason)
            self.state.save()

        # Write empty orchestrator_output.json
        phase_dir = os.path.join(self.out_dir, self.phase_name)
        os.makedirs(phase_dir, exist_ok=True)
        output = {
            "status": "skipped",
            "message": skip_message,
            "phase": self.phase_name,
            "batches": [],
            "to_apply": [],
            "needs_human_review": [],
            "skipped_items": self.formatted_skipped,
            "user_skipped_items": self.user_skipped_items,
            "skipped_count": len(self.skipped),
            "user_skipped_count": len(self.user_skipped_items),
            "summary": {
                "total_groups": len(self.groups),
                "valid_count": 0,
                "needs_human_count": 0,
                "skipped_count": len(self.skipped),
                "user_skipped_count": len(self.user_skipped_items),
                "batch_count": 0,
            },
        }
        write_and_emit_output(output, phase_dir)
        self.emit_payload(output)
        sys.exit(0)

    # ----------------------------------------------------------------
    # Phase hooks
    # ----------------------------------------------------------------

    def _validation_missing(
        self, validation_path: Path, groups: Optional[List[Dict[str, Any]]]
    ) -> None:
        """A review with no findings writes no validation: the phase is
        skipped (exit 0). Groups without validation are an error."""
        if groups:
            super()._validation_missing(validation_path, groups)
        skip_reason = "no actionable findings from review-tasks"
        print(
            "No actionable task suggestions found — skipping apply-task-suggestions phase.",
            file=sys.stderr,
        )
        if self.state is not None:
            self.state.mark_phase_skipped(self.phase_name, skip_reason)
            self.state.save()
        # Write empty output
        phase_dir = os.path.join(self.out_dir, self.phase_name)
        output = build_skipped_output(
            self.phase_name,
            "No actionable task suggestions found — skipping apply-task-suggestions phase.",
        )
        write_and_emit_output(output, phase_dir)
        self.emit_payload(output)
        sys.exit(0)

    def _reference_fields(self, reference: str) -> Dict[str, Any]:
        """``task_reference``: ``Task T###`` when the reference names a task id."""
        task_reference = ""
        if reference:
            task_match = re.search(r"(T\d+)", reference)
            if task_match:
                task_reference = f"Task {task_match.group(1)}"
            else:
                task_reference = reference
        return {"task_reference": task_reference}

    def _target_output_fields(self, phase_dir: str) -> Dict[str, Any]:
        """The tasks file, backed up before any batch edits it."""
        # Backup tasks.md before any modifications. A resumed run finds the
        # file as the failed batch left it — half-applied, by design — so the
        # backup a previous run took is the one that still holds the pre-phase
        # bytes, and it is kept rather than overwritten (measured 2026-09-15:
        # three resumes in a row each copied the partial edits over it).
        tasks_backup_path = os.path.join(phase_dir, target_backup_name(self.phase_name))
        if getattr(self.args, "resume", False) and os.path.isfile(tasks_backup_path):
            print(
                f"Tasks file backup kept from the previous run: {tasks_backup_path}",
                file=sys.stderr,
            )
        else:
            if getattr(self.args, "fresh", False):
                # `--fresh` re-stamps, but never over a rollback point: an
                # earlier backup with other bytes is kept beside the new one.
                kept = self.keep_backup_aside(tasks_backup_path, self.tasks_file)
                if kept:
                    print(
                        f"Earlier tasks file backup kept at {kept} (its bytes "
                        f"differ from the file --fresh is about to back up)",
                        file=sys.stderr,
                    )
            shutil.copy2(self.tasks_file, tasks_backup_path)
            print(f"Tasks file backup: {tasks_backup_path}", file=sys.stderr)
        return {"tasks_file": self.tasks_file, "tasks_file_backup": tasks_backup_path}

    def _summary_target_lines(self) -> List[str]:
        return [f"Tasks file: {self.tasks_file}"]

    # ----------------------------------------------------------------
    # Private helpers
    # ----------------------------------------------------------------

    def _generate_single_batch_prompt(self, batch: SuggestionBatch) -> str:
        """Generate a task-specific prompt for a single batch."""
        suggestions = batch.suggestions
        if not suggestions:
            raise ValueError("Cannot format prompt for empty batch")

        type_instructions = """
## Task-Specific Edit Rules

For each suggestion type, follow these rules precisely:

### Addition
- Add new task(s) using `### Task T0XX:` format
- Assign the next available ID (scan existing IDs to determine the highest, then increment)
- New tasks MUST include ALL canonical fields:
  - `files_to_modify` (list of files to change)
  - `files_to_create` (list of new files, if any)
  - `estimated_complexity` (low/medium/high)
  - `executor_role` — rendered as `**Executor**: agent`, or as
    `**Type**: Manual (user action required)` when the task is for a human
  - `depends_on` (list of prerequisite task IDs, or empty)
  - Acceptance criteria (bulleted list)
- After adding, regenerate the dependency graph and update header metadata (task count, complexity summary)

### Modification
- Update the specified task fields (description, dependencies, acceptance criteria, etc.)
- Modified tasks MUST preserve or explicitly update ALL canonical fields
  (`files_to_modify`, `files_to_create`, `estimated_complexity`, `executor_role`,
  acceptance criteria) — never silently drop fields; a task rendered as
  `**Type**: Manual (user action required)` stays manual unless the suggestion
  says otherwise
- If changing `depends_on`, regenerate the dependency graph and update header metadata

### Deletion
- Remove the specified task entirely
- Clean up `depends_on` references to the deleted task ID in ALL other tasks
- Surviving tasks MUST NOT be renumbered — IDs are stable identifiers
- After deletion, regenerate the dependency graph and update header metadata (task count, complexity summary)

### Clarification
- Rewrite the task description and/or acceptance criteria for clarity
- ALL canonical fields must be preserved — do not remove or alter fields that are not being clarified

### Consistency across tasks (every type)
- A task graph is edited by many batches and nobody reads it whole afterwards, so keep it consistent yourself
- Work moved into one task (a helper, a field, a function) must be removed from, or re-pointed in, the task that used to own it — never leave two tasks that both define it
- A task that now uses something another task defines MUST list that task in `depends_on`; a new task goes where the tasks that depend on it can follow it, not last, and gets an ID no existing task has
- Before you finish, re-read every task you touched and every task that depends on one, and fix any disagreement in IDs, dependencies or ordering
"""

        if len(suggestions) == 1:
            s = suggestions[0]
            return f"""Apply the following task suggestion to the tasks file.

**Target file (to edit)**: {self.tasks_file}
**Plan file (context only)**: {self.plan_path}

This prompt was materialized before any batch ran, so it carries no snapshot of
tasks.md — earlier batches in this run may have already changed its header
metadata and dependency graph. Read the file (step 1 below) before editing it.

**Suggestion**: {s.get('title', 'Untitled')}
**Type**: {s.get('type', 'modification')}
**Task reference**: {s.get('reference', 'N/A')}
**Importance**: {s.get('importance', 'MEDIUM')}

**Details**:
{s.get('description', 'No description provided.')}

## Changes Applied in Prior Batches
(Review these to avoid redoing work — do NOT re-apply these changes)

{{prior_changes_context}}
{type_instructions}
## Instructions

1. Read the current tasks.md file
2. Locate the task mentioned in the reference (if applicable)
3. Apply the suggested change following the type-specific rules above
4. Ensure the change integrates smoothly with surrounding content
5. Check if the tasks file already contains a similar change (from a previously applied suggestion). If so, skip this suggestion or merge it with the existing content rather than duplicating
6. After any structural edit (addition, deletion, dependency change), regenerate the dependency graph and update header metadata
7. Do NOT make any other changes beyond this specific suggestion

Return a brief summary of what was changed."""

        # Multiple suggestions — batch format
        section_info = f" (Section: {batch.section_key})" if batch.section_key != "unknown" else ""

        prompt_parts = [
            f"Apply the following {len(suggestions)} related task suggestions to the tasks file{section_info}:",
            f"\n**Target file (to edit)**: {self.tasks_file}",
            f"**Plan file (context only)**: {self.plan_path}",
            f"**Batch type**: {batch.batch_type}",
            f"**Suggestions in this batch**: {len(suggestions)}",
            "\nThis prompt was materialized before any batch ran, so it carries no "
            "snapshot of tasks.md — earlier batches in this run may have already "
            "changed its header metadata and dependency graph. Read the file "
            "(step 1 below) before editing it.",
        ]

        for i, s in enumerate(suggestions, 1):
            prompt_parts.append(format_suggestion_block(i, s, "Task reference"))

        prompt_parts.append(PRIOR_BATCHES_SECTION)

        prompt_parts.append(f"---{type_instructions}")

        prompt_parts.append("""## Instructions

1. Read the current tasks.md file first
2. Apply ALL suggestions in this batch, processing them in order
3. For each suggestion:
   - Locate the referenced task (if applicable)
   - Apply the change according to its type (addition/modification/deletion/clarification)
   - Follow the type-specific rules above
   - Ensure changes integrate smoothly with surrounding content
4. After any structural edit (addition, deletion, dependency change), regenerate the dependency graph and update header metadata
5. Do NOT make any changes beyond these specific suggestions
6. If suggestions affect the same area, apply them intelligently to avoid conflicts
7. Before applying each suggestion, check if the tasks file already reflects a similar change (from a previously applied batch). If a suggestion is already addressed, note it as "already applied" in the summary and move on

## Return Format

Return a brief summary for EACH suggestion applied:
```
Suggestion 1: [What was changed]
Suggestion 2: [What was changed]
Suggestion N: Already addressed by prior changes - skipped
...
```""")

        return "\n".join(prompt_parts)


def main(argv=None) -> int:
    """Main entry point."""
    bootstrap_streams()
    args = ApplyTaskSuggestionsOrchestrator.parse_args(argv)
    orchestrator = ApplyTaskSuggestionsOrchestrator(args)
    return orchestrator.run()


if __name__ == "__main__":
    from utils import process_control

    # A process entry of its own: provider children must stay this process's.
    process_control.restore_sigchld_default()
    sys.exit(main(sys.argv[1:]))
