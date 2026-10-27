# Sponsored Brands Search Term mapping

*Equivalent to v3 Sponsored_Brands_Search_term_report — 27 v3 columns mapped to v1 fields*

## Summary

This template replicates the v3 Sponsored Brands Search Term report on the Amazon Ads API v1 cross-product reporting endpoint (CreateReport). 26 of 27 v3 columns map cleanly to v1 fields; only ACOS variants are derived client-side. Both attribution layers (all-attribution and click-only) are produced in the same row via paired metric variants — no second report needed.

The 29-field payload was validated against the packaged v1 catalog: zero unknown fields, zero missing required, zero incompatible pairs.

## Field list (grouped by role)

**Time dimension (exactly one required)**

- `date.value`

**Level-of-detail dimensions**

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
- `campaign.costType`
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
- `metric.vcpm`
>
- `metric.totalCost`

**All-attribution conversion (14-day)**

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

**Click-only attribution variants**

- `metric.salesFromClicks`
>
- `metric.purchasesFromClicks`
>
- `metric.unitsSoldFromClicks`
>
- `metric.roasFromClicks`

**Filter (limits the report to SB)**

- `adProduct.value = SPONSORED_BRANDS`

## v3 → v1 field mapping

| **v3 Column (Sponsored_Brands_Search_term)** | **v1 field_id**                                        | **Role**         | **Notes**                                                                                                                                            |
|----------------------------------------------|--------------------------------------------------------|------------------|------------------------------------------------------------------------------------------------------------------------------------------------------|
| Date                                         | date.value                                             | Time dimension   | Required time dimension.                                                                                                                             |
| Portfolio name                               | portfolio.name                                         | Dimension        | Pair with portfolio.portfolioId.                                                                                                                     |
| —                                            | portfolio.portfolioId                                  | Dimension        | Stable join key.                                                                                                                                     |
| Currency                                     | campaign.currencyCode                                  | Dimension        | Pair with budgetCurrency.value.                                                                                                                      |
| Campaign Name                                | campaign.name                                          | Dimension        | Pair with campaign.id.                                                                                                                               |
| —                                            | campaign.id                                            | Dimension        | Stable join key.                                                                                                                                     |
| Ad Group Name                                | adGroup.name                                           | Dimension        | Pair with adGroup.id.                                                                                                                                |
| —                                            | adGroup.id                                             | Dimension        | Stable join key.                                                                                                                                     |
| Targeting                                    | target.value                                           | Dimension        | The keyword expression.                                                                                                                              |
| Match Type                                   | target.matchType                                       | Dimension        | BROAD / PHRASE / EXACT for SB keywords.                                                                                                              |
| Customer Search Term                         | searchTerm.value                                       | Dimension        | Direct equivalent — the search term used by the customer. Primary Key in v1.                                                                         |
| Cost type                                    | campaign.costType                                      | Dimension        | CPC / CPM / vCPM. Native dimension in v1.                                                                                                            |
| —                                            | budgetCurrency.value                                   | Required support | v1 minimal-baseline supporting field for currency-denominated metrics.                                                                               |
| Impressions                                  | metric.impressions                                     | Metric           | Direct.                                                                                                                                              |
| Viewable Impressions                         | metric.viewableImpressions                             | Metric           | Direct.                                                                                                                                              |
| Clicks                                       | metric.clicks                                          | Metric           | Direct.                                                                                                                                              |
| Click-Thru Rate (CTR)                        | metric.ctr                                             | Metric           | Direct.                                                                                                                                              |
| Spend                                        | metric.totalCost                                       | Metric           | v1 renames 'spend' to totalCost.                                                                                                                     |
| Cost Per Click (CPC)                         | metric.cpc                                             | Metric           | Direct.                                                                                                                                              |
| Cost per 1,000 viewable impressions (VCPM)   | metric.vcpm                                            | Metric           | Direct.                                                                                                                                              |
| Total ACOS                                   | (derive client-side)                                   | Derived          | totalCost / NULLIF(sales, 0) or 1 / roas.                                                                                                            |
| Total ROAS                                   | metric.roas                                            | Metric           | Direct.                                                                                                                                              |
| 14 Day Total Sales                           | metric.sales                                           | Metric           | 14-day window is set on the report request.                                                                                                          |
| 14 Day Total Orders (#)                      | metric.purchases                                       | Metric           | Equivalent — orders → purchases.                                                                                                                     |
| 14 Day Total Units (#)                       | metric.unitsSold                                       | Metric           | Direct.                                                                                                                                              |
| 14 Day Conversion Rate                       | metric.purchaseRateOverClicks (or metric.purchaseRate) | Metric           | purchaseRateOverClicks = purchases/clicks (typical SB UI definition); purchaseRate = purchases/impressions. Both included so the warehouse can pick. |
| Total ACOS - (Click)                         | (derive client-side)                                   | Derived          | totalCost / NULLIF(salesFromClicks, 0).                                                                                                              |
| Total ROAS - (Click)                         | metric.roasFromClicks                                  | Metric           | Direct.                                                                                                                                              |
| 14 Day Total Sales - (Click)                 | metric.salesFromClicks                                 | Metric           | Direct.                                                                                                                                              |
| 14 Day Total Orders (#) - (Click)            | metric.purchasesFromClicks                             | Metric           | Direct.                                                                                                                                              |
| 14 Day Total Units (#) - (Click)             | metric.unitsSoldFromClicks                             | Metric           | Direct.                                                                                                                                              |

*Yellow rows highlight columns derived client-side or with multiple valid mappings.*

## Critical differences from the v3 report

| **Change**                                                     | **What it means for the request**                                                                                                                                             |
|----------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Filter on adProduct.value = SPONSORED_BRANDS                   | The v1 endpoint is shared across all ad products; the filter is the only thing that scopes results to Sponsored Brands.                                                       |
| 'Customer Search Term' is searchTerm.value                     | Direct one-to-one mapping. searchTerm.value is a Primary Key dimension in v1 — pivots cleanly with target.value to compare what you targeted vs what shoppers actually typed. |
| No metric.acos field — applies to BOTH all-attr and click-only | Compute totalCost / NULLIF(sales, 0) for the all-attribution ACOS column, and totalCost / NULLIF(salesFromClicks, 0) for the '- (Click)' ACOS variant.                        |
| No 'conversion rate' field — choose by definition              | metric.purchaseRateOverClicks (purchases/clicks) matches the typical SB UI definition; metric.purchaseRate is purchases/impressions. Both included.                           |
| Click-only attribution is the \*FromClicks family              | v3's '- (Click)' suffix maps to v1's \*FromClicks variants: salesFromClicks, purchasesFromClicks, unitsSoldFromClicks, roasFromClicks.                                        |
| Attribution windows leave the field name                       | v3's '14 Day' prefix is gone; the 14-day window is set on the report request itself.                                                                                          |
| 'Spend' → metric.totalCost                                     | Renamed across all ad products in v1.                                                                                                                                         |

## Operational notes



-   Conversion rate: SB UIs typically use orders/clicks → metric.purchaseRateOverClicks. Drop metric.purchaseRate if you don't need the impressions-denominated alternative.

-   Derivations to materialize in the warehouse: acos = totalCost / NULLIF(sales, 0); acosClickOnly = totalCost / NULLIF(salesFromClicks, 0). Persist the raw inputs alongside the views.
