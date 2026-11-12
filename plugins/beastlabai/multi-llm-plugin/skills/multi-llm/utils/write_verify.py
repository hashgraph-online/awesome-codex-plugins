"""A write phase's own check of the repository, and its tracked-files census (D3n).

:class:`VerifyStep` is the part of a code phase's ending that asks the
repository rather than the batches: whether a task of the phase applied an edit
still owed a check (:meth:`VerifyStep.phase_has_applied_batches`), running
``driver.verify_command`` once after the last batch (:meth:`VerifyStep.run`)
and saying so when nothing ran the tests (:meth:`VerifyStep.note_unverified_on_stop`),
and recording what the phase changed in ``tracked_files`` after each batch and
at the end (:meth:`VerifyStep.record_batch_tracking`,
:meth:`VerifyStep.finalize_tracking`). It holds no state of its own.
:class:`VerifyCommand` runs the command: in a process group (a Job Object on
Windows) of its own, its output bounded, and a timeout that ends the whole
tree and words what the kill confirmed (:meth:`VerifyCommand.run`,
:meth:`VerifyCommand.kill_tree`).

``WriteBatchScheduler`` composes both with the run's ``RunContext`` and hands
``VerifyStep`` the few things it calls back: the command runner
(``VerifyCommand.run``), the tests line worded from the batches' checks, the
stop's headline and the task lookup
(docs/development/write-scheduler.md#where-the-schedulers-helpers-live).
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from . import batch_prompt as _batch_prompt
from . import check_records as _check_records
from . import process_control as _process_control
from . import write_context as _write_context
from .batch_ledger import touched_files
from .cli_common import EXIT_NEEDS_HUMAN
from .provider_registry import get_verify_command, get_verify_settings
from .batch_reply import WRITE_APPLIED, WRITE_PARTIAL
from .dispatch_spawn import _host_env_guards
from .subagent_tasks import PHASE_BY_WRITE_KIND
from .redact import redact_text
from .providers.child_env import build_child_env

#: How much of the verification command's output travels in the result payload,
#: the summary and `.status.json`. A tail rather than the whole capture: a failing
#: build prints megabytes and what names the failure is the end of it.
VERIFY_TAIL_CHARS = 2000


def load_finalize_tracking():
    """The tracked-files census (``utils.tracking``, the body of
    ``finalize_tracking.py``), or ``None`` if unimportable.

    ``None`` keeps a batch record from failing on a census it cannot run.
    """
    try:
        # `tracking` reaches this module through the write scheduler: a load-time cycle.
        from . import tracking
    except ImportError:  # pragma: no cover - a module of this package
        return None
    return tracking


class VerifyStep:
    """The repository check and the tracked-files census, over one run's result.

    Built once per run by the scheduler. *effects_lock* is the scheduler's
    ``_effects_lock``, which every in-memory ``state.json`` write of the run
    takes; *finalize* is the scheduler's ``finalize``. The four callables
    reach the scheduler's ``_task_by_id``, ``_unverified_text``,
    ``StopAccount.set_stop_headline`` and ``VerifyCommand.run``, looked up at
    each call.
    """

    def __init__(
        self,
        ctx: _write_context.RunContext,
        *,
        effects_lock: threading.Lock,
        finalize: bool,
        task_by_id: Callable[[str], Optional[Dict[str, Any]]],
        unverified_text: Callable[..., str],
        set_stop_headline: Callable[..., Any],
        run_verify_command: Callable[[str, int], Any],
    ) -> None:
        self._ctx = ctx
        self._effects_lock = effects_lock
        self._finalize = finalize
        self._task_by_id = task_by_id
        self._unverified_text = unverified_text
        self._set_stop_headline = set_stop_headline
        self._run_verify_command = run_verify_command

    def note_unverified_on_stop(self, result: Any) -> List[str]:
        """The "nothing ran this repository's tests" line on a stop (fix
        round 16); the lines to print, ``[]`` when none is owed.

        Run 6 (Codex and OpenCode stop 01): a code phase that stopped after
        code batches ran said nothing about the repository's tests — the line
        :meth:`run` adds reached only a finished run's result,
        notice and summary. Set on ``result.unverified`` (the notice, the
        Verification line, the report, the mirror) when this is a code phase,
        a task of it applied an edit (this run or an earlier one,
        :meth:`phase_has_applied_batches` — the rule
        :meth:`run` keeps too) and no ``driver.verify_command``
        is set. Never runs anything. Fix round 17: it counted any completed
        task, so a stop after a check alone (which edits nothing, and may have
        run the tests itself) said that nothing had run them.

        Fix round 18 (live run 7, Codex and OpenCode stop 01): the line was
        in the result's ``notice``, and neither host relayed ``notice`` at a
        stop — both relay the stop's headline, the result line's ``error``
        (the one line the needs-human ``message`` quotes). So the line also
        ends the headline of a stop already recorded (the scheduler's ``StopAccount.record_stop``
        and ``StopAccount.record_check_block`` run first): the tool routes carry it where
        they carry the stop — the result line's ``error`` in the tool output
        — and ``run.error`` and ``status`` with it. Not the OpenCode stop
        title (fix round 19, review of round 18, #5): that cuts the error
        line at ``modes.STOP_TITLE["max_line"]`` (300) characters, and a
        real stop headline runs past that before this line (live run 7:
        644), so the title shows what stopped and the resume command. The
        line stays in the ``notice`` too, the field a finished run carries
        it in, so a tool result shows it in both.
        """
        if self._ctx.kind not in _batch_prompt.CODE_WRITE_KINDS or self._ctx.dry_run or result.unverified:
            return []
        if not self.phase_has_applied_batches(result):
            return []
        try:
            command = get_verify_command(anchor=self._ctx.anchor)
        except Exception:  # noqa: BLE001 - advisory on a stop
            return []
        if command:
            return []
        result.unverified = self._unverified_text(stop=True)
        headline = (result.stop or {}).get("headline")
        if headline and result.unverified not in headline:
            # The result line's `error` is bounded: the headline is fitted
            # again with this line as its whole end (fix round 19: the
            # model's quoted words give way first, never the remedy).
            self._set_stop_headline(result.stop, tail=result.unverified)
        return [result.unverified]

    def run(self, result: Any) -> bool:
        """Run ``driver.verify_command`` once, after the last batch (F4).

        Returns whether the phase may complete. Three ways that is ``True``
        without a command ever running, and only the first is announced:

        * **No command configured.** Logged, because "this repo declares no
          check" and "the check passed" are different facts and a silent skip
          spells them the same way. `instructions/apply-code-fixes.md` used to
          hard-code `pnpm typecheck && pnpm lint:fix`, which is right for one
          repo shape and wrong for the rest — the audited run's target had no
          `package.json` at all.
        * **A markdown phase.** `apply_suggestions`/`apply_task_suggestions`
          edit the plan and the tasks file; a typecheck has nothing to say about
          them, so they skip silently rather than nagging about a command that
          was never going to apply.
        * **Nothing applied.** No task of this run **and** none recorded by an
          earlier run of this phase applied an edit
          (:meth:`phase_has_applied_batches`) means no edit to check. Fix
          round 17: a dispatched batch used to be enough, so a run whose only
          batches were checks or no-ops ran the command (or said nothing had
          run the tests) about edits nobody made; the stop's line
          (:meth:`note_unverified_on_stop`) asks the same question.

        The command is a **shell string** (`&&` is in its documented shape), run
        with `cwd` at the pinned repo root — the same root every containment
        check resolves against — and bounded by `driver.verify_timeout_s`, which
        is a bound on the whole process group and not just on `/bin/sh`
        (:meth:`VerifyCommand.run`). It is logged before it starts and again
        with its exit code once it ends.
        """
        if self._ctx.kind not in _batch_prompt.CODE_WRITE_KINDS:
            return True
        if not self.phase_has_applied_batches(result):
            return True
        # One load for the command, its timeout and the layer named in the log
        # (docs/development/providers.md#configuration-and-runner-resolution).
        command, timeout, source = get_verify_settings(anchor=self._ctx.anchor)
        if not command:
            self._ctx.log(
                "[write-subagents] no driver.verify_command configured — "
                f"{len(result.batches_dispatched)} batch(es) were verified "
                "against their own snapshots, but nothing checked the "
                "repository as a whole."
            )
            # Fix round 14: said on the result too, not only in the log —
            # codex racing run 5's apply-code-fixes left the repository's own
            # test failing and every surface a host relays read clean.
            # Fix round 20: and which checks the batches were asked to run,
            # with what each batch reported (apply-code-fixes); fix round 24:
            # led by what ran, implement's tasks' checks too.
            result.unverified = self._unverified_text()
            result.messages.append(result.unverified)
            return True
        # Announced BEFORE it runs, which is what `docs/configuration.md`'s
        # safety section already promises of the one config key whose value is
        # executed: the only line used to be written once the command returned,
        # so a 600 s check left a detached run's log silent about what it was
        # waiting on — and naming it is the whole mitigation for an untrusted
        # repo's override (F6/F3a, 2026-09-16). The closing line below still
        # reports the exit code and the duration.
        self._ctx.log(
            f"[write-subagents] verification ({source}): running "
            f"`{redact_text(command)}` (timeout {timeout}s)"
        )
        started = time.monotonic()
        exit_code, output = self._run_verify_command(command, timeout)
        duration = time.monotonic() - started
        # Redact BEFORE the tail cap, the same order the audit log uses: a build
        # that echoes a token into its log would otherwise put it in
        # `.status.json`, `write_batch_report.json` and `summary.md` at once.
        result.verification = {
            "command": redact_text(command),
            "source": source,
            "exit_code": exit_code,
            "duration_seconds": round(duration, 1),
            "output_tail": redact_text(output).strip()[-VERIFY_TAIL_CHARS:],
        }
        self._ctx.log(
            f"[write-subagents] verification ({source}): "
            f"`{result.verification['command']}` exited {exit_code} "
            f"in {duration:.1f}s"
        )
        if exit_code == 0:
            return True
        result.exit_code = EXIT_NEEDS_HUMAN
        result.messages.extend(self.verification_message(result))
        return False

    def phase_has_applied_batches(
        self, result: Optional[Any] = None,
    ) -> bool:
        """Whether a task of this phase applied an edit that is still owed a
        check: one of *result*'s outcomes, or one an earlier run left (F3).

        The check used to gate on ``result.batches_dispatched`` alone. The
        apply kinds re-materialize their full batch list on ``--resume`` and a
        resume skip counts as dispatched, so their check re-ran; ``implement``
        materializes only the tasks still owed, so after a run in which every
        task applied and only the check failed, the resumed list was EMPTY,
        nothing dispatched, the check never re-ran and ``_finalize`` stamped
        the phase completed against a repository still failing its own check
        — the exact ``--resume`` the exit-3 message had told the user to run
        (2026-09-16). ``state.json``'s task statuses are the record that
        survives that filter, so they answer here.

        Fix round 17: only an edit counts. This run's ``ok`` outcomes count
        when they ``applied`` (a resume skip carries the earlier verdict); a
        task ``state.json`` records ``completed`` counts when the phase's
        audit log's last completion of it applied or partly applied an edit
        (a failed batch the user accepted keeps what it moved). A check task
        (``no-op``, ``verification_only``), a ``no-op`` batch and a manual
        task answered ``done`` (no dispatch at all) edit nothing. A completed
        task with no completion in the audit log (the native leg records
        none) still counts unless it is a manual or a check task this run
        knows of: the conservative reading, which runs the check.
        """
        if result is not None and any(
            outcome.ok and outcome.write_outcome == WRITE_APPLIED
            for outcome in result.outcomes
        ):
            return True
        if not hasattr(self._ctx.state, "get_all_task_statuses"):
            return False
        try:
            statuses = self._ctx.state.get_all_task_statuses()
        except Exception:  # noqa: BLE001 - advisory, never fatal
            return False
        candidates = {str(task.get("task_id") or "") for task in self._ctx.tasks}
        if self._ctx.kind in _write_context._ID_KEYED_WRITE_KINDS:
            # The plan's own task ids, materialized this run or not — the flat
            # map also holds the apply kinds' batch ids, which are not this
            # phase's.
            candidates |= {
                task_id for task_id in statuses if _check_records._IMPLEMENT_TASK_ID.match(task_id)
            }
        candidates.discard("")
        completed = sorted(
            task_id for task_id in candidates if statuses.get(task_id) == "completed"
        )
        if not completed:
            return False
        record = getattr(self._ctx.state, "state", None)
        human = {
            str(task_id) for task_id in (
                (record.get("implement_human_task_ids") if isinstance(record, dict)
                 else None) or []
            )
        }
        for task_id in completed:
            task = self._task_by_id(task_id)
            expected = [str(i) for i in ((task or {}).get("expected_ids") or [])]
            try:
                done = self._ctx.audit.completion_for(
                    task_id, expected_ids=expected or None,
                )
            except Exception:  # noqa: BLE001 - an unreadable log is no record
                done = None
            if done is not None:
                if done.get("write_outcome") in (WRITE_APPLIED, WRITE_PARTIAL):
                    return True
                continue
            if task_id in human:
                continue
            if task is not None and (
                _batch_prompt.is_check_task(self._ctx.kind, task)
                or task.get("executor_role") == "human" or task.get("is_human")
            ):
                continue
            return True
        return False

    def verification_message(self, result: Any) -> List[str]:
        """The exit-3 block for a failed `driver.verify_command` (F4).

        Worded like the scheduler's ``StopAccount.stop_message``: what happened, what was NOT undone,
        and the one command that moves it forward. Deliberately *not* a rollback
        — every batch was verified against its own snapshot and the half-applied
        state a revert would destroy is exactly what a human needs to read.
        """
        record = result.verification or {}
        lines = [
            "",
            f"ERROR: every batch applied and verified, but the repository's own "
            f"check failed, so the {self._ctx.phase} phase is NOT marked completed.",
            f"  - driver.verify_command ({record.get('source', 'unknown')}): "
            f"`{record.get('command', '')}` exited {record.get('exit_code')} "
            f"after {record.get('duration_seconds')}s",
        ]
        tail = str(record.get("output_tail") or "").strip()
        if tail:
            lines.append("Last output:")
            lines += [f"  {line}" for line in tail.splitlines()[-20:]]
        applied = (
            f"batches {', '.join(str(i) for i in result.batches_dispatched)} "
            f"are applied"
            if result.batches_dispatched
            else "every batch an earlier run of this phase applied is still applied"
        )
        lines += [
            f"Nothing was rolled back: {applied} and the pre-batch snapshots "
            f"are intact under {os.path.join(self._ctx.safety_dir, 'pre_batch')}/.",
            "Fix the repository (or the fix the batches applied), then re-invoke "
            "with --resume: every batch is already done, so nothing is "
            "re-dispatched and only the check runs again.",
        ]
        return lines

    def finalize_tracking(self, result: Optional[Any] = None) -> None:
        """``finalize_tracking.py --state-file`` in process (D3n).

        Every file a batch verifiably changed travels as ``--touched``.
        ``finalize_tracking`` otherwise subtracts ``pre_existing_changes`` from
        the working tree's current diff, which is right for a file the run
        never touched and wrong for one it did: a file already modified when the
        phase started (measured 2026-09-16, ``index.html`` under ``AM``) is
        subtracted along with the rest, ``tracked_files`` ends up naming only
        the noise, and ``review-code`` reviews the noise.
        """
        state_file = getattr(self._ctx.state, "state_file", None)
        if not state_file:
            return  # no state.json to census (a run without a state)
        touched = self.touched_files(result)
        finalize_tracking = load_finalize_tracking()
        if finalize_tracking is None:
            return
        argv = ["--state-file", str(state_file)]
        for path in touched:
            argv += ["--touched", path]
        argv += ["--phase", PHASE_BY_WRITE_KIND[self._ctx.kind]]
        try:
            code = finalize_tracking.main(argv)
        except SystemExit:  # pragma: no cover - argparse-style exit
            return
        except Exception as exc:  # noqa: BLE001
            self._ctx.log(f"[write-subagents] warning: finalize_tracking failed: {exc}")
            return
        # F4 (2026-09-17): `main` *returns* 1 for an unreadable or unparseable
        # state file and for a failed write — it does not raise — and the return
        # value used to be dropped. `_reload_state` then silently kept whatever
        # it could read, the phase finalized, and `tracked_files` stayed whatever
        # an earlier phase had left for `review-code` to review. A census that
        # did not happen has to be visible in both places a reader looks.
        if code:
            message = (
                f"WARNING: finalize_tracking exited {code}; tracked_files was "
                f"NOT updated — `review-code` will read whatever the previous "
                f"phase left. Re-run: util finalize-tracking --state-file "
                f"{state_file}"
            )
            self._ctx.log(f"[write-subagents] {message}")
            if result is not None:
                result.messages.append(message)

    def touched_files(self, result: Optional[Any]) -> List[str]:
        """Every file an ``ok`` batch of this phase verifiably changed.

        This run's outcomes, and on a ``--resume`` the earlier runs' ``ok``
        rows too: a resumed implement materializes only the unfinished tasks,
        so without those rows a file an earlier run edited while it was
        already dirty (the baseline subtracts it) left ``tracked_files`` the
        moment the resumed run recorded its own.
        """
        if result is None:
            return []
        return touched_files(
            [*result.earlier_rows, *result.outcomes], include_partial=False)

    def record_batch_tracking(self, result: Any) -> None:
        """Record what this code phase has changed so far, after each batch.

        ``tracked_files`` used to be written only by ``_finalize``, which a
        run that stops part-way never reaches: the Codex racing run 3
        (2026-10-05) stopped implement at its ninth task with ``index.html``
        created and unrecorded, and review-code reviewed the plan and
        ``tasks.md`` an earlier phase had left there instead. The same census
        ``_finalize`` runs, in memory through this phase's own
        ``StateManager`` (the one writer), quietly, and saved only when the
        list moved.
        """
        if (self._ctx.dry_run or not self._finalize
                or self._ctx.kind not in _batch_prompt.CODE_WRITE_KINDS):
            return
        recorded = getattr(self._ctx.state, "state", None)
        state_file = getattr(self._ctx.state, "state_file", None)
        if not isinstance(recorded, dict) or not state_file:
            return
        finalize_tracking = load_finalize_tracking()
        if finalize_tracking is None:
            return
        try:
            entries = finalize_tracking.phase_tracked_files(
                recorded, self.touched_files(result),
                state_path=Path(str(state_file)),
                phase=PHASE_BY_WRITE_KIND[self._ctx.kind],
                say=lambda line: None,
            )
        except Exception as exc:  # noqa: BLE001 - bookkeeping must not fail a phase
            self._ctx.log(
                f"[write-subagents] warning: could not record the files this "
                f"batch changed in tracked_files: {exc}"
            )
            return
        if entries == recorded.get("tracked_files"):
            return
        with self._effects_lock:
            self._ctx.state.set("tracked_files", entries)
            self._ctx.state.save()
        named = ", ".join(
            f"{entry['path']} ({entry['action']})" for entry in entries[:5]
        )
        more = f", and {len(entries) - 5} more" if len(entries) > 5 else ""
        self._ctx.log(
            f"[write-subagents] tracked_files now names {len(entries)} "
            f"file(s): {named}{more}"
        )


# ---------------------------------------------------------------------------
# The command runner
# ---------------------------------------------------------------------------

#: How much of the command's output is read back off disk before redaction and
#: the tail cap (:data:`VERIFY_TAIL_CHARS`). `capture_output=True` buffered a whole build in this
#: process to hand 2000 characters of it to a report (F6); a bounded read off the
#: end of the capture file is the same tail at a fixed cost.
VERIFY_OUTPUT_CAP_BYTES = 64 * 1024

#: SIGTERM→SIGKILL grace for a timed-out command's process group, then how long
#: the reaping wait holds. The same shape `subagent_executor` uses on a runner.
VERIFY_KILL_GRACE_S = 0.5
VERIFY_REAP_S = 5.0

#: Recorded when the command produced no exit status of its own, in the shell's
#: own vocabulary so a reader of `verification.exit_code` learns nothing private.
VERIFY_EXIT_TIMEOUT = 124
VERIFY_EXIT_NOT_RUN = 127


def _verify_timeout_note(
    timeout: int, verdict: Optional[str], pid: int, pgid: Optional[int],
    outside: Sequence[_process_control.Descendant] = (),
) -> str:
    """The line a timed-out verify command's output ends with, from its kill's
    *verdict* (``kill_tree``). Only ``killed`` and
    ``gone`` confirm the command stopped (``process_control.unconfirmed_kill``);
    every other verdict, ``None`` for a kill that raised included, names the
    pid and says the command may still be running, never that it was killed.
    *outside* are the command's processes outside its process group still
    running after the kill (:meth:`VerifyCommand.left_the_group`): the group
    kill never reaches them, so the line names them as still running whatever
    the verdict (docs/development/write-scheduler.md, "When the verify command
    times out")."""
    reason = _process_control.unconfirmed_kill(verdict)
    who = f"pid {pid}" + (f", process group {pgid}" if pgid is not None else "")
    if reason is None and verdict == "gone":
        body = (f"timed out after {timeout}s: the command had already stopped, "
                f"and nothing of its process group still runs")
    elif reason is None:
        body = (f"killed after {timeout}s: SIGTERM then SIGKILL to the command's "
                f"whole process group")
    elif verdict == "skipped":
        # The kill could not trust the command's pid to name it any more.
        body = (f"timed out after {timeout}s: termination attempted, but no signal "
                f"was sent, so the command ({who}) may still be running")
    elif verdict == "unresolved":
        # What ran in its group that could not be identified as the command's
        # got nothing.
        body = (f"timed out after {timeout}s: not every process of the command "
                f"({who}) could be confirmed stopped; what could not be identified as "
                f"the command's was not signalled and may still be running")
    else:
        body = (f"timed out after {timeout}s: termination attempted, but the command "
                f"({who}) could not be confirmed stopped: {reason}, so it may still be "
                f"running")
    if outside:
        count = len(outside)
        body += (f" — verdict {verdict}; {count} process{'' if count == 1 else 'es'} "
                 f"the command started outside its process group "
                 f"{'is' if count == 1 else 'are'} out of the group kill's reach and "
                 f"still {'runs' if count == 1 else 'run'}: "
                 f"{VerifyCommand.named(outside)}")
    else:
        body += f" — verdict {verdict}"
    return f"\n({body})"


class VerifyCommand:
    """``driver.verify_command``'s runner (F3/F4, F6): the shell string in a
    process group of its own (a Job Object on Windows), its output bounded,
    and a timeout that ends the whole tree and says what the kill confirmed
    (docs/development/write-scheduler.md, "When the verify command times out").

    Built once per run by the scheduler over the run's ``RunContext``: it runs
    in ``ctx.repo_root``, composes its environment for ``ctx.anchor`` and warns
    through ``ctx.log``. :meth:`VerifyStep.run` calls :meth:`run`.
    """

    def __init__(self, ctx: _write_context.RunContext) -> None:
        self._ctx = ctx

    def run(self, command: str, timeout: int) -> Tuple[int, str]:
        """Run the shell string; return ``(exit_code, output)`` (F3/F4, F6).

        Three things the old one-line ``subprocess.run(shell=True, timeout=…)``
        could not do, each measured 2026-09-16:

        * **Stop the check.** ``run``'s timeout SIGKILLs ``/bin/sh`` and nothing
          else, and the documented ``pnpm typecheck && pnpm lint:fix`` shape is
          exactly the one where the shell cannot exec into the command — so the
          phase reported ``exited 124`` while ``node`` kept the CPU, reparented
          to init. The child is its own process-group leader here
          (``process_control.new_process_group_kwargs``) and a timeout takes the
          whole group down through ``kill_tree``, the same facade and the same
          escalation the runner spawn uses. On Windows, which has no groups,
          the command starts in a Job Object of its own
          (``process_control.popen_tree``) and the timeout ends that job.
        * **Bound the wait.** A grandchild that inherited the capture pipes keeps
          ``communicate()`` blocked past the deadline, so ``verify_timeout_s``
          was not a bound at all. Both streams go to one temp file instead:
          ``wait`` bounds on the direct child, and no descriptor this process
          reads is held by anything that outlived the kill.
        * **Bound the memory.** Only the last :data:`VERIFY_OUTPUT_CAP_BYTES` are
          read back — a failing build prints megabytes and what names the failure
          is the end of it, which is why the record keeps a tail in the first
          place.
        """
        env = self.env()
        try:
            sink = tempfile.TemporaryFile(prefix="multi_llm_verify_")
        except OSError as exc:  # pragma: no cover - no writable temp dir
            return VERIFY_EXIT_NOT_RUN, (
                f"verification output could not be captured: {exc}"
            )
        with sink:
            try:
                proc, job = _process_control.popen_tree(  # noqa: S602 - a shell string is the contract
                    command, shell=True, cwd=self._ctx.repo_root,
                    stdin=subprocess.DEVNULL, stdout=sink,
                    stderr=subprocess.STDOUT, env=env,
                    **_process_control.new_process_group_kwargs(),
                )
            except OSError as exc:  # pragma: no cover - the shell itself is missing
                return VERIFY_EXIT_NOT_RUN, (
                    f"verification command could not be started: {exc}"
                )
            try:
                # Read the group while the leader is alive: `os.getpgid` stops
                # answering once it is reaped, and the group is what still
                # holds the build's children.
                pgid = _process_control.process_group_id(proc.pid)
                note = ""
                try:
                    exit_code = int(proc.wait(timeout=timeout))
                except subprocess.TimeoutExpired:
                    outside = self.left_the_group(proc.pid, pgid)
                    verdict = self.kill_tree(proc, pgid, job)
                    exit_code = VERIFY_EXIT_TIMEOUT
                    left = self.left_outside(proc.pid, outside)
                    note = _verify_timeout_note(timeout, verdict, proc.pid, pgid, left)
            finally:
                if job is not None:
                    job.close()
            return exit_code, self.output_tail(sink) + note

    def kill_tree(
        self, proc: Any, pgid: Optional[int], job: Any = None,
    ) -> Optional[str]:
        """SIGTERM → SIGKILL the timed-out command *and its group*, then reap it.
        Returns ``kill_tree``'s verdict; ``None`` when the kill raised (the
        command was then sent a kill through its job or its ``Popen``,
        unconfirmed).

        ``start_time=None`` is how an unverified kill is *requested*: this pid is
        a child still held open here, not a record read off disk, so there is
        nothing to corroborate and no recycled pid to protect; as ``child``,
        unreaped until the wait below, it anchors its pid and group through the
        kill where the owned kill runs (Linux, glibc or musl; see ``kill_tree``).
        *job* is the command's Windows Job Object, the group's stand-in there.

        Only ``killed`` and ``gone`` confirm the command stopped, the executor's
        rule for its timed-out runner (``process_control.unconfirmed_kill``):
        a ``survived`` that is only the command's own zombie becomes ``killed``
        once its exit is confirmed (``process_control.own_child_stopped``), and
        any other outcome is logged as a warning naming the pid, which a
        detached run's record keeps for a later abort or sweep
        (``detach.note_left_running``; docs/development/write-scheduler.md,
        "When the verify command times out").
        """
        verdict: Optional[str]
        try:
            verdict = _process_control.kill_tree(
                proc.pid, start_time=None, pgid=pgid,
                escalate_after_s=VERIFY_KILL_GRACE_S, poll_interval_s=0.05,
                job=job, child=proc,
            )
            if verdict == "survived" and _process_control.own_child_stopped(proc, pgid):
                verdict = "killed"
        except Exception:  # noqa: BLE001 - teardown must never mask the timeout
            verdict = None
            if job is None or not job.terminate():
                try:
                    proc.kill()
                except OSError:  # pragma: no cover - already gone
                    pass
        try:
            proc.wait(timeout=VERIFY_REAP_S)
        except subprocess.TimeoutExpired:  # pragma: no cover - survived SIGKILL
            pass
        reason = _process_control.unconfirmed_kill(verdict)
        if reason is not None:
            detach = sys.modules.get(f"{__package__}.detach") if __package__ else None
            kept = detach is not None and detach.note_left_running(proc.pid, pgid, verdict)
            self._ctx.log(
                f"[write-subagents] warning: the timed-out verification command "
                f"pid {proc.pid} (process group {pgid if pgid is not None else '?'}) "
                f"could not be confirmed stopped (kill verdict {verdict}): {reason}, "
                f"so it may still be running. Check it by hand"
                + ("; the run's record keeps it for status --abort." if kept else ".")
            )
        return verdict

    @staticmethod
    def left_the_group(
        pid: int, pgid: Optional[int],
    ) -> List[_process_control.Descendant]:
        """The timed-out command's descendants outside its process group
        *pgid*, listed before the kill: the list follows parent links, and
        once a process's parent dies it belongs to init. A ``setsid`` or a
        daemon's double fork leaves the group, and the group kill never
        reaches it. Empty when the group is unknown, on Windows (the command's
        Job Object holds the whole tree) and when the process table cannot be
        read (docs/development/write-scheduler.md, "When the verify command
        times out")."""
        if pgid is None or _process_control.IS_WINDOWS:
            return []
        try:
            found = _process_control.descendants(pid)
        except Exception:  # noqa: BLE001 - a look at the process table never fails the check
            return []
        return [entry for entry in found if entry.pgid != pgid]

    @staticmethod
    def named(outside: Sequence[_process_control.Descendant]) -> str:
        """``pid 7 (process group 7)`` for each process in *outside*, for a
        message."""
        return ", ".join(
            f"pid {entry.pid} (process group "
            f"{entry.pgid if entry.pgid is not None else '?'})" for entry in outside)

    def left_outside(
        self, pid: int, outside: Sequence[_process_control.Descendant],
    ) -> List[_process_control.Descendant]:
        """The processes in *outside* (:meth:`left_the_group`, listed before
        the kill) not confirmed gone after it: their pid is still that
        process (its start time, where known) or cannot be told apart from
        it. Each is logged as a warning: no signal reached them and none is
        recorded for a later abort, so the user stops them by hand
        (docs/development/write-scheduler.md, "When the verify command
        times out")."""
        left = [entry for entry in outside
                if _process_control.probe(entry.pid, entry.start_time)
                != _process_control.DEAD]
        if left:
            count = len(left)
            self._ctx.log(
                f"[write-subagents] warning: the timed-out verification command "
                f"pid {pid} started {count} process{'' if count == 1 else 'es'} "
                f"outside its process group, which the kill of the group does not "
                f"reach, still running: {self.named(left)}. Nothing records "
                f"{'it' if count == 1 else 'them'} for status --abort; check by hand.")
        return left

    def output_tail(self, sink: Any) -> str:
        """The last :data:`VERIFY_OUTPUT_CAP_BYTES` the command wrote, as text."""
        try:
            size = sink.seek(0, os.SEEK_END)
            sink.seek(max(0, size - VERIFY_OUTPUT_CAP_BYTES))
            raw = sink.read()
        except (OSError, ValueError):  # pragma: no cover - sink already closed
            return ""
        if isinstance(raw, bytes):
            return raw.decode("utf-8", errors="replace")
        return raw or ""

    def env(self) -> Optional[Dict[str, str]]:
        """The environment ``driver.verify_command`` runs with (F6).

        Composed by the same function the runner spawn uses
        (``providers.base.build_child_env``) instead of being inherited wholesale
        from ``os.environ``: the running host's own ``env_guards`` — the
        nested-session marker and the session-scoped ids this dispatcher was
        handed — are stripped, and an operator who turned ``env_allowlist`` on
        gets this check reduced to the same deny-by-default set a runner sees.
        There is no provider (this is the repository's own command, not an agent
        CLI), so nothing adapter-specific applies, and ``None`` means "inherit
        unchanged" exactly as it does at the two spawn sites.

        The reason it is worth composing at all: the *string* is config and a run
        cannot change it, but the **scripts it invokes** — `package.json`'s
        `typecheck`, a `Makefile` target — are files the write subagent was just
        allowed to edit, so this command is inside the phase's own blast radius.
        `docs/configuration.md`'s safety section says so too.
        """
        try:
            guards, passthrough = _host_env_guards()
            return build_child_env(
                None, provider_env={}, host_guards=guards,
                host_passthrough=passthrough, anchor=self._ctx.anchor,
            )
        except Exception as exc:  # noqa: BLE001 - env policy must not fail a check
            self._ctx.log(
                f"[write-subagents] warning: could not compose the verification "
                f"environment ({exc}); inheriting this process's unchanged"
            )
            return None
