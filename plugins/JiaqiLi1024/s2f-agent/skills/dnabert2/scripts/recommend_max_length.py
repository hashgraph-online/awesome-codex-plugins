#!/usr/bin/env python3
"""Recommend DNABERT2 model_max_length from sequence lengths."""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Recommend DNABERT2 model_max_length using README guidance "
            "(default ratio 0.25 of sequence length)."
        )
    )
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument(
        "--sequence-length-bp",
        type=int,
        help="Single raw sequence length (bp).",
    )
    src.add_argument(
        "--csv",
        help="CSV file to estimate from. Uses all sequence columns except final label column.",
    )
    parser.add_argument(
        "--ratio",
        type=float,
        default=0.25,
        help="Compression ratio from bp length to token max length. Default: 0.25.",
    )
    parser.add_argument(
        "--round-to",
        type=int,
        default=1,
        help="Round recommendation up to a multiple of this value. Default: 1.",
    )
    return parser.parse_args()


def round_up(x: int, to: int) -> int:
    if to <= 1:
        return x
    return ((x + to - 1) // to) * to


def percentile(values: list[int], q: float) -> int:
    if not values:
        return 0
    values = sorted(values)
    idx = int(math.ceil((q / 100.0) * len(values))) - 1
    idx = max(0, min(idx, len(values) - 1))
    return values[idx]


def recommend(length_bp: int, ratio: float, round_to: int) -> int:
    if length_bp <= 0:
        raise ValueError("sequence length must be positive")
    if ratio <= 0:
        raise ValueError("ratio must be positive")
    base = max(1, math.ceil(length_bp * ratio))
    return round_up(base, round_to)


def load_lengths_from_csv(path: Path) -> list[int]:
    lengths: list[int] = []
    with path.open(newline="") as f:
        rows = list(csv.reader(f))
    if not rows:
        return lengths
    ncols = len(rows[0])
    if ncols < 2:
        return lengths

    for row in rows[1:]:
        if len(row) != ncols:
            continue
        seq_cols = row[:-1]
        for seq in seq_cols:
            seq = seq.strip()
            if seq:
                lengths.append(len(seq))
    return lengths


def main() -> int:
    args = parse_args()

    if args.round_to <= 0:
        raise SystemExit("--round-to must be positive")

    if args.sequence_length_bp is not None:
        rec = recommend(args.sequence_length_bp, args.ratio, args.round_to)
        print(f"input_bp={args.sequence_length_bp}")
        print(f"ratio={args.ratio}")
        print(f"round_to={args.round_to}")
        print(f"recommended_model_max_length={rec}")
        return 0

    csv_path = Path(args.csv)
    lengths = load_lengths_from_csv(csv_path)
    if not lengths:
        raise SystemExit(f"no valid sequence rows found in {csv_path}")

    lengths_sorted = sorted(lengths)
    min_len = lengths_sorted[0]
    median_len = lengths_sorted[len(lengths_sorted) // 2]
    p95_len = percentile(lengths_sorted, 95)
    max_len = lengths_sorted[-1]

    rec_p95 = recommend(p95_len, args.ratio, args.round_to)
    rec_max = recommend(max_len, args.ratio, args.round_to)

    print(f"csv={csv_path}")
    print(f"rows_with_sequences={len(lengths_sorted)}")
    print(f"min_bp={min_len}")
    print(f"median_bp={median_len}")
    print(f"p95_bp={p95_len}")
    print(f"max_bp={max_len}")
    print(f"ratio={args.ratio}")
    print(f"round_to={args.round_to}")
    print(f"recommended_from_p95={rec_p95}")
    print(f"recommended_from_max={rec_max}")
    print("guidance=use_recommended_from_max_for_safe_truncation_control")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
