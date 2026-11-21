#!/usr/bin/env python3
"""Check a Risk Desk FRTB result for internal consistency and print a one line verdict.

Run rather than read: only the output enters the conversation.

    python3 check_artifact.py /path/to/frtb_result.json

It recomputes every figure that can be derived from other figures in the same
result (the IMCC weighting, the capital identities, the PLA zone, the
backtesting verdict, the SBM scenario maximum). It cannot re-check a figure
against inputs the result does not carry. Exit 0 OK or DEGRADED, 1 FAIL, 2 usage.
"""

import json
import math
import sys

TOL = 1e-9
TABLE = {5: 1.70, 6: 1.76, 7: 1.83, 8: 1.88, 9: 1.92}  # MAR32.9 Table 1


def close(a, b):
    return abs(a - b) <= TOL * max(1.0, abs(a), abs(b))


def table(exceptions):
    if exceptions <= 4:
        return "green", 1.50
    return ("amber", TABLE[exceptions]) if exceptions <= 9 else ("red", 2.00)


def check_imcc(r, bad):
    for name, part in [("portfolio", r["portfolio"])] + sorted(r["risk_classes"].items()):
        floored = max(1.0, part["es_full_current"] / part["es_reduced_current"])
        if not close(part["imcc"], part["es_reduced_stressed"] * floored):
            bad.append(name + ": imcc is not ES_R,S times the floored ratio (MAR33.6)")
    constrained = math.fsum(c["imcc"] for c in r["risk_classes"].values())
    if not close(r["imcc"], r["rho"] * r["portfolio"]["imcc"] + (1 - r["rho"]) * constrained):
        bad.append("imcc is not the MAR33.15 weighting")


def check_capital(r, bad):
    if (r["backtesting_zone"], r["backtesting_multiplier"]) not in [table(n) for n in range(11)]:
        bad.append("backtesting zone and multiplier are not a MAR32.9 row")
    if r["multiplier"] < r["backtesting_multiplier"]:
        bad.append("multiplier is below the table value")
    if not close(r["ima_green_amber"], r["c_a"] + r["drc"]):
        bad.append("IMA_G,A is not C_A + DRC (MAR33.43)")
    if not 0 <= r["k"] <= 0.5 or r["capital_surcharge"] < 0:
        bad.append("k or the surcharge is out of range (MAR33.45)")
    if not close(r["rwa"], 12.5 * r["aggregate_capital"]):
        bad.append("RWA is not 12.5 times the capital (MAR33.46)")


def check_pla(r, bad):
    rho, count = r["spearman"], r["ks_count"]
    zone = ("green" if rho > 0.80 and count < 22.5 else
            "red" if rho < 0.70 or count > 30 else "amber")
    if r["zone"] != zone:
        bad.append("zone {} does not follow MAR32.42 for these metrics ({})".format(r["zone"], zone))
    if not close(r["ks"], count / 250):
        bad.append("ks is not 0.004 times its count")


def check_backtest(r, bad):
    for key in ("exceptions_99", "exceptions_975"):
        e = r.get(key)
        if e is not None and e["overall"] != max(e["apl"], e["hpl"]):
            bad.append(key + ": overall is not the greater of APL and HPL")
    if r["level"] == "desk":
        passes = r["exceptions_99"]["overall"] <= 12 and r["exceptions_975"]["overall"] <= 30
        if r["passes"] != passes:
            bad.append("passes does not follow MAR32.19 for these counts")
    elif (r["zone"], r["backtesting_multiplier"]) != table(r["exceptions_99"]["overall"]):
        bad.append("bank zone does not follow MAR32.9 for this count")


def check_sbm(r, bad):
    scenarios = r["scenarios"]
    for name, row in scenarios.items():
        if not close(row["total"], row["delta"] + row["vega"]):
            bad.append(name + ": total is not delta plus vega")
    binding = max(scenarios, key=lambda n: scenarios[n]["total"])
    if not close(r["capital"], scenarios[binding]["total"]):
        bad.append("capital is not the largest scenario total (MAR21.7)")


CHECKS = [("IMCC", check_imcc), ("capital aggregation", check_capital), ("attribution test", check_pla),
          ("backtesting", check_backtest), ("sensitivities-based", check_sbm)]


def numbers(value):
    if isinstance(value, bool):
        return
    if isinstance(value, (int, float)):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from numbers(item)
    elif isinstance(value, list):
        for item in value:
            yield from numbers(item)


def main(path):
    with open(path, encoding="utf-8") as handle:
        r = json.load(handle)
    bad = [f for f in ("method", "currency", "as_of", "source", "data_mode", "degraded") if f not in r]
    bad = ["missing field: " + f for f in bad]
    if not bad:
        if not all(math.isfinite(x) for x in numbers(r)):
            bad.append("non-finite number")
        check = next((fn for key, fn in CHECKS if key in r["method"]), None)
        if check is None:
            bad.append("not an FRTB result: " + r["method"])
        else:
            try:
                check(r, bad)
            except (KeyError, TypeError, ZeroDivisionError) as error:
                bad.append("malformed result: {!r}".format(error))
    verdict = "FAIL" if bad else ("DEGRADED" if r.get("degraded") else "OK")
    print("{} {} {} as of {}{}".format(verdict, r.get("method", "?"), r.get("currency", "?"), r.get("as_of", "?"),
                                       ", reason: " + str(r.get("degraded_reason")) if r.get("degraded") else ""))
    for problem in bad:
        print("  " + problem)
    return 1 if bad else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: check_artifact.py <frtb result json>")
        raise SystemExit(2)
    raise SystemExit(main(sys.argv[1]))
