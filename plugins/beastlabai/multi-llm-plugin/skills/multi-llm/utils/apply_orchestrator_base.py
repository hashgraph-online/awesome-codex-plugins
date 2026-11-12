"""Base class for apply orchestrators using the Template Method pattern.

Provides ``ApplyOrchestratorBase`` — a generic base class that owns the
shared 5-phase orchestration flow (setup, load, user-feedback, batching,
output).  Each concrete orchestrator (apply_suggestions, apply_code_fixes,
apply_task_suggestions) subclasses this and overrides ~8-11 abstract or
hook methods to supply phase-specific behavior.

Also provides ``build_common_arg_parser()`` for shared CLI flag construction,
and ``OrchestratorError`` for structured error propagation with exit codes.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import logging
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import (
    Any,
    Dict,
    Generic,
    List,
    Optional,
    Sequence,
    Set,
    Tuple,
    TypeVar,
)

from .apply_output_helpers import (
    build_confirmation_needed_output,
    emit_json_output,
    invalidate_orchestrator_views,
    publish_orchestrator_views,
    write_and_emit_output,
)
from .cli_common import (
    add_retired_flag,
    build_parent_parser,
    add_scope_policy_argument,
    record_error,
    record_commit_fixes_result,
    add_notice,
    record_notice,
)
from .apply_selection_helpers import (
    merge_validation_with_groups,
    resolve_priority_args,
)
from .consolidation import load_merged_suggestions
from .filtering import (
    filter_items,
    filter_user_skipped_groups,
    should_bypass_no_selection_confirmation,
    validate_judge_decide_items_honored,
)
from . import importance as _importance
from .importance import get_highest_importance
from .judge_vocab import (
    JUDGE_AUTO_DECIDE,
    JUDGE_DECIDE,
    JUDGE_DECIDE_ITEM_IDS,
    canonical_value,
)
from .output_handler import derive_prefix, find_output_dir, output_dir_path
from .provider_registry import set_run_anchor
from .report_parser import load_html_selections, merge_selections
from .state_manager import (
    CURRENT_FORMAT_VERSION,
    StateManager,
    _parse_completion_time,
    group_join_ids,
    predates_review,
    processed_record_counts,
    stamp_or_mtime,
)
from .suggestion_batcher import (
    SuggestionBatch,
    estimate_batch_processing_stats,
    group_suggestions_for_subagents,
)
from .validation import (
    ERROR_TYPE_AMBIGUOUS,
    host_views_lock,
    prepare_batched_revalidation_tasks,
    save_validation_results,
    merge_batched_revalidation_results,
    REVALIDATION_SNAPSHOT_NAME,
    bind_document_file,
)
from .human_decisions import (
    apply_verdicts_to_work_set,
    build_judge_tasks,
    group_id_of,
    ingest_verdicts,
    judge_labels,
    native_judge_label,
    is_judge_source,
    JUDGE_SKIPPED_STATUS,
    judge_item_from_group,
    record_verdicts,
    write_judge_tasks,
)
from .apply_report import ApplyPhaseReport, applied_to_label
from . import scope_apply as _scope
from . import scope_policy as _sp
from . import unattended as _unattended
from .unattended import AGENT_DECIDE_FLAG, LEGACY_AGENT_DECIDE_FLAGS
from . import detach as _detach
from . import host_capabilities as _hosts
from . import next_phase_words as _words
from . import routes as _routes
from . import metrics
from . import scope_policy_runs as _scope_policy_runs
from . import review_orchestrator_base
from . import review_round as _review_round
from . import write_safety
from . import write_batch_scheduler
from . import write_phase_bridge
from .commit_paths import document_label, read_commit_range, is_commit_brief
from .known_checks import APPLY_FIX_BATCH_CHECKS_KEY
from .subagent_tasks import file_content_hash
from .commit_range import (
    SLUG_PATTERN,
    pinned_endpoints,
    pinned_spelling,
    RangeError,
    pinned_record,
    resolve_recorded,
    DATA_UNDER_REVIEW,
)
from .git_utils import get_project_root_from_dir, git_path, get_modified_files, get_staged_files
from .commit_apply import GUARD_SKIP_STATUS, skip_reason, take_guard
from .write_batch_scheduler import SchedulerOptions
from .write_reports import WRITE_BATCH_REPORT_FILENAME
from .write_resume import review_completed_at
from .write_safety import AuditLog, relative_to_root, WriteSafetyError
from .task_result import OUTPUT_NAME_PATTERN_BY_KIND
from .task_outcome import ExecutorError
from .check_records import write_result_notice
from .write_phase_bridge import native_run_record
from .host_capabilities import resolve_host_id
from .batch_done import resume_refusal_lines, unrecorded_logged_batches
from .write_prompt import round_superseded, superseded_round_text
from .verification_lines import native_apply_fixes_unverified_line


# ---------------------------------------------------------------------------
# Type variables for generic base class
# ---------------------------------------------------------------------------

TItem = TypeVar("TItem")
TBatch = TypeVar("TBatch")


# ---------------------------------------------------------------------------
# Custom exception
# ---------------------------------------------------------------------------


class OrchestratorError(Exception):
    """Raised for expected orchestrator failures with a specific exit code.

    Attributes:
        message: Human-readable error description including lifecycle phase
            and step context.
        exit_code: Process exit code to use when this error is not caught.
    """

    def __init__(self, message: str, exit_code: int = 1) -> None:
        super().__init__(message)
        self.message = message
        self.exit_code = exit_code


#: The ``status`` of an ``--output-format json`` stop object whose exit named
#: no reason of its own (``ApplyOrchestratorBase._stop_payload``); any other
#: code is ``error``. The words follow the exit codes in
#: docs/development/dispatcher.md ("Entrypoint and result protocol").
_STOP_STATUS_BY_EXIT: Dict[int, str] = {
    0: "stopped",
    2: "nothing_to_do",
    3: "needs_human",
}


#: The file under its phase dir that holds a phase's target as the phase
#: found it (``write_target_backup``): ``backup.md``, except for
#: apply-task-suggestions, which publishes it as ``tasks-backup.md`` (its
#: ``tasks_file_backup`` output). apply-code-fixes keeps none.
_TARGET_BACKUP_NAMES: Dict[str, str] = {"apply-task-suggestions": "tasks-backup.md"}


def target_backup_name(phase_name: str) -> str:
    """The name of *phase_name*'s target backup (:data:`_TARGET_BACKUP_NAMES`)."""
    return _TARGET_BACKUP_NAMES.get(phase_name, "backup.md")


def _system_exit_code(exc: SystemExit) -> int:
    """The process exit code a ``SystemExit`` carries (``None`` is 0)."""
    if exc.code is None:
        return 0
    return exc.code if isinstance(exc.code, int) else 1


# ---------------------------------------------------------------------------
# Validation-override allowlist
# ---------------------------------------------------------------------------

# The only override values accepted when ingested report selections are turned
# into status/marker decisions. Anything else (a typo or a stale value left in
# user_selections.json / consolidated_user_selections.json / a hand-edited
# Markdown checkbox label) is warned-and-ignored at the apply boundary rather
# than written verbatim into ``validation_status`` (which would produce a bogus
# status that silently falls through ``filter_items``). ``judge_decide`` is a
# *routing marker*, not a status: an allowlisted ``judge_decide`` is handed to
# ``_route_judge_decide_marker`` and never assigned to ``validation_status``.
# ``needs-human-decision`` is accepted because the consolidated surface can emit
# it as an override value. Every check site reads the value through
# ``judge_vocab.canonical_value`` first, so a selections file written before the
# rename (``claude_decide``) is accepted as the same marker.
VALID_OVERRIDE_VALUES: frozenset = frozenset(
    {"valid", "invalid", JUDGE_DECIDE, "needs-human-decision"}
)


def _format_override_target(value: str) -> str:
    """Render an override value for the dry-run/no-selection override print.

    ``judge_decide`` is a routing marker, not a validation status, so label it
    as such instead of printing a bare ``-> judge_decide`` (which misreads as a
    status change).
    """
    if canonical_value(value) == JUDGE_DECIDE:
        return "Let the agent decide (routing marker)"
    return value


# ---------------------------------------------------------------------------
# D6 rows 10 and 11 — what `--yes` turns on for an apply phase
# ---------------------------------------------------------------------------

def apply_unattended_defaults(args: argparse.Namespace) -> argparse.Namespace:
    """Make ``--yes`` mean what D6 rows 10/11 say it means, in Python.

    Row 11 (the no-selections confirmation) was already covered:
    ``should_bypass_no_selection_confirmation(yes=...)`` treats ``--yes`` as
    deliberate intent, so no ``confirmation_needed`` payload is emitted.

    Row 10 (``needs-human-decision`` items) was **not**: ``--agent-decide`` was
    implied only by the instruction files telling the agent to append it, which
    means a host that invoked the orchestrator directly with ``--yes`` got items
    routed to a prompt that an unattended run can never answer. D5a is explicit
    that ``--yes`` sets *both*, so it is set here — one place, every apply phase,
    whichever entry point was used.

    Mutates and returns *args* (argparse namespaces are the shared carrier here).
    """
    if getattr(args, "yes", False) and not getattr(args, "agent_decide", False):
        args.agent_decide = True
    return args


# ---------------------------------------------------------------------------
# Argument parser builder
# ---------------------------------------------------------------------------


def build_common_arg_parser(
    description: str,
    epilog: str,
    *,
    include_revalidation: bool = False,
    include_output_format: bool = False,
    include_skip: bool = False,
    include_base_ref: bool = False,
    include_approve_validation_failed: bool = False,
    include_revalidate_all_human: bool = False,
    include_internal_revalidation: bool = False,
    include_mark_completed: bool = False,
) -> argparse.ArgumentParser:
    """Build an argument parser with common flags plus per-orchestrator extras.

    Always includes the full common flag set:
        --plan-file, --yes, --force, --dry-run, --fresh, --resume,
        --approve-all, --include-low, --min-priority, --verbose,
        --approve-all-low, --skip-all-human, --approve-importance,
        --agent-decide, --include-high, --no-batch, --max-batch-size,
        --batch-review-mode, --accept-stale-consolidation, --no-confirm,
        --skip-human-review

    Conditionally includes flags based on keyword toggles to match the
    per-orchestrator flag matrix.

    Args:
        description: Parser description text.
        epilog: Parser epilog text.
        include_revalidation: Add --revalidate and --revalidate-model.
        include_output_format: Add --output-format.
        include_skip: Add --skip.
        include_base_ref: Add --base-ref.
        include_approve_validation_failed: Add --approve-validation-failed.
        include_revalidate_all_human: Add --revalidate-all-human.
        include_internal_revalidation: Accept the retired, hidden
            --internal-revalidation (it warns and changes nothing).
        include_mark_completed: Add --mark-completed.

    Returns:
        A fully-constructed ``argparse.ArgumentParser``.
    """
    parser = argparse.ArgumentParser(
        description=description,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=epilog,
        parents=[build_parent_parser()],
    )

    # =================================================================
    # Common flags (always present)
    # =================================================================
    parser.add_argument(
        "--plan-file",
        required=True,
        help="Path to the implementation plan markdown file",
    )

    # --- Legacy/Basic Options ---
    parser.add_argument(
        "--skip-human-review",
        action="store_true",
        help="[DEPRECATED] Skip needs-human-decision items (use --skip-all-human instead)",
    )

    parser.add_argument(
        "--min-priority",
        choices=["low", "medium", "high"],
        default=None,
        help="Minimum importance level to include (default: low = all valid suggestions)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be applied without outputting for execution",
    )

    parser.add_argument(
        "--no-batch",
        action="store_true",
        help="Disable smart batching (process each suggestion separately)",
    )

    parser.add_argument(
        "--max-batch-size",
        type=int,
        default=4,
        help="Maximum suggestions per batch (default: 4)",
    )

    # --- Bulk Approval Options ---
    parser.add_argument(
        "--approve-all-low",
        action="store_true",
        help="Auto-approve all LOW importance items with needs-human-decision status",
    )

    parser.add_argument(
        "--approve-all",
        action="store_true",
        help="Auto-approve ALL needs-human-decision items (use with caution, requires --yes or --force)",
    )

    parser.add_argument(
        "--skip-all-human",
        action="store_true",
        help="Skip all needs-human-decision and validation_failed items",
    )

    parser.add_argument(
        "--approve-importance",
        choices=["LOW", "MEDIUM", "HIGH"],
        nargs="+",
        help="Auto-approve needs-human-decision items at these importance levels",
    )

    parser.add_argument(
        AGENT_DECIDE_FLAG,
        *LEGACY_AGENT_DECIDE_FLAGS,
        dest="agent_decide",
        action="store_true",
        help=(
            "Let the judge agent decide each needs-human-decision item with its "
            "own judgment (no interactive prompt), instead of asking you. "
            "Equivalent to choosing 'Let the agent decide' in the interactive "
            "review. The legacy spellings --claude-decide and --let-claude-decide "
            "are still accepted. Unlike "
            "--approve-all / --skip-all-human, this is a per-item judgment, not a "
            "blanket rule: partially-valid items are salvaged (trimmed to their "
            "worthwhile core and applied) rather than skipped wholesale. Does not "
            "bypass the no-selection confirmation for valid items — combine with "
            "--no-confirm for fully unattended runs."
        ),
    )

    # --- Safety Guardrails ---
    # `--yes` / `-y` (and its `--non-interactive` spelling) come from the shared
    # cross-cutting parent parser so the flag is defined once for every entry
    # point; `--approve-all` still requires it.
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Force bulk approval operations (alias for --yes)",
    )

    parser.add_argument(
        "--include-high",
        action="store_true",
        help="Allow --approve-all to include HIGH importance items (otherwise blocked)",
    )

    # --- Resume/State Options ---
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from last checkpoint, skipping already-processed items",
    )

    parser.add_argument(
        "--fresh",
        action="store_true",
        help=(
            "Discard this phase's recorded progress (decisions, processed "
            "items, prior-changes log) and dispatch every batch again. Put "
            "back what the previous run edited first, or every batch lands "
            "twice: for apply-suggestions copy the plan back from "
            "{phase}/backup.md, for apply-task-suggestions copy tasks.md back "
            "from {phase}/tasks-backup.md; apply-code-fixes keeps no backup "
            "(undo its batches by hand; `git diff` shows them). After "
            "an --exec-subagents run, `util restore-batch` can roll the "
            "batches back newest-first instead; it holds nothing of a native "
            "run's. Only after an --exec-subagents run of the two suggestion "
            "phases is a target still carrying that run's edits refused "
            "(exit 3); after a native run, or for apply-code-fixes, nothing "
            "checks it for you. Earlier rollback points are kept aside, never "
            "overwritten."
        ),
    )

    parser.add_argument(
        "--human-task",
        action="append",
        default=None,
        metavar="BATCH=skip",
        help=(
            "With --resume and --exec-subagents, answer a batch that stopped "
            "as a partial application because its report left items out "
            "(the stop names it): --human-task apply-fix-batch-1=skip keeps "
            "what that batch applied as it stands, records each item it did "
            "not report applied as skipped at your request (never counted "
            "as applied), and goes on with the batches after it. Refused "
            "when the files it changed no longer hold what it left."
        ),
    )

    # --- Batch Review Mode ---
    parser.add_argument(
        "--batch-review-mode",
        choices=["individual", "by-importance", "summary-only"],
        default="by-importance",
        help="How to present items for human review (default: by-importance)",
    )

    parser.add_argument(
        "--accept-stale-consolidation",
        action="store_true",
        help="Accept consolidated decisions even if grouped.json has changed since consolidation",
    )

    parser.add_argument(
        "--no-confirm",
        action="store_true",
        help="Skip confirmation prompt when no user selections are found (for unattended operation)",
    )

    parser.add_argument(
        "--include-low",
        action="store_true",
        help="[DEPRECATED] No longer needed, low is now default. Use --min-priority to filter.",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose/debug output",
    )

    # Declared once, in cli_common.
    add_scope_policy_argument(parser, role="apply")

    # =================================================================
    # Conditional flags (per-orchestrator toggles)
    # =================================================================

    if include_revalidation:
        parser.add_argument(
            "--revalidate",
            action="store_true",
            help="Re-run validation only on items with validation_failed status",
        )
        parser.add_argument(
            "--revalidate-model",
            type=str,
            default=None,
            help="Model to use for revalidation (e.g., cursor-agent:opus)",
        )

    if include_output_format:
        parser.add_argument(
            "--output-format",
            choices=["json", "text"],
            default="text",
            help="Output format (default: text)",
        )

    if include_skip:
        parser.add_argument(
            "--skip",
            action="store_true",
            help="Mark the phase as skipped without applying suggestions",
        )

    if include_base_ref:
        parser.add_argument(
            "--base-ref",
            type=str,
            help="Git ref to use for diffs (default: from state file or HEAD~1)",
        )

    if include_approve_validation_failed:
        parser.add_argument(
            "--approve-validation-failed",
            action="store_true",
            help="Auto-approve items that had recoverable validation failures (e.g., parsing/timeout)",
        )

    if include_revalidate_all_human:
        parser.add_argument(
            "--revalidate-all-human",
            action="store_true",
            help="Re-run validation on ALL needs-human-decision items",
        )

    if include_internal_revalidation:
        add_retired_flag(parser, "--internal-revalidation")

    if include_mark_completed:
        parser.add_argument(
            "--mark-completed",
            action="store_true",
            help="Mark the phase as completed (call after all batches are processed)",
        )

    return parser


# ---------------------------------------------------------------------------
# Base class
# ---------------------------------------------------------------------------


class ApplyOrchestratorBase(Generic[TItem, TBatch]):
    """Template Method base class for the three apply orchestrators.

    Subclasses **must** set the following class-level attributes:

    * ``phase_name``  — e.g. ``"apply-suggestions"``
    * ``review_subdir`` — e.g. ``"review-plan"``
    * ``item_noun`` — e.g. ``"suggestion"``
    * ``supports_revalidation`` — ``True`` / ``False``
    * ``supports_skip_flag`` — ``True`` / ``False``

    And implement the nine abstract methods (see the *Abstract methods*
    section below).

    The constructor accepts a pre-parsed ``argparse.Namespace`` — the
    caller (typically ``__main__``) is responsible for invoking
    ``SubClass.parse_args()`` and passing the result.
    """

    # ------------------------------------------------------------------
    # Class-level config (subclass must override)
    # ------------------------------------------------------------------

    phase_name: str = ""
    review_subdir: str = ""
    item_noun: str = ""
    # The plural every user-facing surface prints. Left empty, `__init_subclass__`
    # fills it with the arithmetic plural (`item_noun + "s"`), which is correct
    # for "suggestion"/"task suggestion". A noun with an irregular plural (F8:
    # "fix" -> "fixs" read on every apply-code-fixes line) must set this
    # explicitly, the way `display_decisions.py` already does.
    item_noun_plural: str = ""
    supports_revalidation: bool = False
    supports_skip_flag: bool = False
    # Override to emit a different phase identifier in confirmation_needed output.
    # When empty, defaults to phase_name.
    confirmation_phase_name: str = ""
    # Whether find_output_dir should guard against double-nesting when the
    # parent directory already matches the prefix.  The code-fixes orchestrator
    # needs this (True); the suggestions and task-suggestions orchestrators
    # originally did not have this guard, so they set it to False.
    guard_double_nesting: bool = True
    # The materialized write kind this phase's batches become under
    # ``--exec-subagents`` (D3g/D3n). ``""`` means the phase has no write
    # executor path and always emits task JSON for a native invoker.
    write_kind: str = ""
    # Whether ``write_phase_artifact()`` names ONE file the phase overwrites.
    # apply-suggestions edits the plan and apply-task-suggestions the tasks file,
    # so each can snapshot its target as ``{phase}/backup.md`` before the first
    # batch. apply-code-fixes partitions by ``file_key`` — its declared set is
    # per batch and it has no single target — so it sets this False and takes no
    # backup. The backup itself is announced on stderr by ``write_target_backup``
    # and is NOT one of the paths ``ApplyPhaseReport.record_write_artifacts``
    # publishes; what it publishes for a single-target phase is ``applied_to``
    # (the file itself).
    has_single_write_target: bool = True
    # Whether this phase's batches rewrite the PLAN itself. Only
    # apply-suggestions does; apply-task-suggestions edits the tasks file and
    # apply-code-fixes edits source. It gates exactly one thing — the
    # ``plan_hash`` re-stamp in the ``--mark-completed`` branch below — because
    # for a phase that never opens the plan, drift there is a HUMAN's edit and
    # clearing `plan_changed` would swallow the warning `implement --resume`
    # exists to print. Cannot be derived from
    # ``write_phase_artifact()``: that early exit runs before `_load_inputs`
    # has resolved the tasks file.
    edits_the_plan: bool = False
    # Whether this phase applies a review's fixes to code, and so runs the
    # commit apply guard when state pins reviewed endpoints (`commit_range`, or
    # `head_ref` after a direct `--head-ref` review). Only apply-code-fixes does: the
    # other two phases edit the plan or
    # its task list, never code a commit review judged at `head`.
    guards_commit_fixes: bool = False

    # ------------------------------------------------------------------
    # Subclass validation
    # ------------------------------------------------------------------

    def __init_subclass__(cls, *, abstract: bool = False, **kwargs: Any) -> None:
        """Validate that subclasses set all required config attributes.

        ``abstract=True`` in the class statement marks a shared intermediate
        class (``apply_suggestion_phase.SuggestionApplyPhase``): it is never
        run as a phase, so its subclasses are the ones validated.
        """
        super().__init_subclass__(**kwargs)
        if abstract:
            return

        # Validate string config attributes are non-empty
        for attr in ("phase_name", "review_subdir", "item_noun"):
            value = getattr(cls, attr, "")
            if not isinstance(value, str) or not value.strip():
                raise TypeError(
                    f"{cls.__name__} must set '{attr}' to a non-empty string "
                    f"(got {value!r})"
                )

        # A subclass that leaves `item_noun_plural` unset gets the arithmetic
        # plural of its own `item_noun`, computed once here rather than at every
        # call site (F8).
        if not getattr(cls, "item_noun_plural", ""):
            cls.item_noun_plural = f"{cls.item_noun}s"

        # Validate boolean config attributes are explicitly set (not inherited defaults)
        for attr in ("supports_revalidation", "supports_skip_flag"):
            # Check that the attribute is defined directly on the subclass, not inherited
            if attr not in cls.__dict__:
                raise TypeError(
                    f"{cls.__name__} must explicitly set '{attr}' (bool). "
                    f"Do not rely on the base class default."
                )
            value = cls.__dict__[attr]
            if not isinstance(value, bool):
                raise TypeError(
                    f"{cls.__name__}.{attr} must be a bool (got {type(value).__name__})"
                )

    # ------------------------------------------------------------------
    # Constructor
    # ------------------------------------------------------------------

    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args
        # D6 rows 10/11 are recorded, not merely applied — see
        # `_record_resolution` for why they have to be buffered rather than
        # written straight through to `.status.json`.
        self._pending_resolutions: List[Tuple[str, str]] = []
        agent_decide_before = getattr(args, "agent_decide", False)
        apply_unattended_defaults(args)
        if not agent_decide_before and getattr(args, "agent_decide", False):
            self._record_resolution(
                _unattended.row(10).site_id,
                f"{AGENT_DECIDE_FLAG} implied by --yes: needs-human-decision items "
                "are judged, never prompted",
            )
        self.logger = logging.getLogger(f"orchestrator.{self.phase_name}")

        # State populated during lifecycle phases
        self.plan_path: str = ""
        self.prefix: str = ""
        self.out_dir: str = ""
        self.state: Optional[StateManager] = None
        # The reviewed endpoints state pins, strictly re-resolved in `_setup`
        # (`commit_range.Resolved`), the record they came from and the
        # repository root the guard's git reads run in. All None on a run
        # whose state pins nothing, which then behaves exactly as before.
        self._pinned: Optional[Any] = None
        self._pinned_source: Optional[str] = None
        self._repo_root: Optional[str] = None

        # Data populated during _load_and_parse_inputs
        self.groups: List[Dict[str, Any]] = []
        self.validation: List[Dict[str, Any]] = []
        self.merged: List[Dict[str, Any]] = []
        # How many groups step 23 dropped from a `--resume` as recorded done.
        # Non-zero with nothing left to apply is the closing call an earlier
        # run never made (apply-code-fixes' no-items exit reads it).
        self.resume_dropped_groups: int = 0

        # User feedback data
        self.edit_log: List[Dict[str, Any]] = []
        self.skipped_group_indices: Set[str] = set()
        self.skipped_suggestion_ids: Set[str] = set()
        self.old_skipped_ids: Set[str] = set()
        self.validation_overrides: Dict[str, str] = {}
        self.suggestion_validation_overrides: Dict[str, str] = {}
        # Group hashes / suggestion ids the reviewer pre-marked "Let the agent
        # decide" in the report. A routing marker, not a validation status —
        # marked items keep validation_status == "needs-human-decision" and
        # carry group["judge_decide"] = True so they reach the per-item judge.
        #
        # NOTE: write-only diagnostic mirror. Nothing in the production code
        # paths READS this set — all routing/filtering/formatting is driven by
        # group["judge_decide"] and the per-item decision_mode flag. It exists
        # purely as an observable record for tests/diagnostics and does NOT gate
        # any runtime behavior. (The _write_outputs() judge_decide audit keys
        # off build_human_review_config()["judge_decide_item_ids"], not this
        # set.) Do not assume populating it changes how items are routed.
        self.judge_decide_overrides: Set[str] = set()

        # Filtering results
        self.valid: List[Dict[str, Any]] = []
        self.needs_human: List[Dict[str, Any]] = []
        self.skipped: List[Dict[str, Any]] = []
        self.user_skipped_items: List[Dict[str, Any]] = []
        self.formatted_skipped: List[Dict[str, Any]] = []
        self.formatted_valid: List[Dict[str, Any]] = []
        self.formatted_human: List[Dict[str, Any]] = []

        # Batching results
        self.batches: List[Any] = []
        self.batching_stats: Dict[str, Any] = {}

        # What the write executor did, kept so the end-of-run summary can report
        # outcomes instead of restating the plan of work (the scheduler's
        # `SchedulerResult`, and the materialized tasks whose `expected_ids` say
        # how many items each batch carried).
        self.write_result: Optional[Any] = None
        self.write_tasks: List[Dict[str, Any]] = []
        # The review report path `regenerate_decisions_overlay()` rewrote, if it
        # ran and matched anything (F7) — read by `record_write_artifacts`.
        self._decisions_overlay_path: Optional[str] = None

        # The scope policy: its
        # effective apply policy, deferrals and policy change (:attr:`scope_gate`).
        self._scope_gate = _scope.ApplyScopeGate()

    # ------------------------------------------------------------------
    # D6 auto-resolutions (rows 10 and 11)
    # ------------------------------------------------------------------

    def _record_resolution(self, site_id: str, decision: str) -> None:
        """Announce one auto-resolved decision now; record it after the detach.

        `unattended.record_resolution` does both halves at once, but an apply
        phase cannot: BOTH of its decision sites (row 10 in the constructor, row
        11 in `_apply_user_feedback`) fire *before* `run()` crosses the detach
        boundary, where no run handle is active yet — so the `.status.json` half
        would be a silent no-op and `run.resolutions` would stay `[]` on exactly
        the runs that need it. The marker line is printed here (the foreground
        record, D6's minimum) and the entry is replayed into `run.resolutions`
        by :meth:`_flush_resolutions` once the worker owns the phase dir.

        Announced only under ``--yes``, like every other D6 site: with ``--yes``
        unset a run stays byte-for-byte what it was, and a bypass that came from
        ``--no-confirm`` or a bulk-approval flag alone is a flag the caller typed
        rather than a question the run answered for them.

        Announced on exactly one leg of a ``--detach`` launch, too. Both sites
        fire before the boundary, so the invoker reaches them and then
        re-executes itself as the worker, which reaches them again: one decision,
        printed twice, once on the caller's terminal and once into the log. The
        worker is the leg that keeps it — it is the leg that writes the entry to
        ``run.resolutions``, so the line and the record stay together.
        """
        if not getattr(self.args, "yes", False):
            return
        if self._is_detach_invoker():
            return
        # Row 10 fires in the constructor, before `run()` reserves stdout
        # for `--output-format json`, so the marker picks its stream here.
        with contextlib.redirect_stdout(
            sys.stderr if self.json_output() else sys.stdout
        ):
            _unattended.record_resolution(None, site_id, decision)
        self._pending_resolutions.append((site_id, decision))

    def _loaded_groups_tally(self) -> str:
        """What row 11's "apply all valid items" covers, in counts.

        ``11 task suggestion group(s) loaded: 10 valid (applied), 1 invalid
        (left out)``. The record used to name only the loaded count — "11
        loaded task suggestion group(s)" beside a review that reported 10
        valid and 1 invalid — which read as
        all eleven being applied. The statuses are the review's verdicts as
        loaded; a later override or the priority floor can still move a
        group, and the ``Filtered …`` block printed next states the final
        split.
        """
        counts: Dict[str, int] = {}
        deferred = 0
        for group in merge_validation_with_groups(
            self.groups, self.validation or []
        ):
            status = str(group.get("validation_status") or "needs-human-decision")
            if status == "valid" and self.scope_gate.counts_as_deferred(group):
                # Valid, but not applied: the scope policy defers it.
                deferred += 1
                continue
            counts[status] = counts.get(status, 0) + 1
        parts = [f"{counts.pop('valid', 0)} valid (applied)"]
        if deferred:
            parts.append(f"{deferred} valid but deferred by {_sp.FLAG} preserve")
        invalid = counts.pop("invalid", 0)
        if invalid:
            parts.append(f"{invalid} invalid (left out)")
        undecided = sum(counts.values())
        if undecided:
            parts.append(
                f"{undecided} awaiting a decision (applied only if decided valid)"
            )
        return (
            f"{len(self.groups)} {self.item_noun} group(s) loaded: "
            + ", ".join(parts)
        )

    def _no_selection_bypass_flags(self) -> str:
        """Which flag(s) made row 11's bypass deliberate, for the record.

        ``should_bypass_no_selection_confirmation`` is an ``or`` over nine flags
        and returns only a bool; an auto-resolution that says "bypassed" without
        saying *by what* is not attributable, so the same flags are named here.
        """
        set_flags = [
            name for name, value in (
                ("--no-confirm", getattr(self.args, "no_confirm", False)),
                ("--yes", getattr(self.args, "yes", False)),
                ("--force", getattr(self.args, "force", False)),
                ("--approve-all", getattr(self.args, "approve_all", False)),
                ("--skip-all-human", getattr(self.args, "skip_all_human", False)),
                ("--approve-all-low", getattr(self.args, "approve_all_low", False)),
                ("--approve-importance",
                 bool(getattr(self.args, "approve_importance", None))),
                ("--approve-validation-failed",
                 getattr(self.args, "approve_validation_failed", False)),
                ("--dry-run", getattr(self.args, "dry_run", False)),
            ) if value
        ]
        return ", ".join(set_flags) if set_flags else "(no flag)"

    def _flush_resolutions(self) -> None:
        """Replay the pre-boundary auto-resolutions into ``{phase}/.status.json``.

        Quiet: the marker line was already printed at the decision site, and
        printing it twice would make one decision read as two.
        """
        if not self._pending_resolutions:
            return
        phase_dir = os.path.join(self.out_dir, self.phase_name)
        for site_id, decision in self._pending_resolutions:
            _unattended.record_resolution(phase_dir, site_id, decision, quiet=True)
        self._pending_resolutions = []

    # ------------------------------------------------------------------
    # Template method
    # ------------------------------------------------------------------

    def run(self) -> int:
        """Template method: orchestrate the full apply flow.

        Calls the five lifecycle phases in order.  Catches
        ``OrchestratorError`` for consistent exit codes. Under
        ``--output-format json`` the run goes through :meth:`_run_json`,
        which keeps stdout to one JSON document.

        Returns:
            Process exit code (0 on success).
        """
        if self.json_output():
            return self._run_json()
        return self._run_lifecycle()

    # ------------------------------------------------------------------
    # `--output-format json`: one JSON document on stdout
    # ------------------------------------------------------------------

    def json_output(self) -> bool:
        """Whether this run promised ``--output-format json``."""
        return getattr(self.args, "output_format", "text") == "json"

    def _run_json(self) -> int:
        """Run the phase with stdout reserved for exactly one JSON document.

        Everything printed for a reader (markers, ``[AUTO_RESOLVED]`` lines,
        judging and executor progress) goes to stderr; the payload goes to the
        stdout found here, through :meth:`emit_payload`. A run that ends
        without one (a dry run, an error, a stop, a detach handshake) prints a
        fresh stop object from :meth:`_stop_payload`, never an earlier run's
        output file. The exit code is unchanged either way. Through
        ``multi_llm.py`` the dispatcher's ``MULTI_LLM_RESULT`` line still
        follows as the last stdout line (docs/development/dispatcher.md,
        "Entrypoint and result protocol", **JSON output**).
        """
        self._payload_stream = sys.stdout
        self._payload_emitted = False
        self._json_stop = None
        self._stop_error = None
        exit_code = 1
        try:
            with contextlib.redirect_stdout(sys.stderr):
                exit_code = self._run_lifecycle()
            return exit_code
        except SystemExit as exc:
            exit_code = _system_exit_code(exc)
            raise
        finally:
            if not self._payload_emitted:
                self.emit_payload(self._stop_payload(exit_code))
            self._payload_stream = None

    def emit_payload(self, output: Dict[str, Any], *, indent: Optional[int] = 2) -> None:
        """Print this run's machine payload: the one document stdout carries."""
        emit_json_output(
            output, stream=getattr(self, "_payload_stream", None), indent=indent
        )
        self._payload_emitted = True

    def emit_summary(self, batches: List[Any], output_path: str) -> None:
        """The run's closing summary: the written output file under
        ``--output-format json``, else the phase's text summary."""
        if self.json_output():
            with open(output_path, "r", encoding="utf-8") as handle:
                self.emit_payload(json.load(handle))
            return
        self.print_text_summary(batches, output_path)

    def _note_json_stop(self, status: str, message: str, **fields: Any) -> None:
        """Name what an exit that prints no payload stopped at, for :meth:`_stop_payload`."""
        self._json_stop = {"status": status, "message": message, "fields": fields}

    def _stop_payload(self, exit_code: int) -> Dict[str, Any]:
        """The fresh object an ``--output-format json`` run ends with when no
        payload was printed: what stopped, the exit code, and why."""
        note = getattr(self, "_json_stop", None) or {}
        status = note.get("status") or _STOP_STATUS_BY_EXIT.get(exit_code, "error")
        payload: Dict[str, Any] = {
            "status": status,
            "phase": self.confirmation_phase_name or self.phase_name,
            "exit_code": exit_code,
            "plan_file": getattr(self, "plan_path", "") or None,
        }
        message = note.get("message") or getattr(self, "_stop_error", None)
        if message:
            payload["message"] = message
        payload.update(note.get("fields") or {})
        return payload

    def _run_lifecycle(self) -> int:
        """The five lifecycle phases, in order; see :meth:`run`."""
        try:
            self._setup()
            self._load_and_parse_inputs()
            self._apply_user_feedback()
            # The detach boundary (D4) — "after all pre-flight, before the first
            # child". It sits HERE, not further down in _write_outputs(), because
            # _handle_human_decisions() is a child-starting step too: under
            # `--exec-subagents` (which `--detach` implies) it dispatches the
            # judge subagents synchronously. Crossing after it would leave the
            # invoker blocked on judging — minutes of agent work — instead of
            # forking and returning the log/status lines immediately, and the
            # judging would run outside the worker's `.status.json` claim, where
            # `status` cannot see it.
            #
            # Everything that can fail on the caller's terminal with no child and
            # no log still runs above: flags, inputs, loading, filtering, the
            # no-selection confirmation and the no-items early exit. Batching and
            # output assembly are pure Python over data already loaded, so the
            # worker is the right place for them.
            detached = self.maybe_detach_write_phase()
            if detached is not None:
                if detached == 0 and self._is_detach_invoker():
                    self._note_json_stop(
                        "detached",
                        "The phase runs in a detached worker; its log and "
                        "status commands are on stderr.",
                    )
                return detached
            # Past the boundary this process owns the phase dir, so the D6
            # decisions taken above can finally be written where `status` reads
            # them (`run.resolutions`).
            self._flush_resolutions()
            self._handle_human_decisions()
            # Judging moves groups between the three work sets, so the skip list
            # published downstream has to be re-derived from what it left behind
            # — not from the pre-judging snapshot `_apply_user_feedback` built.
            self._rebuild_formatted_skipped()
            # The scope gate again, after every change to the selected
            # proposals (judge approval and salvage included) and immediately
            # before batching; then this review's earlier materialization
            # under another policy, if any.
            gate = self.scope_gate
            gate.gate_work_set(self.valid, self.needs_human)
            gate.apply_policy_change(self.valid, self.needs_human,
                                     phase=self._scope_phase_word(), dry=self._scope_dry())
            if self.state is not None and not self._scope_dry():
                gate.persist(self.state, self._scope_phase_word())
            self._prepare_batches()
            return self._write_outputs()
        except OrchestratorError as e:
            self.logger.error("Orchestrator failed: %s", e)
            self._stop_error = e.message
            return e.exit_code
        except SystemExit:
            # Allow sys.exit() calls to propagate (used by early-exit paths)
            raise
        except Exception as e:
            self.logger.error(
                "Unexpected error in %s: %s",
                self.phase_name,
                e,
                exc_info=True,
            )
            self._stop_error = f"Unexpected error: {type(e).__name__}: {e}"
            return 1

    # ==================================================================
    # Phase 1 — _setup
    # ==================================================================

    def _batch_answers(self) -> List[str]:
        """The batches answered ``--human-task <batch>=skip``, checked.

        An apply phase takes only ``skip``, only on ``--resume`` and only on
        the ``--exec-subagents`` leg, whose own stop record the answer is
        checked against (``ResumeEvidence.check_partial_skips``). The
        native leg's host records such a batch itself (``util batch-done
        --skipped``). Anything else is exit 3, before any work.
        """
        values = getattr(self.args, "human_task", None) or []
        if not values:
            return []
        word = self.confirmation_phase_name or self.phase_name
        problems: List[str] = []
        try:
            decisions = _unattended.parse_human_task_decisions(values)
        except _unattended.NeedsHuman as exc:
            decisions = {}
            problems.append(str(exc).replace("ERROR: ", "", 1).strip())
        for task_id, action in decisions.items():
            if action != "skip":
                problems.append(
                    f"--human-task {task_id}={action}: an apply batch takes "
                    f"only =skip (keep what a stopped batch applied and go on "
                    f"without the items it left out)"
                )
        if not getattr(self.args, "resume", False):
            problems.append(
                "--human-task answers a stopped batch, so it needs --resume"
            )
        if not getattr(self.args, "exec_subagents", False):
            problems.append(
                "--human-task answers a batch the --exec-subagents leg stopped; "
                "on this leg the batch loop is yours, and a batch kept as it "
                "stands is recorded with util batch-done --skipped <id>"
            )
        if problems:
            for line in problems:
                print(f"ERROR: {line}", file=sys.stderr)
            print(
                f"       Nothing was changed. The {word} stop names the answer "
                f"it takes and the command that carries it.",
                file=sys.stderr,
            )
            # The refusal is the result
            # line's `error`, which the tool routes relay; it used to be on
            # stderr alone, and the line said it named no error.
            record_error(
                f"{word} cannot take this --human-task answer: "
                f"{'; '.join(problems)}. Nothing was changed; the {word} stop "
                f"names the answer it takes and the command that carries it."
            )
            raise OrchestratorError(
                f"Phase _setup, step 6b: --human-task refused: {problems[0]}",
                exit_code=3,
            )
        return sorted(decisions)

    def _document_title(self, plan_word: str = "Plan") -> str:
        """*plan_word* (``Plan``, ``Plan file``) as today, or ``Commit brief``
        when the plan's ``state.json`` records a ``commit_range``: the phase's
        own lines never call a commit brief a plan, through the one owner of the word,
        ``commit_paths.document_label``. Read-only; no state is a plan."""
        try:
            word = document_label({"commit_range": read_commit_range(
                os.path.abspath(str(self.args.plan_file)))})
        except Exception:  # noqa: BLE001 - advisory: the plan's word stands
            return plan_word
        return plan_word if word == "plan" else word.capitalize()

    def _stop_user_commands(self) -> Dict[str, str]:
        """The stop's answer in this host's own spelling:
        ``skip``, the resume carrying ``--human-task {task_id}=skip``. Empty
        when nothing can be spelled; the stop then names the flags."""
        try:
            host_id = _hosts.resolve_host_id(explicit=getattr(self.args, "host", None))
            route = _routes.resolve_route(host_id)
            handle = _detach.active_run()
            plan_arg = (
                (handle.plan_arg if handle is not None else None)
                or os.environ.get(_detach.PLAN_ARG_ENV)
                or str(self.args.plan_file)
            )
            word = self.confirmation_phase_name or self.phase_name
            return {
                "skip": _words.phase_command(
                    plan_arg, host_id, route, word,
                    "--resume", "--human-task", "{task_id}=skip",
                ),
            }
        except Exception:  # noqa: BLE001 - advisory: the flags are named instead
            return {}

    def _setup(self) -> None:
        """Phase 1: Environment and argument validation.

        Steps 1-10 from the lifecycle spec.
        """
        self.logger.debug("Entering _setup phase")

        # Step 1: Resolve plan path
        self.plan_path = os.path.abspath(self.args.plan_file)

        # Step 2: Handle --skip (if supports_skip_flag)
        if self.supports_skip_flag and getattr(self.args, "skip", False):
            # A state file this apply cannot trust is refused before it is
            # loaded and saved over (here, `--mark-completed` and step 3a).
            self._refuse_unusable_state()
            state = StateManager(Path(self.plan_path))
            state.mark_phase_skipped(self.phase_name, "User chose to skip")
            state.save()
            self.emit_payload(
                {
                    "status": "skipped",
                    "message": f"{self.phase_name.capitalize()} phase skipped by user request",
                },
                indent=None,
            )
            sys.exit(0)

        # Handle --mark-completed: the host's POST-LOOP finalization command, the
        # native counterpart of `WriteBatchScheduler._finalize`. It is the only
        # place the native path records completion — the emit path records the
        # phase *started* instead — so a host whose batch loop stopped early
        # simply never reaches it and the phase stays `in_progress`.
        #
        # The word persisted is `confirmation_phase_name or phase_name`, the same
        # fallback already used for the confirmation-needed output and for
        # `maybe_detach`'s mode. It matters for exactly one class:
        # apply-code-fixes runs under `phase_name = "apply-fixes"` (its phase
        # DIR, which `full_workflow_orchestrator.WRITE_PHASE_DIRS` and the
        # instruction's `prior_changes append --phase apply-fixes` both depend
        # on) while its canonical completion word is
        # `confirmation_phase_name = "apply-code-fixes"` — what
        # `check_workflow_prerequisites.PHASE_PREREQUISITES` is keyed on and what
        # the executor path writes via `PHASE_BY_WRITE_KIND`. Persisting
        # `phase_name` here would record a third spelling nothing reads.
        # `apply-suggestions` and `apply-task-suggestions` leave
        # `confirmation_phase_name` unset, so the fallback yields their existing
        # word byte-for-byte. The stdout `message` below stays on `phase_name`:
        # it names the orchestrator the host invoked, not the state key.
        if getattr(self.args, "mark_completed", False):
            self._refuse_unusable_state()
            state = StateManager(Path(self.plan_path))
            state.mark_phase_completed(
                self.confirmation_phase_name or self.phase_name
            )
            # This command runs AFTER the host applied the batches, so for a
            # phase whose write target IS the plan the file on disk no longer
            # matches the hash the pre-run state recorded. Re-stamping here is
            # the native leg's counterpart of
            # `WriteBatchScheduler._finalize`'s own re-stamp: without it the
            # next `StateManager` reads the plugin's own edit as a human
            # editing the plan mid-workflow and `implement --resume` reports
            # "Plan has changed since last session" for a change the plugin
            # made. Gated, because for the two phases that
            # never open the plan the same drift is a human's edit.
            if self.edits_the_plan:
                state.refresh_plan_hash()
            # The scope policy's completion record: "eligible work
            # completed" with the deferrals kept, or the concrete blockers a
            # `preserve` batch declined with, which stop this call at exit 3.
            scope_blockers = self._scope_close(state)
            state.save()
            self.print_native_tests_not_run()
            # The native
            # leg's closing line names the file its batches edited, as the
            # executor's progress line does.
            target = self._completed_target_label()
            self.emit_payload(
                {
                    "status": "completed",
                    "message": f"{self.phase_name} phase marked as completed"
                    + (f"; its batches edited {target}" if target else ""),
                },
                indent=None,
            )
            if scope_blockers:
                self._scope_report_blockers(scope_blockers)
                sys.exit(3)
            sys.exit(0)

        # Step 3: Validate plan file exists
        if not os.path.isfile(self.plan_path):
            print(
                f"ERROR: {self._document_title('Plan file')} not found: "
                f"{self.args.plan_file}",
                file=sys.stderr,
            )
            print(
                f"       Resolved path: {self.plan_path}",
                file=sys.stderr,
            )
            raise OrchestratorError(
                f"Phase _setup, step 3: {self._document_title('Plan file')} not "
                f"found: {self.plan_path}",
                exit_code=1,
            )

        # The anchor capture point — absolute, before anything can
        # chdir and before any provider read that decides routing. One line
        # here covers all three apply modes. It sits *below* the `--skip` and
        # `--mark-completed` early exits on purpose: those record a phase word
        # and stop, starting no run for an anchor to belong to.
        set_run_anchor(self.plan_path)

        # Step 3a: a state file this apply cannot trust is refused before
        # anything below loads it (step 10) and saves over it.
        self._refuse_unusable_state()

        # Step 4: Derive prefix + output dir
        self.prefix = derive_prefix(self.plan_path)
        self.out_dir = find_output_dir(
            self.plan_path, guard_double_nesting=self.guard_double_nesting
        )

        print(f"{self._document_title()}: {self.plan_path}", file=sys.stderr)
        print(f"Output directory: {self.out_dir}", file=sys.stderr)
        print(f"Prefix: {self.prefix}", file=sys.stderr)

        # Step 5: pre_validate_hook (subclass-specific setup)
        try:
            self.pre_validate_hook()
        except OrchestratorError:
            raise
        except Exception as e:
            raise OrchestratorError(
                f"Phase _setup, step 5: pre_validate_hook failed: {e}",
                exit_code=1,
            ) from e

        # Step 6: Safety guardrails for --approve-all
        if getattr(self.args, "approve_all", False):
            if not (getattr(self.args, "yes", False) or getattr(self.args, "force", False)):
                print(
                    "ERROR: --approve-all requires --yes or --force flag for safety.",
                    file=sys.stderr,
                )
                print(
                    "       This prevents accidental bulk approval of potentially risky changes.",
                    file=sys.stderr,
                )
                raise OrchestratorError(
                    "Phase _setup, step 6: --approve-all requires --yes or --force",
                    exit_code=1,
                )

        # Step 6b: `--human-task <batch>=skip` answers a stopped
        # partial application on the executor leg's resume, and nothing else.
        self.partial_skips = self._batch_answers()

        # Step 7: Deprecation warnings
        if getattr(self.args, "skip_human_review", False):
            print(
                "DEPRECATION WARNING: --skip-human-review is deprecated.",
                file=sys.stderr,
            )
            print(
                "                     Please use --skip-all-human instead.",
                file=sys.stderr,
            )

        # Step 8: Warn on contradictory --agent-decide combinations.
        # --agent-decide only affects items that remain needs-human-decision;
        # bulk flags that drain that bucket leave it with nothing to judge.
        if getattr(self.args, "agent_decide", False):
            draining_flags = [
                name
                for name, flag in (
                    ("--skip-all-human", getattr(self.args, "skip_all_human", False)),
                    ("--skip-human-review", getattr(self.args, "skip_human_review", False)),
                    ("--approve-all", getattr(self.args, "approve_all", False)),
                )
                if flag
            ]
            if draining_flags:
                print(
                    f"WARNING: {AGENT_DECIDE_FLAG} has no effect alongside "
                    f"{', '.join(draining_flags)}; those flags resolve all "
                    "needs-human-decision items before the judge agent can "
                    "judge them.",
                    file=sys.stderr,
                )

        # Step 9: Validate output dir exists
        if not os.path.isdir(self.out_dir):
            print(
                f"ERROR: Output directory not found: {self.out_dir}",
                file=sys.stderr,
            )
            raise OrchestratorError(
                f"Phase _setup, step 9: Output directory not found: {self.out_dir}",
                exit_code=1,
            )

        # Step 9a: the review's verdicts belong to the round on record, checked
        # before anything is written (`--fresh` below clears progress).
        self._refuse_another_rounds_verdicts()

        # Step 10: Initialize StateManager + handle --fresh
        self.state = StateManager(Path(self.plan_path))

        # Step 10a: the reviewed endpoints, resolved strictly before anything
        # is written (`--fresh` below), any model runs or any batch is built:
        # a recorded SHA that no longer names a commit is exit 3
        # `[RANGE_UNRESOLVED]`, never a `HEAD~1` fallback.
        self._resolve_pinned_endpoints()

        # Step 10b: the effective scope policy of this apply, before any filtering
        # (docs/development/write-scheduler.md#scope-policy-at-the-write-seam).
        self._resolve_scope_policy()

        if getattr(self.args, "fresh", False) and not getattr(
            self.args, "resume", False
        ):
            # Before anything is cleared: a target still carrying the previous
            # run's edits would take every batch a second time, and the clear
            # below is what a plain re-run needs to skip them.
            refusal = self._fresh_target_refusal()
            if refusal:
                print(refusal, file=sys.stderr)
                raise OrchestratorError(
                    "Phase _setup, step 10: --fresh refused, the target still "
                    "carries the previous run's edits",
                    exit_code=3,
                )

        if getattr(self.args, "fresh", False):
            print(
                "[orchestrator] Fresh start requested, clearing previous progress...",
                file=sys.stderr,
            )
            self.state.clear_human_decisions(self.phase_name)
            self.state.clear_processed_items(self.phase_name)
            self.state.clear_processing_progress(self.phase_name)
            if self.write_kind == "apply_code_fixes":
                # What the void run's batches reported about
                # their own checks is no earlier batch of this run.
                self.state.clear_key(APPLY_FIX_BATCH_CHECKS_KEY)
            self.state.save()
            # Clear prior changes history for a fresh start
            prior_changes_file = Path(self.out_dir) / "prior_changes.jsonl"
            if prior_changes_file.exists():
                prior_changes_file.unlink()
                print(
                    "[orchestrator] Cleared prior changes history.",
                    file=sys.stderr,
                )

        # Step 10c: this review's earlier materialization under another
        # policy (after `--fresh`, which clears the records it reads). Its
        # refusal comes before the explicit policy is recorded, so a refused
        # run leaves the round's record as it found it.
        self._scope_detect_change()
        self._record_explicit_scope_policy()

        self.logger.info(
            "Setup complete: plan=%s, out_dir=%s", self.plan_path, self.out_dir
        )

    # ==================================================================
    # Phase 2 — _load_and_parse_inputs
    # ==================================================================

    def _load_and_parse_inputs(self) -> None:
        """Phase 2: Data loading and report parsing.

        Steps 11-17 from the lifecycle spec.
        """
        self.logger.debug("Entering _load_and_parse_inputs phase")

        # Step 11: load_data() -> (groups, validation)
        try:
            self.groups, self.validation = self.load_data()
        except OrchestratorError:
            raise
        except Exception as e:
            raise OrchestratorError(
                f"Phase _load_and_parse_inputs, step 11: load_data failed: {e}",
                exit_code=1,
            ) from e

        # Step 11a: the round the verdicts came from is still the one on record.
        self._recheck_verdicts_round("Phase _load_and_parse_inputs, step 11a")

        self.logger.info(
            "Loaded %d groups, %d validation results",
            len(self.groups),
            len(self.validation) if self.validation else 0,
        )
        print(f"Loaded {len(self.groups)} {self.item_noun} groups", file=sys.stderr)
        if self.validation is not None:
            print(
                f"Loaded {len(self.validation)} validation results",
                file=sys.stderr,
            )

        # Step 12: post_load_hook
        try:
            self.post_load_hook()
        except OrchestratorError:
            raise
        except Exception as e:
            raise OrchestratorError(
                f"Phase _load_and_parse_inputs, step 12: post_load_hook failed: {e}",
                exit_code=1,
            ) from e

        # Step 13: Parse user edits
        review_dir = os.path.join(self.out_dir, self.review_subdir)
        report_path = os.path.join(review_dir, "report.md")

        try:
            edited_descriptions = self.parse_user_edits(report_path)
        except Exception as e:
            raise OrchestratorError(
                f"Phase _load_and_parse_inputs, step 13: parse_user_edits failed: {e}",
                exit_code=1,
            ) from e

        if edited_descriptions:
            try:
                self.groups, self.edit_log = self.merge_user_edits(
                    self.groups, edited_descriptions
                )
            except Exception as e:
                raise OrchestratorError(
                    f"Phase _load_and_parse_inputs, step 13: merge_user_edits failed: {e}",
                    exit_code=1,
                ) from e
            print(
                f"Merged {len(self.edit_log)} user-edited descriptions",
                file=sys.stderr,
            )

        # Step 14: Parse skips from report
        try:
            skips_result = self.parse_skips_from_report(report_path)
        except Exception as e:
            raise OrchestratorError(
                f"Phase _load_and_parse_inputs, step 14: parse_skips_from_report failed: {e}",
                exit_code=1,
            ) from e

        # parse_skips_from_report returns a tuple of
        # (skipped_group_indices, skipped_suggestion_ids, old_skipped_ids)
        if isinstance(skips_result, tuple) and len(skips_result) == 3:
            self.skipped_group_indices, self.skipped_suggestion_ids, self.old_skipped_ids = skips_result
        else:
            # Fallback: single set of skipped IDs treated as group indices
            self.skipped_group_indices = skips_result if isinstance(skips_result, set) else set()

        # Step 15: Parse validation overrides from report
        try:
            overrides_result = self.parse_validation_overrides_from_report(report_path)
        except Exception as e:
            raise OrchestratorError(
                f"Phase _load_and_parse_inputs, step 15: parse_validation_overrides_from_report failed: {e}",
                exit_code=1,
            ) from e

        if isinstance(overrides_result, tuple) and len(overrides_result) == 2:
            self.validation_overrides = dict(overrides_result[0])
            self.suggestion_validation_overrides = dict(overrides_result[1])
        else:
            self.validation_overrides = dict(overrides_result) if overrides_result else {}

        # Step 16: Load HTML selections + apply HTML-edited descriptions
        self.load_html_selections(review_dir, edited_descriptions)

        # Step 17: Load/apply consolidated (C-level) decisions
        self.load_and_apply_consolidated_decisions(review_dir)

        # Log skip/override summary
        if self.skipped_group_indices:
            print(
                f"User skipped {len(self.skipped_group_indices)} groups: "
                f"{sorted(self.skipped_group_indices)}",
                file=sys.stderr,
            )
        if self.skipped_suggestion_ids:
            print(
                f"User skipped {len(self.skipped_suggestion_ids)} individual suggestions: "
                f"{', '.join(sorted(self.skipped_suggestion_ids))}",
                file=sys.stderr,
            )
        if self.old_skipped_ids:
            print(
                f"User skipped {len(self.old_skipped_ids)} suggestions (old format): "
                f"{', '.join(sorted(self.old_skipped_ids))}",
                file=sys.stderr,
            )

        self.logger.info(
            "Input parsing complete: %d groups, %d skips, %d overrides",
            len(self.groups),
            len(self.skipped_group_indices) + len(self.skipped_suggestion_ids),
            len(self.validation_overrides),
        )

    # ==================================================================
    # Phase 3 — _apply_user_feedback
    # ==================================================================

    def _apply_user_feedback(self) -> None:
        """Phase 3: Validation, filtering, and user confirmation.

        Steps 18-27 from the lifecycle spec.
        """
        self.logger.debug("Entering _apply_user_feedback phase")

        # Step 18: Print preference summary to stderr
        has_any_preferences = (
            self.skipped_group_indices
            or self.skipped_suggestion_ids
            or self.old_skipped_ids
            or self.edit_log
            or self.validation_overrides
            or self.suggestion_validation_overrides
        )

        if has_any_preferences:
            parts: List[str] = []
            total_skips = (
                len(self.skipped_group_indices)
                + len(self.skipped_suggestion_ids)
                + len(self.old_skipped_ids)
            )
            if total_skips:
                parts.append(f"{total_skips} items will be skipped")
            if self.validation_overrides:
                parts.append(f"{len(self.validation_overrides)} validation overrides")
            if self.edit_log:
                parts.append(f"{len(self.edit_log)} edited descriptions")
            if self.suggestion_validation_overrides:
                parts.append(
                    f"{len(self.suggestion_validation_overrides)} per-suggestion overrides"
                )
            print(
                f"User preference summary: {', '.join(parts)}", file=sys.stderr
            )
            # Detail which groups are skipped by theme (hash-based lookup)
            if self.skipped_group_indices:
                _hash_to_info: Dict[str, Tuple[str, str]] = {}
                for group in self.groups:
                    ghash = group.get("group_hash", "")
                    if ghash:
                        _hash_to_info[ghash] = (
                            group.get("display_label", ghash[:8]),
                            group.get("theme", "Unknown"),
                        )
                for ghash in sorted(self.skipped_group_indices):
                    if ghash in _hash_to_info:
                        label, theme = _hash_to_info[ghash]
                        print(
                            f"  Skipping group {label}: {theme}",
                            file=sys.stderr,
                        )
                    else:
                        print(
                            f"  Skipping group [{ghash[:8]}]",
                            file=sys.stderr,
                        )
            if self.skipped_suggestion_ids:
                print(
                    f"  Skipping individual suggestions: "
                    f"{', '.join(sorted(self.skipped_suggestion_ids))}",
                    file=sys.stderr,
                )
            # Detail validation overrides
            if self.validation_overrides:
                _hash_to_info_ovr: Dict[str, Tuple[str, str]] = {}
                for group in self.groups:
                    ghash = group.get("group_hash", "")
                    if ghash:
                        _hash_to_info_ovr[ghash] = (
                            group.get("display_label", ghash[:8]),
                            group.get("theme", "Unknown"),
                        )
                for ghash in sorted(self.validation_overrides):
                    new_status = _format_override_target(
                        self.validation_overrides[ghash]
                    )
                    if ghash in _hash_to_info_ovr:
                        label, theme = _hash_to_info_ovr[ghash]
                        print(
                            f"  Override {label} ({theme}): -> {new_status}",
                            file=sys.stderr,
                        )
                    else:
                        print(
                            f"  Override [{str(ghash)[:8]}]: -> {new_status}",
                            file=sys.stderr,
                        )
            if self.suggestion_validation_overrides:
                for sid in sorted(self.suggestion_validation_overrides):
                    new_status = _format_override_target(
                        self.suggestion_validation_overrides[sid]
                    )
                    print(
                        f"  Override {sid}: -> {new_status}",
                        file=sys.stderr,
                    )
        else:
            # Step 19: No-selection confirmation prompt
            print(
                "No user preferences detected (checked user_selections.json, "
                "consolidated_user_selections.json, and report.md)",
                file=sys.stderr,
            )
            if not should_bypass_no_selection_confirmation(
                no_confirm=getattr(self.args, "no_confirm", False),
                yes=getattr(self.args, "yes", False),
                force=getattr(self.args, "force", False),
                approve_all=getattr(self.args, "approve_all", False),
                skip_all_human=getattr(self.args, "skip_all_human", False),
                approve_all_low=getattr(self.args, "approve_all_low", False),
                approve_importance=getattr(self.args, "approve_importance", None),
                approve_validation_failed=getattr(
                    self.args, "approve_validation_failed", False
                ),
                dry_run=getattr(self.args, "dry_run", False),
            ):
                output = build_confirmation_needed_output(
                    phase=self.confirmation_phase_name or self.phase_name,
                    message=self._scope_confirmation_message(
                        "No user selections found in user_selections.json, "
                        "consolidated_user_selections.json, or report.md. "
                        "ALL valid items will be applied if you proceed. "
                        "To proceed, re-run with --no-confirm, --yes, or any bulk approval flag."
                    ),
                    item_count=len(self.groups),
                )
                self.emit_payload(output)
                sys.exit(0)
            # Row 11 taken, and therefore recorded. This is the decision a `--yes`
            # apply run actually makes — "nobody selected anything, apply ALL of
            # it" — and until now it left no trace at all: not in the log (the
            # notice above is printed before the detach boundary), not in
            # `run.resolutions`, not in the terminal payload.
            #
            # Except under `--dry-run`, which is itself one of the nine bypass
            # flags: that run exits at step 30 having applied nothing, so
            # recording "apply all valid items" would put a decision the run
            # never took into `run.resolutions` and the log.
            if not getattr(self.args, "dry_run", False):
                self._record_resolution(
                    _unattended.row(11).site_id,
                    f"apply all valid items: {self._loaded_groups_tally()}; "
                    f"bypassed by {self._no_selection_bypass_flags()}",
                )

        # Step 21: Handle revalidation (if supports_revalidation)
        self.handle_revalidation()

        # Step 22: Merge validation with groups
        self.merged = merge_validation_with_groups(self.groups, self.validation)

        # Step 23: Handle --resume
        #
        # `processed_<phase>` is the per-batch record (`util batch-done` on
        # the native leg, the scheduler on the executor leg): one
        # entry per member id of every batch recorded,
        # keyed by the id the batch's `expected_ids` carry — the group's
        # stamped `group_hash`, which is what the suggestion's `group_id` was
        # copied from. A `failed` record keeps the group in the work set (the
        # batch is dispatched again, as the executor leg re-dispatches a
        # failed batch), and so does a declined or skipped record of an
        # earlier review (a later review's re-report of an item
        # its batch did not apply is offered again, on both legs); every other
        # record drops it (`processed_record_counts`). On the
        # executor leg a record the executor wrote drops nothing: its resume
        # evidence is the result file on disk (`ResumeEvidence.done_evidence`), under the
        # batch's own id. Records and human decisions are looked up by
        # `group_join_ids`: the stamped id, or the plain content hash only
        # where it names one group, so one same-content group's record never
        # drops or decides the others.
        if getattr(self.args, "resume", False) and self.state is not None:
            previous_decisions = self.state.get_all_human_decisions(self.phase_name)
            executor_leg = bool(self.write_kind) and bool(
                getattr(self.args, "exec_subagents", False)
                or getattr(self.args, "dry_run_subagents", False)
            )

            review_stamp = file_content_hash(
                os.path.join(self.out_dir, self.review_subdir, "grouped.json"))
            processed_items = {
                key: record
                for key, record in self.state.get_processed_items(self.phase_name).items()
                if processed_record_counts(
                    record, review_stamp=review_stamp, executor_leg=executor_leg)
            }

            unprocessed_merged = []
            for g, ids in zip(self.merged, group_join_ids(self.merged)):
                if any(key in processed_items for key in ids):
                    continue
                decision = next(
                    (previous_decisions[key] for key in ids if key in previous_decisions),
                    None,
                )
                if decision is not None:
                    if decision["decision"] == "approved":
                        g["validation_status"] = "valid"
                        g["validation_reason"] = (
                            "Previously approved by human (resumed)"
                        )
                    elif decision["decision"] == "skipped":
                        g["validation_status"] = "invalid"
                        g["validation_reason"] = (
                            "Previously skipped by human (resumed)"
                        )
                unprocessed_merged.append(g)

            # On the write executor's leg its own records count for nothing
            # here: the batches an earlier run finished are kept by the
            # scheduler from their result files, which no batch exists yet to
            # look up. A count here read "0 already processed, 12 remaining"
            # on a resume that then kept batch 0, so
            # this leg defers to the scheduler's own `resume:` line.
            if executor_leg and not processed_items:
                print(
                    f"[resume] {len(unprocessed_merged)} item(s) in scope; the "
                    f"write executor keeps every batch an earlier run finished "
                    f"(its result file is on disk) and dispatches the rest "
                    f"(a `resume:` line below names any it kept)",
                    file=sys.stderr,
                )
            else:
                print(
                    f"[resume] {len(processed_items)} already processed, "
                    f"{len(unprocessed_merged)} remaining",
                    file=sys.stderr,
                )
            self.resume_dropped_groups = len(self.merged) - len(unprocessed_merged)
            self.merged = unprocessed_merged

        # Step 24: Apply validation overrides
        self.apply_group_validation_overrides()

        # Apply per-suggestion validation overrides
        self.apply_suggestion_validation_overrides()

        # Step 25: Filter user-skipped + by status/importance
        self.user_skipped_items = []
        if (
            self.skipped_group_indices
            or self.skipped_suggestion_ids
            or self.old_skipped_ids
        ):
            for group_idx, group in enumerate(self.merged, 1):
                theme = group.get("theme", "")
                suggestions = group.get("suggestions", [])
                primary_title = (
                    suggestions[0].get("title", theme) if suggestions else theme
                )
                importance = get_highest_importance(group)
                ghash = group.get("group_hash", "")
                if ghash and ghash in self.skipped_group_indices:
                    self.user_skipped_items.append(
                        {
                            "title": primary_title,
                            "theme": theme,
                            "importance": importance,
                        }
                    )
                else:
                    for sugg_idx, sugg in enumerate(suggestions, 1):
                        shash = sugg.get("suggestion_hash", "")
                        positional_id = f"G{group_idx}S{sugg_idx}"
                        old_id = sugg.get("id", "")
                        skipped_ids_upper = {
                            s.upper() for s in self.skipped_suggestion_ids
                        }
                        is_skipped = (
                            (shash and shash in self.skipped_suggestion_ids)
                            or positional_id.upper() in skipped_ids_upper
                            or old_id in self.old_skipped_ids
                        )
                        if is_skipped:
                            self.user_skipped_items.append(
                                {
                                    "title": sugg.get("title", theme),
                                    "theme": theme,
                                    "importance": sugg.get(
                                        "importance", importance
                                    ),
                                }
                            )
            self.merged, user_skipped_count = filter_user_skipped_groups(
                self.merged,
                self.skipped_group_indices,
                self.skipped_suggestion_ids,
                self.old_skipped_ids,
            )
            if user_skipped_count > 0:
                print(
                    f"Filtered {user_skipped_count} user-skipped items",
                    file=sys.stderr,
                )

        # Safety check for --approve-all with HIGH importance
        if getattr(self.args, "approve_all", False) and not getattr(
            self.args, "include_high", False
        ):
            high_importance_count = sum(
                1
                for g in self.merged
                if get_highest_importance(g) == "HIGH"
                and g.get("validation_status")
                in ("needs-human-decision", "validation_failed")
            )
            if high_importance_count > 0:
                print(
                    f"ERROR: --approve-all would approve {high_importance_count} HIGH importance items.",
                    file=sys.stderr,
                )
                print(
                    "       Use --include-high to explicitly allow approving HIGH importance items.",
                    file=sys.stderr,
                )
                if getattr(self.args, "approve_validation_failed", False):
                    print(
                        "       Or use --approve-validation-failed to only approve recoverable failures.",
                        file=sys.stderr,
                    )
                raise OrchestratorError(
                    "Phase _apply_user_feedback, step 25: --approve-all blocked by HIGH importance items",
                    exit_code=1,
                )

        # Filter items by validation status and importance
        min_priority = resolve_priority_args(self.args)
        self.valid, self.needs_human, self.skipped, dry_run_report = filter_items(
            groups=self.merged,
            min_priority=min_priority,
            skip_human_review=getattr(self.args, "skip_human_review", False),
            approve_all_human=getattr(self.args, "approve_all", False),
            approve_low_human=getattr(self.args, "approve_all_low", False),
            approve_importance_levels=getattr(self.args, "approve_importance", None),
            approve_validation_failed=getattr(
                self.args, "approve_validation_failed", False
            ),
            skip_all_human=getattr(self.args, "skip_all_human", False),
            dry_run=getattr(self.args, "dry_run", False),
        )

        # Step 25a: the commit apply guard, on
        # what filtering left to apply or decide, before the no-items exit,
        # human decisions and batching, so both legs take the same decision
        # and a run whose fixes it skips entirely still prints its block.
        self._apply_commit_guard()

        # Step 25b: the scope-policy gate over what selection left,
        # before the counts, the dry-run report, the no-items exit and the
        # judge, so each describes the same eligible set. A pass-through
        # under `expand`; re-applied in `run()` after judging. What an earlier
        # run of this review landed under another policy leaves first: it is
        # applied, never this run's deferral.
        self.scope_gate.exclude_landed(self.valid, self.needs_human,
                                       phase=self._scope_phase_word())
        self.scope_gate.gate_work_set(self.valid, self.needs_human)

        print(f"\nFiltered {self.item_noun_plural}:", file=sys.stderr)
        print(f"  Valid (to apply): {len(self.valid)}", file=sys.stderr)
        print(f"  Needs human review: {len(self.needs_human)}", file=sys.stderr)
        print(f"  Skipped: {len(self.skipped)}", file=sys.stderr)
        if self.scope_gate.preserve:
            print(
                f"  Deferred (scope policy preserve): {len(self.scope_gate.deferred)}",
                file=sys.stderr,
            )

        # Show dry-run bulk approval report
        if getattr(self.args, "dry_run", False) and dry_run_report.get(
            "would_auto_approve"
        ):
            print("\n[dry-run] Would auto-approve:", file=sys.stderr)
            for item in dry_run_report["would_auto_approve"][:5]:
                print(
                    f"  - [{item['importance']}] "
                    f"{item.get('theme', 'Group ' + str(item['group_index']))}: "
                    f"{item['reason']}",
                    file=sys.stderr,
                )
            if len(dry_run_report["would_auto_approve"]) > 5:
                print(
                    f"  ... and {len(dry_run_report['would_auto_approve']) - 5} more",
                    file=sys.stderr,
                )

        # Build formatted_skipped for output
        self._rebuild_formatted_skipped()

        # Step 27: handle_no_items_early_exit
        if not self.valid and not self.needs_human:
            if self.scope_gate.deferred or self._scope_open_blockers():
                # Everything eligible is done and the rest is deferred by
                # scope: the phase's eligible work is complete —
                # or, when a batch of this review declined a blocker, the
                # phase stays blocked (exit 3), whatever the subclass's own
                # nothing-left exit would have recorded.
                self._scope_all_deferred_exit()
            self.handle_no_items_early_exit()

        self.logger.info(
            "User feedback applied: %d valid, %d needs_human, %d skipped",
            len(self.valid),
            len(self.needs_human),
            len(self.skipped),
        )

    def _rebuild_formatted_skipped(self) -> None:
        """Re-derive ``formatted_skipped`` from ``self.skipped`` as it stands now.

        Called twice on purpose — once at the end of ``_apply_user_feedback``,
        once after ``_handle_human_decisions`` — because judging *appends* to
        ``self.skipped`` (``apply_verdicts_to_work_set``, ``_skip_unjudged``)
        long after the first build. Built once, the list and the count it is
        published beside disagreed by exactly the judged items: measured
        2026-09-16, `orchestrator_output.json` said `skipped_count: 3` over two
        `skipped_items`, the RESULT block said `Skipped: 2`, and `util decisions`
        listed 19 of 20 groups — the one decision the run actually *made* was the
        one missing from every surface meant to report decisions.
        """
        self.formatted_skipped = []
        for g in self.skipped:
            suggestions = g.get("suggestions", [])
            title = (
                suggestions[0].get("title", g.get("theme", "Unknown"))
                if suggestions
                else g.get("theme", "Unknown")
            )
            importance = get_highest_importance(g)
            status = g.get("validation_status", "unknown")
            reason = g.get("validation_reason", "")
            # A judge-sourced skip is not a validation skip and must not be
            # bucketed with one: it carries its own reason (the judge's, on
            # `reason`) and the `decision_source` that says who decided. The
            # marker is the key `apply_verdicts_to_work_set` stamps on the group.
            decision_source = str(g.get("decision_source") or "")
            guard_skip = g.get("_guard_skip")
            if isinstance(guard_skip, dict):
                # The commit guard's skip: the plugin's, decided before
                # any judge or batch, so neither a validation nor a judge
                # bucket. Its reason and files go everywhere a skip is listed.
                skip_status = guard_skip.get("status") or "commit_guard"
                reason = g.get("reason") or reason
            elif is_judge_source(decision_source):
                skip_status = JUDGE_SKIPPED_STATUS
                reason = g.get("reason") or reason
            elif status == "skipped":
                # A skip with no `decision_source`: `_skip_unjudged`'s groups,
                # which `--yes` skipped because no verdict came back. The skip
                # is the decision, so the reason it recorded — on `reason`, the
                # same key a judge-sourced skip uses — is what every surface
                # must show. `validation_reason` still holds the needs-human
                # text the skip superseded, and showing *that* said the run had
                # asked for a human while reporting it had skipped.
                skip_status = status
                reason = g.get("reason") or reason
            elif status == "invalid":
                skip_status = "invalid"
            elif g.get("_bulk_skipped"):
                skip_status = "bulk_skipped"
            elif status == "valid":
                skip_status = "below_priority"
            else:
                skip_status = status
            entry = {
                # The same key `format_item_for_output` puts on every
                # `to_apply` entry, and for the same reason: without it a
                # skip can only be traced back to its report entry by
                # string-matching the title, which is neither stable nor
                # unique. A skip is the one outcome a reader most needs to
                # look up.
                "group_id": g.get("group_hash", ""),
                "title": title,
                "theme": g.get("theme", ""),
                "importance": importance,
                "status": skip_status,
                "reason": reason,
            }
            # Added only when there is one, so a run with no judged item emits
            # byte-identical output to the one it emitted before this key existed.
            if decision_source:
                entry["decision_source"] = decision_source
            if isinstance(guard_skip, dict):
                entry["files"] = list(guard_skip.get("files") or [])
            self.formatted_skipped.append(entry)

    # ==================================================================
    # The commit apply guard
    # ==================================================================

    def _refuse_unusable_state(self) -> None:
        """Exit 3, before anything is written, when the guard cannot be
        keyed.

        ``StateManager`` replaces a ``state.json`` that does not parse with
        a fresh initial state, so the apply would run with no guard, against
        ``head_at_start`` rather than the reviewed base, and its first save
        would overwrite the file. So, on apply-code-fixes only
        (:attr:`guards_commit_fixes`):

        - a ``state.json`` that exists but does not parse, or holds no JSON
          object, is refused for any plan;
        - a commit brief (``commit_paths.is_commit_brief``) whose state is
          missing or pins no endpoints is refused.

        The file is only read here, never written. The front door's own
        step-6 load may still replace an unparseable state: by then a
        review is recorded afresh, and its apply refuses an unreadable state
        first (``commit_apply.require_completed_review``).
        """
        if not self.guards_commit_fixes:
            return

        plan = Path(self.plan_path)
        state_file = output_dir_path(plan) / "state.json"
        exists = state_file.exists()
        document: Any = None
        problem: Optional[str] = None
        if exists:
            try:
                document = json.loads(state_file.read_text(encoding="utf-8"))
            except (OSError, ValueError) as exc:
                problem = f"it does not parse ({' '.join(str(exc).split())[:160]})"
            else:
                if not isinstance(document, dict):
                    problem = "it does not hold a JSON object"
        try:
            brief = is_commit_brief(plan)
        except Exception:  # noqa: BLE001 - not a brief we can recognise
            brief = False
        if problem is None:
            if not brief or pinned_endpoints(document) is not None:
                return
            problem = ("it records no reviewed commit range" if exists
                       else "it does not exist")
        shown = state_file
        try:
            shown = Path(os.path.relpath(state_file))
        except ValueError:  # pragma: no cover - another drive on Windows
            pass
        if brief:
            match = re.fullmatch(f"({SLUG_PATTERN})", plan.stem)
            pinned = None
            if match:
                base12, head12 = plan.stem.split("-", 1)
                pinned = pinned_spelling(None if base12 == "root" else base12, head12)
            pinned = pinned or str(self.args.plan_file)
            message = (
                f"ERROR: this commit brief's state.json ({shown}) cannot be used: "
                f"{problem}, so the reviewed range and the apply guard cannot be "
                f"read, and apply-code-fixes would apply the fixes unguarded "
                f"against the wrong base. Nothing was written. Restore the file, "
                f"or review the range again: --review-commits {pinned}, then "
                f"--apply-commit-fixes {pinned}."
            )
        else:
            message = (
                f"ERROR: {shown} cannot be used: {problem}. apply-code-fixes "
                f"would start from an empty state and overwrite it. Nothing was "
                f"written. Repair the file, or move it aside to start the phase "
                f"over, then re-run."
            )
        print(message, file=sys.stderr)

        record_error(message)
        raise OrchestratorError(
            f"Phase _setup, step 3a: {state_file} cannot be used: {problem}",
            exit_code=3,
        )

    def _resolve_pinned_endpoints(self) -> None:
        """Resolve the endpoints state pins, strictly, once.

        Keyed on ``commit_range.pinned_endpoints``: ``commit_range`` (a
        commit brief) or ``head_ref`` (a plan after a direct ``--head-ref``
        review). A recorded SHA that no longer names a commit is exit 3
        ``[RANGE_UNRESOLVED]`` naming the recovery, before the guard or any
        batch, so no fix prompt is ever written against ``HEAD~1``. A run
        whose state pins nothing is left exactly as it was.
        """
        if not self.guards_commit_fixes or self.state is None:
            return

        endpoints = pinned_endpoints(self.state.state)
        if endpoints is None:
            return
        root = get_project_root_from_dir(os.path.dirname(self.plan_path)) or os.getcwd()
        label = git_path(self.plan_path, repo_root=root)
        if endpoints.source == "commit_range":
            recovery = (
                "This review can no longer be resumed, reaggregated or applied: "
                "review the commits as they are now with --review-commits <range>, "
                "which resolves to new SHAs and so to a new commit brief."
            )
        else:
            recovery = (
                f"This review can no longer be applied: review the plan again on "
                f"commits that exist with review-code {label} --base-ref <rev> "
                f"--head-ref <rev>."
            )
        try:
            resolved = resolve_recorded(
                pinned_record(self.state.state), cwd=root, label=label, recovery=recovery,
            )
        except RangeError as exc:
            print(exc.message)

            record_error(" ".join(exc.message.split("\n")))
            raise OrchestratorError(
                f"Phase _setup, step 10a: {exc.message.splitlines()[0]}",
                exit_code=exc.exit_code,
            ) from exc
        self._pinned = resolved
        self._pinned_source = endpoints.source
        self._repo_root = root
        typed = getattr(self.args, "base_ref", None)
        if typed and typed != resolved.base_ref:
            print(
                f"NOTE: --base-ref {typed} is not used: this {endpoints.source} pins "
                f"the reviewed range, so the fixes' base is its recorded base "
                f"{resolved.base_ref[:12]}",
                file=sys.stderr,
            )

    def _apply_commit_guard(self) -> None:
        """Take the guard decision over what filtering left, and print
        ``[COMMIT_FIXES]``.

        Every group it skips (the context plan, a fix file changed since the
        reviewed ``head``, a protected path) moves from ``valid`` /
        ``needs_human`` to ``skipped``, before human decisions and batching,
        so the judge never sees it and no batch carries it. The decision is
        saved to the pinned record's ``guard`` through this phase's own
        ``StateManager`` (the one it saves with), under
        ``state_file_lock``. The block is printed once, here, and the result
        line carries ``commit_fixes``. Not on a ``--detach`` launcher, whose
        worker takes the decision (and prints the block into its log); both
        dry runs decide and print but write nothing.
        """
        if self._pinned is None or self.state is None or self._is_detach_invoker():
            return

        dry = bool(getattr(self.args, "dry_run", False)
                   or getattr(self.args, "dry_run_subagents", False))
        phase_dir = os.path.abspath(os.path.join(self.out_dir, self.phase_name))
        resume = bool(getattr(self.args, "resume", False))
        outcome = take_guard(
            self.state.state,
            list(self.valid) + list(self.needs_human),
            cwd=self._repo_root or os.getcwd(),
            plan_path=self.plan_path,
            out_dir=self.out_dir,
            phase_dir=phase_dir,
            resume=resume,
            persist=not dry,
            completed=self._finished_group_ids() if resume else (),
        )
        if outcome is None:
            return
        if not dry:
            record = pinned_record(self.state.state)
            if record is not None:
                record["guard"] = outcome.guard

                with metrics.state_file_lock(self.state.state_file):
                    self.state.save()

        head = str(outcome.guard.get("head") or "")
        context_plan = outcome.guard.get("context_plan")
        if outcome.skipped:
            for work in (self.valid, self.needs_human):
                kept = []
                for group in work:
                    entry = outcome.skipped.get(group_id_of(group))
                    if entry is None:
                        kept.append(group)
                        continue
                    reason = skip_reason(str(entry.get("reason")), head=head,
                                         context_plan=context_plan)
                    group["_guard_skip"] = {
                        "status": GUARD_SKIP_STATUS,
                        "reason": entry.get("reason"),
                        "files": list(entry.get("files") or []),
                    }
                    group["reason"] = reason
                    self.skipped.append(group)
                    print(
                        f"[commit guard] skipped {group_id_of(group)} "
                        f"({reason}: {', '.join(entry.get('files') or [])})",
                        file=sys.stderr,
                    )
                work[:] = kept
        for line in outcome.lines:
            print(line)
        record_commit_fixes_result(outcome.payload)

    def _finished_group_ids(self) -> Set[str]:
        """The groups whose batch an earlier run of this phase finished, for
        the apply guard's re-check on a ``--resume`` (``take_guard``'s
        *completed*).

        Every ``processed_<phase>`` record that keeps its item out of a
        native resume (:func:`processed_record_counts`), the executor's own
        records included: step 23 drops those items on the native leg, while
        the executor leg keeps them in the work set so the scheduler can keep
        their batch from its result file. The guard must then leave their
        batch as it landed.
        """
        if self.state is None:
            return set()

        review_stamp = file_content_hash(
            os.path.join(self.out_dir, self.review_subdir, "grouped.json"))
        return {
            str(key)
            for key, record in self.state.get_processed_items(self.phase_name).items()
            if processed_record_counts(record, review_stamp=review_stamp)
        }

    # ==================================================================
    # The scope policy
    # ==================================================================

    @property
    def scope_gate(self) -> "_scope.ApplyScopeGate":
        """This run's scope-policy state (``scope_apply.ApplyScopeGate``).

        ``__init__`` makes it; an instance built without ``__init__`` (a
        test's ``object.__new__``) gets its own on first use, which reads
        ``expand``.
        """
        gate = self.__dict__.get("_scope_gate")
        if gate is None:
            gate = self.__dict__["_scope_gate"] = _scope.ApplyScopeGate()
        return gate

    def _scope_phase_word(self) -> str:
        """The phase word the round record and completion are keyed by."""
        return self.confirmation_phase_name or self.phase_name

    def _scope_dry(self) -> bool:
        """Both dry runs stay read-only (``write_target_backup``'s rule)."""
        return bool(getattr(self.args, "dry_run", False)
                    or getattr(self.args, "dry_run_subagents", False))

    def _resolve_scope_policy(self) -> None:
        """Step 10b: the effective apply policy.

        Explicit ``--scope-policy`` → the round's recorded apply override →
        the round's review policy → ``expand`` (``scope_apply.
        resolve_apply_policy``). An invalid value is exit 3. An explicit
        choice is recorded at step 10c (:meth:`_record_explicit_scope_policy`),
        once the policy-change refusal has had its say.
        """
        explicit = getattr(self.args, _sp.DEST, None)
        problem = _scope.invalid_policy_message(explicit)
        if problem:
            print(f"ERROR: {problem}", file=sys.stderr)
            record_error(problem)
            raise OrchestratorError(f"Phase _setup, step 10b: {problem}", exit_code=3)
        word = self._scope_phase_word()
        state = self.state.state if self.state is not None else {}
        scope = self.scope_gate.policy = _scope.resolve_apply_policy(explicit, state, word)
        if scope.source != _sp.SOURCE_EXPLICIT:
            # D6 row 16: a policy nobody typed is recorded under `--yes` only
            # (`_record_resolution` returns early otherwise).
            self._record_resolution(
                _scope_policy_runs.SITE_ID,
                _scope_policy_runs.resolution_text(scope.policy, scope.source),
            )
        if scope.preserve or scope.source in (
                _sp.SOURCE_EXPLICIT, _sp.SOURCE_CONTINUATION):
            baseline = f", baseline {scope.baseline_id}" if scope.baseline_id else ""
            print(
                f"[scope-policy] {word}: {scope.policy} "
                f"(source: {scope.source}; review requested "
                f"{scope.review_policy}{baseline})",
                file=sys.stderr,
            )

    def _record_explicit_scope_policy(self) -> None:
        """Step 10c: record an explicit choice on the round.

        ``scope_policy.record_apply_policy``, so the choice survives a later
        run that omits it. Dry runs record nothing, and neither does a run
        :meth:`_scope_detect_change` refused (it raised before this).
        """
        scope = self.scope_gate.policy
        if (scope is None or scope.source != _sp.SOURCE_EXPLICIT
                or self.state is None or self._scope_dry()):
            return
        _sp.record_scope_apply_policy(self.state, self._scope_phase_word(),
                                      scope.policy, _sp.SOURCE_EXPLICIT)
        self.state.save()

    def _scope_detect_change(self) -> None:
        """Step 10c: this review's earlier materialization under another policy.

        Read-only. A batch of that run that did not finish is exit 3 here,
        before anything is recorded or built (rebuilding the batches could
        apply its half-applied items again). Otherwise the change is kept on
        the gate for ``exclude_landed`` (before the gate) and
        ``apply_policy_change`` (before batching).
        """
        gate = self.scope_gate
        gate.change = None
        if gate.policy is None or not self.write_kind or self.state is None:
            return

        phase_dir = os.path.join(self.out_dir, self.phase_name)
        change = _scope.detect_policy_change(
            phase_dir, current_policy=gate.policy.policy,
            review_stamp=file_content_hash(
                os.path.join(self.out_dir, self.review_subdir, "grouped.json")),
            processed=self.state.get_processed_items(self.phase_name),
        )
        if change is None:
            return
        if change.unsettled:
            lines = _scope.unsettled_refusal(change, mode_word=self._scope_phase_word())
            for line in lines:
                print(line, file=sys.stderr)
            record_error(lines[0])
            raise OrchestratorError(
                "Phase _setup, step 10c: a scope-policy change over an unfinished batch",
                exit_code=3,
            )
        gate.change = change

    def _scope_confirmation_message(self, message: str) -> str:
        """Step 19's text, naming the deferred set under ``preserve`` only."""
        if not self.scope_gate.preserve:
            return message
        return self.scope_gate.confirmation_message(
            message, merge_validation_with_groups(self.groups, self.validation or []))

    def scope_annotate(self, formatted: Dict[str, Any], group: Dict[str, Any], *,
                       original_description: Optional[str] = None) -> Dict[str, Any]:
        """A formatter's last step: the ``preserve`` scope context.

        Under ``preserve`` a bound selected remedy becomes the item's
        instruction (``scope_apply.annotate_item``); under ``expand`` the
        formatted item is returned untouched.
        """
        return self.scope_gate.annotate(formatted, group,
                                        original_description=original_description)

    def _scope_effective(self, state: StateManager) -> "_scope.ApplyPolicy":
        """This run's policy, or (``--mark-completed``, which resolves none)
        the one the round's record gives."""
        return self.scope_gate.effective(
            state.state, getattr(self.args, _sp.DEST, None), self._scope_phase_word())

    def _scope_blockers(self, state: Optional[StateManager]) -> List[Dict[str, Any]]:
        """The blockers this review's batches declined, from the phase's records.

        Under ``preserve`` a declined item whose reason starts with
        ``scope_apply.BLOCKER_PREFIX`` is the concrete blocker names.
        Read from ``processed_<phase>`` (both legs record declines there), so
        every completion writer derives the same answer — a ``--resume`` that
        drops the declined item still finds it. ``[]`` under ``expand``.
        """
        if state is None or not self._scope_effective(state).preserve:
            return []

        out_dir = self.out_dir or find_output_dir(
            self.plan_path, guard_double_nesting=self.guard_double_nesting)
        stamp = file_content_hash(
            os.path.join(out_dir, self.review_subdir, "grouped.json"))
        return _scope.blockers_from_processed(
            state.get_processed_items(self.phase_name), stamp)

    def _scope_open_blockers(self) -> List[Dict[str, Any]]:
        """Step 27's question: does this review's record hold a blocker?

        Read-only, and ``[]`` under a dry run (which records nothing and
        keeps its own exit) and under ``expand``.
        """
        if self._scope_dry():
            return []
        return self._scope_blockers(self.state)

    def _scope_close(self, state: Optional[StateManager]) -> List[Dict[str, Any]]:
        """The round's completion outcome; the blockers it found.

        Every completion writer calls this — ``--mark-completed``, the
        executor leg's finished loop, the emit-time empty loop and the
        all-deferred exit — so each derives the blockers the same way
        (:meth:`_scope_blockers`): recorded with the completion
        (``blocked``), which dependent phases read, and returned so the
        caller stops at exit 3. Only a completion that finds none clears
        them (an ``expand`` apply, a re-run whose batch applies the item) —
        or a fresh review round, which replaces the record.
        """
        if state is None:
            return []
        blockers = self._scope_blockers(state)
        _scope.record_scope_completion(
            state, self._scope_phase_word(), self._scope_effective(state), blockers)
        return blockers

    def _scope_report_blockers(self, blockers: Sequence[Dict[str, Any]]) -> None:
        word = self._scope_phase_word()
        for line in _scope.blocker_lines(blockers, mode_word=word):
            print(line, file=sys.stderr)
        record_error(_scope.blocker_error(blockers, mode_word=word))

    def _print_scope_summary(self) -> None:
        """The native leg's deferral lines, beside its plan of work."""
        lines = self.scope_gate.summary_lines()
        if not lines:
            return
        stream = sys.stderr if getattr(self.args, "output_format", "text") == "json" else sys.stdout
        for line in lines:
            print(line, file=stream)

    def _publish_scope_notice(self) -> None:
        note = self.scope_gate.notice(self.item_noun_plural)
        if note:
            add_notice(note)

    def _scope_all_deferred_exit(self) -> None:
        """Every remaining item is deferred: eligible work completed.

        Replaces the subclass's no-items exit for this case, and for the one
        where nothing remains but a batch of this review declined a blocker,
        so the phase is recorded *completed* with its deferrals kept (never
        "no actionable findings", never a skip), on both legs, before the
        detach boundary like that exit. A recorded blocker keeps the phase
        blocked and stops at exit 3 (a ``--resume`` over a blocked phase
        must not clear it). Dry runs record nothing.
        """
        word = self._scope_phase_word()
        blockers: List[Dict[str, Any]] = []
        if not self._scope_dry() and self.state is not None:
            _scope.record_scope_deferrals(self.state, word, self.scope_gate.deferred)
            self.state.mark_phase_completed(word)
            blockers = self._scope_close(self.state)
            if self.edits_the_plan and getattr(self.args, "resume", False):
                self.state.refresh_plan_hash()
            self.state.save()
            if self.resume_dropped_groups:
                self.print_native_tests_not_run()
        phase_dir = os.path.join(self.out_dir, self.phase_name)
        os.makedirs(phase_dir, exist_ok=True)
        count = len(self.scope_gate.deferred)
        output: Dict[str, Any] = {
            "format_version": CURRENT_FORMAT_VERSION,
            "status": "completed",
            "message": (
                _scope.blocker_error(blockers, mode_word=word) if blockers else
                f"Eligible work completed: no {self.item_noun} is eligible under "
                f"{_sp.FLAG} preserve and {count} "
                f"{self.item_noun if count == 1 else self.item_noun_plural} "
                f"stay deferred"
            ),
            "phase": word,
            "plan_file": self.plan_path,
            "prefix": self.prefix,
            "output_dir": self.out_dir,
            "timestamp": datetime.now().isoformat(),
            "batches": [],
            "to_apply": [],
            "needs_human_review": [],
            "skipped_items": self.formatted_skipped,
            "user_skipped_items": self.user_skipped_items,
            "skipped_count": len(self.skipped),
            "summary": {
                "total_groups": len(self.groups),
                "valid_count": 0,
                "needs_human_count": 0,
                "skipped_count": len(self.skipped),
                "user_skipped_count": len(self.user_skipped_items),
                "batch_count": 0,
                "scope_deferred_count": count,
            },
        }
        output.update(self.scope_gate.output_fields())
        if not blockers:
            print(f"\nNo {self.item_noun_plural} eligible under {_sp.FLAG} preserve.",
                  file=sys.stderr)
        for line in self.scope_gate.summary_lines():
            print(line, file=sys.stderr)
        self._publish_scope_notice()
        write_and_emit_output(output, phase_dir)
        self.emit_payload(output)
        if blockers:
            self._scope_report_blockers(blockers)
            sys.exit(3)
        sys.exit(0)

    # ==================================================================
    # Phase 4 — _prepare_batches
    # ==================================================================

    # ==================================================================
    # Phase 3b — human-decision judging (D2a/D2b)
    # ==================================================================

    def human_decision_scope(self) -> List[Dict[str, Any]]:
        """Return the needs-human-decision groups a judge should decide.

        ``--agent-decide`` puts every needs-human item in scope; otherwise only
        the ones the reviewer pre-marked "Let the agent decide" in the report (the
        per-item routing marker). The judge prompt is one deterministic function
        of that set, so an unattended run and an interactive one that picked "Let
        the agent decide" produce the same prompt for the same items.
        """
        if getattr(self.args, "agent_decide", False):
            return list(self.needs_human)
        return [g for g in self.needs_human if g.get(JUDGE_DECIDE)]

    def human_decision_phase_dir(self) -> str:
        """The phase dir judging tasks and verdict files live in."""
        return os.path.dirname(self.get_output_path())

    def _handle_human_decisions(self) -> None:
        """Phase 3b: ingest judge verdicts, then materialize any still needed.

        Additive by construction, in both directions:

        * When the invoker has already persisted ``human_decision_batch_<n>.json``
          files, they are validated, mapped by stable ``group_id``, recorded
          through ``record_human_decision`` with today's exact translation, and
          the work set is rebuilt from those decisions — so ``--resume`` sees
          exactly the state an interactive pass would have produced.
        * Any in-scope item still without a verdict gets a materialized
          ``human_decision_judge`` task written to ``human_decision_tasks.json``.
          Nothing exits early and no existing output changes shape, so an
          orchestrator stays directly invocable with identical flags and exit
          codes.

        A group with no verdict stays ``needs-human-decision``: never silently
        approved, never silently dropped. Under ``--yes`` those groups are
        skipped with a warning by the caller's normal unattended handling;
        interactively they fall back to the normal ask.
        """
        scope = self.human_decision_scope()
        phase_dir = self.human_decision_phase_dir()
        expected_ids = [group_id_of(g) for g in scope]

        ingest, remaining = self._ingest_judge_verdicts(scope, phase_dir, expected_ids)
        if not remaining:
            return

        # Judging ran but did not cover everything, and this is an unattended
        # run: skip the leftovers with a warning rather than stalling. When
        # judging has not run at all (no verdict file yet) there is nothing to
        # be unattended about — the tasks are materialized below and the invoker
        # runs them. Interactively, leftovers fall back to the normal ask by
        # staying in needs_human.
        if ingest.verdicts and getattr(self.args, "yes", False):
            self._skip_unjudged(remaining)
            return

        items = [judge_item_from_group(g) for g in remaining]
        # Same "does this phase have a tasks file distinct from the plan?"
        # question `run_write_executor` asks via `write_phase_artifact()` (D3h) —
        # apply-task-suggestions judges decisions about tasks.md, not the plan,
        # so its judging tasks need `inputs.tasks_sha256` too (F8).
        artifact = self.write_phase_artifact()
        tasks_file = artifact if artifact != self.plan_path else None
        # On a pinned run the judge rules on findings built from commits and
        # files read at `head`, all of it data under review: its task says so. Absent
        # otherwise, so a plan's run keeps
        # its prompt byte for byte.
        trust_note: Optional[str] = None
        if self._pinned is not None:
            trust_note = DATA_UNDER_REVIEW
        try:
            document = build_judge_tasks(
                items=items,
                phase_dir=phase_dir,
                plan_file=str(self.plan_path),
                tasks_file=tasks_file,
                **({"trust_note": trust_note} if trust_note else {}),
            )
            tasks_path = write_judge_tasks(document, phase_dir)
        except Exception as exc:  # noqa: BLE001 - must not fail the apply run
            self.logger.warning("Could not materialize judging tasks: %s", exc)
            return

        print(f"\n[HUMAN_DECISION_JUDGING_PENDING] {tasks_path}")
        print(f"Items to judge: {len(items)}")

        # D3b/D2b: with --exec-subagents the judges run here and their verdict
        # FILES are ingested in the same invocation, so the decisions reach
        # ``record_human_decision`` and the apply batch without a verdict ever
        # travelling through chat context.
        if not review_orchestrator_base.dispatch_subagent_tasks(
            self.args,
            task_file=tasks_path,
            phase_dir=phase_dir,
            phase=self.phase_name,
            document=document,
            plan_path=str(self.plan_path),
            label="human-decision judging",
        ):
            return

        ingest, remaining = self._ingest_judge_verdicts(
            scope, phase_dir, expected_ids,
            dispatched_ids=[group_id_of(g) for g in remaining],
        )
        if remaining and getattr(self.args, "yes", False):
            self._skip_unjudged(remaining)

    def _host_id(self) -> Optional[str]:
        """The declared host (``--host``, else ``$MULTI_LLM_HOST``), never guessed."""
        return getattr(self.args, "host", None) or os.environ.get("MULTI_LLM_HOST") or None

    def _skip_unjudged(self, remaining: List[Dict[str, Any]]) -> None:
        """Move judged-but-unresolved groups to skipped under ``--yes``."""
        for group in remaining:
            print(
                "Warning: no judge verdict for group "
                f"{group_id_of(group)}; skipping it (--yes).",
                file=sys.stderr,
            )
            group["validation_status"] = "skipped"
            group["reason"] = "No judge decision returned for this group"
            self.skipped.append(group)
        leftover = {id(g) for g in remaining}
        self.needs_human[:] = [
            g for g in self.needs_human if id(g) not in leftover
        ]

    def _ingest_judge_verdicts(
        self,
        scope: List[Dict[str, Any]],
        phase_dir: str,
        expected_ids: List[str],
        dispatched_ids: Sequence[str] = (),
    ) -> Tuple[Any, List[Dict[str, Any]]]:
        """Read, record and apply every verdict file present. Returns the leftovers.

        Extracted so both judging legs run the *same* ingest: the native path
        reaches it once (the driving agent persisted the files before re-invoking)
        and the executor path reaches it twice — before dispatching, and again
        after — which is what closes the loop in one invocation.

        *dispatched_ids* is the set of groups this invocation's executor just
        judged; it is empty on the pre-dispatch pass. Only those groups may fall
        back to ``executor (runner unrecorded)`` when the executor's provenance
        does not cover their file.
        """
        ingest = ingest_verdicts(phase_dir=phase_dir, expected_group_ids=expected_ids)
        for message in ingest.errors:
            print(f"ERROR: human-decision verdict rejected: {message}", file=sys.stderr)
        if ingest.unexpected:
            print(
                "Warning: ignoring verdicts for groups that are not in scope: "
                f"{sorted(set(ingest.unexpected))}",
                file=sys.stderr,
            )

        if ingest.verdicts and not ingest.conflicts:
            items_by_group = {
                group_id_of(g): judge_item_from_group(g) for g in scope
            }
            if (getattr(self.args, "exec_subagents", False)
                    or getattr(self.args, "detach", False)):
                # A verdict file already on disk before this invocation
                # dispatched (a `--resume`, a Codex retry) may have been written
                # by a native host agent, so without matching provenance neither
                # the runner nor "executor" is known: it is just unrecorded. Only
                # the groups this invocation dispatched are an executor's work.
                dispatched = set(dispatched_ids)
                fallback_judge = "unrecorded"
                judges = judge_labels(
                    phase_dir,
                    {gid: path for gid, path in ingest.sources.items()
                     if gid not in dispatched},
                    fallback=fallback_judge,
                    ingest=ingest,
                )
                judges.update(judge_labels(
                    phase_dir,
                    {gid: path for gid, path in ingest.sources.items()
                     if gid in dispatched},
                    fallback="executor (runner unrecorded)",
                    ingest=ingest,
                ))
            else:
                fallback_judge = native_judge_label(self._host_id())
                judges = judge_labels(
                    phase_dir, ingest.sources, fallback=fallback_judge,
                    ingest=ingest,
                )
            if self.state is not None:
                record_verdicts(
                    state=self.state,
                    phase=self.phase_name,
                    ingest=ingest,
                    items_by_group=items_by_group,
                    judges=judges,
                    default_judge=fallback_judge,
                )
                self.state.save()
            counts = apply_verdicts_to_work_set(
                verdicts=ingest.verdicts,
                needs_human=self.needs_human,
                valid=self.valid,
                skipped=self.skipped,
                judges=judges,
                default_judge=fallback_judge,
            )
            print(
                f"Ingested judge decisions ({', '.join(sorted(set(judges.values())))}): "
                f"{counts['approved']} approved, {counts['salvaged']} salvaged, "
                f"{counts['skipped']} skipped, {counts['unresolved']} still "
                "needing a decision",
                file=sys.stderr,
            )

        remaining = [
            g for g in self.needs_human
            if group_id_of(g) in set(expected_ids)
        ]
        return ingest, remaining

    # ==================================================================
    # Phase 4 — _prepare_batches
    # ==================================================================

    def _prepare_batches(self) -> None:
        """Phase 4: Formatting, batching, and prompt generation.

        Steps 28-31 from the lifecycle spec.
        """
        self.logger.debug("Entering _prepare_batches phase")

        # Step 28: Format items for output
        try:
            self.formatted_valid = [
                self.format_item_for_output(g, i)
                for i, g in enumerate(self.valid)
            ]
            self.formatted_human = [
                self.format_item_for_output(g, i)
                for i, g in enumerate(self.needs_human)
            ]
        except Exception as e:
            raise OrchestratorError(
                f"Phase _prepare_batches, step 28: format_item_for_output failed: {e}",
                exit_code=1,
            ) from e

        # Step 29: Create batches
        try:
            self.batches = self.create_batches(self.formatted_valid)
        except Exception as e:
            raise OrchestratorError(
                f"Phase _prepare_batches, step 29: create_batches failed: {e}",
                exit_code=1,
            ) from e

        self.logger.info("Created %d batches", len(self.batches))

        # Step 30: Handle --dry-run
        if getattr(self.args, "dry_run", False):
            self._handle_dry_run()
            sys.exit(0)

        # Step 31: Generate prompts
        try:
            self.batches = self.generate_batch_prompts(self.batches)
        except Exception as e:
            raise OrchestratorError(
                f"Phase _prepare_batches, step 31: generate_batch_prompts failed: {e}",
                exit_code=1,
            ) from e

        self.logger.info("Batch preparation complete")

    # ==================================================================
    # Phase 5 — _write_outputs
    # ==================================================================

    def _write_outputs(self) -> int:
        """Phase 5: Output assembly and completion.

        Steps 32-35 from the lifecycle spec.

        Returns:
            Exit code (0 on success).
        """
        self.logger.debug("Entering _write_outputs phase")

        # Before any batch is published: the verdicts' round is still on record.
        self._recheck_verdicts_round("Phase _write_outputs, step 32")

        # Build resume_info
        resume_info: Optional[Dict[str, Any]] = None
        if self.state is not None:
            resume_info = {
                "previously_processed": list(
                    self.state.get_processed_items(self.phase_name).keys()
                ),
                "previous_decisions": self.state.get_all_human_decisions(
                    self.phase_name
                ),
                "can_resume": (
                    len(self.state.get_processed_items(self.phase_name)) > 0
                    or len(self.state.get_all_human_decisions(self.phase_name)) > 0
                ),
            }

        # Post-hoc audit: verify every report-pre-marked "Let the agent decide"
        # item actually reached the judge (decision_source == judge_*), rather
        # than being prompted interactively or dropped. This is the runtime
        # backstop for the per-item routing the apply instructions perform; it
        # surfaces warnings but never fails the run (a sibling of the
        # batch-mode-compliance audit). Recorded decisions only exist once at
        # least one batch has been processed (e.g. on --resume), so this is a
        # no-op on the initial pass when nothing has been recorded yet.
        if self.state is not None:
            recorded_decisions = self.state.get_all_human_decisions(
                self.phase_name
            )
            cd_ok, cd_warnings = validate_judge_decide_items_honored(
                self.build_human_review_config(),
                recorded_decisions,
            )
            if not cd_ok:
                for warning in cd_warnings:
                    self.logger.warning(warning)

        # Step 32: Build output JSON
        try:
            output = self.build_output_json(
                self.batches,
                resume_info=resume_info,
            )
        except Exception as e:
            raise OrchestratorError(
                f"Phase _write_outputs, step 32: build_output_json failed: {e}",
                exit_code=1,
            ) from e
        # The scope policy's block: present only under `preserve`
        # or when an `expand` override released earlier deferrals, so a
        # default run's payload keeps exactly its keys.
        output.update(self.scope_gate.output_fields())

        # Step 33: Write output + mark phase completed
        try:
            output_path = self.get_output_path()
        except Exception as e:
            raise OrchestratorError(
                f"Phase _write_outputs, step 33: get_output_path failed: {e}",
                exit_code=1,
            ) from e

        output_dir = os.path.dirname(output_path)
        os.makedirs(output_dir, exist_ok=True)
        # The host's views of the output this one replaces go first; the native
        # leg publishes this output's once `write_tasks.json` names its task
        # ids (docs/development/write-scheduler.md#the-host-summary).
        invalidate_orchestrator_views(output_path)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2)
        print(f"[OUTPUT_FILE] {output_path}", file=sys.stderr)

        # Step 33a: the detach boundary (D4) is NOT here. It is crossed in run(),
        # before _handle_human_decisions(), because that step starts children too
        # (the judge subagents under `--exec-subagents`) and D4 puts the boundary
        # before the *first* child, not before the last one. By the time control
        # reaches this line the process is either the ordinary foreground run or
        # the detached worker that already owns the phase dir.

        # Step 33aa: the target file is about to be rewritten — by the scheduler
        # below, or by the host following the JSON just written — so snapshot it
        # first, on both legs.
        self.write_target_backup()

        # Step 33b: the write executor (D3n). Strictly additive — with neither
        # `--exec-subagents` nor `--dry-run-subagents` this returns None and the
        # rest of this method is byte-for-byte the native path. When it DOES run it
        # owns phase completion too: the base's `mark_phase_completed` below is
        # skipped, because a stopped batch loop must leave the phase incomplete.
        scheduled = self.run_write_executor()
        if scheduled is not None:
            dispatched = not getattr(self.args, "dry_run_subagents", False)
            if dispatched:
                # The instructions' *Generate Summary Report* step, run here
                # because this leg never returns to the host to run it: the
                # report plus the decisions overlay on the review HTML. Written
                # *before* the artifact record, so the report is one of the
                # files handed back.
                try:
                    report = self.phase_report()
                    summary_path = report.write_apply_summary_report()
                    self._decisions_overlay_path = report.regenerate_decisions_overlay()
                    if summary_path:
                        # F11: the scheduler already serialized
                        # write_batch_report.json with summary_file: null by
                        # this point — patch it now that the path is known.
                        report.patch_write_batch_report_summary_file(summary_path)
                except Exception as e:  # noqa: BLE001 - reporting is non-fatal
                    self.logger.warning("summary report failed: %s", e)
            self.phase_report().record_write_artifacts(output_path)
            try:
                # `print_text_summary` is a *plan of work* — "SUGGESTIONS TO
                # APPLY", every batch, every description — and on this leg it ran
                # after `run_write_executor()` had already applied them, i.e. it
                # described finished work in the future tense and named no
                # outcome at all. So the outcome takes its place here, and the
                # plan of work keeps the two legs where it is still a plan: the
                # native path below, and `--dry-run-subagents`, which dispatches
                # nothing. Under `--output-format json` the machine payload is
                # emitted regardless, because that flag is a contract.
                as_json = self.json_output()
                if not dispatched or as_json:
                    self.emit_summary(self.batches, output_path)
                if dispatched:
                    # On stderr when the payload above claimed stdout: a
                    # contract with a human-readable block printed after it is
                    # not a contract, and a consumer that parses stdout as JSON
                    # gets the outcome block in its teeth. It is still printed —
                    # to the stream the scheduler's own progress lines already
                    # use, which is the same log either way under `--detach`.
                    report = self.phase_report()
                    with contextlib.redirect_stdout(
                        sys.stderr if as_json else sys.stdout
                    ):
                        report.print_write_outcome_summary()
                    report.publish_run_notes()
            except Exception as e:  # noqa: BLE001 - summary is non-fatal
                self.logger.warning("write outcome summary failed: %s", e)
            return scheduled

        # The native leg: the same materialized task file the
        # executor leg writes, so the host's per-batch `util write-prompt`
        # binds each batch's prior-changes context late, from the same seam,
        # and the host loops over task ids instead of guessing the JSON shape.
        # Reported on stderr like `[OUTPUT_FILE]` — stdout stays the contract.
        try:
            task_file = self._materialize_native_write_tasks()
        except Exception as exc:  # noqa: BLE001 - the batch document is still usable
            self.logger.warning("write task file not materialized: %s", exc)
            print(f"WARNING: write_tasks.json not written: {exc}", file=sys.stderr)
        else:
            if task_file:
                print(f"[WRITE_TASKS_FILE] {task_file}", file=sys.stderr)
                # A native `--resume` promises to skip what already landed.
                # A batch about to go out again whose `prior_changes_id` the
                # log already holds for this phase, with no record
                # (`util batch-done`) saying it finished, is one the host
                # applied without recording: re-emitting it would apply it
                # twice, so the resume stops here (exit 3) naming the batch
                # and the record command (reviewer repro, 2026-10-05).
                self._refuse_unrecorded_native_resume()
            # The summary and batch details, from the output and the task ids
            # just written; none when a batch has no task to pair with.
            publish_orchestrator_views(
                output, output_path,
                getattr(self, "_native_write_tasks", None) if task_file else None,
            )

        # The native leg: the batches are now the host's to apply, so the phase
        # is recorded *started*, never completed — completion is the host's
        # post-loop `--mark-completed`, the only place the native path records
        # it (the word it persists is the same `confirmation_phase_name or
        # phase_name`). Until 2026-10-05 apply-suggestions marked itself
        # completed right here, before a single edit existed, so `status`
        # and the next-step builder read a phase as done while the host was
        # still applying its batches — or after it had died halfway.
        scope_blockers: List[Dict[str, Any]] = []
        if self.state is not None:
            word = self.confirmation_phase_name or self.phase_name
            if not self.batches and not self.needs_human:
                # Nothing handed out and nothing left to decide (every item
                # invalid or skipped): the phase's work is done at emit, so
                # the record says so — a started record here would wait for
                # a closing step over an empty loop. The scope record is the
                # same completion `--mark-completed` writes: a blocker a
                # batch of this review declined (and `--resume` dropped)
                # keeps the phase blocked, exit 3 below.
                self.state.mark_phase_completed(word)
                scope_blockers = self._scope_close(self.state)
                # Under `--resume` the empty loop is what step 23 left after
                # dropping every group an earlier native run applied: that
                # host edited the plan and died before its `--mark-completed`,
                # so the drift on disk is the plugin's own, and this record
                # stands in for that call's re-stamp. Without it the next
                # `StateManager` reads the edit as a human's and `implement
                # --resume` reports "Plan has changed since last session"
                # (Fable review 2026-10-09). A run with no `--resume` applied
                # nothing, so any drift there stays the human's to report.
                if self.edits_the_plan and getattr(self.args, "resume", False):
                    self.state.refresh_plan_hash()
            else:
                self.state.mark_phase_started(word)
            self.state.save()

        # Step 34: Print summary
        try:
            self.emit_summary(self.batches, output_path)
        except Exception as e:
            # Non-fatal: log but don't fail
            self.logger.warning(
                "print_text_summary failed: %s", e, exc_info=True
            )
        self._print_scope_summary()
        self._publish_scope_notice()

        self.logger.info("Output written to %s", output_path)

        if scope_blockers:
            self._scope_report_blockers(scope_blockers)
            return 3

        # Step 35: Return exit code 0
        return 0

    # ==================================================================
    # The write executor (D3f/D3g/D3h/D3l/D3n)
    # ==================================================================

    def _is_detach_invoker(self) -> bool:
        """True on the leg that will fork a worker and return the handshake.

        The three conditions :meth:`maybe_detach_write_phase` forks under, asked
        as one question so a step *before* the boundary can tell which leg it is
        on. ``--dry-run`` is one of them: a dry run prints its report and exits
        before any child exists, so the invoker has nothing to daemonize and
        stays in the foreground (the worker leg is untouched — it must still
        claim the phase dir).
        """
        return (
            getattr(self.args, "detach", False)
            and not getattr(self.args, "internal_worker", False)
            and not getattr(self.args, "dry_run", False)
        )

    def maybe_detach_write_phase(self) -> Optional[int]:
        """The one detach boundary a write phase crosses (D4), or ``None``.

        Returns ``None`` to keep running in this process — the ordinary foreground
        run, and also the detached worker once it owns the phase dir — or an exit
        code the caller must return immediately (the invoker, after forking).

        Delegates to the *same* ``review_orchestrator_base.maybe_detach`` the
        fan-out modes use: one spawn implementation, one handshake, one
        ``.status.json`` claim, so a write run is observable through exactly the
        same ``status`` command.

        Called from :meth:`run` *before* ``_handle_human_decisions`` — the first
        step that can start a child — and therefore before batching and output
        assembly, which the worker does.
        """
        # The invoker's three conditions (`_is_detach_invoker`, which the D6
        # sites above the boundary ask too), or the worker leg — which forks
        # nothing and only has to claim the phase dir.
        if not (self._is_detach_invoker()
                or getattr(self.args, "internal_worker", False)):
            # The foreground run replaces a damaged checkpoint, never a dry run
            # (utils/detach.py, `settle_foreground_checkpoint`).
            if not getattr(self.args, "dry_run", False):
                _detach.settle_foreground_checkpoint(
                    os.path.join(self.out_dir, self.phase_name), phase=self.phase_name)
            return None

        phase_dir = os.path.join(self.out_dir, self.phase_name)
        os.makedirs(phase_dir, exist_ok=True)
        mode = self.confirmation_phase_name or self.phase_name
        return review_orchestrator_base.maybe_detach(
            args=self.args,
            mode=mode,
            phase_dir=phase_dir,
            plan_file=self.plan_path,
            phase=self.phase_name,
        )

    def write_phase_artifact(self) -> str:
        """The shared artifact this phase's batches edit (D3h).

        apply-suggestions and apply-task-suggestions each edit exactly ONE file, so
        that file is what gets snapshotted, what the byte comparison decides on, and
        why those phases are pinned to one concurrent write regardless of the driver
        config. apply-code-fixes overrides this to nothing: its batches are
        partitioned by ``file_key``, so the declared set is per-batch.
        """
        return self.plan_path

    def write_target_file(self) -> Optional[str]:
        """The single file this phase overwrites, or ``None`` when there is none.

        The backup and the "here is the file I edited" artifact both need a *one
        file* answer, which ``write_phase_artifact`` gives for the two suggestion
        phases and deliberately does not give for apply-code-fixes (its declared
        set is per batch). ``has_single_write_target`` is the switch.
        """
        if not self.has_single_write_target:
            return None
        return self.write_phase_artifact() or None

    def _review_completed_at(self) -> Optional[datetime]:
        """When the review this phase applies last completed, or ``None``.

        The cutoff between review cycles that every check over this phase's
        own records dates against, read as the scheduler reads it
        (``write_batch_scheduler.review_completed_at``). ``None`` for a phase
        with no write kind, before ``_setup`` built the state, or when the
        review has no parseable completion — and every caller then keeps
        what it was dating (absence of a date is not staleness).
        """
        return review_completed_at(
            getattr(getattr(self, "state", None), "state", None),
            getattr(self, "write_kind", ""),
        )

    def _refuse_another_rounds_verdicts(self) -> None:
        """Step 9a: apply only the verdicts of the review round on record.

        A review re-run stamps a new round id in the review's ``.status.json``
        before it replaces the previous round's files (``utils/review_round``).
        One that is still running, or stopped before it validated (every
        model failed, or it was interrupted), leaves the previous round's
        ``validation.json`` in place while the review phase is pending, and
        applying it would apply a review the phase has since replaced. So a
        ``validation.json`` that records another round than the checkpoint's
        is refused at exit 3, before anything is written, as
        ``--reaggregate`` refuses it; one of the round on record goes ahead.
        A file or a checkpoint with no round id (written before round ids, or
        unreadable) proves nothing and is applied as before
        (docs/development/review-results.md, "Round identity").

        The file is read once, here: ``load_data`` parses these bytes
        (:meth:`held_verdicts`), never a later read, and the round they
        record is kept (:attr:`_verdicts_round`) for the re-checks before
        work is published (:meth:`_recheck_verdicts_round`) and for the
        native emit's batches, which ``util write-prompt`` refuses once the
        review has started another round.
        """
        self._held_verdicts = None
        self._verdicts_round = None
        review_dir = os.path.join(self.out_dir, self.review_subdir)
        path = os.path.abspath(os.path.join(review_dir, _review_round.VALIDATION_NAME))
        try:
            data = Path(path).read_bytes()
        except FileNotFoundError:
            return
        except OSError:
            return  # left to load_data, which names the problem
        self._held_verdicts = (path, data)
        recorded = _review_round.verdicts_of(data).round_id
        current = _review_round.current_round(review_dir)
        owner = _review_round.ownership(current, recorded)
        if owner == _review_round.OWNED:
            self._verdicts_round = recorded
        elif owner == _review_round.STALE:
            self._refuse_superseded_verdicts(recorded, current, "Phase _setup, step 9a")

    def held_verdicts(self, validation_path: Any) -> Optional[bytes]:
        """The bytes of ``validation.json`` step 9a read and checked, when
        *validation_path* names that file; ``None`` otherwise (read it then).
        ``load_data`` parses these, so the verdicts applied are the ones whose
        round was checked."""
        held = getattr(self, "_held_verdicts", None)
        if held is None or os.path.abspath(str(validation_path)) != held[0]:
            return None
        return held[1]

    def _recheck_verdicts_round(self, step: str) -> None:
        """Before judged decisions are recorded and before batches are
        published: the review's checkpoint still records the round the held
        verdicts came from, or the run stops as step 9a stops it (a review
        run started a new round since). Nothing for verdicts with no round
        id."""
        recorded = getattr(self, "_verdicts_round", None)
        if recorded is None:
            return
        current = _review_round.current_round(
            os.path.join(self.out_dir, self.review_subdir))
        if _review_round.ownership(current, recorded) == _review_round.STALE:
            self._refuse_superseded_verdicts(recorded, current, step)

    def _superseded_before_batch(
        self, batch_index: int, tasks: Sequence[Dict[str, Any]],
    ) -> Optional[str]:
        """The executor's check before each batch it dispatches
        (``SchedulerOptions.before_batch``): once the review's checkpoint
        records another round than the held verdicts' (a review run started
        one after the last check), the batch is refused with the native
        loop's words (``write_prompt.superseded_round_text``) and nothing
        later is dispatched. Verdicts with no round id are never refused."""
        recorded = getattr(self, "_verdicts_round", None)
        if recorded is None:
            return None
        current = round_superseded(
            Path(self.out_dir) / self.review_subdir, recorded)
        if current is None:
            return None
        task_id = str((tasks[0] or {}).get("task_id") or "") if tasks else ""
        return superseded_round_text(
            task_id or f"batch {batch_index}", self.review_subdir, recorded, current,
            native=False,
        )

    def _refuse_superseded_verdicts(
        self, recorded: Optional[str], current: Optional[str], step: str,
    ) -> None:
        """Print the refusal of verdicts from round *recorded* while the
        review's checkpoint records *current*, and stop at exit 3."""
        review_dir = os.path.join(self.out_dir, self.review_subdir)
        try:
            host_id = _hosts.resolve_host_id(explicit=getattr(self.args, "host", None))
            rerun = _words.phase_command(
                str(self.args.plan_file), host_id, _routes.resolve_route(host_id),
                self.review_subdir, "--force",
            )
        except Exception:  # noqa: BLE001 - advisory: the flag is named instead
            rerun = f"the review ({self.review_subdir}) again with --force"
        lines = [
            f"ERROR: {self.confirmation_phase_name or self.phase_name} refused: "
            f"{os.path.join(review_dir, _review_round.VALIDATION_NAME)} "
            f"holds the verdicts of review round {recorded}, but "
            f"{self.review_subdir}'s .status.json records another round, "
            f"{current}: a later run of the review started it and it has "
            f"not produced verdicts — it is still running, or it stopped before "
            f"it validated (every model failed, or it was interrupted). "
            f"Applying the earlier round's verdicts would apply a review the "
            f"phase has since replaced. Nothing was applied or recorded.",
            "  If that round is still running, let it finish (`status`), then "
            "run this again.",
            "  Otherwise run the review again with --force (it keeps each "
            "reusable model result, regroups and validates again), then run "
            f"this again: {rerun}",
        ]
        for line in lines:
            print(line, file=sys.stderr)
        record_error(lines[0])
        raise OrchestratorError(
            f"{step}: validation.json belongs to an earlier review round than "
            f"the one on record",
            exit_code=3,
        )

    def _fresh_target_refusal(self) -> Optional[str]:
        """Why ``--fresh`` must not run against the target as it is, or ``None``.

        ``--fresh`` dispatches every batch again, so it presumes the target
        file is back at its pre-run bytes. Measured otherwise (adversarial
        review, 2026-10-02): a completed run, then ``--fresh`` on the plan as
        the run left it — every batch landed a second time at exit 0, and
        ``backup.md`` and every ``pre_batch/`` slot were re-stamped with the
        already-applied bytes, so nothing under the plan dir held the
        pre-run file any more (the plan is often untracked; git does not
        save the user). The evidence is the audit log: every completion of
        this review cycle whose bytes moved recorded the target's
        ``sha256_after``, and a target whose hash is one of those still
        carries that run's edits. Records from before the review this phase
        applies belong to an earlier cycle, whose edits are the legitimate
        starting point, and are not counted.
        """
        target = self.write_target_file()
        if not target or not os.path.isfile(target):
            return None
        phase_dir = os.path.join(self.out_dir, self.phase_name)
        records = AuditLog(phase_dir).records()
        if not records:
            return None
        current = write_safety.file_sha256(target)
        if not current:
            return None
        try:
            root = write_safety.resolve_repo_root(self.plan_path)
            target_key = relative_to_root(target, root)
        except Exception:  # noqa: BLE001 - fall back to matching by hash alone
            target_key = None
        reviewed_at = self._review_completed_at()
        hits: List[Tuple[str, str]] = []
        for record in records:
            if record.get("event") != "completed":
                continue
            # The audit stamps whole seconds; a completion in the review's
            # own second is this cycle's.
            if predates_review(
                _parse_completion_time(record.get("timestamp")), reviewed_at,
                whole_seconds=True,
            ):
                continue
            for path, info in (record.get("observed") or {}).items():
                if target_key is not None and str(path) != target_key:
                    continue
                before = (info or {}).get("sha256_before")
                after = (info or {}).get("sha256_after")
                if after and after != before and after == current:
                    hits.append((str(record.get("task_id")), str(record.get("timestamp"))))
        if not hits:
            return None
        task_id, stamped = hits[-1]
        backup = os.path.join(phase_dir, target_backup_name(self.phase_name))
        backup_hint = (
            f"copy the pre-run file back from {backup}"
            if os.path.isfile(backup)
            else f"there is no {backup} to copy back from"
        )
        return (
            f"ERROR: --fresh would dispatch every batch again, and {target} "
            f"still carries the edits the previous run applied (its sha256 is "
            f"what {task_id} left behind at {stamped}), so each batch would "
            f"land a second time. Put the pre-run file back first — "
            f"{backup_hint}, or roll the batches back newest-first with "
            f"`multi_llm.py util restore-batch --phase-dir \"{phase_dir}\" "
            f"--task-id {task_id}` — or re-invoke with --resume to continue "
            f"from the recorded progress instead. Nothing was dispatched, "
            f"nothing was cleared and no file was modified."
        )

    @staticmethod
    def keep_backup_aside(backup_path: str, target: str) -> Optional[str]:
        """Rename an existing backup whose bytes differ from ``target``'s.

        For ``--fresh``, which re-stamps the backup: the bytes it finds there
        are a rollback point someone may still need, so they move to
        ``<stem>.<sha8 of the bytes>.md`` beside the new backup rather than
        being overwritten (adversarial review, 2026-10-02). A backup already
        holding the target's bytes is left for the re-stamp — nothing is
        lost by overwriting it. Returns the path kept, or ``None``.
        """
        if not os.path.isfile(backup_path) or not os.path.isfile(target):
            return None
        kept_sha = write_safety.file_sha256(backup_path)
        if not kept_sha or kept_sha == write_safety.file_sha256(target):
            return None
        stem, ext = os.path.splitext(backup_path)
        kept = f"{stem}.{kept_sha[:8]}{ext}"
        try:
            os.replace(backup_path, kept)
        except OSError as exc:  # noqa: BLE001 - a backup must not fail the phase
            print(f"Warning: could not keep {backup_path} aside: {exc}", file=sys.stderr)
            return None
        return kept

    def write_target_backup(self) -> Optional[str]:
        """Snapshot the file this phase overwrites as ``{phase}/backup.md``.

        The only ``backup.md`` on disk used to be review-plan's, written when the
        plan was *reviewed* — an hour, and any human edit, before this phase
        rewrote the same file, so the file named "backup" was not a backup of what
        got overwritten. Recovery did exist (batch 0's ``pre_batch/`` snapshot),
        just nowhere a user would look.

        An existing backup is **kept** when this phase already moved bytes —
        a resume's target is part-applied and overwriting the backup with
        part-applied bytes would destroy the only copy of the pre-run file.
        It is *not* kept merely because the file is there: an apply phase may be
        re-run freely after a new review cycle, with the same phase dir and no
        progress *of that cycle* in it (:meth:`_phase_has_recorded_progress`
        dates each signal against the review), and keeping cycle 1's snapshot
        there would leave the cycle-2 bytes the phase is about to overwrite
        saved nowhere while the line below told the user they were backed up.
        ``--fresh`` declares prior progress void and re-stamps for the same
        reason. Either re-stamp keeps a differing earlier backup aside first
        (:meth:`keep_backup_aside`, ``backup.<sha8>.md``): cycle 1's is the
        plan from before cycle 1, a rollback point nothing else holds.
        Returns the path written, or ``None`` when nothing was.

        Neither dry run writes one: ``--dry-run`` reports and stops, and
        ``--dry-run-subagents`` is a preflight that dispatches nothing, so there
        is nothing about to be overwritten on either.
        """
        if getattr(self.args, "dry_run", False) or getattr(
            self.args, "dry_run_subagents", False
        ):
            return None
        target = self.write_target_file()
        if not target or not os.path.isfile(target):
            return None
        phase_dir = os.path.join(self.out_dir, self.phase_name)
        os.makedirs(phase_dir, exist_ok=True)
        backup_path = os.path.join(phase_dir, target_backup_name(self.phase_name))
        if (
            os.path.exists(backup_path)
            and not getattr(self.args, "fresh", False)
            and self._phase_has_recorded_progress(phase_dir)
        ):
            print(
                f"Backup kept: {backup_path} (pre-run bytes from an earlier "
                f"attempt at this phase)",
                file=sys.stderr,
            )
            return None
        # A re-stamp, by `--fresh` or over an earlier review cycle's backup:
        # a backup whose bytes differ from the file about to be overwritten is
        # an earlier run's rollback point, and is kept aside. (Only `--fresh`
        # used to, so the apply after a re-run review lost the plan from
        # before the first cycle.)
        kept = self.keep_backup_aside(backup_path, target)
        if kept:
            about = (
                "the file --fresh is about to back up"
                if getattr(self.args, "fresh", False)
                else "the file this run is about to back up"
            )
            print(
                f"Earlier backup kept at {kept} (its bytes differ from {about})",
                file=sys.stderr,
            )
        try:
            shutil.copy2(target, backup_path)
        except OSError as exc:  # noqa: BLE001 - a backup must not fail the phase
            print(f"Warning: could not write {backup_path}: {exc}", file=sys.stderr)
            return None
        print(f"Backup saved: {backup_path}", file=sys.stderr)
        return backup_path

    def _phase_has_recorded_progress(self, phase_dir: str) -> bool:
        """Whether this phase has already applied something in this review cycle.

        Three signals, any one of which means the target file on disk is no
        longer the pre-run file: an item recorded as processed, the scheduler's
        own report, or one of this write kind's batch results in the phase dir.
        ``--resume`` counts as well, because the native leg leaves none of the
        three — the host applies the edits and the orchestrator never sees them
        — and that flag is how the instructions tell a user to re-enter a
        half-applied phase (`apply_task_suggestions_orchestrator` keys its own
        `tasks-backup.md` on the same flag).

        Each signal is dated against the review's latest completion
        (:meth:`_review_completed_at`) and compared strictly, as the
        scheduler's ``ResumeEvidence.earlier_report_rows`` compares: a processed record by
        its ``timestamp``, the report by its ``written_at`` (its mtime when
        that is missing or unreadable), a batch result by its mtime. One older
        than the review is an earlier cycle's: the phase dir and ``state.json``
        outlive a review re-run, and counting it made the apply after a
        ``--review-plan --force`` print "Backup kept" over the bytes from
        before the first cycle, leaving the plan as the new cycle found it
        saved nowhere. A missing date on either side keeps the signal, as in
        every other cycle check. ``--resume`` is not dated: mid-cycle it is
        the native leg's only signal.

        What is deliberately NOT a signal is the backup file's existence: a new
        review cycle re-runs the phase in the same dir, so that question answers
        "resume" for a run that is nothing of the kind.
        """
        if getattr(self.args, "resume", False):
            return True

        reviewed_at = self._review_completed_at()

        def this_cycle(stamped: Optional[datetime]) -> bool:
            return not predates_review(stamped, reviewed_at)

        if self.state is not None:
            for record in self.state.get_processed_items(self.phase_name).values():
                stamped = (
                    _parse_completion_time(record.get("timestamp"))
                    if isinstance(record, dict) else None
                )
                if this_cycle(stamped):
                    return True
        try:
            names = os.listdir(phase_dir)
        except OSError:
            return False
        if WRITE_BATCH_REPORT_FILENAME in names:
            report_path = os.path.join(phase_dir, WRITE_BATCH_REPORT_FILENAME)
            try:
                with open(report_path, "r", encoding="utf-8") as handle:
                    report = json.load(handle)
            except (OSError, ValueError):
                report = None
            written = report.get("written_at") if isinstance(report, dict) else None
            if this_cycle(stamp_or_mtime(written, report_path)):
                return True
        # The kind's own result pattern, never a glob typed here: it is the same
        # table the executor admits a result filename against, so a new write
        # kind cannot leave this check silently blind.
        pattern = OUTPUT_NAME_PATTERN_BY_KIND.get(self.write_kind)
        return pattern is not None and any(
            # A batch result carries no stamp of its own: its mtime dates it.
            pattern.match(name)
            and this_cycle(stamp_or_mtime(None, os.path.join(phase_dir, name)))
            for name in names
        )

    # ------------------------------------------------------------------
    # The executor leg's closing report (F3): utils/apply_report.py
    # ------------------------------------------------------------------

    def phase_report(self) -> ApplyPhaseReport:
        """The closing report over what this phase holds now.

        Built from the phase's own data each time it is asked for, so a
        report step reads the state the steps before it left. The phase's
        hooks (:meth:`consistency_warnings`, :meth:`resolve_base_ref`,
        :meth:`_document_title`) are read when the report needs them.
        """
        return ApplyPhaseReport(
            phase_name=self.phase_name,
            write_kind=self.write_kind,
            item_noun=self.item_noun,
            item_noun_plural=self.item_noun_plural,
            plan_path=self.plan_path,
            out_dir=self.out_dir,
            review_subdir=self.review_subdir,
            write_result=self.write_result,
            write_tasks=self.write_tasks,
            batches=self.batches,
            batching_stats=self.batching_stats,
            formatted_valid=self.formatted_valid,
            formatted_human=self.formatted_human,
            formatted_skipped=self.formatted_skipped,
            scope_deferred=self.scope_gate.deferred,
            scope_released=self.scope_gate.released,
            state=self.state,
            pinned=self._pinned,
            decisions_overlay_path=self._decisions_overlay_path,
            target_file=self.write_target_file(),
            consistency_warnings=self.consistency_warnings,
            resolve_base_ref=self.resolve_base_ref,
            document_title=self._document_title,
            logger=self.logger,
        )

    def _completed_target_label(self) -> Optional[str]:
        """:meth:`_applied_to_label` for the native ``--mark-completed``
        call, which runs before any setup hook."""
        return self._applied_to_label()

    def _applied_to_label(self) -> Optional[str]:
        """The single file this phase edits, relative to the repository
        root (``write_target_file``), or ``None`` without one."""
        return applied_to_label(self.write_target_file(), self.plan_path)

    def consistency_warnings(self) -> List[str]:
        """Problems the finished edits left in the file they edited (advisory).

        Nothing by default. A phase whose artifact is a graph overrides it
        (apply-task-suggestions re-checks ``tasks.md``), because its batches
        each edit one corner of that graph and none of them sees the whole.
        """
        return []

    def run_write_executor(self) -> Optional[int]:
        """Drive this phase's batches through the write scheduler, or decline.

        Returns ``None`` — meaning "not requested, carry on natively" — unless
        ``--exec-subagents`` or ``--dry-run-subagents`` was passed *and* the phase
        declares a ``write_kind``. Otherwise returns the phase's exit code, which is
        the scheduler's: 0 when every batch verified and finalization ran, 3 when
        the loop stopped at a batch boundary or a human task needs an answer.
        """
        if not self.write_kind:
            return None
        if not (getattr(self.args, "exec_subagents", False)
                or getattr(self.args, "dry_run_subagents", False)):
            return None
        if not self.batches:
            return None

        phase_dir = os.path.join(self.out_dir, self.phase_name)
        os.makedirs(phase_dir, exist_ok=True)
        grouped_file = os.path.join(self.out_dir, self.review_subdir, "grouped.json")
        artifact = self.write_phase_artifact()
        tasks_file = artifact if artifact != self.plan_path else None
        tasks = write_phase_bridge.materialize_write_tasks(
            kind=self.write_kind,
            batches=[
                batch if isinstance(batch, dict) else batch.to_dict()
                for batch in self.batches
            ],
            phase_dir=phase_dir,
            plan_file=self.plan_path,
            tasks_file=tasks_file,
            grouped_file=grouped_file if os.path.exists(grouped_file) else None,
            **self.scope_gate.materialize_kwargs(),
        )
        task_file = write_phase_bridge.write_task_file_for_phase(
            kind=self.write_kind, tasks=tasks, phase_dir=phase_dir,
            plan_file=self.plan_path,
            tasks_file=tasks_file,
            grouped_file=grouped_file if os.path.exists(grouped_file) else None,
        )
        print(
            f"[write-subagents] materialized {len(tasks)} {self.phase_name} "
            f"task(s): {task_file}"
        )

        # D3h: every executor-backed WRITE mode gets a dirty-tree baseline, not just
        # `--implement`, and it is reported at start rather than silently absorbed
        # into the run's diff.
        self._record_pre_existing_changes()

        # The phase's one write
        # target — the plan, or the tasks file — is the grant a dispatch on
        # the plugin-landlock rung carries, and every task's declared set is
        # checked against it. A phase with no single target (apply-code-fixes,
        # `repo-wide`) passes none; its grant is one rule on the repository
        # root (step 3b, revised 2026-10-05), never a target.
        write_target = artifact if self.has_single_write_target else None
        # Every run resumes — a re-run must never apply a landed batch twice —
        # except `--fresh`, which declares prior progress void (`_setup` has
        # already cleared the decisions, the processed items and the
        # prior-changes log): every batch is dispatched again, no result file
        # counts as done, no earlier row is carried and no snapshot reused.
        # That is implement's run without `--resume`. It used to resume as
        # well, so a user who reverted the target and asked to start over got
        # exit 0 with every batch "already complete". `--resume` wins over
        # `--fresh` (the retry builder drops `--fresh` beside it, too).
        fresh = bool(getattr(self.args, "fresh", False)) and not getattr(
            self.args, "resume", False
        )
        try:
            scheduler = write_batch_scheduler.WriteBatchScheduler(SchedulerOptions(
                tasks=tasks,
                phase_dir=phase_dir,
                kind=self.write_kind,
                output_dir=self.out_dir,
                state=self.state,
                plan_file=self.plan_path,
                anchor=self.plan_path,
                resume=not fresh,
                dry_run=bool(getattr(self.args, "dry_run_subagents", False)),
                write_target=write_target,
                # The stopped batches answered `=skip`, and the
                # answer the stop offers, in this host's spelling.
                partial_skips=getattr(self, "partial_skips", None) or None,
                user_commands=self._stop_user_commands(),
                before_batch=self._superseded_before_batch,
                **self.scope_gate.scheduler_kwargs(),
            ))
        except (ExecutorError, WriteSafetyError) as exc:
            # A target that cannot be granted (gone, a symlink, not a regular
            # file, outside the repo) — or a repository root that cannot be
            # pinned (a planted `core.worktree`, review fixes 2026-10-05) —
            # is refused at construction: exit 3 with the scheduler's own
            # words, never the generic handler's exit 1.
            print(f"ERROR: {exc.message}", file=sys.stderr)
            return int(getattr(exc, "exit_code", 3) or 3)
        self.write_tasks = list(tasks)
        result = scheduler.run()
        self.write_result = result
        for line in result.messages:
            print(line, file=sys.stderr if result.exit_code else sys.stdout)
        if result.report_path:
            print(f"[write-subagents] report: {result.report_path}")
        # A batch whose own check failed after its edits, and
        # a code phase nothing verified, are on the result line a host relays.
        stop = getattr(result, "stop", None) or {}
        if stop.get("headline"):
            # An apply phase's
            # stop left the result line with no `error`, so the tool's
            # needs-human message said "Its result line names no error" and
            # the host relayed only the resume command — not what stopped,
            # what the batch reported or what did not run. The headline is
            # that line, as implement records it.
            record_error(stop["headline"])
        notice = write_result_notice(result)
        if notice:
            record_notice(notice)
        if result.exit_code == 0 and not getattr(self.args, "dry_run_subagents", False):
            # The scope policy's completion record; a `preserve`
            # batch's blocker decline is the one stop it adds (exit 3).
            blockers = self._scope_close(self.state)
            if self.state is not None and _sp.round_record(
                    self.state.state, self._scope_phase_word()) is not None:
                self.state.save()
            if blockers:
                self._scope_report_blockers(blockers)
                return 3
        return result.exit_code

    def _materialize_native_write_tasks(self) -> Optional[str]:
        """Write ``{phase}/write_tasks.json`` for the native leg; its path.

        The executor leg's :meth:`run_write_executor` materializes the same
        file through the same bridge before it schedules anything. On the
        native leg it is the input of ``util write-prompt`` — one task id per
        batch, in dispatch order, each with the `prior_changes_id` the host's
        prior-changes append wants — and nothing else reads it. ``None`` when
        this phase declares no write kind or emitted no batch.
        """
        if not self.write_kind or not self.batches:
            return None

        phase_dir = os.path.join(self.out_dir, self.phase_name)
        os.makedirs(phase_dir, exist_ok=True)
        grouped_file = os.path.join(self.out_dir, self.review_subdir, "grouped.json")
        grouped = grouped_file if os.path.exists(grouped_file) else None
        artifact = self.write_phase_artifact()
        tasks_file = artifact if artifact != self.plan_path else None
        tasks = write_phase_bridge.materialize_write_tasks(
            kind=self.write_kind,
            batches=[
                batch if isinstance(batch, dict) else batch.to_dict()
                for batch in self.batches
            ],
            phase_dir=phase_dir,
            plan_file=self.plan_path,
            tasks_file=tasks_file,
            grouped_file=grouped,
            **self.scope_gate.materialize_kwargs(),
        )
        self._native_write_tasks = list(tasks)
        # Stamped native, so `status` shows this run rather
        # than an earlier executor run's `.status.json`.
        # The run its batches belong to is read before
        # this rewrite, so `status` counts what the whole run handed out
        # across a `--resume` and none of an earlier run's records.
        run = native_run_record(
            phase_dir, tasks, resume=bool(getattr(self.args, "resume", False)))
        # The review round its verdicts came from: `util write-prompt`
        # refuses a batch once the review has started another.
        if getattr(self, "_verdicts_round", None):
            run[write_phase_bridge.REVIEW_ROUND_KEY] = {
                "review": self.review_subdir, "round_id": self._verdicts_round,
            }
        return write_phase_bridge.write_task_file_for_phase(
            kind=self.write_kind, tasks=tasks, phase_dir=phase_dir,
            plan_file=self.plan_path, tasks_file=tasks_file, grouped_file=grouped,
            native_host=resolve_host_id(explicit=self._host_id()),
            native_run=run,
        )

    def _refuse_unrecorded_native_resume(self) -> None:
        """Exit 3 when a native ``--resume`` would re-emit a logged, unrecorded batch.

        See :func:`utils.batch_done.unrecorded_logged_batches`. Only under
        ``--resume`` (a bare re-run starts the phase over by contract) and
        only on the native leg, whose batches this method's caller has just
        materialized; the executor leg judges its own result files.
        """
        if not getattr(self.args, "resume", False) or self.state is None:
            return
        tasks = getattr(self, "_native_write_tasks", None) or []
        if not tasks:
            return

        word = self.confirmation_phase_name or self.phase_name
        unrecorded = unrecorded_logged_batches(
            tasks, output_dir=self.out_dir, phase=word,
            state=self.state.state, processed_phase=self.phase_name,
        )
        if not unrecorded:
            return
        phase_dir = os.path.join(self.out_dir, self.phase_name)
        for line in resume_refusal_lines(
            unrecorded, phase_dir=phase_dir, mode_word=word,
        ):
            print(line, file=sys.stderr)
        raise OrchestratorError(
            f"Phase _write_outputs, step 33: --resume refused, "
            f"{len(unrecorded)} logged batch(es) carry no progress record",
            exit_code=3,
        )

    def _record_pre_existing_changes(self) -> None:
        """Record the dirty-tree baseline for this write phase (D3h).

        The same recording ``implement_orchestrator.record_pre_existing_changes``
        does, extended to every executor-backed write mode so each has a baseline
        the final diff can be isolated against — and reported at start, because a
        dirty tree silently absorbed into a run's diff is how an unrelated edit gets
        attributed to a batch.
        """
        if self.state is None:
            return
        if self.state.get("pre_existing_changes") is not None:
            existing = self.state.get("pre_existing_changes") or []
            # "path(s)", not "file(s)": `git status --porcelain` collapses an
            # untracked directory into one entry, so a baseline routinely names
            # directories (`plans/`) as well as files.
            print(
                f"[write-subagents] dirty-tree baseline already recorded "
                f"({len(existing)} path(s))"
            )
            return
        try:
            pre_existing = sorted(
                {f for f in get_modified_files() if f} | {f for f in get_staged_files() if f}
            )
        except Exception as exc:  # noqa: BLE001 - a baseline probe must not fail a run
            print(f"[write-subagents] warning: could not record baseline: {exc}")
            pre_existing = []
        self.state.set("pre_existing_changes", list(pre_existing))
        self.state.save()
        if pre_existing:
            print(
                f"[write-subagents] dirty tree at start: {len(pre_existing)} "
                f"uncommitted path(s) recorded as the baseline — they are NOT part "
                f"of this run's changes: {', '.join(pre_existing[:10])}"
                + (" …" if len(pre_existing) > 10 else "")
            )
        else:
            print("[write-subagents] clean working tree at start")

    # ==================================================================
    # Abstract methods (subclass must implement)
    # ==================================================================

    def load_data(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Load grouped items and validation results from the phase subdirectory.

        Returns:
            Tuple of (groups, validation) where groups is the list of
            grouped items and validation is the list of validation results.

        Raises:
            OrchestratorError: If required data files are missing or malformed.
        """
        raise NotImplementedError(
            f"{type(self).__name__} must implement load_data()"
        )

    def parse_user_edits(
        self, report_path: str
    ) -> Dict[str, Tuple[str, str]]:
        """Parse user-edited descriptions from the review report markdown.

        Args:
            report_path: Path to the report.md file.

        Returns:
            Dict mapping item ID to (original_description, edited_description).
        """
        raise NotImplementedError(
            f"{type(self).__name__} must implement parse_user_edits()"
        )

    def merge_user_edits(
        self,
        groups: List[Dict[str, Any]],
        edited_descriptions: Dict[str, Tuple[str, str]],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Apply user-edited descriptions to group items.

        Args:
            groups: List of group dicts (deep-copied internally).
            edited_descriptions: Mapping from parse_user_edits().

        Returns:
            Tuple of (updated_groups, edit_log).
        """
        raise NotImplementedError(
            f"{type(self).__name__} must implement merge_user_edits()"
        )

    def parse_skips_from_report(
        self, report_path: str
    ) -> Tuple[Set[str], Set[str], Set[str]]:
        """Parse user-skipped item identifiers from the review report.

        Args:
            report_path: Path to the report.md file.

        Returns:
            Tuple of (skipped_group_indices, skipped_suggestion_ids,
            old_skipped_ids). Each is a set of string identifiers.
        """
        raise NotImplementedError(
            f"{type(self).__name__} must implement parse_skips_from_report()"
        )

    def parse_validation_overrides_from_report(
        self, report_path: str
    ) -> Tuple[Dict[str, str], Dict[str, str]]:
        """Parse validation status overrides from the review report.

        Args:
            report_path: Path to the report.md file.

        Returns:
            Tuple of (group_overrides, suggestion_overrides). Each maps
            item ID to override status string.
        """
        raise NotImplementedError(
            f"{type(self).__name__} must implement parse_validation_overrides_from_report()"
        )

    def format_item_for_output(
        self, group: Dict[str, Any], index: int
    ) -> Dict[str, Any]:
        """Format a single group for inclusion in output JSON.

        Args:
            group: A merged group dict (with validation fields).
            index: Zero-based index in the filtered list.

        Returns:
            Dict with phase-specific fields ready for JSON serialization.
        """
        raise NotImplementedError(
            f"{type(self).__name__} must implement format_item_for_output()"
        )

    def create_batches(
        self, items: List[Dict[str, Any]]
    ) -> List[Any]:
        """Partition formatted items into SuggestionBatch batches.

        Default implementation uses ``SuggestionBatch`` and
        ``group_suggestions_for_subagents``.  Subclasses that need a
        different batch type (e.g. ``CodeFixBatch``) should override.

        Args:
            items: List of formatted item dicts.

        Returns:
            List of SuggestionBatch objects (or subclass-specific batch type).
        """
        if getattr(self.args, "no_batch", False):
            batches: List[Any] = [
                SuggestionBatch(
                    suggestions=[s],
                    section_key=s.get("reference", "unknown"),
                    batch_type=s.get("type", "modification"),
                    total_chars=len(s.get("description", "")),
                )
                for s in items
            ]
            self.batching_stats = {
                "total_suggestions": len(items),
                "total_batches": len(items),
                "subagent_calls_saved": 0,
                "efficiency_gain_percent": 0,
                "batching_enabled": False,
            }
        else:
            batches = group_suggestions_for_subagents(
                items,
                max_per_batch=getattr(self.args, "max_batch_size", 4),
            )
            self.batching_stats = estimate_batch_processing_stats(batches)
            self.batching_stats["batching_enabled"] = True

        print("\nBatching results:", file=sys.stderr)
        print(f"  Total suggestions: {self.batching_stats.get('total_suggestions', 0)}", file=sys.stderr)
        print(f"  Total batches: {self.batching_stats.get('total_batches', 0)}", file=sys.stderr)
        if self.batching_stats.get("batching_enabled"):
            print(f"  Subagent calls saved: {self.batching_stats.get('subagent_calls_saved', 0)}", file=sys.stderr)
            print(f"  Efficiency gain: {self.batching_stats.get('efficiency_gain_percent', 0)}%", file=sys.stderr)

        return batches

    def generate_batch_prompts(
        self, batches: List[Any]
    ) -> List[Any]:
        """Attach prompt text to each batch for subagent consumption.

        Args:
            batches: List of batch objects from create_batches().

        Returns:
            The same batch list with prompt fields populated.
        """
        raise NotImplementedError(
            f"{type(self).__name__} must implement generate_batch_prompts()"
        )

    def build_output_json(
        self,
        batches: List[Any],
        *,
        resume_info: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Assemble the final orchestrator_output.json payload.

        Args:
            batches: List of batch objects with prompts attached.
            resume_info: Optional resume state from a prior interrupted run.

        Returns:
            Dict representing the complete output JSON structure.
        """
        raise NotImplementedError(
            f"{type(self).__name__} must implement build_output_json()"
        )

    def get_output_path(self) -> str:
        """Return the filesystem path for orchestrator_output.json.

        Under ``self.out_dir``, which carries ``find_output_dir``'s
        double-nesting guard.
        """
        return os.path.join(self.out_dir, self.phase_name, "orchestrator_output.json")

    def print_text_summary(
        self,
        batches: List[Any],
        output_path: str,
    ) -> None:
        """Print a human-readable summary of the orchestrator results.

        Args:
            batches: List of batch objects that were written.
            output_path: Path where orchestrator_output.json was saved.
        """
        raise NotImplementedError(
            f"{type(self).__name__} must implement print_text_summary()"
        )

    # ==================================================================
    # Shared helpers for subclass use
    # ==================================================================

    def build_human_review_config(self) -> Dict[str, Any]:
        """Build the human_review_config dict from formatted_human items.

        This is identical across all three orchestrator subclasses, so it
        lives here to avoid triplication.
        """
        by_importance: Dict[str, List[Dict[str, Any]]] = {"HIGH": [], "MEDIUM": [], "LOW": []}
        for item in self.formatted_human:
            by_importance[_importance.normalize(item.get("importance"))].append(item)

        mode = getattr(self.args, "batch_review_mode", "by-importance")
        agent_decide = bool(getattr(self.args, "agent_decide", False))
        return {
            "mode": mode,
            "batch_enabled": mode != "individual",
            # When "judge_auto_decide", the host agent skips the interactive
            # batch-review prompt and evaluates each needs-human-decision item
            # itself ("Let the agent decide" mode). See
            # references/human-decision-batch.md.
            "decision_mode": JUDGE_AUTO_DECIDE if agent_decide else "interactive",
            "prompt_strategy": "single_batch" if mode != "individual" else "per_item",
            "by_importance": by_importance,
            "total_count": len(self.formatted_human),
            "batch_prompt_template": "batch_approval_v1",
            # Convenience index of items the reviewer pre-marked "Let the agent
            # decide" in the report. The authoritative per-item signal is the
            # per-item ``decision_mode == "judge_auto_decide"`` flag the
            # formatters emit; this list lets the instructions find them without
            # scanning every item. The global ``decision_mode`` above stays
            # "interactive" unless --agent-decide was passed; per-item routing
            # is purely additive.
            JUDGE_DECIDE_ITEM_IDS: [
                it.get("group_id", "")
                for it in self.formatted_human
                if it.get("decision_mode") == JUDGE_AUTO_DECIDE
            ],
        }

    # ==================================================================
    # Optional hooks (override if needed)
    # ==================================================================

    def pre_validate_hook(self) -> None:
        """Hook called during _setup before output directory validation.

        Subclasses can use this to discover additional files (e.g.,
        tasks.md), check prerequisites (e.g., prior phase completion),
        or set up instance state needed by later phases.

        The default implementation is a no-op.
        """
        pass

    def post_load_hook(self) -> None:
        """Hook called after load_data() in _load_and_parse_inputs.

        Subclasses can use this to build auxiliary data structures
        (e.g., issue-to-group map for code_fixes).

        The default implementation is a no-op.
        """
        pass

    def resolve_base_ref(self) -> str:
        """Return the git base ref used for revalidation and batch prompts.

        Called by ``handle_revalidation()`` and (in the code_fixes
        subclass) ``generate_batch_prompts()``.  The default returns an
        empty string, which is correct for plan-review orchestrators
        that have no git diff context.  The code_fixes subclass
        overrides this to resolve ``--base-ref`` / ``state.head_at_start``.

        Returns:
            A validated git ref string, or empty string.
        """
        return ""

    def _route_judge_decide_marker(
        self, group: Dict[str, Any], key: Any, value: str
    ) -> bool:
        """Handle a ``judge_decide`` override as a routing marker, not a status.

        Returns ``True`` if *value* was a ``judge_decide`` marker (the caller
        should skip the ``validation_status`` assignment), ``False`` otherwise.

        A ``judge_decide`` marker keeps the item in ``needs_human`` and tags it
        so the per-item "Let the agent decide" judge picks it up at apply time; it
        must NEVER be written into ``validation_status`` (which is not a real
        status and would silently fall through ``filter_items``).
        """
        if canonical_value(value) == JUDGE_DECIDE:
            group[JUDGE_DECIDE] = True
            # Diagnostics-only mirror; routing is driven by group["judge_decide"]
            # above, not by this set (see declaration note in __init__).
            self.judge_decide_overrides.add(key)
            # A surfaced reason so the routing is visible in logs/reports. Not a
            # setdefault no-op — the item already carries a needs-human reason.
            group["validation_reason"] = "Routed to the judge agent by reviewer"
            return True
        return False

    def apply_group_validation_overrides(self) -> None:
        """Apply group-level validation overrides to merged groups.

        Default implementation: hash-based string key matching.
        Keys in ``self.validation_overrides`` are matched against
        the ``group_hash`` field of each merged group.

        The ``apply_code_fixes`` subclass overrides this to match on
        integer issue-number keys instead.
        """
        if not self.validation_overrides:
            return

        override_count = 0
        for group in self.merged:
            ghash = group.get("group_hash", "")
            if ghash and ghash in self.validation_overrides:
                value = canonical_value(self.validation_overrides[ghash])
                if value not in VALID_OVERRIDE_VALUES:
                    print(
                        f"WARNING: ignoring unknown validation override "
                        f"{value!r} for group [{str(ghash)[:8]}]; leaving its "
                        f"underlying status unchanged.",
                        file=sys.stderr,
                    )
                    continue
                # Route "judge_decide" as a marker, never as a status.
                if self._route_judge_decide_marker(group, ghash, value):
                    override_count += 1
                    continue
                old_status = group.get("validation_status", "unknown")
                group["validation_status"] = value
                group["validation_reason"] = f"User override (was {old_status})"
                group["user_override"] = True
                override_count += 1
        if override_count:
            print(
                f"Applied {override_count} user validation overrides",
                file=sys.stderr,
            )

    def apply_suggestion_validation_overrides(self) -> None:
        """Apply per-suggestion validation overrides to ``self.merged``.

        ``invalid`` drops the suggestion; ``valid`` flags it (and promotes the
        group if *all* survivors are valid); ``judge_decide`` is a routing
        marker that keeps the suggestion and, after the loop, routes the whole
        containing group to the per-item judge (the apply-time review unit is a
        group, so the marker is propagated up — including the mixed-group case
        where only one suggestion is marked). Unknown values are warned and
        ignored.
        """
        if not self.suggestion_validation_overrides:
            return

        sugg_override_count = 0
        for idx, group in enumerate(self.merged, 1):
            suggestions = group.get("suggestions", [])
            modified = False
            for sugg_idx, sugg in enumerate(suggestions, 1):
                shash = sugg.get("suggestion_hash", "")
                positional_id = f"G{idx}S{sugg_idx}"
                matched_key = None
                if shash and shash in self.suggestion_validation_overrides:
                    matched_key = shash
                elif positional_id in self.suggestion_validation_overrides:
                    matched_key = positional_id

                if matched_key is not None:
                    override_status = canonical_value(
                        self.suggestion_validation_overrides[matched_key]
                    )
                    if override_status not in VALID_OVERRIDE_VALUES:
                        print(
                            f"WARNING: ignoring unknown per-suggestion "
                            f"validation override {override_status!r} for "
                            f"{positional_id}; leaving it unchanged.",
                            file=sys.stderr,
                        )
                        continue
                    if override_status == "invalid":
                        sugg["_user_override_invalid"] = True
                    elif override_status == "valid":
                        sugg["_user_override_valid"] = True
                    elif override_status == JUDGE_DECIDE:
                        # Routing marker: keep the suggestion (do NOT drop or
                        # promote) and tag it. Propagated to the group below so
                        # the whole group routes to the per-item judge.
                        sugg[JUDGE_DECIDE] = True
                    sugg_override_count += 1
                    modified = True

            if modified:
                remaining = [
                    s
                    for s in suggestions
                    if not s.get("_user_override_invalid")
                ]
                group["suggestions"] = remaining
                # A "Let the agent decide" marker (set group-level by
                # apply_group_validation_overrides, or per-suggestion in the
                # loop above) is an affirmative "route to the judge" request and
                # must win over a "valid" promotion. Without this guard, a group
                # marked judge_decide whose surviving suggestions are all
                # individually "valid" would be promoted to "valid" while still
                # carrying judge_decide=True; filter_items only honours
                # judge_decide in the needs-human-decision branch, so the group
                # would auto-apply and bypass the judge.
                marked_judge_decide = group.get(JUDGE_DECIDE) or any(
                    s.get(JUDGE_DECIDE) for s in remaining
                )
                if (
                    not marked_judge_decide
                    and remaining
                    and all(s.get("_user_override_valid") for s in remaining)
                    and group.get("validation_status")
                    in ("needs-human-decision", "validation_failed")
                ):
                    old_status = group.get("validation_status", "unknown")
                    group["validation_status"] = "valid"
                    group["validation_reason"] = (
                        f"All suggestions individually marked valid by user "
                        f"(was {old_status})"
                    )
                    group["user_override"] = True

                # Reconcile per-suggestion -> group granularity: if any
                # surviving suggestion is "judge_decide", route the whole
                # group to the judge (the apply-time review unit is a group,
                # and the formatters only inspect the group). This also covers
                # the mixed-group case (one judge_decide suggestion alongside
                # other untouched needs-human suggestions).
                if any(
                    s.get(JUDGE_DECIDE)
                    for s in group.get("suggestions", [])
                ):
                    group[JUDGE_DECIDE] = True
                    # Diagnostics-only mirror; the group["judge_decide"] flag
                    # above is what actually routes the group to the judge (see
                    # declaration note in __init__). This set is never read.
                    self.judge_decide_overrides.add(
                        group.get("group_hash", "")
                    )

        if sugg_override_count:
            print(
                f"Applied {sugg_override_count} per-suggestion validation overrides",
                file=sys.stderr,
            )

    def handle_revalidation(self) -> None:
        """Handle --revalidate flow if supports_revalidation is True.

        When ``supports_revalidation`` is ``False`` (e.g., for
        task_suggestions), this returns immediately.

        Checks the --revalidate, --revalidate-model, --revalidate-all-human,
        and --dry-run CLI flags to determine the revalidation mode:

        1. **dry-run**: Print which items *would* be revalidated, then return
           (the caller continues with the normal flow).
        2. **default** (subagent delegation): Prepare batched revalidation
           tasks, write them to ``revalidation_tasks.json``, emit the
           ``[REVALIDATION_PENDING]`` / ``[REVALIDATION_BATCHES_PENDING]``
           marker, and ``sys.exit(0)`` so that Claude Code picks up the
           task file.
        """
        if not self.supports_revalidation:
            return

        revalidate = getattr(self.args, "revalidate", False)
        revalidate_model = getattr(self.args, "revalidate_model", None)

        if not revalidate and not revalidate_model:
            return

        print("\n--- REVALIDATION MODE ---", file=sys.stderr)

        review_dir = os.path.join(self.out_dir, self.review_subdir)
        validation_path = Path(review_dir) / "validation.json"
        include_all_human = getattr(self.args, "revalidate_all_human", False)
        dry_run = getattr(self.args, "dry_run", False)

        # ----- dry-run: report what would be revalidated -----
        if dry_run:
            items_to_revalidate = []
            for i, val in enumerate(self.validation):
                status = val.get("status", "needs-human-decision")
                error_type = val.get("error_type", "unknown")
                would_revalidate = (
                    status == "validation_failed"
                    or (
                        include_all_human
                        and status == "needs-human-decision"
                        and error_type != ERROR_TYPE_AMBIGUOUS
                    )
                )
                if would_revalidate:
                    items_to_revalidate.append(
                        {
                            "group_index": i,
                            "current_status": status,
                            "error_type": error_type,
                            "reason": val.get("reason", ""),
                        }
                    )

            print(
                f"\n[dry-run] Would revalidate {len(items_to_revalidate)} items:",
                file=sys.stderr,
            )
            for item in items_to_revalidate[:5]:
                print(
                    f"  - Group {item['group_index']}: "
                    f"{item['current_status']} ({item['error_type']})",
                    file=sys.stderr,
                )
            if len(items_to_revalidate) > 5:
                print(
                    f"  ... and {len(items_to_revalidate) - 5} more",
                    file=sys.stderr,
                )
            # Return without exiting — caller proceeds with normal flow
            return

        # Read context for revalidation prompts
        context = self.get_revalidation_context()
        model = revalidate_model or "auto"

        # ----- default: prepare for Claude Code subagent revalidation -----
        print(
            "Preparing batched revalidation for Claude Code subagent...",
            file=sys.stderr,
        )

        # Resolve base_ref via hook (non-empty for code_fixes, empty for others)
        base_ref = self.resolve_base_ref()
        if base_ref:
            print(
                f"Revalidation git base reference: {base_ref}",
                file=sys.stderr,
            )

        # 2.1b: the revalidation judges the CURRENT document (the one this
        # apply step just wrote), bound when revalidation is materialized —
        # read once and snapshotted as `revalidation-snapshot.md`, so an
        # over-limit document is named by a hash-bound path. The subclass says
        # which document it is (`plan`, `tasks`, `diff`).
        context_document = self.get_revalidation_document(review_dir)
        if context_document is not None:
            context = context_document.text
        # One views transaction: the round's sidecars and its task file
        # (docs/development/delegation.md#the-host-index).
        with host_views_lock(review_dir):
            revalidation_tasks = prepare_batched_revalidation_tasks(
                groups=self.groups,
                validation_results=self.validation,
                context=context,
                output_dir=review_dir,
                plan_file=str(self.plan_path),
                include_all_human=include_all_human,
                model=model,
                orchestrator=os.path.basename(sys.argv[0])
                if sys.argv
                else f"{self.phase_name}_orchestrator.py",
                base_ref=base_ref,
                context_document=context_document,
                context_kind=(
                    context_document.label if context_document is not None else None
                ),
                phase=os.path.basename(os.path.normpath(review_dir)),
                extra_instructions=self.get_revalidation_instructions(),
                # The apply's effective policy (step 10b: explicit flag, the
                # round's recorded apply override, its review policy, expand);
                # the raw flag only when step 10b never ran.
                scope_policy=(
                    self.scope_gate.policy.policy if self.scope_gate.policy is not None
                    else getattr(self.args, "scope_policy", None)
                ),
            )

            if revalidation_tasks["items_to_revalidate"] == 0:
                print("No items need revalidation.", file=sys.stderr)
                return

            # Save revalidation task instructions
            revalidation_task_path = os.path.join(
                review_dir, "revalidation_tasks.json"
            )
            with open(revalidation_task_path, "w", encoding="utf-8") as f:
                json.dump(revalidation_tasks, f, indent=2)

        total_batches = revalidation_tasks.get("total_batches", 1)
        if total_batches == 1:
            print(f"\n[REVALIDATION_PENDING] {revalidation_task_path}")
        else:
            print(
                f"\n[REVALIDATION_BATCHES_PENDING] {revalidation_task_path}"
            )
            print(f"Batches: {total_batches}")

        print("\nRevalidation prepared for Claude Code subagent.")
        print(
            f"Items to revalidate: {revalidation_tasks['items_to_revalidate']}"
        )

        # D3b: with --exec-subagents this process dispatches the revalidation
        # batch and merges it in place, so the phase continues with the updated
        # validation instead of exiting for a host to drive a second turn.
        if review_orchestrator_base.dispatch_subagent_tasks(
            self.args,
            task_file=revalidation_task_path,
            phase_dir=review_dir,
            phase=self.phase_name,
            document=revalidation_tasks,
            plan_path=str(self.plan_path),
            label="revalidation",
        ):
            self.validation = merge_batched_revalidation_results(
                output_dir=review_dir,
                revalidation_metadata=revalidation_tasks,
                groups=self.groups,
            )
            save_validation_results(
                self.validation, validation_path, model=model,
                scope=revalidation_tasks.get("scope"),
            )
            print(f"Updated validation saved to: {validation_path}", file=sys.stderr)
            return

        print(
            "\nAfter revalidation completes, run this orchestrator again "
            "without --revalidate"
        )
        self._note_json_stop(
            "revalidation_pending",
            "Revalidation tasks are written for the host to run; re-run this "
            "phase without --revalidate once they complete.",
            revalidation_tasks=revalidation_task_path,
        )
        sys.exit(0)  # Exit — Claude Code handles revalidation

    def get_revalidation_instructions(self) -> Optional[str]:
        """Phase guidance appended to every revalidation batch prompt.

        ``None`` (the default) lets ``prepare_batched_revalidation_tasks``
        derive it from the context kind, as it always has. A subclass whose
        revalidators must read code a particular way returns the text itself,
        whatever document the batch carries as its context.
        """
        return None

    def get_revalidation_document(self, review_dir: str) -> Optional[Any]:
        """The document a revalidation judges, bound for this round (2.1b).

        Default: the plan as it is now, read once as bytes and snapshotted to
        ``{review_dir}/revalidation-snapshot.md`` (never over the original
        round's ``validation-snapshot.md``, which that round's task file still
        binds). ``None`` when it cannot be read or decoded, which falls back to
        :meth:`get_revalidation_context`'s text with no path.
        """

        try:
            return bind_document_file(
                str(self.plan_path), review_dir, label="plan",
                snapshot_name=REVALIDATION_SNAPSHOT_NAME,
            )
        except Exception as exc:  # noqa: BLE001 - degrade to the text context
            print(
                f"Warning: could not bind {self.plan_path} for revalidation "
                f"({exc}); the revalidation prompts carry no path.",
                file=sys.stderr,
            )
            return None

    def get_revalidation_context(self) -> str:
        """Return the context string used during revalidation.

        Default returns plan file contents. Subclasses override to provide
        alternative context (e.g. diff_context.txt for code_fixes).

        Only called when ``supports_revalidation=True``.

        Returns:
            Context string for revalidation prompts.
        """
        try:
            with open(self.plan_path, "r", encoding="utf-8") as f:
                return f.read()
        except (OSError, IOError):
            self.logger.warning(
                "Could not read plan file for revalidation context: %s",
                self.plan_path,
            )
            return ""

    def print_native_tests_not_run(self) -> None:
        """``--mark-completed``'s ``[TESTS_NOT_RUN]`` line, for apply-code-fixes.

        The native leg's line saying nothing ran the repository's
        tests, naming the checks the batches were asked to run and what each
        reported (the executor's own, ``native_apply_fixes_unverified_line``,
        which is ``None`` with a ``driver.verify_command`` set or no batch of
        the phase recorded completed). One method, because two calls close the
        phase: ``--mark-completed``, and the no-items exit of a ``--resume``
        that found every batch already applied (Fable review 2026-10-09), and
        the record and this line must not disagree between them. A no-op for
        the phases that edit no code.
        """
        if self.write_kind != "apply_code_fixes":
            return

        tests = native_apply_fixes_unverified_line(self.plan_path)
        if tests:
            print(f"[TESTS_NOT_RUN] {tests}", file=sys.stderr)

    def handle_no_items_early_exit(self) -> None:
        """Handle the case where no actionable items remain after filtering.

        Called when both ``self.valid`` and ``self.needs_human`` are empty.
        The default implementation is a no-op (suggestions has no early exit).

        Subclasses override to write empty output, log messages, mark
        the phase as skipped, and call ``sys.exit(0)``.
        """
        pass

    # ==================================================================
    # Shared base-class logic (not abstract, not hooks)
    # ==================================================================

    def load_html_selections(
        self,
        review_dir: str,
        edited_descriptions: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Load HTML-based user selections and apply edits.

        Step 16 of ``_load_and_parse_inputs()``.  Identical across all
        three orchestrators.

        Args:
            review_dir: Path to the review phase directory.
            edited_descriptions: Previously parsed edited descriptions
                (from report.md), used as fallback when HTML selections
                are absent.
        """
        html_selections = load_html_selections(
            Path(review_dir),
            groups=self.groups,
            plan_path=self.plan_path,
        )
        if not html_selections:
            return

        print(
            f"Found HTML selections from: {review_dir}/user_selections.json",
            file=sys.stderr,
        )

        # Merge with HTML taking precedence
        (
            self.skipped_group_indices,
            self.skipped_suggestion_ids,
            html_edited,
        ) = merge_selections(
            html_selections,
            self.skipped_group_indices,
            self.skipped_suggestion_ids,
            edited_descriptions or {},
        )

        # Apply HTML-edited descriptions if any
        if html_edited:
            # Build lookup for original descriptions (by hash and positional ID)
            groups_lookup: Dict[str, str] = {}
            for group_idx, group in enumerate(self.groups, start=1):
                for sugg_idx, sugg in enumerate(
                    group.get("suggestions", []), start=1
                ):
                    positional_id = f"G{group_idx}S{sugg_idx}"
                    groups_lookup[positional_id] = sugg.get("desc", "")
                    shash = sugg.get("suggestion_hash", "")
                    if shash:
                        groups_lookup[shash] = sugg.get("desc", "")

            html_edit_dict = {
                k: (groups_lookup.get(k, ""), v) for k, v in html_edited.items()
            }
            if html_edit_dict:
                self.groups, extra_log = self.merge_user_edits(
                    self.groups, html_edit_dict
                )
                self.edit_log.extend(extra_log)
                print(
                    f"Applied {len(extra_log)} HTML-edited descriptions",
                    file=sys.stderr,
                )

        # Merge validation overrides from HTML.
        #
        # Keys can arrive in three shapes:
        #   - "G{N}S{M}"  -> a per-suggestion override
        #   - a group_hash (current report format)
        #   - a bare 0-based group index, e.g. "0" == the first group as
        #     displayed (legacy report format)
        #
        # A bare index must be resolved to its group_hash *here*, while the
        # groups are in scope, so that both orchestrator families match by
        # hash downstream. If it isn't: the code-fixes matcher enumerates
        # groups 1-based (so index "0" is off-by-one and never matches) and
        # the suggestion orchestrators match on hash strings only (so an int
        # key never matches at all). Either way the user's override was
        # silently dropped. Resolving to a hash also makes the override
        # order-independent, consistent with the rest of the join logic.
        #
        # A group_hash is normally non-numeric but can rarely be all digits,
        # so check the known-hash set first — a hash is never mistaken for an
        # index.
        known_group_hashes = {
            g.get("group_hash", "")
            for g in self.groups
            if g.get("group_hash")
        }
        html_overrides = html_selections.get("validation_overrides", {})
        for key, value in html_overrides.items():
            key_str = str(key)
            if re.match(r"G\d+S\d+", key_str, re.IGNORECASE):
                self.suggestion_validation_overrides[key_str.upper()] = value
            elif key_str in known_group_hashes:
                # Current report format: already keyed by group_hash.
                self.validation_overrides[key_str] = value
            elif key_str.isdigit() and int(key_str) < len(self.groups):
                # Legacy report format: 0-based group index -> group_hash.
                ghash = self.groups[int(key_str)].get("group_hash", "")
                if ghash:
                    self.validation_overrides[ghash] = value
                else:
                    print(
                        f"WARNING: HTML validation override for group index "
                        f"{key_str} has no group_hash; falling back to a "
                        f"positional key (may not apply).",
                        file=sys.stderr,
                    )
                    self.validation_overrides[int(key_str)] = value
            else:
                # Unrecognized: an out-of-range index, or a hash from a
                # different grouping. Preserve the original key (as int when
                # numeric, so the legacy code-fixes integer-key path keeps
                # working) rather than dropping the override outright.
                if key_str.isdigit():
                    self.validation_overrides[int(key_str)] = value
                else:
                    self.validation_overrides[key_str] = value

    def load_and_apply_consolidated_decisions(
        self, review_dir: str
    ) -> None:
        """Load and apply C-level consolidated decisions.

        Step 17 of ``_load_and_parse_inputs()``.  Identical across all
        three orchestrators.

        Args:
            review_dir: Path to the review phase directory.
        """
        c_level_skips, c_level_overrides = load_merged_suggestions(
            phase_dir=review_dir,
            groups=self.groups,
            plan_file=self.plan_path,
            accept_stale=getattr(
                self.args, "accept_stale_consolidation", False
            ),
        )

        if not c_level_skips and not c_level_overrides:
            return

        # Convert C-level 0-based indices to group hashes for merging
        for idx_0based in c_level_skips:
            if 0 <= idx_0based < len(self.groups):
                ghash = self.groups[idx_0based].get("group_hash", "")
                if ghash:
                    self.skipped_group_indices.add(ghash)
                else:
                    print(
                        f"WARNING: C-level skip for group index {idx_0based} has no group_hash",
                        file=sys.stderr,
                    )

        # C-level validation overrides
        for idx_0based, override_status in c_level_overrides.items():
            if 0 <= idx_0based < len(self.groups):
                ghash = self.groups[idx_0based].get("group_hash", "")
                if ghash:
                    if ghash not in self.validation_overrides:
                        self.validation_overrides[ghash] = override_status
                else:
                    print(
                        f"WARNING: C-level override for group index {idx_0based} has no group_hash",
                        file=sys.stderr,
                    )

        c_total = len(c_level_skips) + len(c_level_overrides)
        print(
            f"Applied {c_total} consolidated (C-level) decisions "
            f"({len(c_level_skips)} skips, {len(c_level_overrides)} overrides)",
            file=sys.stderr,
        )

    # ==================================================================
    # Internal helpers
    # ==================================================================

    def _handle_dry_run(self) -> None:
        """Print dry-run batch summary and return.

        Called from ``_prepare_batches`` when ``--dry-run`` is active. Under
        ``--output-format json`` the same report is also the run's payload: a
        fresh ``status: dry_run`` object carrying the selection under the
        output file's own keys (``to_apply``, ``needs_human_review``,
        ``skipped_items``, ``summary``), never the output file of a real run.
        """
        print("\n--- DRY RUN ---", file=sys.stderr)
        print("\nWould apply the following batches:", file=sys.stderr)
        batches: List[Dict[str, Any]] = []
        for i, batch in enumerate(self.batches):
            # Try to get batch info generically
            section = getattr(batch, "section_key", None) or getattr(
                batch, "file_key", None
            ) or "various"
            count = getattr(batch, "size", 0)
            batch_type = getattr(batch, "batch_type", "unknown")
            print(
                f"  Batch {i + 1}: {count} {self.item_noun}(s) [{batch_type}] in {section}",
                file=sys.stderr,
            )
            items = getattr(batch, "suggestions", None) or getattr(
                batch, "fixes", None
            ) or []
            for s in items:
                print(
                    f"    - [{s.get('importance', 'MEDIUM')}] {s.get('title', 'Unknown')}",
                    file=sys.stderr,
                )
            batches.append({
                "batch": i + 1,
                "batch_type": batch_type,
                "section": section,
                "item_count": count,
                "items": [
                    {"importance": s.get("importance", "MEDIUM"),
                     "title": s.get("title", "Unknown")}
                    for s in items
                ],
            })

        if self.needs_human:
            print("\nWould ask for human review:", file=sys.stderr)
            for group in self.needs_human:
                theme = group.get("theme", group.get("title", "Unknown"))
                reason = group.get("validation_reason", "No reason")
                print(f"  - {theme}: {reason}", file=sys.stderr)

        for line in self.scope_gate.summary_lines(would=True):
            print(line, file=sys.stderr)

        if self.json_output():
            self.emit_payload({
                "status": "dry_run",
                "phase": self.confirmation_phase_name or self.phase_name,
                "exit_code": 0,
                "plan_file": self.plan_path,
                # A dry run renders no prompts, so a batch is its items.
                "batches": batches,
                "to_apply": self.formatted_valid,
                "needs_human_review": self.formatted_human,
                "skipped_items": self.formatted_skipped,
                "user_skipped_items": self.user_skipped_items,
                "summary": {
                    "batch_count": len(batches),
                    "valid_count": len(self.valid),
                    "needs_human_count": len(self.needs_human),
                    "skipped_count": len(self.skipped),
                    "user_skipped_count": len(self.user_skipped_items),
                },
            })
