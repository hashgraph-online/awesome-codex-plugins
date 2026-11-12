#!/usr/bin/env python3
"""The Python-side subagent executor: `--exec-subagents` (D3, read/analyze half).

D2 materialized every subagent prompt into a task JSON; this module is the
*second* invoker of those tasks, next to a host's native subagent tool. Both run
the identical ``task.prompt`` and both land on the identical ``output_path`` file
(D3a), so a phase driven headlessly and a phase driven by Claude Code's Task tool
reaggregate byte-identical inputs.

One dispatch, in order:

1. **Refuse before spawning** — the D2 pre-dispatch refusals (``inline-json``,
   ``executor_role: human``, ``workspace-read`` against a runner that cannot read
   a workspace) plus the D3f containment check on ``output_name``. Nothing is
   started for a task that cannot legally produce a result.
2. **Pick a profile, never a raw command** (D3e) — every read/analyze kind runs
   under ``agent-readonly``, *derived from the task kind* so a materialized prompt
   (untrusted once it embeds plan text) can never request escalation, with ``cwd``
   pinned to the target repository.
3. **Capture, then parse through the adapter** (D3) — provider CLIs emit
   structured event streams, not plain text, so ``parse_output`` is mandatory
   rather than an optimization: running ``json_extractor`` over raw stdout would
   match an event envelope or a reasoning item and silently write a garbage
   result that reaggregation would accept.
4. **Validate, then write atomically** (D3f) — the extracted JSON is checked
   against its kind's result shape *before* anything is written, under the phase
   dir, 0600, via ``os.replace``.
5. **Classify every failure on exactly one rung** (D3k) and record it in
   ``subagent_batch_report.json`` plus ``.status.json``. A batch with any failed
   or incomplete task refuses to reaggregate and exits 3 — even under ``--yes``,
   and never by falling back to salvage.

The write path (``agent-write``, D3f/D3g/D3h/D3l/D3n) is deliberately not here:
:func:`profile_for_kind` and :func:`dispatch_task` are the seams it extends.

**A facade.** This module defines nothing of its own any more. The
executor's code lives in thirteen modules below it, lowest first:
``batch_reply``, ``failure_capture``, ``task_outcome``, ``task_result``,
``runner_selection``, ``probe_state``, ``sandbox_walk``,
``dispatch_spawn``, ``attempt_classifier``, ``runner_preflight``,
``task_dispatch``, ``task_batch`` and ``task_file_runner``
(docs/development/delegation.md#where-the-executors-helpers-live).
Every name that moved there is still readable here (:data:`_MOVED`), as is
the ``retry_ladder`` vocabulary, **for reading only**:
``subagent_executor.X`` and ``from .subagent_executor import X`` return the
owner's current object, but a patch or assignment here only shadows the
name in this module and reaches no code, because no code is left here to
read it. Patch a name in the module whose code reads it;
``tests/test_subagent_executor_moved_names.py`` fails any test that writes
a name here.
"""

from __future__ import annotations

import subprocess  # noqa: F401 - re-exported for readers of this module
from typing import (
    Any, Dict, List, Tuple,
)

from . import process_capture  # noqa: F401 - re-exported for readers of this module
from . import process_control  # noqa: F401 - re-exported for readers of this module
from .json_extractor import (
    extract_json_from_text,  # noqa: F401 - re-exported for readers of this module
)
from .llm_client import (
    expand_env_home,  # noqa: F401 - re-exported for readers of this module
)
from .provider_registry import (
    SESSION_LAYER,  # noqa: F401 - re-exported for readers of this module
)
from .providers.base import (
    PROFILE_AGENT_READONLY,  # noqa: F401 - re-exported for readers of this module
    PROFILE_AGENT_WRITE,  # noqa: F401 - re-exported for readers of this module
    ProfileUnsupported,
    version_verdict,  # noqa: F401 - re-exported for readers of this module
)
from .retry_ladder import (  # noqa: F401 - re-exported, see below
    BACKOFF_STATUSES,
    FATAL_STATUSES,
    MIN_ATTEMPT_BUDGET_S,
    RETRYABLE_STATUSES,
    RUNG_BY_STATUS,
    STATUS_AUTH_FAILED,
    STATUS_BUDGET_EXHAUSTED,
    STATUS_INCOMPLETE,
    STATUS_INCOMPLETE_REPORT,
    STATUS_INVALID_MODEL,
    STATUS_OK,
    STATUS_RATE_LIMITED,
    STATUS_REJECTED,
    STATUS_RUNNER_ERROR,
    STATUS_SALVAGE_UNRECOVERABLE,
    STATUS_SANDBOX_UNAVAILABLE,
    STATUS_SCHEMA_INVALID,
    STATUS_SPAWN_FAILED,
    STATUS_TIMEOUT,
    STATUS_UNPARSEABLE,
    STOP_BUDGET,
    STOP_DEADLINE,
    REPAIR_INCOMPLETE_REPORT,
    REPAIR_SCHEMA_INVALID,
    RESEND_NOTHING_CHANGED,
    RetryLadder,
    budget_exhausted_reason,
)
from .subagent_prompts import (
    build_schema_repair_prompt,  # noqa: F401 - re-exported for readers of this module
)
from .subagent_tasks import (
    KINDS,  # noqa: F401 - re-exported for callers that read it off this module
    WRITE_KINDS,  # noqa: F401 - re-exported for readers of this module
)
from . import known_checks as _known_checks  # noqa: F401 - `_MOVED` reads it
from . import batch_reply as _batch_reply  # noqa: F401 - `_MOVED` reads it
from . import failure_capture as _failure_capture  # noqa: F401 - `_MOVED` reads it
from . import task_outcome as _task_outcome  # noqa: F401 - `_MOVED` reads it
from . import task_result as _task_result  # noqa: F401 - `_MOVED` reads it
from . import runner_selection as _runner_selection  # noqa: F401 - `_MOVED` reads it
from . import probe_state as _probe_state  # noqa: F401 - `_MOVED` reads it
from . import sandbox_walk as _sandbox_walk  # noqa: F401 - `_MOVED` reads it
from . import dispatch_spawn as _dispatch_spawn  # noqa: F401 - `_MOVED` reads it
from . import attempt_classifier as _attempt_classifier  # noqa: F401 - `_MOVED` reads it
from . import runner_preflight as _runner_preflight  # noqa: F401 - `_MOVED` reads it
from . import task_dispatch as _task_dispatch  # noqa: F401 - `_MOVED` reads it
from . import task_batch as _task_batch  # noqa: F401 - `_MOVED` reads it
from . import task_file_runner as _task_file_runner  # noqa: F401 - `_MOVED` reads it


#: The status vocabulary, the D3k rung table, ``MIN_ATTEMPT_BUDGET_S`` and the
#: two policy frozensets (``RETRYABLE_STATUSES``, ``BACKOFF_STATUSES``,
#: ``FATAL_STATUSES``) are **defined in** :mod:`utils.retry_ladder` and imported
#: above. The ladder is their only consumer now that ``dispatch_task``'s retry
#: loop is one of its callers (§7.1.b), and a policy object that does not own its
#: own vocabulary is not a policy object. They are re-exported from here
#: unchanged, so every ``from utils.subagent_executor import STATUS_TIMEOUT``
#: in the tree keeps working exactly as it did.

#: ``STATUS_BUDGET_EXHAUSTED`` (§7.5 rule 4) is re-exported with them and is
#: deliberately **absent from** ``RUNG_BY_STATUS``: no child was spawned, so
#: there is no transport failure to put on a rung, and it is never retried (a
#: second admission test against a shorter budget has the same answer) and never
#: fatal to the batch (a sibling with a longer slot, or a runner with a smaller
#: declared envelope, is unaffected).


__all__ = [
    "BATCH_REPORT_FILENAME",
    "FAILED_CAPTURE_DIRNAME",
    "TASK_GENERATION_LIST_KEYS",
    "normalize_result",
    "MAX_RESULT_BYTES",
    "MAX_CAPTURE_BYTES",
    "STATUS_OK",
    "STATUS_TIMEOUT",
    "STATUS_RATE_LIMITED",
    "STATUS_RUNNER_ERROR",
    "STATUS_UNPARSEABLE",
    "STATUS_SCHEMA_INVALID",
    "STATUS_REJECTED",
    "STATUS_SPAWN_FAILED",
    "STATUS_AUTH_FAILED",
    "STATUS_INVALID_MODEL",
    "STATUS_SANDBOX_UNAVAILABLE",
    "STATUS_BUDGET_EXHAUSTED",
    "STATUS_INCOMPLETE",
    "STATUS_SALVAGE_UNRECOVERABLE",
    "STATUS_PARTIAL",
    "STATUS_POLICY_VIOLATION",
    "STATUS_BATCH_FAILED",
    "WRITE_APPLIED",
    "WRITE_CLEAN_FAILURE",
    "WRITE_NO_OP",
    "WRITE_PARTIAL",
    "WRITE_SCHEMA_REJECTED",
    "WRITE_POLICY_VIOLATION",
    "WRITE_STOP_OUTCOMES",
    "DeclinedItems",
    "declined_items",
    "declined_record",
    "row_declined",
    "RUNG_BY_STATUS",
    "RETRYABLE_STATUSES",
    "FATAL_STATUSES",
    "ExecutorError",
    "BatchFailed",
    "RunnerRejected",
    "ResultRejected",
    "ProfileUnsupported",
    "Attempt",
    "TaskOutcome",
    "BatchReport",
    "SCHEMA_PHASE_BY_KIND",
    "schema_phase_for_kind",
    "profile_for_kind",
    "resolve_task_runner",
    "resolve_output_target",
    "effective_ceiling",
    "extract_result",
    "validate_result",
    "persist_result",
    "task_is_complete",
    "dispatch_task",
    "run_tasks",
    "run_task_file",
    "continue_past_marker",
    "dry_run_report",
    "preflight_runner",
    "sandbox_rung",
    "write_rung_notice",
    "repo_wide_write_refusal",
    "jail_summary_count",
    "jail_summary_lines",
    "WRITE_SCOPE_BY_KIND",
    "RUNG_SKIPPED_BY_SWITCH",
    "SANDBOX_DECISION_WRITE_BY_CONSENT",
    "SandboxBackstopViolation",
]


# ---------------------------------------------------------------------------
# The names that moved to the modules beside this one
# ---------------------------------------------------------------------------

#: Every top-level name of the thirteen modules split out of this one, by
#: owner, the one constant ``known_checks`` owns now, and the kind table
#: ``runner_selection`` took beside its profile map. They are read-only
#: re-exports (see the module docstring): reading one here returns the owner's
#: current binding, and ``dir()`` lists them. Nothing is copied into this
#: module, so a patch of the owner shows through here.
_MOVED: Dict[str, Tuple[str, ...]] = {
    "known_checks": (
        "CHECK_FAILED_WITHOUT_FINDINGS",
    ),
    "batch_reply": (
        "BATCH_CHECK_COULD_NOT_RUN",
        "CHECK_FINDINGS_MAX",
        "CHECK_FINDING_MAX_CHARS",
        "CHECK_NOTE_MAX_CHARS",
        "CHECK_RESULT_UNKNOWN",
        "CheckReply",
        "DECLINED_REASON_MAX_CHARS",
        "DECLINED_SECTION_HEADING",
        "DeclinedItems",
        "SKIPPED_SECTION_HEADING",
        "WRITE_APPLIED",
        "WRITE_CLEAN_FAILURE",
        "WRITE_LABEL_CHECK_FINDINGS",
        "WRITE_LABEL_VERIFIED",
        "WRITE_NO_OP",
        "WRITE_PARTIAL",
        "WRITE_POLICY_VIOLATION",
        "WRITE_SCHEMA_REJECTED",
        "WRITE_STOP_OUTCOMES",
        "_CHECK_FAILED_WORDS",
        "_CHECK_PASSED_WORDS",
        "_EMPTY_FINDINGS_WORDS",
        "_RAN_COMMAND_KEYS",
        "_RAN_OUTCOME_KEYS",
        "_check_passed",
        "_finding_text",
        "_is_placeholder",
        "_names_a_command",
        "_ran_word",
        "_report_check_evidence",
        "_row_findings_by_check",
        "_says_nothing_found",
        "_stated_findings",
        "_with_ran_failures",
        "batch_check_could_not_run",
        "batch_check_findings",
        "batch_check_note",
        "batch_check_words",
        "check_findings_from",
        "check_record",
        "declined_items",
        "declined_reason",
        "declined_record",
        "ran_check_outcomes",
        "ran_no_check",
        "read_check_reply",
        "row_batch_check_accepted",
        "row_batch_check_findings",
        "row_batch_check_note",
        "row_batch_check_repeats",
        "row_check_findings",
        "row_declined",
        "row_outcome_label",
        "write_outcome_label",
    ),
    "failure_capture": (
        "FAILED_CAPTURE_DIRNAME",
        "MAX_CAPTURE_BYTES",
        "_atomic_write_json",
        "_redact_json",
        "_redact_probe_tail",
        "_retire_capture",
        "_safe_task_filename",
        "_tail",
        "_write_failure_capture",
    ),
    "task_outcome": (
        "Attempt",
        "BATCH_REPORT_FILENAME",
        "BatchFailed",
        "BatchReport",
        "ExecutorError",
        "KINDS_SHARING_A_WRITE_PHASE_DIR",
        "ResultRejected",
        "RunnerRejected",
        "TaskOutcome",
        "_batch_report_filename",
        "batch_report_path",
    ),
    "task_result": (
        "MAX_RESULT_BYTES",
        "MAX_STREAM_BYTES",
        "OBJECT_RESULT_KINDS",
        "OUTPUT_NAME_PATTERN_BY_KIND",
        "RESERVED_OUTPUT_NAMES",
        "RESERVED_OUTPUT_PREFIXES",
        "RESERVED_OUTPUT_SUFFIXES",
        "SALVAGE_EMPTY_AFTER_TIMEOUT_REASON",
        "SALVAGE_FAILED_KEY",
        "TASK_GENERATION_LIST_KEYS",
        "VERSIONED_RESULT_SCHEMAS",
        "_extract_result_and_syntax",
        "_is_unsafe_windows_path",
        "_report_normalized",
        "_result_names_foreign_groups",
        "_salvage_gave_up",
        "_salvage_result_errors",
        "_validation_result_errors",
        "complete_result_bytes",
        "extract_result",
        "normalize_result",
        "persist_result",
        "persist_result_bytes",
        "resolve_output_target",
        "salvage_failure_of",
        "supply_result_version",
        "task_is_complete",
        "the_reply_object",
        "validate_result",
    ),
    "runner_selection": (
        "PROFILE_BY_KIND",
        "WRITE_SCOPE_BY_KIND",
        "_REASON_EXPLANATION",
        "_RECORDED_RUNNER_SUFFIX",
        "_availability_detail",
        "_catalog_file_for_warning",
        "_effort_stripped",
        "_in_operator_roster",
        "_is_session_model",
        "_model_needs_credentials",
        "_registry_module",
        "_render_runner_rejection",
        "_resolve_task_source",
        "eligible_runners",
        "profile_for_kind",
        "resolve_task_runner",
        "resolve_task_runner_source",
    ),
    "probe_state": (
        "SANDBOX_DECISION_WRITE_BY_CONSENT",
        "SANDBOX_STATE_BYPASSED",
        "SandboxProbeResult",
        "_AUTH_CACHE",
        "_JAILED_CHILDREN",
        "_JAIL_SUMMARY_LINES",
        "_JAIL_SUMMARY_LOCK",
        "_MODEL_CACHE",
        "_NESTED_CACHE",
        "_PLAIN_SANDBOX_STATES",
        "_PROBE_VERSION_CACHE",
        "_PROBE_VERSION_LOCKS",
        "_RETIREMENTS_ANNOUNCED",
        "_SANDBOX_DECISIONS",
        "_SANDBOX_NOTICE_PARTS",
        "_SANDBOX_PROBE_CACHE",
        "_SANDBOX_PROBE_KEY_LOCKS",
        "_SANDBOX_PROBE_LOCK",
        "_VERSION_CACHE",
        "_current_host_id",
        "_host_nested_exec",
        "_record_jail_line",
        "_sandbox_decision_key",
        "_sandbox_probe_running",
        "_sandbox_state_word",
        "jail_summary_count",
        "jail_summary_lines",
        "reset_auth_cache",
        "reset_model_cache",
        "reset_nested_exec_cache",
        "reset_sandbox_cache",
        "reset_version_cache",
        "sandbox_bypassed",
        "sandbox_rung",
    ),
    "sandbox_walk": (
        "ADVISORY_PROBE_BUDGET_S",
        "F6_LEAD",
        "JAIL_KEPT_OFF_SENTENCE",
        "JAIL_SELF_TEST_SENTENCE",
        "JAIL_UNAVAILABLE_SENTENCE",
        "PROBE_WORKDIR_LOCK_PREFIX",
        "RUNG_ABSENT",
        "RUNG_REJECTED",
        "RUNG_RETIRED",
        "RUNG_SKIPPED",
        "RUNG_SKIPPED_BY_SWITCH",
        "RUNG_TAKEN",
        "RUNG_UNAVAILABLE",
        "RUNG_UNKNOWN",
        "RUNG_UNPROBED",
        "SANDBOX_PROBE_KILL_S",
        "SANDBOX_PROBE_TIMEOUT_S",
        "_announce_executor_retirements",
        "_detect_sandbox",
        "_f6_key",
        "_f6_lead",
        "_fallback_rungs",
        "_installed_cli_version",
        "_jail_rung",
        "_jail_rung_sentence",
        "_jail_versions_clause",
        "_ladder_has_removed_at",
        "_plugin_landlock_positive_exit",
        "_prepare_probe_workdir",
        "_probe_cwd",
        "_probe_workdir",
        "_probe_workdir_lock_path",
        "_remove_created_dirs",
        "_render_target",
        "_run_sandbox_probe",
        "_run_sandbox_probe_tree",
        "_rung_probe_tail",
        "_sandbox_cli_version",
        "_sandbox_fallback_policy",
        "_sandbox_probe_inconclusive",
        "_sandbox_probe_lock",
        "_sandbox_unavailable_rejection",
        "_scrub_probe_paths",
        "_uncontained_rung",
        "_walk_fallback_rungs",
        "_walk_wrapped_rung",
        "_write_consent_bypass_line",
        "cached_sandbox_verdict",
        "probe_budget_cut",
        "recorded_rung_retirements",
        "repo_wide_write_refusal",
        "rung_retirements",
        "sandbox_bypass_line",
        "sandbox_fallback_rung",
        "sandbox_verdict",
        "sandbox_walk_note",
        "write_rung_notice",
    ),
    "dispatch_spawn": (
        "SandboxBackstopViolation",
        "TIMEOUT_DRAIN_S",
        "TIMEOUT_KILL_GRACE_S",
        "_Capture",
        "_HELD_WHAT",
        "_JailSpawn",
        "_carries_full_access",
        "_context_read_dirs",
        "_decode",
        "_dispatch_grant",
        "_drain_after_kill",
        "_home_check_line",
        "_host_env_guards",
        "_jail_hook_context",
        "_jail_installed_version",
        "_kill_timed_out",
        "_missing_write_grant",
        "_note_runner_stop",
        "_preflight_version",
        "_read_jailed_outcome",
        "_record_held_pipe",
        "_report_jail_outcome",
        "_spawn",
        "_spawn_child",
        "_spawn_in_context",
        "_spawn_with_schema",
        "_stop_held_group",
        "_wrapping_rung",
        "audit_argv",
        "dispatch_child_env",
        "pipe_held_note",
        "render_audit_argv",
    ),
    "attempt_classifier": (
        "_VERDICT_QUOTE_CHARS",
        "_VERDICT_QUOTE_LEAD",
        "_classify_failed_run",
        "_classify_pre_parse",
        "_parse_and_validate",
        "_parse_with_schema_policy",
        "_quote_verdict",
        "_redact_tracking",
        "_reply_text",
        "_sandbox_hinted",
        "_unlowered_offset",
    ),
    "runner_preflight": (
        "NESTED_EXEC_FIELDS",
        "NESTED_PROBE_MARKER",
        "NESTED_PROBE_PROMPT",
        "NESTED_PROBE_TIMEOUT_S",
        "NETWORK_DENIAL_PATTERNS",
        "_CREDENTIAL_NAME",
        "_PROBE_ESCAPE",
        "_auth_cache_key",
        "_detect_auth",
        "_detect_model",
        "_detect_nested_exec",
        "_detect_version",
        "_dropped_credential_names",
        "_model_cache_key",
        "_probe_nested_exec",
        "_probe_verdict_stream",
        "_run_probe",
        "preflight_runner",
        "probe_setup_metadata",
    ),
    "task_dispatch": (
        "AttemptReading",
        "AttemptState",
        "DispatchHooks",
        "DispatchPlan",
        "HOOK_CONTEXT_KEYS",
        "NEXT_RETRY",
        "NEXT_STOP",
        "Next",
        "RECLASSIFIABLE_STATUSES",
        "RESENDS_BY_KIND",
        "Refusal",
        "RetryGuard",
        "SCHEMA_PHASE_BY_KIND",
        "SCHEMA_REPAIRS_BY_KIND",
        "STATUS_BATCH_FAILED",
        "STATUS_PARTIAL",
        "STATUS_POLICY_VIOLATION",
        "_PRIOR_CHANGES_TOKEN",
        "_accumulate_usage",
        "_apply_backoff_hook",
        "_ask_incomplete_report",
        "_ask_nothing_changed",
        "_ask_restate_findings",
        "_ask_write_hook",
        "_attempt_row",
        "_capture_attempt",
        "_denied_write_turn",
        "_incomplete_report_reask",
        "_moved_during_repair",
        "_never_started",
        "_note_held_pipe",
        "_nothing_changed_files",
        "_notify_after_attempt",
        "_prompt_over_budget",
        "_record_attempt",
        "_record_unspawned_attempt",
        "_safe_parse_usage",
        "_start_report_reask",
        "_start_resend",
        "_start_schema_repair",
        "_write_report_repairable",
        "admit_attempt",
        "ask_about_reply",
        "check_moved_before_retry",
        "close_outcome",
        "decide_next",
        "dispatch_task",
        "finish_ok",
        "hook_context",
        "merge_restated_check",
        "plan_dispatch",
        "read_attempt",
        "record_failed_attempt",
        "schema_phase_for_kind",
        "spawn_attempt",
    ),
    "task_batch": (
        "UNPINNED_ROW_STATUSES",
        "_ProviderBackpressure",
        "_STATUS_MIRROR_KEY",
        "_batch_provenance",
        "_dispatch_order",
        "_estimated_cost",
        "_gather",
        "_host_ceiling",
        "_judge_audit_before_attempt",
        "_judge_audit_completed",
        "_judge_dispatch_argv_preview",
        "_mirror_status",
        "_narrow_on_rate_limited_attempt",
        "_pin_sha256",
        "_pinned_runner_note",
        "_preflight_batch_runners",
        "_recorded_provenance",
        "_recorded_runners",
        "_run_sync",
        "_saw_rate_limit",
        "_unsettled_outcome",
        "effective_ceiling",
        "run_tasks",
    ),
    "task_file_runner": (
        "_INPUT_SOURCE_KEYS",
        "_artifacts_usable",
        "_force_variant",
        "_preview_argv",
        "_recomputed_inputs",
        "_retry_instruction",
        "_shaped_retry_block",
        "continue_past_marker",
        "dry_run_report",
        "run_task_file",
    ),
}
_MOVED_TO: Dict[str, str] = {
    name: module for module, names in _MOVED.items() for name in names
}


def __getattr__(name: str) -> Any:
    """A moved name, read from the module that defines it now."""
    owner = _MOVED_TO.get(name)
    if owner is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    try:
        return getattr(globals()[f"_{owner}"], name)
    except AttributeError:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from None


def __dir__() -> List[str]:
    """This module's own names and the moved ones it re-exports."""
    return sorted({*globals(), *_MOVED_TO})
