# Formulas and the script contract

## Input document

`scripts/margin.py` reads a JSON document with two required keys, `inputs` and
`fee_model`, and an optional `solve_range`.

```json
{
  "inputs": {
    "selling_price": 29.99,
    "vat_rate": 0.0,
    "cogs": 8.00,
    "inbound_shipping": 1.00,
    "advertising_per_unit": 2.00,
    "return_rate": 0.03,
    "restock_share": 0.60,
    "storage_per_unit": 0.29,
    "other_costs": 0.0,
    "target_margin": 0.20,

    "inbound_placement_fee": 0.0,
    "low_inventory_fee": 0.0,
    "storage_utilisation_surcharge": 0.0,
    "aged_inventory_surcharge": 0.0,
    "other_amazon_fees": 0.0,
    "returns_processing_fee": 0.0,

    "refund_admin_fee_rate": 0.20,
    "refund_admin_fee_cap": 5.0,

    "referral_fee_override": null,
    "fba_fee_override": null
  },
  "fee_model": { "type": "probes", "points": [] },
  "solve_range": { "low": 6.0, "high": 90.0 }
}
```

Rates are fractions, not percentages: 3% is `0.03`.

The refund administration fee is 20% of the referral fee, capped at 5 units of local
currency — 52.5 SEK or 20 PLN in those markets. Set `refund_admin_fee_cap`
accordingly when working outside USD/GBP/EUR.

## Fee models

### `probes` — live mode

```json
{
  "type": "probes",
  "points": [
    {"price": 15.00, "referral": 2.25, "fba": 5.50},
    {"price": 20.00, "referral": 3.00, "fba": 5.50},
    {"price": 29.99, "referral": 4.50, "fba": 6.31}
  ]
}
```

Each point comes from a `fees_getMyFeesEstimates` call at that price. Referral is
interpolated linearly between bracketing probes; FBA is carried forward as a step from
the nearest probe at or below the price, matching how FBA price bands behave.

Outside the probed range the model **clamps rather than extrapolates**, because
extrapolating a banded schedule invents rates Amazon never quoted. If a solved price
lands outside the range, the script warns — probe wider and re-run.

Probe density bounds solver accuracy. At $1 intervals the solved prices are good to a
few cents. Fewer than five probes triggers a warning.

### `rule` — manual mode

```json
{
  "type": "rule",
  "referral_bands": [
    {"up_to": 10, "rate": 0.08, "mode": "whole"},
    {"up_to": null, "rate": 0.15, "mode": "whole"}
  ],
  "fba_fee": 6.31,
  "closing_fee": 0.0,
  "per_item_minimum": 0.30
}
```

Band `mode` encodes the two shapes Amazon's schedules actually take:

- `marginal` — the rate applies only to the portion of the price inside the band.
  Jewelry: 20% on the portion up to $250, 5% above. At $300 the fee is $52.50.
- `whole` — once the price passes the previous ceiling, the rate applies to the
  **entire** price. Beauty: 8% up to $10, then 15% on the whole price. At $9 the fee
  is $0.72; at $11 it jumps to $1.65.

Getting this distinction wrong is the most common error in hand-built Amazon
calculators, and it is why the solvers scan rather than divide — a `whole` band puts a
genuine discontinuity in the profit curve.

## Line definitions

| Line | Definition |
| --- | --- |
| Net revenue | `selling_price / (1 + vat_rate)`. VAT is collected for a tax authority and is not revenue. |
| Referral fee | From the fee model at the current price, or the override |
| FBA fulfilment fee | Same |
| Storage, programme, inventory-health fees | Summed as supplied; not returned by the fee estimate |
| COGS landed | Seller input |
| Inbound shipping | Seller input, per unit |
| Advertising | Ad spend ÷ units. See the convention note in SKILL.md. |
| Other costs | Seller input |

Returns are an **expected value per unit sold**, not per unit returned — all four
components are multiplied by the return rate:

| Line | Definition |
| --- | --- |
| Refunded revenue | `−return_rate × net_revenue` |
| Referral refunded | `+return_rate × (referral − min(referral × 0.20, cap))` |
| Processing fee | `−return_rate × returns_processing_fee` |
| Stock recovered | `+return_rate × restock_share × cogs` |

Outputs:

| Metric | Definition |
| --- | --- |
| Operating profit/unit | Net revenue − Amazon fees − COGS − inbound − advertising − other + returns net |
| Operating margin | Operating profit ÷ net revenue |
| ROI on COGS | Operating profit ÷ COGS |
| Amazon take | Total Amazon fees ÷ net revenue. `amazon_take_of_gross_price` carries the VAT-inclusive version |
| Break-even price | **Safe floor** — lowest price profitable all the way to the top of the solve range |
| `lowest_break_even` | First price where profit turns positive. Equal to the safe floor only when nothing dips below it again |
| `loss_zones` | Price ranges inside the solve range where the unit loses money |
| Price for target margin | Lowest price that holds the target all the way up; `below_target_zones` lists the dips |
| Max ad spend at target | Profit excluding advertising, minus target × net revenue, at the current price |

Note that the target-margin price can land **below** the current price when the product
already exceeds the target. That is correct behaviour, not a bug — it is the price at
which the margin falls to exactly the target.

**Why a safe floor rather than the first root.** A `whole` band re-rates the entire
price at its threshold, so the profit curve genuinely jumps. Profit can be positive
below the threshold, negative just above it, and positive again higher up. A solver that
returns the first root reports the price *below* the dip and hides the loss zone above
it — the exact error this model exists to prevent. So the solvers scan the whole range,
report the lowest price above which the condition holds throughout, and name the dead
zones. FBA price bands do the same thing in live mode, so this is not a manual-mode
curiosity.

## Validation

The script reproduces the published Clarisix worked example — US Home and Kitchen,
$29.99, $8.00 landed, $1.00 inbound, $2.00 ads, 3% returns with 60% restocked, $0.29
storage, 15% referral, $6.31 FBA — to the cent:

| Metric | Expected | Produced |
| --- | --- | --- |
| Operating profit | $7.24 | 7.2438 |
| Operating margin | 24.1% | 24.15% |
| ROI on COGS | 90.5% | 90.55% |
| Amazon take | 37.0% | 37.01% |
| Returns (net) | −$0.65 | −0.6477 |
| Break-even price | $21.20 | 21.19 |
| Price for 20% margin | $28.00 | 27.99 |
| Max ad spend at 20% | $3.24 | 3.246 |

Break-even differs by a cent because the reference implementation re-derives the FBA
price band at the lower price while this run held FBA fixed. In live mode a probe
sweep captures that band change.

This case ships as `scripts/fixtures/per-unit-us-home-kitchen.json`, alongside
`per-unit-beauty-whole-band.json`, which pins the discontinuity behaviour. Re-run both
after any change to the script:

```bash
python scripts/validate_fixtures.py
```
