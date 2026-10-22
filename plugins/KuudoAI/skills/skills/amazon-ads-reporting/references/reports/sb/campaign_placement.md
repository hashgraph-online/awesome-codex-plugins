# Sponsored Brands Campaign Placement mapping

*Equivalent to v3 Sponsored_Brands_Campaign_placement_report — 42 v3 columns mapped to v1 fields*

## Summary

This template replicates the v3 Sponsored Brands Campaign Placement report on the Amazon Ads API v1 cross-product reporting endpoint (CreateReport). 39 of 42 v3 columns map cleanly to v1 fields; 3 are derived client-side (ACOS, click-only ACOS, % of units new-to-brand).

The 42-field payload was validated against the packaged v1 catalog: zero unknown fields, zero missing required, zero incompatible pairs.

**Single-report architecture — Top-of-search Impression Share isn't on the v3 report, so no supplemental query is needed. Filter or pivot on placementClassification.value = TOP_OF_SEARCH downstream if you need the top-of-search slice.**

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
- `placementClassification.value`

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
- `metric.vctr`
>
- `metric.cpc`
>
- `metric.vcpm`
>
- `metric.totalCost`

**Video metrics**

- `metric.firstQuartileVideoAd`
>
- `metric.midpointVideoAd`
>
- `metric.thirdQuartileVideoAd`
>
- `metric.completeViewsVideoAd`
>
- `metric.unmutesVideoAd`
>
- `metric.5secondViewsVideoAd`
>
- `metric.5secondViewRateVideoAd`
>
- `metric.completionRateVideoAd`

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

**Brand engagement**

- `metric.brandedSearches`
>
- `metric.detailPageViews`

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

| **v3 Column (Sponsored_Brands_Campaign_placement)** | **v1 field_id**                                        | **Role**                      | **Notes**                                                                                                                                                                                                                                                                                             |
|-----------------------------------------------------|--------------------------------------------------------|-------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Date                                                | date.value                                             | Time dimension                | Required time dimension.                                                                                                                                                                                                                                                                              |
| Portfolio name                                      | portfolio.name                                         | Dimension                     | Pair with portfolio.portfolioId.                                                                                                                                                                                                                                                                      |
| —                                                   | portfolio.portfolioId                                  | Dimension                     | Stable join key.                                                                                                                                                                                                                                                                                      |
| Currency                                            | campaign.currencyCode                                  | Dimension                     | Pair with budgetCurrency.value.                                                                                                                                                                                                                                                                       |
| Campaign Name                                       | campaign.name                                          | Dimension                     | Pair with campaign.id.                                                                                                                                                                                                                                                                                |
| —                                                   | campaign.id                                            | Dimension                     | Stable join key.                                                                                                                                                                                                                                                                                      |
| Cost type                                           | campaign.costType                                      | Dimension                     | CPC / CPM / vCPM. Native dimension in v1.                                                                                                                                                                                                                                                             |
| Placement                                           | placementClassification.value                          | Dimension                     | Direct equivalent — classifies placements as TOP_OF_SEARCH, DETAIL_PAGE, OTHER, etc. Tagged as Primary Key in v1. Note: placement.name (specific placement) and placement.size (pixel dimensions) also exist; placementClassification.value is the right one for the v3 'Placement' column semantics. |
| —                                                   | budgetCurrency.value                                   | Required support              | v1 minimal-baseline supporting field.                                                                                                                                                                                                                                                                 |
| Impressions                                         | metric.impressions                                     | Metric                        | Direct.                                                                                                                                                                                                                                                                                               |
| Viewable Impressions                                | metric.viewableImpressions                             | Metric                        | Direct.                                                                                                                                                                                                                                                                                               |
| Clicks                                              | metric.clicks                                          | Metric                        | Direct.                                                                                                                                                                                                                                                                                               |
| Click-Thru Rate (CTR)                               | metric.ctr                                             | Metric                        | Direct.                                                                                                                                                                                                                                                                                               |
| Spend                                               | metric.totalCost                                       | Metric                        | v1 renames 'spend' to totalCost.                                                                                                                                                                                                                                                                      |
| Cost Per Click (CPC)                                | metric.cpc                                             | Metric                        | Direct.                                                                                                                                                                                                                                                                                               |
| Cost per 1,000 viewable impressions (VCPM)          | metric.vcpm                                            | Metric                        | Direct.                                                                                                                                                                                                                                                                                               |
| Total ACOS                                          | (derive client-side)                                   | Derived                       | totalCost / NULLIF(sales, 0) or 1 / roas.                                                                                                                                                                                                                                                             |
| Total ROAS                                          | metric.roas                                            | Metric                        | Direct.                                                                                                                                                                                                                                                                                               |
| 14 Day Total Sales                                  | metric.sales                                           | Metric                        | 14-day window is set on the report request.                                                                                                                                                                                                                                                           |
| 14 Day Total Orders (#)                             | metric.purchases                                       | Metric                        | Equivalent — orders → purchases.                                                                                                                                                                                                                                                                      |
| 14 Day Total Units (#)                              | metric.unitsSold                                       | Metric                        | Direct.                                                                                                                                                                                                                                                                                               |
| 14 Day Conversion Rate                              | metric.purchaseRateOverClicks (or metric.purchaseRate) | Metric                        | Both included so the warehouse can pick by definition.                                                                                                                                                                                                                                                |
| View-Through Rate (VTR)                             | metric.completionRateVideoAd (closest)                 | Metric — definition-dependent | v1 has no metric.vtr or metric.viewThroughRate. Two candidates: metric.completionRateVideoAd (full play) or metric.5secondViewRateVideoAd (5-second view rate). Pick whichever matches your downstream definition; both are in the request for safety.                                                |
| Click-Through Rate for Views (vCTR)                 | metric.vctr                                            | Metric                        | v1 calls this 'Viewable CTR' — clicks / viewable impressions.                                                                                                                                                                                                                                         |
| Video First Quartile Views                          | metric.firstQuartileVideoAd                            | Metric                        | Direct — 25% played.                                                                                                                                                                                                                                                                                  |
| Video Midpoint Views                                | metric.midpointVideoAd                                 | Metric                        | Direct — 50% played.                                                                                                                                                                                                                                                                                  |
| Video Third Quartile Views                          | metric.thirdQuartileVideoAd                            | Metric                        | Direct — 75% played.                                                                                                                                                                                                                                                                                  |
| Video Complete Views                                | metric.completeViewsVideoAd                            | Metric                        | Direct.                                                                                                                                                                                                                                                                                               |
| Video Unmutes                                       | metric.unmutesVideoAd                                  | Metric                        | Direct.                                                                                                                                                                                                                                                                                               |
| 5 Second Views                                      | metric.5secondViewsVideoAd                             | Metric                        | Direct.                                                                                                                                                                                                                                                                                               |
| 5 Second View Rate                                  | metric.5secondViewRateVideoAd                          | Metric                        | Direct.                                                                                                                                                                                                                                                                                               |
| 14 Day Branded Searches                             | metric.brandedSearches                                 | Metric                        | Direct.                                                                                                                                                                                                                                                                                               |
| 14 Day Detail Page Views (DPV)                      | metric.detailPageViews                                 | Metric                        | Direct.                                                                                                                                                                                                                                                                                               |
| 14 Day New-to-brand Orders (#)                      | metric.newToBrandPurchases                             | Metric                        | Direct.                                                                                                                                                                                                                                                                                               |
| 14 Day % of Orders New-to-brand                     | metric.percentOfPurchasesNewToBrand                    | Metric                        | Direct.                                                                                                                                                                                                                                                                                               |
| 14 Day New-to-brand Sales                           | metric.newToBrandSales                                 | Metric                        | Direct.                                                                                                                                                                                                                                                                                               |
| 14 Day % of Sales New-to-brand                      | metric.percentOfSalesNewToBrand                        | Metric                        | Direct.                                                                                                                                                                                                                                                                                               |
| 14 Day New-to-brand Units (#)                       | metric.newToBrandUnitsSold                             | Metric                        | Direct.                                                                                                                                                                                                                                                                                               |
| 14 Day % of Units New-to-brand                      | (derive client-side)                                   | Derived                       | v1 has no metric.percentOfUnitsNewToBrand. Compute as newToBrandUnitsSold / NULLIF(unitsSold, 0).                                                                                                                                                                                                     |
| 14 Day New-to-brand Order Rate                      | metric.newToBrandPurchaseRate                          | Metric                        | Direct.                                                                                                                                                                                                                                                                                               |
| Total ACOS - (Click)                                | (derive client-side)                                   | Derived                       | totalCost / NULLIF(salesFromClicks, 0).                                                                                                                                                                                                                                                               |
| Total ROAS - (Click)                                | metric.roasFromClicks                                  | Metric                        | Direct.                                                                                                                                                                                                                                                                                               |
| 14 Day Total Sales - (Click)                        | metric.salesFromClicks                                 | Metric                        | Direct.                                                                                                                                                                                                                                                                                               |
| 14 Day Total Orders (#) - (Click)                   | metric.purchasesFromClicks                             | Metric                        | Direct.                                                                                                                                                                                                                                                                                               |
| 14 Day Total Units (#) - (Click)                    | metric.unitsSoldFromClicks                             | Metric                        | Direct.                                                                                                                                                                                                                                                                                               |

*Yellow rows highlight columns derived client-side or with multiple valid mappings.*

## Critical differences from the v3 report

| **Change**                                                              | **What it means for the request**                                                                                                                                                                                                                                                            |
|-------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| This is the SB Keyword report's metric set at coarser dimensional grain | The metric layout is identical to the regular SB Keyword report. The dimensional grain swaps target.value/target.matchType/adGroup.\* (keyword grain) for placementClassification.value (placement grain). Same 14-day window, same NTB suite, same click-only variants, same video metrics. |
| No supplemental TOS impression share report needed                      | Like the SB Keyword Placement report, top-of-search performance is recovered by filtering or pivoting placementClassification.value = TOP_OF_SEARCH downstream. Single-report architecture.                                                                                                  |
| Filter on adProduct.value = SPONSORED_BRANDS                            | The v1 endpoint is shared across all ad products.                                                                                                                                                                                                                                            |
| No metric.acos field — applies to BOTH all-attr and click-only          | Compute totalCost / NULLIF(sales, 0) and totalCost / NULLIF(salesFromClicks, 0).                                                                                                                                                                                                             |
| No 'View-Through Rate' field                                            | Pick metric.completionRateVideoAd or metric.5secondViewRateVideoAd based on your VTR definition. The template includes both for safety.                                                                                                                                                      |
| No metric.percentOfUnitsNewToBrand field                                | Derive: newToBrandUnitsSold / NULLIF(unitsSold, 0).                                                                                                                                                                                                                                          |
| No 'conversion rate' field — choose by definition                       | metric.purchaseRateOverClicks for orders/clicks (typical SB UI default); metric.purchaseRate for purchases/impressions. Both included.                                                                                                                                                       |
| Click-only attribution is the \*FromClicks family                       | v3's '- (Click)' suffix maps to v1's \*FromClicks variants.                                                                                                                                                                                                                                  |
| Attribution windows leave the field name                                | v3's '14 Day' prefix is gone; window is set on the report request.                                                                                                                                                                                                                           |
| 'Spend' → metric.totalCost                                              | Renamed across all ad products in v1.                                                                                                                                                                                                                                                        |
| Cost type is a native dimension                                         | campaign.costType returns CPC / CPM / vCPM.                                                                                                                                                                                                                                                  |

## Operational notes

-   VTR definition: confirm with consumers whether VTR means completion (full play) or 5-second view. The template carries both metric.completionRateVideoAd AND metric.5secondViewRateVideoAd. Drop whichever isn't needed.

-   Conversion rate definition: SB UIs typically use orders/clicks → metric.purchaseRateOverClicks. Drop metric.purchaseRate if you don't need it.


-   Derivations to materialize in the warehouse: acos = totalCost / NULLIF(sales, 0); acosClickOnly = totalCost / NULLIF(salesFromClicks, 0); percentOfUnitsNewToBrand = newToBrandUnitsSold / NULLIF(unitsSold, 0). Persist the raw inputs alongside the views.

-   Reusing this template: the field set is functionally a superset of the SB Keyword Placement report. Drop video / NTB / brand-engagement / click-only blocks if you only need basic placement performance.
