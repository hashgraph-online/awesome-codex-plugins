# Sponsored Display Targeting mapping

*Equivalent to v3 Sponsored_Display_Targeting_report — 32 v3 columns mapped to v1 fields*

## Summary

This template replicates the v3 Sponsored Display Targeting report on the Amazon Ads API v1 cross-product reporting endpoint (CreateReport). 31 of 32 v3 columns map cleanly to v1 fields; ACOS variants are derived client-side. The one v3 column without a v1 reporting equivalent is 'Bid optimization' — recovered by joining campaign management API output.

The 31-field payload was validated against the packaged v1 catalog: zero unknown fields, zero missing required, zero incompatible pairs.

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
- `metric.detailPageViews`
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
- `metric.roas`
>
- `metric.newToBrandPurchases`
>
- `metric.newToBrandSales`
>
- `metric.newToBrandUnitsSold`

**Click-only attribution variants**

- `metric.salesFromClicks`
>
- `metric.purchasesFromClicks`
>
- `metric.unitsSoldFromClicks`
>
- `metric.roasFromClicks`
>
- `metric.newToBrandPurchasesFromClicks`
>
- `metric.newToBrandSalesFromClicks`
>
- `metric.newToBrandUnitsSoldFromClicks`

**Filter (limits the report to SD)**

- `adProduct.value = SPONSORED_DISPLAY`

## v3 → v1 field mapping

| **v3 Column (Sponsored_Display_Targeting)** | **v1 field_id**                                                    | **Role**         | **Notes**                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
|---------------------------------------------|--------------------------------------------------------------------|------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Date                                        | date.value                                                         | Time dimension   | Required time dimension.                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| Currency                                    | campaign.currencyCode                                              | Dimension        | Pair with budgetCurrency.value.                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| Campaign Name                               | campaign.name                                                      | Dimension        | Pair with campaign.id.                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| —                                           | campaign.id                                                        | Dimension        | Stable join key.                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| Portfolio name                              | portfolio.name                                                     | Dimension        | Pair with portfolio.portfolioId.                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| —                                           | portfolio.portfolioId                                              | Dimension        | Stable join key.                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| Cost type                                   | campaign.costType                                                  | Dimension        | CPC / VCPM. Native dimension in v1. SD frequently uses VCPM bidding (the report sample shows it).                                                                                                                                                                                                                                                                                                                                                                                           |
| Ad Group Name                               | adGroup.name                                                       | Dimension        | Pair with adGroup.id.                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| —                                           | adGroup.id                                                         | Dimension        | Stable join key.                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| Targeting                                   | target.value                                                       | Dimension        | The SD targeting expression — product target (asin="B..."), category target, or audience expression. Note: SD has no match types, so target.matchType is intentionally NOT in this template (unlike SP/SB).                                                                                                                                                                                                                                                                                 |
| Bid optimization                            | (no v1 reporting equivalent — recover via campaign management API) | —                | v1 has no campaign.bidOptimization or bidOptimization.value field (validator-confirmed unknown). SD-specific bid optimization values like SD_REACH, SD_CONVERSIONS, SD_DPV are campaign-management attributes that are not exposed at the report grain. Recovery: call the campaign-list operation and join the bidOptimization field on campaign.id in the warehouse. Don't conflate with campaign.bidStrategy — that's a different concept (LEGACY_FOR_SALES, AUTO_FOR_SALES, etc.). |
| —                                           | budgetCurrency.value                                               | Required support | v1 minimal-baseline supporting field for currency-denominated metrics.                                                                                                                                                                                                                                                                                                                                                                                                                      |
| Impressions                                 | metric.impressions                                                 | Metric           | Direct.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| Viewable Impressions                        | metric.viewableImpressions                                         | Metric           | Direct.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| Clicks                                      | metric.clicks                                                      | Metric           | Direct.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| Click-Thru Rate (CTR)                       | metric.ctr                                                         | Metric           | Direct.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| 14 Day Detail Page Views (DPV)              | metric.detailPageViews                                             | Metric           | Direct — all-attribution DPV.                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| Spend                                       | metric.totalCost                                                   | Metric           | v1 renames 'spend' to totalCost across all ad products.                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| Cost Per Click (CPC)                        | metric.cpc                                                         | Metric           | Direct.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| Cost per 1,000 viewable impressions (VCPM)  | metric.vcpm                                                        | Metric           | Direct.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| Total ACOS                                  | (derive client-side)                                               | Derived          | v1 has no metric.acos. Compute as totalCost / NULLIF(sales, 0) or 1 / roas.                                                                                                                                                                                                                                                                                                                                                                                                                 |
| Total ROAS                                  | metric.roas                                                        | Metric           | Direct.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| 14 Day Total Orders (#)                     | metric.purchases                                                   | Metric           | Equivalent — orders → purchases.                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| 14 Day Total Units (#)                      | metric.unitsSold                                                   | Metric           | Direct.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| 14 Day Total Sales                          | metric.sales                                                       | Metric           | 14-day window is set on the report request.                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| 14 Day New-to-brand Orders (#)              | metric.newToBrandPurchases                                         | Metric           | Direct.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| 14 Day New-to-brand Sales                   | metric.newToBrandSales                                             | Metric           | Direct.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| 14 Day New-to-brand Units (#)               | metric.newToBrandUnitsSold                                         | Metric           | Direct.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| Total ACOS - (Click)                        | (derive client-side)                                               | Derived          | totalCost / NULLIF(salesFromClicks, 0).                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| Total ROAS - (Click)                        | metric.roasFromClicks                                              | Metric           | Direct.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| 14 Day Total Orders (#) - (Click)           | metric.purchasesFromClicks                                         | Metric           | Direct.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| 14 Day Total Units (#) - (Click)            | metric.unitsSoldFromClicks                                         | Metric           | Direct.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| 14 Day Total Sales - (Click)                | metric.salesFromClicks                                             | Metric           | Direct.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| 14 Day New-to-brand Orders (#) - (Click)    | metric.newToBrandPurchasesFromClicks                               | Metric           | Direct.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| 14 Day New-to-brand Sales - (Click)         | metric.newToBrandSalesFromClicks                                   | Metric           | Direct.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| 14 Day New-to-brand Units (#) - (Click)     | metric.newToBrandUnitsSoldFromClicks                               | Metric           | Direct.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |

*Red row highlights the column with no v1 reporting equivalent. Yellow rows are derived client-side.*

## Critical differences from the v3 report

| **Change**                                                     | **What it means for the request**                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
|----------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Filter on adProduct.value = SPONSORED_DISPLAY                  | The v1 endpoint is shared across all ad products; the filter scopes results to Sponsored Display. SPONSORED_PRODUCTS, SPONSORED_BRANDS, SPONSORED_DISPLAY are the canonical filter values for the three programs.                                                                                                                                                                                                                                                                                               |
| No 'Bid optimization' dimension in v1 reporting                | Validator-confirmed unknown for campaign.bidOptimization, bidOptimization.value, and similar variants. SD bid-optimization settings (SD_REACH, SD_CONVERSIONS, SD_DPV, SD_VIEWABLE_CPM) are campaign-management attributes only. Recovery path: call the campaign-list operation and join the bidOptimization field on campaign.id. Don't substitute campaign.bidStrategy — that's a different concept covering AUTO_FOR_SALES vs LEGACY_FOR_SALES vs MANUAL bidding behavior, not SD's optimization goal. |
| No target.matchType in this template — SD has no match types   | SP and SB Keyword reports include target.matchType (BROAD/PHRASE/EXACT for keywords, EXPANDED/TARGETED for product targets). SD targeting is product/category/audience expressions only, not keywords — so target.matchType doesn't apply at this grain. The v3 SD Targeting report doesn't have a Match Type column for this reason.                                                                                                                                                                           |
| No metric.acos field — applies to BOTH all-attr and click-only | Compute totalCost / NULLIF(sales, 0) and totalCost / NULLIF(salesFromClicks, 0) downstream.                                                                                                                                                                                                                                                                                                                                                                                                                     |
| Click-only attribution is the \*FromClicks family              | SD also has \*FromViews variants if you want explicit view-only columns. The v3 report only carries '- (Click)' suffixes (click-only), not '- (View)' suffixes; total - click gives view-attribution if you need it.                                                                                                                                                                                                                                                                                            |
| Attribution windows leave the field name                       | v3's '14 Day' prefix is gone; the 14-day window is set on the report request itself.                                                                                                                                                                                                                                                                                                                                                                                                                            |
| 'Spend' → metric.totalCost                                     | Renamed across all ad products in v1.                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| Cost type is a native dimension                                | campaign.costType returns CPC / VCPM — direct equivalent of the v3 'Cost type' column. Sponsored Display campaigns frequently use VCPM bidding.                                                                                                                                                                                                                                                                                                                                                                 |

## Operational notes

-   Recovering 'Bid optimization': call the campaign-list operation once per ETL run (it's a small list) and persist a campaign_id → bidOptimization mapping in the warehouse. LEFT JOIN onto the report on campaign.id. Refresh weekly or when bid-optimization changes are made.



-   Derivations to materialize in the warehouse: acos = totalCost / NULLIF(sales, 0); acosClickOnly = totalCost / NULLIF(salesFromClicks, 0).

-   Reusing this template: this is the canonical SD targeting-grain template. The SD Advertised Product report uses the same field set with target.value swapped for advertisedProduct.id/sku; the SD Campaign report uses the same metric set at coarser grain with extra ATC/branded-search/long-term metrics layered on.
