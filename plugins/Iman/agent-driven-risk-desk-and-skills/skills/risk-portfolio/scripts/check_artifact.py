#!/usr/bin/env python3
"""Re-derive the identities of a saved risk_exposure result and print a one line verdict.

Run rather than read: only the output enters the conversation.

    python3 check_artifact.py /path/to/exposure_result.json

Exit 0 when every check passes (OK or DEGRADED), 1 on FAIL, 2 on usage error.
Standard library only, so it runs without the Risk Desk environment.
"""
import json
import math
import sys

FIELDS = ("currency", "as_of", "source", "data_mode", "input_sha256", "degraded", "degraded_reason", "nav",
          "gross_exposure", "net_exposure", "gross_leverage", "net_leverage", "net_by_asset", "gross_shares")


def finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def close(a, b, scale=1.0):
    return math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-9 * scale)


def check(result):
    """Return a list of problems with an exposure result."""
    if "error" in result:
        return ["the tool refused the request: {}: {}".format(result["error"], result.get("message"))]
    found =["missing field: " + f for f in FIELDS if f not in result]
    if found:
        return found
    if result["degraded"] != bool(result["degraded_reason"]):
        found.append("degraded flag and degraded_reason disagree")
    net_by_asset, shares = result["net_by_asset"], result["gross_shares"]
    numbers = [result[k] for k in ("nav", "gross_exposure", "net_exposure", "gross_leverage", "net_leverage")]
    if not all(finite(v) for v in numbers + list(net_by_asset.values()) + list(shares.values())):
        return found + ["missing or non-finite number"]
    nav, gross, net = result["nav"], result["gross_exposure"], result["net_exposure"]
    scale = max(abs(gross), abs(net), 1.0)
    if nav <= 0:
        found.append("nav is not positive")
    if gross < abs(net) - 1e-9 * scale:
        found.append("gross is below the absolute value of net")
    if not close(result["gross_leverage"], gross / nav, scale / nav):
        found.append("gross_leverage is not gross / nav")
    if not close(result["net_leverage"], net / nav, scale / nav):
        found.append("net_leverage is not net / nav")
    if not close(math.fsum(net_by_asset.values()), net, scale):
        found.append("net_by_asset does not sum to net_exposure")
    if set(net_by_asset) != set(shares):
        found.append("net_by_asset and gross_shares name different assets")
    if any(s < 0 or s > 1 + 1e-12 for s in shares.values()):
        found.append("a share of gross is outside [0, 1]")
    if gross > 0 and not close(math.fsum(shares.values()), 1.0):
        found.append("gross_shares do not sum to 1")
    if gross == 0 and any(shares.values()):
        found.append("gross is zero but a share is not")
    for asset in set(net_by_asset) & set(shares):
        if shares[asset] * gross < abs(net_by_asset[asset]) - 1e-9 * scale:
            found.append("asset {}: gross share is below its absolute net".format(asset))
    return found


def main(path):
    with open(path, encoding="utf-8") as handle:
        result = json.load(handle)
    found = check(result)
    verdict = "FAIL" if found else ("DEGRADED" if result.get("degraded") else "OK")
    shares = result.get("gross_shares") or {}
    top = max(shares, key=shares.get) if shares and not found else None
    print("{} {} gross {} net {}, {} asset(s){}{}".format(
        verdict, result.get("currency", "?"), result.get("gross_exposure"), result.get("net_exposure"),
        len(shares), ", largest share {} {:.2%}".format(top, shares[top]) if top else "",
        ", reason: " + str(result.get("degraded_reason")) if result.get("degraded") else ""))
    for problem in found:
        print("  " + problem)
    return 1 if found else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: check_artifact.py <risk_exposure result JSON>")
        raise SystemExit(2)
    raise SystemExit(main(sys.argv[1]))
