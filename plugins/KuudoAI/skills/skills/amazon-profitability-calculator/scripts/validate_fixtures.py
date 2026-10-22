#!/usr/bin/env python3
"""
Re-run the documented worked examples against the scripts.

Both reference docs say "re-run this case after any change." This is that command.
The fixtures in fixtures/ carry their own `expected` block, so the numbers quoted in
references/formulas.md and references/period-pnl.md are checked against the code
rather than trusted, and a change that silently moves a fee model or a checkpoint
fails here instead of in someone's margin.

    python scripts/validate_fixtures.py
"""

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))

import margin  # noqa: E402
import pnl  # noqa: E402

FIXTURES = pathlib.Path(__file__).parent / "fixtures"
TOL = 5e-3  # half a cent, or half a tenth of a point


def compare(label, got, want, tol=TOL):
    ok = got is not None and abs(got - want) <= tol
    print(f"  {'PASS' if ok else 'FAIL'}  {label:<30} expected {want:>12,.4f}  got "
          f"{'None' if got is None else format(got, '>12,.4f')}")
    return ok


def check_per_unit(path, doc):
    exp = doc["expected"]
    r = margin.run(doc)
    ok = True
    for key, want in exp.items():
        if key == "loss_zones_count":
            got = len(r["loss_zones"])
            hit = got == want
            print(f"  {'PASS' if hit else 'FAIL'}  {key:<30} expected {want:>12}  got {got:>12}")
            ok &= hit
        elif key == "warning_contains":
            hit = any(want in w for w in r["warnings"])
            print(f"  {'PASS' if hit else 'FAIL'}  {key:<30} expected {want!r} in warnings")
            ok &= hit
        else:
            ok &= compare(key, r.get(key), want)
    return ok


def check_period(path, doc):
    exp = doc["expected"]
    r = pnl.analyse(doc)
    ok = compare("net_revenue", r["checkpoints"]["net_revenue"], exp["net_revenue"], 0.05)
    for key in ("product_margin_pct", "channel_margin_pct", "growth_margin_pct",
                "net_operating_profit_pct"):
        ok &= compare(key, r["margins"][key], exp[key], 5e-4)
    ok &= compare("tacos", r["tacos"], exp["tacos"], 5e-4)
    return ok


def main():
    all_ok = True
    for path in sorted(FIXTURES.glob("*.json")):
        doc = json.load(open(path))
        print(f"\n{path.name} — {doc.get('_case', '')}")
        runner = check_period if path.name.startswith("period-") else check_per_unit
        all_ok &= runner(path, doc)
    print("\nAll fixtures pass." if all_ok else "\nFIXTURE FAILURES — do not ship.")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
