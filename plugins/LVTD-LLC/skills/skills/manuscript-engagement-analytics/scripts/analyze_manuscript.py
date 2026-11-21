#!/usr/bin/env python3
"""Analyze Markdown manuscript headings and section word counts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


DEFAULT_VALUE_RE = re.compile(
    r"\b("
    r"how|build|create|make|fix|choose|decide|deploy|verify|test|restore|"
    r"troubleshoot|checklist|workflow|steps|example|lab|exercise|diagnose|"
    r"avoid|when|why|use|turn|plan|design|audit"
    r")\b",
    re.IGNORECASE,
)


HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
WORD_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_'/-]*")


@dataclass
class Section:
    line: int
    level: int
    heading: str
    words: int
    cumulative_words: int
    flags: list[str]


def strip_markdown_noise(text: str) -> str:
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    text = re.sub(r"`[^`]+`", " ", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", " ", text)
    text = re.sub(r"\[[^\]]+\]\([^)]+\)", " ", text)
    text = re.sub(r"<[^>]+>", " ", text)
    return text


def count_words(text: str) -> int:
    return len(WORD_RE.findall(strip_markdown_noise(text)))


def parse_sections(markdown: str, max_level: int, value_re: re.Pattern[str]) -> list[Section]:
    lines = markdown.splitlines()
    headings: list[tuple[int, int, str]] = []

    for index, line in enumerate(lines, start=1):
        match = HEADING_RE.match(line)
        if not match:
            continue
        level = len(match.group(1))
        if level <= max_level:
            heading = match.group(2).strip().strip("#").strip()
            headings.append((index, level, heading))

    if not headings:
        words = count_words(markdown)
        flags = ["no-headings"]
        if words > 1200:
            flags.append("long-section")
        return [Section(1, 0, "(whole document)", words, words, flags)]

    sections: list[Section] = []
    cumulative = 0

    for idx, (line_no, level, heading) in enumerate(headings):
        next_line = headings[idx + 1][0] if idx + 1 < len(headings) else len(lines) + 1
        body = "\n".join(lines[line_no: next_line - 1])
        words = count_words(body)
        cumulative += words

        flags: list[str] = []
        if words > 2500:
            flags.append("very-long-section")
        elif words > 1200:
            flags.append("long-section")
        if not value_re.search(heading):
            flags.append("no-value-marker")
        if len(heading.split()) <= 2:
            flags.append("short-topic-heading")

        sections.append(Section(line_no, level, heading, words, cumulative, flags))

    return sections


def render_markdown(sections: list[Section]) -> str:
    rows = [
        "| Line | Lvl | Heading | Words | Cumulative | Flags |",
        "|------|-----|---------|-------|------------|-------|",
    ]
    for section in sections:
        heading = section.heading.replace("|", "\\|")
        flags = ", ".join(section.flags) if section.flags else ""
        rows.append(
            f"| {section.line} | {section.level} | {heading} | "
            f"{section.words} | {section.cumulative_words} | {flags} |"
        )
    return "\n".join(rows)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Analyze Markdown manuscript headings and section word counts.",
    )
    parser.add_argument("manuscript", help="Path to a Markdown manuscript")
    parser.add_argument(
        "--max-level",
        type=int,
        default=3,
        help="Deepest heading level to treat as a section (default: 3)",
    )
    parser.add_argument(
        "--value-regex",
        default=None,
        help="Custom regex for headings that imply reader value",
    )
    parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format (default: markdown)",
    )
    args = parser.parse_args()

    path = Path(args.manuscript)
    if not path.exists():
        print(f"error: manuscript not found: {path}", file=sys.stderr)
        return 2

    try:
        markdown = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        markdown = path.read_text(encoding="latin-1")

    if args.value_regex:
        try:
            value_re = re.compile(args.value_regex, re.IGNORECASE)
        except re.error as exc:
            print(f"error: invalid --value-regex: {exc}", file=sys.stderr)
            return 2
    else:
        value_re = DEFAULT_VALUE_RE

    sections = parse_sections(markdown, args.max_level, value_re)

    if args.format == "json":
        print(json.dumps([asdict(section) for section in sections], indent=2))
    else:
        print(render_markdown(sections))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
