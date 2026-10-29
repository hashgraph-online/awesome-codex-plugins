#!/usr/bin/env python3
"""
Orchestrator for reviewing generated implementation tasks against the original plan.

This orchestrator sends the task decomposition to multiple LLMs for quality review,
with plan coverage analysis as the primary concern. It follows the review-plan
pattern as a thin specialization -- all shared review-orchestration logic
(model invocation, result saving, validation, grouping, HTML reports, state
management) lives in utils/review_orchestrator_base.py.

The phase is optional: `--implement` does NOT require `--review-tasks`.

Supports multiple providers (cursor-agent, gemini, opencode) via the provider
registry. Models can be specified as 'provider:model' or bare 'model' names
(which use the default provider from providers.yaml).

Usage:
    # Use YAML defaults (no prompting if defaults.models is set)
    uv run --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" review-tasks plans/my-plan.md

    # Override defaults with specific models
    uv run --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" review-tasks plans/my-plan.md --models cursor-agent:auto gemini:gemini-2.5-flash

    # Force interactive selection even if defaults exist
    uv run --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" review-tasks plans/my-plan.md --interactive
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.stream_bootstrap import bootstrap_streams
from utils.cli_common import build_parent_parser, dispatcher_prefix
from utils.output_handler import output_dir_path
from utils.prompt_loader import load_prompt
from utils.provider_registry import get_all_model_specs
from utils.review_orchestrator_base import (
    derive_prefix,
    run_review_orchestration,
)
from utils.tasks_file import find_tasks_file
from utils import unattended as unattended_mod
from check_workflow_prerequisites import build_unmet_message


# Phase configuration constants
PHASE_NAME = 'review-tasks'
INVOKE_PHASE = 'task_review'
SALVAGE_PHASE_NAME = 'review_tasks'
ORCHESTRATOR_SCRIPT = 'review_tasks_orchestrator.py'
TASK_REVIEW_PROMPT_FILE = "task_review.txt"


def load_task_review_prompt_template() -> str:
    """Load the task review prompt template.

    Returns:
        Prompt template string with placeholders for substitution
    """
    return load_prompt(TASK_REVIEW_PROMPT_FILE)


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command line arguments for task review."""
    try:
        available_models = get_all_model_specs()
    except FileNotFoundError:
        available_models = ["(providers.yaml not found - run with --models to specify)"]
    except Exception as e:
        available_models = [f"(config error: {type(e).__name__} - check providers.yaml)"]

    # Printed commands, so resolved from `__file__` and never a skill-dir
    # placeholder (see review_plan_orchestrator.parse_args for why).
    run = dispatcher_prefix()
    parser = argparse.ArgumentParser(
        description="Review generated implementation tasks against the original plan",
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
  {run} review-tasks plans/my-plan.md

  # Specify models explicitly
  {run} review-tasks plans/my-plan.md --models cursor-agent:auto gemini:gemini-2.5-flash

  # Force interactive selection
  {run} review-tasks plans/my-plan.md --interactive
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

    parser.add_argument(
        '--internal-validation',
        action='store_true',
        help='Run validation inside orchestrator (legacy mode) instead of delegating to Claude Code subagent'
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

    return parser.parse_args(argv)


async def main(argv: Optional[List[str]] = None) -> int:
    """Main entry point."""
    # Line buffering + UTF-8/replace stream encoding (Windows-safe output);
    # see utils/stream_bootstrap.py for the full rationale.
    bootstrap_streams()

    args = parse_args(argv)

    # Load the prompt template
    prompt_template = load_task_review_prompt_template()

    # Resolve plan path early for find_tasks_file
    plan_path_abs = os.path.abspath(args.plan_file)

    # Pre-run existence check: validate tasks file before any model invocation.
    # This is done here rather than in the pre_run_hook because we need the
    # resolved tasks_path for the prompt context factory.
    # In reaggregate mode, we don't need the tasks file (just reprocessing results).
    tasks_path = None
    # Reaggregation re-materializes the same `validation_tasks.json`, whose
    # prompts now *embed* the task list, so this path needs the tasks file after
    # all — but non-fatally, unlike the fan-out: a reaggregate whose tasks file
    # has since moved still has model results worth aggregating, and it ran with
    # no tasks file at all before the text was embedded.
    reaggregate_tasks_path = None
    if not args.reaggregate:
        try:
            tasks_path = find_tasks_file(plan_path_abs)
            print(f"Tasks file: {tasks_path}")
        except (FileNotFoundError, ValueError) as e:
            # D6 row 13: a plan with no task list is "needs a human", not an
            # unexpected error. `check_workflow_prerequisites` owns the gate; this
            # is the orchestrator's own backstop for a dispatcher command invoked
            # directly (which runs no instruction-level prereq check), so it must
            # land on the same exit code and name the same repair — generate the
            # tasks, then re-run — instead of a bare exit 1.
            print(f"ERROR: {e}", file=sys.stderr)
            return unattended_mod.fail_closed(
                build_unmet_message(
                    "review-tasks",
                    Path(plan_path_abs),
                    output_dir_path(Path(plan_path_abs)),
                    [{"phase": "generate-tasks", "reason": str(e)}],
                ),
                site_id="no-tasks-to-review",
                mode="review-tasks",
            )
    else:
        try:
            reaggregate_tasks_path = find_tasks_file(plan_path_abs)
        except (FileNotFoundError, ValueError) as e:
            print(
                f"Warning: {e}; validation will be prepared against the plan alone.",
                file=sys.stderr,
            )

    effective_prefix = derive_prefix(plan_path_abs)

    def prompt_context_factory(model_spec: str) -> Dict:
        return {
            "plan_path": plan_path_abs,
            "tasks_path": tasks_path or "",
            "prefix": effective_prefix,
        }

    # Pass tasks_file as extra validation metadata: it is the artifact under
    # review, so the base embeds its text in every validation prompt (and hashes
    # it into the task file's `inputs`) rather than only recording the path.
    extra_validation_metadata = {}
    validation_tasks_file = tasks_path or reaggregate_tasks_path
    if validation_tasks_file:
        extra_validation_metadata["tasks_file"] = validation_tasks_file

    await run_review_orchestration(
        args=args,
        phase_name=PHASE_NAME,
        invoke_phase=INVOKE_PHASE,
        salvage_phase_name=SALVAGE_PHASE_NAME,
        prompt_template=prompt_template,
        prompt_context_factory=prompt_context_factory,
        orchestrator_script=ORCHESTRATOR_SCRIPT,
        supports_consolidation=False,
        extra_validation_metadata=extra_validation_metadata or None,
        base_ref=None,
        tasks_path=Path(tasks_path) if tasks_path else None,
        template_style=args.report_style,
    )
    # Any non-zero outcome is raised as SystemExit by the orchestration itself;
    # reaching here means the phase completed.
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main(sys.argv[1:])))
