# Sponsored Brands Campaign mapping

*Equivalent to v3 Sponsored_Brands_Campaign_report — 56 v3 columns mapped to v1 fields (largest report in the series)*

## Summary

This template replicates the v3 Sponsored Brands Campaign report on the Amazon Ads API v1 cross-product reporting endpoint (CreateReport). With 56 v3 columns this is the largest report in the series — it combines the full SB Keyword metric set with NTB DPV breakdown, ATC suite, Branded Search breakdown, Brand Store page views, and Long-Term Sales/ROAS at the campaign grain.

53 of 56 v3 columns map cleanly to v1 fields; 3 are derived client-side (ACOS, click-only ACOS, % of units NTB).

The 56-field payload was validated against the packaged v1 catalog: zero unknown fields, zero missing required, zero incompatible pairs.

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
- `country.code`
>
- `country.name`

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
>
- `metric.roas`

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

**Brand engagement (all-attribution)**

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

**NTB DPV breakdown (click-attributed only in this report)**

- `metric.newToBrandDetailPageViews`
>
- `metric.newToBrandDetailPageViewsFromClicks`
>
- `metric.newToBrandDetailPageViewRate`
>
- `metric.costPerNewToBrandDetailPageView`

**Brand Store page views**

- `metric.brandStorePageViews`

**Add to Cart suite (click-attributed only in this report)**

- `metric.addToCart`
>
- `metric.addToCartFromClicks`
>
- `metric.addToCartRate`
>
- `metric.costPerAddToCart`

**Branded Searches breakdown (click-attributed only in this report)**

- `metric.brandedSearchesFromClicks`
>
- `metric.brandedSearchRate`
>
- `metric.costPerBrandedSearch`

**Long-term metrics**

- `metric.longTermSales`
>
- `metric.longTermRoas`

**Filter (limits the report to SB)**

- `adProduct.value = SPONSORED_BRANDS`

## v3 → v1 field mapping

| **v3 Column (Sponsored_Brands_Campaign)**               | **v1 field_id**                                        | **Role**                      | **Notes**                                                                                                                                                                                                                        |
|---------------------------------------------------------|--------------------------------------------------------|-------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Date                                                    | date.value                                             | Time dimension                | Required time dimension.                                                                                                                                                                                                         |
| Portfolio name                                          | portfolio.name                                         | Dimension                     | Pair with portfolio.portfolioId.                                                                                                                                                                                                 |
| —                                                       | portfolio.portfolioId                                  | Dimension                     | Stable join key.                                                                                                                                                                                                                 |
| Currency                                                | campaign.currencyCode                                  | Dimension                     | Pair with budgetCurrency.value.                                                                                                                                                                                                  |
| Campaign Name                                           | campaign.name                                          | Dimension                     | Pair with campaign.id.                                                                                                                                                                                                           |
| —                                                       | campaign.id                                            | Dimension                     | Stable join key.                                                                                                                                                                                                                 |
| Cost type                                               | campaign.costType                                      | Dimension                     | CPC / CPM / vCPM. Native dimension in v1.                                                                                                                                                                                        |
| Country                                                 | country.name                                           | Dimension                     | Pair with country.code.                                                                                                                                                                                                          |
| —                                                       | country.code                                           | Dimension                     | ISO country code.                                                                                                                                                                                                                |
| —                                                       | budgetCurrency.value                                   | Required support              | v1 minimal-baseline supporting field.                                                                                                                                                                                            |
| Impressions                                             | metric.impressions                                     | Metric                        | Direct.                                                                                                                                                                                                                          |
| Clicks                                                  | metric.clicks                                          | Metric                        | Direct.                                                                                                                                                                                                                          |
| Click-Thru Rate (CTR)                                   | metric.ctr                                             | Metric                        | Direct.                                                                                                                                                                                                                          |
| Cost Per Click (CPC)                                    | metric.cpc                                             | Metric                        | Direct.                                                                                                                                                                                                                          |
| Spend                                                   | metric.totalCost                                       | Metric                        | v1 renames 'spend' to totalCost.                                                                                                                                                                                                 |
| Total ACOS                                              | (derive client-side)                                   | Derived                       | totalCost / NULLIF(sales, 0) or 1 / roas.                                                                                                                                                                                        |
| Total ROAS                                              | metric.roas                                            | Metric                        | Direct.                                                                                                                                                                                                                          |
| 14 Day Total Sales                                      | metric.sales                                           | Metric                        | 14-day window is set on the report request.                                                                                                                                                                                      |
| 14 Day Total Orders (#)                                 | metric.purchases                                       | Metric                        | Equivalent — orders → purchases.                                                                                                                                                                                                 |
| 14 Day Total Units (#)                                  | metric.unitsSold                                       | Metric                        | Direct.                                                                                                                                                                                                                          |
| 14 Day Conversion Rate                                  | metric.purchaseRateOverClicks (or metric.purchaseRate) | Metric                        | purchaseRateOverClicks = purchases/clicks (typical SB UI default); purchaseRate = purchases/impressions. Both included so the warehouse can pick.                                                                                |
| Viewable Impressions                                    | metric.viewableImpressions                             | Metric                        | Direct.                                                                                                                                                                                                                          |
| Cost per 1,000 viewable impressions (VCPM)              | metric.vcpm                                            | Metric                        | Direct.                                                                                                                                                                                                                          |
| View-Through Rate (VTR)                                 | metric.completionRateVideoAd (closest)                 | Metric — definition-dependent | v1 has no metric.vtr or metric.viewThroughRate. Pick metric.completionRateVideoAd (full play) or metric.5secondViewRateVideoAd (5-second view rate) per your downstream definition. Both are in the request for safety.          |
| Click-Through Rate for Views (vCTR)                     | metric.vctr                                            | Metric                        | v1 calls this 'Viewable CTR' — clicks / viewable impressions.                                                                                                                                                                    |
| Video First Quartile Views                              | metric.firstQuartileVideoAd                            | Metric                        | Direct — 25% played.                                                                                                                                                                                                             |
| Video Midpoint Views                                    | metric.midpointVideoAd                                 | Metric                        | Direct — 50% played.                                                                                                                                                                                                             |
| Video Third Quartile Views                              | metric.thirdQuartileVideoAd                            | Metric                        | Direct — 75% played.                                                                                                                                                                                                             |
| Video Complete Views                                    | metric.completeViewsVideoAd                            | Metric                        | Direct.                                                                                                                                                                                                                          |
| Video Unmutes                                           | metric.unmutesVideoAd                                  | Metric                        | Direct.                                                                                                                                                                                                                          |
| 5 Second Views                                          | metric.5secondViewsVideoAd                             | Metric                        | Direct.                                                                                                                                                                                                                          |
| 5 Second View Rate                                      | metric.5secondViewRateVideoAd                          | Metric                        | Direct.                                                                                                                                                                                                                          |
| 14 Day Branded Searches                                 | metric.brandedSearches                                 | Metric                        | Direct — all-attribution branded searches.                                                                                                                                                                                       |
| 14 Day Detail Page Views (DPV)                          | metric.detailPageViews                                 | Metric                        | Direct — all-attribution DPV.                                                                                                                                                                                                    |
| 14 Day New-to-brand Orders (#)                          | metric.newToBrandPurchases                             | Metric                        | Direct.                                                                                                                                                                                                                          |
| 14 Day % of Orders New-to-brand                         | metric.percentOfPurchasesNewToBrand                    | Metric                        | Direct.                                                                                                                                                                                                                          |
| 14 Day New-to-brand Sales                               | metric.newToBrandSales                                 | Metric                        | Direct.                                                                                                                                                                                                                          |
| 14 Day % of Sales New-to-brand                          | metric.percentOfSalesNewToBrand                        | Metric                        | Direct.                                                                                                                                                                                                                          |
| 14 Day New-to-brand Units (#)                           | metric.newToBrandUnitsSold                             | Metric                        | Direct.                                                                                                                                                                                                                          |
| 14 Day % of Units New-to-brand                          | (derive client-side)                                   | Derived                       | v1 has no metric.percentOfUnitsNewToBrand. Compute as newToBrandUnitsSold / NULLIF(unitsSold, 0).                                                                                                                                |
| 14 Day New-to-brand Order Rate                          | metric.newToBrandPurchaseRate                          | Metric                        | Direct.                                                                                                                                                                                                                          |
| Total ACOS - (Click)                                    | (derive client-side)                                   | Derived                       | totalCost / NULLIF(salesFromClicks, 0).                                                                                                                                                                                          |
| Total ROAS - (Click)                                    | metric.roasFromClicks                                  | Metric                        | Direct.                                                                                                                                                                                                                          |
| 14 Day Total Sales - (Click)                            | metric.salesFromClicks                                 | Metric                        | Direct.                                                                                                                                                                                                                          |
| 14 Day Total Orders (#) - (Click)                       | metric.purchasesFromClicks                             | Metric                        | Direct.                                                                                                                                                                                                                          |
| 14 Day Total Units (#) - (Click)                        | metric.unitsSoldFromClicks                             | Metric                        | Direct.                                                                                                                                                                                                                          |
| New-to-brand detail page views                          | metric.newToBrandDetailPageViews                       | Metric                        | Direct — all-attribution NTB DPV.                                                                                                                                                                                                |
| New-to-brand detail page view click-through conversions | metric.newToBrandDetailPageViewsFromClicks             | Metric                        | Click-attributed NTB DPV. Note: this v3 report omits the view-attributed variant; v1 has it (metric.newToBrandDetailPageViewsFromViews) if you want to add it.                                                                   |
| New-to-brand detail page view rate                      | metric.newToBrandDetailPageViewRate                    | Metric                        | Direct — NTB DPV / impressions.                                                                                                                                                                                                  |
| Effective cost per new-to-brand detail page view        | metric.costPerNewToBrandDetailPageView                 | Metric                        | Direct.                                                                                                                                                                                                                          |
| Brand Store page views                                  | metric.brandStorePageViews                             | Metric                        | Direct equivalent — visits to the advertiser's brand store page attributed to an ad interaction. Distinct from metric.detailPageViews (product detail page) — brand stores are the curated brand pages SB ads typically link to. |
| 14 Day ATC                                              | metric.addToCart                                       | Metric                        | Direct — total Add to Cart events.                                                                                                                                                                                               |
| 14 Day ATC Clicks                                       | metric.addToCartFromClicks                             | Metric                        | Click-attributed ATC. Note: this v3 report omits the view-attributed variant; v1 has it (metric.addToCartFromViews).                                                                                                             |
| 14 Day ATCR                                             | metric.addToCartRate                                   | Metric                        | Direct — ATC / impressions.                                                                                                                                                                                                      |
| Effective cost per Add to Cart (eCPATC)                 | metric.costPerAddToCart                                | Metric                        | Direct.                                                                                                                                                                                                                          |
| Branded Searches click-through conversions              | metric.brandedSearchesFromClicks                       | Metric                        | Click-attributed branded searches. Note: this v3 report omits the view-attributed variant; v1 has it (metric.brandedSearchesFromViews).                                                                                          |
| Branded Searches Rate                                   | metric.brandedSearchRate                               | Metric                        | Direct — branded searches / impressions.                                                                                                                                                                                         |
| Effective cost per Branded Search                       | metric.costPerBrandedSearch                            | Metric                        | Direct.                                                                                                                                                                                                                          |
| Long-Term Sales                                         | metric.longTermSales                                   | Metric                        | Direct — projected 12-month sales from incremental NTB shopper engagement driven by the campaign.                                                                                                                                |
| Long-Term ROAS                                          | metric.longTermRoas                                    | Metric                        | Direct — long-term sales / total cost.                                                                                                                                                                                           |

*Yellow rows are derived client-side or have multiple valid mappings.*

## Critical differences from the v3 report

| **Change**                                                                          | **What it means for the request**                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
|-------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Filter on adProduct.value = SPONSORED_BRANDS                                        | The v1 endpoint is shared across all ad products.                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| 'Brand Store page views' is metric.brandStorePageViews — a distinct metric from DPV | v1 distinguishes brand-store pages (the advertiser's curated brand storefront, where SB ads typically click through to) from product detail pages (the regular ASIN page). metric.brandStorePageViews counts visits to brand-store pages; metric.detailPageViews counts visits to product detail pages. v1 also exposes metric.brandStorePageViewsFromClicks / \*FromViews / metric.brandStorePageViewRate / metric.costPerBrandStorePageView if you want the full breakdown.               |
| v3 surfaces ONLY click-attributed variants of NTB DPV / ATC / Branded Search        | The SB Campaign report's NTB DPV breakdown, ATC suite, and Branded Search breakdown all omit the view-attributed variants — only click-attributed columns are shown (e.g. 'NTB DPV click-through conversions' but no 'view-through conversions' counterpart). v1 has both: metric.newToBrandDetailPageViewsFromViews, metric.addToCartFromViews, metric.brandedSearchesFromViews. Add them if you want symmetric click+view breakdowns. The SD Campaign report carries both for comparison. |
| No metric.acos field — applies to BOTH all-attr and click-only                      | Compute totalCost / NULLIF(sales, 0) and totalCost / NULLIF(salesFromClicks, 0).                                                                                                                                                                                                                                                                                                                                                                                                            |
| No 'View-Through Rate' field — definition-dependent                                 | Pick metric.completionRateVideoAd or metric.5secondViewRateVideoAd based on your VTR definition. The template includes both for safety.                                                                                                                                                                                                                                                                                                                                                     |
| No 'conversion rate' field — choose by definition                                   | metric.purchaseRateOverClicks for orders/clicks (typical SB UI default); metric.purchaseRate for purchases/impressions. Both included.                                                                                                                                                                                                                                                                                                                                                      |
| No metric.percentOfUnitsNewToBrand field                                            | v1 has the % for sales and orders, but not units. Derive: newToBrandUnitsSold / NULLIF(unitsSold, 0).                                                                                                                                                                                                                                                                                                                                                                                       |
| Long-Term Sales / ROAS — direct mapping                                             | metric.longTermSales is the 12-month projected sales from incremental NTB shopper engagement; metric.longTermRoas = longTermSales / totalCost. These are forward-looking model estimates, not realized revenue.                                                                                                                                                                                                                                                                             |
| Attribution windows leave the field name                                            | v3's '14 Day' prefix is gone; the 14-day window is set on the report request itself.                                                                                                                                                                                                                                                                                                                                                                                                        |
| 'Spend' → metric.totalCost                                                          | Renamed across all ad products in v1.                                                                                                                                                                                                                                                                                                                                                                                                                                                       |

## Operational notes

-   VTR definition: confirm with consumers whether VTR means completion (full play) or 5-second view. The template carries both metric.completionRateVideoAd AND metric.5secondViewRateVideoAd — drop whichever isn't needed.

-   Conversion rate definition: SB UIs typically use orders/clicks → metric.purchaseRateOverClicks. Drop metric.purchaseRate if you don't need the impressions-denominated alternative.

-   Long-Term Sales / ROAS: these are PROJECTED 12-month metrics derived from NTB shopper-engagement modeling. Treat as forward-looking estimates rather than realized revenue.

-   Adding view-attributed variants: this v3 report omits the view-attributed columns of NTB DPV, ATC, and Branded Search, but v1 has them — metric.newToBrandDetailPageViewsFromViews, metric.addToCartFromViews, metric.brandedSearchesFromViews are all valid additions to symmetrize the breakdowns. Useful if downstream consumers want full click+view comparison alongside the click-only columns the v3 report carries.


-   Derivations to materialize in the warehouse: acos = totalCost / NULLIF(sales, 0); acosClickOnly = totalCost / NULLIF(salesFromClicks, 0); percentOfUnitsNewToBrand = newToBrandUnitsSold / NULLIF(unitsSold, 0). Persist raw inputs alongside the views.

-   Reusing this template: this is the canonical SB campaign-grain template. The SB Campaign Placement report is essentially this report with placementClassification.value added; the SB Keyword report is this report at finer grain (target.value + target.matchType added, country dropped if not needed).
