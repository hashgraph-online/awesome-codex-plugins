"""The dispatcher's positional grammar, shared with the commit front door.

Which leading tokens of a mode's argv are positionals (:func:`split_positionals`),
and a commit mode's range words as the flag its front door parses
(:func:`revs_flags`). ``multi_llm.py`` splits every invocation with them;
``util commit-brief`` (``commit_front_door.commit_brief_main``) splits the
tokens it is given the same way, so the two can never disagree. The generated
CLI surface reads :data:`RANGE_COUNT_WORD` and :data:`COMMIT_BRIEF_SUFFIX`
(``packaging/common/surface.py``). See docs/development/dispatcher.md.
"""

from __future__ import annotations

import os
import re
from typing import List, Optional, Sequence, Tuple

import modes as mode_table

#: A ``-N`` range word: a hyphen and ASCII
#: digits, nothing else. ``-h``, ``-2h``, ``--2``, ``-2.5`` and a lone ``-``
#: are not one; they end the leading run as any flag does.
RANGE_COUNT_WORD = re.compile(r"-[0-9]+")

#: What a commit brief's path ends in (:func:`names_a_commit_brief` asks no
#: other word). Its one spelling: the generated CLI surface reads it as
#: ``revs.brief_suffix``, so a server keeps a ``revs`` value ending in it as
#: one argv element and a brief path holding a space reaches the dispatcher
#: as the one word it turns into ``--plan-file``.
COMMIT_BRIEF_SUFFIX = ".md"


def takes_revs(mode: Optional["mode_table.Mode"]) -> bool:
    """Whether *mode* takes the commit modes' range (``POS_REVS``)."""
    return mode is not None and mode_table.POS_REVS in mode.positionals


def split_positionals(
    rest: Sequence[str], mode: Optional["mode_table.Mode"] = None,
) -> Tuple[List[str], List[str]]:
    """Leading bare words are positionals; everything from the first flag on is
    forwarded verbatim.

    Deliberately not argparse: ``parse_known_args`` can reorder or swallow the
    residual argv, and the residual has to reach the target's own parser exactly
    as the user typed it.

    On a mode that takes a range (``POS_REVS``), a token that fully matches
    ``-[0-9]+`` continues the leading run instead of ending it: ``-2`` is the
    range ``last 2``, never a flag. Only the leading run is scanned, so in
    ``--review-commits --quick -2`` the ``-2`` is forwarded as typed (the front
    door refuses it as a range word after a flag), and every other mode splits
    as it always has: ``--review-code -2`` forwards ``-2``. This is the one
    place that decides what is positional, and it runs before any parser.
    """
    revs = takes_revs(mode)
    index = 0
    while index < len(rest):
        token = rest[index]
        if token.startswith("-") and not (revs and RANGE_COUNT_WORD.fullmatch(token)):
            break
        index += 1
    return list(rest[:index]), list(rest[index:])


def revs_flags(words: Sequence[str]) -> List[str]:
    """The range words of a commit mode, as the flag its front door parses.

    Zero words emit nothing, which means ``HEAD``. One word that is a commit
    brief's path (:func:`names_a_commit_brief`) becomes ``--plan-file``: a
    root range's pinned spelling, and the re-attach a tool route builds, name
    the brief. Anything else is joined with single spaces into one ``--revs``
    value, since revisions never contain spaces (``last 2 commits`` needs no
    quotes). So a markdown path is never a plan on these modes: a plan or a
    README goes to the range grammar, which refuses it naming
    ``--context-plan``.
    """
    if not words:
        return []
    if len(words) == 1 and names_a_commit_brief(words[0]):
        return ["--plan-file", words[0]]
    return ["--revs", " ".join(words)]


def names_a_commit_brief(word: str) -> bool:
    """Whether *word* is a commit brief's path: it ends in
    :data:`COMMIT_BRIEF_SUFFIX` (``.md``), names an existing file and
    ``commit_paths.is_commit_brief`` accepts it.

    One helper decides what a brief is (its marker on line 1, or a
    ``<commit_reviews_dir>/<slug>.md`` path); this only finds the file. A
    relative path that names nothing from here but a file at the root of the
    repository the cwd is in is asked about there: a brief path spelled from
    the root and typed in a subdirectory then becomes ``--plan-file``, and
    ``multi_llm._run_from_repository_root`` moves the command to the root as
    it would for a plan.
    """
    if not word.endswith(COMMIT_BRIEF_SUFFIX):
        return False
    # Imported here to keep multi_llm, which loads this module, light.
    from utils import commit_paths

    if os.path.isfile(word):
        return bool(commit_paths.is_commit_brief(word))
    root = root_holding(word)
    if root is None:
        return False
    return bool(commit_paths.is_commit_brief(os.path.join(root, word), cwd=root))


def root_holding(path: str) -> Optional[str]:
    """The root of the repository the cwd is in, when relative *path* names a
    file there and stays inside it; else ``None``."""
    if not relative_paths([path]):
        return None
    try:
        # Imported here to keep multi_llm, which loads this module, light.
        from utils.git_utils import pin_repo_root

        root, problem = pin_repo_root(os.getcwd())
    except Exception:  # noqa: BLE001 - a convenience: the word stays a range
        return None
    if root is None or problem:
        return None
    candidate = os.path.join(root, path)
    if not (
        os.path.isfile(candidate)
        and inside(os.path.normpath(candidate), root)
        and inside(os.path.realpath(candidate), root)
    ):
        return None
    return root


def inside(path: str, root: str) -> bool:
    return path == root or path.startswith(root.rstrip(os.sep) + os.sep)


def relative_paths(paths: Sequence[Optional[str]]) -> List[str]:
    return [
        path for path in paths
        if path and path != "-" and not path.startswith("~") and not os.path.isabs(path)
    ]
