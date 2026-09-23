#!/usr/bin/env python3
"""Extract likely legal dates and timeline phrases from plain text."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


DATE_PATTERNS = [
    r"\b\d{1,2}\s+[A-Za-ząćęłńóśźżĄĆĘŁŃÓŚŹŻ]+\s+\d{4}\b",
    r"\b\d{4}-\d{2}-\d{2}\b",
    r"\b\d{1,2}\.\d{1,2}\.\d{4}\b",
]

KEYWORD_PATTERNS = [
    r"wchodzi w życie",
    r"stosuje się od",
    r"najpóźniej do dnia",
    r"entry into force",
    r"shall apply from",
    r"no later than",
]


def extract(text: str) -> list[dict]:
    lines = text.splitlines()
    results: list[dict] = []
    for i, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        lowered = line.lower()
        has_keyword = any(re.search(k, lowered, re.IGNORECASE) for k in KEYWORD_PATTERNS)
        if not has_keyword:
            continue
        dates = []
        for pat in DATE_PATTERNS:
            dates.extend(re.findall(pat, line, flags=re.IGNORECASE))
        results.append(
            {
                "line": i,
                "text": line.strip(),
                "dates": sorted(set(dates)),
            }
        )
    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-file", required=True, help="Path to plain text file")
    args = parser.parse_args()
    text = Path(args.input_file).read_text(encoding="utf-8", errors="ignore")
    print(json.dumps({"matches": extract(text)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

