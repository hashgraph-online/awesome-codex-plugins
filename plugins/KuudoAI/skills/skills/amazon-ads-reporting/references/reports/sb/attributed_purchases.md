# Sponsored Brands Attributed Purchases mapping

*Equivalent to v3 Sponsored_Brands_Attributed_Purchases_report — 18 v3 columns mapped (with attribution-type restructured into metric variants)*

## Summary

This template replicates the v3 Sponsored Brands Attributed Purchases report on the Amazon Ads API v1 cross-product reporting endpoint (CreateReport). The grain is (date, campaign, purchased ASIN) with attribution split — but unlike v3 where 'Attribution type' is a row-level dimension, v1 encodes click-vs-view in metric variants, so the v1 layout is wider rows with click-only and total columns side-by-side.

Of the 18 v3 columns: 14 map cleanly to v1 fields, 1 is restructured (Attribution type → metric variants), and 3 are derived client-side (% of Sales NTB, % of Units NTB are derived; ACOS isn't applicable to this report).

The 17-field payload was validated against the packaged v1 catalog: zero unknown fields, zero missing required, zero incompatible pairs.

Why this report has the same constraints as SP Purchased Product

Like the SP Purchased Product report, this is a HALO-style report whose grain pins down the actual purchased ASIN (convertedProduct.id). v1's catalog explicitly marks metric.impressions, metric.clicks, and metric.totalCost as INCOMPATIBLE with the convertedProduct.\* family — and that's why the v3 SB Attributed Purchases report omits Impressions/Clicks/Spend/CTR/CPC. v3 hid this constraint by giving you a sparse 18-column conversion-only report; v1 surfaces it via the validator.

**This report's primary use case is decomposition: showing which Purchased ASINs an SB campaign drove sales for, and how much of that was new-to-brand. v1 covers this use case completely — but with one validator-detected restriction (the percent-of-sales NTB metric is blocked when grouping by purchased ASIN). The percent-of-purchases NTB variant survives, and the missing percentages are simple downstream divisions.**

Layout difference: attribution type

In v3, 'Attribution type' is a column with values like 'Total' (all-attribution = click + view) and 'Click'. Each combination of (date, campaign, attribution type, purchased ASIN) is one row. So a single (date, campaign, ASIN) appears in TWO rows — one with the totals, one with the click-only numbers.

In v1 the same data is one wider row per (date, campaign, ASIN) with both metric.sales (total) and metric.salesFromClicks (click-only) populated together. This is the same shape v3 reports like SB Keyword and SB Search Term use for their click-only variants. It is generally cleaner for downstream warehouses — joins and pivots get simpler when click-vs-view is on the same row.

If your downstream consumers absolutely require the v3 long-format shape, rebuild it in the warehouse: take the v1 rows once with `attribution_type` 'Total' and `col_value` from `sales`, append them (UNION ALL) to the same rows with `attribution_type` 'Click' and `col_value` from `salesFromClicks`. Same for purchases and unitsSold.

## Field list (grouped by role)

**Time dimension (exactly one required)**

- `date.value`

**Level-of-detail dimensions**

- `campaign.id`
>
- `campaign.name`
>
- `campaign.currencyCode`
>
- `campaign.costType`
>
- `convertedProduct.id`
>
- `convertedProductMarketplace.value`

**Required supporting field**

- `budgetCurrency.value`

**All-attribution conversion (14-day)**

- `metric.sales`
>
- `metric.purchases`
>
- `metric.unitsSold`

**Click-only attribution variants**

- `metric.salesFromClicks`
>
- `metric.purchasesFromClicks`
>
- `metric.unitsSoldFromClicks`

**New-to-brand**

- `metric.newToBrandSales`
>
- `metric.newToBrandPurchases`
>
- `metric.newToBrandUnitsSold`
>
- `metric.percentOfPurchasesNewToBrand`

**Filter (limits the report to SB)**

- `adProduct.value = SPONSORED_BRANDS`

## v3 → v1 field mapping

| **v3 Column (Sponsored_Brands_Attributed_Purchases)** | **v1 field_id**                                      | **Role**         | **Notes**                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
|-------------------------------------------------------|------------------------------------------------------|------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Date                                                  | date.value                                           | Time dimension   | Required time dimension.                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| Currency                                              | campaign.currencyCode                                | Dimension        | Pair with budgetCurrency.value.                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| Campaign Name                                         | campaign.name                                        | Dimension        | Pair with campaign.id.                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| —                                                     | campaign.id                                          | Dimension        | Stable join key.                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| Attribution type                                      | (NOT a dimension in v1 — encoded in metric variants) | —                | v1 has NO 'attribution type' dimension. Click-vs-view attribution is encoded in the \*FromClicks vs \*FromViews metric variants instead. The v3 layout (one row per attribution type with metrics per row) becomes a v1 layout (one row per date+campaign+convertedProduct.id with click and total columns side-by-side). v3's 'View' attribution = (total - clicks-only); v1 surfaces both metric.sales (total = click+view) and metric.salesFromClicks (click-only) on the same row. |
| Purchased ASIN                                        | convertedProduct.id                                  | Dimension        | Direct equivalent — Primary Key for the converted-product family.                                                                                                                                                                                                                                                                                                                                                                                                                      |
| —                                                     | convertedProductMarketplace.value                    | Dimension        | REQUIRED supporting field for convertedProduct.id (validator-confirmed). Also disambiguates same-ASIN purchases across marketplaces.                                                                                                                                                                                                                                                                                                                                                   |
| Cost type                                             | campaign.costType                                    | Dimension        | CPC / CPM / vCPM. Native dimension in v1.                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| —                                                     | budgetCurrency.value                                 | Required support | v1 minimal-baseline supporting field.                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| 14 Day Total Sales                                    | metric.sales                                         | Metric           | All-attribution sales. The 14-day window is set on the report request.                                                                                                                                                                                                                                                                                                                                                                                                                 |
| 14 Day Total Orders (#)                               | metric.purchases                                     | Metric           | Equivalent — orders → purchases.                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| 14 Day Total Units (#)                                | metric.unitsSold                                     | Metric           | Direct.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| 14 Day New-to-brand Sales                             | metric.newToBrandSales                               | Metric           | Direct.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| 14 Day New-to-brand Orders (#)                        | metric.newToBrandPurchases                           | Metric           | Direct.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| 14 Day New-to-brand Units (#)                         | metric.newToBrandUnitsSold                           | Metric           | Direct.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| 14 Day % of Sales New-to-brand                        | (derive client-side)                                 | Derived          | metric.percentOfSalesNewToBrand is INCOMPATIBLE with convertedProduct.id (validator-confirmed). Compute as newToBrandSales / NULLIF(sales, 0).                                                                                                                                                                                                                                                                                                                                         |
| 14 Day % of Orders New-to-brand                       | metric.percentOfPurchasesNewToBrand                  | Metric           | DIRECT — and notably, this percent IS compatible with convertedProduct.id (validator-confirmed). The sales-NTB% variant isn't, but the purchases-NTB% variant is.                                                                                                                                                                                                                                                                                                                      |
| 14 Day % of Units New-to-brand                        | (derive client-side)                                 | Derived          | v1 has no metric.percentOfUnitsNewToBrand anywhere. Compute as newToBrandUnitsSold / NULLIF(unitsSold, 0).                                                                                                                                                                                                                                                                                                                                                                             |
| 14 Day Total Sales - (Click)                          | metric.salesFromClicks                               | Metric           | Click-only attribution.                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| 14 Day Total Orders (#) - (Click)                     | metric.purchasesFromClicks                           | Metric           | Click-only attribution.                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| 14 Day Total Units (#) - (Click)                      | metric.unitsSoldFromClicks                           | Metric           | Click-only attribution.                                                                                                                                                                                                                                                                                                                                                                                                                                                                |

*Red row: Attribution type is restructured into metric variants. Yellow rows are derived client-side.*

## Critical differences from the v3 report

| **Change**                                                                           | **What it means for the request**                                                                                                                                                                                                                                                                                                                                                                                                                                         |
|--------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| v3 'Attribution type' is NOT a dimension in v1                                       | v1 has no attribution-type dimension. Click-vs-view is encoded in metric variants: metric.salesFromClicks vs metric.salesFromViews vs metric.sales (total = click + view). The v3 layout (one row per attribution type) becomes a v1 layout (one row per (date, campaign, convertedProduct.id) with click-only and total metrics on the same row). v3's 'View' attribution = total − click — derive in the warehouse if downstream consumers expect three rows per group. |
| This is a HALO-style report — most metrics are forbidden at this grain               | Same constraint as the SP Purchased Product report: convertedProduct.id is incompatible with metric.impressions, metric.clicks, and metric.totalCost. Only conversion-event metrics (sales, purchases, unitsSold and their \*FromClicks / \*FromViews / \*NewToBrand variants) coexist with convertedProduct.id.                                                                                                                                                          |
| Filter on adProduct.value = SPONSORED_BRANDS                                         | The v1 endpoint is shared across all ad products.                                                                                                                                                                                                                                                                                                                                                                                                                         |
| Only ONE of the percent-NTB metrics survives convertedProduct.id                     | metric.percentOfPurchasesNewToBrand IS compatible with convertedProduct.id; metric.percentOfSalesNewToBrand is INCOMPATIBLE (validator-confirmed). All Halo and Promoted variants of the SALES NTB% are also incompatible. Workaround: derive percent-of-sales-NTB downstream as newToBrandSales / NULLIF(sales, 0). The percent-of-units-NTB has no v1 field anywhere — derive as newToBrandUnitsSold / NULLIF(unitsSold, 0).                                            |
| convertedProduct.id requires convertedProductMarketplace.value as a supporting field | Validator surfaced this requirement on probe — convertedProductMarketplace.value must be in the field list when convertedProduct.id is. It also serves a useful purpose: distinguishing same-ASIN purchases across regional marketplaces.                                                                                                                                                                                                                                 |
| Attribution windows leave the field name                                             | v3's '14 Day' prefix is gone; the 14-day window is set on the report request.                                                                                                                                                                                                                                                                                                                                                                                             |

## Operational notes

-   Reproducing the v3 long-format attribution shape: UNION two SELECT statements over the v1 wide-format result. v3 'Total' = metric.sales; v3 'Click' = metric.salesFromClicks; v3 'View' (if present in your downstream consumers) = metric.sales − metric.salesFromClicks (or use metric.salesFromViews directly — also compatible with convertedProduct.id).

-   Adding metric.salesFromViews / metric.purchasesFromViews / metric.unitsSoldFromViews: all three are compatible with convertedProduct.id and provide the view-only column directly. Add them if your warehouse prefers explicit view metrics over (total − clicks).

-   Enriching with brand/category: convertedProduct.brand, convertedProduct.category, convertedProduct.subcategory, convertedProduct.parentProductId, convertedProduct.productGroup are all compatible with this metric set. Add convertedProduct.brand to roll halo purchases up by brand.

-   Derivations: percentOfSalesNewToBrand = newToBrandSales / NULLIF(sales, 0); percentOfUnitsNewToBrand = newToBrandUnitsSold / NULLIF(unitsSold, 0). Persist raw inputs alongside the derived views.
