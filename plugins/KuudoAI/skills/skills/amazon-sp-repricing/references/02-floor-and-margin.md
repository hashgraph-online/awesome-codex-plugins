# The floor: computing it instead of guessing

Every repricing failure that loses money traces back to a floor that was wrong.
A floor set by feel is usually a round number the seller finds comfortable, and
comfort is not a break-even. This file is the arithmetic.

## Why the floor cannot be a single number for the catalog

Referral fees are a percentage, so they scale with price. FBA fulfillment fees
scale with size and weight, not price. Storage scales with volume and season.
So two SKUs at the same price have different break-evens, and one SKU has a
different break-even at two different prices. A catalog-wide "never go below
$X" or "keep 20% margin" collapses all of that into a number that is wrong
almost everywhere.

Compute per SKU. The Product Fees API will estimate fees for a price you have
not set yet, which is exactly what this needs.

## The components

Work down from the price a customer pays.

| Component | Where it comes from | Notes |
|---|---|---|
| Selling price | The candidate you are testing | Include shipping if merchant-fulfilled, since the buyer sees landed price |
| Referral fee | Fee estimate at that price | Percentage of price, category-dependent |
| Fulfillment fee | Fee estimate at that price | FBA: size and weight tier. MFN: your actual shipping cost |
| Storage | Seller's own figures | Monthly plus long-term; seasonal rates differ |
| Cost of goods | Seller-supplied | Landed unit cost including inbound freight and duty |
| Returns allowance | Seller's return rate per SKU | A 12% return rate on a category with restocking losses is a real per-unit cost |
| Advertising allocation | Seller-supplied | If a SKU only sells with ads, ad cost belongs in the floor |

The last three are the ones people leave out, and they are why a "profitable"
repricing floor produces an unprofitable quarter. Storage and returns in
particular are invisible at the transaction level and obvious at the P&L level.

**Break-even price** is the price where the components above net to zero
contribution. **Floor** is break-even plus the minimum contribution the seller
is willing to accept on that SKU. Those are different numbers and the
difference is a business decision, so ask for it rather than assuming zero.

## Getting the inputs you cannot compute

Cost of goods, target contribution, storage, and return allowance are the
seller's data, not Amazon's. Ask for them once, explicitly, and record what
you were given. Where the seller does not know a figure, say what you assumed
and flag it, rather than silently picking one.

This is the honest version of the questionnaire the vendor skill opens with.
The difference is what you ask for: not "what is your Buy Box win rate", which
the API can answer, but "what is your landed unit cost", which it cannot.

## A worked shape

For one SKU, at a candidate price:

```
  Selling price                     P
- Referral fee                      fee estimate at P
- Fulfillment fee                   fee estimate at P
- Storage per unit                  seller figure
- Cost of goods                     seller figure
- Returns allowance                 return rate x per-unit loss
- Advertising allocation            seller figure
= Contribution per unit
```

Break-even is the P where contribution reaches zero. Floor is the P where
contribution reaches the seller's minimum. Solve by evaluating fees at two or
three candidate prices and interpolating, because the referral fee moves with
P and a single evaluation will be slightly wrong.

## Ceilings are real too

A ceiling gets less attention than a floor and causes a different failure. Set
one, for three reasons.

- Amazon's fair pricing policy can suppress or deactivate a listing priced far
  above the market. A repricer with no ceiling that follows a competitor's
  error upward can walk a listing into that.
- The Featured Offer can be suppressed entirely when no offer is priced
  competitively, so an unbounded upward move can cost the Buy Box for
  everyone on the ASIN, including you.
- A price that looks like an error erodes trust even when it converts.

## What to check before trusting a floor

- Fees were estimated at the candidate price, not the current one.
- Fulfillment channel matches reality. An FBA fee estimate on a SKU you ship
  yourself is meaningless.
- Merchant-fulfilled floors account for shipping cost, since the buyer compares
  landed price.
- The seller's cost figure is landed cost, not invoice cost.
- Any figure you assumed rather than received is labelled as an assumption in
  the output.

---

**Provenance:** fee behaviour and the ability to estimate fees for an unset
price come from Amazon's Product Fees API documentation, consulted 2026-09-08.
Cost, storage, returns, and advertising inputs are seller-supplied by
definition. The arithmetic here is standard contribution analysis, not an
Amazon-published formula.
