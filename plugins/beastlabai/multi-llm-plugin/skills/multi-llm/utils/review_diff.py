"""The review scope a code review reads: the one path classifier, the scope
manifest (``review-scope.md``) and one whole diff per changed source or test
file.

Split out of :mod:`utils.git_utils`, which re-exports every name defined here
for reading only: patch one of them here, in ``utils.review_diff``, never
through ``git_utils``. Every git command goes through ``git_utils``' hardened
builders (``git_argv``, ``_run_git``, ``_run_git_process``), so the hardening
documented there (and in docs/development/providers.md) applies unchanged:
this module spells no git argv of its own. Those helpers, and the other
``git_utils`` names used here, are looked up on the current ``git_utils`` at
each call (:func:`_git_utils`), never imported by name, so a patch of one
there reaches this module too.
"""

import functools
import hashlib
import importlib
import json
import os
import posixpath
import re
import shlex
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from types import ModuleType
from typing import (
    Any,
    Dict,
    Iterable,
    List,
    Mapping,
    NamedTuple,
    Optional,
    Pattern,
    Sequence,
    Set,
    Tuple,
    Union,
)


def _git_utils() -> ModuleType:
    """The ``git_utils`` module now in ``sys.modules``, looked up at each call.
    Holding no reference of its own, this module cannot keep using a
    ``git_utils`` that a failed import and its retry replaced, and a patch of a
    runner there reaches every command here."""
    return importlib.import_module(".git_utils", __package__)


# ---------------------------------------------------------------------------
# Review scope: the one classifier every consumer of the scope goes through
# ---------------------------------------------------------------------------
#
# A code review's scope is grouped and ordered in more than one place: the file
# list each reviewer's prompt carries, and the scope manifest plus per-file
# diffs written beside it (plan: review-run-scope-salvage-and-failure-visibility
# §2, D2.1/D2.2). Every one of them asks `classify_review_paths`, and nothing
# else holds a copy of the rules, so the prompt and the manifest can never put
# one path in two different groups.

REVIEW_GROUP_SOURCE = "source"
REVIEW_GROUP_TESTS = "tests"
REVIEW_GROUP_FIXTURES = "fixtures"
REVIEW_GROUP_GENERATED = "generated"

#: The groups in review order. The prompt's file list is cut at a character
#: budget, so whatever sorts last is what a cut drops, and hand-written source
#: is what a reviewer needs first. In plain path order `…/tests/…` sorts ahead
#: of `…/utils/…`: measured on a 1 040-path scope (880 of them
#: `tests/fixtures/opencode/**`), a populated list cut at 5 000 characters would
#: have kept the fixtures and dropped every `utils/` source file.
REVIEW_GROUP_ORDER: Tuple[str, ...] = (
    REVIEW_GROUP_SOURCE,
    REVIEW_GROUP_TESTS,
    REVIEW_GROUP_FIXTURES,
    REVIEW_GROUP_GENERATED,
)

#: The two configurable rules, as the ``code_review.collapse_paths`` block of
#: ``providers.yaml`` spells them. The shipped defaults below reproduce the
#: built-in fixture rule exactly (a ``tests/fixtures/`` or ``tests/golden/``
#: segment at any depth), so an unconfigured repository classifies as it always
#: did. This is the one copy of the defaults: the config accessor
#: (``provider_registry.get_collapse_paths``) falls back to it, and a test pins
#: the shipped ``providers.yaml`` block to it. Treat it as read-only.
COLLAPSE_PATH_KEYS: Tuple[str, ...] = (REVIEW_GROUP_GENERATED, REVIEW_GROUP_FIXTURES)
DEFAULT_COLLAPSE_PATHS: Mapping[str, Tuple[str, ...]] = {
    REVIEW_GROUP_GENERATED: (),
    REVIEW_GROUP_FIXTURES: ("**/tests/fixtures/**", "**/tests/golden/**"),
}

#: Directory components that make a path a test. Whole components only, so
#: ``contests/x.py`` and ``latest/x.py`` stay source.
_TEST_DIR_SEGMENTS = frozenset({"tests", "test"})
#: File-name markers that make a path a test, looked for in the file name only
#: (never in a directory name): ``test_x.py``, ``x_test.go``, ``x.test.ts``,
#: ``x.spec.js``.
_TEST_NAME_PREFIX = "test_"
_TEST_NAME_MARKERS: Tuple[str, ...] = ("_test.", ".test.", ".spec.")


@functools.lru_cache(maxsize=512)
def compile_path_glob(pattern: str) -> Pattern[str]:
    """Compile one ``collapse_paths`` glob into a regex over a repo-relative path.

    ``fnmatch`` does not fit: its ``*`` crosses ``/`` and it has no ``**``, so
    the shipped ``**/tests/fixtures/**`` would miss a top-level
    ``tests/fixtures/x.json`` (the leading ``**/`` would demand a separator
    before ``tests``). The rules here are the gitignore ones a user writing
    such a pattern already expects:

    * ``**/`` matches zero or more whole directories, a trailing ``/**``
      everything beneath a directory, and any other ``**`` any run of
      characters;
    * ``*`` and ``?`` never cross ``/``; ``[...]`` is a character class and
      ``[!...]`` its negation;
    * a pattern with no ``/`` in it matches the file name at any depth, so
      ``*.lock`` collapses ``poetry.lock`` and ``web/yarn.lock`` alike.

    Raises ``re.error`` for a class the regex engine rejects (``[z-a]``); the
    config loader compiles every configured pattern at load time so that
    surfaces as a config error, never mid-review.
    """
    pat = pattern.strip().replace("\\", "/")
    while pat.startswith("./"):
        pat = pat[2:]
    pat = pat.lstrip("/")
    if "/" not in pat:
        pat = "**/" + pat
    out: List[str] = []
    index, length = 0, len(pat)
    while index < length:
        if pat.startswith("**/", index):
            out.append("(?:.*/)?")
            index += 3
            continue
        if pat.startswith("/**", index) and index + 3 == length:
            out.append("/.*")
            index += 3
            continue
        if pat.startswith("**", index):
            out.append(".*")
            index += 2
            continue
        char = pat[index]
        if char == "*":
            out.append("[^/]*")
        elif char == "?":
            out.append("[^/]")
        elif char == "[":
            close = pat.find("]", index + 2)
            if close == -1:
                out.append(re.escape(char))
            else:
                body = pat[index + 1:close]
                if body.startswith("!"):
                    body = "^" + body[1:]
                out.append("[" + body.replace("\\", "\\\\") + "]")
                index = close + 1
                continue
        else:
            out.append(re.escape(char))
        index += 1
    return re.compile("".join(out), re.DOTALL)


def _normalized_review_path(path: str) -> str:
    """A path as the group rules read it: POSIX separators, no leading ``./``."""
    normalized = path.replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def _matches_any_glob(path: str, patterns: Sequence[str]) -> bool:
    return any(compile_path_glob(pattern).fullmatch(path) for pattern in patterns)


def _is_test_path(path: str) -> bool:
    """D2.1 rule 3: a ``tests/``/``test/`` directory component, or a test file name."""
    parts = [part for part in path.split("/") if part]
    if not parts:
        return False
    directories, name = parts[:-1], parts[-1]
    if any(part in _TEST_DIR_SEGMENTS for part in directories):
        return True
    if name.startswith(_TEST_NAME_PREFIX):
        return True
    return any(marker in name for marker in _TEST_NAME_MARKERS)


def _resolved_collapse_globs(
    collapse_paths: Optional[Mapping[str, Sequence[str]]],
) -> Dict[str, Tuple[str, ...]]:
    """Both glob lists, each falling back to its shipped default when absent.

    Per key, like ``get_write_paths``: a caller that passes only ``generated``
    keeps the default fixture rule rather than silently losing it. An explicit
    empty list is honoured — that is how a repository switches a rule off.
    """
    configured: Mapping[str, Sequence[str]] = collapse_paths or {}
    resolved: Dict[str, Tuple[str, ...]] = {}
    for key in COLLAPSE_PATH_KEYS:
        patterns = configured.get(key)
        if patterns is None:
            resolved[key] = tuple(DEFAULT_COLLAPSE_PATHS[key])
        else:
            resolved[key] = tuple(str(p) for p in patterns if str(p).strip())
    return resolved


def _check_attr_rejects_source(result: "subprocess.CompletedProcess[str]") -> bool:
    """Whether a ``check-attr --source`` call failed only because this git
    predates the option (Git 2.40): exit 129 with ``unknown option`` on stderr,
    as git's option parser reports it. Nothing else qualifies, so a bad
    ``--source`` value (exit 128) keeps the any-failure rule."""
    return result.returncode == 129 and "unknown option" in (result.stderr or "")


def _git_version_text(cwd: Optional[str]) -> str:
    """``git version 2.39.2`` or the like, for a warning; never raises."""
    try:
        stdout, _, rc = _git_utils()._run_git("--version", check=False, cwd=cwd)
    except (OSError, ValueError):
        return "an unknown git version"
    return stdout.strip() if rc == 0 and stdout.strip() else "an unknown git version"


def _linguist_generated(
    paths: Sequence[str], cwd: Optional[str] = None, *, source: Optional[str] = None,
) -> Set[str]:
    """The paths carrying the ``linguist-generated`` attribute, in one git call.

    ``--stdin -z`` rather than one argument per path: a large scope (1 040 paths
    on the run that motivated this) must not hit the argv limit, and ``-z``
    hands every path back byte-for-byte as given, with no quoting to undo.
    ``linguist-generated`` and ``linguist-generated=true`` both count (git
    reports them as ``set`` and ``true``); ``-linguist-generated`` and ``=false``
    do not.

    A failed call — outside a repository, or no ``git`` at all — marks nothing
    generated and prints one warning. It never raises: the attribute is one of
    four rules, and the other three still classify every path.

    ``source`` (a commit review's ``head``) reads ``.gitattributes`` as that
    commit has it, through ``check-attr --source=<head>`` (plans/review-commits.md
    §2.5). The option dates from Git 2.40; an older git fails the whole call on
    it (exit 129, ``unknown option``), and the any-failure rule would then
    classify nothing by attribute on every commit review. On that failure
    alone the call uses ``--attr-source`` (Git 2.41+) or a private index loaded
    from the pinned tree, with one warning naming the git version. It never
    falls back to the working tree's attributes. Any other failure keeps the
    rule above.
    """
    if not paths:
        return set()
    attr_args: List[str] = ["check-attr"]
    if source is not None:
        attr_args.append(f"--source={source}")
    attr_args += ["--stdin", "-z", "linguist-generated"]
    try:
        result = subprocess.run(
            _git_utils().git_argv(*attr_args, cwd=cwd),
            input="\0".join(paths) + "\0",
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=cwd,
        )
        if source is not None and _check_attr_rejects_source(result):
            print(
                f"Warning: git check-attr --source needs Git 2.40 or later and "
                f"this is {_git_version_text(cwd)}; reading linguist-generated "
                f"attributes from {source[:7]} through the pinned attribute fallback",
                file=sys.stderr,
            )
            result = _git_utils()._run_git_process(
                [*_git_utils().attribute_source_args(source), "check-attr", "--stdin", "-z", "linguist-generated"],
                input="\0".join(paths) + "\0",
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                cwd=cwd,
            )
    except (OSError, ValueError) as exc:
        print(
            f"Warning: git check-attr linguist-generated could not run ({exc}); "
            f"no review path is classified generated by attribute — the other "
            f"rules still apply",
            file=sys.stderr,
        )
        return set()
    if result.returncode != 0:
        detail = (result.stderr or "").strip().splitlines()
        print(
            f"Warning: git check-attr linguist-generated failed "
            f"({detail[0] if detail else f'exit {result.returncode}'}); no review "
            f"path is classified generated by attribute — the other rules still "
            f"apply",
            file=sys.stderr,
        )
        return set()
    fields = result.stdout.split("\0")
    generated: Set[str] = set()
    for index in range(0, len(fields) - 2, 3):
        path, _attribute, info = fields[index:index + 3]
        if info.strip().lower() in ("set", "true"):
            generated.add(path)
    return generated


def classify_review_paths(
    paths: Iterable[str],
    collapse_paths: Optional[Mapping[str, Sequence[str]]] = None,
    *,
    cwd: Optional[str] = None,
    source: Optional[str] = None,
) -> Dict[str, str]:
    """Put every review path in exactly one group; the first matching rule wins.

    1. *generated* — the path has the ``linguist-generated`` attribute (one
       batched ``git check-attr`` call, see :func:`_linguist_generated`), or it
       matches a ``collapse_paths["generated"]`` glob;
    2. *fixtures* — it matches a ``collapse_paths["fixtures"]`` glob (shipped:
       any ``tests/fixtures/`` or ``tests/golden/`` segment);
    3. *tests* — a ``tests/`` or ``test/`` directory component at any depth, or
       a file name starting ``test_`` or containing ``_test.``, ``.test.`` or
       ``.spec.``;
    4. *source* — everything else.

    So generated beats fixtures beats tests beats source: the codex mirror's
    ``utils/*.py`` copies are generated, not source, and a ``tests/fixtures/``
    file is a fixture, never a test.

    ``collapse_paths`` is the loaded ``code_review.collapse_paths`` block
    (``provider_registry.get_collapse_paths``) passed in by the caller, which
    keeps this free of config reads; ``None`` — or a key left out — means the
    shipped default for that rule. ``cwd`` is where git runs; the paths are
    the root-relative ones ``git diff --name-only`` prints, so a caller passes
    the repository root. The default, the process's cwd, is right only when
    that cwd IS the root: from a subdirectory git reads each path relative to
    it, and ``check-attr`` answers for files that do not exist.

    ``source`` is a commit review's ``head``: the attributes are then read as
    that commit has them (``check-attr --source``, with the pre-2.40 fallback
    :func:`_linguist_generated` describes). ``None`` reads the working tree's,
    as always.

    Returns ``{path: group}`` keyed by each distinct, non-empty input path as
    given; the order is the input's.
    """
    unique = [path for path in dict.fromkeys(paths) if path]
    globs = _resolved_collapse_globs(collapse_paths)
    by_attribute = _linguist_generated(unique, cwd=cwd, source=source)
    groups: Dict[str, str] = {}
    for path in unique:
        normalized = _normalized_review_path(path)
        if path in by_attribute or _matches_any_glob(
            normalized, globs[REVIEW_GROUP_GENERATED]
        ):
            groups[path] = REVIEW_GROUP_GENERATED
        elif _matches_any_glob(normalized, globs[REVIEW_GROUP_FIXTURES]):
            groups[path] = REVIEW_GROUP_FIXTURES
        elif _is_test_path(normalized):
            groups[path] = REVIEW_GROUP_TESTS
        else:
            groups[path] = REVIEW_GROUP_SOURCE
    return groups


def order_review_paths(
    paths: Iterable[str],
    collapse_paths: Optional[Mapping[str, Sequence[str]]] = None,
    *,
    cwd: Optional[str] = None,
    source: Optional[str] = None,
) -> List[str]:
    """The review order: source, tests, fixtures, generated; by path within each.

    The order is decided here, after resolution, and never taken from the
    resolver: its tracked-files branch de-duplicates through a ``set`` (hash
    order, different on every run) and its git fallback returns path order.
    Sorting within each group makes the result a function of the *set* of
    paths, so every permutation of the same input — and so every run over the
    same scope — renders the same list. Duplicates and empty strings are
    dropped. ``source`` is :func:`classify_review_paths`' (a commit review's
    ``head``).
    """
    return _review_order(
        classify_review_paths(paths, collapse_paths, cwd=cwd, source=source)
    )


def _review_order(groups: Mapping[str, str]) -> List[str]:
    """The paths of a :func:`classify_review_paths` result, in review order.

    Split out so :func:`write_review_diff` can order and group from ONE
    classification (one ``git check-attr``) instead of classifying twice.
    """
    rank = {group: index for index, group in enumerate(REVIEW_GROUP_ORDER)}
    return sorted(groups, key=lambda path: (rank[groups[path]], path))


def count_review_groups(groups: Mapping[str, str]) -> Dict[str, int]:
    """``{group: count}`` in :data:`REVIEW_GROUP_ORDER`, every group present."""
    counts = {group: 0 for group in REVIEW_GROUP_ORDER}
    for group in groups.values():
        counts[group] = counts.get(group, 0) + 1
    return counts


# ---------------------------------------------------------------------------
# The scope manifest and per-file diffs a code review reads
# ---------------------------------------------------------------------------
#
# A code reviewer used to be told only to run `git diff`, and a lane with no
# shell (cursor-agent in `--mode ask`, claude-code under `acceptEdits`) never saw
# a diff at all: on the run behind this, kimi returned nothing and grok spent
# 89% of its budget and made one wrong high-severity claim. The diff cannot be
# put in the prompt either — an argv lane's whole prompt is one argument (Linux
# `MAX_ARG_STRLEN`, 128 KB) and that change was 288 KB for its non-test source
# alone. So the scope and one whole diff per source or test file are written as
# files beside the report, and every lane that can read files reads them by
# path; its harness pages through a large file itself (plan:
# review-run-scope-salvage-and-failure-visibility §2, D2.2, decision 11.4).

REVIEW_SCOPE_FILENAME = "review-scope.md"
REVIEW_DIFF_DIRNAME = "diff"
DIFF_COVERAGE_COMPLETE = "complete"
DIFF_COVERAGE_PARTIAL = "partial"
DIFF_STATUS_FULL = "full"
#: The one reason a source or test path has no diff file although it changed.
#: There is no size-based omission: every diff is written whole.
DIFF_OMITTED_REASON = "git diff failed"
DIFF_STATUS_OMITTED = "omitted: " + DIFF_OMITTED_REASON
WRITTEN_BY_FANOUT = "fan-out"
WRITTEN_BY_REAGGREGATE = "reaggregate (regenerated from the current tree)"

#: A diff file name is ``<n>-<slug>.diff``; the slug is capped so a deep path
#: cannot produce a name the filesystem refuses. ``<n>`` keeps names unique.
_DIFF_SLUG_MAX_CHARS = 80
#: Generous on purpose: a timeout omits the path (coverage goes partial), so it
#: must only ever fire on a git that is genuinely stuck, never on a large file.
_DIFF_GIT_TIMEOUT_S = 300
_SCOPE_ID_CHARS = 12
_DIFF_FAILED_PRINT_LIMIT = 5
_DIFF_PARTIAL_SAMPLE = 5
#: `*` ignores the directory's contents and the file itself: a plans directory
#: that is committed does not commit a diff snapshot with every run, and
#: `git ls-files --others --exclude-standard` (the fallback's untracked count)
#: never counts an earlier run's diff files.
_DIFF_GITIGNORE = "*\n"
#: Diff flags that make the bytes a function of the tree, not of the user's
#: config: no colour codes from `color.ui=always`, no external diff program
#: (which may be interactive), and no rename pairing — each path's diff stands
#: on its own, so a deleted file shows every removed line.
_DIFF_FLAGS = ("--no-color", "--no-ext-diff", "--no-renames")


class ReviewDiffContainmentError(RuntimeError):
    """A diff file whose resolved target would not lie directly inside ``diff/``.

    Raised and never caught: the slug rule makes it impossible, so reaching it
    means that rule is broken, and a write outside the phase dir must not be
    skipped quietly. It is not a git failure and is not reported as one.
    """


class ReviewDiffSet(NamedTuple):
    """What :func:`write_review_diff` wrote (or found already on disk).

    ``coverage`` is :data:`DIFF_COVERAGE_COMPLETE` or
    :data:`DIFF_COVERAGE_PARTIAL`; ``omitted`` names every source or test path
    that has no diff file although it may have changed, with its reason.
    ``written`` is ``False`` when the manifest on disk already described this
    exact set and nothing was touched; ``written_by`` is then the header on
    disk, which may be an earlier reaggregate's.
    """

    coverage: str
    omitted: List[Tuple[str, str]]
    scope_id: str
    scope_file: str
    diff_dir: str
    base_ref: str
    base_commit: Optional[str]
    written_by: str
    written: bool
    failure: Optional[str]
    #: The commit a two-commit review ends at (``--head-ref``), as given, and
    #: what it resolved to; both ``None`` for a diff against the working tree.
    head_ref: Optional[str] = None
    head_commit: Optional[str] = None


class ReviewScopeHeader(NamedTuple):
    """The header and coverage block of a ``review-scope.md``, read back."""

    scope_id: str
    base_ref: str
    base_commit: Optional[str]
    written_by: str
    coverage: str
    omitted: List[Tuple[str, str]]
    #: Every diff file the manifest names, relative to the manifest
    #: (``diff/<n>-<slug>.diff``).
    diff_files: List[str]
    #: The byte size the manifest records for each of ``diff_files``.
    diff_sizes: Dict[str, int]
    #: The manifest's ``Head ref`` line, read back: the ref and its commit, or
    #: ``None`` when the set diffs against the working tree (no such line).
    head_ref: Optional[str] = None
    head_commit: Optional[str] = None


def review_diff_slug(path: str) -> str:
    """``path`` as a file-name fragment that can never leave ``diff/``.

    Every character outside ``[A-Za-z0-9._-]`` — ``/`` included — becomes
    ``-``, leading dots are stripped and the length is capped, so a slug holds
    no separator and is never ``.`` or ``..``.
    """
    slug = re.sub(r"[^A-Za-z0-9._-]", "-", path).lstrip(".")
    return slug[:_DIFF_SLUG_MAX_CHARS] or "file"


def _code_span(text: str) -> str:
    """``text`` as a Markdown code span that survives a backtick inside it."""
    longest = max((len(run) for run in re.findall(r"`+", text)), default=0)
    fence = "`" * (longest + 1)
    pad = " " if text.startswith("`") or text.endswith("`") else ""
    return f"{fence}{pad}{text}{pad}{fence}"


def _git_diff_output(
    args: Sequence[str], cwd: Optional[str]
) -> Tuple[Optional[bytes], Optional[str]]:
    """One git call for the diff set: ``(stdout bytes, None)`` or ``(None, why)``.

    Bytes, not text: a diff file must be the bytes git printed, and
    ``_run_git``'s lossy decode would change a non-UTF-8 line. Every way git can
    fail — a non-zero exit, a binary that will not start, a hang — comes back as
    the first line of its reason and never raises, because a git failure
    degrades the artifacts, never the phase. ``--literal-pathspecs`` so a path
    holding ``*`` or ``:(`` means that file and nothing else.
    """
    try:
        proc = _git_utils()._run_git_process(
            ["--literal-pathspecs", *args],
            capture_output=True,
            stdin=subprocess.DEVNULL,
            cwd=cwd,
            timeout=_DIFF_GIT_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired:
        return None, f"timed out after {_DIFF_GIT_TIMEOUT_S} s"
    except (OSError, ValueError) as exc:
        return None, f"git could not run ({exc})"
    if proc.returncode != 0:
        detail = proc.stderr.decode("utf-8", errors="replace").strip().splitlines()
        return None, detail[0] if detail else f"exit {proc.returncode}"
    return proc.stdout, None


def _resolve_base_commit(base_ref: str, cwd: Optional[str]) -> Optional[str]:
    out, error = _git_diff_output(
        ["rev-parse", "--verify", "--quiet", f"{base_ref}^{{commit}}"], cwd
    )
    if error is not None or not out:
        return None
    return out.decode("utf-8", errors="replace").strip() or None


_FULL_OBJECT_ID = re.compile(r"[0-9a-f]{40}|[0-9a-f]{64}")


def _is_empty_tree_base(base_ref: str, cwd: Optional[str]) -> bool:
    """Whether *base_ref* is the repository's empty-tree id: a root range's
    base (plans/review-commits.md §2.2). Only a full-length id is asked about,
    so any other ref costs no git call and keeps today's path exactly."""
    return bool(base_ref) and bool(_FULL_OBJECT_ID.fullmatch(base_ref)) and (
        _git_utils().is_empty_tree_id(base_ref, cwd)
    )


def _range_text(
    base_ref: str, base_commit: Optional[str], empty_tree: bool,
    head_ref: str, head_commit: Optional[str],
) -> str:
    """``<base7>..<head7>`` (``root..<head7>`` on a root range), as a user
    reads a range; display only, never typed back."""
    base = "root" if empty_tree else (base_commit or base_ref)[:7]
    return f"{base}..{(head_commit or head_ref)[:7]}"


_Counts = Tuple[Optional[int], Optional[int]]


def _scope_bytes(text: str) -> bytes:
    """``text`` as UTF-8, each ``surrogateescape`` stand-in as the byte it replaced.

    A file name that is not valid UTF-8 reaches this module the way Python
    decodes argv and file names — a lone surrogate per undecodable byte — and
    :func:`_numstat_counts` decodes git's ``-z`` output the same way, so the
    scope's paths can carry them; strict UTF-8 raises on one. The scope id and
    the manifest both encode through this, so each holds the bytes the file is
    really named by. Any other lone surrogate names no file git could have been
    handed, and falls back to ``surrogatepass`` so this never raises.
    """
    try:
        return text.encode("utf-8", errors="surrogateescape")
    except UnicodeEncodeError:
        return text.encode("utf-8", errors="surrogatepass")


def _numstat_counts(
    base_ref: str, paths: Sequence[str], cwd: Optional[str],
    head_ref: Optional[str] = None,
) -> Tuple[Dict[str, _Counts], Optional[str]]:
    """``{path: (added, deleted)}`` for the scope, or the first failure.

    ``-z`` hands each path back byte-for-byte, and it is decoded with
    ``surrogateescape`` — the inverse of how ``subprocess`` encoded the path it
    was given — so a path that is not valid UTF-8 keys its row under the very
    string the scope holds rather than a lossy stand-in :func:`_entry_counts`
    would never find. A binary (or ``-diff``) path reports ``-`` for both
    counts, kept as ``None``. ``head_ref`` makes it ``base head``: two
    commits, not the base against the working tree.
    """
    counts: Dict[str, _Counts] = {}
    sides = [base_ref] if head_ref is None else [base_ref, head_ref]
    for start in range(0, len(paths), _git_utils()._NUMSTAT_CHUNK):
        chunk = list(paths[start:start + _git_utils()._NUMSTAT_CHUNK])
        out, error = _git_diff_output(
            [*_git_utils().attribute_source_args(head_ref), "diff", "--numstat", "-z", *_DIFF_FLAGS,
             *sides, "--", *chunk], cwd
        )
        if error is not None:
            return counts, error
        for record in (out or b"").decode("utf-8", errors="surrogateescape").split("\0"):
            fields = record.split("\t", 2)
            if len(fields) != 3 or not fields[2]:
                continue
            added, deleted, path = fields
            counts[path] = (
                int(added) if added.isdigit() else None,
                int(deleted) if deleted.isdigit() else None,
            )
    return counts, None


def _entry_counts(path: str, counts: Mapping[str, _Counts]) -> _Counts:
    """A scope entry's counts: its own row, or the sum of the rows beneath it.

    A path absent from the numstat changed nothing (``(0, 0)``). A directory
    entry (an old ``tracked_files`` can hold one) sums what lies under it.
    """
    if path in counts:
        return counts[path]
    prefix = path.rstrip("/") + "/"
    rows = [value for key, value in counts.items() if key.startswith(prefix)]
    if not rows:
        return (0, 0)
    if any(a is None or d is None for a, d in rows):
        return (None, None)
    return (sum(a for a, _ in rows), sum(d for _, d in rows))  # type: ignore[misc]


def _counts_text(counts: Optional[_Counts]) -> str:
    if counts is None:
        return ""
    added, deleted = counts
    if added is None or deleted is None:
        return " (binary)"
    return f" (+{added} -{deleted})"


def _render_review_scope(
    *,
    scope_id: str,
    base_ref: str,
    base_commit: Optional[str],
    scope_source: Optional[str],
    written_by: str,
    failure: Optional[str],
    coverage: str,
    omitted: Sequence[Tuple[str, str]],
    reviewed_total: int,
    entries: Sequence[Dict[str, Any]],
    collapsed: Sequence[Dict[str, Any]],
    head_ref: Optional[str] = None,
    head_commit: Optional[str] = None,
    empty_tree: bool = False,
) -> str:
    if not base_ref:
        base_line = "- Base ref: (none: neither the requested ref nor HEAD~1 resolves)"
    elif empty_tree:
        description = (
            "empty tree: the range starts at the root commit" if head_ref is not None
            else "the empty tree: the repository had no commit, so every file is new"
        )
        base_line = f"- Base ref: `{base_ref}` ({description})"
    elif base_commit:
        base_line = f"- Base ref: `{base_ref}` (commit `{base_commit}`)"
    elif _git_utils().is_empty_tree(base_ref):
        base_line = (
            f"- Base ref: `{base_ref}` (the empty tree: the repository had no "
            f"commit, so every file is new)"
        )
    else:
        base_line = f"- Base ref: `{base_ref}` (does not resolve to a commit)"
    ref_lines = [base_line]
    if head_ref is not None:
        ref_lines.append(
            f"- Head ref: `{head_ref}` (commit `{head_commit}`)" if head_commit
            else f"- Head ref: `{head_ref}` (does not resolve to a commit)"
        )
    lines = [
        "# Review scope",
        "",
        f"- Scope id: `{scope_id}`",
        *ref_lines,
        f"- Scope source: {scope_source or 'not recorded'}",
        f"- Written: {datetime.now().isoformat(timespec='seconds')}",
        f"- Written by: {written_by}",
        "",
    ]
    if failure is not None:
        lines.append(f"Diff failed: {failure}")
    if coverage == DIFF_COVERAGE_COMPLETE:
        lines.append(f"Diff coverage: {DIFF_COVERAGE_COMPLETE}")
    else:
        lines.append(
            f"Diff coverage: {DIFF_COVERAGE_PARTIAL} — {len(omitted)} of "
            f"{reviewed_total} source and test files omitted"
        )
        for path, reason in omitted:
            lines.append(f"- {_code_span(path)}: {reason}")
    if head_ref is None:
        lines.extend([
            "",
            "Every path under review is listed below, grouped as source, tests, "
            "fixtures and generated. Each source and test entry names its diff file "
            "(relative to this file) with its size, or says on its own line why it "
            "has none. The diff files are the authoritative record of the change: "
            "each is one file's whole unified diff against the base ref, with both "
            "sides of every hunk, removed lines and deleted files included. A file's "
            "current contents show only the new side, so never review them in place "
            "of its diff. Fixture and generated paths are collapsed to one line per "
            "directory and get no diff file.",
        ])
    else:
        # A two-commit set: the new side is `head`, never the working tree,
        # which may hold other bytes (plans/review-commits.md §2.5).
        head7 = (head_commit or head_ref)[:7]
        lines.extend([
            "",
            "Every path under review is listed below, grouped as source, tests, "
            "fixtures and generated. Each source and test entry names its diff file "
            "(relative to this file) with its size, or says on its own line why it "
            "has none. The diff files are the authoritative record of the change: "
            "each is one file's whole unified diff from the base ref to the head "
            f"ref, commit `{head7}`, with both sides of every hunk, removed lines "
            "and deleted files included. The new side is each file as that commit "
            f"holds it (`git show {head7}:<path>`), not the working tree, which may "
            "differ from it, so never review a file's working-tree contents in "
            "place of its diff. Fixture and generated paths are collapsed to one "
            "line per directory and get no diff file.",
        ])

    def group_heading(title: str, count: int, suffix: str = "") -> None:
        noun = "file" if count == 1 else "files"
        lines.extend(["", f"## {title} ({count} {noun}{suffix})", ""])

    for group, title in ((REVIEW_GROUP_SOURCE, "Source"), (REVIEW_GROUP_TESTS, "Tests")):
        members = [entry for entry in entries if entry["group"] == group]
        group_heading(title, len(members))
        if not members:
            lines.append("_None._")
        for entry in members:
            head = f"{entry['number']}. {_code_span(entry['path'])}{_counts_text(entry['counts'])}"
            status = entry["status"]
            if entry["diff"]:
                lines.append(
                    f"{head} — {status}: `{entry['diff']}`, {entry['size']} bytes"
                )
            elif status == DIFF_STATUS_OMITTED and base_ref:
                sides = base_ref if head_ref is None else f"{base_ref} {head_ref}"
                command = f"git diff {sides} -- {shlex.quote(entry['path'])}"
                lines.append(
                    f"{head} — {status}. With a shell, {_code_span(command)} "
                    f"shows it"
                )
            else:
                lines.append(f"{head} — {status}")

    for group, title in (
        (REVIEW_GROUP_FIXTURES, "Fixtures"), (REVIEW_GROUP_GENERATED, "Generated"),
    ):
        members = [row for row in collapsed if row["group"] == group]
        group_heading(title, len(members), ", collapsed" if members else "")
        if not members:
            lines.append("_None._")
            continue
        by_dir: Dict[str, List[Dict[str, Any]]] = {}
        for row in members:
            directory = posixpath.dirname(_normalized_review_path(row["path"]))
            by_dir.setdefault(directory + "/" if directory else "./", []).append(row)
        for directory in sorted(by_dir):
            rows = by_dir[directory]
            noun = "file" if len(rows) == 1 else "files"
            summed: Optional[_Counts] = None
            if failure is None:
                known = [row["counts"] for row in rows]
                if any(a is None or d is None for a, d in known):
                    summed = (None, None)
                else:
                    summed = (sum(a for a, _ in known), sum(d for _, d in known))  # type: ignore[misc]
            lines.append(
                f"- {_code_span(directory)} — {len(rows)} {noun}"
                f"{_counts_text(summed)} — no diff: collapsed ({group})"
            )
    lines.append("")
    return "\n".join(lines)


_SCOPE_ID_LINE = re.compile(r"^- Scope id: `([0-9a-f]+)`\s*$")
_BASE_REF_LINE = re.compile(r"^- Base ref: (.*)$")
_HEAD_REF_LINE = re.compile(r"^- Head ref: (.*)$")
_WRITTEN_BY_LINE = re.compile(r"^- Written by: (.+?)\s*$")
_COVERAGE_LINE = re.compile(r"^Diff coverage: (complete|partial)\b")
_OMITTED_LINE = re.compile(r"^- (`+) ?(.*?) ?\1: (.+?)\s*$")
#: A source or test entry naming its diff file, as ``_render_review_scope``
#: writes it: ``<n>. <path>[ (counts)] — full: `diff/<name>.diff`, <size> bytes``.
#: Anchored on the numbered entry and on the end of its line, so an in-scope
#: path that merely looks like a diff file (``diff/fix-1.diff``, in its own
#: code span or in the coverage block) is never read as one the set wrote.
_DIFF_ENTRY_LINE = re.compile(
    r"^\d+\. .* — " + re.escape(DIFF_STATUS_FULL)
    + r": `(" + re.escape(REVIEW_DIFF_DIRNAME) + r"/[A-Za-z0-9._-]+\.diff)`, "
    + r"(\d+) bytes\r?$"
)


def read_review_scope(scope_file: Union[str, Path]) -> Optional[ReviewScopeHeader]:
    """The header and coverage of a ``review-scope.md``; ``None`` if unusable.

    ``None`` for a missing or unreadable file and for one without a scope id or
    a coverage line — an interrupted or hand-cut manifest reads as missing, and
    a reader then regenerates it rather than trusting half a file. The diff
    files are read off the numbered entries alone, each with the size its entry
    records. Decoded with ``surrogateescape``, as :func:`write_review_diff`
    encoded it, so a path that is not valid UTF-8 reads back as given.

    A two-commit set's ``Head ref`` line reads back as ``head_ref`` and
    ``head_commit``; a root range's base (the empty-tree id) reads back as
    that ``base_ref`` with no ``base_commit``.
    """
    try:
        text = Path(scope_file).read_text(encoding="utf-8", errors="surrogateescape")
    except (OSError, ValueError):
        return None
    scope_id = base_ref = written_by = coverage = None
    base_commit: Optional[str] = None
    head_ref: Optional[str] = None
    head_commit: Optional[str] = None
    omitted: List[Tuple[str, str]] = []
    in_coverage = False
    for line in text.splitlines():
        if in_coverage:
            match = _OMITTED_LINE.match(line)
            if match:
                omitted.append((match.group(2), match.group(3)))
                continue
            in_coverage = False
        if scope_id is None and (match := _SCOPE_ID_LINE.match(line)):
            scope_id = match.group(1)
        elif base_ref is None and (match := _BASE_REF_LINE.match(line)):
            value = match.group(1)
            ref = re.match(r"`([^`]*)`", value)
            base_ref = ref.group(1) if ref else ""
            commit = re.search(r"commit `([0-9a-f]+)`", value)
            base_commit = commit.group(1) if commit else None
        elif head_ref is None and (match := _HEAD_REF_LINE.match(line)):
            value = match.group(1)
            ref = re.match(r"`([^`]*)`", value)
            head_ref = ref.group(1) if ref else ""
            commit = re.search(r"commit `([0-9a-f]+)`", value)
            head_commit = commit.group(1) if commit else None
        elif written_by is None and (match := _WRITTEN_BY_LINE.match(line)):
            written_by = match.group(1)
        elif coverage is None and (match := _COVERAGE_LINE.match(line)):
            coverage = match.group(1)
            in_coverage = coverage == DIFF_COVERAGE_PARTIAL
    if not scope_id or not coverage:
        return None
    # Split on the "\n" the writer joins with, not `splitlines()`, which also
    # breaks at characters a path may hold (U+2028, \x1c…) and would part an
    # entry from its diff file.
    diff_sizes: Dict[str, int] = {}
    for line in text.split("\n"):
        match = _DIFF_ENTRY_LINE.match(line)
        if match:
            diff_sizes[match.group(1)] = int(match.group(2))
    diff_files = list(diff_sizes)
    return ReviewScopeHeader(
        scope_id=scope_id,
        base_ref=base_ref or "",
        base_commit=base_commit,
        written_by=written_by or "not recorded",
        coverage=coverage,
        omitted=omitted,
        diff_files=diff_files,
        diff_sizes=diff_sizes,
        head_ref=head_ref,
        head_commit=head_commit,
    )


def _diff_file_is_whole(target: Path, size: int) -> bool:
    try:
        return target.is_file() and target.stat().st_size == size
    except OSError:
        return False


def load_review_scope(out_dir: Union[str, Path]) -> Optional[ReviewScopeHeader]:
    """The manifest in ``out_dir`` when the pair is whole, else ``None``.

    Whole means: ``review-scope.md`` parses, ``diff/`` is a directory, and
    every diff file the manifest names exists at the byte size its entry
    records. Anything less — a phase dir from before the manifest existed, one
    cleaned by hand, a write interrupted part way, a diff file truncated or
    edited to another length — reads as missing.
    """
    out = Path(out_dir)
    header = read_review_scope(out / REVIEW_SCOPE_FILENAME)
    if header is None or not (out / REVIEW_DIFF_DIRNAME).is_dir():
        return None
    if not all(
        _diff_file_is_whole(out / rel, header.diff_sizes[rel])
        for rel in header.diff_files
    ):
        return None
    return header


def _diff_set_mismatch(
    out: Path, header: ReviewScopeHeader, entries: Sequence[Dict[str, Any]]
) -> Optional[str]:
    """Why the diff files on disk are not the ones ``entries`` hold, or ``None``.

    A scope id is computed from the diffs just generated, but reviewers read
    the files on disk, so a set is reused only when the manifest names exactly
    this set's files and each holds the very bytes computed for it (size, then
    sha256).
    """
    expected = {entry["diff"]: entry for entry in entries if entry["diff"]}
    if set(header.diff_files) != set(expected):
        return "its manifest names other diff files than this scope has"
    for rel, entry in expected.items():
        try:
            data = (out / rel).read_bytes()
        except OSError as exc:
            return f"{rel} cannot be read ({exc.strerror or exc})"
        if len(data) != entry["size"] or hashlib.sha256(data).hexdigest() != entry["sha256"]:
            return f"{rel} is not the diff that scope id describes"
    return None


def _contained_diff_target(out_dir: Path, diff_dir: Path, name: str) -> Path:
    """``diff_dir / name``, checked to lie directly inside ``diff/``."""
    target = diff_dir / name
    real_dir = os.path.realpath(diff_dir)
    if (
        not name
        or name in (".", "..")
        or "/" in name
        or os.sep in name
        or os.path.dirname(os.path.realpath(target)) != real_dir
        or os.path.dirname(real_dir) != os.path.realpath(out_dir)
    ):
        raise ReviewDiffContainmentError(
            f"refusing to write diff file {name!r}: its target "
            f"{os.path.realpath(target)} does not lie directly inside {real_dir} "
            f"(the diff file name rule is broken)"
        )
    return target


def _write_diff_file(target: Path, data: bytes) -> None:
    """Write one file of the set. A seam of its own so a test can interrupt it."""
    with open(target, "wb") as handle:
        handle.write(data)


def _reset_diff_dir(diff_dir: Path) -> None:
    """Empty ``diff/`` (or replace whatever stands at that name) and recreate it."""
    if diff_dir.is_symlink() or (diff_dir.exists() and not diff_dir.is_dir()):
        diff_dir.unlink()
    if diff_dir.is_dir():
        for child in diff_dir.iterdir():
            if child.is_dir() and not child.is_symlink():
                shutil.rmtree(child)
            else:
                child.unlink()
    diff_dir.mkdir(parents=True, exist_ok=True)


def write_review_diff(
    base_ref: Optional[str],
    paths: Iterable[str],
    out_dir: Union[str, Path],
    collapse_paths: Optional[Mapping[str, Sequence[str]]] = None,
    *,
    scope_source: Optional[str] = None,
    written_by: str = WRITTEN_BY_FANOUT,
    cwd: Optional[str] = None,
    head_ref: Optional[str] = None,
) -> ReviewDiffSet:
    """Write ``review-scope.md`` and ``diff/`` for a code review into ``out_dir``.

    The manifest lists every in-scope path with its ``git diff --numstat``
    counts, grouped by :func:`classify_review_paths` (the one classifier the
    prompt's file list uses too, so the two can never put a path in different
    groups; no ``git check-attr`` of its own), in :func:`order_review_paths`'
    order, which is why ``<n>`` numbers files source first even when the
    reaggregate hands over an unordered list. Each source and test path gets
    one whole diff file, ``diff/<n>-<slug>.diff`` — no per-file cap, no total
    cap, no chunking (decision 11.4) — or a status saying why it has none:
    ``no diff: no net change since <base_ref>``, or ``omitted: git diff
    failed``. Fixture and generated paths collapse to one line per directory
    (``no diff: collapsed (fixtures|generated)``).

    Git failures degrade the set, never the phase: an empty ``base_ref`` or a
    failed ``--numstat`` omits every source and test path (``Diff failed:`` in
    the manifest), a failed per-path diff omits that path, each prints
    ``[DIFF_FAILED]``, the coverage goes ``partial`` (``[DIFF_PARTIAL]``), and
    this returns normally. Only :class:`ReviewDiffContainmentError` raises.

    The set is computed in memory first. When the manifest on disk carries the
    same scope id (a hash of the base commit — or the failure — and every
    entry's path, status, counts and diff bytes) and the diff files it names
    are exactly this set's, each holding the bytes just computed for it,
    nothing is touched; a diff file truncated or edited since it was written
    fails that check, so a reused set shows reviewers the change its id
    describes. Otherwise the pair is replaced in an order that
    never leaves a manifest naming a file it did not write: delete the
    manifest, empty ``diff/``, write the diffs, then write the manifest last by
    temp file and rename. ``diff/.gitignore`` (``*``) keeps git from tracking
    any of it.

    ``cwd`` is where git runs, and a caller passes the repository root: the
    paths are root-relative, and a path intent-to-add marked for this review
    shows only in that repository's ``git diff``. The default, the process's
    cwd, is right only at the root — from a subdirectory git reads every path
    relative to it, each diff comes back empty, and the manifest would record
    ``no net change`` under ``complete`` coverage for files that did change.

    ``head_ref`` makes it a two-commit set (plans/review-commits.md §2.5):
    ``--numstat``, every per-path diff and the omitted-file command take
    ``base head``, so the working tree never enters it; ``.gitattributes`` is
    read as ``head`` has it (``check-attr --source``); a path with no diff
    reads ``no net change in <base7>..<head7>``; the manifest gains a ``Head
    ref`` line and says the new side is ``head``, not the working tree; and
    the scope id fingerprints both commits. ``None`` is the diff against the
    working tree, byte for byte as before. A ``base_ref`` that is the
    empty-tree id (a root range, §2.2) is not resolved as a commit: every file
    shows as added, and the manifest's ``Base ref`` line says the range starts
    at the root commit.
    """
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    scope_file = out / REVIEW_SCOPE_FILENAME
    diff_dir = out / REVIEW_DIFF_DIRNAME
    base_ref = base_ref or ""
    empty_tree = _is_empty_tree_base(base_ref, cwd)

    groups = classify_review_paths(paths, collapse_paths, cwd=cwd, source=head_ref)
    ordered = _review_order(groups)
    reviewed = [
        path for path in ordered
        if groups[path] in (REVIEW_GROUP_SOURCE, REVIEW_GROUP_TESTS)
    ]

    failure: Optional[str] = None
    base_commit: Optional[str] = None
    head_commit: Optional[str] = None
    counts: Dict[str, _Counts] = {}
    # The diff's two sides as git takes them: `base` alone (against the
    # working tree), or `base head`.
    sides: List[str] = [base_ref] if head_ref is None else [base_ref, head_ref]
    sides_text = " ".join(sides)
    if not base_ref:
        failure = (
            "git diff: no base ref (neither the requested ref nor HEAD~1 "
            "resolves: an initial commit, or a shallow clone), so there is "
            "nothing to diff against"
        )
    else:
        # The empty tree is no commit, and `^{commit}` would only say so.
        base_commit = None if empty_tree else _resolve_base_commit(base_ref, cwd)
        if head_ref is not None:
            head_commit = _resolve_base_commit(head_ref, cwd)
        if ordered:
            counts, numstat_error = _numstat_counts(
                base_ref, ordered, cwd, head_ref=head_ref
            )
            if numstat_error is not None:
                failure = (
                    f"git diff --numstat {sides_text} -- <{len(ordered)} paths>: "
                    f"{numstat_error}"
                )
    if failure is not None:
        print(f"[DIFF_FAILED] {failure}")
    if head_ref is None:
        no_change_status = f"no diff: no net change since {base_ref}"
    else:
        no_change_status = "no diff: no net change in " + _range_text(
            base_ref, base_commit, empty_tree, head_ref, head_commit
        )

    width = len(str(len(reviewed))) if reviewed else 1
    entries: List[Dict[str, Any]] = []
    diffs: Dict[str, bytes] = {}
    omitted: List[Tuple[str, str]] = []
    path_failures: List[str] = []
    for number, path in enumerate(reviewed, 1):
        entry: Dict[str, Any] = {
            "path": path, "group": groups[path], "number": number,
            "counts": None, "diff": None, "size": None, "sha256": None,
        }
        if failure is not None:
            entry["status"] = DIFF_STATUS_OMITTED
            omitted.append((path, DIFF_OMITTED_REASON))
        else:
            entry["counts"] = _entry_counts(path, counts)
            data, error = _git_diff_output(
                [*_git_utils().attribute_source_args(head_ref), "diff", *_DIFF_FLAGS, *sides, "--", path], cwd
            )
            if error is not None:
                entry["status"] = DIFF_STATUS_OMITTED
                omitted.append((path, DIFF_OMITTED_REASON))
                path_failures.append(
                    f"git diff {sides_text} -- {shlex.quote(path)}: {error}"
                )
            elif not data:
                entry["status"] = no_change_status
            else:
                name = f"{str(number).zfill(width)}-{review_diff_slug(path)}.diff"
                entry.update(
                    status=DIFF_STATUS_FULL,
                    diff=f"{REVIEW_DIFF_DIRNAME}/{name}",
                    size=len(data),
                    sha256=hashlib.sha256(data).hexdigest(),
                )
                diffs[name] = data
        entries.append(entry)
    for line in path_failures[:_DIFF_FAILED_PRINT_LIMIT]:
        print(f"[DIFF_FAILED] {line}")
    if len(path_failures) > _DIFF_FAILED_PRINT_LIMIT:
        print(
            f"[DIFF_FAILED] … and {len(path_failures) - _DIFF_FAILED_PRINT_LIMIT} "
            f"more path(s); every one is listed in {scope_file}"
        )

    collapsed = [
        {
            "path": path,
            "group": groups[path],
            "counts": _entry_counts(path, counts) if failure is None else None,
            "status": f"no diff: collapsed ({groups[path]})",
        }
        for path in ordered
        if groups[path] in (REVIEW_GROUP_FIXTURES, REVIEW_GROUP_GENERATED)
    ]

    # Partial exactly when a source or test path has no diff file although it
    # may have changed. A failed set omits every such path, so it is partial
    # whenever there is one; a scope of only fixtures (or nothing) lacks
    # nothing, and its `Diff failed:` line still says what git refused.
    coverage = DIFF_COVERAGE_PARTIAL if omitted else DIFF_COVERAGE_COMPLETE
    fingerprint: List[Any] = [
        base_commit or failure or base_ref,
        [
            [row["path"], row["group"], row["status"], row["counts"], row.get("sha256")]
            for row in [*entries, *collapsed]
        ],
    ]
    if head_ref is not None:
        # Both commits: the same diff bytes between another pair of commits
        # (a later head, the same base) are another review. A diff against
        # the working tree keeps its two-element fingerprint, so its scope id
        # is the one it always had.
        fingerprint.insert(1, head_commit or head_ref)
    scope_id = hashlib.sha256(
        _scope_bytes(json.dumps(fingerprint, ensure_ascii=False))
    ).hexdigest()[:_SCOPE_ID_CHARS]

    if coverage == DIFF_COVERAGE_PARTIAL:
        sample = ", ".join(path for path, _ in omitted[:_DIFF_PARTIAL_SAMPLE])
        if len(omitted) > _DIFF_PARTIAL_SAMPLE:
            sample += f" … and {len(omitted) - _DIFF_PARTIAL_SAMPLE} more"
        print(
            f"[DIFF_PARTIAL] {len(omitted)} of {len(reviewed)} source and test "
            f"files have no diff file ({DIFF_OMITTED_REASON})"
            + (f": {sample}" if sample else "")
            + "; a reviewer that cannot run git diff cannot review them"
        )

    def result(written: bool, recorded_by: str) -> ReviewDiffSet:
        return ReviewDiffSet(
            coverage=coverage,
            omitted=omitted,
            scope_id=scope_id,
            scope_file=str(scope_file.absolute()),
            diff_dir=str(diff_dir.absolute()),
            base_ref=base_ref,
            base_commit=base_commit,
            written_by=recorded_by,
            written=written,
            failure=failure,
            head_ref=head_ref,
            head_commit=head_commit,
        )

    existing = load_review_scope(out)
    if existing is not None and existing.scope_id == scope_id:
        mismatch = _diff_set_mismatch(out, existing, entries)
        if mismatch is None:
            if not (diff_dir / ".gitignore").exists():
                _write_diff_file(
                    _contained_diff_target(out, diff_dir, ".gitignore"),
                    _DIFF_GITIGNORE.encode("utf-8"),
                )
            print(f"Review scope unchanged (scope {scope_id}): {scope_file}")
            return result(False, existing.written_by)
        print(
            f"Review scope {scope_id} is on disk, but {mismatch}; rewriting the set"
        )

    text = _render_review_scope(
        scope_id=scope_id,
        base_ref=base_ref,
        base_commit=base_commit,
        scope_source=scope_source,
        written_by=written_by,
        failure=failure,
        coverage=coverage,
        omitted=omitted,
        reviewed_total=len(reviewed),
        entries=entries,
        collapsed=collapsed,
        head_ref=head_ref,
        head_commit=head_commit,
        empty_tree=empty_tree,
    )
    # The replacement order is the whole of the guarantee that a manifest on
    # disk only ever names files that exist and that this call wrote: with the
    # manifest gone first and written last, a write interrupted anywhere in
    # between leaves no manifest, which every reader treats as missing.
    scope_file.unlink(missing_ok=True)
    _reset_diff_dir(diff_dir)
    _write_diff_file(
        _contained_diff_target(out, diff_dir, ".gitignore"),
        _DIFF_GITIGNORE.encode("utf-8"),
    )
    for name, data in diffs.items():
        _write_diff_file(_contained_diff_target(out, diff_dir, name), data)
    # Imported here: this module's import-time code imports only the standard
    # library (it loads lazily through git_utils, tests/test_git_utils_moved_names.py).
    from .atomic_io import atomic_write_bytes

    atomic_write_bytes(scope_file, _scope_bytes(text))
    print(
        f"Review scope written (scope {scope_id}, coverage {coverage}, "
        f"{len(diffs)} diff file(s) for {len(reviewed)} source and test "
        f"file(s)): {scope_file}"
    )
    return result(True, written_by)
