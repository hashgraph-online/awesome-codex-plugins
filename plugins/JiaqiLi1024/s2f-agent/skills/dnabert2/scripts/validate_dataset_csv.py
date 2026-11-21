#!/usr/bin/env python3
"""Validate DNABERT2 train/dev/test CSV files for fine-tuning."""

from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate DNABERT2 dataset CSV files. Checks split files, header shape, "
            "label parsing, row consistency, and sequence alphabet constraints."
        )
    )
    parser.add_argument(
        "--data-dir",
        default=".",
        help="Directory containing train.csv, dev.csv, and test.csv. Default: current directory.",
    )
    parser.add_argument(
        "--allow-iupac",
        action="store_true",
        help="Allow extended IUPAC nucleotide symbols beyond A/C/G/T/N.",
    )
    return parser.parse_args()


def percentile(values: list[int], q: float) -> int:
    if not values:
        return 0
    idx = int(math.ceil((q / 100.0) * len(values))) - 1
    idx = max(0, min(idx, len(values) - 1))
    return values[idx]


def check_sequence_alphabet(seq: str, allow_iupac: bool) -> str | None:
    base = set("ACGTN")
    if allow_iupac:
        base = set("ACGTNRYSWKMBVDH")

    bad = sorted({c for c in seq.upper() if c not in base})
    if bad:
        return "".join(bad)
    return None


def validate_file(path: Path, allow_iupac: bool) -> tuple[list[str], int]:
    issues: list[str] = []
    lengths: list[int] = []

    with path.open(newline="") as f:
        rows = list(csv.reader(f))

    if not rows:
        return [f"{path.name}: empty file"], 0

    header = [c.strip().lower() for c in rows[0]]
    ncols = len(header)

    if ncols not in (2, 3):
        issues.append(f"{path.name}: header must have 2 or 3 columns, got {ncols}")
        return issues, 0

    if ncols == 2 and header != ["sequence", "label"]:
        issues.append(
            f"{path.name}: expected header sequence,label for 2-column mode, got {','.join(header)}"
        )
    if ncols == 3 and header[-1] != "label":
        issues.append(f"{path.name}: 3-column header must end with label, got {','.join(header)}")

    for i, row in enumerate(rows[1:], start=2):
        if len(row) != ncols:
            issues.append(f"{path.name}:{i}: expected {ncols} columns, got {len(row)}")
            continue

        seq_cols = row[:-1]
        label_raw = row[-1].strip()

        if not label_raw:
            issues.append(f"{path.name}:{i}: empty label")
        else:
            try:
                int(label_raw)
            except ValueError:
                issues.append(f"{path.name}:{i}: label is not int: {label_raw}")

        for j, seq in enumerate(seq_cols, start=1):
            seq = seq.strip()
            if not seq:
                issues.append(f"{path.name}:{i}: sequence column {j} is empty")
                continue
            bad = check_sequence_alphabet(seq, allow_iupac=allow_iupac)
            if bad is not None:
                issues.append(
                    f"{path.name}:{i}: sequence column {j} has invalid chars: {bad}"
                )
            lengths.append(len(seq))

    if lengths:
        lengths_sorted = sorted(lengths)
        p95 = percentile(lengths_sorted, 95)
        print(
            f"{path.name}: rows={len(rows)-1} cols={ncols} "
            f"min_len={lengths_sorted[0]} median_len={lengths_sorted[len(lengths_sorted)//2]} "
            f"p95_len={p95} max_len={lengths_sorted[-1]}"
        )
    else:
        print(f"{path.name}: rows={len(rows)-1} cols={ncols} no_valid_sequences")

    return issues, len(rows) - 1


def main() -> int:
    args = parse_args()
    data_dir = Path(args.data_dir)

    required = ["train.csv", "dev.csv", "test.csv"]
    missing = [name for name in required if not (data_dir / name).exists()]
    if missing:
        for name in missing:
            print(f"missing: {data_dir / name}", file=sys.stderr)
        return 1

    all_issues: list[str] = []
    total_rows = 0

    for name in required:
        issues, rows = validate_file(data_dir / name, allow_iupac=args.allow_iupac)
        all_issues.extend(issues)
        total_rows += rows

    if all_issues:
        print("validation=failed", file=sys.stderr)
        for issue in all_issues:
            print(f"issue: {issue}", file=sys.stderr)
        return 1

    print("validation=passed")
    print(f"total_rows={total_rows}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
