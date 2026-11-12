"""The write grant of one write phase (plan step 3, 2026-09-30; F1 "How a
dispatch receives its grant").

A write phase carries ONE grant: the scope its kind maps to
(``write_batch_scheduler.write_scope_for_kind``), the phase's one write target
and the one :class:`JailRequest` built from them, never a per-task path, so
nothing a task file says can widen it. :func:`checked_write_target` and
:func:`build_jail_request` make the target and the request when the scheduler
is built; :class:`WriteGrant` is what the run does with them: the pre-dispatch
check that a task declares exactly the grant (:meth:`WriteGrant.grant_mismatch`),
the runner's preflight under the request and the rung it recorded
(:meth:`WriteGrant.preflight`, :meth:`WriteGrant.recorded_rung`,
:meth:`WriteGrant.announce_rung`), the replaced-target check
(:meth:`WriteGrant.target_replacement`,
:meth:`WriteGrant.replaced_target_unclassified`), the jail's denials as the
verdict reads them (:meth:`WriteGrant.jail_facts`) and the warn-only
``[GIT_CONFIG_CHANGED]`` line of a repo-wide batch
(:meth:`WriteGrant.warn_git_metadata_changed`).

``WriteBatchScheduler`` composes it with the run's ``RunContext``
(docs/development/write-scheduler.md#where-the-schedulers-helpers-live). Its
per-dispatch records, keyed by task id, are its own; the scheduler's loop and
its classification read and spend them. ``dispatch_rungs`` is the scheduler's
own dict (the rung each executor dispatch ran on), handed in and never rebound.
"""

from __future__ import annotations

import os
from dataclasses import replace
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from . import git_utils as _git_utils
from . import landlock_dispatch as _landlock
from . import probe_state as _probe_state
from . import sandbox_walk as _sandbox_walk
from . import write_context as _write_context
from .providers.base import (
    SANDBOX_RUNG_PLUGIN_LANDLOCK,
    WRITE_SCOPE_REPO_WIDE,
    WRITE_SCOPE_TASKS,
    WRITE_SCOPES_ON_RUNG,
    JailRequest,
)
from .task_dispatch import STATUS_BATCH_FAILED
from .batch_reply import WRITE_CLEAN_FAILURE
from .task_outcome import (
    ExecutorError,
    TaskOutcome,
)
from .runner_preflight import preflight_runner
from .subagent_tasks import declared_file_set
from .write_safety import TaskSnapshot, relative_to_root
from .write_verdict import (
    JailFacts,
    TargetReplaced,
    WriteFacts,
    guard,
    replaced_target_reason,
)


def checked_write_target(
    raw: Optional[str], *, repo_root: str, phase: str,
) -> Optional[str]:
    """``raw`` ``realpath``-resolved, or refuse the phase at construction.

    F1 "How a dispatch receives its grant": the target must exist, be a
    regular file, not be a symlink (checked on the path as given, before
    resolution) and lie under the repo root. A target that fails any of
    these is a phase that cannot be granted, so it fails here with exit 3
    and nothing dispatched, rather than as a jail refusal mid-run.
    """
    if raw is None or not str(raw).strip():
        return None
    given = os.path.abspath(str(raw))
    problem = None
    if os.path.islink(given):
        problem = "is a symlink (a grant is never bound through one)"
    elif not os.path.exists(given):
        problem = "does not exist"
    elif not os.path.isfile(given):
        problem = "is not a regular file"
    resolved = os.path.realpath(given)
    root = os.path.realpath(repo_root)
    if problem is None and not resolved.startswith(root.rstrip(os.sep) + os.sep):
        problem = f"lies outside the repository root {root}"
    if problem is not None:
        raise ExecutorError(
            f"The {phase} write target {given} {problem}, so this "
            f"phase cannot be granted its one file. Nothing was dispatched."
        )
    return resolved


def build_jail_request(
    *,
    kind: str,
    write_scope: Optional[str],
    repo_root: str,
    output_dir: str,
    write_target: Optional[str],
    plan_file: Optional[str],
) -> Optional[JailRequest]:
    """The phase's one :class:`JailRequest` (F1 "How a dispatch receives
    its grant").

    ``plan-file`` and ``tasks`` carry the target; ``tasks`` also carries a
    ``target_dir`` — a dir rule — only when the tasks file sits in the
    plan's default ``plans/<stem>/tasks/`` (``default_tasks_dir``), and a
    file rule on the tasks file anywhere else. ``repo-wide`` (step 3b;
    one dir rule on the root since 2026-10-05) carries no target but this
    run's output folder, which the developer message names as hands-off.
    """
    if not write_scope:
        return None
    repo_root = os.path.realpath(repo_root)
    if write_scope == WRITE_SCOPE_REPO_WIDE:
        return JailRequest(
            repo_root=repo_root, kind=kind, write_scope=write_scope,
            output_dir=os.path.realpath(output_dir),
        )
    if write_scope not in WRITE_SCOPES_ON_RUNG:
        return JailRequest(
            repo_root=repo_root, kind=kind, write_scope=write_scope,
        )
    target_dir = None
    if (
        write_scope == WRITE_SCOPE_TASKS
        and write_target and plan_file
    ):
        target_dir = _landlock.default_tasks_dir(
            plan_file, write_target
        )
    return JailRequest(
        repo_root=repo_root, kind=kind, write_scope=write_scope,
        target=write_target, target_dir=target_dir,
    )


class WriteGrant:
    """What one write phase does with its grant, dispatch by dispatch.

    Built once per run by the scheduler, over the scope, target and request
    it made at construction (:func:`checked_write_target`,
    :func:`build_jail_request`). *dispatch_rungs* is the scheduler's
    ``task id -> rung`` dict, filled as each executor dispatch preflights.
    """

    def __init__(
        self,
        ctx: _write_context.RunContext,
        *,
        write_scope: Optional[str],
        write_target: Optional[str],
        jail_request: Optional[JailRequest],
        dispatch_rungs: Mapping[str, Optional[str]],
    ) -> None:
        self._ctx = ctx
        self.write_scope = write_scope
        self.write_target = write_target
        self.jail_request = jail_request
        self._dispatch_rungs = dispatch_rungs
        #: The write target's ``(st_dev, st_ino)`` recorded right after this
        #: dispatch's pre-batch snapshot — never the first run's, so a
        #: ``util restore-batch`` between runs (whose ``os.replace`` leaves a
        #: new inode) does not read as a replaced target (§8.3 item 14).
        self.target_identity_before: Dict[str, Optional[Tuple[int, int]]] = {}
        #: The jail-denial count that did not change a verdict (out-of-scope
        #: denials, or a replacement the runner recovered from), for the
        #: batch's line and its outcome's reason.
        self.jail_notes: Dict[str, str] = {}
        #: The denials themselves, for the report row.
        self.jail_denials: Dict[str, Dict[str, Any]] = {}
        #: Root grant (2026-10-05): ``task_id -> git_utils.git_metadata_fingerprint``
        #: taken right before a repo-wide dispatch, compared after it for the
        #: warn-only ``[GIT_CONFIG_CHANGED]`` line (never a copy, never a revert).
        self.git_meta_before: Dict[str, Optional[Dict[str, Any]]] = {}
        #: Tasks whose verdict came from the jail (a denied edit or a replaced
        #: target) and failed the batch: never a success line in the
        #: prior-changes log — the failed batch's own line, which the
        #: ``--resume`` that re-dispatches it supersedes (fix round 15).
        self.jail_failed: set = set()
        #: The subset whose target was replaced under the batch: their failure
        #: writes no prior-changes line at all (fix round 15).
        self.replaced_targets: set = set()
        #: Batch indexes whose stray-writes-only line was already printed.
        self.rung_noticed: set = set()

    def git_metadata_fingerprint(self) -> Optional[Dict[str, Any]]:
        """``git_utils.git_metadata_fingerprint`` of the pinned root for a
        ``repo-wide`` batch (a hash and a listing, never bytes); ``None`` for
        the narrower scopes, whose grant never reaches ``.git/``, and on any
        failure — a warning line may not fail a dispatch."""
        if self.write_scope != WRITE_SCOPE_REPO_WIDE:
            return None
        try:
            return _git_utils.git_metadata_fingerprint(self._ctx.repo_root)
        except Exception:  # noqa: BLE001 - observability must not fail a phase
            return None

    def warn_git_metadata_changed(self, task_id: str) -> None:
        """One warn-only ``[GIT_CONFIG_CHANGED]`` line when ``.git/config`` or
        the ``.git/hooks/`` listing moved across this dispatch (root grant,
        2026-10-05: the sweep prunes ``.git/`` and nothing is backed up, so
        this line is the one place a planted hook or config key is named).
        The user's own git honours what was planted; the plugin's calls carry
        ``git_utils.GIT_HARDENING_ARGS``. Never a failed batch."""
        before = self.git_meta_before.pop(task_id, None)
        if before is None:
            return
        try:
            change = _git_utils.describe_git_metadata_change(
                before, self.git_metadata_fingerprint()
            )
        except Exception:  # noqa: BLE001 - observability must not fail a phase
            return
        if change:
            self._ctx.log(
                f"{_git_utils.GIT_CONFIG_CHANGED_MARKER} {task_id}: the repository's "
                f"git metadata changed during this batch ({change}). The jail "
                f"grants the whole repository and nothing was backed up; "
                f"inspect .git/config and .git/hooks/ before your next git "
                f"command runs what a batch may have planted (warn-only)."
            )

    def grant_mismatch(self, task: Dict[str, Any]) -> Optional[str]:
        """Why ``task``'s declared set is not this phase's grant, or ``None``.

        Under ``plan-file`` and ``tasks`` the declared set must resolve to
        exactly the target, on every rung (F1 "How a dispatch receives its
        grant"). ``materialize_write_tasks`` always declares exactly the target,
        so only an edited task file differs — and the task file is re-read on
        ``--resume``, so it is checked here and never supplies a grant.
        """
        if self.write_scope not in WRITE_SCOPES_ON_RUNG or not self.write_target:
            return None
        declared = declared_file_set(task)
        resolved = set()
        for path in declared:
            candidate = path if os.path.isabs(path) else os.path.join(
                self._ctx.repo_root, path
            )
            resolved.add(os.path.realpath(candidate))
        if resolved == {self.write_target}:
            return None
        shown = ", ".join(declared) or "nothing"
        return (
            f"Refusing to dispatch write task {task.get('task_id')}: it declares "
            f"{shown}, but a {self._ctx.kind} batch's grant ({self.write_scope}) is "
            f"exactly this phase's write target {self.write_target}. Only an "
            f"edited task file declares anything else, and a task file never "
            f"supplies a grant. Nothing was snapshotted or dispatched."
        )

    def identity_path(self) -> Optional[str]:
        """What the replaced-target check watches: the target file under a
        file rule, the tasks directory under the dir rule (F1 "Supported edits
        under a file-only grant", "The target replaced during the dispatch")."""
        request = self.jail_request
        if request is None or request.write_scope not in WRITE_SCOPES_ON_RUNG:
            return None
        return request.target_dir or request.target

    @staticmethod
    def identity_of(path: Optional[str]) -> Optional[Tuple[int, int]]:
        """``(st_dev, st_ino)`` of ``path`` itself (``lstat``), or ``None``."""
        if not path:
            return None
        try:
            info = os.lstat(path)
        except OSError:
            return None
        return (info.st_dev, info.st_ino)

    def target_label(self) -> str:
        request = self.jail_request
        if request is not None and request.target_dir:
            return "the tasks directory"
        if self.write_scope == WRITE_SCOPE_TASKS:
            return "the tasks file"
        return "the plan file"

    def preflight(
        self, runner: str, profile: str, **extra: Any
    ) -> Dict[str, Any]:
        """``preflight_runner`` with this phase's request.

        For ``agent-write`` the request's scope joins the executor's sandbox
        decision key, so a ``plan-file`` decision is never replayed for a
        ``repo-wide`` dispatch of the same runner.
        """
        return preflight_runner(
            runner, profile=profile, anchor=self._ctx.anchor,
            key="driver.subagent_runner", jail_request=self.jail_request,
            **extra,
        )

    def recorded_rung(self, runner: str, profile: str) -> Optional[str]:
        """The fallback rung the preflight recorded for this runner, profile
        and scope, or ``None`` (codex's own sandbox, or another runner)."""
        try:
            rung = _probe_state.sandbox_rung(
                runner, profile, write_scope=self.write_scope or None
            )
        except Exception:  # noqa: BLE001 - a lookup must never fail a dispatch
            return None
        return str(rung) if rung else None

    def announce_rung(self, runner: str, batch_index: Optional[int]) -> None:
        """Print the stray-writes-only line once before a batch on the rung.

        The executor composes it (``write_rung_notice``, the same builder as
        every ``[SANDBOX_INCIDENTAL]`` line): it names the scope, the target
        and the open network, and it is ``None`` for a batch on codex's own
        sandbox, which therefore prints nothing (§8.2 "The stray-writes-only
        line").
        """
        if self.jail_request is None:
            return
        key = batch_index if batch_index is not None else runner
        if key in self.rung_noticed:
            return
        try:
            notice = _sandbox_walk.write_rung_notice(runner, self.jail_request)
        except Exception:  # noqa: BLE001 - a notice must never fail a dispatch
            return
        if notice:
            self.rung_noticed.add(key)
            self._ctx.log(str(notice))

    def relative(self, path: str) -> str:
        """``path`` repo-relative when it lies under the root, else as given."""
        return relative_to_root(path, self._ctx.repo_root)

    def in_grant(self, path: str, task_id: Optional[str] = None) -> bool:
        """Whether the resolved ``path`` is inside this phase's write grant —
        under ``repo-wide`` (one dir rule on the root, 2026-10-05), inside
        the repository."""
        request = self.jail_request
        if request is not None and request.write_scope == WRITE_SCOPE_REPO_WIDE:
            root = os.path.realpath(request.repo_root)
            resolved = os.path.realpath(path)
            return resolved == root or resolved.startswith(root.rstrip(os.sep) + os.sep)
        if request is None or not request.target:
            return False
        resolved = os.path.realpath(path)
        if request.target_dir:
            base = os.path.realpath(request.target_dir)
            return resolved == base or resolved.startswith(base.rstrip(os.sep) + os.sep)
        return resolved == os.path.realpath(request.target)

    def target_replacement(
        self, before: Optional[Tuple[int, int]],
    ) -> Optional[TargetReplaced]:
        """The replaced-target check (F1 "The target replaced during the
        dispatch"): the watched target's identity now against *before*, the
        one recorded at this dispatch's pre-batch snapshot. ``None`` when it
        is the same file, or there is nothing to compare.

        Detection only: the plugin never guesses which process swapped the
        file, and never widens the grant to the directory to ride a swap out.
        """
        path = self.identity_path()
        if path is None or before is None:
            return None
        after = self.identity_of(path)
        if after == before:
            return None
        return TargetReplaced(
            label=self.target_label(),
            shown=self.relative(path),
            before_inode=before[1],
            after_inode=None if after is None else after[1],
        )

    def record_replaced_target(self, outcome: TaskOutcome) -> None:
        """A replaced target's records. No rollback over the new file:
        ``files_touched`` is what ``util restore-batch`` restores, so the
        target (and, under the dir rule, anything beneath it) leaves it; the
        pre-batch snapshot stays on disk for comparison."""
        outcome.files_touched = [
            relative for relative in outcome.files_touched
            if not self.in_grant(os.path.join(self._ctx.repo_root, relative))
        ]
        self.jail_failed.add(outcome.task_id)
        self.replaced_targets.add(outcome.task_id)

    def replaced_target_unclassified(
        self, outcome: TaskOutcome, snapshot: TaskSnapshot
    ) -> bool:
        """The replaced-target verdict for a plugin-landlock dispatch that
        never reached the scheduler's ``_classify``. ``True`` when it decided
        the outcome.

        ``_classify`` runs only on a schema-valid result. A timeout, a runner
        error, a schema-invalid reply, a ``[JAIL_DENIED]`` rejection or a
        T4.8 partial ends in ``WriteBatchScheduler._audit_terminal`` instead, whose
        ``files_touched`` is the byte comparison against the snapshot. A target
        saved over by rename differs from that snapshot, so without this check
        the audit record, and the stop message's restore-batch command, would
        overwrite the new file, which may be the user's. F1: a replaced target
        is never restored. The verdict is the replaced-target row's
        (:func:`write_verdict.replaced_target_reason`), naming the dispatch's
        own ending in the claim's place, with its failure kept at the end.
        """
        task_id = outcome.task_id
        if self._dispatch_rungs.get(task_id) != SANDBOX_RUNG_PLUGIN_LANDLOCK:
            return False
        replaced = self.target_replacement(
            self.target_identity_before.pop(task_id, None)
        )
        if replaced is None:
            return False
        ended, detail = outcome.status, outcome.reason
        self.record_replaced_target(outcome)
        outcome.status = STATUS_BATCH_FAILED
        outcome.write_outcome = WRITE_CLEAN_FAILURE
        outcome.reason = replaced_target_reason(
            replaced, str(snapshot.directory), "", ended=ended,
        )
        if detail:
            outcome.reason = f"{outcome.reason} The dispatch's own failure: {detail}"
        return True

    def jail_facts(
        self, task_id: str, denials: Any, facts: WriteFacts,
    ) -> JailFacts:
        """The jail's denials (F1 "A denied edit is never recorded as
        applied") as the verdict reads them, every path repo-relative.

        The row's facts name no path. Each path is resolved after them, and
        only for what *facts* with them land on: the denied paths and the
        scope sentence when a jail row decides, the note's when none does.
        """
        replaced = list(denials.replacement_paths)
        jail = JailFacts(
            hard=bool(denials.failed_file_changes or denials.in_scope_paths),
            replacements=len(replaced),
        )
        if guard(replace(facts, jail=jail)) is None:
            return replace(
                jail,
                replacement=tuple(self.relative(p) for p in replaced),
                out_of_scope_count=denials.out_of_scope_count,
                out_of_scope=(
                    tuple(self.relative(p) for p in denials.out_of_scope_paths)
                    if denials.out_of_scope_count else ()
                ),
            )
        denied = denials.denied_paths()
        paths = [self.relative(p) for p in denied]
        in_grant = [
            self.relative(p) for p in denied
            if self.in_grant(p, task_id) or p in replaced
        ]
        return replace(
            jail,
            denied=tuple(paths),
            scope_sentence=self.jail_scope_sentence(
                in_grant, [p for p in paths if p not in in_grant],
            ),
        )

    def jail_scope_sentence(
        self, in_grant: Sequence[str], outside: Sequence[str]
    ) -> str:
        """The reason's second half: why an in-grant path was refused, what to
        do instead, and F6 (the non-Codex runner)."""
        request = self.jail_request
        parts: List[str] = []

        def verb(paths: Sequence[str], one: str, many: str) -> str:
            return one if len(paths) == 1 else many

        if in_grant and request is not None and request.write_scope == WRITE_SCOPE_REPO_WIDE:
            parts.append(
                f"{', '.join(in_grant)} {verb(in_grant, 'lies', 'lie')} inside "
                f"the repository, which the jail granted whole (one rule on "
                f"its root, 2026-10-05): a denial there is the jail's own "
                f"failure, not a write shape the grant withholds."
            )
        elif in_grant:
            target = self.relative(request.target) if request and request.target else "the target"
            if request is not None and request.target_dir:
                parts.append(
                    f"{', '.join(in_grant)} {verb(in_grant, 'lies', 'lie')} "
                    f"inside this batch's grant (the "
                    f"tasks directory {self.relative(request.target_dir)}), so "
                    f"the allow-list may not grant the write shape the runner "
                    f"used (a new sibling file, a rename)."
                )
            else:
                parts.append(
                    f"{', '.join(in_grant)} {verb(in_grant, 'belongs', 'belong')} "
                    f"to this batch's "
                    f"{self.write_scope} grant, which admits in-place edits of "
                    f"{target} only: the allow-list does not grant the write "
                    f"shape the runner used (a new sibling file, a rename — "
                    f"sed -i, perl -i, a temp-file save, mv over it). Edit it in "
                    f"place with apply_patch (or a shell redirect); the grant "
                    f"never widens to its directory."
                )
        if outside:
            parts.append(
                f"{', '.join(outside)} {verb(outside, 'lies', 'lie')} outside "
                f"this batch's grant: the runner tried an edit its scope does "
                f"not grant."
            )
        parts.append(
            "To run this batch without the jail, set `driver.subagent_runner` "
            "to a runner that is not Codex (F6)."
        )
        return " ".join(parts) + " "
