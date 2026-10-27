# Amazon Ads API v1 Report Template

*Equivalent to v3 Sponsored_Products_Video_report — 25 v3 columns mapped to v1 fields*

## Summary

This template replicates the v3 Sponsored Products Video report on the Amazon Ads API v1 cross-product reporting endpoint (CreateReport). Field names changed substantially: 'spend' is now totalCost, ACOS is no longer a native metric (derive from ROAS or totalCost/sales), the '7 Day' prefix is dropped from sales/orders/units (the attribution window is set on the report request), and the SP-specific endpoint is replaced by a single endpoint that filters on adProduct.value = SPONSORED_PRODUCTS.

The field list below was validated against the packaged v1 catalog: zero unknown fields, zero missing required, zero incompatible pairs.

## Field list (grouped by role)

### Time dimension (exactly one required)

- `date.value`

### Level-of-detail dimensions

- `campaign.id`
>
- `campaign.name`
>
- `adGroup.id`
>
- `adGroup.name`
>
- `ad.id`
>
- `ad.name`
>
- `ad.format`
>
- `country.code`
>
- `country.name`
>
- `advertisedProduct.id`
>
- `advertisedProduct.sku`
>
- `advertisedProduct.marketplace`

### Required supporting field

- `budgetCurrency.value`

### Delivery metrics

- `metric.impressions`
>
- `metric.clicks`
>
- `metric.ctr`
>
- `metric.cpc`
>
- `metric.totalCost`

### Attributed conversion metrics

- `metric.sales`
>
- `metric.purchases`
>
- `metric.unitsSold`
>
- `metric.salesPromoted`
>
- `metric.salesHalo`
>
- `metric.purchasesPromoted`
>
- `metric.purchasesHalo`
>
- `metric.unitsSoldPromoted`
>
- `metric.unitsSoldHalo`
>
- `metric.roas`

### Video metrics

- `metric.5secondViewsVideoAd`
>
- `metric.5secondViewRateVideoAd`

### Filter (not a field — limits the report to SP)

- `adProduct.value = SPONSORED_PRODUCTS`

## v3 → v1 field mapping

| **v3 Column (Sponsored_Products_Video_report)** | **v1 field_id**               | **Role**         | **Notes**                                                                                                                                        |
|-------------------------------------------------|-------------------------------|------------------|--------------------------------------------------------------------------------------------------------------------------------------------------|
| Date                                            | date.value                    | Time dimension   | Required time dimension.                                                                                                                         |
| Campaign Name                                   | campaign.name                 | Dimension        | Pair with campaign.id (primary key).                                                                                                             |
| —                                               | campaign.id                   | Dimension        | Stable join key.                                                                                                                                 |
| Ad Group Name                                   | adGroup.name                  | Dimension        | Pair with adGroup.id.                                                                                                                            |
| —                                               | adGroup.id                    | Dimension        | Stable join key.                                                                                                                                 |
| Country                                         | country.name                  | Dimension        | Use country.code for ISO joins.                                                                                                                  |
| —                                               | country.code                  | Dimension        | ISO country code.                                                                                                                                |
| Video Details                                   | ad.name + ad.format           | Dimension        | v1 has no single 'Video Details' field. ad.format identifies video creatives; ad.name is the creative label. Add ad.id as the stable PK.         |
| —                                               | ad.id                         | Dimension        | Creative-level primary key.                                                                                                                      |
| Advertised SKU                                  | advertisedProduct.sku         | Dimension        | Direct equivalent.                                                                                                                               |
| Advertised ASIN                                 | advertisedProduct.id          | Dimension        | ASIN is the v1 primary key for advertised product.                                                                                               |
| —                                               | advertisedProduct.marketplace | Dimension        | Distinguishes the same ASIN across EU/NA marketplaces.                                                                                           |
| —                                               | budgetCurrency.value          | Required support | v1 minimal-baseline supporting field for currency-denominated metrics.                                                                           |
| Impressions                                     | metric.impressions            | Metric           | Direct.                                                                                                                                          |
| Clicks                                          | metric.clicks                 | Metric           | Direct.                                                                                                                                          |
| Click-Thru Rate (CTR)                           | metric.ctr                    | Metric           | Direct.                                                                                                                                          |
| Cost Per Click (CPC)                            | metric.cpc                    | Metric           | Direct.                                                                                                                                          |
| Spend                                           | metric.totalCost              | Metric           | v1 renames 'spend' to totalCost across all ad products.                                                                                          |
| 7 Day Total Sales                               | metric.sales                  | Metric           | v1 attribution window is set on the report request, not encoded in the field name. Configure 7-day window via the report's attribution settings. |
| 7 Day Total Orders (#)                          | metric.purchases              | Metric           | Equivalent — orders → purchases.                                                                                                                 |
| 7 Day Total Units (#)                           | metric.unitsSold              | Metric           | Direct.                                                                                                                                          |
| 7 Day Advertised SKU Sales                      | metric.salesPromoted          | Metric           | Promoted = sales of the SKU directly advertised.                                                                                                 |
| 7 Day Other SKU Sales                           | metric.salesHalo              | Metric           | Halo = sales of other SKUs from the same brand.                                                                                                  |
| 7 Day Advertised SKU Orders (#)                 | metric.purchasesPromoted      | Metric           | Promoted purchases.                                                                                                                              |
| 7 Day Other SKU Orders (#)                      | metric.purchasesHalo          | Metric           | Halo purchases.                                                                                                                                  |
| 7 Day Advertised SKU Units (#)                  | metric.unitsSoldPromoted      | Metric           | Promoted units sold.                                                                                                                             |
| 7 Day Other SKU Units (#)                       | metric.unitsSoldHalo          | Metric           | Halo units sold.                                                                                                                                 |
| Total Return on Advertising Spend (ROAS)        | metric.roas                   | Metric           | Direct.                                                                                                                                          |
| Total Advertising Cost of Sales (ACOS)          | (derive client-side)          | Derived          | v1 has no metric.acos — the validate API explicitly returns 'unknown_fields' for it. Compute as totalCost / sales (or `1 / roas`).                 |
| 5 Second View                                   | metric.5secondViewsVideoAd    | Metric           | Direct.                                                                                                                                          |
| 5 Second View Rate                              | metric.5secondViewRateVideoAd | Metric           | Direct.                                                                                                                                          |

## Critical differences from the v3 report

| **Change**                                               | **What it means for the request**                                                                                                                                                                                                                      |
|----------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| No metric.acos field                                     | v1 does not expose ACOS as a native metric. The catalog's validate endpoint flags metric.acos as unknown and suggests metric.roas as the replacement. `ACOS = totalCost / sales` (or `1 / roas`) — derive in the consumer.                                 |
| 'Spend' is renamed to metric.totalCost                   | Across all ad products in v1. The legacy 'spend' field name is unknown to v1 and is replaced by totalCost (CURRENCY type).                                                                                                                             |
| Attribution window moves out of the field name           | The v3 '7 Day' prefix on Sales/Orders/Units does not exist in v1 field names. metric.sales is the same logical metric — the 7-day window is configured on the report request itself.                                                                   |
| No 'Video Details' dimension                             | v1 exposes the creative through the ad.\* dimension family: ad.id (primary key), ad.name (creative label), ad.format (video / image / etc.), ad.size.                                                                                                  |
| Advertised product is its own dimension family           | advertisedProduct.id (= ASIN), advertisedProduct.sku, advertisedProduct.marketplace — the marketplace dimension lets a single ASIN be split across EU country marketplaces.                                                                            |
| Filter on adProduct.value, not on a separate report type | The v3 endpoint had a separate /sp/video report. In v1 there is one cross-product report endpoint; restrict to Sponsored Products with the adProduct.value filter (use 'sponsoredProducts.adProduct' is wrong — the correct field is adProduct.value). |
| accessRequestedAccounts uses advertiser account IDs      | Pass amzn1.ads-account.g.\* IDs, NOT legacy numeric profile IDs. Resolve a profileId via the advertiser-account query operation first.                                                                                                                           |
| Asynchronous report creation                             | CreateReport returns a report ID. Retrieve it with bounded polling or the host's task/wait facility, then download every completed part.                                                                                                            |

## Operational notes



- ACOS derivation: in the destination warehouse, compute `acos = totalCost / NULLIF(sales, 0)`. Store as a view alongside the raw metric.totalCost and metric.sales columns rather than mixing derived columns into the load.

- Adding the 'campaign budget type' or 'placement' to the grain is supported — extend query.fields with campaign.budgetType, placement.value, etc., and re-run validate.
