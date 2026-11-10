#!/usr/bin/env python3
"""Check a saved risk_tail or risk_tail_models result and print a one line verdict.

Run rather than read: only the verdict enters the conversation.

    python3 check_artifact.py result.json
"""
import json
import math
import sys

ENVELOPE = ("currency", "as_of", "source", "data_mode", "input_sha256", "degraded", "confidence", "horizon_days")


def main(path):
    with open(path, encoding="utf-8") as handle:
        result = json.load(handle)
    problems = ["missing field: " + f for f in ENVELOPE if f not in result]
    if result.get("degraded") and not result.get("degraded_reason"):
        problems.append("degraded without a reason")
    methods = result.get("methods") or {"historical": result}
    for name, row in methods.items():
        var, es = row.get("var"), row.get("expected_shortfall")
        if not isinstance(var, (int, float)) or not math.isfinite(var):
            problems.append(name + ": VaR missing or non-finite")
        elif es is not None and (not isinstance(es, (int, float)) or not math.isfinite(es)):
            problems.append(name + ": ES non-finite")
        elif es is not None and es < var - 1e-9*max(1.0, abs(var)):
            problems.append(name + ": ES below VaR")
    for name in result.get("unavailable", {}):
        if name in methods:
            problems.append(name + ": both reported and unavailable")
    verdict = "FAIL" if problems else ("DEGRADED" if result.get("degraded") else "OK")
    print("{} {} at {} over {} day(s), {} method(s){}".format(
        verdict, result.get("currency", "?"), result.get("confidence"),
        result.get("horizon_days"), len(methods),
        ", reason: " + str(result.get("degraded_reason")) if result.get("degraded") else ""))
    for problem in problems:
        print("  " + problem)
    return 1 if problems else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: check_artifact.py <risk_tail or risk_tail_models result JSON>")
        raise SystemExit(2)
    raise SystemExit(main(sys.argv[1]))
