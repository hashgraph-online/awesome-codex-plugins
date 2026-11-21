#!/usr/bin/env python3
"""Check a saved risk_backtest result and print a one line verdict.

Run rather than read: only the verdict enters the conversation.

    python3 check_artifact.py result.json
"""
import json
import sys

ENVELOPE = ("currency", "as_of", "source", "data_mode", "input_sha256", "degraded", "observations", "exceptions")
TESTS = ("kupiec_pof", "christoffersen_independence", "christoffersen_conditional_coverage")


def main(path):
    with open(path, encoding="utf-8") as handle:
        result = json.load(handle)
    problems = ["missing field: " + f for f in ENVELOPE if f not in result]
    n, x = result.get("observations", 0), result.get("exceptions", -1)
    if not 0 <= x <= n:
        problems.append("exceptions outside 0..observations")
    for name in TESTS:
        test = result.get(name) or {}
        if not (test.get("lr", -1) >= 0 and 0 <= test.get("p_value", -1) <= 1):
            problems.append(name + ": statistic or p-value out of range")
    zone = result.get("basel_traffic_light")
    if zone is not None:
        cumulative = zone.get("cumulative_probability", -1)
        expected = "red" if cumulative >= 0.9999 else "amber" if cumulative >= 0.95 else "green"
        if zone.get("zone") != expected:
            problems.append("Basel zone does not match its cumulative probability")
    elif not result.get("basel_traffic_light_unavailable"):
        problems.append("Basel zone absent without a reason")
    es = result.get("es_backtest")
    if es is not None and not 0 < es.get("p_value", -1) <= 1:
        problems.append("ES backtest p-value out of range")
    verdict = "FAIL" if problems else ("DEGRADED" if result.get("degraded") else "OK")
    print("{} {} exceptions in {} observations, Basel zone {}, ES p-value {}".format(
        verdict, x, n, zone.get("zone") if zone else "n/a", es.get("p_value") if es else "n/a"))
    for problem in problems:
        print("  " + problem)
    return 1 if problems else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: check_artifact.py <risk_backtest result JSON>")
        raise SystemExit(2)
    raise SystemExit(main(sys.argv[1]))
