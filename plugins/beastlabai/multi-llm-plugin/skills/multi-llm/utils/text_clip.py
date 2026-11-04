"""One rule for cutting text a model or a user wrote down to a line's budget.

Fix round 22 (live run 9, #4): every surface that showed a model's words in
a bounded line — ``status``'s progress line naming a declined fix, the
"check findings for review-code" line and the result's ``notice``, the stop
``error``, the batch log lines and the native leg's printed records — cut
them with a bare ``text[:n]``. That stopped mid-word with no mark ("… would
reverse that dec)", "… but scripts/c)"), left a dangling ", )" when the cut
fell after a comma inside the caller's own brackets, and a Codex host relayed
"truncated at 'but scripts/c'" as if that were the text. :func:`clip` is the
one cut: at a word boundary, marked with :data:`ELLIPSIS`, never ending on a
separator, and with every bracket or quote the kept part opened closed again
after the mark, so the caller's own ``(…)`` around it still pairs up.

Pure and import-free (``status`` stays sub-second); :func:`plain_line` moved
here from ``cli_common``, which re-exports it, so the result line's ``error``
and every clipped preview drop the same control characters.
"""

from __future__ import annotations

import re
from typing import Any, List, Tuple

#: The mark a cut text ends with (before any bracket it closes again).
ELLIPSIS = "…"

#: What :func:`plain_line` removes after collapsing whitespace: the C0
#: controls, DEL, the C1 controls and the bidirectional overrides and
#: isolates. A terminal acts on any of them — an ESC sequence can erase or
#: rewrite the line it sits on — and none belongs in a line a host shows.
_CONTROL_CHARACTERS = re.compile(
    "[\x00-\x1f\x7f-\x9f‎‏‪-‮⁦-⁩]"
)

#: Characters a cut never ends on before its mark: a separator or a closing
#: sentence mark left there reads as the start of something the cut dropped
#: (", …", "; …", " — …", "2.…").
DANGLING = " \t,;:.!?/\\|&+=*-–—·"

#: Bracket pairs :func:`clip` closes again after its mark.
_PAIRS = {"(": ")", "[": "]", "{": "}", "“": "”"}
_CLOSING = {closer: opener for opener, closer in _PAIRS.items()}

#: Marks that open and close with the same character.
_TOGGLES = ('"', "`")

#: A cut backs off to the last word boundary only while that keeps at least
#: two thirds of the room (``3 * kept >= 2 * room``, integers, so the
#: OpenCode plugin's copy of this rule decides alike); past it the text is
#: one long token (a path, a URL), which is cut inside rather than dropped.


def plain_line(text: Any) -> str:
    """``text`` as one plain line: whitespace runs collapsed to one space and
    every control character removed (:data:`_CONTROL_CHARACTERS`).

    Fix round 17 (the Fable review of round 16): the stop headline carries a
    task title from tasks.md and the runner's own summary, and ``set_error``
    only collapsed whitespace, so an ANSI sequence in either reached the
    OpenCode tool line, the codex tool result and ``status`` intact."""
    collapsed = " ".join(str(text).split()) if text else ""
    return " ".join(_CONTROL_CHARACTERS.sub("", collapsed).split())


def _closes_quote(text: str, index: int) -> bool:
    """Whether the ``'`` at *index* can close a single quote (not a letter's
    apostrophe, as in "plan's"): something before it and no letter after."""
    after = text[index + 1] if index + 1 < len(text) else " "
    before = text[index - 1] if index else " "
    return not before.isspace() and not after.isalnum()


def _opens_quote(text: str, index: int) -> bool:
    """Whether the ``'`` at *index* opens a single quote: no letter before it
    and something after it."""
    after = text[index + 1] if index + 1 < len(text) else " "
    before = text[index - 1] if index else " "
    return not before.isalnum() and not after.isspace()


def unclosed(text: str) -> List[Tuple[int, str]]:
    """The brackets and quotes *text* opens and never closes, outermost first,
    each as ``(index, mark)``.

    Brackets pair by kind, a closer with no opener is ignored, a closer whose
    opener sits under other open marks closes those too (they were left open
    inside it). ``"`` and backticks toggle. A single quote counts only where
    it cannot be a letter's apostrophe ("plan's", "models'" are not quotes).
    """
    stack: List[Tuple[int, str]] = []

    def close(mark: str) -> bool:
        for depth in range(len(stack) - 1, -1, -1):
            if stack[depth][1] == mark:
                del stack[depth:]
                return True
        return False

    for index, char in enumerate(text):
        if char in _PAIRS:
            stack.append((index, char))
        elif char in _CLOSING:
            close(_CLOSING[char])
        elif char in _TOGGLES:
            if not close(char):
                stack.append((index, char))
        elif char == "'":
            open_here = any(mark == "'" for _, mark in stack)
            if open_here and _closes_quote(text, index):
                close("'")
            elif _opens_quote(text, index):
                stack.append((index, char))
    return stack


def _closers(stack: List[Tuple[int, str]]) -> str:
    return "".join(_PAIRS.get(mark, mark) for _, mark in reversed(stack))


def _cut_at_word(text: str, room: int) -> str:
    """The first *room* characters of *text*, backed off to the last word
    boundary unless that drops more than a third (one long token)."""
    head = text[:room]
    if text[room].isspace():
        return head
    for index in range(len(head) - 1, -1, -1):
        if head[index].isspace():
            return head[:index] if 3 * index >= 2 * room else head
    return head


def _trimmed(kept: str) -> Tuple[str, List[Tuple[int, str]]]:
    """*kept* without a dangling separator or a mark it opens last with
    nothing after it, and the marks still open in what is left."""
    while True:
        kept = kept.rstrip(DANGLING)
        stack = unclosed(kept)
        if stack and stack[-1][0] == len(kept) - 1:
            kept = kept[:-1]
            continue
        return kept, stack


def _cut_inside(flat: str, limit: int) -> str:
    """*flat* cut inside within *limit*, for a head the word-boundary cut
    left nothing of (fix round 23, review of round 22 #5: ``clip("(" *
    5000, 1200)`` was the bare mark): the first characters that fit beside
    the mark and the closers of what they open, a trailing separator
    dropped unless that leaves nothing."""
    room = limit - len(ELLIPSIS)
    while room > 0:
        head = flat[:room]
        kept = head.rstrip(DANGLING) or head.rstrip()
        if not kept:
            break
        clipped = kept + ELLIPSIS + _closers(unclosed(kept))
        if len(clipped) <= limit:
            return clipped
        # Each character dropped takes at most one closer with it.
        room -= (len(clipped) - limit + 1) // 2
    return ELLIPSIS[:limit]


def clip(text: Any, limit: int, *, flatten: bool = True) -> str:
    """*text* within *limit* characters, cut at a word boundary.

    Text that fits comes back unchanged (as a :func:`plain_line` under
    *flatten*, the default). A longer one keeps as many whole words as fit,
    drops a trailing separator (``,``, ``;``, ``:``, ``—``, a full stop…),
    ends in :data:`ELLIPSIS` and then closes every bracket or quote the kept
    part left open, so ``f"({clip(reason, 120)})"`` never reads ``(…, )``
    and never leaves a ``(`` or ``"`` unpaired. A single token longer than
    two thirds of the room (a path, a URL) is cut inside, and so is a head
    made only of openers or separators (:func:`_cut_inside`). The result is
    never longer than *limit*.
    """
    flat = plain_line(text) if flatten else ("" if text is None else str(text))
    if limit is None or len(flat) <= limit:
        return flat
    if limit <= 0:
        return ""
    room = limit - len(ELLIPSIS)
    while room > 0:
        kept, stack = _trimmed(_cut_at_word(flat, room))
        if not kept:
            return _cut_inside(flat, limit)
        clipped = kept + ELLIPSIS + _closers(stack)
        if len(clipped) <= limit:
            return clipped
        room -= len(clipped) - limit
    return ELLIPSIS[:limit]


def was_clipped(text: Any, shown: str, *, flatten: bool = True) -> bool:
    """Whether *shown* (a :func:`clip` of *text*) is shorter than *text*."""
    flat = plain_line(text) if flatten else ("" if text is None else str(text))
    return shown != flat


def without_closing_mark(text: Any) -> str:
    """*text* without one closing full stop or semicolon, for a place that
    puts a separator or a bracket right after it (``<reason>; <reason>``,
    ``(<reason>)``). A line that ends the sentence after it uses
    :func:`with_closing_mark` instead.

    Fix round 26 (live run 11 #10): a batch's declined reason is recorded as
    the batch wrote it, closing stop included, as its reply and the host's
    summary.md carry it; only a line that adds its own mark after the reason
    drops the reason's one (the decline fixture, 2026-10-07, printed "…
    MAX_SPEED.."). One mark at most, and only while text remains, so a
    reason of ``...`` or ``.`` still reads as one (fix round 21). A closing
    ``...`` is an ellipsis, not a stop, and stays whole (fix round 27: the
    executor's sentences read "… MAX_SPEED.." once their own stop no longer
    made it three again).
    """
    stripped = str(text or "").strip()
    if stripped.endswith("..."):
        return stripped
    if stripped[-1:] in (".", ";"):
        trimmed = stripped[:-1].rstrip()
        if trimmed:
            return trimmed
    return stripped


#: The marks that already end a sentence: a line that puts a full stop after
#: a reason adds none after one of these (:func:`with_closing_mark`).
SENTENCE_ENDS: Tuple[str, ...] = (".", "?", "!", ELLIPSIS)

#: What may follow a sentence's own mark and still close it: a closing quote,
#: bracket or code span (``… MAX_SPEED."``, ``… on purpose.)``).
_AFTER_A_SENTENCE_END = "\"'”’»)]}`"

#: A closing mark the line's own full stop takes the place of (``… it;``
#: reads ``… it.``), while text remains before it.
_REPLACED_BY_A_STOP = (";", ",", ":")


def with_closing_mark(text: Any) -> str:
    """*text* ending a sentence, for a line that goes on after it (``—
    <reason> List it …``): one full stop added unless it already ends in
    one of :data:`SENTENCE_ENDS`, after any closing quotes or brackets.

    Fix round 27 (the Fable review of round 26): :func:`without_closing_mark`
    dropped only a closing ``.`` or ``;`` before the line added its own stop,
    so a reason that ended in ``?``, ``!`` or ``…`` (every reason the
    record's 300-character clip cuts ends in ``…``), or in a mark inside a
    closing quote or bracket, printed ``?.``, ``….``, ``."."``. The reason
    keeps its own mark now and the line adds one only where none is: a
    closing ``;``, ``,`` or ``:`` gives way to it, and a reason of ``.`` or
    ``...`` stays as it is. The records keep the reason as written.
    """
    stripped = str(text or "").strip()
    if not stripped:
        return stripped
    if stripped.rstrip(_AFTER_A_SENTENCE_END).endswith(SENTENCE_ENDS):
        return stripped
    if stripped[-1:] in _REPLACED_BY_A_STOP and stripped[:-1].rstrip():
        stripped = stripped[:-1].rstrip()
    return stripped + "."


#: How a notice joins its clauses (:func:`join_clauses`).
CLAUSE_SEPARATOR = "; "


def join_clauses(parts: Any, separator: str = CLAUSE_SEPARATOR) -> str:
    """*parts* as one line, joined by *separator*: each part but the last
    without its one closing full stop or semicolon
    (:func:`without_closing_mark`), the last kept as written.

    Fix round 28 (live run 12 #7): a result's ``notice`` joins clauses that
    are often whole sentences — the tests line, a quoted check finding, a
    declined reason — and a bare ``"; ".join`` printed ``… scripts.test).;
    Opponent speed …`` (Codex decline and accept 02, OpenCode 08), while the
    line that dropped a declined reason's stop to make room for the join
    lost it where nothing followed (OpenCode decline). Every notice join
    goes through here, so a part keeps its own mark when it ends the line
    and gives it up only to the separator. Empty parts are left out.
    """
    if parts is None:
        return ""
    kept = [str(part).strip() for part in parts
            if part is not None and str(part).strip()]
    if not kept:
        return ""
    return separator.join(
        [without_closing_mark(part) for part in kept[:-1]] + [kept[-1]])


def drop_said_clauses(text: Any, said: Any) -> str:
    """*text* without the clauses *said* already carries word for word
    (:func:`plain_line`, closing mark aside): *text* as it is when it repeats
    none, ``""`` when it repeats every one.

    A composite joins the notice each of its phases recorded as if it were the
    only one, and two phases word one fact alike: implement's and
    apply-code-fixes' "Nothing ran this repository's tests: …", which a stop's
    error may end with too (Fable review of D2, 2026-10-27). Split where
    :func:`join_clauses` joins, so a part that repeats one clause of an
    earlier one keeps the rest.
    """
    whole = str(text or "").strip()
    seen = plain_line(said)
    clauses = [clause for clause in whole.split(CLAUSE_SEPARATOR) if clause.strip()]
    kept = [
        clause for clause in clauses
        if plain_line(without_closing_mark(clause)) not in seen
    ]
    if len(kept) == len(clauses):
        return whole
    return with_closing_mark(join_clauses(kept)) if kept else ""
