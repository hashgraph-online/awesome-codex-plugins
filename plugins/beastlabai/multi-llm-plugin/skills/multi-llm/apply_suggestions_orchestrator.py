#!/usr/bin/env python3
"""
Orchestrator for applying validated suggestions to a plan file.

This script reads validation results from a plan review and outputs
the list of suggestions that should be applied. The actual application
is handled by Claude Code using Task subagents sequentially.

Usage:
    uv run --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" apply-suggestions plans/my-plan.md [options]
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.stream_bootstrap import bootstrap_streams
from utils.apply_orchestrator_base import build_common_arg_parser
from utils.apply_suggestion_phase import SuggestionApplyPhase
from utils.cli_common import dispatcher_prefix
from utils.suggestion_batcher import SuggestionBatch, format_batch_for_prompt


class ApplySuggestionsOrchestrator(SuggestionApplyPhase):
    """Thin subclass for the apply-suggestions phase."""

    phase_name = "apply-suggestions"
    review_subdir = "review-plan"
    item_noun = "suggestion"
    supports_revalidation = True
    supports_skip_flag = True
    guard_double_nesting = False
    # One shared artifact (the plan), so batches are strictly sequential (D3h).
    write_kind = "apply_suggestions"
    # That artifact being the plan is also what makes `--mark-completed` re-stamp
    # `plan_hash`: this phase's own edits are not a human's.
    edits_the_plan = True
    phase_dir_key = "apply_suggestions_dir"
    summary_title = "SUGGESTIONS TO APPLY (BATCHED)"

    # ----------------------------------------------------------------
    # Argument parser
    # ----------------------------------------------------------------

    @classmethod
    def parse_args(cls, argv=None):
        """Build and parse CLI arguments for apply-suggestions."""
        # Printed commands, so resolved from `__file__` and never a skill-dir
        # placeholder (see review_plan_orchestrator.parse_args for why).
        run = dispatcher_prefix()
        parser = build_common_arg_parser(
            description="Prepare validated suggestions for application to a plan",
            epilog=f"""
This orchestrator outputs a JSON list of suggestions to apply.
The actual application is handled by Claude Code using Task subagents.

Example:
  {run} apply-suggestions plans/my-plan.md

Bulk Approval Examples:
  # Auto-approve all LOW importance items
  {run} apply-suggestions plans/my-plan.md --approve-all-low

  # Auto-approve items with validation failures (parsing errors, timeouts)
  {run} apply-suggestions plans/my-plan.md --approve-validation-failed

  # Skip all items requiring human review
  {run} apply-suggestions plans/my-plan.md --skip-all-human

  # Re-run validation on failed items with a different model
  {run} apply-suggestions plans/my-plan.md --revalidate --revalidate-model cursor-agent:opus
        """,
            include_revalidation=True,
            include_output_format=True,
            include_skip=True,
            include_approve_validation_failed=True,
            include_revalidate_all_human=True,
            include_internal_revalidation=True,
            include_mark_completed=True,
        )
        return parser.parse_args(argv)

    # ----------------------------------------------------------------
    # Phase hooks
    # ----------------------------------------------------------------

    def _validation_missing(
        self, validation_path: Path, groups: Optional[List[Dict[str, Any]]]
    ) -> None:
        """No validation, no apply: says so on stderr, then stops."""
        print(
            f"ERROR: Validation results not found at {validation_path}",
            file=sys.stderr,
        )
        print(
            "Run --review-plan first to generate validation results.",
            file=sys.stderr,
        )
        super()._validation_missing(validation_path, groups)

    def _generate_single_batch_prompt(self, batch: SuggestionBatch) -> str:
        """The plan-specific prompt for one batch."""
        return format_batch_for_prompt(batch, self.plan_path)


def main(argv=None) -> int:
    """Main entry point."""
    bootstrap_streams()
    args = ApplySuggestionsOrchestrator.parse_args(argv)
    orchestrator = ApplySuggestionsOrchestrator(args)
    return orchestrator.run()


if __name__ == "__main__":
    from utils import process_control

    # A process entry of its own: provider children must stay this process's.
    process_control.restore_sigchld_default()
    sys.exit(main(sys.argv[1:]))
