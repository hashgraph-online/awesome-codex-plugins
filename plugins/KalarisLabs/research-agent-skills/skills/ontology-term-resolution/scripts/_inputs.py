"""Shared input collection for the ontology-term-resolution command-line scripts."""
from __future__ import annotations

import sys
from pathlib import Path


def _clean_lines(raw: str) -> list[str]:
    """Return stripped, non-empty, non-comment lines from raw text."""
    lines = []
    for line in raw.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            lines.append(line)
    return lines


def collect_inputs(positional: list[str], input_path: str | None) -> list[str]:
    """Collect unique strings from positional values, an input file or ``-``, or stdin.

    Order is preserved and duplicates are dropped. Stdin is read as a fallback
    only when nothing else supplied a value and stdin is not a terminal.
    """
    values: list[str] = list(positional)
    if input_path:
        raw = (
            sys.stdin.read()
            if input_path == "-"
            else Path(input_path).read_text(encoding="utf-8")
        )
        values.extend(_clean_lines(raw))
    if not values and not sys.stdin.isatty():
        values.extend(_clean_lines(sys.stdin.read()))
    seen: set[str] = set()
    unique = []
    for value in values:
        if value not in seen:
            seen.add(value)
            unique.append(value)
    return unique
