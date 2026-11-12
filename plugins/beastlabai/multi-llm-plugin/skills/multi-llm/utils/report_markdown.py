"""The report.md grammar: the structure the writers emit and the parsers trust.

A review's ``report.md`` (and ``consolidated-report.md``) is written by the
plugin and read back by the apply phases: a ticked box under a header is a
decision (skip, mark valid or invalid, let the agent decide), and an edited
description is new text for the apply prompt. The same file also carries model
text (titles, themes, descriptions, validation reasons, failure messages), and
that text can quote a hostile plan or repository. This module is the one place
that knows both sides, so model text can never pass for structure:

- **Structure is line-anchored.** A header is read only at column 0 and a box
  only at the start of a line (after optional indentation), one line at a time;
  ``-\\s*\\[`` no longer matches across a line break or in mid-sentence.
- **One structural pass.** :func:`plan_sections` finds every group and
  suggestion header of a plan or task report, the refused ones included, and
  gives each its own region; every decision reader takes its boxes from there,
  so a header one reader refuses never lends its box to another.
- **Model text is written inert.** :func:`inline_text` puts a field on one
  line (header titles, metadata fields), and :func:`neutralize_model_text`
  backslash-escapes every line of a text block that could read as a header
  (``##``), a box (``- [``) or the ``---`` rule that ends a block. The escape
  renders as the same characters and
  :func:`restore_model_text` undoes it exactly, so a description read back for
  an edit is the model's own text, not the escaped copy. Only a report whose
  first line is :data:`ESCAPED_TEXT_MARKER` was written that way
  (:func:`has_escaped_text`); an older one keeps its backslashes.

docs/development/review-results.md ("Report grammar") has the rules.
"""

import re
from typing import Any, Iterator, List, NamedTuple, Optional, Sequence, Tuple

# ---------------------------------------------------------------------------
# Checkboxes
# ---------------------------------------------------------------------------

SKIP = "Skip"
SKIP_GROUP = "Skip this group"
MARK_VALID = "Mark valid"
MARK_INVALID = "Mark invalid"
LET_AGENT_DECIDE = "Let the agent decide"
NEEDS_HUMAN = "Needs human attention"

#: Every box label a writer emits.
CHECKBOX_LABELS: Tuple[str, ...] = (
    SKIP, SKIP_GROUP, MARK_VALID, MARK_INVALID, LET_AGENT_DECIDE, NEEDS_HUMAN,
)

#: What a ticked box says after its brackets, per label. ``Skip`` is not the
#: start of ``Skip this group``; ``Let Claude decide`` is the pre-rename label.
_LABEL_PATTERNS = {
    SKIP: r"skip\b(?![ \t]+this[ \t]+group)",
    SKIP_GROUP: r"skip[ \t]+this[ \t]+group",
    MARK_VALID: r"mark[ \t]+valid",
    MARK_INVALID: r"mark[ \t]+invalid",
    LET_AGENT_DECIDE: r"let[ \t]+(?:claude|the[ \t]+agent)[ \t]+decide",
    NEEDS_HUMAN: r"needs[ \t]+human[ \t]+attention",
}

#: A ticked box at the start of a line: any non-blank mark inside the brackets
#: (``x``, ``X``, ``v``, ``✓``) with optional spaces around it.
_TICKED = r"^[ \t]*-[ \t]*\[[ \t]*[^\]\s]+[ \t]*\][ \t]*"

_TICKED_RE = {
    label: re.compile(_TICKED + pattern, re.MULTILINE | re.IGNORECASE)
    for label, pattern in _LABEL_PATTERNS.items()
}


def checkbox_line(label: str) -> str:
    """The unticked box a writer emits for *label*."""
    if label not in _LABEL_PATTERNS:
        raise ValueError(f"not a report checkbox label: {label!r}")
    return f"- [ ] {label}"


def is_checked(text: str, label: str) -> bool:
    """Whether *text* holds a ticked *label* box on a line of its own."""
    return bool(_TICKED_RE[label].search(text or ""))


def first_checked(text: str, choices: Sequence[Tuple[str, Any]]) -> Any:
    """The value of the first ``(label, value)`` in *choices* ticked in *text*.

    *choices* is in precedence order, so ``invalid`` before ``valid`` before
    ``judge_decide`` makes ``invalid`` win when both are ticked. ``None`` when
    nothing is ticked.
    """
    for label, value in choices:
        if is_checked(text, label):
            return value
    return None


def _next_line(text: str, newline: int) -> Tuple[str, int]:
    """The line after the newline at *newline*, and the index of its own
    newline (``-1`` at the end of *text*)."""
    following = text.find("\n", newline + 1)
    return text[newline + 1:following if following != -1 else len(text)], following


def line_after(text: str, end: int) -> Optional[str]:
    """The line that follows the one ending at *end* (a header match's end)."""
    newline = text.find("\n", end)
    return _next_line(text, newline)[0] if newline != -1 else None


def first_line_after(text: str, end: int) -> Optional[str]:
    """The first non-blank line after the one ending at *end*."""
    newline = text.find("\n", end)
    while newline != -1:
        line, newline = _next_line(text, newline)
        if line.strip():
            return line
    return None


# ---------------------------------------------------------------------------
# Headers
# ---------------------------------------------------------------------------

#: ``## G1 [a1b2c3d4]: Theme`` (v2) or ``## G1: Theme`` (v1, legacy).
GROUP_HEADER_RE = re.compile(
    r"^##[ \t]+G(\d+)(?:[ \t]+\[([0-9a-f]{8,16})\])?:[^\n]*$",
    re.MULTILINE | re.IGNORECASE,
)
#: ``### G1S2 [e5f6a7b8]: Title`` (v2) or ``### G1S2: Title`` (v1, legacy).
SUGGESTION_HEADER_RE = re.compile(
    r"^###[ \t]+(G\d+S\d+)(?:[ \t]+\[([0-9a-f]{8,16})\])?:[^\n]*$",
    re.MULTILINE | re.IGNORECASE,
)
#: ``### S001: Title`` (the flat legacy report).
FLAT_SUGGESTION_HEADER_RE = re.compile(
    r"^###[ \t]+(S\d+):[^\n]*$", re.MULTILINE | re.IGNORECASE,
)
#: ``### 1. Title`` (code review).
ISSUE_HEADER_RE = re.compile(r"^###[ \t]+(\d+)\.[^\n]*$", re.MULTILINE)
#: ``## CG1 [abc123def456]: Title`` (consolidated report).
CONSOLIDATED_HEADER_RE = re.compile(
    r"^##[ \t]+CG\d+[ \t]+\[([0-9a-fA-F]{12})\]:[^\n]*$",
    re.MULTILINE | re.IGNORECASE,
)


def group_header(display_label: str, display_hash: str, theme: Any) -> str:
    """``## G1 [hash]: theme`` (no bracket without a hash), theme on one line."""
    if display_hash:
        return f"## {display_label} [{display_hash}]: {inline_text(theme)}"
    return f"## {display_label}: {inline_text(theme)}"


def suggestion_header(display_label: str, display_hash: str, title: Any) -> str:
    """``### G1S1 [hash]: title`` (no bracket without a hash), title on one line."""
    if display_hash:
        return f"### {display_label} [{display_hash}]: {inline_text(title)}"
    return f"### {display_label}: {inline_text(title)}"


def flat_suggestion_header(suggestion_id: str, title: Any) -> str:
    """``### S001: title``, title on one line."""
    return f"### {suggestion_id}: {inline_text(title)}"


def issue_header(index: int, title: Any) -> str:
    """``### N. title``, title on one line: the Skip box must be the next line."""
    return f"### {index}. {inline_text(title)}"


def consolidated_header(display_index: Any, consolidated_id: str, title: Any) -> str:
    """``## CG1 [id]: title``, title on one line."""
    return f"## CG{display_index} [{consolidated_id}]: {inline_text(title)}"


def hashed_headers(
    content: str, header_re: "re.Pattern[str]",
) -> Tuple[List["re.Match[str]"], bool]:
    """Every *header_re* header in *content*, and whether to trust the unhashed.

    A writer stamps a bracket hash on every group and suggestion header or on
    none (``state_manager._assign_display_hashes``), so a report holding both
    kinds was not written that way: an unhashed ``## G2:`` among hashed ones
    is text that resolves through the legacy index map to a real group. The
    second value is ``False`` then, and callers ignore every unhashed header
    (it still ends the region before it, :func:`plan_sections`). Group 2 of
    *header_re* is the hash.
    """
    matches = list(header_re.finditer(content))
    hashed = any(m.group(2) for m in matches)
    return matches, not hashed


GROUP = "group"
SUGGESTION = "suggestion"

#: Where a header's region ends, besides the next group or suggestion header:
#: a ``---`` rule (the writer closes every group with one) or any other
#: level-2 line (``## Models Failed``, a hand-added ``## Notes``).
_REGION_END_RE = re.compile(r"^(?:---|##(?!#))", re.MULTILINE)


class Section(NamedTuple):
    """A group or suggestion header and the region it owns."""

    kind: str  #: :data:`GROUP` or :data:`SUGGESTION`
    match: "re.Match[str]"  #: the header line; group 2 is its hash
    trusted: bool  #: ``False``: an unhashed header among hashed ones
    body: str  #: from the end of the header line to the end of its region

    def _lines(self) -> List[str]:
        # ``body`` starts with the header line's own newline.
        return self.body.split("\n")[1:]

    def line_under(self) -> Optional[str]:
        """The line right under the header (a suggestion's Skip box)."""
        lines = self._lines()
        return lines[0] if lines else None

    def first_line(self) -> Optional[str]:
        """The first non-blank line under the header (a group's Skip box)."""
        return next((line for line in self._lines() if line.strip()), None)


def plan_sections(content: str) -> List[Section]:
    """Every ``## G{N}`` and ``### G{N}S{M}`` header of a plan or task report,
    in order, each with the region it owns: up to the next such header,
    refused or not, or an earlier ``---`` or ``##`` line.

    The one structural pass every decision reader of these reports uses. A
    region never runs through another header, so a box is read only under the
    header right above it: a group's own boxes stop at its first suggestion,
    the last suggestion of a group stops at the group's closing rule, and a
    refused header (``trusted`` false, :func:`hashed_headers`) keeps its box
    to itself, where every reader ignores it.
    """
    groups, trust_groups = hashed_headers(content, GROUP_HEADER_RE)
    suggestions, trust_suggestions = hashed_headers(content, SUGGESTION_HEADER_RE)
    headers = sorted(
        [(m, GROUP, trust_groups) for m in groups]
        + [(m, SUGGESTION, trust_suggestions) for m in suggestions],
        key=lambda header: header[0].start(),
    )
    found = []
    for i, (match, kind, trust_unhashed) in enumerate(headers):
        end = headers[i + 1][0].start() if i + 1 < len(headers) else len(content)
        rule = _REGION_END_RE.search(content, match.end(), end)
        if rule:
            end = rule.start()
        found.append(Section(
            kind, match, bool(match.group(2)) or trust_unhashed,
            content[match.end():end],
        ))
    return found


def sections(
    content: str, matches: Sequence["re.Match[str]"],
) -> Iterator[Tuple["re.Match[str]", str]]:
    """Each header with its block: the text up to the next header or the end."""
    for i, match in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        yield match, content[match.end():end]


# ---------------------------------------------------------------------------
# Model text
# ---------------------------------------------------------------------------

#: The line breaks a reader sees: ``Path.read_text`` turns ``\r\n`` and a lone
#: ``\r`` into ``\n``, and CommonMark ends a line on all three.
_LINE_BREAK_RE = re.compile(r"\r\n?|\n")

#: A line that could read as structure: after indentation and any run of
#: backslashes, a ``##`` header, a ``- [`` box or a ``---`` rule (where
#: ``report_parser`` ends a description's block, so a quoted diff header or a
#: model's own rule would cut the description there). Escaping adds one
#: backslash to the run and restoring removes one, so the two are exact
#: inverses.
_STRUCTURE_LINE_RE = re.compile(r"^([ \t]*)(\\*)(?=##|-[ \t]*\[|---)", re.MULTILINE)
_ESCAPED_LINE_RE = re.compile(r"^([ \t]*)\\(\\*)(?=##|-[ \t]*\[|---)", re.MULTILINE)


def inline_text(value: Any) -> str:
    """Model text for a header or a metadata field: every line break a space.

    Nothing after a header's prefix or inside a ``**Field:**`` line can open a
    line of its own, so it cannot push the box off the line under the header
    or start a header or a box.
    """
    if value is None:
        return ""
    return _LINE_BREAK_RE.sub(" ", str(value))


def neutralize_model_text(value: Any) -> str:
    """Model text for a block (a description, a reason), inert as structure.

    Line breaks become ``\\n`` and every line that could read as a ``##``
    header, a ``- [`` box or a ``---`` rule gets a backslash before its
    marker: ``\\## G2:``, ``\\- [x] Skip`` and ``\\--- a/app.py`` render as
    the same characters but no parser in ``report_parser`` reads them as
    structure. :func:`restore_model_text` is the inverse.
    """
    if value is None:
        return ""
    text = _LINE_BREAK_RE.sub("\n", str(value))
    return _STRUCTURE_LINE_RE.sub(lambda m: m.group(1) + "\\" + m.group(2), text)


def restore_model_text(text: str) -> str:
    """Undo :func:`neutralize_model_text` on text read back from a report.

    A description parsed out of ``report.md`` is compared with the original
    and, when the user edited it, handed to the apply prompt; both want the
    model's own text, not the escaped copy. Only for a report that
    :func:`has_escaped_text`: in an older one a backslash before ``##``,
    ``- [`` or ``---`` is the model's own and stays.
    """
    if not text:
        return text
    return _ESCAPED_LINE_RE.sub(lambda m: m.group(1) + m.group(2), text)


#: The first line of a ``report.md`` written with :func:`neutralize_model_text`
#: (plan, task and code review). The writers before it put the title there
#: and model text never comes first, so no report can claim it falsely.
ESCAPED_TEXT_MARKER = "<!-- multi-llm:model-text-escaped -->"


def has_escaped_text(content: str) -> bool:
    """Whether *content* (a whole report) starts with :data:`ESCAPED_TEXT_MARKER`,
    so its descriptions are read back through :func:`restore_model_text`."""
    first = (content or "").lstrip("\ufeff").split("\n", 1)[0]
    return first.rstrip() == ESCAPED_TEXT_MARKER


# ---------------------------------------------------------------------------
# Round line
# ---------------------------------------------------------------------------

#: The second line of a ``report.md`` a review round wrote: the round's id,
#: then the digest of the ``validation.json`` its verdicts came from (absent
#: for a report built without one) and of the report's text below the line
#: (``utils/review_round.py``, "the report's seal"). It sits right under
#: :data:`ESCAPED_TEXT_MARKER`, a place no model text reaches, and is absent
#: from a report written before round ids or with no round on record.
ROUND_LINE_RE = re.compile(
    r"<!-- multi-llm:round ([0-9a-f]{16,64})"
    r"(?: validation ([0-9a-f]{16,64}))?"
    r"(?: report ([0-9a-f]{16,64}))? -->"
)


class RoundMark(NamedTuple):
    """What a report's round line records (:data:`ROUND_LINE_RE`)."""

    round_id: str
    validation: Optional[str]
    body: Optional[str]


def round_line(round_id: str, *, validation: Optional[str] = None,
               body: Optional[str] = None) -> str:
    """The line that records *round_id* (and the digests) in a report."""
    parts = [f"<!-- multi-llm:round {round_id}"]
    if validation:
        parts.append(f"validation {validation}")
    if body:
        parts.append(f"report {body}")
    return " ".join(parts) + " -->"


def report_round_mark(content: str) -> Optional[RoundMark]:
    """The round line a report records, or ``None``: read only from the line
    right after :data:`ESCAPED_TEXT_MARKER`, never from anywhere model text is."""
    lines = (content or "").lstrip("\ufeff").split("\n", 2)
    if len(lines) < 2 or lines[0].rstrip() != ESCAPED_TEXT_MARKER:
        return None
    match = ROUND_LINE_RE.fullmatch(lines[1].rstrip())
    return RoundMark(*match.groups()) if match else None


def report_round(content: str) -> Optional[str]:
    """The round id a report records, or ``None`` (:func:`report_round_mark`)."""
    mark = report_round_mark(content)
    return mark.round_id if mark else None


# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------

#: The issue-numbering footer ``generate_review_report`` writes last.
ISSUE_DIGEST_RE = re.compile(
    r"^<!--\s*multi-llm:issues-digest\s+([0-9a-f]{8,64})\s*-->", re.MULTILINE,
)


def issue_digest(text: str) -> Optional[str]:
    """The footer's digest: the last one on a line of its own, since the
    writer puts it after everything else, model text included."""
    found = ISSUE_DIGEST_RE.findall(text or "")
    return found[-1] if found else None
