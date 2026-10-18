#!/usr/bin/env python3
"""
Amazon period P&L: the eight-step waterfall from gross ordered revenue to net
operating profit, with four margin checkpoints.

This is a different calculation from margin.py. That one models one hypothetical unit
and solves for prices. This one reports what a period actually did, and has lines the
per-unit model has no concept of: cancellations, A-to-Z claims, chargebacks, shipping
and gift wrap revenue, reimbursements, and allocated overheads.

The checkpoints are the point of the exercise. The final number says how much was made;
the checkpoints say why:

  Net Revenue      the denominator for every margin below — not gross sales
  Product Margin   what the product earns before any selling cost
  Channel Margin   what survives Amazon's fees; the cost of the channel, in points
  Growth Margin    what survives paying for growth
  Net Operating Profit

VAT is deliberately absent from the waterfall. It is collected for a tax authority and
is neither revenue nor cost; including it either inflates revenue or invents a cost,
and distorts every margin below. Pass it as `vat_memo` to have it reported outside the
profit math.

Usage:
    python pnl.py period.json
    cat period.json | python pnl.py
"""

import json
import sys

# Every line, in waterfall order: (key, label, sign, checkpoint_after)
LINES = [
    ("gross_ordered_revenue", "Gross Ordered Revenue", +1, None),
    ("cancelled_orders", "Cancelled Orders", -1, "gross_shipped_revenue"),
    ("refunds", "Refunds", -1, None),
    ("a_to_z_claims", "A-to-Z Claims", -1, None),
    ("chargebacks", "Chargebacks", -1, "net_product_revenue"),
    ("shipping_revenue", "Shipping Revenue", +1, None),
    ("gift_wrap_revenue", "Gift Wrap Revenue", +1, None),
    ("shipping_refunds", "Shipping Refunds", -1, "net_revenue"),
    ("cogs", "COGS", -1, "product_margin"),
    ("amazon_fees", "Amazon Fees", -1, "channel_margin"),
    ("advertising", "Advertising", -1, None),
    ("reimbursements", "Reimbursements", +1, "growth_margin"),
    ("allocated_overheads", "Allocated Overheads", -1, "net_operating_profit"),
]

CHECKPOINT_LABELS = {
    "gross_shipped_revenue": "Gross Shipped Revenue",
    "net_product_revenue": "Net Product Revenue",
    "net_revenue": "Net Revenue",
    "product_margin": "Product Margin",
    "channel_margin": "Channel Margin",
    "growth_margin": "Growth Margin",
    "net_operating_profit": "Net Operating Profit",
}

# Checkpoints that get a margin percentage. The revenue subtotals above Net Revenue
# do not — dividing revenue by revenue says nothing.
MARGIN_CHECKPOINTS = [
    "product_margin",
    "channel_margin",
    "growth_margin",
    "net_operating_profit",
]


def build_waterfall(period):
    running = 0.0
    rows = []
    checkpoints = {}

    for key, label, sign, checkpoint in LINES:
        value = float(period.get(key, 0.0) or 0.0)
        running += sign * value
        rows.append(
            {
                "key": key,
                "label": label,
                "value": sign * value,
                "sign": sign,
                "supplied": key in period and period[key] is not None,
            }
        )
        if checkpoint:
            checkpoints[checkpoint] = running
            rows.append(
                {
                    "key": checkpoint,
                    "label": CHECKPOINT_LABELS[checkpoint],
                    "value": running,
                    "is_checkpoint": True,
                }
            )

    return rows, checkpoints


def analyse(period):
    rows, cp = build_waterfall(period)
    net_revenue = cp["net_revenue"]

    if net_revenue == 0:
        raise ValueError("Net Revenue is zero — cannot compute margins.")

    margins = {
        f"{name}_pct": cp[name] / net_revenue for name in MARGIN_CHECKPOINTS
    }

    # Each cost expressed as points of net revenue. This is what makes a period
    # comparable to another period, and what the checkpoints are read against.
    points = {}
    for key, label, sign, _ in LINES:
        value = float(period.get(key, 0.0) or 0.0)
        if key in ("gross_ordered_revenue", "cancelled_orders"):
            continue
        points[key] = value / net_revenue

    ads = float(period.get("advertising", 0.0) or 0.0)
    tacos_denominator = period.get("tacos_denominator", "net_revenue")
    if tacos_denominator == "gross_ordered_revenue":
        denom = float(period.get("gross_ordered_revenue", 0.0) or 0.0)
    else:
        denom = net_revenue

    result = {
        "date_basis": period.get("date_basis"),
        "currency": period.get("currency"),
        "period_label": period.get("period_label"),
        "waterfall": rows,
        "checkpoints": cp,
        "margins": margins,
        "points_of_net_revenue": points,
        "tacos": (ads / denom) if denom else None,
        "tacos_denominator": tacos_denominator,
        "vat_memo": period.get("vat_memo"),
        "warnings": check(period, cp),
    }

    prior = period.get("prior")
    if prior:
        _, prior_cp = build_waterfall(prior)
        prior_nr = prior_cp["net_revenue"]
        if prior_nr:
            # Points, not fractions. The key says points, render() prints points,
            # and anything reading --json should not have to multiply by 100 to
            # agree with the text output.
            result["deltas_in_points"] = {
                name: 100.0
                * ((cp[name] / net_revenue) - (prior_cp[name] / prior_nr))
                for name in MARGIN_CHECKPOINTS
            }

    return result


def check(period, cp):
    """Flag the failure patterns that quietly inflate an Amazon margin."""
    w = []

    if not period.get("date_basis"):
        w.append(
            "No date basis stated. Order, shipment and settlement bases give three "
            "different answers for the same period; mixing them is the most common "
            "way this calculation breaks silently."
        )

    for key, label, _, _ in LINES:
        if key in ("gross_ordered_revenue",):
            continue
        if period.get(key) is None:
            if key in ("a_to_z_claims", "chargebacks"):
                w.append(
                    f"{label} not supplied. These sit in a different report from "
                    f"refunds and are routinely missed, which overstates revenue."
                )
            elif key == "reimbursements":
                w.append(
                    "Reimbursements not supplied. They are a positive line — money "
                    "Amazon owes for lost and damaged inventory. Omitting them "
                    "understates profit."
                )
            elif key == "allocated_overheads":
                w.append(
                    "Allocated overheads not supplied. Without them this stops at "
                    "Growth Margin and is not a net operating margin."
                )
            elif key == "cogs":
                w.append("COGS not supplied. Product Margin is meaningless without it.")

    if period.get("vat_memo") is None and period.get("currency") not in (
        "USD", "$", "usd", None
    ):
        w.append(
            "No VAT memo. VAT stays outside the waterfall, but sellers need the cash "
            "figure visible."
        )

    if cp["net_operating_profit"] > cp["net_revenue"]:
        w.append("Net operating profit exceeds net revenue — check the input signs.")

    return w


def render(r):
    """Plain-text waterfall, for reading rather than machine consumption."""
    cur = r.get("currency") or ""
    out = []
    header = r.get("period_label") or "Period"
    if r.get("date_basis"):
        header += f" · {r['date_basis']} basis"
    out.append(header)
    out.append("=" * len(header))

    nr = r["checkpoints"]["net_revenue"]
    for row in r["waterfall"]:
        if row.get("is_checkpoint"):
            pct = ""
            if row["key"] in MARGIN_CHECKPOINTS:
                pct = f"   {row['value'] / nr:6.1%}"
            out.append(f"  {'= ' + row['label']:<32}{cur}{row['value']:>12,.1f}{pct}")
        else:
            sign = "(-)" if row.get("sign", 1) < 0 else "(+)"
            out.append(
                f"  {sign} {row['label']:<28}{cur}{row['value']:>12,.1f}"
            )

    out.append("")
    out.append(f"  TACoS ({r['tacos_denominator']}): {r['tacos']:.1%}")
    if r.get("vat_memo") is not None:
        out.append(f"  VAT memo (outside the P&L): {cur}{r['vat_memo']:,.1f}")

    if r.get("deltas_in_points"):
        out.append("")
        out.append("  Change vs prior period, in points of net revenue:")
        for k, v in r["deltas_in_points"].items():
            out.append(f"    {k:<26}{v:+6.1f}")

    if r["warnings"]:
        out.append("")
        out.append("  Warnings:")
        for x in r["warnings"]:
            out.append(f"    - {x}")

    return "\n".join(out)


def main():
    raw = open(sys.argv[1]).read() if len(sys.argv) > 1 else sys.stdin.read()
    result = analyse(json.loads(raw))
    if "--json" in sys.argv:
        print(json.dumps(result, indent=2))
    else:
        print(render(result))


if __name__ == "__main__":
    main()
