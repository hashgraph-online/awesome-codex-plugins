"""Benchmark humanization quality across a directory of sample files.

Usage:
  python3 -m scripts.benchmark <samples_dir> [--llm]

For each .md file in samples_dir, runs the unslop (deterministic by default)
and reports word count delta and AI-ism delta.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .humanize import humanize_deterministic, humanize_llm
from .validate import validate


def _word_count(text: str) -> int:
    return len(text.split())


def _format_row(name: str, orig_words: int, new_words: int, ai_before: int, ai_after: int) -> str:
    delta_words = new_words - orig_words
    pct_words = (delta_words / orig_words * 100) if orig_words else 0
    return (
        f"  {name:<40} "
        f"{orig_words:>5} → {new_words:>5} ({pct_words:+5.1f}%)  "
        f"AI-isms {ai_before:>3} → {ai_after:>3}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("samples_dir", type=Path)
    parser.add_argument("--llm", action="store_true", help="Use LLM mode instead of deterministic")
    args = parser.parse_args()

    samples_dir: Path = args.samples_dir
    if not samples_dir.is_dir():
        sys.stderr.write(f"Not a directory: {samples_dir}\n")
        sys.exit(1)

    files = sorted(samples_dir.glob("*.md"))
    files = [f for f in files if not f.name.endswith(".original.md")]
    if not files:
        sys.stderr.write(f"No .md files found in {samples_dir}\n")
        sys.exit(1)

    mode = "LLM" if args.llm else "deterministic"
    sys.stdout.write(f"Benchmarking {len(files)} file(s) in {mode} mode\n\n")

    total_orig_words = 0
    total_new_words = 0
    total_ai_before = 0
    total_ai_after = 0
    failures: list[str] = []

    for f in files:
        original = f.read_text(encoding="utf-8")
        try:
            humanized = humanize_llm(original) if args.llm else humanize_deterministic(original)
        except Exception as exc:
            failures.append(f"{f.name}: {exc}")
            continue

        result = validate(original, humanized)
        ow, nw = _word_count(original), _word_count(humanized)
        sys.stdout.write(_format_row(f.name, ow, nw, result.ai_isms_before, result.ai_isms_after) + "\n")
        if not result.ok:
            failures.append(f"{f.name}: {'; '.join(result.errors[:3])}")

        total_orig_words += ow
        total_new_words += nw
        total_ai_before += result.ai_isms_before
        total_ai_after += result.ai_isms_after

    sys.stdout.write("\n" + "─" * 80 + "\n")
    sys.stdout.write(_format_row("TOTAL", total_orig_words, total_new_words, total_ai_before, total_ai_after) + "\n")

    if failures:
        sys.stdout.write(f"\n{len(failures)} validation failure(s):\n")
        for f_msg in failures:
            sys.stdout.write(f"  - {f_msg}\n")
        sys.exit(2)


if __name__ == "__main__":  # pragma: no cover
    main()
