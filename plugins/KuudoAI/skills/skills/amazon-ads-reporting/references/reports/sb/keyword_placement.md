# Sponsored Brands Keyword Placement mapping

*Equivalent to v3 Sponsored_Brands_Keyword_Placement_report — 25 v3 columns mapped to v1 fields*

## Summary

This template replicates the v3 Sponsored Brands Keyword Placement report on the Amazon Ads API v1 cross-product reporting endpoint (CreateReport). Of the 25 v3 columns, 22 map cleanly to v1 fields and 2 are derived client-side (ACOS and % of units new-to-brand). One v3 column ('14 Day Conversion Rate') has two valid v1 mappings depending on definition; both are included so the warehouse can pick.

**This is the first SB report in the series that does NOT require a supplemental Top-of-search Impression Share query — that metric isn't on the v3 report, and the placementClassification.value dimension already exposes top-of-search performance directly (filter or pivot the result on placementClassification.value = TOP_OF_SEARCH).**

The 26-field payload was validated against the packaged v1 catalog: zero unknown fields, zero missing required, zero incompatible pairs.

Single-report architecture

Unlike the regular SB Keyword report and the SP Targeting report, this template is a single CreateReport call. metric.topOfSearchImpressionShare isn't requested here, so the adGroup-incompatibility constraint that forced two-report architectures elsewhere doesn't apply. Submit one report and consume.

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
- `target.value`
>
- `target.matchType`
>
- `placementClassification.value`

**Required supporting field**

- `budgetCurrency.value`

**Delivery metrics**

- `metric.impressions`
>
- `metric.clicks`
>
- `metric.ctr`
>
- `metric.cpc`
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

**New-to-brand**

- `metric.newToBrandPurchases`
>
- `metric.newToBrandSales`
>
- `metric.newToBrandUnitsSold`
>
- `metric.percentOfPurchasesNewToBrand`
>
- `metric.percentOfSalesNewToBrand`
>
- `metric.newToBrandPurchaseRate`

**Filter (limits the report to SB)**

- `adProduct.value = SPONSORED_BRANDS`

## v3 → v1 field mapping

| **v3 Column (Sponsored_Brands_Keyword_Placement)** | **v1 field_id**                                        | **Role**         | **Notes**                                                                                                                                                                                                                                                                                 |
|----------------------------------------------------|--------------------------------------------------------|------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Date                                               | date.value                                             | Time dimension   | Required time dimension.                                                                                                                                                                                                                                                                  |
| Portfolio name                                     | portfolio.name                                         | Dimension        | Pair with portfolio.portfolioId.                                                                                                                                                                                                                                                          |
| —                                                  | portfolio.portfolioId                                  | Dimension        | Stable join key.                                                                                                                                                                                                                                                                          |
| Currency                                           | campaign.currencyCode                                  | Dimension        | Pair with budgetCurrency.value.                                                                                                                                                                                                                                                           |
| Campaign Name                                      | campaign.name                                          | Dimension        | Pair with campaign.id.                                                                                                                                                                                                                                                                    |
| —                                                  | campaign.id                                            | Dimension        | Stable join key.                                                                                                                                                                                                                                                                          |
| Targeting                                          | target.value                                           | Dimension        | The keyword expression.                                                                                                                                                                                                                                                                   |
| Match Type                                         | target.matchType                                       | Dimension        | BROAD / PHRASE / EXACT for SB keywords.                                                                                                                                                                                                                                                   |
| Placement Type                                     | placementClassification.value                          | Dimension        | Direct equivalent — classifies placements as TOP_OF_SEARCH, DETAIL_PAGE, OTHER, etc. The 'Primary Key' tag in v1 catalog confirms this is the canonical placement-type dimension. Note: not to be confused with placement.name (specific placement) or placement.size (pixel dimensions). |
| —                                                  | budgetCurrency.value                                   | Required support | v1 minimal-baseline supporting field for currency-denominated metrics.                                                                                                                                                                                                                    |
| Impressions                                        | metric.impressions                                     | Metric           | Direct.                                                                                                                                                                                                                                                                                   |
| Clicks                                             | metric.clicks                                          | Metric           | Direct.                                                                                                                                                                                                                                                                                   |
| Click-Thru Rate (CTR)                              | metric.ctr                                             | Metric           | Direct.                                                                                                                                                                                                                                                                                   |
| Cost Per Click (CPC)                               | metric.cpc                                             | Metric           | Direct.                                                                                                                                                                                                                                                                                   |
| Spend                                              | metric.totalCost                                       | Metric           | v1 renames 'spend' to totalCost across all ad products.                                                                                                                                                                                                                                   |
| Total Advertising Cost of Sales (ACOS)             | (derive client-side)                                   | Derived          | v1 has no metric.acos. Compute as totalCost / NULLIF(sales, 0) or 1 / roas.                                                                                                                                                                                                               |
| Total Return on Advertising Spend (ROAS)           | metric.roas                                            | Metric           | Direct.                                                                                                                                                                                                                                                                                   |
| 14 Day Total Sales                                 | metric.sales                                           | Metric           | 14-day window is set on the report request, not in the field name.                                                                                                                                                                                                                        |
| 14 Day Total Orders (#)                            | metric.purchases                                       | Metric           | Equivalent — orders → purchases.                                                                                                                                                                                                                                                          |
| 14 Day Total Units (#)                             | metric.unitsSold                                       | Metric           | Direct.                                                                                                                                                                                                                                                                                   |
| 14 Day Conversion Rate                             | metric.purchaseRateOverClicks (or metric.purchaseRate) | Metric           | v1 has no 'conversionRate' field. purchaseRateOverClicks = purchases/clicks (typical SB UI definition); purchaseRate = purchases/impressions. Both included so the warehouse can pick.                                                                                                    |
| 14 Day New-to-brand Orders (#)                     | metric.newToBrandPurchases                             | Metric           | Direct.                                                                                                                                                                                                                                                                                   |
| 14 Day % of Orders New-to-brand                    | metric.percentOfPurchasesNewToBrand                    | Metric           | Direct.                                                                                                                                                                                                                                                                                   |
| 14 Day New-to-brand Sales                          | metric.newToBrandSales                                 | Metric           | Direct.                                                                                                                                                                                                                                                                                   |
| 14 Day % of Sales New-to-brand                     | metric.percentOfSalesNewToBrand                        | Metric           | Direct.                                                                                                                                                                                                                                                                                   |
| 14 Day New-to-brand Units (#)                      | metric.newToBrandUnitsSold                             | Metric           | Direct.                                                                                                                                                                                                                                                                                   |
| 14 Day % of Units New-to-brand                     | (derive client-side)                                   | Derived          | v1 has no metric.percentOfUnitsNewToBrand (validator-confirmed unknown). Compute as newToBrandUnitsSold / NULLIF(unitsSold, 0).                                                                                                                                                           |
| 14 Day New-to-brand Order Rate                     | metric.newToBrandPurchaseRate                          | Metric           | Direct — newToBrandPurchases / impressions.                                                                                                                                                                                                                                               |

*Yellow rows highlight columns that don't have a clean one-to-one v1 mapping (derived client-side or definition-dependent).*

## Critical differences from the v3 report

| **Change**                                                            | **What it means for the request**                                                                                                                                                                                                                                                                                                                         |
|-----------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Filter on adProduct.value = SPONSORED_BRANDS                          | Same as the SB Keyword report — the v1 endpoint is shared across all ad products, so the filter is the only thing that scopes results to Sponsored Brands. Using SPONSORED_PRODUCTS will silently return SP data.                                                                                                                                         |
| 'Placement Type' is placementClassification.value, not placement.name | The v1 catalog has three placement-related dimensions: placement.name (the specific placement), placement.size (pixel dimensions), and placementClassification.value (TOP_OF_SEARCH / DETAIL_PAGE / OTHER classifications). The v3 'Placement Type' column matches the classification dimension, which is also tagged as a Primary Key in the v1 catalog. |
| No supplemental TOS impression share report is needed                 | Unlike the regular SB Keyword report (and the SP Targeting report), this v3 report does NOT include 'Top-of-search Impression Share'. The placement dimension already exposes top-of-search performance directly — filter or pivot on placementClassification.value = TOP_OF_SEARCH to recover that view. Single-report architecture; no two-step join.   |
| No metric.acos field                                                  | Validator rejects metric.acos. Compute totalCost / NULLIF(sales, 0) or 1 / roas in the warehouse.                                                                                                                                                                                                                                                         |
| No 'conversion rate' field — choose by definition                     | Same as the SP Targeting and SB Keyword reports. metric.purchaseRateOverClicks (purchases/clicks) matches the typical SB UI definition; metric.purchaseRate is purchases/impressions. Both included so the warehouse can pick.                                                                                                                            |
| No metric.percentOfUnitsNewToBrand field                              | v1 exposes the % for sales and orders, but not units. Derive: percentOfUnitsNewToBrand = newToBrandUnitsSold / NULLIF(unitsSold, 0).                                                                                                                                                                                                                      |
| Attribution windows leave the field name                              | v3's '14 Day' prefix on Sales/Orders/Units/Conversion Rate/NTB-\* is gone. The 14-day window is set on the report request itself; the fields are window-agnostic.                                                                                                                                                                                         |
| 'Spend' → metric.totalCost                                            | Renamed across all ad products in v1.                                                                                                                                                                                                                                                                                                                     |

## Operational notes



-   Conversion rate: SB UIs typically use orders/clicks → metric.purchaseRateOverClicks. Drop metric.purchaseRate if you don't need the impressions-denominated alternative.

-   Derivations to materialize in the warehouse: acos = totalCost / NULLIF(sales, 0); percentOfUnitsNewToBrand = newToBrandUnitsSold / NULLIF(unitsSold, 0). Persist the raw inputs alongside the views.

-   Reusing this template: this report is essentially a slim version of the SB Keyword report with placementClassification.value added and the video / viewable / click-only / brand-engagement metric blocks dropped. If you need to pivot to TOP_OF_SEARCH performance only, filter the result on placementClassification.value = TOP_OF_SEARCH.
