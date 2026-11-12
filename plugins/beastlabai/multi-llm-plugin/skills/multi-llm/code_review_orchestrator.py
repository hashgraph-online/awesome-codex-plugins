#!/usr/bin/env python3
"""
Code review orchestrator for reviewing implementation changes.

This orchestrator reviews code changes made during implementation against
the original plan. It identifies issues, validates changes, and generates
a review report.

Supports multiple providers (cursor-agent, gemini, opencode) via the provider
registry. Models can be specified as 'provider:model' or bare 'model' names
(which use the default provider from providers.yaml).

Usage:
    # Use YAML defaults (no prompting if defaults.models is set)
    uv run --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" review-code plans/my-plan.md

    # Override defaults with specific models
    uv run --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" review-code plans/my-plan.md --models cursor-agent:auto gemini:gemini-2.5-flash

    # Force interactive selection even if defaults exist
    uv run --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" review-code plans/my-plan.md --interactive
"""

import argparse
import asyncio
import contextlib
import dataclasses
import glob as glob_module
import hashlib
import json
import os
import posixpath
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, NamedTuple, Optional, Sequence, Set, Tuple

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.git_utils import (
    get_files_changed_since_ref,
    intent_to_add_untracked,
    subtract_baseline,
)
from utils.output_handler import get_output_paths, sanitize_prefix
from utils.prompt_loader import load_prompt
from utils.schema_validator import drop_non_record_entries, validate_code_review_issues
from utils.state_manager import get_or_create_state
from utils.suggestion_processor import group_similar_suggestions
from utils.stream_bootstrap import bootstrap_streams
from utils import cli_common
from utils import prior_changes
from utils.cli_common import (
    EXIT_NEEDS_HUMAN,
    EXIT_OK,
    build_parent_parser,
    dispatcher_prefix,
    reaggregate_command,  # noqa: F401 - re-export
    record_next,
    add_scope_policy_argument,
)
from utils.report_parser import issue_numbering_footer
from utils import report_markdown
# A commit brief's run (its state records
# `commit_range`) gets the commit template, attribution and report header.
from utils import commit_report
from utils import commit_spelling
from utils.commit_attribution import attribute_review_groups
from utils.atomic_io import atomic_write_text, read_back_text
from utils.state_manager import (
    load_groups_payload,  # noqa: F401 - the module's name for grouped.json's reader
    match_issues_to_suggestions,
    stamp_stable_ids,
    CURRENT_FORMAT_VERSION,
)
from utils.output_handler import (
    get_phase_dir, output_dir_path, phase_dir_path, workflow_file_entries,
)
from utils.detach import PhaseRun, record_output_files
from utils.run_record import report_progress
from utils.progress_tracker import FanoutProgress, PhaseProgress
from utils import importance as _importance
from utils import review_lane as _review_lane
from utils import review_round as _review_round
from utils import scope_policy as _sp
from utils import scope_round as _scope_round
from utils.review_orchestrator_base import (
    RETIRE_REJECTED,
    RETIRE_SUPERSEDED,
    raised_slot_record,
    run_models_concurrent,
    round_results_exist,
    retire_scope_round_results,
    resolve_scope_round,
    validation_scope_block,
    backfill_deadline_losses,
    dispatch_salvage_tasks,
    dispatch_with_ladder,
    slot_ladder,
    dispatch_subagent_tasks,
    dispatch_in_round,
    phase_thread,
    exec_subagents_requested,
    grouped_coverage_gap,
    maybe_detach,
    merge_validation_batches,
    record_high_priority_groups,
    record_validation_counts,
    reopen_phase_for_validation,
    report_already_completed,
    report_misnamed_result,
    validation_counts,
    VALIDATION_COUNT_KEYS,
    record_models_present,
    record_models_salvaged,
    record_review_artifacts,
    resolve_result_files_by_model,
    retire_salvage_artifacts,
    retire_stale_validation,
    retire_stale_validation_round,
    retire_validation_for_regroup,
    retire_unselected_results,
    salvage_failure_fields,
    salvage_failure_kind,
    salvage_source,
    bind_plan_for_validation,
    materialization_read_refusal,
    verify_round_context,
    announce_retired_rungs,
    jail_record_fields,
    print_closing_summary,
    record_sandbox_bypassed,
    recorded_served_models,
    recorded_usage,
    # What a reaggregate says about the models that produced nothing.
    announce_remaining_failures,
    exit_when_every_reviewer_failed,
    remaining_failed_models,
    salvage_requested_models,
    sandbox_fallback_kwargs,
    slot_exception_error,
    update_status,
    write_model_result,
    write_status,
)
from utils.slot_guard import Refused, SlotGuard
# The read side is named from the module that owns it rather than through the
# base's re-export. That re-export exists because every existing caller and test
# already spelled `write_status`/`update_status` through the base
# (`utils/review_orchestrator_base.py`, "Status file helpers"); there is no such
# legacy for `read_status`, and `utils/detach.py` reaches for `status_file`
# directly too. Its one use below is the read-back that turns a silently failed
# checkpoint write into a warning.
from utils.status_file import read_status
from utils import result_files as _result_files
from utils.validation_context import RECORD_CUT_REASON, report_header_lines
from utils.validation_sections import batch_code_windows_enabled
from utils.validation import (
    VALIDATION_CONTEXT_LIMIT,
    BoundDocument,
    ValidationContextError,
    bind_document_text,
    decode_document,
    excerpt_context_reported,
    PLAN_CONTEXT_LABEL,
    ContextBlock,
    RoundProvenance,
    ValidationRound,
    materialize_validation_round,
)
from utils.subagent_prompts import (
    CODE_REVIEW_VALIDATION_GUIDANCE,
    code_review_validation_guidance,
)
from utils.subagent_tasks import (
    build_inputs,
    content_hash,
    write_salvage_task_file,
)
from utils.provider_registry import (
    get_all_model_specs,
    get_collapse_paths,
    parse_model_spec,
    get_provider_timeout,
    set_run_anchor,
)
from utils.json_extractor import (
    build_unsanitize_map,
    has_salvageable_json,
    sanitize_model_name,
)
from utils.llm_client import (
    argv_prompt_bytes,
    describe_output_file,
    describe_usage,
    invoke_with_file_output,
    misnamed_result_baseline,
    requested_result_baseline,
    sandbox_record_word,
)
from utils.prompt_channels import (
    INLINE_MANIFEST_LABEL,
    INLINE_PROMPT_CAP_BYTES,
    render_diff_access,
)
from utils.git_utils import (
    attribute_source_args,
    DIFF_COVERAGE_COMPLETE,
    DIFF_COVERAGE_PARTIAL,
    REVIEW_DIFF_DIRNAME,
    REVIEW_GROUP_ORDER,
    REVIEW_GROUP_SOURCE,
    REVIEW_GROUP_TESTS,
    REVIEW_SCOPE_FILENAME,
    WRITTEN_BY_REAGGREGATE,
    capture_file_context,
    capture_file_snapshots,
    capture_file_snapshots_at,
    classify_review_paths,
    count_review_groups,
    get_project_root,
    get_project_root_from_dir,
    git_path,
    is_empty_tree,
    is_empty_tree_id,
    list_worktree_untracked_files,
    load_review_scope,
    order_review_paths,
    paths_changed_since,
    paths_in_commit,
    rename_map,
    validate_git_ref,
    write_review_diff,
    run_git,
)
from utils.html_report_generator import generate_html_report, write_html_report, model_label, served_model_label, VALIDATION_ORDER, UNKNOWN_STATUS_RANK
from utils.html_report_generator import failed_models_line, sidecar_json
from utils.commit_paths import (
    commit_review_artifact,
    commit_reviews_folder_rel,
    document_label,
    read_commit_range,
)
from utils.commit_range import (
    RangeError,
    display_range,
    pinned_endpoints,
    pinned_head_read_rule,
    pinned_record,
    render_drift_line,
    resolve_base_strict,
    resolve_commit_strict,
    resolve_recorded,
)
from utils import scope_report as _scope_report
from utils import status_file
from utils.tasks_file import find_tasks_file
from utils.commit_front_door import hand_worker_the_stage_applier
from utils.commit_spelling import commit_view, spell_mode


def derive_prefix(plan_path: Path) -> str:
    """Derive output prefix from plan file path."""
    return sanitize_prefix(plan_path.name)


# ---------------------------------------------------------------------------
# One story about a phase dir whose checkpoint records no models
# ---------------------------------------------------------------------------
#
# Two moments can discover that `models_requested` is not on disk, and neither
# can repair it. The fan-out discovers it immediately after `write_status`,
# which is best-effort *by contract* — it wraps the temp write and the
# `os.replace` in a bare `except Exception: pass` (`utils/status_file.py`),
# returns `None`, and so cannot report a read-only or full filesystem, a phase
# dir made unwritable between the mkdir and the write, a checkpoint lock it
# could not take, or an `os.replace` across a boundary that refuses it.
# `--reaggregate` discovers it later, arriving at a dir whose checkpoint was
# lost that way, was never written (every dir whose fan-out predates the write),
# or was hand-merged without the field. Same defect from either end, so both
# sites print the same consequence and the same two recoveries instead of two
# paraphrases the operator has to reconcile into one.
#
# Warning, never refusal, at both. In the fan-out this sits below the detach
# boundary, after the models are resolved and immediately before dispatch:
# raising there would trade a checkpoint that could not be written for a fan-out
# that never ran — the expensive half of the run, on the machine where nobody is
# watching the terminal. At reaggregation a pre-checkpoint dir plus
# `--skip-validation` produces a report *today*, so failing closed would break a
# path that currently completes and would need an override flag to hand back.
# Fail-closed belongs at `resolve_models` (`utils/interactive.py`), where
# refusing costs a correct run nothing; it is wrong at both of these.

#: What is actually lost, in the operator's terms rather than the mechanism's.
#: `sanitize_model_name` (`utils/json_extractor.py`) is one
#: `re.sub(r'[^a-zA-Z0-9\-_]', '_', model)`, so it is lossy in one direction
#: only and the checkpoint is the sole record of the other.
_STEM_ATTRIBUTION_CONSEQUENCE = (
    "--reaggregate over this phase dir attributes issues by filename stem "
    "instead of by model spec: sanitize_model_name flattens every separator a "
    "spec carries, so 'cursor-agent_cursor-grok-4_6-xhigh' can never be turned "
    "back into 'cursor-agent:cursor-grok-4.6-xhigh'. The report then names a "
    "stem where a model belongs, and nothing downstream contradicts it."
)

#: Both recoveries, each with its cost named, because the choice is the
#: operator's: one costs money and reviews a diff that has moved on, the other
#: costs nothing but needs the specs from a source that still holds them.
_STEM_ATTRIBUTION_RECOVERIES = (
    "Recover either way: re-run the fan-out with --force, which writes the "
    "checkpoint on the way through, at the cost of a second round of model "
    "spend against whatever the diff is by then; or write .status.json in the "
    "phase dir by hand — build_unsanitize_map reads nothing but the canonical "
    "specs listed under models_requested / models_completed."
)


def warn_stem_attribution(
    headline: str, model_specs: Optional[List[str]] = None
) -> None:
    """Print the stem-attribution warning to stderr. Never raises, never exits.

    *headline* is the only part that differs between the two sites: it says
    which moment found the gap and in what tense. The consequence and the
    recoveries are shared verbatim so the fan-out's warning and the
    reaggregation's warning are recognisably the same story.

    *model_specs* is passed by the fan-out alone, where the specs are still in
    hand. Printing them makes this warning itself the canonical source the
    hand-written-checkpoint recovery needs — otherwise the operator has to
    reconstruct it from console scrollback, and a stem copied out of an old
    report is exactly the thing that cannot be inverted.

    stderr, not stdout: stdout is this phase's machine-readable channel (the
    `[VALIDATION_BATCHES_PENDING]`, `[PARTIAL_RESULTS: ...]` and
    `[REAGGREGATE_AFTER_SALVAGE]` markers a host parses), and a degradation
    nobody chose does not belong in it.
    """
    lines = [
        headline,
        f"  {_STEM_ATTRIBUTION_CONSEQUENCE}",
        f"  {_STEM_ATTRIBUTION_RECOVERIES}",
    ]
    if model_specs:
        lines.append(
            "  This run's canonical specs, for that second recovery: "
            + ", ".join(model_specs)
        )
    print("\n".join(lines), file=sys.stderr)


def leftover_model_results(phase_dir: Any) -> List[str]:
    """The per-model result files in *phase_dir* (``<stem>.json``), sorted.

    What the partial-completion guard refuses a plain re-run over when no
    ``grouped.json`` is beside them, and what ``improve_workflow.read_records``
    reads as a fan-out cut off before grouping, which its review step resumes
    with ``--force`` (Fable review 2026-10-27, finding 1). The names are
    ``result_files.model_result_paths``'s, the rule every phase-dir reader uses.
    """
    return _result_files.model_result_paths(phase_dir)


def save_model_result(
    prefix: str,
    model: str,
    success: bool,
    issues: Optional[List[Dict]],
    error: Optional[str],
    phase_dir: Path
) -> bool:
    """Save per-model code review result to file.

    The issues were parsed and checked by :func:`run_single_review`; entries
    that are not objects are kept here and dropped when the round is
    aggregated (``schema_validator.drop_non_record_entries``). The file is
    written whole or not at all (``review_orchestrator_base.write_model_result``):
    issues the encoder cannot write back out fail the model, and nothing ends
    the round's save loop.
    """
    sanitized_model = sanitize_model_name(model)

    if success and issues is not None:
        return write_model_result(model, issues, phase_dir, noun="issues")
    elif error:
        error_path = phase_dir / f"error_{sanitized_model}.log"
        with open(error_path, 'w', encoding='utf-8') as f:
            f.write(f"Model: {model}\n")
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            f.write(f"Error: {error}\n")
        print(f"[{model}] Error logged to: {error_path}")
        return False
    return False


def code_round_steps() -> "_review_lane.RoundSteps":
    """review-code's :class:`~utils.review_lane.RoundSteps`, from this module's
    names as they are bound when it is called, so a test that patches one here
    reaches the shared stages."""
    return _review_lane.RoundSteps(
        group_similar_suggestions=group_similar_suggestions,
        stamp_stable_ids=stamp_stable_ids,
        grouped_coverage_gap=grouped_coverage_gap,
        verify_round_context=verify_round_context,
        bind_plan_for_validation=bind_plan_for_validation,
        reopen_phase_for_validation=reopen_phase_for_validation,
        retire_stale_validation=retire_stale_validation,
        retire_stale_validation_round=retire_stale_validation_round,
        retire_validation_for_regroup=retire_validation_for_regroup,
        materialize_validation_round=materialize_validation_round,
        dispatch_in_round=dispatch_in_round,
        dispatch_subagent_tasks=dispatch_subagent_tasks,
        merge_validation_batches=merge_validation_batches,
        write_status=write_status,
        update_status=update_status,
        report_progress=report_progress,
        record_next=record_next,
        recorded_usage=recorded_usage,
        recorded_served_models=recorded_served_models,
        build_unsanitize_map=build_unsanitize_map,
        resolve_result_files_by_model=resolve_result_files_by_model,
        record_models_present=record_models_present,
        remaining_failed_models=remaining_failed_models,
        announce_remaining_failures=announce_remaining_failures,
        exit_when_every_reviewer_failed=exit_when_every_reviewer_failed,
        record_validation_counts=record_validation_counts,
        record_output_files=record_output_files,
        record_review_artifacts=record_review_artifacts,
    )


class CodeLane:
    """review-code's :class:`~utils.review_lane.ReviewLane`.

    What it holds is what legitimately differs from the review base's lane: a
    commit review's commands are spelled in its commit mode, a slot's issues
    are saved without a salvage request (``emit_salvage_task`` wrote that in
    the slot), and a salvaged model's repaired issues rejoin the round, which
    review-code aggregates from its slots rather than from the files
    (docs/development/review-results.md, "The shared review lane").
    """

    mode = "review-code"
    phase_name = "code-review"
    orchestrator_script = "code_review_orchestrator.py"
    # Reused verdicts stay bound to the reviewed-code excerpt and a commit
    # review's frozen context plan (`ReviewLane.reuse_checks_inputs`).
    reuse_checks_inputs = True

    def __init__(self, *, plan_path: Path, phase_dir: Path, prefix: str) -> None:
        self.plan_path = plan_path
        self.phase_dir = phase_dir
        self.prefix = prefix

    def retry_command(self, *flags: str) -> str:
        return commit_spelling.spell_retry_command(
            self.mode, self.plan_path, *flags,
            flags=cli_common.current_replay_flags(mode=self.mode),
        )

    def round_follow_up(
        self, document: Mapping[str, Any], *, typed: bool = False,
    ) -> Optional[str]:
        # Fully resolved, in a commit review's commit mode, and still starting
        # with `uv run` (Claude Code's `Bash(uv:*)` allow rule matches it);
        # the typed form names the plan as the user typed it. The live
        # invocation's flags win; without one, the task file's stored
        # `replay_flags`, as `resolved_reaggregate_command` falls back on the
        # other lanes (D2's precedence rule).
        return commit_spelling.spell_retry_command(
            self.mode, self.plan_path, '--reaggregate',
            **({"typed_plan": cli_common.typed_plan_for(self.plan_path)} if typed else {}),
            flags=cli_common.current_replay_flags(
                document.get("replay_flags"), mode=self.mode,
            ),
        )

    def round_steps(self) -> "_review_lane.RoundSteps":
        return code_round_steps()

    def save_slot(self, slot: "_review_lane.SlotResult") -> bool:
        return save_model_result(
            self.prefix, slot.model_spec, slot.success, slot.payload, slot.error,
            self.phase_dir,
        )

    def adopt_salvaged(
        self, model_spec: str, path: Path, *, data: Optional[bytes] = None,
    ) -> Optional["_review_lane.SlotResult"]:
        # The bytes the salvage dispatch persisted (*data*), or the file read
        # once here when it reported none: the issues they hold rejoin the
        # round, which never reads the file again (docs/development/
        # review-results.md, "Consuming checked bytes").
        if data is None:
            if not (path.exists() and path.stat().st_size > 0):
                return None
        elif not data:
            return None
        try:
            repaired_issues = json.loads(
                path.read_text(encoding="utf-8") if data is None
                else read_back_text(data)
            )
        except (OSError, ValueError) as read_error:
            print(
                f"[{model_spec}] salvage output unreadable, leaving failed: "
                f"{read_error}",
                file=sys.stderr,
            )
            return None
        if not isinstance(repaired_issues, list):
            print(
                f"[{model_spec}] salvage output is not a JSON array, "
                f"leaving failed: {path}",
                file=sys.stderr,
            )
            return None
        return _review_lane.SlotResult(
            model_spec, True, payload=repaired_issues, source="salvage",
        )

    def fanout_steps(self) -> "_review_lane.FanoutSteps":
        return _review_lane.FanoutSteps(
            backfill_deadline_losses=backfill_deadline_losses,
            record_sandbox_bypassed=record_sandbox_bypassed,
            announce_retired_rungs=announce_retired_rungs,
            exec_subagents_requested=exec_subagents_requested,
            dispatch_in_round=dispatch_in_round,
            dispatch_salvage_tasks=dispatch_salvage_tasks,
            record_models_salvaged=record_models_salvaged,
            sanitize_model_name=sanitize_model_name,
            print_closing_summary=print_closing_summary,
        )


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command line arguments."""
    # Get available models for help text
    available_models = get_all_model_specs()

    # Printed commands, so resolved from `__file__` and never a skill-dir
    # placeholder (see review_plan_orchestrator.parse_args for why).
    run = dispatcher_prefix()
    parser = argparse.ArgumentParser(
        description="Review implementation changes against a plan",
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
  {run} review-code plans/my-plan.md

  # Specify models explicitly
  {run} review-code plans/my-plan.md --models cursor-agent:auto gemini:gemini-2.5-flash

  # Force interactive selection
  {run} review-code plans/my-plan.md --interactive
        """
    )

    parser.add_argument(
        '--plan-file',
        required=True,
        help='Path to the implementation plan markdown file'
    )

    # A commit front door's `--detach` stage:
    # the detached worker applies it right after its lock
    # (`utils/detach.RunHandle`). Hidden: only a front door writes it, and
    # replay drops it.
    parser.add_argument('--commit-stage', dest='commit_stage', default=None,
                        help=argparse.SUPPRESS)

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
        '--base-ref',
        type=str,
        help='Git ref to compare against (default: from state file)'
    )

    # A two-commit review. A real flag, because
    # the commit front doors synthesise it and every replay (a resume line, a
    # detached child) carries it, as the full SHA the run resolved.
    parser.add_argument(
        '--head-ref',
        type=str,
        default=None,
        metavar='REV',
        help='Review `git diff <base-ref> <head-ref>`, two commits, instead of '
             'the base against the working tree. Both refs resolve strictly '
             '(no HEAD~1 fallback; an empty-tree --base-ref reviews a range '
             'from the root commit), every model reads code at the head '
             'commit, and the pair is recorded as head_ref in state.json, so '
             '--reaggregate and a later apply-code-fixes use it.'
    )

    # Decision 11.1 of the review-scope plan: an exact scope for an implementer
    # that recorded nothing in state.json (anything outside `/multi-llm
    # implement`). Without it the review falls back to the whole `git diff
    # <base-ref>`, which on the run that motivated this was 1 040 files, ~30 of
    # them hand-written source.
    parser.add_argument(
        '--files',
        action='append',
        default=[],
        metavar='PATH',
        help='Review exactly these files (repeatable; repo-relative, or absolute '
             'inside the repository). Wins over the implement phase\'s '
             'tracked_files and the git-diff fallback, and is recorded in '
             'state.json so a later --reaggregate reviews the same scope; a '
             'fan-out without it clears the record.'
    )

    parser.add_argument(
        '--files-from',
        metavar='FILE',
        default=None,
        help='Like --files, one path per line read from FILE ("-" for stdin); '
             'blank lines are ignored. Combines with --files.'
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
        default=3,
        help='Maximum parallel model invocations (default: 3)'
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
        '--apply-fixes',
        action='store_true',
        # F13: host-neutral (printed by `multi_llm.py review-code --help` on
        # every host, not only Claude Code).
        help='Prepare fix tasks for the invoker to delegate to subagents'
    )

    parser.add_argument(
        '--reaggregate',
        action='store_true',
        help='Re-aggregate existing model results (use after salvage operations complete)'
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

    # Opt-in CI gate. A completed review is exit 0 whatever it found (see the
    # summary block in main()); this is for a standalone caller who wants HIGH
    # findings to stop a pipeline. Exit 3 — "needs a human" — never 1, because
    # the review did not error. `full` never passes it: the phase whose whole job
    # is to fix what the review found runs next.
    parser.add_argument(
        '--fail-on-high',
        action='store_true',
        help='Exit 3 ("needs a human") when the review finds HIGH-importance '
             'issues, instead of the default 0. For standalone CI gating; the '
             '[HIGH_PRIORITY_ISSUES] <n> marker is printed either way.'
    )

    # Declared once, in cli_common.
    add_scope_policy_argument(parser, role="review")

    return parser.parse_args(argv)


def load_code_review_prompt() -> str:
    """Load the code review prompt template."""
    return load_prompt("code_review.txt")


#: Where a review's scope came from (:attr:`ReviewScope.source`), in the order
#: :func:`resolve_review_scope` tries them. ``commit_range`` is a review pinned
#: to two commits (``--head-ref``): ``git diff
#: --name-only <base> <head>``, which ``--files`` narrows and never widens.
SCOPE_SOURCE_COMMIT_RANGE = "commit_range"
SCOPE_SOURCE_FILES_FLAG = "files_flag"
SCOPE_SOURCE_TRACKED = "tracked_files"
SCOPE_SOURCE_GIT_DIFF = "git_diff"
SCOPE_SOURCE_NONE = "none"

#: The ``state.json`` key ``--files``/``--files-from`` are recorded under when a
#: fan-out starts, so a later ``--reaggregate`` (which takes no ``--files``)
#: resolves the scope the reviewers were given. A fan-out without the flags
#: removes it, so a stale override never outlives its run.
REVIEW_SCOPE_FILES_KEY = "review_scope_files"

#: ``[SCOPE_LARGE]`` fires when a fallback scope holds MORE than this many
#: source and test files (fixtures and generated files are not counted: they
#: are collapsed, not reviewed file by file). A warning only; nothing is
#: dropped. Decision 11.4 keeps it as a log-only cap.
SCOPE_LARGE_THRESHOLD = 200

#: How many untracked paths ``[SCOPE_FALLBACK]`` names before ``… and <k>
#: more``: a repository with unignored build output must not flood the log.
UNTRACKED_SAMPLE_SIZE = 10


class ReviewScope(NamedTuple):
    """What ``review-code`` reviews, and where that list came from.

    ``source`` is one of :data:`SCOPE_SOURCE_FILES_FLAG` (``--files`` /
    ``--files-from``, or their record in state), :data:`SCOPE_SOURCE_TRACKED`
    (the implement phase's ``tracked_files``), :data:`SCOPE_SOURCE_GIT_DIFF`
    (the ``git diff --name-only <base_ref>`` fallback) or
    :data:`SCOPE_SOURCE_NONE` (no tracked files and no base ref to diff).
    ``task_ids`` maps each path to its tracked entry's ``task_id``; only the
    ``tracked_files`` branch fills it. ``paths`` carries no order a caller may
    rely on — ``utils.git_utils.order_review_paths`` sets the review order.

    On :data:`SCOPE_SOURCE_COMMIT_RANGE` (a review pinned to two commits),
    ``narrowed`` says a ``--files`` list (typed or recorded) was intersected
    with the range's diff, and ``not_in_range`` names the listed paths the
    range did not change, each reported ``no diff: not changed in <range>``.
    Both keep their defaults on every other source.
    """

    paths: List[str]
    source: str
    task_ids: Dict[str, str]
    not_in_range: Tuple[str, ...] = ()
    narrowed: bool = False


def review_git_root(project_root: Optional[str]) -> Optional[str]:
    """The directory every review-scope git call runs in: the repository root.

    The scope is repository-root-relative (``--files`` is made so,
    ``tracked_files`` comes from ``git status --porcelain`` and the fallback
    from ``git diff --name-only``, both root-relative from any directory), but
    ``git diff -- <path>``, ``git check-attr`` and ``git ls-files``/``git add
    -N`` read a path relative to where they run. Run from the caller's cwd, a
    ``review-code`` invoked from a subdirectory diffed paths that do not exist
    there: every diff came back empty, and the manifest recorded ``no net
    change`` under ``complete`` coverage. So diff generation, classification
    and the intent-to-add marking all run here instead.

    ``project_root`` is the plan's repository (``get_project_root(plan)``), the
    root the rest of this orchestrator already resolves against; when the plan
    lies outside any repository it is the root of the cwd's. ``None`` only when
    neither is in a repository, where git has nothing to diff anyway.
    """
    return project_root or get_project_root_from_dir()


# ---------------------------------------------------------------------------
# Two-commit reviews: `--head-ref` and the pinned records
#
# ---------------------------------------------------------------------------
# A review pinned to two commits diffs `<base> <head>`, never the working tree.
# Three things can pin one: a commit brief's `commit_range` (written by a front
# door before this phase runs), the `head_ref` a direct `--head-ref` round
# recorded, and the refs typed on this command line. They are read in that
# order by :func:`resolve_pinned_range`, the one place every endpoint reader of
# this orchestrator goes through: the fan-out's base ref, `--reaggregate`, the
# validation excerpts and the report. Nothing here tests `base` for truth (a
# root range's base is `None`, diffed against the empty tree), and nothing
# falls back to `head_before_implement`, `head_at_start` or `HEAD~1` once a
# record is present: a recorded SHA that no longer names a commit is exit 3
# (`[RANGE_UNRESOLVED]`), before anything is written.

#: Where a :class:`PinnedRange` came from.
PIN_COMMIT_RANGE = "commit_range"   # a commit brief's record (a fronted run)
PIN_HEAD_REF = "head_ref"           # a direct round's record, read back
PIN_TYPED = "typed"                 # this command line's --head-ref (a direct run)

#: The refusal for a typed pair that is not the pair on record.
HEAD_REF_MISMATCH = "[HEAD_REF_MISMATCH]"


class PinnedRange(NamedTuple):
    """A review pinned to two commits, resolved strictly.

    ``base`` and ``head`` are full SHAs; ``base`` is ``None`` on a root range,
    whose ``base_ref`` (the old side every git call takes) is the repository's
    empty-tree id; otherwise ``base_ref == base``. ``source`` is one of
    :data:`PIN_COMMIT_RANGE`, :data:`PIN_HEAD_REF` or :data:`PIN_TYPED`.
    ``drifted`` lists the reviewed files that differ on disk from ``head``
    (``commit_range.drifted`` on a fronted run, this run's own drift check on
    a direct one). ``not_in_range`` and ``narrowed`` are copied from the
    resolved :class:`ReviewScope` so the scope-source line can say them.
    """

    base: Optional[str]
    head: str
    base_ref: str
    source: str
    drifted: Tuple[str, ...] = ()
    not_in_range: Tuple[str, ...] = ()
    narrowed: bool = False

    @property
    def display(self) -> str:
        """``<base7>..<head7>`` (``root..<head7>``): what a user reads."""
        return display_range(self.base, self.head)

    @property
    def fronted(self) -> bool:
        """Whether a commit brief's ``commit_range`` pins this review."""
        return self.source == PIN_COMMIT_RANGE


def _recorded_drift(record: Mapping[str, Any]) -> Tuple[str, ...]:
    return tuple(str(path) for path in (record.get("drifted") or ()) if path)


def _range_recovery(brief: str) -> str:
    return (
        f"Re-run --review-commits <range> on the commits as they are now: it "
        f"resolves to new SHAs, and so to a new brief, because the review in "
        f"{brief} can no longer be resumed, reaggregated or applied."
    )


def _direct_recovery(plan_path: Any) -> str:
    return (
        f"Run a new review on commits that exist: review-code {plan_path} "
        f"--base-ref <rev> --head-ref <rev>."
    )


def _refuse_another_pair(
    recorded: Any,
    typed_base: Optional[str],
    typed_head: Optional[str],
    *,
    cwd: str,
    what: str,
    remedy: str,
) -> None:
    """Exit-3 :class:`RangeError` when a typed ref resolves elsewhere than the
    pair on record (*recorded* is a ``commit_range.Resolved``). A typed ref
    that does not resolve at all is "elsewhere" too: the pair on record is
    named either way, so the user can type it back."""
    mismatched: List[str] = []
    if typed_head is not None:
        try:
            head = resolve_commit_strict(typed_head, cwd=cwd)
        except RangeError:
            head = None
        if head != recorded.head:
            mismatched.append(f"--head-ref {typed_head}")
    if typed_base is not None:
        try:
            base = resolve_base_strict(typed_base, cwd=cwd)
        except RangeError:
            base = None
        if base != recorded.base_ref:
            mismatched.append(f"--base-ref {typed_base}")
    if not mismatched:
        return
    pair = display_range(recorded.base, recorded.head)
    raise RangeError(
        HEAD_REF_MISMATCH,
        f"{HEAD_REF_MISMATCH} {' and '.join(mismatched)} resolve(s) elsewhere than "
        f"the pair {what} recorded: --base-ref {recorded.base_ref} --head-ref "
        f"{recorded.head} ({pair})\n  {remedy}",
    )


def _replays_record(
    record: Mapping[str, Any], typed_base: Optional[str], typed_head: str, cwd: str,
) -> bool:
    """Whether the typed refs are the recorded SHAs as written (a replayed
    resume line or detached child), so a pruned one is reported as the
    record's ``[RANGE_UNRESOLVED]`` rather than as a bad typed ref."""
    if typed_head != record.get("head"):
        return False
    if typed_base is None:
        return True
    recorded_base = record.get("base")
    if recorded_base is None:
        return is_empty_tree_id(typed_base, cwd)
    return typed_base == recorded_base


def resolve_pinned_range(
    state: Optional[Mapping[str, Any]],
    args: Any,
    *,
    cwd: str,
    plan_path: Any,
    reaggregate: bool = False,
) -> Optional[PinnedRange]:
    """The two commits this review is pinned to, or ``None`` for a review of
    the working tree. Raises :class:`RangeError` (exit 3) — print its
    ``message`` and exit with its ``exit_code`` before writing anything.

    In order:

    1. ``commit_range`` (a commit brief): both SHAs re-resolved strictly
       (``[RANGE_UNRESOLVED]`` naming ``--review-commits``); a typed
       ``--base-ref``/``--head-ref`` must resolve to the same pair.
    2. A typed ``--head-ref`` (a direct run). Replaying the recorded
       ``head_ref`` SHAs re-resolves that record (``[RANGE_UNRESOLVED]``
       naming ``review-code <plan> --base-ref … --head-ref …``); otherwise both
       refs resolve through the strict resolvers (``[RANGE_BAD_REF]``), an
       empty-tree ``--base-ref`` included. With no ``--base-ref`` the base is
       the recorded ``head_ref``'s, else the state's ``head_before_implement``
       resolved strictly too, else ``[RANGE_BAD_REF]`` (never
       ``head_at_start``, stamped from the current ``HEAD``). On
       ``--reaggregate`` a recorded ``head_ref`` wins, and a typed ref
       resolving elsewhere is :data:`HEAD_REF_MISMATCH`.
    3. ``--reaggregate`` with a recorded ``head_ref``: that pair, which is the
       review on record.

    A fan-out without ``--head-ref`` on a plan whose state holds only a
    ``head_ref`` is a review of the working tree (``None``): its round deletes
    the record, so the record always describes the review on record.
    """
    doc: Mapping[str, Any] = state if isinstance(state, Mapping) else {}
    typed_head = getattr(args, "head_ref", None) or None
    typed_base = getattr(args, "base_ref", None) or None

    # The one reader (`commit_range`, else `head_ref`): its source decides
    # which record pins the review, and the live record is what is resolved.
    endpoints = pinned_endpoints(doc)
    live = pinned_record(doc)
    if endpoints is not None and endpoints.source == PIN_COMMIT_RANGE and live is not None:
        commit_range = live
        brief = str(commit_range.get("brief") or plan_path)
        resolved = resolve_recorded(
            commit_range, cwd=cwd, label=brief, recovery=_range_recovery(brief),
        )
        _refuse_another_pair(
            resolved, typed_base, typed_head, cwd=cwd,
            what=f"the commit brief {brief}",
            remedy="A commit brief reviews one range: drop the refs, or review "
                   "another range with --review-commits <range>.",
        )
        return PinnedRange(
            resolved.base, resolved.head, resolved.base_ref, PIN_COMMIT_RANGE,
            drifted=endpoints.drifted,
        )

    record = live if endpoints is not None and endpoints.source == PIN_HEAD_REF else None
    remedy = (
        "--reaggregate regroups the review on record: drop the refs or pass the "
        "recorded pair. To review another pair, run a new round: review-code "
        f"{plan_path} --base-ref <rev> --head-ref <rev>."
    )
    if typed_head is None:
        if reaggregate and record is not None:
            resolved = resolve_recorded(
                record, cwd=cwd, label=str(plan_path),
                recovery=_direct_recovery(plan_path),
            )
            _refuse_another_pair(
                resolved, typed_base, None, cwd=cwd,
                what=f"{plan_path}'s head_ref", remedy=remedy,
            )
            return PinnedRange(
                resolved.base, resolved.head, resolved.base_ref, PIN_HEAD_REF,
                drifted=_recorded_drift(record),
            )
        return None

    if record is not None and (
        reaggregate or _replays_record(record, typed_base, typed_head, cwd)
    ):
        resolved = resolve_recorded(
            record, cwd=cwd, label=str(plan_path),
            recovery=_direct_recovery(plan_path),
        )
        _refuse_another_pair(
            resolved, typed_base, typed_head, cwd=cwd,
            what=f"{plan_path}'s head_ref", remedy=remedy,
        )
        return PinnedRange(
            resolved.base, resolved.head, resolved.base_ref,
            PIN_HEAD_REF if reaggregate else PIN_TYPED,
            drifted=_recorded_drift(record) if reaggregate else (),
        )

    head = resolve_commit_strict(typed_head, cwd=cwd)
    if typed_base is not None:
        base_ref = resolve_base_strict(typed_base, cwd=cwd)
    elif record is not None:
        base_ref = resolve_recorded(
            record, cwd=cwd, label=str(plan_path),
            recovery=_direct_recovery(plan_path),
        ).base_ref
    else:
        # Never `head_at_start`: `StateManager` stamps it from the current
        # `HEAD`, so on a plan whose state was created at the reviewed tip the
        # pair would silently be `head..head` or inverted. Only
        # implement's own `head_before_implement` names where a change starts.
        fallback = doc.get("head_before_implement")
        if not fallback:
            raise RangeError(
                "[RANGE_BAD_REF]",
                "[RANGE_BAD_REF] --head-ref needs a base: pass --base-ref <rev> "
                "(the commit the change starts after)",
            )
        base_ref = resolve_base_strict(str(fallback), cwd=cwd)
    base = None if is_empty_tree_id(base_ref, cwd) else base_ref
    return PinnedRange(base, head, base_ref, PIN_TYPED)


def pin_recorded_refs(pinned: PinnedRange) -> bool:
    """Rewrite this invocation's recorded argv so it carries the pinned pair
    as full SHAs (``--base-ref <base> --head-ref <head>``), never as typed.

    The record (``cli_common.invocation()``) is what a detached child, a
    resume line and a next command replay, so after this a moved branch
    cannot change which commits they review. Every
    spelling argparse binds to either flag (``--head-ref=x``, ``--head x``) is
    replaced in place; a missing one is appended. Only a ``review-code``
    record is touched. True when the record changed.
    """
    record = cli_common.invocation()
    if not record or record.get("mode") != "review-code":
        return False
    argv = [str(token) for token in (record.get("argv") or [])]
    wanted = {"--base-ref": pinned.base_ref, "--head-ref": pinned.head}
    out: List[str] = []
    seen: set = set()
    index = 0
    while index < len(argv):
        token = argv[index]
        name, separator, _ = token.partition("=")
        flag = next(
            (
                full for full in wanted
                if name.startswith("--") and cli_common._flag_matches(name, full)
            ),
            None,
        )
        if flag is None:
            out.append(token)
            index += 1
            continue
        out.extend([flag, wanted[flag]])
        seen.add(flag)
        index += 1 if separator else 2
    for flag, value in wanted.items():
        if flag not in seen:
            out.extend([flag, value])
    if out == argv:
        return False
    record["argv"] = out
    return True


def landed_stage(args: Any) -> bool:
    """Whether a commit front door's stage may have landed during this run's
    detach boundary: a worker whose argv names one (the hidden
    ``--commit-stage``). The worker applies it
    right after ``_acquire_lock``, inside ``maybe_detach`` — after this phase's
    pre-flight loaded ``state``, read the brief and resolved the pair."""
    return bool(getattr(args, "commit_stage", None))


def refresh_pinned_after_stage(
    state: Any,
    pinned: Optional[PinnedRange],
    args: Any,
    *,
    cwd: str,
    plan_path: Any,
) -> Optional[PinnedRange]:
    """The pinned pair re-resolved from *state* once it has been reloaded past
    a landed stage: the stage may have brought the brief's ``commit_range``
    (a new brief has none before it) with its own drift list. The scope's
    ``--files`` narrowing is kept, and a direct run keeps its own drift check.
    Raises :class:`RangeError` like :func:`resolve_pinned_range`."""
    refreshed = resolve_pinned_range(
        getattr(state, "state", None), args, cwd=cwd, plan_path=plan_path,
    )
    if refreshed is None or pinned is None:
        return refreshed
    refreshed = refreshed._replace(
        not_in_range=pinned.not_in_range, narrowed=pinned.narrowed,
    )
    if not refreshed.fronted:
        refreshed = refreshed._replace(drifted=pinned.drifted)
    return refreshed


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def round_starts(
    phase_dir: Any, model_specs: Sequence[str], scope_id: Optional[str],
    *, rerun_all: bool,
) -> bool:
    """Whether this fan-out starts a new round rather than resuming one.

    A resume reuses at least one model's result: a ``<stem>.json`` the scope
    ledger ties to this run's scope id, which ``run_all_reviews`` answers from
    disk. ``--rerun-all`` reuses none, and neither does a run whose scope
    moved (another pair, another ``--files``), so each of those starts one.
    """
    if rerun_all:
        return True
    ledger = read_scope_ledger(phase_dir)
    for spec in model_specs:
        stem = sanitize_model_name(spec)
        result = Path(phase_dir) / f"{stem}.json"
        try:
            reusable = result.is_file() and result.stat().st_size > 0
        except OSError:
            reusable = False
        if reusable and (scope_id is None or ledger.get(stem) == scope_id):
            return False
    return True


def record_round_start(state: Any, pinned: Optional[PinnedRange]) -> bool:
    """The pinned records a new round writes, on *state* in memory.

    Through the ``StateManager`` the phase already holds and saves:

    - a commit brief (``commit_range`` present): ``reviewed_header_sha256``
      takes ``header_sha256`` and ``guard`` is deleted, so the next apply
      takes a fresh decision against this round's groups;
    - a direct ``--head-ref`` round: ``head_ref`` becomes ``{base, head,
      drifted, resolved_at}`` (full SHAs; no ``guard``);
    - a round with neither: ``head_ref`` is deleted.

    True when the document changed; the caller saves.
    """
    doc = getattr(state, "state", None)
    if not isinstance(doc, dict):
        return False
    before = json.dumps(
        {key: doc.get(key) for key in ("commit_range", "head_ref")},
        sort_keys=True, default=str,
    )
    commit_range = doc.get("commit_range")
    if isinstance(commit_range, dict):
        commit_range["reviewed_header_sha256"] = commit_range.get("header_sha256")
        commit_range.pop("guard", None)
    elif pinned is not None:
        doc["head_ref"] = {
            "base": pinned.base,
            "head": pinned.head,
            "drifted": list(pinned.drifted),
            "resolved_at": _utc_now(),
        }
    else:
        doc.pop("head_ref", None)
    after = json.dumps(
        {key: doc.get(key) for key in ("commit_range", "head_ref")},
        sort_keys=True, default=str,
    )
    return before != after


def drift_check(
    pinned: PinnedRange, paths: Sequence[str], *, repo_root: Optional[str],
    staged: bool = False,
) -> PinnedRange:
    """The drift list for this review, and the ``[SCOPE_DRIFT]`` line.

    A fronted run's list is the front door's (``commit_range.drifted``):
    neither recomputed nor printed here, since the commit block already said
    it. *staged* (the run carries a front door's hidden ``--commit-stage``,
    :func:`landed_stage`) is a fronted run too, even while the pair reads as
    typed: on a new brief its ``commit_range`` is still only in the stage,
    which lands in the worker's detach boundary, after this pre-flight. The
    front door printed the line already, and the landed record brings the list
    (:func:`refresh_pinned_after_stage`). A direct run checks its own scope
    with the one change test (``git_utils.paths_changed_since``), in the pre-flight, so
    the line reaches the caller's terminal
    before any detach.
    """
    if pinned.fronted or staged:
        return pinned
    drifted = sorted(paths_changed_since(pinned.head, list(paths), cwd=repo_root))
    line = render_drift_line(drifted, len(paths), pinned.head)
    if line:
        print(line)
    return pinned._replace(drifted=tuple(drifted))


def _context_plan(state: Optional[Mapping[str, Any]]) -> Tuple[Optional[str], Optional[str]]:
    """``(plan_snapshot, plan_sha256)`` of a commit brief's frozen context plan."""
    record = (state or {}).get("commit_range") if state else None
    if not isinstance(record, Mapping):
        return None, None
    snapshot = record.get("plan_snapshot") or None
    digest = record.get("plan_sha256") or None
    return (str(snapshot) if snapshot else None), (str(digest) if digest else None)


def context_plan_snapshot_sha256(snapshot: str, repo_root: Optional[str]) -> str:
    """The SHA-256 of the context plan's snapshot as it is now, ``""`` when
    it cannot be read (so a missing snapshot is a changed one)."""
    path = Path(snapshot)
    if not path.is_absolute():
        path = Path(repo_root or os.getcwd()) / path
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return ""


def resolve_review_scope(
    state: Any,
    base_ref: Optional[str],
    *,
    anchor: Optional[str] = None,
    repo_root: Optional[str] = None,
    head_ref: Optional[str] = None,
) -> ReviewScope:
    """The files under review, labelled with the branch that picked them.

    With ``head_ref`` (a review pinned to two commits) the range decides, ahead of
    everything below: ``git diff
    --name-only <base_ref> <head_ref>`` minus the workflow's own paths is the
    universe, and a ``--files`` list (typed, or recorded as
    ``review_scope_files``) is intersected with it, never widening it; a
    listed path the range did not change is named ``no diff: not changed in
    <range>``. The baseline subtraction, the untracked announcement and the
    ``--base-ref HEAD`` hint are all for a working-tree guess, so none runs.

    Otherwise tried in order, first non-empty wins:

    1. ``review_scope_files`` — the exact list a ``--files``/``--files-from``
       fan-out recorded (decision 11.1 of the review-scope plan);
    2. ``tracked_files`` — what the implement phase recorded;
    3. ``git diff --name-only <base_ref>`` minus the ``pre_existing_changes``
       baseline, announced loudly (``[SCOPE_FALLBACK]``, and ``[SCOPE_LARGE]``
       above :data:`SCOPE_LARGE_THRESHOLD` source and test files), because it
       is a guess: it reviews every committed and uncommitted change since the
       ref, and it never sees an untracked file;
    4. nothing, when there is no base ref either.

    One resolution for both entry points. The fan-out always had the fallback;
    the reaggregate path read ``tracked_files`` alone, so a review that had
    printed ``Files to review: 144`` from the diff reported ``**Files
    Changed:** 0`` in every ``report.md`` its reaggregate wrote. The fallback is the
    same live computation either way, so it is
    re-derived — and its lines re-printed, since they explain where the count
    came from — rather than persisted.

    The label is returned by the branch that picked the paths, never derived
    from a second read of ``state`` that could disagree with it. ``anchor`` is
    the run's plan path, for the ``code_review.collapse_paths`` read behind the
    fallback's per-group counts; ``None`` falls back to the process's run
    anchor, which every entry point pins before it gets here. ``repo_root``
    (:func:`review_git_root`) is where that classification's ``git
    check-attr`` runs.
    """
    if head_ref is not None:
        return _commit_range_scope(
            state, base_ref or "", head_ref, anchor=anchor, repo_root=repo_root,
        )

    recorded = state.get(REVIEW_SCOPE_FILES_KEY)
    if isinstance(recorded, list):
        explicit = list(dict.fromkeys(
            item for item in recorded if isinstance(item, str) and item.strip()
        ))
        if explicit:
            print(
                f"Using {len(explicit)} files given with --files "
                f"(state.json {REVIEW_SCOPE_FILES_KEY})"
            )
            return ReviewScope(explicit, SCOPE_SOURCE_FILES_FLAG, {})

    # The plan, its task list and the output folder are never code under
    # review, whichever branch below names them: an older `tracked_files`
    # holds the plan and `tasks.md` an apply phase recorded, and the git-diff
    # fallback sees the plan the planning phases edited.
    workflow = review_workflow_entries(state, anchor, repo_root)

    tracked_files = state.get("tracked_files", [])
    entries = [
        entry for entry in (tracked_files or [])
        if isinstance(entry, dict) and entry.get("path")
    ]
    kept_paths = set(_drop_workflow_paths(
        [entry["path"] for entry in entries], workflow, repo_root=repo_root,
    ))
    entries = [entry for entry in entries if entry["path"] in kept_paths]
    if entries:
        paths = list(dict.fromkeys(entry["path"] for entry in entries))
        print(f"Using {len(paths)} tracked files from implementation phase")
        # First entry wins for a path listed twice. The paths themselves stay
        # a de-duplicated *set*: the review order is `order_review_paths`'s
        # job, and nobody may take one from here.
        task_ids: Dict[str, str] = {}
        for entry in entries:
            path, task_id = entry.get("path"), entry.get("task_id")
            if path and task_id and path not in task_ids:
                task_ids[path] = str(task_id)
        return ReviewScope(paths, SCOPE_SOURCE_TRACKED, task_ids)

    # Fallback to git diff (legacy behavior or no implement phase run)
    if not base_ref:
        print(
            "Warning: No tracked files and no valid base_ref — cannot discover changed files via git diff. "
            "Code review will have no files to review.",
            file=sys.stderr,
        )
        return ReviewScope([], SCOPE_SOURCE_NONE, {})

    print(f"No tracked files in state, falling back to git diff from {base_ref}")
    try:
        changed_files = get_files_changed_since_ref(base_ref)
    except Exception:
        changed_files = []
    changed_files = _drop_workflow_paths(changed_files, workflow, repo_root=repo_root)

    # Filter out pre-existing changes that were present before implementation.
    # Through `subtract_baseline`, so a baseline entry that is an untracked
    # *directory* (`plans/`, one porcelain line) covers the files under it.
    baseline = state.get("pre_existing_changes")
    pre_existing = list(baseline or [])
    filtered_count = 0
    if pre_existing and changed_files:
        original_count = len(changed_files)
        changed_files = subtract_baseline(changed_files, pre_existing)
        filtered_count = original_count - len(changed_files)
        if filtered_count > 0:
            print(f"Filtered out {filtered_count} pre-existing files (not part of implementation)")

    _announce_fallback_scope(
        changed_files,
        base_ref,
        baseline_recorded=baseline is not None,
        baseline_entries=len(pre_existing),
        subtracted=filtered_count,
        anchor=anchor,
        repo_root=repo_root,
        workflow=workflow,
    )
    return ReviewScope(changed_files, SCOPE_SOURCE_GIT_DIFF, {})


def _range_text_of(
    base_ref: str, head_ref: str, repo_root: Optional[str],
) -> Tuple[str, bool]:
    """``<base7>..<head7>`` (``root..<head7>`` for an empty-tree base), and
    whether *base_ref* is the empty tree: callers key on that flag, never on
    the display text."""
    root = is_empty_tree_id(base_ref, repo_root)
    return display_range(None if root else base_ref, head_ref), root


def _commit_range_scope(
    state: Any,
    base_ref: str,
    head_ref: str,
    *,
    anchor: Optional[str],
    repo_root: Optional[str],
) -> ReviewScope:
    """:data:`SCOPE_SOURCE_COMMIT_RANGE`: the range's own diff, narrowed by
    ``--files`` (see :func:`resolve_review_scope`)."""
    workflow = review_workflow_entries(state, anchor, repo_root)
    shown, root = _range_text_of(base_ref, head_ref, repo_root)
    try:
        universe = get_files_changed_since_ref(base_ref, head_ref, cwd=repo_root)
    except Exception as exc:  # noqa: BLE001 - the review goes on with no files
        print(
            f"Warning: git diff --name-only {base_ref} {head_ref} failed ({exc}); "
            f"the review of {shown} has no files to review.",
            file=sys.stderr,
        )
        universe = []
    universe = _drop_workflow_paths(universe, workflow, repo_root=repo_root)

    recorded = state.get(REVIEW_SCOPE_FILES_KEY)
    named = list(dict.fromkeys(
        item for item in (recorded if isinstance(recorded, list) else [])
        if isinstance(item, str) and item.strip()
    ))
    if not named:
        # The empty tree is spelled whole: git knows it only by its full id.
        base = base_ref if root else base_ref[:12]
        print(
            f"Using the {len(universe)} file(s) changed in {shown} "
            f"(`git diff --name-only {base} {head_ref[:12]}`)"
        )
        return ReviewScope(universe, SCOPE_SOURCE_COMMIT_RANGE, {})
    in_range = set(universe)
    paths = [path for path in named if path in in_range]
    outside = tuple(path for path in named if path not in in_range)
    print(
        f"Using {len(paths)} of the {len(named)} file(s) given with --files "
        f"(state.json {REVIEW_SCOPE_FILES_KEY}): the ones {shown} changed "
        f"({len(universe)} file(s) in the range)"
    )
    for path in outside:
        print(f"  - {path}: no diff: not changed in {shown}")
    return ReviewScope(paths, SCOPE_SOURCE_COMMIT_RANGE, {}, outside, True)


def review_workflow_entries(
    state: Any, anchor: Optional[str], repo_root: Optional[str],
) -> List[str]:
    """The workflow's own files for this review, relative to *repo_root*.

    ``output_handler.workflow_file_entries`` for the plan (*anchor*, else the
    state's ``plan_path``), with the folder the state file lives in added
    when the state object has one. Empty when no plan or no repository is
    known: nothing is left out on a guess.
    """
    plan = anchor or (state.get("plan_path") if hasattr(state, "get") else None)
    root = repo_root or get_project_root_from_dir()
    if not root:
        return []
    state_file = getattr(state, "state_file", None)
    folders = (
        [Path(state_file).parent]
        if isinstance(state_file, (str, os.PathLike)) else []
    )
    return workflow_file_entries(plan, root=root, output_dirs=folders)


def _drop_workflow_paths(
    paths: List[str], workflow: List[str], *, repo_root: Optional[str] = None,
) -> List[str]:
    """*paths* without the workflow's own files, saying once what went.

    Besides this run's *workflow* entries, every commit review's brief and
    report folder goes as a class (``commit_paths.commit_review_artifact``), on every
    mode and whatever plan the run
    has: a range holding a commit of another review's files, or a diff across
    one, would otherwise review them. The folder is read for *repo_root*
    (the cwd's repository when None); when the accessor refuses it, nothing
    extra is dropped.
    """
    if not paths:
        return list(paths)
    kept = subtract_baseline(paths, workflow) if workflow else list(paths)
    root = repo_root or get_project_root_from_dir()
    folder = commit_reviews_folder_rel(root) if root else None
    if folder:
        kept = [path for path in kept if not commit_review_artifact(path, folder)]
    kept_set = set(kept)
    dropped = sorted({path for path in paths if path not in kept_set})
    if dropped:
        print(
            f"Left out {len(dropped)} of the workflow's own file(s) (the plan, "
            f"its task list, its output folder and commit reviews are never "
            f"code under review): {', '.join(dropped[:5])}"
            f"{', …' if len(dropped) > 5 else ''}"
        )
    return kept


def _announce_fallback_scope(
    changed_files: List[str],
    base_ref: str,
    *,
    baseline_recorded: bool,
    baseline_entries: int,
    subtracted: int,
    anchor: Optional[str],
    repo_root: Optional[str] = None,
    workflow: List[str] = (),
) -> None:
    """Print ``[SCOPE_FALLBACK]`` (and ``[SCOPE_LARGE]``) for a git-diff scope.

    The fallback used to print one plain line, so a 1 040-file guess — 880 of
    the paths opencode fixtures, 26 the generated codex mirror, ~30 hand-written
    source — read exactly like a scoped review (review-scope, D2.5).
    This says what was guessed and how big the guess is, and names what it left
    out: ``git diff`` never shows an untracked file, so an implementer that did
    not stage its new files has them dropped here (decision 11.2: they stay out
    of the diff and are counted). Nothing is capped silently: the sample of
    untracked paths is a log cap, and ``[SCOPE_LARGE]`` drops nothing.
    """
    groups = classify_review_paths(
        changed_files, get_collapse_paths(anchor=anchor), cwd=repo_root
    )
    counts = count_review_groups(groups)
    per_group = ", ".join(f"{group} {counts[group]}" for group in REVIEW_GROUP_ORDER)
    if baseline_recorded:
        baseline_text = (
            f"baseline: pre_existing_changes recorded ({baseline_entries} "
            f"entries), {subtracted} path(s) subtracted"
        )
    else:
        baseline_text = (
            "baseline: none recorded (no pre_existing_changes), nothing subtracted"
        )
    print(
        f"[SCOPE_FALLBACK] no implement phase recorded the files under review "
        f"(tracked_files is empty); the scope is `git diff --name-only "
        f"{base_ref}`: {len(changed_files)} files ({per_group}); {baseline_text}"
    )

    untracked = list_worktree_untracked_files()
    if untracked and workflow:
        # The plugin's own output folder is not a file the diff "left out":
        # naming its 200 phase artifacts buried the one new source file.
        untracked = subtract_baseline(untracked, list(workflow))
    if untracked is None:
        print(
            "[SCOPE_FALLBACK] untracked in worktree, not reviewed: unknown "
            "(git ls-files failed)"
        )
    else:
        # Worktree-wide, so on an ordinary dirty tree the count alone cannot
        # say whether this change's own new files were dropped. The sample
        # leads with the untracked paths that sit in a directory the diff
        # touched — where an implementer's unstaged new file would be.
        diffed_dirs = {posixpath.dirname(path) for path in changed_files}
        beside = sorted(p for p in untracked if posixpath.dirname(p) in diffed_dirs)
        beside_set = set(beside)
        rest = sorted(p for p in untracked if p not in beside_set)
        print(
            f"[SCOPE_FALLBACK] untracked in worktree, not reviewed: "
            f"{len(untracked)} (a worktree-wide count, not only files beside "
            f"this change; git diff never shows an untracked file, so the "
            f"fallback leaves them out)"
        )
        sample = beside + rest
        for path in sample[:UNTRACKED_SAMPLE_SIZE]:
            note = " (beside a diffed file)" if path in beside_set else ""
            print(f"  - {path}{note}")
        if len(sample) > UNTRACKED_SAMPLE_SIZE:
            print(f"  … and {len(sample) - UNTRACKED_SAMPLE_SIZE} more")

    reviewed = counts[REVIEW_GROUP_SOURCE] + counts[REVIEW_GROUP_TESTS]
    if reviewed > SCOPE_LARGE_THRESHOLD:
        # Two remedies, because the right one depends on where the work is:
        # `git diff HEAD` shows only UNCOMMITTED changes, so an implementer
        # that committed its work (as the run behind this marker did) would
        # get an empty review from `--base-ref HEAD`.
        print(
            f"[SCOPE_LARGE] {reviewed} source and test files in this fallback "
            f"scope (more than {SCOPE_LARGE_THRESHOLD}; fixtures and generated "
            f"files not counted; nothing is dropped). If the implementation is "
            f"uncommitted, re-run with `--base-ref HEAD`. Otherwise (`git diff "
            f"HEAD` sees only uncommitted changes, so committed work would get "
            f"an empty review) record the exact scope with `util "
            f"finalize-tracking --state-file <state.json> --only-touched "
            f"--touched <path> …`, or pass it with `review-code --files <path> "
            f"…`."
        )


def describe_scope_source(
    source: Optional[str],
    base_ref: Optional[str],
    pinned: Optional[PinnedRange] = None,
) -> str:
    """The review prompt's one-line account of where the file list came from.

    Rendered into ``prompt_context["scope_source"]``, which is how the prompt
    tells a reviewer why its list looks the way it does — including why it is
    empty. On a review pinned to two commits (*pinned*) the line names the
    range and says the change ends at the head commit, not the working tree,
    plus any ``--files`` narrowing and the listed paths the range did not
    change (the manifest's ``Scope source`` line carries the same text).
    """
    if source == SCOPE_SOURCE_COMMIT_RANGE:
        if pinned is None:
            return (
                f"`git diff --name-only {base_ref} <head>` (the files the "
                f"commits under review changed)"
            )
        base = pinned.base_ref if pinned.base is None else pinned.base[:12]
        text = (
            f"`git diff --name-only {base} {pinned.head[:12]}`: every file the "
            f"commits `{pinned.display}` changed (the change ends at commit "
            f"`{pinned.head[:7]}`, not at the working tree)"
        )
        if pinned.narrowed:
            text += ", narrowed to the ones given with --files"
        if pinned.not_in_range:
            text += (
                f"; given with --files but not changed in {pinned.display}, so "
                f"not reviewed: " + ", ".join(
                    f"`{path}` (no diff: not changed in {pinned.display})"
                    for path in pinned.not_in_range
                )
            )
        return text
    if source == SCOPE_SOURCE_FILES_FLAG:
        return "given with --files (the exact scope the user named)"
    if source == SCOPE_SOURCE_TRACKED:
        return "recorded by the implement phase (tracked_files)"
    if source == SCOPE_SOURCE_GIT_DIFF:
        return (
            f"`git diff --name-only {base_ref}` (fallback: no implement phase "
            f"recorded the files it changed, so this is every change since "
            f"that ref; untracked files are not in it)"
        )
    if source == SCOPE_SOURCE_NONE:
        return (
            "none: no implement phase recorded any files, and there is no base "
            "ref to diff against"
        )
    return "not stated"


class ScopeFilesError(ValueError):
    """A ``--files``/``--files-from`` value that cannot be a review scope."""


#: Why ``--files-from -`` is refused where the review cannot read the caller's
#: stdin. One constant, because two guards raise it: this phase's own under
#: ``--detach`` (:func:`read_scope_files_flags`), and ``--improve-code``'s for a
#: review it runs (``utils.improve_workflow.files_from_stdin_refused``), which
#: never forwards ``--detach`` to the phase and so is not covered by this one.
FILES_FROM_STDIN_DETACHED = (
    "--files-from - reads stdin, which a --detach worker does not inherit; "
    "write the list to a file and pass its path instead"
)


def _repo_relative_scope_path(raw: str, root: str) -> str:
    """``raw`` as a repo-relative POSIX path, or :class:`ScopeFilesError`.

    A relative path is taken relative to the repository root (not the cwd), so
    the value means the same thing to a ``--detach`` worker as to the shell
    that launched it. An absolute path must lie inside the repository; one that
    reaches it through a symlinked spelling is accepted by its real location.
    Existence is not checked: a file the change deleted is legitimately in
    scope.
    """
    text = raw.strip()
    root_abs = os.path.abspath(root)
    root_real = os.path.realpath(root)
    candidate = text if os.path.isabs(text) else os.path.join(root_abs, text)
    lexical = os.path.normpath(os.path.abspath(candidate))

    def _inside(path: str, base: str) -> Optional[str]:
        try:
            rel = os.path.relpath(path, base)
        except ValueError:  # another drive on Windows
            return None
        if rel == os.curdir or rel == os.pardir or rel.startswith(os.pardir + os.sep):
            return None
        return rel.replace(os.sep, "/")

    for base in (root_abs, root_real):
        rel = _inside(lexical, base)
        if rel is not None:
            return rel
    rel = _inside(os.path.realpath(candidate), root_real)
    if rel is not None:
        return rel
    raise ScopeFilesError(
        f"--files path is outside the repository ({root_real}): {raw}"
    )


def read_scope_files_flags(args: argparse.Namespace, root: str) -> Optional[List[str]]:
    """The exact scope ``--files``/``--files-from`` name, or ``None`` when unused.

    Both flags combine, ``--files`` first, then ``--files-from`` (one path per
    line, ``-`` for stdin, blank lines ignored). Paths are made repo-relative
    and de-duplicated in the order given. Raises :class:`ScopeFilesError` for
    a path outside the repository, an unreadable list file, ``--files-from -``
    under ``--detach`` (the worker does not inherit this stdin), or flags that
    name no path at all — an empty explicit scope would otherwise quietly send
    the review back to the git-diff fallback it was given to avoid.
    """
    given = [item for item in (getattr(args, "files", None) or []) if item is not None]
    files_from = getattr(args, "files_from", None)
    if not given and files_from is None:
        return None
    raw: List[str] = list(given)
    if files_from is not None:
        if files_from == "-":
            if getattr(args, "detach", False):
                raise ScopeFilesError(FILES_FROM_STDIN_DETACHED)
            text = sys.stdin.read()
        else:
            try:
                text = Path(files_from).read_text(encoding="utf-8")
            except OSError as exc:
                raise ScopeFilesError(
                    f"--files-from {files_from}: cannot read it ({exc})"
                ) from exc
        raw.extend(text.splitlines())
    paths = [
        _repo_relative_scope_path(item, root) for item in raw if item.strip()
    ]
    paths = list(dict.fromkeys(paths))
    if not paths:
        raise ScopeFilesError(
            "--files/--files-from named no path; an empty explicit scope would "
            "fall back to the whole git diff, which is what the flags are for "
            "avoiding"
        )
    return paths


def stage_scope_files_record(state: Any, scope_files: Optional[List[str]]) -> bool:
    """Set or clear ``review_scope_files`` on *state* in memory; True when it moved.

    Staged in memory before resolution (so :func:`resolve_review_scope` reads
    this run's value) and saved by the caller only past the detach boundary:
    an invoker that fails pre-flight, or hands the run to a worker, must not
    leave its scope in ``state.json`` for another run's reaggregate to adopt.
    """
    current = state.get(REVIEW_SCOPE_FILES_KEY)
    if scope_files is not None:
        if current == scope_files:
            return False
        state.set(REVIEW_SCOPE_FILES_KEY, list(scope_files))
        return True
    if current is None:
        return False
    # StateManager has no delete; its dict is the documented `.state`.
    state.state.pop(REVIEW_SCOPE_FILES_KEY, None)
    return True


#: What the prompt's file list says when the resolved scope is empty. The
#: prompt's scope-source line (``prompt_context["scope_source"]``) says why.
#: It replaces "(No tracked files - using git diff to discover changes)", which
#: every reviewer of a 1 040-file fallback scope received in place of the list.
NO_CHANGED_FILES_LINE = "(No changed files found.)"


def format_tracked_files_for_prompt(
    paths: List[str],
    task_ids: Optional[Dict[str, str]] = None,
    max_chars: int = 5000,
    full_scope_ref: Optional[str] = None,
) -> str:
    """
    Format the resolved review scope for the code review prompt.

    Args:
        paths: The files under review, already in review order
            (``utils.git_utils.order_review_paths``: source, tests, fixtures,
            generated). The order is kept, so a cut drops the least useful
            paths first.
        task_ids: ``{path: task_id}`` for a scope the implement phase recorded
            (``ReviewScope.task_ids``). A path with an entry gets a
            ``(from task: <id>)`` suffix; any other path — every git-diff or
            ``--files`` path — is listed bare, since it has no task.
        max_chars: Maximum character length before truncation (default 5000)
        full_scope_ref: Where the whole list can be read (the scope manifest).
            When given and the list is cut, the notice is followed by one
            sentence naming it, because a prompt that says "review ONLY these
            files" over a cut list would put every dropped path out of scope.

    Returns:
        Formatted string for inclusion in the prompt
    """
    if not paths:
        return NO_CHANGED_FILES_LINE

    task_ids = task_ids or {}
    lines = []
    for path in paths:
        task_id = task_ids.get(path)
        suffix = f" (from task: {task_id})" if task_id else ""
        lines.append(f"- `{path}`{suffix}")

    full_text = "\n".join(lines)

    if len(full_text) > max_chars:
        # Truncate to fit within threshold
        truncated_lines = []
        current_length = 0
        for line in lines:
            # +1 for the newline separator
            if current_length + len(line) + 1 > max_chars:
                break
            truncated_lines.append(line)
            current_length += len(line) + 1

        omitted = len(lines) - len(truncated_lines)
        notice = f"\n\n[... {omitted} more files not shown — list truncated to stay within context limits ...]"
        if full_scope_ref:
            notice += (
                f"\nEvery path not shown is still in scope; the full list is "
                f"{full_scope_ref}."
            )
        print(f"WARNING: File list truncated — {omitted} of {len(lines)} files omitted to stay within context limits")
        return "\n".join(truncated_lines) + notice

    return full_text


# ---------------------------------------------------------------------------
# What the reviewers and the validators are shown, beyond the plan
# ---------------------------------------------------------------------------

#: The implement phase's own change log, as rendered into the code-review
#: prompts. Far above :data:`utils.prior_changes.MAX_CHARS` (the write-batch
#: budget, which keeps 15 entries and 2 000 chars) because this is a *summary of
#: a whole phase*, not the tail a single write batch needs: at the write budget
#: the phase measured here showed ten of its thirteen entries and dropped the
#: one that mattered. 200 entries and 20 000 chars still leave the plan and the
#: code their own blocks under `VALIDATION_CONTEXT_LIMIT`.
IMPLEMENTATION_RECORD_TAIL = 200
IMPLEMENTATION_RECORD_CHARS = 20000

#: Lines of surrounding file content carried either side of an issue's cited
#: ``line_range`` in the validation prompt's second context block. Wide enough
#: to hold the enclosing function of a typical finding, narrow enough that the
#: whole excerpt scales with the number of findings rather than with file size.
REVIEWED_CODE_CONTEXT_LINES = 30

#: What the second context block is called in a code-review validation prompt.
#: Named for both halves it carries, because ``build_validation_prompt`` renders
#: one heading per block and an unlabelled half reads as part of the other.
REVIEWED_CODE_CONTEXT_LABEL = (
    "The implementation under review — what it recorded about itself, and the "
    "code at the lines these issues cite"
)


def _issue_line_windows(
    groups: List[Any],
    context_lines: int,
) -> Dict[str, List[Tuple[int, int]]]:
    """Merged ``[start, end]`` windows per file, from every issue's own citation.

    One window per issue would repeat the same lines for the several issues a
    group collects about one function, so overlapping (and touching) windows are
    merged: the excerpt is the *union* of what the phase asks about.
    """
    raw: Dict[str, List[Tuple[int, int]]] = {}
    for group in groups:
        group_dict = group.to_dict() if hasattr(group, "to_dict") else group
        for suggestion in (group_dict.get("suggestions") or []):
            path = str(suggestion.get("file") or "").strip()
            line_range = suggestion.get("line_range")
            if not path or not isinstance(line_range, (list, tuple)) or not line_range:
                continue
            try:
                start = int(line_range[0])
                end = int(line_range[1]) if len(line_range) > 1 else start
            except (TypeError, ValueError):
                continue
            if end < start:
                start, end = end, start
            raw.setdefault(path, []).append(
                (max(1, start - context_lines), end + context_lines)
            )

    merged: Dict[str, List[Tuple[int, int]]] = {}
    for path, windows in raw.items():
        out: List[Tuple[int, int]] = []
        for start, end in sorted(windows):
            if out and start <= out[-1][1] + 1:
                out[-1] = (out[-1][0], max(out[-1][1], end))
            else:
                out.append((start, end))
        merged[path] = out
    return merged


def _readable_inside_repo(path: str, root: Path) -> Optional[str]:
    """The on-disk path a cited ``file`` may be read from, or ``None``.

    ``path`` is **model output** — it arrives inside a reviewer's JSON — and
    whatever it names is read, embedded in every validation batch prompt and
    written into ``validation_tasks.json``, which lives under the plan's output
    dir and is commonly committed. A relative path with ``..`` escaped the
    project root and an absolute one was used verbatim, so a reviewer (or a
    prompt injection in a comment a reviewer echoes) citing
    ``../../.config/multi-llm/e2e.env`` had those lines shipped to the
    validation provider.

    A code-review finding is about the code under review, so the boundary is the
    repository: absolute paths are refused outright — ``prompts/code_review.txt``
    asks for ``"file": string, relative path to affected file``, so an absolute
    one is already off-contract — and a relative one is kept only when it
    resolves *inside* ``root``. Both sides are ``resolve()``d, so a symlink
    inside the tree pointing out of it is refused too.
    """
    if os.path.isabs(path):
        return None
    try:
        candidate = (root / path).resolve()
        root_resolved = root.resolve()
    except OSError:
        return None
    if candidate != root_resolved and root_resolved not in candidate.parents:
        return None
    return str(candidate)


def build_reviewed_code_excerpt(
    groups: List[Any],
    *,
    project_root: Optional[str] = None,
    context_lines: int = REVIEWED_CODE_CONTEXT_LINES,
    budget: Optional[int] = None,
    pinned: Optional[PinnedRange] = None,
) -> str:
    """The code these issues are about, as the line windows they cite.

    The validation prompt declares ``context_mode: inline``, so whatever a
    validator is not shown it cannot check. Before this it was shown the plan
    and the issue records and nothing of the code — every "index.html:98 sets
    accel: 32" verdict was right only because the runner happened to be able to
    open the file.

    **Windows, not the diff**, and deliberately: the second context block is
    held to ``VALIDATION_CONTEXT_LIMIT`` (each batch carries the windows its
    own issues cite, :func:`reviewed_code_for_batch`), so what goes in it has
    to fit that budget. A review of a
    file the implementation *created* has a diff the size of the file — the run
    this was measured on reviewed a 1 393-line, 61 KB ``index.html``, twice the
    budget — and truncating that would put the same hole back one block over.
    Windows scale with the number of findings instead, and they carry the real
    line numbers the issue records cite, which a unified diff only implies.

    ``budget`` fits the excerpt into a character count by dropping **whole
    files, named** (a half-shown window reads as a complete one to a validator,
    and a file the prompt never mentions at least cannot be misread). The first
    file is always kept, so a single over-budget file falls through to the
    caller's own trim rather than producing nothing. Confinement to
    ``project_root`` is :func:`_readable_inside_repo`'s job.

    The two halves are :func:`_reviewed_code_sections` (the reads) and
    :func:`_fit_reviewed_code_sections` (the budget), so a caller that needs
    the dropped list — :func:`build_validation_secondary_context` names it on
    stderr — can read the files once and fit them twice.

    ``pinned`` reads every window at the review's head commit instead of disk, so the
    excerpt — and the
    ``reviewed_code_sha256`` hashed from it — is the same on every reaggregate
    whatever the working tree holds by then.
    """
    sections = _reviewed_code_sections(
        groups, project_root=project_root, context_lines=context_lines,
        **({"pinned": pinned} if pinned is not None else {}),
    )
    return _fit_reviewed_code_sections(sections, budget)[0]


def _reviewed_code_sections(
    groups: List[Any],
    *,
    project_root: Optional[str],
    context_lines: int,
    pinned: Optional[PinnedRange] = None,
) -> List[Tuple[str, str]]:
    """``(path, rendered section)`` per cited file, files read once, in path order.

    ``pinned`` reads them at the head commit (:func:`_pinned_code_sections`).
    """
    windows = _issue_line_windows(groups, context_lines)
    if not windows:
        return []
    if pinned is not None:
        root = Path(project_root) if project_root else Path.cwd()
        return _pinned_code_sections(windows, root=root, pinned=pinned)

    # With no git root (a plan outside a repository) the run's own working
    # directory is the only boundary there is, and a code review always runs
    # against the tree it reviews — so it stands in rather than disabling the
    # confinement entirely.
    root = Path(project_root) if project_root else Path.cwd()
    resolved = {path: _readable_inside_repo(path, root) for path in windows}
    snapshots = capture_file_snapshots(
        sorted({on_disk for on_disk in resolved.values() if on_disk})
    )

    sections: List[Tuple[str, str]] = []
    for path in sorted(windows):
        on_disk = resolved[path]
        if on_disk is None:
            sections.append(
                (path, f"### {path}\n\n(outside the repository; not shown)")
            )
            continue
        if on_disk not in snapshots:
            sections.append((path, f"### {path}\n\n(not readable at review time)"))
            continue
        blocks: List[str] = []
        for start, end in windows[path]:
            lines = capture_file_context(
                on_disk, [start, end], context_lines=0, file_snapshots=snapshots
            )
            if not lines:
                continue
            body = "\n".join(
                f"{entry['line_number']}: {entry['content']}" for entry in lines
            )
            blocks.append(f"```\n{body}\n```")
        if blocks:
            sections.append((path, f"### {path}\n\n" + "\n\n".join(blocks)))
    return sections


#: A unified-diff hunk header: ``@@ -<old start>[,<count>] +<new>… @@``.
_HUNK_HEADER = re.compile(r"^@@ -(\d+)(?:,\d+)? \+\d+(?:,\d+)? @@")

#: What :func:`absent_at_head` calls a path the head commit does not hold.
ABSENT_DELETED = "deleted"        # present at base, deleted by the range
ABSENT_RENAMED = "renamed"        # present at base, renamed away by the range
ABSENT_UNLABELLED = "absent"      # present at base; the rename lookup failed
ABSENT_BOTH = "absent-both"       # at neither end: nothing to show


def pinned_git_name(path: str) -> Optional[str]:
    """A cited path in git's form for a read at a commit, or ``None``.

    ``path`` is model output. An absolute path is refused, as on the disk
    branch (the prompt asks for a relative one), and so is any path that
    climbs out of the repository; the rest go through ``git_path``
     and are normalised.
    Lexical only: the working tree is never consulted, so the answer is the
    same however it has moved since ``head``.
    """
    text = str(path or "").strip()
    if not text or "\n" in text or "\0" in text or os.path.isabs(text):
        return None
    name = posixpath.normpath(git_path(text))
    if name in (".", "..") or name.startswith("../") or name.startswith("/"):
        return None
    return name


def absent_at_head(
    names: Sequence[str], pinned: PinnedRange, *, cwd: Optional[str],
) -> Dict[str, Tuple[str, Optional[str]]]:
    """``{name: (kind, new path)}`` for git-form *names* absent at ``head``.

    One ``paths_in_commit`` at the base (a root range has none) and, when any
    name is there, one ``rename_map`` over the whole range, used for the label
    only. ``kind`` is
    :data:`ABSENT_RENAMED` (with its new path), :data:`ABSENT_DELETED`,
    :data:`ABSENT_UNLABELLED` (present at base, the rename lookup failed) or
    :data:`ABSENT_BOTH`.
    """
    if not names:
        return {}
    if pinned.base is None:
        return {name: (ABSENT_BOTH, None) for name in names}
    at_base = paths_in_commit(pinned.base, names, cwd=cwd)
    if at_base is None:
        return {name: (ABSENT_UNLABELLED, None) for name in names}
    renames = (
        rename_map(pinned.base_ref, pinned.head, cwd=cwd)
        if any(name in at_base for name in names) else {}
    )
    kinds: Dict[str, Tuple[str, Optional[str]]] = {}
    for name in names:
        if name not in at_base:
            kinds[name] = (ABSENT_BOTH, None)
        elif renames is None:
            kinds[name] = (ABSENT_UNLABELLED, None)
        elif name in renames:
            kinds[name] = (ABSENT_RENAMED, renames[name])
        else:
            kinds[name] = (ABSENT_DELETED, None)
    return kinds


def absent_label(kind: str, new: Optional[str], pinned: PinnedRange) -> str:
    """The words a path absent at ``head`` is labelled with, in the excerpt's
    header and the report's: ``deleted in <range>``, ``renamed to <new> in
    <range>``, or ``absent at <head7>``."""
    if kind == ABSENT_DELETED:
        return f"deleted in {pinned.display}"
    if kind == ABSENT_RENAMED and new:
        return f"renamed to {new} in {pinned.display}"
    return f"absent at {pinned.head[:7]}"


def _removed_lines(
    pinned: PinnedRange, name: str, *, cwd: Optional[str],
) -> Optional[Dict[int, str]]:
    """``{line number at base: text}`` for the lines ``git diff --no-renames
    <base> <head> -- <name>`` removes; for a path absent at ``head`` that is
    the whole file as ``base`` had it. ``None`` when the diff fails."""
    try:
        stdout, _, rc = run_git(
            *attribute_source_args(pinned.head), "--literal-pathspecs", "diff", "--no-renames", "--no-color",
            pinned.base_ref, pinned.head, "--", name, check=False, cwd=cwd,
        )
    except (OSError, ValueError):
        return None
    if rc != 0:
        return None
    removed: Dict[int, str] = {}
    old_line: Optional[int] = None
    for line in stdout.split("\n"):
        header = _HUNK_HEADER.match(line)
        if header:
            old_line = int(header.group(1))
            continue
        if old_line is None:
            continue  # the file header, before the first hunk
        if line.startswith("-"):
            removed[old_line] = line[1:].rstrip("\r")
            old_line += 1
        elif line.startswith(" "):
            old_line += 1
    return removed


def _pinned_code_sections(
    windows: Dict[str, List[Tuple[int, int]]],
    *,
    root: Path,
    pinned: PinnedRange,
) -> List[Tuple[str, str]]:
    """The cited windows read at the review's head commit, never from disk.

    Every read is immutable — ``head``, or for a path the range removed,
    ``base`` — so the excerpt is byte-identical on every reaggregate however
    the working tree moves. One ``paths_in_commit`` and one ``git cat-file --batch`` over
    the cited paths at ``head``; a path absent there keeps its slot:

    - deleted or renamed away (present at ``base``): the cited windows of the
      removal, numbered as at ``base``, under ``### <path> (deleted in
      <range>; lines as at <base7>)`` (``renamed to <new> in <range>`` for a
      rename, ``absent at <head7>`` when the rename lookup failed);
    - absent at both ends: ``(absent at <base7> and <head7>; no code to
      show)``;
    - a ``git diff`` that fails, or a file ``head`` holds that cannot be shown
      as text: ``(not readable at <head7>)``.
    """
    cwd = str(root)
    head7 = pinned.head[:7]
    base7 = "root" if pinned.base is None else pinned.base[:7]
    names = {path: pinned_git_name(path) for path in windows}
    asked = sorted({name for name in names.values() if name})
    present = paths_in_commit(pinned.head, asked, cwd=cwd) if asked else set()
    snapshots = (
        capture_file_snapshots_at(pinned.head, sorted(present), cwd=cwd)
        if present else {}
    )
    absent = [name for name in asked if present is not None and name not in present]
    kinds = absent_at_head(absent, pinned, cwd=cwd)

    def numbered(lines: List[Tuple[int, str]]) -> str:
        body = "\n".join(f"{number}: {text}" for number, text in lines)
        return f"```\n{body}\n```"

    sections: List[Tuple[str, str]] = []
    for path in sorted(windows):
        name = names[path]
        if name is None:
            sections.append((path, f"### {path}\n\n(outside the repository; not shown)"))
            continue
        if present is None:
            sections.append((path, f"### {path}\n\n(not readable at {head7})"))
            continue
        if name in present:
            lines_at_head = snapshots.get(name)
            if lines_at_head is None:
                sections.append((path, f"### {path}\n\n(not readable at {head7})"))
                continue
            blocks = []
            for start, end in windows[path]:
                cut = [
                    (number, lines_at_head[number - 1])
                    for number in range(max(1, start), min(end, len(lines_at_head)) + 1)
                ]
                if cut:
                    blocks.append(numbered(cut))
            if blocks:
                sections.append((path, f"### {path}\n\n" + "\n\n".join(blocks)))
            continue
        kind, new = kinds.get(name, (ABSENT_UNLABELLED, None))
        if kind == ABSENT_BOTH:
            if pinned.base is None:
                note = (
                    f"(absent at {head7}, and the range starts at the repository's "
                    f"first commit; no code to show)"
                )
            else:
                note = f"(absent at {base7} and {head7}; no code to show)"
            sections.append((path, f"### {path}\n\n{note}"))
            continue
        removed = _removed_lines(pinned, name, cwd=cwd)
        if removed is None:
            sections.append((path, f"### {path}\n\n(not readable at {head7})"))
            continue
        header = f"### {path} ({absent_label(kind, new, pinned)}; lines as at {base7})"
        blocks = []
        for start, end in windows[path]:
            cut = [(number, removed[number]) for number in range(start, end + 1)
                   if number in removed]
            if cut:
                blocks.append(numbered(cut))
        if blocks:
            sections.append((path, header + "\n\n" + "\n\n".join(blocks)))
        else:
            sections.append((path, f"{header}\n\n(no line at the cited lines)"))
    return sections


def _fit_reviewed_code_sections(
    sections: List[Tuple[str, str]],
    budget: Optional[int],
    *,
    unnamed: frozenset[str] = frozenset(),
) -> Tuple[str, List[str]]:
    """``(excerpt, dropped paths)`` — the sections under ``budget``, whole files only.

    ``unnamed`` are paths the in-block note must not repeat when they are
    dropped: a cited path that resolves outside the repository is model output
    with no window to show, and a prompt that names it among "files not shown"
    reads as an invitation to go and read it. They are still returned in the
    dropped list, which only reaches stderr and the run's own records.
    """
    if not sections:
        return "", []
    header = (
        "Lines are numbered as they are in the file. Only the windows these "
        "issues cite are shown; nothing between them is.\n\n"
    )
    kept: List[str] = []
    dropped: List[str] = []
    used = len(header)
    for path, rendered in sections:
        if budget is not None and kept and used + len(rendered) + 2 > budget:
            dropped.append(path)
            continue
        kept.append(rendered)
        used += len(rendered) + 2
    named = [path for path in dropped if path not in unnamed]
    if named:
        kept.append(
            "(Over this block's budget, so the windows for these files are not "
            "shown: " + ", ".join(named) + ".)"
        )
    return header + "\n\n".join(kept), dropped


def build_implementation_record(plan_path: Path) -> str:
    """What the implement phase recorded about its own work.

    A reviewer shown only the plan and the diff reads every *deliberate* logged
    deviation as an unexplained one. Measured on a real run: the implement phase
    recorded ``accel tuned 28->32 for <4s`` in ``prior_changes.jsonl`` — the tune
    that satisfies the plan's own milestone — a reviewer filed "CONFIG accel
    deviates from plan", the validator upheld it, and the next phase would have
    reverted it. The same sources also say which tasks were never implemented, so
    a task the user deferred cannot be reported as missing work.
    """
    output_dir = output_dir_path(plan_path)
    implement_dir = phase_dir_path(plan_path, "implement")

    lines: List[str] = []

    summary_path = implement_dir / "summary.md"
    if summary_path.exists():
        lines.append(f"- Implementation summary: `{summary_path}`")

    # Only when state.json is already there. `StateManager` *creates* one
    # otherwise, and `_create_initial_state` shells out to git for
    # `head_at_start` — a reader summarizing a phase that may never have run
    # must not be the thing that writes the run's state, nor fail where git
    # cannot answer.
    if (output_dir / "state.json").exists():
        state = get_or_create_state(plan_path)
        unfinished = sorted(
            (task_id, status)
            for task_id, status in state.implementation_task_statuses().items()
            if status != "completed"
        )
        # Two lists, not one. "Must not be reported as missing" is a claim about
        # a *decision* — a task somebody chose not to run — and implement seeds
        # every task `pending` at start (9e374b5), so a run that crashed, was
        # aborted, or whose batch failed used to hand the reviewers every task
        # it never finished under exactly the sentence that tells them to ignore
        # the gap. A task that failed is the one whose missing work a code
        # review most needs to report, so it goes on the other line with its
        # recorded reason for context.
        decided = []
        unfinished_gaps = []
        for task_id, status in unfinished:
            reason = state.get_task_status_reason(task_id)
            rendered = f"{task_id} ({status}{f': {reason}' if reason else ''})"
            # A `pending` task whose reason says the implement run stopped
            # before dispatching it (`not run — …`, racing re-run 3,
            # 2026-10-05) was never decided against: its missing work is
            # exactly the gap to report.
            not_run = bool(reason) and str(reason).startswith("not run")
            if status in ("skipped", "deferred") or (
                status == "pending" and reason and not not_run
            ):
                decided.append(rendered)
            else:
                unfinished_gaps.append(rendered)
        if decided:
            lines.append(
                "- Tasks the implement phase was told not to do, and whose work "
                "must not be reported as missing: " + "; ".join(decided)
            )
        if unfinished_gaps:
            lines.append(
                "- Tasks the implement phase did not finish (report gaps in "
                "their work normally): " + "; ".join(unfinished_gaps)
            )
        # A task recorded `completed` because the user ACCEPTED its failure
        # (`--human-task <id>=done` after a failed check): the
        # check still failed, so the reviewers are told what it found rather
        # than reading `completed` as a check that passed.
        accepted = [
            f"{task_id} ({state.get_task_status_reason(task_id)})"
            for task_id, status in sorted(state.implementation_task_statuses().items())
            if status == "completed"
            and str(state.get_task_status_reason(task_id) or "").startswith("accepted —")
        ]
        if accepted:
            lines.append(
                "- Tasks that failed (or whose check reported problems) and "
                "whose failure the user accepted with --human-task <id>=done "
                "(recorded completed, but the check or work did not pass; "
                "report what it found as a gap normally): "
                + "; ".join(accepted)
            )
        # A check task that ran, changed nothing and reported problems
        # (`task_check_findings`, from its reply's structured `check`): it is
        # recorded completed, so without this line a reviewer read it as a
        # check that passed (racing re-run 4, 2026-10-05: T007's two
        # html-validate problems reached no reviewer).
        for entry in state.implementation_check_findings():
            lines.append(
                f"- Check task {entry['id']} ran and reported these problems, "
                f"which nobody has fixed yet (implement continued past them; "
                f"report each one that still holds in the code as an issue): "
                + "; ".join(entry["findings"])
            )
        # A task whose own check (a test it ran on its edits) failed: the
        # edits were kept, recorded `completed`.
        for entry in state.implementation_batch_check_findings():
            lines.append(
                f"- Task {entry['id']}'s own check failed after its edits (the "
                f"edits were kept; report each failure that still holds in the "
                f"code as an issue): " + "; ".join(entry["findings"])
            )

    changes = prior_changes.render(
        str(output_dir),
        phase="implement",
        tail=IMPLEMENTATION_RECORD_TAIL,
        max_chars=IMPLEMENTATION_RECORD_CHARS,
    )
    if changes and changes != prior_changes.DEFAULT_TEXT:
        lines.append(
            "- Changes the implementation recorded as it made them "
            "(`prior_changes.jsonl`):\n" + changes
        )

    if not lines:
        return (
            "(Nothing on record — this plan's implement phase left no summary, "
            "task status or change log. Judge the code against the plan alone.)"
        )
    return (
        "The implement phase recorded the following about its own work. A "
        "deviation from the plan that appears here was a deliberate, logged "
        "decision: say so and weigh it against the plan's intent rather than "
        "reporting it as an unexplained divergence.\n\n" + "\n".join(lines)
    )


def build_validation_secondary_context(
    groups: List[Any],
    plan_path: Path,
    *,
    project_root: Optional[str] = None,
    cut_report: Optional[Dict[str, Any]] = None,
    pinned: Optional[PinnedRange] = None,
    per_batch: Optional[Dict[str, Any]] = None,
) -> Tuple[str, str]:
    """``(secondary_context, reviewed_code)`` for a code-review validation batch.

    The two halves travel in one block because ``build_validation_prompt``
    renders exactly two, and the record is the shorter and the more load-bearing
    of them — so it goes first.

    **One budget each, not one between them.** Putting the record first under
    the shared ``VALIDATION_CONTEXT_LIMIT`` made the *code* the half that gets
    cut, and the code is the block's reason to exist: measured, a 150-entry
    implement record (~20 KB) plus 20 cited files left 11 of the 20 files with
    no window at all, traced only by a `[... truncated ...]` line inside the
    prompt. The record is therefore excerpted on its own
    ``IMPLEMENTATION_RECORD_CHARS`` and the code gets everything that is left,
    which is the same rule ``review-tasks`` applies to its two blocks.

    Only the code half comes back separately, to be hashed into
    ``inputs.reviewed_code_sha256``, and it is the **untrimmed** excerpt: the
    hash answers "did the cited code move on disk", which is what the resume
    check needs and what the reaggregate site recomputes with no budget of its
    own. The record is regenerated on every read, so hashing it would refuse a
    stored task file over a summary line rather than over the code a verdict was
    reached about.

    ``cut_report``, when given, is filled with what was left out —
    ``record_cut`` (the record went over ``IMPLEMENTATION_RECORD_CHARS``),
    ``record_chars`` (the record's uncut length), ``dropped_files`` and ``files_total`` — so the caller can record the block
    as a ``reviewed-code`` context source with ``mode: truncated``.
    Neither half is ever named by path: the record has no file and the windows
    are live working-tree bytes no snapshot binds.

    ``cut_report["open_paths"]`` is the other half of a drop: the dropped files
    a validator can open itself, absolute, for
    :func:`validation_extra_instructions` to name **outside** this block. The
    block's own "not shown" note is appended last, so it is the first text
    ``build_context_source``'s tail cut removes from a nearly full block; the
    instruction travels in ``extra_instructions``, which no context budget cuts.
    Review-code validators are dispatched ``agent-readonly``, which guarantees
    workspace reads, so they can open the files; they were just never told to.
    The dropped paths are model output, so each is resolved with
    :func:`_readable_inside_repo` under the same root rule
    :func:`_reviewed_code_sections` uses (``project_root``, else the cwd) and
    kept only when it resolves to a file inside it — never a raw join onto the
    root: an ``agent-readonly`` prompt naming an escaping path would send the
    validator to it, and codex reads outside its cwd. Computed here, in the one
    function both validation sites call, so both get the same containment and
    the same text.

    ``pinned`` (a review pinned to two commits) reads the windows at the head
    commit, and ``open_paths`` are then the dropped files' repository-relative
    names, for a validator to read at that commit, never on disk.

    ``per_batch``, when given, receives ``for_batch``: a function from one
    batch's indices into ``groups`` to that batch's ``(secondary_context,
    cut_report)``, which carries the record and only the windows the batch's
    own issues cite, fitted to the same budget (:func:`reviewed_code_for_batch`).
    It selects from this one read, so a batch never re-reads a file and its
    own files are dropped only when they alone are over the budget. Not filled
    when ``MULTI_LLM_VALIDATION_CONTEXT=full``; the round-wide over-budget line
    is then printed as before, and otherwise each batch reports its own drops.
    """
    raw_record = build_implementation_record(plan_path)
    record = excerpt_context_reported(
        raw_record,
        "implementation-record",
        IMPLEMENTATION_RECORD_CHARS,
    )
    record_part = f"#### Implementation record\n\n{record}"
    code_heading = "#### Code at the cited lines\n\n"
    code_budget = VALIDATION_CONTEXT_LIMIT - len(record_part) - len(code_heading) - 2

    sections = _reviewed_code_sections(
        groups, project_root=project_root, context_lines=REVIEWED_CODE_CONTEXT_LINES,
        **({"pinned": pinned} if pinned is not None else {}),
    )
    reviewed_code, _ = _fit_reviewed_code_sections(sections, None)
    embedded = reviewed_code
    # The same root `_reviewed_code_sections` confines its reads to.
    root = Path(project_root) if project_root else Path.cwd()
    if pinned is None:
        inside = {path: _readable_inside_repo(path, root) for path, _ in sections}
    else:
        inside = {path: pinned_git_name(path) for path, _ in sections}
    unnamed = frozenset(path for path, on_disk in inside.items() if on_disk is None)
    batch_view = per_batch is not None and batch_code_windows_enabled()
    if len(embedded) > code_budget:
        # Re-cut by whole files rather than letting the caller's shared excerpt
        # slice the last file mid-window. The files were read once, above; only
        # the fit is redone. The stderr line names the files that went, not a
        # char count, because "which cited file has no window" is the question
        # a verdict about an unshown file raises.
        embedded, dropped = _fit_reviewed_code_sections(
            sections, code_budget, unnamed=unnamed,
        )
        if not batch_view:
            print(
                f"[VALIDATION_CONTEXT_TRUNCATED] reviewed-code "
                f"{len(reviewed_code) - code_budget} chars over; windows for "
                f"{len(dropped)} of {len(sections)} cited files not shown: "
                + ", ".join(dropped),
                file=sys.stderr,
            )
    else:
        dropped = []
    record_cut = len(raw_record) > IMPLEMENTATION_RECORD_CHARS
    if cut_report is not None:
        cut_report["record_cut"] = record_cut
        cut_report["record_chars"] = len(raw_record)
        cut_report["dropped_files"] = list(dropped)
        cut_report["files_total"] = len(sections)
        cut_report["open_paths"] = _dropped_open_paths(dropped, inside, pinned)
    if batch_view:
        def for_batch(indices: Sequence[int]) -> Tuple[str, Dict[str, Any]]:
            return reviewed_code_for_batch(
                [groups[i] for i in indices if 0 <= i < len(groups)],
                sections,
                record_part=record_part,
                code_heading=code_heading,
                code_budget=code_budget,
                inside=inside,
                pinned=pinned,
                record_cut=record_cut,
                record_chars=len(raw_record),
                label=", ".join(str(i) for i in indices),
            )

        per_batch["for_batch"] = for_batch

    parts = [record_part]
    if embedded:
        parts.append(f"{code_heading}{embedded}")
    return "\n\n".join(parts), reviewed_code


def _dropped_open_paths(
    dropped: Sequence[str],
    inside: Mapping[str, Optional[str]],
    pinned: Optional[PinnedRange],
) -> List[str]:
    """The dropped files a validator can open itself (``cut_report["open_paths"]``)."""
    open_paths: List[str] = []
    for path in dropped:
        on_disk = inside.get(path)
        if pinned is not None:
            # A name to read at `head`; the disk is never the reviewed code.
            if on_disk and on_disk not in open_paths:
                open_paths.append(on_disk)
            continue
        if on_disk and os.path.isfile(on_disk) and on_disk not in open_paths:
            open_paths.append(on_disk)
    return open_paths


def _windows_cited(rendered: str, windows: Sequence[Tuple[int, int]]) -> str:
    """One file's section narrowed to the windows that overlap ``windows``.

    A section is ``### <path>`` and fenced blocks of ``<n>: <line>`` rows
    (:func:`_reviewed_code_sections`, :func:`_pinned_code_sections`); a block
    is kept when its shown lines overlap one of ``windows``. A section that is
    a note rather than blocks, or whose blocks would all go, is kept whole.
    """
    header, sep, body = rendered.partition("\n\n")
    if not sep:
        return rendered
    blocks = body.split("\n\n")
    kept: List[str] = []
    for block in blocks:
        rows = block.split("\n")
        if len(rows) < 3 or rows[0] != "```" or rows[-1] != "```":
            return rendered
        try:
            first = int(rows[1].split(":", 1)[0])
            last = int(rows[-2].split(":", 1)[0])
        except ValueError:
            return rendered
        if any(first <= end and last >= start for start, end in windows):
            kept.append(block)
    if not kept or len(kept) == len(blocks):
        return rendered
    return header + "\n\n" + "\n\n".join(kept)


def reviewed_code_for_batch(
    batch_groups: List[Any],
    sections: List[Tuple[str, str]],
    *,
    record_part: str,
    code_heading: str,
    code_budget: int,
    inside: Mapping[str, Optional[str]],
    pinned: Optional[PinnedRange],
    record_cut: bool,
    record_chars: int,
    label: str = "",
) -> Tuple[str, Dict[str, Any]]:
    """One batch's reviewed-code block and cut report, selected from the round's read.

    The record, then for each file the batch's own issues cite, the windows
    of the round's section that overlap those issues' windows
    (:func:`_issue_line_windows` over this batch alone), fitted to
    ``code_budget`` by whole files like the round-wide block. A window other
    batches cite is not shown here: no group of this batch is about it. The
    cut report has :func:`build_validation_secondary_context`'s keys, counted
    over this batch's files.
    """
    own = _issue_line_windows(batch_groups, REVIEWED_CODE_CONTEXT_LINES)
    selected = [
        (path, _windows_cited(rendered, own[path]))
        for path, rendered in sections
        if path in own
    ]
    unnamed = frozenset(path for path, _ in selected if inside.get(path) is None)
    embedded, dropped = _fit_reviewed_code_sections(selected, code_budget, unnamed=unnamed)
    if dropped:
        whole, _ = _fit_reviewed_code_sections(selected, None)
        print(
            f"[VALIDATION_CONTEXT_TRUNCATED] reviewed-code (groups {label}) "
            f"{len(whole) - code_budget} chars over; windows for "
            f"{len(dropped)} of {len(selected)} cited files not shown: "
            + ", ".join(dropped),
            file=sys.stderr,
        )
    report = {
        "record_cut": record_cut,
        "record_chars": record_chars,
        "dropped_files": list(dropped),
        "files_total": len(selected),
        "open_paths": _dropped_open_paths(dropped, inside, pinned),
    }
    parts = [record_part]
    if embedded:
        parts.append(f"{code_heading}{embedded}")
    return "\n\n".join(parts), report


def reviewed_code_batch_view(
    per_batch: Optional[Dict[str, Any]], **guidance_kwargs: Any,
) -> Optional[Any]:
    """``ValidationRound.secondary_for_batch`` for review-code.

    ``None`` when :func:`build_validation_secondary_context` filled no
    ``for_batch`` (``MULTI_LLM_VALIDATION_CONTEXT=full``), so every batch
    embeds the round-wide block as before. Otherwise each batch gets its own
    block, its own ``reviewed-code`` source (:func:`reviewed_code_document`)
    and its own extra instructions naming only its own dropped files, both
    validation sites building them here so they materialize the same prompt.
    """
    for_batch = (per_batch or {}).get("for_batch")
    if for_batch is None:
        return None

    def view(indices: List[int]) -> Tuple[str, BoundDocument, str]:
        text, report = for_batch(indices)
        return (
            text,
            reviewed_code_document(text, report),
            validation_extra_instructions(report, **guidance_kwargs),
        )

    return view


def validation_extra_instructions(
    cut_report: Dict[str, Any],
    *,
    pinned: Optional[PinnedRange] = None,
    plan_snapshot: Optional[str] = None,
    plan_sha256: Optional[str] = None,
) -> str:
    """``extra_instructions`` for a code-review validation batch.

    On a review pinned to two commits (*pinned*) the guidance states the
    pinned-head read rule, with the trust sentence, for every file
    (``subagent_prompts.code_review_validation_guidance``), and the dropped
    files are named for a read at the head commit; a commit brief's frozen
    context plan (*plan_snapshot*) is named by its snapshot, never the user's
    file. With neither, the text is exactly what it was.

    :data:`CODE_REVIEW_VALIDATION_GUIDANCE`, then — only when the reviewed-code
    block dropped files a validator can open (``cut_report["open_paths"]``, see
    :func:`build_validation_secondary_context`) — one instruction naming them,
    absolute. ``build_validation_prompt`` renders this field outside both
    context blocks, so ``excerpt_context`` never touches it; it counts against
    the batch's prompt budget, which splits a batch or fails loudly but never
    truncates. Both validation sites build the argument here, so they
    materialize the same prompt.
    """
    open_paths = [p for p in cut_report.get("open_paths") or [] if p]
    if pinned is None and not plan_snapshot:
        guidance = CODE_REVIEW_VALIDATION_GUIDANCE
    else:
        guidance = code_review_validation_guidance(
            read_rule=(
                pinned_head_read_rule(pinned.base, pinned.head)
                if pinned is not None else None
            ),
            head=pinned.head if pinned is not None else None,
            change=pinned.display if pinned is not None else None,
            plan_snapshot=plan_snapshot,
            plan_sha256=plan_sha256,
        )
    if not open_paths:
        return guidance
    if pinned is not None:
        head = pinned.head[:12]
        return (
            f"{guidance}\n\n"
            "These files were dropped from the reviewed-code block only for its "
            f"budget. Read each at commit `{head}` (`git show {head}:<path>`) at "
            "the lines the findings cite before judging them: "
            + ", ".join(f"`{path}`" for path in open_paths)
        )
    return (
        f"{guidance}\n\n"
        "These files were dropped from the reviewed-code block only for its "
        "budget. Open each at the lines the findings cite before judging them: "
        + ", ".join(f"`{path}`" for path in open_paths)
    )


def reviewed_code_document(secondary: str, cut_report: Dict[str, Any]) -> BoundDocument:
    """The ``reviewed-code`` context source for review-code's second block.

    Always inline, never a path. A record cut or any dropped window makes it
    ``mode: truncated``, and its notice names the dropped files and the record
    cut (with the record's uncut length, since the block is measured after it).
    """
    dropped = list(cut_report.get("dropped_files") or [])
    record_cut = bool(cut_report.get("record_cut"))
    if not dropped and not record_cut:
        return bind_document_text(secondary, label="reviewed-code")
    reasons = []
    if dropped:
        reasons.append(
            f"windows for {len(dropped)} of {cut_report.get('files_total')} cited "
            f"files not shown: {', '.join(dropped)}"
        )
    if record_cut:
        # The raw length, not the cut one: the block's own size is measured
        # after the cut, so this clause is the only place the notice and the
        # report can say how much of the record went.
        record_chars = cut_report.get("record_chars")
        of_total = f" of {record_chars}" if isinstance(record_chars, int) else ""
        reasons.append(
            f"{RECORD_CUT_REASON} at {IMPLEMENTATION_RECORD_CHARS}{of_total} chars"
        )
    return bind_document_text(
        secondary,
        label="reviewed-code",
        reason="; ".join(reasons),
        forced_truncated=True,
        dropped_files=dropped or None,
        files_total=cut_report.get("files_total") if dropped else None,
    )


def prepare_fixes_for_subagents(
    validated_groups: List[Dict],
    plan_path: Path,
    out_dir: Path
) -> Optional[Path]:
    """
    Prepare validated issues for Claude Code subagents to fix.

    This outputs a JSON file with fix tasks that Claude will use to spawn
    Task subagents for each fix.

    Args:
        validated_groups: List of validated issue groups
        plan_path: Path to the plan file
        out_dir: Output directory

    Returns:
        Path to the fix tasks JSON file
    """
    # Filter to only valid issues
    valid_issues = [
        g for g in validated_groups
        if g.get("validation_status") == "valid"
    ]

    if not valid_issues:
        print("No valid issues to fix")
        return None

    # Build fix tasks for each valid issue
    fix_tasks = []
    for i, issue in enumerate(valid_issues, 1):
        # Build location hints from issue data with safe access
        location_hints = []
        if issue.get("file"):
            location_hints.append(f"File: {issue['file']}")

        line_range = issue.get("line_range")
        if line_range and isinstance(line_range, (list, tuple)) and len(line_range) >= 2:
            location_hints.append(f"Lines: {line_range[0]}-{line_range[1]}")

        if issue.get("anchor_text"):
            location_hints.append(f"Anchor text: {issue['anchor_text']}")

        # For grouped issues, include suggestions from all models (max 3)
        suggestions = issue.get("suggestions", [])
        if isinstance(suggestions, list):
            for sugg in suggestions[:3]:
                if isinstance(sugg, dict) and sugg.get("reference"):
                    location_hints.append(f"Reference: {sugg['reference']}")

        # Get issue type for subagent routing
        issue_type = issue.get("type", "unknown")

        fix_task = {
            "id": f"FIX-{i:03d}",
            "title": issue.get("title") or issue.get("theme", "Unknown issue"),
            "type": issue_type,
            "importance": _importance.normalize(issue.get("importance")),
            "description": issue.get("desc") or issue.get("description", "No description provided"),
            "location_hints": location_hints,
            "plan_path": str(plan_path.absolute()),
            # D2h: executor_role is the host-neutral routing field every reader
            # branches on; subagent_type rides along as optional Claude-only
            # metadata for hosts whose native Task tool requires the parameter.
            "executor_role": "agent",
            "subagent_type": "general-purpose",
            "status": "pending"
        }
        fix_tasks.append(fix_task)

    # Save fix tasks to JSON
    phase_dir = get_phase_dir(plan_path, 'code-review')
    fix_tasks_path = phase_dir / "fix_tasks.json"
    try:
        with open(fix_tasks_path, "w", encoding="utf-8") as f:
            json.dump({
                "format_version": CURRENT_FORMAT_VERSION,
                "plan_path": str(plan_path.absolute()),
                "total_issues": len(fix_tasks),
                "tasks": fix_tasks
            }, f, indent=2)
        print(f"\nPrepared {len(fix_tasks)} fix tasks for subagents: {fix_tasks_path}")
        return fix_tasks_path
    except (IOError, OSError) as e:
        print(f"ERROR: Failed to write fix tasks file: {e}")
        return None


# ---------------------------------------------------------------------------
# Which scope each result reviewed, and what the prompt says about the diff set
# ---------------------------------------------------------------------------

#: ``{<result stem>: <scope id>}`` — the scope manifest each model's latest
#: attempt was shown. Every run for a plan shares one phase dir and a resume
#: reuses every ``<model>.json`` on disk, so without this a result written
#: against an earlier change would be reported as a review of this one. A
#: dotfile, so the reaggregate's ``*.json`` glob skips it as it skips
#: ``.status.json``.
REVIEW_SCOPE_LEDGER = ".review-scope.json"

#: A result with no ledger entry predates the ledger (or lost its entry), so
#: which change it reviewed cannot be said.
SCOPE_UNKNOWN = "unknown"

#: The scope placeholders when no diff set was written for the slot — a direct
#: call or a fixture; ``main`` always writes one before dispatch.
NO_SCOPE_MANIFEST_TEXT = (
    "(no scope manifest was written for this review, so the list above is the "
    "whole scope)"
)
NO_DIFF_DIR_TEXT = "(no diff files were written for this review)"
NO_DIFF_ACCESS_TEXT = (
    "No scope manifest or diff files were written for this review. Review the "
    "files listed above against the plan with the tools you have."
)

#: The same placeholders for a lane on the inline branch of the diff-access
#: block: it cannot open the phase dir, so the prompt names no path there and
#: points at the labelled blocks instead.
INLINE_PLAN_TEXT = (
    "(reproduced in full as the `plan` block under Diff Access below; you "
    "cannot open it)"
)
INLINE_SCOPE_FILE_TEXT = (
    f"`{INLINE_MANIFEST_LABEL}` (reproduced in full as a block under Diff Access "
    f"below; you cannot open it)"
)
INLINE_DIFF_DIR_TEXT = (
    "`diff/` (each diff file is reproduced as a block under Diff Access below)"
)
INLINE_FULL_SCOPE_REF = f"the `{INLINE_MANIFEST_LABEL}` block under Diff Access below"


def read_scope_ledger(phase_dir: Any) -> Dict[str, str]:
    """``.review-scope.json`` as ``{stem: scope id}``; ``{}`` when absent or unreadable."""
    try:
        data = json.loads(
            (Path(phase_dir) / REVIEW_SCOPE_LEDGER).read_text(encoding="utf-8")
        )
    except (OSError, ValueError):
        return {}
    if not isinstance(data, dict):
        return {}
    return {
        stem: scope_id for stem, scope_id in data.items()
        if isinstance(stem, str) and isinstance(scope_id, str)
    }


def record_scope_attempt(phase_dir: Any, stem: str, scope_id: str) -> None:
    """Record that ``stem``'s attempt starting now was shown scope ``scope_id``.

    At attempt start rather than at save: a result this attempt's salvage
    writes later lands on the same ``<stem>.json`` (a salvage task's
    ``output_name`` is the model's result file), and is covered too. Atomic
    replace, so a torn ledger never reads as "every result is unknown".
    Best-effort, loud: a failed write only costs the next resume a re-run.
    """
    ledger = read_scope_ledger(phase_dir)
    ledger[stem] = scope_id
    target = Path(phase_dir) / REVIEW_SCOPE_LEDGER
    try:
        atomic_write_text(target, json.dumps(ledger, indent=2, sort_keys=True) + "\n")
    except OSError as exc:
        print(
            f"Warning: could not record the scope of {stem}'s attempt in "
            f"{target}: {exc}",
            file=sys.stderr,
        )


def retire_result_from_another_scope(
    phase_dir: Any, stem: str, scope_id: str
) -> Optional[Path]:
    """Rename a ``<stem>.json`` the ledger does not tie to ``scope_id``.

    It becomes ``<stem>.json.stale-<old id|unknown>`` — never deleted, like a
    retired salvage pair — so a re-run that then fails leaves no result from
    another change for the report or the reaggregate to count; the new name no
    longer matches ``*.json``. An existing stale file of that name is not
    overwritten. Returns the new path, or ``None`` when nothing was retired.
    """
    result = Path(phase_dir) / f"{stem}.json"
    if not result.exists():
        return None
    recorded = read_scope_ledger(phase_dir).get(stem)
    if recorded == scope_id:
        return None
    target = result.with_name(f"{result.name}.stale-{recorded or SCOPE_UNKNOWN}")
    if target.exists():
        target = target.with_name(
            f"{target.name}.{datetime.now().strftime('%Y%m%dT%H%M%S%f')}"
        )
    try:
        os.replace(result, target)
    except OSError as exc:
        print(
            f"Warning: could not retire {result} (reviewed scope "
            f"{recorded or SCOPE_UNKNOWN}, this run's is {scope_id}): {exc}",
            file=sys.stderr,
        )
        return None
    print(
        f"Retired {result.name} (reviewed scope {recorded or SCOPE_UNKNOWN}, "
        f"this run's is {scope_id}) as {target.name}"
    )
    return target


class ExistingResult(NamedTuple):
    """What the fan-out does with a model's existing ``<stem>.json``.

    ``verdict`` is ``reuse`` (answered from disk, ``[SKIP]``; ``issues`` holds
    the list), ``absent`` (no non-empty file), ``withheld`` (no checked
    attempt of the model has superseded one that failed its safety checks or
    ended before they passed, so the file may be that answer; ``withheld``
    says which: ``result_files.Withheld``), ``corrupt`` (unreadable, or not
    JSON), ``not_a_list`` (JSON of another shape) or ``scope_changed`` (the
    ledger ties it to ``reviewed_scope``, another scope, or to none). Every
    verdict but ``reuse`` re-runs the model.
    """

    verdict: str
    issues: Optional[List[Any]] = None
    reviewed_scope: Optional[str] = None
    withheld: Optional[Any] = None


def existing_result_reuse(
    phase_dir: Any, stem: str, scope_id: Optional[str]
) -> ExistingResult:
    """Whether the fan-out answers model ``stem`` from its existing result.

    The one reuse test, shared by :func:`run_all_reviews` and ``util
    resume-state`` (``utils/resume_state``): a non-empty ``<stem>.json``
    holding a JSON list and, when ``scope_id`` is given, a scope ledger entry
    recording that id for ``stem`` (D2.2). ``scope_id`` ``None`` reuses every
    list. A model ``result_files.withheld_models`` names is never reused.
    Read-only.
    """
    path = Path(phase_dir) / f"{stem}.json"
    try:
        present = path.exists() and path.stat().st_size > 0
    except OSError:
        present = False
    if not present:
        return ExistingResult("absent")
    withheld = _result_files.withheld_models(phase_dir)
    owner = withheld.owner(stem)
    if owner is not None:
        return ExistingResult("withheld", withheld=withheld[owner])
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError):
        return ExistingResult("corrupt")
    if not isinstance(data, list):
        return ExistingResult("not_a_list")
    if scope_id is not None:
        reviewed = read_scope_ledger(phase_dir).get(stem)
        if reviewed != scope_id:
            return ExistingResult("scope_changed", reviewed_scope=reviewed)
    return ExistingResult("reuse", issues=data)


#: How many omitted paths ``report.md``'s coverage line names before "… and N
#: more"; ``report_data.json`` and ``review-scope.md`` carry every one.
REPORT_OMITTED_SAMPLE = 10


def review_scope_record(
    phase_dir: Any,
    *,
    scope_id: str,
    base_ref: str,
    base_commit: Optional[str],
    written_by: str,
    coverage: str,
    omitted: List[Tuple[str, str]],
    result_notes: Optional[Dict[str, str]] = None,
    results_match: Optional[bool] = None,
) -> Dict[str, Any]:
    """The scope a report describes, as ``generate_review_report`` renders it.

    One shape for both entry points: the fan-out builds it from what
    ``write_review_diff`` returned, the reaggregate from the manifest it read
    back (or regenerated). ``scopeFile``/``diffDir`` are set only when the
    artifact exists, so the report links nothing that is not there.
    ``result_notes`` is ``{model: "reviewed another scope (<id>)" | "scope
    unknown"}`` for each loaded result the ledger does not tie to this set.
    """
    scope_file = Path(phase_dir) / REVIEW_SCOPE_FILENAME
    diff_dir = Path(phase_dir) / REVIEW_DIFF_DIRNAME
    record: Dict[str, Any] = {
        "scopeId": scope_id,
        "baseRef": base_ref,
        "baseCommit": base_commit,
        "writtenBy": written_by,
        "regenerated": written_by == WRITTEN_BY_REAGGREGATE,
        "scopeFile": str(scope_file.absolute()) if scope_file.is_file() else None,
        "diffDir": str(diff_dir.absolute()) if diff_dir.is_dir() else None,
        "coverage": coverage,
        "omitted": [{"path": path, "reason": reason} for path, reason in omitted],
        "results": dict(result_notes or {}),
    }
    if results_match is not None:
        record["resultsMatch"] = bool(results_match)
    return record


def reaggregate_review_scope(
    phase_dir: Path,
    plan_path: Path,
    base_ref: str,
    changed_files: List[str],
    scope_source: Optional[str],
    result_stems: Dict[str, str],
    *,
    repo_root: Optional[str] = None,
    pinned: Optional[PinnedRange] = None,
) -> Dict[str, Any]:
    """The reaggregate's half of D2.2: report the scope that was reviewed.

    It never enters the fan-out block, so it writes the pair only when the pair
    is missing — a phase dir from before the manifest existed, one cleaned by
    hand, an interrupted write — and then from the current tree, marked
    ``Written by: reaggregate (regenerated from the current tree)``. A whole
    pair is read back and left untouched. Each loaded result is then checked
    against the scope ledger; one tied to another set, or to none, is named in
    the report, and its findings stay. ``repo_root`` (:func:`review_git_root`)
    is where a regeneration's git runs, as on the fan-out. A pinned review
    (*pinned*) regenerates the two-commit set (``head_ref``), so the pair is
    the same whatever the tree holds now.
    """
    header = load_review_scope(phase_dir)
    if header is None:
        print(
            f"[REVIEW_SCOPE_REGENERATED] {REVIEW_SCOPE_FILENAME} or "
            f"{REVIEW_DIFF_DIRNAME}/ is missing or incomplete in {phase_dir}; "
            f"regenerating both from the current tree — the change as it is "
            f"now, not a record of what the reviewers read"
        )
        diff_set = write_review_diff(
            base_ref, changed_files, phase_dir,
            get_collapse_paths(anchor=str(plan_path)),
            scope_source=describe_scope_source(
                scope_source, base_ref,
                **({"pinned": pinned} if pinned is not None else {}),
            ),
            written_by=WRITTEN_BY_REAGGREGATE,
            cwd=repo_root,
            **({"head_ref": pinned.head} if pinned is not None else {}),
        )
        scope_id, header_base_ref, base_commit = (
            diff_set.scope_id, diff_set.base_ref, diff_set.base_commit,
        )
        written_by, coverage, omitted = (
            diff_set.written_by, diff_set.coverage, list(diff_set.omitted),
        )
    else:
        print(
            f"Review scope read back from {Path(phase_dir) / REVIEW_SCOPE_FILENAME} "
            f"(scope {header.scope_id}, written by {header.written_by}); nothing "
            f"rewritten"
        )
        scope_id, header_base_ref, base_commit = (
            header.scope_id, header.base_ref, header.base_commit,
        )
        written_by, coverage, omitted = (
            header.written_by, header.coverage, list(header.omitted),
        )

    ledger = read_scope_ledger(phase_dir)
    notes: Dict[str, str] = {}
    for model in sorted(result_stems):
        recorded = ledger.get(result_stems[model])
        if recorded is None:
            notes[model] = "scope unknown"
        elif recorded != scope_id:
            notes[model] = f"reviewed another scope ({recorded})"
    for model, note in notes.items():
        print(
            f"[{model}] {note}: its findings stay in the report, but it did not "
            f"review scope {scope_id}"
        )
    # The id is derived from content, so a regenerated set every result's
    # ledger entry matches IS the set the reviewers were shown.
    results_match = bool(result_stems) and not notes
    return review_scope_record(
        phase_dir,
        scope_id=scope_id,
        base_ref=header_base_ref,
        base_commit=base_commit,
        written_by=written_by,
        coverage=coverage,
        omitted=omitted,
        result_notes=notes,
        results_match=results_match,
    )


def review_scope_report_lines(record: Optional[Dict[str, Any]]) -> List[str]:
    """``report.md``'s header lines for the scope manifest and its coverage."""
    if not record:
        return []
    if record.get("scopeFile"):
        manifest = f"[`{REVIEW_SCOPE_FILENAME}`]({REVIEW_SCOPE_FILENAME})"
    else:
        manifest = f"`{REVIEW_SCOPE_FILENAME}` (not on disk)"
    base_ref = record.get("baseRef") or ""
    if base_ref:
        base = f"base `{base_ref}`"
        if record.get("baseCommit"):
            base += f" at `{str(record['baseCommit'])[:12]}`"
    else:
        base = "no base ref"
    line = (
        f"**Review scope:** {manifest} — scope `{record.get('scopeId')}`, {base}, "
        f"written by {record.get('writtenBy')}"
    )
    if record.get("diffDir"):
        line += f"; per-file diffs in [`{REVIEW_DIFF_DIRNAME}/`]({REVIEW_DIFF_DIRNAME}/)"
    if record.get("regenerated"):
        if record.get("resultsMatch"):
            line += (
                ". Regenerated from the current tree, and every result's "
                "recorded scope matches it, so it is the set the reviewers "
                "were shown"
            )
        else:
            line += (
                ". Regenerated from the current tree: the change as it is now, "
                "not a record of what the reviewers read"
            )
    lines = [line]
    omitted = record.get("omitted") or []
    if record.get("coverage") == DIFF_COVERAGE_COMPLETE:
        lines.append(f"**Diff coverage:** {DIFF_COVERAGE_COMPLETE}")
    else:
        named = ", ".join(
            f"`{item['path']}` ({item['reason']})"
            for item in omitted[:REPORT_OMITTED_SAMPLE]
        )
        if len(omitted) > REPORT_OMITTED_SAMPLE:
            named += f", … and {len(omitted) - REPORT_OMITTED_SAMPLE} more"
        lines.append(
            f"**Diff coverage:** {DIFF_COVERAGE_PARTIAL} — {len(omitted)} source "
            f"and test file(s) have no diff file, so reviewers without a shell "
            f"could not review them" + (f": {named}" if named else "")
        )
    notes = record.get("results") or {}
    if notes:
        lines.append(
            "**Scope notes:** "
            + "; ".join(f"`{model}` {note}" for model, note in notes.items())
            + " — their findings stay in this report, but they did not review "
            "this scope"
        )
    return lines


def record_review_scope_in_report_data(
    phase_dir: Any, record: Optional[Dict[str, Any]]
) -> None:
    """Add ``diffCoverage`` and ``reviewScope`` to ``report_data.json``.

    Merged into the sidecar ``generate_html_report`` just wrote, rather than
    threaded through it, so the HTML generator stays phase-agnostic.
    Best-effort, like the sidecar write itself.
    """
    if not record:
        return
    sidecar = Path(phase_dir) / "report_data.json"
    try:
        data = json.loads(sidecar.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return
    if not isinstance(data, dict):
        return
    coverage: Dict[str, Any] = {
        "coverage": record.get("coverage"),
        "omitted": list(record.get("omitted") or []),
        "scopeFile": record.get("scopeFile"),
        "diffDir": record.get("diffDir"),
    }
    if record.get("coverage") != DIFF_COVERAGE_COMPLETE:
        coverage["note"] = (
            "reviewers without a shell could not review the omitted files"
        )
    data["diffCoverage"] = coverage
    data["reviewScope"] = {
        key: record.get(key)
        for key in (
            "scopeId", "baseRef", "baseCommit", "writtenBy", "regenerated",
            "scopeFile", "diffDir", "results",
        )
    }
    if "resultsMatch" in record:
        data["reviewScope"]["resultsMatch"] = record["resultsMatch"]
    try:
        # Replaced whole, as the generator writes it: apply reads it back.
        _review_round.replace_file(sidecar, sidecar_json(data))
    except OSError:
        pass


def emit_salvage_task(
    salvage_request: Dict,
    salvage_path: Path,
    phase_dir: Path,
    plan_path: Path,
) -> None:
    """Materialize the salvage task beside a just-written salvage request.

    The prompt is assembled in Python (D2/D2i) rather than by a Claude reading
    ``references/salvage-handling.md``, so any invoker can run it. Best-effort:
    the parse error that produced the request must not be masked by a task-file
    problem, and a request with no task file is still recoverable by hand.
    """
    try:
        task_path = write_salvage_task_file(
            salvage_request=salvage_request,
            salvage_request_path=str(salvage_path),
            phase_dir=str(phase_dir),
            plan_file=str(plan_path),
        )
        print(f"[SALVAGE_TASK] {task_path}")
    except Exception as task_error:  # noqa: BLE001 - diagnostics only
        print(f"Warning: could not materialize salvage task: {task_error}")


#: The issue fields a salvage subagent rebuilds a code reviewer's answer with.
SALVAGE_ISSUE_FIELDS = ("title", "desc", "importance", "file", "line_range", "type",
                        "anchor_text")


def salvage_issue_fields(commit_record: Optional[Mapping[str, Any]]) -> List[str]:
    """The salvage request's ``expected_schema.fields``. A commit review's
    reviewers also answer ``introduced_by``: a repaired answer without it
    would drop every claim that slot made, and attribution falls back to the
    claim. Any other run keeps the fields it always had."""
    fields = list(SALVAGE_ISSUE_FIELDS)
    if commit_record is not None:
        fields.append("introduced_by")
    return fields


def code_review_scope_baseline(
    state: Any,
    plan_path: Path,
    plan_document: Optional[BoundDocument],
    *,
    base_ref: Optional[str],
    head_ref: Optional[str] = None,
) -> Dict[str, Any]:
    """The scope baseline of a code (or commit) review round.

    Intent is the accepted plan — for a commit review, the pinned brief and
    its frozen context plan; the task list and the reviewed range are
    evidence. The primary document is hashed from the bytes the round binds
    to ``validation-snapshot.md`` (``plan_document``), else from the plan as
    read now (a ``--skip-validation`` round binds no snapshot).
    """
    record = getattr(state, "state", None) or {}
    commit_review = isinstance(record.get("commit_range"), dict)
    tasks_path: Optional[str] = None
    if not commit_review:
        try:
            tasks_path = find_tasks_file(str(plan_path))
        except (FileNotFoundError, ValueError, OSError):
            tasks_path = None
    return _scope_round.build_round_baseline(
        "code-review",
        plan_document=plan_document,
        plan_path=None if plan_document is not None else str(plan_path),
        primary_role="commit_brief" if commit_review else "plan",
        tasks_path=tasks_path,
        extra_sources=_scope_round.code_review_extra_sources(
            record, base_ref=base_ref, head_ref=head_ref,
        ),
    )


async def run_single_review(
    model_spec: str,
    plan_path: Path,
    out_dir: Path,
    timeout: Optional[int] = None,
    changed_files: Optional[List[str]] = None,
    base_ref: str = "HEAD~1",
    served_models: Optional[Dict[str, Dict[str, Any]]] = None,
    usage: Optional[Dict[str, Dict[str, Any]]] = None,
    *,
    tracker: Optional[FanoutProgress] = None,
    scope_source: Optional[str] = None,
    task_ids: Optional[Dict[str, str]] = None,
    scope_file: Optional[str] = None,
    diff_dir: Optional[str] = None,
    scope_id: Optional[str] = None,
    diff_coverage: Optional[str] = None,
    run_model_specs: Optional[List[str]] = None,
    pinned: Optional[PinnedRange] = None,
    scope_policy: Optional[str] = None,
) -> Tuple[bool, Optional[List[Dict]], Optional[str]]:
    """
    Run a single model code review using agent exploration with file-based output.

    Uses file-based JSON output where the LLM writes results to a specified file
    instead of stdout. Falls back to stdout parsing if file output fails.

    The agent will:
    1. Read the plan file to understand requirements
    2. Take the files to review from the resolved scope it is handed
    3. Read each file's change from the diff set main wrote before dispatch
       (``review-scope.md`` and ``diff/``), reached the way its adapter can
       (the ``{diff_access}`` block, :func:`utils.prompt_channels.render_diff_access`)
    4. Write findings as JSON to the specified output file

    Args:
        model_spec: Model specification (e.g., 'cursor-agent:auto', 'gemini:gemini-2.5-flash')
        plan_path: Path to the implementation plan
        out_dir: Directory for output files
        timeout: Optional timeout override in seconds. Uses provider default if not specified.
        changed_files: The resolved review scope, in review order (main
            applies ``order_review_paths`` to ``ReviewScope.paths``). It used to
            be the implement phase's raw ``tracked_files``, which main passed
            even when it had just resolved a git-diff fallback — so every
            reviewer of a plan with no implement phase got an empty list.
        base_ref: Git reference to diff against (commit at implementation start)
        scope_source: ``ReviewScope.source`` — where ``changed_files`` came
            from — rendered into ``prompt_context["scope_source"]`` by
            :func:`describe_scope_source`.
        task_ids: ``ReviewScope.task_ids``; each listed path's ``(from task:
            <id>)`` attribution. Empty for every source but ``tracked_files``.
        scope_file: Absolute path of the ``review-scope.md`` main wrote
            (:func:`utils.git_utils.write_review_diff`). ``None`` — a direct
            call — renders the scope placeholders as "none written" and skips
            the diff-access decision, so the slot dispatches as it always did.
        pinned: The two commits a pinned review (``--head-ref``) is of: the
            ``{diff_access}`` block names ``<base7>..<head7>`` ending at the
            head commit, the drifted files and the pinned-head read rule, and
            ``{scope_source}`` names the range. ``None`` renders today's text.
        diff_dir: Absolute path of the ``diff/`` beside it.
        scope_id: That set's scope id. At attempt start a ``<stem>.json``
            the scope ledger ties to another id is retired to
            ``.stale-<id|unknown>``, and the ledger records this id.
        diff_coverage: That set's coverage, ``complete`` or ``partial``; a
            lane that cannot open the phase dir gets the change inline only
            when it is complete (D2.3).
        served_models: Optional collector for the attribution.  When a
            configured ``--fallback-model`` list produced a served model, this
            slot's ``{model_spec: {"served_model", "fallback"}}`` entry is
            written into it, so the report can name the model that really
            answered.  The return tuple is deliberately unchanged — every caller
            of it destructures three values.
        usage: Optional collector for what the slot spent, filled from
            ``details["usage"]`` when the adapter reported any — the same
            channel and the same absent-means-unreported rule as above, and a
            collector for the same reason: the return tuple has no fourth slot.
            This lane's twin of the base fan-out's :func:`collect_usage`.
        tracker: The fan-out's
            :class:`~utils.progress_tracker.FanoutProgress`, when
            ``run_all_reviews`` supplied one.  This function owns the *terminal*
            transitions for its slot — the return tuple is ``(success, issues,
            error)`` and carries no ``source``, so ``record_result`` does not
            fit and each site calls ``done``/``failed`` itself, passing the
            ``source`` the completion print already names.  ``None`` (a direct
            call, or a fixture) leaves every transition unmade and costs nothing
            but the map, which is what keeps this function callable on its own.

    The slot is :func:`utils.review_lane.run_slot`, the core review-plan's
    slot runs too (the guard, the ladder loop and the checks), over this
    lane's :class:`CodeSlot`; this function is its entry point.

    Returns:
        Tuple of (success, issues_list, error)
    """
    start_time = time.time()
    slot = CodeSlot(
        model_spec, plan_path, out_dir, timeout=timeout,
        changed_files=changed_files, base_ref=base_ref,
        served_models=served_models, usage=usage, tracker=tracker,
        scope_source=scope_source, task_ids=task_ids, scope_file=scope_file,
        diff_dir=diff_dir, scope_id=scope_id, diff_coverage=diff_coverage,
        run_model_specs=run_model_specs, pinned=pinned, scope_policy=scope_policy,
    )
    return (await _review_lane.run_slot(slot, start_time=start_time)).as_review()


def code_slot_steps() -> "_review_lane.SlotSteps":
    """review-code's :class:`~utils.review_lane.SlotSteps`, from this module's
    names as they are bound when it is called, so a test that patches one here
    reaches :func:`~utils.review_lane.run_slot`."""
    return _review_lane.SlotSteps(
        slot_guard=SlotGuard,
        refused=Refused,
        slot_ladder=slot_ladder,
        phase_thread=phase_thread,
        misnamed_result_baseline=misnamed_result_baseline,
        requested_result_baseline=requested_result_baseline,
        invoke_with_file_output=invoke_with_file_output,
        dispatch_with_ladder=dispatch_with_ladder,
        sandbox_fallback_kwargs=sandbox_fallback_kwargs,
        retire_salvage_artifacts=retire_salvage_artifacts,
        retire_rejected=RETIRE_REJECTED,
    )


class CodeSlot:
    """review-code's model slot, a :class:`~utils.review_lane.ReviewSlot`
    (see :func:`run_single_review`).

    What it holds is what this lane's slot does its own way: the scope ledger
    and an earlier attempt's salvage pair, the diff set and how the lane
    reaches it (``[REVIEW_UNSUPPORTED]`` when it cannot), the commit
    templates, the argv cap of an inline prompt, the slot's provenance in the
    run's collectors, a failure's spend on its error, the slot's own terminal
    tracker transitions, the salvage request written here, and the issue list
    checked here (docs/development/review-results.md, "The shared review
    lane").
    """

    def __init__(
        self,
        model_spec: str,
        plan_path: Path,
        out_dir: Path,
        *,
        timeout: Optional[int],
        changed_files: Optional[List[str]],
        base_ref: str,
        served_models: Optional[Dict[str, Dict[str, Any]]],
        usage: Optional[Dict[str, Dict[str, Any]]],
        tracker: Optional[FanoutProgress],
        scope_source: Optional[str],
        task_ids: Optional[Dict[str, str]],
        scope_file: Optional[str],
        diff_dir: Optional[str],
        scope_id: Optional[str],
        diff_coverage: Optional[str],
        run_model_specs: Optional[List[str]],
        pinned: Optional[PinnedRange],
        scope_policy: Optional[str],
    ) -> None:
        self.model_spec = model_spec
        self.plan_path = plan_path
        self.anchor = str(plan_path)
        self.guard_plan_path = plan_path
        self.out_dir = out_dir
        self.timeout = timeout
        self.changed_files = changed_files
        self.base_ref = base_ref
        self.served_models = served_models
        self.usage = usage
        self.tracker = tracker
        self.scope_source = scope_source
        self.task_ids = task_ids
        self.scope_file = scope_file
        self.diff_dir = diff_dir
        self.scope_id = scope_id
        self.diff_coverage = diff_coverage
        self.run_model_specs = run_model_specs
        self.pinned = pinned
        self.scope_policy = scope_policy

        # Detect project root so CLI providers (e.g. Claude Code) run in the
        # correct working directory and can access project files.
        self.project_root = get_project_root(str(plan_path))
        # Parse the model spec to get provider info for display, anchored on the plan.
        self.provider_name, model_name = parse_model_spec(model_spec, anchor=str(plan_path))
        self.display_name = f"{self.provider_name}:{model_name}"

        # Set by `prepare`, once the guard has admitted the slot.
        self.phase_dir: Optional[Path] = None
        self.log_file: Optional[Path] = None
        self.sanitized_model = ""
        self.commit_record: Optional[Mapping[str, Any]] = None
        self.diff_access: Any = None

    def slot_steps(self) -> "_review_lane.SlotSteps":
        return code_slot_steps()

    def _failed(self, error: str, *, source: str) -> "_review_lane.SlotResult":
        """A failed ending, this lane's terminal tracker transition taken here."""
        if self.tracker is not None:
            self.tracker.failed(self.model_spec, error=error, source=source)
        return _review_lane.SlotResult(self.model_spec, False, payload=None, error=error)

    def refused(self, reason: str) -> "_review_lane.SlotResult":
        # The gate `run_single_model` applies to the other review lanes, asked
        # here for the same reason and off the same once-per-run cache: this
        # slot is a `generate` dispatch, and a runner whose own sandbox cannot
        # start reads neither the plan nor the diff — it answers with a
        # sentence about not being able to open them, which scores as a
        # completed review. Refused before the phase dir is claimed and before
        # an earlier attempt's salvage pair is retired, because a refused slot
        # replaces nothing. The one thing a refusal still retires is a
        # `<stem>.json` from ANOTHER scope (D2.2): it is not a review of this
        # change whether or not this attempt runs, and left on disk the next
        # `--reaggregate` would load it, move the model out of `models_failed`
        # and report another change's findings as this one's.
        #
        # Retired, never re-recorded: no attempt started, so the ledger keeps
        # the old id — the one the `.stale-<id>` name carries — and the next
        # attempt that really starts records this scope over it.
        if self.scope_id is not None:
            retire_result_from_another_scope(
                get_phase_dir(self.plan_path, 'code-review'),
                sanitize_model_name(self.model_spec),
                self.scope_id,
            )
        # Terminal, and `not-dispatched` is the whole of what happened: no
        # attempt was started, so there is no channel a result could have come
        # from. Without this the slot would sit `queued` until the fan-out's
        # sweep retired it as `cancelled`, which names the wrong cause for a
        # model the report is about to list under its sandbox error.
        return self._failed(reason, source="not-dispatched")

    async def prepare(self, sandbox: Any) -> Any:
        model_spec, plan_path, display_name = self.model_spec, self.plan_path, self.display_name
        project_root, base_ref, changed_files = self.project_root, self.base_ref, self.changed_files
        pinned = self.pinned

        # Generate log file path for debugging
        sanitized_model = sanitize_model_name(model_spec)
        phase_dir = get_phase_dir(plan_path, 'code-review')
        phase_dir.mkdir(parents=True, exist_ok=True)
        log_file = phase_dir / f"log_{sanitized_model}.txt"
        self.sanitized_model, self.phase_dir, self.log_file = sanitized_model, phase_dir, log_file

        # This model's attempt starts here, so a salvage pair an earlier attempt left
        # in the phase dir stops being outstanding work before the provider is
        # invoked. The phase dir is stable per plan and `--force` deletes nothing, so
        # without this the previous run's `salvage_task_<stem>.json` would still be
        # dispatched over this model's fresh result path. Retire by rename, at the
        # attempt that replaces the artifact: a resumed model that is skipped keeps
        # its pair, and a model dropped from the selection keeps its stale pair as it
        # keeps its stale `<model>.json`. Quiet; the renamed file is the audit trail
        # (docs/development/delegation.md#in-process-continuations).
        retire_salvage_artifacts(
            str(phase_dir), sanitized_model, reason=RETIRE_SUPERSEDED, quiet=True
        )

        # The same rule for this model's result file, keyed on the scope it
        # reviewed (D2.2): a `<stem>.json` written against another change is
        # retired to `.stale-<id|unknown>` before this attempt can fail and leave
        # it behind, and then the ledger records what THIS attempt is shown. The
        # skip branch in `run_all_reviews` only sends a result here when its
        # ledger id differs, but `--rerun-all` reaches here with every result.
        if self.scope_id is not None:
            retire_result_from_another_scope(phase_dir, sanitized_model, self.scope_id)
            record_scope_attempt(phase_dir, sanitized_model, self.scope_id)

        # How this lane reaches the change (D2.3): by path when its adapter can
        # read the phase dir, inline when it cannot and the whole change fits the
        # argv cap with nothing omitted, and otherwise not at all. Decided before
        # `tracker.running`, because an unsupported slot is not dispatched and
        # costs nothing: it is recorded failed with the reason, so the report names
        # it like any other lost reviewer, rather than handed a prompt it cannot
        # act on — which is how two cursor-agent lanes once "reviewed" a change
        # they never saw.
        #
        # A commit brief's run (its state records `commit_range`) with a context
        # plan hands the frozen snapshot over too: an inline lane cannot open it, so its
        # text is one more block
        # of the bounded payload, and a lane it does not fit is not dispatched.
        commit_record = commit_report.run_commit_range(plan_path)
        self.commit_record = commit_record
        context_plan = commit_report.context_plan_path(
            commit_record, repo_root=project_root or os.getcwd()
        )
        diff_access = None
        if self.scope_file is not None and self.diff_dir is not None:
            diff_access = render_diff_access(
                model_spec,
                self.scope_file,
                self.diff_dir,
                str(phase_dir.absolute()),
                project_root or os.getcwd(),
                base_ref=base_ref,
                coverage=self.diff_coverage or DIFF_COVERAGE_PARTIAL,
                plan_path=str(plan_path.absolute()),
                anchor=str(plan_path),
                context_plan_path=context_plan,
                **(
                    {"head_ref": pinned.head, "drifted": list(pinned.drifted)}
                    if pinned is not None else {}
                ),
            )
            if diff_access.mode == "unsupported":
                detail = (
                    f"read scope {diff_access.read_scope}, inline "
                    f"{diff_access.inline_bytes} B — {diff_access.reason}"
                )
                print(f"[REVIEW_UNSUPPORTED] {display_name}: {detail}")
                return self._failed(f"review unsupported: {detail}", source="not-dispatched")
        self.diff_access = diff_access

        if diff_access is None:
            plan_text, scope_file_text, diff_dir_text = (
                str(plan_path.absolute()), NO_SCOPE_MANIFEST_TEXT, NO_DIFF_DIR_TEXT,
            )
            diff_access_text, full_scope_ref = NO_DIFF_ACCESS_TEXT, None
        elif diff_access.mode == "inline":
            # The lane cannot open the phase dir, so the prompt names no path there:
            # every pointer is to a labelled block inside `{diff_access}`.
            plan_text, scope_file_text, diff_dir_text = (
                INLINE_PLAN_TEXT, INLINE_SCOPE_FILE_TEXT, INLINE_DIFF_DIR_TEXT,
            )
            diff_access_text, full_scope_ref = diff_access.text, INLINE_FULL_SCOPE_REF
        else:
            plan_text, scope_file_text, diff_dir_text = (
                str(plan_path.absolute()), str(self.scope_file), str(self.diff_dir),
            )
            diff_access_text, full_scope_ref = diff_access.text, str(self.scope_file)

        # The resolved scope, in the review order main gave it. The placeholder key
        # keeps its old name (`tracked_files_list`) because the template binds it;
        # what it carries is now the scope whatever its source. When the list is
        # cut, its notice names the manifest as the full list, so a dropped path
        # never reads as out of scope.
        tracked_files_list = format_tracked_files_for_prompt(
            changed_files or [], task_ids=self.task_ids, full_scope_ref=full_scope_ref
        )

        # Load prompt template. A commit brief's run (its state records
        # `commit_range`, read above) gets `commit_review.txt`; every other run, a
        # direct `--head-ref` one included, keeps `code_review.txt`.
        prompt_template = (
            load_code_review_prompt() if commit_record is None
            else load_prompt(commit_report.review_prompt_name(commit_record))
        )

        # Derive prefix from plan path (same as in main())
        prefix = derive_prefix(plan_path)

        # Build prompt context for invoke_with_file_output. The implementation
        # record is read here, per slot, rather than threaded down from main(): it
        # is three small files, and `run_all_reviews` hands this slot every
        # other input it needs from the plan path alone.
        #
        # Every placeholder the template binds has its key here on every path
        # (`working_limits`, `output_location` and `output_json_path` are added by
        # `invoke_with_file_output`): a placeholder with no key fails the slot with
        # `PROMPT_FORMAT_ERROR`, and it would fail every slot at once.
        prompt_context = {
            "plan_path": plan_text,
            "tracked_files_list": tracked_files_list,
            # Where the list came from (tracked files, the `git diff` fallback,
            # `--files`, or nothing).
            "scope_source": describe_scope_source(self.scope_source, base_ref, pinned),
            "base_ref": base_ref,
            "prefix": prefix,
            "implementation_record": build_implementation_record(plan_path),
            "scope_file": scope_file_text,
            "diff_dir": diff_dir_text,
            "diff_access": diff_access_text,
            # The round's scope block, rendered per slot from the resolved policy:
            # a commit review judges scope against its brief, a code review against
            # the accepted plan.
            "scope_policy_guidance": _sp.reviewer_guidance(
                self.scope_policy,
                _scope_round.guidance_phase("code-review", commit_review=commit_record is not None),
            ),
        }
        if commit_record is not None:
            # The commit template's own slots. The block's pointer names
            # the brief by the path this lane can open, or the `git log` command
            # when it cannot open the brief at all.
            inline_lane = diff_access is not None and diff_access.mode == "inline"
            prompt_context.update(commit_report.commit_prompt_context(
                commit_record,
                brief_text=plan_text,
                brief_pointer=None if inline_lane else str(plan_path.absolute()),
                repo_root=project_root,
                scope_total=len(changed_files or []),
                inline=inline_lane,
            ))

        # Determine timeout: use provided override, or get provider-specific default
        effective_timeout = (
            self.timeout if self.timeout is not None
            else get_provider_timeout(self.provider_name, anchor=str(plan_path))
        )
        return _review_lane.SlotDispatch(
            prompt_template=prompt_template,
            prompt_context=prompt_context,
            output_dir=self.out_dir,
            invoke_phase="code_review",
            log_file=str(log_file),
            timeout=effective_timeout,
            start_line=lambda attempt, attempt_timeout: (
                f"[{display_name}] Starting code review with file-based output "
                f"(attempt {attempt}, timeout: {attempt_timeout}s "
                f"of a {effective_timeout}s slot)..."
            ),
            jail_summary_key=phase_dir,
        )

    def before_dispatch(
        self, dispatch: "_review_lane.SlotDispatch",
    ) -> Optional["_review_lane.SlotResult"]:
        # The inline cap bounds the `{diff_access}` block alone, but the
        # prompt that goes on argv also carries the implementation record, the
        # file list, the template and the working limits. Measured whole, as it
        # will be dispatched, so a block that fit is still refused — undispatched,
        # `[REVIEW_UNSUPPORTED]` like any other inline miss — when the prompt it
        # sits in would fail the spawn with E2BIG and be recorded as a provider
        # error. `None` is a lane whose prompt does not travel on argv.
        diff_access = self.diff_access
        if diff_access is None or diff_access.mode != "inline":
            return None
        prompt_bytes = argv_prompt_bytes(
            dispatch.prompt_template,
            self.model_spec,
            dispatch.prompt_context,
            dispatch.output_dir,
            "code_review",
            timeout=int(dispatch.timeout),
            anchor=str(self.plan_path),
        )
        if prompt_bytes is not None and prompt_bytes > INLINE_PROMPT_CAP_BYTES:
            detail = (
                f"read scope {diff_access.read_scope}, inline "
                f"{diff_access.inline_bytes} B — rendered prompt {prompt_bytes} B "
                f"exceeds the {INLINE_PROMPT_CAP_BYTES} B argv cap"
            )
            print(f"[REVIEW_UNSUPPORTED] {self.display_name}: {detail}")
            return self._failed(f"review unsupported: {detail}", source="not-dispatched")
        return None

    def ladder_refused(self, reason: str, duration: float) -> "_review_lane.SlotResult":
        return self._failed(reason, source="not-dispatched")

    def after_ladder(self, run: Any) -> None:
        # Record which model served this slot before any of the endings
        # return, so a fallback that fired is attributed even on the paths
        # that end in salvage. Only ever populated when a fallback is configured.
        # The D6 override's provenance lands in the same collector,
        # with or without a served model beside it.
        details = run.details
        if self.served_models is not None:
            entry: Dict[str, Any] = {}
            if details.get("served_model"):
                entry["served_model"] = details["served_model"]
                entry["fallback"] = bool(details.get("served_model_is_fallback"))
            # A contained rung arrives as its rung id (`landlock`), so map through
            # the same helper the review-plan collector uses: `bypassed` for the
            # uncontained rung, `fallback-<rung>` for a contained one.
            word = sandbox_record_word(details.get("sandbox"))
            if word:
                entry["sandbox"] = word
            # A slot the plugin's jail failed keeps `failure_reason: jail-denied`
            # and the path on the durable record (F1 item 6, 2026-09-30).
            entry.update(jail_record_fields(details))
            if entry:
                self.served_models[self.model_spec] = entry
        # Stage U: and what it spent, recorded here for the same reason and before
        # the same endings — a slot that ends in salvage, or fails outright, spent
        # what it spent, summed over every attempt. Absent when the adapter reported
        # nothing; never `{}`, which would read as a free review.
        if self.usage is not None:
            spent = run.usage
            if isinstance(spent, dict) and spent:
                self.usage[self.model_spec] = spent

    def outcome(
        self, run: Any, violated: Optional[str], duration: float,
    ) -> "_review_lane.SlotResult":
        model_spec, plan_path, display_name = self.model_spec, self.plan_path, self.display_name
        phase_dir, log_file, sanitized_model = self.phase_dir, self.log_file, self.sanitized_model
        commit_record = self.commit_record
        tracker = self.tracker
        # The last returned attempt's; `{}` when the first dispatch raised.
        result = run.result or {}
        output_file = result.get("output_file", "")
        source = "exception" if run.exception is not None else result.get("source", "unknown")

        # The guard's checks failed the slot (`run_slot` ran them over every
        # attempt, on the uncontained rung the porcelain check, on the plugin's
        # jail the mode and home checks, whose `[JAIL_DENIED]` line and denial
        # count the ladder loop printed per attempt). Failed whatever the
        # invocation reported — nothing is restored, and nothing it returned is
        # parsed as a review: `source` records which channel the rejected answer
        # arrived on, `error` why nothing of it is parsed. `run_slot` passes its
        # own reason here too, for an answer it does not accept
        # (`review_lane.UNSHOWN_ANSWER_REASON`), which rejects nothing.
        if violated is not None:
            return self._failed(violated, source=source)

        if run.exception is not None:
            # A dispatch raised, which ended the slot; recorded as that exception
            # after the checks above, with what every attempt before it spent, as
            # the review base records it.
            error_msg = slot_exception_error(run.exception)
            spent = describe_usage(run.usage)
            if spent:
                error_msg = f"{error_msg} (spent {spent})"
            print(f"[{display_name}] {error_msg}")
            return self._failed(error_msg, source="exception")

        print(f"[{display_name}] Log saved to: {log_file}")
        # Only for a slot that answered: a failed invocation carries `output_file`
        # and no `source`, and "Result will be saved to: <path> (source: unknown)"
        # two lines above "Agent failed" promised a file nothing would write
        # (measured 2026-09-17, on every one of a run's three dead slots).
        if output_file and result["success"]:
            print(f"[{display_name}] {describe_output_file(output_file, source)}")

        if not result["success"]:
            # The ladder's own reason when it ended the slot (the 429 chain, a
            # context overflow's remedies, a budget that refused the retry), and
            # the attempt's error otherwise, as on the review base.
            error_msg = run.stop_error(model_spec)
            # What the failed slot spent, on the one string every artifact of a
            # failure carries: this ending's `error` is what `save_model_result`
            # writes to `error_<model>.log` and what `.status.json` records under
            # `models_failed`, and the triple `run_single_review` returns is
            # destructured by every caller, so a fourth value has nowhere to go.
            # Measured 2026-09-17: $25.05 and 137 348 output tokens went into a
            # claude-code slot that ended on a usage cap, and the only place
            # either number existed was the raw envelope in `log_<model>.txt`.
            spent = describe_usage(run.usage)
            if spent:
                error_msg = f"{error_msg} (spent {spent})"
            file_error = result.get("file_error", "")
            if file_error:
                print(f"[{display_name}] File error: {file_error}")
            print(f"[{display_name}] Agent failed ({duration:.1f}s): {error_msg}")

            # Write a salvage request only when the failure output still holds an
            # answer to repair, never on "stderr is non-empty": a hard provider
            # failure (an auth error with no JSON in the stream) would otherwise get
            # an empty array written over this model's result path and aggregate as a
            # reviewer that found nothing. With nothing to salvage the model stays
            # failed. The source is the adapter's `salvage_text` when it has one (a
            # stream adapter's answer is not its stream), else the first non-empty of
            # `stdout_excerpt`, then stderr: precedence, never concatenation, because
            # `raw_output` goes to a subagent as the one damaged answer to repair. The
            # gate judges `raw_content` and the request stores the same text
            # (docs/development/delegation.md#in-process-continuations).
            details = result.get("details", {}) or {}
            raw_content = salvage_source(details)
            timed_out = salvage_failure_kind(result) is not None
            salvageable = has_salvageable_json(raw_content)

            if salvageable and _review_lane.salvage_refused(str(phase_dir), model_spec):
                pass  # a recovered phase: said there, and the model stays failed
            elif salvageable:
                salvage_request = {
                    "model": model_spec,
                    "phase": "code_review",
                    "raw_output": raw_content,
                    "expected_type": "array",
                    "expected_schema": {
                        "fields": salvage_issue_fields(commit_record),
                        "optional_fields": list(_sp.SCOPE_FIELDS),
                        "importance_values": list(_importance.MODEL_VALUES),
                        "type_values": ["bug", "missing", "improvement", "style", "scope"]
                    },
                    "output_path": str(phase_dir / f"{sanitized_model}.json"),
                    "output_json_path": output_file,
                    "timestamp": datetime.now().isoformat(),
                    # `"failure": "timeout"` on a run a deadline ended, so the
                    # executor refuses a salvaged `[]` from it (D4.5): a reviewer
                    # killed mid-review never reported an empty review.
                    **salvage_failure_fields(result),
                }
                salvage_path = phase_dir / f"salvage_{sanitized_model}.json"
                with open(salvage_path, 'w', encoding='utf-8') as f:
                    json.dump(salvage_request, f, indent=2)
                print(f"[SALVAGE_NEEDED] {salvage_path}")
                emit_salvage_task(salvage_request, salvage_path, phase_dir, plan_path)
            elif timed_out and not raw_content.strip():
                # A deadline, and no answer text at all: the adapter read its whole
                # stream and found none (a reviewer killed while a tool ran, or
                # while it was still reasoning), or the run printed nothing. Named
                # as the timeout it was, not as a provider that never produced JSON.
                print(
                    f"[{display_name}] Provider timed out before writing an answer — "
                    f"nothing to salvage, model recorded as failed"
                )
            else:
                # Say which failure this was, in the same line-per-model channel the
                # markers use. Silence here would read as "salvage was not reached",
                # when what happened is that the provider failed before it produced
                # an answer — an auth, quota or launch failure whose fix is the
                # provider, not a JSON repair. The stream itself is in the log file
                # named above; the one-line summary belongs to the adapter's
                # `describe_failure` hook, which is why it is not re-printed here.
                print(
                    f"[{display_name}] Provider failed before producing any JSON — "
                    f"nothing to salvage, model recorded as failed"
                )

            # The failure print above is this slot's terminal site, and `error_msg`
            # is the same string `save_model_result` writes to `error_<model>.log`
            # and `main()` keys into `failed_models` — one reason, in the table and
            # in the report's failure list, rather than one phrasing per reader.
            return self._failed(error_msg, source=source)

        if result.get("misnamed_from"):
            report_misnamed_result(model_spec, result, phase_dir)
        print(f"[{display_name}] Completed in {duration:.1f}s (source: {source})")

        # Get the parsed data from result
        output_data = result.get("data")

        if isinstance(output_data, list):
            # Validate issues format
            is_valid, errors = validate_code_review_issues(output_data)
            if not is_valid:
                print(f"[{display_name}] Warning: Validation errors: {errors}")
            # Stored in canonical spelling, as the base lane stores it.
            _importance.canonicalize(output_data)
            print(f"[{display_name}] Found {len(output_data)} issues")
            # `done` at the *return*, not at the completion print two branches up,
            # even though the print is where `source` is named. The print only says
            # the provider exited cleanly; whether there is a usable result is
            # decided here, and the two branches below it return a failure with an
            # error `main()` keys into `failed_models`. Terminal transitions are
            # idempotent, so a `done` stamped at the print would freeze those slots
            # `done` in the table while the report called them failed.
            if tracker is not None:
                tracker.done(model_spec, source=source)
            return _review_lane.SlotResult(model_spec, True, payload=output_data, error=None)
        elif isinstance(output_data, dict) and "raw" in output_data:
            # No valid JSON found - write salvage request for Claude Code to process
            raw_content = output_data["raw"]
            raw_preview = raw_content[:500] if raw_content else "(empty)"

            # Same rule as the hard-failure path above, for the same reason: a reply
            # with no JSON in it is not a parse failure, and salvage against it can
            # only print the empty array its prompt falls back to. This branch is
            # where the two write-refusal shapes land — cursor-agent's "I can't
            # write the requested file while Ask mode is active" and gemini's
            # "JSON written to …" confirmation for a write that never happened —
            # and a `[]` recorded for either would be an invented clean review.
            if not has_salvageable_json(raw_content):
                print(f"[{display_name}] Response carries no JSON — nothing to salvage")
                return self._failed(
                    f"Model produced no JSON output: {raw_preview}", source=source,
                )
            if _review_lane.salvage_refused(str(phase_dir), model_spec):
                return self._failed(
                    f"Could not extract JSON from response: {raw_preview}", source=source,
                )

            salvage_request = {
                "model": model_spec,
                "phase": "code_review",
                "raw_output": raw_content,
                "expected_type": "array",
                "expected_schema": {
                    "fields": salvage_issue_fields(commit_record),
                    "optional_fields": list(_sp.SCOPE_FIELDS),
                    "importance_values": list(_importance.MODEL_VALUES),
                    "type_values": ["bug", "missing", "improvement", "style", "scope"]
                },
                "output_path": str(phase_dir / f"{sanitized_model}.json"),
                "output_json_path": output_file,
                "timestamp": datetime.now().isoformat()
            }
            salvage_path = phase_dir / f"salvage_{sanitized_model}.json"
            with open(salvage_path, 'w', encoding='utf-8') as f:
                json.dump(salvage_request, f, indent=2)

            print(f"[SALVAGE_NEEDED] {salvage_path}")
            emit_salvage_task(salvage_request, salvage_path, phase_dir, plan_path)
            # Failed *for now*: a salvage subagent may repair this model's result
            # file minutes from now, and `main()` moves it out of `failed_models`
            # when it does. The map is the fan-out's record of what the fan-out saw,
            # so it says what happened here; `record_models_present` is the writer
            # that reconciles a later repair.
            return self._failed(
                f"Could not extract JSON from response: {raw_preview}", source=source,
            )
        return self._failed(
            f"Expected JSON array, got {type(output_data).__name__}", source=source,
        )

    def raised(self, exc: Exception) -> Optional["_review_lane.SlotResult"]:
        # Left to `run_all_reviews`' slot wrapper, which records it with its
        # own text (`raised_slot_record`), as a direct call raises it.
        return None


async def run_all_reviews(
    model_specs: List[str],
    plan_path: Path,
    out_dir: Path,
    timeout: Optional[int],
    max_parallel: int,
    changed_files: Optional[List[str]] = None,
    base_ref: str = "HEAD~1",
    skip_existing: bool = True,
    served_models: Optional[Dict[str, Dict[str, Any]]] = None,
    usage: Optional[Dict[str, Dict[str, Any]]] = None,
    prior_usage: Optional[Dict[str, Dict[str, Any]]] = None,
    tracker_out: Optional[List[FanoutProgress]] = None,
    scope_source: Optional[str] = None,
    task_ids: Optional[Dict[str, str]] = None,
    scope_file: Optional[str] = None,
    diff_dir: Optional[str] = None,
    scope_id: Optional[str] = None,
    diff_coverage: Optional[str] = None,
    pinned: Optional[PinnedRange] = None,
    scope_policy: Optional[str] = None,
) -> Dict[str, Tuple[bool, Optional[List[Dict]], Optional[str]]]:
    """
    Run code review across all models using agent exploration.

    Supports multiple providers - each model spec can specify a different
    provider (e.g., 'cursor-agent:auto', 'gemini:gemini-2.5-flash').

    Each agent:
    - Receives the resolved review scope, in review order, labelled with its source
    - Receives the base_ref to use for git diff commands
    - Reads the plan to understand requirements
    - Uses git diff to examine actual changes
    - Writes findings to a JSON file

    Args:
        model_specs: List of model specifications in provider:model format
        plan_path: Path to the implementation plan
        out_dir: Output directory for results
        timeout: Optional timeout override per model in seconds. If None, uses per-provider defaults.
        max_parallel: Maximum concurrent model invocations
        changed_files: The resolved, ordered review scope, forwarded to each
            :func:`run_single_review` (see its docstring)
        base_ref: Git reference to diff against
        scope_source: ``ReviewScope.source``, forwarded the same way
        task_ids: ``ReviewScope.task_ids``, forwarded the same way
        scope_file, diff_dir, scope_id, diff_coverage: The diff set main wrote
            before dispatch (``write_review_diff``), forwarded the same way.
            ``scope_id`` also gates the resume: an existing result is reused
            only when the scope ledger records this id for its stem;
            otherwise ``[SCOPE_CHANGED]`` and the model re-runs. ``None``
            reuses every result, as before the ledger existed.
        pinned: The two commits of a pinned review, forwarded to each
            :func:`run_single_review` (only when set, so a stand-in written for
            an unpinned run need not accept it).
        served_models: Optional attribution collector, forwarded to each
            :func:`run_single_review` (see its docstring)
        usage: Optional per-slot usage collector, forwarded the same way
        prior_usage: What an earlier attempt of this phase recorded, read off
            the checkpoint before this run replaced it.  A slot answered from
            its existing ``<model>.json`` invokes no adapter and so reports no
            usage of its own; its entry here is copied into ``usage`` at the
            skip, which is the one place that knows a result was reused.  A
            slot that really re-runs is never seeded from it.
        tracker_out: Optional one-element collector for the
            :class:`~utils.progress_tracker.FanoutProgress` this function builds.
            The fan-out owns the tracker — it seeds the map before the first
            dispatch, runs the ticker and sweeps in its own ``finally`` — but
            F11's backfill runs one level up, in ``main()``, and has to give the
            map the same treatment it gives ``failed_models``.  Handed back
            through a collector for the same reason ``served_models`` and
            ``usage`` are: this function's return value is destructured by every
            caller, so there is no second slot in it.

    Returns:
        Dict mapping model spec to tuple of (success, issues_list, error)
    """
    # The tracker carries the slots' map: `models_done` counts finished slots,
    # not successful ones (a failed or skipped model has finished its slot),
    # and `models_succeeded` the ones with a usable result. Built here and
    # handed back through `tracker_out`, because F11's backfill runs one level
    # up and gives the map the treatment it gives `failed_models`.
    tracker = FanoutProgress(
        str(get_phase_dir(plan_path, 'code-review')),
        model_specs,
        anchor=str(plan_path),
        # This fan-out's per-model override. `None` leaves each slot's budget to
        # `get_provider_timeout`, which is the same call the total deadline is
        # sized from, so the table's denominator and the deadline agree.
        timeout=timeout,
    )
    if tracker_out is not None:
        tracker_out.append(tracker)
    pinned_kwargs: Dict[str, Any] = {"pinned": pinned} if pinned is not None else {}
    # Only a non-default policy is handed down by keyword: the slot's own
    # default renders `expand`, so a default run calls it exactly as before.
    scope_kwargs: Dict[str, Any] = (
        {"scope_policy": scope_policy}
        if _sp.effective(scope_policy) != _sp.DEFAULT_POLICY else {}
    )

    def display_name_of(model_spec: str) -> str:
        provider_name, model_name = parse_model_spec(model_spec, anchor=str(plan_path))
        return f"{provider_name}:{model_name}"

    def skip_existing_result(model_spec: str, index: int) -> Optional[_review_lane.SlotResult]:
        """A resumed slot answered from its ``<model>.json``, or ``None`` to run it."""
        if not skip_existing:
            return None
        display_name = display_name_of(model_spec)
        sanitized = sanitize_model_name(model_spec)
        phase_dir = get_phase_dir(plan_path, 'code-review')
        # D2.2: a result is reused only when it reviewed the diff set this
        # run's reviewers are shown. One written against an earlier change —
        # or before the ledger existed, which is `unknown` — re-runs, and
        # `run_single_review` retires the old file at its attempt start. The
        # alternative reports a review of another change as a review of this
        # one. `util resume-state` applies the same test.
        existing = existing_result_reuse(phase_dir, sanitized, scope_id)
        if existing.verdict == "corrupt":
            print(f"[{display_name}] Existing result file corrupt, re-running...")
        elif (existing.verdict == "withheld"
              and existing.withheld.key != _result_files.RECOVERED_KEY):
            # A recovered phase reuses no file at all, which its round's
            # opening said once.
            print(f"[{display_name}] Result file is from a slot that "
                  f"{existing.withheld.phrase}; re-running...")
        elif existing.verdict == "scope_changed":
            print(
                f"[SCOPE_CHANGED] {display_name}: result reviewed "
                f"scope {existing.reviewed_scope or SCOPE_UNKNOWN}, this "
                f"run's is {scope_id}; re-running"
            )
        elif existing.verdict == "reuse":
            existing_data = existing.issues
            print(f"[SKIP] {display_name} - already has results ({len(existing_data)} issues)")
            # Stage U: the result is reused, so what it cost is reused with
            # it. Nothing else can refill this entry: no adapter runs for a
            # skipped slot.
            if usage is not None:
                spent = (prior_usage or {}).get(model_spec)
                if isinstance(spent, dict) and spent:
                    usage[model_spec] = spent
            # Terminal the moment it is seeded (`attempt: 0`, `elapsed_s: 0`),
            # counted in `models_done` and `models_succeeded`; the renderer
            # labels the row from `source in RESUME_SOURCES`.
            return _review_lane.SlotResult(
                model_spec, True, payload=existing_data, source="existing_file",
            )
        return None

    async def review_slot(model_spec: str, index: int) -> _review_lane.SlotResult:
        # The slot's terminal transitions sit at `run_single_review`'s own
        # completion and failure sites, where the reason and the `source` are
        # known; the fan-out's `record_result` behind them is then a no-op.
        try:
            result = await run_single_review(
                model_spec, plan_path, out_dir, timeout, changed_files,
                base_ref, served_models=served_models, usage=usage,
                tracker=tracker, scope_source=scope_source,
                task_ids=task_ids, scope_file=scope_file,
                diff_dir=diff_dir, scope_id=scope_id,
                diff_coverage=diff_coverage,
                run_model_specs=list(model_specs),
                **pinned_kwargs,
                **scope_kwargs,
            )
        except Exception as exc:
            # An exception IS this slot's ending, recorded with its own text
            # as on the review base's lane; re-raised, the gather would drop
            # it and `backfill_deadline_losses` would call it a deadline loss.
            return _review_lane.SlotResult.from_record(
                model_spec, raised_slot_record(model_spec, exc, anchor=str(plan_path)),
            )
        return _review_lane.SlotResult.coerce(model_spec, result)

    # The concurrency mechanics are the base fan-out's, shared by both review
    # lanes (utils/review_lane.py): the semaphores (a provider's before the
    # global one), the launch spacing, the seeded map, the overall deadline
    # that harvests finished slots before it cancels the rest, and the
    # ticker's teardown and sweep in its `finally`.
    slots = await run_models_concurrent(
        model_specs, review_slot, timeout, max_parallel,
        skip_predicate=skip_existing_result,
        anchor=str(plan_path),
        tracker=tracker,
    )
    return {spec: slot.as_review() for spec, slot in slots.items()}


def generate_review_report(
    plan_path: Path,
    results: Dict[str, Tuple[bool, Optional[List[Dict]], Optional[str]]],
    changed_files: List[str],
    validated_groups: Optional[List[Dict]] = None,
    phase_dir: Optional[Path] = None,
    base_ref: Optional[str] = None,
    template_style: str = 'pr',
    served_models: Optional[Dict[str, Dict[str, Any]]] = None,
    usage: Optional[Dict[str, Dict[str, Any]]] = None,
    failed_models: Optional[Dict[str, str]] = None,
    requested_models: Optional[int] = None,
    commit_review: Optional[Dict[str, Any]] = None,
    review_scope: Optional[Dict[str, Any]] = None,
    pinned: Optional[PinnedRange] = None,
    repo_root: Optional[str] = None,
    scope_state: Optional[Dict[str, Any]] = None,
) -> str:
    """Generate a markdown review report.

    ``scope_state`` is the ``state.json`` dict holding the review round's
    ``scope_policy`` record;
    ``None`` reads the saved one beside *phase_dir*. Each issue shows its own
    provisional scope tag and its group's validated one, and the header the
    effective policy and the tag counts over distinct groups.

    ``pinned`` (a review pinned to two commits) hands the HTML report the
    head commit and *repo_root*: its hunks are ``base..head``, its context is
    the files as ``head`` holds them, never the disk, and a path absent at
    ``head`` carries its label (:func:`pinned_report_kwargs`).

    ``review_scope`` is :func:`review_scope_record`'s account of the scope
    manifest the reviewers were pointed at (review-scope plan D2.2): rendered
    as the ``**Review scope:**`` / ``**Diff coverage:**`` header lines and
    added to ``report_data.json`` as ``reviewScope`` and ``diffCoverage``.
    ``None`` (a direct call) adds neither.

    ``served_models`` is the attribution
    (``{model_spec: {"served_model", "fallback"}}``): every row that names a
    model — the ``**Models:**`` summary, each issue's ``**Model:**`` field and
    the HTML report's badges — names the model that actually served the turn
    instead of silently crediting the primary. Empty (the shipped default, since
    ``fallback_models`` ships empty) leaves the report byte-for-byte what it was.

    ``usage`` is ``{model_spec: usage}`` for the slots whose adapter reported
    what they spent. It renders on the ``**Models:**`` summary line and on the
    HTML badges — the two surfaces that name each model once — and nowhere
    per issue, because a cost repeated under every finding is noise. Empty for
    a fan-out of duration-only adapters, which leaves the report as it was.

    ``commit_review`` is a commit review's report payload
    (:func:`utils.commit_report.report_context`): the header labels the brief "Commit
    brief" and carries the commit
    block with the focus and context plan under it, each finding whose group
    was attributed gets an "Introduced by" line, and the HTML report gets the
    commit filter, the drift badges and the apply command its export help
    names. ``None`` (every plan's review) leaves the report as it was.

    ``failed_models`` is the caller's authoritative failure map (model ->
    reason): main()'s post-salvage map, including any model F11 seeded for
    never returning at all, or the reaggregate's read-back of
    ``.status.json.models_failed`` plus every requested model with neither a
    result file nor a recorded failure (``remaining_failed_models``) — the
    reaggregate's ``results`` holds only models with a file, so deriving the
    map from it named no failure at all. A caller with no map of its own (a
    fixture exercising this function directly) gets one derived from
    ``results`` on ``success`` alone (F10).

    Whatever the map holds is named on a ``**Models failed:**`` line directly
    under ``**Models:**`` (``failed_models_line``: "N of M requested" when
    ``requested_models`` is given, and the salvage clause for a model this
    attempt asked a salvage of, ``salvage_requested_models``), in the HTML
    report's warning notice and failure row from the same inputs, and in the
    ``## Failed Reviews`` section at the bottom. ``requested_models`` is the
    size of the requested set — main()'s ``len(model_specs)``, the
    reaggregate's recorded requested set — never succeeded plus failed.
    """
    # "Commit brief", never "Plan", for a commit review, through the
    # one owner of the word.
    document = (
        commit_review.get("documentLabel") if commit_review
        else commit_report.label_title(None)
    )
    lines = [
        # Model text below is escaped; the parser un-escapes descriptions
        # only under this first line (`report_markdown.has_escaped_text`).
        # The round line goes under it at publication
        # (`review_round.publish_report`).
        report_markdown.ESCAPED_TEXT_MARKER,
        "# Code Review Report",
        "",
        f"**{document}:** {plan_path.name}",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Files Changed:** {len(changed_files)}",
        "",
    ]
    if commit_review:
        lines.extend(commit_report.report_header_lines(commit_review))

    # Collect all issues
    all_issues = []
    successful_models = []
    # F10: `success and issues` misclassified a reviewer that legitimately
    # returned `[]` as failed — it was listed under "## Failed Reviews" as
    # "No issues returned" even though `save_model_result` had already
    # written its (empty) result file and `.status.json.models_completed`
    # already counted it done. Testing `success` alone, on the caller's
    # authoritative map when it has one.
    if failed_models is None:
        failed_models = {
            model: (error or "No issues returned")
            for model, (success, issues, error) in results.items()
            if not success
        }
    for model, (success, issues, error) in results.items():
        if success:
            successful_models.append(model)
            # `drop_non_record_entries` because `issue["model"] = model` is an
            # item assignment: one non-dict element used to raise TypeError here
            # and lose every model's findings, not just this model's.
            for issue in drop_non_record_entries(issues, model, noun="issues"):
                issue["model"] = model
                all_issues.append(issue)

    lines.append(
        "**Models:** "
        + ", ".join(model_label(m, served_models, usage) for m in successful_models)
    )
    #  T5.2: the models that produced nothing, directly under the ones
    # that did (the bottom `## Failed Reviews` section alone left a lost
    # reviewer below the fold). The salvage answer is computed once and handed
    # to the HTML report too, so the notice there is this line minus its bold.
    salvage_requested = salvage_requested_models(
        str(phase_dir) if phase_dir is not None else None, list(failed_models)
    )
    # A jail-denied slot's `models_served` entry makes the line say "denied by
    # the plugin's jail: <path>".
    failure_line = failed_models_line(
        failed_models, requested_models, salvage_requested,
        served_models=served_models,
    )
    if failure_line:
        lines.append(failure_line)
    # A result file read from under the wrong name, or set aside as no
    # recorded model's (`utils/result_files.py`); absent when neither happened.
    result_files_line = _result_files.result_notes_line(phase_dir)
    if result_files_line:
        lines.append(result_files_line)
    lines.append(f"**Total Issues:** {len(all_issues)}")

    # The blocks below are per issue (one per model finding) but every count
    # downstream of grouping — the validation line, grouped.json, report.html's
    # summary — is per group, so say how many groups there are and which count
    # is which. Without this the header read "12 issues, 7 valid, 1 invalid,
    # 1 needs human review" and nothing reconciled 12 with 7+1+1.
    if validated_groups:
        lines.append(
            f"**Groups:** {len(validated_groups)} "
            "(issues that report the same finding are one group; `group_index` "
            "in the JSON files counts from 0)"
        )

    # Add validation summary if available. T6.1: the four counts come from
    # the base's `validation_counts`, the same helper that records them on the
    # result line below, so a `validation_failed` group shows here too and the
    # header and payload agree.
    if validated_groups:
        counts = validation_counts(validated_groups) or {
            key: 0 for key in VALIDATION_COUNT_KEYS.values()
        }
        lines.append(
            f"**Validation:** {counts['valid']} valid, {counts['invalid']} invalid, "
            f"{counts['needs_human_decision']} needs human review, "
            f"{counts['validation_failed']} validation failed "
            f"(of {len(validated_groups)} groups)"
        )
    if phase_dir is not None:
        record_validation_counts(str(phase_dir), validated_groups)
    # The published `validation_context`, read from `.status.json`
    # and never recomputed; absent adds nothing, so the report is unchanged.
    if phase_dir is not None:
        lines.extend(
            report_header_lines(
                read_status(str(phase_dir)).get("validation_context")
            )
        )
    # Review-scope plan D2.2: the manifest and per-file diffs the reviewers
    # were pointed at, their coverage, and any result that reviewed another set.
    lines.extend(review_scope_report_lines(review_scope))
    # Scope tags: the round's
    # effective policy and the tag counts over distinct groups, never over the
    # issue rows below (a consensus finding is one row per model).
    if scope_state is None:
        scope_state = _scope_report.read_state(phase_dir)
    scope_round = _scope_report.round_info(scope_state, "code-review", validated_groups or [])
    group_scopes = [
        (str(g.get("group_hash") or ""), _scope_report.group_scope(g, scope_round))
        for g in validated_groups or []
    ]
    lines.extend(_scope_report.md_header_lines(
        scope_round, _scope_report.count_entries(group_scopes)))
    lines.append("")

    lines.append("> **Note:** An interactive HTML report is also available at `report.html`.")
    lines.append("> If you export selections from the HTML report (`user_selections.json`),")
    lines.append("> those selections will take precedence over checkboxes in this file.")
    if validated_groups:
        lines.append("> Checkboxes act on the whole group: marking one issue marks every")
        lines.append("> issue listed as the same finding, because there is one fix between them.")
    lines.append(_scope_report.md_legend_line())
    lines.append("")

    # Build validation info lookup from validated_groups
    # Map (title, file) -> {status, reason} for correlation
    validation_lookup: Dict[Tuple[str, str], Dict[str, str]] = {}
    if validated_groups:
        for group in validated_groups:
            status = group.get("validation_status")
            reason = group.get("validation_reason", "")
            if status:
                info = {"status": status, "reason": reason}
                # Try to match by theme/title and file
                theme = group.get("theme", "")
                title = group.get("title", "")
                file_path = group.get("file", "")

                # Also look in suggestions for individual issue data
                suggestions = group.get("suggestions", [])
                for sugg in suggestions:
                    if isinstance(sugg, dict):
                        sugg_title = sugg.get("title", title or theme)
                        sugg_file = sugg.get("file", file_path)
                        if sugg_title:
                            validation_lookup[(sugg_title, sugg_file)] = info

                # Also store by theme/title directly
                if theme:
                    validation_lookup[(theme, file_path)] = info
                if title:
                    validation_lookup[(title, file_path)] = info

    def get_validation_info(issue: Dict) -> Tuple[Optional[str], Optional[str]]:
        """Look up validation status and reason for an issue."""
        title = issue.get("title", "")
        file_path = issue.get("file", "")
        # Try exact match first
        if (title, file_path) in validation_lookup:
            info = validation_lookup[(title, file_path)]
            return info.get("status"), info.get("reason")
        # Try with empty file
        if (title, "") in validation_lookup:
            info = validation_lookup[(title, "")]
            return info.get("status"), info.get("reason")
        return None, None

    # Build issue-to-global-index mapping (matches grouped.json order)
    issue_global_index = {}
    for idx, issue in enumerate(all_issues, 1):
        issue_global_index[id(issue)] = idx

    # Which group each numbered issue belongs to, and who its siblings are.
    # The same matcher the apply phase's issue->group map uses, so the report
    # and the checkbox contract agree — including on a word-identical finding
    # in two files, which is two groups and must not read "Same finding as".
    issue_siblings: Dict[int, List[int]] = {}   # id(issue) -> other issue numbers
    issue_group_models: Dict[int, int] = {}     # id(issue) -> models in its group
    if validated_groups:
        placement = match_issues_to_suggestions(all_issues, validated_groups)
        members: Dict[int, List[Dict]] = {}
        for idx, issue in enumerate(all_issues, 1):
            location = placement.get(idx)
            if location:
                members.setdefault(location[0], []).append(issue)
        for group_issues in members.values():
            if len(group_issues) < 2:
                continue
            model_count = len({i.get("model", "") for i in group_issues if i.get("model")})
            numbers = [issue_global_index[id(i)] for i in group_issues]
            for issue in group_issues:
                mine = issue_global_index[id(issue)]
                issue_siblings[id(issue)] = [n for n in sorted(numbers) if n != mine]
                issue_group_models[id(issue)] = model_count

    # Each finding names the commit its group was attributed to
    # (`introduced_by`, decided by `utils/commit_attribution.py`), with the
    # subject from `commit_range.commits`; an unattributed one shows nothing.
    issue_introduced: Dict[int, str] = {}
    if commit_review and validated_groups:
        commit_placement = match_issues_to_suggestions(all_issues, validated_groups)
        for idx, issue in enumerate(all_issues, 1):
            location = commit_placement.get(idx)
            if not location or not 0 < location[0] <= len(validated_groups):
                continue
            introduced = commit_report.group_introduced_by_line(
                validated_groups[location[0] - 1], commit_review
            )
            if introduced:
                issue_introduced[id(issue)] = introduced

    # Each numbered issue's group scope entry: every member of a group shows
    # the group's one validated tag, as it shows the group's one verdict.
    issue_scope: Dict[int, Dict[str, Any]] = {}
    if validated_groups:
        scope_placement = match_issues_to_suggestions(all_issues, validated_groups)
        for idx, issue in enumerate(all_issues, 1):
            location = scope_placement.get(idx)
            if location and 0 < location[0] <= len(group_scopes):
                issue_scope[id(issue)] = group_scopes[location[0] - 1][1]

    # Group by importance, read in either case; a value naming no level is
    # MEDIUM (`utils/importance.py`), so every counted issue lands in a section.
    high = [i for i in all_issues if _importance.normalize(i.get("importance")) == "HIGH"]
    medium = [i for i in all_issues if _importance.normalize(i.get("importance")) == "MEDIUM"]
    low = [i for i in all_issues if _importance.normalize(i.get("importance")) == "LOW"]

    def _issue_sort_key(issue):
        status, _ = get_validation_info(issue)
        return (
            VALIDATION_ORDER.get(status or "", UNKNOWN_STATUS_RANK),
            issue_global_index.get(id(issue), 0),
        )

    high.sort(key=_issue_sort_key)
    medium.sort(key=_issue_sort_key)
    low.sort(key=_issue_sort_key)

    # HIGH issues
    lines.append("## HIGH Priority")
    lines.append("")
    if high:
        for issue in high:
            status, reason = get_validation_info(issue)
            lines.extend(_format_issue(
                issue_global_index[id(issue)], issue,
                validation_status=status, validation_reason=reason,
                served_models=served_models,
                siblings=issue_siblings.get(id(issue)),
                group_model_count=issue_group_models.get(id(issue), 0),
                introduced_by=issue_introduced.get(id(issue)),
                group_scope=issue_scope.get(id(issue)),
            ))
    else:
        lines.append("_No high priority issues._")
        lines.append("")

    # MEDIUM issues
    lines.append("## MEDIUM Priority")
    lines.append("")
    if medium:
        for issue in medium:
            status, reason = get_validation_info(issue)
            lines.extend(_format_issue(
                issue_global_index[id(issue)], issue,
                validation_status=status, validation_reason=reason,
                served_models=served_models,
                siblings=issue_siblings.get(id(issue)),
                group_model_count=issue_group_models.get(id(issue), 0),
                introduced_by=issue_introduced.get(id(issue)),
                group_scope=issue_scope.get(id(issue)),
            ))
    else:
        lines.append("_No medium priority issues._")
        lines.append("")

    # LOW issues
    lines.append("## LOW Priority")
    lines.append("")
    if low:
        for issue in low:
            status, reason = get_validation_info(issue)
            lines.extend(_format_issue(
                issue_global_index[id(issue)], issue,
                validation_status=status, validation_reason=reason,
                served_models=served_models,
                siblings=issue_siblings.get(id(issue)),
                group_model_count=issue_group_models.get(id(issue), 0),
                introduced_by=issue_introduced.get(id(issue)),
                group_scope=issue_scope.get(id(issue)),
            ))
    else:
        lines.append("_No low priority issues._")
        lines.append("")

    # Everything below sits inside the last issue's block, so a path, a
    # failure message or a validator's reason is written inert
    # (`report_markdown`): none of it may read as a header or a ticked box.
    # Changed files list
    lines.append("## Changed Files")
    lines.append("")
    for f in changed_files:
        lines.append(f"- `{report_markdown.inline_text(f)}`")
    lines.append("")

    # Failed models
    if failed_models:
        lines.append("## Failed Reviews")
        lines.append("")
        for model, error in failed_models.items():
            lines.append(
                f"- **{report_markdown.inline_text(model)}**: "
                f"{report_markdown.neutralize_model_text(error)}"
            )
        lines.append("")

    # Add section for items needing human review
    if validated_groups:
        needs_human = [g for g in validated_groups if g.get("validation_status") == "needs-human-decision"]
        if needs_human:
            lines.append("## Needs Human Review")
            lines.append("")
            lines.append("The following issues require human judgment:")
            lines.append("")
            for g in needs_human:
                theme = g.get("theme", "Unknown issue")
                reason = g.get("validation_reason", "No reason provided")
                lines.append(
                    f"- **{report_markdown.inline_text(theme)}**: "
                    f"{report_markdown.neutralize_model_text(reason)}"
                )
            lines.append("")

    # The binding between the `### N.` numbers above and the issues.json the
    # apply phase resolves them against (`build_issue_to_group_map` reads a
    # number as a POSITION in that file). A footer comment, so it renders as
    # nothing and leaves every parser of this report reading what it read
    # before; `apply-code-fixes` warns when it no longer matches.
    lines.append(issue_numbering_footer(all_issues))
    lines.append("")

    # Generate HTML report if phase_dir provided
    if phase_dir:
        try:
            html_content = generate_html_report(
                groups=validated_groups or [],
                plan_path=plan_path,
                # The commit header, filter, badges and export help.
                commit_review=commit_review,
                phase_dir=phase_dir,
                phase_type="code-review",
                models=successful_models,
                failed_models=failed_models,
                base_ref=base_ref,
                template_style=template_style,
                served_models=served_models,
                usage=usage,
                requested_models=requested_models,
                salvage_requested=salvage_requested,
                scope_state=scope_state,
                **pinned_report_kwargs(validated_groups or [], pinned, repo_root),
            )
            write_html_report(html_content, phase_dir)
            print(f"HTML report written to: {phase_dir / 'report.html'}")
        except Exception as e:
            print(f"Warning: Failed to generate HTML report: {e}")
        # D2.2: `diffCoverage` and `reviewScope`, beside what the page shows.
        record_review_scope_in_report_data(phase_dir, review_scope)

    return "\n".join(lines)


def pinned_report_kwargs(
    groups: List[Any], pinned: Optional[PinnedRange], repo_root: Optional[str],
) -> Dict[str, Any]:
    """``generate_html_report``'s pinned-review keywords; ``{}`` when unpinned.

    ``head_ref`` and ``repo_root`` (the report reads its hunks and snapshots at
    the head commit), and ``file_labels``: for each cited file absent at
    ``head``, the label its validation excerpt carries (``deleted in
    <range>``, ``renamed to <new> in <range>``, ``absent at <head7>``).
    """
    if pinned is None:
        return {}
    files = sorted({
        str(suggestion.get("file")).strip()
        for group in groups
        for suggestion in (
            (group.to_dict() if hasattr(group, "to_dict") else group).get("suggestions")
            or []
        )
        if isinstance(suggestion, dict) and suggestion.get("file")
    })
    names = {path: pinned_git_name(path) for path in files}
    asked = sorted({name for name in names.values() if name})
    labels: Dict[str, str] = {}
    present = paths_in_commit(pinned.head, asked, cwd=repo_root) if asked else set()
    if present is not None:
        kinds = absent_at_head(
            [name for name in asked if name not in present], pinned, cwd=repo_root,
        )
        for path, name in names.items():
            if name in kinds:
                labels[path] = absent_label(*kinds[name], pinned)
    return {"head_ref": pinned.head, "repo_root": repo_root, "file_labels": labels}


def _format_issue(
    index: int,
    issue: Dict,
    validation_status: Optional[str] = None,
    validation_reason: Optional[str] = None,
    served_models: Optional[Dict[str, Dict[str, Any]]] = None,
    siblings: Optional[List[int]] = None,
    group_model_count: int = 0,
    introduced_by: Optional[str] = None,
    group_scope: Optional[Dict[str, Any]] = None,
) -> List[str]:
    """Format a single issue for the report.

    Args:
        index: The issue number for display
        issue: The issue dict with title, desc, type, file, model, etc.
        validation_status: The validation status (valid, invalid, needs-human-decision, etc.)
        validation_reason: The reason for the validation decision (shown for invalid/needs-human-decision)
        served_models: Optional attribution.  The ``**Model:**`` field is
            the one place this report credits a finding to a model, so a slot
            served by a configured fallback is named here too — otherwise the
            row reads as if the primary produced it.
        siblings: Issue numbers of the other members of this issue's group.
            A consensus finding is rendered once per model, so without this
            line the same bug reads as three unrelated findings with three
            checkboxes — and the verdict shown on each is the *group's* one
            verdict, which is why the badge says so when there are siblings.
        group_model_count: Distinct models behind this issue's group, for the
            agreement phrase.
        introduced_by: A commit review's "Introduced by `<sha7>` — <subject>"
            line for this issue's group. It
            sits above the metadata line, so the description the parser reads
            after that line is unchanged, and its subject is escaped so it
            cannot pass for a checkbox.
        group_scope: The issue's group scope entry
            (``scope_report.group_scope``): its validated tag and, under
            ``preserve``, its policy outcome. The issue's own provisional tag
            is always shown. Both sit above the metadata line, so
            ``report_parser.parse_issue_descriptions`` reads the same
            description as before.
    """
    # Both normalised on arrival (`normalize_issue_shapes`); a caller that
    # hands raw model output still gets a location, never an IndexError.
    file_ref = str(issue.get("file") or "unknown")
    line_range = _usable_line_range(issue.get("line_range"))
    if line_range:
        file_ref += f":{line_range[0]}-{line_range[1]}"

    # Build explicit validation status string
    validation_display = {
        "valid": "Valid",
        "invalid": "Invalid",
        "needs-human-decision": "? Needs Review",
        "validation_failed": "? Validation Failed",
    }
    validation_str = validation_display.get(validation_status, "? Unknown") if validation_status else "? Unknown"
    if siblings and validation_status:
        validation_str += " (group verdict)"

    # The header and the Skip box are one unit to `report_parser`: it reads the
    # checkbox off the line *immediately* after `### N.`. A title is model
    # output and can hold a newline, which pushes the box a line further down
    # and loses the tick with no warning — so `issue_header` flattens the title
    # onto its own line rather than the parser being taught to hunt for the
    # box. The other model text below is one line or escaped line by line
    # (`report_markdown`), so it can forge neither a header nor a box.
    rm = report_markdown
    lines = [
        rm.issue_header(index, issue.get("title", "Untitled")),
        rm.checkbox_line(rm.SKIP),
    ]

    # Add override checkboxes for items needing human review
    if validation_status in ("needs-human-decision", "validation_failed"):
        lines.append(rm.checkbox_line(rm.MARK_VALID))
        lines.append(rm.checkbox_line(rm.MARK_INVALID))
    # "Let the agent decide" routes this issue to the per-item judge at apply time.
    # Scoped to needs-human-decision only.
    if validation_status == "needs-human-decision":
        lines.append(rm.checkbox_line(rm.LET_AGENT_DECIDE))

    # Name the other members of this issue's group. One finding, one verdict,
    # one fix — and one checkbox between them, whichever block it is ticked on.
    if siblings:
        refs = ", ".join(f"#{n}" for n in siblings)
        agreement = (
            f"{group_model_count} models agree"
            if group_model_count > 1
            else f"{len(siblings) + 1} findings grouped"
        )
        lines.append(f"_Same finding as {refs} ({agreement}); marking any marks all._")

    if introduced_by:
        lines.append(introduced_by)

    lines.append(_scope_report.md_member_line(issue))
    if group_scope is not None:
        lines.extend(_scope_report.md_group_lines(group_scope))

    lines.extend([
        f"**Validation:** {validation_str} | **File:** `{rm.inline_text(file_ref)}` | **Type:** {rm.inline_text(issue.get('type', 'unknown'))} | **Model:** {rm.inline_text(served_model_label(issue.get('model', 'unknown'), served_models))}",
        "",
    ])

    # Include validation reason for invalid or needs-human-decision issues.
    # Every line of it is quoted, so a reason of several paragraphs, or one
    # holding a `---` line, stays out of the description the apply phase reads
    # back (`report_parser.parse_issue_descriptions`).
    if validation_reason and validation_status in ("invalid", "needs-human-decision", "validation_failed"):
        first, *rest = rm.neutralize_model_text(validation_reason).split("\n")
        lines.append(f"> **Validation Reason:** {first}")
        lines.extend(f"> {line}".rstrip() for line in rest)
        lines.append("")

    lines.extend([
        rm.neutralize_model_text(issue.get("desc", "No description")),
        "",
        "---",
        "",
    ])
    return lines


def pinned_provenance(
    pinned: Optional[PinnedRange],
    plan_snapshot: Optional[str],
    plan_sha256: Optional[str],
    repo_root: Optional[str] = None,
) -> Dict[str, Any]:
    """:class:`RoundProvenance`'s pinned fields; ``{}`` when the review is
    neither pinned nor carries a frozen context plan."""
    kwargs: Dict[str, Any] = {}
    if pinned is not None:
        kwargs["head_ref"] = pinned.head
    if plan_snapshot and plan_sha256:
        kwargs["context_plan_sha256"] = plan_sha256
        kwargs["context_plan_file"] = os.path.join(repo_root or os.getcwd(), plan_snapshot)
    return kwargs


def code_review_validation_round(
    groups: List[Dict[str, Any]],
    *,
    args: argparse.Namespace,
    plan_path: Path,
    phase_dir: Path,
    plan_document: BoundDocument,
    base_ref: str,
    project_root: Optional[str],
    git_root: Optional[str],
    pinned: Optional[PinnedRange],
    plan_snapshot: Optional[str],
    plan_sha256: Optional[str],
    scope_round_policy: Any,
    state: Any,
    round_id: Optional[str] = None,
) -> ValidationRound:
    """The validation round review-code materializes, after its fan-out and on
    ``--reaggregate``: one builder, so a reaggregate re-validates against the
    prompt the fan-out wrote.

    The plan block is the bound snapshot, with no ``Plan file:``
    line: a second path, the live plan, would point a validator at bytes the
    snapshot hash does not cover. The second block is the reviewed code, each
    batch embedding the windows its own issues cite, from one read.
    *round_id* is the materializing invocation's claim (utils/review_round.py).
    """
    guidance = pinned_guidance_kwargs(pinned, plan_snapshot, plan_sha256)
    cut_report: Dict[str, Any] = {}
    per_batch: Dict[str, Any] = {}
    secondary, reviewed_code = build_validation_secondary_context(
        groups, plan_path, project_root=project_root,
        cut_report=cut_report, per_batch=per_batch,
        **({"pinned": pinned} if pinned is not None else {}),
    )
    provenance = RoundProvenance(
        model=args.validation_model,
        orchestrator="code_review_orchestrator.py",
        phase="code-review",
        base_ref=base_ref,
        **pinned_provenance(pinned, plan_snapshot, plan_sha256, git_root),
        # The materializing invocation's own round, captured once: the
        # fan-out's, or on a `--reaggregate` the round it continues
        # (utils/review_round.py), never a re-read of the checkpoint.
        round_id=round_id,
    )
    # The guidance, plus the dropped files to open when the reviewed-code
    # block lost any (T7.4), outside every block a context budget can cut.
    extra_instructions = validation_extra_instructions(cut_report, **guidance)
    secondary_block = ContextBlock(
        secondary, REVIEWED_CODE_CONTEXT_LABEL,
        reviewed_code_document(secondary, cut_report),
    )
    batch_view = reviewed_code_batch_view(per_batch, **guidance)
    read_refusal = materialization_read_refusal(args, str(plan_path))
    recorded = getattr(state, "state", {}) or {}
    # The reviewers' policy and baseline, in the one task file
    # both invokers run.
    scope = validation_scope_block(
        "code-review", scope_round_policy, state,
        _scope_round.round_baseline(recorded, "code-review"),
        plan_document=plan_document,
        commit_review=isinstance(recorded.get("commit_range"), dict),
    )
    return ValidationRound(
        groups=groups,
        output_dir=str(phase_dir),
        plan_file=str(plan_path),
        primary=ContextBlock(plan_document.text, PLAN_CONTEXT_LABEL, plan_document),
        secondary=secondary_block,
        secondary_for_batch=batch_view,
        reviewed_code=reviewed_code,
        extra_instructions=extra_instructions,
        scope=scope,
        runner_read_refusal=read_refusal,
        provenance=provenance,
    )


def pinned_guidance_kwargs(
    pinned: Optional[PinnedRange],
    plan_snapshot: Optional[str],
    plan_sha256: Optional[str],
) -> Dict[str, Any]:
    """:func:`validation_extra_instructions`' pinned keywords; ``{}`` when
    there is nothing to pin, so the unpinned call is unchanged."""
    kwargs: Dict[str, Any] = {}
    if pinned is not None:
        kwargs["pinned"] = pinned
    if plan_snapshot:
        kwargs["plan_snapshot"] = plan_snapshot
        kwargs["plan_sha256"] = plan_sha256
    return kwargs


async def reaggregate_from_existing_files(
    prefix: str,
    out_dir: Path,
    plan_path: Path,
    args: argparse.Namespace,
    template_style: str = 'pr',
    base_ref: Optional[str] = None,
    pinned: Optional[PinnedRange] = None,
) -> int:
    """Re-aggregate all model results after salvage operations complete.

    This function scans the output directory for model result files (including
    salvaged ones) and re-runs grouping, validation, and report generation.

    Args:
        prefix: Output file prefix
        out_dir: Output directory containing model results
        plan_path: Path to the plan file
        args: Command-line arguments for validation settings
        template_style: Template to use — ``'pr'`` or ``'flat'``.
            Defaults to ``'pr'``.
        base_ref: Optional explicit base git ref for diff context.
            When provided, takes priority over ``args.base_ref`` and
            the state's ``head_at_start``.
        pinned: The review on record's two commits (``commit_range`` or
            ``head_ref``, :func:`resolve_pinned_range`, resolved by ``main``
            before anything was written). The base is then that pair's, never
            ``head_before_implement``/``head_at_start``/``HEAD~1``; the scope,
            a regenerated diff set, the validation excerpts and the report are
            all read at its head, so ``reviewed_code_sha256`` is stable however
            the working tree moved.

    Returns:
        The process exit code: :func:`finish_code_review`'s on a completed
        phase (``--fail-on-high`` holds there), ``EXIT_OK`` on every ending
        that leaves the phase open. Refusals ``sys.exit`` themselves.
    """
    # Find all model result files in the code-review phase directory
    phase_dir = get_phase_dir(plan_path, 'code-review')
    # The round on record, captured once: everything this reaggregate writes
    # records it and is published only while the checkpoint still does. A task
    # file or validation.json of another round is refused before anything is
    # touched (utils/review_round.py, the check every orchestrator shares).
    claim = _review_round.continue_round(phase_dir)
    _review_round.refuse_foreign_round(claim, commit_spelling.spell_retry_command(
        "review-code", plan_path, "--force",
        flags=cli_common.current_replay_flags(mode="review-code"),
    ))
    lane = CodeLane(plan_path=plan_path, phase_dir=phase_dir, prefix=prefix)
    steps = lane.round_steps()
    # The result files a reaggregate reads, one rule for every review lane
    # (utils/review_lane.py); none at all is exit 3 when every requested
    # reviewer failed, else exit 0.
    result_files = _review_lane.reaggregate_result_files(
        steps, mode="review-code", phase_dir=str(phase_dir), plan_path=str(plan_path),
    )
    if result_files is None:
        return EXIT_OK

    def unattributed() -> None:
        # A checkpoint that records no models (no `.status.json`, an
        # unreadable one, or one without the fields; `build_unsanitize_map`'s
        # result, not the file's existence): every group from here on is
        # attributed to a stem that no longer names a model, which on the
        # `--skip-validation` leg completes and writes a report that nothing
        # downstream contradicts. Said, and the reaggregation goes on.
        warn_stem_attribution(
            f"WARNING: {phase_dir} holds {len(result_files)} model result "
            f"file(s), but its checkpoint records no models_requested — either "
            f"no .status.json at all, or one that never got the field. This "
            f"reaggregation continues."
        )

    def stamp(issues: List[Dict[str, Any]], model: str) -> None:
        # `model` before `source_model`, the order the fan-out stamps them in:
        # `SuggestionGroup.to_dict` carries a suggestion's dict through
        # unreordered, `json.dump` keeps that order and `grouped_sha256` hashes
        # the file's bytes, so the other order moved grouped.json's bytes and
        # made the task file refuse its own round.
        for issue in issues:
            issue["model"] = model            # report generation reads this one
            issue["source_model"] = model     # grouping attributes by this one
        # A salvage or an older run wrote whichever case it was given.
        _importance.canonicalize(issues)
        # Read back in the shapes the fan-out grouped (normalize_issue_shapes).
        normalize_issue_shapes(issues, model)

    # Every model's issues read back, one rule for every review lane: the
    # canonical specs from the checkpoint, one file per logical model (W3),
    # non-record entries dropped before anything is stamped, a model with a
    # file reconciled as completed and the failures left named. No readable
    # result at all ends here, its verdict counts cleared.
    loaded = _review_lane.load_reaggregate_results(
        steps, result_files, mode="review-code", phase_dir=str(phase_dir),
        plan_path=str(plan_path), noun="issues", stamp=stamp,
        on_unattributed=unattributed,
    )
    if loaded is None:
        return EXIT_OK
    all_issues = loaded.records
    # Each model's result file stem, for the scope-ledger check (D2.2).
    result_stems = loaded.stems
    # The report's per-model rows: `results` holds only the models with a
    # file, so it has no failures of its own to report.
    results: Dict[str, Tuple[bool, Optional[List[Dict]], Optional[str]]] = {
        model: (True, issues, None) for model, issues in loaded.by_model.items()
    }
    failed_models_map, requested_set = loaded.failed_models, loaded.requested

    # Get changed files from state (or empty list if not available)
    state = get_or_create_state(plan_path)

    # The root an issue's relative `file` is resolved against when the
    # validation prompt embeds the code at the lines it cites.
    project_root = get_project_root(str(plan_path))

    # Resolve base_ref for validation context.
    # Priority: the pinned pair on record > explicit parameter > args.base_ref
    # > state head_before_implement > head_at_start > fallback
    if pinned is not None:
        base_ref = pinned.base_ref
        print(
            f"Git base reference: {base_ref} (the review on record is "
            f"{pinned.display}, head {pinned.head})"
        )
    else:
        if base_ref is None:
            args_base_ref = getattr(args, 'base_ref', None)
            state_base_ref = state.get('head_before_implement') or state.get('head_at_start')
            if args_base_ref:
                base_ref = args_base_ref
            elif state_base_ref:
                base_ref = state_base_ref
            else:
                base_ref = 'HEAD~1'
                print(
                    "Warning: head_at_start not found in state; falling back to HEAD~1. "
                    "This may produce incorrect diffs if the branch has advanced since "
                    "the original review.",
                    file=sys.stderr,
                )
        base_ref = validate_git_ref(base_ref)
    pinned_kw: Dict[str, Any] = {"pinned": pinned} if pinned is not None else {}
    plan_snapshot, plan_sha256 = _context_plan(getattr(state, "state", None))
    # A reaggregate belongs to the round on record: its policy and
    # baseline stay; a differing explicit policy was refused before the
    # boundary and is refused here too for a direct caller.
    scope_round_policy = resolve_scope_round(
        state, "code-review", args, same_round=True, phase_dir=str(phase_dir),
    )

    # The fan-out's own resolution (`resolve_review_scope`, the same printed
    # lines), kept whole because a regenerated scope manifest names its source
    # (D2.2).
    # The scope is root-relative, so its git calls run at the root, never at a
    # subdirectory the command happened to be invoked from.
    git_root = review_git_root(project_root)
    reaggregate_scope = resolve_review_scope(
        state, base_ref, anchor=str(plan_path), repo_root=git_root,
        **({"head_ref": pinned.head} if pinned is not None else {}),
    )
    changed_files = reaggregate_scope.paths
    print(f"Files to review: {len(changed_files)}")
    if pinned is not None:
        pinned = pinned._replace(
            not_in_range=reaggregate_scope.not_in_range,
            narrowed=reaggregate_scope.narrowed,
        )
        pinned_kw = {"pinned": pinned}

    # Two commits need no intent-to-add marking: the working tree is not in
    # their diff.
    with (
        contextlib.nullcontext() if pinned is not None
        else intent_to_add_untracked(changed_files, cwd=git_root)
    ):
        # The scope the loaded results reviewed (D2.2): read back from the
        # fan-out's manifest, or — when the pair is missing or incomplete —
        # regenerated from the current tree, inside this block so a new file's
        # intent-to-add entry is visible to `git diff`. Never touches a whole
        # pair, and names each result the scope ledger ties to another set.
        scope_record = reaggregate_review_scope(
            phase_dir, plan_path, base_ref, changed_files,
            reaggregate_scope.source, result_stems, repo_root=git_root,
            **pinned_kw,
        )

        # Save raw issues as JSON
        issues_path = get_output_paths(plan_path, "code_review_issues", phase='code-review')
        issues_path = issues_path.with_suffix(".json")
        with open(issues_path, "w", encoding="utf-8") as f:
            json.dump(all_issues, f, indent=2)
        print(f"Issues JSON saved to: {issues_path}")

        grouped_path = get_output_paths(plan_path, "code_review_grouped", phase='code-review')
        validation_path = get_output_paths(plan_path, "code_review_validation", phase='code-review')
        # The bound grouped.json reused (this function checks its bytes against
        # the task file below, so a rewrite would refuse its own round), or
        # the issues regrouped: one rule for every review lane. A
        # `--reaggregate` completing a run interrupted before grouping finds no
        # grouped.json and groups as the fan-out would. Attributed again
        # in memory on a reused grouping, into the file on a regroup.
        bound = _review_lane.bind_grouping(
            claim, steps, phase_dir=str(phase_dir), grouped_path=str(grouped_path),
            validation_path=str(validation_path), records=all_issues,
            records_by_model=loaded.by_model,
            skip_validation=bool(args.skip_validation), noun="issues",
            annotate=lambda groups: attribute_review_groups(
                groups, state, repo_root=git_root or project_root
            ),
        )
        grouped = bound.groups
        commit_attribution_pass = bound.annotation

        # A round built from truncated context, verdicts bound to this
        # grouping, zero groups, `--skip-validation`, a materialized round to
        # merge or resume, or a new round: one resolution for every review lane.
        outcome = await _review_lane.resolve_validation_round(
            claim, args, steps,
            phase_name="code-review", phase_dir=str(phase_dir),
            plan_path=str(plan_path), grouped=grouped,
            grouped_path=str(grouped_path),
            validation_path=str(validation_path),
            current_inputs=lambda: build_inputs(
                plan_file=str(plan_path),
                grouped_file=str(grouped_path),
                # The grouping this reaggregate reports, as it holds it.
                grouped_text=claim.grouping_text,
                # Recut from the same groups and the files as they are now: a
                # reviewed file edited between fan-out and this reaggregate
                # moves this hash, and only this hash — `diff_base` names the
                # ref the diff was taken against and sits still for any edit on
                # the near side of it.
                reviewed_code=build_reviewed_code_excerpt(
                    grouped, project_root=project_root, **pinned_kw,
                ),
                # A commit brief's frozen context plan: its snapshot as it is
                # now, against what the round recorded.
                **(
                    {"context_plan_sha256": context_plan_snapshot_sha256(
                        plan_snapshot, git_root,
                    )}
                    if plan_snapshot and plan_sha256 else {}
                ),
            ),
            # Reused verdicts are held to these inputs too.
            reuse_checks_inputs=CodeLane.reuse_checks_inputs,
            build_round=lambda plan_document: code_review_validation_round(
                [g.to_dict() if hasattr(g, 'to_dict') else g for g in grouped],
                args=args, plan_path=plan_path, phase_dir=phase_dir,
                plan_document=plan_document, base_ref=base_ref,
                project_root=project_root, git_root=git_root, pinned=pinned,
                plan_snapshot=plan_snapshot, plan_sha256=plan_sha256,
                scope_round_policy=scope_round_policy, state=state,
                round_id=claim.round_id,
            ),
            scope_round_policy=scope_round_policy,
            scope_baseline=_scope_round.round_baseline(
                getattr(state, "state", {}) or {}, "code-review"
            ),
            findings="issues",
            # The command the fan-out's hand-off names: a commit review's is
            # spelled in its commit mode.
            follow_up=lambda document: lane.round_follow_up(document, typed=True),
        )
        if outcome.handed_off:
            return EXIT_OK
        # The validation.json bytes the report's verdicts come from, when they do.
        verdicts = outcome.verdicts
        # With validation skipped the report shows the groups on disk, as the
        # base lane's report and this lane's fan-out do.
        validated_groups_for_report = (
            outcome.groups if outcome.groups is not None else grouped
        )

        # Generate report. `served_models` is what the fan-out recorded in the
        # checkpoint (the attribution and the D6 override's `sandbox:
        # bypassed`, 2026-09-17): the per-model files carry neither, so without
        # this read a reaggregated report named a bypassed slot as if it had
        # run sandboxed.
        report = generate_review_report(
            plan_path, results, changed_files, validated_groups_for_report,
            # The commit header from the record, never from git.
            commit_review=commit_report.report_context(
                state, commit_attribution_pass, changed_files,
                repo_root=git_root or project_root,
            ),
            phase_dir=phase_dir, base_ref=base_ref, template_style=template_style,
            served_models=recorded_served_models(str(phase_dir)),
            # …and what each slot spent, off the same checkpoint: `{model}.json`
            # is a bare issue list here too, so a reaggregated report that did
            # not read this lost every number the original run recorded.
            usage=recorded_usage(str(phase_dir)),
            #  T5.1: the failures read back above, and the recorded
            # requested set as the "of M requested" denominator.
            failed_models=failed_models_map,
            requested_models=(
                len(requested_set) if requested_set is not None else None
            ),
            # D2.2: the scope read back (or regenerated) above.
            review_scope=scope_record,
            **({"pinned": pinned, "repo_root": git_root} if pinned is not None else {}),
        )

        # Save report: published whole and sealed with this round's line
        # (utils/review_round.py, "the report's seal").
        report_path = get_output_paths(plan_path, "code_review", phase='code-review')
        report_path = report_path.with_suffix(".md")
        _review_round.publish_report(report_path, report, claim=claim,
                                     verdicts=verdicts)

        print("\nReaggregation complete!")
        print(f"Report: {report_path}")

        # The report's files handed back on both channels, as every review
        # lane's completion hands them (utils/review_lane.py).
        _review_lane.hand_back_report(
            steps, phase_dir, report=report_path, grouped=grouped_path,
            validation=validation_path, issues=issues_path,
        )

        # `[PARTIAL_RESULTS]` for the models still missing, then the phase
        # recorded complete while the round on record is still this one's, as
        # every review lane's reaggregate ends (utils/review_lane.py).
        _review_lane.complete_reaggregate(
            claim, steps, loaded, state=get_or_create_state(plan_path),
            phase_name="code-review", phase_dir=str(phase_dir),
        )

        # The fan-out's ending, shared: a host-driven review finishes here.
        return finish_code_review(
            phase_dir, validated_groups_for_report, args,
            total_issues=len(all_issues),
        )


def finish_code_review(
    phase_dir: Path,
    groups: Optional[List[Dict[str, Any]]],
    args: argparse.Namespace,
    *,
    total_issues: int,
) -> int:
    """The summary, the HIGH-group record and the ``--fail-on-high`` gate.

    Called by both of the phase's completion sites, the fan-out and
    ``--reaggregate``, after the phase is recorded complete: the gate's exit 3
    is ``modes.REVIEW_GATE``, which hosts read as "completed, wants a decision".
    Returns the exit code.

    The count is distinct HIGH-importance *groups*, not raw issues, recorded in
    ``.status.json`` and on the result line by the base's
    ``record_high_priority_groups`` (which clears a stale count), because a
    bare print reaches no detached caller (docs/development/review-results.md).
    The bracketed marker is printed only when there is a finding.

    A review that found HIGH issues *worked*, so it is exit 0: a non-zero exit
    would stop ``full`` one phase before ``apply-code-fixes`` and put
    ``state: "error"`` on the result line (docs/development/dispatcher.md).
    ``--fail-on-high`` is the opt-in for a standalone CI gate, exit 3 and never
    1, since nothing errored.
    """
    high_count = record_high_priority_groups(str(phase_dir), groups)
    print("\n=== Review Summary ===")
    print(f"Total issues: {total_issues}")
    print(f"High priority: {high_count} group(s)")
    if high_count > 0:
        print(f"[HIGH_PRIORITY_ISSUES] {high_count}")
    if high_count > 0 and getattr(args, "fail_on_high", False):
        return EXIT_NEEDS_HUMAN
    return EXIT_OK


def _sealed_grouping(
    phase_dir: Path, *, validation_bytes: Optional[bytes] = None,
) -> Tuple[Optional[List[Dict[str, Any]]], str]:
    """``(groups, "")`` from the ``grouped.json`` the ``validation.json``
    beside it binds, or ``(None, why)``.

    ``validation.json`` records the digest of the grouping its verdicts were
    reached on (``metadata.grouped_sha256``, D7), and a report's seal binds
    those ``validation.json`` bytes, so this is the grouping the sealed report
    was built from. A grouping that is missing, unreadable, of other bytes, or
    that ``validation.json`` binds no digest for, gives no groups: it is never
    read as zero groups. The bytes hashed are the bytes parsed.

    *validation_bytes* are the ``validation.json`` bytes the seal was checked
    against (``review_round.sealed_verdicts``): the digest is read from them,
    never from the file again, so a pair replaced after the seal check does
    not pass; ``None`` reads the file once.
    """
    grouped_path = phase_dir / "grouped.json"
    validation_path = phase_dir / "validation.json"
    try:
        validation = json.loads(
            validation_path.read_text(encoding="utf-8") if validation_bytes is None
            else read_back_text(validation_bytes)
        )
    except (OSError, ValueError) as exc:
        return None, f"{validation_path.name} could not be read: {exc}"
    metadata = validation.get("metadata") if isinstance(validation, dict) else None
    bound = metadata.get("grouped_sha256") if isinstance(metadata, dict) else None
    if not bound:
        return None, (f"{validation_path.name} records no grouping digest "
                      f"(metadata.grouped_sha256) to check {grouped_path.name} against")
    try:
        text = grouped_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        text = None
    except (OSError, UnicodeDecodeError) as exc:
        return None, f"{grouped_path.name} could not be read: {exc}"
    current = content_hash(text) if text is not None else ""
    if current != bound:
        return None, (f"{validation_path.name} belongs to grouping {bound}, current "
                      f"{grouped_path.name} is {current or 'missing'}")
    try:
        payload = load_groups_payload(json.loads(text))
    except ValueError as exc:
        return None, f"{grouped_path.name} is not a grouping: {exc}"
    return [g for g in payload if isinstance(g, dict)], ""


def heal_unrecorded_completion(
    phase_dir: Path, state: Any, args: argparse.Namespace, *, report_path: Path,
    plan_path: Path, validation_bytes: Optional[bytes] = None,
) -> int:
    """Finish the completion of a round whose report outlived its record.

    The partial-completion guard calls this only when the round on record's
    task file, its ``validation.json`` and a whole ``report.md`` sealed with
    that ``validation.json`` are all on disk: a run that stopped after
    publishing its report and before recording the phase. Nothing is
    re-derived from the files but what the fan-out records after the report:
    the artifacts handed back to a detached caller, the phase recorded
    complete, then :func:`finish_code_review`'s summary, HIGH-group record and
    ``--fail-on-high`` gate, counted from the ``grouped.json`` that
    ``validation.json`` binds (:func:`_sealed_grouping`; the count is of
    groups, whatever their verdicts) and ``issues.json``. Its exit code is
    returned, so a healed review is never a passing gate that never ran.
    A grouping that does not check out records nothing and refuses with exit 3,
    naming ``--force``: unavailable evidence is never counted as zero HIGH
    groups (docs/development/review-results.md, "The shared review lane").
    *validation_bytes* are the ``validation.json`` bytes the caller checked the
    seal against; the grouping is bound through them, never through a later
    read (docs/development/review-results.md, "Consuming checked bytes").
    """
    grouped_path = phase_dir / "grouped.json"
    validation_path = phase_dir / "validation.json"
    issues_path = phase_dir / "issues.json"
    sealed, problem = _sealed_grouping(phase_dir, validation_bytes=validation_bytes)
    if sealed is None:
        print("ERROR: Partial completion detected for 'code-review'.")
        print("  validation.json and a whole report.md sealed with it record this "
              f"round, but {problem}.")
        print("  The completion counts the HIGH groups from grouped.json, so it is "
              "not finished from a grouping that does not check out.")
        print("  Re-run with --force: it keeps each reusable model result "
              "([SKIP]), regroups and validates again:")
        print("  " + commit_spelling.spell_retry_command(
            "review-code", plan_path, "--force",
            flags=cli_common.current_replay_flags(mode="review-code"),
        ))
        return EXIT_NEEDS_HUMAN
    groups: List[Dict[str, Any]] = sealed
    try:
        issues = json.loads(issues_path.read_text(encoding="utf-8"))
        total_issues = len(issues) if isinstance(issues, list) else 0
    except (OSError, ValueError):
        total_issues = sum(
            len(g.get("suggestions", g.get("issues", [])) or []) for g in groups
        )
    steps = code_round_steps()
    _review_lane.hand_back_report(
        steps, phase_dir, report=report_path, grouped=grouped_path,
        validation=validation_path, issues=issues_path,
    )
    _review_lane.record_phase_complete(
        None, steps, state=state, phase_name="code-review",
        phase_dir=str(phase_dir),
    )
    print("Phase 'code-review' was complete but not marked. Auto-healed state.")
    print(f"Report: {report_path}")
    return finish_code_review(phase_dir, groups, args, total_issues=total_issues)


def _plan_file_label(plan_path: Path, args: Any = None) -> str:
    """``Plan file`` as today, or ``Commit brief`` when the plan's
    ``state.json`` records a ``commit_range``: the phase's own lines never call
    a commit brief a plan, through the one owner of the word,
    ``commit_paths.document_label``. *args* carrying a front door's stage
    (:func:`landed_stage`) is a commit brief too: a detached launch of a new
    brief has its ``commit_range`` only in that stage until the worker's
    boundary, after this label prints. Read-only; no state is a plan."""

    record = read_commit_range(plan_path)
    if record is None and landed_stage(args):
        record = {}
    word = document_label({"commit_range": record})
    return "Plan file" if word == "plan" else word.capitalize()


async def main(argv: Optional[List[str]] = None) -> int:
    """Main entry point: :func:`_main` under this run's hold on the code-review
    phase dir, taken at its entry and released when it returns or exits
    (``detach.PhaseRun``; docs/development/runtime.md, "One writer per phase
    dir")."""

    # A worker started here directly (review-commits --detach) applies its
    # stage as the dispatcher's does.
    hand_worker_the_stage_applier(argv)
    with PhaseRun() as run:
        return await _main(argv, run)


async def _main(argv: Optional[List[str]], run: PhaseRun) -> int:
    """The review: a fan-out, or a ``--reaggregate`` of the round on record.

    A fan-out is a sequence of named stages over one :class:`RunScope`.
    Everything before :func:`_cross_detach_boundary` is pre-flight, run in the
    invoker so a failure lands on the caller's terminal; nothing after that
    stage's ``maybe_detach`` runs there. ``intent_to_add_untracked`` wraps the
    diff set, the reviewer run and the round built on them, and
    :func:`_group_validate_and_report` stops its phase ticker only after the
    terminal ``progress.step`` (docs/development/review-results.md, "The
    shared review lane").
    """
    # Line buffering + UTF-8/replace stream encoding (Windows-safe output);
    # see utils/stream_bootstrap.py for the full rationale.
    bootstrap_streams()

    args = parse_args(argv)
    plan_path, prefix, out_dir = _locate_plan(args)

    # Handle --reaggregate mode: skip model invocation, just re-process existing results
    if args.reaggregate:
        return await _reaggregate_entry(
            args, run, plan_path=plan_path, out_dir=out_dir, prefix=prefix,
        )

    # One writer per phase dir, as on the reaggregate path: taken before this
    # run reads state.json or the phase's files. A `--detach` launcher whose
    # dir a live run holds re-attaches, takes it over or refuses right here,
    # before any of its pre-flight (`detach.take_for_launch`).
    run.take(get_phase_dir(plan_path, 'code-review'), mode="review-code",
             plan_file=str(plan_path), args=args, phase="code-review")
    pinned = _guard_phase_state(args, plan_path)

    # Model selection, one rule for every review lane: CLI --models >
    # --interactive > --quick > the mode's YAML defaults > interactive
    # selection; under --yes it stops at defaults.models (D6 row 2).
    model_specs, unattended = _review_lane.select_review_models(
        args, mode='code-review', anchor=str(plan_path),
    )
    _announce_fanout(args, plan_path, out_dir, model_specs)

    # Get tracked files and base ref from state (if available from implementation phase)
    state = get_or_create_state(plan_path)
    scope = _resolve_base_and_scope(args, state, plan_path=plan_path, pinned=pinned)
    scope_round_policy, plan_bytes = _resolve_round_policy_and_plan_bytes(
        args, state, plan_path=plan_path,
    )

    detach_phase_dir, claim, scope, plan_bytes = _cross_detach_boundary(
        args, state, scope, plan_path=plan_path, model_specs=model_specs,
        plan_bytes=plan_bytes,
    )
    plan_document_at_load, opening = _open_fanout_round(
        args, state, scope, claim, plan_path=plan_path,
        detach_phase_dir=detach_phase_dir,
        model_specs=model_specs, plan_bytes=plan_bytes,
        scope_round_policy=scope_round_policy, unattended=unattended,
    )

    # Two commits need no intent-to-add marking: the working tree is not in
    # their diff.
    with (
        contextlib.nullcontext() if scope.pinned is not None
        else intent_to_add_untracked(scope.changed_files, cwd=scope.git_root)
    ):
        diff_set = _write_diff_set(
            args, state, scope, detach_phase_dir=detach_phase_dir,
            model_specs=model_specs,
        )
        slots = await _run_reviews_and_save(
            args, scope, claim, diff_set, plan_path=plan_path, out_dir=out_dir,
            prefix=prefix, detach_phase_dir=detach_phase_dir, model_specs=model_specs,
            scope_round_policy=scope_round_policy, unattended=unattended,
            opening=opening,
        )
        outcome = await _group_validate_and_report(
            args, state, scope, claim, diff_set, slots, plan_path=plan_path,
            out_dir=out_dir, model_specs=model_specs,
            plan_document_at_load=plan_document_at_load,
            scope_round_policy=scope_round_policy,
        )
        if outcome is None:
            return  # the host runs the round and comes back with --reaggregate

    # Summary, HIGH-group record and gate: the ending `--reaggregate` shares.
    exit_code = finish_code_review(
        slots.phase_dir, outcome.groups, args, total_issues=len(outcome.all_issues),
    )
    _announce_fix_tasks(args, outcome)
    _announce_pending_salvage(slots.phase_dir, plan_path, slots.salvaged_models)

    # `finish_code_review`'s exit: 0 whatever the review found, 3 under
    # `--fail-on-high` with a HIGH group.
    return exit_code


# ---------------------------------------------------------------------------
# The stages of `_main`, in the order it runs them
# ---------------------------------------------------------------------------

@dataclasses.dataclass(frozen=True)
class RunScope:
    """What one review-code fan-out reviews, resolved once in its pre-flight.

    :func:`_resolve_base_and_scope` builds it before the detach boundary, and
    every stage past the boundary reads it rather than a local of its own.

    * ``base_ref``: the old side every git call takes.
    * ``review_scope``: the resolved :class:`ReviewScope`, labelled with the
      branch that picked it.
    * ``changed_files``: that scope in review order, what every reviewer's
      prompt lists, what ``intent_to_add_untracked`` marks and what the report
      counts.
    * ``pinned``: the pair a review pinned to two commits diffs, with its drift
      list, or ``None``.
    * ``plan_snapshot``, ``plan_sha256``: a commit brief's frozen context plan.
    * ``git_root``: where every git call over the (root-relative) scope runs;
      ``project_root``: what an issue's relative ``file`` is resolved against.
    * ``collapse_paths``: the one read of ``code_review.collapse_paths`` the
      prompt's order and the diff set's groups share.
    * ``scope_files``: the ``--files``/``--files-from`` list, or ``None``,
      staged on the in-memory state; ``files_record_moved`` says staging it
      changed that record, which the phase then saves past the boundary.

    A front door's stage can land inside the boundary; :meth:`refresh`
    re-derives what depends on it.
    """

    base_ref: Optional[str]
    review_scope: ReviewScope
    changed_files: List[str]
    pinned: Optional[PinnedRange]
    plan_snapshot: Optional[str]
    plan_sha256: Optional[str]
    git_root: Optional[str]
    project_root: Optional[str]
    collapse_paths: Dict[str, List[str]]
    scope_files: Optional[List[str]]
    files_record_moved: bool

    @property
    def pinned_kw(self) -> Dict[str, Any]:
        """``{"pinned": pinned}`` for a review pinned to two commits, else ``{}``."""
        return {"pinned": self.pinned} if self.pinned is not None else {}

    def refresh(self, state: Any, *, args: Any, plan_path: Path) -> "RunScope":
        """This scope re-derived past a landed stage (:func:`landed_stage`).

        *state* is reloaded, its staged ``--files`` record redone, the pinned
        pair (and a fronted run's drift list) re-resolved and the context plan
        read again from the reloaded state; the base ref and the ordered paths
        are kept. A pair that no longer resolves is exit 3 here, like the
        pre-flight's (:class:`RangeError`).
        """
        state.reload()
        files_record_moved = stage_scope_files_record(state, self.scope_files)
        try:
            pinned = refresh_pinned_after_stage(
                state, self.pinned, args, cwd=self.git_root or os.getcwd(),
                plan_path=plan_path,
            )
        except RangeError as exc:
            print(exc.message)
            sys.exit(exc.exit_code)
        plan_snapshot, plan_sha256 = _context_plan(getattr(state, "state", None))
        return dataclasses.replace(
            self, pinned=pinned, plan_snapshot=plan_snapshot,
            plan_sha256=plan_sha256, files_record_moved=files_record_moved,
        )


def _locate_plan(args: argparse.Namespace) -> Tuple[Path, str, Path]:
    """``(plan_path, prefix, out_dir)``, with this run's anchor set.

    A plan that does not exist is exit 1. The anchor is captured here, before
    anything can chdir.
    """
    # Validate plan file (resolve to absolute path first to handle
    # uv --directory which changes the working directory)
    plan_path = Path(args.plan_file).resolve()
    if not plan_path.exists():
        print(f"ERROR: {_plan_file_label(plan_path, args)} not found: {args.plan_file}")
        print(f"       Resolved path: {plan_path}")
        sys.exit(1)

    # The anchor capture point — absolute, before anything can chdir
    # and before any provider read that decides routing.
    set_run_anchor(str(plan_path))

    # Derive prefix and output directory (needed for both normal and reaggregate modes)
    prefix = derive_prefix(plan_path)
    base_dir = plan_path.parent

    # Guard against double-nesting if parent already is the prefix
    if base_dir.name == prefix:
        out_dir = base_dir
    else:
        out_dir = base_dir / prefix
    return plan_path, prefix, out_dir


def _resolve_pinned_or_exit(
    state: Any, args: argparse.Namespace, plan_path: Path, **kwargs: Any,
) -> Optional[PinnedRange]:
    """:func:`resolve_pinned_range` over *state* at the plan's repository root,
    or the :class:`RangeError`'s message and exit code (``[RANGE_UNRESOLVED]``
    is exit 3). *kwargs* go to the resolver (``reaggregate=True``)."""
    try:
        return resolve_pinned_range(
            getattr(state, "state", None), args,
            cwd=review_git_root(get_project_root(str(plan_path))) or os.getcwd(),
            plan_path=plan_path, **kwargs,
        )
    except RangeError as exc:
        print(exc.message)
        sys.exit(exc.exit_code)


async def _reaggregate_entry(
    args: argparse.Namespace, run: PhaseRun, *, plan_path: Path, out_dir: Path,
    prefix: str,
) -> int:
    """``--reaggregate``: the round on record re-processed, no model run.

    :func:`_reaggregate_preflight` runs in the invoker; the boundary follows,
    and past it the re-dispatch runs under the phase-scoped ticker. Returns
    ``reaggregate_from_existing_files``' exit code.
    """
    reaggregate_pinned = _reaggregate_preflight(
        args, run, plan_path=plan_path, out_dir=out_dir,
    )

    # The detach boundary, crossed here as well as on the fan-out path
    # (`_cross_detach_boundary`): a `--reaggregate --detach` launch must
    # print its run banner and hand the re-dispatch to a worker, or the host
    # that composed `--detach` has nothing to poll (see the same branch in
    # `utils/review_orchestrator_base.main`).
    detach_outcome = maybe_detach(
        args=args,
        mode='review-code',
        phase_dir=str(get_phase_dir(plan_path, 'code-review')),
        plan_file=str(plan_path),
        phase='code-review',
    )
    if detach_outcome is not None:
        sys.exit(detach_outcome)
    # A front door's stage lands inside that boundary: the pair and
    # its drift list come from the state it left, not the one the pre-flight
    # read.
    if landed_stage(args):
        reaggregate_pinned = _resolve_pinned_or_exit(
            get_or_create_state(plan_path), args, plan_path, reaggregate=True,
        )

    # T5: this path has no fan-out at all, and it is not short — it
    # regroups, re-materializes or merges a validation round (dispatching it
    # in-process under `--exec-subagents`) and rebuilds the report. The
    # fan-out's ticker cannot cover a window it does not run in, so the
    # caller starts the phase-scoped one, which prints the step, the elapsed
    # since it started and whatever counters the current step already
    # publishes (`progress.subagents`). Stopped in a `finally` because
    # `reaggregate_from_existing_files` ends by writing its terminal
    # `progress.step` — and, on the `TaskFileError` branch, by `sys.exit`.
    phase_ticker = PhaseProgress(
        str(get_phase_dir(plan_path, 'code-review')), anchor=str(plan_path)
    )
    phase_ticker.start_ticker()
    # See the fan-out path's copy of this: one turn so the task enters its
    # body, because `await`ing a coroutine is not itself a suspension point
    # and a never-scheduled task loses the teardown line.
    await asyncio.sleep(0)
    # A refusal (`sys.exit` on a stale task file or changed snapshot) wrote
    # no step of its own, so its teardown line would re-print the previous
    # run's `step: complete` (dogfood 2026-09-25): dropped on that ending.
    refused = False
    try:
        reaggregate_exit = await reaggregate_from_existing_files(
            prefix, out_dir, plan_path, args,
            template_style=args.report_style,
            **(
                {"pinned": reaggregate_pinned}
                if reaggregate_pinned is not None else {}
            ),
        )
    except SystemExit:
        refused = True
        raise
    finally:
        await phase_ticker.stop_ticker(final_line=not refused)
    return reaggregate_exit


def _reaggregate_preflight(
    args: argparse.Namespace, run: PhaseRun, *, plan_path: Path, out_dir: Path,
) -> Optional[PinnedRange]:
    """A ``--reaggregate``'s pre-flight, on the caller's terminal: the phase
    dir's lock, the pinned pair on record, and the refusals (a stale review,
    another scope policy, another round's validation files). Returns the
    pair, or ``None`` for a review pinned to nothing."""
    print("=== REAGGREGATE MODE ===")
    print(f"{_plan_file_label(plan_path, args)}: {plan_path}")
    print(f"Output directory: {out_dir}")
    # `--files`/`--files-from` are not re-read here: the results on disk
    # were reviewed against the scope their fan-out recorded, so that is
    # the scope this pass reports. Said, not dropped silently — an explicit
    # scope request ignored without a word is the fallback the flags exist
    # to remove. A line, not an exit: every reaggregate command this
    # orchestrator prints replays the fan-out's own flags, `--files`
    # included, so refusing them would break its own recovery path.
    # Never parsed either, so `--files-from -` reads no stdin.
    ignored_scope_flags = [
        flag
        for flag, given in (
            ("--files", bool(getattr(args, "files", None))),
            ("--files-from", getattr(args, "files_from", None) is not None),
        )
        if given
    ]
    if ignored_scope_flags:
        print(
            f"[SCOPE_FLAGS_IGNORED] --reaggregate does not re-resolve "
            f"{' or '.join(ignored_scope_flags)}; it uses the scope recorded "
            f"in state.json ({REVIEW_SCOPE_FILES_KEY}, else tracked_files, "
            f"else the git diff). Run a fan-out with the flag to review "
            f"another scope."
        )
    print("")

    if not out_dir.is_dir():
        print(f"ERROR: Output directory does not exist: {out_dir}")
        sys.exit(1)

    # One writer per phase dir: held from here until this run exits, so a
    # second run is refused before it reads or changes anything (a
    # launcher hands it to its worker at the boundary).
    run.take(get_phase_dir(plan_path, 'code-review'), mode="review-code",
             plan_file=str(plan_path), args=args, phase="code-review")

    # The review on record's two commits, when state pins them (a commit
    # brief's `commit_range`, a direct round's `head_ref`): resolved
    # strictly here, before the detach boundary and before anything is
    # written, so a pruned SHA is `[RANGE_UNRESOLVED]` exit 3 on the
    # caller's terminal and never a `HEAD~1` stand-in, and a typed ref
    # that resolves elsewhere is refused.
    reaggregate_pinned = _resolve_pinned_or_exit(
        get_or_create_state(plan_path), args, plan_path, reaggregate=True,
    )
    if reaggregate_pinned is not None:
        pin_recorded_refs(reaggregate_pinned)

    # The stale guard the fan-out path applies (`_guard_phase_state`),
    # applied here too. A review completed before the latest implement
    # judged an earlier state of the code; the fan-out takes
    # `--force` on it, but this path ran no model and ended in
    # `mark_phase_completed`, which re-stamped the stale review newer than
    # implement, so apply-code-fixes then applied the empty-repo findings
    # (adversarial review, 2026-10-02). Refused, not re-run: a reaggregate
    # is a promise to run no model. Before the detach boundary, so the
    # refusal lands on the caller's terminal with no child and no log.
    if get_or_create_state(plan_path).phase_completion_is_stale("code-review"):
        print("ERROR: code-review was completed before the latest implement, "
              "so its results judge an earlier state of the code; "
              "--reaggregate would only re-stamp them.")
        print("  Re-run the review instead: "
              + commit_spelling.spell_retry_command(
                  "review-code", plan_path, "--force",
                  flags=cli_common.current_replay_flags(mode="review-code"),
              ))
        sys.exit(EXIT_NEEDS_HUMAN)

    # The round on record keeps its scope policy: a differing explicit
    # `--scope-policy` is refused here, before the boundary.
    resolve_scope_round(
        get_or_create_state(plan_path), "code-review", args, same_round=True,
        phase_dir=str(get_phase_dir(plan_path, 'code-review')),
    )
    # Another round's validation files are refused here too, before the
    # boundary, so a `--reaggregate --detach` refusal reaches the caller
    # (the worker checks again against the round it captures).
    _review_round.refuse_foreign_round(
        _review_round.continue_round(get_phase_dir(plan_path, 'code-review')),
        commit_spelling.spell_retry_command(
            "review-code", plan_path, "--force",
            flags=cli_common.current_replay_flags(mode="review-code"),
        ),
    )
    return reaggregate_pinned


def _guard_phase_state(args: argparse.Namespace, plan_path: Path) -> Optional[PinnedRange]:
    """A fan-out's guards over the phase on record, in pre-flight.

    The pinned pair is resolved first, strictly, because the guards may write
    ``state.json`` and a pair that no longer resolves must be refused before
    anything is written; it is returned. Then ``state.json`` is materialized,
    a stale completion re-runs as ``--force``, a completed phase is reported
    done, and :func:`_guard_partial_completion` judges the files of a round
    that stopped part way. Each refusal exits.
    """
    # Guard against re-running already-completed phase (expensive LLM calls)
    state_guard = get_or_create_state(plan_path)
    # A review pinned to two commits (`--head-ref`, or a commit brief's
    # `commit_range`): both ends resolved strictly, never through
    # `validate_git_ref`'s `HEAD~1` fallback, and a recorded SHA that no longer
    # names a commit is `[RANGE_UNRESOLVED]` exit 3 — all before this phase
    # writes anything, `state.json` included. The recorded invocation then carries the
    # pair as full SHAs, so a
    # detached child, a resume line and a next command replay the same pair
    # after a branch moves.
    pinned = _resolve_pinned_or_exit(state_guard, args, plan_path)
    if pinned is not None:
        pin_recorded_refs(pinned)
    # A `--detach` launcher writes no state before the boundary: its launch can
    # still be refused (the detached ceiling, a run that appeared since), and a
    # refusal must leave state.json as it found it. The worker runs this same
    # pre-flight and saves (review fix 3, A1).
    detach_launcher = bool(getattr(args, "detach", False)) and not getattr(
        args, "internal_worker", False)
    # First run on this plan: materialize `state.json` now, for the same
    # reason `review_orchestrator_base` does (the instructions' `util metrics
    # start --state-file` runs before the phase completes, and a standalone
    # review-code on a fresh plan used to find no file).
    if not state_guard.state_file.exists() and not detach_launcher:
        state_guard.save()
    if not args.force and state_guard.phase_completion_is_stale("code-review"):
        # Implement completed after this review did, so the review judged an
        # earlier state of the code. `is_phase_completed` already reads it as pending;
        # the artifacts it left in the phase dir must not auto-heal it back to
        # complete below, so a plain run takes the `--force` path.
        print("NOTE: code-review was completed before the latest implement; "
              "re-running it (as --force)")
        args.force = True
    if state_guard.is_phase_completed("code-review") and not args.force:
        # Said as done, never as an error. A
        # commit review says it as the mode the user typed, of its commit
        # brief.
        sys.exit(report_already_completed(
            spell_mode("review-code", commit_view(state_guard.state)),
            get_phase_dir(plan_path, 'code-review'),
            document=document_label(state_guard.state)))
    elif args.force and state_guard.is_phase_completed("code-review"):
        state_guard.state.get("phases_completed", {}).pop("code-review", None)
        if not detach_launcher:
            state_guard.save()
        print("NOTE: Cleared previous phase completion (--force mode)")

    # Secondary guard: detect partial completion (validation_tasks.json, grouped.json, etc.)
    # Under the phase lock, so no other run can be writing the files it judges
    # or completes the phase on.
    if not args.force:
        _guard_partial_completion(args, plan_path, state_guard)
    return pinned


def _checkpoint_unreadable(phase_dir: Path) -> bool:
    """Whether *phase_dir*'s checkpoint is damaged or cannot be read
    (``status_file.checkpoint_damage``)."""

    try:
        return status_file.checkpoint_damage(str(phase_dir)) is not None
    except status_file.CheckpointUnreadable:
        return True


def _guard_partial_completion(
    args: argparse.Namespace, plan_path: Path, state_guard: Any,
) -> None:
    """The files of a round that stopped part way, judged without ``--force``.

    Returns when the phase dir holds none. Otherwise it exits: the round on
    record's verdicts and sealed report are finished by
    :func:`heal_unrecorded_completion`; every other leftover is exit 3 naming
    the command that continues it (``--reaggregate``, the task file's own
    resume, or ``--force`` for files that may be another round's).
    """
    phase_dir_check = get_phase_dir(plan_path, 'code-review')
    validation_tasks_path = phase_dir_check / "validation_tasks.json"
    grouped_path = phase_dir_check / "grouped.json"
    validation_path = phase_dir_check / "validation.json"
    report_path_check = phase_dir_check / "report.md"

    # A checkpoint that cannot be read proves nothing about these files, and
    # read as `{}` it would name them another round's: the startup recovers a
    # damaged one, setting them aside, or stops with the shared advice
    # (utils/review_lane.py, `recover_damaged_checkpoint`).
    if _checkpoint_unreadable(phase_dir_check):
        return

    if validation_tasks_path.exists():
        # Only the round on record's own files may complete the phase or
        # be resumed (utils/review_round.py). A `--force` re-run stamps a
        # new round before it replaces anything, so one stopped early
        # leaves the previous round's task file, validation.json and
        # report.md beside a checkpoint that names another round.
        status_check = read_status(str(phase_dir_check))
        rounds = _review_round.round_files(phase_dir_check, status_check)
        unproven = rounds.stale()
        if not _review_round.tasks_file_is_this_rounds(rounds, status_check):
            unproven = (_review_round.TASKS_NAME,) + tuple(
                name for name in unproven if name != _review_round.TASKS_NAME
            )
        if unproven:
            print("ERROR: Partial completion detected for 'code-review'.")
            print(f"  {', '.join(unproven)} may not be this round's: "
                  f"{_review_round.evidence(rounds, unproven, status_check)}.")
            print("  Files a re-run stopped before replacing look exactly like "
                  "this, so they neither complete this phase nor resume it.")
            print("  Re-run with --force: it keeps each reusable model result "
                  "([SKIP]), regroups and validates again:")
            print("  " + commit_spelling.spell_retry_command(
                "review-code", plan_path, "--force",
                flags=cli_common.current_replay_flags(mode="review-code"),
            ))
            sys.exit(EXIT_NEEDS_HUMAN)
        # The seal read once, with the validation.json bytes it hashed: the
        # heal takes its verdicts' grouping digest from those bytes, never
        # from the file read again, and the round both record is checked on
        # the same reads (docs/development/review-results.md, "Consuming
        # checked bytes").
        seal, sealed_validation = _review_round.sealed_verdicts(phase_dir_check)
        recorded_round = _review_round.status_round(status_check)
        if validation_path.exists() and report_path_check.exists() and (
            rounds.owner(_review_round.VALIDATION_NAME) == _review_round.OWNED
            and rounds.owner(_review_round.REPORT_NAME) == _review_round.OWNED
            and seal.whole and seal.binds_validation
            and sealed_validation is not None
            and seal.round_id == recorded_round
            and _review_round.verdicts_of(sealed_validation).round_id == recorded_round
        ):
            # Auto-heal: this round's verdicts and report are both on disk
            # (both record the round on record, and the report is whole and
            # was built from this very validation.json: its seal), so only
            # the completion is missing, and it is finished the way the run
            # would have finished it: the HIGH groups recorded and the
            # `--fail-on-high` gate applied. The heal counts them from the
            # grouped.json that validation.json binds, or refuses (exit 3).
            sys.exit(heal_unrecorded_completion(
                phase_dir_check, state_guard, args, report_path=report_path_check,
                plan_path=plan_path, validation_bytes=sealed_validation,
            ))
        elif validation_path.exists() and report_path_check.exists():
            # This round's task file, but a validation.json or report.md
            # that does not record this round, or a report cut short or
            # built from another validation.json (its seal): a report
            # rebuilt from the verdicts the reaggregate checks against this
            # task file, never a completion taken from the files as they are.
            unrecorded = (_review_round.VALIDATION_NAME, _review_round.REPORT_NAME)
            print("ERROR: Partial completion detected for 'code-review'.")
            if (rounds.owner(_review_round.VALIDATION_NAME) == _review_round.OWNED
                    and rounds.owner(_review_round.REPORT_NAME) == _review_round.OWNED):
                print("  validation.json and report.md record this round, but "
                      "report.md is not the whole report built from this "
                      "validation.json (it was cut short, edited, or written "
                      "before the verdicts were merged again).")
            else:
                print("  validation.json and report.md are on disk, but "
                      f"{_review_round.evidence(rounds, unrecorded, status_check)}.")
            print("  Run: --reaggregate, which checks validation.json against this "
                  "round's task file and rebuilds the report.")
            sys.exit(3)
        elif validation_path.exists():
            print("ERROR: Partial completion detected for 'code-review'.")
            print("  validation.json exists but report is missing.")
            print("  Run: --reaggregate to regenerate the report.")
            sys.exit(3)
        else:
            # Check for batch files. A retired round's
            # `validation_batch_<n>.<stamp>.stale.json` (D7) still matches
            # the glob and is not validation in progress.
            batch_files = [
                path for path in phase_dir_check.glob("validation_batch_*.json")
                if not path.name.endswith(".stale.json")
            ]
            if batch_files:
                print("ERROR: Partial completion detected for 'code-review'.")
                print(f"  Found {len(batch_files)} validation batch file(s).")
                print("  Check if all batches are complete, then run: --reaggregate")
                sys.exit(3)
            else:
                print("ERROR: Partial completion detected for 'code-review'.")
                print("  validation_tasks.json exists but validation has not started.")
                print("  Resume it: for each task in that file, run task.prompt")
                print("  (or the file at task.prompt_path, whose bytes are the same)")
                print("  as a subagent and write the JSON it returns to task.output_path.")
                sys.exit(3)
    elif grouped_path.exists():
        print("ERROR: Partial completion detected for 'code-review'.")
        print("  grouped.json exists but no validation_tasks.json.")
        print("  Run: --reaggregate to continue from grouping.")
        sys.exit(3)
    else:
        # Check for per-model result files
        model_files = leftover_model_results(phase_dir_check)
        if model_files:
            print("ERROR: Partial completion detected for 'code-review'.")
            print(f"  Found {len(model_files)} per-model result file(s) but no grouped.json.")
            print("  Run: --reaggregate to aggregate results.")
            sys.exit(3)


def _announce_fanout(
    args: argparse.Namespace, plan_path: Path, out_dir: Path, model_specs: List[str],
) -> None:
    """The fan-out's header lines, and its output directory created."""
    print(f"{_plan_file_label(plan_path, args)}: {plan_path}")
    print(f"Output directory: {out_dir}")
    print(f"Models: {', '.join(model_specs)}")
    if args.timeout:
        print(f"Timeout override: {args.timeout}s per model")
    else:
        print("Timeout: per-provider defaults from providers.yaml")
    print(f"Max parallel: {args.max_parallel}")

    out_dir.mkdir(parents=True, exist_ok=True)


def _resolve_base_and_scope(
    args: argparse.Namespace, state: Any, *, plan_path: Path,
    pinned: Optional[PinnedRange],
) -> RunScope:
    """The fan-out's :class:`RunScope`, resolved in pre-flight.

    The roots, the ``--files`` list (staged on *state* in memory, saved only
    past the boundary), the base ref, the scope in review order, a pinned
    pair's drift check and a commit brief's context plan. A ``--files`` path
    outside the repository is exit 1 here, on the caller's terminal.
    """
    # The root an issue's relative `file` is resolved against when the
    # validation prompt embeds the code at the lines it cites.
    project_root = get_project_root(str(plan_path))
    # Where every git call over the (root-relative) scope runs — classification,
    # intent-to-add and the diff set — so a review invoked from a subdirectory
    # diffs the files it names rather than none of them.
    git_root = review_git_root(project_root)

    # `--files`/`--files-from` (decision 11.1): the exact scope, checked ahead
    # of `tracked_files` and the git fallback. Parsed here, in pre-flight, so a
    # path outside the repository fails on the caller's terminal naming it.
    # Staged on the in-memory state now — `resolve_review_scope` reads it from
    # there — and saved only past the detach boundary.
    try:
        scope_files = read_scope_files_flags(args, git_root or os.getcwd())
    except ScopeFilesError as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)
    scope_record_moved = stage_scope_files_record(state, scope_files)

    # Get the git base reference - this is the commit when implementation started
    # Used by agents to run: git diff <base_ref> -- <file>
    if pinned is not None:
        # The pinned pair, resolved strictly in `_guard_phase_state`: never
        # `head_before_implement`, `head_at_start` or `HEAD~1`, and never a
        # `validate_git_ref` fallback.
        base_ref = pinned.base_ref
        print(f"Git base reference: {base_ref}")
        # "as committed", not "two commits": a one-commit range is one commit,
        # and a root range's base is the empty tree, no commit at all.
        print(
            f"Git head reference: {pinned.head} (reviewing {pinned.display} as "
            f"committed, not the working tree)"
        )
    else:
        base_ref = args.base_ref or state.get("head_before_implement") or state.get("head_at_start") or "HEAD~1"
        base_ref = validate_git_ref(base_ref)
        print(f"Git base reference: {base_ref or '(empty - validation will lack diff context)'}")

    # Skipped for a pinned review: its `is-ancestor <base> HEAD` and
    # `rev-list <base>..HEAD` are about an implement base, and two commits are
    # reviewed whatever HEAD is.
    if base_ref and pinned is None:
        _note_base_ref_lag(base_ref)

    # The scope, labelled by the branch that picked it, then put in review
    # order: source, tests, fixtures, generated, by path within each. The
    # resolver's own order is never used (its tracked-files branch is a set).
    # This ordered list is what every reviewer's prompt lists, what
    # `intent_to_add_untracked` marks and what the report counts; before this,
    # main resolved it and then handed the reviewers the raw — and, on the
    # fallback, empty — `tracked_files` instead (review-scope).
    review_scope = resolve_review_scope(
        state, base_ref, anchor=str(plan_path), repo_root=git_root,
        **({"head_ref": pinned.head} if pinned is not None else {}),
    )
    # One read of `code_review.collapse_paths` for the prompt's order and the
    # diff set's groups, so the two classify every path alike.
    collapse_paths = get_collapse_paths(anchor=str(plan_path))
    changed_files = order_review_paths(
        review_scope.paths, collapse_paths, cwd=git_root,
        # `.gitattributes` as the head commit has it, as the manifest reads it.
        **({"source": pinned.head} if pinned is not None else {}),
    )
    print(f"Files to review: {len(changed_files)}")
    if pinned is not None:
        pinned = pinned._replace(
            not_in_range=review_scope.not_in_range, narrowed=review_scope.narrowed,
        )
        # `[SCOPE_DRIFT]` must reach the caller's terminal, so a direct run
        # checks here, before its detach boundary; a fronted run's list is
        # the front door's (`commit_range.drifted`), neither recomputed nor
        # printed, a staged launch's
        # included: its record arrives with the stage, past the boundary.
        pinned = drift_check(pinned, changed_files, repo_root=git_root,
                             staged=landed_stage(args))
    plan_snapshot, plan_sha256 = _context_plan(getattr(state, "state", None))
    print("Running code review in agent exploration mode...")
    print("")
    return RunScope(
        base_ref=base_ref, review_scope=review_scope, changed_files=changed_files,
        pinned=pinned, plan_snapshot=plan_snapshot, plan_sha256=plan_sha256,
        git_root=git_root, project_root=project_root, collapse_paths=collapse_paths,
        scope_files=scope_files, files_record_moved=scope_record_moved,
    )


def _note_base_ref_lag(base_ref: str) -> None:
    """Best-effort base-ref staleness visibility. Wrapped so it can NEVER fail
    the run: surface the resolved commit, and warn if the base ref lags behind
    HEAD (a common foot-gun when only the latest uncommitted work was meant to
    be reviewed)."""
    try:
        if is_empty_tree(base_ref):
            # `git log` names no commit for a tree, so say what it is.
            print(
                "Base ref is the empty tree: the repository had no commit "
                "when this workflow started, so every file under review is new"
            )
        log_out, _, log_rc = run_git(
            "log", "-1", "--format=%h %s", base_ref, check=False
        )
        if log_rc == 0 and log_out.strip():
            print(f"Base ref commit: {log_out.strip()}")

        _, _, anc_rc = run_git(
            "merge-base", "--is-ancestor", base_ref, "HEAD", check=False
        )
        if anc_rc == 0:
            count_out, _, count_rc = run_git(
                "rev-list", "--count", f"{base_ref}..HEAD", check=False
            )
            ahead = int(count_out.strip()) if count_rc == 0 and count_out.strip() else 0
            if ahead > 0:
                print(
                    f"NOTE: base ref is {ahead} commit(s) behind HEAD. If you "
                    f"intend to review only the latest (uncommitted) work, pass "
                    f"--base-ref HEAD."
                )
    except Exception:
        pass


def _read_plan_bytes(plan_path: Path) -> bytes:
    """The plan's bytes, checked to decode; an undecodable plan prints its
    error to stderr and exits with the error's code."""
    try:
        plan_bytes = plan_path.read_bytes()
        decode_document(plan_bytes, str(plan_path))
    except ValidationContextError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(exc.exit_code)
    return plan_bytes


def _resolve_round_policy_and_plan_bytes(
    args: argparse.Namespace, state: Any, *, plan_path: Path,
) -> Tuple["_scope_round.RoundPolicy", Optional[bytes]]:
    """The round's scope policy and the plan's bytes, both in pre-flight.

    The plan is read only when validation will run (``None`` under
    ``--skip-validation``); it is bound to the phase's snapshot past the
    boundary, by :func:`_open_fanout_round`.
    """
    # The round's scope policy, resolved before the boundary: it
    # decides the reviewer and validator prompts alike, and a same-round
    # resume keeps the recorded one. A change that would mix reviewer outputs
    # in one round is refused here, on the caller's terminal (exit 3).
    scope_round_policy = resolve_scope_round(
        state, "code-review", args,
        force=bool(getattr(args, "force", False)),
        has_results=round_results_exist(str(get_phase_dir(plan_path, 'code-review'))),
        rerun_all=bool(getattr(args, "rerun_all", False)),
        phase_dir=str(get_phase_dir(plan_path, 'code-review')),
    )
    _scope_round.print_round_line("code-review", scope_round_policy)

    # The plan the reviewers are pointed at, read once here and bound to this
    # phase's `validation-snapshot.md` past the detach boundary (the same split
    # review-plan and review-tasks make): binding at materialization, after the
    # fan-out, let a plan edited during the review become the snapshot the
    # validators are hash-bound to. Only the read and the UTF-8 check happen
    # before the boundary, so an undecodable plan still fails in the foreground
    # and a repeated `--detach` never replaces an active run's snapshot.
    plan_bytes: Optional[bytes] = None
    if not args.skip_validation:
        plan_bytes = _read_plan_bytes(plan_path)
    return scope_round_policy, plan_bytes


def _cross_detach_boundary(
    args: argparse.Namespace, state: Any, scope: RunScope, *, plan_path: Path,
    model_specs: List[str], plan_bytes: Optional[bytes],
) -> Tuple[Path, "_review_round.Claim", RunScope, Optional[bytes]]:
    """The detach boundary, and the round this process opens past it.

    ``maybe_detach`` hands a ``--detach`` launch to its worker (and exits the
    launcher); nothing after it runs in the invoker. Past it a new round is
    claimed, a landed front-door stage re-derives the scope
    (:meth:`RunScope.refresh`) and re-reads the plan, and a commit brief's
    frozen context plan is checked. Returns ``(phase_dir, claim, scope,
    plan_bytes)``.
    """
    # --- the detach boundary (see utils/review_orchestrator_base.maybe_detach) --
    # Late on purpose: every stage before this one is pre-flight that must
    # fail on the caller's terminal — models resolved, base ref validated,
    # changed files discovered — and nothing below runs in the invoker.
    detach_phase_dir = get_phase_dir(plan_path, 'code-review')
    # A damaged checkpoint is recovered first, by the process that will own
    # the round (never a `--detach` launcher, whose worker does it): under the
    # phase lock this run took at its entry, before a worker claims its run
    # in that checkpoint and before the round is stamped
    # (utils/review_lane.py, `recover_damaged_checkpoint`).
    launcher = bool(getattr(args, "detach", False)) and not getattr(
        args, "internal_worker", False)
    recovery = None if launcher else _review_lane.recover_damaged_checkpoint(
        phase_dir=str(detach_phase_dir), phase_name='code-review',
        plan_file=str(plan_path),
        run_id=getattr(args, "internal_run_id", None),
        retire_validation_round=code_round_steps().retire_stale_validation_round,
    )
    detach_outcome = maybe_detach(
        args=args,
        mode='review-code',
        phase_dir=str(detach_phase_dir),
        plan_file=str(plan_path),
        phase='code-review',
        model_specs=model_specs,
    )
    if detach_outcome is not None:
        sys.exit(detach_outcome)

    # A new review round, recorded before this process replaces or retires
    # anything: from here on the previous round's validation files and report
    # read as another round's, so neither the partial-completion guard nor a
    # resume answer completes this phase on them (utils/review_round.py). The
    # opening checkpoint write (`_open_fanout_round`) carries it, every file
    # this run writes records it, and each publication checks that the
    # checkpoint still does (`claim.held`).
    claim = _review_round.start_round(
        detach_phase_dir, notes=_review_lane.recovery_notes(recovery))

    # A detached worker takes its lock inside `maybe_detach`, and a commit
    # front door's stage (the new header, `commit_range`, a context-plan
    # snapshot) is applied there — after the
    # pre-flight loaded `state`, read the brief and resolved the pair.
    # Saved as loaded, `state` would put the old `commit_range` back (or, on a
    # new brief, drop it) and the validation snapshot would bind the old
    # header. So everything derived from either is derived again: `state`
    # reloaded, its staged `--files` record redone, the pair (and a fronted
    # run's drift list and context plan) re-resolved, the brief re-read.
    if landed_stage(args):
        scope = scope.refresh(state, args=args, plan_path=plan_path)
        if plan_bytes is not None:
            plan_bytes = _read_plan_bytes(plan_path)

    if scope.plan_snapshot and scope.plan_sha256 and (
        context_plan_snapshot_sha256(scope.plan_snapshot, scope.git_root)
        != scope.plan_sha256
    ):
        print(
            f"[CONTEXT_PLAN_SNAPSHOT_CHANGED] {scope.plan_snapshot} is missing or "
            "differs from the frozen context plan. Restore the snapshot, or re-run "
            "--review-commits with --context-plan <path> to capture it again.",
            file=sys.stderr,
        )
        sys.exit(EXIT_NEEDS_HUMAN)
    return detach_phase_dir, claim, scope, plan_bytes


def _open_fanout_round(
    args: argparse.Namespace, state: Any, scope: RunScope,
    claim: "_review_round.Claim", *, plan_path: Path, detach_phase_dir: Path,
    model_specs: List[str], plan_bytes: Optional[bytes],
    scope_round_policy: "_scope_round.RoundPolicy", unattended: bool,
) -> Tuple[Optional[BoundDocument], "_review_lane.RoundOpening"]:
    """What this process records before the fan-out, as the phase's owner.

    The ``--files`` record saved (or cleared), the plan bound to the phase's
    validation snapshot, the round's scope baseline, and the round's opening
    checkpoint (:func:`utils.review_lane.open_round`). Returns the bound plan
    (``None`` under ``--skip-validation``) and what the opening read of the
    previous attempt.
    """
    # The fan-out starts here, so its `--files` scope is recorded here — or a
    # previous run's is cleared — for a later `--reaggregate` to resolve the
    # same scope. Below the boundary, like the plan snapshot: only the process
    # that owns the phase writes it.
    if scope.files_record_moved:
        state.save()
        if scope.scope_files is not None:
            print(
                f"Recorded the --files scope ({len(scope.scope_files)} files) as "
                f"{REVIEW_SCOPE_FILES_KEY} in state.json"
            )
        else:
            print(
                f"Cleared {REVIEW_SCOPE_FILES_KEY} from state.json (this fan-out "
                f"was not given --files)"
            )

    # This process now owns the phase, so the snapshot may be replaced.
    plan_document_at_load: Optional[BoundDocument] = None
    if plan_bytes is not None:
        plan_document_at_load = bind_plan_for_validation(
            str(plan_path), str(detach_phase_dir), data=plan_bytes
        )

    # The round's scope baseline: the accepted plan (a commit
    # review's brief) from the same bytes the validation snapshot holds, the
    # task list and the pinned range as evidence, a frozen context plan by its
    # recorded hash. Recorded through `state`, the instance this phase saves.
    retire_scope_round_results(
        str(detach_phase_dir), state, "code-review", scope_round_policy,
    )
    _scope_round.record_round(
        state, "code-review", scope_round_policy,
        code_review_scope_baseline(
            state, plan_path, plan_document_at_load,
            base_ref=scope.base_ref,
            head_ref=scope.pinned.head if scope.pinned is not None else None,
        ),
    )

    def models_requested_landed() -> None:
        # The opening write is best-effort by contract (`write_status` returns
        # nothing and raises nothing), and `models_requested` is the only
        # record of this run's canonical specs: without it a later
        # `--reaggregate` attributes every group to a result-file stem, which
        # moves grouped.json's bytes and makes the task file refuse its own
        # round. So it is read straight back, and a lost write is said now,
        # while the run is cheap to re-do; the fan-out goes on either way.
        try:
            recorded_specs = read_status(str(detach_phase_dir)).get("models_requested")
        except Exception:  # pragma: no cover - read_status is documented not to raise
            recorded_specs = None
        if not recorded_specs:
            warn_stem_attribution(
                f"WARNING: this run's checkpoint {detach_phase_dir / '.status.json'} "
                f"records no models_requested — the write is best-effort and cannot "
                f"report why. The fan-out below is unaffected and continues.",
                model_specs=list(model_specs),
            )

    # The round's opening checkpoint, one rule for every review lane
    # (utils/review_lane.py): what the previous attempt recorded (its `usage`
    # for reused slots, Stage U; its sandbox words for the retired-rung
    # notice) read before the write erases it, the requested specs (W3: the
    # only record a reaggregate inverts a stem with), the previous `progress`
    # dropped, the `--yes` resolutions recorded.
    opening = _review_lane.open_round(
        claim, code_round_steps(), args,
        phase_name="code-review", phase_dir=str(detach_phase_dir),
        model_specs=model_specs, scope_round_policy=scope_round_policy,
        unattended=unattended, after_opening=models_requested_landed,
    )
    return plan_document_at_load, opening


def _write_diff_set(
    args: argparse.Namespace, state: Any, scope: RunScope, *,
    detach_phase_dir: Path, model_specs: List[str],
) -> Any:
    """The diff set (``write_review_diff``'s ``ReviewDiffSet``) and the
    round's start, the first thing inside the intent-to-add block."""
    # The scope manifest and one whole diff per source or test file, the
    # FIRST thing inside the intent-to-add block (D2.2): inside it because
    # `git diff` shows a new untracked file only once it is intent-to-add, and
    # before the fan-out because every reviewer's prompt names these two
    # paths — a slot that started first would find them missing, or holding
    # the previous run's set. Into `detach_phase_dir`, resolved up front: the
    # `get_phase_dir` call in `_run_reviews_and_save` runs only after the
    # fan-out returns. A git failure degrades the set (`[DIFF_FAILED]`,
    # coverage partial) and the fan-out goes on. At `git_root`, like the
    # intent-to-add marking: the paths are root-relative, and from a
    # subdirectory every diff came back empty and the manifest called that
    # complete coverage with no net change.
    diff_set = write_review_diff(
        scope.base_ref, scope.changed_files, detach_phase_dir, scope.collapse_paths,
        scope_source=describe_scope_source(
            scope.review_scope.source, scope.base_ref, scope.pinned,
        ),
        cwd=scope.git_root,
        **({"head_ref": scope.pinned.head} if scope.pinned is not None else {}),
    )

    # A new round (not a resume of the missing models) records which
    # review is on record, through this phase's own `state`, the instance
    # it saves at the end: a commit brief's
    # `reviewed_header_sha256` (and its apply guard cleared), a direct
    # round's `head_ref`, or — a round with neither — no `head_ref`.
    if round_starts(
        detach_phase_dir, model_specs, diff_set.scope_id,
        rerun_all=bool(getattr(args, "rerun_all", False)),
    ) and record_round_start(state, scope.pinned):
        state.save()
    return diff_set


@dataclasses.dataclass(frozen=True)
class _ClosedFanout:
    """What :func:`_run_reviews_and_save` hands the round: the phase dir, the
    lane, each slot's ``(success, issues, details)`` after the fan-out's close
    (a salvaged model holds its repaired issues), the failed and salvaged
    models, and the served-model and usage maps the report prints."""

    phase_dir: Path
    lane: CodeLane
    results: Dict[str, Tuple[bool, Any, Any]]
    failed_models: Dict[str, Any]
    salvaged_models: Set[str]
    served_models: Dict[str, Dict[str, Any]]
    usage: Dict[str, Dict[str, Any]]


async def _run_reviews_and_save(
    args: argparse.Namespace, scope: RunScope, claim: "_review_round.Claim",
    diff_set: Any, *, plan_path: Path, out_dir: Path, prefix: str,
    detach_phase_dir: Path, model_specs: List[str],
    scope_round_policy: "_scope_round.RoundPolicy", unattended: bool,
    opening: "_review_lane.RoundOpening",
) -> _ClosedFanout:
    """The fan-out over the diff set, closed by the shared lane.

    ``run_all_reviews`` runs the slots; :func:`utils.review_lane.close_fanout`
    saves each, names the losses, salvages in-process under
    ``--exec-subagents`` and exits 3 when no model answered.
    """
    # Filled per slot by run_single_review when a configured fallback
    # served the turn; empty under the shipped config, which is what keeps the
    # report identical.
    served_models: Dict[str, Dict[str, Any]] = {}
    # Stage U: filled per slot by run_single_review from `details["usage"]`,
    # for the slots that failed as much as the ones that answered. Empty for a
    # fan-out of adapters that report nothing, which keeps this run's
    # checkpoint and report exactly what they were.
    usage: Dict[str, Dict[str, Any]] = {}
    # The fan-out builds its own tracker — it seeds the map before the first
    # dispatch, owns the `[PROGRESS]` ticker and sweeps in its own `finally` —
    # and hands it back here, because F11's backfill runs at this level and has
    # to give the map the same treatment it gives `failed_models`. Same
    # collector idiom, and the same reason, as `served_models` and `usage`
    # above: `run_all_reviews`' return value is destructured by every caller.
    fanout_trackers: List[FanoutProgress] = []

    # A model whose spec changed since the last run (`codex:x` becoming
    # `codex:x:high`) has no slot in this run to retire its old files, and a
    # later `--reaggregate` would read them back into this run's report.
    retire_unselected_results(str(detach_phase_dir), model_specs)

    # Run reviews - agents receive the resolved, ordered scope (labelled
    # with its source), the diff set, and the base ref
    results = await run_all_reviews(
        model_specs,
        plan_path,
        out_dir,
        args.timeout,  # May be None - run_all_reviews will use per-provider defaults
        args.max_parallel,
        scope.changed_files,
        scope.base_ref,
        skip_existing=not args.rerun_all,
        served_models=served_models,
        usage=usage,
        prior_usage=opening.prior_usage,
        tracker_out=fanout_trackers,
        scope_source=scope.review_scope.source,
        task_ids=scope.review_scope.task_ids,
        scope_file=diff_set.scope_file,
        diff_dir=diff_set.diff_dir,
        scope_id=diff_set.scope_id,
        diff_coverage=diff_set.coverage,
        **scope.pinned_kw,
        **(
            {"scope_policy": scope_round_policy.policy}
            if scope_round_policy.policy != _sp.DEFAULT_POLICY else {}
        ),
    )

    # Get the phase directory for code review outputs
    phase_dir = get_phase_dir(plan_path, 'code-review')
    phase_dir.mkdir(parents=True, exist_ok=True)

    # Everything between the fan-out and grouping, written once for both
    # review lanes (utils/review_lane.py): each slot saved, the deadline's
    # losses named, the round checked, the bypassed slots recorded, salvage
    # run in-process under `--exec-subagents` (a repaired model's issues
    # join the round), and the exit 3 of a run where no model answered.
    lane = CodeLane(plan_path=plan_path, phase_dir=phase_dir, prefix=prefix)
    closed = await _review_lane.close_fanout(
        lane,
        claim, args,
        model_specs=model_specs, results=results,
        served_models=served_models, usage=usage, prior_served=opening.prior_served,
        tracker=fanout_trackers[0] if fanout_trackers else None,
        unattended=unattended,
    )
    failed_models = closed.failed_models
    # The round is aggregated from these slots, not from the files: a slot
    # whose issues could not be saved is failed here, a salvaged one holds
    # its repaired issues.
    results = {spec: slot.as_review() for spec, slot in closed.slots.items()}
    salvaged_models = {sanitize_model_name(spec) for spec in closed.salvaged}
    return _ClosedFanout(
        phase_dir=phase_dir, lane=lane, results=results,
        failed_models=failed_models, salvaged_models=salvaged_models,
        served_models=served_models, usage=usage,
    )


@dataclasses.dataclass(frozen=True)
class _ReviewOutcome:
    """A finished round, for the run's ending: the groups the report
    carries, every raw issue, and the fix tasks file (``--apply-fixes``)."""

    groups: Optional[List[Dict[str, Any]]]
    all_issues: List[Dict[str, Any]]
    fix_tasks_path: Any


async def _group_validate_and_report(
    args: argparse.Namespace, state: Any, scope: RunScope,
    claim: "_review_round.Claim", diff_set: Any, slots: _ClosedFanout, *,
    plan_path: Path, out_dir: Path, model_specs: List[str],
    plan_document_at_load: Optional[BoundDocument],
    scope_round_policy: "_scope_round.RoundPolicy",
) -> Optional[_ReviewOutcome]:
    """Everything after the fan-out, under the phase-scoped ticker.

    The raw issues saved, grouped and validated (:func:`_group_and_validate`),
    the fix tasks prepared under ``--apply-fixes``, the report published and
    the phase recorded complete (:func:`_publish_report`). ``None`` when the
    validation round was handed to the host, which comes back with
    ``--reaggregate``. The ticker is stopped, and the closing summary
    printed, on every ending, after the terminal ``progress.step``.
    """
    phase_dir = slots.phase_dir
    # T5: the fan-out is not the phase. `run_all_reviews` returned the
    # moment its last slot did, and everything below keeps this phase
    # working for minutes — grouping, the reviewed-code and plan excerpts,
    # validation-batch preparation, and under `--exec-subagents` the whole
    # validation dispatch and merge in-process. Without a second ticker that
    # window is where the log goes quiet, now at the *end* of the run instead
    # of throughout it.
    #
    # Started here rather than hoisted around the fan-out: lifetime rule 1
    # requires the fan-out's own ticker to be cancelled and awaited before
    # its per-model summary is printed (in the fan-out), and this one must not
    # interleave with that summary either.
    #
    # It has no per-model map and never touches `models`: it prints the step,
    # its own elapsed, and whatever counters the current step already
    # publishes — `progress.subagents`, which
    # `task_batch._mirror_status` writes straight through
    # `update_status` on every outcome. So the map the sweep froze stays
    # frozen, and a table rendered while validation runs still shows each
    # model's real duration rather than a clock that kept ticking after the
    # model finished.
    #
    # Cancelled *and awaited* in the `finally`, after the phase has written
    # its terminal `progress.step`, so the log's last `[PROGRESS]` reads
    # `step: complete` rather than trailing off at whatever step the last
    # interval caught. The `finally` is what covers the other two endings
    # this block has: the `return` that hands validation to the host
    # ("Exit early - Claude Code handles validation"), and a `sys.exit` out
    # of a refused task file.
    phase_ticker = PhaseProgress(str(phase_dir), anchor=str(plan_path))
    phase_ticker.start_ticker()
    # One loop turn, so the task actually enters its body. A task cancelled
    # before it has ever been scheduled is closed without running its
    # `finally`, and that `finally` is where the teardown line carrying the
    # terminal step comes from — the whole reason this ticker is stopped
    # *after* `progress.step` is written.
    #
    # It is no longer the ONLY turn the loop gets, but most of this stretch
    # still does not yield. `dispatch_subagent_tasks` is
    # the long one — it blocks in `_run_sync`'s
    # `pool.submit(asyncio.run, …).result()` for the whole validation
    # window, which used to pin this loop and leave the executor lane with
    # exactly one `[PROGRESS]` line, the teardown one — and it is awaited
    # off the loop (`phase_thread`) below, so the ticker gets its interval
    # for those minutes. Everything around it — grouping, the excerpts,
    # `materialize_validation_round`, the merge — is still synchronous,
    # so an interval expiring inside them is serviced only once they
    # return. Moving those off the loop as well is a larger change than
    # this one.
    await asyncio.sleep(0)
    try:
        all_issues = _save_raw_issues(slots.results, plan_path=plan_path)
        validated = await _group_and_validate(
            args, state, scope, claim, slots, all_issues, plan_path=plan_path,
            plan_document_at_load=plan_document_at_load,
            scope_round_policy=scope_round_policy,
        )
        if validated is None:
            return None  # the host runs the round and comes back with --reaggregate

        fix_tasks_path = None
        # Prepare fix tasks for Claude Code subagents if requested
        if args.apply_fixes and validated.groups:
            fix_tasks_path = prepare_fixes_for_subagents(
                validated.groups,
                plan_path,
                out_dir
            )

        _publish_report(
            args, state, scope, claim, diff_set, slots, validated,
            plan_path=plan_path, model_specs=model_specs,
        )
    finally:
        await phase_ticker.stop_ticker()
        # Every
        # `[CODEX_HOME_CHECK]` and `[JAIL_DENIED]` line of this run's
        # slots, repeated — on every ending this `finally` covers.
        print_closing_summary(str(phase_dir))
    return _ReviewOutcome(
        groups=validated.groups, all_issues=all_issues, fix_tasks_path=fix_tasks_path,
    )


#: A line number, a ``"40-42"`` range (hyphen, en dash or colon) or an
#: ``"L40-L42"`` one, as text.
_LINE_TEXT_RE = re.compile(r"\s*L?(\d+)\s*(?:[-\u2013:]\s*L?(\d+))?\s*")


def _line_number(value: Any) -> Optional[int]:
    """*value* as a line number, ``None`` when it is not one."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str) and value.strip().isdecimal():
        return int(value.strip())
    return None


def _usable_line_range(value: Any) -> Optional[List[int]]:
    """*value* as the ``[start, end]`` the schema asks for, ``None`` when no
    line can be read from it. One line (``[42]``, ``42``, ``"42"``) is
    ``[42, 42]``."""
    if isinstance(value, (list, tuple)):
        numbers = [_line_number(item) for item in value[:2]]
        if not numbers or None in numbers:
            return None
        return [numbers[0], numbers[-1]]
    if isinstance(value, str):
        match = _LINE_TEXT_RE.fullmatch(value)
        if not match:
            return None
        start = int(match.group(1))
        return [start, int(match.group(2)) if match.group(2) else start]
    number = _line_number(value)
    return None if number is None else [number, number]


def normalize_issue_shapes(issues: List[Dict[str, Any]], model: str) -> None:
    """Give each issue's ``title``, ``file`` and ``line_range`` the shapes
    every reader takes, in place, with one warning naming *model* and what
    changed.

    All three are model output, and the report, the grouping, the issue map
    and fix batching key on ``title`` and ``file`` and read ``line_range`` as
    ``[start, end]`` (the issue schema), so a reply of another shape must not
    crash the report after every model ran, and every ``--reaggregate`` after
    it. A title that is a list or an object becomes its text, a path list
    keeps its first path, one line becomes ``[n, n]``, and a field nothing
    usable can be read from is removed; the issue itself is always kept. Run
    on arrival, where importance is canonicalized: the fan-out's issues and
    every reaggregate's read-back, so both group the same records
    (docs/development/review-results.md, "Malformed result entries").
    """
    changes: List[str] = []
    for number, issue in enumerate(issues, 1):
        title = issue.get("title")
        if isinstance(title, (list, tuple, dict)):
            issue["title"] = (
                " ".join(str(part) for part in title)
                if not isinstance(title, dict) else json.dumps(title, sort_keys=True)
            )
            changes.append(f"issue {number}: title {title!r} -> {issue['title']!r}")
        label = f"issue {number} ({report_markdown.inline_text(issue.get('title'))[:60]!r})"
        if "file" in issue and not isinstance(issue["file"], str):
            raw = issue["file"]
            paths = [p for p in raw if isinstance(p, str) and p] if isinstance(raw, (list, tuple)) else []
            if paths:
                issue["file"] = paths[0]
                changes.append(f"{label}: file {raw!r} -> {paths[0]!r}")
            else:
                del issue["file"]
                changes.append(f"{label}: file {raw!r} removed")
        raw_range = issue.get("line_range")
        if raw_range is None or (
            isinstance(raw_range, list) and len(raw_range) == 2
            and all(type(line) is int for line in raw_range)
        ):
            continue
        usable = _usable_line_range(raw_range)
        if usable is None:
            del issue["line_range"]
            changes.append(f"{label}: line_range {raw_range!r} removed")
        else:
            issue["line_range"] = usable
            changes.append(f"{label}: line_range {raw_range!r} -> {usable!r}")
    if changes:
        listed = "; ".join(changes[:3]) + ("; …" if len(changes) > 3 else "")
        print(
            f"WARNING: {model} gave {len(changes)} issue field(s) in a shape "
            f"the report cannot use: {listed}.\n  Normalised; every issue is "
            f"kept, and every other model's are aggregated as usual.",
            file=sys.stderr,
        )


def _save_raw_issues(
    results: Mapping[str, Tuple[bool, Any, Any]], *, plan_path: Path,
) -> List[Dict[str, Any]]:
    """Every answering slot's issues, stamped with the slot's spec, written to
    ``issues.json`` (an empty list too) and returned."""
    # Save raw issues as JSON
    all_issues = []
    for model_spec, (success, issues, _) in results.items():
        if success and issues:
            records = drop_non_record_entries(issues, model_spec, noun="issues")
            normalize_issue_shapes(records, model_spec)
            for issue in records:
                issue["model"] = model_spec
                all_issues.append(issue)
    # An in-process salvage's file reaches `results` in the case it
    # was written in.
    _importance.canonicalize(all_issues)

    # An empty successful review replaces the previous findings too.
    # Otherwise --force can report zero issues while apply-code-fixes
    # still reads and applies the previous run's groups.
    issues_path = get_output_paths(plan_path, "code_review_issues", phase='code-review')
    issues_path = issues_path.with_suffix(".json")
    with open(issues_path, "w", encoding="utf-8") as f:
        json.dump(all_issues, f, indent=2)
    print(f"Issues JSON saved to: {issues_path}")
    return all_issues


@dataclasses.dataclass(frozen=True)
class _ValidatedRound:
    """The grouping's outcome for the report: the groups it carries, the
    ``validation.json`` bytes their verdicts come from (``None`` when none
    do), the round's steps and the commit-attribution pass."""

    groups: Optional[List[Dict[str, Any]]]
    verdicts: Optional["_review_round.Verdicts"]
    steps: "_review_lane.RoundSteps"
    commit_attribution: Any


async def _group_and_validate(
    args: argparse.Namespace, state: Any, scope: RunScope,
    claim: "_review_round.Claim", slots: _ClosedFanout,
    all_issues: List[Dict[str, Any]], *, plan_path: Path,
    plan_document_at_load: Optional[BoundDocument],
    scope_round_policy: "_scope_round.RoundPolicy",
) -> Optional[_ValidatedRound]:
    """The issues grouped and their validation round resolved.

    Zero groups need no round, ``--skip-validation`` reports the groups as
    grouped, and otherwise the shared lane publishes, dispatches or hands out
    the round (:func:`utils.review_lane.materialize_fanout_round`). ``None``
    when it was handed to the host.
    """
    phase_dir = slots.phase_dir
    # Group similar issues and validate
    validated_groups_for_report = None
    # The validation.json bytes the report's verdicts come from, when they do.
    verdicts: Optional[_review_round.Verdicts] = None
    # The slot that returned an issue is its reviewer, whatever
    # `source_model` the reply claims: grouping attributes by it and the
    # reports print it (docs/development.md#vendored-report-scripts).
    for issue in all_issues:
        issue["source_model"] = issue["model"]
    grouped_path = get_output_paths(plan_path, "code_review_grouped", phase='code-review')
    validation_path = get_output_paths(plan_path, "code_review_validation", phase='code-review')
    steps = code_round_steps()
    # The grouping and its round, one rule for every review lane
    # (utils/review_lane.py): grouped.json replaced with the previous
    # verdicts retired in the same step, or, for zero issues, a
    # finished review with zero groups whose whole previous round
    # retires (otherwise --force could report zero issues while
    # apply-code-fixes still applied the previous run's groups). A commit review names
    # the commit behind each group, as sibling
    # fields written before grouped.json (off the hash).
    grouping = _review_lane.group_findings(
        claim, steps, phase_dir=str(phase_dir), grouped_path=str(grouped_path),
        validation_path=str(validation_path), records=all_issues,
        noun="issues",
        annotate=lambda groups: attribute_review_groups(
            groups, state, repo_root=scope.git_root or scope.project_root
        ),
    )
    # The stamped groups (`group_hash`, `display_label`) grouped.json was
    # written from: the decisions overlay joins on `group_hash`, so every
    # group reported downstream must carry it.
    grouped_list = grouping.groups
    commit_attribution_pass = grouping.annotation

    if not grouped_list:
        validated_groups_for_report = []
    elif args.skip_validation:
        print("\nSkipping validation (--skip-validation flag set)")
        # The groups on disk, so `--apply-fixes` and the HIGH-group count
        # see them.
        validated_groups_for_report = grouped_list
    else:
        outcome = await _review_lane.materialize_fanout_round(
            slots.lane, claim, args, steps,
            grouped=grouped_list, validation_path=str(validation_path),
            # The plan bound at load, before the fan-out, to this phase
            # dir's own `validation-snapshot.md`, never a
            # re-read of a plan edited while the models ran.
            plan_document=lambda: plan_document_at_load or bind_plan_for_validation(
                str(plan_path), str(phase_dir)
            ),
            build_round=lambda document: code_review_validation_round(
                grouped_list,
                args=args, plan_path=plan_path, phase_dir=phase_dir,
                plan_document=document, base_ref=scope.base_ref,
                project_root=scope.project_root, git_root=scope.git_root,
                pinned=scope.pinned,
                plan_snapshot=scope.plan_snapshot, plan_sha256=scope.plan_sha256,
                scope_round_policy=scope_round_policy, state=state,
                round_id=claim.round_id,
            ),
        )
        if outcome.handed_off:
            return None  # the host runs the round and comes back with --reaggregate
        validated_groups_for_report = outcome.groups
        verdicts = outcome.verdicts
    return _ValidatedRound(
        groups=validated_groups_for_report, verdicts=verdicts, steps=steps,
        commit_attribution=commit_attribution_pass,
    )


def _publish_report(
    args: argparse.Namespace, state: Any, scope: RunScope,
    claim: "_review_round.Claim", diff_set: Any, slots: _ClosedFanout,
    validated: _ValidatedRound, *, plan_path: Path, model_specs: List[str],
) -> None:
    """The report generated, published sealed with this round's line, its
    files handed back, and the phase recorded complete (the terminal
    ``progress.step``)."""
    phase_dir = slots.phase_dir
    # Generate report (after validation so we can include validation status)
    # F10: `failed_models` is this run's own authoritative post-salvage map
    # (and, since F11, includes any model that never returned at all) —
    # passed in rather than left for the function to re-derive.
    report = generate_review_report(
        plan_path, slots.results, scope.changed_files, validated.groups,
        # The commit header, "Introduced by" lines and filter.
        commit_review=commit_report.report_context(
            state, validated.commit_attribution, scope.changed_files,
            repo_root=scope.git_root or scope.project_root,
        ),
        phase_dir=phase_dir, base_ref=scope.base_ref, template_style=args.report_style,
        served_models=slots.served_models or None,
        usage=slots.usage or None,
        failed_models=slots.failed_models,
        #  T5.2: "N of M requested" counts this run's own specs.
        requested_models=len(model_specs),
        # D2.2: the diff set this fan-out wrote before dispatch.
        review_scope=review_scope_record(
            phase_dir,
            scope_id=diff_set.scope_id,
            base_ref=diff_set.base_ref,
            base_commit=diff_set.base_commit,
            written_by=diff_set.written_by,
            coverage=diff_set.coverage,
            omitted=list(diff_set.omitted),
            # Every result here was either run against this set or
            # reused because the ledger ties it to this set, so even
            # a set an earlier reaggregate wrote (left untouched,
            # same id) is the one the reviewers were shown.
            results_match=True,
        ),
        **(
            {"pinned": scope.pinned, "repo_root": scope.git_root}
            if scope.pinned is not None else {}
        ),
    )

    # Save report: published whole and sealed with this round's line
    # (utils/review_round.py, "the report's seal").
    report_path = get_output_paths(plan_path, "code_review", phase='code-review')
    report_path = report_path.with_suffix(".md")
    _review_round.publish_report(report_path, report, claim=claim,
                                 verdicts=validated.verdicts)
    print(f"\nReport saved to: {report_path}")

    # The report's files handed back on both channels, one rule for
    # every review lane (utils/review_lane.py). validation.json and
    # issues.json are included (F3): apply-code-fixes reads exactly
    # those two files, and a missing validation.json makes it treat
    # every group as needs-human-decision.
    _review_lane.hand_back_report(
        validated.steps, phase_dir, report=report_path,
        grouped=phase_dir / "grouped.json",
        validation=phase_dir / "validation.json",
        issues=phase_dir / "issues.json",
    )

    # The phase recorded complete in this run's `state`, while the round
    # on record is still this run's, and the in-phase machine's
    # terminal word, which `status` renders.
    _review_lane.record_phase_complete(
        claim, validated.steps, state=state, phase_name="code-review",
        phase_dir=str(phase_dir),
    )


def _announce_fix_tasks(args: argparse.Namespace, outcome: _ReviewOutcome) -> None:
    """The ``--apply-fixes`` hand-off: the fix tasks file and what the invoker
    must do with it, when tasks were prepared."""
    # Report fix tasks if prepared
    if args.apply_fixes and outcome.fix_tasks_path:
        valid_count = len([
            g for g in (outcome.groups or []) if g.get("validation_status") == "valid"
        ])
        print(f"\n{'='*60}")
        print("IMPORTANT: SUBAGENT DELEGATION REQUIRED")
        print(f"{'='*60}")
        print(f"\nValid issues to fix: {valid_count}")
        print(f"Fix tasks file: {outcome.fix_tasks_path}")
        # Host-neutral: the invoker runs task.prompt and persists what comes
        # back. No agent-type vocabulary, which is also what keeps the
        # forbidden-token lint green on printed text.
        print("\nThe invoker MUST NOW:")
        print("1. Read the fix tasks JSON file")
        print("2. For each task, run task.prompt as a subagent, then write the")
        print("   JSON it returns to task.output_path")
        print("3. DO NOT implement fixes manually - delegate every task")
        print("4. After all fixes complete, update the code review file with results")
        print("5. Update the original plan file to reference the code review")
        print(f"{'='*60}\n")


def _announce_pending_salvage(
    phase_dir: Path, plan_path: Path, salvaged_models: Set[str],
) -> None:
    """The salvage requests still pending, and the ``--reaggregate`` that
    follows them (``[REAGGREGATE_AFTER_SALVAGE]``, also the result line's
    ``next``)."""
    # Check for salvage requests and print reaggregate command
    salvage_pattern = str(phase_dir / "salvage_*.json")
    # emit_salvage_task writes salvage_task_<model>.json beside each
    # salvage_<model>.json and the glob matches both, so one failed model would
    # be counted twice and the task file would yield a bogus model name
    # ("task_<model>") pointing the invoker at an output filename
    # reaggregation never reads. Only the request files are salvage requests.
    salvage_files = [
        path for path in glob_module.glob(salvage_pattern)
        if not os.path.basename(path).startswith("salvage_task_")
    ]

    if salvaged_models:
        # A model this run already repaired in-process is not pending salvage.
        # Its request file stays on disk as the audit trail, but it must not put
        # the host back on the salvage-then-reaggregate path.
        salvage_files = [
            path for path in salvage_files
            if os.path.basename(path) not in {
                f"salvage_{model}.json" for model in salvaged_models
            }
        ]

    if salvage_files:
        print("")
        print("=" * 60)
        print("SALVAGE NEEDED")
        print("=" * 60)
        print(f"Models requiring salvage: {len(salvage_files)}")
        for i, salvage_path in enumerate(salvage_files, 1):
            # Extract model name from filename
            basename = os.path.basename(salvage_path)
            model_name = basename.replace("salvage_", "").replace(".json", "")
            output_file = f"{model_name}.json"
            print(f"  {i}. {model_name} -> {basename}")
            print(f"     Output: {output_file}")

        # Print the reaggregate command for the host to use after salvage.
        # Fully resolved (see above) and still `uv run …`-prefixed.
        salvage_reaggregate_cmd = commit_spelling.spell_retry_command(
            'review-code', plan_path, '--reaggregate',
            typed_plan=cli_common.typed_plan_for(plan_path),
            flags=cli_common.current_replay_flags(mode='review-code'),
        )
        print("")
        print(f"[REAGGREGATE_AFTER_SALVAGE] {salvage_reaggregate_cmd}")
        record_next(salvage_reaggregate_cmd)
        print("")
        # F13: host-neutral — this prints into the run log of whatever host is
        # driving, not only Claude Code.
        print("After all salvage subagents complete, run the above command to regenerate grouped/validation/report files.")


if __name__ == "__main__":
    from utils import process_control

    # A process entry of its own: provider children must stay this process's.
    process_control.restore_sigchld_default()
    sys.exit(asyncio.run(main(sys.argv[1:])))
