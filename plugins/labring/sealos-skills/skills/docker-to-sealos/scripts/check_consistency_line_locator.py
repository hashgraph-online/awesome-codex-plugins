#!/usr/bin/env python3
"""Line-location helper with lightweight key indexing."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Optional, Sequence


SIMPLE_KEY_LINE_PATTERN = re.compile(r"^\s*([A-Za-z0-9_.\-/]+)\s*:")
SIMPLE_KEY_REGEX_PATTERN = re.compile(r"^\^\\s\*([A-Za-z0-9_.\\\-/]+)\\s\*:\$?$")
ESCAPED_CHAR_PATTERN = re.compile(r"\\(.)")


def _unescape_regex_literal(value: str) -> str:
    return ESCAPED_CHAR_PATTERN.sub(r"\1", value)


def _extract_simple_key(pattern: str) -> Optional[str]:
    match = SIMPLE_KEY_REGEX_PATTERN.fullmatch(pattern)
    if match is None:
        return None
    return _unescape_regex_literal(match.group(1))


def _build_key_index(lines: Sequence[str], start_line: int) -> Dict[str, int]:
    index: Dict[str, int] = {}
    for offset, line in enumerate(lines):
        match = SIMPLE_KEY_LINE_PATTERN.match(line)
        if match is None:
            continue
        key = match.group(1)
        index.setdefault(key, start_line + offset)
    return index


@dataclass
class LineLocator:
    start_line: int
    lines: Sequence[str]

    def __post_init__(self) -> None:
        self._key_index = _build_key_index(self.lines, self.start_line)
        self._pattern_cache: Dict[str, Optional[int]] = {}

    def find(self, pattern: str, default: Optional[int] = None) -> int:
        if pattern in self._pattern_cache:
            cached = self._pattern_cache[pattern]
            return cached if cached is not None else self._default(default)

        key = _extract_simple_key(pattern)
        if key is not None and key in self._key_index:
            line = self._key_index[key]
            self._pattern_cache[pattern] = line
            return line

        regex = re.compile(pattern)
        for offset, line in enumerate(self.lines):
            if regex.search(line):
                found = self.start_line + offset
                self._pattern_cache[pattern] = found
                return found

        self._pattern_cache[pattern] = None
        return self._default(default)

    def _default(self, default: Optional[int]) -> int:
        if default is not None:
            return default
        return self.start_line
