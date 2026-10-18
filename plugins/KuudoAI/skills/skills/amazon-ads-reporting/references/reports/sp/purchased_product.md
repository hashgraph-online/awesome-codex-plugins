# Amazon Ads API v1 Report Template

*Equivalent to v3 Sponsored_Products_Purchased_product_report — 15 v3 columns mapped to v1 fields*

## Summary

This template replicates the v3 Sponsored Products Purchased Product report on the Amazon Ads API v1 cross-product reporting endpoint (CreateReport). This is a HALO report — its grain pins down the actual 'Purchased ASIN' (convertedProduct.id), so the only metrics compatible with this grain are the \*Halo family. The report exposes which other-brand-SKUs your ads sold alongside the advertised SKU, broken down by the actual purchased ASIN.

Of the 15 v3 columns, 14 map cleanly to v1 fields and 1 ('Retailer') has no v1 equivalent. The 21-field payload was validated against the packaged v1 catalog: zero unknown fields, zero missing required, zero incompatible pairs.

## The convertedProduct.* incompatibility — the structural reason this report is so narrow

**convertedProduct.id (and the entire convertedProduct.* family) is incompatible in v1 with metric.impressions, metric.clicks, and metric.totalCost. The catalog confirms this explicitly — every standard delivery metric lists the convertedProduct.* dimensions in its incompatible_dimension_ids list. This is not arbitrary: impressions, clicks, and spend are events upstream of any conversion; they cannot be partitioned by what the shopper eventually purchased. Only conversion-event metrics (the \*Halo and \*Promoted families) coexist with convertedProduct.id, because those metrics are themselves indexed by purchase events.**

The v3 report hid this constraint by giving you a sparse, halo-only column set. v1 surfaces it via the validator. If you need Impressions/Clicks/Spend/CTR/CPC/ROAS/ACOS at the target grain, run a SEPARATE report without convertedProduct.id and join on (date.value, campaign.id, adGroup.id, target.value, advertisedProduct.id).

## Field list (grouped by role)

### Time dimension (exactly one required)

- `date.value`

### Level-of-detail dimensions

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
- `country.code`
>
- `country.name`
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
>
- `target.value`
>
- `target.matchType`
>
- `convertedProduct.id`
>
- `convertedProductMarketplace.value`

### Required supporting field

- `budgetCurrency.value`

**Halo metrics (the only metrics compatible with convertedProduct.*)**

- `metric.unitsSoldHalo`
>
- `metric.purchasesHalo`
>
- `metric.salesHalo`

### Filter (limits the report to SP)

- `adProduct.value = SPONSORED_PRODUCTS`

## v3 → v1 field mapping

| **v3 Column (Sponsored_Products_Purchased_product)** | **v1 field_id**                   | **Role**         | **Notes**                                                                                                                                                                             |
|------------------------------------------------------|-----------------------------------|------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Date                                                 | date.value                        | Time dimension   | Required time dimension.                                                                                                                                                              |
| Portfolio name                                       | portfolio.name                    | Dimension        | Pair with portfolio.portfolioId.                                                                                                                                                      |
| —                                                    | portfolio.portfolioId             | Dimension        | Stable join key.                                                                                                                                                                      |
| Campaign Name                                        | campaign.name                     | Dimension        | Pair with campaign.id.                                                                                                                                                                |
| —                                                    | campaign.id                       | Dimension        | Stable join key.                                                                                                                                                                      |
| Country                                              | country.name                      | Dimension        | Pair with country.code.                                                                                                                                                               |
| —                                                    | country.code                      | Dimension        | ISO country code.                                                                                                                                                                     |
| Currency                                             | campaign.currencyCode             | Dimension        | Pair with budgetCurrency.value.                                                                                                                                                       |
| Ad Group Name                                        | adGroup.name                      | Dimension        | Pair with adGroup.id.                                                                                                                                                                 |
| —                                                    | adGroup.id                        | Dimension        | Stable join key.                                                                                                                                                                      |
| Retailer                                             | (no v1 equivalent — drop)         | Dimension        | Validator returns retailer.* as unknown. country.code already partitions Amazon's regional marketplaces; cross-retailer reporting is outside Amazon Ads.                             |
| Advertised SKU                                       | advertisedProduct.sku             | Dimension        | Direct equivalent — the SKU that was promoted.                                                                                                                                        |
| Advertised ASIN                                      | advertisedProduct.id              | Dimension        | ASIN is the v1 primary key for advertised product.                                                                                                                                    |
| —                                                    | advertisedProduct.marketplace     | Dimension        | Distinguishes the same ASIN across EU/NA marketplaces.                                                                                                                                |
| Targeting                                            | target.value                      | Dimension        | The keyword, product, or category target expression.                                                                                                                                  |
| Match Type                                           | target.matchType                  | Dimension        | BROAD/PHRASE/EXACT for keywords, EXPANDED/TARGETED for product targets, AUTO match types for auto campaigns. v3 shows '-' when the target is a product target (no match type).        |
| Purchased ASIN                                       | convertedProduct.id               | Dimension        | The KEY DIMENSION of this report — the ASIN the shopper actually purchased after the ad interaction. Can equal advertisedProduct.id (own SKU purchase) or differ (halo SKU purchase). |
| —                                                    | convertedProductMarketplace.value | Dimension        | The marketplace where the conversion event occurred. Required when distinguishing same-ASIN purchases across regional marketplaces.                                                   |
| —                                                    | budgetCurrency.value              | Required support | v1 minimal-baseline supporting field for currency-denominated metrics.                                                                                                                |
| 7 Day Other SKU Units (#)                            | metric.unitsSoldHalo              | Metric           | Halo units sold — units sold for products that were NOT directly promoted in the campaign. The 7-day window is set on the report request.                                             |
| 7 Day Other SKU Orders (#)                           | metric.purchasesHalo              | Metric           | Halo purchases.                                                                                                                                                                       |
| 7 Day Other SKU Sales                                | metric.salesHalo                  | Metric           | Halo sales.                                                                                                                                                                           |

*Yellow row highlights the column with no clean v1 mapping.*

## Critical differences from the v3 report

| **Change**                                                       | **What it means for the request**                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
|------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| This is a HALO report — most metrics are forbidden at this grain | convertedProduct.id (and the rest of the convertedProduct.* family) is incompatible in v1 with metric.impressions, metric.clicks, and metric.totalCost (validator-confirmed via the catalog's incompatible_dimension_ids list). Only the \*Halo metric family — metric.unitsSoldHalo, metric.purchasesHalo, metric.salesHalo — coexists with convertedProduct.id. This is the same constraint that made the v3 version of this report so column-sparse. To add Impressions/Clicks/Spend/CTR/CPC/ROAS at the target grain, run a SEPARATE report WITHOUT convertedProduct.id and join on (date.value, campaign.id, adGroup.id, target.value, advertisedProduct.id). |
| 'Purchased ASIN' is convertedProduct.id                          | The unique identifier of the product attributed to the ad. v1 also exposes a richer family that v3 didn't surface: convertedProduct.brand, .category, .subcategory, .name, .parentProductId, .productGroup. Add any of these to the field list if you want to enrich the halo analysis (e.g. group halo purchases by brand or category) — they'll all be compatible with the halo metrics.                                                                                                                                                                                                                                                                          |
| 'Other SKU' = halo in v1                                         | Direct one-to-one mapping: 7 Day Other SKU Units → metric.unitsSoldHalo, 7 Day Other SKU Orders → metric.purchasesHalo, 7 Day Other SKU Sales → metric.salesHalo. Halo means 'highly relevant non-promoted products from the same brand', which is exactly what v3 calls 'Other SKU'. The 'Promoted' counterparts (unitsSoldPromoted etc.) are also compatible with convertedProduct.id if you want to add them.                                                                                                                                                                                                                                                    |
| Attribution window leaves the field name                         | v3's '7 Day' prefix on the halo metrics is gone in v1. metric.unitsSoldHalo / metric.purchasesHalo / metric.salesHalo are the same logical metrics — the 7-day window is set on the report request itself.                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| No 'Retailer' dimension                                          | Retailer.* fields are unknown to the v1 catalog. country.code already partitions Amazon's regional marketplaces.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| No 'Match Type' for product targets                              | v3 shows '-' for the Match Type when the targeting expression is a product target (e.g. asin="B09XCV2FP4"). v1 returns the actual product-target match modifier in target.matchType (typically EXPANDED or TARGETED for product targets, the AUTO\_\* values for auto campaigns). Expect concrete values where v3 had blanks — clean those up in the warehouse if downstream consumers depend on the v3 '-' convention.                                                                                                                                                                                                                                             |
| Why convertedProductMarketplace.value is included                | Because the same ASIN can be a valid product in multiple Amazon marketplaces (US/CA/MX or DE/IT/ES/FR/UK), and a single advertiser account can route conversions across marketplaces. convertedProductMarketplace.value disambiguates 'a US shopper purchased B0... on amazon.com' from 'a CA shopper purchased B0... on amazon.ca'. Drop it if you operate single-marketplace accounts only.                                                                                                                                                                                                                                                                       |

## Operational notes

- Adding promoted-purchase metrics: metric.unitsSoldPromoted, metric.purchasesPromoted, metric.salesPromoted are also compatible with convertedProduct.id and will populate when convertedProduct.id == advertisedProduct.id (i.e. the shopper bought the actual advertised SKU). Add them if you want a single report that distinguishes own-SKU purchases from halo purchases.

- Enriching halo analysis: convertedProduct.brand, .category, .subcategory, .productGroup, .parentProductId, .name are all available and compatible with the halo metrics. Add convertedProduct.brand to roll halo purchases up by brand (most common analysis), or convertedProduct.parentProductId to roll variations up to the parent ASIN.

- Two-report pattern for full-funnel analysis: pair this report with a target-grain report that drops convertedProduct.* and adds Impressions/Clicks/Spend/CTR/CPC/ROAS. Join on (date.value, campaign.id, adGroup.id, target.value, advertisedProduct.id) — Impressions and Clicks fan out across all halo Purchased ASINs for the same target-day, which is correct, not duplication.
