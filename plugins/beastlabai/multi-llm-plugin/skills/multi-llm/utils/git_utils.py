"""Git utilities for the multi-llm skill: the hardened git argv builder and
runners, repository roots, worktree and index helpers, and the repository
metadata fingerprint.

Diff capture for a review's embedded context lives in :mod:`utils.git_diff`,
and the review scope (classifier, manifest, per-file diffs) in
:mod:`utils.review_diff`. This module still re-exports their names
(:data:`_MOVED`), **for reading only**: ``git_utils.capture_diff_hunks`` and
``from .git_utils import capture_diff_hunks`` return the owner's current
object, but a write here (``patch``, ``patch.object``, ``monkeypatch.setattr``,
plain assignment) only shadows the name in this module and reaches no moved
code (``monkeypatch``'s undo even leaves that copy behind), and ``del`` /
``monkeypatch.delattr`` raise ``AttributeError``. Patch a
moved name where it lives, ``utils.git_diff.X`` or ``utils.review_diff.X``;
``tests/test_git_utils_moved_names.py`` fails any test that patches one here.

The runner seam is the other way round and holds: both modules build and run
every git command through this module's ``git_argv``, ``_run_git`` and
``_run_git_process`` (and read the few other helpers they need) on the
``git_utils`` now in ``sys.modules``, at each call. A patch of one of those
here, such as an injected git refusal, reaches every caller, the moved code
included, as before the split.
"""

import hashlib
import importlib
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    Iterator,
    List,
    Mapping,
    Optional,
    Sequence,
    Set,
    Tuple,
    Union,
)

class GitError(Exception):
    """Raised when a git operation fails."""
    pass


#: The ``-c`` overrides every git command the plugin spawns carries (root
#: grant, 2026-10-05). A repo-wide batch on the plugin's Landlock jail can
#: write ``.git/config`` and ``.git/hooks/`` — the user decided against
#: backing the metadata up around each batch — so the plugin's own git calls
#: that run after it (the sweep's ``status``, ``ls-files`` and
#: ``hash-object``, intent-to-add's ``add -N``, review-code's diffs) must not
#: execute anything the batch planted: ``core.fsmonitor`` is a hook ``status``
#: and ``diff`` run on every call, and ``core.hooksPath`` is where ``add -N``
#: finds ``post-index-change``. Cheap and detective: the user's own git still
#: honours the planted config, which :func:`git_metadata_fingerprint` and the
#: scheduler's ``[GIT_CONFIG_CHANGED]`` line exist to say.
GIT_HARDENING_ARGS: Tuple[str, ...] = (
    "-c", "core.fsmonitor=false",
    "-c", "core.hooksPath=/dev/null",
    # `log.showSignature` makes `git log` / `git show <commit>` run
    # `gpg.program` on a signed commit (review fixes 2026-10-05).
    "-c", "log.showSignature=false",
    # Review fixes 2026-10-05: a planted `diff.noprefix` / `diff.mnemonicPrefix`
    # moves the `a/`, `b/` prefixes `_parse_unified_diff` keys hunks by, so
    # `capture_diff_hunks` returned no hunks and review-code reviewed nothing;
    # `diff.relative` from a subdirectory cwd prints nothing at all for a path
    # named from the root (measured, git 2.43). `diff.srcPrefix`/`dstPrefix`
    # are git 2.45+ and silently ignored before that.
    "-c", "diff.noprefix=false",
    "-c", "diff.mnemonicPrefix=false",
    "-c", "diff.srcPrefix=a/",
    "-c", "diff.dstPrefix=b/",
    "-c", "diff.relative=false",
)
#: The diff options for the same reason: ``diff.external`` and a driver's
#: ``diff.<x>.command`` / ``diff.<x>.textconv`` (bound by a plantable
#: ``.gitattributes``) are executables ``git diff`` runs by config.
GIT_DIFF_HARDENING_ARGS: Tuple[str, ...] = ("--no-ext-diff", "--no-textconv")

#: The git subcommands that take :data:`GIT_DIFF_HARDENING_ARGS`.
_DIFF_SUBCOMMANDS = frozenset({"diff", "diff-index", "diff-tree", "diff-files", "log", "show"})

#: The git global options that take a value, skipped by :func:`git_argv`'s
#: walk to the subcommand.
_GIT_GLOBAL_OPTIONS_WITH_VALUE = frozenset({"-C", "-c", "--git-dir", "--work-tree"})

#: The config keys a batch can plant that make git **execute** a program on
#: the subcommands the plugin runs, beyond the static set above: a clean /
#: smudge / process filter bound to a path by any attributes file (the
#: worktree's ``.gitattributes``, ``.git/info/attributes``, or a
#: ``core.attributesFile`` the same config names). Measured on git 2.43
#: (review fixes 2026-10-05): ``status --porcelain``, ``diff``, ``diff
#: --numstat``, ``add`` and ``hash-object`` (without ``--no-filters``) all run
#: a clean filter on a modified matching file; ``--attr-source=<empty tree>``
#: and ``required=false`` do not stop it, an empty ``-c filter.<n>.clean=``
#: does. Only a driver the **repository's own** config defines (scope
#: ``local`` or ``worktree``, includes resolved) is neutralized: that is what a
#: batch can write under the root grant, while a global ``filter.lfs.*`` is
#: the user's own tool, bound by the same attributes and left in force so the
#: plugin's view of an LFS-tracked file stays the user's.
_PLANTABLE_DRIVER_KEYS = r"^(filter\..+\.(clean|smudge|process|required)|core\.attributesfile)$"
_DRIVER_SCOPES_A_BATCH_CAN_WRITE = frozenset({"local", "worktree"})

#: The words, in any case, without which the repository's own config file
#: cannot give the probe anything to report, so :func:`planted_driver_overrides`
#: may answer ``[]`` without starting git (on Windows each git process costs
#: tens of milliseconds, and the probe ran before every plugin git call).
#: Git spells a section and a key in ASCII letters, digits, ``-`` and ``.``
#: only, compared case-insensitively, with no escapes and no line continuation
#: outside values, so a ``filter.<name>.*`` key cannot be written without the
#: letters ``filter``, nor ``core.attributesFile`` without ``attributesfile``.
#: ``include`` covers ``include.path`` and ``includeIf``, which read another
#: file into the same scope; ``worktree`` covers ``extensions.worktreeConfig``
#: (a second, worktree-scoped file) and ``core.worktree``. Any of them, even
#: in a value or a comment, sends the call to the probe: a false alarm costs
#: one git process, a miss would run a planted driver.
_CONFIG_WORDS_THE_PROBE_MUST_READ = (b"filter", b"attributesfile", b"include", b"worktree")

#: The ``GIT_*`` variables that move neither which repository git finds nor
#: which files it reads as that repository's own config. Identity, prompts,
#: tracing, and the global, system and command-line config layers (whose
#: drivers the probe leaves in force anyway) are all here. Any other ``GIT_*``
#: variable that is set (``GIT_DIR``, ``GIT_COMMON_DIR``, ``GIT_WORK_TREE``,
#: ``GIT_CEILING_DIRECTORIES``, ``GIT_CONFIG``, ``GIT_OBJECT_DIRECTORY``, or
#: one this list does not know) sends every call to the probe.
_GIT_ENV_THAT_MOVES_NO_REPOSITORY_CONFIG = frozenset({
    "GIT_OPTIONAL_LOCKS", "GIT_TERMINAL_PROMPT", "GIT_ASKPASS", "GIT_EDITOR",
    "GIT_SEQUENCE_EDITOR", "GIT_PAGER", "GIT_SSH", "GIT_SSH_COMMAND", "GIT_SSH_VARIANT",
    "GIT_AUTHOR_NAME", "GIT_AUTHOR_EMAIL", "GIT_AUTHOR_DATE",
    "GIT_COMMITTER_NAME", "GIT_COMMITTER_EMAIL", "GIT_COMMITTER_DATE",
    "GIT_CONFIG_GLOBAL", "GIT_CONFIG_SYSTEM", "GIT_CONFIG_NOSYSTEM",
    "GIT_CONFIG_PARAMETERS", "GIT_CONFIG_COUNT",
    "GIT_TRACE", "GIT_TRACE2", "GIT_TRACE2_EVENT", "GIT_TRACE2_PERF",
    "GIT_TRACE_PERFORMANCE", "GIT_TRACE_SETUP", "GIT_TRACE_PACKET", "GIT_TRACE_CURL",
    "GIT_MERGE_AUTOEDIT", "GIT_FLUSH", "GIT_PROTOCOL_FROM_USER",
})
#: ``GIT_CONFIG_KEY_<n>`` / ``GIT_CONFIG_VALUE_<n>``: the command-line layer too.
_GIT_ENV_COMMAND_CONFIG = re.compile(r"^GIT_CONFIG_(KEY|VALUE)_\d+$")


def _hardened_argv(*args: str) -> List[str]:
    """``git`` plus the static :data:`GIT_HARDENING_ARGS` plus ``args``: the
    one place a ``["git", …]`` list is spelled. :func:`git_argv` adds the
    per-repository driver overrides on top; the probe that reads them uses
    this builder directly, which is what keeps the two from recursing."""
    return ["git", *GIT_HARDENING_ARGS, *args]


def _parse_scoped_config(stdout: str) -> List[Tuple[str, str, str]]:
    """``(scope, key, value)`` triples from ``git config -z --show-scope
    --get-regexp`` output: ``scope NUL key LF value NUL`` per match, a
    valueless key carrying no LF."""
    tokens = stdout.split("\0")
    out: List[Tuple[str, str, str]] = []
    for index in range(0, len(tokens) - 1, 2):
        scope, rest = tokens[index], tokens[index + 1]
        key, _, value = rest.partition("\n")
        if key:
            out.append((scope, key, value))
    return out


def _cwd_from_global_options(args: Sequence[str]) -> Optional[str]:
    """The ``-C <dir>`` a caller put ahead of the subcommand, if any."""
    index = 0
    while index < len(args) and args[index].startswith("-"):
        if args[index] == "-C" and index + 1 < len(args):
            return args[index + 1]
        index += 2 if args[index] in _GIT_GLOBAL_OPTIONS_WITH_VALUE else 1
    return None


#: How much of HEAD git's ``validate_headref`` reads: ``sizeof(buffer) - 1`` of
#: a 256-byte buffer. A ``refs/`` that starts beyond it is invisible to git,
#: which then treats the directory as no repository and keeps looking above
#: it, so this check must not see further than git does.
_HEAD_BYTES_GIT_READS = 255


def _head_is_valid(git_dir: str) -> bool:
    """Whether ``<git_dir>/HEAD`` passes git's own check (``validate_headref``):
    a symbolic ref into ``refs/``, or an object id, within the first
    :data:`_HEAD_BYTES_GIT_READS` bytes. A directory whose HEAD fails it is not
    a repository to git, which then keeps looking above it. Where the two
    could differ this is the stricter one (only spaces and tabs after
    ``ref:``, nothing after an object id), so a doubt goes to the probe."""
    head = os.path.join(git_dir, "HEAD")
    if os.path.islink(head):
        return os.readlink(head)[:_HEAD_BYTES_GIT_READS].startswith("refs/")
    with open(head, "rb") as handle:
        data = handle.read(_HEAD_BYTES_GIT_READS)
    if data.startswith(b"ref:"):
        return data[4:].lstrip(b" \t").startswith(b"refs/")
    return re.match(rb"^([0-9a-f]{40}|[0-9a-f]{64})\s*$", data) is not None


def _repository_config_names_no_driver(cwd: Optional[str]) -> bool:
    """``True`` only when the repository git would find from ``cwd`` certainly
    defines no driver :func:`planted_driver_overrides` reports, read from its
    one config file without starting git. ``False`` whenever that is not
    certain, and the caller then asks git.

    Certain means all of:

    * no ``GIT_*`` variable outside :data:`_GIT_ENV_THAT_MOVES_NO_REPOSITORY_CONFIG`
      is set, so git discovers the repository from ``cwd`` as below;
    * walking up from ``cwd`` (resolved, as git sees it), the first directory
      holding a ``.git`` holds a real ``.git`` directory that git itself would
      accept: a valid HEAD and ``objects``/``refs`` directories, else git walks
      past it to a repository above. No level on the way is itself a ``.git``
      directory or holds a ``HEAD`` (git also accepts a bare repository there),
      and none is unreadable. A gitfile (a linked worktree or a submodule), a
      symlinked ``.git`` or no repository at all is not certain;
    * that directory has no ``commondir`` (a linked worktree's config lives in
      the main repository) and no ``config.worktree``;
    * its ``config``, if any, holds none of :data:`_CONFIG_WORDS_THE_PROBE_MUST_READ`.

    The file is read on every call, never cached: the batch that plants a
    driver runs between the plugin's git calls.
    """
    for name in os.environ:
        upper = name.upper()
        if (upper.startswith("GIT_") and upper not in _GIT_ENV_THAT_MOVES_NO_REPOSITORY_CONFIG
                and not _GIT_ENV_COMMAND_CONFIG.match(upper)):
            return False
    level = os.path.realpath(cwd or os.getcwd())
    while True:
        if os.path.basename(level).lower() == ".git":
            return False
        dot_git = os.path.join(level, ".git")
        try:
            info = os.lstat(dot_git)
        except FileNotFoundError:
            info = None
        if info is not None:
            if not stat.S_ISDIR(info.st_mode):
                return False
            break
        if os.path.lexists(os.path.join(level, "HEAD")):
            return False
        parent = os.path.dirname(level)
        if parent == level:
            return False
        level = parent
    # git's is_git_directory: both directories searchable (access X_OK) and HEAD valid.
    for name in ("objects", "refs"):
        path = os.path.join(dot_git, name)
        if not (os.path.isdir(path) and os.access(path, os.X_OK)):
            return False
    if not _head_is_valid(dot_git):
        return False
    if (os.path.lexists(os.path.join(dot_git, "commondir"))
            or os.path.lexists(os.path.join(dot_git, "config.worktree"))):
        return False
    try:
        with open(os.path.join(dot_git, "config"), "rb") as handle:
            text = handle.read().lower()
    except FileNotFoundError:
        return True
    return not any(word in text for word in _CONFIG_WORDS_THE_PROBE_MUST_READ)


def planted_driver_overrides(cwd: Optional[str] = None) -> List[str]:
    """The ``-c`` overrides that neutralize every filter driver, and any
    ``core.attributesFile``, the repository at ``cwd`` defines in its own
    config (see :data:`_PLANTABLE_DRIVER_KEYS`). Read without executing
    anything — one ``git config`` probe, itself hardened and never a
    :func:`git_argv` call — and empty outside a repository, when git is
    absent, or when the probe fails: a probe may not fail a git call. Read
    on every call rather than cached, because the batch that plants a driver
    runs between the plugin's git calls (~1 ms measured on Linux, tens of ms
    on Windows).

    The probe is skipped when the repository's config file is read directly
    and cannot name such a driver (:func:`_repository_config_names_no_driver`),
    which is the usual case; anything that read cannot settle goes to git."""
    try:
        if _repository_config_names_no_driver(cwd):
            return []
    except (OSError, ValueError):
        pass
    try:
        proc = subprocess.Popen(
            _hardened_argv(
                "config", "-z", "--show-scope", "--get-regexp", _PLANTABLE_DRIVER_KEYS,
            ),
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL,
            **({"cwd": cwd} if cwd else {}),
        )
        try:
            stdout, _ = proc.communicate(timeout=30)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.communicate()
            return []
    except (OSError, ValueError, subprocess.SubprocessError):
        return []
    if not isinstance(stdout, bytes) or proc.returncode not in (0, 1):
        return []
    names: Set[str] = set()
    attributes_file = False
    for scope, key, _value in _parse_scoped_config(
        stdout.decode("utf-8", errors="replace")
    ):
        if scope not in _DRIVER_SCOPES_A_BATCH_CAN_WRITE:
            continue
        if key == "core.attributesfile":
            attributes_file = True
        elif key.startswith("filter."):
            name = key[len("filter."):].rsplit(".", 1)[0]
            if name:
                names.add(name)
    overrides: List[str] = []
    for name in sorted(names):
        overrides += [
            "-c", f"filter.{name}.clean=",
            "-c", f"filter.{name}.smudge=",
            "-c", f"filter.{name}.process=",
            # `required=true` beside an emptied driver is `fatal: clean filter
            # failed` (measured): the planted key must not break the call.
            "-c", f"filter.{name}.required=false",
        ]
    if attributes_file:
        overrides += ["-c", f"core.attributesFile={os.devnull}"]
    return overrides


def git_argv(*args: str, cwd: Optional[str] = None) -> List[str]:
    """``git`` plus :data:`GIT_HARDENING_ARGS` plus the repository's
    :func:`planted_driver_overrides` plus ``args`` — the one way the plugin
    spells a git command (``tests/test_git_utils.py`` fails any runtime git
    list literal outside :func:`_hardened_argv`). ``cwd`` is where the
    command will run — pass the same value the spawn gets, since the driver
    overrides are read from that repository; a ``-C <dir>`` global option
    counts, else the process's cwd. A diff-producing subcommand also gets
    :data:`GIT_DIFF_HARDENING_ARGS` right after its name; a ``git show
    <ref>:<path>`` blob read accepts them harmlessly."""
    rest = list(args)
    argv = _hardened_argv(*planted_driver_overrides(cwd or _cwd_from_global_options(rest)))
    # Global options (`--literal-pathspecs`, `-C <dir>`) precede the subcommand.
    index = 0
    while index < len(rest) and rest[index].startswith("-"):
        index += 2 if rest[index] in _GIT_GLOBAL_OPTIONS_WITH_VALUE else 1
    if index < len(rest) and rest[index] in _DIFF_SUBCOMMANDS:
        rest[index + 1:index + 1] = list(GIT_DIFF_HARDENING_ARGS)
    return argv + rest


def attribute_source_args(source: Optional[str]) -> List[str]:
    """Pin attributes as well as blobs for a two-commit read."""
    return [f"--attr-source={source}"] if source is not None else []


def _run_git_process(args: Sequence[str], *, cwd: Optional[str] = None,
                     **kwargs: Any) -> subprocess.CompletedProcess:
    """Run hardened git, with a private-index fallback for pre-2.41 git.

    Two commits alone do not pin a diff: working-tree attributes can mark a
    text file binary or change its hunk boundaries. ``--attr-source`` fixes
    that. Older git reads the same attributes from a temporary index populated
    from the source tree and an empty worktree. Neither the real index nor the
    checkout is modified, and each call owns its environment and temporary files.
    """
    where = {"cwd": cwd} if cwd is not None else {}
    argv = git_argv(*args, cwd=cwd)
    result = subprocess.run(argv, **where, **kwargs)
    source_arg = next((arg for arg in args if arg.startswith("--attr-source=")), None)
    error = result.stderr or ""
    if isinstance(error, bytes):
        error = error.decode("utf-8", errors="replace")
    if source_arg is None or result.returncode != 129 or not (
        "unknown option" in error and "attr-source" in error
    ):
        return result

    git_dir, _, rc = _run_git("rev-parse", "--absolute-git-dir", check=False, cwd=cwd)
    if rc != 0:
        return result
    source = source_arg.partition("=")[2]
    with tempfile.TemporaryDirectory(prefix="multi-llm-attributes-") as scratch:
        env = dict(kwargs.get("env") or os.environ)
        env.update(GIT_DIR=git_dir.strip(), GIT_WORK_TREE=scratch,
                   GIT_INDEX_FILE=os.path.join(scratch, "index"))
        env.pop("GIT_ATTR_SOURCE", None)
        prepared = subprocess.run(
            git_argv("read-tree", source, cwd=cwd), cwd=scratch, env=env,
            capture_output=True, stdin=subprocess.DEVNULL,
            timeout=kwargs.get("timeout", 60),
        )
        if prepared.returncode != 0:
            # Preserve the caller's text/bytes contract on this failure too.
            if kwargs.get("text") or kwargs.get("encoding"):
                prepared.stdout = prepared.stdout.decode("utf-8", errors="replace")
                prepared.stderr = prepared.stderr.decode("utf-8", errors="replace")
            return prepared
        options = dict(kwargs, env=env)
        return subprocess.run([arg for arg in argv if arg != source_arg],
                              cwd=scratch, **options)


def _run_git(
    *args: str, check: bool = True, cwd: Optional[str] = None
) -> Tuple[str, str, int]:
    """Run a git command and return (stdout, stderr, returncode).

    ``cwd`` is where git runs; ``None`` is the process's cwd (and passes no
    ``cwd`` at all, so every caller that names none runs exactly as before).
    """
    # Decode git output as UTF-8 with errors="replace": lossy for non-UTF-8
    # bytes but guarantees a total decode, the standard choice for tool/LLM
    # text output. Rejected alternatives: surrogateescape (lone surrogates
    # raise UnicodeEncodeError on downstream UTF-8 re-encode) and
    # backslashreplace (noisier in model-visible output).
    result = _run_git_process(
        args, cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if check and result.returncode != 0:
        raise GitError(f"git {' '.join(args)} failed: {result.stderr}")
    return result.stdout, result.stderr, result.returncode

def get_project_root(from_path: str) -> Optional[str]:
    """Detect project root via git rev-parse --show-toplevel.

    Args:
        from_path: A file path within the project (used to determine
                   which directory to run git from).

    Returns:
        Absolute path to the project root, or None if not in a git repo.
    """
    probe_dir = os.path.dirname(from_path) or "."
    result = subprocess.run(
        git_argv("rev-parse", "--show-toplevel", cwd=probe_dir),
        capture_output=True, text=True,
        encoding="utf-8", errors="replace",
        cwd=probe_dir,
    )
    if result.returncode == 0:
        return result.stdout.strip()
    return None


#: Environment variables that point git at another repository or working
#: tree than the one the plan is in. :func:`pin_repo_root` refuses while any
#: is set: the plugin's git calls and a repo-wide jail would then disagree
#: about which tree they act on.
GIT_ENV_REDIRECTS: Tuple[str, ...] = ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR")


def find_git_entry_root(start: str) -> Optional[str]:
    """The nearest directory at or above ``start`` holding a ``.git`` entry
    (a directory, or the gitfile of a linked worktree or submodule),
    ``realpath``'d; ``None`` when there is none. Pure path walking — git
    itself is not asked, so no configuration can move the answer."""
    current = os.path.realpath(start)
    while True:
        if os.path.lexists(os.path.join(current, ".git")):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            return None
        current = parent


def pin_repo_root(start_dir: str) -> Tuple[Optional[str], Optional[str]]:
    """``(root, problem)``: the repository root pinned independently of git's
    configuration, and why it cannot be trusted when it cannot.

    The root is :func:`find_git_entry_root`'s walk, never ``git rev-parse
    --show-toplevel`` alone: a repo-wide batch on the root grant can write
    ``[core] worktree = <dir>`` into ``.git/config`` (or replace ``.git`` with
    a gitfile naming a git dir whose config says so), after which every
    later phase and ``--resume`` re-pinned the root from git's answer and the
    next repo-wide jail's one rule landed on the planted directory (review
    fixes 2026-10-05). git is still asked, and its answer must **equal** the
    walked root; a ``core.worktree`` that agrees (a submodule sets one
    legitimately) is fine, one that disagrees is named as the cause. While a
    :data:`GIT_ENV_REDIRECTS` variable is set nothing is pinned at all.
    ``(None, None)`` outside any repository.
    """
    # Spelled out rather than iterated: the codex package's environment
    # census resolves literal reads and module constants only.
    redirected = [
        name for name, value in (
            ("GIT_DIR", os.environ.get("GIT_DIR")),
            ("GIT_WORK_TREE", os.environ.get("GIT_WORK_TREE")),
            ("GIT_COMMON_DIR", os.environ.get("GIT_COMMON_DIR")),
        ) if value
    ]
    if redirected:
        return None, (
            f"{', '.join(redirected)} is set in the environment, so git would act "
            f"on another repository or working tree than the one the plan is in; "
            f"unset it for this run"
        )
    root = find_git_entry_root(start_dir)
    if root is None:
        return None, None
    worktree_out, _, worktree_rc = _run_git(
        "config", "--get", "core.worktree", check=False, cwd=root,
    )
    configured = worktree_out.strip() if worktree_rc == 0 else ""
    top_out, _, top_rc = _run_git("rev-parse", "--show-toplevel", check=False, cwd=root)
    answered = os.path.realpath(top_out.strip()) if top_rc == 0 and top_out.strip() else None
    if answered == root or (answered is None and not configured):
        # Agreement — or nothing to compare: git cannot answer (a `.git`
        # that is not a repository, dubious ownership) and no `core.worktree`
        # is configured, so the walked root stands; a redirect needs the
        # configuration git would have honoured, and none is there.
        return root, None
    cause = (
        f"core.worktree = {configured!r} in its configuration redirects the "
        f"working tree — a repo-wide batch can plant that key in .git/config, so "
        f"inspect .git/config and remove it (git config --unset core.worktree)"
        if configured else
        f"the .git entry or the configuration it points at redirects the "
        f"working tree (a gitfile naming another git directory, say); inspect "
        f"{os.path.join(root, '.git')}"
    )
    where = (
        f"git answers {answered} as the top level" if answered
        else "git cannot confirm the top level"
    )
    return root, (
        f"{where} of the tree whose .git entry is at {root}: {cause}"
    )


def get_project_root_from_dir(directory: Optional[str] = None) -> Optional[str]:
    """Detect the git project root by running git from a *directory* directly.

    Unlike :func:`get_project_root`, which takes a *file* path and uses its
    ``dirname`` to choose where to run git, this takes a directory and runs
    ``git rev-parse --show-toplevel`` there with no path manipulation. Pass a
    directory (e.g. CWD or a target-repo dir) directly without the brittle
    synthetic-path trick (``get_project_root(os.path.join(cwd, "_"))``) that
    relies on ``dirname`` stripping a fake segment.

    Args:
        directory: Directory to run git discovery from. Defaults to CWD.

    Returns:
        Absolute path to the project root, or None if not in a git repo.
    """
    result = subprocess.run(
        git_argv("rev-parse", "--show-toplevel", cwd=directory or "."),
        capture_output=True, text=True,
        encoding="utf-8", errors="replace",
        cwd=directory or "."
    )
    if result.returncode == 0:
        return result.stdout.strip()
    return None


def _porcelain_destination(path_field: str) -> str:
    """Return the on-disk path of a ``git status --porcelain`` path field.

    Rename and copy entries render as ``<old> -> <new>``; the path that exists
    in the working tree is the destination, so the source half is dropped. Git
    quotes either side when it contains a space, which is what makes the
    separator unambiguous: an unquoted destination contains no space of its own,
    and a quoted one is the trailing ``"..."``.
    """
    if path_field.endswith('"'):
        index = path_field.rfind(' -> "')
        if index != -1:
            return path_field[index + len(" -> "):]
        return path_field
    index = path_field.rfind(" -> ")
    if index != -1:
        return path_field[index + len(" -> "):]
    return path_field


_C_ESCAPES = {
    "a": "\a", "b": "\b", "f": "\f", "n": "\n",
    "r": "\r", "t": "\t", "v": "\v", "\\": "\\", '"': '"',
}


def _unescape_c_quoted(body: str) -> str:
    """Undo git's C-style escaping inside a quoted path field.

    Git escapes the control characters and the quote/backslash by name and
    every other byte it does not consider printable as a three-digit octal
    ``\\303`` — one per UTF-8 *byte*, so the octals are collected as bytes and
    decoded together at the end (``errors="replace"``, matching `_run_git`).
    """
    out = bytearray()
    i = 0
    while i < len(body):
        ch = body[i]
        if ch != "\\" or i + 1 >= len(body):
            out += ch.encode("utf-8")
            i += 1
            continue
        nxt = body[i + 1]
        if nxt in _C_ESCAPES:
            out += _C_ESCAPES[nxt].encode("utf-8")
            i += 2
        elif nxt.isdigit() and len(body) >= i + 4:
            try:
                out.append(int(body[i + 1:i + 4], 8))
                i += 4
            except ValueError:
                out += ch.encode("utf-8")
                i += 1
        else:
            # Not an escape git produces; keep the backslash verbatim rather
            # than inventing a path that does not exist.
            out += ch.encode("utf-8")
            i += 1
    return out.decode("utf-8", errors="replace")


def _unquote_porcelain_path(path: str) -> str:
    """Return the real on-disk path behind a quoted ``git status`` path field.

    Git quotes a path that contains a space, a quote or a non-printable byte
    and C-escapes what is inside. Both halves have to come off: a census entry
    left as ``"sp ace.txt"`` (quotes included) matches no baseline entry, lands
    in ``tracked_files`` verbatim, and `review-code` then diffs a path that
    does not exist. An unquoted path is returned untouched —
    a literal backslash in a bare porcelain path is not an escape.
    """
    if len(path) >= 2 and path.startswith('"') and path.endswith('"'):
        return _unescape_c_quoted(path[1:-1])
    return path


def subtract_baseline(paths: Iterable[str], baseline: Iterable[str]) -> List[str]:
    """Return the ``paths`` a dirty-tree ``baseline`` does *not* already cover.

    A baseline entry ending in ``/`` is a *directory*, and it covers everything
    under it. That is not a convenience: ``git status --porcelain`` reports an
    untracked directory as a single ``?? some_dir/`` line, so every baseline
    ever recorded names directories alongside files, and a plain set difference
    subtracts none of them — no file path equals ``"plans/"``. Measured
    2026-09-16: a run whose baseline was the four directories ``.claude/``,
    ``.multi-llm/``, ``plans/``, ``saved/`` subtracted nothing and tracked all
    1 511 untracked files in the repo as its own changes.

    Order is preserved so a caller's list stays in the order it discovered
    things in.
    """
    exact = set()
    prefixes = []
    for entry in baseline:
        if not entry:
            continue
        exact.add(entry)
        bare = _unquote_porcelain_path(entry)
        if bare.endswith("/"):
            # The directory itself, with and without the separator, plus
            # everything beneath it.
            exact.add(bare)
            exact.add(bare.rstrip("/"))
            prefixes.append(bare)
        else:
            exact.add(bare)
    kept = []
    for path in paths:
        if path in exact:
            continue
        bare_path = _unquote_porcelain_path(path)
        if bare_path in exact:
            continue
        if any(bare_path.startswith(prefix) for prefix in prefixes):
            continue
        kept.append(path)
    return kept


def baseline_covers(path: str, baseline: Iterable[str]) -> bool:
    """True when ``baseline`` already accounts for ``path`` (see above)."""
    return not subtract_baseline([path], baseline)


def get_modified_files() -> List[str]:
    """Get list of modified and untracked files.

    Deliberately plain ``--porcelain``, so an untracked *directory* stays one
    ``?? some_dir/`` line instead of expanding to every file beneath it. A
    file-granular census cannot tell an edit inside an untracked tree from the
    rest of that tree anyway — an untracked file has no "modified" state in git
    — so the expansion bought nothing and cost a great deal: it made the census
    disagree with the compact baselines already stored in ``state.json`` (see
    ``subtract_baseline``, which is what reconciles the two), and in a repo with
    1 511 untracked files it wrote all of them into ``tracked_files``. The
    authoritative signal for what a run changed is the write executor's verified
    ``files_touched``, threaded to ``finalize_tracking`` as ``--touched``.
    """
    stdout, _, _ = _run_git("status", "--porcelain")
    files = []
    # NEVER strip leading whitespace off this output: a worktree-only change is
    # reported as `" M path"`, so `stdout.strip()` would eat the first line's
    # status column and `line[3:]` would then cut a character off the filename.
    # Only the trailing newline is dropped, by filtering short/blank lines.
    for line in stdout.split("\n"):
        # A real entry is `XY <path>`: two status columns, a space, a path.
        if len(line) < 4:
            continue
        status = line[:2]
        if not status.strip():
            continue
        # Unquote here and not only in `subtract_baseline`: the census is what
        # gets STORED (in `tracked_files`, and handed to every consumer that
        # opens the file), so a path with a space has to leave this function as
        # the path it really is.
        filename = _unquote_porcelain_path(_porcelain_destination(line[3:]))
        if filename:
            files.append(filename)
    return files


def list_untracked_files(directory: str) -> List[str]:
    """List the untracked files git reports under ``directory``.

    The counterpart of the compact census above: `get_modified_files` collapses
    an untracked directory to one ``dir/`` entry, which is what lets a stored
    baseline subtract a whole pre-existing tree cheaply — but a directory the
    run itself CREATED survives that subtraction, and a directory path is not
    something a diff or a file read can act on. Expanding just that entry
    recovers the files without re-censusing the whole repo.

    ``-z`` so the paths come back raw, with no C-quoting to undo. Best-effort:
    a git failure (or a directory that has since gone) returns nothing and the
    caller keeps whatever it had.
    """
    stdout, _, rc = _run_git(
        "ls-files", "--others", "--exclude-standard", "-z", "--", directory,
        check=False,
    )
    if rc != 0:
        return []
    return [path for path in stdout.split("\0") if path]

def paths_in_commit(
    ref: str, paths: Iterable[str], *, cwd: Optional[str] = None,
) -> Optional[Set[str]]:
    """The subset of repo-root-relative *paths* present in *ref*'s tree.

    ``None`` when *ref* does not resolve to a tree (an unborn ``HEAD``, a
    pruned ``head_before_implement``), so the caller can tell "absent from
    the tree" from "no tree to ask". A commit's tree, or a tree itself: the
    empty tree a repository with no commit records as its base
    (:func:`head_or_empty_tree`) holds no path, so every file reads as new
    rather than as unknown. One ``git cat-file --batch-check`` over
    ``<sha>:<path>`` lines: exact paths, never pathspec patterns (a ``*`` in a
    filename is a filename). A path holding a newline cannot be asked and is
    reported absent.
    """
    answers = _batch_check_in_commit(ref, paths, "%(objecttype)", cwd=cwd, allow_tree=True)
    if answers is None:
        return None
    return {path for path, _answer in answers}


def _batch_check_in_commit(
    ref: str, paths: Iterable[str], fmt: str, *, cwd: Optional[str] = None,
    allow_tree: bool = False,
) -> Optional[List[Tuple[str, str]]]:
    """``[(path, answer)]`` for each of *paths* present in *ref*'s tree, where
    *answer* is ``git cat-file --batch-check=<fmt>``'s line for it.

    The one reader behind :func:`paths_in_commit` and :func:`blobs_in_commit`,
    so both use one call over ``<sha>:<path>`` lines, exact paths, and report a
    path holding a newline (which cannot be asked) absent. ``None`` when the
    batch fails or *ref* cannot resolve: to a commit for guard expectations,
    or to any tree when ``allow_tree`` lets path classification accept an
    unborn repository's empty-tree base.

    Each path is encoded with ``surrogateescape``, the inverse of
    :func:`_run_git_for_paths`'s decode (and of how ``subprocess`` encodes a
    path argument), so a file name that is not valid UTF-8 reaches git as the
    very bytes that name it; a lossy encode would ask git about a ``?`` name
    and read a file present at *ref* as absent. A string no bytes can carry
    (a lone surrogate outside that escape range) names no file git could
    hold, so it is reported absent too.
    """
    candidates: List[Tuple[str, bytes]] = []
    for path in paths:
        if not path or "\n" in path:
            continue
        try:
            candidates.append((path, path.encode("utf-8", "surrogateescape")))
        except UnicodeEncodeError:
            continue
    kind = "tree" if allow_tree else "commit"
    stdout, _, rc = _run_git(
        "rev-parse", "--verify", "--quiet", f"{ref}^{{{kind}}}",
        check=False, cwd=cwd,
    )
    sha = stdout.strip()
    if rc != 0 or not sha:
        return None
    if not candidates:
        return []
    where: Dict[str, str] = {"cwd": cwd} if cwd is not None else {}
    prefix = f"{sha}:".encode("ascii")
    result = subprocess.run(
        git_argv("cat-file", f"--batch-check={fmt}", cwd=cwd),
        input=b"".join(prefix + raw + b"\n" for _path, raw in candidates),
        capture_output=True, **where,
    )
    if result.returncode != 0:
        return None
    answers = result.stdout.splitlines()
    if len(answers) != len(candidates):
        return None
    return [
        (path, answer.decode("utf-8", errors="replace"))
        for (path, _raw), answer in zip(candidates, answers)
        if not answer.endswith(b" missing")
    ]


def blobs_in_commit(
    ref: str, paths: Iterable[str], *, cwd: Optional[str] = None,
) -> Optional[Dict[str, str]]:
    """``{path: object id}`` for each of *paths* present in *ref*'s tree.

    The sibling of :func:`paths_in_commit` the apply guard saves its ``head``
    expectations from: one ``git cat-file
    --batch-check=%(objectname)`` call over the same ``<sha>:<path>`` lines,
    under the same path rules, so its keys equal that function's set for a
    commit. A non-commit ref is ``None`` here; ``paths_in_commit`` also accepts
    bare trees for an unborn repository's base. A path missing from the dict is
    absent at *ref*. Each id is what ``git rev-parse <ref>:<path>`` prints: a
    blob's id for a file or symlink, the tree's for a directory.
    """
    answers = _batch_check_in_commit(ref, paths, "%(objectname)", cwd=cwd)
    if answers is None:
        return None
    return {path: answer.strip() for path, answer in answers}


def read_at_commit(
    ref: str, path: str, *, cwd: Optional[str] = None,
) -> Optional[bytes]:
    """The bytes of *path* as commit *ref* holds it; ``None`` when absent.

    ``git cat-file blob <ref>:<path>``: the blob exactly as stored, with no
    textconv, filter or eol conversion, which is what ``git show <ref>:<path>``
    prints for a file. *path* goes through :func:`git_path` first (relative to
    the repository at *cwd*), so a Windows ``pkg\\mod.py`` or an absolute path
    reads ``pkg/mod.py``. ``None`` for a path absent at *ref*, a directory or submodule
    there, a *ref* that does not resolve, and a failed call: Python's reads at
    ``head`` treat each as "nothing to show", never as an error.
    """
    if not path or "\n" in path:
        return None
    name = git_path(path, cwd=cwd)
    where: Dict[str, str] = {"cwd": cwd} if cwd is not None else {}
    try:
        result = subprocess.run(
            git_argv("cat-file", "blob", f"{ref}:{name}", cwd=cwd),
            capture_output=True, stdin=subprocess.DEVNULL, **where,
        )
    except (OSError, ValueError):
        return None
    if result.returncode != 0:
        return None
    return result.stdout


#: The empty-tree id per repository (keyed by the realpath of the cwd asked).
_EMPTY_TREE_IDS: Dict[str, str] = {}


def empty_tree_id(cwd: Optional[str] = None) -> str:
    """The repository's empty-tree id, computed, never written as a literal.

    ``git hash-object -t tree --stdin`` on empty input: ``4b825dc…`` in a
    SHA-1 repository, its own id in a SHA-256 one. Git knows this tree
    without storing it, but only by its full id, so the id is never
    abbreviated. Raises :class:`GitError` outside a repository.
    """
    key = os.path.realpath(cwd or os.getcwd())
    cached = _EMPTY_TREE_IDS.get(key)
    if cached:
        return cached
    where: Dict[str, str] = {"cwd": cwd} if cwd is not None else {}
    result = subprocess.run(
        git_argv("hash-object", "-t", "tree", "--stdin", cwd=cwd),
        input="", capture_output=True, text=True, encoding="utf-8",
        errors="replace", **where,
    )
    tree = result.stdout.strip()
    if result.returncode != 0 or not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", tree):
        raise GitError(f"git hash-object -t tree failed: {result.stderr.strip()}")
    _EMPTY_TREE_IDS[key] = tree
    return tree


def is_empty_tree_id(ref: Optional[str], cwd: Optional[str] = None) -> bool:
    """True when *ref* is exactly the repository's full empty-tree id."""
    if not ref:
        return False
    try:
        return ref == empty_tree_id(cwd)
    except GitError:
        return False


def git_path(
    path: Union[str, Path],
    repo_root: Optional[Union[str, Path]] = None,
    *,
    cwd: Optional[str] = None,
) -> str:
    """*path* as git names it: repository-relative, with forward slashes.

    An absolute path is made relative to *repo_root* (when ``None``, the root
    of the repository at *cwd*, itself the process's cwd by default; looked
    up only for an absolute path, so a relative one costs no git call). Then
    ``as_posix()``: on Windows ``\\`` is a separator (``PureWindowsPath``), on
    POSIX it is a legal name character and is left alone (``PurePosixPath``).
    A leading ``./`` is dropped. Paths outside the root are returned as given,
    made posix, so the caller's own lookup fails on them rather than this
    helper guessing.
    """

    text = str(path)
    pure = PureWindowsPath(text) if os.name == "nt" else PurePosixPath(text)
    if pure.is_absolute():
        root = repo_root
        if root is None:
            root = get_project_root_from_dir(cwd or os.getcwd())
        if root:
            try:
                # The directories are resolved, the last component is not: a
                # symlink the repository tracks is named by its own path, never
                # by its target's, and a root reached through a symlinked
                # directory (macOS's temp dir) still matches its real spelling.
                head, tail = os.path.split(text)
                real = os.path.join(os.path.realpath(head), tail)
                real_root = os.path.realpath(str(root))
                relative = os.path.relpath(real, real_root)
                if relative != os.pardir and not relative.startswith(os.pardir + os.sep):
                    pure = (PureWindowsPath(relative) if os.name == "nt"
                            else PurePosixPath(relative))
            except ValueError:  # another drive on Windows
                pass
    posix = pure.as_posix()
    while posix.startswith("./"):
        posix = posix[2:]
    return posix


def paths_changed_since(
    head: str, paths: Iterable[str], *, cwd: Optional[str] = None,
) -> Set[str]:
    """The subset of *paths* whose disk entry is not what commit *head* holds.

    THE change test of a commit review: the drift check runs it over the
    scope files and the apply guard over the fix files, so the drift list
    and the apply's skips never disagree about a file. It compares as git sees a file —
    the content after the path's clean filters (eol, ``ident``, LFS), the mode
    and the kind — and hashes nothing itself, so a CRLF checkout of an
    unchanged file under ``* text=auto`` matches. Three reads, each one call
    over all the paths, can mark a path changed:

    1. ``git diff --name-only --no-renames -z <head> -- <paths>``: later
       commits, staged and unstaged edits, a mode-only change, a changed kind,
       a deletion on disk. ``--no-renames`` because ``--name-only`` names a
       detected rename by its new path only, so a scope file moved onto
       another scope path the range deleted would go unlisted; without
       pairing every path is listed under its own name.
    2. :func:`paths_in_commit` plus an ``lstat`` of each path: a path absent
       at *head* but present on disk in any form (untracked, ignored, added
       with ``git add -N``, a directory) is changed, and so is any path whose
       disk entry is neither a regular file nor a symlink (a directory, a
       submodule, a socket). A path absent at *head* and absent on disk
       matches, so a fix may restore a deleted file or create a new one.
    3. ``git ls-files -v -z -- <paths>``: an entry tagged ``S``
       (skip-worktree) or with a lowercase tag (assume-unchanged), whose disk
       copy ``git diff`` never reads.

    *paths* are repository-relative and *cwd* is the repository root (the
    process's cwd when ``None``). Each path is put in git's form
    (:func:`git_path`) before it is asked about, and the result holds the
    strings as given. A read that fails marks every path changed, with one
    warning on stderr: the guard must never let a fix through on a question
    git did not answer. A path holding a newline cannot be asked about at
    *head*, so it is changed whenever it exists on disk.
    """
    given = [path for path in dict.fromkeys(paths) if path]
    if not given:
        return set()
    by_name: Dict[str, List[str]] = {}
    for path in given:
        by_name.setdefault(git_path(path, cwd=cwd), []).append(path)
    names = list(by_name)
    changed_names: Set[str] = set()

    def fail(what: str, detail: str) -> Set[str]:
        print(
            f"Warning: {what} failed ({detail}); every one of the {len(given)} "
            f"path(s) is treated as changed since {head[:12]}",
            file=sys.stderr,
        )
        return set(given)

    # 1. The drift primitive.
    for chunk in _argv_chunks(names):
        stdout, stderr, rc = _run_git_for_paths(
            "--literal-pathspecs", "diff", "--name-only", "--no-renames", "-z", head,
            "--", *chunk, cwd=cwd,
        )
        if rc != 0:
            return fail(f"git diff --name-only {head[:12]}", _first_line(stderr, rc))
        changed_names.update(name for name in stdout.split("\0") if name in by_name)

    # 2. Presence at `head` against the disk entry's kind.
    try:
        present = paths_in_commit(head, names, cwd=cwd)
    except (OSError, ValueError) as exc:
        return fail(f"git cat-file at {head[:12]}", f"git could not run ({exc})")
    if present is None:
        return fail(f"git cat-file at {head[:12]}", "no such commit, or the call failed")
    base = cwd if cwd is not None else os.getcwd()
    for name in names:
        try:
            info = os.lstat(os.path.join(base, name))
        except (FileNotFoundError, NotADirectoryError):
            continue  # absent on disk: matches when absent at head too
        except OSError:
            changed_names.add(name)  # cannot tell what is there: not head's
            continue
        if name not in present:
            changed_names.add(name)
        elif not (stat.S_ISREG(info.st_mode) or stat.S_ISLNK(info.st_mode)):
            changed_names.add(name)

    # 3. Index entries whose disk copy git diff never reads.
    for chunk in _argv_chunks(names):
        stdout, stderr, rc = _run_git_for_paths(
            "--literal-pathspecs", "ls-files", "-v", "-z", "--", *chunk, cwd=cwd,
        )
        if rc != 0:
            return fail("git ls-files -v", _first_line(stderr, rc))
        for record in stdout.split("\0"):
            tag, _, name = record.partition(" ")
            if name in by_name and (tag == "S" or (tag.isalpha() and tag.islower())):
                changed_names.add(name)

    return {path for name in changed_names for path in by_name[name]}


#: The argv budget of one path-carrying git call: far under Linux's limits and
#: under Windows' 32 767-character command line, which a few hundred long
#: paths would otherwise pass.
_ARGV_CHUNK_CHARS = 24000
#: Paths per ``git diff --numstat`` call, far under any argv limit even for
#: long paths (a 1 040-path scope is three calls).
_NUMSTAT_CHUNK = 500


def _argv_chunks(names: Sequence[str]) -> Iterator[List[str]]:
    """*names* in runs of at most :data:`_NUMSTAT_CHUNK` paths and
    :data:`_ARGV_CHUNK_CHARS` characters: one run, so one git call, for any
    scope a review normally has; more only where one call could not carry it."""
    chunk: List[str] = []
    size = 0
    for name in names:
        cost = len(name) + 3
        if chunk and (len(chunk) >= _NUMSTAT_CHUNK or size + cost > _ARGV_CHUNK_CHARS):
            yield chunk
            chunk, size = [], 0
        chunk.append(name)
        size += cost
    if chunk:
        yield chunk


def _first_line(stderr: str, rc: int) -> str:
    lines = (stderr or "").strip().splitlines()
    return lines[0] if lines else f"exit {rc}"


def _run_git_for_paths(*args: str, cwd: Optional[str] = None) -> Tuple[str, str, int]:
    """:func:`_run_git` for a call that prints paths: stdout is decoded with
    ``surrogateescape``, the inverse of how ``subprocess`` encodes a path
    argument, so a file name that is not valid UTF-8 comes back as the very
    string that names it (``_run_git``'s lossy decode would hide it from a
    membership test). A git that will not start is ``("", why, -1)``,
    never a raise."""
    try:
        result = _run_git_process(
            args, cwd=cwd, capture_output=True, stdin=subprocess.DEVNULL,
        )
    except (OSError, ValueError) as exc:
        return "", f"git could not run ({exc})", -1
    return (
        result.stdout.decode("utf-8", errors="surrogateescape"),
        result.stderr.decode("utf-8", errors="replace"),
        result.returncode,
    )


#: The two runners' public names, for other modules. The underscore spellings
#: stay for this module's own calls and the tests that patch them.
run_git = _run_git
run_git_for_paths = _run_git_for_paths


def rename_map(
    base_ref: str, head: str, *, cwd: Optional[str] = None,
) -> Optional[Dict[str, str]]:
    """``{old path: new path}`` for every rename between *base_ref* and *head*.

    One ``git diff -M --name-status -z <base> <head>``, not limited to any
    scope, so both sides of a rename are seen. It labels a path absent at
    *head* (``renamed to <new>`` rather than ``deleted``) and nothing else:
    the scope stays the ``--name-only`` list. ``None`` when the call fails, so the caller
    falls back to ``absent at <head7>``. An empty-tree *base_ref* (a root
    range) has no renames.
    """
    stdout, _, rc = _run_git_for_paths(
        *attribute_source_args(head), "diff", "-M", "--name-status", "-z", base_ref, head, cwd=cwd,
    )
    if rc != 0:
        return None
    fields = stdout.split("\0")
    renames: Dict[str, str] = {}
    index = 0
    while index < len(fields):
        status = fields[index]
        if not status:
            index += 1
            continue
        if status[0] in ("R", "C"):
            if index + 2 >= len(fields):
                break
            if status[0] == "R":
                renames[fields[index + 1]] = fields[index + 2]
            index += 3
        else:
            index += 2
    return renames


def deleting_commit(
    base: Optional[str], head: str, path: str, *, cwd: Optional[str] = None,
) -> Optional[str]:
    """The commit in ``<base>..<head>`` that deleted *path*, or ``None``.

    ``git log -1 --diff-filter=D --format=%H <base>..<head> -- <path>`` (the
    newest such commit), for the fix prompt's ``git show <deleting>^:<path>``
    on a file absent at ``head``. ``--no-renames`` so a path renamed away
    counts as deleted by the commit that moved it. A root range (*base*
    ``None``, or the empty-tree id) has no ``<base>..`` side. ``None`` when no
    range commit deleted the path, or when the call fails.
    """
    if not path or "\n" in path:
        return None
    if base is None or is_empty_tree_id(base, cwd):
        revisions = head
    else:
        revisions = f"{base}..{head}"
    stdout, _, rc = _run_git_for_paths(
        "--literal-pathspecs", "log", "-1", "--no-renames", "--diff-filter=D",
        "--format=%H", revisions, "--", git_path(path, cwd=cwd), cwd=cwd,
    )
    sha = stdout.strip()
    if rc != 0 or not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", sha):
        return None
    return sha


def ignored_paths(paths: Iterable[str], *, cwd: Optional[str] = None) -> Set[str]:
    """The subset of ``paths`` git ignores, as the strings given.

    ``git check-ignore`` without ``--no-index``, so a *tracked* file that a
    pattern happens to match is not reported: only untracked-and-ignored paths
    (transcripts, build output, caches) come back. Best-effort: outside a
    repository, or when git fails, nothing is ignored, because dropping a path
    on a guess is worse than keeping it. ``-z`` both ways so no path is C-quoted.

    A path outside the repository is never asked about: ``check-ignore`` exits
    128 ("fatal: … is outside repository") for the whole batch on one such
    path, which used to answer "nothing is ignored" for every path beside it
    (adversarial review, 2026-10-02; ``finalize_tracking --touched`` can carry
    one). Such a path is not ignored — it is not the repository's at all.
    """
    candidates = [path for path in paths if path]
    if not candidates:
        return set()
    where: Dict[str, str] = {"cwd": cwd} if cwd is not None else {}
    stdout, _, rc = _run_git("rev-parse", "--show-toplevel", check=False, cwd=cwd)
    if rc != 0:
        return set()
    toplevel = os.path.realpath(stdout.strip())
    base = os.path.realpath(cwd) if cwd is not None else os.path.realpath(os.getcwd())
    inside = [
        path for path in candidates
        if _under_toplevel(os.path.join(base, path), toplevel)
    ]
    if not inside:
        return set()
    try:
        result = subprocess.run(
            git_argv("check-ignore", "-z", "--stdin", cwd=cwd),
            input="\0".join(inside) + "\0",
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            **where,
        )
    except OSError:
        return set()
    if result.returncode not in (0, 1):  # 128: not a repository, bad path
        return set()
    return {path for path in result.stdout.split("\0") if path}


def _under_toplevel(path: str, toplevel: str) -> bool:
    """Whether ``path`` (absolute or cwd-joined) lies at or under ``toplevel``.

    Lexical after ``normpath`` on the path and ``realpath`` on the root: the
    path need not exist (a deleted file is still a candidate) and a symlink
    inside the repo pointing out is ``check-ignore``'s own question to answer.
    """
    resolved = os.path.normpath(path)
    return resolved == toplevel or resolved.startswith(toplevel.rstrip(os.sep) + os.sep)


def get_staged_files() -> List[str]:
    """Get list of currently staged files."""
    stdout, _, _ = _run_git("diff", "--cached", "--name-only")
    # Like porcelain, --name-only C-quotes non-ASCII and control characters.
    # Keep the same decoded paths as get_modified_files so their union cannot
    # contain a second, nonexistent quoted spelling of a staged file.
    return [_unquote_porcelain_path(f) for f in stdout.split("\n") if f]

def stage_files(files: List[str]) -> None:
    """Stage specific files."""
    if files:
        _run_git("add", "--", *files)

def unstage_files(files: List[str]) -> None:
    """Unstage specific files."""
    if files:
        _run_git("reset", "HEAD", "--", *files)


@contextmanager
def intent_to_add_untracked(
    file_paths: List[str], *, cwd: Optional[str] = None
) -> Iterator[List[str]]:
    """Make untracked files visible to `git diff` without touching the real index.

    `git diff` (all variants -- `git diff`, `git diff HEAD`, `git diff A..B`) silently
    ignores fully-untracked files. For code review flows that rely on git diff to
    surface implementation changes, this means new files never show up. Marking them
    with `git add -N` creates an empty index entry so diffs treat them as full-file
    additions without staging any content.

    The mark is made in a **private copy of the index**, exported as
    ``GIT_INDEX_FILE`` for the duration of the block. Every git call in this
    process, and every reviewer subprocess that inherits the environment, reads
    the copy and sees the files as additions; the user's own ``.git/index`` is
    never written, so there is nothing to undo, an interrupted run cannot leave
    ``intent-to-add`` entries behind, and a ``git status`` the user runs in
    another terminal meanwhile shows a clean tree. On exit the variable is
    restored (or removed) and the copy deleted. Files that were already in the
    index (staged, or already intent-to-add by the user) are never touched.

    Args:
        file_paths: Candidate files to consider. Files not currently untracked are
            skipped. A file listed here but missing from the working tree is also
            skipped.
        cwd: Where git runs, and so what ``file_paths`` are relative to. The
            review scope is repository-root-relative, so a caller holding one
            passes the repository root: from a subdirectory, the process's cwd
            would read every path relative to that subdirectory and mark
            nothing.

    Yields:
        The list of files this context manager actually marked (may be empty).
    """
    touched: List[str] = []
    private_index: Optional[str] = None
    had_index_var = "GIT_INDEX_FILE" in os.environ
    previous_index_var = os.environ.get("GIT_INDEX_FILE")
    if file_paths:
        try:
            stdout, _, rc = _run_git(
                "ls-files", "--others", "--exclude-standard", "--", *file_paths,
                check=False, cwd=cwd,
            )
            if rc == 0:
                touched = [line for line in stdout.splitlines() if line.strip()]
        except Exception as exc:
            print(
                f"Warning: could not list untracked files for intent-to-add: {exc}",
                file=sys.stderr,
            )
            touched = []

        if touched:
            try:
                private_index = _private_index_copy(cwd)
                os.environ["GIT_INDEX_FILE"] = private_index
                _run_git("add", "-N", "--", *touched, cwd=cwd)
                print(
                    f"Marked {len(touched)} untracked file(s) as intent-to-add "
                    f"in a private index copy so review can see their contents"
                )
            except (GitError, OSError) as exc:
                _restore_index_var(had_index_var, previous_index_var)
                _discard_private_index(private_index)
                private_index = None
                print(
                    f"Warning: could not mark untracked files intent-to-add "
                    f"({exc}); untracked files may be invisible to reviewers",
                    file=sys.stderr,
                )
                touched = []
    try:
        yield touched
    finally:
        if private_index is not None:
            _restore_index_var(had_index_var, previous_index_var)
            _discard_private_index(private_index)


def _private_index_copy(cwd: Optional[str]) -> str:
    """Copy the index git would use into a file of its own; return its path.

    Source: ``$GIT_INDEX_FILE`` if the caller already redirected git, else the
    worktree's own index (``git rev-parse --git-path index``, which is right for
    linked worktrees). The copy sits beside it inside the git directory, so a
    reviewer sandbox that can read the repository can read it; a git directory
    that refuses the write falls back to the system temp dir. A repository with
    no index yet (nothing ever staged) copies nothing: git creates the file.
    """
    source = os.environ.get("GIT_INDEX_FILE")
    if not source:
        stdout, _, _ = _run_git("rev-parse", "--git-path", "index", cwd=cwd)
        source = stdout.strip()
    # Either value can be relative, and both are relative to where git runs
    # (`cwd`), not to this process's own directory: a git hook exports
    # `GIT_INDEX_FILE=.git/index`, and resolving that against the process cwd
    # pointed the copy at a directory that did not exist, so `git add -N`
    # failed on its lock file and no untracked file reached the reviewers
    # (adversarial review, 2026-10-02).
    if not os.path.isabs(source):
        source = os.path.join(cwd or os.getcwd(), source)
    source = os.path.abspath(source)
    _sweep_dead_index_copies(os.path.dirname(source))
    name = f"multi-llm-index.{os.getpid()}.{time.monotonic_ns()}"
    target = os.path.join(os.path.dirname(source), name)
    try:
        if os.path.exists(source):
            _copy_index_keeping_its_time(source, target)
    except OSError:
        descriptor, target = tempfile.mkstemp(prefix="multi-llm-index.")
        os.close(descriptor)
        if os.path.exists(source):
            _copy_index_keeping_its_time(source, target)
        else:
            os.unlink(target)
    return target


def _copy_index_keeping_its_time(source: str, target: str) -> None:
    """Copy the index at *source* to *target*, with *source*'s timestamps.

    git trusts an entry's cached stat data (size, mtime, inode) to say a
    tracked file is unchanged, except when the entry is not older than the
    index file itself: such a "racily clean" entry may have been edited in the
    same second it was cached, so git compares its contents instead. A copy
    stamped with the time it was made is newer than every entry, which turns
    that check off: an edit of the same size made within the cached entry's
    second (review-code's fixture rewrites ``return 1`` as ``return 2`` at
    once) matched its stale stat data and dropped out of every diff the review
    ran on the copy (commit review of 5025463..fb0634f, 2026-10-08). The copy
    is read from one open file, so the time it carries is that file's even
    if git replaces the index meanwhile. A copy that fails halfway is removed.
    """
    try:
        with open(source, "rb") as reader:
            stamp = os.fstat(reader.fileno())
            with open(target, "wb") as writer:
                shutil.copyfileobj(reader, writer)
        os.utime(target, ns=(stamp.st_atime_ns, stamp.st_mtime_ns))
    except OSError:
        try:
            os.unlink(target)
        except OSError:
            pass
        raise


#: The private index copies, as :func:`_private_index_copy` names them:
#: ``multi-llm-index.<pid>.<monotonic ns>`` plus git's own ``.lock`` sibling.
_INDEX_COPY_NAME = re.compile(r"^multi-llm-index\.(\d+)\.\d+(\.lock)?$")


def _sweep_dead_index_copies(git_dir: str) -> None:
    """Remove the index copies a killed run left behind in *git_dir*.

    The ``finally`` in :func:`intent_to_add_untracked` cannot run under
    SIGKILL, so a hard-killed review leaves ``multi-llm-index.<pid>.<ns>`` (and
    its ``.lock``) in the git directory forever: harmless to git, which never
    reads them, but they accumulate (adversarial review, 2026-10-02). A copy
    is swept only when the pid in its name is not alive; this process's own
    copies (a nested block) and another live run's are left alone. Best
    effort: a directory that cannot be listed, or a file that cannot be
    removed, changes nothing about the run.
    """
    # Imported here: the git family imports only the standard library while it initialises
    # (tests/test_git_utils_moved_names.py).
    from .process_control import process_alive
    try:
        names = os.listdir(git_dir)
    except OSError:
        return
    for name in names:
        match = _INDEX_COPY_NAME.match(name)
        if not match:
            continue
        pid = int(match.group(1))
        if pid == os.getpid() or process_alive(pid):
            continue
        try:
            os.unlink(os.path.join(git_dir, name))
        except OSError:
            pass


def _restore_index_var(had: bool, previous: Optional[str]) -> None:
    if had and previous is not None:
        os.environ["GIT_INDEX_FILE"] = previous
    else:
        os.environ.pop("GIT_INDEX_FILE", None)


def _discard_private_index(path: Optional[str]) -> None:
    if not path:
        return
    for leftover in (path, f"{path}.lock"):
        try:
            os.unlink(leftover)
        except FileNotFoundError:
            pass
        except OSError as exc:
            print(
                f"Warning: could not remove the private index copy {leftover}: {exc}",
                file=sys.stderr,
            )


def get_staged_diff() -> str:
    """Get diff of all staged changes."""
    stdout, _, _ = _run_git("diff", "--cached")
    return stdout

def get_file_diff(file_path: str, base_ref: Optional[str] = None) -> str:
    """Get diff for a specific file."""
    if base_ref:
        stdout, _, _ = _run_git("diff", base_ref, "--", file_path)
    else:
        stdout, _, _ = _run_git("diff", "--", file_path)
    return stdout

def get_current_head() -> str:
    """Get current HEAD commit hash.

    Strict: raises :class:`GitError` when HEAD names no commit, which includes
    a repository whose first commit has not been made yet. A caller that wants
    a *diff base* — "the tree as of now", which exists in every repository —
    reads :func:`head_or_empty_tree` instead.
    """
    stdout, _, _ = _run_git("rev-parse", "HEAD")
    return stdout.strip()


# ---------------------------------------------------------------------------
# A repository with no commit (an unborn HEAD)
# ---------------------------------------------------------------------------

#: git's empty tree in a SHA-1 repository (``git hash-object -t tree
#: /dev/null``). A fast spelling check for :func:`is_empty_tree`; actual diff
#: bases come from :func:`empty_tree_id`, which also supports SHA-256 repositories.
EMPTY_TREE_SHA1 = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"


def head_is_unborn(cwd: Optional[str] = None) -> bool:
    """Whether HEAD names a branch that has no commit yet.

    A plain ``git init`` before its first commit, and ``git checkout
    --orphan`` in a repository that has history elsewhere: ``rev-parse
    --verify HEAD`` fails while ``symbolic-ref HEAD`` still names the branch.
    A first-time user's project is exactly this (a new project, ``git init``,
    no commit), and every mode that opens ``state.json`` used to exit 1 on it
    with ``GitError: git rev-parse HEAD failed``, because the new state
    recorded ``head_at_start`` through :func:`get_current_head`. Anything
    else that fails the first
    check — not a repository, a detached HEAD whose object is gone — is not
    unborn, and the caller's own git call reports it.
    """
    _, _, code = _run_git("rev-parse", "--verify", "--quiet", "HEAD", check=False, cwd=cwd)
    if code == 0:
        return False
    _, _, code = _run_git("symbolic-ref", "--quiet", "HEAD", check=False, cwd=cwd)
    return code == 0


def is_empty_tree(ref: Optional[str], cwd: Optional[str] = None) -> bool:
    """Whether *ref* is spelled as the empty tree's id (either object format).

    git is asked only for a 64-character ref, the one shape a SHA-256
    repository's empty tree can have, so ``HEAD~1`` or a commit id costs no
    spawn.
    """
    if not ref:
        return False
    if ref == EMPTY_TREE_SHA1:
        return True
    return len(ref) == 64 and is_empty_tree_id(ref, cwd)


def head_or_empty_tree(cwd: Optional[str] = None) -> str:
    """HEAD's commit, or the empty tree's id when HEAD is unborn.

    The diff base "as of now": what ``state.json`` records as ``head_at_start``
    and ``head_before_implement``, which code review and apply-code-fixes later
    diff against and :func:`paths_in_commit` reads a tree from. Before the first
    commit nothing is committed, so the honest base is the empty tree and every
    file reads as new — never a refusal, and never an invented commit. Raises
    :class:`GitError` as :func:`get_current_head` does for every other HEAD
    that names no commit (outside a repository, a broken ref).
    """
    stdout, _, code = _run_git(
        "rev-parse", "--verify", "--quiet", "HEAD^{commit}", check=False, cwd=cwd,
    )
    if code == 0 and stdout.strip():
        return stdout.strip()
    if head_is_unborn(cwd):
        return empty_tree_id(cwd)
    stdout, _, _ = _run_git("rev-parse", "HEAD", cwd=cwd)
    return stdout.strip()

def get_branch_name() -> Optional[str]:
    """Get current branch name, or None if detached HEAD."""
    stdout, _, code = _run_git("symbolic-ref", "--short", "HEAD", check=False)
    if code == 0:
        return stdout.strip()
    return None

def is_clean_working_tree() -> bool:
    """Check if working tree is clean (no uncommitted changes)."""
    _, _, code = _run_git("diff", "--quiet", check=False)
    if code != 0:
        return False
    _, _, code = _run_git("diff", "--cached", "--quiet", check=False)
    return code == 0

def get_diff_since_ref(base_ref: str) -> str:
    """Get diff of all changes since a reference commit."""
    stdout, _, _ = _run_git("diff", base_ref)
    return stdout

def get_files_changed_since_ref(
    base_ref: str, head_ref: Optional[str] = None, *, cwd: Optional[str] = None,
) -> List[str]:
    """Get list of files changed since a reference commit.

    ``head_ref=None`` is ``git diff --name-only <base>``: the base against the
    working tree, as always. With a head it is ``git diff --name-only -z <base>
    <head>``, the two commits alone, whatever the working tree holds. Git's default
    rename detection is kept on
    purpose: a rename is listed under its new path only, which is the path the
    scope reviews. ``-z`` there hands back every path raw (decoded as
    :func:`_numstat_counts` decodes them), so a non-ASCII name is not C-quoted
    into a path no later diff matches. ``base_ref`` may be the empty-tree id
    (a root range), which lists every file at ``head``. Raises
    :class:`GitError` when git fails, either way.
    """
    where: Dict[str, str] = {"cwd": cwd} if cwd is not None else {}
    if head_ref is not None:
        stdout, stderr, rc = _run_git_for_paths(
            *attribute_source_args(head_ref), "diff", "--name-only", "-z", base_ref, head_ref, cwd=cwd,
        )
        if rc != 0:
            raise GitError(
                f"git diff --name-only -z {base_ref} {head_ref} failed: {stderr}"
            )
        return [f for f in stdout.split("\0") if f]
    stdout, _, _ = _run_git("diff", "--name-only", base_ref, **where)
    # Same rule as get_staged_files: one unquoted path per line, so the only
    # thing safe to drop is the line separator.
    return [f for f in stdout.split("\n") if f]


def validate_git_ref(ref: str) -> str:
    """Validate a git ref using git rev-parse --verify.

    If the ref is invalid, falls back to HEAD~1. If HEAD~1 is also invalid
    (or the original ref was already HEAD~1), returns an empty string. Before
    the first commit (:func:`head_is_unborn`) an invalid ref falls back to the
    empty tree instead, the one base that exists there.

    Args:
        ref: The git ref to validate (e.g., a commit hash, branch name, HEAD~1).

    Returns:
        The validated ref if valid, the empty tree's id when HEAD is unborn,
        'HEAD~1' as fallback, or empty string if both the ref and HEAD~1 are
        invalid.
    """
    if not ref:
        return ""

    try:
        subprocess.run(
            git_argv("rev-parse", "--verify", ref),
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        return ref
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    # Before the first commit no ref resolves, `HEAD~1` least of all, and
    # the empty base used to leave every diff empty. The honest base is the
    # empty tree: nothing is committed, so every file is new.
    try:
        unborn = head_is_unborn()
    except OSError:
        unborn = False
    if unborn:
        tree = empty_tree_id()
        print(
            f"Warning: git ref '{ref}' does not resolve and HEAD has no commit "
            f"yet; diffing against the empty tree ({tree}), so every file is new",
            file=sys.stderr,
        )
        return tree

    print(
        f"Warning: git ref '{ref}' is invalid, falling back to HEAD~1",
        file=sys.stderr,
    )

    # If the ref was already HEAD~1, don't redundantly retry it
    if ref == "HEAD~1":
        print(
            "Warning: HEAD~1 is not a valid git ref (shallow clone or initial commit?), "
            "using empty base_ref",
            file=sys.stderr,
        )
        return ""

    # Fallback to HEAD~1
    try:
        subprocess.run(
            git_argv("rev-parse", "--verify", "HEAD~1"),
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        return "HEAD~1"
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(
            "Warning: HEAD~1 is also not a valid git ref (shallow clone or initial commit?), "
            "using empty base_ref",
            file=sys.stderr,
        )
        return ""


# ---------------------------------------------------------------------------
# The repository metadata a repo-wide batch can now write (root grant,
# 2026-10-05): a fingerprint, never a copy
# ---------------------------------------------------------------------------

#: The name a changed-metadata line carries.
GIT_CONFIG_CHANGED_MARKER = "[GIT_CONFIG_CHANGED]"


def git_common_dir(repo_root: str) -> Optional[str]:
    """The repository's common git directory (``.git``, or the main
    repository's for a linked worktree), absolute; ``None`` when git cannot
    say. ``config`` and ``hooks/`` live there."""
    stdout, _, rc = _run_git("rev-parse", "--git-common-dir", check=False, cwd=repo_root)
    if rc != 0 or not stdout.strip():
        return None
    path = stdout.strip()
    if not os.path.isabs(path):
        path = os.path.join(repo_root, path)
    return os.path.realpath(path)


def _file_sha256_or_none(path: str) -> Optional[str]:
    try:
        with open(path, "rb") as handle:
            return hashlib.sha256(handle.read()).hexdigest()
    except OSError:
        return None


def git_config_include_targets(repo_root: str, common_dir: str) -> List[str]:
    """The files the repository's own config pulls in through ``include.path``
    / ``includeIf.<cond>.path`` (scope ``local`` or ``worktree``), absolute, in
    config order; empty when git cannot say. A relative target is resolved
    the way git resolves it, against the including file's directory — the
    git directory for ``config`` — and ``~`` is expanded."""
    try:
        proc = subprocess.run(
            git_argv("config", "-z", "--show-scope", "--get-regexp", r"^include(if\..*)?\.path$",
                     cwd=repo_root),
            capture_output=True, cwd=repo_root, timeout=30, stdin=subprocess.DEVNULL,
        )
    except (OSError, ValueError, subprocess.SubprocessError):
        return []
    if proc.returncode not in (0, 1) or not isinstance(proc.stdout, bytes):
        return []
    targets: List[str] = []
    for scope, _key, value in _parse_scoped_config(proc.stdout.decode("utf-8", errors="replace")):
        if scope not in _DRIVER_SCOPES_A_BATCH_CAN_WRITE or not value:
            continue
        path = os.path.expanduser(value)
        if not os.path.isabs(path):
            path = os.path.join(common_dir, path)
        targets.append(os.path.normpath(path))
    return targets


def git_metadata_fingerprint(repo_root: str) -> Optional[Dict[str, Any]]:
    """A fingerprint of what a batch could plant for the user's next git
    command to run: the sha256 of ``<git-dir>/config``, of
    ``<git-dir>/config.worktree``, of ``<git-dir>/info/attributes`` (binds a
    filter or diff driver to paths) and ``<git-dir>/info/exclude`` (hides
    paths from ``status``), of every file the config includes
    (:func:`git_config_include_targets`), and a listing of
    ``<git-dir>/hooks/`` (name → size, mode, mtime_ns; a symlink's
    destination). No bytes are kept; ``None`` when there is no git directory.
    Taken before a repo-wide dispatch and compared after it by
    :func:`describe_git_metadata_change` — detective, never a rollback."""
    common = git_common_dir(repo_root)
    if common is None:
        return None
    config_sha = _file_sha256_or_none(os.path.join(common, "config"))
    files: Dict[str, Optional[str]] = {
        ".git/config.worktree": _file_sha256_or_none(os.path.join(common, "config.worktree")),
        ".git/info/attributes": _file_sha256_or_none(os.path.join(common, "info", "attributes")),
        ".git/info/exclude": _file_sha256_or_none(os.path.join(common, "info", "exclude")),
    }
    includes: Dict[str, Optional[str]] = {}
    for target in git_config_include_targets(repo_root, common):
        includes[target] = _file_sha256_or_none(target)
    hooks: Dict[str, Tuple[Any, ...]] = {}
    hooks_dir = os.path.join(common, "hooks")
    try:
        names = sorted(os.listdir(hooks_dir))
    except OSError:
        names = []
    for name in names:
        path = os.path.join(hooks_dir, name)
        try:
            info = os.lstat(path)
        except OSError:
            continue
        if os.path.islink(path):
            try:
                hooks[name] = ("link", os.readlink(path))
            except OSError:
                hooks[name] = ("link", "unreadable")
        else:
            hooks[name] = ("file", info.st_size, info.st_mode, info.st_mtime_ns)
    return {
        "git_dir": common, "config_sha256": config_sha, "hooks": hooks,
        "files": files, "includes": includes,
    }


def _describe_hash_moves(
    old: Mapping[str, Any], new: Mapping[str, Any], label: Callable[[str], str],
) -> List[str]:
    parts: List[str] = []
    for name in sorted(set(old) | set(new)):
        was, now = old.get(name), new.get(name)
        if was == now:
            continue
        if was is None:
            parts.append(f"{label(name)} added")
        elif now is None:
            parts.append(f"{label(name)} removed")
        else:
            parts.append(f"{label(name)} changed")
    return parts


def describe_git_metadata_change(
    before: Optional[Mapping[str, Any]], after: Optional[Mapping[str, Any]]
) -> Optional[str]:
    """What moved between two fingerprints, as ``.git``-relative names
    (``.git/config changed; .git/hooks/pre-commit added; .git/info/attributes
    added; include.path target /x/evil.inc changed``), or ``None`` when
    nothing did or either side is missing."""
    if not before or not after:
        return None
    parts: List[str] = []
    if before.get("config_sha256") != after.get("config_sha256"):
        parts.append(".git/config changed")
    parts += _describe_hash_moves(
        before.get("files") or {}, after.get("files") or {}, lambda name: name,
    )
    parts += _describe_hash_moves(
        before.get("includes") or {}, after.get("includes") or {},
        lambda path: f"include.path target {path}",
    )
    old = before.get("hooks") or {}
    new = after.get("hooks") or {}
    for name in sorted(set(old) | set(new)):
        if name not in old:
            parts.append(f".git/hooks/{name} added")
        elif name not in new:
            parts.append(f".git/hooks/{name} removed")
        elif old[name] != new[name]:
            parts.append(f".git/hooks/{name} changed")
    return "; ".join(parts) if parts else None


def worktree_file_stats(
    repo_root: str, *, exclude_prefixes: Iterable[str] = ()
) -> Optional[Dict[str, Tuple[int, int]]]:
    """``path -> (size, mtime_ns)`` for the files git sees in the worktree:
    tracked plus untracked-not-ignored, repo-relative with ``/``.

    The map :func:`worktree_fingerprint` digests, and what the native leg's
    check guard compares across one check's dispatch (``util write-prompt``
    records it, ``util batch-done`` reads it back), so both
    see the same files the same way. *exclude_prefixes* are repo-relative
    files or directories whose contents are left out. ``None`` when git
    cannot answer.
    """
    try:
        stdout, _, returncode = _run_git(
            "ls-files", "--cached", "--others", "--exclude-standard", "-z",
            "--full-name", "--", ":/",
            check=False, cwd=repo_root,
        )
    except OSError:
        return None
    if returncode != 0:
        return None
    excluded_paths = {
        prefix.strip("/").replace(os.sep, "/")
        for prefix in exclude_prefixes if prefix and prefix.strip("/")
    }
    excluded = tuple(path + "/" for path in excluded_paths)
    stats: Dict[str, Tuple[int, int]] = {}
    for path in sorted(p for p in stdout.split("\0") if p):
        if path in excluded_paths or path.startswith(excluded) or path in stats:
            continue
        try:
            info = os.lstat(os.path.join(repo_root, path))
        except OSError:
            continue
        stats[path] = (info.st_size, info.st_mtime_ns)
    return stats


def worktree_fingerprint(
    repo_root: str, *, exclude_prefixes: Iterable[str] = ()
) -> Optional[str]:
    """One digest over the files git sees in the worktree: tracked plus
    untracked-not-ignored, each as ``path``, size and ``mtime_ns``
    (:func:`worktree_file_stats`).

    What a resumed ``implement`` asks before re-running a verification-only
    task that failed: has anything the check could have read changed since?
    (racing re-run 3, 2026-10-05: ``--resume`` re-ran a read-only
    ``html-validate`` check on an unchanged page, 148 s for the same
    failure). Cheap on purpose — one ``git ls-files`` plus an ``lstat`` per
    path, no content hashing — and a ``mtime`` move counts as a change, so
    the answer errs towards re-running. Gitignored paths are left out, since
    a host's transcript or a build log growing beside the code is not a code
    change. *exclude_prefixes* are repo-relative directories (the plugin's
    own output trees) whose files are left out too. ``None`` when git cannot
    answer, so a caller re-runs rather than guesses.
    """
    stats = worktree_file_stats(repo_root, exclude_prefixes=exclude_prefixes)
    if stats is None:
        return None
    digest = hashlib.sha256()
    for path in sorted(stats):
        size, mtime_ns = stats[path]
        digest.update(f"{path}\0{size}\0{mtime_ns}\n".encode("utf-8"))
    return digest.hexdigest()


def list_worktree_untracked_files() -> Optional[List[str]]:
    """Every untracked, not-ignored file in the whole worktree, root-relative.

    What ``git diff <ref>`` leaves out of a fallback scope: git diff never shows
    a fully untracked file. The ``:/`` pathspec and ``--full-name`` make the
    answer the same from any directory inside the repository, and ``-z`` hands
    each path back raw. ``None`` when git fails, so a caller can say the count
    is unknown rather than report zero.
    """
    try:
        stdout, _, returncode = _run_git(
            "ls-files", "--others", "--exclude-standard", "-z", "--full-name",
            "--", ":/",
            check=False,
        )
    except OSError:
        return None
    if returncode != 0:
        return None
    return [path for path in stdout.split("\0") if path]


# ---------------------------------------------------------------------------
# The names that moved to utils/git_diff.py and utils/review_diff.py
# ---------------------------------------------------------------------------

#: Every top-level name of the two modules split out of this one, by owner.
#: They are read-only re-exports (see the module docstring): reading one here
#: imports its owner on first use and returns the owner's current binding, and
#: ``dir()`` lists them, so ``from .git_utils import capture_diff_hunks``,
#: ``inspect.getmembers`` and ``create_autospec(git_utils)`` work as before the
#: split. Nothing is copied into this module, so a patch of the owner shows
#: through here; a write here stays here and reaches no moved code, which
#: ``tests/test_git_utils_moved_names.py`` refuses in any test.
_MOVED: Dict[str, Tuple[str, ...]] = {
    "git_diff": (
        "_ASSUMED_BYTES_PER_DIFF_LINE",
        "_GIT_TIMEOUT_SECONDS",
        "_MAX_LINES_PER_FILE",
        "_MAX_TOTAL_BYTES",
        "_is_binary_file",
        "_parse_unified_diff",
        "_per_file_line_cap",
        "_split_diff_by_file",
        "capture_diff_hunks",
        "capture_file_context",
        "capture_file_snapshots",
        "capture_file_snapshots_at",
    ),
    "review_diff": (
        "COLLAPSE_PATH_KEYS",
        "DEFAULT_COLLAPSE_PATHS",
        "DIFF_COVERAGE_COMPLETE",
        "DIFF_COVERAGE_PARTIAL",
        "DIFF_OMITTED_REASON",
        "DIFF_STATUS_FULL",
        "DIFF_STATUS_OMITTED",
        "REVIEW_DIFF_DIRNAME",
        "REVIEW_GROUP_FIXTURES",
        "REVIEW_GROUP_GENERATED",
        "REVIEW_GROUP_ORDER",
        "REVIEW_GROUP_SOURCE",
        "REVIEW_GROUP_TESTS",
        "REVIEW_SCOPE_FILENAME",
        "ReviewDiffContainmentError",
        "ReviewDiffSet",
        "ReviewScopeHeader",
        "WRITTEN_BY_FANOUT",
        "WRITTEN_BY_REAGGREGATE",
        "_BASE_REF_LINE",
        "_COVERAGE_LINE",
        "_Counts",
        "_DIFF_ENTRY_LINE",
        "_DIFF_FAILED_PRINT_LIMIT",
        "_DIFF_FLAGS",
        "_DIFF_GITIGNORE",
        "_DIFF_GIT_TIMEOUT_S",
        "_DIFF_PARTIAL_SAMPLE",
        "_DIFF_SLUG_MAX_CHARS",
        "_FULL_OBJECT_ID",
        "_HEAD_REF_LINE",
        "_OMITTED_LINE",
        "_SCOPE_ID_CHARS",
        "_SCOPE_ID_LINE",
        "_TEST_DIR_SEGMENTS",
        "_TEST_NAME_MARKERS",
        "_TEST_NAME_PREFIX",
        "_WRITTEN_BY_LINE",
        "_check_attr_rejects_source",
        "_code_span",
        "_contained_diff_target",
        "_counts_text",
        "_diff_file_is_whole",
        "_diff_set_mismatch",
        "_entry_counts",
        "_git_diff_output",
        "_git_version_text",
        "_is_empty_tree_base",
        "_is_test_path",
        "_linguist_generated",
        "_matches_any_glob",
        "_normalized_review_path",
        "_numstat_counts",
        "_range_text",
        "_render_review_scope",
        "_reset_diff_dir",
        "_resolve_base_commit",
        "_resolved_collapse_globs",
        "_review_order",
        "_scope_bytes",
        "_write_diff_file",
        "classify_review_paths",
        "compile_path_glob",
        "count_review_groups",
        "load_review_scope",
        "order_review_paths",
        "read_review_scope",
        "review_diff_slug",
        "write_review_diff",
    ),
}
_MOVED_TO: Dict[str, str] = {
    name: module for module, names in _MOVED.items() for name in names
}


def __getattr__(name: str) -> Any:
    """A moved name, read from the module that defines it now. Its owner is
    imported here, on first use, never while this module initialises: the
    owners import nothing from the package at import time either, so no
    order of importing the three can wait on another's import lock."""
    owner = _MOVED_TO.get(name)
    if owner == "git_diff":
        module = importlib.import_module(".git_diff", __package__)
    elif owner == "review_diff":
        module = importlib.import_module(".review_diff", __package__)
    else:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    try:
        return getattr(module, name)
    except AttributeError:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from None


def __dir__() -> List[str]:
    """This module's own names and the moved ones it re-exports."""
    return sorted({*globals(), *_MOVED_TO})
