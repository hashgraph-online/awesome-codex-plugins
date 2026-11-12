#!/usr/bin/env python3
"""The write-batch scheduler (D3n): a write phase *schedules*, it does not fan out.

D3g says what one write dispatch means, D3h how it stays safe, D3i how a batch of
them is bounded. None of them owns the **loop**, and three facts — all invisible
from the read path — make a write phase a loop with state rather than a fan-out:

1. **Pattern A's "complete prompt" is complete except for one token.** Every apply
   prompt the batchers build carries a literal ``{prior_changes_context}``, whose
   value is a function of the batches that already *finished*. An executor that
   dispatched the stored prompt verbatim would send the model the brace text and
   silently drop every prior-batch summary — exactly the context that keeps batch N
   from re-applying or contradicting batch N−1. So the substitution is **late, in
   Python, per dispatch**, and it produces the *dispatched* prompt without ever
   rewriting the hash-bound task file.
2. **Implement batches are a dependency order, not a list.** Ascending
   ``batch_index``, and batch N+1 is dispatched only after batch N's D3g
   classification has completed and been recorded — ordering and verification are
   the same rule seen twice.
3. **Human tasks sit inside that graph.** ``executor_role: human`` is a per-task
   guard, not a strategy: a phase-wide strategy is resolved once, then skips
   propagate through ``depends_on``.

Everything here is stated **once** and driven by both invokers: the executor under
``--exec-subagents``, and (through the ``dispatcher=`` seam) the simulated native
invoker the equivalence tests inject (``tests/harness/native_invoker.py``). Finalization is part of the loop's contract, not a caller's
courtesy: *a run that dispatched every batch and produced no summary, no
``prior_changes`` entries and no completed phase is a **failed** run, not a partial
one.*

**One job per module.** This module is the loop: :class:`WriteBatchScheduler`,
its result and :func:`run_write_phase`. The helpers both legs share live in seven
modules below it, lowest first: ``commit_write_guard``, ``check_records``,
``verification_lines``, ``human_task_plan``, ``stop_answers``, ``batch_prompt``
and ``write_outcomes`` (docs/development/write-scheduler.md#where-the-schedulers-helpers-live).
A batch's records are read together, and its verdict stamped, through
``batch_ledger``. The scheduler composes its collaborators over one
``write_context.RunContext``: ``write_verify.VerifyStep`` (the repository's own
check and the tracked-files census) and ``write_verify.VerifyCommand`` (the
check's runner), ``write_sweep.ContainmentSweep`` (the post-run containment
sweep and its rollback store), ``write_eta.EtaLines`` (the ``[ETA]`` lines),
``write_reports.WriteReports`` (the mirror, the report, the summary),
``write_stop.StopAccount`` (how a stop is worded and recorded),
``batch_prompt_builder.BatchPromptBuilder`` (the dispatched prompt),
``write_commit_leg.CommitGuardLeg`` (the commit write policy's leg),
``write_check_holds.CheckHolds`` (what implement's checks hold back),
``write_resume.ResumeEvidence`` (what an earlier run left for a resume),
``write_grant.WriteGrant`` (what the phase does with its one write grant) and
``write_snapshots.PreBatchSnapshots`` (each dispatch's pre-batch snapshot and
where the phase stores them) and ``write_dry_run.DryRunReport``
(``--dry-run-subagents``' report).
What a run refused before dispatch is on its result (``result.refusals``).
Every name that moved there is still readable here (:data:`_MOVED`), **for
reading only**: ``write_batch_scheduler.X`` and ``from .write_batch_scheduler
import X`` return the owner's current object, but a patch or assignment here
only shadows the name in this module and reaches no code. Patch a moved name
where it lives; ``tests/test_write_batch_scheduler_moved_names.py`` fails any
test that patches one here.
"""

from __future__ import annotations

import copy
import json
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field, replace
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from . import git_utils as _git_utils
from . import known_checks as _known_checks
from . import landlock_dispatch as _landlock
from . import metrics as _metrics
from . import prior_changes as _prior_changes
from . import batch_reply as _batch_reply
from . import dispatch_spawn as _dispatch_spawn
from . import runner_selection as _runner_selection
from . import commit_write_guard as _commit_write_guard  # noqa: F401 - `_MOVED` reads it
from . import check_records as _check_records
from . import verification_lines as _verification_lines
from . import human_task_plan as _human_task_plan
from . import stop_answers as _stop_answers  # noqa: F401 - `_MOVED` reads it
from . import batch_prompt as _batch_prompt
from . import write_outcomes as _write_outcomes
from . import write_context as _write_context
from . import write_verify as _write_verify
from . import write_sweep as _write_sweep
from . import write_eta as _write_eta
from . import write_reports as _write_reports
from . import write_stop as _write_stop
from . import batch_prompt_builder as _batch_prompt_builder
from . import write_commit_leg as _write_commit_leg
from . import write_check_holds as _write_check_holds
from . import write_resume as _write_resume
from . import write_grant as _write_grant
from . import write_snapshots as _write_snapshots
from . import write_dry_run as _write_dry_run
from .held_folder import write_in_plan_dir
from .cli_common import EXIT_NEEDS_HUMAN, EXIT_OK
from .batch_ledger import (
    outcome_from_verdict,
    verdict_record,
)
from .task_ledger import (
    ACCEPTED_REASON_PREFIX,  # noqa: F401 - re-exported for readers of this module
    ANSWERED_SKIP_PREFIX,  # noqa: F401 - re-exported for readers of this module
    COMPLETED_MANUAL_REASON,  # noqa: F401 - re-exported for readers of this module
    USER_DECLINED_REASON,  # noqa: F401 - re-exported for readers of this module
)
from .text_clip import (
    clip,
)
from .providers.base import (
    SANDBOX_RUNG_PLUGIN_LANDLOCK,
    host_write_posture_consent,
)
from .provider_registry import (
    get_max_concurrent_write_subagents,
    get_provider_max_concurrent,
    load_config_snapshot,
    parse_model_spec,
)
from .retry_ladder import (
    STATUS_OK,
    STATUS_REJECTED,
)
from .batch_reply import (
    WRITE_APPLIED,
    WRITE_CLEAN_FAILURE,
    WRITE_NO_OP,
    WRITE_POLICY_VIOLATION,
    batch_check_findings,
    batch_check_note,
    batch_check_words,
    check_findings_from,  # noqa: F401 - re-exported for readers of this module
    check_record,
    declined_items,
    read_check_reply,
    row_batch_check_accepted,
    row_batch_check_findings,
    row_batch_check_note,
    row_batch_check_repeats,
    row_check_findings,
)
from .task_outcome import (
    ExecutorError,
    ResultRejected,
    TaskOutcome,
)
from .task_batch import _host_ceiling
from .task_dispatch import dispatch_task
from .runner_selection import (
    profile_for_kind,
    resolve_task_runner,
)
from .subagent_tasks import (
    PHASE_BY_WRITE_KIND,
    PRIOR_CHANGES_TOKEN,  # noqa: F401 - re-exported for readers of this module
    APPLY_WRITE_KINDS,
    SHARED_ARTIFACT_WRITE_KINDS,
    WRITE_KINDS,
    declared_file_set,
    implement_output_name,
)
from .state_manager import (
    PROCESSED_LEG_EXECUTOR,
)
from .write_safety import (
    AuditLog,
    PolicyViolation,
    TaskSnapshot,
    WritePolicy,
    WriteSafetyError,
    admit_disjoint_groups,
    file_sha256,
    overlapping_pairs,
    relative_to_root,
    resolve_repo_root,
    safety_dir,
)
from .write_record import BatchFacts, BatchRecord, record_batch_facts
from .write_verdict import (
    DECLARED_NAMES_ROWS,
    PolicyFacts,
    PolicyRestore,
    VerdictRule,
    WriteFacts,
    decide,
    guard,
    jail_note,
    reason_for,
)
from . import provider_registry
from .probe_state import jail_summary_count, jail_summary_lines


__all__ = [
    "BATCH_CHECK_MARKER",
    "CHECK_FINDINGS_MARKER",
    "check_findings_line",
    "STRATEGIES",
    "STRATEGY_PAUSE",
    "STRATEGY_SKIP_CONTINUE",
    "STRATEGY_SKIP_DEPENDENTS",
    "WRITE_BATCH_REPORT_FILENAME",
    "SchedulerOptions",
    "SchedulerResult",
    "HumanTaskPlan",
    "WriteBatchScheduler",
    "answered_done_on_record",
    "answered_done_label",
    "accepted_checks_on_record",
    "accepted_checks_section",
    "accepted_upstream_checks",
    "BATCH_CHECK_ACCEPTED_MARKER",
    "accepted_findings_with_words_added",
    "BATCH_CHECK_REPEATED_MARKER",
    "batch_check_repeated_line",
    "repeated_findings_for",
    "reported_checks_on_record",
    "split_repeated_findings",
    "move_check_repeats_in_state",
    "batch_check_accepted_line",
    "check_note_clause",
    "restate_findings_problem",
    "words_added_to",
    "split_accepted_findings",
    "accepted_findings_for",
    "task_owns_the_check",
    "task_own_text",
    "BLOCKED_BY_CHECK_PREFIX",
    "bind_prior_changes",
    "last_phase_end",
    "OWN_RUN_CONTEXT_PHASES",
    "blocked_by_check_reason",
    "decomposition_graph",
    "DISPATCHED_PROMPTS_SUBDIR",
    "dispatched_prompt_name",
    "dispatched_prompt_path",
    "held_back_by_checks",
    "rerunnable_checks",
    "transitive_dependents",
    "upstream_held_check",
    "mark_no_longer_skipped",
    "persist_human_task_plan",
    "resolve_human_task_plan",
    "run_write_phase",
    "batch_check_line",
    "batch_check_section",
    "batch_check_summary",
    "declined_words",
    "item_word",
    "quoted_findings",
    "unverified_line",
    "native_stop_unverified_line",
    "native_apply_fixes_unverified_line",
    "write_result_notice",
    "verification_line",
    "verify_command_candidate",
    "with_result_contract",
    "COMMIT_GUARD_KIND",
    "ORCHESTRATOR_OUTPUT_FILENAME",
    "batch_fixes_for",
    "commit_group_files",
    "commit_guard_of",
    "commit_head7",
    "commit_protected_rule",
    "commit_recheck_failing",
    "commit_stale_line",
    "commit_stale_reason",
    "commit_stale_split",
    "load_commit_apply",
    "load_orchestrator_batches",
]


# ---------------------------------------------------------------------------
# The names that moved to the helper modules beside this one
# ---------------------------------------------------------------------------

#: Every top-level name of the modules split out of this one, by owner.
#: They are read-only re-exports (see the module docstring): reading one here
#: returns the owner's current binding, and ``dir()`` lists them. Nothing is
#: copied into this module, so a patch of the owner shows through here, and
#: this module's own code reaches each one through its owner at every call.
_MOVED: Dict[str, Tuple[str, ...]] = {
    "commit_write_guard": (
        "COMMIT_GUARD_KIND",
        "ORCHESTRATOR_OUTPUT_FILENAME",
        "batch_fixes_for",
        "commit_group_files",
        "commit_guard_of",
        "commit_head7",
        "commit_protected_rule",
        "commit_recheck_failing",
        "commit_stale_line",
        "commit_stale_reason",
        "commit_stale_split",
        "load_commit_apply",
        "load_orchestrator_batches",
    ),
    "check_records": (
        "ACCEPTED_MATCH_MIN_WORDS",
        "ACCEPTED_NOTE_FINDING_CHARS",
        "ACCEPTED_NOTE_MAX_CHECKS",
        "ACCEPTED_NOTE_MAX_FINDINGS",
        "ACCEPTED_NOTE_TITLE_CHARS",
        "BATCH_CHECK_ACCEPTED_MARKER",
        "BATCH_CHECK_MARKER",
        "BATCH_CHECK_REPEATED_MARKER",
        "BLOCKED_BY_CHECK_PREFIX",
        "CHECK_FINDINGS_MARKER",
        "CHECK_NOTE_SHOWN_CHARS",
        "_BARE_COMMAND_WORDS",
        "_FINDING_ACCEPTANCE_NOTE",
        "_FINDING_COMMAND_END",
        "_FINDING_EXIT",
        "_FINDING_FILLER",
        "_FINDING_QUOTES",
        "_FINDING_WORD",
        "_FIX_ASK",
        "_FIX_NEGATIONS",
        "_FIX_TARGET",
        "_IMPLEMENT_TASK_ID",
        "_PASS_ASK",
        "_SENTENCE_END",
        "_asks_to_fix",
        "_declined_from_a_failed_claim",
        "_finding_parts",
        "_findings_from_a_failed_claim",
        "_id_range",
        "_names_command",
        "_note_sentence",
        "_plain_words",
        "_quoted_finding",
        "_says_only",
        "accepted_checks_on_record",
        "accepted_checks_section",
        "accepted_findings_for",
        "accepted_findings_with_words_added",
        "accepted_upstream_checks",
        "batch_check_accepted_line",
        "batch_check_line",
        "batch_check_repeated_line",
        "batch_check_section",
        "batch_check_summary",
        "blocked_by_check_reason",
        "check_findings_line",
        "check_note_clause",
        "declined_words",
        "decomposition_graph",
        "held_back_by_checks",
        "item_word",
        "move_check_repeats_in_state",
        "quoted_findings",
        "repeated_findings_for",
        "reported_checks_on_record",
        "rerunnable_checks",
        "restate_findings_problem",
        "split_accepted_findings",
        "split_repeated_findings",
        "task_own_text",
        "task_owns_the_check",
        "transitive_dependents",
        "unlanded_on_record",
        "upstream_held_check",
        "words_added_to",
        "write_result_notice",
    ),
    "verification_lines": (
        "CHECKS_RAN_MAX_IDS",
        "NOTHING_RAN_TESTS",
        "PLUGIN_RAN_NO_TESTS",
        "STOP_TALLY_MAX_CHARS",
        "_NPM_PLACEHOLDER_TEST",
        "_check_task_ids_of_plan",
        "implement_checks_ran",
        "native_apply_fixes_unverified_line",
        "native_stop_unverified_line",
        "unverified_line",
        "unverified_with_report",
        "verification_line",
        "verify_command_candidate",
    ),
    "human_task_plan": (
        "HumanTaskPlan",
        "MANUAL_DECLINED_TAIL",
        "STRATEGIES",
        "STRATEGY_PAUSE",
        "STRATEGY_SKIP_CONTINUE",
        "STRATEGY_SKIP_DEPENDENTS",
        "_declined_split",
        "_deferred_reason",
        "_deferred_split",
        "answered_done_label",
        "answered_done_on_record",
        "manual_gate_head",
        "manual_gate_way_on",
        "mark_no_longer_skipped",
        "persist_human_task_plan",
        "plan_manual_gates",
        "resolve_human_task_plan",
        "set_aside_by_plan",
    ),
    "stop_answers": (
        "FailedAnswerable",
        "HALF_APPLIED_LEFT_CLAUSE",
        "HALF_APPLIED_PREFIX",
        "HEADLINE_BESIDE_SECTION_KEY",
        "NATIVE_REFUSED_PREFIX",
        "OUTSIDE_REFUSAL_WORDS",
        "STOP_HEADLINE_LABEL_CAPS",
        "STOP_HEADLINE_QUOTE_MIN",
        "UNLANDED_REASON",
        "_HEADLINE_ANSWER",
        "_accounting_line",
        "_native_stop_facts",
        "answers_cover",
        "check_kept_on_resume",
        "compose_resume_why",
        "compose_stop_answers",
        "executor_check_stamp",
        "fit_stop_headline",
        "implement_tasks_done",
        "native_resume_why",
        "native_stop_answers",
    ),
    "batch_prompt": (
        "BATCH_PROMPT_RULE",
        "CHECK_RESULT_CONTRACT",
        "CODE_WRITE_KINDS",
        "DISPATCHED_PROMPTS_SUBDIR",
        "IMPLEMENT_WHICH_CHECKS",
        "OWN_RUN_CONTEXT_PHASES",
        "RESULT_IDS_HEADING",
        "WRITE_CHECK_CONTRACT",
        "_scope_apply",
        "_state_on_disk",
        "bind_prior_changes",
        "dispatch_line",
        "dispatched_prompt_name",
        "dispatched_prompt_path",
        "is_check_task",
        "last_phase_end",
        "with_result_contract",
    ),
    "write_outcomes": (
        "REFUSED_SKIP_WAY_FORWARD",
        "ResumeContext",
        "already_kept",
        "check_partial_skips",
        "classify_attempt",
        "partial_skip_refusal",
        "partial_when_bytes_moved",
        "resume_why",
    ),
    "write_context": (
        "NullState",
        "Refusals",
        "RunContext",
        "_ID_KEYED_WRITE_KINDS",
        "has_state",
        "manager_or_none",
        "refusals_of",
    ),
    "write_verify": (
        "VERIFY_EXIT_NOT_RUN",
        "VERIFY_EXIT_TIMEOUT",
        "VERIFY_KILL_GRACE_S",
        "VERIFY_OUTPUT_CAP_BYTES",
        "VERIFY_REAP_S",
        "VERIFY_TAIL_CHARS",
        "VerifyCommand",
        "VerifyStep",
        "_verify_timeout_note",
        "load_finalize_tracking",
    ),
    "write_sweep": (
        "ContainmentSweep",
        "ROLLBACK_STORE_DIRNAME",
        "SWEEP_ADOPT_MAX_FILES",
        "SWEEP_MAX_FILES",
        "SWEEP_PRUNED_DIR_NAMES",
        "SWEEP_RETAIN_MAX_BYTES",
        "UndeclaredWrites",
    ),
    "write_eta": (
        "EtaLines",
    ),
    "write_reports": (
        "WRITE_BATCH_REPORT_FILENAME",
        "WriteReports",
    ),
    "write_stop": (
        "StopAccount",
    ),
    "batch_prompt_builder": (
        "BatchPromptBuilder",
    ),
    "write_commit_leg": (
        "CommitGuardLeg",
    ),
    "write_check_holds": (
        "CheckHolds",
    ),
    "write_resume": (
        "REVIEW_PHASE_BY_WRITE_KIND",
        "ResumeEvidence",
        "WRITE_FINGERPRINT_FILENAME",
        "_RESULT_TOKEN",
        "review_completed_at",
    ),
    "write_grant": (
        "WriteGrant",
        "build_jail_request",
        "checked_write_target",
    ),
    "write_snapshots": (
        "PreBatchSnapshots",
    ),
    "write_dry_run": (
        "DryRunReport",
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


def _same_batch_row(left: Dict[str, Any], right: Dict[str, Any]) -> bool:
    """Whether two ``write_batch_report.json`` rows describe the same batch.

    The items a row was materialized for (``expected_ids``) when both rows
    carry them, else the task id. An apply kind's task ids are positional
    (``apply-batch-N``): a ``--resume`` after the selection changed (a stopped
    batch's items skipped in the report) renumbers its batches, and an id
    match alone replaced the earlier run's ``apply-batch-1`` row, whose edits
    are still on disk, with a row for different items. ``implement``'s
    ``expected_ids`` is ``[task_id]``, so it is unaffected. A row without
    them (refused before any verdict, or a report older than F9) falls back
    to the id.
    """
    left_ids = left.get("expected_ids") or []
    right_ids = right.get("expected_ids") or []
    if left_ids and right_ids:
        return sorted(map(str, left_ids)) == sorted(map(str, right_ids))
    return str(left.get("task_id", "")) == str(right.get("task_id", ""))


# ---------------------------------------------------------------------------
# The write grant on the plugin-landlock rung (step 3 option (b), 2026-09-30)
# ---------------------------------------------------------------------------

def write_scope_for_kind(kind: str) -> Optional[str]:
    """The ``write_scope`` a write kind's dispatches carry, or ``None``.

    ``plan-file`` for apply-suggestions, ``tasks`` for apply-task-suggestions,
    ``repo-wide`` for apply-code-fixes and implement (on the rung since plan
    step 3b, 2026-10-02), read from the executor's one table
    (``runner_selection.WRITE_SCOPE_BY_KIND``). The scope comes from the
    phase's kind, never from the task JSON (F1 "How a dispatch receives its
    grant"). An unmapped kind gets ``None``, which the executor refuses on the
    rung rather than widening it.
    """
    return _runner_selection.WRITE_SCOPE_BY_KIND.get(kind)


def _tighter_cap(first: Optional[int], second: Optional[int]) -> Optional[int]:
    """The lower of two ``max_concurrent`` caps, ``None`` being "no cap"."""
    if first is None:
        return second
    if second is None:
        return first
    return min(first, second)


#: ``after_result``'s ``jail_denials`` as a ``landlock_dispatch.JailDenials``
#: (the executor's dataclass, or a dict in its ``to_dict()`` shape read back
#: from a record), ``None`` for a dispatch not on the rung or carrying no write
#: scope: ``_classify`` reads one type. The shared normaliser, read under this
#: name at each call.
_as_jail_denials = _landlock.as_jail_denials


# ---------------------------------------------------------------------------
# The scheduler
# ---------------------------------------------------------------------------

@dataclass
class SchedulerResult:
    """What one write phase's loop produced. ``exit_code`` is the phase's."""

    exit_code: int = EXIT_OK
    kind: str = ""
    phase: str = ""
    outcomes: List[TaskOutcome] = field(default_factory=list)
    batches_dispatched: List[int] = field(default_factory=list)
    stopped_at_batch: Optional[int] = None
    #: F4: what `driver.verify_command` did, or ``None`` when it never ran (no
    #: command configured, a markdown phase, or no batch applied). Present with a
    #: non-zero ``exit_code`` is the one shape that costs a fully applied run its
    #: completion, so it is a field on the result rather than a log line.
    verification: Optional[Dict[str, Any]] = None
    human_plan: _human_task_plan.HumanTaskPlan = field(default_factory=_human_task_plan.HumanTaskPlan)
    finalized: bool = False
    summary_file: Optional[str] = None
    report_path: Optional[str] = None
    dry_run_path: Optional[str] = None
    messages: List[str] = field(default_factory=list)
    #: ``task_id -> {sandbox_rung, jail_denials}``
    #: for a write batch that ran on a fallback rung. step 2 subtask item 3:
    #: from step 3 "a write batch's recorded outcome also names the rung:
    #: applied, failed, partial or timed out" — and ``TaskOutcome`` is the
    #: executor's row, so the scheduler's own report carries it beside that
    #: row rather than in it. Absent for a batch on codex's own sandbox or on
    #: another runner, so those reports are byte-identical to before.
    sandbox_records: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    #: #28: a ``--resume`` re-materializes only the unfinished tasks,
    #: so its reports described the resumed stretch alone and the first run's
    #: T001-T008 rows were overwritten and gone. These are the previous
    #: ``write_batch_report.json``'s task rows, read before this run replaces it
    #: (and already merged if that run was itself a resume), so the phase's
    #: report and summary cover the whole phase.
    earlier_rows: List[Dict[str, Any]] = field(default_factory=list)
    #: ``task_id -> reason`` for every task of this run that was never
    #: dispatched because the loop stopped first (racing re-run 3, 2026-10-05:
    #: two such tasks were absent from the summary, the counts and the
    #: message). Set by ``StopAccount.record_stop``; empty on a run that did not stop.
    not_run: Dict[str, str] = field(default_factory=dict)
    #: The stop, as one record: which task, what failed, who was not run and
    #: the way forward — what the summary, the status mirror and the result
    #: line's ``error`` all render from, so they cannot disagree.
    stop: Optional[Dict[str, Any]] = None
    #: ``task_id -> check task id`` for every task this run did not dispatch
    #: because it depends (transitively) on a check task that reported
    #: problems (the dependents ran on code the check had just
    #: rejected). Each is in ``not_run`` too, with
    #: :func:`blocked_by_check_reason` as its reason.
    blocked_by_check: Dict[str, str] = field(default_factory=dict)
    #: Findings of recorded checks absent from a selected task's handoff.
    #: They must still explain a hold, even after switching from the native
    #: leg, which writes no executor report rows.
    recorded_check_findings: Dict[str, List[str]] = field(default_factory=dict)
    #: The tasks this run refused before any runner started, and why
    #: (``write_context.Refusals``): read by the stop, the ``[ETA]`` lines,
    #: the summary and the mirror. Never in the report (``to_dict``).
    refusals: _write_context.Refusals = field(default_factory=_write_context.Refusals)
    #: The line saying nothing ran the repository's tests,
    #: when a code phase finished with no ``driver.verify_command`` set
    #: (:func:`unverified_line`); ``None`` when one ran, or none was owed.
    unverified: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.exit_code == EXIT_OK

    @property
    def failed(self) -> List[TaskOutcome]:
        return [o for o in self.outcomes if not o.ok]

    def check_findings(self) -> Dict[str, List[str]]:
        """``{task_id: findings}`` for every check task that finished ``ok``
        with problems, this run's and the earlier runs' rows alike, in row
        order (racing re-run 4)."""
        found: Dict[str, List[str]] = {}
        for row in self.report_rows():
            findings = row_check_findings(row)
            if row.get("status") == STATUS_OK and findings:
                found[str(row.get("task_id"))] = findings
        found.update(self.recorded_check_findings)
        return found

    def batch_check_findings(self) -> Dict[str, List[str]]:
        """``{task_id: findings}`` for every code batch that finished ``ok``
        while a check it ran on its own edits failed, this
        run's and the earlier runs' rows alike, in row order."""
        found: Dict[str, List[str]] = {}
        for row in self.report_rows():
            findings = row_batch_check_findings(row)
            if row.get("status") == STATUS_OK and findings:
                found[str(row.get("task_id"))] = findings
        return found

    def batch_check_accepted(self) -> Dict[str, Dict[str, List[str]]]:
        """``{task_id: {check id: findings}}`` for every code task that
        finished ``ok`` while its own check reported again findings the user
        accepted for a check, in row order."""
        found: Dict[str, Dict[str, List[str]]] = {}
        for row in self.report_rows():
            matched = row_batch_check_accepted(row)
            if row.get("status") == STATUS_OK and matched:
                found[str(row.get("task_id"))] = matched
        return found

    def batch_check_repeats(self) -> Dict[str, Dict[str, List[str]]]:
        """``{task_id: {check id: findings}}`` for every code task that
        finished ``ok`` while its own check reported only what a check task
        of the run reported, in row order."""
        found: Dict[str, Dict[str, List[str]]] = {}
        for row in self.report_rows():
            matched = row_batch_check_repeats(row)
            if row.get("status") == STATUS_OK and matched:
                found[str(row.get("task_id"))] = matched
        return found

    def batch_check_notes(self) -> Dict[str, str]:
        """``{task_id: note}`` for every code task that finished ``ok`` with
        an own-check note (its ``check.note``), in row order."""
        found: Dict[str, str] = {}
        for row in self.report_rows():
            note = row_batch_check_note(row)
            if row.get("status") == STATUS_OK and note:
                found[str(row.get("task_id"))] = note
        return found

    def report_rows(self) -> List[Dict[str, Any]]:
        """Every task row of the phase: earlier runs' first, this run's after.

        This run's row replaces an earlier one for the same batch, except a
        resume *skip*: that row only says "already done", and the earlier run's
        row is the one that holds what was done, so it stays (flagged
        ``from_earlier_run``). "The same batch" is :func:`_same_batch_row`'s:
        the same items, not merely the same id, because an apply kind's ids
        are positional and a resume whose selection changed hands
        ``apply-batch-1`` to other items.
        """
        current = [
            {**o.to_dict(), **self.sandbox_records.get(o.task_id, {})}
            for o in self.outcomes
        ]
        rows: List[Dict[str, Any]] = []
        stood_in: set = set()
        for earlier in self.earlier_rows:
            match = next(
                (index for index, row in enumerate(current)
                 if _same_batch_row(earlier, row)),
                None,
            )
            if match is not None and not current[match].get("skipped"):
                continue
            if match is not None:
                stood_in.add(match)
            rows.append({**earlier, "from_earlier_run": True})
        rows.extend(
            row for index, row in enumerate(current) if index not in stood_in
        )
        return rows

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_version": 1,
            "kind": self.kind,
            "phase": self.phase,
            # When this report was written, so a later `--resume` can tell
            # whether its rows belong to the current review cycle
            # (`ResumeEvidence.earlier_report_rows`); the file's mtime is the fallback for
            # a report that predates the key.
            "written_at": datetime.now().isoformat(),
            "exit": self.exit_code,
            "batches_dispatched": list(self.batches_dispatched),
            "stopped_at_batch": self.stopped_at_batch,
            "verification": self.verification,
            "finalized": self.finalized,
            "summary_file": self.summary_file,
            "human_task_strategy": self.human_plan.strategy,
            "skipped_tasks": dict(self.human_plan.skipped),
            "dependency_overrides": {
                k: list(v) for k, v in self.human_plan.overrides.items()
            },
            "pending_human_tasks": list(self.human_plan.pending),
            "accepted_tasks": dict(self.human_plan.accepted),
            "not_run_tasks": dict(self.not_run),
            "blocked_by_check": dict(self.blocked_by_check),
            **({"recorded_check_findings": self.recorded_check_findings}
               if self.recorded_check_findings else {}),
            "stop": copy.deepcopy(self.stop) if self.stop else None,
            **({"unverified": self.unverified} if self.unverified else {}),
            "tasks": self.report_rows(),
        }


#: The label of the summary-path line an ending of a run prints
#: (:meth:`WriteBatchScheduler._end_run`): a stop's summary is partial, a
#: manual gate's covers the run.
PARTIAL_SUMMARY_LINE = "Partial implementation summary"
FULL_SUMMARY_LINE = "Implementation summary"


@dataclass(frozen=True, kw_only=True)
class SchedulerOptions:
    """What one ``WriteBatchScheduler`` is built from (WRITE-5).

    The two orchestrators that drive a write phase build one and pass it
    (``WriteBatchScheduler(options)``); a test may pass the same fields as
    keywords instead. Frozen: the scheduler reads it once, in ``__init__``,
    and keeps it as ``options``.
    """

    #: Materialized write tasks (any ``batch_index`` order — sorted here).
    tasks: Sequence[Dict[str, Any]]
    #: Where results, snapshots, the audit log and both reports land.
    phase_dir: str
    #: One of ``utils.subagent_tasks.WRITE_KINDS``.
    kind: str
    #: The plan's output dir, which owns ``prior_changes.jsonl``.
    output_dir: str
    #: The pinned root (D3h). Resolved from ``anchor`` when omitted.
    repo_root: Optional[str] = None
    #: The phase's name; ``PHASE_BY_WRITE_KIND[kind]`` when omitted.
    phase: Optional[str] = None
    #: A ``StateManager``, for task statuses, override records and the
    #: phase-completed marker. Optional only so a unit test can drive the loop
    #: without one; a real phase always has one.
    state: Any = None
    #: The plan the phase works for.
    plan_file: Optional[str] = None
    #: implement's summary, and its path as the plan's back-reference names it.
    summary_file: Optional[str] = None
    summary_file_relative: Optional[str] = None
    #: What the repository root and the write policy are resolved from;
    #: ``plan_file`` when omitted.
    anchor: Optional[str] = None
    #: The host's ``max_concurrent_subagents``. ``None`` means "look it
    #: up from ``hosts/capabilities.yaml`` for the host this invocation
    #: declared" (D5b) — the same seam, with the same meaning, as
    #: ``task_batch.effective_ceiling``'s parameter of the same name.
    #: No orchestrator passes it; a caller that already knows the number
    #: still may.
    host_max: Optional[int] = None
    #: A runner every task is dispatched to, over each task's own.
    runner: Optional[str] = None
    #: ``--resume`` (``False`` for ``--fresh``).
    resume: bool = True
    #: ``--dry-run-subagents``. Renders every command, applies every
    #: admission and policy check, writes ``subagent_dry_run.json`` and starts
    #: **no** child.
    dry_run: bool = False
    #: ``--force-strategy`` and the ``--human-task`` answers.
    human_task_strategy: Optional[str] = None
    human_task_decisions: Optional[Dict[str, str]] = None
    #: How each admitted task is dispatched, called as
    #: ``dispatcher(scheduler, task, prompt, snapshot, profile, declared,
    #: batch_index=...)``. ``None`` is ``WriteBatchScheduler._dispatch_executor``,
    #: the executor under ``--exec-subagents``; no orchestrator passes another.
    #: An injected one (the equivalence tests' simulated native invoker)
    #: names itself in its ``invoker`` attribute and starts no runner, so
    #: no runner preflight decides rollback storage for it. Containment,
    #: classification and the prior-changes append are the loop's, the
    #: same for either — which is what makes "either invoker, same
    #: terminal state" a property of the code.
    dispatcher: Optional[Callable[..., TaskOutcome]] = None
    #: Whether a run whose batches all verified completes the phase.
    finalize: bool = True
    #: Where the run's lines go; ``print`` when omitted.
    log: Optional[Callable[[str], None]] = None
    #: The phase's one write target — ``write_phase_artifact()``,
    #: the plan for apply-suggestions and the tasks file for
    #: apply-task-suggestions. ``realpath``-resolved and checked at
    #: construction: it must exist, be a regular file, not be a symlink and
    #: lie under the repo root, or nothing runs. For the ``plan-file`` and
    #: ``tasks`` scopes it is the grant's target, and every task's declared
    #: set must resolve to exactly it, on every rung, before its snapshot.
    #: ``None`` for implement and apply-code-fixes (``repo-wide`` is one
    #: dir rule on the repository root, with this run's output folder on
    #: the request for the developer message, never a target); a
    #: ``plan-file``/``tasks`` phase built without one carries no grant, and
    #: the executor refuses it on the rung.
    write_target: Optional[str] = None
    #: The way forward after a stop, in this host's spelling.
    user_commands: Optional[Dict[str, str]] = None
    #: The apply batches answered ``--human-task <id>=skip`` on this resume.
    partial_skips: Optional[Sequence[str]] = None
    #: The scope policy an apply dispatch enforces, and its baseline.
    scope_policy: Optional[str] = None
    scope_baseline_id: Optional[str] = None
    #: Asked before each batch is dispatched, as ``before_batch(batch_index,
    #: tasks)``: a message refuses that batch and stops the run as any
    #: pre-dispatch refusal does (exit 3, no child started for it, nothing
    #: later dispatched); ``None`` lets it go. The apply phases pass the check
    #: that the review round their verdicts came from is still on record.
    before_batch: Optional[Callable[[int, Sequence[Dict[str, Any]]], Optional[str]]] = None


class WriteBatchScheduler:
    """Drives one write phase's batches in ``batch_index`` order (D3n).

    Built from one :class:`SchedulerOptions`, or from its fields as keywords
    (``WriteBatchScheduler(tasks=..., phase_dir=..., kind=..., output_dir=...)``),
    which is the same thing: the fields are documented there.
    """

    def __init__(
        self, options: Optional[SchedulerOptions] = None, /, **fields: Any,
    ) -> None:
        if options is None:
            options = SchedulerOptions(**fields)
        elif fields or not isinstance(options, SchedulerOptions):
            raise TypeError(
                "WriteBatchScheduler takes one SchedulerOptions, or its fields "
                "as keywords, not both"
            )
        #: What this scheduler was built from, as given (WRITE-5).
        self.options = options
        if options.kind not in WRITE_KINDS:
            raise ExecutorError(
                f"{options.kind!r} is not a write kind (known: {', '.join(WRITE_KINDS)}). "
                f"Nothing was dispatched."
            )
        self.tasks = list(options.tasks)
        self.phase_dir = str(options.phase_dir)
        self.kind = options.kind
        self.phase = options.phase or PHASE_BY_WRITE_KIND[options.kind]
        self.output_dir = str(options.output_dir)
        self.anchor = options.anchor or options.plan_file
        # An explicit root is checked the way the resolver pins one (review
        # fixes 2026-10-05): a planted `core.worktree` or a redirecting `.git`
        # refuses the phase at construction, before any snapshot or dispatch.
        self.repo_root = (
            self._checked_repo_root(options.repo_root) if options.repo_root
            else resolve_repo_root(self.anchor)
        )
        #: The run's one ``StateManager``; a run built without one (a unit
        #: test) holds a ``write_context.NullState``, which writes nothing.
        self.state = (
            options.state if options.state is not None else _write_context.NullState()
        )
        self.plan_file = options.plan_file
        self.summary_file = options.summary_file
        self.summary_file_relative = options.summary_file_relative
        # `host_max=None` means *look it up*, exactly as it does for the read
        # path's `task_batch.effective_ceiling` — never "this phase has no
        # host leg". Reading it as the latter cost the write half its host leg
        # outright: no orchestrator passes `host_max` (both construction sites are
        # keyword-complete without it), so `write_ceiling`'s host branch never
        # ran on a real invocation and every write batch report recorded a null
        # where the read half records a number. Resolved here rather than
        # per-call so `write_ceiling`, the batch report and the dry-run record
        # cannot disagree about which number bound the phase.
        self.host_max = _host_ceiling() if options.host_max is None else options.host_max
        # The phase's driver and provider legs of the same minimum, filled on
        # first use and kept as every batch's upper bound: see `_ceiling_legs`.
        self._ceiling_legs_cache: Optional[
            Tuple[int, Dict[str, Optional[int]]]
        ] = None
        # The runner each task of the batch being dispatched resolved to, and
        # what the admitted batches read: see `_batch_ceiling`.
        self._batch_runners: Dict[str, str] = {}
        self._admitted_ceilings: List[int] = []
        self._admitted_driver: Optional[int] = None
        self._admitted_limits: Dict[str, Optional[int]] = {}
        self.forced_runner = options.runner
        self.resume = options.resume
        self.dry_run = options.dry_run
        self.human_task_strategy = options.human_task_strategy
        self.human_task_decisions = dict(options.human_task_decisions or {})
        #: The dispatch seam (``SchedulerOptions.dispatcher``), an unbound callable
        #: taking this scheduler first.
        self._dispatcher: Callable[..., TaskOutcome] = (
            options.dispatcher or WriteBatchScheduler._dispatch_executor
        )
        #: True when dispatches go through the executor, which spawns runners.
        self._executor_dispatch = options.dispatcher is None
        self.finalize = options.finalize
        self.log = options.log or (lambda line: print(line))
        #: The way forward after a stop, spelled the way this host's user
        #: types it (the orchestrator builds them from the host's
        #: `next_command` template; the scheduler knows no host): `resume`,
        #: `review`, `fix`, and the two `--human-task` variants `accept` /
        #: `skip` with `{task_id}` left for the failed task. Absent (a direct
        #: invocation), the stop message names the flags instead.
        self.user_commands: Dict[str, str] = dict(options.user_commands or {})
        #: The apply batches answered ``--human-task <id>=skip``
        #: on this resume — each stopped as a partial application whose report
        #: left items out, kept as it stands, those items recorded as skipped
        #: at the user's request (:meth:`ResumeEvidence.check_partial_skips`).
        self.partial_skips: List[str] = [str(t) for t in (options.partial_skips or [])]
        #: The scope policy an apply dispatch enforces
        #: (docs/development/write-scheduler.md#scope-policy-at-the-write-seam):
        #: the orchestrator's effective one, else the round's record in
        #: ``state.json`` at dispatch.
        self.scope_policy = options.scope_policy
        self.scope_baseline_id = options.scope_baseline_id

        # The grant a write dispatch on the
        # plugin-landlock rung carries. ONE request for the whole phase — the
        # scope from the kind map, the target from the phase's own artifact —
        # never a per-task path, so nothing a task file says can widen it.
        self.write_scope = write_scope_for_kind(options.kind)
        self.write_target = _write_grant.checked_write_target(
            options.write_target, repo_root=self.repo_root, phase=self.phase,
        )
        self.policy = WritePolicy.load(self.repo_root, anchor=self.anchor)
        self.jail_request = _write_grant.build_jail_request(
            kind=self.kind, write_scope=self.write_scope, repo_root=self.repo_root,
            output_dir=self.output_dir, write_target=self.write_target,
            plan_file=self.plan_file,
        )
        self.audit = AuditLog(self.phase_dir)
        #: What the collaborators below may read about this run (WRITE-5):
        #: these same objects, never copies; `log` reaches `self.log` at each
        #: line (`_late`), so quieting it quiets them too.
        self._ctx = _write_context.RunContext(
            kind=self.kind, phase=self.phase, phase_dir=self.phase_dir,
            output_dir=self.output_dir, repo_root=self.repo_root,
            anchor=self.anchor, tasks=self.tasks, state=self.state,
            policy=self.policy, audit=self.audit, log=self._late("log"),
            summary_file=self.summary_file, dry_run=self.dry_run,
        )
        #: Serializes the per-dispatch bookkeeping (`_record_batch_effects`).
        #: With `driver.max_concurrent_write_subagents` > 1 a disjoint group runs
        #: in a thread pool, and every member reaches the SAME in-memory
        #: `StateManager` and the SAME `prior_changes.jsonl`. Both are
        #: read-modify-write, so two unsynchronized siblings would race on
        #: `state.save()`'s `os.replace` — last writer wins and a sibling's task
        #: status is silently dropped, leaving resume and the report disagreeing
        #: with what actually ran.
        self._effects_lock = threading.Lock()
        #: The commit write policy's leg (`write_commit_leg.CommitGuardLeg`): the
        #: guard's deny layer, the
        #: pre-dispatch re-check and the batches it stopped, each dispatch's
        #: watched paths. It mutates and saves the guard under `_effects_lock`.
        self._commit = _write_commit_leg.CommitGuardLeg(
            self._ctx,
            effects_lock=self._effects_lock,
            refused=self._late("_refused"),
        )
        # The apply guard's protected set joins the policy as an exact-path
        # deny layer: the pre-dispatch check and the post-run sweep below then
        # fail a batch that writes one, as for a driver.write_paths deny hit.
        self._commit.protect(self._commit.guard())
        #: ``task id -> the known check commands its prompt listed``
        #: (`BatchPromptBuilder.known_checks_section`), which its reply's
        #: ``listed`` is read against (``_listed_outcomes``).
        self._told_checks: Dict[str, List[str]] = {}
        #: The prompt each dispatch is sent and the copy kept of it
        #: (`batch_prompt_builder.BatchPromptBuilder`). The phase dir the
        #: copies go in is pinned now, before any batch of this run can
        #: replace it.
        self._prompts = _batch_prompt_builder.BatchPromptBuilder(
            self._ctx,
            plan_file=self.plan_file,
            scope_policy=self.scope_policy,
            scope_baseline_id=self.scope_baseline_id,
            told_checks=self._told_checks,
        )
        try:
            self._prompts.pinned_phase_dir()
        except OSError:
            pass  # named on the first prompt kept, with that task's id
        self.invoker = "executor" if options.dispatcher is None else str(options.dispatcher.invoker)
        #: What implement's checks hold back and whether a resumed one runs
        #: again (`write_check_holds.CheckHolds`), stateless: a hold is
        #: recorded on the result.
        self._checks = _write_check_holds.CheckHolds(
            self._ctx,
            invoker=self.invoker,
            task_by_id=self._late("_task_by_id"),
        )
        #: `driver.verify_command`'s runner (`write_verify.VerifyCommand`).
        self._verify_command = _write_verify.VerifyCommand(self._ctx)
        #: The repository's own check and the tracked-files census
        #: (`write_verify.VerifyStep`), stateless; its `state.json` writes
        #: take `_effects_lock` above.
        self._verify = _write_verify.VerifyStep(
            self._ctx,
            effects_lock=self._effects_lock,
            finalize=self.finalize,
            task_by_id=self._late("_task_by_id"),
            unverified_text=self._late("_unverified_text"),
            set_stop_headline=self._late("_stop.set_stop_headline"),
            run_verify_command=self._late("_verify_command.run"),
        )
        #: How a stop is worded and recorded on the result
        #: (`write_stop.StopAccount`), stateless; its one `state.json` write
        #: takes `_effects_lock` above.
        self._stop = _write_stop.StopAccount(
            self._ctx,
            effects_lock=self._effects_lock,
            user_commands=self.user_commands,
            task_by_id=self._late("_task_by_id"),
            dependents_of=self._late("_checks.dependents_of"),
            keep_partial_clause=self._late("_keep_partial_clause"),
            unapplied_words=self._late("_unapplied_words"),
            restamp_check_trees=self._late("_checks.restamp_check_trees"),
            tree_fingerprint=self._late("_checks.tree_fingerprint"),
            started_a_runner=self._late("_started_a_runner"),
            mirror_snapshot=self._late("_reports.mirror_snapshot"),
            mirror_status=self._late("_reports.mirror_status"),
        )
        #: The run's `[ETA]` counts and lines (`write_eta.EtaLines`): the
        #: dispatch walk sets what it will count, the batch bookkeeping marks
        #: each task under `_effects_lock`, and every ending closes them once.
        self._eta = _write_eta.EtaLines(
            self._ctx,
            ran_out_of_time=self._late("_stop.ran_out_of_time"),
            started_a_runner=self._late("_started_a_runner"),
        )
        #: What an earlier run of the phase left, as this resume reads it
        #: (`write_resume.ResumeEvidence`): done results, the inputs
        #: binding, the earlier report's rows and the `--human-task
        #: <batch>=skip` answers it can keep, refused or kept.
        self._evidence = _write_resume.ResumeEvidence(
            self._ctx,
            resume=self.resume,
            partial_skips=self.partial_skips,
            eta=self._eta,
            commit_guard=self._late("_commit.guard"),
        )
        #: Task ids for which a terminal (`completed`) audit line has been
        #: written, so `_audit_terminal` can close out a dispatch that never
        #: reached `_classify` without ever double-recording one that did.
        self._audited: set = set()
        #: The post-run containment sweep and its rollback store
        #: (`write_sweep.ContainmentSweep`): each in-flight dispatch's census,
        #: declared set and retained bytes, under the sweep's own lock.
        self._sweep = _write_sweep.ContainmentSweep(self._ctx)
        #: ``{spec: version}`` for every distinct runner this run actually
        #: preflighted (F12), populated as ``_dispatch_executor`` dispatches —
        #: the read path fills the same-shaped field from
        #: ``_preflight_batch_runners``; the write path preflights inline, per
        #: dispatch, and this is where its return value was being discarded.
        self._runner_versions: Dict[str, str] = {}
        #: Plan step 3, all keyed by task id. The rung each
        #: executor dispatch ran on (``None``: codex's own sandbox or another
        #: runner) — what names the rung on the batch's line, its verdict and
        #: the report whatever the outcome, a timeout included.
        self._dispatch_rungs: Dict[str, Optional[str]] = {}
        #: What the phase does with its one grant (`write_grant.WriteGrant`):
        #: the declared-set check, the runner preflight under the request and
        #: the rung it recorded, the replaced-target check and the jail's
        #: denials, with their per-dispatch records.
        self._grant = _write_grant.WriteGrant(
            self._ctx,
            write_scope=self.write_scope,
            write_target=self.write_target,
            jail_request=self.jail_request,
            dispatch_rungs=self._dispatch_rungs,
        )
        #: Each dispatch's pre-batch snapshot, its rollback point, and where
        #: the phase stores them (`write_snapshots.PreBatchSnapshots`).
        self._snapshots = _write_snapshots.PreBatchSnapshots(
            self._ctx,
            resume=self.resume,
            executor_dispatch=self._executor_dispatch,
            grant=self._grant,
            evidence=self._evidence,
            runner_for=self._late("_runner_for"),
        )
        #: What reading each reply's ``listed`` against ``_told_checks`` gave.
        self._listed_outcomes: Dict[str, Any] = {}
        #: ``task id -> its outcomes so far`` (:meth:`_remember_outcome`).
        self._recorded_outcomes: Dict[str, List[TaskOutcome]] = {}
        #: Whether this run stamped implement's start (:meth:`_mark_implement_started`).
        self._implement_started_marked = False
        #: The run's mirror, report, summary and plan reference
        #: (`write_reports.WriteReports`), read-only over the result; built
        #: last, over the records above that it reads.
        self._reports = _write_reports.WriteReports(
            self._ctx,
            plan_file=self.plan_file,
            summary_file_relative=self.summary_file_relative,
            write_target=self.write_target,
            invoker=self.invoker,
            host_max=self.host_max,
            user_commands=self.user_commands,
            sweep=self._sweep,
            eta=self._eta,
            runner_versions=self._runner_versions,
            dispatch_rungs=self._dispatch_rungs,
            resume_answered_ids=self._late("_evidence.resume_answered_ids"),
            resume_kept_rows=self._late("_evidence.resume_kept_rows"),
            ceiling_record=self._late("_ceiling_record"),
            check_findings_fate=self._late("_checks.check_findings_fate"),
            task_by_id=self._late("_task_by_id"),
            started_a_runner=self._late("_started_a_runner"),
            accounting=self._late("_stop.accounting"),
            manual_gates=self._late("_stop.manual_gates"),
        )
        #: `--dry-run-subagents`' report (`write_dry_run.DryRunReport`).
        self._dry_run_report = _write_dry_run.DryRunReport(
            self._ctx,
            host_max=self.host_max,
            grant=self._grant,
            prompts=self._prompts,
            batch_runners_and_ceiling=self._late("_batch_runners_and_ceiling"),
            render_argv=self._late("_render_argv"),
            ceiling_record=self._late("_ceiling_record"),
        )

    def _late(self, name: str) -> Callable[..., Any]:
        """``self.<name>(...)`` as it is bound when called, for a collaborator
        to call back: an instance patch of *name* applies to it too. A dotted
        *name* (``"_stop.accounting"``) reaches a collaborator's method the
        same way, each part looked up at each call."""
        parts = name.split(".")

        def call(*args: Any, **kwargs: Any) -> Any:
            target: Any = self
            for part in parts:
                target = getattr(target, part)
            return target(*args, **kwargs)

        return call

    # -- the phase's folders and root ----------------------------------

    @property
    def safety_dir(self) -> str:
        """Where this phase's pre-batch snapshots, rollback store and audit
        log live (``write_safety.safety_dir``): the phase dir, or the
        out-of-grant directory a jailed repo-wide run claimed."""
        return safety_dir(self.phase_dir)

    @staticmethod
    def _checked_repo_root(raw: str) -> str:
        """``raw`` ``realpath``-resolved, refused (exit 3) when
        ``git_utils.pin_repo_root`` says git's view of that tree is
        redirected — the check :func:`resolve_repo_root` makes for a root it
        derives itself, applied to one a caller hands in."""
        root = os.path.realpath(str(raw))
        _pinned, problem = _git_utils.pin_repo_root(root)
        if problem:
            raise WriteSafetyError(
                f"Refusing the repository root {root}: {problem}. Nothing was "
                f"dispatched."
            )
        return root

    # -- ceilings -------------------------------------------------------

    def write_ceiling(self) -> int:
        """The effective write parallelism (D3h/D3i), and why it is what it is.

        D3i's three-way minimum with the write gate substituted for the read one:
        ``driver.max_concurrent_write_subagents`` (default 1) × the runner
        provider's own ``max_concurrent`` (claude-code and cursor-agent ship 2) ×
        the host's own ceiling — then **pinned to 1** for a shared-artifact phase
        regardless of all three, because that is the batchers' own invariant
        (apply-suggestions/apply-task-suggestions edit one file), enforced here
        rather than trusted from them.

        The provider leg is not optional: raising the driver key above a
        provider's cap would otherwise over-subscribe it on the parallelizable
        implement/code-fix batches, which is exactly the ceiling the user did not
        set and cannot see. Neither is the host leg, and it reaches here through
        ``__init__``'s lookup rather than through a caller: ``self.host_max`` is
        ``None`` only when the capability data could not be read at all, the same
        partial-install case ``_host_ceiling`` bounds nothing over.

        This is the phase's number, over every task's runner, resolved once
        (:meth:`_ceiling_legs`). Each batch is admitted under it or lower
        (:meth:`_batch_ceiling`).
        """
        configured, provider_limits = self._ceiling_legs()
        candidates = [configured]
        if self.host_max is not None:
            candidates.append(int(self.host_max))
        limits = [
            limit for limit in provider_limits.values()
            if limit is not None
        ]
        if limits:
            # The *min* across providers, where the read path's
            # `effective_ceiling` takes the max: that path holds a per-provider
            # semaphore underneath the global gate, so a permissive group ceiling
            # is still bounded per provider. A write group has no second gate —
            # this number is the only thing standing between a mixed batch and an
            # over-subscribed provider — so it binds to the tightest cap.
            candidates.append(min(limits))
        ceiling = max(1, min(candidates))
        if self.kind in SHARED_ARTIFACT_WRITE_KINDS:
            return 1
        return ceiling

    def provider_write_limits(self) -> Dict[str, Optional[int]]:
        """``max_concurrent`` per provider this phase's runners resolve to (D3i).

        Resolution mirrors the dispatch path (``--runner`` override, else each
        task's own chain), and it is computed identically for both invokers so
        the executor and the simulated native invoker admit the same groups. A
        spec naming a provider with no configured cap contributes ``None``, which
        is "no provider leg", never zero. Read from :meth:`_ceiling_legs`, so it
        is the map :meth:`write_ceiling` was computed from.
        """
        return dict(self._ceiling_legs()[1])

    def _ceiling_legs(self) -> Tuple[int, Dict[str, Optional[int]]]:
        """``driver.max_concurrent_write_subagents`` and the provider caps, once.

        Resolved on the first call, every task's runner from one config
        snapshot, and kept as ``host_max`` is in ``__init__``: the phase's upper
        bound. :meth:`_batch_ceiling` reads the current values for each batch
        and binds to any lower one, so a config change can lower a later
        batch's ceiling but never raise it above this one
        (``docs/development/write-safety.md``). A failed resolution caches
        nothing and raises again on the next call.
        """
        if self._ceiling_legs_cache is None:
            snapshot = load_config_snapshot(anchor=self.anchor)
            configured = get_max_concurrent_write_subagents(snapshot=snapshot)
            specs = [self.forced_runner] if self.forced_runner else [
                resolve_task_runner(task, snapshot=snapshot) for task in self.tasks
            ]
            self._ceiling_legs_cache = (
                configured, self._provider_limits(specs, snapshot=snapshot),
            )
        return self._ceiling_legs_cache

    def _provider_limits(
        self, specs: Iterable[str], *, snapshot: Any,
    ) -> Dict[str, Optional[int]]:
        """``max_concurrent`` of each provider ``specs`` name, from ``snapshot``."""
        limits: Dict[str, Optional[int]] = {}
        for spec in dict.fromkeys(specs):
            provider_name, _ = parse_model_spec(spec, snapshot=snapshot)
            limits[provider_name] = get_provider_max_concurrent(
                provider_name, snapshot=snapshot
            )
        return limits

    def _batch_runners_and_ceiling(
        self, tasks: Sequence[Dict[str, Any]],
    ) -> Tuple[Dict[str, str], int]:
        """One batch's runners (:meth:`_resolve_batch_runners`) and the ceiling
        it is admitted under (:meth:`_batch_ceiling`), from one config snapshot.

        The snapshot is loaded when the batch starts, so it sees an edit made
        since the last batch, and both read it: one config load, so one git
        discovery, per batch however many tasks it holds. The snapshot stands
        for ``self.anchor``, so the reads take it alone, never beside an anchor
        (``provider_registry.require_one_config_source``).
        """
        snapshot = load_config_snapshot(anchor=self.anchor)
        runners = self._resolve_batch_runners(tasks, snapshot=snapshot)
        return runners, self._batch_ceiling(runners, snapshot=snapshot)

    def _resolve_batch_runners(
        self, tasks: Sequence[Dict[str, Any]], *, snapshot: Any,
    ) -> Dict[str, str]:
        """The runner spec of each of one batch's tasks, by task id, resolved once.

        ``--runner``, else the task's own chain, read from the batch's config
        ``snapshot``: the configuration or the installed CLIs may have changed
        since an earlier batch. The batch's ceiling, the rollback-storage
        preflight and the dispatch all read this map (:meth:`_runner_for`), so
        they name one runner per task and the ceiling binds the providers that
        really run.
        """
        return {
            str(task.get("task_id", "")):
                self.forced_runner or resolve_task_runner(task, snapshot=snapshot)
            for task in tasks
        }

    def _runner_for(self, task: Dict[str, Any]) -> str:
        """The runner ``task`` dispatches on: its batch's resolution
        (:meth:`_resolve_batch_runners`), else resolved now (a task outside the
        batch being dispatched)."""
        if self.forced_runner:
            return self.forced_runner
        spec = self._batch_runners.get(str(task.get("task_id", "")))
        if spec is None:
            spec = resolve_task_runner(task, anchor=self.anchor)
        return spec

    def _batch_ceiling(self, runners: Mapping[str, str], *, snapshot: Any) -> int:
        """The ceiling one batch is admitted under: never above :meth:`write_ceiling`.

        The phase's number is the upper bound. Under it the driver key and the
        ``max_concurrent`` of each provider this batch's ``runners`` name (the
        specs it dispatches on) are read again, so a lower value in the current
        configuration, or a task that now resolves to a provider with a tighter
        cap, binds this batch; a raised value leaves it at the phase's number.
        Every one of these values comes from the batch's config ``snapshot``
        (:meth:`_batch_runners_and_ceiling`), never a load per key or per
        provider. Called on the loop's thread before the batch's workers
        start; what it read is kept for :meth:`_ceiling_record`.
        """
        phase = self.write_ceiling()
        configured = get_max_concurrent_write_subagents(snapshot=snapshot)
        limits = self._provider_limits(runners.values(), snapshot=snapshot)
        caps = [limit for limit in limits.values() if limit is not None]
        ceiling = max(1, min([phase, configured, *caps]))
        self._admitted_ceilings.append(ceiling)
        self._admitted_driver = configured if self._admitted_driver is None else min(
            self._admitted_driver, configured
        )
        for provider, limit in limits.items():
            self._admitted_limits[provider] = _tighter_cap(
                self._admitted_limits.get(provider), limit
            )
        return ceiling

    def _ceiling_record(self) -> Tuple[int, int, Dict[str, Optional[int]]]:
        """``(effective, driver, providers)`` for the batch report and the
        dry-run record, from what the batches were admitted under.

        ``effective`` is the highest ceiling a batch was admitted under, or
        :meth:`write_ceiling` when none was. The driver value and each
        provider's cap are the tightest the phase's resolution or any batch
        read, and the providers include every one a batch's runners resolved
        to. So when a config change lowered a later batch, the legs can sit
        below ``effective``.
        """
        configured, phase_limits = self._ceiling_legs()
        limits = dict(phase_limits)
        for provider, limit in self._admitted_limits.items():
            limits[provider] = _tighter_cap(limits.get(provider), limit)
        if self._admitted_driver is not None:
            configured = min(configured, self._admitted_driver)
        effective = (
            max(self._admitted_ceilings) if self._admitted_ceilings
            else self.write_ceiling()
        )
        return effective, configured, limits

    # -- ordering -------------------------------------------------------

    def batches(self) -> List[Tuple[int, List[Dict[str, Any]]]]:
        """The phase's tasks grouped by ascending ``batch_index``."""
        buckets: Dict[int, List[Dict[str, Any]]] = {}
        for task in self.tasks:
            buckets.setdefault(int(task.get("batch_index", 0)), []).append(task)
        return [(index, buckets[index]) for index in sorted(buckets)]

    # -- late prior-changes binding (D3n) -------------------------------

    def _known_checks_report(
        self, max_chars: Optional[int] = None,
    ) -> Optional[Tuple[str, bool]]:
        """What this phase's batches reported about the known checks they
        were told to run, and whether one ran (:func:`known_checks.checks_report`),
        for the tests line; ``None`` for every other kind, or with no check
        known. Never fatal."""
        if self.kind != "apply_code_fixes":
            return None
        try:
            state = _write_context.manager_or_none(self.state)
            if state is None:
                state = _known_checks.read_state(self.output_dir)
            return _known_checks.checks_report(
                self._prompts.known_checks(), state, self.tasks,
                **({} if max_chars is None else {"max_chars": max_chars}),
            )
        except Exception:  # noqa: BLE001 - advisory
            return None

    def _unverified_text(self, *, stop: bool = False) -> str:
        """The tests line this code phase owes with no ``driver.verify_command``
        (:func:`unverified_line`), led by what ran: implement's
        tasks' checks (:func:`implement_checks_ran`), apply-code-fixes' known
        checks (:meth:`_known_checks_report`; at a stop only when a batch
        ran one, cut to :data:`STOP_TALLY_MAX_CHARS`, so the stop's remedy
        and answers keep their room beside it in the bounded ``error``)."""
        if self.kind == "implement":
            return _verification_lines.unverified_line(self.repo_root, ran=self._implement_checks_ran())
        report = self._known_checks_report(_verification_lines.STOP_TALLY_MAX_CHARS if stop else None)
        if stop and not (report and report[1]):
            # A stop's line names the tally only to lead with what ran.
            return _verification_lines.unverified_line(self.repo_root)
        return _verification_lines.unverified_with_report(self.repo_root, report)

    def _implement_checks_ran(self) -> Optional[str]:
        """:func:`implement_checks_ran` over the state this run holds, the
        check tasks read off this run's tasks and the plan's task list (a
        resume's batches leave out the tasks an earlier run finished)."""
        try:
            state = getattr(self.state, "state", None)
            if not isinstance(state, dict):
                state = _known_checks.read_state(self.output_dir)
            checks = {
                str(task.get("task_id") or "")
                for task in self.tasks
                if isinstance(task, dict) and not declared_file_set(task)
                and task.get("executor_role") != "human" and not task.get("is_human")
            }
            if self.plan_file:
                checks |= _verification_lines._check_task_ids_of_plan(Path(self.plan_file))
            return _verification_lines.implement_checks_ran(state, checks)
        except Exception:  # noqa: BLE001 - advisory: the line still stands
            return None

    # -- the loop -------------------------------------------------------

    def run(self) -> SchedulerResult:
        """Schedule the phase. Returns the phase's :class:`SchedulerResult`.

        The rollback store is staging, not an artifact: every path it made
        reversible has its own copy under ``{phase}/pre_batch/{task_id}/files/``
        by the time a dispatch is classified, so it is dropped on every exit —
        success, stop or crash — rather than leaving up to
        ``SWEEP_RETAIN_MAX_BYTES`` of the repository behind in the plan dir.
        """
        jail_lines_before = self._jail_line_count()
        try:
            result = self._run()
            self._evidence.report_resume_tally(result)
            return result
        except WriteSafetyError as exc:
            # A batch can replace the phase path after dispatch. Trusted
            # discovery refuses it; report a human-needed stop without reading
            # or writing through that replacement to produce more artifacts.
            # An ending too, so the `[ETA]` lines say it.
            self._eta.close(self._eta.run_result)
            return SchedulerResult(
                kind=self.kind, phase=self.phase, exit_code=EXIT_NEEDS_HUMAN,
                messages=[f"Rollback safety refusal: {exc.message} The phase was not completed."],
            )
        except KeyboardInterrupt:
            # A foreground run's Ctrl-C (a detached worker's signal goes
            # through `metrics.aborted_eta_line` instead).
            self._eta.close(self._eta.run_result, verb="interrupted")
            raise
        except Exception:
            self._eta.close(self._eta.run_result)
            raise
        finally:
            # Whatever the ending, no abort may close lines a later run owns.
            _metrics.close_eta_run(self._eta.abort_line)
            try:
                self._sweep.report_store_utilization()
                self._sweep.discard_store()
            except WriteSafetyError as exc:
                self.log(f"[write-subagents] rollback evidence retained: {exc.message}")
            self._repeat_jail_lines(jail_lines_before)

    @staticmethod
    def _jail_line_count() -> int:
        return jail_summary_count()

    def _repeat_jail_lines(self, before: int) -> None:
        """Repeat this phase's ``[JAIL_DENIED]`` / ``[CODEX_HOME_CHECK]`` lines
        at its close: write batches dispatch through ``dispatch_task`` directly,
        so ``run_tasks``' own closing summary never runs for them, and a change
        to ``$CODEX_HOME`` outlives the run."""
        for line in jail_summary_lines(before):
            self.log(f"[write-subagents] closing summary: {line}")

    def _run(self) -> SchedulerResult:
        result = SchedulerResult(kind=self.kind, phase=self.phase)
        ordered = self.batches()
        if self.resume and not self.dry_run:
            result.earlier_rows = self._evidence.earlier_report_rows()

        # 0. Advisory only, never a mutation: name any result file left behind
        # by an earlier naming scheme before the batches that matter start.
        self._evidence.warn_stale_result_files()

        # 1. Human tasks: resolve once, apply as a graph walk, persist.
        result.human_plan = _human_task_plan.resolve_human_task_plan(
            self.tasks,
            strategy=self.human_task_strategy,
            decisions=self.human_task_decisions,
            check_findings_ids=(
                _check_records.rerunnable_checks(self.state) if self.kind == "implement" else ()
            ),
            graph=(
                _check_records.decomposition_graph(self.tasks, self.state)
                if self.kind == "implement" else None
            ),
        )
        if self.kind == "implement":
            try:
                recorded = dict(self.state.get_all_task_statuses())
            except Exception:  # noqa: BLE001 - a state fake without the map
                recorded = {}
            _human_task_plan.mark_no_longer_skipped(
                result.human_plan,
                [str(task.get("task_id", "")) for task in self.tasks],
                recorded,
            )
        if not self.dry_run:
            # A dry run resolves the plan (the report says what *would* be
            # skipped) but never persists it: D3l's contract is "no child
            # started, nothing else changed", and persisting would pin the
            # strategy, mark human tasks skipped and record dependency overrides
            # in `state.json` for a run that never dispatched anything.
            self._persist_human_plan(result.human_plan)
        if self.kind == "implement":
            # The answers an earlier run recorded for tasks this resume did
            # not materialize (an accepted failure, a manual task answered
            # done): in no bucket otherwise, and the account's total shrank.
            accepted, completed_manual = _human_task_plan.answered_done_on_record(
                self.state,
                exclude=[str(task.get("task_id", "")) for task in self.tasks],
            )
            for task_id, reason in accepted.items():
                result.human_plan.accepted.setdefault(task_id, reason)
            for task_id in completed_manual:
                if task_id not in result.human_plan.completed:
                    result.human_plan.completed.append(task_id)

        if result.human_plan.pending:
            # Fail closed: an unanswered human task is exactly the D6 "needs a
            # human" condition, and dispatching around it would run code tasks
            # against unmet preconditions.
            result.exit_code = EXIT_NEEDS_HUMAN
            # A stop says nothing ran the tests too. No
            # `[ETA]` baseline exists yet, so there is nothing to close.
            return self._end_run(
                result, lambda: self._pending_human_message(result.human_plan),
                close_eta=False, check_lines=False,
            )

        # What this run will dispatch, counted as the loop below decides it: the
        # orchestrator's line counted every task a resume took up, so "4 task(s) to dispatch" preceded
        # "dispatched 0".
        # The `[ETA]` total starts from the
        # same walk, so the two never disagree.
        if self.kind == "implement":
            self.log(self._dispatch_preview(ordered, result))

        # 2. Dry run: full preflight, zero dispatch.
        if self.dry_run:
            result.dry_run_path = self._dry_run_report.write(ordered, result.human_plan)
            result.messages.append(
                f"[dry-run-subagents] {result.dry_run_path} — every command "
                f"rendered, no child started, nothing changed."
            )
            # No report: `subagent_dry_run.json` IS the dry run's artifact, and
            # writing the zero-outcome batch reports here would clobber a real
            # run's `write_batch_report.json` / `subagent_batch_report.json`.
            return result

        # A `--human-task <batch>=skip` answer is checked
        # against the batch's stopped verdict and the bytes on disk before
        # anything is dispatched; one that cannot apply stops the run here.
        refusals = self._evidence.check_partial_skips()
        if refusals:
            result.exit_code = EXIT_NEEDS_HUMAN
            result.messages.extend(refusals)
            # On the record the tool routes read, so the
            # result line names the refusal and the refused answer is not
            # offered again from the stop it answered.
            self._stop.record_answer_refusal(result, self._evidence.refused_skips)
            return result

        # 3. The batches, in order, each verified before the next is dispatched.
        # Mirrored once before the first dispatch so `progress.step` reads
        # `applying` for the whole stretch rather than only from the first
        # *finished* task — the in-batch mirror runs after a dispatch returns,
        # and a long first batch is exactly when the step matters (F4).
        self._eta.start(result)
        self._reports.mirror_status(result)
        for batch_index, batch_tasks in ordered:
            self._checks.hold_on_recorded_checks(batch_tasks, result)
            runnable = [
                task for task in batch_tasks
                if not result.human_plan.is_skipped(str(task.get("task_id", "")))
                and str(task.get("task_id", "")) not in result.human_plan.accepted
                and str(task.get("task_id", "")) not in result.blocked_by_check
                and task.get("executor_role") != "human"
            ]
            if not runnable:
                continue
            try:
                guard = self.options.before_batch
                refused = guard(batch_index, runnable) if guard is not None else None
                if refused:
                    raise ExecutorError(refused)
                outcomes = self._run_batch(batch_index, runnable, result)
            except ExecutorError as exc:
                # D3k rung 1: a pre-dispatch refusal (a missing binary, an
                # unauthenticated runner, a profile the adapter cannot serve —
                # `preflight_runner` raising `RunnerRejected`) fails the batch
                # *here*, exactly like every other stop. Left to propagate it
                # reached the dispatcher's generic handler as a traceback and exit
                # 1, so the run produced no `write_batch_report.json`, no
                # `.status.json` mirror and none of the exit-3 wording that names
                # the fix — the read path has converted the same exception to
                # `failure.exit_code` since D3b.
                result.stopped_at_batch = batch_index
                result.exit_code = int(exc.exit_code or EXIT_NEEDS_HUMAN)
                self._stop.record_stop(result, batch_index, [], refusal=exc.message)
                # The partial summary only when an earlier batch really
                # applied something: it is that run's account (D3n), and an
                # empty one for a refusal on the first dispatch would claim a
                # run that never started.
                self._end_run(
                    result,
                    lambda exc=exc, batch_index=batch_index: (
                        self._stop.refusal_message(exc, batch_index, result)
                    ),
                    stopped=True,
                    summary=PARTIAL_SUMMARY_LINE if result.outcomes else None,
                )
                self._reports.record_refusal(exc, batch_index)
                return result
            result.outcomes.extend(outcomes)
            result.batches_dispatched.append(batch_index)
            # A check that reported problems keeps every task that depends on
            # it from running; the tasks that do not depend on
            # it go on.
            self._checks.block_dependents_of_checks(outcomes, result)
            self._verify.record_batch_tracking(result)
            self._reports.mirror_status(result)
            # A batch the commit re-check
            # stopped was never dispatched and the loop goes on past it.
            stale = self._commit.stale
            stopping = [o for o in outcomes if o.task_id not in stale]
            if any(o.stops_the_loop for o in stopping) or any(
                not o.ok for o in stopping
            ):
                result.stopped_at_batch = batch_index
                result.exit_code = EXIT_NEEDS_HUMAN
                self._stop.record_stop(
                    result, batch_index, [o for o in stopping if not o.ok],
                )
                # The partial summary is the cancellation's own record (D3n,
                # instructions/implement.md): `_finalize` never runs on this
                # path, so without it the `## Cancelled` section would be
                # unreachable and `--resume` would have no account of what the
                # stopped run applied. The phase is still NOT completed and the
                # plan-side reference is still NOT inserted.
                return self._end_run(
                    result,
                    lambda batch_index=batch_index, outcomes=outcomes: (
                        self._stop.stop_message(batch_index, outcomes, result)
                    ),
                    stopped=True, summary=PARTIAL_SUMMARY_LINE,
                )

        # 4. The tasks a check with findings kept from running: the phase is
        # not complete while they are unrun, so it ends needing a human, the
        # way a stop does — after every task that could run has run, and
        # with no finalization (no verify command, no completion record).
        if result.blocked_by_check:
            result.exit_code = EXIT_NEEDS_HUMAN
            self._stop.record_check_block(result)
            return self._end_run(
                result, lambda: self._stop.check_block_message(result),
                summary=PARTIAL_SUMMARY_LINE,
            )

        # 4b. A run that
        # dispatched nothing because every code task left waits on a manual
        # task not recorded done is not a finished implement. It stops for
        # the user, naming the manual task and the resume that records it.
        gates = self._stop.manual_gate(result)
        if gates is not None:
            return self._stop_on_manual_gate(result, gates)

        # 5. Finalization is part of the contract, not the caller's courtesy.
        # It closes the `[ETA]` lines ("phase complete"), runs the
        # verification and writes the summary itself.
        if self.finalize:
            self._finalize(result)
        return self._end_run(result, close_eta=False, unverified=False)

    def _end_run(
        self,
        result: SchedulerResult,
        ending: Optional[Callable[[], List[str]]] = None,
        *,
        close_eta: bool = True,
        eta_why: str = "",
        unverified: bool = True,
        check_lines: bool = True,
        stopped: bool = False,
        summary: Optional[str] = None,
    ) -> SchedulerResult:
        """End :meth:`_run` with a report, in the one order every ending keeps.

        1. The ``[ETA]`` lines close (*close_eta*, with *eta_why*): every
           ending short of completion says so, rather than leaving
           "~0m 37s remaining" standing.
        2. The "nothing ran the tests" note (*unverified*,
           ``VerifyStep.note_unverified_on_stop``) is set before the summary is
           written, so the summary's Verification line and the stop's
           headline say it too.
        3. The summary, when the ending names one: *summary* is the label of
           its line, and only a plan with a summary file gets one.
        4. The messages, in order: the ``[CHECK_FINDINGS]`` and batch-check
           lines (*check_lines*, *stopped*; read after the summary, which
           they point at), the note, the ending's own lines (*ending*), the
           summary's path.
        5. The report and the status mirror.

        A dry run never reaches here: its record is ``subagent_dry_run.json``.
        """
        if close_eta:
            self._eta.close(result, why=eta_why)
        unverified_lines = self._verify.note_unverified_on_stop(result) if unverified else []
        if summary and self.summary_file:
            result.summary_file = self._reports.write_summary(result)
        if check_lines:
            result.messages.extend(self._checks.check_findings_lines(result, stopped=stopped))
            result.messages.extend(self._checks.batch_check_lines(result))
        result.messages.extend(unverified_lines)
        if ending is not None:
            result.messages.extend(ending())
        if summary and result.summary_file:
            result.messages.append(f"{summary}: {result.summary_file}")
        result.report_path = self._reports.write_report(result)
        self._reports.mirror_status(result)
        return result

    def _dispatch_preview(
        self, ordered: Sequence[Tuple[int, List[Dict[str, Any]]]],
        result: SchedulerResult,
    ) -> str:
        """The ``Organized into …`` line for what this run will dispatch
        (:meth:`_dispatch_walk`), which also sets the ``[ETA]`` line's task
        set (``EtaLines.scope``): the tasks the line counts. A walk
        that fails counts every task, and the ``[ETA]`` total with it."""
        walk = self._dispatch_walk(ordered, result)
        if walk is None:
            self._eta.scope = None
            self._eta.walk_left = {}
            return _batch_prompt.dispatch_line(
                len([1 for _i, b in ordered if b]),
                sum(len(b) for _i, b in ordered),
            )
        batches, picked_ids, waiting = walk
        self._eta.scope = set(picked_ids)
        return _batch_prompt.dispatch_line(batches, len(picked_ids), waiting=waiting)

    def _dispatch_walk(
        self, ordered: Sequence[Tuple[int, List[Dict[str, Any]]]],
        result: SchedulerResult,
    ) -> Optional[Tuple[int, List[str], List[str]]]:
        """``(batches, task ids, waiting ids)`` this run will dispatch, or
        ``None`` when the walk fails.

        The line
        the orchestrator printed counted every task a resume took up, so
        01b and 01c read "4 task(s) to dispatch" before "dispatched 0" and
        fix 02 read 4 for the 2 it ran. This walks the batches in the loop's
        order with the loop's own read-only tests, its log muted, once the
        human-task plan is resolved:

        * the plan's skipped and accepted tasks and the manual ones are out;
        * a resume keeps a task with done evidence (``ResumeEvidence.done_evidence``); a
          check whose findings stand is kept while the files are as it left
          them (``CheckHolds.check_findings_rerun``), and the tasks after it are held;
        * a failed check on unchanged files (``CheckHolds.unchanged_since_failure``) or
          a task the write policy refuses is not dispatched, and the run
          stops there: the tasks after its group in the batch, and the later
          batches, are not reached. A group is what ``_run_batch`` dispatches
          together (``admit_disjoint_groups`` under :meth:`write_ceiling`;
          one task each at the default ceiling of 1), so the tasks dispatched
          beside the refused one count.

        A check this run dispatches is decided by its verdict, which is not
        known yet: the tasks after it count, and are named as waiting on it.
        Once a code task of this run was dispatched ahead of it the files
        have moved, so a check after it counts as run again. A runner that
        fails is not foreseen; the run's own lines and its ``resume:`` line
        say what happened.
        """
        graph = _check_records.decomposition_graph(self.tasks, self.state)
        plan = result.human_plan
        # A dry run never persists the plan, so an accepted check can still
        # read as holding its dependents on record.
        on_record = set(_check_records.rerunnable_checks(self.state)) - set(plan.accepted)
        rerun: set = set()
        dispatched_checks: List[str] = []
        waiting: Dict[str, List[str]] = {}
        picked_batches = 0
        picked_ids: List[str] = []
        # What the walk foresees this run leaves (refused, held
        # by a check on record, not reached) and keeps, for `EtaLines.left_out`.
        left: Dict[str, str] = {}
        kept_ids: set = set()
        candidates: List[str] = []
        edits_dispatched = False
        stopped = False
        quiet_log = self.log
        self.log = lambda *_args, **_kwargs: None
        try:
            ceiling = self.write_ceiling()
            for _index, batch_tasks in ordered:
                candidates.extend(
                    str(task.get("task_id", "")) for task in batch_tasks
                    if not (
                        plan.is_skipped(str(task.get("task_id", "")))
                        or str(task.get("task_id", "")) in plan.accepted
                        or task.get("is_human")
                        or task.get("executor_role") == "human"
                    )
                )
                if stopped:
                    continue
                in_batch = 0
                # The loop's runnable list, as far as a preview can tell, in
                # the groups `_run_batch` admits together: with a write ceiling above 1 a
                # group's tasks are dispatched at once and a stop takes
                # effect only once the whole group settled, so a refused
                # task's siblings in its group run.
                runnable = []
                for task in batch_tasks:
                    task_id = str(task.get("task_id", ""))
                    if (
                        plan.is_skipped(task_id) or task_id in plan.accepted
                        or task.get("is_human")
                        or task.get("executor_role") == "human"
                    ):
                        continue
                    holder = _check_records.upstream_held_check(graph, task_id, on_record - rerun)
                    if holder:
                        left[task_id] = _metrics.left_out_check(holder)
                        continue
                    runnable.append(task)
                for group in admit_disjoint_groups(
                    runnable, ceiling=ceiling, root=self.repo_root,
                ):
                    # A code task this run dispatched before this group moves
                    # the files the two unchanged-tree tests compare; one
                    # dispatched beside it has not moved them yet.
                    moved = edits_dispatched
                    for task in group:
                        task_id = str(task.get("task_id", ""))
                        if self.resume:
                            evidence = self._evidence.done_evidence(task)
                            if evidence is not None:
                                again = self._checks.check_findings_rerun(
                                    task, evidence[0], result)
                                if again is not True and not (again is False and moved):
                                    kept_ids.add(task_id)
                                    continue
                                rerun.add(task_id)
                            elif task_id in on_record:
                                rerun.add(task_id)
                            if not moved and self._checks.unchanged_since_failure(
                                task, result,
                            ) is not None:
                                stopped = True
                                left[task_id] = _metrics.LEFT_NOT_RUN
                                continue
                        try:
                            self.policy.check([
                                relative_to_root(path, self.repo_root)
                                for path in declared_file_set(task)
                            ], when="pre-dispatch")
                        except PolicyViolation:
                            stopped = True
                            left[task_id] = _metrics.LEFT_REFUSED
                            continue
                        in_batch += 1
                        picked_ids.append(task_id)
                        upstream = [
                            check for check in dispatched_checks
                            if task_id in _check_records.transitive_dependents(graph, check)
                        ]
                        if upstream:
                            waiting[task_id] = upstream
                        if _batch_prompt.is_check_task(self.kind, task):
                            dispatched_checks.append(task_id)
                        else:
                            edits_dispatched = True
                    if stopped:
                        break
                if in_batch:
                    picked_batches += 1
        except Exception:  # noqa: BLE001 - a count line must not fail a phase
            return None
        finally:
            self.log = quiet_log
        for task_id in candidates:
            if task_id not in left and task_id not in kept_ids and task_id not in picked_ids:
                # After the stop: not reached.
                left[task_id] = _metrics.LEFT_NOT_RUN
        self._eta.walk_left = left
        return picked_batches, picked_ids, list(waiting)

    # -- one batch ------------------------------------------------------

    def _run_batch(
        self,
        batch_index: int,
        tasks: Sequence[Dict[str, Any]],
        result: SchedulerResult,
    ) -> List[TaskOutcome]:
        # One resolution of this batch's runners, read by its ceiling, its
        # rollback-storage preflight and its dispatches (`_runner_for`).
        self._batch_runners, ceiling = self._batch_runners_and_ceiling(tasks)
        clashes = overlapping_pairs(tasks, root=self.repo_root)
        groups = admit_disjoint_groups(tasks, ceiling=ceiling, root=self.repo_root)
        if ceiling > 1 and clashes:
            for left, right, shared in clashes:
                self.log(
                    f"[write-subagents] batch {batch_index}: {left} and {right} "
                    f"both declare {', '.join(shared)} — refusing to co-schedule "
                    f"them; they run sequentially instead (D3h)."
                )
        outcomes: List[TaskOutcome] = []
        # `outcomes` is the task file's order (what the report and the stop
        # check read); this one grows in completion order, and is what the
        # mirror reports.
        outcomes_so_far: List[TaskOutcome] = []
        # The mirror below the loop in `_run` moves once per *batch*, so a batch
        # of co-scheduled tasks reported nothing until its last one landed. This
        # is the same counts write, per task: display only, never the report,
        # and taken under a lock because a disjoint group dispatches on threads.
        mirror_lock = threading.Lock()

        def dispatch_and_mirror(task: Dict[str, Any]) -> TaskOutcome:
            outcome = self._dispatch_one(task, batch_index, result)
            if outcome.skipped:
                # A resume-skipped task is still one of the run's finished tasks
                # — the mirror counts it in `completed` — and its branch returns
                # before `_record_batch_effects`, so the `[ETA]` numerator is
                # advanced here instead, or a resumed run's last line stops short
                # of its own total by exactly the batches it skipped (F3). An
                # implement run counts only what it dispatches,
                # so there the skip leaves both halves.
                with self._effects_lock:
                    self._eta.mark(outcome.task_id, ran=False)
            with mirror_lock:
                outcomes_so_far.append(outcome)
                self._reports.mirror_status(result, finished_in_batch=outcomes_so_far)
            return outcome

        for group in groups:
            # Earlier groups have settled; the next group's runnable candidates
            # alone can select a new storage location. Do this before any of its
            # threads takes a snapshot. Human/check-held tasks never get probed.
            self._snapshots.storage_candidates = group
            self._snapshots.storage_decided = False
            if len(group) == 1:
                outcomes.append(dispatch_and_mirror(group[0]))
            else:
                with ThreadPoolExecutor(max_workers=len(group)) as pool:
                    futures = [
                        pool.submit(dispatch_and_mirror, task)
                        for task in group
                    ]
                    outcomes.extend(future.result() for future in futures)
            stale = self._commit.stale
            if any(
                (o.stops_the_loop or not o.ok) and o.task_id not in stale
                for o in outcomes
            ):
                # Verification gates the next dispatch (D3h): a partial
                # application is never compounded by a concurrent one.
                break
        return outcomes

    def _dispatch_one(
        self, task: Dict[str, Any], batch_index: int, result: SchedulerResult
    ) -> TaskOutcome:
        task_id = str(task.get("task_id", ""))
        profile = profile_for_kind(self.kind)

        if task_id in self._evidence.kept_at_request:
            # Answered `--human-task <id>=skip` — kept as it
            # stood, never dispatched again.
            return self._keep_at_request(task, batch_index, result)

        # Resume: a batch counts as done when its result file exists, parses and
        # validates (D3i). Its summary is already in the prior-changes log on
        # disk, so a resumed run replays rather than reconstructs.
        evidence = self._evidence.done_evidence(task) if self.resume else None
        kept_findings = False
        if evidence is not None and self.kind == "implement":
            rerun = self._checks.check_findings_rerun(task, evidence[0], result)
            if rerun is True:
                evidence = None
            elif rerun is False:
                kept_findings = True
        if evidence is not None:
            output_path, _recorded_id, recorded = evidence
            self.log(f"[write-subagents] {task_id} already complete — skipping")
            data = json.loads(Path(output_path).read_text(encoding="utf-8"))
            # The outcome its verdict stamp records (`batch_ledger`, the
            # stamp's round trip): its check's label, what its own checks
            # reported, an apply batch's declined items, the files it moved.
            outcome = outcome_from_verdict(
                data, recorded, task, kind=self.kind, runner=self.invoker,
                profile=profile, output_path=output_path,
                files_on_record=lambda: self._evidence.recorded_files_touched(output_path),
            )
            if kept_findings:
                outcome.reason = (
                    f"NOT RE-RUN: nothing in the repository changed since "
                    f"{task_id}'s check reported problems (the files git sees "
                    f"have the same sizes and timestamps), so it would report "
                    f"them again; its findings stand. Fix what it reported "
                    f"and resume, accept the findings with --human-task "
                    f"{task_id}=done, or run it again anyway with "
                    f"--human-task {task_id}=retry."
                )
            # One line per skip, before the early return: this branch reaches
            # neither `_audit_terminal` nor `_record_batch_effects`, so without it
            # a resumed run's audit log is silent about every task it declared
            # complete — the one place the 2026-09-16 five-task skip would have
            # been visible as it happened (D3l).
            self._audit_resume_skip(outcome, task)
            # The status the earlier run left for this task is not necessarily
            # `completed`: the result file lands before `_record_batch_effects`
            # saves, so a run killed in that window leaves a file resume trusts
            # beside a `pending` nothing ever revisited — a finished phase
            # reporting `(13/14 tasks)` with one task still `pending`
            # (state-tracking F5, 2026-09-16). No metric: the duration was the
            # earlier run's to measure, and a fabricated one would average in.
            with self._effects_lock:
                self._remember_outcome(outcome)
                resumed_reason = (
                    "not run again: nothing changed since its check "
                    "reported problems" if kept_findings else
                    f"resumed from {Path(outcome.output_path).name}"
                )
                # Its status and items again; its verdict stays as the
                # earlier run recorded it.
                self._write_record(task, replace(self._batch_facts(
                    task, outcome, "completed", resumed_reason,
                    dispatched=False, kept=False), resumed=True))
                # Its completion's identities, should the earlier
                # run have stopped before it saved them.
                self._commit.repin(task, outcome)
                self.state.save()
            return outcome

        # Past the resume skips, the task is this run's to handle.
        self._mark_implement_started()

        # A resumed verification-only task that failed, with nothing in the
        # repository changed since: not dispatched again (racing re-run 3,
        # 2026-10-05 — `--resume` spent 148 s on the same `html-validate`
        # failure against the same bytes).
        if self.resume:
            refused = self._checks.unchanged_since_failure(task, result)
            if refused is not None:
                self._record_batch_effects(task, refused, batch_index, result)
                return refused

        # The scope policy's stale-task check: a task materialized
        # under another policy, baseline or binding is never sent with the
        # wrong policy's prompt. Never blocks an `expand` task without scope
        # metadata.
        scope_refusal = self._prompts.scope_refusal(task)
        if scope_refusal is not None:
            return self._refused(task, scope_refusal, batch_index, result)
        try:
            prompt = self._prompts.with_result_contract(task, self._prompts.dispatched_prompt(task))
        except ResultRejected as exc:
            return self._refused(
                task, exc.message, batch_index, result, status=exc.status)
        self._evidence.retire_foreign_result(task)

        # "Every batch is re-checked immediately
        # before it is dispatched": beside the D3l check below and before the
        # snapshot, every fix file the batch declares is held to the content
        # the apply guard saved for it. A batch that fails is never
        # dispatched; the loop goes on to the next one. No-op without a guard.
        stale = self._commit.recheck(task, batch_index, result)
        if stale is not None:
            return stale

        # D3l pre-dispatch: a batch whose DECLARED set is not wholly inside the
        # policy never starts a runner — and the check runs BEFORE the snapshot,
        # not after it. Snapshotting first would copy the bytes of every denied
        # path the task named (`.env`, `.git/config`, `*.pem`) into
        # `{phase}/pre_batch/{task_id}/files/` and then refuse the dispatch,
        # leaving the payload behind: the deny list exists precisely to keep that
        # material out of executor-owned artifacts, so a refusal that creates one
        # is the control defeating itself.
        declared = [
            relative_to_root(path, self.repo_root)
            for path in declared_file_set(task)
        ]
        try:
            # As declared: a file outside the repository is
            # named as the task wrote it, never by its resolved absolute path.
            self.policy.check(declared_file_set(task), when="pre-dispatch")
        except PolicyViolation as exc:
            result.refusals.policy_paths[task_id] = list(exc.paths)
            result.refusals.policy_hits[task_id] = list(exc.hits)
            return self._refused(
                task, exc.message, batch_index, result,
                write_outcome=WRITE_POLICY_VIOLATION,
            )
        # Plan step 3, beside the D3l check and before the
        # snapshot for the same reason: under `plan-file`/`tasks` the declared
        # set must be exactly the phase's write target, on every rung, or the
        # batch is refused with nothing snapshotted and nothing spawned.
        mismatch = self._grant.grant_mismatch(task)
        if mismatch is not None:
            return self._refused(task, mismatch, batch_index, result)

        try:
            self._snapshots.decide_rollback_storage(task, profile)
            snapshot = self._snapshots.take(task)
        except WriteSafetyError as exc:
            return self._refused(task, exc.message, batch_index, result)
        # The replaced-target check's "before": taken at THIS dispatch's
        # pre-batch snapshot (reused or fresh), so the identity compared after
        # the child is always the one this spawn saw.
        self._grant.target_identity_before[task_id] = self._grant.identity_of(
            self._grant.identity_path()
        )
        # The protected set's (and context plan's) "before" for this
        # dispatch's own post-run check, independent of the sweep below.
        self._commit.watch_begin(task_id)

        try:
            self._begin_sweep(
                task_id, declared,
                verification_only=self._verification_only(snapshot),
            )
        except WriteSafetyError as exc:
            # The census is this task's whole verdict and there is none: a
            # refusal, with nothing spawned (W1, adversarial review 2026-10-02).
            self._grant.target_identity_before.pop(task_id, None)
            self._commit.watch_before.pop(task_id, None)
            return self._refused(task, exc.message, batch_index, result)
        started = time.time()
        self._grant.git_meta_before[task_id] = self._grant.git_metadata_fingerprint()
        try:
            outcome = self._dispatcher(
                self, task, prompt, snapshot, profile, declared,
                batch_index=batch_index,
            )
            self._grant.warn_git_metadata_changed(task_id)
            outcome.snapshot_dir = snapshot.directory
            if not outcome.duration_seconds:
                outcome.duration_seconds = time.time() - started
            # A dispatch `_classify` never saw still gets its write outcome
            # (`write_outcomes.classify_attempt`); `_audit_terminal` makes it
            # a partial application when the batch moved bytes.
            _write_outcomes.classify_attempt(outcome, snapshot_dir=snapshot.directory)

            self._audit_terminal(outcome, snapshot, profile)
        finally:
            # The census and its retained-byte index are consumed by whichever of
            # `_classify` / `_audit_terminal` got there first; this drops them in
            # the one case neither did (a dispatch that raised out).
            #
            # I11: that case is also a batch refused before any child
            # started (`preflight_runner` raising `RunnerRejected` at batch 0),
            # and `_begin_sweep` had already published it in flight. Left
            # registered, the refusal's own `WriteReports.mirror_status` re-published it,
            # so `.status.json` read `in flight: apply-batch-0 (since 0m 9s)`
            # for the rest of the dir's life. The dispatch is over either way.
            self._sweep.abandon(task_id)
            self._grant.target_identity_before.pop(task_id, None)
            self._commit.watch_before.pop(task_id, None)
        self._record_batch_effects(task, outcome, batch_index, result)
        return outcome

    def _keep_at_request(
        self, task: Dict[str, Any], batch_index: int, result: SchedulerResult,
    ) -> TaskOutcome:
        """Keep a stopped batch as it stands, at the user's request.

        Answered ``--human-task <id>=skip`` and checked by
        :meth:`ResumeEvidence.partial_skip_evidence`. Nothing is dispatched:
        the outcome is the batch's own, read by
        :meth:`ResumeEvidence.kept_outcome`, which writes nothing. Here it is
        recorded: its verdict is stamped again and the audit gains a
        completion line, so a later resume and ``util restore-batch`` read it
        as done (the pre-batch snapshot stays its rollback point); its
        summary joins the prior-changes log the next batch reads; and the
        loop goes on.
        """
        outcome = self._evidence.kept_outcome(
            task, invoker=self.invoker, item_words=self._declined_words,
        )
        task_id, expected = outcome.task_id, outcome.expected_ids
        recorded = self.audit.completion_for(task_id, expected_ids=expected) or {}
        self.audit.completed(
            task_id=task_id, kind=self.kind, attempt=0, runner=self.invoker,
            profile=outcome.profile, status=STATUS_OK,
            write_outcome=WRITE_APPLIED, exit_code=None,
            files_touched=outcome.files_touched,
            observed=dict(recorded.get("observed") or {}),
            duration_seconds=0.0, reason=outcome.reason, expected_ids=expected,
        )
        self._stamp_verdict(outcome)
        self._record_batch_effects(
            task, outcome, batch_index, result, dispatched=False, kept=True,
        )
        return outcome

    def _refused(
        self, task: Dict[str, Any], reason: str, batch_index: int,
        result: SchedulerResult, *, status: str = STATUS_REJECTED,
        write_outcome: Optional[str] = None,
    ) -> TaskOutcome:
        """:meth:`_refuse_before_dispatch` for a refusal worded *reason*:
        the outcome no runner produced, in this phase's kind and profile."""
        return self._refuse_before_dispatch(task, TaskOutcome(
            task_id=str(task.get("task_id", "")), kind=self.kind,
            runner=self.invoker, status=status, profile=profile_for_kind(self.kind),
            reason=reason, write_outcome=write_outcome,
        ), batch_index, result)

    def _refuse_before_dispatch(
        self, task: Dict[str, Any], outcome: TaskOutcome, batch_index: int,
        result: SchedulerResult,
    ) -> TaskOutcome:
        """Record a task refused before any runner started, and return it.

        A task ``driver.write_paths``
        refused before dispatch was never recorded — it stayed ``pending``
        with no reason while the task after it read "T005 failed" — so
        ``--human-task <id>=skip`` was refused as "a code task that did not
        fail" and changing the policy was the only way past it. It goes
        through the normal record path now (``_record_batch_effects``:
        ``failed`` with its reason in ``state.json``, the batch line), minus
        the metric, since no child ran; a ``--resume`` checks it again, so a
        policy the user widened lets it run, and ``--human-task
        <id>=done|skip|retry`` answers it like any failed task.
        """
        result.refusals.before_dispatch.add(outcome.task_id)
        self._record_batch_effects(
            task, outcome, batch_index, result, dispatched=False,
        )
        return outcome

    def _audit_resume_skip(
        self, outcome: TaskOutcome, task: Dict[str, Any]
    ) -> None:
        """Record the one decision a resume skip makes, naming what it trusted."""
        try:
            data = json.loads(
                Path(outcome.output_path).read_text(encoding="utf-8")
            )
            raw = data.get("ids") if isinstance(data, dict) else None
            result_ids = [str(item) for item in raw] if isinstance(raw, list) else []
        except (OSError, ValueError):  # noqa: BLE001 - the skip already happened
            result_ids = []
        self.audit.skipped(
            task_id=outcome.task_id, kind=self.kind,
            output_path=outcome.output_path, result_ids=result_ids,
            files_touched=outcome.files_touched,
        )

    def _audit_terminal(
        self, outcome: TaskOutcome, snapshot: TaskSnapshot, profile: str
    ) -> None:
        """Close the audit record for a dispatch that never reached ``_classify``.

        D3l's contract is *one fsynced line before dispatch and one after
        classification*, but the classifier only runs once rung-6 validation has
        passed. A dispatch that timed out, errored, was rate-limited out or came
        back as prose (rungs 2-5) therefore left a ``dispatched`` line with no
        terminal record — and ``AuditLog.failed_task_ids`` reads only
        ``completed`` events, so ``util restore-batch --all-failed`` silently
        skipped exactly the dispatches most likely to have left half-written
        bytes behind (a timeout mid-edit).

        The record carries the observed post-run hashes, and ``files_touched`` is
        filled from the byte comparison rather than left empty, because that set
        is what the restore path restores and verifies against. The sweep runs
        first on purpose: a timeout mid-edit is exactly the case where the runner
        was writing somewhere it never declared, and adopting those paths into the
        snapshot before ``changed()`` is read is what puts them in reach of
        ``util restore-batch --all-failed``.

        On the plugin-landlock rung the replaced-target check runs here as
        well, once ``files_touched`` is filled
        (:meth:`_replaced_target_unclassified`): a target a user or an editor
        saved over by rename differs from the snapshot, so without it the
        user's new file would land in the restore set.
        """
        if outcome.task_id in self._audited:
            return
        if self._executor_dispatch and not outcome.attempts:
            # `dispatch_task` refused before its first `before_attempt`, so no
            # `dispatched` line was written either. A lone completion here would
            # claim a run that never started.
            return
        undeclared = self._undeclared_writes(outcome.task_id, snapshot)
        observed = self._sweep.observed_with_undeclared(snapshot, undeclared)
        # A protected path this window changed is put back here too,
        # before the byte comparison below reads the snapshot.
        self._commit.protected_unclassified(outcome, snapshot)
        if not outcome.files_touched:
            outcome.files_touched = snapshot.changed()
        if not outcome.unrestorable:
            outcome.unrestorable = list(undeclared.unrecoverable)
        # After the fill, never before it: the fill is what would put the
        # replaced target back into the restore set.
        if not self._grant.replaced_target_unclassified(outcome, snapshot):
            self._partial_when_bytes_moved(outcome, snapshot)
        last = outcome.attempts[-1] if outcome.attempts else None
        self._audit_completion(
            outcome,
            outcome.runner,
            profile,
            last.index if last is not None else 1,
            last.exit_code if last is not None else None,
            observed,
            outcome.duration_seconds,
        )

    def _partial_when_bytes_moved(
        self, outcome: TaskOutcome, snapshot: TaskSnapshot
    ) -> None:
        """A failed dispatch that never reached ``_classify`` and moved bytes
        is a partial application (``write_outcomes.partial_when_bytes_moved``,
        over the byte comparison :meth:`_audit_terminal` just filled)."""
        _write_outcomes.partial_when_bytes_moved(
            outcome, snapshot_dir=snapshot.directory)

    # -- D3l post-run containment: the OBSERVED set, not the declared one ---

    def _begin_sweep(
        self, task_id: str, declared: Sequence[str], *,
        verification_only: bool = False,
    ) -> None:
        """Open this dispatch's sweep (:meth:`ContainmentSweep.begin`), then
        publish it in flight.

        Raises :class:`WriteSafetyError` for a ``verification_only`` task when
        the census is unusable: never VERIFIED without a census.
        """
        self._sweep.begin(task_id, declared, verification_only=verification_only)
        # F10: the mirror's own writes only happen at a batch's boundaries
        # (`WriteReports.mirror_status`), which says nothing while a single-task batch is
        # still running — measured 2026-09-16, T001 ran 659s as one batch and
        # `.status.json` read `dispatched: 0` the entire time. This is the one
        # place a dispatch's start time is known, so it patches the mirror's
        # `in_flight` list directly rather than waiting for the next full
        # recompute; that next call (whenever it lands) replaces the whole
        # `write_subagents` object, `in_flight` included, from
        # the sweep's in-flight entries afresh, so a stale patch here never lingers.
        self._reports.publish_in_flight()

    def _undeclared_writes(
        self, task_id: str, snapshot: TaskSnapshot
    ) -> _write_sweep.UndeclaredWrites:
        """Close this dispatch's sweep (:meth:`ContainmentSweep.undeclared_writes`).
        The seam ``_classify`` and ``_audit_terminal`` call, so a test can
        stand in for the sweep on a scheduler it built by hand."""
        return self._sweep.undeclared_writes(task_id, snapshot)

    def _dispatch_executor(
        self,
        task: Dict[str, Any],
        prompt: str,
        snapshot: TaskSnapshot,
        profile: str,
        declared: Sequence[str],
        *,
        batch_index: Optional[int] = None,
    ) -> TaskOutcome:
        """Real subprocess dispatch, with the D3g/D3l hooks bound to this task.

        The phase's :class:`JailRequest` goes to the
        preflight (its scope joins the sandbox decision's key) and to
        ``dispatch_task``, and a batch that will run on the plugin-landlock rung
        is announced first with the stray-writes-only line.
        """
        task_id = str(task.get("task_id", ""))
        runner = self._runner_for(task)
        info = self._grant.preflight(runner, profile)
        # F12: `subagent_batch_report.json.runner_versions` was empty on this
        # path — the read half fills it from its own batch-start preflight
        # (`_preflight_batch_runners`); this call already runs one per
        # dispatch and its version was simply never kept.
        self._runner_versions[runner] = str(info.get("version") or "unknown")
        rung = self._grant.recorded_rung(runner, profile)
        self._dispatch_rungs[task_id] = rung
        request = self.jail_request
        self._grant.announce_rung(runner, batch_index)

        def before_attempt(context: Dict[str, Any]) -> None:
            # The prompt this attempt really sends: a report re-ask (the
            # ladder's rule 7) sends its own, never the batch's instructions.
            sent = context.get("prompt") or prompt
            self.audit.dispatched(
                task_id=context["task_id"],
                kind=self.kind,
                attempt=context["attempt"],
                runner=runner,
                profile=profile,
                cwd=context["cwd"],
                sandbox_root=self.repo_root,
                argv=self._render_argv(runner, sent, profile),
                prompt=sent,
                declared_files=list(declared),
                snapshot_dir=snapshot.directory,
                snapshot_before={
                    entry.relative: entry.sha256 for entry in snapshot.entries
                },
            )
            self._prompts.keep_dispatched_prompt(
                task_id, int(context["attempt"]), sent, prompt
            )

        def after_result(context: Dict[str, Any]) -> None:
            # The executor's own record of the rung this attempt ran on wins
            # over the preflight's: every `after_result` context carries it,
            # `None` included (`dispatch_spawn._jail_hook_context`).
            seen = context["sandbox_rung"]
            self._dispatch_rungs[task_id] = seen
            self._classify(task, context["outcome"], snapshot, context["result"],
                           runner=runner, profile=profile,
                           attempt=context["attempt"],
                           exit_code=context["exit_code"],
                           duration=context["duration_seconds"],
                           sandbox_rung=seen,
                           jail_denials=context.get("jail_denials"),
                           resent=bool(context.get("resent")),
                           resend_note=context.get("resend_note"))

        def nothing_changed(context: Dict[str, Any]) -> Optional[str]:
            # Rule 9: asked before `after_result`, read-only,
            # so a re-send leaves the census for the classification that
            # follows it.
            return self._applied_without_changes(task, snapshot, context)

        def incomplete_report(context: Dict[str, Any]) -> Optional[str]:
            # Asked before `after_result`, read-only, like rule
            # 9's question; a reason sends the one report re-ask.
            return self._incomplete_report(task, snapshot, context)

        def restate_findings(
            context: Dict[str, Any],
        ) -> Optional[Tuple[str, List[str]]]:
            # Asked the same way; never a classification.
            return self._restate_findings(task, context)

        def changed_files(context: Dict[str, Any]) -> List[str]:
            # T4.8: a turn a denial ended has no result, so `_classify`
            # never runs and `dispatch_task` would retry on top of whatever it
            # half-applied. Asked before that retry decision, against the same
            # pre-batch snapshot and pre-run census `_classify` reads.
            return self._sweep.moved_since_dispatch(context["task_id"], snapshot)

        def tree_fingerprint(context: Dict[str, Any]) -> Dict[str, Optional[str]]:
            # A report re-ask's guard: the current bytes of every declared file
            # and of every path this dispatch has moved so far (the same two
            # sources `_classify` decides on, peeked). The executor compares the
            # value before and after the re-ask; any difference is an edit the
            # re-ask was told not to make.
            moved = self._sweep.moved_since_dispatch(context["task_id"], snapshot)
            paths = set(moved) | {entry.relative for entry in snapshot.entries}
            return {
                relative: file_sha256(os.path.join(self.repo_root, relative))
                for relative in sorted(paths)
            }

        return dispatch_task(
            task,
            phase_dir=self.phase_dir,
            runner=runner,
            anchor=self.anchor,
            cwd=self.repo_root,
            prompt=prompt,
            before_attempt=before_attempt,
            after_result=after_result,
            changed_files=changed_files,
            jail_request=request,
            tree_fingerprint=tree_fingerprint,
            nothing_changed=nothing_changed,
            incomplete_report=(
                incomplete_report if self.kind in APPLY_WRITE_KINDS else None
            ),
            restate_findings=(
                restate_findings if self.kind == "implement" else None
            ),
        )

    def _render_argv(self, runner: str, prompt: str, profile: str) -> List[str]:
        """The rendered argv for the audit record / dry run, never executed here.

        The rung the preflight recorded for this runner and scope, rendered as
        the dispatch will render it (``dispatch_spawn.audit_argv``): on the
        plugin-landlock rung the wrapped shape with placeholder paths, on any
        other recorded rung (F5's uncontained one) the rung with this run's
        consent, so the audit record never shows a sandbox the child did not
        get. It creates nothing (F1 "Task-specific paths stay out of shared
        state").
        """
        provider_name, model = parse_model_spec(runner, anchor=self.anchor)
        provider = provider_registry.get_provider(provider_name)
        if provider is None:
            return [runner]
        return _dispatch_spawn.audit_argv(
            provider, provider_name, model, profile, prompt,
            rung=self._grant.recorded_rung(runner, profile),
            jail_request=self.jail_request,
            consent=host_write_posture_consent(write_scope=self.write_scope),
        )

    # -- D3g: the classification ----------------------------------------

    def _classify(
        self,
        task: Dict[str, Any],
        outcome: TaskOutcome,
        snapshot: TaskSnapshot,
        result: Any,
        *,
        runner: str,
        profile: str,
        attempt: int,
        exit_code: Optional[int],
        duration: float,
        sandbox_rung: Optional[str] = None,
        jail_denials: Any = None,
        resent: bool = False,
        resend_note: Optional[str] = None,
    ) -> None:
        """Decide which D3g outcome this dispatch landed on, and record it.

        The decision is :func:`write_verdict.decide`, a table read in order:
        the write policy over every touched path, then the plugin-landlock
        rung's replaced target and jail denials, then a task that declares no
        files, then the claim rows, where the claim is never the verdict and a
        non-zero exit never lands on APPLIED (D3k). The rows and why:
        ``docs/development/write-scheduler.md``, "The verdict table".

        This method gathers the facts, asks the table and applies the verdict.
        The guards' facts are gathered in the table's order, each only while
        no guard before it has matched (:func:`write_verdict.guard`), so
        reading one a later row needs (the target's inode, a jail path
        resolved) never stands between a matched guard and what its row does.
        Every side effect is here, around the pure call: the containment sweep
        is consumed exactly once, a policy violation's files are restored
        before its verdict is set and audited, the jail's records are kept,
        and one audit line closes the dispatch.
        *resent* says the batch was sent once more after an unchanged
        ``applied`` (the ladder's rule 9), *resend_note* why it was not. A
        prose result never reaches here: it already failed rung 6 as
        ``schema_invalid``, the fourth outcome.
        """
        task_id = outcome.task_id
        claimed = str((result or {}).get("status") or "")
        summary = str((result or {}).get("summary") or "").strip()
        notes = str((result or {}).get("notes") or "").strip()
        outcome.runner_notes = clip(notes, 600) or None
        reported_ids = [str(i) for i in ((result or {}).get("ids") or [])]
        expected_ids = [str(i) for i in (task.get("expected_ids") or [])]
        # An apply batch's declined item is not applied and not missing; an
        # id it put in both `ids` and `declined` is neither. `implement` has
        # no decline: a reply declining its task did not do it (`failed`).
        declined = declined_items(result, expected_ids)
        declined_task: Optional[str] = None
        if self.kind in APPLY_WRITE_KINDS:
            outcome.declined = dict(declined.items)
        elif declined.items:
            declined_task = next(iter(declined.items.values()))
            claimed = "failed"
            outcome.runner_notes = outcome.runner_notes or (
                f"declined: {declined_task}"
            )
        # `changed` is the DECLARED verdict: the byte comparison taken before
        # the sweep adopts this dispatch's undeclared writes into the snapshot.
        changed = snapshot.changed()
        undeclared = self._undeclared_writes(task_id, snapshot)
        observed = self._sweep.observed_with_undeclared(snapshot, undeclared)
        # Under an apply guard, the protected
        # set's (and the context plan's) own post-run check, which never
        # depends on the sweep above. Empty without a guard.
        watched, commit_apply, watched_guard = self._commit.watch_after(task_id)

        # F9: the verification evidence rides the outcome, which both batch
        # reports are built from.
        outcome.expected_ids = expected_ids
        outcome.returned_ids = reported_ids
        # Whatever row decides it, a file-less implement task's verdict reads
        # VERIFIED or PARTIAL on every surface (`outcome_label`).
        outcome.verification_only = self._verification_only(snapshot)
        self._record_reply_checks(task, outcome, result)
        outcome.sha256_before = {
            relative: row.get("sha256_before") for relative, row in observed.items()
        }
        outcome.sha256_after = {
            relative: row.get("sha256_after") for relative, row in observed.items()
        }
        # `files_touched` is the ROLLBACK set: the declared files plus the
        # undeclared writes the sweep retained bytes for. `util restore-batch`
        # reads it, so a path with no rollback point is left out and
        # `unrestorable` carries it (`TaskOutcome.bytes_moved` reads both).
        outcome.files_touched = list(changed) + list(undeclared.restorable)
        outcome.unrestorable = list(undeclared.unrecoverable)
        outcome.summary = summary or None
        if undeclared:
            self._log_undeclared(task_id, undeclared)

        facts = WriteFacts(
            task_id=task_id,
            kind=self.kind,
            claimed=claimed,
            exit_code=exit_code,
            changed=tuple(changed),
            expected_ids=tuple(expected_ids),
            reported_ids=tuple(reported_ids),
            attested_ids=tuple(
                i for i in reported_ids if i not in declined.conflicting
            ),
            declined=dict(outcome.declined),
            declined_task=declined_task,
            declined_problems=tuple(declined.problems),
            undeclared=tuple(undeclared.paths),
            undeclared_own=tuple(undeclared.own),
            siblings=tuple(sorted(undeclared.shared)),
            sweep_observed=undeclared.observed,
            verification_only=outcome.verification_only,
            summary=summary,
            snapshot_dir=str(snapshot.directory),
            snapshot_reused=task_id in self._snapshots.reused,
            resent=resent,
            resend_note=resend_note,
            repo_root=str(self.repo_root),
            sweep_max_files=_write_sweep.SWEEP_MAX_FILES,
        )
        # The guards' facts, in the table's order, each gathered only while no
        # guard before it has matched: reading a later one can fail (its
        # paths are resolved), and must never stand between a matched guard
        # and what its row does, a policy violation's restore above all.
        violation = self._post_run_violation(changed, undeclared, watched)
        if violation is not None:
            facts = replace(
                facts, policy=PolicyFacts(violation.message, tuple(violation.paths)),
            )
        if guard(facts) is None:
            # This dispatch's "before", spent by every row past the policy's.
            before = self._grant.target_identity_before.pop(task_id, None)
            if sandbox_rung == SANDBOX_RUNG_PLUGIN_LANDLOCK:
                facts = replace(facts, replaced=self._grant.target_replacement(before))
        if guard(facts) is None:
            denials = _as_jail_denials(jail_denials)
            if denials is not None:
                # Kept before any of its paths is resolved.
                self._grant.jail_denials[task_id] = denials.to_dict()
                facts = replace(facts, jail=self._grant.jail_facts(task_id, denials, facts))
                note = jail_note(facts.jail) if guard(facts) is None else None
                if note:
                    self._grant.jail_notes[task_id] = note
        reply_check: Optional[_batch_reply.CheckReply] = None
        if guard(facts) is None:
            reply_check = read_check_reply(result)
            facts = replace(
                facts,
                check=(
                    None if reply_check.findings is None
                    else tuple(reply_check.findings)
                ),
                check_listed=reply_check.listed,
                check_could_not_run=reply_check.could_not_run,
                declined_words=self._declined_words(outcome.declined),
                named_files=tuple(
                    str(path) for path in ((result or {}).get("files_touched") or [])
                    if isinstance(path, str)
                ),
            )
        verdict = decide(facts)
        if verdict.rule in DECLARED_NAMES_ROWS:
            facts = replace(facts, declared_names=(
                ", ".join(e.relative for e in snapshot.declared_entries())
                or "any declared file"
            ))

        restore: Optional[PolicyRestore] = None
        if verdict.rule is VerdictRule.POLICY_VIOLATION:
            assert violation is not None
            report = snapshot.restore(violation.paths)
            # A protected path the snapshot holds no bytes for is put back
            # from what the guard kept; no-op without a guard.
            report = self._commit.restore_watched(
                task_id, report, commit_apply, watched_guard,
            )
            restore = PolicyRestore.from_report(report, {
                getattr(commit_apply, name, None)
                for name in ("RESTORED_FROM_COPY", "DELETED_ABSENT_BEFORE")
            } - {None})
        elif verdict.rule is VerdictRule.REPLACED_TARGET:
            self._grant.record_replaced_target(outcome)
        elif verdict.rule is VerdictRule.JAIL_FAILED:
            self._grant.jail_failed.add(task_id)
        if (
            verdict.check_not_run and reply_check is not None
            and reply_check.findings and not outcome.runner_notes
        ):
            # A check that did not run: what its reply listed is the stop's
            # account of it, never findings the run goes on past.
            outcome.runner_notes = clip("; ".join(reply_check.findings), 600)
        # The verdict is on the outcome before anything below can fail: a
        # restored violation is never left unclassified by its audit line.
        outcome.status = verdict.status
        outcome.write_outcome = verdict.write_outcome
        if verdict.applied_without_changes:
            outcome.applied_without_changes = True
        if verdict.unapplied_ids:
            outcome.unapplied_ids = list(verdict.unapplied_ids)
        if verdict.rule is VerdictRule.CHECK_FINDINGS:
            outcome.check_findings = list(facts.check or [])
        elif verdict.rule is VerdictRule.VERIFIED:
            outcome.check_findings = None if facts.check is None else list(facts.check)
        reason = reason_for(verdict, facts, restore)
        if reason is not None:
            outcome.reason = reason
        if verdict.rule is VerdictRule.POLICY_VIOLATION:
            self.audit.restored(task_id=task_id, report=report, force=False)
        elif verdict.rule is VerdictRule.APPLIED_NO_OP_CLAIMED and not facts.snapshot_reused:
            self.log(
                f"[write-subagents] warning: {task_id} claimed "
                f"'no-op' but {', '.join(changed)} changed against a snapshot "
                f"taken this dispatch — treating the bytes as "
                f"authoritative."
            )
        self._audit_completion(outcome, runner, profile, attempt, exit_code,
                               observed, duration)

    def _record_reply_checks(
        self, task: Dict[str, Any], outcome: TaskOutcome, result: Any,
    ) -> None:
        """The checks a code batch's reply says it ran on its own edits, on
        the outcome: its findings, its own words about them (never
        a finding) and, for apply-code-fixes, what it says each known
        check it was told to run did."""
        if self.kind in _batch_prompt.CODE_WRITE_KINDS and not outcome.verification_only:
            outcome.batch_check = batch_check_findings(result)
            outcome.batch_check_note = batch_check_note(result)
            if self.kind == "implement" and outcome.batch_check:
                # What only repeats findings the user accepted for a check is
                # that check's, never this task's own failure: only the checks
                # this task was told were accepted, and none whose failure is
                # its own job.
                own, matched = _check_records.split_accepted_findings(
                    outcome.batch_check,
                    _check_records.accepted_findings_for(self.tasks, task, self.state),
                )
                if matched:
                    outcome.batch_check_accepted = matched
                    outcome.batch_check = own or None
        if self.kind == "apply_code_fixes":
            # Read against the commands its prompt listed; a command it lists
            # as failed is a failing check on every surface.
            listed = _known_checks.listed_check_outcomes(
                _known_checks.reply_listed(result),
                self._told_checks.get(outcome.task_id) or (),
            )
            self._listed_outcomes[outcome.task_id] = listed
            outcome.batch_check = _known_checks.with_listed_failures(
                outcome.batch_check, listed,
            )

    def _log_undeclared(self, task_id: str, undeclared: _write_sweep.UndeclaredWrites) -> None:
        stranded = undeclared.unrecoverable
        self.log(
            f"[write-subagents] {task_id}: {len(undeclared)} file(s) "
            f"changed outside this task's declared set "
            f"({', '.join(undeclared.paths[:5])}"
            f"{', …' if len(undeclared) > 5 else ''}) — checking them against "
            f"driver.write_paths."
            + (
                f" {len(stranded)} of them had no retained pre-run bytes and "
                f"cannot be restored automatically."
                if stranded else ""
            )
        )

    def _post_run_violation(
        self, changed: Sequence[str], undeclared: _write_sweep.UndeclaredWrites,
        watched: Sequence[str],
    ) -> Optional[PolicyViolation]:
        """D3l post-run: the write policy over the touched set, or ``None``.

        The touched set is the declared files whose bytes moved, whatever
        else under the pinned root the sweep saw move (declared or not: the
        sweep retained its pre-run bytes, so a restore covers an undeclared
        write too, :meth:`_undeclared_writes`), and the watched paths the
        sweep did not see. Enforcing on ``changed`` alone is vacuous: every
        path in it passed the identical pre-dispatch check.
        """
        swept = set(changed) | set(undeclared.paths)
        try:
            self.policy.check(
                list(changed) + undeclared.paths
                + [path for path in watched if path not in swept],
                when="post-run",
            )
        except PolicyViolation as exc:
            return exc
        return None

    def _declined_words(self, declined: Dict[str, str]) -> str:
        """``fix 1 (`<id>`) — <reason>; …``: an apply batch's declined items,
        numbered as its result contract numbers them."""
        return _check_records.declined_words(self.kind, self._task_ids_in_order(), declined)

    def _unapplied_words(self, items: Sequence[str]) -> str:
        """``fix 1 (`<id>`)`` for each item a partial application left out."""
        positions = self._task_ids_in_order()
        word = _check_records.item_word(self.kind)
        return ", ".join(
            f"{word} {positions[str(i)][1]} (`{i}`)" if str(i) in positions
            else f"`{i}`"
            for i in items
        )

    def _keep_partial_clause(self, outcome: TaskOutcome) -> str:
        """What ``--human-task <batch>=skip`` does, in one clause."""
        return (
            f"keep what {outcome.task_id} applied and go on without "
            f"{self._unapplied_words(outcome.unapplied_ids)}: "
            f"{'it is' if len(outcome.unapplied_ids) == 1 else 'they are'} "
            f"recorded as not applied, skipped at your request, and the "
            f"batches after it run"
        )

    def _task_ids_in_order(self) -> Dict[str, Tuple[str, int]]:
        """``member id -> (task id, 1-based position)`` over this run's tasks."""
        positions: Dict[str, Tuple[str, int]] = {}
        for task in self.tasks:
            for index, member in enumerate(task.get("expected_ids") or [], 1):
                positions.setdefault(str(member), (str(task.get("task_id", "")), index))
        return positions

    def _applied_without_changes(
        self, task: Dict[str, Any], snapshot: TaskSnapshot, context: Dict[str, Any],
    ) -> Optional[str]:
        """Rule 9's measurement: why a schema-valid reply that said ``applied``
        moved not one byte, or ``None`` when that is not what happened.

        Read-only — the census stays registered for the classification —
        and asked before ``_classify``. ``None`` whenever the
        classification decides on something else, or a re-send could land on
        moved bytes: a claim other than ``applied``, a check task (it changes
        nothing by design, and its verdict is VERIFIED or check-findings), a
        non-zero exit, a jail denial, a replaced target, a sweep that could
        not look (the tree outgrew the census), or any path — declared or
        not — that moved.
        """
        result = context.get("result")
        if not isinstance(result, dict) or str(result.get("status") or "") != "applied":
            return None
        if self._verification_only(snapshot):
            return None
        expected = [str(i) for i in (task.get("expected_ids") or [])]
        declined = declined_items(result, expected).items
        if expected and all(item in declined for item in expected):
            # It declined every item, so nothing was meant to
            # land; sending it again would ask for what it refused.
            return None
        if context.get("exit_code") not in (0, None):
            return None
        denials = _as_jail_denials(context.get("jail_denials"))
        if denials is not None and denials.total:
            return None
        task_id = str(task.get("task_id", ""))
        looked = self._sweep.has_census(task_id)
        if not looked:
            return None
        if context.get("sandbox_rung") == SANDBOX_RUNG_PLUGIN_LANDLOCK:
            before = self._grant.target_identity_before.get(task_id)
            if before is not None and self._grant.identity_of(self._grant.identity_path()) != before:
                return None
        if snapshot.changed():
            # A declared file moved: applied, whatever else moved beside it.
            # Decided before the census walk below, which could only agree.
            return None
        moved = self._sweep.moved_since_dispatch(task_id, snapshot)
        outside: List[str] = []
        if moved and self.kind in SHARED_ARTIFACT_WRITE_KINDS:
            # For a plan or task-list batch the declared file
            # is the whole contract, so a stray write beside an unchanged
            # plan does not make it applied, and the plan's own bytes cannot
            # be applied twice by a re-send. Told which files moved instead.
            outside = list(moved)
            context["moved_outside"] = outside
        elif moved:
            return None
        declared = (
            ", ".join(e.relative for e in snapshot.declared_entries())
            or "the files it declares"
        )
        named = [
            str(path) for path in (result.get("files_touched") or [])
            if isinstance(path, str)
        ]
        verb = 'is' if len(snapshot.declared_entries()) == 1 else 'are'
        return (
            "the reply said 'applied'"
            + (f" and named {', '.join(named[:5])} as edited" if named else "")
            + (
                f", but {declared} {verb} byte-for-byte as before the dispatch "
                f"(only {', '.join(outside[:5])}"
                f"{', …' if len(outside) > 5 else ''} changed, outside it)"
                if outside else
                f", but no file changed: {declared} {verb} byte-for-byte as "
                f"before the dispatch"
            )
        )

    def _incomplete_report(
        self, task: Dict[str, Any], snapshot: TaskSnapshot, context: Dict[str, Any],
    ) -> Optional[str]:
        """Why an apply batch's readable report, after edits that moved
        bytes, leaves some of its items out of both ``ids`` and ``declined``
        — the one problem its report re-ask names — or ``None``.

        Read-only, asked before ``_classify``. ``None`` whenever the
        classification would not read the reply as a partial application for
        that reason: a ``failed`` claim, a non-zero exit, a jail denial (its
        verdict is read off this stream), every item accounted for, or no byte
        moved (for a plan or task-list batch, its declared file).
        """
        if self.kind not in APPLY_WRITE_KINDS:
            return None
        result = context.get("result")
        if not isinstance(result, dict) or str(result.get("status") or "") == "failed":
            return None
        if context.get("exit_code") not in (0, None):
            return None
        denials = _as_jail_denials(context.get("jail_denials"))
        if denials is not None and denials.total:
            return None
        expected = [str(i) for i in (task.get("expected_ids") or [])]
        raw = result.get("ids")
        reported = [str(i) for i in raw] if isinstance(raw, list) else []
        declined = declined_items(result, expected)
        attested = {i for i in reported if i not in declined.conflicting}
        missing = [
            i for i in expected if i not in attested and i not in declined.items
        ]
        if not missing:
            return None
        task_id = str(task.get("task_id", ""))
        moved = bool(snapshot.changed()) or (
            self.kind not in SHARED_ARTIFACT_WRITE_KINDS
            and bool(self._sweep.moved_since_dispatch(task_id, snapshot))
        )
        if not moved:
            return None
        accounted = len(expected) - len(missing)
        return (
            f"The report accounts for {accounted} of the batch's "
            f"{len(expected)} items: {self._unapplied_words(missing)} "
            f"{'is' if len(missing) == 1 else 'are'} in neither `ids` nor "
            f"`declined`. Every item goes in exactly one of them: `ids` if the "
            f"previous turn applied it (or found it already applied), "
            f"`declined` with the reason it gave if it left the item unapplied "
            f"on purpose."
            + (
                f" Also: {'; '.join(declined.problems[:5])}."
                if declined.problems else ""
            )
        )

    def _restate_findings(
        self, task: Dict[str, Any], context: Dict[str, Any],
    ) -> Optional[Tuple[str, List[str]]]:
        """``(problem, accepted findings)`` when an implement task's readable
        report has an own-check finding that holds a finding the user
        accepted, word for word, with words added
        (:func:`accepted_findings_with_words_added`) — the one problem its
        report re-ask names and what such a finding may be cut down to — or
        ``None``.

        Read-only, asked before ``_classify``, and never a classification:
        the re-ask's restated report is classified like any. ``None`` for a
        check task, a ``failed`` claim, a non-zero exit, a jail denial, a
        task released by no accepted check, or no such finding."""
        if self.kind != "implement" or _batch_prompt.is_check_task(self.kind, task):
            return None
        result = context.get("result")
        if not isinstance(result, dict) or str(result.get("status") or "") == "failed":
            return None
        if context.get("exit_code") not in (0, None):
            return None
        denials = _as_jail_denials(context.get("jail_denials"))
        if denials is not None and denials.total:
            return None
        findings = batch_check_findings(result)
        if not findings:
            return None
        accepted = _check_records.accepted_findings_for(self.tasks, task, self.state)
        if not accepted:
            return None
        own, _matched = _check_records.split_accepted_findings(findings, accepted)
        flagged = _check_records.accepted_findings_with_words_added(own, accepted)
        if not flagged:
            return None
        task_id = str(task.get("task_id", ""))
        return (
            _check_records.restate_findings_problem(task_id, flagged),
            [accepted_text for _finding, _check, accepted_text in flagged],
        )

    def _verification_only(self, snapshot: TaskSnapshot) -> bool:
        """Whether this dispatch declared no files at all (``implement`` only)."""
        return self.kind == "implement" and not snapshot.declared_entries()

    def _audit_completion(
        self,
        outcome: TaskOutcome,
        runner: str,
        profile: str,
        attempt: int,
        exit_code: Optional[int],
        observed: Dict[str, Any],
        duration: float,
    ) -> None:
        self._audited.add(outcome.task_id)
        # A jail-denial count that left the verdict alone still
        # goes on the outcome (and, through it, the report and the stamp).
        note = self._grant.jail_notes.get(outcome.task_id)
        if note and note not in (outcome.reason or ""):
            outcome.reason = (
                f"{outcome.reason} {note}" if outcome.reason else note
            )
        # Every branch of `_classify` ends here, so this is the one place the
        # verdict reaches the result file that resume reads (F1).
        self._stamp_verdict(outcome)
        # The items, so a set-aside snapshot's record is findable by them
        # once its positional id belongs to another batch; a terminal record
        # (no `_classify`) reads them off the snapshot the dispatch took.
        expected_ids = outcome.expected_ids or (
            (self._snapshots.taken.get(outcome.task_id).expected_ids or [])
            if self._snapshots.taken.get(outcome.task_id) is not None else []
        )
        self.audit.completed(
            task_id=outcome.task_id, kind=self.kind, attempt=attempt,
            runner=runner, profile=profile, status=outcome.status,
            write_outcome=outcome.write_outcome, exit_code=exit_code,
            files_touched=outcome.files_touched, observed=observed,
            duration_seconds=duration, reason=outcome.reason,
            expected_ids=[str(i) for i in expected_ids],
        )

    def _remember_outcome(self, outcome: TaskOutcome) -> None:
        """Keep *outcome* by task id for :meth:`_move_repeats_of`, which may
        run before the outcome's batch joins ``result.outcomes`` (a check
        and a code task in one batch). Caller holds the effects lock."""
        self._recorded_outcomes.setdefault(outcome.task_id, []).append(outcome)

    def _split_check_repeats(self, task: Dict[str, Any], outcome: TaskOutcome) -> None:
        """Move out of a finished code task's own failing check what is the
        same finding a check task of the run already reported
        (:func:`repeated_findings_for`, the strict comparison), into
        ``batch_check_repeats``, and re-stamp its verdict. Caller holds the effects lock."""
        if not outcome.ok or outcome.verification_only or not outcome.batch_check:
            return
        repeats = _check_records.repeated_findings_for(self.tasks, task, self.state)
        if not repeats:
            return
        own, matched = _check_records.split_repeated_findings(outcome.batch_check, repeats)
        if not matched:
            return
        outcome.batch_check = own or None
        outcome.batch_check_repeats = {**outcome.batch_check_repeats, **matched}
        self._restamp_own_check(outcome.output_path, outcome.batch_check,
                                outcome.batch_check_repeats)

    def _move_repeats_of(
        self, check_id: str,
        moved: Mapping[str, Tuple[List[str], Dict[str, List[str]]]],
        result: SchedulerResult,
    ) -> None:
        """The check task recording second: what
        :func:`move_check_repeats_in_state` *moved* in ``state.json`` (the
        record ``write_record`` wrote) is moved on the code task's outcome,
        its earlier run's row in *result* and its verdict stamp too, with one
        log line. Caller holds the effects lock."""
        seen = self._recorded_outcomes
        for task_id, (own, merged) in moved.items():
            path: Optional[str] = None
            for outcome in [*result.outcomes, *seen.get(task_id, [])]:
                if outcome.task_id == task_id and outcome.ok:
                    outcome.batch_check = own or None
                    outcome.batch_check_repeats = dict(merged)
                    path = outcome.output_path or path
            for row in result.earlier_rows:
                if isinstance(row, dict) and str(row.get("task_id")) == task_id:
                    if own:
                        row["batch_check"] = check_record(own)
                    else:
                        row.pop("batch_check", None)
                    row["batch_check_repeats"] = {k: list(v) for k, v in merged.items()}
            self._restamp_own_check(
                path or os.path.join(self.phase_dir, implement_output_name(task_id)),
                own or None, merged,
            )
            self.log(
                f"[write-subagents] {task_id}'s own check reported only what check "
                f"task {check_id} reported: recorded as repeating {check_id}'s "
                f"finding, not as {task_id}'s own failure"
            )

    def _restamp_own_check(
        self, output_path: Optional[str], batch_check: Optional[List[str]],
        repeats: Mapping[str, Sequence[str]],
    ) -> None:
        """Re-write a result file's verdict ``batch_check`` and
        ``batch_check_repeats`` keys after :meth:`_split_check_repeats` or
        :meth:`_move_repeats_of` moved findings, so a resume
        skip reads what the records say; every other key is left alone."""
        if not output_path:
            return
        path = Path(output_path)
        if not path.is_file():
            return
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            verdict = data.get("verdict") if isinstance(data, dict) else None
            if not isinstance(verdict, dict):
                return
            if batch_check is not None:
                verdict["batch_check"] = check_record(batch_check)
            else:
                verdict.pop("batch_check", None)
            if repeats:
                verdict["batch_check_repeats"] = {
                    str(check_id): list(found) for check_id, found in repeats.items()
                }
            else:
                verdict.pop("batch_check_repeats", None)
            # Owner-only, as the executor wrote it (docs/development/
            # runtime.md#atomic-file-writes), through its folder held as
            # `persist_result` writes it
            # (docs/development/write-safety.md#plan-output-containment).
            write_in_plan_dir(path, json.dumps(data, indent=2).encode("utf-8"), mode=0o600)
        except (OSError, ValueError) as exc:  # noqa: BLE001 - bookkeeping
            self.log(
                f"[write-subagents] warning: could not re-record the own check "
                f"on {path.name}: {exc}"
            )

    def _stamp_verdict(self, outcome: TaskOutcome) -> None:
        """Write the classified verdict back onto the batch's result file (F1).

        ``persist_result`` runs BEFORE ``_classify``, so the file on disk
        carries the runner's own ``status`` and nothing else — and the claim
        is never the verdict. A runner that printed ``{"status": "applied",
        "ids": [all of them]}`` and then died mid-edit is a partial
        application: the loop stops at exit 3 promising "--resume
        re-dispatches this batch", and ``ResumeEvidence.already_done`` then read that same
        file — ``applied``, ids intersecting, a fingerprint recorded — and
        skipped the batch as done (measured 2026-09-16, for the crash and the
        reported-failure shapes both). The ``verdict`` key is additive (the
        result schema admits extra properties, so the file still validates)
        and its ``ok`` is the one bit resume needs: the same bit that decides
        the task's ``completed``/``failed`` status and whether an inputs
        binding is recorded, so the three records cannot disagree.
        """
        if not outcome.output_path:
            return
        path = Path(outcome.output_path)
        if not path.is_file():
            # `output_path` is where the result WOULD go, set before dispatch;
            # a dispatch that persisted nothing (a prose reply, a timeout, a
            # partial application) has no file to stamp, and the audit's
            # `completed` line and `state.json` carry its verdict instead. A
            # warning here named a file that was never meant to exist.
            return
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                return
            # `batch_ledger.verdict_record`: what the stamp holds and why,
            # read back by a resume skip (`outcome_from_verdict`).
            data["verdict"] = verdict_record(
                outcome,
                task=self._task_by_id(outcome.task_id),
                inputs_fingerprint=self._evidence.task_fingerprint,
                tree_fingerprint=self._checks.tree_fingerprint,
                sandbox_rung=self._dispatch_rungs.get(outcome.task_id),
            )
            # Owner-only, as the executor wrote it (docs/development/
            # runtime.md#atomic-file-writes), through its folder held as
            # `persist_result` writes it
            # (docs/development/write-safety.md#plan-output-containment).
            write_in_plan_dir(path, json.dumps(data, indent=2).encode("utf-8"), mode=0o600)
        except (OSError, ValueError) as exc:  # noqa: BLE001 - bookkeeping must not fail a phase
            self.log(
                f"[write-subagents] warning: could not record the verdict on "
                f"{path.name} for {outcome.task_id}: {exc}"
            )

    # -- per-batch bookkeeping (D3n: append BEFORE the next substitution) ---

    def _write_record(self, task: Dict[str, Any], facts: BatchFacts) -> BatchRecord:
        """Record *facts* in ``state.json`` through the writer both legs
        share (``write_record``), the status journaled through
        ``StateManager.update_task_status``; a state without a dict (a test
        double) takes the status alone. Caller holds the effects lock."""
        state_dict = getattr(self.state, "state", None)
        if not isinstance(state_dict, dict):
            self.state.update_task_status(facts.task_id, facts.status, reason=facts.reason)
            return BatchRecord()
        return record_batch_facts(
            state_dict, task, facts, tasks=self.tasks,
            set_status=self.state.update_task_status,
        )

    def _batch_facts(
        self, task: Dict[str, Any], outcome: TaskOutcome, status: str,
        reason: Optional[str], *, dispatched: bool, kept: bool,
    ) -> BatchFacts:
        """*outcome* as the facts both legs record (``write_record``): what
        ``util batch-done`` reads from the host's flags, read from the
        outcome. Its own check reported when it passed, failed, or only
        repeated findings that are not its own; an apply-code-fixes batch
        refused before dispatch and read as done reports no checks."""
        task_id = str(task.get("task_id", ""))
        return BatchFacts(
            task_id=task_id, kind=self.kind, status=status, reason=reason,
            leg=PROCESSED_LEG_EXECUTOR,
            processed_phase=os.path.basename(os.path.normpath(self.phase_dir)),
            check_findings=outcome.check_findings,
            batch_check=outcome.batch_check,
            own_check_ran=(
                outcome.batch_check is not None
                or bool(outcome.batch_check_accepted)
                or bool(outcome.batch_check_repeats)
            ),
            batch_check_accepted=outcome.batch_check_accepted or {},
            batch_check_repeats=outcome.batch_check_repeats or {},
            note=outcome.batch_check_note,
            listed=self._listed_outcomes.get(task_id),
            reports_checks=dispatched or kept or not outcome.ok,
            declined=dict(outcome.declined or {}),
            skipped=dict(outcome.skipped_items or {}),
            no_op=outcome.write_outcome == WRITE_NO_OP,
        )

    def _record_batch_effects(
        self,
        task: Dict[str, Any],
        outcome: TaskOutcome,
        batch_index: int,
        result: SchedulerResult,
        *,
        dispatched: bool = True,
        kept: bool = False,
    ) -> None:
        """Append prior-changes, record metrics, update task status — in that order.

        *dispatched* is ``False`` for a task refused before any runner
        started (:meth:`_refuse_before_dispatch`): no metric, and its batch
        line says it was refused. *kept* (with ``dispatched=False``) is an
        apply batch kept as it stood at the user's request
        (:meth:`_keep_at_request`): its summary is appended, its
        status is ``completed`` with that reason, and its line says so.

        The ordering is not cosmetic: the append must land before batch N+1's
        substitution reads the log, or the injected context lags a batch behind.

        The whole body is serialized. A co-scheduled group runs this from several
        threads against one in-memory ``StateManager``, one ``prior_changes.jsonl``
        and one ``state.json`` — all three read-modify-write — so without the lock
        two siblings can interleave and the later ``state.save()`` overwrites the
        earlier sibling's task status, leaving resume and both reports describing
        a run that did not happen. The work here is bookkeeping measured in
        milliseconds, so serializing it costs the batch nothing.
        """
        task_id = str(task.get("task_id", ""))
        entry_id = str(task.get("prior_changes_id") or task_id)

        if outcome.write_outcome == WRITE_APPLIED:
            summary = outcome.summary or f"batch {batch_index} applied"
        elif (outcome.write_outcome == WRITE_NO_OP and outcome.verification_only
              and outcome.check_findings):
            # A check that found problems: never "verified" on the line the
            # next batch and review-code's implementation record read.
            summary = (
                f"(check findings — {len(outcome.check_findings)} problem(s): "
                f"{'; '.join(outcome.check_findings)}; no file changed)"
            )
        elif outcome.write_outcome == WRITE_NO_OP and outcome.verification_only:
            # A check that ran and moved nothing: say it passed, in the word
            # every other surface uses for it.
            summary = (
                f"(verified — {outcome.summary or 'the check passed'}, "
                f"no file changed)"
            )
        elif outcome.write_outcome == WRITE_NO_OP:
            # The claim and the verdict agreed; say so, so the next batch reads
            # "already there" rather than "failed".
            summary = (
                f"(no-op — {outcome.summary or 'nothing needed changing'}, "
                f"verified no file changes)"
            )
        else:
            summary = None
        if not outcome.ok or task_id in self._grant.jail_failed or outcome.not_rerun:
            # A batch that is not done gets the line the native leg appends
            # for it (the executor wrote none, so later prompts
            # differed between the legs for the same history). Safe made `append`
            # supersede a changed summary per `(id,
            # phase)`: the --resume that dispatches it again replaces the line
            # with its real entry, and a task answered `--human-task <id>=skip`
            # keeps it on both legs, which tells the tasks after it that the
            # work is not there.
            summary = (
                self._failed_entry(outcome, result.refusals) if dispatched else None
            )

        # The rung the batch ran on, named on its
        # line and in the report whatever the outcome (a timeout included).
        rung = self._dispatch_rungs.get(task_id)
        if rung:
            record: Dict[str, Any] = {"sandbox_rung": rung}
            if task_id in self._grant.jail_denials:
                record["jail_denials"] = self._grant.jail_denials[task_id]
            result.sandbox_records[task_id] = record
        rung_text = f" [on {rung}]" if rung else ""
        note = self._grant.jail_notes.get(task_id)
        if note:
            rung_text += f" {note}"

        with self._effects_lock:
            if summary:
                _prior_changes.append(
                    self.output_dir, entry_id, self.phase, clip(summary, 400),
                    task_id=task_id,
                )

            # Before the metric, so the `[ETA]` line this task drives carries its
            # own 1-based position in the run (F3). No metric for a check that
            # was not run again: no child ran, and a zero would average in.
            ran = bool(not outcome.not_rerun and dispatched)
            self._eta.mark(task_id, ran=ran, ok=outcome.ok)
            # A check that reported
            # findings holds its dependents only once its batch returns
            # (`CheckHolds.block_dependents_of_checks`), so its own line and the lines
            # of the tasks beside it in the batch still counted them, and a
            # check that held the last tasks ended the run on "batch 3/5 …
            # remaining". They leave the `[ETA]` total now, as the native
            # leg's `util batch-done` takes them out before `util metrics
            # record`.
            self._eta.held.update({
                held: outcome.task_id for held in self._checks.check_holds(outcome, result)
            })
            if ran:
                self._eta.record(task, outcome, result)

            self._remember_outcome(outcome)
            if self.kind == "implement" and isinstance(
                getattr(self.state, "state", None), dict
            ):
                # Under this lock, so whichever of a code
                # task and a check task records second sees the other.
                self._split_check_repeats(task, outcome)
            status = "completed" if outcome.ok else "failed"
            reason = None if outcome.ok else (outcome.reason or outcome.status)
            if kept:
                reason = (
                    f"kept at your request (--human-task {task_id}=skip): "
                    f"{len(outcome.skipped_items)} item(s) not applied"
                )
            # The record `util batch-done` writes on the native leg.
            record = self._write_record(task, self._batch_facts(
                task, outcome, status, reason, dispatched=dispatched, kept=kept))
            if record.repeats_moved:
                self._move_repeats_of(task_id, record.repeats_moved, result)
            # A completed batch re-pins its
            # fix files to the bytes it left (no-op without a guard).
            self._commit.repin(task, outcome)
            # Persists the metric recorded just above too: it is a mutation
            # of this object's dict now, not a second writer's file (F4).
            self.state.save()

            # One line per batch, on the happy path (F7). Every other `self.log`
            # in the loop is exceptional, so a 25-minute five-batch run left an
            # 11-line log — and `status` points the user at that log.
            verdict = outcome.outcome_label or outcome.status
            if outcome.not_rerun:
                verdict = "not run again (nothing changed since it failed)"
            elif kept:
                verdict = (
                    f"kept as it stood at your request, not dispatched again "
                    f"({outcome.outcome_label or outcome.status}; not applied, "
                    f"skipped at your request: "
                    f"{clip(self._declined_words(outcome.skipped_items), 300)})"
                )
            elif not dispatched:
                verdict = "refused before dispatch" + (
                    f" ({outcome.write_outcome})" if outcome.write_outcome else ""
                )
            elif outcome.ok and outcome.check_findings:
                verdict = (
                    f"{verdict} ({len(outcome.check_findings)} problem(s): "
                    f"{clip('; '.join(outcome.check_findings), 300)})"
                )
            elif outcome.ok and outcome.batch_check:
                verdict = (
                    f"{verdict}, but its own report says "
                    f"{batch_check_words(outcome.batch_check)} "
                    f"({_check_records.quoted_findings(outcome.batch_check, 300)})"
                )
            if outcome.ok and outcome.batch_check_accepted:
                # Reported again, never its own failure.
                verdict = (
                    f"{verdict}; its own check reported again only what you "
                    f"accepted for {', '.join(outcome.batch_check_accepted)}"
                )
            if outcome.ok and outcome.batch_check_repeats:
                # A check task's finding, never its own.
                verdict = (
                    f"{verdict}; its own check reported only what check task "
                    f"{', '.join(outcome.batch_check_repeats)} reported"
                )
            if outcome.ok and outcome.declined:
                # What it left out on purpose, and why.
                verdict = (
                    f"{verdict}; declined {len(outcome.declined)}, not applied: "
                    f"{clip(self._declined_words(outcome.declined), 300)}"
                )
            elif outcome.write_outcome and not outcome.ok:
                # A failed batch whose write outcome reads
                # "clean-failure" says which failure it was.
                verdict = f"{verdict} ({outcome.status})"
            stale_line = self._commit.stale.get(task_id)
            if stale_line is not None and not dispatched:
                # The pre-dispatch re-check's
                # `[COMMIT_FIXES_STALE]` line is this batch's line.
                self.log(stale_line)
            elif dispatched and not outcome.not_rerun:
                self.log(
                    f"[write-subagents] batch {batch_index}: {task_id} "
                    f"{verdict} in "
                    f"{outcome.duration_seconds:.1f}s — "
                    f"{', '.join(outcome.files_touched) or 'no files changed'}"
                    f"{rung_text}"
                )
            else:
                # A task no runner started was named as "batch 3"
                # beside "Organized into 3 execution batches", which counts
                # the batches the run dispatches (0 to 2), so the log read as
                # four. It names no batch: none was dispatched for it.
                self.log(
                    f"[write-subagents] {task_id} {verdict} — "
                    f"{', '.join(outcome.files_touched) or 'no files changed'}"
                    f"{rung_text}"
                )

            if outcome.output_path and outcome.ok:
                # A result file only counts as this task's on resume when it was
                # produced from these inputs (D2g/D3i). The binding is written
                # here, under the same lock, because the file is one shared
                # read-modify-write map for the whole phase — and only for an
                # outcome that counts as done: a binding recorded for a failed
                # or partial batch attested that its optimistic result file was
                # current, which is half of how resume skipped it (F1).
                self._evidence.record_fingerprint(task)

    def _failed_entry(
        self, outcome: TaskOutcome, refusals: _write_context.Refusals,
    ) -> Optional[str]:
        """The prior-changes line a failed batch leaves, in the native leg's
        words (``instructions/implement.md``, the three ``apply-*.md`` cores):
        ``(task failed — …)`` for an implement task, ``(batch failed — …,
        verified no file changes)`` for an apply batch that moved nothing.

        ``None`` where the native leg appends nothing: an apply batch that
        moved bytes (its loop stops before the append), and a check not run
        again (the line of the run that ran it stands). A task refused before
        dispatch gets none either (the caller's ``dispatched``): the native
        emit records it, and no host appends for a task it never ran.
        """
        if outcome.not_rerun or outcome.task_id in self._grant.replaced_targets:
            # A replaced target: the file at the path changed under the batch,
            # and not by it — no line can say what it left.
            return None
        task = self._task_by_id(outcome.task_id) or {}
        is_check = self.kind == "implement" and not declared_file_set(task)
        last = outcome.attempts[-1] if outcome.attempts else None
        if outcome.applied_without_changes:
            what = "said applied, but its change did not land"
        elif outcome.write_outcome == WRITE_CLEAN_FAILURE and not is_check:
            if outcome.task_id in self._grant.jail_failed:
                what = "the write jail refused its edit"
            elif last is not None and last.exit_code not in (0, None):
                what = f"the runner exited {last.exit_code}"
            else:
                # It said it failed: what it said, in its own words.
                what = " ".join(str(outcome.summary or "").split()) or (
                    "it reported that it could not do the task"
                )
            if not outcome.bytes_moved and self.kind == "implement":
                what += ", no file changed"
        else:
            what = " ".join(self._stop.failure_sentence(outcome, refusals).split())
        if self.kind == "implement":
            return f"(task failed — {what})"
        if outcome.bytes_moved:
            return None
        return f"(batch failed — {what}, verified no file changes)"

    # -- tasks ----------------------------------------------------------

    def _task_by_id(self, task_id: str) -> Optional[Dict[str, Any]]:
        for task in self.tasks:
            if str(task.get("task_id", "")) == task_id:
                return task
        return None

    # -- human plan persistence -----------------------------------------

    def _persist_human_plan(self, plan: _human_task_plan.HumanTaskPlan) -> None:
        _human_task_plan.persist_human_task_plan(self.state, plan)

    def _pending_human_message(self, plan: _human_task_plan.HumanTaskPlan) -> List[str]:
        lines = [
            "",
            f"ERROR: {len(plan.pending)} human task(s) need an answer before this "
            f"phase can continue, and an unattended run may not decide for you.",
        ]
        for task_id in plan.pending:
            lines.append(f"  - {task_id}: answer with one of")
            lines.append(f"      --human-task {task_id}=done")
            lines.append(f"      --human-task {task_id}=skip")
        if not plan.strategy:
            lines.append(
                "  (or resolve the whole phase at once with --force-strategy "
                f"{'|'.join(_human_task_plan.STRATEGIES)})"
            )
        lines.append(
            "Nothing was dispatched, no file was modified, and the phase is not "
            "marked completed."
        )
        return lines

    # -- stop / finalize ------------------------------------------------

    def _stop_on_manual_gate(
        self, result: SchedulerResult, gates: Dict[str, Any],
    ) -> SchedulerResult:
        """End a run that ran nothing because a manual task gates every code
        task left: exit 3, the phase recorded started and not completed (so
        every reader offers its resume), the stop record, the closing
        ``[ETA]`` line, summary.md and the block naming the way on."""
        result.exit_code = EXIT_NEEDS_HUMAN
        self._mark_implement_started()
        self._stop.record_manual_gate(result, gates)
        gating = list(result.stop.get("manual_task_ids") or [])
        held = list(result.stop.get("held_task_ids") or [])
        return self._end_run(
            result, lambda: self._stop.manual_gate_message(result),
            eta_why=(
                f"{', '.join(gating)} left for you (manual); {len(held)} code "
                f"task(s) wait on {'it' if len(gating) == 1 else 'them'}"
            ),
            unverified=False, check_lines=False, summary=FULL_SUMMARY_LINE,
        )

    def _finalize(self, result: SchedulerResult) -> None:
        """``mark_phase_completed`` + tracking + summary + plan reference (D3n).

        Called only after every batch verified. A run that dispatched every batch
        and skipped this is a **failed** run, which is why the flag lands on the
        result rather than being left implicit.

        F4: the repository's own check runs *before* `mark_phase_completed`, and a
        non-zero exit costs the phase its completion. Per-batch verification is a
        byte comparison against a snapshot — it says the runner edited what it
        declared, never that the result still builds — so a phase that applied
        seven code fixes and marked itself completed without once asking the repo
        was reporting on a property it had not checked.
        """
        if not self._verify.run(result):
            # The stop path's shape, for the same reason: the summary is this
            # run's own account and `--resume` has no other record of what was
            # applied. Nothing is rolled back and nothing is completed — the
            # plan reference, the tracking census and the phase marker all wait
            # for a run whose check passes. And its `[ETA]` lines
            # close on the failed command, not on "ALL BATCHES COMPLETE".
            verification = result.verification or {}
            self._eta.close(
                result,
                why=(
                    f"`{verification.get('command')}` exited "
                    f"{verification.get('exit_code')}"
                    if verification.get("command") else ""
                ),
            )
            if self.summary_file:
                result.summary_file = self._reports.write_summary(result)
                result.messages.append(
                    f"Implementation summary: {result.summary_file}"
                )
            return
        self._eta.finish(result)
        # A resume of a phase already completed that dispatched nothing —
        # `implement --resume --human-task T007=done` closing a deferred
        # manual task — changed no code, so its completion keeps its date:
        # re-stamping it made review-code and apply-code-fixes read stale,
        # and the closing answer cost a review cycle. "dispatched nothing" is read off
        # the outcomes, not
        # `batches_dispatched`, which a batch of resume skips joins too —
        # a check whose findings stand, materialized again on every
        # resume and kept without a dispatch, re-stamped the date.
        # 2026-10-09: but never a date older than the review this apply
        # phase applies. A `--force` round whose review re-reports every
        # batch byte for byte keeps them all and dispatches nothing; the
        # findings are applied, so the apply is stamped after the review. Kept, the old date
        # read as "review not applied yet" to `ImproveWorkflow`, and no
        # later re-run of the composite reached `[ALREADY_COMPLETE]`.
        ran = any(not outcome.skipped for outcome in result.outcomes)
        review = _write_resume.REVIEW_PHASE_BY_WRITE_KIND.get(self.kind)
        keeps_date = (
            not ran
            and self.state.is_phase_completed(self.phase)
            and not (
                review is not None
                and self.state.completion_predates(self.phase, review)
            )
        )
        if not keeps_date:
            self.state.mark_phase_completed(self.phase)
        # F5: re-stamp `plan_hash` to what this run actually left on disk.
        # Every batch's edit is already written by the time `_finalize`
        # runs, so without this the *next* `StateManager` built on this
        # plan reads the run's own edit as a human editing the plan
        # mid-workflow and sets `plan_changed`, which
        # `implement_orchestrator.py` reports as "Plan has changed since
        # last session" for a change the plugin made.
        self.state.refresh_plan_hash()
        self.state.save()
        if self.kind in _batch_prompt.CODE_WRITE_KINDS:
            # Only a code phase records `tracked_files`: the planning
            # phases edit the plan and the task list, which are never
            # code under review.
            self._verify.finalize_tracking(result)
            # `finalize_tracking` is a file-level writer: it read the state
            # we just saved, computed `tracked_files` and wrote it back.
            # Adopt its file before touching the dict again, or the `save()`
            # below dumps the pre-finalize dict over it and the phase's
            # only deliverable is not tracked at all.
            self._reload_state()
        if self.summary_file:
            result.summary_file = self._reports.write_summary(result)
            self._reports.insert_plan_reference(result.summary_file)
            # `WriteReports.insert_plan_reference` is the one plan edit a run makes
            # *after* the stamp above (implement's own back-reference
            # insertion) — re-stamp once more so it is not left stale too.
            self.state.refresh_plan_hash()
            self.state.save()
        # A check whose findings stand and hold nothing back
        # lets the run finish; the run's own later edits (the tasks after it,
        # the plan's back-reference just above) are not a change the user
        # made, so its tree is stamped as the run leaves it, as on a stop —
        # or the next resume ran it again on files nobody touched.
        self._checks.restamp_check_trees(result)
        result.finalized = True

    def _reload_state(self) -> None:
        """Re-read `state.json` after an external writer touched it."""
        reload = getattr(self.state, "reload", None)
        if reload is None:
            return
        try:
            reload()
        except Exception as exc:  # noqa: BLE001 - bookkeeping must not fail a phase
            self.log(f"[write-subagents] warning: state reload failed: {exc}")

    def _mark_implement_started(self) -> None:
        """Record implement started, once per run, as the native emit does.

        The executor leg never wrote
        ``phases_started.implement``, so once an implement had finished, a
        later run that stopped left that completion standing — ``status``
        read implement done, and the next plain ``--implement`` started over
        instead of continuing. Called as a task is handed to this run (past
        the resume skips), so a resume that dispatches nothing — a
        ``--human-task <id>=done`` closing a manual task, a check whose
        findings stand — leaves a completed implement completed, and
        :meth:`_finalize` completes one that ran. A start-over already
        stamped it (``implement_orchestrator._start_over``). Best-effort.
        """
        if (
            self.kind != "implement" or self.dry_run
            or self._implement_started_marked
        ):
            return
        with self._effects_lock:
            if self._implement_started_marked:
                return
            self._implement_started_marked = True
            try:
                if not self.state.is_phase_started(self.phase):
                    self.state.mark_phase_started(self.phase)
                    self.state.save()
            except Exception:  # noqa: BLE001 - bookkeeping must not fail a phase
                pass

    def _started_a_runner(
        self, outcome: TaskOutcome, refusals: _write_context.Refusals,
    ) -> bool:
        """Whether this run started a runner for *outcome*'s task: not a
        resume skip, a task refused before dispatch, a check not run again
        or a batch kept as it stood at the user's request (its left-out
        items are ``skipped_items``, :meth:`_keep_at_request`)."""
        return not (
            outcome.skipped or outcome.not_rerun or outcome.skipped_items
            or outcome.task_id in refusals.before_dispatch
        )


# ---------------------------------------------------------------------------
# The one entry point an orchestrator calls
# ---------------------------------------------------------------------------

def run_write_phase(args: Any, **kwargs: Any) -> Optional[SchedulerResult]:
    """Drive a write phase through the scheduler, or decline (D3b's write twin).

    Returns ``None`` when neither ``--exec-subagents`` nor ``--dry-run-subagents``
    was requested, so the caller emits its task JSON and its follow-up marker
    exactly as before — **with the flag off, the native path is byte-identical.**
    """
    exec_requested = bool(getattr(args, "exec_subagents", False))
    dry_run = bool(getattr(args, "dry_run_subagents", False))
    if not exec_requested and not dry_run:
        return None
    kwargs.setdefault("dry_run", dry_run)
    scheduler = WriteBatchScheduler(**kwargs)
    return scheduler.run()
