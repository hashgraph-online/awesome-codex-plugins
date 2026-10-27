# Sponsored Brands Prompts partial mapping

*Partial replacement for v3 Sponsored_Brands_Prompts_report — 25 of 26 columns reproducible at Ad grain*

## Summary

This template is a PARTIAL replacement for the v3 Sponsored Brands Prompts report on the Amazon Ads API v1 cross-product reporting endpoint.

**CRITICAL: The v3 'Prompt details' dimension has NO v1 equivalent. The v1 catalog returns zero hits for 'prompt' or 'rufus' across all categories. Amazon Rufus AI-shopping prompt-level performance has not been added to the v1 reporting catalog as of catalog parse 2026-04-18. The closest reproducible level of detail is Ad (ad.id / ad.name / ad.format).**

The 31-field payload was validated against the packaged v1 catalog: zero unknown fields, zero missing required, zero incompatible pairs. The result reproduces 25 of 26 v3 columns at Ad grain.

Why prompt-level dimensions are missing

The v3 SB Prompts report is part of Amazon's Rufus integration — generative-AI shopping prompts that drive Sponsored Brands placements when shoppers ask Rufus product questions. v3 exposes the prompt text or category as a dimension; v1 does not yet. Validator probes for prompt.value, promptDetails.value, rufusPrompt.value, and similar all return unknown.

This is likely a catalog-completeness gap rather than a deliberate omission — the underlying telemetry exists and v3 surfaces it, but the v1 cross-product reporting catalog has not been extended to cover it. Track Amazon's Ads API release notes for additions to the dimension family.

Recommended recovery paths

-   Continue using the v3 Sponsored Brands Prompts report endpoint until v1 adds prompt dimensions.

-   Hybrid: use this v1 partial template for steady-state Ad-grain Rufus reporting, and run the v3 endpoint at a lower cadence (e.g. weekly) for prompt-level breakdowns.

-   If you only need to know which ads use Rufus prompt creatives vs traditional ads, ad.format may carry a distinguishing format value — verify by inspecting a sample of returned rows.

Field list (grouped by role) — partial replacement only

**Time dimension (exactly one required)**

- `date.value`

**Level-of-detail dimensions (Ad grain — closest to v3 prompt grain)**

- `portfolio.portfolioId`
>
- `portfolio.name`
>
- `campaign.id`
>
- `campaign.name`
>
- `campaign.currencyCode`
>
- `adGroup.id`
>
- `adGroup.name`
>
- `country.code`
>
- `country.name`
>
- `ad.id`
>
- `ad.name`
>
- `ad.format`

**Required supporting field**

- `budgetCurrency.value`

**Delivery metrics**

- `metric.impressions`
>
- `metric.viewableImpressions`
>
- `metric.clicks`
>
- `metric.ctr`
>
- `metric.cpc`
>
- `metric.totalCost`

**All-attribution conversion (7-day)**

- `metric.sales`
>
- `metric.purchases`
>
- `metric.unitsSold`
>
- `metric.purchaseRateOverClicks`
>
- `metric.purchaseRate`
>
- `metric.roas`

**Advertised-SKU vs Other-SKU split**

- `metric.salesPromoted`
>
- `metric.salesHalo`
>
- `metric.purchasesPromoted`
>
- `metric.purchasesHalo`
>
- `metric.unitsSoldPromoted`
>
- `metric.unitsSoldHalo`

**Filter (limits the report to SB)**

- `adProduct.value = SPONSORED_BRANDS`

## v3 → v1 field mapping

| **v3 Column (Sponsored_Brands_Prompts)** | **v1 field_id**                                        | **Role**         | **Notes**                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
|------------------------------------------|--------------------------------------------------------|------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Date                                     | date.value                                             | Time dimension   | Required time dimension.                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| Portfolio name                           | portfolio.name                                         | Dimension        | Pair with portfolio.portfolioId.                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| —                                        | portfolio.portfolioId                                  | Dimension        | Stable join key.                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| Currency                                 | campaign.currencyCode                                  | Dimension        | Pair with budgetCurrency.value.                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| Campaign Name                            | campaign.name                                          | Dimension        | Pair with campaign.id.                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| —                                        | campaign.id                                            | Dimension        | Stable join key.                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| Ad Group Name                            | adGroup.name                                           | Dimension        | Pair with adGroup.id.                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| —                                        | adGroup.id                                             | Dimension        | Stable join key.                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| Country                                  | country.name                                           | Dimension        | Pair with country.code.                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| —                                        | country.code                                           | Dimension        | ISO country code.                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| Ad Name                                  | ad.name                                                | Dimension        | Pair with ad.id.                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| —                                        | ad.id                                                  | Dimension        | Stable join key.                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| —                                        | ad.format                                              | Dimension        | video / image / etc — closest available indicator that an ad is a Rufus prompt creative.                                                                                                                                                                                                                                                                                                                                                                                 |
| Prompt details                           | (NOT REPRODUCIBLE in v1)                               | —                | v1 has NO prompt-level dimension. Validator returns zero hits for 'prompt' or 'rufus' across the entire catalog. The v3 SB Prompts report exposes Amazon Rufus AI-shopping prompt-level performance which has not been added to the v1 reporting catalog as of catalog parse 2026-04-18. The closest available level of detail is Ad (ad.id, ad.name, ad.format) — Rufus-prompt-bearing ads will appear as separate ad rows but the specific prompt text is not exposed. |
| —                                        | budgetCurrency.value                                   | Required support | v1 minimal-baseline supporting field.                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| Impressions                              | metric.impressions                                     | Metric           | Direct.                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| Viewable Impressions                     | metric.viewableImpressions                             | Metric           | Direct.                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| Clicks                                   | metric.clicks                                          | Metric           | Direct.                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| Click-Thru Rate (CTR)                    | metric.ctr                                             | Metric           | Direct.                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| Spend                                    | metric.totalCost                                       | Metric           | v1 renames 'spend' to totalCost.                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| Cost Per Click (CPC)                     | metric.cpc                                             | Metric           | Direct.                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| 7 Day Total Sales                        | metric.sales                                           | Metric           | 7-day window is set on the report request.                                                                                                                                                                                                                                                                                                                                                                                                                               |
| 7 Day Total Orders (#)                   | metric.purchases                                       | Metric           | Equivalent — orders → purchases.                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| 7 Day Total Units (#)                    | metric.unitsSold                                       | Metric           | Direct.                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| 7 Day Conversion Rate                    | metric.purchaseRateOverClicks (or metric.purchaseRate) | Metric           | Both included so the warehouse can pick by definition.                                                                                                                                                                                                                                                                                                                                                                                                                   |
| 7 Day Advertised SKU Orders (#)          | metric.purchasesPromoted                               | Metric           | Promoted = directly advertised SKU.                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| 7 Day Other SKU Orders (#)               | metric.purchasesHalo                                   | Metric           | Halo = other SKUs from the same brand.                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| 7 Day Advertised SKU Units (#)           | metric.unitsSoldPromoted                               | Metric           | Promoted units sold.                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| 7 Day Other SKU Units (#)                | metric.unitsSoldHalo                                   | Metric           | Halo units sold.                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| 7 Day Advertised SKU Sales               | metric.salesPromoted                                   | Metric           | Promoted sales.                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| 7 Day Other SKU Sales                    | metric.salesHalo                                       | Metric           | Halo sales.                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| Total ACOS                               | (derive client-side)                                   | Derived          | totalCost / NULLIF(sales, 0) or 1 / roas.                                                                                                                                                                                                                                                                                                                                                                                                                                |
| Total ROAS                               | metric.roas                                            | Metric           | Direct.                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |

*Red rows highlight columns NOT REPRODUCIBLE in v1. Yellow rows are derived or definition-dependent.*

## Critical differences from the v3 report

| **Change**                                               | **What it means for the request**                                                                                                                                                                                                                                                                                                                                                                                          |
|----------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 'Prompt details' is NOT REPRODUCIBLE in v1               | Zero catalog hits for 'prompt' or 'rufus'. Amazon's v1 reporting catalog has not yet exposed prompt-level dimensions for Sponsored Brands AI-shopping creatives. The closest available level of detail is Ad (ad.id / ad.name / ad.format). Each Rufus-prompt-bearing ad will be a separate row, but the specific prompt text or category is not exposed. To get prompt-level granularity, continue using the v3 endpoint. |
| The other 25 v3 columns ARE reproducible at the Ad grain | All delivery, conversion, and Advertised-SKU/Other-SKU split metrics map cleanly. Rolling up to ad.id gives Ad-level totals across all of an ad's prompt invocations.                                                                                                                                                                                                                                                      |
| Filter on adProduct.value = SPONSORED_BRANDS             | Same as the SB Keyword and SB Search Term reports.                                                                                                                                                                                                                                                                                                                                                                         |
| 7 Day vs 14 Day attribution windows                      | v3 SB Prompts uses a 7-day attribution window (different from most other SB reports, which are 14-day). Set the window correctly on the report request before submitting; v1 fields are window-agnostic.                                                                                                                                                                                                                   |
| No metric.acos field                                     | Compute totalCost / NULLIF(sales, 0).                                                                                                                                                                                                                                                                                                                                                                                      |
| Advertised SKU vs Other SKU mapping                      | v3 'Advertised SKU' = v1 \*Promoted (the directly advertised SKU). v3 'Other SKU' = v1 \*Halo (other highly-relevant SKUs from the same brand).                                                                                                                                                                                                                                                                            |

## Operational notes

-   Attribution window: this v3 report uses a 7-day window (not the SB-typical 14-day). Set the window on the report request explicitly to match.


-   Reusing this template: this is essentially a slim version of the SB Keyword report at Ad grain instead of keyword grain. If you also want Branded Searches and DPV, add metric.brandedSearches and metric.detailPageViews — both are compatible with the Ad grain.
