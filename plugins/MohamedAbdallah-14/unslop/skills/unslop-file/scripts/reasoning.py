"""Strip agent reasoning traces from text before humanization runs.

Research basis — "reason privately, humanize publicly" (Category 06):

  - Turpin et al. / Anthropic 2023/2025: chain-of-thought output can diverge
    from the computation that produced the answer. A published CoT trace is
    not a transcript of what the model computed; it's a secondary artifact
    that often leaks stylistic tells ("Let me think step by step...", "First,
    I need to...", "Wait, let me reconsider...").
  - Muennighoff et al. s1 (arXiv 2501.19393, EMNLP 2025): budget forcing with
    "Wait" tokens makes reasoning visible in the token stream.
  - Anthropic Claude 4 / Claude 4.5 ship `<thinking>` wrappers; DeepSeek-R1 /
    Qwen ship `<think>` tags; OpenAI o-series ships internal reasoning that
    sometimes leaks into final output. Agents that write files frequently
    include these as prose artifacts.
  - Karpathy's IQ-vs-EQ split: humanizers should operate on the public
    output, not the reasoning trace. The two have different goals and
    different evaluation criteria.

This module strips six reasoning-trace shapes before humanization begins.
It is destructive by design: stripped content is returned in the report so
the CLI can write a `.reasoning.md` sidecar if the caller wants an audit
trail. Default is OFF. Callers must opt in (`--strip-reasoning` on the
CLI, `strip_reasoning=True` on the API).

Shapes handled:

  1. `<thinking>...</thinking>`   Claude-style
  2. `<think>...</think>`          DeepSeek-R1 / Qwen
  3. `<analysis>...</analysis>`    generic analysis wrapper
  4. `<reasoning>...</reasoning>`  generic reasoning wrapper
  5. `<scratchpad>...</scratchpad>`  agent scratchpad
  6. `## Reasoning` / `## Thought Process` / `## Internal Reasoning` /
     `## My Analysis` / `## Plan` / `## Scratch` / `## Thinking`
     markdown sections — stripped from the heading down to the next
     heading of equal or lower depth (or EOF).

Explicitly NOT stripped:

  - Free-text preludes like "Let me think step by step..." outside of a
    tagged block. Too ambiguous; the prose may be legitimate explanation.
    A downstream humanizer rule (signposting / sycophancy) catches the
    worst offenders at sentence level.
  - Reasoning that appears inside code fences — code is protected upstream.
  - Reasoning tags inside inline code or quoted prose ("`<thinking>` is
    how Claude emits its reasoning"). We only match when the tag opens at
    line-start or after whitespace, so a word-like use in prose survives.

No API calls. No heavy deps. Deterministic."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# XML-style reasoning wrappers. Match multi-line with DOTALL so `.` crosses
# newlines. Non-greedy so adjacent blocks are not merged into one giant
# match. The opening tag must sit at line start or after whitespace; this
# avoids matching inline uses like "...the `<thinking>` tag..." in prose.
_XML_TAGS = (
    "thinking",
    "think",
    "analysis",
    "reasoning",
    "scratchpad",
    "plan",
)

_XML_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = tuple(
    (
        tag,
        re.compile(
            rf"(?:^|(?<=\s))<{tag}\b[^>]*>[\s\S]*?</{tag}>\s*",
            re.IGNORECASE,
        ),
    )
    for tag in _XML_TAGS
)

# Markdown section headings that introduce reasoning. Match the heading
# line and everything until the next `#`-heading (any depth) or EOF.
# The heading match uses a lookahead so the *next* heading is not consumed.
_MARKDOWN_HEADINGS = (
    "Reasoning",
    "Thought Process",
    "Thoughts",
    "Thinking",
    "Internal Reasoning",
    "Internal Monologue",
    "My Analysis",
    "Analysis",
    "Plan",
    "Scratch",
    "Scratchpad",
    "Chain of Thought",
    "CoT",
)

_MARKDOWN_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = tuple(
    (
        heading,
        re.compile(
            rf"(?m)^[ \t]*#{{1,6}}[ \t]+{re.escape(heading)}[ \t]*$"
            rf"[\s\S]*?(?=^[ \t]*#{{1,6}}[ \t]+\S|\Z)",
        ),
    )
    for heading in _MARKDOWN_HEADINGS
)


@dataclass
class ReasoningReport:
    """Audit trail for reasoning-trace stripping.

    `blocks_stripped` is the count of matches across all patterns.
    `patterns_matched` lists which named patterns fired at least once.
    `stripped_content` is the concatenation of every stripped block,
    separated by `\\n---\\n` — useful for the CLI's `.reasoning.md`
    sidecar. Empty when nothing fired."""

    blocks_stripped: int = 0
    patterns_matched: list[str] = field(default_factory=list)
    stripped_content: str = ""

    def to_dict(self) -> dict:
        return {
            "blocks_stripped": self.blocks_stripped,
            "patterns_matched": list(self.patterns_matched),
            "stripped_bytes": len(self.stripped_content),
        }


def strip_reasoning_traces(text: str) -> tuple[str, ReasoningReport]:
    """Strip agent reasoning traces from `text`.

    Returns the cleaned text and a `ReasoningReport` documenting what was
    removed. The caller is responsible for deciding whether to persist
    the stripped content (CLI writes it to a `.reasoning.md` sidecar on
    --strip-reasoning; the Python API exposes it for inspection).

    Idempotent: running twice on the same output is a no-op on the second
    pass (all traces were removed on the first). Safe on empty input."""
    if not text:
        return text, ReasoningReport()

    report = ReasoningReport()
    cleaned = text
    stripped_parts: list[str] = []

    for name, pattern in _XML_PATTERNS:
        matches = list(pattern.finditer(cleaned))
        if matches:
            report.patterns_matched.append(f"xml:{name}")
            for m in matches:
                stripped_parts.append(m.group(0).strip())
            report.blocks_stripped += len(matches)
            cleaned = pattern.sub("", cleaned)

    for name, pattern in _MARKDOWN_PATTERNS:
        matches = list(pattern.finditer(cleaned))
        if matches:
            report.patterns_matched.append(f"markdown:{name}")
            for m in matches:
                stripped_parts.append(m.group(0).strip())
            report.blocks_stripped += len(matches)
            cleaned = pattern.sub("", cleaned)

    # Collapse the triple-newline runs that stripping often leaves behind.
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    # Trim leading whitespace that may now sit before the first real content.
    cleaned = cleaned.lstrip("\n")

    if stripped_parts:
        report.stripped_content = "\n---\n".join(stripped_parts)

    return cleaned, report
