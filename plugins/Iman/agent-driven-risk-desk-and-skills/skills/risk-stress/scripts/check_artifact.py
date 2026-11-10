#!/usr/bin/env python3
"""Verify a Risk Desk stress, replay, reverse stress or scaling result and print a one line verdict.

Run rather than read: only the output enters the conversation.

    python3 check_artifact.py /path/to/result.json

Exit 0 when every check passes (verdict OK or DEGRADED), 1 on FAIL, 2 on usage error.
Standard library only, so it runs without the Risk Desk environment.
"""
import json
import math
import sys

ENVELOPE = ("schema_version", "method", "currency", "as_of", "source", "data_mode", "input_sha256",
            "degraded", "degraded_reason", "assumptions", "scenarios")


def close(a, b, rel=1e-6, scale=1.0):
    return math.isclose(a, b, rel_tol=rel, abs_tol=rel * scale)


def finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def problems(result):
    found = [f"missing field: {field}" for field in ENVELOPE if field not in result]
    if found:
        return found
    if result["degraded"] != bool(result["degraded_reason"]):
        found.append("degraded flag and degraded_reason disagree")
    rows = result["scenarios"]
    if not rows:
        found.append("no scenarios")
    bases = []
    for row in rows:
        values = [row.get("pnl"), row.get("loss"), row.get("stressed_nav"), *row.get("contributions", {}).values()]
        if not all(finite(v) for v in values):
            found.append(f"scenario {row.get('name')}: missing or non-finite number")
            continue
        size = max([abs(v) for v in values] + [1.0])
        if not close(row["loss"], -row["pnl"], scale=size):
            found.append(f"scenario {row['name']}: loss is not minus P&L")
        if not close(math.fsum(row["contributions"].values()), row["pnl"], scale=size):
            found.append(f"scenario {row['name']}: contributions do not sum to P&L")
        bases.append((row["stressed_nav"] - row["pnl"], size))
    if bases and not all(close(b, bases[0][0], scale=s) for b, s in bases):
        found.append("stressed NAV minus P&L differs between scenarios")
    shocks = result.get("shocks", {})
    if any(not finite(s) or s < -1 for s in shocks.values()):
        found.append("a shock is non-finite or below -100%")
    if "target_loss" in result and rows and finite(rows[-1].get("loss")):
        if not close(rows[-1]["loss"], result["target_loss"], scale=result["target_loss"]):
            found.append("final scenario loss does not equal target_loss")
    if "mahalanobis_distance" in result:
        bounded, unbounded = result["mahalanobis_distance"], result["unbounded_mahalanobis_distance"]
        if bounded < unbounded * (1 - 1e-9):
            found.append("distance is below the unbounded minimum")
        normal = 0.5 * math.erfc(unbounded / math.sqrt(2))
        if not close(result["loss_exceedance_probability_if_normal"], normal, rel=1e-9):
            found.append("normal probability does not equal Phi(-L / sd)")
        if not any(text.startswith("ASSUMPTION:") for text in result["assumptions"]):
            found.append("normal probability is not labelled as an assumption")
    if "multiple" in result:
        for asset, base in result["base_shocks"].items():
            if not close(shocks.get(asset, math.nan), result["multiple"] * base, rel=1e-9):
                found.append(f"scaled shock for {asset} is not multiple times base shock")
    for asset, row in result.get("series", {}).items():
        if not close(row["to_level"] / row["from_level"] - 1, row["shock"], rel=1e-12):
            found.append(f"series {asset}: shock does not match its levels")
        if not close(shocks.get(asset, math.nan), row["shock"], rel=1e-12):
            found.append(f"series {asset}: shock differs from the scenario shock")
        if row["from_date"] > row["to_date"]:
            found.append(f"series {asset}: dates out of order")
        window = result.get("window", {})
        if window.get("measure") == "end_over_start" and (row["from_date"], row["to_date"]) != (
                window.get("start"), window.get("end")):
            found.append(f"series {asset}: end-over-start return does not span the window")
    return found


def main(path):
    with open(path, encoding="utf-8") as handle:
        result = json.load(handle)
    found = problems(result)
    verdict = "FAIL" if found else ("DEGRADED" if result.get("degraded") else "OK")
    print("{} {}, {} scenario(s){}".format(verdict, result.get("method", "?"), len(result.get("scenarios", [])),
                                          ", reason: " + str(result["degraded_reason"]) if result.get("degraded")
                                          else ""))
    for problem in found:
        print("  " + problem)
    return 1 if found else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: check_artifact.py <result json>")
        raise SystemExit(2)
    raise SystemExit(main(sys.argv[1]))
