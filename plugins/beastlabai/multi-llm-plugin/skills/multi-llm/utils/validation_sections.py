#!/usr/bin/env python3
"""Per-batch plan context: the sections a validation batch's suggestions cite.

A validation round embeds the same plan excerpt in every batch, so a 14-batch
round carries the plan 14 times while each batch judges two or four groups
about a few of its sections. This module picks, for one batch, the plan text
those groups cite, so the batch prompt can carry that and a pointer to the
round's whole snapshot instead. It is opt-in
(``MULTI_LLM_VALIDATION_CONTEXT=cited``) until a live comparison shows verdicts
hold up without the rest of the plan; the rule, its fallbacks and the
measurements are in ``docs/development/delegation.md``, "Cited plan sections".

Pure and stdlib-only: :meth:`CitedPlan.select` is a function of the plan text
and the batch's suggestion records, so identical inputs render byte-identical
excerpts, which the prompts' determinism rests on. The caller
(``utils.validation.prepare_batched_validation_tasks``) decides whether a
round may be cited at all: it needs a hash-bound snapshot a validator can read.
"""

from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from .process_state import process_cache
from .validation_context import SELECTION_CITED

#: The environment switch. Unset, every batch embeds the whole plan and a
#: review-code batch carries the code windows its own issues cite; ``cited``
#: also scopes the plan block per batch; ``full`` embeds the round-wide plan and
#: code blocks in every batch. Any other value is reported and read as
#: ``full``, the safe reading.
CITED_CONTEXT_ENV = "MULTI_LLM_VALIDATION_CONTEXT"
CONTEXT_CITED = "cited"
CONTEXT_FULL = "full"

#: Plans shorter than this are embedded whole: the per-batch saving is a few
#: thousand characters and not worth losing the sections a group does not cite.
CITED_MIN_CHARS = 12_000

#: A selection at least this share of the plan is replaced by the whole plan:
#: the saving is small and the whole text is the safer context.
CITED_MAX_SHARE = 0.6

#: How many omitted headings a gap marker names before ``(+n more)``, and how
#: long each name may be.
_GAP_NAMED = 3
_GAP_TITLE_CHARS = 60

_ATX_HEADING = re.compile(r"^(#{1,6})[ \t]+\S")
#: A fence opener: three or more backticks or tildes. A backtick fence's info
#: string holds no backtick (CommonMark), so a line that opens and closes a
#: backtick run is inline code, not a fence.
_FENCE_OPEN = re.compile(r"^[ \t]*(`{3,}|~{3,})(.*)$")
#: A setext underline: a line of ``=`` or ``-`` under a line of text.
_SETEXT_UNDERLINE = re.compile(r"^ {0,3}(?:=+|-+)[ \t]*$")

#: Top-level sections every cited batch carries whatever it cites: a heading
#: at the plan's shallowest section level whose title (without its number)
#: has one of these words. They hold what any suggestion can conflict with —
#: goals, non-goals and scope, constraints and requirements, definitions,
#: assumptions and invariants, decisions taken.
_GLOBAL_TITLE = re.compile(
    r"\b(?:goals?|non-?goals?|objectives?|scope|constraints?|requirements?"
    r"|definitions?|glossary|terminology|assumptions?|invariants?|principles?"
    r"|decisions?)\b"
)

#: Separators between the parts of one ``reference``: ``" / "`` and ``"; "``
#: always split; a comma splits only when what follows looks like another
#: reference, so a heading's own commas (``### Stage A — adapter, registry``)
#: stay inside it.
_REFERENCE_SEPARATOR = re.compile(
    r"\s+/\s+|;\s+|,\s+(?=#|§|\d|(?:stage|phase|step|part|appendix|section)\s)",
    re.IGNORECASE,
)
_NUMBER_KEY = re.compile(
    r"^(?:section\s+|sec\.\s*|§\s*)?(\d+(?:\.\d+)*)\.?(?=$|[\s:)\-,])"
)
_WORD_KEY = re.compile(
    r"^(stage|phase|step|part|appendix|milestone|task)\s+([a-z]|\d+)(?=$|[\s:.)\-,])"
)
#: A letter-and-number id: ``T001``, ``T4.2``, ``D3``, ``R6``.
_ID_KEY = re.compile(r"^([a-z]{1,2}\d+(?:\.\d+)*)(?=$|[\s:.)\-,])")
#: A key in parentheses after the text: ``### Fix (D5)``, ``Retries (§3.2)``.
_QUALIFIER_KEY = re.compile(r"\((?:§\s*)?([a-z]{0,2}\d+(?:\.\d+)*)\)")
_RANGE = re.compile(r"^(?:§\s*)?(\d+(?:\.\d+)*)\s*-\s*(?:§\s*)?(\d+(?:\.\d+)*)$")


_REPORTED_VALUES: set = process_cache("utils.validation_sections._REPORTED_VALUES", set)


def context_setting(environ: Optional[Mapping[str, str]] = None) -> str:
    """:data:`CITED_CONTEXT_ENV` read: ``""`` (unset), ``cited`` or ``full``.

    Any other value is reported once per process and read as ``full``.
    """
    value = (environ if environ is not None else os.environ).get(CITED_CONTEXT_ENV, "")
    value = value.strip().lower()
    if value in ("", CONTEXT_CITED, CONTEXT_FULL):
        return value
    if value not in _REPORTED_VALUES:
        _REPORTED_VALUES.add(value)
        print(
            f"[VALIDATION_CONTEXT_CITED] {CITED_CONTEXT_ENV}={value!r} is not "
            f"'{CONTEXT_CITED}' or '{CONTEXT_FULL}'; embedding the whole plan "
            f"and the round's whole code block in every batch.",
            file=sys.stderr,
        )
    return CONTEXT_FULL


def cited_context_enabled(environ: Optional[Mapping[str, str]] = None) -> bool:
    """Whether a batch's plan block may carry only the sections it cites.

    Only when :data:`CITED_CONTEXT_ENV` is ``cited``: the whole plan stays the
    default until a live check shows verdicts keep their quality without it.
    """
    return context_setting(environ) == CONTEXT_CITED


def batch_code_windows_enabled(environ: Optional[Mapping[str, str]] = None) -> bool:
    """Whether a review-code batch carries only the windows its own issues cite.

    The default; ``full`` (or an unknown value) restores the round-wide block.
    """
    return context_setting(environ) != CONTEXT_FULL


def _normalize(text: str) -> str:
    """Lowercased heading or reference text without ``#``, emphasis or ``§`` marks."""
    text = re.sub(r"^#+\s*", "", text.strip())
    text = text.replace("`", "").replace("*", "")
    text = text.replace("—", "-").replace("–", "-")
    text = text.lower()
    text = re.sub(r"^§+\s*", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text.rstrip(" .:")


def _section_key(norm: str) -> Tuple[Optional[str], str]:
    """``(key, title)``: a numbered or named section key and the text after it."""
    match = _NUMBER_KEY.match(norm)
    if match:
        return _canonical_key(match.group(1)), norm[match.end():].lstrip(" .:)-,")
    match = _WORD_KEY.match(norm)
    if match:
        word, value = match.group(1), match.group(2)
        if value.isdigit():
            value = str(int(value))
        return f"{word} {value}", norm[match.end():].lstrip(" .:)-,")
    match = _ID_KEY.match(norm)
    if match:
        return _canonical_key(match.group(1)), norm[match.end():].lstrip(" .:)-,")
    return None, norm


def _canonical_key(key: str) -> str:
    """``key`` with each number's leading zeros dropped (``2.03`` is ``2.3``)."""
    return re.sub(r"\d+", lambda m: str(int(m.group(0))), key)


def _starts_at_boundary(text: str, prefix: str) -> bool:
    """``text`` starts with ``prefix`` and the next character ends a word."""
    if not prefix or not text.startswith(prefix):
        return False
    return len(text) == len(prefix) or not text[len(prefix)].isalnum()


def _key_tuple(key: Optional[str]) -> Optional[Tuple[int, ...]]:
    if not key or not re.fullmatch(r"\d+(?:\.\d+)*", key):
        return None
    return tuple(int(part) for part in key.split("."))


@dataclass(frozen=True)
class Heading:
    """One ATX heading outside a code fence."""

    offset: int
    level: int
    line: str
    norm: str
    key: Optional[str]
    title: str

    @property
    def name(self) -> str:
        """The heading as a gap marker names it."""
        line = self.line.strip()
        if len(line) > _GAP_TITLE_CHARS:
            line = line[: _GAP_TITLE_CHARS - 1] + "…"
        return line


def _scan(text: str) -> Tuple[List[Heading], List[str]]:
    """``(ATX headings, setext heading lines)`` outside code fences.

    A line scan, not a multiline regex, for the reason
    ``utils.validation._markdown_headings`` gives: a plan's shell blocks are
    full of ``# comment`` lines. A fence closes only on a line of its own
    character at least as long as its opener and nothing else (CommonMark),
    so a four-backtick example that shows a three-backtick block stays one
    fence. Setext headings are found, not parsed: :meth:`CitedPlan.parse`
    marks a plan that has one (or a line that looks like one) as unscoped.
    """
    headings: List[Heading] = []
    setext: List[str] = []
    offset = 0
    fence: Optional[str] = None
    previous = ""
    for line in text.splitlines(keepends=True):
        stripped = line.rstrip("\r\n")
        if fence is not None:
            close = stripped.strip()
            if close.startswith(fence) and set(close) == {fence[0]}:
                fence = None
            previous = ""
        else:
            opener = _FENCE_OPEN.match(stripped)
            if opener and not (
                opener.group(1)[0] == "`" and "`" in opener.group(2)
            ):
                fence = opener.group(1)
                previous = ""
            else:
                match = _ATX_HEADING.match(stripped)
                if match:
                    norm = _normalize(stripped)
                    key, title = _section_key(norm)
                    headings.append(Heading(
                        offset=offset, level=len(match.group(1)), line=stripped,
                        norm=norm, key=key, title=title,
                    ))
                    previous = ""
                elif _SETEXT_UNDERLINE.match(stripped) and previous.strip():
                    setext.append(previous.strip())
                    previous = ""
                else:
                    previous = stripped
        offset += len(line)
    return headings, setext


def markdown_headings(text: str) -> List[Heading]:
    """Every ATX heading (levels 1-6) outside code fences, in document order."""
    return _scan(text)[0]


def split_reference(reference: Any) -> List[str]:
    """The non-empty parts of one suggestion's ``reference``."""
    if isinstance(reference, (list, tuple)):
        reference = " / ".join(str(part) for part in reference if part)
    text = str(reference or "").strip()
    if not text:
        return []
    return [part.strip() for part in _REFERENCE_SEPARATOR.split(text) if part.strip()]


def resolve_part(part: str, headings: Sequence[Heading]) -> List[int]:
    """Indices into ``headings`` that ``part`` names; ``[]`` when none does.

    The first rule that matches anything decides, and every heading it matches
    is taken (two headings sharing a key both come along: more context is the
    safe side of an ambiguity):

    1. the part is the heading, or its start up to a word boundary
       (``## 2`` names ``## 2. Uploads``); a part with no section key also
       names every heading whose title without its key it starts, so
       ``Testing`` names both ``## Testing`` and ``## 3. Testing``;
    2. a numeric range ``§2.3-2.5``: every heading whose key lies in it;
    3. the same section key (``### 9.2 P5`` names ``### 9.2 Open``,
       ``Stage A fixtures row`` names ``### Stage A — adapter``);
    4. the heading's title without its key starts with the part, for a part of
       four or more characters (``Retry Design`` names ``## 3. Retry Design``);
    5. the part starts with a heading title of six or more characters
       (``Testing strategy table`` names ``## Testing strategy``);
    6. a key in parentheses names that section (``### Fix (D5)`` names
       ``## D5 — …``, the parent the qualifier points at).
    """
    norm = _normalize(part)
    if not norm:
        return []
    key, title = _section_key(norm)

    def where(test) -> List[int]:
        return [i for i, heading in enumerate(headings) if test(heading)]

    found = where(
        lambda h: _starts_at_boundary(h.norm, norm)
        or (key is None and len(norm) >= 4 and _starts_at_boundary(h.title, norm))
    )
    if found:
        return found
    span = _RANGE.match(norm)
    if span:
        low, high = _key_tuple(span.group(1)), _key_tuple(span.group(2))
        if low and high and len(low) == len(high) and low <= high:
            depth = len(low)

            def in_range(h: Heading) -> bool:
                value = _key_tuple(h.key)
                return bool(value) and len(value) >= depth and low <= value[:depth] <= high

            found = where(in_range)
            if found:
                return found
    if key:
        found = where(lambda h: h.key == key)
        if found:
            return found
    if len(norm) >= 4:
        found = where(lambda h: _starts_at_boundary(h.title, norm))
        if found:
            return found
    found = where(
        lambda h: len(h.title) >= 6
        and (_starts_at_boundary(norm, h.title) or _starts_at_boundary(title, h.title))
    )
    if found:
        return found
    qualifiers = {_canonical_key(m.group(1)) for m in _QUALIFIER_KEY.finditer(norm)}
    return where(lambda h: h.key is not None and h.key in qualifiers)


@dataclass
class CitedSelection:
    """What :meth:`CitedPlan.select` decided for one batch.

    ``excerpt`` is ``None`` when the batch falls back to the whole plan, and
    ``reason`` then says why. ``parts``/``resolved`` count the batch's
    reference parts and those that named a heading.
    """

    excerpt: Optional[str]
    reason: Optional[str] = None
    parts: int = 0
    resolved: int = 0
    sections_shown: int = 0


@dataclass
class CitedPlan:
    """A plan parsed once per round, from which each batch selects its sections.

    ``headings`` are the section headings: every heading except a lone
    level-1 title, which belongs to the preamble with the text before the
    first section. ``global_sections`` index the top-level sections every
    cited batch carries (:data:`_GLOBAL_TITLE`). ``unscoped`` says why no
    batch of this plan may be cited, when one cannot be.
    """

    text: str
    headings: List[Heading]
    preamble_end: int
    global_sections: List[int] = field(default_factory=list)
    unscoped: Optional[str] = None
    _cache: Dict[str, List[int]] = field(default_factory=dict)

    @classmethod
    def parse(cls, text: str) -> Optional["CitedPlan"]:
        """The parsed plan, or ``None`` when it has no section headings.

        A plan with a setext heading (a line of text over ``===`` or ``---``)
        parses ``unscoped``: its sections end where this scan cannot see, so
        a selection could stop inside one.
        """
        headings, setext = _scan(text)
        level_one = [h for h in headings if h.level == 1]
        if len(level_one) == 1 and headings and headings[0] is level_one[0]:
            headings = headings[1:]
        if not headings:
            return None
        top = min(h.level for h in headings)
        global_sections = [
            i for i, h in enumerate(headings)
            if h.level == top and _GLOBAL_TITLE.search(h.title)
        ]
        unscoped = (
            "the plan has a setext heading, which scoping does not parse"
            if setext else None
        )
        return cls(
            text=text, headings=headings, preamble_end=headings[0].offset,
            global_sections=global_sections, unscoped=unscoped,
        )

    def _resolve(self, part: str) -> List[int]:
        if part not in self._cache:
            self._cache[part] = resolve_part(part, self.headings)
        return self._cache[part]

    def _subtree_end(self, index: int) -> int:
        level = self.headings[index].level
        for heading in self.headings[index + 1:]:
            if heading.level <= level:
                return heading.offset
        return len(self.text)

    def _intro_end(self, index: int) -> int:
        if index + 1 < len(self.headings):
            return self.headings[index + 1].offset
        return len(self.text)

    def _ancestors(self, index: int) -> List[int]:
        level = self.headings[index].level
        found: List[int] = []
        for j in range(index - 1, -1, -1):
            if self.headings[j].level < level:
                found.append(j)
                level = self.headings[j].level
        return found

    def _gap_marker(self, start: int, end: int) -> str:
        names = [h.name for h in self.headings if start <= h.offset < end]
        shown = ", ".join(names[:_GAP_NAMED])
        more = len(names) - _GAP_NAMED
        return (
            f"[... not cited by this batch, not shown: {shown}"
            + (f" (+{more} more)" if more > 0 else "")
            + " ...]"
        )

    def select(
        self,
        records: Iterable[Mapping[str, Any]],
        *,
        limit: int,
        min_chars: int = CITED_MIN_CHARS,
        max_share: float = CITED_MAX_SHARE,
    ) -> CitedSelection:
        """The cited excerpt for one batch's suggestion records, or a fallback.

        The excerpt is the preamble, the global sections, then every cited
        section's subtree with the intro of each heading above it, in plan
        order, merged where they touch; each omitted stretch becomes one
        marker line naming its first headings. It falls back (``excerpt is
        None``) when the plan is shorter than ``min_chars`` or ``unscoped``;
        when any suggestion has no reference, or any part of one names no
        heading (a batch is cited only when every section its suggestions name
        is shown); or when the excerpt would be ``max_share`` of the plan or
        more, or over ``limit``.
        """
        if len(self.text) < min_chars:
            return CitedSelection(None, f"the plan is under {min_chars} chars")
        if self.unscoped:
            return CitedSelection(None, self.unscoped)
        cited: set = set(self.global_sections)
        parts = resolved = 0
        missing: Optional[str] = None
        for record in records:
            group = record.get("group_index", "?")
            suggestions = [
                s for s in record.get("suggestions") or [] if isinstance(s, Mapping)
            ]
            if not suggestions and missing is None:
                missing = f"group {group} has no suggestion to cite a section"
            for suggestion in suggestions:
                split = split_reference(suggestion.get("reference"))
                if not split and missing is None:
                    missing = f"group {group} has a suggestion with no reference"
                for part in split:
                    parts += 1
                    found = self._resolve(part)
                    if found:
                        resolved += 1
                        cited.update(found)
                    elif missing is None:
                        missing = (
                            f"group {group} cites a part that names no section "
                            f"of the plan"
                        )
        if missing is not None:
            return CitedSelection(None, missing, parts, resolved)
        spans: List[Tuple[int, int]] = []
        if self.preamble_end > 0:
            spans.append((0, self.preamble_end))
        shown: set = set()
        for index in cited:
            end = self._subtree_end(index)
            spans.append((self.headings[index].offset, end))
            shown.update(
                i for i, h in enumerate(self.headings)
                if self.headings[index].offset <= h.offset < end
            )
            for ancestor in self._ancestors(index):
                spans.append((self.headings[ancestor].offset, self._intro_end(ancestor)))
                shown.add(ancestor)
        spans.sort()
        merged: List[List[int]] = []
        for start, end in spans:
            if merged and start <= merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], end)
            else:
                merged.append([start, end])
        pieces: List[str] = []
        cursor = 0
        for start, end in merged:
            if start > cursor:
                pieces.append(self._gap_marker(cursor, start))
            pieces.append(self.text[start:end].rstrip("\n"))
            cursor = end
        if cursor < len(self.text):
            pieces.append(self._gap_marker(cursor, len(self.text)))
        excerpt = "\n\n".join(pieces)
        if len(excerpt) >= max_share * len(self.text):
            return CitedSelection(
                None,
                f"the cited sections are {round(100 * max_share)}% of the plan or more",
                parts, resolved,
            )
        if len(excerpt) > limit:
            return CitedSelection(
                None, f"the cited sections are over {limit} chars", parts, resolved,
            )
        return CitedSelection(excerpt, None, parts, resolved, len(shown))


def summary_line(
    selections: Sequence[CitedSelection], plan_chars: int,
) -> Optional[str]:
    """The phase's one ``[VALIDATION_CONTEXT_CITED]`` stderr line, or ``None``.

    Silent when no suggestion carried a reference and no batch was cited (a
    code review's issues cite files, not sections): there was nothing to say.
    """
    if not selections:
        return None
    cited = [s for s in selections if s.excerpt is not None]
    if not cited and not any(s.parts for s in selections):
        return None
    fell_back: Dict[str, int] = {}
    for selection in selections:
        if selection.excerpt is None:
            reason = re.sub(r"^group \S+ ", "a group ", selection.reason or "unknown")
            fell_back[reason] = fell_back.get(reason, 0) + 1
    parts = sum(s.parts for s in selections)
    resolved = sum(s.resolved for s in selections)
    if cited:
        sizes = sorted(len(s.excerpt or "") for s in cited)
        head = (
            f"{len(cited)} of {len(selections)} batches carry the plan sections "
            f"their groups cite ({sizes[0]}-{sizes[-1]} of {plan_chars} chars)"
        )
    else:
        head = f"0 of {len(selections)} batches carry cited plan sections"
    tail = ""
    if fell_back:
        tail = "; whole plan in " + ", ".join(
            f"{count} ({reason})" for reason, count in sorted(fell_back.items())
        )
    return (
        f"[VALIDATION_CONTEXT_CITED] plan: {head}{tail}; "
        f"{resolved}/{parts} reference parts resolved"
    )


__all__ = [
    "CITED_CONTEXT_ENV",
    "CITED_MAX_SHARE",
    "CITED_MIN_CHARS",
    "CONTEXT_CITED",
    "CONTEXT_FULL",
    "CitedPlan",
    "CitedSelection",
    "Heading",
    "SELECTION_CITED",
    "batch_code_windows_enabled",
    "cited_context_enabled",
    "context_setting",
    "markdown_headings",
    "resolve_part",
    "split_reference",
    "summary_line",
]
