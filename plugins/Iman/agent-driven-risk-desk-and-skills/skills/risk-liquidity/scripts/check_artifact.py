#!/usr/bin/env python3
"""Re-derive days to liquidate, the schedule, the spread cost and L-VaR in a liquidity result.

Run rather than read: only the output enters the conversation.

    python3 check_artifact.py /path/to/liquidity_result.json
"""

import json
import math
import sys


def close(a, b):
    return math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-9)


def check(artifact):
    problems = []
    rate, multiplier = artifact.get("participation_rate"), artifact.get("spread_multiplier")
    rows = artifact.get("by_asset")
    if not isinstance(rows, dict) or not rows or rate is None or multiplier is None:
        return ["missing by_asset, participation_rate or spread_multiplier"]
    for asset, row in rows.items():
        capacity = rate*row["average_daily_value"]
        cost = 0.5*row["gross_value"]*(row["mean_relative_spread"] + multiplier*row["spread_volatility"])
        if not close(row["daily_capacity"], capacity):
            problems.append("{}: daily capacity is not rate x average daily value".format(asset))
        if not close(row["days_to_liquidate"], row["gross_value"]/capacity):
            problems.append("{}: days to liquidate is not gross value / capacity".format(asset))
        if not close(row["cost_of_liquidity"], cost):
            problems.append("{}: cost of liquidity does not match 1/2 V (S + a sigma)".format(asset))
    if not close(artifact["cost_of_liquidity"], math.fsum(r["cost_of_liquidity"] for r in rows.values())):
        problems.append("total cost of liquidity is not the sum over assets")
    schedule = artifact.get("schedule") or []
    for entry in schedule:
        held = math.fsum(max(0.0, r["gross_value"] - r["daily_capacity"]*entry["day"]) for r in rows.values())
        if not close(entry["held_value"], held):
            problems.append("day {}: held value does not follow the daily capacities".format(entry["day"]))
            break
    if not schedule or schedule[-1]["held_value"] != 0 or not close(schedule[0]["held_value"], artifact["gross_value"]):
        problems.append("schedule must start at the gross value and end at zero")
    if artifact.get("liquidity_adjusted_var") is not None and not close(
            artifact["liquidity_adjusted_var"], artifact["var"] + artifact["cost_of_liquidity"]):
        problems.append("liquidity-adjusted VaR is not VaR + cost of liquidity")
    return problems


def main(path):
    with open(path, encoding="utf-8") as handle:
        artifact = json.load(handle)
    problems = check(artifact)
    verdict = "FAIL" if problems else ("DEGRADED" if artifact.get("degraded") else "OK")
    print("{} {} assets, longest {} days, cost of liquidity {}, L-VaR {}{}".format(
        verdict, len(artifact.get("by_asset") or {}), artifact.get("max_days_to_liquidate"),
        artifact.get("cost_of_liquidity"), artifact.get("liquidity_adjusted_var"),
        ", reason: " + str(artifact.get("degraded_reason")) if artifact.get("degraded") else ""))
    for problem in problems:
        print("  " + problem)
    return 1 if problems else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: check_artifact.py <liquidity result>")
        raise SystemExit(2)
    raise SystemExit(main(sys.argv[1]))
