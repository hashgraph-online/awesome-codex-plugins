#!/usr/bin/env python3
"""`--full`, in Python: a resumable state machine over the other modes (D1a/D1e).

``instructions/full-workflow.md`` used to *be* the sequencer: 460 lines telling a
driving agent which orchestrator to shell out to next, when to skip a phase, and
what to do when one failed. That made the whole plan-to-code workflow reachable on
exactly one host. This module is the same sequence as code — the markdown stays as
narrative, the **sequencing** lives here — so a single-shot host reaches it with
one invocation and a detached run can own it end to end.

What that buys, and what it costs:

* **One state machine, on the existing ``state.json``.** There is no second
  progress file: a phase is done when *it* recorded itself done
  (``phases_completed`` / ``phases_skipped``), which is the same record `status`
  reports and the same one every standalone invocation writes. So resume is not a
  feature bolted on here — it is what the loop already reads. Every phase boundary
  is a resume point.
* **The outcome is verified, never the phase's claim.** A phase that returns 0 but
  did not record itself complete (the ordinary native-host case: it printed
  ``[VALIDATION_PENDING]`` and stopped for a subagent to run) is *not* progress, so
  the workflow stops there with exit **3**, naming the phase, the follow-up that
  phase printed, and the ``--resume`` re-invocation. That is D6 row 14: under
  ``--yes`` a hard failure is terminal, never a question.
* **This is ``ensure_prerequisites``' missing caller.** Rows 5 and 6 auto-run the
  missing apply phase **once** and re-check (D6a); the runner is injected from
  here, because applying suggestions needs a subagent channel this module has and
  ``check_workflow_prerequisites.py`` does not. The auto-run is bounded here too:
  at most once per phase per run, and a second unmet re-check is exit 3 rather than
  a retry.
* **No phase is entered on a guess.** Row 12 (review the tasks?) resolves from
  ``--yes`` / ``--review-tasks`` and records a skip otherwise; the two conditional
  apply phases ask the *existing* prerequisite counters whether there is anything
  to apply, and record their skip when there is not — so `status` never shows a
  phase as perpetually pending.

Usage::

    uv run --project <skill-dir> -- python <skill-dir>/multi_llm.py \\
        full <plan> [--yes] [--models …|--quick] [--review-tasks] [--resume]
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Union

# Absolute, symlinks preserved — see utils/cli_common.py.
sys.path.insert(0, str(Path(os.path.abspath(__file__)).parent))

import modes as mode_table
from check_workflow_prerequisites import (
    _grouped_has_suggestions,
    check_apply_task_suggestions_prerequisite,
    ensure_prerequisites,
    record_prerequisite_skip,
)
from utils.cli_common import (
    ERROR_MAX_CHARS,
    EXIT_ERROR,
    EXIT_NEEDS_HUMAN,
    EXIT_NOTHING_TO_DO,
    EXIT_OK,
    active_result,
    build_parent_parser,
    dispatcher_command,
    record_artifact,
    record_error,
    record_next,
)
from utils.output_handler import get_output_dir, get_phase_dir
from utils.state_manager import StateManager
from utils.stream_bootstrap import bootstrap_streams
from utils.text_clip import clip, drop_said_clauses, join_clauses
from utils import unattended as unattended_mod
from utils.unattended import NeedsHuman

#: Step outcomes the driver branches on.
DONE = "done"
SKIPPED = "skipped"
ALREADY = "already-complete"
FAILED = "failed"

#: The phases whose real work is a **batch loop an invoker runs**, mapped to the
#: directory each leaves that loop's instruction document in. Every one of
#: them records itself *started* the moment the document is written — before a
#: single edit exists — and completed only by the invoker's closing command
#: (``<mode> --plan-file … --mark-completed``, ``util finalize-tracking
#: --mark-completed`` for implement), so a recorded completion IS a claim about
#: work done and a loop that stopped early never reaches it. Until 2026-10-05
#: ``apply-suggestions`` and ``implement`` recorded themselves *completed* at
#: emit time, which is why this driver checks the document itself: inside
#: ``full`` there is no invoker to run the loop, and the exit-0 phase that
#: handed its batches to nobody must not count as progress.
#: ``apply-code-fixes``'s mode word is not its phase dir: the orchestrator's own
#: ``phase_name`` is ``apply-fixes``. Its completion record uses the **mode**
#: word (``apply-code-fixes``), not the dir word, because it is what
#: ``PHASE_PREREQUISITES`` and the executor's ``_finalize`` both use.
WRITE_PHASE_DIRS: Dict[str, str] = {
    "apply-suggestions": "apply-suggestions",
    "apply-task-suggestions": "apply-task-suggestions",
    "apply-code-fixes": "apply-fixes",
}

#: The fourth write phase. Its document is ``--output``, not a plan-dir file.
IMPLEMENT_PHASE = "implement"


@dataclass
class StepReport:
    """What one step did, for the final report."""

    label: str
    phase: str
    outcome: str
    detail: str = ""
    exit_code: Optional[int] = None


@dataclass
class Step:
    """One entry in the sequence.

    Attributes:
        phase: The ``state.json`` phase this step must end up recording, or ``""``
            for an advisory step that records nothing (consolidation).
        label: How the report names it.
        run: ``() -> (outcome, detail, exit_code)``.
        skippable: Whether a recorded completion/skip lets the driver pass over it
            (every real phase; never the advisory ones, which are cheap and
            idempotent).
    """

    phase: str
    label: str
    run: Callable[[], Tuple[str, str, Optional[int]]]
    skippable: bool = True


# ---------------------------------------------------------------------------
# Arguments
# ---------------------------------------------------------------------------

def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="full_workflow_orchestrator.py",
        description=(
            "Run the whole plan-to-code workflow as one resumable sequence: "
            "review-plan, apply-suggestions, generate-tasks, review-tasks, "
            "apply-task-suggestions, implement, review-code, apply-code-fixes."
        ),
        parents=[build_parent_parser()],
    )
    parser.add_argument(
        "--plan-file", required=True, help="Path to the plan markdown file"
    )
    parser.add_argument(
        "--models",
        nargs="+",
        default=None,
        metavar="PROVIDER:MODEL",
        help="Models for the two fan-out phases (D6 row 2). Omit to use "
             "providers.yaml defaults; --quick is the other non-interactive answer.",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Use the quick model set for the fan-out phases (D6 row 2).",
    )
    parser.add_argument(
        "--review-tasks",
        action="store_true",
        help="Opt in to the optional task-review phase (D6 row 12). Implied by "
             "--yes; without either, the phase is recorded skipped rather than "
             "left perpetually pending.",
    )
    parser.add_argument(
        "--consolidate",
        action="store_true",
        help="Force the post-review-plan consolidation step (D6 row 4). Under "
             "--yes it auto-runs when review-plan recommends it.",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Continue from the first phase state.json does not record as "
             "completed or skipped (D6 row 14's named re-invocation). This is also "
             "the default behavior; the flag additionally forwards --resume to the "
             "phases that support it, so partially processed batches are not "
             "re-applied.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-run every phase even when state.json records it completed or "
             "skipped. Not forwarded to the phases (there --force means "
             "'re-invoke the models'); it only clears this loop's skipping.",
    )
    return parser.parse_args(list(argv) if argv is not None else None)


# ---------------------------------------------------------------------------
# The workflow
# ---------------------------------------------------------------------------

class FullWorkflow:
    """The state machine. One instance per invocation.

    A composite mode that runs a few of these phases subclasses it rather than
    copying it, so everything that names *which* workflow this is lives on the
    class and is read through the instance: a read that bound a module global
    would hand the subclass `full`'s run dir, progress record and resume
    command. The hooks (:meth:`step_argv`, :meth:`skip_reason`,
    :meth:`nothing_to_do`, :meth:`resume_flags`, :meth:`report_artifacts`)
    default to `full`'s own behaviour.
    """

    #: The mode word, and the run-dir name ``--detach`` claims. `full` records no
    #: workflow phase of its own — each phase it runs records itself — but it does
    #: own a directory for ``.status.json``, the run log and the lock.
    MODE_NAME = "full"
    RUN_DIR_PHASE = "full"

    #: Where the workflow's own bookkeeping lands in ``state.json``. Display and
    #: diagnostics only: the resume decision reads ``phases_completed`` /
    #: ``phases_skipped``, never this key, so a hand-deleted record cannot make
    #: the workflow re-run a phase that really did complete.
    STATE_KEY = "full_workflow"

    #: The heading :meth:`print_report` prints.
    REPORT_TITLE = "Full Workflow Summary"

    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.plan_path = Path(os.path.abspath(args.plan_file))
        self.unattended = bool(getattr(args, "yes", False))
        self.plan_dir = get_output_dir(self.plan_path)
        self.reports: List[StepReport] = []
        #: What each step that ran recorded on the result line, in step order
        #: (:meth:`_close_step_result`), for a detached caller's poll.
        self.step_results: List[Dict[str, Any]] = []
        #: Phases whose apply step this run already auto-ran (D6a: at most once
        #: per phase per run — a second unmet re-check is exit 3, not a retry).
        self.auto_ran: List[str] = []
        self._state: Optional[StateManager] = None

    # -- state ----------------------------------------------------------
    @property
    def state(self) -> StateManager:
        """A freshly read ``StateManager``.

        Re-read rather than cached: each phase runs in this process and writes its
        own completion through its own manager instance, so a cached copy would
        answer "is this phase done?" from before the phase ran.
        """
        return StateManager(self.plan_path)

    def _recorded(self, phase: str) -> Optional[str]:
        """``"completed"``/``"skipped"`` when *phase* is already accounted for."""
        state = self.state
        if state.is_phase_completed(phase):
            return "completed"
        if state.is_phase_skipped(phase):
            return "skipped"
        return None

    def _record_skip(self, phase: str, reason: str) -> Tuple[str, str, Optional[int]]:
        """Record *phase* skipped, unless it is already recorded completed.

        The guard matters under ``--force``, where the driver re-enters a phase the
        conditional counters would report as "nothing to apply" *because* it already
        ran — recording a skip over a completed phase would make `status` show both.
        """
        state = self.state
        if state.is_phase_completed(phase):
            return ALREADY, "completed", None
        record_prerequisite_skip(state, phase, reason=reason)
        return SKIPPED, reason, None

    def _record_progress(self, *, current: str, failed: Optional[str] = None) -> None:
        state = self.state
        record = dict(state.get(self.STATE_KEY) or {})
        record.update({
            "current_phase": current,
            "failed_phase": failed,
            "steps": {r.phase or r.label: r.outcome for r in self.reports},
        })
        state.set(self.STATE_KEY, record)
        state.save()

    # -- in-process dispatch -------------------------------------------
    def run_mode(self, mode_word: str, extra: Sequence[str]) -> int:
        """Call another mode's ``main(argv)`` in-process (D1a's dispatch rule).

        Deliberately not ``multi_llm.main``: the dispatcher owns one
        ``MULTI_LLM_RESULT`` line and one result context per invocation, and
        nesting it would emit a second line and deactivate the outer context. The
        *target* is resolved through the same ``modes.py`` table the dispatcher
        uses, so there is still exactly one mode → module mapping.
        """
        mode = mode_table.resolve(mode_word)
        if mode is None or not mode.target_module:  # pragma: no cover - table-guarded
            raise RuntimeError(f"no dispatch target for mode {mode_word!r}")
        target = getattr(
            importlib.import_module(mode.target_module), mode.target_attr
        )
        argv = ["--plan-file", str(self.plan_path), *extra]
        print(f"\n$ {dispatcher_command(mode.name, self.plan_path, *extra)}")
        self._clear_next()
        try:
            if inspect.iscoroutinefunction(target):
                import asyncio

                from utils import process_control

                # As the dispatcher's `_call_target` does: a Ctrl-C stops the
                # phase's CLIs inside the cancellation, before `asyncio.run`
                # joins the worker threads that are waiting on them.
                result = asyncio.run(
                    process_control.sweeping_live_clis_on_interrupt(target(argv))
                )
            else:
                result = target(argv)
        except SystemExit as exc:
            code = exc.code
            if code is None:
                return EXIT_OK
            if isinstance(code, int):
                return code
            print(str(code), file=sys.stderr)
            return EXIT_ERROR
        except NeedsHuman as exc:
            print(exc.message, file=sys.stderr)
            return exc.exit_code
        return EXIT_OK if result is None else int(result)

    @staticmethod
    def _clear_next() -> None:
        """Drop a previous phase's follow-up so a stale one is never re-reported."""
        ctx = active_result()
        if ctx is not None:
            ctx.next = None

    @staticmethod
    def _pending_next() -> Optional[str]:
        ctx = active_result()
        return ctx.next if ctx is not None else None

    @staticmethod
    def _clear_error() -> None:
        """Drop an earlier step's ``error`` line before the next step runs.

        A step that recorded one and still finished did not stop the run, so
        its line is not the stop :meth:`_phase_failed` reports for a later one.
        """
        ctx = active_result()
        if ctx is not None:
            ctx.error = None

    @staticmethod
    def _open_step_result() -> Optional[Dict[str, Any]]:
        """The result line's notice, counts and validation context before a
        step, its notice set aside so the step's own can be told apart."""
        ctx = active_result()
        if ctx is None:
            return None
        mark = {
            "notice": ctx.notice,
            "validation_counts": ctx.validation_counts,
            "validation_context": ctx.validation_context,
        }
        ctx.notice = None
        return mark

    def _close_step_result(self, step: Step, mark: Optional[Dict[str, Any]]) -> None:
        """Keep what *step* recorded on the result line (:attr:`step_results`),
        and put its notice after the earlier steps'.

        Joined, never replaced: a phase records its notice as if it were the
        only one, so the apply's replaced the review's truncation sentence.
        A clause an earlier step said word for word is not said again
        (``text_clip.drop_said_clauses``); the record keeps the step's whole
        notice, as it recorded it. The counts and validation context are the
        step's own only when it recorded them (each record stores a new
        object), and a step that recorded none of the three is not kept.
        """
        ctx = active_result()
        if ctx is None or mark is None:
            return
        own = ctx.notice
        ctx.notice = join_clauses(
            [mark["notice"], drop_said_clauses(own, mark["notice"])]) or None
        result: Dict[str, Any] = {"notice": own} if own else {}
        for key in ("validation_counts", "validation_context"):
            value = getattr(ctx, key)
            if value and value is not mark[key]:
                result[key] = dict(value)
        if result:
            self.step_results.append({"phase": step.phase or step.label, **result})

    # -- flag forwarding -----------------------------------------------
    def common_flags(self) -> List[str]:
        """Cross-cutting flags every phase gets, and only those.

        ``--detach``/``--if-not-running``/``--max-detached`` are deliberately
        absent: this run already crossed the detach boundary, and a phase that
        forked again would leave the workflow polling a child it does not own.
        The ``--internal-*`` re-entry flags are absent for the same reason.
        """
        flags: List[str] = []
        if getattr(self.args, "host", None):
            flags += ["--host", str(self.args.host)]
        if self.unattended:
            flags += ["--yes"]
        elif getattr(self.args, "interactive", False):
            flags += ["--interactive"]
        if getattr(self.args, "exec_subagents", False):
            flags += ["--exec-subagents"]
        if getattr(self.args, "dry_run_subagents", False):
            flags += ["--dry-run-subagents"]
        if getattr(self.args, "skip_prerequisites", False):
            flags += ["--skip-prerequisites"]
        return flags

    def model_flags(self) -> List[str]:
        """Row 2, resolved once and reused: the same models in both fan-out phases."""
        if self.args.models:
            return ["--models", *self.args.models]
        if self.args.quick:
            return ["--quick"]
        return []

    def apply_flags(self) -> List[str]:
        """The apply phases' unattended answers (rows 10/11).

        Both flags are gated the same way, because both *are* the unattended
        dispositions of those two rows — the core appends ``--agent-decide
        --no-confirm`` only under ``--yes``. Attended, the no-selection
        confirmation stays a real gate: the phase prints ``confirmation_needed``
        and records nothing, which this driver reads as "did not finish" and ends
        at exit 3 naming the phase (row 14). Silently applying every valid item
        nobody selected is the one thing an attended run must not do.
        """
        flags: List[str] = []
        if self.unattended:
            flags += [unattended_mod.AGENT_DECIDE_FLAG, "--no-confirm"]
        if getattr(self.args, "resume", False):
            flags += ["--resume"]
        return flags

    def step_argv(self, step: str) -> List[str]:
        """The flags after the plan for *step*: a mode word, or ``"consolidate"``.

        One hook for the five steps a composite reuses (both reviews, both
        applies of their findings, and review-plan's consolidation pass), so a
        subclass that gives them its own flags reaches every one, the inherited
        steps included. The steps only `full` runs, and :meth:`apply_runner`'s
        auto-run, build their own argv.
        """
        if step in ("review-plan", "review-code"):
            return self.model_flags() + self.common_flags()
        if step in ("apply-suggestions", "apply-code-fixes"):
            return self.apply_flags() + self.common_flags()
        if step == "consolidate":
            return ["--consolidate", *self.common_flags()]
        raise ValueError(f"no step_argv for step {step!r}")

    # -- the prerequisite gates (D6a rows 5/6) --------------------------
    def apply_runner(self, site_id: str) -> Optional[Callable[[str], int]]:
        """The runner ``ensure_prerequisites`` auto-runs, bounded per phase.

        Supplied only under ``--yes``: the D6 table's auto-run is the *unattended*
        resolution of rows 5/6. Attended, the gate keeps its standalone ending and
        names the fix, which in the normal sequence never fires — Phase 2 runs
        before Phase 3, so the gate is satisfied rather than repaired.
        """
        if not self.unattended:
            return None

        def runner(phase: str) -> int:
            if phase in self.auto_ran:
                print(
                    f"[PREREQUISITE_UNMET] {phase} was already auto-run once in "
                    f"this run and the gate is still unmet; not retrying (D6a: at "
                    f"most once per phase per run).",
                    file=sys.stderr,
                )
                return EXIT_NEEDS_HUMAN
            self.auto_ran.append(phase)
            unattended_mod.record_resolution(
                str(self.run_dir),
                site_id,
                f"auto-ran {phase} once, then re-checked the gate",
            )
            return self.run_mode(phase, self.apply_flags() + self.common_flags())

        return runner

    def gate(self, mode_word: str, site_id: str) -> Optional[str]:
        """``None`` when *mode_word* may run, else the blocking message."""
        outcome = ensure_prerequisites(
            self.plan_path,
            mode_word,
            unattended=self.unattended,
            in_workflow=True,
            skip_prerequisites=bool(getattr(self.args, "skip_prerequisites", False)),
            apply_runner=self.apply_runner(site_id),
        )
        for notice in outcome.notices:
            print(notice)
        if outcome.met:
            return None
        return outcome.message or (
            f"[PREREQUISITE_UNMET] {mode_word}: prerequisites are not met."
        )

    # -- run dir --------------------------------------------------------
    @property
    def run_dir(self) -> Path:
        return get_phase_dir(self.plan_path, self.RUN_DIR_PHASE)

    # ------------------------------------------------------------------
    # Steps
    # ------------------------------------------------------------------
    def steps(self) -> List[Step]:
        return [
            Step("review-plan", "Phase 1: Review Plan", self.step_review_plan),
            Step("", "Phase 1b: Consolidation", self.step_consolidate,
                 skippable=False),
            Step("apply-suggestions", "Phase 2: Apply Suggestions",
                 self.step_apply_suggestions),
            Step("generate-tasks", "Phase 3: Generate Tasks",
                 self.step_generate_tasks),
            Step("review-tasks", "Phase 3b: Review Tasks", self.step_review_tasks),
            Step("apply-task-suggestions", "Phase 3c: Apply Task Suggestions",
                 self.step_apply_task_suggestions),
            Step("implement", "Phase 4: Implement", self.step_implement),
            Step("code-review", "Phase 5: Review Code", self.step_review_code),
            Step("apply-code-fixes", "Phase 6: Apply Code Fixes",
                 self.step_apply_code_fixes),
        ]

    def step_review_plan(self) -> Tuple[str, str, Optional[int]]:
        code = self.run_mode("review-plan", self.step_argv("review-plan"))
        return self._verify("review-plan", code)

    def step_consolidate(self) -> Tuple[str, str, Optional[int]]:
        """Row 4: auto-run consolidation when review-plan recommended it.

        Advisory by construction — consolidation clusters the *report*, it does not
        gate anything — so a failure here is a warning and the workflow continues.
        Without ``--exec-subagents`` the consolidate pass prints its batch marker
        for a native invoker and returns; that is the same "not progress" state as
        any other pending batch, but it cannot block a workflow whose next phase
        does not read consolidated output.
        """
        if not self.args.consolidate:
            if not self.unattended:
                return SKIPPED, "not requested (--consolidate)", None
            reason = consolidation_skip_reason(self.plan_dir)
            if reason:
                return SKIPPED, reason, None
            unattended_mod.record_resolution(
                str(self.run_dir),
                unattended_mod.row(4).site_id,
                "auto-ran consolidation once ([CONSOLIDATION_RECOMMENDED])",
            )
        code = self.run_mode("review-plan", self.step_argv("consolidate"))
        if code != EXIT_OK:
            print(
                f"multi-llm warning: consolidation exited {code}; continuing "
                f"(it clusters the review report and gates nothing).",
                file=sys.stderr,
            )
            return SKIPPED, f"consolidation exited {code} (non-fatal)", code
        return DONE, "", code

    def step_apply_suggestions(self) -> Tuple[str, str, Optional[int]]:
        code = self.run_mode(
            "apply-suggestions", self.step_argv("apply-suggestions")
        )
        return self._verify("apply-suggestions", code)

    def step_generate_tasks(self) -> Tuple[str, str, Optional[int]]:
        """Phase 3, through ``generate_tasks_orchestrator`` — never an inlined prompt.

        Called as a Python function rather than through :meth:`run_mode` for one
        reason: this is where ``ensure_prerequisites``' ``apply_runner`` is
        injected (row 5). Everything else about the phase — materialization,
        dispatch, validation, the in-process ``update_plan_tasks`` and the
        ``TASKS_FILE`` verification — is the standalone mode's code, unchanged.
        """
        import generate_tasks_orchestrator as generate_tasks

        child = argparse.Namespace(**vars(self.args))
        child.reaggregate = False
        # `full --force` re-runs phases; it never re-invokes the models — with one
        # exception, and it is the one the phase's own failure message names. A
        # `task_generation_result.json` a native invoker persisted can be
        # schema-invalid, and the resume branch re-consumes it forever: every
        # `--resume` *and* `--force` would fail identically at consume time while
        # the printed fix ("re-run with --force to re-dispatch") pointed at a flag
        # this driver swallowed. So when the phase has no recorded completion,
        # `--force` travels: there is no earlier progress a re-dispatch could
        # discard. Once it *is* recorded, force means "re-run the phase" again.
        child.force = bool(getattr(self.args, "force", False)) and (
            self._recorded("generate-tasks") is None
        )
        child.detach = False
        child.internal_worker = False
        extra = list(self.common_flags())
        if child.force:
            extra += ["--force"]
        print(f"\n$ {dispatcher_command('generate-tasks', self.plan_path, *extra)}")
        self._clear_next()
        try:
            code = generate_tasks.run_generate_tasks(
                child,
                in_workflow=True,
                apply_runner=self.apply_runner(unattended_mod.row(5).site_id),
            )
        except SystemExit as exc:  # pragma: no cover - defensive
            code = EXIT_OK if exc.code is None else int(exc.code)
        except NeedsHuman as exc:
            print(exc.message, file=sys.stderr)
            code = exc.exit_code
        # `--full` never proceeds past a failed generation: implementing against a
        # plan with no tasks is the error `--implement`'s auto-detection already
        # reports, and every later phase would treat an invented list as ground
        # truth.
        return self._verify("generate-tasks", code)

    def step_review_tasks(self) -> Tuple[str, str, Optional[int]]:
        """Row 12: run it under ``--yes``/``--review-tasks``, else record the skip."""
        if not (self.unattended or self.args.review_tasks):
            return self._record_skip(
                "review-tasks", "not requested (--review-tasks not passed)"
            )
        if self.unattended and not self.args.review_tasks:
            unattended_mod.record_resolution(
                str(self.run_dir),
                unattended_mod.row(12).site_id,
                "ran review-tasks automatically",
            )
        code = self.run_mode(
            "review-tasks", self.model_flags() + self.common_flags()
        )
        return self._verify("review-tasks", code)

    def step_apply_task_suggestions(self) -> Tuple[str, str, Optional[int]]:
        """The three-case conditional, answered by the existing counter.

        (a) review-tasks was skipped, (b) it ran and found nothing, (c) it found
        findings. Cases (a) and (b) are recorded skips — ``check_workflow_``
        ``prerequisites.check_apply_task_suggestions_prerequisite`` already
        distinguishes them, so the decision is not re-derived here.
        """
        state = self.state
        # The effective status (`_recorded`: a completion wins over a stale skip
        # record), the precedence `get_workflow_status` uses too.
        if self._recorded("review-tasks") == "skipped":
            return self._record_skip(
                "apply-task-suggestions", "Skipped: review-tasks was not executed"
            )
        check = check_apply_task_suggestions_prerequisite(state, self.plan_dir)
        if check.get("met"):
            return self._record_skip(
                "apply-task-suggestions",
                f"Skipped: {check.get('reason', 'nothing to apply')}",
            )
        code = self.run_mode(
            "apply-task-suggestions", self.apply_flags() + self.common_flags()
        )
        return self._verify("apply-task-suggestions", code)

    def step_implement(self) -> Tuple[str, str, Optional[int]]:
        blocked = self.gate("implement", unattended_mod.row(6).site_id)
        if blocked:
            print(blocked, file=sys.stderr)
            return FAILED, "prerequisites unmet (D6 row 6)", EXIT_NEEDS_HUMAN
        extra = list(self.common_flags())
        if getattr(self.args, "resume", False):
            extra += ["--resume"]
        code = self.run_mode("implement", extra)
        return self._verify("implement", code)

    def step_review_code(self) -> Tuple[str, str, Optional[int]]:
        code = self.run_mode("review-code", self.step_argv("review-code"))
        return self._verify("code-review", code)

    def step_apply_code_fixes(self) -> Tuple[str, str, Optional[int]]:
        """Run apply-code-fixes only when code-review left something to fix.

        The review's own status is checked before any file, as
        :meth:`step_apply_task_suggestions` does for review-tasks: a skipped
        code-review is a recorded skip whatever ``grouped.json`` an earlier
        review left on disk. That status is the effective one (:meth:`_recorded`,
        the precedence ``get_workflow_status`` uses too): a code-review that
        completed after an earlier skip is completed — ``mark_phase_completed``
        leaves the stale skip record in place — so its findings still reach
        apply-code-fixes. Then the one predicate ``status``'s workflow view
        asks too (``check_workflow_prerequisites._grouped_has_suggestions``), so
        the two cannot disagree.
        """
        if self._recorded("code-review") == "skipped":
            return self._record_skip(
                "apply-code-fixes", "Skipped: code-review was not executed"
            )
        if not _grouped_has_suggestions(self.plan_dir / "code-review" / "grouped.json"):
            return self._record_skip(
                "apply-code-fixes",
                "Skipped: code review produced zero actionable findings",
            )
        code = self.run_mode(
            "apply-code-fixes", self.step_argv("apply-code-fixes")
        )
        return self._verify("apply-code-fixes", code)

    # ------------------------------------------------------------------
    # The driver
    # ------------------------------------------------------------------
    def _write_phase_document(self, phase: str) -> Optional[Path]:
        """Where *phase* left its batches for an invoker, or ``None``.

        ``None`` for every read/analyze phase: they have no batch loop, so there is
        nothing for this check to look at.
        """
        subdir = WRITE_PHASE_DIRS.get(phase)
        if subdir:
            return self.plan_dir / subdir / "orchestrator_output.json"
        if phase != IMPLEMENT_PHASE:
            return None
        # `implement` writes its batches to `--output`, which this driver never
        # passes — so the phase used its own default. Recomputed through the
        # phase's own function (never a second spelling of that path) and only
        # once its git-root precondition holds, so the probe cannot exit for it.
        try:
            import implement_orchestrator

            if not implement_orchestrator.get_project_root(str(self.plan_path)):
                return None
            return Path(
                implement_orchestrator.resolve_default_output(
                    Path(self.plan_path).resolve()
                )
            )
        except (ImportError, SystemExit):  # pragma: no cover - defensive
            return None

    def _unexecuted_batches(self, phase: str) -> int:
        """How many batches *phase* emitted that nothing in this run could apply.

        ``full`` runs every phase **inside this one process**: there is no invoker
        between a phase and the next one, so the only thing that can execute a
        write phase's batches here is the write scheduler under
        ``--exec-subagents`` (which finalizes — and therefore completes the phase —
        only after every batch verified, D3n). Without it the batches are handed to
        an invoker that never arrives: the phase exits 0 recorded *started*, and
        this is what tells that apart from a phase that never emitted anything.

        Zero is the answer whenever there is no evidence of a pending loop — no
        document, an unreadable one, one belonging to another plan, or one
        declaring no batches (the honest "nothing to apply" completion this must
        not turn into a failure).
        """
        if getattr(self.args, "exec_subagents", False):
            return 0
        document = self._write_phase_document(phase)
        if document is None or not document.is_file():
            return 0
        try:
            payload = json.loads(document.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            return 0
        if not isinstance(payload, dict):
            return 0
        declared = payload.get("plan_file")
        if declared and os.path.realpath(str(declared)) != os.path.realpath(
            str(self.plan_path)
        ):
            # `implement`'s default output lives in a shared `.multi-llm/tmp/`;
            # a document for another plan says nothing about this phase.
            return 0
        batches = payload.get("batches")
        return len(batches) if isinstance(batches, list) else 0

    def _unexecuted_write_phase(self, phase: str, pending: int) -> str:
        """Print the row-14 explanation for *phase*, and return the report detail."""
        follow_up = dispatcher_command(
            phase, self.plan_path, *(["--yes"] if self.unattended else []),
        )
        document = self._write_phase_document(phase)
        print(
            "\n".join([
                f"[WRITE_PHASE_NOT_EXECUTED] {phase} exited 0 after writing "
                f"{pending} batch(es) to",
                f"       {document}",
                "       — but nothing applied them: `full` runs every phase "
                "inside this one process,",
                "       so with --exec-subagents unset there is no invoker "
                "between this phase and the",
                "       next. Run the phase on its own, so your host's subagents "
                "execute its batches,",
                "       then resume the workflow — or re-run the whole workflow "
                "with --exec-subagents,",
                "       which applies the batches in process.",
            ]),
            file=sys.stderr,
        )
        record_next(follow_up)
        return (
            f"exited 0, but the {pending} batch(es) it emitted were never "
            f"executed"
        )

    def _verify(self, phase: str, code: int) -> Tuple[str, str, Optional[int]]:
        """A phase counts as progress only if *it* recorded itself (D2i's rule).

        Exit 0 is the phase's claim; ``state.json`` is the artifact. The common way
        the two disagree is the native-invoker path — a fan-out that stopped at
        ``[VALIDATION_PENDING]`` exits 0 with the phase deliberately incomplete —
        and marching on from there would review, implement and code-review against
        output nobody produced.

        A write phase needs the *second* artifact check
        (:meth:`_unexecuted_batches`): on the native leg it exits 0 recorded
        *started* with its batch document written and nobody to run it, and
        until 2026-10-05 two of the four recorded themselves *completed* there.
        Trusting either would generate tasks from a plan whose suggestions were
        never applied and code-review an unimplemented tree — the same
        claim-vs-artifact failure, one phase further on. The check runs before
        the completion test so a stale completion record cannot mask it, and
        the explanation names the pending document rather than the generic
        "records no completion".
        """
        recorded = self._recorded(phase)
        if code in (EXIT_OK, EXIT_NOTHING_TO_DO):
            pending = self._unexecuted_batches(phase)
            if pending and (recorded or self.state.is_phase_started(phase)):
                return FAILED, self._unexecuted_write_phase(phase, pending), code
        if code in (EXIT_OK, EXIT_NOTHING_TO_DO) and recorded:
            return DONE, recorded, code
        if code in (EXIT_OK, EXIT_NOTHING_TO_DO):
            return (
                FAILED,
                f"exited {code} but state.json records no completion for "
                f"'{phase}', so the phase did not finish",
                code,
            )
        return FAILED, f"exited {code}", code

    def skip_reason(self, step: Step) -> Optional[str]:
        """The word :meth:`run` passes over *step* with, or ``None`` to run it.

        Asked only for a skippable step and never under ``--force``. `full`
        passes over any phase already recorded completed or skipped
        (:meth:`_recorded`), which is what makes every phase boundary a resume
        point.
        """
        return self._recorded(step.phase)

    def nothing_to_do(self) -> bool:
        """Whether every step of this workflow would be passed over.

        A composite asks it before its detach boundary, to exit 2 instead of
        launching a worker with nothing to run. `full` answers ``False``: a
        re-run of a finished workflow passes over each recorded phase and
        exits 0, as it always has.
        """
        return False

    def resume_flags(self) -> List[str]:
        """The flags after the plan in row 14's re-invocation.

        The run's own ``--yes`` and ``--resume``, never an invented flag: an
        attended run is resumed attended.
        """
        return [*(["--yes"] if self.unattended else []), "--resume"]

    def continuation_command(self) -> str:
        """Row 14's re-invocation: ``<mode> <plan> <resume flags>``.

        On a commit review (the brief's ``state.json`` holds
        ``commit_range``; ``improve-commits``) it is spelled through the
        commit spelling hook (plans/review-commits.md §2.8): the pinned
        ``<base12>..<head12>`` (the brief path on a root range) in place of
        the plan, and none of the flags its front door synthesises or
        consumes. Every other run keeps ``dispatcher_command`` byte for byte.
        """
        from utils import next_phase
        from utils.commit_spelling import spell_command

        view = next_phase.commit_view_for(self.MODE_NAME, str(self.plan_path))
        if view is None:
            return dispatcher_command(self.MODE_NAME, self.plan_path, *self.resume_flags())
        return spell_command(self.MODE_NAME, self.plan_path, *self.resume_flags(), view=view)

    def _commit_spelled(self, command: Optional[str]) -> Optional[str]:
        """*command*, a follow-up the stopped phase printed, in the commit
        spelling when it is a dispatcher command naming this plan and the
        plan is a commit brief (plans/review-commits.md §2.8: the stop prints
        it and records it as ``next``); anything else comes back unchanged."""
        if not command:
            return command
        import shlex

        try:
            tokens = shlex.split(command)
        except ValueError:
            return command
        script = next((index for index, token in enumerate(tokens)
                       if os.path.basename(token) == "multi_llm.py"), None)
        if script is None or script + 2 >= len(tokens):
            return command
        mode, plan, rest = tokens[script + 1], tokens[script + 2], tokens[script + 3:]
        if plan.startswith("-") or (
                os.path.realpath(plan) != os.path.realpath(str(self.plan_path))):
            return command
        from utils import next_phase
        from utils.commit_spelling import spell_command

        view = next_phase.commit_view_for(mode, plan)
        if view is None:
            return command
        return spell_command(next_phase.commit_mode_word(mode, view), plan, *rest, view=view)

    def _phase_failed(self, step: Step, detail: str, code: Optional[int]) -> int:
        """D6 row 14: exit 3, name the phase and the ``--resume`` re-invocation
        (:meth:`continuation_command`), which is also the result line's
        ``next``; on a commit brief a follow-up the phase printed reads in the
        commit spelling too (:meth:`_commit_spelled`)."""
        resume = self.continuation_command()
        pending = self._commit_spelled(self._pending_next())
        head = f"{step.label} did not complete ("
        tail = "). The workflow stopped here; no later phase ran."
        lines = ["", f"ERROR: {head}{detail}{tail}"]
        if pending:
            lines += [
                "       That phase printed a follow-up of its own — run it first:",
                f"         {pending}",
            ]
        lines += [
            "       Then continue the workflow from this phase:",
            f"         {resume}",
            "       A failed phase is never a question, even attended: nothing "
            "makes a hard failure proceed (D6 row 14).",
        ]
        print("\n".join(lines), file=sys.stderr)
        # The stop is the result line's `error` too, which a detached close-out
        # writes as `run.error` and both tool routes relay as the run's last
        # line; it used to be on stderr alone (Fable review 2026-10-09). A
        # phase that recorded its own stop line keeps it: an apply's or
        # implement's names the remedy, where this one would say `exited 3`.
        # The detail gives way to the limit, never the sentence saying the
        # workflow stopped.
        ctx = active_result()
        if ctx is None or not ctx.error:
            room = ERROR_MAX_CHARS - len(head) - len(tail)
            record_error(f"{head}{clip(detail, room)}{tail}")
        self._record_progress(current=step.phase or step.label,
                              failed=step.phase or step.label)
        unattended_mod.mark_needs_human(self.MODE_NAME)
        # The machine-readable follow-up is the *next* command to run, and when the
        # phase printed a prerequisite of its own that is that one — resuming
        # before it re-materializes the same pending state and points back here, so
        # a host that follows `next` mechanically would loop. The prose above still
        # names both, in order.
        record_next(pending or resume)
        return EXIT_NEEDS_HUMAN

    def run(self) -> int:
        for step in self.steps():
            if step.skippable and not self.args.force:
                reason = self.skip_reason(step)
                if reason:
                    print(f"\n=== {step.label}: already {reason}, skipping ===")
                    self.reports.append(
                        StepReport(step.label, step.phase, ALREADY, reason)
                    )
                    continue
            print(f"\n=== {step.label} ===")
            self._record_progress(current=step.phase or step.label)
            self._clear_error()
            mark = self._open_step_result()
            try:
                outcome, detail, code = step.run()
            finally:
                self._close_step_result(step, mark)
            self.reports.append(
                StepReport(step.label, step.phase, outcome, detail, code)
            )
            if outcome == FAILED:
                self.print_report()
                return self._phase_failed(step, detail, code)
            if outcome == SKIPPED and detail:
                print(f"[SKIPPED] {step.label}: {detail}")
        self._record_progress(current="complete")
        self.print_report()
        record_next(None)
        return EXIT_OK

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------
    def print_report(self) -> None:
        print(f"\n## {self.REPORT_TITLE}\n")
        # "Commit brief", never "Plan", for a commit review's composite
        # (plans/review-commits.md §2.8), through the one owner of the word.
        print(f"**{self._document_title()}**: {self.plan_path}")
        print("")
        for report in self.reports:
            suffix = f" — {report.detail}" if report.detail else ""
            print(f"- {report.label}: {report.outcome}{suffix}")
        artifacts = self.report_artifacts()
        if artifacts:
            print("\n### Output files\n")
            for path in artifacts:
                print(f"- {path}")
                record_artifact(path)
        self._record_step_results()
        print("")
        self._print_metrics()

    def _record_step_results(self) -> None:
        """Each step's result and the result line's artifacts, in this run dir.

        A detached caller never reads the worker's line: its poll pins this
        run dir and restates what this records there, under this run's id
        (``detach.record_step_results``; live test 2026-10-26, D2: a detached
        ``improve-commits`` handed back its log alone). Every step ran in this
        process and recorded its artifacts on the line, so the whole list
        goes. A no-op in the foreground.
        """
        from utils import detach

        ctx = active_result()
        if ctx is None or detach.active_run() is None:
            return
        detach.record_step_results(
            str(self.run_dir), self.RUN_DIR_PHASE, self.step_results, ctx.artifacts)

    def _document_title(self) -> str:
        """``Plan``, or ``Commit brief`` when the plan's ``state.json``
        records a ``commit_range`` (``commit_review.document_label``)."""
        try:
            from utils.commit_review import document_label, read_commit_range

            return document_label(
                {"commit_range": read_commit_range(self.plan_path)}).capitalize()
        except Exception:  # noqa: BLE001 - advisory: the plan's word stands
            return "Plan"

    def report_artifacts(self) -> List[str]:
        """The per-phase artifacts a reader is most likely to open next.

        Only the ones that exist: the report lists them under *Output files* and
        records each on the result line.
        """
        candidates = [
            self.plan_dir / "review-plan" / "report.html",
            self.plan_dir / "review-plan" / "consolidated-report.md",
            self.plan_dir / "tasks" / "tasks.md",
            self.plan_dir / "review-tasks" / "report.html",
            self.plan_dir / "apply-task-suggestions" / "orchestrator_output.json",
            self.plan_dir / "code-review" / "report.html",
        ]
        return [str(path) for path in candidates if path.exists()]

    def _print_metrics(self) -> None:
        """Combined resource usage, when the run recorded any."""
        try:
            from utils import metrics

            state_file = self.plan_dir / "state.json"
            if not state_file.exists():
                return
            report = metrics.generate_all_phases_report(state_file)
        except Exception:  # noqa: BLE001 - a report must never fail a green run
            return
        if report:
            print(report)


# ---------------------------------------------------------------------------
# Row 4: whether the unattended consolidation pass runs
# ---------------------------------------------------------------------------

def consolidation_skip_reason(plan_dir: Union[str, Path]) -> Optional[str]:
    """Why the unattended consolidation pass does not run, or ``None`` to run it.

    A module function, not a method, so a planner that builds no workflow asks
    the same question with only the plan dir. The step that runs the pass is
    not skippable, so a resumed run re-enters it; without the first check it
    ran the pass again on groups it had already consolidated (live run 8's
    stale recommendation, the workflow's copy).
    """
    from utils.consolidation import consolidation_is_current

    if consolidation_is_current(str(Path(plan_dir) / "review-plan")):
        return "already ran on these review groups"
    if not _consolidation_recommended(plan_dir):
        return "not recommended by review-plan"
    return None


def _consolidation_recommended(plan_dir: Union[str, Path]) -> bool:
    """The same threshold ``review_plan_orchestrator`` prints its marker on."""
    from utils.consolidation import CONSOLIDATION_RECOMMENDED_THRESHOLD

    entries = _validation_entries(Path(plan_dir) / "review-plan" / "validation.json")
    actionable = sum(
        1 for entry in entries
        if entry.get("status") in ("valid", "needs-human-decision")
    )
    return actionable >= CONSOLIDATION_RECOMMENDED_THRESHOLD


# ---------------------------------------------------------------------------
# Small readers (shapes the existing counters already tolerate)
# ---------------------------------------------------------------------------

def _validation_entries(path: Path) -> List[Dict[str, Any]]:
    """``validation.json`` entries, v1 flat dict or v2 envelope."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return []
    if isinstance(data, dict) and "groups" in data:
        entries = data["groups"]
    elif isinstance(data, dict):
        entries = list(data.values())
    elif isinstance(data, list):
        entries = data
    else:
        return []
    return [entry for entry in entries if isinstance(entry, dict)]


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(argv: Optional[Sequence[str]] = None) -> int:
    bootstrap_streams()
    args = parse_args(argv)

    plan_path = Path(os.path.abspath(args.plan_file))
    if not plan_path.is_file():
        print(f"ERROR: Plan file not found: {args.plan_file}", file=sys.stderr)
        print(f"       Resolved path: {plan_path}", file=sys.stderr)
        return EXIT_ERROR

    workflow = FullWorkflow(args)

    # The detach boundary: after pre-flight (plan readable, flags parsed, run dir
    # created) and before the first phase runs, so a bad flag fails on the
    # caller's terminal with no child and no log.
    from utils.review_orchestrator_base import maybe_detach

    detached = maybe_detach(
        args=args,
        mode=workflow.MODE_NAME,
        phase_dir=str(workflow.run_dir),
        plan_file=str(plan_path),
        phase=workflow.RUN_DIR_PHASE,
    )
    if detached is not None:
        return detached

    return workflow.run()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
