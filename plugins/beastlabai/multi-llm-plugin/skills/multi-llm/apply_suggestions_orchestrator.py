#!/usr/bin/env python3
"""
Orchestrator for applying validated suggestions to a plan file.

This script reads validation results from a plan review and outputs
the list of suggestions that should be applied. The actual application
is handled by Claude Code using Task subagents sequentially.

Usage:
    uv run --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" apply-suggestions plans/my-plan.md [options]
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.stream_bootstrap import bootstrap_streams
from utils.apply_orchestrator_base import (
    ApplyOrchestratorBase,
    OrchestratorError,
    build_common_arg_parser,
)
from utils.cli_common import dispatcher_prefix
from utils.text_clip import clip
from utils.judge_vocab import JUDGE_AUTO_DECIDE, JUDGE_DECIDE
from utils.apply_output_helpers import (
    build_skipped_output,
    emit_json_output,
    write_and_emit_output,
)
from utils.apply_path_helpers import load_json_file
from utils.apply_selection_helpers import merge_edited_descriptions
from utils.importance import get_highest_importance
from utils.report_parser import (
    find_edited_descriptions,
    parse_skipped_groups,
    parse_skipped_group_suggestions,
    parse_skipped_suggestions,
    parse_suggestion_validation_overrides,
    parse_validation_overrides_groups,
)
from utils.state_manager import (
    CURRENT_FORMAT_VERSION,
    StateManager,
    load_groups_payload,
    stamp_stable_ids,
)
from utils.suggestion_batcher import (
    SuggestionBatch,
    format_batch_for_prompt,
)
from utils.validation import (
    load_validation_results as load_validation_v2,
)


class ApplySuggestionsOrchestrator(ApplyOrchestratorBase[Dict[str, Any], SuggestionBatch]):
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
    # Abstract method implementations
    # ----------------------------------------------------------------

    def load_data(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Load grouped suggestions and validation from review-plan subdir."""
        review_dir = os.path.join(self.out_dir, self.review_subdir)
        validation_path = Path(review_dir) / "validation.json"

        # Load grouped suggestions
        grouped_path = os.path.join(review_dir, "grouped.json")
        raw = load_json_file(grouped_path)
        groups: Optional[List[Dict[str, Any]]] = None
        if raw is not None:
            groups = load_groups_payload(raw)
            stamp_stable_ids(groups)

        # Check validation file exists
        if not validation_path.exists():
            print(
                f"ERROR: Validation results not found at {validation_path}",
                file=sys.stderr,
            )
            print(
                "Run --review-plan first to generate validation results.",
                file=sys.stderr,
            )
            raise OrchestratorError(
                f"Validation results not found at {validation_path}. "
                "Run --review-plan first to generate validation results.",
                exit_code=1,
            )

        # Load validation using v2 loader
        validation = load_validation_v2(validation_path)

        if groups is None:
            raise OrchestratorError(
                f"Grouped suggestions not found in {self.out_dir}. "
                "Run --review-plan first to generate grouped suggestions.",
                exit_code=1,
            )

        return groups, validation

    def parse_user_edits(self, report_path: str) -> Dict[str, Tuple[str, str]]:
        """Detect and return user-edited descriptions from report.md."""
        return find_edited_descriptions(report_path, self.groups)

    def merge_user_edits(
        self,
        groups: List[Dict[str, Any]],
        edited_descriptions: Dict[str, Tuple[str, str]],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Delegate to shared merge_edited_descriptions helper."""
        return merge_edited_descriptions(groups, edited_descriptions)

    def parse_skips_from_report(
        self, report_path: str
    ) -> Tuple[Set[str], Set[str], Set[str]]:
        """Parse skipped groups and suggestions from report.md."""
        skipped_group_indices = parse_skipped_groups(report_path)
        skipped_suggestion_ids = parse_skipped_group_suggestions(report_path)
        old_skipped_ids = parse_skipped_suggestions(report_path)
        return skipped_group_indices, skipped_suggestion_ids, old_skipped_ids

    def parse_validation_overrides_from_report(
        self, report_path: str
    ) -> Tuple[Dict[str, str], Dict[str, str]]:
        """Parse validation overrides from report.md."""
        group_overrides = parse_validation_overrides_groups(report_path)
        suggestion_overrides = parse_suggestion_validation_overrides(report_path)
        return group_overrides, suggestion_overrides

    def format_item_for_output(self, group: Dict[str, Any], index: int) -> Dict[str, Any]:
        """Format a suggestion group for output to Claude Code."""
        suggestions = group.get("suggestions", [])

        if suggestions:
            primary = suggestions[0]
            title = primary.get("title", group.get("theme", "Unknown"))
            desc = primary.get("desc", "")
            suggestion_type = primary.get("type", "modification")
            reference = primary.get("reference", "")
            importance = primary.get("importance", "MEDIUM")
        else:
            title = group.get("theme", "Unknown")
            desc = ""
            suggestion_type = "modification"
            reference = ""
            importance = "MEDIUM"

        # Combine descriptions if multiple suggestions in group
        if len(suggestions) > 1:
            all_descs = [s.get("desc", "") for s in suggestions if s.get("desc")]
            desc = "\n\n".join(all_descs)

        formatted = {
            "index": index,
            # Stable group identifier so judging subagents / human-decision
            # routing can reference pre-marked items.
            "group_id": group.get("group_hash", ""),
            "title": title,
            "description": desc,
            "type": suggestion_type,
            "reference": reference,
            "importance": importance,
            "theme": group.get("theme", ""),
            "category": group.get("category", ""),
            "validation_status": group.get("validation_status", "valid"),
            "validation_reason": group.get("validation_reason", ""),
            "validation_confidence": group.get("validation_confidence", 0.0),
            "models": group.get("models", []),
            "suggestion_count": len(suggestions),
        }
        # Per-item routing flag: reviewer pre-marked this group "Let the agent
        # decide" in the report. Routed to the per-item judge without prompting.
        if group.get(JUDGE_DECIDE):
            formatted["decision_mode"] = JUDGE_AUTO_DECIDE
        return formatted

    def generate_batch_prompts(self, batches: List[SuggestionBatch]) -> List[Dict[str, Any]]:
        """Attach plan-specific prompts to each batch.

        Returns a list of dicts (batch.to_dict() + prompt) for output assembly.
        """
        result = []
        for batch in batches:
            prompt = format_batch_for_prompt(batch, self.plan_path)
            result.append({**batch.to_dict(), "prompt": prompt})
        return result

    def build_output_json(
        self,
        batches: List[Any],
        *,
        resume_info: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Assemble the final orchestrator_output.json payload."""
        phase_dir = os.path.join(self.out_dir, self.phase_name)
        os.makedirs(phase_dir, exist_ok=True)

        return {
            "format_version": CURRENT_FORMAT_VERSION,
            "plan_file": self.plan_path,
            "prefix": self.prefix,
            "output_dir": self.out_dir,
            "apply_suggestions_dir": phase_dir,
            "timestamp": datetime.now().isoformat(),
            "batches": batches,
            "to_apply": self.formatted_valid,
            "needs_human_review": self.formatted_human,
            "skipped_items": self.formatted_skipped,
            "user_skipped_items": self.user_skipped_items,
            "skipped_count": len(self.skipped),
            "batching_stats": self.batching_stats,
            "human_review_config": self.build_human_review_config(),
            "resume_info": resume_info,
            "edited_descriptions": self.edit_log,
            "summary": {
                "total_groups": len(self.groups),
                "valid_count": len(self.valid),
                "needs_human_count": len(self.needs_human),
                "skipped_count": len(self.skipped),
                "user_skipped_count": len(self.user_skipped_items),
                "batch_count": len(batches),
                "validation_failed_count": sum(
                    1 for g in self.merged if g.get("validation_status") == "validation_failed"
                ),
                "auto_approved_count": sum(
                    1 for g in self.valid if g.get("auto_approved", False)
                ),
                "edited_description_count": len(self.edit_log),
            },
        }

    def get_output_path(self) -> str:
        """Return path for orchestrator_output.json."""
        phase_dir = os.path.join(self.out_dir, self.phase_name)
        return os.path.join(phase_dir, "orchestrator_output.json")

    def print_text_summary(self, batches: List[Any], output_path: str) -> None:
        """Print human-readable summary or JSON output to stdout."""
        output_format = getattr(self.args, "output_format", "text")

        if output_format == "json":
            # Read back and emit to stdout for JSON format
            with open(output_path, "r", encoding="utf-8") as f:
                output = json.load(f)
            print(json.dumps(output, indent=2))
        else:
            # Text format for human reading
            print(f"\n{'=' * 60}")
            print("SUGGESTIONS TO APPLY (BATCHED)")
            print(f"{'=' * 60}")
            print(f"Plan: {self.plan_path}")
            print(f"Valid suggestions: {len(self.valid)}")
            print(f"Batches: {len(batches)}")
            print(f"Needs human review: {len(self.needs_human)}")
            print(f"Skipped: {len(self.skipped)}")

            if self.batching_stats.get("batching_enabled"):
                print("\nBatching efficiency:")
                print(f"  Subagent calls saved: {self.batching_stats.get('subagent_calls_saved', 0)}")
                print(f"  Efficiency gain: {self.batching_stats.get('efficiency_gain_percent', 0)}%")

            for i, batch in enumerate(batches):
                batch_suggestions = batch.get("suggestions", [])
                batch_section = batch.get("section_key", "")
                batch_type = batch.get("batch_type", "")
                batch_size = batch.get("suggestion_count", len(batch_suggestions))
                batch_priority = batch.get("priority_score", 0)

                print(f"\n{'=' * 60}")
                print(f"BATCH {i + 1} ({batch_size} suggestion(s))")
                print(f"{'=' * 60}")
                print(f"Section: {batch_section}")
                print(f"Type: {batch_type}")
                print(f"Priority score: {batch_priority}")

                for j, s in enumerate(batch_suggestions):
                    print(f"\n  --- Suggestion {j + 1} ---")
                    print(f"  Title: {s['title']}")
                    print(f"  Type: {s['type']}")
                    print(f"  Importance: {s['importance']}")
                    print(f"  Section: {s['reference']}")
                    print(f"  Description:\n  {clip(s['description'], 200)}")

            if self.formatted_human:
                print(f"\n{'=' * 60}")
                print("NEEDS HUMAN REVIEW")
                print(f"{'=' * 60}")
                for s in self.formatted_human:
                    print(f"\n- {s['title']}")
                    print(f"  Reason: {s['validation_reason']}")


def main(argv=None) -> int:
    """Main entry point."""
    bootstrap_streams()
    args = ApplySuggestionsOrchestrator.parse_args(argv)
    orchestrator = ApplySuggestionsOrchestrator(args)
    return orchestrator.run()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
