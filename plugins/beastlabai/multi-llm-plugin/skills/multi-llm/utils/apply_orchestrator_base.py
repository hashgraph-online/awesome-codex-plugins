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
import asyncio
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
    build_skipped_output,
    emit_json_output,
    write_and_emit_output,
)
from .apply_path_helpers import load_json_file
from .cli_common import build_parent_parser, record_artifacts
from .apply_selection_helpers import (
    merge_validation_with_groups,
    resolve_priority_args,
)
from .consolidation import load_merged_suggestions
from .filtering import (
    filter_items,
    filter_user_skipped_groups,
    resolve_bulk_option_conflicts,
    should_bypass_no_selection_confirmation,
    validate_judge_decide_items_honored,
)
from .importance import get_highest_importance
from .judge_vocab import (
    JUDGE_AUTO_DECIDE,
    JUDGE_DECIDE,
    JUDGE_DECIDE_ITEM_IDS,
    canonical_value,
)
from .output_handler import derive_prefix, find_output_dir, get_phase_dir
from .provider_registry import set_run_anchor
from .report_parser import load_html_selections, merge_selections
from .state_manager import (
    CURRENT_FORMAT_VERSION,
    StateManager,
    generate_group_id,
    processed_record_counts,
)
from .text_clip import join_clauses
from .suggestion_batcher import (
    SuggestionBatch,
    estimate_batch_processing_stats,
    group_suggestions_for_subagents,
)
from .validation import (
    ERROR_TYPE_AMBIGUOUS,
    prepare_batched_revalidation_tasks,
    revalidate_failed_items,
    save_validation_results,
)
from .human_decisions import (
    apply_verdicts_to_work_set,
    build_judge_tasks,
    group_id_of,
    ingest_verdicts,
    judge_labels,
    native_judge_label,
    is_judge_source,
    judge_outcome,
    judge_source_label,
    judge_status_label,
    JUDGE_SKIPPED_STATUS,
    judge_item_from_group,
    record_verdicts,
    write_judge_tasks,
)
from . import unattended as _unattended
from .unattended import AGENT_DECIDE_FLAG, LEGACY_AGENT_DECIDE_FLAGS


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
        include_internal_revalidation: Add --internal-revalidation.
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
            "items, prior-changes log) and dispatch every batch again. The "
            "target file must already be back at its pre-run bytes (copy it "
            "from {phase}/backup.md, or roll the batches back with `util "
            "restore-batch`): a target still carrying the previous run's "
            "edits is refused (exit 3), since every batch would land twice. "
            "Earlier rollback points are kept aside, never overwritten."
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
        parser.add_argument(
            "--internal-revalidation",
            action="store_true",
            help="Run revalidation inside orchestrator (legacy mode) instead of delegating to Claude Code subagent",
        )

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

    And implement all 11 abstract methods (see the *Abstract methods*
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
    # and is NOT one of the paths ``_record_write_artifacts`` publishes; what it
    # publishes for a single-target phase is ``applied_to`` (the file itself).
    has_single_write_target: bool = True
    # Whether this phase's batches rewrite the PLAN itself. Only
    # apply-suggestions does; apply-task-suggestions edits the tasks file and
    # apply-code-fixes edits source. It gates exactly one thing — the
    # ``plan_hash`` re-stamp in the ``--mark-completed`` branch below — because
    # for a phase that never opens the plan, drift there is a HUMAN's edit and
    # clearing `plan_changed` would swallow the warning `implement --resume`
    # exists to print (F1, 2026-09-16). Cannot be derived from
    # ``write_phase_artifact()``: that early exit runs before `_load_inputs`
    # has resolved the tasks file.
    edits_the_plan: bool = False
    # Whether this phase applies a review's fixes to code, and so runs the
    # commit apply guard when state pins reviewed endpoints (`commit_range`, or
    # `head_ref` after a direct `--head-ref` review; plans/review-commits.md
    # §2.7). Only apply-code-fixes does: the other two phases edit the plan or
    # its task list, never code a commit review judged at `head`.
    guards_commit_fixes: bool = False

    # ------------------------------------------------------------------
    # Subclass validation
    # ------------------------------------------------------------------

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Validate that subclasses set all required config attributes."""
        super().__init_subclass__(**kwargs)

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
        # ran and matched anything (F7) — read by `_record_write_artifacts`.
        self._decisions_overlay_path: Optional[str] = None

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
        _unattended.record_resolution(None, site_id, decision)
        self._pending_resolutions.append((site_id, decision))

    def _loaded_groups_tally(self) -> str:
        """What row 11's "apply all valid items" covers, in counts.

        ``11 task suggestion group(s) loaded: 10 valid (applied), 1 invalid
        (left out)``. The record used to name only the loaded count — "11
        loaded task suggestion group(s)" beside a review that reported 10
        valid and 1 invalid (2026-10-05, Codex racing run 3) — which read as
        all eleven being applied. The statuses are the review's verdicts as
        loaded; a later override or the priority floor can still move a
        group, and the ``Filtered …`` block printed next states the final
        split.
        """
        counts: Dict[str, int] = {}
        for group in merge_validation_with_groups(
            self.groups, self.validation or []
        ):
            status = str(group.get("validation_status") or "needs-human-decision")
            counts[status] = counts.get(status, 0) + 1
        parts = [f"{counts.pop('valid', 0)} valid (applied)"]
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
        ``OrchestratorError`` for consistent exit codes.

        Returns:
            Process exit code (0 on success).
        """
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
            self._prepare_batches()
            return self._write_outputs()
        except OrchestratorError as e:
            self.logger.error("Orchestrator failed: %s", e)
            return e.exit_code
        except SystemExit as e:
            # Allow sys.exit() calls to propagate (used by early-exit paths)
            raise
        except Exception as e:
            self.logger.error(
                "Unexpected error in %s: %s",
                self.phase_name,
                e,
                exc_info=True,
            )
            return 1

    # ==================================================================
    # Phase 1 — _setup
    # ==================================================================

    def _batch_answers(self) -> List[str]:
        """The batches answered ``--human-task <batch>=skip``, checked (fix round 18).

        An apply phase takes only ``skip``, only on ``--resume`` and only on
        the ``--exec-subagents`` leg, whose own stop record the answer is
        checked against (``WriteBatchScheduler._check_partial_skips``). The
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
            # Fix round 19 (review of round 18): the refusal is the result
            # line's `error`, which the tool routes relay; it used to be on
            # stderr alone, and the line said it named no error.
            from .cli_common import record_error

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
        own lines never call a commit brief a plan (plans/review-commits.md
        §2.8), through the one owner of the word,
        ``commit_review.document_label``. Read-only; no state is a plan."""
        try:
            from .commit_review import document_label, read_commit_range

            word = document_label({"commit_range": read_commit_range(
                os.path.abspath(str(self.args.plan_file)))})
        except Exception:  # noqa: BLE001 - advisory: the plan's word stands
            return plan_word
        return plan_word if word == "plan" else word.capitalize()

    def _stop_user_commands(self) -> Dict[str, str]:
        """The stop's answer in this host's own spelling (fix round 18):
        ``skip``, the resume carrying ``--human-task {task_id}=skip``. Empty
        when nothing can be spelled; the stop then names the flags."""
        try:
            from . import detach as _detach
            from . import host_capabilities as _hosts
            from . import next_phase as _next

            host_id = _hosts.resolve_host_id(explicit=getattr(self.args, "host", None))
            route = _next.resolve_route(host_id)
            handle = _detach.active_run()
            plan_arg = (
                (handle.plan_arg if handle is not None else None)
                or os.environ.get(_detach.PLAN_ARG_ENV)
                or str(self.args.plan_file)
            )
            word = self.confirmation_phase_name or self.phase_name
            return {
                "skip": _next.phase_command(
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
            print(
                json.dumps(
                    {
                        "status": "skipped",
                        "message": f"{self.phase_name.capitalize()} phase skipped by user request",
                    }
                )
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
            # made (F1, 2026-09-16). Gated, because for the two phases that
            # never open the plan the same drift is a human's edit.
            if self.edits_the_plan:
                state.refresh_plan_hash()
            state.save()
            self.print_native_tests_not_run()
            # Fix round 26 (live run 11, OpenCode 05: "applied to
            # plans/racing-game.md" for edits to tasks/tasks.md): the native
            # leg's closing line names the file its batches edited, as the
            # executor's progress line does.
            target = self._completed_target_label()
            print(
                json.dumps(
                    {
                        "status": "completed",
                        "message": f"{self.phase_name} phase marked as completed"
                        + (f"; its batches edited {target}" if target else ""),
                    }
                )
            )
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

        # §9.3.a/b: the anchor capture point — absolute, before anything can
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

        # Step 6b (fix round 18): `--human-task <batch>=skip` answers a stopped
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

        # Step 10: Initialize StateManager + handle --fresh
        self.state = StateManager(Path(self.plan_path))

        # Step 10a: the reviewed endpoints, resolved strictly before anything
        # is written (`--fresh` below), any model runs or any batch is built:
        # a recorded SHA that no longer names a commit is exit 3
        # `[RANGE_UNRESOLVED]`, never a `HEAD~1` fallback (§2.4).
        self._resolve_pinned_endpoints()

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
                # Fix round 21: what the void run's batches reported about
                # their own checks is no earlier batch of this run.
                from .known_checks import APPLY_FIX_BATCH_CHECKS_KEY
                self.state.state.pop(APPLY_FIX_BATCH_CHECKS_KEY, None)
            self.state.save()
            # Clear prior changes history for a fresh start
            prior_changes_file = Path(self.out_dir) / "prior_changes.jsonl"
            if prior_changes_file.exists():
                prior_changes_file.unlink()
                print(
                    "[orchestrator] Cleared prior changes history.",
                    file=sys.stderr,
                )

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
                    message=(
                        "No user selections found in user_selections.json, "
                        "consolidated_user_selections.json, or report.md. "
                        "ALL valid items will be applied if you proceed. "
                        "To proceed, re-run with --no-confirm, --yes, or any bulk approval flag."
                    ),
                    item_count=len(self.groups),
                )
                print(json.dumps(output, indent=2))
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
        # the native leg, 2026-10-05; the scheduler on the executor leg since
        # fix round 22): one entry per member id of every batch recorded,
        # keyed by the id the batch's `expected_ids` carry — the group's
        # stamped `group_hash`, which is what the suggestion's `group_id` was
        # copied from. A `failed` record keeps the group in the work set (the
        # batch is dispatched again, as the executor leg re-dispatches a
        # failed batch), and so does a declined or skipped record of an
        # earlier review (fix round 22: a later review's re-report of an item
        # its batch did not apply is offered again, on both legs); every other
        # record drops it (`processed_record_counts`). On the
        # executor leg a record the executor wrote drops nothing: its resume
        # evidence is the result file on disk (`_done_evidence`), under the
        # batch's own id.
        if getattr(self.args, "resume", False) and self.state is not None:
            previous_decisions = self.state.get_all_human_decisions(self.phase_name)
            executor_leg = bool(self.write_kind) and bool(
                getattr(self.args, "exec_subagents", False)
                or getattr(self.args, "dry_run_subagents", False)
            )
            from .subagent_tasks import file_content_hash

            review_stamp = file_content_hash(
                os.path.join(self.out_dir, self.review_subdir, "grouped.json"))
            processed_items = {
                key: record
                for key, record in self.state.get_processed_items(self.phase_name).items()
                if processed_record_counts(
                    record, review_stamp=review_stamp, executor_leg=executor_leg)
            }

            for group in self.merged:
                group["_group_id"] = generate_group_id(group)

            def _recorded_done(group: Dict[str, Any]) -> bool:
                return any(
                    str(key or "") in processed_items
                    for key in (group.get("_group_id"), group.get("group_hash"))
                )

            unprocessed_merged = []
            for g in self.merged:
                gid = g["_group_id"]
                if _recorded_done(g):
                    continue
                if gid in previous_decisions:
                    decision = previous_decisions[gid]
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
            # on a resume that then kept batch 0 (OpenCode racing run 4), so
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
                    f"Phase _apply_user_feedback, step 25: --approve-all blocked by HIGH importance items",
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

        # Step 25a: the commit apply guard (plans/review-commits.md §2.7), on
        # what filtering left to apply or decide, before the no-items exit,
        # human decisions and batching, so both legs take the same decision
        # and a run whose fixes it skips entirely still prints its block.
        self._apply_commit_guard()

        print(f"\nFiltered {self.item_noun_plural}:", file=sys.stderr)
        print(f"  Valid (to apply): {len(self.valid)}", file=sys.stderr)
        print(f"  Needs human review: {len(self.needs_human)}", file=sys.stderr)
        print(f"  Skipped: {len(self.skipped)}", file=sys.stderr)

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
                # The commit guard's skip (§2.7): the plugin's, decided before
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
    # The commit apply guard (plans/review-commits.md §2.5, §2.7)
    # ==================================================================

    def _refuse_unusable_state(self) -> None:
        """Exit 3, before anything is written, when the guard cannot be
        keyed (plans/review-commits.md §2.7, "The guard is keyed on the
        endpoints state pins").

        ``StateManager`` replaces a ``state.json`` that does not parse with
        a fresh initial state, so the apply would run with no guard, against
        ``head_at_start`` rather than the reviewed base, and its first save
        would overwrite the file. So, on apply-code-fixes only
        (:attr:`guards_commit_fixes`):

        - a ``state.json`` that exists but does not parse, or holds no JSON
          object, is refused for any plan;
        - a commit brief (``commit_review.is_commit_brief``) whose state is
          missing or pins no endpoints is refused.

        The file is only read here, never written. The front door's own
        step-6 load may still replace an unparseable state (§2.1): by then a
        review is recorded afresh, and its apply refuses an unreadable state
        first (``commit_apply.require_completed_review``).
        """
        if not self.guards_commit_fixes:
            return
        from .commit_range import SLUG_PATTERN, pinned_endpoints, pinned_spelling
        from .commit_review import is_commit_brief
        from .output_handler import output_dir_path

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
        from .cli_common import record_error

        record_error(message)
        raise OrchestratorError(
            f"Phase _setup, step 3a: {state_file} cannot be used: {problem}",
            exit_code=3,
        )

    def _resolve_pinned_endpoints(self) -> None:
        """Resolve the endpoints state pins, strictly, once (§2.4).

        Keyed on ``commit_range.pinned_endpoints``: ``commit_range`` (a
        commit brief) or ``head_ref`` (a plan after a direct ``--head-ref``
        review). A recorded SHA that no longer names a commit is exit 3
        ``[RANGE_UNRESOLVED]`` naming the recovery, before the guard or any
        batch, so no fix prompt is ever written against ``HEAD~1``. A run
        whose state pins nothing is left exactly as it was.
        """
        if not self.guards_commit_fixes or self.state is None:
            return
        from .commit_range import RangeError, pinned_endpoints, pinned_record, resolve_recorded
        from .git_utils import get_project_root_from_dir, git_path

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
            from .cli_common import record_error

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
        """Take the §2.7 guard decision over what filtering left, and print
        ``[COMMIT_FIXES]``.

        Every group it skips (the context plan, a fix file changed since the
        reviewed ``head``, a protected path) moves from ``valid`` /
        ``needs_human`` to ``skipped``, before human decisions and batching,
        so the judge never sees it and no batch carries it. The decision is
        saved to the pinned record's ``guard`` through this phase's own
        ``StateManager`` (the one it saves with, §2.1), under
        ``state_file_lock``. The block is printed once, here, and the result
        line carries ``commit_fixes``. Not on a ``--detach`` launcher, whose
        worker takes the decision (and prints the block into its log); both
        dry runs decide and print but write nothing.
        """
        if self._pinned is None or self.state is None or self._is_detach_invoker():
            return
        from .cli_common import record_commit_fixes_result
        from .commit_apply import GUARD_SKIP_STATUS, skip_reason, take_guard
        from .commit_range import pinned_record
        from .human_decisions import group_id_of

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
                from .metrics import state_file_lock

                with state_file_lock(self.state.state_file):
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
        batch as it landed (plans/review-commits.md §2.8).
        """
        if self.state is None:
            return set()
        from .subagent_tasks import file_content_hash

        review_stamp = file_content_hash(
            os.path.join(self.out_dir, self.review_subdir, "grouped.json"))
        return {
            str(key)
            for key, record in self.state.get_processed_items(self.phase_name).items()
            if processed_record_counts(record, review_stamp=review_stamp)
        }

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
        # files read at `head`, all of it data under review (§2.6 "Trust
        # boundary"): its task says so. Absent otherwise, so a plan's run keeps
        # its prompt byte for byte.
        trust_note: Optional[str] = None
        if self._pinned is not None:
            from .commit_range import DATA_UNDER_REVIEW

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
        from .review_orchestrator_base import dispatch_subagent_tasks

        if not dispatch_subagent_tasks(
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
                )
                judges.update(judge_labels(
                    phase_dir,
                    {gid: path for gid, path in ingest.sources.items()
                     if gid in dispatched},
                    fallback="executor (runner unrecorded)",
                ))
            else:
                fallback_judge = native_judge_label(self._host_id())
                judges = judge_labels(
                    phase_dir, ingest.sources, fallback=fallback_judge
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
                    summary_path = self.write_apply_summary_report()
                    self._decisions_overlay_path = self.regenerate_decisions_overlay()
                    if summary_path:
                        # F11: the scheduler already serialized
                        # write_batch_report.json with summary_file: null by
                        # this point — patch it now that the path is known.
                        self._patch_write_batch_report_summary_file(summary_path)
                except Exception as e:  # noqa: BLE001 - reporting is non-fatal
                    self.logger.warning("summary report failed: %s", e)
            self._record_write_artifacts(output_path)
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
                as_json = getattr(self.args, "output_format", "text") == "json"
                if not dispatched or as_json:
                    self.print_text_summary(self.batches, output_path)
                if dispatched:
                    # On stderr when the payload above claimed stdout: a
                    # contract with a human-readable block printed after it is
                    # not a contract, and a consumer that parses stdout as JSON
                    # gets the outcome block in its teeth. It is still printed —
                    # to the stream the scheduler's own progress lines already
                    # use, which is the same log either way under `--detach`.
                    with contextlib.redirect_stdout(
                        sys.stderr if as_json else sys.stdout
                    ):
                        self.print_write_outcome_summary()
                    self._publish_run_notes()
            except Exception as e:  # noqa: BLE001 - summary is non-fatal
                self.logger.warning("write outcome summary failed: %s", e)
            return scheduled

        # The native leg (2026-10-05): the same materialized task file the
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

        # The native leg: the batches are now the host's to apply, so the phase
        # is recorded *started*, never completed — completion is the host's
        # post-loop `--mark-completed`, the only place the native path records
        # it (the word it persists is the same `confirmation_phase_name or
        # phase_name`). Until 2026-10-05 apply-suggestions marked itself
        # completed right here, before a single edit existed, so `status`
        # and the next-step builder read a phase as done while the host was
        # still applying its batches — or after it had died halfway.
        if self.state is not None:
            word = self.confirmation_phase_name or self.phase_name
            if not self.batches and not self.needs_human:
                # Nothing handed out and nothing left to decide (every item
                # invalid or skipped): the phase's work is done at emit, so
                # the record says so — a started record here would wait for
                # a closing step over an empty loop.
                self.state.mark_phase_completed(word)
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
            self.print_text_summary(self.batches, output_path)
        except Exception as e:
            # Non-fatal: log but don't fail
            self.logger.warning(
                "print_text_summary failed: %s", e, exc_info=True
            )

        self.logger.info("Output written to %s", output_path)

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
            return None
        from .review_orchestrator_base import maybe_detach

        phase_dir = os.path.join(self.out_dir, self.phase_name)
        os.makedirs(phase_dir, exist_ok=True)
        mode = self.confirmation_phase_name or self.phase_name
        return maybe_detach(
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
        own records dates against: the review is
        ``REVIEW_PHASE_BY_WRITE_KIND``'s entry for this write kind (the
        scheduler's ``_review_completed_at`` reads the same one), and its
        stamp is read with the scheduler's ``_parse_local_timestamp``.
        ``None`` for a phase with no write kind, before ``_setup`` built the
        state, or when the review has no parseable completion — and every
        caller then keeps what it was dating (absence of a date is not
        staleness).
        """
        from .write_batch_scheduler import (
            REVIEW_PHASE_BY_WRITE_KIND, _parse_local_timestamp,
        )
        recorded_state = getattr(getattr(self, "state", None), "state", None)
        if not isinstance(recorded_state, dict):
            return None
        completed = recorded_state.get("phases_completed")
        review = REVIEW_PHASE_BY_WRITE_KIND.get(getattr(self, "write_kind", "") or "")
        if not isinstance(completed, dict) or not review:
            return None
        return _parse_local_timestamp(completed.get(review))

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
        from .write_safety import (
            AuditLog, file_sha256, relative_to_root, resolve_repo_root,
        )
        from .write_batch_scheduler import _parse_local_timestamp
        records = AuditLog(phase_dir).records()
        if not records:
            return None
        current = file_sha256(target)
        if not current:
            return None
        try:
            root = resolve_repo_root(self.plan_path)
            target_key = relative_to_root(target, root)
        except Exception:  # noqa: BLE001 - fall back to matching by hash alone
            target_key = None
        reviewed_at = self._review_completed_at()
        if reviewed_at is not None:
            # The audit stamps whole seconds; a completion in the review's
            # own second is this cycle's.
            reviewed_at = reviewed_at.replace(microsecond=0)
        hits: List[Tuple[str, str]] = []
        for record in records:
            if record.get("event") != "completed":
                continue
            if reviewed_at is not None:
                stamped = _parse_local_timestamp(record.get("timestamp"))
                if stamped is not None and stamped < reviewed_at:
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
        backup = os.path.join(phase_dir, "backup.md")
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
        from .write_safety import file_sha256
        kept_sha = file_sha256(backup_path)
        if not kept_sha or kept_sha == file_sha256(target):
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
        backup_path = os.path.join(phase_dir, "backup.md")
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
        scheduler's ``_earlier_report_rows`` compares: a processed record by
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
        from .subagent_executor import OUTPUT_NAME_PATTERN_BY_KIND
        from .write_batch_scheduler import (
            WRITE_BATCH_REPORT_FILENAME, _parse_local_timestamp,
        )

        reviewed_at = self._review_completed_at()

        def this_cycle(stamped: Optional[datetime]) -> bool:
            return stamped is None or reviewed_at is None or not stamped < reviewed_at

        def modified_at(path: str) -> Optional[datetime]:
            try:
                return datetime.fromtimestamp(os.stat(path).st_mtime)
            except OSError:
                return None

        if self.state is not None:
            for record in self.state.get_processed_items(self.phase_name).values():
                stamped = (
                    _parse_local_timestamp(record.get("timestamp"))
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
            written_at = (
                _parse_local_timestamp(report.get("written_at"))
                if isinstance(report, dict) else None
            )
            if this_cycle(written_at or modified_at(report_path)):
                return True
        # The kind's own result pattern, never a glob typed here: it is the same
        # table the executor admits a result filename against, so a new write
        # kind cannot leave this check silently blind.
        pattern = OUTPUT_NAME_PATTERN_BY_KIND.get(self.write_kind)
        return pattern is not None and any(
            pattern.match(name) and this_cycle(modified_at(os.path.join(phase_dir, name)))
            for name in names
        )

    def _touched_files(self) -> List[str]:
        """The files the write batches actually verified changed (F7).

        The observed post-run byte comparison, not the runner's own claim — the
        same set each applied or partially applied outcome's ``files_touched``
        carries. Partial application stops the run but preserves its edits,
        so those files must remain visible for inspection. Repo-root-
        relative, order-preserving, de-duplicated across every outcome; empty
        before the write executor has run, or when every batch was a no-op /
        clean failure. This is the only "what did this phase change" answer for
        a phase with no single write target (``has_single_write_target`` False —
        apply-code-fixes partitions by ``file_key``), and it is honest for the
        single-target phases too since it reflects what actually moved rather
        than the phase's own convention.

        Read from :meth:`_phase_rows`, so a ``--resume`` still names the files
        an earlier run of this phase changed.
        """
        touched: List[str] = []
        seen: Set[str] = set()
        for row in self._phase_rows():
            if not self._row_ok(row) and (
                row.get("write_outcome") != "partial-application"
            ):
                continue
            for touched_path in row.get("files_touched") or []:
                if touched_path and touched_path not in seen:
                    seen.add(touched_path)
                    touched.append(touched_path)
        return touched

    def _phase_rows(self) -> List[Dict[str, Any]]:
        """Every batch row of this phase, earlier runs' first (#28).

        The scheduler's own ``report_rows()``, the rows
        ``write_batch_report.json`` carries, so ``summary.md``, the result
        block and the report cannot disagree. On a ``--resume`` they include
        the rows an interrupted run of this review cycle recorded, flagged
        ``from_earlier_run``, and never rows of an earlier cycle (the
        scheduler drops a report that predates the review). Built from this
        run's outcomes when the result has no rows of its own.
        """
        result = self.write_result
        report_rows = getattr(result, "report_rows", None)
        if callable(report_rows):
            return [dict(row) for row in report_rows()]
        rows: List[Dict[str, Any]] = []
        for outcome in getattr(result, "outcomes", None) or []:
            rows.append({
                "task_id": str(getattr(outcome, "task_id", "")),
                "status": getattr(outcome, "status", None),
                "write_outcome": getattr(outcome, "write_outcome", None),
                "runner": getattr(outcome, "runner", None),
                "duration_seconds": getattr(outcome, "duration_seconds", 0.0),
                "reason": getattr(outcome, "reason", None),
                "files_touched": list(getattr(outcome, "files_touched", None) or []),
                "output_path": getattr(outcome, "output_path", None),
                "expected_ids": list(getattr(outcome, "expected_ids", None) or []),
                "skipped": bool(getattr(outcome, "skipped", False)),
                **(
                    {"batch_check": {
                        "passed": not outcome.batch_check,
                        "findings": list(outcome.batch_check),
                    }}
                    if getattr(outcome, "batch_check", None) is not None else {}
                ),
            })
        return rows

    @staticmethod
    def _row_ok(row: Dict[str, Any]) -> bool:
        return row.get("status") == "ok"

    def _row_item_ids(self, row: Dict[str, Any]) -> List[str]:
        """The items a row's batch carried: the row's own ``expected_ids``,
        else this run's materialized task of the same id."""
        own = row.get("expected_ids")
        if own:
            return [str(item) for item in own]
        for task in self.write_tasks:
            if str(task.get("task_id", "")) == str(row.get("task_id", "")):
                return [str(item) for item in task.get("expected_ids") or []]
        return []

    @staticmethod
    def _row_provenance(row: Dict[str, Any]) -> str:
        """The marker a row from before this run carries, else ``""``."""
        if row.get("from_earlier_run"):
            return " (earlier run)"
        if row.get("skipped"):
            # A resume skip whose earlier row the scheduler could not supply
            # (that run left no report, or its report belonged to an earlier
            # review): this run reused the result file and dispatched nothing.
            return " (earlier result, not dispatched again)"
        return ""

    def _rows_provenance_note(self, rows: List[Dict[str, Any]]) -> str:
        """`` (N from an earlier run of this phase, …)`` for a count line."""
        earlier = sum(1 for row in rows if row.get("from_earlier_run"))
        reused = sum(
            1 for row in rows
            if row.get("skipped") and not row.get("from_earlier_run")
        )
        parts = []
        if earlier:
            parts.append(f"{earlier} from an earlier run of this phase")
        if reused:
            parts.append(f"{reused} earlier result(s) reused")
        if not parts:
            return ""
        return f" ({', '.join(parts)}, not dispatched again)"

    def _items_by_member_id(self) -> Dict[str, Dict[str, Any]]:
        """``member id -> formatted item`` over this run's batches.

        Each materialized task's ``expected_ids`` are its batch's items in
        order (``write_phase_bridge``), so an earlier run's row, whose
        positional id may now name another batch, still finds its own items.
        """
        items: Dict[str, Dict[str, Any]] = {}
        for task, batch in zip(self.write_tasks, self.batches):
            if not isinstance(batch, dict):
                continue
            members = self._batch_member_items(batch)
            for member_id, item in zip(task.get("expected_ids") or [], members):
                items.setdefault(str(member_id), item)
        return items

    def _record_write_artifacts(self, output_path: str) -> None:
        """Hand back the files this phase produced, on the executor leg.

        A fully successful detached run reported ``artifacts: []`` and no
        ``output_files``: the phase that rewrote the plan never named the plan,
        its own output JSON, its batch report or the prior-changes log, so the
        host was left to glob a phase dir or mine a log it cannot see. Same two
        channels the review base writes — ``record_output_files`` feeds
        ``.status.json`` for ``status``, ``record_artifacts`` feeds the terminal
        ``MULTI_LLM_RESULT`` line every host is told to trust — and both drop
        paths that do not exist, so a stopped run names only what it produced.

        F7: also names every file the batches verified changed
        (``touched_file_{n}``, resolved against the same
        ``write_safety.resolve_repo_root`` anchor the scheduler pins the write
        path to — mirrors ``implement_orchestrator._record_implement_write_
        artifacts``), plus the judge's own dispatch report and the review report
        this run's decisions overlay rewrote, when either exists.
        """
        phase_dir = os.path.join(self.out_dir, self.phase_name)
        paths: Dict[str, str] = {}
        target = self.write_target_file()
        if target:
            paths["applied_to"] = target
        paths["orchestrator_output"] = output_path
        report_path = getattr(self.write_result, "report_path", None)
        paths["write_batch_report"] = report_path or os.path.join(
            phase_dir, "write_batch_report.json"
        )
        paths["prior_changes"] = os.path.join(self.out_dir, "prior_changes.jsonl")
        # The summary report this leg writes itself (F3). Dropped like every
        # other path when absent, so `--dry-run-subagents` names no report.
        paths["summary"] = os.path.join(phase_dir, "summary.md")

        try:
            from .write_safety import repo_root_for_report
        except ImportError:  # pragma: no cover - direct script runs
            from write_safety import repo_root_for_report  # type: ignore

        repo_root = repo_root_for_report(self.plan_path)
        for index, touched_path in enumerate(self._touched_files(), start=1):
            resolved = (
                touched_path if os.path.isabs(touched_path)
                else os.path.join(repo_root, touched_path)
            )
            paths[f"touched_file_{index}"] = resolved

        # The judge's own dispatch report, kind-qualified because a judge
        # dispatch can share this phase dir with the later write dispatch
        # (KINDS_SHARING_A_WRITE_PHASE_DIR) — otherwise invisible to a host
        # that only reads this run's `output_files`. Asked of the executor
        # rather than spelled out here (F6, 2026-09-17): it owns the naming
        # rule, and a hand-typed copy would drop this key on the day it moves.
        try:
            from .subagent_executor import batch_report_path
        except ImportError:  # pragma: no cover - direct script runs
            from subagent_executor import batch_report_path  # type: ignore

        judge_report = batch_report_path(phase_dir, "human_decision_judge")
        if os.path.exists(judge_report):
            paths["human_decision_judge_report"] = judge_report

        # The review report this phase's own decisions overlay just rewrote,
        # if any (`regenerate_decisions_overlay`, called just before this).
        overlay_path = getattr(self, "_decisions_overlay_path", None)
        if overlay_path:
            paths["decisions_overlay"] = overlay_path

        try:
            from . import detach as _detach
        except ImportError:  # pragma: no cover - direct script runs
            import detach as _detach  # type: ignore
        _detach.record_output_files(phase_dir, **paths)
        record_artifacts(
            path for path in paths.values() if path and os.path.exists(path)
        )

    def _write_item_counts(self, rows: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count items by the scheduler's verdict, rather than dispatch success.

        An ``ok`` dispatch may be a no-op or a clean failure. Neither is
        evidence that its requested changes were applied. Counted over
        :meth:`_phase_rows`, the rows the report lists, so the count lines
        agree with the table under them.
        """
        counts = {
            "applied": 0, "no-op": 0, "clean-failure": 0,
            "declined": 0, "skipped": 0,
        }
        for row in rows:
            verdict = row.get("write_outcome")
            if self._row_ok(row) and verdict in counts:
                # Fix round 18: an item its batch declined, or one skipped at
                # the user's request, is never counted under the batch's
                # verdict (an `applied` batch did not apply it).
                declined, skipped = self._row_not_applied(row)
                counts[verdict] += len([
                    item for item in self._row_item_ids(row)
                    if item not in declined and item not in skipped
                ])
                counts["declined"] += len(declined)
                counts["skipped"] += len(skipped)
        return counts

    def _not_applied_lines(self, rows: List[Dict[str, Any]]) -> List[str]:
        """One plain line per item a finished batch did not apply on purpose
        (fix round 18): ``<title> [<id8>] (fix 2 of apply-fix-batch-1) not
        applied: the batch declined it — <reason>``, and the same for an item
        skipped at the user's request. Over the finished (``ok``) rows only:
        a stopped batch is dispatched again."""
        word = "fix" if self.write_kind == "apply_code_fixes" else "suggestion"
        lines: List[str] = []
        for row in rows:
            if not self._row_ok(row):
                continue
            declined, skipped = self._row_not_applied(row)
            if not declined and not skipped:
                continue
            item_ids = self._row_item_ids(row)
            titles = {
                member: str(item.get("title") or item.get("theme") or "").strip()
                for member, item in self._row_items_with_ids(row, item_ids)
                if member
            }
            for member in item_ids:
                # Fix round 26: the record keeps the reason's closing stop.
                # Fix round 28 (live run 12 #7): so does this line, which
                # ends with it; the notice's join (`join_clauses`) drops it
                # only where another clause follows (OpenCode decline's
                # notice lost it as its last clause).
                if member in declined:
                    why = f"the batch declined it — {str(declined[member] or '').strip()}"
                elif member in skipped:
                    why = f"skipped at your request — {str(skipped[member] or '').strip()}"
                else:
                    continue
                title = titles.get(member) or "Untitled"
                lines.append(
                    f"{title} [{member[:8]}] ({word} {item_ids.index(member) + 1} "
                    f"of {row.get('task_id')}) not applied: {why}"
                )
        return lines

    def print_write_outcome_summary(self) -> None:
        """Report what the batch loop DID, plus the decision summary.

        Two gaps close here. The first is tense: the log's 12 KB tail described
        batches that had already run, and carried no outcome, duration or runner
        anywhere in it. The second is reach: ``util decisions`` (step 3 of the
        apply instructions) is the only surface for the applied/skipped
        breakdown, and on the ``--exec-subagents`` leg the phase finishes in one
        invocation, so that step never runs — the per-item reasons, which are the
        good part, existed only inside ``orchestrator_output.json``.
        """
        from .subagent_executor import batch_check_could_not_run, row_batch_check_findings

        result = self.write_result
        rows = self._phase_rows()
        ok = [row for row in rows if self._row_ok(row)]
        item_counts = self._write_item_counts(rows)
        target = self.write_target_file()
        touched = self._touched_files()

        print(f"\n{'=' * 60}")
        print(f"{self.phase_name.upper()}: RESULT")
        print(f"{'=' * 60}")
        # F7: a phase with no single write target (has_single_write_target False —
        # apply-code-fixes partitions by file_key) used to fall back to
        # `self.plan_path` here, which the phase never opens, so every run named
        # the plan as what it changed. The files the batches actually verified
        # changed are the honest answer, and they exist for every phase.
        if target:
            print(f"File: {target}")
        else:
            print(f"Files changed: {', '.join(touched) if touched else '(none)'}")
        print(
            f"Batches: {len(ok)}/{len(rows)} ok"
            + self._rows_provenance_note(rows)
        )
        print(f"{self.item_noun_plural.capitalize()} applied: {item_counts['applied']}")
        if item_counts["declined"]:
            print(
                f"{self.item_noun_plural.capitalize()} declined by their batch "
                f"(not applied): {item_counts['declined']}"
            )
        if item_counts["skipped"]:
            print(
                f"{self.item_noun_plural.capitalize()} skipped at your request "
                f"(not applied): {item_counts['skipped']}"
            )
        if item_counts["no-op"]:
            print(f"{self.item_noun_plural.capitalize()} needing no changes: {item_counts['no-op']}")
        if item_counts["clean-failure"]:
            print(f"{self.item_noun_plural.capitalize()} without verified changes: {item_counts['clean-failure']}")
        print(f"Skipped: {len(self.formatted_skipped)}")
        if getattr(result, "stopped_at_batch", None) is not None:
            print(f"Stopped at batch: {result.stopped_at_batch}")
        failing = {
            str(row.get("task_id")): row_batch_check_findings(row)
            for row in rows
            if self._row_ok(row) and row_batch_check_findings(row)
        }
        if failing:
            # Fix round 14: applied, but not a clean finish.
            from .write_batch_scheduler import batch_check_summary

            print(f"Not a clean finish: {batch_check_summary(failing)}")
        if getattr(result, "unverified", None):
            print(result.unverified)

        if rows:
            print("\nBatches:")
            for row in rows:
                count = len(self._row_item_ids(row))
                # `subagent_executor.row_outcome_label`'s reading order.
                verdict = row.get("outcome_label") or row.get("write_outcome") or "-"
                if self._row_ok(row) and row_batch_check_findings(row):
                    verdict += (
                        ", its check could not run"
                        if batch_check_could_not_run(row_batch_check_findings(row))
                        else ", its check fails"
                    )
                print(
                    f"  {row.get('task_id')}{self._row_provenance(row)}: "
                    f"{row.get('status')} ({verdict}), "
                    f"{count} {self.item_noun}(s), "
                    f"{float(row.get('duration_seconds') or 0.0):.1f}s, "
                    f"runner {row.get('runner') or '(none)'}"
                )
                reason = row.get("reason")
                if reason:
                    print(f"      reason: {reason}")
            not_applied = self._not_applied_lines(rows)
            if not_applied:
                print(f"\n{self.item_noun_plural.capitalize()} not applied:")
                for line in not_applied:
                    print(f"  - {line}")

        for warning in self.consistency_warnings():
            print(f"\n[CONSISTENCY_WARNING] {warning}")

        # The decision summary, folded in: every skip with the status and the
        # specific reason validation gave it, plus its group id so the skip can
        # be looked up in the review report.
        if self.formatted_skipped:
            print(f"\nSkipped {self.item_noun_plural} (not applied):")
            for item in self.formatted_skipped:
                gid = str(item.get("group_id") or "")
                label = f" [{gid[:8]}]" if gid else ""
                print(
                    f"  - [{judge_status_label(item.get('status'))}] "
                    f"{item.get('title', 'Unknown')}{label}"
                )
                if item.get("reason"):
                    print(f"      reason: {item['reason']}")
        # What the judge decided, on the leg where nothing else reports it. The
        # instructions put a `## Decided by the judge agent` section in the summary
        # report, but that step lives on the native leg only, so before
        # this the one decision a `--yes --exec-subagents` run actually *made*
        # reached no output the phase wrote (measured 2026-09-16).
        decided = self.judge_decisions()
        if decided:
            print(f"\nDecided by the judge agent ({len(decided)}):")
            print(f"  judge: {', '.join(self._judges_of(decided))}")
            titles = self._titles_by_group_id()
            for group_id, record in decided.items():
                title = titles.get(group_id, group_id)
                context = record.get("batch_context") or {}
                print(
                    f"  - [{judge_outcome(record)}] {title} "
                    f"[{group_id[:8]}]"
                )
                print(f"      source: {judge_source_label(context.get('decision_source'))}")
                if record.get("reason"):
                    print(f"      reason: {record['reason']}")

        if self.formatted_human:
            print(f"\nStill needing a human ({len(self.formatted_human)}):")
            for item in self.formatted_human:
                print(f"  - {item.get('title', 'Unknown')}")

    # ------------------------------------------------------------------
    # The executor leg's own summary report and decisions overlay (F3)
    # ------------------------------------------------------------------

    def run_notes(self) -> List[str]:
        """The lines a host must relay beside this run's counts (fix round 14).

        Codex racing re-run 5, apply-task-suggestions: the log carried
        ``[CONSISTENCY_WARNING] T003 depends on T004, listed after it`` and
        "Skipped: 1" (a suggestion the judge skipped), while the result the
        host read said "10/10 items applied" and nothing else, so the host
        reported "Applied 10 of 10". One line per consistency warning, and one
        naming every item left unapplied with why, its title and group id —
        the RESULT block's own facts, in plain words.
        """
        notes = [
            f"consistency warning: {warning}" for warning in self.consistency_warnings()
        ]
        # Fix round 18: an item a batch declined (or one skipped at the
        # user's request) is named with its reason, never only counted.
        notes.extend(self._not_applied_lines(self._phase_rows()))
        skipped = list(self.formatted_skipped or [])
        if skipped:
            applied = self._write_item_counts(self._phase_rows())["applied"]
            noun = self.item_noun if len(skipped) == 1 else self.item_noun_plural
            by_label: Dict[str, List[str]] = {}
            for item in skipped:
                gid = str(item.get("group_id") or "")
                title = str(item.get("title") or "Unknown").strip()
                by_label.setdefault(judge_status_label(item.get("status")), []).append(
                    f"{title}{f' [{gid[:8]}]' if gid else ''}"
                )
            shown = "; ".join(
                f"{label}: {', '.join(titles[:5])}"
                + (f" (+{len(titles) - 5} more)" if len(titles) > 5 else "")
                for label, titles in by_label.items()
            )
            # Fix round 26 (live run 11, OpenCode 05: the host said the task
            # suggestions went "to plans/racing-game.md"): the file they went to.
            target = self._applied_to_label()
            notes.append(
                f"{len(skipped)} {noun} not applied, beside the {applied} "
                f"applied{f' to {target}' if target else ''} — {shown} "
                "(reasons in summary.md)"
            )
        return notes

    def _completed_target_label(self) -> Optional[str]:
        """:meth:`_applied_to_label` for the native ``--mark-completed``
        call, which runs before any setup hook (fix round 26)."""
        return self._applied_to_label()

    def _applied_to_label(self) -> Optional[str]:
        """The single file this phase edits, relative to the repository
        root (``write_target_file``), or ``None`` without one."""
        target = self.write_target_file()
        if not target:
            return None
        try:
            from .git_utils import find_git_entry_root
        except ImportError:  # pragma: no cover - direct script runs
            from git_utils import find_git_entry_root  # type: ignore
        try:
            # The `.git` holder above the plan, walked (no git runs here).
            start = os.path.dirname(os.path.realpath(self.plan_path))
            root = os.path.realpath(find_git_entry_root(start) or start)
            relative = os.path.relpath(os.path.realpath(target), root)
        except (OSError, ValueError):
            return target
        # A label in prose and in the result line: `/` on every platform.
        return target if relative.startswith(os.pardir) else relative.replace(os.sep, "/")

    def _publish_run_notes(self) -> None:
        """Hand :meth:`run_notes` to the result line and to ``status``.

        The run's own ``notice`` (appended, never replacing one) for a
        foreground caller, and ``progress.notes`` in the phase's
        ``.status.json``, which a detached run's terminal poll carries into
        its ``notice`` — the poll is the only result line a tool route reads.
        """
        notes = self.run_notes()
        if not notes:
            return
        from . import cli_common as _cli

        try:
            from . import detach as _detach
        except ImportError:  # pragma: no cover - direct script runs
            import detach as _detach  # type: ignore
        _detach.report_progress(
            os.path.join(self.out_dir, self.phase_name), notes=notes,
        )
        _cli.add_notice(join_clauses(notes))

    def consistency_warnings(self) -> List[str]:
        """Problems the finished edits left in the file they edited (advisory).

        Nothing by default. A phase whose artifact is a graph overrides it
        (apply-task-suggestions re-checks ``tasks.md``), because its batches
        each edit one corner of that graph and none of them sees the whole.
        """
        return []

    def judge_decisions(self) -> Dict[str, Dict[str, Any]]:
        """This phase's recorded decisions that a judge subagent made.

        The same filter the instructions' ``## Decided by the judge agent`` section
        specifies: ``human_decisions_{phase}`` entries whose
        ``batch_context.decision_source`` is ``judge_auto_decide`` or
        ``judge_auto_decide_salvage`` (or the ``claude_*`` spelling of either
        that a run started before the rename recorded).
        """
        if self.state is None:
            return {}
        try:
            recorded = self.state.get_all_human_decisions(self.phase_name)
        except Exception:  # noqa: BLE001 - reporting must not fail a run
            return {}
        return {
            group_id: record
            for group_id, record in (recorded or {}).items()
            if is_judge_source(
                ((record or {}).get("batch_context") or {}).get("decision_source")
            )
        }

    @staticmethod
    def _judge_breakdown(decided: Dict[str, Dict[str, Any]]) -> str:
        """`` (N approved, N salvaged, N skipped)`` for the summary's count line.

        The same three counts the ingest line prints, so one run never reports
        a salvage as "salvaged" in one place and "approved" in another.
        """
        if not decided:
            return ""
        outcomes = [judge_outcome(record) for record in decided.values()]
        return (
            f" ({outcomes.count('approved')} approved, "
            f"{outcomes.count('salvaged')} salvaged, "
            f"{outcomes.count('skipped')} skipped)"
        )

    @staticmethod
    def _judges_of(decided: Dict[str, Dict[str, Any]]) -> List[str]:
        """The distinct judges named by *decided*'s records, in first-seen order."""
        judges: List[str] = []
        for record in decided.values():
            judge = str(((record or {}).get("batch_context") or {}).get("judge")
                        or "unrecorded")
            if judge not in judges:
                judges.append(judge)
        return judges

    def _titles_by_group_id(self) -> Dict[str, str]:
        """``group_id -> title`` over every work set, for decision reporting."""
        titles: Dict[str, str] = {}
        for formatted in (
            self.formatted_valid,
            self.formatted_human,
            self.formatted_skipped,
        ):
            for item in formatted or []:
                gid = str(item.get("group_id") or "")
                if gid:
                    titles[gid] = str(item.get("title") or gid)
        return titles

    @staticmethod
    def _batch_member_items(batch: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """The formatted items a batch dict carries (F10).

        ``fixes`` for a ``CodeFixBatch``, ``suggestions`` for the two sibling
        phases' ``SuggestionBatch`` — whichever key the batch's own
        ``to_dict()`` used, so this reads all three phases' batches without a
        subclass override.
        """
        if not batch:
            return []
        return list(batch.get("fixes") or batch.get("suggestions") or [])

    @staticmethod
    def _read_batch_result_notes(
        output_path: Optional[str], item_ids: Optional[List[str]] = None
    ) -> Optional[str]:
        """Best-effort read of a write batch's own ``notes`` field (F10).

        ``notes`` (``schemas/write_batch_result.schema.json``) is the runner's
        free-text detail beyond the structured ``status``/``ids``/``summary``
        fields ``TaskOutcome`` already carries — on a real run, the only place a
        batch's own account of *why* (e.g. "Fix 1: car.accel 32->28 per plan
        §8.") survives past verification. Silent on any read/parse failure —
        the field is optional and this is reporting, never gating.

        With ``item_ids``, a file whose own ``ids`` name none of them is
        another batch's: an apply result file is named by position, and a
        resumed run may have rewritten it for the batch that now holds it.
        """
        if not output_path or not os.path.isfile(output_path):
            return None
        try:
            with open(output_path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError):
            return None
        if not isinstance(data, dict):
            return None
        returned = [str(i) for i in data.get("ids") or []]
        if item_ids and returned and not set(returned) & set(item_ids):
            return None
        notes = data.get("notes")
        return notes if isinstance(notes, str) and notes.strip() else None

    def _row_items(
        self, row: Dict[str, Any], item_ids: List[str]
    ) -> List[Dict[str, Any]]:
        """The formatted items (titles, files) a report row's batch carried.

        This run's batch of the same id when it holds the same items — task
        and batch are materialized from the same ``self.batches`` list, in the
        same order (``run_write_executor``), so a positional zip joins them —
        else the items found by member id: an earlier run's row whose
        positional id now names another batch.
        """
        return [item for _member, item in self._row_items_with_ids(row, item_ids)]

    def _row_items_with_ids(
        self, row: Dict[str, Any], item_ids: List[str]
    ) -> List[Tuple[Optional[str], Dict[str, Any]]]:
        """:meth:`_row_items` with each item's own id beside it (fix round 18:
        a declined item is named by its id on the row). ``None`` for an item
        whose id cannot be told."""
        task_id = str(row.get("task_id", ""))
        for task, batch in zip(self.write_tasks, self.batches):
            if str(task.get("task_id", "")) != task_id or not isinstance(batch, dict):
                continue
            task_ids = [str(i) for i in task.get("expected_ids") or []]
            if not row.get("expected_ids") or sorted(task_ids) == sorted(item_ids):
                members = self._batch_member_items(batch)
                return [
                    (task_ids[index] if index < len(task_ids) else None, item)
                    for index, item in enumerate(members)
                ]
            break
        by_id = self._items_by_member_id()
        return [(i, by_id[i]) for i in item_ids if i in by_id]

    @staticmethod
    def _row_not_applied(row: Dict[str, Any]) -> Tuple[Dict[str, str], Dict[str, str]]:
        """``(declined, skipped)``: a row's items its batch declined and the
        items a ``--human-task <id>=skip`` answer recorded as skipped at the
        user's request, each ``{id: reason}`` (fix round 18). Never applied."""
        from .subagent_executor import row_declined

        return (
            row_declined(row),
            row_declined({"declined": row.get("skipped_items")}),
        )

    @staticmethod
    def _item_file_lines(item: Dict[str, Any]) -> List[str]:
        """An item's ``   - File: <path>[:<a>-<b>]`` line, when it names one."""
        file_path = item.get("file")
        if not file_path:
            return []
        line_range = item.get("line_range") or []
        if len(line_range) >= 2:
            return [f"   - File: {file_path}:{line_range[0]}-{line_range[1]}"]
        return [f"   - File: {file_path}"]

    def _not_applied_item_lines(
        self, member: str, item: Optional[Dict[str, Any]], task_id: str, why: str,
    ) -> List[str]:
        """One item of a not-applied section (fix round 22): ``- **<title>**
        (`<id>`, <batch>) — <reason>``, then its file; the id alone when this
        run's batches no longer hold the item."""
        if item is None:
            return [f"- `{member}` ({task_id}) — {why}"]
        title = item.get("title") or item.get("theme") or "Untitled"
        return [f"- **{title}** (`{member}`, {task_id}) — {why}"] + self._item_file_lines(item)

    def write_apply_summary_report(self) -> Optional[str]:
        """Write ``{phase}/summary.md`` — the report the instructions promise (F3).

        Their *Output Files* block lists this file for all three apply phases,
        and their *Generate Summary Report* step describes its sections; both
        live on the native leg, which ``--exec-subagents`` never reaches ("the phase
        finishes in that one invocation"). So the executor leg writes the same
        document itself, from the data it already has: the batch outcomes, the
        skip list rebuilt after judging, and the judge's own decisions.

        F10 extends it with the per-fix detail the instructions' own template
        promises and that was sitting unread on disk: each batch's own items
        (title, file:lines when the item has them, applied/not-applied) from
        ``self.batches``, the runner's free-text ``notes`` from its result file,
        plus ``Base ref`` / batching-efficiency lines when the orchestrator
        computed them (empty for the two sibling phases, which is why both are
        conditional rather than assumed present).

        Best-effort and never fatal — a report is not worth failing an applied
        run over. Returns the path written, or ``None``.
        """
        try:
            from .write_batch_scheduler import (
                CODE_WRITE_KINDS, batch_check_section, verification_line,
            )
        except ImportError:  # pragma: no cover - direct script runs
            from utils.write_batch_scheduler import (  # type: ignore
                CODE_WRITE_KINDS,
                batch_check_section,
                verification_line,
            )
        from .commit_spelling import commit_view
        from .subagent_executor import (
            DECLINED_SECTION_HEADING,
            SKIPPED_SECTION_HEADING,
            batch_check_could_not_run,
            row_batch_check_findings,
        )
        phase_dir = os.path.join(self.out_dir, self.phase_name)
        result = self.write_result
        # #28: the phase's rows, not this run's outcomes — a `--resume` keeps
        # the batches an interrupted run of this review cycle finished, marked
        # "(earlier run)" with that run's runner, duration and verdict. The
        # count lines below are computed from the same rows as the table.
        rows = self._phase_rows()
        ok = [row for row in rows if self._row_ok(row)]
        item_counts = self._write_item_counts(rows)
        decided = self.judge_decisions()
        titles = self._titles_by_group_id()
        nouns = self.item_noun_plural

        lines = [
            f"# Applied {nouns.title()} Report",
            "",
            # `**Commit brief**:` on a commit review (plans/review-commits.md §2.8).
            f"**{self._document_title()}**: {self.plan_path}",
        ]
        target = self.write_target_file()
        touched = self._touched_files()
        if target:
            lines.append(f"**Applied to**: {target}")
        elif touched:
            # F7: apply-code-fixes has no single write target — the files the
            # batches verified changed is the honest "what did this phase
            # change" answer, where before nothing named it at all.
            lines.append(f"**Files changed**: {', '.join(touched)}")
        base_ref = self.resolve_base_ref()
        if base_ref:
            lines.append(f"**Base ref**: {base_ref}")
        lines += [
            f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Summary",
            f"- Batches processed: {len(ok)}/{len(rows)}"
            + self._rows_provenance_note(rows),
            f"- {nouns.capitalize()} applied: {item_counts['applied']}",
            *(
                [f"- {nouns.capitalize()} declined by their batch (not "
                 f"applied): {item_counts['declined']}"]
                if item_counts["declined"] else []
            ),
            *(
                [f"- {nouns.capitalize()} skipped at your request (not "
                 f"applied): {item_counts['skipped']}"]
                if item_counts["skipped"] else []
            ),
            f"- {nouns.capitalize()} skipped: {len(self.formatted_skipped)}",
            f"- Decided by the judge agent: {len(decided)}"
            + self._judge_breakdown(decided),
        ]
        if item_counts["no-op"]:
            lines.append(f"- {nouns.capitalize()} needing no changes: {item_counts['no-op']}")
        if item_counts["clean-failure"]:
            lines.append(f"- {nouns.capitalize()} without verified changes: {item_counts['clean-failure']}")
        # F4: the instructions' own report template requires a verification line
        # and this leg had none, so a phase that applied seven code fixes without
        # running any check read exactly like one that had. Only for the
        # code-editing phase — a typecheck has nothing to say about a plan file.
        if self.write_kind in CODE_WRITE_KINDS:
            lines.append(f"- Verification: {verification_line(result)}")
        if self.batching_stats.get("batching_enabled"):
            lines.append(
                f"- Batching efficiency: "
                f"{self.batching_stats.get('subagent_calls_saved', 0)} "
                f"subagent call(s) saved "
                f"({self.batching_stats.get('efficiency_gain_percent', 0)}%)"
            )
        lines += [
            "",
            "## Applied Changes",
            "",
        ]
        # Fix round 22 (live run 9): an item its batch declined, or that a
        # `=skip` answer recorded as skipped at your request, is listed in a
        # section of its own below, never under this applied heading.
        not_applied_sections: Dict[str, List[str]] = {
            DECLINED_SECTION_HEADING: [], SKIPPED_SECTION_HEADING: [],
        }
        if rows:
            for row in rows:
                item_ids = self._row_item_ids(row)
                # `subagent_executor.row_outcome_label`'s reading order.
                verdict = row.get("outcome_label") or row.get("write_outcome") or "-"
                failing = (
                    (", its check could not run"
                     if batch_check_could_not_run(row_batch_check_findings(row))
                     else ", its check fails")
                    if self._row_ok(row) and row_batch_check_findings(row) else ""
                )
                lines.append(
                    f"### {row.get('task_id')}{self._row_provenance(row)} — "
                    f"{row.get('status')} ({verdict}{failing})"
                )
                lines.append(
                    f"**{nouns.capitalize()}**: {len(item_ids)}  "
                    f"**Duration**: {float(row.get('duration_seconds') or 0.0):.1f}s  "
                    f"**Runner**: {row.get('runner') or '(none)'}"
                )
                members = self._row_items_with_ids(row, item_ids)
                items = [item for _member, item in members]
                declined, skipped = self._row_not_applied(row)
                if not items and item_ids and row.get("from_earlier_run"):
                    # An earlier batch whose items this run no longer selects:
                    # its ids are all that is left to name them by.
                    lines.append(
                        "**Items**: " + ", ".join(f"`{i}`" for i in item_ids)
                    )
                titles_by_member = {member: item for member, item in members}
                for kept, heading in (
                    (declined, DECLINED_SECTION_HEADING),
                    (skipped, SKIPPED_SECTION_HEADING),
                ):
                    for member, why in kept.items():
                        not_applied_sections[heading] += self._not_applied_item_lines(
                            member, titles_by_member.get(member),
                            str(row.get("task_id")), why,
                        )
                if declined or skipped:
                    told = [
                        f'{len(kept)} {words} (listed under "{heading}" below)'
                        for kept, words, heading in (
                            (declined, "declined by the batch", DECLINED_SECTION_HEADING),
                            (skipped, "skipped at your request", SKIPPED_SECTION_HEADING),
                        ) if kept
                    ]
                    lines.append(f"**Not applied**: {'; '.join(told)}")
                listed = [
                    (member, item) for member, item in members
                    if member not in declined and member not in skipped
                ]
                if listed:
                    item_status = {
                        "applied": "Applied",
                        "no-op": "No changes needed",
                        "clean-failure": "No verified changes",
                        "partial-application": "Partial application; inspect batch",
                    }.get(verdict, "Not applied")
                    for item_index, (member, item) in enumerate(listed, 1):
                        item_title = item.get("title") or item.get("theme") or "Untitled"
                        lines.append(f"{item_index}. **{item_title}** - {item_status}")
                        lines += self._item_file_lines(item)
                notes = self._read_batch_result_notes(
                    row.get("output_path"), item_ids
                )
                if notes:
                    lines.append(f"**Notes**: {notes}")
                reason = row.get("reason")
                if reason:
                    lines.append(f"**Reason**: {reason}")
                lines.append("")
            # Fix round 14: the batches whose own check failed, whole, in the
            # commit modes' words on a commit review (§2.8).
            section = batch_check_section(
                rows, commit_review=commit_view(self.plan_path) is not None)
            if section:
                lines += section[1:] + [""]
            for heading, entries in not_applied_sections.items():
                if entries:
                    lines += [f"## {heading}", ""] + entries + [""]
        else:
            lines += ["(no batches were dispatched)", ""]

        if decided:
            lines += [
                f"## Decided by the judge agent ({len(decided)})",
                "",
                f"judge: {', '.join(self._judges_of(decided))}",
                "",
                f"{nouns.capitalize()} whose decision was offloaded to a judge "
                f"subagent (`{AGENT_DECIDE_FLAG}`, or a per-item \"Let the agent "
                "decide\" selection).",
                "",
            ]
            for group_id, record in decided.items():
                context = record.get("batch_context") or {}
                lines.append(
                    f"### {titles.get(group_id, group_id)} "
                    f"({context.get('importance_at_decision', 'MEDIUM')}) — "
                    f"{judge_outcome(record).capitalize()}"
                )
                lines.append(f"**Group**: `{group_id}`")
                lines.append(f"**Source**: {judge_source_label(context.get('decision_source'))}")
                if context.get("salvaged_description"):
                    lines.append(f"**Kept**: {context['salvaged_description']}")
                if context.get("dropped"):
                    lines.append(f"**Dropped**: {context['dropped']}")
                if record.get("reason"):
                    lines.append(f"**Reason**: {record['reason']}")
                lines.append("")

        warnings = self.consistency_warnings()
        if warnings:
            lines += ["## Consistency warnings", ""]
            lines += [f"- {warning}" for warning in warnings]
            lines.append("")

        if self.formatted_skipped:
            lines += [f"## Skipped {nouns.title()}", ""]
            for item in self.formatted_skipped:
                lines.append(
                    f"### {item.get('title', 'Unknown')} "
                    f"[{judge_status_label(item.get('status'))}]"
                )
                gid = str(item.get("group_id") or "")
                if gid:
                    lines.append(f"**Group**: `{gid}`")
                if item.get("reason"):
                    lines.append(f"**Reason**: {item['reason']}")
                if item.get("files"):
                    # A commit guard skip (§2.7): the files that caused it.
                    lines.append(
                        "**Files**: " + ", ".join(f"`{f}`" for f in item["files"])
                    )
                lines.append("")

        path = os.path.join(phase_dir, "summary.md")
        try:
            os.makedirs(phase_dir, exist_ok=True)
            with open(path, "w", encoding="utf-8") as handle:
                handle.write("\n".join(lines).rstrip() + "\n")
        except OSError as exc:  # noqa: BLE001 - a report must not fail a run
            self.logger.warning("summary report not written: %s", exc)
            return None
        print(f"[write-subagents] summary report: {path}")
        return path

    def _patch_write_batch_report_summary_file(self, summary_path: str) -> None:
        """Fill in ``write_batch_report.json``'s ``summary_file`` after the fact (F11).

        ``WriteBatchScheduler`` serializes that report inside
        ``run_write_executor()``, before this base ever calls
        ``write_apply_summary_report()`` — the scheduler only fills
        ``summary_file`` itself when constructed with its own ``summary_file``
        argument, which the apply phases never pass (they write their own
        summary here, on this leg). So the report on disk said
        ``summary_file: null`` for a run that went on to write one a few lines
        later. Patched here, once the apply phase's own path is known, rather
        than by changing the scheduler (owned elsewhere — see AGENTS.md).

        Best-effort: a read/parse/write failure is logged and never raised, the
        same posture as the report it patches.
        """
        if self.write_result is not None:
            self.write_result.summary_file = summary_path
        report_path = getattr(self.write_result, "report_path", None)
        if not report_path or not os.path.isfile(report_path):
            return
        try:
            with open(report_path, "r", encoding="utf-8") as handle:
                report = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:  # noqa: BLE001 - best-effort
            self.logger.warning("write_batch_report.json not patched: %s", exc)
            return
        if not isinstance(report, dict) or report.get("summary_file") == summary_path:
            return
        report["summary_file"] = summary_path
        try:
            from .subagent_executor import _atomic_write_json
        except ImportError:  # pragma: no cover - direct script runs
            from subagent_executor import _atomic_write_json  # type: ignore
        try:
            _atomic_write_json(report_path, report)
        except OSError as exc:  # noqa: BLE001 - best-effort
            self.logger.warning("write_batch_report.json not patched: %s", exc)

    def regenerate_decisions_overlay(self) -> Optional[str]:
        """Badge the review report's findings with this phase's decisions (F3).

        The in-process twin of ``util report regenerate-decisions --apply-phase
        {phase}``, which the instructions run on the native leg only.
        Called as a function rather than shelled out: the executor leg is
        already inside the process that holds the decisions, and a subprocess
        would re-resolve the skill dir it is running from.

        Best-effort by design — the command it mirrors exits 0 with a notice
        when the review predates the ``report_data.json`` sidecar.
        """
        if self.state is None:
            return None
        review_dir = Path(self.out_dir) / self.review_subdir
        if not (review_dir / "report_data.json").exists():
            return None
        decisions = self.state.get_all_human_decisions(self.phase_name)
        # The commit guard's skips badge their groups beside the decisions
        # (plans/review-commits.md §2.10): read from the saved guard.
        guard = None
        if self._pinned is not None:
            from .commit_apply import guard_record

            guard = guard_record(self.state.state)
        if not decisions and not (guard and guard.get("skipped")):
            return None
        try:
            from .html_report_generator import (
                regenerate_report_with_human_decisions,
            )
        except ImportError:  # pragma: no cover - direct script runs
            from utils.html_report_generator import (  # type: ignore
                regenerate_report_with_human_decisions,
            )
        try:
            report_path, matched = regenerate_report_with_human_decisions(
                review_dir, decisions, **({"guard": guard} if guard else {})
            )
        except Exception as exc:  # noqa: BLE001 - an overlay must not fail a run
            self.logger.warning("decision overlay not regenerated: %s", exc)
            return None
        if report_path is None:
            return None
        print(
            f"[write-subagents] decisions overlaid on {report_path} "
            f"({matched} of {len(decisions)} decision(s) matched)"
        )
        if matched < len(decisions):
            self.logger.warning(
                "decision overlay matched %d of %d decision(s) on %s — the "
                "rest joined no group (no groupHash, or a stale group id)",
                matched, len(decisions), report_path,
            )
        return str(report_path)

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

        from .subagent_executor import ExecutorError
        from .write_safety import WriteSafetyError
        from .write_batch_scheduler import WriteBatchScheduler
        from .write_phase_bridge import (
            materialize_write_tasks,
            write_task_file_for_phase,
        )

        phase_dir = os.path.join(self.out_dir, self.phase_name)
        os.makedirs(phase_dir, exist_ok=True)
        grouped_file = os.path.join(self.out_dir, self.review_subdir, "grouped.json")
        artifact = self.write_phase_artifact()
        tasks_file = artifact if artifact != self.plan_path else None
        tasks = materialize_write_tasks(
            kind=self.write_kind,
            batches=[
                batch if isinstance(batch, dict) else batch.to_dict()
                for batch in self.batches
            ],
            phase_dir=phase_dir,
            plan_file=self.plan_path,
            tasks_file=tasks_file,
            grouped_file=grouped_file if os.path.exists(grouped_file) else None,
        )
        task_file = write_task_file_for_phase(
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

        # Plan step 3 (codex-sandbox-unavailable-findings-and-fixes, F1 "How a
        # dispatch receives its grant", 2026-09-30): the phase's one write
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
            scheduler = WriteBatchScheduler(
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
                # Fix round 18: the stopped batches answered `=skip`, and the
                # answer the stop offers, in this host's spelling.
                partial_skips=getattr(self, "partial_skips", None) or None,
                user_commands=self._stop_user_commands(),
            )
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
        # Fix round 14: a batch whose own check failed after its edits, and
        # a code phase nothing verified, are on the result line a host relays.
        from .cli_common import record_error, record_notice
        from .write_batch_scheduler import write_result_notice

        stop = getattr(result, "stop", None) or {}
        if stop.get("headline"):
            # Fix round 18 (live run 7, Codex racing 08): an apply phase's
            # stop left the result line with no `error`, so the tool's
            # needs-human message said "Its result line names no error" and
            # the host relayed only the resume command — not what stopped,
            # what the batch reported or what did not run. The headline is
            # that line, as implement records it.
            record_error(stop["headline"])
        notice = write_result_notice(result)
        if notice:
            record_notice(notice)
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
        from .write_phase_bridge import (
            materialize_write_tasks,
            native_run_record,
            write_task_file_for_phase,
        )

        phase_dir = os.path.join(self.out_dir, self.phase_name)
        os.makedirs(phase_dir, exist_ok=True)
        grouped_file = os.path.join(self.out_dir, self.review_subdir, "grouped.json")
        grouped = grouped_file if os.path.exists(grouped_file) else None
        artifact = self.write_phase_artifact()
        tasks_file = artifact if artifact != self.plan_path else None
        tasks = materialize_write_tasks(
            kind=self.write_kind,
            batches=[
                batch if isinstance(batch, dict) else batch.to_dict()
                for batch in self.batches
            ],
            phase_dir=phase_dir,
            plan_file=self.plan_path,
            tasks_file=tasks_file,
            grouped_file=grouped,
        )
        self._native_write_tasks = list(tasks)
        # Fix round 26: stamped native, so `status` shows this run rather
        # than an earlier executor run's `.status.json`.
        from .host_capabilities import resolve_host_id

        # Fix round 29: and with the run its batches belong to, read before
        # this rewrite, so `status` counts what the whole run handed out
        # across a `--resume` and none of an earlier run's records.
        run = native_run_record(
            phase_dir, tasks, resume=bool(getattr(self.args, "resume", False)))
        return write_task_file_for_phase(
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
        from .batch_done import resume_refusal_lines, unrecorded_logged_batches

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
        try:
            from .git_utils import get_modified_files, get_staged_files
        except ImportError:  # pragma: no cover
            from utils.git_utils import get_modified_files, get_staged_files
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

        Returns:
            Absolute path where the output JSON should be written.
        """
        raise NotImplementedError(
            f"{type(self).__name__} must implement get_output_path()"
        )

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
            imp = item.get("importance", "MEDIUM").upper()
            if imp in by_importance:
                by_importance[imp].append(item)

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
        --internal-revalidation, and --dry-run CLI flags to determine the
        revalidation mode:

        1. **dry-run**: Print which items *would* be revalidated, then return
           (the caller continues with the normal flow).
        2. **internal-revalidation** (legacy): Run revalidation in-process via
           ``asyncio.run(revalidate_failed_items(...))``, save updated
           validation results, and continue.
        3. **default** (subagent delegation): Prepare batched revalidation
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

        # ----- internal-revalidation (legacy in-process mode) -----
        if getattr(self.args, "internal_revalidation", False):
            print("Running internal revalidation...", file=sys.stderr)

            self.validation = asyncio.run(
                revalidate_failed_items(
                    groups=self.groups,
                    validation_results=self.validation,
                    context=context,
                    model=model,
                    include_all_human=include_all_human,
                )
            )

            save_validation_results(
                self.validation, validation_path, model=model
            )
            print(
                f"Updated validation saved to: {validation_path}",
                file=sys.stderr,
            )
            # Continue with the updated validation (no exit)
            return

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
        from .review_orchestrator_base import dispatch_subagent_tasks

        if dispatch_subagent_tasks(
            self.args,
            task_file=revalidation_task_path,
            phase_dir=review_dir,
            phase=self.phase_name,
            document=revalidation_tasks,
            plan_path=str(self.plan_path),
            label="revalidation",
        ):
            from .validation import merge_batched_revalidation_results

            self.validation = merge_batched_revalidation_results(
                output_dir=review_dir,
                revalidation_metadata=revalidation_tasks,
            )
            save_validation_results(self.validation, validation_path, model=model)
            print(f"Updated validation saved to: {validation_path}", file=sys.stderr)
            return

        print(
            "\nAfter revalidation completes, run this orchestrator again "
            "without --revalidate"
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
        from .validation import REVALIDATION_SNAPSHOT_NAME, bind_document_file

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

        Fix round 20: the native leg's line saying nothing ran the repository's
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
        from .write_batch_scheduler import native_apply_fixes_unverified_line

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

        Called from ``_prepare_batches`` when ``--dry-run`` is active.
        """
        print("\n--- DRY RUN ---", file=sys.stderr)
        print("\nWould apply the following batches:", file=sys.stderr)
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

        if self.needs_human:
            print("\nWould ask for human review:", file=sys.stderr)
            for group in self.needs_human:
                theme = group.get("theme", group.get("title", "Unknown"))
                reason = group.get("validation_reason", "No reason")
                print(f"  - {theme}: {reason}", file=sys.stderr)
