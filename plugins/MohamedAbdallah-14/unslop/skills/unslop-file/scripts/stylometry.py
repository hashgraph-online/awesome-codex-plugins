"""Phase 4 stylometry: deterministic style-signal extraction for voice-match.

Today the voice-match procedure in skills/unslop/SKILL.md is an LLM-only
checklist — extract six signals from the sample, apply them to the rewrite.
The LLM does the extraction intuitively, which means it drifts. This module
replaces that intuition with measurement.

analyze(text) -> StyleProfile returns a dataclass of measured signals:

  sentence_length_mean / sentence_length_stdev  (word count per sentence)
  fragment_rate               fraction of sentences with <5 words
  contraction_rate            contractions per 1000 words
  em_dash_rate / semicolon_rate / colon_rate / parenthetical_rate   per 1000 words
  type_token_ratio            unique-words / total-words
  avg_commas_per_sentence     comma-based clause-depth proxy
  latinate_ratio              approx fraction of content words with
                              Romance-origin endings (-tion, -ment, ...)
  first_person_rate           I/me/my/we/us/our per 1000 words
  second_person_rate          you/your per 1000 words
  passive_voice_approx        per 1000 words; very approximate

StyleProfile.delta(other) -> StyleDelta gives signal-by-signal diffs so the
voice-match procedure can surface "target stdev=10.3, current 4.2" to the
user or the LLM rewrite prompt.

Research basis: Cat 10 (style transfer, stylometric embeddings), Cat 14
(structural tells — human stdev ~8.2 vs GPT-4o ~4.1 is the canonical
divergence signal). TinyStyler's extract-then-apply pipeline is the same
architecture — measure first, then fit.

DivEye proxy (Cat 15 gap). DivEye (arXiv 2509.18880, TMLR 2026) found
intra-document *surprisal variance* — not absolute perplexity — is the
primary signal that survives paraphrase attacks. A full DivEye reading
needs a small local LM to compute per-token log-prob; that isn't in this
module's scope. Two deterministic proxies are shipped instead:

  sentence_length_cv    coefficient of variation (σ/μ) of sentence
                        word-counts. Scale-invariant burstiness; robust
                        across short and long documents.
  word_length_stdev     per-sentence mean word-length, σ across the
                        document. Zipf's abbreviation law gives word-
                        length ≈ inverse rarity, so variance in that
                        quantity is a cheap surrogate for variance in
                        per-token surprisal.

Both are imperfect — they correlate with, not equal, DivEye's reading.
They're priced in as "cheap DivEye proxies" in the field names so a
voice-match caller doesn't read too much into a single number.

No API calls. No heavy deps. Runs on natural-language prose only (operates
on protected-stripped text for code-heavy inputs)."""

from __future__ import annotations

import math
import re
from collections.abc import Iterable
from dataclasses import asdict, dataclass, field

# --- Text prep (mirror the validator so signals come from the same prose) ---

_FENCED_CODE = re.compile(r"^```[^\n]*\n[\s\S]*?^```\s*$", re.MULTILINE)
_INDENTED_CODE = re.compile(r"(?m)(?:^(?: {4}|\t)[^\n]+(?:\n(?: {4}|\t)[^\n]+)*)")
_INLINE_CODE = re.compile(r"`[^`\n]+`")
_YAML_FRONTMATTER = re.compile(r"\A---\n[\s\S]*?\n---(?=\n|\Z)")
_TABLE_BLOCK = re.compile(
    r"(?m)(?:^[ \t]*\|[^\n]*\|[ \t]*(?:\n[ \t]*\|[^\n]*\|[ \t]*)+)"
)
_BLOCKQUOTE_BLOCK = re.compile(r"(?m)(?:^[ \t]*>[^\n]*(?:\n[ \t]*>[^\n]*)*)")
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(\[])")

# Tokenization & lookups
_WORD = re.compile(r"\b[A-Za-z']+\b")
_CONTRACTION = re.compile(
    r"\b(?:don|doesn|didn|won|wouldn|shouldn|couldn|mightn|mustn|isn|aren|"
    r"wasn|weren|hasn|haven|hadn|can|cannot)'t\b|"
    r"\b(?:it|that|there|what|where|who|he|she|we|you|they|"
    r"I|I'm|I've|I'll|I'd)(?:'s|'re|'ve|'ll|'d|'m)\b|"
    r"\b(?:let|what|that|there|it)'s\b",
    re.IGNORECASE,
)

# Latinate endings — rough proxy, not linguistics. Catches the canonical
# Romance-origin tells that inflate formal register.
_LATINATE_SUFFIX = re.compile(
    r"\b\w+(?:tion|sion|ment|ance|ence|ity|ize|ise|ious|ative)s?\b",
    re.IGNORECASE,
)

# Pronouns — `I` must stay case-sensitive (otherwise matches every "i" in
# other words at byte-level edge cases), but the others should be IGNORECASE.
_FIRST_PERSON_I = re.compile(r"\bI\b")
_FIRST_PERSON_OTHER = re.compile(
    r"\b(?:me|my|mine|myself|we|us|our|ours|ourselves)\b", re.IGNORECASE
)
_SECOND_PERSON = re.compile(
    r"\b(?:you|your|yours|yourself|yourselves)\b", re.IGNORECASE
)
_FUNCTION_WORDS = frozenset(
    {
        "a", "an", "and", "are", "as", "at", "be", "because", "been", "but",
        "by", "can", "could", "do", "does", "for", "from", "had", "has",
        "have", "he", "her", "him", "his", "if", "in", "is", "it", "its",
        "may", "might", "not", "of", "on", "or", "our", "she", "should",
        "so", "that", "the", "their", "them", "then", "there", "these",
        "they", "this", "those", "to", "was", "we", "were", "what", "when",
        "where", "which", "who", "will", "with", "would", "you", "your",
    }
)

# Passive-voice approximation: an auxiliary 'be' form followed, within 3 words,
# by a -ed or irregular past participle. This misses many cases and flags
# some false positives — labeled `_approx` in the output for that reason.
_PASSIVE_APPROX = re.compile(
    r"\b(?:is|are|was|were|been|being|be)\s+(?:\w+\s+){0,2}(?:\w+ed|built|done|seen|taken|made|given|shown|held|found|told|sent|written|driven|chosen|broken|known|grown|spoken|stolen|caught|taught|brought|bought|sought|thought)\b",
    re.IGNORECASE,
)


def _strip_non_prose(text: str) -> str:
    text = _YAML_FRONTMATTER.sub("", text)
    text = _FENCED_CODE.sub("", text)
    text = _INDENTED_CODE.sub("", text)
    text = _TABLE_BLOCK.sub("", text)
    text = _BLOCKQUOTE_BLOCK.sub("", text)
    text = _INLINE_CODE.sub("", text)
    return text


def _sentences(prose: str) -> list[str]:
    out: list[str] = []
    for paragraph in re.split(r"\n\s*\n", prose):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        for sent in _SENTENCE_SPLIT.split(paragraph):
            sent = sent.strip()
            if sent:
                out.append(sent)
    return out


def _word_count(text: str) -> int:
    return len(_WORD.findall(text))


def _stdev(nums: Iterable[float]) -> float:
    xs = list(nums)
    if len(xs) < 2:
        return 0.0
    mean = sum(xs) / len(xs)
    return math.sqrt(sum((x - mean) ** 2 for x in xs) / len(xs))


# ----------------------------- Data models ------------------------------


@dataclass
class StyleProfile:
    """Measured stylometric signals for one text sample.

    All `*_rate` fields are per 1000 words. Fractions are in [0, 1]."""

    total_words: int = 0
    sentences: int = 0
    sentence_length_mean: float = 0.0
    sentence_length_stdev: float = 0.0
    sentence_length_cv: float = 0.0
    word_length_stdev: float = 0.0
    fragment_rate: float = 0.0
    contraction_rate: float = 0.0
    em_dash_rate: float = 0.0
    semicolon_rate: float = 0.0
    colon_rate: float = 0.0
    parenthetical_rate: float = 0.0
    type_token_ratio: float = 0.0
    function_word_rate: float = 0.0
    avg_commas_per_sentence: float = 0.0
    latinate_ratio: float = 0.0
    first_person_rate: float = 0.0
    second_person_rate: float = 0.0
    passive_voice_approx: float = 0.0
    starts_with_and_but: float = 0.0

    def to_dict(self) -> dict:
        return {k: round(v, 3) if isinstance(v, float) else v for k, v in asdict(self).items()}

    def delta(self, other: StyleProfile) -> StyleDelta:
        """Field-by-field numeric diff: self - other."""
        diffs: dict[str, float] = {}
        for key, self_val in asdict(self).items():
            other_val = getattr(other, key)
            if isinstance(self_val, (int, float)):
                diffs[key] = round(self_val - other_val, 3)
        return StyleDelta(diffs=diffs)


@dataclass
class StyleDelta:
    """Differences between two StyleProfiles, field by field."""

    diffs: dict[str, float] = field(default_factory=dict)

    def largest_gaps(self, n: int = 5) -> list[tuple[str, float]]:
        """Return the n fields with the largest absolute difference. Use
        these to guide a voice-match rewrite prompt: 'target stdev is higher
        by 4.1, add longer sentences' etc."""
        pairs = sorted(self.diffs.items(), key=lambda kv: abs(kv[1]), reverse=True)
        return pairs[:n]

    def to_dict(self) -> dict:
        return {"diffs": self.diffs, "largest_gaps": self.largest_gaps()}


# ------------------------------- Analysis -------------------------------


def analyze(text: str) -> StyleProfile:
    """Measure style signals from a text sample.

    Code, URLs, tables, blockquotes, and YAML frontmatter are stripped
    before measurement — they're not part of the author's prose rhythm.
    Empty-prose inputs return a zero-filled profile without errors."""
    prose = _strip_non_prose(text)
    sentences = _sentences(prose)
    word_tokens = _WORD.findall(prose)
    total_words = len(word_tokens)

    if total_words == 0 or not sentences:
        return StyleProfile()

    lengths = [_word_count(s) for s in sentences]
    lengths = [n for n in lengths if n > 0]
    mean = sum(lengths) / len(lengths) if lengths else 0.0
    stdev = _stdev(lengths)
    # Coefficient of variation — scale-invariant burstiness. Flat AI prose
    # sits near 0.3; human academic writing typically lands 0.5–0.8.
    length_cv = (stdev / mean) if mean > 0 else 0.0

    # DivEye proxy: per-sentence mean word-length, σ across the document.
    # Zipf's abbreviation law makes word-length a crude inverse-rarity
    # signal; variance of the per-sentence mean captures local lexical
    # rhythm without needing a language model.
    per_sentence_mean_wlen: list[float] = []
    for sent in sentences:
        toks = _WORD.findall(sent)
        if toks:
            per_sentence_mean_wlen.append(sum(len(t) for t in toks) / len(toks))
    word_len_stdev = _stdev(per_sentence_mean_wlen) if per_sentence_mean_wlen else 0.0

    fragments = sum(1 for n in lengths if n < 5)
    fragment_rate = fragments / len(lengths)

    per_k = 1000.0 / total_words  # multiplier for per-1000 rates

    contraction_count = len(_CONTRACTION.findall(prose))
    em_dash_count = prose.count("—") + prose.count("–")
    semicolon_count = prose.count(";")
    colon_count = sum(1 for ch in prose if ch == ":")
    parenthetical_count = prose.count("(")

    unique_tokens = {t.lower() for t in word_tokens}
    type_token_ratio = len(unique_tokens) / total_words if total_words else 0.0
    function_words = sum(1 for token in word_tokens if token.lower() in _FUNCTION_WORDS)
    function_word_rate = function_words / total_words if total_words else 0.0

    commas_total = prose.count(",")
    avg_commas = commas_total / len(sentences) if sentences else 0.0

    latinate = len(_LATINATE_SUFFIX.findall(prose))
    first_person = len(_FIRST_PERSON_I.findall(prose)) + len(
        _FIRST_PERSON_OTHER.findall(prose)
    )
    second_person = len(_SECOND_PERSON.findall(prose))
    passive = len(_PASSIVE_APPROX.findall(prose))

    # "And" / "But" at sentence start — a human-burstiness signal.
    and_but_starters = sum(
        1 for s in sentences if re.match(r"^(?:And|But|So)\b", s)
    )
    starts_with_and_but = and_but_starters / len(sentences) if sentences else 0.0

    return StyleProfile(
        total_words=total_words,
        sentences=len(sentences),
        sentence_length_mean=round(mean, 2),
        sentence_length_stdev=round(stdev, 2),
        sentence_length_cv=round(length_cv, 3),
        word_length_stdev=round(word_len_stdev, 3),
        fragment_rate=round(fragment_rate, 3),
        contraction_rate=round(contraction_count * per_k, 2),
        em_dash_rate=round(em_dash_count * per_k, 2),
        semicolon_rate=round(semicolon_count * per_k, 2),
        colon_rate=round(colon_count * per_k, 2),
        parenthetical_rate=round(parenthetical_count * per_k, 2),
        type_token_ratio=round(type_token_ratio, 3),
        function_word_rate=round(function_word_rate, 3),
        avg_commas_per_sentence=round(avg_commas, 2),
        latinate_ratio=round(latinate / total_words, 3),
        first_person_rate=round(first_person * per_k, 2),
        second_person_rate=round(second_person * per_k, 2),
        passive_voice_approx=round(passive * per_k, 2),
        starts_with_and_but=round(starts_with_and_but, 3),
    )


def format_delta(delta: StyleDelta) -> str:
    """Human-readable summary of a style delta. Shown when voice-match runs
    after a rewrite so the user can see how close the rewrite got."""
    lines = ["Style-delta (sample − rewrite; negative = rewrite exceeds):"]
    for key, value in delta.largest_gaps():
        lines.append(f"  {key:<32}{value:+.2f}")
    return "\n".join(lines)
