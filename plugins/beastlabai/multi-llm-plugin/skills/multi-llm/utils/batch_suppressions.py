"""Each write leg's evidence of what one code batch changed, read for the suppression scan.

:mod:`utils.suppression_scan` lists the suppression and skip markers a batch
added; this module hands it the batch's own before and after text, never a
working-tree diff, which would also hold the user's uncommitted edits and the
earlier batches' (docs/development/write-scheduler.md#suppressions-a-batch-added).

- **The executor leg** (:func:`executor_scan`): the batch's mandatory pre-batch
  snapshot holds the bytes of every file it declared and of every undeclared
  file the containment sweep adopted. Each file the post-run comparison saw
  change (``files_touched``) is scanned from that copy to the file as the batch
  left it, before any later batch runs. A moved file with no copy
  (``unrestorable``) is listed as not scanned.
- **The native leg** (:func:`native_base`, :func:`native_scan`): it takes no
  snapshot of a code batch, so ``util write-prompt`` records a scan base as it
  binds the batch (its ``prompts/<task id>.scan.json``): the commit ``HEAD``
  named, the files git sees with their sizes and modification times, and the
  marker counts (:func:`suppression_scan.before_side`) of every declared file
  and every file that already differed from that commit. ``util batch-done``
  scans each file whose size or time moved since, against its recorded counts,
  or, for a file that matched the commit then, against the commit's copy.

A batch kept at the user's request (``--human-task <batch>=skip``) is not
scanned again (:func:`kept_scan`): its row carries what the scan found when
it stopped, since a scan now would list edits made since as the batch's.

Report only, on both legs: a file the scan cannot read or fails on is listed
as not scanned, and nothing here fails a batch. Each hit is printed as one
:data:`SUPPRESSION_MARKER` line.
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from . import suppression_scan as _scan
from .git_utils import head_or_empty_tree, run_git
from .write_safety import (
    MANIFEST_NAME,
    MAX_SNAPSHOT_BYTES,
    PAYLOAD_DIRNAME,
    WriteSafetyError,
    contain_under_root,
)

__all__ = [
    "SCAN_BASE_SUFFIX",
    "SUPPRESSION_MARKER",
    "executor_scan",
    "kept_scan",
    "marker_lines",
    "native_base",
    "native_scan",
    "scan_failed",
]

#: One line per hit, on the executor's log and ``util batch-done``'s stdout.
SUPPRESSION_MARKER = "[SUPPRESSION_ADDED]"

#: The suffix of a native code batch's bind-time scan base, beside its prompt.
SCAN_BASE_SUFFIX = ".scan.json"

#: The version of the scan base's shape.
SCAN_BASE_VERSION = 1

#: The largest file either side of a scan reads; a larger one is not scanned.
SCAN_MAX_BYTES = MAX_SNAPSHOT_BYTES

Hits = List[Dict[str, Any]]
Unscanned = List[Dict[str, str]]


def _unscanned(path: str, why: str) -> Dict[str, str]:
    return {"path": path, "why": why}


def _read_text(root: str, relative: str) -> Tuple[Optional[str], Optional[str]]:
    """``(text, None)`` for a regular file below *root*, ``(None, None)`` for
    one that is not there, and ``(None, why)`` for one that cannot be read.

    Contained below the root first (``contain_under_root``), then opened
    without following a link where the platform can, so a link the batch put
    there is never read through."""
    try:
        resolved = contain_under_root(relative, root, what="scanned file")
    except WriteSafetyError:
        return None, "it resolves outside the repository"
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_BINARY", 0)
    try:
        handle = os.open(str(resolved), flags)
    except FileNotFoundError:
        return None, None
    except OSError as exc:
        return None, f"it could not be read ({exc.strerror or exc})"
    try:
        info = os.fstat(handle)
        if not stat.S_ISREG(info.st_mode):
            return None, "it is not a regular file"
        if info.st_size > SCAN_MAX_BYTES:
            return None, f"it is over {SCAN_MAX_BYTES} bytes"
        with os.fdopen(handle, "rb", closefd=False) as stream:
            data = stream.read(SCAN_MAX_BYTES + 1)
    except OSError as exc:
        return None, f"it could not be read ({exc.strerror or exc})"
    finally:
        os.close(handle)
    if len(data) > SCAN_MAX_BYTES:
        return None, f"it is over {SCAN_MAX_BYTES} bytes"
    return data.decode("utf-8", errors="replace"), None


def marker_lines(task_id: str, hits: Iterable[Mapping[str, Any]]) -> List[str]:
    """One :data:`SUPPRESSION_MARKER` line per hit."""
    return [f"{SUPPRESSION_MARKER} {task_id}: {_scan.hit_line(hit)}" for hit in hits]


def scan_failed(paths: Iterable[Any], exc: BaseException) -> Unscanned:
    """The not-scanned entries of a batch whose scan raised as a whole: each
    of *paths* the scan would have read, so the summary still names them."""
    why = f"the suppression scan did not run ({type(exc).__name__})"
    return [_unscanned(str(path), why) for path in paths or () if _scan.scannable(str(path))]


#: Why a kept batch's files are listed as not scanned when the stopped run's
#: report row is not on record.
KEPT_NOT_ON_RECORD = (
    "it was kept at your request and the scan taken when it stopped is not on "
    "record; a scan now could list edits made since the stop as the batch's"
)


def kept_scan(
    stopped_row: Optional[Mapping[str, Any]], files_touched: Sequence[str],
) -> Tuple[Hits, Unscanned]:
    """``(hits, not scanned)`` for a batch kept at the user's request.

    Never a new scan: what the batch added was scanned when it stopped (a
    partial application is scanned like any batch that moved bytes), and
    its stopped run's report row (*stopped_row*), which the kept row
    replaces, holds the result; it is carried as it stands. A scan now would
    read the files as they are at the resume, so edits made between the stop
    and the resume would be listed as the batch's. With no row on record
    (the report was unreadable, or belongs to an earlier review cycle), or
    with its fields not as this module writes them, each file of
    *files_touched* the scan would read is listed as not scanned.
    """
    carried = _carried(stopped_row) if stopped_row is not None else None
    if carried is None:
        return [], [
            _unscanned(str(path), KEPT_NOT_ON_RECORD)
            for path in files_touched if _scan.scannable(str(path))
        ]
    return carried


def _carried(row: Mapping[str, Any]) -> Optional[Tuple[Hits, Unscanned]]:
    """A report row's hits and not-scanned files, or ``None`` when they are
    not as written: a list of objects each, every hit's line a number."""
    hits = row.get("suppressions") or []
    skipped = row.get("suppressions_not_scanned") or []
    if not isinstance(hits, list) or not isinstance(skipped, list) \
            or not all(isinstance(entry, Mapping) for entry in [*hits, *skipped]):
        return None
    try:
        for hit in hits:
            int(hit.get("line") or 0)
    except (TypeError, ValueError):
        return None
    return [dict(hit) for hit in hits], [
        _unscanned(str(entry.get("path")), str(entry.get("why") or "")) for entry in skipped
    ]


# ---------------------------------------------------------------------------
# The executor leg
# ---------------------------------------------------------------------------

def executor_scan(
    snapshot_dir: Optional[str],
    files_touched: Sequence[str],
    unrestorable: Sequence[str] = (),
) -> Tuple[Hits, Unscanned]:
    """``(hits, not scanned)`` for one executor batch, from its pre-batch
    snapshot at *snapshot_dir* to the files as they are now.

    *files_touched* is the batch's verified rollback set and *unrestorable*
    the moved files with no rollback point (``TaskOutcome``). The manifest is
    read from disk, so the undeclared writes the sweep adopted into it are
    included; a payload whose bytes no longer hash to the manifest's
    ``sha256_before`` is not trusted, and its file is listed as not scanned.
    """
    unscanned: Unscanned = []
    wanted = [path for path in files_touched if _scan.scannable(path)]
    entries: Dict[str, Mapping[str, Any]] = {}
    root = ""
    if snapshot_dir and wanted:
        try:
            manifest = json.loads(
                (Path(snapshot_dir) / MANIFEST_NAME).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            manifest = {}
        if isinstance(manifest, dict):
            root = str(manifest.get("root") or "")
            for entry in manifest.get("files") or []:
                if isinstance(entry, dict) and entry.get("path"):
                    entries[str(entry["path"])] = entry
    changes: List[Tuple[str, Optional[str], Optional[str]]] = []
    for path in wanted:
        entry = entries.get(path)
        if entry is None or not root:
            unscanned.append(_unscanned(path, "no copy of it from before the batch"))
            continue
        before: Optional[str] = None
        if entry.get("existed"):
            payload = entry.get("payload")
            data: Optional[bytes] = None
            if payload:
                try:
                    data = (Path(snapshot_dir) / PAYLOAD_DIRNAME / str(payload)).read_bytes()
                except OSError:
                    data = None
            if data is None or hashlib.sha256(data).hexdigest() != entry.get("sha256_before"):
                unscanned.append(_unscanned(
                    path, "its copy from before the batch is missing or changed"))
                continue
            before = data.decode("utf-8", errors="replace")
        after, why = _read_text(root, path)
        if why:
            unscanned.append(_unscanned(path, why))
            continue
        changes.append((path, before, after))
    for path in unrestorable:
        if _scan.scannable(path):
            unscanned.append(_unscanned(path, "no copy of it from before the batch"))
    return _scan.scan_changes(changes, unscanned), unscanned


# ---------------------------------------------------------------------------
# The native leg
# ---------------------------------------------------------------------------

def _git_paths(root: str, *args: str) -> Optional[List[str]]:
    """The ``-z`` path list a git command prints, or ``None`` when it fails."""
    try:
        stdout, _, code = run_git(*args, check=False, cwd=root)
    except OSError:
        return None
    if code != 0:
        return None
    return [path for path in stdout.split("\0") if path]


def _differing_from(root: str, head: str) -> Optional[List[str]]:
    """The files whose disk copy is not what *head* holds: tracked files with
    staged or unstaged changes, and untracked files git does not ignore."""
    tracked = _git_paths(root, "diff", "--name-only", "--no-renames", "-z", head, "--")
    untracked = _git_paths(root, "ls-files", "--others", "--exclude-standard", "-z",
                           "--full-name", "--", ":/")
    if tracked is None or untracked is None:
        return None
    return sorted(set(tracked) | set(untracked))


def native_base(
    root: str,
    declared: Iterable[str],
    tree: Optional[Mapping[str, Sequence[int]]],
) -> Optional[Dict[str, Any]]:
    """The scan base a native code batch is bound with, or ``None`` when the
    commit cannot be named.

    *root* is the pinned repository root, *declared* the batch's declared
    files (repository-relative), *tree* the files git sees now with
    ``[size, mtime_ns]`` (``write_prompt``'s check-tree reading), ``None``
    when it could not be read: the base then holds the declared files alone,
    and only they are scanned.
    """
    try:
        head = head_or_empty_tree(cwd=root)
    except Exception:  # noqa: BLE001 - report only: no base, no scan
        return None
    declared_paths = sorted({str(path).replace("\\", "/") for path in declared})
    wanted = set(declared_paths)
    if tree is not None:
        differing = _differing_from(root, head)
        if differing is None:
            tree = None
        else:
            wanted |= {path for path in differing if path in tree}
    before: Dict[str, Optional[Dict[str, Any]]] = {}
    unread: Dict[str, str] = {}
    for path in sorted(wanted):
        if not _scan.scannable(path):
            continue
        text, why = _read_text(root, path)
        if why:
            unread[path] = why
            continue
        before[path] = _scan.before_side(path, text)
    return {
        "version": SCAN_BASE_VERSION,
        "repo_root": root,
        "head": head,
        "declared": declared_paths,
        "tree": None if tree is None else {path: list(stat_) for path, stat_ in tree.items()},
        "before": before,
        "unread": unread,
    }


def _blob_text(root: str, head: str, path: str) -> Tuple[Optional[str], bool]:
    """``(text, found)``: *path*'s bytes in commit *head*."""
    try:
        stdout, _, code = run_git("cat-file", "blob", f"{head}:{path}", check=False, cwd=root)
    except OSError:
        return None, False
    if code != 0:
        return None, False
    return stdout, True


def native_scan(
    base: Mapping[str, Any],
    root: str,
    tree: Optional[Mapping[str, Sequence[int]]],
    others: Iterable[str] = (),
) -> Tuple[Hits, Unscanned]:
    """``(hits, not scanned)`` for one native code batch, from its scan base
    (:func:`native_base`) to the files as they are now.

    *tree* is the files git sees now, read as the base's was; when either is
    ``None`` only the declared files are scanned. A file that matched the
    base's commit when the batch was bound nets against that commit's copy; a
    file not in the base's tree then is one the batch created. *others* are
    the files the phase's other tasks declare: the host may run a batch's
    tasks side by side, so a change to one of them is that task's, never
    this one's, as the check guard reads it (``write_prompt.changed_since_bound``).
    """
    unscanned: Unscanned = []
    if str(base.get("repo_root") or "") != str(root):
        return [], unscanned
    head = str(base.get("head") or "")
    before: Mapping[str, Any] = base.get("before") or {}
    unread: Mapping[str, str] = base.get("unread") or {}
    declared = [str(path) for path in base.get("declared") or []]
    then = base.get("tree")
    if isinstance(then, dict) and tree is not None:
        changed = sorted(
            path for path in set(then) | set(tree)
            if list(then.get(path) or []) != list(tree.get(path) or [])
        )
    else:
        then = None
        changed = sorted(set(declared))
    theirs = {str(path) for path in others} - set(declared)
    changed = [path for path in changed if path not in theirs]
    changes: List[Tuple[str, Any, Optional[str]]] = []
    for path in changed:
        if not _scan.scannable(path):
            continue
        if path in unread:
            unscanned.append(_unscanned(path, f"before the batch {unread[path]}"))
            continue
        if path in before:
            side: Any = before[path]
        elif then is not None and path not in then:
            side = None
        elif then is not None:
            side, found = _blob_text(root, head, path)
            if not found:
                unscanned.append(_unscanned(path, "no copy of it from before the batch"))
                continue
        else:
            continue
        after, why = _read_text(root, path)
        if why:
            unscanned.append(_unscanned(path, why))
            continue
        changes.append((path, side, after))
    return _scan.scan_changes(changes, unscanned), unscanned
