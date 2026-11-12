"""Commit reviews' front-door core: the seven steps, shared by the commit modes.

``--review-commits``, ``--apply-commit-fixes`` and ``--improve-commits`` do not
fork the review pipeline. Each is a front door that resolves a commit range
(``utils/commit_range.py``), writes a generated **commit brief** for it, and
runs review-code or apply-code-fixes on that brief as if it were a plan. What the brief
is and where it lives is the
path layer, ``utils/commit_paths.py``; its names are re-exported here.

**The front-door core** is the one
implementation of the seven steps that ``--review-commits``,
``--apply-commit-fixes``, ``--improve-commits`` and ``util commit-brief``
share, so the four entry points cannot drift apart:

1. resolve the range (or, on a no-argument apply, pick the review on record);
2. print the commit block, with ``[SCOPE_DRIFT]`` computed here so it lands
   in the foreground before any detach boundary;
3. decide the brief's identity (``--focus`` and ``--context-plan``, typed or
   inherited), reading only;
4. take ownership of the state the run changes: the phase dir's ``.lock`` in
   the foreground, a launch-unique **stage** file under ``--detach`` that the
   worker applies right after it wins the lock (``utils/detach.py``), so a
   refused or re-attached launch publishes nothing;
5. write or reuse the brief (archiving a replaced round first) and print
   ``[COMMIT_BRIEF]``;
6. record ``commit_range`` through ``StateManager.record_commit_range``
   before the fronted phase builds a ``StateManager`` of its own;
7. re-record the invocation under the fronted mode word with the argv that
   run needs, then call the fronted ``main`` in-process.

The brief's bytes come from ``utils/commit_brief.py`` (header, identity hash,
snapshot, restart archive), imported lazily here.
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import hashlib
import inspect
import json
import os
import re
import shlex
import sys
import textwrap
import time
import uuid
from dataclasses import dataclass, field, replace
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

from .cli_common import EXIT_ERROR as _EXIT_ERROR
from .cli_common import EXIT_NEEDS_HUMAN as _EXIT_NEEDS_HUMAN
from .cli_common import (
    EXIT_OK as _EXIT_OK,
    record_error,
    dispatcher_prefix,
    INTERNAL_FLAG_PREFIX,
    record_commit_range_result,
    flag_present,
    record_invocation,
)
from .clock import utc_iso_z
from .git_utils import git_path, run_git, attribute_source_args, run_git_for_paths, GitError
from .provider_registry import ConfigError, get_commit_reviews_dir

# The path layer. Every name is re-exported: ``utils.commit_review``, the old
# name of this module, is an alias of it.
from .commit_paths import (  # noqa: F401
    BRIEF_END_MARKER,
    brief_for_pinned,
    BRIEF_MARKER,
    _BRIEF_NAME_RE,
    brief_path_for,
    commit_review_artifact,
    commit_reviews_folder_rel,
    CommitReviewError,
    document_label,
    ensure_commit_reviews_dir,
    _FIRST_LINE_BYTES,
    _first_line_is_marker,
    FOLDER_GITIGNORE,
    is_commit_brief,
    matches_brief_path,
    not_ignored_warning,
    output_dir_for_brief,
    PathLike,
    PINNED_PATTERN,
    _PINNED_RE,
    read_commit_range,
    read_stage,
    _relative_to_root,
    repo_root_of,
    _slug,
    SLUG_PATTERN,
    _SLUG_RE,
    stage_takes_over,
    _STAGE_VERSION,
    _start_dir,
)
from . import git_utils
from . import process_control
import modes as mode_table
from .unattended import mark_needs_human
from .text_clip import clip, plain_line

# ``commit_range``, ``commit_brief``, ``commit_apply``, ``state_manager``,
# ``detach``, ``positionals`` and ``improve_workflow`` load in the functions
# that use them: a front door's ``--help`` and the dispatcher's
# ``is_commit_brief`` read none of them (tests/test_utils_imports.py
# ``test_a_reader_path_loads_no_module_its_base_did_not``).


# ===========================================================================
# The front-door core
# ===========================================================================
#
# Everything below is shared by the three commit modes' thin orchestrators and
# by `util commit-brief`. The range grammar is `commit_range`'s and the brief's
# bytes are `commit_brief`'s; this part decides what to do with them, in the
# seven steps' order, and owns the one rule that ties them together: steps 1
# to 3 only read, and nothing that changes a run's inputs is published before
# the front door owns the state it changes.

#: The three front doors, by mode word.
COMMIT_MODES: Tuple[str, ...] = ("review-commits", "apply-commit-fixes", "improve-commits")

#: The mode word each front door re-records under: the phase it fronts, or the composite itself.
FRONTED: Dict[str, str] = {
    "review-commits": "review-code",
    "apply-commit-fixes": "apply-code-fixes",
    "improve-commits": "improve-commits",
}

#: The hidden flag that names one ``--detach`` launch's stage on the worker's
#: argv; ``cli_common.replay_flags`` drops it as it drops ``--revs``.
STAGE_FLAG = "--commit-stage"

#: A stage file is ``<phase dir>/.commit-stage-<id>.json``: launch-unique,
#: and matched by ``commit_brief.STAGE_FILE_PATTERN`` so a restart's archive
#: never moves it.
STAGE_PREFIX = ".commit-stage-"
STAGE_SUFFIX = ".json"

#: How ``util commit-brief`` names itself in its messages, and the composite
#: whose native leg it prepares (its parser is the one the tokens are read
#: with, and it checks the composite's dirs for a live owner).
UTIL_DOOR = "util commit-brief"
_UTIL_MODE = "improve-commits"

# Markers this core prints (the commit block's own are commit_range's).
COMMIT_BRIEF = "[COMMIT_BRIEF]"
COMMIT_RANGE_PINNED = "[COMMIT_RANGE_PINNED]"
COMMIT_REVIEW_RESTARTED = "[COMMIT_REVIEW_RESTARTED]"
COMMIT_REVIEW_ARCHIVED = "[COMMIT_REVIEW_ARCHIVED]"
COMMIT_DECISIONS_DROPPED = "[COMMIT_DECISIONS_DROPPED]"
CONTEXT_PLAN_CHANGED = "[CONTEXT_PLAN_CHANGED]"
COMMIT_REVIEW_KEPT = "[COMMIT_REVIEW_KEPT]"
COMMIT_REVIEW_NOT_FOUND = "[COMMIT_REVIEW_NOT_FOUND]"
COMMIT_REMAINING_FLAGS = "[COMMIT_REMAINING_FLAGS]"
RANGE_AFTER_FLAGS = "[RANGE_AFTER_FLAGS]"
#: Step 6 replaced a ``state.json`` that did not parse.
STATE_REPLACED = "[STATE_REPLACED]"

_REVIEW_DIR = "code-review"
_APPLY_DIR = "apply-fixes"

#: The tokens only a front door reads, each with one value: the range (as
#: ``--revs`` or a brief path's ``--plan-file``), the two identity options and
#: the stage. Taken out of every argv a fronted phase is handed.
_DOOR_ONLY: Tuple[str, ...] = ("--revs", "--plan-file", "--focus", "--context-plan",
                               "--commit-stage")

#: The flags a front door synthesises for the phase it fronts; the
#: ``[RANGE_AFTER_FLAGS]`` parse gives the fronted parser placeholders for them.
_SYNTHESISED: Tuple[str, ...] = ("--plan-file", "--base-ref", "--head-ref")
_PLACEHOLDER = "front-door-placeholder"


_DASH_N_RE = re.compile(r"-[0-9]+")


class FrontDoorExit(Exception):
    """A front door stopped before its fronted phase; ``exit_code`` is its exit.

    Raised by :func:`prepare` once every line the stop owes the user is
    printed (and the result line's error recorded), so the caller only
    returns the code.
    """

    def __init__(self, exit_code: int):
        super().__init__(exit_code)
        self.exit_code = exit_code


def _brief_api():
    """``utils.commit_brief``: the header, identity, snapshot and archive.

    Imported at call time: the brief writer lands beside this module, and
    the dispatcher imports this module for :func:`is_commit_brief` alone.
    """
    # Imported here: a commit front door's `--help` loads only its base modules.
    from . import commit_brief

    return commit_brief


#: ``resolved_at``/``created_at``: now, in UTC, ISO-8601 with a ``Z``
#: (``utils/clock.py``).
_now_iso = utc_iso_z


def _shown_path(path: PathLike) -> str:
    """*path* relative to the cwd when it lies under it (``/``-separated), else
    absolute: how ``[COMMIT_BRIEF]``, the block's pointer and the result line
    name a brief, so the printed path works when typed back from here."""
    text = os.path.abspath(os.fspath(path))
    try:
        shown = os.path.relpath(text)
    except ValueError:  # Windows: another drive than the cwd's
        return text
    if shown == os.pardir or shown.startswith(os.pardir + os.sep):
        return text
    return shown.replace(os.sep, "/")


def _absolute(path: str, cwd: str) -> Path:
    return Path(path if os.path.isabs(path) else os.path.join(cwd, path))


def _door_word(mode: str, util: bool) -> str:
    """How the user names the command: ``--review-commits``, ``util commit-brief``."""
    return UTIL_DOOR if util else f"--{mode}"


def _stop(message: str, exit_code: int) -> FrontDoorExit:
    """Print *message* (a marker line to stdout, an ``ERROR:`` to stderr),
    record its first line as the run's error, and return the exit to raise."""

    text = message.rstrip("\n")
    lines = text.splitlines()
    split = next((index for index, line in enumerate(lines) if line.startswith("ERROR:")),
                 len(lines))
    if not text.startswith("["):
        split = 0
    if lines[:split]:
        print("\n".join(lines[:split]))
    if lines[split:]:
        print("\n".join(lines[split:]), file=sys.stderr)
    if text:
        record_error(text.splitlines()[0])
    if exit_code == _EXIT_NEEDS_HUMAN:
        mark_needs_human()
    return FrontDoorExit(exit_code)


# ---------------------------------------------------------------------------
# Options and parsers
# ---------------------------------------------------------------------------


def add_commit_options(parser: argparse.ArgumentParser, *, skip_present: bool = False) -> None:
    """Add the front doors' own options to *parser*.

    ``--focus <text>`` and ``--context-plan <path>``: only the front
    doors and ``util commit-brief`` take them; the fronted phases' parsers
    never do, so ``--review-code x.md --focus y`` keeps argparse's error.
    Hidden: ``--revs`` (the dispatcher's joined range words) and
    ``--commit-stage`` (a detached launch's stage). *skip_present* leaves out
    any option *parser* already has (the composite's parser carries the
    hidden ``--commit-stage`` itself).
    """
    present = getattr(parser, "_option_string_actions", {}) if skip_present else {}
    if "--focus" not in present:
        parser.add_argument(
            "--focus", default=None, metavar="TEXT",
            help='Steer the review toward TEXT ("error handling"). Recorded with the '
                 'commit brief: omitted later, it is kept; a different value restarts '
                 'the review round; --focus "" clears it.',
        )
    if "--context-plan" not in present:
        parser.add_argument(
            "--context-plan", default=None, metavar="PATH",
            help="A plan the review reads as read-only context. Its bytes are "
                 "snapshotted into the review's folder and every reader reads the "
                 "snapshot; recorded like --focus (omitted: kept; other bytes or "
                 'another file: restarts; --context-plan "": clears).',
        )
    if "--revs" not in present:
        parser.add_argument("--revs", default=None, help=argparse.SUPPRESS)
    if "--commit-stage" not in present:
        parser.add_argument("--commit-stage", dest="commit_stage", default=None,
                            help=argparse.SUPPRESS)


_DESCRIPTIONS: Dict[str, str] = {
    "review-commits": (
        "Review a commit range with every model, then group and validate the "
        "findings. Python resolves the range, prints the commits it covers, "
        "writes a commit brief for them (the stated intent is the commit "
        "messages) and runs review-code on that brief, diffing the range's two "
        "commits rather than the working tree."
    ),
    "apply-commit-fixes": (
        "Apply a commit review's validated fixes as uncommitted edits. With no "
        "range, the newest completed commit review that ends at HEAD (or behind "
        "it) is applied; with one, that range's review. Runs apply-code-fixes on "
        "the review's commit brief; a fix to a file changed since the reviewed "
        "commit is skipped and named."
    ),
    "improve-commits": (
        "Review a commit range with every model, then apply the validated fixes, "
        "unattended: review-commits and apply-commit-fixes in one resumable "
        "command, run as the improve-commits composite on the commit brief."
    ),
}

_RANGE_HELP = (
    "The range goes right after the mode word, before any flag, and needs no "
    "quotes. It is git revision syntax (A..B, A...B, one commit), one phrase "
    "(last 2 commits, -2, this branch, since <rev>, today, last two days), a "
    "commit brief's path, or the pinned <base12>..<head12> a run printed. No "
    "range means HEAD: the last commit against its first parent."
)


def _help_parser(mode: str, *, util: bool = False) -> argparse.ArgumentParser:
    """The ``--help`` surface of a front door (or of ``util commit-brief``)."""

    run = dispatcher_prefix()
    fronted = FRONTED[mode] if mode != "improve-commits" else "improve-code"
    if util:
        prog = UTIL_DOOR
        description = (
            "A commit mode's preparation, launching nothing: resolve the range, "
            "print the commit block, take ownership of the review, write or reuse "
            "its commit brief and record the range, then print [COMMIT_BRIEF] "
            "<path>, [COMMIT_RANGE_PINNED] and [COMMIT_REMAINING_FLAGS] <the tokens "
            "it did not consume> for `util improve-steps <brief> --mode "
            "improve-commits`. Takes every token the command was typed with.\n\n"
            + _RANGE_HELP
        )
        examples = [
            f"  {run} util commit-brief last 2 commits --focus \"error handling\"",
            f"  {run} util commit-brief this branch --quick",
        ]
        forwarded = "improve-commits"
    else:
        prog = f"--{mode}"
        description = _DESCRIPTIONS[mode] + "\n\n" + _RANGE_HELP
        if mode == "apply-commit-fixes":
            examples = [
                f"  {run} apply-commit-fixes",
                f"  {run} apply-commit-fixes a1b2c3d4e5f6..e4f5a6b7c8d9",
            ]
        else:
            examples = [
                f"  {run} {mode}",
                f"  {run} {mode} last 2 commits --focus \"error handling\"",
                f"  {run} {mode} main...HEAD --context-plan docs/design.md --quick",
            ]
        forwarded = FRONTED[mode]
    epilog_lines = [
        "",
        f"Every other flag is forwarded to {forwarded} unchanged (--models, --quick, "
        "--scope-policy, --resume, --force, --detach, ...):" if not util else
        "Every other flag is the composite's (--models, --quick, --files, "
        "--scope-policy, --resume, --force, ...), handed back on "
        "[COMMIT_REMAINING_FLAGS]:",
        f"  {run} {fronted} --help",
        "--plan-file, --base-ref and --head-ref are refused: the front door "
        "synthesises them from the range.",
        "",
        "Examples:",
        *examples,
    ]

    parser = argparse.ArgumentParser(
        prog=prog,
        usage=f"{prog} [<range>] [--focus TEXT] [--context-plan PATH] [flags...]",
        description="\n\n".join(textwrap.fill(paragraph, width=78)
                                for paragraph in description.split("\n\n")),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="\n".join(epilog_lines) + "\n",
    )
    add_commit_options(parser)
    parser.add_argument("--plan-file", default=None, help=argparse.SUPPRESS)
    return parser


def parse_args(mode: str, argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    """Parse a front door's own options (the thin orchestrators' ``parse_args``).

    *mode* is a commit mode word, or ``"commit-brief"`` for ``util
    commit-brief``. ``--help`` prints the door's help and exits 0. Any token
    the door does not own is left on ``remaining``: it is the fronted phase's
    to parse.
    """
    util = mode in ("commit-brief", UTIL_DOOR)
    parser = _help_parser(_UTIL_MODE if util else mode, util=util)
    namespace, rest = parser.parse_known_args(
        list(sys.argv[1:] if argv is None else argv)
    )
    namespace.remaining = list(rest)
    return namespace


class _ParserCaptured(Exception):
    def __init__(self, parser: argparse.ArgumentParser):
        super().__init__("parser captured")
        self.parser = parser


def _capture_parser(parse: Callable[[List[str]], Any]) -> argparse.ArgumentParser:
    """The parser a phase's ``parse_args`` builds, without parsing anything.

    review-code and apply-code-fixes build their parser inside ``parse_args``
    and expose no builder; the ``[RANGE_AFTER_FLAGS]`` check needs that very
    parser (its options, its ``nargs``), so its ``parse_args`` call is
    intercepted for the length of one build.
    """
    original = argparse.ArgumentParser.parse_args

    def capture(self, args=None, namespace=None):  # noqa: ARG001
        raise _ParserCaptured(self)

    argparse.ArgumentParser.parse_args = capture  # type: ignore[assignment]
    try:
        parse([])
    except _ParserCaptured as captured:
        return captured.parser
    finally:
        argparse.ArgumentParser.parse_args = original  # type: ignore[assignment]
    raise RuntimeError("the fronted phase's parse_args built no parser")


def _fronted_parser(mode: str) -> argparse.ArgumentParser:
    """The parser of the phase *mode* fronts (the composite's for improve-commits)."""
    if mode == "improve-commits":
        # Imported here: a commit front door's `--help` loads only its base modules.
        from . import improve_workflow

        return improve_workflow.build_parser(mode)
    if mode == "review-commits":
        # The fronted orchestrators import this module: a load-time cycle.
        import code_review_orchestrator as target

        return _capture_parser(target.parse_args)
    # A load-time cycle, as for review-commits above.
    import apply_code_fixes_orchestrator as target

    return _capture_parser(target.ApplyCodeFixesOrchestrator.parse_args)


def _door_parser(mode: str) -> argparse.ArgumentParser:
    """The fronted parser plus the door's own options: the one parser that
    reads a front door's argv, so abbreviations resolve as argparse would
    over both sets."""
    parser = _fronted_parser(mode)
    add_commit_options(parser, skip_present=True)
    return parser


def _canonical_option(head: str, parser: argparse.ArgumentParser) -> Optional[str]:
    """The option *head* binds to in *parser*: an exact spelling, else a
    unique ``--`` prefix (argparse's abbreviation rule); else None."""
    actions = parser._option_string_actions  # noqa: SLF001 - argparse's own table
    if head in actions:
        return head
    if not head.startswith("--") or len(head) <= 2:
        return None
    matches = [option for option in actions if option.startswith("--") and option.startswith(head)]
    return matches[0] if len(matches) == 1 else None


def _split_door_tokens(
    argv: Sequence[str], parser: argparse.ArgumentParser,
) -> Tuple[List[str], Dict[str, str]]:
    """``(forwarded, own)``: *argv* without the front-door-only tokens
    (:data:`_DOOR_ONLY`, each with its value), and those tokens' values by
    canonical option (the last one wins, as argparse's ``store`` does)."""
    forwarded: List[str] = []
    own: Dict[str, str] = {}
    tokens = list(argv)
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token == "--":
            forwarded.extend(tokens[index:])
            break
        if token.startswith("--"):
            head, separator, inline = token.partition("=")
            option = _canonical_option(head, parser)
            if option in _DOOR_ONLY:
                if separator:
                    own[option] = inline
                    index += 1
                else:
                    if index + 1 < len(tokens):
                        own[option] = tokens[index + 1]
                    index += 2
                continue
        forwarded.append(token)
        index += 1
    return forwarded, own


def _swallowed_by_models(values: Sequence[str]) -> List[str]:
    """The ``--models`` values that are really a range: a run of values the pure phrase matcher recognizes
    (``last 2 commits``), else every value holding ``..``, ``~``, ``^`` or
    ``@{`` (or a bare ``-N``). No model id has those shapes."""
    # Imported here: a commit front door's `--help` loads only its base modules.
    from .commit_range import looks_like_range_word, match_phrase

    texts = [str(value) for value in values]
    for start in range(len(texts)):
        for end in range(min(len(texts), start + 6), start, -1):
            if match_phrase(" ".join(texts[start:end])):
                return texts[start:end]
    return [text for text in texts if looks_like_range_word(text)]


def _without_tokens(tokens: Sequence[str], moved: Sequence[str]) -> List[str]:
    """*tokens* with one occurrence of each *moved* word taken out, last first."""
    out = list(tokens)
    for word in reversed(list(moved)):
        for index in range(len(out) - 1, -1, -1):
            if out[index] == word:
                del out[index]
                break
    return out


def _check_range_after_flags(
    door: str, argv: Sequence[str], namespace: argparse.Namespace, extras: Sequence[str],
    parser: argparse.ArgumentParser, own: Mapping[str, str],
) -> None:
    """The ``[RANGE_AFTER_FLAGS]``, before step 1 and before any write.

    A leftover bare word or ``-N``, or ``--models`` values shaped like a
    range, is exit 3 naming the command with those words moved right after
    the mode word. Any other leftover (an unknown flag) is the fronted
    parser's own unrecognized-arguments error, raised now rather than after
    the brief is written.

    An unknown flag is checked first: a word after it may be its value
    (``--nosuch value``; ``--models x`` on apply-commit-fixes, whose parser
    has no ``--models``), and any ``Run:`` command printed for moved words
    would still carry the flag the fronted parser refuses. So any unknown
    flag is that parser's error, naming every leftover as ``parse_args``
    would, and no word is ever moved past it. A bare ``--`` is a separator,
    not a flag.
    """
    words = [token for token in extras if not token.startswith("-") or _DASH_N_RE.fullmatch(token)]
    unknown = [token for token in extras if token not in words and token != "--"]
    if unknown:
        parser.error(f"unrecognized arguments: "
                     f"{' '.join(token for token in extras if token != '--')}")
    moved = _swallowed_by_models(getattr(namespace, "models", None) or []) + words
    if moved:
        rest = _without_tokens(argv, moved)
        typed_range: List[str] = []
        kept: List[str] = []
        index = 0
        while index < len(rest):
            token = rest[index]
            head, separator, inline = token.partition("=")
            option = _canonical_option(head, parser) if token.startswith("--") else None
            if option in ("--revs", "--plan-file") and option in own:
                value = inline if separator else (rest[index + 1] if index + 1 < len(rest) else "")
                typed_range = value.split() if option == "--revs" else [value]
                index += 1 if separator else 2
                continue
            kept.append(token)
            index += 1
        command = " ".join(door.split() + [shlex.quote(word) for word in typed_range + moved]
                           + [shlex.quote(token) for token in kept])
        raise _stop(
            f"{RANGE_AFTER_FLAGS} {' '.join(moved)}\n"
            f"ERROR: a range goes right after the mode word, before any flag (a word "
            f"after a flag may be that flag's value: --models takes several). Run: "
            f"{command}",
            _EXIT_NEEDS_HUMAN,
        )


@dataclass
class _Typed:
    """What a front door read off its argv."""

    argv: List[str]
    namespace: argparse.Namespace
    forwarded: List[str]
    revs: Optional[str]
    brief_arg: Optional[str]
    focus: Optional[str]
    context_plan: Optional[str]
    stage: Optional[str]

    def flag(self, name: str, default: Any = None) -> Any:
        return getattr(self.namespace, name, default)


def _parse_door(mode: str, argv: Sequence[str], *, door: str) -> _Typed:
    """Read a front door's argv with the door parser, then run the
    ``[RANGE_AFTER_FLAGS]`` check over what is left."""
    parser = _door_parser(mode)
    placeholders: List[str] = []
    for flag in _SYNTHESISED:
        if flag in parser._option_string_actions:  # noqa: SLF001
            placeholders += [flag, _PLACEHOLDER]
    namespace, extras = parser.parse_known_args(placeholders + list(argv))
    forwarded, own = _split_door_tokens(argv, parser)
    _check_range_after_flags(door, argv, namespace, extras, parser, own)
    return _Typed(
        argv=list(argv),
        namespace=namespace,
        forwarded=forwarded,
        revs=own.get("--revs"),
        brief_arg=own.get("--plan-file"),
        focus=own.get("--focus"),
        context_plan=own.get("--context-plan"),
        stage=own.get("--commit-stage"),
    )


# ---------------------------------------------------------------------------
# Step 1: the range
# ---------------------------------------------------------------------------


@dataclass
class _Resolution:
    cr: Any                                   # commit_range.CommitRange
    brief: Optional[Path] = None              # known when the input named the brief
    record: Optional[Dict[str, Any]] = None   # read with it
    selected_line: Optional[str] = None       # a no-argument apply's pick
    selected: Optional[Dict[str, Any]] = None


def _not_found_no_range(shown: str) -> CommitReviewError:
    return CommitReviewError(
        f"{COMMIT_REVIEW_NOT_FOUND} {shown}: no commit range recorded for this brief\n"
        f"  Its range is read from its state.json, never from the header. Review the "
        f"commits again with --review-commits <range>."
    )


def _from_brief(path: Path, shown: str, root: Path) -> _Resolution:
    """Step 1 for a brief path: ``commit_range`` re-resolved strictly, no words parsed.

    A brief whose state records no range (a detached first launch refused or
    killed after the brief was created) is re-entered by its name: the slug
    resolved strictly (``commit_range.resolve_slug``), then the first
    resolution, as its typed pinned spelling would be. That is the only way
    back into a root range, whose one pinned spelling is the brief path
    (review fix 3, A5). A slug that resolves to no range keeps
    ``[COMMIT_REVIEW_NOT_FOUND]``."""
    # Imported here: a commit front door's `--help` loads only its base modules.
    from .commit_range import CommitRange, RangeError, resolve_recorded, resolve_slug

    record = read_commit_range(path)
    if record is None:
        try:
            cr = resolve_slug(Path(path).stem, cwd=str(root))
        except RangeError:
            raise _not_found_no_range(shown) from None
        return _Resolution(cr=cr, brief=Path(os.path.abspath(path)), record=None)
    resolved = resolve_recorded(
        record, cwd=str(root), label=shown,
        recovery=("Re-run --review-commits <range> on the commits as they are now: it "
                  "resolves to new SHAs and a new brief, since this review can no "
                  "longer be resumed, reaggregated or applied."),
    )
    cr = CommitRange.from_record({**record, "base": resolved.base, "head": resolved.head})
    return _Resolution(cr=cr, brief=Path(os.path.abspath(path)), record=record)


def _from_text(text: str, mode: str, root: Path, cwd: str) -> _Resolution:
    """Step 1 for typed words, with the markdown-path messages."""
    # Imported here: a commit front door's `--help` loads only its base modules.
    from .commit_range import RANGE_BAD_REF, RANGE_UNRECOGNIZED, RangeError, resolve_range

    word = " ".join(text.split())
    if " " in word or not word.lower().endswith(".md"):
        return _Resolution(cr=resolve_range(word, cwd=str(root)))
    path = _absolute(word, cwd)
    if path.is_file():
        if is_commit_brief(path, cwd=cwd):
            return _from_brief(path, word, root)
        reviewer = "review-commits" if mode == "apply-commit-fixes" else mode
        return _Resolution(cr=resolve_range(
            word, cwd=str(root), file_hint="a file, but not a commit brief",
            file_hint_lines=(
                f"To review commits against that plan: --{reviewer} <range> "
                f"--context-plan {shlex.quote(word)}",
                f"To review the working tree against it: --review-code {shlex.quote(word)}",
            ),
        ))
    try:
        return _Resolution(cr=resolve_range(word, cwd=str(root),
                                            file_hint="no such file or revision"))
    except RangeError as exc:
        if exc.tag == RANGE_UNRECOGNIZED and ".." in word:
            # `A..B` whose B ends in `.md` (a tag `v1.md`): the file-hint path
            # tries the word as one `<rev>` only, so the full grammar reads it
            # before the refusal stands (review fix 3, A4). A range it finds
            # but refuses (diverged, empty, shallow) is that answer; one it
            # cannot resolve at all keeps the file-hint message.
            try:
                return _Resolution(cr=resolve_range(word, cwd=str(root)))
            except RangeError as grammar:
                if grammar.tag not in (RANGE_UNRECOGNIZED, RANGE_BAD_REF):
                    raise
        if exc.tag == RANGE_UNRECOGNIZED and matches_brief_path(word, cwd=cwd):
            raise CommitReviewError(
                f"{COMMIT_REVIEW_NOT_FOUND} {word}: no commit brief at {word}\n"
                f"  Review the range again: --review-commits <range>"
            ) from None
        raise


def _refuse_unborn(root: Path) -> None:
    """The unborn ``HEAD`` (exit 2), before a no-argument apply's lookup."""
    # Imported here: a commit front door's `--help` loads only its base modules.
    from .commit_range import NOTHING_TO_REVIEW, RangeError

    _out, _err, code = run_git("rev-parse", "--verify", "--quiet", "HEAD^{commit}",
                                check=False, cwd=str(root))
    if code == 0:
        return
    branch, _err, code = run_git("symbolic-ref", "-q", "HEAD", check=False, cwd=str(root))
    branch = branch.strip()
    if code == 0 and branch:
        short = branch[len("refs/heads/"):] if branch.startswith("refs/heads/") else branch
        raise RangeError(NOTHING_TO_REVIEW, f"{NOTHING_TO_REVIEW} no commits yet on {short}", 2)


def _resolve(mode: str, typed: _Typed, root: Path, cwd: str) -> _Resolution:
    """Step 1: the range from the brief path, the typed words, or (a
    no-argument apply) the review on record."""
    # Imported here: a commit front door's `--help` loads only its base modules.
    from .commit_range import resolve_range

    if typed.brief_arg is not None:
        path = _absolute(typed.brief_arg, cwd)
        if path.is_file() and is_commit_brief(path, cwd=cwd):
            return _from_brief(path, typed.brief_arg, root)
        return _from_text(typed.brief_arg, mode, root, cwd)
    text = (typed.revs or "").strip()
    if text:
        return _from_text(text, mode, root, cwd)
    if mode == "apply-commit-fixes":
        _refuse_unborn(root)
        # Imported here: a commit front door's `--help` loads only its base modules.
        from . import commit_apply

        selection = commit_apply.select_review(cwd=str(root))
        brief = Path(os.fspath(selection.brief))
        result = _from_brief(brief, _shown_path(brief), root)
        result.selected_line = getattr(selection, "line", None)
        result.selected = getattr(selection, "payload", None)
        return result
    return _Resolution(cr=resolve_range(None, cwd=str(root)))


# ---------------------------------------------------------------------------
# Step 2: the commit block, with the drift check
# ---------------------------------------------------------------------------


def _block_view(cr: Any, record: Optional[Mapping[str, Any]]) -> Any:
    """The range as a reuse shows it: this resolution's commits, with the
    first resolution's phrase, window, ``(outside window)`` tags and notes, plus any
    note this resolution adds."""
    if record is None:
        return cr
    # Imported here: a commit front door's `--help` loads only its base modules.
    from .commit_range import Window

    window = record.get("window")
    recorded_notes = [str(note) for note in (record.get("notes") or ())]
    notes = recorded_notes + [note for note in cr.notes if note not in recorded_notes]
    flags = {
        str(entry.get("sha")): bool(entry.get("outside_window"))
        for entry in (record.get("commits") or ()) if isinstance(entry, Mapping)
    }
    commits = tuple(
        replace(commit, outside_window=flags.get(commit.sha, commit.outside_window))
        for commit in cr.commits
    )
    return replace(
        cr,
        phrase=record.get("phrase"),
        window=Window.from_record(window) if isinstance(window, Mapping) else None,
        notes=tuple(notes),
        commits=commits,
    )


def _typed_scope(typed: _Typed, root: Path) -> Optional[List[str]]:
    """The typed ``--files``/``--files-from <file>``, through review-code's own
    reader; never ``--files-from -`` (the phase is stdin's one reader)."""
    files = [item for item in (typed.flag("files") or []) if item is not None]
    files_from = typed.flag("files_from")
    if not files and files_from is None:
        return None
    if files_from == "-":
        files_from = None
        if not files:
            return None
    # ``code_review_orchestrator`` imports this module: a load-time cycle.
    import code_review_orchestrator as review_code

    try:
        return review_code.read_scope_files_flags(
            argparse.Namespace(files=files, files_from=files_from, detach=False), str(root)
        )
    except review_code.ScopeFilesError as exc:
        raise CommitReviewError(f"ERROR: {exc}", exit_code=_EXIT_ERROR) from None


def _review_scope(cr: Any, typed: _Typed, root: Path) -> List[str]:
    """``git diff --name-only <diff_base> <head>`` minus every commit review's
    own files, narrowed by the typed scope."""
    # Imported here: a commit front door's `--help` loads only its base modules.
    from .commit_range import diff_base

    out, err, code = run_git_for_paths(
        *attribute_source_args(cr.head), "diff", "--name-only", "-z",
        diff_base(cr, cwd=str(root)), cr.head, "--", cwd=str(root),
    )
    if code != 0:
        raise CommitReviewError(f"ERROR: git diff --name-only failed: {err.strip()}",
                                exit_code=_EXIT_ERROR)
    names = [name for name in out.split("\0") if name]
    folder = commit_reviews_folder_rel(root)
    if folder:
        names = [name for name in names if not commit_review_artifact(name, folder)]
    narrowed = _typed_scope(typed, root)
    if narrowed is not None:
        wanted = set(narrowed)
        names = [name for name in names if name in wanted]
    return names


def _drift(cr: Any, typed: _Typed, root: Path) -> Tuple[List[str], int]:
    """``(drifted, scope size)``: the scope files the shared change test marks."""
    scope = _review_scope(cr, typed, root)
    if not scope:
        return [], 0

    changed = set(git_utils.paths_changed_since(cr.head, scope, cwd=str(root)))
    return [path for path in scope if path in changed], len(scope)


# ---------------------------------------------------------------------------
# Step 3: the identity
# ---------------------------------------------------------------------------


@dataclass
class _Identity:
    focus: Optional[str]
    plan: Optional[str]
    plan_snapshot: Optional[str]
    plan_sha256: Optional[str]
    header_sha256: Optional[str]
    changed: bool
    reasons: List[str] = field(default_factory=list)
    plan_data: Optional[bytes] = None       # a new snapshot's bytes, from the one read
    plan_source: Optional[str] = None

    def fields(self) -> Dict[str, Any]:
        return {
            "focus": self.focus,
            "plan": self.plan,
            "plan_snapshot": self.plan_snapshot,
            "plan_sha256": self.plan_sha256,
            "header_sha256": self.header_sha256,
        }


def _quoted(text: Optional[str]) -> str:
    return '"' + clip(plain_line(text or ""), 80) + '"'


def _plan_file(plan: str, root: Path) -> Path:
    return Path(plan) if os.path.isabs(plan) else root.joinpath(*plan.split("/"))


def _read_typed_plan(typed_plan: str, root: Path, cwd: str) -> Tuple[str, Path, bytes]:
    """``(normalised path, file, bytes)`` of a typed ``--context-plan``: one read."""
    plan = _brief_api().normalize_plan_path(typed_plan, cwd=cwd, root=root)
    source = _plan_file(plan, root)
    try:
        data = source.read_bytes()
    except OSError as exc:
        raise CommitReviewError(
            f"ERROR: --context-plan {typed_plan}: cannot read it "
            f"({exc.strerror or exc}); nothing was written",
            exit_code=_EXIT_ERROR,
        ) from None
    return plan, source, data


def _identity(mode: str, cr: Any, record: Optional[Mapping[str, Any]], typed: _Typed,
              root: Path, cwd: str, brief: Path, *, check_plan: bool, quiet: bool) -> _Identity:
    """Step 3: the identity this invocation asks for, against the record.

    An omitted ``--focus``/``--context-plan`` inherits the recorded value; a
    typed one is compared, ``""`` clearing it. apply-commit-fixes never changes the
    identity: a typed value
    that differs prints ``[COMMIT_REVIEW_KEPT]`` and the recorded review is
    applied. Prints ``[CONTEXT_PLAN_CHANGED]`` for an inherited plan whose
    file moved on, on the doors that review (*check_plan*).
    """
    api = _brief_api()
    rec = dict(record or {})
    rec_focus = rec.get("focus") or None
    rec_plan = rec.get("plan") or None
    rec_snapshot = rec.get("plan_snapshot") or None
    rec_sha = rec.get("plan_sha256") or None
    pinned = cr.pinned or _shown_path(brief)

    if mode == "apply-commit-fixes":
        if not quiet:
            _print_kept(typed, rec_focus, rec_plan, rec_sha, pinned, root, cwd)
        return _Identity(focus=rec_focus, plan=rec_plan, plan_snapshot=rec_snapshot,
                         plan_sha256=rec_sha, header_sha256=rec.get("header_sha256"),
                         changed=False)

    focus = rec_focus if typed.focus is None else (typed.focus or None)
    plan_data: Optional[bytes] = None
    plan_source: Optional[str] = None
    if typed.context_plan is None:
        plan, snapshot, sha = rec_plan, rec_snapshot, rec_sha
    elif typed.context_plan == "":
        plan = snapshot = sha = None
    else:
        plan, source, data = _read_typed_plan(typed.context_plan, root, cwd)
        sha = hashlib.sha256(data).hexdigest()
        if plan == rec_plan and sha == rec_sha and rec_snapshot and (
            api.file_sha256(_plan_file(rec_snapshot, root)) == rec_sha
        ):
            snapshot = rec_snapshot
        else:
            snapshot = git_path(output_dir_for_brief(brief) / api.CONTEXT_PLAN_SNAPSHOT,
                                repo_root=root)
            plan_data, plan_source = data, str(source)

    if snapshot and sha and plan_data is None and api.file_sha256(_plan_file(snapshot, root)) != sha:
        raise CommitReviewError(
            f"[CONTEXT_PLAN_SNAPSHOT_CHANGED] {snapshot} is missing or differs from the "
            "frozen context plan. Restore that snapshot, or type --context-plan "
            f"{shlex.quote(plan or '')} to capture the user's plan again."
        )

    header_sha256 = api.header_identity(base=cr.base, head=cr.head, focus=focus,
                                        plan=plan, plan_sha256=sha)
    changed = record is not None and rec.get("header_sha256") != header_sha256
    reasons: List[str] = []
    if changed:
        if focus != rec_focus:
            if focus is None:
                reasons.append(f"focus cleared (was {_quoted(rec_focus)})")
            elif rec_focus is None:
                reasons.append(f"focus {_quoted(focus)} added")
            else:
                reasons.append(f"focus {_quoted(rec_focus)} became {_quoted(focus)}")
        if plan != rec_plan:
            if plan is None:
                reasons.append(f"context plan {rec_plan} cleared")
            elif rec_plan is None:
                reasons.append(f"context plan {plan} added")
            else:
                reasons.append(f"context plan {plan} replaces {rec_plan}")
        elif sha != rec_sha:
            reasons.append(f"context plan {plan} changed")
        if not reasons:
            reasons.append("the review's identity changed")

    if check_plan and not quiet and typed.context_plan is None and rec_plan:
        current = api.file_sha256(_plan_file(rec_plan, root))
        if current != rec_sha:
            print(
                f"{CONTEXT_PLAN_CHANGED} {rec_plan} differs from the snapshot this review "
                f"uses ({(rec_sha or '')[:12]}); type --context-plan {rec_plan} to review "
                f"against the new text"
            )
    return _Identity(focus=focus, plan=plan, plan_snapshot=snapshot, plan_sha256=sha,
                     header_sha256=header_sha256, changed=changed, reasons=reasons,
                     plan_data=plan_data, plan_source=plan_source)


def _print_kept(typed: _Typed, rec_focus: Optional[str], rec_plan: Optional[str],
                rec_sha: Optional[str], pinned: str, root: Path, cwd: str) -> None:
    """apply-commit-fixes' ``[COMMIT_REVIEW_KEPT]`` for each typed value that
    is not what the review on record used."""
    checks: List[Tuple[str, str, str]] = []
    if typed.focus is not None and (typed.focus or None) != rec_focus:
        checks.append(("--focus", typed.focus,
                       shlex.quote(rec_focus) if rec_focus else "none"))
    if typed.context_plan is not None:
        if typed.context_plan == "":
            differs = rec_plan is not None
        else:
            try:
                plan, _source, data = _read_typed_plan(typed.context_plan, root, cwd)
                differs = plan != rec_plan or hashlib.sha256(data).hexdigest() != rec_sha
            except CommitReviewError:
                differs = True
        if differs:
            checks.append(("--context-plan", typed.context_plan, rec_plan or "none"))
    for flag, value, recorded in checks:
        shown = shlex.quote(value)
        print(
            f"{COMMIT_REVIEW_KEPT} {flag} {shown} is not what the review on record used "
            f"({recorded}); applying that review. To review with it: --review-commits "
            f"{pinned} {flag} {shown}, then --apply-commit-fixes {pinned}, or "
            f"--improve-commits {pinned} {flag} {shown}"
        )


# ---------------------------------------------------------------------------
# Step 4: ownership
# ---------------------------------------------------------------------------


def _lock_dir(mode: str, brief: Path) -> Tuple[str, Path]:
    """``(phase word, dir)`` whose ``.lock`` the door holds for its writes:
    ``apply-fixes/`` for apply-commit-fixes (its own ``commit_range`` writes),
    else the review phase dir (a header rewrite changes the review's inputs)."""
    out = output_dir_for_brief(brief)
    if mode == "apply-commit-fixes":
        return "apply-code-fixes", out / _APPLY_DIR
    return "code-review", out / _REVIEW_DIR


def _owner_of(mode: str, brief: Path, *, reattaching: bool = False) -> Any:
    """The live run owning a dir this door writes, or None; read-only.

    improve-commits (and ``util commit-brief``, its native preparation) asks
    what the composite's preflight asks: its run dir and both step dirs. The
    phase doors ask about their one dir: a live ``run`` record or a held lock.
    """
    # Imported here: a commit front door's `--help` loads only its base modules.
    from . import improve_workflow

    if mode == "improve-commits":
        return improve_workflow.live_owner(mode, brief, skip_own_run_dir=reattaching)
    phase, directory = _lock_dir(mode, brief)
    return improve_workflow._inspect(str(brief), phase, directory)  # noqa: SLF001


def _owner_refusal(door: str, owner: Any) -> str:
    age = owner.heartbeat_age_s
    shown = _shown_path(owner.directory).rstrip("/") + "/"
    lines = [
        f"ERROR: {door}: a live run owns {shown} ({owner.holder}, pid "
        f"{owner.pid or 'unrecorded'}, {owner.verdict}, last heartbeat "
        f"{'never' if age is None else f'{age:.0f}s ago'}). Two runs must not write one "
        f"phase dir, so nothing was started; brief and state left unchanged.",
        f"       Watch it: {owner.status_command}",
    ]
    if owner.abort_command:
        lines.append(f"       Abort it: {owner.abort_command}")
    lines.append("       Then run this command again; it continues from what that run leaves.")
    return "\n".join(lines)


def _take_lock(mode: str, door: str, brief: Path) -> Any:
    """The door's lock, taken non-blocking with the composite step lock's
    retry (a ``status`` poll probes every lock by taking it); a refusal is
    the live-run exit 3."""
    # Imported here: a commit front door's `--help` loads only its base modules.
    from . import detach, improve_workflow

    phase, directory = _lock_dir(mode, brief)
    directory.mkdir(parents=True, exist_ok=True)
    lock = process_control.PhaseLock(detach.lock_path(str(directory)))
    payload = {
        "holder": f"{door} front door",
        "mode": mode,
        "pid": os.getpid(),
        "process_start_time": process_control.process_start_time(os.getpid()),
        "acquired_at": datetime.now().isoformat(),
    }
    refused: Any = None
    for attempt in range(improve_workflow.STEP_LOCK_ATTEMPTS):
        if attempt:
            time.sleep(improve_workflow.STEP_LOCK_RETRY_S)
        try:
            lock.acquire(payload)
        except process_control.LockUnavailable as exc:
            refused = exc
            continue
        # Before the door's first write: an earlier run's teardown not
        # confirmed refuses as a live run does (docs/development/runtime.md).
        try:
            detach.refuse_unconfirmed_cleanup(str(directory), plan_file=str(brief),
                                              phase=phase, lock=lock)
        except detach.DetachError as exc:
            raise _stop(str(exc), _EXIT_NEEDS_HUMAN) from exc
        return lock
    owner = improve_workflow._inspect(str(brief), phase, directory) or improve_workflow.LiveOwner(  # noqa: SLF001
        directory=str(directory),
        holder=str((refused.holder or {}).get("holder") or "an unrecorded holder"),
        pid=(refused.holder or {}).get("pid"),
        verdict=process_control.holder_verdict(refused.holder or None),
        heartbeat_age_s=None,
        status_command=detach.status_command_for(str(brief), phase=phase),
        abort_command=None,
    )
    raise _stop(_owner_refusal(door, owner), _EXIT_NEEDS_HUMAN)


# ---------------------------------------------------------------------------
# Steps 5 and 6: the brief, the snapshot, the archive and the record
# ---------------------------------------------------------------------------


@dataclass
class _Decision:
    """What steps 5 and 6 publish: done in place in the foreground, staged
    under ``--detach`` and applied by the worker once it owns the dir."""

    header: Optional[str]                    # header text to write; None: brief left as is
    exclusive: bool                          # the header creates the brief
    restart: bool                            # archive the old round first
    reasons: List[str]
    fields: Dict[str, Any]                   # the commit_range fields to record
    refresh_plan_hash: bool
    snapshot_source: Optional[str] = None
    snapshot_data: Optional[bytes] = None


def _current_header(brief: Path) -> Optional[str]:
    try:
        text = brief.read_text(encoding="utf-8", errors="surrogateescape")
    except OSError:
        return None
    return _brief_api().split_brief(text)[0]


def _unread_record(brief: Path) -> Optional[str]:
    """Why the brief's existing ``state.json`` gave no ``commit_range``, as a
    ``[COMMIT_REVIEW_RESTARTED]`` reason; None when there is no file (an entry
    cut off before its first record, so no round has run on it)."""
    path = output_dir_for_brief(brief) / "state.json"
    if not path.exists():
        return None
    why = "did not parse" if _unparseable_state(path) else "records no commit range"
    return (f"{_shown_path(path)} {why}, so the header the earlier round reviewed is "
            f"unknown and this one differs")


def _decide(mode: str, cr: Any, view: Any, record: Optional[Mapping[str, Any]],
            ident: _Identity, brief: Path, root: Path, size: Any,
            drifted: Optional[Sequence[str]]) -> _Decision:
    """Steps 5 and 6, decided: which header (if any) to write, whether the
    round restarts, and the ``commit_range`` fields this entry records."""
    api = _brief_api()

    def render() -> str:
        return api.render_brief_header(view, cwd=str(root), focus=ident.focus, plan=ident.plan,
                                       plan_snapshot=ident.plan_snapshot,
                                       plan_sha256=ident.plan_sha256)

    exists = brief.is_file()
    header: Optional[str] = None
    exclusive = restart = refresh = False
    reasons = list(ident.reasons)
    if mode != "apply-commit-fixes":
        if record is None:
            text = render()
            if not exists:
                header, exclusive = text, True
            elif _current_header(brief) != text:
                header, refresh = text, True
                unread = _unread_record(brief)
                if unread is not None:
                    # A state.json is there but gives no record (it does not
                    # parse, is `[]`, or holds no range), so nothing says
                    # which header the round in code-review/ was reviewed
                    # against, and this one differs: a changed --focus would
                    # otherwise resume the old per-model results, report.md
                    # and selections under a new brief. The round is set
                    # aside and restarted, as a recorded identity change is.
                    restart = True
                    reasons.append(unread)
        elif ident.changed:
            header, restart = render(), True
            exclusive, refresh = not exists, exists
        elif not exists:
            header, exclusive = render(), True
        else:
            # A reuse: the header must be the recorded identity's. A crash
            # between an earlier entry's step-5 header write and its step-6
            # record leaves a header the record does not describe (review
            # fix 3, A3); it is rewritten here, so a continuation never
            # reviews against it. Unchanged bytes are left alone.
            text = render()
            if _current_header(brief) != text:
                header, refresh = text, True

    fields: Dict[str, Any] = {
        "brief": git_path(brief, repo_root=root),
        "resolved_at": _now_iso(),
        "size": size.to_record(),
    }
    if drifted is not None:
        fields["drifted"] = list(drifted)
    if record is None:
        fields = {**cr.to_record(), **fields, **ident.fields()}
    elif ident.changed:
        fields.update(ident.fields())
    snapshot = ident.plan_data is not None and mode != "apply-commit-fixes"
    return _Decision(
        header=header, exclusive=exclusive, restart=restart, reasons=reasons,
        fields=fields, refresh_plan_hash=refresh,
        snapshot_source=ident.plan_source if snapshot else None,
        snapshot_data=ident.plan_data if snapshot else None,
    )


def _dropped_line(counts: Any, where: str) -> str:
    return (
        f"{COMMIT_DECISIONS_DROPPED} {counts.skips} skips, {counts.overrides} valid/invalid "
        f"overrides, {counts.edited} edited descriptions in {where} are not applied to the "
        f"new round; mark them again in its report"
    )


def _publish_brief(brief: Path, decision: _Decision, *, keep_extra: Sequence[str] = (),
                   announce: bool = True) -> None:
    """Step 5's writes, in the order a crash can survive: the old round's
    completion is popped, the round moves out, then the snapshot, then the
    header (a crash between them keeps the old identity, so the next typed
    change restarts again, and never leaves the archived round reading as a
    completed review)."""
    api = _brief_api()
    out = output_dir_for_brief(brief)
    if decision.restart:
        _clear_review_completion(brief)
        review_dir = out / _REVIEW_DIR
        counts = api.count_decisions(review_dir) if review_dir.is_dir() else None
        archive = api.archive_round(review_dir, keep_extra=keep_extra) if review_dir.is_dir() else None
        if archive is not None:
            shown = _shown_path(archive).rstrip("/") + "/"
            print(f"{COMMIT_REVIEW_ARCHIVED} {shown}")
            if counts is not None and counts.any():
                print(_dropped_line(counts, shown))
    if decision.snapshot_data is not None:
        api.snapshot_context_plan(decision.snapshot_source or "", out, data=decision.snapshot_data)
    if decision.header is not None:
        brief.parent.mkdir(parents=True, exist_ok=True)
        if decision.exclusive or not brief.exists():
            api.write_brief(brief, decision.header, exclusive=True)
        else:
            api.write_brief(brief, decision.header)
    if decision.restart and announce:
        print(f"{COMMIT_REVIEW_RESTARTED} {'; '.join(decision.reasons)}")


def _unparseable_state(path: Path) -> bool:
    """Whether *path* exists but is not a JSON object: the file
    ``record_commit_range`` replaces with a fresh initial state."""
    if not path.exists():
        return False
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return True
    return not isinstance(loaded, dict)


def _record_state(brief: Path, fields: Mapping[str, Any], refresh_plan_hash: bool) -> None:
    """Step 6: ``StateManager.record_commit_range``, which creates
    ``state.json`` with the ordinary initial state when there is none, and
    replaces one that does not parse. That replacement drops every
    record the earlier round left, while the apply door refuses the same
    file loudly, so it is said in one ``[STATE_REPLACED]`` line."""
    # Imported here: a commit front door's `--help` loads only its base modules.
    from .state_manager import StateManager

    manager = StateManager(brief)
    replaced = _unparseable_state(Path(manager.state_file))
    manager.record_commit_range(fields, refresh_plan_hash=refresh_plan_hash)
    if replaced:
        print(f"{STATE_REPLACED} {_shown_path(manager.state_file)} did not parse; a "
              f"fresh state was written and the earlier round's records are gone")


def _clear_review_completion(brief: Path) -> None:
    """A restart's first write, before the old round moves out: pop
    ``phases_completed["code-review"]`` under ``state_file_lock`` (an empty
    ``record_commit_range``, which keeps every recorded field). The review
    stops reading as completed now, not only when review-code's ``--force``
    gets to it: a phase that never runs, a worker that dies or a crash
    between the archive and step 6 would otherwise leave an archived round
    standing as a completed review (review fix 3, item 3).

    A ``state.json`` that does not parse holds no completion to pop, and is
    left for step 6: replacing it here would leave that write nothing to say
    ``[STATE_REPLACED]`` about."""
    # Imported here: a commit front door's `--help` loads only its base modules.
    from .state_manager import StateManager

    if _unparseable_state(output_dir_for_brief(brief) / "state.json"):
        return
    StateManager(brief).record_commit_range({}, clear_phases=("code-review",))


def _write_stage(directory: Path, *, mode: str, brief: Path, cr: Any, base_ref: str,
                 decision: _Decision, typed_force: bool) -> Path:
    """Stage what steps 5 and 6 decided under a launch-unique name in
    *directory*, created exclusively; the worker applies it after its lock."""
    directory.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": _STAGE_VERSION,
        "mode": mode,
        "brief": str(brief),
        "base": cr.base,
        "head": cr.head,
        "diff_base": base_ref,
        "header": decision.header,
        "restart": decision.restart,
        "reasons": decision.reasons,
        "refresh_plan_hash": decision.refresh_plan_hash,
        "fields": decision.fields,
        "snapshot": (
            None if decision.snapshot_data is None else {
                "source": decision.snapshot_source,
                "data": base64.b64encode(decision.snapshot_data).decode("ascii"),
            }
        ),
        # The live-run decision is the typed flags': detach.launch reads this.
        "typed_force": bool(typed_force),
        "created_at": _now_iso(),
    }
    data = json.dumps(payload, indent=2).encode("utf-8")
    path = directory / f"{STAGE_PREFIX}{uuid.uuid4().hex}{STAGE_SUFFIX}"
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0),
                         0o600)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    return path


def apply_stage(stage: PathLike) -> None:
    """Apply a ``--detach`` launch's stage, in the worker, once it owns the dir.

    Called by ``detach.RunHandle`` right after ``_acquire_lock`` (a worker
    that loses the lock applies nothing; the worker's entry hands it over,
    :func:`hand_worker_the_stage_applier`): the restart's archive, the new
    context-plan snapshot, the new header, then ``commit_range`` through
    ``StateManager.record_commit_range``; then the stage is deleted. The
    archive and dropped-decision lines go to the worker's log. A stage that
    is already gone is a no-op.
    """
    path = Path(stage)
    data = read_stage(path)
    if data is None:
        return
    snapshot = data.get("snapshot") if isinstance(data.get("snapshot"), Mapping) else None
    decision = _Decision(
        header=data.get("header"),
        exclusive=False,
        restart=bool(data.get("restart")),
        reasons=[str(reason) for reason in (data.get("reasons") or ())],
        fields=dict(data.get("fields") or {}),
        refresh_plan_hash=bool(data.get("refresh_plan_hash")),
        snapshot_source=(snapshot or {}).get("source"),
        snapshot_data=(base64.b64decode(snapshot["data"]) if snapshot else None),
    )
    brief = Path(str(data["brief"]))
    _publish_brief(brief, decision, keep_extra=(path.name,), announce=False)
    _record_state(brief, decision.fields, decision.refresh_plan_hash)
    try:
        path.unlink()
    except FileNotFoundError:
        pass


def hand_worker_the_stage_applier(argv: Optional[Sequence[str]] = None) -> None:
    """In a detached worker (*argv*, default ``sys.argv[1:]``, carries
    ``--internal-worker``), hand ``detach`` :func:`apply_stage`, which it calls
    right after the worker's lock. ``detach`` sits below this module and imports
    nothing above its layer (docs/development/dispatcher.md#import-layers).

    Every entry a staged worker starts from calls this before its phase: the
    dispatcher (``multi_llm.main``) and, run directly by path or ``-m``, the
    orchestrators the front doors run (``code_review_orchestrator``,
    ``apply_code_fixes_orchestrator``, ``improve_commits_orchestrator``). Any
    other process is handed nothing.
    """
    # Imported here: a commit front door's `--help` loads only its base modules.
    from .detach import register_commit_stage_applier

    tokens = sys.argv[1:] if argv is None else argv
    if INTERNAL_FLAG_PREFIX + "worker" in tokens:
        register_commit_stage_applier(apply_stage)


def header_identity(*, base: Optional[str], head: str, focus: Optional[str],
                    plan: Optional[str], plan_sha256: Optional[str]) -> str:
    """``commit_range.header_sha256`` (``commit_brief.header_identity``)."""
    return _brief_api().header_identity(base=base, head=head, focus=focus, plan=plan,
                                        plan_sha256=plan_sha256)


# ---------------------------------------------------------------------------
# prepare: steps 1 to 6
# ---------------------------------------------------------------------------


@dataclass
class Prepared:
    """What steps 1 to 6 left in place, for step 7 or ``util commit-brief``."""

    mode: str
    door: str
    brief: Path
    commit_range: Any                    # commit_range.CommitRange (the block's view)
    record: Dict[str, Any]               # commit_range as recorded (or staged)
    restart: bool
    stage: Optional[Path]
    remaining: List[str]                 # the argv without the front-door tokens
    lock: Any                            # the held PhaseLock (foreground), or None
    payload: Dict[str, Any]              # the result line's commit_range
    root: Path
    diff_base: str
    reasons: List[str] = field(default_factory=list)
    reattach: bool = False               # --detach --if-not-running onto a live run
    dropped_line: Optional[str] = None   # the launcher's post-launch decisions line

    def release(self) -> None:
        """Drop the door's lock, if held. Idempotent."""
        lock, self.lock = self.lock, None
        if lock is not None:
            lock.release()


def _refuse_before_step1(mode: str, typed: _Typed, detaching: bool) -> None:
    """The composite's refusals that must come before any write."""
    if mode != "improve-commits":
        if mode == "review-commits" and detaching and typed.flag("files_from") == "-":
            # ``code_review_orchestrator`` imports this module: a load-time cycle.
            import code_review_orchestrator as review_code

            raise _stop(f"ERROR: {review_code.FILES_FROM_STDIN_DETACHED}", _EXIT_ERROR)
        return
    # Imported here: a commit front door's `--help` loads only its base modules.
    from . import improve_workflow

    if typed.flag("interactive"):
        raise _stop(improve_workflow.interactive_refusal(mode), _EXIT_NEEDS_HUMAN)
    if detaching and typed.flag("files_from") == "-":
        raise _stop(improve_workflow.files_from_stdin_refusal(), _EXIT_ERROR)


def prepare(mode: str, argv: Sequence[str], *, util: bool = False) -> Prepared:
    """Steps 1 to 6 for *mode* (``util``: ``util commit-brief``).

    Prints the commit block, ``[COMMIT_BRIEF]`` and every marker a step owes;
    returns with the door's lock held in the foreground (the caller releases
    it). Raises :class:`FrontDoorExit` for a stop, its lines printed.
    """
    if mode not in COMMIT_MODES:
        raise ValueError(f"not a commit mode: {mode!r}")
    # Imported here: a commit front door's `--help` loads only its base modules.
    from .commit_range import RangeError

    door = _door_word(mode, util)
    try:
        return _prepare(mode, list(argv), util=util, door=door)
    except RangeError as exc:
        raise _stop(exc.message, exc.exit_code) from None
    except CommitReviewError as exc:
        raise _stop(exc.message, exc.exit_code) from None
    except ConfigError as exc:
        raise _stop(f"ERROR: {exc}; nothing was written", _EXIT_NEEDS_HUMAN) from None


def _prepare(mode: str, argv: List[str], *, util: bool, door: str) -> Prepared:
    # Imported here: a commit front door's `--help` loads only its base modules.
    from .commit_range import diff_base, measure_range, render_commit_block, render_drift_line
    from .commit_range import result_payload

    cwd = os.getcwd()
    typed = _parse_door(mode, argv, door=door)
    detaching = bool(typed.flag("detach")) and not util
    _refuse_before_step1(mode, typed, detaching)
    root = repo_root_of(cwd)

    # -- step 1: the range ---------------------------------------------------
    resolution = _resolve(mode, typed, root, cwd)
    cr = resolution.cr

    # -- step 2: the block ---------------------------------------------------
    brief: Optional[Path] = resolution.brief
    brief_error: Optional[BaseException] = None
    if brief is None:
        try:
            brief = brief_path_for(cr.base, cr.head, anchor=root)
        except (ConfigError, ValueError) as exc:
            brief_error = exc
    record = resolution.record if resolution.brief is not None else (
        read_commit_range(brief) if brief is not None else None)
    view = _block_view(cr, record)
    try:
        size = measure_range(cr, cwd=str(root))
    except GitError as exc:
        raise CommitReviewError(f"ERROR: {exc}", exit_code=_EXIT_ERROR) from None
    drifted: Optional[List[str]] = None
    extra: List[str] = []
    if util or mode in ("review-commits", "improve-commits"):
        drifted, total = _drift(cr, typed, root)
        line = render_drift_line(drifted, total, cr.head)
        if line:
            extra.append(line)
    if resolution.selected_line:
        extra.append(resolution.selected_line)
    max_commits = _brief_api().BRIEF_MAX_COMMITS
    on_disk = brief is not None and brief.is_file()
    pointer = _shown_path(brief) if on_disk else None
    block = render_commit_block(view, size=size, brief_pointer=pointer,
                                brief_max_commits=max_commits, extra_lines=extra)
    for line in block:
        print(line)
    payload = result_payload(view, size=size, brief=pointer, brief_on_disk=on_disk,
                             drifted=drifted or (), selected=resolution.selected,
                             brief_max_commits=max_commits)
    # The block exactly as printed, as `commit_fixes` carries its own: a tool
    # route relays these lines and composes none (its server holds no word).
    payload["lines"] = list(block)
    record_commit_range_result(payload)

    if mode == "apply-commit-fixes" and resolution.selected is None and brief is not None:
        # Imported here: a commit front door's `--help` loads only its base modules.
        from . import commit_apply

        commit_apply.require_completed_review(brief, pinned=cr.pinned or _shown_path(brief), cwd=str(root))

    # -- step 3: the folder and the identity (reads only) --------------------
    if brief_error is not None:
        raise brief_error
    assert brief is not None
    folder = get_commit_reviews_dir(anchor=root)
    warning = not_ignored_warning(brief.parent, brief)
    if warning:
        print(warning)
    if mode == "apply-commit-fixes" and record is None:
        raise _not_found_no_range(_shown_path(brief))
    check_plan = util or mode in ("review-commits", "improve-commits")
    ident = _identity(mode, cr, record, typed, root, cwd, brief,
                      check_plan=check_plan, quiet=False)
    # The one write before step 4: the folder (with its .gitignore when new)
    # and the brief's empty output and phase dirs, which change no run's inputs.
    if os.path.realpath(brief.parent) == os.path.realpath(folder):
        ensure_commit_reviews_dir(root)
    out = output_dir_for_brief(brief)
    _phase, lock_dir = _lock_dir(mode, brief)
    lock_dir.mkdir(parents=True, exist_ok=True)
    stage_dir = out / mode if (mode == "improve-commits" and detaching) else lock_dir
    stage_dir.mkdir(parents=True, exist_ok=True)
    base_ref = diff_base(cr, cwd=str(root))

    # -- step 4: ownership ---------------------------------------------------
    typed_force = bool(typed.flag("force"))
    reattaching = detaching and bool(typed.flag("if_not_running"))
    lock: Any = None
    reattach = False
    if detaching:
        if mode == "improve-commits":
            owner = _owner_of(mode, brief, reattaching=reattaching)
            if owner is not None:
                raise _stop(_owner_refusal(door, owner), _EXIT_NEEDS_HUMAN)
            if reattaching:
                # Imported here: a commit front door's `--help` loads only its base modules.
                from . import improve_workflow

                reattach = improve_workflow._inspect(  # noqa: SLF001
                    str(brief), mode, out / mode) is not None
        else:
            owner = _owner_of(mode, brief)
            if owner is not None:
                if reattaching:
                    reattach = True
                elif not typed_force:
                    raise _stop(_owner_refusal(door, owner), _EXIT_NEEDS_HUMAN)
    else:
        owner = _owner_of(mode, brief)
        if owner is not None:
            raise _stop(_owner_refusal(door, owner), _EXIT_NEEDS_HUMAN)
        lock = _take_lock(mode, door, brief)

    if reattach:
        # `detach.launch` re-attaches: nothing is staged, nothing moves.
        shown = _shown_path(brief)
        print(f"{COMMIT_BRIEF} {shown}")
        payload = result_payload(view, size=size, brief=shown, brief_on_disk=True,
                                 drifted=drifted or (), selected=resolution.selected,
                                 brief_max_commits=max_commits)
        payload["lines"] = list(block)
        record_commit_range_result(payload)
        return Prepared(mode=mode, door=door, brief=brief, commit_range=view,
                        record=dict(record or {}), restart=False, stage=None,
                        remaining=list(typed.forwarded), lock=None, payload=payload,
                        root=root, diff_base=base_ref, reattach=True)

    stage: Optional[Path] = None
    try:
        # -- step 5: write (or stage) the brief ------------------------------
        dropped_line: Optional[str] = None
        for attempt in range(2):
            decision = _decide(mode, cr, view, record, ident, brief, root, size, drifted)
            try:
                if detaching:
                    if decision.header is not None and decision.exclusive:
                        # The one launcher write: no run can be reading a
                        # brief that does not exist yet.
                        _brief_api().write_brief(brief, decision.header, exclusive=True)
                        decision = replace(decision, header=None, exclusive=False)
                    if decision.restart:
                        review_dir = out / _REVIEW_DIR
                        counts = (_brief_api().count_decisions(review_dir)
                                  if review_dir.is_dir() else None)
                        if counts is not None and counts.any():
                            where = _shown_path(review_dir).rstrip("/") + "/restarted-*/"
                            dropped_line = _dropped_line(counts, where)
                    # [COMMIT_REVIEW_RESTARTED] waits, with the decisions
                    # line, for a worker to consume the stage (_settle_stage):
                    # detach.launch can still refuse, and then nothing restarted.
                    stage = _write_stage(stage_dir, mode=mode, brief=brief, cr=cr,
                                         base_ref=base_ref, decision=decision,
                                         typed_force=typed_force)
                else:
                    _publish_brief(brief, decision)
                break
            except FileExistsError:
                # Lost the exclusive create: the existing-brief path.
                if attempt:
                    raise
                record = read_commit_range(brief)
                view = _block_view(cr, record)
                ident = _identity(mode, cr, record, typed, root, cwd, brief,
                                  check_plan=check_plan, quiet=True)
        shown = _shown_path(brief)
        print(f"{COMMIT_BRIEF} {shown}")

        # -- step 6: record commit_range (staged under --detach) -------------
        if not detaching:
            _record_state(brief, decision.fields, decision.refresh_plan_hash)
        payload = result_payload(view, size=size, brief=shown, brief_on_disk=True,
                                 drifted=drifted or (), selected=resolution.selected,
                                 brief_max_commits=max_commits)
        payload["lines"] = list(block)
        record_commit_range_result(payload)
    except BaseException:
        if lock is not None:
            lock.release()
        if stage is not None:
            try:
                stage.unlink()
            except OSError:
                pass
        raise
    return Prepared(
        mode=mode, door=door, brief=brief, commit_range=view,
        record={**(record or {}), **decision.fields}, restart=decision.restart,
        stage=stage, remaining=list(typed.forwarded), lock=lock, payload=payload,
        root=root, diff_base=base_ref, reasons=list(decision.reasons),
        dropped_line=dropped_line,
    )


# ---------------------------------------------------------------------------
# front_door: steps 1 to 7, then the fronted main
# ---------------------------------------------------------------------------


def _fronted_argv(prep: Prepared) -> Tuple[str, List[str], List[str]]:
    """``(record mode, recorded argv, argv the fronted main is called with)``."""

    forwarded = list(prep.remaining)
    shown = _shown_path(prep.brief)
    stage = [STAGE_FLAG, str(prep.stage)] if prep.stage is not None else []
    head = prep.commit_range.head
    if prep.mode == "review-commits":
        restart: List[str] = []
        if prep.restart:
            restart += [] if flag_present(forwarded, "--force") else ["--force"]
            restart += [] if flag_present(forwarded, "--rerun-all") else ["--rerun-all"]
        argv = forwarded + ["--plan-file", shown, "--base-ref", prep.diff_base,
                            "--head-ref", head] + restart + stage
        return FRONTED[prep.mode], argv, argv
    if prep.mode == "apply-commit-fixes":
        argv = forwarded + ["--plan-file", shown] + stage
        return FRONTED[prep.mode], argv, argv
    restart = ["--force"] if prep.restart and not flag_present(forwarded, "--force") else []
    pinned = prep.commit_range.pinned
    typed_range = ["--revs", pinned] if pinned else ["--plan-file", shown]
    recorded = forwarded + typed_range + restart + stage
    called = forwarded + restart + stage + ["--plan-file", shown, "--base-ref", prep.diff_base,
                                            "--head-ref", head]
    return FRONTED[prep.mode], recorded, called


def _call_main(target: Callable[..., Any], argv: Sequence[str]) -> int:
    """Call a phase's ``main(argv)`` in-process, awaiting it when it is async
    (as the dispatcher's ``_call_target`` does)."""
    if inspect.iscoroutinefunction(target):
        result = asyncio.run(
            process_control.sweeping_live_clis_on_interrupt(target(list(argv)))
        )
    else:
        result = target(list(argv))
    return _EXIT_OK if result is None else int(result)


def _call_fronted(mode: str, argv: Sequence[str]) -> int:
    """The fronted ``main``, looked up at call time."""
    if mode == "review-commits":
        # The fronted orchestrators import this module: a load-time cycle.
        import code_review_orchestrator as target

        return _call_main(target.main, argv)
    if mode == "apply-commit-fixes":
        # A load-time cycle, as for review-commits above.
        import apply_code_fixes_orchestrator as target

        return _call_main(target.main, argv)
    # Imported here: a commit front door's `--help` loads only its base modules.
    from . import improve_workflow

    return int(improve_workflow.entry_point(mode, list(argv)) or 0)


def _settle_stage(prep: Prepared) -> None:
    """After the fronted main: a stage still on disk was never applied (the
    launch was refused or re-attached, or the phase stopped before its
    boundary), so it goes, and no restart is announced; one the worker
    consumed means the round really restarted, so the launcher names the
    decisions it set aside and prints ``[COMMIT_REVIEW_RESTARTED]``, in the
    foreground's order."""
    if prep.stage is None:
        return
    if prep.stage.exists():
        try:
            prep.stage.unlink()
        except OSError:
            pass
        return
    if prep.dropped_line:
        print(prep.dropped_line)
    if prep.restart:
        print(f"{COMMIT_REVIEW_RESTARTED} {'; '.join(prep.reasons)}")


def _improve_worker(argv: Sequence[str]) -> int:
    """The improve-commits front door in its detached child: idempotent.

    Prints no block, takes no ownership, decides no header and writes
    nothing: the launcher did all of that. It takes ``base`` and ``head``
    from the staged record its ``--commit-stage`` names (never from the
    brief's ``state.json``, which the stage has not reached yet on a new
    brief), then calls ``entry_point`` with ``--plan-file <brief> --base-ref
    <base> --head-ref <head>``; the composite's worker branch takes the run
    dir's lock and applies the stage.
    """
    # Imported here: a commit front door's `--help` loads only its base modules.
    from .commit_range import RangeError, diff_base, resolve_range, resolve_recorded

    mode = "improve-commits"
    parser = _door_parser(mode)
    forwarded, own = _split_door_tokens(argv, parser)
    stage = own.get("--commit-stage")
    cwd = os.getcwd()
    try:
        data = read_stage(stage) if stage else None
        if data is not None:
            brief = str(data["brief"])
            head = str(data["head"])
            base_ref = str(data.get("diff_base") or diff_base(data.get("base"), cwd=cwd))
        else:
            root = repo_root_of(cwd)
            brief_arg = own.get("--plan-file")
            if brief_arg:
                record = read_commit_range(brief_arg)
                if record is None:
                    raise _not_found_no_range(brief_arg)
                resolved = resolve_recorded(record, cwd=str(root), label=brief_arg,
                                            recovery="Re-run --improve-commits <range>.")
                brief, head, base_ref = brief_arg, resolved.head, resolved.base_ref
            else:
                cr = resolve_range(own.get("--revs"), cwd=str(root))
                brief = str(brief_path_for(cr.base, cr.head, anchor=root))
                head, base_ref = cr.head, diff_base(cr, cwd=str(root))
    except (RangeError, CommitReviewError) as exc:
        print(exc.message, file=sys.stderr)
        return exc.exit_code
    # Imported here: a commit front door's `--help` loads only its base modules.
    from . import improve_workflow

    called = forwarded + ([STAGE_FLAG, stage] if stage else []) + [
        "--plan-file", brief, "--base-ref", base_ref, "--head-ref", head]
    return int(improve_workflow.entry_point(mode, called) or 0)


def front_door(mode: str, argv: Sequence[str]) -> int:
    """A commit mode: the steps 1 to 7, then the fronted ``main``'s exit.

    ``review-commits`` runs ``code_review_orchestrator.main`` recorded as
    ``review-code``; ``apply-commit-fixes`` runs ``apply_code_fixes_orchestrator.main``
    recorded as ``apply-code-fixes``; ``improve-commits`` runs
    ``improve_workflow.entry_point`` recorded as itself, with the pinned range.
    The door's lock is held through the fronted phase in the foreground, the
    composite included: its code-review lock is handed to the composite
    (``improve_workflow.holding``), whose preflight does not read it as another
    run's and whose review step runs under it rather than taking it again, so
    no other invocation can rewrite or archive the round while the apply step
    reads it. A stage the launch did not consume is deleted.
    """

    if mode not in COMMIT_MODES:
        raise ValueError(f"not a commit mode: {mode!r}")
    tokens = list(argv)
    if flag_present(tokens, "--help", "-h"):
        parse_args(mode, ["--help"])
        return _EXIT_OK
    if mode == "improve-commits" and flag_present(tokens, "--internal-worker"):
        return _improve_worker(tokens)
    try:
        prep = prepare(mode, tokens)
    except FrontDoorExit as stop:
        return stop.exit_code
    try:
        record_mode, recorded, called = _fronted_argv(prep)
        # Step 7, once the brief and commit_range (or the stage carrying
        # them) are in place, so no child reads a record ahead of its inputs.
        record_invocation(record_mode, recorded)
        if mode == "improve-commits" and prep.lock is not None:
            # Imported here: a commit front door's `--help` loads only its base modules.
            from . import improve_workflow

            with improve_workflow.holding(_lock_dir(mode, prep.brief)[1], prep.lock):
                return _call_fronted(mode, called)
        return _call_fronted(mode, called)
    finally:
        prep.release()
        _settle_stage(prep)


# ---------------------------------------------------------------------------
# util commit-brief: steps 1 to 6 on their own
# ---------------------------------------------------------------------------


def commit_brief_main(argv: Optional[Sequence[str]] = None) -> int:
    """``util commit-brief``: the front door's preparation half, launching nothing.

    Takes every token the user typed, range words first. Splits them as the
    dispatcher does (the leading bare words, ``-N`` included, joined, or a
    brief path), runs steps 1 to 6 with the composite's parser (the native
    improve-commits leg is its caller), prints ``[COMMIT_RANGE_PINNED]`` and
    ``[COMMIT_REMAINING_FLAGS]``, and releases ownership on exit. Re-records
    no invocation.
    """

    tokens = list(sys.argv[1:] if argv is None else argv)
    if flag_present(tokens, "--help", "-h"):
        parse_args("commit-brief", ["--help"])
        return _EXIT_OK
    # Imported here: a commit front door's `--help` loads only its base modules.
    from .positionals import revs_flags, split_positionals

    words, flags = split_positionals(tokens, mode_table.resolve(_UTIL_MODE))
    door_argv = revs_flags(words) + list(flags)
    try:
        prep = prepare(_UTIL_MODE, door_argv, util=True)
    except FrontDoorExit as stop:
        return stop.exit_code
    try:
        cr = prep.commit_range
        print(f"{COMMIT_RANGE_PINNED} {cr.base if cr.base is not None else 'root'}..{cr.head}")
        print(f"{COMMIT_REMAINING_FLAGS} {shlex.join(prep.remaining)}".rstrip())
    finally:
        prep.release()
    return _EXIT_OK


def main(argv: Optional[Sequence[str]] = None) -> int:
    """This module's command (``util commit-brief``): :func:`commit_brief_main`."""
    return commit_brief_main(argv)
