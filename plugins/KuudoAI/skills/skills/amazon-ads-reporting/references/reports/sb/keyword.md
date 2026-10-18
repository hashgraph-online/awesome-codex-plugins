# Sponsored Brands Keyword mapping

*Equivalent to v3 Sponsored_Brands_Keyword_report — 46 v3 columns mapped to v1 fields across two reports*

## Summary

This template replicates the v3 Sponsored Brands Keyword report on the Amazon Ads API v1 cross-product reporting endpoint (CreateReport). Of the 46 v3 columns, 41 map cleanly to v1 fields, 4 are derived client-side (ACOS, click-only ACOS, % of units new-to-brand, and the VTR definition choice), and 1 (Top-of-search Impression Share) requires a separate campaign-level report that joins back to the main report on (date.value, campaign.id).

Both report payloads were validated against the packaged v1 catalog: 47 fields in the main report and 8 in the supplemental TOS report — all returned valid: true with zero unknown fields, zero missing required, and zero incompatible pairs.

**Most important difference vs the SP reports in this series: the filter is adProduct.value = SPONSORED_BRANDS (not SPONSORED_PRODUCTS). The v1 endpoint is shared across all ad products and the filter is the only thing that scopes the result set.**

## Two-report architecture

The validator caught that metric.topOfSearchImpressionShare is incompatible with adGroup.id, adGroup.name (and portfolio.\*, country.\*) and requires adProduct.value + advertiserAccount.id. This means the metric only lives at the campaign grain in v1. Build two reports:

-   Report 1 (main): all 41 mappable v3 columns at the date × portfolio × campaign × ad group × keyword × match-type grain, plus the four derivation inputs.

-   Report 2 (supplemental): metric.topOfSearchImpressionShare at the date × campaign grain. LEFT JOIN onto Report 1 on (date.value, campaign.id). The TOS impression share value will fan out across all (keyword, match type, ad group) rows for the same campaign-day — that's correct, not a bug.

## Report 1 — field list (grouped by role)

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
>
- `metric.detailPageViewsFromClicksHalo`

**Filter (limits the report to SB)**

- `adProduct.value = SPONSORED_BRANDS`

## v3 → v1 field mapping

| **v3 Column (Sponsored_Brands_Keyword)**           | **v1 field_id**                                        | **Role**                      | **Notes**                                                                                                                                                                                                                                                                                                                                                                      |
|----------------------------------------------------|--------------------------------------------------------|-------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Date                                               | date.value                                             | Time dimension                | Required time dimension.                                                                                                                                                                                                                                                                                                                                                       |
| Portfolio name                                     | portfolio.name                                         | Dimension                     | Pair with portfolio.portfolioId.                                                                                                                                                                                                                                                                                                                                               |
| —                                                  | portfolio.portfolioId                                  | Dimension                     | Stable join key.                                                                                                                                                                                                                                                                                                                                                               |
| Currency                                           | campaign.currencyCode                                  | Dimension                     | Pair with budgetCurrency.value.                                                                                                                                                                                                                                                                                                                                                |
| Campaign Name                                      | campaign.name                                          | Dimension                     | Pair with campaign.id.                                                                                                                                                                                                                                                                                                                                                         |
| —                                                  | campaign.id                                            | Dimension                     | Stable join key — also used for the supplemental TOS report.                                                                                                                                                                                                                                                                                                                   |
| Ad Group Name                                      | adGroup.name                                           | Dimension                     | Pair with adGroup.id.                                                                                                                                                                                                                                                                                                                                                          |
| —                                                  | adGroup.id                                             | Dimension                     | Stable join key.                                                                                                                                                                                                                                                                                                                                                               |
| Targeting                                          | target.value                                           | Dimension                     | The keyword expression.                                                                                                                                                                                                                                                                                                                                                        |
| Match Type                                         | target.matchType                                       | Dimension                     | BROAD / PHRASE / EXACT for SB keywords.                                                                                                                                                                                                                                                                                                                                        |
| Cost type                                          | campaign.costType                                      | Dimension                     | CPC / vCPM — the bidding cost model. Native dimension in v1.                                                                                                                                                                                                                                                                                                                   |
| —                                                  | budgetCurrency.value                                   | Required support              | v1 minimal-baseline supporting field for currency-denominated metrics.                                                                                                                                                                                                                                                                                                         |
| Impressions                                        | metric.impressions                                     | Metric                        | Direct.                                                                                                                                                                                                                                                                                                                                                                        |
| Top-of-search Impression Share                     | metric.topOfSearchImpressionShare                      | Metric — separate report      | INCOMPATIBLE with adGroup.\* (and portfolio.\*, country.\*). Validator-confirmed. Must be requested in a SEPARATE campaign-level report (Report 2) and joined on (date.value, campaign.id). Requires adProduct.value + advertiserAccount.id.                                                                                                                                   |
| Viewable Impressions                               | metric.viewableImpressions                             | Metric                        | Direct.                                                                                                                                                                                                                                                                                                                                                                        |
| Clicks                                             | metric.clicks                                          | Metric                        | Direct.                                                                                                                                                                                                                                                                                                                                                                        |
| Click-Thru Rate (CTR)                              | metric.ctr                                             | Metric                        | Direct.                                                                                                                                                                                                                                                                                                                                                                        |
| Spend                                              | metric.totalCost                                       | Metric                        | v1 renames 'spend' to totalCost across all ad products.                                                                                                                                                                                                                                                                                                                        |
| Cost Per Click (CPC)                               | metric.cpc                                             | Metric                        | Direct.                                                                                                                                                                                                                                                                                                                                                                        |
| Cost per 1,000 viewable impressions (VCPM)         | metric.vcpm                                            | Metric                        | Direct — Viewable CPM.                                                                                                                                                                                                                                                                                                                                                         |
| Total Advertising Cost of Sales (ACOS)             | (derive client-side)                                   | Derived                       | v1 has no metric.acos. Compute as totalCost / NULLIF(sales, 0) or 1 / roas.                                                                                                                                                                                                                                                                                                    |
| Total Return on Advertising Spend (ROAS)           | metric.roas                                            | Metric                        | Direct.                                                                                                                                                                                                                                                                                                                                                                        |
| 14 Day Total Sales                                 | metric.sales                                           | Metric                        | 14-day window is set on the report request, not in the field name.                                                                                                                                                                                                                                                                                                             |
| 14 Day Total Orders (#)                            | metric.purchases                                       | Metric                        | Equivalent — orders → purchases.                                                                                                                                                                                                                                                                                                                                               |
| 14 Day Total Units (#)                             | metric.unitsSold                                       | Metric                        | Direct.                                                                                                                                                                                                                                                                                                                                                                        |
| 14 Day Conversion Rate                             | metric.purchaseRateOverClicks (or metric.purchaseRate) | Metric                        | v1 has no 'conversionRate' field. purchaseRateOverClicks = purchases / clicks (typical SB UI definition); purchaseRate = purchases / impressions. Both included so the warehouse can pick.                                                                                                                                                                                     |
| View-Through Rate (VTR)                            | metric.completionRateVideoAd (closest)                 | Metric — definition-dependent | v1 has no metric.vtr or metric.viewThroughRate. Validator suggests metric.5secondViewRateVideoAd as a partial match. VTR's definition varies: completion rate (full play) maps to metric.completionRateVideoAd; 5-second-view-based VTR maps to metric.5secondViewRateVideoAd. Pick whichever matches your downstream definition; both are included in the request for safety. |
| Click-Through Rate for Views (vCTR)                | metric.vctr                                            | Metric                        | v1 calls this 'Viewable CTR' = clicks / viewable impressions.                                                                                                                                                                                                                                                                                                                  |
| Video First Quartile Views                         | metric.firstQuartileVideoAd                            | Metric                        | Direct — 25% played.                                                                                                                                                                                                                                                                                                                                                           |
| Video Midpoint Views                               | metric.midpointVideoAd                                 | Metric                        | Direct — 50% played.                                                                                                                                                                                                                                                                                                                                                           |
| Video Third Quartile Views                         | metric.thirdQuartileVideoAd                            | Metric                        | Direct — 75% played.                                                                                                                                                                                                                                                                                                                                                           |
| Video Complete Views                               | metric.completeViewsVideoAd                            | Metric                        | Direct.                                                                                                                                                                                                                                                                                                                                                                        |
| Video Unmutes                                      | metric.unmutesVideoAd                                  | Metric                        | Direct.                                                                                                                                                                                                                                                                                                                                                                        |
| 5 Second Views                                     | metric.5secondViewsVideoAd                             | Metric                        | Direct.                                                                                                                                                                                                                                                                                                                                                                        |
| 5 Second View Rate                                 | metric.5secondViewRateVideoAd                          | Metric                        | Direct.                                                                                                                                                                                                                                                                                                                                                                        |
| 14 Day Branded Searches                            | metric.brandedSearches                                 | Metric                        | Direct.                                                                                                                                                                                                                                                                                                                                                                        |
| 14 Day Detail Page Views (DPV)                     | metric.detailPageViews                                 | Metric                        | Direct — all-attribution DPV.                                                                                                                                                                                                                                                                                                                                                  |
| 14 Day New-to-brand Orders (#)                     | metric.newToBrandPurchases                             | Metric                        | Direct.                                                                                                                                                                                                                                                                                                                                                                        |
| 14 Day % of Orders New-to-brand                    | metric.percentOfPurchasesNewToBrand                    | Metric                        | Direct.                                                                                                                                                                                                                                                                                                                                                                        |
| 14 Day New-to-brand Sales                          | metric.newToBrandSales                                 | Metric                        | Direct.                                                                                                                                                                                                                                                                                                                                                                        |
| 14 Day % of Sales New-to-brand                     | metric.percentOfSalesNewToBrand                        | Metric                        | Direct.                                                                                                                                                                                                                                                                                                                                                                        |
| 14 Day New-to-brand Units (#)                      | metric.newToBrandUnitsSold                             | Metric                        | Direct.                                                                                                                                                                                                                                                                                                                                                                        |
| 14 Day % of Units New-to-brand                     | (derive client-side)                                   | Derived                       | v1 has no metric.percentOfUnitsNewToBrand (validator-confirmed unknown). Compute as newToBrandUnitsSold / NULLIF(unitsSold, 0).                                                                                                                                                                                                                                                |
| 14 Day New-to-brand Order Rate                     | metric.newToBrandPurchaseRate                          | Metric                        | Direct — newToBrandPurchases / impressions.                                                                                                                                                                                                                                                                                                                                    |
| Total ACOS - (Click)                               | (derive client-side)                                   | Derived                       | ACOS variants don't exist in v1. Compute as totalCost / NULLIF(salesFromClicks, 0).                                                                                                                                                                                                                                                                                            |
| Total ROAS - (Click)                               | metric.roasFromClicks                                  | Metric                        | Direct.                                                                                                                                                                                                                                                                                                                                                                        |
| 14 Day Total Sales - (Click)                       | metric.salesFromClicks                                 | Metric                        | Direct — click-attributed sales.                                                                                                                                                                                                                                                                                                                                               |
| 14 Day Total Orders (#) - (Click)                  | metric.purchasesFromClicks                             | Metric                        | Direct — click-attributed purchases.                                                                                                                                                                                                                                                                                                                                           |
| 14 Day Total Units (#) - (Click)                   | metric.unitsSoldFromClicks                             | Metric                        | Direct — click-attributed units.                                                                                                                                                                                                                                                                                                                                               |
| 14 Day Brand Total Detail Page Views (#) - (Click) | metric.detailPageViewsFromClicksHalo                   | Metric                        | Brand DPV from clicks. 'Halo' = highly relevant non-promoted products from the same brand — which is what 'Brand Total DPV' means in the v3 column. Pair with metric.detailPageViewsFromClicksPromoted if you want to recompose the full click-attributed DPV total.                                                                                                           |

*Yellow rows highlight columns that don't have a clean one-to-one v1 mapping (no v1 equivalent, derived client-side, definition-dependent, or split across reports).*

## Critical differences from the v3 report

| **Change**                                                         | **What it means for the request**                                                                                                                                                                                                                                                                                                                                                   |
|--------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Filter on adProduct.value = SPONSORED_BRANDS                       | Critical change vs the SP reports — the v1 endpoint is shared across all ad products, so the filter is the only thing that scopes results to Sponsored Brands. Using SPONSORED_PRODUCTS will silently return SP data and zero SB rows.                                                                                                                                              |
| Top-of-search Impression Share forces a SECOND report              | Same constraint as in the SP Targeting report. metric.topOfSearchImpressionShare is incompatible with adGroup.\* (validator-confirmed) and requires adProduct.value + advertiserAccount.id. Run two reports and join on (date.value, campaign.id).                                                                                                                                  |
| No metric.acos field — applies to BOTH all-attr and click-only     | Validator rejects metric.acos. Compute totalCost / NULLIF(sales, 0) for the all-attribution ACOS column, and totalCost / NULLIF(salesFromClicks, 0) for the '- (Click)' ACOS variant.                                                                                                                                                                                               |
| No 'View-Through Rate (VTR)' field — definition is ambiguous in v1 | v1 has no metric.vtr or metric.viewThroughRate. The validator suggests metric.5secondViewRateVideoAd as a partial match. SB's VTR definition typically means a completed view (or in some accounts, a 5-second view). The template includes both metric.completionRateVideoAd AND metric.5secondViewRateVideoAd; pick the right one downstream based on what your consumers expect. |
| No 'conversion rate' field — choose by definition                  | Same as the SP Targeting report. metric.purchaseRateOverClicks (purchases/clicks) matches the typical SB UI definition; metric.purchaseRate is purchases/impressions. Including both lets the warehouse decide.                                                                                                                                                                     |
| No metric.percentOfUnitsNewToBrand field                           | v3 has '14 Day % of Units New-to-brand' but v1 does not expose it (validator-confirmed unknown — it has the % for sales and orders, but not units). Derive: percentOfUnitsNewToBrand = newToBrandUnitsSold / NULLIF(unitsSold, 0).                                                                                                                                                  |
| Click-only attribution is the \*FromClicks family                  | v3's '- (Click)' suffix maps to v1's \*FromClicks variants: salesFromClicks, purchasesFromClicks, unitsSoldFromClicks, roasFromClicks, detailPageViewsFromClicksHalo. The '- (Click)' suffix on ACOS is also derived (totalCost/salesFromClicks).                                                                                                                                   |
| Brand DPV is 'halo' DPV from clicks                                | The v3 column '14 Day Brand Total Detail Page Views (#) - (Click)' means click-attributed detail-page views for the brand's halo (non-directly-promoted) products. v1 maps this exactly to metric.detailPageViewsFromClicksHalo. If you also want promoted-only DPV, add metric.detailPageViewsFromClicksPromoted.                                                                  |
| Attribution windows leave the field name                           | v3's '14 Day' prefix on Sales/Orders/Units/Conversion Rate/Branded Searches/DPV/NTB-\* is gone. The 14-day window is set on the report request itself; the fields are window-agnostic.                                                                                                                                                                                              |
| 'Spend' → metric.totalCost                                         | Renamed across all ad products in v1.                                                                                                                                                                                                                                                                                                                                               |
| Cost type is a native dimension                                    | campaign.costType returns 'CPC' or 'CPM' / 'vCPM' — direct equivalent of v3's 'Cost type' column. No derivation needed.                                                                                                                                                                                                                                                             |

## Operational notes


-   VTR definition: confirm with consumers whether they expect VTR to mean completion rate (full play) or 5-second view rate. The template carries both metric.completionRateVideoAd AND metric.5secondViewRateVideoAd so the warehouse can pick. If you only want one, drop the other from the field list to slim the payload.

-   Conversion rate: same definition pattern as the SP Targeting report. SB UIs typically use orders/clicks → metric.purchaseRateOverClicks. Drop metric.purchaseRate if you don't need the impressions-denominated alternative.


-   Derivations to materialize in the warehouse: acos = totalCost / NULLIF(sales, 0); acosClickOnly = totalCost / NULLIF(salesFromClicks, 0); percentOfUnitsNewToBrand = newToBrandUnitsSold / NULLIF(unitsSold, 0). Persist the raw inputs alongside the views.

-   Reusing this template for SB Campaign or SB Ad Group: drop target.value, target.matchType (and adGroup.\* for campaign grain), keep everything else — the metric set is identical at coarser grains.
