#!/usr/bin/env python3
"""Identify likely EU regulation from alias, CELEX-like token, or free text."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


CELEX_RE = re.compile(r"\b\d{4}[A-Z]\d{4}\b")
ACT_NUMBER_RE = re.compile(r"\b(19|20)\d{2}/\d{2,4}\b")


def parse_aliases_minimal_yaml(path: Path) -> dict[str, dict]:
    aliases: dict[str, dict] = {}
    current_key: str | None = None
    in_aliases = False

    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        if not line.strip() or line.strip().startswith("#"):
            continue
        if line.strip() == "aliases:":
            in_aliases = True
            continue
        if not in_aliases:
            continue
        if re.match(r"^\S", line):
            break

        key_match = re.match(r"^\s{2}([a-z0-9-]+):\s*$", line)
        if key_match:
            current_key = key_match.group(1)
            aliases[current_key] = {"canonical": "", "hints": []}
            continue

        if current_key is None:
            continue

        canon_match = re.match(r'^\s{4}canonical:\s*"(.*)"\s*$', line)
        if canon_match:
            aliases[current_key]["canonical"] = canon_match.group(1)
            continue

        hint_match = re.match(r'^\s{6}-\s*"(.*)"\s*$', line)
        if hint_match:
            aliases[current_key]["hints"].append(hint_match.group(1))

    return aliases


def identify(query: str, aliases: dict[str, dict]) -> dict:
    q = query.strip()
    q_low = q.lower()

    celex = CELEX_RE.search(q)
    if celex:
        return {
            "input": query,
            "match_type": "celex",
            "primary": {"celex": celex.group(0)},
            "confidence": "high",
            "note": "CELEX detected in user input; validate in EUR-Lex.",
        }

    act_number = ACT_NUMBER_RE.search(q)
    if act_number:
        return {
            "input": query,
            "match_type": "act_number",
            "primary": {"act_number": act_number.group(0)},
            "confidence": "medium",
            "note": "Act number pattern detected; resolve in EUR-Lex.",
        }

    candidates = []
    for key, data in aliases.items():
        score = 0
        if key in q_low:
            score += 3
        canonical = str(data.get("canonical", "")).lower()
        if canonical and canonical in q_low:
            score += 2
        for hint in data.get("hints", []):
            if str(hint).lower() in q_low:
                score += 1
        if score > 0:
            candidates.append(
                {
                    "alias": key,
                    "canonical": data.get("canonical", ""),
                    "score": score,
                }
            )

    candidates.sort(key=lambda x: x["score"], reverse=True)
    if candidates:
        top = candidates[0]
        return {
            "input": query,
            "match_type": "alias",
            "primary": top,
            "candidates": candidates,
            "confidence": "high" if top["score"] >= 3 else "medium",
            "note": "Alias-based match; confirm CELEX/ELI in official source.",
        }

    return {
        "input": query,
        "match_type": "topic",
        "primary": None,
        "candidates": [],
        "confidence": "low",
        "note": "No confident structured identifier found. Use EUR-Lex search.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", required=True, help="Alias/CELEX/act number/topic")
    parser.add_argument("--aliases", required=True, help="Path to regulation-aliases.yaml")
    args = parser.parse_args()

    aliases = parse_aliases_minimal_yaml(Path(args.aliases))
    print(json.dumps(identify(args.query, aliases), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

