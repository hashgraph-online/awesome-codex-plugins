#!/usr/bin/env python3
"""
Amazon per-unit margin cascade, with break-even and target-margin solvers.

Reads a JSON input document on stdin or from a file path argument, writes a JSON
result document to stdout.

The point of this script is that the two solvers are not simple division. Referral
bands, FBA price bands and VAT all move with price, so the fee has to be recomputed
at every candidate price. Doing that by hand is where the arithmetic goes wrong.

Fee model
---------
Amazon's side of the P&L is supplied one of two ways:

  "probes"  - a list of {price, referral, fba} points sampled from
              fees_getMyFeesEstimates. This is the preferred mode: Amazon applies its
              own band logic, so no fee tables are embedded here and nothing goes
              stale. Referral is interpolated linearly between bracketing probes;
              FBA is held as a step from the nearest probe at or below the price,
              which matches how FBA price bands actually behave.

  "rule"    - explicit referral bands plus a fixed FBA fee. For pre-launch products
              with no ASIN, or when the seller is overriding what Seller Central
              shows them.

Solver accuracy is bounded by probe density. Probe every $1 across the plausible
range and the solved prices are good to a few cents.

Usage:
    python margin.py inputs.json
    cat inputs.json | python margin.py
"""

import json
import sys

# --------------------------------------------------------------------------
# Fee models
# --------------------------------------------------------------------------


class ProbeFeeModel:
    """Fees sampled from SP-API at a set of candidate prices."""

    def __init__(self, points):
        if not points:
            raise ValueError("probe fee model needs at least one point")
        self.points = sorted(points, key=lambda p: p["price"])

    def fees(self, price):
        pts = self.points
        if len(pts) == 1:
            p = pts[0]
            return p["referral"], p["fba"], p.get("closing", 0.0)

        # Clamp outside the probed range rather than extrapolating: extrapolating a
        # banded fee schedule invents rates Amazon never quoted.
        if price <= pts[0]["price"]:
            lo = hi = pts[0]
        elif price >= pts[-1]["price"]:
            lo = hi = pts[-1]
        else:
            # lo is the highest probe at or below the price. Taking the bracket this
            # way matters when the price exactly matches a probe: that probe's own
            # FBA fee should win, not the one below it.
            idx = 0
            for i, p in enumerate(pts):
                if p["price"] <= price:
                    idx = i
            lo = pts[idx]
            hi = pts[min(idx + 1, len(pts) - 1)]

        if hi["price"] == lo["price"]:
            referral = lo["referral"]
        else:
            t = (price - lo["price"]) / (hi["price"] - lo["price"])
            referral = lo["referral"] + t * (hi["referral"] - lo["referral"])

        # FBA fee steps at band boundaries; carry the last observed value forward.
        return referral, lo["fba"], lo.get("closing", 0.0)


class RuleFeeModel:
    """
    Referral bands plus a fixed FBA fee.

    Each band is {"up_to": <price or null>, "rate": <fraction>, "mode": "marginal"|"whole"}.

      marginal - the rate applies only to the portion of the price inside this band
                 (e.g. Jewelry: 20% on the portion up to $250, 5% above)
      whole    - once the price exceeds the previous band's ceiling, this rate applies
                 to the entire price (e.g. Beauty: 8% up to $10, then 15% on the whole
                 price)

    A "whole" band creates a discontinuity in the fee curve, which is exactly why the
    solvers scan rather than divide.
    """

    def __init__(self, bands, fba_fee, closing_fee=0.0, per_item_minimum=0.0):
        self.bands = bands
        self.fba_fee = fba_fee
        self.closing_fee = closing_fee
        self.per_item_minimum = per_item_minimum

    def fees(self, price):
        referral = 0.0
        lower = 0.0
        for band in self.bands:
            ceiling = band.get("up_to")
            mode = band.get("mode", "marginal")
            if mode == "whole":
                if ceiling is None or price <= ceiling:
                    if price > lower:
                        referral = price * band["rate"]
                        break
                else:
                    lower = ceiling
                    continue
            portion_top = price if ceiling is None else min(price, ceiling)
            if portion_top > lower:
                referral += (portion_top - lower) * band["rate"]
            if ceiling is None or price <= ceiling:
                break
            lower = ceiling

        referral = max(referral, self.per_item_minimum)
        return referral, self.fba_fee, self.closing_fee


def build_fee_model(spec):
    kind = spec.get("type", "probes")
    if kind == "probes":
        return ProbeFeeModel(spec["points"])
    if kind == "rule":
        return RuleFeeModel(
            spec["referral_bands"],
            spec.get("fba_fee", 0.0),
            spec.get("closing_fee", 0.0),
            spec.get("per_item_minimum", 0.0),
        )
    raise ValueError(f"unknown fee model type: {kind}")


# --------------------------------------------------------------------------
# The cascade
# --------------------------------------------------------------------------


def cascade(price, inp, fee_model):
    """Build the full per-unit waterfall at a given selling price."""

    vat_rate = inp.get("vat_rate", 0.0)
    net_revenue = price / (1.0 + vat_rate)

    referral, fba, closing = fee_model.fees(price)
    if inp.get("referral_fee_override") is not None:
        referral = inp["referral_fee_override"]
    if inp.get("fba_fee_override") is not None:
        fba = inp["fba_fee_override"]

    storage = inp.get("storage_per_unit", 0.0)
    programme = (
        inp.get("inbound_placement_fee", 0.0)
        + inp.get("low_inventory_fee", 0.0)
        + inp.get("storage_utilisation_surcharge", 0.0)
        + inp.get("aged_inventory_surcharge", 0.0)
        + inp.get("other_amazon_fees", 0.0)
    )

    cogs = inp.get("cogs", 0.0)
    inbound = inp.get("inbound_shipping", 0.0)
    advertising = inp.get("advertising_per_unit", 0.0)
    other = inp.get("other_costs", 0.0)

    # Returns, as an expected value per unit sold.
    rr = inp.get("return_rate", 0.0)
    restock = inp.get("restock_share", 0.0)
    admin_cap = inp.get("refund_admin_fee_cap", 5.0)
    admin_rate = inp.get("refund_admin_fee_rate", 0.20)
    processing_fee = inp.get("returns_processing_fee", 0.0)

    admin_fee = min(referral * admin_rate, admin_cap)
    referral_refunded = referral - admin_fee

    ret_revenue_lost = -rr * net_revenue
    ret_referral_back = rr * referral_refunded
    ret_processing = -rr * processing_fee
    ret_stock_recovered = rr * restock * cogs
    returns_net = (
        ret_revenue_lost + ret_referral_back + ret_processing + ret_stock_recovered
    )

    amazon_fees = referral + fba + closing + storage + programme

    profit = (
        net_revenue
        - amazon_fees
        - cogs
        - inbound
        - advertising
        - other
        + returns_net
    )

    return {
        "selling_price": price,
        "net_revenue": net_revenue,
        "lines": {
            "referral_fee": -referral,
            "closing_fee": -closing,
            "fba_fulfilment_fee": -fba,
            "fba_storage_fee": -storage,
            "programme_and_inventory_fees": -programme,
            "cogs_landed": -cogs,
            "inbound_shipping": -inbound,
            "advertising": -advertising,
            "returns_refunded_revenue": ret_revenue_lost,
            "returns_referral_refunded": ret_referral_back,
            "returns_processing_fee": ret_processing,
            "returns_stock_recovered": ret_stock_recovered,
            "other_costs": -other,
        },
        "amazon_fees_total": amazon_fees,
        "returns_net": returns_net,
        "operating_profit": profit,
        "operating_margin": profit / net_revenue if net_revenue else None,
        "roi_on_cogs": profit / cogs if cogs else None,
        # Net revenue, to match every other margin here. Dividing by the
        # VAT-inclusive price understates the take by the VAT rate.
        "amazon_take": amazon_fees / net_revenue if net_revenue else None,
        "amazon_take_of_gross_price": amazon_fees / price if price else None,
        "amazon_take_denominator": "net_revenue",
    }


# --------------------------------------------------------------------------
# Solvers
# --------------------------------------------------------------------------


def _refine(f, neg_x, pos_x, want_negative_side, iters=60):
    """
    Bisect between a price that loses money and one that does not, returning the
    boundary between them.

    `want_negative_side` picks which side to return, and that choice is not
    pedantry. Banded schedules make the profit curve genuinely discontinuous: at a
    "whole" referral band threshold the curve jumps straight across zero, so there
    may be no price where f == 0 at all. Bisecting to "the root" of a jump returns a
    price that is not a root. Naming the side is the only honest answer — the
    negative side is the last price that loses money, the positive side the first
    that does not.
    """
    a, b = neg_x, pos_x
    for _ in range(iters):
        m = (a + b) / 2.0
        if f(m) < 0:
            a = m
        else:
            b = m
    return a if want_negative_side else b


def _negative_zones(f, lo, hi, steps=2000):
    """
    Every contiguous stretch of [lo, hi] where f < 0, with refined edges.

    Scanning the whole range, rather than returning the first root, is what makes
    banded schedules safe to act on. A "whole" referral band re-rates the *entire*
    price once the threshold is crossed, so profit can be positive below the
    threshold, negative just above it, and positive again further up. FBA price
    bands do the same thing in live mode. A solver that stops at the first root
    reports the price below the dip and silently hides the loss zone above it, which
    is precisely the trap this model exists to avoid.
    """
    if hi <= lo:
        return []
    width = (hi - lo) / steps
    xs = [lo + i * width for i in range(steps + 1)]
    flags = [f(x) < 0 for x in xs]

    zones = []
    i = 0
    while i <= steps:
        if not flags[i]:
            i += 1
            continue
        j = i
        while j + 1 <= steps and flags[j + 1]:
            j += 1
        start = xs[0] if i == 0 else _refine(f, xs[i], xs[i - 1], True)
        end = xs[steps] if j == steps else _refine(f, xs[j], xs[j + 1], False)
        zones.append((start, end))
        i = j + 1
    return zones


def _solve(f, lo, hi, steps=2000):
    """
    Resolve a price target into the two numbers a seller actually needs.

    `safe_floor` is the lowest price at or above which the condition holds all the
    way to the top of the range — the number to act on. `lowest_crossing` is where
    the curve first turns non-negative, which is the classic answer and is only
    equal to the safe floor when nothing dips back down above it.
    """
    zones = _negative_zones(f, lo, hi, steps)
    if not zones:
        return {
            "safe_floor": lo,
            "lowest_crossing": lo,
            "loss_zones": [],
            "holds_at_range_floor": True,
        }

    holds_at_floor = zones[0][0] > lo
    last_end = zones[-1][1]
    return {
        "safe_floor": None if last_end >= hi else last_end,
        "lowest_crossing": lo if holds_at_floor else zones[0][1],
        "loss_zones": [[a, b] for a, b in zones],
        "holds_at_range_floor": holds_at_floor,
    }


def solve_break_even(inp, fee_model, lo, hi):
    return _solve(lambda p: cascade(p, inp, fee_model)["operating_profit"], lo, hi)


def solve_target_margin(inp, fee_model, target, lo, hi):
    def f(p):
        c = cascade(p, inp, fee_model)
        return c["operating_profit"] - target * c["net_revenue"]

    return _solve(f, lo, hi)


def max_ad_spend(inp, fee_model, target, price):
    """Advertising the unit can absorb at the current price and still hit target."""
    stripped = dict(inp)
    stripped["advertising_per_unit"] = 0.0
    c = cascade(price, stripped, fee_model)
    allowed = target * c["net_revenue"]
    return c["operating_profit"] - allowed


# --------------------------------------------------------------------------


def run(doc):
    inp = doc["inputs"]
    fee_model = build_fee_model(doc["fee_model"])
    price = inp["selling_price"]
    target = inp.get("target_margin", 0.20)

    solve_lo = doc.get("solve_range", {}).get("low", max(0.5, price * 0.2))
    solve_hi = doc.get("solve_range", {}).get("high", price * 3.0)

    result = cascade(price, inp, fee_model)
    result["target_margin"] = target

    be = solve_break_even(inp, fee_model, solve_lo, solve_hi)
    tm = solve_target_margin(inp, fee_model, target, solve_lo, solve_hi)

    # The headline number is the safe floor, not the first crossing. When a band
    # threshold sits above the first crossing, pricing anywhere in the dip loses
    # money, and the first crossing is the number that gets someone there.
    result["break_even_price"] = be["safe_floor"]
    result["lowest_break_even"] = be["lowest_crossing"]
    result["loss_zones"] = be["loss_zones"]
    result["price_for_target_margin"] = tm["safe_floor"]
    result["lowest_price_at_target_margin"] = tm["lowest_crossing"]
    result["below_target_zones"] = tm["loss_zones"]

    result["max_ad_spend_at_target"] = max_ad_spend(inp, fee_model, target, price)
    result["solve_range"] = {"low": solve_lo, "high": solve_hi}

    warnings = []

    def _dead_zones(solved, label, verb):
        floor = solved["lowest_crossing"]
        dips = [z for z in solved["loss_zones"] if z[0] > floor + 1e-9]
        if dips:
            spans = "; ".join(f"{a:.2f}-{b:.2f}" for a, b in dips)
            warnings.append(
                f"{label} is non-monotonic: the unit {verb} again between {spans}. "
                "A whole-price referral band or an FBA price band re-rates the entire "
                "price at that threshold. Report the safe floor "
                f"({solved['safe_floor']:.2f}), not the lowest crossing "
                f"({floor:.2f}), and do not price inside those ranges."
                if solved["safe_floor"] is not None
                else f"{label} is non-monotonic: the unit {verb} again between "
                f"{spans}, and never recovers inside the solve range. Probe higher."
            )

    _dead_zones(be, "Break-even", "loses money")
    _dead_zones(tm, "Target margin", "falls below target")

    if be["holds_at_range_floor"]:
        warnings.append(
            "Profitable at the bottom of the solve range, so the true break-even "
            "sits below it. Widen solve_range.low to find it."
        )
    if be["safe_floor"] is None:
        warnings.append("No price inside the solve range is profitable all the way up.")
    if tm["safe_floor"] is None:
        warnings.append("Target margin is not held anywhere inside the solve range.")

    if doc["fee_model"].get("type", "probes") == "probes":
        pts = sorted(p["price"] for p in doc["fee_model"]["points"])
        floor = result["break_even_price"] or result["lowest_break_even"]
        if floor is not None and floor < pts[0]:
            warnings.append(
                "Break-even price falls below the lowest probed price; fees were "
                "clamped. Probe lower to confirm."
            )
        if len(pts) < 5:
            warnings.append(
                "Fewer than 5 fee probes. Solved prices may miss a band boundary."
            )
    result["warnings"] = warnings

    return result


def main():
    raw = open(sys.argv[1]).read() if len(sys.argv) > 1 else sys.stdin.read()
    print(json.dumps(run(json.loads(raw)), indent=2))


if __name__ == "__main__":
    main()
