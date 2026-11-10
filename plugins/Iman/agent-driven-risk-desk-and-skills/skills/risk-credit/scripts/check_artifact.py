#!/usr/bin/env python3
"""Verify a saved risk_credit_asrf or risk_credit_copula result; print a one line verdict.

Run rather than read: only the output enters the conversation.

    python3 check_artifact.py /path/to/result.json
"""

import json
import math
import sys

TOLERANCE = 1e-9


def close(a, b):
    return abs(a - b) <= TOLERANCE * max(1.0, abs(a), abs(b))


def main(path):
    with open(path, encoding="utf-8") as handle:
        result = json.load(handle)
    method = result.get("method", "")
    if "credit VaR" not in method:
        print("FAIL not a risk_credit_asrf or risk_credit_copula result")
        return 1
    problems = []
    keys = ["credit_var", "expected_loss", "unexpected_loss", "total_exposure"]
    copula = "Monte Carlo" in method
    if copula:
        keys += ["expected_shortfall", "loss_standard_deviation"]
    missing = [k for k in keys if not isinstance(result.get(k), (int, float))
               or not math.isfinite(result[k])]
    if missing:
        problems.append("missing or non finite " + ", ".join(missing))
    else:
        if not close(result["unexpected_loss"], result["credit_var"] - result["expected_loss"]):
            problems.append("unexpected loss is not credit VaR minus expected loss")
        if not 0 <= result["expected_loss"] <= result["total_exposure"]:
            problems.append("expected loss outside zero to total exposure")
        if result["credit_var"] > result["total_exposure"] * (1 + TOLERANCE):
            problems.append("credit VaR above total exposure")
        if copula and result["expected_shortfall"] < result["credit_var"] * (1 - TOLERANCE):
            problems.append("expected shortfall below VaR")
        if not copula and not close(math.fsum(result["contributions"].values()),
                                    result["credit_var"]):
            problems.append("contributions do not add up to credit VaR")
    verdict = "FAIL" if problems else ("DEGRADED" if result.get("degraded") else "OK")
    print("{} {} credit VaR {} {} at {} over {} days{}{}".format(
        verdict, "copula" if copula else "ASRF", result.get("credit_var"),
        result.get("currency", "?"), result.get("confidence"), result.get("horizon_days"),
        ", seed {} scenarios {}".format(result.get("seed"), result.get("scenarios")) if copula else "",
        ", reason: " + str(result.get("degraded_reason")) if result.get("degraded") else ""))
    for problem in problems:
        print("  " + problem)
    return 1 if problems else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: check_artifact.py <result json>")
        raise SystemExit(2)
    raise SystemExit(main(sys.argv[1]))
