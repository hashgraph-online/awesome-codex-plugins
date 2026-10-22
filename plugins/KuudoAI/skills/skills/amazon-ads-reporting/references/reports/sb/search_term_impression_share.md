# Sponsored Brands Search Term Impression Share partial mapping

*Partial replacement for v3 Sponsored_Brands_Search_Term_Impression_Share_report — 17 of 19 columns reproducible*

## Summary

This template is a PARTIAL replacement for the v3 Sponsored Brands Search Term Impression Share report on the Amazon Ads API v1 cross-product reporting endpoint.

**CRITICAL: 2 of 19 v3 columns — 'Search Term Impression Rank' and 'Search Term Impression Share' — have NO v1 equivalent and CANNOT be obtained from this endpoint. The remaining 17 columns map cleanly. To recover the missing rank/share columns, use Amazon Marketing Stream's 'sb-search-term-impression-share' dataset or the legacy v2 SB reporting endpoint.**

The 20-field payload was validated against the packaged v1 catalog: zero unknown fields, zero missing required, zero incompatible pairs.

Why per-search-term rank and share are missing

The v1 catalog has metric.impressionShare and metric.impressionShareRank, and their compatibility flags say they CAN coexist with searchTerm.value. But the canonical metric descriptions are explicit: 'The percentage share of all your impressions compared to all other advertisers' and 'The numeric rank of your account-wide impression share compared to all other advertisers'. These are ACCOUNT-WIDE aggregates, not per-search-term competitive metrics. Including them in a search-term-grain report produces the same constant value on every row — which is not what the v3 'Search Term Impression Rank/Share' columns measure.

Validator probes for the per-search-term metrics confirm: metric.searchTermImpressionRank, metric.searchTermImpressionShare, metric.searchTermImpressionShareRank, and metric.searchTermRank are all UNKNOWN to the v1 catalog. The catalog suggests the account-wide replacements but warns indirectly via the description text.

Recommended recovery paths

-   Amazon Marketing Stream — 'sb-search-term-impression-share' dataset. Real-time streaming, indexed per search term per campaign. Closest functional equivalent.

-   Legacy v2 SB Reporting endpoint — sb/searchTerm reportType continues to expose searchTermImpressionRank and searchTermImpressionShare for SB campaigns. Slower-moving than v1's catalog improvements but still supported as of catalog parse 2026-04-18.

-   If neither is available: drop the rank/share columns and surface only the 17 reproducible columns. The use case (find low-rank search terms to bid up) can be approximated downstream by joining searchTerm.value impressions against historical maxima per campaign.

Field list (grouped by role) — partial replacement only

**Time dimension (exactly one required)**

- `date.value`

**Level-of-detail dimensions**

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
- `target.value`
>
- `target.matchType`
>
- `searchTerm.value`

**Required supporting field**

- `budgetCurrency.value`

**Delivery & conversion metrics**

- `metric.impressions`
>
- `metric.clicks`
>
- `metric.ctr`
>
- `metric.cpc`
>
- `metric.totalCost`
>
- `metric.sales`
>
- `metric.purchases`
>
- `metric.purchaseRateOverClicks`
>
- `metric.salesFromClicks`
>
- `metric.purchasesFromClicks`
>
- `metric.roasFromClicks`

**Filter (limits the report to SB)**

- `adProduct.value = SPONSORED_BRANDS`

## v3 → v1 field mapping

| **v3 Column (Sponsored_Brands_Search_Term_Impression_Share)** | **v1 field_id**                                        | **Role**         | **Notes**                                                                                                                                                                                                                                                                                                                                                                    |
|---------------------------------------------------------------|--------------------------------------------------------|------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Date                                                          | date.value                                             | Time dimension   | Required time dimension.                                                                                                                                                                                                                                                                                                                                                     |
| Customer Search Term                                          | searchTerm.value                                       | Dimension        | Direct equivalent. Primary Key in v1.                                                                                                                                                                                                                                                                                                                                        |
| Search Term Impression Rank                                   | (NOT REPRODUCIBLE in v1)                               | —                | v1 has no per-search-term impression rank. Validator-confirmed unknown for metric.searchTermImpressionRank. The closest v1 metric is metric.impressionShareRank, but its description explicitly says 'account-wide rank', NOT per-search-term. Use Marketing Stream's sb-search-term-impression-share dataset or the legacy v2 SB reporting endpoint to recover this column. |
| Search Term Impression Share                                  | (NOT REPRODUCIBLE in v1)                               | —                | Same as the rank — v1 only has account-wide metric.impressionShare. Validator-confirmed unknown for metric.searchTermImpressionShare. Same recovery path as the rank column.                                                                                                                                                                                                 |
| Targeting                                                     | target.value                                           | Dimension        | The keyword expression.                                                                                                                                                                                                                                                                                                                                                      |
| Match Type                                                    | target.matchType                                       | Dimension        | BROAD / PHRASE / EXACT.                                                                                                                                                                                                                                                                                                                                                      |
| Campaign Name                                                 | campaign.name                                          | Dimension        | Pair with campaign.id.                                                                                                                                                                                                                                                                                                                                                       |
| —                                                             | campaign.id                                            | Dimension        | Stable join key.                                                                                                                                                                                                                                                                                                                                                             |
| Ad Group Name                                                 | adGroup.name                                           | Dimension        | Pair with adGroup.id.                                                                                                                                                                                                                                                                                                                                                        |
| —                                                             | adGroup.id                                             | Dimension        | Stable join key.                                                                                                                                                                                                                                                                                                                                                             |
| Currency                                                      | campaign.currencyCode                                  | Dimension        | Pair with budgetCurrency.value.                                                                                                                                                                                                                                                                                                                                              |
| —                                                             | budgetCurrency.value                                   | Required support | v1 minimal-baseline supporting field.                                                                                                                                                                                                                                                                                                                                        |
| Clicks                                                        | metric.clicks                                          | Metric           | Direct.                                                                                                                                                                                                                                                                                                                                                                      |
| Impressions                                                   | metric.impressions                                     | Metric           | Direct.                                                                                                                                                                                                                                                                                                                                                                      |
| Click-Thru Rate (CTR)                                         | metric.ctr                                             | Metric           | Direct.                                                                                                                                                                                                                                                                                                                                                                      |
| Spend                                                         | metric.totalCost                                       | Metric           | v1 renames 'spend' to totalCost.                                                                                                                                                                                                                                                                                                                                             |
| Cost Per Click (CPC)                                          | metric.cpc                                             | Metric           | Direct.                                                                                                                                                                                                                                                                                                                                                                      |
| 14 Day Total Orders (#)                                       | metric.purchases                                       | Metric           | Equivalent — orders → purchases.                                                                                                                                                                                                                                                                                                                                             |
| 14 Day Total Sales                                            | metric.sales                                           | Metric           | Direct.                                                                                                                                                                                                                                                                                                                                                                      |
| Total ACOS - (Click)                                          | (derive client-side)                                   | Derived          | totalCost / NULLIF(salesFromClicks, 0).                                                                                                                                                                                                                                                                                                                                      |
| Total ROAS - (Click)                                          | metric.roasFromClicks                                  | Metric           | Direct.                                                                                                                                                                                                                                                                                                                                                                      |
| 14 Day Conversion Rate                                        | metric.purchaseRateOverClicks (or metric.purchaseRate) | Metric           | Both included so the warehouse can pick by definition.                                                                                                                                                                                                                                                                                                                       |

*Red rows highlight columns NOT REPRODUCIBLE in v1. Yellow rows are derived or definition-dependent.*

## Critical differences from the v3 report

| **Change**                                                        | **What it means for the request**                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
|-------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| TWO v3 COLUMNS ARE NOT REPRODUCIBLE in v1                         | 'Search Term Impression Rank' and 'Search Term Impression Share' have no v1 equivalent. The v1 catalog has metric.impressionShare and metric.impressionShareRank, but their canonical descriptions explicitly say 'account-wide' — they are NOT per-search-term metrics. Validator-confirmed unknown for metric.searchTermImpressionRank, metric.searchTermImpressionShare, metric.searchTermImpressionShareRank. To recover these two columns, use Amazon Marketing Stream's 'sb-search-term-impression-share' dataset (real-time stream) or the legacy v2 SB reporting endpoint. |
| The other 17 v3 columns ARE reproducible at the search-term grain | All delivery (Clicks, Impressions, CTR, Spend, CPC), all conversion (Sales/Orders + click-only variants, Conversion Rate, ROAS-Click, ACOS-Click derived) map cleanly. The result is functionally equivalent to v3 minus the rank/share columns.                                                                                                                                                                                                                                                                                                                                   |
| Filter on adProduct.value = SPONSORED_BRANDS                      | Same as the SB Keyword and SB Search Term reports.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| No metric.acos field                                              | Compute totalCost / NULLIF(salesFromClicks, 0) for the click-only ACOS column. v3 only carries the click-attributed ACOS variant, so all-attribution ACOS isn't needed unless you extend the report.                                                                                                                                                                                                                                                                                                                                                                               |
| No 'conversion rate' field — choose by definition                 | metric.purchaseRateOverClicks for orders/clicks (typical SB UI default); metric.purchaseRate for purchases/impressions. Both included.                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| Attribution window leaves the field name                          | v3's '14 Day' prefix is gone; window is set on the report request.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |

## Operational notes

-   If you need a complete replacement and Marketing Stream is available, recommend that the user set up the sb-search-term-impression-share subscription; the v1 partial report can then complement it with longer-window aggregates. Creating the subscription is a write this skill does not perform.


-   Conversion rate definition: metric.purchaseRateOverClicks for orders/clicks (typical SB UI default); metric.purchaseRate for purchases/impressions.
