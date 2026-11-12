"""One fan-out slot's sandbox gate and write audit: :class:`SlotGuard`.

Every lane that dispatches a fan-out slot brackets the dispatch with the same
sequence: ask's single-shot slot (``AskRun.ask_one``), review-code's
``run_single_review``, and ``run_single_model`` for review-plan and
review-tasks, on both of its lanes (the file-output ladder and the single
stdout dispatch). This module is that sequence, written once.

* :meth:`SlotGuard.begin`, before anything is dispatched. It runs the
  pre-dispatch sandbox gate (``sandbox_refusal``) and prints the one line a
  refusal or a fallback rung gets. Then it takes the before-snapshots: the
  porcelain baseline on the uncontained rung, the file modes on the plugin's
  own jail. A refused slot comes back :class:`Refused` and must not be
  dispatched.
* :meth:`SlotGuard.finish`, once, after the slot's last attempt. It runs the
  porcelain delta and its verdict (a not-attributed warning when the slot's
  own audited stream clears it, otherwise the fail-closed violation naming the
  boundary-less siblings), the jail's own lines when the lane asks for them,
  and the mode and home checks. It returns the one reason the slot fails
  with, or ``None``.

What a lane does with that reason stays the lane's: ask sets the answer file
aside as ``.violated`` and keeps its stdout text as a partial, review-code
records the tracker's ``failed`` and returns its tuple, and the review base
drops ``output`` so ``save_model_result`` never parses it.

The checks themselves are ``review_orchestrator_base``'s and are looked up on
that module at call time. They stay there because the sibling counts there
ask the same gate, and the tests that pin a probe verdict or a snapshot patch
them on that module.

The rules are in docs/development/providers.md (the fallback ladder, the
porcelain check and its stream-audit exemption, the plugin's jail and its mode
and home checks) and docs/development/write-safety.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, Optional, Sequence, Union

from . import readonly_audit as _readonly_audit
from . import review_orchestrator_base as _base

#: Every attempt's ``details["home_check"]``, or, for a lane whose single call
#: raised, a coroutine function that compares the homes that call armed
#: (``raised_attempt_home_records``). The second form runs only when the
#: write check passed, which is where the stdout lane has always run it.
HomeChecks = Union[Sequence[Any], Callable[[], Awaitable[Sequence[Any]]]]


@dataclass(frozen=True)
class Refused:
    """The gate refused the slot: dispatch nothing. ``reason`` is the
    ``[SANDBOX_UNAVAILABLE]`` line, already printed under the slot's name."""

    reason: str


@dataclass(frozen=True)
class Ready:
    """The slot may be dispatched with ``sandbox_fallback_kwargs(sandbox)``."""

    sandbox: _base.SandboxVerdict


class SlotGuard:
    """The gate and the write audit around one fan-out slot's dispatch.

    ``display_name`` prefixes every line the guard prints (ask's slots print
    under the model spec, the review lanes under ``provider:model``).
    ``tracker`` is the fan-out's ``FanoutProgress`` or ``None``; the guard
    records the audit verdicts and the not-attributed warnings on it and
    leaves every slot transition to the lane.

    The porcelain check's ignore list is resolved in ``begin()`` and again in
    ``finish()``, before the after snapshot, and a path is left out only where
    both lists leave it out (``common_ignore_prefixes``). The list follows the
    plan's output folder through symlinks, and an unsandboxed slot can
    re-point that folder during its window; either list alone would then
    leave out a tracked tree. The folders only one list covers are hashed
    apart from the rest, so they can never switch off the content comparison
    of the paths both lists audit (docs/development/providers.md, the
    porcelain check).
    """

    def __init__(
        self,
        *,
        provider_name: str,
        display_name: str,
        model_spec: str,
        project_root: Optional[str],
        plan_path: Union[str, Path],
        tracker: Optional[Any] = None,
    ) -> None:
        self.provider_name = provider_name
        self.display_name = display_name
        self.model_spec = model_spec
        self.project_root = project_root
        self.plan_path = plan_path
        self.tracker = tracker
        self.sandbox: Optional[_base.SandboxVerdict] = None
        self._ignore_before: Sequence[str] = ()
        self._tree_before: Optional[_base.PorcelainSnapshot] = None
        self._mode_before: Optional[Dict[str, str]] = None

    async def begin(self) -> Union[Refused, Ready]:
        """The gate, then the before-snapshots; call it before the dispatch.

        The gate runs in a thread: it may spawn the sandbox probe, and the
        sibling slots share this event loop. So do the snapshots, since
        ``git status`` is not instant on a large repository. The porcelain
        baseline is taken for the uncontained rung alone (the rung id decides,
        ``porcelain_check_applies``), so a sandboxed or contained-rung slot
        makes no git call. Its ignore list is the roster-aware one, computed
        here in the slot's task where the fan-out roster lives; ``finish()``
        resolves it again and keeps only what both cover. The entries under
        the plan's output folder, the one entry that follows symlinks, are
        kept in the baseline as a zone of their own, hashed under their own
        cap, for ``finish()`` to compare should the list move; otherwise they
        are never compared. The mode baseline is taken for the plugin's own
        jail alone (``mode_check_applies``).
        """
        sandbox = await _base.phase_thread(
            _base.sandbox_refusal, self.provider_name, self.project_root
        )
        self.sandbox = sandbox
        if sandbox.refused:
            print(f"[{self.display_name}] {sandbox.reason}")
            return Refused(sandbox.reason)
        # Any fallback rung prints its one line: `[SANDBOX_FALLBACK]` for a
        # contained rung, `[SANDBOX_INCIDENTAL]` for the plugin's jail,
        # `[SANDBOX_BYPASSED]` for the uncontained one.
        if sandbox.fallback:
            print(f"[{self.display_name}] {sandbox.reason}")
        if _base.porcelain_check_applies(sandbox):
            self._ignore_before = self._resolve_ignore_prefixes()
            self._tree_before = await _base.phase_thread(
                _base.porcelain_snapshot, self.project_root,
                ignore_prefixes=self._resolve_ignore_prefixes(output_folder=False),
                zones=(self._ignore_before,),
            )
        if _base.mode_check_applies(sandbox):
            self._mode_before = await _base.phase_thread(
                _base.mode_snapshot, self.project_root
            )
        return Ready(sandbox)

    async def finish(
        self,
        audits: Sequence[Any],
        home_checks: HomeChecks,
        *,
        summary_key: Any,
        jail_details: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """The one reason this slot fails with, or ``None``; once, after the
        slot's last attempt and before the lane reads anything it returned.

        ``audits`` is every attempt's ``details["readonly_audit"]`` in the
        slot's window, ``None`` for an attempt that raised (plan §4.3: ANDed,
        so a clean retry never excuses an earlier attempt). ``summary_key``
        keys the run's closing summary (the phase or question directory).

        The write check runs first and its violation ends the sequence. Then
        ``jail_details``, when given, gets its ``[JAIL_DENIED]`` line and
        in-stream denial count (``report_jail_outcome``). Ask's single-shot
        slot passes its call's ``details``; the ladder lanes leave it out,
        because the ladder loop reports the jail per attempt. Then the mode
        and home checks for a slot on the plugin's jail.
        """
        violation = await self._write_check(audits, summary_key)
        if violation is not None:
            return violation
        if jail_details is not None:
            _base.report_jail_outcome(self.display_name, jail_details, summary_key)
        if callable(home_checks):
            home_checks = await home_checks()
        return await _base.run_incidental_checks(
            self._verdict(), provider_name=self.provider_name,
            display_name=self.display_name, model_spec=self.model_spec,
            project_root=self.project_root, plan_path=self.plan_path,
            mode_before=self._mode_before, home_checks=home_checks, audits=audits,
            tracker=self.tracker, summary_key=summary_key,
        )

    async def _write_check(
        self, audits: Sequence[Any], summary_key: Any
    ) -> Optional[str]:
        """The reason to fail an uncontained slot whose window changed the tree, or ``None``.

        A delta fails the slot whatever the attempt reported. A review that
        also edited the repository is not a review the phase may count. Nothing
        is restored: no snapshot of the files was taken, so the operator is
        told which paths and left to decide. The reason line
        (``bypass_write_violation``) states the change without naming an
        author, and counts the fan-out's other boundary-less slots. ``None``
        for every slot not on the uncontained rung: the rung id gates it, so a
        contained-rung or sandboxed slot makes no git call at all. The
        ``git status`` and the sibling count run in threads, like the gate.

        When the AND of ``audits`` is clean and option B is switched on
        (``bypass_stream_audit_clears``), the delta is reported as a
        ``not attributed`` warning on ``progress.models[spec].warning`` and
        the slot keeps its output.

        The ignore list is resolved again here, in the slot's task like
        ``begin()``'s and before the after snapshot. When both lists cover the
        same paths, the after snapshot and the comparison are the plain ones.
        When they differ, one ``[SANDBOX_BYPASSED]`` line names the folders
        only one of them covers (``bypass_ignore_drift``), printed and noted
        for the closing summary, and only what both cover is left out
        (``common_ignore_prefixes``). The after snapshot then hashes the paths
        outside both lists and the folders under each list alone under caps
        of their own, and ``unexpected_writes_across_drift`` compares them, so
        the verdict names every change either list alone would have seen.
        """
        if not _base.porcelain_check_applies(self._verdict()):
            return None
        ignore_after = self._resolve_ignore_prefixes()
        drift = _base.bypass_ignore_drift(
            self.provider_name, self._ignore_before, ignore_after
        )
        if drift is not None:
            print(f"[{self.display_name}] {drift}")
            _base.note_for_closing_summary(summary_key, drift)
        if self.tracker is not None:
            self.tracker.record_readonly_audit(
                self.model_spec, _readonly_audit.combine_audits(audits).to_dict()
            )
        if drift is None:
            tree_after = await _base.phase_thread(
                _base.porcelain_snapshot, self.project_root,
                ignore_prefixes=ignore_after,
            )
            touched = _base.unexpected_writes(
                self._tree_before, tree_after, ignore_prefixes=ignore_after,
            )
        else:
            tree_after = await _base.phase_thread(
                _base.porcelain_snapshot, self.project_root,
                ignore_prefixes=_base.common_ignore_prefixes(
                    self._ignore_before, ignore_after
                ),
                zones=(ignore_after, self._ignore_before),
            )
            touched = _base.unexpected_writes_across_drift(
                self._tree_before, tree_after,
                before_prefixes=self._ignore_before, after_prefixes=ignore_after,
            )
        if not touched:
            return None
        if _base.bypass_stream_audit_clears(audits):
            warning = _base.bypass_write_not_attributed(self.provider_name, touched)
            print(f"[{self.display_name}] {warning}")
            if self.tracker is not None:
                self.tracker.warn(self.model_spec, warning)
            return None
        siblings = await _base.phase_thread(
            _base.boundaryless_sibling_count,
            self.model_spec, self.project_root, self.plan_path,
        )
        violation = _base.bypass_write_violation(
            self.provider_name, touched, boundaryless_siblings=siblings
        )
        print(f"[{self.display_name}] {violation}")
        return violation

    def _resolve_ignore_prefixes(self, *, output_folder: bool = True) -> Sequence[str]:
        """The roster-aware ignore list, resolved now; called in the slot's
        task, where the fan-out roster lives (``fanout_ignore_prefixes``).
        ``output_folder=False`` leaves out the plan's output folder."""
        return _base.fanout_ignore_prefixes(
            self.plan_path, self.project_root, anchor=self.plan_path,
            output_folder=output_folder,
        )

    def _verdict(self) -> _base.SandboxVerdict:
        if self.sandbox is None:
            raise RuntimeError("SlotGuard: the checks ran before begin() took the gate")
        return self.sandbox
