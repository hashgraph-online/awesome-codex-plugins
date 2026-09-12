#!/usr/bin/env python3
"""Parse final provisions and relation cues from legal text (offline helper)."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


FINAL_KEYWORDS = [
    "wchodzi w życie",
    "stosuje się od",
    "uchyla się",
    "zmienia się",
    "przepisy przejściowe",
    "entry into force",
    "shall apply from",
    "shall be repealed",
    "is amended",
    "transitional provisions",
]

ARTICLE_RE = re.compile(r"\bart\.?\s*\d+[a-z]?\b|\barticle\s+\d+[a-z]?\b", re.IGNORECASE)


def extract_final_provisions(text: str) -> list[dict]:
    results: list[dict] = []
    lines = text.splitlines()
    for idx, line in enumerate(lines, start=1):
        low = line.lower()
        if not any(k in low for k in FINAL_KEYWORDS):
            continue
        articles = ARTICLE_RE.findall(line)
        results.append(
            {
                "line": idx,
                "article_refs": sorted(set(a.strip() for a in articles)),
                "text": line.strip(),
            }
        )
    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-file", required=True, help="Path to legal text file")
    args = parser.parse_args()

    text = Path(args.input_file).read_text(encoding="utf-8", errors="ignore")
    payload = {
        "final_provisions": extract_final_provisions(text),
        "disclaimer": "Wynik pomocniczy. Potwierdź przepisy i daty w EUR-Lex/OJ oraz źródłach PL.",
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

