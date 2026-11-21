#!/usr/bin/env python3
"""Verify a saved risk_saccr or risk_exposure_profile result; print a one line verdict.

Run rather than read: only the output enters the conversation.

    python3 check_artifact.py /path/to/result.json
"""

import json
import math
import sys

TOLERANCE = 1e-9


def close(a, b):
    return abs(a - b) <= TOLERANCE * max(1.0, abs(a), abs(b))


def finite(value):
    return isinstance(value, (int, float)) and math.isfinite(value)


def check_saccr(result, problems):
    for key in ("ead", "replacement_cost", "pfe", "multiplier", "addon_aggregate"):
        if not finite(result.get(key)):
            problems.append("non finite or missing " + key)
            return "SA-CCR"
    if result["replacement_cost"] < 0 or result["addon_aggregate"] < 0:
        problems.append("negative replacement cost or add-on")
    if not 0.05 - TOLERANCE <= result["multiplier"] <= 1 + TOLERANCE:
        problems.append("multiplier outside [0.05, 1]")
    if not close(math.fsum(result["addon_by_asset_class"].values()), result["addon_aggregate"]):
        problems.append("asset class add-ons do not sum to the aggregate")
    if not close(result["pfe"], result["multiplier"] * result["addon_aggregate"]):
        problems.append("PFE is not multiplier times aggregate add-on")
    ead = result["alpha"] * (result["replacement_cost"] + result["pfe"])
    if result.get("margined"):
        ead = min(ead, result["unmargined_ead"])
    if not close(result["ead"], ead):
        problems.append("EAD is not alpha times (RC + PFE), capped when margined")
    return "SA-CCR EAD {:.2f} {}".format(result["ead"], result.get("currency", "?"))


def check_profile(result, problems):
    rows = result.get("effective_ee", [])
    values = [r.get("effective_ee") for r in rows]
    if not values or not all(finite(v) for v in values):
        problems.append("missing or non finite effective EE")
        return "profile"
    if any(b < a for a, b in zip(values, values[1:])):
        problems.append("effective EE decreases")
    if any(r["effective_ee"] < r["BaselEE"] for r in rows):
        problems.append("effective EE below EE")
    for key in ("epe", "effective_epe", "peak_pfe"):
        if not finite(result.get(key)) or result[key] < 0:
            problems.append("non finite or negative " + key)
    if not problems and result["effective_epe"] < result["epe"] - TOLERANCE * abs(result["epe"]):
        problems.append("effective EPE below EPE")
    return "profile Effective EPE {} over {} years".format(
        result.get("effective_epe"), result.get("averaging_horizon_years"))


def main(path):
    with open(path, encoding="utf-8") as handle:
        result = json.load(handle)
    problems = []
    method = result.get("method", "")
    if method.startswith("SA-CCR"):
        label = check_saccr(result, problems)
    elif method.startswith("Basel exposure profile"):
        label = check_profile(result, problems)
    else:
        print("FAIL not a risk_saccr or risk_exposure_profile result")
        return 1
    verdict = "FAIL" if problems else ("DEGRADED" if result.get("degraded") else "OK")
    reason = ", reason: " + str(result.get("degraded_reason")) if result.get("degraded") else ""
    print("{} {}{}".format(verdict, label, reason))
    for problem in problems:
        print("  " + problem)
    return 1 if problems else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: check_artifact.py <result json>")
        raise SystemExit(2)
    raise SystemExit(main(sys.argv[1]))
