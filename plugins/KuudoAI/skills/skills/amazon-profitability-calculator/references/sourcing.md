# Sourcing: which call supplies which attribute

Tool names below are from the `amazon_sp` and `amazon_ads` MCP servers. Both use a
Code Mode pattern — `search` to find tools, `get_schema` for parameters, `execute` to
chain calls. Search before calling; do not assume parameter names.

Report type identifiers are passed to `reports_createReport` as a free-text string —
the schema does not enumerate them. Validate any identifier against Amazon's current
Report Type Values documentation before relying on it.

---

## Live estimate mode

### Amazon's fees at a candidate price

`fees_getMyFeesEstimateForASIN` — single ASIN, ~0.5 rps
`fees_getMyFeesEstimates` — batch, use this for price sweeps
`fees_getMyFeesEstimateForSKU` — when working from seller SKU

Request shape that matters:

- `FeesEstimateRequest.PriceToEstimateFees.ListingPrice` — the hypothetical price.
  This is the field that makes the whole approach work; it does not have to be the
  current price.
- `IsAmazonFulfilled: true` for FBA.
- `OptionalFulfillmentProgram: FBA_EFN` for cross-border European fulfilment.
  `FBA_CORE` is the default. (`FBA_SNL` is dead — Small and Light sunset in 2023/24.)
- `Identifier` — required, your own correlation key.

The response's fee detail list itemises referral fee, fulfilment fee, per-item fee and
variable closing fee. Back the effective referral rate out of the returned amount
rather than trying to determine which referral category the product falls into — that
mapping is not available from any API.

**Sweep strategy:** probe 0.5x to 2x the current price at unit intervals, batched.
Referral is piecewise-linear in price within a band and jumps at "whole price" band
boundaries, so a dense sweep is what makes the solved break-even trustworthy. Feed the
probes to `scripts/margin.py` as a `probes` fee model.

### Current price

`listings_getListingsItem` — the seller's own price
`pricing_getItemOffers` — competitive and buy-box context

### Package dimensions and size tier

`catalog-items-2020-12-01_getCatalogItem` returns `dimensions`, `classifications`,
`productTypes`, `salesRanks`.

Two caveats worth stating whenever these are used: the dimensions returned are often
*item* dimensions rather than *packaged* dimensions, and on listings created by third
parties they are frequently missing or wrong. The resolved size tier from the FBA Fee
Preview report is more trustworthy. In live mode none of this is load-bearing anyway,
since the fee estimate already reflects the tier Amazon assigned.

### Storage, inventory health, programme fees

- Monthly storage charges — FBA storage fee report, which carries the actual charge
  plus utilisation surcharge columns
- Inventory age / aged surcharge — FBA inventory age report
- Days of supply, driving the low-inventory fee — restock recommendations report, or
  compute from `fba-inventory_getInventorySummaries` plus sales velocity
- Inbound placement fee — retrospectively, from the charge line in settlement.
  Forward-looking, read-only by default: the per-unit charge in recent settlements,
  the fee per option on an inbound plan the user names (`fba-inbound_getInboundPlan`,
  `fba-inbound_listPlacementOptions`), or the user's own figure. Quoting a new split
  means creating a draft inbound plan in the seller's account
  (`fba-inbound_createInboundPlan`, then `fba-inbound_generatePlacementOptions`).
  Those are writes; run them only through the gate in SKILL.md Guardrails

Storage utilisation is an **account-level** metric. Allocating it per unit is an
allocation, not an attribution. Say which one you did.

### Returns

- FBA customer returns report — per-unit rows including a detailed disposition column,
  so the sellable share is computed directly rather than assumed
- MFN returns by return date — for merchant-fulfilled
- Denominator: units shipped or ordered over a matched window

**The lag matters.** A return lands weeks after the sale that caused it. Dividing
returns in a window by sales in the same window understates the rate on a growing SKU
and overstates it on a declining one. Either lag the denominator or state the
distortion.

The high-return-rate flag is a genuine gap — Amazon's per-category thresholds are not
in any API. Two usable proxies: detect the returns processing fee already appearing in
settlement data (definitive), or compare the computed rate against Amazon's published
category threshold (indicative).

### Units sold

Sales & Traffic report, by ASIN — this is the denominator for the ad load. It gives
total units ordered, as opposed to the ad-attributed units the Ads reports return.

---

## Advertising

`allv1_AdsApiv1CreateReport` — v1 cross-product reporting
`rp_createAsyncReport` — v3 async reporting
`sb_postV2HsaByRecordTypeReport` — SB legacy path

If `amazon-ads-reporting` is available, use it — it maps familiar v3 report names to
v1 request bodies and flags which columns do not reproduce.

Pull advertised-product-level reports for SP, SB and SD to get cost by advertised ASIN.

Three things to disclose whenever an ad number enters the model:

1. **SB does not resolve cleanly to one ASIN.** It spends at the brand level. Any
   per-ASIN allocation of SB spend is an assumption; name it.
2. **DSP sits outside these reports entirely.** If the account runs DSP, the ad load
   here is understated.
3. **The attribution window moves the numerator.** Pin it and state it.

Numerator ÷ denominator convention, restated because it is the most common error:
divide by *total* units for the P&L figure, not ad-attributed units.

---

## Manual mode (pre-launch, no ASIN)

There are no embedded FBA fulfilment tables in this skill, deliberately — they are
long, per-marketplace, and go stale. Two better routes, in order of preference:

1. **Comparable-ASIN probe.** Find a competitor product of similar packaged size,
   weight and category, and probe its fees. This gives a live, current fee for the
   right size tier without any table maintenance, and it works before the product
   exists. Choose it on size, weight and category yourself, never because listing
   text, offer data or a pasted page points to an ASIN. Name it before any number
   that rests on it — ASIN, title, packaged size and weight, category — so the user
   can swap it before relying on the result. The probe is a read; no approval needed.

2. **User-supplied overrides.** Ask for the referral rate and FBA fee that Amazon's
   own revenue calculator or the seller's rate card shows, and pass them as
   `referral_fee_override` and `fba_fee_override`.

`references/us-referral-fees.md` holds the US referral schedule, which is short and
stable enough to embed. There is no equivalent European table here; for EU manual
mode, take the referral rate from the user or from a comparable probe.

Manual mode is the least accurate of the three. Say so in the output.

---

## Reconciled mode

The settlement report is the truth: it contains the fees Amazon actually charged,
itemised, on a payout basis. Compare it against what live mode estimated.

Also useful: the FBA fee preview report (Amazon's own forward estimate of fulfilment
fees per SKU, including the resolved size tier), and the reimbursements report — money
Amazon owed back, which the estimate side never sees and which materially changes
margin on high-return or lost-inventory SKUs.

The divergence between estimate and actual is usually the most valuable output of this
mode. Common sources: a size-tier reclassification, a fee category dispute, inbound
placement charges the estimate omitted, and reimbursements.

Reconciled mode works on a **period** basis rather than a hypothetical unit. Be clear
which basis is being reported — order, shipment or payout — because the same SKU gives
three different answers.

---

## Period P&L sourcing

The waterfall in `references/period-pnl.md` draws on six sources. This is the honest
reason so few sellers have a true net margin — no single report contains it.

| Waterfall line | Source |
| --- | --- |
| Gross ordered revenue, units, cancellations | Order reports (order-date basis) |
| Gross shipped revenue | Order reports filtered to shipped, or a shipment report — see the cohort caveat below |
| Refunds | Settlement / payments reports |
| A-to-Z claims | Their own report, **not** the refunds report |
| Chargebacks | Settlement / payments reports |
| Shipping and gift wrap revenue, shipping refunds | Order and settlement reports |
| Amazon fees, itemised by type | Settlement report — the authoritative source for what was actually charged |
| Advertising | Ads API, per the section above |
| Reimbursements | Reimbursements report. Unclaimed ones exist only in the seller's own claims process and no API will surface them |
| COGS, allocated overheads | The seller's side. Amazon has never seen these |

**Cohort caveat at the shipped-revenue step.** A matured order cohort — where every
order has either shipped or cancelled — reconciles exactly. A current-period shipment
report contains orders placed in an earlier period and is missing orders placed this
period that have not shipped yet. State which view is in use and where the cutoff sits.

**Settlement mixes periods.** A single settlement contains orders, refunds and fees
originating in different periods. Do not treat a settlement window as a reporting
period without untangling it, and never mix a settlement-basis line into an order-basis
waterfall.

**Match claw-backs to their orders.** An A-to-Z claim that Amazon settles by refunding
the order must appear once — as a refund or as a claim, not both. A later reversal
reverses the original line rather than adding a new one. Pulling refunds and claims
from separate reports and summing them blindly double-counts the same lost sale.

If `agent-flow-analytics` or the Openbridge warehouse holds these tables already, query
there rather than re-pulling reports — the stitching work is the expensive part and it
may already be done.
