"""A cascade stage's close-out: its archive, its counts and the per-round table.

``--cascade`` (``utils/improve_cascade.py``) runs one review-then-apply round
per model. Each round's next round replaces the live phase dirs
(``--force --rerun-all``), and ``state.json`` keeps one record per group id,
so a later round overwrites an earlier round's records. When a stage's apply
is done, :func:`close_out` therefore copies the stage's review and apply dirs
into ``stage-<k>/artifacts/`` together with the ``state.json`` entries that
are the stage's own (``records.json``), and the counts, the per-round table
and the forward ledger (``utils/cascade_ledger.py``) are read from those
archives only.

**Copies, not moves.** The live dirs stay as the phases left them, so every
existing reader (``status``, ``--reaggregate``, the next-step lookup) works
unchanged; the next stage's fresh round retires them as today. Every file is
copied except ``*.lock`` files, and links are never followed: not inside a
live dir, and not at one. Before any lock is taken, each live dir and the
plan's output dir above it must be a real folder, not a link
(:func:`_hold_live`: a link is :class:`ArchiveRefusal`, exit 3, nothing locked
or copied); on Linux and macOS each is then reached from the plan's directory
without following a link and held by a descriptor, which its lock file is
opened and its tree walked relative to, so a folder swapped for a link
afterwards cannot lead the close-out outside the plan's output dir.

**Locks.** Close-out takes the composite run dir's lock, then the review
dir's, then the apply dir's, always in that order: the same
``process_control.PhaseLock`` files each phase run holds (one writer per
phase dir, docs/development/runtime.md). A lock this process already holds
(a detached worker's run dir) is used as it is and left held; one it takes is
retried as a composite step retries its own (``status`` polls take and drop
every lock), checked for an unconfirmed teardown
(``detach.refuse_unconfirmed_cleanup``), and released when the close-out
returns. A lock a live run holds is never broken: exit 3 with
``improve_workflow.live_owner_refusal``'s text. After locking, the caller's
``recheck`` re-reads the stage's state; a stage no longer done is
:class:`CloseOutRaced`.

**Publication.** The archive is built in ``artifacts.partial/``; the
publication mark ``.complete.json`` (cascade id, stage, model, round id,
``grouped.json`` hash, every file's sha256) is written last, and only then is
the directory renamed to ``artifacts/``, a name that does not exist yet. A
crash leaves either ``artifacts.partial/`` (removed and redone) or a
published ``artifacts/`` (read, never copied again). An ``artifacts/`` whose
mark is missing, invalid or another cascade's is exit 3 naming the directory.

Every write goes through the plan-output containment helpers
(``cascade_ledger.write_file`` / ``held_folder``), never a raw join.

The developer contract: docs/development/workflows.md, "A cascade
(``--cascade``)".
"""

from __future__ import annotations

import contextlib
import json
import os
import stat
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Mapping, Optional, Sequence, Tuple

from . import cascade_ledger as ledger_mod
from . import cascade_provenance as provenance
from . import detach, process_control
from .cascade_ledger import (
    ARTIFACTS,
    COMPLETE_NAME,
    COMPLETE_SCHEMA_VERSION,
    FILES_TOUCHED,
    JUDGE_SALVAGE_SOURCE,
    JUDGE_SOURCE,
    PARTIAL,
    PLAN_AFTER,
    RECORDS_NAME,
    RECORDS_SCHEMA_VERSION,
    STAGE_DIFF,
    ArchiveRefusal,
    Phases,
    read_json,
)
from .clock import local_iso
# The no-link walk and the folder held by its descriptor, as write_safety
# imports them: a live phase dir is read and locked through one.
from .held_folder import (
    OPENS_WITHOUT_FOLLOWING,
    _HeldFolder,
    _open_below_root,
    anchor_plan_dir,
    rename_in_plan_dir,
    utime_in_plan_dir,
)
from .judge_vocab import canonical_value, upgrade_legacy
from .metrics import format_duration
from .output_handler import output_dir_path
from .state_manager import _parse_completion_time, predates_review
from .text_clip import clip

__all__ = [
    "ArchiveRefusal",
    "CloseOutRaced",
    "COUNT_KEYS",
    "close_out",
    "extract_records",
    "published_counts",
    "render_summary",
    "stage_counts",
]

#: The keys of a stage's counts (``record.json`` ``stages[k].counts``), in
#: the order the table reads them. All ints except ``nothing_to_apply``
#: (bool), ``time_s`` (number or ``None``) and ``cost`` (string or ``None``;
#: ``None`` is "not recorded", never 0).
COUNT_KEYS = (
    "findings", "valid", "invalid", "needs_decision", "reraises",
    "applied", "no_op", "declined", "skipped_by_user", "held_back",
    "judge_approved", "judge_salvaged", "judge_skipped",
    "nothing_to_apply", "time_s", "cost",
)

_WRITE_TASKS = "write_tasks.json"
_STATE = "state.json"
_STATUS = ".status.json"

#: What the table prints for a value no file recorded.
NOT_RECORDED = "not recorded"


class CloseOutRaced(Exception):
    """The re-read after locking no longer shows the stage done: another run
    replaced its round or its apply between the plan and the locks. The locks
    are released; the caller plans again."""


# ---------------------------------------------------------------------------
# Locks: run dir, then review dir, then apply dir
# ---------------------------------------------------------------------------

def _lock_payload(mode: str, phase: str) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "holder": f"{mode} cascade close-out ({phase})",
        "mode": mode,
        "pid": os.getpid(),
        "process_start_time": process_control.process_start_time(os.getpid()),
        "acquired_at": datetime.now().isoformat(),
    }
    active = detach.active_run()
    if active is not None:
        payload["run_id"] = active.run_id
    return payload


def _take(stack: contextlib.ExitStack, plan: Path, mode: str, phase: str,
          directory: Path, live: Optional["_Live"]) -> None:
    """Hold *directory*'s phase lock for the rest of *stack*, or refuse.

    *live* is :func:`_hold_live`'s answer for it: ``None`` for a dir that
    does not exist, which is passed over (nothing in it can be copied, and
    making one only to lock it would add an empty phase dir to the live
    tree). A lock this process already holds (``improve_workflow.holding``'s
    registry, or any ``PhaseLock`` it took) is used as it is and stays held;
    its taker releases it. One it takes is opened relative to the folder
    *live* holds, never through a link (``PhaseLock.acquire``'s ``dir_fd``;
    by its path on Windows). Every lock, held or taken, is then checked for
    an earlier run's unconfirmed teardown before anything is read. Each is
    registered with ``improve_workflow.holding`` for the block, so a
    live-owner check run inside it (the caller's ``recheck``) does not read
    this process's own close-out as another run.
    """
    # Imported here: improve_workflow imports the cascade core, which imports this module.
    from . import improve_workflow as iw

    if live is None:
        return
    path = detach.lock_path(str(directory))
    held = iw._held_lock(directory) or process_control.held_phase_lock(path)  # noqa: SLF001
    if held is not None:
        try:
            detach.refuse_unconfirmed_cleanup(str(directory), plan_file=str(plan), phase=phase)
        except detach.DetachError as exc:
            raise ArchiveRefusal(str(exc)) from exc
        stack.enter_context(iw.holding(directory, held))
        return
    lock = process_control.PhaseLock(path)
    payload = _lock_payload(mode, phase)
    refused: Optional[process_control.LockUnavailable] = None
    for attempt in range(iw.STEP_LOCK_ATTEMPTS):
        if attempt:
            time.sleep(iw.STEP_LOCK_RETRY_S)
        try:
            if live.folder is not None:
                lock.acquire(payload, dir_fd=live.folder.fd)
            else:
                lock.acquire(payload)
        except process_control.LockUnavailable as exc:
            refused = exc
            continue
        except OSError as exc:
            raise ArchiveRefusal(
                f"ERROR: could not lock {path} ({exc}). A cascade close-out archives a "
                "phase dir only while it holds that dir's lock, so nothing was archived."
            ) from exc
        refused = None
        break
    if refused is not None:
        owner = iw._inspect(str(plan), phase, directory) or iw.LiveOwner(  # noqa: SLF001
            directory=str(directory),
            holder=str(refused.holder.get("holder") or "an unrecorded holder"),
            pid=refused.holder.get("pid"),
            verdict=process_control.holder_verdict(refused.holder or None),
            heartbeat_age_s=None,
            status_command=detach.status_command_for(str(plan), phase=phase),
            abort_command=None,
        )
        raise ArchiveRefusal(iw.live_owner_refusal(mode, owner))
    try:
        detach.refuse_unconfirmed_cleanup(str(directory), plan_file=str(plan), phase=phase,
                                          lock=lock)
    except detach.DetachError as exc:
        raise ArchiveRefusal(str(exc)) from exc
    stack.callback(lock.release)
    stack.enter_context(iw.holding(directory, lock))


# ---------------------------------------------------------------------------
# The live dirs: real folders, reached and held without following a link
# ---------------------------------------------------------------------------

#: Whether a live dir is held by a descriptor and walked relative to it
#: (Linux, macOS): the no-link walk from the plan's directory, ``fwalk``, and
#: ``stat`` relative to a folder without following a link at the name.
#: Windows checks each folder on the way with ``lstat`` and reads by path.
_HOLDS_LIVE = bool(
    OPENS_WITHOUT_FOLLOWING and hasattr(os, "fwalk")
    and os.stat in os.supports_dir_fd and os.stat in os.supports_follow_symlinks
)


@dataclass(frozen=True)
class _Live:
    """A live phase dir the close-out locks and copies: *path*, checked, and
    on Linux and macOS *folder*, the folder held by its descriptor (``None``
    on Windows)."""

    path: Path
    folder: Optional[_HeldFolder]


def _not_a_folder(path: Path, what: str) -> ArchiveRefusal:
    return ArchiveRefusal(
        f"ERROR: {path} is {what}, not the phase folder a cascade close-out archives, "
        "so archiving it could read or lock files outside the plan's output folder. "
        "Nothing was locked, copied or archived. Put the real folder back in its place "
        "(or remove the link), then run the command again."
    )


def _hold_live(stack: contextlib.ExitStack, plan: Path, directory: Path) -> Optional[_Live]:
    """*directory*, a live phase dir below the plan's output dir, checked and held; ``None`` when absent.

    Every folder from the plan's output dir down to *directory* is read with
    ``lstat`` before anything is locked: a link there, or anything but a
    folder, is :class:`ArchiveRefusal` (exit 3): the dir is never locked and
    nothing below it copied, since ``os.walk`` follows a link given as its
    root and the lock file would be created at the link's target. A folder
    missing on the way means the dir does not exist (passed over, as
    before). On Linux and macOS the dir is then reached from the plan's
    directory one component at a time without following a link
    (``held_folder``'s walk) and held by its descriptor for the rest of
    *stack*: its lock file is opened and its tree walked relative to it.
    """
    spelled = Path(os.path.abspath(str(plan))).parent
    try:
        parts = tuple(directory.relative_to(spelled).parts)
    except ValueError:
        raise _not_a_folder(directory, "not below the plan's folder") from None
    current = spelled
    for name in parts:
        current = current / name
        try:
            info = os.lstat(current)
        except FileNotFoundError:
            return None
        except OSError as exc:
            raise ArchiveRefusal(
                f"ERROR: cannot read {current} ({exc.strerror or exc}) to archive the cascade "
                "stage; nothing was locked, copied or archived.") from exc
        if stat.S_ISLNK(info.st_mode) or (
                hasattr(os.path, "isjunction") and os.path.isjunction(current)):
            raise _not_a_folder(current, "a link")
        if not stat.S_ISDIR(info.st_mode):
            raise _not_a_folder(current, "not a folder")
    if not _HOLDS_LIVE:
        return _Live(path=directory, folder=None)
    root = anchor_plan_dir(spelled)
    fd = _open_below_root(root, parts, folder=True)
    if fd is None:
        raise _not_a_folder(directory, "no longer the folder just checked (moved, or "
                                       "replaced by a link)")
    stack.callback(os.close, fd)
    return _Live(path=directory, folder=_HeldFolder(fd, root, parts, str(directory)))


@contextlib.contextmanager
def _locked(plan: Path, mode: str, dirs: Sequence[Tuple[str, Path]]) -> Iterator[List[Optional[_Live]]]:
    """Hold every ``(phase, dir)`` lock of *dirs*, taken in that order and
    released in the reverse order when the block ends, by return or raise;
    yields each dir's :class:`_Live` (``None`` for one that does not exist).

    Every dir is checked and held (:func:`_hold_live`) before the first lock
    is taken, so a link refuses with nothing locked; after the last, each
    held folder must still be the one at its path, or the folder the locks
    and the copy would use is not the live dir any more.
    """
    with contextlib.ExitStack() as stack:
        live = [_hold_live(stack, plan, directory) for _phase, directory in dirs]
        for (phase, directory), held in zip(dirs, live):
            _take(stack, plan, mode, phase, directory, held)
        for held in live:
            if held is not None and held.folder is not None and not held.folder.in_place():
                raise _not_a_folder(held.path, "no longer the folder its lock was taken in "
                                               "(moved, or replaced by a link)")
        yield live


# ---------------------------------------------------------------------------
# Copying a live phase dir
# ---------------------------------------------------------------------------

_READ_FLAGS = (os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_BINARY", 0)
               | getattr(os, "O_CLOEXEC", 0))


def _read_regular(path: str) -> bytes:
    fd = os.open(path, _READ_FLAGS)
    with os.fdopen(fd, "rb") as handle:
        return handle.read()


def _copy_file(data: bytes, info: os.stat_result, destination: Path) -> None:
    ledger_mod.write_file(destination, data, mode=stat.S_IMODE(info.st_mode))
    utime_in_plan_dir(destination, (info.st_atime_ns, info.st_mtime_ns))


def _read_regular_at(name: str, dir_fd: int) -> Optional[bytes]:
    """The bytes of the regular file *name* in the folder *dir_fd*, never
    through a link at the name (``None`` when it is no regular file by now)."""
    fd = os.open(name, _READ_FLAGS | getattr(os, "O_NONBLOCK", 0), dir_fd=dir_fd)
    with os.fdopen(fd, "rb") as handle:
        if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
            return None
        return handle.read()


def _is_link_at(name: str, dir_fd: int) -> bool:
    try:
        return stat.S_ISLNK(os.stat(name, dir_fd=dir_fd, follow_symlinks=False).st_mode)
    except FileNotFoundError:
        return True


def _copy_held(folder: _HeldFolder, target: Path) -> None:
    """:func:`_copy_tree` through the folder held: ``os.fwalk`` from its
    descriptor, every folder and file opened relative to the one above it
    and never through a link, so a folder swapped for a link during the walk
    is not entered."""
    for where, dirnames, filenames, dir_fd in os.fwalk(".", dir_fd=folder.fd,
                                                       follow_symlinks=False):
        dirnames[:] = sorted(d for d in dirnames if not _is_link_at(d, dir_fd))
        for name in sorted(filenames):
            if name.endswith(".lock"):
                continue
            try:
                info = os.stat(name, dir_fd=dir_fd, follow_symlinks=False)
                if not stat.S_ISREG(info.st_mode):
                    continue
                data = _read_regular_at(name, dir_fd)
            except FileNotFoundError:
                continue
            if data is None:
                continue
            _copy_file(data, info, target / os.path.normpath(os.path.join(where, name)))


def _copy_tree(source: Path, target: Path) -> None:
    """Copy every regular file below *source* to the same place below *target*.

    ``*.lock`` files are left out (a lock belongs to the live dir, and a copy
    of one held is meaningless). Links are neither followed nor copied, so
    nothing outside the phase dir lands in the archive (the dir itself is
    never a link: :func:`_hold_live`). Each copy keeps its source's
    permission bits (``.status.json`` is owner-only) and its modification
    time, which the archive's readers date a file by when it carries no
    stamp of its own (``write_batch_report.json``). A file that disappears
    during the walk is passed over. Linux and macOS walk the folder held
    instead (:func:`_copy_held`).
    """
    for folder, dirnames, filenames in os.walk(source, followlinks=False):
        dirnames[:] = sorted(d for d in dirnames if not os.path.islink(os.path.join(folder, d)))
        for name in sorted(filenames):
            if name.endswith(".lock"):
                continue
            path = os.path.join(folder, name)
            try:
                info = os.lstat(path)
                if not stat.S_ISREG(info.st_mode):
                    continue
                data = _read_regular(path)
            except FileNotFoundError:
                continue
            _copy_file(data, info, target / Path(os.path.relpath(path, source)))


def _copy_live(live: Optional[_Live], target: Path) -> None:
    """Copy the live dir *live* (nothing for ``None``) below *target*."""
    if live is None:
        return
    if live.folder is not None:
        _copy_held(live.folder, target)
    else:
        _copy_tree(live.path, target)


# ---------------------------------------------------------------------------
# records.json: the stage's own state.json entries
# ---------------------------------------------------------------------------

def _dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def _stamp_of(value: Any) -> Optional[datetime]:
    """A stamp from a ``phases_completed`` / ``phases_skipped`` value (a string,
    or an object with ``skipped_at``)."""
    if isinstance(value, dict):
        value = value.get("skipped_at") or value.get("completed_at")
    return _parse_completion_time(value)


def _batches(document: Mapping[str, Any]) -> List[Dict[str, Any]]:
    tasks = document.get("batches") or document.get("tasks")
    return [t for t in _list(tasks) if isinstance(t, dict)]


def _batch_stamp(batches: Sequence[Mapping[str, Any]]) -> str:
    for batch in batches:
        stamp = str(_dict(batch.get("inputs")).get("grouped_sha256") or "")
        if stamp:
            return stamp
    return ""


def extract_records(state: Mapping[str, Any], names: Phases, apply_dir: Path,
                    status: Mapping[str, Any], grouped_sha256: str) -> Dict[str, Any]:
    """The stage's ``records.json``, from the live ``state.json`` (*state*)
    and the stage's copied apply dir (*apply_dir*), at close-out.

    * ``processed``: the ``processed_<apply dir>`` entries recorded after
      the stage's review completed whose ``details.grouped_sha256`` is the
      stage's ``grouped.json`` hash, or, for an unstamped entry, whose item
      is one of the run's items. The time window comes first: group ids are
      content hashes, so a later stage whose findings repeat an earlier
      stage's word for word has the same ``grouped.json`` hash, and only the
      date tells the earlier stage's entries from its own. The run's items
      are ``write_tasks.json``'s ``native_run.items`` and its batches'
      ``expected_ids``, when that file is this review's (its batches' stamp
      is the stage's hash, and it was not emitted before the review
      completed); an entry older than ``native_run.started_at`` is an
      earlier run's (instructions/improve-plan.md, "Report"). An undated
      entry is kept, as every review-cycle window keeps one.
    * ``human_decisions``: the ``human_decisions_<apply dir>`` entries
      recorded after the stage's review completed (judge records carry no
      ``grouped_sha256``; each stage has a fresh review, so the window is
      unambiguous). An undated one is kept.
    * ``phases_completed`` / ``phases_skipped``: the review's and the apply's.
    * ``scope_policy``: the review round's record (its deferrals included).
    * ``batches`` / ``files_by_task``: the run's batches (task id, items,
      declared files) and, from a ``write_batch_report.json`` of this review
      cycle, the files each finished or partly applied batch changed.
    * ``reused_items``: from that report, the processed items of each batch
      an earlier stage ran and this stage's apply reused without dispatching
      it (:func:`_reused_row`), which the time window cannot tell from this
      stage's own (``cascade_ledger.reused_items``).
    * ``nothing_to_apply``: the apply handed out no item of this review.
    """
    completed = _dict(state.get("phases_completed"))
    skipped = _dict(state.get("phases_skipped"))
    review_done = _stamp_of(completed.get(names.review_phase))
    since = review_done or _parse_completion_time(status.get("started_at"))

    document = _dict(read_json(apply_dir / _WRITE_TASKS))
    batches = _batches(document)
    run = _dict(document.get("native_run"))
    stamp = _batch_stamp(batches)
    emitted_before = predates_review(_parse_completion_time(run.get("emitted_at")),
                                     review_done)
    if not batches:
        current = False
    elif stamp and grouped_sha256:
        current = stamp == grouped_sha256 and not emitted_before
    else:
        current = not emitted_before
    items: Dict[str, None] = {}
    started: Optional[datetime] = None
    if current:
        for item in _list(run.get("items")):
            if str(item):
                items.setdefault(str(item), None)
        for batch in batches:
            for item in _list(batch.get("expected_ids")):
                if str(item):
                    items.setdefault(str(item), None)
        started = _parse_completion_time(run.get("started_at"))

    processed: Dict[str, Any] = {}
    for item, entry in sorted(_dict(state.get(f"processed_{names.apply_dir}")).items()):
        if not isinstance(entry, dict):
            continue
        written = _parse_completion_time(entry.get("timestamp"))
        if predates_review(written, review_done):
            continue
        if started is not None and written is not None and written < started:
            continue
        recorded = str(_dict(entry.get("details")).get("grouped_sha256") or "")
        if recorded and grouped_sha256:
            keep = recorded == grouped_sha256
        else:
            keep = str(item) in items
        if keep:
            processed[str(item)] = entry

    decisions: Dict[str, Any] = {}
    for item, entry in sorted(_dict(state.get(f"human_decisions_{names.apply_dir}")).items()):
        if isinstance(entry, dict) and not predates_review(
                _parse_completion_time(entry.get("timestamp")), since):
            decisions[str(item)] = entry

    files_by_task: Dict[str, List[str]] = {}
    reused: Dict[str, None] = {}
    if current:
        # Imported here: batch_ledger is a heavy module the counters never need.
        from .batch_ledger import BatchLedger, touched_files

        report = BatchLedger(apply_dir)
        rows = report.rows()
        if rows is not None and not predates_review(report.written_at(), review_done):
            for row in rows:
                if isinstance(row, dict) and _reused_row(row, apply_dir, review_done):
                    for item in _list(row.get("expected_ids")):
                        if str(item) in processed:
                            reused.setdefault(str(item), None)
                if isinstance(row, dict) and row.get("task_id"):
                    touched = touched_files([row], include_partial=True)
                    if touched:
                        files_by_task.setdefault(str(row["task_id"]), [])
                        for path in touched:
                            if path not in files_by_task[str(row["task_id"])]:
                                files_by_task[str(row["task_id"])].append(path)

    scope = _dict(state.get("scope_policy")).get(names.review_phase)
    return {
        "schema_version": RECORDS_SCHEMA_VERSION,
        "mode": names.mode,
        "review_phase": names.review_phase,
        "apply_phase": names.apply_phase,
        "apply_dir": names.apply_dir,
        "grouped_sha256": grouped_sha256,
        "processed": processed,
        "human_decisions": decisions,
        "phases_completed": {p: completed[p] for p in (names.review_phase, names.apply_phase)
                             if p in completed},
        "phases_skipped": {p: skipped[p] for p in (names.review_phase, names.apply_phase)
                           if p in skipped},
        "scope_policy": scope if isinstance(scope, dict) else None,
        "run_items": list(items),
        "batches": [
            {"task_id": str(b.get("task_id") or ""),
             "expected_ids": [str(i) for i in _list(b.get("expected_ids")) if str(i)],
             "declared_files": [str(p) for p in _list(b.get("declared_files")) if str(p)]}
            for b in batches
        ] if current else [],
        "files_by_task": files_by_task,
        "reused_items": sorted(reused),
        "nothing_to_apply": not items and not processed,
    }


def _reused_row(row: Mapping[str, Any], apply_dir: Path,
                review_done: Optional[datetime]) -> bool:
    """Whether a ``write_batch_report.json`` row is a batch an earlier stage ran, reused here.

    The scheduler's resume skip marks a batch whose result file it found
    already complete ``skipped`` (``batch_ledger.VERDICT_FIELDS``). Within
    one stage, a resume's skip of a batch the stage's own earlier run
    dispatched is replaced by that run's row (``from_earlier_run``, without
    ``skipped``), so a ``skipped`` row is a result no run of this stage
    produced. As a guard for a resume whose earlier run left no report (a
    killed run), a result file written after this stage's review completed
    is this stage's own; one that cannot be read keeps the marker's word.
    """
    if not row.get("skipped"):
        return False
    output = row.get("output_path")
    if not isinstance(output, str) or not output or review_done is None:
        return True
    try:
        written = datetime.fromtimestamp(
            os.stat(apply_dir / os.path.basename(output)).st_mtime)
    except OSError:
        return True
    return predates_review(written, review_done)


def files_touched(records: Mapping[str, Any]) -> List[str]:
    """improve-code: the files the stage's apply changed, in first-seen order.

    From ``write_batch_report.json`` where the stage has one (each finished
    or partly applied batch's verified ``files_touched``), else the declared
    files of every batch that applied an item (the native leg writes no
    report).
    """
    by_task = _dict(records.get("files_by_task"))
    files: List[str] = []
    if by_task:
        for paths in by_task.values():
            for path in _list(paths):
                if str(path) and str(path) not in files:
                    files.append(str(path))
        return files
    applied = {item for item, entry in _dict(records.get("processed")).items()
               if isinstance(entry, dict) and entry.get("status") == "applied"}
    tasks = {str(_dict(entry.get("details")).get("task_id") or "")
             for item, entry in _dict(records.get("processed")).items()
             if item in applied and isinstance(entry, dict)}
    for batch in _list(records.get("batches")):
        if not isinstance(batch, dict):
            continue
        if batch.get("task_id") in tasks or applied & set(_list(batch.get("expected_ids"))):
            for path in _list(batch.get("declared_files")):
                if str(path) and str(path) not in files:
                    files.append(str(path))
    return files


# ---------------------------------------------------------------------------
# close_out
# ---------------------------------------------------------------------------

def _read_state(mode: str, path: Path) -> Dict[str, Any]:
    """``state.json`` read as the composite reads it; ``{}`` with no file;
    a file it cannot read is :class:`ArchiveRefusal` (exit 3)."""
    # Imported here: improve_workflow imports the cascade core, which imports this module.
    from . import improve_workflow as iw

    try:
        document = iw.read_state_document(path)
    except iw.StateReadError as exc:
        raise ArchiveRefusal(iw.state_read_error_line(mode, exc)) from exc
    return upgrade_legacy(document) if document is not None else {}


def _plan_before(cascade_dir: Path, stage: int) -> bytes:
    """The stage's frozen ``plan.before.md``, its manifest verified."""
    manifest = ledger_mod.stage_dir(cascade_dir, stage) / ledger_mod.INPUTS / provenance.MANIFEST_NAME
    try:
        doc = provenance.load_manifest(manifest)
    except provenance.CascadeProvenanceError as exc:
        raise ArchiveRefusal(provenance.error_line(exc)) from exc
    if provenance.PLAN_BEFORE not in doc.get("files", {}):
        raise ArchiveRefusal(
            f"ERROR: the cascade stage's manifest {manifest} lists no "
            f"{provenance.PLAN_BEFORE}, so the stage's diff cannot be written; "
            "nothing was archived.")
    return (manifest.parent / provenance.PLAN_BEFORE).read_bytes()


def _build(partial: Path, *, plan: Path, names: Phases, out: Path, cascade_dir: Path,
           cascade_id: str, stage: int, model: str, round_id: Optional[str],
           review: Optional[_Live], apply: Optional[_Live]) -> None:
    """Fill ``artifacts.partial/`` from the held live dirs *review* and
    *apply* and write its ``.complete.json`` last."""
    _copy_live(review, partial / names.review_dir)
    _copy_live(apply, partial / names.apply_dir)
    state = _read_state(names.mode, out / _STATE)
    status = _dict(read_json(partial / names.review_dir / _STATUS))
    grouped_sha256 = ledger_mod.grouped_hash(partial / names.review_dir / "grouped.json")
    records = extract_records(state, names, partial / names.apply_dir, status, grouped_sha256)
    ledger_mod.write_file(partial / RECORDS_NAME,
                          json.dumps(records, indent=2, sort_keys=True) + "\n")
    if names.mode == "improve-plan":
        try:
            after = plan.read_bytes()
        except OSError as exc:
            raise ArchiveRefusal(
                f"ERROR: cannot read the plan {plan} ({exc.strerror or exc}) to archive "
                f"cascade stage {stage}; nothing was archived.") from exc
        before = _plan_before(cascade_dir, stage)
        ledger_mod.write_file(partial / PLAN_AFTER, after)
        ledger_mod.write_file(partial / STAGE_DIFF, ledger_mod.unified_diff(
            before.decode("utf-8", errors="replace"), after.decode("utf-8", errors="replace"),
            before_name=f"a/{provenance.PLAN_BEFORE}", after_name=f"b/{PLAN_AFTER}"))
    else:
        touched = files_touched(records)
        ledger_mod.write_file(partial / FILES_TOUCHED,
                              "".join(f"{path}\n" for path in touched))
    mark = {
        "schema_version": COMPLETE_SCHEMA_VERSION,
        "cascade_id": str(cascade_id),
        "mode": names.mode,
        "stage": int(stage),
        "model": str(model),
        "round_id": round_id or status.get("round_id"),
        "grouped_sha256": grouped_sha256,
        "review_dir": names.review_dir,
        "apply_dir": names.apply_dir,
        "published_at": local_iso(),
        "files": ledger_mod.hash_tree(partial),
    }
    ledger_mod.write_file(partial / COMPLETE_NAME,
                          json.dumps(mark, indent=2, sort_keys=True) + "\n")


def _stage_started(cascade_dir: Path, stage: int) -> Optional[str]:
    """Stage *stage*'s ``started_at`` in the cascade's ``record.json``, or
    ``None`` (no record, no stamp). Set once, when the stage is handed out,
    so a retry fan-out does not move it, as it moves the review's own
    ``started_at``."""
    record = _dict(read_json(Path(cascade_dir) / ledger_mod.RECORD_NAME))
    for entry in _list(record.get("stages")):
        if isinstance(entry, dict) and entry.get("index") == int(stage):
            value = entry.get("started_at")
            return value if isinstance(value, str) and value else None
    return None


def _published(artifacts: Path, *, cascade_id: str, stage: int, mode: str,
               cascade_dir: Path) -> Dict[str, Any]:
    mark = ledger_mod.read_complete(artifacts, cascade_id=cascade_id, stage=stage)
    if mark.get("mode") != mode:
        raise ArchiveRefusal(
            f"ERROR: the cascade archive {artifacts} is a {mark.get('mode')} stage's, "
            f"not {mode}'s, so it cannot be read as this stage's. Nothing was changed.")
    return stage_counts(artifacts, mode, started_at=_stage_started(cascade_dir, stage))


def close_out(*, plan_path: Path, mode: str, cascade_dir: Path, cascade_id: str,
              stage: int, model: str, round_id: Optional[str],
              recheck: Callable[[], bool]) -> Dict[str, Any]:
    """Archive stage *stage* and return its counts (:func:`stage_counts` of
    the published dir).

    Recovery, by what is on disk: a published ``artifacts/`` whose
    ``.complete.json`` names this cascade and stage gives its counts with no
    copy and no lock; one whose mark is missing, invalid or mismatched is
    :class:`ArchiveRefusal` naming it; an ``artifacts.partial/`` is removed and
    the close-out redone. Otherwise the run dir, review dir and apply dir are
    checked to be real folders, not links, up to the plan's output dir (a
    link is :class:`ArchiveRefusal` with nothing locked or copied) and held,
    their locks are taken in that order, *recheck* is called (``False``:
    the locks are released and :class:`CloseOutRaced` raised), the archive is
    built in ``artifacts.partial/`` with ``.complete.json`` last, renamed to
    ``artifacts/``, and the locks released. A lock a live run holds is
    :class:`ArchiveRefusal` with ``improve_workflow.live_owner_refusal``'s
    text; a lock is never broken. ``record.json`` is the caller's to update.
    """
    names = ledger_mod.phases(mode)
    plan = Path(os.path.abspath(str(plan_path)))
    out = output_dir_path(plan)
    cascade_dir = Path(os.path.abspath(str(cascade_dir)))
    ledger_mod.anchor_cascade_dir(cascade_dir)
    home = ledger_mod.stage_dir(cascade_dir, stage)
    artifacts = home / ARTIFACTS
    if os.path.lexists(artifacts):
        return _published(artifacts, cascade_id=cascade_id, stage=stage, mode=names.mode,
                          cascade_dir=cascade_dir)
    dirs = [
        (names.run_phase, out / names.run_phase),
        (names.review_phase, out / names.review_dir),
        (names.apply_phase, out / names.apply_dir),
    ]
    with _locked(plan, names.mode, dirs) as live:
        if not recheck():
            raise CloseOutRaced(
                f"cascade stage {stage}: the review or apply on record changed before "
                "its close-out took the locks")
        if os.path.lexists(artifacts):
            return _published(artifacts, cascade_id=cascade_id, stage=stage, mode=names.mode,
                              cascade_dir=cascade_dir)
        partial = home / PARTIAL
        try:
            if os.path.lexists(partial):
                ledger_mod.remove_tree(partial)
            _build(partial, plan=plan, names=names, out=out, cascade_dir=cascade_dir,
                   cascade_id=cascade_id, stage=stage, model=model, round_id=round_id,
                   review=live[1], apply=live[2])
            rename_in_plan_dir(partial, ARTIFACTS)
        except OSError as exc:
            # A refused containment check (a link swapped in below the plan's
            # directory) is an OSError too: never written through, never retried here.
            raise ArchiveRefusal(
                f"ERROR: cascade stage {stage}'s archive could not be written in "
                f"{home} ({exc}). Nothing was published; the next run redoes the "
                "close-out from the live phase dirs, which are untouched.") from exc
    return stage_counts(artifacts, names.mode, started_at=_stage_started(cascade_dir, stage))


def published_counts(cascade_dir: Path, stage: int, cascade_id: str) -> Optional[Dict[str, Any]]:
    """Counts from ``stage-<stage>/artifacts/`` when its ``.complete.json``
    matches *cascade_id* and *stage*, else ``None`` (no archive, or one that
    does not check out). Read-only."""
    artifacts = ledger_mod.stage_dir(cascade_dir, stage) / ARTIFACTS
    if not artifacts.is_dir():
        return None
    try:
        mark = ledger_mod.read_complete(artifacts, cascade_id=cascade_id, stage=stage)
    except ArchiveRefusal:
        return None
    return stage_counts(artifacts, str(mark["mode"]),
                        started_at=_stage_started(cascade_dir, stage))


# ---------------------------------------------------------------------------
# Counting
# ---------------------------------------------------------------------------

def _int(value: Any) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) else 0


def _time_s(status: Mapping[str, Any], records: Mapping[str, Any],
            names: Phases, started_at: Optional[str] = None) -> Optional[float]:
    """Seconds from the stage's start to its last recorded finish (the
    apply's completion or skip, else the review's completion); ``None`` when
    either end is not recorded.

    The start is the record's ``stages[k].started_at`` (*started_at*), set
    once when the stage is handed out; only without one (an archive read with
    no record) the review round's ``.status.json`` ``started_at``, which
    every retry fan-out resets, so a retried stage would undercount."""
    started = (_parse_completion_time(started_at)
               or _parse_completion_time(status.get("started_at")))
    completed = _dict(records.get("phases_completed"))
    skipped = _dict(records.get("phases_skipped"))
    ends = [stamp for stamp in (
        _stamp_of(completed.get(names.apply_phase)),
        _stamp_of(skipped.get(names.apply_phase)),
        _stamp_of(completed.get(names.review_phase)),
    ) if stamp is not None]
    if started is None or not ends or max(ends) < started:
        return None
    return round((max(ends) - started).total_seconds(), 1)


def _cost(status: Mapping[str, Any]) -> Optional[str]:
    """The reviewer's cost as the review recorded it (``.status.json``
    ``usage``, per model ``cost_usd``: the CLI's own estimate, hence
    ``est.``), or ``None`` when no model reported one. Validation, the judge
    and the apply run on the host and are not metered. ``None`` is printed
    ``not recorded``, never ``$0``."""
    costs = [
        entry.get("cost_usd") for entry in _dict(status.get("usage")).values()
        if isinstance(entry, dict)
    ]
    numbers = [c for c in costs if isinstance(c, (int, float)) and not isinstance(c, bool)]
    if not numbers:
        return None
    return f"${sum(numbers):.2f} est."


def stage_counts(artifacts_dir: Path, mode: str, *,
                 started_at: Optional[str] = None) -> Dict[str, Any]:
    """A published stage's counts (:data:`COUNT_KEYS`), from its archive
    (and, for ``time_s``, the stage's *started_at* from ``record.json``).

    These definitions are the cascade's own, not borrowed from either existing
    counter (the native report counts ``applied`` and ``no-op`` as items
    applied; ``status`` counts ``applied`` only):

    * ``findings``: the groups in the archived ``grouped.json``;
    * ``valid`` / ``invalid`` / ``needs_decision``: the review's
      ``.status.json`` ``validation_counts``; with none, the archived
      ``validation.json`` records by status (0 each when it has none);
    * ``reraises``: archived ``validation.json`` records that carry a
      non-empty ``reraise_of``;
    * ``applied`` / ``no_op`` / ``declined`` / ``skipped_by_user``: the
      ``records.json`` processed entries by status ``applied``, ``no-op``,
      ``declined``, ``skipped`` (the table shows declined plus skipped, as
      ``Declined (n skipped)``); an ``applied`` item whose batch the apply
      reused without dispatching it (``cascade_ledger.reused_items``) counts as
      ``no_op``;
    * ``held_back``: the scope deferrals of the review round recorded in
      ``records.json`` (``scope_policy.deferrals``: valid findings a
      ``preserve`` policy did not apply);
    * ``judge_approved`` / ``judge_salvaged`` / ``judge_skipped``: the stage's
      judge decisions (``batch_context.decision_source``
      ``judge_auto_decide`` by ``decision``, or ``judge_auto_decide_salvage``);
    * ``nothing_to_apply``: the apply handed out no item of this review;
    * ``time_s`` and ``cost``: see :func:`_time_s` and :func:`_cost`.
    """
    names = ledger_mod.phases(mode)
    root = Path(artifacts_dir)
    review = root / names.review_dir
    grouped = _dict(read_json(review / "grouped.json"))
    status = _dict(read_json(review / _STATUS))
    validation = [r for r in _list(_dict(read_json(review / "validation.json")).get("groups"))
                  if isinstance(r, dict)]
    records = _dict(read_json(root / RECORDS_NAME))
    counts: Dict[str, Any] = {key: 0 for key in COUNT_KEYS}
    counts["findings"] = len([g for g in _list(grouped.get("groups")) if isinstance(g, dict)])
    recorded = _dict(status.get("validation_counts"))
    if recorded:
        counts["valid"] = _int(recorded.get("valid"))
        counts["invalid"] = _int(recorded.get("invalid"))
        counts["needs_decision"] = _int(recorded.get("needs_human_decision"))
    else:
        for record in validation:
            key = {"valid": "valid", "invalid": "invalid",
                   "needs-human-decision": "needs_decision"}.get(str(record.get("status")))
            if key:
                counts[key] += 1
    counts["reraises"] = sum(1 for r in validation if str(r.get("reraise_of") or "").strip())
    reused = ledger_mod.reused_items(records)
    for item, entry in _dict(records.get("processed")).items():
        if not isinstance(entry, dict):
            continue
        key = {"applied": "applied", "no-op": "no_op", "declined": "declined",
               "skipped": "skipped_by_user"}.get(str(entry.get("status")))
        if key == "applied" and str(item) in reused:
            key = "no_op"
        if key:
            counts[key] += 1
    counts["held_back"] = sum(
        1 for d in _list(_dict(records.get("scope_policy")).get("deferrals"))
        if isinstance(d, dict))
    for entry in _dict(records.get("human_decisions")).values():
        if not isinstance(entry, dict):
            continue
        source = canonical_value(_dict(entry.get("batch_context")).get("decision_source"))
        decision = canonical_value(entry.get("decision"))
        if source == JUDGE_SALVAGE_SOURCE:
            counts["judge_salvaged"] += 1
        elif source == JUDGE_SOURCE and decision == "approved":
            counts["judge_approved"] += 1
        elif source == JUDGE_SOURCE and decision == "skipped":
            counts["judge_skipped"] += 1
    counts["nothing_to_apply"] = bool(records.get("nothing_to_apply"))
    counts["time_s"] = _time_s(status, records, names, started_at)
    counts["cost"] = _cost(status)
    return counts


# ---------------------------------------------------------------------------
# The per-round table
# ---------------------------------------------------------------------------

TABLE_HEADER = (
    "| Stage | Model | Findings | Valid | Invalid | Needs decision | Re-raises "
    "| Applied | No-op | Declined | Held back | Judge (A/V/S) | Time | Cost |"
)
TABLE_RULE = "| " + " | ".join(["---"] * 14) + " |"

TABLE_NOTES = (
    "Applied counts items whose edits this round's apply made; No-op counts items "
    "the apply found already addressed, a finding that repeats an earlier round's "
    "word for word included (the apply reused that round's batch and dispatched "
    "nothing). The native report's \"items applied\" is Applied + No-op.",
    "Declined counts the items their batch declined, plus the ones skipped at your "
    "request, shown as (n skipped). Judge (A/V/S): needs-human-decision items the "
    "judge approved, salvaged and skipped. Re-raises: findings the validator marked "
    "as repeating an earlier round's rejected entry (— for a round with no earlier "
    "rounds).",
    "Held back counts valid findings the scope policy (preserve) kept out of the "
    "apply. Only the last round's can still be applied: once the cascade is "
    "finished, run the mode again without --cascade with --scope-policy expand. "
    "Earlier rounds' stay in the ledger as held back.",
    "Time is the round's wall-clock span from hand-out to close-out, retries "
    "included, and so is the idle time of a round that stopped and was resumed "
    "later. Cost is the "
    "reviewer's recorded estimate (validation and apply run on the host and are not "
    "metered); \"not recorded\" means no figure was reported, never zero.",
)


def _cell(text: Any) -> str:
    return str(text).replace("|", "\\|")


def _time_cell(seconds: Any) -> str:
    if not isinstance(seconds, (int, float)) or isinstance(seconds, bool):
        return NOT_RECORDED
    return format_duration(int(round(seconds * 1000)))


def _row(index: int, model: str, counts: Mapping[str, Any], *, ledger_before: bool) -> str:
    if counts.get("nothing_to_apply"):
        applied = "0 (nothing to apply)"
    else:
        applied = str(_int(counts.get("applied")))
    declined = _int(counts.get("declined")) + _int(counts.get("skipped_by_user"))
    skipped = _int(counts.get("skipped_by_user"))
    declined_cell = f"{declined} ({skipped} skipped)" if skipped else str(declined)
    cells = [
        str(index), _cell(model),
        str(_int(counts.get("findings"))), str(_int(counts.get("valid"))),
        str(_int(counts.get("invalid"))), str(_int(counts.get("needs_decision"))),
        str(_int(counts.get("reraises"))) if ledger_before else "—",
        applied, str(_int(counts.get("no_op"))), declined_cell,
        str(_int(counts.get("held_back"))),
        f"{_int(counts.get('judge_approved'))}/{_int(counts.get('judge_salvaged'))}/"
        f"{_int(counts.get('judge_skipped'))}",
        _time_cell(counts.get("time_s")),
        _cell(counts.get("cost")) if counts.get("cost") else NOT_RECORDED,
    ]
    return "| " + " | ".join(cells) + " |"


def _short_row(index: int, model: str, text: str) -> str:
    return "| " + " | ".join([str(index), _cell(model), _cell(text)] + [""] * 11) + " |"


def _record_time_s(entry: Mapping[str, Any]) -> Optional[float]:
    """A closed stage's seconds in ``record.json``: ``started_at`` (set when
    the stage was handed out) to ``finished_at`` (its close-out), a wall-clock
    span that includes the idle time of a stage stopped and resumed later
    (the table's notes say so); ``None`` when either is missing or they are
    out of order."""
    started = _parse_completion_time(entry.get("started_at"))
    finished = _parse_completion_time(entry.get("finished_at"))
    if started is None or finished is None or finished < started:
        return None
    return round((finished - started).total_seconds(), 1)


def render_summary(cascade_dir: Path, record: Dict[str, Any]) -> str:
    """Write ``summary.md`` (the per-round table) and the top-level
    ``ledger.md`` view in *cascade_dir*; return the table with its notes.

    Each closed stage's row is read from its ``artifacts/`` only
    (:func:`published_counts`; the record's ``counts`` stand in when an
    archive cannot be read). A skipped stage is one row reading
    ``skipped: <reason>``; a stage not closed yet reads ``in progress`` or
    ``not started``. An apply that handed out no item prints ``0`` items with
    ``(nothing to apply)``. A closed stage's Time is the record's own
    ``started_at`` to ``finished_at`` (:func:`_record_time_s`), else the
    counts' ``time_s``. ``ledger.md`` is every ledger entry up to the
    last closed stage (empty before one). Both files are views: nothing
    points into them and no prompt reads them.
    """
    cascade_dir = Path(os.path.abspath(str(cascade_dir)))
    ledger_mod.anchor_cascade_dir(cascade_dir)
    cascade_id = str(record.get("cascade_id") or "")
    mode = str(record.get("mode") or "")
    stages = sorted((s for s in _list(record.get("stages")) if isinstance(s, dict)),
                    key=lambda s: _int(s.get("index")))
    rows: List[str] = []
    ledger_before = False
    last_closed = 0
    for entry in stages:
        index = _int(entry.get("index"))
        model = str(entry.get("model") or "")
        state = entry.get("state")
        if state == "skipped":
            reason = clip(entry.get("skip_reason") or "no reason recorded", 200)
            rows.append(_short_row(index, model, f"skipped: {reason}"))
            continue
        if state != "done":
            rows.append(_short_row(index, model,
                                   "in progress" if state == "running" else "not started"))
            continue
        counts = published_counts(cascade_dir, index, cascade_id) if cascade_id else None
        if counts is None and isinstance(entry.get("counts"), dict):
            counts = entry["counts"]
        seconds = _record_time_s(entry)
        if counts is not None and seconds is not None:
            counts = {**counts, "time_s": seconds}
        if counts is None:
            rows.append(_short_row(index, model, "done (archive not readable)"))
        else:
            rows.append(_row(index, model, counts, ledger_before=ledger_before))
        if (ledger_mod.stage_dir(cascade_dir, index) / ARTIFACTS).is_dir():
            ledger_before = True
            last_closed = index
    table = "\n".join([TABLE_HEADER, TABLE_RULE, *rows])
    text = table + "\n\n" + "\n\n".join(TABLE_NOTES) + "\n"
    state = record.get("state") or "running"
    heading = (f"# Cascade summary\n\nCascade `{cascade_id}` ({mode}), "
               f"{len(stages)} stage{'' if len(stages) == 1 else 's'}, state: {state}.\n\n")
    ledger_mod.write_file(cascade_dir / "summary.md", heading + text)
    ledger_text = ""
    if last_closed and mode in ledger_mod.MODES:
        ledger_text = ledger_mod.render_full(ledger_mod.build_ledger(
            cascade_dir, last_closed, mode, cascade_id=cascade_id or None))
    ledger_mod.write_file(cascade_dir / "ledger.md", ledger_text)
    return text
