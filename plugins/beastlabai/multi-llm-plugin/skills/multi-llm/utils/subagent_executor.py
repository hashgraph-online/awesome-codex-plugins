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
"""

from __future__ import annotations

import asyncio
import contextlib
import copy
import hashlib
import inspect
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import (
    Any, Callable, Dict, Iterable, Iterator, List, Mapping, NamedTuple, Optional, Sequence,
    Set, Tuple,
)

try:  # pragma: no cover - import shim mirrors the rest of utils/
    from . import process_control
    from . import structured_output
    from .text_clip import clip
    from .json_extractor import (
        describe_syntax_error,
        extract_json_from_text,
        is_answer_shaped,
    )
    from .llm_client import (
        SALVAGE_FAILURE_KEY,
        SALVAGE_FAILURE_TIMEOUT,
        _CMD_UNSAFE_CHARS,
        _resolve_executable,
        expand_env_home,
        provider_dispatch_context,
    )
    from .provider_registry import (
        EXPLICIT_DRIVER_LAYERS,
        HOST_DEFAULT_LAYER,
        SESSION_LAYER,
        session_runner,
        get_max_concurrent_subagents,
        get_provider,
        get_provider_max_concurrent,
        get_subagent_retries,
        get_subagent_runner,
        get_subagent_timeout,
        is_model_valid,
        parse_model_spec,
        resolve_subagent_runner,
    )
    from . import landlock_dispatch
    from .providers.base import (
        CODEX_HOME_CHECK_MARKER,
        HOST_POSTURE_FULL_ACCESS,
        HOST_SANDBOX_POSTURE_ENV,
        INCIDENTAL_LANE_EXECUTOR,
        JAIL_DENIED_MARKER,
        JailContext,
        JailRequest,
        SANDBOX_WRITE_FALLBACK_PROFILES,
        SKIP_RUNG_ENV,
        WALK_OUTCOME_SKIPPED_BY_SWITCH,
        WRITE_SCOPE_PLAN_FILE,
        WRITE_SCOPE_REPO_WIDE,
        WRITE_SCOPE_TASKS,
        WRITE_SCOPES_BY_CONSENT,
        WRITE_SCOPES_ON_RUNG,
        WritePostureConsent,
        host_write_posture_consent,
        rung_is_incidental,
        sandbox_incidental_notice_text,
        skip_rung_requested,
        version_tuple,
        write_consent_allows,
        write_rung_allowed,
        LLMProvider,
        PROFILE_AGENT_READONLY,
        PROFILE_AGENT_WRITE,
        SANDBOX_BYPASSED_MARKER,
        SANDBOX_CANARY_DENIED,
        SANDBOX_CANARY_NOT_DENIED,
        SANDBOX_FALLBACK_AUTO,
        SANDBOX_FALLBACK_CONTAINED,
        SANDBOX_FALLBACK_OFF,
        SANDBOX_FALLBACK_PROFILES,
        SANDBOX_RUNG_UNSANDBOXED,
        ProfileUnsupported,
        SandboxRung,
        StructuredOutputUnavailable,
        availability_from_failure,
        sandbox_bypassed_notice_text,
        sandbox_fallback_notice_text,
        sandbox_rung_allowed,
        sandbox_rung_retired_notice,
        sandbox_walk_clause,
        rung_probe_said_removed,
        rung_removed_for_version,
        sandbox_rung_id,
        split_reasoning_effort,
        build_child_env,
        env_allowlist_enabled,
        matches_any,
        version_verdict,
        AUTH_STATE_CONFIG,
        CONFIG_AUTH_DECLARED,
        CONFIG_AUTH_UNKNOWN,
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
        build_nothing_changed_resend_prompt,
        build_schema_repair_prompt,
    )
    from .schema_validator import (
        validate_human_decision_verdicts,
        validate_with_schema_file,
    )
    from .subagent_tasks import (
        KINDS,  # noqa: F401 - re-exported for callers that read it off this module
        READ_KINDS,
        WRITE_KINDS,
        declared_file_set,
        preferred_prompt_transport,
        refuse_reason,
        tasks_of,
    )
except ImportError:  # pragma: no cover - direct-script import shim
    from utils import process_control
    from utils import structured_output
    from utils.text_clip import clip  # type: ignore
    from utils.json_extractor import (
        describe_syntax_error,
        extract_json_from_text,
        is_answer_shaped,
    )
    from utils.llm_client import (
        SALVAGE_FAILURE_KEY,
        SALVAGE_FAILURE_TIMEOUT,
        _CMD_UNSAFE_CHARS,
        _resolve_executable,
        expand_env_home,
        provider_dispatch_context,
    )
    from utils.provider_registry import (
        EXPLICIT_DRIVER_LAYERS,
        HOST_DEFAULT_LAYER,
        SESSION_LAYER,
        session_runner,
        get_max_concurrent_subagents,
        get_provider,
        get_provider_max_concurrent,
        get_subagent_retries,
        get_subagent_runner,
        get_subagent_timeout,
        is_model_valid,
        parse_model_spec,
        resolve_subagent_runner,
    )
    from utils import landlock_dispatch  # type: ignore[no-redef]
    from utils.providers.base import (
        CODEX_HOME_CHECK_MARKER,
        HOST_POSTURE_FULL_ACCESS,
        HOST_SANDBOX_POSTURE_ENV,
        INCIDENTAL_LANE_EXECUTOR,
        JAIL_DENIED_MARKER,
        JailContext,
        JailRequest,
        SANDBOX_WRITE_FALLBACK_PROFILES,
        SKIP_RUNG_ENV,
        WALK_OUTCOME_SKIPPED_BY_SWITCH,
        WRITE_SCOPE_PLAN_FILE,
        WRITE_SCOPE_REPO_WIDE,
        WRITE_SCOPE_TASKS,
        WRITE_SCOPES_BY_CONSENT,
        WRITE_SCOPES_ON_RUNG,
        WritePostureConsent,
        host_write_posture_consent,
        rung_is_incidental,
        sandbox_incidental_notice_text,
        skip_rung_requested,
        version_tuple,
        write_consent_allows,
        write_rung_allowed,
        LLMProvider,
        PROFILE_AGENT_READONLY,
        PROFILE_AGENT_WRITE,
        SANDBOX_BYPASSED_MARKER,
        SANDBOX_CANARY_DENIED,
        SANDBOX_CANARY_NOT_DENIED,
        SANDBOX_FALLBACK_AUTO,
        SANDBOX_FALLBACK_CONTAINED,
        SANDBOX_FALLBACK_OFF,
        SANDBOX_FALLBACK_PROFILES,
        SANDBOX_RUNG_UNSANDBOXED,
        ProfileUnsupported,
        SandboxRung,
        StructuredOutputUnavailable,
        availability_from_failure,
        sandbox_bypassed_notice_text,
        sandbox_fallback_notice_text,
        sandbox_rung_allowed,
        sandbox_rung_retired_notice,
        sandbox_walk_clause,
        rung_probe_said_removed,
        rung_removed_for_version,
        sandbox_rung_id,
        split_reasoning_effort,
        build_child_env,
        env_allowlist_enabled,
        matches_any,
        version_verdict,
        AUTH_STATE_CONFIG,
        CONFIG_AUTH_DECLARED,
        CONFIG_AUTH_UNKNOWN,
    )
    from utils.retry_ladder import (  # noqa: F401 - re-exported, see below
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
    from utils.subagent_prompts import (
        build_nothing_changed_resend_prompt,
        build_schema_repair_prompt,
    )
    from utils.schema_validator import (
        validate_human_decision_verdicts,
        validate_with_schema_file,
    )
    from utils.subagent_tasks import (
        KINDS,  # noqa: F401 - re-exported for callers that read it off this module
        READ_KINDS,
        WRITE_KINDS,
        declared_file_set,
        preferred_prompt_transport,
        refuse_reason,
        tasks_of,
    )


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
    "simulate_native_invoker",
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
# Constants
# ---------------------------------------------------------------------------

#: The executor-owned bookkeeping file beside the immutable task JSON (D3i).
#: The task file stays a hash-bound snapshot, so attempt counts live here.
BATCH_REPORT_FILENAME = "subagent_batch_report.json"

#: The one READ_KINDS member whose dispatch can land in a phase dir a WRITE_KINDS
#: dispatch also writes to (F6, 2026-09-16): every apply phase's unattended
#: judging pass runs on this, the read-path executor, *before* the same phase's
#: own write batches ever touch the dir. Every other read kind (validation,
#: revalidation, consolidation, salvage, task_generation) owns its phase dir
#: alone, so the bare name below is unambiguous for them and stays their
#: report's name. Without this, a judged decision — the one subagent output a
#: human is most likely to want to re-examine — had its report silently
#: overwritten the moment the write phase ran (both write to the identical
#: path), and its argv/duration/usage survived nowhere.
KINDS_SHARING_A_WRITE_PHASE_DIR = frozenset({"human_decision_judge"})


def _batch_report_filename(kind: str) -> str:
    """Which filename this ``kind``'s :class:`BatchReport` writes to (F6).

    Every kind but the one in :data:`KINDS_SHARING_A_WRITE_PHASE_DIR` keeps the
    bare :data:`BATCH_REPORT_FILENAME` — byte-identical for every existing
    reader (``run_status``, ``_authoritative_validator_runner``, the
    reaggregation-glob exclude lists, every test that opens the file by name).
    Only a kind that can share a phase dir with a different dispatch's report
    gets a name that says which report it is.
    """
    if kind in KINDS_SHARING_A_WRITE_PHASE_DIR:
        return f"subagent_batch_report_{kind}.json"
    return BATCH_REPORT_FILENAME


def batch_report_path(phase_dir: str, kind: str) -> str:
    """Where ``kind``'s batch report lives under ``phase_dir`` — the public form.

    The naming rule belongs to this module (F6, 2026-09-17), so a reader
    outside it asks rather than spelling a filename out: ``apply_orchestrator_
    base`` hands the judge's report to the host through ``output_files``, and a
    hand-typed copy of the name would drop that key silently the day the rule
    moves.
    """
    return os.path.join(phase_dir, _batch_report_filename(kind))


#: Per-attempt diagnostic captures (D3k). A directory, so the reaggregation glob
#: (``{phase_dir}/*.json``) never sees them.
FAILED_CAPTURE_DIRNAME = "failed"

#: Result size cap (D3f): reject rather than truncate, so a runaway or
#: adversarial runner cannot fill the disk through the executor.
MAX_RESULT_BYTES = 8 * 1024 * 1024

#: Per-stream diagnostic capture cap (D3k): last 64 KiB each of stdout/stderr.
MAX_CAPTURE_BYTES = 64 * 1024

#: Captured-stream cap. Beyond this the capture is refused (rung 5) rather than
#: half-parsed into a plausible-looking result.
MAX_STREAM_BYTES = 32 * 1024 * 1024

#: Grace between the SIGTERM and the SIGKILL of a timed-out dispatch's process
#: group (D3k rung 2). Short on purpose: the child has already spent its entire
#: ``subagent_timeout_s``, so this is teardown, not one more chance to finish.
TIMEOUT_KILL_GRACE_S = 0.5

#: Ceiling on the post-kill drain. A grandchild the kill did not reach still
#: holds the inherited stdout pipe, so the drain must be bounded — an unbounded
#: one is the hang that turns a timed-out task into a wedged batch.
TIMEOUT_DRAIN_S = 5.0

#: The status vocabulary, the D3k rung table, ``MIN_ATTEMPT_BUDGET_S`` and the
#: two policy frozensets (``RETRYABLE_STATUSES``, ``BACKOFF_STATUSES``,
#: ``FATAL_STATUSES``) are **defined in** :mod:`utils.retry_ladder` and imported
#: above. The ladder is their only consumer now that ``dispatch_task``'s retry
#: loop is one of its callers (§7.1.b), and a policy object that does not own its
#: own vocabulary is not a policy object. They are re-exported from here
#: unchanged, so every ``from utils.subagent_executor import STATUS_TIMEOUT``
#: in the tree keeps working exactly as it did.

#: The only statuses ``_classify_failed_run`` may reclassify (D3k). Rungs 4 and 5
#: mean "the run produced nothing usable", which is exactly the condition under
#: which a 429 or a login notice is the *real* explanation. Rung 6 is deliberately
#: absent: a ``schema_invalid`` result **parsed** — it is a deterministic
#: disagreement with the kind's result shape that is never retried — and its
#: streams carry the model's own prose, which routinely quotes "rate limit",
#: "429" or "unauthorized" straight out of the plan or diff under review. Matching
#: those substrings there would launder a schema disagreement into backoff retries
#: or, worse, into a batch-failing ``auth_failed``.
RECLASSIFIABLE_STATUSES = frozenset({STATUS_RUNNER_ERROR, STATUS_UNPARSEABLE})

#: ``STATUS_BUDGET_EXHAUSTED`` (§7.5 rule 4) is re-exported with them and is
#: deliberately **absent from** ``RUNG_BY_STATUS``: no child was spawned, so
#: there is no transport failure to put on a rung, and it is never retried (a
#: second admission test against a shorter budget has the same answer) and never
#: fatal to the batch (a sibling with a longer slot, or a runner with a smaller
#: declared envelope, is unaffected).
#:
#: Not a dispatch outcome either: the two D3g **verification** failures. They have
#: no D3k rung by design — the child ran, produced a schema-valid result and the
#: transport worked; what failed is the executor's own byte comparison, so
#: attaching a transport rung would be a category error (and would make a retry
#: look reasonable, which it never is for a half-applied file).
STATUS_PARTIAL = "partial_application"
STATUS_POLICY_VIOLATION = "policy_violation"
#: The third: the batch itself said ``failed`` (or its runner exited non-zero)
#: and the byte comparison agrees that nothing moved. Not ``ok`` — a runner that
#: reports it could not do the work has not done it, and continuing to the next
#: batch would build on the gap — and not retried either: the runner already
#: tried, and its own verdict, not a transport fault, is what is recorded.
#: Measured 2026-09-16: before this status a schema-valid ``{"status":
#: "failed"}`` with an empty diff was recorded as a *clean failure* with
#: ``status: ok``, the loop went on, and the phase completed at exit 0.
STATUS_BATCH_FAILED = "batch_failed"

#: Every read/analyze kind runs read-only; every write kind runs ``agent-write``.
#: Derived from the kind by the executor (D3e), never read from the task JSON —
#: which is the whole point: a materialized prompt embeds untrusted plan/diff text
#: and must not be able to request escalation.
PROFILE_BY_KIND = {
    **{kind: PROFILE_AGENT_READONLY for kind in READ_KINDS},
    **{kind: PROFILE_AGENT_WRITE for kind in WRITE_KINDS},
}

#: Every write kind maps to ``agent-write`` above, so the profile cannot tell a
#: plan edit from a code edit. The grant the plugin's Landlock jail gives a
#: write dispatch is therefore keyed by the KIND here, beside the profile map
#: and derived the same way — never read from the task JSON (plan
#: codex-sandbox-unavailable §6 F1 "How a dispatch receives its grant",
#: 2026-09-30). ``plan-file`` is one file rule on the plan, ``tasks`` the tasks
#: directory (or file); ``repo-wide`` (step 3b, 2026-10-02; one dir rule on
#: the repository root since 2026-10-05) the whole repository. A write kind
#: missing from this map is refused, never widened.
WRITE_SCOPE_BY_KIND = {
    "apply_suggestions": WRITE_SCOPE_PLAN_FILE,
    "apply_task_suggestions": WRITE_SCOPE_TASKS,
    "apply_code_fixes": WRITE_SCOPE_REPO_WIDE,
    "implement": WRITE_SCOPE_REPO_WIDE,
}

#: §4.2.2's phase → schema table is keyed by **phase**; a Lane B dispatch's
#: document contract is its **kind**. The two are not interchangeable here: the
#: ``code-review`` phase dispatches ``validation`` tasks whose result is a
#: validation batch, not the phase's ``code_review_issues`` array, so handing a
#: subagent the phase's schema would constrain it to a document it was never
#: asked for — and then validate its answer against a second, different file.
#:
#: So the phase is derived from the kind, and the table is exactly the
#: intersection where the kind's own result schema (``validate_result``) and
#: ``structured_output.PHASE_SCHEMA_FILE`` resolve to the **same file**:
#: ``task_generation`` → ``generated_tasks.schema.json`` and ``consolidation``
#: → ``consolidation_batch.schema.json``. That identity is what lets §4.2.1's
#: recovery branch stay this lane's own (see :func:`_parse_with_schema_policy`)
#: instead of validating the same document twice against two files, and it is
#: asserted functionally in ``tests/test_lane_b_structured_output.py`` rather
#: than trusted.
#:
#: Every other kind maps to nothing, which is the off switch: no phase, no
#: schema resolve, no flag, and an argv byte-identical to the pre-M7 lane. The
#: write kinds are absent for §4.2.1's own reason — their product is a file
#: diff, and ``PHASE_SCHEMA_FILE`` puts every apply/implement phase at ``None``.
#:
#: **W1 disposition: DEFER — repository owner, 2026-08-20.** Emptying this table
#: to ``{}`` remains the one-line switch that returns the lane to dormant, and
#: it stays a switch rather than becoming the setting: Lane A's own callers are
#: not wired because its six shipped documents are array-rooted and claude-code
#: cannot natively carry an array-rooted schema. Object-rooting those six files
#: is a contract change for every consumer of them, so the decision is the
#: repository owner's and it has not been made.
#: **Re-check trigger:** claude-code accepts an array-rooted ``--json-schema``.
#: **Re-read date:** 2027-02-20. See ``plans/harness-residual-work.md`` §3, W1.
SCHEMA_PHASE_BY_KIND = {
    "task_generation": "generate-tasks",
    "consolidation": "consolidation",
}


#: The ladder's rule 7, granted per kind: how many schema-repair re-asks a
#: ``schema_invalid`` attempt of that kind gets before rung 6 is terminal.
#:
#: * ``task_generation`` (2026-10-05): the one kind whose prompt is the *only*
#:   contract on a runner with no structured output (opencode declares none),
#:   and the one whose rung-6 failure dead-ends a whole phase — measured
#:   2026-10-04, ``opencode/big-pickle`` answered the wrong shape twice and
#:   generate-tasks exited 3 both times.
#: * the three apply kinds (2026-10-05, run 3): one big-pickle apply batch's
#:   report was unreadable and the whole phase stopped at exit 3 until a
#:   ``--resume`` re-ran the batch. A write kind's reply is the report of edits
#:   already on disk, so its re-ask is a different question
#:   (``subagent_prompts.build_schema_repair_prompt``'s write form): the
#:   original prompt is not re-sent, the runner restates its own previous
#:   reply without touching a file, and the dispatch fails as a partial
#:   application if any file moved during it (``tree_fingerprint``).
#: * ``implement`` (fix round 14, OpenCode racing run 5): T013 edited
#:   ``index.html`` for 442 s, replied in prose ("No valid JSON found in
#:   text"), and the stop called a finished edit a partial application. The
#:   same report re-ask, with the same guards: it restates the report and
#:   edits nothing, a file it moves makes the dispatch a partial application,
#:   and the byte comparison still decides what was applied.
#:
#: Validation and consolidation keep rung 6 terminal: a batch is one of many
#: and fails alone. A kind listed here must have a shape in
#: ``subagent_prompts.SCHEMA_REPAIR_SHAPES``.
SCHEMA_REPAIRS_BY_KIND = {
    "task_generation": 1,
    "apply_suggestions": 1,
    "apply_task_suggestions": 1,
    "apply_code_fixes": 1,
    "implement": 1,
}


def schema_phase_for_kind(kind: str) -> Optional[str]:
    """The §4.2.2 phase whose schema governs ``kind``'s result, or ``None``."""
    return SCHEMA_PHASE_BY_KIND.get(kind)


#: The ladder's rule 9, granted per kind: how many times a write batch whose
#: reply said ``applied`` while not one byte moved is sent again, told so,
#: before it is recorded failed (fix round 14, OpenCode racing run 5: T016
#: said ``applied`` and named ``index.html``, the file was unchanged, and the
#: task was recorded completed). Every write kind, because the classification
#: is shared; the scheduler's ``nothing_changed`` hook is what decides an
#: attempt qualifies (never a check task, which changes nothing by design).
RESENDS_BY_KIND = {
    "apply_suggestions": 1,
    "apply_task_suggestions": 1,
    "apply_code_fixes": 1,
    "implement": 1,
}

#: The four D3g write outcomes, plus the D3l containment failure. Recorded on the
#: outcome as its own axis rather than being folded into ``status``. "Applied"
#: and "no-op" are dispatches the loop continues past; "clean failure" (nothing
#: moved and the work is not done: a ``failed`` claim, a crash, or — since fix
#: round 14 — an ``applied`` claim no byte backs, after its one re-send) is
#: never ``ok``, and "partial application" and "policy violation" stop it too.
WRITE_APPLIED = "applied"
WRITE_CLEAN_FAILURE = "clean-failure"
#: The runner said ``no-op`` and the byte comparison agrees. Its own outcome
#: rather than a clean failure, because the claim and the verdict AGREE: a
#: clean failure is *success* claimed with nothing moved, and labelling an
#: honest "already present" batch ``(batch failed — …)`` in the prior-changes
#: log and the summary table told the next batch, and the reader, that the
#: work had failed. Measured 2026-09-16 on two verification-only tasks.
WRITE_NO_OP = "no-op"
#: What a verification-only ``implement`` task (one declaring no files) reads as
#: when nothing moved: the check ran and left the repository as it was. A
#: *label*, never a ``write_outcome`` value — the outcome stays ``no-op``, which
#: resume, ``util restore-batch`` and every older reader key on — so it rides
#: beside it as ``outcome_label`` (2026-10-04: the reason said VERIFIED while the
#: summary cell, the batch log line, the status breakdown and both reports said
#: ``no-op``). A verification-only task that moved bytes reads
#: ``partial-application`` like any other partial, so the pair is VERIFIED or
#: PARTIAL on every surface.
WRITE_LABEL_VERIFIED = "verified"
#: A verification-only task whose check ran, changed nothing and reported
#: problems in its reply's structured ``check`` object (``passed: false`` or a
#: non-empty ``findings`` list). Never ``verified``: racing re-run 4
#: (2026-10-05) recorded T007 VERIFIED while ``npx html-validate`` had reported
#: two problems that lived only in the runner's free-text notes. Not a stop
#: either: what a check finds is a finding, never an exit code (AGENTS.md), and
#: review-code / apply-code-fixes are the phases that fix it — so the tasks
#: that do not depend on the check go on, ``write_outcome`` stays ``no-op``
#: and every surface names the findings. The tasks that DO depend on it are
#: not run (fix round 11): ``WriteBatchScheduler`` records them ``not run —
#: upstream check … reported problems`` and implement ends needing a human.
WRITE_LABEL_CHECK_FINDINGS = "check-findings"
WRITE_PARTIAL = "partial-application"

#: Bounds on what one check reply's ``findings`` may put on the surfaces
#: (summary.md, the reports, state.json, review-code's prompts).
CHECK_FINDINGS_MAX = 20
CHECK_FINDING_MAX_CHARS = 300

#: The finding recorded for a ``check`` that said it did not pass and listed
#: no finding, so the task still reads as one with findings.
CHECK_FAILED_WITHOUT_FINDINGS = (
    "the check reported that it did not pass but listed no finding; "
    "see the runner notes"
)

#: The finding recorded for a ``check`` that says neither that it passed nor
#: what it found (``{}``, ``{"passed": null, "findings": []}``): an unknown
#: result is never a pass (fix round 11 — ``check: {}`` used to read VERIFIED).
CHECK_RESULT_UNKNOWN = (
    "the check's reply did not say whether it passed (its `check` object had "
    "no usable `passed` value and no findings); see the runner notes"
)

#: The words ``check.passed`` (and ``check.could_not_run``) may be spelled
#: in, besides the JSON booleans (a near-miss reply: ``"false"``, ``0``, and
#: since fix round 13 the strings ``"1"``/``"0"``, which read as the numbers
#: do). Anything else is an unknown result.
_CHECK_PASSED_WORDS = frozenset({"true", "yes", "pass", "passed", "1"})
_CHECK_FAILED_WORDS = frozenset({"false", "no", "fail", "failed", "0"})

#: A bare ``findings`` value that says "nothing found" (any case, a trailing
#: ``.``/``!`` ignored), read as ``[]`` only beside a ``passed`` that reads
#: true (fix round 12: ``{"passed": true, "findings": "none"}`` was one
#: finding, "none", which held back every task after the check). Kept
#: short on purpose: any other text is a finding.
_EMPTY_FINDINGS_WORDS = frozenset({
    "", "none", "n/a", "na", "no problems", "no problems found", "no findings", "0",
})


def _says_nothing_found(value: Any) -> bool:
    """Whether a bare (non-list) ``findings`` value is an empty-ish marker."""
    if isinstance(value, bool):
        return False
    if isinstance(value, (int, float)):
        return value == 0
    if isinstance(value, str):
        word = " ".join(value.strip().lower().rstrip(".!").split())
        return word in _EMPTY_FINDINGS_WORDS
    return False


def write_outcome_label(
    write_outcome: Optional[str], verification_only: bool = False,
    check_findings: Optional[Sequence[str]] = None,
) -> Optional[str]:
    """The word every report shows for a write outcome (:data:`WRITE_LABEL_VERIFIED`)."""
    if verification_only and write_outcome == WRITE_NO_OP:
        return WRITE_LABEL_CHECK_FINDINGS if check_findings else WRITE_LABEL_VERIFIED
    return write_outcome


def _check_passed(value: Any) -> Optional[bool]:
    """``check.passed`` read leniently: ``True``/``False``, else ``None``.

    The JSON booleans, ``1``/``0`` (numbers or strings) and the words in
    :data:`_CHECK_PASSED_WORDS` / :data:`_CHECK_FAILED_WORDS` (any case);
    anything else (``null``, a missing key, ``"maybe"``) is unknown.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and value in (0, 1):
        return bool(value)
    if isinstance(value, str):
        word = value.strip().lower()
        if word in _CHECK_PASSED_WORDS:
            return True
        if word in _CHECK_FAILED_WORDS:
            return False
    return None


def _finding_text(item: Any) -> str:
    """One finding as one line: an object is read as its non-empty values."""
    if item is None:
        return ""
    if isinstance(item, dict):
        # An object per finding (`{"command": …, "message": …}`) is read as
        # its values, so a near-miss shape still names the problem.
        item = "; ".join(
            f"{key}: {value}" for key, value in item.items()
            if value not in (None, "", [], {})
        )
    return " ".join(str(item).split())


class CheckReply(NamedTuple):
    """What a check task's reply says in its ``check`` object.

    ``findings`` is :func:`check_findings_from`'s answer. ``listed`` is
    whether the reply listed at least one finding of its own (not one this
    reader supplied: :data:`CHECK_FAILED_WITHOUT_FINDINGS`,
    :data:`CHECK_RESULT_UNKNOWN`). ``could_not_run`` is ``check.could_not_run``
    read as leniently as ``passed`` (``true``, ``1``, ``"1"``,
    ``"true"``/``"yes"``; :func:`_check_passed`): the runner says
    a check could not run (fix round 12).
    """

    findings: Optional[List[str]]
    listed: bool
    could_not_run: bool


def read_check_reply(result: Any) -> CheckReply:
    """The reply's ``check`` object, read (:class:`CheckReply`).

    Fix round 12 (a coordinator decision after racing run 3: real runners
    answer ``failed`` for a check that ran and found problems): a check
    that could not run says so with ``check.could_not_run: true``, and only
    that, or a crash, is a check that did not run. ``_verification_verdict``
    reads a ``failed`` reply whose ``check`` lists findings, and does not
    say it could not run, as findings.
    """
    findings = check_findings_from(result)
    check = result.get("check") if isinstance(result, dict) else None
    if not isinstance(check, dict):
        return CheckReply(findings, False, False)
    could_not_run = _check_passed(check.get("could_not_run")) is True
    listed = bool(findings) and findings[0] not in (
        CHECK_FAILED_WITHOUT_FINDINGS, CHECK_RESULT_UNKNOWN,
    )
    return CheckReply(findings, listed, could_not_run)


def check_findings_from(result: Any) -> Optional[List[str]]:
    """The structured check result of a write reply, as a findings list.

    ``None`` when the reply carries no ``check`` key at all (an older reply,
    a task that is not a check); ``[]`` when it says the check passed and
    lists nothing; otherwise the findings, one line each
    and bounded (:data:`CHECK_FINDINGS_MAX`, :data:`CHECK_FINDING_MAX_CHARS`).
    Read from the reply's own field, never from its notes.

    Lenient on shape, strict on meaning (fix round 11). The schema admits
    any ``check``, because a near-miss shape (``passed: "false"``,
    ``findings: "one problem"``, a number as a finding) used to be a
    ``schema_invalid`` reply, and implement had no report re-ask then, so the
    run stopped for good on a check that had answered (it has one since fix
    round 14; the lenient reading stays, so a near-miss costs no re-ask).
    Each shape is read here
    instead, and only a clear pass with nothing listed is a pass: a finding
    beside ``passed: true`` still counts, ``passed: false`` with none listed
    gets :data:`CHECK_FAILED_WITHOUT_FINDINGS`, and a ``check`` that says
    neither (``{}``, ``passed: null``, ``check: null``, a ``check`` that is
    not an object) gets :data:`CHECK_RESULT_UNKNOWN` — never a pass. Fix
    round 12: ``check: null`` read as no result, so a check task's reply
    carrying it was VERIFIED; only a missing key is no result now. A bare
    ``findings`` that says "nothing found" (``"none"``, ``"N/A"``, ``"No
    problems found."``, ``0``) beside a ``passed`` that reads true is
    ``[]`` (:data:`_EMPTY_FINDINGS_WORDS`).
    """
    if not isinstance(result, dict) or "check" not in result:
        return None
    check = result.get("check")
    if check is None:
        return [f"{CHECK_RESULT_UNKNOWN} (its `check` was null)"]
    if not isinstance(check, dict):
        shown = clip(check, 80)
        return [
            f"{CHECK_RESULT_UNKNOWN} (its `check` was "
            f"{type(check).__name__} {shown!r}, not an object)"
        ]
    raw = check.get("findings")
    passed = _check_passed(check.get("passed"))
    if isinstance(raw, list):
        items = raw
    elif raw is None:
        items = []
    elif passed is True and _says_nothing_found(raw):
        # "findings": "none" beside a pass says there is none (fix round 12).
        items = []
    else:
        # One finding given bare (a string, an object, a number).
        items = [raw]
    findings = []
    for item in items:
        text = _finding_text(item)
        if text:
            findings.append(clip(text, CHECK_FINDING_MAX_CHARS))
    if len(findings) > CHECK_FINDINGS_MAX:
        extra = len(findings) - (CHECK_FINDINGS_MAX - 1)
        findings = findings[:CHECK_FINDINGS_MAX - 1] + [
            f"(+{extra} more finding(s) in the batch result file)"
        ]
    if findings:
        return findings
    if passed is True:
        return []
    if passed is False:
        return [CHECK_FAILED_WITHOUT_FINDINGS]
    return [CHECK_RESULT_UNKNOWN]


#: The finding a code batch's own check carries when its reply said
#: ``check.could_not_run`` (fix round 15): every surface then says "its check
#: could not run", never that it fails.
BATCH_CHECK_COULD_NOT_RUN = "its check could not run"


def batch_check_could_not_run(findings: Optional[Sequence[str]]) -> bool:
    """Whether a code batch's own-check findings say the check could not run."""
    return bool(findings) and str(findings[0]).startswith(BATCH_CHECK_COULD_NOT_RUN)


def batch_check_words(findings: Optional[Sequence[str]]) -> str:
    """How a surface names a code batch's own check that did not pass:
    "its check could not run", else "a check it ran fails"."""
    return (
        BATCH_CHECK_COULD_NOT_RUN if batch_check_could_not_run(findings)
        else "a check it ran fails"
    )


def batch_check_findings(result: Any) -> Optional[List[str]]:
    """What a code-writing batch's own ``check`` object says about the checks
    it ran on its edits (fix round 14).

    ``None`` when the reply reports no usable check — no ``check`` key, one
    that says neither whether it passed nor what failed (``{}``, ``null``), or
    (fix round 26) one whose ``ran`` is empty, the contract's way of saying no
    check ran (:func:`ran_no_check`), and that names no finding and does not
    say it failed (fix round 27): saying nothing is not a finding here, as
    it is for a check task, whose whole answer it is. A command ``ran`` maps
    to ``failed`` is a failing check whatever ``passed`` says
    (:func:`ran_check_outcomes`). ``[]`` for a clear pass; else the failing checks, bounded. Codex
    racing run 5 (2026-10-06): an apply-code-fixes batch wrote "the bundled
    test fails" in its free-text ``notes``, the repository's test failed
    afterwards, and the run reported every fix applied. Never read from
    ``notes``.

    Not the check task's fail-closed reading (fix round 15, review of round
    14): a check task's ``check`` is its whole verdict, so a finding beside
    ``passed: true`` counts there; here ``passed: true`` is the batch's own
    word that its checks passed, and what it lists beside it ("npm test: 12
    passed") is informational, never a failing check. ``could_not_run``
    (read as leniently as ``passed``) is one finding,
    :data:`BATCH_CHECK_COULD_NOT_RUN` with whatever the reply listed after
    it, so it reads "its check could not run", never "fails".

    Fix round 27 (review of round 26): one rule on both legs, the one
    ``references/own-check.md`` states for the native host's ``util
    batch-done --own-check``, first match wins: no ``check`` object is no
    check; ``could_not_run`` is that; a reply that ran nothing
    (:func:`ran_no_check`) is failing when it names a finding, whatever
    ``passed`` says (a pass of nothing is no verdict), or says ``passed:
    false`` (:data:`CHECK_FAILED_WITHOUT_FINDINGS` kept), and no check
    otherwise (a ``not_run`` reason with no ``ran`` ran nothing too); any other reply is a pass on ``passed: true`` (fix round 15,
    a command ``ran`` maps to ``failed`` aside), failing on ``passed:
    false`` or a finding, a pass when only ``ran`` says what passed, and no
    check when it says nothing at all.
    """
    check = result.get("check") if isinstance(result, dict) else None
    if not isinstance(check, dict):
        # No `check` key, `null`, or not an object: no usable report.
        return None
    stated = _stated_findings(check)
    if _check_passed(check.get("could_not_run")) is True:
        text = BATCH_CHECK_COULD_NOT_RUN + (
            f": {'; '.join(stated)}" if stated else ""
        )
        return [clip(text, CHECK_FINDING_MAX_CHARS)]
    passed = _check_passed(check.get("passed"))
    if ran_no_check(result):
        # It ran nothing (an empty `ran`, every entry "not run", or only the
        # result shape's placeholder): its `passed: true` is a pass of
        # nothing, so a failure it names counts and nothing else is a pass;
        # a `passed: false` is a failing check (fix round 27: round 26 made
        # it "no check", where it had been CHECK_FAILED_WITHOUT_FINDINGS).
        if stated:
            return stated
        return [CHECK_FAILED_WITHOUT_FINDINGS] if passed is False else None
    ran = ran_check_outcomes(result)
    if passed is True:
        # Fix round 15: what it lists beside a pass is informational.
        return _with_ran_failures([], ran)
    if passed is False:
        return _with_ran_failures(stated or [CHECK_FAILED_WITHOUT_FINDINGS], ran)
    if stated:
        return _with_ran_failures(stated, ran)
    # It says neither: `ran` alone says how its checks ended, if anything.
    if any(word == _ran_word("failed") for word in ran.values()):
        return _with_ran_failures([], ran)
    if any(word == _ran_word("passed") for word in ran.values()):
        return []
    return None


#: How much of a code batch's ``check.note`` the records carry (fix round 28).
CHECK_NOTE_MAX_CHARS = 300


def batch_check_note(result: Any) -> Optional[str]:
    """A code batch's ``check.note``: its own words about the checks it ran,
    one plain line bounded at :data:`CHECK_NOTE_MAX_CHARS`, or ``None``.

    Fix round 28 (live run 12, stop accept 02 on Claude Code and OpenCode):
    T007 re-ran the check the user accepted and wrote its comment into the
    finding ("… (known problem the user accepted in T002)", "… — the
    accepted T002 problem (…), not caused by this note"), and the strict
    match read the finding as T007's own failure. The contract asks for
    each finding as the check reported it and for any comment here instead
    (:data:`write_batch_scheduler.WRITE_CHECK_CONTRACT`). Recorded and shown
    beside the check on both legs (``util batch-done --note``); never read
    as a finding and never matched on."""
    check = result.get("check") if isinstance(result, dict) else None
    if not isinstance(check, dict):
        return None
    note = check.get("note")
    if not isinstance(note, str):
        return None
    return clip(note, CHECK_NOTE_MAX_CHARS) or None


def _ran_word(which: str) -> str:
    """``known_checks``' ``passed`` / ``failed`` outcome word."""
    try:
        from .known_checks import LISTED_FAILED, LISTED_PASSED
    except ImportError:  # pragma: no cover - direct script import shim
        from utils.known_checks import LISTED_FAILED, LISTED_PASSED
    return LISTED_FAILED if which == "failed" else LISTED_PASSED


def _stated_findings(check: Dict[str, Any]) -> List[str]:
    """The findings a ``check`` object names itself, bounded, without the
    placeholders :func:`check_findings_from` puts in for none. Beside a
    ``passed`` that reads true, an entry that only says nothing was found
    (``"none"``, ``"n/a"``, ``0``) is no finding either (fix round 12's
    reading of a bare one, which fix round 27 extends to a list entry, so
    ``["n/a"]`` beside a ``passed: true`` that ran nothing is no check, not
    a failing one); beside any other ``passed`` it stays one, as before."""
    raw = check.get("findings")
    if _check_passed(check.get("passed")) is True:
        if isinstance(raw, list):
            raw = [item for item in raw if not _says_nothing_found(item)]
        elif _says_nothing_found(raw):
            raw = None
    return [
        text for text in (check_findings_from(
            {"check": {"passed": False, "findings": raw}}
        ) or [])
        if text not in (CHECK_FAILED_WITHOUT_FINDINGS, CHECK_RESULT_UNKNOWN)
    ]


def ran_check_outcomes(result: Any) -> Dict[str, str]:
    """``{command: passed|failed|not run}`` from a code batch's ``check.ran``
    (fix round 26): the commands it says it ran, read as leniently as an
    apply-code-fixes batch's ``listed`` (``known_checks.listed_check_outcomes``).

    The contract asks for a map; a list of ``"<command>: <outcome>"`` strings
    is read too. An entry that cannot be read is left out, never guessed.
    """
    check = result.get("check") if isinstance(result, dict) else None
    ran = check.get("ran") if isinstance(check, dict) else None
    if isinstance(ran, list):
        pairs: Dict[str, Any] = {}
        for item in ran:
            if isinstance(item, str):
                command, sep, word = item.rpartition(":")
                if sep and command.strip():
                    pairs[command] = word
            elif isinstance(item, dict):
                # `{"command": …, "outcome": …}` per check, a near miss.
                command = next((item[k] for k in _RAN_COMMAND_KEYS if k in item), None)
                word = next((item[k] for k in _RAN_OUTCOME_KEYS if k in item), None)
                if isinstance(command, str) and command.strip():
                    pairs[command] = word
        ran = pairs
    if not isinstance(ran, dict) or not ran:
        return {}
    try:
        from .known_checks import listed_check_outcomes
    except ImportError:  # pragma: no cover - direct script import shim
        from utils.known_checks import listed_check_outcomes
    return {
        command: word for command, word in listed_check_outcomes(ran).items()
        if not _is_placeholder(command)
    }


#: The keys a ``ran`` entry written as an object names its command and its
#: outcome under (fix round 26), first found wins.
_RAN_COMMAND_KEYS = ("command", "cmd", "check", "name")
_RAN_OUTCOME_KEYS = ("outcome", "result", "status", "passed")


def _is_placeholder(command: str) -> bool:
    """Whether a ``ran`` key is the contract's own placeholder copied as it
    is (``<each check command you ran>``): it names no command."""
    text = command.strip()
    return len(text) > 1 and text[0] == "<" and text[-1] == ">"


def _names_a_command(entry: Any) -> bool:
    """Whether one entry of a ``ran`` list may name a command it ran: not the
    contract's placeholder, whether written as a ``"<command>: <outcome>"``
    string or (fix round 27, review of round 26: it read as a clean pass) as
    an object whose command is the placeholder. An entry that cannot be read
    counts, so what ran stays unknown rather than nothing."""
    if isinstance(entry, str):
        return not _is_placeholder(entry.rpartition(":")[0] or entry)
    if isinstance(entry, dict):
        command = next((entry[k] for k in _RAN_COMMAND_KEYS if k in entry), None)
        return not (isinstance(command, str) and _is_placeholder(command))
    return True


def ran_no_check(result: Any) -> bool:
    """Whether a code batch's ``check`` says it ran no check (fix round 26):
    its ``ran`` is present and empty, holds only the contract's placeholder,
    or every entry in it reads ``not run`` — or (fix round 27) it has no
    ``ran`` at all but gives a ``not_run`` reason, the contract's other half
    of "I ran no check", so ``{"passed": true, "not_run": "…"}`` is never a
    pass of nothing.

    A missing ``ran`` with no ``not_run`` reason is not this (an older reply,
    read as before), and neither is a ``ran`` holding an entry that cannot be
    read: what it ran is then unknown, and ``passed``/``findings`` decide.
    """
    check = result.get("check") if isinstance(result, dict) else None
    ran = check.get("ran") if isinstance(check, dict) else None
    if ran is None and isinstance(check, dict):
        reason = check.get("not_run")
        return isinstance(reason, str) and bool(reason.strip())
    if not isinstance(ran, (dict, list)):
        return False
    # The contract's placeholder copied as it is names no command (a reply
    # that pasted the shape without running anything).
    named = [
        entry for entry in ran if _names_a_command(entry)
    ] if isinstance(ran, list) else [key for key in ran if not _is_placeholder(str(key))]
    if not named:
        return True
    try:
        from .known_checks import LISTED_NOT_RUN
    except ImportError:  # pragma: no cover - direct script import shim
        from utils.known_checks import LISTED_NOT_RUN
    outcomes = ran_check_outcomes(result)
    return len(outcomes) == len(named) and all(
        word == LISTED_NOT_RUN for word in outcomes.values()
    )


def _with_ran_failures(
    findings: Optional[List[str]], ran: Dict[str, str],
) -> Optional[List[str]]:
    """*findings* with one added for each command ``ran`` says failed that no
    finding names (``known_checks.with_listed_failures``): a reply whose
    ``passed`` says true beside a failed command is never a clean pass.

    Fix round 27: it only adds. A ``ran`` naming no failure leaves a
    ``passed: false`` that named nothing a failing check
    (:data:`CHECK_FAILED_WITHOUT_FINDINGS`), as the native leg records it;
    round 26 read it as a pass through ``with_listed_failures``' rule for an
    apply-code-fixes batch's ``listed`` (fix round 21), which stays
    ``listed``'s alone. A failed command added stands in for that bare
    placeholder, as the native host names the command instead."""
    failed = {
        command: word for command, word in ran.items() if word == _ran_word("failed")
    }
    if not failed:
        return findings
    try:
        from .known_checks import with_listed_failures
    except ImportError:  # pragma: no cover - direct script import shim
        from utils.known_checks import with_listed_failures
    current = with_listed_failures(findings, failed) or []
    if len(current) > 1 and current[0] == CHECK_FAILED_WITHOUT_FINDINGS:
        current = current[1:]
    return current


def _report_check_evidence(result: Any) -> Optional[Dict[str, Any]]:
    """A readable check object to retain across a report-only re-ask.

    A restatement runs no check, so it cannot retract the original turn's
    evidence. Keep the whole object, including ``listed`` and any extra
    detail, when the existing lenient readers can use it. A missing or
    unreadable check remains repairable rather than pinning an unknown
    result over a useful correction.
    """
    check = result.get("check") if isinstance(result, dict) else None
    if not isinstance(check, dict):
        return None
    try:
        from .known_checks import listed_check_outcomes
    except ImportError:  # pragma: no cover - direct script import shim
        from utils.known_checks import listed_check_outcomes

    if (
        batch_check_findings(result) is not None
        or listed_check_outcomes(check.get("listed"))
        # Fix round 26: "I ran no check" is an answer too; a restatement
        # cannot turn it into a pass.
        or ran_no_check(result)
    ):
        return copy.deepcopy(check)
    return None


#: How much of one declined item's reason a row, a stamp or a notice carries.
DECLINED_REASON_MAX_CHARS = 300


def declined_reason(text: Any) -> str:
    """One declined item's reason as every record carries it: the batch's
    own words, whitespace collapsed and bounded; ``""`` for no text.

    Both legs read a reason through here: the executor's
    :func:`declined_items` and ``util batch-done --declined``, and
    :func:`row_declined` reads a record back through it.

    Fix round 26 (live run 11 #10): the closing full stop is kept.
    ``processed_<phase>``, the write mirror, the verdict stamp and the report
    dropped it while the reply, the log and the host's summary.md kept it.
    A line that puts its own punctuation right after a reason drops the
    reason's one there (``text_clip.without_closing_mark``: the
    ``[BATCH_DECLINED]`` line, the stop and log text, the notes, ``status``),
    so a reason is still printed with one full stop (the decline fixture,
    2026-10-07: "… MAX_SPEED.."); a reason of ``...`` or ``.`` stays a
    reason (fix round 21).
    """
    if not isinstance(text, str):
        return ""
    reason = " ".join(text.split())
    # Fix round 22: cut at a word and marked, never mid-word.
    return clip(reason, DECLINED_REASON_MAX_CHARS)


@dataclass
class DeclinedItems:
    """What a write reply's ``declined`` says, read against its batch (fix round 18).

    ``items`` maps each expected id the batch declined — not also in ``ids``,
    with a non-empty reason — to that reason, in the batch's own order.
    ``conflicting`` holds the ids the reply put in both ``ids`` and
    ``declined``: neither claim stands, so such an id is not attested at all.
    ``problems`` names every other entry that could not be read as a decline
    (an id the batch does not hold, an entry without an id or a reason, a
    value that is not a list of objects), in plain words for the stop.
    """

    items: Dict[str, str] = field(default_factory=dict)
    conflicting: List[str] = field(default_factory=list)
    problems: List[str] = field(default_factory=list)


def declined_items(
    result: Any, expected_ids: Sequence[str],
) -> DeclinedItems:
    """Read a write reply's ``declined`` leniently against *expected_ids*.

    Codex racing run 7 (2026-10-06, apply-code-fixes 08): a batch applied
    one fix and left the other on purpose ("Not applied; T011 records the
    clamp removal as deliberate"), said so only in ``notes``, and stopped as
    a partial application on the run and on its resume; the contract had no
    place for a decline. A reason is what makes a decline: an entry without
    one is a problem, and its id reads as not having come back, as an id
    missing from ``ids`` always has. Never read from ``notes``.
    """
    out = DeclinedItems()
    raw = result.get("declined") if isinstance(result, dict) else None
    if raw is None:
        return out
    expected = [str(item) for item in expected_ids]
    reported = result.get("ids") if isinstance(result, dict) else None
    applied = {str(item) for item in reported} if isinstance(reported, list) else set()
    if not isinstance(raw, list):
        out.problems.append("`declined` is not a list")
        return out
    found: Dict[str, str] = {}
    for index, entry in enumerate(raw, 1):
        if not isinstance(entry, dict):
            out.problems.append(f"`declined` entry {index} is not an object")
            continue
        item = entry.get("id")
        item = str(item).strip() if isinstance(item, (str, int)) else ""
        if not item:
            out.problems.append(f"`declined` entry {index} names no id")
            continue
        if item not in expected:
            out.problems.append(
                f"`declined` names {item!r}, which this batch does not hold"
            )
            continue
        if item in applied:
            if item not in out.conflicting:
                out.conflicting.append(item)
                out.problems.append(f"{item} is in both `ids` and `declined`")
            continue
        reason = declined_reason(entry.get("reason"))
        if not reason:
            out.problems.append(f"`declined` gives no reason for {item}")
            continue
        found.setdefault(item, reason)
    out.items = {item: found[item] for item in expected if item in found}
    return out


def row_declined(row: Any) -> Dict[str, str]:
    """A serialized row's (or verdict stamp's) declined items, ``{id: reason}``."""
    raw = row.get("declined") if isinstance(row, dict) else None
    out: Dict[str, str] = {}
    for entry in raw if isinstance(raw, list) else []:
        if isinstance(entry, dict) and entry.get("id") and entry.get("reason"):
            # As recorded (a record from before fix round 26 has no closing
            # stop; one from before `declined_reason` reads the same way).
            reason = declined_reason(str(entry["reason"])) or str(entry["reason"])
            out.setdefault(str(entry["id"]), reason)
    return out


#: summary.md's sections for an apply phase's items that were not applied
#: (fix round 22, live run 9: a declined fix sat under "## Applied Fixes" on
#: the native leg and under its batch in "## Applied Changes" on the
#: executor's), written by the executor's summary and named by the native
#: runbooks' template and `util batch-done`'s `[BATCH_DECLINED]` /
#: `[BATCH_SKIPPED]` lines.
DECLINED_SECTION_HEADING = "Declined by their batch (not applied)"
SKIPPED_SECTION_HEADING = "Skipped at your request (not applied)"


def declined_record(items: Dict[str, str]) -> List[Dict[str, str]]:
    """The ``declined`` list a row, a verdict stamp and a mirror row carry."""
    return [{"id": item, "reason": reason} for item, reason in items.items()]


def row_batch_check_findings(row: Dict[str, Any]) -> List[str]:
    """A serialized row's own-check findings (its ``batch_check``), else ``[]``."""
    check = row.get("batch_check") if isinstance(row, dict) else None
    if not isinstance(check, dict):
        return []
    return [str(item) for item in (check.get("findings") or []) if str(item)]


def row_batch_check_accepted(row: Dict[str, Any]) -> Dict[str, List[str]]:
    """A serialized row's own-check findings that only repeat what the user
    accepted, by check id (its ``batch_check_accepted``, fix round 22), else
    ``{}``."""
    found = row.get("batch_check_accepted") if isinstance(row, dict) else None
    if not isinstance(found, dict):
        return {}
    return {
        str(check_id): [str(item) for item in items if str(item)]
        for check_id, items in found.items()
        if isinstance(items, list) and any(str(item) for item in items)
    }


def row_batch_check_repeats(row: Dict[str, Any]) -> Dict[str, List[str]]:
    """A serialized row's own-check findings that are the same findings a
    check task of the run reported, by that check's id (its
    ``batch_check_repeats``, fix round 28), else ``{}``."""
    found = row.get("batch_check_repeats") if isinstance(row, dict) else None
    if not isinstance(found, dict):
        return {}
    return {
        str(check_id): [str(item) for item in items if str(item)]
        for check_id, items in found.items()
        if isinstance(items, list) and any(str(item) for item in items)
    }


def row_batch_check_note(row: Dict[str, Any]) -> Optional[str]:
    """A serialized row's own-check note (its ``batch_check_note``, fix round
    28), else ``None``."""
    note = row.get("batch_check_note") if isinstance(row, dict) else None
    if not isinstance(note, str):
        return None
    return clip(note, CHECK_NOTE_MAX_CHARS) or None


def row_outcome_label(row: Dict[str, Any]) -> Optional[str]:
    """A serialized row's label: ``outcome_label`` when present, else ``write_outcome``.

    Only a verification-only row carries ``outcome_label`` (every other row
    is byte-identical to before), so a reader asks this rather than either key.
    """
    return row.get("outcome_label") or row.get("write_outcome")


def check_record(findings: Sequence[str]) -> Dict[str, Any]:
    """The ``check`` object a row, a verdict stamp and a mirror row carry."""
    return {"passed": not findings, "findings": list(findings)}


def row_check_findings(row: Dict[str, Any]) -> List[str]:
    """A serialized row's check findings (its ``check`` object), else ``[]``."""
    check = row.get("check") if isinstance(row, dict) else None
    if not isinstance(check, dict):
        return []
    return [str(item) for item in (check.get("findings") or []) if str(item)]
WRITE_SCHEMA_REJECTED = "schema-rejection"
WRITE_POLICY_VIOLATION = "policy-violation"

#: Write outcomes that stop the batch loop at its boundary (D3g/D3n): the phase is
#: not completed, snapshots stay in place, and the run exits 3 naming the restore
#: command — under ``--yes`` too, since an unattended run may not decide that a
#: half-applied plan file is acceptable.
WRITE_STOP_OUTCOMES = frozenset({WRITE_PARTIAL, WRITE_POLICY_VIOLATION})

#: Per-kind ``output_name`` patterns (D3f), so the reaggregation glob can never be
#: fed a foreign file. ``salvage`` is the one kind whose output IS a model result
#: file (it repairs one), so its pattern is "any plain .json basename" and the
#: reserved-name check below is what bounds it.
OUTPUT_NAME_PATTERN_BY_KIND = {
    "validation": re.compile(r"^validation_batch_\d+\.json$"),
    # Revalidation deliberately reuses the validation batch filenames: it is the
    # same producer (``prepare_batched_revalidation_tasks`` delegates to
    # ``prepare_batched_validation_tasks``) and the same merge reads them back, so
    # the pattern accepts both spellings rather than the kind's own name.
    "revalidation": re.compile(r"^(?:re)?validation_batch_\d+\.json$"),
    "consolidation": re.compile(r"^consolidation_batch_\d+\.json$"),
    # A judge verdict file is keyed by the judged item's stable ``group_id``
    # (``human_decisions.verdict_output_name``), not by a batch index, so that a
    # resumed judging phase — which materializes only the *remaining* items —
    # cannot have one group's task adopt another group's already-written verdict
    # as its own completed output. The token is therefore any basename-safe id;
    # older ``_<n>`` names still match.
    "human_decision_judge": re.compile(
        r"^human_decision_batch_[A-Za-z0-9][A-Za-z0-9._-]*\.json$"
    ),
    "task_generation": re.compile(r"^task_generation_result\.json$"),
    "salvage": re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*\.json$"),
    # Write kinds (D3g): the batch result JSON. One distinct pattern per kind, so a
    # hand-edited or regenerated task from one phase can never write into another
    # phase's result set even when the phase dirs are siblings.
    "apply_suggestions": re.compile(r"^apply_batch_\d+\.json$"),
    "apply_task_suggestions": re.compile(r"^apply_task_batch_\d+\.json$"),
    "apply_code_fixes": re.compile(r"^apply_fix_batch_\d+\.json$"),
    # An implement result is keyed by the plan task's stable id
    # (``subagent_tasks.implement_output_name``), not by a batch index, for the
    # same reason the judge verdict above is: a resumed implement phase
    # materializes only the *remaining* tasks, so a positional token would let
    # one task adopt a predecessor's already-written result as its own
    # completed output. The token is therefore any basename-safe id; older
    # ``_<n>`` names still match.
    "implement": re.compile(r"^implement_batch_[A-Za-z0-9][A-Za-z0-9._-]*\.json$"),
}

#: Orchestrator-owned artifacts an executor write may never land on (D3f).
RESERVED_OUTPUT_NAMES = frozenset({
    "grouped.json",
    "validation.json",
    "validation_tasks.json",
    "revalidation.json",
    "revalidation_tasks.json",
    "consolidation_tasks.json",
    "consolidated.json",
    "human_decision_tasks.json",
    "report_data.json",
    "state.json",
    ".status.json",
    "orchestrator-run.log",
    BATCH_REPORT_FILENAME,
    # Write-path artifacts the executor owns (D3g/D3l). A subagent result landing
    # on any of these would overwrite the very evidence the classification, the
    # audit trail and `util restore-batch` depend on.
    "orchestrator_output.json",
    "subagent_audit.jsonl",
    "subagent_dry_run.json",
    "prior_changes.jsonl",
    "write_batch_report.json",
    # The two materialized task files the list above was missing: the write half's
    # (``write_phase_bridge.WRITE_TASK_FILENAME``, spelled out rather than imported
    # only to keep this module's import graph unchanged) and ``generate-tasks``'s
    # single-task envelope. A result landing on either would overwrite the very
    # file the phase is dispatching from, which ``salvage``'s deliberately broad
    # "any plain .json basename" pattern would otherwise permit.
    "write_tasks.json",
    "task_generation_tasks.json",
})

#: Basename prefixes an executor write may never land on (a task file, a salvage
#: request, a rotated log).
RESERVED_OUTPUT_PREFIXES = ("salvage_", "error_", "orchestrator-run.")

#: Basename suffixes an executor write may never land on. Every materialized task
#: file is ``<phase>_tasks.json``, so the suffix — not the enumeration above — is
#: what keeps a later phase's task file safe without a second edit here.
RESERVED_OUTPUT_SUFFIXES = ("_tasks.json",)

#: Statuses mirrored into ``.status.json`` under ``progress`` (display only).
_STATUS_MIRROR_KEY = "subagents"

#: The token D3n substitutes late, per dispatch. Duplicated as a private constant
#: rather than imported at module scope only to keep this module's import graph
#: unchanged; ``tests/test_subagent_tasks.py`` pins the two spellings together.
#: A prompt-template placeholder, not an authentication credential.
_PRIOR_CHANGES_TOKEN: str = "{prior_changes_context}"


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

class ExecutorError(Exception):
    """Something the executor refuses to do. Exit 3 ("needs a human", D6)."""

    exit_code = 3

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class RunnerRejected(ExecutorError):
    """A configured runner spec cannot serve this phase (one rejection surface).

    Rendered by :func:`_render_runner_rejection` so the wording cannot drift per
    call site: the offending key, the spec as written, a reason code
    (``unknown_provider`` | ``missing_capability`` | ``missing_profile``), that
    code's explanation, the runners on this host that *would* satisfy the request,
    and the fix.
    """

    def __init__(self, message: str, *, key: str = "", spec: str = "",
                 reason_code: str = "", detail: str = "") -> None:
        super().__init__(message)
        self.key = key
        self.spec = spec
        self.reason_code = reason_code
        #: The provider's own words behind the refusal, already redacted — the
        #: probe tail carrying a "Did you mean" list, say — kept as a field so
        #: the exit-3 handler can print it as a line of its own (D4 step 5)
        #: rather than leaving the reader to find it inside ``message``.
        self.detail = detail


class ResultRejected(ExecutorError):
    """One task's result cannot be used. Carries the D3k status it lands on."""

    def __init__(self, message: str, status: str) -> None:
        super().__init__(message)
        self.status = status


class BatchFailed(ExecutorError):
    """A batch had failed or incomplete tasks, so the phase must not reaggregate."""

    def __init__(self, message: str, report: "BatchReport") -> None:
        super().__init__(message)
        self.report = report


# ---------------------------------------------------------------------------
# Records
# ---------------------------------------------------------------------------

@dataclass
class Attempt:
    """One dispatch attempt of one task."""

    index: int
    status: str
    exit_code: Optional[int] = None
    duration_seconds: float = 0.0
    error: Optional[str] = None
    usage: Optional[Dict[str, Any]] = None
    capture_path: Optional[str] = None
    #: Set on an attempt that carried the schema-repair re-ask (the ladder's
    #: rule 7) — :data:`REPAIR_SCHEMA_INVALID` — so the batch report says which
    #: attempt was the second question rather than a second try of the first.
    repair: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {
            "attempt": self.index,
            "status": self.status,
            "duration_seconds": round(self.duration_seconds, 3),
        }
        if self.exit_code is not None:
            out["exit_code"] = self.exit_code
        if self.error:
            out["error"] = self.error
        if self.usage:
            out["usage"] = dict(self.usage)
        if self.capture_path:
            out["capture"] = self.capture_path
        if self.repair:
            out["repair"] = self.repair
        return out


@dataclass
class TaskOutcome:
    """The row ``subagent_batch_report.json`` records for one ``task_id``."""

    task_id: str
    kind: str
    runner: str
    status: str
    profile: str = PROFILE_AGENT_READONLY
    attempts: List[Attempt] = field(default_factory=list)
    output_path: Optional[str] = None
    reason: Optional[str] = None
    duration_seconds: float = 0.0
    usage: Optional[Dict[str, Any]] = None
    usage_reported: bool = False
    skipped: bool = False
    #: D3g, write kinds only: which of the four outcomes the snapshot/diff
    #: classification landed on. Its own axis rather than a status, because
    #: the status says whether the loop goes on and this says what the bytes did.
    write_outcome: Optional[str] = None
    #: The files the post-run byte comparison actually observed as changed — the
    #: set the write policy is enforced against, never the runner's own claim.
    files_touched: List[str] = field(default_factory=list)
    #: The `summary` line lifted from the batch result JSON, for the prior-changes
    #: append. Never a compressed chat message.
    summary: Optional[str] = None
    #: Where this task's pre-batch snapshot lives, so an exit-3 message can name
    #: the restore command instead of describing it.
    snapshot_dir: Optional[str] = None
    #: F9: write kinds only, alongside `write_outcome` — the batch's own
    #: declared item ids and the ids the runner's reply actually returned, so
    #: `write_batch_report.json` and this row's own `subagent_batch_report.json`
    #: (they serialize the same `TaskOutcome`) can answer "did every item come
    #: back?" without re-deriving it from `subagent_audit.jsonl` or the
    #: per-batch result file.
    expected_ids: List[str] = field(default_factory=list)
    returned_ids: List[str] = field(default_factory=list)
    #: F9: the pre-batch snapshot's own before/after hashes for every file the
    #: post-run sweep observed (declared or not), keyed by repo-relative path —
    #: the same evidence `subagent_audit.jsonl`'s `observed.<file>.sha256_*`
    #: carries, so the hash chain's contiguity is checkable from this report
    #: alone.
    sha256_before: Dict[str, Optional[str]] = field(default_factory=dict)
    sha256_after: Dict[str, Optional[str]] = field(default_factory=dict)
    #: §4.2.1's marker for a schema-carrying dispatch: ``native`` (the CLI's own
    #: ``structured_output`` key, conformant), ``recovered`` (the document came
    #: out of the prose answer and validated against the same schema file) or
    #: ``unvalidated`` (no schema was in play). ``None`` — and therefore absent
    #: from the report row — for every kind with no schema phase, which is what
    #: keeps ``subagent_batch_report.json`` byte-identical off this path.
    structured_output: Optional[str] = None
    #: An ``implement`` dispatch that declared no files (the scheduler's
    #: ``_verification_only``): its write outcome reads as
    #: :func:`write_outcome_label` says — ``verified`` for a ``no-op``.
    verification_only: bool = False
    #: The runner's own ``notes`` for a write batch (what a check reported:
    #: the validator's lines, the failing command), bounded. Carried so the
    #: stop message and a later ``--resume`` can say what failed rather than
    #: only that it did (racing re-run 3, 2026-10-05).
    runner_notes: Optional[str] = None
    #: A resumed verification-only task that was NOT dispatched again because
    #: nothing in the repository changed since it failed (the scheduler's
    #: unchanged-tree guard). No child ran, so no metric is recorded for it.
    not_rerun: bool = False
    #: A verification-only task's structured check result
    #: (:func:`check_findings_from`): ``None`` when its reply carried none,
    #: ``[]`` when the check passed, else what the check found. Non-empty on a
    #: ``no-op`` makes the label ``check-findings`` (racing re-run 4).
    check_findings: Optional[List[str]] = None
    #: A code-writing batch's own ``check`` (:func:`batch_check_findings`):
    #: the checks it ran on its edits. ``None`` when its reply reported none,
    #: ``[]`` when they passed, else what failed. Its own axis, never
    #: ``check_findings``: a write task whose test fails holds nothing back,
    #: but an ``ok`` row carrying findings is never reported as a plain
    #: success (fix round 14).
    batch_check: Optional[List[str]] = None
    #: The own-check findings of an implement task that only repeat what the
    #: user accepted for a check (``--human-task <check>=done``), by check id
    #: (``write_batch_scheduler.split_accepted_findings``, fix round 22): taken
    #: out of ``batch_check``, so they never make the task's own failure, and
    #: named beside that check's accepted findings instead. Empty otherwise.
    batch_check_accepted: Dict[str, List[str]] = field(default_factory=dict)
    #: The own-check findings of an implement task that are the same
    #: findings a check task of the run reported (the strict comparison of
    #: ``write_batch_scheduler.split_repeated_findings``), by that check's id
    #: (``write_batch_scheduler.repeated_findings_for``, fix round 28, live
    #: run 12 OpenCode accept 01: T001 ran T002's release check and was
    #: blamed for T002's finding). Taken out of ``batch_check`` whichever of
    #: the two finished first, and named beside that check's findings.
    batch_check_repeats: Dict[str, List[str]] = field(default_factory=dict)
    #: The code batch's own words about its checks (its ``check.note``,
    #: :func:`batch_check_note`, fix round 28): recorded and shown beside
    #: the check, never a finding. ``None`` when it gave none.
    batch_check_note: Optional[str] = None
    #: A write batch whose reply said ``applied`` while no byte moved, after
    #: its one re-send (the ladder's rule 9): a ``clean-failure`` that is
    #: never ``ok``, worded on the stop as a change that did not land (fix
    #: round 14). ``False`` for every other outcome.
    applied_without_changes: bool = False
    #: The files this dispatch moved that have no rollback point: observed by
    #: the post-run sweep outside the declared set, with no pre-run bytes in
    #: the rollback store (a path the write policy denies, a file over the
    #: per-file cap or past the store's budget, one unreadable before the
    #: run). Never in ``files_touched``, which ``util restore-batch`` reads,
    #: but moved all the same (fix round 15: a partial application that moved
    #: only such a file was announced "Nothing was half-applied").
    unrestorable: List[str] = field(default_factory=list)
    #: Killed at its time limit (``driver.subagent_timeout_s``, else the
    #: runner's ``default_timeout``) after its edits landed: a partial
    #: application whose stop says the edits are kept (fix round 16).
    ran_out_of_time: bool = False
    #: An apply batch's items it deliberately left unapplied, ``{id: reason}``
    #: in the batch's order (:func:`declined_items`, fix round 18). Never
    #: counted as applied, named on every surface, and a batch whose every
    #: item is applied or declined is complete.
    declined: Dict[str, str] = field(default_factory=dict)
    #: A partial application whose readable report attests some items and
    #: leaves these out of both ``ids`` and ``declined`` (fix round 18): the
    #: items ``--human-task <id>=skip`` records as skipped at the user's
    #: request, keeping what the batch applied. Empty for every other outcome,
    #: and so the stop offers that answer only here.
    unapplied_ids: List[str] = field(default_factory=list)
    #: The items a ``--human-task <id>=skip`` answer recorded as skipped at
    #: the user's request when it kept the batch as it stood, ``{id:
    #: reason}`` (fix round 18). Never counted as applied.
    skipped_items: Dict[str, str] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.status == STATUS_OK

    @property
    def bytes_moved(self) -> bool:
        """Whether this dispatch left any file changed: the rollback set
        (``files_touched``) or a moved file with no rollback point."""
        return bool(self.files_touched or self.unrestorable)

    @property
    def outcome_label(self) -> Optional[str]:
        """The word every surface shows for this outcome (:func:`write_outcome_label`)."""
        return write_outcome_label(
            self.write_outcome, self.verification_only, self.check_findings,
        )

    @property
    def stops_the_loop(self) -> bool:
        """Whether this outcome forbids dispatching the next batch (D3g/D3n)."""
        return self.write_outcome in WRITE_STOP_OUTCOMES

    @property
    def rung(self) -> Optional[int]:
        return RUNG_BY_STATUS.get(self.status)

    @property
    def repair(self) -> Optional[str]:
        """The re-ask this task's dispatch sent (the ladder's rule 7), if any.

        The attempt that carried it already says so; the row says it too, so a
        reader of ``subagent_batch_report.json`` sees ``repair:
        schema_invalid`` beside the task's final status without walking its
        attempts (2026-10-05: only ``attempt_count: 2`` showed it).
        """
        for attempt in self.attempts:
            if attempt.repair:
                return attempt.repair
        return None

    @property
    def fatal(self) -> bool:
        return self.status in FATAL_STATUSES

    def to_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {
            "task_id": self.task_id,
            "kind": self.kind,
            "runner": self.runner,
            "profile": self.profile,
            "status": self.status,
            "attempt_count": len(self.attempts),
            "duration_seconds": round(self.duration_seconds, 3),
        }
        if self.repair:
            out["repair"] = self.repair
        if self.rung is not None:
            out["rung"] = self.rung
        if self.output_path:
            out["output_path"] = self.output_path
        if self.reason:
            out["reason"] = self.reason
        if self.skipped:
            out["skipped"] = True
        if self.structured_output:
            out["structured_output"] = self.structured_output
        if self.write_outcome:
            out["write_outcome"] = self.write_outcome
            if self.verification_only:
                # Additive and only here, so every other row is unchanged.
                out["verification_only"] = True
                out["outcome_label"] = self.outcome_label
                if self.check_findings is not None:
                    out["check"] = check_record(self.check_findings)
            if self.batch_check is not None:
                # Additive and only here, so a row whose reply ran no check
                # is unchanged.
                out["batch_check"] = check_record(self.batch_check)
            if self.batch_check_accepted:
                # Additive and only here (fix round 22).
                out["batch_check_accepted"] = {
                    str(check_id): list(found)
                    for check_id, found in self.batch_check_accepted.items()
                }
            if self.batch_check_repeats:
                # Additive and only here (fix round 28).
                out["batch_check_repeats"] = {
                    str(check_id): list(found)
                    for check_id, found in self.batch_check_repeats.items()
                }
            if self.batch_check_note:
                # Additive and only here (fix round 28).
                out["batch_check_note"] = self.batch_check_note
            if self.runner_notes:
                out["runner_notes"] = self.runner_notes
            if self.not_rerun:
                out["not_rerun"] = True
            if self.applied_without_changes:
                out["applied_without_changes"] = True
            out["files_touched"] = list(self.files_touched)
            if self.unrestorable:
                # Additive and only here (fix round 15).
                out["unrestorable"] = list(self.unrestorable)
            if self.declined:
                # Additive and only here (fix round 18).
                out["declined"] = declined_record(self.declined)
            if self.unapplied_ids:
                out["unapplied_ids"] = list(self.unapplied_ids)
            if self.skipped_items:
                out["skipped_items"] = declined_record(self.skipped_items)
            if self.summary:
                out["summary"] = self.summary
            if self.snapshot_dir:
                out["snapshot_dir"] = self.snapshot_dir
            # F9: verification evidence, present on every write outcome
            # (`expected_ids`/`sha256_*` even when empty — an empty pair is
            # itself evidence, e.g. an `implement` task with no declared file).
            out["expected_ids"] = list(self.expected_ids)
            out["returned_ids"] = list(self.returned_ids)
            out["sha256_before"] = dict(self.sha256_before)
            out["sha256_after"] = dict(self.sha256_after)
        if self.usage_reported:
            out["usage"] = dict(self.usage or {})
        else:
            out["usage_reported"] = False
        if self.attempts:
            out["attempts"] = [a.to_dict() for a in self.attempts]
        return out


@dataclass
class BatchReport:
    """Every ``task_id`` in a batch with its status, attempts and runner (D3i)."""

    phase: str = ""
    kind: str = ""
    phase_dir: str = ""
    task_file: Optional[str] = None
    outcomes: List[TaskOutcome] = field(default_factory=list)
    ceilings: Dict[str, Any] = field(default_factory=dict)
    runner_versions: Dict[str, str] = field(default_factory=dict)
    #: The one substitution the resolution ladder is allowed to make silently at
    #: dispatch time, recorded so it is not silent after the fact:
    #: ``{"from", "reason", "to", "layer"}`` when the host session's own model
    #: failed preflight and the batch fell through to the next rung (see
    #: :func:`_preflight_batch_runners`). ``None`` on every ordinary run.
    runner_fallback: Optional[Dict[str, str]] = None
    #: §7.3a: per-output provenance, ``{task_id: {task_id, kind, round, runner,
    #: sha256}}`` for every result file this batch (or, carried forward, an
    #: earlier dispatch of the same round) persisted. ``sha256`` is over the
    #: file's bytes at the moment the executor recorded it, and ``round`` is
    #: :func:`subagent_tasks.task_round` of the batch's task list, so the merge
    #: can tell a file the executor's runner wrote from one rewritten by hand or
    #: by another host since — by content, never by mtime. Empty (and absent
    #: from the report) when nothing was persisted.
    batch_provenance: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    #: :func:`_pin_sha256` of the task list this report dispatched. A recorded
    #: runner is a pin only for a re-dispatch of the *same* round and inputs
    #: (:func:`_recorded_runners`); a report that carries no digest (written before
    #: it existed) pins as it always did. Empty means "not recorded".
    pin_sha256: str = ""
    invoker: str = "executor"

    @property
    def ok(self) -> bool:
        """True only when every task produced a schema-valid result file."""
        return bool(self.outcomes) and all(o.ok for o in self.outcomes)

    @property
    def failed(self) -> List[TaskOutcome]:
        return [o for o in self.outcomes if not o.ok]

    def counts(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for outcome in self.outcomes:
            counts[outcome.status] = counts.get(outcome.status, 0) + 1
        return counts

    def usage_totals(self) -> Dict[str, Any]:
        """Partial sum **plus** the count of tasks with no usage data (D3j).

        Never a total that pretends to be complete: a batch mixing a
        usage-reporting runner with a duration-only one reports both numbers.
        """
        totals: Dict[str, Any] = {}
        missing = 0
        for outcome in self.outcomes:
            if not outcome.usage_reported or not outcome.usage:
                missing += 1
                continue
            for key, value in outcome.usage.items():
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    totals[key] = totals.get(key, 0) + value
        result: Dict[str, Any] = dict(totals)
        result["tasks_without_usage"] = missing
        result["attempts"] = sum(len(o.attempts) for o in self.outcomes)
        return result

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_version": 1,
            "invoker": self.invoker,
            "phase": self.phase,
            "kind": self.kind,
            "task_file": self.task_file,
            "ceilings": dict(self.ceilings),
            "runner_versions": dict(self.runner_versions),
            **({"runner_fallback": dict(self.runner_fallback)}
               if self.runner_fallback else {}),
            # Always present, even empty: `_recorded_provenance` reads an absent
            # key as a pre-§7.3a report and falls back to the legacy per-row
            # runners, so `{}` (no provenance survives) must stay distinguishable.
            "batch_provenance": {
                task_id: dict(row) for task_id, row in self.batch_provenance.items()
            },
            **({"pin_sha256": self.pin_sha256} if self.pin_sha256 else {}),
            "counts": self.counts(),
            "usage": self.usage_totals(),
            "tasks": [o.to_dict() for o in self.outcomes],
        }

    def write(self, phase_dir: Optional[str] = None) -> str:
        """Write this report atomically (F6: :func:`_batch_report_filename`
        picks the name); return its path.

        The third of §4.5.3's four sinks — six planted shapes × fifteen rows,
        carried in the ``reason`` and per-attempt ``error`` strings that quote a
        provider's stream. Redaction sits on the write rather than on
        :meth:`to_dict`, so it covers every field a failure record grows without
        a per-field list to keep in step.
        """
        target_dir = phase_dir or self.phase_dir
        path = os.path.join(target_dir, _batch_report_filename(self.kind))
        _atomic_write_json(path, _redact_json(self.to_dict()))
        return path

    def failure_summary(self) -> List[str]:
        """One line per failure, for the phase's stdout summary (D3i).

        This is the *rendering* half of §4.5.3's fourth sink — the exit-3 block
        prints these lines, and under ``--detach`` they are
        ``orchestrator-run.log``. ``_classify_failed_run`` redacts the reason it
        builds, but rungs 4–6 take theirs from an adapter's own error string,
        which is provider output like any other; redacting here covers every rung
        rather than the two that quote a stream by name.
        """
        lines = []
        for outcome in self.failed:
            rung = outcome.rung
            rung_text = f"rung {rung}" if rung is not None else "no rung"
            lines.append(_redact(
                f"  - {outcome.task_id}: {outcome.status} ({rung_text}, "
                f"{len(outcome.attempts)} attempt(s), runner {outcome.runner}) "
                f"{outcome.reason or ''}".rstrip()
            ))
        return lines


# ---------------------------------------------------------------------------
# Profiles, runners, ceilings
# ---------------------------------------------------------------------------

def profile_for_kind(kind: str) -> str:
    """The D3e invocation profile for a task kind.

    Derived here and nowhere else: the profile must never come from the task JSON,
    which embeds untrusted plan/diff/review text and could otherwise request
    escalation to ``agent-write``.
    """
    try:
        return PROFILE_BY_KIND[kind]
    except KeyError:
        raise ExecutorError(
            f"Unknown task kind {kind!r}: the executor dispatches only "
            f"{', '.join(sorted(PROFILE_BY_KIND))}. Nothing was dispatched."
        ) from None


def eligible_runners(profile: str) -> List[str]:
    """Runner specs on this host that could serve ``profile``.

    The intersection of the adapters declaring the profile with the binaries
    actually present on PATH. Printed as advice by every rejection; an empty
    intersection gets its own sentence rather than an empty list.
    """
    try:
        from .provider_registry import _PROVIDERS  # local import: avoids a cycle
    except ImportError:  # pragma: no cover
        from utils.provider_registry import _PROVIDERS
    names = []
    for name, provider in _PROVIDERS.items():
        if not provider.supports_profile(profile):
            continue
        try:
            if provider.is_available():
                names.append(name)
        except Exception:  # noqa: BLE001 - a probe must never break a refusal
            continue
    return sorted(names)


_REASON_EXPLANATION = {
    "unknown_provider": (
        "the provider name has no built-in adapter, so nothing can run it — "
        "this is a stale-config condition"
    ),
    "missing_capability": (
        "the adapter exists and runs fine, but does not declare the capability "
        "this phase needs — this is a capability condition, not a stale config"
    ),
    "missing_profile": (
        "the adapter exists and runs fine, but implements no invocation for this "
        "profile, and a fabricated one would hand an untrusted prompt write access"
    ),
    "binary_absent": (
        "the adapter is implemented but its CLI is not on PATH"
    ),
    "unresolvable_model": (
        "the model token cannot be expressed in this CLI's own addressing "
        "scheme, so no catalog, no release and no server could resolve it — a "
        "structural refusal, never a catalog lookup"
    ),
    "not_authenticated": (
        "the CLI is installed but not logged in — installed is not authenticated, "
        "and no retry can fix a missing credential"
    ),
    "nested_exec_denied": (
        "this host's capability data declares that a third-party agent CLI cannot "
        "be run from inside it at all — the executor refuses the run naming the "
        "field rather than dispatching into a sandbox that eats the failure"
    ),
    "nested_exec_spawn": (
        "the host's sandbox denied the spawn: the throwaway preflight dispatch "
        "could not start the runner as a child of this host's own shell"
    ),
    "runner_invalid_model": (
        "the runner rejected the model id itself during the preflight probe — "
        "a rejected id is a property of the spec, so every task in the batch "
        "would fail identically and the fix is a config edit, never a retry"
    ),
    "invalid_model_catalog": (
        "the CLI's own model listing, read in this dispatch's configuration, "
        "does not contain this model id — the id is a property of the spec, so "
        "every task in the batch would fail identically and the fix is a config "
        "edit, never a retry"
    ),
    "nested_exec_network": (
        "the runner started inside this host but could not reach its provider "
        "API — the host's egress rules, not the runner, are what failed"
    ),
    "nested_exec_credentials": (
        "the runner started inside this host but could not read its own "
        "credential store — a login notice from inside a sandbox is a host "
        "condition as often as a logged-out CLI, and neither is retryable"
    ),
    "sandbox_unavailable": (
        "the runner's own sandbox cannot start under this repo; on Ubuntu 24.04 "
        "this is the AppArmor user-namespace restriction, see "
        "`multi_llm.py doctor`"
    ),
}

#: The four ``nested_exec`` refusal codes, mapped to the capability field each
#: one is a verdict about.
#:
#: These are *structured* refusals rather than crashes, and the mapping exists
#: because their consumers are not all Python. The OpenCode plugin surfaces each
#: one as a named tool error carrying the reason code **and the field it came
#: from**, so a model is told which capability said no rather than handed a bare
#: non-zero exit — and it reads that pairing from generated data rather than
#: re-deriving it in JavaScript.
NESTED_EXEC_FIELDS: Dict[str, str] = {
    "nested_exec_denied": "nested_exec",
    "nested_exec_spawn": "nested_exec.spawn",
    "nested_exec_network": "nested_exec.network",
    "nested_exec_credentials": "nested_exec.credentials",
}


#: Substrings that identify a *host-side egress* failure in a nested probe's
#: streams (D3c ``nested_exec.network``). Deliberately narrower than the adapters'
#: own classifier sets: these are matched only on a throwaway probe whose entire
#: expected output is one fixed token, and every entry names a transport
#: condition a model answer has no reason to contain. Matched through
#: ``matches_any`` (boundary-aware), never as bare substrings.
NETWORK_DENIAL_PATTERNS: Tuple[str, ...] = (
    "network is unreachable",
    "no route to host",
    "connection refused",
    "connection reset by peer",
    "connection timed out",
    "could not connect",
    "unable to connect",
    "failed to connect",
    "temporary failure in name resolution",
    "name or service not known",
    "getaddrinfo",
    "eai_again",
    "econnrefused",
    "enetunreach",
    "certificate verify failed",
    "self signed certificate",
    "tls handshake",
    "proxy connect",
    "blocked by proxy",
    "egress blocked",
)

#: The word the probe asks for and then looks for. Split out of the prompt so the
#: question and the answer cannot drift apart: the verdict below is decided by
#: searching for this exact string, and a prompt that asked for a different one
#: would record ``unknown`` on every healthy runner.
NESTED_PROBE_MARKER = "MULTI_LLM_NESTED_EXEC_OK"

#: The throwaway prompt the nested-exec probe dispatches (D3c). Trivial on
#: purpose: it is a real, billed turn, so it asks for one token and nothing that
#: needs the workspace, and it runs under ``agent-readonly`` regardless of the
#: profile the batch itself will use — a probe must never hold write access.
NESTED_PROBE_PROMPT = (
    f"Reply with exactly this token and nothing else: {NESTED_PROBE_MARKER}"
)

#: Wall-clock budget for that probe. Long enough for a cold agent CLI start plus
#: one trivial turn, short enough that a wedged sandbox — or merely a slow
#: runner — fails the preflight rather than consuming the batch's own budget.
#:
#: **Why 30 s and not the 120 s this used to be.** The deadline only ever decides
#: how long an *inconclusive* probe is allowed to stall the batch: everything it
#: can still learn after the first seconds is ``allowed``, and ``allowed`` and
#: ``unknown`` dispatch identically. The three verdicts that actually refuse — a
#: launch error (the child never started), a login notice, an egress failure —
#: are all decided before the runner's first token, so no denial needs a long
#: window to surface. What a long window buys is dead time, and the 2026-09-13
#: review-plan run measured it: on ``opencode:opencode/nemotron-3-ultra-free``
#: (a free-tier rung where a one-word ``opencode run`` reply takes ~62 s idle,
#: and longer behind a reviewer fan-out) the probe blew the 120 s deadline
#: anyway, so the run paid 120 s of wall clock between the fan-out and the first
#: validation dispatch to record the same ``unknown`` a 30 s deadline would have
#: recorded 90 s sooner. 30 s still clears a cold CLI start plus a trivial turn
#: on every runner fast enough for the verdict to mean anything.
NESTED_PROBE_TIMEOUT_S = 30.0

#: Wall-clock budget for the D6 sandbox self-test (`sandbox_probe_command`).
#: The command is model-free — codex's runs in ~30 ms — so ten seconds is
#: generous; a probe that outlives it is recorded ``unknown`` and dispatches,
#: exactly like the nested-exec probe's inconclusive branch.
SANDBOX_PROBE_TIMEOUT_S = 10.0

#: How long a timed-out sandbox probe's tree kill, and then the read of what is
#: left in its pipes, may each take on Windows (:func:`_run_sandbox_probe`).
#: The kill is a Job Object's, a single call; the bound is for the ``taskkill``
#: fallback of a probe that got no job.
SANDBOX_PROBE_KILL_S = 1.0

#: The advisory readers' probe budget (`status`, `init`, the next-step block:
#: `repo_wide_write_refusal`), for the standard probe and the rung walk
#: together. `status` has a sub-second contract and dispatches nothing, so a
#: probe that hangs or is slow must cost it this much at most and draw no
#: warning (a warning that may be wrong is worse than none) — and a
#: measurement this budget cut short is never cached, so a dispatch later in
#: the same process probes afresh under `SANDBOX_PROBE_TIMEOUT_S`, which
#: does not move (adversarial review, 2026-10-02).
ADVISORY_PROBE_BUDGET_S = 1.0


def _availability_detail(spec: str) -> str:
    """The typed availability sentence for ``spec``'s adapter, or ``""`` (M10, §5.1).

    Reads the adapter's declared data only — no probe is run and no child is
    spawned — so it is safe on a refusal path that has already decided nothing
    will be dispatched. Any failure to resolve the adapter is silence, because a
    diagnostic may never be the reason a refusal cannot be printed.
    """
    try:
        provider_name, _, model = str(spec or "").partition(":")
        provider = get_provider(provider_name.strip())
        if provider is None:
            return ""
        return provider.describe_availability(
            credentials_required=_model_needs_credentials(provider, model.strip())
        ).detail
    except Exception:  # noqa: BLE001 - a diagnostic may never break a refusal
        return ""


def _model_needs_credentials(provider: Any, model: str) -> bool:
    """``provider.model_needs_credentials(model)``, defaulting to ``True``.

    The base adapter declares the hook; a narrow test double may not, and a
    missing declaration must read as "needs one" — the exemption is narrow or
    it is a hole (D3 step 2).
    """
    hook = getattr(provider, "model_needs_credentials", None)
    if not callable(hook):
        return True
    try:
        return bool(hook(model))
    except Exception:  # noqa: BLE001 - a declaration read may not break a preflight
        return True


def _render_runner_rejection(
    *, key: str, spec: str, reason_code: str, profile: str, detail: str = ""
) -> RunnerRejected:
    """The single rejection formatter (D3). Exit 3."""
    if reason_code == "binary_absent" and not detail:
        # M10 (§5.1). The refusal itself stays a **bool** decision — the caller
        # gated on `is_available()` and this formatter does not second-guess it.
        # What gains the typed state is the *text*, here, in the one place every
        # rejection is rendered, so a `binary_absent` message finally names which
        # binary and why instead of leaving the reader with a reason code.
        detail = _availability_detail(spec)
    candidates = eligible_runners(profile)
    if candidates:
        advice = (
            f"Runners on this host that can serve {profile!r}: "
            f"{', '.join(candidates)}."
        )
    else:
        advice = (
            f"No runner on this host can serve {profile!r} — install one of the "
            f"supported CLIs (claude, codex, opencode) and authenticate it."
        )
    explanation = _REASON_EXPLANATION.get(reason_code, reason_code)
    message = (
        f"Refusing to dispatch: {key} is {spec!r} (reason: {reason_code}) — "
        f"{explanation}. {detail} {advice} "
        f"Fix: run --init to refresh a stale provider name, install the missing "
        f"CLI, or set {key} to one of the runners named above."
    ).replace("  ", " ")
    return RunnerRejected(message, key=key, spec=spec, reason_code=reason_code)


def resolve_task_runner(
    task: Dict[str, Any],
    *,
    anchor: Optional[str] = None,
    recorded: Optional[Dict[str, str]] = None,
) -> str:
    """Resolve one task's runner spec, once, at batch start (D2e/D3o).

    Chain: a recorded runner from a previous attempt (so ``--resume`` and
    ``--retry-failed-subagents`` re-dispatch the runner the first attempt used,
    not one a since-edited config would pick) → the task's own ``model_hint`` when
    it is a concrete ``provider:model`` and not ``auto`` → ``capability_tier``
    (``cheap`` → ``driver.subagent_runner_cheap``) → ``driver.subagent_runner``.
    """
    return resolve_task_runner_source(task, anchor=anchor, recorded=recorded)[0]


def resolve_task_runner_source(
    task: Dict[str, Any],
    *,
    anchor: Optional[str] = None,
    recorded: Optional[Dict[str, str]] = None,
) -> Tuple[str, str]:
    """:func:`resolve_task_runner`, plus the ``key`` naming what supplied the spec.

    The second element is what a preflight refusal prints as *the thing to
    edit* (D3 step 3's ``key=`` repair). Before it, every message said
    ``driver.subagent_runner`` whatever rung answered — and on the host and base
    rungs that names a key no file on the user's machine sets, then closes by
    telling them to edit it. So the source travels with the spec:

    * a runner recorded by a previous attempt → ``tasks[<id>].runner (recorded
      from a previous attempt)``;
    * the task's own ``model_hint`` → ``tasks[<id>].model_hint``;
    * the ladder → ``driver.subagent_runner`` (or ``_cheap``) with the layer
      :func:`resolve_subagent_runner` reported in parentheses — ``env``,
      ``project``, ``session``, ``host capabilities`` or ``base``/``default``.
    """
    spec, key, _layer = _resolve_task_source(
        task, anchor=anchor, recorded=recorded
    )
    return spec, key


def _resolve_task_source(
    task: Dict[str, Any],
    *,
    anchor: Optional[str] = None,
    recorded: Optional[Dict[str, str]] = None,
    skip_session: bool = False,
) -> Tuple[str, str, str]:
    """:func:`resolve_task_runner_source`, plus the raw ladder *layer* word.

    The layer travels separately from the rendered ``key`` because one rung —
    ``session`` — is treated differently by :func:`run_tasks` when a preflight
    refuses it, and re-deriving that from the human-readable key would mean
    parsing a sentence written for a person. ``""`` is the layer for the two
    task-level overrides, which come off the task file rather than off the
    ladder and therefore have no rung of their own.

    ``skip_session`` is forwarded to the ladder so the fallback re-resolution
    cannot return the session spec that was just refused.
    """
    task_id = str(task.get("task_id", ""))
    if recorded and task_id in recorded:
        return (
            recorded[task_id],
            f"tasks[{task_id}].runner {_RECORDED_RUNNER_SUFFIX}",
            "",
        )
    hint = task.get("model_hint")
    if isinstance(hint, str) and hint.strip() and hint.strip() != "auto" and ":" in hint:
        return hint.strip(), f"tasks[{task_id}].model_hint", ""
    tier = str(task.get("capability_tier") or "full")
    spec, layer = resolve_subagent_runner(
        tier, anchor=anchor, skip_session=skip_session
    )
    driver_key = "driver.subagent_runner_cheap" if tier == "cheap" else "driver.subagent_runner"
    return spec, f"{driver_key} ({layer})", layer


def _is_session_model(
    provider_name: str, model: str, *, anchor: Optional[str] = None
) -> bool:
    """Whether ``provider:model`` is the host session's own model, whoever named it.

    The configured catalog is the operator's fan-out list; the session's model
    is by definition one the host is already running, so "not configured" is
    never news about it — on whichever rung, or under whichever recorded key,
    it arrives. Answers ``False`` whenever the session rung cannot answer, so a
    host with no session model keeps the warning exactly as it was.
    """
    try:
        session = session_runner()
        if not session:
            return False
        session_provider, session_model = parse_model_spec(session, anchor=anchor)
    except Exception:  # noqa: BLE001 - an advisory exemption never ends a run
        return False
    return (session_provider, session_model) == (provider_name, model)


def _registry_module() -> Any:
    try:  # pragma: no cover - import shim mirrors the rest of utils/
        from . import provider_registry
    except ImportError:  # pragma: no cover - direct-script import shim
        import utils.provider_registry as provider_registry  # type: ignore[no-redef]
    return provider_registry


def _effort_stripped(provider: Any, model: str) -> str:
    """``model`` without a trailing ``:effort`` the adapter accepts."""
    hook = getattr(provider, "_accepted_efforts", None)
    try:
        efforts = hook() if callable(hook) else ()
    except Exception:  # noqa: BLE001 - an advisory read never ends a run
        efforts = ()
    base, _effort = split_reasoning_effort(str(model or ""), efforts or ())
    return base.strip()


def _in_operator_roster(
    provider_name: str, provider: Any, model: str, *, anchor: Optional[str] = None
) -> bool:
    """Whether ``provider:model``, effort suffix stripped from both sides, is in
    the operator's own roster or in ``<provider>.models`` (plan §6.1,
    2026-09-24).

    The roster is ``defaults.quick_models`` + ``defaults.models`` of the
    **effective** config — the same project-layer-resolved ``providers.yaml``
    ``is_model_valid(spec, anchor=anchor)`` reads the catalog from — so a
    project that narrowed its roster and left the model out keeps the warning.
    ``codex:gpt-6-astra`` matches the roster entry ``codex:gpt-6-astra:xhigh``;
    a typo'd id, suffixed or not, matches neither and stays warned.
    """
    wanted = _effort_stripped(provider, model)
    if not wanted:
        return False
    try:
        config = _registry_module().load_config(anchor=anchor)
    except Exception:  # noqa: BLE001 - an advisory read never ends a run
        return False
    defaults = config.get("defaults") or {}
    roster: List[str] = []
    for key in ("quick_models", "models"):
        value = defaults.get(key) or []
        if isinstance(value, list):
            roster += [entry for entry in value if isinstance(entry, str)]
    for entry in roster:
        try:
            entry_provider, entry_model = parse_model_spec(entry, anchor=anchor)
        except Exception:  # noqa: BLE001
            continue
        if entry_provider == provider_name and _effort_stripped(provider, entry_model) == wanted:
            return True
    block = (config.get("providers") or {}).get(provider_name) or {}
    catalog = block.get("models") if isinstance(block, dict) else None
    if isinstance(catalog, list):
        for entry in catalog:
            name = entry.get("name") if isinstance(entry, dict) else entry
            if isinstance(name, str) and _effort_stripped(provider, name) == wanted:
                return True
    return False


def _catalog_file_for_warning(anchor: Optional[str] = None) -> str:
    """The ``providers.yaml`` an operator edits to quiet the catalog warning:
    the project layer's resolved path, else the env layer's, else the base
    file — never ``hosts/capabilities.yaml``, whose pin follows the roster."""
    registry = _registry_module()
    try:
        layers = dict(registry._override_paths(anchor))
    except Exception:  # noqa: BLE001 - an advisory read never ends a run
        layers = {}
    for name in ("project", "env"):
        path = layers.get(name)
        if path is not None:
            try:
                return str(Path(path).resolve())
            except OSError:
                return str(path)
    return str((Path(registry.__file__).parent.parent / "providers.yaml").resolve())


def preflight_runner(
    spec: str,
    *,
    profile: str = PROFILE_AGENT_READONLY,
    key: str = "driver.subagent_runner",
    anchor: Optional[str] = None,
    check_version: bool = True,
    layer: Optional[str] = None,
    check_auth: bool = True,
    check_nested: bool = True,
    probe_nested: bool = True,
    jail_request: Optional[JailRequest] = None,
) -> Dict[str, Any]:
    """Validate one runner spec; detect version, auth and nested-exec (D3c/D3m).

    Checks, earliest wins: the provider has an adapter, the model spec is valid
    for that provider, the adapter declares the requested profile, and (for a
    ``workspace-read`` phase) it declares ``supports_workspace_reads``. Then
    ``version_cmd`` runs once and its result is cached for the process: below
    ``min_version`` is a hard exit-3 refusal before any child is dispatched, above
    ``verified_version`` is a one-line warning (blocking on new releases would rot
    faster than the CLIs do), and unparseable output is recorded ``unknown`` with
    the same warning.

    The adapter's ``auth_check`` runs in the same preflight and is cached the same
    way (D3c): **installed is not authenticated** — every ``is_available()`` is a
    bare ``shutil.which``, so a logged-out CLI passes detection and would
    otherwise be discovered one spawned child at a time, once per task in the
    batch. A recognized login notice is exit 3 here, before anything is
    dispatched; anything the probe cannot read (no ``auth_check`` declared, the
    subcommand missing, the probe itself failing) is recorded ``unknown`` and
    never blocks, leaving the reactive ``auth_error_patterns`` path (rung 1) to
    catch it.

    Last comes the host's own ``nested_exec`` verdict (D3c), because presence,
    version and auth all describe the *runner* and none of them answers whether
    this host lets a third-party CLI run inside it with network and credentials
    intact. A declared ``denied`` leg is exit 3 naming the field — dispatching
    into a sandbox that eats the failure would spend the retry budget on every
    task in the batch — and a leg the data records as ``unknown`` or
    ``needs-config`` is *probed*, once per distinct host/runner/run, with one
    throwaway ``agent-readonly`` dispatch whose recognized denials (a refused
    spawn, an egress block, a credential notice from inside the sandbox) are the
    same exit 3 before anything is scheduled. An inconclusive probe is recorded
    ``unknown`` and never blocks, exactly like the version and auth probes.
    ``probe_nested=False`` keeps the declared verdict and suppresses only that
    throwaway dispatch — it is what ``--dry-run-subagents`` passes, because the
    probe is a real turn and "start no child" (D3l) means it.

    Between the catalog leg and the host's verdict sits the D6 sandbox
    self-test: an adapter that puts an OS sandbox between the model and the
    filesystem (codex, through bubblewrap) declares a model-free
    ``sandbox_probe_command`` for **every** profile it dispatches — the
    read-only one too, because a bwrap that cannot start denies a read dispatch
    the repository it was sent to read — and a non-zero exit is exit 3 here,
    ``sandbox_unavailable``, before the first dispatch of that profile. Cached
    per host/spec/profile; a timeout is ``unknown`` and dispatches.

    ``jail_request`` (plan codex-sandbox-unavailable step 3, 2026-09-30) is a
    write dispatch's grant — its kind, write scope and target — which the
    sandbox leg needs to decide whether the plugin's Landlock jail may take
    the dispatch: the scope joins the decision key, and the rung probe's
    positive control writes the target. Read profiles need none.

    Returns:
        ``{"provider", "model", "version", "auth", "nested_exec", "sandbox",
        "usage_support", "profile"}``.

    Raises:
        RunnerRejected: exit 3, through the one rejection formatter.
    """
    provider_name, model = parse_model_spec(spec, anchor=anchor)
    provider = get_provider(provider_name)
    if provider is None:
        raise _render_runner_rejection(
            key=key, spec=spec, reason_code="unknown_provider", profile=profile
        )
    if not provider.supports_profile(profile):
        raise _render_runner_rejection(
            key=key, spec=spec, reason_code="missing_profile", profile=profile,
            detail=(
                f"{provider_name} declares "
                f"{', '.join(provider.agent_profiles) or 'no profiles'}."
            ),
        )
    if not provider.is_available():
        raise _render_runner_rejection(
            key=key, spec=spec, reason_code="binary_absent", profile=profile,
        )
    # R3 — a *structural* refusal, which is a different predicate from the
    # catalog warning below and must be kept different. The adapter is asked
    # whether its own addressing scheme can express this model token at all;
    # only an adapter that can answer that question declares the hook (opencode
    # resolves `provider/model` and a bare token yields an empty model half), and
    # the answer never comes from a catalog. A catalog that is empty, stale or
    # unreadable can therefore only ever downgrade the *warning* below to
    # silence — it can never produce an exit.
    describe_unresolvable = getattr(provider, "describe_unresolvable_model", None)
    if callable(describe_unresolvable):
        # Plan §8 T8.3: `profile` and `anchor` let opencode answer the hermetic
        # reconstructibility question here, ahead of the auth leg, so a
        # user-config-only provider gets the `config_providers` sentence rather
        # than "run `opencode auth login`". A narrow double declaring only
        # `(model)` keeps working through the TypeError fallback.
        try:
            try:
                unresolvable = describe_unresolvable(
                    model, profile=profile, anchor=anchor
                )
            except TypeError:
                unresolvable = describe_unresolvable(model)
        except Exception:  # noqa: BLE001 - a diagnostic may not break a preflight
            unresolvable = None
        if unresolvable:
            raise _render_runner_rejection(
                key=key, spec=spec, reason_code="unresolvable_model",
                profile=profile, detail=str(unresolvable),
            )
    # A catalog problem downgrades to "no warning", never to an exit (R3): the
    # catalog is advisory here, and a read that fails says nothing about whether
    # the runner can serve this model.
    try:
        catalogued = is_model_valid(spec, anchor=anchor)
    except Exception:  # noqa: BLE001 - an advisory read may not end a run
        catalogued = True
    # The session rung is exempt: the configured catalog is the operator's list
    # of fan-out models in providers.yaml, and the session's own model is by
    # definition one the host is already running — warning that it is "not
    # configured" told an opencode user their selected model was suspect on
    # every run. The live catalog leg (`_detect_model`) still judges it.
    # The exemption is keyed on the *model* as well as on the rung: the same
    # model reaches this function under other keys — the generate-tasks
    # orchestrator's own preflight, and `tasks[<id>].runner (recorded from a
    # previous attempt)` on a re-invocation — and each of those printed the
    # warning the session rung had just been excused from (measured
    # 2026-09-14, twice per `generate-tasks` retry).
    # Plan §6.1 (2026-09-24): the operator's own roster exempts too, under every
    # key — the host-capabilities pin included, whose comment says it "follows
    # the roster" — matched with the effort suffix stripped from both sides
    # (`codex:gpt-6-astra` is `codex:gpt-6-astra:xhigh`'s model). The roster is
    # the effective config's, never the base file's alone.
    if (
        not catalogued
        and layer != SESSION_LAYER
        and not _is_session_model(provider_name, model, anchor=anchor)
        and not _in_operator_roster(provider_name, provider, model, anchor=anchor)
    ):
        print(
            f"multi-llm warning: {key} names model {model!r}, which is not in "
            f"{provider_name}'s configured catalog — dispatching anyway. Add it "
            f"to `{provider_name}.models` (or to `defaults.quick_models` / "
            f"`defaults.models`) in {_catalog_file_for_warning(anchor)}.",
            file=sys.stderr,
        )

    info = {
        "provider": provider_name,
        "model": model,
        "profile": profile,
        "usage_support": provider.usage_support,
        "version": "unknown",
        "auth": "unknown",
        "nested_exec": "unknown",
        "sandbox": "unknown",
    }
    if check_version:
        info["version"] = _detect_version(provider_name, key=key, spec=spec, profile=profile)
    if check_auth:
        info["auth"] = _detect_auth(
            provider_name, model, key=key, spec=spec, profile=profile,
            anchor=anchor,
        )
    # D3 step 3 — the CLI's own catalog, after version and auth and before
    # nested-exec: a too-old CLI, or a logged-out one running a model that needs
    # a credential, is already a refusal and neither can produce a trustworthy
    # listing. A credential-free id exempted by the auth leg does reach here.
    # Gated on `check_auth` and `check_version` alike, because a caller that
    # asked for neither probe asked for no CLI spawn at all.
    if check_version or check_auth:
        info["model_catalog"] = _detect_model(
            provider_name, model, key=key, spec=spec, profile=profile, anchor=anchor
        )
        # D6 step 3 — the runner's own OS sandbox, exercised where the batch
        # would run it, with no model involved. Only an adapter that declares a
        # command for this profile is probed (codex, for every profile it
        # dispatches — read-only included, since that is the same bubblewrap);
        # everything else records `not-required`. Same gate as the catalog
        # leg: a caller that asked for no CLI spawn gets none.
        info["sandbox"] = _detect_sandbox(
            provider_name, key=key, spec=spec, profile=profile, anchor=anchor,
            **({"jail_request": jail_request} if jail_request is not None else {}),
        )
    if check_nested:
        info["nested_exec"] = _detect_nested_exec(
            provider_name, model,
            key=key, spec=spec,
            # The version probe already started this CLI as a child of the host's
            # own shell, so a parsed version is a *spawn* observation and the
            # throwaway dispatch has one less leg to answer for.
            spawn_observed=info["version"] != "unknown",
            probe=probe_nested,
        )
    return info


#: Process-local version cache: detected once per *distinct* runner, never per
#: dispatch (D3m).
_VERSION_CACHE: Dict[str, str] = {}

#: The same, for the D3c auth probe: ``ok`` | ``unknown`` | ``not-required`` |
#: ``config``, keyed ``<provider>|<needs-credentials 0/1>|<profile>|<model
#: prefix>|<hermetic/plain>`` — NOT by bare provider name (D3 step 2): one
#: process holding both ``opencode/big-pickle`` and ``openrouter/deepseek/…``
#: would otherwise serve one's verdict to the other. The profile joined the key
#: with T8.13 (the probe runs under that profile's dispatch env), and the model
#: prefix and hermeticity with T8.4 (whether a config declares the provider
#: depends on both). A failed probe is never cached — it raises, and the run
#: ends.
_AUTH_CACHE: Dict[str, str] = {}

#: The same, for the D3c nested-exec verdict, keyed by ``<host id>|<runner spec>``
#: rather than by provider: the question is about the *pair*, and a host that
#: denies one runner's egress may hand another its own bundled CLI. A denial is
#: never cached either — it raises.
_NESTED_CACHE: Dict[str, str] = {}

#: The same, for the D3 step 3 catalog leg: ``ok`` | ``unknown`` per
#: ``<provider>|<hermetic on/off>|<config-content digest>|<normalized model>``
#: — not provider+model, because the effective configuration changes the
#: answer, and a hermetic and a non-hermetic slot in one process must not share
#: a verdict. A refusal is never cached — it raises.
_MODEL_CACHE: Dict[str, str] = {}

#: The executor's per-runner sandbox **decision** for the D6 self-test: ``ok``
#: | ``unknown`` | ``not-required`` | a **rung id** per ``<host id>|<runner
#: spec>|<profile>``. Not a probe cache — the measurement lives in the one
#: probe cache both lanes share (:data:`_SANDBOX_PROBE_CACHE`, 2026-09-24);
#: this records only what the preflight *decided* from it, so
#: :func:`sandbox_rung` can hand the rung id to every dispatch of that runner
#: under that profile — the id, never a bool, because the dispatch must render
#: *that* rung and a bool cannot say which. A refusal is never recorded — it
#: raises. A rung id (``landlock``, ``unsandboxed``) is the one
#: ``unavailable`` that did not raise. Recorded so the notice prints once per
#: runner rather than once per batch.
_SANDBOX_DECISIONS: Dict[str, str] = {}

#: The **one** per-process sandbox probe cache (plan §3.6, 2026-09-24),
#: replacing the fan-out's ``_FANOUT_SANDBOX_CACHE`` and this module's old
#: verdict-word cache, which cached separately and so could probe one codex
#: version twice. Values are the whole :class:`SandboxProbeResult` — walk,
#: per-rung probe tails and CLI version included — so a cache hit renders the
#: same ``[SANDBOX_BYPASSED]`` line as the cold probe that filled it. Two key
#: shapes, both tuples:
#:
#: * ``("verdict", host, provider, profile, cwd, version, policy)`` — one
#:   profile's probe plus its walk, as :func:`cached_sandbox_verdict` returns it;
#: * ``("walk", host, provider, cwd, version, rung ids)`` — the fallback walk
#:   alone. The rung probes do not depend on the profile (``generate`` and
#:   ``agent-readonly`` declare the same ladder), so the fan-out and the
#:   executor share **one** rung probe per codex version; the profiles' own
#:   probes differ (one writes a byte, the other does not) and stay per profile.
_SANDBOX_PROBE_CACHE: Dict[Tuple[str, ...], "SandboxProbeResult"] = {}

#: Guards :data:`_SANDBOX_PROBE_CACHE` for the dict read and write only; the
#: probe itself runs under a per-key lock (:func:`_sandbox_probe_lock`), so one
#: provider's slow probe never holds up another provider's slot (F5,
#: 2026-09-17). A ``threading.Lock``: the fan-out runs the blocking probe in a
#: worker thread, and one process may drive more than one event loop.
_SANDBOX_PROBE_LOCK = threading.Lock()
_SANDBOX_PROBE_KEY_LOCKS: Dict[Tuple[str, ...], threading.Lock] = {}

#: The CLI version the sandbox probe keys on, per provider, when the version
#: preflight (:data:`_VERSION_CACHE`) has not already read it. Read only for an
#: adapter whose ladder declares a ``removed_at`` rung, so every other adapter
#: spawns nothing extra.
_PROBE_VERSION_CACHE: Dict[str, str] = {}
#: One lock per provider around that version spawn, so two specs of one
#: provider probed concurrently (``asyncio.to_thread``) spawn it once.
_PROBE_VERSION_LOCKS: Dict[str, threading.Lock] = {}

#: ``<provider>|<version>`` pairs whose retirement line (a contained rung
#: measured unavailable from this build) this process already printed.
_RETIREMENTS_ANNOUNCED: Set[str] = set()

#: What :func:`_detect_sandbox` returns (and ``preflight_runner`` records as
#: ``info["sandbox"]``) for the uncontained rung — the word it has always been.
#: The decision record (:data:`_SANDBOX_DECISIONS`) stores the rung id; this word is derived from exactly
#: :data:`SANDBOX_RUNG_UNSANDBOXED` and nothing else.
SANDBOX_STATE_BYPASSED = "bypassed"

#: The recorded states that are **not** a rung id.
_PLAIN_SANDBOX_STATES = frozenset({"ok", "unknown", "not-required"})

#: The decision word for plan step 6 (F5, user decision 2026-09-30): a WRITE
#: dispatch on the uncontained rung, taken only because the chat itself runs
#: with the ``danger-full-access`` posture and the plugin-landlock rung could
#: not take the dispatch. Its own word, never the rung id, so nothing that
#: replays a decision can mistake it for a read phase's bypass; it is stored
#: only under a key that carries the posture (:func:`_sandbox_decision_key`),
#: so a later call without that posture never finds it. :func:`sandbox_rung`
#: hands the dispatch ``unsandboxed`` for it.
SANDBOX_DECISION_WRITE_BY_CONSENT = "unsandboxed-by-consent"

#: Per decision key, what the executor-lane ``[SANDBOX_INCIDENTAL]`` line of a
#: write dispatch on the plugin-landlock rung is built from — ``(provider,
#: rung id, policy, standard probe tail, walk clause)`` — so the scheduler can
#: print it before each batch (:func:`write_rung_notice`). No path: the write
#: target is rendered from the caller's request at print time.
_SANDBOX_NOTICE_PARTS: Dict[str, Tuple[str, str, Optional[str], str, str]] = {}

#: Lines the run's closing summary repeats (F1 item 6 and Limits): every
#: ``[JAIL_DENIED]`` and ``[CODEX_HOME_CHECK]`` line this process printed,
#: plus the trust-entry notes rendered only when the summary prints
#: (``landlock_dispatch.TrustEntriesNote``). Per process, like the probe
#: cache; :func:`jail_summary_lines` renders it and :func:`run_tasks` prints
#: the ones its own batch added (counted by :func:`jail_summary_count`).
_JAIL_SUMMARY_LINES: List[Any] = []
_JAIL_SUMMARY_LOCK = threading.Lock()

#: How many jailed codex children of this process are live, and how many have
#: started, so a ``[CODEX_HOME_CHECK]`` line can say how many *other* children
#: could also have made the change it reports.
_JAILED_CHILDREN = {"live": 0, "started": 0}


def _sandbox_decision_key(
    spec: str,
    profile: str,
    write_scope: Optional[str] = None,
    consent: Optional[WritePostureConsent] = None,
) -> str:
    """``<host>|<spec>|<profile>``, plus ``|<scope>`` for a write profile that
    carries one, plus ``|<posture>`` when the chat's F5 consent is present.

    The scope keeps a ``plan-file`` decision from ever being replayed for a
    ``repo-wide`` dispatch of the same runner; the posture keeps an F5
    decision from ever being replayed for a call without the posture (it is
    read per call from ``os.environ``, plan step 6). Read-only keys are
    unchanged. Never a path.
    """
    key = f"{_current_host_id()}|{spec}|{profile}"
    if profile in SANDBOX_WRITE_FALLBACK_PROFILES:
        if write_scope:
            key += f"|{write_scope}"
        if consent is not None:
            key += f"|{consent.posture}"
    return key


def sandbox_rung(
    spec: str, profile: str, write_scope: Optional[str] = None
) -> Optional[str]:
    """The fallback rung id the preflight recorded for this runner and profile,
    or ``None``.

    Read by :func:`dispatch_task` (and the dry-run preview) to hand
    ``sandbox_fallback=<rung id>`` to the argv build, which renders that rung.
    Strictly the cache, never a fresh probe or a config read: the decision was
    taken once, in :func:`_detect_sandbox`, with every gate in hand, and a
    dispatch may only replay it. A runner the preflight never saw (or saw
    under another profile) is ``None`` and renders the argv it always did.

    ``write_scope`` (plan step 3, 2026-09-30) selects a write profile's
    decision: one taken for ``plan-file`` is never replayed for ``repo-wide``.
    An F5 decision (plan step 6) is found only while the chat's
    ``danger-full-access`` posture is in this process's environment, and is
    handed out as ``unsandboxed``.
    """
    consent = (
        host_write_posture_consent()
        if profile in SANDBOX_WRITE_FALLBACK_PROFILES else None
    )
    keys = [_sandbox_decision_key(spec, profile, write_scope, consent)]
    if consent is not None:
        # A decision taken without the posture (the plugin-landlock rung, say)
        # is valid with it too; the reverse never holds, and the F5 word is
        # only ever stored under a key that carries the posture.
        keys.append(_sandbox_decision_key(spec, profile, write_scope, None))
    for key in keys:
        recorded = _SANDBOX_DECISIONS.get(key)
        if not recorded or recorded in _PLAIN_SANDBOX_STATES:
            continue
        if recorded == SANDBOX_DECISION_WRITE_BY_CONSENT:
            return SANDBOX_RUNG_UNSANDBOXED if consent is not None else None
        return recorded
    return None


def jail_summary_count() -> int:
    """How many entries the closing summary holds so far: the mark a caller
    takes before its batch and hands :func:`jail_summary_lines` after it."""
    with _JAIL_SUMMARY_LOCK:
        return len(_JAIL_SUMMARY_LINES)


def jail_summary_lines(start: int = 0) -> List[str]:
    """Every ``[JAIL_DENIED]`` / ``[CODEX_HOME_CHECK]`` line this process
    recorded from entry ``start`` on, in order, for a run's closing summary
    (plan F1 item 6, Limits). Trust-entry notes are rendered now and merged
    per home (``landlock_dispatch.render_summary_entries``): a table gone
    again by now is left out."""
    with _JAIL_SUMMARY_LOCK:
        entries = list(_JAIL_SUMMARY_LINES[start:])
    return landlock_dispatch.render_summary_entries(entries)


def _record_jail_line(line: Any, *, echo: bool = True) -> None:
    """Print ``line`` (the run log) and keep it for the closing summary."""
    with _JAIL_SUMMARY_LOCK:
        _JAIL_SUMMARY_LINES.append(line)
    if echo:
        print(f"[exec-subagents] {line}")


def sandbox_bypassed(spec: str, profile: str) -> bool:
    """Whether the preflight recorded the **uncontained** rung for this runner
    and profile — rung 2 exactly, never a contained rung."""
    return sandbox_rung(spec, profile) == SANDBOX_RUNG_UNSANDBOXED


def _sandbox_state_word(recorded: str) -> str:
    """The ``info["sandbox"]`` word for a cached state: ``bypassed`` for the
    uncontained rung (unchanged since D6) — an F5 write decision included,
    since that is the same rung — the recorded value otherwise."""
    if recorded in (SANDBOX_RUNG_UNSANDBOXED, SANDBOX_DECISION_WRITE_BY_CONSENT):
        return SANDBOX_STATE_BYPASSED
    return recorded


def reset_version_cache() -> None:
    """Clear the per-process runner-version, auth, catalog, nested-exec and
    sandbox caches (tests)."""
    _VERSION_CACHE.clear()
    _AUTH_CACHE.clear()
    _NESTED_CACHE.clear()
    _MODEL_CACHE.clear()
    reset_sandbox_cache()


def reset_sandbox_cache() -> None:
    """Clear the per-process sandbox probe cache and decisions (tests)."""
    _SANDBOX_DECISIONS.clear()
    _SANDBOX_NOTICE_PARTS.clear()
    with _JAIL_SUMMARY_LOCK:
        _JAIL_SUMMARY_LINES.clear()
    _SANDBOX_PROBE_CACHE.clear()
    _SANDBOX_PROBE_KEY_LOCKS.clear()
    _PROBE_VERSION_CACHE.clear()
    _PROBE_VERSION_LOCKS.clear()
    _RETIREMENTS_ANNOUNCED.clear()


def reset_auth_cache() -> None:
    """Clear the per-process runner-auth cache (tests)."""
    _AUTH_CACHE.clear()


def reset_model_cache() -> None:
    """Clear the per-process model-catalog cache (tests)."""
    _MODEL_CACHE.clear()


def reset_nested_exec_cache() -> None:
    """Clear the per-process nested-exec cache (tests)."""
    _NESTED_CACHE.clear()


# The version comparison this module used to own (`_version_tuple`) is gone:
# M14 (§5.4) merged it with the twin in `providers/base.py` so the preflight's
# refusal and `describe_availability`'s label are computed from one rule. The
# floor, the ceiling and the above-verified warning now all come back from
# `version_verdict`, which is imported above.


def _preflight_version(provider: Any) -> Optional[str]:
    """The version :func:`_detect_version` already read for this provider, or None.

    Strictly the cache (:data:`_VERSION_CACHE`), never a spawn: it is read on
    the dispatch path, once per dispatch, and handed to the adapter's dispatch
    context so a version-gated config key (opencode's
    ``continue_loop_on_deny``, plan T4.2) costs nothing beyond the preflight's
    one ``version_cmd`` per process. A recorded ``"unknown"`` is passed through
    as itself, so the adapter can tell "the read failed" from "no read here".
    """
    try:
        name = provider.name
    except Exception:  # noqa: BLE001 - a lookup may never end a dispatch
        return None
    return _VERSION_CACHE.get(name) if isinstance(name, str) else None


def _run_probe(
    argv: Sequence[str], env: Optional[Mapping[str, str]] = None
) -> Optional["subprocess.CompletedProcess"]:
    """Run one cheap preflight argv (``version_cmd`` / ``auth_check``).

    Returns ``None`` when the probe could not be run at all, which every caller
    reads as "unknown": a preflight probe reports, it never blocks on its own
    failure.

    ``env`` (plan §8 T8.13) is the environment the probe runs under; ``None``
    inherits this process's, which is what every caller but the auth leg
    passes. The auth leg hands in :func:`dispatch_child_env`'s result, so the
    probe sees what a dispatch would.
    """
    launcher, _ = _resolve_executable(argv[0])
    kwargs: Dict[str, Any] = {}
    if env is not None:
        kwargs["env"] = dict(env)
    try:
        return subprocess.run(
            [*launcher, *argv[1:]],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            stdin=subprocess.DEVNULL,
            **kwargs,
        )
    except (OSError, subprocess.SubprocessError):
        return None


def dispatch_child_env(
    provider: Any,
    model: str,
    profile: str,
    *,
    anchor: Optional[str] = None,
    cwd: Optional[str] = None,
) -> Optional[Dict[str, str]]:
    """The child environment one spawn of ``provider`` gets (plan §8 T8.13).

    ``resolve_env`` + ``build_child_env`` and nothing else: the two calls
    :func:`_spawn_in_context` makes, factored out so the auth probe and
    opencode's ``debug config`` reader (T8.3) see what a dispatch sees — the
    adapter's delta, the ``env_allowlist`` filter and the running host's
    ``env_guards``. ``None`` means "inherit this process's environment
    unchanged", exactly as :func:`build_child_env` returns it.

    Not pure for every adapter: cursor-agent's ``resolve_env`` creates its
    run-scoped profile directory (or arms its side-effect guard), both bounded
    and idempotent per process. Callers outside a dispatch therefore build it
    at most once per cache key and never hand one call's result to another
    spawn.
    """
    provider_env = expand_env_home(
        provider.resolve_env(model, profile, anchor=anchor, cwd=cwd)
    )
    host_guards, passthrough = _host_env_guards()
    return build_child_env(
        provider,
        provider_env=provider_env,
        host_guards=host_guards,
        host_passthrough=passthrough,
        anchor=anchor,
    )


def _detect_version(
    provider_name: str, *, key: str, spec: str, profile: str
) -> str:
    """Run ``version_cmd`` once per provider and apply the shared gate (D3m).

    The probe is this module's; the **verdict is not**. Both bounds — the
    ``min_version`` floor and M14's ``max_version_exclusive`` ceiling — plus the
    advisory above-``verified_version`` warning come back from
    ``providers.base.version_verdict``, which is the same rule
    ``describe_availability`` labels a runner with (§5.4). Reading the streams
    **concatenated** is :meth:`parse_version`'s job, and it is why a CLI that
    banners its version to stderr is read at all.
    """
    if provider_name in _VERSION_CACHE:
        return _VERSION_CACHE[provider_name]

    provider = get_provider(provider_name)
    version = "unknown"
    argv = list(getattr(provider, "version_cmd", ()) or ())
    if argv:
        completed = _run_probe(argv)
        if completed is not None:
            parsed = provider.parse_version(completed.stdout, completed.stderr)
            if parsed:
                version = parsed

    if version == "unknown":
        if argv:
            print(
                f"multi-llm warning: could not determine the {provider_name} "
                f"version from `{' '.join(argv)}` — recording 'unknown'. A CLI "
                f"that dropped --version still answers prompts, so this is not a "
                f"blocker, but a stream-shape failure will not name a build.",
                file=sys.stderr,
            )
    else:
        verdict = version_verdict(provider, version, name=provider_name)
        if verdict.refuses:
            # A build outside the declared range is a refusal before any child,
            # not a degraded run: the adapter's parser was written against a
            # stream shape this build does not produce.
            raise _render_runner_rejection(
                key=key, spec=spec, reason_code="missing_capability",
                profile=profile, detail=verdict.detail,
            )
        if verdict.detail:
            # Above `verified_version` — a warning, never a block: blocking on
            # new releases would rot faster than the CLIs do.
            print(f"multi-llm warning: {verdict.detail}", file=sys.stderr)

    _VERSION_CACHE[provider_name] = version
    return version


#: A CSI or OSC terminal escape — enough to tell a stream that carries only
#: colour resets from one that says something.
_PROBE_ESCAPE = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)")


def _probe_verdict_stream(
    completed: Optional["subprocess.CompletedProcess"],
) -> str:
    """The stream a ``not_authenticated`` refusal should quote.

    stderr when it says anything, else stdout. "Says anything" is judged with
    terminal escapes removed, because a bare ``stderr or stdout`` quoted
    opencode 1.18.32's stderr — which is exactly ``"\\x1b[0m\\n"``, a colour
    reset and nothing else — while the ``└  0 credentials`` line the verdict was
    drawn from sat on stdout. The refusal then told its reader the probe had
    printed nothing, which is how a correct refusal was first mis-diagnosed as
    a parser break (measured in the container lane, 2026-09-25).
    """
    if completed is None:
        return ""
    stderr = completed.stderr or ""
    if _PROBE_ESCAPE.sub("", stderr).strip():
        return stderr
    return completed.stdout or stderr


#: A variable name shaped like a credential, for the one sentence that names
#: what ``env_allowlist`` (or a host guard) dropped from the probe's env. Names
#: only, never values.
_CREDENTIAL_NAME = re.compile(
    r"(?:API_KEY|_TOKEN|_SECRET|ACCESS_KEY|_KEY)$", re.IGNORECASE
)


def _accepts_keyword(func: Callable[..., Any], name: str) -> bool:
    """Does ``func`` take ``name`` as a keyword (explicitly or via ``**kwargs``)?

    The F6 rule, applied to an optional hook or argument: a stand-in patched
    over :func:`_run_probe` (a narrow ``(argv)`` test double) or
    ``dispatch_task`` is never handed a keyword it does not accept. A callable
    whose signature cannot be read is treated as not accepting it.
    """
    try:
        params = inspect.signature(func).parameters.values()
    except (TypeError, ValueError):
        return False
    return any(
        param.kind is inspect.Parameter.VAR_KEYWORD
        or (param.name == name and param.kind in (
            inspect.Parameter.KEYWORD_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        ))
        for param in params
    )


def _auth_cache_key(
    provider: Any,
    provider_name: str,
    model: str,
    *,
    needs_auth: bool,
    profile: str,
    anchor: Optional[str],
) -> str:
    """``<provider>|<needs 0/1>|<profile>|<model prefix>|<hermetic/plain>``.

    The prefix is the model's ``provider/`` half after the ``:effort`` split
    (empty for a bare token); hermeticity is asked of the adapter's module the
    way :func:`_model_cache_key` asks it. Every leg degrades to a constant: a
    cache key may never be what ends a preflight.
    """
    normalized = model or ""
    try:
        normalized, _ = split_reasoning_effort(
            normalized, provider._accepted_efforts()  # noqa: SLF001 - the base's hook
        )
    except Exception:  # noqa: BLE001
        normalized = model or ""
    normalized = normalized.strip()
    prefix = normalized.split("/", 1)[0] if "/" in normalized else ""
    hermetic = "plain"
    try:
        module = sys.modules.get(type(provider).__module__)
        enabled = getattr(module, "hermetic_enabled", None)
        if callable(enabled) and enabled(profile, anchor):
            hermetic = "hermetic"
    except Exception:  # noqa: BLE001
        hermetic = "plain"
    return (
        f"{provider_name}|{1 if needs_auth else 0}|{profile}|{prefix}|"
        f"{hermetic}"
    )


def _dropped_credential_names(child_env: Optional[Mapping[str, str]]) -> List[str]:
    """Credential-shaped names this process carries that the probe env lacks."""
    if child_env is None:
        return []
    return sorted(
        name for name in os.environ
        if name not in child_env and _CREDENTIAL_NAME.search(name)
    )


def _detect_auth(
    provider_name: str,
    model: str = "",
    *,
    key: str,
    spec: str,
    profile: str,
    anchor: Optional[str] = None,
    cwd: Optional[str] = None,
) -> str:
    """Run ``auth_check`` once per cache key and refuse a logged-out CLI (D3c).

    Returns ``"ok"``, ``"unknown"``, ``"not-required"`` or ``"config"``; a
    recognized login/credential notice raises instead, because every sibling
    task in the batch would fail identically and no retry can fix a missing
    credential. ``unknown`` is the honest answer for a CLI that declares no
    probe (claude-code has no non-interactive status subcommand) or whose probe
    could not be read — never an assumption of success.

    ``model`` is what decides whether a ``False`` verdict is *allowed to refuse*
    (D3 step 2). On a CLI that fronts several vendors "needs a credential" is a
    property of the model, not of the binary, so the adapter is asked
    ``model_needs_credentials(model)``: when it declares the model credential-free
    the probe still runs and its verdict is still recorded (status keeps its
    evidence) but the refusal is skipped and the leg reads ``not-required``. A
    ``True``/``None`` verdict is untouched either way, and a credential-requiring
    spec on the same provider in the same process still refuses — the cache is
    keyed on the answer, not on the provider alone.

    **The probe runs under the dispatch's env (plan §8 T8.13).** On a cache
    miss, and only then, :func:`dispatch_child_env` builds what a dispatch of
    this model under ``profile`` would get — the adapter's delta, the
    ``env_allowlist`` filter, the host's ``env_guards`` — and ``auth_check``
    runs under it; ``cwd`` (default: the repo root the dispatch pins) is what
    ``resolve_env`` and the config hook see, not the probe's working directory
    (every probe adapter's status command reads a fixed store). A key the
    allowlist drops is therefore not counted as a login, and the refusal says
    so by name. An env that cannot be built never turns a refusal into a pass:
    the probe runs under the inherited environment, but only its ``False`` is
    kept (a ``True`` reads ``unknown``) and the config leg is not asked. The probe deliberately runs **outside**
    ``hermetic_dispatch``: the slot's delta redirects only ``XDG_CONFIG_HOME``
    and cannot hide ``auth.json`` (``XDG_DATA_HOME`` passes through), and
    entering it would turn a user-config-only provider into a skipped probe
    instead of the structural leg's ``unresolvable_model`` sentence.

    **The config leg (T8.4).** When the verdict is ``False`` for a model that
    needs a credential, the adapter's ``config_credential_source`` is asked
    whether the dispatch's own resolved config declares the provider (opencode:
    a custom provider, or a built-in override whose key resolves in the
    dispatch env). ``declared``
    records ``config`` and refuses nothing; ``unknown`` is today's refusal.
    Lazy: a ``True`` verdict never spawns it.
    """
    provider = get_provider(provider_name)
    needs_credentials = _model_needs_credentials(provider, model)
    cache_key = _auth_cache_key(
        provider, provider_name, model,
        # Keyword named `needs_auth`: the same-name credentials keyword form
        # trips the redaction-looseness tripwire in test_redaction.py.
        needs_auth=needs_credentials, profile=profile, anchor=anchor,
    )
    if cache_key in _AUTH_CACHE:
        return _AUTH_CACHE[cache_key]

    argv = list(getattr(provider, "auth_check", ()) or ())
    if not argv:
        _AUTH_CACHE[cache_key] = "unknown"
        return "unknown"

    probe_cwd = cwd if cwd is not None else _probe_cwd(anchor)

    def build_env() -> Optional[Dict[str, str]]:
        # Built only on this cache miss, immediately before its spawn, and never
        # handed to a dispatch: cursor-agent's `resolve_env` has a bounded side
        # effect, and a hermetic delta belongs to one spawn. A failure raises:
        # `None` already means "inherit this process's env", so swallowing it
        # into `None` would run the probe (or the config hook's `debug config`)
        # with neither the delta nor the `env_allowlist`, counting a key the
        # dispatch will never see as a login. The config hook's own catch-all
        # turns the raise into `unknown`.
        return dispatch_child_env(
            provider, model, profile, anchor=anchor, cwd=probe_cwd
        )

    env_build_failed = False
    try:
        probe_env = build_env()
    except Exception:  # noqa: BLE001 - an env build may never end a preflight
        # Fail closed, never open: the probe still runs (inheriting this
        # process's env) so a logged-out CLI is still refused, but a `True`
        # it returns is demoted to "unknown" below and the config leg is not
        # asked — an env we could not build cannot vouch for a credential.
        probe_env = None
        env_build_failed = True
    if _accepts_keyword(_run_probe, "env"):
        completed = _run_probe(argv, env=probe_env)
    else:  # a narrow `(argv)` test double
        completed = _run_probe(argv)
    verdict: Optional[bool] = None
    if completed is not None:
        try:
            verdict = provider.classify_auth_probe(
                completed.stdout, completed.stderr, completed.returncode
            )
        except Exception:  # noqa: BLE001 - a probe must never break a preflight
            verdict = None
    if verdict is True and env_build_failed:
        # The inherited env may carry a key the dispatch env would drop
        # (`env_allowlist`, a host guard), so this login is not evidence.
        verdict = None
    if verdict is False and not needs_credentials:
        # Measured, not assumed: the adapter declared this model answers with no
        # credential present, so a logged-out probe is evidence about *other*
        # models on this CLI and refuses nothing here.
        _AUTH_CACHE[cache_key] = "not-required"
        return "not-required"
    if verdict is False:
        source = CONFIG_AUTH_UNKNOWN
        hook = getattr(provider, "config_credential_source", None)
        if callable(hook) and not env_build_failed:
            try:
                source = hook(
                    model, profile=profile, anchor=anchor, cwd=probe_cwd,
                    env_builder=build_env,
                )
            except Exception:  # noqa: BLE001 - a diagnostic read may never end a preflight
                source = CONFIG_AUTH_UNKNOWN
        if source == CONFIG_AUTH_DECLARED:
            _AUTH_CACHE[cache_key] = AUTH_STATE_CONFIG
            return AUTH_STATE_CONFIG
        login = getattr(provider, "login_cmd", "") or f"{argv[0]} login"
        # The probe's own envelope, redacted at this boundary: cursor-agent's
        # `status --format json` carries `userEmail`/`terminalProgram`/`shell`
        # (M13), and this message is printed straight to a terminal and a log —
        # it reaches neither of §4.5.3's redacting write sinks.
        tail = _redact_probe_tail(_probe_verdict_stream(completed), 500)
        dropped = _dropped_credential_names(probe_env)
        dropped_note = ""
        if dropped:
            # T8.13: this case used to pass preflight and fail at dispatch with
            # a vendor auth error, so the behaviour change is named. Names only.
            cause = (
                "`env_allowlist: on` does not admit "
                + ("it" if len(dropped) == 1 else "them")
                + " for this runner"
                if env_allowlist_enabled(anchor)
                else "a host env guard strips "
                + ("it" if len(dropped) == 1 else "them")
            )
            dropped_note = (
                f" This process's environment sets {', '.join(dropped)}, but the "
                f"runner's environment does not carry "
                f"{'it' if len(dropped) == 1 else 'them'} ({cause}), so the probe "
                f"ran without {'it' if len(dropped) == 1 else 'them'}, as a "
                f"dispatch would."
            )
        raise RunnerRejected(
            f"Refusing to dispatch: {key} is {spec!r} (reason: not_authenticated) — "
            f"{_REASON_EXPLANATION['not_authenticated']}. "
            f"`{' '.join(argv)}` reported: {tail!r}.{dropped_note} "
            f"Fix: run `{login}`"
            + (
                " (a stored credential is not filtered by env_allowlist)"
                if dropped and env_allowlist_enabled(anchor)
                else ""
            )
            + ", then re-run this phase. Nothing was dispatched.",
            key=key,
            spec=spec,
            reason_code="not_authenticated",
        )

    state = "ok" if verdict else "unknown"
    _AUTH_CACHE[cache_key] = state
    return state


def _run_sandbox_probe(
    argv: Sequence[str],
    *,
    cwd: Optional[str],
    timeout: float,
    env: Optional[Mapping[str, str]] = None,
) -> Optional["subprocess.CompletedProcess"]:
    """Run one ``sandbox_probe_command`` argv (D6 step 3).

    A sibling of :func:`_run_probe` rather than a flag on it — a write
    profile's probe writes a byte, so it has to run with ``cwd`` at the repo
    root the dispatch would use, and it has its own, shorter budget. ``None``
    means the command could not be run at all (the binary vanished between
    ``is_available`` and here, the interpreter refused the spawn) and every
    caller reads it as ``unknown``: a preflight probe reports, it never blocks
    on its own failure.
    A timeout is ``None`` too, for the same reason.

    ``env`` (plan codex-sandbox-unavailable §6 F1, 2026-09-30) is the wrapped
    rung probe's own environment — the probe's ``TMPDIR`` and the canary's
    seeded file and targets — from ``landlock_dispatch.rung_probe``; ``None``
    inherits this process's, as every other probe does.
    """
    launcher, _ = _resolve_executable(argv[0])
    kwargs: Dict[str, Any] = {}
    if env is not None:
        kwargs["env"] = dict(env)
    if process_control.IS_WINDOWS:
        return _run_sandbox_probe_tree([*launcher, *argv[1:]], cwd=cwd,
                                       timeout=timeout, **kwargs)
    try:
        return subprocess.run(
            [*launcher, *argv[1:]],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            stdin=subprocess.DEVNULL,
            cwd=cwd,
            **kwargs,
        )
    except (OSError, subprocess.SubprocessError):
        return None


def _run_sandbox_probe_tree(
    command: Sequence[str], *, cwd: Optional[str], timeout: float, **kwargs: Any,
) -> Optional["subprocess.CompletedProcess"]:
    """:func:`_run_sandbox_probe` on Windows, where ``subprocess.run`` does not
    keep its timeout.

    There ``run`` kills the direct child alone on a timeout and then reads both
    pipes to their end with no timeout at all, so a grandchild still holding
    them (``sh -c`` → ``sleep``, a CLI's own helper) held the probe for as long
    as it lived: 5.3 s against a 0.2 s budget on the Windows CI (Windows port,
    round seven). A timed-out probe's whole tree is killed instead and its
    pipes are read for at most :data:`SANDBOX_PROBE_KILL_S` more, then let go
    unclosed — a close would wait on the read that holds them. ``None`` on a
    timeout, as before.

    The probe runs in a Job Object (``process_control.popen_tree``), so the
    kill is one ``TerminateJobObject`` call that reaches exactly its tree
    (round-8 review): ``taskkill /T``, now only the fallback for a probe that
    got no job, walks parent pids and can reach an unrelated orphan, and
    within :data:`SANDBOX_PROBE_KILL_S` on a loaded runner it can time out
    having killed nothing past the direct child.
    """
    try:
        proc, job = process_control.popen_tree(
            list(command),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=cwd,
            **kwargs,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        process_control.end_tree(proc.pid, job, timeout=SANDBOX_PROBE_KILL_S)
        try:
            proc.kill()
        except OSError:  # pragma: no cover - already gone
            pass
        try:
            proc.communicate(timeout=SANDBOX_PROBE_KILL_S)
        except (subprocess.SubprocessError, OSError, ValueError):
            pass
        return None
    except BaseException as exc:
        # What `run` does on any other way out: no child left, and an OSError
        # is "could not be run", like the spawn's.
        if job is None or not job.terminate():
            proc.kill()
        if isinstance(exc, (OSError, subprocess.SubprocessError)):
            return None
        raise
    finally:
        if job is not None:
            job.close()
    return subprocess.CompletedProcess(proc.args, proc.returncode, stdout, stderr)


#: How one rung of the fallback walk ended (landlock rung, 2026-09-22).
#: ``taken`` — the rung was selected; ``rejected`` — its probe exited but its
#: containment canary's write was NOT denied (the flag was a no-op: fail-open);
#: ``unavailable`` — a real sandbox failure; ``absent`` — the CLI did not
#: understand the probe (this build does not know the rung), or exited 0
#: without the canary's affirmative ``SANDBOX_CANARY_DENIED`` marker (the
#: canary never ran to completion, so no boundary was measured); ``unprobed`` — the
#: walk's shared deadline ran out before or while this rung was measured;
#: ``unknown`` — the probe produced no exit status for another reason (spawn
#: failure), or the rung's canary directory (``SandboxRung.probe_workdir``)
#: could not be created and proven writable outside the sandbox, so the probe
#: was never run. The first four let the walk continue (``taken`` ends it with a
#: rung); the last two **stop** it with none: "nothing learned" never licenses
#: a widening.
RUNG_TAKEN = "taken"
RUNG_REJECTED = "rejected"
RUNG_UNAVAILABLE = "unavailable"
RUNG_ABSENT = "absent"
RUNG_UNPROBED = "unprobed"
RUNG_UNKNOWN = "unknown"
#: 2026-09-24 (plan §3): ``skipped`` — not probed because the detected CLI
#: version is at or above the rung's ``removed_at`` (the probe would only
#: re-measure a known exit-101 panic); ``retired`` — probed, and its output
#: carried the rung's ``removed_signature`` (codex 0.156.1's "requires
#: bubblewrap" panic), classified by text and never by exit code. Both let the
#: walk continue, like ``unavailable``; they are the two outcomes that earn the
#: retirement line. A timeout, a canary-setup failure or any other error is
#: never either of them.
RUNG_SKIPPED = "skipped"
RUNG_RETIRED = "retired"
#: 2026-09-30 (plan codex-sandbox-unavailable §6 F1 item 6): the process was
#: told to skip this rung (``MULTI_LLM_CODEX_SKIP_RUNG=plugin-landlock``). Not
#: probed, the walk moves on — and never a retirement, so it earns no
#: retirement line. Base's word, so the walk clause renders it.
RUNG_SKIPPED_BY_SWITCH = WALK_OUTCOME_SKIPPED_BY_SWITCH


class SandboxProbeResult(NamedTuple):
    """What :func:`sandbox_verdict` measured: ``(state, tail, rung, walk, rung_tails, version)``.

    A NamedTuple, not a widened plain tuple, so a stale two-value unpack
    (``state, tail = sandbox_verdict(...)``) *raises* instead of silently
    dropping the rung — the rung is what makes the dispatch render the right
    argv, and losing it quietly re-opens the skip-the-rewrite failure.

    * ``state`` — the profile's own probe: ``ok`` | ``unavailable`` |
      ``unknown`` | ``not-required``, exactly as before the ladder.
    * ``tail`` — the redacted end of what that probe printed.
    * ``rung`` — the id of the fallback rung the walk selected, or ``None``.
      Only ever set beside ``state == "unavailable"``; whether the rung may be
      *taken* is still the gates' decision (the ``sandbox_fallback`` key).
    * ``walk`` — ``((rung id, outcome), …)`` for every rung the walk reached,
      in order, outcomes from the ``RUNG_*`` constants. ``()`` when no walk
      ran. It is how a reader tells a rung that was measured and rejected from
      one the deadline never let anyone measure (``unprobed``).
    * ``rung_tails`` — ``((rung id, redacted probe tail), …)`` for every rung
      whose probe actually ran (2026-09-24), so the ``[SANDBOX_BYPASSED]`` line
      can say why a contained rung was not taken — and say it identically on a
      cache hit. A rung ``skipped`` by version has no tail.
    * ``version`` — the CLI version the walk was judged against (``""`` when
      unread): what the line and the retirement notice name.
    """

    state: str
    tail: str
    rung: Optional[str] = None
    walk: Tuple[Tuple[str, str], ...] = ()
    rung_tails: Tuple[Tuple[str, str], ...] = ()
    version: str = ""


def _sandbox_probe_inconclusive(text: str) -> bool:
    try:  # pragma: no cover - import shim mirrors the rest of utils/
        from .providers.base import sandbox_probe_inconclusive
    except ImportError:  # pragma: no cover - direct-script import shim
        from utils.providers.base import sandbox_probe_inconclusive
    return sandbox_probe_inconclusive(text)


def _fallback_rungs(provider: Any, profile: str) -> Tuple[SandboxRung, ...]:
    """The adapter's declared ladder for ``profile``, or ``()``.

    ``getattr`` because a test's stand-in adapter may not declare the hook, and
    any failure reads as "no ladder" — a diagnostic may not break a preflight,
    and no ladder is the narrow reading.
    """
    hook = getattr(provider, "sandbox_fallback_rungs", None)
    if not callable(hook):
        return ()
    try:
        return tuple(hook(profile) or ())
    except Exception:  # noqa: BLE001 - a diagnostic may not break a preflight
        return ()


def _prepare_probe_workdir(cwd: Optional[str], workdir: str) -> Optional[List[str]]:
    """Create ``workdir`` under ``cwd`` and prove a file can be written there —
    outside any sandbox — before a contained rung's canary runs in it.

    Returns the directories this call created (deepest first, for
    :func:`_remove_created_dirs`), or ``None`` when the directory cannot be
    made (a non-directory in the way) or is not writable by this user: a
    canary whose write is refused by plain permissions must not read as a
    boundary. Anything this call created is removed again on failure.
    """
    base = os.path.abspath(cwd or os.getcwd())
    target = os.path.join(base, workdir)
    created: List[str] = []
    missing: List[str] = []
    probe = target
    while probe != base and not os.path.lexists(probe):
        missing.append(probe)
        probe = os.path.dirname(probe)
    try:
        for path in reversed(missing):
            os.mkdir(path)
            created.insert(0, path)
        if not os.path.isdir(target):
            raise NotADirectoryError(target)
        fd, scratch = tempfile.mkstemp(prefix="sandbox-setup-", dir=target)
        os.close(fd)
        os.unlink(scratch)
    except OSError:
        _remove_created_dirs(created)
        return None
    return created


def _remove_created_dirs(created: Optional[Sequence[str]]) -> None:
    """``rmdir`` what :func:`_prepare_probe_workdir` created, deepest first.

    Only ever those directories, only if empty, and quietly: a canary that ran
    unsandboxed may already have removed them itself.
    """
    for path in created or ():
        try:
            os.rmdir(path)
        except OSError:
            pass


#: The interprocess mutex a rung probe holds while its canary directory
#: exists, one file per repository under the system temp dir (never unlinked,
#: like every lock file of ``process_control``).
PROBE_WORKDIR_LOCK_PREFIX = "multi-llm-probe-"


def _probe_workdir_lock_path(cwd: Optional[str]) -> str:
    base = os.path.realpath(cwd or os.getcwd())
    digest = hashlib.sha256(base.encode("utf-8", "surrogateescape")).hexdigest()[:16]
    return os.path.join(tempfile.gettempdir(), f"{PROBE_WORKDIR_LOCK_PREFIX}{digest}.lock")


@contextlib.contextmanager
def _probe_workdir(
    cwd: Optional[str], workdir: Optional[str], deadline: float,
) -> Iterator[Optional[List[str]]]:
    """Prepare a rung probe's canary directory, serialized across processes,
    and remove what was created once the probe has run.

    Yields what :func:`_prepare_probe_workdir` created (``[]`` for a rung with
    no ``probe_workdir``), ``None`` when it could not be prepared — or when the
    mutex could not be taken before ``deadline`` (the caller reads the clock
    and records ``unprobed``). Each probe only ever removes the directories
    it created, so two probes of one repository at once — twelve concurrent
    ``status`` polls, measured 2026-10-02 — used to leave an empty
    ``.multi-llm/`` and ``.multi-llm/tmp/`` behind: the first one's ``rmdir``
    failed on the second one's seed, and the second one had created nothing.
    Under the mutex the second waits its turn and creates and removes its own.
    A mutex file that cannot be opened proceeds unserialized, as before.
    """
    if not workdir:
        yield []
        return
    mutex = process_control.FileMutex(_probe_workdir_lock_path(cwd))
    acquired = mutex.acquire(timeout_s=max(0.0, deadline - time.monotonic()))
    try:
        if not acquired and time.monotonic() >= deadline:
            yield None
            return
        created = _prepare_probe_workdir(cwd, workdir)
        try:
            yield created
        finally:
            _remove_created_dirs(created)
    finally:
        mutex.release()


def _rung_probe_tail(rung: SandboxRung, completed: Any) -> str:
    """The redacted line a rung's probe is remembered by: the line carrying
    its ``removed_signature`` when present, else the last non-empty line of
    stderr (stdout when stderr is empty)."""
    text = f"{completed.stderr or ''}\n{completed.stdout or ''}"
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    signature = getattr(rung, "removed_signature", None)
    if signature:
        needle = " ".join(signature.split())
        hit = next((line for line in lines if needle in " ".join(line.split())), None)
        if hit is None and rung_probe_said_removed(rung, text):
            hit = needle
        if hit:
            return _redact_probe_tail(hit, 500)
    source = [line.strip() for line in (completed.stderr or completed.stdout or "").splitlines()
              if line.strip()]
    return _redact_probe_tail(source[-1] if source else "", 500)


def _scrub_probe_paths(text: str, *paths: Optional[str]) -> str:
    """``text`` with the rung probe's own per-attempt paths replaced by
    placeholders, so no cached tail holds a slot ``TMPDIR`` or a seeded file
    (plan F1 "Task-specific paths stay out of shared state and caches")."""
    for path in paths:
        if path:
            text = text.replace(path, landlock_dispatch.PLACEHOLDER_TMPDIR)
    return text


def _walk_wrapped_rung(
    rung: SandboxRung,
    *,
    cwd: Optional[str],
    deadline: float,
    request: Optional[JailRequest],
    tails: Optional[List[Tuple[str, str]]],
) -> Tuple[str, bool]:
    """One wrapping rung's turn in the walk: ``(outcome, stop the walk)``.

    Plan codex-sandbox-unavailable §6 F1 "Where it sits" item 3 (2026-09-30).
    The rung has three kinds of result, and the walk keeps its old rule for
    each: a probe that measured nothing never counts as a failed rung.

    * **Skipped** (``MULTI_LLM_CODEX_SKIP_RUNG=plugin-landlock``): not probed,
      the walk moves on, never a retirement. A value the switch does not
      accept stops the walk (never ignored, never a widening).
    * **Stops the walk with no rung**: the deadline was already spent
      (``unprobed``), the negative target, seeded file or probe ``TMPDIR``
      could not be prepared outside the jail (``unknown``), or the probe
      produced no exit status (``unknown``/``unprobed``).
    * **Measured**, from the wrapper's exit and the canary: exit 126 (no
      Landlock, an ABI below 3) or 125 (a required allow entry missing) —
      and a required entry refused before the spawn (``JailRefused``, e.g.
      ``$CODEX_HOME`` missing) — are ``absent``; a write or truncation that
      landed (``SANDBOX_CANARY_NOT_DENIED``, or the parent's byte comparison
      of the seeded file) is ``rejected``; a failed positive control (exit 5)
      is ``unavailable``; exit 0 with ``SANDBOX_CANARY_DENIED`` and the seed
      intact is ``taken``; exit 0 without the marker is ``absent``; any other
      exit reads through the existing branches.

    The probe gets only what is left of the walk's one shared deadline, never
    a timeout of its own.
    """
    try:
        skipped = skip_rung_requested()
    except ValueError as exc:
        if tails is not None:
            tails.append((rung.name, _redact_probe_tail(str(exc), 500)))
        return RUNG_UNKNOWN, True
    if skipped == rung.name:
        return RUNG_SKIPPED_BY_SWITCH, False
    if deadline - time.monotonic() <= 0:
        return RUNG_UNPROBED, True
    with _probe_workdir(cwd, rung.probe_workdir, deadline) as created:
        if created is None:
            ran_out = time.monotonic() >= deadline
            return (RUNG_UNPROBED if ran_out else RUNG_UNKNOWN), True
        if request is None:
            request = JailRequest(
                repo_root=os.path.realpath(cwd or os.getcwd()), kind=PROFILE_AGENT_READONLY,
            )
        launcher, _ = _resolve_executable(str(rung.probe_argv[0]))
        resolved = [*launcher, *(str(a) for a in rung.probe_argv[1:])]
        completed = None
        seed_intact = True
        scrub: Tuple[Optional[str], ...] = ()
        try:
            with landlock_dispatch.rung_probe(rung, request, resolved, cwd=cwd) as probe:
                scrub = (probe.env.get("TMPDIR"), probe.seeded)
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return RUNG_UNPROBED, True
                completed = _run_sandbox_probe(
                    probe.argv, cwd=cwd, timeout=remaining, env=probe.env,
                )
                seed_intact = probe.seed_intact()
        except landlock_dispatch.ProbeSetupFailed as exc:
            if tails is not None:
                tails.append((rung.name, _redact_probe_tail(str(exc), 500)))
            return RUNG_UNKNOWN, True
        except landlock_dispatch.JailRefused as exc:
            # A required entry the probe (and so every dispatch it gates) cannot
            # be granted: the rung is not usable here, measured before any spawn.
            if tails is not None:
                tails.append((rung.name, _redact_probe_tail(exc.message, 500)))
            return RUNG_ABSENT, False
    if completed is None:
        ran_out = time.monotonic() >= deadline
        return (RUNG_UNPROBED if ran_out else RUNG_UNKNOWN), True
    said = f"{completed.stdout}\n{completed.stderr}"
    note = landlock_dispatch.wrapper_note(completed.stderr)
    if tails is not None:
        if not seed_intact and SANDBOX_CANARY_NOT_DENIED not in said:
            # The parent's byte comparison caught what the canary did not: the
            # canary's last line is its DENIED marker, which would read as the
            # opposite of the verdict (acceptance review, 2026-09-30).
            tail = "the truncation control changed the seeded file (truncate(2) was not denied)"
        else:
            tail = _redact_probe_tail(note, 500) if note else _rung_probe_tail(rung, completed)
        tails.append((rung.name, _scrub_probe_paths(tail, *scrub)))
    if SANDBOX_CANARY_NOT_DENIED in said or not seed_intact:
        # Checked first: a write or truncation that landed rejects the rung
        # whatever the exit status says — the canary's own word, or the
        # parent's byte comparison of the seeded file.
        return RUNG_REJECTED, False
    if completed.returncode in (
        landlock_dispatch.EXIT_UNAVAILABLE, landlock_dispatch.EXIT_REQUIRED_ENTRY,
    ):
        return RUNG_ABSENT, False
    positive_exit = _plugin_landlock_positive_exit()
    if completed.returncode == positive_exit:
        return RUNG_UNAVAILABLE, False
    if completed.returncode == 0 and SANDBOX_CANARY_DENIED in said:
        return RUNG_TAKEN, False
    if completed.returncode == 0:
        return RUNG_ABSENT, False
    if rung_probe_said_removed(rung, said):
        return RUNG_RETIRED, False
    if _sandbox_probe_inconclusive(said):
        return RUNG_ABSENT, False
    return RUNG_UNAVAILABLE, False


def _plugin_landlock_positive_exit() -> int:
    """The rung canary's positive-control exit (5), read from the adapter
    module so the two cannot drift; 5 when the adapter cannot be imported."""
    try:  # pragma: no cover - import shim mirrors the rest of utils/
        from .providers.codex import PLUGIN_LANDLOCK_CANARY_POSITIVE_EXIT
    except ImportError:  # pragma: no cover - direct-script import shim
        try:
            from utils.providers.codex import PLUGIN_LANDLOCK_CANARY_POSITIVE_EXIT
        except ImportError:
            return 5
    return int(PLUGIN_LANDLOCK_CANARY_POSITIVE_EXIT)


def _walk_fallback_rungs(
    rungs: Sequence[SandboxRung],
    *,
    cwd: Optional[str],
    deadline: float,
    version: Optional[str] = None,
    tails: Optional[List[Tuple[str, str]]] = None,
    jail_request: Optional[JailRequest] = None,
) -> Tuple[Optional[str], Tuple[Tuple[str, str], ...]]:
    """Walk ``rungs`` in order under one shared ``deadline`` (T3's walk table).

    Returns ``(selected rung id or None, walk record)``. Each rung probe gets
    only what is left of the deadline; a rung with nothing left is not started
    and is recorded ``unprobed``, which — like a probe with no exit status —
    stops the walk with no rung, so the uncontained rung is never rendered on
    exhausted time.

    ``version`` (2026-09-24): a rung whose ``removed_at`` the version reaches
    is not probed at all — recorded ``skipped`` — and the walk moves on. An
    unread version never skips. ``tails``, when given, receives ``(rung id,
    probe tail)`` for every rung whose probe ran.

    A wrapping rung (the plugin's Landlock jail, 2026-09-30) is probed by
    :func:`_walk_wrapped_rung` under ``jail_request`` — the grant the dispatch
    it gates would carry, so a write profile's positive control writes that
    dispatch's own target. ``None`` builds the read-only request for ``cwd``.
    """
    walk: List[Tuple[str, str]] = []
    for rung in rungs:
        if rung.probe_argv and rung_removed_for_version(rung, version):
            walk.append((rung.name, RUNG_SKIPPED))
            continue
        if not rung.probe_argv:
            # Nothing to measure (the uncontained rung): reaching it is taking it.
            walk.append((rung.name, RUNG_TAKEN))
            return rung.name, tuple(walk)
        if getattr(rung, "wrapper", None):
            # The plugin's own Landlock jail (plan codex-sandbox-unavailable
            # §6 F1 item 3, 2026-09-30): its probe is wrapped, seeded and
            # read with its own outcome table, under the same deadline.
            outcome, stop = _walk_wrapped_rung(
                rung, cwd=cwd, deadline=deadline, request=jail_request,
                tails=tails,
            )
            walk.append((rung.name, outcome))
            if outcome == RUNG_TAKEN:
                return rung.name, tuple(walk)
            if stop:
                return None, tuple(walk)
            continue
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            walk.append((rung.name, RUNG_UNPROBED))
            return None, tuple(walk)
        workdir = getattr(rung, "probe_workdir", None)
        with _probe_workdir(cwd, workdir, deadline) as created:
            if created is None:
                # The canary's directory could not be made writable *outside*
                # the sandbox, so a denied write inside it would prove nothing
                # about the boundary: nothing was measured, never a widening —
                # or the deadline went while waiting for the workdir's turn.
                ran_out = time.monotonic() >= deadline
                walk.append((rung.name, RUNG_UNPROBED if ran_out else RUNG_UNKNOWN))
                return None, tuple(walk)
            completed = _run_sandbox_probe(
                list(rung.probe_argv), cwd=cwd,
                timeout=max(deadline - time.monotonic(), 0.0),
            )
        if completed is None:
            ran_out = time.monotonic() >= deadline
            walk.append((rung.name, RUNG_UNPROBED if ran_out else RUNG_UNKNOWN))
            return None, tuple(walk)
        said = f"{completed.stdout}\n{completed.stderr}"
        if tails is not None:
            tails.append((rung.name, _rung_probe_tail(rung, completed)))
        if SANDBOX_CANARY_NOT_DENIED in said:
            # Checked first: a write that landed rejects the rung whatever the
            # exit status says.
            walk.append((rung.name, RUNG_REJECTED))
        elif completed.returncode == 0 and SANDBOX_CANARY_DENIED in said:
            # Exit 0 *and* the canary's own affirmative marker: the canary ran
            # to completion and its write was denied.
            walk.append((rung.name, RUNG_TAKEN))
            return rung.name, tuple(walk)
        elif completed.returncode == 0:
            # Exit 0 without the marker is not containment: the canary never
            # ran to completion (a CLI that printed usage and exited 0, a flag
            # accepted as a no-op). Nothing about a boundary was measured, so
            # the rung is not usable here — read like a probe the CLI did not
            # understand.
            walk.append((rung.name, RUNG_ABSENT))
        elif rung_probe_said_removed(rung, said):
            # Classified by its text, before the generic branches: this build
            # no longer supports the rung (codex 0.156.1's panic, exit 101 —
            # the same exit as constraint 2's unrelated panic).
            walk.append((rung.name, RUNG_RETIRED))
        elif _sandbox_probe_inconclusive(said):
            walk.append((rung.name, RUNG_ABSENT))
        else:
            walk.append((rung.name, RUNG_UNAVAILABLE))
    return None, tuple(walk)


def sandbox_verdict(
    provider: Any,
    profile: str,
    *,
    cwd: Optional[str] = None,
    timeout: Optional[float] = None,
    version: Optional[str] = None,
    walk_key: Optional[Tuple[str, ...]] = None,
    jail_request: Optional[JailRequest] = None,
    walk: bool = True,
) -> SandboxProbeResult:
    """One adapter's sandbox self-test (D6 step 3), plus its fallback walk.

    ``state`` is ``not-required`` when the adapter answers no command for this
    profile, ``ok`` on exit 0, ``unavailable`` on any other exit, and
    ``unknown`` when the command could not be run or did not finish. ``tail``
    is the redacted end of what the command printed — the ``bwrap:`` line, on
    the machine this was written for. Shared by the executor's preflight and
    ``multi_llm.py doctor`` so both read the same command the same way.

    On ``unavailable`` — and only then — the adapter's fallback ladder
    (``sandbox_fallback_rungs``) is walked in order (landlock rung,
    2026-09-22): a rung whose probe exits 0 **and** prints the canary's
    affirmative ``SANDBOX_CANARY_DENIED`` marker (its canary write was
    *denied*) is selected — exit 0 alone is not containment; a rejected
    canary, a real sandbox failure, a probe the CLI did not understand or an
    exit 0 without the marker moves on; a probe with no exit status
    stops the walk with no rung. ``timeout`` is the budget for the **whole**
    call, not per probe: the deadline is taken once on entry and every rung
    probe gets only what is left of it, so a two-probe ladder never costs more
    than one ``SANDBOX_PROBE_TIMEOUT_S``.

    ``version`` (2026-09-24) is the CLI version the walk is judged against: a
    rung whose ``removed_at`` it reaches is recorded ``skipped`` without a
    probe. ``None`` — what ``doctor`` passes — probes every rung, so a build
    that restores a rung is measured rather than assumed. ``walk_key``, when
    given, is the :data:`_SANDBOX_PROBE_CACHE` key the walk is shared under:
    a walk already recorded there is reused rather than re-probed, and a fresh
    one is stored there.

    ``jail_request`` (plan codex-sandbox-unavailable §6 F1, 2026-09-30) is the
    grant a wrapping rung's probe is prepared under; ``None`` is the read-only
    request for ``cwd`` (``kind`` = ``profile``). A write profile's request
    carries its scope and target, which the rung canary's positive control
    writes. ``walk=False`` runs the profile's own probe and walks no rung — a
    caller that already knows no rung can take this dispatch (the ``off``
    policy, a write scope the rung does not serve) spawns no rung probe.
    """
    try:
        argv = provider.sandbox_probe_command(profile)
    except Exception:  # noqa: BLE001 - a diagnostic may not break a preflight
        argv = None
    if not argv:
        return SandboxProbeResult("not-required", "")
    if timeout is None:
        # Resolved at call time so a test can shorten the module constant.
        timeout = SANDBOX_PROBE_TIMEOUT_S
    deadline = time.monotonic() + max(timeout, 0.0)
    completed = _run_sandbox_probe(list(argv), cwd=cwd, timeout=timeout)
    if completed is None:
        return SandboxProbeResult("unknown", "")
    tail = _redact_probe_tail(completed.stderr or completed.stdout, 500)
    if completed.returncode == 0:
        return SandboxProbeResult("ok", tail)
    if _sandbox_probe_inconclusive(f"{completed.stdout}\n{completed.stderr}"):
        # The CLI did not understand the probe (a build older than its
        # `sandbox` subcommand): nothing about the sandbox was learned.
        return SandboxProbeResult("unknown", tail)
    rungs = _fallback_rungs(provider, profile) if walk else ()
    if not rungs:
        return SandboxProbeResult("unavailable", tail)
    if jail_request is None:
        jail_request = JailRequest(
            repo_root=os.path.realpath(cwd or os.getcwd()), kind=profile,
        )
    shared = None
    if walk_key is not None:
        with _SANDBOX_PROBE_LOCK:
            shared = _SANDBOX_PROBE_CACHE.get(walk_key)
    if shared is not None:
        return SandboxProbeResult(
            "unavailable", tail, shared.rung, shared.walk, shared.rung_tails,
            version or "",
        )
    tails: List[Tuple[str, str]] = []
    rung, walked = _walk_fallback_rungs(
        rungs, cwd=cwd, deadline=deadline, version=version, tails=tails,
        jail_request=jail_request,
    )
    result = SandboxProbeResult(
        "unavailable", tail, rung, walked, tuple(tails), version or "",
    )
    stopped = any(outcome in (RUNG_UNPROBED, RUNG_UNKNOWN) for _, outcome in walked)
    if walk_key is not None and not stopped:
        # A walk that stopped on "nothing learned" is not shared: another
        # profile's probe, with its own budget, may yet get an answer.
        with _SANDBOX_PROBE_LOCK:
            _SANDBOX_PROBE_CACHE[walk_key] = result
    return result


def _probe_cwd(anchor: Optional[str]) -> Optional[str]:
    """Where the sandbox probe writes its byte: the repo root a dispatch pins.

    The anchor is the plan path (or directory) the run discovers its config
    from; its git root is the ``cwd`` every write dispatch is pinned to, so the
    probe asks the same question in the same place. Without a resolvable root
    the process cwd stands in — ``None`` here means "inherit".
    """
    try:
        from .git_utils import get_project_root_from_dir
    except ImportError:  # pragma: no cover - direct-script import shim
        from utils.git_utils import get_project_root_from_dir
    start: Optional[str] = None
    if anchor:
        start = anchor if os.path.isdir(anchor) else (os.path.dirname(anchor) or ".")
    try:
        root = get_project_root_from_dir(start) if start else get_project_root_from_dir()
    except Exception:  # noqa: BLE001 - a cwd choice may never end a preflight
        root = None
    return root or None


def _current_host_id() -> str:
    """The host id the sandbox cache is keyed under (``unknown-host`` off-data)."""
    resolved = _host_nested_exec()
    return resolved[0] if resolved else "unknown-host"


def _sandbox_fallback_policy(
    provider: Any, profile: str, *, anchor: Optional[str]
) -> Optional[str]:
    """The adapter's resolved ``sandbox_fallback`` policy for ``profile``, or
    ``None`` when it declares none (or the read fails).

    ``getattr`` because a test's stand-in adapter may not declare the hook; a
    config read that raises is ``None`` — the narrow reading, and the one that
    matches every other gate's posture on a config it cannot read. ``anchor``
    is the plan path, so the key is read from the same
    ``.multi-llm/providers.yaml`` the dispatch's env and timeout come from.
    """
    hook = getattr(provider, "sandbox_fallback_policy", None)
    if not callable(hook):
        return None
    try:
        policy = hook(profile, anchor=anchor)
    except Exception:  # noqa: BLE001 - a config read may never end a preflight
        return None
    return policy if isinstance(policy, str) else None


def sandbox_fallback_rung(
    provider: Any, profile: str, rung_id: Optional[str], policy: Optional[str]
) -> Optional[SandboxRung]:
    """The declared rung ``rung_id`` if ``policy`` may take it for ``profile``.

    The policy half of both gates (this module's :func:`_detect_sandbox` and
    ``review_orchestrator_base.sandbox_refusal``), in one place: the profile is
    one of ``SANDBOX_FALLBACK_PROFILES`` (repeated here although the adapter
    answers ``None``/``()`` outside it — two places have to agree before a
    write profile could slip through), the walk selected a rung the adapter
    actually declares for that profile, and :func:`sandbox_rung_allowed` says
    the key permits it — ``auto`` any rung, ``contained`` a contained one only,
    ``off`` none. The probe verdict ``unavailable`` is the caller's gate.

    A write profile (plan step 3, user decision 2026-09-30) is answered
    separately: it reaches a rung its adapter declares in the write ladder, and
    only through :func:`write_rung_allowed` — a wrapping ``incidental``-grade
    rung (the plugin's Landlock jail) under ``auto``. Never the uncontained or
    the legacy ``landlock`` rung, under any policy word. Two places still have
    to agree (the adapter's write ladder and this gate) before a write
    dispatch widens.
    """
    if not rung_id:
        return None
    if profile in SANDBOX_WRITE_FALLBACK_PROFILES:
        for rung in _fallback_rungs(provider, profile):
            if rung.name == rung_id:
                return rung if write_rung_allowed(rung, policy) else None
        return None
    if profile not in SANDBOX_FALLBACK_PROFILES:
        return None
    for rung in _fallback_rungs(provider, profile):
        if rung.name == rung_id:
            return rung if sandbox_rung_allowed(rung, policy) else None
    return None


def sandbox_walk_note(
    verdict: "SandboxProbeResult",
    policy: Optional[str],
    *,
    provider_name: Optional[str] = None,
    rungs: Sequence[SandboxRung] = (),
) -> str:
    """One sentence on why an ``unavailable`` verdict took no rung, or ``""``.

    Said only where it changes what the reader should do: the walk stopped on
    a probe that produced no answer (fail-closed — a hung or unstartable rung
    probe refuses where the old single probe would have bypassed), or
    ``contained`` refused the uncontained rung the walk reached. ``off`` and an
    adapter with no ladder say nothing new: that refusal is the old one.

    Under ``contained``, given ``provider_name`` (and the declared ``rungs``
    for ``removed_at``), the sentence carries the same rung clause the
    ``[SANDBOX_BYPASSED]`` line does (:func:`sandbox_walk_clause`) — so a rung
    ``skipped`` by version or ``retired`` by its probe's panic is named with
    its version and probe tail, not hidden behind "no contained rung".
    """
    if policy in (None, SANDBOX_FALLBACK_OFF):
        return ""
    stopped = next(
        (
            (name, outcome) for name, outcome in verdict.walk
            if outcome in (RUNG_UNPROBED, RUNG_UNKNOWN)
        ),
        None,
    )
    if stopped is not None:
        return (
            f"fallback rung {stopped[0]!r} was {stopped[1]} (its probe gave no "
            f"answer), so no fallback rung was taken"
        )
    if policy == SANDBOX_FALLBACK_CONTAINED and verdict.walk:
        clause = ""
        if provider_name:
            try:
                clause = sandbox_walk_clause(
                    provider_name, verdict.walk, verdict.rung_tails,
                    verdict.version or None, rungs,
                )
            except Exception:  # noqa: BLE001 - a note may never end a preflight
                clause = ""
        return (
            f"sandbox_fallback={SANDBOX_FALLBACK_CONTAINED}: no contained "
            f"fallback rung is usable here"
            + (f" ({clause})" if clause else "")
            + ", and the uncontained one is never taken under that value"
        )
    return ""


def _sandbox_probe_lock(key: Tuple[str, ...]) -> threading.Lock:
    """The probe lock for one :data:`_SANDBOX_PROBE_CACHE` key, created once."""
    with _SANDBOX_PROBE_LOCK:
        lock = _SANDBOX_PROBE_KEY_LOCKS.get(key)
        if lock is None:
            lock = _SANDBOX_PROBE_KEY_LOCKS[key] = threading.Lock()
        return lock


def _ladder_has_removed_at(provider: Any, profile: str) -> bool:
    """Whether ``provider``'s ladder for ``profile`` declares a rung that a
    version can retire — the only case the probe needs the CLI version."""
    return any(getattr(rung, "removed_at", None) for rung in _fallback_rungs(provider, profile))


def _sandbox_cli_version(
    provider_name: str, provider: Any, *, timeout: Optional[float] = None,
) -> str:
    """The CLI version the sandbox probe is keyed and judged on, or ``""``.

    The version preflight's own read (:data:`_VERSION_CACHE`) when it ran;
    otherwise one ``version_cmd`` spawn per provider per process, through the
    sandbox probe's runner (so the suite's guard on real CLIs covers it) and
    cached in :data:`_PROBE_VERSION_CACHE`. ``""`` when nothing could be read —
    and an unread version never skips a rung. ``timeout`` is an advisory
    reader's budget in place of :data:`SANDBOX_PROBE_TIMEOUT_S`; an empty
    read under it is not cached, so a dispatch reads the version itself.
    """
    if provider_name in _VERSION_CACHE:
        # The preflight's read is settled either way: a recorded "unknown"
        # already spawned `version_cmd` once, and a second spawn would only
        # re-measure the same failure. It reads as an unread version here.
        known = _VERSION_CACHE[provider_name]
        return "" if known == "unknown" else (known or "")
    with _SANDBOX_PROBE_LOCK:
        if provider_name in _PROBE_VERSION_CACHE:
            return _PROBE_VERSION_CACHE[provider_name]
        lock = _PROBE_VERSION_LOCKS.get(provider_name)
        if lock is None:
            lock = _PROBE_VERSION_LOCKS[provider_name] = threading.Lock()
    with lock:
        # Double-checked: a sibling spec of this provider, probed concurrently
        # in another thread, may have read the version while this one waited.
        with _SANDBOX_PROBE_LOCK:
            if provider_name in _PROBE_VERSION_CACHE:
                return _PROBE_VERSION_CACHE[provider_name]
        version = ""
        argv = list(getattr(provider, "version_cmd", ()) or ())
        if argv:
            completed = _run_sandbox_probe(
                argv, cwd=None,
                timeout=SANDBOX_PROBE_TIMEOUT_S if timeout is None else timeout,
            )
            if completed is not None:
                try:
                    version = provider.parse_version(completed.stdout, completed.stderr) or ""
                except Exception:  # noqa: BLE001 - a diagnostic may not break a preflight
                    version = ""
        if version or timeout is None:
            with _SANDBOX_PROBE_LOCK:
                _PROBE_VERSION_CACHE[provider_name] = version
        return version


def cached_sandbox_verdict(
    provider_name: str,
    provider: Any,
    profile: str,
    *,
    cwd: Optional[str],
    policy: Optional[str],
    jail_request: Optional[JailRequest] = None,
    timeout: Optional[float] = None,
) -> SandboxProbeResult:
    """Run — or recall — ``provider``'s sandbox self-test for ``profile``: the
    one per-process probe cache both lanes share (plan §3.6, 2026-09-24).

    ``timeout`` is an advisory reader's budget (:data:`ADVISORY_PROBE_BUDGET_S`,
    2026-10-02) for the version read, the standard probe and the walk
    together; a verdict it cut short (:func:`probe_budget_cut`) is returned
    but **not** cached, so the dispatch's own probe, under its own timeout,
    never inherits a reader's `unprobed`. A cached verdict is recalled
    whatever the budget: it was settled.

    Keyed by host, provider, profile, ``cwd``, the CLI version and the
    ``sandbox_fallback`` policy, and holding the whole
    :class:`SandboxProbeResult` — walk, rung probe tails and version included
    — so a cache hit prints the same line as the cold probe that filled it.
    The fallback walk is shared across profiles under its own key, so the
    fan-out (``generate``) and the executor (``agent-readonly``) in one process
    spawn one rung probe per codex version, not two. The version is read only
    for an adapter whose ladder declares a ``removed_at`` rung; at or above it
    the rung is not probed at all. A probe that raises reads ``unknown`` and is
    cached like any answer.

    Blocking — the fan-out hands it to a thread. The cache lock is held for
    the dict read and write only; the probe runs under a per-key lock, so two
    slots of one provider share a probe and a slow provider never holds up
    another (F5, 2026-09-17).

    Plan codex-sandbox-unavailable §6 F1 (2026-09-30):

    * ``off`` walks no rung: the policy takes none, so no rung probe spawns.
    * ``MULTI_LLM_CODEX_SKIP_RUNG``, when set, joins both keys, so a walk taken
      without the switch is never replayed with it (or the reverse).
    * For a write profile, ``jail_request`` is the dispatch's grant. Both the
      ``verdict`` and the ``walk`` key add its scope and — for ``plan-file``
      and ``tasks``, whose positive control writes it — its target; never a
      per-task declared path, a slot ``TMPDIR`` or an allow list. A write
      scope the rung does not serve (an unmapped kind: none) walks no rung.
      Read-only keys are unchanged.
    """
    host = _current_host_id()
    version = (
        _sandbox_cli_version(provider_name, provider, timeout=timeout)
        if _ladder_has_removed_at(provider, profile) else ""
    )
    write = profile in SANDBOX_WRITE_FALLBACK_PROFILES
    scope = getattr(jail_request, "write_scope", None) if write else None
    target = (
        getattr(jail_request, "target", None)
        if write and scope in WRITE_SCOPES_ON_RUNG else None
    )
    try:
        switch = skip_rung_requested() or ""
    except ValueError:
        switch = "invalid"
    extra: Tuple[str, ...] = ()
    if write:
        extra += (f"scope={scope or ''}", f"target={target or ''}")
    if switch:
        extra += (f"skip={switch}",)
    key = ("verdict", host, provider_name, profile, cwd or "", version, policy or "") + extra
    with _SANDBOX_PROBE_LOCK:
        cached = _SANDBOX_PROBE_CACHE.get(key)
    if cached is not None:
        return cached
    with _sandbox_probe_lock(key):
        # Double-checked: a sibling slot on this key may have finished the
        # probe while this thread waited for the lock.
        with _SANDBOX_PROBE_LOCK:
            cached = _SANDBOX_PROBE_CACHE.get(key)
        if cached is not None:
            return cached
        walk = policy != SANDBOX_FALLBACK_OFF and not (
            write and scope not in WRITE_SCOPES_ON_RUNG
        )
        rungs = _fallback_rungs(provider, profile) if walk else ()
        walk_key = (
            ("walk", host, provider_name, cwd or "", version,
             ",".join(rung.name for rung in rungs)) + extra
            if rungs else None
        )
        kwargs: Dict[str, Any] = {}
        if write and jail_request is not None:
            kwargs["jail_request"] = jail_request
        if not walk:
            kwargs["walk"] = False
        if timeout is not None:
            kwargs["timeout"] = timeout
        try:
            if walk_key is not None or version:
                verdict = sandbox_verdict(
                    provider, profile, cwd=cwd, version=version or None,
                    walk_key=walk_key, **kwargs,
                )
            else:
                verdict = sandbox_verdict(provider, profile, cwd=cwd, **kwargs)
        except Exception:  # noqa: BLE001 - a diagnostic may never end a run
            verdict = SandboxProbeResult("unknown", "")
        if timeout is None or not probe_budget_cut(verdict):
            with _SANDBOX_PROBE_LOCK:
                _SANDBOX_PROBE_CACHE[key] = verdict
        return verdict


def probe_budget_cut(verdict: SandboxProbeResult) -> bool:
    """Whether ``verdict`` measured nothing for want of time: the standard
    probe did not finish (``unknown``), or the walk ran out of deadline
    (``unprobed``). Not a rung's ``unknown`` — a canary directory or seed
    that could not be prepared is a fact about the machine, not the clock."""
    if verdict.state == "unknown":
        return True
    return any(outcome == RUNG_UNPROBED for _, outcome in (verdict.walk or ()))


def rung_retirements(verdict: SandboxProbeResult) -> List[str]:
    """The rung ids ``verdict``'s walk found retired — ``skipped`` by version
    or ``retired`` by the probe's own text. Never a timeout, a canary-setup
    failure or any other outcome: those are reported as themselves."""
    return [
        name for name, outcome in (verdict.walk or ())
        if outcome in (RUNG_SKIPPED, RUNG_RETIRED)
    ]


def recorded_rung_retirements(provider_name: str) -> List[Tuple[str, str]]:
    """``[(rung id, version), …]`` this process's probe cache recorded as
    retired for ``provider_name`` — what ``announce_retired_rungs`` prints the
    once-per-run retirement line from, whatever the previous run recorded."""
    found: List[Tuple[str, str]] = []
    with _SANDBOX_PROBE_LOCK:
        items = list(_SANDBOX_PROBE_CACHE.items())
    for key, verdict in items:
        if len(key) < 3 or key[0] != "verdict" or key[2] != provider_name:
            continue
        for name in rung_retirements(verdict):
            pair = (name, verdict.version or "")
            if pair not in found:
                found.append(pair)
    return found


def sandbox_bypass_line(
    provider_name: str, verdict: SandboxProbeResult,
    rungs: Sequence[SandboxRung] = (),
) -> str:
    """The ``[SANDBOX_BYPASSED]`` line for ``verdict``: the fixed stem plus the
    rung clause naming each rung tried with its outcome and probe tail
    (``rungs`` — the adapter's declared ladder — supplies ``removed_at``)."""
    return sandbox_bypassed_notice_text(
        provider_name,
        sandbox_walk_clause(
            provider_name, verdict.walk, verdict.rung_tails,
            verdict.version or None, rungs,
        ),
    )


#: Plan codex-sandbox-unavailable §7 "Step 4: the refusal's wording in each
#: state" (2026-09-30): every ``sandbox_unavailable`` refusal leads with an
#: option that works on this host today (F6), before it says why Codex cannot
#: run here. ``{key}`` is the refused key — ``driver.subagent_runner`` for
#: editing jobs.
F6_LEAD = (
    "To run this now, set `{key}` to a runner that is not Codex (for example "
    "`claude-code:<model>`) in `.multi-llm/providers.yaml`."
)

#: The three rung sentences of the step-4 refusal, picked from the walk.
JAIL_KEPT_OFF_SENTENCE = "The plugin's Landlock jail does not take this job: {case}."
JAIL_UNAVAILABLE_SENTENCE = (
    "The plugin's Landlock jail cannot run here either: this kernel or "
    "container lacks Landlock ({note}). Only a system-level change gives Codex "
    "a sandbox here: the AppArmor or sysctl repair `multi_llm.py doctor` "
    "prints, which needs sudo."
)
JAIL_SELF_TEST_SENTENCE = (
    "The plugin's Landlock jail is present but failed its self-test ({what}). "
    "Run `multi_llm.py doctor`: its `plugin-landlock` row shows the probe "
    "result."
)


def _f6_key(key: str) -> str:
    """The ``providers.yaml`` key the F6 lead names: the refused ``driver.*``
    key without its layer note, else ``driver.subagent_runner`` (a recorded or
    task-level spec is still replaced there)."""
    base = (key or "").split(" (", 1)[0].strip()
    return base if base.startswith("driver.") else "driver.subagent_runner"


def _f6_lead(key: str) -> str:
    return F6_LEAD.format(key=_f6_key(key))


def _sandbox_unavailable_rejection(
    *,
    key: str,
    spec: str,
    tail: str,
    rung_sentence: str = "",
    note: str = "",
    trailer: str = "",
) -> RunnerRejected:
    """The one ``sandbox_unavailable`` refusal text (plan §7 step 4): the F6
    lead; why Codex cannot run here (today's reason, then one rung sentence);
    the probe tail and the ladder note; "Nothing was dispatched." No sudo
    "Fix:" sentence — the AppArmor text lives in the reason, the
    Landlock-unavailable sentence and ``doctor``'s repair block only."""
    message = (
        f"{_f6_lead(key)} Refusing to dispatch: {key} is {spec!r} (reason: "
        f"sandbox_unavailable) — {_REASON_EXPLANATION['sandbox_unavailable']}. "
        + (f"{rung_sentence} " if rung_sentence else "")
        + f"Probe tail: {tail!r}. "
        + (trailer if trailer else "")
        + (f"Fallback ladder: {note}. " if note else "")
        + "Nothing was dispatched."
    )
    return RunnerRejected(
        message, key=key, spec=spec, reason_code="sandbox_unavailable", detail=tail,
    )


def _jail_rung(provider: Any) -> Optional[SandboxRung]:
    """The adapter's wrapping rung (the plugin's Landlock jail), from either
    ladder, or ``None`` when it declares none."""
    for profile in (*SANDBOX_FALLBACK_PROFILES, *SANDBOX_WRITE_FALLBACK_PROFILES):
        for rung in _fallback_rungs(provider, profile):
            if getattr(rung, "wrapper", None):
                return rung
    return None


def _installed_cli_version(provider_name: str, verdict: SandboxProbeResult) -> str:
    """The CLI version the preflight or the probe read, or ``""``."""
    for value in (
        verdict.version, _VERSION_CACHE.get(provider_name),
        _PROBE_VERSION_CACHE.get(provider_name),
    ):
        if value and value != "unknown":
            return str(value)
    return ""


def _newer_than(installed: str, measured: str) -> bool:
    """Whether ``installed`` is a newer version than ``measured``."""
    found = re.search(r"\d+(?:\.\d+)+", installed or "")
    if not found or not measured:
        return False
    try:
        return version_tuple(found.group(0)) > version_tuple(measured)
    except Exception:  # noqa: BLE001 - a wording choice never ends a refusal
        return False


def _jail_versions_clause(provider_name: str, rung: SandboxRung, verdict: SandboxProbeResult) -> str:
    """" Codex X is installed, newer than Y …" when it is, else ``""``."""
    measured = (getattr(rung, "measured_through", None) or ("",))[0]
    installed = _installed_cli_version(provider_name, verdict)
    if measured and _newer_than(installed, measured):
        return (
            f" Codex {installed} is installed, newer than {measured}, the "
            f"version the jail was measured through; a changed start-up write "
            f"list is the likely cause."
        )
    return ""


def _jail_rung_sentence(
    provider_name: str,
    provider: Any,
    profile: str,
    policy: Optional[str],
    verdict: SandboxProbeResult,
    write_scope: Optional[str],
) -> str:
    """The step-4 rung sentence for one refusal, picked from the walk's record
    (plan §7 "Step 4: the refusal's wording in each state").

    Kept off the rung (whatever the rung's state): a write profile with the
    step-3 opt-in off, a write dispatch with no grant, a scope the rung does
    not serve, a ``sandbox_fallback`` value that does not reach the rung, or
    ``MULTI_LLM_CODEX_SKIP_RUNG``. Otherwise the rung's own outcome: Landlock
    unavailable (the wrapper's exit 126 and its note), or a failed self-test
    (the failing control or path, and both codex versions when the installed
    one is newer than the rung was measured through). ``""`` for an adapter
    with no jail.
    """
    jail = _jail_rung(provider)
    if jail is None:
        return ""
    kept_off = JAIL_KEPT_OFF_SENTENCE.format
    if profile in SANDBOX_WRITE_FALLBACK_PROFILES:
        if not any(
            r.name == jail.name for r in _fallback_rungs(provider, profile)
        ):
            return kept_off(case=(
                "write jobs are not enabled on it (the step-3 opt-in is off)"
            ))
        if not write_scope:
            return kept_off(case=(
                "the write dispatch carries no write grant (no write scope)"
            ))
        if write_scope not in WRITE_SCOPES_ON_RUNG:
            return kept_off(case=(
                f"the {write_scope!r} write scope is not one the jail serves "
                f"({', '.join(WRITE_SCOPES_ON_RUNG)}); such a job needs a "
                f"non-Codex runner (F6, as above)"
            ))
    if policy == SANDBOX_FALLBACK_OFF:
        return kept_off(case=(
            f"providers.{provider_name}.sandbox_fallback=off reaches no "
            f"fallback rung"
        ))
    if policy == SANDBOX_FALLBACK_CONTAINED:
        return kept_off(case=(
            f"providers.{provider_name}.sandbox_fallback=contained does not "
            f"reach it: that value promises a real OS boundary, and the jail "
            f"stops stray writes, not the model"
        ))
    outcome = dict(verdict.walk or ()).get(jail.name)
    tail = dict(verdict.rung_tails or ()).get(jail.name, "")
    if outcome == RUNG_SKIPPED_BY_SWITCH:
        return kept_off(case=f"skipped by {SKIP_RUNG_ENV}")
    if outcome is None:
        return ""
    if outcome == RUNG_ABSENT and tail.startswith(
        landlock_dispatch.NOTE_PREFIX + "unavailable"
    ):
        note = tail[len(landlock_dispatch.NOTE_PREFIX):].strip()
        return JAIL_UNAVAILABLE_SENTENCE.format(note=note)
    if outcome in (RUNG_UNKNOWN, RUNG_UNPROBED):
        what = f"its probe gave no answer ({outcome})"
    elif outcome == RUNG_REJECTED:
        what = "a write or truncation its canary made was not denied"
    elif outcome == RUNG_ABSENT:
        # A required allow entry (the wrapper's own code, or a grant refused
        # before the spawn) names itself; otherwise the canary never finished.
        what = "" if tail else "the canary never reported a denied write"
    else:
        what = "an allowed write failed, or Codex did not start under the allow-list"
    if tail:
        what = f"{what}: {tail}" if what else tail
    return (
        JAIL_SELF_TEST_SENTENCE.format(what=what)
        + _jail_versions_clause(provider_name, jail, verdict)
    )


def _write_consent_bypass_line(
    provider_name: str,
    verdict: SandboxProbeResult,
    rungs: Sequence[SandboxRung],
    policy: Optional[str],
    write_scope: Optional[str],
) -> str:
    """The ``[SANDBOX_BYPASSED]`` line for an F5 write dispatch (plan step 6).

    Built here rather than through ``sandbox_bypassed_notice_text``, whose
    stem says "read-only phase": this is a WRITE phase, uncontained because
    the chat itself runs with ``danger-full-access`` and the plugin's jail
    could not take it. It keeps the marker, so counting ``[SANDBOX_BYPASSED]``
    still counts every uncontained dispatch."""
    clause = sandbox_walk_clause(
        provider_name, verdict.walk, verdict.rung_tails,
        verdict.version or None, rungs,
    )
    said = " ".join((verdict.tail or "").split())
    if len(said) > 160:
        said = said[:157].rstrip() + " …"
    text = f"{SANDBOX_BYPASSED_MARKER} {provider_name}: its own sandbox cannot start here"
    if said:
        text += f" ({said})"
    if clause:
        text += f"; {clause}"
    text += (
        f"; running this write phase (scope {write_scope or 'none'}) under "
        f"--sandbox danger-full-access because the chat itself runs with the "
        f"{HOST_POSTURE_FULL_ACCESS} sandbox posture ({HOST_SANDBOX_POSTURE_ENV}; "
        f"F5, plan step 6) and the plugin's Landlock jail could not take this "
        f"job, under providers.{provider_name}.sandbox_fallback="
        f"{policy or SANDBOX_FALLBACK_AUTO}: no OS boundary between the model's "
        f"shell and this machine"
    )
    return text


def _render_target(request: Optional[JailRequest]) -> Optional[str]:
    """The write target a notice names: the tasks directory under a dir rule,
    else the file; the repository root for ``repo-wide``; ``$HOME`` as ``~``."""
    if request is None:
        return None
    if request.write_scope == WRITE_SCOPE_REPO_WIDE:
        return landlock_dispatch.render_home(request.repo_root)
    shown = request.target_dir or request.target
    return landlock_dispatch.render_home(shown) if shown else None


def write_rung_notice(spec: str, jail_request: Optional[JailRequest]) -> Optional[str]:
    """The executor-lane ``[SANDBOX_INCIDENTAL]`` line for a write dispatch of
    ``spec`` that will run on the plugin's Landlock jail, or ``None``.

    Plan codex-sandbox-unavailable §6 F1 item 4 (2026-09-30): "a write
    dispatch on the rung prints that line before its batch starts". The
    scheduler prints it once before each batch on the rung; it is built with
    the same builder as every other ``[SANDBOX_INCIDENTAL]`` line, from what
    :func:`_detect_sandbox` recorded for this runner and scope, and names the
    scope and target from ``jail_request``. ``None`` for a batch on Codex's
    own sandbox, on no rung, or with no request.
    """
    if jail_request is None or not jail_request.write_scope:
        return None
    scope = jail_request.write_scope
    rung_id = sandbox_rung(spec, PROFILE_AGENT_WRITE, write_scope=scope)
    if not rung_id:
        return None
    parts = _SANDBOX_NOTICE_PARTS.get(
        _sandbox_decision_key(spec, PROFILE_AGENT_WRITE, scope, None)
    )
    if parts is None:
        return None
    provider_name, recorded_rung, policy, tail, clause = parts
    if recorded_rung != rung_id:
        return None
    provider = get_provider(provider_name)
    rung = next(
        (r for r in _fallback_rungs(provider, PROFILE_AGENT_WRITE) if r.name == rung_id),
        None,
    )
    if rung is None or not rung_is_incidental(rung):
        return None
    return sandbox_incidental_notice_text(
        provider_name, rung, policy, tail, walk_clause=clause,
        lane=INCIDENTAL_LANE_EXECUTOR, write_scope=scope,
        target=_render_target(jail_request),
    )


def repo_wide_write_refusal(
    spec: str,
    *,
    anchor: Optional[str],
    output_dir: Optional[str] = None,
    key: str = "driver.subagent_runner",
    budget_s: Optional[float] = ADVISORY_PROBE_BUDGET_S,
) -> Optional[str]:
    """Why a ``repo-wide`` write dispatch of ``spec`` (``implement``,
    ``apply-code-fixes``) would be refused on this host right now, or ``None``
    when it would run (racing-run issue #1's early warning, 2026-10-02).

    The same decision the dispatch takes — :func:`_detect_sandbox` with the
    ``agent-write`` profile and a repo-wide :class:`JailRequest` — so the
    answer is never a guess from recorded evidence: it runs the adapter's
    model-free probes once per process (the standard sandbox, then the rung
    walk) through the shared probe cache, and a runner with no sandbox probe
    (every adapter but codex) answers ``None`` with nothing spawned. The
    refusal text is the dispatch's own, led by F6 and ending in "Nothing was
    dispatched." Advisory: any failure other than the refusal reads as
    ``None``, because a warning that may be wrong is worse than none.

    Silent: :func:`_detect_sandbox` prints the preflight's own lines (the
    ``unknown`` note says "Dispatching anyway", which is wrong for a reader
    that dispatches nothing), so both streams are swallowed here; the only
    output is the warning the caller renders from the returned text. The
    decision is cached under the repo-wide scope key, so a read-only phase or
    a step-3 write phase that ends with the next-step block costs one rung
    probe for this scope on top of its own.

    ``budget_s`` (:data:`ADVISORY_PROBE_BUDGET_S`, 2026-10-02) bounds the
    probes: a hung or slow probe draws no warning, costs the reader at most
    the budget, and leaves nothing in the caches for a dispatch to inherit.
    ``None`` probes under the dispatch's own timeout.
    """
    import contextlib
    import io

    try:
        from .write_safety import resolve_repo_root
    except ImportError:  # pragma: no cover - direct-script import shim
        from utils.write_safety import resolve_repo_root  # type: ignore[no-redef]
    provider_name = str(spec).partition(":")[0]
    try:
        repo_root = resolve_repo_root(anchor)
        request = JailRequest(
            repo_root=repo_root, kind="implement", write_scope=WRITE_SCOPE_REPO_WIDE,
            output_dir=os.path.realpath(output_dir) if output_dir else None,
        )
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            _detect_sandbox(
                provider_name, key=key, spec=str(spec), profile=PROFILE_AGENT_WRITE,
                anchor=anchor, jail_request=request, probe_budget_s=budget_s,
            )
    except RunnerRejected as exc:
        return exc.message
    except Exception:  # noqa: BLE001 - advisory, never a failed status or init
        return None
    return None


def _uncontained_rung(provider: Any) -> Optional[SandboxRung]:
    """The adapter's uncontained rung (read ladder), for F5's consent check."""
    for rung in _fallback_rungs(provider, PROFILE_AGENT_READONLY):
        if rung.name == SANDBOX_RUNG_UNSANDBOXED:
            return rung
    return None


def _detect_sandbox(
    provider_name: str,
    *,
    key: str,
    spec: str,
    profile: str,
    anchor: Optional[str] = None,
    jail_request: Optional[JailRequest] = None,
    probe_budget_s: Optional[float] = None,
) -> str:
    """Run the adapter's model-free sandbox self-test once per host/spec/profile
    and refuse a runner whose own sandbox cannot run (D6 step 3).

    ``probe_budget_s`` marks an advisory read (``repo_wide_write_refusal``,
    2026-10-02): the probes run under that budget instead of
    :data:`SANDBOX_PROBE_TIMEOUT_S`, and a measurement the budget cut short
    answers ``unknown`` with nothing printed and nothing recorded — neither
    in the probe cache nor in the decision table — so the reader stays fast
    and silent while the dispatch, later or elsewhere, measures for itself.
    A settled measurement is cached and recorded as any other.

    Returns ``ok`` | ``unknown`` | ``not-required`` | ``bypassed`` | a rung id
    (``landlock``, ``plugin-landlock``); a non-zero exit with no permitted
    rung raises, because bubblewrap failing to start is a property of the
    machine — every sibling on this runner would fail identically, and a retry
    never changes it (the system-level AppArmor or sysctl repair ``multi_llm.py
    doctor`` prints is one way out, and needs sudo; a non-Codex runner is the
    other — the refusal leads with it, plan §7 step 4). A timeout or a command
    that could not run records ``unknown`` and dispatches, exactly like the
    nested-exec probe's inconclusive branch.

    A **rung** (D6 override 2026-09-17, landlock rung 2026-09-22) is the *only*
    way an ``unavailable`` verdict does not raise here: the adapter's ladder
    walk selected one, the adapter declares it for this profile, and the
    ``sandbox_fallback`` key permits it — a contained rung under ``auto`` or
    ``contained``, the uncontained and the incidental rung under ``auto``
    alone, nothing under ``off``. The selected rung's **id** is what gets
    recorded, so :func:`sandbox_rung` hands the dispatch the rung it must
    render.

    Plan codex-sandbox-unavailable (2026-09-30):

    * **Write profiles (steps 3 and 3b).** ``agent-write`` computes its policy
      too, and reaches exactly one rung, the plugin's Landlock jail, through
      :func:`write_rung_allowed` — ``auto`` alone, and only for a
      ``jail_request`` whose scope the rung serves (``plan-file``, ``tasks``
      and, since 2026-10-02, ``repo-wide``). A write dispatch with no scope
      walks no rung and is refused naming the case and F6. A failed rung
      probe is refused, never walked on. The decision key adds the scope.
    * **The incidental grade.** A rung of the ``incidental`` grade prints one
      ``[SANDBOX_INCIDENTAL]`` line (executor lane: no mode check, a warn-only
      home check), never ``[SANDBOX_BYPASSED]`` or ``[SANDBOX_FALLBACK]``.
    * **F5 (step 6).** Only when the plugin's jail could NOT take a write
      dispatch and the chat's own posture, read per call from this process's
      environment, is ``danger-full-access`` under ``auto``, the write takes
      the uncontained rung: a ``[SANDBOX_BYPASSED]`` line naming F5, and a
      decision word of its own stored under a key that carries the posture.
      Never under ``contained`` or ``off``, never ahead of the jail, never on a
      walk that measured nothing.
    * **Refusals (step 4)** lead with F6 and add one rung sentence picked from
      the walk.

    The measurement comes from the probe cache the fan-out shares
    (:func:`cached_sandbox_verdict`, 2026-09-24); the uncontained rung's line
    names every rung tried first, and a rung retired from this CLI build
    (skipped by version, or its probe's own panic text) gets the retirement
    line once per process.
    """
    provider = get_provider(provider_name)
    write = profile in SANDBOX_WRITE_FALLBACK_PROFILES
    scope = getattr(jail_request, "write_scope", None) if write else None
    consent = host_write_posture_consent() if write else None
    cache_key = _sandbox_decision_key(spec, profile, scope, consent)
    if cache_key in _SANDBOX_DECISIONS:
        return _sandbox_state_word(_SANDBOX_DECISIONS[cache_key])
    if consent is not None:
        # A rung taken without the posture stands with it too (the jail is
        # always preferred to F5); only the F5 word is posture-bound.
        recorded = _SANDBOX_DECISIONS.get(
            _sandbox_decision_key(spec, profile, scope, None)
        )
        if recorded and recorded not in _PLAIN_SANDBOX_STATES:
            return _sandbox_state_word(recorded)
    try:
        skip_rung_requested()
    except ValueError as exc:
        # Rejected at start-up, never silently ignored (F1 item 6).
        raise RunnerRejected(
            f"Refusing to dispatch: {exc}. Nothing was dispatched.",
            key=SKIP_RUNG_ENV, spec=spec, reason_code="invalid_skip_rung",
        ) from None

    policy: Optional[str] = (
        _sandbox_fallback_policy(provider, profile, anchor=anchor)
        if profile in SANDBOX_FALLBACK_PROFILES or write else None
    )
    verdict = cached_sandbox_verdict(
        provider_name, provider, profile, cwd=_probe_cwd(anchor), policy=policy,
        timeout=probe_budget_s,
        **({"jail_request": jail_request} if write and jail_request is not None else {}),
    )
    state, tail = verdict.state, verdict.tail
    if probe_budget_s is not None and probe_budget_cut(verdict):
        return "unknown"
    if state == "unavailable":
        rung = None
        if not write or scope in WRITE_SCOPES_ON_RUNG:
            rung = sandbox_fallback_rung(provider, profile, verdict.rung, policy)
        if rung is not None:
            declared = _fallback_rungs(provider, profile)
            # One line per runner per process, on stdout beside the other
            # preflight lines, in the same words the fan-out prints — the
            # reader greps one marker across the run. `unknown` never reaches
            # here: no rung widens anything on a probe that was not read.
            if rung_is_incidental(rung):
                clause = sandbox_walk_clause(
                    provider_name, verdict.walk, verdict.rung_tails,
                    verdict.version or None, declared,
                )
                if write:
                    # A write dispatch's line is the scheduler's to print, once
                    # before EACH batch on the rung (`write_rung_notice`, the
                    # same builder); printing it here too would show batch 0
                    # twice. What it is built from is kept, path-free.
                    _SANDBOX_NOTICE_PARTS[
                        _sandbox_decision_key(spec, profile, scope, None)
                    ] = (provider_name, rung.name, policy, tail, clause)
                else:
                    print(
                        "[exec-subagents] "
                        + sandbox_incidental_notice_text(
                            provider_name, rung, policy, tail, walk_clause=clause,
                            lane=INCIDENTAL_LANE_EXECUTOR,
                        )
                    )
            elif rung.contained:
                print(
                    "[exec-subagents] "
                    + sandbox_fallback_notice_text(provider_name, rung, policy)
                )
            else:
                print(
                    "[exec-subagents] "
                    + sandbox_bypass_line(provider_name, verdict, declared)
                )
                _announce_executor_retirements(provider_name, provider, spec, profile, verdict)
            # A decision without the posture is valid with it too: stored
            # under the posture-free key (`sandbox_rung` looks there second).
            _SANDBOX_DECISIONS[
                _sandbox_decision_key(spec, profile, scope, None)
            ] = rung.name
            return _sandbox_state_word(rung.name)
        # F5 serves the step-3 scopes alone (`WRITE_SCOPES_BY_CONSENT`):
        # repo-wide edits (`apply-code-fixes`, `implement`) run on the jail
        # since step 3b and never reach the uncontained rung by consent,
        # whatever the chat's posture (the safer reading, 2026-10-02).
        if write and consent is not None and scope in WRITE_SCOPES_BY_CONSENT:
            stopped = any(
                outcome in (RUNG_UNPROBED, RUNG_UNKNOWN)
                for _, outcome in (verdict.walk or ())
            )
            floor = _uncontained_rung(provider)
            if not stopped and write_consent_allows(floor, policy, consent):
                print(
                    "[exec-subagents] "
                    + _write_consent_bypass_line(
                        provider_name, verdict, _fallback_rungs(provider, profile),
                        policy, scope,
                    )
                )
                _SANDBOX_DECISIONS[cache_key] = SANDBOX_DECISION_WRITE_BY_CONSENT
                return SANDBOX_STATE_BYPASSED
    if state == "unavailable":
        declared = _fallback_rungs(provider, profile)
        if policy == SANDBOX_FALLBACK_CONTAINED:
            # The operator who opted into containment is the one who sees this
            # runner refused; a retired rung is named once per process here
            # too, worded as the refusal it is (plan §3.2).
            _announce_executor_retirements(
                provider_name, provider, spec, profile, verdict, refused=True,
            )
        note = sandbox_walk_note(
            verdict, policy, provider_name=provider_name, rungs=declared,
        )
        raise _sandbox_unavailable_rejection(
            key=key, spec=spec, tail=tail,
            rung_sentence=_jail_rung_sentence(
                provider_name, provider, profile, policy, verdict, scope,
            ),
            note=note,
        )
    if state == "unknown":
        print(
            f"multi-llm warning: the sandbox self-test for {spec} ({profile}) "
            f"could not be read within {SANDBOX_PROBE_TIMEOUT_S:.0f}s — recording "
            f"sandbox 'unknown'. Dispatching anyway; a broken sandbox will land on "
            f"the D3k ladder as sandbox_unavailable (rung 1).",
            file=sys.stderr,
        )
    _SANDBOX_DECISIONS[cache_key] = state
    return state


def _announce_executor_retirements(
    provider_name: str, provider: Any, spec: str, profile: str,
    verdict: SandboxProbeResult,
    *,
    refused: bool = False,
) -> None:
    """Print the retirement line once per process per provider and version
    for a rung ``verdict``'s walk found retired (plan §3.2). The fan-out's
    twin is ``review_orchestrator_base.announce_retired_rungs``. ``refused``
    words it for the ``contained`` refusal path, where the run did not fall
    to the uncontained rung."""
    for name in rung_retirements(verdict):
        marker = f"{provider_name}|{name}|{verdict.version or ''}"
        if marker in _RETIREMENTS_ANNOUNCED:
            continue
        declared = next(
            (r for r in _fallback_rungs(provider, profile) if r.name == name), None,
        )
        if declared is None:
            continue
        _RETIREMENTS_ANNOUNCED.add(marker)
        print(
            "[exec-subagents] "
            + sandbox_rung_retired_notice(
                provider_name, spec, declared, measured=True,
                version=verdict.version or None, refused=refused,
            )
        )


def _model_cache_key(
    provider: Any, provider_name: str, model: str, *, profile: str,
    anchor: Optional[str],
) -> str:
    """``<provider>|<hermetic on/off>|<config-content digest>|<normalized model>``.

    The digest is over the adapter's own merged ``providers.<name>`` block —
    the source every rebuilt ``OPENCODE_CONFIG_CONTENT`` and the hermetic policy
    are read from — so an edit that would change the listing changes the key.
    Every leg degrades to a constant rather than raising: a cache key may never
    be what ends a preflight.
    """
    hermetic = "plain"
    try:
        module = sys.modules.get(type(provider).__module__)
        enabled = getattr(module, "hermetic_enabled", None)
        if callable(enabled) and enabled(profile, anchor):
            hermetic = "hermetic"
    except Exception:  # noqa: BLE001
        hermetic = "plain"
    digest = "-"
    try:
        try:
            from .provider_registry import load_config
        except ImportError:  # pragma: no cover
            from utils.provider_registry import load_config
        block = (load_config(anchor=anchor).get("providers") or {}).get(provider_name)
        import hashlib

        digest = hashlib.sha256(
            json.dumps(block or {}, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()[:16]
    except Exception:  # noqa: BLE001
        digest = "-"
    normalized = model
    try:
        efforts = provider._accepted_efforts()  # noqa: SLF001 - the base's own hook
        normalized, _ = split_reasoning_effort(model, efforts)
    except Exception:  # noqa: BLE001
        normalized = model
    return f"{provider_name}|{hermetic}|{digest}|{normalized.strip()}"


def _detect_model(
    provider_name: str,
    model: str,
    *,
    key: str,
    spec: str,
    profile: str,
    anchor: Optional[str] = None,
) -> str:
    """Ask the CLI's own catalog whether ``model`` exists — once per slot (D3 step 3).

    The third and last leg about the *runner*, and the only one of the three
    model checks that spawns anything: ``describe_unresolvable_model`` is the
    structural, catalog-free refusal and the ``is_model_valid`` line is an
    advisory warning about *our* configured list; this is the CLI's answer.
    The adapter's :meth:`describe_unlisted_model` reads the listing inside the
    same dispatch context the dispatch will use (D3 step 4), under the same
    30 s ceiling every probe has — a listing that hangs is killed and read as
    unknown.

    Verdicts: ``known=True`` → ``"ok"``; ``known=False`` → the same
    ``RunnerRejected`` every other leg raises, reason ``invalid_model_catalog``
    (deliberately distinct from D4's dispatch-time ``runner_invalid_model``, so
    a preflight refusal and a dispatch-time one stay separable in a log), with
    the ``detail`` the adapter composed from the listing it just read;
    ``known=None`` → ``"unknown"``, printed like every other unknown and
    **never blocking** — the run proceeds exactly as it would with no probe at
    all, and D4 is the backstop that catches a real miss one attempt later in
    the provider's own words.

    **This runs at preflight and nowhere on the resolution ladder**: the ladder
    stays subprocess-free so ``status`` stays sub-second, and there is no rung
    fallback — the spec refused is the spec the ladder already finished
    resolving, whatever rung supplied it, and ``key`` names that rung.
    """
    provider = get_provider(provider_name)
    cache_key = _model_cache_key(
        provider, provider_name, model, profile=profile, anchor=anchor
    )
    if cache_key in _MODEL_CACHE:
        return _MODEL_CACHE[cache_key]

    try:
        verdict = provider.describe_unlisted_model(
            model, anchor=anchor, profile=profile
        )
    except TypeError:
        # An adapter (or a narrow double) declaring the plan's minimal
        # signature, without the profile keyword.
        try:
            verdict = provider.describe_unlisted_model(model, anchor=anchor)
        except Exception:  # noqa: BLE001 - a catalog read may never end a preflight
            verdict = None
    except Exception:  # noqa: BLE001 - a catalog read may never end a preflight
        verdict = None

    known = getattr(verdict, "known", None)
    if known is False:
        raise _render_runner_rejection(
            key=key, spec=spec, reason_code="invalid_model_catalog",
            profile=profile, detail=str(getattr(verdict, "detail", "") or ""),
        )
    state = "ok" if known is True else "unknown"
    overrides_hook = (
        getattr(type(provider), "describe_unlisted_model", None)
        is not LLMProvider.describe_unlisted_model
    )
    if state == "unknown" and overrides_hook:
        # Only an adapter that has a listing to read gets the warning: the
        # base's typed default is "no catalog here", which is not a failed read.
        print(
            f"multi-llm warning: could not confirm {model!r} against "
            f"{provider_name}'s own model listing — recording 'unknown' and "
            f"dispatching anyway; a model the runner really rejects is caught "
            f"on the first attempt in the runner's own words.",
            file=sys.stderr,
        )
    _MODEL_CACHE[cache_key] = state
    return state


def probe_setup_metadata(provider_name: str) -> Dict[str, str]:
    """Run an adapter's declared ``setup_probe`` and read it as metadata (M13, §5.2).

    The status path's counterpart to :func:`_detect_auth`, and deliberately not
    part of :func:`preflight_runner`: what this returns decides **nothing** — no
    refusal, no retry, no availability state — so a dispatch preflight would be
    paying a subprocess per phase for a sentence only a human reads. It is
    spawned from ``install-host --check`` row 5, which already runs the version
    and auth probes and is invoked by hand.

    It is not an auth probe and cannot become one. cursor-agent's ``about`` — the
    only declared readout today — returns the same two nulls for a logged-in CLI
    with the endpoint unreachable as for a logged-out one, which is why M13
    demoted it; the verdict comes from ``auth_check`` and only from there.

    Nothing here blocks or raises: an adapter that declares no readout, a probe
    that will not run, a reader that fails all report ``{}``, which renders as a
    status row with one less fact on it.

    Returns:
        ``label -> value`` exactly as the adapter's
        :meth:`~utils.providers.base.LLMProvider.read_setup_probe` reported it,
        minus any blank value. Every pair is rendered into a status row, so the
        adapter owes it the same care a refusal message is owed (§4.5.1).
    """
    provider = get_provider(provider_name)
    argv = list(getattr(provider, "setup_probe", ()) or ())
    if provider is None or not argv:
        return {}
    completed = _run_probe(argv)
    if completed is None:
        return {}
    try:
        facts = provider.read_setup_probe(
            completed.stdout, completed.stderr, completed.returncode
        )
    except Exception:  # noqa: BLE001 - a readout never breaks the status path
        return {}
    return {
        str(label): str(value).strip()
        for label, value in (facts or {}).items()
        if str(value).strip()
    }


def _host_nested_exec() -> Optional[Tuple[str, Dict[str, str], str]]:
    """``(host_id, {leg: state}, notes)`` for the running host, or ``None``.

    ``None`` means the capability data could not be read at all (a partial
    install, a direct script run without ``utils`` importable). That is the one
    case where the nested-exec leg is skipped outright rather than probed: a
    throwaway dispatch is a real billed turn, and "I do not know which host I am
    on" is not a reason to spend one — nor to refuse, since the legs it would
    have answered are exactly the ones the reactive D3k ladder still catches.
    """
    try:
        from . import host_capabilities as caps
    except ImportError:  # pragma: no cover - direct script runs
        try:
            import host_capabilities as caps  # type: ignore
        except ImportError:
            return None
    try:
        host_id = caps.resolve_host_id(sys.argv[1:])
        declared = caps.nested_exec(host_id)
    except Exception:  # pragma: no cover - unknown host / missing data
        return None
    notes = str(declared.pop("notes", "") or "").strip()
    legs = {
        leg: str(declared.get(leg) or "unknown")
        for leg in caps.NESTED_EXEC_LEGS
    }
    return host_id, legs, notes


def _detect_nested_exec(
    provider_name: str,
    model: str,
    *,
    key: str,
    spec: str,
    spawn_observed: bool = False,
    probe: bool = True,
) -> str:
    """Can a runner really run *inside this host*? Once per host/runner (D3c).

    Presence, version and auth are all facts about the runner; this is the one
    preflight leg about the **host**. Three verdicts:

    * a declared ``denied`` leg → exit 3 naming the field and its notes, before
      anything is scheduled. Every task in the batch would fail identically, and
      a sandbox that denies a spawn or an egress usually eats the failure into
      something the D3k ladder reads as generic runner noise and *retries*.
    * every leg ``allowed`` → ``"allowed"``, with no child spawned. The data has
      already answered; a probe would only spend a billed turn re-confirming it.
    * anything ``unknown`` or ``needs-config`` → one throwaway ``agent-readonly``
      dispatch, cached per ``host|spec`` for the process, whose recognized
      denials are the same exit 3 and whose inconclusive outcomes are
      ``"unknown"`` (a preflight probe reports; it never blocks on its own
      failure).
    """
    resolved = _host_nested_exec()
    if resolved is None:
        return "unknown"
    host_id, legs, notes = resolved

    denied = [leg for leg in legs if legs[leg] == "denied"]
    if denied:
        raise RunnerRejected(
            f"Refusing to dispatch: host {host_id!r} declares nested_exec "
            f"{', '.join(denied)} denied (reason: nested_exec_denied) — "
            f"{_REASON_EXPLANATION['nested_exec_denied']}. "
            + (f"{notes} " if notes else "")
            + f"Fix: drop --exec-subagents and let this host's own subagent "
            f"mechanism run the phase, or run it from a host whose nested_exec "
            f"permits a nested CLI. Nothing was dispatched.",
            key=key,
            spec=spec,
            reason_code="nested_exec_denied",
        )

    cache_key = f"{host_id}|{spec}"
    cached = _NESTED_CACHE.get(cache_key)
    if cached is not None:
        return cached

    unresolved = [leg for leg in legs if legs[leg] != "allowed"]
    if spawn_observed and unresolved == ["spawn"]:
        # The version probe already ran this CLI as a child of this host's shell,
        # which is the whole of the spawn leg. Nothing else is open, so there is
        # nothing left for a billed turn to answer.
        unresolved = []
    if not unresolved:
        _NESTED_CACHE[cache_key] = "allowed"
        return "allowed"
    if not probe:
        # Deliberately uncached: the declared verdict has not been answered, and a
        # later real dispatch in this same process must still get its probe.
        return "unknown"

    state = _probe_nested_exec(
        provider_name, model,
        key=key, spec=spec, host_id=host_id, legs=unresolved, notes=notes,
    )
    _NESTED_CACHE[cache_key] = state
    return state


def _probe_nested_exec(
    provider_name: str,
    model: str,
    *,
    key: str,
    spec: str,
    host_id: str,
    legs: Sequence[str],
    notes: str,
) -> str:
    """The throwaway dispatch behind an ``unknown``/``needs-config`` leg (D3c).

    One trivial ``agent-readonly`` turn, through the *same* :func:`_spawn` the
    batch uses — same argv builder, same composed environment, same host env
    guards — because a probe that composed its own child would answer a question
    about a process the batch never runs. Only a recognized denial refuses:

    * the child could not be started at all → the spawn leg, exit 3;
    * a login/credential notice → the credentials leg, exit 3 (from inside a
      sandbox this is as often the host's doing as a logged-out CLI, and neither
      is retryable);
    * an egress failure → the network leg, exit 3.

    ``allowed`` requires the reply to carry :data:`NESTED_PROBE_MARKER` — the word
    the prompt asked for. A clean exit whose output never mentions it is
    ``unknown`` under a warning of its own, distinct from the inconclusive one
    below so a log tells the two causes apart.

    Everything else — a timeout, a non-zero exit with nothing recognized, a
    silent zero-byte success, a clean exit that answered with something other
    than the token, an adapter that will not render the probe — is ``unknown``
    plus one warning line. The reactive ladder still covers those, and blocking a
    batch on an unreadable probe would be worse than the dispatch the probe
    exists to save.
    """
    provider = get_provider(provider_name)
    if provider is None:  # pragma: no cover - presence is checked before this
        return "unknown"
    opened = "/".join(legs)
    try:
        capture = _spawn(
            provider=provider,
            model=model,
            prompt=NESTED_PROBE_PROMPT,
            # Always read-only, never the batch's own profile: a preflight has no
            # result to write, so it has no reason to hold write access.
            profile=PROFILE_AGENT_READONLY,
            transport=preferred_prompt_transport(provider_name),
            timeout=NESTED_PROBE_TIMEOUT_S,
            cwd=None,
        )
    except Exception as exc:  # noqa: BLE001 - a probe reports, it never blocks
        print(
            f"multi-llm warning: could not render the nested-exec probe for "
            f"{spec} on host {host_id} ({exc}) — recording nested_exec "
            f"'unknown' for {opened}.",
            file=sys.stderr,
        )
        return "unknown"

    trailer = (
        f"Host: {host_id} (nested_exec {opened} was not recorded as allowed). "
        + (f"{notes} " if notes else "")
    )

    if capture.launch_error is not None:
        raise RunnerRejected(
            f"Refusing to dispatch: {key} is {spec!r} (reason: nested_exec_spawn) "
            f"— {_REASON_EXPLANATION['nested_exec_spawn']}: "
            f"{capture.launch_error}. {trailer}"
            f"Fix: grant this host's sandbox permission to start the runner, or "
            f"run the phase without --exec-subagents. Nothing was dispatched.",
            key=key,
            spec=spec,
            reason_code="nested_exec_spawn",
        )

    streams = f"{capture.stdout or ''}\n{capture.stderr or ''}".lower()

    if capture.timed_out:
        # A note, not a warning (2026-10-05, run 3): nothing here is the
        # user's to act on. A slow model's first turn routinely outlives the
        # probe (opencode/big-pickle, every run), the batch is dispatched anyway,
        # and a host that really blocks nested runs fails that batch with its
        # own timeout, which is where the user is told.
        print(
            f"[exec-subagents] note: the start-up check for {spec} (a one-word "
            f"test turn) did not answer within {NESTED_PROBE_TIMEOUT_S:.0f}s, so "
            f"it is unconfirmed that host {host_id} lets the runner start its "
            f"own model turn; dispatching anyway (nested_exec 'unknown' for "
            f"{opened}). Nothing to do unless a batch then times out.",
            file=sys.stderr,
        )
        return "unknown"

    classified = _classify_failed_run(provider, capture)
    if classified is not None and classified[0] == STATUS_AUTH_FAILED:
        login = getattr(provider, "login_cmd", "") or f"{provider_name} login"
        raise RunnerRejected(
            f"Refusing to dispatch: {key} is {spec!r} (reason: "
            f"nested_exec_credentials) — "
            f"{_REASON_EXPLANATION['nested_exec_credentials']}. "
            f"Probe tail: "
            f"{_redact_probe_tail(capture.stderr or capture.stdout, 500)!r}. "
            f"{trailer}"
            f"Fix: run `{login}` from outside this host, or allow the runner to "
            f"read its credential store from inside it. Nothing was dispatched.",
            key=key,
            spec=spec,
            reason_code="nested_exec_credentials",
        )

    if classified is not None and classified[0] == STATUS_SANDBOX_UNAVAILABLE:
        # D6 step 4. The path that catches what step 3 has no command for —
        # any bubblewrap user whose adapter declares no `sandbox_probe_command`
        # — and, like the D4 branch below, opportunistic: it runs only where a
        # leg was unresolved and a probe therefore happened. A `bwrap:` line is
        # a fact about the machine, so every sibling fails identically and a
        # retry never changes it. The way out that works today is a non-Codex
        # runner (F6), which the refusal leads with; the AppArmor or sysctl
        # repair `doctor` prints is a system-level alternative that needs sudo
        # (plan codex-sandbox-unavailable §7 step 4, 2026-09-30). This
        # refusal walks no rung, so it carries no rung sentence.
        tail = _redact_probe_tail(capture.stderr or capture.stdout, 500)
        raise _sandbox_unavailable_rejection(
            key=key, spec=spec, tail=tail, trailer=trailer,
        )

    if classified is not None and classified[0] == STATUS_INVALID_MODEL:
        # D4 step 3. Opportunistic by construction: this branch only runs on a
        # host where a leg was still unresolved and a probe therefore happened.
        # The unconditional pre-dispatch gate is the preflight catalog leg (D3);
        # the guarantee when neither can answer is the fatal rung-1 status the
        # first real batch records. What this buys is zero dispatches where a
        # billed probe was going to run anyway.
        #
        # The window is `_classify_failed_run`'s 2000 bytes rather than the 500
        # the other legs quote: a login notice is the last thing a CLI prints,
        # but opencode's `ProviderModelNotFoundError` — the one line with the
        # "Did you mean" list — sits above a bun stack trace that alone
        # outruns 500 bytes, and a refusal that quotes only the frames has
        # thrown away the reason it exists to print.
        tail = _redact_probe_tail(capture.stderr or capture.stdout, 2000)
        raise RunnerRejected(
            f"Refusing to dispatch: {key} is {spec!r} (reason: "
            f"runner_invalid_model) — "
            f"{_REASON_EXPLANATION['runner_invalid_model']}. "
            f"Probe tail: {tail!r}. "
            f"{trailer}"
            f"Fix: set `{key}` to a model this CLI lists "
            f"(`{provider_name} models`), or update the plugin's host default. "
            f"Nothing was dispatched.",
            key=key,
            spec=spec,
            reason_code="runner_invalid_model",
            detail=tail,
        )

    if matches_any(NETWORK_DENIAL_PATTERNS, streams):
        raise RunnerRejected(
            f"Refusing to dispatch: {key} is {spec!r} (reason: "
            f"nested_exec_network) — "
            f"{_REASON_EXPLANATION['nested_exec_network']}. "
            f"Probe tail: "
            f"{_redact_probe_tail(capture.stderr or capture.stdout, 500)!r}. "
            f"{trailer}"
            f"Fix: allow this host's sandbox to reach the provider API (a domain "
            f"allow-list entry, a proxy setting), or run the phase without "
            f"--exec-subagents. Nothing was dispatched.",
            key=key,
            spec=spec,
            reason_code="nested_exec_network",
        )

    if capture.exit_code == 0 and streams.strip():
        # The probe asked for a word; this is where it is read back. Until
        # 2026-09-22 the verdict was "exit 0 and *something* on a stream", which
        # a usage banner, a progress spinner or a CLI that echoed its prompt and
        # quit all satisfy — so `allowed` meant "the binary ran", not "a model
        # answered through this host", and the container lane recorded it for a
        # runner whose every turn had been refused 422.
        #
        # PRESENCE, NOT EQUALITY, and deliberately so. These are the runner's raw
        # streams, not a parsed answer: every agent CLI this dispatches wraps the
        # reply in its own envelope (NDJSON events, usage counters, a `--print-
        # logs` tail), and `_probe_nested_exec` never calls `parse_output` — a
        # preflight has no result document, and adding a parse step here would
        # let an adapter's parser failure turn a working host into `unknown`. So
        # the prompt's "and nothing else" is a request for a cheap turn, not a
        # condition the verdict rests on; holding a model to literal exactness
        # would measure instruction-following rather than nested exec.
        #
        # The known hole, stated rather than papered over: a runner that echoes
        # our prompt into its own event stream carries the token whether or not a
        # model ever answered. That case read `allowed` under the old rule too,
        # so nothing regresses — this is strictly the tighter gate — and the
        # reactive D3k ladder still covers what it lets through.
        if NESTED_PROBE_MARKER.lower() in streams:
            return "allowed"
        print(
            f"multi-llm warning: the nested-exec probe for {spec} on host "
            f"{host_id} exited 0 with {len(streams.strip())} byte(s) of output, "
            f"but none of it carried the probe's token ({NESTED_PROBE_MARKER}) — "
            f"recording nested_exec 'unknown' for {opened}. The runner started "
            f"and returned, so this is not a denial; what is unproven is that a "
            f"model answered through it. Dispatching anyway; a real denial will "
            f"land on the D3k ladder.",
            file=sys.stderr,
        )
        return "unknown"

    print(
        f"multi-llm warning: the nested-exec probe for {spec} on host {host_id} "
        f"was inconclusive (exit {capture.exit_code}, "
        f"{len(streams.strip())} byte(s) of output) — recording nested_exec "
        f"'unknown' for {opened}. Dispatching anyway; a real denial will land on "
        f"the D3k ladder.",
        file=sys.stderr,
    )
    return "unknown"


def _host_env_guards() -> Tuple[List[str], List[str]]:
    """``(strip, passthrough)`` from the running host's ``env_guards`` (D3c/D5b).

    Under ``subagents: executor`` the runner is a *grandchild* — the host's shell
    tool spawned this dispatcher, this dispatcher spawns the runner — so the child
    inherits the host's injected variables on top of the runner's own: the
    nested-session marker that makes a same-binary runner refuse to start, and the
    session/skill ids that make it join or overwrite the parent's session instead
    of running its own turn. The adapter's ``get_remove_env()`` only knows about
    the *runner*, so the strip list is the union of the two, composed here at the
    single spawn site.

    Deliberately non-fatal, like :func:`_host_ceiling`: a partial install that
    cannot answer falls back to the adapter's own list rather than failing a
    dispatch.
    """
    try:
        from . import host_capabilities as caps
    except ImportError:  # pragma: no cover - direct script runs
        try:
            import host_capabilities as caps  # type: ignore
        except ImportError:
            return [], []
    try:
        declared = caps.env_guards(caps.resolve_host_id(sys.argv[1:]))
    except Exception:  # pragma: no cover - unknown host / missing data
        return [], []
    return (
        [*declared["guards"], *declared["session_scoped"]],
        list(declared["passthrough"]),
    )


def _host_ceiling() -> Optional[int]:
    """This host's ``max_concurrent_subagents``, or ``None`` if it cannot be read.

    ``sys.argv[1:]`` is passed for the same reason :func:`_host_env_guards` and
    :func:`_host_nested_exec` pass it: a shim declares its host by baking
    ``--host <id>`` into the dispatcher line, and ``$MULTI_LLM_HOST`` is only the
    *fallback* for a host that calls ``multi_llm.py`` directly (D5b). Reading the
    env alone made every argv-declared host answer the reference host's ceiling —
    an ``opencode`` run recorded ``host_max_concurrent_subagents: 10`` against an
    entry that declares 4 — so the one leg of D3i's minimum that is a fact about
    the host was silently the wrong host's.

    Deliberately non-fatal: the ceiling is a *bound*, and a partial install that
    cannot answer must not turn a dispatch into a hard failure — the driver and
    provider legs of the minimum still apply.
    """
    try:
        from . import host_capabilities as caps
    except ImportError:  # pragma: no cover - direct script runs
        try:
            import host_capabilities as caps  # type: ignore
        except ImportError:
            return None
    try:
        return caps.max_concurrent_subagents(caps.resolve_host_id(sys.argv[1:]))
    except Exception:  # pragma: no cover - unknown host / missing data
        return None


def effective_ceiling(
    runners: Sequence[str],
    *,
    anchor: Optional[str] = None,
    host_max: Optional[int] = None,
) -> Dict[str, Any]:
    """The three-way minimum, computed per dispatch and logged once (D3i).

    ``driver.max_concurrent_subagents`` (user) × the runner provider's
    ``max_concurrent`` × the host's own ceiling from the capability data. Returned
    as a record rather than a bare int so the batch report and the log line can
    both say *which* ceiling bound the batch.

    Args:
        host_max: The host's ``max_concurrent_subagents``. ``None`` means "look it
            up from ``hosts/capabilities.yaml`` for the host this invocation
            declared" (D5b) — the seam is this parameter, not a second code path,
            and a caller that already knows the number still passes it directly.
    """
    if host_max is None:
        host_max = _host_ceiling()
    driver_gate = get_max_concurrent_subagents(anchor=anchor)
    provider_limits: Dict[str, Optional[int]] = {}
    for spec in dict.fromkeys(runners):
        provider_name, _ = parse_model_spec(spec, anchor=anchor)
        provider_limits[provider_name] = get_provider_max_concurrent(
            provider_name, anchor=anchor
        )

    candidates = [driver_gate]
    if host_max is not None:
        candidates.append(host_max)
    limits = [limit for limit in provider_limits.values() if limit is not None]
    if limits:
        candidates.append(max(limits))
    effective = max(1, min(candidates))
    return {
        "effective": effective,
        "driver_max_concurrent_subagents": driver_gate,
        "host_max_concurrent_subagents": host_max,
        "provider_max_concurrent": {
            name: limit for name, limit in provider_limits.items()
        },
    }


# ---------------------------------------------------------------------------
# D3f — containment and the atomic write
# ---------------------------------------------------------------------------

def _is_unsafe_windows_path(name: str) -> bool:
    """Drive-relative (``C:foo``), UNC (``\\\\host\\share``) or an ADS (``a.json:x``)."""
    if name.startswith("\\\\") or name.startswith("//"):
        return True
    if re.match(r"^[A-Za-z]:", name):
        return True
    # An NTFS alternate data stream: a colon anywhere in a *basename*.
    return ":" in name


def resolve_output_target(task: Dict[str, Any], phase_dir: str) -> Path:
    """Resolve and contain a task's ``output_name`` under ``phase_dir`` (D3f).

    ``output_name`` resolved against the dir the task file was actually loaded
    from is authoritative; an absolute ``output_path`` in the JSON is accepted
    only when it resolves to that same file. Task files are persisted in the
    target workspace, survive across runs and (after D2) embed untrusted text, so
    a stale, hand-edited or injected path is an arbitrary-file-overwrite
    primitive.

    Raises:
        ResultRejected: status ``rejected`` (rung 7, no child started), naming the
            task, the offending path and the rule violated.
    """
    task_id = task.get("task_id", "<unnamed>")
    kind = task.get("kind", "")
    name = task.get("output_name")

    def _reject(rule: str, offending: Any) -> "ResultRejected":
        return ResultRejected(
            f"Task {task_id}: refusing the output path {offending!r} — {rule}. "
            f"Phase dir: {phase_dir}. Nothing was written and nothing was "
            f"dispatched.",
            STATUS_REJECTED,
        )

    if not isinstance(name, str) or not name:
        raise _reject("output_name must be a non-empty string", name)
    if os.path.basename(name) != name or _is_unsafe_windows_path(name):
        raise _reject(
            "output_name must be a bare basename (no separators, no drive-relative "
            "or UNC prefix, no alternate data stream)",
            name,
        )
    if (
        name in RESERVED_OUTPUT_NAMES
        or any(name.startswith(prefix) for prefix in RESERVED_OUTPUT_PREFIXES)
        or any(name.endswith(suffix) for suffix in RESERVED_OUTPUT_SUFFIXES)
    ):
        raise _reject(
            "it collides with an orchestrator-owned artifact (the task file, "
            "grouped.json, state, the run log or the batch report)",
            name,
        )
    pattern = OUTPUT_NAME_PATTERN_BY_KIND.get(kind)
    if pattern is None:
        raise _reject(f"kind {kind!r} is not one the executor dispatches", name)
    if not pattern.match(name):
        raise _reject(
            f"it does not match the {kind} output pattern {pattern.pattern!r}, so "
            f"the reaggregation glob could be fed a foreign file",
            name,
        )
    # `salvage`'s pattern is necessarily broad — its output IS a model result file
    # — so it must not be allowed to land on another kind's result. Without this a
    # hand-edited or injected salvage task could overwrite validation_batch_0.json
    # with a suggestion array that the merge would then read as validation.
    if kind == "salvage":
        for other_kind, other_pattern in OUTPUT_NAME_PATTERN_BY_KIND.items():
            if other_kind != "salvage" and other_pattern.match(name):
                raise _reject(
                    f"it is the {other_kind} result filename, which a salvage "
                    f"task may never write",
                    name,
                )

    resolved_dir = Path(phase_dir).resolve()
    # Refuse to write *through* a symlink at the final component, before the
    # containment test — otherwise a link pointing outside the phase dir would be
    # reported as an "outside the phase dir" escape and the fix ("stop symlinking
    # the result file") would not be in the message.
    if (resolved_dir / name).is_symlink():
        raise _reject("the target is a symlink", str(resolved_dir / name))
    # Resolve AFTER joining, so a symlinked path component cannot redirect the
    # write, then require containment beneath the resolved phase dir.
    candidate = (resolved_dir / name).resolve()
    try:
        contained = candidate.is_relative_to(resolved_dir)
    except AttributeError:  # pragma: no cover - Python < 3.9
        contained = os.path.commonpath([str(candidate), str(resolved_dir)]) == str(
            resolved_dir
        )
    if not contained or candidate == resolved_dir:
        raise _reject("it resolves outside the phase directory", str(candidate))

    declared = task.get("output_path")
    if isinstance(declared, str) and declared:
        declared_path = Path(declared)
        if not declared_path.is_absolute():
            declared_path = resolved_dir / declared_path
        # Resolve BOTH sides (D1c: asymmetry is the bug). ``make_task`` derives
        # ``output_path`` from the *unresolved* phase-dir string, so whenever that
        # path crosses a symlink — a symlinked repo root, macOS ``/tmp`` →
        # ``/private/tmp``, a CI workspace link — a normpath-only comparison
        # differs from the resolved candidate and every task in the phase is
        # refused before dispatch. D3f accepts an absolute ``output_path`` that
        # RESOLVES to the same file, which is what this compares.
        try:
            declared_resolved = declared_path.resolve()
        except OSError:  # pragma: no cover - unresolvable path is a mismatch
            declared_resolved = Path(os.path.normpath(str(declared_path)))
        if declared_resolved != candidate:
            raise _reject(
                "the task's absolute output_path does not resolve to "
                f"{candidate} (names are authoritative, paths are a "
                "convenience field)",
                declared,
            )

    return resolved_dir / name


def _atomic_write_json(path: str, data: Any) -> None:
    """Write ``data`` as JSON via a same-directory temp file, 0600, ``os.replace``.

    An executor killed mid-batch (expected on the D4 detached path) therefore
    never leaves a half-written result for the reaggregation glob to pick up.
    """
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_name(f".{target.name}.{os.getpid()}.tmp")
    payload = json.dumps(data, indent=2)
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    handle = os.open(str(tmp), flags, 0o600)
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        try:
            os.unlink(str(tmp))
        except OSError:
            pass
        raise
    os.replace(str(tmp), str(target))
    try:
        os.chmod(str(target), 0o600)
    except OSError:  # pragma: no cover - exotic filesystems
        pass


def persist_result(task: Dict[str, Any], phase_dir: str, data: Any) -> str:
    """The invoker-persists leg of the D3a contract. Returns the path written.

    **Shared by both invokers.** The executor calls it with the JSON it extracted
    from captured stdout; :func:`simulate_native_invoker` calls it with the JSON a
    driving agent's subagent returned. Same containment, same serialization, same
    bytes — which is what makes the result-contract equivalence assertion possible
    rather than aspirational.

    Deliberately does **not** branch on ``result_channel``: ``file`` is the only
    behavior the executor has, so a task carrying ``inline-json`` is refused
    before dispatch instead of selecting a second write path here.
    """
    target = resolve_output_target(task, phase_dir)
    encoded = json.dumps(data, indent=2)
    if len(encoded.encode("utf-8")) > MAX_RESULT_BYTES:
        raise ResultRejected(
            f"Task {task.get('task_id')}: the extracted result is "
            f"{len(encoded.encode('utf-8'))} bytes, over the {MAX_RESULT_BYTES}-byte "
            f"cap. Rejected rather than truncated — a truncated result file would "
            f"still parse and would reaggregate as a real one.",
            STATUS_SCHEMA_INVALID,
        )
    _atomic_write_json(str(target), data)
    return str(target)


# ---------------------------------------------------------------------------
# Extraction and per-kind result validation
# ---------------------------------------------------------------------------

#: The kinds whose result is one JSON object (their schema's root is an
#: object): the write report, the task list, a consolidation batch and the
#: judge's verdicts. Validation's reply may be a bare array, a salvage's is
#: one.
OBJECT_RESULT_KINDS = frozenset({
    "task_generation", "consolidation", "human_decision_judge", *WRITE_KINDS,
})


def the_reply_object(kind: str, data: Any, extracted: Mapping[str, Any]) -> Any:
    """*data*, or the reply's one JSON object when *kind*'s result is an
    object and the extraction served an array (fix round 28, live run 12 #6).

    Codex decline batch 0 opened its reply with two prose lines, then the
    report object; the adapter's array-preferring extraction served the
    report's own ``declined`` array (an array holding an object ranks as an
    answer), the batch read "<root>: expected type object, got list", and a
    repair re-ask restated the same report. The extractor names the reply's
    one object outside every other document (``only_object``,
    :func:`utils.json_extractor._only_object`); a reply holding two such
    objects names none and keeps its re-ask, as a validation reply holding
    two does. Both invokers read a reply through this."""
    if kind in OBJECT_RESULT_KINDS and isinstance(data, list):
        whole = extracted.get("only_object") if isinstance(extracted, Mapping) else None
        if isinstance(whole, dict):
            return whole
    return data


def extract_result(provider: Any, stdout: str, stderr: str, *, prefer_arrays: bool) -> Any:
    """Recover the subagent's answer: ``parse_output`` first, then extraction.

    :func:`_extract_result_and_syntax` without the syntax diagnosis.
    """
    return _extract_result_and_syntax(
        provider, stdout, stderr, prefer_arrays=prefer_arrays
    )[0]


def _extract_result_and_syntax(
    provider: Any, stdout: str, stderr: str, *, prefer_arrays: bool,
    kind: str = "",
) -> Tuple[Any, Optional[Dict[str, Any]]]:
    """Recover the subagent's answer: ``parse_output`` first, then extraction.

    Returns ``(data, enclosing_syntax_error)``: the second is the extractor's
    own report (``json_extractor.extract_json_from_text``) that ``data`` is a
    piece of a larger document which does not parse, else ``None``. It comes
    from whichever extraction served ``data`` — the adapter's, handed back on
    its ``parse_output`` dict, or this function's own for an adapter that
    returns text — so nothing scans the reply a second time to rediscover it.

    The ordering is **mandatory, not an optimization** (D3): provider CLIs emit
    structured event streams, so running ``json_extractor`` over raw stdout would
    match an event envelope or a reasoning item instead of the answer, and
    silently write a garbage result that reaggregation would accept.

    Adapters already run ``extract_json_from_text`` on the text they recover, so
    a dict/list ``data`` is the extracted result; a *string* ``data`` (adapters
    that return raw text) goes through ``utils/json_extractor`` here.

    Raises:
        ResultRejected: rung 4 (``runner_error``) when the adapter recovered no
            response text at all, rung 5 (``unparseable_result``) when it recovered
            text but no result object.
    """
    if len(stdout.encode("utf-8", errors="replace")) > MAX_STREAM_BYTES:
        raise ResultRejected(
            f"the runner produced more than {MAX_STREAM_BYTES} bytes on stdout; "
            f"refusing to parse it rather than truncating a stream into a result",
            STATUS_UNPARSEABLE,
        )

    parsed = provider.parse_output(stdout, stderr)
    if not isinstance(parsed, dict):  # pragma: no cover - adapter contract
        raise ResultRejected(
            "the adapter's parse_output did not return a result dict",
            STATUS_RUNNER_ERROR,
        )

    if not parsed.get("success"):
        raw = parsed.get("raw")
        error = parsed.get("error") or "parse_output reported failure"
        if isinstance(raw, str) and raw.strip():
            # Text WAS recovered; it just carries no result object (prose, a
            # refusal, a truncated stream) → rung 5.
            raise ResultRejected(str(error), STATUS_UNPARSEABLE)
        reason = None
        try:
            reason = provider.describe_failure(stdout, stderr)
        except Exception:  # noqa: BLE001 - diagnostics must not raise
            reason = None
        if reason:
            error = f"{error}: {reason}"
        # M10 (§5.1) — the **status**-consumer half of this site, on the same
        # rule as `llm_client`'s twin and through the same shared helper, so a
        # login notice reads the same on both lanes. Diagnostics only: the rung
        # is still `STATUS_RUNNER_ERROR`, decided above and not by this line.
        unavailable = availability_from_failure(provider, stdout, stderr)
        if unavailable is not None:
            error = f"{error} [{unavailable.value}]"
        raise ResultRejected(str(error), STATUS_RUNNER_ERROR)

    data = parsed.get("data")
    syntax = parsed.get("enclosing_syntax_error")
    served: Mapping[str, Any] = parsed
    if isinstance(data, str):
        extracted = extract_json_from_text(data, prefer_arrays=prefer_arrays)
        if not extracted.get("success"):
            raise ResultRejected(
                extracted.get("error") or "no JSON found in the recovered text",
                STATUS_UNPARSEABLE,
            )
        data = extracted.get("data")
        syntax = extracted.get("enclosing_syntax_error")
        served = extracted
    whole = the_reply_object(kind, data, served)
    if whole is not data:
        # The object parsed whole: the array's syntax note was about it.
        data, syntax = whole, None
    if data is None or (isinstance(data, dict) and set(data.keys()) == {"raw"}):
        raise ResultRejected(
            "the adapter recovered no result object from the stream",
            STATUS_UNPARSEABLE,
        )
    if not isinstance(data, (dict, list)):
        raise ResultRejected(
            f"the recovered result is a {type(data).__name__}, not a JSON object "
            f"or array",
            STATUS_UNPARSEABLE,
        )
    return data, syntax if isinstance(syntax, dict) else None


def _validation_result_errors(data: Any) -> List[str]:
    """Structural check for a ``validation_batch_N.json`` / revalidation result.

    There is no shipped JSON Schema for these (the merge deliberately tolerates
    several index shapes and joins by ``group_hash``), so this pins the two things
    the merge cannot recover from: it must be a wrapper object with a ``groups``
    array (or a bare array), and every entry must carry a ``status`` plus the
    ``group_hash``/``group_id`` the merge joins on.
    """
    if isinstance(data, dict):
        groups = data.get("groups")
        if groups is None:
            return ["expected a `groups` array (or a bare array of group results)"]
    elif isinstance(data, list):
        groups = data
    else:
        return [f"expected an object or array, got {type(data).__name__}"]
    if not isinstance(groups, list):
        return [f"`groups` must be an array, got {type(groups).__name__}"]
    errors: List[str] = []
    for index, entry in enumerate(groups):
        if not isinstance(entry, dict):
            errors.append(f"groups[{index}]: expected an object")
            continue
        if not entry.get("status"):
            errors.append(f"groups[{index}]: missing `status`")
        if not (entry.get("group_hash") or entry.get("group_id")):
            errors.append(
                f"groups[{index}]: missing `group_hash`/`group_id` — the merge "
                f"joins by hash, never by position"
            )
    return errors


def _salvage_result_errors(data: Any) -> List[str]:
    """A salvaged model result is the same array shape a model review produces.

    Which is also why the *other* thing a salvage can print — the
    ``{"salvage_failed": true, "reason": ...}`` sentinel — has to fail here. The
    sentinel is not a document any consumer can read; it is this dispatch saying
    it found none. It is recognised **before** validation, by
    :func:`_salvage_gave_up`, and turned into a failed outcome that writes
    nothing. Should one ever reach the disk anyway, keeping it invalid is what
    stops :func:`task_is_complete` from reading the file back and calling the
    task done.

    An empty array stays valid. From here it is indistinguishable from a model
    whose review really was empty, and that ambiguity is precisely why the
    negative was given a shape of its own rather than being refused here.

    The non-array clause below also happens to catch a relayed
    ``{"error": …}`` body or an ``opencode``/``codex`` ``{"type": "error", …}``
    event a salvage subagent "recovered" out of a truncated stream, but that is
    not this function's job and must not be relied on as it: by the time such a
    reply gets here :func:`_salvage_gave_up` has already turned it down with a
    reason that names what actually happened, where "expected a JSON array"
    would have sent the reader back to the repair pass instead of to the
    provider's login. This clause is the floor under that rule, not the rule.
    """
    if not isinstance(data, list):
        return [f"expected a JSON array of suggestions, got {type(data).__name__}"]
    errors = []
    for index, entry in enumerate(data):
        if not isinstance(entry, dict):
            errors.append(f"[{index}]: expected an object")
    return errors


#: The key ``build_salvage_prompt`` tells a salvage subagent to set when the raw
#: output it was handed holds nothing recoverable. A recovered salvage result is
#: an *array*, so no genuine recovery can carry it.
SALVAGE_FAILED_KEY = "salvage_failed"

#: The reason :func:`_salvage_gave_up` gives for an empty array recovered from a
#: run a deadline ended. The request records ``"failure": "timeout"``
#: (``review_orchestrator_base.salvage_failure_kind``); this is its read side.
SALVAGE_EMPTY_AFTER_TIMEOUT_REASON = (
    "salvage recovered an empty array from a run that timed out: a reviewer "
    "killed at its deadline never reported an empty review, so `[]` is not "
    "written as this model's result"
)


def salvage_failure_of(task: Dict[str, Any], phase_dir: str) -> Optional[str]:
    """How the run behind a salvage task was lost, read from its request file.

    A salvage task's ``output_name`` is ``<stem>.json`` and its request is
    ``salvage_<stem>.json`` beside it — the pairing every writer uses and every
    retire glob relies on. The request is the record that says whether a
    deadline ended the run (``"failure": "timeout"``); the task itself carries no
    such field, and its ``inputs.salvage_request_sha256`` already binds it to
    that request's bytes. ``None`` for any other kind, and whenever the request
    cannot be read — which keeps today's behaviour (a salvaged ``[]`` persists).
    """
    if str(task.get("kind", "")) != "salvage":
        return None
    output_name = str(task.get("output_name") or "")
    if not output_name:
        return None
    path = os.path.join(phase_dir, f"salvage_{output_name}")
    try:
        with open(path, encoding="utf-8") as handle:
            request = json.load(handle)
    except (OSError, ValueError):
        return None
    if not isinstance(request, dict):
        return None
    failure = request.get(SALVAGE_FAILURE_KEY)
    return failure if isinstance(failure, str) and failure else None


def _salvage_gave_up(kind: str, data: Any, failure: Optional[str] = None) -> Optional[str]:
    """Why this salvage recovered nothing, or ``None`` if it recovered a result.

    A salvage task's ``output_name`` **is** the model result file it repairs, so
    whatever a salvage dispatch persists *becomes* that model's review. The
    subagent therefore cannot report the negative as an empty array: it would
    validate, be written over the model's own result path, and reaggregation
    would read it as "this model reviewed the input and found nothing". A model
    that never produced a parseable word would join the aggregate as a phantom
    participant — and since finding priority is scored partly by how many models
    flagged something, its silence would count as agreement.

    A salvage arrives here having recovered nothing two ways, read in this order:

    1. **It said so.** ``build_salvage_prompt`` asks for
       ``{"salvage_failed": true, "reason": …}`` and this is the one place that
       shape is read. The reason travels into the outcome because it is the
       diagnostic the empty array threw away — "the raw output was an
       authentication error" is what a reader of ``subagent_batch_report.json``
       needs, and it costs one string to keep. It is checked **first** for
       exactly that: the subagent read the raw output and named what was in it,
       which is a better diagnostic than anything clause 2 can reconstruct from
       the reply alone.
    2. **It did not say so, and what came back is not an answer.** A subagent
       handed a truncated stream that turns out to hold a relayed
       ``{"error": {"code": 401, "message": "User not found"}}`` body, or the
       ``{"type": "error", "message": …}`` envelope an ``opencode``/``codex``
       run prints as an event, can "recover" that object perfectly faithfully
       and never print the sentinel — it believes it found something. Today
       :func:`_salvage_result_errors` stops that object at the door anyway, on
       the narrow ground that it is not an array. What it cannot do is say what
       happened: "does not match the salvage result shape" reads as a botched
       repair pass and invites another one, when what the model actually hit was
       an authentication failure and the fix is the provider's login — the exact
       mis-direction ``has_salvageable_json`` exists to prevent one step
       earlier. So the rule is stated *here*, where the phantom-participant
       argument lives, instead of being left to rest on an array check written
       for the consumer's benefit: were the salvage result shape ever to grow a
       wrapper-object form (the way :func:`_validation_result_errors` tolerates
       ``{"groups": [ … ]}``), an error envelope would sail through that check
       and onto the model's result path with nothing left to stop it. The
       predicate is ``json_extractor.is_answer_shaped``, the one behind
       ``has_salvageable_json``, imported rather than restated: the gate asks
       "is there an answer in this raw output to ask a repair pass for?", this
       asks "is what the repair pass came back with an answer?", and one rule
       spelled once at both ends cannot drift apart from itself.

    Both invokers call this immediately before the point where they would
    validate and persist, and both answer a non-``None`` result the same way:
    ``STATUS_SALVAGE_UNRECOVERABLE``, nothing written, never retried.

    Deliberately **not** folded into :func:`validate_result`: that answers "is
    this a document this kind's consumer can read", and the sentinel must keep
    failing that question for the reason :func:`_salvage_result_errors` gives.

    Scoped to ``kind == "salvage"``; every other kind is judged by its own result
    shape alone. A bare ``[]`` from a salvage still persists — clause 2 lets it
    through because ``is_answer_shaped([])`` is True on purpose: refusing it
    cannot tell "salvage found nothing" from "the model's review was genuinely
    empty", and the sentinel is what carries that distinction. Nor does clause 2
    swallow a *near-miss*: an object naming a field the answer schemas require is
    answer-shaped, so a subagent that returned a single record where an array was
    asked for still falls through to :func:`validate_result` and is reported as
    "does not match the salvage result shape" — the accurate diagnostic for a
    recovery that found an answer and mis-packaged it. Only replies with no
    answer anywhere in them are "recovered nothing".

    The truth test on the sentinel is deliberately loose: a subagent that spelled
    the flag ``"true"`` is still read as the negative, and every reading that
    errs errs towards writing nothing — and clause 2 is the backstop in any case,
    since the sentinel object names no answer field either.

    **The one ``[]`` that is refused** (decision 11.10, timeouts only): when the
    salvage request records ``"failure": "timeout"`` (``failure`` here, read by
    :func:`salvage_failure_of`), an empty array is
    :data:`SALVAGE_EMPTY_AFTER_TIMEOUT_REASON`. A run killed at its deadline
    never said "I found nothing" — a subagent handed only its ``toolcall_delta``
    fragments can return ``[]``, and that would read as a clean review. A ``[]``
    from a run that finished and then exited non-zero still persists: there
    the model did write it.

    Args:
        kind: The task's kind. Anything but ``salvage`` returns ``None``.
        data: The extracted result, before validation.
        failure: The salvage request's ``"failure"`` value, or ``None``.

    Returns:
        The reason for the outcome row, or ``None``.
    """
    if kind != "salvage":
        return None
    if isinstance(data, dict) and data.get(SALVAGE_FAILED_KEY):
        reason = data.get("reason")
        reason = reason.strip() if isinstance(reason, str) else ""
        return (
            f"salvage recovered no result from the raw output: "
            f"{reason or 'the subagent gave no reason'}"
        )
    if failure == SALVAGE_FAILURE_TIMEOUT and isinstance(data, list) and not data:
        return SALVAGE_EMPTY_AFTER_TIMEOUT_REASON
    if is_answer_shaped(data):
        return None
    # Name the shape, never the payload: the keys are what diagnoses this (an
    # `error` or a `type`/`message` pair says "the stream relayed a provider
    # failure" at a glance), while the values are the raw output this dispatch
    # was handed and have no business in a batch report. Bounded, because
    # nothing here promises the object is small.
    if isinstance(data, dict):
        names = sorted(str(key) for key in data)
        listed = ", ".join(names[:5]) + (", …" if len(names) > 5 else "")
        shape = (
            f"an object naming no answer field and holding no array "
            f"({listed or 'no keys at all'}). A relayed provider error or event "
            f"envelope reads as a recovery to the subagent that faithfully "
            f"pulled it out of the stream; it is not this model's review"
        )
    else:
        shape = (
            f"a bare {type(data).__name__} where an array of suggestions was "
            f"the answer; there is nothing in it to write as this model's review"
        )
    return f"salvage recovered no result from the raw output: it returned {shape}"


#: The list-valued keys of a generated task a runner may leave out when the
#: list is empty. ``generated_tasks.schema.json`` requires all three, and a
#: small model reads "no files to create" as "no ``files_to_create`` key" —
#: measured 2026-09-14: ``opencode/nemotron-3-ultra-free`` returned ten
#: well-formed tasks for a single-file plan, every one carrying
#: ``files_to_modify`` and none carrying ``files_to_create``, and the whole
#: reply failed rung 6 (never retried) on that one absent key, twice. An absent
#: list and an empty list mean the same thing to every consumer
#: (``task_decomposer.from_dict`` reads each with a ``[]`` default), so the
#: invoker supplies the key. A key that is *present* with the wrong type is
#: left alone for the schema to name.
TASK_GENERATION_LIST_KEYS: Tuple[str, ...] = (
    "depends_on", "files_to_create", "files_to_modify",
)


def normalize_result(kind: str, data: Any) -> List[str]:
    """Supply what a reply left out that means the same thing absent as empty.

    Mutates ``data`` in place and returns one note per key it supplied, shaped
    ``'files_to_create' on 10 task(s)``; ``[]`` means the reply was already in
    shape. Runs *before* :func:`validate_result` on both parse lanes and on the
    native host's consume path, so the document written to disk is the
    normalized one and :func:`task_is_complete` re-reads what was validated.

    Only ``task_generation`` has such keys. Every other kind returns ``[]``
    with ``data`` untouched: a validation verdict or a write-batch result
    missing a field is a real disagreement, not a spelling of "none".
    """
    if kind != "task_generation":
        return []
    if not isinstance(data, dict) or not isinstance(data.get("tasks"), list):
        return []
    supplied: Dict[str, int] = {}
    for task in data["tasks"]:
        if not isinstance(task, dict):
            continue
        for key in TASK_GENERATION_LIST_KEYS:
            if key not in task:
                task[key] = []
                supplied[key] = supplied.get(key, 0) + 1
        # Required-but-nullable in the schema (OpenAI's strict subset needs every
        # property required) and absent from the prompt's reply shape, so most
        # replies omit it; "no value" is what null says. Counted like the list
        # keys, not supplied silently: the notes are what makes the native leg
        # write the completed document back before validating, and a silent
        # key left a pre-upgrade `task_generation_result.json` schema-invalid
        # on disk — `task_is_complete` False for a file the phase had consumed
        # (adversarial review, 2026-10-02).
        if "subagent_type" not in task:
            task["subagent_type"] = None
            supplied["subagent_type"] = supplied.get("subagent_type", 0) + 1
    return [f"{key!r} on {count} task(s)" for key, count in supplied.items()]


def _report_normalized(
    kind: str, notes: List[str], version: Optional[str] = None,
) -> None:
    """One stdout line per reply the executor had to complete, or nothing;
    one more when it read an absent ``schema_version`` as *version*."""
    if version:
        print(
            f"[exec-subagents] {kind}: "
            + _schema_version_supplied("the reply", version)
            + ", before validating."
        )
    if notes:
        print(
            f"[exec-subagents] {kind}: the reply omitted {', '.join(notes)}; "
            f"supplied the empty value ([] for a list, null for subagent_type) "
            f"before validating (absent and empty mean the same thing to every "
            f"consumer of this document)."
        )


#: The read kinds whose result names a ``schema_version`` its schema pins to
#: one value (fix round 28, live run 12: a host's copy of a task-generation
#: reply left the key out and the first ``--reaggregate`` failed on it). A
#: result without the key is read as that version, on every lane that reads
#: one: the executor's parse, :func:`task_is_complete`, generate-tasks'
#: consume and the judge verdicts' ingest.
VERSIONED_RESULT_SCHEMAS = {
    "task_generation": "generated_tasks.schema.json",
    "human_decision_judge": "human_decision_verdicts.schema.json",
}


def supply_result_version(kind: str, data: Any) -> Optional[str]:
    """Supply a *kind* result's absent ``schema_version`` in place
    (``schema_validator.supply_schema_version``); the version, or ``None``."""
    schema = VERSIONED_RESULT_SCHEMAS.get(kind)
    if schema is None:
        return None
    try:
        from .schema_validator import supply_schema_version
    except ImportError:  # pragma: no cover - direct-script import shim
        from utils.schema_validator import supply_schema_version
    return supply_schema_version(data, schema)


def _schema_version_supplied(subject: str, version: str) -> str:
    try:
        from .schema_validator import schema_version_supplied
    except ImportError:  # pragma: no cover - direct-script import shim
        from utils.schema_validator import schema_version_supplied
    return schema_version_supplied(subject, version)


def validate_result(kind: str, data: Any) -> List[str]:
    """Validate an extracted result against its kind's result shape (D3f).

    Runs *before* anything is written, so a runner that returned prose or the
    wrong object fails the task instead of writing garbage that reaggregation
    accepts. Shipped JSON Schemas are used where they exist; the two kinds with
    no schema get the structural check their consumer actually depends on.

    One kind can also reply with something that is not a document at all:
    ``salvage``'s ``salvage_failed`` sentinel, and the relayed error envelope a
    salvage subagent can "recover" in perfectly good faith. Neither is decided
    here — :func:`_salvage_gave_up` intercepts both a step earlier — and the
    sentinel stays invalid against this function on purpose.
    """
    if kind in ("validation", "revalidation"):
        return _validation_result_errors(data)
    if kind == "consolidation":
        return validate_with_schema_file(data, "consolidation_batch.schema.json")
    if kind == "human_decision_judge":
        return validate_human_decision_verdicts(data)
    if kind == "task_generation":
        # The schema pins the shape; `task_decomposer.validate_generated_tasks`
        # owns the graph rules every later phase depends on (unique T### ids,
        # `depends_on` naming declared ids, acyclic, a dependency-free task).
        # Both are this kind's result shape (fix round 6): a document that only
        # the consumer refused used to be persisted `ok`, get no schema-repair
        # re-ask, and count as done to `task_is_complete` on the next run.
        errors = validate_with_schema_file(data, "generated_tasks.schema.json")
        if errors:
            return errors
        from .task_decomposer import validate_generated_tasks

        return validate_generated_tasks(data.get("tasks") or [])
    if kind == "salvage":
        return _salvage_result_errors(data)
    if kind in WRITE_KINDS:
        # D3g's "the batch still returns JSON on stdout" made concrete: the same
        # schema gate a validation result gets, so a runner that narrated its work
        # in prose fails the task instead of being counted as applied.
        return validate_with_schema_file(data, "write_batch_result.schema.json")
    return [f"unknown kind {kind!r}"]


def task_is_complete(task: Dict[str, Any], phase_dir: str) -> bool:
    """Whether a task counts as already done, deterministically (D3i).

    Done **iff** its ``output_name`` exists under the phase dir, parses, and
    validates against its kind's result schema. Anything else is re-dispatched
    under its original ``task_id``. Orphans are defined by artifacts, never by
    memory: there is no in-memory queue to recover and no "running" state to
    trust.

    A salvage that recovered nothing writes no file at all, so it is not complete
    here — and a ``salvage_failed`` sentinel that reached the disk by some other
    route is not complete either, because it fails :func:`validate_result` the
    way any other non-document would.
    """
    try:
        target = resolve_output_target(task, phase_dir)
    except ResultRejected:
        return False
    if not target.exists() or target.stat().st_size == 0:
        return False
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return False
    # Read as every lane reads it: an absent schema_version is the one
    # version there is (fix round 28), in memory only.
    supply_result_version(str(task.get("kind", "")), data)
    if validate_result(str(task.get("kind", "")), data):
        return False
    return not _result_names_foreign_groups(task, data)


def _result_names_foreign_groups(task: Dict[str, Any], data: Any) -> bool:
    """Whether a batch result echoes a group hash this task was not assigned.

    A task file that lists ``group_ids`` (a validation or revalidation batch)
    says which groups its result may speak about. A file left by an earlier round
    answers a different grouping, so it must not count as done: measured
    2026-10-02 on a Codex ``review-code --force``, a ``validation_batch_0.json``
    from the previous day (judged against an empty repo, hashes of the old
    groups) parsed and schema-validated, was skipped as "already complete", and
    the merge then discarded every row as a foreign ``group_hash`` -- all three
    groups ended ``validation_failed`` and the new code was never validated.
    The same test the merge applies (``merge_batch_validations`` routes by
    ``group_hash``), moved in front of the re-dispatch decision. A result row
    with no hash is not foreign (the merge falls back to its index for those).
    """
    assigned = task.get("group_ids")
    if not isinstance(assigned, list) or not assigned or not isinstance(data, dict):
        return False
    groups = data.get("groups")
    if not isinstance(groups, list):
        return False
    allowed = {str(item) for item in assigned}
    for row in groups:
        if not isinstance(row, dict):
            continue
        echoed = row.get("group_hash") or row.get("group_id")
        if echoed and str(echoed) not in allowed:
            return True
    return False


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

def _tail(text: str, limit: int = MAX_CAPTURE_BYTES) -> str:
    """The last ``limit`` bytes of ``text``, decoded leniently for diagnostics."""
    encoded = (text or "").encode("utf-8", errors="replace")
    if len(encoded) <= limit:
        return text or ""
    return encoded[-limit:].decode("utf-8", errors="replace")


def _redact(text: str) -> str:
    """§4.5's one redaction boundary, imported late.

    ``write_safety`` is imported lazily everywhere in this module (it reaches
    back here through ``subagent_tasks``), and this keeps that convention.

    **Every caller runs this before ``_tail``, never after.** ``_tail`` keeps the
    *last* bytes, so a cut landing inside ``aws_secret_access_key=`` leaves
    ``_access_key=<value>`` — a shape ``SECRET_KEY`` does not match, so no later
    pass could recover it. That ordering is why §4.4 and §4.5 land together.
    """
    try:  # pragma: no cover - import shim mirrors the rest of utils/
        from .write_safety import redact_text
    except ImportError:  # pragma: no cover - direct-script import shim
        from utils.write_safety import redact_text
    return redact_text(text)


def _redact_probe_tail(text: str, limit: int = MAX_CAPTURE_BYTES) -> str:
    """A captured stream, redacted then tailed, for quoting into a refusal.

    Also the wrapper for a tail that leaves this module with no redacting sink
    behind it to name — ``dispatch_task``'s ``after_result`` payload, whose
    consumer is a caller's callback.

    The refusal-message counterpart to
    ``providers.cursor_agent.redact_probe_output``, and the same §4.5 boundary as
    :func:`_redact` — not a second mechanism, a wrapper that fixes the two things
    a refusal needs on top of it.

    **Diagnostic value is the point.** A refusal quotes a probe so the reader can
    see *why* the runner was refused, so this redacts identity- and
    credential-shaped **values** and nothing else: cursor-agent's ``status
    --format json`` is a nine-key object, three of whose keys are §4.5.1 P13
    identity fields, and the other six — plus every key name — survive, so two
    runs stay diffable. Dropping the whole tail would trade one regression for
    another.

    Redaction runs **before** ``_tail`` for the reason :func:`_redact` states: the
    tail keeps the *last* bytes, so a cut landing inside a keyword leaves a value
    no later pass can match.

    **Fail safe.** A redactor that cannot be imported, or that raises, must never
    fall back to the raw stream — the fallback drops the text exactly the way
    M13's probe boundary does.
    """
    try:
        redacted = _redact(text or "")
    except Exception:  # noqa: BLE001 - a diagnostic never leaks on failure
        return "<redacted:probe-output>"
    return _tail(redacted, limit).strip()


def _redact_json(value: Any) -> Any:
    """``value`` with every string in it redacted, structure preserved.

    Used at the two JSON write boundaries. A per-field list would have to be
    kept in step with every new diagnostic field a failure record grows; walking
    the payload cannot fall behind one.
    """
    if isinstance(value, str):
        return _redact(value)
    if isinstance(value, dict):
        return {key: _redact_json(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_redact_json(item) for item in value]
    return value


def _safe_task_filename(task_id: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]", "_", task_id or "task") or "task"


def _retire_capture(target: Path) -> None:
    """Move an earlier invocation's capture aside rather than overwrite it.

    Attempt numbering restarts at 1 on every invocation, and a re-invoked phase
    re-dispatches the failed task under the same id — so without this the retry
    destroyed the evidence of the attempt it was retrying (measured
    2026-09-14: two ``generate-tasks`` runs an hour apart left one
    ``task_generation.attempt1.json``, the second's). The stamp is the retired
    file's own mtime in UTC, so the name says when that attempt ran; the batch
    report that named the old path is rewritten by the same invocation.
    Best-effort: a rename that fails leaves the overwrite as it was.
    """
    try:
        if not target.exists():
            return
        from datetime import datetime, timezone

        stamp = datetime.fromtimestamp(
            target.stat().st_mtime, tz=timezone.utc
        ).strftime("%Y%m%dT%H%M%SZ")
        retired = target.with_name(f"{target.stem}.{stamp}{target.suffix}")
        serial = 1
        while retired.exists():
            retired = target.with_name(
                f"{target.stem}.{stamp}-{serial}{target.suffix}"
            )
            serial += 1
        target.replace(retired)
    except OSError:  # pragma: no cover - diagnostics must never fail a run
        return


def _write_failure_capture(
    *,
    phase_dir: str,
    task: Dict[str, Any],
    attempt_index: int,
    argv: Sequence[str],
    prompt: str,
    stdout: str,
    stderr: str,
    exit_code: Optional[int],
    duration: float,
    status: str,
    error: str,
    repair: Optional[str] = None,
) -> Optional[str]:
    """Persist one failed attempt's bounded capture (D3k). Best-effort.

    A detached or CI failure has no chat context and no stdout to scroll back
    through, so the diagnosis has to survive on disk. The rendered argv carries
    the prompt **elided to its sha256 and byte length** — never the prompt bytes,
    which embed the plan/diff under review.

    Six of the nine planted secret shapes landed here, three times each: the
    existing 64 KiB ``_tail`` preserved every one, which is why §4.4 does not
    subsume §4.5. Redaction runs on the **full** stream before the tail is taken,
    and the assembled payload is walked once more on the way out.
    """
    import hashlib

    try:
        capture_dir = Path(phase_dir) / FAILED_CAPTURE_DIRNAME
        name = f"{_safe_task_filename(str(task.get('task_id', '')))}.attempt{attempt_index}.json"
        digest = hashlib.sha256((prompt or "").encode("utf-8")).hexdigest()
        rendered = [
            f"<prompt sha256:{digest} bytes:{len((prompt or '').encode('utf-8'))}>"
            if arg == prompt
            else arg
            for arg in argv
        ]
        _retire_capture(capture_dir / name)
        _atomic_write_json(str(capture_dir / name), _redact_json({
            "task_id": task.get("task_id"),
            "kind": task.get("kind"),
            "attempt": attempt_index,
            "status": status,
            "rung": RUNG_BY_STATUS.get(status),
            "error": error,
            "exit_code": exit_code,
            "duration_seconds": round(duration, 3),
            "argv": rendered,
            "prompt_sha256": digest,
            "prompt_bytes": len((prompt or "").encode("utf-8")),
            # §4.5 before §4.4: redact the whole stream, then tail it. Tailing
            # first would keep a value whose key name the cut had just removed.
            "stdout_tail": _tail(_redact(stdout)),
            "stderr_tail": _tail(_redact(stderr)),
            # Only on the schema-repair re-ask, so every other capture keeps
            # exactly the keys it always had.
            **({"repair": repair} if repair else {}),
        }))
        return str(capture_dir / name)
    except OSError:  # pragma: no cover - diagnostics must never fail a run
        return None


@dataclass
class _Capture:
    stdout: str = ""
    stderr: str = ""
    exit_code: Optional[int] = None
    duration: float = 0.0
    timed_out: bool = False
    launch_error: Optional[str] = None
    argv: List[str] = field(default_factory=list)
    #: Plan codex-sandbox-unavailable §6 F1 (2026-09-30), set only for an
    #: attempt on a wrapping rung (the plugin's Landlock jail). Paths, classes
    #: and counts only — never output text beyond the ≤300-char excerpt the
    #: ``[JAIL_DENIED]`` line quotes.
    #: The rung id the attempt ran on.
    sandbox_rung: Optional[str] = None
    #: ``JailEvidence.to_dict()`` for a codex-internal EACCES (any class).
    jail_evidence: Optional[Dict[str, Any]] = None
    #: The one ``[JAIL_DENIED]`` line when the attempt failed on the jail
    #: (class ``jail`` or ``probable``, or a grant refused before the spawn):
    #: a non-retryable failure that never moves to another rung.
    jail_denied_line: Optional[str] = None
    #: The stream's denials (``landlock_dispatch.JailDenials``), read from the
    #: FULL stdout before any excerpt is bounded.
    jail_denials: Optional[Any] = None
    #: ``HomeChange.to_dict()`` when ``$CODEX_HOME``'s security-relevant set
    #: changed during the attempt (warn-only in this lane).
    home_change: Optional[Dict[str, Any]] = None
    #: Why the reply's JSON did not parse, as one redacted line, when the
    #: extractor served only a piece of a broken document and that piece failed
    #: validation; set by :func:`_parse_and_validate`, read by the re-ask.
    reply_syntax_error: Optional[str] = None


@dataclass(frozen=True)
class _JailSpawn:
    """What a spawn on a wrapping rung carries from :func:`_spawn` down to
    :func:`_spawn_in_context`: the rung, the lane's request and this attempt's
    scratch directory. An argument, dropped with the attempt — never stored."""

    rung: SandboxRung
    request: JailRequest
    tmpdir: str


class SandboxBackstopViolation(ExecutorError):
    """An ``agent-write`` argv carrying ``danger-full-access`` reached the spawn
    without the jail's wrapper prefix or an F5 consent, or with a grant whose
    write scope the rung does not serve, or an F5 consent whose scope F5 does
    not cover (``repo-wide``; plan steps 3 and 3b's backstop). Raised before
    ``Popen``: a write profile never renders the uncontained value unwrapped,
    whatever a gate above got wrong."""


def _wrapping_rung(provider: Any, profile: str, rung_id: Optional[str]) -> Optional[SandboxRung]:
    """The declared rung ``rung_id`` of ``profile``'s ladder when it wraps the
    CLI (the plugin's Landlock jail), else ``None``."""
    if not rung_id:
        return None
    for rung in _fallback_rungs(provider, profile):
        if rung.name == rung_id and getattr(rung, "wrapper", None):
            return rung
    return None


def _carries_full_access(argv: Sequence[str]) -> bool:
    """Whether ``argv`` renders codex's ``danger-full-access`` value — as the
    ``--sandbox`` value or a ``sandbox_mode`` override, never as prose inside
    a prompt."""
    for item in argv:
        text = str(item)
        if text == HOST_POSTURE_FULL_ACCESS:
            return True
        if text.startswith("sandbox_mode=") and HOST_POSTURE_FULL_ACCESS in text:
            return True
    return False


def _spawn(
    *,
    provider: Any,
    model: str,
    prompt: str,
    profile: str,
    transport: str,
    timeout: float,
    cwd: Optional[str],
    schema: Optional[Any] = None,
    anchor: Optional[str] = None,
    sandbox_fallback: Optional[str] = None,
    read_dirs: Sequence[str] = (),
    jail_request: Optional[JailRequest] = None,
    write_consent: Optional[WritePostureConsent] = None,
) -> _Capture:
    """Run one dispatch, materializing ``schema`` for the CLIs that take a file.

    §4.2.1 puts codex's sidecar in the **caller** — adapters are module-level
    singletons in ``_PROVIDERS`` shared across a concurrent fan-out and cannot
    hold per-run state — and requires the directory to be removed in a
    ``finally`` covering timeout, kill-path teardown and exception alike. That is
    precisely this scope: the ``with`` below opens *before* :func:`_spawn_child`
    renders any argv (codex refuses a schema whose file is unreadable before
    returning argv at all, so nothing partial can reach the CLI) and closes only
    after the child has been spawned, communicated with, and — on a timeout —
    killed with its process group and drained.

    **One sidecar per attempt, not per dispatch.** This lane's retry loop lives
    inside :func:`dispatch_task`, which returns from four points and breaks from
    three more; a dispatch-scoped directory would have to be unwound by
    re-indenting that whole region into a ``try/finally``. Per attempt gets the
    same guarantee from one ``with`` in the one function that spawns, it matches
    Lane A's *observable* lifetime (its ladder re-enters
    ``invoke_with_provider``, which opens and closes a sidecar per call), and it
    re-materializes a file that vanished between two attempts instead of failing
    the retry on it. The cost is one ``mkdtemp`` plus one small write per
    attempt, and only on the adapter whose transport is a file (codex);
    claude's schema is inline and never touches the disk at all.

    ``schema=None`` — every kind with no schema phase, and every adapter that
    declined the flag — skips all of it and renders the argv it always did.

    **The jailed attempt's scratch directory** (plan codex-sandbox-unavailable
    §6 F1 "How a dispatch receives its grant", 2026-09-30). When
    ``sandbox_fallback`` names a wrapping rung, this ``with`` also owns the
    attempt's ``TMPDIR`` (``landlock_dispatch.slot_tmpdir``), beside the schema
    sidecar and for the same reason: made before any rule is applied, removed
    after the child exits — on a clean exit, a timeout's group kill,
    ``KeyboardInterrupt`` and the teardown alike — and fresh on every retry,
    so no attempt inherits another's scratch files. A dispatch on the rung with
    no ``jail_request`` is refused here with nothing made and nothing spawned
    (never rendered with the base entries alone), and a directory that cannot
    be made is a launch error, never a model error.
    """
    wrap = _wrapping_rung(provider, profile, sandbox_fallback)
    common: Dict[str, Any] = {
        "provider": provider, "model": model, "prompt": prompt, "profile": profile,
        "transport": transport, "timeout": timeout, "cwd": cwd, "schema": schema,
        "anchor": anchor, "sandbox_fallback": sandbox_fallback,
        "read_dirs": read_dirs, "write_consent": write_consent,
    }
    if wrap is None:
        return _spawn_with_schema(jail=None, **common)
    if jail_request is None:
        refused = _Capture(sandbox_rung=wrap.name)
        refused.launch_error = (
            f"the plugin's Landlock jail ({wrap.name}) needs this dispatch's "
            f"grant and none was handed to the spawn; nothing was made or "
            f"spawned"
        )
        return refused
    with contextlib.ExitStack() as stack:
        try:
            tmpdir = stack.enter_context(
                landlock_dispatch.slot_tmpdir(jail_request.repo_root)
            )
        except (landlock_dispatch.JailRefused, OSError) as exc:
            refused = _Capture(sandbox_rung=wrap.name)
            refused.launch_error = (
                f"the plugin's Landlock jail could not make this attempt's "
                f"scratch directory: {getattr(exc, 'message', None) or exc}"
            )
            return refused
        return _spawn_with_schema(
            jail=_JailSpawn(rung=wrap, request=jail_request, tmpdir=tmpdir),
            **common,
        )


def _spawn_with_schema(*, jail: Optional[_JailSpawn], **common: Any) -> _Capture:
    """:func:`_spawn`'s sidecar leg: the schema file for a file-transport CLI,
    removed in the same ``with`` that spawned the child. ``jail`` and
    ``write_consent`` reach :func:`_spawn_child` only when set, so a stand-in
    with the historical keyword set is called as it always was."""
    extra: Dict[str, Any] = {}
    if jail is not None:
        extra["jail"] = jail
    consent = common.pop("write_consent", None)
    if consent is not None:
        extra["write_consent"] = consent
    read_dirs = common.pop("read_dirs", ())
    provider = common["provider"]
    schema = common.pop("schema", None)
    if schema is not None and getattr(
        provider, "structured_output_transport", "inline"
    ) == "file":
        with structured_output.schema_sidecar(schema) as materialized:
            return _spawn_child(
                schema=materialized, read_dirs=read_dirs, **common, **extra,
            )
    return _spawn_child(schema=schema, read_dirs=read_dirs, **common, **extra)


def _spawn_child(
    *,
    provider: Any,
    model: str,
    prompt: str,
    profile: str,
    transport: str,
    timeout: float,
    cwd: Optional[str],
    schema: Optional[Any] = None,
    anchor: Optional[str] = None,
    sandbox_fallback: Optional[str] = None,
    read_dirs: Sequence[str] = (),
    jail: Optional[_JailSpawn] = None,
    write_consent: Optional[WritePostureConsent] = None,
) -> _Capture:
    """Run one dispatch: build argv for the profile, spawn, capture everything.

    ``cwd`` is passed explicitly (never inherited) so the runner's sandbox root is
    the intended repository and a task cannot be steered into ``$HOME`` or a
    sibling checkout (D3e). Env composition is the adapter's
    ``get_env``/``get_remove_env`` pair — the same single site the fan-out path and
    the detached child use, so there is never a second hand-rolled env filter.

    ``anchor`` is the dispatch's plan anchor, threaded from the batch exactly as
    Lane A threads it into ``resolve_env``/``build_child_env`` — it is what makes
    config discovery resolve against the **plan's** git root rather than the
    process CWD's. Dropping it here is not cosmetic: an ``env_allowlist``,
    ``git_env`` or hermetic setting written into a plan-anchored
    ``.multi-llm/providers.yaml`` would govern Lane A slots and silently skip Lane
    B dispatches whenever the two roots differ, which is the one divergence
    M3/M17 (A6) exist to close.

    ``schema`` is §4.2.2's optional keyword, already materialized by
    :func:`_spawn` when this adapter's transport is a file. An adapter that
    declares no ``structured_output_support`` ignores it and renders the same
    argv either way; one that cannot carry it raises before any argv exists.

    M4/§2.3: the adapter's run-scoped dispatch context wraps argv *and* env,
    because an adapter that contains its own config layering renders a flag and
    an env redirect that only mean anything together (opencode's ``--pure`` and
    its ``XDG_CONFIG_HOME``). The ``with`` is the ``finally`` half of that
    lifecycle — it is left on a clean return, on a per-slot timeout, on
    ``KeyboardInterrupt`` and on the §8 process-group teardown alike.

    ``jail`` (a wrapping rung's attempt) and ``write_consent`` (F5) are
    handed on to :func:`_spawn_in_context` only when set.
    """
    extra: Dict[str, Any] = {}
    if jail is not None:
        extra["jail"] = jail
    if write_consent is not None:
        extra["write_consent"] = write_consent
    with provider_dispatch_context(
        provider, model, profile, anchor=anchor,
        runner_version=_preflight_version(provider),
    ) as dispatch:
        if dispatch.refusal:
            # Nothing has been spawned and nothing has been claimed. The refusal
            # rides the same `launch_error` channel a failed `Popen` uses, so it
            # lands on the ladder's spawn rung rather than inventing a state.
            refused = _Capture()
            refused.launch_error = dispatch.refusal
            return refused
        return _spawn_in_context(
            provider=provider, model=model, prompt=prompt, profile=profile,
            transport=transport, timeout=timeout, cwd=cwd, schema=schema,
            anchor=anchor, sandbox_fallback=sandbox_fallback,
            read_dirs=read_dirs, **extra,
        )


def _codex_versions_text(provider_name: str, rung: SandboxRung) -> Tuple[str, bool]:
    """``("codex X installed, jail measured through Y", newer)``."""
    measured = (getattr(rung, "measured_through", None) or ("",))[0] or "unknown"
    installed = (
        _VERSION_CACHE.get(provider_name) or _PROBE_VERSION_CACHE.get(provider_name)
        or "unknown"
    )
    newer = _newer_than(installed, measured)
    text = (
        f"{provider_name} {installed} installed, the jail measured through "
        f"{measured}"
    )
    if newer:
        text += (
            "; Codex is newer than the jail was measured with, the likely cause"
        )
    return text, newer


def _render_home_text(text: str) -> str:
    """``text`` with every ``$HOME`` prefix shown as ``~`` (paste-ready)."""
    home = os.path.expanduser("~")
    if not home or home in ("~", os.sep):
        return text
    return text.replace(home + os.sep, "~" + os.sep).replace(home + "'", "~'")


def jail_denied_line(
    *,
    spec: str,
    rung: SandboxRung,
    path: Optional[str],
    excerpt: str,
    allow_list: str,
    profile: Optional[str] = None,
    write_scope: Optional[str] = None,
) -> str:
    """The one ``[JAIL_DENIED]`` line for a dispatch the plugin's jail failed
    (plan codex-sandbox-unavailable §6 F1 item 6, 2026-09-30).

    It names the runner and spec, the rung, the denied path (or "path not
    named"), the ≤300-char excerpt, the allow-list, the installed and
    measured-through Codex versions — adding "Codex is newer than the jail was
    measured with, the likely cause" when it is — and the next steps. ``$HOME``
    renders as ``~``, so the line can be pasted into an issue as it is.

    The skip step is worded per lane (``profile``/``write_scope``): for a read
    dispatch, skipping the rung runs the job on the next rung for one run; for
    an ``agent-write`` dispatch the jail is the only write rung, so skipping it
    is a refusal unless F5's consent (the chat's own ``danger-full-access``
    posture, under ``sandbox_fallback=auto``) is present — the line says so
    rather than advising a switch that does not run the job.
    """
    provider_name = spec.split(":", 1)[0]
    versions, _newer = _codex_versions_text(provider_name, rung)
    where = (
        landlock_dispatch.render_home(path) if path
        else "path not named (Codex did not name the path; a probable jail denial)"
    )
    shown = _render_home_text(" ".join((excerpt or "").split())[:300])
    if profile in SANDBOX_WRITE_FALLBACK_PROFILES:
        skip = (
            f"to run the job anyway, set `driver.subagent_runner` to a runner "
            f"that is not Codex (F6). Setting {SKIP_RUNG_ENV}={rung.name} does "
            f"not run it: this is a write dispatch (scope "
            f"{write_scope or 'none'}) and {rung.name!r} is its only write "
            f"rung, so with it skipped the write is refused unless the chat "
            f"itself runs in {HOST_POSTURE_FULL_ACCESS} "
            f"({HOST_SANDBOX_POSTURE_ENV}; F5, under "
            f"sandbox_fallback={SANDBOX_FALLBACK_AUTO}), which then runs it with "
            f"no OS boundary."
        )
    else:
        skip = (
            f"to run the job anyway, set `driver.subagent_runner` to a runner "
            f"that is not Codex (F6), or else set {SKIP_RUNG_ENV}={rung.name} "
            f"for one run."
        )
    return (
        f"{JAIL_DENIED_MARKER} {spec} on rung {rung.name!r}: denied {where}; "
        f"excerpt: {shown!r}; allow-list: {allow_list or '(not computed)'}; "
        f"{versions}. This is a jail failure, not a model error, and is not "
        f"retried on another rung. Next: compare with `multi_llm.py doctor`'s "
        f"`{rung.name}` row; report it at "
        f"github.com/beastlabai/multi-llm-plugin/issues with this line and that "
        f"row; {skip}"
    )


def _home_check_line(spec: str, rung: SandboxRung, change: Any, others: int) -> str:
    """The warn-only ``[CODEX_HOME_CHECK]`` line of the executor lane: the
    changed files and, for ``config.toml``, the changed key names — never a
    value — and how many other codex children of this run were live."""
    return (
        f"{CODEX_HOME_CHECK_MARKER} {spec} on rung {rung.name!r}: $CODEX_HOME "
        f"changed during this dispatch: {change.describe()}; {others} other "
        f"codex child(ren) of this run were live in the window, so any of them "
        f"may have made it. Review the file(s): the plugin does not revert "
        f"them. Warn-only in the executor lane: this dispatch's verdict is "
        f"unchanged."
    )


def _spawn_in_context(
    *,
    provider: Any,
    model: str,
    prompt: str,
    profile: str,
    transport: str,
    timeout: float,
    cwd: Optional[str],
    schema: Optional[Any] = None,
    anchor: Optional[str] = None,
    sandbox_fallback: Optional[str] = None,
    read_dirs: Sequence[str] = (),
    jail: Optional[_JailSpawn] = None,
    write_consent: Optional[WritePostureConsent] = None,
) -> _Capture:
    """:func:`_spawn_child`'s body, inside the adapter's dispatch context.

    ``sandbox_fallback`` is the D6 override (2026-09-17): the rung id
    :func:`dispatch_task` read off the preflight's cache for this runner and
    profile (:func:`sandbox_rung`), or ``None``; the adapter's
    ``apply_sandbox_fallback`` is what turns that rung into argv, and every
    adapter without one ignores it.

    **On the plugin's Landlock jail** (``jail`` set; plan codex-sandbox-
    unavailable §6 F1 "How a dispatch receives its grant", 2026-09-30), in this
    order: render the codex argv with ``JailContext(request, tmpdir)`` (the
    ``--sandbox`` slot and ``-c developer_instructions=…``); resolve the
    executable; compose the child env as today; complete the context with the
    ``$CODEX_HOME`` that env names (a missing or in-repo home refuses here —
    reported as a jail failure naming the path, nothing spawned); add the
    wrapper prefix through ``landlock_dispatch.wrap_argv``, the only site that
    does; snapshot the home, spawn in a new process group (the wrapper
    ``exec``s codex, so the PID and the group are codex's own and a timeout's
    group kill reaches it and everything it started), and snapshot again.
    While the context is alive the parent reads the outcome: a codex-internal
    EACCES (``is_jail_failure``), the stream's denials (``jail_denied_edits``,
    on the full stdout) and the home comparison. Only paths, classes and
    counts travel back, on the capture.

    **Backstop** (plan steps 3 and 3b): an ``agent-write`` argv carrying
    ``danger-full-access`` that is neither wrapped nor backed by an F5 consent
    — or whose jail grant names a write scope outside
    :data:`WRITE_SCOPES_ON_RUNG`, or whose consent names one outside
    :data:`WRITE_SCOPES_BY_CONSENT` — raises :class:`SandboxBackstopViolation`
    before ``Popen``.
    """
    capture = _Capture()
    render: Dict[str, Any] = {}
    if jail is not None:
        render["jail_context"] = JailContext(request=jail.request, tmpdir=jail.tmpdir)
        capture.sandbox_rung = jail.rung.name
    if write_consent is not None:
        render["write_consent"] = write_consent
    argv, stdin_text = provider.build_agent_command_for_transport(
        prompt, model, profile, transport, schema=schema,
        sandbox_fallback=sandbox_fallback, **render,
    )
    if read_dirs:
        # The adapter's own read-scope flag (claude-code `--add-dir`), for the
        # directories of path-named context snapshots outside cwd only.
        argv = provider.widen_read_scope(list(argv), read_dirs)
    # The batch-shim flag is consumed pre-dispatch by `_prompt_over_budget`, which
    # resolves argv[0] the same way: it applies cmd.exe's 8,191-unit cap and
    # refuses a metacharacter-bearing prompt (rung 7, nothing spawned) before this
    # runs, so by here the prompt is already known to be safe for this launcher.
    launcher, _is_batch_shim = _resolve_executable(argv[0])
    argv = [*launcher, *argv[1:]]
    capture.argv = list(argv)

    # `resolve_env`, not `get_env`: the dispatch's own profile is what scopes the
    # §2.2 git block. `agent-readonly` gets the global non-interactive keys AND
    # `credential.helper=""` (a hanging helper fails in ~0.27 s instead of burning
    # the slot and orphaning a child); `agent-write` gets the global keys ONLY and
    # keeps whatever helper the user configured, because it is the profile that
    # legitimately reaches private remotes. Passing a constant here would erase
    # that distinction.
    # `cwd` is passed for the same reason it is passed to `Popen` below: this
    # dispatch runs in an explicit directory, and an adapter whose delta carries
    # a workspace-scoped side effect (cursor's trust-marker guard) must scope it
    # to *that* directory rather than to the orchestrator's.
    # M3/M17 (A6): the union of the adapter's list and the host's guards, minus
    # the host's `passthrough`, is computed inside `build_child_env` — the one
    # builder Lane A goes through too. Before it existed the two lanes composed
    # the child env differently, which is what let `passthrough` cancel §2.1's
    # credential strip on this lane alone. The host entry still declares what
    # *this* host injects into every child; what it may no longer do is sanction
    # a vendor credential back into a runner the adapter just stripped it from.
    # Both calls live in `dispatch_child_env` (plan §8 T8.13), which the auth
    # preflight shares, so the probe and the dispatch cannot compose it apart.
    env = dispatch_child_env(provider, model, profile, anchor=anchor, cwd=cwd)

    spec = f"{getattr(provider, 'name', 'runner')}:{model}"
    context: Optional[JailContext] = None
    if jail is not None:
        composed = dict(os.environ) if env is None else dict(env)
        try:
            context = landlock_dispatch.complete_context(jail.request, jail.tmpdir, composed)
            argv, env = landlock_dispatch.wrap_argv(argv, jail.rung, context, composed)
        except landlock_dispatch.JailRefused as exc:
            # Between the probe and this dispatch a required entry vanished (or
            # the home is unusable): a jail failure naming the path, never a
            # model error, never retried on another rung, nothing spawned.
            capture.launch_error = exc.message
            capture.jail_evidence = {
                "where": "setup", "line": exc.message[:300], "path": exc.path,
                "class": landlock_dispatch.JAIL_CLASS_JAIL, "reason": exc.reason,
            }
            capture.jail_denied_line = jail_denied_line(
                spec=spec, rung=jail.rung, path=exc.path, excerpt=exc.message,
                allow_list="", profile=profile,
                write_scope=jail.request.write_scope,
            )
            return capture
        capture.argv = list(argv)
    if profile == PROFILE_AGENT_WRITE and _carries_full_access(argv):
        wrapped = landlock_dispatch.is_wrapped(argv)
        if not wrapped and write_consent is None:
            raise SandboxBackstopViolation(
                f"Refusing to spawn {spec}: an agent-write argv carries "
                f"{HOST_POSTURE_FULL_ACCESS} without the plugin's Landlock wrapper "
                f"prefix or the chat's F5 consent. A write profile never runs "
                f"uncontained unwrapped. Nothing was spawned."
            )
        # The grant's scope, not only its presence: the jail serves the
        # scopes in WRITE_SCOPES_ON_RUNG and F5 the narrower
        # WRITE_SCOPES_BY_CONSENT, so an unscoped write — or a repo-wide one
        # by consent — is refused here even if a gate upstream let it through.
        if wrapped:
            grant = "the plugin's Landlock jail"
            scope = getattr(getattr(jail, "request", None), "write_scope", None)
            served = WRITE_SCOPES_ON_RUNG
        else:
            grant = "the chat's F5 consent"
            scope = getattr(write_consent, "write_scope", None)
            served = WRITE_SCOPES_BY_CONSENT
        if scope not in served:
            raise SandboxBackstopViolation(
                f"Refusing to spawn {spec}: an agent-write argv carries "
                f"{HOST_POSTURE_FULL_ACCESS} under {grant} for write scope "
                f"{scope!r}, which it does not serve (served: "
                f"{', '.join(served)}; repo-wide edits run on the jail "
                f"alone). Nothing was spawned."
            )

    home_before = None
    run_cwds = [os.path.realpath(cwd or os.getcwd())]
    if context is not None:
        home_before = landlock_dispatch.home_snapshot(context.codex_home, run_cwds)

    start = time.time()
    # `Popen`, not `subprocess.run`: the timeout has to kill the child *with its
    # process group* (D3k rung 2), and `run` neither hands out the pid nor kills
    # anything but the direct child. An agentic runner is not a leaf — its tool
    # children (a shell, a nested provider CLI) inherit both the group and this
    # stdout pipe — so `run`'s leader-only kill leaves them running against a
    # task nobody is reading, and its own post-kill drain is unbounded on
    # Windows: a timed-out task wedges the whole batch instead of failing on
    # rung 2. On the jail the leader is the wrapper, which `exec`s codex: the
    # PID and the group recorded here are codex's own. Windows has no groups:
    # there the child starts in a Job Object of its own, and the job is what
    # the timeout kills (`process_control.popen_tree`).
    try:
        proc, job = process_control.popen_tree(
            argv,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE if stdin_text is not None else subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
            cwd=cwd,
            **process_control.new_process_group_kwargs(),
        )
    except OSError as exc:
        capture.duration = time.time() - start
        capture.launch_error = str(exc)
        return capture

    if context is not None:
        with _JAIL_SUMMARY_LOCK:
            live_before = _JAILED_CHILDREN["live"]
            started_before = _JAILED_CHILDREN["started"]
            _JAILED_CHILDREN["live"] += 1
            _JAILED_CHILDREN["started"] += 1
    try:
        # Read the group now, while the child is alive: `os.getpgid` stops
        # answering the moment the leader is reaped, and the group — the thing
        # that still holds the tool children — outlives it. `None` on Windows,
        # where the job stands in for it.
        pgid = process_control.process_group_id(proc.pid)
        try:
            stdout, stderr = proc.communicate(input=stdin_text, timeout=timeout)
            capture.duration = time.time() - start
            capture.stdout = _decode(stdout)
            capture.stderr = _decode(stderr)
            capture.exit_code = proc.returncode
        except subprocess.TimeoutExpired as exc:
            _kill_timed_out(proc, pgid, job)
            stdout, stderr = _drain_after_kill(proc, exc)
            capture.duration = time.time() - start
            capture.timed_out = True
            capture.stdout = stdout
            capture.stderr = stderr
        except OSError as exc:
            _kill_timed_out(proc, pgid, job)
            _drain_after_kill(proc, None)
            capture.duration = time.time() - start
            capture.launch_error = str(exc)
            return capture
        except BaseException:
            # The foreground SIGTERM handler's `SystemExit` (or a Ctrl-C) landing
            # in the wait: the child runs in a group of its own, so nothing else
            # reaches it. Stop and reap the group *before* unwinding — the
            # callers' cleanup removes the jail's TMPDIR and restores the trust
            # state, which a still-running codex could otherwise write the plan
            # into or rewrite behind it. Then re-raise, so the signal still ends
            # the run; a teardown failure never masks it.
            _kill_timed_out(proc, pgid, job)
            try:
                _drain_after_kill(proc, None)
            except Exception:  # noqa: BLE001 - the interrupt is what propagates
                pass
            raise
    finally:
        if job is not None:
            job.close()
        if context is not None:
            with _JAIL_SUMMARY_LOCK:
                _JAILED_CHILDREN["live"] -= 1
                others = live_before + (
                    _JAILED_CHILDREN["started"] - started_before - 1
                )
    if context is not None and jail is not None:
        _read_jailed_outcome(
            capture, jail=jail, context=context, spec=spec, cwd=cwd,
            home_before=home_before, run_cwds=run_cwds, others=others,
            profile=profile,
        )
    return capture


def _read_jailed_outcome(
    capture: _Capture,
    *,
    jail: _JailSpawn,
    context: JailContext,
    spec: str,
    cwd: Optional[str],
    home_before: Any,
    run_cwds: Sequence[str],
    others: int,
    profile: Optional[str] = None,
) -> None:
    """After a jailed child exits, while its context is alive: the jail
    failure, the stream's denials and the home check (plan F1 item 6,
    Limits). Only paths, classes and counts are kept on ``capture``.

    The exit code goes in too: the wrapper's own refusal at dispatch (exit
    125/126 with its ``landlock_exec:`` note — a required entry gone or a
    symlink since the probe, or Landlock failing after a good ABI query) is
    a jail failure, and the ``[JAIL_DENIED]`` line it sets rejects the
    attempt before any output is parsed — never retried, as on the fan-out
    lane."""
    evidence = landlock_dispatch.is_jail_failure(
        capture.stderr, capture.stdout, context, returncode=capture.exit_code,
    )
    if evidence is not None:
        capture.jail_evidence = evidence.to_dict()
        failed_turn = evidence.where == "event" or capture.exit_code not in (0, None)
        if (
            failed_turn
            and not capture.timed_out
            and evidence.klass in (
                landlock_dispatch.JAIL_CLASS_JAIL, landlock_dispatch.JAIL_CLASS_PROBABLE,
            )
        ):
            try:
                allow = landlock_dispatch.render_allow_list(
                    landlock_dispatch.allow_entries(context)
                )
            except landlock_dispatch.JailRefused:
                allow = ""
            capture.jail_denied_line = jail_denied_line(
                spec=spec, rung=jail.rung, path=evidence.path, excerpt=evidence.line,
                allow_list=allow, profile=profile,
                write_scope=jail.request.write_scope,
            )
    capture.jail_denials = landlock_dispatch.jail_denied_edits(
        capture.stdout, context, cwd=cwd,
    )
    home_after = landlock_dispatch.home_snapshot(context.codex_home, run_cwds)
    change = landlock_dispatch.compare_home(home_before, home_after)
    if change is not None:
        if change.any:
            capture.home_change = change.to_dict()
            _record_jail_line(_home_check_line(spec, jail.rung, change, others))
        if change.foreign_trust:
            # Trust tables for directories other than this run's cwds (I12):
            # this run's batch or a concurrent codex session added them. Named
            # in the closing summary only, never a warning per dispatch, and
            # only those still in the config when it prints (fix round 17).
            _record_jail_line(
                landlock_dispatch.TrustEntriesNote(
                    home=context.codex_home,
                    paths=tuple(change.foreign_trust),
                ),
                echo=False,
            )


def _kill_timed_out(
    proc: Any, pgid: Optional[int], job: Optional["process_control.TreeJob"] = None,
) -> None:
    """SIGTERM → SIGKILL the child *and its group*, through the one facade.

    ``start_time=None`` is how an unverified kill is *requested* (see
    ``process_control.kill_tree``): this pid is not a record read off disk, it is
    a child this process is still holding open, so there is nothing to
    corroborate and nothing to recycle. The verdict is advisory — the child is
    an unreaped zombie until :func:`_drain_after_kill` collects it, so the probe
    that decides it cannot see the difference; what matters is that the signals
    reached the group. *job* is the child's Windows Job Object, the group's
    stand-in there (``None`` elsewhere).
    """
    try:
        process_control.kill_tree(
            proc.pid,
            start_time=None,
            pgid=pgid,
            escalate_after_s=TIMEOUT_KILL_GRACE_S,
            poll_interval_s=0.05,
            job=job,
        )
    except Exception:  # noqa: BLE001 - teardown must never mask the timeout
        if job is not None and job.terminate():
            return
        try:
            proc.kill()
        except OSError:
            pass


def _drain_after_kill(
    proc: Any, exc: Optional[subprocess.TimeoutExpired]
) -> Tuple[str, str]:
    """Collect the killed child's output and reap it, without ever hanging.

    A second ``communicate()`` returns everything buffered, including what the
    first one had already read before it timed out. If even *that* blocks, a
    grandchild the kill did not reach is still holding the pipe: fall back to the
    partial capture the ``TimeoutExpired`` carries and let the descriptors go,
    because a diagnostic tail is never worth wedging the batch for.
    """
    try:
        stdout, stderr = proc.communicate(timeout=TIMEOUT_DRAIN_S)
        return _decode(stdout), _decode(stderr)
    except (subprocess.TimeoutExpired, OSError, ValueError):
        if process_control.IS_WINDOWS:
            # communicate's reader threads can still hold the streams' locks.
            # close() waits for those reads, defeating TIMEOUT_DRAIN_S even
            # after the tree kill was attempted. Let the readers release the
            # pipes when the remaining writer exits, as the probe does. With
            # the child's Job Object terminated no writer is left; only a
            # child that got no job (`popen_tree`) can still have one.
            return (
                _decode(getattr(exc, "stdout", None)),
                _decode(getattr(exc, "stderr", None)),
            )
        for stream in (proc.stdin, proc.stdout, proc.stderr):
            try:
                if stream is not None:
                    stream.close()
            except (OSError, ValueError):  # pragma: no cover - best effort
                pass
        return (
            _decode(getattr(exc, "stdout", None)),
            _decode(getattr(exc, "stderr", None)),
        )


def _decode(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return value.decode("utf-8", errors="replace")


def _context_read_dirs(task: Dict[str, Any], cwd: Optional[str]) -> List[str]:
    """Directories of a task's ``mode: path`` context snapshots outside ``cwd``."""
    root = os.path.realpath(cwd or os.getcwd())
    dirs: List[str] = []
    for record in task.get("context_sources") or []:
        if not isinstance(record, dict) or record.get("mode") != "path":
            continue
        path = record.get("abs_path")
        if not path:
            continue
        directory = os.path.dirname(os.path.realpath(str(path)))
        if directory == root or directory.startswith(root.rstrip(os.sep) + os.sep):
            continue
        if directory not in dirs:
            dirs.append(directory)
    return dirs


def _missing_write_grant(
    request: Optional[JailRequest], *, kind: str, scope: str
) -> Optional[str]:
    """Why ``request`` is not a complete grant for a ``kind`` write dispatch on
    the plugin's jail, or ``None`` (plan F1 "A missing grant is refused, never
    narrowed or widened")."""
    if request is None:
        return "no grant was handed to the dispatch"
    if request.kind != kind:
        return f"its grant names kind {request.kind!r}, not the task's {kind!r}"
    if request.write_scope != scope:
        return (
            f"its grant's write scope is {request.write_scope!r}, not "
            f"{scope!r} (the scope of kind {kind!r})"
        )
    if scope == WRITE_SCOPE_REPO_WIDE:
        # The grant is one dir rule on the repository root (step 3b, revised
        # 2026-10-05): no single target, but the root and the run's output
        # folder, which the developer message names as hands-off.
        if not request.repo_root:
            return "its repo-wide grant names no repository root"
        if not request.output_dir:
            return "its repo-wide grant names no output folder for the developer message"
        return None
    if not request.target:
        return f"its {scope} grant names no target"
    return None


def _dispatch_grant(
    task: Dict[str, Any],
    *,
    kind: str,
    profile: str,
    runner: str,
    cwd: Optional[str],
    provider: Any,
    jail_request: Optional[JailRequest],
) -> Tuple[Optional[str], Optional[JailRequest], Optional[str]]:
    """``(refusal, request, rung id)`` for one dispatch (plan
    codex-sandbox-unavailable §6 F1 "How a dispatch receives its grant",
    2026-09-30).

    The rung is the preflight's decision, replayed: for a write kind, the one
    taken for the kind's own write scope (:data:`WRITE_SCOPE_BY_KIND`, never
    the task JSON). A read kind gets a request built from ``cwd`` when it has
    none, and is refused if handed one that carries a scope or a target. A
    write kind on the jail is refused unless its request is complete for the
    task. An unmapped write kind is refused outright. Every refusal is rung 7
    with nothing spawned.
    """
    task_id = str(task.get("task_id", ""))
    if kind in WRITE_KINDS:
        scope = WRITE_SCOPE_BY_KIND.get(kind)
        if scope is None:
            return (
                f"Task {task_id}: write kind {kind!r} has no write scope "
                f"(WRITE_SCOPE_BY_KIND), so it is refused rather than given a "
                f"wider grant. Nothing was dispatched."
            ), jail_request, None
        fallback = sandbox_rung(runner, profile, write_scope=scope)
        wrap = _wrapping_rung(provider, profile, fallback)
        if wrap is not None:
            missing = _missing_write_grant(jail_request, kind=kind, scope=scope)
            if missing is not None:
                return (
                    f"Task {task_id}: the plugin's Landlock jail ({wrap.name}) "
                    f"needs this write dispatch's grant, and {missing}; a "
                    f"missing grant is refused, never narrowed or widened. "
                    f"Nothing was dispatched."
                ), jail_request, fallback
        return None, jail_request, fallback
    if jail_request is not None and (
        jail_request.write_scope or jail_request.target or jail_request.target_dir
    ):
        return (
            f"Task {task_id}: this read-only {kind} dispatch was handed a write "
            f"grant (scope {jail_request.write_scope!r}); a read kind never "
            f"carries one. Nothing was dispatched."
        ), jail_request, None
    if jail_request is None:
        jail_request = JailRequest(
            repo_root=os.path.realpath(cwd or os.getcwd()), kind=kind,
        )
    return None, jail_request, sandbox_rung(runner, profile)


def _jail_hook_context(
    capture: Any, request: Optional[JailRequest], fallback: Optional[str],
) -> Dict[str, Any]:
    """The keys ``after_result`` and ``changed_files`` gain (plan step 3):
    the rung the attempt ran on, the stream's denials for a write dispatch on
    the jail (``landlock_dispatch.JailDenials``; ``None`` otherwise), and the
    jail evidence (a dict, or ``None``). Paths, kinds and counts only."""
    denials = getattr(capture, "jail_denials", None)
    on_jail = getattr(capture, "sandbox_rung", None) is not None
    return {
        "sandbox_rung": fallback,
        "jail_denials": (
            denials if on_jail and request is not None and request.write_scope
            else None
        ),
        "jail_evidence": getattr(capture, "jail_evidence", None),
    }


def _report_jail_outcome(task_id: str, capture: Any) -> None:
    """Print what the parent read off a jailed attempt (plan F1 item 6): the
    ``[JAIL_DENIED]`` line (kept for the closing summary), and — on every
    dispatch on the rung — the count and first three paths of the command
    writes the jail stopped, which fail nothing."""
    line = getattr(capture, "jail_denied_line", None)
    if line:
        _record_jail_line(line)
    denials = getattr(capture, "jail_denials", None)
    if denials is None:
        return
    stray = getattr(denials, "out_of_scope_count", 0) or 0
    failed = len(getattr(denials, "failed_file_changes", ()) or ())
    if not stray and not failed:
        return
    shown = ", ".join(
        landlock_dispatch.render_home(p)
        for p in (getattr(denials, "out_of_scope_paths", ()) or ())[:3]
    )
    parts = []
    if stray:
        parts.append(
            f"{stray} command write(s) outside the grant denied"
            + (f" ({shown})" if shown else "")
        )
    if failed:
        parts.append(f"{failed} failed file_change item(s)")
    print(
        f"[exec-subagents] {task_id}: the plugin's Landlock jail stopped "
        f"{'; '.join(parts)} — stray writes stopped by the jail"
    )


def dispatch_task(
    task: Dict[str, Any],
    *,
    phase_dir: str,
    runner: str,
    anchor: Optional[str] = None,
    cwd: Optional[str] = None,
    retries: Optional[int] = None,
    timeout: Optional[int] = None,
    sleep: Optional[Callable[[float], None]] = None,
    prompt: Optional[str] = None,
    before_attempt: Optional[Callable[[Dict[str, Any]], None]] = None,
    after_result: Optional[Callable[[Dict[str, Any]], None]] = None,
    after_attempt: Optional[Callable[[Attempt], None]] = None,
    changed_files: Optional[Callable[[Dict[str, Any]], Sequence[str]]] = None,
    jail_request: Optional[JailRequest] = None,
    tree_fingerprint: Optional[Callable[[Dict[str, Any]], Any]] = None,
    nothing_changed: Optional[Callable[[Dict[str, Any]], Optional[str]]] = None,
    incomplete_report: Optional[Callable[[Dict[str, Any]], Optional[str]]] = None,
    restate_findings: Optional[
        Callable[[Dict[str, Any]], Optional[Tuple[str, Sequence[str]]]]
    ] = None,
) -> TaskOutcome:
    """Dispatch one task and return its :class:`TaskOutcome` (D3k classified).

    Synchronous by design: the concurrency lives in
    ``review_orchestrator_base.run_tasks_concurrent``, which runs this in a
    thread, so one dispatch is a straight line that is readable and unit-testable
    on its own.

    Retries are bounded and only for transport-shaped failures — a timeout, a run
    yielding no parsed text, or a ``parse_output`` failure. A result that parsed
    but failed schema validation is **never** retried: that is a deterministic
    disagreement a retry would only launder. A retried task keeps its ``task_id``,
    so the task-keyed result map and reaggregation are unaffected.

    ``timeout`` (or ``driver.subagent_timeout_s``) is the task's **total**
    wall-clock budget, not a per-attempt one: a monotonic deadline is fixed at
    entry, every attempt is spawned with what is left of it, backoff sleeps are
    spent from it, and a retry is refused once no usable slice remains. So a
    dispatch is bounded by the configured ceiling however many times it retries.

    §4.2.2's structured-output leg is read **here, before dispatch**, and it is
    the second of M7's two phase callers (``llm_client.invoke_with_provider`` is
    the first). The phase comes from the task's *kind*
    (:data:`SCHEMA_PHASE_BY_KIND`), the schema file is loaded once per dispatch,
    codex's sidecar is written per attempt inside :func:`_spawn`'s ``finally``,
    and §4.2.1's verdict lands on this lane's own rungs (see
    :func:`_parse_with_schema_policy`) plus ``TaskOutcome.structured_output``. A
    kind with no schema phase — every kind but ``task_generation`` and
    ``consolidation`` — takes none of it and renders the argv it always did.

    Args:
        prompt: The prompt to dispatch, overriding ``task["prompt"]``. This is the
            D3n seam: an apply prompt is complete except for
            ``{prior_changes_context}``, whose value is a function of the batches
            that already finished, so the scheduler substitutes it and hands the
            *dispatched* prompt in here. The task JSON stays the immutable
            hash-bound snapshot D2g made it — this never rewrites it.
        before_attempt: Called once per attempt, immediately **before** the spawn,
            with ``{task, profile, runner, cwd, attempt, argv, prompt}``. The write
            path's pre-batch snapshot, its pre-dispatch write-policy check and its
            ``dispatched`` audit line hang here. Raising :class:`ResultRejected`
            refuses the task with nothing spawned (D3l).
        after_result: Called **after** rung-6 validation passed and the result was
            persisted, with ``{task, outcome, result, capture, ...}``. This is the
            D3g seam: the snapshot/diff classification, the post-run policy
            recomputation and the ``completed`` audit line. It mutates
            ``outcome`` (``write_outcome``, ``files_touched``, ``summary``,
            ``status``) — the model's claim is never the verdict.
        after_attempt: Called with each :class:`Attempt` the moment it is
            recorded — before ``after_result``, ``ladder.record`` and any backoff
            sleep — so a caller can react to one attempt while the task is still
            retrying (§5: rate-limit backpressure narrows on the attempt, not on
            the finished task). It runs on the dispatching thread. It is an
            observer: an exception it raises is reported on stderr and
            swallowed, never allowed to fail the attempt.
        changed_files: The write lane's pre-retry check (plan
            opencode-validator-false-rate-limit-and-denied-turn §4.4 step 4,
            T4.8). Called only for an ``agent-write`` attempt that the adapter's
            structural check classified ``runner_error`` (a turn ended by an
            auto-rejected permission, so no result exists and ``after_result``
            never runs), with ``{task, task_id, kind, attempt, cwd, outcome}``;
            it returns the paths whose bytes moved against the task's pre-batch
            snapshot. Any → the attempt is recorded ``partial_application`` and
            no further attempt starts: a retry on top of a half-applied edit is
            the unsafe case. None → it stays ``runner_error`` and is retried like
            any other. A hook that raises is read as "could not tell", which
            fails closed the same way as a non-empty answer.
        jail_request: The grant a dispatch on the plugin's Landlock jail
            carries (plan codex-sandbox-unavailable §6 F1 "How a dispatch
            receives its grant", 2026-09-30). A read kind needs none — one is
            built from ``cwd`` — and is refused (rung 7, nothing spawned) if
            handed one that carries a write scope or target: a read kind never
            carries a grant. A write kind on the rung must carry one whose
            ``kind`` is the task's, whose ``write_scope`` is
            :data:`WRITE_SCOPE_BY_KIND`'s for it, and which names its target;
            anything else is refused on rung 7 naming the missing grant, never
            narrowed or widened. ``after_result`` and ``changed_files`` then
            see ``sandbox_rung``, ``jail_denials`` (a write dispatch on the
            rung) and ``jail_evidence``. A jail failure — a codex-internal
            EACCES the parent classifies as the jail's — is recorded rejected
            with one ``[JAIL_DENIED]`` line, never retried and never moved to
            another rung.
        tree_fingerprint: The write lane's guard on a report re-ask (the
            ladder's rule 7 for a write kind, :data:`SCHEMA_REPAIRS_BY_KIND`).
            Called with ``{task, task_id, kind, cwd, outcome}`` just before the
            re-ask and again after it; it returns a comparable value naming the
            current bytes of every file the batch may have moved (a dict keyed
            by path, so a difference can be named). Any difference — or a hook
            that raises — records the re-ask ``partial_application``: it was
            asked only to restate the batch's report, so a file it moved is an
            edit nobody verified. Without the hook a write kind gets no re-ask.
        nothing_changed: The write lane's question before ``after_result``
            (the ladder's rule 9, :data:`RESENDS_BY_KIND`, fix round 14),
            with the ``after_result`` context: why this schema-valid reply
            said ``applied`` while not one byte moved, or ``None`` when that
            is not the case (any byte moved, a check task, a crash, a jail
            denial — the classification decides those). A reason, while the
            allowance holds a re-send the deadline admits, sends the batch's
            own prompt once more with
            :func:`subagent_prompts.build_nothing_changed_resend_prompt`
            appended, instead of classifying the attempt; it is recorded
            ``batch_failed`` with that reason and a failure capture. A hook
            that raises is "no re-send": the classification decides.
        incomplete_report: The write lane's other question before
            ``after_result`` (an apply kind, fix round 18), with the same
            context: why this readable report, after edits that moved bytes,
            leaves some of the batch's items out of both ``ids`` and
            ``declined``, or ``None``. A reason, while the schema-repair
            allowance and the deadline admit it (:meth:`RetryLadder.
            record_report_reask`) and ``tree_fingerprint`` can guard it,
            sends the report re-ask (``incomplete=True``, the reason as its
            one problem) instead of classifying: Codex racing run 7's batch
            left a fix out of its report on purpose and stopped as a partial
            application on every resume. The restated report is classified
            like any; a re-ask that cannot restate it (prose, a timeout)
            leaves the original reply to be classified, and one that moved a
            file is a partial application. A hook that raises is "no re-ask".
        restate_findings: The implement lane's third question before
            ``after_result`` (fix round 28), with the same context:
            ``(problem, accepted findings)`` when the reply's own check holds
            an accepted finding verbatim with words added (live run 12: "…
            (known problem the user accepted in T002)"), or ``None``. It
            sends the same one report re-ask, the problem as its one problem
            and the check's findings open to restating
            (``restate_findings=True``), and nothing is recorded as accepted
            by it: the restated report is classified like any, and only its
            ``findings`` and ``note`` are taken, through
            :func:`merge_restated_check`, which keeps the first report's
            whole ``check`` unless every finding it changed was cut down to
            one of the accepted findings, word for word. A hook that raises
            is "no re-ask".
    """
    task_id = str(task.get("task_id", ""))
    kind = str(task.get("kind", ""))
    profile = profile_for_kind(kind)
    outcome = TaskOutcome(
        task_id=task_id, kind=kind, runner=runner, status=STATUS_REJECTED,
        profile=profile,
    )

    provider_name, model = parse_model_spec(runner, anchor=anchor)
    provider = get_provider(provider_name)
    if provider is None:
        outcome.status = STATUS_SPAWN_FAILED
        outcome.reason = f"runner {runner!r} has no built-in adapter"
        return outcome

    # --- pre-dispatch refusals: nothing is spawned for these ----------------
    reason = refuse_reason(
        task,
        supports_workspace_reads=provider.supports_workspace_reads,
        runner=runner,
    )
    if reason is not None:
        outcome.reason = reason
        return outcome
    if not provider.supports_profile(profile):
        outcome.reason = (
            f"{provider_name} does not implement the {profile!r} profile; a "
            f"read/analyze task is never downgraded to a write-capable "
            f"invocation, so this fails dispatch"
        )
        return outcome
    # D6 override (2026-09-17): replay the preflight's decision, never re-take
    # it here. A read kind reads the id of the rung its argv must render
    # (landlock rung); a write kind reads the decision taken for its own write
    # scope (plan step 3, 2026-09-30) — the plugin's jail, the F5 floor, or
    # none, in which case its argv renders unchanged.
    grant_refusal, jail_request, fallback = _dispatch_grant(
        task, kind=kind, profile=profile, runner=runner, cwd=cwd,
        provider=provider, jail_request=jail_request,
    )
    if grant_refusal is not None:
        outcome.reason = grant_refusal
        return outcome
    wrapping = _wrapping_rung(provider, profile, fallback)
    # The consent carries the kind's own write scope down to the render and the
    # backstop, which both refuse a scope the jail does not serve.
    write_consent = (
        host_write_posture_consent(write_scope=WRITE_SCOPE_BY_KIND.get(kind))
        if profile == PROFILE_AGENT_WRITE and fallback == SANDBOX_RUNG_UNSANDBOXED
        else None
    )
    # §2.2 (validation context by path): a snapshot named by path may sit in a
    # phase dir outside the runner's cwd. A runner that reads anywhere needs
    # nothing; one that can widen its read scope gets the flag for exactly
    # those directories; any other is refused here rather than handed a path
    # it cannot open (which reads as a confident, blind verdict).
    read_dirs = _context_read_dirs(task, cwd)
    if read_dirs and getattr(provider, "reads_outside_cwd", False):
        read_dirs = []
    if read_dirs and not getattr(provider, "read_scope_flag", None):
        outcome.reason = (
            f"{kind} batch {task.get('batch_index', task_id)} names "
            f"{', '.join(read_dirs)} outside the runner's working directory; "
            f"runner {runner} cannot read files there; rematerialize with a "
            f"capable runner. Nothing was dispatched."
        )
        return outcome
    try:
        target = resolve_output_target(task, phase_dir)
    except ResultRejected as exc:
        outcome.reason = exc.message
        return outcome
    outcome.output_path = str(target)

    prompt = (task.get("prompt") if prompt is None else prompt) or ""
    if not prompt.strip():
        outcome.reason = f"Task {task_id}: carries no prompt"
        return outcome
    # D3n: the literal token must never reach a runner. A write prompt that still
    # carries it means the scheduler's late substitution did not run, which would
    # silently drop every prior-batch summary — the exact context that keeps batch
    # N from re-applying or contradicting batch N-1. Contract error, not a warning.
    if kind in WRITE_KINDS and _PRIOR_CHANGES_TOKEN in prompt:
        outcome.reason = (
            f"Task {task_id}: the dispatched prompt still contains the literal "
            f"{_PRIOR_CHANGES_TOKEN} token, so the prior-batch context was never "
            f"substituted. A runner would receive the brace text and silently lose "
            f"every prior-batch summary. Nothing was dispatched."
        )
        return outcome

    transport = preferred_prompt_transport(provider_name)
    # D2d/D3: refuse an over-budget prompt HERE rather than letting llm_client's
    # Windows command-line guard fail it late with PROMPT_TOO_LONG. A stdin/file
    # transport is unbounded, so this only ever fires for an argv-only runner.
    over_budget = _prompt_over_budget(
        provider, model, prompt, transport, profile,
        **({"sandbox_fallback": fallback, "jail_request": jail_request}
           if wrapping is not None else {}),
    )
    if over_budget is not None:
        outcome.reason = f"Task {task_id}: {over_budget}"
        return outcome

    prefer_arrays = kind == "salvage"
    # D4.5: a salvage of a timed-out run may not persist `[]` (read once, here,
    # from the request the task is bound to; `None` for every other kind).
    salvage_failure = salvage_failure_of(task, phase_dir)
    effective_timeout = timeout or get_subagent_timeout(provider_name, anchor=anchor)
    budget = retries if retries is not None else get_subagent_retries(anchor=anchor)
    napper = sleep or time.sleep

    # §4.2.2's "the caller reads the flag before dispatch", on this lane and once
    # per dispatch — the schema file is read here, not per attempt, and the
    # per-(provider, phase) WARN is emitted once per process by
    # `schema_for_dispatch`. The phase comes from the KIND (see
    # `SCHEMA_PHASE_BY_KIND`): `None` means no schema, no flag and an argv
    # byte-identical to the pre-M7 lane. A `None` schema with a phase means the
    # adapter declined — no `structured_output_support`, or a schema this CLI
    # provably cannot carry — which resolves exactly like a failed §5.4.1 gate:
    # prompt-level JSON, marked `recovered`/`unvalidated`, never `native`.
    schema_phase = schema_phase_for_kind(kind)
    schema = None
    declined_marker = None
    if schema_phase:
        try:
            schema, resolved_marker = structured_output.schema_for_dispatch(
                provider, schema_phase
            )
        except structured_output.SchemaConfigError as exc:
            # Rung 7, not a rung 4/5 transport failure: no dispatch can produce a
            # schema file that is not there, so it is never retried and nothing
            # was spawned.
            outcome.status = STATUS_REJECTED
            outcome.reason = f"structured output: {exc}"
            return outcome
        if schema is None:
            # The adapter declined, so the marker is already decided and only the
            # result is still open; when a schema IS dispatched the post-run
            # verdict decides between `native` and `recovered` instead.
            declined_marker = resolved_marker

    # §7.1.b: what the two invocation lanes share is the *policy*, not the loop.
    # `RetryLadder` owns D3i's single monotonic deadline — taken once, every
    # attempt spawned with what is LEFT of it, every backoff sleep charged to the
    # same deadline, so a task with N retries can never run for (N+1) × the
    # configured ceiling — plus D3k's two separate counters and §7.5's admission
    # tests. The only lane-specific lines below are the blocking `_spawn` and the
    # `napper` call.
    #
    # The adapter's DECLARED vendor envelope (§7.6(b)) switches on §7.5's two
    # composition rules: rule 4's pre-dispatch admission test ("would one
    # worst-case attempt fit in what is left?", recorded `budget_exhausted` with
    # nothing spawned) and rule 6(b)'s refusal to re-issue an identical
    # rate-limit dispatch against a CLI that already exhausted its own 429 chain.
    # `getattr` rather than an attribute read: the eleven unmeasured adapters
    # declare `None`, which rule 6(c) reads as "assume one request" — never
    # "assume the worst".
    #
    # Rule 7 (the ladder's own): `SCHEMA_REPAIRS_BY_KIND` grants a kind its
    # schema-repair re-asks — `task_generation` one, every other kind none, so
    # rung 6 stays terminal for them exactly as before. A granted re-ask is an
    # attempt like any other: same deadline, its own `failed/` capture and its
    # own row in the batch report.
    ladder = RetryLadder(
        timeout=effective_timeout,
        retries=budget,
        envelope=getattr(provider, "internal_retries", None),
        now=time.monotonic,
        schema_repairs=SCHEMA_REPAIRS_BY_KIND.get(kind, 0),
        resends=(
            RESENDS_BY_KIND.get(kind, 0)
            if nothing_changed is not None and after_result is not None else 0
        ),
    )
    # What this attempt sends: the task's prompt, until the ladder grants the
    # schema-repair re-ask and it becomes that prompt plus the validator's
    # errors. A transport retry after the re-ask re-sends the re-ask.
    attempt_prompt = prompt
    attempt_repair: Optional[str] = None
    # Rule 9's re-send (fix round 14) is the batch again, not a re-ask: it
    # keeps every guard a first dispatch has (the pre-retry check included),
    # so it is marked on the attempt it produced and nowhere else.
    attempt_resend: Optional[str] = None
    resend_note: Optional[str] = None
    # A write kind's report re-ask: the files' state when it was granted, which
    # the re-ask must leave exactly as it found it (`tree_fingerprint`).
    repair_baseline: Any = None
    # A report-only turn cannot change what the original turn observed when
    # it ran its checks. Apply this before persisting the restated report so
    # the result file and the scheduler's verdict read the same evidence.
    repair_check: Optional[Dict[str, Any]] = None
    # Fix round 28: a restatement of a check's findings, the first report's
    # check and the accepted findings a changed finding may be cut down to.
    restate_check: Optional[Tuple[Dict[str, Any], List[str]]] = None
    # Fix round 18: the `after_result` context of a readable report that left
    # items out, kept while its re-ask runs, so a re-ask that cannot restate
    # it leaves this one to be classified.
    reask_fallback: Optional[Dict[str, Any]] = None
    fingerprint_context = {
        "task": task, "task_id": task_id, "kind": kind, "cwd": cwd,
        "outcome": outcome,
    }

    def elapsed() -> float:
        # D3j: wall-clock across *every* attempt, including the backoff sleeps
        # between them — not the sum of the children's own runtimes. That sum is
        # what made "bounded by a total per-task wall-clock budget" bound
        # nothing: a task that slept through four exponential backoffs would
        # report only the seconds its children ran and never reach
        # `effective_timeout`. Monotonic, so a clock step cannot rewind it.
        return ladder.elapsed()

    def never_started(attempts_done: int) -> str:
        return (
            f"the per-task wall-clock budget of {effective_timeout}s was "
            f"exhausted after {attempts_done} attempt(s); attempt "
            f"{attempts_done + 1} was never started"
        )

    while True:
        if ladder.next_attempt() is None:
            # §7.5 rules 3 and 4: no attempt starts with less than
            # MIN_ATTEMPT_BUDGET_S of the deadline left, and none starts at all
            # when what is left cannot hold one worst-case attempt of this
            # adapter's *declared* vendor envelope — better a slot that spawned
            # nothing than a child killed part-way through a retry chain the
            # harness cannot see.
            if ladder.stop_reason == STOP_BUDGET and not ladder.attempt_index:
                status = STATUS_BUDGET_EXHAUSTED
                error = budget_exhausted_reason(
                    ladder, target=runner, timeout=effective_timeout
                )
            elif ladder.stop_reason == STOP_BUDGET:
                # A grant taken back at the next start: `record()` applies the
                # same admission test to every grant, so only a clock that
                # moved in between (an overslept backoff) lands here. The last
                # attempt RAN, so its own status stands — `budget_exhausted`
                # means nothing was spawned (fix round 6).
                error = (
                    f"{error} (no further attempt: "
                    f"{budget_exhausted_reason(ladder, target=runner, timeout=effective_timeout)})"
                )
            else:
                status, error = STATUS_TIMEOUT, never_started(ladder.attempt_index)
            break
        attempt_index = ladder.attempt_index
        if before_attempt is not None:
            # The write path's snapshot / policy / audit leg. A refusal here means
            # nothing is spawned for this attempt — the whole point of enforcing
            # the policy pre-dispatch rather than only detecting it afterwards.
            try:
                before_attempt({
                    "task": task,
                    "task_id": task_id,
                    "kind": kind,
                    "profile": profile,
                    "runner": runner,
                    "provider": provider_name,
                    "model": model,
                    "cwd": cwd,
                    "attempt": attempt_index,
                    "prompt": attempt_prompt,
                    "repair": attempt_repair,
                    "transport": transport,
                    "outcome": outcome,
                })
            except ResultRejected as exc:
                outcome.status = exc.status
                outcome.reason = exc.message
                outcome.duration_seconds = elapsed()
                return outcome
        attempt_budget = ladder.remaining()
        if attempt_budget <= 0:
            # The ladder already admitted this attempt, so what drained the
            # budget is the `before_attempt` leg (a large pre-batch snapshot)
            # spending what the attempt was admitted with. Spawning here would
            # hand a runner a budget it cannot use and record the kill as its
            # own timeout; the budget is the task's, so its exhaustion is the
            # task's outcome.
            status, error = STATUS_TIMEOUT, never_started(attempt_index - 1)
            break
        try:
            capture = _spawn(
                provider=provider,
                model=model,
                prompt=attempt_prompt,
                profile=profile,
                transport=transport,
                timeout=attempt_budget,
                cwd=cwd,
                schema=schema,
                anchor=anchor,
                sandbox_fallback=fallback,
                # Only when there is something to widen, so a stand-in `_spawn`
                # with the historical keyword set is called as it always was.
                **({"read_dirs": read_dirs} if read_dirs else {}),
                # The same rule for the jail's grant and F5's consent: handed
                # on only to a dispatch on the rung that needs them.
                **({"jail_request": jail_request} if wrapping is not None else {}),
                **({"write_consent": write_consent} if write_consent is not None else {}),
            )
        except (
            StructuredOutputUnavailable, structured_output.SchemaConfigError
        ) as exc:
            # §4.2.1's sixth acceptance case: raised while the sidecar was being
            # written or while the argv was being rendered, so **nothing was
            # spawned and no partial argv reached the CLI**. Rung 7 — a
            # configuration error, never retried, because re-running produces the
            # same missing file.
            status, error = STATUS_REJECTED, f"structured output: {exc}"
            break
        except SandboxBackstopViolation as exc:
            # Plan step 3's backstop: nothing was spawned. Rung 7, never retried.
            status, error = STATUS_REJECTED, exc.message
            _record_unspawned_attempt(outcome, attempt_index, error, after_attempt)
            break
        except ValueError as exc:
            if not fallback:
                raise
            # An adapter refusing to render a rung without its grant (the
            # plugin's jail with no context): nothing was spawned. Rung 7.
            status, error = STATUS_REJECTED, str(exc)
            _record_unspawned_attempt(outcome, attempt_index, error, after_attempt)
            break
        usage = _safe_parse_usage(provider, capture)
        _report_jail_outcome(task_id, capture)
        # The document this attempt extracted, if any — what a schema-repair
        # re-ask quotes the validator's errors about.
        data = None
        denied_line = getattr(capture, "jail_denied_line", None)
        if denied_line:
            # A jail failure (plan F1 item 6): not a model error, never
            # retried, never moved to another rung.
            status, error = STATUS_REJECTED, denied_line
        else:
            status, error = _classify_pre_parse(capture)
        if repair_baseline is not None:
            moved = _moved_during_repair(
                tree_fingerprint, fingerprint_context, repair_baseline
            )
            if moved is not None:
                shown = ", ".join(moved[:5]) + (", …" if len(moved) > 5 else "")
                status, error = STATUS_PARTIAL, (
                    f"PARTIAL APPLICATION: the report re-ask (attempt "
                    f"{attempt_index}) was asked only to restate this batch's "
                    f"report, but files changed while it ran ({shown}). Nothing "
                    f"it did is recorded as applied, no further attempt is "
                    f"started, the batch loop stops here and the phase is NOT "
                    f"marked completed."
                )

        if status == STATUS_OK:
            status, error, data, marker = _parse_with_schema_policy(
                provider, capture, kind=kind, prefer_arrays=prefer_arrays,
                schema=schema, schema_phase=schema_phase or "",
                model=f"{provider_name}:{model}",
                declined_marker=declined_marker,
                failure=salvage_failure,
            )
            if marker is not None:
                outcome.structured_output = marker
            if status == STATUS_OK:
                if repair_check is not None and isinstance(data, dict):
                    data = {**data, "check": copy.deepcopy(repair_check)}
                elif restate_check is not None and isinstance(data, dict):
                    data = {**data, "check": merge_restated_check(
                        restate_check[0], data.get("check"), restate_check[1],
                    )}
                try:
                    written = persist_result(task, phase_dir, data)
                except ResultRejected as exc:
                    status, error = exc.status, exc.message
                    # The byte cap, not the shape: the document validated, so a
                    # re-ask quoting "the validator's errors" would quote none
                    # and tell the runner its reply has the wrong shape (fix
                    # round 6). Rung 6 stays terminal for it.
                    data = None
                else:
                    outcome.output_path = written
                    result_context = {
                        "task": task,
                        "task_id": task_id,
                        "kind": kind,
                        "profile": profile,
                        "runner": runner,
                        "cwd": cwd,
                        "attempt": attempt_index,
                        "prompt": attempt_prompt,
                        "result": data,
                        "exit_code": capture.exit_code,
                        **_jail_hook_context(capture, jail_request, fallback),
                    }
                    resend_why = (
                        _ask_nothing_changed(nothing_changed, result_context)
                        if ladder.resends_left > 0 else None
                    )
                    if resend_why:
                        resend = ladder.record_resend()
                        if resend.retry:
                            # Rule 9: nothing moved, so the batch goes again,
                            # told so; this attempt is not classified.
                            outcome.attempts.append(Attempt(
                                index=attempt_index,
                                status=STATUS_BATCH_FAILED,
                                exit_code=capture.exit_code,
                                duration_seconds=capture.duration,
                                error=resend_why,
                                usage=usage,
                                capture_path=_write_failure_capture(
                                    phase_dir=phase_dir, task=task,
                                    attempt_index=attempt_index,
                                    argv=capture.argv, prompt=attempt_prompt,
                                    stdout=capture.stdout, stderr=capture.stderr,
                                    exit_code=capture.exit_code,
                                    duration=capture.duration,
                                    status=STATUS_BATCH_FAILED, error=resend_why,
                                    repair=attempt_repair or attempt_resend,
                                ),
                                repair=attempt_repair or attempt_resend,
                            ))
                            _accumulate_usage(outcome, usage)
                            _notify_after_attempt(after_attempt, outcome.attempts[-1])
                            outside = [
                                str(path) for path in
                                (result_context.get("moved_outside") or [])
                            ]
                            attempt_prompt = build_nothing_changed_resend_prompt(
                                prompt,
                                declared=_nothing_changed_files(task, cwd),
                                named=[
                                    str(path) for path in
                                    (data.get("files_touched") or [])
                                    if isinstance(path, str)
                                ] if isinstance(data, dict) else [],
                                outside=outside,
                            )
                            attempt_resend = RESEND_NOTHING_CHANGED
                            attempt_repair = None
                            repair_baseline = None
                            repair_check = None
                            restate_check = None
                            print(
                                f"[exec-subagents] {task_id}: the reply says the "
                                f"batch was applied, but "
                                f"{'none of the files it declares changed' if outside else 'no file changed'}; "
                                f"sending the batch to {runner} once more, "
                                f"told so (attempt {attempt_index + 1}). What "
                                f"was applied is still decided by comparing "
                                f"the files with the pre-batch snapshot."
                            )
                            continue
                        resend_note = resend.note
                    reask_why = (
                        _ask_incomplete_report(incomplete_report, result_context)
                        if incomplete_report is not None and not resend_why
                        and attempt_repair is None
                        and ladder.schema_repairs_left > 0 else None
                    )
                    # Fix round 28: or its own check holds an accepted
                    # finding with words added; the same one re-ask.
                    restate = (
                        _ask_restate_findings(restate_findings, result_context)
                        if restate_findings is not None and not reask_why
                        and not resend_why and attempt_repair is None
                        and ladder.schema_repairs_left > 0 else None
                    )
                    if restate is not None:
                        reask_why = restate[0]
                    reask = (
                        _incomplete_report_reask(
                            kind=kind, prompt=prompt, task=task,
                            why=reask_why, provider=provider, model=model,
                            capture=capture, transport=transport,
                            profile=profile, ladder=ladder,
                            tree_fingerprint=tree_fingerprint,
                            fingerprint_context=fingerprint_context,
                            budget_kwargs=(
                                {"sandbox_fallback": fallback,
                                 "jail_request": jail_request}
                                if wrapping is not None else {}
                            ),
                            restate_findings=restate is not None,
                        ) if reask_why else None
                    )
                    if reask is not None:
                        # Rule 7, second form (fix round 18): the report read
                        # but left items out; the runner restates it once.
                        reask_prompt, repair_baseline = reask
                        if restate is not None:
                            # Fix round 28: only its findings and note may
                            # change, and only as `merge_restated_check` lets.
                            original = data.get("check") if isinstance(data, dict) else None
                            restate_check = (
                                (copy.deepcopy(original), [str(a) for a in restate[1]])
                                if isinstance(original, dict) else None
                            )
                            repair_check = None
                        else:
                            repair_check = _report_check_evidence(data)
                        # Fix round 19: a readable report, so its own status
                        # and no failure capture (the re-ask's prompt file
                        # quotes the reply).
                        outcome.attempts.append(Attempt(
                            index=attempt_index,
                            status=STATUS_INCOMPLETE_REPORT,
                            exit_code=capture.exit_code,
                            duration_seconds=capture.duration,
                            error=reask_why,
                            usage=usage,
                            repair=attempt_resend,
                        ))
                        _accumulate_usage(outcome, usage)
                        _notify_after_attempt(after_attempt, outcome.attempts[-1])
                        reask_fallback = {
                            "task": task,
                            "task_id": task_id,
                            "kind": kind,
                            "profile": profile,
                            "runner": runner,
                            "cwd": cwd,
                            "attempt": attempt_index,
                            "prompt": attempt_prompt,
                            "result": data,
                            "exit_code": capture.exit_code,
                            "stderr_tail": _redact_probe_tail(capture.stderr, 2000),
                            "usage": usage,
                            "resent": attempt_resend is not None,
                            "resend_note": resend_note,
                            **_jail_hook_context(capture, jail_request, fallback),
                        }
                        attempt_prompt = reask_prompt
                        attempt_repair = REPAIR_INCOMPLETE_REPORT
                        attempt_resend = None
                        if restate is not None:
                            print(
                                f"[exec-subagents] {task_id}: its own check "
                                f"reports a finding the user accepted with "
                                f"words added; asking {runner} once to restate "
                                f"its report without touching any file (report "
                                f"re-ask, attempt {attempt_index + 1}). Nothing "
                                f"is recorded as accepted unless the restated "
                                f"finding is the accepted one, word for word."
                            )
                            continue
                        print(
                            f"[exec-subagents] {task_id}: the batch's report "
                            f"leaves some of its items out of both `ids` and "
                            f"`declined`; asking {runner} once to restate it "
                            f"without touching any file (report re-ask, "
                            f"attempt {attempt_index + 1}). What was applied is "
                            f"still decided by comparing the files with the "
                            f"pre-batch snapshot."
                        )
                        continue
                    outcome.attempts.append(Attempt(
                        index=attempt_index,
                        status=STATUS_OK,
                        exit_code=capture.exit_code,
                        duration_seconds=capture.duration,
                        usage=usage,
                        repair=attempt_repair or attempt_resend,
                    ))
                    _notify_after_attempt(after_attempt, outcome.attempts[-1])
                    outcome.status = STATUS_OK
                    outcome.duration_seconds = elapsed()
                    _accumulate_usage(outcome, usage)
                    if after_result is not None:
                        # D3g: the model's claim is never the verdict. The
                        # snapshot/diff classification runs HERE — after rung 6, so
                        # a prose result has already failed as `schema_invalid` and
                        # can never be classified as "applied".
                        after_result({
                            "task": task,
                            "task_id": task_id,
                            "kind": kind,
                            "profile": profile,
                            "runner": runner,
                            "cwd": cwd,
                            "attempt": attempt_index,
                            "prompt": attempt_prompt,
                            "result": data,
                            "exit_code": capture.exit_code,
                            # Not an `outcome` field: this one leaves the module
                            # through the caller's callback, so no sink here can
                            # promise it is redacted on the way out. The only
                            # shipped `after_result` ignores the key, which made
                            # a bare tail safe by accident of its consumer — and
                            # would have kept the AST guard green while a future
                            # callback logged its context raw. Redacted at the
                            # source instead, fail-safe: a raising redactor
                            # yields a placeholder, never the stream.
                            "stderr_tail": _redact_probe_tail(capture.stderr, 2000),
                            "usage": usage,
                            "duration_seconds": outcome.duration_seconds,
                            "outcome": outcome,
                            # Rule 9: whether this attempt was the re-send of
                            # a batch that changed nothing, and why a re-send
                            # the classification would have wanted was not
                            # granted (the deadline), for its wording.
                            "resent": attempt_resend is not None,
                            "resend_note": resend_note,
                            **_jail_hook_context(capture, jail_request, fallback),
                        })
                        if not outcome.ok:
                            return outcome
                    if capture.exit_code not in (0, None):
                        # Exit code is evidence, never the verdict: for a read
                        # task a schema-valid result wins over a non-zero exit
                        # (several CLIs exit non-zero on a warning while still
                        # printing the answer), and the anomaly stays visible
                        # here rather than being either fatal or invisible.
                        outcome.reason = (
                            f"runner exited {capture.exit_code} but produced a "
                            f"schema-valid result; stderr tail: "
                            f"{_tail(capture.stderr, 2000)!r}"
                        )
                    return outcome
            elif status in RECLASSIFIABLE_STATUSES:
                # Only a run with no usable result may be reclassified as
                # rate-limited or unauthenticated: the classifier matches on the
                # captured streams, and both a successful answer and a
                # schema-invalid one routinely quote plan text that would trip
                # those patterns. Rung 6 therefore never reaches this branch —
                # it is never retried (D3k), so laundering it into rung 3's
                # backoff or rung 1's batch-wide auth failure would be pure loss.
                reclassified = _classify_failed_run(provider, capture, model)
                if reclassified is not None:
                    status, error = reclassified

        # The pre-retry check (T4.8, widened in fix round 8): a write attempt
        # the ladder could answer by sending the batch's own prompt again — a
        # timeout, a runner error, a prose reply, a rate limit — is asked first
        # whether it already moved bytes. If it did, the batch is never sent
        # again on top of its own edits: the attempt is a partial application,
        # or, for a write kind whose reply could not be read, the one report
        # re-ask (rule 7), which restates the report and edits nothing. A re-ask
        # in flight is exempt: its retry re-sends the re-ask, and
        # `repair_baseline` above already fails one that moved a file.
        repeatable = True
        partial_if_refused: Optional[str] = None
        reply_text: Optional[str] = None
        if (
            (status in RETRYABLE_STATUSES or status in BACKOFF_STATUSES)
            and profile == PROFILE_AGENT_WRITE
            and changed_files is not None
            and attempt_repair is None
        ):
            checked_status, checked_error = _denied_write_turn(
                changed_files, error,
                {
                    "task": task,
                    "task_id": task_id,
                    "kind": kind,
                    "attempt": attempt_index,
                    "cwd": cwd,
                    "outcome": outcome,
                    **_jail_hook_context(capture, jail_request, fallback),
                },
                status=status,
            )
            if checked_status == STATUS_PARTIAL:
                repeatable = False
                if status == STATUS_UNPARSEABLE and ladder.schema_repairs_left > 0:
                    reply_text = _reply_text(provider, capture.stdout)
                    if _write_report_repairable(capture, reply_text, tree_fingerprint):
                        partial_if_refused = checked_error
                if partial_if_refused is None:
                    # Fix round 16: a batch killed at its time limit after its
                    # edits landed is said so on the stop, edits kept.
                    outcome.ran_out_of_time = status == STATUS_TIMEOUT
                    status, error = checked_status, checked_error

        evidence = getattr(capture, "jail_evidence", None) or {}
        if (
            status != STATUS_OK
            and not getattr(capture, "jail_denied_line", None)
            and evidence.get("class") == landlock_dispatch.JAIL_CLASS_ORDINARY
        ):
            # An EACCES the parent classified as an ordinary permission error
            # (inside an allow entry, or unwritable by the user too): the
            # attempt fails as it always did, and says why it is not the jail.
            error = (
                f"{error} (not a jail denial: "
                f"{evidence.get('reason') or 'ordinary permission error'})"
            )
        capture_path = _write_failure_capture(
            phase_dir=phase_dir,
            task=task,
            attempt_index=attempt_index,
            argv=capture.argv,
            # The prompt this attempt really sent, so the argv elision below
            # still finds it on an argv-transport runner's re-ask.
            prompt=attempt_prompt,
            stdout=capture.stdout,
            stderr=capture.stderr,
            exit_code=capture.exit_code,
            duration=capture.duration,
            status=status,
            error=error,
            repair=attempt_repair or attempt_resend,
        )
        outcome.attempts.append(Attempt(
            index=attempt_index,
            status=status,
            exit_code=capture.exit_code,
            duration_seconds=capture.duration,
            error=error,
            usage=usage,
            capture_path=capture_path,
            repair=attempt_repair or attempt_resend,
        ))
        _accumulate_usage(outcome, usage)
        # Before the ladder decides and before any backoff sleep: a caller that
        # narrows on a rate limit (§5) reacts while this task is still retrying.
        _notify_after_attempt(after_attempt, outcome.attempts[-1])

        # One `record` call is the whole decision (D3k, §7.5 rules 2/3/6): rung 1
        # is fatal to the batch; rung 3 backs off with jitter, at most three
        # times, without consuming the transport budget; rungs 2/4/5 spend
        # `driver.subagent_retries`; rungs 6/7 are never retried — rung 6 only
        # once the kind's schema-repair allowance (rule 7) is spent or was never
        # granted. Every one of those decisions is taken against the same
        # deadline the spawns are charged to, which is what keeps the counters a
        # ceiling the wall clock usually reaches first.
        # A schema-invalid attempt with no extracted document is the CLI's own
        # exhausted structured-output budget (§4.2.1: the CLI already spent the
        # pinned re-ask), so it is not repairable here either; nor is a valid
        # document `persist_result` refused for its size (`data` dropped above).
        repairable = data is not None
        if repairable and status == STATUS_SCHEMA_INVALID and kind in WRITE_KINDS:
            # A write kind's re-ask restates the runner's own previous reply, so
            # it needs that reply, the hook that proves it moved nothing, and an
            # attempt the jail denied nothing in (its verdict would otherwise
            # be read off the re-ask's clean stream instead).
            reply_text = _reply_text(provider, capture.stdout)
            repairable = _write_report_repairable(
                capture, reply_text, tree_fingerprint
            )
        if partial_if_refused is not None:
            # A prose reply after edits (the pre-retry check above): the same
            # re-ask an unreadable report gets, never the batch again.
            repairable = True
        action = ladder.record(
            status, repairable=repairable, repeatable=repeatable
        )
        if partial_if_refused is not None and not action.retry:
            # The re-ask was refused for want of budget: the edits stay
            # unverified, so the attempt ends as the partial application the
            # check found, with the ladder's reason appended.
            status, error = STATUS_PARTIAL, partial_if_refused
            if action.note:
                error = f"{error} ({action.note})"
            break
        if action.retry and action.repair:
            # The one schema-repair re-ask: same runner, same deadline. A read
            # kind gets the original prompt plus what was wrong and the reply
            # shape; a write kind gets only its own previous reply to restate,
            # never the batch's instructions again. The errors are re-read from
            # the extracted document, because the status line keeps only five,
            # and a reply that is not valid JSON is told so instead of being
            # handed the errors of a fragment from inside it. A prose reply has
            # no document: its own error is the one problem. A write kind's
            # re-ask lists the batch's ids in prompt order, so a reply that
            # numbered its items ("Suggestion 1: …") restates them by id.
            problems = validate_result(kind, data) if data is not None else []
            syntax = capture.reply_syntax_error
            repair_prompt = build_schema_repair_prompt(
                kind, prompt, problems or [error], syntax_error=syntax,
                **({
                    "previous_reply": reply_text,
                    "expected_ids": [
                        str(item) for item in task.get("expected_ids") or []
                    ],
                } if kind in WRITE_KINDS else {}),
            )
            too_long = _prompt_over_budget(
                provider, model, repair_prompt, transport, profile,
                **({"sandbox_fallback": fallback, "jail_request": jail_request}
                   if wrapping is not None else {}),
            )
            if too_long is not None:
                if partial_if_refused is not None:
                    status, error = STATUS_PARTIAL, partial_if_refused
                error = f"{error} (no schema-repair re-ask: {too_long})"
                break
            if kind in WRITE_KINDS:
                try:
                    repair_baseline = tree_fingerprint(fingerprint_context)
                except Exception as exc:  # noqa: BLE001 - fail closed: no re-ask
                    if partial_if_refused is not None:
                        status, error = STATUS_PARTIAL, partial_if_refused
                    error = (
                        f"{error} (no report re-ask: the files' state before it "
                        f"could not be recorded, {type(exc).__name__})"
                    )
                    break
                repair_check = _report_check_evidence(data)
            attempt_prompt = repair_prompt
            attempt_repair = REPAIR_SCHEMA_INVALID
            if kind in WRITE_KINDS:
                print(
                    f"[exec-subagents] {task_id}: the batch's closing report "
                    f"could not be read; asking {runner} once to restate it "
                    f"without touching any file (report re-ask, attempt "
                    f"{attempt_index + 1}). What was applied is still decided "
                    f"by comparing the files with the pre-batch snapshot."
                )
            else:
                print(
                    f"[exec-subagents] {task_id}: the reply "
                    + ("is not valid JSON" if syntax else
                       f"does not match the {kind} result shape "
                       f"({len(problems) or 1} problem(s))")
                    + f"; re-asking {runner} once with what was wrong "
                    f"(schema repair, attempt {attempt_index + 1})."
                )
            continue
        if action.retry:
            if action.delay:
                # The ladder computes the delay — it is pure, so the test switch
                # cannot live there. Applying the hook *here*, at the one place
                # this lane really sleeps, keeps MULTI_LLM_TEST_FAST_BACKOFF=1 an
                # exact 10 ms without putting an env read in the policy object.
                napper(_apply_backoff_hook(action.delay))
            continue
        if action.note:
            # A retry, backoff or schema-repair re-ask the status earned and the
            # budget refused (rule 3's deadline or rule 4's declared envelope):
            # the retry budget is not the only budget, and without the note the
            # recorded reason names a failure the harness had, and did not
            # spend, an attempt for. The unused counts are the ladder's own.
            error = f"{error} ({action.note})"
        break

    if (
        reask_fallback is not None and after_result is not None
        and status != STATUS_PARTIAL
    ):
        # Fix round 18: the re-ask of a report that left items out could not
        # restate it (prose, a timeout, a refused runner) and moved nothing,
        # so the report the batch did send is classified as it stands.
        outcome.status = STATUS_OK
        outcome.duration_seconds = elapsed()
        after_result({
            **reask_fallback,
            "duration_seconds": outcome.duration_seconds,
            "outcome": outcome,
        })
        outcome.reason = (
            f"{outcome.reason or ''} (its report re-ask did not restate the "
            f"report: {error})"
        ).strip()
        return outcome
    if attempt_repair and status in (STATUS_SCHEMA_INVALID, STATUS_UNPARSEABLE):
        error = f"{error} (after the one schema-repair re-ask)"
    outcome.status = status
    outcome.reason = error
    outcome.duration_seconds = elapsed()
    return outcome


def _denied_write_turn(
    changed_files: Callable[[Dict[str, Any]], Sequence[str]],
    error: str,
    context: Dict[str, Any],
    *,
    status: str = STATUS_RUNNER_ERROR,
) -> Tuple[str, str]:
    """``(status, reason)`` for a failed write attempt a retry would re-send.

    T4.8 asked it for a turn a denial ended (``runner_error``); since fix
    round 8 it is asked for every write attempt whose ``status`` the ladder
    could answer with the batch's own prompt again (a timeout, a prose reply,
    a rate limit). With changed files, ``partial_application`` in the
    scheduler's own words (``PARTIAL APPLICATION: …``, stop the loop, keep the
    snapshot, do not complete the phase), never retried because the status is
    on no rung. With none, ``status`` and ``error`` unchanged, retried as
    before.
    """
    try:
        changed = [str(path) for path in (changed_files(context) or ())]
    except Exception as exc:  # noqa: BLE001 - fail closed, never retry blind
        return STATUS_PARTIAL, (
            f"PARTIAL APPLICATION (unverified): the attempt failed ({error}), "
            f"and the working tree could not be compared with the pre-batch "
            f"snapshot ({type(exc).__name__}), so no further attempt is "
            f"started — a retry would send the whole batch again on top of "
            f"whatever it already edited. The batch loop stops here and the "
            f"phase is NOT marked completed."
        )
    if not changed:
        return status, error
    shown = ", ".join(changed[:5]) + (", …" if len(changed) > 5 else "")
    return STATUS_PARTIAL, (
        f"PARTIAL APPLICATION: {len(changed)} file(s) changed ({shown}), but "
        f"the attempt failed ({error}). No further attempt is started — a "
        f"retry would send the whole batch again on top of those edits. The "
        f"batch loop stops here and the phase is NOT marked completed."
    )


def _ask_nothing_changed(
    hook: Optional[Callable[[Dict[str, Any]], Optional[str]]],
    context: Dict[str, Any],
) -> Optional[str]:
    """Rule 9's question to the write lane's ``nothing_changed`` hook.

    ``None`` — no re-send, the classification decides — when there is no
    hook, it answers nothing, or it raises: a re-send is granted only on a
    measured "not one byte moved", never on "could not tell".
    """
    if hook is None:
        return None
    try:
        answer = hook(context)
    except Exception as exc:  # noqa: BLE001 - no re-send without a measurement
        print(
            f"[exec-subagents] warning: could not tell whether "
            f"{context.get('task_id')} changed any file "
            f"({type(exc).__name__}); its reply is classified as it stands.",
            file=sys.stderr,
        )
        return None
    return str(answer) if answer else None


def _nothing_changed_files(task: Dict[str, Any], cwd: Optional[str]) -> List[str]:
    """The batch's declared files, relative to *cwd* when they lie under it,
    for the rule-9 re-send's prompt."""
    names: List[str] = []
    for path in declared_file_set(task):
        if cwd and os.path.isabs(path):
            try:
                relative = os.path.relpath(path, cwd)
            except ValueError:  # pragma: no cover - another drive on Windows
                relative = path
            if not relative.startswith(".."):
                path = relative
        names.append(path.replace(os.sep, "/"))
    return names


def _ask_incomplete_report(
    hook: Optional[Callable[[Dict[str, Any]], Optional[str]]],
    context: Dict[str, Any],
) -> Optional[str]:
    """The ``incomplete_report`` hook's answer: why a readable write report
    leaves items out, or ``None`` (no hook, no answer, or it raised — a re-ask
    is never sent on "could not tell")."""
    if hook is None:
        return None
    try:
        answer = hook(context)
    except Exception as exc:  # noqa: BLE001 - no re-ask without an answer
        print(
            f"[exec-subagents] warning: could not tell whether "
            f"{context.get('task_id')}'s report accounts for every item "
            f"({type(exc).__name__}); its reply is classified as it stands.",
            file=sys.stderr,
        )
        return None
    return str(answer) if answer else None


def _ask_restate_findings(
    hook: Optional[Callable[[Dict[str, Any]], Optional[Tuple[str, Sequence[str]]]]],
    context: Dict[str, Any],
) -> Optional[Tuple[str, List[str]]]:
    """The ``restate_findings`` hook's answer (fix round 28): ``(problem,
    accepted findings)``, or ``None`` (no hook, no answer, a malformed one,
    or it raised — a re-ask is never sent on "could not tell")."""
    if hook is None:
        return None
    try:
        answer = hook(context)
    except Exception as exc:  # noqa: BLE001 - no re-ask without an answer
        print(
            f"[exec-subagents] warning: could not tell whether "
            f"{context.get('task_id')}'s check findings need restating "
            f"({type(exc).__name__}); its reply is classified as it stands.",
            file=sys.stderr,
        )
        return None
    if not answer or len(answer) != 2 or not str(answer[0] or "").strip():
        return None
    allowed = [str(item) for item in (answer[1] or []) if str(item).strip()]
    return (str(answer[0]), allowed) if allowed else None


def merge_restated_check(
    original: Dict[str, Any], restated: Any, allowed: Sequence[str],
) -> Dict[str, Any]:
    """The ``check`` a restated report is classified with (fix round 28):
    the first report's whole ``check`` — ``passed``, ``ran``, ``listed``,
    everything its checks observed, as :func:`_report_check_evidence` keeps
    it across any report-only turn — with only two things taken from the
    restatement:

    * its ``findings``, when every finding of the first report it changed
      was cut down to one of *allowed* (the accepted findings the re-ask
      named), whitespace aside, that the changed finding held word for word,
      and the words cut are in its ``note`` (case and punctuation aside), so
      nothing a finding said leaves the record. A restatement that drops a
      finding, rewords one, turns the check into a pass or cuts words it
      does not move to its note keeps the first report's findings: a
      report-only turn ran no check, so it can say less about one only by
      moving the words the re-ask named to the note. A finding it adds is
      kept.
    * its ``note``, when it is a non-blank string.

    Never a classification: what is accepted is still decided by
    ``write_batch_scheduler.split_accepted_findings`` on what this returns.
    """
    merged = copy.deepcopy(original)
    if not isinstance(restated, dict):
        return merged

    def plain(text: Any) -> str:
        return " ".join(str(text or "").split())

    def words(text: Any) -> str:
        return " ".join(re.findall(r"[a-z0-9]+", str(text or "").lower()))

    note = restated.get("note")
    note_words = words(note) if isinstance(note, str) else ""

    def moved_to_note(old: str, new: str) -> bool:
        head, _, tail = plain(old).partition(plain(new))
        return all(words(part) in note_words for part in (head, tail) if words(part))

    before = batch_check_findings({"check": original}) or []
    candidate = copy.deepcopy(original)
    candidate["findings"] = copy.deepcopy(restated.get("findings"))
    after = batch_check_findings({"check": candidate}) or []
    accepted = {plain(item) for item in allowed if plain(item)}
    changed = [finding for finding in before if finding not in after]
    added = [finding for finding in after if finding not in before]
    cut_down = all(
        any(
            plain(new) in accepted and plain(new) in plain(old)
            and moved_to_note(old, new)
            for new in added
        )
        for old in changed
    )
    if after and cut_down:
        merged["findings"] = candidate["findings"]
    if isinstance(note, str) and note.strip():
        merged["note"] = note
    return merged


def _incomplete_report_reask(
    *,
    kind: str,
    prompt: str,
    task: Dict[str, Any],
    why: str,
    provider: Any,
    model: str,
    capture: Any,
    transport: str,
    profile: str,
    ladder: RetryLadder,
    tree_fingerprint: Optional[Callable[[Dict[str, Any]], Any]],
    fingerprint_context: Dict[str, Any],
    budget_kwargs: Dict[str, Any],
    restate_findings: bool = False,
) -> Optional[Tuple[str, Any]]:
    """``(re-ask prompt, files' state)`` when the report re-ask for an
    incomplete report may go out, else ``None`` (fix round 18).

    The same guards as the rule-7 re-ask of an unreadable report: a reply to
    quote, the hook that proves the re-ask moved nothing, no jail denial on
    the attempt's stream, a prompt the transport carries — and then the
    ladder's grant, which spends the schema-repair allowance. Any guard that
    does not hold leaves the reply to be classified as it stands.
    *restate_findings* (fix round 28) asks for the restatement of a check
    finding instead of the items' account (the re-ask prompt's
    ``restate_findings`` form); the guards and the grant are the same.
    """
    reply_text = _reply_text(provider, capture.stdout)
    if not _write_report_repairable(capture, reply_text, tree_fingerprint):
        return None
    reask_prompt = build_schema_repair_prompt(
        kind, prompt, [why], previous_reply=reply_text,
        expected_ids=[str(item) for item in task.get("expected_ids") or []],
        incomplete=not restate_findings, restate_findings=restate_findings,
    )
    if _prompt_over_budget(
        provider, model, reask_prompt, transport, profile, **budget_kwargs,
    ) is not None:
        return None
    try:
        baseline = tree_fingerprint(fingerprint_context)  # type: ignore[misc]
    except Exception:  # noqa: BLE001 - fail closed: no re-ask
        return None
    if not ladder.record_report_reask().retry:
        return None
    return reask_prompt, baseline


def _write_report_repairable(
    capture: Any,
    reply_text: Optional[str],
    tree_fingerprint: Optional[Callable[[Dict[str, Any]], Any]],
) -> bool:
    """Whether a write attempt's unreadable report may be re-asked (rule 7).

    All three, or rung 6 stays terminal exactly as before: a previous reply to
    restate, the hook that proves the re-ask moved nothing, and a stream the
    plugin's jail recorded no denial on — the jail's verdict is read off the
    attempt's own stream, so a re-ask with a clean stream would launder it.
    """
    if tree_fingerprint is None or not (reply_text or "").strip():
        return False
    denials = getattr(capture, "jail_denials", None)
    if denials is not None and getattr(denials, "total", 0):
        return False
    return True


def _moved_during_repair(
    tree_fingerprint: Optional[Callable[[Dict[str, Any]], Any]],
    context: Dict[str, Any],
    baseline: Any,
) -> Optional[List[str]]:
    """The paths a report re-ask moved, or ``None`` when it moved nothing.

    A hook that raises is "could not tell", which fails closed as a move.
    """
    if tree_fingerprint is None:  # pragma: no cover - a baseline needs the hook
        return ["<the files could not be compared>"]
    try:
        after = tree_fingerprint(context)
    except Exception as exc:  # noqa: BLE001 - fail closed
        return [f"<the files could not be compared: {type(exc).__name__}>"]
    if after == baseline:
        return None
    if isinstance(after, dict) and isinstance(baseline, dict):
        moved = sorted(
            str(path) for path in set(after) | set(baseline)
            if after.get(path) != baseline.get(path)
        )
        return moved or ["<the files could not be compared>"]
    return ["<the files could not be compared>"]


def _prompt_over_budget(
    provider: Any,
    model: str,
    prompt: str,
    transport: str,
    profile: str,
    *,
    sandbox_fallback: Optional[str] = None,
    jail_request: Optional[JailRequest] = None,
) -> Optional[str]:
    """Why ``prompt`` cannot travel this runner's argv, or ``None`` (D2d).

    The budget is a Windows command-line constraint, so a ``stdin``/``file``
    transport is unbounded and this is a no-op there. For an argv-only runner it
    measures the *rendered* non-prompt argv too, because that is what Windows
    actually limits — and it resolves ``argv[0]`` exactly as :func:`_spawn` does,
    because an npm ``.cmd``/``.bat`` shim is run by cmd.exe and therefore carries
    the 8,191-unit cap rather than ``CreateProcess``'s 32,767. The same resolution
    answers the second cmd.exe hazard: the shim's command line is *reparsed*, so a
    metacharacter-bearing prompt is refused here rather than handed to that
    reparse (BatBadBut / CVE-2024-24576 class), mirroring ``llm_client``'s guard
    on the fan-out path.

    On the plugin's Landlock jail (``sandbox_fallback`` a wrapping rung; plan
    codex-sandbox-unavailable §6 F1 "Dispatch shape" item 4, 2026-09-30) the
    argv measured is the WRAPPED one — the interpreter, the wrapper, the
    ``--allow`` entries and the rung's in-CLI atoms — rendered with
    placeholder paths (``landlock_dispatch.preview_wrap_argv``), creating
    nothing.
    """
    try:
        from .subagent_tasks import prompt_budget_utf16, utf16_units
    except ImportError:  # pragma: no cover
        from utils.subagent_tasks import prompt_budget_utf16, utf16_units

    if transport in ("stdin", "file"):
        return None
    wrap = _wrapping_rung(provider, profile, sandbox_fallback)
    try:
        argv = provider.build_agent_command(prompt, model, profile)
        if wrap is not None and jail_request is not None:
            argv = provider.apply_sandbox_fallback(
                argv, profile, wrap.name,
                context=landlock_dispatch.preview_context(jail_request),
            )
    except Exception:  # noqa: BLE001 - a budget probe must not mask a refusal
        return None
    try:
        launcher, is_batch_shim = _resolve_executable(argv[0])
    except OSError:  # pragma: no cover - PATH probe failure is not a refusal
        launcher, is_batch_shim = [argv[0]], False
    if wrap is not None and jail_request is not None:
        launcher = landlock_dispatch.preview_wrap_argv(launcher, wrap, jail_request)
    if is_batch_shim:
        unsafe = sorted(set(prompt) & _CMD_UNSAFE_CHARS)
        if unsafe:
            chars = ", ".join(repr(ch) for ch in unsafe)
            return (
                f"{provider.name} resolves to a cmd.exe batch shim "
                f"({launcher[0]}) and delivers the prompt on argv, but the "
                f"prompt contains cmd.exe metacharacters ({chars}). cmd.exe "
                f"reparses the shim's command line, so these characters could "
                f"corrupt the prompt or escape into executed commands "
                f"(BatBadBut / CVE-2024-24576 class). Install a native "
                f"executable for this runner, or configure a runner with a "
                f"stdin/file prompt transport (driver.subagent_runner). "
                f"Nothing was dispatched."
            )
    # Measure the argv `_spawn` will actually run: the resolved launcher, not the
    # adapter's bare command name.
    rendered = [*launcher, *argv[1:]]
    non_prompt = [arg for arg in rendered if arg != prompt]
    ceiling = prompt_budget_utf16(
        transport=transport,
        non_prompt_argv=non_prompt,
        is_batch_shim=is_batch_shim,
    )
    if ceiling is None:
        return None
    units = utf16_units(prompt)
    if units <= ceiling:
        return None
    launcher_kind = (
        "a .cmd/.bat shim run via cmd.exe (8,191-unit command-line cap)"
        if is_batch_shim
        else "a native executable (32,767-unit CreateProcess cap)"
    )
    return (
        f"its prompt is {units} UTF-16 code units but {provider.name} delivers "
        f"the prompt on argv through {launcher_kind}, where this platform allows "
        f"{ceiling}. Configure a runner with a stdin/file prompt transport "
        f"(driver.subagent_runner). The prompt is never truncated. Nothing was "
        f"dispatched."
    )


def _apply_backoff_hook(delay: float) -> float:
    """Apply the ``MULTI_LLM_TEST_FAST_BACKOFF`` switch to a computed delay.

    The rung-3 arithmetic and its jitter belong to
    :func:`utils.retry_ladder.backoff_delay` — "equal jitter", half the
    exponential step deterministic and half random, so the N sibling tasks a
    shared provider throttled at the same moment never re-attempt in lockstep
    and re-trip the same limit together. That function is **pure**, which is the
    point: it reads no environment and keeps no import of this package, so the
    test switch cannot live inside it.

    It lives here instead, wrapping the delay at the one place this lane really
    sleeps. ``get_backoff_delay`` returns its argument unchanged outside
    ``MULTI_LLM_TEST_FAST_BACKOFF`` and an exact 10 ms under it — a jittered test
    suite would be both slower and nondeterministic.
    """
    try:
        from .review_orchestrator_base import get_backoff_delay
    except ImportError:  # pragma: no cover
        from utils.review_orchestrator_base import get_backoff_delay
    return get_backoff_delay(delay)


def _safe_parse_usage(provider: Any, capture: _Capture) -> Optional[Dict[str, Any]]:
    """``parse_usage`` that can never fail a dispatch (D3j)."""
    try:
        usage = provider.parse_usage(capture.stdout, capture.stderr)
    except Exception:  # noqa: BLE001 - metrics must not break the run
        return None
    if not isinstance(usage, dict) or not usage:
        return None
    return usage


def _notify_after_attempt(
    callback: Optional[Callable[[Attempt], None]], attempt: Attempt
) -> None:
    """Hand one recorded attempt to ``dispatch_task``'s observer (§5).

    An observer can never fail the attempt it observes: whatever it raises is
    reported on stderr and dropped, and the attempt loop carries on exactly as
    if no callback had been passed.
    """
    if callback is None:
        return
    try:
        callback(attempt)
    except Exception as exc:  # noqa: BLE001 - an observer never fails a dispatch
        print(
            f"multi-llm warning: after_attempt callback failed on attempt "
            f"{attempt.index} ({type(exc).__name__}: {exc})",
            file=sys.stderr,
        )


def _record_unspawned_attempt(
    outcome: TaskOutcome,
    attempt_index: int,
    error: str,
    after_attempt: Optional[Callable[[Attempt], None]],
) -> None:
    """Record a rejected attempt that ``before_attempt`` admitted but that
    spawned nothing (the step-3 backstop, or a rung refused for want of its
    grant).

    ``before_attempt`` has already written the audit's ``dispatched`` line by
    then, and the write scheduler's ``_audit_terminal`` closes that line only
    when ``outcome.attempts`` is non-empty — its early return reads an empty
    list as "refused before the first ``before_attempt``". Without this row the
    ``dispatched`` entry would stay open for good, breaking D3l's one line
    before dispatch, one line after. ``exit_code`` is ``None``: no child ran.
    """
    outcome.attempts.append(Attempt(
        index=attempt_index,
        status=STATUS_REJECTED,
        exit_code=None,
        duration_seconds=0.0,
        error=error,
    ))
    _notify_after_attempt(after_attempt, outcome.attempts[-1])


def _accumulate_usage(outcome: TaskOutcome, usage: Optional[Dict[str, Any]]) -> None:
    """Accumulate usage across every attempt of one ``task_id`` (D3j).

    A timed-out or rate-limited attempt still burned tokens, so it counts. Absent
    stays absent: a runner that reports nothing records duration only.
    """
    if not usage:
        return
    outcome.usage_reported = True
    totals = dict(outcome.usage or {})
    for key, value in usage.items():
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            totals[key] = totals.get(key, 0) + value
    outcome.usage = totals


def _classify_pre_parse(capture: _Capture) -> Tuple[str, str]:
    """Ladder rungs 1–2, decidable without parsing anything (D3k).

    ``STATUS_OK`` here means only "the child ran to completion"; rungs 3–6 need
    the parse result, because telling a rate limit from "no text at all" from
    "text with no result object" is exactly what the streams say.
    """
    if capture.launch_error is not None:
        return STATUS_SPAWN_FAILED, (
            f"could not start the runner: {capture.launch_error}. Either the CLI "
            f"is missing/not executable, or the host sandbox denied the spawn."
        )
    if capture.timed_out:
        return STATUS_TIMEOUT, (
            "the runner exceeded its per-task timeout and was killed; no partial "
            "result file exists (executor writes are atomic)"
        )
    return STATUS_OK, ""


def _reply_text(provider: Any, stdout: str) -> Optional[str]:
    """The runner's own reply text, or ``None`` when there is none to quote.

    The adapter's :meth:`salvage_text` when it has an opinion (the assistant's
    own words, never tool output or event framing); else the ``result`` string
    of a one-object result envelope; else the stream itself, which for a CLI
    that prints its answer as plain text is the reply. Never raises.
    """
    try:
        text = provider.salvage_text(stdout or "")
    except Exception:  # noqa: BLE001 - a diagnosis must never fail a dispatch
        text = None
    if isinstance(text, str):
        return text if text.strip() else None
    body = (stdout or "").strip()
    if body.startswith("{"):
        try:
            envelope = json.loads(body)
        except json.JSONDecodeError:
            envelope = None
        if isinstance(envelope, dict) and isinstance(envelope.get("result"), str):
            return envelope["result"] if envelope["result"].strip() else None
    return body or None


def _parse_and_validate(
    provider: Any,
    capture: _Capture,
    *,
    kind: str,
    prefer_arrays: bool,
    failure: Optional[str] = None,
) -> Tuple[str, str, Any]:
    """Ladder rungs 4–6, plus the two ways a salvage answers with no answer.

    Returns ``(status, error, data)``. Every caller persists ``data`` only on
    ``STATUS_OK``, which is what makes this the place to recognise a salvage that
    recovered nothing: :func:`_salvage_gave_up` runs between extraction and
    validation, so both the ``salvage_failed`` sentinel and a reply that is not
    answer-shaped at all — the provider error a subagent faithfully pulled out of
    a truncated stream — leave here as failures, and no invented review is ever
    written over the model's result file. Its status is not a rung — the
    dispatch itself worked (see ``STATUS_SALVAGE_UNRECOVERABLE``) — and it is in
    none of the ladder's policy sets, so ``record()`` files it under "never
    retried": the same raw output through the same prompt has the same answer.
    """
    try:
        data, fragment = _extract_result_and_syntax(
            provider, capture.stdout, capture.stderr, prefer_arrays=prefer_arrays,
            kind=kind,
        )
    except ResultRejected as exc:
        return exc.status, exc.message, None
    gave_up = _salvage_gave_up(kind, data, failure)
    if gave_up is not None:
        return STATUS_SALVAGE_UNRECOVERABLE, gave_up, data
    _report_normalized(
        kind, normalize_result(kind, data), supply_result_version(kind, data))
    errors = validate_result(kind, data)
    if errors:
        syntax = _redact(describe_syntax_error(fragment)) if fragment else None
        capture.reply_syntax_error = syntax
        if syntax:
            # The errors are the fragment's, not the reply's: say so first
            # (2026-10-05, a task-generation reply with the right keys was
            # reported "missing schema_version" over one unescaped quote).
            return (
                STATUS_SCHEMA_INVALID,
                f"the reply is not valid JSON ({syntax}); only a fragment of "
                f"it could be read, and that fragment does not match the "
                f"{kind} result shape: " + "; ".join(errors[:5]),
                data,
            )
        return (
            STATUS_SCHEMA_INVALID,
            f"the extracted result does not match the {kind} result shape: "
            + "; ".join(errors[:5]),
            data,
        )
    return STATUS_OK, "", data


def _parse_with_schema_policy(
    provider: Any,
    capture: _Capture,
    *,
    kind: str,
    prefer_arrays: bool,
    schema: Optional[Any] = None,
    schema_phase: str = "",
    model: str = "",
    declined_marker: Optional[str] = None,
    failure: Optional[str] = None,
) -> Tuple[str, str, Any, Optional[str]]:
    """:func:`_parse_and_validate` plus §4.2.1, when a schema was really carried.

    Returns ``(status, error, data, marker)``. ``marker`` is set **only** when a
    document was produced, so a report row never claims a path for a dispatch
    that produced nothing.

    ``schema=None`` — every kind with no schema phase, and every adapter that
    declined the flag — returns exactly what :func:`_parse_and_validate` returns,
    so this lane is byte-identical to its pre-M7 self and nothing new can fail a
    dispatch. ``declined_marker`` is what ``schema_for_dispatch`` already decided
    for the declining half of that case (``recovered``/``unvalidated``, never
    ``native``) and is ``None`` for a kind that resolved no phase at all — which
    is why such a kind's report row grows no key.

    With a schema, ``structured_output.classify_attempt`` (the one policy object
    both lanes share) reads the captured streams and its verdict is translated
    into D3k rungs:

    * a **configuration error** — the CLI refused the schema *before making any
      request* — is rung 7 (``rejected``): never retried, nothing billed. It
      must not be allowed to land on rungs 4/5, which **are** retried: re-running
      a refusal that made zero requests spends the transport budget on an
      identical failure and reports it as if it were transient.
    * the CLI's **own exhausted structured-output budget**
      (``error_max_structured_output_retries``) is rung 6 (``schema_invalid``):
      never retried here, because the CLI already spent the budget §4.2.1
      pinned, and rung 6 is this lane's existing "deterministic disagreement"
      rung.
    * ``structured_output`` **present and conformant** is the answer. It is taken
      as the result rather than re-derived from prose, and still passes through
      the kind's own :func:`validate_result` — the CLI validates client-side, so
      a disagreement here should be unreachable and is treated as case 2's
      failure rather than trusted.
    * anything else falls through to **this lane's own** extraction, which *is*
      §4.2.1 case 2 performed against the same schema file:
      :func:`validate_result` resolves to the file ``PHASE_SCHEMA_FILE`` names
      for exactly the kinds :data:`SCHEMA_PHASE_BY_KIND` lists. It is preferred
      over ``classify_attempt``'s own recovery because it runs the mandatory
      ``parse_output``-before-extraction ordering (D3) and the kind's own
      ``prefer_arrays``, neither of which a lane-agnostic policy function can
      know — and because failing a document *this* extractor would have accepted
      would be a regression dressed as a policy. Fail-closed is preserved
      either way: a document that does not validate is rung 5/6 exactly as
      before, so exit 0 is never on its own a success for a schema-carrying
      dispatch.
    """
    if schema is None:
        status, error, data = _parse_and_validate(
            provider, capture, kind=kind, prefer_arrays=prefer_arrays,
            failure=failure,
        )
        return (
            status, error, data,
            declined_marker if status == STATUS_OK else None,
        )

    # The native document is completed before it is validated, as this lane's
    # own parse is: a reply that left out a required-but-nullable key is
    # native, not "present but did not validate" (fix round 8).
    native_notes: List[str] = []
    verdict = structured_output.classify_attempt(
        schema,
        stdout=capture.stdout,
        stderr=capture.stderr,
        exit_code=capture.exit_code,
        phase=schema_phase,
        model=model,
        native_document=structured_output.native_document_for(
            provider, capture.stdout
        ),
        normalize=lambda document: native_notes.extend(
            normalize_result(kind, document)
        ),
    )
    if verdict.warning:
        print(f"[WARN] {verdict.warning}", file=sys.stderr)
    if verdict.failure_reason == structured_output.FAILURE_CONFIG_ERROR:
        return STATUS_REJECTED, verdict.warning or (
            f"structured output: the CLI refused {schema.name}"
        ), None, None
    if (
        verdict.failure_reason == structured_output.FAILURE_SCHEMA_VIOLATION
        and not verdict.retryable
    ):
        return STATUS_SCHEMA_INVALID, verdict.warning or (
            f"structured output: no document conforming to {schema.name}"
        ), None, None
    if verdict.marker == structured_output.MARKER_NATIVE and verdict.data is not None:
        _report_normalized(kind, native_notes + normalize_result(kind, verdict.data))
        errors = validate_result(kind, verdict.data)
        if errors:
            return (
                STATUS_SCHEMA_INVALID,
                f"the CLI's own structured_output does not match the {kind} "
                f"result shape: " + "; ".join(errors[:5]),
                verdict.data,
                None,
            )
        return STATUS_OK, "", verdict.data, structured_output.MARKER_NATIVE

    status, error, data = _parse_and_validate(
        provider, capture, kind=kind, prefer_arrays=prefer_arrays,
        failure=failure,
    )
    if status == STATUS_OK:
        if not verdict.warning:
            # §4.2.1 wants one WARN whenever a document was recovered rather than
            # handed over natively. `classify_attempt` prints its own when *its*
            # recovery succeeded; this covers the case where only this lane's
            # extractor got there, so a recovered result always says so.
            print(
                f"[WARN] structured output: no `structured_output` key "
                f"({schema_phase} {model}); the document was recovered from the "
                f"reply and validated against {schema.name}. Marked "
                f"'{structured_output.MARKER_RECOVERED}'.",
                file=sys.stderr,
            )
        return status, error, data, structured_output.MARKER_RECOVERED
    return status, error, data, None


#: The cap on the text a forwarded verdict quotes (§4.5.3's exit-3 sink).
_VERDICT_QUOTE_CHARS = 2000
#: How much of that window sits before the matched text: enough to show what
#: led up to it, with the rest of the window after it.
_VERDICT_QUOTE_LEAD = 400


def _redact_tracking(text: str, offset: int) -> Tuple[str, int]:
    """``_redact(text)`` plus where ``offset`` lands in the redacted text.

    The redacted text is always :func:`_redact` of the **unmodified** stream:
    nothing is inserted into it to carry the position, because any inserted
    character can split a credential so that no redaction pattern recognizes it
    (a marker inserted into the middle of a bearer-token credential left the
    part after the marker unredacted). The position is carried alongside instead, by
    replaying ``write_safety``'s own passes and shifting it by each
    replacement's length change; an offset inside a redacted span moves to the
    span's start. Should the replay ever disagree with :func:`_redact`, the
    position falls back to the redacted length of the prefix — the returned
    text is still the canonical redaction, so only the window's placement can
    be off, never what it contains.
    """
    redacted = _redact(text)
    offset = min(max(0, offset), len(text))
    try:
        try:  # pragma: no cover - import shim mirrors the rest of utils/
            from .write_safety import _REDACTIONS, _replace_group
        except ImportError:  # pragma: no cover - direct-script import shim
            from utils.write_safety import _REDACTIONS, _replace_group
        out, pos = text or "", offset
        if out:
            for _name, pattern, group, predicate in _REDACTIONS:
                pieces: List[str] = []
                last = 0
                new_pos = pos
                for m in pattern.finditer(out):
                    if predicate is not None and not predicate(m.group(group)):
                        continue
                    repl = _replace_group(m, group, _name)
                    start, end = m.span()
                    pieces.append(out[last:start])
                    pieces.append(repl)
                    last = end
                    if end <= pos:
                        new_pos += len(repl) - (end - start)
                    elif start < pos:
                        new_pos -= pos - start
                pieces.append(out[last:])
                out, pos = "".join(pieces), new_pos
        if out == redacted:
            return redacted, min(max(0, pos), len(redacted))
    except Exception:  # noqa: BLE001 - the quote must never raise
        pass
    return redacted, min(len(_redact(text[:offset])), len(redacted))


def _unlowered_offset(text: str, lowered_offset: int) -> int:
    """Map an index into ``text.lower()`` back to an index into ``text``.

    :func:`match_streams` reports offsets into the channel's lowered text, and
    ``str.lower()`` is not length-preserving for every character (U+0130
    lowers to two code points), so the raw offset can drift from the original
    stream. Lowering is applied per character here, which sums to the same
    length as lowering the whole string; an offset that lands inside one
    character's expansion maps to that character.
    """
    lowered_offset = max(0, lowered_offset)
    if len(text.lower()) == len(text):
        return min(lowered_offset, len(text))
    consumed = 0
    for index, char in enumerate(text):
        width = len(char.lower())
        if consumed + width > lowered_offset:
            return index
        consumed += width
    return len(text)


def _quote_verdict(
    provider: Any, stdout: str, stderr: str, exit_code: int, classified: str
) -> str:
    """The redacted text around what decided ``classified`` (T2.5).

    The verdict is ``provider.classify_failure``'s and nothing here changes it.
    ``stdout``/``stderr`` arrive already reduced by the adapter's own
    ``vendor_text`` — applied by :func:`_classify_failed_run`, the one
    permitted second application of that hook, see its docstring — and
    :func:`match_streams` re-scans the reduced text with the adapter's
    declared tables, for the quote only. When the re-scan lands on the same status
    with a pattern, the quote is the window around that match on the channel
    it matched; otherwise (an adapter's structural override decided a verdict
    no pattern produced, or the re-scan found another status) it is the head of
    the reduced ``stdout + "\n" + stderr``, never a pattern match that did not
    decide the verdict.

    Before this, the quote was ``stderr or stdout``: run b38de8bb recorded
    ``rate_limited`` off a ``rate limit`` in opencode's stdout and quoted a
    stderr line that said nothing of the kind.

    Redaction runs on the whole reduced channel **before** the window is cut,
    for the reason ``_redact`` gives; the match position is carried beside it by
    :func:`_redact_tracking`, never by a character inserted into the stream.
    """
    try:  # pragma: no cover - import shim mirrors the rest of utils/
        from .providers.base import match_streams
    except ImportError:  # pragma: no cover - direct-script import shim
        from utils.providers.base import match_streams

    match = None
    try:
        match = match_streams(
            stdout or "",
            stderr or "",
            exit_code or 0,
            auth_patterns=getattr(provider, "auth_error_patterns", None),
            rate_limit_patterns=getattr(provider, "rate_limit_patterns", None),
            exit_zero_markers=getattr(provider, "exit_zero_failure_markers", ()),
        )
    except Exception:  # noqa: BLE001 - the quote must never raise
        match = None
    stdout, stderr = stdout or "", stderr or ""
    if (
        match is not None and match.status == classified
        and match.pattern is not None and match.offset is not None
    ):
        text = stdout if match.channel == "stdout" else stderr
        offset = _unlowered_offset(text, match.offset)
        redacted, at = _redact_tracking(text, offset)
        if len(redacted) <= _VERDICT_QUOTE_CHARS:
            return redacted
        start = max(0, at - _VERDICT_QUOTE_LEAD)
        start = min(start, len(redacted) - _VERDICT_QUOTE_CHARS)
        return redacted[start:start + _VERDICT_QUOTE_CHARS]
    head = stdout if not stderr else (f"{stdout}\n{stderr}" if stdout else stderr)
    return _redact(head)[:_VERDICT_QUOTE_CHARS]


def _classify_failed_run(
    provider: Any, capture: _Capture, model: str = ""
) -> Optional[Tuple[str, str]]:
    """Ladder rung 3, plus the two rung-1 verdicts (auth, invalid model) and the
    rung-less ``context_length_exceeded``, consulted only for a run with no
    result.

    Classification lives in the adapter — it is the only layer that knows the
    provider's error shape — and is deliberately **not** consulted for a run that
    produced a schema-valid result: the patterns match on captured streams, and a
    successful answer routinely quotes plan text containing "rate limit" or
    "unauthorized".

    Of the five ``CATEGORY_*`` names the ladder has no rung for, exactly two are
    mapped here — ``invalid_model`` (D4) and ``sandbox_unavailable`` (D6) —
    because a rejected id is a property of the spec and a sandbox that cannot
    start is a property of the machine, so the batch-wide fatal gate is
    telling the truth about every sibling on it. ``connection_error`` and ``server_error`` fall through to the
    parse failure's own retryable status, which is the policy the classifier's
    table asks for; ``permission_denied`` can fail one task and not its
    neighbour, so a fatal mapping would be this function's complaint pointed
    the other way. They return ``None`` on purpose.

    One more verdict is forwarded, and it is not a pattern verdict: an
    adapter's ``classify_structural`` ``runner_error`` (opencode's turn ended
    by an auto-rejected permission, §4.2 step 4), with the adapter's own reason
    sentence. It is asked only when the pattern verdict is none of the above.

    The forwarded pattern verdicts quote the text that decided them
    (:func:`_quote_verdict`), not ``stderr or stdout``.
    """
    # §7.6(a)'s terminal status is the ladder's, imported here rather than
    # redeclared: `retry_ladder` owns the status vocabulary and this module
    # re-exports it. Function-local because the constants block above is being
    # converted to re-exports in the same window.
    try:  # pragma: no cover - import shim mirrors the rest of utils/
        from .retry_ladder import STATUS_CONTEXT_LENGTH_EXCEEDED
    except ImportError:  # pragma: no cover - direct-script import shim
        from utils.retry_ladder import STATUS_CONTEXT_LENGTH_EXCEEDED

    try:
        classified = provider.classify_failure(
            capture.stdout, capture.stderr, capture.exit_code or 0
        )
    except Exception:  # noqa: BLE001 - classification must not raise
        return None
    # §4.5.3's fourth sink: this reason is printed by the exit-3 block, which is
    # `orchestrator-run.log` under `--detach`, and is also stored in
    # `subagent_batch_report.json`. Redaction runs on the full stream **before**
    # the 2 KB tail — an auth failure is precisely the run whose stream quotes a
    # credential back, and tailing first would keep the value and drop the key
    # name that makes it matchable.
    if classified == STATUS_CONTEXT_LENGTH_EXCEEDED:
        # Terminal, and NOT a rung: it is in none of RETRYABLE/BACKOFF/FATAL, so
        # the dispatch loop below falls through to its final `break` and the slot
        # ends after exactly one attempt. §7.6(a) is explicit that this is the
        # shipping behaviour until open question 13 designs a prompt splitter —
        # re-sending an unchanged oversized prompt is the one retry guaranteed to
        # fail identically, and a rung-down would only spend the budget doing it.
        try:  # pragma: no cover - import shim mirrors the rest of utils/
            from .providers.base import context_length_message
        except ImportError:  # pragma: no cover - direct-script import shim
            from utils.providers.base import context_length_message
        return STATUS_CONTEXT_LENGTH_EXCEEDED, context_length_message(model)
    if classified == STATUS_BUDGET_EXHAUSTED:
        # The provider already consumed its internal step budget. Repeating
        # the same prompt would silently grant a fresh budget to the same run.
        return STATUS_BUDGET_EXHAUSTED, "the provider exhausted its internal step budget"
    if classified not in (
        STATUS_AUTH_FAILED, STATUS_RATE_LIMITED, STATUS_INVALID_MODEL,
        STATUS_SANDBOX_UNAVAILABLE,
    ):
        # §4.2 step 4 (T4.3): a verdict the adapter reads off the stream's
        # SHAPE, with its own reason — opencode's turn ended by an auto-rejected
        # permission. It is consulted only here, after every forwarded pattern
        # verdict above had its chance, so a genuine vendor 429 or auth error
        # in the same stream still wins; and ahead of everything else, so the
        # attempt is recorded `runner_error` with the permission sentence rather
        # than `unparseable` with "No text events found in output". Its reason
        # is the adapter's own sentence, so the matched-pattern quote below
        # never applies to it.
        structural = getattr(provider, "classify_structural", None)
        if structural is None:
            return None
        try:
            found = structural(
                capture.stdout, capture.stderr, capture.exit_code or 0
            )
        except Exception:  # noqa: BLE001 - classification must not raise
            return None
        if (
            isinstance(found, tuple) and len(found) == 2
            and found[0] == STATUS_RUNNER_ERROR and found[1]
        ):
            return STATUS_RUNNER_ERROR, _redact(str(found[1]))
        return None
    # T2.5: the quote is cut from the VENDOR-reduced capture, around the text
    # that decided the verdict. This is the one application of `vendor_text`
    # outside `classify_failure` (its docstring names both), and it is for the
    # quote only: the verdict above is already decided and nothing below moves
    # it. A reduction that raises quotes the capture as it came.
    reduced_out, reduced_err = capture.stdout or "", capture.stderr or ""
    if getattr(provider, "vendor_text", None) is not None:
        try:
            reduced_out, reduced_err = provider.vendor_text(
                reduced_out, reduced_err
            )
        except Exception:  # noqa: BLE001 - the quote must never raise
            reduced_out, reduced_err = capture.stdout or "", capture.stderr or ""
    tail = _quote_verdict(
        provider, reduced_out, reduced_err, capture.exit_code or 0, classified
    )
    if classified == STATUS_SANDBOX_UNAVAILABLE:
        # D6 step 4. `STATUS_SANDBOX_UNAVAILABLE` *is* the classifier's
        # `CATEGORY_SANDBOX_UNAVAILABLE` string, on D4's pattern. The stream
        # tail carries the `bwrap:` line itself, which is the one thing the
        # reader needs to recognise the machine condition `doctor` repairs.
        return STATUS_SANDBOX_UNAVAILABLE, (
            f"the runner's own sandbox could not start — "
            f"{_REASON_EXPLANATION['sandbox_unavailable']} (a property of the "
            f"machine, never fixed by a retry). Stream tail: {tail!r}"
        )
    if classified == STATUS_INVALID_MODEL:
        # D4 step 2. `STATUS_INVALID_MODEL` *is* the classifier's
        # `CATEGORY_INVALID_MODEL` string, so this is the category under its own
        # name. The verdict ends in the redacted stream tail on purpose: that is
        # how the provider's "Did you mean" line reaches the log and the report,
        # and it is what replaces the adapter's composed text on the exit-3 line
        # (`status, error = reclassified` in `dispatch_task`) — never appended
        # to it, never deduplicated against it.
        provider_name = str(getattr(provider, "name", "") or "")
        spec = f"{provider_name}:{model}" if model else provider_name or "(unknown)"
        return STATUS_INVALID_MODEL, (
            f"the runner rejected the model id {spec!r} (the fix is a config "
            f"edit, never a retry). Stream tail: {tail!r}"
        )
    if classified == STATUS_AUTH_FAILED:
        return STATUS_AUTH_FAILED, (
            f"the runner is installed but not authenticated (it printed a "
            f"login/credential notice). No retry can fix this and every sibling "
            f"task would fail identically, so the whole batch fails. Stream tail: "
            f"{tail!r}"
        )
    if classified == STATUS_RATE_LIMITED:
        return STATUS_RATE_LIMITED, (
            f"the provider reported a rate limit / quota / overloaded condition. "
            f"Stream tail: {tail!r}"
        )
    return None


# ---------------------------------------------------------------------------
# Batch orchestration
# ---------------------------------------------------------------------------

def _preflight_batch_runners(
    resolved: Dict[str, Tuple[str, str, str]],
    task_by_id: Dict[str, Dict[str, Any]],
    *,
    profile: str,
    anchor: Optional[str] = None,
    recorded: Optional[Dict[str, str]] = None,
    jail_request: Optional[JailRequest] = None,
) -> Tuple[Dict[str, str], Optional[Dict[str, str]]]:
    """Preflight each DISTINCT runner once; return its versions and any fallback.

    Presence, profile, version, auth, the CLI's own catalog and the host's
    nested-exec verdict, paid once per spec rather than once per task. A refusal
    is exit 3 before any child is dispatched, and it names the layer that
    supplied the spec — the first task's source for each distinct spec — rather
    than a ``driver.*`` key the user may never have written (D3 step 3).

    **One rung is allowed to fall through, and only one**: ``session``. That spec
    is the model the host session happens to be running on — nobody typed it into
    a config file, so a refusal is not a config error and refusing the batch over
    it would make "I switched the session model" a way to break a run that worked
    a minute ago. Whatever the reason code (``invalid_model_catalog``,
    ``not_authenticated``, a denied ``nested_exec`` leg, ``sandbox_unavailable``
    …), every task that was going to run on it is re-resolved with the session
    rung skipped, one line says so on stdout, and the *next* rung is preflighted
    under the ordinary rule. Explicit layers keep refusing exactly as before: an
    opinion an operator really expressed and that cannot be served is a config
    error, and silently substituting something else is how "I set it and nothing
    changed" begins.

    ``resolved`` is mutated in place, so the caller's runner map is the map the
    fallback produced.

    ``jail_request`` (plan codex-sandbox-unavailable step 3, 2026-09-30) is a
    write batch's grant, handed to every preflight so the sandbox leg decides
    for that scope; a read batch passes none.

    Returns:
        ``({spec: version}, fallback)`` where *fallback* is ``None`` or
        ``{"from", "reason", "to", "layer"}`` — the record
        ``subagent_batch_report.json`` carries so a substitution is visible after
        the fact. Per-task truth stays in ``tasks[].runner``; this names the
        first substitution, which in a homogeneous batch is the only one.
    """
    versions: Dict[str, str] = {}
    fallback: Optional[Dict[str, str]] = None
    while True:
        sources: Dict[str, Tuple[str, str, str]] = {}
        for task_id, (spec, key, layer) in resolved.items():
            sources.setdefault(spec, (task_id, key, layer))
        pending = [
            (spec, meta) for spec, meta in sources.items() if spec not in versions
        ]
        if not pending:
            return versions, fallback
        spec, (task_id, key, layer) = pending[0]
        try:
            versions[spec] = preflight_runner(
                spec, profile=profile, anchor=anchor, key=key, layer=layer,
                **({"jail_request": jail_request} if jail_request is not None else {}),
            )["version"]
            continue
        except RunnerRejected as exc:
            if layer != SESSION_LAYER:
                raise
            # Bound out of the `except` block, which deletes `exc` on the way
            # out: the refusal has to survive to the impossible-branch re-raise.
            rejection, reason = exc, exc.reason_code or STATUS_REJECTED
        # Re-resolve every task that was going to run on the refused spec, each
        # through its own tier, so a `cheap` task lands on the cheap rung rather
        # than on whatever the first task got.
        replacement: Optional[Tuple[str, str, str]] = None
        for other_id, source in list(resolved.items()):
            if source[0] != spec:
                continue
            new_source = _resolve_task_source(
                task_by_id[other_id], anchor=anchor, recorded=recorded,
                skip_session=True,
            )
            resolved[other_id] = new_source
            if replacement is None:
                replacement = new_source
        if replacement is None:  # pragma: no cover - spec came from `resolved`
            raise rejection
        print(
            f"[exec-subagents] session model {spec} failed preflight "
            f"({reason}); falling back to {replacement[0]} ({replacement[2]})"
        )
        if fallback is None:
            fallback = {
                "from": spec,
                "reason": reason,
                "to": replacement[0],
                "layer": replacement[2],
            }


def _estimated_cost(task: Dict[str, Any]) -> int:
    """How expensive this task looks *before* it runs, for dispatch order only.

    The prompt's length is the whole of it. A subagent turn is dominated by the
    tokens the runner has to read and reason over, and for every materialized
    kind the prompt is where those tokens are: a validation batch's prompt
    carries its grouped suggestions inline, an implement task's carries its step.
    Nothing here reads the clock or the provider, so the estimate is free, stable
    across resumes and identical on every host.

    ``groups_count`` is the fallback for a task whose prompt is absent or
    non-textual — a coarser proxy for the same quantity — and ``0`` (dispatch it
    last, order unchanged among its peers) when neither says anything. This is a
    *ranking*, never a prediction: it is wrong only by mis-ordering a batch that
    would otherwise have been ordered by an accident of file position.
    """
    prompt = task.get("prompt")
    if isinstance(prompt, str) and prompt:
        return len(prompt)
    groups = task.get("groups_count")
    if isinstance(groups, int) and not isinstance(groups, bool) and groups > 0:
        return groups
    return 0


def _dispatch_order(tasks: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """The same tasks, longest-first, for **dispatch scheduling only** (D3i).

    Longest-processing-time-first is the classic answer to the tail this fixes.
    The batch runs as ``ceil(tasks / parallelism)`` waves, so whatever is
    dispatched last runs with the lanes beside it emptying out; dispatch in file
    order and the last task in the file gets that slot no matter how big it is.
    The 2026-09-13 review-plan run is the worked example: eleven validation
    batches at parallelism 4, per-batch 237/960/1123/895/671/811/610/486/478/545/
    1076 s, ideal packing 1973 s, actual 2594 s — the 621 s gap is almost exactly
    batch 10 (1076 s) running alone at the end because it happened to be last in
    ``validation_tasks.json``. Dispatching it first puts it in the first wave,
    where three lanes run beside it.

    **Only the dispatch order changes.** Task ids, ``batch_index``,
    ``output_path``, the merge, and ``tasks[]`` in ``subagent_batch_report.json``
    all keep the task file's own order — :func:`run_tasks` re-indexes the
    outcomes by ``task_id`` against its original ``selected`` list, so this
    function's return value never reaches an artifact. The tie-break is the
    original index, so a batch whose tasks all estimate the same (or that has one
    task) is dispatched in exactly the order it always was.
    """
    ordered = sorted(
        enumerate(tasks), key=lambda row: (-_estimated_cost(row[1]), row[0])
    )
    if [index for index, _ in ordered] != list(range(len(tasks))):
        print(
            "[exec-subagents] dispatch order (longest first): "
            + ", ".join(
                str(task.get("task_id", index)) for index, task in ordered
            )
        )
    return [task for _index, task in ordered]


#: The suffix :func:`_resolve_task_source` puts on a runner a previous attempt
#: of the same task recorded.
_RECORDED_RUNNER_SUFFIX = "(recorded from a previous attempt)"

#: Row statuses whose recorded runner is not a pin for a re-run (fix round 8):
#: the reply-quality failures, rungs 5 and 6. See :func:`_recorded_runners`.
UNPINNED_ROW_STATUSES = frozenset({STATUS_SCHEMA_INVALID, STATUS_UNPARSEABLE})


def _pinned_runner_note(key: str, kind: str = "") -> str:
    """The dispatch line's reason when the runner is a recorded pin, else ``""``.

    A pin outranks every rung of the ladder — the session model and
    ``driver.subagent_runner`` included — so without this the line named a
    runner the user had just tried to move away from and gave no reason
    (2026-10-05, run 3: generate-tasks re-run after a host-model switch stayed
    on ``opencode/big-pickle``, the runner its failed first run recorded).
    The file it names is the one :func:`_recorded_runners` read for ``kind``
    (the judge's is kind-qualified, :func:`_batch_report_filename`).
    """
    if not key.endswith(_RECORDED_RUNNER_SUFFIX):
        return ""
    return (
        "; the runner this task's earlier attempt used, kept from "
        f"{_batch_report_filename(kind)} so a re-run repeats it — the session "
        "model and driver.subagent_runner do not change it"
    )


def run_tasks(
    tasks: Sequence[Dict[str, Any]],
    *,
    phase_dir: str,
    phase: str = "",
    kind: str = "",
    task_file: Optional[str] = None,
    anchor: Optional[str] = None,
    cwd: Optional[str] = None,
    host_max: Optional[int] = None,
    resume: bool = True,
    only_task_ids: Optional[Iterable[str]] = None,
    write_report: bool = True,
) -> BatchReport:
    """Dispatch a materialized batch and return its report (D3i).

    Runners are resolved **once per task at batch start** and pinned into the
    report, so a re-dispatch under ``--resume`` or ``--retry-failed-subagents``
    uses the runner the first attempt did rather than re-resolving against a
    config that may have changed mid-run — except a task whose attempt failed
    fatally or on its reply's shape (:func:`_recorded_runners`). The effective
    ceilings are logged once
    at batch start alongside each task's runner, so a slow batch is diagnosable
    from the log rather than inferred.

    Tasks are *dispatched* longest-first (:func:`_dispatch_order`) so the biggest
    one never runs alone in the final wave. Everything the caller can observe
    stays in the task file's order: ``report.outcomes`` below is rebuilt by
    walking ``selected``, so ``tasks[]`` in the report, the merge that reads it
    and the per-task runner listing on stdout are all in the order the tasks were
    materialized.
    """
    selected = list(tasks)
    if only_task_ids is not None:
        wanted = set(only_task_ids)
        selected = [t for t in selected if str(t.get("task_id", "")) in wanted]

    report = BatchReport(
        phase=phase, kind=kind, phase_dir=phase_dir, task_file=task_file,
    )
    if not selected:
        report.ceilings = {"effective": 0}
        if write_report:
            report.write()
        return report

    pin_sha256 = _pin_sha256(tasks)
    report.pin_sha256 = pin_sha256
    recorded = _recorded_runners(phase_dir, kind, pin_sha256=pin_sha256)
    # §7.3a: read before this dispatch overwrites the report, so a resumed
    # (skipped) task keeps the provenance its original dispatch recorded.
    previous_provenance = _recorded_provenance(phase_dir, kind) or {}
    task_by_id: Dict[str, Dict[str, Any]] = {
        str(task.get("task_id", index)): task
        for index, task in enumerate(selected)
    }
    resolved = {
        task_id: _resolve_task_source(task, anchor=anchor, recorded=recorded)
        for task_id, task in task_by_id.items()
    }

    profile = profile_for_kind(str(selected[0].get("kind") or kind))
    versions, fallback = _preflight_batch_runners(
        resolved, task_by_id, profile=profile, anchor=anchor, recorded=recorded,
    )
    report.runner_versions.update(versions)
    report.runner_fallback = fallback
    runners = {task_id: spec for task_id, (spec, _key, _layer) in resolved.items()}

    report.ceilings = effective_ceiling(
        list(runners.values()), anchor=anchor, host_max=host_max
    )
    print(
        f"[exec-subagents] {len(selected)} task(s), effective parallelism "
        f"{report.ceilings['effective']} "
        f"(driver={report.ceilings['driver_max_concurrent_subagents']}, "
        f"host={report.ceilings['host_max_concurrent_subagents']}, "
        f"provider={report.ceilings['provider_max_concurrent']})"
    )
    # Listed in the task file's own order — this is the batch's runner map, not
    # its schedule, and a reader matching it against `validation_tasks.json` or
    # against `tasks[]` in the report must find the same sequence in all three.
    # The schedule is the separate line `_dispatch_order` prints when it differs.
    for task_id, spec in runners.items():
        version = report.runner_versions.get(spec, "unknown")
        print(
            f"[exec-subagents]   {task_id} -> {spec} (version {version}"
            f"{_pinned_runner_note(resolved[task_id][1], kind)})"
        )

    # D4a, the *during* half: a batch of eleven validation tasks ran for a
    # minute behind a status line that said nothing had started, because the
    # mirror below this call was the only one (measured 2026-09-16). Each
    # completion writes the counts so far against the batch's full size, so a
    # poll reads `validation 3/11 ok` while it is happening. Display only, and
    # deliberately not the batch report: that file is the batch's *record* and
    # stays a single write after the last task.
    finished: List[TaskOutcome] = []

    def task_finished(outcome: TaskOutcome) -> None:
        # Called from the dispatch loop's own event loop, one at a time, so the
        # list needs no lock; `update_status` holds the inter-process one.
        finished.append(outcome)
        _mirror_status(
            phase_dir, replace(report, outcomes=list(finished)),
            total=len(selected),
        )

    # Plan codex-sandbox-unavailable §6 F1 item 6 / Limits (2026-09-30): the
    # `[JAIL_DENIED]` and `[CODEX_HOME_CHECK]` lines this batch prints are
    # repeated at its close, because a home change outlives the run.
    jail_lines_before = jail_summary_count()
    outcomes = _run_sync(_gather(
        _dispatch_order(selected),
        runners=runners,
        phase_dir=phase_dir,
        anchor=anchor,
        cwd=cwd,
        max_parallel=report.ceilings["effective"],
        resume=resume,
        on_task_finished=task_finished,
    ))
    report.outcomes = [outcomes[str(t.get("task_id", i))]
                       for i, t in enumerate(selected)
                       if str(t.get("task_id", i)) in outcomes]

    # A task whose coroutine never returned (cancelled by the overall timeout) is
    # *incomplete*, not silently absent: it has no result file, so the batch must
    # not reaggregate.
    for index, task in enumerate(selected):
        task_id = str(task.get("task_id", index))
        if task_id in outcomes:
            continue
        report.outcomes.append(TaskOutcome(
            task_id=task_id,
            kind=str(task.get("kind", "")),
            runner=runners[task_id],
            status=STATUS_INCOMPLETE,
            reason=(
                "the dispatch did not complete (cancelled by the batch timeout or "
                "the run was killed); no result file exists"
            ),
        ))

    report.batch_provenance = _batch_provenance(
        report.outcomes, tasks, kind=kind, previous=previous_provenance,
    )

    if write_report:
        report.write()
    _mirror_status(phase_dir, report)
    for line in jail_summary_lines(jail_lines_before):
        print(f"[exec-subagents] closing summary: {line}")
    return report


def _batch_provenance(
    outcomes: Sequence[TaskOutcome],
    tasks: Sequence[Dict[str, Any]],
    *,
    kind: str,
    previous: Dict[str, Dict[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    """Per-output provenance for :attr:`BatchReport.batch_provenance` (§7.3a).

    A task this dispatch ran to a persisted result file records its runner and
    the sha256 of the file's bytes as they are now. A task it did *not* run —
    skipped under ``--resume``, or outside ``only_task_ids`` — keeps the row an
    earlier dispatch recorded, but only while that row is still true: same
    round, and the file's bytes still hash to the recorded value. Anything else
    records nothing, so the merge falls back to the batch's own
    ``metadata.model`` rather than crediting this executor with a file it never
    wrote.
    """
    try:
        from .subagent_tasks import file_bytes_sha256, task_round
    except ImportError:  # pragma: no cover
        from utils.subagent_tasks import file_bytes_sha256, task_round
    round_id = task_round(tasks)
    task_kinds = {
        str(task.get("task_id", index)): str(task.get("kind") or kind)
        for index, task in enumerate(tasks)
    }
    output_by_id: Dict[str, str] = {}
    provenance: Dict[str, Dict[str, Any]] = {}
    for outcome in outcomes:
        if outcome.ok and outcome.output_path:
            output_by_id[outcome.task_id] = outcome.output_path
        if not outcome.ok or outcome.skipped or not outcome.output_path:
            continue
        digest = file_bytes_sha256(outcome.output_path)
        if not digest:
            continue
        provenance[outcome.task_id] = {
            "task_id": outcome.task_id,
            "kind": outcome.kind or task_kinds.get(outcome.task_id, kind),
            "round": round_id,
            "runner": outcome.runner,
            "sha256": digest,
        }
    for task_id, row in previous.items():
        if task_id in provenance or not isinstance(row, dict):
            continue
        if task_id not in task_kinds or row.get("round") != round_id:
            continue
        path = output_by_id.get(task_id)
        if path is None:
            task = next(
                (t for i, t in enumerate(tasks)
                 if str(t.get("task_id", i)) == task_id),
                None,
            )
            path = task.get("output_path") if isinstance(task, dict) else None
        if path and row.get("sha256") and file_bytes_sha256(path) == row["sha256"]:
            provenance[task_id] = dict(row)
    return provenance


def _run_sync(coro):
    """Run ``coro`` to completion whether or not a loop is already running.

    :func:`run_tasks` is a **synchronous** façade on purpose — it is called from
    an async review orchestrator (`run_review_orchestration`), from a sync
    consolidation handler and from the sync apply base, and threading
    async/await through all three call chains would be a much larger change than
    the executor itself. Inside an existing loop the batch runs on a worker
    thread with its own loop; ``asyncio.run`` from within a running loop is a
    ``RuntimeError``, and the concurrency this schedules is subprocess work in
    threads either way.
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, coro).result()


class _ProviderBackpressure:
    """D3i's rate-limit backpressure, applied at the provider's in-flight slots.

    A 429 belongs to the *provider*, not to the task that happened to draw it:
    every sibling dispatched into the same limit will hit it too, burn its own
    (budget-free but bounded) rate-limit attempts and then fail. D3i's answer is
    to degrade the batch instead — "the executor narrows that provider's
    in-flight slots for the rest of the batch instead of failing sibling tasks".

    This is a *narrowing* gate, never a second dispatch pool: it is acquired
    inside ``run_tasks_concurrent``'s per-provider and global semaphores, so the
    effective concurrency is the minimum of the two layers and the D3i three-way
    ceiling still bounds the batch from above. Acquisition order is therefore the
    same for every task (provider semaphore → global semaphore → this gate) and a
    holder always already owns the outer two, so narrowing can queue tasks but
    cannot deadlock them.
    """

    #: A throttled provider is halved, never closed: one in-flight slot is the
    #: floor, because zero would strand the rest of the batch behind a provider
    #: whose only way back is a successful attempt.
    MIN_SLOTS = 1

    def __init__(self, limits: Dict[str, int]) -> None:
        self._limits = dict(limits)
        self._in_flight: Dict[str, int] = {}
        self._condition = asyncio.Condition()

    async def acquire(self, provider: str) -> None:
        if provider not in self._limits:
            return
        async with self._condition:
            while self._in_flight.get(provider, 0) >= self._limits[provider]:
                await self._condition.wait()
            self._in_flight[provider] = self._in_flight.get(provider, 0) + 1

    async def release(self, provider: str) -> None:
        if provider not in self._limits:
            return
        async with self._condition:
            self._in_flight[provider] = max(0, self._in_flight.get(provider, 0) - 1)
            self._condition.notify_all()

    def can_narrow(self, provider: str) -> bool:
        """Would :meth:`narrow` still change ``provider``'s slots right now?

        A snapshot for the event-loop thread (the only one that mutates the
        limits): it decides whether a dispatch needs the per-attempt narrowing
        hook at all, never whether a narrowing happens — :meth:`narrow` re-checks
        under the condition.
        """
        current = self._limits.get(provider)
        return current is not None and current > self.MIN_SLOTS

    async def narrow(self, provider: str) -> Optional[int]:
        """Halve ``provider``'s slots. Returns the new count, or ``None`` at the floor."""
        async with self._condition:
            current = self._limits.get(provider)
            if current is None or current <= self.MIN_SLOTS:
                return None
            self._limits[provider] = max(self.MIN_SLOTS, current // 2)
            # Nothing to wake: narrowing only ever removes capacity.
            return self._limits[provider]


def _saw_rate_limit(outcome: TaskOutcome) -> bool:
    """Did any attempt of this task draw a 429/quota response (D3i)?

    A task that was throttled and then *succeeded* on a later attempt still
    proves the provider is throttling this batch, so it narrows the slots too.
    """
    if outcome.status == STATUS_RATE_LIMITED:
        return True
    return any(attempt.status == STATUS_RATE_LIMITED for attempt in outcome.attempts)


def _narrow_on_rate_limited_attempt(
    backpressure: _ProviderBackpressure,
    provider: str,
    loop: asyncio.AbstractEventLoop,
    task_id: str,
    state: Dict[str, bool],
) -> Callable[[Attempt], None]:
    """The ``after_attempt`` hook that narrows ``provider`` on a 429 attempt (§5).

    ``dispatch_task`` runs under ``asyncio.to_thread``, so this fires on that
    worker thread, never on the event loop: ``loop`` is captured on the loop
    thread beforehand, and the narrowing is submitted to it with
    ``run_coroutine_threadsafe``. The hook never waits on that future — blocking
    here would stall the attempt loop, backoff sleep included — so the outcome
    is reported from the future's done-callback: the exception if ``narrow()``
    raised, otherwise the usual log line with the attempt number added.

    At most one narrowing per task: ``state["done"]`` is set before the
    submission, so it holds even when ``narrow()`` later fails, and the task
    wrapper's post-return check skips a task that already narrowed. Nothing in
    here may propagate into ``dispatch_task`` — every failure is logged and the
    attempt stands as recorded.
    """

    def report(future: Any, attempt_index: int) -> None:
        try:
            exc = future.exception()
            if exc is not None:
                print(
                    f"multi-llm warning: narrowing {provider} after a rate limit "
                    f"on {task_id} attempt {attempt_index} failed "
                    f"({type(exc).__name__}: {exc})",
                    file=sys.stderr,
                )
                return
            narrowed = future.result()
            if narrowed is not None:
                print(
                    f"[exec-subagents] {provider} reported a rate limit "
                    f"({task_id}, attempt {attempt_index}) — narrowing it to "
                    f"{narrowed} in-flight slot(s) for the rest of the batch"
                )
        except Exception as report_exc:  # noqa: BLE001 - reporting never raises
            print(
                f"multi-llm warning: narrowing {provider} after a rate limit on "
                f"{task_id}: {type(report_exc).__name__}: {report_exc}",
                file=sys.stderr,
            )

    def on_attempt(attempt: Attempt) -> None:
        try:
            if state["done"] or attempt.status != STATUS_RATE_LIMITED:
                return
            state["done"] = True
            coro = backpressure.narrow(provider)
            try:
                future = asyncio.run_coroutine_threadsafe(coro, loop)
            except BaseException:
                coro.close()  # never scheduled: no "never awaited" warning
                raise
            future.add_done_callback(
                lambda done, index=attempt.index: report(done, index)
            )
        except Exception as exc:  # noqa: BLE001 - an observer never fails a dispatch
            print(
                f"multi-llm warning: could not narrow {provider} after a rate "
                f"limit on {task_id} attempt {attempt.index} "
                f"({type(exc).__name__}: {exc})",
                file=sys.stderr,
            )

    return on_attempt


def _judge_dispatch_argv_preview(
    runner: str, prompt: str, profile: str, anchor: Optional[str]
) -> List[str]:
    """A best-effort argv for the F6 audit line — never the real dispatch's own.

    Mirrors ``write_batch_scheduler._render_argv``: the provider's own command
    builder, called directly and never executed. Deliberately not
    :func:`_preview_argv` (the ``--dry-run-subagents`` renderer), which enters
    the full dispatch context and materializes a schema sidecar per call — a
    judge task carries no schema, so that machinery would only double the
    per-attempt setup this hook runs beside for no more accurate an argv. A
    render failure falls back to naming the runner: an audit hook must never
    fail the dispatch it is watching.
    """
    provider_name, model = parse_model_spec(runner, anchor=anchor)
    provider = get_provider(provider_name)
    if provider is None:
        return [runner]
    try:
        return list(provider.build_agent_command(prompt, model, profile))
    except Exception:  # noqa: BLE001 - an audit preview must never fail a dispatch
        return [provider_name, "<profile unsupported>"]


def _judge_audit_before_attempt(
    phase_dir: str, anchor: Optional[str]
) -> Callable[[Dict[str, Any]], None]:
    """F6: give the judging dispatch the same ``subagent_audit.jsonl`` trail
    the write executor gives every write dispatch.

    Built only for ``human_decision_judge`` (see :func:`_gather`'s call site),
    never for the other read kinds: ``AuditLog`` is this repo's write-safety
    control (D3l) — reversibility for a dispatch that edits a file — and a
    validation or consolidation batch touches nothing to roll back. A judged
    human decision is different: it is the one subagent output a human is most
    likely to want to re-examine, and until now its dispatch left no argv, no
    prompt hash and no duration anywhere durable — ``subagent_batch_report.json``
    was the only record, and (before the filename split above) the write phase
    that follows it in the same phase dir promptly overwrote that file.
    """
    try:
        from .write_safety import AuditLog
    except ImportError:  # pragma: no cover - direct-script import shim
        from utils.write_safety import AuditLog
    audit = AuditLog(phase_dir)

    def before_attempt(context: Dict[str, Any]) -> None:
        audit.dispatched(
            task_id=context["task_id"], kind=context["kind"],
            attempt=context["attempt"], runner=context["runner"],
            profile=context["profile"], cwd=context["cwd"],
            sandbox_root=str(context["cwd"] or ""),
            argv=_judge_dispatch_argv_preview(
                context["runner"], context["prompt"], context["profile"], anchor,
            ),
            prompt=context["prompt"], declared_files=[],
        )

    return before_attempt


def _judge_audit_completed(phase_dir: str, outcome: TaskOutcome) -> None:
    """The judging dispatch's terminal audit line, written once ``dispatch_task``
    returns — success or failure alike, unlike ``dispatch_task``'s own
    ``after_result`` hook, which only fires on the schema-valid success path.

    Skipped when no attempt was ever made (a pre-dispatch refusal): a
    ``completed`` line with no matching ``dispatched`` line would claim a run
    that never started, the same guard ``write_batch_scheduler._audit_terminal``
    applies.
    """
    if not outcome.attempts:
        return
    try:
        from .write_safety import AuditLog
    except ImportError:  # pragma: no cover - direct-script import shim
        from utils.write_safety import AuditLog
    last = outcome.attempts[-1]
    AuditLog(phase_dir).completed(
        task_id=outcome.task_id, kind=outcome.kind, attempt=last.index,
        runner=outcome.runner, profile=outcome.profile, status=outcome.status,
        write_outcome=None, exit_code=last.exit_code, files_touched=[],
        observed={}, duration_seconds=outcome.duration_seconds,
        reason=outcome.reason,
        usage=outcome.usage if outcome.usage_reported else None,
    )


async def _gather(
    tasks: Sequence[Dict[str, Any]],
    *,
    runners: Dict[str, str],
    phase_dir: str,
    anchor: Optional[str],
    cwd: Optional[str],
    max_parallel: int,
    resume: bool,
    on_task_finished: Optional[Callable[[TaskOutcome], None]] = None,
) -> Dict[str, TaskOutcome]:
    """Run the batch through the task-keyed concurrency helper.

    ``on_task_finished`` is called once per task as it settles — dispatched,
    skipped or refused by the fatal gate alike — from this loop and nowhere
    else, which is what lets :func:`run_tasks` mirror progress without a lock.
    """
    try:
        from .review_orchestrator_base import run_tasks_concurrent
    except ImportError:  # pragma: no cover
        from utils.review_orchestrator_base import run_tasks_concurrent

    # One flag for the whole batch, consulted at slot-acquisition time — so a
    # task already inside `dispatch_task` when it flips runs to its own verdict,
    # and everything that reaches it afterwards spawns nothing. `spec` is the
    # runner the fatal row resolved: the gate is batch-wide, the claim an
    # undispatched row is allowed to print is per-spec (D4 step 1).
    fatal: Dict[str, Any] = {"hit": False, "spec": None}

    # The starting slot count per provider: its own `max_concurrent`, bounded by
    # the batch's effective ceiling (a provider limit above it could never be
    # reached through the global gate anyway). Passed to `run_tasks_concurrent` as
    # the explicit `provider_limits` it takes for exactly this purpose, and used to
    # seed the gate that narrows them from there.
    provider_limits: Dict[str, int] = {}
    per_task_budget = 0.0
    for spec in dict.fromkeys(runners.values()):
        provider_name, _ = parse_model_spec(spec, anchor=anchor)
        declared = get_provider_max_concurrent(provider_name, anchor=anchor)
        provider_limits[provider_name] = max(
            1, min(declared or max_parallel, max_parallel)
        )
        per_task_budget = max(
            per_task_budget, get_subagent_timeout(provider_name, anchor=anchor)
        )
    backpressure = _ProviderBackpressure(provider_limits)

    # The batch cap must be derived from the budget a dispatch actually runs on.
    # Left to itself, `run_tasks_concurrent` computes it from
    # `get_provider_timeout` — the *model-call* timeout, which says nothing about
    # `driver.subagent_timeout_s`. Configure a subagent budget above the
    # provider's model timeout (agentic runners routinely need one) and the
    # batch-level `wait_for` cancels tasks that are still healthily inside their
    # own deadline; they come back with no result file, are recorded
    # `incomplete` by `run_tasks` and fail the phase with exit 3 while every
    # runner was behaving. `dispatch_task` bounds one task by
    # `get_subagent_timeout(provider)` **in total** — retries and rate-limit
    # backoff are spent inside that same deadline, so the retry budget no longer
    # multiplies it — and the gate serializes the batch into
    # ceil(tasks / effective parallelism) waves, so that product is the batch's
    # own ceiling. `run_tasks_concurrent` still doubles it and adds the stagger,
    # which is the headroom for queueing, kill grace and drain.
    lanes = max(1, max_parallel)
    waves = (len(tasks) + lanes - 1) // lanes
    batch_timeout = per_task_budget * waves if per_task_budget > 0 else None

    def settled(outcome: TaskOutcome) -> TaskOutcome:
        """One task has reached its verdict — tell the caller, then hand it back."""
        if on_task_finished is not None:
            try:
                on_task_finished(outcome)
            except Exception:  # noqa: BLE001 - observability never fails a batch
                pass
        return outcome

    async def per_task(task: Dict[str, Any], runner: str, index: int) -> TaskOutcome:
        if fatal["hit"]:
            failed_spec = fatal["spec"]
            if runner == failed_spec:
                reason = (
                    f"not dispatched: {failed_spec} failed on a rung that fails "
                    f"the whole batch; every task on that runner would fail "
                    f"identically"
                )
            else:
                # Predicts nothing: a rejected id on one spec says nothing
                # about a sibling `model_hint` pinned to another.
                reason = (
                    f"not dispatched: the batch stopped after {failed_spec} "
                    f"failed fatally; this task's runner {runner} was never tried"
                )
            return settled(TaskOutcome(
                task_id=str(task.get("task_id", index)),
                kind=str(task.get("kind", "")),
                runner=runner,
                status=STATUS_INCOMPLETE,
                reason=reason,
            ))
        provider_name, _ = parse_model_spec(runner, anchor=anchor)
        await backpressure.acquire(provider_name)
        # F6: route the judging dispatch through `subagent_audit.jsonl` too —
        # see `_judge_audit_before_attempt`. Every other kind passes `None` and
        # dispatches exactly as it always has — and the call stays the exact
        # kwargs it always took, `before_attempt` included, for every non-judge
        # dispatch (a test double patched in for `dispatch_task` need not accept
        # a keyword it never receives).
        is_judge = str(task.get("kind", "")) == "human_decision_judge"
        judge_kwargs: Dict[str, Any] = (
            {"before_attempt": _judge_audit_before_attempt(phase_dir, anchor)}
            if is_judge else {}
        )
        # §5: narrow on the rate-limited *attempt*, not on the finished task —
        # a task that backs off and retries can hold its verdict for many
        # minutes, and every sibling acquiring meanwhile should already see the
        # narrower gate. Passed under the same F6 rule as `before_attempt`: only
        # when narrowing can still change something, and only to a
        # `dispatch_task` that takes the keyword, so a stand-in double keeps
        # the exact kwargs it always received. A dispatch without it still
        # narrows below, after it returns.
        narrowing = {"done": False}
        attempt_kwargs: Dict[str, Any] = (
            {"after_attempt": _narrow_on_rate_limited_attempt(
                backpressure, provider_name, asyncio.get_running_loop(),
                str(task.get("task_id", index)), narrowing,
            )}
            if backpressure.can_narrow(provider_name)
            and _accepts_keyword(dispatch_task, "after_attempt")
            else {}
        )
        try:
            outcome = await asyncio.to_thread(
                dispatch_task,
                task,
                phase_dir=phase_dir,
                runner=runner,
                anchor=anchor,
                cwd=cwd,
                **judge_kwargs,
                **attempt_kwargs,
            )
        finally:
            await backpressure.release(provider_name)
        if is_judge:
            _judge_audit_completed(phase_dir, outcome)
        if outcome.fatal and not fatal["hit"]:
            fatal["hit"] = True
            fatal["spec"] = runner
        # At most once per task: a task whose attempt already narrowed (or
        # tried to — the flag is set before `narrow()` is submitted) is skipped.
        if not narrowing["done"] and _saw_rate_limit(outcome):
            narrowed = await backpressure.narrow(provider_name)
            if narrowed is not None:
                print(
                    f"[exec-subagents] {provider_name} reported a rate limit — "
                    f"narrowing it to {narrowed} in-flight slot(s) for the rest "
                    f"of the batch"
                )
        return settled(outcome)

    def skip_done(task: Dict[str, Any], runner: str, index: int) -> Optional[TaskOutcome]:
        if not resume or not task_is_complete(task, phase_dir):
            return None
        target = resolve_output_target(task, phase_dir)
        print(f"[exec-subagents] {task.get('task_id')} already complete — skipping")
        return settled(TaskOutcome(
            task_id=str(task.get("task_id", index)),
            kind=str(task.get("kind", "")),
            runner=runner,
            status=STATUS_OK,
            output_path=str(target),
            skipped=True,
        ))

    return await run_tasks_concurrent(
        list(tasks),
        per_task,
        runner_for_task=lambda task: runners[str(task.get("task_id", ""))],
        timeout=batch_timeout,
        max_parallel=max_parallel,
        skip_predicate=skip_done,
        provider_limits=provider_limits,
        # §9.3.c: the helper has no plan path of its own; this batch's is the
        # anchor its per-provider bounds and timeouts must resolve against.
        anchor=anchor,
    )


def _pin_sha256(tasks: Sequence[Dict[str, Any]]) -> str:
    """What a recorded runner is a pin *for*: the round plus the batch inputs.

    :func:`subagent_tasks.task_round` fingerprints which groups each output
    answers; the first task's ``inputs`` (plan, grouped file, diff base, reviewed
    code) say what they were judged against. A forced re-review that changes
    either is a new dispatch, not a re-dispatch.
    """
    try:
        from .subagent_tasks import task_round
    except ImportError:  # pragma: no cover
        from utils.subagent_tasks import task_round
    first_inputs = next(
        (t.get("inputs") for t in tasks if isinstance(t, dict) and t.get("inputs")),
        None,
    )
    canonical = json.dumps(
        [task_round(tasks), first_inputs], sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _recorded_runners(
    phase_dir: str, kind: str = "", *, pin_sha256: str = ""
) -> Dict[str, str]:
    """Runners pinned by a previous batch report, for a re-dispatch (D3o).

    **A recorded runner whose recorded status is fatal is not a pin, it is a
    rejected assignment** (D4 step 6) — and neither is the same spec on a row
    the fatal gate stopped before it could be tried. One rule, keyed on the spec
    rather than the row: every row whose runner equals a spec that *any* row in
    the same report recorded with a status in ``FATAL_STATUSES`` is dropped, so
    ``resolve_task_runner`` falls through to the current configuration for
    exactly the tasks the rejected spec touched, and a config repair takes
    effect on re-invocation. Rows on a spec that never failed keep their pin.
    The spec-keyed half is load-bearing: the concurrent gate records
    undispatched siblings ``incomplete`` (not fatal) while still writing the
    spec they were about to use, and preflight runs once per *distinct* spec —
    so one surviving pin would re-refuse the whole batch, repaired config and
    all.

    ``kind`` (F6): a re-dispatch must read *this* dispatch's own report back,
    not whichever kind's report happens to sit at the bare filename — see
    :func:`_batch_report_filename`. Omitted by the one caller that can never
    collide (``_authoritative_validator_runner``, always a validation-family
    kind), where it defaults to the bare name exactly as before.

    **A row whose own status is a reply-quality failure is not a pin either**
    (:data:`UNPINNED_ROW_STATUSES`, fix round 8): the runner was reached and
    answered, in a shape nobody could use, so a re-run is the moment to try
    another runner — the session model the host switched to, or a repaired
    ``driver.subagent_runner`` — not to repeat it. Row-level, unlike the fatal
    rule: the spec itself works. A transport failure (timeout, rate limit,
    runner error) or an ``incomplete`` row keeps its pin, so a re-run of a
    batch that merely ran out of time stays on the runner its siblings used.
    Measured 2026-10-05, OpenCode run 3: generate-tasks failed twice on
    ``opencode/big-pickle``'s reply shape, the host switched model, and the
    re-run dispatched big-pickle again on the strength of that failed row.

    ``pin_sha256`` (2026-10-02, #29): the current batch's :func:`_pin_sha256`. A
    report that recorded a *different* digest was written for another round or other
    inputs, and its runners are not pins for this batch. Measured on a Codex
    ``review-code --force``: the previous day's validation report recorded the
    session model (``codex:gpt-6-astra``, before the project set
    ``driver.subagent_runner: claude-code:sonnet``), and the forced re-review
    re-used that pin instead of the configured runner. A report with no digest, or a
    caller that passes none, pins exactly as before.
    """
    path = Path(phase_dir) / _batch_report_filename(kind)
    if not path.exists():
        return {}
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    recorded_sha256 = document.get("pin_sha256") if isinstance(document, dict) else None
    if pin_sha256 and recorded_sha256 and recorded_sha256 != pin_sha256:
        return {}
    rows = [
        row for row in document.get("tasks", [])
        if isinstance(row, dict) and row.get("task_id") and row.get("runner")
    ]
    rejected_specs = {
        str(row["runner"]) for row in rows if row.get("status") in FATAL_STATUSES
    }
    recorded = {}
    for row in rows:
        spec = str(row["runner"])
        if spec in rejected_specs or row.get("status") in UNPINNED_ROW_STATUSES:
            continue
        recorded[str(row["task_id"])] = spec
    return recorded


def _recorded_provenance(
    phase_dir: str, kind: str = ""
) -> Optional[Dict[str, Dict[str, Any]]]:
    """The ``batch_provenance`` block of ``kind``'s batch report (§7.3a).

    ``None`` when there is no report, or the report predates the block (no
    ``batch_provenance`` key at all) — the caller then falls back to the legacy
    per-row ``runner`` (:func:`_recorded_runners`). ``{}`` is a report that
    recorded provenance and has none to offer.
    """
    path = Path(phase_dir) / _batch_report_filename(kind)
    if not path.exists():
        return None
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(document, dict) or "batch_provenance" not in document:
        return None
    block = document.get("batch_provenance")
    if not isinstance(block, dict):
        return {}
    return {
        str(task_id): row for task_id, row in block.items() if isinstance(row, dict)
    }


def _mirror_status(
    phase_dir: str, report: BatchReport, *, total: Optional[int] = None
) -> None:
    """Mirror the batch counts into ``.status.json`` (D4a). Best-effort.

    ``total`` is the batch's task count, which while the batch is in flight is
    larger than the number of outcomes recorded so far; it defaults to the
    outcomes present, so the mirror a finished batch writes is byte-identical to
    the one this wrote before it took the argument.
    """
    try:
        from . import status_file as _status_file
    except ImportError:  # pragma: no cover
        from utils import status_file as _status_file
    try:
        _status_file.update_status(phase_dir, {
            "progress": {
                _STATUS_MIRROR_KEY: {
                    "kind": report.kind,
                    "invoker": report.invoker,
                    "total": total if isinstance(total, int) else len(report.outcomes),
                    "ok": sum(1 for o in report.outcomes if o.ok),
                    "counts": report.counts(),
                    "failed_task_ids": [o.task_id for o in report.failed],
                    "runner_versions": dict(report.runner_versions),
                    "effective_parallelism": report.ceilings.get("effective"),
                }
            }
        })
    except Exception:  # noqa: BLE001 - observability must not fail a phase
        pass


#: The provenance a task file records about itself: the document key naming a
#: source file → the ``inputs`` key its hash was recorded under. This is what
#: makes the default read path able to re-bind a file nobody handed it: every
#: producer writes the source paths next to the hashes (validation and
#: consolidation their ``plan_file``/``grouped_file``, salvage its
#: ``salvage_request_path``). ``diff_sha256``/``items_sha256`` are deliberately
#: absent — their source is not a file on disk, so they stay unchecked rather
#: than spuriously refused (:func:`subagent_tasks.check_task_file_inputs`
#: compares only keys present in both blocks).
_INPUT_SOURCE_KEYS = {
    "plan_file": "plan_sha256",
    "grouped_file": "grouped_sha256",
    "tasks_file": "tasks_sha256",
    "salvage_request_path": "salvage_request_sha256",
}


def _recomputed_inputs(
    document: Dict[str, Any], phase_dir: str, anchor: Optional[str]
) -> Dict[str, str]:
    """Re-hash the inputs this task file's own recorded provenance still names.

    Freshly computed hashes are what turn ``read_task_file``'s inputs guard on —
    without them it version- and schema-checks the file and binds nothing. A
    caller that already knows its inputs passes them in; this is the fallback for
    one that only has the file, and it reads the sources *the document itself*
    names so a re-hash can never bind the file to something it was not
    materialized from.

    A source that cannot be read is skipped rather than hashed to ``""``: a
    missing file would compare as "changed" and refuse a phase dir that was
    merely moved, and an input nobody can recompute is exactly the case
    ``check_task_file_inputs`` documents as "simply does not check it". A
    recorded hash that is *already* ``""`` is skipped for the mirror-image
    reason — that is ``file_content_hash``'s "the producer had no such file"
    (every salvage task file records ``plan_sha256: ""``), so re-hashing
    something in its place would refuse a file that was never bound to it.
    """
    try:
        from .subagent_tasks import file_content_hash
    except ImportError:  # pragma: no cover
        from utils.subagent_tasks import file_content_hash

    recorded = document.get("inputs")
    if not isinstance(recorded, dict):
        return {}
    sources: Dict[str, Any] = {
        key: document.get(key) for key in _INPUT_SOURCE_KEYS
    }
    # The salvage files record no `plan_file` (the request is what their prompt is
    # built from), but they do record `plan_sha256`, and the dispatching caller
    # already threads the plan path through as `anchor` — which is a plan file or
    # a repo directory, so it only stands in when it is really a file.
    if not sources.get("plan_file") and anchor and os.path.isfile(anchor):
        sources["plan_file"] = anchor

    current: Dict[str, str] = {}
    for source_key, input_key in _INPUT_SOURCE_KEYS.items():
        source = sources.get(source_key)
        if not recorded.get(input_key) or not isinstance(source, str) or not source:
            continue
        path = source if os.path.isabs(source) else os.path.join(phase_dir, source)
        if not os.path.isfile(path):
            continue
        current[input_key] = file_content_hash(path)
    return current


def run_task_file(
    task_file: str,
    *,
    phase_dir: Optional[str] = None,
    phase: str = "",
    anchor: Optional[str] = None,
    cwd: Optional[str] = None,
    document: Optional[Dict[str, Any]] = None,
    current_inputs: Optional[Dict[str, str]] = None,
    host_max: Optional[int] = None,
    resume: bool = True,
    only_task_ids: Optional[Iterable[str]] = None,
) -> BatchReport:
    """Dispatch every task in a materialized task file.

    ``document`` lets a caller that already read (and input-bound) the file hand
    it in rather than re-reading — the version/inputs guards belong to
    ``utils/subagent_tasks.read_task_file`` and must not be bypassed here.

    ``current_inputs`` is the freshly recomputed hash block for the read path.
    It is optional but the binding is **not**: ``read_task_file`` only enforces
    the inputs guard when it is given one, so passing nothing would silently
    downgrade the default read to a version-and-schema check — and a phase dir
    outlives the run that wrote it, so a plan or a salvage request edited between
    a crash and the resume would produce a confidently stale prompt against text
    nobody is reviewing any more (D2g). When it is omitted the hashes are
    recomputed from the provenance the document records (:func:`_recomputed_inputs`).

    Human tasks are filtered out rather than dispatched: ``executor_role: human``
    means no invoker ever runs them, and they route to the D6 human-task pause.

    Raises:
        ExecutorError: exit 3 — the file is the wrong version, the wrong shape,
            or was materialized from inputs that have since moved. Raised as the
            executor's own refusal so both invokers' handlers (which exit 3 on
            the fan-out path and skip the one non-fatal salvage dispatch) see it
            rather than a bare traceback. Nothing is dispatched either way.
    """
    resolved_dir = phase_dir or os.path.dirname(os.path.abspath(task_file))
    if document is None:
        try:
            from .subagent_tasks import (
                TaskFileError,
                check_task_file_inputs,
                read_task_file,
            )
        except ImportError:  # pragma: no cover
            from utils.subagent_tasks import (
                TaskFileError,
                check_task_file_inputs,
                read_task_file,
            )
        try:
            document = read_task_file(task_file, phase_dir=resolved_dir)
            bound = (
                current_inputs if current_inputs is not None
                else _recomputed_inputs(document, resolved_dir, anchor)
            )
            if bound:
                check_task_file_inputs(document, task_file, resolved_dir, bound)
        except TaskFileError as exc:
            raise ExecutorError(str(exc)) from exc

    # A frozen context plan is read by path even when the caller has already
    # materialized the document in memory. Bind it on both entry paths, and
    # treat a missing snapshot (or old task file lacking provenance) as stale.
    if (document.get("inputs") or {}).get("context_plan_sha256"):
        try:
            from .subagent_tasks import TaskFileError, check_task_file_inputs, file_bytes_sha256
        except ImportError:  # pragma: no cover - flat import layout
            from utils.subagent_tasks import TaskFileError, check_task_file_inputs, file_bytes_sha256

        source = document.get("context_plan_file")
        path = os.path.join(resolved_dir, source) if isinstance(source, str) and source else None
        try:
            check_task_file_inputs(document, task_file, resolved_dir, {
                "context_plan_sha256": file_bytes_sha256(path),
            })
        except TaskFileError as exc:
            raise ExecutorError(str(exc)) from exc

    tasks = [
        task for task in tasks_of(document)
        if task.get("executor_role") != "human"
    ]
    return run_tasks(
        tasks,
        phase_dir=resolved_dir,
        phase=phase,
        kind=str(document.get("kind", "")),
        task_file=task_file,
        anchor=anchor,
        cwd=cwd,
        host_max=host_max,
        resume=resume,
        only_task_ids=only_task_ids,
    )


# ---------------------------------------------------------------------------
# The native invoker, simulated (D3a equivalence)
# ---------------------------------------------------------------------------

def simulate_native_invoker(
    tasks: Sequence[Dict[str, Any]],
    *,
    phase_dir: str,
    respond: Callable[[Dict[str, Any]], Any],
    phase: str = "",
    kind: str = "",
    write_report: bool = False,
) -> BatchReport:
    """Play the *native* invoker half of the D3a contract as real code.

    On a native-subagent host the driving agent runs ``task.prompt`` and writes the
    JSON its subagent returned to the task's ``output_path``. That write is
    :func:`persist_result` — the same containment, the same per-kind validation and
    the same serialization the executor uses — so the two invokers produce
    byte-identical files by construction rather than by convention, and the
    equivalence assertion has something real to compare.

    Args:
        respond: ``task -> the JSON the subagent returned`` (a dict/list), or the
            raw text it printed (a string, run through the same extraction the
            executor uses).
    """
    report = BatchReport(
        phase=phase, kind=kind, phase_dir=phase_dir, invoker="native-simulated",
    )
    for index, task in enumerate(tasks):
        task_id = str(task.get("task_id", index))
        task_kind = str(task.get("kind", kind))
        outcome = TaskOutcome(
            task_id=task_id, kind=task_kind, runner="native", status=STATUS_REJECTED,
            profile=PROFILE_AGENT_READONLY,
        )
        if task.get("executor_role") == "human":
            outcome.reason = "executor_role: human — never dispatched by any invoker"
            report.outcomes.append(outcome)
            continue
        reason = refuse_reason(task, supports_workspace_reads=True, runner="native")
        if reason is not None:
            outcome.reason = reason
            report.outcomes.append(outcome)
            continue
        data = respond(task)
        if isinstance(data, str):
            extracted = extract_json_from_text(
                data, prefer_arrays=task_kind == "salvage"
            )
            if not extracted.get("success"):
                outcome.status = STATUS_UNPARSEABLE
                outcome.reason = extracted.get("error") or "no JSON in the reply"
                report.outcomes.append(outcome)
                continue
            data = the_reply_object(task_kind, extracted["data"], extracted)
        gave_up = _salvage_gave_up(
            task_kind, data, salvage_failure_of(task, phase_dir)
        )
        if gave_up is not None:
            # The same rule the executor lane applies in `_parse_and_validate`,
            # at the same point: after extraction, before validation, and before
            # anything can be written over the model's own result file. Two call
            # sites because the D3a contract is two invokers, not one loop — the
            # predicate they share is what keeps them equivalent.
            outcome.status = STATUS_SALVAGE_UNRECOVERABLE
            outcome.reason = gave_up
            report.outcomes.append(outcome)
            continue
        errors = validate_result(task_kind, data)
        if errors:
            outcome.status = STATUS_SCHEMA_INVALID
            outcome.reason = "; ".join(errors[:5])
            report.outcomes.append(outcome)
            continue
        outcome.output_path = persist_result(task, phase_dir, data)
        outcome.status = STATUS_OK
        report.outcomes.append(outcome)
    if write_report:
        report.write()
    return report


# ---------------------------------------------------------------------------
# D3l — --dry-run-subagents for the read half
# ---------------------------------------------------------------------------

def _preview_argv(
    provider: Any,
    *,
    prompt: str,
    model: str,
    profile: str,
    schema: Optional[Any],
    anchor: Optional[str] = None,
    sandbox_fallback: Optional[str] = None,
    jail_request: Optional[JailRequest] = None,
) -> Tuple[Optional[List[str]], Optional[str]]:
    """The argv a dispatch WOULD render, built the way a dispatch builds it.

    A preview whose argv differs from the real argv is worth less than its own
    output implies, so this is deliberately :func:`_spawn` / :func:`_spawn_child`
    minus the ``Popen``: the same two context managers, in the same order, around
    the same adapter call.

    * **The dispatch context first** (M4/§2.3). An adapter that contains its own
      config layering renders a flag and an env redirect that only mean anything
      together — opencode's ``--pure`` pairs with its ``XDG_CONFIG_HOME``
      redirect and neither is emitted outside an active context — so rendering
      here without entering it would preview an argv no dispatch ever runs. The
      ``with`` is also the ``finally`` half of that lifecycle: the context is
      refcounted and its shared temp directory is removed when the last user
      leaves, so a preview cleans up exactly as a dispatch does. A refusal comes
      back as a *reason*, not an argv — the same refusal the real spawn would
      have taken on its spawn rung, minus the child.
    * **The sidecar second** (§4.2.1), for the adapters whose structured-output
      transport is a file: codex refuses a schema whose file is unreadable
      *before* it returns any argv, so a preview that passed the unmaterialized
      schema would report "would not dispatch" for a task that dispatches fine.
      The directory is removed on the way out, here as there.

    ``schema=None`` — every kind with no schema phase, and every adapter that
    declined the flag — renders exactly what this preview rendered before.
    ``sandbox_fallback`` is the rung id the preflight just recorded (or
    ``None``): a dry run's argv has to show the rung a real dispatch would
    render — ``danger-full-access``, or ``read-only`` plus the landlock feature
    — or the preview would be the one artifact that hid it.

    On the plugin's Landlock jail (plan codex-sandbox-unavailable §6 F1,
    2026-09-30) the preview shows the wrapped shape — the interpreter, the
    wrapper, the ``--allow`` entries and ``-c developer_instructions=…`` —
    with placeholder paths, and creates nothing: no scratch directory, no
    home lookup. ``jail_request`` is the dispatch's grant; a read kind's is
    built from the process cwd when none is given.
    """
    rung = sandbox_rung_id(sandbox_fallback)
    wrap = _wrapping_rung(provider, profile, rung)
    if wrap is not None and jail_request is None:
        jail_request = JailRequest(repo_root=os.path.realpath(os.getcwd()), kind=profile)

    def _render(materialized_schema: Optional[Any]) -> List[str]:
        argv = provider.build_agent_command(
            prompt, model, profile, schema=materialized_schema
        )
        if wrap is not None and jail_request is not None:
            argv = provider.apply_sandbox_fallback(
                argv, profile, rung,
                context=landlock_dispatch.preview_context(jail_request),
            )
            return landlock_dispatch.preview_wrap_argv(argv, wrap, jail_request)
        if rung:
            argv = provider.apply_sandbox_fallback(argv, profile, rung)
        return argv

    with provider_dispatch_context(
        provider, model, profile, anchor=anchor,
        runner_version=_preflight_version(provider),
    ) as dispatch:
        if dispatch.refusal:
            return None, dispatch.refusal
        if schema is not None and getattr(
            provider, "structured_output_transport", "inline"
        ) == "file":
            with structured_output.schema_sidecar(schema) as materialized:
                return _render(materialized), None
        return _render(schema), None


def dry_run_report(
    task_file: str,
    *,
    phase_dir: str,
    phase: str = "",
    document: Optional[Dict[str, Any]] = None,
    anchor: Optional[str] = None,
    cwd: Optional[str] = None,
) -> str:
    """Render every read/analyze dispatch without starting one. Returns the path.

    The read-half twin of the scheduler's write dry run: resolve the runner, render
    the exact argv (prompt elided to its digest), check the transport and the
    prompt budget, apply the profile, probe runner presence and version — then write
    ``{phase}/subagent_dry_run.json`` and return, having spawned nothing but
    ``--version``.
    """
    try:
        from .write_safety import DRY_RUN_FILENAME, redact_argv
    except ImportError:  # pragma: no cover
        from utils.write_safety import DRY_RUN_FILENAME, redact_argv

    resolved_dir = phase_dir or os.path.dirname(os.path.abspath(task_file))
    if document is None:
        try:
            from .subagent_tasks import read_task_file
        except ImportError:  # pragma: no cover
            from utils.subagent_tasks import read_task_file
        document = read_task_file(task_file, phase_dir=resolved_dir)

    kind = str(document.get("kind", ""))
    entries: List[Dict[str, Any]] = []
    runners: List[str] = []
    for task in tasks_of(document):
        task_id = str(task.get("task_id", ""))
        entry: Dict[str, Any] = {
            "task_id": task_id,
            "kind": str(task.get("kind", kind)),
            "cwd": cwd,
        }
        if task.get("executor_role") == "human":
            entry["would_dispatch"] = False
            entry["reason"] = "executor_role: human — never dispatched by any invoker"
            entries.append(entry)
            continue
        try:
            entry["profile"] = profile_for_kind(str(task.get("kind", kind)))
        except ExecutorError as exc:
            entry["would_dispatch"] = False
            entry["reason"] = exc.message
            entries.append(entry)
            continue
        runner = resolve_task_runner(task, anchor=anchor)
        entry["runner"] = runner
        runners.append(runner)
        provider_name, model = parse_model_spec(runner, anchor=anchor)
        provider = get_provider(provider_name)
        transport = preferred_prompt_transport(provider_name)
        entry["prompt_transport"] = transport
        prompt = str(task.get("prompt") or "")
        try:
            from .subagent_tasks import utf16_units
        except ImportError:  # pragma: no cover
            from utils.subagent_tasks import utf16_units
        entry["prompt_utf16_units"] = utf16_units(prompt)
        reason = refuse_reason(
            task,
            supports_workspace_reads=bool(
                provider is not None and provider.supports_workspace_reads
            ),
            runner=runner,
        )
        if reason is None:
            try:
                resolve_output_target(task, resolved_dir)
            except ResultRejected as exc:
                reason = exc.message
        if reason is None and provider is not None:
            fallback = sandbox_rung(runner, entry["profile"])
            reason = _prompt_over_budget(
                provider, model, prompt, transport, entry["profile"],
                **({"sandbox_fallback": fallback, "jail_request": JailRequest(
                    repo_root=os.path.realpath(cwd or os.getcwd()),
                    kind=entry["kind"],
                )} if _wrapping_rung(provider, entry["profile"], fallback) else {}),
            )
        if reason is None:
            try:
                info = preflight_runner(
                    runner, profile=entry["profile"], anchor=anchor,
                    key="driver.subagent_runner",
                    # D3l: a dry run renders commands and starts no child, so the
                    # declared nested_exec verdict still refuses a `denied` host
                    # but the throwaway dispatch behind an `unknown` leg does not
                    # run — it is a real turn, and this flag promises none.
                    probe_nested=False,
                )
                entry["runner_version"] = info["version"]
                entry["nested_exec"] = info["nested_exec"]
            except ExecutorError as exc:
                reason = exc.message
        if reason is not None:
            entry["would_dispatch"] = False
            entry["reason"] = reason
            entries.append(entry)
            continue
        # §4.2.2's pre-dispatch read, resolved from the KIND exactly as
        # `dispatch_task` resolves it (`schema_phase_for_kind` +
        # `schema_for_dispatch`) — never hard-coded here, or the preview would
        # be right for one schema-bearing kind and wrong for the other. `warn`
        # is off: the per-(provider, phase) WARN belongs to a dispatch that is
        # really taking the fallback, and a preview that emitted it would both
        # duplicate the line and consume the once-per-process budget the real
        # run needs.
        schema = None
        schema_phase = schema_phase_for_kind(str(task.get("kind", kind)))
        # `provider is not None` for the same reason the budget check above
        # carries it: a runner with no built-in adapter is normally refused by
        # `preflight_runner` before here, and a preflight may not raise on the
        # path where it was not.
        if schema_phase and provider is not None:
            try:
                schema, _marker = structured_output.schema_for_dispatch(
                    provider, schema_phase, warn=False
                )
            except structured_output.SchemaConfigError as exc:
                # Rung 7 in a dispatch, "would not dispatch" here: no run can
                # produce a schema file that is not there.
                entry["would_dispatch"] = False
                entry["reason"] = f"structured output: {exc}"
                entries.append(entry)
                continue
        try:
            fallback = sandbox_rung(runner, entry["profile"])
            argv, refusal = _preview_argv(
                provider, prompt=prompt, model=model, profile=entry["profile"],
                schema=schema, anchor=anchor,
                sandbox_fallback=fallback,
                **({"jail_request": JailRequest(
                    repo_root=os.path.realpath(cwd or os.getcwd()),
                    kind=entry["kind"],
                )} if _wrapping_rung(provider, entry["profile"], fallback) else {}),
            )
        except Exception as exc:  # noqa: BLE001 - a preflight must not raise
            entry["would_dispatch"] = False
            entry["reason"] = str(exc)
            entries.append(entry)
            continue
        if refusal is not None or argv is None:
            entry["would_dispatch"] = False
            entry["reason"] = refusal or "the adapter rendered no command"
            entries.append(entry)
            continue
        entry["argv"] = redact_argv(argv, prompt)
        entry["would_dispatch"] = True
        entries.append(entry)

    path = os.path.join(resolved_dir, DRY_RUN_FILENAME)
    _atomic_write_json(path, {
        "dry_run_version": 1,
        "kind": kind,
        "phase": phase,
        "task_file": task_file,
        "cwd": cwd,
        "ceilings": effective_ceiling(runners, anchor=anchor) if runners
        else {"effective": 0},
        "tasks": entries,
    })
    return path


# ---------------------------------------------------------------------------
# D3b — the self-contained continuation past a marker
# ---------------------------------------------------------------------------

def _retry_instruction(
    args: Any, *, failed_ids: str, retry_command: Optional[str]
) -> List[str]:
    """The failed batch's recovery block, addressed to whoever can follow it.

    ``--host`` is already on this run's own namespace — a shim bakes it into
    every command it renders — so the addressee is resolved at the point host
    capability is *already known*, in Python, and the agent is handed a finished
    sentence. Nothing here asks an agent to consult the capability matrix
    mid-run (D5); the matrix stays off every agent read path.

    Two imports, no third fallback: ``host_capabilities`` sits beside this module
    in the same package, so if neither spelling resolves this module's own
    top-level imports have already failed.
    """
    try:
        from . import host_capabilities as caps
    except ImportError:  # pragma: no cover - direct script runs
        import host_capabilities as caps  # type: ignore
    host_id = caps.resolve_host_id(explicit=getattr(args, "host", None))
    return caps.retry_instruction(
        host_id, failed_ids=failed_ids, retry_command=retry_command
    )


def continue_past_marker(
    args: Any,
    *,
    task_file: str,
    phase_dir: str,
    phase: str = "",
    document: Optional[Dict[str, Any]] = None,
    anchor: Optional[str] = None,
    cwd: Optional[str] = None,
    label: str = "subagent",
    retry_command: Optional[str] = None,
) -> bool:
    """Should this phase continue in-process past the marker it just printed?

    Host-driven (the default, and today's behavior byte-for-byte): returns
    ``False`` immediately when ``--exec-subagents`` is off, so the caller prints
    its follow-up command and exits exactly as before. The executor is strictly
    additive until a host asks for it.

    Self-contained (``--exec-subagents``): dispatches the batch, and returns
    ``True`` when every task produced a schema-valid result file, so the caller
    falls through to reaggregation / verdict ingest / consolidation inline and the
    phase completes in one invocation. Markers are still printed — they are
    informational on this path, and the run is finished when the process exits.

    Raises:
        BatchFailed: exit 3 (even under ``--yes``) when any task failed or is
            incomplete. The phase does **not** reaggregate the short set and never
            falls back to salvage.
    """
    if not getattr(args, "exec_subagents", False):
        return False

    if getattr(args, "dry_run_subagents", False):
        # D3l: the flag means "start no child", and it means it on the read half
        # too. Without this branch a read phase would dispatch for real under a
        # flag whose whole promise is that it does not — the surprise being worse
        # here than on the write path precisely because nothing visibly changes.
        report = dry_run_report(
            task_file, phase_dir=phase_dir, phase=phase, document=document,
            anchor=anchor, cwd=cwd,
        )
        print(
            f"[dry-run-subagents] {report} — every {label} command rendered, no "
            f"child started, nothing else changed. This phase still prints its "
            f"marker and its follow-up command."
        )
        return False

    print(f"\n[exec-subagents] dispatching {label} tasks from {task_file}")
    report = run_task_file(
        task_file,
        phase_dir=phase_dir,
        phase=phase,
        document=document,
        anchor=anchor,
        cwd=cwd,
    )
    if report.ok:
        print(
            f"[exec-subagents] {len(report.outcomes)} {label} task(s) complete; "
            f"continuing in-process"
        )
        return True

    failed_ids = ", ".join(o.task_id for o in report.failed)
    lines = [
        f"\nERROR: {len(report.failed)} of {len(report.outcomes)} {label} task(s) "
        f"did not produce a usable result, so this phase refuses to reaggregate a "
        f"short set. Under --yes this is still exit 3: an unattended run may not "
        f"decide that a missing batch is acceptable.",
        *report.failure_summary(),
        # F6: names the file this dispatch's own kind actually wrote, not
        # always the bare name — a failed judging dispatch would otherwise
        # point at a report a later write dispatch may go on to overwrite.
        f"Report: {batch_report_path(phase_dir, report.kind)}",
        f"Diagnostics: {os.path.join(phase_dir, FAILED_CAPTURE_DIRNAME)}/",
        # Resume IS the retry-only-the-failures path: a task counts as done iff
        # its result file exists, parses and validates, so re-invoking the phase
        # skips every completed task and re-dispatches exactly the failed set
        # ({failed_ids}) under its original task_id. Who is being asked to
        # re-invoke is the host's `multi_turn` answer, not an assumption: a host
        # that ends its run with this command leaves no agent able to follow the
        # instruction, so it is addressed to the human instead.
        #
        # D2 step 4: the block is *shaped* from this call's own report — the
        # statuses of `report.failed`, and whether the fan-out's artifacts are
        # usable — never from a count. A fatal status names its repair above
        # the command; a transient one names the cost beneath it; unusable
        # artifacts make --force the command. Only one runnable string either
        # way, so a host's option scrape yields one retry tool call.
        *_shaped_retry_block(
            args, report, phase_dir=phase_dir, document=document,
            failed_ids=failed_ids, retry_command=retry_command,
        ),
    ]
    raise BatchFailed("\n".join(lines), report)


def _artifacts_usable(document: Optional[Dict[str, Any]], phase_dir: str) -> bool:
    """Whether the fan-out's own artifacts this batch reads still parse.

    The grouped file the task document names (``grouped_file``, recorded
    beside its hash) is the one artifact a validation/consolidation batch is
    downstream of; when it is missing or unreadable the reviewer pass itself
    has to run again, and no ``--reaggregate`` can help. A document naming no
    such file has nothing to check and is usable by definition.
    """
    if not document:
        return True
    grouped = document.get("grouped_file")
    if not grouped:
        return True
    path = grouped if os.path.isabs(str(grouped)) else os.path.join(phase_dir, str(grouped))
    try:
        with open(path, "r", encoding="utf-8") as stream:
            json.load(stream)
    except (OSError, ValueError):
        return False
    return True


def _force_variant(command: Optional[str]) -> Optional[str]:
    """The same retry with ``--force`` as its verb (shape 3 only)."""
    if not command:
        return None
    for verb in ("--reaggregate", "--reaggregate-consolidation", "--yes"):
        if command.endswith(" " + verb):
            return command[: -len(verb)] + "--force"
    return command + " --force"


def _shaped_retry_block(
    args: Any,
    report: "BatchReport",
    *,
    phase_dir: str,
    document: Optional[Dict[str, Any]],
    failed_ids: str,
    retry_command: Optional[str],
) -> List[str]:
    """`_retry_instruction` wrapped in the shape `cli_common.retry_shape` picks."""
    try:
        from . import cli_common
    except ImportError:  # pragma: no cover - direct script runs
        import cli_common  # type: ignore
    statuses = [o.status for o in report.failed]
    shape = cli_common.retry_shape(
        statuses=statuses, artifacts_ok=_artifacts_usable(document, phase_dir)
    )
    redispatch = len(report.failed)
    kept = sum(1 for o in report.outcomes if o.ok)
    if shape == cli_common.SHAPE_FORCE:
        return [
            "The fan-out's own artifacts are unusable (the grouped file this "
            "batch reads is missing or does not parse), so the reviewer pass "
            "has to run again — re-invoke with --force:",
            *_retry_instruction(
                args, failed_ids=failed_ids,
                retry_command=_force_variant(retry_command),
            ),
        ]
    lines: List[str] = []
    if shape == cli_common.SHAPE_REPAIR:
        counts: Dict[str, int] = {}
        for status in statuses:
            counts[status] = counts.get(status, 0) + 1
        lines.append(
            "Repair first: "
            + cli_common.repair_sentence(counts=counts, statuses=statuses)
            + "."
        )
    lines.extend(
        _retry_instruction(args, failed_ids=failed_ids, retry_command=retry_command)
    )
    lines.append(
        f"  (re-dispatches the {redispatch} failed task(s) and keeps the {kept} "
        f"valid result(s) already on disk; --force is not needed and would "
        f"re-run the reviewer panel)"
    )
    return lines
