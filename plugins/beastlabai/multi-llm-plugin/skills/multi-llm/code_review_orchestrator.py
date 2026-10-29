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
import hashlib
import json
import os
import posixpath
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, NamedTuple, Optional, Sequence, Tuple

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils import (
    get_or_create_state,
    load_prompt,
    get_output_paths,
    drop_non_record_entries,
    validate_code_review_issues,
    get_files_changed_since_ref,
    group_similar_suggestions,
    export_groups_to_json,
    validate_groups,
    sanitize_prefix,
    intent_to_add_untracked,
    subtract_baseline,
    PlanUpdater,
)
from utils.stream_bootstrap import bootstrap_streams
from utils.text_clip import clip
from utils import cli_common
from utils import prior_changes
from utils.cli_common import (
    EXIT_NEEDS_HUMAN,
    EXIT_OK,
    build_parent_parser,
    dispatcher_prefix,
    reaggregate_command,
    record_next,
)
from utils.report_parser import issue_numbering_footer
# plans/review-commits.md §2.6/§2.10: a commit brief's run (its state records
# `commit_range`) gets the commit template, attribution and report header.
from utils import commit_report
from utils import commit_spelling
from utils.commit_attribution import attribute_review_groups
from utils.state_manager import (
    load_groups_payload,
    match_issues_to_suggestions,
    save_groups_payload,
    stamp_stable_ids,
    CURRENT_FORMAT_VERSION,
)
from utils.output_handler import (
    get_phase_dir, output_dir_path, phase_dir_path, workflow_file_entries,
)
from utils.detach import record_output_files, report_progress
from utils.progress_tracker import DEADLINE_ERROR, FanoutProgress, PhaseProgress
from utils.readonly_audit import combine_audits
from utils.review_orchestrator_base import (
    RETIRE_SUPERSEDED,
    backfill_deadline_losses,
    dispatch_salvage_tasks,
    dispatch_subagent_tasks,
    exec_subagents_requested,
    grouped_coverage_gap,
    maybe_detach,
    merge_validation_batches,
    record_high_priority_groups,
    record_validation_counts,
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
    fanout_ignore_prefixes,
    boundaryless_sibling_count,
    bypass_stream_audit_clears,
    bypass_write_not_attributed,
    bypass_write_violation,
    porcelain_check_applies,
    porcelain_snapshot,
    # Plan codex-sandbox-unavailable §6 F1 (2026-09-30): a slot on the
    # plugin's own jail runs the mode check and the home check instead.
    jail_record_fields,
    mode_check_applies,
    mode_snapshot,
    print_closing_summary,
    report_jail_outcome,
    run_incidental_checks,
    record_sandbox_bypassed,
    recorded_served_models,
    recorded_usage,
    # Plan §5: what a reaggregate says about the models that produced nothing.
    announce_remaining_failures,
    exit_when_every_reviewer_failed,
    remaining_failed_models,
    salvage_requested_models,
    sandbox_fallback_kwargs,
    sandbox_refusal,
    spawn_fanout_slot,
    unexpected_writes,
    update_status,
    write_status,
)
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
from utils.validation import (
    VALIDATION_CONTEXT_LIMIT,
    BoundDocument,
    ValidationContextError,
    bind_document_text,
    decode_document,
    excerpt_context_reported,
    legacy_context_round_reason,
    prepare_batched_validation_tasks,
    resolved_reaggregate_command,
)
from utils.subagent_prompts import (
    CODE_REVIEW_VALIDATION_GUIDANCE,
    code_review_validation_guidance,
)
from utils.subagent_tasks import (
    TaskFileError,
    build_inputs,
    read_task_file,
    write_salvage_task_file,
)
from utils.interactive import resolve_models
from utils import unattended as unattended_mod
from utils.unattended import NeedsHuman
from utils.provider_registry import (
    get_all_model_specs,
    get_collapse_paths,
    parse_model_spec,
    get_provider_timeout,
    get_provider_max_concurrent,
    is_model_valid,
    set_run_anchor,
)
from utils.json_extractor import (
    build_unsanitize_map,
    generate_output_path,
    has_salvageable_json,
    read_json_from_file,
    sanitize_model_name,
)
from utils.llm_client import (
    INLINE_MANIFEST_LABEL,
    INLINE_PROMPT_CAP_BYTES,
    argv_prompt_bytes,
    describe_output_file,
    describe_usage,
    invoke_with_file_output,
    invoke_with_provider,
    misnamed_result_baseline,
    render_diff_access,
    sandbox_record_word,
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
    _run_git,
)
from utils.html_report_generator import generate_html_report, write_html_report, model_label, served_model_label, VALIDATION_ORDER, UNKNOWN_STATUS_RANK
from utils.html_report_generator import failed_models_line
from utils.commit_review import commit_review_artifact, commit_reviews_folder_rel
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


#: Name fragments of the phase dir's ``*.json`` files that are not a model's
#: result, for :func:`leftover_model_results`.
_NOT_A_MODEL_RESULT = ('grouped', 'validation', 'salvage', 'issues', 'fix_tasks',
                       'state', '.status', 'report_data')


def leftover_model_results(phase_dir: Any) -> List[str]:
    """The per-model result files in *phase_dir* (``<stem>.json``), sorted.

    What the partial-completion guard refuses a plain re-run over when no
    ``grouped.json`` is beside them, and what ``improve_workflow.read_records``
    reads as a fan-out cut off before grouping, which its review step resumes
    with ``--force`` (Fable review 2026-10-27, finding 1).
    """
    import glob as glob_module

    return sorted(
        f for f in glob_module.glob(str(Path(phase_dir) / "*.json"))
        if not any(ex in os.path.basename(f) for ex in _NOT_A_MODEL_RESULT)
    )


def save_model_result(
    prefix: str,
    model: str,
    success: bool,
    issues: Optional[List[Dict]],
    error: Optional[str],
    phase_dir: Path
) -> bool:
    """Save per-model code review result to file."""
    sanitized_model = sanitize_model_name(model)

    if success and issues is not None:
        result_path = phase_dir / f"{sanitized_model}.json"
        with open(result_path, 'w', encoding='utf-8') as f:
            json.dump(issues, f, indent=2)
        print(f"[{model}] Saved {len(issues)} issues to: {result_path}")
        return True
    elif error:
        error_path = phase_dir / f"error_{sanitized_model}.log"
        with open(error_path, 'w', encoding='utf-8') as f:
            f.write(f"Model: {model}\n")
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            f.write(f"Error: {error}\n")
        print(f"[{model}] Error logged to: {error_path}")
        return False
    return False


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

    # A commit front door's `--detach` stage (plans/review-commits.md §2.1):
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

    # plans/review-commits.md §2.5: a two-commit review. A real flag, because
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

    return parser.parse_args(argv)


def load_code_review_prompt() -> str:
    """Load the code review prompt template."""
    return load_prompt("code_review.txt")


#: Where a review's scope came from (:attr:`ReviewScope.source`), in the order
#: :func:`resolve_review_scope` tries them. ``commit_range`` is a review pinned
#: to two commits (``--head-ref``, plans/review-commits.md §2.5): ``git diff
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
# (plans/review-commits.md §2.4, §2.5)
# ---------------------------------------------------------------------------
#
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

    In order (§2.5 "One reader"):

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
        # pair would silently be `head..head` or inverted (§2.2, §2.5). Only
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
    cannot change which commits they review (§2.5 "Record and replay"). Every
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
    ``--commit-stage``, plans/review-commits.md §2.1). The worker applies it
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

    Through the ``StateManager`` the phase already holds and saves (§2.1 "The
    phase writes through the instance it saves with"):

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
    with the one change test (``git_utils.paths_changed_since``, §2.5
    "Drift"), in the pre-flight, so the line reaches the caller's terminal
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

    With ``head_ref`` (a review pinned to two commits, plans/review-commits.md
    §2.5) the range decides, ahead of everything below: ``git diff
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
    Changed:** 0`` in every ``report.md`` its reaggregate wrote (measured
    2026-09-17). The fallback is the same live computation either way, so it is
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
    # fallback sees the plan the planning phases edited (2026-10-05, Codex
    # racing run 3: `tasks.md` reviewed as code, two duplicate findings).
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
    report folder goes as a class (``commit_review.commit_review_artifact``,
    plans/review-commits.md §2.4), on every mode and whatever plan the run
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
    source — read exactly like a scoped review (review-scope plan §2.1, D2.5).
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
        # naming its 200 phase artifacts buried the one new source file
        # (2026-10-05, Codex racing run 3: `index.html` among them).
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


def resolve_changed_files(state: Any, base_ref: Optional[str]) -> List[str]:
    """The paths of :func:`resolve_review_scope`, for a caller that needs no label.

    The reaggregate path uses this: it dispatches no reviewer, so it needs only
    the paths (and the same printed lines). No order is promised.
    """
    return resolve_review_scope(state, base_ref).paths


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
    excerpted once per phase and reused by every batch
    (``utils.validation.excerpt_context``, ``VALIDATION_CONTEXT_LIMIT``), so
    what goes in it has to fit that budget for the whole phase. A review of a
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

    ``pinned`` reads every window at the review's head commit instead of disk
    (plans/review-commits.md §2.5), so the excerpt — and the
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
    (plans/review-commits.md §2.5, "Paths in git's form") and are normalised.
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
    only (§2.5 "Deleted or renamed: the label"). ``kind`` is
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
        stdout, _, rc = _run_git(
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
    the working tree moves (plans/review-commits.md §2.5, "Validation
    excerpts"). One ``paths_in_commit`` and one ``git cat-file --batch`` over
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
        # (`--human-task <id>=done` after a failed check, fix round 8): the
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
        # edits were kept, recorded `completed` (fix round 15).
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
    as a ``reviewed-code`` context source with ``mode: truncated`` (§2.6).
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
    if len(embedded) > code_budget:
        # Re-cut by whole files rather than letting the caller's shared excerpt
        # slice the last file mid-window. The files were read once, above; only
        # the fit is redone. The stderr line names the files that went, not a
        # char count, because "which cited file has no window" is the question
        # a verdict about an unshown file raises.
        embedded, dropped = _fit_reviewed_code_sections(
            sections,
            code_budget,
            unnamed=frozenset(path for path, on_disk in inside.items() if on_disk is None),
        )
        print(
            f"[VALIDATION_CONTEXT_TRUNCATED] reviewed-code "
            f"{len(reviewed_code) - code_budget} chars over; windows for "
            f"{len(dropped)} of {len(sections)} cited files not shown: "
            + ", ".join(dropped),
            file=sys.stderr,
        )
    else:
        dropped = []
    if cut_report is not None:
        cut_report["record_cut"] = len(raw_record) > IMPLEMENTATION_RECORD_CHARS
        cut_report["record_chars"] = len(raw_record)
        cut_report["dropped_files"] = list(dropped)
        cut_report["files_total"] = len(sections)
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
        cut_report["open_paths"] = open_paths

    parts = [record_part]
    if embedded:
        parts.append(f"{code_heading}{embedded}")
    return "\n\n".join(parts), reviewed_code


def validation_extra_instructions(
    cut_report: Dict[str, Any],
    *,
    pinned: Optional[PinnedRange] = None,
    plan_snapshot: Optional[str] = None,
    plan_sha256: Optional[str] = None,
) -> str:
    """``extra_instructions`` for a code-review validation batch.

    On a review pinned to two commits (*pinned*) the guidance states the
    pinned-head read rule, with the §2.6 trust sentence, for every file
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
    """The ``reviewed-code`` context source for review-code's second block (§2.6).

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
            "importance": issue.get("importance", "medium"),
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


def update_plan_with_fixes(
    plan_path: Path,
    fix_results: List[Dict]
) -> None:
    """
    Update the plan file to document what was fixed during review.

    Args:
        plan_path: Path to the plan file
        fix_results: List of fix results
    """
    if not fix_results:
        return

    # Validate input
    if not isinstance(fix_results, list):
        print(f"ERROR: fix_results must be a list, got {type(fix_results)}")
        return

    try:
        updater = PlanUpdater(plan_path)
    except Exception as e:
        print(f"ERROR: Failed to load plan file for update: {e}")
        return

    # Build the fixes section content
    fixed_count = sum(1 for r in fix_results if r.get("fixed"))
    failed_count = len(fix_results) - fixed_count

    lines = [
        "",
        "<!-- REVIEW_FIXES_START -->",
        "",
        "## Review Fixes Applied",
        "",
        f"*Applied: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
        "",
        f"**Summary:** {fixed_count} fixed, {failed_count} could not be fixed",
        "",
    ]

    # List fixed issues
    fixed_items = [r for r in fix_results if r.get("fixed")]
    if fixed_items:
        lines.append("### Successfully Fixed")
        lines.append("")
        for item in fixed_items:
            lines.append(f"- **{item.get('issue_title', 'Unknown')}**")
            if item.get("changes_made"):
                lines.append(f"  - {item['changes_made']}")
            if item.get("files_modified"):
                for file_mod in item["files_modified"]:
                    path = file_mod.get("path", "unknown")
                    summary = file_mod.get("summary", "")
                    if summary:
                        lines.append(f"  - `{path}`: {summary}")
                    else:
                        lines.append(f"  - `{path}`")
        lines.append("")

    # List failed fixes
    failed_items = [r for r in fix_results if not r.get("fixed")]
    if failed_items:
        lines.append("### Could Not Fix")
        lines.append("")
        for item in failed_items:
            reason = clip(item.get("reason") or "Unknown reason", 100)
            lines.append(f"- **{item.get('issue_title', 'Unknown')}**: {reason}")
        lines.append("")

    lines.append("<!-- REVIEW_FIXES_END -->")
    lines.append("")

    # Check if section already exists and replace, or append
    try:
        content = updater.get_content()
        start_marker = "<!-- REVIEW_FIXES_START -->"
        end_marker = "<!-- REVIEW_FIXES_END -->"

        start_idx = content.find(start_marker)
        end_idx = content.find(end_marker)

        if start_idx != -1 and end_idx != -1:
            # Replace existing section
            parts = [
                content[:start_idx],
                "\n".join(lines),
                content[end_idx + len(end_marker):]
            ]
            updater.content = "".join(parts)
        else:
            # Append new section at the end
            updater.content = content.rstrip() + "\n" + "\n".join(lines)

        updater.save()
        print(f"Updated plan with fix results: {plan_path}")
    except Exception as e:
        print(f"ERROR: Failed to update plan file: {e}")


# ---------------------------------------------------------------------------
# Which scope each result reviewed, and what the prompt says about the diff set
# (plan: review-run-scope-salvage-and-failure-visibility §2, D2.2/D2.3)
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
    temp = target.with_name(f"{REVIEW_SCOPE_LEDGER}.{os.getpid()}.tmp")
    try:
        temp.write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(temp, target)
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
        sidecar.write_text(json.dumps(data, indent=2), encoding="utf-8")
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
    reviewers also answer ``introduced_by`` (plans/review-commits.md §2.6,
    ``schemas/code_review_issues.schema.json``): a repaired answer without it
    would drop every claim that slot made, and attribution falls back to the
    claim. Any other run keeps the fields it always had."""
    fields = list(SALVAGE_ISSUE_FIELDS)
    if commit_record is not None:
        fields.append("introduced_by")
    return fields


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
       (the ``{diff_access}`` block, :func:`utils.llm_client.render_diff_access`)
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
        served_models: Optional collector for §3.6's attribution.  When a
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

    Returns:
        Tuple of (success, issues_list, error)
    """
    import time
    start_time = time.time()

    # Detect project root so CLI providers (e.g. Claude Code) run in the
    # correct working directory and can access project files.
    project_root = get_project_root(str(plan_path))

    # Parse model spec to get provider info for display. Anchored on the plan
    # (§9.3.a): the value already exists here, it just used to be dropped.
    provider_name, model_name = parse_model_spec(model_spec, anchor=str(plan_path))
    display_name = f"{provider_name}:{model_name}"

    # D6 step 3, the gate `run_single_model` applies to the other review lanes,
    # asked here for the same reason and off the same once-per-run cache: this
    # slot is a `generate` dispatch, and a runner whose own sandbox cannot start
    # reads neither the plan nor the diff — it answers with a sentence about not
    # being able to open them, which scores as a completed review. Refused
    # before the phase dir is claimed and before an earlier attempt's salvage
    # pair is retired, because a refused slot replaces nothing. The one thing
    # a refusal still retires is a `<stem>.json` from ANOTHER scope (D2.2): it
    # is not a review of this change whether or not this attempt runs, and
    # left on disk the next `--reaggregate` would load it, move the model out
    # of `models_failed` and report another change's findings as this one's.
    #
    # The third answer (D6 override, 2026-09-17): `dispatch_unsandboxed` when
    # the probe said `unavailable` AND `providers.<name>.sandbox_fallback` is
    # `auto` (the default; `off` refuses). One `[SANDBOX_BYPASSED]` line, the
    # flag on the invoker, and a porcelain snapshot taken now so a write the
    # model makes can be named.
    sandbox = await asyncio.to_thread(sandbox_refusal, provider_name, project_root)
    if sandbox.refused:
        print(f"[{display_name}] {sandbox.reason}")
        # Retired, never re-recorded: no attempt started, so the ledger keeps
        # the old id — the one the `.stale-<id>` name carries — and the next
        # attempt that really starts records this scope over it.
        if scope_id is not None:
            retire_result_from_another_scope(
                get_phase_dir(plan_path, 'code-review'),
                sanitize_model_name(model_spec),
                scope_id,
            )
        # Terminal, and `not-dispatched` is the whole of what happened: no
        # attempt was started, so there is no channel a result could have come
        # from. Without this the slot would sit `queued` until the fan-out's
        # sweep retired it as `cancelled`, which names the wrong cause for a
        # model the report is about to list under its sandbox error.
        if tracker is not None:
            tracker.failed(
                model_spec, error=sandbox.reason, source="not-dispatched"
            )
        return False, None, sandbox.reason
    tree_before = None
    if sandbox.fallback:
        print(f"[{display_name}] {sandbox.reason}")
    if porcelain_check_applies(sandbox):
        # Roster-aware (plans/ask-answer-recovery-and-false-success.md D4.3):
        # evaluated here in the slot's task, where the fan-out roster lives, so
        # an aider sibling's tag cache is exempt; the after check matches it.
        tree_before = await asyncio.to_thread(
            porcelain_snapshot, project_root,
            ignore_prefixes=fanout_ignore_prefixes(
                plan_path, project_root, anchor=plan_path
            ),
        )
    # The plugin's own jail (F1 "What it fixes", 2026-09-30): the porcelain
    # check above is skipped for it by decision; the mode check's
    # before-snapshot is taken instead, as `run_single_model` does.
    mode_before = None
    if mode_check_applies(sandbox):
        mode_before = await asyncio.to_thread(mode_snapshot, project_root)

    # Generate log file path for debugging
    sanitized_model = sanitize_model_name(model_spec)
    phase_dir = get_phase_dir(plan_path, 'code-review')
    phase_dir.mkdir(parents=True, exist_ok=True)
    log_file = phase_dir / f"log_{sanitized_model}.txt"

    # This model's attempt starts *here*, so any salvage pair an earlier attempt
    # left in the phase dir stops being outstanding work *here* — before the
    # provider is invoked, and whatever this attempt goes on to do.
    #
    # `get_phase_dir` is stable per plan (`utils/output_handler.py`), so every
    # run for this plan writes into the same directory, and `--force` clears
    # only the state file's phase-completion marker (see main()) — it deletes
    # nothing from disk. Without this call the exact P2 rerun still reproduces
    # P2: kilocode dies on `User not found.`, `has_salvageable_json` correctly
    # writes nothing, and the *previous* run's `salvage_task_<stem>.json` is
    # still dispatched by `dispatch_salvage_tasks`'s glob and still advertised
    # by main()'s end-of-run `salvage_*.json` scan. A salvage task's
    # `output_name` IS this model's result file, so what that repairs is a run
    # that no longer exists, over a slot this run recorded as failed — the
    # phantom participant the gate exists to prevent, arriving by the one route
    # the gate cannot see. Confirmed on disk: a real `code-review` phase dir
    # holds request/task pairs from three separate runs that are long over.
    #
    # **Retire-by-rename rather than run-stamping**, deliberately, and the
    # resumed run is what decides it. Retiring belongs to *the attempt that
    # would replace the artifact*, and this function is only ever reached by a
    # model that is actually re-running: `run_all_reviews` answers a resume
    # (`skip_existing`, i.e. no `--rerun-all`) from the existing
    # `<model>.json` and returns before calling here, so a skipped model keeps
    # its pair and a re-run model loses one that can only describe an answer it
    # is about to replace. That is the whole of the shared-phase-dir case a run
    # stamp was wanted for, without a run id to thread through two writers, two
    # globs and two reporting blocks — and without the question a stamp cannot
    # answer, which is what to do with the unstamped pairs already on disk.
    # What this shape does *not* cover is a model dropped from the selection
    # between runs: it begins no attempt, so nothing retires its pair. That is
    # the same residual as its stale `<model>.json`, which the fan-out also
    # leaves for reaggregation to pick up (see the `--rerun-all` note at the
    # salvage dispatch in main()), and it belongs to whatever eventually scopes
    # the phase dir by run rather than to the gate.
    #
    # Quiet: the fan-out already prints a line per model per phase, and one
    # `[SALVAGE_RETIRED]` per re-run model would bury them. The audit trail is
    # the renamed file, which is not deleted.
    retire_salvage_artifacts(
        str(phase_dir), sanitized_model, reason=RETIRE_SUPERSEDED, quiet=True
    )

    # The same rule for this model's result file, keyed on the scope it
    # reviewed (D2.2): a `<stem>.json` written against another change is
    # retired to `.stale-<id|unknown>` before this attempt can fail and leave
    # it behind, and then the ledger records what THIS attempt is shown. The
    # skip branch in `run_all_reviews` only sends a result here when its
    # ledger id differs, but `--rerun-all` reaches here with every result.
    if scope_id is not None:
        retire_result_from_another_scope(phase_dir, sanitized_model, scope_id)
        record_scope_attempt(phase_dir, sanitized_model, scope_id)

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
    # plan hands the frozen snapshot over too (§2.4 "Everyone reads the
    # snapshot"): an inline lane cannot open it, so its text is one more block
    # of the bounded payload, and a lane it does not fit is not dispatched.
    commit_record = commit_report.run_commit_range(plan_path)
    context_plan = commit_report.context_plan_path(
        commit_record, repo_root=project_root or os.getcwd()
    )
    diff_access = None
    if scope_file is not None and diff_dir is not None:
        diff_access = render_diff_access(
            model_spec,
            scope_file,
            diff_dir,
            str(phase_dir.absolute()),
            project_root or os.getcwd(),
            base_ref=base_ref,
            coverage=diff_coverage or DIFF_COVERAGE_PARTIAL,
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
            unsupported = f"review unsupported: {detail}"
            if tracker is not None:
                tracker.failed(model_spec, error=unsupported, source="not-dispatched")
            return False, None, unsupported

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
            str(plan_path.absolute()), str(scope_file), str(diff_dir),
        )
        diff_access_text, full_scope_ref = diff_access.text, str(scope_file)

    # The resolved scope, in the review order main gave it. The placeholder key
    # keeps its old name (`tracked_files_list`) because the template binds it;
    # what it carries is now the scope whatever its source. When the list is
    # cut, its notice names the manifest as the full list, so a dropped path
    # never reads as out of scope.
    tracked_files_list = format_tracked_files_for_prompt(
        changed_files or [], task_ids=task_ids, full_scope_ref=full_scope_ref
    )

    # Load prompt template. A commit brief's run (its state records
    # `commit_range`, read above) gets `commit_review.txt`; every other run, a
    # direct `--head-ref` one included, keeps `code_review.txt` (§2.6
    # "Loading").
    prompt_template = (
        load_code_review_prompt() if commit_record is None
        else load_prompt(commit_report.review_prompt_name(commit_record))
    )

    # Derive prefix from plan path (same as in main())
    prefix = derive_prefix(plan_path)

    # Build prompt context for invoke_with_file_output. The implementation
    # record is read here, per slot, rather than threaded down from main(): it
    # is three small files, and `run_all_reviews` hands this function every
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
        "scope_source": describe_scope_source(scope_source, base_ref, pinned),
        "base_ref": base_ref,
        "prefix": prefix,
        "implementation_record": build_implementation_record(plan_path),
        "scope_file": scope_file_text,
        "diff_dir": diff_dir_text,
        "diff_access": diff_access_text,
    }
    if commit_record is not None:
        # The commit template's own slots (§2.6). The block's pointer names
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
        timeout if timeout is not None
        else get_provider_timeout(provider_name, anchor=str(plan_path))
    )

    # The inline cap above bounds the `{diff_access}` block alone, but the
    # prompt that goes on argv also carries the implementation record, the
    # file list, the template and the working limits. Measured whole, as it
    # will be dispatched, so a block that fit is still refused — undispatched,
    # `[REVIEW_UNSUPPORTED]` like any other inline miss — when the prompt it
    # sits in would fail the spawn with E2BIG and be recorded as a provider
    # error. `None` is a lane whose prompt does not travel on argv.
    if diff_access is not None and diff_access.mode == "inline":
        prompt_bytes = argv_prompt_bytes(
            prompt_template,
            model_spec,
            prompt_context,
            out_dir,
            "code_review",
            timeout=int(effective_timeout),
            anchor=str(plan_path),
        )
        if prompt_bytes is not None and prompt_bytes > INLINE_PROMPT_CAP_BYTES:
            detail = (
                f"read scope {diff_access.read_scope}, inline "
                f"{diff_access.inline_bytes} B — rendered prompt {prompt_bytes} B "
                f"exceeds the {INLINE_PROMPT_CAP_BYTES} B argv cap"
            )
            print(f"[REVIEW_UNSUPPORTED] {display_name}: {detail}")
            unsupported = f"review unsupported: {detail}"
            if tracker is not None:
                tracker.failed(model_spec, error=unsupported, source="not-dispatched")
            return False, None, unsupported

    print(f"[{display_name}] Starting code review with file-based output (timeout: {effective_timeout}s)...")
    # The dispatch starts here, so the row stops being `queued`/`staggering`.
    # `attempt=1` and no `retrying` transition anywhere below, because this lane
    # has no retry ladder to report: it is one `invoke_with_file_output` call per
    # slot, and whatever the adapter retries internally it does inside that one
    # attempt. `timeout_s` is passed for the case the seed cannot know about —
    # a per-slot override that gave this model a budget its provider default
    # does not have.
    if tracker is not None:
        tracker.running(model_spec, attempt=1, timeout_s=effective_timeout)

    # The misnamed-result baseline is the slot's, taken before its dispatch and
    # handed down, as the review base's ladder does for every attempt.
    misnamed_baseline = (
        await asyncio.to_thread(
            misnamed_result_baseline, out_dir, "code_review", model_spec
        )
        if run_model_specs is not None else None
    )

    # Use asyncio.to_thread to run the synchronous invoke_with_file_output
    # in a thread pool, allowing concurrent execution
    result = await asyncio.to_thread(
        invoke_with_file_output,
        prompt_template=prompt_template,
        model_spec=model_spec,
        prompt_context=prompt_context,
        output_dir=out_dir,
        phase="code_review",
        timeout=int(effective_timeout),
        log_file=str(log_file),
        prefer_arrays=True,
        cwd=project_root,
        anchor=str(plan_path),
        # Every model of the fan-out, so a result written under the wrong name
        # is read from where the model put it (live run 10, pi).
        run_model_specs=run_model_specs,
        misnamed_baseline=misnamed_baseline,
        **sandbox_fallback_kwargs(sandbox),
    )

    duration = time.time() - start_time
    output_file = result.get("output_file", "")
    source = result.get("source", "unknown")

    # §3.6: record which model served this slot before any of the branches
    # below return, so a fallback that fired is attributed even on the paths
    # that end in salvage. Only ever populated when a fallback is configured.
    # The D6 override's provenance (2026-09-17) lands in the same collector,
    # with or without a served model beside it.
    details = result.get("details", {}) or {}
    if served_models is not None:
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
            served_models[model_spec] = entry
    # Stage U: and what it spent, recorded here for the same reason and before
    # the same branches — a slot that ends in salvage, or fails outright, spent
    # what it spent. Absent when the adapter reported nothing; never `{}`, which
    # would read as a free review.
    if usage is not None:
        spent = details.get("usage")
        if isinstance(spent, dict) and spent:
            usage[model_spec] = spent

    # D6 override: the detective check, ahead of every branch below. A bypassed
    # slot that changed the working tree is failed by path whatever the
    # invocation reported — nothing is restored, and nothing it returned is
    # parsed as a review. Skipped entirely (no git call) for a sandboxed slot.
    if porcelain_check_applies(sandbox):
        ignore_prefixes = fanout_ignore_prefixes(
            plan_path, project_root, anchor=plan_path
        )
        # Plan §4.3: one `invoke_with_file_output` call per slot, so its one
        # attempt's verdict is the whole window's.
        audits = [details.get("readonly_audit")]
        if tracker is not None:
            tracker.record_readonly_audit(
                model_spec, combine_audits(audits).to_dict()
            )
        tree_after = await asyncio.to_thread(
            porcelain_snapshot, project_root, ignore_prefixes=ignore_prefixes
        )
        touched = unexpected_writes(
            tree_before, tree_after, ignore_prefixes=ignore_prefixes,
        )
        if touched and bypass_stream_audit_clears(audits):
            warning = bypass_write_not_attributed(provider_name, touched)
            print(f"[{display_name}] {warning}")
            if tracker is not None:
                tracker.warn(model_spec, warning)
        elif touched:
            siblings = await asyncio.to_thread(
                boundaryless_sibling_count, model_spec, project_root, plan_path
            )
            violation = bypass_write_violation(
                provider_name, touched, boundaryless_siblings=siblings
            )
            print(f"[{display_name}] {violation}")
            # Failed by path, whatever the invocation reported: `source` records
            # which channel the rejected answer arrived on, `error` why nothing
            # of it is parsed.
            if tracker is not None:
                tracker.failed(model_spec, error=violation, source=source)
            return False, None, violation

    # The plugin's own jail: its `[JAIL_DENIED]` line and in-stream denial
    # count, then the mode check and the home check's verdict — fail closed
    # unless the slot's own audited stream clears it, exactly as above.
    report_jail_outcome(display_name, details, phase_dir)
    incidental = await run_incidental_checks(
        sandbox, provider_name=provider_name, display_name=display_name,
        model_spec=model_spec, project_root=project_root, plan_path=plan_path,
        mode_before=mode_before, home_checks=[details.get("home_check")],
        audits=[details.get("readonly_audit")], tracker=tracker,
        summary_key=phase_dir,
    )
    if incidental is not None:
        if tracker is not None:
            tracker.failed(model_spec, error=incidental, source=source)
        return False, None, incidental

    print(f"[{display_name}] Log saved to: {log_file}")
    # Only for a slot that answered: a failed invocation carries `output_file`
    # and no `source`, and "Result will be saved to: <path> (source: unknown)"
    # two lines above "Agent failed" promised a file nothing would write
    # (measured 2026-09-17, on every one of a run's three dead slots).
    if output_file and result["success"]:
        print(f"[{display_name}] {describe_output_file(output_file, source)}")

    if not result["success"]:
        error_msg = result.get("error", "Unknown error")
        # What the failed slot spent, on the one string every artifact of a
        # failure carries: this return's `error` is what `save_model_result`
        # writes to `error_<model>.log` and what `.status.json` records under
        # `models_failed`, and the tuple this function returns is destructured
        # by every caller, so a fourth value has nowhere to go. Measured
        # 2026-09-17: $25.05 and 137 348 output tokens went into a claude-code
        # slot that ended on a usage cap, and the only place either number
        # existed was the raw envelope in `log_<model>.txt`.
        spent = describe_usage(details.get("usage"))
        if spent:
            error_msg = f"{error_msg} (spent {spent})"
        file_error = result.get("file_error", "")
        if file_error:
            print(f"[{display_name}] File error: {file_error}")
        print(f"[{display_name}] Agent failed ({duration:.1f}s): {error_msg}")

        # Write a salvage request only when the failure output still holds an
        # answer to repair. "stderr is non-empty" is not that test: a hard
        # provider failure — kilocode answering `Error: User not found.` on a
        # dead account, in ANSI colour — passes it with no JSON anywhere in the
        # stream, and the salvage prompt's own "if nothing recoverable is
        # present, print an empty array" then writes `[]` over this model's
        # result path, so a model that never ran is aggregated as one that
        # reviewed the diff and found nothing. It also spends the operator's
        # next move on a JSON repair when the fix is `kilocode` auth. With
        # nothing to salvage the model simply stays failed, which is the D6
        # row-3 partial-results path already taken by every other dead slot.
        # `has_salvageable_json` subsumes the old condition: a `stdout_error`
        # with empty stderr only ever produced a salvage request whose
        # `raw_output` was the empty string.
        #
        # WHICH CHANNEL THE ANSWER IS ON, and this branch used to look at only
        # one of them. `if not result["success"]` is not merely "the provider
        # never spoke": it also covers the provider that wrote a truncated or
        # fenced array and *then* exited non-zero — a kill at the deadline, a
        # crash on teardown — and that array is on **stdout**, never on stderr.
        # Gating on stderr alone therefore printed "Provider failed before
        # producing any JSON — nothing to salvage" about a run that had produced
        # JSON, and threw a recoverable review away without a word. The
        # JSON-erroring providers press the same point from the other side:
        # `opencode run --format json` puts its failure shape on stdout with
        # stderr empty, and a relayed `{"error": {"code": 401, ...}}` body is
        # indistinguishable from any HTTP-backed CLI — those reached the
        # predicate as `""`, so even the verdicts it reached correctly were
        # reached for the wrong reason. The pre-gate code was equally blind (its
        # `raw_output` was the empty string), so this closes a latent hole rather
        # than a regression; it is closed here because site A is the one place
        # the gate above could make a real loss *visible*.
        #
        # **Precedence, not concatenation.** The first non-empty channel wins and
        # the other is not appended, because `raw_output` is handed to a subagent
        # as *the* damaged answer to repair (`build_salvage_prompt` in
        # `utils/subagent_prompts.py`), and gluing a launch banner or an auth
        # notice onto a truncated array gives that subagent two documents and no
        # way to tell which one it was asked about — with the same empty-array
        # fallback waiting when it guesses wrong. stdout is the one that can hold
        # an answer, so stdout is the one that is asked first.
        #
        # `utils/llm_client.py`'s `_attach_stdout_excerpt` attaches
        # `stdout_excerpt` on all three losing paths — non-zero exit, timeout
        # kill, and the zero exit whose output would not parse — already
        # `_redact`ed and `_bound_stream`ed in that order (§4.5/§4.4), and it
        # **omits the key entirely** when nothing survived rather than setting
        # `""`. So when no reducer applies, absent and empty mean the same thing,
        # and stderr still answers for the provider that died before printing a
        # byte.
        #
        # Whatever this picks is also what gets persisted: the gate below judges
        # `raw_content` and the salvage request stores `raw_content`, so the text
        # a subagent is asked to repair is the text the decision was made on.
        # Gating on one string and writing another would let a request be written
        # for evidence nobody ever saw.
        #
        # **And a stream adapter's answer is not its stream.** `salvage_source`
        # (the rule `failure_output_from_result` applies to the other lane)
        # reads `details["salvage_text"]` first — the adapter's own reduction of
        # its full stdout to the assistant's answer text — and, when that key is
        # present, reads nothing else, even when it is `""`. On pi and omp the
        # stdout excerpt is JSONL whose `content` arrays pass the gate as
        # findings: a reviewer killed while a tool ran was sent to salvage over
        # its own `thinking`/`toolCall` parts (plan:
        # review-run-scope-salvage-and-failure-visibility §4). Only when no
        # reducer applies does the stdout-then-stderr order above still hold.
        details = result.get("details", {}) or {}
        raw_content = salvage_source(details)
        timed_out = salvage_failure_kind(result) is not None

        if has_salvageable_json(raw_content):
            salvage_request = {
                "model": model_spec,
                "phase": "code_review",
                "raw_output": raw_content,
                "expected_type": "array",
                "expected_schema": {
                    "fields": salvage_issue_fields(commit_record),
                    "importance_values": ["high", "medium", "low"],
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
        if tracker is not None:
            tracker.failed(model_spec, error=error_msg, source=source)
        return False, None, error_msg

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
        print(f"[{display_name}] Found {len(output_data)} issues")
        # `done` at the *return*, not at the completion print two branches up,
        # even though the print is where `source` is named. The print only says
        # the provider exited cleanly; whether there is a usable result is
        # decided here, and the two branches below it return `False` with an
        # error `main()` keys into `failed_models`. Terminal transitions are
        # idempotent, so a `done` stamped at the print would freeze those slots
        # `done` in the table while the report called them failed.
        if tracker is not None:
            tracker.done(model_spec, source=source)
        return True, output_data, None
    elif isinstance(output_data, dict) and "raw" in output_data:
        # No valid JSON found - write salvage request for Claude Code to process
        raw_content = output_data["raw"]
        raw_preview = raw_content[:500] if raw_content else "(empty)"

        # Same rule as the hard-failure path above, for the same reason: a reply
        # with no JSON in it is not a parse failure, and salvage against it can
        # only print the empty array its prompt falls back to. This branch is
        # where §40's two write-refusal shapes land — cursor-agent's "I can't
        # write the requested file while Ask mode is active" and gemini's
        # "JSON written to …" confirmation for a write that never happened —
        # and a `[]` recorded for either would be an invented clean review.
        if not has_salvageable_json(raw_content):
            print(f"[{display_name}] Response carries no JSON — nothing to salvage")
            no_json = f"Model produced no JSON output: {raw_preview}"
            if tracker is not None:
                tracker.failed(model_spec, error=no_json, source=source)
            return False, None, no_json

        salvage_request = {
            "model": model_spec,
            "phase": "code_review",
            "raw_output": raw_content,
            "expected_type": "array",
            "expected_schema": {
                "fields": salvage_issue_fields(commit_record),
                "importance_values": ["high", "medium", "low"],
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
        unparsed = f"Could not extract JSON from response: {raw_preview}"
        if tracker is not None:
            tracker.failed(model_spec, error=unparsed, source=source)
        return False, None, unparsed
    else:
        wrong_type = f"Expected JSON array, got {type(output_data).__name__}"
        if tracker is not None:
            tracker.failed(model_spec, error=wrong_type, source=source)
        return False, None, wrong_type


# Delay between launching provider processes to avoid concurrent launch bugs
# Especially important for cursor-agent which has known issues with concurrent starts
PROVIDER_STAGGER_DELAY = 2.0  # seconds


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
        served_models: Optional §3.6 attribution collector, forwarded to each
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
    semaphore = asyncio.Semaphore(max_parallel)
    # Per-provider semaphores for concurrency limiting
    provider_semaphores: Dict[str, asyncio.Semaphore] = {}
    for spec in model_specs:
        prov, _ = parse_model_spec(spec, anchor=str(plan_path))
        if prov not in provider_semaphores:
            limit = get_provider_max_concurrent(prov, anchor=str(plan_path))
            if limit is not None:
                provider_semaphores[prov] = asyncio.Semaphore(limit)
    results: Dict[str, Tuple[bool, Optional[List[Dict]], Optional[str]]] = {}
    # F6, and the counter this replaces. `progress.models_done` was written `0`
    # before dispatch and recomputed only after the last model returned, so a
    # mid-run poll read `models 0/3` beside three finished reviewers (measured
    # 2026-09-16: 646 s of an 833 s run); D4a's `fanout_slot_counter`, borrowed
    # from the base fan-out, fixed the *number* and nothing else — no names, no
    # states, no timings, no attempt.
    #
    # The tracker carries that counter's documented meaning with it —
    # `models_done` counts **finished slots, not successful ones**, because a
    # failed or skipped model has finished its slot, and which ones produced a
    # usable result is `models_succeeded`'s job — and adds the per-model map
    # beside it. The counter itself is *deleted* rather than left ticking beside
    # the map: two writers for one key can only disagree, since the counter
    # ticked at slot exit while the map turns terminal at the completion print,
    # so a lane running both flickers between counter-order and map-order.
    tracker = FanoutProgress(
        str(get_phase_dir(plan_path, 'code-review')),
        model_specs,
        anchor=str(plan_path),
        # This fan-out's per-model override. `None` leaves each slot's budget to
        # `get_provider_timeout`, which is the same call the total deadline
        # below is sized from, so the table's denominator and the deadline agree.
        timeout=timeout,
    )
    if tracker_out is not None:
        tracker_out.append(tracker)
    pinned_kwargs: Dict[str, Any] = {"pinned": pinned} if pinned is not None else {}

    async def run_with_semaphore(model_spec: str, index: int) -> Tuple[str, Tuple[bool, Optional[List[Dict]], Optional[str]]]:
        provider_name, model_name = parse_model_spec(model_spec, anchor=str(plan_path))
        display_name = f"{provider_name}:{model_name}"

        # Skip models that already have results (resume after partial failure)
        if skip_existing:
            sanitized = sanitize_model_name(model_spec)
            phase_dir = get_phase_dir(plan_path, 'code-review')
            existing_path = phase_dir / f"{sanitized}.json"
            if existing_path.exists() and existing_path.stat().st_size > 0:
                try:
                    with open(existing_path, 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                    # D2.2: a result is reused only when it reviewed the diff
                    # set this run's reviewers are shown. One written against
                    # an earlier change — or before the ledger existed, which
                    # is `unknown` — re-runs, and `run_single_review` retires
                    # the old file at its attempt start. The alternative
                    # reports a review of another change as a review of this
                    # one.
                    scope_changed = False
                    if isinstance(existing_data, list) and scope_id is not None:
                        reviewed_scope = read_scope_ledger(phase_dir).get(sanitized)
                        if reviewed_scope != scope_id:
                            scope_changed = True
                            print(
                                f"[SCOPE_CHANGED] {display_name}: result reviewed "
                                f"scope {reviewed_scope or SCOPE_UNKNOWN}, this "
                                f"run's is {scope_id}; re-running"
                            )
                    if isinstance(existing_data, list) and not scope_changed:
                        print(f"[SKIP] {display_name} - already has results ({len(existing_data)} issues)")
                        # Stage U: the result is reused, so what it cost is
                        # reused with it. Nothing else can refill this entry —
                        # no adapter runs for a skipped slot — and without it
                        # the run's own `models_complete` write drops a number
                        # an earlier attempt really paid for.
                        if usage is not None:
                            spent = (prior_usage or {}).get(model_spec)
                            if isinstance(spent, dict) and spent:
                                usage[model_spec] = spent
                        # A slot answered from disk is terminal the moment it
                        # is seeded — no attempt is ever dispatched, so
                        # `attempt: 0` and `elapsed_s: 0` — and it counts in
                        # `models_done` *and* in `models_succeeded`, because it
                        # has a usable result. A resumed run of four models that
                        # finds three on disk therefore reads `3/4` at the first
                        # poll rather than `0/4`, which is D4a itself landing on
                        # the one lane where nothing dispatches at all. The
                        # `source` is supplied here because this branch's return
                        # tuple carries none of its own; there is no `skipped`
                        # state, so a renderer labels the row from
                        # `source in RESUME_SOURCES`.
                        tracker.done(model_spec, source="existing_file")
                        return (model_spec, (True, existing_data, None))
                except (json.JSONDecodeError, IOError):
                    print(f"[{display_name}] Existing result file corrupt, re-running...")

        # Stagger launches to avoid concurrent start bugs (especially with cursor-agent)
        # First model starts immediately, subsequent models wait
        if index > 0:
            stagger_delay = index * PROVIDER_STAGGER_DELAY
            print(f"[{display_name}] Waiting {stagger_delay:.1f}s before starting (staggered launch)...")
            # The row is not idle and it is not running: it was admitted at
            # `started_at` and has not dispatched, so the table renders this
            # sleep as a wait (`waiting …`), never as budget spent. Its run
            # time starts at `running()` — `dispatched_at`, the same point this
            # slot's own timeout clock starts — and the wait lands in
            # `queued_s` (plan: review-run-scope-salvage-and-failure-visibility
            # §6).
            tracker.staggering(model_spec, delay_s=stagger_delay)
            await asyncio.sleep(stagger_delay)
            # The stagger is spent, but this slot is not dispatched: the two
            # semaphores below can park it for minutes (five models at
            # `max_parallel: 2` park three of them), and `running` is only
            # reached inside `run_single_review`. Without this the whole wait
            # rendered `staggering` — a state the slot left at the line above —
            # while index 0, which never staggers, rendered the same wait as
            # `queued`. One word for one wait, on this lane as on the base's.
            tracker.queued(model_spec)

        # Acquire provider semaphore first (if any), then global semaphore.
        # This order prevents capped providers from hogging global slots while
        # waiting for their provider-specific turn.
        #
        # No `finally` here any more. `slot_finished()` used to tick from one,
        # because a slot that raised — or was cancelled by the overall
        # deadline — has stopped occupying the fan-out just as surely as one
        # that returned a result. The map keeps that promise in three better
        # places: the terminal transitions sit at `run_single_review`'s own
        # completion and failure sites, where the reason and the `source` are
        # known; a slot that raises past them is retired by the `except` below
        # with its own message and `source: "exception"` (F5, 2026-09-20 — it
        # used to fall through to the sweep and be labelled `cancelled`, which
        # is the wording reserved for a slot that has no ending of its own);
        # and every slot that reaches none of the three is retired by the sweep
        # in this function's own `finally`, which runs whichever way the fan-out
        # ends. A transition here as well would be the second writer.
        prov_sem = provider_semaphores.get(provider_name)
        try:
            if prov_sem:
                async with prov_sem:
                    async with semaphore:
                        result = await run_single_review(
                            model_spec, plan_path, out_dir, timeout, changed_files,
                            base_ref, served_models=served_models, usage=usage,
                            tracker=tracker, scope_source=scope_source,
                            task_ids=task_ids, scope_file=scope_file,
                            diff_dir=diff_dir, scope_id=scope_id,
                            diff_coverage=diff_coverage,
                            run_model_specs=list(model_specs),
                            **pinned_kwargs,
                        )
            else:
                async with semaphore:
                    result = await run_single_review(
                        model_spec, plan_path, out_dir, timeout, changed_files,
                        base_ref, served_models=served_models, usage=usage,
                        tracker=tracker, scope_source=scope_source,
                        task_ids=task_ids, scope_file=scope_file,
                        diff_dir=diff_dir, scope_id=scope_id,
                        diff_coverage=diff_coverage,
                        run_model_specs=list(model_specs),
                        **pinned_kwargs,
                    )
        except Exception as exc:
            # F5, 2026-09-20: two lanes, one event, two different answers. A
            # slot that raises is printed as `Review exception:` below and
            # dropped from `completed` without ever being keyed into `results`,
            # so this is the only place its *spec* is still known — and without
            # this it reached no terminal transition at all and was retired by
            # the teardown sweep as `cancelled` with `source: null`, where
            # `run_models_concurrent` records `source: "exception"` and the
            # exception's own text. The base lane is the one that is right: an
            # exception IS this slot's ending, and the sweep's two wordings are
            # for slots that have no ending of their own.
            #
            # `Exception` and deliberately not `BaseException`: a
            # `CancelledError` arriving here is the deadline's own
            # `task.cancel()`, and retiring it as an exception would stamp the
            # empty `str(CancelledError())` over the wording the sweep is about
            # to write. It is re-raised unchanged either way, because
            # `return_exceptions=True` is the contract the gather below is
            # written against.
            tracker.failed(
                model_spec,
                error=str(exc) or type(exc).__name__,
                source="exception",
            )
            raise
        return (model_spec, result)

    # Seeded before the coroutines exist, so a poller reads a *complete* map
    # from its first read instead of one that fills in as models start — and the
    # write that claims the phase dir drops the predecessor's `progress`
    # wholesale, so a model missing from this map is a bug and never a leftover.
    # (`claim_run` does that on the detached lane; on the foreground one the
    # launch write does — nothing did until F1, 2026-09-20.)
    tracker.seed()

    # Create tasks for all models with staggered starts.
    #
    # `create_task`, not bare coroutines (F2, 2026-09-20). `gather` wraps
    # coroutines into tasks of its own that nothing out here can reach, which
    # cost this fan-out both halves of its deadline path: the cancel loop below
    # raised `AttributeError` on the first `task.done()` — so the deadline
    # branch *crashed* out of the orchestrator instead of returning what had
    # been collected — and there was no handle to harvest the finished slots
    # from either. Scheduling is unchanged: nothing between here and the
    # `gather` awaits, and `gather` would have scheduled them at the same point.
    tasks = [
        spawn_fanout_slot(model_specs, run_with_semaphore(spec, idx))
        for idx, spec in enumerate(model_specs)
    ]

    # Calculate total timeout based on longest provider timeout
    if timeout is not None:
        base_timeout = timeout
    else:
        # Use maximum of all provider timeouts
        base_timeout = max(
            get_provider_timeout(
                parse_model_spec(spec, anchor=str(plan_path))[0], anchor=str(plan_path)
            )
            for spec in model_specs
        )

    stagger_overhead = len(model_specs) * PROVIDER_STAGGER_DELAY
    total_timeout = base_timeout * 2 + stagger_overhead

    # One `[PROGRESS]` line per `progress.interval_s`, computed from the map this
    # function holds; `None` at `interval_s: 0`, where the lines are silenced and
    # every event-driven transition is still written.
    tracker.start_ticker()

    try:
        completed = await asyncio.wait_for(
            asyncio.gather(*tasks, return_exceptions=True),
            timeout=total_timeout
        )

        for item in completed:
            if isinstance(item, Exception):
                print(f"Review exception: {item}")
                continue
            model_spec, result = item
            results[model_spec] = result

    except asyncio.TimeoutError:
        print(f"Total timeout ({total_timeout}s) exceeded for all models")
        # F2, 2026-09-20: **harvest before cancelling.** `asyncio.wait_for`
        # raises instead of assigning `completed`, so this branch used to leave
        # `results` empty even for the slots that had already returned a review
        # — while the tracker, which recorded each of those slots `done` inside
        # `run_single_review`, said so in the same checkpoint. The report then
        # named every model a deadline loss (`backfill_deadline_losses` walks
        # `results`) beside a `<model>.json` already on disk, and
        # `models_succeeded` was restated to 0 over a map counting real
        # successes. `cancelled()` is asked before `exception()`, which raises
        # on a cancelled task; a task that raised keeps the terminal transition
        # its own `except` above gave it and is deliberately not keyed into
        # `results`.
        for task in tasks:
            if not task.done() or task.cancelled() or task.exception() is not None:
                continue
            model_spec, result = task.result()
            results[model_spec] = result
        # Name the cause *before* anything sweeps. The reason is stored on the
        # tracker rather than passed to `sweep()` because there are two sweepers
        # — the `finally` below and the ticker's own — and a reason passed at one
        # call site would let them disagree about the wording for one ending.
        # `DEADLINE_ERROR` is the same string `backfill_deadline_losses` writes
        # into `failed_models`, so the table and the report's failure list name
        # one cause.
        tracker.set_sweep_reason(DEADLINE_ERROR)
        # Cancel remaining tasks
        for task in tasks:
            if not task.done():
                task.cancel()
    finally:
        # The sweep goes here, beside where `slot_finished()` used to tick, and
        # deliberately *not* on the timeout branch above. That branch used to be
        # unable to finish at all — `tasks` held bare coroutines, so its first
        # `task.done()` raised `AttributeError` — and the sweep surviving that
        # is exactly why it was put here; the coroutines are real tasks now
        # (F2, 2026-09-20) and the branch runs to the end, but the placement is
        # still the right one. This `finally` runs whichever way the fan-out
        # ends — the clean return, the deadline, a `KeyboardInterrupt`, an exception
        # out of the machinery itself — which is what makes "no entry is left
        # `queued`, `staggering`, `running` or `retrying` after this function
        # returns" a property of the code rather than of the happy path.
        # It does NOT cover `--abort` (F1, 2026-09-20): that is SIGTERM to the
        # worker, whose handler calls `os._exit` after `finish()`, so no
        # `finally` anywhere runs. The map is retired on disk instead, by
        # `progress_tracker.retire_live_entries` called from `finish()`.
        #
        # Order is fixed: **cancel and await the ticker, then sweep, then
        # return.** Awaiting is the point rather than politeness — the caller's
        # per-model summary follows immediately, and a ticker merely cancelled
        # could still emit a line into the middle of it; and because the map is
        # written whole on every transition, a write landing after the sweep
        # would resurrect the very entries the sweep had just retired.
        await tracker.stop_ticker()
        tracker.sweep()

    return results


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
) -> str:
    """Generate a markdown review report.

    ``pinned`` (a review pinned to two commits) hands the HTML report the
    head commit and *repo_root*: its hunks are ``base..head``, its context is
    the files as ``head`` holds them, never the disk, and a path absent at
    ``head`` carries its label (:func:`pinned_report_kwargs`).

    ``review_scope`` is :func:`review_scope_record`'s account of the scope
    manifest the reviewers were pointed at (review-scope plan D2.2): rendered
    as the ``**Review scope:**`` / ``**Diff coverage:**`` header lines and
    added to ``report_data.json`` as ``reviewScope`` and ``diffCoverage``.
    ``None`` (a direct call) adds neither.

    ``served_models`` is §3.6's attribution
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
    (:func:`utils.commit_report.report_context`, plans/review-commits.md
    §2.10): the header labels the brief "Commit brief" and carries the commit
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
    # "Commit brief", never "Plan", for a commit review (§2.8), through the
    # one owner of the word.
    document = (
        commit_review.get("documentLabel") if commit_review
        else commit_report.label_title(None)
    )
    lines = [
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
    # Plan §5 T5.2: the models that produced nothing, directly under the ones
    # that did (the bottom `## Failed Reviews` section alone left a lost
    # reviewer below the fold). The salvage answer is computed once and handed
    # to the HTML report too, so the notice there is this line minus its bold.
    salvage_requested = salvage_requested_models(
        str(phase_dir) if phase_dir is not None else None, list(failed_models)
    )
    # A jail-denied slot's `models_served` entry makes the line say "denied by
    # the plugin's jail: <path>" (plan codex-sandbox-unavailable F1 item 6).
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

    # Add validation summary if available. §6 T6.1: the four counts come from
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
    # Plan §2.4: the published `validation_context`, read from `.status.json`
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
    lines.append("")

    lines.append("> **Note:** An interactive HTML report is also available at `report.html`.")
    lines.append("> If you export selections from the HTML report (`user_selections.json`),")
    lines.append("> those selections will take precedence over checkboxes in this file.")
    if validated_groups:
        lines.append("> Checkboxes act on the whole group: marking one issue marks every")
        lines.append("> issue listed as the same finding, because there is one fix between them.")
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

    # §2.10: each finding names the commit its group was attributed to
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

    # Group by importance
    high = [i for i in all_issues if i.get("importance") == "high"]
    medium = [i for i in all_issues if i.get("importance") == "medium"]
    low = [i for i in all_issues if i.get("importance") == "low"]

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
            ))
    else:
        lines.append("_No low priority issues._")
        lines.append("")

    # Changed files list
    lines.append("## Changed Files")
    lines.append("")
    for f in changed_files:
        lines.append(f"- `{f}`")
    lines.append("")

    # Failed models
    if failed_models:
        lines.append("## Failed Reviews")
        lines.append("")
        for model, error in failed_models.items():
            lines.append(f"- **{model}**: {error}")
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
                lines.append(f"- **{theme}**: {reason}")
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
                # §2.10: the commit header, filter, badges and export help.
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
) -> List[str]:
    """Format a single issue for the report.

    Args:
        index: The issue number for display
        issue: The issue dict with title, desc, type, file, model, etc.
        validation_status: The validation status (valid, invalid, needs-human-decision, etc.)
        validation_reason: The reason for the validation decision (shown for invalid/needs-human-decision)
        served_models: Optional §3.6 attribution.  The ``**Model:**`` field is
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
            line for this issue's group (plans/review-commits.md §2.10). It
            sits above the metadata line, so the description the parser reads
            after that line is unchanged, and its subject is escaped so it
            cannot pass for a checkbox.
    """
    file_ref = issue.get("file", "unknown")
    line_range = issue.get("line_range")
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
    # and loses the tick with no warning — so the title is flattened onto its
    # own line here rather than the parser being taught to hunt for the box.
    title = str(issue.get("title", "Untitled")).replace("\r\n", " ").replace(
        "\n", " "
    ).replace("\r", " ")
    lines = [
        f"### {index}. {title}",
        f"- [ ] Skip",  # Skip checkbox
    ]

    # Add override checkboxes for items needing human review
    if validation_status in ("needs-human-decision", "validation_failed"):
        lines.append("- [ ] Mark valid")
        lines.append("- [ ] Mark invalid")
    # "Let the agent decide" routes this issue to the per-item judge at apply time.
    # Scoped to needs-human-decision only.
    if validation_status == "needs-human-decision":
        lines.append("- [ ] Let the agent decide")

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

    lines.extend([
        f"**Validation:** {validation_str} | **File:** `{file_ref}` | **Type:** {issue.get('type', 'unknown')} | **Model:** {served_model_label(issue.get('model', 'unknown'), served_models)}",
        "",
    ])

    # Include validation reason for invalid or needs-human-decision issues
    if validation_reason and validation_status in ("invalid", "needs-human-decision", "validation_failed"):
        lines.append(f"> **Validation Reason:** {validation_reason}")
        lines.append("")

    lines.extend([
        issue.get("desc", "No description"),
        "",
        "---",
        "",
    ])
    return lines


def pinned_validation_kwargs(
    pinned: Optional[PinnedRange],
    plan_snapshot: Optional[str],
    plan_sha256: Optional[str],
    repo_root: Optional[str] = None,
) -> Dict[str, Any]:
    """``prepare_batched_validation_tasks``'s pinned keywords; ``{}`` when the
    review is neither pinned nor carries a frozen context plan."""
    kwargs: Dict[str, Any] = {}
    if pinned is not None:
        kwargs["head_ref"] = pinned.head
    if plan_snapshot and plan_sha256:
        kwargs["context_plan_sha256"] = plan_sha256
        kwargs["context_plan_file"] = os.path.join(repo_root or os.getcwd(), plan_snapshot)
    return kwargs


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
) -> None:
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
    """
    import glob as glob_module

    # Find all model result files in the code-review phase directory
    phase_dir = get_phase_dir(plan_path, 'code-review')
    pattern = str(phase_dir / "*.json")
    # Sort for a deterministic load order — glob() returns filesystem order,
    # which varies between machines/runs. Grouping itself is now order-
    # independent (see group_similar_suggestions), but a stable file order
    # keeps issues.json reproducible too.
    all_files = sorted(glob_module.glob(pattern))

    # Exclude non-model files
    # `subagent_batch_report` is executor bookkeeping (D3i), never a model
    # result — see the same note in review_orchestrator_base, which also explains
    # `subagent_dry_run` (D3l) and the write scheduler's two reports.
    exclude_patterns = ['grouped', 'validation', 'salvage', 'issues', 'fix_tasks', 'report_data', 'subagent_batch_report', 'subagent_dry_run', 'write_batch_report', 'write_tasks']
    result_files = [
        f for f in all_files
        if not any(ex in os.path.basename(f) for ex in exclude_patterns)
    ]
    # Only the models this phase records are read: live run 10's misnamed
    # `pi_…_v4-flash.json` was loaded as a third reviewer by its stem, with
    # "scope unknown". Any other result file is named and set aside; a dir
    # with no recorded models keeps the stem-as-identity reading below.
    result_files = _result_files.set_aside_unrecorded_results(phase_dir, result_files)
    _result_files.publish_result_notes(phase_dir)

    if not result_files:
        print(f"No model result files found matching: {pattern}")
        # Decision 11.11 (T5.4c): nothing to aggregate because every requested
        # reviewer failed is the fan-out's exit 3 naming them, not a quiet
        # exit 0; with no recorded failure it stays exit 0.
        no_results, _requested = remaining_failed_models(str(phase_dir), [])
        announce_remaining_failures(str(phase_dir), no_results)
        exit_when_every_reviewer_failed(
            str(phase_dir), no_results,
            mode="review-code", plan_path=str(plan_path),
        )
        return

    # Collect all issues and build synthetic results dict for report generation
    all_issues = []
    models_found = set()
    # Each model's result file stem, for the scope-ledger check (D2.2).
    result_stems: Dict[str, str] = {}
    results: Dict[str, Tuple[bool, Optional[List[Dict]], Optional[str]]] = {}

    # Restore original model specs (with colons) from .status.json
    unsanitize = build_unsanitize_map(str(phase_dir))

    # An empty map is not "this dir has no models" — `result_files` is non-empty
    # or the function has already returned above. It is a phase dir whose
    # checkpoint records none, and from here on every group in the report is
    # attributed to a stem that no longer names a model. That outcome was
    # previously reached in complete silence, and on the `--skip-validation` leg
    # it still completes and still writes a report, so nothing downstream ever
    # contradicts it either.
    #
    # The condition is `build_unsanitize_map`'s *result*, deliberately, not
    # `.status.json`'s existence: the helper returns `{}` for a missing file, an
    # unreadable one, and one carrying neither `models_requested` nor
    # `models_completed` — and a hand-merged checkpoint holding `phase` and
    # `state` and nothing else inverts exactly as little as no file at all. Same
    # field-not-file rule as the fan-out's read-back below.
    if not unsanitize:
        warn_stem_attribution(
            f"WARNING: {phase_dir} holds {len(result_files)} model result "
            f"file(s), but its checkpoint records no models_requested — either "
            f"no .status.json at all, or one that never got the field. This "
            f"reaggregation continues."
        )

    # One file per logical model (W3): a phase dir that straddles the L1 anchor
    # upgrade holds both `<model>.json` and `<provider>_<model>.json` for the same
    # model, and reading both double-counts every issue. `results` matters as much
    # as the counts here — a duplicate entry renders the same model twice in the
    # report. The precedence (anchored wins, divergence WARNs, an ambiguous legacy
    # stem exits 3) lives in the shared helper.
    for model, _chosen_path, issues in resolve_result_files_by_model(
        str(phase_dir), result_files, unsanitize, noun="issues"
    ):
        models_found.add(model)
        result_stems[model] = Path(_chosen_path).stem

        # The file on disk is whatever the fan-out (or a salvage, or a hand
        # edit) left there, so the same guard the fan-out's own aggregate uses
        # applies before anything is stamped — this is the site the documented
        # `--reaggregate` recovery died at, on the very file a malformed
        # fan-out had just written.
        issues = drop_non_record_entries(issues, model, noun="issues")
        for issue in issues:
            # `model` before `source_model`, which is the order the fan-out
            # stamps them in (`main` sets `model` as it flattens `results`, then
            # fills `source_model` in just before grouping). Insertion order is
            # not cosmetic here: `SuggestionGroup.to_dict` carries a suggestion's
            # dict through unreordered, `json.dump` writes keys in that order,
            # and `grouped_sha256` hashes the file's *bytes*. Stamped the other
            # way round, reaggregating a phase whose specs are already canonical
            # still moved grouped.json's bytes and still made
            # `check_task_file_inputs` refuse `validation_tasks.json` — the same
            # failure the missing checkpoint caused, from the other direction.
            issue["model"] = model            # report generation reads this one
            issue["source_model"] = model     # grouping attributes by this one
        all_issues.extend(issues)

        # Add to results dict for report generation
        results[model] = (True, issues, None)

        print(f"  Loaded {len(issues)} issues from {model}")

    print(f"\nRe-aggregating {len(all_issues)} issues from {len(models_found)} models")

    if not results:
        print("No readable model results to aggregate.")
        # T5.4c: no model has a readable result. With reviewers recorded
        # failed this is exit 3 naming them (the phase stays unrecorded);
        # otherwise today's exit 0.
        no_results, _requested = remaining_failed_models(str(phase_dir), [])
        announce_remaining_failures(str(phase_dir), no_results)
        exit_when_every_reviewer_failed(
            str(phase_dir), no_results,
            mode="review-code", plan_path=str(plan_path),
        )
        return

    # A model whose result file is on disk has completed as far as this
    # report is concerned, whatever the fan-out recorded about it: a salvage
    # the host ran after the marker, or a result obtained out of band for a
    # slot the fan-out could not run, arrives by exactly this path. The
    # checkpoint is what `status` and `build_unsanitize_map` read.
    for model in record_models_present(str(phase_dir), sorted(models_found)):
        print(f"[{model}] result file present; recorded as completed (was failed)")

    # Plan §5 (T5.1/T5.4a): read back only now, after the reconciliation above
    # moved every model with a file out of `models_failed`. What is left — plus
    # any requested model with neither a file nor a recorded failure — is named
    # to the host here, and handed to the report below; `results` holds only
    # the models with a file, so it has no failures of its own to report.
    failed_models_map, requested_set = remaining_failed_models(
        str(phase_dir), sorted(models_found)
    )
    announce_remaining_failures(str(phase_dir), failed_models_map)

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

    # The same resolution as `resolve_changed_files` (the same printed lines),
    # kept whole because a regenerated scope manifest names its source (D2.2).
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
    # their diff (plans/review-commits.md §2.5).
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

        # Group similar issues — or, on the path where it matters most, do not.
        #
        # This function is the one that *checks* `grouped.json`'s bytes: a few
        # lines below it hands `build_inputs(..., grouped_file=grouped_path)` to
        # `read_task_file`, which compares the hash against the
        # `inputs.grouped_sha256` `validation_tasks.json` was materialized with
        # (`check_task_file_inputs`, `utils/subagent_tasks.py`). Regrouping
        # unconditionally meant it broke that binding and then audited it — the
        # file it hashes is the file it has just rewritten — so
        #
        #     ERROR: Refusing task file .../validation_tasks.json: the inputs it
        #     was materialized from have changed (grouped_sha256: ...)
        #
        # was this command refusing itself, and review-code's documented
        # validate-then-reaggregate flow could not complete at all.
        #
        # Making the round trip byte-identical (the canonical
        # `model`-then-`source_model` insertion order stamped above) fixes the
        # instance, not the class: it holds only while regrouping is perfectly
        # reproducible out of two separate dict literals in two functions. A
        # field added to an issue on one path, a reorder inside
        # `SuggestionGroup.to_dict` (`utils/suggestion_processor.py`), a changed
        # argument to this `json.dump`, or a grouping change that reorders the
        # array re-opens it — and none of those reads as a hash-binding change at
        # review time, which is how the original got in. So the bound file is not
        # rewritten at all, and byte-identity survives as the regression guard it
        # is good at being rather than as the thing the flow rests on.
        #
        # The branch is `utils/review_orchestrator_base.reaggregate_from_existing_files`'s,
        # ported — "preserves validation alignment", in its own printed words —
        # with each half of its guard meaning here what it means there:
        #
        #   * `validation.json` counts only when this run will *use* it, hence
        #     the `--skip-validation` half: a run told to ignore validation has
        #     no alignment to preserve. In this phase that disjunct is close to
        #     subsumed, since code-review only ever writes `validation.json`
        #     after merging batches and so `validation_tasks.json` was there
        #     first; it is kept because a hand-copied or partially cleaned dir
        #     carrying only the merged file is still a dir whose groups are
        #     spoken for.
        #   * `validation_tasks.json` counts *regardless* of the flag, and that
        #     asymmetry is deliberate: it is a binding on this file's bytes that
        #     outlives the invocation. A `--skip-validation` reaggregate that
        #     rewrote `grouped.json` would leave the refusal armed for the next
        #     run that does consume validation — the same defect, one command
        #     later, with nothing on screen to connect them.
        #
        # Both are ANDed with `grouped.json` actually existing, because
        # `--reaggregate` is also the path that completes a run interrupted
        # *before* grouping: `main` sends exactly that dir here ("Found N
        # per-model result file(s) but no grouped.json"). With nothing on disk
        # there is nothing bound and nothing to preserve, so that run groups and
        # writes as it always did.
        grouped_path = get_output_paths(plan_path, "code_review_grouped", phase='code-review')
        validation_path = get_output_paths(plan_path, "code_review_validation", phase='code-review')
        validation_tasks_path = phase_dir / "validation_tasks.json"

        has_existing_validation = (
            (validation_path.exists() and not args.skip_validation)
            or validation_tasks_path.exists()
        )

        reuse_bound_grouping = (
            all_issues and has_existing_validation and grouped_path.exists()
        )
        if reuse_bound_grouping:
            with open(grouped_path, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
            grouped = load_groups_payload(raw_data)
            # The premise of reuse is that the bound file still describes the
            # results on disk. A per-model file that landed after grouping — a
            # salvage the host ran once the fan-out had returned at the
            # validation marker, or a result obtained out of band for a slot
            # the fan-out recorded as failed — falsifies it, and reusing the
            # file then excluded that model from every group while `results`
            # still listed it (measured 2026-09-17: three of eight issues in no
            # group, and no line on screen saying so). The round is retired,
            # not deleted, and the regroup branch below re-materializes
            # validation for the grouping that does cover the dir.
            gap = grouped_coverage_gap(
                grouped, {m: issues for m, (_ok, issues, _err) in results.items()}
            )
            if gap:
                print(
                    "grouped.json does not cover the model results on disk; "
                    "regrouping and retiring the validation round bound to it:"
                )
                for line in gap:
                    print(f"  {line}")
                retire_stale_validation_round(
                    str(phase_dir), reason="grouped.json did not cover the results on disk"
                )
                reuse_bound_grouping = False

        if reuse_bound_grouping:
            print("Using existing grouped.json (preserves validation alignment)")
            # §2.6 on a reaggregate: attributed again in memory for the
            # report; the bound file keeps its bytes (and its own pass's fields).
            commit_attribution_pass = attribute_review_groups(
                grouped, state, repo_root=git_root or project_root
            )
        else:
            raw_grouped = group_similar_suggestions(all_issues)
            # The two branches are made to agree on shape *here* rather than at
            # each consumer: `load_groups_payload` yields plain dicts (a v1 bare
            # array, or the v2 envelope's `groups`), so the regroup branch hands
            # on its stamped dict list too instead of the `SuggestionGroup`s it
            # used to. Everything below already tolerates dicts — `len(grouped)`,
            # the `[g.to_dict() if hasattr(g, 'to_dict') else g ...]` re-entries,
            # `merge_validation_batches` — and passing the stamped list moves no
            # group id, because `generate_group_id` reads `theme` and each
            # suggestion's `type`/`section`/`details` and never the stamped keys.
            grouped = [g.to_dict() if hasattr(g, 'to_dict') else g for g in raw_grouped]
            # Stamp stable content-based hashes on groups and suggestions
            stamp_stable_ids(grouped)
            # §2.6: the regrouped file carries the attribution (off the hash).
            commit_attribution_pass = attribute_review_groups(
                grouped, state, repo_root=git_root or project_root
            )
            # D7: a re-group orphans any verdicts on disk, so they leave with it.
            retire_stale_validation(str(phase_dir), reason="grouped.json rewritten by reaggregate")
            with open(grouped_path, 'w', encoding='utf-8') as f:
                json.dump(save_groups_payload(grouped), f, indent=2)
            print(f"Grouped issues saved to: {grouped_path}")

        validated_groups_for_report = None

        # Task 2.10: a contract-1 round built from an over-limit plan is never
        # reused — retired whole (renamed, kept) and rematerialized below.
        legacy_round = (
            None if args.skip_validation
            else legacy_context_round_reason(str(phase_dir))
        )
        if legacy_round:
            print(f"\n{legacy_round}")
            retire_stale_validation_round(
                str(phase_dir),
                reason="validation built from truncated context (contract 1)",
            )

        # Check if we're merging validation batch results
        if not grouped:
            validated_groups_for_report = []
            validation_path.write_text("[]\n", encoding="utf-8")
        elif not args.skip_validation and validation_tasks_path.exists():
            print("\nMerging validation batch results...")
            # Same resume guard as the plan-review path: a v1 file (no prompts to
            # recover) or moved inputs both mean "re-materialize this phase", not
            # "interpret it anyway". Exit 3, nothing dispatched.
            try:
                batch_metadata = read_task_file(
                    str(validation_tasks_path),
                    phase_dir=str(phase_dir),
                    current_inputs=build_inputs(
                        plan_file=str(plan_path),
                        grouped_file=str(grouped_path),
                        # Recut from the same groups and the files as they are
                        # now: a reviewed file edited between fan-out and this
                        # merge moves this hash, and only this hash — `diff_base`
                        # names the ref the diff was taken against and sits
                        # still for any edit on the near side of it.
                        reviewed_code=build_reviewed_code_excerpt(
                            grouped, project_root=project_root, **pinned_kw,
                        ),
                        # A commit brief's frozen context plan: its snapshot
                        # as it is now, against what the round recorded.
                        **(
                            {"context_plan_sha256": context_plan_snapshot_sha256(
                                plan_snapshot, git_root,
                            )}
                            if plan_snapshot and plan_sha256 else {}
                        ),
                    ),
                )
            except TaskFileError as task_file_error:
                print(f"ERROR: {task_file_error}", file=sys.stderr)
                # Identical to the sibling guard in review_orchestrator_base: the
                # refusal has to reach the *process* exit code. main()'s
                # reaggregate branch discards this coroutine's return value, so a
                # `return 3` here would surface to a polling host as exit 0 —
                # "done" on a run that produced no report and needs --force.
                sys.exit(task_file_error.exit_code)
            # §2.3 step 5 / 2.9: re-hash the snapshots the stored prompts name,
            # rebinding a moved phase dir; a changed or missing one is exit 3.
            verify_round_context(
                batch_metadata, str(phase_dir), str(validation_tasks_path)
            )

            # The shared merge: batch files -> validation.json (with the
            # executor's own runner attribution, F3) -> groups. This branch
            # used to re-implement the three steps, importing the base's
            # private runner lookup to do it.
            validated_groups_for_report = merge_validation_batches(
                str(phase_dir), batch_metadata, grouped, str(validation_path)
            )
        elif not args.skip_validation:
            # No validation batches exist - need to prepare them
            print("\nPreparing batched validation for subagent execution...")
            # One read of the plan, bound to this phase dir's own snapshot
            # (§2.3 step 5): the plan block names it, never the live plan.
            plan_document = bind_plan_for_validation(str(plan_path), str(phase_dir))
            plan_content = plan_document.text

            # Same two contexts and the same single budget owner as the
            # fan-out's own prep above; the two sites must materialize the same
            # prompt or a reaggregate re-validates against a different one.
            cut_report: Dict[str, Any] = {}
            secondary, reviewed_code = build_validation_secondary_context(
                grouped, plan_path, project_root=project_root,
                cut_report=cut_report, **pinned_kw,
            )
            batched_tasks = prepare_batched_validation_tasks(
                **pinned_validation_kwargs(pinned, plan_snapshot, plan_sha256, git_root),
                groups=[g.to_dict() if hasattr(g, 'to_dict') else g for g in grouped],
                # No `Plan file:` line: the block names the bound
                # snapshot, and a second path — the live plan — would
                # point a validator at bytes the snapshot hash does not cover.
                context=plan_content,
                output_dir=str(phase_dir),
                plan_file=str(plan_path),
                model=args.validation_model,
                orchestrator="code_review_orchestrator.py",
                base_ref=base_ref,
                secondary_context=secondary,
                secondary_context_label=REVIEWED_CODE_CONTEXT_LABEL,
                reviewed_code=reviewed_code,
                # The guidance, plus the dropped files to open when the
                # reviewed-code block lost any (T7.4) — outside every block
                # a context budget can cut.
                extra_instructions=validation_extra_instructions(
                    cut_report,
                    **pinned_guidance_kwargs(pinned, plan_snapshot, plan_sha256),
                ),
                context_document=plan_document,
                secondary_document=reviewed_code_document(secondary, cut_report),
                runner_read_refusal=materialization_read_refusal(args, str(plan_path)),
                phase="code-review",
            )

            # Save validation task instructions
            with open(validation_tasks_path, 'w', encoding='utf-8') as f:
                json.dump(batched_tasks, f, indent=2)

            # 2026-09-21, the remaining lane-parity gap: the phase machine's own
            # word for the stretch that starts here, written UNCONDITIONALLY the
            # way `review_orchestrator_base` writes it at both of its own
            # materialization sites — before the dispatch, not only on the
            # host-driven return below. The `--exec-subagents` branch does not
            # return here; it dispatches, and that dispatch is the second long
            # stretch of the phase (62 s of a measured 516 s run). Without this
            # write it ran under `state: models_complete`, the word the fan-out
            # left behind, while `progress.step` read `validating` — exactly the
            # `phase state: grouping_complete` / `progress: validating`
            # disagreement the base lane fixed on 2026-09-16, and a checkpoint
            # that misreports which stretch it is in is what rule 2's
            # instant-return test tells a polling agent to read.
            update_status(str(phase_dir), {"state": "validation_pending"})

            total_batches = batched_tasks["total_batches"]
            stats = batched_tasks.get("batching_stats", {})

            if total_batches == 1:
                print(f"\n[VALIDATION_PENDING] {validation_tasks_path}")
            else:
                print(f"\n[VALIDATION_BATCHES_PENDING] {validation_tasks_path}")
                print(f"Batches: {total_batches}")

            print(f"\nValidation prepared for subagent execution.")
            print(f"Groups to validate: {stats.get('total_groups', len(grouped))}")

            # Resolved here, from the running skill dir, because the task file
            # stores only the durable mode + plan pair (D1c).
            reaggregate_cmd = resolved_reaggregate_command(batched_tasks)

            # D3b: with --exec-subagents this process dispatches the batch itself
            # and continues to the merge below instead of exiting at the marker.
            if await asyncio.to_thread(
                dispatch_subagent_tasks,
                args,
                task_file=str(validation_tasks_path),
                phase_dir=str(phase_dir),
                phase="code-review",
                document=batched_tasks,
                plan_path=str(plan_path),
                label="validation",
                retry_command=reaggregate_cmd,
            ):
                validated_groups_for_report = merge_validation_batches(
                    str(phase_dir), batched_tasks, grouped, str(validation_path)
                )
            else:
                # The plan as the user typed it (fix round 14).
                reaggregate_cmd = resolved_reaggregate_command(
                    batched_tasks, typed_plan=True,
                )
                print("\nAfter validation completes, run:")
                print(f"  {reaggregate_cmd or ''}")
                record_next(reaggregate_cmd or None)
                # The phase machine's own word for this stretch, plus the
                # poller's copy of it — the pair `review_orchestrator_base`
                # writes at its own host hand-off. Without them this return
                # left `state: models_complete` beside `progress.step:
                # grouping`, and neither word is terminal: `run_status`'s
                # checkpoint view therefore read every host-validated code
                # review as still in flight, so a foreground run rendered
                # "running in foreground (…)" until `--reaggregate` finished it
                # and `next` on a finished detached one waited the whole
                # `poll_s` before exiting 0. A host-driven hand-off IS this
                # process's ending, which is why both words are listed in
                # `CHECKPOINT_TERMINAL_STATES` / `CHECKPOINT_TERMINAL_STEPS`.
                update_status(str(phase_dir), {"state": "validation_pending"})
                report_progress(str(phase_dir), step="validation_pending")
                return  # Exit early - Claude Code handles validation
        else:
            print("\nSkipping validation (--skip-validation flag set)")

        # Generate report. `served_models` is what the fan-out recorded in the
        # checkpoint (§3.6's attribution and the D6 override's `sandbox:
        # bypassed`, 2026-09-17): the per-model files carry neither, so without
        # this read a reaggregated report named a bypassed slot as if it had
        # run sandboxed.
        report = generate_review_report(
            plan_path, results, changed_files, validated_groups_for_report,
            # §2.10: the commit header from the record, never from git.
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
            # Plan §5 T5.1: the failures read back above, and the recorded
            # requested set as the "of M requested" denominator.
            failed_models=failed_models_map,
            requested_models=(
                len(requested_set) if requested_set is not None else None
            ),
            # D2.2: the scope read back (or regenerated) above.
            review_scope=scope_record,
            **({"pinned": pinned, "repo_root": git_root} if pinned is not None else {}),
        )

        # Save report
        report_path = get_output_paths(plan_path, "code_review", phase='code-review')
        report_path = report_path.with_suffix(".md")
        report_path.write_text(report, encoding="utf-8")

        print("\nReaggregation complete!")
        print(f"Report: {report_path}")

        # F2/F3: this reaggregate path never called either recorder, so a
        # detached --reaggregate run reported `output_files` with nothing in it
        # and `MULTI_LLM_RESULT.artifacts: []` — the same gap main()'s own
        # completion site had. Same existence-filtered list as there.
        report_html_path = str(phase_dir / "report.html")
        record_output_files(
            str(phase_dir),
            report=str(report_path),
            report_html=report_html_path,
            grouped=str(grouped_path),
            validation=str(validation_path),
            issues=str(issues_path),
        )
        record_review_artifacts(
            report_path, report_html_path, grouped_path, validation_path, issues_path
        )

        # T5.4b (decision 11.11): a reaggregate that still lacks some models
        # reports `[PARTIAL_RESULTS: …]` and `state: "partial"` (exit 0), as the
        # fan-out does — the host's cue to name them from `progress.models`.
        # `unattended=False`: the `[AUTO_RESOLVED]` record that call writes names
        # the fan-out's in-process continuation, never a separate reaggregate.
        # The phase is still recorded completed below and no `next` is
        # recorded, so the result line keeps `next: null`.
        unattended_mod.report_partial_results(
            completed=sorted(models_found),
            failed=list(failed_models_map),
            phase_dir=str(phase_dir),
            unattended=False,
        )

        # Mark phase complete after successful reaggregation
        state = get_or_create_state(plan_path)
        state.mark_phase_completed("code-review")
        state.save()
        update_status(str(phase_dir), {"state": "complete"})
        report_progress(str(phase_dir), step="complete")


def _plan_file_label(plan_path: Path, args: Any = None) -> str:
    """``Plan file`` as today, or ``Commit brief`` when the plan's
    ``state.json`` records a ``commit_range``: the phase's own lines never call
    a commit brief a plan (plans/review-commits.md §2.8, "'Commit brief',
    never 'plan'"), through the one owner of the word,
    ``commit_review.document_label``. *args* carrying a front door's stage
    (:func:`landed_stage`) is a commit brief too: a detached launch of a new
    brief has its ``commit_range`` only in that stage until the worker's
    boundary, after this label prints. Read-only; no state is a plan."""
    from utils.commit_review import document_label, read_commit_range

    record = read_commit_range(plan_path)
    if record is None and landed_stage(args):
        record = {}
    word = document_label({"commit_range": record})
    return "Plan file" if word == "plan" else word.capitalize()


async def main(argv: Optional[List[str]] = None) -> int:
    """Main entry point."""
    # Line buffering + UTF-8/replace stream encoding (Windows-safe output);
    # see utils/stream_bootstrap.py for the full rationale.
    bootstrap_streams()

    args = parse_args(argv)

    # Validate plan file (resolve to absolute path first to handle
    # uv --directory which changes the working directory)
    plan_path = Path(args.plan_file).resolve()
    if not plan_path.exists():
        print(f"ERROR: {_plan_file_label(plan_path, args)} not found: {args.plan_file}")
        print(f"       Resolved path: {plan_path}")
        sys.exit(1)

    # §9.3.a/b: the anchor capture point — absolute, before anything can chdir
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

    # Handle --reaggregate mode: skip model invocation, just re-process existing results
    if args.reaggregate:
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

        # The review on record's two commits, when state pins them (a commit
        # brief's `commit_range`, a direct round's `head_ref`): resolved
        # strictly here, before the detach boundary and before anything is
        # written, so a pruned SHA is `[RANGE_UNRESOLVED]` exit 3 on the
        # caller's terminal and never a `HEAD~1` stand-in, and a typed ref
        # that resolves elsewhere is refused (plans/review-commits.md §2.4,
        # §2.5).
        try:
            reaggregate_pinned = resolve_pinned_range(
                getattr(get_or_create_state(plan_path), "state", None), args,
                cwd=review_git_root(get_project_root(str(plan_path))) or os.getcwd(),
                plan_path=plan_path, reaggregate=True,
            )
        except RangeError as exc:
            print(exc.message)
            sys.exit(exc.exit_code)
        if reaggregate_pinned is not None:
            pin_recorded_refs(reaggregate_pinned)

        # The stale guard the fan-out path applies below, applied here too. A
        # review completed before the latest implement judged an earlier state
        # of the code (2026-10-02: the empty repository); the fan-out takes
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

        # The detach boundary, crossed here as well as on the fan-out path
        # below: a `--reaggregate --detach` launch must print its run banner
        # and hand the re-dispatch to a worker, or the host that composed
        # `--detach` has nothing to poll (see the same branch in
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
        # A front door's stage lands inside that boundary (§2.1): the pair and
        # its drift list come from the state it left, not the one read above.
        if landed_stage(args):
            try:
                reaggregate_pinned = resolve_pinned_range(
                    getattr(get_or_create_state(plan_path), "state", None), args,
                    cwd=review_git_root(get_project_root(str(plan_path))) or os.getcwd(),
                    plan_path=plan_path, reaggregate=True,
                )
            except RangeError as exc:
                print(exc.message)
                sys.exit(exc.exit_code)

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
            await reaggregate_from_existing_files(
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
        return

    # Guard against re-running already-completed phase (expensive LLM calls)
    state_guard = get_or_create_state(plan_path)
    # A review pinned to two commits (`--head-ref`, or a commit brief's
    # `commit_range`): both ends resolved strictly, never through
    # `validate_git_ref`'s `HEAD~1` fallback, and a recorded SHA that no longer
    # names a commit is `[RANGE_UNRESOLVED]` exit 3 — all before this phase
    # writes anything, `state.json` included (plans/review-commits.md §2.4,
    # §2.5). The recorded invocation then carries the pair as full SHAs, so a
    # detached child, a resume line and a next command replay the same pair
    # after a branch moves.
    try:
        pinned = resolve_pinned_range(
            getattr(state_guard, "state", None), args,
            cwd=review_git_root(get_project_root(str(plan_path))) or os.getcwd(),
            plan_path=plan_path,
        )
    except RangeError as exc:
        print(exc.message)
        sys.exit(exc.exit_code)
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
        # earlier state of the code (2026-10-02: the empty repository, before
        # implement existed). `is_phase_completed` already reads it as pending;
        # the artifacts it left in the phase dir must not auto-heal it back to
        # complete below, so a plain run takes the `--force` path.
        print("NOTE: code-review was completed before the latest implement; "
              "re-running it (as --force)")
        args.force = True
    if state_guard.is_phase_completed("code-review") and not args.force:
        # Fix round 28 (live run 12 #11): said as done, never as an error. A
        # commit review says it as the mode the user typed, of its commit
        # brief (plans/review-commits.md §2.8).
        from utils.commit_review import document_label
        from utils.commit_spelling import commit_view, spell_mode

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
    if not args.force:
        phase_dir_check = get_phase_dir(plan_path, 'code-review')
        validation_tasks_path = phase_dir_check / "validation_tasks.json"
        grouped_path = phase_dir_check / "grouped.json"
        validation_path = phase_dir_check / "validation.json"
        report_path_check = phase_dir_check / "report.md"

        if validation_tasks_path.exists():
            if validation_path.exists() and report_path_check.exists():
                # Auto-heal: all artifacts present, just mark complete
                state_guard.mark_phase_completed("code-review")
                state_guard.save()
                update_status(str(phase_dir_check), {"state": "complete"})
                report_progress(str(phase_dir_check), step="complete")
                print("Phase 'code-review' was complete but not marked. Auto-healed state.")
                print(f"Report: {report_path_check}")
                sys.exit(0)
            elif validation_path.exists():
                print("ERROR: Partial completion detected for 'code-review'.")
                print(f"  validation.json exists but report is missing.")
                print(f"  Run: --reaggregate to regenerate the report.")
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
                    print(f"  Check if all batches are complete, then run: --reaggregate")
                    sys.exit(3)
                else:
                    print("ERROR: Partial completion detected for 'code-review'.")
                    print(f"  validation_tasks.json exists but validation has not started.")
                    print(f"  Resume it: for each task in that file, run task.prompt")
                    print(f"  (or the file at task.prompt_path, whose bytes are the same)")
                    print(f"  as a subagent and write the JSON it returns to task.output_path.")
                    sys.exit(3)
        elif grouped_path.exists():
            print("ERROR: Partial completion detected for 'code-review'.")
            print(f"  grouped.json exists but no validation_tasks.json.")
            print(f"  Run: --reaggregate to continue from grouping.")
            sys.exit(3)
        else:
            # Check for per-model result files
            model_files = leftover_model_results(phase_dir_check)
            if model_files:
                print("ERROR: Partial completion detected for 'code-review'.")
                print(f"  Found {len(model_files)} per-model result file(s) but no grouped.json.")
                print(f"  Run: --reaggregate to aggregate results.")
                sys.exit(3)

    # Mutual exclusivity check: --quick and --interactive
    if args.quick and args.interactive:
        print("ERROR: --quick and --interactive are mutually exclusive.")
        sys.exit(1)

    # Handle model selection using the priority-based resolver
    # Priority: CLI --models > --interactive flag > --quick flag > YAML defaults > Interactive selection
    # D6 row 2: under --yes the ladder stops at defaults.models and an
    # unresolvable set is exit 3 — never a rendered multi-select.
    unattended = bool(getattr(args, "yes", False))
    try:
        model_specs = resolve_models(
            cli_models=args.models,
            interactive=args.interactive,
            quick=args.quick,
            mode='code-review',  # Mode-specific defaults from providers.yaml
            anchor=str(plan_path),  # per-project config discovery follows the plan-derived root
            unattended=unattended,
        )
    except NeedsHuman as e:
        sys.exit(unattended_mod.fail_closed(e.message, site_id=e.site))
    except RuntimeError as e:
        print(f"ERROR: {e}")
        available = get_all_model_specs(anchor=str(plan_path))
        print(f"Use --models flag. Available: {', '.join(available[:5])}...")
        sys.exit(1)

    if not model_specs:
        print("ERROR: No models selected.")
        sys.exit(1)

    # Display how models were selected
    if args.models:
        print(f"Using models from --models flag: {', '.join(model_specs)}")
    elif args.interactive:
        print(f"Using interactively selected models: {', '.join(model_specs)}")
    elif args.quick:
        print(f"Using quick models from providers.yaml: {', '.join(model_specs)}")
    else:
        print(f"Using default models from providers.yaml: {', '.join(model_specs)}")

    # Validate model specs against the registry
    invalid_models = [m for m in model_specs if not is_model_valid(m, anchor=str(plan_path))]
    if invalid_models:
        print(f"WARNING: Unknown models (proceeding anyway): {', '.join(invalid_models)}")
        # Anchored to match the rejection above (§9.3.c).
        available = get_all_model_specs(anchor=str(plan_path))
        print(f"Available models: {', '.join(available[:10])}...")

    print(f"{_plan_file_label(plan_path, args)}: {plan_path}")
    print(f"Output directory: {out_dir}")
    print(f"Models: {', '.join(model_specs)}")
    if args.timeout:
        print(f"Timeout override: {args.timeout}s per model")
    else:
        print("Timeout: per-provider defaults from providers.yaml")
    print(f"Max parallel: {args.max_parallel}")

    out_dir.mkdir(parents=True, exist_ok=True)

    # Get tracked files and base ref from state (if available from implementation phase)
    state = get_or_create_state(plan_path)

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
    # there — and saved only past the detach boundary below.
    try:
        scope_files = read_scope_files_flags(args, git_root or os.getcwd())
    except ScopeFilesError as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)
    scope_record_moved = stage_scope_files_record(state, scope_files)

    # Get the git base reference - this is the commit when implementation started
    # Used by agents to run: git diff <base_ref> -- <file>
    if pinned is not None:
        # The pinned pair, resolved strictly above: never `head_before_implement`,
        # `head_at_start` or `HEAD~1`, and never a `validate_git_ref` fallback.
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

    # Best-effort base-ref staleness visibility. Wrapped so it can NEVER fail the
    # run: surface the resolved commit, and warn if the base ref lags behind HEAD
    # (a common foot-gun when only the latest uncommitted work was meant to be
    # reviewed). Skipped for a pinned review: its `is-ancestor <base> HEAD` and
    # `rev-list <base>..HEAD` are about an implement base, and two commits are
    # reviewed whatever HEAD is.
    if base_ref and pinned is None:
        try:
            if is_empty_tree(base_ref):
                # `git log` names no commit for a tree, so say what it is.
                print(
                    "Base ref is the empty tree: the repository had no commit "
                    "when this workflow started, so every file under review is new"
                )
            log_out, _, log_rc = _run_git(
                "log", "-1", "--format=%h %s", base_ref, check=False
            )
            if log_rc == 0 and log_out.strip():
                print(f"Base ref commit: {log_out.strip()}")

            _, _, anc_rc = _run_git(
                "merge-base", "--is-ancestor", base_ref, "HEAD", check=False
            )
            if anc_rc == 0:
                count_out, _, count_rc = _run_git(
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

    # The scope, labelled by the branch that picked it, then put in review
    # order: source, tests, fixtures, generated, by path within each. The
    # resolver's own order is never used (its tracked-files branch is a set).
    # This ordered list is what every reviewer's prompt lists, what
    # `intent_to_add_untracked` marks and what the report counts; before this,
    # main resolved it and then handed the reviewers the raw — and, on the
    # fallback, empty — `tracked_files` instead (review-scope plan §2.1).
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
        # printed (plans/review-commits.md §2.5 "Drift"), a staged launch's
        # included: its record arrives with the stage, past the boundary.
        pinned = drift_check(pinned, changed_files, repo_root=git_root,
                             staged=landed_stage(args))
    pinned_kw: Dict[str, Any] = {"pinned": pinned} if pinned is not None else {}
    plan_snapshot, plan_sha256 = _context_plan(getattr(state, "state", None))
    print("Running code review in agent exploration mode...")
    print("")

    # The plan the reviewers are pointed at, read once here and bound to this
    # phase's `validation-snapshot.md` past the detach boundary (the same split
    # review-plan and review-tasks make): binding at materialization, after the
    # fan-out, let a plan edited during the review become the snapshot the
    # validators are hash-bound to. Only the read and the UTF-8 check happen
    # before the boundary, so an undecodable plan still fails in the foreground
    # and a repeated `--detach` never replaces an active run's snapshot.
    plan_bytes: Optional[bytes] = None
    if not args.skip_validation:
        try:
            plan_bytes = plan_path.read_bytes()
            decode_document(plan_bytes, str(plan_path))
        except ValidationContextError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            sys.exit(exc.exit_code)

    # --- the detach boundary (see utils/review_orchestrator_base.maybe_detach) --
    # Late on purpose: everything above is pre-flight that must fail on the
    # caller's terminal — models resolved, base ref validated, changed files
    # discovered — and nothing below runs in the invoker.
    detach_phase_dir = get_phase_dir(plan_path, 'code-review')
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

    # A detached worker takes its lock inside `maybe_detach`, and a commit
    # front door's stage (the new header, `commit_range`, a context-plan
    # snapshot; plans/review-commits.md §2.1) is applied there — after the
    # pre-flight above loaded `state`, read the brief and resolved the pair.
    # Saved as loaded, `state` would put the old `commit_range` back (or, on a
    # new brief, drop it) and the validation snapshot would bind the old
    # header. So everything derived from either is derived again: `state`
    # reloaded, its staged `--files` record redone, the pair (and a fronted
    # run's drift list and context plan) re-resolved, the brief re-read.
    if landed_stage(args):
        state.reload()
        scope_record_moved = stage_scope_files_record(state, scope_files)
        try:
            pinned = refresh_pinned_after_stage(
                state, pinned, args, cwd=git_root or os.getcwd(), plan_path=plan_path,
            )
        except RangeError as exc:
            print(exc.message)
            sys.exit(exc.exit_code)
        pinned_kw = {"pinned": pinned} if pinned is not None else {}
        plan_snapshot, plan_sha256 = _context_plan(getattr(state, "state", None))
        if plan_bytes is not None:
            try:
                plan_bytes = plan_path.read_bytes()
                decode_document(plan_bytes, str(plan_path))
            except ValidationContextError as exc:
                print(f"ERROR: {exc}", file=sys.stderr)
                sys.exit(exc.exit_code)

    if plan_snapshot and plan_sha256 and (
        context_plan_snapshot_sha256(plan_snapshot, git_root) != plan_sha256
    ):
        print(
            f"[CONTEXT_PLAN_SNAPSHOT_CHANGED] {plan_snapshot} is missing or differs from "
            "the frozen context plan. Restore the snapshot, or re-run --review-commits "
            "with --context-plan <path> to capture it again.", file=sys.stderr,
        )
        sys.exit(EXIT_NEEDS_HUMAN)

    # The fan-out starts here, so its `--files` scope is recorded here — or a
    # previous run's is cleared — for a later `--reaggregate` to resolve the
    # same scope. Below the boundary, like the plan snapshot: only the process
    # that owns the phase writes it.
    if scope_record_moved:
        state.save()
        if scope_files is not None:
            print(
                f"Recorded the --files scope ({len(scope_files)} files) as "
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

    # Stage U: what an earlier attempt of this phase recorded, read *before* the
    # write below — `write_status` replaces every key but the two reserved
    # objects, so the `usage` the last attempt wrote is gone the instant it
    # lands. A resume skips every model that already has a `<model>.json`
    # (`run_all_reviews`'s skip branch) and a skipped slot invokes no adapter,
    # so nothing refills those entries: the regenerated report, and every
    # `--reaggregate` after it, lost the numbers the first attempt paid for.
    # Handed to the fan-out rather than merged into the collector wholesale, so
    # it is restored only for the slots whose results were REUSED — a model
    # that really re-ran is reported on what *this* attempt spent, and a
    # re-run that reported nothing keeps no stale number.
    prior_usage = recorded_usage(str(detach_phase_dir)) or {}
    # Landlock rung (2026-09-22): the previous run's sandbox words, read before
    # this run's `write_status` erases them (`announce_retired_rungs`).
    prior_served = recorded_served_models(str(detach_phase_dir)) or {}

    # The checkpoint this phase's *own* salvage path reads back (W3). Below the
    # boundary for the same reason the base fan-out writes it there — nothing
    # under that line runs in the invoker — and against `detach_phase_dir`,
    # which `get_phase_dir` has already created.
    #
    # `models_requested` is the only record anywhere of the canonical
    # `provider:model` specs this run fanned out to. `sanitize_model_name` is
    # lossy in one direction only, so `cursor-agent_cursor-grok-4_6-xhigh` can
    # never be turned back into `cursor-agent:cursor-grok-4.6-xhigh` from the
    # filename. Without this write `build_unsanitize_map` finds no `.status.json`
    # and returns `{}`, `resolve_result_files_by_model` falls through to "the
    # stem IS the identity", and `--reaggregate` re-attributes every group to the
    # stem — rewriting `grouped.json`'s `models` and `source_model`, and so its
    # bytes, and so the `grouped_sha256` that `check_task_file_inputs`
    # (`utils/subagent_tasks.py`) checks `validation_tasks.json` against moments
    # later in the same command. review-code's documented validate-then-
    # reaggregate path refused its own task file until this line existed.
    write_status(str(detach_phase_dir), {
        "phase": "code-review",
        "state": "models_running",
        "started_at": datetime.now().isoformat(),
        "models_requested": list(model_specs),
        "error": None,
        # A re-used phase dir keeps its predecessor's `progress` unless someone
        # drops it, and on the FOREGROUND lane nobody did: `claim_run` is the
        # only writer of `progress: None` and only the detached worker calls it,
        # while `write_status` carries the reserved objects over from disk by
        # design. So a re-review of the same plan opened with the last run's
        # per-model map on screen — every slot `done`, `2 ok` — and the
        # `just finished:` line, whose baseline is "what this map already calls
        # terminal", could never announce a model whose predecessor row was
        # already terminal: it was in the baseline before this run seeded it
        # queued, and in every later poll's baseline after it really finished
        # (F1, 2026-09-20). Dropping it here is the same move `claim_run` makes,
        # at the same moment — the write that claims the dir for this fan-out.
        # `report_progress` below rebuilds it two statements later.
        "progress": None,
    })
    # ...and read it straight back, because the write above cannot tell us it
    # failed. `write_status` is best-effort by contract (see the module note
    # beside `warn_stem_attribution`): no return value to check and no exception
    # to catch, so every way it can fail leaves this run proceeding *exactly* as
    # it did before the write existed, and leaves the operator with no signal at
    # all until a `--reaggregate` days later reports stems where models belong —
    # by which time the run that could have been re-done cheaply is gone.
    #
    # The probe is on `models_requested`, not on the file: that field alone is
    # what `build_unsanitize_map` needs to invert a stem, and a torn or
    # half-merged `.status.json` carrying `phase` and `state` without it is worth
    # exactly as little as no file. `read_status` returns `{}` for absent,
    # unreadable and torn alike and is documented never to raise; the try is
    # belt-and-braces so this diagnostic can never become the thing that stops
    # the dispatch it is warning about.
    #
    # Scoped to this one write. The `update_status` after the fan-out (below)
    # runs once the models have already finished, so losing it costs a resume
    # path some completion detail rather than the identity map, and does not earn
    # a second probe.
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
    if unattended and not args.models and not args.quick:
        # D6 row 2, recorded rather than merely applied (see review base): an
        # auto-selection nobody can see afterwards is indistinguishable from a
        # silent degradation. Only under `--yes`, where it replaced a question —
        # with `--yes` unset nothing about a run changes.
        unattended_mod.record_resolution(
            str(detach_phase_dir),
            unattended_mod.row(2).site_id,
            "defaults.models: " + ", ".join(model_specs),
        )
    report_progress(
        str(detach_phase_dir), step="fanout",
        models_total=len(model_specs), models_done=0, models_succeeded=0,
    )

    fix_tasks_path = None
    # §3.6: filled per slot by run_single_review when a configured fallback
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
    # Two commits need no intent-to-add marking: the working tree is not in
    # their diff (plans/review-commits.md §2.5).
    with (
        contextlib.nullcontext() if pinned is not None
        else intent_to_add_untracked(changed_files, cwd=git_root)
    ):
        # The scope manifest and one whole diff per source or test file, the
        # FIRST thing inside this block (D2.2): inside it because `git diff`
        # shows a new untracked file only once it is intent-to-add, and before
        # the fan-out because every reviewer's prompt names these two paths — a
        # slot that started first would find them missing, or holding the
        # previous run's set. Into `detach_phase_dir`, resolved up front: the
        # `get_phase_dir` call below runs only after the fan-out returns. A git
        # failure degrades the set (`[DIFF_FAILED]`, coverage partial) and the
        # fan-out goes on. At `git_root`, like the marking above: the paths are
        # root-relative, and from a subdirectory every diff came back empty and
        # the manifest called that complete coverage with no net change.
        diff_set = write_review_diff(
            base_ref, changed_files, detach_phase_dir, collapse_paths,
            scope_source=describe_scope_source(review_scope.source, base_ref, pinned),
            cwd=git_root,
            **({"head_ref": pinned.head} if pinned is not None else {}),
        )

        # A new round (not a resume of the missing models) records which
        # review is on record, through this phase's own `state`, the instance
        # it saves at the end (plans/review-commits.md §2.1): a commit brief's
        # `reviewed_header_sha256` (and its apply guard cleared), a direct
        # round's `head_ref`, or — a round with neither — no `head_ref`.
        if round_starts(
            detach_phase_dir, model_specs, diff_set.scope_id,
            rerun_all=bool(getattr(args, "rerun_all", False)),
        ) and record_round_start(state, pinned):
            state.save()

        # A model whose spec changed since the last run (`codex:x` becoming
        # `codex:x:high`) has no slot in this run to retire its old files, and a
        # later `--reaggregate` would read them back into this run's report (#30).
        retire_unselected_results(str(detach_phase_dir), model_specs)

        # Run reviews - agents receive the resolved, ordered scope (labelled
        # with its source), the diff set, and the base ref
        results = await run_all_reviews(
            model_specs,
            plan_path,
            out_dir,
            args.timeout,  # May be None - run_all_reviews will use per-provider defaults
            args.max_parallel,
            changed_files,
            base_ref,
            skip_existing=not args.rerun_all,
            served_models=served_models,
            usage=usage,
            prior_usage=prior_usage,
            tracker_out=fanout_trackers,
            scope_source=review_scope.source,
            task_ids=review_scope.task_ids,
            scope_file=diff_set.scope_file,
            diff_dir=diff_set.diff_dir,
            scope_id=diff_set.scope_id,
            diff_coverage=diff_set.coverage,
            **pinned_kw,
        )

        # Get the phase directory for code review outputs
        phase_dir = get_phase_dir(plan_path, 'code-review')
        phase_dir.mkdir(parents=True, exist_ok=True)

        # Save per-model results
        failed_models: Dict[str, str] = {}
        for model_spec, (success, issues, error) in results.items():
            if not save_model_result(prefix, model_spec, success, issues, error, phase_dir):
                failed_models[model_spec] = error or "Unknown error"

        # F11: a model `run_all_reviews`'s deadline cancelled has no result
        # and, so far, no failure entry either — in the report *or* in the map.
        # One pass writes both facts off one wording (`DEADLINE_ERROR`), so a
        # reader polling afterwards can never see a slot the report calls failed
        # while the table still calls it `running`. Idempotent against the
        # fan-out's own `finally` sweep, which normally got there first: both
        # touch only non-terminal entries, so whoever arrives first records the
        # real ending and this is the belt that catches a fan-out which returned
        # by a path the sweep missed.
        backfill_deadline_losses(
            model_specs, results, failed_models,
            tracker=fanout_trackers[0] if fanout_trackers else None,
        )

        # D3b: a salvage task exists for every model whose output would not parse
        # (emit_salvage_task materialized it above). With --exec-subagents this
        # run repairs them itself, exactly as the fan-out path in
        # review_orchestrator_base does — otherwise review-code would print
        # [REAGGREGATE_AFTER_SALVAGE] and hand the host salvage subagents it may
        # not have. A recovered model's issues are folded back into `results` so
        # grouping, validation and the report all see the post-salvage truth
        # rather than the pre-salvage one. Deliberately non-fatal: a salvage that
        # fails leaves that model failed, which is the ordinary partial-results
        # outcome.
        salvaged_models = set()
        salvaged_specs: List[str] = []
        if failed_models and exec_subagents_requested(args):
            # T5, the sibling of review_orchestrator_base's own salvage window:
            # salvage is the first stretch of the post-fan-out window and was
            # the one stretch nothing narrated. `run_all_reviews`'s ticker is
            # cancelled and awaited by the time it returns (lifetime rule 1),
            # and the phase-scoped ticker below does not start until grouping —
            # so a salvage dispatch, which is a real subagent run and can last
            # minutes, sat between them emitting no `[PROGRESS]` line at all
            # while `progress.step` still read `fanout`. Both halves of the cure
            # are the ones the validation window already uses: publish the step
            # *before* the dispatch (so the ticker's lines and a `--poll` both
            # name the work), and reach the dispatch through `asyncio.to_thread`
            # — it ends in `subagent_executor._run_sync`'s
            # `pool.submit(asyncio.run, …).result()` and would otherwise pin
            # this loop and starve the ticker for the whole window, which is
            # exactly the F6 failure one stretch over.
            report_progress(str(phase_dir), step="salvage")
            salvage_ticker = PhaseProgress(str(phase_dir), anchor=str(plan_path))
            salvage_ticker.start_ticker()
            try:
                repaired = await asyncio.to_thread(
                    dispatch_salvage_tasks,
                    args,
                    phase_dir=str(phase_dir),
                    phase='code-review',
                    plan_path=str(plan_path),
                )
            finally:
                await salvage_ticker.stop_ticker()
            repaired_paths = {os.path.abspath(path) for path in repaired}
            for model_spec in list(failed_models):
                sanitized = sanitize_model_name(model_spec)
                recovered = phase_dir / f"{sanitized}.json"
                # The dispatcher's own outcome decides, not the mere presence of
                # the file: under --rerun-all a stale result from an earlier run
                # is still sitting there and must never be read as a repair.
                if os.path.abspath(str(recovered)) not in repaired_paths:
                    continue
                if not (recovered.exists() and recovered.stat().st_size > 0):
                    continue
                try:
                    repaired_issues = json.loads(recovered.read_text(encoding="utf-8"))
                except (OSError, ValueError) as read_error:
                    print(
                        f"[{model_spec}] salvage output unreadable, leaving failed: "
                        f"{read_error}",
                        file=sys.stderr,
                    )
                    continue
                if not isinstance(repaired_issues, list):
                    print(
                        f"[{model_spec}] salvage output is not a JSON array, "
                        f"leaving failed: {recovered}",
                        file=sys.stderr,
                    )
                    continue
                print(f"[{model_spec}] recovered by salvage: {recovered}")
                results[model_spec] = (True, repaired_issues, None)
                salvaged_models.add(sanitized)
                del failed_models[model_spec]
                salvaged_specs.append(model_spec)
            # F3, 2026-09-20: the per-model map has to move with
            # `failed_models`. Deleting the entry above is what makes the write
            # below list this model under `models_completed` and count it in
            # `models_succeeded`, and the map — frozen `failed` by the fan-out,
            # and immune to a plain `tracker.done()` because terminal
            # transitions are idempotent — went on saying the opposite in the
            # same file. `record_models_salvaged` writes the flip through
            # `update_progress` exactly as `record_models_present` does for the
            # `--reaggregate` path, and carries no counters, so the restatement
            # below composes with it instead of overwriting it.
            if salvaged_specs:
                record_models_salvaged(str(phase_dir), salvaged_specs)

        # D6 row 3: partial results are usable output, so a run that lost *some*
        # models prints [PARTIAL_RESULTS: …], reports `state: "partial"` and
        # carries on to group, validate and report what exists — never a
        # question, never `--rerun-all`. A run where *no* model produced a result
        # has nothing to aggregate: exit 3 naming the retry command, taken here
        # (before the report is written and before mark_phase_completed) so a
        # total failure is never recorded as a completed phase. Same accounting
        # as review_orchestrator_base's fan-out, on the post-salvage truth.
        completed_models = [m for m in model_specs if m not in failed_models]
        if not completed_models:
            # Record the failure map before exiting (plan
            # review-run-scope-salvage-and-failure-visibility, D5.2): a later
            # `--reaggregate` of this dir reads `models_failed` back to name
            # each loss and to exit 3 when every requested reviewer failed.
            # Without it that reaggregate finds no recorded failure and names
            # the models only with the "no result file" gap reason, at exit 0.
            update_status(str(phase_dir), {
                "models_completed": [],
                "models_failed": failed_models,
            })
            print("\nERROR: All models failed")
            for model_spec, reason in failed_models.items():
                print(f"  - {model_spec}: {reason}")
            # The home check's and the jail's lines, repeated (F1): this exit
            # is the run's last word.
            print_closing_summary(str(phase_dir))
            sys.exit(unattended_mod.report_partial_results(
                completed=completed_models,
                failed=list(failed_models),
                phase_dir=str(phase_dir),
                # D2 row 5: shape 3 by construction (no reviewer produced a
                # result), so --force stays a command — with the caller's flags.
                retry_command=commit_spelling.spell_retry_command(
                    "review-code", plan_path, "--force",
                    flags=cli_common.current_replay_flags(mode="review-code"),
                ),
            ))
        unattended_mod.report_partial_results(
            completed=completed_models,
            failed=list(failed_models),
            phase_dir=str(phase_dir),
            unattended=unattended,
        )

        # The base fan-out's completion fields, on the same post-salvage truth.
        # Two things read them and neither is optional here: `status --view run`
        # prints the top-level `state` on its own line, so a review-code run left
        # at `models_running` reports as still fanning out forever; and
        # `build_unsanitize_map` unions `models_requested` with
        # `models_completed`, so writing only the first would leave this phase's
        # checkpoint a different document from the base's for the one reader that
        # has to treat both alike.
        update_status(str(phase_dir), {
            "state": "models_complete",
            "models_completed": completed_models,
            "models_failed": failed_models,
            # Added only when something was attributed, so a default run's
            # `.status.json` gains no key.
            **({"models_served": served_models} if served_models else {}),
            # Same rule, one field over: absent means no adapter reported a
            # cost, never that the run was free. This is the copy
            # `--reaggregate` reads back.
            **({"usage": usage} if usage else {}),
        })
        # D6 override (2026-09-17): the poller's copy, under `progress`.
        record_sandbox_bypassed(str(phase_dir), served_models)
        announce_retired_rungs(prior_served, served_models, anchor=str(plan_path))
        # Both counters, restated on the post-salvage truth. `models_done` is
        # the *terminal* count — every slot has finished by now, which is what
        # the retired slot counter meant by "done" and what a live progress line
        # needs, since a numerator that walks backwards at the end of a lossy run
        # can never reach `3/3`. What this site used to write into `models_done`
        # is the success count, and it lives on under its own name, so "one model
        # was lost" survives as `3/3 done, 2 ok, 1 failed` rather than as a
        # shrinking numerator.
        #
        # Counters only: no `models` key, so the map the fan-out's sweep froze is
        # left exactly as it is (`progress` merges key by key at its top level,
        # and only a write carrying `models` replaces the map wholesale).
        report_progress(
            str(phase_dir), step="grouping",
            models_total=len(model_specs),
            models_done=len(model_specs),
            models_succeeded=len(model_specs) - len(failed_models),
        )

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
        # its per-model summary is printed (above), and this one must not
        # interleave with that summary either.
        #
        # It has no per-model map and never touches `models`: it prints the step,
        # its own elapsed, and whatever counters the current step already
        # publishes — `progress.subagents`, which
        # `subagent_executor._mirror_status` writes straight through
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
        # still does not yield (F6, 2026-09-20). `dispatch_subagent_tasks` is
        # the long one — it blocks in `_run_sync`'s
        # `pool.submit(asyncio.run, …).result()` for the whole validation
        # window, which used to pin this loop and leave the executor lane with
        # exactly one `[PROGRESS]` line, the teardown one — and it is awaited
        # through `asyncio.to_thread` below, so the ticker gets its interval
        # for those minutes. Everything around it — grouping, the excerpts,
        # `prepare_batched_validation_tasks`, the merge — is still synchronous,
        # so an interval expiring inside them is serviced only once they
        # return. Moving those off the loop as well is a larger change than
        # this one.
        await asyncio.sleep(0)
        try:
            # Save raw issues as JSON
            all_issues = []
            for model_spec, (success, issues, _) in results.items():
                if success and issues:
                    for issue in drop_non_record_entries(
                        issues, model_spec, noun="issues"
                    ):
                        issue["model"] = model_spec
                        all_issues.append(issue)

            # An empty successful review replaces the previous findings too.
            # Otherwise --force can report zero issues while apply-code-fixes
            # still reads and applies the previous run's groups.
            issues_path = get_output_paths(plan_path, "code_review_issues", phase='code-review')
            issues_path = issues_path.with_suffix(".json")
            with open(issues_path, "w", encoding="utf-8") as f:
                json.dump(all_issues, f, indent=2)
            print(f"Issues JSON saved to: {issues_path}")

            # Group similar issues and validate
            validated_groups_for_report = None
            commit_attribution_pass = None
            if all_issues:
                # Add source_model field for grouping
                for issue in all_issues:
                    if "source_model" not in issue:
                        issue["source_model"] = issue.get("model", "unknown")

                grouped = group_similar_suggestions(all_issues)
                # Stamp stable content-based hashes on groups and suggestions
                grouped_list = [g.to_dict() if hasattr(g, 'to_dict') else g for g in grouped]
                stamp_stable_ids(grouped_list)
                # §2.6: a commit review names the commit behind each group, as
                # sibling fields written before grouped.json (off the hash).
                commit_attribution_pass = attribute_review_groups(
                    grouped_list, state, repo_root=git_root or project_root
                )
                grouped_path = get_output_paths(plan_path, "code_review_grouped", phase='code-review')
                # D7: the previous run's verdicts belong to the grouping this write
                # replaces; retired in the same step so no later reaggregate finds them.
                # Round-wide when the grouping changed: the batch replies are that
                # grouping's verdicts too, and a survivor is skipped as "already
                # complete" by the executor (2026-10-02, #25). `validation.json`
                # alone when the hashes are the same grouping (a resume that
                # skipped every model), so completed batches are not re-run
                # (adversarial review, 2026-10-02).
                retire_validation_for_regroup(str(grouped_path.parent), grouped_list, reason="grouped.json rewritten by a re-run")
                with open(grouped_path, 'w', encoding='utf-8') as f:
                    json.dump(save_groups_payload(grouped_list), f, indent=2)
                print(f"Grouped issues saved to: {grouped_path}")

                # Validate grouped issues (unless skipped)
                if not args.skip_validation:
                    print("\nPreparing batched validation for subagent execution...")
                    # The plan bound at load, before the fan-out, to this
                    # phase dir's own `validation-snapshot.md` (§2.3 step 5) —
                    # never a re-read of a plan edited while the models ran.
                    plan_document = plan_document_at_load or bind_plan_for_validation(
                        str(plan_path), str(phase_dir)
                    )
                    plan_content = plan_document.text

                    # No `[:30000]` here: `excerpt_context` owns the per-context
                    # budget, and slicing first could only lose more. The plan this
                    # was measured on is 44 374 chars, so the caller's slice ended
                    # mid-§4.6 and §4.7–§11 — the acceptance criteria and the whole
                    # tunable-config table — reached no validator, while four of the
                    # nine verdicts cited exactly those sections.
                    cut_report: Dict[str, Any] = {}
                    secondary, reviewed_code = build_validation_secondary_context(
                        grouped_list, plan_path, project_root=project_root,
                        cut_report=cut_report, **pinned_kw,
                    )
                    # `grouped_list`, not `grouped`: it already carries the stable
                    # `group_hash`/`display_label` `stamp_stable_ids` stamped above
                    # (and is what `grouped.json` was written from). Handing the
                    # un-stamped objects here means every group this phase reports
                    # on downstream — through `merge_validation_batches`, below —
                    # has no `group_hash`, which is the key `_overlay_human_decisions`
                    # joins on; the decisions overlay then matches nothing and
                    # reports success anyway.
                    batched_tasks = prepare_batched_validation_tasks(
                        **pinned_validation_kwargs(pinned, plan_snapshot, plan_sha256, git_root),
                        groups=grouped_list,
                        # No `Plan file:` line: the block names the bound
                        # snapshot, and a second path — the live plan — would
                        # point a validator at bytes the snapshot hash does
                        # not cover.
                        context=plan_content,
                        output_dir=str(phase_dir),
                        plan_file=str(plan_path),
                        model=args.validation_model,
                        orchestrator="code_review_orchestrator.py",
                        base_ref=base_ref,
                        secondary_context=secondary,
                        secondary_context_label=REVIEWED_CODE_CONTEXT_LABEL,
                        reviewed_code=reviewed_code,
                        # Same builder as the `--reaggregate` site, so both
                        # materialize the same instruction (T7.4).
                        extra_instructions=validation_extra_instructions(
                            cut_report,
                            **pinned_guidance_kwargs(pinned, plan_snapshot, plan_sha256),
                        ),
                        context_document=plan_document,
                        secondary_document=reviewed_code_document(
                            secondary, cut_report
                        ),
                        runner_read_refusal=materialization_read_refusal(
                            args, str(plan_path)
                        ),
                        phase="code-review",
                    )

                    # Save validation task instructions
                    validation_tasks_path = phase_dir / "validation_tasks.json"
                    with open(validation_tasks_path, 'w', encoding='utf-8') as f:
                        json.dump(batched_tasks, f, indent=2)

                    # The same unconditional write as the `--reaggregate` site
                    # above, and the same reason: the stretch starts here, not at
                    # the host-driven return further down, so the word is written
                    # before the dispatch that may never come back to write it.
                    update_status(str(phase_dir), {"state": "validation_pending"})

                    total_batches = batched_tasks["total_batches"]
                    stats = batched_tasks.get("batching_stats", {})

                    if total_batches == 1:
                        print(f"\n[VALIDATION_PENDING] {validation_tasks_path}")
                    else:
                        print(f"\n[VALIDATION_BATCHES_PENDING] {validation_tasks_path}")
                        print(f"Batches: {total_batches}")

                    print(f"\nValidation prepared for subagent execution.")
                    print(f"Groups to validate: {stats.get('total_groups', len(grouped))}")
                    print(f"HIGH priority groups: {stats.get('high_count', 0)}")
                    print(f"Normal priority groups: {stats.get('normal_count', 0)}")
                    # Fully resolved: a skill-dir placeholder no shell expands is
                    # the bug. Still starts with `uv run`, so Claude Code's
                    # Bash(uv:*) allow rule keeps matching.
                    reaggregate_cmd = commit_spelling.spell_retry_command(
                        'review-code', plan_path, '--reaggregate',
                        flags=cli_common.current_replay_flags(mode='review-code'),
                    )

                    # D3b: self-contained mode dispatches and merges here rather than
                    # exiting for a host to drive a second turn.
                    if await asyncio.to_thread(
                        dispatch_subagent_tasks,
                        args,
                        task_file=str(validation_tasks_path),
                        phase_dir=str(phase_dir),
                        phase="code-review",
                        document=batched_tasks,
                        plan_path=str(plan_path),
                        label="validation",
                        retry_command=reaggregate_cmd,
                    ):
                        validation_path = get_output_paths(
                            plan_path, "code_review_validation", phase='code-review'
                        )
                        validated_groups_for_report = merge_validation_batches(
                            str(phase_dir), batched_tasks, grouped_list, str(validation_path)
                        )
                        validated_groups = validated_groups_for_report
                    else:
                        # The plan as the user typed it (fix round 14).
                        reaggregate_cmd = commit_spelling.spell_retry_command(
                            'review-code', plan_path, '--reaggregate',
                            typed_plan=cli_common.typed_plan_for(plan_path),
                            flags=cli_common.current_replay_flags(mode='review-code'),
                        )
                        print("\nAfter validation completes, run:")
                        print(f"  {reaggregate_cmd}")
                        record_next(reaggregate_cmd)
                        # The same pair the `--reaggregate` hand-off above
                        # writes, and for the same reason: this return is the
                        # phase's ending on a host-driven run, so the checkpoint
                        # has to say so or every reader treats the run as still
                        # in flight. The phase ticker's teardown line lands
                        # after this write (its `finally` below), so the log's
                        # last `[PROGRESS]` reads `step: validation_pending`.
                        update_status(str(phase_dir), {"state": "validation_pending"})
                        report_progress(str(phase_dir), step="validation_pending")
                        return  # Exit early - Claude Code handles validation
                else:
                    print("\nSkipping validation (--skip-validation flag set)")
                    # `grouped_list`, same reason as the validated branch above:
                    # it carries the stamped `group_hash` the decisions overlay
                    # joins on.
                    validated_groups = grouped_list
                    # Every other branch above sets both names to the same value;
                    # this one set only `validated_groups`, so `--skip-validation`
                    # left `validated_groups_for_report` `None` — which starved
                    # `--apply-fixes` (its guard just below) of any group to build
                    # fix tasks from, and undercounted F4's HIGH-group total to 0.
                    validated_groups_for_report = validated_groups

                # Prepare fix tasks for Claude Code subagents if requested
                if args.apply_fixes and validated_groups_for_report:
                    fix_tasks_path = prepare_fixes_for_subagents(
                        validated_groups_for_report,
                        plan_path,
                        out_dir
                    )
            else:
                validated_groups_for_report = []
                grouped_path = get_output_paths(plan_path, "code_review_grouped", phase='code-review')
                retire_stale_validation_round(str(grouped_path.parent), reason="review returned no issues")
                grouped_path.write_text(json.dumps(save_groups_payload([]), indent=2), encoding="utf-8")
                validation_path = get_output_paths(plan_path, "code_review_validation", phase='code-review')
                validation_path.write_text("[]\n", encoding="utf-8")

            # Generate report (after validation so we can include validation status)
            # F10: `failed_models` is this run's own authoritative post-salvage map
            # (and, since F11, includes any model that never returned at all) —
            # passed in rather than left for the function to re-derive.
            report = generate_review_report(
                plan_path, results, changed_files, validated_groups_for_report,
                # §2.10: the commit header, "Introduced by" lines and filter.
                commit_review=commit_report.report_context(
                    state, commit_attribution_pass, changed_files,
                    repo_root=git_root or project_root,
                ),
                phase_dir=phase_dir, base_ref=base_ref, template_style=args.report_style,
                served_models=served_models or None,
                usage=usage or None,
                failed_models=failed_models,
                # Plan §5 T5.2: "N of M requested" counts this run's own specs.
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
                **({"pinned": pinned, "repo_root": git_root} if pinned is not None else {}),
            )

            # Save report
            report_path = get_output_paths(plan_path, "code_review", phase='code-review')
            report_path = report_path.with_suffix(".md")
            report_path.write_text(report, encoding="utf-8")
            print(f"\nReport saved to: {report_path}")

            # A detached run's caller never saw this stdout, so `status` hands the
            # artifacts back instead (no-op in the foreground). validation.json and
            # issues.json are included too (F3): apply-code-fixes reads exactly
            # those two files, and a missing validation.json makes it treat every
            # group as needs-human-decision — that was invisible to the host before,
            # since only report/report_html/grouped were ever recorded here.
            report_html_path = str(phase_dir / "report.html")
            grouped_path_out = str(phase_dir / "grouped.json")
            validation_path_out = str(phase_dir / "validation.json")
            issues_path_out = str(phase_dir / "issues.json")
            record_output_files(
                str(phase_dir),
                report=str(report_path),
                report_html=report_html_path,
                grouped=grouped_path_out,
                validation=validation_path_out,
                issues=issues_path_out,
            )

            # The terminal `MULTI_LLM_RESULT.artifacts` half of the hand-back (F2);
            # validation.json/issues.json only when they exist.
            record_review_artifacts(
                report_path, report_html_path, grouped_path_out,
                validation_path_out, issues_path_out,
            )

            # Mark phase as completed in state
            state.mark_phase_completed("code-review")
            state.save()
            # And the in-phase machine's terminal word, which `status` renders.
            update_status(str(phase_dir), {"state": "complete"})
            report_progress(str(phase_dir), step="complete")
        finally:
            await phase_ticker.stop_ticker()
            # Plan codex-sandbox-unavailable F1 (2026-09-30): every
            # `[CODEX_HOME_CHECK]` and `[JAIL_DENIED]` line of this run's
            # slots, repeated — on every ending this `finally` covers.
            print_closing_summary(str(phase_dir))

    # Summary
    # F4: distinct HIGH-importance *groups*, not raw issues (the old per-issue
    # count printed `[HIGH_PRIORITY_ISSUES] 3` for one 3-model finding), and
    # recorded in `.status.json` and on the result line — a bare print is
    # nothing a detached caller sees. The count and the record are the base's,
    # shared with review-plan and review-tasks.
    high_count = record_high_priority_groups(str(phase_dir), validated_groups_for_report)
    print("\n=== Review Summary ===")
    print(f"Total issues: {len(all_issues)}")
    print(f"High priority: {high_count} group(s)")
    if high_count > 0:
        # The finding, in the channel this skill already uses for every other
        # "you must act on this" fact ([VALIDATION_PENDING], [PARTIAL_RESULTS: …],
        # [REAGGREGATE_AFTER_SALVAGE], [CONSOLIDATION_RECOMMENDED]). It carries the
        # count, which the exit code it replaces could not.
        print(f"[HIGH_PRIORITY_ISSUES] {high_count}")

    # Report fix tasks if prepared
    if args.apply_fixes and fix_tasks_path:
        valid_count = len([g for g in (validated_groups_for_report or []) if g.get("validation_status") == "valid"])
        print(f"\n{'='*60}")
        print("IMPORTANT: SUBAGENT DELEGATION REQUIRED")
        print(f"{'='*60}")
        print(f"\nValid issues to fix: {valid_count}")
        print(f"Fix tasks file: {fix_tasks_path}")
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

    # Check for salvage requests and print reaggregate command
    import glob as glob_module
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

    # A review that found HIGH-importance issues *worked*: the report is written
    # and `code-review` is recorded completed in state.json. Under the uniform
    # contract (0 done, 1 unexpected error, 2 nothing to do, 3 needs a human) that
    # is exit 0, and the 1 this shipped with claimed an error that never happened.
    # Two things read that claim. `full` routes every phase through
    # `_verify(phase, code)`, which stops the chain on any non-zero — so the
    # workflow aborted at review-code, one step before `apply-code-fixes`, the
    # phase that exists to fix exactly what the review found. And
    # `cli_common._STATE_BY_EXIT` maps 1 to "error", so the single
    # MULTI_LLM_RESULT line every host reads reported `state: "error"` for a
    # successful run. The finding itself is not lost: it is printed as
    # [HIGH_PRIORITY_ISSUES] <n> above, and `--fail-on-high` restores a non-zero
    # exit for a standalone CI gate. The sibling fan-outs (`review-plan`,
    # `review-tasks`) already return 0 regardless of what they found.
    if high_count > 0 and getattr(args, "fail_on_high", False):
        return EXIT_NEEDS_HUMAN
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(asyncio.run(main(sys.argv[1:])))
