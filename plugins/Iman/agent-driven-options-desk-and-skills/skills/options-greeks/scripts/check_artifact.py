#!/usr/bin/env python3
"""Verify a Greek ladder artifact and print a one line verdict.

Run rather than read: the point of a script here is that its code never
enters the context window and only its output does.

    python3 check_artifact.py /path/to/greeks_SPY_2026-09-18.json
"""

import json
import math
import sys

REQUIRED = ("meta", "underlying", "spot", "units", "rows")
GREEKS = ("delta", "gamma", "vega", "theta", "rho", "lam", "vanna", "vomma",
          "charm", "veta", "speed", "zomma", "color", "ultima",
          "dual_delta", "dual_gamma")


def main(path):
    with open(path, encoding="utf-8") as handle:
        artifact = json.load(handle)

    problems = []
    for field in REQUIRED:
        if field not in artifact:
            problems.append("missing top level field: " + field)
    rows = artifact.get("rows", [])
    for index, row in enumerate(rows):
        missing = [g for g in GREEKS if g not in row]
        if missing:
            problems.append("row {} missing {}".format(index,
                                                       ", ".join(missing)))
            break
        bad = [g for g in GREEKS
               if not isinstance(row[g], (int, float))
               or not math.isfinite(row[g])]
        if bad:
            problems.append("row {} non finite {}".format(index,
                                                          ", ".join(bad)))
            break
        if not row.get("iv") or row["iv"] <= 0:
            problems.append("row {} graded without a volatility".format(index))
            break

    meta = artifact.get("meta", {})
    verdict = "FAIL" if problems else ("DEGRADED" if meta.get("degraded")
                                       else "OK")
    print("{} {} {} rows, {} skipped for no volatility{}".format(
        verdict, artifact.get("underlying", "?"), len(rows),
        artifact.get("skipped", {}).get("no_iv", 0),
        "" if not meta.get("degraded")
        else ", reason: " + str(meta.get("degraded_reason"))))
    for problem in problems:
        print("  " + problem)
    return 1 if problems else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: check_artifact.py <greeks artifact>")
        raise SystemExit(2)
    raise SystemExit(main(sys.argv[1]))
