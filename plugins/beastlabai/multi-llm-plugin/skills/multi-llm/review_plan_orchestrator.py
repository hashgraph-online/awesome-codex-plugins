#!/usr/bin/env python3
"""
Orchestrator for running plan reviews across multiple LLM models.

This script takes an implementation plan file and runs it through multiple
LLM models in parallel to gather review suggestions. Results are saved
per-model and aggregated into a consolidated markdown report.

Supports multiple providers (cursor-agent, gemini, opencode) via the provider
registry. Models can be specified as 'provider:model' or bare 'model' names
(which use the default provider from providers.yaml).

Usage:
    # Use YAML defaults (no prompting if defaults.models is set)
    uv run --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" review-plan plans/my-plan.md

    # Override defaults with specific models
    uv run --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" review-plan plans/my-plan.md --models cursor-agent:auto gemini:gemini-2.5-flash

    # Force interactive selection even if defaults exist
    uv run --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" review-plan plans/my-plan.md --interactive
"""

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.stream_bootstrap import bootstrap_streams
from utils import cli_common
from utils.cli_common import build_parent_parser, dispatcher_prefix, add_scope_policy_argument
from utils.prompt_loader import load_prompt
from utils import scope_round as _scope_round
from utils.state_manager import load_groups_payload
from utils.provider_registry import (
    get_all_model_specs,
)
from utils.consolidation import (
    pre_group_by_section,
    prepare_consolidation_tasks,
    merge_consolidation_results,
    generate_consolidated_json,
    generate_consolidated_report,
    generate_consolidated_html,
    CONSOLIDATION_RECOMMENDED_THRESHOLD,
)
from utils.html_report_generator import (
    sort_consolidated_groups_by_priority,
    derive_aggregate_validation_status,
)
from utils.review_orchestrator_base import (
    run_review_orchestration,
    dispatch_subagent_tasks,
    recorded_served_models,
    recorded_usage,
    derive_prefix,
)
from utils import status_file as _status_file
from utils.output_handler import _compute_file_hash

# Prompt template filename
REVIEW_PROMPT_FILE = "plan_review.txt"


def load_review_prompt_template() -> str:
    """Load the plan review prompt template.

    Returns:
        Prompt template string with placeholders for substitution
    """
    return load_prompt(REVIEW_PROMPT_FILE)


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command line arguments."""
    # Get available models for help text - wrapped in try/except to allow --help
    # even if providers.yaml is missing or malformed
    try:
        available_models = get_all_model_specs()
    except FileNotFoundError:
        available_models = ["(providers.yaml not found - run with --models to specify)"]
    except Exception as e:
        available_models = [f"(config error: {type(e).__name__} - check providers.yaml)"]

    # `--help` goes to stdout, so its examples are *printed* commands and follow
    # the rule the follow-ups do (D1/D1c): fully resolved from `__file__`, never a
    # skill-dir placeholder — no shell but Claude Code's expands one, so on Codex or
    # OpenCode a copied example would die before Python started. Interpolating
    # `dispatcher_prefix()` also keeps the leading token `uv run`, which is what
    # keeps Claude Code's `Bash(uv:*)` glob matching, and names the single entry
    # point rather than this script.
    run = dispatcher_prefix()
    parser = argparse.ArgumentParser(
        description="Run plan reviews across multiple LLM models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        parents=[build_parent_parser()],
        epilog=f"""
Available models (provider:model format):
  {', '.join(available_models[:10])}{'...' if len(available_models) > 10 else ''}

Model selection priority:
  1. --models flag       -> Use specified models
  2. --interactive flag  -> Force two-step interactive selection
  3. --quick flag        -> Use quick_models from providers.yaml (2 models)
  4. YAML defaults       -> Use configured defaults from providers.yaml
  5. Interactive         -> Two-step selection (fallback if no defaults)

Examples:
  # Use YAML defaults (no prompting)
  {run} review-plan plans/my-plan.md

  # Specify models explicitly
  {run} review-plan plans/my-plan.md --models cursor-agent:auto gemini:gemini-2.5-flash

  # Force interactive selection
  {run} review-plan plans/my-plan.md --interactive
        """
    )

    parser.add_argument(
        '--plan-file',
        required=True,
        help='Path to the implementation plan markdown file'
    )

    parser.add_argument(
        '--models',
        nargs='+',
        default=None,
        help='List of models in provider:model format (e.g., cursor-agent:auto gemini:gemini-2.5-flash). '
             'Bare model names use default provider from providers.yaml.'
    )

    parser.add_argument(
        '--quick', '-q',
        action='store_true',
        help='Use quick_models from providers.yaml for lightweight reviews (2 models)'
    )

    parser.add_argument(
        '--out-dir',
        default=None,
        help='Output directory (default: same as input plan file)'
    )

    parser.add_argument(
        '--timeout',
        type=int,
        default=None,
        help='Override timeout per model in seconds (default: use per-provider timeout from providers.yaml)'
    )

    parser.add_argument(
        '--max-parallel',
        type=int,
        default=5,
        help='Maximum number of parallel model invocations (default: 5)'
    )

    parser.add_argument(
        '--skip-validation',
        action='store_true',
        help='Skip the validation step (faster but no false-positive filtering)'
    )

    parser.add_argument(
        '--validation-model',
        type=str,
        default='auto',
        help='Model to use for validation (default: auto)'
    )

    parser.add_argument(
        '--reaggregate',
        action='store_true',
        help='Re-aggregate existing model results (use after salvage operations complete)'
    )

    cli_common.add_retired_flag(parser, '--internal-validation')

    parser.add_argument(
        '--consolidate',
        action='store_true',
        help='Run consolidation to cluster related suggestion groups by plan section'
    )

    parser.add_argument(
        '--reaggregate-consolidation',
        action='store_true',
        help='Re-aggregate consolidation batch results into final consolidated output'
    )

    parser.add_argument(
        '--consolidation-threshold',
        type=int,
        default=None,
        help='Override the minimum valid group count for consolidation recommendation '
             f'(default: {CONSOLIDATION_RECOMMENDED_THRESHOLD})'
    )

    parser.add_argument(
        '--consolidate-dry-run',
        action='store_true',
        help='Show consolidation batching stats without running subagents'
    )

    parser.add_argument(
        '--force',
        action='store_true',
        help='Bypass the completed-phase and partial-completion guards and resume '
             'the phase (already-completed per-model results are kept; only missing '
             'models re-run). For a full re-run that discards existing results, also '
             'pass --rerun-all.'
    )

    parser.add_argument(
        '--rerun-all',
        action='store_true',
        help='Re-run every model from scratch, discarding any existing per-model '
             'result files (default: resume — skip models that already have results).'
    )

    parser.add_argument(
        '--report-style',
        choices=['pr', 'flat'],
        default='pr',
        help='HTML report template style: "pr" for PR-style contextual view, "flat" for classic card layout (default: pr)'
    )

    # plans/scope-policy-and-report-tags.md §4: declared once, in cli_common.
    add_scope_policy_argument(parser, role="review")

    return parser.parse_args(argv)


# ---------------------------------------------------------------------------
# Consolidation handlers (specific to review-plan)
# ---------------------------------------------------------------------------

def consolidate_mode(phase_dir: str, plan_path: str, args=None) -> None:
    """Run consolidation to cluster related suggestion groups.

    ``args`` is optional so a direct call still works; when it carries
    ``--exec-subagents`` the consolidation batch is dispatched and reaggregated in
    this same invocation (D3b) instead of printing a follow-up command for a host
    to drive.
    """
    grouped_path = os.path.join(phase_dir, "grouped.json")
    validation_path = os.path.join(phase_dir, "validation.json")

    if not os.path.exists(grouped_path):
        print(f"ERROR: grouped.json not found at {grouped_path}")
        sys.exit(1)
    if not os.path.exists(validation_path):
        print(f"ERROR: validation.json not found at {validation_path}")
        sys.exit(1)

    with open(grouped_path, 'r', encoding='utf-8') as f:
        groups = load_groups_payload(json.load(f))
    with open(validation_path, 'r', encoding='utf-8') as f:
        validation_data = json.load(f)
    if isinstance(validation_data, dict) and "groups" in validation_data:
        validation = validation_data["groups"]
    else:
        validation = validation_data

    section_groups = pre_group_by_section(groups, validation)

    tasks_metadata = prepare_consolidation_tasks(
        groups, section_groups, phase_dir, plan_path
    )

    total_batches = tasks_metadata["total_batches"]
    tasks_path = os.path.join(phase_dir, "consolidation_tasks.json")

    if total_batches == 0:
        print("No sections need consolidation (all singletons).")
        print("[CONSOLIDATION_SKIPPED] No batches to process.")
        return

    if total_batches == 1:
        print(f"\n[CONSOLIDATION_PENDING] {tasks_path}")
    else:
        print(f"\n[CONSOLIDATION_BATCHES_PENDING] {tasks_path}")
        print(f"Batches: {total_batches}")

    print("\nConsolidation prepared for Claude Code subagent.")
    if any(batch.get("prompt_path") for batch in tasks_metadata.get("batches", [])):
        # Live run 8: the host wrote these files itself, outside the
        # repository, when the batches named none.
        print(
            "Each batch's prompt is also in its own file "
            "(`prompt_path`, consolidation_batch_N.prompt.txt in the phase "
            "directory, the same bytes as its `prompt`)."
        )
    print(f"Sections with 2+ groups: {len([s for s in section_groups.values() if len(s) >= 2])}")
    print(f"Singleton sections: {len(tasks_metadata.get('singleton_sections', {}))}")

    # The stored value is the bare verb, never a command (D2 row 8): compose
    # the runnable string here, from this mode, the document's own plan_file,
    # that verb and the document's replay_flags — a live invocation of this
    # mode winning over the stored list.
    reaggregate_cmd = cli_common.retry_command(
        "review-plan",
        tasks_metadata.get("plan_file") or plan_path,
        tasks_metadata.get("reaggregate_command") or "--reaggregate-consolidation",
        flags=cli_common.current_replay_flags(
            tasks_metadata.get("replay_flags"), mode="review-plan"
        ),
    )

    # D3b: continue past the marker in-process when this run drives its own
    # subagents — consolidation's consumer is reaggregate_consolidation_mode, so
    # the phase closes here rather than owing a host a second turn.
    if args is not None and dispatch_subagent_tasks(
        args,
        task_file=tasks_path,
        phase_dir=phase_dir,
        phase="review-plan",
        document=tasks_metadata,
        plan_path=plan_path,
        label="consolidation",
        retry_command=reaggregate_cmd,
    ):
        prefix = derive_prefix(plan_path)
        reaggregate_consolidation_mode(phase_dir, plan_path, prefix)
        return

    # The plan as the user typed it (fix round 14).
    reaggregate_cmd = cli_common.retry_command(
        "review-plan",
        cli_common.typed_plan_for(tasks_metadata.get("plan_file") or plan_path),
        tasks_metadata.get("reaggregate_command") or "--reaggregate-consolidation",
        flags=cli_common.current_replay_flags(
            tasks_metadata.get("replay_flags"), mode="review-plan"
        ),
    )
    print("\nAfter consolidation completes, run:")
    print(f"  {reaggregate_cmd}")


def consolidate_dry_run_mode(phase_dir: str, plan_path: str) -> None:
    """Show consolidation stats without running subagents."""
    grouped_path = os.path.join(phase_dir, "grouped.json")
    validation_path = os.path.join(phase_dir, "validation.json")

    if not os.path.exists(grouped_path):
        print(f"ERROR: grouped.json not found at {grouped_path}")
        sys.exit(1)
    if not os.path.exists(validation_path):
        print(f"ERROR: validation.json not found at {validation_path}")
        sys.exit(1)

    with open(grouped_path, 'r', encoding='utf-8') as f:
        groups = load_groups_payload(json.load(f))
    with open(validation_path, 'r', encoding='utf-8') as f:
        validation_data = json.load(f)
    if isinstance(validation_data, dict) and "groups" in validation_data:
        validation = validation_data["groups"]
    else:
        validation = validation_data

    section_groups = pre_group_by_section(groups, validation)

    tasks_metadata = prepare_consolidation_tasks(
        groups, section_groups, phase_dir, plan_path
    )

    total_batches = tasks_metadata["total_batches"]
    singleton_count = len(tasks_metadata.get("singleton_sections", {}))
    multi_sections = len([s for s in section_groups.values() if len(s) >= 2])
    total_groups = sum(len(indices) for indices in section_groups.values())

    print("\n=== CONSOLIDATION DRY RUN ===")
    print(f"Total valid groups: {total_groups}")
    print(f"Sections with 2+ groups: {multi_sections}")
    print(f"Singleton sections: {singleton_count}")
    print(f"Batches needed: {total_batches}")

    for batch in tasks_metadata.get("batches", []):
        print(f"  Batch {batch['batch_index']}: {batch['groups_count']} groups in '{batch['section_key']}'")

    print("\n[DRY_RUN_COMPLETE]")


def reaggregate_consolidation_mode(
    phase_dir: str, plan_path: str, prefix: str
) -> None:
    """Merge consolidation batch results and generate output files."""
    tasks_path = os.path.join(phase_dir, "consolidation_tasks.json")
    grouped_path = os.path.join(phase_dir, "grouped.json")

    if not os.path.exists(tasks_path):
        print(f"ERROR: consolidation_tasks.json not found at {tasks_path}")
        sys.exit(1)
    if not os.path.exists(grouped_path):
        print(f"ERROR: grouped.json not found at {grouped_path}")
        sys.exit(1)

    with open(tasks_path, 'r', encoding='utf-8') as f:
        tasks_metadata = json.load(f)
    with open(grouped_path, 'r', encoding='utf-8') as f:
        groups = load_groups_payload(json.load(f))

    consolidated_groups, partial_failures = merge_consolidation_results(
        phase_dir, tasks_metadata, groups
    )

    if partial_failures.get("count", 0) > 0:
        print(f"Warning: {partial_failures['count']} batch(es) had failures "
              f"(indices: {partial_failures['batches']})")

    plan_hash = _compute_file_hash(plan_path)
    grouped_hash = _compute_file_hash(grouped_path)

    total_original = sum(
        len(cg.get("underlying_group_indices", []))
        for cg in consolidated_groups
    )
    merged_count = sum(1 for cg in consolidated_groups if not cg.get("is_singleton", True))
    singleton_count = len(consolidated_groups) - merged_count

    metadata = {
        "schema_version": "1.0",
        "total_original_groups": total_original,
        "total_consolidated": len(consolidated_groups),
        "merged_count": merged_count,
        "singleton_count": singleton_count,
        "consolidation_ratio": round(
            len(consolidated_groups) / max(total_original, 1), 2
        ),
        "timestamp": datetime.now().isoformat(),
        "plan_hash": plan_hash,
        "grouped_hash": grouped_hash,
        "plan_hash_algorithm": "sha256",
        "skipped_report": False,
        "sections_processed": len(tasks_metadata.get("batches", [])) + len(tasks_metadata.get("singleton_sections", {})),
    }

    if partial_failures.get("count", 0) > 0:
        metadata["partial_failures"] = partial_failures

    json_path = generate_consolidated_json(consolidated_groups, metadata, phase_dir)
    print(f"Consolidated JSON: {json_path}")
    # Live run 8 (Claude Code racing 01): the checkpoint kept the
    # recommendation this pass answers, so `status` and its result line went
    # on saying "run --consolidate" after it ran.
    _status_file.remove_status_keys(phase_dir, ["consolidation_recommended"])

    if metadata.get("skipped_report"):
        print("Consolidation complete (report skipped -- minimal reduction).")
        return

    # --- Pre-generation coordination point ---
    # Load validation data for aggregate status derivation
    all_models = set()
    for group in groups:
        for m in group.get("models", []):
            all_models.add(m)

    validation_path = os.path.join(phase_dir, "validation.json")
    validation_for_html = None
    if os.path.exists(validation_path):
        with open(validation_path, 'r', encoding='utf-8') as f:
            validation_raw = json.load(f)
        if isinstance(validation_raw, dict) and "groups" in validation_raw:
            validation_for_html = validation_raw["groups"]
        else:
            validation_for_html = validation_raw
        # The underlying groups carry their validated scope verdicts (by stable
        # hash only) into the consolidated reports; consolidation itself is no
        # new scope authority (plan §3).
        _scope_round.attach_verdicts(groups, validation_for_html)
        scope_meta = (
            validation_raw.get("metadata") if isinstance(validation_raw, dict) else None
        ) or {}
        _scope_round.annotate_decisions(
            groups, scope_meta.get("scope_policy"),
            scope_meta.get("scope_round_baseline_id") or scope_meta.get("scope_baseline_id"),
        )

    # Derive aggregate validation status for each consolidated group
    if validation_for_html:
        validation_by_index = {}
        for entry in validation_for_html:
            g_idx = entry.get("group_index")
            if g_idx is not None:
                validation_by_index[g_idx] = entry.get("status", "")
        for cg in consolidated_groups:
            underlying_indices = cg.get("underlying_group_indices", [])
            statuses = [
                validation_by_index[idx]
                for idx in underlying_indices
                if idx in validation_by_index
            ]
            cg["validation_status"] = derive_aggregate_validation_status(statuses)

    # Sort once, reassign displayIndex, pass to both generators
    consolidated_groups = sort_consolidated_groups_by_priority(consolidated_groups)
    for i, cg in enumerate(consolidated_groups):
        cg["display_index"] = i + 1

    report_path = generate_consolidated_report(
        consolidated_groups, groups, phase_dir, prefix,
        validation=validation_for_html,
    )
    print(f"Consolidated report: {report_path}")

    # What the fan-out spent and which model and sandbox served each slot,
    # read back off the checkpoint the way the full report reads them:
    # consolidation runs in its own invocation, long after the slots exited,
    # and the per-model `{model}.json` files this mode re-reads are bare
    # suggestion lists. `None` for a default run, which leaves the report
    # exactly as it was.
    html_path = generate_consolidated_html(
        consolidated_groups, groups, phase_dir, plan_path, list(all_models),
        validation=validation_for_html,
        usage=recorded_usage(phase_dir),
        served_models=recorded_served_models(phase_dir),
    )
    print(f"Consolidated HTML: {html_path}")

    reduction_pct = round((1 - metadata["consolidation_ratio"]) * 100, 1)
    print("\nConsolidation complete!")
    print(f"  {total_original} groups -> {len(consolidated_groups)} consolidated ({reduction_pct}% reduction)")
    print(f"  Merged: {merged_count}, Singletons: {singleton_count}")


async def main(argv: Optional[List[str]] = None) -> int:
    """Main entry point."""
    # Line buffering + UTF-8/replace stream encoding (Windows-safe output);
    # see utils/stream_bootstrap.py for the full rationale.
    bootstrap_streams()

    args = parse_args(argv)

    # Load the prompt template
    prompt_template = load_review_prompt_template()

    # Build prompt context factory
    plan_path_abs = os.path.abspath(args.plan_file)
    effective_prefix = derive_prefix(plan_path_abs)

    def prompt_context_factory(model_spec: str) -> Dict:
        return {
            "plan_path": plan_path_abs,
            "prefix": effective_prefix,
        }

    # Set up consolidation handlers
    consolidation_handlers = {
        'dry_run': consolidate_dry_run_mode,
        'consolidate': consolidate_mode,
        'reaggregate_consolidation': reaggregate_consolidation_mode,
    }

    await run_review_orchestration(
        args=args,
        phase_name='review-plan',
        invoke_phase='plan_review',
        salvage_phase_name='review_plan',
        prompt_template=prompt_template,
        prompt_context_factory=prompt_context_factory,
        orchestrator_script='review_plan_orchestrator.py',
        supports_consolidation=True,
        consolidation_handlers=consolidation_handlers,
        base_ref=None,
        tasks_path=None,
        template_style=args.report_style,
    )
    # Any non-zero outcome is raised as SystemExit by the orchestration itself;
    # reaching here means the phase completed.
    return 0


if __name__ == "__main__":
    from utils import process_control

    # A process entry of its own: provider children must stay this process's.
    process_control.restore_sigchld_default()
    sys.exit(asyncio.run(main(sys.argv[1:])))
