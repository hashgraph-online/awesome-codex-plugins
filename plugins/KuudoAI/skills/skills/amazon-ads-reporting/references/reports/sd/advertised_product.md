# Sponsored Display Advertised Product mapping

*Equivalent to v3 Sponsored_Display_Advertised_product_report — 33 v3 columns mapped to v1 fields*

## Summary

This template replicates the v3 Sponsored Display Advertised Product report on the Amazon Ads API v1 cross-product reporting endpoint (CreateReport). 32 of 33 v3 columns map cleanly to v1 fields; 2 are derived client-side (ACOS, click-only ACOS); 1 ('Bid optimization') has no v1 reporting equivalent — recover by joining campaign management API output.

The 33-field payload was validated against the packaged v1 catalog: zero unknown fields, zero missing required, zero incompatible pairs.

*This report is structurally the SD Targeting report's metric set at the advertised-product grain instead of the target grain. Same metric set, same derivations, same gaps.*

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
- `advertisedProduct.id`
>
- `advertisedProduct.sku`
>
- `advertisedProduct.marketplace`

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

| **v3 Column (Sponsored_Display_Advertised_product)** | **v1 field_id**                                                    | **Role**         | **Notes**                                                                                                                                                                                                                                                                                                          |
|------------------------------------------------------|--------------------------------------------------------------------|------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Date                                                 | date.value                                                         | Time dimension   | Required time dimension.                                                                                                                                                                                                                                                                                           |
| Portfolio name                                       | portfolio.name                                                     | Dimension        | Pair with portfolio.portfolioId.                                                                                                                                                                                                                                                                                   |
| —                                                    | portfolio.portfolioId                                              | Dimension        | Stable join key.                                                                                                                                                                                                                                                                                                   |
| Currency                                             | campaign.currencyCode                                              | Dimension        | Pair with budgetCurrency.value.                                                                                                                                                                                                                                                                                    |
| Campaign Name                                        | campaign.name                                                      | Dimension        | Pair with campaign.id.                                                                                                                                                                                                                                                                                             |
| —                                                    | campaign.id                                                        | Dimension        | Stable join key.                                                                                                                                                                                                                                                                                                   |
| Cost type                                            | campaign.costType                                                  | Dimension        | CPC / VCPM. Native dimension in v1.                                                                                                                                                                                                                                                                                |
| Ad Group Name                                        | adGroup.name                                                       | Dimension        | Pair with adGroup.id.                                                                                                                                                                                                                                                                                              |
| —                                                    | adGroup.id                                                         | Dimension        | Stable join key.                                                                                                                                                                                                                                                                                                   |
| Bid optimization                                     | (no v1 reporting equivalent — recover via campaign management API) | —                | Same gap as the SD Targeting report. Validator-confirmed unknown for campaign.bidOptimization, bidOptimization.value. SD bid-optimization values (SD_REACH, SD_CONVERSIONS, SD_DPV, SD_VIEWABLE_CPM) are campaign-management attributes only — recover by joining the campaign-list operation on campaign.id. |
| Advertised SKU                                       | advertisedProduct.sku                                              | Dimension        | Direct equivalent.                                                                                                                                                                                                                                                                                                 |
| Advertised ASIN                                      | advertisedProduct.id                                               | Dimension        | ASIN is the v1 primary key for advertised product.                                                                                                                                                                                                                                                                 |
| —                                                    | advertisedProduct.marketplace                                      | Dimension        | Distinguishes the same ASIN across regional marketplaces.                                                                                                                                                                                                                                                          |
| —                                                    | budgetCurrency.value                                               | Required support | v1 minimal-baseline supporting field.                                                                                                                                                                                                                                                                              |
| Impressions                                          | metric.impressions                                                 | Metric           | Direct.                                                                                                                                                                                                                                                                                                            |
| Viewable Impressions                                 | metric.viewableImpressions                                         | Metric           | Direct.                                                                                                                                                                                                                                                                                                            |
| Clicks                                               | metric.clicks                                                      | Metric           | Direct.                                                                                                                                                                                                                                                                                                            |
| Click-Thru Rate (CTR)                                | metric.ctr                                                         | Metric           | Direct.                                                                                                                                                                                                                                                                                                            |
| 14 Day Detail Page Views (DPV)                       | metric.detailPageViews                                             | Metric           | Direct — all-attribution DPV.                                                                                                                                                                                                                                                                                      |
| Spend                                                | metric.totalCost                                                   | Metric           | v1 renames 'spend' to totalCost.                                                                                                                                                                                                                                                                                   |
| Cost Per Click (CPC)                                 | metric.cpc                                                         | Metric           | Direct.                                                                                                                                                                                                                                                                                                            |
| Cost per 1,000 viewable impressions (VCPM)           | metric.vcpm                                                        | Metric           | Direct.                                                                                                                                                                                                                                                                                                            |
| Total ACOS                                           | (derive client-side)                                               | Derived          | totalCost / NULLIF(sales, 0) or 1 / roas.                                                                                                                                                                                                                                                                          |
| Total ROAS                                           | metric.roas                                                        | Metric           | Direct.                                                                                                                                                                                                                                                                                                            |
| 14 Day Total Orders (#)                              | metric.purchases                                                   | Metric           | Equivalent — orders → purchases.                                                                                                                                                                                                                                                                                   |
| 14 Day Total Units (#)                               | metric.unitsSold                                                   | Metric           | Direct.                                                                                                                                                                                                                                                                                                            |
| 14 Day Total Sales                                   | metric.sales                                                       | Metric           | 14-day window is set on the report request.                                                                                                                                                                                                                                                                        |
| 14 Day New-to-brand Orders (#)                       | metric.newToBrandPurchases                                         | Metric           | Direct.                                                                                                                                                                                                                                                                                                            |
| 14 Day New-to-brand Sales                            | metric.newToBrandSales                                             | Metric           | Direct.                                                                                                                                                                                                                                                                                                            |
| 14 Day New-to-brand Units (#)                        | metric.newToBrandUnitsSold                                         | Metric           | Direct.                                                                                                                                                                                                                                                                                                            |
| Total ACOS - (Click)                                 | (derive client-side)                                               | Derived          | totalCost / NULLIF(salesFromClicks, 0).                                                                                                                                                                                                                                                                            |
| Total ROAS - (Click)                                 | metric.roasFromClicks                                              | Metric           | Direct.                                                                                                                                                                                                                                                                                                            |
| 14 Day Total Orders (#) - (Click)                    | metric.purchasesFromClicks                                         | Metric           | Direct.                                                                                                                                                                                                                                                                                                            |
| 14 Day Total Units (#) - (Click)                     | metric.unitsSoldFromClicks                                         | Metric           | Direct.                                                                                                                                                                                                                                                                                                            |
| 14 Day Total Sales - (Click)                         | metric.salesFromClicks                                             | Metric           | Direct.                                                                                                                                                                                                                                                                                                            |
| 14 Day New-to-brand Orders (#) - (Click)             | metric.newToBrandPurchasesFromClicks                               | Metric           | Direct.                                                                                                                                                                                                                                                                                                            |
| 14 Day New-to-brand Sales - (Click)                  | metric.newToBrandSalesFromClicks                                   | Metric           | Direct.                                                                                                                                                                                                                                                                                                            |
| 14 Day New-to-brand Units (#) - (Click)              | metric.newToBrandUnitsSoldFromClicks                               | Metric           | Direct.                                                                                                                                                                                                                                                                                                            |

*Red row highlights the column with no v1 reporting equivalent. Yellow rows are derived client-side.*

## Critical differences from the v3 report

| **Change**                                                                                                         | **What it means for the request**                                                                                                                                    |
|--------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Filter on adProduct.value = SPONSORED_DISPLAY                                                                      | The v1 endpoint is shared across all ad products.                                                                                                                    |
| No 'Bid optimization' dimension in v1 reporting                                                                    | Same gap as the SD Targeting report. Recover by joining the campaign-list operation on campaign.id.                                                             |
| This report is essentially the SD Targeting report's metric set with target.value swapped for advertisedProduct.\* | Same exact metric set, same exact derivations, same filter. Identical caveats apply (no metric.acos, no Bid optimization, attribution windows leave the field name). |
| No metric.acos field — applies to BOTH all-attr and click-only                                                     | Compute totalCost / NULLIF(sales, 0) and totalCost / NULLIF(salesFromClicks, 0).                                                                                     |
| 'Spend' → metric.totalCost                                                                                         | Renamed across all ad products in v1.                                                                                                                                |
| Attribution windows leave the field name                                                                           | v3's '14 Day' prefix is gone; window is set on the report request.                                                                                                   |

## Operational notes

-   Recovering 'Bid optimization': call the campaign-list operation once per ETL run and persist a campaign_id → bidOptimization mapping. LEFT JOIN onto the report on campaign.id.


-   Derivations to materialize in the warehouse: acos = totalCost / NULLIF(sales, 0); acosClickOnly = totalCost / NULLIF(salesFromClicks, 0).

-   Reusing this template alongside SD Targeting: the SD Targeting and SD Advertised Product reports have identical metric sets — the only difference is the dimensional grain (target.value vs advertisedProduct.id/sku). Run both reports for the same time range and join on campaign.id and adGroup.id to get a unified target × advertised-product cross-tab.
