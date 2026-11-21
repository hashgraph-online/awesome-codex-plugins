#!/usr/bin/env python3
"""Re-derive every limit status in a limit check or what-if result and print a one line verdict.

Run rather than read: only the output enters the conversation.

    python3 check_artifact.py /path/to/limits_result.json
"""

import json
import math
import sys

SEVERITY = ("within", "not_evaluated", "warning", "breach")


def exceeds(direction, value, threshold):
    return value > threshold if direction == "max" else value < threshold


def check(artifact):
    """Return a list of problems. A what-if result is checked through its limits_after block."""
    if "limits_after" in artifact:
        artifact = artifact["limits_after"]
        if artifact is None:
            return ["what-if result carries no limit check"]
    problems = []
    rows = artifact.get("limits")
    if not isinstance(rows, list) or not rows:
        return ["no limits rows"]
    for row in rows:
        name, value = row.get("name"), row.get("value")
        if row.get("status") == "not_evaluated":
            if value is not None or not row.get("reason"):
                problems.append("{}: not_evaluated needs a reason and no value".format(name))
            continue
        if not isinstance(value, (int, float)) or not math.isfinite(value):
            problems.append("{}: evaluated without a finite value".format(name))
            continue
        limit, warning, direction = row["limit"], row["warning"], row["direction"]
        expected = ("breach" if exceeds(direction, value, limit) else
                    "warning" if warning is not None and not exceeds(direction, warning, value)
                    else "within")
        if row.get("status") != expected:
            problems.append("{}: status {} but value {} gives {}".format(
                name, row.get("status"), value, expected))
        utilisation = value/limit if limit else None
        if utilisation is not None and not math.isfinite(utilisation):
            utilisation = None
            if not row.get("utilisation_unavailable_reason") or not artifact.get("degraded"):
                problems.append("{}: overflowing utilisation needs a reason and degraded status".format(name))
        if (utilisation is None) != (row.get("utilisation") is None) or (
                utilisation is not None and not math.isclose(utilisation, row["utilisation"], rel_tol=1e-12)):
            problems.append("{}: utilisation is not value / limit".format(name))
    worst = max((row.get("status") for row in rows), key=lambda s: SEVERITY.index(s) if s in SEVERITY else 99)
    if artifact.get("overall_status") != worst:
        problems.append("overall_status {} but the worst row is {}".format(artifact.get("overall_status"), worst))
    if any(row.get("status") == "not_evaluated" for row in rows) and not artifact.get("degraded"):
        problems.append("a limit was not evaluated but the result is not degraded")
    return problems


def main(path):
    with open(path, encoding="utf-8") as handle:
        artifact = json.load(handle)
    problems = check(artifact)
    block = artifact.get("limits_after") or artifact
    verdict = "FAIL" if problems else ("DEGRADED" if artifact.get("degraded") else "OK")
    print("{} overall {} {}{}".format(verdict, block.get("overall_status"), block.get("status_counts"),
                                     ", reason: " + str(artifact.get("degraded_reason"))
                                     if artifact.get("degraded") else ""))
    for problem in problems:
        print("  " + problem)
    return 1 if problems else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: check_artifact.py <limit check or what-if result>")
        raise SystemExit(2)
    raise SystemExit(main(sys.argv[1]))
