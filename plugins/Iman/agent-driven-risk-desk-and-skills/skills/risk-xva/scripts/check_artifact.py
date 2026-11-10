#!/usr/bin/env python3
"""Check a saved risk_xva result (OUTPUT/riskdesk-xva.json) and print a one line verdict.

Run rather than read: only the output enters the conversation.

    python3 check_artifact.py /path/to/output/riskdesk-xva.json

It checks what the adapter guarantees, not ORE's models: no ORE errors, XVA
rows present, every row keyed by its report's columns, finite numbers,
input hashes recorded. It also names the XVA columns that hold nulls, which
are unavailable values and not zeros.
Exit 0 when every check passes, 1 on FAIL, 2 on usage error. Standard library only.
"""
import json
import math
import re
import sys

FIELDS = ("backend", "backend_version", "backend_git_hash", "currency", "as_of", "requested_xva_flags", "errors",
          "reports", "data_mode", "input_hashes", "degraded", "degraded_reason", "assumptions", "artifact")


def check(result):
    """Return a list of problems with a risk_xva result."""
    if "error" in result:
        return ["the run was refused: {}: {}".format(result["error"], result.get("message"))]
    found = ["missing field: " + f for f in FIELDS if f not in result]
    if found:
        return found
    if result["errors"]:
        found.append("ORE reported errors; the adapter never accepts such a run")
    if result["degraded"] != bool(result["degraded_reason"]):
        found.append("degraded flag and degraded_reason disagree")
    if not result["currency"]:
        found.append("no base currency (baseCurrency) in the xva analytic")
    hashes = result["input_hashes"]
    if not hashes or not all(re.fullmatch(r"[0-9a-f]{64}", str(h)) for h in hashes.values()):
        found.append("input_hashes missing or not SHA-256")
    reports = result["reports"]
    if not reports.get("xva", {}).get("rows"):
        found.append("no XVA rows")
    for name, report in sorted(reports.items()):
        if name != "xva" and not name.startswith("exposure_"):
            found.append("report {}: not one the adapter keeps".format(name))
        columns = report.get("columns")
        for index, row in enumerate(report.get("rows", [])):
            if list(row) != columns:
                found.append("report {} row {}: keys differ from its columns".format(name, index))
                break
            if any(isinstance(v, float) and not math.isfinite(v) for v in row.values()):
                found.append("report {} row {}: non-finite number".format(name, index))
                break
    return found


def main(path):
    with open(path, encoding="utf-8") as handle:
        result = json.load(handle)
    found = check(result)
    rows = (result.get("reports") or {}).get("xva", {}).get("rows") or []
    nulls = sorted({k for row in rows for k, v in row.items() if v is None})
    exposure = [n for n in result.get("reports") or {} if n.startswith("exposure_")]
    print("{} {} as of {}, {} XVA row(s), {} exposure report(s), flags {}{}".format(
        "FAIL" if found else "OK", result.get("currency", "?"), result.get("as_of", "?"), len(rows),
        len(exposure), result.get("requested_xva_flags"),
        ", null (unavailable) in: " + ", ".join(nulls) if nulls else ""))
    for problem in found:
        print("  " + problem)
    return 1 if found else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: check_artifact.py <OUTPUT/riskdesk-xva.json>")
        raise SystemExit(2)
    raise SystemExit(main(sys.argv[1]))
