"""Core humanization logic: deterministic regex pass and LLM-driven rewrite.

Contract:
  - Read file at `path`.
  - Write `<stem>.original.md` backup.
  - Humanize prose. Preserve fenced code, inline code, URLs, paths, headings.
  - Validate. On failure: targeted fix (LLM mode only) up to 2 retries.
  - On final success: overwrite original. On final failure: restore original.

Intensity levels:
  - subtle   — stock vocab only. Keep structure and rhythm mostly intact.
  - balanced — default. Adds sycophancy, hedging, transition tics, em-dash cap,
               performative balance, authority tropes, signposting.
  - full     — balanced plus filler phrases, negative parallelisms, and an
               LLM pass when available.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from .reasoning import ReasoningReport, strip_reasoning_traces
from .soul import SoulReport, humanize_soul
from .structural import StructuralReport, humanize_structural
from .validate import ValidationResult, validate

MAX_RETRIES = 2
DEFAULT_ANTHROPIC_MODEL = "claude-sonnet-5"

Intensity = Literal["subtle", "balanced", "full", "anti-detector"]
VALID_INTENSITIES: tuple[Intensity, ...] = (
    "subtle",
    "balanced",
    "full",
    "anti-detector",
)


@dataclass
class Replacement:
    """One deterministic edit made by `humanize_deterministic_with_report`.

    `rule` is the category (e.g. `sycophancy`, `stock_vocab`, `authority_trope`);
    `pattern` is the human-readable summary of the regex that matched; `before`
    and `after` are the matched text and its replacement. Offsets refer to
    positions in the protected text (code blocks replaced with placeholders)
    so they're mainly useful for an audit trail, not for re-applying to raw
    text."""

    rule: str
    pattern: str
    before: str
    after: str


@dataclass
class HumanizeReport:
    """Summary of a deterministic humanization pass.

    Returned by `humanize_deterministic_with_report`. The CLI uses this for
    `--report` and `--json` output."""

    intensity: Intensity
    replacements: list[Replacement] = field(default_factory=list)
    em_dashes_before: int = 0
    em_dashes_after: int = 0
    structural: StructuralReport = field(default_factory=StructuralReport)
    soul: SoulReport = field(default_factory=SoulReport)
    reasoning: ReasoningReport = field(default_factory=ReasoningReport)

    @property
    def counts_by_rule(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for r in self.replacements:
            counts[r.rule] = counts.get(r.rule, 0) + 1
        return counts

    def to_dict(self) -> dict:
        """JSON-serializable shape. Used by the CLI's --json and --report modes."""
        return {
            "intensity": self.intensity,
            "replacements": [
                {
                    "rule": r.rule,
                    "pattern": r.pattern,
                    "before": r.before,
                    "after": r.after,
                }
                for r in self.replacements
            ],
            "counts_by_rule": self.counts_by_rule,
            "em_dashes_before": self.em_dashes_before,
            "em_dashes_after": self.em_dashes_after,
            "structural": self.structural.to_dict(),
            "soul": self.soul.to_dict(),
            "reasoning": self.reasoning.to_dict(),
        }


# ---------- Code block protection ----------

FENCED_CODE_BLOCK = re.compile(r"^```[^\n]*\n[\s\S]*?^```\s*$", re.MULTILINE)
INDENTED_CODE_BLOCK = re.compile(
    r"(?m)(?:^(?: {4}|\t)[^\n]+(?:\n(?: {4}|\t)[^\n]+)*)"
)
INLINE_CODE = re.compile(r"`[^`\n]+`")
URL_PATTERN = re.compile(r"https?://[^\s)>\]]+")
HEADING_LINE = re.compile(r"^#{1,6}[ \t]+[^\n]+", re.MULTILINE)
MD_LINK = re.compile(r"\[[^\]\n]+\]\([^)\n]+\)")
# YAML frontmatter at file start: "---\n...\n---" with the closing fence on its
# own line. The regex intentionally stops AT the closing fence and does not
# consume the newline after it, so the body below still begins at a line start
# for other regexes (e.g. line-start sycophancy openers).
YAML_FRONTMATTER = re.compile(r"\A---\n[\s\S]*?\n---(?=\n|\Z)")
# Blockquotes: contiguous block of lines starting with ">". Usually quoted examples.
BLOCKQUOTE_BLOCK = re.compile(
    r"(?m)(?:^[ \t]*>[^\n]*(?:\n[ \t]*>[^\n]*)*)"
)
# GitHub-flavored markdown table row: line contains at least one inner pipe and
# starts/ends with "|" (after optional whitespace). Table separator rows (---|---)
# and content rows are both captured. Matches contiguous table blocks.
TABLE_BLOCK = re.compile(
    r"(?m)(?:^[ \t]*\|[^\n]*\|[ \t]*(?:\n[ \t]*\|[^\n]*\|[ \t]*)+)"
)
# Quoted examples: `"delve"`, `"It's important to note that"`, `"Great question!"`.
# Rationale: when a word or phrase appears in quotes, the author is discussing
# it or reporting it, not using it (use/mention distinction). A unslop that
# strips "Great question!" from `The opener "Great question!" is a tell.` has
# destroyed the sentence's point. We match straight (") and curly (“”) quotes,
# single line only, bounded at 160 chars so we don't accidentally swallow an
# entire paragraph across two opening/closing quote marks that the author
# mismatched. Placed last in _protect so inline code and markdown links inside
# the quoted span are already placeholder-swapped before we see them.
QUOTED_PROSE = re.compile(
    r'(?:"[^"\n]{1,160}"|\u201c[^\u201d\n]{1,160}\u201d)'
)

_CURLY_QUOTE_TRANSLATION = str.maketrans(
    {
        "\u201c": '"',
        "\u201d": '"',
        "\u2018": "'",
        "\u2019": "'",
    }
)


def _normalize_quotes(text: str) -> str:
    """Normalize curly prose quotes to plain ASCII quotes."""
    return text.translate(_CURLY_QUOTE_TRANSLATION)


def _normalize_quoted_placeholders(table: dict[str, str]) -> None:
    """Normalize quote marks in protected quoted prose, but not code/URLs."""
    for placeholder, original in list(table.items()):
        if "\x00QUOTED#" in placeholder:
            table[placeholder] = _normalize_quotes(original)


def _placeholder(idx: int, kind: str) -> str:
    return f"\x00{kind}#{idx}\x00"


def _protect(text: str) -> tuple[str, dict[str, str]]:
    """Replace anything we promise to preserve with opaque placeholders.

    Covered: YAML frontmatter, fenced code, indented code, blockquotes, markdown
    tables, headings (whole line), markdown links, inline code, bare URLs.

    Order matters: the largest / most specific pattern runs first so nested
    matches (e.g. inline code inside a table row) don't double-protect or leak
    through. Fenced code is first because it can contain every other pattern.
    YAML frontmatter can only appear at file start, so it's placeholder-swapped
    before anything else that might match its interior.

    Blockquotes and tables are protected because they're the two forms of
    "illustrative prose" markdown has: the reader expects them to remain
    verbatim (quoted examples, glossary rows, reference tables). Rewriting them
    destroys the doc's meaning."""
    table: dict[str, str] = {}

    def make_sub(kind: str):
        def sub(m: re.Match) -> str:
            ph = _placeholder(len(table), kind)
            table[ph] = m.group(0)
            return ph

        return sub

    text = YAML_FRONTMATTER.sub(make_sub("YAML"), text)
    text = FENCED_CODE_BLOCK.sub(make_sub("FENCE"), text)
    text = INDENTED_CODE_BLOCK.sub(make_sub("INDENT"), text)
    text = TABLE_BLOCK.sub(make_sub("TABLE"), text)
    text = BLOCKQUOTE_BLOCK.sub(make_sub("QUOTE"), text)
    text = HEADING_LINE.sub(make_sub("HEAD"), text)
    text = MD_LINK.sub(make_sub("LINK"), text)
    text = INLINE_CODE.sub(make_sub("INLINE"), text)
    text = URL_PATTERN.sub(make_sub("URL"), text)
    # Quoted examples go last: they sit inside prose and must not shadow code /
    # links / tables above. See QUOTED_PROSE doc for use/mention rationale.
    text = QUOTED_PROSE.sub(make_sub("QUOTED"), text)

    return text, table


def _restore(text: str, table: dict[str, str]) -> str:
    # Restore in reverse protection order so outer placeholders that contain
    # earlier inner placeholders (quoted prose containing inline code) unwrap
    # before the inner placeholders are restored.
    for ph, original in reversed(table.items()):
        text = text.replace(ph, original)
    return text


# ---------- Deterministic rules ----------

# Sycophancy openers — strip whole opener at start of any line. Trailing whitespace
# is consumed so the next sentence flows naturally. Looped until stable so multiple
# stacked openers (e.g. "Great question! I'd be happy to help.") all get stripped.
SYCOPHANCY = [
    re.compile(r"^[ \t]*(?:Great|Excellent|Wonderful|Fantastic|Awesome) question[^.!\n]*[.!]?[ \t]*", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^[ \t]*(?:Certainly|Absolutely|Sure)[!.,][ \t]*", re.IGNORECASE | re.MULTILINE),
    re.compile(r"(?<=[.!?]\s)(?:Certainly|Absolutely|Sure)[!.,][ \t]*", re.IGNORECASE),
    re.compile(r"^[ \t]*I(?:'m| am) happy to help[^.!\n]*[.!]?[ \t]*", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^[ \t]*I(?:'d| would) be happy to help[^.!\n]*[.!]?[ \t]*", re.IGNORECASE | re.MULTILINE),
    re.compile(r"(?<=[.!?]\s)I(?:'d| would) be happy to help[^.!\n]*[.!]?[ \t]*", re.IGNORECASE),
    re.compile(r"^[ \t]*What a (?:fascinating|wonderful|great|terrific)[^.!\n]*[.!]?[ \t]*", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^[ \t]*I hope this (?:email|message) finds you well[.!]?[ \t]*", re.IGNORECASE | re.MULTILINE),
    re.compile(r"(?<=[.!?]\s)I hope this (?:email|message) finds you well[.!]?[ \t]*", re.IGNORECASE),
    re.compile(r"^[ \t]*Thank you for (?:your |the )?(?:question|asking)[^.!\n]*[.!]?[ \t]*", re.IGNORECASE | re.MULTILINE),
]

# Hedging stack openers — strip the opener AND the optional trailing ", " so the
# remaining sentence reads naturally.
HEDGING_OPENERS = [
    re.compile(r"\bIt(?:'s| is) (?:also )?important to note that[,]?[ \t]*", re.IGNORECASE),
    re.compile(r"\bIt(?:'s| is) (?:also )?worth (?:mentioning|noting|pointing out) that[,]?[ \t]*", re.IGNORECASE),
    re.compile(r"\bIt should be noted that[,]?[ \t]*", re.IGNORECASE),
    re.compile(r"\bIt(?:'s| is) a (?:well-known|well known) fact that[,]?[ \t]*", re.IGNORECASE),
    re.compile(r"\bNeedless to say[,]?[ \t]+", re.IGNORECASE),
    re.compile(r"\bGenerally speaking[,]?[ \t]+", re.IGNORECASE),
    re.compile(r"\bIn essence[,]?[ \t]+", re.IGNORECASE),
    re.compile(r"\bAt its core[,]?[ \t]+", re.IGNORECASE),
]

# Transitional AI tics. "Furthermore", "Moreover", "Additionally" at sentence start
# is the canonical AI-essay glue. Research category 01 (prompt engineering) and 04
# (language quality) both flag it. Strip at line-start or after ". " punctuation.
# Do NOT strip mid-sentence, where they sometimes appear legitimately.
TRANSITION_TICS = [
    re.compile(r"(^|(?<=[.!?]\s))(?:Furthermore|Moreover|Additionally)[,]?[ \t]+", re.MULTILINE),
    re.compile(r"(^[ \t]*(?:[-*+]|\d+\.)[ \t]+)(?:Furthermore|Moreover|Additionally)[,]?[ \t]+", re.MULTILINE),
    re.compile(r"(^|(?<=[.!?]\s))In conclusion[,]?[ \t]+", re.MULTILINE),
    re.compile(r"(^[ \t]*(?:[-*+]|\d+\.)[ \t]+)In conclusion[,]?[ \t]+", re.MULTILINE),
    re.compile(r"(^|(?<=[.!?]\s))To summarize[,]?[ \t]+", re.MULTILINE),
    re.compile(r"(^[ \t]*(?:[-*+]|\d+\.)[ \t]+)To summarize[,]?[ \t]+", re.MULTILINE),
    re.compile(r"(^|(?<=[.!?]\s))(?:Firstly|Secondly|Thirdly|Finally)[,]?[ \t]+", re.MULTILINE),
    re.compile(r"(^[ \t]*(?:[-*+]|\d+\.)[ \t]+)(?:Firstly|Secondly|Thirdly|Finally)[,]?[ \t]+", re.MULTILINE),
]

# Stock vocab → plain replacement. Keep the noun-context guard on `navigate`/`journey`
# so we don't replace literal navigation or actual journeys.
#
# New additions (2026-04 audit vs blader/unslop #7–#12 and
# Wikipedia:Signs_of_AI_writing): `interplay`, `intricate`, `vibrant`,
# `underscore(s)` in the figurative-verb sense, `crucial`, `vital`,
# `ever-evolving`, `ever-changing`, `in today's (digital) world`,
# `in today's (digital) age`, and `dynamic landscape` as a compound.
# Each change has a corresponding entry in validate.py's AI_ISMS so the
# validator refuses to let the count grow.
STOCK_VOCAB = [
    (re.compile(r"\bdelving into\b", re.IGNORECASE), "looking at"),
    (re.compile(r"\bdelves into\b", re.IGNORECASE), "looks at"),
    (re.compile(r"\bdelved into\b", re.IGNORECASE), "looked at"),
    (re.compile(r"\bdelve into\b", re.IGNORECASE), "look at"),
    (re.compile(r"\bdelving\b", re.IGNORECASE), "looking at"),
    (re.compile(r"\bdelves\b", re.IGNORECASE), "looks at"),
    (re.compile(r"\bdelved\b", re.IGNORECASE), "looked at"),
    (re.compile(r"\bdelve\b", re.IGNORECASE), "look at"),
    (re.compile(r"\btapestry\b", re.IGNORECASE), "blend"),
    # "stands/stood/standing as a testament to" — must run before the other
    # testament-variants so it consumes the full phrase; otherwise the shorter
    # `(?:a|the)\s+testament\s+to` pattern leaves "stands as" stranded.
    (
        re.compile(
            r"\b(?:stand(?:s|ing)?|stood)\s+as\s+(?:a|an|the)\s+testament\s+to\b",
            re.IGNORECASE,
        ),
        "shows",
    ),
    (re.compile(r"\bhas\s+been\s+(?:a|the)\s+testament\s+to\b", re.IGNORECASE), "shows"),
    (re.compile(r"\bhave\s+been\s+(?:a|the)\s+testament\s+to\b", re.IGNORECASE), "show"),
    (re.compile(r"\b(?:is|was)\s+(?:a|the)\s+testament\s+to\b", re.IGNORECASE), "shows"),
    (re.compile(r"\b(?:are|were)\s+(?:a|the)\s+testament\s+to\b", re.IGNORECASE), "show"),
    (re.compile(r"\b\w+(?:es|s|ed)\s+(?:a|the)\s+testament\s+to\b", re.IGNORECASE), r"shows"),
    (re.compile(r"\b(?:a|the)\s+testament\s+to\b", re.IGNORECASE), r"shows"),
    (re.compile(r"\btestament to\b", re.IGNORECASE), "shows"),
    (re.compile(r"\bnavigating\s+through\b", re.IGNORECASE), "working through"),
    (re.compile(r"\bnavigated\s+through\b", re.IGNORECASE), "worked through"),
    (re.compile(r"\bnavigates\s+through\b", re.IGNORECASE), "works through"),
    (re.compile(r"\bnavigate\s+through\b", re.IGNORECASE), "work through"),
    (re.compile(r"\bnavigating(?=\s+(?:the|around|these|this|that|our|complex))\b", re.IGNORECASE), "working through"),
    (re.compile(r"\bnavigated(?=\s+(?:the|around|these|this|that|our|complex))\b", re.IGNORECASE), "worked through"),
    (re.compile(r"\bnavigates(?=\s+(?:the|around|these|this|that|our|complex))\b", re.IGNORECASE), "works through"),
    (re.compile(r"\bnavigate(?=\s+(?:the|around|these|this|that|our|complex))\b", re.IGNORECASE), "work through"),
    (re.compile(r"\bembarking on (?:a |the )?journey of (\w+)ing\b", re.IGNORECASE),
     lambda m: "starting to " + m.group(1).lower()),
    (re.compile(r"\bembark(?:ed|s)? on (?:a |the )?journey of (\w+)ing\b", re.IGNORECASE),
     lambda m: "start " + m.group(1).lower() + "ing"),
    (re.compile(r"\bembarking on (?:a |the )?journey to ", re.IGNORECASE), "starting to "),
    (re.compile(r"\bembark(?:ed|s)? on (?:a |the )?journey to ", re.IGNORECASE), "start to "),
    (re.compile(r"\bembarking on\b", re.IGNORECASE), "starting"),
    (re.compile(r"\bembarks on\b", re.IGNORECASE), "starts"),
    (re.compile(r"\bembarked on\b", re.IGNORECASE), "started"),
    (re.compile(r"\bembark on\b", re.IGNORECASE), "start"),
    (re.compile(r"\bjourney(?=\s+(?:toward|to|of))\b", re.IGNORECASE), "path"),
    (re.compile(r"\brealm of\b", re.IGNORECASE), "world of"),
    (re.compile(r"\blandscape of\b", re.IGNORECASE), "world of"),
    (re.compile(r"\bpivotal\b", re.IGNORECASE), "key"),
    (re.compile(r"\bparamount\b", re.IGNORECASE), "essential"),
    (re.compile(r"\bseamlessly\b", re.IGNORECASE), "smoothly"),
    (re.compile(r"\bseamless\b", re.IGNORECASE), "smooth"),
    (re.compile(r"\bholistically\b", re.IGNORECASE), "as a whole"),
    (re.compile(r"\bholistic\b", re.IGNORECASE), "overall"),
    (re.compile(r"\bleverages\b", re.IGNORECASE), "uses"),
    (re.compile(r"\bleveraged\b", re.IGNORECASE), "used"),
    (re.compile(r"\bleveraging\b", re.IGNORECASE), "using"),
    (re.compile(r"\bleverage\b", re.IGNORECASE), "use"),
    (re.compile(r"\bcutting-edge\b", re.IGNORECASE), "advanced"),
    (re.compile(r"\ba state-of-the-art\b", re.IGNORECASE), "the latest"),
    (re.compile(r"\bstate-of-the-art\b", re.IGNORECASE), "latest"),
    (re.compile(r"\bcomprehensively\b", re.IGNORECASE), "thoroughly"),
    (re.compile(r"\bcomprehensive\b", re.IGNORECASE), "broad"),
    (re.compile(r"\brobust(?=\s+(?:and|solution|implementation|approach|system|architecture|framework|platform|infrastructure|backend|frontend|foundation|delivery|automation|CI/CD|pipeline|tooling|mechanism|strategy))\b", re.IGNORECASE), "reliable"),
    (re.compile(r"\baligns?\s+with\b", re.IGNORECASE), "matches"),
    (re.compile(r"\baligned\s+with\b", re.IGNORECASE), "matched"),
    (re.compile(r"\baligning\s+with\b", re.IGNORECASE), "matching"),
    (re.compile(r"\bfostering\b", re.IGNORECASE), "building"),
    (re.compile(r"\bfosters\b", re.IGNORECASE), "builds"),
    (re.compile(r"\bfostered\b", re.IGNORECASE), "built"),
    (re.compile(r"\bfoster\b", re.IGNORECASE), "build"),
    (re.compile(r"\bshowcasing\b", re.IGNORECASE), "showing"),
    (re.compile(r"\bshowcases\b", re.IGNORECASE), "shows"),
    (re.compile(r"\bshowcased\b", re.IGNORECASE), "showed"),
    (re.compile(r"\bshowcase\b", re.IGNORECASE), "show"),
    (re.compile(r"\bfast-paced\b", re.IGNORECASE), "fast"),
    (re.compile(r"\bgroundbreaking\b", re.IGNORECASE), "new"),
    (re.compile(r"\bwell-rounded\b", re.IGNORECASE), "rounded"),
    # Expanded vocabulary (blader/unslop + Wikipedia:Signs_of_AI_writing).
    (re.compile(r"\binterplay\s+(?:between|of)\b", re.IGNORECASE), "link between"),
    (re.compile(r"\bintricate\b", re.IGNORECASE), "detailed"),
    (re.compile(r"\bvibrant\b", re.IGNORECASE), "lively"),
    # `underscore(s)` as a figurative verb — guard so literal underscore chars
    # (in code, in variable_name discussions) pass through. We only match it in
    # verb position with a following noun phrase article.
    (re.compile(r"\bunderscores\s+(?=(?:the|our|a|an|its|their|this|that|how|why)\b)", re.IGNORECASE), "shows "),
    (re.compile(r"\bunderscored\s+(?=(?:the|our|a|an|its|their|this|that|how|why)\b)", re.IGNORECASE), "showed "),
    (re.compile(r"\bunderscoring\s+(?=(?:the|our|a|an|its|their|this|that|how|why)\b)", re.IGNORECASE), "showing "),
    (re.compile(r"\bunderscore\s+(?=(?:the|our|a|an|its|their|this|that|how|why)\b)", re.IGNORECASE), "show "),
    (re.compile(r"\bcrucial\b", re.IGNORECASE), "important"),
    (re.compile(r"\bvital(?=\s+(?:role|importance|part|component|aspect))\b", re.IGNORECASE), "important"),
    (re.compile(r"\bever[- ]evolving\b", re.IGNORECASE), "changing"),
    (re.compile(r"\bever[- ]changing\b", re.IGNORECASE), "changing"),
    (re.compile(r"\bin today'?s (?:digital )?(?:world|age|landscape|era)\b", re.IGNORECASE), "today"),
    (re.compile(r"\bdynamic landscape\b", re.IGNORECASE), "world"),
    # 2026-04 additions (Wikipedia:Signs_of_AI_writing + blader taxonomy
    # follow-up). These are the classic "purple AI" vocabulary tells that
    # routinely survive a first humanization pass.
    #
    # `meticulous(ly)` — almost never justified; "careful" or plain omission
    # reads human.
    (re.compile(r"\bmeticulously\b", re.IGNORECASE), "carefully"),
    (re.compile(r"\bmeticulous\b", re.IGNORECASE), "careful"),
    # `bustling` as a setting adjective ("bustling city", "bustling market").
    # Always AI-purple; "busy" is the human word.
    (re.compile(r"\bbustling\b", re.IGNORECASE), "busy"),
    # `paradigm shift` — dead metaphor since the 1990s; shorten to "shift".
    (re.compile(r"\bparadigm\s+shift\b", re.IGNORECASE), "shift"),
    # `game-changer` / `game-changing` — cliché. Drop to "important change"
    # or "major". Guard: only when used as noun/adj phrase, not in literal
    # game contexts (`a game-changing play in the final quarter`).
    (re.compile(r"\bgame[- ]?changers?\b(?!\s+(?:play|move|goal|call))", re.IGNORECASE), "major change"),
    (re.compile(r"\bgame[- ]?changing\b(?!\s+(?:play|move|goal|call))", re.IGNORECASE), "major"),
    # `revolutionize/s/d/ing` — verb-level hype. "change" carries the actual
    # claim; the reader can judge magnitude from the surrounding facts.
    (re.compile(r"\brevolutioniz(?:es|ed|ing)\b", re.IGNORECASE),
     lambda m: {"revolutionizes": "changes", "revolutionized": "changed", "revolutionizing": "changing"}.get(m.group(0).lower(), "changes")),
    (re.compile(r"\brevolutionize\b", re.IGNORECASE), "change"),
    # `transformative` — the adjective form of the same hype; "big" or
    # "major" conveys the same magnitude without the brochure tone.
    (re.compile(r"\btransformative\b", re.IGNORECASE), "major"),
    # `unprecedented` — flagged by AP, Reuters, and Wikipedia style. Guard:
    # keep the word in strict factual context (e.g. "unprecedented
    # {scale,levels,volume,rate,drought,heat wave}") where it genuinely
    # quantifies. Strip only the generic adjective-before-noun form in
    # connective prose.
    (re.compile(r"\bunprecedented(?=\s+(?:opportunity|opportunities|challenge|challenges|growth|success|impact|change)\b)", re.IGNORECASE), "major"),
    # `myriad (of)` / `plethora of` — dress-up words for "many" / "lots of".
    # Two forms of `myriad`: noun ("a myriad of X") and adjective
    # ("myriad X"). Both collapse to "many X".
    (re.compile(r"\ba\s+myriad\s+of\b", re.IGNORECASE), "many"),
    (re.compile(r"\bmyriad\s+(?=\w)", re.IGNORECASE), "many "),
    (re.compile(r"\ba\s+plethora\s+of\b", re.IGNORECASE), "many"),
    # `uncharted territory/waters/ground` — cliché. Prefer "new ground" or
    # plain "new {territory/area}".
    (re.compile(r"\buncharted\s+territory\b", re.IGNORECASE), "new ground"),
    (re.compile(r"\buncharted\s+waters\b", re.IGNORECASE), "new territory"),
    (re.compile(r"\buncharted\s+(?=ground|area|domain)\b", re.IGNORECASE), "new "),
    # `nuanced` as a connective adjective ("nuanced understanding",
    # "nuanced view"). Collapse to "detailed" which claims less.
    (re.compile(r"\bnuanced\b(?=\s+(?:understanding|view|perspective|approach|analysis|take))", re.IGNORECASE), "detailed"),
    # `synergy` / `synergies` / `synergize(s/d/ing)` — McKinsey-deck hype.
    # Collapse to neutral replacements.
    (re.compile(r"\bsynergies\b", re.IGNORECASE), "shared benefits"),
    (re.compile(r"\bsynergy\b", re.IGNORECASE), "shared benefit"),
    (re.compile(r"\bsynergiz(?:es|ed|ing)\b", re.IGNORECASE),
     lambda m: {"synergizes": "works well with", "synergized": "worked well with", "synergizing": "working well with"}.get(m.group(0).lower(), "works well with")),
    (re.compile(r"\bsynergize\b", re.IGNORECASE), "work well with"),
    # 2026-04-28 promotional-register additions (Wikipedia "Signs of AI writing"
    # + blader/unslop #4 promotional language). These are the postcard-and-
    # press-release adjectives that flag a paragraph as marketing-AI even when
    # the rest of the prose is clean.
    #
    # `nestled` (in/between/amongst/among/within/by) — travel-guide cliché.
    # The word adds nothing factual; the preposition does the work.
    (re.compile(r"\bnestled\s+(in|between|amongst|among|within|by)\b", re.IGNORECASE), r"\1"),
    # "rich heritage" / "deep heritage" — promotional puffery. "history" is
    # the literal word.
    (re.compile(r"\b(?:a\s+)?(?:rich|deep)\s+heritage\b", re.IGNORECASE), "history"),
    # "steeped in (rich) tradition/history/heritage" — same family. Collapse
    # to "rooted in tradition" which makes the same claim without the
    # brochure stylization.
    (
        re.compile(r"\bsteeped\s+in\s+(?:rich\s+)?(?:tradition|history|heritage)\b", re.IGNORECASE),
        "rooted in tradition",
    ),
]

# Authority tropes (blader/unslop #27). Persuasive framing that signals
# AI-voice when stacked, but a bare "at its core" sometimes appears in genuine
# writing. We strip these only when they appear at sentence start (same
# position as the existing transition tics), where the tell is strongest.
AUTHORITY_TROPES = [
    re.compile(r"(^|(?<=[.!?]\s))At its core[,]?[ \t]+", re.MULTILINE),
    re.compile(r"(^[ \t]*(?:[-*+]|\d+\.)[ \t]+)At its core[,]?[ \t]+", re.MULTILINE),
    re.compile(r"(^|(?<=[.!?]\s))In reality[,]?[ \t]+", re.MULTILINE),
    re.compile(r"(^[ \t]*(?:[-*+]|\d+\.)[ \t]+)In reality[,]?[ \t]+", re.MULTILINE),
    re.compile(r"(^|(?<=[.!?]\s))What really matters is that[,]?[ \t]+", re.MULTILINE | re.IGNORECASE),
    re.compile(r"(^|(?<=[.!?]\s))What really matters is[,]?[ \t]+", re.MULTILINE | re.IGNORECASE),
    re.compile(r"(^|(?<=[.!?]\s))Fundamentally[,]?[ \t]+", re.MULTILINE),
    re.compile(r"(^[ \t]*(?:[-*+]|\d+\.)[ \t]+)Fundamentally[,]?[ \t]+", re.MULTILINE),
    re.compile(r"(^|(?<=[.!?]\s))The heart of the matter is that[,]?[ \t]+", re.MULTILINE | re.IGNORECASE),
    re.compile(r"(^|(?<=[.!?]\s))At the heart of [^.!?\n]+? (?:is|lies)[,]?[ \t]+", re.MULTILINE | re.IGNORECASE),
]

# Signposting announcements (blader/unslop #28). Meta-commentary that
# announces the writing rather than doing the writing. Strip whole sentence
# where possible; at sentence start, strip the lead-in and let the next clause
# carry the content.
SIGNPOSTING = [
    re.compile(r"(^|(?<=[.!?]\s))Let(?:'s| us) dive in(?:to [^.!?\n]+)?[.!]?[ \t]*", re.MULTILINE | re.IGNORECASE),
    re.compile(r"(^|(?<=[.!?]\s))Let(?:'s| us) (?:break|walk) (?:this|it) down[.!]?[ \t]*", re.MULTILINE | re.IGNORECASE),
    re.compile(r"(^|(?<=[.!?]\s))Here'?s what you need to know[:.!]?[ \t]*", re.MULTILINE | re.IGNORECASE),
    re.compile(r"(^|(?<=[.!?]\s))Without further ado[,]?[ \t]*", re.MULTILINE | re.IGNORECASE),
    re.compile(r"(^|(?<=[.!?]\s))In this (?:article|post|guide|section|piece|write-up), (?:I|we)(?:'ll| will) [^.!?\n]+?[.!][ \t]*", re.MULTILINE | re.IGNORECASE),
    re.compile(r"(^|(?<=[.!?]\s))Buckle up[.!]?[ \t]*", re.MULTILINE | re.IGNORECASE),
]

KNOWLEDGE_CUTOFF = [
    re.compile(
        r"(^|(?<=[.!?]\s))As of my (?:last update|knowledge cutoff)[,;]?[ \t]*",
        re.MULTILINE | re.IGNORECASE,
    ),
    re.compile(
        r"(^|(?<=[.!?]\s))I do not have access to real-time information[,;]?[ \t]*",
        re.MULTILINE | re.IGNORECASE,
    ),
    re.compile(
        r"(^|(?<=[.!?]\s))My training data only goes up to [^,.;\n]+[,;]?[ \t]*",
        re.MULTILINE | re.IGNORECASE,
    ),
]

VAGUE_ATTRIBUTION = [
    re.compile(
        r"(^|(?<=[.!?]\s))Observers (?:say|note|suggest)(?: that)?[ \t]+",
        re.MULTILINE | re.IGNORECASE,
    ),
]

# Filler phrases (blader/unslop #23). Wordy constructions that collapse to
# one or two words with no loss of meaning. Applied only at `full` intensity:
# `due to the fact that` is occasionally justified in legal/technical text.
FILLER_PHRASES = [
    (re.compile(r"\bin order to\b", re.IGNORECASE), "to"),
    (re.compile(r"\bdue to the fact that\b", re.IGNORECASE), "because"),
    (re.compile(r"\bin spite of the fact that\b", re.IGNORECASE), "although"),
    (re.compile(r"\ba (?:wide )?(?:variety|range) of\b", re.IGNORECASE), "many"),
    (re.compile(r"\ba (?:significant|substantial) (?:amount|number) of\b", re.IGNORECASE), "many"),
    (re.compile(r"\bat (?:the|this) (?:point|moment) in time\b", re.IGNORECASE), "now"),
    (re.compile(r"\bfor (?:the|all) intents and purposes\b", re.IGNORECASE), "effectively"),
    (re.compile(r"\bin the event that\b", re.IGNORECASE), "if"),
    (re.compile(r"\bwith (?:regard|regards|respect) to\b", re.IGNORECASE), "about"),
    (re.compile(r"\bprior to\b", re.IGNORECASE), "before"),
    (re.compile(r"\bsubsequent to\b", re.IGNORECASE), "after"),
    (re.compile(r"\bthe fact that\b", re.IGNORECASE), "that"),
]

# Negative parallelisms + trailing negations (blader/unslop #10). Applied at
# `full` only. Example: "No guesswork. No bloated frameworks." — each clause
# flags as AI on its own but the stack is the real tell. We strip the
# standalone sentence form "No <noun>." that appears at paragraph end as a
# rhetorical punch. Conservative: only when the clause has no verb.
NEGATIVE_PARALLELISM = [
    # "No guesswork, no bloat, no surprises." — three-clause tricolon of negations
    re.compile(
        r"(^|(?<=[.!?]\s))No [A-Za-z][A-Za-z -]{1,20}(?:, no [A-Za-z][A-Za-z -]{1,20}){2,}[.!]",
        re.MULTILINE,
    ),
    # "Not just X, but (also) Y" / "Not only X, but (also) Y" — canonical
    # negative parallelism (Wikipedia "Signs of AI writing" + blader/unslop
    # #9). The framing is rhetorical filler; Y carries the actual claim. We
    # strip the "Not just/only X, but (also) " lead-in and let Y stand alone.
    # Bound by the next clause boundary so multi-sentence overrun is impossible.
    re.compile(
        r"(^|(?<=[.!?]\s))Not (?:just|only) [^,.!?\n]{1,80},\s*but (?:also )?",
        re.MULTILINE | re.IGNORECASE,
    ),
    # "It's not X — it's Y" — em-dash contrast form. Strip "It's not X — "
    # so "it's Y" carries the sentence.
    re.compile(
        r"(^|(?<=[.!?]\s))It'?s not [^—.!?\n]{1,80}\s+[—–]\s+(?=[Ii]t'?s )",
        re.MULTILINE,
    ),
    # "It's not X. It's Y." — period-break contrast form. Strip the negation
    # half; the affirmation half remains as its own sentence.
    re.compile(
        r"(^|(?<=[.!?]\s))It'?s not [^.!?\n]{1,80}[.!]\s+(?=[Ii]t'?s )",
        re.MULTILINE,
    ),
]

# Performative balance: collapse mid-sentence ", however," to ". " (sentence break),
# and strip "However, " at the start of any sentence (line OR after period+space).
PERFORMATIVE = [
    (re.compile(r",\s*however,\s*", re.IGNORECASE), ". "),
    (re.compile(r"(^|(?<=[.!?]\s))However,\s+", re.MULTILINE), r"\1"),
]

# --- Phase 2 new lexical families (2026-04-21) ---
#
# Source: blader/humanizer taxonomy (MIT) + Wikipedia "Signs of AI writing"
# maintained by WikiProject AI Cleanup. Each family mirrors a category named in
# that taxonomy that unslop previously did not cover. Credit due to those
# sources; original regex implementations here.
#
# Conservative stance: each pattern needs a clear semantic bound so we never
# destroy meaning. Where a pattern is borderline, we only flag in the validator
# and leave rewrite to LLM mode.

# SIGNIFICANCE_INFLATION: phrases that inflate historical importance without
# evidence. The Wikipedia article names this the single most common AI-writing
# tell on encyclopedic content. Strip the inflated framing; leave the fact.
SIGNIFICANCE_INFLATION = [
    # "marks a pivotal moment in" / "represents a defining moment in" → "happened in"
    (
        re.compile(
            r"\b(?:marks?|represents?|stands?\s+as)\s+"
            r"(?:a|an|the)\s+(?:pivotal|defining|critical|key|watershed|seminal)\s+"
            r"(?:moment|turning\s+point|milestone|chapter)\s+(?:in|for)\s+",
            re.IGNORECASE,
        ),
        "happened in ",
    ),
    # "underscores its importance" / "emphasizes the significance of X" →
    # strip the inflation; the remaining noun stands on its own.
    (
        re.compile(
            r",?\s+(?:underscor(?:es|ing)|emphasiz(?:es|ing)|highlight(?:s|ing))\s+"
            r"(?:the|its|their|his|her)\s+"
            r"(?:importance|significance|role|impact|value|relevance|necessity)"
            r"(?=[,.\s])",
            re.IGNORECASE,
        ),
        "",
    ),
    # "an enduring legacy" / "lasting legacy" → "a legacy"
    (
        re.compile(r"\b(?:an\s+)?(?:enduring|lasting|indelible)\s+legacy\b", re.IGNORECASE),
        "a legacy",
    ),
    # "leaves an indelible mark on" → "affects"
    (
        re.compile(r"\bleaves?\s+an?\s+indelible\s+mark\s+on\b", re.IGNORECASE),
        "affects",
    ),
    # "deeply rooted in" → "rooted in"
    (re.compile(r"\bdeeply\s+rooted\s+in\b", re.IGNORECASE), "rooted in"),
    # "contributing to the broader" / "shaping the broader narrative" —
    # paragraph-inflation clauses. Strip the trailing fragment.
    (
        re.compile(
            r",?\s+(?:contributing\s+to|shaping|influencing)\s+"
            r"the\s+(?:broader|wider|ongoing)\s+"
            r"(?:narrative|landscape|conversation|discourse|trajectory|movement)"
            r"(?=[,.\s])",
            re.IGNORECASE,
        ),
        "",
    ),
]

# NOTABILITY_NAMEDROPPING: "cited in <list of outlets>", "leading expert",
# "active social media presence". Classic encyclopedic puffery. Conservative:
# only the formulaic phrases, not any mention of a source.
NOTABILITY_NAMEDROPPING = [
    # "maintains an active social media presence" → removed (adds nothing)
    (
        re.compile(
            r"\b(?:maintains?|has)\s+an\s+active\s+"
            r"(?:social\s+media\s+)?presence\b"
            r"(?:\s+on\s+[A-Z][A-Za-z]+(?:\s+and\s+[A-Z][A-Za-z]+)?)?",
            re.IGNORECASE,
        ),
        "is active online",
    ),
    # "a leading expert in X" / "a leading voice on X" → "an expert on X"
    (
        re.compile(
            r"\ba\s+leading\s+(?:expert|voice|authority|figure)\s+(?:in|on)\b",
            re.IGNORECASE,
        ),
        "an expert on",
    ),
    # "renowned for his/her/their work on X" → "known for work on X"
    (
        re.compile(
            r"\brenowned\s+for\s+(?:his|her|their)\s+work\s+(?:on|in|with)\b",
            re.IGNORECASE,
        ),
        "known for work on",
    ),
    # "has been / is / was / are / were widely cited in" → "appeared in".
    # The match consumes the preceding auxiliary so we don't leave "is has
    # appeared" or "are appeared" behind.
    (
        re.compile(
            r"\b(?:(?:is|are|was|were|has\s+been|have\s+been|had\s+been)\s+)?"
            r"widely\s+(?:cited|featured|covered)\s+(?:in|by)\b",
            re.IGNORECASE,
        ),
        "appeared in",
    ),
    # "recognized globally as" / "internationally recognized as" → "known as"
    (
        re.compile(
            r"\b(?:internationally|globally)\s+recogni[sz]ed\s+as\b", re.IGNORECASE
        ),
        "known as",
    ),
]

# SUPERFICIAL_ING: trailing participle clauses that claim analysis without
# adding content. Wikipedia: "Superficial -ing analyses." Very conservative:
# only strip when the participle phrase is clearly filler (, VERBing the/its
# importance/significance/role/impact/need), i.e. the tail adds no new concrete
# information. Any tail containing a specific noun is left alone.
SUPERFICIAL_ING = [
    (
        re.compile(
            r",\s+(?:highlighting|underscoring|emphasizing|illustrating|"
            r"reflecting|showcasing|demonstrating|revealing)\s+"
            r"(?:the|its|their|his|her|a|an)\s+"
            r"(?:importance|significance|role|impact|value|need|necessity|"
            r"relevance|nature|essence|complexity|depth|breadth)"
            r"(?:\s+of\s+(?:the|this|that|these|those|its|their|his|her))?"
            r"(?=[.!?\n])",
            re.IGNORECASE,
        ),
        "",
    ),
]

# COPULA_AVOIDANCE: Latinate appositive ", being a/an/the X," used where simple
# "is" would do. Wikipedia lists this as a sign of AI-generated prose trying
# to sound formal. Only the appositive comma-bound form; bare "being" (gerund)
# is untouched.
COPULA_AVOIDANCE = [
    # ", being a reliable platform," → ", a reliable platform,"
    # Drop the "being" word; the remaining appositive is idiomatic English.
    (
        re.compile(
            r",\s+being\s+(?=(?:a|an|the)\s+[a-z])", re.IGNORECASE
        ),
        ", ",
    ),
    # 2026-04-28: full copula-avoidance set (Wikipedia "Signs of AI writing":
    # "Avoidance of copulas"). Each pattern fires only when the verb is
    # followed by a clearly promotional/positional noun phrase, so legit
    # uses like "the function serves as a callback" or "features include
    # caching" survive untouched.
    #
    # "X serves as a/an Y" → "X is a/an Y" — only when Y is in the
    # promotional/positional noun set. Verb tense preserved across forms.
    (
        re.compile(
            r"\bserves\s+as\s+(?=(?:a|an|the)\s+(?:reliable|powerful|leading|prominent|key|major|prime|cornerstone|hub|center|centre|foundation|backbone|gateway|model|standard|benchmark|symbol|reminder|catalyst|beacon|cornerstone)\b)",
            re.IGNORECASE,
        ),
        "is ",
    ),
    (
        re.compile(
            r"\bserved\s+as\s+(?=(?:a|an|the)\s+(?:reliable|powerful|leading|prominent|key|major|prime|cornerstone|hub|center|centre|foundation|backbone|gateway|model|standard|benchmark|symbol|reminder|catalyst|beacon)\b)",
            re.IGNORECASE,
        ),
        "was ",
    ),
    (
        re.compile(
            r"\bserve\s+as\s+(?=(?:a|an|the)\s+(?:reliable|powerful|leading|prominent|key|major|prime|cornerstone|hub|center|centre|foundation|backbone|gateway|model|standard|benchmark|symbol|reminder|catalyst|beacon)\b)",
            re.IGNORECASE,
        ),
        "are ",
    ),
    # "boasts a/an X" — promotional copula. Drop to "has". Verb tense
    # preserved across forms. Guards: only `(?:a|an)` continuation, so
    # "He boasts about Python" / "boasts of his work" / "boasts that ..."
    # are not touched (the AI tell is specifically `boasts a/an <noun>`).
    (re.compile(r"\bboasts\s+(?=(?:a|an)\s+[a-z])", re.IGNORECASE), "has "),
    (re.compile(r"\bboasted\s+(?=(?:a|an)\s+[a-z])", re.IGNORECASE), "had "),
    (re.compile(r"\bboasting\s+(?=(?:a|an)\s+[a-z])", re.IGNORECASE), "with "),
    (re.compile(r"\bboast\s+(?=(?:a|an)\s+[a-z])", re.IGNORECASE), "have "),
    # "features a/an Y" — promotional copula avoidance. Strict guard: only
    # when followed by an unambiguously promotional adjective. Avoids
    # collapsing "features include", "features of X", "feature-list", or
    # technical product-feature prose.
    (
        re.compile(
            r"\bfeatures\s+(?=(?:a|an)\s+(?:stunning|beautiful|breathtaking|impressive|elegant|sleek|innovative|intuitive|seamless|cutting-edge|state-of-the-art|world-class|industry-leading|best-in-class|revolutionary|groundbreaking)\b)",
            re.IGNORECASE,
        ),
        "has ",
    ),
]

# Em-dash per-paragraph cap. Research (Cat 04, Cat 05) says em-dash pileups are a
# top stylometric tell. Skill contract: no more than two em-dashes per paragraph.
# We implement this in code (`_cap_em_dashes_per_paragraph`) rather than regex,
# since regex can't count across paragraph boundaries reliably.
#
# Tricolon padding is intentionally NOT handled deterministically. A regex that
# collapses "X, Y, and Z" to "X and Y" would destroy legitimate enumerations
# ("red, white, and blue"). Tricolon tightening is a judgment call and stays
# in LLM mode only.


_LIST_MARKER = re.compile(r"^[ \t]*(?:[-*+]|\d+\.)[ \t]")


def _cap_in_block(block: str, max_dashes: int) -> str:
    protected_pair_starts: dict[int, int] = {}
    protected_pair_ends: dict[int, bool] = {}
    for match in re.finditer(
        r"—[^—.!?\n]{1,160}—(?=\s+(?:is|are|was|were|has|have|had|will|would|can|could|should)\b)",
        block,
    ):
        protected_pair_starts[match.start()] = match.end() - 1

    count = 0
    buf: list[str] = []
    chars = list(block)
    i = 0
    while i < len(chars):
        if chars[i] == "—":
            if i in protected_pair_starts:
                keep_pair = count + 2 <= max_dashes
                protected_pair_ends[protected_pair_starts[i]] = keep_pair
                if keep_pair:
                    count += 1
                    buf.append("—")
                else:
                    if buf and buf[-1] == " ":
                        buf.pop()
                    buf.append(" (")
                    if i + 1 < len(chars) and chars[i + 1] == " ":
                        i += 1
                i += 1
                continue
            if i in protected_pair_ends:
                keep_pair = protected_pair_ends[i]
                if keep_pair:
                    count += 1
                    buf.append("—")
                else:
                    if buf and buf[-1] == " ":
                        buf.pop()
                    buf.append(")")
                    if i + 1 < len(chars) and chars[i + 1] == " ":
                        buf.append(" ")
                        i += 1
                i += 1
                continue
            count += 1
            if count <= max_dashes:
                buf.append("—")
            else:
                # Replace " — " with ", " to avoid ugly " , " spacing.
                if buf and buf[-1] == " ":
                    buf.pop()
                buf.append(",")
                if i + 1 < len(chars) and chars[i + 1] == " ":
                    buf.append(" ")
                    i += 1
                else:
                    buf.append(" ")
        else:
            buf.append(chars[i])
        i += 1
    return "".join(buf)


def _cap_em_dashes_per_paragraph(text: str, max_dashes: int = 2) -> str:
    """Cap em-dashes per paragraph, with a per-item carve-out for lists.

    Research basis: Cat 04 / Cat 05 name em-dash pileups as a top stylometric
    tell; the skill contract caps them at 2 per paragraph. But a list is not
    one paragraph for rhythm purposes — each bullet has its own voice. And
    lists in the wild frequently have an intro line ("Exports:"), so we can't
    require the whole paragraph to be list-only.

    Rule:
    - Paragraphs are separated by blank lines.
    - Inside a paragraph, every line that starts with a list marker opens a new
      chunk; continuation lines and leading non-list prose attach to the current
      chunk. Each chunk gets its own em-dash budget.
    - A paragraph with zero list markers is one chunk, budget = max_dashes."""
    paragraphs = text.split("\n\n")
    for i, para in enumerate(paragraphs):
        lines = para.split("\n")

        # Any list markers at all? If not, treat the whole paragraph as one chunk.
        has_list = any(_LIST_MARKER.match(line) for line in lines)
        if not has_list:
            paragraphs[i] = _cap_in_block(para, max_dashes)
            continue

        chunks: list[list[str]] = []
        current: list[str] = []
        for line in lines:
            if _LIST_MARKER.match(line):
                if current:
                    chunks.append(current)
                current = [line]
            else:
                if current:
                    current.append(line)
                else:
                    # Leading non-list prose becomes the first chunk.
                    current = [line]
        if current:
            chunks.append(current)

        paragraphs[i] = "\n".join(
            _cap_in_block("\n".join(chunk), max_dashes) for chunk in chunks
        )

    return "\n\n".join(paragraphs)


def _tracking_sub(
    pattern: re.Pattern,
    repl,
    text: str,
    *,
    rule: str,
    log: list[Replacement] | None,
) -> str:
    """Like `pattern.sub(repl, text)` but records each replacement when `log`
    is provided. `repl` may be a string or a callable, matching `re.sub`."""
    if log is None:
        return pattern.sub(repl, text)

    def track(match: re.Match) -> str:
        before = match.group(0)
        if callable(repl):
            after = repl(match)
        else:
            try:
                after = match.expand(repl)
            except re.error:
                after = repl
        if before != after:
            log.append(
                Replacement(
                    rule=rule,
                    pattern=pattern.pattern,
                    before=before,
                    after=after,
                )
            )
        return after

    return pattern.sub(track, text)


def _resolve_toggles(
    intensity: Intensity, structural: bool | None, soul: bool | None
) -> tuple[bool, bool]:
    """Intensity-driven defaults for Phase 1 (structural) and Phase 5 (soul).

    After the Phase 6 humanness benchmark showed 100% win rate with
    structural + soul on at `balanced`, both features became part of the
    `balanced` and `full` defaults. `subtle` remains lexical-only.

    Explicit True/False overrides the intensity default. `None` falls back
    to the intensity-driven value.
    """
    intensity_wants_them = intensity in ("balanced", "full", "anti-detector")
    resolved_structural = intensity_wants_them if structural is None else structural
    resolved_soul = intensity_wants_them if soul is None else soul
    return resolved_structural, resolved_soul


def humanize_deterministic(
    text: str,
    *,
    intensity: Intensity = "balanced",
    structural: bool | None = None,
    soul: bool | None = None,
    strip_reasoning: bool = False,
) -> str:
    """Pure regex pass. Preserves code/URLs via placeholders; strips canonical AI-isms.

    `intensity` gates which rule families run:
      - subtle:   stock vocab only. Lexical-only; no structural or soul pass.
      - balanced: sycophancy, hedging openers, transition tics, stock vocab,
                  performative balance, authority tropes, signposting,
                  em-dash cap, significance-inflation, notability-namedropping,
                  copula-avoidance, plus Phase 1 structural and Phase 5 soul.
      - full:     everything balanced does, plus filler phrases,
                  negative-parallelism, superficial-ing.
      - anti-detector: full plus detector-oriented target nudges.

    `structural` and `soul` default to None and are resolved by intensity
    (on for balanced/full, off for subtle). Pass True/False to override.

    `strip_reasoning` (default False) removes agent reasoning traces —
    `<thinking>`, `<think>`, `<analysis>`, `<reasoning>`, `<scratchpad>`,
    `<plan>` wrappers and markdown `## Reasoning` / `## Thought Process` /
    `## Analysis` / `## Plan` sections — before any other rule runs. Opt-in
    because it is destructive; see `unslop/scripts/reasoning.py` for the
    full pattern list and the "reason privately, humanize publicly" research
    basis (Category 06).

    Phase 6 benchmark: balanced with both defaults wins 100% blind LLM-judge
    preference vs the original AI text.
    """
    result, _report = humanize_deterministic_with_report(
        text,
        intensity=intensity,
        structural=structural,
        soul=soul,
        strip_reasoning=strip_reasoning,
    )
    return result


def humanize_deterministic_with_report(
    text: str,
    *,
    intensity: Intensity = "balanced",
    structural: bool | None = None,
    soul: bool | None = None,
    strip_reasoning: bool = False,
) -> tuple[str, HumanizeReport]:
    """Like `humanize_deterministic` but returns an audit trail of every
    replacement made. Used by the CLI's `--report` and `--json` output."""
    if intensity not in VALID_INTENSITIES:
        raise ValueError(
            f"unknown intensity {intensity!r}; expected one of {VALID_INTENSITIES}"
        )

    structural, soul = _resolve_toggles(intensity, structural, soul)

    report = HumanizeReport(intensity=intensity)
    log = report.replacements

    # Reasoning-trace strip runs first — before em-dash measurement and
    # _protect. Stripping here means `<thinking>` wrappers don't show up
    # in em-dash counts or placeholder tables, and the stripped content
    # doesn't leak into the voice-match profile if the caller later feeds
    # the cleaned text back into stylometry.
    if strip_reasoning:
        text, report.reasoning = strip_reasoning_traces(text)

    em_dashes_before = text.count("—")

    protected, table = _protect(text)

    # Sycophancy stacks ("Great question! I'd be happy to help.") need multiple passes
    # because each strip can expose a new line-start pattern. Cap at 5 to avoid
    # pathological loops on adversarial input.
    run_balanced = intensity in ("balanced", "full", "anti-detector")
    run_full = intensity in ("full", "anti-detector")
    run_sycophancy = run_balanced
    run_hedging = run_balanced
    run_transitions = run_balanced
    run_performative = run_balanced
    run_authority = run_balanced
    run_signposting = run_balanced
    run_knowledge_cutoff = run_balanced
    run_vague_attribution = run_balanced
    run_em_dash_cap = run_balanced
    run_significance_inflation = run_balanced
    run_notability_namedropping = run_balanced
    run_copula_avoidance = run_balanced
    run_superficial_ing = run_full
    run_filler = run_full
    run_negative_parallelism = run_full

    protected = _normalize_quotes(protected)
    _normalize_quoted_placeholders(table)

    if run_sycophancy:
        for _ in range(5):
            before = protected
            for pattern in SYCOPHANCY:
                protected = _tracking_sub(pattern, "", protected, rule="sycophancy", log=log)
            if protected == before:
                break

    if run_hedging:
        for pattern in HEDGING_OPENERS:
            protected = _tracking_sub(pattern, "", protected, rule="hedging_opener", log=log)

    if run_transitions:
        for pattern in TRANSITION_TICS:
            protected = _tracking_sub(pattern, r"\1", protected, rule="transition_tic", log=log)

    if run_authority:
        for pattern in AUTHORITY_TROPES:
            protected = _tracking_sub(
                pattern, r"\1", protected, rule="authority_trope", log=log
            )

    if run_signposting:
        for pattern in SIGNPOSTING:
            protected = _tracking_sub(pattern, r"\1", protected, rule="signposting", log=log)

    if run_knowledge_cutoff:
        for pattern in KNOWLEDGE_CUTOFF:
            protected = _tracking_sub(
                pattern, r"\1", protected, rule="knowledge_cutoff", log=log
            )

    if run_vague_attribution:
        for pattern in VAGUE_ATTRIBUTION:
            protected = _tracking_sub(
                pattern, r"\1", protected, rule="vague_attribution", log=log
            )

    # Stock vocab runs at every intensity, including `subtle`.
    for pattern, repl in STOCK_VOCAB:
        protected = _tracking_sub(pattern, repl, protected, rule="stock_vocab", log=log)

    if run_significance_inflation:
        for pattern, repl in SIGNIFICANCE_INFLATION:
            protected = _tracking_sub(
                pattern, repl, protected, rule="significance_inflation", log=log
            )

    if run_notability_namedropping:
        for pattern, repl in NOTABILITY_NAMEDROPPING:
            protected = _tracking_sub(
                pattern, repl, protected, rule="notability_namedropping", log=log
            )

    if run_copula_avoidance:
        for pattern, repl in COPULA_AVOIDANCE:
            protected = _tracking_sub(
                pattern, repl, protected, rule="copula_avoidance", log=log
            )

    if run_superficial_ing:
        for pattern, repl in SUPERFICIAL_ING:
            protected = _tracking_sub(
                pattern, repl, protected, rule="superficial_ing", log=log
            )

    if run_filler:
        for pattern, repl in FILLER_PHRASES:
            protected = _tracking_sub(pattern, repl, protected, rule="filler_phrase", log=log)

    if run_negative_parallelism:
        for pattern in NEGATIVE_PARALLELISM:
            protected = _tracking_sub(
                pattern, r"\1", protected, rule="negative_parallelism", log=log
            )

    if run_performative:
        for pattern, repl in PERFORMATIVE:
            protected = _tracking_sub(pattern, repl, protected, rule="performative", log=log)

    # Phase 1 structural pass — sentence-length rebalancer + bullet-soup merger.
    # Runs after lexical scrubbing because the lexical passes remove openers and
    # phrases that would otherwise skew word counts, and before the em-dash cap
    # because splitting a long sentence can move an em-dash into its own clause
    # where it's no longer an offender. Gated off by default — see flag doc.
    if structural:
        protected = humanize_structural(protected, report=report.structural)

    if intensity == "anti-detector":
        from .lexical_targets import apply_targeted_pass, measure_gaps

        protected = apply_targeted_pass(
            protected,
            measure_gaps(_restore(protected, table)),
            intensity=intensity,
        )

    # Phase 5 soul-injection pass — contraction lift. Token-distribution lever
    # for detector resistance. Runs after lexical + structural so the
    # contractions apply to the final prose shape. Opt-in.
    if soul:
        protected = humanize_soul(protected, report=report.soul)

    if run_em_dash_cap:
        protected = _cap_em_dashes_per_paragraph(protected, max_dashes=2)

    # Cleanup: strip stranded leading punctuation that openers left behind, e.g.
    # "It's worth mentioning that, generally speaking, you should..." after both
    # openers strip leaves ", you should..." — drop the leading comma+space.
    protected = re.sub(r"^[ \t]*[,;:][ \t]*", "", protected, flags=re.MULTILINE)
    # Likewise after a paragraph break.
    protected = re.sub(r"\n\n[ \t]*[,;:][ \t]*", "\n\n", protected)

    # Capitalize first letter of every sentence/paragraph that openers exposed.
    # Sentence-start = file-start, paragraph break, OR sentence-ending punctuation+space.
    # Guard against common abbreviations (i.e., e.g., etc.) so "i.e. not" doesn't
    # become "i.e. Not". Python's re does not support variable-width lookbehind,
    # so we inspect the prefix inside the replacement callback.
    _SENTENCE_ABBREVS = re.compile(
        r"(?:^|[^a-zA-Z])(?:i\.e|e\.g|etc|vs|cf|viz|et al|Dr|Mr|Mrs|Ms|St|Jr|Sr|No)\Z"
    )

    def capitalize_after_start(m: re.Match) -> str:
        return m.group(1) + m.group(2).upper()

    def capitalize_after_sentence(m: re.Match) -> str:
        start = m.start()
        prefix = m.string[max(0, start - 10):start]
        if _SENTENCE_ABBREVS.search(prefix):
            return m.group(0)
        return m.group(1) + m.group(2).upper()

    protected = re.sub(r"(^|\n\n)([a-z])", capitalize_after_start, protected)
    protected = re.sub(r"([.!?]\s+)([a-z])", capitalize_after_sentence, protected)
    # Capitalize after bullet markers when opener stripping left lowercase.
    protected = re.sub(
        r"(^[ \t]*(?:[-*+]|\d+\.)[ \t]+)([a-z])",
        lambda m: m.group(1) + m.group(2).upper(),
        protected,
        flags=re.MULTILINE,
    )

    # Article agreement: replacements like holistic→overall or state-of-the-art→latest
    # can leave "a overall" or "a advanced" which is ungrammatical. Fix "a" → "an"
    # before words starting with a vowel sound.
    protected = re.sub(
        r"\ba(?= (?:overall|advanced|essential|important|earlier|original|"
        r"open|obvious|interesting|unusual|earlier|underlying|ongoing|optional|"
        r"older|outer|initial|ideal|upper|ultimate|average|alternate|"
        r"effective|efficient|elaborate|elegant|enormous))\b",
        "an",
        protected,
        flags=re.IGNORECASE,
    )

    # Collapse 3+ blank lines to 2 (BUT not 1 → preserve heading/paragraph spacing)
    protected = re.sub(r"\n{3,}", "\n\n", protected)
    # Strip trailing whitespace on each line so we don't ship messy diffs
    protected = re.sub(r"[ \t]+\n", "\n", protected)

    restored = _restore(protected, table)
    report.em_dashes_before = em_dashes_before
    report.em_dashes_after = restored.count("—")
    return restored, report


# ---------- LLM-driven humanization ----------


_INTENSITY_PROMPT_GUIDANCE: dict[str, str] = {
    "subtle": (
        "INTENSITY: subtle. Trim AI tells only. Keep paragraph structure and "
        "sentence count roughly intact. Do not restructure, do not merge bullets, "
        "do not break tricolons unless they are obviously redundant."
    ),
    "balanced": (
        "INTENSITY: balanced (default). Cut slop, vary rhythm, restore voice, "
        "allow contractions and short fragments. Moderate rewrite allowed. Paragraph "
        "order must stay the same; paragraph boundaries may shift."
    ),
    "full": (
        "INTENSITY: full. Strong rewrite. Restructure paragraphs for rhythm. Drop "
        "performative balance. Merge bullet-soup. Collapse filler phrases "
        "(\"in order to\" → \"to\", \"due to the fact that\" → \"because\"). Use "
        "contractions. Sound like a human with a stake."
    ),
    "anti-detector": (
        "INTENSITY: anti-detector. Use the full rewrite rules, then actively "
        "REMOVE patterns associated with AI assistant output:\n"
        "- even sentence rhythm and parallel structure\n"
        "- hedging openers (\"It's important to note\", \"In today's world\")\n"
        "- stock transitions (Furthermore, Moreover, In conclusion)\n"
        "- overly safe, symmetrical paragraphs\n"
        "Break uniform sentence shapes. Add grounded specificity only when the "
        "user supplied it. Keep meaning exact. Keep code, URLs, headings, quoted "
        "content, paths, and commands intact."
    ),
}


def _format_voice_targets(profile) -> str:
    """Render a StyleProfile as the 'VOICE SAMPLE TARGETS' prompt block.
    Separated from measurement so the same block renders for both a
    freshly-measured sample and a persisted profile from style memory."""
    return f"""
VOICE SAMPLE TARGETS (measured — match these):
- Sentence-length mean: {profile.sentence_length_mean} words (σ {profile.sentence_length_stdev}, cv {profile.sentence_length_cv})
- Word-length σ across sentences: {profile.word_length_stdev} (DivEye-style surprisal-variance proxy)
- Fragments (<5 words): {profile.fragment_rate * 100:.0f}% of sentences
- Contractions per 1k words: {profile.contraction_rate}
- Em-dash / semicolon / colon / paren rate per 1k: {profile.em_dash_rate} / {profile.semicolon_rate} / {profile.colon_rate} / {profile.parenthetical_rate}
- First-person / second-person rate per 1k: {profile.first_person_rate} / {profile.second_person_rate}
- Starts-with-And/But fraction: {profile.starts_with_and_but * 100:.0f}%
- Latinate-suffix ratio: {profile.latinate_ratio * 100:.1f}%

Match the numeric profile, not just the surface feel. If the sample is
fragment-heavy and the input text is long-sentence-heavy, cut sentences.
If the sample uses 40 contractions per 1k words and the input has none,
contract where grammatical. Higher cv and word-length σ both indicate
bursty human rhythm — mix short and long sentences, mix Anglo-Saxon
fragments with longer Latinate clauses.
"""


def _build_voice_block(sample_text: str | None, profile=None) -> str:
    """If a voice sample or profile is provided, return a prompt block with
    explicit numeric targets. Empty string otherwise.

    Sample text takes precedence — it's fresh measurement. Profile-only is
    the style-memory path: the user saved a profile and we rehydrate it
    without re-reading the original sample."""
    if profile is not None:
        return _format_voice_targets(profile)
    if not sample_text:
        return ""
    from .stylometry import analyze

    profile = analyze(sample_text)
    if profile.total_words < 50:
        return (
            "\nVOICE SAMPLE (too short to extract reliable signals): "
            "treat as rough tone guidance only.\n"
        )
    return _format_voice_targets(profile)


def _build_humanize_prompt(
    original: str,
    intensity: Intensity = "balanced",
    voice_sample: str | None = None,
    voice_profile=None,
) -> str:
    guidance = _INTENSITY_PROMPT_GUIDANCE.get(intensity, _INTENSITY_PROMPT_GUIDANCE["balanced"])
    voice_block = _build_voice_block(voice_sample, profile=voice_profile)
    return f"""Humanize this markdown so it reads like a careful human wrote it.

{guidance}
{voice_block}

STRICT RULES (preservation):
- Do NOT modify anything inside ``` code blocks
- Do NOT modify anything inside inline backticks
- Preserve ALL URLs exactly
- Preserve ALL headings exactly (text and level)
- Preserve file paths and commands
- Preserve technical terms, version numbers, error messages
- Return ONLY the humanized markdown body — do NOT wrap the entire output in a ```markdown fence or any other fence. Inner code blocks from the original stay as-is; do not add a new outer fence around the whole file.

HUMANIZATION RULES (only on natural-language prose between code regions):
- Drop sycophancy openers ("Great question!", "Certainly!", "I'd be happy to help")
- Drop stock vocab (delve, tapestry, testament, navigate, embark, journey, realm, landscape, pivotal, paramount, seamless, holistic, leverage as filler, robust as filler, comprehensive as filler, cutting-edge, state-of-the-art, interplay, intricate, vibrant, underscore [verb], crucial, vital [as filler], ever-evolving/ever-changing, "in today's digital world/age")
- Drop hedging stack openers ("It's important to note that", "It's worth mentioning that", "Generally speaking", "In essence", "At its core")
- Drop authority tropes at sentence start ("At its core", "In reality", "What really matters", "Fundamentally", "The heart of the matter")
- Drop signposting announcements ("Let's dive in", "Let's break this down", "Here's what you need to know", "Without further ado", "Buckle up")
- Drop performative balance — every claim does not need a "however"
- Engineer burstiness — mix short and long sentences deliberately (target a mix of 4–35 word sentences per paragraph)
- Tighten tricolons — "X, Y, and Z" stacks where two would suffice → keep two
- Merge bullet soup — three bullets that say the same thing → one sentence
- Vary paragraph length — no tidy five-paragraph essay shape
- Prefer active voice; avoid subjectless AI fragments ("Works great." by itself — add a subject)

ANTI-BLANDIFICATION (critical):
- Do NOT neutralize distinctive claims, opinions, or stylistic choices from the original. LLM-assisted rewrites neutralize ~70% of author voice on average (arXiv 2603.18161). Your job is to remove AI-isms, not to sand down the original's personality.
- If the original has a strong stance, keep it. If it has an unusual metaphor, keep it. Strip the slop; preserve the signal.

TWO-PASS SELF-AUDIT (required):
1. After your first rewrite, silently ask yourself: "What in the draft above still reads as obviously AI-generated? Did I accidentally neutralize the original's voice or opinions?"
2. Revise in place, then return the revised version only.
Do NOT include the audit in the output. Return the final text directly.

Pattern: [concrete observation]. [why or implication]. [what to do next].

TEXT:
{original}
"""


def _build_fix_prompt(original: str, broken_humanized: str, errors: list[str]) -> str:
    error_list = "\n".join(f"- {e}" for e in errors)
    return f"""Your previous humanization broke structural preservation. Fix it.

ERRORS:
{error_list}

ORIGINAL:
{original}

BROKEN HUMANIZED:
{broken_humanized}

Return ONLY the corrected humanized markdown. Restore every code block, URL, and heading exactly. Keep the humanization improvements that did not break structure.
"""


def _build_audit_prompt(humanized: str, original: str | None = None) -> str:
    original_block = f"\n## Original text\n{original}\n" if original is not None else ""
    return f"""You are reviewing a piece of writing for residual AI-generated patterns.

Be specific. Cite phrases and structural tells. Do not rewrite. Diagnose only.
{original_block}
## Text to audit
{humanized}

## Question
What makes the text above read as AI-generated? List specific phrases, sentence shapes, structural patterns, and rhetorical moves. If nothing reads as AI, say so explicitly.
"""


def _build_audit_rewrite_prompt(audit_findings: str, current: str) -> str:
    return f"""You are rewriting a text to fix specific AI-generated patterns.

Apply only the fixes listed. Preserve all code, URLs, paths, headings, and quoted content byte-identical. Do not introduce new patterns.

## Findings to fix
{audit_findings}

## Current text
{current}

## Instruction
Rewrite the current text addressing only the findings above. Output the rewritten text only, no preamble.
"""


def _call_anthropic_sdk(prompt: str) -> str | None:
    try:
        from anthropic import Anthropic
    except ImportError:
        return None
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return None
    client = Anthropic()
    msg = client.messages.create(
        model=os.environ.get("UNSLOP_MODEL", DEFAULT_ANTHROPIC_MODEL),
        max_tokens=8000,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(block.text for block in msg.content if hasattr(block, "text")).strip()


def _call_claude_cli(prompt: str) -> str | None:
    if shutil.which("claude") is None:
        return None
    proc = subprocess.run(
        ["claude", "--print"],
        input=prompt,
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    if proc.returncode != 0:
        sys.stderr.write(f"claude CLI returned {proc.returncode}: {proc.stderr.strip()[:200]}\n")
        return None
    return proc.stdout.strip()


def _call_llm(prompt: str) -> str | None:
    return _call_anthropic_sdk(prompt) or _call_claude_cli(prompt)


def _word_count_for_audit(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text))


def humanize_llm(
    text: str,
    *,
    intensity: Intensity = "balanced",
    voice_sample: str | None = None,
    voice_profile=None,
    audit: bool | None = None,
) -> str:
    from .detect import has_sensitive_content

    if has_sensitive_content(text):
        raise RuntimeError(
            "Refusing to send secret-like content to LLM mode. "
            "Use --deterministic for a local-only pass."
        )

    prompt = _build_humanize_prompt(
        text,
        intensity=intensity,
        voice_sample=voice_sample,
        voice_profile=voice_profile,
    )
    result = _call_llm(prompt)
    if result is None:
        raise RuntimeError(
            "LLM mode requires either ANTHROPIC_API_KEY (with `anthropic` package) "
            "or the `claude` CLI on PATH. Use --deterministic for offline use."
        )
    pass1 = _strip_outer_fence(result)

    if audit is None:
        audit = intensity in ("full", "anti-detector")
    if not audit or _word_count_for_audit(pass1) < 100:
        return pass1

    findings = _call_llm(_build_audit_prompt(pass1, text))
    if findings is None:
        return pass1
    pass2_raw = _call_llm(_build_audit_rewrite_prompt(findings, pass1))
    if pass2_raw is None:
        return pass1
    pass2 = _strip_outer_fence(pass2_raw)
    result2 = validate(text, pass2)
    if not result2.ok:
        sys.stderr.write("audit rewrite failed preservation; using first-pass output\n")
        return pass1
    return pass2


def _strip_outer_fence(text: str) -> str:
    """If the LLM wrapped the whole reply in ```markdown ... ```, strip that fence."""
    stripped = text.strip()
    m = re.match(r"^```(?:markdown|md)?\s*\n([\s\S]*?)\n```\s*$", stripped)
    if m:
        return m.group(1)
    return text


def _llm_fix(original: str, broken: str, errors: list[str]) -> str | None:
    prompt = _build_fix_prompt(original, broken, errors)
    result = _call_llm(prompt)
    if result is None:
        return None
    return _strip_outer_fence(result)


# ---------- Top-level orchestrator ----------


@dataclass
class HumanizeOutcome:
    """Result of `humanize_file_ex`. Carries enough information for the CLI's
    --json, --diff, and --report modes without duplicating the read/write."""

    ok: bool
    original: str
    humanized: str
    validation: ValidationResult | None = None
    report: HumanizeReport | None = None
    attempts: int = 1
    error: str | None = None


def humanize_file(
    path: Path,
    *,
    deterministic: bool = False,
    intensity: Intensity = "balanced",
    backup: bool = True,
) -> bool:
    """Legacy entry point: read, humanize, write, return success bool."""
    outcome = humanize_file_ex(
        path,
        deterministic=deterministic,
        intensity=intensity,
        backup=backup,
        write=True,
    )
    return outcome.ok


def humanize_file_ex(
    path: Path,
    *,
    deterministic: bool = False,
    intensity: Intensity = "balanced",
    backup: bool = True,
    write: bool = True,
    structural: bool | None = None,
    soul: bool | None = None,
    voice_sample: str | None = None,
    voice_profile=None,
    strip_reasoning: bool = False,
    audit: bool | None = None,
) -> HumanizeOutcome:
    """Rich entry point. Returns the full outcome (humanized text, report,
    validation) regardless of whether we actually wrote to disk. The CLI uses
    `write=False` for `--dry-run` and `--diff`.

    `structural=True` enables the Phase 1 structural pass (sentence splitting
    and bullet-soup merging). Opt-in until we default it on for `balanced`
    after benchmark validation.

    `soul=True` enables the Phase 5 soul pass (contraction lift).

    `strip_reasoning=True` (deterministic mode only) removes agent reasoning
    traces (`<thinking>`, `<think>`, `## Reasoning` sections, etc.) before
    humanization. Stripped content is written to `<stem>.reasoning.md` next
    to the target file when `write=True`, so the audit trail survives.

    `voice_sample` (LLM mode only) is a text sample whose stylometric profile
    the rewrite should match. Ignored in deterministic mode."""
    original_text = path.read_text(encoding="utf-8")
    backup_path = path.with_name(path.stem + ".original.md")

    if backup and write and backup_path.exists():
        return HumanizeOutcome(
            ok=False,
            original=original_text,
            humanized=original_text,
            error=(
                f"Backup already exists at {backup_path}. "
                "Remove or rename it before re-humanizing."
            ),
        )

    if deterministic:
        humanized, report = humanize_deterministic_with_report(
            original_text,
            intensity=intensity,
            structural=structural,
            soul=soul,
            strip_reasoning=strip_reasoning,
        )
        # Validation compares the humanized text against the text the
        # regex rules actually saw. When we stripped reasoning traces
        # first, we need to validate against the stripped input, not the
        # raw input — otherwise the validator correctly flags the
        # reasoning block as missing content.
        validate_against = (
            original_text.replace(report.reasoning.stripped_content, "")
            if strip_reasoning and report.reasoning.blocks_stripped
            else original_text
        )
        # Fall back to the raw input if the replace didn't match cleanly
        # (stripping reformats whitespace, so an exact substring match
        # isn't guaranteed). The simpler and correct approach: re-strip
        # the original and compare against that.
        if strip_reasoning and report.reasoning.blocks_stripped:
            validate_against, _ = strip_reasoning_traces(original_text)
        result = validate(validate_against, humanized)
        if not result.ok:
            return HumanizeOutcome(
                ok=False,
                original=original_text,
                humanized=humanized,
                validation=result,
                report=report,
                error="Deterministic pass produced a structural change.",
            )
        if write:
            if backup:
                backup_path.write_text(original_text, encoding="utf-8")
            path.write_text(humanized, encoding="utf-8")
            if strip_reasoning and report.reasoning.blocks_stripped:
                reasoning_path = path.with_name(path.stem + ".reasoning.md")
                reasoning_path.write_text(
                    report.reasoning.stripped_content + "\n", encoding="utf-8"
                )
        return HumanizeOutcome(
            ok=True,
            original=original_text,
            humanized=humanized,
            validation=result,
            report=report,
        )

    # LLM mode.
    if backup and write:
        backup_path.write_text(original_text, encoding="utf-8")

    try:
        # Only pass voice_sample when set so legacy test mocks that don't
        # accept the kwarg continue to work.
        llm_kwargs: dict = {"intensity": intensity}
        if voice_sample is not None:
            llm_kwargs["voice_sample"] = voice_sample
        if voice_profile is not None:
            llm_kwargs["voice_profile"] = voice_profile
        if audit is not None:
            llm_kwargs["audit"] = audit
        humanized = humanize_llm(original_text, **llm_kwargs)
    except RuntimeError as exc:
        if backup and write:
            backup_path.unlink(missing_ok=True)
        return HumanizeOutcome(
            ok=False,
            original=original_text,
            humanized=original_text,
            error=str(exc),
        )

    last_result = None
    for attempt in range(MAX_RETRIES + 1):
        last_result = validate(original_text, humanized)
        if last_result.ok:
            if write:
                path.write_text(humanized, encoding="utf-8")
            return HumanizeOutcome(
                ok=True,
                original=original_text,
                humanized=humanized,
                validation=last_result,
                attempts=attempt + 1,
            )
        if attempt < MAX_RETRIES:
            fixed = _llm_fix(original_text, humanized, last_result.errors)
            if fixed is None:
                break
            humanized = fixed

    if write:
        path.write_text(original_text, encoding="utf-8")
    return HumanizeOutcome(
        ok=False,
        original=original_text,
        humanized=humanized,
        validation=last_result,
        attempts=MAX_RETRIES + 1,
        error="Could not produce a structurally valid humanization.",
    )
