"""The class the two suggestion apply phases share.

``apply-suggestions`` and ``apply-task-suggestions`` both apply validated
review suggestions to one shared artifact (the plan, or the task list), and
read their review the same way: ``grouped.json`` and ``validation.json``
under the review's directory, and the user's edits, skips and overrides in
its ``report.md``. Each orchestrator keeps what differs through the hooks
below: its parser and help text, its target and backup, the path taken when
the review left no validation, its batch prompt and edit rules.
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from . import importance as _importance
from .apply_orchestrator_base import ApplyOrchestratorBase, OrchestratorError
from .apply_output_helpers import detail_pointer_lines
from .apply_path_helpers import load_json_file
from .apply_selection_helpers import merge_edited_descriptions
from .judge_vocab import JUDGE_AUTO_DECIDE, JUDGE_DECIDE
from .report_parser import (
    find_edited_descriptions,
    parse_skipped_group_suggestions,
    parse_skipped_groups,
    parse_skipped_suggestions,
    parse_suggestion_validation_overrides,
    parse_validation_overrides_groups,
)
from .state_manager import CURRENT_FORMAT_VERSION, load_groups_payload, stamp_stable_ids
from .suggestion_batcher import SuggestionBatch
from .validation import load_validation_results


class SuggestionApplyPhase(
    ApplyOrchestratorBase[Dict[str, Any], SuggestionBatch], abstract=True,
):
    """An apply phase over a review's grouped suggestions."""

    #: The ``orchestrator_output.json`` key naming the phase directory. A
    #: contract with the phase's instruction file, so each phase spells it.
    phase_dir_key: str = ""
    #: The text summary's heading.
    summary_title: str = ""

    # ----------------------------------------------------------------
    # Inputs
    # ----------------------------------------------------------------

    def load_data(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Load grouped suggestions and validation from the review's directory."""
        review_dir = os.path.join(self.out_dir, self.review_subdir)
        validation_path = Path(review_dir) / "validation.json"

        raw = load_json_file(os.path.join(review_dir, "grouped.json"))
        groups: Optional[List[Dict[str, Any]]] = None
        if raw is not None:
            groups = load_groups_payload(raw)
            stamp_stable_ids(groups)

        if not validation_path.exists():
            self._validation_missing(validation_path, groups)

        # The bytes whose round step 9a checked (`held_verdicts`), not a new read.
        validation = load_validation_results(
            validation_path, raw=self.held_verdicts(validation_path))

        if groups is None:
            raise OrchestratorError(
                f"Grouped suggestions not found in {self.out_dir}. "
                f"Run --{self.review_subdir} first to generate grouped suggestions.",
                exit_code=1,
            )

        return groups, validation

    def _validation_missing(
        self, validation_path: Path, groups: Optional[List[Dict[str, Any]]]
    ) -> None:
        """The review left no ``validation.json``: stop. Never returns."""
        raise OrchestratorError(
            f"Validation results not found at {validation_path}. "
            f"Run --{self.review_subdir} first to generate validation results.",
            exit_code=1,
        )

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

    # ----------------------------------------------------------------
    # Items and batches
    # ----------------------------------------------------------------

    def format_item_for_output(self, group: Dict[str, Any], index: int) -> Dict[str, Any]:
        """Format a suggestion group for output to the host."""
        suggestions = group.get("suggestions", [])

        if suggestions:
            primary = suggestions[0]
            title = primary.get("title", group.get("theme", "Unknown"))
            desc = primary.get("desc", "")
            suggestion_type = primary.get("type", "modification")
            reference = primary.get("reference", "")
            importance = _importance.normalize(primary.get("importance"))
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
            **self._reference_fields(reference),
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
        # Under `--scope-policy preserve`: the item's validated scope, and a
        # selected remedy as its instruction. Untouched under `expand`.
        return self.scope_annotate(formatted, group)

    def _reference_fields(self, reference: str) -> Dict[str, Any]:
        """Fields an item carries after ``reference``; none by default."""
        return {}

    def generate_batch_prompts(self, batches: List[SuggestionBatch]) -> List[Dict[str, Any]]:
        """Attach the phase's prompt to each batch.

        Returns a list of dicts (batch.to_dict() + prompt) for output assembly.
        """
        return [
            {**batch.to_dict(), "prompt": self._generate_single_batch_prompt(batch)}
            for batch in batches
        ]

    def _generate_single_batch_prompt(self, batch: SuggestionBatch) -> str:
        """The prompt one batch is dispatched with."""
        raise NotImplementedError(
            f"{type(self).__name__} must implement _generate_single_batch_prompt()"
        )

    # ----------------------------------------------------------------
    # Output
    # ----------------------------------------------------------------

    def build_output_json(
        self,
        batches: List[Any],
        *,
        resume_info: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Assemble the final orchestrator_output.json payload."""
        phase_dir = os.path.join(self.out_dir, self.phase_name)
        os.makedirs(phase_dir, exist_ok=True)
        target_fields = self._target_output_fields(phase_dir)

        return {
            "format_version": CURRENT_FORMAT_VERSION,
            "plan_file": self.plan_path,
            **target_fields,
            "prefix": self.prefix,
            "output_dir": self.out_dir,
            self.phase_dir_key: phase_dir,
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

    def _target_output_fields(self, phase_dir: str) -> Dict[str, Any]:
        """Output fields naming the phase's target, placed after
        ``plan_file``; none by default. Called once the phase directory
        exists and before the rest of the payload is read."""
        return {}

    def print_text_summary(self, batches: List[Any], output_path: str) -> None:
        """Print the human-readable summary (``emit_summary`` owns JSON)."""
        print(f"\n{'=' * 60}")
        print(self.summary_title)
        print(f"{'=' * 60}")
        print(f"Plan: {self.plan_path}")
        for line in self._summary_target_lines():
            print(line)
        print(f"Valid suggestions: {len(self.valid)}")
        print(f"Batches: {len(batches)}")
        print(f"Needs human review: {len(self.needs_human)}")
        print(f"Skipped: {len(self.skipped)}")

        if self.batching_stats.get("batching_enabled"):
            print("\nBatching efficiency:")
            print(f"  Subagent calls saved: {self.batching_stats.get('subagent_calls_saved', 0)}")
            print(f"  Efficiency gain: {self.batching_stats.get('efficiency_gain_percent', 0)}%")

        # The counts only: each batch's items are in the files named here, and
        # `util decisions` shows them to the user (instructions, step 3).
        print()
        for line in detail_pointer_lines(output_path):
            print(line)

    def _summary_target_lines(self) -> List[str]:
        """Summary lines naming the phase's target, after the plan's."""
        return []


__all__ = ["SuggestionApplyPhase"]
