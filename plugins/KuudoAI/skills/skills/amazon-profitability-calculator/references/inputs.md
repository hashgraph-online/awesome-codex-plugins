# Attribute matrix and data sourcing

Every attribute the model needs, what it means, and whether the `amazon_sp` or
`amazon_ads` MCP server can supply it. Read this when deciding what to ask the user
for, or when explaining why a number could not be sourced.

Source tiers used throughout:

| Tier | Meaning |
| --- | --- |
| **SP** | Retrievable per ASIN/SKU from SP-API |
| **ADS** | Retrievable from the Amazon Ads API |
| **SELLER** | No API knows this. Must be supplied, or read from your own store (Openbridge / agent-flow / a COGS table) |
| **DERIVED** | Computed by the calculator from other inputs |
| **GAP** | Neither API exposes it cleanly; needs inference, a published table, or a user toggle |

---

## 1. The headline finding

The calculator's hardest problem — mapping a product to Amazon's referral-fee
category and then to the right FBA size-tier table — **does not have to be solved
at all when an ASIN exists.**

`fees_getMyFeesEstimateForASIN` accepts an arbitrary `PriceToEstimateFees.ListingPrice`
and returns Amazon's own itemised fee estimate at that price. That means:

- No referral-fee category mapping needed (Amazon applies its own band logic).
- No FBA size-tier calculation needed (Amazon applies its own tier + billable weight).
- No fee-table maintenance, no staleness, no per-marketplace rate cards.
- Break-even and target-margin prices can be **solved by probing the API at candidate
  prices**, which is exactly what the tiered referral bands require.

The rate limit is the constraint: `getMyFeesEstimateForASIN` is ~0.5 rps.
`fees_getMyFeesEstimates` takes a batch, which is the one to use for a price sweep
or a whole catalogue.

What SP-API's fee estimate does **not** cover, and therefore still needs modelling or
a user input: storage, inbound placement, low-inventory fee, storage-utilisation and
aged-inventory surcharges, returns processing fee, and the non-CEP surcharge.

---

## 2. Attribute inventory

### 2.1 Context

| Attribute | Unit | Source | Notes |
| --- | --- | --- | --- |
| Marketplace | enum (10 stores) | SELLER / account context | Maps to SP-API `marketplaceIds`. Drives currency, units (lb/in vs kg/cm), and every fee table. Present the account's available marketplaces rather than defaulting. |
| Currency | ISO 4217 | DERIVED | From marketplace. Cross-market comparison needs an FX rate the APIs do not provide. |
| Reporting basis | order / shipment / payout | SELLER | Not a Clarisix field, but it determines which SP-API source is authoritative. Worth making explicit. |

### 2.2 Product

| Attribute | Unit | Source | Notes |
| --- | --- | --- | --- |
| ASIN / seller SKU | id | SELLER | The key that unlocks every SP tier below. Absent it, the whole model drops to manual entry. |
| Amazon referral-fee category | enum (~35) | **GAP** (avoidable) | `catalog-items-2020-12-01_getCatalogItem` returns browse-node `classifications`, `productTypes` and `salesRanks` — **none of which is the referral-fee category**. There is no API that returns it. Avoid needing it by using the fees estimate (§1). Only required for pre-launch/no-ASIN mode. |
| Selling price | currency | SP | `listings_getListingsItem` (your own price), `pricing_getItemOffers` (buy-box/competitive), or average selling price from the Sales & Traffic report. |
| VAT rate | % | SELLER | Derivable from actuals — EU settlement rows carry tax columns — but not from a hypothetical price. Treat as an input with a per-marketplace default. |
| COGS per unit (landed) | currency | SELLER | Amazon has no visibility. This is the single most important number in the model and the one no API will ever give you. |

### 2.3 Package

| Attribute | Unit | Source | Notes |
| --- | --- | --- | --- |
| Packaged weight | lb / kg | SP (caveat) | `getCatalogItem` `dimensions` often returns **item** dimensions, not packaged, and is frequently missing or wrong on third-party-created listings. |
| Length / Width / Height | in / cm | SP (caveat) | Same caveat. |
| Size tier | enum | SP | The FBA Fee Preview report carries the resolved size tier directly, which is more trustworthy than deriving it from catalogue dimensions. Also implicit in the fees estimate. |
| Inbound shipping to FBA | currency/unit | SELLER | Your freight cost. Not an Amazon number. |
| Inbound placement fee | currency/unit | SP | Retrospective: it appears as a charge line in settlement, which is also the default forward estimate. An inbound plan the user names lists the fee per placement option (`fba-inbound_listPlacementOptions`). Quoting a new split needs a new plan: `fba-inbound_createInboundPlan` writes a draft plan into the seller's account, so it is gated (SKILL.md Guardrails). Otherwise take the user's figure. |

### 2.4 Programme flags

| Attribute | Source | Notes |
| --- | --- | --- |
| Season (Jan–Sep vs Q4 peak) | DERIVED | From the date being modelled. |
| Lithium batteries / dangerous goods | SP (weak) | Listings/catalogue attributes (battery, hazmat, dangerous-goods regulations) exist but are inconsistently populated. Better as a confirmed toggle than an inferred one. |
| Germany outside Central Europe Programme | SELLER | Account-level enrolment. Not exposed as a clean flag. |
| Pan-EU / EFN | SP (partial) | The fees estimate has `OptionalFulfillmentProgram: FBA_EFN` for cross-border, which covers part of this. |

### 2.5 Costs and returns

| Attribute | Unit | Source | Notes |
| --- | --- | --- | --- |
| Advertising per unit | currency/unit | **ADS + SP** | See §3. The single biggest modelling decision in the whole calculator. |
| Return rate | % of units | SP | Returns reports ÷ units shipped over a matched window. Watch the lag: a return lands weeks after the sale, so a naive same-window ratio understates it on a growing SKU. |
| Returns restocked as sellable | % of returns | SP | Directly computable — the FBA customer returns report carries a per-unit disposition (sellable vs defective vs customer-damaged). This is one of the cleanest wins in the whole matrix. |
| Above high-return-rate threshold | boolean | **GAP** | Amazon's per-category thresholds are not in any API. Two workable proxies: (a) detect the returns-processing fee already appearing in settlement/fee data, which is definitive; (b) compare the computed return rate to Amazon's published category threshold. |
| Other costs | currency/unit | SELLER | Overhead allocation, 3PL prep, insurance, software. |

### 2.6 Storage and inventory health

| Attribute | Unit | Source | Notes |
| --- | --- | --- | --- |
| Months in stock (average) | months | SP | From inventory age / ledger data, or as the inverse of turns. |
| Days of supply | days | SP | Restock recommendations carry it; otherwise compute from `fba-inventory_getInventorySummaries` plus sales velocity. Drives the low-inventory fee. |
| Storage utilisation ratio | weeks | SP (partial) | Surfaced in the monthly storage fee data and Seller Central inventory performance. Account-level, not per-SKU, so it allocates rather than attributes. |
| Age when sold | days | SP | From inventory age buckets. Drives the aged-inventory surcharge. |
| Monthly storage fee | currency/unit | SP | The actual charge is in the monthly storage fee report — preferable to modelling cubic feet × rate × season. |

### 2.7 Overrides and solver targets

| Attribute | Source | Notes |
| --- | --- | --- |
| Referral fee % override | SP | Made largely redundant by the fees estimate, which returns the real number. Keep it for FBM and edge cases. |
| FBA fulfilment fee override | SP | Same. Also the documented escape hatch for modelling FBM: enter your own pick-pack-ship cost here. |
| Target margin | SELLER | Pure business input. |

---

## 3. Advertising per unit — the one that needs a decision

The calculator takes a single number ("total ad spend ÷ units sold"). Producing it
correctly requires **both** servers and a stated convention:

**Numerator — ad spend attributable to the ASIN (`amazon_ads`)**
- `allv1_AdsApiv1CreateReport` (v1 cross-product reporting) or `rp_createAsyncReport` (v3).
- Advertised-product-level reports for SP, SB and SD give cost by advertised ASIN.
- SB and SD are not always resolvable to a single ASIN; SB in particular spends at the
  brand level. Any per-ASIN SB allocation is an assumption that should be declared.
- DSP spend, if any, sits outside these reports entirely.

**Denominator — units (`amazon_sp`)**
- Sales & Traffic report gives **total** units ordered by ASIN.
- Ads reports give **ad-attributed** units.

Dividing by *ad-attributed* units gives you cost-per-attributed-unit, which flatters
nothing and is close to ACoS-per-unit. Dividing by *total* units gives the TACOS-style
per-unit ad load — and that is the one that belongs in a P&L, because the ad spend was
incurred to sell the whole quantity, not just the attributed slice.

The calculator's own label ("total ad spend ÷ units sold") implies the TACOS
convention. A skill should compute that by default, show both, and say which it used.
Attribution window also has to be pinned and stated, or the numerator moves under you.

---

## 4. Derived outputs

All computed, none sourced:

| Output | Formula |
| --- | --- |
| Net revenue | Selling price ÷ (1 + VAT rate) |
| Operating profit/unit | Net revenue − Amazon fees − COGS − inbound − advertising − net returns cost − other |
| Operating margin | Operating profit ÷ net revenue |
| ROI on COGS | Operating profit ÷ COGS |
| Amazon take | Total Amazon fees ÷ selling price |
| Net returns cost | (return rate × refunded net revenue) − (return rate × referral refund net of admin fee) + (return rate × processing fee) − (return rate × restock share × COGS) |
| Break-even price | Solve for price where operating profit = 0, **recomputing fees at each candidate price** |
| Price for target margin | Same solve, with profit = target × net revenue |
| Max ad spend at target | Net revenue × (1 − target) − all non-ad costs |

The refund administration fee is 20% of the referral fee, capped at 5 units of the
local currency (52.5 SEK / 20 PLN).

The two solves are why the fees estimate matters so much: referral bands, FBA price
bands and VAT all move with price, so a fixed fee assumption produces a wrong
break-even. Either probe the API across a price sweep (batch endpoint) or model the
bands locally and calibrate against one live estimate.

---

## 5. Summary — what each side owns

**SP-API can supply:** referral fee, FBA fulfilment fee, size tier, current price,
package dimensions (with caveats), storage charges, inventory age, days of supply,
return rate, return dispositions, inbound placement fees, and — via settlement — the
fees Amazon *actually charged*.

**Ads API can supply:** ad spend by advertised ASIN across SP/SB/SD, plus attributed
units and sales.

**Neither can supply:** COGS, inbound freight, VAT rate, other per-unit costs, target
margin. These are the irreducible seller inputs — five fields, and the model cannot
run without them.

**Genuine gaps:** referral-fee category name (avoidable via the fees estimate),
high-return-rate threshold status, CEP enrolment, and cross-market FX.

---

## 6. Implications for a skill

Three distinct modes, which want different code paths:

1. **Pre-launch / no ASIN.** Everything manual. Requires the full fee tables to be
   embedded, which means they go stale and need a verification date. This is the
   expensive mode to build and the one most likely to be wrong six months out.

2. **Live estimate (ASIN exists).** SP-API computes Amazon's side at any candidate
   price; Ads supplies the ad load; the seller supplies five numbers. No fee tables to
   maintain. This is the mode with the best accuracy-to-effort ratio.

3. **Reconciled actuals.** Settlement data gives the fees Amazon actually charged
   rather than estimated, which closes the gap between the model and the P&L. Slowest
   to build, most defensible output.

**Recommendation:** build mode 2 first. Mode 1 is a fee-table maintenance burden
dressed as a feature; mode 3 is a data-pipeline problem more than a calculator problem.

Two things to carry into the skill regardless of mode: report type identifiers should
be validated against Amazon's current Report Type Values documentation rather than
hardcoded from memory, and account/marketplace/profile selection should be presented
as options rather than silently defaulted.
