"""The plan's task-list marker, ``<!-- TASKS_FILE: tasks/tasks.md -->``, read.

:data:`TASKS_FILE_MARKER_PATTERN` is the one pattern every phase reads it with,
:func:`tasks_marker_spans` says which markers count (not one quoted as code,
:func:`markdown_code_ranges`) and :func:`tasks_marker` reads the first. Text
only, so the output folder's bookkeeping (``output_handler``) reads the marker
without the task-list resolution above it; ``tasks_file`` follows the marker
inside the plan's directory and re-exports every name here
(docs/development/dispatcher.md#import-layers).
"""

import bisect
import re
from typing import List, Optional, Tuple


#: The plan's task-list marker. ``plan_updater.insert_tasks_file_reference``
#: writes the canonical ``<!-- TASKS_FILE: path -->``; the whitespace inside the
#: comment is tolerated, and the value may be empty or span lines, because a
#: reader that misses a marker sees a plan with no task list, and parsing a
#: plan's prose invents tasks. A match counts only outside code
#: (:func:`tasks_marker_spans`). Every reader uses this pattern
#: (docs/development/workflows.md, "Task generation").
TASKS_FILE_MARKER_PATTERN = r"<!--\s*TASKS_FILE:\s*([\s\S]*?)\s*-->"
TASKS_FILE_MARKER_RE = re.compile(TASKS_FILE_MARKER_PATTERN)

_FENCE_OPEN_RE = re.compile(r"[ \t]*(`{3,}|~{3,})(.*)")
_BACKTICK_RUN_RE = re.compile(r"`+")


def markdown_code_ranges(text: str) -> List[Tuple[int, int]]:
    """The ``(start, end)`` offsets of *text* that Markdown shows as code, in order.

    Fenced code blocks (```` ``` ```` or ``~~~``, closed by a run of the same
    character at least as long) and inline code spans (a backtick run closed
    by one of the same length inside the same paragraph). Two departures from
    CommonMark, each on the side of a marker counting: a fence still open at
    the end of the text is not code, and an HTML block (a line opening with
    ``<!--``, through the line that closes it) holds no inline code, so a
    stray backtick in a paragraph never hides the marker line after it.
    """
    ranges: List[Tuple[int, int]] = []
    fence: Optional[Tuple[str, int, int]] = None  # (character, length, start)
    in_comment = False
    paragraph: Optional[List[int]] = None  # [start, end]

    def close_paragraph() -> None:
        nonlocal paragraph
        if paragraph is not None:
            ranges.extend(_inline_code_ranges(text, paragraph[0], paragraph[1]))
            paragraph = None

    pos, size = 0, len(text)
    while pos < size:
        newline = text.find("\n", pos)
        end = size if newline == -1 else newline + 1
        line = text[pos:end].rstrip("\r\n")
        if fence is not None:
            char, length, start = fence
            if re.fullmatch(rf"[ \t]*{re.escape(char)}{{{length},}}[ \t]*", line):
                ranges.append((start, end))
                fence = None
        elif in_comment:
            in_comment = "-->" not in line
        elif _opens_fence(line):
            close_paragraph()
            run = _FENCE_OPEN_RE.match(line).group(1)  # type: ignore[union-attr]
            fence = (run[0], len(run), pos)
        elif not line.strip():
            close_paragraph()
        elif line.lstrip().startswith("<!--"):
            close_paragraph()
            in_comment = "-->" not in line.lstrip()[4:]
        elif paragraph is None:
            paragraph = [pos, end]
        else:
            paragraph[1] = end
        pos = end
    close_paragraph()
    ranges.sort()
    return ranges


def _opens_fence(line: str) -> bool:
    match = _FENCE_OPEN_RE.match(line)
    if match is None:
        return False
    # A backtick fence's info string holds no backtick (```` ```a``` ```` is
    # inline code, not a fence).
    return not (match.group(1)[0] == "`" and "`" in match.group(2))


def _inline_code_ranges(text: str, start: int, end: int) -> List[Tuple[int, int]]:
    ranges: List[Tuple[int, int]] = []
    pos = start
    while True:
        opener = _BACKTICK_RUN_RE.search(text, pos, end)
        if opener is None:
            return ranges
        closer = next(
            (
                run for run in _BACKTICK_RUN_RE.finditer(text, opener.end(), end)
                if len(run.group(0)) == len(opener.group(0))
            ),
            None,
        )
        if closer is None:  # an unmatched run is literal backticks
            pos = opener.end()
            continue
        ranges.append((opener.start(), closer.end()))
        pos = closer.end()


def tasks_marker_spans(plan_text: str) -> List[Tuple[int, int, str]]:
    """Every marker that counts, as ``(start, end, path as written)``, in plan order.

    A marker inside fenced code or inline code is an example of the syntax,
    not the plan's marker (:func:`markdown_code_ranges`). The writer,
    ``plan_updater.insert_tasks_file_reference``, rewrites exactly these.
    """
    code = markdown_code_ranges(plan_text)
    starts = [start for start, _ in code]
    spans: List[Tuple[int, int, str]] = []
    pos = 0
    while True:
        match = TASKS_FILE_MARKER_RE.search(plan_text, pos)
        if match is None:
            return spans
        index = bisect.bisect_right(starts, match.start()) - 1
        if index >= 0 and match.start() < code[index][1]:
            # Quoted as code. Search on from the next character, not past the
            # match: an example left unclosed would otherwise swallow the
            # plan's own marker after it.
            pos = match.start() + 1
            continue
        spans.append((match.start(), match.end(), match.group(1).strip()))
        pos = match.end()


def tasks_marker(plan_text: str) -> Optional[str]:
    """The path the plan's first ``TASKS_FILE`` marker names, as written.

    ``None`` when the plan carries no marker outside code. A marker naming
    nothing gives ``""``: it is still a marker, so a plan carrying one is not
    the legacy format and its prose is never parsed into tasks. A plan whose
    markers disagree is refused by :func:`resolve_tasks_marker`, not here.
    """
    spans = tasks_marker_spans(plan_text)
    return spans[0][2] if spans else None
