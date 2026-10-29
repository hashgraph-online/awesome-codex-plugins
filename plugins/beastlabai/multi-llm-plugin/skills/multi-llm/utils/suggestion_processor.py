"""Suggestion processor module for handling multi-LLM review suggestions."""

import heapq
import json
import math
import re
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

from .schema_validator import drop_non_record_entries


class SuggestionGroup:
    """A group of similar suggestions from multiple models."""

    def __init__(self, category: str, theme: str):
        self.category = category
        self.theme = theme
        self.suggestions: List[Dict[str, Any]] = []
        self.models: List[str] = []
        self.priority_score: float = 0.0
        self.validation_status: Optional[str] = None
        self.validation_reason: Optional[str] = None

    def add_suggestion(self, suggestion: Dict[str, Any], model: str) -> None:
        """Add a suggestion to this group."""
        self.suggestions.append(suggestion)
        if model not in self.models:
            self.models.append(model)
        self._recalculate_priority()

    def _recalculate_priority(self) -> None:
        """Recalculate priority based on model consensus and importance."""
        base_score = len(self.models)

        importance_weights = {"high": 3, "medium": 2, "low": 1}
        for suggestion in self.suggestions:
            importance = suggestion.get("importance", "medium")
            base_score += importance_weights.get(importance, 1)

        self.priority_score = base_score

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "category": self.category,
            "theme": self.theme,
            "suggestions": self.suggestions,
            "models": self.models,
            "priority_score": self.priority_score,
            "validation_status": self.validation_status,
            "validation_reason": self.validation_reason,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SuggestionGroup":
        """Create from dictionary."""
        group = cls(data["category"], data["theme"])
        group.suggestions = data.get("suggestions", [])
        group.models = data.get("models", [])
        group.priority_score = data.get("priority_score", 0.0)
        group.validation_status = data.get("validation_status")
        group.validation_reason = data.get("validation_reason")
        return group


def extract_suggestions_from_review(
    review_text: str,
    model_name: str
) -> List[Dict[str, Any]]:
    """
    Extract structured suggestions from a model's review text.

    Args:
        review_text: Raw review output from a model
        model_name: Name of the model that produced the review

    Returns:
        List of suggestion dictionaries
    """
    suggestions = []

    # Try to extract JSON if present
    json_match = re.search(r'```(?:json)?\s*([\[\{][\s\S]*?[\]\}])\s*```', review_text)
    if json_match:
        try:
            parsed = json.loads(json_match.group(1))
            if isinstance(parsed, list):
                # Same guard as the aggregation sites: `item["source_model"] = …`
                # is an item assignment, and a fenced array can carry a bare
                # scalar the same way a model result file can.
                for item in drop_non_record_entries(
                    parsed, model_name, noun="suggestions"
                ):
                    item["source_model"] = model_name
                    suggestions.append(item)
                return suggestions
        except json.JSONDecodeError:
            pass

    # Fall back to pattern-based extraction
    suggestion_patterns = [
        r'(?:Suggestion|Issue|Problem|Concern|Improvement)[\s:]+(.+?)(?=\n\n|\n-|\n\d+\.|\Z)',
        r'-\s+(.+?)(?=\n-|\n\n|\Z)',
        r'\d+\.\s+(.+?)(?=\n\d+\.|\n\n|\Z)',
    ]

    for pattern in suggestion_patterns:
        matches = re.findall(pattern, review_text, re.IGNORECASE | re.DOTALL)
        for match in matches:
            text = match.strip()
            if len(text) > 20:  # Filter out too-short matches
                suggestions.append({
                    "title": text[:100] + "..." if len(text) > 100 else text,
                    "desc": text,
                    "importance": _infer_importance(text),
                    "type": _infer_type(text),
                    "source_model": model_name,
                })

    return suggestions


def _infer_importance(text: str) -> str:
    """Infer importance level from suggestion text."""
    text_lower = text.lower()

    high_indicators = ["critical", "must", "required", "security", "bug", "error", "fail"]
    low_indicators = ["minor", "optional", "consider", "could", "nice to have", "style"]

    for indicator in high_indicators:
        if indicator in text_lower:
            return "high"

    for indicator in low_indicators:
        if indicator in text_lower:
            return "low"

    return "medium"


def _infer_type(text: str) -> str:
    """Infer suggestion type from text."""
    text_lower = text.lower()

    type_indicators = {
        "bug": ["bug", "error", "fix", "broken", "incorrect"],
        "missing": ["missing", "add", "include", "need"],
        "improvement": ["improve", "enhance", "better", "optimize"],
        "style": ["style", "format", "naming", "convention"],
        "scope": ["scope", "out of scope", "beyond", "different"],
    }

    for stype, indicators in type_indicators.items():
        for indicator in indicators:
            if indicator in text_lower:
                return stype

    return "improvement"


# ---------------------------------------------------------------------------
# Similarity
#
# The rules below are deliberately small, dependency-free (stdlib only) and
# explainable — no embeddings, no model call, no corpus but the suggestions
# being grouped:
#
#   1. Text is reduced to *content tokens*: lowercased, identifiers split on
#      camelCase/dots/underscores (``maxSpeedMultiplier`` → ``max speed
#      multiplier``), punctuation stripped, generic English stopwords and
#      review boilerplate removed ("specify", "undefined", "add", "plan",
#      "task" …, which every review suggestion says and none of them means),
#      then lightly stemmed (``charges``/``charging``/``charged`` → ``charg``).
#      Inline code spans are tokenized like prose rather than dropped: a
#      backticked identifier is the *most* specific thing a reviewer can name,
#      and two reviewers who both write ``Car.reset()`` or ``#boost-meter``
#      agree about something no paraphrase of theirs shares. Dropping them
#      cost real merges — on the 2026-09-13 racing-game review one model put
#      ``Car.reset()`` in backticks and the other in prose, and their two
#      findings about resetting boost state never met. The ubiquitous ones
#      (``CONFIG``, the plan's own subject) are handled by rule 2, not by a
#      blanket exclusion.
#   2. Every token is weighted by how *rare* it is in the set being grouped
#      (inverse document frequency). In a review of a boost feature, "boost"
#      is in 43 of 56 suggestions and separates nothing, while "particle" or
#      "lerp" is in two and separates everything. That weighting is what a
#      hand-maintained per-project stopword list would otherwise have to do.
#   3. Title and body are scored separately. A shared title token is worth
#      roughly ten times a shared body token (a title is ~5 tokens against a
#      body's ~40), but the body still has to agree: an accidental title
#      overlap ("Boost activation semantics undefined" vs. "Opponent boost
#      scope undefined") is exactly what a title-only score gets wrong.
#      A *rare* word in both titles gets a small channel of its own (0.04):
#      two titles that both say "particles", "HUD" or "reset" are naming the
#      same subject, and dice — which divides by both titles' total mass —
#      dilutes that signal to nothing when one of the two titles is long.
#      Only words rarer than roughly a fifth of the set count, so "boost" in
#      a boost review, or "lap" in a plan with a lap section, never does.
#   4. ``reference``/``section`` — or, for a code-review finding, the file it
#      is anchored to — is a weak tiebreak (0.08) and a matching ``type`` is a
#      weaker one (0.02): types are model-assigned and noisy, so a type match
#      can only settle a near-tie, never carry a merge (the previous flat 0.2
#      bonus put half of a 0.4 threshold on it). The section bonus is scaled
#      by the section's own rarity for the same reason tokens are: "### 4.
#      Physics Integration", cited by 14 of 55 suggestions, separates nothing,
#      while "### 6. HUD Updates", cited by three, separates a lot. Flat, it
#      was a systematic bonus handed to every pair inside the review's biggest
#      section — which is where the near-threshold false pairs live. Two
#      findings naming *different* files never merge at all.
# ---------------------------------------------------------------------------

#: Generic English function words — they say nothing about *what* a
#: suggestion is about.
_STOPWORDS = frozenset("""
a about above across after again against all almost already also although always am among an and
another any anything are around as at be because been before being below beside between both but by
can cannot could did do does doing done down during each either else enough etc even ever every few
for from further had has have having he her here hers herself him himself his how however if in
inside instead into is it its itself just least less like made make many may me might more most much
must my myself neither never no nor not nothing now of off often on once one only onto or other
others ought our ours out over own per perhaps rather same she should since so some something still
such than that the their theirs them themselves then there therefore these they thing things this
those though through thus to too under until up upon us use used using very via was way we well
were what when where whether which while who whom whose why will with within without would yet you
your yours
""".split())

#: Review boilerplate: the vocabulary of *critiquing a document* rather than
#: of the subject under review. These show up in nearly every suggestion of
#: every review ("the plan does not specify…", "add a section that defines…"),
#: so shared occurrences are evidence of the genre, not of agreement.
_REVIEW_WORDS = frozenset("""
specify specifies specified specifying specification specifications unspecified underspecified
define defines defined defining definition undefined
document documents documented documenting undocumented
describe describes described mention mentions mentioned
clarify clarifies clarified clarification unclear ambiguous vague
add adds added adding note noted notes
consider considers ensure ensures provide provides recommend recommends
suggest suggests suggested propose proposes proposed
plan plans section sections task tasks
""".split())

#: Suffix stripping, longest first. Deliberately cruder than a real stemmer:
#: both sides of every comparison get the same treatment, so the only cost of
#: a crude rule is an occasional missed match.
_SUFFIX_RULES = (("ies", "y"), ("ing", ""), ("ed", ""), ("s", ""))

_CODE_SPAN = re.compile(r"`[^`]*`")
_WORD_CHUNK = re.compile(r"[A-Za-z][A-Za-z0-9_.\-]*")
_SUB_WORD = re.compile(r"[A-Z]+(?![a-z])|[A-Z]?[a-z0-9]+")

#: Component weights. They sum to 1.0, so a score is always in [0, 1].
WEIGHT_TITLE = 0.33
WEIGHT_BODY = 0.53
WEIGHT_REFERENCE = 0.08
WEIGHT_TYPE = 0.02
WEIGHT_TITLE_RARITY = 0.04

#: An IDF at or above this counts a shared title word as *naming the subject*
#: rather than as vocabulary. ``log(1 + N/(1+df)) >= 1.6`` is roughly
#: "at most a fifth of the set uses it" for a review-sized N, and for a small
#: set it is unreachable by any word two suggestions share — so the channel is
#: inert on the handful-of-suggestions inputs where no frequency is meaningful.
TITLE_RARITY_FLOOR = 1.6

#: The IDF at which a rarity channel saturates — one word this rare is all the
#: evidence the channel can offer. ``log(1 + N/(1+df))`` reaches 3.0 at about
#: two occurrences in fifty.
RARITY_FULL = 3.0

#: Tuned on two real 3-reviewer plan reviews (see
#: ``tests/test_suggestion_processor.py::TestRealWorldGrouping``). On the
#: 55-suggestion 2026-09-13 review the band that keeps every coherent group
#: intact is 0.196–0.205, and this sits in it: below 0.196 a third finding
#: joins the lap-hook pair, above 0.205 the game-state pair comes apart.
DEFAULT_SIMILARITY_THRESHOLD = 0.20


def _stem(word: str) -> str:
    """Reduce a word to a form its whole family shares.

    Strip one plural/participle suffix, collapse a doubled consonant, then
    drop a trailing "e" — which is what puts ``charge``, ``charges``,
    ``charging`` and ``charged`` on one token instead of two.
    """
    for suffix, replacement in _SUFFIX_RULES:
        if word.endswith(suffix) and len(word) - len(suffix) >= 4:
            word = word[: -len(suffix)] + replacement
            break
    if len(word) >= 5 and word[-1] == word[-2] and word[-1] not in "lsz":
        word = word[:-1]  # "dragged" -> "dragg" -> "drag"
    if len(word) >= 4 and word.endswith("e"):
        word = word[:-1]  # "charge" -> "charg", matching "charging"
    return word


_REVIEW_STEMS = frozenset(_stem(word) for word in _REVIEW_WORDS)


def _uncode(match: "re.Match") -> str:
    """Unwrap an inline code span, keeping its identifiers as ordinary words.

    Surrounded by spaces so ``foo`bar`baz`` cannot weld two words together.
    """
    return " " + match.group(0).strip("`") + " "


def normalize_tokens(text: str) -> List[str]:
    """Reduce free text to comparable content tokens (see the note above)."""
    if not text:
        return []
    text = _CODE_SPAN.sub(_uncode, text)
    tokens: List[str] = []
    for chunk in _WORD_CHUNK.findall(text):
        for part in _SUB_WORD.findall(chunk):
            word = "".join(ch for ch in part.lower() if ch.isalnum())
            if len(word) < 3 or word in _STOPWORDS or word in _REVIEW_WORDS:
                continue
            word = _stem(word)
            if len(word) < 3 or word in _STOPWORDS or word in _REVIEW_STEMS:
                continue
            tokens.append(word)
    return tokens


def _body_text(suggestion: Dict[str, Any]) -> str:
    """The suggestion's prose body, under whichever key this phase uses."""
    for key in ("desc", "details", "description"):
        value = suggestion.get(key)
        if value:
            return str(value)
    return ""


_LINE_SUFFIX = re.compile(r":\d+(?:-\d+)?$")


def _file_anchor(suggestion: Dict[str, Any]) -> str:
    """The file a code-review finding is anchored to, as a comparable path.

    Line ranges are dropped and separators normalized, so
    ``"src\\security.py:120-134"`` becomes ``"src/security.py"``. Plan-review
    suggestions have no file and get ``""``.
    """
    raw = str(suggestion.get("file", suggestion.get("fileRef", "")) or "").strip()
    if not raw:
        return ""
    raw = _LINE_SUFFIX.sub("", raw.replace("\\", "/")).strip().lower()
    while raw.startswith("./"):
        raw = raw[2:]
    return raw.strip("/")


def _files_disagree(a: str, b: str) -> bool:
    """True when two anchors name files that cannot be the same file.

    One anchor may be a suffix of the other — models spell the same file as
    ``src/security.py`` and ``security.py`` — but only at a path boundary, so
    ``a/utils.py`` and ``b/utils.py`` stay two files.
    """
    if not a or not b or a == b:
        return False
    return not (a.endswith("/" + b) or b.endswith("/" + a))


def _reference_tokens(suggestion: Dict[str, Any]) -> set:
    """Each section a suggestion cites, as a normalized set.

    A composite reference (``"## Design Requirements / ### 7. Lap Integration"``)
    names two sections and is split on a *delimited* ``/`` or on ``,`` — the
    same rule ``html_report_generator.split_section_refs`` buckets by, so a
    bare slash inside a heading (``"### 5. Visual/Audio Effects (Juice)"``)
    stays one section. Splitting it made a review's single most-cited section
    look like two, and two suggestions citing it looked like they agreed
    twice.
    """
    raw = str(suggestion.get("reference", suggestion.get("section", "")) or "")
    parts = re.split(r"\s+/\s+|\s*,\s*", raw)
    return {part.strip().lstrip("#").strip().lower() for part in parts if part.strip()}


def compute_token_weights(suggestions: Iterable[Dict[str, Any]]) -> Dict[str, float]:
    """Inverse document frequency of every token across ``suggestions``.

    ``log(1 + N / (1 + df))``: across fifty-odd suggestions a token every one
    of them uses bottoms out near 0.7, one used by two lands near 3.3 — so a
    rare word is worth several common ones, without any word being silenced
    outright. Order-independent, so a re-grouping of the same set produces
    identical weights (and identical ``group_hash``es).
    """
    total = 0
    document_frequency: Dict[str, int] = {}
    for suggestion in suggestions:
        total += 1
        seen = set(normalize_tokens(str(suggestion.get("title", "") or "")))
        seen |= set(normalize_tokens(_body_text(suggestion)))
        for token in seen:
            document_frequency[token] = document_frequency.get(token, 0) + 1
    return {
        token: math.log(1.0 + total / (1.0 + count))
        for token, count in document_frequency.items()
    }


def compute_section_weights(
    suggestions: Iterable[Dict[str, Any]]
) -> Dict[str, float]:
    """Inverse document frequency of every cited section across ``suggestions``.

    The same measure as ``compute_token_weights``, over the sections a review
    cites rather than the words it uses, and it answers the same question: a
    plan's busiest section is where most of its findings land and says nothing
    about which of them are the same finding, while a section only three
    suggestions reach is a strong hint that those three are about one thing.
    """
    total = 0
    document_frequency: Dict[str, int] = {}
    for suggestion in suggestions:
        total += 1
        for section in _reference_tokens(suggestion):
            document_frequency[section] = document_frequency.get(section, 0) + 1
    return {
        section: math.log(1.0 + total / (1.0 + count))
        for section, count in document_frequency.items()
    }


def _mass(tokens: Iterable[str], token_weights: Optional[Mapping[str, float]]) -> float:
    """Total weight of a token set (its count when no weights are supplied)."""
    if token_weights is None:
        return float(len(list(tokens)))
    return sum(token_weights.get(token, 1.0) for token in tokens)


def _weighted_dice(a: set, b: set, token_weights) -> float:
    """Symmetric overlap — the right shape for two short, comparable titles."""
    total = _mass(a, token_weights) + _mass(b, token_weights)
    if total <= 0:
        return 0.0
    return 2.0 * _mass(a & b, token_weights) / total


def _weighted_cosine(a: set, b: set, token_weights) -> float:
    """Length-tolerant overlap — bodies differ wildly in length by model."""
    mass_a = _mass(a, token_weights)
    mass_b = _mass(b, token_weights)
    if mass_a <= 0 or mass_b <= 0:
        return 0.0
    return _mass(a & b, token_weights) / math.sqrt(mass_a * mass_b)


def _overlap(a: set, b: set) -> float:
    """Unweighted containment, used only for the reference tiebreak."""
    if not a or not b:
        return 0.0
    return len(a & b) / min(len(a), len(b))


def _section_agreement(
    a: set, b: set, section_weights: Optional[Mapping[str, float]]
) -> float:
    """Containment over cited sections, scaled by how rare those sections are.

    With no weights (a one-off ``compute_similarity``) this is the plain
    containment it has always been — there is no set to measure rarity over.
    """
    base = _overlap(a, b)
    if base <= 0.0 or not section_weights:
        return base
    shared = a & b
    mean = sum(section_weights.get(section, 1.0) for section in shared) / len(shared)
    return base * min(1.0, mean / RARITY_FULL)


def _title_rarity(a: set, b: set, token_weights: Optional[Mapping[str, float]]) -> float:
    """How much distinctive vocabulary the two titles literally share.

    Only tokens at or above ``TITLE_RARITY_FLOOR`` count, so this fires on
    "particles" and not on the word the whole review is about. With no weights
    every token is 1.0, below the floor, and the channel is silent.
    """
    if not token_weights:
        return 0.0
    mass = sum(
        weight
        for weight in (token_weights.get(token, 1.0) for token in (a & b))
        if weight >= TITLE_RARITY_FLOOR
    )
    return min(1.0, mass / RARITY_FULL) if mass > 0 else 0.0


def _prepare(suggestion: Dict[str, Any]) -> Tuple[set, set, set, str, str]:
    """Tokenize a suggestion once, for repeated pairwise comparison."""
    title = set(normalize_tokens(str(suggestion.get("title", "") or "")))
    body = set(normalize_tokens(_body_text(suggestion))) | title
    return (
        title,
        body,
        _reference_tokens(suggestion),
        str(suggestion.get("type", "") or ""),
        _file_anchor(suggestion),
    )


def _similarity(
    a: Tuple[set, set, set, str, str],
    b: Tuple[set, set, set, str, str],
    token_weights: Optional[Mapping[str, float]],
    section_weights: Optional[Mapping[str, float]] = None,
) -> float:
    """Score two prepared suggestions."""
    if _files_disagree(a[4], b[4]):
        # A code-review finding is anchored to a file, and its fix lands in
        # that file. Two findings naming different files are two fixes — one
        # validation verdict cannot speak for both, and a report that merges
        # them hides one of the two places that needs work. Word-identical
        # findings in two files are the *most* likely pair to be merged by
        # text alone, and the most certainly distinct.
        #
        # The rule is deliberately one-sided: a *shared* file is no evidence
        # of sameness (one module hosts a dozen unrelated findings), where a
        # shared plan section — one of eight a reviewer chose deliberately —
        # is, which is why that one earns the weak positive below and this one
        # only refuses. Plan-review suggestions declare no file at all.
        return 0.0
    score = (
        WEIGHT_TITLE * _weighted_dice(a[0], b[0], token_weights)
        + WEIGHT_BODY * _weighted_cosine(a[1], b[1], token_weights)
        + WEIGHT_REFERENCE * _section_agreement(a[2], b[2], section_weights)
        + WEIGHT_TYPE * (1.0 if a[3] and a[3] == b[3] else 0.0)
        + WEIGHT_TITLE_RARITY * _title_rarity(a[0], b[0], token_weights)
    )
    return min(1.0, score)


def compute_similarity(
    s1: Dict[str, Any],
    s2: Dict[str, Any],
    token_weights: Optional[Mapping[str, float]] = None,
    section_weights: Optional[Mapping[str, float]] = None,
) -> float:
    """
    Compute a meaning-tracking similarity score between two suggestions.

    Args:
        s1: First suggestion
        s2: Second suggestion
        token_weights: Optional token → weight map from
            ``compute_token_weights()`` over the whole set being grouped.
            Omitted (the default), every token counts the same — fine for a
            one-off comparison, weaker for clustering, which is why
            ``group_similar_suggestions`` always passes one. Without it the
            title-rarity channel is silent: rarity is a property of a set.
        section_weights: Optional section → weight map from
            ``compute_section_weights()``. Omitted, a shared section scores
            plain containment, as it did before sections were weighted.

    Returns:
        Similarity score between 0 and 1
    """
    return _similarity(_prepare(s1), _prepare(s2), token_weights, section_weights)


#: A theme is a label, not a sentence — it goes in a heading, a table cell and
#: a validation prompt, all of which need it short. Sixty characters is about
#: what fits without wrapping, and most suggestion titles are shorter.
THEME_MAX_CHARS = 60


def summarize_theme(title: Any) -> str:
    """A group's theme: its representative's title, cut at a word boundary.

    A title that fits comes through untouched. A longer one is cut back to the
    last whole word inside the budget and marked with an ellipsis, so the label
    reads as a shortened title rather than as a typo — a hard ``[:50]`` slice
    produced "Activation edge vs. held-key semantics left undefi", which is
    what a reader has to decode before they can use it.
    """
    text = str(title or "").strip()
    if not text:
        return "Untitled"
    if len(text) <= THEME_MAX_CHARS:
        return text
    cut = text[:THEME_MAX_CHARS]
    boundary = cut.rfind(" ")
    # Refuse a boundary that would throw away most of the budget: a title whose
    # first "word" is longer than that is a path or an identifier, and half of
    # it still identifies the group better than nothing does.
    if boundary >= THEME_MAX_CHARS // 2:
        cut = cut[:boundary]
    return cut.rstrip(" \t,;:.-–—") + "…"


def group_similar_suggestions(
    suggestions: List[Dict[str, Any]],
    similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD
) -> List[SuggestionGroup]:
    """
    Group similar suggestions together.

    Agglomerative **average-link** clustering: every suggestion starts alone,
    the two most similar clusters merge, and a merged cluster's similarity to
    every other is the average over all cross pairs. It stops when no pair
    reaches ``similarity_threshold``.

    Average-link is what keeps a group about one thing. The previous greedy
    single-link pass admitted a suggestion that beat the threshold against
    *any* one member, so A–B–C chained into a group even when C had nothing to
    do with A — on a real review that put "Boost activation semantics
    undefined", "Opponent boost scope undefined" and "Opponent parity is left
    as unresolved scope" in one group, the third having joined at 0.267
    against the second alone. Under average-link a newcomer must look like the
    group as a whole, and the merge order is a property of the scores rather
    than of arrival order.

    Cost is O(n²) similarity computations (each suggestion is tokenized once);
    merging then walks a heap of the pairs that actually cleared the
    threshold, which on real inputs is a small fraction of them.

    Args:
        suggestions: List of all suggestions from all models
        similarity_threshold: Minimum similarity to group suggestions

    Returns:
        List of SuggestionGroup objects
    """
    # Rank by importance (HIGH first), then by a stable content signature, so
    # every tiebreak below — which cluster absorbs which, the representative
    # whose title names the group, the order members are listed in — is a pure
    # function of the suggestion *set* and never of input order.
    #
    # Clustering itself is already order-independent (average-link merges in
    # score order), but the ranking still matters: the same suggestions
    # arriving in a different order (``results.items()`` order in the live
    # review vs. ``glob`` order during ``--reaggregate``) must produce
    # byte-identical groups, or validation — tasked against the original
    # grouping — mis-joins the re-grouped output by stale index.
    importance_order = {"high": 0, "medium": 1, "low": 2}

    def _stable_sort_key(item: Tuple[int, Dict[str, Any]]):
        _, s = item
        return (
            importance_order.get(s.get("importance", "medium"), 1),
            str(s.get("file", "")),
            str(s.get("line_range", s.get("line", ""))),
            str(s.get("title", "")),
            str(s.get("desc", "")),
            str(s.get("source_model", s.get("model", ""))),
        )

    if not suggestions:
        return []

    ranked = [idx for idx, _ in sorted(enumerate(suggestions), key=_stable_sort_key)]
    rank = {idx: position for position, idx in enumerate(ranked)}
    count = len(suggestions)

    token_weights = compute_token_weights(suggestions)
    section_weights = compute_section_weights(suggestions)
    prepared = [_prepare(s) for s in suggestions]

    # Cluster state. A cluster is identified by the index of its
    # highest-ranked member; ``members`` holds every index it covers and
    # ``pair_similarity`` the current average-link score of each live pair.
    members: Dict[int, List[int]] = {idx: [idx] for idx in range(count)}
    pair_similarity: Dict[Tuple[int, int], float] = {}
    candidates: List[Tuple[float, int, int, int, int]] = []

    def _key(a: int, b: int) -> Tuple[int, int]:
        return (a, b) if a < b else (b, a)

    def _offer(a: int, b: int, score: float) -> None:
        """Queue a pair that currently clears the threshold."""
        if score >= similarity_threshold:
            low, high = (a, b) if rank[a] < rank[b] else (b, a)
            heapq.heappush(candidates, (-score, rank[low], rank[high], low, high))

    for i in range(count):
        for j in range(i + 1, count):
            score = _similarity(
                prepared[i], prepared[j], token_weights, section_weights
            )
            pair_similarity[(i, j)] = score
            _offer(i, j, score)

    while candidates:
        negative_score, _, _, a, b = heapq.heappop(candidates)
        score = -negative_score
        # Skip entries superseded by a merge or by a recomputed average.
        if a not in members or b not in members:
            continue
        if pair_similarity.get(_key(a, b)) != score:
            continue

        keeper, absorbed = (a, b) if rank[a] < rank[b] else (b, a)
        size_keeper = len(members[keeper])
        size_absorbed = len(members[absorbed])

        for other in list(members):
            if other in (keeper, absorbed):
                continue
            merged_score = (
                size_keeper * pair_similarity.get(_key(keeper, other), 0.0)
                + size_absorbed * pair_similarity.get(_key(absorbed, other), 0.0)
            ) / (size_keeper + size_absorbed)
            pair_similarity[_key(keeper, other)] = merged_score
            pair_similarity.pop(_key(absorbed, other), None)
            _offer(keeper, other, merged_score)

        members[keeper] = members[keeper] + members[absorbed]
        del members[absorbed]
        pair_similarity.pop(_key(keeper, absorbed), None)

    groups: List[SuggestionGroup] = []
    for cluster_id in sorted(members, key=lambda idx: rank[idx]):
        cluster = sorted(members[cluster_id], key=lambda idx: rank[idx])
        representative = suggestions[cluster[0]]
        group = SuggestionGroup(
            category=representative.get("type", "improvement"),
            theme=summarize_theme(representative.get("title", "Untitled")),
        )
        for idx in cluster:
            suggestion = suggestions[idx]
            group.add_suggestion(suggestion, suggestion.get("source_model", "unknown"))
        groups.append(group)

    # Sort groups by priority (stable, so equal scores keep rank order)
    groups.sort(key=lambda g: g.priority_score, reverse=True)

    return groups


def deduplicate_suggestions(suggestions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Remove duplicate suggestions.

    Args:
        suggestions: List of suggestions

    Returns:
        Deduplicated list
    """
    seen_hashes = set()
    unique = []

    for suggestion in suggestions:
        # Create a hash from title and description
        hash_str = f"{suggestion.get('title', '')}|{suggestion.get('desc', '')}"
        if hash_str not in seen_hashes:
            seen_hashes.add(hash_str)
            unique.append(suggestion)

    return unique


def merge_suggestions_by_model(
    reviews: Dict[str, str]
) -> List[Dict[str, Any]]:
    """
    Extract and merge suggestions from multiple model reviews.

    Args:
        reviews: Dictionary mapping model names to their review text

    Returns:
        Merged list of suggestions
    """
    all_suggestions = []

    for model_name, review_text in reviews.items():
        suggestions = extract_suggestions_from_review(review_text, model_name)
        all_suggestions.extend(suggestions)

    return deduplicate_suggestions(all_suggestions)


def filter_by_importance(
    groups: List[SuggestionGroup],
    min_importance: str = "low"
) -> List[SuggestionGroup]:
    """
    Filter suggestion groups by minimum importance.

    Args:
        groups: List of suggestion groups
        min_importance: Minimum importance level ("low", "medium", "high")

    Returns:
        Filtered list of groups
    """
    importance_levels = {"low": 0, "medium": 1, "high": 2}
    min_level = importance_levels.get(min_importance, 0)

    def group_meets_threshold(group: SuggestionGroup) -> bool:
        for suggestion in group.suggestions:
            importance = suggestion.get("importance", "medium")
            if importance_levels.get(importance, 1) >= min_level:
                return True
        return False

    return [g for g in groups if group_meets_threshold(g)]


def export_groups_to_json(groups: List[SuggestionGroup]) -> str:
    """Export suggestion groups to JSON string."""
    return json.dumps([g.to_dict() for g in groups], indent=2)


def import_groups_from_json(json_str: str) -> List[SuggestionGroup]:
    """Import suggestion groups from JSON string."""
    data = json.loads(json_str)
    return [SuggestionGroup.from_dict(item) for item in data]
