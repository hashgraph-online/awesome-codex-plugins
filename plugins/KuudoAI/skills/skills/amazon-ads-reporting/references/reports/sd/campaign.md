# Sponsored Display Campaign mapping

*Equivalent to v3 Sponsored_Display_Campaign_report — 49 v3 columns mapped to v1 fields*

## Summary

This template replicates the v3 Sponsored Display Campaign report on the Amazon Ads API v1 cross-product reporting endpoint (CreateReport). 47 of 49 v3 columns map cleanly to v1 fields; 2 are derived client-side (ACOS, click-only ACOS). This is the broadest of the four SD reports — it includes the full Add to Cart suite, NTB DPV breakdown, Branded Search breakdown, and Long-Term metrics on top of the standard delivery/conversion metric set.

The 51-field payload was validated against the packaged v1 catalog: zero unknown fields, zero missing required, zero incompatible pairs.

## Field list (grouped by role)

**Time dimension (exactly one required)**

- `date.value`

**Level-of-detail dimensions**

- `country.code`
>
- `country.name`
>
- `campaign.country`
>
- `campaign.deliveryStatus`
>
- `campaign.currencyCode`
>
- `campaign.budgetAmount`
>
- `campaign.budgetType`
>
- `campaign.id`
>
- `campaign.name`
>
- `portfolio.portfolioId`
>
- `portfolio.name`
>
- `campaign.costType`
>
- `adProduct.value`

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

**NTB Detail Page View breakdown**

- `metric.newToBrandDetailPageViews`
>
- `metric.newToBrandDetailPageViewsFromViews`
>
- `metric.newToBrandDetailPageViewsFromClicks`
>
- `metric.newToBrandDetailPageViewRate`
>
- `metric.costPerNewToBrandDetailPageView`

**Add to Cart suite**

- `metric.addToCart`
>
- `metric.addToCartFromViews`
>
- `metric.addToCartFromClicks`
>
- `metric.addToCartRate`
>
- `metric.costPerAddToCart`

**Branded Searches breakdown**

- `metric.brandedSearches`
>
- `metric.brandedSearchesFromViews`
>
- `metric.brandedSearchesFromClicks`
>
- `metric.brandedSearchRate`
>
- `metric.costPerBrandedSearch`

**Long-term metrics**

- `metric.longTermSales`
>
- `metric.longTermRoas`

**Filter (limits the report to SD)**

- `adProduct.value = SPONSORED_DISPLAY`

## v3 → v1 field mapping

| **v3 Column (Sponsored_Display_Campaign)**              | **v1 field_id**                            | **Role**         | **Notes**                                                                                                                                                                                                                                            |
|---------------------------------------------------------|--------------------------------------------|------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Date                                                    | date.value                                 | Time dimension   | Required time dimension.                                                                                                                                                                                                                             |
| Country                                                 | country.name                               | Dimension        | Pair with country.code.                                                                                                                                                                                                                              |
| —                                                       | country.code                               | Dimension        | ISO country code.                                                                                                                                                                                                                                    |
| —                                                       | campaign.country                           | Dimension        | Campaign-setup country (independent of impression country). Both included for redundancy.                                                                                                                                                            |
| Status                                                  | campaign.deliveryStatus                    | Dimension        | Replaces v3's 'Status' column. v1 reports CURRENT delivery status (DELIVERING/INACTIVE/ENDED), not historical — same as the SP Campaign report. If you need a historical status timeline, capture campaign.deliveryStatus daily at ingest as an SCD. |
| Currency                                                | campaign.currencyCode                      | Dimension        | Pair with budgetCurrency.value.                                                                                                                                                                                                                      |
| Budget Amount                                           | campaign.budgetAmount                      | Dimension        | Pair with campaign.budgetType to disambiguate daily vs lifetime.                                                                                                                                                                                     |
| —                                                       | campaign.budgetType                        | Dimension        | DAILY / LIFETIME — context for budgetAmount.                                                                                                                                                                                                         |
| Campaign Name                                           | campaign.name                              | Dimension        | Pair with campaign.id.                                                                                                                                                                                                                               |
| —                                                       | campaign.id                                | Dimension        | Stable join key.                                                                                                                                                                                                                                     |
| Portfolio name                                          | portfolio.name                             | Dimension        | Pair with portfolio.portfolioId.                                                                                                                                                                                                                     |
| —                                                       | portfolio.portfolioId                      | Dimension        | Stable join key.                                                                                                                                                                                                                                     |
| Cost type                                               | campaign.costType                          | Dimension        | CPC / VCPM. Native dimension in v1.                                                                                                                                                                                                                  |
| —                                                       | adProduct.value                            | Dimension        | Identifies SD; also used in the report filter.                                                                                                                                                                                                       |
| —                                                       | budgetCurrency.value                       | Required support | v1 minimal-baseline supporting field.                                                                                                                                                                                                                |
| Impressions                                             | metric.impressions                         | Metric           | Direct.                                                                                                                                                                                                                                              |
| Viewable Impressions                                    | metric.viewableImpressions                 | Metric           | Direct.                                                                                                                                                                                                                                              |
| Clicks                                                  | metric.clicks                              | Metric           | Direct.                                                                                                                                                                                                                                              |
| Click-Thru Rate (CTR)                                   | metric.ctr                                 | Metric           | Direct.                                                                                                                                                                                                                                              |
| 14 Day Detail Page Views (DPV)                          | metric.detailPageViews                     | Metric           | Direct — all-attribution DPV.                                                                                                                                                                                                                        |
| Spend                                                   | metric.totalCost                           | Metric           | v1 renames 'spend' to totalCost.                                                                                                                                                                                                                     |
| Cost Per Click (CPC)                                    | metric.cpc                                 | Metric           | Direct.                                                                                                                                                                                                                                              |
| Cost per 1,000 viewable impressions (VCPM)              | metric.vcpm                                | Metric           | Direct.                                                                                                                                                                                                                                              |
| Total ACOS                                              | (derive client-side)                       | Derived          | totalCost / NULLIF(sales, 0) or 1 / roas.                                                                                                                                                                                                            |
| Total ROAS                                              | metric.roas                                | Metric           | Direct.                                                                                                                                                                                                                                              |
| 14 Day Total Orders (#)                                 | metric.purchases                           | Metric           | Equivalent — orders → purchases.                                                                                                                                                                                                                     |
| 14 Day Total Units (#)                                  | metric.unitsSold                           | Metric           | Direct.                                                                                                                                                                                                                                              |
| 14 Day Total Sales                                      | metric.sales                               | Metric           | 14-day window is set on the report request.                                                                                                                                                                                                          |
| 14 Day New-to-brand Orders (#)                          | metric.newToBrandPurchases                 | Metric           | Direct.                                                                                                                                                                                                                                              |
| 14 Day New-to-brand Sales                               | metric.newToBrandSales                     | Metric           | Direct.                                                                                                                                                                                                                                              |
| 14 Day New-to-brand Units (#)                           | metric.newToBrandUnitsSold                 | Metric           | Direct.                                                                                                                                                                                                                                              |
| Total ACOS - (Click)                                    | (derive client-side)                       | Derived          | totalCost / NULLIF(salesFromClicks, 0).                                                                                                                                                                                                              |
| Total ROAS - (Click)                                    | metric.roasFromClicks                      | Metric           | Direct.                                                                                                                                                                                                                                              |
| 14 Day Total Orders (#) - (Click)                       | metric.purchasesFromClicks                 | Metric           | Direct.                                                                                                                                                                                                                                              |
| 14 Day Total Units (#) - (Click)                        | metric.unitsSoldFromClicks                 | Metric           | Direct.                                                                                                                                                                                                                                              |
| 14 Day Total Sales - (Click)                            | metric.salesFromClicks                     | Metric           | Direct.                                                                                                                                                                                                                                              |
| 14 Day New-to-brand Orders (#) - (Click)                | metric.newToBrandPurchasesFromClicks       | Metric           | Direct.                                                                                                                                                                                                                                              |
| 14 Day New-to-brand Sales - (Click)                     | metric.newToBrandSalesFromClicks           | Metric           | Direct.                                                                                                                                                                                                                                              |
| 14 Day New-to-brand Units (#) - (Click)                 | metric.newToBrandUnitsSoldFromClicks       | Metric           | Direct.                                                                                                                                                                                                                                              |
| New-to-brand detail page views                          | metric.newToBrandDetailPageViews           | Metric           | Direct.                                                                                                                                                                                                                                              |
| New-to-brand detail page view view-through conversions  | metric.newToBrandDetailPageViewsFromViews  | Metric           | Direct — view-attributed NTB DPV.                                                                                                                                                                                                                    |
| New-to-brand detail page view click-through conversions | metric.newToBrandDetailPageViewsFromClicks | Metric           | Direct — click-attributed NTB DPV.                                                                                                                                                                                                                   |
| New-to-brand detail page view rate                      | metric.newToBrandDetailPageViewRate        | Metric           | Direct — NTB DPV / impressions.                                                                                                                                                                                                                      |
| Effective cost per new-to-brand detail page view        | metric.costPerNewToBrandDetailPageView     | Metric           | Direct.                                                                                                                                                                                                                                              |
| 14 Day ATC                                              | metric.addToCart                           | Metric           | Direct — total Add to Cart events.                                                                                                                                                                                                                   |
| 14 Day ATC Views                                        | metric.addToCartFromViews                  | Metric           | Direct — view-attributed ATC.                                                                                                                                                                                                                        |
| 14 Day ATC Clicks                                       | metric.addToCartFromClicks                 | Metric           | Direct — click-attributed ATC.                                                                                                                                                                                                                       |
| 14 Day ATCR                                             | metric.addToCartRate                       | Metric           | Direct — ATC / impressions.                                                                                                                                                                                                                          |
| Effective cost per Add to Cart (eCPATC)                 | metric.costPerAddToCart                    | Metric           | Direct.                                                                                                                                                                                                                                              |
| 14 Day Branded Searches                                 | metric.brandedSearches                     | Metric           | Direct.                                                                                                                                                                                                                                              |
| Branded Searches view-through conversions               | metric.brandedSearchesFromViews            | Metric           | Direct — view-attributed branded searches.                                                                                                                                                                                                           |
| Branded Searches click-through conversions              | metric.brandedSearchesFromClicks           | Metric           | Direct — click-attributed branded searches.                                                                                                                                                                                                          |
| Branded Searches Rate                                   | metric.brandedSearchRate                   | Metric           | Direct — branded searches / impressions.                                                                                                                                                                                                             |
| Effective cost per Branded Search                       | metric.costPerBrandedSearch                | Metric           | Direct.                                                                                                                                                                                                                                              |
| Long-Term Sales                                         | metric.longTermSales                       | Metric           | Direct — projected 12-month sales from incremental NTB shopper engagement driven by the campaign.                                                                                                                                                    |
| Long-Term ROAS                                          | metric.longTermRoas                        | Metric           | Direct — long-term sales / total cost.                                                                                                                                                                                                               |

*Yellow rows are derived client-side. All other rows are direct mappings.*

## Critical differences from the v3 report

| **Change**                                                     | **What it means for the request**                                                                                                                                                                                                                                                                                    |
|----------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Filter on adProduct.value = SPONSORED_DISPLAY                  | The v1 endpoint is shared across all ad products.                                                                                                                                                                                                                                                                    |
| Status semantics shift                                         | v3 'Status' was historical; v1 campaign.deliveryStatus is the campaign's CURRENT delivery status (DELIVERING/INACTIVE/ENDED). Same caveat as the SP Campaign report — for a true historical status timeline, capture daily snapshots in the warehouse.                                                               |
| Add to Cart suite — full mapping                               | v3 ATC, ATC Views, ATC Clicks, ATCR, eCPATC map directly to metric.addToCart, metric.addToCartFromViews, metric.addToCartFromClicks, metric.addToCartRate, metric.costPerAddToCart. v1 has a much wider ATC family (newToBrand variants, halo variants, promoted variants) — extend the field list if you need them. |
| Branded Searches breakdown — full mapping                      | v3 columns map directly: brandedSearches, brandedSearchesFromViews, brandedSearchesFromClicks, brandedSearchRate, costPerBrandedSearch. The 'view-through conversions' / 'click-through conversions' suffixes on v3 column names map to \*FromViews / \*FromClicks in v1.                                            |
| NTB DPV breakdown — full mapping                               | v3's 'New-to-brand detail page view view-through conversions' = metric.newToBrandDetailPageViewsFromViews; same pattern for click-through and the rate / cost variants.                                                                                                                                              |
| Long-Term Sales / ROAS — direct mapping                        | metric.longTermSales is the 12-month projected sales from incremental NTB shopper engagement; metric.longTermRoas = longTermSales / totalCost. Available at the SD campaign grain.                                                                                                                                   |
| No metric.acos field — applies to BOTH all-attr and click-only | Compute totalCost / NULLIF(sales, 0) and totalCost / NULLIF(salesFromClicks, 0).                                                                                                                                                                                                                                     |
| 'Spend' → metric.totalCost                                     | Renamed across all ad products in v1.                                                                                                                                                                                                                                                                                |
| Attribution windows leave the field name                       | v3's '14 Day' prefix is gone; window is set on the report request.                                                                                                                                                                                                                                                   |

## Operational notes

-   Status historicity: campaign.deliveryStatus reports CURRENT status. For a historical status timeline, capture daily snapshots in the warehouse as a slowly-changing dimension.

-   Long-Term Sales / ROAS: these are PROJECTED 12-month metrics derived from NTB shopper engagement modeling — they're estimates, not actuals. Treat as forward-looking metrics rather than realized revenue.


-   Derivations to materialize in the warehouse: acos = totalCost / NULLIF(sales, 0); acosClickOnly = totalCost / NULLIF(salesFromClicks, 0). Persist raw inputs alongside the views.

-   Bid optimization recovery: this v3 report doesn't include the 'Bid optimization' column, but the SD Targeting and SD Advertised Product reports do. If you join all four SD reports together in the warehouse, fetch bidOptimization from the campaign-list operation once and join on campaign.id.
