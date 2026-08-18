#!/usr/bin/env python3
"""Calculate expected value for simple weighted outcomes.

Examples:
  expected_value.py --outcome 0:0.5 --outcome 10:0.5
  expected_value.py --json outcomes.json

JSON format:
[
  {"value": 0, "probability": 0.5},
  {"value": 10, "probability": 0.5}
]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def parse_outcome(raw: str) -> tuple[float, float]:
    try:
        value_raw, probability_raw = raw.split(":", 1)
        value = float(value_raw)
        probability = float(probability_raw)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"Invalid outcome '{raw}'. Use VALUE:PROBABILITY, for example 10:0.25."
        ) from exc
    if not 0.0 <= probability <= 1.0:
        raise argparse.ArgumentTypeError(
            f"Probability {probability} in '{raw}' must be between 0 and 1."
        )
    return value, probability


def load_json(path: Path) -> list[tuple[float, float]]:
    try:
        data = json.loads(path.read_text())
    except OSError as exc:
        raise SystemExit(f"error: could not read JSON file {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"error: invalid JSON in {path}: {exc}") from exc

    if not isinstance(data, list):
        raise SystemExit(
            f"error: JSON file must contain a list of outcomes, got {type(data).__name__}."
        )

    outcomes: list[tuple[float, float]] = []
    for index, item in enumerate(data):
        if not isinstance(item, dict):
            raise SystemExit(f"error: item {index} in JSON file must be an object.")
        if "value" not in item or "probability" not in item:
            raise SystemExit(
                f"error: item {index} in JSON file is missing 'value' or 'probability'."
            )
        try:
            value = float(item["value"])
            probability = float(item["probability"])
        except (TypeError, ValueError) as exc:
            raise SystemExit(f"error: item {index} has a non-numeric value or probability.") from exc
        if not 0.0 <= probability <= 1.0:
            raise SystemExit(
                f"error: probability {probability} for item {index} must be between 0 and 1."
            )
        outcomes.append((value, probability))
    return outcomes


def main() -> int:
    parser = argparse.ArgumentParser(description="Calculate expected value for weighted outcomes.")
    parser.add_argument("--outcome", action="append", type=parse_outcome, default=[], help="VALUE:PROBABILITY")
    parser.add_argument("--json", type=Path, help="Path to a JSON outcomes file")
    args = parser.parse_args()

    outcomes = list(args.outcome)
    if args.json:
        outcomes.extend(load_json(args.json))

    if not outcomes:
        parser.error("Provide at least one --outcome or --json file.")

    probability_sum = sum(probability for _, probability in outcomes)
    expected_value = sum(value * probability for value, probability in outcomes)

    print(f"outcomes: {len(outcomes)}")
    print(f"probability_sum: {probability_sum:.6g}")
    print(f"expected_value: {expected_value:.6g}")

    if abs(probability_sum - 1.0) > 0.000001:
        print("warning: probabilities do not sum to 1.0", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
