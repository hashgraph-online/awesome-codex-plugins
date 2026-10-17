"""Validate that humanization preserved structure (code, URLs, paths, headings, bullets)
and reduced AI-isms (residual count must drop, never grow).

Also reports a burstiness metric (sentence-length variance). Flat burstiness is the #1
signal AI-text detectors key on (see docs/research/04-natural-language-quality/ and 05-ai-text-detection-and-evasion/).
The metric is informational — low burstiness does not fail validation, it warns."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass

FENCED_CODE = re.compile(r"^```[^\n]*\n[\s\S]*?^```\s*$", re.MULTILINE)
INDENTED_CODE = re.compile(
    r"(?m)(?:^(?: {4}|\t)[^\n]+(?:\n(?: {4}|\t)[^\n]+)*)"
)
INLINE_CODE = re.compile(r"`[^`\n]+`")
URL = re.compile(r"https?://[^\s)>\]]+")
MD_LINK = re.compile(r"\[[^\]\n]+\]\([^)\n]+\)")
MD_HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
PATH = re.compile(r"(?:^|\s)(/[A-Za-z0-9._/\-]+|[A-Za-z]:\\[A-Za-z0-9._\\\-]+|\./[A-Za-z0-9._/\-]+)")
BULLET = re.compile(r"^\s*[-*+]\s+", re.MULTILINE)
YAML_FRONTMATTER = re.compile(r"\A---\n[\s\S]*?\n---(?=\n|\Z)")
BLOCKQUOTE_BLOCK = re.compile(r"(?m)(?:^[ \t]*>[^\n]*(?:\n[ \t]*>[^\n]*)*)")
TABLE_BLOCK = re.compile(
    r"(?m)(?:^[ \t]*\|[^\n]*\|[ \t]*(?:\n[ \t]*\|[^\n]*\|[ \t]*)+)"
)


AI_ISMS = (
    # Sycophancy openers (case-insensitive)
    r"\bgreat question\b", r"\bcertainly[!.,]", r"\babsolutely[!.,]", r"\bsure[!.,]",
    r"\bi'?d be happy to help\b", r"\bwhat a (?:fascinating|wonderful|great|terrific)\b",
    r"\bi hope this (?:email|message) finds you well\b",
    r"\bthank you for (?:your |the )?(?:question|asking)\b",
    # Stock vocab — context-guarded to match humanize.py's STOCK_VOCAB patterns.
    # Bare \bnavigate\b etc. caused false positives on literal uses like
    # "navigate to the next page" that the unslop correctly preserves.
    r"\bdelv(?:e|es|ed|ing)\b", r"\btapestry\b", r"\btestament to\b",
    r"\bnavigate(?:s|d)?(?=\s+(?:the|through|around|these|this|that|our|complex))\b",
    r"\bnavigating(?=\s+(?:the|through|around|these|this|that|our|complex))\b",
    r"\bembark(?:s|ed|ing)? on\b",
    r"\bjourney(?=\s+(?:toward|to|of))\b",
    r"\brealm of\b", r"\blandscape of\b",
    r"\bpivotal\b", r"\bparamount\b", r"\bseamless(?:ly)?\b", r"\bholistic(?:ally)?\b",
    r"\brobust(?=\s+(?:and|solution|implementation|approach|system|architecture|framework|platform|infrastructure|backend|frontend|foundation|delivery|automation|CI/CD|pipeline|tooling|mechanism|strategy))\b",
    r"\bleverage\b", r"\bleverag(?:es|ed|ing)\b",
    r"\bcutting-edge\b", r"\bstate-of-the-art\b",
    r"\bcomprehensive(?:ly)?\b",
    r"\baligns?\s+with\b", r"\baligned\s+with\b", r"\baligning\s+with\b",
    r"\bfoster(?:s|ed|ing)?\b",
    r"\bshowcas(?:e|es|ed|ing)\b",
    r"\bfast-paced\b", r"\bgroundbreaking\b", r"\bwell-rounded\b",
    # Expanded vocabulary (2026-04 sync with blader/unslop and
    # Wikipedia:Signs_of_AI_writing). Each entry mirrors a rule in
    # humanize.py's STOCK_VOCAB so the residual check can detect when a
    # rewrite accidentally introduces them.
    r"\binterplay\s+(?:between|of)\b",
    r"\bintricate\b", r"\bvibrant\b",
    r"\bunderscor(?:e|es|ed|ing)\s+(?:the|our|a|an|its|their|this|that|how|why)\b",
    r"\bcrucial\b",
    r"\bvital(?=\s+(?:role|importance|part|component|aspect))\b",
    r"\bever[- ](?:evolving|changing)\b",
    r"\bin today'?s (?:digital )?(?:world|age|landscape|era)\b",
    r"\bdynamic landscape\b",
    # 2026-04 additions — mirror humanize.py's vocabulary extension. Each
    # entry has a corresponding STOCK_VOCAB rewrite; the validator refuses
    # to let an LLM rewrite reintroduce them.
    r"\bmeticulous(?:ly)?\b",
    r"\bbustling\b",
    r"\bparadigm\s+shift\b",
    r"\bgame[- ]?chang(?:er|ers|ing)\b",
    r"\brevolutioniz(?:e|es|ed|ing)\b",
    r"\btransformative\b",
    r"\bunprecedented(?=\s+(?:opportunity|opportunities|challenge|challenges|growth|success|impact|change)\b)",
    r"\ba\s+myriad\s+of\b",
    r"\bmyriad\s+(?=\w)",
    r"\ba\s+plethora\s+of\b",
    r"\buncharted\s+(?:territory|waters|ground|area|domain)\b",
    r"\bnuanced\b(?=\s+(?:understanding|view|perspective|approach|analysis|take))",
    r"\bsynerg(?:y|ies|ize|izes|ized|izing)\b",
    # Hedging stacks
    r"\bit'?s important to note that\b",
    r"\bit'?s worth (?:mentioning|noting|pointing out) that\b",
    r"\bgenerally speaking\b",
    r"\bin essence\b",
    r"\bat its core\b",
    r"\bit should be noted that\b",
    r"\bneedless to say\b",
    # Authority tropes (blader/unslop #27). Position-sensitive — only at
    # sentence start is the AI tell strong.
    r"(?:^|(?<=[.!?]\s))In reality\b",
    r"(?:^|(?<=[.!?]\s))Fundamentally\b",
    r"(?:^|(?<=[.!?]\s))What really matters\b",
    r"(?:^|(?<=[.!?]\s))The heart of the matter\b",
    # Signposting announcements (blader/unslop #28).
    r"\blet(?:'s| us) dive in(?:to\b|\b)",
    r"\blet(?:'s| us) (?:break|walk) (?:this|it) down\b",
    r"\bhere'?s what you need to know\b",
    r"\bwithout further ado\b",
    r"\bbuckle up\b",
    # Knowledge-cutoff / model-limitation disclaimers.
    r"\bas of my (?:last update|knowledge cutoff)\b",
    r"\bi do not have access to real-time information\b",
    r"\bmy training data only goes up to\b",
    # Vague attribution.
    r"\bobservers (?:say|note|suggest)\b",
    r"\bexperts (?:argue|believe|maintain)\b",
    r"\bindustry reports\b",
    r"\bscholarship (?:has|shows|suggests)\b",
    r"\bmany (?:believe|argue|maintain)\b",
    # Filler phrases (blader/unslop #23). These are the strongest signals;
    # we keep the list short and conservative. More verbose expansions can
    # occasionally appear in legitimate prose (e.g. legal boilerplate).
    r"\bin order to\b",
    r"\bdue to the fact that\b",
    r"\bfor (?:the|all) intents and purposes\b",
    # Transitional AI tics at sentence start or after bullet markers.
    r"(?:^|(?<=[.!?]\s))(?:furthermore|moreover|additionally)\b",
    r"(?:^[ \t]*(?:[-*+]|\d+\.)[ \t]+)(?:furthermore|moreover|additionally)\b",
    r"(?:^|(?<=[.!?]\s))in conclusion\b",
    r"(?:^[ \t]*(?:[-*+]|\d+\.)[ \t]+)in conclusion\b",
    r"(?:^|(?<=[.!?]\s))to summarize\b",
    r"(?:^|(?<=[.!?]\s))(?:firstly|secondly|thirdly|finally)\b",
    r"(?:^[ \t]*(?:[-*+]|\d+\.)[ \t]+)(?:firstly|secondly|thirdly|finally)\b",
    # Phase 2 (2026-04-21): significance inflation, notability namedropping,
    # superficial -ing analyses, copula avoidance. Mirrors humanize.py Phase 2
    # rule families so the validator can detect when a rewrite accidentally
    # reintroduces them (e.g. an LLM rewrite adds "marks a pivotal moment").
    # Significance inflation
    r"\b(?:marks?|represents?|stands?\s+as)\s+(?:a|an|the)\s+(?:pivotal|defining|critical|key|watershed|seminal)\s+(?:moment|turning\s+point|milestone)\b",
    r"(?:underscor(?:es|ing)|emphasiz(?:es|ing))\s+(?:the|its|their)\s+(?:importance|significance|role)",
    r"\b(?:enduring|lasting|indelible)\s+legacy\b",
    r"\bleaves?\s+an?\s+indelible\s+mark\b",
    r"\bdeeply\s+rooted\s+in\b",
    r"\b(?:contributing\s+to|shaping)\s+the\s+(?:broader|wider|ongoing)\s+(?:narrative|landscape|conversation|discourse)\b",
    # Notability namedropping
    r"\b(?:maintains?|has)\s+an\s+active\s+(?:social\s+media\s+)?presence\b",
    r"\ba\s+leading\s+(?:expert|voice|authority|figure)\s+(?:in|on)\b",
    r"\brenowned\s+for\s+(?:his|her|their)\s+work\b",
    r"\bwidely\s+(?:cited|featured|covered)\s+(?:in|by)\b",
    r"\b(?:internationally|globally)\s+recogni[sz]ed\s+as\b",
    # Superficial -ing analyses (matches only the canonical filler forms)
    r",\s+(?:highlighting|underscoring|emphasizing|illustrating|reflecting|showcasing)\s+(?:the|its|their|his|her|a|an)\s+(?:importance|significance|role|impact|value|need|necessity|relevance|nature)\b",
    # Copula avoidance (", being a/an/the X,")
    r",\s+being\s+(?:a|an|the)\s+[a-z]",
    # 2026-04-28 Tier 1 gap-fill: full copula avoidance set, canonical
    # negative parallelism, additional promotional register. Each pattern
    # mirrors a humanize.py rule so the residual check refuses to let an
    # LLM rewrite reintroduce them.
    #
    # Promotional copula avoidance — mirrors humanize.py COPULA_AVOIDANCE.
    r"\bserves?\s+as\s+(?:a|an|the)\s+(?:reliable|powerful|leading|prominent|key|major|prime|cornerstone|hub|center|centre|foundation|backbone|gateway|model|standard|benchmark|symbol|reminder|catalyst|beacon)\b",
    r"\bserved\s+as\s+(?:a|an|the)\s+(?:reliable|powerful|leading|prominent|key|major|prime|cornerstone|hub|center|centre|foundation|backbone|gateway|model|standard|benchmark|symbol|reminder|catalyst|beacon)\b",
    r"\bboast(?:s|ed|ing)?\s+(?:a|an)\s+[a-z]",
    r"\bfeatures\s+(?:a|an)\s+(?:stunning|beautiful|breathtaking|impressive|elegant|sleek|innovative|intuitive|seamless|cutting-edge|state-of-the-art|world-class|industry-leading|best-in-class|revolutionary|groundbreaking)\b",
    # Negative parallelism (canonical) — "Not just/only X, but Y" and
    # "It's not X — it's Y". Mirrors humanize.py NEGATIVE_PARALLELISM.
    r"(?:^|(?<=[.!?]\s))Not (?:just|only) [^,.!?\n]{1,80},\s*but(?:\s+also)?\b",
    r"(?:^|(?<=[.!?]\s))It'?s not [^—.!?\n]{1,80}\s+[—–]\s+it'?s ",
    # Promotional register (Wikipedia #4) — mirrors STOCK_VOCAB additions.
    r"\bnestled\s+(?:in|between|amongst|among|within|by)\b",
    r"\b(?:rich|deep)\s+heritage\b",
    r"\bsteeped\s+in\s+(?:rich\s+)?(?:tradition|history|heritage)\b",
)

# FALSE_RANGES — "from X to Y" clichés where the range is formulaic rather than
# literal. Wikipedia "Signs of AI writing". Validator-only: regex rewrite risks
# corrupting literal ranges (dates, versions, measurements). These trigger a
# warning on match so the user can hand-edit or run LLM mode.
FALSE_RANGES = tuple(
    re.compile(p, re.IGNORECASE)
    for p in (
        r"\bfrom\s+(?:beginners?|novices?)\s+to\s+(?:experts?|professionals?|veterans?)\b",
        r"\bfrom\s+(?:humble\s+)?beginnings?\s+to\b",
        r"\bfrom\s+simple\s+\w+\s+to\s+complex\s+\w+\b",
        r"\bfrom\s+the\s+mundane\s+to\s+the\s+(?:extraordinary|sublime|profound)\b",
        r"\bfrom\s+(?:small|tiny)\s+startups?\s+to\s+(?:global|massive)\s+enterprises?\b",
        r"\bspan(?:s|ning)?\s+the\s+spectrum\s+from\b",
    )
)

# SYNONYM_CYCLING — same concept referred to by multiple words in a short span.
# Wikipedia calls this a sign of AI writing trying to avoid repetition without
# recognizing that controlled repetition is a valid style choice. Heuristic:
# detect when 3+ members of a known synonym group appear in the same paragraph.
_SYNONYM_GROUPS: tuple[frozenset[str], ...] = (
    frozenset({"utilize", "utilise", "leverage", "employ", "harness"}),
    frozenset({"showcase", "highlight", "emphasize", "emphasise", "underscore"}),
    frozenset({"pivotal", "crucial", "vital", "paramount", "essential"}),
    frozenset({"comprehensive", "thorough", "exhaustive", "holistic"}),
    frozenset({"robust", "resilient", "reliable", "solid"}),
)
AI_ISM_PATTERNS = [re.compile(p, re.IGNORECASE) for p in AI_ISMS]


@dataclass
class ValidationResult:
    ok: bool
    errors: list[str]
    warnings: list[str]
    ai_isms_before: int
    ai_isms_after: int
    burstiness_before: float = 0.0
    burstiness_after: float = 0.0
    sentence_length_range_after: tuple[int, int] = (0, 0)
    flat_paragraphs_before: int = 0
    flat_paragraphs_after: int = 0
    false_ranges_before: int = 0
    false_ranges_after: int = 0
    synonym_cycling_before: int = 0
    synonym_cycling_after: int = 0
    contraction_rate_before: float = 0.0
    contraction_rate_after: float = 0.0
    curly_quotes_before: int = 0
    curly_quotes_after: int = 0
    title_case_headings: int = 0
    inline_header_lists: int = 0
    generic_positive_conclusions: int = 0
    outline_conclusions: int = 0

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "ai_isms_before": self.ai_isms_before,
            "ai_isms_after": self.ai_isms_after,
            "burstiness_before": round(self.burstiness_before, 3),
            "burstiness_after": round(self.burstiness_after, 3),
            "sentence_length_range_after": list(self.sentence_length_range_after),
            "flat_paragraphs_before": self.flat_paragraphs_before,
            "flat_paragraphs_after": self.flat_paragraphs_after,
            "false_ranges_before": self.false_ranges_before,
            "false_ranges_after": self.false_ranges_after,
            "synonym_cycling_before": self.synonym_cycling_before,
            "synonym_cycling_after": self.synonym_cycling_after,
            "contraction_rate_before": round(self.contraction_rate_before, 3),
            "contraction_rate_after": round(self.contraction_rate_after, 3),
            "curly_quotes_before": self.curly_quotes_before,
            "curly_quotes_after": self.curly_quotes_after,
            "title_case_headings": self.title_case_headings,
            "inline_header_lists": self.inline_header_lists,
            "generic_positive_conclusions": self.generic_positive_conclusions,
            "outline_conclusions": self.outline_conclusions,
        }


def _extract(pattern: re.Pattern, text: str) -> list[str]:
    return pattern.findall(text)


def _strip_code_for_prose(text: str) -> str:
    """Remove everything that isn't natural-language prose so burstiness reflects
    the actual writing: code (fenced, indented, inline), YAML frontmatter, tables,
    and blockquotes (those are either examples or quoted material, not the
    author's own rhythm)."""
    text = YAML_FRONTMATTER.sub("", text)
    text = FENCED_CODE.sub("", text)
    text = INDENTED_CODE.sub("", text)
    text = TABLE_BLOCK.sub("", text)
    text = BLOCKQUOTE_BLOCK.sub("", text)
    text = INLINE_CODE.sub("", text)
    return text


_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(\[])")


def _sentence_lengths(text: str) -> list[int]:
    """Word-count per sentence across prose only. Used for burstiness."""
    prose = _strip_code_for_prose(text)
    lengths: list[int] = []
    for paragraph in re.split(r"\n\s*\n", prose):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        for sentence in _SENTENCE_SPLIT.split(paragraph):
            words = [w for w in re.split(r"\s+", sentence.strip()) if w]
            if words:
                lengths.append(len(words))
    return lengths


def _paragraph_sentence_lengths(text: str) -> list[list[int]]:
    """Per-paragraph sentence-length lists. Empty paragraphs skipped.

    Used for per-paragraph burstiness: uniform-length-within-paragraph is a
    stronger structural signal than document-wide σ, which can hide flat
    paragraphs when they average out."""
    prose = _strip_code_for_prose(text)
    groups: list[list[int]] = []
    for paragraph in re.split(r"\n\s*\n", prose):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        lengths: list[int] = []
        for sentence in _SENTENCE_SPLIT.split(paragraph):
            words = [w for w in re.split(r"\s+", sentence.strip()) if w]
            if words:
                lengths.append(len(words))
        if lengths:
            groups.append(lengths)
    return groups


def _burstiness(lengths: list[int]) -> float:
    """Standard deviation of sentence lengths. Higher = more human-like rhythm.
    Returns 0.0 if fewer than 2 sentences (not meaningful)."""
    if len(lengths) < 2:
        return 0.0
    mean = sum(lengths) / len(lengths)
    variance = sum((x - mean) ** 2 for x in lengths) / len(lengths)
    return math.sqrt(variance)


def _count_flat_paragraphs(
    paragraph_lengths: list[list[int]],
    *,
    min_sentences: int = 3,
    sigma_threshold: float = 3.0,
) -> int:
    """Count paragraphs that are structurally flat.

    A paragraph counts as flat when it has >=`min_sentences` sentences and its
    sentence-length standard deviation is < `sigma_threshold`. Short paragraphs
    (1-2 sentences) are excluded because σ isn't meaningful there."""
    flat = 0
    for lengths in paragraph_lengths:
        if len(lengths) < min_sentences:
            continue
        if _burstiness(lengths) < sigma_threshold:
            flat += 1
    return flat


def _extract_fenced_blocks(text: str) -> list[str]:
    """Return fenced code blocks as a list, preserving content exactly."""
    return FENCED_CODE.findall(text)


def _extract_indented_blocks(text: str) -> list[str]:
    """Return indented code blocks as a list, preserving content exactly."""
    return INDENTED_CODE.findall(text)


def _count_ai_isms(text: str) -> int:
    return sum(len(p.findall(text)) for p in AI_ISM_PATTERNS)


def _count_false_ranges(text: str) -> int:
    """Count occurrences of AI-cliché `from X to Y` formulations in prose."""
    prose = _strip_code_for_prose(text)
    return sum(len(p.findall(prose)) for p in FALSE_RANGES)


_WORD_RE = re.compile(r"[A-Za-z]+")

# Contraction detection — AI text typically has near-zero contractions per word
# vs human ~0.17 (empirical; source citation pending re-verification). Low
# contraction rate is a distributional fingerprint that token-level detectors read.
_CONTRACTION_RE = re.compile(
    r"\b(?:don|doesn|didn|won|wouldn|shouldn|couldn|mightn|mustn|isn|aren|"
    r"wasn|weren|hasn|haven|hadn|can)'t\b|"
    r"\b(?:it|that|there|what|where|who|he|she|we|you|they|"
    r"I)'(?:s|re|ve|ll|d|m)\b|"
    r"\bI'm\b",
    re.IGNORECASE,
)


def _contraction_rate(text: str) -> float:
    """Contractions per 1000 words in prose-only text. Human baseline ~17 per
    1k words; AI-generated text often has 0."""
    prose = _strip_code_for_prose(text)
    words = len(_WORD_RE.findall(prose))
    if words < 20:
        return 0.0
    contractions = len(_CONTRACTION_RE.findall(prose))
    return (contractions / words) * 1000


def _count_synonym_cycling(text: str) -> int:
    """Count paragraphs where 3+ members of a known synonym group co-occur.

    Heuristic: true synonym cycling requires semantic similarity (would need
    embeddings). This catches the lexical subset: a paragraph using "utilize"
    + "leverage" + "employ" in close proximity. False positives on genuine
    distinctions are possible; the signal is a warning, not an error."""
    prose = _strip_code_for_prose(text)
    paragraphs = re.split(r"\n\s*\n", prose)
    flagged = 0
    for para in paragraphs:
        words = {w.lower() for w in _WORD_RE.findall(para)}
        for group in _SYNONYM_GROUPS:
            if len(words & group) >= 3:
                flagged += 1
                break  # count once per paragraph
    return flagged


_CURLY_QUOTE = re.compile(r"[\u2018\u2019\u201c\u201d]")
_CONTENT_WORD = re.compile(r"[A-Za-z][A-Za-z'-]*")
_TITLE_CASE_STOPWORDS = {
    "a",
    "an",
    "and",
    "as",
    "at",
    "by",
    "for",
    "from",
    "in",
    "into",
    "of",
    "on",
    "or",
    "the",
    "to",
    "vs",
    "with",
}
_INLINE_HEADER_ITEM = re.compile(r"^[ \t]*[-*+]\s+\*\*[^*\n]+:\*\*", re.MULTILINE)
_GENERIC_POSITIVE_FINAL = re.compile(
    r"(?:^|(?<=[.!?]\s))[^.!?\n]*\b(?:remains|stands as|continues to be) "
    r"(?:a|an) (?:fascinating|important|powerful|essential|critical) [a-z]+\b[^.!?\n]*[.!?](?=\s*$)",
    re.IGNORECASE,
)
_GENERIC_POSITIVE_SUMMARY = re.compile(
    r"(?:^|(?<=[.!?]\s))In (?:summary|conclusion), [^.?!]*"
    r"(?:fascinating|important|powerful|remarkable)[^.?!]*[.!?]",
    re.IGNORECASE,
)

# Outline-like-conclusion (Wikipedia "Signs of AI writing" #6, blader/unslop
# #6). Encyclopedic AI-essay closer that pairs a "Despite X" concession with
# a "Y faces (significant) challenges" forecast. The structure is the tell;
# the words inside it can be plausible. Validator-only — auto-rewriting risks
# destroying real concession + forecast prose. Surface as a warning so the
# user can hand-edit or run LLM mode.
_OUTLINE_CONCLUSION = re.compile(
    # Anchor at start of a line (MULTILINE) or after a sentence terminator.
    # MULTILINE matters because paragraph breaks are `\n\n`, and the lookbehind
    # would otherwise see only the trailing `\n` and fail.
    r"(?:^|(?<=[.!?]\s))Despite\s+[^,.!?\n]{3,120},\s+"
    # Optional subject clause: zero-or-more non-sentence-terminator chars
    # followed by required whitespace. Bounded by `[^.!?\n]` so the regex
    # can never overrun into the next sentence.
    r"(?:[A-Za-z][^.!?\n]{0,80}?\s+)?"
    r"(?:faces?|will\s+face|continues?\s+to\s+face|must\s+(?:overcome|address|navigate|confront))\s+"
    r"(?:significant|major|numerous|various|several|many|ongoing|continuing|persistent|considerable)?\s*"
    r"(?:challenges|hurdles|obstacles|difficulties|headwinds|barriers)\b",
    re.IGNORECASE | re.MULTILINE,
)


def _count_curly_quotes(text: str) -> int:
    return len(_CURLY_QUOTE.findall(_strip_code_for_prose(text)))


def _count_title_case_headings(text: str) -> int:
    count = 0
    for _level, heading in MD_HEADING.findall(text):
        words = [w for w in _CONTENT_WORD.findall(heading) if w.lower() not in _TITLE_CASE_STOPWORDS]
        if len(words) < 3:
            continue
        capped = sum(1 for w in words if w[:1].isupper())
        if capped / len(words) >= 0.8:
            count += 1
    return count


def _count_inline_header_lists(text: str) -> int:
    prose = _strip_code_for_prose(text)
    count = 0
    streak = 0
    for line in prose.splitlines():
        if _INLINE_HEADER_ITEM.match(line):
            streak += 1
            continue
        if streak >= 3:
            count += 1
        streak = 0
    if streak >= 3:
        count += 1
    return count


def _count_generic_positive_conclusions(text: str) -> int:
    prose = _strip_code_for_prose(text)
    count = 0
    for paragraph in re.split(r"\n\s*\n", prose):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        if _GENERIC_POSITIVE_FINAL.search(paragraph):
            count += 1
        count += len(_GENERIC_POSITIVE_SUMMARY.findall(paragraph))
    return count


def _count_outline_conclusions(text: str) -> int:
    """Count "Despite X, Y faces (significant) challenges" closers in prose."""
    prose = _strip_code_for_prose(text)
    return len(_OUTLINE_CONCLUSION.findall(prose))


def validate(original: str, humanized: str) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    # Code blocks — exact comparison, no normalization
    orig_code = _extract_fenced_blocks(original)
    new_code = _extract_fenced_blocks(humanized)
    if orig_code != new_code:
        errors.append(
            "Code block(s) modified, reordered, removed, or added."
        )

    # Indented code blocks
    orig_indented = _extract_indented_blocks(original)
    new_indented = _extract_indented_blocks(humanized)
    if orig_indented != new_indented:
        errors.append(
            f"Indented code block(s) modified or removed. {len(orig_indented)} → {len(new_indented)}."
        )

    # YAML frontmatter
    orig_yaml = YAML_FRONTMATTER.findall(original)
    new_yaml = YAML_FRONTMATTER.findall(humanized)
    if orig_yaml != new_yaml:
        errors.append("YAML frontmatter modified, removed, or added.")

    # Blockquotes — treat as verbatim-quoted content
    orig_quotes = BLOCKQUOTE_BLOCK.findall(original)
    new_quotes = BLOCKQUOTE_BLOCK.findall(humanized)
    if orig_quotes != new_quotes:
        errors.append(
            f"Blockquote(s) modified. {len(orig_quotes)} → {len(new_quotes)}."
        )

    # Tables — treat as reference content (glossaries, comparison rows)
    orig_tables = TABLE_BLOCK.findall(original)
    new_tables = TABLE_BLOCK.findall(humanized)
    if orig_tables != new_tables:
        errors.append(
            f"Markdown table(s) modified. {len(orig_tables)} → {len(new_tables)}."
        )

    # Inline code
    orig_inline = set(_extract(INLINE_CODE, original))
    new_inline = set(_extract(INLINE_CODE, humanized))
    missing_inline = orig_inline - new_inline
    if missing_inline:
        errors.append(
            f"Inline code missing: {sorted(missing_inline)[:5]}"
            + (f" (+{len(missing_inline) - 5} more)" if len(missing_inline) > 5 else "")
        )

    # URLs
    orig_urls = set(_extract(URL, original))
    new_urls = set(_extract(URL, humanized))
    missing_urls = orig_urls - new_urls
    if missing_urls:
        errors.append(
            f"URL(s) missing: {sorted(missing_urls)[:5]}"
            + (f" (+{len(missing_urls) - 5} more)" if len(missing_urls) > 5 else "")
        )

    # Markdown links
    orig_md_links = _extract(MD_LINK, original)
    new_md_links = _extract(MD_LINK, humanized)
    if orig_md_links != new_md_links:
        errors.append("Markdown link(s) modified, reordered, removed, or added.")

    # Headings
    orig_headings = [(level, text.strip()) for level, text in MD_HEADING.findall(original)]
    new_headings = [(level, text.strip()) for level, text in MD_HEADING.findall(humanized)]
    if orig_headings != new_headings:
        if len(orig_headings) != len(new_headings):
            errors.append(
                f"Heading count changed: {len(orig_headings)} → {len(new_headings)}"
            )
        else:
            for (lo, ho), (ln, hn) in zip(orig_headings, new_headings, strict=False):
                if lo != ln or ho != hn:
                    errors.append(f"Heading changed: {lo} {ho!r} → {ln} {hn!r}")
                    break

    # Paths
    orig_paths = set(m.group(1) for m in PATH.finditer(original))
    new_paths = set(m.group(1) for m in PATH.finditer(humanized))
    missing_paths = orig_paths - new_paths
    if missing_paths:
        warnings.append(
            f"Path(s) possibly missing: {sorted(missing_paths)[:3]}"
            + (f" (+{len(missing_paths) - 3} more)" if len(missing_paths) > 3 else "")
        )

    # Bullets — unslop is allowed to consolidate, but not to drop more than half
    orig_bullets = len(BULLET.findall(original))
    new_bullets = len(BULLET.findall(humanized))
    if orig_bullets > 0 and new_bullets < orig_bullets // 2:
        warnings.append(
            f"Bullet count dropped sharply: {orig_bullets} → {new_bullets}. "
            "Unslop may have over-consolidated."
        )

    # AI-ism residual: must not increase
    ai_before = _count_ai_isms(original)
    ai_after = _count_ai_isms(humanized)
    if ai_after > ai_before:
        errors.append(
            f"AI-ism count increased: {ai_before} → {ai_after}. Unslop added slop."
        )
    elif ai_before > 0 and ai_after == ai_before:
        warnings.append(
            f"AI-isms unchanged ({ai_before}). Unslop did not strip canonical phrases."
        )

    # Burstiness — sentence-length variance. Flat = detector bait. Informational.
    orig_lengths = _sentence_lengths(original)
    new_lengths = _sentence_lengths(humanized)
    burst_before = _burstiness(orig_lengths)
    burst_after = _burstiness(new_lengths)
    length_range = (
        (min(new_lengths), max(new_lengths)) if new_lengths else (0, 0)
    )
    # Threshold: stddev < 4 on a doc with ≥8 sentences means suspiciously uniform.
    if len(new_lengths) >= 8 and burst_after < 4.0:
        warnings.append(
            f"Burstiness low (σ={burst_after:.1f} across {len(new_lengths)} sentences). "
            "Flat sentence length is the #1 AI-detector signal. Vary rhythm more."
        )

    # Per-paragraph shape — document-wide σ can hide flat paragraphs that average
    # out with each other. Count paragraphs of >=3 sentences whose internal σ<3.
    orig_para_lengths = _paragraph_sentence_lengths(original)
    new_para_lengths = _paragraph_sentence_lengths(humanized)
    flat_before = _count_flat_paragraphs(orig_para_lengths)
    flat_after = _count_flat_paragraphs(new_para_lengths)
    if flat_after > flat_before:
        warnings.append(
            f"Flat paragraphs increased: {flat_before} → {flat_after}. "
            "A paragraph with 3+ sentences at uniform length is a detector tell."
        )

    # Phase 2: false-range and synonym-cycling detectors. Informational.
    fr_before = _count_false_ranges(original)
    fr_after = _count_false_ranges(humanized)
    if fr_after > 0:
        warnings.append(
            f"False-range clichés present ({fr_after}). "
            "Formulaic 'from X to Y' patterns read as AI; hand-edit or run --mode full."
        )

    sc_before = _count_synonym_cycling(original)
    sc_after = _count_synonym_cycling(humanized)
    if sc_after > sc_before:
        warnings.append(
            f"Synonym cycling in {sc_after} paragraph(s). "
            "Using 3+ synonyms for one concept in the same paragraph reads as AI."
        )

    # Contraction rate — AI text often has 0 contractions; human baseline ~17/1k words.
    cr_before = _contraction_rate(original)
    cr_after = _contraction_rate(humanized)
    if len(new_lengths) >= 8 and cr_after < 2.0:
        warnings.append(
            f"Contraction rate low ({cr_after:.1f}/1k words). "
            "Human writing uses ~17 contractions per 1k words; zero contractions is a detector signal."
        )

    cq_before = _count_curly_quotes(original)
    cq_after = _count_curly_quotes(humanized)
    if cq_after > 0:
        warnings.append(
            f"Curly quotes present ({cq_after}). Normalize to straight quotes unless house style requires them."
        )

    title_case_headings = _count_title_case_headings(humanized)
    if title_case_headings:
        warnings.append(
            f"Title-case heading(s) present ({title_case_headings}). Sentence-case headings usually read less generated."
        )

    inline_header_lists = _count_inline_header_lists(humanized)
    if inline_header_lists:
        warnings.append(
            f"Inline-header list cluster(s) present ({inline_header_lists}). Repeating '- **X:**' bullets read as templated."
        )

    generic_positive_conclusions = _count_generic_positive_conclusions(humanized)
    if generic_positive_conclusions:
        warnings.append(
            f"Generic positive conclusion(s) present ({generic_positive_conclusions}). Replace with a concrete closing claim."
        )

    outline_conclusions = _count_outline_conclusions(humanized)
    if outline_conclusions:
        warnings.append(
            f"Outline-like conclusion(s) present ({outline_conclusions}). "
            "'Despite X, Y faces challenges' is the canonical encyclopedic AI closer; "
            "rewrite with a concrete next step or hand-edit."
        )

    return ValidationResult(
        ok=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        ai_isms_before=ai_before,
        ai_isms_after=ai_after,
        burstiness_before=burst_before,
        burstiness_after=burst_after,
        sentence_length_range_after=length_range,
        flat_paragraphs_before=flat_before,
        flat_paragraphs_after=flat_after,
        false_ranges_before=fr_before,
        false_ranges_after=fr_after,
        synonym_cycling_before=sc_before,
        synonym_cycling_after=sc_after,
        contraction_rate_before=cr_before,
        contraction_rate_after=cr_after,
        curly_quotes_before=cq_before,
        curly_quotes_after=cq_after,
        title_case_headings=title_case_headings,
        inline_header_lists=inline_header_lists,
        generic_positive_conclusions=generic_positive_conclusions,
        outline_conclusions=outline_conclusions,
    )


def format_report(result: ValidationResult) -> str:
    parts: list[str] = []
    if result.ok:
        parts.append("Validation: OK")
    else:
        parts.append("Validation: FAILED")
    parts.append(f"  AI-isms: {result.ai_isms_before} → {result.ai_isms_after}")
    if result.burstiness_after > 0:
        lo, hi = result.sentence_length_range_after
        parts.append(
            f"  Burstiness σ: {result.burstiness_before:.1f} → {result.burstiness_after:.1f}"
            f" (range {lo}-{hi} words/sentence)"
        )
    if result.flat_paragraphs_after or result.flat_paragraphs_before:
        parts.append(
            f"  Flat paragraphs: {result.flat_paragraphs_before} → {result.flat_paragraphs_after}"
        )
    if result.contraction_rate_after > 0 or result.contraction_rate_before > 0:
        parts.append(
            f"  Contractions/1k: {result.contraction_rate_before:.1f} → {result.contraction_rate_after:.1f}"
        )
    for err in result.errors:
        parts.append(f"  ERROR: {err}")
    for warn in result.warnings:
        parts.append(f"  warn:  {warn}")
    return "\n".join(parts)
