#!/usr/bin/env python3
"""Everything a headless *write* dispatch must be safe before it is useful.

``utils/subagent_executor.py`` hardens what the executor writes and where the
runner is rooted for the read/analyze half. The write half's exposure is one level
out: ``claude -p --permission-mode acceptEdits``, ``codex exec --sandbox
workspace-write`` and opencode's ``build`` agent **pre-approve every write the
model chooses to make**, anywhere in the repository, and under ``--detach`` or in
CI there is no human between the model and the working tree at all. "Sandbox flags
per adapter" is a boundary, not a security model. The five controls here make it
one, all on by default:

* **A pinned repo root** (D3h). ``git rev-parse --show-toplevel`` of the target
  workspace, ``realpath``-resolved, and every path the executor snapshots,
  expects a batch to touch, or observes it having touched must resolve beneath it.
  Both sides of every containment comparison are canonicalized — asymmetry is the
  bug (D1c), not the shortcut.
* **A declared write policy, enforced twice** (D3l). ``driver.write_paths``
  ``allow``/``deny`` globs resolved against that root. **Pre-dispatch**, a batch
  whose declared file set is not wholly inside the policy is refused before the
  runner starts. **Post-run**, the observed touched set is recomputed and anything
  outside the policy is a containment violation: the batch fails, the offending
  files are restored from their pre-batch snapshot, the loop stops. Stated
  honestly: post-run enforcement is *detective*. The runner's own sandbox stays
  the preventive control; this is the second layer that makes the violation loud.
* **A mandatory pre-batch snapshot** (D3h/D3g). Under ``{phase}/pre_batch/{task_id}/``
  — never a shared workspace temp path — so concurrent or resumed batches cannot
  clobber each other's rollback point, and a partial application leaves
  recoverable bytes. The snapshot is also the *verdict*: the model's claim is
  never trusted, byte comparison decides. It covers the declared set at
  ``take`` time and grows by :meth:`TaskSnapshot.adopt` for the paths the
  scheduler's post-run sweep observed *outside* that set — the only paths the
  post-run policy check can actually fail on, and therefore the ones a rollback
  point has to exist for.
* **Dispatch-time disjointness admission** (D3h). Parallel write dispatch is
  admitted only when the in-flight tasks' declared file sets are pairwise
  disjoint; a task declaring no file set runs alone. Checked executor-side rather
  than trusted from the batcher, so a hand-edited task file cannot produce two
  agents editing one file.
* **An append-only audit record** (D3l). One fsynced line per dispatch and one
  per classification in ``{phase}/subagent_audit.jsonl``, with the prompt reduced
  to its sha256 and byte length. The prompt body, the runner's environment and any
  auth value are **never** logged: prompts are large and carry untrusted text, and
  an audit log that leaks credentials is a new vulnerability rather than a control.

Scope, so the claim is not oversold: this is workspace-write discipline, not a
sandbox-escape defense. A runner that ignores its own sandbox flags, or a host
that grants the executor more than the repo, is outside what this can enforce.
"""

from __future__ import annotations

import errno
import hashlib
import json
import os
import posixpath
import re
import secrets
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile
import threading
import time
from datetime import datetime
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Set, Tuple, Union

from .atomic_io import atomic_write_bytes, temp_path_for
from .clock import local_iso_seconds
from .git_utils import pin_repo_root, find_git_entry_root
# The walk and the hold (a folder reached from a root without following a link,
# held by its descriptor) live below this module, so the L1 writers beside a
# plan (state_file, status_file) hold their folder the same way.
from .held_folder import (  # noqa: F401 - OPENS_WITHOUT_FOLLOWING is re-exported
    _CLOEXEC,
    _MOVED,
    _PROC_SELF_FD,
    _PUT_BACK,
    _READ_FLAGS,
    _REMOVED,
    _WRITTEN,
    OPENS_WITHOUT_FOLLOWING,
    _checked,
    _folder_moved,
    _HeldFolder,
    _in_held_folder,
    _open_below_root,
    _Wording,
    plan_dir_of,
    write_in_plan_dir,
)
from .process_control import (
    FileMutex, descriptor_owning_handle, handle_of_descriptor, process_alive,
)
from .process_state import process_cache
from .provider_registry import get_write_paths
# Redaction is the leaf module utils/redact.py and the state home lives in
# output_handler, so the layers below this one reach them without importing it.
# This module reads them there; the names below are re-exported for reading
# only (tests/test_layer_moves.py), redact_text and redact_argv in __all__.
from . import output_handler as _output_handler
from . import redact as _redact
from .output_handler import state_home  # noqa: F401 - re-exported
from .redact import (  # noqa: F401 - re-exported
    _REDACTIONS,
    _looks_like_credential,
    _replace_group,
    _sha256_text,
    redact_argv,
    redact_text,
)
from .state_manager import _parse_completion_time, predates_review
from .subagent_tasks import declared_file_set

try:  # pragma: no cover - Windows only
    import _winapi
except ImportError:
    _winapi = None


__all__ = [
    "AUDIT_FILENAME",
    "DRY_RUN_FILENAME",
    "PRE_BATCH_DIRNAME",
    "WriteSafetyError",
    "PathEscape",
    "PolicyViolation",
    "PolicyHit",
    "WritePolicy",
    "AuditLog",
    "TaskSnapshot",
    "SnapshotEntry",
    "resolve_repo_root",
    "repo_root_for_report",
    "safety_dir",
    "external_safety_dir",
    "claim_external_safety_dir",
    "state_home",
    "contain_under_root",
    "contain_local_path",
    "write_below_root",
    "rename_below_root",
    "remove_below_root",
    "relative_to_root",
    "admit_disjoint_groups",
    "file_sha256",
    "OPENS_WITHOUT_FOLLOWING",
    "CopyNotContained",
    "RestoreLeftovers",
    "restore_leftovers",
    "read_capped",
    "write_copy",
    "remove_tree",
    "redact_argv",
    "redact_text",
]


#: The append-only write log (D3l). A ``.jsonl`` name, so the reaggregation glob
#: (``{phase_dir}/*.json``) never sees it.
AUDIT_FILENAME = "subagent_audit.jsonl"

#: ``--dry-run-subagents``'s preflight report (D3l).
DRY_RUN_FILENAME = "subagent_dry_run.json"

#: Where per-task snapshots live, under the *phase* dir (D3h) rather than the
#: shared workspace temp path the markdown uses, so concurrent or resumed batches
#: cannot clobber each other's rollback point.
PRE_BATCH_DIRNAME = "pre_batch"

#: The per-snapshot manifest inside ``{phase}/pre_batch/{task_id}/``.
MANIFEST_NAME = "manifest.json"

#: Snapshot payloads live in a sub-directory so the manifest name can never
#: collide with a snapshotted file's own flattened name.
PAYLOAD_DIRNAME = "files"

#: Refuse to snapshot (and therefore to dispatch) a file larger than this. A
#: snapshot that silently did not happen is worse than a refused batch: the
#: classification would read "unchanged" for a file with no rollback point.
MAX_SNAPSHOT_BYTES = 16 * 1024 * 1024

#: Where the rollback evidence of a repo-wide batch on the plugin's Landlock
#: jail lives instead of the phase dir (review fixes 2026-10-05): under the
#: user's state home, outside the root grant. The jail handles only write
#: rights, so a key the batch could not read does not exist — an HMAC over
#: in-grant files would be forgeable by the very batch it guards against —
#: while a directory the jail never grants cannot be written at all. The
#: pre-batch snapshots, the rollback store and the audit log of such a run
#: are what ``util restore-batch`` and ``--resume`` trust; a copy of any of
#: them inside the phase dir is the batch's to write and is never read once
#: this directory exists for the phase.
STATE_SUBDIR = "write-safety"
#: The pointer file the out-of-grant directory carries for a human reader.
STATE_POINTER_NAME = "phase_dir.txt"


def _phase_key(path: str) -> str:
    return hashlib.sha256(path.encode("utf-8", "surrogateescape")).hexdigest()[:32]


def _phase_binding_path(path: str) -> str:
    return os.path.join(_output_handler.state_home(), STATE_SUBDIR, "paths", _phase_key(path))


def _bound_phase(phase_dir: str) -> str:
    """Resolve a phase through its trusted, out-of-grant alias binding first.

    Re-resolving a path the batch replaced with a symlink must never select a
    fresh, unprotected evidence directory. Canonical paths also keep working
    with evidence created before alias bindings existed.
    """
    given = os.path.abspath(str(phase_dir))
    resolved = os.path.realpath(given)
    binding = _phase_binding_path(given)
    try:
        recorded = Path(binding).read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        # Old releases keyed the directory by the canonical path alone.
        legacy = Path(_output_handler.state_home()) / STATE_SUBDIR / _phase_key(given)
        pointer = legacy / STATE_POINTER_NAME
        try:
            recorded = pointer.read_text(encoding="utf-8").strip()
        except FileNotFoundError:
            return resolved
        except (OSError, ValueError) as exc:
            raise WriteSafetyError(f"Cannot read trusted phase identity {pointer}: {exc}") from exc
    except (OSError, ValueError) as exc:
        raise WriteSafetyError(f"Cannot read trusted phase identity {binding}: {exc}") from exc
    if not recorded or not os.path.isabs(recorded) or recorded != resolved:
        raise WriteSafetyError(
            f"Refusing rollback evidence for {given}: its trusted phase identity "
            f"is {recorded or '(missing)'}, but the path now resolves to {resolved}. "
            "The phase path changed after its evidence was bound; no in-repository "
            "snapshot or audit copy is trusted. Restore the original phase path first."
        )
    return recorded


def external_safety_dir(phase_dir: str) -> str:
    """The trusted external location, preserving already-bound path aliases."""
    return os.path.join(
        _output_handler.state_home(), STATE_SUBDIR, _phase_key(_bound_phase(phase_dir)))


def _remember_phase_paths(phase_dir: str, canonical: str) -> None:
    for path in {os.path.abspath(str(phase_dir)), canonical}:
        binding = _phase_binding_path(path)
        if os.path.exists(binding):
            # Never overwrite a binding to another phase.
            _bound_phase(path)
            continue
        # Distinct readers may discover the same alias together. Serialize the
        # check and atomic publication; never replace another phase's binding.
        os.makedirs(os.path.dirname(binding), mode=0o700, exist_ok=True)
        mutex = FileMutex(binding + ".lock")
        try:
            if not mutex.acquire():
                raise WriteSafetyError(f"Cannot lock trusted phase identity for {path}.")
            if os.path.exists(binding):
                _bound_phase(path)
            else:
                _atomic_write(binding, canonical + "\n")
        finally:
            mutex.release()


def _validate_external_identity(external: str, phase_dir: str) -> None:
    try:
        canonical = Path(external, STATE_POINTER_NAME).read_text(encoding="utf-8").strip()
    except (OSError, ValueError) as exc:
        raise WriteSafetyError(f"Cannot read trusted rollback identity in {external}: {exc}") from exc
    if os.path.islink(external) or canonical != _bound_phase(phase_dir):
        raise WriteSafetyError(f"Refusing rollback evidence at {external}: its phase identity does not match {phase_dir}.")
    # A previously unseen legitimate alias becomes bound before any caller
    # trusts evidence through it; a later replacement cannot select a new key.
    try:
        _remember_phase_paths(phase_dir, canonical)
    except OSError as exc:
        raise WriteSafetyError(f"Cannot bind trusted rollback identity for {phase_dir}: {exc}") from exc


def safety_dir(phase_dir: str) -> str:
    """Where ``phase_dir``'s pre-batch snapshots, rollback store and audit
    log live: the out-of-grant directory once a jailed repo-wide run claimed
    it (:func:`claim_external_safety_dir`), else the phase dir itself — every
    other runner's behaviour, unchanged."""
    external = external_safety_dir(phase_dir)
    if os.path.lexists(external):
        _validate_external_identity(external, phase_dir)
        return external
    # A binding outlives the directory it identifies: losing trusted evidence
    # is a refusal, never permission to trust a writable replacement.
    if os.path.exists(_phase_binding_path(os.path.abspath(str(phase_dir)))):
        raise WriteSafetyError(f"Trusted rollback evidence is missing at {external}; refusing the in-repository copy.")
    return str(phase_dir)


def _copy_safety_evidence(phase_dir: str, staging: str, repo_root: str) -> None:
    """Copy and validate the old evidence before publishing the new location."""
    for name in (PRE_BATCH_DIRNAME, "rollback_store", AUDIT_FILENAME):
        source = Path(phase_dir) / name
        if not os.path.lexists(source):
            continue
        paths = [source]
        if source.is_dir() and not source.is_symlink():
            paths.extend(source.rglob("*"))
        for path in paths:
            mode = path.lstat().st_mode
            if not (stat.S_ISREG(mode) or stat.S_ISDIR(mode)):
                raise WriteSafetyError(f"Cannot promote rollback evidence: {path} is not a regular file or directory.")
        destination = Path(staging) / name
        if source.is_dir():
            shutil.copytree(source, destination)
        else:
            shutil.copy2(source, destination)
    for manifest in (Path(staging) / PRE_BATCH_DIRNAME).glob("*/manifest.json"):
        try:
            snapshot = TaskSnapshot.load(staging, manifest.parent.name, expected_root=repo_root)
        except (AttributeError, TypeError, ValueError) as exc:
            raise WriteSafetyError(f"Cannot promote invalid rollback manifest {manifest}: {exc}") from exc
        if snapshot is None:
            raise WriteSafetyError(f"Cannot promote unreadable rollback manifest {manifest}.")
        for entry in snapshot.entries:
            _revalidated_target(repo_root, entry.relative, create_parents=False)
            if entry.existed:
                payload = Path(snapshot.directory) / PAYLOAD_DIRNAME / (entry.payload or "")
                if (not entry.payload or Path(entry.payload).name != entry.payload
                        or not payload.is_file() or file_sha256(str(payload)) != entry.sha256):
                    raise WriteSafetyError(f"Cannot promote rollback evidence: payload for {entry.relative} does not match its manifest.")
    audit = Path(staging) / AUDIT_FILENAME
    if audit.exists():
        try:
            records = [json.loads(line) for line in audit.read_text(encoding="utf-8").splitlines() if line.strip()]
            if any(not isinstance(record, dict) for record in records):
                raise ValueError("audit entries must be objects")
        except (OSError, ValueError) as exc:
            raise WriteSafetyError(f"Cannot promote unreadable rollback audit {audit}: {exc}") from exc


def claim_external_safety_dir(phase_dir: str, repo_root: str) -> str:
    """Create (0700) and return the out-of-grant directory for ``phase_dir``,
    refusing one that would sit inside ``repo_root`` — inside the grant it
    protects nothing."""
    external = external_safety_dir(phase_dir)
    root = os.path.realpath(repo_root).rstrip(os.sep) + os.sep
    if os.path.realpath(external).startswith(root):
        raise WriteSafetyError(
            f"The rollback evidence of a repo-wide batch on the plugin's jail "
            f"must live outside the repository, but the state home "
            f"{_output_handler.state_home()} is inside {repo_root}; set XDG_STATE_HOME to a "
            f"directory outside it. Nothing was dispatched."
        )
    safety_dir(phase_dir)  # a missing previously-bound store is never recreated
    parent = os.path.dirname(external)
    staging = None
    mutex = FileMutex(os.path.join(parent, f".{os.path.basename(external)}.lock"))
    try:
        os.makedirs(parent, mode=0o700, exist_ok=True)
        if not mutex.acquire():
            raise WriteSafetyError(f"Cannot lock rollback evidence promotion for {phase_dir}; nothing was dispatched.")
        if os.path.lexists(external):
            _validate_external_identity(external, phase_dir)
            return external
        # Do not publish an empty directory: discovery switches at the rename,
        # after every old snapshot, audit record and retained blob is copied.
        staging = tempfile.mkdtemp(prefix=".promote-", dir=parent)
        _copy_safety_evidence(phase_dir, staging, repo_root)
        canonical = _bound_phase(phase_dir)
        _atomic_write(os.path.join(staging, STATE_POINTER_NAME), canonical + "\n")
        os.rename(staging, external)
        staging = None
        _remember_phase_paths(phase_dir, canonical)
        return external
    except (OSError, ValueError) as exc:
        raise WriteSafetyError(f"Cannot promote rollback evidence for {phase_dir}: {exc}. Nothing was dispatched.") from exc
    finally:
        if staging is not None:
            shutil.rmtree(staging, ignore_errors=True)
        mutex.release()


class WriteSafetyError(Exception):
    """A write dispatch the executor refuses. Exit 3 ("needs a human", D6)."""

    exit_code = 3

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class PathEscape(WriteSafetyError):
    """A path from a task file resolves outside the pinned repo root (D3f/D3h)."""


class PolicyViolation(WriteSafetyError):
    """A path is outside ``driver.write_paths`` (D3l). Carries the offenders:
    ``paths`` as named, and ``hits``, each one's
    :class:`PolicyHit`, which every way forward is worded from."""

    def __init__(
        self, message: str, paths: Sequence[str], rule: str = "",
        hits: Optional[Sequence["PolicyHit"]] = None,
    ) -> None:
        super().__init__(message)
        self.paths = list(paths)
        self.rule = rule
        self.hits = list(hits or [])


# ---------------------------------------------------------------------------
# The pinned repo root (D3h) and containment (D3f)
# ---------------------------------------------------------------------------

def resolve_repo_root(anchor: Optional[str]) -> str:
    """The write path's one root: the directory holding the ``.git`` entry
    above the anchor, canonicalized (``git_utils.pin_repo_root``).

    ``realpath``, not ``abspath``: this value is one side of every containment
    comparison below and the other side is canonicalized too, so a symlinked
    checkout compares equal instead of every path reading as an escape. (The
    opposite rule applies to the *skill* dir, which must keep its symlinks — see
    ``utils/cli_common``. The distinction is exactly D1c: canonicalize for
    containment, preserve for invocation.)

    Until the 2026-10-05 review fixes this was ``git rev-parse --show-toplevel``
    alone, which a planted ``core.worktree`` (writable by a repo-wide batch
    under the root grant) redirected to any directory, where the next
    repo-wide jail's one rule then landed. The root is now walked from the
    anchor, git's answer must agree with it, and a disagreement — or a
    ``GIT_DIR``/``GIT_WORK_TREE`` in the environment — is refused with exit 3
    naming the cause rather than silently re-pinned.

    Falls back to the anchor's own directory when the anchor is not in a git repo,
    because a plan in a bare directory is a legitimate target — but the root is
    still pinned to *something* explicit, never left to the process cwd.
    """
    start = Path(anchor).resolve() if anchor else Path.cwd().resolve()
    probe_dir = str(start if start.is_dir() else start.parent)
    try:
        root, problem = pin_repo_root(probe_dir)
    except (OSError, subprocess.SubprocessError):  # pragma: no cover - no git
        return str(Path(probe_dir).resolve())
    if problem:
        raise WriteSafetyError(
            f"Refusing to pin the repository root for {anchor or probe_dir}: "
            f"{problem}. Nothing was dispatched."
        )
    if root:
        return root
    return str(Path(probe_dir).resolve())


def repo_root_for_report(anchor: Optional[str]) -> str:
    """:func:`resolve_repo_root` for a post-run *report* — the artifact hand-back
    that resolves ``files_touched`` — which must not crash a finished phase
    when a batch planted a redirect during the run: the refusal is printed as
    a warning and the walked ``.git`` holder (else the anchor's directory),
    which no configuration moves, resolves the paths instead."""
    try:
        return resolve_repo_root(anchor)
    except WriteSafetyError as exc:
        print(f"WARNING: {exc.message}", file=sys.stderr)
    start = Path(anchor).resolve() if anchor else Path.cwd().resolve()
    probe_dir = str(start if start.is_dir() else start.parent)
    return find_git_entry_root(probe_dir) or str(Path(probe_dir).resolve())


def _resolves_within(resolved: Path, resolved_root: Path) -> bool:
    """Whether *resolved* is *resolved_root* or beneath it; both canonical."""
    try:
        return resolved.is_relative_to(resolved_root)
    except AttributeError:  # pragma: no cover - Python < 3.9
        return os.path.commonpath(
            [str(resolved), str(resolved_root)]
        ) == str(resolved_root)


def contain_local_path(
    path: Union[str, "os.PathLike[str]"], root: Union[str, "os.PathLike[str]"],
    *, what: str,
) -> Path:
    """Resolve *path*, a path the plugin computed itself, and require it at or
    beneath *root*, or raise :class:`PathEscape`.

    The comparison is :func:`contain_under_root`'s: both sides resolved, every
    symlinked component followed, so a link planted in the repository cannot
    redirect the write. What it leaves out are the refusals for a path a task
    file or a model supplied (a drive-relative or UNC spelling, an NTFS stream
    colon): this path is built from the plan's own location, where a colon in a
    POSIX directory name or a plan on a network share is real. A relative
    *path* or *root* is taken from the working directory, as the write would
    take it. Resolution is ``os.path.realpath``, the call ``atomic_io`` makes
    to write through a link, so the check and the write agree on the target on
    every Python (``Path.resolve`` raised on a symlink loop before 3.13).
    """
    resolved_root = Path(os.path.realpath(os.path.abspath(root)))
    try:
        resolved = Path(os.path.realpath(os.path.abspath(path)))
    except OSError as exc:  # pragma: no cover - realpath is non-strict
        raise PathEscape(
            f"Refusing the {what} {os.fspath(path)}: it cannot be resolved ({exc})."
        ) from exc
    if not _resolves_within(resolved, resolved_root):
        raise PathEscape(
            f"Refusing the {what} {os.fspath(path)}: it resolves to {resolved}, "
            f"outside {resolved_root}."
        )
    return resolved


def contain_under_root(candidate: str, root: str, *, what: str = "path") -> Path:
    """Resolve ``candidate`` and require it beneath ``root``, or raise (D3f/D3h).

    Resolution happens **after** joining, so a symlinked path component cannot
    redirect the write, and *both* sides are resolved — an asymmetric comparison
    (one resolved, one not) is the classic way this check passes while the write
    lands outside.
    """
    resolved_root = Path(root).resolve()
    raw = Path(candidate)
    joined = raw if raw.is_absolute() else (resolved_root / raw)
    if _looks_like_a_windows_escape(str(candidate)):
        raise PathEscape(
            f"Refusing the {what} {candidate!r}: a drive-relative, UNC or "
            f"alternate-data-stream path is never resolved against the repo root. "
            f"Repo root: {resolved_root}. Nothing was dispatched."
        )
    resolved = joined.resolve()
    if not _resolves_within(resolved, resolved_root):
        raise PathEscape(
            f"Refusing the {what} {candidate!r}: it resolves to {resolved}, outside "
            f"the pinned repo root {resolved_root}. A batch cannot be steered into "
            f"$HOME or a sibling checkout through an injected path. Nothing was "
            f"dispatched."
        )
    return resolved


def _looks_like_a_windows_escape(text: str) -> bool:
    """Drive-relative (``C:foo``), UNC (``\\\\host\\share``) or an ADS (``a.json:b``)."""
    if text.startswith("\\\\") or text.startswith("//"):
        return True
    if re.match(r"^[A-Za-z]:[^\\/]", text):
        return True
    # An NTFS alternate data stream: *any* colon left once the drive prefix has
    # been sliced off, mirroring ``task_result._is_unsafe_windows_path``.
    # The standard shape is ``name.ext:stream``, whose colon is preceded by a
    # letter — a rule that exempted those would flag nothing that matters (D3f).
    remainder = text[2:] if re.match(r"^[A-Za-z]:", text) else text
    return ":" in remainder


def relative_to_root(path: str, root: str) -> str:
    """``path`` as a POSIX repo-relative string, for policy matching and logs."""
    resolved_root = Path(root).resolve()
    resolved = Path(path)
    if not resolved.is_absolute():
        resolved = resolved_root / resolved
    try:
        return resolved.resolve().relative_to(resolved_root).as_posix()
    except ValueError:
        return resolved.resolve().as_posix()


def _outside_root(relative: str) -> bool:
    """Whether :func:`relative_to_root`'s answer lies outside the root."""
    return Path(relative).is_absolute() or relative.startswith("..")


def file_sha256(path: str) -> Optional[str]:
    """The file's sha256, or ``None`` when it does not exist.

    ``None`` is a real state, not an error: the artifact an apply batch edits is
    frequently untracked and may not exist yet, and "absent then present" is the
    creation case the classification has to distinguish from "unchanged".
    """
    try:
        with open(path, "rb") as handle:
            digest = hashlib.sha256()
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
            return digest.hexdigest()
    except (OSError, IsADirectoryError):
        return None


def read_capped(handle: int, limit: int, *, size_hint: int = 0) -> Optional[bytes]:
    """Every byte left in the descriptor *handle*, or ``None`` once more than
    *limit* came (the file grew past the cap since it was last measured).
    *size_hint* (its ``st_size``) sizes the first read, so a file that did not
    grow costs one read and one at the end."""
    chunks: List[bytes] = []
    total = 0
    want = min(max(size_hint, 0), limit) + 1
    while True:
        chunk = os.read(handle, want)
        if not chunk:
            return b"".join(chunks)
        total += len(chunk)
        if total > limit:
            return None
        chunks.append(chunk)
        want = 1 << 16


#: Windows (Python 3.12+): ``CopyFile2``, the call ``shutil.copy2`` makes
#: there. It keeps what a copy of a descriptor's bytes cannot: NTFS alternate
#: data streams, file attributes and EFS encryption.
_COPY_FILE2 = getattr(_winapi, "CopyFile2", None)
#: ``shutil.copy2``'s flag, plus ``COPY_FILE_FAIL_IF_EXISTS`` (0x1 in
#: WinBase.h), so the copy itself is the exclusive creation of its name, and
#: ``COPY_FILE_COPY_SYMLINK`` (0x800). ``CopyFileEx`` documents that with
#: both the copy fails on any link already at the destination, and with
#: ``COPY_FILE_FAIL_IF_EXISTS`` alone only on one whose target exists. Windows
#: does not do so for a regular source: with both flags, a link at the
#: destination to a target that does not exist is followed and that target
#: created with the copy's bytes (``windows-latest``, CI of 2026-11-12, a
#: link planted at the name between its clearing and the copy). So nothing
#: rests on the flags for a link there: ``CopyFile2`` only ever copies to a
#: name nobody can know before it makes it (:func:`_copy_name`, and the
#: restore's :func:`_staging_name`), cleared or checked empty first. At the source
#: the flag copies a link as a link, and the source was checked to be a
#: regular file, so a link there is a swap, refused after the copy
#: (docs/development/write-safety.md, the rollback store's reads).
_COPY_FILE2_FLAGS = (getattr(_winapi, "COPY_FILE_ALLOW_DECRYPTED_DESTINATION", 0x8)
                     | getattr(_winapi, "COPY_FILE_FAIL_IF_EXISTS", 0x1)
                     | getattr(_winapi, "COPY_FILE_COPY_SYMLINK", 0x800))
#: Whether ``os.open``'s exclusive creation can be written through a link
#: already at the name. On Windows ``O_CREAT | O_EXCL`` is ``CreateFile``'s
#: ``CREATE_NEW`` without ``FILE_FLAG_OPEN_REPARSE_POINT``, and there is no
#: ``O_NOFOLLOW``: a link at the name to a target that does not exist is
#: followed and that target created (``windows-latest``, CI of 2026-11-12,
#: the store's plain copy over a link planted at its pending name). POSIX
#: ``open(2)`` with ``O_CREAT | O_EXCL`` refuses any link there (``EEXIST``),
#: dangling or not. Where it can, :func:`write_copy` makes its plain copy
#: through :meth:`_HeldCopyCalls.create` instead
#: (:func:`_written_through_handle`).
_EXCLUSIVE_OPEN_FOLLOWS_LINKS = os.name == "nt"
#: The ``CopyFile2`` refusal ``shutil.copy2`` answers with a plain copy.
_ERROR_ACCESS_DENIED = getattr(_winapi, "ERROR_ACCESS_DENIED", 5)


class CopyNotContained(OSError):
    """:func:`write_copy` cannot show that what it copied is gone or stayed
    where it put it: a refused copy, or a name already at *pending*, that it
    could not remove, or a link at *pending* once ``CopyFile2`` had copied,
    which the copy may have been written through. ``pending`` names the
    place. What is left there, or at the link's target, can be another
    file's bytes, one from outside the repository included, so the caller
    says so instead of dropping it like any other failed copy."""

    def __init__(self, pending: str, message: str) -> None:
        super().__init__(message)
        self.pending = pending


#: A file's identity as the leftover set keeps it (:data:`_LEFTOVERS`):
#: ``(st_dev, st_ino, st_ctime_ns)``. The change time is in it because a
#: filesystem can give a removed file's inode number to the next file made, and
#: no call sets it.
_Identity = Tuple[int, int, int]


class _StagingLeft(CopyNotContained):
    """:class:`CopyNotContained` for a restore's own staged entry, kept at
    *pending* after a failure for the user to check and remove; *identity*
    is its :data:`_Identity`, ``None`` where it could not be read. The
    restore records it (:func:`_record_left`) and ``unrecorded`` says why
    when it could not (docs/development/write-safety.md, restore)."""

    def __init__(self, pending: str, message: str,
                 identity: Optional[_Identity]) -> None:
        super().__init__(pending, message)
        self.identity = identity
        self.unrecorded: Optional[str] = None


def write_copy(pending: str, data: bytes, source: int, *,
               path: Optional[str] = None) -> None:
    """*data*, just read from the descriptor *source*, as the new file
    *pending*, with what ``shutil.copy2`` keeps of the source's metadata.
    Raises ``OSError``; nothing is left at *pending* then, or it raises
    :class:`CopyNotContained`, naming what is.

    Created exclusively and never through a link: a name already at
    *pending* (a killed run's leftover, or a link planted at that
    predictable name) is removed, never written through.

    * Windows on Python 3.12+ (``CopyFile2``), with *path* the name *source*
      was opened by: copied by path with ``CopyFile2``, as ``shutil.copy2``
      copies there, so the copy keeps the source's alternate data streams,
      attributes and EFS encryption. ``CopyFile2`` follows a link to nothing
      at its destination whatever the flags (:data:`_COPY_FILE2_FLAGS`), so
      it never copies to *pending*, which a link can be planted at between
      its clearing and the copy, but to a name beside it drawn at random for
      this copy (:func:`_copy_name`), which nobody can know before the copy
      makes it. Then that copy must be a plain new file (no link, no reparse
      point, no other name), *path* must still name the file *source* reads
      (``lstat`` against ``fstat``) and the copy must hold exactly *data*, so
      a blob never holds bytes other than the ones read and hashed; then it
      is renamed to *pending* (``os.replace``: the entry itself, never
      through a link). Otherwise the copy is removed, its read-only
      attribute (which ``CopyFile2`` copies) cleared first, as is whatever a
      failed ``CopyFile2`` left there. Where ``CopyFile2`` refuses access,
      ``shutil.copy2`` falls back to a plain copy, and so does this.
    * Windows otherwise (Python before 3.12, a refused ``CopyFile2``, no
      *path*): :func:`_written_through_handle`, as ``os.open``'s exclusive
      creation follows a link to nothing there
      (:data:`_EXCLUSIVE_OPEN_FOLLOWS_LINKS`).
    * Elsewhere: *data* is written, and the times, extended attributes,
      mode and flags come from the descriptor *source*, ``fstat``-ed now,
      after the read, as ``copy2`` stats after copying, never from a path
      that can name another file by now. The times and mode are set through
      the new file's descriptor where the platform can."""
    if path is not None and _COPY_FILE2 is not None:
        fresh = _copy_name(os.fsdecode(pending))
        try:
            _copy_file2(os.fsdecode(path), os.fsdecode(pending), fresh)
        except CopyNotContained:
            raise
        except BaseException as failure:
            # Whatever a failed copy left at its name (part of a copy) goes.
            _discard_after(failure, fresh, None)
            if getattr(failure, "winerror", None) != _ERROR_ACCESS_DENIED:
                raise
        else:
            made: List[Tuple[int, int]] = []
            try:
                if not _copied_unchanged(path, fresh, data, source, made):
                    raise OSError(
                        f"{path} changed while it was copied to {fresh}")
            except BaseException as failure:
                _discard_after(failure, fresh, made[0] if made else None)
                raise
            try:
                os.replace(fresh, pending)
            except BaseException as failure:
                # Something put at *pending* since its clearing (a folder, a
                # junction, a read-only file) refuses the rename. The copy
                # goes, and so does that name, as a copy made at *pending*
                # itself removed what it found there; what cannot be removed
                # is CopyNotContained, never a silent OSError.
                _discard_after(failure, fresh, made[0] if made else None)
                _discard_after(failure, pending, None)
                raise
            return
    info = os.fstat(source)
    if _EXCLUSIVE_OPEN_FOLLOWS_LINKS:
        _written_through_handle(os.fsdecode(pending), data, info)
        return
    flags = (os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
             | _CLOEXEC | getattr(os, "O_NOINHERIT", 0) | getattr(os, "O_BINARY", 0))
    try:
        handle = os.open(pending, flags, 0o600)
    except FileExistsError:
        _discard(pending)
        handle = os.open(pending, flags, 0o600)
    by_descriptor = os.utime in os.supports_fd and os.chmod in os.supports_fd
    created: Optional[Tuple[int, int]] = None
    try:
        with os.fdopen(handle, "wb") as stream:
            opened = os.fstat(stream.fileno())
            created = (opened.st_dev, opened.st_ino)
            stream.write(data)
            stream.flush()
            _copy_xattrs(source, stream.fileno())
            if by_descriptor:
                _copy_times_and_mode(stream.fileno(), info)
        if not by_descriptor:  # pragma: no cover - descriptors take neither, once closed
            _copy_times_and_mode(pending, info)
        if hasattr(info, "st_flags") and hasattr(os, "chflags"):  # pragma: no cover - BSD, macOS
            try:
                os.chflags(pending, info.st_flags, follow_symlinks=(
                    os.chflags not in os.supports_follow_symlinks))
            except OSError as exc:
                if exc.errno not in (errno.EOPNOTSUPP, errno.ENOTSUP):
                    raise
    except BaseException as failure:
        _discard_after(failure, pending, created)
        raise


def _copy_file2(path: str, pending: str, fresh: str) -> None:
    """``CopyFile2`` of *path* to the new file *fresh* (:func:`_copy_name`),
    which :func:`write_copy` renames to *pending* once it is checked. A name
    already at *pending* (a leftover, or a link planted at that predictable
    name, dangling or not) is removed first, never followed, or nothing is
    copied, and so is one at *fresh*, which only someone who knew its token
    can have put there.

    Never copied to *pending* itself: a link to nothing put there between
    its clearing and the copy would be followed, and its target created
    with the copy's bytes, ``COPY_FILE_FAIL_IF_EXISTS`` with
    ``COPY_FILE_COPY_SYMLINK`` notwithstanding (:data:`_COPY_FILE2_FLAGS`).
    Nobody can plant one at *fresh* before ``CopyFile2`` makes it, as its
    token is drawn now; :func:`_copied_unchanged` still refuses a copy that
    is a link once made."""
    _discard(pending)
    _discard(fresh)
    _COPY_FILE2(path, fresh, _COPY_FILE2_FLAGS)


#: :func:`_copy_name`'s names: ``.copy.<pid>.<token>.tmp``, the pid the
#: copying process's, so a copy a killed process left can be told from one in
#: flight (:func:`_reclaim_dead_copies`).
_COPY_NAME = re.compile(r"\A\.copy\.(\d+)\.[0-9a-f]{16}\.tmp\Z")

#: The folders :func:`_reclaim_dead_copies` has already looked through in this
#: process: once each, never once per copy.
_RECLAIMED_LOCK = threading.Lock()
_RECLAIMED: Set[str] = process_cache(
    "utils.write_safety._RECLAIMED", set, lock=_RECLAIMED_LOCK)


def _copy_name(pending: str) -> str:
    """The name ``CopyFile2`` makes *pending*'s copy under
    (:func:`_copy_file2`): beside it, so the rename that puts it at
    *pending* stays on one filesystem; hidden; this process's pid, then a
    token drawn now (:func:`_copy_token`), so the name cannot be known
    before the copy makes it. It is 30-odd characters, which can be longer
    than *pending*'s own name (a snapshot payload's can be 8): in a folder
    that close to ``MAX_PATH``, without long paths, the copy fails and says
    so. What a killed process left under such names in the folder goes first
    (:func:`_reclaim_dead_copies`)."""
    folder = os.path.dirname(pending)
    _reclaim_dead_copies(folder)
    return os.path.join(folder, f".copy.{os.getpid()}.{_copy_token()}.tmp")


def _reclaim_dead_copies(folder: str) -> None:
    """Remove from *folder* the copies (:data:`_COPY_NAME`) whose process is
    gone, once per folder in this process.

    A process killed between ``CopyFile2`` and the rename (every abort of a
    detached run is ``TerminateJobObject``) leaves a whole copy under a name
    no later run can derive, read-only when its source was. Only a name that
    is this shape, whose pid no process has any more, goes, and only as
    :func:`_discard` removes an entry: the entry itself, a plain file's
    read-only attribute cleared, never through a link. A live pid's copy (one
    in flight in another process, or a leftover whose pid was reused) stays;
    what cannot be removed stays too. Never raises."""
    key = os.path.abspath(folder)
    with _RECLAIMED_LOCK:
        if key in _RECLAIMED:
            return
        _RECLAIMED.add(key)
    try:
        names = os.listdir(folder)
    except OSError:
        return
    for name in names:
        match = _COPY_NAME.match(name)
        if match is None:
            continue
        pid = int(match.group(1))
        if pid == os.getpid() or process_alive(pid):
            continue
        try:
            _discard(os.path.join(folder, name))
        except (CopyNotContained, OSError):
            pass


def _copy_token() -> str:
    """A random token for one copy's name (:func:`_copy_name`)."""
    return secrets.token_hex(8)


def _written_through_handle(pending: str, data: bytes, info: os.stat_result) -> None:
    """:func:`write_copy`'s plain copy on Windows, where ``os.open``'s
    exclusive creation follows a link to nothing at the name
    (:data:`_EXCLUSIVE_OPEN_FOLLOWS_LINKS`): *pending* made as a new file and
    held through one handle (:meth:`_HeldCopyCalls.create`: ``CREATE_NEW``
    with ``FILE_FLAG_OPEN_REPARSE_POINT``, on the name itself, failing on
    any name there, a link included, never following it), *data* written
    through it, and the source's times and read-only attribute (*info*, its
    ``fstat`` after the read) set through it as ``copystat``'s ``os.utime``
    and ``os.chmod`` give them there, all before it closes: nothing is set
    by path, where the name can be swapped for a link between two calls. A
    name already at *pending* is removed first (:func:`_discard`), never
    followed, and the creation tried once more. What a failure leaves is
    removed as :func:`write_copy` removes it. Raises ``OSError`` when the
    handle calls cannot be loaded: nothing is then copied, as ``os.open``
    could write through a link."""
    calls = _held_copy_calls()
    if calls is None:
        raise OSError(
            f"the Windows calls that create {pending} without following a link "
            f"could not be loaded, so nothing was copied")
    try:
        held = calls.create(pending)
    except FileExistsError:
        _discard(pending)
        held = calls.create(pending)
    created: Optional[Tuple[int, int]] = None
    disposed = False
    try:
        try:
            opened = os.fstat(held)
            created = (opened.st_dev, opened.st_ino)
            view = memoryview(data)
            while view:
                view = view[os.write(held, view):]
            calls.set_basic(held, _copied_attributes(opened, info),
                            info.st_atime_ns, info.st_mtime_ns)
        except BaseException:
            # Deleted through the handle that made it, as it closes: no name
            # to look up again, where a swap could stand by then.
            try:
                calls.dispose(held)
                disposed = True
            except Exception:  # noqa: BLE001 - removed by name below instead
                pass
            raise
        finally:
            os.close(held)
    except BaseException as failure:
        if not disposed:
            _discard_after(failure, pending, created)
        raise


def _copied_attributes(made: os.stat_result, info: os.stat_result) -> int:
    """The attributes a plain copy made on Windows (*made*, its handle's
    ``fstat``) takes from its source (*info*): its own, with the read-only
    one set or cleared as the source's mode says, as ``os.chmod`` sets it
    for ``copystat`` there (``SetFileAttributesW`` with the other attributes
    kept)."""
    attributes = getattr(made, "st_file_attributes", 0) & _SETTABLE_ATTRIBUTES
    if info.st_mode & stat.S_IWRITE:
        attributes &= ~stat.FILE_ATTRIBUTE_READONLY
    else:
        attributes |= stat.FILE_ATTRIBUTE_READONLY
    return attributes or _FILE_ATTRIBUTE_NORMAL


def _copied_unchanged(path: str, pending: str, data: bytes, source: int,
                      made: List[Tuple[int, int]]) -> bool:
    """Whether *pending* is the plain new file ``CopyFile2`` made of *path*,
    *path* is still the file the descriptor *source* reads, and *pending*
    holds exactly *data*, the bytes read through *source*. *made* gets
    *pending*'s ``(st_dev, st_ino)`` once it is known to name the file read
    back. Raises :class:`CopyNotContained` when *pending* is not a plain file
    once the copy was made: a link there may have taken the copy elsewhere."""
    named = os.lstat(pending)
    if not _plain_new_file(named):
        raise CopyNotContained(pending, _not_the_copy(pending, named))
    handle = os.open(pending, _READ_FLAGS | getattr(os, "O_NOFOLLOW", 0))
    try:
        opened = os.fstat(handle)
        if not _names_file(pending, opened):
            return False
        made.append((opened.st_dev, opened.st_ino))
        if not _names_file(path, os.fstat(source)):
            return False
        return read_capped(handle, len(data)) == data
    finally:
        os.close(handle)


def _plain_new_file(named: os.stat_result) -> bool:
    """Whether a name's own entry (*named*, its ``lstat``) is what a copy
    just made is: a regular file with no other name and no reparse point."""
    return (stat.S_ISREG(named.st_mode) and named.st_nlink == 1
            and not getattr(named, "st_file_attributes", 0)
            & stat.FILE_ATTRIBUTE_REPARSE_POINT)


def _not_the_copy(pending: str, named: os.stat_result) -> str:
    """Why *pending* (``lstat`` *named*) is not the copy just made there."""
    if stat.S_ISLNK(named.st_mode) or (
            getattr(named, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT):
        try:
            target = os.readlink(pending)
        except OSError:
            return (f"{pending} was a reparse point once the copy was made, so "
                    f"the copy may have been written wherever it leads")
        return (f"{pending} was a link to {target} once the copy was made, so "
                f"the copy may have been written there")
    return f"{pending} was not a plain new file once the copy was made"


def _spelled_plainly(path: str) -> bool:
    """Whether *path* has no ``.`` or ``..`` component and no trailing
    separator. Spelled so, a path can name another file than its lexically
    normalised form, the one the descriptor walk opens: ``src/a.py/`` names
    no file (a directory that is not there), ``src/link/../a.py`` names what
    lies beside the link's target. The resolving check
    (:meth:`WritePolicy.violation`) drops a trailing separator and takes
    ``..`` after the link before it, so it can permit such a spelling for
    another file than the walk would open. Refused instead, the answer never
    rests on how the caller spells a path (the census never spells one so)."""
    separators = os.sep + (os.altsep or "")
    if not path or path[-1] in separators:
        return False
    parts = re.split("[" + re.escape(separators) + "]", path)
    return os.curdir not in parts and os.pardir not in parts


def _names_file(path: str, opened: os.stat_result) -> bool:
    """Whether *path*'s own entry, never followed, is a regular file and the
    one *opened* (a descriptor's ``fstat``) describes."""
    try:
        named = os.lstat(path)
    except OSError:
        return False
    return stat.S_ISREG(named.st_mode) and (
        (named.st_dev, named.st_ino) == (opened.st_dev, opened.st_ino)
    )


def _discard(path: str, made: Optional[Tuple[int, int]] = None) -> None:
    """Remove *path*'s own entry, never what a link there names, if there is
    one; raise :class:`CopyNotContained` when something is left there.

    *made*, the ``(st_dev, st_ino)`` of the file this pass made there, must
    still be what the name holds; otherwise that file has gone elsewhere and
    nothing is removed. Windows will not delete a read-only file, and
    ``CopyFile2`` copies the attribute from the source, so when the removal
    is refused the attribute is cleared and the removal tried once more
    (:func:`_clear_readonly`)."""
    try:
        named = os.lstat(path)
    except FileNotFoundError:
        return
    except OSError as exc:
        raise CopyNotContained(path, f"{path} could not be examined ({exc})") from exc
    if made is not None and (named.st_dev, named.st_ino) != made:
        raise CopyNotContained(
            path, f"{path} no longer held the copy made there, so that copy "
                  f"could not be removed")
    error = _unlink(path)
    if error is not None and _clear_readonly(path, named):
        error = _unlink(path)
    if error is not None:
        raise CopyNotContained(path, f"{path} could not be removed ({error})") from error


def _discard_after(failure: BaseException, pending: str,
                   made: Optional[Tuple[int, int]]) -> None:
    """:func:`_discard` *pending* once a copy to it failed with *failure*.
    What cannot be removed is raised as :class:`CopyNotContained`, chained
    to *failure*; an interrupt goes on as it is."""
    try:
        _discard(pending, made)
    except CopyNotContained as left:
        if isinstance(failure, Exception):
            raise left from failure


def _unlink(path: str) -> Optional[OSError]:
    """Remove the entry *path* (a link itself, never its target); the error
    when it stays."""
    try:
        os.unlink(path)
    except FileNotFoundError:
        return None
    except OSError as exc:
        return exc
    return None


def _clear_readonly(path: str, named: os.stat_result) -> bool:
    """Clear the read-only attribute of *path*'s own entry, *named* its
    ``lstat`` (Windows); whether it was cleared. Only for a plain file
    (:func:`_plain_new_file`): no reparse point, and no other name, whose
    file's attribute would change too. Set on the entry itself: ``os.chmod``
    without following (3.13+) and 3.12's ``os.chmod`` are both
    ``SetFileAttributesW`` on the path, the call CPython makes for
    ``lchmod`` there."""
    if not (getattr(named, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_READONLY
            and _plain_new_file(named)):
        return False
    try:
        if os.chmod in os.supports_follow_symlinks:
            os.chmod(path, stat.S_IREAD | stat.S_IWRITE, follow_symlinks=False)
        else:  # pragma: no cover - Windows before 3.13
            os.chmod(path, stat.S_IREAD | stat.S_IWRITE)
    except OSError:
        return False
    return True


def _copy_times_and_mode(target: Any, info: os.stat_result) -> None:
    """``shutil.copystat``'s times, then mode (in its order), onto *target*:
    a descriptor, or a path where descriptors take neither."""
    os.utime(target, ns=(info.st_atime_ns, info.st_mtime_ns))
    os.chmod(target, stat.S_IMODE(info.st_mode))


def _copy_xattrs(source: int, target: int) -> None:
    """``shutil.copystat``'s extended attributes, descriptor to descriptor,
    skipping what it skips; a no-op where there are none (macOS, Windows)."""
    if not hasattr(os, "listxattr"):  # pragma: no cover - macOS, Windows
        return
    try:
        names = os.listxattr(source)
    except OSError as exc:
        if exc.errno not in (errno.ENOTSUP, errno.ENODATA, errno.EINVAL):
            raise
        return
    for name in names:
        try:
            os.setxattr(target, name, os.getxattr(source, name))
        except OSError as exc:
            if exc.errno not in (errno.EPERM, errno.ENOTSUP, errno.ENODATA,
                                 errno.EINVAL, errno.EACCES):
                raise


# ---------------------------------------------------------------------------
# D3l — the declared write policy
# ---------------------------------------------------------------------------

def glob_to_regex(pattern: str) -> "re.Pattern[str]":
    """Translate a ``write_paths`` glob into an anchored regex over POSIX paths.

    ``**/`` spans zero or more directories (so ``**/.env`` matches both ``.env``
    and ``a/b/.env``), ``**`` spans anything, ``*`` and ``?`` stop at a separator.
    Hand-rolled rather than ``fnmatch`` because ``fnmatch``'s ``*`` crosses ``/``,
    which would make ``**/node_modules/**`` and ``*.pem`` mean the same thing.
    """
    text = pattern.replace("\\", "/")
    # Strip a leading "./" PREFIX only — `str.lstrip("./")` strips leading
    # characters, which silently turned `.git/**` into `git/**` and let every
    # `.git` write through the deny list.
    while text.startswith("./"):
        text = text[2:]
    out: List[str] = ["^"]
    index = 0
    while index < len(text):
        char = text[index]
        if text.startswith("**/", index):
            out.append("(?:.*/)?")
            index += 3
            continue
        if text.startswith("**", index):
            out.append(".*")
            index += 2
            continue
        if char == "*":
            out.append("[^/]*")
        elif char == "?":
            out.append("[^/]")
        else:
            out.append(re.escape(char))
        index += 1
    out.append("$")
    return re.compile("".join(out))


#: The pre-rename spelling, kept for callers that imported it.
_glob_to_regex = glob_to_regex


#: Where the user's own ``driver.write_paths`` lives, as every way-forward
#: line names it.
POLICY_FILE = ".multi-llm/providers.yaml"


def describe_paths(paths: Sequence[str], limit: int = 3) -> str:
    """``a``, ``a and b``, ``a, b and c``, ``a, b, c and 2 more``."""
    names = [str(path) for path in paths if str(path)]
    if not names:
        return "the file it declares"
    if len(names) > limit:
        return f"{', '.join(names[:limit])} and {len(names) - limit} more"
    if len(names) == 1:
        return names[0]
    return f"{', '.join(names[:-1])} and {names[-1]}"


@dataclass(frozen=True)
class PolicyHit:
    """One file ``driver.write_paths`` refuses, and which of its rules do.

    The way forward said
    "allow it in driver.write_paths" for every refusal, while the deny list
    wins over ``allow`` — so for a deny hit, adding the file to ``allow``
    resumed into the same refusal with the same advice. The way forward is
    now worded from what refused each file: *deny* is every deny pattern
    that covers it (each must be removed or narrowed), *allowed* whether an
    ``allow`` pattern matches it (when not, it must be added), and
    *outside* a path outside the repository, which no rule can allow.
    *path* is repo-relative, or, outside the repository, as the task
    declared it (never resolved to an absolute path).

    *protected* is the rule text of :attr:`WritePolicy.exact_deny` when that
    layer refuses the path, ``""`` otherwise. No
    ``driver.write_paths`` change lets such a write through, so the way
    forward never offers one (:func:`policy_allow_clause`).
    """

    path: str
    deny: Tuple[str, ...] = ()
    allowed: bool = True
    outside: bool = False
    protected: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """The stop record's entry (``policy_rules``)."""
        if self.outside:
            return {"path": self.path, "outside": True}
        entry: Dict[str, Any] = {
            "path": self.path, "deny": list(self.deny), "allowed": self.allowed,
        }
        if self.protected:
            entry["protected"] = self.protected
        return entry

    @classmethod
    def from_dict(cls, data: Any) -> Optional["PolicyHit"]:
        """The entry back, or ``None`` for one that cannot be read."""
        if not isinstance(data, dict) or not str(data.get("path") or ""):
            return None
        if data.get("outside"):
            return cls(path=str(data["path"]), outside=True)
        deny = data.get("deny")
        return cls(
            path=str(data["path"]),
            deny=tuple(str(p) for p in deny) if isinstance(deny, list) else (),
            allowed=bool(data.get("allowed", True)),
            protected=str(data.get("protected") or ""),
        )


def policy_hits(entries: Iterable[Any]) -> List[PolicyHit]:
    """:class:`PolicyHit` entries from hits or their recorded dicts."""
    hits: List[PolicyHit] = []
    for entry in entries or ():
        hit = entry if isinstance(entry, PolicyHit) else PolicyHit.from_dict(entry)
        if hit is not None:
            hits.append(hit)
    return hits


def _quoted_rules(patterns: Sequence[str]) -> str:
    quoted = [f"`{pattern}`" for pattern in patterns]
    if len(quoted) == 1:
        return quoted[0]
    return f"{', '.join(quoted[:-1])} and {quoted[-1]}"


#: How many deny rules a way forward names one by one; the rest are counted.
POLICY_RULES_SHOWN = 3


def policy_allow_clause(refused: Sequence[Any]) -> Optional[str]:
    """The way past a write ``driver.write_paths`` refused that changes the
    policy, worded as the user's own call and per rule: ``if you want <paths>
    written, remove or narrow the deny rule `<pattern>` in driver.write_paths
    (.multi-llm/providers.yaml) so it no longer covers <paths>`` for a deny
    hit, ``… add <paths> to driver.write_paths.allow (…)`` for an allow miss,
    each refused file under its own rule. ``None`` when a refused file is
    outside the repository: no policy change lets the task run, and the
    way forward is the skip alone (:func:`policy_outside_note`).

    *refused* holds :class:`PolicyHit` entries (or their recorded dicts).
    Plain path strings, and a recorded dict that kept no rule, get the wording
    that is right for either rule.

    The plugin keeps offering the policy change, since it is the user's to
    decide and it lets the run complete, but plainly as their choice, naming
    the file. A deny hit names the deny rule to narrow (the deny list wins
    over ``allow``, so "allow it" would resume into the same refusal). Every stop,
    refusal and status line that offers it says it in these words, and the
    hosts relay it as given and never change the policy themselves
    (``modes.STOP_POLICY_RULE``).
    """
    entries = list(refused or ())
    plain = [str(e) for e in entries if isinstance(e, str) and str(e)]
    hits = policy_hits(e for e in entries if not isinstance(e, str))
    if any(hit.outside or hit.protected for hit in hits):
        # Neither a path outside the repository nor one the commit review
        # protects is a driver.write_paths matter: no rule change
        # lets the write through (:func:`policy_outside_note` says why).
        return None
    where = f"driver.write_paths ({POLICY_FILE})"
    if plain or not hits:
        names = plain + [hit.path for hit in hits]
        it = "it" if len(names) <= 1 else "them"
        return (
            f"if you want {describe_paths(names)} written, change {where} so "
            f"it allows {it}: add {it} to `allow`, and remove or narrow any "
            f"deny rule that covers {it}"
        )
    groups: Dict[Tuple[str, ...], List[str]] = {}
    for hit in hits:
        if hit.deny:
            groups.setdefault(tuple(hit.deny), []).append(hit.path)
    unallowed = [hit.path for hit in hits if not hit.allowed]
    actions: List[str] = []
    shown_rules = 0
    hidden: List[str] = []
    hidden_paths: List[str] = []
    for patterns, paths in groups.items():
        if shown_rules >= POLICY_RULES_SHOWN:
            hidden += [p for p in patterns if p not in hidden]
            hidden_paths += [p for p in paths if p not in hidden_paths]
            continue
        shown_rules += len(patterns)
        many = len(patterns) > 1
        # Every file the clause opens with: "covers it", not the list again
        # (the stop's headline has a budget, `fit_stop_headline`).
        covered = (
            ("it" if len(paths) == 1 else "them")
            if len(paths) == len(hits) else describe_paths(paths)
        )
        actions.append(
            f"remove or narrow the deny rule{'s' if many else ''} "
            f"{_quoted_rules(patterns)} in {where if not actions else 'driver.write_paths'} "
            f"so the rule{'s' if many else ''} no longer cover{'' if many else 's'} "
            f"{covered}"
        )
    if hidden:
        many = len(hidden) > 1
        actions.append(
            f"remove or narrow the {len(hidden)} other deny rule"
            f"{'s' if many else ''} that cover{'' if many else 's'} "
            f"{describe_paths(hidden_paths)} (the refusal's details name "
            f"{'each' if many else 'it'})"
        )
    if unallowed:
        # Every file the clause opens with: "add it", not the list again.
        named = (
            ("it" if len(hits) == 1 else "them")
            if len(unallowed) == len(hits) else describe_paths(unallowed)
        )
        actions.append(
            f"add {named} to driver.write_paths.allow"
            + (f" ({POLICY_FILE})" if not actions else "")
        )
    if len(actions) > 1:
        done = f"{', '.join(actions[:-1])}, and {actions[-1]}"
    else:
        done = actions[0] if actions else f"change {where}"
    return f"if you want {describe_paths([hit.path for hit in hits])} written, {done}"


def policy_outside_note(refused: Sequence[Any]) -> str:
    """Why no policy change can let a task run: ``../x is
    outside the repository, so no driver.write_paths rule can allow it``,
    naming each such file as the task declared it.

    A file the commit review protects (:attr:`PolicyHit.protected`) gets
    :func:`protected_note`'s clause
    instead, after the outside one when there are both; with neither the
    note reads exactly as before."""
    hits = policy_hits(e for e in (refused or ()) if not isinstance(e, str))
    outside = [hit.path for hit in hits if hit.outside]
    protected = [hit for hit in hits if hit.protected and not hit.outside]
    parts: List[str] = []
    if outside or not protected:
        one = len(outside) <= 1
        parts.append(
            f"{describe_paths(outside)} {'is' if one else 'are'} outside the "
            f"repository, so no driver.write_paths rule can allow "
            f"{'it' if one else 'them'}"
        )
    if protected:
        parts.append(protected_note(protected))
    return "; ".join(parts)


#: The exact-path deny layer's rule text for the commit review's context
#: plan: read-only whether or not it differs from the reviewed head.
CONTEXT_PLAN_RULE = "the context plan, read-only in this review"


def protected_note(hits: Sequence[Any]) -> str:
    """The clause naming the files the commit review protects: ``the commit review protects src/b.py, which
    changed since reviewed commit abc1234: this apply never writes it, so
    make that change by hand, or review a range that ends at HEAD``. One
    clause per distinct rule text (one reviewed head in practice). The
    context plan (:data:`CONTEXT_PLAN_RULE`) gets its own ways forward."""
    by_rule: Dict[str, List[str]] = {}
    for hit in policy_hits(e for e in (hits or ()) if not isinstance(e, str)):
        if hit.protected:
            by_rule.setdefault(hit.protected, []).append(hit.path)
    clauses: List[str] = []
    for rule, paths in by_rule.items():
        one = len(paths) == 1
        if rule == CONTEXT_PLAN_RULE:
            clauses.append(
                f"{describe_paths(paths)} {'is' if one else 'are'} the context "
                f"plan this commit review checks the commits against, read-only "
                f"in this review: this apply never writes "
                f"{'it' if one else 'them'}, so edit {'it' if one else 'them'} "
                f"by hand, or review again with --context-plan \"\" so "
                f"{'it is an ordinary file' if one else 'they are ordinary files'}"
            )
            continue
        clauses.append(
            f"the commit review protects {describe_paths(paths)}, which "
            f"{rule}: this apply never writes {'it' if one else 'them'}, so "
            f"make that change by hand, or review a range that ends at HEAD "
            f"so the review reads {'it' if one else 'them'} as "
            f"{'it is' if one else 'they are'} now"
        )
    return "; ".join(clauses)


def policy_skip_clause(task_id: str, *, alone: bool = False) -> str:
    """The way past an implement task the policy refused that leaves it
    undone, beside :func:`policy_allow_clause`: ``if not, skip T005: …``.
    *alone* drops the ``if not,`` for a refusal no policy change answers
    (a file outside the repository)."""
    return (
        ("" if alone else "if not, ")
        + f"skip {task_id}: add --human-task {task_id}=skip to the "
        f"resume command ({task_id} and the tasks after it stay undone)"
    )


def policy_way_forward(refused: Sequence[Any], *, then: str = "resume") -> str:
    """:func:`policy_allow_clause` and *then*, or, when no policy change can
    let the task run, :func:`policy_outside_note` — the sentence every
    refusal ends with (``WritePolicy.check``'s message)."""
    clause = policy_allow_clause(refused)
    if clause is None:
        note = policy_outside_note(refused)
        return f"{note[0].upper()}{note[1:]}."
    return f"Your call: {clause}, then {then}."


def _exact_key(path: str) -> str:
    """*path* as an :attr:`WritePolicy.exact_deny` key: forward slashes, no
    leading ``./``, normalized, never resolved (a symlink is its own path)."""
    text = str(path).replace(os.sep, "/")
    while text.startswith("./"):
        text = text[2:]
    return posixpath.normpath(text) if text else ""


@dataclass
class WritePolicy:
    """``driver.write_paths``, resolved against the pinned repo root (D3l).

    *exact_deny* is a second deny layer of exact repo-relative paths, each
    with the rule text a refusal names. It is the commit review's protected
    set (every path
    that differed from the reviewed ``head`` when the apply guard ran, plus
    the fix files a pre-dispatch re-check found changed since), so a fix
    batch that writes one fails exactly as a ``driver.write_paths`` deny hit
    does: refused before dispatch when declared, failed, restored and the
    loop stopped when observed after the run. It is not part of the user's
    configuration and never comes from it (:meth:`load` leaves it empty);
    the scheduler adds it from the guard (:meth:`deny_exact`). Empty, every
    answer here is what it was before the layer existed.
    """

    root: str
    allow: List[str] = field(default_factory=list)
    deny: List[str] = field(default_factory=list)
    exact_deny: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def load(cls, root: str, *, anchor: Optional[str] = None) -> "WritePolicy":
        """Read the merged ``driver.write_paths`` through the typed accessor."""
        configured = get_write_paths(anchor=anchor)
        return cls(root=str(Path(root).resolve()),
                   allow=list(configured["allow"]),
                   deny=list(configured["deny"]))

    def __post_init__(self) -> None:
        self._allow = [_glob_to_regex(p) for p in self.allow]
        self._deny = [_glob_to_regex(p) for p in self.deny]
        self.exact_deny = {
            _exact_key(path): str(rule)
            for path, rule in dict(self.exact_deny or {}).items()
            if _exact_key(path)
        }
        #: ``(root, realpath(root))`` for :meth:`open_permitted`'s walk.
        self._resolved_root: Optional[Tuple[str, str]] = None

    def deny_exact(self, paths: Iterable[str], rule: str) -> List[str]:
        """Add *paths* (repo-relative, git's form) to the exact-path deny
        layer with *rule* as their refusal's text; the keys newly added. A
        path already in the layer keeps its first rule."""
        added: List[str] = []
        for path in paths or ():
            key = _exact_key(path)
            if key and key not in self.exact_deny:
                self.exact_deny[key] = str(rule)
                added.append(key)
        return added

    def exact_match(self, path: str) -> Optional[Tuple[str, str]]:
        """``(key, rule text)`` of the :attr:`exact_deny` entry that refuses
        *path*, or ``None``.

        Matched first on the path as given (made repo-relative without
        resolving it, so a protected symlink is refused by its own name),
        then on its resolved repo-relative form (so an absolute path through
        a symlinked checkout matches too). *key* is the entry's own path,
        which is what a hit is named by (:meth:`hit`): resolving a protected
        symlink a batch re-pointed names its target, often the batch's own
        fix file, and the restore would then undo that file and leave the
        link as the batch left it."""
        if not self.exact_deny:
            return None
        text = str(path)
        keys = []
        if os.path.isabs(text):
            try:
                keys.append(_exact_key(os.path.relpath(text, self.root)))
            except ValueError:  # pragma: no cover - another drive on Windows
                pass
        else:
            keys.append(_exact_key(text))
        keys.append(_exact_key(relative_to_root(text, self.root)))
        for key in keys:
            rule = self.exact_deny.get(key)
            if rule:
                return key, rule
        return None

    def exact_rule(self, path: str) -> Optional[str]:
        """The :attr:`exact_deny` rule text that refuses *path*, or ``None``
        (:meth:`exact_match`)."""
        matched = self.exact_match(path)
        return matched[1] if matched else None

    def denied(self, path: str, *, exact: bool = True) -> Optional[str]:
        """The deny-side rule ``path`` hits, or ``None``: the deny list alone.

        A path outside the pinned root counts as denied here too — nothing
        outside the root is ever harmless to an executor artifact. What this
        deliberately does **not** ask is whether an ``allow`` pattern matches:
        the sweep's "gitignored and harmless" drop needs exactly that
        distinction (adversarial review, 2026-10-02: under ``allow:
        ["src/**"]`` an ignored ``logs/run.jsonl`` failed :meth:`violation` on
        the allow side, stayed in the sweep and became the policy violation
        #22 was fixed for), while :meth:`violation` keeps asking both.

        *exact* (the default) also asks the :attr:`exact_deny` layer, after
        the deny patterns; ``exact=False`` asks ``driver.write_paths`` alone,
        which is what decides whether an executor artifact may hold a copy
        of the file's bytes (a protected file is ordinary code, and its
        rollback point is what lets the post-run check restore it).
        """
        relative = relative_to_root(path, self.root)
        if _outside_root(relative):
            return f"outside the pinned repo root {self.root}"
        rule = self._deny_rule(relative)
        if rule is not None:
            return rule
        if exact:
            return self.exact_rule(path)
        return None

    def violation(self, path: str, *, exact: bool = True) -> Optional[str]:
        """The rule ``path`` violates, or ``None`` when the policy permits it.

        Deny wins: a path matched by both lists is denied, because the deny list is
        the statement of what a code-editing batch has no business touching and an
        ``allow: ["**"]`` default would otherwise neutralize it entirely.
        *exact* is :meth:`denied`'s.
        """
        denied = self.denied(path, exact=exact)
        if denied is not None:
            return denied
        return self._allow_rule(relative_to_root(path, self.root))

    def violation_relative(self, relative: str) -> Optional[str]:
        """``violation(path, exact=False)`` for the repo-relative POSIX
        *relative* as it stands, never resolved.

        Only for a path the caller reached from the root without following a
        link (:meth:`open_permitted`): resolving it again would ask about
        wherever a link swapped in since leads, not about the file in hand.
        """
        if _outside_root(relative):
            return f"outside the pinned repo root {self.root}"
        return self._deny_rule(relative) or self._allow_rule(relative)

    def _deny_rule(self, relative: str) -> Optional[str]:
        """The first deny pattern matching the repo-relative *relative*, named."""
        for pattern, matcher in zip(self.deny, self._deny):
            if matcher.match(relative):
                return f"driver.write_paths.deny pattern {pattern!r}"
        return None

    def _allow_rule(self, relative: str) -> Optional[str]:
        """Why no allow pattern admits the repo-relative *relative*, or ``None``."""
        if not self._allow:
            return "driver.write_paths.allow is empty, so nothing may be written"
        for matcher in self._allow:
            if matcher.match(relative):
                return None
        return (
            f"no driver.write_paths.allow pattern matches it "
            f"(allow: {', '.join(self.allow)})"
        )

    def open_permitted(self, path: str) -> Optional[Tuple[int, os.stat_result]]:
        """A read-only descriptor of the regular file at *path*, and its
        ``fstat``, when the file that descriptor reads is one
        ``violation(path, exact=False)`` permits; ``None`` otherwise. The
        caller closes the descriptor.

        The check is bound to the descriptor, not to an earlier look at the
        path: whatever *path* resolved to a moment ago, the descriptor is what
        gets read (docs/development/write-safety.md, the rollback store's
        reads).

        * Where :data:`OPENS_WITHOUT_FOLLOWING` (Linux, macOS), *path* is taken
          lexically below the root and each component is opened through its
          parent's descriptor, never through a link. The file opened is the one
          at that repo-relative path, so the policy is asked about the path
          itself (:meth:`violation_relative`). A link anywhere below the root
          is refused, never followed.
        * Elsewhere (Windows: no ``dir_fd``, no ``O_NOFOLLOW``) the file is
          opened by path, then asked about again by :meth:`violation`, which
          resolves, and the path's own entry must then be a regular file with
          the descriptor's ``(st_dev, st_ino)`` (``lstat`` against ``fstat``,
          as ``result_files.read_regular_text`` checks). A link at the file's
          own name is refused whenever it was there; what this cannot see is a
          directory junction above the file that is there for the open, gone
          for the resolving check and back for the identity check.

        Either way a path spelled with a ``.`` or ``..`` component or a
        trailing separator is refused (:func:`_spelled_plainly`), so the
        answer never depends on how the caller spells a path.
        """
        if not _spelled_plainly(path):
            return None
        joined = path if os.path.isabs(path) else os.path.join(self.root, path)
        if not OPENS_WITHOUT_FOLLOWING:
            return self._open_by_path(joined)
        # The root as `violation` sees it (resolved), once per root.
        if self._resolved_root is None or self._resolved_root[0] != self.root:
            self._resolved_root = (self.root, os.path.realpath(self.root))
        root = self._resolved_root[1]
        relative = os.path.relpath(joined, root)
        parts = relative.split(os.sep)
        if (relative == os.curdir or os.pardir in parts or "" in parts
                or self.violation_relative("/".join(parts)) is not None):
            return None
        handle = _open_below_root(root, parts)
        if handle is None:
            return None
        try:
            opened = os.fstat(handle)
            if stat.S_ISREG(opened.st_mode):
                return handle, opened
        except OSError:
            pass
        os.close(handle)
        return None

    def _open_by_path(self, path: str) -> Optional[Tuple[int, os.stat_result]]:
        """:meth:`open_permitted` where a path cannot be walked by descriptor."""
        try:
            handle = os.open(path, _READ_FLAGS)
        except OSError:
            return None
        try:
            opened = os.fstat(handle)
            if (stat.S_ISREG(opened.st_mode)
                    and self.violation(path, exact=False) is None
                    and _names_file(path, opened)):
                return handle, opened
        except OSError:
            pass
        os.close(handle)
        return None

    def hit(self, path: str) -> Optional[PolicyHit]:
        """``path``'s :class:`PolicyHit`, or ``None`` when the policy permits
        it: every deny pattern that covers it and whether ``allow`` matches
        it, so the way forward names each rule to change.

        A hit the :attr:`exact_deny` layer refuses is named by the entry it
        matched (:meth:`exact_match`), never by the resolved path: the
        executor restores what a violation names, so a protected symlink is
        restored as the link itself, from what the guard kept of it, and
        its target is left alone (review R2, item 3)."""
        relative = relative_to_root(path, self.root)
        if _outside_root(relative):
            return PolicyHit(path=str(path), outside=True)
        deny = tuple(
            pattern for pattern, matcher in zip(self.deny, self._deny)
            if matcher.match(relative)
        )
        allowed = any(matcher.match(relative) for matcher in self._allow)
        matched = self.exact_match(path)
        protected = matched[1] if matched else ""
        if not deny and allowed and not protected:
            return None
        return PolicyHit(path=matched[0] if matched else relative, deny=deny,
                         allowed=allowed, protected=protected)

    def check(self, paths: Iterable[str], *, when: str) -> None:
        """Raise :class:`PolicyViolation` naming every offender and its rule.

        Each offender is named repo-relative, or, outside the repository, as
        given (a task's ``../x`` was named by its resolved
        absolute path, in the way forward and every record of it).
        """
        offenders: List[Tuple[str, str]] = []
        hits: List[PolicyHit] = []
        for path in paths:
            rule = self.violation(path)
            if rule is not None:
                hit = self.hit(path) or PolicyHit(path=relative_to_root(path, self.root))
                offenders.append((hit.path, rule))
                hits.append(hit)
        if not offenders:
            return
        detail = "; ".join(f"{path} ({rule})" for path, rule in offenders)
        named = [path for path, _ in offenders]
        checked = (
            "driver.write_paths and the commit review's protected paths are"
            if any(hit.protected for hit in hits) else "driver.write_paths is"
        )
        raise PolicyViolation(
            f"Write policy violation ({when}): {detail}. Repo root: {self.root}. "
            f"{checked} checked before dispatch and after the run. "
            f"{policy_way_forward(hits)}",
            paths=named,
            rule=offenders[0][1],
            hits=hits,
        )

    def to_dict(self) -> Dict[str, Any]:
        record: Dict[str, Any] = {
            "root": self.root, "allow": list(self.allow), "deny": list(self.deny),
        }
        if self.exact_deny:
            record["protected"] = dict(sorted(self.exact_deny.items()))
        return record


# ---------------------------------------------------------------------------
# D3h/D3g — the pre-batch snapshot, which is also the verdict
# ---------------------------------------------------------------------------

@dataclass
class SnapshotEntry:
    """One snapshotted file: where it was, what it hashed to, where the copy is.

    ``declared`` separates the two ways an entry gets here: ``take`` records the
    batch's declared set, :meth:`TaskSnapshot.adopt` records a write the post-run
    sweep observed outside it. Both are restorable; only the first was ever
    promised, so the classification's prose must not confuse them.
    """

    relative: str
    absolute: str
    existed: bool
    sha256: Optional[str]
    size: int
    payload: Optional[str]
    declared: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.relative,
            "absolute": self.absolute,
            "existed": self.existed,
            "sha256_before": self.sha256,
            "size_before": self.size,
            "payload": self.payload,
            "declared": self.declared,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SnapshotEntry":
        return cls(
            relative=str(data.get("path", "")),
            absolute=str(data.get("absolute", "")),
            existed=bool(data.get("existed")),
            sha256=data.get("sha256_before"),
            size=int(data.get("size_before") or 0),
            payload=data.get("payload"),
            # Absent in a v1 manifest, where every entry was a declared file.
            declared=bool(data.get("declared", True)),
        )


def _open_declared(resolved: Path, resolved_root: Path, relative: str,
                   task_id: str) -> Optional[Tuple[int, os.stat_result]]:
    """A read-only descriptor of the declared file *resolved* and its
    ``fstat``, for :meth:`TaskSnapshot.take` to read once; ``None`` when no
    regular file is there (absent, a directory: nothing to snapshot).

    *resolved* is :func:`contain_under_root`'s answer, below *resolved_root*
    with every link resolved, and *relative* its path below it. Where the
    platform can (:data:`OPENS_WITHOUT_FOLLOWING`), it is opened one
    component at a time from the root, never through a link
    (:func:`_open_below_root`, the walk the rollback store's reads take);
    elsewhere by path, and its own entry must then be the file opened
    (``lstat`` against ``fstat``). The check resolved every link, so a link
    found now, or a file that cannot be opened, was put there since: refused
    (:class:`WriteSafetyError`), nothing is dispatched
    (docs/development/write-safety.md, the rollback store's reads)."""
    parts = list(PurePosixPath(relative).parts)
    handle: Optional[int] = None
    if parts and OPENS_WITHOUT_FOLLOWING:
        handle = _open_below_root(str(resolved_root), parts)
    elif parts:
        try:
            handle = os.open(str(resolved), _READ_FLAGS)
        except OSError:
            handle = None
    if handle is not None:
        try:
            info = os.fstat(handle)
        except OSError:
            info = None
        if info is not None and stat.S_ISREG(info.st_mode) and (
                OPENS_WITHOUT_FOLLOWING or _names_file(str(resolved), info)):
            return handle, info
        os.close(handle)
        if info is not None and not stat.S_ISREG(info.st_mode):
            return None
    try:
        named = os.lstat(str(resolved))
    except (FileNotFoundError, NotADirectoryError):
        return None
    except OSError as exc:
        named, why = None, str(exc)
    else:
        why = ""
    if named is not None and not (stat.S_ISREG(named.st_mode) or stat.S_ISLNK(named.st_mode)
                                  or _names_another_path(named)):
        return None
    raise WriteSafetyError(
        f"Refusing to dispatch task {task_id}: {relative} could not be opened "
        f"for its pre-batch snapshot without following a link"
        + (f" ({why})" if why else "")
        + ": a link was put there after its containment check, or the file "
        "cannot be read. A batch with no rollback point is not dispatched (D3h)."
    )


@dataclass
class TaskSnapshot:
    """The mandatory pre-batch snapshot for one write task (D3h).

    Lives at ``{phase_dir}/pre_batch/{task_id}/`` with a ``manifest.json`` and a
    ``files/`` payload dir. Deliberately **not** ``git``-based: the artifact an
    apply batch edits is frequently untracked, which every ``git diff`` variant
    silently reports as unchanged — the exact failure mode that would make a clean
    failure read as success (D3g).
    """

    task_id: str
    directory: str
    root: str
    entries: List[SnapshotEntry] = field(default_factory=list)
    #: The items the batch was materialized for (its ``expected_ids``), so a
    #: resume can tell this batch's snapshot from one an earlier run took
    #: under the same positional id for other items. ``None`` for a manifest
    #: written before the key existed.
    expected_ids: Optional[List[str]] = None
    #: When the snapshot was taken (local, to the second), kept across
    #: re-saves; ``None`` until the first save or for a manifest without it.
    taken_at: Optional[str] = None

    # -- creation -------------------------------------------------------

    @classmethod
    def take(
        cls,
        *,
        phase_dir: str,
        task_id: str,
        files: Sequence[str],
        root: str,
        expected_ids: Optional[Sequence[str]] = None,
    ) -> "TaskSnapshot":
        """Snapshot ``files`` before dispatch. Every path is contained first.

        A snapshot is taken even for a file that does not exist yet: "absent
        before, present after" is the creation case, and recording the absence is
        what lets ``util restore-batch`` delete a file the batch created.

        Each file is read once, through a descriptor opened without following
        a link below the root (:func:`_open_declared`), and the payload is
        those bytes, hashed as read (:func:`write_copy`, the rollback store's
        writer): a link swapped in after the containment check, by a sibling
        batch still running, is refused and never read, so the payload never
        holds another file's bytes (docs/development/write-safety.md, the
        rollback store's reads).
        """
        directory = Path(safety_dir(phase_dir)) / PRE_BATCH_DIRNAME / _safe_component(task_id)
        payload_dir = directory / PAYLOAD_DIRNAME
        payload_dir.mkdir(parents=True, exist_ok=True)
        resolved_root = Path(root).resolve()
        entries: List[SnapshotEntry] = []
        for index, candidate in enumerate(files):
            resolved = contain_under_root(candidate, root, what="snapshot target")
            # Taken from the checked path itself, never resolved again: a
            # second resolution follows whatever link is there by now.
            relative = resolved.relative_to(resolved_root).as_posix()
            opened = _open_declared(resolved, resolved_root, relative, task_id)
            if opened is None:
                entries.append(SnapshotEntry(
                    relative=relative, absolute=str(resolved), existed=False,
                    sha256=None, size=0, payload=None,
                ))
                continue
            source, info = opened
            payload_name = f"{index:03d}-{_safe_component(relative)}"
            try:
                data = (read_capped(source, MAX_SNAPSHOT_BYTES, size_hint=info.st_size)
                        if info.st_size <= MAX_SNAPSHOT_BYTES else None)
                if data is None:
                    size = (f"is {info.st_size} bytes" if info.st_size > MAX_SNAPSHOT_BYTES
                            else "grew while it was read")
                    raise WriteSafetyError(
                        f"Refusing to dispatch task {task_id}: {relative} {size}, "
                        f"over the {MAX_SNAPSHOT_BYTES}-byte snapshot cap. A "
                        f"batch with no rollback point is not dispatched — every "
                        f"declared file must be snapshottable (D3h)."
                    )
                write_copy(str(payload_dir / payload_name), data, source,
                           path=str(resolved))
            finally:
                os.close(source)
            entries.append(SnapshotEntry(
                relative=relative,
                absolute=str(resolved),
                existed=True,
                sha256=hashlib.sha256(data).hexdigest(),
                size=len(data),
                payload=payload_name,
            ))
        snapshot = cls(task_id=task_id, directory=str(directory), root=str(root),
                       entries=entries,
                       expected_ids=(None if expected_ids is None
                                     else [str(i) for i in expected_ids]))
        snapshot.save()
        return snapshot

    def adopt(
        self,
        relative: str,
        *,
        existed: bool,
        sha256: Optional[str] = None,
        size: int = 0,
        payload_source: Optional[str] = None,
        save: bool = True,
    ) -> Optional[SnapshotEntry]:
        """Record a rollback point for a path the batch touched but never declared.

        ``take`` covers the declared set, and that set is the one thing the
        post-run policy check can never fail on — it passed the byte-identical
        pre-dispatch check. The paths that *can* fail it are the ones a runner
        wrote outside what it declared, and a violation the executor can name but
        not undo is half a control. The scheduler's containment sweep retains
        those files' pre-run bytes in a content-addressed store; adopting one
        here puts it in the same manifest :meth:`changed`, :meth:`restore` and
        ``util restore-batch`` already read, so an undeclared write rolls back
        exactly like a declared one.

        Args:
            payload_source: The retained pre-run bytes. Required, with the
                ``sha256`` they must hash to, when ``existed`` — an entry
                claiming a rollback point it has no copy for is worse than an
                honest ``None``, which is what this returns instead.
            save: Off when a caller adopts a batch of paths and saves once; the
                manifest is rewritten whole, so per-path saves are quadratic.

        Returns:
            The entry, or ``None`` when no rollback point could be recorded.
        """
        resolved = contain_under_root(relative, self.root, what="observed write")
        key = resolved.relative_to(Path(self.root).resolve()).as_posix()
        existing = self.entry_for(key)
        if existing is not None:
            return existing
        # `existed=False` needs no bytes at all: the rollback for a file the
        # runner created is deletion, which `restore` already does for an entry
        # with no payload.
        payload: Optional[str] = None
        if existed:
            if not payload_source or not sha256:
                return None
            # The retained bytes are content-addressed by `sha256`. The blob
            # is read once, through a descriptor that never follows a link at
            # its name (where the platform cannot refuse one at the open, the
            # name must be the file opened: `lstat` against `fstat`), and only
            # bytes that hash to it are copied: a blob rewritten after the
            # sweep retained it (the store sits where the batch can write), or
            # swapped for a link to another file, is no rollback point (review
            # fixes 2026-10-05; docs/development/write-safety.md, the rollback
            # store's reads).
            flags = _READ_FLAGS | (os.O_NOFOLLOW if OPENS_WITHOUT_FOLLOWING else 0)
            try:
                source = os.open(payload_source, flags)
            except OSError:
                return None
            try:
                info = os.fstat(source)
                data = (read_capped(source, MAX_SNAPSHOT_BYTES, size_hint=info.st_size)
                        if stat.S_ISREG(info.st_mode) and (
                            OPENS_WITHOUT_FOLLOWING
                            or _names_file(str(payload_source), info))
                        else None)
                if data is None or hashlib.sha256(data).hexdigest() != sha256:
                    return None
                payload = f"{len(self.entries):03d}-{_safe_component(key)}"
                payload_dir = Path(self.directory) / PAYLOAD_DIRNAME
                payload_dir.mkdir(parents=True, exist_ok=True)
                write_copy(str(payload_dir / payload), data, source,
                           path=str(payload_source))
            finally:
                os.close(source)
        entry = SnapshotEntry(
            relative=key,
            absolute=str(resolved),
            existed=existed,
            sha256=sha256,
            size=size,
            payload=payload,
            declared=False,
        )
        self.entries.append(entry)
        if save:
            self.save()
        return entry

    def declared_entries(self) -> List[SnapshotEntry]:
        """Only the entries ``take`` recorded — what the batch said it would edit."""
        return [entry for entry in self.entries if entry.declared]

    def save(self) -> str:
        path = Path(self.directory) / MANIFEST_NAME
        path.parent.mkdir(parents=True, exist_ok=True)
        # Stamped once: a later save (an adopted undeclared write) must not
        # move the date a review-cycle cutoff reads.
        self.taken_at = self.taken_at or time.strftime("%Y-%m-%dT%H:%M:%S")
        manifest: Dict[str, Any] = {
            "snapshot_version": 1,
            "task_id": self.task_id,
            "root": self.root,
            "taken_at": self.taken_at,
            "files": [entry.to_dict() for entry in self.entries],
        }
        if self.expected_ids is not None:
            manifest["expected_ids"] = list(self.expected_ids)
        _atomic_write(str(path), json.dumps(manifest, indent=2))
        return str(path)

    @classmethod
    def load(
        cls, phase_dir: str, task_id: str, *, expected_root: Optional[str] = None,
    ) -> Optional["TaskSnapshot"]:
        """Re-read a snapshot from disk (resume, and ``util restore-batch``).

        With ``expected_root``, a manifest naming another repository root is
        **refused** (``WriteSafetyError``) rather than loaded: the manifest's
        ``root`` is where :meth:`restore` writes, and a batch that can write
        the phase dir could plant one naming any directory (review fixes
        2026-10-05).
        """
        directory = Path(safety_dir(phase_dir)) / PRE_BATCH_DIRNAME / _safe_component(task_id)
        manifest = directory / MANIFEST_NAME
        if not manifest.is_file():
            return None
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        recorded_root = str(data.get("root", ""))
        if expected_root is not None and (
            not recorded_root
            or os.path.realpath(recorded_root) != os.path.realpath(expected_root)
        ):
            raise WriteSafetyError(
                f"Refusing the pre-batch snapshot {manifest}: its manifest names "
                f"{recorded_root or 'no repository root'} as the repository root, "
                f"but this phase belongs to {os.path.realpath(expected_root)}. A "
                f"snapshot is restored only under the root it was taken in; a "
                f"manifest naming another one is a planted or moved rollback "
                f"point, and nothing is written from it."
            )
        recorded_ids = data.get("expected_ids")
        return cls(
            task_id=str(data.get("task_id", task_id)),
            directory=str(directory),
            root=str(data.get("root", "")),
            entries=[SnapshotEntry.from_dict(row) for row in data.get("files", [])],
            expected_ids=(
                [str(i) for i in recorded_ids]
                if isinstance(recorded_ids, list) else None
            ),
            taken_at=(
                str(data["taken_at"]) if data.get("taken_at") else None
            ),
        )

    def taken_before(self, cutoff: Optional[datetime]) -> bool:
        """Whether this snapshot predates ``cutoff`` (a review's completion).

        The review-cycle rule (:func:`state_manager.predates_review`) to the
        second, as ``taken_at`` is stamped. Unlike the rule's other readers,
        a manifest with no parseable date is read as predating any cutoff
        given: the only such manifests are older than the field, and an
        unknown-age rollback point is kept aside rather than trusted as this
        cycle's.
        """
        return predates_review(
            _parse_completion_time(self.taken_at), cutoff,
            whole_seconds=True, undated_predates=True,
        )

    @staticmethod
    def items_digest(expected_ids: Optional[Sequence[str]]) -> str:
        """The eight hex chars a set-aside name carries for a batch's items."""
        return hashlib.sha256(
            "\n".join(sorted(str(i) for i in (expected_ids or []))).encode("utf-8")
        ).hexdigest()[:8]

    def set_aside(self) -> Optional[str]:
        """Move this snapshot out of its task id's slot; return where it went.

        For a snapshot that belongs to another batch than the one about to
        take the slot (an apply id reused for other items on a resume, or
        every slot under ``--fresh``): its rollback point must survive, so it
        is renamed ``<id>.items-<sha8 of its items>`` beside the slot (``-2``,
        ``-3`` … when that name is taken), never deleted. ``util restore-batch
        --task-id <new name>`` restores it, verified against the completion
        record that names the same items (``AuditLog.completion_for``), and
        :meth:`set_aside_dirs` finds it again when those items come back to
        the slot.
        """
        source = Path(self.directory)
        if not source.is_dir():
            return None
        base = f"{source.name}.items-{self.items_digest(self.expected_ids)}"
        target = source.with_name(base)
        counter = 2
        while target.exists():
            target = source.with_name(f"{base}-{counter}")
            counter += 1
        os.replace(str(source), str(target))
        self.directory = str(target)
        return str(target)

    @classmethod
    def set_aside_dirs(
        cls, phase_dir: str, task_id: str, expected_ids: Sequence[str],
    ) -> List[Path]:
        """The set-aside snapshots of ``task_id`` taken for these items, newest first.

        Newest is the highest ``-N`` suffix: a name is reused once its holder
        moves back into the slot, so within one review cycle there is one,
        and a second one only ever appears when ``--fresh`` set a slot aside
        beside an older cycle's copy — the newest is then the current
        cycle's pre-first-dispatch bytes.
        """
        base = f"{_safe_component(task_id)}.items-{cls.items_digest(expected_ids)}"
        parent = Path(safety_dir(phase_dir)) / PRE_BATCH_DIRNAME
        found: List[Tuple[int, Path]] = []
        for candidate in parent.glob(f"{base}*"):
            if not (candidate / MANIFEST_NAME).is_file():
                continue
            suffix = candidate.name[len(base):]
            if suffix == "":
                found.append((1, candidate))
            elif suffix.startswith("-") and suffix[1:].isdigit():
                found.append((int(suffix[1:]), candidate))
        return [path for _, path in sorted(found, key=lambda item: -item[0])]

    @classmethod
    def reinstate(
        cls, phase_dir: str, task_id: str, expected_ids: Sequence[str],
        *, not_before: Optional[datetime] = None,
    ) -> Optional["TaskSnapshot"]:
        """Move the newest set-aside snapshot for these items back into the slot.

        Only into a free slot (the caller set the holder aside first, or none
        was there). The items that come back to a positional id after a
        selection change get their pre-FIRST-dispatch bytes back as the
        rollback point, instead of a fresh snapshot of the edits every run
        since left on disk (adversarial review, 2026-10-02). A copy taken
        before ``not_before`` (the current review cycle's completion) is a
        previous cycle's and stays aside.
        """
        slot = Path(safety_dir(phase_dir)) / PRE_BATCH_DIRNAME / _safe_component(task_id)
        if slot.exists():
            return None
        for candidate in cls.set_aside_dirs(phase_dir, task_id, expected_ids):
            loaded = cls.load(phase_dir, candidate.name)
            if loaded is None or loaded.taken_before(not_before):
                continue
            os.replace(str(candidate), str(slot))
            return cls.load(phase_dir, task_id)
        return None

    @classmethod
    def locate(
        cls, phase_dir: str, task_id: str, expected_ids: Optional[Sequence[str]],
    ) -> Optional[str]:
        """The directory name holding this batch's snapshot, slot or set-aside.

        The slot when its manifest names the same items (or none); else the
        newest set-aside copy for them; else ``None``. A completion record
        naming no items resolves to the slot alone, as before.
        """
        slot = cls.load(phase_dir, task_id)
        wanted = sorted(str(i) for i in expected_ids) if expected_ids else None
        if slot is not None and (
            wanted is None or not slot.expected_ids
            or sorted(slot.expected_ids) == wanted
        ):
            return Path(slot.directory).name
        if wanted is None:
            return None
        aside = cls.set_aside_dirs(phase_dir, task_id, wanted)
        return aside[0].name if aside else None

    # -- the verdict ----------------------------------------------------

    def changed(self) -> List[str]:
        """Repo-relative paths whose bytes moved since the snapshot (D3g).

        Byte comparison, in Python, on the artifacts the batch declared — the
        classification the markdown performs with ``diff -u``, moved into code so
        both invokers reach the same verdict.
        """
        moved: List[str] = []
        for entry in self.entries:
            now = file_sha256(entry.absolute)
            before = entry.sha256 if entry.existed else None
            if now != before:
                moved.append(entry.relative)
        return moved

    def observed(self) -> Dict[str, Dict[str, Any]]:
        """Per-file before/after hashes, for the audit record (D3l)."""
        out: Dict[str, Dict[str, Any]] = {}
        for entry in self.entries:
            out[entry.relative] = {
                "sha256_before": entry.sha256,
                "sha256_after": file_sha256(entry.absolute),
                "existed_before": entry.existed,
                "exists_after": Path(entry.absolute).is_file(),
                "declared": entry.declared,
            }
        return out

    # -- rollback -------------------------------------------------------

    def entry_for(self, relative: str) -> Optional[SnapshotEntry]:
        for entry in self.entries:
            if entry.relative == relative:
                return entry
        return None

    def restore(
        self,
        paths: Optional[Sequence[str]] = None,
        *,
        expected: Optional[Dict[str, Optional[str]]] = None,
        force: bool = False,
    ) -> Dict[str, str]:
        """Restore snapshot bytes for ``paths`` (default: everything snapshotted).

        Every destination is re-derived from the pinned root and revalidated
        component by component before anything is written (see
        :func:`_revalidated_target`). The manifest's ``absolute`` is a claim about
        the tree as it was *before* a write-capable runner had it, so following it
        now — which ``shutil.copy2`` onto the destination would do — is how a
        rollback ends up writing the saved bytes through a symlink the runner left
        behind, into a file outside the repository. The path *entry* is replaced or
        unlinked instead; neither operation follows a link.

        Args:
            expected: ``relative -> sha256`` the audit recorded at completion. A
                file whose current hash no longer matches is **refused** rather
                than restored: someone edited it since the run, and silently
                reverting their edit is a second data-loss bug. ``--force``
                overrides, deliberately explicitly.

        Returns:
            ``relative -> "restored" | "deleted" | "skipped: <why>"``.
        """
        wanted = list(paths) if paths is not None else [e.relative for e in self.entries]
        report: Dict[str, str] = {}
        leftovers: Optional[RestoreLeftovers] = None
        for relative in wanted:
            entry = self.entry_for(relative)
            if entry is None:
                report[relative] = "skipped: not in this task's snapshot"
                continue
            restoring = bool(entry.existed and entry.payload)
            try:
                target = _revalidated_target(
                    self.root, entry.relative, create_parents=restoring
                )
            except WriteSafetyError as exc:
                report[relative] = f"skipped: {exc.message}"
                continue
            except OSError as exc:
                report[relative] = f"skipped: {exc}"
                continue
            if target is None:
                # The delete leg, with a parent directory already gone.
                report[relative] = "deleted (already absent)"
                continue
            # A staged entry a restore kept for the user is neither replaced
            # nor deleted, even when a snapshot adopted it, --force included
            # (docs/development/write-safety.md, restore).
            if leftovers is None:
                leftovers = restore_leftovers(self.root)
            if leftovers.holds(str(target)):
                report[relative] = _kept_for_the_user(str(target))
                continue
            symlinked = _is_symlink(target)
            if expected is not None and not force:
                recorded = expected.get(relative, "__missing__")
                if recorded != "__missing__":
                    if symlinked:
                        report[relative] = (
                            "skipped: the path is a symlink now, not the file "
                            "that was snapshotted — pass --force to replace the "
                            "link itself (its target is never written through)"
                        )
                        continue
                    current = file_sha256(str(target))
                    if current != recorded:
                        report[relative] = (
                            "skipped: changed after the run (recorded "
                            f"{_short(recorded)}, now {_short(current)}) — pass "
                            "--force to overwrite anyway"
                        )
                        continue
            if restoring:
                source = Path(self.directory) / PAYLOAD_DIRNAME / entry.payload
                if not source.is_file():
                    report[relative] = "skipped: snapshot payload is missing"
                    continue
                # The payload must still be the bytes the manifest hashed at
                # snapshot time; a payload rewritten since is not a rollback
                # point and is never written (review fixes 2026-10-05).
                payload_hash = file_sha256(str(source))
                if payload_hash != entry.sha256:
                    report[relative] = (
                        "skipped: the snapshot payload no longer matches the "
                        f"manifest (recorded {_short(entry.sha256)}, payload "
                        f"{_short(payload_hash)}) — the rollback point was "
                        "altered after it was taken; nothing written"
                    )
                    continue
                try:
                    _replace_with_payload(source, target, root=self.root,
                                          sha256=entry.sha256)
                except CopyNotContained as left:
                    report[relative] = _skipped_leaving(left)
                    continue
                except OSError as exc:
                    report[relative] = f"skipped: {exc}"
                    continue
                report[relative] = "restored"
            else:
                # Absent before the batch: the correct rollback is deletion
                # of the entry itself (a symlink left in the file's place is
                # removed, never followed), relative to its folder held.
                report[relative] = _delete_entry(self.root, target)
        return report


def restore_path(root: str, relative: str, source: Optional[str]) -> str:
    """Put repo-relative *relative* back from *source* (a file or symlink the
    caller has checked holds what belongs there), or delete it when *source*
    is ``None``: the commit write policy's restore for a watched path the
    pre-batch snapshot holds no bytes for (``commit_apply.restore_watched``).

    The same rules as :meth:`TaskSnapshot.restore`: every component below the
    pinned root is revalidated no-follow (:func:`_revalidated_target`), the
    entry itself is replaced (``os.replace``) or unlinked, never written
    through, and a directory now at the path is never removed. Returns
    ``"restored"``, ``"deleted"``, ``"deleted (already absent)"`` or
    ``"skipped: <why>"``.
    """
    try:
        target = _revalidated_target(root, relative, create_parents=source is not None)
    except WriteSafetyError as exc:
        return f"skipped: {exc.message}"
    except OSError as exc:
        return f"skipped: {exc}"
    if target is None:
        return "deleted (already absent)"
    if restore_leftovers(root).holds(str(target)):
        return _kept_for_the_user(str(target))
    if source is None:
        return _delete_entry(root, target)
    try:
        if os.path.islink(source):
            _restored_link(os.readlink(source), target, root)
        else:
            _replace_with_payload(Path(source), target, root=root)
    except CopyNotContained as left:
        return _skipped_leaving(left)
    except OSError as exc:
        return f"skipped: {exc}"
    return "restored"


def _delete_entry(root: str, target: Path) -> str:
    """A rollback's delete leg: remove the entry *target*, which
    :func:`_revalidated_target` derived under the pinned *root*, never a
    link's target and never a directory. ``"deleted"``, ``"deleted (already
    absent)"`` or ``"skipped: <why>"``.

    On Linux and macOS the name is removed relative to its folder, reached
    from *root* without following a link and held (:class:`_HeldFolder`),
    which must still be the folder at its path just before the removal: a
    folder swapped for a link after the revalidation is refused, and a
    removal never lands in a folder a link leads to
    (docs/development/write-safety.md, restore). A folder that cannot be
    reached because it is gone (:func:`_folder_gone`) leaves nothing to
    delete. Windows removes it by path, the window a removal by path always
    had."""
    if not _PUBLISHES_BY_DESCRIPTOR:
        try:
            if stat.S_ISDIR(os.lstat(str(target)).st_mode):
                return "skipped: a directory is at the path now"
            os.unlink(str(target))
        except FileNotFoundError:
            return "deleted (already absent)"
        except OSError as exc:
            return f"skipped: {exc}"
        return "deleted"
    try:
        folder = _HeldFolder.open(root, target, say=_REMOVED)
    except OSError as exc:
        if _folder_gone(root, target):
            return "deleted (already absent)"
        return f"skipped: {exc}"
    try:
        try:
            info = os.lstat(target.name, dir_fd=folder.fd)
        except FileNotFoundError:
            return "deleted (already absent)"
        if stat.S_ISDIR(info.st_mode):
            return "skipped: a directory is at the path now"
        if not folder.in_place():
            return f"skipped: {_folder_moved(folder, str(target))}"
        os.unlink(target.name, dir_fd=folder.fd)
    except FileNotFoundError:
        return "deleted (already absent)"
    except OSError as exc:
        return f"skipped: {_respelled(exc, str(target))}"
    finally:
        os.close(folder.fd)
    return "deleted"


def _folder_gone(root: str, target: Path) -> bool:
    """Whether *target*'s folder below *root* is gone: a fresh walk from
    the root, each folder opened without following a link relative to the
    one above (as :class:`_HeldFolder` walks), finds one missing. A link
    met first, something that is not a folder, or a folder that cannot be
    opened is not absence, so :func:`_delete_entry` still refuses those."""
    resolved = str(Path(root).resolve())
    try:
        parts = target.parent.relative_to(resolved).parts
        handle = os.open(resolved, os.O_RDONLY | os.O_DIRECTORY | _CLOEXEC)
    except (ValueError, OSError):
        return False
    try:
        for name in parts:
            try:
                child = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
                                | _CLOEXEC, dir_fd=handle)
            except FileNotFoundError:
                return True
            except OSError:
                return False
            os.close(handle)
            handle = child
        return False
    finally:
        os.close(handle)


def _short(digest: Optional[str]) -> str:
    return (digest or "absent")[:12]


def _skipped_leaving(left: CopyNotContained) -> str:
    """A restore's ``skipped`` state when its refused copy is left behind, or
    may have gone through a link: named for the user to check, as the
    rollback store's pass names a copy of its own it could not remove. For
    the restore's own staged entry (:class:`_StagingLeft`) it also says how
    to remove it, and whether the write checks leave it alone meanwhile
    (:func:`restore_leftovers`)."""
    if not isinstance(left, _StagingLeft):
        return f"skipped: {left}; check what is left there and delete it by hand"
    if left.unrecorded is None:
        meanwhile = ("until it is gone, no write check in this process counts it "
                     "as a batch's file and no rollback in it replaces or deletes "
                     "it; another process checks it as any other file")
    else:
        meanwhile = (f"it could not be recorded as the restore's ({left.unrecorded}), "
                     f"so a write check can count it as a batch's file meanwhile")
    return (f"skipped: {left}; check it and delete it by hand "
            f"({_removal_command(left.pending)}): {meanwhile}")


def _kept_for_the_user(path: str) -> str:
    """A rollback's ``skipped`` state for a staged entry a restore in this
    process kept for the user (:func:`restore_leftovers`), on either leg."""
    return (f"skipped: {path} is a file a restore in this process left for you "
            f"to check, so no rollback in it replaces or deletes it; delete it by "
            f"hand once checked ({_removal_command(path)})")


def _removal_command(path: str) -> str:
    """The command that deletes the entry *path* itself (a link, never its
    target), for a message."""
    if os.name == "nt":  # pragma: no cover - Windows
        return f'del /f "{path}"'
    return f"rm -- {shlex.quote(path)}"


#: The staged entries a restore in this process kept for the user, per
#: repository: ``{normcase(realpath(root)): {normcase(path): (path, identity)}}``.
#: Held in this process's memory alone, never on disk: an entry takes its file
#: out of every write check, and whatever a runner can write (the state home
#: and the phase dir included, on the uncontained rung) it could forge
#: (docs/development/write-safety.md, restore).
_LEFTOVERS_LOCK = threading.Lock()
_LEFTOVERS: Dict[str, Dict[str, Tuple[str, _Identity]]] = process_cache(
    "utils.write_safety._LEFTOVERS", lock=_LEFTOVERS_LOCK)


class RestoreLeftovers:
    """The staged entries a restore in this process kept in one repository
    for the user to check and remove: each its absolute path and
    :data:`_Identity` (:func:`restore_leftovers`)."""

    def __init__(self, entries: Sequence[Tuple[str, _Identity]]) -> None:
        self._entries = {os.path.normcase(path): identity for path, identity in entries}

    def __bool__(self) -> bool:
        return bool(self._entries)

    def holds(self, path: str) -> bool:
        """Whether the absolute *path* is one of them: that path, and the
        entry there (never followed) that very file. Another file at the
        path, a model's with the same name included, is not."""
        identity = self._entries.get(os.path.normcase(path))
        return identity is not None and _identity_at(path) == identity


def restore_leftovers(root: str) -> RestoreLeftovers:
    """The staged entries a restore in this process kept under the
    repository *root* for the user (:class:`_StagingLeft`), each still at its
    path. The write checks this process runs leave exactly these out: the
    containment sweep's census and the differences it computes, the
    porcelain write check, and both legs of a rollback (replace and delete).
    An entry that is gone, or with another file at its path, is dropped:
    whatever is there is an ordinary file again. Only this process's own
    restores add one, from the staged file's descriptor, so nothing a runner
    writes can: a file another process kept (an earlier ``util
    restore-batch``, another run) is checked as any other
    (docs/development/write-safety.md, restore)."""
    return RestoreLeftovers(_leftovers_live(root))


def _record_left(root: str, left: _StagingLeft) -> None:
    """Record *left*, kept under the repository *root*, for
    :func:`restore_leftovers`; ``left.unrecorded`` says why when it cannot
    be."""
    if left.identity is None:
        left.unrecorded = "its file identity could not be read"
    elif not os.path.isabs(left.pending):
        left.unrecorded = "the folder it is in was moved"
    else:
        _leftovers_live(root, (os.path.abspath(left.pending), left.identity))


def _forget_gone(root: str) -> None:
    """Drop the recorded leftovers under *root* that are gone, once a
    restore there put its file back."""
    _leftovers_live(root)


def _leftovers_live(
    root: str, kept: Optional[Tuple[str, _Identity]] = None,
) -> List[Tuple[str, _Identity]]:
    """*root*'s entries in :data:`_LEFTOVERS` still at their paths, under its
    lock, those that are gone dropped; then *kept* added, its identity read
    from the staged file's descriptor (its name is not looked up again)."""
    key = os.path.normcase(os.path.realpath(root))
    with _LEFTOVERS_LOCK:
        live = {name: entry for name, entry in _LEFTOVERS.get(key, {}).items()
                if _identity_at(entry[0]) == entry[1]}
        if kept is not None:
            live[os.path.normcase(kept[0])] = kept
        if live:
            _LEFTOVERS[key] = live
        else:
            _LEFTOVERS.pop(key, None)
        return list(live.values())


def _identity_at(path: str, dir_fd: Optional[int] = None) -> Optional[_Identity]:
    """The :data:`_Identity` of the entry at *path* (relative to *dir_fd*),
    never followed."""
    try:
        info = os.lstat(path, dir_fd=dir_fd)
    except (OSError, ValueError):
        return None
    return info.st_dev, info.st_ino, info.st_ctime_ns


def _is_symlink(path: Path) -> bool:
    try:
        return stat.S_ISLNK(os.lstat(str(path)).st_mode)
    except OSError:
        return False


def _revalidated_target(
    root: str,
    relative: str,
    *,
    create_parents: bool,
) -> Optional[Path]:
    """Re-derive ``relative`` under ``root``, checking every component no-follow.

    Rollback runs *after* a write-capable runner had the working tree, so the
    snapshot's absolute path is a claim about the past: the file it names can have
    become a symlink into ``$HOME`` since, and so can any directory above it. Each
    component below the pinned root is therefore re-checked with ``os.lstat``
    (never ``stat``, which answers about a link's target, and never
    ``Path.resolve``, which follows one silently) and a symlinked or non-directory
    parent is refused. The path ``take`` recorded was canonicalized at snapshot
    time, so a symlink on this walk is always something that appeared afterwards.

    Args:
        create_parents: On for the restore leg, which may have to recreate a
            directory the batch removed — each level with ``os.mkdir``, which
            fails rather than silently accepting an existing symlink the way
            ``mkdir(parents=True, exist_ok=True)`` would. Off for the delete leg,
            which returns ``None`` for a missing parent: nothing left to delete.

    Raises:
        PathEscape: any component is a symlink, or on Windows a directory
            junction or another reparse point naming another path (``lstat``
            reports a junction as a directory), or the path is not a plain
            repo-relative one.
    """
    if not root:
        raise PathEscape(
            f"the snapshot manifest records no repo root, so {relative} cannot be "
            f"revalidated before writing"
        )
    resolved_root = Path(root).resolve()
    if not resolved_root.is_dir():
        raise PathEscape(
            f"the pinned repo root {resolved_root} is gone, so {relative} cannot "
            f"be revalidated before writing"
        )
    text = str(relative).replace("\\", "/")
    parts = [part for part in PurePosixPath(text).parts if part != "."]
    if (
        Path(relative).is_absolute()
        or PurePosixPath(text).is_absolute()
        or _looks_like_a_windows_escape(str(relative))
        or not parts
        or any(part == ".." for part in parts)
    ):
        raise PathEscape(
            f"{relative!r} is not a plain path under the pinned repo root "
            f"{resolved_root}"
        )
    current = resolved_root
    for part in parts[:-1]:
        current = current / part
        try:
            info = os.lstat(str(current))
        except FileNotFoundError:
            if not create_parents:
                return None
            os.mkdir(str(current))
            continue
        if stat.S_ISLNK(info.st_mode):
            raise PathEscape(
                f"{current} is a symlink now, so rolling {relative} back through "
                f"it would leave the pinned repo root {resolved_root}"
            )
        if _names_another_path(info):
            raise PathEscape(
                f"{current} is a directory junction or another link now, so "
                f"rolling {relative} back through it would leave the pinned repo "
                f"root {resolved_root}"
            )
        if not stat.S_ISDIR(info.st_mode):
            raise PathEscape(
                f"{current} is not a directory, so {relative} cannot be restored "
                f"under the pinned repo root {resolved_root}"
            )
    return current / parts[-1]


def _replace_with_payload(source: Path, target: Path, *, root: str,
                          sha256: Optional[str] = None) -> None:
    """Put ``source``'s bytes back as a new file and swap it in for ``target``'s
    own entry; *root* is the pinned repo root ``target`` was revalidated under
    (:func:`_revalidated_target`).

    Never ``shutil.copy2`` onto the destination: it opens the destination for
    writing and follows it, so a snapshotted regular file that has since become a
    symlink would have the saved bytes written *through* the link. A rename swaps
    the directory entry itself — atomic, and no-follow — and the new file is
    staged in the same revalidated directory, so the rename cannot cross a
    filesystem.

    The staged file is reached through one descriptor (one handle on Windows)
    from its creation to its rename, never by its path, because whoever can
    write the file's folder can swap that name for a link to another file, a
    hard link to one outside the repository included, at any moment
    (docs/development/write-safety.md, restore). The bytes read through the
    payload's descriptor must hash to ``sha256``, the manifest's digest, when it
    is given (``restore_path`` gives none: its caller checked its copy), and the
    staged file, read back after the flush, must hold them.

    * Windows with ``CopyFile2`` (Python 3.12+), a payload that is not
      read-only: ``CopyFile2``'s copy, checked and swapped in through one handle
      that excludes every other writer (:func:`_restored_by_copy_file2`), so
      the file keeps the payload's alternate data streams, attributes and EFS
      encryption, which the snapshot's ``shutil.copy2`` kept.
    * Linux and macOS: :func:`_restored_through_descriptor`, in ``target``'s
      folder as reached from *root* (:class:`_HeldFolder`).
    * Windows otherwise (a read-only payload, Python before 3.12, a failed
      ``CopyFile2`` that left nothing): :func:`_restored_through_handle`.

    Raises ``OSError`` when nothing was put back, :class:`CopyNotContained`
    when something is left beside the file for the user to look at; the
    restore's own staged file left there (:class:`_StagingLeft`) is recorded
    first, for the write checks to leave alone (:func:`restore_leftovers`).
    """
    tmp = _staging_name(target)
    try:
        if _COPY_FILE2 is not None and _restored_by_copy_file2(
                str(source), str(tmp), str(target), sha256):
            pass
        elif _STAGES_BY_DESCRIPTOR:
            _restored_through_descriptor(str(source), tmp, target, sha256, root)
        else:
            _restored_through_handle(_held_copy_calls(), str(source), str(tmp),
                                     str(target), sha256)
    except _StagingLeft as left:
        _record_left(root, left)
        raise
    _forget_gone(root)


def _staging_name(target: Path) -> Path:
    """The name a restore stages *target*'s file or link under, beside it:
    hidden, this process's, and new for each attempt
    (:func:`_staging_token`), so an entry an earlier attempt kept there for
    the user never blocks a later one, and the name cannot be known before
    the attempt makes it."""
    return target.with_name(
        f".{target.name}.restore.{os.getpid()}.{_staging_token()}.tmp")


def _staging_token() -> str:
    """A random token for one staging name (:func:`_staging_name`)."""
    return secrets.token_hex(4)


#: Whether a restore can stage its file through descriptors alone (Linux,
#: macOS): its folder reached from the repo root without following a link and
#: held by a descriptor, every name in it reached relative to that descriptor,
#: the file's times and mode set through its own descriptor. Windows stages
#: through a handle instead.
_STAGES_BY_DESCRIPTOR = bool(
    OPENS_WITHOUT_FOLLOWING and hasattr(os, "fchmod") and os.utime in os.supports_fd
    and os.stat in os.supports_dir_fd and os.rename in os.supports_dir_fd
    and os.symlink in os.supports_dir_fd and os.readlink in os.supports_dir_fd
)
#: ``O_TMPFILE`` (Linux): a file made with no name in a folder, so nobody can
#: reach it by a name until it is given one (``0`` where there is none).
_O_TMPFILE = getattr(os, "O_TMPFILE", 0)
#: How ``open(2)`` refuses ``O_TMPFILE`` where the kernel (``EISDIR``) or the
#: folder's filesystem (``EOPNOTSUPP``) cannot make one.
_NO_TMPFILE = tuple(getattr(errno, name) for name in (
    "EISDIR", "EOPNOTSUPP", "ENOTSUP", "EINVAL") if hasattr(errno, name))
#: How the staged file is made by its name where it cannot be made unnamed:
#: exclusively, never through a link already there.
_STAGE_FLAGS = (os.O_RDWR | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
                | _CLOEXEC)


def _restored_through_descriptor(source: str, tmp: Path, target: Path,
                                 sha256: Optional[str], root: str) -> None:
    """:func:`_replace_with_payload` on Linux and macOS
    (docs/development/write-safety.md, restore).

    The payload is opened without following a link and read once. The
    target's folder is reached from *root* without following a link and held
    (:class:`_HeldFolder`), and every name in it (the staged file's, the
    target's) is reached relative to that descriptor. The staged file is made
    with no name where Linux can (``O_TMPFILE``) and is named *tmp* only once
    its bytes are checked and its metadata set, or else made as *tmp*
    exclusively, never through a link, and held by its descriptor from then
    on. Through that descriptor alone: the payload's bytes are written,
    flushed and read back; the hash of the bytes read must be *sha256* when it
    is given; and the file takes the payload's times, extended attributes,
    mode and file flags, as ``shutil.copystat`` gave them. Then the name *tmp*
    must still be that file, a regular file with no other name (``lstat``
    against ``fstat``), the folder must still be the one at its path, and the
    file is renamed over *target*; once renamed, the folder must still be in
    place and *target* must name the file.

    A refusal leaves the file as it was and the snapshot kept. Once the
    staged file has a name it is never removed (:func:`_leave_staged`): it
    is left and raised as :class:`CopyNotContained`, named, as is a name
    found where the staged file was to be."""
    payload = os.open(source, _READ_FLAGS | os.O_NOFOLLOW)
    try:
        if not stat.S_ISREG(os.fstat(payload).st_mode):
            raise OSError(f"{source} is no longer the snapshot's payload file")
        folder = _HeldFolder.open(root, target)
        try:
            _refuse_a_directory(folder.fd, target.name, str(target))
            _stage_and_rename(payload, folder, source, str(tmp), str(target), sha256)
        finally:
            os.close(folder.fd)
    finally:
        os.close(payload)


def _stage_and_rename(payload: int, folder: _HeldFolder, source: str, tmp: str,
                      target: str, sha256: Optional[str]) -> None:
    """The staged file's whole life in :func:`_restored_through_descriptor`:
    *payload* the payload's descriptor, *folder* the target's folder. The
    bytes and the metadata are the payload's; staging, naming, the checks and
    the rename are :func:`_publish_staged`'s."""

    def fill(staged: int) -> None:
        digest = _copy_hashed(payload, staged)
        if sha256 is not None and digest != sha256:
            raise OSError(
                f"the snapshot payload no longer matches the manifest (recorded "
                f"{_short(sha256)}, payload {_short(digest)}); nothing written")
        os.fsync(staged)
        if _descriptor_sha256(staged) != digest:
            raise OSError(f"{tmp} does not hold the bytes of {source}")
        info = os.fstat(payload)
        # What `copy2` preserved, in `copystat`'s order, through the descriptor.
        os.utime(staged, ns=(info.st_atime_ns, info.st_mtime_ns))
        _copy_xattrs(payload, staged)
        os.fchmod(staged, stat.S_IMODE(info.st_mode))
        flags = getattr(info, "st_flags", 0)
        if flags != getattr(os.fstat(staged), "st_flags", 0):
            _set_flags(staged, flags, target)

    _publish_staged(folder, tmp, target, fill)


def _publish_staged(folder: _HeldFolder, tmp: str, target: str,
                    fill: Callable[[int], None], *, mode: int = 0o600) -> None:
    """Stage a new file in the held *folder*, have *fill* put its bytes and
    metadata in through its descriptor, and rename it over *target*: the
    rules every write through a held folder keeps, the restore's
    (:func:`_stage_and_rename`) and the plan outputs' (:func:`write_below_root`)
    (docs/development/write-safety.md, restore). The file is made with no
    name where Linux can, else as *tmp* exclusively and never through a link
    (:func:`_staged`, with *mode*), and is named only once filled; just
    before the rename *tmp* must still be that file, a regular file with no
    other name, and the folder must still be the one at its path. Once
    renamed, the folder must still be in place and *target* must name the
    file. A named file that is not renamed is left and raised
    (:func:`_leave_staged`), never removed. The messages are the folder's
    (:class:`_Wording`)."""
    say = folder.say
    name, target_name = os.path.basename(tmp), os.path.basename(target)
    staged, named = _staged(folder.fd, name, tmp, mode=mode, say=say)
    try:
        made = os.fstat(staged)
        fill(staged)
        if not named:
            if os.fstat(staged).st_nlink:
                raise OSError(_given_another_name(tmp, target, say))
            if not folder.in_place():
                raise OSError(_folder_moved(folder, target))
            _link_unnamed(staged, folder.fd, name, tmp, say)
            named = True
        _check_staged(folder.fd, name, staged, tmp, target, say)
        if not folder.in_place():
            raise OSError(_folder_moved(folder, target))
        try:
            os.replace(name, target_name, src_dir_fd=folder.fd, dst_dir_fd=folder.fd)
        except OSError as exc:
            raise _respelled(exc, tmp, target) from exc
        named = False
    except BaseException as failure:
        # A name found where the staged file was to be (CopyNotContained) is
        # not the staged file's, and is left as it is already.
        if named and not isinstance(failure, CopyNotContained):
            _leave_staged(folder, name, tmp, failure, say.staged, _identity_of(staged))
        raise
    finally:
        os.close(staged)
    if not folder.in_place():
        raise OSError(
            f"{folder.shown} was moved or replaced while {target} was being "
            f"{say.done}, so what is at {target} now is not {say.ours} (the "
            f"file {say.done} is at {folder.where(target_name, target)}); check "
            f"both{say.kept}")
    try:
        published = os.lstat(target_name, dir_fd=folder.fd)
    except OSError:
        published = None
    if published is None or (
            (published.st_dev, published.st_ino) != (made.st_dev, made.st_ino)):
        raise OSError(
            f"{target} did not name the file {say.done} once it was renamed "
            f"there: another file was swapped in for {tmp} just before the "
            f"rename, or over {target} just after it, so what is at {target} "
            f"now is not {say.ours}; check it{say.kept}")


def _staged(folder: int, name: str, tmp: str, *, mode: int = 0o600,
            say: _Wording = _PUT_BACK) -> Tuple[int, bool]:
    """A new file to stage a write in, open to read and write, and whether
    it is named: with no name (``O_TMPFILE``) where the folder's filesystem
    can make one and :data:`_PROC_SELF_FD` can name it later, else made as
    *name* in *folder*, exclusively and never through a link. *mode* is the
    one ``open(2)`` takes (the umask applies). A name already there is left
    as it is and raised as :class:`CopyNotContained`."""
    if _O_TMPFILE:
        try:
            handle = os.open(".", _O_TMPFILE | os.O_RDWR | _CLOEXEC, mode, dir_fd=folder)
        except OSError as exc:
            if exc.errno not in _NO_TMPFILE:
                raise _respelled(exc, os.path.dirname(tmp)) from exc
        else:
            if os.path.exists(f"{_PROC_SELF_FD}/{handle}"):
                return handle, False
            os.close(handle)
    try:
        return os.open(name, _STAGE_FLAGS, mode, dir_fd=folder), True
    except FileExistsError as exc:
        raise _already_there(tmp, say) from exc
    except OSError as exc:
        raise _respelled(exc, tmp) from exc


def _link_unnamed(staged: int, folder: int, name: str, tmp: str,
                  say: _Wording = _PUT_BACK) -> None:
    """Give the unnamed file *staged* the name *name* in *folder*. A link
    is never made over a name already there, a link included: that name is
    left as it is and raised as :class:`CopyNotContained`."""
    try:
        os.link(f"{_PROC_SELF_FD}/{staged}", name, dst_dir_fd=folder,
                follow_symlinks=True)
    except FileExistsError as exc:
        raise _already_there(tmp, say) from exc
    except OSError as exc:
        raise _respelled(exc, tmp) from exc


def _check_staged(folder: int, name: str, staged: int, tmp: str, target: str,
                  say: _Wording = _PUT_BACK) -> None:
    """Refuse to rename *name* unless it is still the file *staged* holds,
    a regular file with no other name. A name swapped in is raised as
    :class:`CopyNotContained` (left as it is); another name given to the
    staged file as ``OSError``."""
    try:
        named = os.lstat(name, dir_fd=folder)
    except OSError as exc:
        raise OSError(f"{tmp}, {say.staged}, could not be examined ({exc}), so "
                      f"nothing was {say.done}") from exc
    opened = os.fstat(staged)
    if (named.st_dev, named.st_ino) != (opened.st_dev, opened.st_ino):
        what = ("a link" if stat.S_ISLNK(named.st_mode) else
                "another file" if stat.S_ISREG(named.st_mode) else "something else")
        raise CopyNotContained(
            tmp, f"{tmp} was {what} by the time the file staged there was to be "
                 f"renamed over {target}, so nothing was {say.done}, and what is "
                 f"at {tmp} was left as it is")
    if not stat.S_ISREG(named.st_mode) or opened.st_nlink != 1:
        raise OSError(_given_another_name(tmp, target, say))


def _given_another_name(tmp: str, target: str, say: _Wording = _PUT_BACK) -> str:
    return (f"{tmp}, {say.staged}, was given another name before it could be "
            f"renamed over {target}, so nothing was {say.done}")


def _refuse_a_directory(fd: Optional[int], name: str, target: str) -> None:
    """Raise ``IsADirectoryError`` when a directory is at *target* (its
    *name* relative to the folder descriptor *fd*, or by path without one),
    before anything is staged: a file or link renamed over a directory fails
    once its staged name exists, and that name is never removed
    (:func:`_leave_staged`), so each attempt would leave one more copy
    (docs/development/write-safety.md, restore). A directory put there after
    this look still fails the rename, and the staged name is then left."""
    try:
        info = os.lstat(name, dir_fd=fd)
    except OSError:
        return
    if stat.S_ISDIR(info.st_mode):
        raise IsADirectoryError(
            f"{target} is a directory now, so nothing was put back (the snapshot "
            f"is kept)")


def _leave_staged(folder: Optional[_HeldFolder], name: str, tmp: str,
                  failure: BaseException, what: str,
                  made: Optional[_Identity]) -> None:
    """Once a restore failed with *failure* after *what* (:data:`_Identity`
    *made*) was given the name *name* (*tmp* in full): leave that
    name, and raise it as :class:`_StagingLeft` naming it, chained to
    *failure*, for the user to check and remove; an interrupt goes on as it
    is. The name is never removed: POSIX removes a name, not a file, and
    between any check of the name and ``unlink(2)`` another process can swap
    its own file in, which the removal would then delete, its only name
    perhaps (docs/development/write-safety.md, restore). A plan-output
    write leaves its staged file the same way (:func:`_publish_staged`)."""
    if not isinstance(failure, Exception):
        return
    where = folder.where(name, tmp) if folder is not None else tmp
    actor = (folder.say if folder is not None else _PUT_BACK).actor
    raise _StagingLeft(
        where, f"{failure}; {what} was left at {where}: a {actor} never removes "
               f"a name it made, as another file can be swapped in for it between "
               f"a check and the removal", made) from failure


# ---------------------------------------------------------------------------
# Plan outputs: a write, a move aside or a removal through a held folder
# ---------------------------------------------------------------------------

#: Whether a plan-output write goes through a held folder (Linux, macOS): the
#: restore's staging by descriptor (:data:`_STAGES_BY_DESCRIPTOR`), plus making
#: and removing a name relative to a folder's descriptor. Windows writes by
#: path instead (:func:`write_below_root`).
_PUBLISHES_BY_DESCRIPTOR = bool(
    _STAGES_BY_DESCRIPTOR and os.mkdir in os.supports_dir_fd
    and os.unlink in os.supports_dir_fd
)


def write_below_root(root: Union[str, "os.PathLike[str]"],
                     target: Union[str, "os.PathLike[str]"], data: bytes, *,
                     mode: Optional[int] = None, fsync: bool = True,
                     resolve_root: bool = True) -> None:
    """Replace *target*, a file below the folder *root*, with *data*, never
    through a link (docs/development/write-safety.md#plan-output-containment).

    *target* is the caller's checked path: :func:`contain_local_path` gives
    it resolved, below *root* resolved. A check of a path followed by a write
    by that path can always be redirected in between, by a link swapped in
    for the file or for any folder above it, so on Linux and macOS the write
    is made through the folder, held: reached from *root* one component at a
    time without following a link, a missing one made on the way relative to
    its parent's descriptor (:class:`_HeldFolder`), and every name in it
    reached through that descriptor. The bytes are staged and renamed in by
    the restore's rules (:func:`_publish_staged`): a new file made
    exclusively, never through a link, flushed with its mode, and renamed
    over the target only while the folder is still the one at its path. Any
    link or junction swapped in on the way is refused, and so is anything but
    a file at the target's own name: the caller resolved it, so a link there
    now was put there since, or leads nowhere. An existing file's permission
    bits carry over, a new one gets the umask's, *mode* overrides both, and
    the bytes go in owner-only (``atomic_io``'s rules); *fsync* flushes the
    file and its folder. *resolve_root* off: *root* is a plan's directory
    the run recorded resolved (``held_folder.anchor_plan_dir``), walked from
    as recorded and never resolved again, so a link swapped in for it or a
    folder above it since is not adopted as the root (the caller checked
    *target* below it as recorded).

    Windows (no ``dir_fd``, no ``O_NOFOLLOW``) writes the checked path with
    ``atomic_io``, which replaces a link at the name and never follows one:
    a folder above it swapped for a link or junction between the caller's
    check and the write is still followed there, the window a write by path
    always had.

    Raises ``OSError`` with nothing written at the target, or once the file
    is in, when the folder moved or the name changed meanwhile (the message
    says where the file is). A staged file that was named but not renamed is
    left and named (:class:`CopyNotContained`), never removed.
    """
    target = Path(target)
    if not _PUBLISHES_BY_DESCRIPTOR:
        os.makedirs(target.parent, exist_ok=True)
        atomic_write_bytes(target, data, mode=mode, fsync=fsync)
        return
    folder = _HeldFolder.open(str(root), target, make=True, say=_WRITTEN,
                              resolve_root=resolve_root)
    try:
        kept = _mode_at_name(folder, target)
        final = mode if mode is not None else kept

        def fill(staged: int) -> None:
            final_mode, apply = final, final is not None
            if final_mode is None:
                # A new file: the umask's mode, read off the empty file, and
                # the bytes go in owner-only until it is applied.
                final_mode = stat.S_IMODE(os.fstat(staged).st_mode)
                if final_mode & ~0o600:
                    try:
                        os.fchmod(staged, final_mode & 0o600)
                        apply = True
                    except OSError:  # a filesystem that keeps no modes
                        pass
            view = memoryview(data)
            while view:
                view = view[os.write(staged, view):]
            if apply:
                os.fchmod(staged, final_mode)
            if fsync:
                os.fsync(staged)

        _publish_staged(folder, temp_path_for(str(target)), str(target), fill,
                        mode=0o666 if final is None else 0o600)
        if fsync:
            try:
                os.fsync(folder.fd)
            except OSError:
                pass
    finally:
        os.close(folder.fd)


def _mode_at_name(folder: _HeldFolder, target: Path) -> Optional[int]:
    """The permission bits of the file at *target*'s name in *folder*, to
    carry over (``None`` when there is none); ``OSError`` for anything else
    there, a link above all (:func:`write_below_root`)."""
    try:
        info = os.lstat(target.name, dir_fd=folder.fd)
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise _respelled(exc, str(target)) from exc
    if stat.S_ISREG(info.st_mode):
        return stat.S_IMODE(info.st_mode)
    what = "a symlink" if stat.S_ISLNK(info.st_mode) else "not a file"
    raise OSError(f"{target} is {what}, so nothing was written: its name was "
                  f"resolved before the write, so a link there now was put "
                  f"there since, or leads nowhere")


def rename_below_root(root: Union[str, "os.PathLike[str]"],
                      source: Union[str, "os.PathLike[str]"], name: str, *,
                      resolve_root: bool = True) -> Path:
    """Rename *source*, a file below the folder *root* whose folder the
    caller checked (resolved, as :func:`contain_local_path` gives it), to
    *name* in that folder; the new path. The entry is renamed, never a
    link's target, and on Linux and macOS relative to the folder held as
    :func:`write_below_root` holds it, *resolve_root* included, which must
    still be the one at its path; Windows renames by path (the window
    :func:`write_below_root` names). ``OSError`` when nothing was renamed."""
    source = Path(source)
    renamed = source.with_name(name)
    if not _PUBLISHES_BY_DESCRIPTOR:
        os.replace(source, renamed)
        return renamed

    def rename(fd: int) -> None:
        try:
            os.replace(source.name, name, src_dir_fd=fd, dst_dir_fd=fd)
        except OSError as exc:
            raise _respelled(exc, str(source), str(renamed)) from exc

    _in_held_folder(root, source, _MOVED, rename, resolve_root=resolve_root)
    return renamed


def remove_below_root(root: Union[str, "os.PathLike[str]"],
                      target: Union[str, "os.PathLike[str]"]) -> None:
    """Remove the name *target*, below the folder *root* (checked as for
    :func:`rename_below_root`), relative to its folder held: the name is
    removed, never a link's target, and never a name in a folder a link
    swapped in leads to. A name already gone is nothing to remove."""
    target = Path(target)
    if not _PUBLISHES_BY_DESCRIPTOR:
        try:
            os.unlink(target)
        except FileNotFoundError:
            pass
        return

    def remove(fd: int) -> None:
        try:
            os.unlink(target.name, dir_fd=fd)
        except FileNotFoundError:
            pass
        except OSError as exc:
            raise _respelled(exc, str(target)) from exc

    _in_held_folder(root, target, _REMOVED, remove)


def _identity_of(descriptor: int) -> Optional[_Identity]:
    """The :data:`_Identity` of the file open as *descriptor*."""
    try:
        info = os.fstat(descriptor)
    except OSError:
        return None
    return info.st_dev, info.st_ino, info.st_ctime_ns


def _set_flags(staged: int, flags: int, target: str) -> None:
    """The payload's file flags (BSD, macOS) onto the staged file through its
    descriptor, as ``copystat`` sets them (a filesystem without flags is
    skipped). Python has no ``fchflags``, so libc's (:func:`_fchflags`).
    Where it cannot be called the file goes back without them and a warning
    names them: set by its name they could land on another file, a hard link
    to one outside the repository swapped in for that name included
    (docs/development/write-safety.md, restore)."""
    call = _fchflags()
    if call is not None:
        try:
            call(staged, flags)
            return
        except OSError as exc:
            if exc.errno in (errno.EOPNOTSUPP, errno.ENOTSUP):
                return
            if exc.errno != errno.ENOSYS:  # a libc stub: no such call after all
                raise
    print(f"WARNING: {target} is restored without its file flags "
          f"({_flag_names(flags)}): they can be set here only by the file's "
          f"name, which another file can be swapped in for; set them by hand "
          f"once it is back", file=sys.stderr)


def _fchflags() -> Optional[Callable[[int, int], None]]:
    """libc's ``fchflags(2)`` (BSD, macOS) as ``call(descriptor, flags)``,
    raising ``OSError``; ``None`` where Python has no ``chflags`` (no file
    flags there) or libc's cannot be loaded. Looked up on each call: a
    restore that needs it is rare."""
    if not hasattr(os, "chflags"):
        return None
    try:
        # ctypes loads only on the platform path that calls it.
        import ctypes
        import ctypes.util

        function = ctypes.CDLL(ctypes.util.find_library("c"), use_errno=True).fchflags
    except (ImportError, OSError, AttributeError):  # pragma: no cover - BSD, macOS
        return None
    # The flags are `__uint32_t` on macOS, `unsigned int` on OpenBSD and
    # `unsigned long` on FreeBSD, NetBSD and DragonFly (fchflags(2)).
    wide = sys.platform.startswith(("freebsd", "netbsd", "dragonfly"))
    function.argtypes = [ctypes.c_int, ctypes.c_ulong if wide else ctypes.c_uint]
    function.restype = ctypes.c_int

    def call(descriptor: int, flags: int) -> None:  # pragma: no cover - BSD, macOS
        if function(descriptor, flags) != 0:
            code = ctypes.get_errno()
            raise OSError(code, os.strerror(code))

    return call


def _flag_names(flags: int) -> str:
    """*flags* as ``stat``'s names (``UF_HIDDEN|SF_ARCHIVED``), bits without
    one in hex."""
    names, rest = [], flags
    for name in sorted(dir(stat)):
        bit = getattr(stat, name)
        if (name[:3] in ("UF_", "SF_") and isinstance(bit, int) and bit > 0
                and not bit & (bit - 1) and rest & bit):
            names.append(name)
            rest &= ~bit
    if rest:
        names.append(hex(rest))
    return "|".join(names) or "0x0"


def _restored_link(text: str, target: Path, root: str) -> None:
    """``restore_path``'s symlink: a link reading *text* put back at
    *target*, under a file's rules (docs/development/write-safety.md,
    restore). It is made as the staged name beside *target*, never over a
    name already there (left as it is, named); just before the rename that
    name must still be the link made (``lstat``) and read *text*
    (``readlink``), and once renamed *target* must be. On Linux and macOS
    every name is reached relative to *target*'s folder, held as
    :class:`_HeldFolder`, which must still be the folder at its path before
    the rename and after it; Windows reaches them by path. Once made, the
    link is never removed (:func:`_leave_staged`), and is recorded for the
    write checks to leave alone (:func:`restore_leftovers`)."""
    tmp = str(_staging_name(target))
    try:
        if not _STAGES_BY_DESCRIPTOR:
            _link_and_rename(None, text, tmp, str(target))
        else:
            folder = _HeldFolder.open(root, target)
            try:
                _link_and_rename(folder, text, tmp, str(target))
            finally:
                os.close(folder.fd)
    except _StagingLeft as left:
        _record_left(root, left)
        raise
    _forget_gone(root)


def _link_and_rename(folder: Optional[_HeldFolder], text: str, tmp: str,
                     target: str) -> None:
    """The link's whole life in :func:`_restored_link`: every name relative
    to *folder*'s descriptor, or by its full path without one (Windows)."""
    fd = folder.fd if folder is not None else None
    if folder is not None:
        name, target_name = os.path.basename(tmp), os.path.basename(target)
    else:
        name, target_name = tmp, target
    _refuse_a_directory(fd, target_name, target)
    try:
        os.symlink(text, name, dir_fd=fd)
    except FileExistsError as exc:
        raise _already_there(tmp) from exc
    except OSError as exc:
        raise _respelled(exc, tmp) from exc
    made: Optional[Tuple[int, int, str]] = None
    try:
        made = _link_at(fd, name)
        # Windows may spell a link's text back otherwise than it was given.
        if made is None or (folder is not None and made[2] != text):
            raise CopyNotContained(tmp, _not_the_link(tmp, target))
        if folder is not None and not folder.in_place():
            raise OSError(_folder_moved(folder, target))
        if _link_at(fd, name) != made:
            raise CopyNotContained(tmp, _not_the_link(tmp, target))
        try:
            os.replace(name, target_name, src_dir_fd=fd, dst_dir_fd=fd)
        except OSError as exc:
            raise _respelled(exc, tmp, target) from exc
    except BaseException as failure:
        if not isinstance(failure, CopyNotContained):
            now = _identity_at(name, fd)
            _leave_staged(folder, name, tmp, failure, "the link made to put back",
                          now if made is not None and now is not None
                          and now[:2] == made[:2] else None)
        raise
    if folder is not None and not folder.in_place():
        raise OSError(
            f"{folder.shown} was moved or replaced while {target} was being put "
            f"back, so what is at {target} now is not the link put back (it is "
            f"at {folder.where(target_name, target)}); check both")
    if _link_at(fd, target_name) != made:
        raise OSError(
            f"{target} did not name the link put back once it was renamed there: "
            f"another file was swapped in for {tmp} just before the rename, or "
            f"over {target} just after it, so what is at {target} now is not "
            f"the link restored; check it")


def _link_at(fd: Optional[int], name: str) -> Optional[Tuple[int, int, str]]:
    """``(st_dev, st_ino, text)`` of the symlink *name* (relative to *fd*),
    without following it; ``None`` when it is gone or not a symlink."""
    try:
        info = os.lstat(name, dir_fd=fd)
        if not stat.S_ISLNK(info.st_mode):
            return None
        return info.st_dev, info.st_ino, os.readlink(name, dir_fd=fd)
    except OSError:
        return None


def _not_the_link(tmp: str, target: str) -> str:
    return (f"{tmp} was no longer the link made there by the time it was to be "
            f"renamed over {target}, so nothing was put back, and what is at "
            f"{tmp} was left as it is")


def _already_there(tmp: str, say: _Wording = _PUT_BACK) -> CopyNotContained:
    return CopyNotContained(
        tmp, f"{tmp} was already there, so nothing was {say.done}, and it was "
             f"left as it is")


def _respelled(exc: OSError, path: str, other: Optional[str] = None) -> OSError:
    """*exc*, from a call made relative to a folder's descriptor, spelled with
    the full *path* (and *other*) it reached."""
    if other is None:
        return OSError(exc.errno, exc.strerror, path)
    return OSError(exc.errno, exc.strerror, path, None, other)


def _copy_hashed(source: int, target: int) -> str:
    """Copy every byte left in the descriptor *source* to *target*; the
    sha256 of the bytes read."""
    digest = hashlib.sha256()
    while True:
        chunk = os.read(source, 1024 * 1024)
        if not chunk:
            return digest.hexdigest()
        digest.update(chunk)
        view = memoryview(chunk)
        while view:
            view = view[os.write(target, view):]


def _restored_through_handle(calls: Any, source: str, tmp: str, target: str,
                             sha256: Optional[str]) -> None:
    """:func:`_replace_with_payload` on Windows where ``CopyFile2`` does not
    restore (docs/development/write-safety.md, restore on Windows).

    The payload is opened and held (Windows will neither delete nor rename
    it meanwhile), and its own name must be that regular file. *tmp* is made
    as a new file through the one handle :func:`_publish_bound` holds it by
    (:meth:`_HeldCopyCalls.create`): never through a link or over any name
    already there, which is left as it is, and shared for reading alone from
    its creation. The payload's bytes are written through it, and the bytes
    read must hash to *sha256* when it is given; :func:`_publish_bound` does
    the rest. Raises ``OSError`` when the handle calls cannot be loaded:
    nothing is then put back, as a restore by path could change another
    file."""
    if calls is None:
        raise OSError(
            f"the Windows calls that hold {tmp} while it is put back could not "
            f"be loaded, so nothing was put back")
    payload = os.open(source, _READ_FLAGS)
    try:
        if not _names_file(source, os.fstat(payload)):
            raise OSError(f"{source} is no longer the snapshot's payload file")
        try:
            held = calls.create(tmp)
        except FileExistsError as exc:
            raise _already_there(tmp) from exc
        try:
            digest = _copy_hashed(payload, held)
            if sha256 is not None and digest != sha256:
                raise OSError(
                    f"the snapshot payload no longer matches the manifest "
                    f"(recorded {_short(sha256)}, payload {_short(digest)}); "
                    f"nothing written")
            read = os.fstat(payload)
        except BaseException as failure:
            try:
                _dispose_held(calls, held, tmp, failure)
            finally:
                os.close(held)
            raise
        _publish_bound(calls, held, source, tmp, target, digest, read)
    finally:
        os.close(payload)


def _restored_by_copy_file2(source: str, tmp: str, target: str,
                            sha256: Optional[str]) -> bool:
    """:func:`_replace_with_payload` through ``CopyFile2`` (Windows on Python
    3.12+): ``True`` once *target* is restored, ``False`` when nothing was done
    and :func:`_restored_through_handle` restores instead, writing the
    payload's bytes itself (docs/development/write-safety.md, restore on
    Windows). Raises ``OSError`` when nothing was put back, and
    :class:`CopyNotContained` when something may be left at *tmp*.

    The payload *source* is opened and held, so Windows will neither delete
    nor rename it meanwhile. ``False`` when it is read-only (``CopyFile2``
    copies the attribute, and Windows opens a read-only file for writing to
    nobody, so the copy could not be held as :func:`_publish_held` holds it)
    or when the calls that hold it cannot be loaded. Otherwise its own name
    must be that regular file (``lstat`` against ``fstat``) and the bytes read
    through the descriptor must hash to *sha256* when it is given.
    Any name already at *tmp*, a link included, is left as it is and the
    file skipped (:func:`_already_there`), as the staged restore's exclusive
    creation refuses it: ``CopyFile2`` would follow a link to nothing there
    and create its target with the payload's bytes, its flags
    notwithstanding (:data:`_COPY_FILE2_FLAGS`). *tmp*'s token is drawn for
    this attempt (:func:`_staging_name`), so nobody can put a link there
    between that look and the copy. ``CopyFile2`` then copies the payload
    by path to *tmp* with ``COPY_FILE_FAIL_IF_EXISTS`` and
    ``COPY_FILE_COPY_SYMLINK``. A failed copy that left nothing at *tmp*
    returns ``False``; one that left something raises. The copy is checked
    and put back by :func:`_publish_held`."""
    calls = _held_copy_calls()
    if calls is None:
        return False
    payload = os.open(source, _READ_FLAGS)
    try:
        read = os.fstat(payload)
        if not stat.S_IMODE(read.st_mode) & stat.S_IWRITE:
            return False
        if not (stat.S_ISREG(read.st_mode) and _names_file(source, read)):
            raise OSError(f"{source} is no longer the snapshot's payload file")
        digest = _descriptor_sha256(payload)
        if sha256 is not None and digest != sha256:
            raise OSError(
                f"the snapshot payload no longer matches the manifest (recorded "
                f"{_short(sha256)}, payload {_short(digest)}); nothing written")
        try:
            os.lstat(tmp)
        except FileNotFoundError:
            pass
        else:
            raise _already_there(tmp)
        try:
            _COPY_FILE2(source, tmp, _COPY_FILE2_FLAGS)
            copied = _identity_at(tmp)
        except OSError as failure:
            if not os.path.lexists(tmp):
                return False
            raise _left_by_name(
                tmp, f"CopyFile2 could not copy {source} to {tmp} ({failure}), "
                     f"and what is at {tmp} was left as it is") from failure
        _publish_held(calls, source, tmp, target, payload, digest, read, copied)
        return True
    finally:
        os.close(payload)


def _publish_held(calls: Any, source: str, tmp: str, target: str, payload: int,
                  digest: str, read: os.stat_result,
                  copied: Optional[_Identity] = None) -> None:
    """Check *tmp*, ``CopyFile2``'s copy of *source* (open as *payload*,
    ``fstat`` *read*), and swap it in for *target*'s own entry, all through one
    handle on it that excludes every other writer (Windows;
    docs/development/write-safety.md, restore on Windows).

    *tmp* is bound once, by path, as itself (never through a reparse point
    there), to read, write, delete and set attributes, shared for reading
    alone: a handle already open on it to write or delete refuses the bind,
    and while it is held nobody can open it to write, rename or delete it.
    :func:`_publish_bound` does the rest, and checks too that *source* still
    names the file *payload* reads; a copy that cannot be bound raises
    :class:`CopyNotContained` naming it, the restore's own (*copied*, its
    identity once made, :func:`_left_by_name`) or not."""
    try:
        held = calls.bind(tmp)
    except OSError as exc:
        raise _left_by_name(
            tmp, f"{tmp}, the copy just made, could not be held for its checks "
                 f"({exc}), so nothing was put back", copied) from exc
    _publish_bound(calls, held, source, tmp, target, digest, read, payload=payload)


def _publish_bound(calls: Any, held: int, source: str, tmp: str, target: str,
                   digest: str, read: os.stat_result, *,
                   payload: Optional[int] = None) -> None:
    """Swap *held*, a handle on *tmp* holding *source*'s bytes that excludes
    every other writer (:meth:`_HeldCopyCalls.bind` or ``create``), in for
    *target*'s own entry, and close it (Windows).

    Through that handle alone: the file must be a regular file with one name
    and no reparse point (``os.fstat``, ``GetFileInformationByHandle``); it is
    flushed (``FlushFileBuffers``); *source* must still name the file the
    descriptor *payload* reads, when it is given (``CopyFile2`` copied it by
    path); the file, read back after the flush, must hash to *digest*; it
    takes *read*'s attributes and times, as ``copystat`` gives them; and it is
    renamed over *target*, replacing that entry, before the handle closes.
    Any failure deletes it through the handle (the name bound: never a link's
    target or another name of its file), its read-only attribute cleared
    first when this set it, and raises ``OSError``; a file that cannot be
    deleted raises :class:`CopyNotContained` naming it. Nothing here changes,
    removes or renames *tmp* by its path: between two calls a name can be
    swapped for a link to another file, a hard link to one outside the
    repository included."""
    attributes, read_only = _settable_attributes(read), False
    try:
        info = os.fstat(held)
        if not _plain_new_file(info):
            raise CopyNotContained(tmp, _not_the_copy(tmp, info))
        os.fsync(held)
        if payload is not None and not _names_file(source, os.fstat(payload)):
            raise OSError(f"{source} changed while it was copied to {tmp}")
        if _descriptor_sha256(held) != digest:
            raise OSError(f"{tmp} does not hold the bytes of {source}")
        calls.set_basic(held, attributes, read.st_atime_ns, read.st_mtime_ns)
        read_only = bool(attributes & stat.FILE_ATTRIBUTE_READONLY)
        calls.rename(held, target)
    except BaseException as failure:
        if read_only:
            # Windows deletes no read-only file, through a handle neither.
            try:
                calls.set_basic(held, attributes & ~stat.FILE_ATTRIBUTE_READONLY
                                or _FILE_ATTRIBUTE_NORMAL,
                                read.st_atime_ns, read.st_mtime_ns)
            except OSError:
                pass  # the deletion then fails, and says so
        _dispose_held(calls, held, tmp, failure)
        raise
    finally:
        os.close(held)


def _left_by_name(tmp: str, message: str,
                  copied: Optional[_Identity] = None) -> CopyNotContained:
    """What ``CopyFile2``'s restore left at *tmp*, the copy it made by that
    name (Windows): the restore's own (:class:`_StagingLeft`) while a
    regular file with one name is there, and the file read as *copied*
    (:data:`_Identity`) once the copy was made, when that is given; anything
    else there, a link or another name of a file swapped in included, is
    not its own. Made by its name, the copy has no identity from before:
    one is read now (docs/development/write-safety.md, restore on
    Windows)."""
    try:
        info = os.lstat(tmp)
    except OSError:
        return CopyNotContained(tmp, message)
    identity = (info.st_dev, info.st_ino, info.st_ctime_ns)
    if (not stat.S_ISREG(info.st_mode) or _names_another_path(info)
            or info.st_nlink != 1
            or (copied is not None and copied[:2] != identity[:2])):
        return CopyNotContained(tmp, message)
    return _StagingLeft(tmp, message, identity)


def _dispose_held(calls: Any, held: int, tmp: str, failure: BaseException) -> None:
    """Delete the file *held* through its handle once a restore through it
    failed with *failure*; what cannot be deleted is raised as
    :class:`CopyNotContained` naming *tmp*, chained to *failure*."""
    try:
        calls.dispose(held)
    except OSError as exc:
        if isinstance(failure, Exception):
            raise _StagingLeft(tmp, f"{tmp} could not be removed ({exc})",
                               _identity_of(held)) from failure


#: The attributes ``FileBasicInfo`` sets (``FILE_ATTRIBUTE_VALID_SET_FLAGS``,
#: ntifs.h: read-only, hidden, system, archive, normal, temporary, offline, not
#: content indexed); encryption and compression stay as ``CopyFile2`` made them.
_SETTABLE_ATTRIBUTES = 0x31A7
#: What sets "no attribute" (``0`` there leaves them as they are).
_FILE_ATTRIBUTE_NORMAL = 0x80


def _settable_attributes(info: os.stat_result) -> int:
    """The attributes of *info* (an ``fstat``) that ``FileBasicInfo`` sets."""
    return (getattr(info, "st_file_attributes", 0) & _SETTABLE_ATTRIBUTES
            or _FILE_ATTRIBUTE_NORMAL)


class _HeldCopyCalls:  # pragma: no cover - Windows
    """The Windows calls a restore makes on the one handle it holds the file
    it puts back by (:func:`_publish_bound`). ``_winapi.CreateFile`` binds
    it, or creates the file and binds it, wrapped as a C runtime descriptor,
    so ``os.fstat`` (``GetFileInformationByHandle``), ``os.fsync``
    (``FlushFileBuffers``), ``os.read``, ``os.write`` and ``os.close`` go
    through it; and ``SetFileInformationByHandle`` sets its attributes and
    times, renames it and deletes it."""

    #: GENERIC_READ | GENERIC_WRITE | DELETE | FILE_WRITE_ATTRIBUTES.
    _ACCESS = 0x80000000 | 0x40000000 | 0x00010000 | 0x0100
    _FILE_SHARE_READ, _CREATE_NEW, _OPEN_EXISTING = 0x1, 1, 3
    _FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000
    #: ``FILE_INFO_BY_HANDLE_CLASS``.
    _BASIC, _RENAME, _DISPOSITION = 0, 3, 4
    #: 1970-01-01 as a ``FILETIME`` (100 ns since 1601).
    _EPOCH = 116444736000000000

    def __init__(self) -> None:
        # ctypes loads only on the platform path that calls it.
        import ctypes
        from ctypes import wintypes

        set_info = ctypes.WinDLL("kernel32", use_last_error=True).SetFileInformationByHandle
        set_info.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
        set_info.restype = wintypes.BOOL

        class Basic(ctypes.Structure):  # FILE_BASIC_INFO
            _fields_ = [("CreationTime", ctypes.c_int64), ("LastAccessTime", ctypes.c_int64),
                        ("LastWriteTime", ctypes.c_int64), ("ChangeTime", ctypes.c_int64),
                        ("FileAttributes", wintypes.DWORD)]

        class Rename(ctypes.Structure):  # FILE_RENAME_INFO; the name runs on past it
            _fields_ = [("ReplaceIfExists", wintypes.DWORD), ("RootDirectory", wintypes.HANDLE),
                        ("FileNameLength", wintypes.DWORD), ("FileName", wintypes.WCHAR * 1)]

        self._ctypes, self._set_info = ctypes, set_info
        self._basic_info, self._rename_info = Basic, Rename
        self._disposition_info = wintypes.BOOLEAN  # FILE_DISPOSITION_INFO's one field

    def bind(self, path: str) -> int:
        """*path* itself, opened to read, write, delete and set attributes,
        shared for reading alone; a C runtime descriptor."""
        return self._open(path, self._OPEN_EXISTING)

    def create(self, path: str) -> int:
        """*path* made as a new file and opened as :meth:`bind` opens one;
        ``FileExistsError`` when any name is there already, a link included
        (``CREATE_NEW`` on the name itself, never followed)."""
        return self._open(path, self._CREATE_NEW)

    def _open(self, path: str, disposition: int) -> int:
        handle = _winapi.CreateFile(
            path, self._ACCESS, self._FILE_SHARE_READ, _winapi.NULL,
            disposition, self._FILE_FLAG_OPEN_REPARSE_POINT, _winapi.NULL)
        try:
            return descriptor_owning_handle(handle)
        except BaseException:
            _winapi.CloseHandle(handle)
            raise

    def set_basic(self, held: int, attributes: int, atime_ns: int, mtime_ns: int) -> None:
        """Set *attributes* and the access and write times; creation and
        change times are left as they are."""
        self._set(held, self._BASIC, self._basic_info(
            0, atime_ns // 100 + self._EPOCH, mtime_ns // 100 + self._EPOCH, 0, attributes))

    def rename(self, held: int, target: str) -> None:
        """Rename the file over *target* (a full path), replacing that entry."""
        ctypes = self._ctypes
        name = os.path.abspath(target).encode("utf-16-le")
        buffer = ctypes.create_string_buffer(ctypes.sizeof(self._rename_info) + len(name))
        info = self._rename_info.from_buffer(buffer)
        info.ReplaceIfExists, info.FileNameLength = 1, len(name)
        ctypes.memmove(ctypes.addressof(buffer) + self._rename_info.FileName.offset,
                       name, len(name))
        self._set(held, self._RENAME, buffer)

    def dispose(self, held: int) -> None:
        """Delete the name the file was bound by, once the handle closes."""
        self._set(held, self._DISPOSITION, self._disposition_info(True))

    def _set(self, held: int, kind: int, info: Any) -> None:
        ctypes = self._ctypes
        if not self._set_info(handle_of_descriptor(held), kind,
                              ctypes.byref(info), ctypes.sizeof(info)):
            raise ctypes.WinError(ctypes.get_last_error())


_HELD_COPY_CALLS: List[Any] = []


def _held_copy_calls() -> Optional[Any]:
    """:class:`_HeldCopyCalls`, loaded once; ``None`` where they cannot be,
    and a restore then copies as on the other platforms."""
    if not _HELD_COPY_CALLS:
        try:
            _HELD_COPY_CALLS.append(_HeldCopyCalls())
        except Exception:  # noqa: BLE001 - the plain copy restores instead
            _HELD_COPY_CALLS.append(None)
    return _HELD_COPY_CALLS[0]


def _descriptor_sha256(handle: int) -> str:
    """The sha256 of every byte the descriptor *handle* reads from the start."""
    os.lseek(handle, 0, os.SEEK_SET)
    digest = hashlib.sha256()
    while True:
        chunk = os.read(handle, 1024 * 1024)
        if not chunk:
            return digest.hexdigest()
        digest.update(chunk)


#: ``IsReparseTagNameSurrogate`` (WinNT.h): a reparse point naming another
#: path, as a symlink and a directory junction do.
_REPARSE_TAG_NAME_SURROGATE = 0x20000000


def _names_another_path(info: os.stat_result) -> bool:
    """Whether a name's own entry (*info*, its ``lstat``) is a reparse point
    naming another path (Windows): a directory junction, which ``lstat``
    reports as a directory, or a symlink. Other reparse points (a OneDrive
    placeholder, say) hold the file itself, and ``lstat`` resolves them."""
    return bool(getattr(info, "st_reparse_tag", 0) & _REPARSE_TAG_NAME_SURROGATE)


def remove_tree(path: str) -> List[str]:
    """Remove the folder *path* and everything in it, each entry itself, never
    what a link there leads to (``shutil.rmtree``); what is left, each with
    why, or nothing when *path* is gone or was never there.

    An entry whose removal is refused is named and never tried again, on any
    platform: a retry by path follows whatever link or junction is at its
    folder's name by then, where ``rmtree`` on Linux and macOS removes through
    the folder's descriptor. On Windows that leaves a read-only file, which
    Windows will not delete (``CopyFile2`` keeps the attribute in a blob). A
    folder left only because something in it is left is not named again."""
    left: List[str] = []
    folders: List[str] = []

    def failed(function: Any, name: str, error: BaseException) -> None:
        if isinstance(error, FileNotFoundError):
            return
        if function in (os.unlink, os.remove):
            left.append(f"{name} could not be removed ({error})")
            return
        if function is os.rmdir and getattr(error, "errno", None) == errno.ENOTEMPTY:
            folders.append(f"{name} ({error})")
            return
        left.append(f"{name} ({error})")

    if sys.version_info >= (3, 12):
        shutil.rmtree(path, onexc=failed)
    else:  # pragma: no cover - Python before 3.12
        shutil.rmtree(path, onerror=lambda function, name, info: failed(
            function, name, info[1]))
    return left or folders


def _safe_component(text: str) -> str:
    """A filesystem-safe single path component derived from ``text``.

    Never a passthrough: ``task_id`` and repo-relative paths both reach this, and
    either could carry a separator, so the sanitization is the containment for the
    snapshot tree itself.
    """
    cleaned = re.sub(r"[^A-Za-z0-9._-]", "_", text or "")
    cleaned = cleaned.strip("._") or "task"
    return cleaned[:160]


def _atomic_write(path: str, payload: str) -> None:
    """*payload* replaces *path* by ``atomic_io``'s write, 0600 and flushed,
    its folder made first — as D3f requires (an exclusively created temp file
    beside it: docs/development/runtime.md#atomic-file-writes). Below a plan's
    directory (a snapshot's manifest in the phase dir) it is published through
    its folder held there (``held_folder.write_in_plan_dir``); elsewhere (the
    out-of-grant directory in the state home) by path
    (docs/development/write-safety.md#plan-output-containment)."""
    write_in_plan_dir(path, payload.encode("utf-8"), make=True, mode=0o600)


#: How the audit log is opened to append a line: made owner-only when
#: missing, never through a link at its name, never blocking on a FIFO put
#: there (:func:`_open_to_append`).
_APPEND_FLAGS = (os.O_WRONLY | os.O_CREAT | os.O_APPEND | getattr(os, "O_NOFOLLOW", 0)
                 | getattr(os, "O_NONBLOCK", 0) | _CLOEXEC)
#: Whether the audit log's folder is held while it is opened (Linux, macOS):
#: reached from the plan's directory without following a link, a missing one
#: made relative to its parent's descriptor.
_APPENDS_HELD = bool(OPENS_WITHOUT_FOLLOWING and os.mkdir in os.supports_dir_fd
                     and os.stat in os.supports_dir_fd)


def _open_to_append(path: str) -> int:
    """A descriptor to append to the file *path*, made owner-only (0600) when
    missing; the caller closes it (:meth:`AuditLog._append`).

    Never through a symlink: ``O_NOFOLLOW`` refuses one at the name, and
    the entry opened must be a regular file that the name, never followed,
    still names. Below a plan's directory, on Linux and macOS, the file's
    folder is reached from that directory without following a link, a
    missing one made on the way, and held (:class:`_HeldFolder`); it must
    resolve inside it (``OutsidePlanDir``) and still be the folder at its
    path once the file is open. Elsewhere (the out-of-grant directory in the
    state home, Windows) the folder is made and reached by path. A hard link
    at the name is appended through, as before
    (docs/development/write-safety.md#plan-output-containment says why).
    ``OSError`` with nothing appended otherwise."""
    root = plan_dir_of(path)
    if root is not None and _APPENDS_HELD:
        target = _checked(path, root, what="append to")
        folder = _HeldFolder.open(root, target, make=True, say=_WRITTEN,
                                  resolve_root=False)
        try:
            try:
                handle = os.open(target.name, _APPEND_FLAGS, 0o600, dir_fd=folder.fd)
            except OSError as exc:
                raise _respelled(exc, str(target)) from exc
            try:
                if not folder.in_place():
                    raise OSError(_folder_moved(folder, str(target)))
                _check_appended(handle, os.lstat(target.name, dir_fd=folder.fd),
                                str(target))
            except BaseException:
                os.close(handle)
                raise
        finally:
            os.close(folder.fd)
        return handle
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    handle = os.open(path, _APPEND_FLAGS, 0o600)
    try:
        _check_appended(handle, os.lstat(path), path)
    except BaseException:
        os.close(handle)
        raise
    return handle


def _check_appended(handle: int, named: os.stat_result, path: str) -> None:
    """Refuse the descriptor *handle*, opened as *path* (whose own entry,
    never followed, is *named*), unless it is a regular file and that entry
    (:func:`_open_to_append`)."""
    opened = os.fstat(handle)
    if not (stat.S_ISREG(opened.st_mode)
            and (named.st_dev, named.st_ino) == (opened.st_dev, opened.st_ino)):
        raise OSError(
            f"{path} is not the regular file its name holds (a link, or not a "
            f"regular file), so nothing was appended to it")


# ---------------------------------------------------------------------------
# D3h — dispatch-time disjointness admission
# ---------------------------------------------------------------------------

def admit_disjoint_groups(
    tasks: Sequence[Dict[str, Any]],
    *,
    ceiling: int,
    root: Optional[str] = None,
) -> List[List[Dict[str, Any]]]:
    """Partition one batch's tasks into co-schedulable groups (D3h).

    A group may run concurrently only when every pair of its tasks declares a
    disjoint file set, every task in it declares ``can_parallelize``, and the group
    is no larger than ``ceiling``. A task declaring **no** file set runs alone —
    "undeclared" is not "touches nothing", and treating it as the latter is how a
    hand-edited task file would end up with two agents editing one file.

    Checked here rather than trusted from the batcher, which is the point: the
    batchers' partitioning invariant is real, but a regenerated or hand-edited task
    file is not bound by it.
    """
    ceiling = max(1, int(ceiling))
    groups: List[List[Dict[str, Any]]] = []
    current: List[Dict[str, Any]] = []
    current_files: Set[str] = set()

    def flush() -> None:
        nonlocal current, current_files
        if current:
            groups.append(current)
        current = []
        current_files = set()

    for task in tasks:
        declared = declared_file_set(task)
        if root is not None:
            declared = [relative_to_root(path, root) for path in declared]
        parallel_ok = bool(task.get("can_parallelize")) and bool(declared)
        if ceiling == 1 or not parallel_ok:
            flush()
            groups.append([task])
            continue
        overlap = current_files & set(declared)
        if not current:
            current = [task]
            current_files = set(declared)
            continue
        if overlap or len(current) >= ceiling:
            flush()
            current = [task]
            current_files = set(declared)
            continue
        current.append(task)
        current_files |= set(declared)
    flush()
    return groups


def overlapping_pairs(
    tasks: Sequence[Dict[str, Any]], *, root: Optional[str] = None
) -> List[Tuple[str, str, List[str]]]:
    """Every pair of tasks whose declared file sets intersect, for a refusal message."""
    resolved: List[Tuple[str, Set[str]]] = []
    for task in tasks:
        declared = declared_file_set(task)
        if root is not None:
            declared = [relative_to_root(path, root) for path in declared]
        resolved.append((str(task.get("task_id", "")), set(declared)))
    clashes: List[Tuple[str, str, List[str]]] = []
    for i in range(len(resolved)):
        for j in range(i + 1, len(resolved)):
            shared = resolved[i][1] & resolved[j][1]
            if shared:
                clashes.append((resolved[i][0], resolved[j][0], sorted(shared)))
    return clashes


# ---------------------------------------------------------------------------
# D3l — the append-only audit record
# ---------------------------------------------------------------------------

class AuditLog:
    """``{phase}/subagent_audit.jsonl``: one fsynced line per event, never a rewrite.

    What makes an unattended write run reviewable *after* the fact instead of
    merely trusted before it. Deliberately **not** a record of the prompt: the
    prompt is reduced to its sha256 and byte length, and the runner's environment
    is never touched, because prompts embed untrusted plan/diff text and an audit
    log that leaks a credential is a new vulnerability rather than a control.
    """

    #: argv elements whose *value* is redacted before logging
    #: (:data:`utils.redact.SECRET_FLAG_HINTS`).
    SECRET_FLAG_HINTS: Tuple[str, ...] = _redact.SECRET_FLAG_HINTS

    def __init__(self, phase_dir: str) -> None:
        self.phase_dir = str(phase_dir)

    @property
    def path(self) -> str:
        """Resolved on every access: a jailed repo-wide run claims its
        out-of-grant directory after the scheduler's own ``AuditLog`` exists
        (:func:`safety_dir`)."""
        return str(Path(safety_dir(self.phase_dir)) / AUDIT_FILENAME)

    # -- writing --------------------------------------------------------

    def _append(self, record: Dict[str, Any]) -> None:
        line = json.dumps(record, sort_keys=True) + "\n"
        # Never through a link, its folder held below the plan's directory
        # (docs/development/write-safety.md#plan-output-containment).
        handle = _open_to_append(self.path)
        try:
            with os.fdopen(handle, "a", encoding="utf-8") as stream:
                stream.write(line)
                stream.flush()
                os.fsync(stream.fileno())
        except BaseException:  # pragma: no cover - append must not mask a dispatch
            raise

    def dispatched(
        self,
        *,
        task_id: str,
        kind: str,
        attempt: int,
        runner: str,
        profile: str,
        cwd: Optional[str],
        sandbox_root: str,
        argv: Sequence[str],
        prompt: str,
        declared_files: Sequence[str],
        snapshot_dir: Optional[str] = None,
        snapshot_before: Optional[Dict[str, Any]] = None,
    ) -> None:
        """The pre-dispatch line. Written **before** the child starts."""
        self._append({
            "event": "dispatched",
            "timestamp": _now(),
            "task_id": task_id,
            "kind": kind,
            "attempt": attempt,
            "runner": runner,
            "profile": profile,
            "cwd": cwd,
            "sandbox_root": sandbox_root,
            "argv": _redact.redact_argv(argv, prompt),
            "prompt_sha256": _redact._sha256_text(prompt),
            "prompt_bytes": len((prompt or "").encode("utf-8")),
            "declared_files": list(declared_files),
            "snapshot_dir": snapshot_dir,
            "snapshot_before": snapshot_before or {},
        })

    def completed(
        self,
        *,
        task_id: str,
        kind: str,
        attempt: int,
        runner: str,
        profile: str,
        status: str,
        write_outcome: Optional[str],
        exit_code: Optional[int],
        files_touched: Sequence[str],
        observed: Dict[str, Any],
        duration_seconds: float,
        reason: Optional[str] = None,
        usage: Optional[Dict[str, Any]] = None,
        expected_ids: Optional[Sequence[str]] = None,
    ) -> None:
        """The post-classification line. The evidence behind D3g's verdict.

        ``usage``: optional and omitted when ``None``, so
        every existing write-path call — none of which passes it — appends a
        byte-identical record to before. The read path's judging dispatch is
        the first caller to pass it, since that record is its only durable
        home for what the dispatch cost.

        ``expected_ids``: the items the batch was materialized
        for, omitted when ``None`` (the judging dispatch has none). An apply
        batch's id is positional, so after a selection change the record a
        set-aside snapshot has to be verified against sits under an id another
        batch now owns; the items are what :meth:`completion_for` finds it by.
        """
        record: Dict[str, Any] = {
            "event": "completed",
            "timestamp": _now(),
            "task_id": task_id,
            "kind": kind,
            "attempt": attempt,
            "runner": runner,
            "profile": profile,
            "status": status,
            "write_outcome": write_outcome,
            "exit_code": exit_code,
            "files_touched": list(files_touched),
            "observed": observed,
            "duration_seconds": round(duration_seconds, 3),
            "reason": reason,
        }
        if usage is not None:
            record["usage"] = usage
        if expected_ids is not None:
            record["expected_ids"] = [str(i) for i in expected_ids]
        self._append(record)

    def skipped(
        self,
        *,
        task_id: str,
        kind: str,
        output_path: str,
        result_ids: Sequence[str],
        files_touched: Sequence[str],
    ) -> None:
        """A ``--resume`` skip. No child ran, so it is neither a dispatch nor a
        completion — but it IS a decision the run made about a task, and this file
        is the record of what the phase did.

        Measured 2026-09-16: five tasks were declared complete on a resume and the
        log jumped straight from the previous run's ``dispatched T006`` to
        ``dispatched T011``, so the one artifact whose whole job is answering
        "what did this phase actually do" had nothing to say about them.
        ``result_ids`` is the ids the trusted file itself attests to, because that
        is the field that would have shown the mismatch by eye.
        """
        self._append({
            "event": "skipped",
            "timestamp": _now(),
            "task_id": task_id,
            "kind": kind,
            "reason": "resume: result file already present and valid",
            "output_path": output_path,
            "result_ids": list(result_ids),
            "files_touched": list(files_touched),
        })

    def restored(
        self, *, task_id: str, report: Dict[str, str], force: bool,
        verified: Optional[bool] = None,
    ) -> None:
        """``util restore-batch``'s own line — a rollback is an auditable event.

        ``verified`` says whether a completion record checked the files'
        hashes first; ``False`` is the ``--force``d restore of a snapshot no
        completion record describes. Omitted when the caller did not say.
        """
        record: Dict[str, Any] = {
            "event": "restored",
            "timestamp": _now(),
            "task_id": task_id,
            "force": bool(force),
            "result": dict(report),
        }
        if verified is not None:
            record["verified"] = bool(verified)
        self._append(record)

    # -- reading --------------------------------------------------------

    def records(self) -> List[Dict[str, Any]]:
        """Every line, in order. Corrupted lines are skipped, never guessed at."""
        try:
            text = Path(self.path).read_text(encoding="utf-8")
        except OSError:
            return []
        out: List[Dict[str, Any]] = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return out

    def completion_for(
        self, task_id: str, *, expected_ids: Optional[Sequence[str]] = None,
        records: Optional[Sequence[Dict[str, Any]]] = None,
    ) -> Optional[Dict[str, Any]]:
        """The last ``completed`` record for this batch, if any.

        With ``expected_ids``, the batch is the one materialized for those
        items, whatever id it ran under: the last record naming the same items
        wins, and a record under ``task_id`` counts only when it names no
        items at all (written before the key existed). A record under the id
        that names *other* items is another batch's — an apply id is
        positional — and is never returned. Without ``expected_ids`` the id
        alone decides, as before. *records* is :meth:`records` as the caller
        just read it, for one decision that reads the log more than once;
        omitted, the log is read now.
        """
        wanted = sorted(str(i) for i in expected_ids) if expected_ids else None
        by_items = None
        by_id = None
        for record in (self.records() if records is None else records):
            if record.get("event") != "completed":
                continue
            recorded = record.get("expected_ids")
            if wanted is not None and isinstance(recorded, list):
                if sorted(str(i) for i in recorded) == wanted:
                    by_items = record
                continue
            if record.get("task_id") == task_id:
                by_id = record
        return by_items if by_items is not None else by_id

    @staticmethod
    def hashes_from(record: Optional[Dict[str, Any]]) -> Dict[str, Optional[str]]:
        """``relative -> sha256_after`` from one completion record."""
        if not record:
            return {}
        observed = record.get("observed") or {}
        return {
            str(path): (info or {}).get("sha256_after")
            for path, info in observed.items()
            if str(path) in set(record.get("files_touched") or [])
        }

    def touched_with_hashes(
        self, task_id: str, *, expected_ids: Optional[Sequence[str]] = None,
    ) -> Dict[str, Optional[str]]:
        """``relative -> sha256_after`` from the completion record (restore input)."""
        return self.hashes_from(self.completion_for(task_id, expected_ids=expected_ids))

    @staticmethod
    def _is_failed(record: Dict[str, Any]) -> bool:
        return (
            record.get("status") != "ok"
            or record.get("write_outcome") in ("partial-application", "policy-violation")
        )

    def failed_completions(self) -> List[Dict[str, Any]]:
        """The last completion of every batch that was not a clean apply.

        A batch is its id plus the items it was materialized for, so the
        resumed batch's clean completion under ``apply-batch-1`` does not
        hide the stopped batch's failure under the same positional id
        (adversarial review, 2026-10-02); a record naming no items is keyed
        by its id alone. In first-seen order.
        """
        latest: Dict[Tuple[str, Optional[Tuple[str, ...]]], Dict[str, Any]] = {}
        for record in self.records():
            if record.get("event") != "completed":
                continue
            recorded = record.get("expected_ids")
            items = (
                tuple(sorted(str(i) for i in recorded))
                if isinstance(recorded, list) else None
            )
            latest[(str(record.get("task_id")), items)] = record
        return [record for record in latest.values() if self._is_failed(record)]

    def failed_task_ids(self) -> List[str]:
        """Task ids whose last completion was not a clean apply."""
        return sorted({str(r.get("task_id")) for r in self.failed_completions()})


#: An audit record's timestamp: local time, whole seconds (``utils/clock.py``).
_now = local_iso_seconds
