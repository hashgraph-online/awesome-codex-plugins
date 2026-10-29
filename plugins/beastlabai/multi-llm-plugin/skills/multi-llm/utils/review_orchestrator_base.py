"""Shared review-orchestration logic for review-plan and review-tasks phases.

This module extracts the common patterns used by review_plan_orchestrator.py
and review_tasks_orchestrator.py into reusable functions, eliminating ~1200+
lines of duplicated logic. Phase-specific orchestrators configure parameters
(prompt template, phase name, output types, consolidation toggle) and delegate
to these shared functions.

Functions cover:
- Model invocation (run_single_model, run_all_models)
- Result saving and validation (save_model_result)
- Status file management (_write_status, _update_status)
- Aggregation (aggregate_results, reaggregate_from_existing_files)
- Common helpers (derive_prefix, get_backoff_delay, extract_json_array, etc.)
"""

import argparse
import asyncio
import contextvars
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, FrozenSet, List, NamedTuple, Optional, Sequence, Tuple, Union

from . import detach as _detach
from . import status_file as _status_file
from . import validation_context as _validation_context
from . import cli_common
from . import progress_tracker as _progress
from . import readonly_audit as _readonly_audit
from . import result_files as _result_files
from .progress_tracker import DEADLINE_ERROR, FanoutProgress, PhaseProgress
from .cli_common import (
    dispatcher_command,
    durable_reaggregate_fields,
    invocation,
    modes_table as _modes,
    record_artifacts,
    record_next,
)
from .output_handler import sanitize_prefix, get_phase_dir
from .prompt_loader import load_prompt
from .interactive import resolve_models
from . import unattended as _unattended
from .unattended import NeedsHuman
from .provider_registry import (
    get_all_model_specs,
    parse_model_spec,
    get_provider,
    get_provider_timeout,
    get_provider_max_concurrent,
    get_subagent_retries,
    is_model_valid,
    set_run_anchor,
)
from .json_extractor import (
    build_unsanitize_map,
    generate_output_path,
    has_salvageable_json,
    read_json_from_file,
    sanitize_model_name,
)
from .schema_validator import drop_non_record_entries
from .llm_client import (
    ERROR_TIMEOUT,
    FAILURE_JAIL_DENIED,
    SALVAGE_FAILURE_KEY,
    SALVAGE_FAILURE_TIMEOUT,
    SALVAGE_TEXT_KEY,
    SANDBOX_BYPASSED,
    STDOUT_OUTPUT_LOCATION,
    _INCIDENTAL_RUNG_IDS,
    sandbox_fallback_rung_of,
    sandbox_record_word,
    sandbox_word_is_incidental,
    describe_output_file,
    invoke_with_provider,
    invoke_with_file_output,
    misnamed_result_baseline,
    render_output_location,
    render_working_limits,
    requested_result_baseline,
)
from .providers.base import (
    CATEGORY_CONNECTION_ERROR,
    CATEGORY_INVALID_MODEL,
    CATEGORY_PERMISSION_DENIED,
    CATEGORY_SANDBOX_UNAVAILABLE,
    CATEGORY_SERVER_ERROR,
    CODEX_HOME_CHECK_MARKER,
    INCIDENTAL_LANE_FANOUT,
    LADDER_RUNGS,
    MODE_CHECK_MARKER,
    PROFILE_GENERATE,
    SANDBOX_BYPASSED_MARKER,
    SANDBOX_FALLBACK_AUTO,
    SANDBOX_RUNG_UNSANDBOXED,
    LLMProvider,
    SandboxRung,
    classify_streams,
    rung_is_incidental,
    sandbox_bypassed_notice_text,
    sandbox_fallback_notice_text,
    sandbox_incidental_notice_text,
    sandbox_rung_retired_notice,
    sandbox_walk_clause,
    split_reasoning_effort,
    context_length_message,
)
from .retry_ladder import (
    RetryLadder,
    STATUS_AUTH_FAILED,
    STATUS_CONTEXT_LENGTH_EXCEEDED,
    STATUS_OK,
    STATUS_RATE_LIMITED,
    STATUS_RUNNER_ERROR,
    STATUS_SALVAGE_UNRECOVERABLE,
    STATUS_SPAWN_FAILED,
    STATUS_TIMEOUT,
    budget_exhausted_reason,
)
from .git_utils import get_project_root, git_argv
from .html_report_generator import (
    failed_models_line,
    generate_html_report,
    write_html_report,
    model_label,
    served_model_label,
    sort_raw_groups_by_priority,
    compute_max_importance,
    IMPORTANCE_ORDER,
)
from .state_manager import (
    get_or_create_state,
    stamp_stable_ids,
    load_groups_payload,
    save_groups_payload,
    CURRENT_FORMAT_VERSION,
)
from .validation import (
    PLAN_SNAPSHOT_NAME,
    TASKS_BACKUP_NAME,
    TASKS_SNAPSHOT_NAME,
    BoundDocument,
    ValidationContextError,
    bind_document_file,
    decode_document,
    ensure_prompt_sidecars,
    legacy_context_round_reason,
    prepare_batched_validation_tasks,
    publish_from_task_document,
    verify_context_sources,
    merge_batched_validation_results,
    resolved_reaggregate_command,
    stale_validation_reason,
    validation_source_decision,
)
from .subagent_tasks import (
    TaskFileError,
    build_inputs,
    read_task_file,
    write_salvage_task_file,
)
from . import (
    group_similar_suggestions,
    export_groups_to_json,
    validate_groups,
    apply_validation_to_groups,
    save_validation_results,
)

# Required fields for each suggestion (shared across review phases)
REQUIRED_FIELDS = ["title", "desc", "importance", "reference", "type"]

# Valid values for certain fields
VALID_IMPORTANCE = {"high", "medium", "low"}
VALID_TYPES = {"addition", "modification", "deletion", "clarification"}

# Delay between launching provider processes to avoid concurrent launch bugs
PROVIDER_STAGGER_DELAY = 2.0  # seconds

# Maximum prompt length to log
MAX_LOGGED_PROMPT_LENGTH = 5000


# ---------------------------------------------------------------------------
# Status file helpers
# ---------------------------------------------------------------------------
# The implementations moved to utils/status_file.py — unchanged semantics (same
# atomic temp+rename, same best-effort swallow, same special-cased merge, now
# extended to the reserved `run`/`progress` objects a detached run writes). They
# are re-exported here, and from review_plan_orchestrator as
# `_write_status`/`_update_status`, because this module is the status file's
# documented owner and every existing caller and test names it through one of
# those two paths.
#
# Why they live in their own module at all: `multi_llm.py status` must be a
# sub-second command (hosts with a 2-minute shell cap poll it in a loop), and
# importing this module pulls in the provider client, the HTML report generator
# and the validation stack.

write_status = _status_file.write_status
update_status = _status_file.update_status


def recompute_consolidation_recommendation(
    phase_dir: str,
    groups: Optional[List[Dict[str, Any]]],
    args: argparse.Namespace,
    supports_consolidation: bool,
) -> Optional[Dict[str, Any]]:
    """Recompute ``consolidation_recommended`` from ``groups``, up **or down** (§7.2a).

    Called by both completion paths — the fan-out's first run and
    ``reaggregate_from_existing_files`` — whenever the phase supports
    consolidation, including when ``groups`` is empty or ``None``: a round that
    drops to zero groups must clear a recommendation an earlier round recorded.

    The count includes ``needs-human-decision`` as well as ``valid`` groups,
    matching ``full_workflow_orchestrator._consolidation_recommended``, even
    though the recorded field is named ``valid_groups`` (renaming it would change
    the result contract). The threshold is ``args.consolidation_threshold``, else
    :data:`consolidation.CONSOLIDATION_RECOMMENDED_THRESHOLD`.

    At or above the threshold the object is written with ``update_status`` and
    put on the result line through ``cli_common.record_consolidation_recommended``
    (never as ``next``). Below it, or when ``consolidated.json`` was already
    built from these groups (:func:`consolidation.consolidation_is_current`),
    the key is **deleted** from ``.status.json``
    with ``status_file.remove_status_keys`` — not written as ``null`` through
    ``update_status``, whose merge cannot remove a key — and nothing is
    recorded, so ``MULTI_LLM_RESULT`` omits it.

    Returns:
        The recommendation written, or ``None``.
    """
    if not supports_consolidation:
        return None
    from .consolidation import (
        CONSOLIDATION_RECOMMENDED_THRESHOLD, consolidation_is_current,
    )
    # Live run 8: a consolidation that already ran on these groups is not
    # recommended again (a `--reaggregate` after `--consolidate` re-enters
    # here); groups that changed since make it stale, and it is again.
    if consolidation_is_current(phase_dir):
        _status_file.remove_status_keys(phase_dir, ["consolidation_recommended"])
        return None
    groups = groups or []
    valid_group_count = sum(
        1 for g in groups
        if isinstance(g, dict)
        and g.get("validation_status") in ("valid", "needs-human-decision")
    )
    threshold = getattr(args, 'consolidation_threshold', None) or CONSOLIDATION_RECOMMENDED_THRESHOLD
    if valid_group_count < threshold:
        _status_file.remove_status_keys(phase_dir, ["consolidation_recommended"])
        return None
    print(f"\n[CONSOLIDATION_RECOMMENDED] {valid_group_count} valid groups >= threshold ({threshold})")
    print(f"Run: --consolidate to cluster related suggestions")
    # The marker is a *log* line, and a detached run's caller never sees the log —
    # so on the route every host actually reads (the launch returns, `status
    # --view run` renders the checkpoint) the recommendation used to vanish
    # entirely. Measured 2026-09-16: a 29-group run printed the marker and the
    # session model reported "no consolidation was recommended". Recorded here in
    # the checkpoint and on the result line, and **never** as `next` —
    # `--consolidate` is a mechanical continuation a host may auto-follow, and a
    # recommendation is not an instruction.
    recommendation = {
        "valid_groups": valid_group_count,
        "threshold": threshold,
        "command": "--consolidate",
    }
    update_status(phase_dir, {"consolidation_recommended": recommendation})
    cli_common.record_consolidation_recommended(recommendation)
    return recommendation


def maybe_detach(
    *,
    args: argparse.Namespace,
    mode: str,
    phase_dir: str,
    plan_file: str,
    phase: Optional[str] = None,
    ask_slug: Optional[str] = None,
    model_specs: Optional[List[str]] = None,
) -> Optional[int]:
    """The one detach boundary a fan-out phase crosses.

    Returns ``None`` to keep running in this process (the ordinary foreground run,
    and also the detached worker once it owns the phase dir) or an exit code the
    caller must return immediately (the invoker, after forking; or a launch
    failure).
    """
    if getattr(args, "internal_worker", False):
        try:
            _detach.handle_phase_detach(
                args=args, mode=mode, argv=[], phase_dir=phase_dir,
                plan_file=plan_file, phase=phase, ask_slug=ask_slug,
            )
        except _detach.DetachError as exc:
            print(str(exc), file=sys.stderr)
            return exc.exit_code
        return None
    if not getattr(args, "detach", False):
        return None

    record = invocation()
    if not record or record.get("mode") != mode:
        # The child re-executes `uv run … multi_llm.py <mode> …`, rebuilt from the
        # dispatcher's normalized argv (never a remembered sys.argv). A direct
        # `python <orchestrator>.py --detach` has no such argv to rebuild from, and
        # guessing one from the parsed namespace would silently drop flags.
        print(
            "ERROR: --detach must be invoked through multi_llm.py — the detached "
            "child re-executes the dispatcher under the same `uv run --project` "
            "wrapping, which a direct orchestrator invocation cannot reconstruct."
            f"\n       Run: {dispatcher_command(mode, plan_file, '--detach')}",
            file=sys.stderr,
        )
        return 3
    try:
        return _detach.handle_phase_detach(
            args=args, mode=mode, argv=record["argv"], phase_dir=phase_dir,
            plan_file=plan_file, phase=phase, ask_slug=ask_slug,
            model_specs=model_specs,
        )
    except _detach.DetachError as exc:
        print(str(exc), file=sys.stderr)
        return exc.exit_code


# ---------------------------------------------------------------------------
# Common helpers
# ---------------------------------------------------------------------------

def derive_prefix(plan_file: str) -> str:
    """Derive output prefix from plan file path."""
    basename = os.path.basename(plan_file)
    return sanitize_prefix(basename)


def read_plan(plan_path: str) -> str:
    """Read and return the plan file content."""
    with open(plan_path, 'r', encoding='utf-8') as f:
        return f.read()


def _batch_self_reported_model(batch_file: str) -> Optional[str]:
    """A batch file's own ``metadata.model`` (its subagent's self-report), or ``None``."""
    try:
        with open(batch_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    metadata = data.get("metadata")
    model = metadata.get("model") if isinstance(metadata, dict) else None
    return str(model) if model else None


def _authoritative_validator_runner(
    phase_dir: str, batch_metadata: Dict[str, Any]
) -> Dict[int, Optional[str]]:
    """Per batch, the runner the executor verifiably dispatched it to (F3, §7.3a).

    A validation batch's own ``metadata.model`` is the subagent's free-hand
    self-report — in one captured run, five different spellings across 11
    batches, one of them another model's name copied out of the suggestions
    it was validating. ``subagent_batch_report.json`` is the executor's own
    record of what it dispatched, keyed by the same ``task_id`` each batch
    carries (``f"{kind}-batch-{batch_index}"``).

    That record only speaks for the bytes the executor persisted, so it is
    decided **per batch and by content hash** (§7.3a), never by mtime:

    - the report's ``batch_provenance`` row for this task matches the file's
      current sha256 *and* the current task file's ``kind``/round → the
      recorded runner;
    - the hash differs (a hand rewrite, a revalidation by another host) or the
      kind/round differs (revalidation reuses the filenames with a different
      subset mapping) → ``None``, and the merge uses the batch's own
      ``metadata.model``;
    - no report at all (the host-native Claude Code Task tool path, whose
      batches this process never dispatched) → ``None`` for every batch.

    **Legacy fallback only:** a report written before ``batch_provenance``
    existed carries just the per-row ``runner``; that row is used as before.

    Returns:
        ``{batch_index: runner_or_None}`` for every batch in ``batch_metadata``.
    """
    try:
        from .subagent_executor import _recorded_provenance, _recorded_runners
        from .subagent_tasks import batch_manifest, file_bytes_sha256
    except ImportError:  # pragma: no cover - direct script runs
        from subagent_executor import _recorded_provenance, _recorded_runners  # type: ignore
        from subagent_tasks import batch_manifest, file_bytes_sha256  # type: ignore
    kind = batch_metadata.get("kind") or "validation"
    batches = batch_metadata.get("batches", [])
    result: Dict[int, Optional[str]] = {}
    provenance = _recorded_provenance(phase_dir)
    if provenance is None:
        legacy = _recorded_runners(phase_dir)
        for batch in batches:
            index = batch.get("batch_index")
            result[index] = legacy.get(batch.get("task_id") or f"{kind}-batch-{index}")
        return result
    manifest = batch_manifest(batch_metadata)
    for batch in batches:
        index = batch.get("batch_index")
        row = provenance.get(str(batch.get("task_id") or f"{kind}-batch-{index}"))
        runner: Optional[str] = None
        if (
            row
            and row.get("kind") == manifest["kind"]
            and row.get("round") == manifest["round"]
            and row.get("sha256")
            and row.get("sha256") == file_bytes_sha256(
                os.path.join(phase_dir, f"validation_batch_{index}.json")
            )
        ):
            runner = str(row.get("runner") or "") or None
        result[index] = runner
    return result


def merge_validation_batches(
    phase_dir: str,
    batch_metadata: Dict[str, Any],
    grouped: List[Any],
    validation_path: str,
) -> List[Dict[str, Any]]:
    """Merge ``validation_batch_N.json`` files into ``validation.json`` + groups.

    Shared by the two reaggregation sites and by the ``--exec-subagents``
    continuation (D3b), which reaches the merge in the *same* invocation that
    dispatched the batch instead of exiting at the marker. One implementation
    means the executor path and the native path cannot drift in how a batch is
    merged — only in who dispatched it.

    The written ``validation.json`` is bound to the exact batch bytes it
    consumed (§7.1a): ``metadata.batch_sha256 = {batch_index: sha256}`` for
    every batch file present, and ``metadata.batch_manifest = {kind, round}``
    of ``batch_metadata``. ``metadata.runners = {batch_index: model}`` records
    who answered each batch (§7.3b), and ``metadata.model`` is the single value
    when every batch agrees, else the sorted comma-joined list.
    """
    try:
        from .subagent_tasks import batch_manifest, file_bytes_sha256
        from .validation import join_model_names
    except ImportError:  # pragma: no cover - direct script runs
        from subagent_tasks import batch_manifest, file_bytes_sha256  # type: ignore
        from validation import join_model_names  # type: ignore
    # Hashed before the merge reads the files: a batch rewritten in between is
    # then recorded under its *old* hash, which the next reaggregate sees as a
    # change and re-merges — the safe direction.
    batch_hashes: Dict[str, str] = {}
    for batch in batch_metadata.get("batches", []):
        index = batch.get("batch_index")
        digest = file_bytes_sha256(
            os.path.join(phase_dir, f"validation_batch_{index}.json")
        )
        if digest:
            batch_hashes[str(index)] = digest
    validation_results = merge_batched_validation_results(
        output_dir=phase_dir,
        batch_metadata=batch_metadata,
        total_groups=len(grouped),
    )
    # `save_validation_results` already announces this write
    # ("[validation] Saved validation results to: ..."); a second line here
    # under a different name announced the same file twice in the run log.
    # F3/§7.3: per batch, the executor's own record of who ran it outranks what
    # the batch said about itself — but only while the batch's bytes are the
    # ones the executor persisted. `model` stays a plain string (compatibility):
    # the single attribution, or the sorted comma-joined list. `runner` carries
    # only the executor-verified attributions, and is omitted when there are
    # none (host-native path).
    recorded = _authoritative_validator_runner(phase_dir, batch_metadata)
    runners: Dict[str, str] = {}
    for batch in batch_metadata.get("batches", []):
        index = batch.get("batch_index")
        if str(index) not in batch_hashes:
            continue
        runners[str(index)] = (
            recorded.get(index)
            or _batch_self_reported_model(
                os.path.join(phase_dir, f"validation_batch_{index}.json")
            )
            or "unknown"
        )
    model = join_model_names(v for v in runners.values() if v != "unknown")
    runner = join_model_names(v for v in recorded.values() if v)
    save_validation_results(
        validation_results, Path(validation_path), model=model, runner=runner,
        runners=runners,
        batch_sha256=batch_hashes,
        batch_manifest=batch_manifest(batch_metadata),
    )
    # §2.4: every aggregation re-publishes `validation_context` from the bound
    # round's own recorded sources (never the live plan), plus how many
    # verdicts said they could not read the snapshot. One site for all four
    # merge callers — the first run, both `--reaggregate` legs and the
    # executor continuation.
    publish_from_task_document(phase_dir, batch_metadata, validation_results)
    return apply_validation_to_groups(
        [g.to_dict() if hasattr(g, 'to_dict') else g for g in grouped],
        validation_results,
    )


# ---------------------------------------------------------------------------
# Facts every review lane reports the same way
#
# review-plan and review-tasks run through `run_review_orchestration` below;
# review-code has its own fan-out and completion sites in
# `code_review_orchestrator.py`. Each of these used to exist twice — once here
# and once there, already drifting slightly — so the lanes were "consistent by
# duplication". They share one implementation of each fact now.
# ---------------------------------------------------------------------------

# D4a's `fanout_slot_counter` used to live here — a closure returning a
# `slot_finished()` that bumped `progress.models_done` once per finished slot,
# because the key was otherwise written `0` before the first launch and
# recomputed only after the last model returned (435 s of a 516 s `review-plan`,
# measured 2026-09-16, reading `models 0/4` beside models that had already
# finished). It is **deleted**, not left standing beside
# `progress_tracker.FanoutProgress`'s per-model map: a map-derived count plus a
# counter is two writers for one key and they can only disagree — the counter
# ticked at slot exit while the map turns terminal at the completion print, so a
# lane running both would flicker between counter-order and map-order. The
# tracker carries the counter's documented meaning with it: `models_done` counts
# **finished slots, not successful ones**, because a failed or skipped model has
# finished its slot, and which ones failed is `models_succeeded`'s job (see
# `FanoutProgress.counts`). The mid-run *number* is unchanged; only the writer
# is consolidated.


def backfill_deadline_losses(
    model_specs: List[str],
    results: Dict[str, Any],
    failed_models: Dict[str, str],
    *,
    tracker: Optional[FanoutProgress] = None,
) -> None:
    """F11: name every model the fan-out lost without a result of its own.

    A model whose task never returned — cancelled by the fan-out's own
    ``asyncio.wait_for`` deadline, or dropped as an ``Exception`` item — is in
    neither *results* nor (so far) *failed_models*: without this it is counted
    completed, inflates ``models_done`` and appears in no report section.

    **Only a model that produced nothing.** Until F2 (2026-09-20) the deadline
    branch discarded ``gather``'s whole result, so a slot that had already
    returned successfully reached here missing from *results* and was named a
    deadline loss beside the ``{model}.json`` it had just written; that branch
    harvests the finished tasks first now, and this walks a *results* dict that
    really does hold every slot that finished. Called by all three fan-out
    lanes — the review base, ``code_review_orchestrator`` and, since F4,
    ``ask_orchestrator``, which used to spell its own third wording for this
    cause.

    *tracker* gives the **per-model map** the same backfill in the same pass, so
    one walk writes both facts and a reader polling afterwards can never see a
    slot the report calls failed while the table still calls it ``running``. The
    wording is :data:`~utils.progress_tracker.DEADLINE_ERROR` on both sides
    rather than a string spelled twice, because the table and the report's
    failure list have to name one cause. Idempotent against the fan-out's own
    ``finally`` sweep: both touch only non-terminal entries, so whichever
    arrives first records the real ending — the sweep retires the common case
    promptly, this is the belt that catches a fan-out which returned by a path
    the sweep missed.
    """
    for model_spec in model_specs:
        if model_spec not in results and model_spec not in failed_models:
            failed_models[model_spec] = DEADLINE_ERROR
            if tracker is not None:
                tracker.failed(model_spec, error=DEADLINE_ERROR, source=None)


def record_review_artifacts(
    report_path: Any,
    report_html_path: Any,
    grouped_path: Any,
    *optional_paths: Any,
) -> List[str]:
    """Hand a review phase's files to the terminal ``MULTI_LLM_RESULT`` line.

    ``record_output_files`` feeds only ``.status.json`` (the channel ``status``
    reads); the ``artifacts`` list every host is told to trust instead comes
    from ``record_artifacts``, which no review lane used to call — a fully
    successful run reported ``artifacts: []``. The three files every lane
    writes are named unconditionally; *optional_paths* (validation.json,
    issues.json) only when they exist — the guard ``record_output_files``
    applies internally and ``record_artifacts`` does not.
    """
    artifacts = [str(report_path), str(report_html_path), str(grouped_path)]
    for path in optional_paths:
        if path and os.path.exists(str(path)):
            artifacts.append(str(path))
    record_artifacts(artifacts)
    return artifacts


def high_priority_group_count(groups: Optional[List[Dict[str, Any]]]) -> int:
    """Distinct HIGH-importance *groups*, not raw suggestions.

    Three models converging on the same bug is one finding, and grouping is
    what decides that; ``compute_max_importance`` is the same helper the HTML
    report ranks a group by. Counting every model's copy printed
    ``[HIGH_PRIORITY_ISSUES] 3`` for a single 3-model HIGH finding (measured
    2026-09-16).
    """
    return sum(
        1 for g in (groups or [])
        if compute_max_importance(g.get("suggestions", g.get("issues", []))) == "HIGH"
    )


def record_high_priority_groups(
    phase_dir: str, groups: Optional[List[Dict[str, Any]]]
) -> int:
    """Record the distinct-HIGH-group count where a detached caller sees it.

    Written to ``.status.json`` and onto the result line the way
    ``consolidation_recommended`` is (F4): a bare print is nothing a host
    polling ``status`` or reading only ``MULTI_LLM_RESULT`` ever sees. Only a
    non-zero count is exposed — a clean reaggregation clears the previous
    count so a detached poll cannot report findings the new review removed.
    Returns the count so the caller can print it.
    """
    count = high_priority_group_count(groups)
    data = {"count": count} if count > 0 else None
    if data or _status_file.read_status(str(phase_dir)).get("high_priority_groups"):
        update_status(str(phase_dir), {"high_priority_groups": data})
    cli_common.record_high_priority_groups(data)
    return count


#: Group ``validation_status`` → its ``validation_counts`` key (§6 T6.1). Keys
#: are snake_case (the hyphenated status string is not a good JSON key), and
#: there is no ``error`` verdict: a model may return only the first three, and
#: ``validation_failed`` is what a group carries when its batch failed every
#: attempt, or its result failed schema validation, and so has no verdict.
VALIDATION_COUNT_KEYS: Dict[str, str] = {
    "valid": "valid",
    "invalid": "invalid",
    "needs-human-decision": "needs_human_decision",
    "validation_failed": "validation_failed",
}


def validation_counts(
    groups: Optional[List[Dict[str, Any]]],
) -> Optional[Dict[str, int]]:
    """Count ``groups`` by exact ``validation_status``, or ``None`` if none has one.

    The one set of predicates behind both the report's ``**Validation:**``
    header line and the recorded ``validation_counts``, so the two cannot
    disagree. ``None`` means no validation ran over these groups (skipped, or
    nothing to validate) — not four zeros.
    """
    counts = {key: 0 for key in VALIDATION_COUNT_KEYS.values()}
    for g in groups or []:
        if not isinstance(g, dict):
            continue
        key = VALIDATION_COUNT_KEYS.get(g.get("validation_status"))
        if key:
            counts[key] += 1
    return counts if any(counts.values()) else None


def validation_counts_line(counts: Optional[Dict[str, int]]) -> Optional[str]:
    """The report's ``**Validation:**`` header line for ``counts``, or ``None``."""
    if not counts:
        return None
    return (
        f"**Validation:** {counts['valid']} valid, {counts['invalid']} invalid, "
        f"{counts['needs_human_decision']} needs human review, "
        f"{counts['validation_failed']} validation failed"
    )


def record_validation_counts(
    phase_dir: str, groups: Optional[List[Dict[str, Any]]]
) -> Optional[Dict[str, int]]:
    """Record the per-verdict group counts where a detached caller sees them.

    Written to ``.status.json`` and onto the result line the way
    ``high_priority_groups`` is, because a host summarising a finished run
    reads those two surfaces and never ``report.md`` (§6: run b38de8bb's
    summary left out its 3 needs-human-decision groups). Recomputed on every
    completion path, reaggregate included, so a revalidation that lowers a
    count lowers it here too (the previous plan's §7.2 lesson). When no group
    carries a verdict the key is **deleted** from ``.status.json`` — not
    written as ``null`` — and nothing is recorded, so ``MULTI_LLM_RESULT``
    omits it.

    Returns:
        The counts written, or ``None``.
    """
    counts = validation_counts(groups)
    if counts is None:
        _status_file.remove_status_keys(str(phase_dir), ["validation_counts"])
    else:
        update_status(str(phase_dir), {"validation_counts": counts})
    cli_common.record_validation_counts(counts)
    return counts


def exec_subagents_requested(args: Any) -> bool:
    """Whether this run drives its own subagents (D3b self-contained mode).

    A single accessor so every marker site asks the same question and the
    flag-off path stays byte-identical to what shipped before the executor.
    """
    return bool(getattr(args, "exec_subagents", False))


def _print_executor_refusal(
    failure: Any, *, phase_dir: str, retry_command: Optional[str]
) -> None:
    """The exit-3 block for a refusal that dispatched nothing (D4 step 5).

    A refused run has no batch report of its own — ``run_tasks`` never assigned
    an outcome — and a report left by an *earlier* run may still be sitting in
    the phase dir, so nothing here reads ``subagent_batch_report.json``: the
    refusal is the whole story, and the document in the directory belongs to
    another run. What the message carries in prose is printed again as
    structured lines (the reason code, the runner key and spec, the provider's
    own words — the "Did you mean" tail), then the option list: the repair
    first, the command second, the human entry last. ``.status.json`` is given
    ``{"state": "runner_rejected", "reason_code": …}`` so ``status`` and a
    detached poll describe this run rather than the one before it.
    """
    from .subagent_executor import _REASON_EXPLANATION, RunnerRejected

    print(f"ERROR: {failure.message}", file=sys.stderr)
    rejected = isinstance(failure, RunnerRejected)
    reason_code = (getattr(failure, "reason_code", "") or "") if rejected else ""
    key = (getattr(failure, "key", "") or "") if rejected else ""
    spec = (getattr(failure, "spec", "") or "") if rejected else ""
    detail = (getattr(failure, "detail", "") or "") if rejected else ""
    lines: List[str] = []
    if rejected:
        lines.append(
            f"Refused before dispatch: reason_code={reason_code or 'unknown'}"
        )
        lines.append(f"Runner: {key or 'driver.subagent_runner'} = {spec!r}")
        if detail:
            lines.append(f"Runner said: {detail}")
    # A refusal *is* a config fault (D2 step 4): shape 1, the repair first and
    # the one tool call — the caller's recorded flags plus its retry verb, which
    # `retry_command` already carries — second. `--force` is a sentence here.
    shape = cli_common.retry_shape(reason_code=reason_code or type(failure).__name__)
    explanation = (
        _REASON_EXPLANATION.get(reason_code, reason_code or "refused") if rejected
        else "fix what the message names"
    )
    if retry_command:
        options: List[str] = cli_common.retry_options(
            shape, reaggregate=retry_command, force="", repair=explanation,
        )
    else:
        options = [
            f"Repair first: {explanation}.",
            "Then re-invoke this phase with --reaggregate — it re-dispatches "
            "exactly this batch; --force is not needed and would re-run the "
            "reviewer panel.",
        ]
    options.append(
        "Otherwise report this to the user: the phase did not complete, and "
        "doing its work by hand is not a fallback."
    )
    lines.append("Options (nothing was dispatched; every result already on disk is kept):")
    lines.extend(f"  {n}. {text}" for n, text in enumerate(options, 1))
    for line in lines:
        print(line, file=sys.stderr)
    update_status(phase_dir, {
        "state": "runner_rejected" if rejected else "executor_refused",
        "reason_code": reason_code or type(failure).__name__,
        "runner": spec,
        "runner_key": key,
    })


#: The ``progress.step`` word each dispatched batch reports while it is in
#: flight, keyed by the caller's ``label``. A dispatch is the *second* long
#: stretch of a detached run — eleven validation batches ran for 62 s of a
#: 516 s ``review-plan`` (measured 2026-09-16) under a progress line still
#: reading ``grouping`` — and the executor's mirror only says how far the batch
#: has got, never that one began. Anything not listed falls back to
#: ``dispatching <label>``, which reads correctly for every label there is.
_DISPATCH_STEPS = {
    "validation": "validating",
    "revalidation": "revalidating",
    "consolidation": "consolidating",
}

#: The two labels review-tasks' validation prompt carries, spelled once. They say
#: which document is which, because the adjudication rule the prompt states ("a
#: claim that the plan or the tasks omit something is judged against the plan or
#: tasks text above") is unanswerable when both arrive as one unnamed blob.
_REVIEW_TASKS_PLAN_LABEL = "Plan — the requirements the tasks must cover"
_REVIEW_TASKS_TASKS_LABEL = "Tasks file — the artifact under review"


def validation_context_kwargs(
    phase_name: str,
    plan_content: str,
    extra_validation_metadata: Optional[Dict[str, str]],
    *,
    plan_document: Optional[BoundDocument] = None,
    phase_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """The inline context kwargs this phase's validation batches embed.

    Every phase but ``review-tasks`` embeds the plan alone, which is what the
    shared defaults already say. ``review-tasks`` validates claims **about a
    task list** — 28 of 30 suggestions on the measured 2026-09-16 run named a
    bare ``T###`` — and it was handed the plan and nothing else, so `'T001' in
    prompt` was `False` for every batch while the prompt told the validator to
    judge those claims "against the plan or tasks text above". Two verdicts came
    back citing text no validator had been given: one quoting a phrase that
    exists only in `tasks.md`, one citing `plan_preamble`, a `state.json`
    bookkeeping field. So this phase embeds both documents, each labelled.

    The tasks text is read here rather than threaded through as content because
    ``extra_validation_metadata`` already carries its path for the file
    envelope; an unreadable file degrades to the plan-only context (the batch
    still validates) rather than failing a completed fan-out.

    §2.3 step 5/7: ``plan_document`` is the round's bound plan (one read, one
    snapshot); its text is the context and it rides along as
    ``context_document``. With ``phase_dir`` the tasks file is bound the same
    way — read once as bytes, reusing ``tasks-backup.md`` when its sha256
    matches, else snapshotted to ``validation-tasks-snapshot.md`` — and rides
    as ``secondary_document``.
    """
    if plan_document is not None:
        plan_content = plan_document.text
    kwargs: Dict[str, Any] = {"context": plan_content}
    if plan_document is not None:
        kwargs["context_document"] = plan_document
    if phase_name != "review-tasks":
        return kwargs
    tasks_file = (extra_validation_metadata or {}).get("tasks_file") or ""
    if not tasks_file:
        return kwargs
    tasks_document: Optional[BoundDocument] = None
    try:
        if phase_dir:
            tasks_document = bind_document_file(
                tasks_file, phase_dir, label="tasks",
                snapshot_name=TASKS_SNAPSHOT_NAME,
                reuse_names=(TASKS_BACKUP_NAME,),
            )
            tasks_content = tasks_document.text
        else:
            tasks_content = Path(tasks_file).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError, ValidationContextError) as exc:
        print(
            f"Warning: could not read {tasks_file} for validation context "
            f"({exc}); validating against the plan alone.",
            file=sys.stderr,
        )
        return kwargs
    kwargs["context_label"] = _REVIEW_TASKS_PLAN_LABEL
    kwargs["secondary_context"] = tasks_content
    kwargs["secondary_context_label"] = _REVIEW_TASKS_TASKS_LABEL
    if tasks_document is not None:
        kwargs["secondary_document"] = tasks_document
    return kwargs


def _path_under(path: str, root: str) -> bool:
    real_root = os.path.realpath(root)
    real = os.path.realpath(path)
    return real == real_root or real.startswith(real_root.rstrip(os.sep) + os.sep)


class _NativeReadAdvisory:
    """The native-host read check: refuses nothing, flags an out-of-root path.

    Called as a refusal it always answers ``None`` (the host's own subagent
    reads, and its permissions are not ours to predict), and it sets
    ``advisory_only`` so a caller that would otherwise impose its own refusal
    still does. :meth:`advisory` is asked for every ``mode: path`` source: for
    one outside the plan's project root it prints one notice line (once per
    path) and returns the ``reason`` the source records. The root is resolved
    on first use, and a root that cannot be resolved flags nothing.
    """

    advisory_only = True

    def __init__(self, plan_path: str) -> None:
        self.plan_path = plan_path
        self._root: Optional[str] = None
        self._resolved = False
        self._noticed: set = set()

    @property
    def root(self) -> Optional[str]:
        if not self._resolved:
            self._resolved = True
            try:
                self._root = get_project_root(self.plan_path)
            except Exception:  # noqa: BLE001 - an advisory never fails a round
                self._root = None
        return self._root

    def __call__(self, path: Optional[str]) -> Optional[str]:
        return None

    def advisory(self, path: Optional[str]) -> Optional[str]:
        if not path or not self.root or _path_under(path, self.root):
            return None
        reason = (
            f"{path} is outside the project root {self.root}: the host's "
            f"subagent may be denied Read on it, and every verdict for this "
            f"round may come back insufficient-context"
        )
        if path not in self._noticed:
            self._noticed.add(path)
            print(f"[VALIDATION_CONTEXT_OUTSIDE_ROOT] {reason}", file=sys.stderr)
        return reason


def materialization_read_refusal(args: Any, plan_path: str) -> Optional[Any]:
    """Who will read a validation batch's snapshot, decided at materialization (§2.3 step 4a).

    ``None`` on a native-subagent host (the host's own subagent reads, and the
    one native host that validates, Claude Code, has a read tool) and whenever
    the executor's runner cannot be resolved here (the dispatch-time refusal is
    the backstop). Under ``--exec-subagents`` it resolves the runner the
    executor will use for a validation task and returns a callable: a runner
    that declares no ``supports_workspace_reads`` refuses every path, and one
    that cannot read outside its cwd and cannot widen its read scope
    (``read_scope_flag``) refuses a snapshot outside the project root. A
    refused source materializes ``mode: truncated`` with that reason — decided
    before dispatch, and always reported.

    On the native path it refuses nothing, but a snapshot outside
    ``get_project_root(plan_path)`` (a plan kept outside the repo) may be one
    the host's subagent is denied ``Read`` on, with no ``--add-dir`` to widen
    it. The returned :class:`_NativeReadAdvisory` then prints a one-line notice
    and records a ``reason`` on that ``mode: path`` source, so an operator
    whose every verdict came back ``insufficient-context:`` learns why.
    """
    if not exec_subagents_requested(args):
        return _NativeReadAdvisory(plan_path)
    try:
        from .subagent_executor import resolve_task_runner
        from .provider_registry import get_provider, parse_model_spec

        spec = resolve_task_runner(
            {
                "task_id": "validation-batch-0",
                "kind": "validation",
                "capability_tier": "full",
                "model_hint": getattr(args, "validation_model", None) or "auto",
            },
            anchor=plan_path,
        )
        provider_name, _model = parse_model_spec(spec, anchor=plan_path)
        provider = get_provider(provider_name)
    except Exception:  # noqa: BLE001 - dispatch-time refusal is the backstop
        return None
    if provider is None:
        return None
    if not getattr(provider, "supports_workspace_reads", False):
        return f"runner {spec} cannot read files"
    if getattr(provider, "reads_outside_cwd", False) or getattr(
        provider, "read_scope_flag", None
    ):
        return None
    root = get_project_root(plan_path)

    def refusal(path: Optional[str]) -> Optional[str]:
        if not path or not root:
            return None
        if _path_under(path, root):
            return None
        return (
            f"runner {spec} cannot read {path}: it is outside the runner's "
            f"working directory and the adapter cannot widen its read scope"
        )

    return refusal


def bind_plan_for_validation(
    plan_path: str, phase_dir: str, *, data: Optional[bytes] = None
) -> BoundDocument:
    """The round's one read of the plan, bound to ``validation-snapshot.md`` (§2.3 step 5).

    Every validating phase (review-plan, review-tasks, review-code) calls this
    at load, the same way, so the plan block of every phase names that phase
    dir's own snapshot — never the live plan and never ``backup.md``. A plan
    that does not decode as UTF-8 refuses the round (exit 3) instead of hashing
    to ``""``.

    ``data`` is the plan's bytes when the caller already read them (the
    pre-flight decode check of a fan-out that binds only past its detach
    boundary), so the snapshot is still the one read the excerpt came from.
    """
    try:
        return bind_document_file(
            plan_path, phase_dir, label="plan", snapshot_name=PLAN_SNAPSHOT_NAME,
            data=data,
        )
    except ValidationContextError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(exc.exit_code)


def verify_round_context(
    document: Dict[str, Any], phase_dir: str, task_file: Optional[str] = None
) -> None:
    """Verify (and, for a moved phase dir, rebind) a round's snapshots, or exit 3.

    Run right before dispatch and on every resume/``--reaggregate`` that
    reuses a materialized round (§2.3 step 5, task 2.9). A rebound document is
    persisted with its sidecars, so a native host reading the JSON sees the
    same prompt the executor dispatches.
    """
    try:
        rebound = verify_context_sources(document, phase_dir)
    except ValidationContextError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(exc.exit_code)
    if rebound:
        ensure_prompt_sidecars(document, phase_dir)
        if task_file:
            from .subagent_executor import _atomic_write_json

            try:
                _atomic_write_json(task_file, document)
            except OSError as exc:
                print(
                    f"ERROR: Could not persist the rebound prompts to "
                    f"{task_file}: {exc}. Nothing was dispatched.",
                    file=sys.stderr,
                )
                sys.exit(3)


def dispatch_subagent_tasks(
    args: Any,
    *,
    task_file: str,
    phase_dir: str,
    phase: str,
    document: Optional[Dict[str, Any]] = None,
    plan_path: Optional[str] = None,
    label: str = "subagent",
    retry_command: Optional[str] = None,
) -> bool:
    """Run a materialized batch through the executor, or decline (D3b).

    Returns ``False`` when neither ``--exec-subagents`` nor ``--dry-run-subagents``
    was requested (the caller then prints its marker and follow-up command exactly
    as before), ``True`` when every task produced a schema-valid result file and
    the caller may continue in-process. A partial batch exits **3** here — even
    under ``--yes`` — rather than letting the phase reaggregate a short set.

    **Synchronous, and it blocks for the whole batch.** ``continue_past_marker``
    ends in ``subagent_executor._run_sync``, which — inside a running loop —
    submits ``asyncio.run`` to a worker thread and then *waits on the result*,
    so calling this from a coroutine pins the event loop for the entire
    validation window and starves anything living on it, the phase-scoped
    ``[PROGRESS]`` ticker included (F6, 2026-09-20: the executor lane got
    exactly one line for that window, the teardown one, under three comments
    claiming the second ticker covered it). Every caller on an async lane
    therefore reaches it through ``await asyncio.to_thread(...)``. The function
    stays sync because the sync lanes — the apply base, the consolidation
    handler, ``generate-tasks`` — call it directly, and ``_run_sync`` handles
    the no-loop case itself.

    ``--dry-run-subagents`` is an executor request **in its own right** (D3l), the
    same way the write twin ``write_batch_scheduler.run_write_phase`` treats it:
    it renders the preflight report and returns ``False``, so the phase still
    prints its native marker. Gating it behind ``--exec-subagents`` would make a
    standalone dry run silently fall back to the native marker on every read,
    generation, consolidation and judging phase — no child *and* no report, which
    is the one outcome the flag must never produce.
    """
    dry_run = bool(getattr(args, "dry_run_subagents", False))
    if not exec_subagents_requested(args) and not dry_run:
        return False
    from .subagent_executor import (
        BatchFailed,
        ExecutorError,
        continue_past_marker,
        dry_run_report,
    )

    project_root = get_project_root(plan_path) if plan_path else None
    try:
        if dry_run:
            report = dry_run_report(
                task_file,
                phase_dir=phase_dir,
                phase=phase,
                document=document,
                anchor=plan_path,
                cwd=project_root,
            )
            print(
                f"[dry-run-subagents] {report} — every {label} command rendered, "
                f"no child started, nothing else changed. This phase still prints "
                f"its marker and its follow-up command."
            )
            return False
        # §2.3 step 5: right before dispatch, re-hash every snapshot a
        # validation prompt names (and rebind a moved phase dir); a snapshot
        # that moved or vanished since materialization refuses the round.
        if document is not None and label in ("validation", "revalidation"):
            verify_round_context(document, phase_dir, task_file)
        # Reported before the dispatch, not after it: `report_progress` merges
        # into `progress`, so the step stands while the executor's mirror fills
        # in underneath it (`validating, validation 3/11 ok`).
        _detach.report_progress(
            phase_dir, step=_DISPATCH_STEPS.get(label, f"dispatching {label}")
        )
        return continue_past_marker(
            args,
            task_file=task_file,
            phase_dir=phase_dir,
            phase=phase,
            document=document,
            anchor=plan_path,
            cwd=project_root,
            label=label,
            retry_command=retry_command,
        )
    except BatchFailed as failure:
        print(failure.message, file=sys.stderr)
        update_status(phase_dir, {"state": "subagents_failed"})
        sys.exit(failure.exit_code)
    except ExecutorError as failure:
        _print_executor_refusal(
            failure, phase_dir=phase_dir, retry_command=retry_command
        )
        sys.exit(failure.exit_code)


#: Why a salvage pair stopped being outstanding work. The word lands in the
#: retired filename, so ``ls`` on a phase dir says which of the two rules moved
#: it: ``superseded`` — a fresh attempt for that model began, so the request
#: describes an answer that no longer exists; ``unrecoverable`` — the executor
#: read the subagent's ``{"salvage_failed": true, …}`` sentinel and filed the
#: dispatch ``salvage_unrecoverable``, a verdict that is in none of the ladder's
#: retry sets and will therefore never change.
RETIRE_SUPERSEDED = "superseded"
RETIRE_UNRECOVERABLE = "unrecoverable"


def retired_salvage_name(name: str, reason: str, stamp: str) -> str:
    """The name a retired ``salvage_*.json`` takes: ``retired_`` + why + when.

    The prefix is load-bearing rather than decorative. Three globs decide what
    is still outstanding — ``dispatch_salvage_tasks``'s ``salvage_task_*.json``
    below, ``code_review_orchestrator``'s ``salvage_*.json`` end-of-run scan,
    and the ``salvage_task_`` filter it applies to that scan — and every one of
    them is prefix-anchored, so anything still *starting* ``salvage_`` is still
    outstanding no matter what is appended to it. Renaming to
    ``salvage_<model>.retired.json`` would keep the artifact in all three and
    hand the end-of-run block a model called ``<model>.retired`` on top.
    Conversely every reaggregation glob excludes a basename *containing*
    ``salvage`` (here at ``reaggregate_from_existing_files`` and in
    ``code_review_orchestrator.reaggregate_from_existing_files``), so keeping
    the word inside the new name is what stops a retired request being read back
    as a model result — which, since a salvage request is a JSON object rather
    than a suggestion array, is a crash rather than a miscount.
    """
    stem = name[: -len(".json")] if name.endswith(".json") else name
    return f"retired_{stem}.{reason}.{stamp}.json"


def retire_salvage_artifacts(
    phase_dir: str,
    sanitized_model: str,
    *,
    reason: str,
    quiet: bool = False,
) -> List[Tuple[str, str]]:
    """Take one model's ``salvage_<model>.json`` + ``salvage_task_<model>.json`` out of play.

    A salvage task's ``output_name`` **is** the model's own result file
    (``utils/subagent_tasks.write_salvage_task_file``), so anything persisted
    there becomes that model's review and reaggregation scores it as one more
    model that flagged a finding (``SuggestionGroup._recalculate_priority`` sums
    ``len(self.models)``). ``has_salvageable_json`` decides whether *this*
    attempt asks for a salvage at all, and the ``salvage_failed`` sentinel
    decides that a dispatched one recovered nothing — but neither of them can
    see an *earlier* attempt's pair still lying in the phase dir. ``get_phase_dir``
    is stable per plan, the two globs above take whatever is in it, and
    ``--force`` clears only the state file's phase-completion marker; it deletes
    nothing from disk. So the pair outlives the decision that produced it, and
    the phantom participant walks in by a route the gate never sees.

    Retiring is a **rename, never a delete**: the request holds the raw output
    the model actually produced, which is the evidence an operator needs to tell
    a truncated answer from a dead account, and the run that supersedes it is
    usually the run that wants to compare. The new name is
    :func:`retired_salvage_name`'s, whose prefix is what removes it from the
    globs.

    Deliberately non-fatal, and loud when it fails. Refusing to run a fan-out
    because a bookkeeping rename failed would cost the operator every model's
    review over a file permission; leaving the failure silent would put the
    phantom back with nothing on screen to connect it to. So a failed rename
    warns on stderr naming the file that survived, and the run continues.

    Args:
        phase_dir: The phase directory both artifacts live in.
        sanitized_model: ``sanitize_model_name(model_spec)`` — the stem both
            filenames are built from, and the stem of the model result file the
            salvage would write to.
        reason: :data:`RETIRE_SUPERSEDED` or :data:`RETIRE_UNRECOVERABLE`.
        quiet: Suppress the per-file ``[SALVAGE_RETIRED]`` line. Set by the
            attempt-start caller, where the interesting event is the attempt and
            a retirement line per re-run model would drown the fan-out.

    Returns:
        ``(old_path, new_path)`` for each artifact actually renamed, in
        request-then-task order. Empty when there was nothing to retire, which
        is the ordinary case: most attempts follow an attempt that parsed.
    """
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    retired: List[Tuple[str, str]] = []
    for name in (
        f"salvage_{sanitized_model}.json",
        f"salvage_task_{sanitized_model}.json",
    ):
        source = os.path.join(phase_dir, name)
        if not os.path.exists(source):
            continue
        target = os.path.join(phase_dir, retired_salvage_name(name, reason, stamp))
        # Two attempts for the same model inside one second is not a scenario
        # anybody plans, but the second rename would silently destroy the first
        # artifact — the one thing renaming instead of deleting exists to avoid.
        suffix = 2
        while os.path.exists(target):
            target = os.path.join(
                phase_dir,
                retired_salvage_name(name, reason, f"{stamp}-{suffix}"),
            )
            suffix += 1
        try:
            os.replace(source, target)
        except OSError as rename_error:  # noqa: PERF203 - one message per file
            print(
                f"Warning: could not retire {name} ({rename_error}); it is still "
                f"in {phase_dir} and will be dispatched and advertised as though "
                f"it were this run's",
                file=sys.stderr,
            )
            continue
        retired.append((source, target))
        if not quiet:
            print(f"[SALVAGE_RETIRED] {os.path.basename(target)} ({reason})")
    return retired


#: Basenames that are never a per-model result file (defined in the leaf
#: ``utils/result_files.py``, which the slot's misnamed-result lookup in
#: ``llm_client`` needs too; re-exported here under the name callers use).
NON_MODEL_JSON_MARKERS = _result_files.NON_MODEL_JSON_MARKERS

#: Suffix of a result retired because its model left the selection.
RETIRED_UNSELECTED = "stale-unselected"


def _effort_vocabulary(provider_name: str) -> FrozenSet[str]:
    """The ``:effort`` names a spec for *provider_name* may carry.

    The adapter's own ``EFFORT_LADDER`` (``accepted_inbound``: what a spec may
    say, aliases included), the way ``LLMProvider._accepted_efforts`` reads it.
    A provider with no adapter or no ladder (a test double) gets the canonical
    rungs, so ``codex:x`` → ``codex:x:high`` is still recognised as a respelling
    whatever the registry holds.
    """
    provider = get_provider(provider_name)
    module = sys.modules.get(type(provider).__module__) if provider else None
    ladder = getattr(module, "EFFORT_LADDER", None)
    try:
        names = ladder.accepted_inbound if ladder is not None else None
    except Exception:  # noqa: BLE001 - a ladder is data; never fail a retire on it
        names = None
    return frozenset(names) if names else LADDER_RUNGS


def respelled_result_stems(model_specs: Sequence[str]) -> Dict[str, str]:
    """``{stem: selected spec}`` for every result stem that is a *respelling*
    of a selected spec: the same provider and model under another effort
    suffix, or none (``codex_gpt-6-luna`` and ``codex_gpt-6-luna_low`` for a
    selected ``codex:gpt-6-luna:high``). A selected spec's own stem is never
    listed. Only an effort suffix the provider's ladder names counts, because
    a model id may itself end in ``:<word>`` (openrouter ``:free``).
    """
    selected = {sanitize_model_name(spec) for spec in model_specs}
    respelled: Dict[str, str] = {}
    for spec in model_specs:
        provider_name, _, model = spec.partition(":")
        if not model:
            continue
        efforts = _effort_vocabulary(provider_name)
        base, _effort = split_reasoning_effort(model, efforts)
        for variant in (f"{provider_name}:{base}", *(f"{provider_name}:{base}:{e}" for e in sorted(efforts))):
            stem = sanitize_model_name(variant)
            if stem not in selected:
                respelled.setdefault(stem, spec)
    return respelled


def retire_unselected_results(
    phase_dir: str, model_specs: Sequence[str]
) -> List[str]:
    """Rename the per-model results (and logs) of a selected spec's respellings.

    Stale detection elsewhere is keyed by the *slot* (``<stem>.json`` and the
    scope ledger), so a model whose spec changed between runs --
    ``codex:gpt-6-luna`` becoming ``codex:gpt-6-luna:high`` -- leaves
    ``codex_gpt-6-luna.json`` and ``log_codex_gpt-6-luna.txt`` behind beside the
    new slot's files (measured 2026-10-02, Codex ``review-code``). The fan-out's
    own report is built from this run's results, so nothing leaked there, but
    the next ``--reaggregate`` globs the phase dir and would count the old
    model's findings in a report whose ``models_requested`` never named it.

    Only a **respelling** of a selected spec is retired (same provider and
    model, another effort suffix or none: :func:`respelled_result_stems`),
    never every stem outside the selection. The first version retired
    everything unselected, and the documented resume -- "re-run only the
    missing models with ``--force``", which a host spells as ``--models
    <missing>`` -- then renamed every completed model's result and log
    ``.stale-unselected``, so the resumed report covered the subset and no
    later ``--reaggregate`` could see the rest (adversarial review,
    2026-10-02; the previous ``.status.json`` is no guard, because the
    fan-out has already replaced ``models_requested`` by the time this runs).
    A result of a model that simply left the selection stays, as it did
    before #30: the fan-out's report never read it. (Since fix round 24 a
    ``--reaggregate`` does not read it either: it reads only the models
    ``.status.json`` records and sets any other result file aside, named,
    ``utils/result_files.set_aside_unrecorded_results``.)

    Called by a **fan-out** only, with the run's selection, before any model
    starts. ``--reaggregate`` never calls it. Same naming as
    ``retire_result_from_another_scope``: ``<stem>.json.stale-unselected``,
    renamed and never deleted, no longer matching ``*.json``; the log follows
    as ``log_<stem>.txt.stale-unselected``. Only a file whose body is a JSON
    list is a result: an unreadable or non-list file is left alone, because
    renaming something this function cannot identify would be the guess.

    Returns:
        The new result-file paths (logs are renamed with them, not listed).
    """
    respelled = respelled_result_stems(model_specs)
    retired: List[str] = []
    for path in sorted(Path(phase_dir).glob("*.json")):
        name = path.name
        if any(marker in name for marker in NON_MODEL_JSON_MARKERS):
            continue
        stem = name[: -len(".json")]
        if stem not in respelled:
            continue
        try:
            if not isinstance(json.loads(path.read_text(encoding="utf-8")), list):
                continue
        except (OSError, ValueError):
            continue
        moved = [(path, path.with_name(f"{name}.{RETIRED_UNSELECTED}"))]
        log = path.with_name(f"log_{stem}.txt")
        if log.exists():
            moved.append((log, log.with_name(f"{log.name}.{RETIRED_UNSELECTED}")))
        for source, target in moved:
            if target.exists():
                target = target.with_name(
                    f"{target.name}.{datetime.now().strftime('%Y%m%dT%H%M%S%f')}"
                )
            try:
                os.replace(source, target)
            except OSError as exc:
                print(
                    f"Warning: could not retire {source.name} (model respelled "
                    f"as {respelled[stem]} in this run's selection): {exc}",
                    file=sys.stderr,
                )
                break
        else:
            retired.append(str(moved[0][1]))
            print(
                f"[SELECTION_CHANGED] {stem}: respelled as {respelled[stem]} in "
                f"this run's selection; retired {name} as {moved[0][1].name}"
            )
    return retired


def retire_stale_validation(phase_dir: str, *, reason: str) -> Optional[str]:
    """Rename ``validation.json`` to ``validation.<stamp>.stale.json`` (D7).

    A ``validation.json`` is a set of verdicts about one grouping. Two events
    make it stale: the grouping is rewritten (``grouped.json`` overwritten by a
    re-run, where this is called *in the same step* as the write), and a
    reaggregate finds that the file does not bind to the ``grouped.json`` it
    sits beside (``stale_validation_reason``). Before D7 the file survived both
    and ``reaggregate_from_existing_files`` trusted it ahead of the batch files
    it had been superseded by — exit 0, no warning, and a report carrying
    another grouping's verdicts.

    A rename, never a delete: the verdicts are still evidence of what a model
    said about the groups it was shown. The new name keeps ``validation`` in
    its basename, so every reaggregation glob's ``exclude_patterns`` still
    skips it, and no longer *is* ``validation.json``, so nothing honours it.
    Non-fatal like ``retire_salvage_artifacts``: a failed rename warns on
    stderr naming the file that survived.

    Returns:
        The new path, or ``None`` when there was nothing to retire (or the
        rename failed).
    """
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return _retire_stale_file(phase_dir, "validation.json", reason=reason, stamp=stamp)


def _retire_stale_file(
    phase_dir: str, name: str, *, reason: str, stamp: str
) -> Optional[str]:
    """Rename one validation artifact to ``<stem>.<stamp>.stale<ext>`` (D7).

    The naming rule :func:`retire_stale_validation` established, factored out
    so the task file and the batch files retire under the same shape as the
    merged file — an operator who knows what ``validation.<stamp>.stale.json``
    means reads ``validation_batch_0.<stamp>.stale.json`` without a second
    convention. Every such name keeps ``validation`` in its basename, which is
    what every reaggregation glob's ``exclude_patterns`` keys on.

    The extension is taken from the name rather than assumed to be ``.json``:
    a prompt sidecar (``validation_batch_0.prompt.txt``) retires as
    ``validation_batch_0.prompt.<stamp>.stale.txt``, not as a ``.txt`` wearing a
    ``.json`` suffix. Output for every ``.json`` name is byte-identical to what
    the hard-coded rule produced.
    """
    source = os.path.join(phase_dir, name)
    if not os.path.exists(source):
        return None
    stem, ext = os.path.splitext(name)
    target = os.path.join(phase_dir, f"{stem}.{stamp}.stale{ext}")
    suffix = 2
    while os.path.exists(target):
        target = os.path.join(phase_dir, f"{stem}.{stamp}-{suffix}.stale{ext}")
        suffix += 1
    try:
        os.replace(source, target)
    except OSError as rename_error:
        print(
            f"Warning: could not retire {name} ({rename_error}); it is "
            f"still in {phase_dir} and does not belong to the current grouping",
            file=sys.stderr,
        )
        return None
    print(f"[VALIDATION_RETIRED] {os.path.basename(target)} ({reason})")
    return target


def retire_stale_validation_round(phase_dir: str, *, reason: str) -> List[str]:
    """Retire every artifact of one validation round: the merged file, the task
    file and the batch replies (D7, extended 2026-09-17).

    :func:`retire_stale_validation` moves ``validation.json`` alone, which is
    the right scope at the fan-out's regroup: the fresh ``validation_tasks.json``
    is written a few lines later and overwrites the old one. It is the wrong
    scope for a reaggregate that has to regroup a dir *already* carrying a
    materialized round, because the task file is hash-bound to the grouping
    being replaced (``inputs.grouped_sha256``) and the batch files are that
    grouping's verdicts, joined by ``group_hash``. Leave either behind and the
    very next step refuses itself — ``read_task_file`` sees the moved hash and
    exits 3 — or a stale ``validation_batch_<n>.json`` is read back into the
    new round's batch of the same index. Measured 2026-09-17 on a real
    ``review-code --quick``: a model result that landed after grouping could
    only be folded in by renaming all three by hand (``validation.json``,
    ``validation_tasks.json``, ``validation_batch_*.json`` →
    ``*.20260917-025330.stale.json``) and reaggregating twice.

    One stamp for the whole round, so ``ls`` groups them. A rename, never a
    delete; non-fatal per file, as the single-file helper is.

    Returns:
        The new paths, in ``validation.json``, ``validation_tasks.json``,
        batch-index, then prompt-sidecar order. Empty when nothing was on disk.
    """
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    names = ["validation.json", "validation_tasks.json"]
    batch_names = sorted(
        (
            os.path.basename(path)
            for path in Path(phase_dir).glob("validation_batch_*.json")
            if not os.path.basename(path).endswith(".stale.json")
        ),
        key=lambda name: (len(name), name),
    )
    # The prompt sidecars belong to the grouping their batch does: left behind,
    # they would describe a retired round beside the fresh one, and the only
    # reader that finds them is a host following `prompt_path`.
    sidecar_names = sorted(
        (
            os.path.basename(path)
            for path in Path(phase_dir).glob("validation_batch_*.prompt.txt")
            if ".stale." not in os.path.basename(path)
        ),
        key=lambda name: (len(name), name),
    )
    retired: List[str] = []
    for name in names + batch_names + sidecar_names:
        target = _retire_stale_file(phase_dir, name, reason=reason, stamp=stamp)
        if target:
            retired.append(target)
    return retired


def _recorded_group_hashes(grouped_path: str) -> Optional[FrozenSet[str]]:
    """The ``group_hash`` set of the ``grouped.json`` on disk, or ``None``.

    ``None`` when there is no readable file, or when any group carries no hash
    (a pre-stamping v1 file): an unknown grouping is a different grouping.
    """
    try:
        with open(grouped_path, "r", encoding="utf-8") as handle:
            groups = load_groups_payload(json.load(handle))
    except (OSError, ValueError, TypeError):
        return None
    hashes = []
    for group in groups:
        ghash = group.get("group_hash") if isinstance(group, dict) else None
        if not ghash:
            return None
        hashes.append(str(ghash))
    return frozenset(hashes)


def retire_validation_for_regroup(
    phase_dir: str, grouped: List[Dict[str, Any]], *, reason: str
) -> List[str]:
    """Retire the verdicts the fan-out's regroup orphans, and no more (D7).

    *grouped* is the stamped grouping about to overwrite ``grouped.json``.
    When its ``group_hash`` set differs from the file on disk (or there is no
    readable, stamped file) the whole round goes --
    :func:`retire_stale_validation_round` -- because a surviving
    ``validation_batch_<n>.json`` of another grouping is skipped as "already
    complete" by the executor and then discarded by the merge as a foreign
    ``group_hash`` (#25, 2026-10-02). When the sets are **equal** the batch
    files are that grouping's own verdicts, so only ``validation.json`` is
    retired, as before #25: a ``--force`` resume that skips every model
    regroups deterministically to the same hashes, and retiring the round
    there re-dispatched every completed batch -- after one batch timed out
    under ``--exec-subagents``, or when a host ran ``--force`` where
    ``--reaggregate`` was meant (adversarial review, 2026-10-02). The
    executor's own ``_result_names_foreign_groups`` still re-dispatches any
    stale batch the equal-set case leaves behind. The comparison is on the
    grouping alone: a plan edited between the rounds moves the task file's
    ``inputs.plan_sha256``, which is the task file's refusal to make.
    """
    current = frozenset(
        str(group.get("group_hash"))
        for group in grouped
        if isinstance(group, dict) and group.get("group_hash")
    )
    previous = _recorded_group_hashes(os.path.join(phase_dir, "grouped.json"))
    if previous is not None and previous == current and len(current) == len(grouped):
        target = retire_stale_validation(phase_dir, reason=reason)
        return [target] if target else []
    return retire_stale_validation_round(phase_dir, reason=reason)


def grouped_coverage_gap(
    grouped: List[Dict[str, Any]],
    results_by_model: Dict[str, List[Dict[str, Any]]],
) -> List[str]:
    """Where ``grouped.json`` and the per-model result files disagree, or ``[]``.

    The reaggregate paths reuse a ``grouped.json`` that validation artifacts
    are bound to ("preserves validation alignment") on the premise that it
    still describes the results on disk. It does not when a per-model file
    landed *after* grouping — a salvage written by the host after the fan-out
    returned at ``[VALIDATION_BATCHES_PENDING]``, or a result obtained out of
    band for a model the fan-out recorded as failed. Reusing the file then
    excludes that model from every group while ``results`` still lists it:
    measured 2026-09-17, the report would have said ``Total Issues: 8`` over
    ``Groups: 4`` covering five of them, and ``apply-code-fixes`` could place
    none of the other three.

    The comparison is by content, not by count or by filename: the multiset of
    ``(model stem, suggestion content hash)`` pairs on each side, the hash
    being :func:`state_manager.generate_suggestion_id`'s plain (undiscriminated)
    form and the stem ``sanitize_model_name`` of the spec, so a dir whose
    checkpoint is missing — where ``resolve_result_files_by_model`` names the
    model by its stem while ``grouped.json`` carries the canonical spec — still
    compares equal. Extra keys a later release stamps on an issue do not enter
    the hash, so a byte-divergent round trip (the case
    ``TestReaggregateReusesTheGroupedFileValidationIsBoundTo`` pins) is not a
    gap either.

    A ``grouped.json`` whose suggestions carry no model attribution at all is
    older than anything this can reason about; the comparison is inconclusive
    and the caller keeps today's behaviour rather than regrouping on a guess.

    Args:
        grouped: The groups as loaded from ``grouped.json`` (plain dicts).
        results_by_model: ``{model: [issue, ...]}`` for every result file the
            reaggregate read — one entry per logical model.

    Returns:
        One line per model that differs, naming what is on disk and not in
        the file and the reverse; empty when the two agree.
    """
    from collections import Counter

    from .state_manager import generate_suggestion_id

    in_file: Dict[str, Counter] = {}
    spec_by_stem: Dict[str, str] = {}
    for group in grouped:
        for suggestion in group.get("suggestions", group.get("issues", [])) or []:
            spec = suggestion.get("source_model") or suggestion.get("model")
            if not spec:
                return []
            stem = sanitize_model_name(str(spec))
            spec_by_stem.setdefault(stem, str(spec))
            in_file.setdefault(stem, Counter())[generate_suggestion_id(suggestion)] += 1

    on_disk: Dict[str, Counter] = {}
    for spec, issues in results_by_model.items():
        stem = sanitize_model_name(str(spec))
        spec_by_stem[stem] = str(spec)
        counter = on_disk.setdefault(stem, Counter())
        for issue in issues or []:
            counter[generate_suggestion_id(issue)] += 1

    lines: List[str] = []
    for stem in sorted(set(in_file) | set(on_disk)):
        disk = on_disk.get(stem, Counter())
        bound = in_file.get(stem, Counter())
        added = sum((disk - bound).values())
        gone = sum((bound - disk).values())
        if added or gone:
            lines.append(
                f"{spec_by_stem[stem]}: {added} issue(s) on disk not in "
                f"grouped.json, {gone} in grouped.json not on disk"
            )
    return lines


def record_models_present(phase_dir: str, models: List[str]) -> List[str]:
    """Reconcile the checkpoint's model outcomes with the result files on disk.

    ``models_completed`` / ``models_failed`` are the fan-out's record of the
    run it drove, and the fan-out is the only writer. A reaggregate reads the
    per-model files, and a model whose file is there now — a salvage the host
    ran after the marker, or a result obtained out of band — has completed as
    far as every consumer of that file is concerned: the report lists it under
    ``**Models:**`` and its issues are grouped and validated. Measured
    2026-09-17: after such a reaggregate the report named three models while
    ``.status.json`` still carried the third under ``models_failed`` with its
    sandbox error, and ``progress.models_done`` read ``2/5``.

    Only a checkpoint that records outcomes at all is touched (a dir with no
    ``.status.json``, or one that never got the fields, gains nothing — same
    field-not-file rule as ``build_unsanitize_map``), and only the models with
    a file are moved: a model the fan-out completed whose file has since gone
    keeps its entry, because the record of what the fan-out did is not this
    function's to rewrite.

    **It writes ``models_succeeded``, not ``models_done``.** Its number is a
    count of *completed results*, which is what the post-fan-out restatements
    compute; ``models_done`` counts finished **slots** and the salvaged model's
    slot finished long ago — as ``failed``. So flipping that entry to ``done`` /
    ``source: existing_file`` moves the success count and not the terminal
    count, and the map and the two derived numbers stay in agreement. This
    writer holds no in-memory map (it is a ``--reaggregate``'s recompute, one
    process later), so it reads the map back off the checkpoint and writes it
    whole; a counts-only write is safe beside it because ``progress`` merges key
    by key at its top level and **only a write carrying a ``models`` key
    replaces the map**.

    Returns:
        The models moved out of ``models_failed``, so the caller can say so.
    """
    status = _status_file.read_status(phase_dir)
    if "models_completed" not in status and "models_failed" not in status:
        return []
    completed = list(status.get("models_completed") or [])
    failed = dict(status.get("models_failed") or {})
    recovered: List[str] = []
    changed = False
    for model in models:
        if model in failed:
            del failed[model]
            recovered.append(model)
            changed = True
        if model not in completed:
            completed.append(model)
            changed = True
    if not changed:
        return []
    update_status(phase_dir, {
        "models_completed": completed,
        "models_failed": failed,
    })
    progress = status.get("progress")
    if isinstance(progress, dict) and progress.get("models_total"):
        updates: Dict[str, Any] = {"models_succeeded": len(completed)}
        models_map = progress.get("models")
        if isinstance(models_map, dict) and flip_map_entries_to_done(
            models_map, models
        ):
            updates["models"] = models_map
        _status_file.update_progress(phase_dir, updates)
    return recovered


def flip_map_entries_to_done(
    models_map: Dict[str, Any],
    models: Sequence[str],
    *,
    source: str = "existing_file",
) -> bool:
    """Move each named ``progress.models`` entry to ``done``/*source*.

    The one rule for "this slot's verdict changed after the fan-out froze it",
    shared by the two events that can change one: a ``--reaggregate`` finding a
    result file the fan-out never saw (:func:`record_models_present`) and an
    in-process salvage repairing one (:func:`record_models_salvaged`). Mutates
    *models_map* in place and reports whether anything moved, so the caller can
    decide whether its write needs to carry a ``models`` key at all.

    ``ended_at``/``elapsed_s``/``queued_s`` are left exactly as the fan-out (or
    an abort's close-out) froze them **on an entry that was already
    terminal**: that slot really did end when it ended, and this is a later
    reading of the same slot's outcome, not a second run of it. Only the
    verdict and its provenance move — and ``error`` is popped, because it is
    terminal-and-failed-only and a ``done`` row carrying one is the
    contradiction this whole function exists to remove.

    **A non-terminal entry has no ending to preserve, so it is given one**
    (2026-09-21). A ``--reaggregate`` can meet a map that still holds a
    ``queued``/``staggering``/``running`` row — a run killed with no close-out
    on the foreground lane, where neither the fan-out's sweep nor
    ``progress_tracker.retire_live_entries`` ever ran, or a hand-written file —
    and flipping that row to ``done`` while leaving ``ended_at`` absent leaves
    ``entry_elapsed_s`` on its *live* branch forever, recomputed at every read,
    so the table renders a finished model whose clock is still running and
    stops only when it hits the slot's own budget. So the row is closed out by
    the dispatch-origin rule all three close-out writers share
    (``FanoutProgress._freeze``, ``retire_live_entries`` and this), on the
    wall clock because this process holds no monotonic origin for a slot
    another process ran:

    * a row that dispatched freezes ``elapsed_s`` as ``now - dispatched_at``
      (clamped at the slot's budget) and ``queued_s`` as ``dispatched_at -
      started_at``, because both stamps are exact;
    * a row that never dispatched freezes ``elapsed_s: 0`` and **no**
      ``queued_s``. Unlike ``retire_live_entries``, which runs at the real end
      of the run, this can run hours after a killed run, so *now* is not when
      the wait ended and its length is unknown. The rule reads ``state``, not
      the absence of ``dispatched_at``, so a queued row in a map written before
      that key existed lands at ``0`` too, rather than at the clamped budget it
      used to (plan: review-run-scope-salvage-and-failure-visibility §6.2);
    * a running row with no ``dispatched_at`` (such a map again) keeps the old
      ``now - started_at`` and gains no ``queued_s``.

    **The two events do not share a ``source``, and that is the caller's to
    say.** ``run_status.SKIPPED_SOURCES`` / ``progress_tracker.RESUME_SOURCES``
    (``existing_file``, ``resume``) mean *this slot never dispatched on this
    run*, and ``run_status._model_state_label`` renders ``done`` + one of them
    as **skipped**. That is true of the ``--reaggregate`` path, which is why
    ``existing_file`` is the default. It is a lie about an in-process salvage,
    whose slot did dispatch, did run, failed to parse and was repaired — so
    :func:`record_models_salvaged` passes ``salvage``, which is deliberately in
    neither set and therefore renders as plain ``done`` in the ``models:`` table
    and on ``just finished:`` (2026-09-21).
    """
    stamp = _status_file.now_iso()
    flipped = False
    for model in models:
        entry = models_map.get(model)
        if not isinstance(entry, dict):
            continue
        if entry.get("state") == _progress.STATE_DONE:
            continue
        if entry.get("state") not in _progress.TERMINAL_STATES:
            # Read before `ended_at` is stamped, because the read-time rules
            # key on it: absent (the live row this branch exists for) gives the
            # live figures, present (only a hand-written row can be both
            # non-terminal and ended) gives the values already frozen there,
            # and either way what lands is a number that never moves again.
            # `_seconds` is progress_tracker's one definition of how a duration
            # reaches the checkpoint — a bare int when integral, which a clamped
            # `1800.0` otherwise would not be.
            elapsed = _progress.entry_elapsed_s(entry)
            # Only a dispatched row's wait has a known end; a never-dispatched
            # row's `entry_queued_s` would be "until this reaggregate".
            queued = (
                _progress.entry_queued_s(entry)
                if entry.get("dispatched_at") else None
            )
            if not entry.get("ended_at"):
                entry["ended_at"] = stamp
            entry["elapsed_s"] = (
                _progress._seconds(round(elapsed, 1)) if elapsed is not None else 0
            )
            if queued is not None:
                entry["queued_s"] = _progress._seconds(round(queued, 1))
        entry["state"] = _progress.STATE_DONE
        entry["source"] = source
        entry["updated_at"] = stamp
        entry.pop("error", None)
        flipped = True
    return flipped


def record_models_salvaged(phase_dir: str, models: Sequence[str]) -> None:
    """F3, 2026-09-20: put the map back in step after an in-process salvage.

    Both fan-out lanes repair a model's result file under ``--exec-subagents``
    and then ``del failed_models[spec]``, so the checkpoint they write a few
    lines later lists that model under ``models_completed`` and counts it in
    ``models_succeeded``. Neither touched the per-model map, and neither could
    have by the obvious route: terminal transitions are **idempotent**
    (``FanoutProgress._freeze`` refuses a second one), so a ``tracker.done()``
    against an entry the fan-out already froze as ``failed`` is a silent no-op.
    The result was a checkpoint reading ``models_completed: [a, b, c]``,
    ``models_failed: {}``, ``progress.models_succeeded: 3`` beside
    ``progress.models.c.state: "failed"`` with the pre-salvage error still on
    it — the exact contradiction :func:`record_models_present` was written to
    remove, recreated one function over.

    So the flip is written straight to the checkpoint through
    ``update_progress``, the way ``record_models_present`` does it, and by the
    same helper — but **not** with the same ``source``. ``existing_file`` is in
    ``run_status.SKIPPED_SOURCES``, so it would have every salvaged model read
    ``skipped`` in the ``models:`` table and on ``just finished:``: a word that
    means "never dispatched", about a slot that dispatched, ran and was
    repaired. ``salvage`` is in neither that set nor
    ``progress_tracker.RESUME_SOURCES``, so the row renders ``done`` and still
    says where the verdict came from. Counters are **not** written here: the
    caller's own post-salvage restatement (``models_done`` /
    ``models_succeeded``) follows immediately and carries no ``models`` key,
    and ``progress`` merges key by key at its top level, so the two writes
    compose rather than overwrite.

    The in-memory tracker is deliberately *not* reconciled, because it is never
    written again past this point on either lane (its last write is F11's
    backfill, above). A lane that ever does write it again after a salvage would
    re-assert ``failed`` from memory — that is the day ``FanoutProgress`` needs
    a method of its own for "a frozen verdict was superseded", which is not this
    change's to add.
    """
    progress = _status_file.read_status(phase_dir).get("progress")
    if not isinstance(progress, dict):
        return
    models_map = progress.get("models")
    if not isinstance(models_map, dict):
        return
    if flip_map_entries_to_done(models_map, models, source="salvage"):
        _status_file.update_progress(phase_dir, {"models": models_map})


def dispatch_salvage_tasks(
    args: Any,
    *,
    phase_dir: str,
    phase: str,
    plan_path: Optional[str] = None,
) -> List[str]:
    """Run every materialized ``salvage_task_*.json`` in a phase dir (D3b).

    Salvage repairs an unparseable *model review* on the fan-out path, so it is
    dispatched here — once, after the fan-out, when the requests exist — rather
    than from inside the per-model result writer, which has no flags and no
    phase-level view.

    **Deliberately non-fatal, unlike a validation batch.** A failed salvage leaves
    that model failed, which is exactly the partial-results outcome D6 row 3
    already covers (partial fan-out results are usable output); it is not the
    "reaggregating a short set" D3i forbids, because the *validation* set is still
    complete. A failed salvage is reported in ``subagent_batch_report.json`` like
    any other task.

    **A salvage the executor declared terminal is retired here**, which is what
    keeps the caller's end-of-run report honest without teaching it to re-derive
    the verdict: ``salvage_unrecoverable`` is the one status that says the answer
    will never change, so its request and task are renamed out of the globs (see
    :func:`retire_salvage_artifacts`) and the subagent's own reason is printed
    where the ``[SALVAGE_NEEDED]`` marker would otherwise have been. Every other
    failed status keeps its request: a timeout or a rate limit is re-runnable,
    and the documented salvage-then-reaggregate flow is how it gets re-run.

    Returns:
        The output paths successfully repaired, in dispatch order.
    """
    if not exec_subagents_requested(args):
        return []
    if getattr(args, "dry_run_subagents", False):
        # D3l: "start no child" has no exception for salvage. Salvage is the one
        # non-fatal dispatch, which is precisely why it would be the easiest place
        # for a dry run to quietly spawn something.
        print(
            "[dry-run-subagents] skipping salvage dispatch: no child is started "
            "under this flag, so no model result is repaired."
        )
        return []
    import glob as glob_module

    from .subagent_executor import ExecutorError, run_task_file

    repaired: List[str] = []
    project_root = get_project_root(plan_path) if plan_path else None
    for task_file in sorted(
        glob_module.glob(os.path.join(phase_dir, "salvage_task_*.json"))
    ):
        print(f"\n[exec-subagents] dispatching salvage task from {task_file}")
        try:
            report = run_task_file(
                task_file,
                phase_dir=phase_dir,
                phase=phase,
                anchor=plan_path,
                cwd=project_root,
            )
        except ExecutorError as failure:
            print(f"  salvage dispatch refused: {failure.message}", file=sys.stderr)
            continue
        for outcome in report.outcomes:
            if outcome.ok and outcome.output_path:
                repaired.append(outcome.output_path)
                continue
            print(
                f"  salvage {outcome.task_id} failed ({outcome.status}): "
                f"{outcome.reason or ''}",
                file=sys.stderr,
            )
            if outcome.status != STATUS_SALVAGE_UNRECOVERABLE:
                # Every other failure here is a *transport* failure with a rung
                # on the ladder — the child never spawned, timed out, was rate
                # limited, answered something unparseable. Re-running it is the
                # documented next move, so its request stays on disk and the
                # caller's end-of-run block goes on advertising it. Only the
                # sentinel is terminal.
                continue
            # `salvage_unrecoverable` is the executor reading the subagent's own
            # `{"salvage_failed": true, "reason": …}`: the child spawned,
            # replied and was understood, and what it said was that the raw
            # output holds no answer. The status is rung-less and in none of
            # `RETRYABLE_STATUSES` / `BACKOFF_STATUSES` / `FATAL_STATUSES`
            # (`utils/retry_ladder.py`) precisely because the same raw output
            # through the same prompt has the same answer — so this request is
            # not outstanding work, and leaving it on disk would print
            # `SALVAGE NEEDED` and `record_next` a `--reaggregate` that sends
            # the operator, or an automated host following that command, round a
            # loop that cannot make progress and buries the one diagnostic that
            # matters. The verdict is applied here, at the single point it is
            # known, rather than re-derived by each reporting block out of
            # `subagent_batch_report.json`.
            #
            # The stem comes from the task file this iteration globbed, not from
            # `outcome.task_id`: `write_salvage_task_file` materializes exactly
            # one task per `salvage_task_<stem>.json`, from exactly one
            # `salvage_<stem>.json`, so the filename is what actually pairs the
            # two artifacts — `task_id` merely echoes the same stem.
            stem = os.path.basename(task_file)[
                len("salvage_task_"): -len(".json")
            ]
            # On stdout, beside the `[SALVAGE_NEEDED]` marker it replaces, and in
            # the run's own output rather than only in the batch report: the
            # operator's next move is the provider, not a JSON repair, and the
            # reason is the only thing on screen that says so.
            print(
                f"[SALVAGE_UNRECOVERABLE] {stem}: "
                f"{outcome.reason or 'the salvage subagent recovered nothing'}"
            )
            retire_salvage_artifacts(
                phase_dir, stem, reason=RETIRE_UNRECOVERABLE
            )
    return repaired


def get_backoff_delay(base_delay: float) -> float:
    """Get backoff delay, respecting test mode for fast retries.

    When MULTI_LLM_TEST_FAST_BACKOFF=1 is set, returns minimal delay (10ms).
    """
    if os.environ.get("MULTI_LLM_TEST_FAST_BACKOFF") == "1":
        return 0.01
    return base_delay


def validate_suggestion(suggestion: dict) -> Tuple[bool, Optional[str]]:
    """Validate that a suggestion has all required fields with valid values."""
    for field in REQUIRED_FIELDS:
        if field not in suggestion:
            return (False, f"Missing required field: {field}")

    importance = suggestion.get("importance", "").lower()
    if importance not in VALID_IMPORTANCE:
        return (False, f"Invalid importance: {importance}")

    stype = suggestion.get("type", "").lower()
    if stype not in VALID_TYPES:
        return (False, f"Invalid type: {stype}")

    return (True, None)


def extract_json_array(text: str) -> Optional[str]:
    """Extract JSON array from text that may contain extra content."""
    try:
        wrapper = json.loads(text)
        if isinstance(wrapper, dict) and 'result' in wrapper:
            text = wrapper['result']
    except (json.JSONDecodeError, TypeError):
        pass

    code_block_match = re.search(r'```(?:json)?\s*(\[[\s\S]*?\])\s*```', text)
    if code_block_match:
        return code_block_match.group(1)

    array_match = re.search(r'\[[\s\S]*\]', text)
    if array_match:
        return array_match.group(0)

    return None


#: The ``Reason:`` line, keyed by the shared classifier's category (§7.1.a).
#:
#: This replaces a seven-branch ``elif`` chain of raw substring tests that had
#: drifted from every other classifier in the tree: its first branch called
#: **every** provider's failure "cursor-agent command not found" (and swallowed
#: "model not found" with a bare ``'not found' in stderr``), its rate-limit
#: branch disagreed with the retry decision three hundred lines below it, and
#: ``'insufficient'`` matched any prose containing the word.
#:
#: A lookup rather than a chain is the point: the sentence a user acts on and
#: the retry decision now read the *same* verdict off the *same* streams, so
#: they can no longer contradict each other.
#:
#: The old "Quota exceeded or insufficient credits" branch is deliberately gone.
#: A quota notice is what the shared classifier calls ``rate_limited`` — that is
#: the rung it is retried on — and a second name for it here is exactly the
#: disagreement this table removes.
_REASON_BY_CATEGORY = {
    STATUS_SPAWN_FAILED:
        "Reason: the runner CLI could not be started (is it installed and in PATH?)",
    CATEGORY_PERMISSION_DENIED: "Reason: Permission denied",
    CATEGORY_SANDBOX_UNAVAILABLE: (
        "Reason: the runner's own sandbox (bubblewrap) could not start — "
        "see `multi_llm.py doctor`"
    ),
    STATUS_AUTH_FAILED: "Reason: Authentication error (check API key)",
    CATEGORY_INVALID_MODEL: "Reason: Model not found or invalid",
    STATUS_RATE_LIMITED: "Reason: Rate limited",
    STATUS_TIMEOUT: "Reason: Timed out",
    CATEGORY_CONNECTION_ERROR: "Reason: Connection/network error",
    CATEGORY_SERVER_ERROR: "Reason: API/Server error",
    STATUS_RUNNER_ERROR: "Reason: the runner reported a failure",
}

_REASON_UNKNOWN = "Reason: Unknown (see tail output below)"


#: The one translation from §7.2's classifier vocabulary into the D3k ladder's
#: (§7.1.b). ``classify_streams`` returns four ``CATEGORY_*`` names the ladder has
#: no rung for; two of them are transport-shaped and therefore rung 4, which is
#: what makes a connection error or a 5xx spend ``driver.subagent_retries``
#: exactly once — the behaviour the deleted ``retry_count < 1`` recursion had.
#:
#: Everything **absent** from this table reaches :meth:`RetryLadder.record` under
#: its own name, and that is deliberate rather than an oversight:
#: ``rate_limited`` and ``timeout`` are already ladder statuses; ``auth_failed``,
#: ``spawn_failed`` and ``invalid_model`` are rung 1 (``invalid_model`` is the
#: classifier's own string, so it needs no row here and lands in ``record``'s
#: ``FATAL_STATUSES`` branch — ``STOP_FATAL``, "invalid_model is fatal to the
#: batch", zero retries either way, D4; ``sandbox_unavailable`` is the same
#: arrangement, D6); and ``permission_denied``,
#: ``context_length_exceeded`` and the unrecognized ``None`` all fall through
#: ``record``'s last branch to "never retried", which is exactly what the
#: deleted ``failure_category in RETRYABLE_FAILURE_CATEGORIES`` guard decided.
#: One table, not two. ``tests/test_lane_a_ladder.py`` pins the two
#: vocabularies in agreement.
_LADDER_STATUS_BY_CATEGORY = {
    CATEGORY_CONNECTION_ERROR: STATUS_RUNNER_ERROR,
    CATEGORY_SERVER_ERROR: STATUS_RUNNER_ERROR,
}

#: The ladder status of an attempt the plugin's jail denied (plan
#: codex-sandbox-unavailable F1 item 6, 2026-09-30). Not one of the ladder's
#: own statuses on purpose: ``RetryLadder.record`` treats every status it does
#: not know as "never retried", and a jail denial must never be re-dispatched —
#: nor moved to another rung.
STATUS_JAIL_DENIED = "jail_denied"


def _get_tail_output(text: str, max_lines: int = 20) -> str:
    """Get the last N lines of text for error context."""
    if not text:
        return ""
    lines = text.strip().split('\n')
    if len(lines) <= max_lines:
        return text.strip()
    return '\n'.join(lines[-max_lines:])


def _format_failure_details(
    returncode: int,
    stdout_text: str,
    stderr_text: str,
    max_tail_lines: int = 20,
    *,
    provider: Optional[LLMProvider] = None,
) -> str:
    """Format failure details with clear reason and tail output.

    The reason is the shared classifier's verdict looked up in
    :data:`_REASON_BY_CATEGORY` (§7.1.a) — there is no second rule here.

    **``provider`` is how this helper stops being the one classifier that reads
    raw stdout.** It is handed a whole ``stdout_text``, and four shipped
    adapters echo our prompt into that stream, so on the committed goose
    ``prompt-echo`` bytes this function answered ``Reason: Timed out`` about a
    run that had *succeeded*. Passing the adapter routes the verdict through
    :meth:`~utils.providers.base.LLMProvider.classify_failure`, which applies
    that adapter's :meth:`~utils.providers.base.LLMProvider.vendor_text`
    reduction first — and any caller that has an adapter in hand must pass it.

    With no adapter the behaviour is exactly what it was: the module-level
    :func:`classify_streams` against :class:`~utils.providers.base.LLMProvider`'s
    own declared pattern sets. That path is deliberately kept rather than made
    an error, because §7.2 depends on ``classify_streams`` staying callable with
    no adapter (``validation.py`` is the other such caller) — but it can only
    under-reduce, never mis-reduce, and it is not a path a production caller
    should be on.
    """
    error_parts = [f"Exit code {returncode}"]

    category = (
        provider.classify_failure(stdout_text, stderr_text, returncode)
        if provider is not None
        else classify_streams(stdout_text, stderr_text, returncode)
    )
    if category == STATUS_CONTEXT_LENGTH_EXCEEDED:
        error_parts.append(f"Reason: {context_length_message('')}")
    else:
        error_parts.append(_REASON_BY_CATEGORY.get(category, _REASON_UNKNOWN))

    tail_parts = []
    if stderr_text.strip():
        stderr_tail = _get_tail_output(stderr_text, max_tail_lines)
        tail_parts.append(f"--- stderr (last {max_tail_lines} lines) ---\n{stderr_tail}")
    if stdout_text.strip():
        stdout_tail = _get_tail_output(stdout_text, max_tail_lines)
        tail_parts.append(f"--- stdout (last {max_tail_lines} lines) ---\n{stdout_tail}")
    if tail_parts:
        error_parts.append("\n" + "\n".join(tail_parts))
    elif not stderr_text.strip() and not stdout_text.strip():
        error_parts.append("(no output captured)")

    return "\n".join(error_parts)


def _try_pretty_print_json(text: str) -> str:
    """Try to pretty-print text as JSON, return original if not valid JSON."""
    if not text or not text.strip():
        return text

    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict) and 'result' in parsed:
            inner = parsed['result']
            if isinstance(inner, str):
                try:
                    inner_parsed = json.loads(inner)
                    pretty_inner = json.dumps(inner_parsed, indent=2, ensure_ascii=False)
                    return (
                        f"[cursor-agent wrapper]\n"
                        f"type: {parsed.get('type', 'unknown')}\n"
                        f"result (pretty-printed):\n{pretty_inner}"
                    )
                except (json.JSONDecodeError, TypeError):
                    pass
        return json.dumps(parsed, indent=2, ensure_ascii=False)
    except (json.JSONDecodeError, TypeError):
        return text


# ---------------------------------------------------------------------------
# Model invocation
# ---------------------------------------------------------------------------

def served_model_fields(details: Dict[str, Any]) -> Dict[str, Any]:
    """§3.6's attribution keys from an invocation's ``details``, or ``{}``.

    Splatted into a per-model result record so the fan-out carries what the
    adapter read. Absent means "nothing was claimed" — every adapter but
    claude-code, and every claude-code run under the shipped empty
    ``fallback_models`` — and the record then has exactly the keys it has
    always had.

    The D6 override's provenance (2026-09-17) rides the same seam: a slot
    ``invoke_with_provider`` ran under ``sandbox_fallback`` carries
    ``details["sandbox"] == "bypassed"``, and the record gets a ``sandbox``
    key for it — independent of whether a served model was claimed, so the
    two facts can travel alone or together. A slot on a **contained** rung
    (landlock rung, 2026-09-22) carries the rung id there instead, and the
    record says ``fallback-<rung>`` (``sandbox_record_word``) — only the
    uncontained rung is ever recorded as ``bypassed``. A slot on the plugin's
    own jail records ``fallback-plugin-landlock`` the same way (2026-09-30).

    A slot the plugin's jail failed also carries :func:`jail_record_fields`'
    two keys, so ``status`` and the report can say "denied by the plugin's
    jail: <path>" after the log is gone (plan codex-sandbox-unavailable F1
    item 6).
    """
    fields: Dict[str, Any] = {}
    served = (details or {}).get("served_model")
    if served:
        fields["served_model"] = served
        fields["served_model_is_fallback"] = bool(
            details.get("served_model_is_fallback")
        )
    word = sandbox_record_word((details or {}).get("sandbox"))
    if word:
        fields["sandbox"] = word
    fields.update(jail_record_fields(details))
    return fields


#: The per-slot record keys of a slot the plugin's jail failed (plan
#: codex-sandbox-unavailable-findings-and-fixes §6 F1 item 6, 2026-09-30):
#: ``failure_reason: "jail-denied"`` and the denied path (``$HOME`` shown as
#: ``~``; ``None`` when codex did not name it). They ride the per-model result
#: record, ``models_served`` in ``.status.json`` and so ``--reaggregate``, the
#: hops the ``sandbox`` word takes.
RECORD_FAILURE_REASON = "failure_reason"
RECORD_JAIL_DENIED_PATH = "jail_denied_path"


def jail_record_fields(details: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """``{failure_reason, jail_denied_path}`` for a jail-denied slot, else ``{}``."""
    if (details or {}).get("failure_reason") != FAILURE_JAIL_DENIED:
        return {}
    evidence = (details or {}).get("jail_failure")
    path = evidence.get("path") if isinstance(evidence, dict) else None
    return {
        RECORD_FAILURE_REASON: FAILURE_JAIL_DENIED,
        RECORD_JAIL_DENIED_PATH: _render_home(path) if path else None,
    }


def _render_home(path: Optional[str]) -> str:
    """``path`` with ``$HOME`` shown as ``~`` (``landlock_dispatch``'s rule)."""
    from .landlock_dispatch import render_home

    return render_home(path)


def usage_fields(details: Dict[str, Any]) -> Dict[str, Any]:
    """The ``usage`` key from an invocation's ``details``, or ``{}``.

    The sibling of :func:`served_model_fields`, and for the same reason: the
    per-model record's shape is one function's, not a literal repeated at each
    of ``run_single_model``'s returns, so a slot that succeeded and a slot that
    failed cannot disagree about what a recorded run looks like.

    Absent means the adapter reported nothing — either it declares
    ``usage_support = "none"``, or this particular stream carried no usage
    block. It never means "free": an empty dict or a zeroed one would average
    into a run total and read as a run that cost nothing, which is the one
    reading these numbers exist to prevent.

    For **one** invocation's ``details``. A slot that retried spent what every
    attempt spent, so the retry lane folds its attempts together with
    :func:`accumulate_usage` and renders the aggregate through
    :func:`usage_total_fields`, which is the same shape this returns.
    """
    return usage_total_fields((details or {}).get("usage"))


def usage_total_fields(spent: Any) -> Dict[str, Any]:
    """:func:`usage_fields`' shape, from a block already summed over attempts.

    The single owner of "what a usage key looks like on a per-model record",
    which is why :func:`usage_fields` delegates to it rather than spelling the
    dict a second time: a slot that answered on its first attempt and one that
    answered on its third must produce the same shape, and the two call sites
    differ only in where the numbers came from.
    """
    return {"usage": spent} if isinstance(spent, dict) and spent else {}


def accumulate_usage(
    total: Optional[Dict[str, Any]], details: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """This slot's usage so far, with one more attempt's block folded in.

    The outer retry loop REPLACES ``details`` on every attempt, so reading the
    last one reports what the winning attempt spent and silently drops every
    attempt before it. A reproduced failure that burned $1 and was then retried
    into a $2 success reported $2 — understating the slot, the checkpoint's
    ``usage`` block and the report header by exactly the cost of the attempts
    an operator is most likely to be asking about. Lane B has always summed
    them (``subagent_executor._accumulate_usage``); this is that rule for
    Lane A.

    Numbers add. Anything else — claude-code files ``served_model`` among its
    token counts — is carried from the attempt that reported it last, which is
    the one whose answer travelled, and ``bool`` is excluded because in Python
    it is an ``int`` and "1 tool use" is not what ``True`` meant. Float sums
    are rounded to six places for the reason :func:`~utils.html_report_generator.sum_usage`
    rounds them: ``0.01 + 0.02`` is ``0.030000000000000002`` in binary floating
    point.

    ``None`` in and nothing reported out stays ``None``: absent must remain
    distinguishable from a measured zero all the way to the record.
    """
    spent = (details or {}).get("usage")
    if not isinstance(spent, dict) or not spent:
        return total
    merged: Dict[str, Any] = dict(total or {})
    for key, value in spent.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            merged[key] = value
            continue
        running = merged.get(key)
        if isinstance(running, (int, float)) and not isinstance(running, bool):
            value = running + value
        merged[key] = round(value, 6) if isinstance(value, float) else value
    return merged


def collect_usage(
    results: Dict[str, Dict[str, Any]]
) -> Dict[str, Dict[str, Any]]:
    """``{model_spec: usage}`` for a fan-out, from its per-model records.

    The report-side shape of what :func:`usage_fields` put on each record, built
    exactly as :func:`collect_served_models` builds its own — including for the
    slots that FAILED. A failed slot is the one whose cost an operator most
    wants named: a review that died on a usage cap after 491 s had spent $25 and
    137 348 output tokens, and every artifact of that run reported a duration.
    Empty when no adapter in the fan-out reported anything, which is what leaves
    a duration-only run's ``.status.json`` and report unchanged.
    """
    spent: Dict[str, Dict[str, Any]] = {}
    for model_spec, result in (results or {}).items():
        if not isinstance(result, dict):
            continue
        entry = result.get("usage")
        if isinstance(entry, dict) and entry:
            spent[model_spec] = entry
    return spent


def collect_served_models(
    results: Dict[str, Dict[str, Any]]
) -> Dict[str, Dict[str, Any]]:
    """``{model_spec: {"served_model", "fallback"[, "sandbox"]}}`` for a fan-out.

    The report-side shape of the same fact, built from the per-model records
    :func:`run_single_model` returns. Empty for a default run, which is what
    keeps every downstream artifact unchanged. A bypassed slot contributes an
    entry with ``sandbox: "bypassed"`` even when nothing served it by fallback
    — ``served_model_label`` renders either half, or both. A slot on a
    contained rung contributes ``sandbox: "fallback-<rung>"`` instead.
    """
    served: Dict[str, Dict[str, Any]] = {}
    for model_spec, result in (results or {}).items():
        if not isinstance(result, dict):
            continue
        entry: Dict[str, Any] = {}
        name = result.get("served_model")
        if name:
            entry["served_model"] = name
            entry["fallback"] = bool(result.get("served_model_is_fallback"))
        word = sandbox_record_word(result.get("sandbox"))
        if word:
            entry["sandbox"] = word
        # A jail-denied slot keeps its reason and path on the durable record
        # (F1 item 6): `models_served` is what `--reaggregate` reads back.
        if result.get(RECORD_FAILURE_REASON) == FAILURE_JAIL_DENIED:
            entry[RECORD_FAILURE_REASON] = FAILURE_JAIL_DENIED
            entry[RECORD_JAIL_DENIED_PATH] = result.get(RECORD_JAIL_DENIED_PATH)
        if entry:
            served[model_spec] = entry
    return served


def record_sandbox_bypassed(
    phase_dir: Union[str, Path], served_models: Dict[str, Dict[str, Any]]
) -> List[str]:
    """Mirror the bypassed slots into ``progress.sandbox_bypassed`` — on every
    run — and return the specs recorded.

    ``models_served`` (top-level, written by the phase's own ``update_status``)
    is the durable copy reaggregate reads; this is the poller's copy, under the
    reserved ``progress`` object ``status --view run`` renders, so a host that
    never reads the log still learns which slots ran without a sandbox. The
    ``run`` object is process state and is not touched (``status_file``).
    ``report_progress`` used to be a no-op in the foreground and this docstring
    used to lean on that; it writes there now, so a default run's checkpoint does
    carry the key — which is the feature working, not a leak. The fact that
    matters to a reader of a foreground checkpoint is the narrower one: it gains
    ``progress`` keys and still no ``run`` object.
    """
    bypassed = sorted(
        spec for spec, entry in (served_models or {}).items()
        if isinstance(entry, dict) and entry.get("sandbox") == SANDBOX_BYPASSED
    )
    # A contained rung (landlock rung, 2026-09-22) is a sandbox, not a bypass:
    # it never joins the list above, and the poller is told which rung each
    # such slot ran on under its own key, `progress.sandbox_fallback`
    # (`{spec: rung}`), which `status --view run` renders by rung name. The
    # plugin's own jail (`plugin-landlock`, 2026-09-30) rides the same key:
    # it is not a bypass either, and the status renderer names its grade
    # (stray writes only) from the rung name.
    contained = {
        spec: rung for spec, rung in sorted(
            (spec, sandbox_fallback_rung_of(entry.get("sandbox")))
            for spec, entry in (served_models or {}).items()
            if isinstance(entry, dict)
        ) if rung
    }
    if bypassed:
        _detach.report_progress(str(phase_dir), sandbox_bypassed=bypassed)
    if contained:
        _detach.report_progress(str(phase_dir), sandbox_fallback=contained)
    return bypassed


def announce_retired_rungs(
    prior_served: Optional[Dict[str, Dict[str, Any]]],
    served_models: Optional[Dict[str, Dict[str, Any]]],
    *,
    anchor: Optional[Union[str, Path]] = None,
) -> List[str]:
    """Name, once per run, a contained rung this run could no longer take — and
    return the lines printed.

    Two triggers, one line per provider and rung (the slots it covers
    comma-joined), printed after the fan-out and never per slot — the per-slot
    ``[SANDBOX_BYPASSED]`` line has by then already said what each slot did.

    * **Measured retirement** (plan §3.2, 2026-09-24): this process's probe
      cache (``subagent_executor.recorded_rung_retirements``) recorded the rung
      ``skipped`` because the codex version is at or above its ``removed_at``,
      or ``retired`` because its probe printed the rung's removal panic. The
      line then says the rung has been unavailable since that version,
      *whatever the previous run recorded* — a plan's first run included, the
      case the transition below misses. A timeout or any other probe failure
      never triggers it.
    * **Transition** (open question 2 of the landlock-rung plan): the previous
      run of this phase (``prior_served``, read before this run's
      ``write_status`` replaced it) recorded ``fallback-<rung>`` for a spec
      whose word is now ``bypassed``. The line names the rung with its
      ``deprecated_at`` version and sentence. The next run compares
      ``bypassed`` with ``bypassed`` and says nothing, which is what makes it
      once.

    Nothing else about the run changes.
    """
    try:
        from .subagent_executor import recorded_rung_retirements
    except Exception:  # noqa: BLE001 - a notice may never end a fan-out
        recorded_rung_retirements = None  # type: ignore[assignment]

    # (provider, rung id) -> {"specs": [...], "measured": bool, "version": str}
    groups: Dict[Tuple[str, str], Dict[str, Any]] = {}
    # (provider, incidental rung id) -> [specs]: the plugin's own jail last run,
    # no sandbox this run (plan codex-sandbox-unavailable §7 step-2 subtask
    # item 3, 2026-09-30). Named with THIS run's rung-probe outcome — never the
    # legacy rung's retirement wording, which would blame a codex upgrade for
    # what is usually a skip switch, a kernel or a failed self-test.
    left_jail: Dict[Tuple[str, str], List[str]] = {}
    retirements: Dict[str, List[Tuple[str, str]]] = {}
    for spec in sorted(served_models or {}):
        entry = (served_models or {}).get(spec)
        if not isinstance(entry, dict) or entry.get("sandbox") != SANDBOX_BYPASSED:
            continue
        try:
            provider_name = parse_model_spec(spec, anchor=anchor)[0]
        except Exception:  # noqa: BLE001 - a notice may never end a fan-out
            provider_name = spec.split(":", 1)[0]
        before = (prior_served or {}).get(spec)
        prior_rung = (
            sandbox_fallback_rung_of(before.get("sandbox"))
            if isinstance(before, dict) else None
        )
        if prior_rung and sandbox_word_is_incidental(prior_rung):
            left_jail.setdefault((provider_name, prior_rung), []).append(spec)
            continue
        if provider_name not in retirements:
            try:
                retirements[provider_name] = (
                    list(recorded_rung_retirements(provider_name))
                    if recorded_rung_retirements else []
                )
            except Exception:  # noqa: BLE001
                retirements[provider_name] = []
        for rung_id, version in retirements[provider_name]:
            group = groups.setdefault(
                (provider_name, rung_id),
                {"specs": [], "measured": True, "version": version},
            )
            group["measured"] = True
            group["version"] = group.get("version") or version
            if spec not in group["specs"]:
                group["specs"].append(spec)
        rung_id = prior_rung
        if not rung_id:
            continue
        group = groups.setdefault(
            (provider_name, rung_id), {"specs": [], "measured": False, "version": ""},
        )
        if spec not in group["specs"]:
            group["specs"].append(spec)

    lines: List[str] = []
    for (provider_name, rung_id), group in groups.items():
        rung = None
        try:
            hook = getattr(get_provider(provider_name), "sandbox_fallback_rungs", None)
            rungs = hook(PROFILE_GENERATE) if callable(hook) else ()
            rung = next((r for r in rungs if r.name == rung_id), None)
        except Exception:  # noqa: BLE001 - a notice may never end a fan-out
            rung = None
        if rung is None:
            # The adapter no longer declares the rung at all — the retirement
            # already reached this code. Name it without the upstream sentence.
            rung = SandboxRung(
                name=rung_id, probe_argv=None, argv_rewrite=(), contained=True,
            )
        line = sandbox_rung_retired_notice(
            provider_name, ", ".join(group["specs"]), rung,
            measured=bool(group["measured"]), version=group.get("version") or None,
        )
        print(line)
        lines.append(line)
    for (provider_name, rung_id), specs in left_jail.items():
        line = sandbox_rung_left_notice(provider_name, specs, rung_id)
        print(line)
        lines.append(line)
    return lines


#: The once-per-run line for specs that ran on the plugin's jail last run and
#: without any sandbox this one. Its own marker: ``[SANDBOX_BYPASSED]`` keeps
#: counting uncontained slots only, and ``[SANDBOX_RUNG_RETIRED]`` means a rung
#: a codex build removed — never the plugin's own rung.
SANDBOX_RUNG_CHANGED_MARKER = "[SANDBOX_RUNG_CHANGED]"


def _recorded_rung_outcome(
    provider_name: str, rung_id: str,
) -> Optional[Tuple[str, str, str]]:
    """``(outcome, probe tail, version)`` this process's probe cache recorded
    for ``rung_id`` of ``provider_name`` this run, or ``None``."""
    try:
        from . import subagent_executor as _executor
    except Exception:  # noqa: BLE001 - a notice may never end a fan-out
        return None
    cache = getattr(_executor, "_SANDBOX_PROBE_CACHE", None)
    lock = getattr(_executor, "_SANDBOX_PROBE_LOCK", None)
    if not isinstance(cache, dict):
        return None
    try:
        if lock is not None:
            with lock:
                items = list(cache.items())
        else:
            items = list(cache.items())
    except Exception:  # noqa: BLE001
        return None
    for key, verdict in items:
        if not isinstance(key, tuple) or len(key) < 3 or key[0] != "verdict":
            continue
        if key[2] != provider_name:
            continue
        for name, outcome in getattr(verdict, "walk", ()) or ():
            if name == rung_id:
                tails = dict(getattr(verdict, "rung_tails", ()) or ())
                return outcome, tails.get(name, ""), getattr(verdict, "version", "") or ""
    return None


def sandbox_rung_left_notice(provider_name: str, specs: Sequence[str], rung_id: str) -> str:
    """The line for specs that left the plugin's jail since the last run,
    naming this run's rung-probe outcome (the walk clause's own wording)."""
    recorded = _recorded_rung_outcome(provider_name, rung_id)
    if recorded is None:
        outcome = (
            f"this run's probe recorded no outcome for fallback rung {rung_id!r}"
        )
    else:
        state, tail, version = recorded
        rungs: Tuple[Any, ...] = ()
        try:
            hook = getattr(get_provider(provider_name), "sandbox_fallback_rungs", None)
            rungs = tuple(hook(PROFILE_GENERATE) or ()) if callable(hook) else ()
        except Exception:  # noqa: BLE001 - a notice may never end a fan-out
            rungs = ()
        try:
            outcome = sandbox_walk_clause(
                provider_name, ((rung_id, state),), ((rung_id, tail),) if tail else (),
                version or None, rungs,
            )
        except Exception:  # noqa: BLE001
            outcome = ""
        outcome = outcome or f"fallback rung {rung_id!r} {state} this run"
    return (
        f"{SANDBOX_RUNG_CHANGED_MARKER} {provider_name}: {', '.join(specs)} ran on "
        f"fallback rung {rung_id!r} (the plugin's Landlock jail, which stops "
        f"stray writes, not the model) last run and without any sandbox this "
        f"run: {outcome}"
    )


def recorded_served_models(phase_dir: str) -> Optional[Dict[str, Dict[str, Any]]]:
    """``models_served`` as the fan-out wrote it to ``.status.json``, or ``None``.

    What lets ``--reaggregate`` keep the provenance the fan-out recorded: the
    per-model ``{model}.json`` is a bare suggestion list, so the served-model
    and sandbox facts live in the checkpoint's ``models_served`` and are read
    back from there rather than re-derived. ``None`` when the checkpoint has
    no such key (a default run), which is what every reaggregate got before —
    and a stale or hand-edited checkpoint is read through the same best-effort
    ``read_status`` every other reaggregate field comes through.
    """
    try:
        recorded = _status_file.read_status(str(phase_dir)).get("models_served")
    except Exception:  # noqa: BLE001 - read_status is documented not to raise
        return None
    if not isinstance(recorded, dict) or not recorded:
        return None
    return {
        spec: entry for spec, entry in recorded.items() if isinstance(entry, dict)
    } or None


def recorded_usage(phase_dir: str) -> Optional[Dict[str, Dict[str, Any]]]:
    """``usage`` as the fan-out wrote it to ``.status.json``, or ``None``.

    The twin of :func:`recorded_served_models`, and needed for the same reason:
    the per-model ``{model}.json`` a reaggregation re-reads is a bare suggestion
    list, so what each slot spent survives only because it was written to the
    checkpoint. Without this read a ``--reaggregate`` produced a report whose
    badges had lost every number the original run recorded — and a reaggregated
    report is the one a human reads after a partial run, which is to say after
    the run whose cost they are most likely to be asking about.

    ``None`` when the checkpoint has no such key (every run of duration-only
    adapters), read through the same best-effort ``read_status`` every other
    reaggregate field comes through.
    """
    try:
        recorded = _status_file.read_status(str(phase_dir)).get("usage")
    except Exception:  # noqa: BLE001 - read_status is documented not to raise
        return None
    if not isinstance(recorded, dict) or not recorded:
        return None
    return {
        spec: entry for spec, entry in recorded.items() if isinstance(entry, dict)
    } or None


# ---------------------------------------------------------------------------
# What a reaggregate says about the models that produced nothing
# (plan: review-run-scope-salvage-and-failure-visibility §5)
# ---------------------------------------------------------------------------

#: The reason a reaggregate gives a requested model that has neither a result
#: file nor a ``models_failed`` entry (its file removed by hand, a fan-out killed
#: before it recorded outcomes). Named rather than dropped, so in "N of M
#: requested" N is always M minus the models listed under ``**Models:**``.
UNACCOUNTED_MODEL_REASON = "no result file and no recorded failure"

#: The stdout line a reaggregate prints per model that is still failed, right
#: after ``record_models_present``: the model and its stored reason, which is
#: what ``references/summary-format.md`` tells a host to name.
MODEL_FAILED_MARKER = "[MODEL_FAILED]"

#: Stands in for an empty or missing stored reason, so the line never reads
#: ``spec: `` with nothing after the colon.
_NO_RECORDED_REASON = "no reason recorded"

#: The three checkpoint fields whose union is the requested set.
_REQUESTED_SET_FIELDS = ("models_requested", "models_completed", "models_failed")


def _stored_reason(reason: Any) -> str:
    text = "" if reason is None else str(reason)
    return text if text.strip() else _NO_RECORDED_REASON


def recorded_failed_models(phase_dir: str) -> Dict[str, str]:
    """``.status.json``'s ``models_failed`` as ``{spec: reason}``, or ``{}``.

    The third reader beside :func:`recorded_served_models` and
    :func:`recorded_usage`, for the same reason: a per-model result file is a
    bare list, so the one record of *why* a model produced nothing is the
    checkpoint the fan-out wrote. Both reaggregates used to report no failure
    at all — code-review's derived its map from ``results``, which holds only
    models with a file, and the base hard-coded ``{}`` — so a reviewer that
    timed out vanished from every report rebuilt after it.

    Call it **after** :func:`record_models_present`, which moves a model whose
    file has since appeared (a salvage, an out-of-band result) out of
    ``models_failed``; read before, a recovered model would be named as
    failed. A legacy list-shaped ``models_failed`` reads as specs with no
    recorded reason, and anything else (absent, unreadable) as ``{}``.
    """
    try:
        recorded = _status_file.read_status(str(phase_dir)).get("models_failed")
    except Exception:  # noqa: BLE001 - read_status is documented not to raise
        return {}
    if isinstance(recorded, dict):
        return {str(spec): _stored_reason(reason) for spec, reason in recorded.items()}
    if isinstance(recorded, list):
        return {str(spec): _NO_RECORDED_REASON for spec in recorded}
    return {}


def recorded_requested_models(
    phase_dir: str, present_models: Optional[Sequence[str]] = None
) -> Optional[List[str]]:
    """The requested set a reaggregate counts "of M requested" against, or ``None``.

    The union, in first-seen order, of ``.status.json``'s ``models_requested``,
    ``models_completed`` and ``models_failed`` plus *present_models* (every
    model with a result file on disk). Each fan-out rewrites all three fields
    wholesale, so a model the latest run did not request is neither counted
    nor named — unless its old result file is still here, in which case it is
    loaded, recorded completed and counted on both sides, and the numbers
    still add up.

    **Never ``progress``.** A detached reaggregate's worker drops ``progress``
    wholesale when it claims the dir, and ``progress.models_total`` is a bare
    count that cannot be reconciled with the files; so a checkpoint that
    predates ``progress.models`` reads exactly like one that has it.

    A checkpoint that records none of the three fields returns ``None``, and
    the caller then leaves ``requestedModels`` out rather than guessing it from
    the files.
    """
    try:
        status = _status_file.read_status(str(phase_dir))
    except Exception:  # noqa: BLE001 - read_status is documented not to raise
        return None
    recorded = [
        status.get(key) for key in _REQUESTED_SET_FIELDS
        if isinstance(status.get(key), (list, dict))
    ]
    if not recorded:
        return None
    ordered: List[str] = []
    seen = set()
    for source in [*recorded, list(present_models or ())]:
        for spec in source:
            spec = str(spec)
            if spec not in seen:
                seen.add(spec)
                ordered.append(spec)
    return ordered


def remaining_failed_models(
    phase_dir: str, present_models: Optional[Sequence[str]] = None
) -> Tuple[Dict[str, str], Optional[List[str]]]:
    """``({spec: reason}, requested)``: every requested model with no result.

    The recorded failures (:func:`recorded_failed_models`, minus any model
    that has a file now), then every model of :func:`recorded_requested_models`
    that has neither a file nor a recorded failure, under
    :data:`UNACCOUNTED_MODEL_REASON`. This one map is what both reaggregates
    print, name on the ``**Models failed:**`` line and put under
    ``failedModels`` — gap models included — so the header, the page and the
    host's summary say the same thing.

    Args:
        phase_dir: The phase directory.
        present_models: The models with a readable result file. ``None`` reads
            ``models_completed`` instead, for a caller that holds no file list
            of its own (the consolidated report, which runs after a reaggregate
            has reconciled that field with the files).
    """
    if present_models is None:
        try:
            completed = _status_file.read_status(str(phase_dir)).get(
                "models_completed"
            )
        except Exception:  # noqa: BLE001 - read_status is documented not to raise
            completed = None
        present = [str(spec) for spec in completed] if isinstance(completed, list) else []
    else:
        present = [str(spec) for spec in present_models]
    present_set = set(present)
    requested = recorded_requested_models(phase_dir, present)
    failures = {
        spec: reason
        for spec, reason in recorded_failed_models(phase_dir).items()
        if spec not in present_set
    }
    for spec in requested or ():
        if spec not in present_set and spec not in failures:
            failures[spec] = UNACCOUNTED_MODEL_REASON
    return failures, requested


def _iso_stamp(value: Any) -> Optional[datetime]:
    """An ISO-8601 checkpoint stamp as a ``datetime``, or ``None``."""
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return datetime.fromisoformat(value.strip())
    except ValueError:
        return None


def salvage_requested_this_attempt(phase_dir: str, model_spec: str) -> bool:
    """Did this attempt ask for a salvage of *model_spec*?

    The one answer both report builders use for the ``**Models failed:**``
    line's salvage clause. The two invokers leave different evidence:

    * **A live request**, ``salvage_{stem}.json``. The native lane's invoker
      deletes it only after the reaggregate (``references/salvage-handling.md``),
      and an executor salvage that failed with a retryable status keeps it.
    * **A retired unrecoverable request**,
      ``retired_salvage_{stem}.unrecoverable.*.json``. Under
      ``--exec-subagents`` ``dispatch_salvage_tasks`` renames the pair
      (:data:`RETIRE_UNRECOVERABLE`) before the fan-out writes its report, and
      that name is also all a later ``--reaggregate`` finds. It counts only when
      the request's own ``timestamp`` is not earlier than
      ``.status.json.started_at`` — set by each fan-out's opening write — because
      :func:`retire_salvage_artifacts` renames only live ``salvage_*`` names, so
      a previous run's verdict survives the next attempt. A checkpoint without
      ``started_at`` gets no clause from this route.

    Never a ``.superseded.`` pair (a previous attempt's, retired when this one
    began), and never ``subagent_batch_report.json``: the validation dispatch
    that follows the salvage in the same phase dir writes the same bare name,
    so the salvage verdict is usually gone by report time.
    """
    import glob as glob_module

    phase_dir = str(phase_dir)
    stem = sanitize_model_name(str(model_spec))
    if os.path.exists(os.path.join(phase_dir, f"salvage_{stem}.json")):
        return True
    try:
        started = _iso_stamp(_status_file.read_status(phase_dir).get("started_at"))
    except Exception:  # noqa: BLE001 - read_status is documented not to raise
        started = None
    if started is None:
        return False
    pattern = os.path.join(
        glob_module.escape(phase_dir),
        f"retired_salvage_{glob_module.escape(stem)}.{RETIRE_UNRECOVERABLE}.*.json",
    )
    for path in sorted(glob_module.glob(pattern)):
        try:
            with open(path, "r", encoding="utf-8") as handle:
                request = json.load(handle)
        except (OSError, ValueError):
            continue
        stamp = _iso_stamp(request.get("timestamp")) if isinstance(request, dict) else None
        if stamp is None:
            continue
        try:
            if stamp >= started:
                return True
        except TypeError:  # one stamp zone-aware, the other naive
            continue
    return False


def salvage_requested_models(
    phase_dir: Optional[str], models: Optional[Sequence[str]]
) -> List[str]:
    """The subset of *models* for which :func:`salvage_requested_this_attempt` holds."""
    if not phase_dir:
        return []
    return [
        str(spec) for spec in (models or ())
        if salvage_requested_this_attempt(str(phase_dir), str(spec))
    ]


def record_failed_models_in_progress(phase_dir: str, failures: Dict[str, str]) -> bool:
    """Write each still-failed model into ``progress.models`` as a ``failed`` row.

    ``progress.models`` is the machine-readable record a host names failures
    from (``cli_common.STATE_PARTIAL``; both Codex templates), and a detached
    reaggregate's worker drops ``progress`` wholesale when it claims the dir —
    so after such a run the source was empty while the result line said
    ``partial``. A row already ``failed`` keeps the fan-out's own entry (its
    timings and wording); any other row is moved to ``failed`` with the stored
    reason, a live one frozen by the same read-time rule
    :func:`flip_map_entries_to_done` uses; a missing row is added with no
    clock, since this process never ran that slot. Counters are left alone.

    Returns whether anything was written. The map is written whole, because
    only a ``progress`` write carrying a ``models`` key replaces it.
    """
    if not failures:
        return False
    try:
        progress = _status_file.read_status(str(phase_dir)).get("progress")
    except Exception:  # noqa: BLE001 - read_status is documented not to raise
        progress = None
    existing = progress.get("models") if isinstance(progress, dict) else None
    models_map: Dict[str, Any] = dict(existing) if isinstance(existing, dict) else {}
    stamp = _status_file.now_iso()
    changed = False
    for spec, reason in failures.items():
        entry = models_map.get(spec)
        if isinstance(entry, dict) and entry.get("state") == _progress.STATE_FAILED:
            continue
        if isinstance(entry, dict):
            row = dict(entry)
            if row.get("state") not in _progress.TERMINAL_STATES:
                elapsed = _progress.entry_elapsed_s(row)
                if not row.get("ended_at"):
                    row["ended_at"] = stamp
                row["elapsed_s"] = (
                    _progress._seconds(round(elapsed, 1)) if elapsed is not None else 0
                )
        else:
            row = {"source": None}
        row["state"] = _progress.STATE_FAILED
        row["error"] = str(reason)
        row["updated_at"] = stamp
        models_map[spec] = row
        changed = True
    if changed:
        _status_file.update_progress(str(phase_dir), {"models": models_map})
    return changed


def announce_remaining_failures(phase_dir: str, failures: Dict[str, str]) -> None:
    """Name every model a reaggregate still has no result for, to the host.

    One :data:`MODEL_FAILED_MARKER` line per model with its stored reason —
    the reaggregate's own summary text, since after ``--reaggregate`` nothing
    else said so (plan §5.1: no ``[PARTIAL_RESULTS]``, no failure section) —
    and the same failures written into ``progress.models``
    (:func:`record_failed_models_in_progress`). ``MULTI_LLM_RESULT.state`` and
    the exit code are the completion path's to set, not this function's.
    """
    for spec, reason in failures.items():
        one_line = " ".join(str(reason).splitlines())
        print(f"{MODEL_FAILED_MARKER} {spec}: {one_line}")
    record_failed_models_in_progress(phase_dir, failures)


def exit_when_every_reviewer_failed(
    phase_dir: str,
    failures: Dict[str, str],
    *,
    mode: str,
    plan_path: str,
) -> None:
    """A reaggregate with no readable result: exit 3 when reviewers failed.

    Both reaggregates return early, before any report, when no model has a
    readable result file. That used to be exit 0 with no phase recorded
    completed. When ``.status.json.models_failed`` is non-empty — reviewers
    were requested and every one failed — this is the fan-out's own zero-result
    ending instead: :func:`unattended.report_partial_results` with no completed
    model names the failures and the retry command and returns exit 3, needs a
    human, and the phase is still not recorded completed (decision 11.11).

    With no recorded failure (nothing was ever requested, or the dir was cleaned
    by hand) it returns, and the caller keeps today's exit 0.
    """
    if not recorded_failed_models(phase_dir):
        return
    try:
        stored_flags = _status_file.read_status(str(phase_dir)).get("replay_flags")
    except Exception:  # noqa: BLE001 - read_status is documented not to raise
        stored_flags = None
    sys.exit(_unattended.report_partial_results(
        completed=[],
        failed=list(failures),
        phase_dir=str(phase_dir),
        retry_command=cli_common.retry_command(
            mode, plan_path, "--force",
            flags=cli_common.current_replay_flags(stored_flags, mode=mode),
        ),
    ))


# The fan-out's own sandbox cache (`_FANOUT_SANDBOX_CACHE`, its lock and its
# per-key probe locks) is gone (plan §3.6, 2026-09-24): the fan-out and the
# executor share one probe cache, `subagent_executor._SANDBOX_PROBE_CACHE`,
# keyed by codex version and policy and holding the whole `SandboxProbeResult`.


def sandbox_unavailable_reason(provider_name: str, tail: str) -> str:
    """The recorded reason for a slot refused because its sandbox cannot start.

    The verdict ``multi_llm.py doctor`` renders, compressed into the one line a
    per-model failure gets: the ``[SANDBOX_UNAVAILABLE]`` marker so the row
    greps next to the classifier's own category, the redacted probe tail (the
    ``bwrap:`` line, on the machine this was written for) so the reader is not
    sent to look for evidence that was already in hand, and the one command
    that prints the repair. No retry command: the fix is an AppArmor profile,
    and a machine's sandbox does not start on the second ask.
    """
    said = f" ({tail.strip()})" if (tail or "").strip() else ""
    return (
        f"[SANDBOX_UNAVAILABLE] {provider_name}'s sandbox cannot start here"
        f"{said}; run `multi_llm.py doctor` for details"
    )


def _fanout_sandbox_verdict(provider_name: str, cwd: Optional[str]) -> Any:
    """Run — or recall — this provider's ``generate`` sandbox self-test.

    Blocking, so the caller hands it to a thread. The probe and its cache are
    the executor's (``subagent_executor.cached_sandbox_verdict``, plan §3.6),
    which is what makes the fan-out, the subagent preflight and ``doctor``
    read the same adapter-declared command the same way — and the fan-out and
    the preflight share one rung probe per codex version. ``cwd`` is the repo
    root the dispatch is pinned to, the same root
    ``subagent_executor._probe_cwd`` derives from the plan anchor. An adapter
    with no probe for this profile answers ``not-required`` without spawning
    anything, so this costs nothing for every adapter that declares no OS
    sandbox — which is all of them but codex.
    """
    from .subagent_executor import SandboxProbeResult, cached_sandbox_verdict

    try:
        provider = get_provider(provider_name)
    except Exception:  # noqa: BLE001 - a diagnostic may never end a fan-out
        return SandboxProbeResult("unknown", "")
    return cached_sandbox_verdict(
        provider_name, provider, PROFILE_GENERATE, cwd=cwd,
        policy=_fanout_sandbox_fallback(provider_name, cwd),
    )


#: The three answers :func:`sandbox_refusal` can give a fan-out slot.
SANDBOX_DISPATCH = "dispatch"
SANDBOX_REFUSE = "refuse"
SANDBOX_DISPATCH_UNSANDBOXED = "dispatch_unsandboxed"


class SandboxVerdict(NamedTuple):
    """What the pre-dispatch sandbox gate decided for one fan-out slot.

    ``verdict`` is one of :data:`SANDBOX_DISPATCH` (run as the adapter renders
    it — the answer for ``ok``, ``unknown`` and ``not-required`` alike),
    :data:`SANDBOX_REFUSE` (``reason`` is the ``[SANDBOX_UNAVAILABLE]`` line
    the slot is failed with) or :data:`SANDBOX_DISPATCH_UNSANDBOXED` — the
    slot runs on a fallback **rung**, named by ``rung`` (landlock rung,
    2026-09-22), which is what :func:`sandbox_fallback_kwargs` hands the
    invoker. ``reason`` is then the one line the lane prints: the
    ``[SANDBOX_BYPASSED]`` line for the uncontained rung, a
    ``[SANDBOX_FALLBACK]`` line for a contained one, a
    ``[SANDBOX_INCIDENTAL]`` line for the plugin's own jail (``incidental``
    grade, 2026-09-30). ``bypass`` means the
    uncontained rung **exactly** — it is what the lanes gate the
    ``[SANDBOX_BYPASSED]`` print on (the porcelain detective check reads the
    rung id itself, :func:`porcelain_check_applies`), and a contained rung is
    a sandbox, not a bypass. A NamedTuple rather than a str
    so a call site cannot take the third answer for the first by truthiness.
    """

    verdict: str
    reason: Optional[str]
    rung: Optional[str] = None
    #: The probe's fallback walk — ``((rung id, outcome), …)`` — that decided
    #: this slot (2026-09-24), so a reader of the verdict can tell a contained
    #: rung that was tried and failed from one never measured.
    walk: Tuple[Tuple[str, str], ...] = ()
    #: The selected rung carries the ``incidental`` grade (the plugin's own
    #: Landlock jail, 2026-09-30): what :func:`mode_check_applies` and
    #: :func:`home_check_applies` key on. A trailing default, so every
    #: positional construction keeps its meaning.
    incidental: bool = False

    @property
    def refused(self) -> bool:
        return self.verdict == SANDBOX_REFUSE

    @property
    def bypass(self) -> bool:
        return (
            self.verdict == SANDBOX_DISPATCH_UNSANDBOXED
            and self.rung == SANDBOX_RUNG_UNSANDBOXED
        )

    @property
    def fallback(self) -> bool:
        """The slot runs on **any** fallback rung, contained or not — what the
        lanes gate the one per-slot notice on (``reason``: ``[SANDBOX_FALLBACK]``
        for a contained rung, ``[SANDBOX_BYPASSED]`` for the uncontained one).
        Never the porcelain check's gate: that is ``porcelain_check_applies``."""
        return self.verdict == SANDBOX_DISPATCH_UNSANDBOXED and bool(self.reason)


def sandbox_bypassed_notice(provider_name: str, probe: Any = None) -> str:
    """The one line a lane prints for a slot dispatched under the D6 override.

    Its **stem** is verbatim the sentence the design fixed (2026-09-17),
    because it is the whole of what the operator is told at the moment it
    matters. Since 2026-09-24 (plan §3.1) the rung clause is appended after
    that stem when ``probe`` — the ``SandboxProbeResult`` — shows the walk
    tried a rung first: each rung with its outcome and, when it was probed,
    its probe tail (``fallback rung 'landlock' unavailable (codex 0.156.1:
    "…")``), or ``not tried: unusable since codex 0.156.1 (panics; measured;
    installed: 0.159.3)`` when the version skipped it. Without ``probe`` the
    stem alone is returned. The stem says which runner,
    why its own sandbox is not in the path, which config key governs it (and
    so which word turns it off), and — the clause that cannot be left out —
    that nothing stands between the model's shell and this machine. It is
    printed under the *default* policy, loudly and on purpose: read-only
    phase or not, the model runs with the operator's rights; 4 of the 5
    reviewers on the host this was measured on already do (muse always,
    under ``--disable-sandbox``), and the sentence is what keeps codex's case
    from being the quiet one.
    """
    if probe is None:
        return sandbox_bypassed_notice_text(provider_name)
    from .subagent_executor import sandbox_bypass_line

    rungs: Tuple[Any, ...] = ()
    try:
        hook = getattr(get_provider(provider_name), "sandbox_fallback_rungs", None)
        rungs = tuple(hook(PROFILE_GENERATE) or ()) if callable(hook) else ()
    except Exception:  # noqa: BLE001 - a notice may never end a fan-out
        rungs = ()
    return sandbox_bypass_line(provider_name, probe, rungs)


def sandbox_fallback_notice(provider_name: str, rung: Any, policy: str) -> str:
    """The one line a lane prints for a slot dispatched on a **contained**
    fallback rung — never the ``[SANDBOX_BYPASSED]`` sentence, which would
    claim the opposite of what happened. Names the rung, its deprecation when
    it has one, and that the raw capture's ``"type":"error"`` deprecation item
    is not the failure (``base.sandbox_fallback_notice_text``, shared with the
    executor's preflight line)."""
    return sandbox_fallback_notice_text(provider_name, rung, policy)


def sandbox_incidental_notice(
    provider_name: str, rung: Any, policy: Optional[str], probe: Any,
) -> str:
    """The one ``[SANDBOX_INCIDENTAL]`` line a fan-out slot on the plugin's
    jail prints (plan codex-sandbox-unavailable §7 "Step 2 subtask" item 2).

    Built by ``base.sandbox_incidental_notice_text`` — the one builder both
    lanes share — with the standard probe's tail and the walk clause of the
    rungs tried **before** this one (the legacy rung skipped by version), so
    the run log names the rung and why codex's own sandbox was not used.
    """
    walk = tuple(getattr(probe, "walk", ()) or ())
    before: List[Tuple[str, str]] = []
    for name, outcome in walk:
        if name == rung.name:
            break
        before.append((name, outcome))
    clause = ""
    if before:
        rungs: Tuple[Any, ...] = ()
        try:
            hook = getattr(get_provider(provider_name), "sandbox_fallback_rungs", None)
            rungs = tuple(hook(PROFILE_GENERATE) or ()) if callable(hook) else ()
        except Exception:  # noqa: BLE001 - a notice may never end a fan-out
            rungs = ()
        try:
            clause = sandbox_walk_clause(
                provider_name, before, tuple(getattr(probe, "rung_tails", ()) or ()),
                getattr(probe, "version", "") or None, rungs,
            )
        except Exception:  # noqa: BLE001
            clause = ""
    return sandbox_incidental_notice_text(
        provider_name, rung, policy, getattr(probe, "tail", "") or "",
        walk_clause=clause, lane=INCIDENTAL_LANE_FANOUT,
    )


def _fanout_sandbox_fallback(provider_name: str, cwd: Optional[str]) -> Optional[str]:
    """The adapter's resolved ``sandbox_fallback`` policy for ``generate``, or
    ``None`` for an adapter that declares no fallback at all.

    ``cwd`` is the repo root the dispatch is pinned to, and it is a valid
    discovery anchor (``load_config`` takes a directory), so the policy is
    read from the same ``.multi-llm/providers.yaml`` the slot's own env and
    timeout come from. A test's stand-in adapter may not declare the hook —
    ``getattr``, and any failure reads as "no fallback": a config read may
    never end a fan-out, and the safe reading of a broken one is the default.
    """
    provider = get_provider(provider_name)
    hook = getattr(provider, "sandbox_fallback_policy", None)
    if not callable(hook):
        return None
    try:
        policy = hook(PROFILE_GENERATE, anchor=cwd)
    except Exception:  # noqa: BLE001 - a config read may never end a fan-out
        return None
    return policy if isinstance(policy, str) else None


def sandbox_refusal(provider_name: str, cwd: Optional[str]) -> SandboxVerdict:
    """The pre-dispatch sandbox verdict for one fan-out slot.

    The one gate all three fan-out lanes ask — :func:`run_single_model` for
    review-plan/review-tasks, ``code_review_orchestrator.run_single_review``
    and ``ask_orchestrator``'s ``ask_one`` — so they share one cache, one
    probe and one wording. Blocking (it may spawn the probe), so each lane
    hands it to ``asyncio.to_thread``. ``ok``, ``unknown`` and ``not-required``
    all answer ``dispatch``: a probe that could not be read is a diagnostic and
    never a gate, and a sandbox that dies mid-dispatch still lands on the D3k
    ladder as rung 1.

    ``unavailable`` answers ``dispatch_unsandboxed`` — the D6 override
    (2026-09-17), now a ladder (landlock rung, 2026-09-22) — when the
    adapter's fallback walk selected a rung it declares for ``generate`` and
    ``providers.<name>.sandbox_fallback`` permits that rung. The key gates
    **every** rung: ``auto`` (the shipped default) takes whichever rung the
    walk selected — the contained ``landlock`` rung first, the uncontained
    ``unsandboxed`` rung only when the contained one's probe failed (and,
    since 2026-09-30, the plugin's own ``incidental``-grade jail between them,
    announced with ``[SANDBOX_INCIDENTAL]``, never ``[SANDBOX_BYPASSED]``);
    ``contained`` takes a contained rung and **never** the uncontained one;
    ``off`` takes none. The verdict carries the rung id, which is what
    :func:`sandbox_fallback_kwargs` hands the invoker. ``refuse`` — the
    ``[SANDBOX_UNAVAILABLE]`` line — is therefore the answer under ``off``
    (exactly as before the ladder: ``off`` still means refusal), under
    ``contained`` when no contained rung is usable, when the walk stopped on a
    rung probe that gave no answer (fail-closed: nothing learned never licenses
    a widening), and for every adapter that declares no fallback.
    """
    from .subagent_executor import _fallback_rungs, sandbox_fallback_rung, sandbox_walk_note

    probe = _fanout_sandbox_verdict(provider_name, cwd)
    if probe.state != "unavailable":
        return SandboxVerdict(SANDBOX_DISPATCH, None)
    policy = _fanout_sandbox_fallback(provider_name, cwd)
    try:
        rung = sandbox_fallback_rung(
            get_provider(provider_name), PROFILE_GENERATE, probe.rung, policy
        )
    except Exception:  # noqa: BLE001 - a diagnostic may never end a fan-out
        rung = None
    if rung is not None:
        if rung.contained:
            notice = sandbox_fallback_notice(provider_name, rung, policy or "")
        elif rung_is_incidental(rung):
            # The plugin's own jail (plan codex-sandbox-unavailable §7 "Step 2
            # subtask" items 1-2, 2026-09-30): `[SANDBOX_INCIDENTAL]`, never
            # `[SANDBOX_BYPASSED]` (whose count must stay the uncontained
            # slots) nor `[SANDBOX_FALLBACK]` (a real OS boundary). The walk
            # clause covers the rungs tried before it — the legacy rung
            # skipped by version — with the standard probe's tail.
            notice = sandbox_incidental_notice(provider_name, rung, policy, probe)
        else:
            notice = sandbox_bypassed_notice(provider_name, probe)
        return SandboxVerdict(
            SANDBOX_DISPATCH_UNSANDBOXED, notice, rung.name, tuple(probe.walk or ()),
            incidental=rung_is_incidental(rung),
        )
    reason = sandbox_unavailable_reason(provider_name, probe.tail)
    try:
        declared = _fallback_rungs(get_provider(provider_name), PROFILE_GENERATE)
    except Exception:  # noqa: BLE001 - a diagnostic may never end a fan-out
        declared = ()
    note = sandbox_walk_note(probe, policy, provider_name=provider_name, rungs=declared)
    if note:
        reason = f"{reason} ({note})"
    return SandboxVerdict(SANDBOX_REFUSE, reason, None, tuple(probe.walk or ()))


def sandbox_fallback_kwargs(verdict: SandboxVerdict) -> Dict[str, str]:
    """``{"sandbox_fallback": <rung id>}`` for a slot on a fallback rung, else ``{}``.

    The rung id, never a bool: the invoker hands it to the adapter's argv
    build, which renders *that* rung — a bool would leave it to guess, and the
    only guess it ever had was the uncontained one.

    Splatted into the invoker call rather than passed as a positional default,
    because the invokers (``invoke_with_provider``, ``invoke_with_file_output``)
    are stood in for by a dozen test fakes with fixed signatures, and a kwarg
    that travels only when it is load-bearing leaves every one of them — and
    every default fan-out — byte-for-byte as it was.
    """
    if verdict.verdict == SANDBOX_DISPATCH_UNSANDBOXED and verdict.rung:
        return {"sandbox_fallback": verdict.rung}
    return {}


#: Plan §4.1 (option A): above this many bytes of dirty/untracked regular
#: files, a snapshot records no content hashes and the slot's comparison falls
#: back to path + status only (today's behaviour), with one printed note.
PORCELAIN_HASH_CAP_BYTES = 50 * 1024 * 1024

#: The fixed markers a baseline entry carries in place of a blob id.
PORCELAIN_ABSENT = "absent"
PORCELAIN_UNREADABLE = "unreadable"
PORCELAIN_DIRECTORY = "directory"
PORCELAIN_SYMLINK_PREFIX = "symlink:"

#: The status an R/C record's OLD path is stored under: under ``-z`` git prints
#: it as its own record with no status columns, and it stays in the compared
#: set so a rename reports both paths.
PORCELAIN_RENAME_SOURCE = "<-"


class PorcelainEntry(NamedTuple):
    """One path of a :class:`PorcelainSnapshot`: ``(status, kind, blob, exec)``.

    ``kind`` is ``file``, ``symlink``, ``directory``, ``absent`` or
    ``unreadable``; ``blob`` is
    the git blob id of a regular file, ``symlink:<target>`` for a symlink (never
    followed), or the kind's own marker; ``exec_bit`` is the owner/group/other
    execute bit of a regular file, so a mode-only change to a pre-dirty file is
    seen even though its bytes and its ` M` status did not move.
    """

    status: str
    kind: str
    blob: str
    exec_bit: bool


class PorcelainSnapshot(NamedTuple):
    """The per-path baseline :func:`porcelain_snapshot` returns (plan §4.1).

    ``hashed`` is False when this snapshot degraded (the dirty set was over
    :data:`PORCELAIN_HASH_CAP_BYTES`, or ``git hash-object`` failed as a whole):
    its entries then carry no blob ids, and a comparison involving it is by path
    and status only. ``note`` is the one line that was printed about it.
    """

    entries: Dict[str, PorcelainEntry]
    hashed: bool = True
    note: Optional[str] = None


def _under_prefixes(path: str, prefixes: Sequence[str]) -> bool:
    return any(path.startswith(prefix) or path == prefix.rstrip("/")
               for prefix in prefixes)


def _normalized_prefixes(ignore_prefixes: Sequence[str]) -> Tuple[str, ...]:
    return tuple(p.rstrip("/") + "/" for p in ignore_prefixes if p and p.rstrip("/"))


_PORCELAIN_STATUS_CHARS = frozenset(" MTADRCU?!")


def _porcelain_records(stdout: str) -> Optional[List[Tuple[str, str]]]:
    """``[(status, path)]`` from ``git status --porcelain -z`` output, or ``None``.

    Under ``-z`` an ``R``/``C`` record is followed by the old path as its own
    NUL-terminated record with no status; it is returned with
    :data:`PORCELAIN_RENAME_SOURCE` as its status. Output that is not a
    sequence of ``XY path`` records is not git's answer at all, and is
    ``None`` — the "git cannot answer" case — rather than a guess.
    """
    records: List[Tuple[str, str]] = []
    fields = [f for f in stdout.split("\0")]
    i = 0
    while i < len(fields):
        field = fields[i]
        i += 1
        if not field:
            continue
        if (len(field) < 4 or field[2] != " "
                or not set(field[:2]) <= _PORCELAIN_STATUS_CHARS):
            return None
        status, path = field[:2], field[3:]
        records.append((status, path))
        if ("R" in status or "C" in status) and i < len(fields) and fields[i]:
            records.append((PORCELAIN_RENAME_SOURCE, fields[i]))
            i += 1
    return records


def porcelain_snapshot(
    cwd: Optional[str], *, ignore_prefixes: Sequence[str] = ()
) -> Optional[PorcelainSnapshot]:
    """A per-path baseline of the working tree's dirty set, or ``None``.

    The detective half of the D6 override (2026-09-17): a bypassed slot has no
    sandbox to *prevent* a write, so the fan-out takes this before the slot and
    again after it, and :func:`unexpected_writes` compares the two. Since plan
    §4.1 (option A, 2026-09-24) it is a baseline, not a set of porcelain lines:

    - ``git status --porcelain -z --untracked-files=all``, so every untracked
      file is its own entry (without the flag an untracked directory is one
      ``?? dir/`` record and a write inside it is invisible);
    - entries under ``ignore_prefixes`` (the plugin's own output trees,
      :func:`bypass_ignore_prefixes`) are dropped **before** hashing, so they
      are never read;
    - every path gets a :class:`PorcelainEntry` — a regular file's blob id from
      ONE ``git hash-object --no-filters --stdin-paths`` run, a symlink's target
      (never followed), ``absent`` for a deletion or a path gone from disk,
      ``directory`` for a directory still reported whole (a nested
      repository), compared by status/path only, and ``unreadable`` for a
      path that cannot be read (a path ``hash-object`` cannot open is
      re-``lstat``-ed and recorded ``absent`` or ``unreadable``, and the rest
      hashed once more, before the snapshot degrades);
    - above :data:`PORCELAIN_HASH_CAP_BYTES` of regular files (summed ``lstat``
      sizes), or when ``hash-object`` fails as a whole, the snapshot records no
      hashes (``hashed=False``) and prints one note, and the comparison falls
      back to path + status for this slot.

    Cost, stated because it runs twice per bracketed slot: two ``lstat`` passes
    and two ``hash-object`` runs over the dirty set, inside the ``to_thread``
    the three call sites already use, each git call under the same 30 s
    timeout. It never raises.

    What it can see now that it could not before: a write to a file that was
    *already* modified or untracked before the slot (its porcelain line does
    not change, its blob id does), a mode-only change, a retargeted symlink, a
    pre-existing untracked file deleted, a dirty file restored to clean —
    unless the snapshot degraded past the cap. What it still cannot see,
    stated plainly: a write outside the repository, anything under ``$HOME``,
    a write to a gitignored path — and **who** made a change: the snapshot is
    of the whole tree, and the other slots of the fan-out, and any other
    process writing to this repository (another session, an editor, a build),
    run in that same tree for the whole window, several of them (cursor-agent,
    pi, claude-code) with no sandbox by design, so a sibling's write lands in
    this slot's diff exactly as the slot's own would (the 2026-09-22 and
    2026-09-24 misattributions). The reason line therefore reports the change
    and the count of boundary-less siblings (:func:`bypass_write_violation`),
    never an author; only the slot's own audited action stream can clear it
    (plan §4.2, ``utils/readonly_audit.py``). It is a cheap, honest check, not
    a boundary.

    Scope, recorded rather than fixed (T7; plan §4.6, Open question 3): only
    the three fan-out lanes take this snapshot. The executor lane
    (``subagent_executor``: validation, revalidation, consolidation, task
    generation) takes none, so a read-only dispatch there on the uncontained
    rung is unchecked — before T7 and after it. Run ``0c477c4d`` (2026-09-24)
    dispatched its 16 validation batches to codex on that rung with no check
    at all. Widening the check (or the §4.2 stream audit, which the executor
    already has each child's stream for) to that lane is separate work.
    ``None`` when git cannot answer (no repo, no ``git``), and the caller then
    skips the comparison rather than failing a slot on a check it never ran.
    """
    if not cwd:
        return None
    try:
        completed = subprocess.run(
            git_argv("status", "--porcelain", "-z", "--untracked-files=all", cwd=cwd),
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            cwd=cwd, timeout=30,
        )
        if completed.returncode != 0:
            return None
        top = subprocess.run(
            git_argv("rev-parse", "--show-toplevel", cwd=cwd),
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            cwd=cwd, timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    root = top.stdout.strip() if top.returncode == 0 else ""
    if not root or not os.path.isdir(root):
        root = cwd
    records = _porcelain_records(completed.stdout)
    if records is None:
        return None

    prefixes = _normalized_prefixes(ignore_prefixes)
    kinds: Dict[str, Tuple[str, str, str, bool]] = {}
    to_hash: List[str] = []
    total = 0
    for status, path in records:
        if _under_prefixes(path, prefixes):
            continue
        if "D" in status and status != PORCELAIN_RENAME_SOURCE:
            kinds[path] = (status, PORCELAIN_ABSENT, PORCELAIN_ABSENT, False)
            continue
        full = os.path.join(root, path)
        try:
            st = os.lstat(full)
        except FileNotFoundError:
            kinds[path] = (status, PORCELAIN_ABSENT, PORCELAIN_ABSENT, False)
            continue
        except OSError:
            kinds[path] = (status, PORCELAIN_UNREADABLE, PORCELAIN_UNREADABLE, False)
            continue
        if stat.S_ISLNK(st.st_mode):
            try:
                target = os.readlink(full)
            except OSError:
                kinds[path] = (status, PORCELAIN_UNREADABLE, PORCELAIN_UNREADABLE, False)
                continue
            kinds[path] = (status, "symlink", PORCELAIN_SYMLINK_PREFIX + target, False)
            continue
        if stat.S_ISDIR(st.st_mode):
            # A directory still reported whole even under
            # `--untracked-files=all` (a nested repository, an unsearchable
            # directory): its contents are not ours to hash, so it is compared
            # by status/path. Recording it `unreadable` (always changed) failed
            # every uncontained slot of any repo holding one, on every run.
            kinds[path] = (status, PORCELAIN_DIRECTORY, PORCELAIN_DIRECTORY, False)
            continue
        if not stat.S_ISREG(st.st_mode) or "\n" in path or not os.access(full, os.R_OK):
            # A device, a name `--stdin-paths` cannot carry, or a file we
            # cannot read.
            kinds[path] = (status, PORCELAIN_UNREADABLE, PORCELAIN_UNREADABLE, False)
            continue
        exec_bit = bool(st.st_mode & 0o111)
        kinds[path] = (status, "file", "", exec_bit)
        to_hash.append(path)
        total += st.st_size

    note: Optional[str] = None
    blobs: Dict[str, str] = {}
    if to_hash and total > PORCELAIN_HASH_CAP_BYTES:
        note = (
            f"[PORCELAIN_CHECK] the dirty set is {total // (1024 * 1024)} MB, over the "
            f"{PORCELAIN_HASH_CAP_BYTES // (1024 * 1024)} MB hashing cap: writes to "
            f"files that were already modified or untracked are not seen for this "
            f"slot (path + status comparison only)"
        )
    elif to_hash:
        def hash_batch(paths: List[str]) -> Tuple[int, List[str]]:
            hashed = subprocess.run(
                git_argv("hash-object", "--no-filters", "--stdin-paths", cwd=root),
                input="\n".join(paths) + "\n",
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                cwd=root, timeout=30,
            )
            return hashed.returncode, hashed.stdout.split()

        try:
            returncode, lines = hash_batch(to_hash)
            if returncode != 0:
                # `--stdin-paths` aborts on the first path it cannot open
                # (`fatal: Cannot open`, exit 128) — typically an editor's
                # transient `4913`/`.swp`/`~` file, present at `git status` and
                # gone by now. Fail closed on THAT path, not open on the whole
                # dirty set: re-lstat every path, record the vanished ones
                # `absent` and the no-longer-readable ones `unreadable`, and
                # hash the rest once more before degrading.
                retry: List[str] = []
                for path in to_hash:
                    status = kinds[path][0]
                    full = os.path.join(root, path)
                    try:
                        st = os.lstat(full)
                    except FileNotFoundError:
                        kinds[path] = (status, PORCELAIN_ABSENT, PORCELAIN_ABSENT, False)
                        continue
                    except OSError:
                        kinds[path] = (
                            status, PORCELAIN_UNREADABLE, PORCELAIN_UNREADABLE, False)
                        continue
                    if not stat.S_ISREG(st.st_mode) or not os.access(full, os.R_OK):
                        kinds[path] = (
                            status, PORCELAIN_UNREADABLE, PORCELAIN_UNREADABLE, False)
                        continue
                    retry.append(path)
                to_hash = retry
                returncode, lines = (hash_batch(to_hash) if to_hash else (0, []))
            if returncode != 0 or len(lines) != len(to_hash):
                raise subprocess.SubprocessError("hash-object failed")
            blobs = dict(zip(to_hash, lines))
        except (OSError, subprocess.SubprocessError):
            note = (
                "[PORCELAIN_CHECK] `git hash-object` could not hash the dirty set: "
                "writes to files that were already modified or untracked are not "
                "seen for this slot (path + status comparison only)"
            )
    if note is not None:
        print(note)

    entries: Dict[str, PorcelainEntry] = {}
    for path, (status, kind, blob, exec_bit) in kinds.items():
        if kind == "file":
            blob = blobs.get(path, "")
        entries[path] = PorcelainEntry(status, kind, blob, exec_bit)
    return PorcelainSnapshot(entries, hashed=note is None, note=note)


def _entry_changed(
    before: PorcelainEntry, after: PorcelainEntry, *, by_content: bool
) -> bool:
    if PORCELAIN_UNREADABLE in (before.kind, after.kind):
        return True  # fail closed: a path we could not read is never "same"
    deletion = (
        PORCELAIN_ABSENT in (before.kind, after.kind)
        or ("D" in before.status and before.status != PORCELAIN_RENAME_SOURCE)
        or ("D" in after.status and after.status != PORCELAIN_RENAME_SOURCE)
    )
    if before.status != after.status and deletion:
        return True  # a deletion on either side always counts as a change
    if not by_content:
        return before.status != after.status
    return (before.kind, before.blob, before.exec_bit) != (
        after.kind, after.blob, after.exec_bit)


def unexpected_writes(
    before: Optional[PorcelainSnapshot],
    after: Optional[PorcelainSnapshot],
    *,
    ignore_prefixes: Sequence[str] = (),
) -> List[str]:
    """Every path whose baseline entry differs between ``before`` and ``after``.

    Walks the **union** of both snapshots (plan §4.1), not ``after - before``:
    a path that appears, one that disappears (a pre-existing untracked file
    deleted, a dirty file restored to clean) and one whose kind, blob id,
    marker or exec bit changed are all reported. A status change with equal
    content and exec bit (``??`` → ``A ``, ``MM`` → ``M ``) is clean unless
    either side is a deletion; an ``unreadable`` path is always changed. If
    either snapshot degraded (``hashed=False``), both are compared by path and
    status only, which is the pre-§4.1 behaviour.

    ``ignore_prefixes`` is where the *plugin* writes during a slot — the
    plan's output directory (logs, result files, ``.status.json``, salvage
    requests, a sibling slot's answer) and ``.multi-llm/`` (the batch snapshot
    tmp files) — because those are this process's writes, made while the slot
    ran, and a check that blamed the model for them would fire on every run.
    :func:`porcelain_snapshot` already drops them before hashing; they are
    filtered again here so a snapshot taken without them still compares right.
    The fan-out call sites pass :func:`fanout_ignore_prefixes`, which also
    lists a declared workspace cache of an adapter in the same fan-out
    (aider's tag cache; plans/ask-answer-recovery-and-false-success.md D4.3).
    Either snapshot ``None`` means the check was not run, and the answer is
    "nothing to report". Sorted by path, for the record.
    """
    if before is None or after is None:
        return []
    prefixes = _normalized_prefixes(ignore_prefixes)
    by_content = bool(before.hashed and after.hashed)
    changed: List[str] = []
    for path in set(before.entries) | set(after.entries):
        if _under_prefixes(path, prefixes):
            continue
        b = before.entries.get(path)
        a = after.entries.get(path)
        if b is None or a is None or _entry_changed(b, a, by_content=by_content):
            changed.append(path)
    return sorted(changed)


def porcelain_check_applies(verdict: SandboxVerdict) -> bool:
    """Whether this slot is bracketed by the porcelain detective check.

    Read off the **rung id**, not off truthiness or the ``bypass`` flag's
    incidental agreement (T7, landlock rung, 2026-09-22): the check fires for
    the uncontained rung — :data:`SANDBOX_RUNG_UNSANDBOXED` — alone. A slot on
    a contained rung is fenced by the kernel and has nothing to detect after
    the fact; a sandboxed or ``not-required`` slot never took a rung at all.

    **The plugin's own jail (``plugin-landlock``) skips it too, and that is an
    accepted trade-off, not a claim that the kernel fences everything** (plan
    codex-sandbox-unavailable-findings-and-fixes §6 F1 "What it fixes",
    2026-09-30). The jail stops content writes outside its allow-list; what it
    does not stop — a flipped executable bit (checked instead by
    :func:`mode_check_applies`' mode check), ``$CODEX_HOME`` (checked by the
    home check), writes through a pathname Unix socket and timestamps (neither
    checked, by decision) — a whole-tree snapshot could not attribute anyway:
    on the host this was written for, every user edit and every sibling run's
    log in the window failed a codex review (§2a). Leaving this predicate
    unchanged *is* that decision; reversing it means changing the code here.
    """
    return (
        verdict.verdict == SANDBOX_DISPATCH_UNSANDBOXED
        and verdict.rung == SANDBOX_RUNG_UNSANDBOXED
    )


#: The model specs of the fan-out the current slot was scheduled in. Set per
#: slot task by :func:`spawn_fanout_slot` — each task carries its own context
#: copy, so nothing leaks between fan-outs — and read by
#: :func:`boundaryless_sibling_count`. Empty for a slot run outside a fan-out
#: (a direct call), which then has no siblings to count.
_FANOUT_ROSTER: "contextvars.ContextVar[Tuple[str, ...]]" = contextvars.ContextVar(
    "multi_llm_fanout_roster", default=()
)


def spawn_fanout_slot(roster: Sequence[str], coro: Any) -> "asyncio.Task[Any]":
    """``asyncio.create_task(coro)`` with the fan-out's roster in its context.

    The one piece of plumbing the detective check's sibling count needs: the
    fan-out already knows which slots it scheduled, and this hands that roster
    to each slot without touching a single slot signature (the lanes are stood
    in for by dozens of test fakes). ``ctx.run(create_task, …)`` rather than
    ``create_task(context=…)``, which is 3.11+ and this skill supports 3.10.
    """
    ctx = contextvars.copy_context()
    ctx.run(_FANOUT_ROSTER.set, tuple(roster))
    return ctx.run(asyncio.create_task, coro)


def boundaryless_sibling_count(
    model_spec: str, cwd: Optional[str], anchor: Optional[Union[str, Path]] = None
) -> int:
    """How many **other** slots of this slot's fan-out had no OS boundary.

    What makes the detective check's verdict ambiguous (T7, 2026-09-22): every
    such slot could have written into the tree during this slot's window. Two
    kinds count — an adapter whose ``generate`` sandbox probe answers
    ``not-required`` (it declares no sandbox by design: cursor-agent, pi,
    claude-code, …) and a sibling that also took the uncontained rung. A count
    taken from the uncontained verdicts alone would have read zero on the
    2026-09-22 run that misfired. A sandboxed, contained-rung, ``unknown`` or
    refused sibling does not count, and neither does a sibling on the plugin's
    own jail (``plugin-landlock``, 2026-09-30): the jail denies it every
    content write into the tree, which is what this count is about — its one
    residual there, a ``chmod``, is what :func:`mode_check_sibling_count`
    counts for the mode check. Derived from the answers the fan-out's own
    gate already gave (:func:`sandbox_refusal` and its cached probe, asked by
    every lane for every roster model), so it costs no new bookkeeping; the
    roster is what the fan-out *scheduled*, so under a ``max_parallel`` smaller
    than the roster a counted sibling may not have overlapped this window —
    the message says "in this fan-out", not "running at the same time".
    Blocking (a sibling not yet started may still need its probe); the caller
    hands it to a thread. A roster entry that cannot be resolved is skipped.
    """
    siblings = list(_FANOUT_ROSTER.get())
    if model_spec in siblings:
        siblings.remove(model_spec)
    count = 0
    for spec in siblings:
        try:
            provider_name, _model = parse_model_spec(spec, anchor=anchor)
            if _fanout_sandbox_verdict(provider_name, cwd).state == "not-required":
                count += 1
            elif porcelain_check_applies(sandbox_refusal(provider_name, cwd)):
                count += 1
        except Exception:  # noqa: BLE001 - a count may never end a fan-out
            continue
    return count


def bypass_write_violation(
    provider_name: str, paths: Sequence[str], *, boundaryless_siblings: int
) -> str:
    """The reason an uncontained slot is failed with when the detective check fires.

    It states what was **observed** — the tree changed during this slot's
    window, and how many other boundary-less slots of the fan-out could have
    made that change — and never who made it: a whole-tree porcelain diff has
    no evidence of authorship, and on 2026-09-22 it named codex for a file it
    had no reason to think codex wrote. ``boundaryless_siblings`` is
    :func:`boundaryless_sibling_count`'s answer; keyword-only and required, so
    no caller can print a count it never took.

    The **verdict** is unchanged by the wording (T7 changes the sentence, not
    the outcome): the slot still fails, its ``output`` is still dropped and its
    findings are still discarded — fail-closed, because on a machine with no
    contained rung this diff is the only containment evidence the slot has.
    Plan §4.4 (2026-09-24) names the writer T7's sentence left out: on run
    ``0c477c4d`` neither path was written by any slot — another session in the
    same repository changed them — so the sibling count alone still read as if
    the fan-out were the only candidate. The one exit from this verdict is the
    slot's own audited action stream (:func:`bypass_stream_audit_clears`).
    """
    n = boundaryless_siblings
    plural = "slot" if n == 1 else "slots"
    return (
        f"{SANDBOX_BYPASSED_MARKER} {provider_name}: the working tree changed "
        f"during this unsandboxed slot's window ({', '.join(paths)}) while {n} "
        f"other boundary-less {plural} in this fan-out, or any other process "
        f"writing to this repository, could also have written it; the check "
        f"cannot tell who made the change, so this slot fails closed and its "
        f"output is discarded"
    )


def bypass_stream_audit_clears(audits: Sequence[Any]) -> bool:
    """Whether a porcelain delta on an uncontained slot is downgraded (plan §4.3).

    ``audits`` is every attempt's ``details['readonly_audit']`` in the slot's
    snapshot window, in order — ``None`` for an attempt that carried none.
    True only when option B's switch is on
    (:data:`utils.readonly_audit.STREAM_AUDIT_EXEMPTION_ENABLED`, on since the
    2026-09-25 live hosted-type capture) AND every attempt audited clean: a clean
    last attempt never excuses an earlier one that wrote, was incomplete, or
    recorded nothing. Adapters with no structured action stream never carry a
    verdict, so their slots keep today's fail-closed verdict.
    """
    return _readonly_audit.exemption_applies(audits)


def bypass_write_not_attributed(provider_name: str, paths: Sequence[str]) -> str:
    """The warning a slot keeps its findings under when its stream cleared it.

    Plan §4.3: the tree changed during the window, and the slot's own audited
    stream shows it could not have made that change (every action read-only,
    the stream complete, on every attempt), so the change is reported — never
    attributed — and the slot counts. Recorded on
    ``progress.models[spec].warning`` by the call sites.
    """
    return (
        f"{SANDBOX_BYPASSED_MARKER} {provider_name}: the working tree changed "
        f"during this unsandboxed slot's window ({', '.join(paths)}), changed "
        f"during the window by something outside this slot — not attributed: "
        f"this slot's own action stream shows only read-only actions, so its "
        f"output is kept"
    )


# ---------------------------------------------------------------------------
# A fan-out slot on the plugin's own jail: the mode check, the home check,
# the jail's own lines, and the run's closing summary (plan
# codex-sandbox-unavailable-findings-and-fixes §6 F1 "What it fixes" and
# Limits, 2026-09-30)
# ---------------------------------------------------------------------------
#
# A slot on `plugin-landlock` skips the porcelain check (the predicate above is
# unchanged, by decision): the kernel denies every content write outside the
# allow-list, so what is left to detect after the fact is narrow and
# attributable. Two checks cover it, both keyed on the `incidental` grade:
#
# * the **mode check** — a flipped owner-execute bit on a tracked file breaks
#   the read-only contract (`git status` shows it, `git commit -a` records it)
#   and Landlock has no right for `chmod`. One `lstat` per tracked path, twice
#   per slot, no hashing and no size cap, so I3 does not return; and nothing
#   that fired the porcelain check without the slot's doing (editor saves,
#   builds, sibling runs' logs) flips the bit of an existing tracked file;
# * the **home check** — a write to `$CODEX_HOME`'s configuration, instruction
#   or plugin files persists into the user's later Codex sessions, outside any
#   jail. The invoker (`llm_client.invoke_with_provider`) fingerprints the set
#   around the child and hands the comparison back on `details["home_check"]`;
#   the lane applies the verdict here.
#
# Both take today's verdict on a narrower signal: fail closed, output
# discarded, unless `bypass_stream_audit_clears` accepts the slot's own stream
# — then a not-attributed warning and the output is kept. Neither ever reverts
# what it found: the user may be the one who changed it. Neither prints
# `[SANDBOX_BYPASSED]`, which keeps counting uncontained slots only.

#: The two modes git records for a regular file.
GIT_MODE_REGULAR = "100644"
GIT_MODE_EXECUTABLE = "100755"


def mode_check_applies(verdict: SandboxVerdict) -> bool:
    """Whether this slot is bracketed by the mode check: the ``incidental``
    grade (the plugin's own jail) alone — the mirror image of
    :func:`porcelain_check_applies`, which keeps ``unsandboxed``. A plain
    dispatch, a refusal, a contained rung and the uncontained rung never."""
    if verdict.verdict != SANDBOX_DISPATCH_UNSANDBOXED:
        return False
    return bool(getattr(verdict, "incidental", False)) or verdict.rung in _INCIDENTAL_RUNG_IDS


def home_check_applies(verdict: SandboxVerdict) -> bool:
    """Whether the fan-out applies the home check's verdict to this slot: the
    ``incidental`` grade, exactly as :func:`mode_check_applies`. A separate
    predicate so either decision can move without the other."""
    return mode_check_applies(verdict)


def mode_snapshot(repo_root: Optional[str]) -> Optional[Dict[str, str]]:
    """``{tracked path: "100644" | "100755"}`` for every tracked regular file,
    read from ``lstat``'s owner-execute bit; ``None`` when the check is off.

    ``None`` when there is no repository to ask, git cannot answer, or
    ``core.fileMode`` is false — git then reports no mode change, so a
    flipped bit does not break the read-only contract. A tracked path that is
    missing or not a regular file (a symlink, a submodule) is left out: its
    content and existence are the kernel's to protect, not this check's.
    Blocking; the lanes hand it to a thread. It never raises: a check that
    could not read the tree is a check that did not run.
    """
    try:
        return _mode_snapshot(repo_root)
    except Exception:  # noqa: BLE001 - a check may never end a slot
        return None


def _mode_snapshot(repo_root: Optional[str]) -> Optional[Dict[str, str]]:
    if not repo_root:
        return None
    try:
        top = subprocess.run(
            git_argv("rev-parse", "--show-toplevel", cwd=repo_root),
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            cwd=repo_root, timeout=30,
        )
        if top.returncode != 0:
            return None
        root = top.stdout.strip() or repo_root
        file_mode = subprocess.run(
            git_argv("config", "--bool", "core.fileMode", cwd=root),
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            cwd=root, timeout=30,
        )
        if file_mode.returncode == 0 and file_mode.stdout.strip() == "false":
            return None
        listed = subprocess.run(
            git_argv("ls-files", "-z", cwd=root), capture_output=True, cwd=root, timeout=120,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if listed.returncode != 0 or not isinstance(listed.stdout, bytes):
        return None
    if not isinstance(root, str) or not os.path.isdir(root):
        return None
    modes: Dict[str, str] = {}
    for raw in listed.stdout.split(b"\0"):
        if not raw:
            continue
        rel = os.fsdecode(raw)
        try:
            info = os.lstat(os.path.join(root, rel))
        except OSError:
            continue
        if not stat.S_ISREG(info.st_mode):
            continue
        modes[rel] = GIT_MODE_EXECUTABLE if info.st_mode & stat.S_IXUSR else GIT_MODE_REGULAR
    return modes


def mode_changes(
    before: Optional[Dict[str, str]], after: Optional[Dict[str, str]],
) -> List[Tuple[str, str, str]]:
    """``[(path, old mode, new mode), …]`` for every tracked path present in
    both snapshots whose executable bit flipped; ``[]`` when either side is
    ``None`` (the check did not run)."""
    if before is None or after is None:
        return []
    return [
        (path, before[path], after[path])
        for path in sorted(set(before) & set(after))
        if before[path] != after[path]
    ]


def _describe_mode_changes(changes: Sequence[Tuple[str, str, str]]) -> str:
    return ", ".join(f"{path} {old} → {new}" for path, old, new in changes)


def mode_check_sibling_count(
    model_spec: str, cwd: Optional[str], anchor: Optional[Union[str, Path]] = None
) -> int:
    """How many **other** slots of this fan-out could also have changed a
    file mode: the kinds :func:`boundaryless_sibling_count` counts, plus a
    sibling on the plugin's own jail — which does not stop ``chmod`` either.
    Blocking; the caller hands it to a thread."""
    siblings = list(_FANOUT_ROSTER.get())
    if model_spec in siblings:
        siblings.remove(model_spec)
    count = 0
    for spec in siblings:
        try:
            provider_name, _model = parse_model_spec(spec, anchor=anchor)
            if _fanout_sandbox_verdict(provider_name, cwd).state == "not-required":
                count += 1
                continue
            verdict = sandbox_refusal(provider_name, cwd)
            if porcelain_check_applies(verdict) or mode_check_applies(verdict):
                count += 1
        except Exception:  # noqa: BLE001 - a count may never end a fan-out
            continue
    return count


def mode_check_violation(
    provider_name: str, changes: Sequence[Tuple[str, str, str]], *, other_slots: int
) -> str:
    """The reason a slot on the plugin's jail fails with when a tracked file's
    executable bit flipped in its window — what was **observed**, never who
    did it (F1 "What it fixes"). ``other_slots`` is
    :func:`mode_check_sibling_count`'s answer; keyword-only and required."""
    plural = "slot" if other_slots == 1 else "slots"
    return (
        f"{MODE_CHECK_MARKER} {provider_name}: a tracked file's executable bit "
        f"changed during this slot on the plugin's Landlock jail, which does not "
        f"stop chmod ({_describe_mode_changes(changes)}), while {other_slots} "
        f"other {plural} in this fan-out that could also change a file mode, or "
        f"any other process writing to this repository, could also have made "
        f"the change; the mode check cannot tell who made it, so this slot "
        f"fails closed and its output is discarded (the mode is left as found)"
    )


def mode_check_not_attributed(
    provider_name: str, changes: Sequence[Tuple[str, str, str]]
) -> str:
    """The warning a slot keeps its output under when its own audited stream
    shows only read-only actions."""
    return (
        f"{MODE_CHECK_MARKER} {provider_name}: a tracked file's executable bit "
        f"changed during this slot's window ({_describe_mode_changes(changes)}) "
        f"— not attributed: this slot's own action stream shows only read-only "
        f"actions, so its output is kept (the mode is left as found)"
    )


def merge_home_checks(records: Sequence[Any]) -> Optional[Dict[str, Any]]:
    """Every attempt's ``details["home_check"]`` of one slot, folded into one
    record: changed files, config key names and foreign trust tables unioned
    in order, the most other live children any attempt saw. ``None`` when no
    attempt carried one."""
    merged: Optional[Dict[str, Any]] = None
    for record in records or ():
        if not isinstance(record, dict):
            continue
        if merged is None:
            merged = {
                "home": record.get("home") or "$CODEX_HOME",
                "changed": [], "config_keys": [], "foreign_trust": [],
                "other_live_children": 0,
            }
        for key in ("changed", "config_keys", "foreign_trust"):
            for item in record.get(key) or ():
                if item not in merged[key]:
                    merged[key].append(item)
        merged["other_live_children"] = max(
            int(merged["other_live_children"] or 0),
            int(record.get("other_live_children") or 0),
        )
    return merged


def _describe_home_change(record: Dict[str, Any]) -> str:
    """``landlock_dispatch.describe_changed`` over a slot's merged record, so
    both lanes name and summarize a change the same way."""
    from .landlock_dispatch import describe_changed

    return describe_changed(
        [str(name) for name in record.get("changed") or ()],
        record.get("config_keys") or (),
    )


def home_check_line(provider_name: str, record: Dict[str, Any], *, kept: bool) -> str:
    """The one ``[CODEX_HOME_CHECK]`` line for a slot whose ``$CODEX_HOME``
    security-relevant set changed (F1 Limits): each changed file, and for
    ``config.toml`` the changed table or key names — never a value, the file
    can hold MCP server tokens — how many other children of this run were live
    in the window, and the verdict."""
    n = int(record.get("other_live_children") or 0)
    others = (
        f"{n} other {provider_name} child{'ren' if n != 1 else ''} of this run "
        f"{'was' if n == 1 else 'were'} live in the window"
    )
    line = (
        f"{CODEX_HOME_CHECK_MARKER} {provider_name}: {record.get('home') or '$CODEX_HOME'} "
        f"changed during this slot on the plugin's Landlock jail, which does not "
        f"stop writes there: {_describe_home_change(record)}; {others}; the "
        f"change persists into later {provider_name} sessions and was not "
        f"reverted — review those files"
    )
    if kept:
        return line + (
            "; not attributed: this slot's own action stream shows only "
            "read-only actions, so its output is kept"
        )
    return line + "; this slot fails closed and its output is discarded"


def foreign_trust_line(provider_name: str, record: Dict[str, Any]) -> Any:
    """The closing-summary-only note for trust tables added to ``config.toml``
    in a slot's window besides the run's own cwd (I12's entries; never a
    failure): this run's batch or a concurrent codex session added them. A
    ``landlock_dispatch.TrustEntriesNote``, rendered by
    :func:`print_closing_summary` with the executor lane's wording and naming
    only the tables still there then (fix round 17)."""
    from .landlock_dispatch import TrustEntriesNote

    home = record.get("home") or None
    return TrustEntriesNote(
        home=os.path.expanduser(home) if home and home != "$CODEX_HOME" else None,
        paths=tuple(record.get("foreign_trust") or ()),
        provider=provider_name,
    )


#: Lines a run repeats in its closing summary, keyed by the run's phase (or
#: question) directory: every ``[CODEX_HOME_CHECK]`` and ``[JAIL_DENIED]``
#: line, and the foreign-trust notes that appear only there — the change
#: outlives the run, so the last thing it prints names it again.
_CLOSING_LINES: Dict[str, List[Any]] = {}
_CLOSING_LOCK = threading.Lock()


def _closing_key(key: Any) -> str:
    return os.path.realpath(str(key)) if key else ""


def phase_summary_key(plan_path: Union[str, Path], phase_name: str) -> str:
    """The closing-summary key of a plan's phase: its phase directory,
    computed and never created (``output_dir_path``, not ``get_phase_dir``)."""
    try:
        from .output_handler import PHASE_DIRECTORIES, output_dir_path
    except ImportError:  # pragma: no cover - direct-script import shim
        from utils.output_handler import PHASE_DIRECTORIES, output_dir_path  # type: ignore[no-redef]
    return str(
        output_dir_path(Path(plan_path)) / PHASE_DIRECTORIES.get(phase_name, phase_name)
    )


def note_for_closing_summary(key: Any, line: Any) -> None:
    """Keep ``line`` for the closing summary of the run keyed by ``key``."""
    if not line:
        return
    with _CLOSING_LOCK:
        lines = _CLOSING_LINES.setdefault(_closing_key(key), [])
        if line not in lines:
            lines.append(line)


def print_closing_summary(key: Any) -> List[str]:
    """Print, once, the lines :func:`note_for_closing_summary` kept for this
    run, under one heading; returns them (``[]`` prints nothing)."""
    from .landlock_dispatch import render_summary_entries

    with _CLOSING_LOCK:
        entries = _CLOSING_LINES.pop(_closing_key(key), [])
    lines = render_summary_entries(entries)
    if lines:
        print("\n=== Sandbox and jail checks (repeated from this run) ===")
        for line in lines:
            print(line)
    return lines


def report_jail_outcome(display_name: str, details: Optional[Dict[str, Any]], summary_key: Any) -> None:
    """Print a jailed attempt's own lines, once: its ``[JAIL_DENIED]`` line
    (built by the invoker, noted for the closing summary) and the count and
    first three paths of the writes the jail denied inside the model's own
    commands — which fail nothing: that is the jail stopping a stray write,
    and it lets a review that calls a tool broken be traced to the jail."""
    details = details or {}
    failure = details.get("jail_failure")
    if isinstance(failure, dict) and failure.get("notice"):
        line = str(failure["notice"])
        print(f"[{display_name}] {line}")
        note_for_closing_summary(summary_key, line)
    denials = details.get("jail_denials")
    if isinstance(denials, dict) and denials.get("total"):
        paths = [_render_home(p) for p in denials.get("paths") or () if p]
        total = int(denials["total"])
        print(
            f"[{display_name}] the plugin's Landlock jail denied {total} "
            f"write{'s' if total != 1 else ''} inside the model's own commands "
            f"(not a failure)" + (f": {', '.join(paths)}" if paths else "")
        )


#: ``details["failure_reason"]`` for a jailed slot whose jail could not be set
#: up — no declared wrapping rung, or no scratch directory outside the repo —
#: so nothing was spawned (``llm_client`` writes it). Non-retryable like
#: ``FAILURE_JAIL_DENIED``, and never moved to another rung.
FAILURE_JAIL_SETUP_FAILED = "jail-setup-failed"

#: Both fan-out failure reasons of the plugin's jail; each gets the ladder
#: status ``STATUS_JAIL_DENIED`` (plan codex-sandbox-unavailable Implementation
#: Notes: "never retried"), whatever its error text classifies as.
_JAIL_FAILURE_REASONS = frozenset({FAILURE_JAIL_DENIED, FAILURE_JAIL_SETUP_FAILED})


def is_jail_denied(details: Optional[Dict[str, Any]]) -> bool:
    """Whether an attempt failed on the plugin's jail (``jail-denied`` or
    ``jail-setup-failed``) — non-retryable, and never moved to another rung."""
    return (details or {}).get("failure_reason") in _JAIL_FAILURE_REASONS


async def run_incidental_checks(
    sandbox: SandboxVerdict,
    *,
    provider_name: str,
    display_name: str,
    model_spec: str,
    project_root: Optional[str],
    plan_path: Union[str, Path],
    mode_before: Optional[Dict[str, str]],
    home_checks: Sequence[Any],
    audits: Sequence[Any],
    tracker: Optional[Any] = None,
    summary_key: Any = None,
) -> Optional[str]:
    """Apply the mode check and the home check to one fan-out slot on the
    plugin's jail, after its last attempt; the fail-closed reason, or ``None``.

    The shared verdict of all three fan-out lanes (``run_single_model``,
    ``code_review_orchestrator.run_single_review``, ``ask_orchestrator``'s
    ``ask_one``), so they print one wording. ``None`` for a slot not on the
    ``incidental`` grade — no git call at all.
    """
    if not mode_check_applies(sandbox):
        return None
    if tracker is not None:
        try:
            tracker.record_readonly_audit(
                model_spec, _readonly_audit.combine_audits(audits).to_dict()
            )
        except Exception:  # noqa: BLE001 - bookkeeping never ends a slot
            pass
    violations: List[str] = []
    if mode_before is not None:
        mode_after = await asyncio.to_thread(mode_snapshot, project_root)
        changes = mode_changes(mode_before, mode_after)
        if changes:
            if bypass_stream_audit_clears(audits):
                warning = mode_check_not_attributed(provider_name, changes)
                print(f"[{display_name}] {warning}")
                if tracker is not None:
                    tracker.warn(model_spec, warning)
            else:
                siblings = await asyncio.to_thread(
                    mode_check_sibling_count, model_spec, project_root, plan_path
                )
                violation = mode_check_violation(
                    provider_name, changes, other_slots=siblings
                )
                print(f"[{display_name}] {violation}")
                violations.append(violation)
    if home_check_applies(sandbox):
        record = merge_home_checks(home_checks)
        if record is not None and record.get("changed"):
            kept = bypass_stream_audit_clears(audits)
            line = home_check_line(provider_name, record, kept=kept)
            print(f"[{display_name}] {line}")
            note_for_closing_summary(summary_key, line)
            if kept:
                if tracker is not None:
                    tracker.warn(model_spec, line)
            else:
                violations.append(line)
        if record is not None and record.get("foreign_trust"):
            note_for_closing_summary(summary_key, foreign_trust_line(provider_name, record))
    return "; ".join(violations) or None


def bypass_ignore_prefixes(
    plan_path: Union[str, Path], project_root: Optional[str]
) -> List[str]:
    """The repo-relative trees the plugin itself writes during a slot.

    The plan's output directory (``output_dir_path``: logs, per-model results,
    ``.status.json``, salvage requests, an ask's answer files) and
    ``.multi-llm/`` (batch snapshot tmp files, the write-safety snapshots). A
    plan outside the repository, or no repository, contributes nothing —
    the check then reports every delta, which is the conservative reading.
    """
    prefixes = [".multi-llm"]
    if not project_root:
        return prefixes
    # `output_dir_path`, not `get_output_dir`: the latter `mkdir`s, and a
    # detective check must not create the directory it is about to exclude.
    try:
        from .output_handler import output_dir_path
    except ImportError:  # pragma: no cover - direct-script import shim
        from utils.output_handler import output_dir_path  # type: ignore[no-redef]
    try:
        out_dir = os.path.realpath(str(output_dir_path(Path(plan_path))))
        relative = os.path.relpath(out_dir, os.path.realpath(project_root))
    except (OSError, ValueError):
        return prefixes
    if relative and not relative.startswith(".."):
        prefixes.append(relative.replace(os.sep, "/"))
    return prefixes


def fanout_workspace_caches(anchor: Optional[Union[str, Path]] = None) -> List[str]:
    """The ``workspace_caches`` every adapter in this slot's fan-out declares.

    Read off the fan-out's roster (:data:`_FANOUT_ROSTER`, the source
    :func:`boundaryless_sibling_count` reads), so aider's
    ``.aider.tags.cache.v4/`` is exempt **only** when an aider slot was
    scheduled beside this one (plans/ask-answer-recovery-and-false-success.md
    D4.3, mirroring the container harness's per-CLI ``tool_artifacts``). A slot
    run outside a fan-out has an empty roster and exempts nothing, and a
    roster entry that cannot be resolved contributes nothing — the
    conservative reading, since a change there then still counts.
    """
    caches: List[str] = []
    for spec in _FANOUT_ROSTER.get():
        try:
            provider_name, _model = parse_model_spec(spec, anchor=anchor)
            provider = get_provider(provider_name)
        except Exception:  # noqa: BLE001 - an exemption may never end a slot
            continue
        for cache in getattr(provider, "workspace_caches", ()) or ():
            if isinstance(cache, str) and cache.strip("/") and cache not in caches:
                caches.append(cache)
    return caches


def fanout_ignore_prefixes(
    plan_path: Union[str, Path],
    project_root: Optional[str],
    anchor: Optional[Union[str, Path]] = None,
) -> List[str]:
    """:func:`bypass_ignore_prefixes`, plus the fan-out's declared workspace caches.

    The roster-aware form every porcelain call site uses (D4.3): the plugin's
    own trees, then each ``workspace_caches`` entry of an adapter in this
    slot's fan-out (:func:`fanout_workspace_caches`). Must be evaluated inside
    the slot's task — where the roster context lives — not in a worker thread
    started without it (``asyncio.to_thread`` copies the context, so either is
    fine there). ``anchor`` resolves bare model specs; it defaults to
    ``plan_path``.
    """
    prefixes = bypass_ignore_prefixes(plan_path, project_root)
    for cache in fanout_workspace_caches(anchor if anchor is not None else plan_path):
        if cache not in prefixes:
            prefixes.append(cache)
    return prefixes


def report_misnamed_result(
    model_spec: str,
    result: Dict[str, Any],
    phase_dir: Union[str, Path],
) -> str:
    """Say that a slot read its answer from a misnamed file (both lanes).

    One ``[RESULT_FILE_MISNAMED]`` line on stdout, and the same sentence in
    ``.status.json``'s ``result_notes`` (the report's ``**Result files:**``
    line) and ``progress.notes`` (``status``'s ``note:`` lines and a terminal
    poll's ``notice``). Not the slot's ``warning``: that key holds one
    sentence, and a bypassed slot's ``[SANDBOX_BYPASSED] … not attributed``
    warning must not be overwritten by this one. Returns the sentence.
    """
    expected = os.path.basename(str(result.get("output_file") or "")) or (
        f"{sanitize_model_name(model_spec)}.json"
    )
    note = _result_files.misnamed_result_note(
        model_spec, str(result.get("misnamed_from")), expected
    )
    print(f"[RESULT_FILE_MISNAMED] {note}")
    _result_files.append_result_note(phase_dir, note)
    return note


def _answer_text(data: Any) -> str:
    """The text :func:`save_model_result` parses, from a completed run's ``data``.

    A parsed payload is serialized back whatever its length: ``[]`` is a whole
    answer, the one a reviewer that found nothing gives. Both success returns
    of :func:`run_single_model` used to test the payload's truthiness, turned
    that ``[]`` into ``""``, and ``save_model_result`` then read a model that
    answered as one that left no output (measured 2026-10-09, plan
    improve-plan-and-improve-code T3: two mock reviewers each answered ``[]``,
    both were recorded failed with ``Unknown error``, and review-plan exited 3
    "All models failed" instead of completing a clean review).
    """
    if data is None:
        return ""
    if isinstance(data, str):
        return data
    return json.dumps(data)


async def run_single_model(
    model_spec: str,
    plan_path: str,
    prompt_template: str,
    prompt_context: Dict[str, Any],
    phase_name: str,
    invoke_phase: str,
    timeout: Optional[float] = None,
    retry_count: int = 0,
    out_dir: Optional[str] = None,
    prefix: Optional[str] = None,
    *,
    tracker: Optional[FanoutProgress] = None,
    run_model_specs: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    """Run a single model review with file-based JSON output.

    Retries are the shared :class:`~utils.retry_ladder.RetryLadder` (§7.1.b),
    **not** the recursion this function used to be. Two self-calls — one for a
    rate limit, one for a network error — each re-entered with the *same*
    ``timeout`` argument, so a claude-code slot at ``default_timeout: 1800``
    could run 4 × 1800 s + 35 s of backoff ≈ 2 h against a configured ceiling of
    1800 s (§7.5's opening paragraph). Being a tail call inside an ``async def``
    it also kept its retry state in a place no budget could see.

    The loop below is the sketch in §7.1.b, and its only lane-specific lines are
    the ``await``ed dispatch and the ``await asyncio.sleep``. It is deliberately
    **not** Lane B's loop: this coroutine is awaited inside ``asyncio.gather``
    under two semaphores, so a blocking retry loop here would serialize the whole
    fan-out. What the two lanes share is the policy object.

    Args:
        model_spec: Model specification (e.g., 'cursor-agent:auto')
        plan_path: Absolute path to the plan file
        prompt_template: The prompt template string
        prompt_context: Dict of variables to substitute in the prompt
        phase_name: Phase directory name (e.g., 'review-plan', 'review-tasks')
        invoke_phase: Phase name for invoke_with_file_output (e.g., 'plan_review', 'task_review')
        timeout: Optional timeout override in seconds — the slot's **whole**
            wall-clock budget, taken once as a deadline and never re-issued.
        tracker: The fan-out's :class:`~utils.progress_tracker.FanoutProgress`,
            when the caller built one. This coroutine supplies only what the
            helper around it cannot see — the ``running`` transition at **both**
            start prints (once per ladder attempt on the file-based lane, so
            ``attempt`` tracks ``ladder.attempt_index``) and the ``retrying``
            transition at the backoff print. Every *terminal* transition is
            ``run_models_concurrent``'s, derived from the result dict this
            returns, so the pre-dispatch sandbox refusal below needs none of its
            own: it returns ``source: "not-dispatched"`` and the helper retires
            the slot from that. ``None`` (a direct call, a test) keeps every
            line here byte-for-byte what it was.
        retry_count: Vestigial. Retry state lives in the ladder now, which is the
            point of §7.5 rule 1; the parameter survives only because
            ``review_plan_orchestrator``'s backward-compatible wrapper forwards
            it. Passing a non-zero value has no effect.
        out_dir: Optional output directory for log files and JSON output
        prefix: Optional prefix for log file names
        run_model_specs: Every model of this fan-out, forwarded to
            ``invoke_with_file_output`` so a result written under the wrong
            name is read from where the model put it (live run 10). ``None``
            (a direct call) never looks.

    Returns:
        Dict with keys: success, output, error, prompt, stdout, stderr,
        duration_seconds, model_spec, source — plus, when the invocation
        reported them, :func:`served_model_fields`' attribution keys and
        :func:`usage_fields`' ``usage``. Both are built by a function rather
        than spelled at each return, so the record a winning slot produces and
        the record a losing one produces cannot drift apart.

        ``output`` and ``stdout`` are **not** two names for one thing, and the
        failure returns below are the only place the difference is load-bearing.
        ``output`` means *the answer produced by a run that completed*: it is
        what :func:`save_model_result` parses, validates and writes to
        ``{model}.json``, so it stays ``None`` on every losing path however much
        text the child left behind. ``stdout`` means *the text a failed run left
        behind, which only salvage may read* — the truncated or fenced array a
        provider streamed before it was killed at the deadline or crashed on
        teardown, which is the single most salvageable failure this skill has.

        Widening ``output`` to carry that text instead is the obvious fix and it
        is the wrong one. ``save_model_result`` would then fall through to its
        parse block, and a hard failure whose stdout happened to hold a
        well-formed suggestions array would be written to ``{model}.json`` and
        counted as that model's completed review — a crashed run recorded as a
        result, which is :func:`retire_salvage_artifacts`'s phantom participant
        arriving through a door the salvage gate never sees. Keeping the two
        keys distinct here is what lets ``save_model_result`` distinguish "no
        output" from "output only salvage may read".

        The text itself is ``details["stdout_excerpt"]``, which
        ``utils/llm_client._attach_stdout_excerpt`` (:413) attaches on all three
        losing paths — non-zero exit, timeout kill, and the zero exit whose
        output would not parse — already ``_redact``ed then ``_bound_stream``ed
        in that order (§4.5/§4.4). That is the only copy of the stream that has
        been through the redactor, and a salvage request is an artifact a human
        reads, so it is the copy that travels. Returns that had no child to
        produce it keep ``""`` and say so in place, rather than attaching an
        always-empty key that later readers would have to re-derive the
        emptiness of.
    """
    import time
    start_time = time.time()

    project_root = get_project_root(plan_path)
    # `plan_path` IS the discovery anchor (§9.3.a): no new value is computed
    # here, the existing one simply stops being thrown away at the spawn.
    provider_name, model_name = parse_model_spec(model_spec, anchor=plan_path)
    display_name = f"{provider_name}:{model_name}"

    effective_prefix = prefix or sanitize_prefix(os.path.basename(plan_path))
    full_prompt_context = {**prompt_context}
    if "prefix" not in full_prompt_context:
        full_prompt_context["prefix"] = effective_prefix

    effective_timeout = (
        timeout if timeout is not None
        else get_provider_timeout(provider_name, anchor=plan_path)
    )

    log_file = None
    if out_dir and prefix:
        sanitized_model = sanitize_model_name(model_spec)
        phase_dir = get_phase_dir(Path(plan_path), phase_name)
        os.makedirs(phase_dir, exist_ok=True)
        log_file = os.path.join(str(phase_dir), f"log_{sanitized_model}.txt")

    # D6 step 3, on the fan-out's own profile: ask this runner's sandbox whether
    # it can start at all, before either lane below dispatches. A review slot is
    # a `generate` dispatch, and a bubblewrap that cannot start denies the child
    # every file operation — the READ of the plan file included, which is this
    # phase's whole input. Ungated, such a slot came back in 28 s with a one-item
    # "review" saying the plan could not be read, and was scored a success
    # (`codex:gpt-5.6-terra`, 2026-09-16). `unknown` and `not-required` dispatch
    # exactly as before: a probe that could not be read is a diagnostic and never
    # a gate, and a sandbox that then dies mid-dispatch still lands on the D3k
    # ladder as rung 1.
    #
    # The third answer (D6 override, 2026-09-17): `dispatch_unsandboxed`, only
    # when the probe said `unavailable` AND `providers.<name>.sandbox_fallback`
    # resolves to `auto` (the default; `off` restores the refusal). The slot
    # then runs with the flag, prints the one `[SANDBOX_BYPASSED]` line, and is
    # bracketed by the porcelain detective check below — nothing else about
    # the lane moves.
    sandbox = await asyncio.to_thread(sandbox_refusal, provider_name, project_root)
    if sandbox.refused:
        reason = sandbox.reason
        print(f"[{display_name}] {reason}")
        return {
            "success": False, "output": None,
            "error": reason,
            # `prompt` and `stdout` stay empty for the reason rule 4's refusal
            # leaves them empty: nothing was dispatched, so there is no stream to
            # excerpt — and neither lane below has chosen an output location yet,
            # so a prompt rendered here would name a file no dispatch ever picked.
            "prompt": "", "stdout": "", "stderr": "",
            "duration_seconds": time.time() - start_time,
            "model_spec": model_spec,
            "source": "not-dispatched",
        }
    tree_before: Optional[PorcelainSnapshot] = None
    # The roster-aware form (plans/ask-answer-recovery-and-false-success.md
    # D4.3): an aider sibling's `.aider.tags.cache.v4/` is not this slot's
    # write. Computed here, in the slot's task, where the fan-out roster lives;
    # the before snapshot, `_bypass_write_check` and `unexpected_writes` all
    # read this one list.
    ignore_prefixes = fanout_ignore_prefixes(plan_path, project_root, anchor=plan_path)
    if sandbox.fallback:
        print(f"[{display_name}] {sandbox.reason}")
    if porcelain_check_applies(sandbox):
        tree_before = await asyncio.to_thread(
            porcelain_snapshot, project_root, ignore_prefixes=ignore_prefixes
        )
    # The plugin's own jail (plan codex-sandbox-unavailable §6 F1, 2026-09-30):
    # no porcelain check (above, unchanged by decision), the mode check's
    # before-snapshot instead, and this run's closing-summary key for the home
    # check's and the jail's lines.
    summary_key = phase_summary_key(plan_path, phase_name)
    mode_before: Optional[Dict[str, str]] = None
    if mode_check_applies(sandbox):
        mode_before = await asyncio.to_thread(mode_snapshot, project_root)

    async def _incidental_check(
        home_checks: Sequence[Any], audits: Sequence[Any]
    ) -> Optional[str]:
        """The mode check and the home check's verdict for a slot on the
        plugin's jail, once, after the last attempt (``None`` elsewhere)."""
        return await run_incidental_checks(
            sandbox, provider_name=provider_name, display_name=display_name,
            model_spec=model_spec, project_root=project_root, plan_path=plan_path,
            mode_before=mode_before, home_checks=home_checks, audits=audits,
            tracker=tracker, summary_key=summary_key,
        )

    async def _bypass_write_check(audits: Sequence[Any]) -> Optional[str]:
        """The reason to fail a bypassed slot whose run changed the tree, or ``None``.

        Runs once, after the last attempt. A delta fails the slot whatever the
        attempt reported — a review that also edited the repository is not a
        review this phase may count — and nothing is restored: no snapshot was
        taken of the files, so the operator is told which paths and left to
        decide. The caller drops ``output`` so ``save_model_result`` never
        parses it — and so the slot's findings are discarded, never kept
        beside the failure: that is the fail-closed policy, and the reason line
        (:func:`bypass_write_violation`) reports the change without naming an
        author. ``None`` for every slot not on the uncontained rung — gated on
        the rung id (:func:`porcelain_check_applies`), so a contained-rung or
        sandboxed slot makes no git call at all. The ``git status`` runs in a
        thread like the one before the slot: on a large repository it is not
        instant, and the sibling slots share this event loop.

        ``audits`` is every attempt's ``details['readonly_audit']`` in this
        slot's window (plan §4.3). When their AND is clean and option B is
        switched on (:func:`bypass_stream_audit_clears`), a delta is reported
        as a ``not attributed`` warning on ``progress.models[spec].warning``
        and the slot keeps its output; otherwise the verdict is as before.
        """
        if not porcelain_check_applies(sandbox):
            return None
        if tracker is not None:
            tracker.record_readonly_audit(
                model_spec, _readonly_audit.combine_audits(audits).to_dict()
            )
        tree_after = await asyncio.to_thread(
            porcelain_snapshot, project_root, ignore_prefixes=ignore_prefixes
        )
        touched = unexpected_writes(
            tree_before, tree_after, ignore_prefixes=ignore_prefixes,
        )
        if not touched:
            return None
        if bypass_stream_audit_clears(audits):
            warning = bypass_write_not_attributed(provider_name, touched)
            print(f"[{display_name}] {warning}")
            if tracker is not None:
                tracker.warn(model_spec, warning)
            return None
        siblings = await asyncio.to_thread(
            boundaryless_sibling_count, model_spec, project_root, plan_path
        )
        violation = bypass_write_violation(
            provider_name, touched, boundaryless_siblings=siblings
        )
        print(f"[{display_name}] {violation}")
        return violation

    # Fall back to old method if no out_dir provided
    if not out_dir:
        # There is no output file on this path at all — the result is whatever
        # `invoke_with_provider` parses off stdout — so the prompt asks for
        # stdout outright, for every provider. It used to interpolate the string
        # "(stdout)" into "Write your JSON output to this file:", which named a
        # channel as if it were a path. The working-limits minutes come from the
        # same `int(effective_timeout)` the one dispatch below is handed.
        prompt = prompt_template.format(
            **full_prompt_context,
            output_json_path="(stdout)",
            output_location=STDOUT_OUTPUT_LOCATION,
            working_limits=render_working_limits(int(effective_timeout)),
        )
        try:
            print(f"[{display_name}] Starting review (timeout: {effective_timeout}s)...")
            if tracker is not None:
                # This lane makes exactly one dispatch and has no ladder, so the
                # attempt is 1 by construction. `timeout_s` is the slot's whole
                # budget, which is also the seed's value unless a per-slot
                # override moved it — the one thing the seed could not know.
                tracker.running(
                    model_spec, attempt=1, timeout_s=effective_timeout
                )
            result = await asyncio.to_thread(
                invoke_with_provider,
                prompt=prompt,
                model_spec=model_spec,
                timeout=int(effective_timeout),
                log_file=log_file,
                cwd=project_root,
                anchor=plan_path,
                **sandbox_fallback_kwargs(sandbox),
            )
            duration = time.time() - start_time
            details = result.get("details", {})
            stderr_text = details.get("stderr", "")
            report_jail_outcome(display_name, details, summary_key)

            violation = await _bypass_write_check([details.get("readonly_audit")])
            if violation is None:
                violation = await _incidental_check(
                    [details.get("home_check")], [details.get("readonly_audit")]
                )
            if violation is not None:
                return {
                    "success": False, "output": None, "error": violation,
                    "prompt": prompt, "stdout": details.get("stdout_excerpt", ""),
                    **salvage_text_fields(details),
                    "stderr": stderr_text, "duration_seconds": duration,
                    "model_spec": model_spec, "source": "stdout",
                    # The slot ran — bypassed, which is why it was checked at
                    # all — so the record keeps its `sandbox` word: without it
                    # `models_served`, `progress.sandbox_bypassed` and the
                    # retired-rung line all lose the one slot that most needs
                    # them. Every failure below that ran a child does the same.
                    **served_model_fields(details),
                    **usage_fields(details),
                }

            if result["success"]:
                output_str = _answer_text(result.get("data"))
                return {
                    "success": True,
                    "output": output_str,
                    "error": None,
                    "prompt": prompt,
                    "stdout": output_str,
                    "stderr": stderr_text,
                    "duration_seconds": duration,
                    "model_spec": model_spec,
                    "source": "stdout",
                    **served_model_fields(details),
                    # Stage U: and what it spent. Every record built from THIS
                    # invocation's `details` carries it — the win, the loss, and
                    # the harness verdicts above — because a slot that failed
                    # spent real money too, and the run that ends without an
                    # answer is the one an operator asks the cost of. The two
                    # `except` handlers below are the exception, and only
                    # because `details` is not bound on the path that reaches
                    # them: they catch OUR failure, not the child's.
                    **usage_fields(details),
                }
            else:
                return {
                    "success": False,
                    "output": None,
                    # `details` is this very invocation's, read off `result` a
                    # dozen lines up, so a provider that streamed an array to
                    # stdout and then exited non-zero has its answer here. The
                    # older of the two dispatch paths, but it loses the same way
                    # and the fix is the same one — see `Returns:` above for why
                    # this is `stdout` and not `output`.
                    "error": result.get("error", "Unknown error"),
                    "prompt": prompt,
                    "stdout": details.get("stdout_excerpt", ""),
                    **salvage_text_fields(details),
                    **salvage_failure_fields(result),
                    "stderr": stderr_text,
                    "duration_seconds": duration,
                    "model_spec": model_spec,
                    "source": "stdout",
                    **served_model_fields(details),
                    **usage_fields(details),
                }
        except Exception as e:
            duration = time.time() - start_time
            # `stdout` stays `""` here, and deliberately. This handler catches
            # *our* exception, not the child's — `error` names a Python failure
            # in this coroutine, and there is no losing-run excerpt that belongs
            # beside it. Reading one would also be unsafe: `details` is assigned
            # inside the `try`, *after* `invoke_with_provider` returns, so on the
            # likeliest arrival here (the invocation itself raising) the name is
            # unbound and the module-level initialiser further down has not run
            # for this path. That would trade a recorded exception for a
            # `NameError`, which is the one outcome worse than a missing excerpt.
            return {
                "success": False,
                "output": None,
                "error": f"Exception: {type(e).__name__}: {e}",
                "prompt": prompt,
                "stdout": "",
                "stderr": "",
                "duration_seconds": duration,
                "model_spec": model_spec,
                "source": "stdout"
            }

    result: Optional[Dict[str, Any]] = None
    details: Dict[str, Any] = {}
    # What the slot has spent across EVERY attempt, not the last one's
    # `details`: the loop below rebinds that on each pass, so a record
    # built from it reports the winning attempt alone. `None` until an
    # adapter reports something, which is what keeps "never reported"
    # distinguishable from a measured zero.
    slot_usage: Optional[Dict[str, Any]] = None
    #: Every attempt's `details['readonly_audit']` (plan §4.3), `None` included.
    slot_audits: List[Any] = []
    #: Every attempt's `details['home_check']` on the plugin's jail (F1 Limits).
    slot_home_checks: List[Any] = []
    stderr_text = ""
    source = "unknown"
    status: Optional[str] = None
    action = None

    try:
        # §7.5 rule 1: ONE deadline for this slot, taken once, here. Every
        # attempt below is spawned with what is LEFT of it — the whole of M9's
        # budget half. The declared vendor envelope (§7.6(b)) turns on rule 4's
        # pre-dispatch admission test and rule 6(b)'s refusal to re-issue a
        # rate-limit dispatch a CLI already exhausted internally; `getattr`
        # because the eleven unmeasured adapters declare `None`, which rule 6(c)
        # reads as "assume one request", never "assume the worst".
        provider = get_provider(provider_name)
        ladder = RetryLadder(
            timeout=effective_timeout,
            retries=get_subagent_retries(anchor=plan_path),
            envelope=getattr(provider, "internal_retries", None),
            now=time.monotonic,
        )
        # A placeholder only until the first attempt names its real output file:
        # rule 4 can refuse this slot before any dispatch, and the result dict
        # still owes its caller a `prompt`. The output-location block is already
        # this provider's real one — it depends on the adapter, not on the path.
        # The working-limits block names the slot's whole budget, rounded the way
        # `attempt_timeout` is below. Not a slice: calling `next_attempt()` here
        # would use up the first attempt, and nothing was sent yet anyway — every
        # dispatched attempt re-renders this with its own `attempt_timeout`.
        prompt = prompt_template.format(
            **full_prompt_context,
            output_json_path="",
            output_location=render_output_location("", model_spec, anchor=plan_path),
            working_limits=render_working_limits(
                max(1, int(round(effective_timeout)))
            ),
        )

        # The misnamed-result baseline is the slot's, not an attempt's: taken
        # once, here, and handed to every attempt, so a file attempt 1 wrote
        # under the wrong name before it was killed is still this slot's when
        # attempt 2 writes nothing (review of fix round 24). `None` without the
        # run's model list, which never looks.
        misnamed_baseline = (
            await asyncio.to_thread(
                misnamed_result_baseline, out_dir, invoke_phase, model_spec
            )
            if run_model_specs is not None else None
        )
        # The requested file's baseline is the slot's too, for the same reason:
        # the file attempt 1 wrote before it was killed is still this slot's
        # answer on attempt 2, and the one already there when the slot started
        # (the previous round's, under `--force --rerun-all`) is never read as
        # this slot's on any attempt (measured 2026-10-09). Taken whatever the
        # model list, since every slot has a requested file.
        requested_baseline = await asyncio.to_thread(
            requested_result_baseline, out_dir, invoke_phase, model_spec
        )

        while (slice_s := ladder.next_attempt()) is not None:
            # Never a fresh copy of `effective_timeout`: `next_attempt()` returns
            # what is left of the one deadline, and rule 3 guarantees it is at
            # least MIN_ATTEMPT_BUDGET_S, so the floor below can never be 0.
            # `round`, not `int`: `invoke_with_file_output` takes whole seconds,
            # and truncating would silently spend up to a second of the slot's
            # budget on every attempt — including the first, whose slice is
            # `effective_timeout` minus the microseconds since the ladder was
            # constructed. The ≤ 0.5 s of overshoot the other way is bounded and
            # sits inside the fan-out's `base_timeout × 2` of slack.
            attempt_timeout = max(1, int(round(slice_s)))
            print(
                f"[{display_name}] Starting review with file-based output "
                f"(attempt {ladder.attempt_index}, timeout: {attempt_timeout}s "
                f"of a {effective_timeout}s slot)..."
            )
            if tracker is not None:
                # Once per ladder attempt, which is what carries a retried slot
                # back out of `retrying` and into `running` with the new attempt
                # number. `timeout_s` stays `effective_timeout` — the slot's
                # whole budget — and is deliberately not `attempt_timeout`,
                # which is what *remains* and shrinks every round: rendered as
                # the denominator it would overstate the budget left.
                tracker.running(
                    model_spec,
                    attempt=ladder.attempt_index,
                    timeout_s=effective_timeout,
                )

            result = await asyncio.to_thread(
                invoke_with_file_output,
                prompt_template=prompt_template,
                model_spec=model_spec,
                prompt_context=full_prompt_context,
                output_dir=out_dir,
                phase=invoke_phase,
                timeout=attempt_timeout,
                log_file=log_file,
                prefer_arrays=True,
                cwd=project_root,
                anchor=plan_path,
                run_model_specs=run_model_specs,
                misnamed_baseline=misnamed_baseline,
                requested_baseline=requested_baseline,
                **sandbox_fallback_kwargs(sandbox),
            )

            details = result.get("details", {})
            slot_usage = accumulate_usage(slot_usage, details)
            # Plan §4.3: every attempt's verdict, in order, for the AND at the
            # end — a retry replaces `details`, so the last one alone would let
            # a clean retry excuse an earlier attempt that wrote.
            slot_audits.append(details.get("readonly_audit"))
            slot_home_checks.append(details.get("home_check"))
            # The jail's own lines for this attempt: its `[JAIL_DENIED]` line
            # (kept for the closing summary) and the in-stream denial count.
            report_jail_outcome(display_name, details, summary_key)
            stderr_text = details.get("stderr", "")
            source = result.get("source", "unknown")
            output_file = result.get("output_file", "")

            # The prompt this attempt really sent, reconstructed for the record:
            # `invoke_with_file_output` renders the same three values from the
            # same spec and the same `attempt_timeout`, so this stays the text
            # the child saw rather than a file-flavoured approximation of it.
            prompt = prompt_template.format(
                **full_prompt_context,
                output_json_path=output_file,
                output_location=render_output_location(
                    output_file, model_spec, anchor=plan_path
                ),
                working_limits=render_working_limits(attempt_timeout),
            )

            # Only for an attempt that answered — same rule as the code-review
            # fan-out: a failed attempt carries `output_file` and no `source`,
            # and the line then promised a file nothing would write.
            if output_file and result.get("success"):
                print(f"[{display_name}] {describe_output_file(output_file, source)}")

            # §7.1.a/§7.2: ONE classification per failed slot, read off the
            # shared classifier, replacing the three raw-substring tests that
            # used to live in this function and disagree with each other. The
            # boundary- and context-awareness L2 introduced is preserved because
            # it is the *same* implementation — a model that wrote "reviewed 429
            # files" still costs one dispatch, not four full-timeout ones plus
            # 35s of backoff.
            # The haystack is the invocation's own ``error`` string and nothing
            # else, exactly as L2 left it. That string is already what
            # ``_format_failure_details`` built from *both* streams, so adding
            # ``stderr_text`` beside it would not add information — it would
            # duplicate the same prose and let the tail of one copy supply the
            # error-context word for a bare token in the other, which is
            # precisely the false positive ``matches_any``'s 48-character window
            # exists to prevent.
            failure_category = (
                None if result.get("success")
                else classify_streams(str(result.get("error", "")), "")
            )
            status = (
                STATUS_OK if result.get("success")
                else _LADDER_STATUS_BY_CATEGORY.get(failure_category, failure_category)
            )
            if not result.get("success") and is_jail_denied(details):
                # F1 item 6: the plugin's jail denied the turn, or could not
                # be set up for it. Non-retryable and never moved to another
                # rung — a status the ladder does not know is "never retried",
                # whatever the text classifies as.
                status = STATUS_JAIL_DENIED

            # One `record` call is the whole retry decision, identical to Lane
            # B's: rung 1 is terminal, rung 3 backs off with jitter at most three
            # times without consuming the transport budget, rungs 2/4/5 spend
            # `driver.subagent_retries`, everything else is never retried — and
            # every one of those decisions is taken against the same deadline the
            # dispatches are charged to. `retry_count < 3` and `retry_count < 1`
            # are gone; they were two counters neither of which saw a clock.
            action = ladder.record(status)
            if not action.retry:
                break
            if action.delay:
                # The ladder is pure, so the test fast-backoff switch cannot live
                # there. Applying it here, at the one place this lane really
                # sleeps, keeps MULTI_LLM_TEST_FAST_BACKOFF=1 an exact 10 ms.
                delay = get_backoff_delay(action.delay)
                print(f"[{display_name}] {status}, retrying in {delay}s...")
                if tracker is not None:
                    # The entry stays `retrying` for the sleep and returns to
                    # `running` at the next attempt's start print above.
                    # `elapsed_s` is not reset by it: the backoff is charged to
                    # the same slot deadline, so a reset would claim budget the
                    # slot does not have.
                    tracker.retrying(
                        model_spec,
                        attempt=ladder.attempt_index,
                        retry_after_s=delay,
                    )
                await asyncio.sleep(delay)

        duration = time.time() - start_time

        if result is None:
            # §7.5 rule 4: the slot was refused before anything was spawned. It
            # is recorded as its own outcome rather than dispatched to be killed
            # part-way through a retry chain the harness cannot see.
            reason = budget_exhausted_reason(
                ladder, target=display_name, timeout=effective_timeout
            )
            print(f"[{display_name}] {reason}")
            # `stdout` stays `""`, and this one is not a hole. `result is None`
            # means `next_attempt()` refused the slot before the first dispatch,
            # so no child ever ran and there is no stream to excerpt. `details`
            # is safe to read — it is initialised to `{}` above the `try` — but
            # it is guaranteed empty, and `details.get("stdout_excerpt", "")`
            # here would be an always-empty key dressed as a live one: a reader
            # would have to re-derive that it can never hold anything, and a
            # later edit to this branch would inherit the pretence.
            return {
                "success": False, "output": None,
                "error": reason,
                "prompt": prompt, "stdout": "", "stderr": "",
                "duration_seconds": duration, "model_spec": model_spec,
                "source": "not-dispatched",
            }

        # D6 override: the detective check, once, after the last attempt and
        # ahead of every branch below — a bypassed slot that changed the tree
        # is failed with the paths whatever its last attempt reported, and the
        # `output` is dropped so `save_model_result` never parses it. Placed
        # after the `result is None` return because nothing ran on that path.
        violation = await _bypass_write_check(slot_audits)
        if violation is None:
            # The plugin's jail: the mode check and the home check, once,
            # after the last attempt, ahead of every branch below — the same
            # fail-closed place the porcelain check's verdict takes.
            violation = await _incidental_check(slot_home_checks, slot_audits)
        if violation is not None:
            return {
                "success": False, "output": None, "error": violation,
                "prompt": prompt, "stdout": details.get("stdout_excerpt", ""),
                **salvage_text_fields(details),
                "stderr": stderr_text,
                "duration_seconds": duration, "model_spec": model_spec,
                "source": source,
                **served_model_fields(details),
                **usage_total_fields(slot_usage),
            }

        # The ladder granted a retry and `next_attempt()` then refused it: what
        # ended this slot is the budget, not the last attempt's error. Lane B
        # appends the same sentence (`subagent_executor.py`'s STOP_DEADLINE leg),
        # because without it the recorded reason names a transport failure that
        # the harness had, and did not spend, retries for.
        budget_note = ""
        if action is not None and action.retry:
            budget_note = (
                f" (no retry: the per-slot wall-clock budget of "
                f"{effective_timeout}s is exhausted — {ladder.stop_reason})"
            )
        elif (
            action is not None and action.note and status != STATUS_RATE_LIMITED
        ):
            # The usual shape since fix round 6: `record()` applies the same
            # admission test (rules 3 and 4) to the grant, so the refusal comes
            # back as the action's own note. A rate limit's branch below quotes
            # `action.reason`, which already carries it.
            budget_note = f" ({action.note})"

        if status == STATUS_RATE_LIMITED:
            # Either the ≤ 3 backoffs are spent, or §7.5 rule 6(b) refused an
            # identical re-dispatch against an adapter whose CLI already ran its
            # own 429 chain. `action.reason` names which, and — for 6(b) — the
            # declared envelope that decided it.
            return {
                "success": False, "output": None,
                "error": f"Rate limited (429) - {action.reason}{budget_note}",
                # Stage U: a 429 chain is not free — the attempts before the
                # last one were served and billed — so the record names what
                # the slot spent getting nowhere.
                # A 429 is usually announced before a byte of answer, but "usually"
                # is not "always": a CLI that streamed most of a review and was then
                # cut off by the vendor mid-response ends the slot here, and the
                # partial array is on stdout. `details` is the last attempt's — the
                # same attempt `stderr_text` and `source` are taken from — so the
                # three fields describe one run rather than three.
                "prompt": prompt, "stdout": details.get("stdout_excerpt", ""),
                **salvage_text_fields(details),
                "stderr": stderr_text,
                "duration_seconds": duration, "model_spec": model_spec,
                "source": source,
                **served_model_fields(details),
                **usage_total_fields(slot_usage),
            }

        # §7.6(a): a context overflow is TERMINAL. Splitting the prompt is open
        # question 13 and nobody has designed it, so the shipping behaviour is to
        # classify it, name it, and fail the slot with the two remedies a human
        # can actually apply — never a re-dispatch, because re-sending an
        # unchanged oversized prompt is the one retry guaranteed to fail
        # identically. The old test here was `'context' in str(error)`, which
        # also fired on `context_mode`, on "in this context", and on any prose
        # quoting the plan's own Context section.
        if status == STATUS_CONTEXT_LENGTH_EXCEEDED:
            return {
                "success": False, "output": None,
                "error": context_length_message(model_spec),
                # Terminal, never re-dispatched (§7.6(a)) — which is exactly why
                # whatever the model managed to emit before the window closed is
                # the only copy anyone will ever get. An overflow hit part-way
                # through a long array is the shape that matters: there is no
                # second attempt to produce it again.
                "prompt": prompt, "stdout": details.get("stdout_excerpt", ""),
                **salvage_text_fields(details),
                "stderr": stderr_text,
                "duration_seconds": duration, "model_spec": model_spec,
                "source": source,
                **served_model_fields(details),
                **usage_total_fields(slot_usage),
            }

        if result.get("success"):
            if result.get("misnamed_from"):
                report_misnamed_result(
                    model_spec, result, get_phase_dir(Path(plan_path), phase_name),
                )
            print(f"[{display_name}] Completed successfully in {duration:.1f}s (source: {source})")
            output_str = _answer_text(result.get("data"))

            return {
                "success": True, "output": output_str,
                "error": None, "prompt": prompt,
                "stdout": output_str, "stderr": stderr_text,
                "duration_seconds": duration, "model_spec": model_spec,
                "source": source,
                # §3.6: the served model rides out with the answer it produced.
                **served_model_fields(details),
                # Stage U: so does what producing it cost.
                **usage_total_fields(slot_usage),
            }
        else:
            error_details = f"{result.get('error', 'Unknown error')}{budget_note}"
            file_error = result.get("file_error", "")
            if file_error:
                print(f"[{display_name}] File error: {file_error}")
            print(f"[{display_name}] Failed: {error_details}")
            return {
                "success": False, "output": None,
                "error": error_details, "prompt": prompt,
                # The return residual item 5 is about. Every ordinary loss lands
                # here: the non-zero exit, the timeout kill, and
                # `invoke_with_file_output`'s "JSON parsing failed from both file
                # and stdout" — all three of which `_attach_stdout_excerpt` has
                # already populated. A `review-plan` or `review-tasks` provider
                # that streams a truncated array and is then killed at the
                # deadline used to lose it here without a word, because this dict
                # hardcoded `""` and `save_model_result` short-circuited on
                # `if not success or not output:` before its salvage gate could
                # run — the gate was unreachable on a hard failure, not merely
                # gated to False. It is reachable now because this line carries
                # the evidence to it.
                "stdout": details.get("stdout_excerpt", ""),
                # The adapter's reduced answer text, when it has a reducer:
                # `failure_output_from_result` gates on it ahead of `stdout`.
                # And whether a deadline ended the run, which the salvage
                # request records so a salvaged `[]` from it is refused.
                **salvage_text_fields(details),
                **salvage_failure_fields(result),
                "stderr": stderr_text,
                "duration_seconds": duration, "model_spec": model_spec,
                "source": source,
                **served_model_fields(details),
                **usage_total_fields(slot_usage),
            }

    except Exception as e:
        duration = time.time() - start_time
        error_msg = f"Exception: {type(e).__name__}: {e}"
        print(f"[{display_name}] {error_msg}")
        try:
            prompt_for_log = prompt
        except NameError:
            prompt_for_log = prompt_template if 'prompt_template' in dir() else "(unavailable)"
        # `stdout` stays `""` for the same reason as the stdout-only lane's own
        # handler above: this is *our* exception. Every child failure the ladder
        # understands has already returned through one of the branches above, so
        # what reaches here is the orchestrator itself breaking — a prompt that
        # would not format, a ladder misuse, an `asyncio` teardown. `details` is
        # in scope (initialised to `{}` before the `try`) and may even hold a
        # completed attempt's excerpt, which is precisely the argument against
        # reading it: `error` names a failure that attempt did not cause, and
        # pairing the two would offer salvage a document with no relationship to
        # the error recorded beside it.
        return {
            "success": False, "output": None,
            "error": error_msg, "prompt": prompt_for_log,
            "stdout": "", "stderr": "",
            "duration_seconds": duration, "model_spec": model_spec,
            "source": "exception"
        }


async def run_models_concurrent(
    model_specs: List[str],
    per_model_coro_factory: Callable[[str, int], Any],
    timeout: Optional[float],
    max_parallel: int,
    skip_predicate: Optional[Callable[[str, int], Optional[Any]]] = None,
    anchor: Optional[Union[str, Path]] = None,
    *,
    tracker: Optional[FanoutProgress] = None,
) -> Dict[str, Any]:
    """Run a per-model async callback across all models with shared concurrency control.

    This encapsulates the concurrency *mechanics* shared by every multi-model
    phase (review and ask), decoupled from JSON/grouping/validation concerns:

    - a global ``asyncio.Semaphore(max_parallel)``
    - per-provider semaphores derived from ``get_provider_max_concurrent`` (a
      provider's semaphore is acquired *before* the global one so capped
      providers do not hog global slots while waiting for their turn)
    - staggered launches (``index * PROVIDER_STAGGER_DELAY``, honoring
      ``MULTI_LLM_TEST_FAST_BACKOFF``)
    - an overall timeout wrapping ``asyncio.gather`` that harvests whatever
      finished before it fired and cancels the stragglers (F2, 2026-09-20: it
      used to harvest nothing, so a deadline threw away the results of the
      models that had already answered)

    The caller supplies ``per_model_coro_factory(model_spec, index)`` returning
    an awaitable; whatever it produces is stored in the returned dict keyed by
    ``model_spec``. Callbacks that raise are logged and omitted from the
    results (mirroring the original gather/return_exceptions behavior).

    Args:
        model_specs: List of model specifications in provider:model format.
        per_model_coro_factory: ``(model_spec, index) -> awaitable``. The
            awaitable's result is what ends up in the results dict.
        timeout: Optional per-model timeout override (seconds); also drives the
            overall-timeout calculation.
        max_parallel: Maximum concurrent model invocations.
        skip_predicate: Optional cheap, synchronous ``(model_spec, index) ->
            Optional[result]`` checked *before* the stagger sleep and any
            semaphore acquisition. If it returns a non-``None`` value, that
            value is stored as the model's result and the model short-circuits
            immediately (no stagger delay, no semaphore serialization). This
            keeps resume of already-completed models fast. Returning ``None``
            means "not skipped" and the model proceeds normally.
        anchor: Optional discovery anchor (the run's plan-file path). This
            function has no plan path of its own, so without it every per-provider
            bound and every provider resolution below falls back to CWD (§9.3.c).
            ``run_review_phase`` and ``ask_orchestrator`` both hold the plan path
            and pass it.
        tracker: The caller's :class:`~utils.progress_tracker.FanoutProgress`.
            Given one, this function owns the *mechanics* of the per-model map,
            because they are the mechanics it already owns: it seeds every
            requested spec **before** the tasks are created (so a poller sees a
            complete map from the first read instead of one that fills in as
            models start), transitions a slot to ``staggering`` at the stagger
            sleep and back to ``queued`` the moment that sleep ends and the
            semaphore wait begins, records the **terminal** transition for every
            slot from the result dict — the skip predicate's return and the
            factory's alike, since both are result dicts carrying
            ``success``/``source``/``error`` — retires a slot that raised, names
            the deadline as the sweep reason when its own ``wait_for`` fires,
            and in its ``finally`` cancels and awaits the ticker, sweeps, and
            only then returns. ``None`` keeps every line here byte-for-byte
            what it was, which is what lets a direct call (a test, another
            caller) stay untouched.

    Returns:
        Dict mapping model spec to whatever the callback returned for it.
    """
    results: Dict[str, Any] = {}
    if not model_specs:
        return results

    semaphore = asyncio.Semaphore(max_parallel)

    # Per-provider semaphores for concurrency limiting
    provider_semaphores: Dict[str, asyncio.Semaphore] = {}
    for spec in model_specs:
        prov, _ = parse_model_spec(spec, anchor=anchor)
        if prov not in provider_semaphores:
            limit = get_provider_max_concurrent(prov, anchor=anchor)
            if limit is not None:
                provider_semaphores[prov] = asyncio.Semaphore(limit)

    async def run_with_semaphore(model_spec: str, index: int) -> Tuple[str, Any]:
        # Display-only, but still anchored: a bare spec must render the same
        # provider the router chose, not a second, different guess (§9.3.c).
        provider_name, model_name = parse_model_spec(model_spec, anchor=anchor)
        display_name = f"{provider_name}:{model_name}"

        # Cheap pre-stagger skip check: short-circuit already-completed models on
        # resume *before* paying the stagger delay or serializing through the
        # semaphores (otherwise a resume of N done models adds ~(N-1) stagger
        # waits + semaphore queueing it never incurred pre-refactor).
        if skip_predicate is not None:
            skipped = skip_predicate(model_spec, index)
            if skipped is not None:
                # A model answered from disk is terminal the moment it is
                # seeded: it has a usable result and no attempt is ever
                # dispatched, so it counts in `models_done` *and* in
                # `models_succeeded` and a resumed run of four models that finds
                # three on disk reads `3/4` at the FIRST poll rather than `0/4`
                # (D4a on the one lane where nothing dispatches at all). The
                # `source` the predicate put on the result — `existing_file`
                # here, `resume` on the ask lane — is what a renderer reads to
                # label the row "skipped"; there is no `skipped` state.
                if tracker is not None:
                    tracker.record_result(model_spec, skipped)
                return (model_spec, skipped)

        # Stagger launches
        if index > 0:
            base_stagger = index * PROVIDER_STAGGER_DELAY
            stagger_delay = get_backoff_delay(base_stagger)
            print(f"[{display_name}] Waiting {stagger_delay:.1f}s before starting (staggered launch)...")
            if tracker is not None:
                tracker.staggering(model_spec, delay_s=stagger_delay)
            await asyncio.sleep(stagger_delay)
            # The stagger is spent, but this slot is not dispatched: the two
            # semaphores below can park it for minutes (five models at
            # `max_parallel: 2` park three of them), and `running` is only
            # reached inside the factory's coroutine. Without this the whole
            # wait rendered `staggering` — a state the slot left at the line
            # above — while index 0, which never staggers, rendered the same
            # wait as `queued`. One word for one wait.
            if tracker is not None:
                tracker.queued(model_spec)

        # Acquire provider semaphore first (if any), then global semaphore.
        prov_sem = provider_semaphores.get(provider_name)
        try:
            if prov_sem:
                async with prov_sem:
                    async with semaphore:
                        result = await per_model_coro_factory(model_spec, index)
            else:
                async with semaphore:
                    result = await per_model_coro_factory(model_spec, index)
        except Exception as exc:
            # A task that raised is printed as `Task exception:` and dropped from
            # `completed` below without ever being keyed into `results`, so this
            # is the only place the *spec* behind that exception is still known.
            # `Exception`, deliberately **not** `BaseException`: a
            # `CancelledError` arriving here is the overall deadline's own
            # `task.cancel()`, and retiring it as an exception would stamp the
            # empty `str(CancelledError())` over the wording the sweep is about
            # to write. Cancellation is the sweep's to name, in one of exactly
            # two phrasings; an exception is this slot's own ending and is
            # re-raised unchanged, because `return_exceptions=True` is what the
            # caller's contract is written against.
            if tracker is not None:
                tracker.failed(
                    model_spec,
                    error=str(exc) or type(exc).__name__,
                    source="exception",
                )
            raise
        # The terminal transition for a slot that returned, derived from the
        # result dict itself: `run_single_model` and `ask_one` both answer with
        # `{"success", "source", "error"}`, so no call site has to re-derive
        # which of `done`/`failed` it means or get the `source` pass-through
        # wrong. This is `fanout_slot_counter`'s tick, with identity attached.
        if tracker is not None:
            tracker.record_result(model_spec, result)
        return (model_spec, result)

    # Seeded before the tasks exist, not as they start: the write that claims
    # the phase dir drops the predecessor's `progress` wholesale, so what this
    # run writes is all any reader ever sees and a model missing from the map is
    # a bug rather than a model carried over. (`claim_run` does that on the
    # detached lane; on the foreground one the launch write does — nothing did
    # until F1, 2026-09-20.)
    if tracker is not None:
        tracker.seed()

    tasks = [
        spawn_fanout_slot(model_specs, run_with_semaphore(spec, idx))
        for idx, spec in enumerate(model_specs)
    ]

    # Calculate total timeout
    if timeout is not None:
        base_timeout = timeout
    else:
        base_timeout = max(
            get_provider_timeout(parse_model_spec(spec, anchor=anchor)[0], anchor=anchor)
            for spec in model_specs
        )

    stagger_overhead = len(model_specs) * PROVIDER_STAGGER_DELAY
    total_timeout = base_timeout * 2 + stagger_overhead

    # Created alongside the `gather`, cancelled-and-awaited in the `finally`.
    # At `progress.interval_s: 0` this is a no-op returning `None`: the lines
    # stop, every event-driven transition is still written.
    if tracker is not None:
        tracker.start_ticker()

    try:
        completed = await asyncio.wait_for(
            asyncio.gather(*tasks, return_exceptions=True),
            timeout=total_timeout
        )

        for item in completed:
            if isinstance(item, Exception):
                print(f"Task exception: {item}")
                continue
            model_spec, result = item
            results[model_spec] = result

    except asyncio.TimeoutError:
        print(f"Total timeout ({total_timeout}s) exceeded for all models")
        # F2, 2026-09-20: **harvest before cancelling.** `asyncio.wait_for`
        # raises instead of assigning `completed`, so this branch used to leave
        # `results` exactly `{}` — including for the slots that had already
        # RETURNED A RESULT before the deadline fired. The tracker, which
        # records each slot's terminal transition inside the wrapper above, then
        # disagreed with the report about the same run: measured on a 2-model
        # fan-out where one slot returned in 10 ms and one straggled, the map
        # read `{fast: done/file, slow: failed/DEADLINE}` and `counts()` `(2, 1,
        # 2)`, while `backfill_deadline_losses` named *both* models in
        # `failed_models` and the restatement wrote `models_succeeded = 0`. So
        # the checkpoint contradicted its own map, and `models_failed` named a
        # model whose `{model}.json` was already on disk for the next
        # `--reaggregate` to pick up. It is also the F11 over-reporting at its
        # source: a finished model is no longer reported failed, because it did
        # not fail.
        #
        # On 3.11 every task is `done()` by the time this runs — `wait_for`
        # awaits `_cancel_and_wait(gather)` before it raises — so the loop below
        # sees each slot's real ending: a result, a cancellation, or its own
        # exception (already retired by the wrapper's `except`, and deliberately
        # not re-keyed into `results`, which is the `return_exceptions=True`
        # contract the caller is written against). `cancelled()` is asked before
        # `exception()`, which raises on a cancelled task.
        for task in tasks:
            if not task.done() or task.cancelled() or task.exception() is not None:
                continue
            model_spec, result = task.result()
            results[model_spec] = result
        # Named before the ticker is torn down, because there are two sweepers —
        # this function's `finally` and the ticker's own — and a reason passed at
        # one call site would let them disagree about the wording for one run.
        # It is `backfill_deadline_losses`' string, so the per-model table and
        # the report's failure list name one cause rather than two.
        if tracker is not None:
            tracker.set_sweep_reason(DEADLINE_ERROR)
        # A no-op on this interpreter (see above: `wait_for` already awaited the
        # gather's own cancellation, so nothing here is still pending). Kept
        # because it is cheap and because the guarantee it encodes — no slot
        # outlives this function — is the sweep's premise, not `wait_for`'s.
        for task in tasks:
            if not task.done():
                task.cancel()
    finally:
        if tracker is not None:
            # Order is fixed and is the whole of lifetime rule 2: cancel AND
            # await the ticker, then sweep, then return. Awaiting is the point,
            # not politeness — the caller's per-model summary follows
            # immediately, and a ticker merely cancelled could emit one more
            # `[PROGRESS]` line into the middle of it; and because the map is
            # written whole on every transition, any write landing after the
            # sweep would resurrect the `queued`/`running` entries the sweep had
            # just retired. After the sweep no entry reads `queued`,
            # `staggering`, `running` or `retrying`, and the map is not left to
            # the slots to close out: a cancelled slot's `finally` runs, but it
            # is the slot's own coroutine and records nothing about the map
            # (F7, 2026-09-20 — the wording here used to say the deadline branch
            # "cancels without awaiting", which has not been true since 3.8:
            # `wait_for` awaits the gather's cancellation before it raises).
            # What is genuinely unreachable from a slot is an ending the slot
            # never sees at all — a `KeyboardInterrupt` unwinding this coroutine
            # between slots, a task the gather drops — so the sweep walks the
            # map rather than the tasks.
            await tracker.stop_ticker()
            tracker.sweep()

    return results


async def run_tasks_concurrent(
    tasks: List[Dict[str, Any]],
    per_task_coro_factory: Callable[[Dict[str, Any], str, int], Any],
    *,
    runner_for_task: Callable[[Dict[str, Any]], str],
    timeout: Optional[float] = None,
    max_parallel: int = 4,
    skip_predicate: Optional[Callable[[Dict[str, Any], str, int], Optional[Any]]] = None,
    provider_limits: Optional[Dict[str, int]] = None,
    anchor: Optional[Union[str, Path]] = None,
) -> Dict[str, Any]:
    """:func:`run_models_concurrent`'s mechanics, keyed by ``task_id`` (D3).

    ``run_models_concurrent`` returns a dict keyed by ``model_spec`` — correct for
    model fan-out, **wrong** for a subagent batch, where every task normally
    shares the one configured runner, so completed tasks would overwrite one
    another. This is the same machinery keyed by each task's stable ``task_id``:

    - the same global ``asyncio.Semaphore(max_parallel)``
    - the same per-provider semaphores from ``get_provider_max_concurrent``,
      acquired *before* the global one, and **shared in shape** with the fan-out
      path so a mixed-tier batch on one provider contends on ONE semaphore
      (the rate limit belongs to the provider, not the model)
    - the same stagger, bucketed by resolved provider
    - the same overall timeout wrapping ``asyncio.gather``

    ``model_spec`` is used *only* to pick the provider semaphore and stagger
    bucket; it is a column on each row, never the key. ``run_models_concurrent``
    keeps its current signature and callers.

    Args:
        tasks: The materialized task objects (not model specs — each task carries
            its own prompt and its runner is a *derived* attribute).
        per_task_coro_factory: ``(task, runner_spec, index) -> awaitable``.
        runner_for_task: Resolves a task's runner spec once, at batch start.
        timeout: Per-task timeout override, also driving the overall timeout.
        max_parallel: The global gate (``driver.max_concurrent_subagents``,
            already reduced to D3i's three-way minimum by the caller).
        skip_predicate: Cheap synchronous ``(task, runner, index) -> result|None``
            checked *before* the stagger sleep and any semaphore acquisition, so a
            resume of already-complete tasks stays fast.
        provider_limits: Optional per-provider in-flight overrides (D3i
            backpressure narrows a throttled provider's slots for the rest of the
            batch); defaults to ``get_provider_max_concurrent``.
        anchor: Optional discovery anchor (the run's plan-file path), the Lane B
            twin of ``run_models_concurrent``'s (§9.3.c). ``subagent_executor``
            already holds the phase's plan path and passes it.

    Returns:
        ``{task_id: whatever the callback returned}``.
    """
    results: Dict[str, Any] = {}
    if not tasks:
        return results

    runners = {
        str(task.get("task_id", index)): runner_for_task(task)
        for index, task in enumerate(tasks)
    }

    semaphore = asyncio.Semaphore(max_parallel)

    provider_semaphores: Dict[str, asyncio.Semaphore] = {}
    for spec in set(runners.values()):
        prov, _ = parse_model_spec(spec, anchor=anchor)
        if prov in provider_semaphores:
            continue
        limit = (provider_limits or {}).get(
            prov, get_provider_max_concurrent(prov, anchor=anchor)
        )
        if limit is not None:
            provider_semaphores[prov] = asyncio.Semaphore(limit)

    async def run_with_semaphore(task: Dict[str, Any], index: int) -> Tuple[str, Any]:
        task_id = str(task.get("task_id", index))
        runner = runners[task_id]
        # Anchored for the same reason the fan-out's display resolution is: the
        # semaphore this picks must be the one the batch was sized for (§9.3.c).
        provider_name, _ = parse_model_spec(runner, anchor=anchor)

        if skip_predicate is not None:
            skipped = skip_predicate(task, runner, index)
            if skipped is not None:
                return (task_id, skipped)

        if index > 0:
            stagger_delay = get_backoff_delay(index * PROVIDER_STAGGER_DELAY)
            await asyncio.sleep(stagger_delay)

        prov_sem = provider_semaphores.get(provider_name)
        if prov_sem:
            async with prov_sem:
                async with semaphore:
                    return (task_id, await per_task_coro_factory(task, runner, index))
        else:
            async with semaphore:
                return (task_id, await per_task_coro_factory(task, runner, index))

    coros = [
        asyncio.create_task(run_with_semaphore(task, idx))
        for idx, task in enumerate(tasks)
    ]

    if timeout is not None:
        base_timeout = timeout
    else:
        base_timeout = max(
            get_provider_timeout(parse_model_spec(spec, anchor=anchor)[0], anchor=anchor)
            for spec in runners.values()
        )
    total_timeout = base_timeout * 2 + len(tasks) * PROVIDER_STAGGER_DELAY

    try:
        completed = await asyncio.wait_for(
            asyncio.gather(*coros, return_exceptions=True), timeout=total_timeout
        )
        for item in completed:
            if isinstance(item, Exception):
                print(f"Subagent task exception: {item}")
                continue
            task_id, result = item
            results[task_id] = result
    except asyncio.TimeoutError:
        print(f"Total subagent batch timeout ({total_timeout}s) exceeded")
        for coro in coros:
            if not coro.done():
                coro.cancel()

    return results


async def run_all_models(
    model_specs: List[str],
    plan_path: str,
    prompt_template: str,
    prompt_context_factory: Callable[[str], Dict[str, Any]],
    phase_name: str,
    invoke_phase: str,
    timeout: Optional[float],
    max_parallel: int,
    out_dir: Optional[str] = None,
    prefix: Optional[str] = None,
    skip_existing: bool = True,
    prior_usage: Optional[Dict[str, Dict[str, Any]]] = None,
    *,
    tracker: Optional[FanoutProgress] = None,
) -> Dict[str, Dict[str, Any]]:
    """Run all models with concurrency limit and staggered starts.

    The concurrency mechanics (semaphores, staggered starts, overall timeout)
    are delegated to :func:`run_models_concurrent`; this function supplies the
    JSON/grouping/validation-specific per-model behavior (resume skip of
    existing ``{model}.json`` files + ``run_single_model`` invocation) via the
    callback it hands to the helper.

    Args:
        model_specs: List of model specifications in provider:model format
        plan_path: Absolute path to the plan file
        prompt_template: The prompt template string
        prompt_context_factory: Callable that takes model_spec and returns prompt_context dict
            (allows per-model context variations if needed; typically returns same dict)
        phase_name: Phase directory name (e.g., 'review-plan', 'review-tasks')
        invoke_phase: Phase name for invoke_with_file_output (e.g., 'plan_review', 'task_review')
        timeout: Optional timeout override per model in seconds
        max_parallel: Maximum concurrent model invocations
        out_dir: Optional output directory for log files
        prefix: Optional prefix for log file names
        skip_existing: If True, skip models that already have result files
        prior_usage: What an earlier attempt of this phase recorded (read off
            the checkpoint before this run replaced it).  A model answered from
            its existing ``{model}.json`` invokes no adapter and so reports no
            usage of its own, so its entry is put back on the skip result here
            — the one place that knows a result was reused.  A model that
            really re-runs is never seeded from it.
        tracker: The caller's :class:`~utils.progress_tracker.FanoutProgress`,
            threaded into both halves of the fan-out —
            :func:`run_models_concurrent` for the seed, the stagger, every
            terminal transition and the teardown sweep, and
            :func:`run_single_model` for the start/retry transitions only it can
            see. It replaces D4a's `fanout_slot_counter` outright rather than
            running beside it: a map-derived `models_done` and a counter are two
            writers for one key, and the two would tick at different moments.

    Returns:
        Dict mapping model spec to result dict
    """
    def skip_existing_result(model_spec: str, index: int) -> Optional[Dict[str, Any]]:
        # Cheap, synchronous resume check (runs before stagger/semaphores):
        # skip models that already have valid results (resume after partial
        # failure). Returns None when the model must (re)run.
        if not (skip_existing and out_dir):
            return None
        provider_name, model_name = parse_model_spec(model_spec, anchor=plan_path)
        display_name = f"{provider_name}:{model_name}"
        sanitized = sanitize_model_name(model_spec)
        existing_path = os.path.join(
            str(get_phase_dir(Path(plan_path), phase_name)),
            f"{sanitized}.json"
        )
        if os.path.exists(existing_path) and os.path.getsize(existing_path) > 0:
            try:
                with open(existing_path, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                if isinstance(existing_data, list):
                    print(f"[SKIP] {display_name} - already has results ({len(existing_data)} items)")
                    # A slot answered from disk is a slot finished; a resumed
                    # run must not read `models 0/4` while it skips four. The
                    # transition itself is `run_models_concurrent`'s, taken from
                    # the `source: existing_file` result below — one writer for
                    # the key, at one moment.
                    return {
                        "success": True,
                        "output": json.dumps(existing_data),
                        "error": None,
                        "prompt": "(skipped - existing results)",
                        "stdout": "", "stderr": "",
                        "duration_seconds": 0.0,
                        "model_spec": model_spec,
                        "source": "existing_file",
                        # Stage U: the result is reused, so what it cost is
                        # reused with it — through the same `usage_fields`
                        # shape a real invocation's record carries, so
                        # `collect_usage` cannot tell the two apart and the
                        # `models_complete` write keeps a number an earlier
                        # attempt really paid for. Absent when that attempt
                        # reported none, which is what leaves a duration-only
                        # fan-out's checkpoint exactly what it was.
                        **usage_fields(
                            {"usage": (prior_usage or {}).get(model_spec)}
                        ),
                    }
            except (json.JSONDecodeError, IOError):
                print(f"[{display_name}] Existing result file corrupt, re-running...")
        return None

    async def per_model(model_spec: str, index: int) -> Dict[str, Any]:
        # The review-plan / review-tasks half of the same rule
        # `code_review_orchestrator.run_single_review` states at length: a
        # fresh attempt for this model retires the salvage pair an earlier
        # attempt left in this phase dir, because `save_model_result` below
        # decides whether *this* attempt writes one and nothing else decides
        # whether the last one is still lying there. Reached only when
        # `skip_existing_result` declined to answer from the existing
        # `<model>.json`, which is what keeps a resumed run's *skipped* models —
        # models that began no attempt — holding on to theirs.
        retire_salvage_artifacts(
            str(get_phase_dir(Path(plan_path), phase_name)),
            sanitize_model_name(model_spec),
            reason=RETIRE_SUPERSEDED,
            quiet=True,
        )
        prompt_context = prompt_context_factory(model_spec)
        # No `finally` tick here any more: the slot's terminal transition is
        # taken by `run_models_concurrent` from what this returns, and a slot
        # that raised or was cancelled is retired by the sweep in that
        # function's own `finally`, which runs whichever way the fan-out ends —
        # including the endings this coroutine never sees, such as a
        # `KeyboardInterrupt` between slots. (It used to say the deadline
        # branch "cancels its stragglers without awaiting them"; `wait_for`
        # awaits the gather's cancellation before it raises, so a cancelled slot
        # does reach its own `finally` — F7, 2026-09-20.)
        return await run_single_model(
            model_spec, plan_path, prompt_template, prompt_context,
            phase_name, invoke_phase, timeout,
            out_dir=out_dir, prefix=prefix, tracker=tracker,
            run_model_specs=list(model_specs),
        )

    return await run_models_concurrent(
        model_specs, per_model, timeout, max_parallel,
        skip_predicate=skip_existing_result,
        anchor=plan_path,
        tracker=tracker,
    )


# ---------------------------------------------------------------------------
# Result saving
# ---------------------------------------------------------------------------

def salvage_source(details: Dict[str, Any]) -> str:
    """The text the salvage gate judges for one losing run — one rule, both lanes.

    ``code_review_orchestrator.run_single_review``'s salvage site A calls it on
    the invocation's ``details``, and :func:`failure_output_from_result` calls it
    on the review-plan / review-tasks result dict, so the two gates cannot come
    to disagree about which channel answers.

    * **``details['salvage_text']`` present** (the adapter's
      ``LLMProvider.salvage_text`` reduced its stream): that text, **even when
      it is ``""``**. It never falls back to ``stdout_excerpt`` or stderr. A
      stream adapter writes its answer into its stdout stream, so the raw
      excerpt is event data whose ``content`` arrays pass
      ``has_salvageable_json`` as findings (a reviewer killed mid-tool-call was
      "salvaged" from its own ``thinking``/``toolCall`` parts), and its stderr
      holds only diagnostics — which the gate also accepts when one is
      array-shaped, e.g. ``{"error":"authentication failed","attempts":[]}``.
      stderr keeps its other uses (the failure message, the log); it just
      never reaches the gate once a reducer has spoken.
    * **Absent** (no reducer applies — the hook returned ``None``): today's
      order, ``stdout_excerpt`` first and stderr second (see
      :func:`failure_output_from_result` for why stdout wins and the two are
      never concatenated).

    Whatever this returns is also the request's ``raw_output``: the text a
    salvage subagent is asked to repair is the text the gate decided on.

    (plan: review-run-scope-salvage-and-failure-visibility §4, D4.3.)
    """
    if SALVAGE_TEXT_KEY in details:
        text = details.get(SALVAGE_TEXT_KEY)
        return text if isinstance(text, str) else ""
    return details.get("stdout_excerpt") or details.get("stderr") or ""


def salvage_text_fields(details: Dict[str, Any]) -> Dict[str, Any]:
    """``{"salvage_text": …}`` when ``details`` carries it, else ``{}``.

    Spread into every losing result dict :func:`run_single_model` builds from a
    child's ``details``, so :func:`failure_output_from_result` can apply
    :func:`salvage_source`'s rule. Copied **only when present**: an absent key
    ("no reducer applies") and ``""`` ("the reducer found nothing") are
    different verdicts, and a dict that always carried the key would turn the
    first into the second.
    """
    if SALVAGE_TEXT_KEY in details:
        return {SALVAGE_TEXT_KEY: details[SALVAGE_TEXT_KEY]}
    return {}


def salvage_failure_kind(result: Dict[str, Any]) -> Optional[str]:
    """``"timeout"`` when an invocation result was lost to a deadline, else ``None``.

    Read off the invocation's ``error_code``: ``ERROR_TIMEOUT`` is set by the
    harness's own kill and by an adapter whose stream says the run was cut by
    its deadline (pi/omp's ``toolUse``/``aborted`` final message). A salvage
    request records it as ``"failure": "timeout"``, and the executor then
    refuses a salvaged ``[]`` from that run (D4.5, decision 11.10): a reviewer
    killed mid-review never reported an empty review.
    """
    if result.get("error_code") == ERROR_TIMEOUT:
        return SALVAGE_FAILURE_TIMEOUT
    return None


def salvage_failure_fields(result: Dict[str, Any]) -> Dict[str, Any]:
    """``{"failure": "timeout"}`` for a timed-out invocation result, else ``{}``.

    Spread into :func:`run_single_model`'s losing result dicts beside
    :func:`salvage_text_fields`, so ``save_model_result`` can stamp the kind on
    the salvage request it writes.
    """
    kind = salvage_failure_kind(result)
    return {SALVAGE_FAILURE_KEY: kind} if kind else {}


def failure_output_from_result(result: Dict[str, Any]) -> str:
    """The text a losing run left behind, for the salvage gate.

    :func:`salvage_source`'s rule applied to a review-plan / review-tasks result
    dict: the adapter's reduced ``salvage_text`` when the dict carries it (even
    ``""``), otherwise stdout first and stderr second.

    One rule, one place. ``code_review_orchestrator.run_single_review``'s
    salvage site A applies the same :func:`salvage_source` to the
    ``review-code`` fan-out's ``details``, and this is that rule for the
    ``review-plan`` / ``review-tasks`` fan-out, whose result dicts have already
    flattened those ``details`` keys into ``stdout``, ``stderr`` and
    ``salvage_text`` by the time :func:`run_single_model` returns. Two lanes, two
    plumbing shapes, one sentence about which channel answers first; spelling it
    twice in two paraphrases is how the two lanes would come to disagree without
    anybody editing either.

    **Why stdout wins, rather than both being used.** The branch this feeds is
    not only "the provider never spoke": it also covers the provider that wrote a
    truncated or fenced array and *then* died — a kill at the deadline, a crash
    on teardown — and that array is on **stdout**, never on stderr. A gate shown
    stderr alone therefore reports "nothing to salvage" about a run that produced
    a recoverable review, and drops it silently.

    **Precedence, not concatenation.** The winner is handed to a salvage subagent
    as *the* damaged answer to repair (``utils.subagent_prompts.build_salvage_prompt``),
    so gluing a launch banner, a progress spinner or an auth notice onto a
    truncated array would give that subagent two documents and no way to tell
    which one it was asked about — with ``build_salvage_prompt``'s
    "found nothing" sentinel waiting when it guesses wrong. stdout is the channel
    that can hold an answer, so stdout is asked first and stderr is not appended.
    stderr stays reachable as a fall-through, which is what still routes a
    provider that died before printing a byte.

    Note that this reads the result dict rather than ``details`` because the
    lane's plumbing already moved the excerpt onto ``result["stdout"]``; see
    :func:`run_single_model`'s ``Returns:`` for why that key is not ``output``.

    Args:
        result: One model's entry from :func:`run_all_models`.

    Returns:
        ``result["salvage_text"]`` when present (``""`` included); otherwise the
        first non-empty of ``stdout`` then ``stderr``, or ``""``. On a run
        that *succeeded* ``stdout`` is the answer itself, which is harmless:
        :func:`save_model_result` only consults this value on the branch where
        there is no usable ``output`` to parse.
    """
    source: Dict[str, Any] = {
        "stdout_excerpt": result.get("stdout"),
        "stderr": result.get("stderr"),
    }
    source.update(salvage_text_fields(result))
    return salvage_source(source)


def _write_salvage_request(
    *,
    model: str,
    sanitized_model: str,
    raw_output: str,
    phase_dir: str,
    phase_name: str,
    failure: Optional[str] = None,
) -> str:
    """Write one model's salvage request **and** its task file, and announce both.

    Factored out because :func:`save_model_result` now asks for salvage from two
    different branches — the parse failure of a run that completed, and the
    leftover stdout of a run that did not — and this is ~35 lines of record
    shape, marker protocol and best-effort pairing. Two copies in one function
    is the forward-maintenance hazard this module argues against everywhere else
    (see :func:`retired_salvage_name` on the three prefix-anchored globs, and
    ``utils/llm_client._attach_stdout_excerpt`` on "a rule spelled three times is
    a rule that drifts twice"): a field added to the request, or a change to the
    ``expected_schema`` the salvage prompt is built from, would land on one
    branch and not the other, and the divergence would only show up in an
    artifact a human reads after the run that needed it is over.

    The request is written *before* the task file on purpose: the task binds to
    the request by ``inputs.salvage_request_sha256``, so the request must exist
    and be final first. Materializing the task is best-effort — a request that
    cannot be paired with a task is still recoverable by hand, and must not mask
    the failure that produced it — which is why its exception is caught, named
    and dropped rather than raised.

    Args:
        model: The model spec, as the operator typed it.
        sanitized_model: ``sanitize_model_name(model)`` — the stem every artifact
            in the pair is named from, and the stem of the result file the
            salvage would write to.
        raw_output: The damaged answer. Whatever the gate judged, so that the
            text a subagent is asked to repair is the text the decision was made
            on; gating on one string and persisting another would let a request
            be written for evidence nobody ever saw.
        phase_dir: Where the pair lands.
        phase_name: Salvage metadata phase (``review_plan`` / ``review_tasks``).
        failure: How the run was lost, when that decides what a salvage may
            return: ``"timeout"`` (:func:`salvage_failure_kind`) is recorded as
            the request's ``"failure"`` key, and a salvaged ``[]`` from such a
            run is then refused rather than written as a clean review. ``None``
            (a run that finished, or failed another way) records nothing.

    Returns:
        The path of the salvage request.
    """
    salvage_request = {
        "model": model,
        "phase": phase_name,
        "raw_output": raw_output,
        "expected_type": "array",
        "expected_schema": {
            "fields": list(REQUIRED_FIELDS),
            "importance_values": list(VALID_IMPORTANCE),
            "type_values": list(VALID_TYPES),
        },
        "output_path": os.path.join(phase_dir, f"{sanitized_model}.json"),
        "timestamp": datetime.now().isoformat()
    }
    if failure == SALVAGE_FAILURE_TIMEOUT:
        salvage_request[SALVAGE_FAILURE_KEY] = SALVAGE_FAILURE_TIMEOUT
    salvage_path = os.path.join(phase_dir, f"salvage_{sanitized_model}.json")
    with open(salvage_path, 'w', encoding='utf-8') as f:
        json.dump(salvage_request, f, indent=2)

    print(f"[SALVAGE_NEEDED] {salvage_path}")
    # The salvage prompt is materialized in Python (D2/D2i) instead of being
    # assembled from references/salvage-handling.md, so any invoker can run it.
    try:
        salvage_task_path = write_salvage_task_file(
            salvage_request=salvage_request,
            salvage_request_path=salvage_path,
            phase_dir=phase_dir,
        )
        print(f"[SALVAGE_TASK] {salvage_task_path}")
    except Exception as task_error:  # noqa: BLE001 - diagnostics only
        print(f"[{model}] Warning: could not materialize salvage task: {task_error}")

    return salvage_path


def save_model_result(
    prefix: str,
    model: str,
    success: bool,
    output: Optional[str],
    error: Optional[str],
    out_dir: str,
    phase_dir: str,
    phase_name: str,
    *,
    failure_output: Optional[str] = None,
    failure: Optional[str] = None,
) -> bool:
    """Save model result to appropriate file.

    Two kinds of text can arrive here and they are not interchangeable.
    ``output`` is the answer of a run that **completed**: it is parsed,
    validated, and — if it survives that — written to ``{model}.json``, which is
    what makes the model a participant in the review. ``failure_output`` is the
    text a run that **did not** complete left behind, and salvage is the only
    thing allowed to read it. The branch below never parses it and never writes
    a result file from it; it decides one question, "is there an answer in here
    worth repairing", and answers it by writing a salvage request or not.

    That separation is the whole of this parameter's reason to exist. Feeding the
    leftover stdout into ``output`` instead would be one line shorter and would
    reintroduce the defect it closes: a hard failure whose stdout happened to
    hold a well-formed suggestions array would fall through to the parse block
    and be recorded as that model's completed review, so a crashed run would
    count toward ``SuggestionGroup._recalculate_priority``'s ``len(self.models)``
    exactly like a run that answered. See :func:`run_single_model`'s ``Returns:``
    for the plumbing half of the same argument.

    Args:
        prefix: Output file prefix
        model: Model name
        success: Whether the model run succeeded
        output: Model output (JSON string)
        error: Error message if failed
        out_dir: Output directory (base folder)
        phase_dir: Phase-specific directory for output files
        phase_name: Phase name for salvage metadata (e.g., 'review_plan', 'review_tasks')
        failure_output: Keyword-only, and defaulting to ``None`` so that every
            existing caller — ``review_plan_orchestrator``'s backward-compatible
            wrapper, and the fourteen-odd test call sites — keeps working
            untouched and keeps today's behaviour exactly. Production callers
            build it with :func:`failure_output_from_result`, which owns the
            stdout-then-stderr precedence.
        failure: Keyword-only, the losing run's kind (the result dict's
            ``"failure"`` key, set by :func:`salvage_failure_fields`). Passed to
            the hard-failure branch's salvage request only, so a salvaged ``[]``
            from a timed-out run is refused; a completed run's parse failure
            never carries one.

    Returns:
        True if result was saved successfully, False otherwise. A salvage request
        written from ``failure_output`` does **not** make this ``True``: the run
        failed, the model stays failed, and D6 row 3 aggregates the slots that
        answered.
    """
    sanitized_model = sanitize_model_name(model)

    if not success or not output:
        # The hard-failure branch, and until residual item 5 was paid it was a
        # dead end: it short-circuited on the condition above, wrote the log and
        # returned, which made the salvage block in the `except` below not merely
        # gated to False on a crashed run but **unreachable**. A `review-plan` or
        # `review-tasks` provider that streamed a truncated array and was then
        # killed at the deadline lost that answer without a word — the same
        # defect `code_review_orchestrator`'s salvage site A carries one lane
        # over, by a different mechanism, which is why site A's fix does not
        # reach here and this one had to be made separately.
        #
        # What changes is only *what the gate is shown*, never what gets parsed.
        # `has_salvageable_json` runs over `failure_output` — the leftover
        # stream, not an answer — and on a hit this writes the same request/task
        # pair the parse branch writes, from the same helper, so the two cannot
        # drift. Then it returns `False` **unconditionally**: this branch must
        # never reach `json.loads`, and must never write `{model}.json`. A hard
        # failure whose stdout happened to parse would otherwise be recorded as
        # that model's completed review, which is a worse defect than the silent
        # loss — the phantom participant of `retire_salvage_artifacts`'s
        # docstring, inverted.
        #
        # Unsalvageable is not fatal, exactly as in the parse branch: the model
        # was already failed on arrival here, so the error log is written on both
        # paths and only its wording moves.
        salvageable = has_salvageable_json(failure_output or "")
        if salvageable:
            _write_salvage_request(
                model=model,
                sanitized_model=sanitized_model,
                raw_output=failure_output or "",
                phase_dir=phase_dir,
                phase_name=phase_name,
                failure=failure,
            )

        error_path = os.path.join(phase_dir, f"error_{sanitized_model}.log")
        with open(error_path, 'w', encoding='utf-8') as f:
            f.write(f"Model: {model}\n")
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            f.write(f"Error: {error or 'Unknown error'}\n")
            if salvageable:
                # Named in the log as well as on stdout: the marker scrolls past
                # in a fan-out of eight models, and this file is what an operator
                # reads afterwards to tell "the provider died with an answer
                # half-written" from "the provider died".
                f.write(
                    "Salvage: requested \u2014 the run failed, but the output it "
                    "left behind still holds an answer to repair.\n"
                )
            if output:
                f.write(f"\nRaw output:\n{output}\n")
            elif failure_output:
                # Under its own heading, because it is not the model's answer:
                # it is whichever stream `failure_output_from_result` chose, and
                # nothing downstream of here treats it as a result.
                f.write(f"\nRaw output (failed run):\n{failure_output}\n")
        print(f"[{model}] Error logged to: {error_path}")
        return False

    try:
        json_text = extract_json_array(output)
        if json_text is None:
            raise json.JSONDecodeError("No JSON array found", output, 0)

        suggestions = json.loads(json_text)

        if not isinstance(suggestions, list):
            raise ValueError("Expected JSON array")

        validated_suggestions = []
        for i, suggestion in enumerate(suggestions):
            is_valid, validation_error = validate_suggestion(suggestion)
            if not is_valid:
                print(f"[{model}] Warning: Suggestion {i} invalid - {validation_error}")
                continue
            suggestion["importance"] = suggestion["importance"].upper()
            suggestion["type"] = suggestion["type"].lower()
            validated_suggestions.append(suggestion)

        if len(suggestions) == 0:
            print(f"[{model}] Warning: Empty suggestions array (no issues found)")
        elif len(validated_suggestions) == 0:
            print(f"[{model}] Warning: All suggestions were invalid")

        result_path = os.path.join(phase_dir, f"{sanitized_model}.json")
        with open(result_path, 'w', encoding='utf-8') as f:
            json.dump(validated_suggestions, f, indent=2)

        print(f"[{model}] Saved {len(validated_suggestions)} suggestions to: {result_path}")
        return True

    except (json.JSONDecodeError, ValueError) as e:
        # The fan-out's sibling of code_review_orchestrator's two salvage sites,
        # and it holds the same rule: salvage only when the reply still holds an
        # answer to repair. A model that answered in prose — §40's write
        # refusals, a provider printing its auth failure on the channel it
        # exited 0 on — reaches this `except` with not one character of JSON,
        # and the salvage prompt's "if nothing recoverable is present, print an
        # empty array" would then write `[]` over `output_path`: a model that
        # produced nothing, recorded as one that reviewed the document and found
        # nothing. Unsalvageable is not fatal here either — the model stays
        # failed and D6 row 3 aggregates what the other slots returned — so the
        # error log below is written on both paths and only its wording moves.
        salvageable = has_salvageable_json(output)
        if salvageable:
            # The same writer the hard-failure branch above uses, and the reason
            # it is a function: the two branches ask for salvage about different
            # text for different reasons, but the request they produce is one
            # record shape and one marker protocol, and a second copy of it here
            # would drift the first time either is extended.
            _write_salvage_request(
                model=model,
                sanitized_model=sanitized_model,
                raw_output=output,
                phase_dir=phase_dir,
                phase_name=phase_name,
            )

        error_path = os.path.join(phase_dir, f"error_{sanitized_model}.log")
        with open(error_path, 'w', encoding='utf-8') as f:
            f.write(f"Model: {model}\n")
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            f.write(f"{'Parse error' if salvageable else 'No JSON in response'}: {e}\n")
            f.write(f"\nRaw output:\n{output}\n")
        if salvageable:
            print(f"[{model}] JSON parse error, raw output saved to: {error_path}")
        else:
            print(
                f"[{model}] Response carries no JSON — nothing to salvage, "
                f"raw output saved to: {error_path}"
            )
        return False


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------

def aggregate_results(
    prefix: str,
    out_dir: str,
    phase_dir: str,
    phase_name: str,
    models: List[str],
    failed_models: Dict[str, str],
    validated_groups: Optional[List[Dict]] = None,
    plan_path: Optional[str] = None,
    base_ref: Optional[str] = None,
    tasks_path: Optional[Path] = None,
    template_style: str = 'pr',
    diff_data: Optional[Dict] = None,
    served_models: Optional[Dict[str, Dict[str, Any]]] = None,
    usage: Optional[Dict[str, Dict[str, Any]]] = None,
    requested_models: Optional[int] = None,
) -> str:
    """Aggregate all model results into a consolidated markdown report.

    Args:
        prefix: Output file prefix
        out_dir: Output directory (base folder)
        phase_dir: Phase-specific directory for output files
        phase_name: Phase type for HTML report (e.g., 'review-plan', 'review-tasks')
        models: List of all models used
        failed_models: Dict of model -> error for failed models. Named on a
            ``**Models failed:**`` line directly under ``**Models:**``
            (:func:`~utils.html_report_generator.failed_models_line`, with the
            salvage clause from :func:`salvage_requested_models`), in the HTML
            report's warning notice and failure row, and in the ``## Models
            Failed`` section at the bottom.
        requested_models: The size of the requested set, for "N of M
            requested": the fan-out's ``len(model_specs)``, a reaggregate's
            :func:`recorded_requested_models`. ``None`` states the count alone
            and leaves ``requestedModels`` out of the HTML report data.
        validated_groups: Optional list of validated suggestion groups
        plan_path: Optional path to the plan file for HTML report
        base_ref: Optional git ref for PR-style diff context (forwarded to
            ``generate_html_report()``).
        tasks_path: Optional path to tasks JSON for task-view metadata
            (forwarded to ``generate_html_report()``).
        template_style: Template to use — ``'pr'`` or ``'flat'``
            (forwarded to ``generate_html_report()``).  Defaults to ``'pr'``.
        diff_data: Optional pre-computed diff hunk data (forwarded to
            ``generate_html_report()``).
        served_models: Optional §3.6 attribution
            (``{model_spec: {"served_model", "fallback"}}``, from
            :func:`collect_served_models`).  A model that was served by a
            configured fallback is named as such on the ``**Models:**`` line and
            in the HTML report; with nothing configured this is empty and the
            report is byte-for-byte what it was.
        usage: Optional per-model usage (``{model_spec: usage}``, from
            :func:`collect_usage`).  Each reporting model's clause joins its
            entry on the ``**Models:**`` line and its badge in the HTML report;
            a model that reported nothing renders nothing, so a run of
            duration-only adapters is byte-for-byte what it was.

    Returns:
        Path to the generated report
    """
    groups_to_display = validated_groups
    if not groups_to_display:
        grouped_path = os.path.join(phase_dir, "grouped.json")
        if os.path.exists(grouped_path):
            try:
                with open(grouped_path, 'r', encoding='utf-8') as f:
                    raw_data = json.load(f)
                groups_to_display = load_groups_payload(raw_data)
            except (json.JSONDecodeError, IOError, ValueError) as e:
                print(f"Warning: Could not read {grouped_path}: {e}")
                groups_to_display = []

    # Count suggestions by importance
    high_count = medium_count = low_count = total_suggestions = 0
    if groups_to_display:
        for group in groups_to_display:
            for s in group.get("suggestions", []):
                total_suggestions += 1
                importance = s.get("importance", "LOW").upper()
                if importance == "HIGH":
                    high_count += 1
                elif importance == "MEDIUM":
                    medium_count += 1
                else:
                    low_count += 1

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    successful_models = [m for m in models if m not in failed_models]

    phase_labels = {
        "review-plan": "Plan Review",
        "review-tasks": "Task Review",
        "code-review": "Code Review",
    }
    phase_label = phase_labels.get(phase_name, "Plan Review")

    report_lines = [
        f"# {phase_label} Report: {prefix}",
        "",
        f"**Original plan:** {prefix}.md",
        f"**Generated:** {timestamp}",
        # `model_label`, not `served_model_label`: this line names each model
        # once, which is the one place a cost belongs. (The per-issue
        # `**Model:**` field in the code-review report repeats per finding and
        # keeps the bare attribution label.)
        f"**Models:** {', '.join(model_label(m, served_models, usage) for m in successful_models)}",
    ]
    # The models that produced nothing, directly under the ones that did — the
    # bottom `## Models Failed` section alone left a lost reviewer below the
    # fold, and a reaggregate never wrote it. The same salvage answer goes to
    # the HTML notice below, so the two surfaces render one string.
    salvage_requested = salvage_requested_models(phase_dir, list(failed_models or {}))
    # A jail-denied slot's `models_served` entry makes the line say "denied by
    # the plugin's jail: <path>" (plan codex-sandbox-unavailable F1 item 6).
    failure_line = failed_models_line(
        failed_models, requested_models, salvage_requested,
        served_models=served_models,
    )
    if failure_line:
        report_lines.append(failure_line)
    # A result file read from under the wrong name, or set aside as no
    # recorded model's (`utils/result_files.py`); absent when neither happened.
    result_files_line = _result_files.result_notes_line(phase_dir)
    if result_files_line:
        report_lines.append(result_files_line)
    report_lines += [
        # `G<n>` below counts from 1; `group_index` in grouped.json,
        # validation.json and validation_tasks.json counts from 0 (G12 is
        # group_index 11). A host reading both reported "group 11" beside a
        # report that says G12 (2026-10-01, Claude Code review-plan); the bracketed
        # hash is the number-free key.
        f"**Groups:** {len(groups_to_display) if groups_to_display else 0} "
        "(`G<n>` counts from 1; `group_index` in the JSON files counts from 0)",
        f"**Suggestions:** {high_count} HIGH, {medium_count} MEDIUM, {low_count} LOW ({total_suggestions} total)",
    ]

    # §6 T6.1: the same four counts `record_validation_counts` puts on the
    # result line below, from the same helper, so a `validation_failed` group
    # shows in the report summary too and the header and payload agree.
    validation_line = validation_counts_line(validation_counts(groups_to_display))
    if validation_line:
        report_lines.append(validation_line)
    # Plan §2.4: read the published `validation_context`, never recomputed;
    # absent (every source inline) adds nothing, so the report is unchanged.
    report_lines.extend(
        _validation_context.report_header_lines(
            _status_file.read_status(phase_dir).get("validation_context")
        )
    )

    # NOTE: All phases (including review-tasks) use interactive reports with
    # skip/approve checkboxes.  The original code suppressed these controls for
    # review-tasks (readOnly=True), but the task-review workflow now supports
    # skip/override actions, so interactivity is intentionally enabled for every
    # phase.  See also html_report_generator.py where readOnly is set to False.
    report_lines.append("")
    report_lines.append("> **Note:** An interactive HTML report is also available at `report.html`.")
    report_lines.append("> If you export selections from the HTML report (`user_selections.json`),")
    report_lines.append("> those selections will take precedence over checkboxes in this file.")
    report_lines.append("")

    if groups_to_display:
        groups_to_display = sort_raw_groups_by_priority(groups_to_display)
        for group_idx, group in enumerate(groups_to_display, 1):
            report_lines.extend(format_group(group, group_idx))
    else:
        report_lines.append("_No suggestions found._")
        report_lines.append("")

    if failed_models:
        report_lines.append("## Models Failed")
        report_lines.append("")
        for model, reason in failed_models.items():
            report_lines.append(f"- **{model}**: {reason}")
        report_lines.append("")

    report_path = os.path.join(phase_dir, "report.md")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))

    # Generate HTML report
    try:
        effective_plan_path = Path(plan_path) if plan_path else Path(out_dir) / f"{prefix}.md"
        html_content = generate_html_report(
            groups=groups_to_display or [],
            plan_path=effective_plan_path,
            phase_dir=Path(phase_dir),
            phase_type=phase_name,
            models=successful_models,
            failed_models=failed_models,
            base_ref=base_ref,
            tasks_path=tasks_path,
            template_style=template_style,
            diff_data=diff_data,
            served_models=served_models,
            usage=usage,
            requested_models=requested_models,
            salvage_requested=salvage_requested,
        )
        write_html_report(html_content, Path(phase_dir))
        print(f"HTML report written to: {os.path.join(phase_dir, 'report.html')}")
    except Exception as e:
        print(f"Warning: Failed to generate HTML report: {e}")

    # A detached run's caller never saw this stdout, so success has to hand back
    # paths rather than a search: `status` on a `done` run prints these and
    # repeats them in MULTI_LLM_RESULT.artifacts. A no-op in the foreground —
    # `record_output_files` kept the handle guard `report_progress` gave up, so a
    # non-detached `.status.json` still gains no `output_files` (it gains
    # `progress`, and nothing else).
    report_html_path = os.path.join(phase_dir, "report.html")
    grouped_path_out = os.path.join(phase_dir, "grouped.json")
    validation_path_out = os.path.join(phase_dir, "validation.json")
    # validation.json is named on BOTH channels or on neither. The host reads the
    # poll result, whose artifacts are rebuilt from `output_files`, and
    # `apply_task_suggestions_orchestrator.load_data` hard-fails without this
    # file — so a run that recorded it only in the terminal `MULTI_LLM_RESULT`
    # (which a detached run prints into a log nobody reads) left the next phase
    # with no way to learn the file exists. `record_output_files` records only
    # paths that exist, which is the same guard the artifact list uses below.
    _detach.record_output_files(
        phase_dir,
        report=report_path,
        report_html=report_html_path,
        grouped=grouped_path_out,
        validation=validation_path_out,
    )

    # The terminal `MULTI_LLM_RESULT.artifacts` half of the same hand-back;
    # validation.json only when it exists, it being the one machine-readable
    # record of the verdicts the report describes.
    record_review_artifacts(report_path, report_html_path, grouped_path_out,
                            validation_path_out)

    # Every lane records this the same way. review-plan and review-tasks used
    # to print `HIGH priority: N` (validation prep only, and a count of
    # suggestions) and record nothing, while review-code recorded its
    # distinct-HIGH-group count in `.status.json` and on the result line; a
    # plan suggestion carries the same `importance` field, so the same fact
    # is now recorded for all three.
    record_high_priority_groups(phase_dir, groups_to_display)
    # §6 T6.1: every completion path (the fan-out's first run and
    # `--reaggregate`) reaches this function, so recording here recomputes
    # the counts, up or down, wherever the report is rebuilt.
    record_validation_counts(phase_dir, groups_to_display)

    return report_path


# ---------------------------------------------------------------------------
# Report formatting helpers
# ---------------------------------------------------------------------------

def format_group(group: Dict[str, Any], group_idx: int) -> List[str]:
    """Format a suggestion group for the markdown report.

    Args:
        group: Group dict with theme, suggestions, validation info, etc.
        group_idx: 1-based group index for display.
    """
    theme = group.get("theme", "Untitled Group")
    category = group.get("category", "unknown")
    validation_status = group.get("validation_status")
    validation_reason = group.get("validation_reason")
    priority_score = group.get("priority_score", 0)
    models = group.get("models", [])
    suggestions = group.get("suggestions", [])

    validation_display = {
        "valid": "Valid",
        "invalid": "Invalid",
        "needs-human-decision": "? Needs Review",
        "validation_failed": "? Validation Failed",
    }
    validation_str = validation_display.get(validation_status, "? Unknown") if validation_status else "? Unknown"

    highest_importance = compute_max_importance(suggestions) or "LOW"

    display_label = group.get("display_label", f"G{group_idx}")
    display_hash = group.get("display_hash", "")
    if display_hash:
        header = f"## {display_label} [{display_hash}]: {theme}"
    else:
        header = f"## {display_label}: {theme}"

    lines = [
        header,
        "",
    ]

    lines.append(f"- [ ] Skip this group")
    if validation_status in ("needs-human-decision", "validation_failed"):
        lines.append("- [ ] Mark valid")
        lines.append("- [ ] Mark invalid")
    # "Let the agent decide" routes this item to the per-item judge at apply time.
    # Scoped to needs-human-decision only (validation_failed stays valid/invalid
    # or --revalidate).
    if validation_status == "needs-human-decision":
        lines.append("- [ ] Let the agent decide")

    lines.extend([
        f"**Validation:** {validation_str} | "
        f"**Category:** {category} | "
        f"**Priority:** {priority_score} | "
        f"**Highest Importance:** {highest_importance} | "
        f"**Models:** {', '.join(models)}",
        "",
    ])

    if validation_reason and validation_status in ("invalid", "needs-human-decision", "validation_failed"):
        lines.append(f"> **Validation Reason:** {validation_reason}")
        lines.append("")

    sorted_suggestions = sorted(
        suggestions,
        key=lambda s: IMPORTANCE_ORDER.get(s.get("importance", "LOW").upper(), 3)
    )

    for suggestion_idx, suggestion in enumerate(sorted_suggestions, 1):
        lines.extend(format_suggestion_in_group(
            suggestion, group_idx, suggestion_idx,
            group_validation_status=validation_status or "",
            group_suggestion_count=len(suggestions),
        ))

    lines.append("---")
    lines.append("")

    return lines


def format_suggestion_in_group(
    suggestion: dict,
    group_idx: int,
    suggestion_idx: int,
    group_validation_status: str = "",
    group_suggestion_count: int = 1,
) -> List[str]:
    """Format a single suggestion within a group for the markdown report.

    Args:
        suggestion: Suggestion dict.
        group_idx: 1-based group index.
        suggestion_idx: 1-based suggestion index within group.
        group_validation_status: Validation status of the parent group.
        group_suggestion_count: Number of suggestions in the parent group.
    """
    suggestion_id = f"G{group_idx}S{suggestion_idx}"
    title = suggestion.get("title", "Untitled")
    desc = suggestion.get("desc", "")
    stype = suggestion.get("type", "unknown")
    reference = suggestion.get("reference", "")
    importance = suggestion.get("importance", "LOW").upper()
    model = suggestion.get("model", suggestion.get("source_model", "unknown"))

    display_label = suggestion.get("display_label", suggestion_id)
    display_hash = suggestion.get("display_hash", "")
    if display_hash:
        header = f"### {display_label} [{display_hash}]: {title}"
    else:
        header = f"### {display_label}: {title}"

    lines = [
        header,
    ]
    lines.append(f"- [ ] Skip")
    if group_validation_status in ("needs-human-decision", "validation_failed") and group_suggestion_count > 1:
        lines.append("- [ ] Mark valid")
        lines.append("- [ ] Mark invalid")
        # "Let the agent decide" — needs-human-decision only. Single-suggestion
        # groups use the group-level checkbox (no per-suggestion select here).
        if group_validation_status == "needs-human-decision":
            lines.append("- [ ] Let the agent decide")
    lines.extend([
        f"**Importance:** {importance} | "
        f"**Type:** {stype} | "
        f"**Section:** {reference} | "
        f"**Model:** {model}",
        "",
        desc,
        "",
    ])

    return lines


def format_suggestion(
    suggestion: dict,
    validation_status: Optional[str] = None,
    validation_reason: Optional[str] = None,
) -> List[str]:
    """Format a single suggestion for the markdown report.

    Args:
        suggestion: Suggestion dict with id, title, type, reference, desc, etc.
        validation_status: Optional validation status string.
        validation_reason: Optional validation reason string.
    """
    validation_display = {
        "valid": "Valid",
        "invalid": "Invalid",
        "needs-human-decision": "? Needs Review",
        "validation_failed": "? Validation Failed",
    }
    validation_str = validation_display.get(validation_status, "? Unknown") if validation_status else "? Unknown"

    lines = [
        f"### {suggestion['id']}: {suggestion['title']}",
    ]
    lines.append(f"- [ ] Skip")
    lines.extend([
        f"**Validation:** {validation_str} | "
        f"**Model:** {suggestion.get('model', 'unknown')} | "
        f"**Type:** {suggestion['type']} | "
        f"**Section:** {suggestion['reference']}",
        "",
    ])

    if validation_reason and validation_status in ("invalid", "needs-human-decision", "validation_failed"):
        lines.append(f"> **Validation Reason:** {validation_reason}")
        lines.append("")

    lines.extend([
        suggestion['desc'],
        "",
        "---",
        "",
    ])
    return lines


# ---------------------------------------------------------------------------
# Reaggregation
# ---------------------------------------------------------------------------

def resolve_result_files_by_model(
    phase_dir: str,
    result_files: List[str],
    unsanitize: Dict[str, str],
    *,
    noun: str = "suggestions",
) -> List[Tuple[str, str, Any]]:
    """Map globbed result files to logical models — one file per model (W3).

    A phase dir that straddles the L1 anchor upgrade holds BOTH ``<model>.json``
    (written before L1) and ``<provider>_<model>.json`` (written by the resume,
    which looked for the anchored name, did not find it, and **re-ran** that
    model). Every ``--reaggregate`` path globs ``*.json``, so it sees two files;
    they are two answers from ONE logical model, and reading both double-counts
    every finding. That is not cosmetic: ``source_model`` is what grouping
    attributes by, and ``SuggestionGroup._recalculate_priority`` scores
    ``len(self.models) + Σ importance``, so a finding read twice renders as two
    models agreeing when one model said it once — corroboration that did not
    happen. Collapsing the model *set* alone would not fix it; the payload of
    exactly one file per model has to be the one that reaches the aggregate.

    Identity is the **recorded canonical spec** in ``.status.json``, never the
    filename: ``sanitize_model_name`` is lossy in one direction only, so a legacy
    stem cannot be re-resolved into a spec, but it CAN be matched against the
    stems the recorded specs generate. (It is also the only workable direction
    because ``write_status`` replaces ``models_requested`` wholesale, so after the
    resume the checkpoint holds the canonical specs only.)

    Shared by both ``--reaggregate`` implementations — this module's, and
    ``code_review_orchestrator.reaggregate_from_existing_files``, which
    accumulates into ``all_issues``/``results`` and would otherwise render the
    same model twice in its report. *unsanitize* is passed in rather than built
    here so each caller keeps its own ``build_unsanitize_map`` seam.

    Args:
        phase_dir: The phase directory the files were globbed from.
        result_files: Candidate model-result paths, already filtered of
            non-model artifacts by the caller's ``exclude_patterns``.
        unsanitize: ``build_unsanitize_map(phase_dir)`` — ``sanitize(spec) -> spec``
            over the checkpoint's ``models_requested``/``models_completed``.
        noun: What the payloads are called in the log lines ("suggestions",
            "issues").

    Returns:
        ``[(model, chosen_path, payload)]`` ordered by model, exactly one entry
        per logical model. Unreadable files are warned about and dropped, as
        before.

    Raises:
        SystemExit: exit 3 when one legacy stem matches two or more recorded
            specs — the genuine ambiguity, which fails closed.
    """
    recorded_specs = sorted(set(unsanitize.values()))
    anchored_stems = {sanitize_model_name(spec): spec for spec in recorded_specs}
    legacy_stems: Dict[str, List[str]] = {}
    for spec in recorded_specs:
        if ":" not in spec:
            continue
        legacy_stems.setdefault(
            sanitize_model_name(spec.split(":", 1)[1]), []
        ).append(spec)

    def resolve_recorded_identity(stem: str) -> Tuple[str, bool]:
        """Map a result-file stem to ``(model identity, is_anchored)``."""
        if stem in anchored_stems:
            return anchored_stems[stem], True
        legacy_candidates = legacy_stems.get(stem, [])
        if len(legacy_candidates) > 1:
            # `openai:gpt-5.2` and `openrouter:gpt-5.2` both generate the legacy
            # stem `gpt-5_2`, and there is no evidence on disk for which one wrote
            # the file. Attributing it to either fabricates a `source_model`;
            # splitting it across both is the double count again. Fail closed on
            # the same needs-human code the resume reader uses on this path.
            print(
                "ERROR: "
                f"{os.path.join(phase_dir, stem + '.json')} is a pre-anchor result "
                "file whose name matches more than one model recorded in "
                f"{os.path.join(phase_dir, '.status.json')}: "
                + ", ".join(legacy_candidates)
                + ". Remove it, or rename it to the <provider>_<model>.json name of "
                "the model that wrote it, then re-run --reaggregate.",
                file=sys.stderr,
            )
            sys.exit(3)
        if legacy_candidates:
            return legacy_candidates[0], False
        # No recorded spec claims this stem — a hand-copied dir, or one with no
        # `.status.json` at all: the stem IS the identity, exactly as before.
        return unsanitize.get(stem, stem), True

    # identity -> [(is_anchored, path, payload)]
    files_by_model: Dict[str, List[Tuple[bool, str, Any]]] = {}
    for result_path in sorted(result_files):
        try:
            with open(result_path, 'r', encoding='utf-8') as f:
                payload = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"  Warning: Could not read {result_path}: {e}")
            continue
        stem = os.path.basename(result_path)[: -len(".json")]
        model, is_anchored = resolve_recorded_identity(stem)
        files_by_model.setdefault(model, []).append(
            (is_anchored, result_path, payload)
        )

    resolved: List[Tuple[str, str, Any]] = []
    for model in sorted(files_by_model):
        # The anchored file wins unconditionally, identical payloads or not:
        # `sanitize_model_name(model_spec) + ".json"` is precisely what the normal
        # path reads, so "anchored wins" is what makes --reaggregate agree with the
        # run it is re-aggregating, and it is the newer file by construction.
        candidates = sorted(files_by_model[model], key=lambda e: (not e[0], e[1]))
        _, chosen_path, payload = candidates[0]
        for _, skipped_path, skipped in candidates[1:]:
            if skipped != payload:
                # Salvage never refuses a whole phase because a stale pre-anchor
                # file disagrees with the file the normal path would have used —
                # that strands results, and it would make salvage stricter than
                # the run it salvages. The divergence is recorded loudly and the
                # newer answer is used.
                print(
                    f"  WARN: {skipped_path} ({len(skipped)} {noun}) disagrees "
                    f"with {chosen_path} ({len(payload)} {noun}) for "
                    f"{model}; using the anchored file."
                )
            # Skipped, not merged and not content-deduplicated.
            print(
                f"  Skipping pre-anchor duplicate {skipped_path} "
                f"({model} is read from {chosen_path})"
            )
        resolved.append((model, chosen_path, payload))
    return resolved


async def reaggregate_from_existing_files(
    prefix: str,
    out_dir: str,
    phase_dir: str,
    phase_name: str,
    plan_path: str,
    args: argparse.Namespace,
    orchestrator_script: str,
    extra_validation_metadata: Optional[Dict[str, str]] = None,
    base_ref: Optional[str] = None,
    tasks_path: Optional[Path] = None,
    template_style: str = 'pr',
    diff_data: Optional[Dict] = None,
    supports_consolidation: bool = False,
) -> None:
    """Re-aggregate all model results after salvage operations complete.

    Args:
        prefix: Output file prefix
        out_dir: Output directory (base folder)
        phase_dir: Phase-specific directory containing model results
        phase_name: Phase name (e.g., 'review-plan', 'review-tasks')
        plan_path: Path to the plan file
        args: Command-line arguments for validation settings
        orchestrator_script: Name of the orchestrator script for reaggregate command
        extra_validation_metadata: Optional extra fields for validation_tasks.json
            (e.g., {"tasks_file": "/path/to/tasks.md"})
        base_ref: Optional git ref for PR-style diff context (forwarded to
            ``aggregate_results()``).
        tasks_path: Optional path to tasks JSON for task-view metadata
            (forwarded to ``aggregate_results()``).
        template_style: Template to use — ``'pr'`` or ``'flat'``
            (forwarded to ``aggregate_results()``).  Defaults to ``'pr'``.
        diff_data: Optional pre-computed diff hunk data (forwarded to
            ``aggregate_results()``).
        supports_consolidation: Whether this phase supports consolidation; when
            true the recommendation is recomputed from the reaggregated groups
            (§7.2a), exactly as the first run does.
    """
    import glob as glob_module

    pattern = os.path.join(phase_dir, "*.json")
    all_files = glob_module.glob(pattern)

    # `subagent_batch_report` is executor bookkeeping (D3i), not a model
    # result: it lives in the phase dir and MUST be excluded or the glob
    # below would parse it as a suggestion list and crash reaggregate.
    # `subagent_dry_run` is the same hazard from --dry-run-subagents (D3l), which
    # writes into THIS dir on a read phase; `write_batch_report`/`write_tasks` are
    # the write scheduler's, which normally land in an apply/implement dir but are
    # listed here so a shared or hand-copied phase dir cannot resurrect the bug.
    exclude_patterns = ['grouped', 'validation', 'salvage', 'revalidation', 'consolidated', 'consolidation', 'report_data', 'subagent_batch_report', 'subagent_dry_run', 'write_batch_report', 'write_tasks']
    result_files = [
        f for f in all_files
        if not any(os.path.basename(f).startswith(ex) or ex in os.path.basename(f) for ex in exclude_patterns)
    ]
    # Only the models this phase records are read (live run 10: a reviewer's
    # misnamed file was loaded as a third reviewer by its stem). Any other
    # result file is named and set aside; a dir with no recorded models keeps
    # the stem-as-identity reading below.
    result_files = _result_files.set_aside_unrecorded_results(phase_dir, sorted(result_files))
    _result_files.publish_result_notes(phase_dir)

    # The mode word a zero-result exit names in its `--force` retry command.
    reaggregate_mode = _modes().mode_for_script(orchestrator_script) or phase_name

    if not result_files:
        print(f"No model result files found in: {phase_dir}")
        # Decision 11.11 (T5.4c): nothing to aggregate because every requested
        # reviewer failed is the fan-out's exit 3 naming them, not a quiet
        # exit 0; with no recorded failure it stays exit 0.
        no_results, _requested = remaining_failed_models(phase_dir, [])
        announce_remaining_failures(phase_dir, no_results)
        exit_when_every_reviewer_failed(
            phase_dir, no_results, mode=reaggregate_mode, plan_path=plan_path,
        )
        return

    # T5, the lane with no fan-out at all: a `--reaggregate` invocation's whole
    # work — regrouping, and on a phase that needs it a full revalidation pass —
    # is the silent window, with no per-model ticker ahead of it to have covered
    # any of it. Same object, same cadence, same `progress.subagents` read; it
    # prints and writes nothing, so the map the original run's sweep froze is
    # untouched.
    phase_ticker = PhaseProgress(str(phase_dir), anchor=plan_path)
    phase_ticker.start_ticker()
    # One yield, so the ticker task is really *entered* before the phase's
    # synchronous stretch begins. `ensure_future` only schedules it, and a
    # task cancelled before its first step never runs its body at all — so
    # without this a tail that happens to contain no `await` (the
    # host-driven `validation_pending` return is one) would emit no
    # `[PROGRESS]` line even at teardown, and the log's last such line would
    # be the fan-out's rather than the phase's terminal step.
    await asyncio.sleep(0)
    # Set only where THIS invocation writes a terminal `progress.step`. The
    # teardown line reads the checkpoint, so on every other ending — an exit 3
    # refusal (changed snapshot, stale task file), "only n/m batch files", no
    # suggestions — it would re-print the previous run's `step: complete |
    # subagents 16/16 done` as if this process had finished (dogfood
    # 2026-09-25). Those endings print their own reason instead.
    concluded = False
    try:
        # Collect all suggestions
        all_suggestions = []
        models_found = set()
        results_by_model: Dict[str, List[Dict[str, Any]]] = {}

        # Restore original model specs (with colons) from .status.json
        unsanitize = build_unsanitize_map(phase_dir)

        for model, _chosen_path, suggestions in resolve_result_files_by_model(
            phase_dir, result_files, unsanitize
        ):
            models_found.add(model)
            # `s["source_model"] = model` is an item assignment, so one non-dict
            # element in one file used to raise TypeError and lose every model's
            # suggestions — the same defect code-review's reaggregate carried.
            suggestions = drop_non_record_entries(
                suggestions, model, noun="suggestions"
            )
            for s in suggestions:
                s["source_model"] = model
            all_suggestions.extend(suggestions)
            results_by_model[model] = suggestions
            print(f"  Loaded {len(suggestions)} suggestions from {model}")

        print(f"\nRe-aggregating {len(all_suggestions)} suggestions from {len(models_found)} models")

        # Same reconciliation as code-review's reaggregate: a result file on disk
        # is a completed model, whatever the fan-out recorded before the salvage
        # (or the out-of-band result) that produced it.
        for model in record_models_present(phase_dir, sorted(models_found)):
            print(f"[{model}] result file present; recorded as completed (was failed)")

        # Plan §5 (T5.1/T5.4a): read back only now, after the reconciliation
        # above moved every model with a file out of `models_failed`. What is
        # left — plus any requested model with neither a file nor a recorded
        # failure — is named here, on every ending below, and in the report.
        failed_models_map, requested_set = remaining_failed_models(
            phase_dir, sorted(models_found)
        )
        announce_remaining_failures(phase_dir, failed_models_map)

        # No readable result at all (no result file on disk could be read). Only
        # this case returns early; `all_suggestions` is necessarily empty here.
        if not models_found:
            print("No suggestions to aggregate.")
            # §7.2a: zero groups is a recount too — clear what an earlier
            # round recommended.
            recompute_consolidation_recommendation(
                str(phase_dir), [], args, supports_consolidation,
            )
            # §6 T6.1: and the verdict counts, which no report rebuild will
            # reach on this early return.
            record_validation_counts(str(phase_dir), [])
            # T5.4c: no readable result at all, and reviewers recorded failed:
            # exit 3 like the fan-out; with no recorded failure, exit 0.
            exit_when_every_reviewer_failed(
                phase_dir, failed_models_map,
                mode=reaggregate_mode, plan_path=plan_path,
            )
            return
        # Readable results that hold no findings (`[]` from every model that
        # answered) are a finished review with zero groups, not "nothing to
        # aggregate": they go through the same report rebuild, partial-results
        # report and completion below as any other reaggregate. Returning here
        # used to leave a reviewer that failed beside a clean `[]` out of
        # report.md, off `[PARTIAL_RESULTS]`, and the phase unrecorded, while
        # the invocation still ended `done`.

        # Group similar suggestions - preserve existing groups if validation exists
        grouped_path = os.path.join(phase_dir, "grouped.json")
        validation_path_check = os.path.join(phase_dir, "validation.json")
        validation_tasks_path_check = os.path.join(phase_dir, "validation_tasks.json")

        has_existing_validation = (
            (os.path.exists(validation_path_check) and not args.skip_validation) or
            os.path.exists(validation_tasks_path_check)
        )

        # Zero findings bind nothing: a grouped.json on disk belongs to an
        # earlier round's findings, so it is rewritten (to zero groups) rather
        # than reused, as code-review's reaggregate does.
        reuse_bound_grouping = (
            bool(all_suggestions)
            and has_existing_validation
            and os.path.exists(grouped_path)
        )
        if reuse_bound_grouping:
            with open(grouped_path, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
            grouped = load_groups_payload(raw_data)
            # Reuse presumes the bound file still describes the results on disk.
            # The documented salvage flow breaks that presumption by design: the
            # fan-out groups without the failed model, materializes validation and
            # returns at the marker; the salvage lands afterwards; `--reaggregate`
            # then found a bound grouping and reused it, so the salvaged model's
            # findings never reached a group (see `grouped_coverage_gap` for the
            # measured review-code instance, 2026-09-17). Retire the round and
            # regroup below.
            gap = grouped_coverage_gap(grouped, results_by_model)
            if gap:
                print(
                    "grouped.json does not cover the model results on disk; "
                    "regrouping and retiring the validation round bound to it:"
                )
                for line in gap:
                    print(f"  {line}")
                retire_stale_validation_round(
                    phase_dir, reason="grouped.json did not cover the results on disk"
                )
                reuse_bound_grouping = False

        if reuse_bound_grouping:
            print(f"Using existing grouped.json (preserves validation alignment)")
        else:
            raw_grouped = group_similar_suggestions(all_suggestions)
            grouped = [g.to_dict() if hasattr(g, 'to_dict') else g for g in raw_grouped]
            stamp_stable_ids(grouped)
            # D7: a re-group orphans any verdicts on disk, so they leave with it.
            retire_stale_validation(phase_dir, reason="grouped.json rewritten by reaggregate")
            with open(grouped_path, 'w', encoding='utf-8') as f:
                json.dump(save_groups_payload(grouped), f, indent=2)
            print(f"Grouped suggestions saved to: {grouped_path}")

        plan_content = read_plan(plan_path)

        validated_groups_for_report: Optional[List[Dict]] = None
        validation_path = os.path.join(phase_dir, "validation.json")
        validation_tasks_path = os.path.join(phase_dir, "validation_tasks.json")

        # Task 2.10: a round materialized under context contract 1 from an
        # over-limit document judged its head alone. Neither its prompts nor the
        # verdicts reached from them are reused: the whole round is retired
        # (renamed, kept for history) and rematerialized below in the path form.
        legacy_round = (
            None if args.skip_validation else legacy_context_round_reason(phase_dir)
        )
        if legacy_round:
            print(f"\n{legacy_round}")
            retire_stale_validation_round(
                phase_dir,
                reason="validation built from truncated context (contract 1)",
            )

        # Check if validation already completed. D7: a validation.json is honoured
        # only when it binds to the grouped.json beside it (or, for a legacy file
        # without the binding, when no batch file postdates it); otherwise it is
        # retired — renamed, not deleted — and the batch files decide.
        honour_validation_file = os.path.exists(validation_path) and not args.skip_validation
        use_note = ""
        if honour_validation_file:
            # §7.1: bound to the exact batch bytes it merged (`batch_sha256` +
            # `batch_manifest`), so a rewritten, restored or missing batch
            # retires it by content; only a file without the binding falls back
            # to the legacy mtime test. Both outcomes name what was checked.
            stale_reason, use_note = validation_source_decision(
                Path(validation_path), Path(grouped_path),
                Path(validation_tasks_path),
            )
            if stale_reason:
                print(f"\nNot using validation.json: {stale_reason}")
                retire_stale_validation(phase_dir, reason=stale_reason)
                honour_validation_file = False

        if not grouped:
            # Zero groups: nothing to validate, and no round to materialize,
            # merge or resume — a leftover validation_tasks.json is bound to the
            # grouping just rewritten and must not be read against it.
            validated_groups_for_report = []
            # So it retires with the rest of that round, and `validation.json`
            # is written as `[]`, the fan-out's empty branch and code-review's
            # reaggregate alike. The regroup above retired `validation.json`
            # alone and put nothing in its place, so apply-suggestions exited 1
            # on the missing file after a reaggregate that found nothing
            # (measured 2026-10-09; plan improve-plan-and-improve-code §2.3,
            # *Empty apply outcomes*).
            retire_stale_validation_round(
                phase_dir, reason="review returned no suggestions"
            )
            with open(validation_path, 'w', encoding='utf-8') as f:
                f.write("[]\n")
        elif honour_validation_file:
            # §2.3 step 5 / 2.9 apply to reused verdicts too, not only to the
            # batch-merge branch below: a merged validation.json whose batch
            # hashes still match says nothing about the snapshots its prompts
            # named. Re-hash them (exit 3 on a missing or changed one) and
            # rebind a moved phase dir before the verdicts are reused. No task
            # file (an internal validation) records no sources to verify.
            reused_round: Optional[Dict[str, Any]] = None
            if os.path.exists(validation_tasks_path):
                try:
                    reused_round = read_task_file(
                        validation_tasks_path, phase_dir=phase_dir
                    )
                except TaskFileError as task_file_error:
                    print(f"ERROR: {task_file_error}", file=sys.stderr)
                    sys.exit(task_file_error.exit_code)
                verify_round_context(reused_round, phase_dir, validation_tasks_path)
            print(
                f"\nUsing validation.json"
                f"{f' ({use_note})' if use_note else ''} for report generation..."
            )
            try:
                from .validation import load_validation_results as load_validation_v2
                validation_results = load_validation_v2(Path(validation_path))
                validated_groups = apply_validation_to_groups(
                    [g.to_dict() if hasattr(g, 'to_dict') else g for g in grouped],
                    validation_results
                )
                validated_groups_for_report = validated_groups
                print(f"Loaded {len(validation_results)} validation results")
                # §2.4: the reused round re-publishes its own recorded context
                # with the reused verdicts, as every merge does.
                publish_from_task_document(
                    phase_dir, reused_round, validation_results
                )
            except Exception as e:
                print(f"Warning: Could not load validation.json: {e}")
                validated_groups_for_report = None

        # Check if batched validation completed
        elif os.path.exists(validation_tasks_path) and not args.skip_validation:
            print("\nFound validation_tasks.json, checking for completed batches...")
            # A phase dir outlives the run that wrote it, and with prompts embedded a
            # task file is a snapshot: a run started under one skill version and
            # resumed under the other would silently mis-spawn, and a plan edited
            # between materialization and resume leaves prompts that still validate
            # cleanly while reviewing text nobody is looking at any more. Both fail
            # loudly here (exit 3) rather than dispatching anything. Read outside the
            # try below, whose broad handler would otherwise downgrade the refusal to
            # a warning.
            try:
                batch_metadata = read_task_file(
                    validation_tasks_path,
                    phase_dir=phase_dir,
                    current_inputs=build_inputs(
                        plan_file=str(plan_path),
                        grouped_file=grouped_path,
                        # review-tasks embeds the task list in every prompt, so an
                        # edit to it between materialization and resume is as stale
                        # as an edited plan. Absent for every other phase, and
                        # unrecorded hashes are simply not compared.
                        tasks_file=(extra_validation_metadata or {}).get("tasks_file"),
                    ),
                )
            except TaskFileError as task_file_error:
                print(f"ERROR: {task_file_error}", file=sys.stderr)
                sys.exit(task_file_error.exit_code)
            # §2.3 step 5 / 2.9: the snapshots this round's prompts name are
            # re-hashed before anything is reused or dispatched, and a moved or
            # copied phase dir rebinds its prompts to the copy's own snapshot.
            # A missing or changed snapshot refuses the round (exit 3).
            verify_round_context(batch_metadata, phase_dir, validation_tasks_path)
            # The recorded `prompt_path` is a derived convenience field like
            # `output_path`, so it goes stale the moment a phase dir is moved or
            # copied — and a host following it would then hand a subagent a file
            # that is missing, or one somebody edited. Re-derive from the
            # loaded-from dir and rewrite anything that is not `prompt` byte for
            # byte, before a single batch is dispatched.
            if ensure_prompt_sidecars(batch_metadata, phase_dir):
                # Native hosts reread the JSON, not this in-memory document. Publish
                # rebound pointers and removed fallback fields before handing off.
                from .subagent_executor import _atomic_write_json

                try:
                    _atomic_write_json(validation_tasks_path, batch_metadata)
                except OSError as exc:
                    print(
                        f"ERROR: Could not persist repaired prompt metadata to "
                        f"{validation_tasks_path}: {exc}. Fix task-file write access "
                        "and retry reaggregation before dispatching native subagents.",
                        file=sys.stderr,
                    )
                    sys.exit(3)
            try:
                total_batches = batch_metadata.get("total_batches", 0)
                batches_found = 0
                for batch in batch_metadata.get("batches", []):
                    batch_file = os.path.join(phase_dir, f"validation_batch_{batch['batch_index']}.json")
                    if os.path.exists(batch_file):
                        batches_found += 1

                if batches_found == total_batches and total_batches > 0:
                    print(f"All {total_batches} batch files found, merging...")
                    validated_groups_for_report = merge_validation_batches(
                        phase_dir, batch_metadata, grouped, validation_path
                    )
                elif await asyncio.to_thread(
                    dispatch_subagent_tasks,
                    args,
                    task_file=validation_tasks_path,
                    phase_dir=phase_dir,
                    phase=phase_name,
                    document=batch_metadata,
                    plan_path=str(plan_path),
                    label="validation",
                    # D2 row 10: this path used to pass none, so its own failure
                    # printed the "re-run the same command" fallback — a flag-less
                    # hint by omission. The document's triple, live flags winning.
                    retry_command=resolved_reaggregate_command(batch_metadata),
                ):
                    # D3b on the reaggregate path: a run resumed with
                    # --exec-subagents dispatches the still-incomplete batches itself
                    # (completed ones are skipped by their result files, D3i) rather
                    # than telling a host to go run subagents it may not have.
                    validated_groups_for_report = merge_validation_batches(
                        phase_dir, batch_metadata, grouped, validation_path
                    )
                else:
                    print(f"Only {batches_found}/{total_batches} batch files found.")
                    print("Wait for all validation subagents to complete before reaggregating.")
                    return
            except Exception as e:
                print(f"Warning: Could not process batch metadata: {e}")
                validated_groups_for_report = None

        # Run internal validation if requested
        elif not args.skip_validation:
            internal_validation = getattr(args, 'internal_validation', False)
            if internal_validation:
                print("\nRunning internal validation...")
                validation_timeout = args.timeout if args.timeout else 600
                validation_results = await validate_groups(
                    [g.to_dict() if hasattr(g, 'to_dict') else g for g in grouped],
                    context=plan_content,
                    model=args.validation_model,
                    timeout=validation_timeout
                )

                validated_groups = apply_validation_to_groups(
                    [g.to_dict() if hasattr(g, 'to_dict') else g for g in grouped],
                    validation_results
                )
                validated_groups_for_report = validated_groups

                save_validation_results(
                    validation_results, Path(validation_path),
                    # §7.1a: merged from no batch files, so bound to none — an
                    # empty binding, not the legacy mtime fallback.
                    batch_sha256={},
                )
                print(f"Validation results saved to: {validation_path}")
            else:
                # Host-neutral: this print runs on every host that dispatches
                # subagent validation (opencode, codex, claude-code, ...), and
                # naming Claude Code here contradicted the runner the log names a
                # few lines later (measured 2026-09-16: an opencode-driven run
                # printed this beside 11 lines correctly naming opencode).
                print("\nPreparing batched validation for subagent execution...")
                extra_kwargs = {}
                if extra_validation_metadata:
                    extra_kwargs = {k: v for k, v in extra_validation_metadata.items()
                                    if k in ("tasks_file",)}
                # A re-materialized round is a new round with a new snapshot
                # (§2.3 step 5), bound from one read of the plan as it is now.
                plan_document = bind_plan_for_validation(str(plan_path), phase_dir)
                batched_tasks = prepare_batched_validation_tasks(
                    groups=[g.to_dict() if hasattr(g, 'to_dict') else g for g in grouped],
                    output_dir=phase_dir,
                    plan_file=str(plan_path),
                    model=args.validation_model,
                    orchestrator=orchestrator_script,
                    **validation_context_kwargs(
                        phase_name, plan_content, extra_validation_metadata,
                        plan_document=plan_document, phase_dir=phase_dir,
                    ),
                    runner_read_refusal=materialization_read_refusal(
                        args, str(plan_path)
                    ),
                    phase=phase_name,
                    **extra_kwargs,
                )
                batched_tasks["format_version"] = CURRENT_FORMAT_VERSION

                with open(validation_tasks_path, 'w', encoding='utf-8') as f:
                    json.dump(batched_tasks, f, indent=2)

                # The phase machine's own word for this stretch. `status` printed
                # `phase state: grouping_complete` beside `progress: validating` for
                # the whole validation run (measured 2026-09-16) because
                # `validation_pending` — documented in utils/status_file.py since D4
                # — was never written by anything.
                update_status(phase_dir, {"state": "validation_pending"})
                # And the progress word, as the first run's hand-off writes it.
                # The executor mirror still describes the PREVIOUS round's
                # batches (16/16 done), and nothing of this round has been
                # dispatched yet, so it is cleared rather than left beside the
                # new step; a dispatch below rewrites it from scratch.
                _detach.report_progress(
                    phase_dir, step="validation_pending", subagents=None
                )

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

                # D3b: with --exec-subagents this process continues past the marker
                # instead of exiting — dispatch the batch, then fall through to the
                # merge below and finish the phase in one invocation. The marker is
                # still printed above (logs and .status.json), but it is
                # informational on this path.
                if await asyncio.to_thread(
                    dispatch_subagent_tasks,
                    args,
                    task_file=validation_tasks_path,
                    phase_dir=phase_dir,
                    phase=phase_name,
                    document=batched_tasks,
                    plan_path=str(plan_path),
                    label="validation",
                    retry_command=reaggregate_cmd,
                ):
                    validated_groups_for_report = merge_validation_batches(
                        phase_dir, batched_tasks, grouped, validation_path
                    )
                else:
                    # The plan as the user typed it (fix round 14).
                    reaggregate_cmd = resolved_reaggregate_command(
                        batched_tasks, typed_plan=True,
                    )
                    print("\nAfter validation completes, run:")
                    print(f"  {reaggregate_cmd or ''}")
                    # The single follow-up a native-subagent host is owed, also
                    # exposed on the dispatcher's MULTI_LLM_RESULT line so a host
                    # that cannot parse prose does not have to regex-mine stdout.
                    record_next(reaggregate_cmd or None)
                    concluded = True
                    return
        else:
            print("\nSkipping validation (--skip-validation flag set)")

        # Build list of successful models. The failure map is the one read back
        # above (after `record_models_present`) — this used to hard-code `{}`,
        # so a reaggregated report never named a model that produced nothing.
        successful_models = list(models_found)

        # Generate report. `served_models` is what the fan-out recorded in the
        # checkpoint (§3.6's attribution and the D6 override's `sandbox: bypassed`,
        # 2026-09-17): the per-model files carry neither, so without this read a
        # reaggregated report named a bypassed slot as if it had run sandboxed.
        report_path = aggregate_results(
            prefix, out_dir, phase_dir, phase_name,
            successful_models, failed_models_map, validated_groups_for_report,
            plan_path=plan_path,
            base_ref=base_ref,
            tasks_path=tasks_path,
            template_style=template_style,
            diff_data=diff_data,
            served_models=recorded_served_models(phase_dir),
            # …and what it spent, read back off the same checkpoint for the same
            # reason: the per-model files never held it.
            usage=recorded_usage(phase_dir),
            # The denominator of "N of M requested": the recorded requested set,
            # never `progress` (a detached worker's claim drops it).
            requested_models=(
                len(requested_set) if requested_set is not None else None
            ),
        )

        print("\nReaggregation complete!")
        print(f"Report: {report_path}")

        # §7.2: this completion path had no recommendation block at all (the
        # first run's lived past the `--reaggregate` branch's early return), so
        # a reaggregate that changed the count left the old one standing.
        print(
            f"[consolidation] reaggregate: "
            f"{len(validated_groups_for_report or [])} validated group(s), "
            f"supports_consolidation={supports_consolidation}"
        )
        # `None` means this run produced no validated groups to count (validation
        # skipped, or validation.json could not be read) — not that there are
        # zero. Recounting it would delete a recommendation whose validated
        # groups still exist on disk, so only a list (empty included) recounts.
        if validated_groups_for_report is not None:
            recompute_consolidation_recommendation(
                str(phase_dir), validated_groups_for_report, args, supports_consolidation,
            )

        # T5.4b (decision 11.11): a reaggregate that still lacks some models
        # reports `[PARTIAL_RESULTS: …]` and `state: "partial"` (exit 0), as
        # the fan-out does — the host's cue to name them from
        # `progress.models`. `unattended=False`: the `[AUTO_RESOLVED]` record
        # that call writes names the fan-out's in-process continuation, never a
        # separate `--reaggregate`. The phase is still recorded completed below
        # and no `next` is recorded, so the result line keeps `next: null`.
        _unattended.report_partial_results(
            completed=sorted(models_found),
            failed=list(failed_models_map),
            phase_dir=str(phase_dir),
            unattended=False,
        )

        # Mark phase complete
        state = get_or_create_state(Path(plan_path))
        state.mark_phase_completed(phase_name)
        state.save()
        # The in-phase machine reaches its terminal word here too: a re-aggregated
        # phase is as finished as a freshly run one, and `status` reads this field.
        update_status(str(phase_dir), {"state": "complete"})
        _detach.report_progress(str(phase_dir), step="complete")
        concluded = True
    finally:
        # Cancelled and awaited past the terminal `progress.step`, exactly as on
        # the fan-out lane, so the log's last `[PROGRESS]` states `step:
        # complete` rather than whatever the last interval caught. The
        # `nothing to aggregate` early return comes out through here too. The
        # *other* early return — no result files at all — does not, and cannot:
        # it is taken before `PhaseProgress` is even constructed, which is the
        # right place for it (there is no phase window to narrate when the dir
        # holds nothing to read). F7, 2026-09-20: this comment used to claim
        # both of them passed through. 2026-09-25: it passes through, but prints
        # a teardown line only when this invocation wrote the step it reads
        # (`concluded`); otherwise the line would be the previous run's.
        await phase_ticker.stop_ticker(final_line=concluded)


# ---------------------------------------------------------------------------
# Main orchestration flow
# ---------------------------------------------------------------------------

def _ensure_state_file(state) -> None:
    """Write ``state.json`` if the plan has none yet (see the guard site)."""
    if not state.state_file.exists():
        state.save()


def already_completed_lines(
    mode_word: str, phase_dir: Union[str, Path], *, document: str = "plan",
) -> List[str]:
    """What a re-run of a review phase the plan already completed says: that
    it is done and nothing ran, where its results are, and the two ways to
    run it again (fix round 28, live run 12 #11: OpenCode 01f retried a
    review-plan its killed first attempt had finished and got "ERROR: Phase
    'review-plan' has already been completed … Use --force", which the host
    relayed as an error block). Nothing failed: the exit is 2, "nothing to
    do / phase already complete", which every route reads as a success, and
    the next phase is the result's ``user_next_step`` as on any exit 2.

    *document* is what the user calls the input: ``plan``, or ``commit brief``
    for a commit review (``commit_review.document_label``; plans/review-
    commits.md §2.8 "'Commit brief', never 'plan'"), whose caller also passes
    the commit mode the user typed as *mode_word*."""
    try:
        shown = os.path.relpath(str(phase_dir)).replace(os.sep, "/")
    except ValueError:  # Windows: another drive than the cwd's
        shown = os.pardir
    if shown == os.pardir or shown.startswith(os.pardir + "/"):
        shown = str(phase_dir)
    return [
        f"{mode_word} has already been completed for this {document}, so nothing "
        f"ran this time; its results are in {shown}.",
        "To run it again from the start, add --force to the command; to "
        "rebuild its report from the results already there, add --reaggregate.",
    ]


def report_already_completed(
    mode_word: str, phase_dir: Union[str, Path], *, document: str = "plan",
) -> int:
    """Print :func:`already_completed_lines`, carry them as the result's
    ``notice`` (the line every route relays as plain text above the next
    step) and return exit 2."""
    lines = already_completed_lines(mode_word, phase_dir, document=document)
    for line in lines:
        print(line)
    cli_common.add_notice(" ".join(lines))
    return cli_common.EXIT_NOTHING_TO_DO


async def run_review_orchestration(
    args: argparse.Namespace,
    phase_name: str,
    invoke_phase: str,
    salvage_phase_name: str,
    prompt_template: str,
    prompt_context_factory: Callable[[str], Dict[str, Any]],
    orchestrator_script: str,
    supports_consolidation: bool = False,
    consolidation_handlers: Optional[Dict[str, Callable]] = None,
    pre_run_hook: Optional[Callable[[], None]] = None,
    extra_validation_metadata: Optional[Dict[str, str]] = None,
    base_ref: Optional[str] = None,
    tasks_path: Optional[Path] = None,
    template_style: str = 'pr',
    diff_data: Optional[Dict] = None,
) -> None:
    """Main review orchestration flow shared across review phases.

    Args:
        args: Parsed command-line arguments (must have plan_file, models, etc.)
        phase_name: Phase directory/state name (e.g., 'review-plan', 'review-tasks')
        invoke_phase: Phase name for invoke_with_file_output (e.g., 'plan_review', 'task_review')
        salvage_phase_name: Phase name used in salvage request metadata
        prompt_template: The prompt template string
        prompt_context_factory: Factory function: model_spec -> prompt_context dict
        orchestrator_script: Script name for reaggregate command
        supports_consolidation: Whether this phase supports consolidation modes
        consolidation_handlers: Optional dict of consolidation mode handler functions
        pre_run_hook: Optional callable to execute before model invocation (e.g., validate tasks file)
        extra_validation_metadata: Optional dict of extra fields to pass to prepare_batched_validation_tasks
            and include in validation_tasks.json (e.g., {"tasks_file": "/path/to/tasks.md"})
        base_ref: Optional git ref for PR-style diff context (forwarded to
            ``aggregate_results()``).
        tasks_path: Optional path to tasks JSON for task-view metadata
            (forwarded to ``aggregate_results()``).
        template_style: Template to use — ``'pr'`` or ``'flat'``
            (forwarded to ``aggregate_results()``).  Defaults to ``'pr'``.
        diff_data: Optional pre-computed diff hunk data (forwarded to
            ``aggregate_results()``).
    """
    # Get absolute path for the plan file
    plan_path = os.path.abspath(args.plan_file)

    if not os.path.isfile(plan_path):
        print(f"ERROR: Plan file not found: {args.plan_file}")
        print(f"       Resolved path: {plan_path}")
        sys.exit(1)

    # §9.3.a/b: the anchor capture point. Absolute, taken before anything can
    # chdir and before any provider read that decides routing, so a call site
    # that forgets the keyword still falls back to THIS plan, not to CWD.
    set_run_anchor(plan_path)

    prefix = derive_prefix(plan_path)
    out_dir_arg = getattr(args, 'out_dir', None)
    base_dir = out_dir_arg or os.path.dirname(plan_path) or "."

    if os.path.basename(base_dir.rstrip(os.sep)) == prefix:
        out_dir = base_dir
    else:
        out_dir = os.path.join(base_dir, prefix)

    phase_dir = str(get_phase_dir(Path(plan_path), phase_name))

    # Handle --reaggregate mode
    if args.reaggregate:
        print("=== REAGGREGATE MODE ===")
        print(f"Plan file: {plan_path}")
        print(f"Output directory: {out_dir}")
        print(f"Phase directory: {phase_dir}")
        print("")

        if not os.path.isdir(phase_dir):
            print(f"ERROR: Phase directory does not exist: {phase_dir}")
            sys.exit(1)

        # The same detach boundary the fan-out crosses below, after the one
        # pre-flight this branch has. Without it a `--reaggregate --detach`
        # launch ran the whole re-dispatch in the invoker's foreground and
        # printed no run banner; the opencode plugin, which composes `--detach`
        # on every launch and adopts a run only from that banner, then reported
        # the completed run as an error it could not poll (measured
        # 2026-09-14 on review-tasks: "the launch reported no run_id on its
        # banner").
        outcome = maybe_detach(
            args=args,
            mode=_modes().mode_for_script(orchestrator_script) or phase_name,
            phase_dir=phase_dir,
            plan_file=plan_path,
            phase=phase_name,
        )
        if outcome is not None:
            sys.exit(outcome)

        await reaggregate_from_existing_files(
            prefix, out_dir, phase_dir, phase_name, plan_path, args, orchestrator_script,
            extra_validation_metadata=extra_validation_metadata,
            base_ref=base_ref,
            tasks_path=tasks_path,
            template_style=template_style,
            diff_data=diff_data,
            supports_consolidation=supports_consolidation,
        )
        return

    # Handle consolidation modes (only for phases that support them)
    if supports_consolidation and consolidation_handlers:
        if getattr(args, 'consolidate_dry_run', False):
            print("=== CONSOLIDATION DRY RUN MODE ===")
            print(f"Plan file: {plan_path}")
            print(f"Phase directory: {phase_dir}")
            print("")
            if not os.path.isdir(phase_dir):
                print(f"ERROR: Phase directory does not exist: {phase_dir}")
                sys.exit(1)
            consolidation_handlers['dry_run'](phase_dir, plan_path)
            return

        if getattr(args, 'consolidate', False):
            print("=== CONSOLIDATION MODE ===")
            print(f"Plan file: {plan_path}")
            print(f"Phase directory: {phase_dir}")
            print("")
            if not os.path.isdir(phase_dir):
                print(f"ERROR: Phase directory does not exist: {phase_dir}")
                sys.exit(1)
            # `args` is threaded so the handler can honor --exec-subagents
            # (D3b): with the flag on it dispatches the consolidation
            # batch and reaggregates in this same invocation.
            consolidation_handlers['consolidate'](phase_dir, plan_path, args)
            return

        if getattr(args, 'reaggregate_consolidation', False):
            print("=== REAGGREGATE CONSOLIDATION MODE ===")
            print(f"Plan file: {plan_path}")
            print(f"Phase directory: {phase_dir}")
            print("")
            if not os.path.isdir(phase_dir):
                print(f"ERROR: Phase directory does not exist: {phase_dir}")
                sys.exit(1)
            import glob as glob_module
            pattern_glob = os.path.join(phase_dir, "*.json")
            exclude = ['grouped', 'validation', 'salvage', 'revalidation', 'consolidated', 'consolidation', 'report_data', 'subagent_batch_report']
            result_files = [
                f for f in glob_module.glob(pattern_glob)
                if not any(os.path.basename(f).startswith(ex) or ex in os.path.basename(f) for ex in exclude)
            ]
            models = [os.path.basename(f).replace('.json', '') for f in result_files]
            consolidation_handlers['reaggregate_consolidation'](phase_dir, plan_path, prefix, models)
            return

    # Guard against re-running already-completed phase
    state_guard = get_or_create_state(Path(plan_path))
    # Materialize `state.json` on the phase's first run (2026-10-05). Nothing
    # else writes it before the phase completes, so on a plan's first phase
    # the instructions' `util metrics start --state-file {plan}/state.json`
    # (run between the fan-out and the validation subagents) failed with
    # "state file not found" (racing re-run, 2026-10-04, review-plan); the
    # host shrugged it off and the phase lost its ETA baseline. Written here,
    # after the completed-phase guard would have refused and before any
    # model runs, so the record of the run exists as soon as the run does.
    _ensure_state_file(state_guard)
    if state_guard.is_phase_completed(phase_name) and not args.force:
        sys.exit(report_already_completed(phase_name, phase_dir))
    elif args.force and state_guard.is_phase_completed(phase_name):
        state_guard.state.get("phases_completed", {}).pop(phase_name, None)
        state_guard.save()
        print("NOTE: Cleared previous phase completion (--force mode)")

    # Mutual exclusivity check
    if args.quick and args.interactive:
        print("ERROR: --quick and --interactive are mutually exclusive.")
        sys.exit(1)

    # Handle model selection (D6 row 2: auto-select `defaults.models` when
    # nothing was named; fail closed with exit 3 when nothing resolves).
    unattended = bool(getattr(args, "yes", False))
    try:
        model_specs = resolve_models(
            cli_models=args.models,
            interactive=args.interactive,
            quick=args.quick,
            mode=phase_name,
            anchor=plan_path,  # per-project config discovery follows the plan-derived root
            unattended=unattended,
        )
    except NeedsHuman as e:
        sys.exit(_unattended.fail_closed(e.message, site_id=e.site))
    except RuntimeError as e:
        print(f"ERROR: {e}")
        available = get_all_model_specs(anchor=plan_path)
        print(f"Use --models flag. Available: {', '.join(available[:5])}...")
        sys.exit(1)

    if not model_specs:
        print("ERROR: No models selected.")
        sys.exit(1)

    # Display selection
    if args.models:
        print(f"Using models from --models flag: {', '.join(model_specs)}")
    elif args.interactive:
        print(f"Using interactively selected models: {', '.join(model_specs)}")
    elif args.quick:
        print(f"Using quick models from providers.yaml: {', '.join(model_specs)}")
    else:
        print(f"Using default models from providers.yaml: {', '.join(model_specs)}")

    # Validate model specs
    invalid_models = [m for m in model_specs if not is_model_valid(m, anchor=plan_path)]
    if invalid_models:
        print(f"WARNING: Unknown models (proceeding anyway): {', '.join(invalid_models)}")
        # Anchored to match the rejection above: an anchored `is_model_valid`
        # paired with a CWD-discovered suggestion list is its own bug (§9.3.c).
        available = get_all_model_specs(anchor=plan_path)
        print(f"Available models: {', '.join(available[:10])}...")

    # Run pre-run hook (e.g., validate tasks file existence)
    if pre_run_hook:
        pre_run_hook()

    # Read plan content — once, as bytes (§2.3 step 5): the excerpt a
    # validator is shown, the snapshot it is pointed at and `inputs.plan_sha256`
    # all derive from this one read, never from a later re-read of a file other
    # sessions may be editing. Only the read and the UTF-8 check happen here, so
    # an undecodable plan still fails in the foreground; the bytes are bound to
    # this phase's `validation-snapshot.md` past the detach boundary below, once
    # this process owns the phase. Binding here replaced the snapshot of a run
    # that was still going whenever a repeated `--detach` launch (e.g. with
    # `--if-not-running`) found that run active and handed it back.
    try:
        plan_bytes = Path(plan_path).read_bytes()
        plan_content = decode_document(plan_bytes, plan_path)
    except ValidationContextError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(exc.exit_code)
    # `chars`, not `bytes`: this is `len(str)`, and on the measured 2026-09-16
    # run it reported 44096 for a 44389-byte file. Counting the encoded bytes
    # would be the other honest fix; the number a reader wants here is the one
    # the excerpt limits are expressed in, which is characters.
    print(f"Loaded plan: {plan_path} ({len(plan_content)} chars)")

    # Ensure output directories exist
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(phase_dir, exist_ok=True)

    # Snapshot the artifact THIS phase reviewed, named after what it holds.
    # review-plan reviews the plan; review-tasks reviews `tasks/tasks.md` and
    # never touches the plan, so its `backup.md` was a 44 KB copy of a file the
    # phase does not own — the same "the file named backup was not a backup of
    # what got overwritten" confusion `apply_orchestrator_base.write_target_backup`
    # documents. Neither review phase overwrites anything, so this is a record of
    # what was reviewed rather than a rollback point; `apply-task-suggestions`
    # writes its own pre-modification `tasks-backup.md` under its own phase dir.
    backup_source = str(tasks_path) if tasks_path else plan_path
    backup_path = os.path.join(
        phase_dir, "tasks-backup.md" if tasks_path else "backup.md"
    )
    try:
        # copyfile, not a re-write of the decoded text: a snapshot should be the
        # source's bytes, not what universal newlines made of them.
        shutil.copyfile(backup_source, backup_path)
        print(f"Backup saved: {backup_path}")
    except OSError as exc:  # a snapshot must not fail the phase
        print(f"Warning: could not write {backup_path}: {exc}", file=sys.stderr)

    print(f"Output prefix: {prefix}")
    print(f"Output directory: {out_dir}")
    print(f"Models: {', '.join(model_specs)}")
    if args.timeout:
        print(f"Timeout override: {args.timeout}s per model")
    else:
        print("Timeout: per-provider defaults from providers.yaml")
    print(f"Max parallel: {args.max_parallel}")
    print("")

    # --- the detach boundary -------------------------------------------------
    # Everything above ran in the foreground on purpose: arguments and flag
    # compatibility, the plan file and prior-phase inputs, provider/model
    # resolution, the completed-phase guard, output-dir creation and the write
    # probe. Detaching before them would bury an ordinary startup failure (a
    # typo'd flag, an unconfigured provider) inside orchestrator-run.log,
    # reachable only by polling `status` and finding `failed` seconds later. So
    # the fork happens here, once nothing knowable is left unchecked — and
    # nothing below this line runs in the invoker.
    outcome = maybe_detach(
        args=args,
        mode=_modes().mode_for_script(orchestrator_script) or phase_name,
        phase_dir=phase_dir,
        plan_file=plan_path,
        phase=phase_name,
        model_specs=model_specs,
    )
    if outcome is not None:
        sys.exit(outcome)

    # This process now owns the phase (the foreground run, or the detached
    # worker after `claim_run`), so the snapshot may be replaced. The worker is
    # a fresh process and reads the plan itself; the foreground run binds the
    # bytes it already read and decoded above.
    plan_document = bind_plan_for_validation(plan_path, phase_dir, data=plan_bytes)
    plan_content = plan_document.text

    # Stage U: what an earlier attempt of this phase recorded, read *before*
    # the write below — `write_status` replaces every key but the two reserved
    # objects, so the `usage` the last attempt wrote is gone the instant it
    # lands, and a resume's skipped models (which invoke no adapter) never
    # refill it. Without this the regenerated report and every `--reaggregate`
    # after it lost the numbers the first attempt paid for. Handed to the
    # fan-out rather than merged into `collect_usage`'s result wholesale, so
    # only a REUSED slot is restored: a model that really re-ran is reported on
    # what this attempt spent.
    prior_usage = recorded_usage(phase_dir) or {}
    # Landlock rung (2026-09-22): the previous run's sandbox words, read before
    # the same write erases them, so a contained rung this run can no longer
    # take is named once (`announce_retired_rungs`).
    prior_served = recorded_served_models(phase_dir) or {}
    write_status(phase_dir, {
        "phase": phase_name,
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
    # D6 row 2, recorded rather than merely applied: an auto-selection nobody can
    # see afterwards is indistinguishable from a silent degradation. Only under
    # `--yes`, where it replaced a question — with `--yes` unset nothing about a
    # run changes.
    if unattended and not args.models and not args.quick:
        _unattended.record_resolution(
            phase_dir,
            _unattended.row(2).site_id,
            "defaults.models: " + ", ".join(model_specs),
        )
    _detach.report_progress(
        phase_dir, step="fanout", models_total=len(model_specs),
        models_done=0, models_succeeded=0,
    )

    # The caller constructs the tracker because the caller is the one that
    # already knows all three of its inputs — the phase dir, the requested
    # specs, and the plan anchor every config read is resolved against (§9.3.c)
    # — and because it owns the map afterwards: the deadline backfill, the
    # both-counters restatement and the phase-scoped ticker all happen out here,
    # past the fan-out's return. The fan-out below owns only the mechanics.
    tracker = FanoutProgress(
        phase_dir, model_specs, anchor=plan_path, timeout=args.timeout
    )

    # A model whose spec changed since the last run has no slot here to retire
    # its old files; a re-aggregate would read them back (#30).
    retire_unselected_results(phase_dir, model_specs)

    # Run all models
    results = await run_all_models(
        model_specs,
        plan_path,
        prompt_template,
        prompt_context_factory,
        phase_name,
        invoke_phase,
        args.timeout,
        args.max_parallel,
        out_dir=out_dir,
        prefix=prefix,
        skip_existing=not getattr(args, "rerun_all", False),
        prior_usage=prior_usage,
        tracker=tracker,
    )

    # Save per-model results
    failed_models: Dict[str, str] = {}
    for model_spec, result in results.items():
        success = result["success"]
        output = result["output"]
        error = result["error"]

        # `output` is the answer of a run that completed and is `None` on every
        # losing path; `failure_output` is the text a losing run left behind, and
        # only salvage may read it. Keeping them separate across this call is
        # what stops a crashed provider whose stdout happened to parse from being
        # written to `{model}.json` and counted as a completed review — see
        # `save_model_result`'s docstring, and `run_single_model`'s `Returns:`
        # for where the two keys diverge. The stdout-then-stderr precedence lives
        # in `failure_output_from_result`, which is the same rule
        # `code_review_orchestrator`'s salvage site A applies to the other lane.
        if not save_model_result(
            prefix, model_spec, success, output, error, out_dir, phase_dir,
            salvage_phase_name,
            failure_output=failure_output_from_result(result),
            failure=result.get(SALVAGE_FAILURE_KEY),
        ):
            failed_models[model_spec] = error or "Unknown error"

    # F11: a model `run_models_concurrent`'s deadline cancelled has no result
    # file and, so far, no failure entry either. Same helper review-code uses,
    # and one pass writes both facts now — `failed_models[spec]` and the map's
    # own entry, under the one `DEADLINE_ERROR` wording.
    backfill_deadline_losses(model_specs, results, failed_models, tracker=tracker)

    # §3.6: which model actually served each slot. The per-model `{model}.json`
    # is a bare suggestion list reaggregation re-reads, so the attribution is
    # recorded once here and carried to the report rather than stamped into an
    # artifact whose shape another phase depends on. Empty for a default run.
    # The D6 override's `sandbox: bypassed` rides the same dict (2026-09-17),
    # and `--reaggregate` reads both back off `.status.json`'s `models_served`.
    served_models = collect_served_models(results)
    record_sandbox_bypassed(phase_dir, served_models)
    announce_retired_rungs(prior_served, served_models, anchor=plan_path)
    # Stage U, the same argument one field over: what each slot spent is on its
    # record and nowhere else, and `{model}.json` is a bare suggestion list, so
    # a reaggregation would lose every number unless the checkpoint carries it.
    # Collected for the failed slots too — `collect_usage` says why.
    usage = collect_usage(results)

    # D3b: a salvage task exists for every model whose output would not parse.
    # With --exec-subagents this run repairs them itself; a model whose result
    # file now exists is no longer failed, so the partial-results accounting
    # below sees the post-salvage truth rather than the pre-salvage one.
    if failed_models and exec_subagents_requested(args):
        # T5: salvage is the first stretch of the post-fan-out window and was
        # the one stretch nothing narrated. The fan-out's ticker is cancelled
        # and awaited by the time `run_all_models` returns (lifetime rule 1),
        # and the phase-scoped ticker below does not start until grouping — so
        # a salvage dispatch, which is a real subagent run and can last
        # minutes, sat between them emitting no `[PROGRESS]` line at all while
        # `progress.step` still read `fanout`. Both halves of the cure are the
        # ones the validation window already uses: publish the step *before*
        # the dispatch (so the ticker's lines and a `--poll` both name the
        # work, the way `dispatch_subagent_tasks` does it for `validating`),
        # and reach the dispatch through `asyncio.to_thread` — it ends in
        # `subagent_executor._run_sync`'s `pool.submit(asyncio.run, …).result()`
        # and would otherwise pin this loop and starve the ticker for the whole
        # window, which is exactly the F6 failure one stretch over.
        _detach.report_progress(phase_dir, step="salvage")
        salvage_ticker = PhaseProgress(phase_dir, anchor=plan_path)
        salvage_ticker.start_ticker()
        try:
            repaired = await asyncio.to_thread(
                dispatch_salvage_tasks,
                args,
                phase_dir=phase_dir,
                phase=phase_name,
                plan_path=plan_path,
            )
        finally:
            await salvage_ticker.stop_ticker()
        # Only a file this attempt's salvage dispatch names as repaired is a
        # recovery, as in `code_review_orchestrator`'s loop. The bare "the file
        # exists and is not empty" test adopted whatever was there: a failed
        # slot under `--force --rerun-all --exec-subagents` (the executor leg's
        # `--improve-plan --force` round) beside the previous round's
        # `{model}.json` printed "recovered by salvage", flipped the model done
        # and grouped, validated and applied round one's findings at exit 0
        # (Fable review 2026-10-09). The slot now sets that file aside
        # (`llm_client._set_aside_unchanged_result`); this is the second lock.
        repaired_paths = {os.path.abspath(path) for path in repaired or ()}
        salvaged: List[str] = []
        for model_spec in list(failed_models):
            recovered = os.path.join(
                phase_dir, f"{sanitize_model_name(model_spec)}.json"
            )
            if os.path.abspath(recovered) not in repaired_paths:
                continue
            if os.path.exists(recovered) and os.path.getsize(recovered) > 0:
                print(f"[{model_spec}] recovered by salvage: {recovered}")
                del failed_models[model_spec]
                salvaged.append(model_spec)
        # F3, 2026-09-20: the map has to move with `failed_models`. Deleting the
        # entry above is what makes the write below count this model as
        # completed and succeeded, and the per-model map — frozen `failed` by
        # the fan-out, and immune to a second `tracker.done()` because terminal
        # transitions are idempotent — said the opposite in the same file.
        if salvaged:
            record_models_salvaged(phase_dir, salvaged)

    # D6 row 3: partial results are usable output, so a run that lost *some*
    # models resumes-then-reaggregates (never a question, never `--rerun-all`)
    # and exits 0 with `state: "partial"`; a run where *no* model produced a
    # result has nothing to aggregate and is exit 3 naming the retry command.
    completed_models = [m for m in model_specs if m not in failed_models]
    if not completed_models:
        # The `models_served` write below is never reached on this exit, and a
        # run whose every slot was failed (the porcelain check on a bypassed
        # slot is one way) still ran those slots without a sandbox: the durable
        # record says so (2026-09-25), as `progress.sandbox_bypassed` already did.
        # The failure map is recorded too (plan
        # review-run-scope-salvage-and-failure-visibility, D5.2): a later
        # `--reaggregate` of this dir reads `models_failed` back to name each
        # loss and to exit 3 when every requested reviewer failed. Without it
        # that reaggregate would find no recorded failure and name the models
        # only with the "no result file" gap reason, at exit 0.
        update_status(phase_dir, {
            "models_completed": [],
            "models_failed": failed_models,
            **({"models_served": served_models} if served_models else {}),
        })
        print("\nERROR: All models failed")
        for model_spec, reason in failed_models.items():
            print(f"  - {model_spec}: {reason}")
        # The home check's and the jail's lines, repeated (F1, 2026-09-30):
        # this exit is the run's last word, so the summary goes here too.
        print_closing_summary(phase_dir)
        sys.exit(_unattended.report_partial_results(
            completed=completed_models,
            failed=list(failed_models),
            phase_dir=phase_dir,
            retry_command=cli_common.retry_command(
                _modes().mode_for_script(orchestrator_script) or phase_name,
                plan_path,
                "--force",
                flags=cli_common.current_replay_flags(
                    mode=_modes().mode_for_script(orchestrator_script) or phase_name
                ),
            ),
        ))
    _unattended.report_partial_results(
        completed=completed_models,
        failed=list(failed_models),
        phase_dir=phase_dir,
        unattended=unattended,
    )

    update_status(phase_dir, {
        "state": "models_complete",
        "models_completed": completed_models,
        "models_failed": failed_models,
        # Added only when something was attributed, so a default run's
        # `.status.json` gains no key.
        **({"models_served": served_models} if served_models else {}),
        # Same rule for what the fan-out spent: absent unless some adapter
        # reported it, so "no key" keeps meaning "nothing was reported" rather
        # than "this run was free".
        **({"usage": usage} if usage else {}),
    })
    # The restatement, and it writes **both** counters now. `models_done` keeps
    # the fan-out's meaning — finished slots, which after the sweep and the
    # backfill is every requested spec — while `models_succeeded` carries what
    # this site used to put under `models_done`: the models that actually
    # produced a result. A lossy run therefore ends on `8/8 done, 7 ok, 1
    # failed` rather than on the shrinking numerator `models 3/4`, which a live
    # progress line cannot use at all: under that meaning the counter walks
    # backwards at the end of a lossy run and can never reach `8/8`.
    succeeded = len(model_specs) - len(failed_models)
    _detach.report_progress(
        phase_dir,
        step="grouping",
        models_total=len(model_specs),
        models_done=len(model_specs),
        models_succeeded=succeeded,
    )

    # T5: the fan-out is not the phase. `run_models_concurrent` returned the
    # moment the last slot did — its ticker cancelled and awaited, its per-model
    # summary printed by the save loop above — and the phase now keeps working
    # for minutes: grouping, validation-batch preparation, and under
    # `--exec-subagents` the validation dispatch and merge in-process. That
    # window is where Claude Code goes silent again, at the END of the run
    # instead of throughout it. This second ticker covers it; lifetime rule 1
    # does not bend for it, which is why it starts here and not one line
    # earlier. The one stretch it does NOT cover is the in-process salvage
    # above, which runs before this point and carries its own instance of this
    # same ticker under `step: salvage`; the fan-out's ticker is already dead
    # by then, so rule 1 holds there too, and the two windows together leave
    # no unnarrated gap between the last model and the report.
    # It reads `progress.subagents` (the executor's own mirror) rather
    # than recomputing a second key, and it never touches `models`, so the
    # fan-out's terminal map stays frozen exactly as the sweep left it.
    #
    # **What it covers, exactly** (F6, 2026-09-20 — this comment used to claim
    # the whole dispatch and merge without qualification, and on the executor
    # lane it was covering neither): a ticker is a task on this loop, so it gets
    # a turn only where this stretch awaits. The long one, the batch dispatch,
    # does now — `dispatch_subagent_tasks` is blocking (it ends in
    # `_run_sync`'s `pool.submit(asyncio.run, …).result()`) and is therefore
    # awaited through `asyncio.to_thread` below, which is what lets the ticker
    # breathe for the minutes it runs. The synchronous stretches around it —
    # grouping, the excerpts, the merge — still pass unnarrated, and the
    # teardown line lands after them; that is a real limit, not something the
    # start-up `sleep(0)` below papers over.
    phase_ticker = PhaseProgress(phase_dir, anchor=plan_path)
    phase_ticker.start_ticker()
    # One yield, so the ticker task is really *entered* before the phase's
    # synchronous stretch begins. `ensure_future` only schedules it, and a
    # task cancelled before its first step never runs its body at all — so
    # without this a tail that happens to contain no `await` (the
    # host-driven `validation_pending` return is one) would emit no
    # `[PROGRESS]` line even at teardown, and the log's last such line would
    # be the fan-out's rather than the phase's terminal step.
    await asyncio.sleep(0)
    try:
        # Group similar suggestions
        all_suggestions = []
        for model_spec in model_specs:
            if model_spec in failed_models:
                continue
            sanitized_model = sanitize_model_name(model_spec)
            result_path = os.path.join(phase_dir, f"{sanitized_model}.json")
            if os.path.exists(result_path):
                try:
                    with open(result_path, 'r', encoding='utf-8') as f:
                        suggestions = drop_non_record_entries(
                            json.load(f), model_spec, noun="suggestions"
                        )
                        for s in suggestions:
                            s["source_model"] = model_spec
                        all_suggestions.extend(suggestions)
                except (json.JSONDecodeError, IOError):
                    pass

        validated_groups_for_report: Optional[List[Dict]] = None

        if all_suggestions:
            raw_grouped = group_similar_suggestions(all_suggestions)
            grouped = [g.to_dict() if hasattr(g, 'to_dict') else g for g in raw_grouped]
            stamp_stable_ids(grouped)
            grouped_path = os.path.join(phase_dir, "grouped.json")
            # D7: the previous run's verdicts belong to the grouping this write
            # replaces; retired in the same step so no later reaggregate finds them.
            # Round-wide when the grouping changed: a surviving
            # `validation_batch_<n>.json` of the previous grouping would be skipped
            # as "already complete" by the executor and then discarded by the merge
            # as a foreign group_hash (#25). `validation.json` alone when the hashes
            # are the same grouping, so a resume that skipped every model does not
            # re-run its completed batches (adversarial review, 2026-10-02).
            retire_validation_for_regroup(phase_dir, grouped, reason="grouped.json rewritten by a re-run")
            with open(grouped_path, 'w', encoding='utf-8') as f:
                json.dump(save_groups_payload(grouped), f, indent=2)
            print(f"Grouped suggestions saved to: {grouped_path}")

            update_status(phase_dir, {
                "state": "grouping_complete",
                "total_groups": len(grouped),
                "total_suggestions": len(all_suggestions),
            })

            # Validate grouped suggestions
            if not args.skip_validation:
                internal_validation = getattr(args, 'internal_validation', False)
                if internal_validation:
                    print("\nRunning internal validation...")
                    validation_timeout = args.timeout if args.timeout else 600
                    validation_results = await validate_groups(
                        [g.to_dict() if hasattr(g, 'to_dict') else g for g in grouped],
                        context=plan_content,
                        model=args.validation_model,
                        timeout=validation_timeout
                    )

                    validated_groups = apply_validation_to_groups(
                        [g.to_dict() if hasattr(g, 'to_dict') else g for g in grouped],
                        validation_results
                    )
                    validated_groups_for_report = validated_groups

                    validation_path = os.path.join(phase_dir, "validation.json")
                    save_validation_results(
                        validation_results, Path(validation_path),
                        # §7.1a: merged from no batch files, so bound to none — an
                        # empty binding, not the legacy mtime fallback.
                        batch_sha256={},
                    )
                else:
                    # Host-neutral: this print runs on every host that dispatches
                    # subagent validation (opencode, codex, claude-code, ...), and
                    # naming Claude Code here contradicted the runner the log
                    # names a few lines later (measured 2026-09-16: an
                    # opencode-driven run printed this beside 11 lines correctly
                    # naming opencode).
                    print("\nPreparing batched validation for subagent execution...")
                    extra_kwargs = {}
                    if extra_validation_metadata:
                        extra_kwargs = {k: v for k, v in extra_validation_metadata.items()
                                        if k in ("tasks_file",)}
                    batched_tasks = prepare_batched_validation_tasks(
                        groups=[g.to_dict() if hasattr(g, 'to_dict') else g for g in grouped],
                        output_dir=phase_dir,
                        plan_file=str(plan_path),
                        model=args.validation_model,
                        # The document's `reaggregate_mode` is what every later
                        # retry hint is rebuilt from (`resolved_reaggregate_command`),
                        # so it has to be THIS phase's script. Measured 2026-09-14
                        # on a `review-tasks` fan-out: the kwarg was missing, the
                        # helper defaulted to review-plan's script, and the exit-3
                        # block told the session model to re-invoke `review-plan
                        # --reaggregate` for a review-tasks run.
                        orchestrator=orchestrator_script,
                        **validation_context_kwargs(
                            phase_name, plan_content, extra_validation_metadata,
                            plan_document=plan_document, phase_dir=phase_dir,
                        ),
                        runner_read_refusal=materialization_read_refusal(
                            args, str(plan_path)
                        ),
                        phase=phase_name,
                        **extra_kwargs,
                    )
                    batched_tasks["format_version"] = CURRENT_FORMAT_VERSION

                    validation_tasks_path = os.path.join(phase_dir, "validation_tasks.json")
                    with open(validation_tasks_path, 'w', encoding='utf-8') as f:
                        json.dump(batched_tasks, f, indent=2)

                    # The phase machine's own word for this stretch — see the
                    # matching write on the reaggregate path.
                    update_status(phase_dir, {"state": "validation_pending"})

                    total_batches = batched_tasks["total_batches"]
                    stats = batched_tasks.get("batching_stats", {})

                    if total_batches == 1:
                        print(f"\n[VALIDATION_PENDING] {validation_tasks_path}")
                    else:
                        print(f"\n[VALIDATION_BATCHES_PENDING] {validation_tasks_path}")
                        print(f"Batches: {total_batches}")
                        if stats.get("efficiency_gain_percent", 0) > 0:
                            print(f"Efficiency gain: {stats['efficiency_gain_percent']}%")

                    print(f"\nValidation prepared for subagent execution.")
                    print(f"Groups to validate: {stats.get('total_groups', len(grouped))}")
                    print(f"HIGH priority groups: {stats.get('high_count', 0)}")
                    print(f"Normal priority groups: {stats.get('normal_count', 0)}")

                    # Resolved here, from the running skill dir, because the task
                    # file stores only the durable mode + plan pair (D1c).
                    reaggregate_cmd = resolved_reaggregate_command(batched_tasks)

                    # D3b: self-contained mode continues past the marker in this same
                    # process — dispatch, merge, and finish the phase in one
                    # invocation. Host-driven mode (the default) is unchanged below.
                    if await asyncio.to_thread(
                        dispatch_subagent_tasks,
                        args,
                        task_file=validation_tasks_path,
                        phase_dir=phase_dir,
                        phase=phase_name,
                        document=batched_tasks,
                        plan_path=str(plan_path),
                        label="validation",
                        retry_command=reaggregate_cmd,
                    ):
                        validation_path = os.path.join(phase_dir, "validation.json")
                        validated_groups_for_report = merge_validation_batches(
                            phase_dir, batched_tasks, grouped, validation_path
                        )
                    else:
                        # The plan as the user typed it (fix round 14).
                        reaggregate_cmd = resolved_reaggregate_command(
                            batched_tasks, typed_plan=True,
                        )
                        print("\nAfter validation completes, run:")
                        print(f"  {reaggregate_cmd or ''}")
                        record_next(reaggregate_cmd or None)

                        # The follow-up command is persisted in its **durable,
                        # rebindable** form (mode word + plan path) — in the task
                        # file above and here alike — never as the
                        # resolved skill-dir-absolute string the same run prints: the
                        # Claude plugin cache is keyed by commit hash, so a stored
                        # absolute command points at a directory that no longer
                        # exists after any plugin update. `status` (and
                        # utils/detach.resolved_reaggregate_command) rebuild it at
                        # read time from the *running* skill dir.
                        update_status(phase_dir, {
                            "state": "validation_pending",
                            "stdout_markers": ["VALIDATION_BATCHES_PENDING"] if total_batches > 1 else ["VALIDATION_PENDING"],
                            "validation_tasks_path": validation_tasks_path,
                            **durable_reaggregate_fields(orchestrator_script, plan_path),
                        })
                        _detach.report_progress(phase_dir, step="validation_pending")

                        return  # Exit early - Claude Code handles validation
            else:
                print("\nSkipping validation (--skip-validation flag set)")
        else:
            # Zero findings from every model that answered: a finished review
            # with zero groups, and it replaces the previous findings, as
            # code-review's own empty branch does (the `else` of its `if
            # all_issues:`). This block used to have no `else`, so the round
            # wrote neither file: apply-suggestions' `load_data` then exited 1
            # on the missing `validation.json` (measured 2026-10-08), stopping
            # `full` at exit 3 on a clean plan, and an empty `--force` round
            # left the previous round's two files in place, so the report
            # below listed its groups and apply-suggestions handed its valid
            # ones out again (plan improve-plan-and-improve-code §2.3, *Empty
            # apply outcomes*). The whole round retires, not only
            # `validation.json`: an empty grouping has no batch of its own to
            # keep. review-tasks shares this branch, and its zero-group
            # `grouped.json` is what `check_apply_task_suggestions_prerequisite`
            # reads as `skipped (no findings)`.
            validated_groups_for_report = []
            retire_stale_validation_round(
                phase_dir, reason="review returned no suggestions"
            )
            grouped_path = os.path.join(phase_dir, "grouped.json")
            with open(grouped_path, 'w', encoding='utf-8') as f:
                json.dump(save_groups_payload([]), f, indent=2)
            print(f"Grouped suggestions saved to: {grouped_path} (no suggestions)")
            with open(os.path.join(phase_dir, "validation.json"), 'w', encoding='utf-8') as f:
                f.write("[]\n")

        # Aggregate results
        report_path = aggregate_results(
            prefix, out_dir, phase_dir, phase_name,
            model_specs, failed_models, validated_groups_for_report,
            plan_path=plan_path,
            base_ref=base_ref,
            tasks_path=tasks_path,
            template_style=template_style,
            diff_data=diff_data,
            served_models=served_models or None,
            usage=usage or None,
            # Plan §5 T5.2: "N of M requested" counts this fan-out's own specs.
            requested_models=len(model_specs),
        )

        # Handle consolidation recommendation (only for phases that support it).
        # §7.2a: recomputed up *or down* by one helper, shared with the
        # reaggregate path, and run even for an empty round so a stale
        # recommendation is removed rather than left standing.
        recompute_consolidation_recommendation(
            phase_dir, validated_groups_for_report, args, supports_consolidation,
        )

        # Mark phase as completed
        state = get_or_create_state(Path(plan_path))
        state.mark_phase_completed(phase_name)
        state.save()

        # §Fix2: the phase machine's own terminal value. status_file.py's module
        # docstring names the sequence ``models_running`` →
        # ``models_complete``/``grouping_complete`` → ``validation_pending`` →
        # ``complete``, but nothing wrote the last link — the most recent `state`
        # this run recorded was whichever intermediate step it last passed
        # through (``grouping_complete``, or ``models_complete`` when there was
        # nothing to group), even on a run that reaches here, past a written
        # report and a completed phase. `run.state`/`progress.step` are the
        # *process*/*display* views this same module docstring distinguishes from
        # the phase machine; this is the third and last of the three. Nothing
        # gates resume or ``--reaggregate`` on this field (both key off artifact
        # existence and ``run.state`` — see ``reaggregate_from_existing_files`` and
        # AGENTS.md's D7 notes), so recording it here only fixes what a reader
        # (``status``, ``check_workflow_prerequisites``) reports for a finished run.
        update_status(phase_dir, {"state": "complete"})
        _detach.report_progress(phase_dir, step="complete")
    finally:
        # Cancelled AND awaited, so the last `[PROGRESS]` line lands before the
        # phase's own report rather than into the middle of it. It is stopped
        # *after* the terminal `progress.step` is written, which is what makes
        # that last line read `step: complete` instead of trailing off at
        # whatever step the last interval happened to catch. Two terminal steps
        # reach here, not one: the `complete` just above, and the
        # `validation_pending` early return, where the host-driven lanes hand
        # validation back to the agent and the process exits — stopping at the
        # second is not a gap,
        # because on Claude Code that return IS the background job's completion
        # signal.
        await phase_ticker.stop_ticker()
        # Plan codex-sandbox-unavailable F1 (2026-09-30): every
        # `[CODEX_HOME_CHECK]` and `[JAIL_DENIED]` line of this run's slots,
        # and the foreign trust tables that appear only here, repeated as the
        # run's last word — the home change outlives the run. On every ending
        # this `finally` covers: complete, validation handed back, exception.
        print_closing_summary(phase_dir)
