# US referral fee schedule

**Marketplace:** amazon.com · **Verified:** 2026-09-08 · **Source:** sell.amazon.com/pricing

For manual mode only. In live mode, probe `fees_getMyFeesEstimates` instead — it
returns the real referral fee and needs no category mapping.

**Check the verification date.** Amazon changes referral fees regularly. If this date is
more than a few months behind the current date, say so in the output and prefer a live
probe or a user-supplied rate.

There is no European equivalent table here. For EU manual mode, take the rate from the
user or from a comparable-ASIN probe rather than guessing.

## Flat 15%

Backpacks/Handbags/Luggage · Eyewear · Footwear · Home and Kitchen · Lawn and Garden ·
Mattresses · Media (Books, DVD, Music, Software, Video) · Musical Instruments and AV
Production · Office Products · Pet Supplies · Sports and Outdoors · Tools and Home
Improvement · Toys and Games · Video Games and Gaming Accessories · Everything Else

```json
[{"up_to": null, "rate": 0.15, "mode": "marginal"}]
```

## Other flat rates

| Category | Rate |
| --- | --- |
| Amazon Device Accessories | 45% |
| Appliances, full-size | 8% |
| Computers | 8% |
| Consumer Electronics | 8% |
| Video Game Consoles | 8% |
| Tires | 10% |
| Automotive and Powersports | 12% |
| Base Equipment Power Tools | 12% |
| Business, Industrial and Scientific Supplies | 12% |
| Pet Supplies: veterinary diets | 22% |

## Marginal bands

The rate applies only to the portion of the price inside each band.

**Appliances, compact** — 15% up to $300, 8% above
```json
[{"up_to": 300, "rate": 0.15, "mode": "marginal"},
 {"up_to": null, "rate": 0.08, "mode": "marginal"}]
```

**Electronics Accessories** — 15% up to $100, 8% above
```json
[{"up_to": 100, "rate": 0.15, "mode": "marginal"},
 {"up_to": null, "rate": 0.08, "mode": "marginal"}]
```

**Furniture** — 15% up to $200, 10% above
```json
[{"up_to": 200, "rate": 0.15, "mode": "marginal"},
 {"up_to": null, "rate": 0.10, "mode": "marginal"}]
```

**Jewelry** — 20% up to $250, 5% above
```json
[{"up_to": 250, "rate": 0.20, "mode": "marginal"},
 {"up_to": null, "rate": 0.05, "mode": "marginal"}]
```

**Watches** — 16% up to $1,500, 3% above
```json
[{"up_to": 1500, "rate": 0.16, "mode": "marginal"},
 {"up_to": null, "rate": 0.03, "mode": "marginal"}]
```

**Fine Art** — 20% up to $100, 15% to $1,000, 10% to $5,000, 5% above
```json
[{"up_to": 100, "rate": 0.20, "mode": "marginal"},
 {"up_to": 1000, "rate": 0.15, "mode": "marginal"},
 {"up_to": 5000, "rate": 0.10, "mode": "marginal"},
 {"up_to": null, "rate": 0.05, "mode": "marginal"}]
```

## Whole-price bands

Crossing the threshold re-rates the **entire** price, which creates a jump in the fee
curve. A product priced just above a threshold can net less than one priced just below.

**Baby Products** and **Beauty, Health and Personal Care** — 8% up to $10, then 15% on the whole price
```json
[{"up_to": 10, "rate": 0.08, "mode": "whole"},
 {"up_to": null, "rate": 0.15, "mode": "whole"}]
```

**Grocery and Gourmet** — 8% up to $15, then 15% on the whole price
```json
[{"up_to": 15, "rate": 0.08, "mode": "whole"},
 {"up_to": null, "rate": 0.15, "mode": "whole"}]
```

**Lawn Mowers and Snow Throwers** — 15% up to $500, then 8% on the whole price
```json
[{"up_to": 500, "rate": 0.15, "mode": "whole"},
 {"up_to": null, "rate": 0.08, "mode": "whole"}]
```

**Clothing and Accessories** — 5% up to $15, 10% up to $20, then 17% on the whole price
```json
[{"up_to": 15, "rate": 0.05, "mode": "whole"},
 {"up_to": 20, "rate": 0.10, "mode": "whole"},
 {"up_to": null, "rate": 0.17, "mode": "whole"}]
```

## Minimums and closing fees

**The amounts are deliberately not embedded here.** Which categories carry them is
stable and is recorded below; what they cost is not, and the guardrail in SKILL.md —
never invent a fee number — applies to these as much as to a referral rate.

A per-item referral **minimum** applies in most categories. Grocery and Gourmet, Media,
Video Games and Gaming Accessories, and Video Game Consoles carry **no** minimum.

A **closing fee** applies to Media, Video Games and Gaming Accessories, and Video Game
Consoles.

Where the category carries one, get the amount from a live `fees_getMyFeesEstimates`
probe (which already includes both, so in live mode there is nothing to pass), from the
seller, or from sell.amazon.com/pricing — then pass them as `per_item_minimum` and
`closing_fee`. If you cannot source them, run without them and say in the output that
the referral fee is understated by an unquantified per-item minimum, rather than
guessing a figure.

## Not covered here

FBA fulfilment fees by size tier, Low-Price FBA rates, apparel tables, peak uplifts,
fuel surcharges, storage rates, and every European schedule. These are deliberately
absent rather than approximated. Get them from a live probe, a comparable ASIN, or the
user.
