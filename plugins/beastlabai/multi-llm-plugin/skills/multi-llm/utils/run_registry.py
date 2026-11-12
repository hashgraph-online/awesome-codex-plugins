#!/usr/bin/env python3
"""The cross-plan registry of live detached runs.

``{phase}/.lock`` makes two runs on the *same* phase dir impossible, but nothing
in it bounds runs across phases and plans — a retrying shim, or a poll loop that
mistakes exit 2 for "launch again", can fork them without limit, each spawning
provider CLIs. So every detached run drops one small JSON file at
``{project_root}/.multi-llm/runs/<run_id>.json`` in the same step it takes the
lock, and removes it on any terminal state. Two things read it:

* ``--detach`` counts live entries before it forks and refuses above
  ``MULTI_LLM_MAX_DETACHED`` (default 4) — in the foreground, on the caller's
  terminal, before anything daemonizes.
* ``multi_llm.py util runs [--sweep]`` answers "the machine rebooted — what is
  still running?". A reboot leaves stale registry files and no processes, and one
  sweep reconciles both: close out the record, kill any surviving process-group
  member whose creation time still matches, delete the file, prune anything older
  than a week.

Sweeping is never automatic on launch. It kills things, so it is a verb a caller
runs.
"""

from __future__ import annotations

import json
import os
import stat
import time
from typing import Any, Callable, Dict, List, Optional

from . import process_control
from .atomic_io import atomic_write_text

#: Registry location, relative to the project root.
REGISTRY_RELPATH = os.path.join(".multi-llm", "runs")

#: Entries older than this are pruned by ``--sweep`` even if they were never
#: closed out (a reboot with no process left to probe).
PRUNE_AFTER_DAYS = 7

#: Default ceiling on concurrent detached runs per project.
DEFAULT_MAX_DETACHED = 4

#: Env override for the ceiling, so a CI job or a big machine can raise it
#: without a code change.
MAX_DETACHED_ENV = "MULTI_LLM_MAX_DETACHED"


def max_detached(override: Optional[int] = None) -> int:
    """The configured ceiling: flag beats env beats default."""
    if override is not None:
        return max(int(override), 1)
    raw = os.environ.get(MAX_DETACHED_ENV)
    if raw:
        try:
            return max(int(raw), 1)
        except ValueError:
            pass
    return DEFAULT_MAX_DETACHED


def resolve_project_root(anchor: Optional[str] = None) -> str:
    """The project root a registry lives under.

    The git top-level of *anchor* (a plan file or a directory), falling back to
    the anchor's own directory so a plan outside a repo still gets a registry
    rather than silently sharing one with the CWD.
    """
    anchor = str(anchor) if anchor else os.getcwd()
    try:
        # Imported here to keep run_status, which loads this module, light.
        from .git_utils import get_project_root, get_project_root_from_dir

        if os.path.isdir(anchor):
            root = get_project_root_from_dir(anchor)
        else:
            root = get_project_root(anchor)
        if root:
            return root
    except Exception:
        pass
    return anchor if os.path.isdir(anchor) else (os.path.dirname(anchor) or ".")


def registry_dir(project_root: str) -> str:
    return os.path.join(str(project_root), REGISTRY_RELPATH)


def entry_path(project_root: str, run_id: str) -> str:
    return os.path.join(registry_dir(project_root), f"{run_id}.json")


def write_entry(project_root: str, entry: Dict[str, Any]) -> Optional[str]:
    """Record one live run. Best-effort: a read-only project must not fail a run.

    ``atomic_io``'s write, flushed to disk: the entry is what a sweep after a
    reboot reconciles (docs/development/runtime.md#atomic-file-writes)."""
    directory = registry_dir(project_root)
    path = entry_path(project_root, entry["run_id"])
    try:
        os.makedirs(directory, exist_ok=True)
        # A fresh file each time, as base made one: the current umask, never
        # an earlier entry's mode carried over.
        atomic_write_text(path, json.dumps(entry, indent=2), keep_mode=False)
        return path
    except (OSError, IOError):
        return None


def remove_entry(project_root: str, run_id: str) -> None:
    try:
        os.unlink(entry_path(project_root, run_id))
    except OSError:
        pass


def _nonblocking(path: str, flags: int) -> int:
    return os.open(path, flags | getattr(os, "O_NONBLOCK", 0))


def _read_entry(path: str) -> Any:
    """The JSON an entry file holds, opened without blocking and read only
    when the descriptor is a regular file (``fstat``): a FIFO or a device at
    the name, at a link's end, or swapped in after a listing, is an
    ``OSError``, never a hang (``status_file._open_checkpoint``'s rule)."""
    with open(path, "r", encoding="utf-8", opener=_nonblocking) as f:
        if not stat.S_ISREG(os.fstat(f.fileno()).st_mode):
            raise OSError(f"{path} is not a regular file")
        return json.load(f)


def list_entries(project_root: str) -> List[Dict[str, Any]]:
    """Every registry entry, each annotated with its own file path."""
    directory = registry_dir(project_root)
    entries: List[Dict[str, Any]] = []
    try:
        names = sorted(os.listdir(directory))
    except OSError:
        return entries
    for name in names:
        if not name.endswith(".json"):
            continue
        path = os.path.join(directory, name)
        try:
            data = _read_entry(path)
        except (OSError, IOError, ValueError):
            data = {"run_id": name[:-5], "corrupt": True}
        if isinstance(data, dict):
            data["_path"] = path
            entries.append(data)
    return entries


class UnreadableEntries(OSError):
    """:func:`read_entries_strictly`: registry entries that exist but could
    not be read as an entry (*paths*), so nothing in them can be told."""

    def __init__(self, paths: List[str]):
        super().__init__(f"registry entries that cannot be read: {', '.join(paths)}")
        self.paths = list(paths)


def read_entries_strictly(
    project_root: str, *, except_run_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Every registry entry, each annotated with its own file path, for a
    reader that decides something on what the registry does *not* hold;
    *except_run_id*'s own entry (``<run_id>.json``) is not read at all.

    :func:`list_entries` is for a view: a listing that fails reads as an empty
    registry, and an entry that cannot be read becomes a placeholder with its
    ``run_id`` alone. Here the folder is listed once: ``[]`` only when it does
    not exist, the ``OSError`` of a listing that fails otherwise. An entry
    removed between the listing and its read is gone (its run's teardown was
    confirmed). One that cannot be opened or parsed, is no regular file (a
    FIFO is refused, never waited on) or is no JSON object, raises
    :class:`UnreadableEntries` naming every such entry, after all are read."""
    directory = registry_dir(project_root)
    try:
        names = sorted(os.listdir(directory))
    except FileNotFoundError:
        return []
    entries: List[Dict[str, Any]] = []
    unreadable: List[str] = []
    for name in names:
        if not name.endswith(".json"):
            continue
        if except_run_id and name == f"{except_run_id}.json":
            continue
        path = os.path.join(directory, name)
        try:
            data = _read_entry(path)
        except FileNotFoundError:
            continue
        except (OSError, ValueError):
            data = None
        if not isinstance(data, dict):
            unreadable.append(path)
            continue
        data["_path"] = path
        entries.append(data)
    if unreadable:
        raise UnreadableEntries(unreadable)
    return entries


def verdict_for(entry: Dict[str, Any]) -> str:
    """``alive`` / ``dead`` / ``unknown`` for one entry's recorded identity."""
    return process_control.probe(
        entry.get("pid"), entry.get("process_start_time")
    )


def live_entries(project_root: str) -> List[Dict[str, Any]]:
    """Entries whose recorded process is alive (or unverifiably so).

    ``unknown`` counts as live on purpose: the ceiling exists to stop runaway
    provider spawning, and refusing to count a run we cannot disprove is the safe
    direction.
    """
    return [e for e in list_entries(project_root) if verdict_for(e) != process_control.DEAD]


def find_launch_key(project_root: str, launch_key: str) -> Optional[Dict[str, Any]]:
    """The live entry for a ``(mode, plan, phase[, ask slug])`` key, if any."""
    for entry in live_entries(project_root):
        if entry.get("launch_key") == launch_key:
            return entry
    return None


def _age_days(entry: Dict[str, Any]) -> Optional[float]:
    path = entry.get("_path")
    if not path:
        return None
    try:
        return (time.time() - os.path.getmtime(path)) / 86400.0
    except OSError:
        return None


#: ``cleanup.state`` words that leave a run's processes not confirmed stopped
#: (``detach.CLEANUP_PENDING``, ``detach.CLEANUP_INCOMPLETE``), on a run record
#: and on an entry kept for it.
CLEANUP_OPEN_STATES = ("pending", "incomplete")


def _cleanup_open(entry: Dict[str, Any]) -> bool:
    cleanup = entry.get("cleanup") if isinstance(entry, dict) else None
    return isinstance(cleanup, dict) and cleanup.get("state") in CLEANUP_OPEN_STATES


def entry_cleanup_open(project_root: str, run_id: str) -> bool:
    """Does run *run_id*'s entry carry a cleanup not confirmed? Never raises."""
    try:
        return _cleanup_open(_read_entry(entry_path(project_root, run_id)))
    except (OSError, ValueError, TypeError):
        return False


def mark_cleanup(
    project_root: str, run_id: str, cleanup: Dict[str, Any], identity: Dict[str, Any],
    *, phase_dir: Optional[str] = None,
) -> None:
    """Keep run *run_id*'s entry, carrying *cleanup*: the recovery state of a
    teardown that could not confirm every process stopped, held here rather
    than only in the run's phase record, which a new run may claim and
    replace. An entry already gone is written again from *identity* (the run
    record). Best-effort, like :func:`write_entry`."""
    entry: Dict[str, Any] = {}
    try:
        loaded = _read_entry(entry_path(project_root, run_id))
        if isinstance(loaded, dict):
            entry = loaded
    except (OSError, ValueError):
        pass
    if not entry:
        entry = {key: identity.get(key) for key in (
            "pid", "process_start_time", "pgid", "plan_file", "mode")}
    entry.pop("_path", None)
    entry["run_id"] = run_id
    if phase_dir and not entry.get("phase_dir"):
        entry["phase_dir"] = str(phase_dir)
    entry["cleanup"] = dict(cleanup)
    write_entry(project_root, entry)


#: The run-lifecycle owner's close-out of one entry's run
#: (``detach.close_out_entry``): ``(entry, *, reason, project_root, kill,
#: [killed])`` -> the outcome of its kill (``run.cleanup``'s shape) or ``None``.
CloseOutEntry = Callable[..., Optional[Dict[str, Any]]]

#: The run-lifecycle owner's kill of one entry's recorded processes
#: (``detach.stop_recorded_run``): ``(phase_dir, entry, *, start_time)`` -> the
#: kill verdict.
StopRecordedRun = Callable[..., Optional[str]]


def sweep(
    project_root: str,
    *,
    close_out_entry: CloseOutEntry,
    stop_recorded_run: StopRecordedRun,
    kill: bool = True,
    prune_after_days: int = PRUNE_AFTER_DAYS,
) -> List[Dict[str, Any]]:
    """Close out what earlier sessions left behind. Returns one row per entry.

    The close-out and the kill are the run-lifecycle owner's
    (``detach.close_out_entry``, ``detach.stop_recorded_run``), passed in by
    the caller (``run_sweep.sweep``, behind ``util runs --sweep``): the
    registry sits below ``detach`` and imports nothing above its layer
    (docs/development/dispatcher.md#import-layers).

    Each row carries ``run_id``, the liveness ``verdict``, the ``action`` taken
    (``kept`` / ``closed`` / ``pruned`` / ``killed`` / ``needs_attention``), the
    ``kill_verdict`` of the kill this sweep made for the entry (``None`` when
    it made none) and the entry itself, so the CLI and a test can assert on
    the same data.

    An entry whose worker is gone, or that carries a cleanup not confirmed
    (``cleanup``, :func:`mark_cleanup`), is closed out from its own
    identities (``detach.close_out_entry``): never from its phase dir's
    current record, which may be another run's by now.

    ``needs_attention``: not every process of the run could be confirmed
    stopped (its kill ``survived``, was ``unresolved`` or ``skipped``, or
    raised). The entry is kept, carrying that outcome, so the next sweep tries
    again, and ``util runs --sweep`` exits 3.
    """
    rows: List[Dict[str, Any]] = []
    for entry in list_entries(project_root):
        verdict = verdict_for(entry)
        age = _age_days(entry)
        action = "kept"
        kill_verdict: Optional[str] = None
        if verdict == process_control.DEAD or _cleanup_open(entry):
            action = "closed"
            outcome = _close_out_entry(entry, project_root, close_out_entry, kill=kill)
            if outcome is not None:
                kill_verdict = outcome.get("verdict")
                if outcome.get("state") in CLEANUP_OPEN_STATES:
                    action = NEEDS_ATTENTION
            if action != NEEDS_ATTENTION:
                remove_entry(project_root, entry.get("run_id", ""))
        elif age is not None and age > prune_after_days:
            action = "pruned"
            if kill:
                # `skipped` is a real outcome here: a week-old entry whose
                # identity probe came back `unknown` (the /proc or ps read
                # failed) is a pid we cannot corroborate, and signalling its
                # process group would hit whatever recycled that pid. It is
                # not reported as killed, nor as stopped. On Windows the run's
                # named job is the kill when it opens
                # (`process_control.kill_run_tree`).
                kill_verdict = _kill_entry(entry, stop_recorded_run)
                if kill_verdict == "killed":
                    action = "killed"
            # Then the close-out, with what the prune's kill found: of the run's
            # own open record, as it always was, else kept in the entry while
            # it is unconfirmed. One kill: a second one's verdict would stand
            # for what only this one saw (`detach.close_out_entry`).
            outcome = _close_out_entry(entry, project_root, close_out_entry, kill=False,
                                       **({"killed": kill_verdict} if kill else {}))
            if outcome is not None and outcome.get("state") in CLEANUP_OPEN_STATES:
                action = NEEDS_ATTENTION
            else:
                remove_entry(project_root, entry.get("run_id", ""))
        rows.append(
            {"run_id": entry.get("run_id"), "verdict": verdict, "action": action,
             "kill_verdict": kill_verdict, "age_days": age, "entry": entry}
        )
    return rows


#: :func:`sweep`'s action for a run whose processes are not all confirmed stopped.
NEEDS_ATTENTION = "needs_attention"

def _kill_entry(entry: Dict[str, Any], stop_recorded_run: StopRecordedRun) -> Optional[str]:
    """The prune's kill: the entry's recorded pid and group, and the processes
    its worker recorded starting, each by its identity, after the run's launch
    gate closed (*stop_recorded_run*, ``detach.stop_recorded_run``: its worker
    may still run). ``None`` when the kill raised.
    """
    try:
        return stop_recorded_run(
            str(entry.get("phase_dir") or ""), entry,
            start_time=entry.get("process_start_time"))
    except Exception:
        return None


def _close_out_entry(entry: Dict[str, Any], project_root: str,
                     close_out_entry: CloseOutEntry, *, kill: bool,
                     **killed: Any) -> Optional[Dict[str, Any]]:
    """Ask the run-lifecycle owner to close this entry's run out, or to try
    again a cleanup it left unconfirmed (*close_out_entry*,
    ``detach.close_out_entry``, which *kill* and a *killed* verdict go to); the
    outcome of its kill (``run.cleanup``'s shape), ``None`` when it made none.
    """
    if not entry.get("run_id"):
        return None
    try:
        return close_out_entry(entry, reason="heartbeat_timeout",
                               project_root=project_root, kill=kill, **killed)
    except Exception:
        return {"state": "incomplete", "verdict": None}
