# Amazon Ads API v1 Report Template

*Equivalent to v3 Sponsored_Products_Targeting_report — 25 v3 columns mapped to v1 fields across two reports*

## Summary

This template replicates the v3 Sponsored Products Targeting report on the Amazon Ads API v1 cross-product reporting endpoint (CreateReport). Twenty-three v3 columns map cleanly to v1 field_ids on a single targeting-grain report. Two columns require special handling: 'Retailer' has no v1 equivalent and is dropped, and 'Top-of-search Impression Share' is incompatible with portfolio/adGroup/country dimensions in v1 and must be requested as a separate campaign-level report and joined back to the main report on (date.value, campaign.id).

Both report payloads were validated against the packaged v1 catalog: zero unknown fields, zero missing required, zero incompatible pairs.

## Two-report architecture

The validator caught that metric.topOfSearchImpressionShare is INCOMPATIBLE with portfolio.portfolioId, portfolio.name, adGroup.id, adGroup.name, country.code, country.name — and REQUIRES adProduct.value and advertiserAccount.id. This means the metric only lives at the campaign grain in v1. Build two reports and union them in the warehouse:

- Report 1 (main): all 23 mappable v3 columns at the date × portfolio × campaign × ad group × country × target × match-type grain.

- Report 2 (supplemental): metric.topOfSearchImpressionShare at the date × campaign grain. Join to Report 1 on (date.value, campaign.id) — TOS impression share will repeat across all targets within the same campaign-day.

## Report 1 — field list (grouped by role)

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
- `adGroup.id`
>
- `adGroup.name`
>
- `country.code`
>
- `country.name`
>
- `target.value`
>
- `target.matchType`

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
- `metric.purchaseRate`
>
- `metric.purchaseRateOverClicks`
>
- `metric.salesPromoted`
>
- `metric.salesHalo`
>
- `metric.unitsSoldPromoted`
>
- `metric.unitsSoldHalo`
>
- `metric.roas`

### Filter (limits the report to SP)

- `adProduct.value = SPONSORED_PRODUCTS`

## v3 → v1 field mapping

| **v3 Column (Sponsored_Products_Targeting)** | **v1 field_id**                                        | **Role**                 | **Notes**                                                                                                                                                                                                                                                                                                          |
|----------------------------------------------|--------------------------------------------------------|--------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Date                                         | date.value                                             | Time dimension           | Required time dimension.                                                                                                                                                                                                                                                                                           |
| Portfolio name                               | portfolio.name                                         | Dimension                | Pair with portfolio.portfolioId.                                                                                                                                                                                                                                                                                   |
| —                                            | portfolio.portfolioId                                  | Dimension                | Stable join key.                                                                                                                                                                                                                                                                                                   |
| Currency                                     | campaign.currencyCode                                  | Dimension                | Currency the campaign was set up in. Pair with budgetCurrency.value.                                                                                                                                                                                                                                               |
| Campaign Name                                | campaign.name                                          | Dimension                | Pair with campaign.id.                                                                                                                                                                                                                                                                                             |
| —                                            | campaign.id                                            | Dimension                | Stable join key — also used to join the supplemental TOS report.                                                                                                                                                                                                                                                   |
| Country                                      | country.name                                           | Dimension                | Use country.code for ISO joins.                                                                                                                                                                                                                                                                                    |
| —                                            | country.code                                           | Dimension                | ISO country code.                                                                                                                                                                                                                                                                                                  |
| Ad Group Name                                | adGroup.name                                           | Dimension                | Pair with adGroup.id.                                                                                                                                                                                                                                                                                              |
| —                                            | adGroup.id                                             | Dimension                | Stable join key.                                                                                                                                                                                                                                                                                                   |
| Retailer                                     | (no v1 equivalent — drop)                              | Dimension                | v1 has no retailer dimension. The validator returns it as unknown. country.code already partitions Amazon vs other regional marketplaces; if cross-retailer reporting is needed (e.g. Walmart Connect), use a separate platform's API.                                                                             |
| Targeting                                    | target.value                                           | Dimension                | The keyword, product, or category target expression.                                                                                                                                                                                                                                                               |
| Match Type                                   | target.matchType                                       | Dimension                | BROAD / PHRASE / EXACT for keywords; EXPANDED / TARGETED for product targets; AUTO match types for auto campaigns.                                                                                                                                                                                                 |
| —                                            | budgetCurrency.value                                   | Required support         | v1 minimal-baseline supporting field for currency-denominated metrics.                                                                                                                                                                                                                                             |
| Impressions                                  | metric.impressions                                     | Metric                   | Direct.                                                                                                                                                                                                                                                                                                            |
| Top-of-search Impression Share               | metric.topOfSearchImpressionShare                      | Metric — separate report | INCOMPATIBLE with portfolio.\*, adGroup.\*, country.\* dimensions. Must be requested in a SEPARATE campaign-level report (see Report 2) and joined on date.value + campaign.id. Requires adProduct.value and advertiserAccount.id in the field list.                                                               |
| Clicks                                       | metric.clicks                                          | Metric                   | Direct.                                                                                                                                                                                                                                                                                                            |
| Click-Thru Rate (CTR)                        | metric.ctr                                             | Metric                   | Direct.                                                                                                                                                                                                                                                                                                            |
| Cost Per Click (CPC)                         | metric.cpc                                             | Metric                   | Direct.                                                                                                                                                                                                                                                                                                            |
| Spend                                        | metric.totalCost                                       | Metric                   | v1 renames 'spend' to totalCost.                                                                                                                                                                                                                                                                                   |
| Total Advertising Cost of Sales (ACOS)       | (derive client-side)                                   | Derived                  | v1 has no metric.acos. Validator suggests metric.roas as replacement. Compute as totalCost / NULLIF(sales, 0) or `1 / roas`.                                                                                                                                                                                         |
| Total Return on Advertising Spend (ROAS)     | metric.roas                                            | Metric                   | Direct.                                                                                                                                                                                                                                                                                                            |
| 7 Day Total Sales                            | metric.sales                                           | Metric                   | Window is set on the report request, not in the field name.                                                                                                                                                                                                                                                        |
| 7 Day Total Orders (#)                       | metric.purchases                                       | Metric                   | Equivalent — orders → purchases.                                                                                                                                                                                                                                                                                   |
| 7 Day Total Units (#)                        | metric.unitsSold                                       | Metric                   | Direct.                                                                                                                                                                                                                                                                                                            |
| 7 Day Conversion Rate                        | metric.purchaseRate (or metric.purchaseRateOverClicks) | Metric                   | v1 has no 'conversionRate' field; validator suggests purchaseRate. purchaseRate = purchases / impressions. purchaseRateOverClicks = purchases / clicks. Pick whichever matches your v3 definition (most SP UIs use orders/clicks → purchaseRateOverClicks). The template includes both so you can pick downstream. |
| 7 Day Advertised SKU Units (#)               | metric.unitsSoldPromoted                               | Metric                   | Promoted units sold.                                                                                                                                                                                                                                                                                               |
| 7 Day Other SKU Units (#)                    | metric.unitsSoldHalo                                   | Metric                   | Halo units sold.                                                                                                                                                                                                                                                                                                   |
| 7 Day Advertised SKU Sales                   | metric.salesPromoted                                   | Metric                   | Promoted sales.                                                                                                                                                                                                                                                                                                    |
| 7 Day Other SKU Sales                        | metric.salesHalo                                       | Metric                   | Halo sales.                                                                                                                                                                                                                                                                                                        |

*Yellow rows highlight columns that don't have a clean one-to-one v1 mapping (no v1 equivalent, derived client-side, or split across reports).*

## Critical differences from the v3 report

| **Change**                                                    | **What it means for the request**                                                                                                                                                                                                                                                                                                                                                          |
|---------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Top-of-search Impression Share forces a SECOND report         | metric.topOfSearchImpressionShare is incompatible with portfolio.\*, adGroup.\*, country.\* and requires adProduct.value + advertiserAccount.id. The v3 report had it on the targeting grain; in v1 you cannot get target-grain rows AND TOS impression share in one query. Run two reports and join on (date.value, campaign.id) — TOS impression share is a campaign-level metric in v1. |
| No 'Retailer' dimension                                       | The v3 'Retailer' column has no v1 equivalent — the validator returns retailer.* as unknown. country.code already partitions Amazon marketplaces; cross-retailer (e.g. Walmart Connect) data lives outside Amazon Ads.                                                                                                                                                                    |
| No metric.acos field                                          | The catalog rejects metric.acos and suggests metric.roas. ACOS is derived as totalCost / NULLIF(sales, 0) or `1 / roas` in the warehouse.                                                                                                                                                                                                                                                    |
| No 'conversion rate' field — choose your definition           | v1 exposes metric.purchaseRate (purchases / impressions) and metric.purchaseRateOverClicks (purchases / clicks). Most legacy SP UIs computed 7-day conversion rate as orders / clicks, which is purchaseRateOverClicks. The template includes both and lets you pick downstream.                                                                                                           |
| 'Spend' → metric.totalCost                                    | Renamed across all ad products in v1.                                                                                                                                                                                                                                                                                                                                                      |
| Attribution window moves out of the field name                | The v3 '7 Day' prefix on Sales/Orders/Units/Conversion Rate doesn't appear in v1 field names. metric.sales is the same logical metric — the 7-day window is configured on the report request, not encoded per-field.                                                                                                                                                                       |
| Targeting expression and match type are split into two fields | v3 had 'Targeting' (expression) + 'Match Type' (modifier). v1 keeps the same split: target.value (the keyword/product/category) + target.matchType (BROAD/PHRASE/EXACT for keywords, EXPANDED/TARGETED for product targets, the AUTO modifiers for auto campaigns).                                                                                                                        |
| Currency is exposed two ways                                  | v3 had a single 'Currency' column. v1 offers campaign.currencyCode (the campaign's currency) and budgetCurrency.value (required supporting field). They normally agree but populate independently — keep both for joining and validation.                                                                                                                                                  |

## Operational notes



- Conversion-rate semantics: pick metric.purchaseRateOverClicks if your downstream consumers expect orders/clicks (legacy SP UI default). Pick metric.purchaseRate if they expect purchases/impressions. Including both lets the warehouse decide.

- ACOS derivation in the warehouse: `acos = totalCost / NULLIF(sales, 0)`. Persist the raw inputs alongside the computed view.

- Joining the two reports: use a LEFT JOIN from Report 1 onto Report 2 on (date.value, campaign.id). Report 2 produces one row per campaign-day; the value will fan out across all (target, match type, ad group) rows in Report 1 — TOS impression share is a campaign-level metric, so this fan-out is correct, not a bug.
