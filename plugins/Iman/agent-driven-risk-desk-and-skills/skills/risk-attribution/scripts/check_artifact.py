#!/usr/bin/env python3
"""Verify a Risk Desk attribution result and print a one line verdict.

Run rather than read: only the output enters the conversation. It checks that
the parts of each result add up to the stated total and that every number is
finite. It recomputes nothing from market data.

    python3 check_artifact.py /path/to/result.json
"""

import json
import math
import sys

REL = 1e-9


def close(a, b):
    return math.isclose(a, b, rel_tol=REL, abs_tol=REL * max(1.0, abs(b)))


def numbers(value):
    if isinstance(value, dict):
        return [n for v in value.values() for n in numbers(v)]
    if isinstance(value, list):
        return [n for v in value for n in numbers(v)]
    return [value] if isinstance(value, float) else []


def problems_for(result):
    method = result.get("method", "")
    problems = ["non finite number"] if not all(map(math.isfinite, numbers(result))) else []
    if method.startswith("parametric"):
        rows = result["positions"]
        for total, part in (("var", "component_var"), ("expected_shortfall", "component_es")):
            if not close(math.fsum(r[part] for r in rows), result[total]):
                problems.append("{} components do not sum to {}".format(part, total))
    elif method.startswith("historical"):
        if not close(math.fsum(r["component_es"] for r in result["positions"]),
                     result["expected_shortfall"]):
            problems.append("component_es does not sum to expected_shortfall")
    elif method.startswith("OLS"):
        v = result["variance"]
        if not close(v["systematic"] + v["idiosyncratic"], v["total"]):
            problems.append("systematic plus idiosyncratic does not equal total variance")
    elif "estimator" in result:
        c = result["covariance"]
        if any(not close(c[i][j], c[j][i]) for i in range(len(c)) for j in range(i)):
            problems.append("covariance is not symmetric")
        if any(c[i][i] < 0 for i in range(len(c))):
            problems.append("negative variance on the diagonal")
    else:
        problems.append("not an attribution result: method " + repr(method))
    return problems


def main(path):
    with open(path, encoding="utf-8") as handle:
        result = json.load(handle)
    problems = problems_for(result)
    verdict = "FAIL" if problems else ("DEGRADED" if result.get("degraded") else "OK")
    print("{} {} {} {}{}".format(verdict, result.get("method"), result.get("currency"),
                                 result.get("as_of"),
                                 ", reason: " + str(result.get("degraded_reason"))
                                 if result.get("degraded") else ""))
    for problem in problems:
        print("  " + problem)
    return 1 if problems else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: check_artifact.py <attribution result json>")
        raise SystemExit(2)
    raise SystemExit(main(sys.argv[1]))
