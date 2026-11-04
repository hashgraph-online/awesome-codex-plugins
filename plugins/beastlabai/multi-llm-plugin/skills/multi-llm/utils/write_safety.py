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

import hashlib
import json
import os
import posixpath
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

try:  # pragma: no cover - import shim mirrors the rest of utils/
    from .git_utils import pin_repo_root
    from .process_control import FileMutex
    from .provider_registry import get_write_paths
    from .subagent_tasks import declared_file_set
except ImportError:  # pragma: no cover - direct-script import shim
    from utils.git_utils import pin_repo_root
    from utils.process_control import FileMutex
    from utils.provider_registry import get_write_paths
    from utils.subagent_tasks import declared_file_set


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
    "relative_to_root",
    "admit_disjoint_groups",
    "file_sha256",
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


def state_home() -> str:
    """``$XDG_STATE_HOME/multi-llm`` (default ``~/.local/state/multi-llm``)."""
    base = os.environ.get("XDG_STATE_HOME") or os.path.join(
        os.path.expanduser("~"), ".local", "state"
    )
    return os.path.join(base, "multi-llm")


def _phase_key(path: str) -> str:
    return hashlib.sha256(path.encode("utf-8", "surrogateescape")).hexdigest()[:32]


def _phase_binding_path(path: str) -> str:
    return os.path.join(state_home(), STATE_SUBDIR, "paths", _phase_key(path))


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
        legacy = Path(state_home()) / STATE_SUBDIR / _phase_key(given)
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
    return os.path.join(state_home(), STATE_SUBDIR, _phase_key(_bound_phase(phase_dir)))


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
            f"{state_home()} is inside {repo_root}; set XDG_STATE_HOME to a "
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
    ``paths`` as named, and ``hits`` (fix round 21), each one's
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
    try:
        from .git_utils import find_git_entry_root
    except ImportError:  # pragma: no cover - direct-script import shim
        from utils.git_utils import find_git_entry_root  # type: ignore[no-redef]
    return find_git_entry_root(probe_dir) or str(Path(probe_dir).resolve())


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
    try:
        contained = resolved.is_relative_to(resolved_root)
    except AttributeError:  # pragma: no cover - Python < 3.9
        contained = os.path.commonpath(
            [str(resolved), str(resolved_root)]
        ) == str(resolved_root)
    if not contained:
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
    # been sliced off, mirroring ``subagent_executor._is_unsafe_windows_path``.
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

    Fix round 21 (review of round 20, the run-8 case): the way forward said
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
    layer refuses the path (plans/review-commits.md §2.7, "The commit write
    policy": ``changed since reviewed commit <head7>``), ``""`` otherwise. No
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
    Plain path strings, a record from before fix round 21 that kept no rule,
    get the wording that is right for either rule.

    Fix round 20 (live run 8 #4, a user decision: permissive): the plugin
    keeps offering it, since it is the user's to decide and it lets the run
    complete, but plainly as their choice, naming the file. Fix round 21: a
    deny hit names the deny rule to narrow (the deny list wins over
    ``allow``, so "allow it" resumed into the same refusal). Every stop,
    refusal and status line that offers it says it in these words, and the
    hosts relay it as given and never change the policy themselves
    (``modes.STOP_POLICY_RULE``).
    """
    entries = list(refused or ())
    plain = [str(e) for e in entries if isinstance(e, str) and str(e)]
    hits = policy_hits(e for e in entries if not isinstance(e, str))
    if any(hit.outside or hit.protected for hit in hits):
        # Neither a path outside the repository nor one the commit review
        # protects (§2.7) is a driver.write_paths matter: no rule change
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
    """Why no policy change can let a task run (fix round 21): ``../x is
    outside the repository, so no driver.write_paths rule can allow it``,
    naming each such file as the task declared it.

    A file the commit review protects (:attr:`PolicyHit.protected`,
    plans/review-commits.md §2.7) gets :func:`protected_note`'s clause
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
#: plan (plans/review-commits.md §2.7, "The user's context plan is
#: protected"): read-only whether or not it differs from the reviewed head.
CONTEXT_PLAN_RULE = "the context plan, read-only in this review"


def protected_note(hits: Sequence[Any]) -> str:
    """The clause naming the files the commit review protects (§2.7, "The
    commit write policy"): ``the commit review protects src/b.py, which
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
    (fix round 21: a file outside the repository)."""
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
    set (plans/review-commits.md §2.7, "The commit write policy": every path
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
        for pattern, matcher in zip(self.deny, self._deny):
            if matcher.match(relative):
                return f"driver.write_paths.deny pattern {pattern!r}"
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
        relative = relative_to_root(path, self.root)
        if not self._allow:
            return "driver.write_paths.allow is empty, so nothing may be written"
        for matcher in self._allow:
            if matcher.match(relative):
                return None
        return (
            f"no driver.write_paths.allow pattern matches it "
            f"(allow: {', '.join(self.allow)})"
        )

    def hit(self, path: str) -> Optional[PolicyHit]:
        """``path``'s :class:`PolicyHit`, or ``None`` when the policy permits
        it: every deny pattern that covers it and whether ``allow`` matches
        it, so the way forward names each rule to change (fix round 21).

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
        given (fix round 21: a task's ``../x`` was named by its resolved
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
        """
        directory = Path(safety_dir(phase_dir)) / PRE_BATCH_DIRNAME / _safe_component(task_id)
        payload_dir = directory / PAYLOAD_DIRNAME
        payload_dir.mkdir(parents=True, exist_ok=True)
        entries: List[SnapshotEntry] = []
        for index, candidate in enumerate(files):
            resolved = contain_under_root(candidate, root, what="snapshot target")
            relative = relative_to_root(str(resolved), root)
            existed = resolved.is_file()
            size = resolved.stat().st_size if existed else 0
            if existed and size > MAX_SNAPSHOT_BYTES:
                raise WriteSafetyError(
                    f"Refusing to dispatch task {task_id}: {relative} is {size} "
                    f"bytes, over the {MAX_SNAPSHOT_BYTES}-byte snapshot cap. A "
                    f"batch with no rollback point is not dispatched — every "
                    f"declared file must be snapshottable (D3h)."
                )
            payload_name = f"{index:03d}-{_safe_component(relative)}"
            payload = None
            if existed:
                shutil.copy2(str(resolved), str(payload_dir / payload_name))
                payload = payload_name
            entries.append(SnapshotEntry(
                relative=relative,
                absolute=str(resolved),
                existed=existed,
                sha256=file_sha256(str(resolved)) if existed else None,
                size=size,
                payload=payload,
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
            payload_source: The retained pre-run bytes. Required when
                ``existed`` — an entry claiming a rollback point it has no copy
                for is worse than an honest ``None``, which is what this returns
                instead.
            save: Off when a caller adopts a batch of paths and saves once; the
                manifest is rewritten whole, so per-path saves are quadratic.

        Returns:
            The entry, or ``None`` when no rollback point could be recorded.
        """
        resolved = contain_under_root(relative, self.root, what="observed write")
        key = relative_to_root(str(resolved), self.root)
        existing = self.entry_for(key)
        if existing is not None:
            return existing
        # `existed=False` needs no bytes at all: the rollback for a file the
        # runner created is deletion, which `restore` already does for an entry
        # with no payload.
        payload: Optional[str] = None
        if existed:
            if not payload_source or not Path(payload_source).is_file():
                return None
            # The retained bytes are content-addressed by `sha256`; a blob
            # whose bytes no longer hash to it was rewritten after the sweep
            # retained it (the store sits where the batch can write) and is
            # no rollback point (review fixes 2026-10-05).
            if sha256 and file_sha256(payload_source) != sha256:
                return None
            payload = f"{len(self.entries):03d}-{_safe_component(key)}"
            payload_dir = Path(self.directory) / PAYLOAD_DIRNAME
            payload_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(payload_source), str(payload_dir / payload))
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

        A manifest with no parseable date cannot be placed in a cycle and is
        read as predating any cutoff given: the only such manifests are
        older than the field, and an unknown-age rollback point is kept
        aside rather than trusted as this cycle's.
        """
        if cutoff is None:
            return False
        try:
            taken = datetime.fromisoformat(self.taken_at or "")
        except ValueError:
            return True
        if taken.tzinfo is not None:
            taken = taken.astimezone().replace(tzinfo=None)
        return taken < cutoff

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
                    _replace_with_payload(source, target)
                except OSError as exc:
                    report[relative] = f"skipped: {exc}"
                    continue
                report[relative] = "restored"
            else:
                # Absent before the batch: the correct rollback is deletion.
                # `os.unlink` removes the entry itself, so a symlink left in the
                # file's place is removed rather than followed.
                try:
                    os.unlink(str(target))
                    report[relative] = "deleted"
                except FileNotFoundError:
                    report[relative] = "deleted (already absent)"
                except OSError as exc:
                    report[relative] = f"skipped: {exc}"
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
    if source is None:
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
        if os.path.islink(source):
            tmp = target.with_name(f".{target.name}.restore.{os.getpid()}.tmp")
            os.symlink(os.readlink(source), str(tmp))
            try:
                os.replace(str(tmp), str(target))
            except BaseException:
                try:
                    os.unlink(str(tmp))
                except OSError:
                    pass
                raise
        else:
            _replace_with_payload(Path(source), target)
    except OSError as exc:
        return f"skipped: {exc}"
    return "restored"


def _short(digest: Optional[str]) -> str:
    return (digest or "absent")[:12]


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
        PathEscape: any component is a symlink, or the path is not a plain
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
        if not stat.S_ISDIR(info.st_mode):
            raise PathEscape(
                f"{current} is not a directory, so {relative} cannot be restored "
                f"under the pinned repo root {resolved_root}"
            )
    return current / parts[-1]


def _replace_with_payload(source: Path, target: Path) -> None:
    """Write ``source``'s bytes as a new file and ``os.replace`` it over ``target``.

    Never ``shutil.copy2`` onto the destination: it opens the destination for
    writing and follows it, so a snapshotted regular file that has since become a
    symlink would have the saved bytes written *through* the link. ``os.replace``
    swaps the directory entry itself — atomic, and no-follow — and the temp file is
    created ``O_EXCL`` in the same revalidated directory, so it cannot land on an
    existing symlink and the rename cannot cross a filesystem.
    """
    tmp = target.with_name(f".{target.name}.restore.{os.getpid()}.tmp")
    handle = os.open(str(tmp), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(handle, "wb") as stream:
            with open(str(source), "rb") as payload:
                shutil.copyfileobj(payload, stream)
            stream.flush()
            os.fsync(stream.fileno())
        # What `copy2` preserved, minus the destination-following write.
        shutil.copystat(str(source), str(tmp))
        os.replace(str(tmp), str(target))
    except BaseException:
        try:
            os.unlink(str(tmp))
        except OSError:
            pass
        raise


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
    """Same-directory temp file, 0600, ``os.replace`` — as D3f requires."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_name(f".{target.name}.{os.getpid()}.tmp")
    handle = os.open(str(tmp), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        try:
            os.unlink(str(tmp))
        except OSError:
            pass
        raise
    os.replace(str(tmp), str(target))


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

    #: argv elements whose *value* is redacted before logging, matched
    #: case-insensitively on the flag that precedes them. Belt-and-braces: no
    #: adapter puts a secret on argv, and if one ever does this catches it.
    SECRET_FLAG_HINTS = ("key", "token", "secret", "password", "credential", "auth")

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
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(record, sort_keys=True) + "\n"
        flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND
        handle = os.open(self.path, flags, 0o600)
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
            "argv": redact_argv(argv, prompt),
            "prompt_sha256": _sha256_text(prompt),
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

        ``usage`` (F6, 2026-09-16): optional and omitted when ``None``, so
        every existing write-path call — none of which passes it — appends a
        byte-identical record to before. The read path's judging dispatch is
        the first caller to pass it, since that record is its only durable
        home for what the dispatch cost.

        ``expected_ids`` (2026-10-02): the items the batch was materialized
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
    ) -> Optional[Dict[str, Any]]:
        """The last ``completed`` record for this batch, if any.

        With ``expected_ids``, the batch is the one materialized for those
        items, whatever id it ran under: the last record naming the same items
        wins, and a record under ``task_id`` counts only when it names no
        items at all (written before the key existed). A record under the id
        that names *other* items is another batch's — an apply id is
        positional — and is never returned. Without ``expected_ids`` the id
        alone decides, as before.
        """
        wanted = sorted(str(i) for i in expected_ids) if expected_ids else None
        by_items = None
        by_id = None
        for record in self.records():
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


# ---------------------------------------------------------------------------
# Redaction over rendered text (§4.5)
# ---------------------------------------------------------------------------
#
# One boundary, four sinks: the success log (``llm_client._save_log``), the
# per-attempt failure captures (``failed/*.attemptN.json``), the batch report
# (``subagent_batch_report.json``) and the exit-3 stdout block that becomes
# ``orchestrator-run.log`` under ``--detach``. Provider stdout/stderr reached all
# four unfiltered; each growing its own filter is the shape this replaces.
#
# **This runs BEFORE any cap.** Both the 64 KiB/line rule and the last-20-lines
# rule cut by construction, and a cut applied first slices a secret into a
# remnant no pattern matches — a byte tail keeps a value whose key name is gone,
# and a line tail keeps a PEM body whose ``-----BEGIN`` header is gone. Nothing
# downstream can recover either.
#
# **Why not just reuse `.gitleaks.toml`.** gitleaks is a Go binary over a file
# tree at commit time; this runs in-process on every rendered line of every
# fan-out slot. The blast radii also run opposite ways — a commit-time false
# positive is a red PR, a runtime false negative is a live credential in
# ``log_*.txt`` — so this set is deliberately a strict *superset*, carrying PII
# and low-entropy delimiter shapes gitleaks must never flag. The one-way drift
# gate lives in ``tests/test_redaction.py``; this table is never transcribed into
# the TOML, which would make the scanner red against this repo's committed
# decoys on day one.

#: The word that makes a key name a *secret* key name.
#: ``auth``/``authorization`` are excluded **on purpose** — P2 covers the header
#: form, and a bare ``auth:`` key is far too common in this repo's auth-plan
#: fixtures. That is the one entry on which this and ``SECRET_FLAG_HINTS``
#: differ, because ``auth`` is a reliable signal in a *flag name*.
_SECRET_KEYWORD = r"(?:secret|passwd|password|token|api[_-]?key|apikey|credential)"

#: What a key name is spelled with. Note which two members are **not** word
#: characters: ``.`` and ``-``. Every ``\b`` inside a run of this class is
#: manufactured by one of those two, and that is the whole of the quadratic
#: story below.
_KEY_CHAR = r"[A-Za-z0-9_.\-]"

#: The key half of a delimited key/value secret: **one maximal run of key
#: characters that contains the keyword**, matched from the run's own start.
#:
#: Underscore/dot/dash-joined compounds around the keyword are the reason this
#: is a run at all — ``aws_secret_access_key`` is a real shape that a
#: word-anchored ``\bsecret\b`` never matches — and the run has to reach from
#: whatever precedes the keyword all the way to the delimiter.
#:
#: **The shape this replaces was quadratic, and it was quadratic at rest.**
#: It read ``\b [KEY_CHAR]* KEYWORD [KEY_CHAR]*``, two unbounded greedy runs
#: around the keyword, and nothing about the 2026-09-22 anchoring work touched
#: it — this row shipped that way for as long as the table has existed. Both
#: runs cost the same way. CPython's ``re`` retries the whole pattern at every
#: start position the left anchor admits; at each of them the leading ``*`` ran
#: to the end of the key-character run and then backtracked one character at a
#: time looking for the keyword, and every keyword it found on the way ran the
#: *trailing* ``*`` to the end of the run and backtracked that too, looking for
#: the delimiter. So the work is (start positions) x (run length), and ``\b``
#: does not bound the first factor the way it does for a prose pattern: ``.``
#: and ``-`` are in the character class **and** are non-word characters, so a
#: run densely punctuated with either manufactures a word boundary every few
#: characters while never breaking the run.
#:
#: MEASURED 2026-09-22 at HEAD, one ``pattern.sub`` pass, doubling the input:
#:
#: ===========================  =========  =========  =========
#: 1 line of...                      8 KB      16 KB      32 KB
#: ===========================  =========  =========  =========
#: prose with spaces             0.0003 s   0.0007 s   0.0014 s
#: JSON-ish                      0.0003 s   0.0005 s   0.0011 s
#: pure base64                   0.0003 s   0.0006 s   0.0012 s
#: base64url (``-``/``_``)       0.1224 s   0.4953 s   1.9670 s
#: hyphenated slugs              0.5020 s   1.9862 s   7.9555 s
#: dotted identifiers            1.0282 s   4.1735 s  16.5351 s
#: ``token.`` repeated           98.904 s          -          -
#: ===========================  =========  =========  =========
#:
#: Four-fold per doubling is n^2. Whitespace, quotes and braces break the run
#: and keep it linear, which is why prose and JSON were never slow and why
#: nobody noticed; a base64url blob, a dotted module-path list or a run of
#: hyphenated slugs on **one line** has none of them. 32 KB of dotted
#: identifiers already costs 15 s, and :func:`redact_text` runs on the FULL
#: provider stream **before** ``_bound_stream`` caps it (§14.4, and that
#: ordering is right), so a megabyte of it is hours inside every log sink.
#:
#: **The rule now.** One run, walked once::
#:
#:     (?<!KEY_CHAR)  (?= KEY_CHAR*? KEYWORD )  KEY_CHAR*   …then _DELIM, _CAND
#:      run start          the run holds it      consume it
#:
#: Three things changed, and each needs its own argument, because only the
#: third one is about speed:
#:
#: 1. *Two runs became one.* The old shape cut the run in half at the keyword
#:    and made the engine find the cut by backtracking. The keyword is still
#:    required, but as a **lookahead over the whole run** rather than as a seam
#:    inside it. That costs nothing: "a run containing the keyword" and "a run
#:    that splits into prefix + keyword + suffix" are the same set of runs, and
#:    the group that gets replaced is the **value**, which is past the run
#:    either way — so where inside the run the old pattern chose to start never
#:    affected what came out.
#: 2. *``\b`` became ``(?<!KEY_CHAR)``, and it HAD to.* The old ``\b`` guarded
#:    the start of the *leading* run, not the keyword. Keep it once the two
#:    runs are one and it demands a word boundary immediately before the
#:    keyword — which ``aws_secret_access_key`` does not have. That is exactly
#:    the narrowing a bound-the-runs-and-keep-``\b`` fix would have shipped,
#:    and it is why this row could not be repaired the way P11 was. The
#:    lookbehind that replaces it says "this is the first character of the
#:    run", which is a property of the *run* rather than of English: it is true
#:    at exactly one position inside any run, and no key name can fail it,
#:    because every run has a start.
#: 3. *The run is still unbounded, deliberately.* Bounding it is the obvious
#:    fix and it is a real narrowing — a key name with more than the bound
#:    between its last secret word and its delimiter would silently stop being
#:    redacted — so it is not what shipped. The linearity comes from the
#:    lookahead instead: a lookahead in Python is **atomic**, never re-entered
#:    on backtracking, so "does this run hold a keyword?" is asked once per
#:    RUN rather than once per keyword occurrence, and the run is then consumed
#:    exactly once. Per run of length L that is O(L) for the lookahead, O(L) to
#:    consume it and O(L) lookbehinds that fail at the other positions; runs
#:    are disjoint, so the pass is O(n).
#:
#: One property of ``_DELIM`` is doing quiet work under (3): its first
#: character is always one of ``"``, ``'``, whitespace, ``:`` or ``=``, and
#: **none of those is a key character**. So the *maximal* run is the only place
#: the delimiter can possibly match, every shorter one is dead, and a run that
#: is walked once rather than re-cut loses nothing by construction.
#:
#: DIFFERENTIALLY VERIFIED 2026-09-22 over 975 200 generated strings (random
#: character soup, random fragment soup, and the full cross product of glue x
#: keyword x separator x delimiter x value, separators up to 1 000 characters):
#: **zero** characters that the old row redacted and this one does not, and on
#: every ASCII-only input the output is byte-identical. The 21 320 inputs where
#: it differs are all the same broadening and all non-ASCII: a keyword glued
#: directly behind a word character *outside* ``[A-Za-z0-9_]`` (``ötoken=…``)
#: has no ``\b`` anywhere in front of it and was therefore invisible to the old
#: row — the same glue gap section 1b closed for the vendor prefixes, closed
#: here for free.
#:
#: And it is linear: 0.04 s per megabyte on **every** shape in the table above,
#: the 98 s one included. ``tests/test_redaction.py``'s
#: ``TestRedactTextIsLinearOnAMegabyteStream`` now runs this row against the
#: dotted, hyphenated, base64url and keyword-dense payloads with no exception
#: list at all.
_SECRET_KEY = (
    r"(?<!" + _KEY_CHAR + r")"                                  # at a run start
    r"(?=" + _KEY_CHAR + r"*?" + _SECRET_KEYWORD + r")"         # the run holds it
    + _KEY_CHAR + r"*"                                          # consume the run
)

#: An explicit ``:`` or ``=`` is mandatory, and the optional quotes are what make
#: ``"api_key": "…"`` match. **Never relax this to whitespace**: the measured
#: 114 false positives — "token generation", "password hashing", "Token refresh"
#: — all came from a whitespace-separated branch, and no real secret is emitted
#: without a delimiter.
_DELIM = r"[\"']?\s*[:=]\s*[\"']?"

#: The candidate value, qualified further by :func:`_looks_like_credential`.
_CAND = r"[^\s\"',;]{8,}"

#: Punctuation that says "expression", not "credential". Model output routinely
#: contains code, and code contains ``JWT_SECRET = os.environ.get(…)``.
_CODEY = set("(){}[]<>$\\!`|&*")

#: Values that are the keyword itself (``password=password``) or a placeholder.
_PLACEHOLDER_VALUES = {
    "password", "secret", "token", "apikey", "api_key", "credential", "passwd",
    "changeme", "example", "redacted", "required", "optional",
    "true", "false", "none", "null",
}


def _looks_like_credential(value: str) -> bool:
    """Whether a delimited value is plausibly a credential rather than code.

    Delimiter-anchoring alone is not sufficient — it still fires on
    ``password=password``, ``JWT_SECRET = os.environ.get(…)`` and
    ``password_hash=bcrypt.hashpw(…)`` in the e2e response fixtures. This is the
    other half of the precision story, and it is not optional.
    """
    if len(value) < 8 or (_CODEY & set(value)):
        return False
    if value.strip("'\"").lower() in _PLACEHOLDER_VALUES:
        return False
    # A bare integer is a count, never a credential. Measured 2026-09-17 on a
    # real ``claude -p --output-format json`` failure: the envelope's
    # ``"cacheReadInputTokens":<eight digits>`` matched the key half on
    # ``token`` and this predicate on "has a digit", so the count came out as
    # ``<redacted:secret-kv>`` and the one JSON document in
    # ``log_claude-code_*.txt`` stopped parsing — the salvage gate then read
    # the mangled excerpt as a truncated structure. Every token counter claude
    # emits (``output_tokens``, ``inputTokens``, ``thinkingTokens``, …) carries
    # the keyword, and a review's counters routinely pass eight digits.
    if value.isdigit():
        return False
    return (
        any(c.isdigit() for c in value)
        or (any(c.isupper() for c in value) and any(c.islower() for c in value))
        or any(c in "-_./+=" for c in value)
    )


#: ``(name, compiled pattern, group to replace, predicate)``. The *value* is
#: replaced, never the whole line, so surrounding text stays diffable and a
#: redacted log is still a usable failure artifact.
#:
#: Order is load-bearing in one direction only: the multi-line and prefix shapes
#: run before the generic key/value branch, so a value they already replaced
#: reaches P1 as ``<redacted:…>`` — which ``_looks_like_credential`` rejects on
#: its angle brackets. That is also what makes :func:`redact_text` idempotent.
_REDACTIONS: List[Tuple[str, Any, int, Optional[Any]]] = [
    # P12 — multi-line, so it runs first: nothing else may chew its body.
    (
        "pem-private-key",
        re.compile(
            r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----"
        ),
        0,
        None,
    ),
    # P13 — identity/PII (§5.2), in the **two shapes the probe boundary really
    # emits**, both of them key-named. A bare unkeyed email pattern is still
    # deliberately not shipped: it would redact commit-message prose in
    # container_turns/.
    #
    # (a) The quoted-JSON key form — what `cursor-agent about|status --format
    # json` returns. The value bound is `+`, not `{3,}`: a two-character shell
    # (`sh`) is as much an identity field as a long one, and the old floor let
    # it through unredacted.
    (
        "identity-json",
        re.compile(
            r"[\"'](?:userEmail|email|terminalProgram|shell)[\"']\s*:\s*[\"']([^\"']+)[\"']"
        ),
        1,
        None,
    ),
    # (b) The `Key  Value` text table a build **without** `--format` prints, and
    # which `providers.cursor_agent._about_text_pairs` parses — reachable since
    # `about` was wired back in as `setup_probe`, so an unmatched line here is a
    # real identity value in a probe tail and in `CursorAbout.redacted`. Kept
    # tight so `shell = …` and `email = …` in prose and source stay untouched:
    # the label **starts the line**, the separator is that parser's own (`: `,
    # two spaces, or a tab) and the value runs to end of line. The label's
    # separator spellings are accepted because the same parser normalizes them
    # away before it looks the key up.
    (
        "identity-text",
        re.compile(
            r"(?im)^[ \t]*(?:user[ _\-]?email|email|terminal[ _\-]?program|shell)"
            r"(?:[ \t]*:[ \t]+|[ \t]{2,}|\t[ \t]*)(\S[^\n]*?)[ \t]*$"
        ),
        1,
        None,
    ),
    # P3–P10 — vendor prefixes, every one qualified by length and charset so a
    # short decoy is a non-match by construction rather than by exception.
    #
    # **The left anchor is per-prefix, and `\b` is not the default.** A leading
    # `\b` says "this shape may not begin inside a token", which is true of
    # prose and false of a credential: a key glued to a preceding word character
    # is still the key. MEASURED 2026-09-22 against a real claude-code
    # transcript, where a probe script printed the word `SET` with the value
    # glued straight onto it — `SETsk-proj-…`, `SETsk-or-v1-…` — after an
    # environment variable's name and a delimiter. `T` followed by `s` is not a
    # word boundary, so not one vendor pattern fired. The `OPENAI_API_KEY` line
    # survived anyway on P1's key half; the line whose key name was the bare
    # word `KEY` matched no key half either and reached disk intact. Agents
    # concatenate, and a rendered log is full of other programs' output, so
    # every row below was vulnerable in isolation.
    #
    # The anchor a row gets is decided by ONE question — *can this row's prefix
    # literal occur inside ordinary text whose tail its body charset accepts?*
    # — and the answer puts it in one of three tiers:
    #
    # * **No left anchor** for a prefix English cannot reach at all: `xox?-`,
    #   `AIza`, `glpat-`, `hf_`, `eyJ` + its two dots, `AKIA`/`ASIA`, and a URL
    #   scheme (which needs `://…:…@` besides). `AKIA`/`ASIA` earn it despite
    #   `ASIA` being an English word: the body is `[0-9A-Z]{16}`, so "inside a
    #   token" here means inside a 20-char uppercase blob, never prose —
    #   word-hood was not what that `\b` was protecting.
    # * **`(?<![a-z])`** for the two prefixes English *can* reach, and which it
    #   can only ever reach with a **lowercase letter** immediately before them.
    #   `sk-` ends `task`, `risk`, `disk`, `ask`, and the body accepts hyphens,
    #   so every vendor infix has a constructible compound behind it —
    #   `risk-ant-colony-optimization-solver`,
    #   `task-or-v1-branch-protection-rules`,
    #   `disk-live-migration-controller`. `gh[opusr]_` is reachable through the
    #   `-s` plural (`laughs_`, `weighs_`, `coughs_`) plus a 16-character run
    #   with no underscore in it. In every one of those the character before the
    #   prefix is lowercase, while the glue this fix exists for is uppercase, a
    #   digit, `_` or punctuation — `sk`/`gh` are lowercase, so a letter before
    #   them is a camelCase transition and never a word. The lookbehind
    #   therefore keeps the whole measured class and gives up exactly one glue:
    #   a lowercase letter. Stated rather than implied, because it is the one
    #   place this fix is narrower than an unanchored sweep would be.
    # * **`\b`, unchanged** for the two genuinely ambiguous ones: bare `sk-`
    #   plus 16 body characters is `task-oriented-development-workflow`,
    #   `risk-projection-model` and this repo's own `ask-suggestion-advisory`,
    #   none of which a lookbehind would save; and P2's `bearer`/`basic` end
    #   `forbearer` and `ultrabasic`, either of which would then eat the next
    #   eight-character word.
    #
    # Nothing below narrows: each row's old anchored language is a subset of
    # its new one, so this is broader redaction and never less.
    (
        "sk-family",
        re.compile(
            r"(?:(?<![a-z])sk-(?:ant-|proj-|or-v1-|live-)|\bsk-)[A-Za-z0-9_\-]{16,}\b"
        ),
        0,
        None,
    ),
    ("slack", re.compile(r"xox[baprse]-[A-Za-z0-9-]{8,}\b"), 0, None),
    ("github", re.compile(r"(?<![a-z])gh[opusr]_[A-Za-z0-9]{16,}\b"), 0, None),
    ("google-api-key", re.compile(r"AIza[0-9A-Za-z_\-]{35,}"), 0, None),
    ("aws-access-key-id", re.compile(r"(?:AKIA|ASIA)[0-9A-Z]{16}\b"), 0, None),
    ("gitlab-pat", re.compile(r"glpat-[A-Za-z0-9_\-]{20,}\b"), 0, None),
    ("huggingface", re.compile(r"hf_[A-Za-z0-9]{30,}\b"), 0, None),
    (
        "jwt",
        re.compile(r"eyJ[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}\b"),
        0,
        None,
    ),
    # P11 — the password half only; the username survives so the URL stays
    # recognisable in a failure artifact. Unanchored: the scheme is lowercase,
    # so `\b` already let a lowercase glue through by matching the glue itself
    # as part of the scheme (`xhttps://…`) while refusing `SEThttps://…` — an
    # inconsistency, not a control, and the group replaced is the password
    # either way.
    #
    # **The scheme run is BOUNDED, and that bound is load-bearing** (measured
    # 2026-09-22). This is the one row whose pattern opens with a character
    # class rather than a literal, so CPython cannot skip start positions with
    # its literal-prefix scan — every other row here begins `sk-`, `xox`, `gh`,
    # `AIza`, `AKIA`, `glpat-`, `hf_` or `eyJ` and is scanned in C. Dropping
    # `\b` therefore took the start positions from "one per word" to "one per
    # character", and with `*` each of them greedily ran to the end of the
    # buffer and backtracked looking for `://`: **quadratic**. Measured on a
    # run of one character, 0.16 s at 20 KB, 2.5 s at 80 KB, 40 s at 320 KB,
    # which is ~1600 s on the 2 MB a provider really can emit — and `redact_text`
    # runs on the FULL stream **before** `_bound_stream` caps it (§14.4, and
    # that ordering is right), so an unbounded quantifier here is a hang in
    # every log sink rather than a slow test. `{0,31}` makes the work per start
    # position constant, so the row is linear again: 0.038 s at 1.28 MB, the
    # same class as the rest of the table.
    #
    # It costs no coverage. The bound is on a *suffix* of the scheme and the
    # pattern is unanchored, so a scheme longer than 32 characters simply
    # matches starting later and replaces the same group — every string the
    # `\b`-anchored original redacted is still redacted, and so is every string
    # the unbounded version was redacting.
    (
        "url-basic-auth",
        re.compile(r"[a-z][a-z0-9+.\-]{0,31}://([^/\s:@]+):([^/\s@]+)@"),
        2,
        None,
    ),
    # P2 — the header form, and the one place `bearer`/`basic` are keywords.
    # `\b` stays: see the third tier above.
    (
        "auth-scheme",
        re.compile(r"(?i)\b(?:authorization\s*:\s*)?(?:bearer|basic)\s+([A-Za-z0-9._\-+/=]{8,})"),
        1,
        None,
    ),
    # P1 — the generic delimited key/value branch, last and predicate-gated.
    # No left anchor: ``_SECRET_KEY`` carries its own, and it is a run-start
    # lookbehind rather than ``\b`` — see the analysis over that constant for
    # why the two are not interchangeable here and why the old ``\b`` shape was
    # quadratic on one line of dotted or hyphenated provider output.
    (
        "secret-kv",
        re.compile(r"(?i)" + _SECRET_KEY + r"(?:" + _DELIM + r")(" + _CAND + r")"),
        1,
        _looks_like_credential,
    ),
]


def _replace_group(match: "re.Match", group: int, name: str) -> str:
    """The matched text with ``group`` swapped for ``<redacted:{name}>``."""
    start, end = match.span(group)
    if start < 0:  # an optional group that did not participate
        return match.group(0)
    base = match.start()
    return match.group(0)[: start - base] + f"<redacted:{name}>" + match.group(0)[end - base:]


def redact_text(text: str) -> str:
    """Credential- and identity-shaped values in ``text``, replaced in place.

    Applied to the **fully rendered** line — and always *before* any truncation
    cap, which is why L3 and L4 land together. The matched value is replaced with
    ``<redacted:{name}>``; the surrounding text is untouched.

    Out of scope, stated rather than implied: a high-entropy value with no
    keyword, no prefix and no delimiter (a bare 40-char blob in prose) cannot be
    caught by regex. That is accepted — keeping the credential out of the child's
    environment in the first place is the primary control, and this is the
    backstop.
    """
    if not text:
        return text or ""
    out = text
    for name, pattern, group, predicate in _REDACTIONS:
        def _sub(match, _name=name, _group=group, _predicate=predicate):
            if _predicate is not None and not _predicate(match.group(_group)):
                return match.group(0)
            return _replace_group(match, _group, _name)

        out = pattern.sub(_sub, out)
    return out


def redact_argv(argv: Sequence[str], prompt: str) -> List[str]:
    """The rendered argv with the prompt elided and any secret-shaped value cut.

    The prompt becomes ``<prompt sha256:… bytes:…>`` so the audit record proves
    *which* prompt ran without carrying its bytes.

    Two passes, and the flag-hint one is **kept, not replaced** (§4.5.5): knowing
    a value's *position* from ``--api-key`` is strictly stronger than any pattern
    and catches the bare high-entropy blob no regex can. Every argument that
    survives that pass then goes through :func:`redact_text`, which closes the
    inverse hole — a secret in an argument that carries no hinted flag.
    """
    digest = _sha256_text(prompt)
    length = len((prompt or "").encode("utf-8"))
    out: List[str] = []
    redact_next = False
    for arg in argv:
        if prompt and arg == prompt:
            out.append(f"<prompt sha256:{digest} bytes:{length}>")
            redact_next = False
            continue
        if redact_next:
            out.append("<redacted>")
            redact_next = False
            continue
        lowered = arg.lower()
        if arg.startswith("-") and any(
            hint in lowered for hint in AuditLog.SECRET_FLAG_HINTS
        ):
            if "=" in arg:
                out.append(arg.split("=", 1)[0] + "=<redacted>")
                continue
            out.append(arg)
            redact_next = True
            continue
        out.append(redact_text(arg))
    return out


def _sha256_text(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S")
