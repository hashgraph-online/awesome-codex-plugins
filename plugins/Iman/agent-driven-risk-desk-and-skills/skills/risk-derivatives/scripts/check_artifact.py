#!/usr/bin/env python3
"""Verify a saved risk-derivatives result and print a one line verdict.

    python3 check_artifact.py RESULT.json

Checks the envelope, that every number is finite, and the identities each
result must satisfy: totals add the underlyings, grid errors equal
approximation minus full revaluation, and the tail used the P&L vector.
"""
import json
import math
import sys

ENVELOPE = ("currency", "as_of", "source", "data_mode", "input_sha256", "degraded", "assumptions")
CASH = ("cash_delta", "cash_gamma_1pct", "vega_per_vol_point", "theta_per_day", "rho_per_rate_point")


def close(a, b):
    return math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-6)


def numbers(value):
    if isinstance(value, bool):
        return
    if isinstance(value, (int, float)):
        yield value
    elif isinstance(value, dict):
        for v in value.values():
            yield from numbers(v)
    elif isinstance(value, list):
        for v in value:
            yield from numbers(v)


def problems(result):
    found = ["missing " + k for k in ENVELOPE if k not in result]
    if not all(math.isfinite(v) for v in numbers(result)):
        found.append("non-finite number")
    if "by_underlying" in result:
        for key in CASH:
            if not close(result["total"][key], math.fsum(r[key] for r in result["by_underlying"].values())):
                found.append("total does not add underlyings: " + key)
    for i, cell in enumerate(result.get("cells", [])):
        if not (close(cell["delta_gamma_error"], cell["delta_gamma_pnl"] - cell["full_pnl"])
                and close(cell["delta_gamma_vega_error"], cell["delta_gamma_vega_pnl"] - cell["full_pnl"])):
            found.append(f"cell {i} error is not approximation minus full")
            break
    if "pnl" in result:
        if result.get("time_mode") not in ("fixed", "decay"):
            found.append("time_mode not reported")
        if result["tail"]["observations"] != len(result["pnl"]):
            found.append("tail observations differ from the P&L vector")
    return found


def main(path):
    with open(path, encoding="utf-8") as handle:
        result = json.load(handle)
    found = problems(result)
    verdict = "FAIL" if found else ("DEGRADED" if result.get("degraded") else "OK")
    kind = "greeks" if "by_underlying" in result else "grid" if "cells" in result else "historical" if "pnl" in result else "unknown"
    print(f"{verdict} {kind} {result.get('currency', '?')} as of {result.get('as_of', '?')}"
          + (f", reason: {result.get('degraded_reason')}" if result.get("degraded") else ""))
    for problem in found:
        print("  " + problem)
    return 1 if found else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: check_artifact.py RESULT.json")
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
