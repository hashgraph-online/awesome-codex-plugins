#!/usr/bin/env python3
"""Classify legal relation snippets from plain text lines."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


RELATION_PATTERNS = {
    "repeals": [r"\buchyla się\b", r"\bshall be repealed\b"],
    "amends": [r"\bzmienia się\b", r"\bis amended\b"],
    "supplements": [r"\buzupełnia\b", r"\bsupplement(s|ed)?\b"],
    "implements": [r"\bwykonawcz", r"\bimplementing\b"],
    "corrigendum": [r"\bsprostowanie\b", r"\bcorrigendum\b"],
    "consolidated_version": [r"\bwersja skonsolidowana\b", r"\bconsolidated version\b"],
    "procedure": [r"\bprocedur", r"\blegislative procedure\b"],
    "national_adaptation": [r"\bdostosow", r"\bnational adaptation\b"],
    "national_sanctions": [r"\bsankcj", r"\bpenalt(y|ies)\b"],
    "competent_authority": [r"\bwłaściwy organ\b", r"\bcompetent authority\b"],
}


def classify_line(line: str) -> list[str]:
    found = []
    low = line.lower()
    for relation, patterns in RELATION_PATTERNS.items():
        if any(re.search(p, low, flags=re.IGNORECASE) for p in patterns):
            found.append(relation)
    return found


def extract(text: str) -> list[dict]:
    out = []
    for index, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        relations = classify_line(line)
        if relations:
            out.append({"line": index, "relations": relations, "text": line.strip()})
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-file", required=True, help="Path to plain text file")
    args = parser.parse_args()
    text = Path(args.input_file).read_text(encoding="utf-8", errors="ignore")
    print(json.dumps({"relations": extract(text)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

