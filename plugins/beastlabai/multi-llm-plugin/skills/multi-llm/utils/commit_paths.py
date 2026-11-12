"""Commit reviews' path layer: the commit brief that stands in for a plan, and its folder.

``--review-commits``, ``--apply-commit-fixes`` and ``--improve-commits`` do not
fork the review pipeline. Each is a front door that resolves a commit range
(``utils/commit_range.py``), writes a generated **commit brief** for it, and
runs review-code or apply-code-fixes on that brief as if it were a plan
(plans/review-commits.md §2.1). Everything a plan anchors (the output dir,
``state.json``, locks, ``status``, run records, the next-step lookup) then
works unchanged. This module owns what the brief is and where it lives; the
range grammar stays in ``commit_range``, which never imports this module, so
the dependency runs one way. The front doors themselves are
``utils/commit_front_door.py``.

**The path layer**:

- The folder is ``code_review.commit_reviews_dir``, read only through
  ``provider_registry.get_commit_reviews_dir`` and joined to the repository
  root. A folder the plugin creates ignores itself with a ``.gitignore``
  holding ``*``; an existing one is left as the user made it, and
  :func:`not_ignored_warning` says when git would show its briefs (§2.4,
  "The folder ignores itself").
- A brief is ``<folder>/<slug>.md`` with the slug ``<base12>-<head12>`` or
  ``root-<head12>``; its output dir is ``<folder>/<slug>/``, as for any plan.
  :func:`is_commit_brief` and :func:`brief_for_pinned` are how the dispatcher
  and ``status`` recognise a brief path or a pinned range without a git call
  beyond finding the root (§2.2).
- :func:`commit_review_artifact` names every brief and report folder by path
  string, so the review scope and ``tracked_files`` drop them as a class,
  whatever run is reviewing (§2.4, "Out of scope for every review").
- :func:`document_label` is the one test for whether a user-facing line calls
  the anchor a "commit brief" or a "plan" (§2.8), and
  :func:`read_commit_range` the read-only lookup of a brief's recorded range.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Tuple, Union

from .cli_common import EXIT_ERROR as _EXIT_ERROR
from .git_utils import get_project_root_from_dir, git_path, ignored_paths
from .output_handler import output_dir_path
from .provider_registry import ConfigError, get_commit_reviews_dir

PathLike = Union[str, os.PathLike]

#: The brief's first line, exactly; the brief writer always puts it there. A
#: file that only quotes it further down (a plan about commit reviews) is not
#: a brief.
BRIEF_MARKER = "<!-- multi-llm:commit-brief v1 -->"

#: The line that closes the generated header. Everything below it (a host's
#: ``## Code Fixes Applied`` section) is kept when the header is rewritten.
BRIEF_END_MARKER = "<!-- /multi-llm:commit-brief -->"

#: §2.4's slug grammar: ``<base12>-<head12>``, or ``root-<head12>`` for a range
#: starting at the root commit. The same text as ``commit_range.SLUG_PATTERN``;
#: kept here as well so this module never imports the range grammar.
SLUG_PATTERN = r"(?:root|[0-9a-f]{12})-[0-9a-f]{12}"

#: §2.2's pinned spelling, ``<base12>..<head12>``, as records, resume lines and
#: next commands print it. The same text as ``commit_range.PINNED_PATTERN``.
PINNED_PATTERN = r"[0-9a-f]{12}\.\.[0-9a-f]{12}"

_SLUG_RE = re.compile(SLUG_PATTERN)
_PINNED_RE = re.compile(PINNED_PATTERN)
_BRIEF_NAME_RE = re.compile(SLUG_PATTERN + r"\.md")

#: The ``.gitignore`` a newly created commit-reviews folder gets.
FOLDER_GITIGNORE = "*\n"

#: How much of a file's first line :func:`is_commit_brief` reads. The marker
#: is 35 bytes; a longer first line is not the marker whatever follows.
_FIRST_LINE_BYTES = 256


class CommitReviewError(Exception):
    """A commit-review refusal: the message to print and the exit code.

    ``exit_code`` is :data:`utils.cli_common.EXIT_NEEDS_HUMAN` (3) unless the
    caller says otherwise; the message's first line starts with its marker
    tag when it has one.
    """

    def __init__(self, message: str, exit_code: int = 3):
        super().__init__(message)
        self.message = message
        self.exit_code = exit_code


def _start_dir(path_or_cwd: Optional[PathLike]) -> str:
    """The existing directory to ask git from: *path_or_cwd* or the cwd.

    A file, or a path that does not exist yet (a brief about to be written),
    is asked from its nearest existing ancestor.
    """
    current = os.path.abspath(os.fspath(path_or_cwd)) if path_or_cwd else os.getcwd()
    while not os.path.isdir(current):
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    return current


def repo_root_of(path_or_cwd: Optional[PathLike] = None) -> Path:
    """The git root of *path_or_cwd* (a file, a directory, or the cwd when None).

    Raises :class:`CommitReviewError` outside a repository: a commit review
    always belongs to one.
    """
    start = _start_dir(path_or_cwd)
    root = get_project_root_from_dir(start)
    if not root:
        raise CommitReviewError(
            f"ERROR: {start} is not in a git repository; commit reviews review "
            f"a repository's commits"
        )
    return Path(root)


def _slug(base: Optional[str], head: str) -> str:
    """``<base12>-<head12>``, or ``root-<head12>`` when *base* is None."""
    head12 = str(head or "")[:12].lower()
    base12 = "root" if base is None else str(base)[:12].lower()
    slug = f"{base12}-{head12}"
    if not _SLUG_RE.fullmatch(slug):
        raise ValueError(
            f"not a commit range's endpoints: base={base!r}, head={head!r} "
            f"(expected full or 12-character hex SHAs, base None for a root range)"
        )
    return slug


def ensure_commit_reviews_dir(anchor: PathLike) -> Tuple[Path, bool]:
    """Create the configured commit-reviews folder if needed; ``(folder, created)``.

    *anchor* is the cwd's repository root, or a brief path. Only the
    configured folder gets a ``.gitignore``, never a parent created with it
    (a tracked or absent ``plans/``): a folder this call creates gets
    ``<folder>/.gitignore`` holding ``*`` with an exclusive create, as
    ``.multi-llm/tmp/`` and the review's ``diff/`` folder do, so plain
    ``git status --porcelain`` (and so ``pre_existing_changes``) never lists
    the briefs and report folders, and ``finalize_tracking``'s ignore filter
    leaves them out of ``tracked_files``.

    An existing folder is left exactly as it is: no ``.gitignore`` is written
    into a folder the plugin did not create, and one the user deleted is
    never restored, since deleting it is how a user chooses to commit reviews.
    Of two concurrent creators, the one whose ``mkdir`` succeeds writes it.

    Raises :class:`~utils.provider_registry.ConfigError` for a refused folder
    (outside the repository) and :class:`CommitReviewError` when the path is
    taken by something that is not a directory.
    """
    folder = get_commit_reviews_dir(anchor=anchor)
    if folder.is_dir():
        return folder, False
    if folder.exists() or folder.is_symlink():
        raise CommitReviewError(
            f"ERROR: code_review.commit_reviews_dir names {folder}, which exists "
            f"and is not a directory; move it or set the key to another folder"
        )
    folder.parent.mkdir(parents=True, exist_ok=True)
    try:
        folder.mkdir()
    except FileExistsError:
        if folder.is_dir():
            return folder, False
        raise
    try:
        with open(folder / ".gitignore", "x", encoding="utf-8", newline="\n") as handle:
            handle.write(FOLDER_GITIGNORE)
    except FileExistsError:
        pass
    return folder, True


def brief_path_for(base: Optional[str], head: str, *, anchor: PathLike) -> Path:
    """``<commit_reviews_dir>/<slug>.md`` for a range, whether it exists or not.

    *base* is None for a range starting at the root commit. Raises
    :class:`ValueError` for endpoints that are not hex SHAs, and the
    accessor's :class:`~utils.provider_registry.ConfigError`.
    """
    slug = _slug(base, head)
    return get_commit_reviews_dir(anchor=anchor) / f"{slug}.md"


def output_dir_for_brief(brief: PathLike) -> Path:
    """The brief's output dir, ``<folder>/<slug>/``: any plan's rule, computed only.

    Equal to ``output_handler.output_dir_path(brief)``; a slug survives
    ``sanitize_prefix`` unchanged, and it never equals its folder's name, so
    ``find_output_dir``'s double-nesting guard never applies (§2.4, "Slug").
    """
    return output_dir_path(Path(brief))


def _first_line_is_marker(path: str) -> bool:
    """Whether the file's first line is exactly :data:`BRIEF_MARKER`."""
    try:
        with open(path, "rb") as handle:
            head = handle.readline(_FIRST_LINE_BYTES)
    except OSError:
        return False
    line = head.decode("utf-8", errors="replace")
    if line.endswith("\n"):
        line = line[:-1]
    if line.endswith("\r"):
        line = line[:-1]
    return line == BRIEF_MARKER


def commit_reviews_folder_rel(root: PathLike) -> Optional[str]:
    """The commit-reviews folder, repository-relative in git's form, for *root*.

    ``get_commit_reviews_dir(root)`` through ``git_utils.git_path``. ``None``
    when the accessor raises (the outside-root refusal, a malformed base, no
    repository): a caller that only drops artifacts then drops nothing extra
    rather than failing, and the front door's own call raises the error.
    """
    try:
        folder = get_commit_reviews_dir(anchor=root)
    except (ConfigError, OSError):
        return None
    relative = git_path(folder, repo_root=root)
    if (not relative or os.path.isabs(relative) or relative.startswith("/")
            or relative == ".." or relative.startswith("../")):
        return None
    return relative.rstrip("/")


def _relative_to_root(path: PathLike, root: Path, cwd: Optional[PathLike]) -> str:
    """*path* (relative to *cwd*, else absolute) as git names it under *root*."""
    text = os.fspath(path)
    if not os.path.isabs(text):
        text = os.path.join(os.fspath(cwd) if cwd else os.getcwd(), text)
    return git_path(os.path.normpath(text), repo_root=root)


def matches_brief_path(path: PathLike, *, cwd: Optional[PathLike] = None) -> bool:
    """§2.2's folder rule on the path string alone: ``<commit_reviews_dir>/<slug>.md``.

    *path* is relative to *cwd* (the process's cwd when None) or absolute; the
    folder comes from ``get_commit_reviews_dir`` anchored on *cwd*'s
    repository root. No file is read, so a deleted brief's path still
    matches (what ``[COMMIT_REVIEW_NOT_FOUND]`` needs). ``False`` outside a
    repository or when the accessor raises.
    """
    try:
        root = repo_root_of(cwd)
    except CommitReviewError:
        return False
    folder = commit_reviews_folder_rel(root)
    if folder is None:
        return False
    relative = _relative_to_root(path, root, cwd)
    prefix = folder + "/"
    return relative.startswith(prefix) and bool(
        _BRIEF_NAME_RE.fullmatch(relative[len(prefix):])
    )


def is_commit_brief(path: PathLike, *, cwd: Optional[PathLike] = None) -> bool:
    """Whether the existing file *path* is a commit brief (§2.2).

    Either its first line is exactly :data:`BRIEF_MARKER`, or it sits at
    ``<commit_reviews_dir>/<slug>.md`` (:func:`matches_brief_path`), so a
    brief whose header the user cut away still qualifies. When the folder
    accessor raises, the marker alone decides. A plan, a README, or a file
    that quotes the marker below line 1 is not a brief, and neither is a path
    that is not a file. No git call beyond finding the root.
    """
    text = os.fspath(path)
    full = text if os.path.isabs(text) else os.path.join(
        os.fspath(cwd) if cwd else os.getcwd(), text
    )
    if not os.path.isfile(full):
        return False
    if _first_line_is_marker(full):
        return True
    return matches_brief_path(full, cwd=cwd)


def brief_for_pinned(text: str, *, cwd: Optional[PathLike] = None) -> Optional[Path]:
    """The brief a pinned ``<base12>..<head12>`` names, or None for other text.

    ``status`` maps its positional through this before its existence check
    (§2.2, "`status` takes the pinned spelling"): text that fully matches
    :data:`PINNED_PATTERN` names ``<commit_reviews_dir>/<base12>-<head12>.md``
    with the folder anchored on *cwd*'s repository root, whether or not the
    brief exists. Resolves nothing: no git call beyond finding the root.
    Raises :class:`CommitReviewError` outside a repository and the accessor's
    :class:`~utils.provider_registry.ConfigError` for a refused folder.
    """
    candidate = (text or "").strip()
    if not _PINNED_RE.fullmatch(candidate):
        return None
    base12, head12 = candidate.split("..")
    root = repo_root_of(cwd)
    return get_commit_reviews_dir(anchor=root) / f"{base12}-{head12}.md"


def commit_review_artifact(path: str, folder: str) -> bool:
    """Whether repo-relative *path* is a commit review's own file (§2.4).

    True for ``<folder>/<slug>.md`` (a brief) and for anything under
    ``<folder>/<slug>/`` (its ``state.json``, phase dirs, context-plan
    snapshot, restart archives), a ``<folder>/<slug>/`` entry itself
    included. Anything else in *folder* (a README, a script the user keeps
    there) is not. Reads the
    string only, never the disk, so a brief present only at a commit, or
    deleted since, still matches. *folder* is
    :func:`commit_reviews_folder_rel`'s answer; an empty one matches nothing.
    """
    folder = (folder or "").replace("\\", "/").strip("/")
    if not folder or not path:
        return False
    candidate = path.replace("\\", "/")
    while candidate.startswith("./"):
        candidate = candidate[2:]
    prefix = folder + "/"
    if not candidate.startswith(prefix):
        return False
    name, separator, _rest = candidate[len(prefix):].partition("/")
    if separator:
        return bool(_SLUG_RE.fullmatch(name))
    return bool(_BRIEF_NAME_RE.fullmatch(name))


def document_label(state: Optional[Mapping]) -> str:
    """``"commit brief"`` when *state* records a ``commit_range``, else ``"plan"``.

    The one owner of the word user-facing lines use for the anchor document
    (§2.8, "'Commit brief', never 'plan'"): each site calls this rather than
    testing ``commit_range`` itself. *state* is a ``state.json`` mapping or
    anything with a ``get`` (a ``StateManager``); None is a plan.
    """
    getter = getattr(state, "get", None)
    if getter is None:
        return "plan"
    return "commit brief" if isinstance(getter("commit_range"), Mapping) else "plan"


def not_ignored_warning(dir: PathLike, brief: PathLike) -> Optional[str]:
    """``[COMMIT_REVIEWS_NOT_IGNORED]`` when git would show the brief, else None.

    Only for a folder that already exists: one the plugin is about to create
    gets its own ``.gitignore`` (:func:`ensure_commit_reviews_dir`). The
    question is whether git ignores the brief's repository-relative path
    (``git_utils.ignored_paths``), so a tracked brief counts as not ignored.
    Read-only; the caller prints the line before writing anything, and the
    run continues.
    """
    folder = Path(dir)
    if not folder.is_dir():
        return None
    try:
        root = repo_root_of(folder)
    except CommitReviewError:
        return None
    brief_rel = _relative_to_root(brief, root, None)
    if brief_rel in ignored_paths([brief_rel], cwd=str(root)):
        return None
    shown = git_path(folder, repo_root=root).rstrip("/")
    return (
        f"[COMMIT_REVIEWS_NOT_IGNORED] {shown} is not ignored by git: its "
        f"briefs and reports show in git status and can be committed; add "
        f"{shown}/ to .gitignore unless committing them is intended"
    )


def read_commit_range(brief: PathLike) -> Optional[Dict[str, Any]]:
    """The ``commit_range`` the brief's ``state.json`` records, or None.

    A raw, read-only JSON read (no ``StateManager``: nothing is created,
    migrated or written back). None when there is no state, it does not
    parse, or it holds no ``commit_range`` mapping.
    """
    path = output_dir_for_brief(brief) / "state.json"
    try:
        with open(path, "r", encoding="utf-8") as handle:
            document = json.load(handle)
    except (OSError, ValueError):
        return None
    record = document.get("commit_range") if isinstance(document, dict) else None
    return dict(record) if isinstance(record, Mapping) else None


# ---------------------------------------------------------------------------
# A --detach launch's stage
# ---------------------------------------------------------------------------
#
# Under ``--detach`` a commit front door stages what it decided in a file in the
# phase dir and names it on the worker's argv (``--commit-stage``); the worker
# applies it once it owns the dir (``commit_front_door.apply_stage``, handed to
# ``detach`` by the worker's entry). Reading a stage is the path layer's, so the
# launcher's take-over decision (``detach``) reads it without the front door.

#: The stage file's format; ``commit_front_door._write_stage`` writes it.
_STAGE_VERSION = 1


def read_stage(stage: PathLike) -> Optional[Dict[str, Any]]:
    """A stage file's payload, or None when it is gone (already applied)."""
    try:
        with open(stage, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError:
        return None
    if not isinstance(data, dict) or data.get("version") != _STAGE_VERSION:
        raise CommitReviewError(f"ERROR: {stage} is not a commit-review stage this "
                                f"version can apply", exit_code=_EXIT_ERROR)
    return data


def stage_takes_over(stage: Optional[PathLike]) -> bool:
    """Whether a launch carrying *stage* may take a live run over with its
    ``--force``: only when the user typed ``--force``. A restart's
    synthesised ``--force`` restarts the round and never takes over a live
    run. True when there is no readable stage (the flag decides)."""
    if not stage:
        return True
    try:
        data = read_stage(stage)
    except (CommitReviewError, OSError, ValueError):
        return True
    if data is None:
        return True
    return bool(data.get("typed_force", True))
