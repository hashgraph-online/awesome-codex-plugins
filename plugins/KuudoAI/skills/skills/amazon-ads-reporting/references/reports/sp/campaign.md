# Amazon Ads API v1 Report Template

*Equivalent to v3 Sponsored_Products_Campaign_report — 24 v3 columns mapped to v1 fields*

## Summary

This template replicates the v3 Sponsored Products Campaign report on the Amazon Ads API v1 cross-product reporting endpoint (CreateReport). Of the 24 v3 columns, 19 map cleanly to v1 fields. Three categories of columns require special handling: 'Retailer' has no v1 equivalent and is dropped; 'Targeting Type' (manual/auto) has no campaign-grain v1 dimension and must be derived from target-grain match types or fetched from the campaign management API; and the four 'Last Year *' YoY columns have no server-side equivalent in v1 — reproduce them by running a second report for the prior-year date range and joining client-side.

The main field list (23 fields) was validated against the packaged v1 catalog: zero unknown fields, zero missing required, zero incompatible pairs.

## Two-report architecture (only if YoY is needed)

If you don't need the v3 'Last Year *' columns, skip Report 2 entirely — the main report alone reproduces 19 of 24 v3 columns. If you do need YoY:

- Report 1 (main): all current-period campaign-grain metrics and dimensions.

- Report 2 (prior year): same shape with timeRange shifted back exactly one year. LEFT JOIN onto Report 1 on campaign.id and (date.value - INTERVAL 1 YEAR). Map metric.impressions → 'Last Year Impressions', metric.clicks → 'Last Year Clicks', metric.totalCost → 'Last Year Spend', metric.cpc → 'Last Year CPC'. Campaigns that didn't exist last year produce NULL — handle in the warehouse layer.

## Report 1 — field list (grouped by role)

### Time dimension (exactly one required)

- `date.value`

### Level-of-detail dimensions

- `portfolio.portfolioId`
>
- `portfolio.name`
>
- `adProduct.value`
>
- `campaign.id`
>
- `campaign.name`
>
- `campaign.deliveryStatus`
>
- `campaign.country`
>
- `country.code`
>
- `country.name`
>
- `campaign.currencyCode`
>
- `campaign.budgetAmount`
>
- `campaign.budgetType`
>
- `campaign.bidStrategy`

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

- `metric.purchases`
>
- `metric.sales`
>
- `metric.roas`

### Filter (limits the report to SP)

- `adProduct.value = SPONSORED_PRODUCTS`

## v3 → v1 field mapping

| **v3 Column (Sponsored_Products_Campaign)** | **v1 field_id**                                     | **Role**                 | **Notes**                                                                                                                                                                                                                                                                                                                                                            |
|---------------------------------------------|-----------------------------------------------------|--------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Date                                        | date.value                                          | Time dimension           | Required time dimension.                                                                                                                                                                                                                                                                                                                                             |
| Portfolio name                              | portfolio.name                                      | Dimension                | Pair with portfolio.portfolioId.                                                                                                                                                                                                                                                                                                                                     |
| —                                           | portfolio.portfolioId                               | Dimension                | Stable join key.                                                                                                                                                                                                                                                                                                                                                     |
| Program Type                                | adProduct.value                                     | Dimension                | Identifies the ad product (SPONSORED_PRODUCTS, SPONSORED_BRANDS, etc.). Also used in the report filter to scope to SP.                                                                                                                                                                                                                                               |
| Campaign Name                               | campaign.name                                       | Dimension                | Pair with campaign.id.                                                                                                                                                                                                                                                                                                                                               |
| —                                           | campaign.id                                         | Dimension                | Stable join key.                                                                                                                                                                                                                                                                                                                                                     |
| Retailer                                    | (no v1 equivalent — drop)                           | Dimension                | Validator returns retailer.* as unknown. country.code already partitions Amazon's regional marketplaces; cross-retailer reporting (e.g. Walmart Connect) is outside Amazon Ads.                                                                                                                                                                                     |
| Country                                     | country.name + campaign.country                     | Dimension                | country.name is the dimension at the impression grain; campaign.country is the campaign-setup country. Both included for redundancy and easier joins. Pair with country.code for ISO joins.                                                                                                                                                                          |
| —                                           | country.code                                        | Dimension                | ISO country code.                                                                                                                                                                                                                                                                                                                                                    |
| Status                                      | campaign.deliveryStatus                             | Dimension                | Replaces the v3 'Status' column. Values include DELIVERING, INACTIVE, ENDED, etc. Note: v1 reports the campaign's CURRENT delivery status, not its status on each historical date.                                                                                                                                                                                   |
| Currency                                    | campaign.currencyCode                               | Dimension                | Three-letter currency code (USD, EUR, GBP, ...). Pair with budgetCurrency.value.                                                                                                                                                                                                                                                                                     |
| Budget Amount                               | campaign.budgetAmount                               | Dimension                | The campaign's total budget. Pair with campaign.budgetType to know whether it's a daily or lifetime budget.                                                                                                                                                                                                                                                          |
| —                                           | campaign.budgetType                                 | Dimension                | DAILY / LIFETIME — disambiguates campaign.budgetAmount.                                                                                                                                                                                                                                                                                                              |
| Targeting Type                              | (no v1 equivalent — drop or derive at target grain) | Dimension                | Validator confirmed: campaign.targetingType, targetingType.value, targetingSetting.value are all unknown. v1 has no campaign-grain manual/auto distinction. To recover this column, descend to the target grain — auto campaigns use AUTO\_\* match types in target.matchType. Aggregate up by checking whether all targets in a campaign have AUTO\_\* match types. |
| Bidding strategy                            | campaign.bidStrategy                                | Dimension                | Direct equivalent.                                                                                                                                                                                                                                                                                                                                                   |
| —                                           | budgetCurrency.value                                | Required support         | v1 minimal-baseline supporting field for currency-denominated metrics.                                                                                                                                                                                                                                                                                               |
| Impressions                                 | metric.impressions                                  | Metric                   | Direct.                                                                                                                                                                                                                                                                                                                                                              |
| Last Year Impressions                       | (no v1 equivalent — second report)                  | Metric — separate report | v1 has NO server-side YoY metrics. Validator returns lastYear\*/previousYear\*/priorPeriod\* as unknown. Run a second report with the SAME fields but a timeRange shifted back exactly one year, then LEFT JOIN on campaign.id and (date.value - INTERVAL 1 YEAR).                                                                                                   |
| Clicks                                      | metric.clicks                                       | Metric                   | Direct.                                                                                                                                                                                                                                                                                                                                                              |
| Last Year Clicks                            | (no v1 equivalent — second report)                  | Metric — separate report | Same as Last Year Impressions — derive from a prior-year report join.                                                                                                                                                                                                                                                                                                |
| Click-Thru Rate (CTR)                       | metric.ctr                                          | Metric                   | Direct.                                                                                                                                                                                                                                                                                                                                                              |
| Spend                                       | metric.totalCost                                    | Metric                   | v1 renames 'spend' to totalCost across all ad products.                                                                                                                                                                                                                                                                                                              |
| Last Year Spend                             | (no v1 equivalent — second report)                  | Metric — separate report | Map to metric.totalCost from the prior-year join.                                                                                                                                                                                                                                                                                                                    |
| Cost Per Click (CPC)                        | metric.cpc                                          | Metric                   | Direct.                                                                                                                                                                                                                                                                                                                                                              |
| Last Year Cost Per Click (CPC)              | (no v1 equivalent — second report)                  | Metric — separate report | Map to metric.cpc from the prior-year join.                                                                                                                                                                                                                                                                                                                          |
| 7 Day Total Orders (#)                      | metric.purchases                                    | Metric                   | Equivalent — orders → purchases. The 7-day window is set on the report request.                                                                                                                                                                                                                                                                                      |
| Total Advertising Cost of Sales (ACOS)      | (derive client-side)                                | Derived                  | v1 has no metric.acos. Compute as totalCost / NULLIF(sales, 0) or `1 / roas`.                                                                                                                                                                                                                                                                                          |
| Total Return on Advertising Spend (ROAS)    | metric.roas                                         | Metric                   | Direct.                                                                                                                                                                                                                                                                                                                                                              |
| 7 Day Total Sales                           | metric.sales                                        | Metric                   | Window is set on the report request, not in the field name.                                                                                                                                                                                                                                                                                                          |

*Yellow rows highlight columns that don't have a clean one-to-one v1 mapping (no v1 equivalent, derived client-side, or recovered via a separate report).*

## Critical differences from the v3 report

| **Change**                                                              | **What it means for the request**                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
|-------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| No 'Last Year *' metrics — period-over-period requires a second report | v1 has no server-side YoY. The validator returns lastYearImpressions, previousYearImpressions, priorPeriodImpressions, etc. as unknown. To reproduce v3's Last Year Impressions / Clicks / Spend / CPC columns, run a second CreateReport with the same fields but a timeRange shifted back exactly one year and LEFT JOIN on campaign.id and (date.value - INTERVAL 1 YEAR). Campaigns that didn't exist last year will be NULL — handle in the warehouse layer.                                          |
| No 'Targeting Type' dimension at the campaign grain                     | v1 has no campaign.targetingType, targetingType.value, or targetingSetting.value (validator-confirmed unknown). Manual vs auto is encoded structurally — auto campaigns use AUTO\_\* match types in target.matchType. Recovering 'Targeting Type' at the campaign grain requires a target-grain query and aggregation: a campaign is 'Auto' if all its targets have AUTO\_\* match types, otherwise 'Manual'. If you only need this label occasionally, fetch it from the campaign management API instead. |
| No 'Retailer' dimension                                                 | Retailer.* fields are unknown to the v1 catalog. country.code already partitions Amazon marketplaces; non-Amazon retailers (e.g. Walmart Connect) live outside the Amazon Ads API.                                                                                                                                                                                                                                                                                                                        |
| No metric.acos                                                          | Validator suggests metric.roas. `ACOS = totalCost / NULLIF(sales, 0)` or `1 / roas` — derive in the warehouse.                                                                                                                                                                                                                                                                                                                                                                                                 |
| 'Spend' → metric.totalCost                                              | Renamed across all ad products in v1.                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| Status semantics shift                                                  | v3 'Status' was the campaign's status on each historical day (often static). v1 campaign.deliveryStatus reports the campaign's CURRENT delivery status, not its status on each historical date. If you need historical status snapshots, capture them at ingest time and persist them in your warehouse — v1 does not provide a historical status timeline.                                                                                                                                                |
| Budget Amount needs Budget Type for context                             | campaign.budgetAmount is the raw number. campaign.budgetType (DAILY / LIFETIME) tells you what that number means. Ingest both; render together in any UI.                                                                                                                                                                                                                                                                                                                                                  |
| Attribution window leaves the field name                                | metric.sales / metric.purchases are the same logical 7-day metrics — the 7-day window is set on the report request, not encoded per-field.                                                                                                                                                                                                                                                                                                                                                                 |

## Operational notes



- Targeting Type recovery: if you need this column without descending to target grain, call the campaign-list operation and join on campaign.id. The campaign object's targetingType field carries 'AUTO' or 'MANUAL' directly. Don't try to derive it from bid strategy — bid strategy is independent of targeting type.

- Status historicity: if you need a true historical campaign status timeline (not just the current status), capture campaign.deliveryStatus daily at ingest time and persist as a slowly-changing dimension in your warehouse. v1 reports the live status only.

- ACOS derivation: in the warehouse, persist the raw inputs (totalCost, sales) and expose ACOS as a view: `acos = totalCost / NULLIF(sales, 0)`.
