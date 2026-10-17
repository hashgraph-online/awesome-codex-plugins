"""Structural (Layer 2) humanization: sentence-length rebalancing and bullet-soup merging.

Research basis: uniform sentence length is the #1 statistical AI-detector signal.
Human prose has sentence-length stddev around 8 words; GPT-4o output sits near 4
(docs/research/04-natural-language-quality/, docs/research/14-creative-writing-storytelling/).
Adversarial Paraphrasing (NeurIPS 2025) showed that synonym-swap rewriting without
structural work actually raises detector TPR by 8-15% — a lexical-only pipeline is
not neutral, it is a regression against modern detectors. This module is the
structural layer: it re-introduces sentence-length variance after lexical scrubbing.

Two passes, both conservative:

  split_long_sentences
      Sentences with >=30 words get one split at the first safe boundary:
      - '; '                (always safe — semicolon already marks a boundary)
      - ', but '            (requires >=8 words per side)
      - ', and then '       (requires >=8 words per side)
      - ', so '             (requires >=8 words per side)
      - ', while '          (requires >=8 words per side)
      Risky connectors (', which ', ', because ', ', if ') are deliberately NOT
      in the list — they open subordinate clauses that can't cleanly become
      independent sentences.

  merge_bullet_soup
      A contiguous run of >=3 bullets that all (a) share the same first word,
      (b) are <=10 words each, and (c) sum to <=40 words, collapses into a
      single sentence with commas. Guards are intentionally tight: false positives
      here destroy readability.

Both passes operate on already-protected text (placeholders for code, URLs,
headings, quoted prose). They do not cross paragraph boundaries and do not
mutate preserved regions.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass

_PLACEHOLDER_RE = re.compile(r"\x00[A-Z]+#\d+\x00")
_WORD_RE = re.compile(r"\w+")

# Sentence boundary — mirrors validate.py to keep measurement and rewrite aligned.
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(\[])")

# Split candidates in priority order. Each entry: (matcher, builder, balance-required).
# matcher.search returns a match whose groups define the boundary; builder takes the
# match and returns the replacement text; if balance-required, both halves must
# meet the min_half word budget before we accept the split.
_SplitBuilder = Callable[[re.Match[str]], str]
_SplitCandidate = tuple[re.Pattern[str], _SplitBuilder, bool]


def _semicolon(m: re.Match[str]) -> str:
    return f"{m.group(1)}. {m.group(2).upper()}"


def _but(m: re.Match[str]) -> str:
    return f"{m.group(1)}. But {m.group(2)}"


def _and_then(m: re.Match[str]) -> str:
    return f"{m.group(1)}. Then {m.group(2)}"


def _so(m: re.Match[str]) -> str:
    return f"{m.group(1)}. So {m.group(2)}"


def _while(m: re.Match[str]) -> str:
    return f"{m.group(1)}. While {m.group(2)}"


def _however(m: re.Match[str]) -> str:
    # ", however, X" → ". However, X"  —  "however" is sentence-starter material
    # when fronted by a comma pair; it cannot function as a subordinator there.
    return f"{m.group(1)}. However, {m.group(2)}"


def _emdash(m: re.Match[str]) -> str:
    # " — " as a sentence boundary. Em-dashes joining two independent clauses
    # are sentence-breakable; em-dashes inside appositives ("my brother — a
    # carpenter — fixed it") are not. The balance check on both halves catches
    # the appositive case: a noun-phrase appositive is short relative to the
    # surrounding sentence, so one half will usually fail min_half.
    return f"{m.group(1)}. {m.group(2).upper()}"


_SPLIT_CANDIDATES: list[_SplitCandidate] = [
    (re.compile(r"(\w)\s*;\s+([a-z])"), _semicolon, False),
    (re.compile(r"(\w),\s+however,\s+([a-z])"), _however, True),
    (re.compile(r"(\w),\s+but\s+([a-z])"), _but, True),
    (re.compile(r"(\w),\s+and\s+then\s+([a-z])"), _and_then, True),
    (re.compile(r"(\w),\s+so\s+([a-z])"), _so, True),
    (re.compile(r"(\w),\s+while\s+([a-z])"), _while, True),
    (re.compile(r"(\w)\s+[—–]\s+([a-z])"), _emdash, True),
]


_BULLET_LINE = re.compile(r"^([ \t]*)([-*+])[ \t]+(.*)$")
_LIST_LINE = re.compile(r"^\s*(?:[-*+]|\d+\.)\s+")


@dataclass
class StructuralReport:
    """Counts of structural edits applied. Used by the CLI audit trail."""

    sentences_split: int = 0
    bullet_groups_merged: int = 0

    def to_dict(self) -> dict:
        return {
            "sentences_split": self.sentences_split,
            "bullet_groups_merged": self.bullet_groups_merged,
        }


def _count_words(text: str) -> int:
    """Word count that treats each placeholder as one token.

    A placeholder like '\\x00LINK#0\\x00' stands in for a chunk of real prose
    (code block, URL, heading). For budget checks we count it as a single
    word — that's what it semantically is in context."""
    stripped = _PLACEHOLDER_RE.sub(" X ", text)
    return len(_WORD_RE.findall(stripped))


def _iter_sentence_spans(paragraph: str) -> list[tuple[int, int]]:
    """Return (start, end) spans for sentence boundaries in paragraph text.

    End index is exclusive and points at the end of the sentence (before the
    whitespace that separates it from the next sentence)."""
    spans: list[tuple[int, int]] = []
    cursor = 0
    for m in _SENTENCE_SPLIT_RE.finditer(paragraph):
        spans.append((cursor, m.start()))
        cursor = m.end()
    if cursor < len(paragraph):
        spans.append((cursor, len(paragraph)))
    return spans


def _try_split(sentence: str, *, min_half: int) -> str | None:
    """Try split candidates in priority order. Return new text or None.

    The first candidate that (a) matches and (b) satisfies the balance check
    wins. Exactly one split per call — we don't cascade in a single pass."""
    for pattern, builder, needs_balance in _SPLIT_CANDIDATES:
        m = pattern.search(sentence)
        if not m:
            continue
        if needs_balance:
            left_text = sentence[: m.start()] + m.group(1)
            right_text = m.group(2) + sentence[m.end() :]
            if _count_words(left_text) < min_half:
                continue
            if _count_words(right_text) < min_half:
                continue
        return sentence[: m.start()] + builder(m) + sentence[m.end() :]
    return None


def _paragraph_sigma(sentences: list[str]) -> float:
    """Sentence-length stddev across a paragraph. Short paragraphs return 0."""
    lengths = [_count_words(s) for s in sentences]
    if len(lengths) < 2:
        return 0.0
    mean = sum(lengths) / len(lengths)
    variance = sum((x - mean) ** 2 for x in lengths) / len(lengths)
    return variance**0.5


def split_long_sentences(
    text: str,
    *,
    min_words: int = 30,
    flat_min_words: int = 20,
    min_half: int = 8,
    target_sigma: float = 5.0,
    report: StructuralReport | None = None,
) -> str:
    """Split sentences at safe boundaries to lift sentence-length variance.

    Two regimes:

    Non-flat paragraphs
        Sentence must have >=`min_words` words to be considered. This is the
        default overlong-sentence cutoff.

    Flat paragraphs (σ < `target_sigma`, 2+ sentences)
        Cutoff drops to `flat_min_words`. A flat paragraph is the point of
        the feature — if every sentence is 25-29 words, the 30-word floor
        would skip it entirely even though splitting is exactly the fix.
        Research basis: human prose σ ~8.2, GPT-4o σ ~4.1 (Cat 04/14).
        Typical AI output sits around σ=4; the 5.0 threshold catches it.

    Single-sentence paragraphs
        Pass through the non-flat path (>=min_words only). There's no σ to
        measure on a single sentence.

    Pure-list paragraphs
        Skipped entirely — handled by merge_bullet_soup and the em-dash cap.

    Operates on already-protected text. At most one split per sentence per
    pass; cascading in a single pass tends to produce choppy fragments.
    """
    paragraphs = text.split("\n\n")
    for pi, para in enumerate(paragraphs):
        if not para.strip():
            continue
        non_blank = [line for line in para.split("\n") if line.strip()]
        if non_blank and all(_LIST_LINE.match(line) for line in non_blank):
            continue

        spans = _iter_sentence_spans(para)
        if not spans:
            continue

        # Decide cutoff based on paragraph shape.
        cutoff = min_words
        if len(spans) >= 2:
            sentences = [para[s:e] for s, e in spans]
            if _paragraph_sigma(sentences) < target_sigma:
                cutoff = flat_min_words
            else:
                # Already varied — leave alone.
                continue

        new_parts: list[str] = []
        changed = False
        for start, end in spans:
            sentence = para[start:end]
            if _count_words(sentence) < cutoff:
                new_parts.append(sentence)
                continue
            split = _try_split(sentence, min_half=min_half)
            if split is None:
                new_parts.append(sentence)
                continue
            new_parts.append(split)
            changed = True
            if report is not None:
                report.sentences_split += 1

        if changed:
            paragraphs[pi] = " ".join(new_parts)

    return "\n\n".join(paragraphs)


def merge_bullet_soup(
    text: str,
    *,
    min_run: int = 3,
    max_bullet_words: int = 10,
    max_total_words: int = 40,
    report: StructuralReport | None = None,
) -> str:
    """Collapse 3+ contiguous short parallel bullets sharing the same first word.

    Guards (all must hold for the run to merge):
      - >=3 consecutive bullets, same indent and same marker character
      - all bullets share the same lowercase first word
      - every bullet has <=max_bullet_words words
      - total words across the run is <=max_total_words

    When a run fails any guard, every bullet in the run is emitted verbatim.
    False-positive cost here is high: merging two unrelated bullets destroys
    meaning. Prefer false negatives.
    """
    lines = text.split("\n")
    out: list[str] = []
    i = 0
    while i < len(lines):
        match_first = _BULLET_LINE.match(lines[i])
        if not match_first:
            out.append(lines[i])
            i += 1
            continue

        indent = match_first.group(1)
        marker = match_first.group(2)

        run: list[tuple[str, str, list[str]]] = []
        j = i
        while j < len(lines):
            m = _BULLET_LINE.match(lines[j])
            if not m or m.group(1) != indent or m.group(2) != marker:
                break
            body = m.group(3).strip()
            # If a bullet body starts with a protected-region placeholder
            # (inline code, URL, quoted prose, etc.), stop the run. Placeholders
            # are opaque tokens; treating their internal kind-name ("INLINE",
            # "URL", ...) as a shared first word would merge 4 bullets that
            # start with different code snippets into one.
            if body.startswith("\x00"):
                break
            words = _WORD_RE.findall(body)
            if not words:
                break
            run.append((words[0], body, words))
            j += 1

        if len(run) < min_run:
            # Emit every line we examined, plus at minimum the current line so
            # we always make progress. When the scan broke immediately (j==i)
            # because the first bullet had a placeholder or didn't match, we
            # still need to emit lines[i] and advance.
            end = max(j, i + 1)
            for k in range(i, end):
                out.append(lines[k])
            i = end
            continue

        first_word_lower = run[0][0].lower()
        if not all(r[0].lower() == first_word_lower for r in run):
            for k in range(i, j):
                out.append(lines[k])
            i = j
            continue

        if any(len(r[2]) > max_bullet_words for r in run):
            for k in range(i, j):
                out.append(lines[k])
            i = j
            continue

        total_words = sum(len(r[2]) for r in run)
        if total_words > max_total_words:
            for k in range(i, j):
                out.append(lines[k])
            i = j
            continue

        tails: list[str] = []
        for _first, body, _words in run:
            # Strip the shared first word from the body to avoid "Uses X, Uses Y, Uses Z".
            tail = body[len(run[0][0]) :].lstrip(" \t,:;")
            if tail:
                tails.append(tail)
        if not tails:
            for k in range(i, j):
                out.append(lines[k])
            i = j
            continue

        # Capitalize the shared opener if it's at line start (bullets always are).
        opener = run[0][0][:1].upper() + run[0][0][1:]
        merged = f"{indent}{marker} {opener} " + ", ".join(tails)
        # Normalize trailing punctuation: ensure exactly one '.' at the end.
        merged = re.sub(r"[.,;:\s]+$", "", merged) + "."
        out.append(merged)
        if report is not None:
            report.bullet_groups_merged += 1
        i = j

    return "\n".join(out)


def humanize_structural(
    text: str,
    *,
    report: StructuralReport | None = None,
) -> str:
    """Apply all structural passes in order. Operates on protected text.

    Order matters: split before merge. Splitting a long sentence can change
    neighbouring bullets (none, in practice — sentences don't live inside bullet
    lines), but merging bullets can remove sentence candidates for the next pass.
    Running splits first lets us catch any long sentences that happen to live
    above or below a mergeable list without losing them to an overeager merge."""
    text = split_long_sentences(text, report=report)
    text = merge_bullet_soup(text, report=report)
    return text
