#!/usr/bin/env python3
"""Screen plain-text technical drafts for editorial review candidates.

The output is an inventory, not an authorship detector or a grammar verdict.
Review every result in context and follow the target journal's style guide.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Iterable


DEFAULT_LAZY_TERM_PATTERNS = {
    "enable": r"\benabl(?:e|es|ed|ing)\b",
    "establish": r"\bestablish(?:es|ed|ing)?\b",
    "unusually": r"\bunusually\b",
    "together": r"\btogether\b",
}
EN_DASH = "\u2013"
EM_DASH = "\u2014"
HYPHENATED_COMPOUND_PATTERN = r"\b[A-Za-z]+(?:-[A-Za-z]+)+\b"


def count_matches(text: str, pattern: str) -> int:
    return len(re.findall(pattern, text, flags=re.IGNORECASE))


def count_spaced_characters(text: str, character: str) -> int:
    return len(re.findall(rf"\s{re.escape(character)}\s", text))


def count_unspaced_characters(text: str, character: str) -> int:
    total = text.count(character)
    return total - count_spaced_characters(text, character)


def collect_hyphenated_compounds(text: str) -> dict[str, int]:
    compounds = re.findall(HYPHENATED_COMPOUND_PATTERN, text)
    return dict(sorted(Counter(item.lower() for item in compounds).items()))


def word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)*", text))


def is_heading_line(line: str) -> bool:
    return bool(
        re.match(r"^\s{0,3}#{1,6}\s+", line)
        or re.search(r"\\(?:title|section|subsection)\{[^{}]+\}", line)
    )


def sentence_candidates(text: str) -> list[dict[str, object]]:
    """Return sentences whose structure may hide the main point from a reader."""
    body = "\n".join(line for line in text.splitlines() if not is_heading_line(line))
    normalized = re.sub(r"\s+", " ", body).strip()
    sentences = [item.strip() for item in re.split(r"(?<=[.!?])\s+", normalized) if item.strip()]
    long_sentences: list[dict[str, object]] = []
    comma_heavy_sentences: list[dict[str, object]] = []
    stacked_modifier_sentences: list[dict[str, object]] = []
    parallel_detail_sentences: list[dict[str, object]] = []
    for number, sentence in enumerate(sentences, start=1):
        words = word_count(sentence)
        comma_count = sentence.count(",")
        compound_count = len(re.findall(HYPHENATED_COMPOUND_PATTERN, sentence))
        record = {"sentence": number, "word_count": words, "text": sentence}
        if words >= 35:
            long_sentences.append(record)
        if comma_count >= 3:
            comma_heavy_sentences.append({**record, "comma_count": comma_count})
        if comma_count >= 3 and re.search(r"\b(?:and|or|nor)\b", sentence, flags=re.IGNORECASE):
            parallel_detail_sentences.append({**record, "comma_count": comma_count})
        if compound_count >= 2:
            stacked_modifier_sentences.append({**record, "hyphenated_compound_count": compound_count})
    return {
        "long_sentences": long_sentences,
        "comma_heavy_sentences": comma_heavy_sentences,
        "stacked_modifier_sentences": stacked_modifier_sentences,
        "parallel_detail_sentences": parallel_detail_sentences,
    }


PROSE_RATE_PATTERNS = {
    "which": r"\bwhich\b",
    "that": r"\bthat\b",
    "rather than": r"\brather than\b",
    "because": r"\bbecause\b",
    "therefore": r"\btherefore\b",
    "so as connective": r"[,;]\s+so\b(?!\s+that)",
    "respectively": r"\brespectively\b",
    "semicolon": r";",
    "colon": r":(?!\d)",
    "inline figure pointer": r"\((?:Figs?|Figure)\.?\s*\d+[a-z]?(?:[,-]\s*\d*[a-z]?)*\)",
    "negation": r"\b(?:does not|do not|cannot|is not|are not)\b",
}


def prose_metrics(text: str) -> dict[str, object]:
    """Sentence lengths and construction rates for comparison with the measured prose targets."""
    body = "\n".join(line for line in text.splitlines() if not is_heading_line(line))
    normalized = re.sub(r"\s+", " ", body).strip()
    protected = re.sub(
        r"\b(Figs?|Eqs?|Refs?|Secs?|al|vs|approx|No|e\.g|i\.e)\.",
        lambda match: match.group(0).replace(".", "\u0000"),
        normalized,
    )
    sentences = [item.replace("\u0000", ".").strip() for item in re.split(r"(?<=[.!?])\s+", protected)]
    lengths = sorted(word_count(sentence) for sentence in sentences if word_count(sentence) > 0)
    total = sum(lengths)
    counts = {name: count_matches(normalized, pattern) for name, pattern in PROSE_RATE_PATTERNS.items()}
    if not lengths:
        return {"sentence_count": 0, "word_count": 0, "counts": counts, "per_10000_words": {}}
    middle = len(lengths) // 2
    median = lengths[middle] if len(lengths) % 2 else (lengths[middle - 1] + lengths[middle]) / 2
    p90 = lengths[min(len(lengths) - 1, int(round(0.9 * (len(lengths) - 1))))]
    return {
        "sentence_count": len(lengths),
        "word_count": total,
        "mean_sentence_words": round(total / len(lengths), 1),
        "median_sentence_words": median,
        "p90_sentence_words": p90,
        "counts": counts,
        "per_10000_words": {name: round(10000 * count / total, 1) for name, count in counts.items()},
    }


def heading_candidates(text: str) -> list[dict[str, object]]:
    """Return catalog-like Markdown or LaTeX headings for human review."""
    headings: list[tuple[int, str]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        markdown_match = re.match(r"^\s{0,3}#{1,6}\s+(.+?)\s*$", line)
        latex_match = re.search(r"\\(?:title|section|subsection)\{([^{}]+)\}", line)
        if markdown_match:
            headings.append((line_number, markdown_match.group(1)))
        elif latex_match:
            headings.append((line_number, latex_match.group(1)))

    crowded: list[dict[str, object]] = []
    for line_number, heading in headings:
        comma_count = heading.count(",")
        has_coordination = bool(re.search(r"\b(?:and|or)\b", heading, flags=re.IGNORECASE))
        if comma_count >= 2 and has_coordination:
            crowded.append(
                {
                    "line": line_number,
                    "word_count": word_count(heading),
                    "comma_count": comma_count,
                    "text": heading,
                }
            )
    return crowded


def term_patterns(extra_terms: Iterable[str]) -> dict[str, str]:
    patterns = dict(DEFAULT_LAZY_TERM_PATTERNS)
    for term in extra_terms:
        normalized = term.strip()
        if normalized:
            patterns[normalized] = rf"\b{re.escape(normalized)}\b"
    return patterns


def build_report(text: str, source: Path, extra_terms: Iterable[str]) -> dict[str, object]:
    patterns = term_patterns(extra_terms)
    reader_focus = sentence_candidates(text)
    reader_focus["crowded_headings"] = heading_candidates(text)
    return {
        "source": str(source),
        "lazy_term_counts": {
            term: count_matches(text, pattern) for term, pattern in patterns.items()
        },
        "dash_forms": {
            "hyphen_minus": text.count("-"),
            "spaced_hyphen_minus": count_spaced_characters(text, "-"),
            "en_dash": text.count(EN_DASH),
            "spaced_en_dash": count_spaced_characters(text, EN_DASH),
            "unspaced_en_dash": count_unspaced_characters(text, EN_DASH),
            "em_dash": text.count(EM_DASH),
            "spaced_em_dash": count_spaced_characters(text, EM_DASH),
            "unspaced_em_dash": count_unspaced_characters(text, EM_DASH),
        },
        "hyphenated_compounds": collect_hyphenated_compounds(text),
        "reader_focus": reader_focus,
        "prose_metrics": prose_metrics(text),
        "editorial_note": (
            "Counts and compound inventories are review candidates, not errors or evidence of AI authorship. "
            "Check whether a term states a specific mechanism or result, whether a compound is standard or defined, "
            "whether dash spacing follows the target style, whether a reader can identify the main point before "
            "the qualifiers, and whether a long parallel list should be consolidated into a specific higher-level concept."
        ),
    }


def format_report(report: dict[str, object]) -> str:
    lazy_terms = report["lazy_term_counts"]
    dashes = report["dash_forms"]
    compounds = report["hyphenated_compounds"]
    lines = ["Technical-writing editorial screen", f"Source: {report['source']}", "", "Lazy-term counts:"]
    lines.extend(f"- {term}: {count}" for term, count in lazy_terms.items())
    lines.extend(["", "Dash forms:"])
    lines.extend(f"- {name}: {count}" for name, count in dashes.items())
    lines.extend(["", "Hyphenated-compound inventory:"])
    if compounds:
        lines.extend(f"- {term}: {count}" for term, count in compounds.items())
    else:
        lines.append("- none detected")
    lines.extend(["", "Reader-focus candidates:"])
    for category, candidates in report["reader_focus"].items():
        lines.append(f"- {category}: {len(candidates)}")
    metrics = report["prose_metrics"]
    lines.extend(["", "Prose metrics (compare with Measured Prose Targets in han-hu-research-style.md):"])
    if metrics["sentence_count"]:
        lines.append(
            f"- sentences: {metrics['sentence_count']}, words: {metrics['word_count']}, "
            f"mean {metrics['mean_sentence_words']}, median {metrics['median_sentence_words']}, "
            f"90th percentile {metrics['p90_sentence_words']} words"
        )
        lines.extend(
            f"- {name}: {count} ({metrics['per_10000_words'][name]} per 10,000 words)"
            for name, count in metrics["counts"].items()
        )
    else:
        lines.append("- no sentences detected")
    lines.extend(["", f"Editorial note: {report['editorial_note']}"])
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Screen a UTF-8 plain-text, Markdown, or LaTeX draft for editorial review candidates."
    )
    parser.add_argument("source", type=Path, help="UTF-8 text, Markdown, or LaTeX draft to inspect")
    parser.add_argument(
        "--term",
        action="append",
        default=[],
        help="Additional exact word or phrase to count; repeat as needed",
    )
    parser.add_argument("--json", action="store_true", help="Emit a machine-readable report")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.source.is_file():
        raise SystemExit(f"ERROR: source file not found: {args.source}")
    text = args.source.read_text(encoding="utf-8")
    report = build_report(text, args.source, args.term)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(format_report(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
