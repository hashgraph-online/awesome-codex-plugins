"""The apply guard of a commit review: which validated fixes may still land.

A commit review judges ``base..head``, but apply-code-fixes edits the working
tree, which can have moved on since ``head``: later commits, uncommitted
edits, a file recreated or deleted on disk. A fix is a prose instruction a
model carries out against the ``head`` text it was written for, so applying it
to a file that no longer holds that text patches code nobody reviewed
(plans/review-commits.md §2.7). This module owns that decision, for every
apply path alike (the ``--apply-commit-fixes`` front door, improve-commits'
apply step on both legs, a plain ``apply-code-fixes <brief>``, and
``apply-code-fixes <plan>`` after a direct ``--head-ref`` review), because the
apply phase's one hook calls it, keyed on the endpoints state pins
(``commit_range.pinned_endpoints``):

- **The decision** (:func:`take_guard`), per group (one fix item): a group
  naming the context plan (by its own name, or a symlinked plan's target's,
  :func:`context_plan_paths`) is skipped first, then a group with any fix file
  :func:`git_utils.paths_changed_since` marks (THE one change test, shared
  with §2.5's drift list), then one naming a path of the protected set. No
  group is ever partly applied, so every count is in groups.
- **The protected set**: every path that differs from ``head`` anywhere in the
  repository (``git diff --name-only <head>`` plus untracked, non-ignored
  files and skip-worktree/assume-unchanged entries; workflow paths left
  out), saved with the blob id of its disk content
  and a byte copy under ``apply-fixes/protected/`` for the native leg's way
  back (never of a path ``driver.write_paths.deny`` names, which keeps
  secrets out of the run's artifacts, :func:`copy_protected`). The context plan joins it as a watched path (``context_plan_id``)
  when it is not already in it, and so does each in-repository target of a
  symlinked plan (``context_plan_targets``) (:func:`watched_ids`). The
  write-policy legs (T6b) deny writes to all of them, and check them after
  every batch on their own
  (:func:`protected_violations`), never only through the executor's
  undeclared-write sweep, each against the ids read as that batch started
  (the executor's pre-batch read; natively, ``util write-prompt``'s
  :func:`bind_watched`), so a user's edit between batches is never a batch's
  violation. A watched path that cannot be read is named once, when the
  guard is taken (``guard["unreadable"]``), never failed batch after batch.
- **Expectations, never approvals**: each file the guard lets through is
  saved as the content it must still have (``{"kind": "head", "blob": …}``),
  later re-pinned to the bytes a completed batch left (``{"kind": "batch",
  "sha256": …}``). Every batch is re-checked against them right before it is
  dispatched (:func:`recheck_files`), so a saved decision is never replayed.
- **The ``[COMMIT_FIXES]`` block** and the result line's ``commit_fixes``,
  rendered from the saved guard (:func:`fixes_from_state`), so the hook's
  printed block, ``status``'s copy of it for a detached run, and the tool
  routes' rendering all read one record.
- **Which review a no-argument ``--apply-commit-fixes`` applies**
  (:func:`select_review`) and the refusal for a range with no completed review
  (:func:`require_completed_review`), which the front door calls.

The guard lives under whichever record ``pinned_endpoints`` sourced
(``commit_range.guard``, or ``head_ref.guard`` after a direct run), and the
review round that replaces the groups removes it (§2.1). Every git call goes
through ``git_utils._run_git`` / ``git_argv``.
"""

from __future__ import annotations

import copy
import json
import os
import posixpath
import re
import shutil
import stat
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple

from .commit_range import (
    BLOCK_SUBJECT_CHARS,
    NOTHING_TO_REVIEW,
    FixBlock,
    RangeError,
    display_range,
    pinned_endpoints,
    pinned_record,
    pinned_spelling,
    render_fix_block,
    resolve_commit_strict,
)
from .commit_review import (
    SLUG_PATTERN,
    CommitReviewError,
    commit_review_artifact,
    commit_reviews_folder_rel,
    output_dir_for_brief,
    repo_root_of,
)
from .git_utils import (
    _run_git,
    _run_git_for_paths,
    blobs_in_commit,
    deleting_commit,
    git_argv,
    git_path,
    paths_changed_since,
    paths_in_commit,
    subtract_baseline,
)
from .text_clip import clip, plain_line

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: The pre-dispatch re-check's line for a batch it stops (T6b prints it).
STALE_MARKER = "[COMMIT_FIXES_STALE]"
#: The native leg's refusal when a batch wrote a protected path (T6b).
PROTECTED_MARKER = "[COMMIT_PROTECTED_WRITE]"
#: The commit block's line naming the review a no-argument apply picked.
SELECTED_MARKER = "[COMMIT_REVIEW_SELECTED]"
#: The exit-3 refusal when no completed review fits.
NOT_FOUND_MARKER = "[COMMIT_REVIEW_NOT_FOUND]"

#: ``guard.skipped[<gid>].reason`` values (CONTRACTS.md, "The apply guard record").
REASON_CHANGED = "changed"
REASON_CONTEXT_PLAN = "context_plan"
REASON_PROTECTED = "protected"

#: The ``status`` a guard-skipped group carries in ``skipped_items`` and
#: ``summary.md``: the plugin's skip, never a validation verdict or a judge's.
GUARD_SKIP_STATUS = "commit_guard"

#: Where the protected files' bytes are copied, inside the apply phase dir.
PROTECTED_COPIES_DIR = "protected"
#: The guard key holding the context plan's disk id when the guard was taken
#: (set only when the plan is inside the repository and not protected).
CONTEXT_PLAN_ID_KEY = "context_plan_id"
#: The guard key holding, when the context plan is a symlink, the other
#: in-repository paths its chain passes through down to the file holding
#: its text, with their disk ids when the guard was taken (``{path: id}``):
#: the context plan's name keeps the link's own name, so a fix or a batch
#: naming the target would otherwise reach the plan's text unseen
#: (:func:`context_plan_paths`).
CONTEXT_PLAN_TARGETS_KEY = "context_plan_targets"
#: The guard key naming the watched paths that could not be read when they
#: were saved (``[path, …]``, set only when there are some): the write legs
#: cannot see a batch write them, so the block says so (:func:`_note_unreadable`).
UNREADABLE_KEY = "unreadable"
#: The guard key holding, per native batch, the watched set's disk ids read
#: when ``util write-prompt`` bound its prompt (``{task_id: {path: id}}``):
#: ``util batch-done`` compares with them, so only a change made while that
#: batch ran counts, as the executor's pre-batch read does
#: (:func:`bind_watched`). A resumed decision drops them.
BOUND_KEY = "bound"
#: The full protected list, written beside them when the prompt names only some.
PROTECTED_LIST_FILE = "protected_paths.txt"
#: How many protected paths a fix prompt names before pointing at the list.
PROTECTED_NAMED_MAX = 20

#: ``; also: …`` names at most this many other reviews (§2.7 "Other reviews").
SELECTED_ALSO_MAX = 3
#: The exit-3 listing shows this many newest candidates.
NOT_FOUND_ROWS = 5

_FULL_SHA = re.compile(r"[0-9a-f]{40}|[0-9a-f]{64}")
_SLUG_RE = re.compile(SLUG_PATTERN)

# Markers on a protected path's saved id that is not a file's blob id.
_DIRECTORY = "directory"
_UNREADABLE = "unreadable"
_SYMLINK_PREFIX = "symlink:"
#: A FIFO, socket or device: no bytes to hash, so its kind is its identity
#: (a batch that replaces it with a file still changes the id).
_SPECIAL_PREFIX = "special:"


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------


def _now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _plural(count: int, singular: str, plural: Optional[str] = None) -> str:
    return f"{count} {singular if count == 1 else (plural or singular + 's')}"


def _inside(name: str) -> bool:
    """Whether a path in git's form names something inside the repository."""
    return bool(name) and not os.path.isabs(name) and not name.startswith("/") \
        and name != ".." and not name.startswith("../")


def _git_name(path: str, cwd: Optional[str]) -> str:
    """*path* in git's form, with ``.`` and ``..`` segments resolved the way
    git's own pathspec normalisation resolves them (lexically), so
    ``docs/../docs/x.md`` is ``docs/x.md`` and compares equal to the context
    plan and the guard's keys, while ``a/../../x`` stays outside the
    repository (``../x``)."""
    name = git_path(str(path).strip(), repo_root=cwd)
    if name and not os.path.isabs(name) and not name.startswith("/"):
        parts = name.split("/")
        if "." in parts or ".." in parts:
            name = posixpath.normpath(name)
    return name


def guard_record(state: Optional[Mapping[str, Any]]) -> Optional[Dict[str, Any]]:
    """The live ``guard`` of the record ``pinned_endpoints`` sources, or None."""
    record = pinned_record(state)
    if record is None:
        return None
    guard = record.get("guard")
    return guard if isinstance(guard, dict) else None


def skip_reason(reason: str, *, head: str, context_plan: Optional[str] = None) -> str:
    """The words every surface prints for a guard skip (§2.7)."""
    if reason == REASON_CONTEXT_PLAN:
        return f"context plan {plain_line(context_plan or '')} is read-only in this review"
    return f"file changed since reviewed commit {head[:7]}"


def group_files(group: Mapping[str, Any], *, repo_root: Optional[str]) -> List[str]:
    """Every distinct fix ``file`` a group names, in git's form, primary first.

    A group is one fix item whose prompt carries every suggestion's
    description, so every file they name is a target (§2.7, "On a mismatch,
    the whole group is skipped"). A group with no suggestions falls back to
    its own ``file``.
    """
    names: List[str] = []
    suggestions = group.get("suggestions") or []
    raw = [s.get("file") for s in suggestions if isinstance(s, Mapping)]
    if not suggestions:
        raw.append(group.get("file"))
    for value in raw:
        if not isinstance(value, str) or not value.strip():
            continue
        names.append(_git_name(value, repo_root))
    return list(dict.fromkeys(names))


def _group_id(group: Mapping[str, Any]) -> str:
    from .human_decisions import group_id_of

    return group_id_of(dict(group))


# ---------------------------------------------------------------------------
# Disk identities and the protected set
# ---------------------------------------------------------------------------


def _not_for_stdin_paths(name: str) -> bool:
    """Whether ``git hash-object --stdin-paths`` could read *name* as another
    path: a line holding a newline is split, and a line starting with ``"``
    is C-unquoted (``hash_stdin_paths``), so ``"x"`` is hashed as ``x``.
    Every name git would C-quote (a ``"`` or ``\\`` anywhere, a control
    character, any non-printable character, an undecodable byte carried as a
    surrogate) is hashed alone with the name in argv instead."""
    return '"' in name or "\\" in name or not name.isprintable()


def disk_blob_ids(paths: Iterable[str], *, cwd: str) -> Dict[str, Optional[str]]:
    """``{path: id}`` of each path's disk entry, as the protected set saves it.

    A regular file's id is ``git hash-object --no-filters`` of its bytes (one
    ``--stdin-paths`` call over all of them; a name that list cannot carry as
    itself, :func:`_not_for_stdin_paths`, is hashed alone with the name in
    argv), a symlink's is its target text, a directory is ``directory``, a
    FIFO, socket or device is ``special:<kind>``, and a path absent on disk
    is ``None``. An entry that cannot be read reads ``unreadable``, an
    identity of its own (:func:`identity_changed`): the guard names such a
    path when it decides (``guard["unreadable"]``), and a move between
    readable and unreadable is a change. *cwd* is the repository root
    (``--stdin-paths`` reads a relative name from the top level, not from a
    subdirectory); an absolute path is hashed where it is.
    """
    ids: Dict[str, Optional[str]] = {}
    to_hash: List[str] = []
    alone: List[str] = []
    for path in dict.fromkeys(paths):
        full = os.path.join(cwd, path)
        try:
            info = os.lstat(full)
        except (FileNotFoundError, NotADirectoryError):
            ids[path] = None
            continue
        except OSError:
            ids[path] = _UNREADABLE
            continue
        if stat.S_ISLNK(info.st_mode):
            try:
                ids[path] = _SYMLINK_PREFIX + os.readlink(full)
            except OSError:
                ids[path] = _UNREADABLE
            continue
        if stat.S_ISDIR(info.st_mode):
            ids[path] = _DIRECTORY
            continue
        if not stat.S_ISREG(info.st_mode):
            ids[path] = f"{_SPECIAL_PREFIX}{stat.S_IFMT(info.st_mode):o}"
            continue
        (alone if _not_for_stdin_paths(path) else to_hash).append(path)
    for path in alone:
        ids[path] = _hash_one(path, cwd)
    if to_hash:
        try:
            result = subprocess.run(
                git_argv("hash-object", "--no-filters", "--stdin-paths", cwd=cwd),
                input="\n".join(to_hash) + "\n",
                capture_output=True, text=True, encoding="utf-8",
                errors="surrogateescape", cwd=cwd,
            )
            lines = result.stdout.split()
            ok = result.returncode == 0 and len(lines) == len(to_hash)
        except (OSError, ValueError):
            ok, lines = False, []
        if ok:
            ids.update(zip(to_hash, lines))
        else:
            # One unreadable file fails the whole batch: hash each alone so the
            # rest keep real ids.
            for path in to_hash:
                ids[path] = _hash_one(path, cwd)
    return ids


def _hash_one(path: str, cwd: str) -> str:
    """One file's ``git hash-object --no-filters`` id, the name in argv (so a
    newline or a leading quote in it is carried as is), or ``unreadable``."""
    try:
        one = subprocess.run(
            git_argv("hash-object", "--no-filters", "--", path, cwd=cwd),
            capture_output=True, text=True, encoding="utf-8",
            errors="surrogateescape", cwd=cwd,
        )
    except (OSError, ValueError):
        return _UNREADABLE
    value = one.stdout.strip()
    return value if one.returncode == 0 and value else _UNREADABLE


def identity_changed(before: Optional[str], now: Optional[str]) -> bool:
    """Whether a watched path's disk identity moved from *before* to *now*
    (both :func:`disk_blob_ids` values).

    ``unreadable`` is an identity of its own. A move between readable and
    unreadable (either way) is a change. ``unreadable`` on both sides is
    not: nothing can be compared, and counting it would fail every batch,
    whatever it wrote, with a reason that is not true. The guard decides
    about such a path once instead, when it is taken: it names it in the
    ``[COMMIT_FIXES]`` block (``guard["unreadable"]``) and skips every group
    whose fix files include it (:func:`take_guard`)."""
    return before != now


def _note_unreadable(guard: Dict[str, Any]) -> None:
    """Set ``guard["unreadable"]`` to the watched paths (:func:`watched_ids`)
    whose saved id is ``unreadable``, sorted, or drop the key when none is:
    the paths the write legs cannot watch, which the ``[COMMIT_FIXES]``
    block names (:func:`fix_block`)."""
    found = sorted(path for path, value in watched_ids(guard).items()
                   if value == _UNREADABLE)
    if found:
        guard[UNREADABLE_KEY] = found
    else:
        guard.pop(UNREADABLE_KEY, None)


def _workflow_filter(paths: Sequence[str], *, cwd: str, plan_path: Optional[str],
                     out_dir: Optional[str]) -> List[str]:
    """*paths* without the workflow's own files and every commit review's.

    The plan or brief, its output folder (``state.json``, the phase dirs, the
    protected copies themselves), its task list, and every brief and report
    folder of the commit-reviews folder: ``code_only_rule`` and the run's own
    writers govern those (§2.7, "The set").
    """
    from .output_handler import workflow_file_entries

    workflow = workflow_file_entries(
        plan_path, root=cwd, output_dirs=[out_dir] if out_dir else [],
    )
    kept = subtract_baseline(paths, workflow) if workflow else list(paths)
    folder = commit_reviews_folder_rel(cwd)
    if folder:
        kept = [path for path in kept if not commit_review_artifact(path, folder)]
    return kept


def protected_paths(head: str, *, cwd: str, plan_path: Optional[str] = None,
                    out_dir: Optional[str] = None) -> Optional[List[str]]:
    """Every path that differs from *head* anywhere in the repository.

    ``git diff --name-only --no-renames -z <head>`` (later commits, staged and
    unstaged edits, deletions; both sides of a move) plus ``git ls-files
    --others --exclude-standard -z`` (untracked, non-ignored files) plus
    ``git ls-files -v -z``'s entries tagged ``S`` (skip-worktree) or with a
    lowercase tag (assume-unchanged), whose disk copy ``git diff`` never reads
    and :func:`git_utils.paths_changed_since` therefore marks changed (its
    third read), so an edit hidden behind either flag is protected too. A
    skip-worktree entry absent on disk is left out: that is the state a sparse
    checkout leaves every path outside its cone in, with no edit to protect.
    Workflow paths are left out. ``None`` when any read fails: the caller
    must not take an unanswered question as an empty set.
    """
    found: List[str] = []
    stdout, stderr, rc = _run_git_for_paths(
        "diff", "--name-only", "--no-renames", "-z", head, "--", cwd=cwd,
    )
    if rc != 0:
        print(f"Warning: git diff --name-only {head[:12]} failed: "
              f"{(stderr or '').strip()[:200]}", file=sys.stderr)
        return None
    found.extend(name for name in stdout.split("\0") if name)
    stdout, stderr, rc = _run_git_for_paths(
        "ls-files", "--others", "--exclude-standard", "-z", cwd=cwd,
    )
    if rc != 0:
        print(f"Warning: git ls-files --others failed: "
              f"{(stderr or '').strip()[:200]}", file=sys.stderr)
        return None
    found.extend(name for name in stdout.split("\0") if name)
    stdout, stderr, rc = _run_git_for_paths("ls-files", "-v", "-z", cwd=cwd)
    if rc != 0:
        print(f"Warning: git ls-files -v failed: "
              f"{(stderr or '').strip()[:200]}", file=sys.stderr)
        return None
    for record in stdout.split("\0"):
        tag, _, name = record.partition(" ")
        if not name or not (tag == "S" or (tag.isalpha() and tag.islower())):
            continue
        if tag in ("S", "s"):
            try:
                os.lstat(os.path.join(cwd, name))
            except (FileNotFoundError, NotADirectoryError):
                continue  # a sparse checkout's out-of-cone path: nothing on disk
            except OSError:
                pass  # cannot tell: protected, and named unreadable if it stays so
        found.append(name)
    return _workflow_filter(list(dict.fromkeys(found)), cwd=cwd, plan_path=plan_path,
                            out_dir=out_dir)


def _copies_dir(guard: Mapping[str, Any], cwd: str) -> Optional[str]:
    where = guard.get("protected_copies")
    if not isinstance(where, str) or not where:
        return None
    return where if os.path.isabs(where) else os.path.join(cwd, where)


def _write_paths_denied(cwd: str, anchor: Optional[str]) -> Optional[Callable[[str], bool]]:
    """Whether ``driver.write_paths.deny`` names a path in git's form, matched
    on the path's own name (a symlink by its name, never its target); ``None``
    when the policy cannot be read. The merged policy both write legs enforce
    (``write_safety.WritePolicy.load``), anchored on *anchor*, else *cwd*."""
    from .write_safety import WritePolicy, glob_to_regex

    try:
        patterns = [glob_to_regex(pattern) for pattern in
                    WritePolicy.load(cwd, anchor=anchor or cwd).deny]
    except Exception as exc:  # noqa: BLE001 - a config that cannot be read copies nothing
        print(f"Warning: driver.write_paths could not be read ({exc}), so no "
              f"protected file is copied", file=sys.stderr)
        return None
    return lambda name: any(pattern.match(name) for pattern in patterns)


def copy_protected(paths: Iterable[str], *, cwd: str, dest: str,
                   anchor: Optional[str] = None) -> None:
    """Copy each protected path's bytes to ``<dest>/<path>`` (files and
    symlinks; an absent path or a directory has nothing to copy). Best-effort:
    a copy that fails is reported and skipped, never fatal.

    A path ``driver.write_paths.deny`` names (``.env``, ``**/*.pem``,
    ``**/.ssh/**``, ``.multi-llm/**``) is never copied, and a copy an earlier
    run left of it is removed, as the executor's rollback store never retains
    one (``write_batch_scheduler._retain``): the deny list exists to keep that
    material out of the run's artifacts, and a copy here would put a
    credential under ``apply-fixes/protected/`` whether or not a batch ever
    touches it. Such a path stays protected and watched, so a batch that
    writes it still fails; its way back is by hand. When the policy cannot be
    read nothing is copied (:func:`_write_paths_denied`, anchored on
    *anchor*, else *cwd*)."""
    paths = list(paths)
    if not paths:
        return
    denied = _write_paths_denied(cwd, anchor)
    for path in paths:
        source = os.path.join(cwd, path)
        target = os.path.join(dest, path)
        if denied is None or denied(path):
            try:
                if os.path.lexists(target) and not os.path.isdir(target):
                    os.unlink(target)
            except OSError:
                pass
            continue
        try:
            info = os.lstat(source)
        except OSError:
            continue
        if not (stat.S_ISREG(info.st_mode) or stat.S_ISLNK(info.st_mode)):
            continue
        try:
            os.makedirs(os.path.dirname(target), exist_ok=True)
            if os.path.lexists(target):
                os.unlink(target)
            shutil.copy2(source, target, follow_symlinks=False)
        except OSError as exc:
            print(f"Warning: could not copy protected file {path} to {dest}: {exc}",
                  file=sys.stderr)


def write_protected_list(phase_dir: str, paths: Sequence[str]) -> str:
    """Write every protected path, one per line, to
    ``<phase_dir>/protected_paths.txt``; returns the file's path."""
    os.makedirs(phase_dir, exist_ok=True)
    target = os.path.join(phase_dir, PROTECTED_LIST_FILE)
    with open(target, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("".join(f"{path}\n" for path in paths))
    return target


# ---------------------------------------------------------------------------
# The shared re-check functions (both legs)
# ---------------------------------------------------------------------------


def recheck_files(guard: Mapping[str, Any], files: Sequence[str], *, cwd: str,
                  file_sha256: Callable[[str], Optional[str]]) -> List[str]:
    """The files that fail their expectation now (§2.7, "Every batch is
    re-checked immediately before it is dispatched"), in git's form.

    - ``{"kind": "batch", "sha256": h}``: fails unless ``file_sha256`` of the
      file (called with its absolute path) equals ``h``;
    - ``{"kind": "head"}``, and a file with no expectation yet: fails when
      ``paths_changed_since(head, …)`` marks it (one call over all of them);
    - a protected path, or one outside the repository, always fails.

    *cwd* is the repository root.
    """
    expect = guard.get("expect") or {}
    protected = guard.get("protected") or {}
    head = str(guard.get("head") or "")
    names = list(dict.fromkeys(_git_name(f, cwd) for f in files if f))
    failing: Set[str] = set()
    head_kind: List[str] = []
    for name in names:
        if not _inside(name) or name in protected:
            failing.add(name)
            continue
        entry = expect.get(name)
        if isinstance(entry, Mapping) and entry.get("kind") == "batch":
            if file_sha256(os.path.join(cwd, name)) != entry.get("sha256"):
                failing.add(name)
        else:
            head_kind.append(name)
    if head_kind:
        changed = paths_changed_since(head, head_kind, cwd=cwd) if head else set(head_kind)
        failing.update(name for name in head_kind if name in changed)
    return [name for name in names if name in failing]


def repin_after_batch(guard: Dict[str, Any], task_id: str,
                      sha256_by_path: Mapping[str, Optional[str]], *,
                      cwd: Optional[str] = None) -> bool:
    """Re-pin every ``expect`` path whose content no longer matches its
    expectation to ``{"kind": "batch", "sha256": …, "task_id": task_id}``;
    True when anything changed.

    *sha256_by_path* is what the completed batch left: the paths it wrote (its
    audit's ``sha256_after``, or the declared files ``util batch-done``
    hashes) and their bytes' sha256 (``None`` for a file the batch deleted).
    Only paths already in ``expect`` are pinned. A ``batch`` entry is re-pinned
    when its ``sha256`` differs. A ``head`` entry is re-pinned when *cwd* is
    given and ``paths_changed_since`` marks the file (the batch changed it);
    with no *cwd* every ``head`` entry named is taken as the batch's write.
    Pass only the batch's own paths: re-pinning a file someone else edited
    meanwhile would accept that edit.
    """
    expect = guard.setdefault("expect", {})
    changed = False
    head_candidates: List[Tuple[str, Optional[str]]] = []
    for path, sha in sha256_by_path.items():
        name = _git_name(path, cwd)
        entry = expect.get(name)
        if not isinstance(entry, Mapping):
            continue
        if entry.get("kind") == "batch":
            if entry.get("sha256") != sha:
                expect[name] = {"kind": "batch", "sha256": sha, "task_id": str(task_id)}
                changed = True
        else:
            head_candidates.append((name, sha))
    if head_candidates:
        if cwd is not None:
            moved = paths_changed_since(str(guard.get("head") or ""),
                                        [name for name, _ in head_candidates], cwd=cwd)
        else:
            moved = {name for name, _ in head_candidates}
        for name, sha in head_candidates:
            if name in moved:
                expect[name] = {"kind": "batch", "sha256": sha, "task_id": str(task_id)}
                changed = True
    return changed


#: How many links :func:`symlink_targets` follows before it gives up (a loop).
_SYMLINK_HOPS_MAX = 40


def symlink_targets(path: str, *, cwd: str) -> List[str]:
    """The in-repository paths, in git's form, that *path*'s symlink chain
    passes through after *path* itself, down to the entry it ends at; ``[]``
    when *path* is not a symlink.

    The context plan is named by the link's own name (``git_utils.git_path``
    resolves the directories, never the last component), so a symlinked
    plan's text lives under another name a fix can target and a batch can
    write. Each hop is named as ``git_path`` names a path (its directories
    resolved, its last component kept); a hop outside the repository is left
    out, and the walk stops at a loop or after :data:`_SYMLINK_HOPS_MAX`
    links. *cwd* is the repository root."""
    current = os.path.join(cwd, path)
    found: List[str] = []
    seen: Set[str] = set()
    for _ in range(_SYMLINK_HOPS_MAX):
        try:
            if not os.path.islink(current):
                break
            target = os.readlink(current)
        except OSError:
            break
        hop = os.path.normpath(os.path.join(os.path.dirname(current), target))
        head, tail = os.path.split(hop)
        try:
            hop = os.path.join(os.path.realpath(head), tail)
        except OSError:
            break
        if hop in seen:
            break
        seen.add(hop)
        name = git_path(hop, repo_root=cwd)
        if _inside(name) and name != path:
            found.append(name)
        current = hop
    return list(dict.fromkeys(found))


def context_plan_paths(guard: Mapping[str, Any]) -> List[str]:
    """Every in-repository name of the context plan's text: the context plan
    itself, then each target of its symlink chain the guard saved
    (``context_plan_targets``). A group naming any of them is skipped as the
    context plan, and the write legs deny and watch each one, so editing a
    symlinked plan's target is caught like editing the plan."""
    names: List[str] = []
    plan = guard.get("context_plan")
    if isinstance(plan, str) and plan and _inside(plan):
        names.append(plan)
    targets = guard.get(CONTEXT_PLAN_TARGETS_KEY)
    if isinstance(targets, Mapping):
        names.extend(str(path) for path in targets
                     if isinstance(path, str) and path and _inside(path))
    return list(dict.fromkeys(names))


def context_plan_watched(guard: Mapping[str, Any]) -> Optional[str]:
    """The context plan when the write legs watch it beside the protected
    set: set, inside the repository, not itself protected, and saved with
    its disk id when the guard was taken (``context_plan_id``)."""
    plan = guard.get("context_plan")
    protected = guard.get("protected")
    if not isinstance(plan, str) or not plan or not _inside(plan):
        return None
    if isinstance(protected, Mapping) and plan in protected:
        return None
    return plan if CONTEXT_PLAN_ID_KEY in guard else None


def watched_ids(guard: Mapping[str, Any]) -> Dict[str, Optional[str]]:
    """``{path: saved disk id}`` of every path no batch may change: the
    protected set, plus the context plan (§2.7, "The user's context plan is
    protected"; its id taken with the guard) and, for a symlinked one, each
    target of its chain (``context_plan_targets``), when not already in it."""
    protected = guard.get("protected")
    watched: Dict[str, Optional[str]] = dict(protected) if isinstance(protected, Mapping) else {}
    plan = context_plan_watched(guard)
    if plan is not None:
        value = guard.get(CONTEXT_PLAN_ID_KEY)
        watched[plan] = str(value) if value is not None else None
    targets = guard.get(CONTEXT_PLAN_TARGETS_KEY)
    if isinstance(targets, Mapping):
        for path, value in targets.items():
            if isinstance(path, str) and path and _inside(path) and path not in watched:
                watched[path] = str(value) if value is not None else None
    return watched


def protected_violations(guard: Mapping[str, Any], *, cwd: str,
                         baseline: Optional[Mapping[str, Optional[str]]] = None) -> List[str]:
    """The watched paths (:func:`watched_ids`: the protected set and the
    context plan) whose disk id moved, sorted.

    Without *baseline* each is compared with the id the guard saved. With
    one (the ids :func:`disk_blob_ids` read just before a batch started: the
    executor's pre-batch read, or the native leg's :func:`bind_watched`), a
    path it holds is compared with that instead, so only a change made
    during the batch's window counts: a protected file the user edited
    between batches is theirs, not the batch's. ``unreadable`` on both sides
    is no change, a move into or out of it is one (:func:`identity_changed`)."""
    watched = watched_ids(guard)
    if not watched:
        return []
    current = disk_blob_ids(list(watched), cwd=cwd)
    hits = []
    for path, saved in watched.items():
        before = baseline[path] if baseline is not None and path in baseline else saved
        if identity_changed(before, current.get(path)):
            hits.append(path)
    return sorted(hits)


def bind_watched(guard: Dict[str, Any], task_id: str, *, cwd: str) -> Dict[str, Optional[str]]:
    """Record, in *guard*, the watched set's disk ids now
    (``guard["bound"][task_id]``) and return them: what ``util write-prompt``
    reads when it binds a native batch's prompt, so that batch's ``util
    batch-done`` compares with the tree as it was when the batch was handed
    out (:func:`bound_baseline`), the executor's per-batch window on the
    native leg. A user's edit to a protected file or to the context plan
    between batches, or between a stop and its ``--resume``, is then never
    the next batch's violation, while a write made during the batch still
    is. A later bind of the same task replaces its record. One
    ``git hash-object`` call over the watched set."""
    ids = disk_blob_ids(list(watched_ids(guard)), cwd=cwd)
    bound = guard.get(BOUND_KEY)
    if not isinstance(bound, dict):
        bound = guard[BOUND_KEY] = {}
    bound[str(task_id)] = dict(ids)
    return ids


def bound_baseline(guard: Mapping[str, Any], task_id: str) -> Optional[Dict[str, Optional[str]]]:
    """The ids :func:`bind_watched` recorded for *task_id*, or ``None`` when
    its prompt was not bound through ``util write-prompt`` since the guard
    was decided or resumed (the caller then compares with the saved ids)."""
    bound = guard.get(BOUND_KEY)
    entry = bound.get(str(task_id)) if isinstance(bound, Mapping) else None
    return dict(entry) if isinstance(entry, Mapping) else None


def drop_bound(guard: Dict[str, Any], task_id: str) -> bool:
    """Forget *task_id*'s bind record (any record of the batch consumes it);
    True when there was one. The key goes when it empties."""
    bound = guard.get(BOUND_KEY)
    if not isinstance(bound, dict) or str(task_id) not in bound:
        return False
    bound.pop(str(task_id))
    if not bound:
        guard.pop(BOUND_KEY, None)
    return True


def copy_holding(guard: Mapping[str, Any], path: str, before: Optional[str], *,
                 cwd: str) -> Optional[str]:
    """The copy :func:`take_guard` (or :func:`mark_stale`) kept of watched
    *path* under ``protected_copies``, when that copy's identity is *before*
    (what the path held before the batch); else ``None``. A copy older than
    a change made since it was taken is never offered as the way back."""
    if before is None or before in (_UNREADABLE, _DIRECTORY) \
            or before.startswith(_SPECIAL_PREFIX):
        return None
    copies = _copies_dir(guard, cwd)
    source = os.path.join(copies, path) if copies else None
    if not source or not os.path.lexists(source):
        return None
    # By absolute path from the repository root: `hash-object
    # --stdin-paths` reads a relative name from the top level whatever the
    # cwd, so a cwd inside the copies dir would hash the repo's file.
    copy_path = os.path.abspath(source)
    if disk_blob_ids([copy_path], cwd=cwd).get(copy_path) != before:
        return None
    return source


#: The states :func:`restore_watched` reports for a path it put back.
RESTORED_FROM_COPY = "restored from the commit review's copy"
DELETED_ABSENT_BEFORE = "deleted (absent before the batch)"


def restore_watched(guard: Mapping[str, Any], paths: Sequence[str], *, cwd: str,
                    baseline: Optional[Mapping[str, Optional[str]]] = None) -> Dict[str, str]:
    """Put each watched path of *paths* back as it was before the batch, for
    the executor's post-run check when the pre-batch snapshot holds no bytes
    for it (the census was unavailable, or the rollback store past its
    budget). ``{path: state}``:

    - absent before the batch (its *baseline* id, else its saved id, is
      ``None``): the file or symlink the batch left there is deleted
      (:data:`DELETED_ABSENT_BEFORE`);
    - otherwise the copy :func:`take_guard` kept under ``protected_copies``,
      only when that copy's id is the id the path had before the batch
      (:data:`RESTORED_FROM_COPY`): a copy older than a change made since the
      guard ran is never written over it;
    - anything else is ``skipped: <why>`` and stays on disk.

    Every write revalidates the path no-follow (``write_safety.restore_path``).
    Paths not watched are left out of the answer."""
    from .write_safety import restore_path

    watched = watched_ids(guard)
    copies = _copies_dir(guard, cwd)
    report: Dict[str, str] = {}
    for path in paths:
        if path not in watched:
            continue
        before = baseline[path] if baseline is not None and path in baseline else watched[path]
        if before is None:
            state = restore_path(cwd, path, None)
            report[path] = DELETED_ABSENT_BEFORE if state.startswith("deleted") else state
            continue
        if before == _UNREADABLE:
            report[path] = "skipped: it could not be read before the batch"
            continue
        if before == _DIRECTORY or before.startswith(_SPECIAL_PREFIX):
            report[path] = "skipped: no copy is kept of a directory or special file"
            continue
        if not copies or not os.path.lexists(os.path.join(copies, path)):
            report[path] = "skipped: the commit review kept no copy of it"
            continue
        source = copy_holding(guard, path, before, cwd=cwd)
        if source is None:
            report[path] = ("skipped: the copy the commit review kept is not what it "
                            "held before the batch")
            continue
        state = restore_path(cwd, path, source)
        report[path] = RESTORED_FROM_COPY if state == "restored" else state
    return report


def mark_stale(guard: Dict[str, Any], groups: Mapping[str, Sequence[str]],
               failing: Sequence[str], *, cwd: str, anchor: Optional[str] = None) -> None:
    """Skip every group naming a failing file (reason ``changed``, its failing
    files named), and add the failing files to the protected set at their
    current disk ids, with byte copies for the native leg (none of a path
    ``driver.write_paths`` denies, :func:`copy_protected`, whose *anchor* it
    is). A group already skipped keeps its reason; a path already protected
    keeps its saved id, so a write to it is still detected. A failing file
    loses its expectation: nothing may write it any more."""
    failing_set = {_git_name(f, cwd) for f in failing if f}
    if not failing_set:
        return
    skipped = guard.setdefault("skipped", {})
    decided = guard.setdefault("groups", {})
    for gid, files in groups.items():
        names = list(dict.fromkeys(_git_name(f, cwd) for f in files if f))
        bad = [name for name in names if name in failing_set]
        if not bad:
            continue
        if gid not in skipped:
            skipped[gid] = {"reason": REASON_CHANGED, "files": bad}
        decided.setdefault(gid, {"files": names, "introduced_by": None})
    protected = guard.setdefault("protected", {})
    new = sorted(name for name in failing_set if name not in protected and _inside(name))
    if new:
        protected.update(disk_blob_ids(new, cwd=cwd))
        dest = _copies_dir(guard, cwd)
        if dest:
            copy_protected(new, cwd=cwd, dest=dest, anchor=anchor)
        _note_unreadable(guard)
    expect = guard.get("expect")
    if isinstance(expect, dict):
        for name in failing_set:
            expect.pop(name, None)


def save_guard(state_path: Any, guard: Mapping[str, Any]) -> None:
    """Write *guard* under the pinned record of ``state.json`` at *state_path*,
    under ``metrics.state_file_lock``, keeping every other key: for an update
    taken outside the apply phase's own ``StateManager`` (a pre-dispatch
    re-check, ``util batch-done``). Raises ``ValueError`` when the file pins
    no endpoints."""
    from .metrics import _read_state, _write_state, state_file_lock

    target = Path(state_path)
    with state_file_lock(target):
        state = _read_state(target)
        record = pinned_record(state) if isinstance(state, dict) else None
        if record is None:
            raise ValueError(f"{target} records neither commit_range nor head_ref")
        record["guard"] = copy.deepcopy(dict(guard))
        _write_state(target, state)


# ---------------------------------------------------------------------------
# The [COMMIT_FIXES] block from the saved guard
# ---------------------------------------------------------------------------


def _attributed(value: Any, commits: Sequence[Mapping[str, Any]]) -> Optional[str]:
    """The ``commits`` entry's SHA *value* (a full SHA or a 7+ hex prefix)
    names, or None."""
    if not isinstance(value, str):
        return None
    text = value.strip().lower()
    if len(text) < 7 or not re.fullmatch(r"[0-9a-f]+", text):
        return None
    matches = [str(c.get("sha")) for c in commits
               if isinstance(c.get("sha"), str) and str(c.get("sha")).startswith(text)]
    return matches[0] if len(matches) == 1 else None


def fix_block(guard: Mapping[str, Any], record: Mapping[str, Any], *, source: str) -> FixBlock:
    """The :class:`FixBlock` the guard's decision shows, in groups.

    The groups the guard decided over (``guard.groups``) minus the skipped
    ones are "to apply", one line per attributed commit in the range's order,
    then ``(unattributed)``. After a direct ``--head-ref`` review nothing is
    attributed, so there are no per-commit lines at all (§2.5, "The apply").
    """
    decided = guard.get("groups") or {}
    skipped = guard.get("skipped") or {}
    head = str(guard.get("head") or record.get("head") or "")
    commits = [c for c in (record.get("commits") or []) if isinstance(c, Mapping)] \
        if source == "commit_range" else []
    counts: Dict[str, int] = {}
    unattributed = to_apply = 0
    for gid, info in decided.items():
        if gid in skipped:
            continue
        to_apply += 1
        sha = _attributed((info or {}).get("introduced_by"), commits) if commits else None
        if sha:
            counts[sha] = counts.get(sha, 0) + 1
        else:
            unattributed += 1
    per_commit = [
        (str(c["sha"]), counts[str(c["sha"])], str(c.get("subject") or ""))
        for c in commits if counts.get(str(c.get("sha")))
    ]
    if source != "commit_range":
        per_commit, unattributed = [], 0
    skipped_changed = skipped_context_plan = 0
    changed_files: List[str] = []
    for gid, entry in skipped.items():
        if gid not in decided or not isinstance(entry, Mapping):
            continue
        if entry.get("reason") == REASON_CONTEXT_PLAN:
            skipped_context_plan += 1
        else:
            skipped_changed += 1
            changed_files.extend(str(f) for f in entry.get("files") or [])
    unreadable = guard.get(UNREADABLE_KEY)
    return FixBlock(
        to_apply=to_apply,
        per_commit=per_commit,
        unattributed=unattributed,
        skipped_changed=skipped_changed,
        changed_files=list(dict.fromkeys(changed_files)),
        head=head,
        skipped_context_plan=skipped_context_plan,
        context_plan=guard.get("context_plan") if skipped_context_plan else None,
        unreadable=[str(path) for path in unreadable] if isinstance(unreadable, list) else [],
    )


def fix_payload(block: FixBlock, *, source: str) -> Dict[str, Any]:
    """The result line's ``commit_fixes``: the block's data plus its lines,
    so a tool route renders exactly what the shell printed."""
    return {
        "source": source,
        "head": block.head,
        "to_apply": block.to_apply,
        "per_commit": [
            {"sha": sha, "groups": groups, "subject": clip(subject, BLOCK_SUBJECT_CHARS)}
            for sha, groups, subject in block.per_commit
        ],
        "unattributed": block.unattributed,
        "skipped_changed": block.skipped_changed,
        "changed_files": list(block.changed_files),
        "skipped_context_plan": block.skipped_context_plan,
        "context_plan": block.context_plan,
        "unreadable": list(block.unreadable),
        "lines": render_fix_block(block),
    }


def fixes_from_state(state: Optional[Mapping[str, Any]]) -> Optional[Tuple[List[str], Dict[str, Any]]]:
    """``([COMMIT_FIXES] lines, commit_fixes payload)`` from the saved guard,
    or None when the state holds no guard. ``status`` renders a detached
    apply's block from this (§2.3)."""
    endpoints = pinned_endpoints(state)
    record = pinned_record(state)
    guard = guard_record(state)
    if endpoints is None or record is None or guard is None:
        return None
    block = fix_block(guard, record, source=endpoints.source)
    payload = fix_payload(block, source=endpoints.source)
    return list(payload["lines"]), payload


# ---------------------------------------------------------------------------
# The decision
# ---------------------------------------------------------------------------


@dataclass
class GuardOutcome:
    """What :func:`take_guard` decided for this run's groups.

    ``guard`` is the record to save under the pinned record; ``skipped`` maps
    each skipped group id of this run to ``{"reason", "files"}``; ``lines``
    and ``payload`` are the ``[COMMIT_FIXES]`` block and ``commit_fixes``;
    ``reused`` says a saved decision was resumed; ``stale`` names the groups
    that resumed decision let through before and the re-check now skips.
    """

    guard: Dict[str, Any]
    skipped: Dict[str, Dict[str, Any]]
    lines: List[str]
    payload: Dict[str, Any]
    reused: bool = False
    stale: List[str] = field(default_factory=list)


def _refresh_context_plan(guard: Dict[str, Any], *, cwd: str, persist: bool,
                          anchor: Optional[str] = None) -> None:
    """On a resumed decision: the context plan's saved id as it is now, with
    its copy retaken when it moved (*persist*).

    The context plan is the user's own document, and editing it between a
    stop and its ``--resume`` is theirs to do (the review read its snapshot,
    so nothing in this review changes). Kept at the id the stopped run saved,
    the edit would read as every later batch's write on the native leg, and
    the way back would name a copy that undoes it. Its id is refreshed under
    whichever key holds it (the protected set, ``context_plan_id``, or
    ``context_plan_targets`` for a symlinked plan's target, the file the
    user's edit lands in); a write made while a batch runs is still caught
    against it."""
    plan = guard.get("context_plan")
    protected = guard.get("protected")
    targets = guard.get(CONTEXT_PLAN_TARGETS_KEY)
    # The user may also have retargeted the link, or replaced a regular plan
    # with one. Discover its current chain before deciding the resumed groups.
    # Keep earlier targets protected for the lifetime of this guard.
    current_targets = symlink_targets(plan, cwd=cwd) if isinstance(plan, str) and plan else []
    if current_targets:
        if not isinstance(targets, dict):
            targets = guard[CONTEXT_PLAN_TARGETS_KEY] = {}
        added = [path for path in current_targets if path not in targets]
        targets.update(disk_blob_ids(added, cwd=cwd))
        dest = _copies_dir(guard, cwd) if persist else None
        if dest and added:
            copy_protected(added, cwd=cwd, dest=dest, anchor=anchor)
    for path in context_plan_paths(guard):
        if isinstance(protected, dict) and path in protected:
            holder: Dict[str, Any] = protected
            key = path
        elif path == plan and CONTEXT_PLAN_ID_KEY in guard:
            holder, key = guard, CONTEXT_PLAN_ID_KEY
        elif path != plan and isinstance(targets, dict) and path in targets:
            holder, key = targets, path
        else:
            continue
        now = disk_blob_ids([path], cwd=cwd).get(path)
        if holder.get(key) == now:
            continue
        holder[key] = now
        dest = _copies_dir(guard, cwd) if persist else None
        if dest:
            stale = os.path.join(dest, path)
            try:
                if os.path.lexists(stale) and not os.path.isdir(stale):
                    os.unlink(stale)
            except OSError:
                pass
            copy_protected([path], cwd=cwd, dest=dest, anchor=anchor)


def take_guard(state: Mapping[str, Any], groups: Sequence[Mapping[str, Any]], *,
               cwd: str, plan_path: Optional[str], out_dir: Optional[str],
               phase_dir: str, resume: bool = False, persist: bool = True,
               file_sha256: Optional[Callable[[str], Optional[str]]] = None,
               completed: Iterable[str] = (),
               ) -> Optional[GuardOutcome]:
    """The §2.7 guard over *groups* (this run's candidates: valid and
    awaiting a decision), or None when *state* pins no endpoints.

    A fresh decision takes the protected set (copied under
    ``<phase_dir>/protected/`` when *persist*, bar the paths
    ``driver.write_paths`` denies, anchored on *plan_path* as the write legs'
    policy is: :func:`copy_protected`), then skips, per group and in
    this order: a group naming the context plan (``commit_range.plan``, or a
    symlinked plan's in-repository target, :func:`symlink_targets`, saved
    under ``context_plan_targets`` and watched like the plan; a group both
    rules would skip is counted once, under it), a group with a
    fix file ``paths_changed_since(head, …)`` marks or outside the
    repository, a group naming a protected path. Every file of every group
    let through gets a ``head`` expectation (``blobs_in_commit``). A watched
    path that cannot be read is decided about here: it is named in the block
    (``guard["unreadable"]``), every group naming it is skipped (it is
    protected), and the write legs compare it only for a move into or out of
    readability (:func:`identity_changed`).

    On *resume*, a saved guard for the same ``head`` is reused: its skips,
    protected set and expectations stand, and :func:`recheck_files` runs over
    every group left; a group failing it is skipped and its failing files
    protected (:func:`mark_stale`). ``guard.groups`` then describes this
    run's groups, so the block counts the groups left. The stopped run's
    per-batch bind records are dropped, and the context plan's saved id and
    copy are refreshed (:func:`_refresh_context_plan`).

    *completed* names the groups whose batch an earlier run of this apply
    already finished (its ``processed_<phase>`` records; on the executor leg
    those groups are still in the work set, because the scheduler keeps their
    batch from its result file). On a resume such a group is never skipped:
    taking it out would re-make its batch without it, and the scheduler would
    then dispatch the rest of that batch a second time (§2.8: "Its own resume
    skips every recorded batch"). Its failing files are still protected, so
    no later batch writes them, and they get no new expectation.

    Nothing here writes ``state.json``: the caller stores ``guard`` through
    its own ``StateManager``. *cwd* is the repository root.
    """
    endpoints = pinned_endpoints(state)
    record = pinned_record(state)
    if endpoints is None or record is None:
        return None
    if file_sha256 is None:
        from .write_safety import file_sha256 as _sha

        file_sha256 = _sha
    head = endpoints.head
    context_plan: Optional[str] = None
    if endpoints.source == "commit_range" and isinstance(record.get("plan"), str) \
            and record.get("plan"):
        context_plan = _git_name(record["plan"], cwd)

    by_id: Dict[str, List[str]] = {}
    attribution: Dict[str, Any] = {}
    for group in groups:
        gid = _group_id(group)
        by_id[gid] = group_files(group, repo_root=cwd)
        attribution[gid] = group.get("introduced_by")

    saved = record.get("guard")
    reused = bool(resume and isinstance(saved, Mapping) and saved.get("head") == head)
    if reused:
        guard: Dict[str, Any] = copy.deepcopy(dict(saved))
        for key in ("skipped", "expect", "protected"):
            if not isinstance(guard.get(key), dict):
                guard[key] = {}
        # The resumed run binds every batch afresh: a record left by a batch
        # of the stopped run never stands for a batch of this one.
        guard.pop(BOUND_KEY, None)
        _refresh_context_plan(guard, cwd=cwd, persist=persist, anchor=plan_path)
        _note_unreadable(guard)
    else:
        copies = os.path.join(phase_dir, PROTECTED_COPIES_DIR)
        copies_rel = git_path(copies, repo_root=cwd)
        guard = {
            "head": head,
            "decided_at": _now_utc(),
            "skipped": {},
            "expect": {},
            "protected": {},
            "protected_copies": copies_rel if _inside(copies_rel) else copies,
            "context_plan": context_plan,
        }
    guard["groups"] = {
        gid: {"files": files, "introduced_by": attribution.get(gid)}
        for gid, files in by_id.items()
    }

    unanswered = False
    if not reused:
        # A symlinked context plan keeps the link's own name, but its text
        # lives in the target: each in-repository hop of the chain is the
        # context plan too, skipped below and watched and denied by both
        # write legs (`context_plan_paths`), saved with its disk id.
        targets = symlink_targets(context_plan, cwd=cwd) if context_plan else []
        if targets:
            guard[CONTEXT_PLAN_TARGETS_KEY] = disk_blob_ids(targets, cwd=cwd)
        listed = protected_paths(head, cwd=cwd, plan_path=plan_path, out_dir=out_dir)
        if listed is None:
            unanswered = True
        else:
            guard["protected"] = disk_blob_ids(listed, cwd=cwd)
            # The context plan is read-only whether or not it differs from
            # `head` (§2.7): when it is not protected already, its disk id is
            # saved too, so both write legs catch a batch that writes it
            # (`watched_ids`), and its bytes are copied beside the others.
            watched_plan: List[str] = []
            if context_plan and _inside(context_plan) and context_plan not in guard["protected"]:
                guard[CONTEXT_PLAN_ID_KEY] = disk_blob_ids([context_plan], cwd=cwd).get(context_plan)
                watched_plan = [context_plan]
            watched_plan.extend(path for path in targets if path not in guard["protected"])
            if persist:
                copies = _copies_dir(guard, cwd)
                if copies:
                    shutil.rmtree(copies, ignore_errors=True)
                    copy_protected(list(listed) + watched_plan, cwd=cwd, dest=copies,
                                   anchor=plan_path)
            # A watched path that cannot be read is decided about here, once:
            # named in the block, and every group naming it skipped below (it
            # is protected), rather than failing every batch later.
            _note_unreadable(guard)

    skipped: Dict[str, Any] = guard["skipped"]
    pending = {gid: files for gid, files in by_id.items() if gid not in skipped}
    if context_plan:
        # The plan by its own name or, for a symlinked one, by a target's.
        plan_names = list(dict.fromkeys([context_plan] + context_plan_paths(guard)))
        for gid, files in list(pending.items()):
            hit = [name for name in plan_names if name in files]
            if hit:
                skipped[gid] = {"reason": REASON_CONTEXT_PLAN, "files": hit}
                pending.pop(gid)

    stale: List[str] = []
    all_files = list(dict.fromkeys(name for files in pending.values() for name in files))
    if unanswered:
        # A question git did not answer never lets a fix through.
        for gid, files in pending.items():
            skipped[gid] = {"reason": REASON_CHANGED, "files": list(files)}
        pending = {}
    elif reused:
        before = set(skipped)
        failing = recheck_files(guard, all_files, cwd=cwd, file_sha256=file_sha256)
        landed = {str(gid) for gid in completed}
        mark_stale(guard, {gid: files for gid, files in pending.items() if gid not in landed},
                   failing, cwd=cwd, anchor=plan_path)
        stale = [gid for gid in pending if gid in skipped and gid not in before]
        pending = {gid: files for gid, files in pending.items() if gid not in skipped}
    else:
        inside = [name for name in all_files if _inside(name)]
        changed = paths_changed_since(head, inside, cwd=cwd) if inside else set()
        protected = guard["protected"]
        for gid, files in list(pending.items()):
            bad = [name for name in files if name in changed or not _inside(name)]
            if bad:
                skipped[gid] = {"reason": REASON_CHANGED, "files": bad}
                pending.pop(gid)
                continue
            held = [name for name in files if name in protected]
            if held:
                skipped[gid] = {"reason": REASON_PROTECTED, "files": held}
                pending.pop(gid)

    expect: Dict[str, Any] = guard["expect"]
    protected_now = guard.get("protected") or {}
    missing = list(dict.fromkeys(
        name for files in pending.values() for name in files
        if name not in expect and name not in protected_now
    ))
    if missing:
        blobs = blobs_in_commit(head, missing, cwd=cwd) or {}
        for name in missing:
            expect[name] = {"kind": "head", "blob": blobs.get(name)}

    block = fix_block(guard, record, source=endpoints.source)
    payload = fix_payload(block, source=endpoints.source)
    return GuardOutcome(
        guard=guard,
        skipped={gid: dict(skipped[gid]) for gid in by_id if gid in skipped},
        lines=list(payload["lines"]),
        payload=payload,
        reused=reused,
        stale=stale,
    )


# ---------------------------------------------------------------------------
# Fix-prompt context on a pinned run
# ---------------------------------------------------------------------------


def deleted_file_history(base: Optional[str], head: str, files: Sequence[str], *,
                         cwd: str) -> Dict[str, Optional[str]]:
    """``{path: deleting commit | None}`` for each of *files* absent at *head*.

    The fix prompt of a file the guard let through while absent at ``head``
    (so absent on disk too) names ``git show <deleting>^:<path>``, the content
    the range removed, or says no range commit deleted it (§2.7, "Historical
    context for a deleted file"). Files present at ``head`` are left out.
    """
    names = [name for name in dict.fromkeys(files) if _inside(name)]
    if not names:
        return {}
    present = paths_in_commit(head, names, cwd=cwd)
    if present is None:
        return {}
    return {
        name: deleting_commit(base, head, name, cwd=cwd)
        for name in names if name not in present
    }


def history_lines(base: Optional[str], head: str,
                  history: Mapping[str, Optional[str]]) -> List[str]:
    """The prompt's lines for :func:`deleted_file_history`, one per file."""
    h = head[:12]
    lines = []
    for path, deleting in history.items():
        if deleting:
            d = deleting[:12]
            lines.append(
                f"`{path}` is absent at the reviewed commit {h} and on disk: the range "
                f"deleted it in {d}. The content it removed: `git show {d}^:{path}`."
            )
        else:
            lines.append(
                f"`{path}` is absent at the reviewed commit {h} and on disk, and no "
                f"commit in the range deleted it, so the range holds no earlier "
                f"content for it."
            )
    return lines


ROOT_RANGE_LINE = (
    "The reviewed range starts at the repository's first commit, so `git diff "
    "{base_ref} -- <file>` shows the whole file as new."
)


# ---------------------------------------------------------------------------
# Which review a no-argument --apply-commit-fixes applies (§2.7)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Selection:
    """The review :func:`select_review` picked: its ``brief`` (absolute), the
    ``[COMMIT_REVIEW_SELECTED]`` ``line`` for the commit block, and the
    result line's ``selected`` ``payload`` (``{completed_at, behind}``)."""

    brief: Path
    line: str
    payload: Dict[str, Any]
    pinned: str = ""
    record: Optional[Dict[str, Any]] = None


@dataclass
class _Review:
    slug: str
    brief: Path
    folder: Path
    record: Dict[str, Any]
    completed_at: Optional[str]
    resolved_at: str

    @property
    def base(self) -> Optional[str]:
        base = self.record.get("base")
        return str(base) if base is not None else None

    @property
    def head(self) -> str:
        return str(self.record.get("head") or "")


def _when(text: Any) -> datetime:
    """An ISO-8601 time as an aware datetime (a naive one is local time);
    the earliest instant for anything unreadable."""
    if isinstance(text, str) and text:
        try:
            value = datetime.fromisoformat(text.replace("Z", "+00:00"))
            return value if value.tzinfo else value.astimezone()
        except ValueError:
            pass
    return datetime.min.replace(tzinfo=timezone.utc)


def _shown_time(text: Optional[str]) -> str:
    """``YYYY-MM-DD HH:MM`` in local time, as the listing prints it."""
    if not text:
        return "?"
    value = _when(text)
    if value.year == 1:
        return plain_line(text)[:16]
    return value.astimezone().strftime("%Y-%m-%d %H:%M")


#: What a completed round leaves that apply-code-fixes cannot run without
#: (``ApplyCodeFixesOrchestrator.load_data``). A restart's archive moves it
#: to ``restarted-<stamp>/``. ``validation.json`` is read when present but not
#: required: a ``--skip-validation`` round completes without one, and apply
#: then treats every finding as needing a decision.
ROUND_RESULTS_FILE = "grouped.json"


def _round_on_disk(out_dir: Path) -> bool:
    """Whether the brief output dir *out_dir* holds its current round's
    results (``code-review/grouped.json``)."""
    return (out_dir / "code-review" / ROUND_RESULTS_FILE).is_file()


def _scan(folder: Path) -> Tuple[List[_Review], List[_Review], List[Path]]:
    """One level of *folder*: (completed reviews, unfinished ones, unreadable
    state files). A slug folder counts only when its brief ``<slug>.md`` is a
    file and it holds a ``state.json``; each is one small JSON read, with no
    lock and no write (§2.7, "How each file is read")."""
    completed: List[_Review] = []
    unfinished: List[_Review] = []
    unreadable: List[Path] = []
    try:
        entries = sorted(os.scandir(folder), key=lambda e: e.name)
    except OSError:
        return completed, unfinished, unreadable
    for entry in entries:
        if not _SLUG_RE.fullmatch(entry.name):
            continue
        try:
            if not entry.is_dir(follow_symlinks=False):
                continue
        except OSError:
            continue
        brief = folder / f"{entry.name}.md"
        state_path = Path(entry.path) / "state.json"
        if not brief.is_file() or not state_path.is_file():
            continue
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, UnicodeDecodeError):
            unreadable.append(state_path)
            continue
        if not isinstance(state, dict):
            unreadable.append(state_path)
            continue
        record = state.get("commit_range")
        if not isinstance(record, dict):
            continue
        phases = state.get("phases_completed")
        done = phases.get("code-review") if isinstance(phases, dict) else None
        if done and not _round_on_disk(Path(entry.path)):
            # A restart archived the round and its phase never ran again to
            # pop the key: no results to apply, so not a candidate.
            done = None
        review = _Review(
            slug=entry.name, brief=brief, folder=Path(entry.path), record=record,
            completed_at=str(done) if done else None,
            resolved_at=str(record.get("resolved_at") or ""),
        )
        (completed if done else unfinished).append(review)
    completed.sort(key=lambda r: (_when(r.completed_at), _when(r.resolved_at), r.slug),
                   reverse=True)
    unfinished.sort(key=lambda r: (_when(r.resolved_at), r.slug), reverse=True)
    return completed, unfinished, unreadable


def _head_sha(cwd: str) -> str:
    """``HEAD``'s full SHA; on an unborn ``HEAD`` §2.2's exit 2."""
    stdout, _, rc = _run_git("rev-parse", "--verify", "--quiet", "HEAD^{commit}",
                             check=False, cwd=cwd)
    sha = stdout.strip()
    if rc == 0 and _FULL_SHA.fullmatch(sha):
        return sha
    stdout, _, rc = _run_git("symbolic-ref", "-q", "HEAD", check=False, cwd=cwd)
    branch = stdout.strip()
    if rc == 0 and branch:
        short = branch[len("refs/heads/"):] if branch.startswith("refs/heads/") else branch
        raise RangeError(NOTHING_TO_REVIEW,
                         f"{NOTHING_TO_REVIEW} no commits yet on {plain_line(short)}", 2)
    return resolve_commit_strict("HEAD", cwd=cwd)


def _ancestry(head: str, current: str, cwd: str) -> Optional[int]:
    """How many commits *head* is behind *current* (0 when equal), or None
    when it is not in *current*'s history, or -1 when it no longer resolves.
    At most one ``merge-base --is-ancestor`` and one ``rev-list --count``."""
    if head == current:
        return 0
    if not _FULL_SHA.fullmatch(head):
        return -1
    _, _, rc = _run_git("merge-base", "--is-ancestor", head, current, check=False, cwd=cwd)
    if rc == 1:
        return None
    if rc != 0:
        return -1
    stdout, _, rc = _run_git("rev-list", "--count", f"{head}..{current}", check=False, cwd=cwd)
    text = stdout.strip()
    return int(text) if rc == 0 and text.isdigit() else 0


def _rel(path: Path, root: Path) -> str:
    rel = git_path(str(path), repo_root=str(root))
    return rel if _inside(rel) else str(path)


def _pinned_of(review: _Review, root: Path) -> str:
    """A review's pinned spelling: ``<base12>..<head12>``, or its brief path
    on a root range (§2.2)."""
    return pinned_spelling(review.base, review.head) or _rel(review.brief, root)


def _behind_text(behind: int) -> str:
    return f"{_plural(behind, 'commit')} behind HEAD"


def _valid_findings(review: _Review) -> Optional[int]:
    path = review.folder / "code-review" / "validation.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeDecodeError):
        return None
    entries = data if isinstance(data, list) else (
        data.get("groups") if isinstance(data, dict) else None)
    if not isinstance(entries, list):
        return None
    return sum(1 for e in entries if isinstance(e, Mapping) and e.get("status") == "valid")


def _not_found(folder_rel: str, head: str, candidates: List[_Review],
               unfinished: List[_Review], unreadable: List[Path], *, root: Path,
               cwd: str) -> CommitReviewError:
    if candidates:
        lines = [f"{NOT_FOUND_MARKER} no completed commit review in {folder_rel} ends at "
                 f"HEAD {head[:7]}, and the newest is not in its history"]
    else:
        lines = [f"{NOT_FOUND_MARKER} no completed commit review in {folder_rel}"]
    rows: List[Tuple[str, str, str, str, str]] = []
    for review in candidates[:NOT_FOUND_ROWS]:
        behind = _ancestry(review.head, head, cwd)
        if behind is None:
            relation = "not in HEAD's history"
        elif behind < 0:
            relation = "head no longer resolves"
        elif behind == 0:
            relation = "ends at HEAD"
        else:
            relation = _behind_text(behind)
        command = ("--review-commits <range>" if behind is not None and behind < 0
                   else f"--apply-commit-fixes {_pinned_of(review, root)}")
        valid = _valid_findings(review)
        rows.append((display_range(review.base, review.head),
                     _shown_time(review.completed_at),
                     f"{valid} valid" if valid is not None else "? valid",
                     relation, command))
    if rows:
        widths = [max(len(row[i]) for row in rows) for i in range(4)]
        for row in rows:
            lines.append("  " + "  ".join(row[i].ljust(widths[i]) for i in range(4))
                         + "  " + row[4])
    if unfinished:
        newest = unfinished[0]
        lines.append(
            f"  {_plural(len(unfinished), 'unfinished commit review')} not listed; newest: "
            f"{display_range(newest.base, newest.head)} (status {_rel(newest.brief, root)})"
        )
    if unreadable:
        shown = _rel(unreadable[0], root)
        more = f" and {len(unreadable) - 1} more" if len(unreadable) > 1 else ""
        lines.append(
            f"  {_plural(len(unreadable), 'unreadable state.json')} skipped: {shown}{more}"
        )
    lines.append("  next: --review-commits or --improve-commits to review HEAD")
    return CommitReviewError("\n".join(lines))


def select_review(*, cwd: str) -> Selection:
    """§2.7's no-argument lookup: the review a bare ``--apply-commit-fixes``
    applies.

    Scans only the folder ``get_commit_reviews_dir`` names now, one level
    deep; a candidate is a review whose code-review phase completed and whose
    round's results are on disk (``code-review/grouped.json``: a restart's
    archive moves them out), newest first by that completion, then
    ``commit_range.resolved_at``, then slug.
    The pick: the newest candidate when its ``head`` is ``HEAD`` or an
    ancestor of it; otherwise the newest whose ``head`` is ``HEAD``;
    otherwise :class:`CommitReviewError` ``[COMMIT_REVIEW_NOT_FOUND]`` (exit 3)
    with the five newest candidates. An unborn ``HEAD`` is ``RangeError``
    ``[NOTHING_TO_REVIEW]`` (exit 2), before any lookup. Git runs a handful of
    times whatever the folder holds: one ``rev-parse HEAD``, the ancestry of
    the newest candidate and of at most three others for ``; also:``, or of
    the five listed rows on exit 3.
    """
    from .provider_registry import ConfigError, get_commit_reviews_dir

    root = repo_root_of(cwd)
    head = _head_sha(str(root))
    try:
        folder = get_commit_reviews_dir(anchor=str(root))
    except ConfigError as exc:
        raise CommitReviewError(f"{NOT_FOUND_MARKER} {' '.join(str(exc).split())}") from exc
    folder_rel = commit_reviews_folder_rel(root) or str(folder)
    candidates, unfinished, unreadable = _scan(folder)
    if not candidates:
        raise _not_found(folder_rel, head, candidates, unfinished, unreadable,
                         root=root, cwd=str(root))

    newest = candidates[0]
    pick: Optional[_Review] = None
    behind = 0
    relation = _ancestry(newest.head, head, str(root))
    if relation is not None and relation >= 0:
        pick, behind = newest, relation
    else:
        pick = next((c for c in candidates if c.head == head), None)
    if pick is None:
        raise _not_found(folder_rel, head, candidates, unfinished, unreadable,
                         root=root, cwd=str(root))

    also: List[_Review] = []
    checks = 0
    for other in candidates:
        if other is pick or len(also) >= SELECTED_ALSO_MAX:
            continue
        if other.head == head:
            also.append(other)
            continue
        if checks >= SELECTED_ALSO_MAX:
            continue
        checks += 1
        found = _ancestry(other.head, head, str(root))
        if found is not None and found >= 0:
            also.append(other)

    pinned = _pinned_of(pick, root)
    if behind == 0:
        where = "ends at HEAD"
    else:
        where = (f"{_behind_text(behind)}; the guard skips fix files "
                 f"{'it' if behind == 1 else 'they'} changed")
    line = f"{SELECTED_MARKER} {pinned} completed {_shown_time(pick.completed_at)}, {where}"
    if also:
        line += "; also: " + ", ".join(_pinned_of(review, root) for review in also)
    return Selection(
        brief=pick.brief,
        line=line,
        payload={"completed_at": pick.completed_at, "behind": behind},
        pinned=pinned,
        record=copy.deepcopy(pick.record),
    )


def require_completed_review(brief: Path, *, pinned: str, cwd: str) -> None:
    """Refuse a range whose review has not completed (§2.7, "Which review"):
    no brief, or a brief whose code-review phase is not in
    ``phases_completed`` (never run, still running, stopped, or reset by a
    restart), or whose round's ``code-review/grouped.json`` is not on disk
    (a restart that never completed archives it, among other causes, so the
    message says what is missing and offers that as one explanation).
    Raises :class:`CommitReviewError` ``[COMMIT_REVIEW_NOT_FOUND]
    <pinned>`` (exit 3) naming ``--review-commits`` and ``--improve-commits``,
    plus ``status <brief>`` when the brief exists. Reads one JSON file."""
    brief = Path(brief)
    out_dir = output_dir_for_brief(brief)
    state_path = out_dir / "state.json"
    exists = brief.is_file()
    archived = False
    if exists and state_path.is_file():
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, UnicodeDecodeError):
            state = None
        phases = state.get("phases_completed") if isinstance(state, dict) else None
        if isinstance(phases, dict) and phases.get("code-review"):
            if _round_on_disk(out_dir):
                return
            archived = True
    try:
        root: Optional[Path] = repo_root_of(cwd)
    except CommitReviewError:
        root = None
    shown = _rel(brief, root) if root else str(brief)
    if archived:
        why = (f"its state records the code review as completed, but its results "
               f"(code-review/{ROUND_RESULTS_FILE}) are not on disk (a restart that "
               f"has not completed since moves them out, for one)")
    elif exists:
        why = "its code review has not completed (never run, still running, or stopped)"
    else:
        why = f"no commit brief at {shown}"
    lines = [
        f"{NOT_FOUND_MARKER} {pinned}: no completed review of this range; {why}",
        f"  review it first: --review-commits {pinned}, then --apply-commit-fixes {pinned}; "
        f"or both in one run: --improve-commits {pinned}",
    ]
    if exists:
        lines.append(f"  its progress: status {shown}")
    raise CommitReviewError("\n".join(lines))
