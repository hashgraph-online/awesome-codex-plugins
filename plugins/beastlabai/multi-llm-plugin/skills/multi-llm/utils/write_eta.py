"""A write phase's ``[ETA]`` lines on the executor leg (F3, F4).

:class:`EtaLines` counts the tasks one run finishes against the tasks it will
dispatch, stamps the phase's baseline before the first dispatch
(:meth:`EtaLines.start`), records each dispatched task's metric and prints the
line it drives (:meth:`EtaLines.record`), and closes the lines once on every
ending: a stop, a refusal, an exception, a foreground Ctrl-C, a detached
worker's abort (:meth:`EtaLines.close`, :meth:`EtaLines.abort_line`) or the
finished phase's ``phase complete`` line (:meth:`EtaLines.finish`). The words
are ``utils/metrics.py``'s, shared with the native leg's ``util metrics``
(docs/development/write-scheduler.md#dispatch-counts).

``WriteBatchScheduler`` composes it with the run's ``RunContext``
(docs/development/write-scheduler.md#where-the-schedulers-helpers-live). Its
state is the counted sets below, written by the scheduler's dispatch walk
(``scope``, ``walk_left``) and its batch bookkeeping (``mark``, ``held``), always
under the scheduler's ``_effects_lock`` once batches run. Its ``state.json``
writes go through ``ctx.state``, the run's one ``StateManager``.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Tuple

from . import human_task_plan as _human_task_plan
from . import metrics as _metrics
from . import write_context as _write_context
from .retry_ladder import STATUS_OK
from .task_dispatch import STATUS_PARTIAL
from .batch_reply import WRITE_PARTIAL
from .task_outcome import TaskOutcome


class EtaLines:
    """One run's ``[ETA]`` counts and the lines they print.

    Built once per run by the scheduler. The two callables reach the
    scheduler's ``StopAccount.ran_out_of_time`` and ``_started_a_runner``, looked up at
    each call.
    """

    def __init__(
        self,
        ctx: _write_context.RunContext,
        *,
        ran_out_of_time: Callable[[TaskOutcome], bool],
        started_a_runner: Callable[..., bool],
    ) -> None:
        self._ctx = ctx
        self._ran_out_of_time = ran_out_of_time
        self._started_a_runner = started_a_runner
        #: Dispatched-or-skipped tasks finished so far, the `[ETA]` line's
        #: numerator. It counts TASKS because the denominator
        #: beside it does — `len(self.tasks) - human skips`, the same total
        #: `WriteReports.mirror_status` publishes — and because an `implement` batch is a
        #: dependency level with k tasks in it: `len(batches_dispatched) + 1`
        #: repeated the same ordinal for every member of such a batch, so a
        #: parallelizable plan could never reach `N/N` or print
        #: `ALL BATCHES COMPLETE`. Read and incremented under `_effects_lock`
        #: because a disjoint group finishes on several threads. A set of
        #: task ids: the numerator is the finished tasks
        #: the total counts (:meth:`progress`).
        self.finished: set = set()
        #: Implement only: the tasks this run will dispatch, from the walk
        #: the `Organized into …` line prints (`_dispatch_walk`, live run 8 #1: the
        #: first run's `[ETA]` total still
        #: counted T005, refused before dispatch, and T006 after it, so the
        #: lines read 1/7 … 4/6 under "5 task(s) to dispatch"). `None`: no
        #: walk (an apply phase), and the total counts every task.
        self.scope: Optional[set] = None
        #: Whether this run stamped an `[ETA]` baseline (:meth:`start`).
        self.started = False
        #: Whether this run printed an
        #: `[ETA]` line, and whether its one closing line is out
        #: (:meth:`close`, or `phase complete` from :meth:`finish`).
        self.printed = False
        self.closed = False
        #: The tasks a check this run recorded with findings holds back, out
        #: of the `[ETA]` total from that check's own line on,
        #: before `CheckHolds.block_dependents_of_checks` holds them for the loop. Each
        #: with its check, which the closing line names.
        self.held: Dict[str, str] = {}
        #: The tasks this run dispatched that
        #: failed, and the tasks the dispatch walk foresaw it would not run
        #: (`{task id: how}`, `metrics.left_out_tail`'s words) — a task the
        #: write policy refuses, the tasks after a stop, a task a check on
        #: record holds. Together with what the run met on the way, they say
        #: whether the last `[ETA]` line may read "complete", and what the
        #: closing line names (:meth:`left_out`).
        self.failed: set = set()
        self.unrun: set = set()
        self.walk_left: Dict[str, str] = {}
        #: The tasks the last `[ETA]` line
        #: counted, so the next line whose total dropped names what left it
        #: (:meth:`dropped`). `None` before the baseline.
        self.line_ids: Optional[set] = None
        #: The result the `[ETA]` lines count over, for an ending that has no
        #: other hold on it (an exception out of `_run`, an abort's signal).
        self.run_result: Optional[Any] = None

    def record(
        self, task: Dict[str, Any], outcome: TaskOutcome, result: Any
    ) -> None:
        """The metric for one batch, with the values the runner reported (D3g).

        Duration is the executor's own wall clock. Tokens and tool uses come from
        the adapter's normalized usage where the provider reports them and are
        simply **omitted** where it does not — ``record_metric`` treats all three as
        optional, and a fabricated zero would average into per-phase totals and read
        as a free run.

        Recorded **through the ``StateManager``**, not through ``metrics.py``'s own
        file-level read/modify/write: the caller's ``state.save()`` follows
        immediately and dumps this object's dict wholesale, so a second writer's
        entry was erased the moment it landed — three audited runs finished with
        no ``metrics`` key at all after every batch had recorded one (F4).

        The ``[ETA]`` line's own ``batch_index``/``total_batches`` are this run's
        own progress and dispatchable count — never ``task["batch_index"]``
        (the plan's global decomposition index, which starts wherever a resumed
        run's first undone task sits) and never bare ``len(self._ctx.tasks)`` (which
        still counts a deferred human task). Passing those two straight through
        made every line on a resumed run read `batch 7/6 done in 0m 51s ...
        WARNING: batch_index > total_batches` (N1, 2026-09-16).

        **Both halves count tasks**. ``len(result.batches_
        dispatched) + 1`` was the numerator, and it is a *batch* ordinal against
        a *task* denominator: for the three apply kinds one task is one batch and
        the two agree, but an ``implement`` dependency level with k independent
        tasks is one batch of k — every one of those k metric entries recorded
        the same ordinal, so a 14-task plan in 9 batches ended at
        ``batch 9/14 · ~Nm remaining``, never reached ``N/N`` and never printed
        ``ALL BATCHES COMPLETE``. Both come from :meth:`progress`: the
        finished tasks among the ones :meth:`total` counts.
        """
        if not hasattr(self._ctx.state, "record_metric"):
            return
        usage = outcome.usage or {}
        label = (
            f"{task.get('task_id')}: "
            f"{task.get('task_title') or self._ctx.kind} "
            f"[{outcome.write_outcome or outcome.status}]"
        ).strip()
        run_batch_index, total_batches = self.progress(result)
        # The line that reaches N/N said "ALL
        # BATCHES COMPLETE" before the run stopped on T005.
        ends_short = (
            run_batch_index >= total_batches and self.ends_short(result)
        )
        # A failed task's line says what
        # happened, the line whose total dropped says why, and a
        # complete run's N/N line names the tasks the plan set aside.
        failed = not outcome.ok
        failure, half_applied = self.failure(outcome) if failed else ("", False)
        dropped = self.dropped(result)
        set_aside = ""
        if self._ctx.kind == "implement" and not failed and run_batch_index >= total_batches:
            set_aside = _metrics.set_aside_tail(_human_task_plan.set_aside_by_plan(
                result.human_plan, self.manual_task_ids()))
        try:
            # The stored baseline follows the line it is printed beside (N1).
            self._ctx.state.set_metrics_total(self._ctx.phase, total_batches)
            eta_line = self._ctx.state.record_metric(
                self._ctx.phase,
                label,
                subagent_type=outcome.runner,
                token_count=(
                    int(usage["total_tokens"]) if isinstance(
                        usage.get("total_tokens"), (int, float)
                    ) else None
                ),
                tool_uses=(
                    int(usage["tool_uses"]) if isinstance(
                        usage.get("tool_uses"), (int, float)
                    ) else None
                ),
                duration_ms=int(outcome.duration_seconds * 1000),
                total_batches=total_batches or None,
                batch_index=run_batch_index,
                ends_short=ends_short,
                failed=failed,
                failure=failure,
                half_applied=half_applied,
                dropped=dropped,
                set_aside=set_aside,
            )
        except Exception as exc:  # noqa: BLE001 - metrics must not fail a phase
            self._ctx.log(f"[write-subagents] warning: metrics record failed: {exc}")
            return
        if eta_line:
            # The `[ETA]` line `instructions/implement.md` step 5 describes. It
            # goes through `self._ctx.log` rather than stderr so it lands in the
            # phase log `status` points at, beside the batch line above it.
            self.printed = True
            self._ctx.log(eta_line)

    def total(self, result: Any) -> int:
        """The ``[ETA]`` denominator: the tasks this run finishes or keeps.

        Every materialized task but the ones it never dispatches: a task the
        human-task plan skips or accepts, a manual task (no runner ever runs
        one), and a task a check with findings holds back
        (``result.blocked_by_check``, which grows as checks report). The accept path's
        resume counted the accepted check
        T002 and its last line read "batch 1/2 … ~0m 24s remaining" after the
        one task it dispatched; a check holding T007 left "6/7" the same way.
        On implement, only the tasks the run dispatches. The numerator never counts the others.
        """
        return len(self.task_ids(result))

    def task_ids(self, result: Any) -> List[str]:
        """The tasks :meth:`total` counts, in the task file's order.

        The run mirror counted its
        ``total`` over another set — a held task and a manual one in — so one
        run read "batch 6/6 … ALL BATCHES COMPLETE" in its log and
        "implement 6/7 batches ok" on ``status`` and the OpenCode poll.
        :meth:`WriteReports.mirror_status` counts over this one too.

        On implement, the set starts from what
        the run will dispatch (``scope``, the walk the ``Organized into
        …`` line counts), so a task the write policy refuses before dispatch,
        the tasks after it that the run never reaches, a task kept from an
        earlier run and one held by a check's findings on record are out from
        the first line; the stop fixture's first run read "batch 1/7" under
        "5 task(s) to dispatch" and stopped at "4/6". A task that finishes
        without a runner leaves it, one dispatched against the walk's
        reading joins it (:meth:`mark`), and a held task leaves it as
        before. On every phase, a task
        that ended without a runner and not ok (an apply batch refused before
        dispatch) is out, so "run stopped after batch 2/3" no longer counts
        the refused batch among the ones done; a resume's kept batch stays in.
        """
        out = (
            set(result.human_plan.skipped) | set(result.human_plan.accepted)
            | set(result.blocked_by_check) | set(self.held)
            | set(self.unrun)
        )
        scope = self.scope
        return [
            str(task.get("task_id", "")) for task in self._ctx.tasks
            if str(task.get("task_id", "")) not in out
            and (scope is None or str(task.get("task_id", "")) in scope)
            and not task.get("is_human") and task.get("executor_role") != "human"
        ]

    def mark(self, task_id: str, *, ran: bool, ok: bool = True) -> None:
        """One more finished task for the ``[ETA]`` numerator (F3).

        *ran*: a runner was started for it (its metric is recorded). On
        implement a task finished without one — kept from an
        earlier run, refused before dispatch, a check not run again — was
        not dispatched, so it leaves the counted set, as the native leg's
        ``util batch-done`` withdraws a refused task; a task dispatched that
        the walk did not foresee joins it, so the line never reads past its
        own total. Called under ``_effects_lock``.

        *ok*: how it ended; a dispatched task that failed stops the run
        short of its phase, so the line it drives at N/N
        claims no completion.
        """
        task_id = str(task_id)
        self.finished.add(task_id)
        self.failed.discard(task_id)
        self.unrun.discard(task_id)
        if not ok:
            # Ran and failed, or ended without a runner: refused before
            # dispatch, a failed check not run again on unchanged files.
            (self.failed if ran else self.unrun).add(task_id)
        if self.scope is not None:
            if ran:
                self.scope.add(task_id)
            else:
                self.scope.discard(task_id)

    def progress(self, result: Any) -> Tuple[int, int]:
        """``(finished, total)`` over the tasks :meth:`task_ids` counts:
        the two numbers every ``[ETA]`` line of this run prints."""
        counted = self.task_ids(result)
        return sum(1 for task_id in counted if task_id in self.finished), len(counted)

    def left_out(self, result: Any) -> Dict[str, str]:
        """``{task id: how}`` for every task this run leaves undone, in
        ``metrics.left_out_tail``'s words: the
        stop fixture's executor closed on a bare "run stopped after batch
        4/4" while T005 (refused), T006 (after it) and T007 (held by check
        T002) had not run. What the dispatch walk foresaw and the run has
        not met yet, a counted task not finished, a task the stop left
        (``result.not_run``), a task a check holds and a task that ended
        without a runner and not ok (refused, or a failed check not run
        again). A task that ran and failed is not in it: it ran. Reads,
        over copies: an abort's signal handler asks it mid-batch."""
        finished = set(self.finished)
        left: Dict[str, str] = {
            task_id: how for task_id, how in dict(self.walk_left).items()
            if task_id not in finished
        }
        for task_id in self.task_ids(result):
            if task_id not in finished:
                left.setdefault(task_id, _metrics.LEFT_NOT_RUN)
        for task_id in list(result.not_run):
            if task_id not in finished:
                left[str(task_id)] = _metrics.LEFT_NOT_RUN
        held = {**dict(self.held), **dict(result.blocked_by_check)}
        for task_id, check_id in held.items():
            left[str(task_id)] = _metrics.left_out_check(str(check_id))
        for task_id in set(self.unrun):
            left[task_id] = (
                _metrics.LEFT_REFUSED if task_id in result.refusals.before_dispatch
                else _metrics.LEFT_NOT_RUN
            )
        return left

    def ends_short(self, result: Any) -> bool:
        """Whether this run will end short of completing its phase: a task
        failed or was left (:meth:`left_out`). The ``[ETA]`` line that
        reaches N/N then claims no completion."""
        return bool(self.failed or self.unrun or self.left_out(result))

    def failure(self, outcome: TaskOutcome) -> Tuple[str, bool]:
        """What a failed dispatch's ``[ETA]`` line says happened, and whether
        its edits are half-applied. The
        status its batch line shows (``timeout``, ``batch failed``); for a
        partial application, what stopped it."""
        half = outcome.write_outcome == WRITE_PARTIAL or outcome.status == STATUS_PARTIAL
        if outcome.applied_without_changes:
            return "its change did not land", half
        status = str(outcome.status or "")
        if half:
            status = "timeout" if self._ran_out_of_time(outcome) else next(
                (
                    str(attempt.status) for attempt in reversed(outcome.attempts)
                    if attempt.status not in (STATUS_OK, STATUS_PARTIAL)
                ),
                "",
            )
        return status.replace("_", " "), half

    def dropped(self, result: Any) -> str:
        """Why this line's total is lower than the last line's, in
        ``metrics.left_out_tail``'s words, or ``""``. Moves
        the baseline to this line's tasks."""
        counted = set(self.task_ids(result))
        before, self.line_ids = self.line_ids, counted
        gone = (before or set()) - counted
        if not gone:
            return ""
        left = self.left_out(result)
        how = {
            task_id: (
                _metrics.LEFT_KEPT
                if task_id in self.finished and task_id not in self.unrun
                and task_id not in left
                else left.get(task_id, _metrics.LEFT_NOT_RUN)
            )
            for task_id in gone
        }
        return _metrics.left_out_tail(how, unit=_metrics.eta_unit(self._ctx.phase))

    def manual_task_ids(self) -> List[str]:
        """This run's manual tasks: no runner ever runs one."""
        return [
            str(task.get("task_id", "")) for task in self._ctx.tasks
            if task.get("is_human") or task.get("executor_role") == "human"
        ]

    def closing_line(
        self, result: Optional[Any], *, verb: str = "stopped",
        why: str = "",
    ) -> Optional[str]:
        """The closing ``[ETA]`` line of a run that ends short of completing
        its phase (``metrics.closing_line``: the native leg's ``util metrics
        finish`` words it the same), or ``None`` when there is nothing to
        close (no baseline). It names what the run left
        (:meth:`left_out`), and a run that dispatched nothing closes
        too ("run stopped with nothing dispatched · …"; 01b and 01c of live
        run 9 logged no line). Pure: it logs and saves nothing, so an
        abort's signal handler can ask for it."""
        if not self.started or result is None:
            return None
        done, total = self.progress(result)
        return _metrics.closing_line(
            self._ctx.phase, done=done, total=total, verb=verb,
            tail=_metrics.left_out_tail(
                self.left_out(result), unit=_metrics.eta_unit(self._ctx.phase),
            ), why=why,
        )

    def close(
        self, result: Optional[Any], *, verb: str = "stopped",
        why: str = "",
    ) -> None:
        """Close this run's ``[ETA]`` lines on an ending short of completion.

        A stop that came before any "N/N" left
        "batch 4/6 done in 0m 15s · ~0m 37s remaining" standing, so a stop
        short of its total logged one closing line. Every ending of a write phase closes
        them, once — a
        stop, a refusal, the tasks a check holds back, a failed
        ``driver.verify_command``, an exception out of the loop, a
        foreground Ctrl-C (``verb="interrupted"``), a detached worker's
        abort (:meth:`abort_line`) — and a finished phase with its
        ``phase complete`` line (:meth:`finish`). A check that
        reported findings and held the last two tasks used to end the run
        on "batch 3/5 … ~<1s remaining" with no closing line, and
        ``metrics_progress.implement.total_batches`` still at 5: the stored
        total is re-stamped here to the one the line and the write mirror
        count. Best-effort.
        """
        if self.closed:
            return
        self.closed = True
        _metrics.close_eta_run(self.abort_line)
        try:
            line = self.closing_line(result, verb=verb, why=why)
            if result is not None and self.started:
                self.restamp(self.progress(result)[1])
        except Exception:  # noqa: BLE001 - a count line must not fail a phase
            return
        if line:
            self._ctx.log(line)

    def restamp(self, total: int) -> None:
        """Keep ``metrics_progress.{phase}.total_batches`` at the total the
        ``[ETA]`` lines and the write mirror count (N1;: an
        ending with no later metric re-stamps it here)."""
        live = getattr(self._ctx.state, "state", None)
        progress = (
            (live.get("metrics_progress") or {}).get(self._ctx.phase)
            if isinstance(live, dict) else None
        )
        if not isinstance(progress, dict) or progress.get("total_batches") == total:
            return
        self._ctx.state.set_metrics_total(self._ctx.phase, total)
        try:
            self._ctx.state.save()
        except Exception:  # noqa: BLE001 - bookkeeping must not fail a phase
            pass

    def abort_line(self, cause: str) -> Optional[str]:
        """The closing line a detached worker's abort prints for this run
        (``metrics.aborted_eta_line``): the signal handler ends
        the process with ``os._exit``, so no ``finally`` of this run closes
        its lines. Reads, takes no lock, logs nothing."""
        return self.closing_line(self.run_result, verb=f"aborted ({cause})")

    def start(self, result: Any) -> None:
        """Stamp the phase's ETA baseline before the first dispatch.

        Only the `util metrics start` CLI leg ever called `start_phase`, so on
        the executor path `metrics_progress` never existed and neither did the
        `[ETA]` line `instructions/implement.md` step 5 describes (F4).

        The baseline is the number of **tasks** this run will actually dispatch
        (or, on an apply phase, resume-skip) — :meth:`total`, the same
        total ``record``
        uses (and keeps the stored baseline at) — never the
        bare materialized count, which still counts a deferred human task that is
        never dispatched (N1, 2026-09-16: with the bare count, the stored
        ``metrics_progress.total_batches`` disagreed with every ``[ETA]`` line
        the run went on to print). Tasks, not batches, because that is the unit
        the numerator counts as well: see :meth:`record` (F3).
        """
        if not hasattr(self._ctx.state, "start_metrics_phase"):
            return
        total_batches = self.total(result)
        try:
            self._ctx.state.start_metrics_phase(self._ctx.phase, total_batches)
            # A native emit's left-out tasks are that leg's: this run closes its own
            # lines. Its set-aside tasks
            # too: this run names its own.
            self._ctx.state.set_metrics_left_out(self._ctx.phase, {})
            self._ctx.state.set_metrics_set_aside(self._ctx.phase, {})
            self.started = True
            self._ctx.state.save()
        except Exception:  # noqa: BLE001 - bookkeeping must not fail a phase
            pass
        if self.started:
            # What an ending with no other hold on the run
            # counts over, and the line a detached worker's abort prints.
            self.run_result = result
            _metrics.open_eta_run(self.abort_line)
            # The total the first line is held to.
            self.line_ids = set(self.task_ids(result))

    def finish(self, result: Optional[Any] = None) -> None:
        """Pop the phase's ETA baseline and log its closing line (F7).

        The line goes through ``self._ctx.log`` for the same reason every per-batch
        ``[ETA]`` line does — so it lands in the phase log ``status`` points at,
        beside the lines it closes. ``finish_metrics_phase`` used to print it to
        stderr itself, which on a foreground or in-process ``full`` run put the
        closing line somewhere none of the others went.

        An implement run that started
        no runner has no N/N line to name the tasks its plan set aside, so
        its ``phase complete`` line names them (a manual task declined with
        ``--human-task <id>=skip`` and the tasks skipped with it, say).
        """
        if not hasattr(self._ctx.state, "finish_metrics_phase"):
            return
        # The finished phase's closing line (one per ending).
        self.closed = True
        _metrics.close_eta_run(self.abort_line)
        try:
            finished = self._ctx.state.finish_metrics_phase(self._ctx.phase)
        except Exception:  # noqa: BLE001 - bookkeeping must not fail a phase
            return
        # `(elapsed_ms, line)` when the phase had a baseline, `None` when it
        # never started.
        if isinstance(finished, tuple) and finished[1]:
            line = finished[1]
            if (result is not None and self._ctx.kind == "implement"
                    and not any(self._started_a_runner(o, result.refusals)
                                for o in result.outcomes)):
                try:
                    tail = _metrics.set_aside_tail(_human_task_plan.set_aside_by_plan(
                        result.human_plan, self.manual_task_ids()))
                except Exception:  # noqa: BLE001 - a count line must not fail a phase
                    tail = ""
                if tail:
                    line = f"{line} · {tail}"
            self._ctx.log(line)
