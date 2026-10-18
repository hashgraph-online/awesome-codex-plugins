# Sponsored Display Matched Target mapping

*Equivalent to v3 Sponsored_Display_Matched_target_report — 16 v3 columns mapped (with daily-vs-aggregate shape note)*

## Summary

This template replicates the v3 Sponsored Display Matched Target report on the Amazon Ads API v1 cross-product reporting endpoint (CreateReport). All 16 v3 columns map cleanly to v1 fields; the only shape difference is daily-vs-aggregate (see below).

The 18-field payload was validated against the packaged v1 catalog: zero unknown fields, zero missing required, zero incompatible pairs.

Aggregate-vs-daily shape

**v3 returns a date-range aggregate: one row per (campaign, target, matched target) covering the entire Start Date → End Date window. v1 returns daily rows. If your downstream consumers expect the v3 aggregate shape, GROUP BY in the warehouse over the requested window and re-derive ratio metrics (CTR = clicks/impressions, CPC = totalCost/clicks, ROAS = sales/totalCost) AFTER aggregation. SUM the count metrics; never average ratios across days.**

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
- `target.value`
>
- `matchedTarget.value`

**Required supporting field**

- `budgetCurrency.value`

**Delivery & conversion metrics**

- `metric.impressions`
>
- `metric.clicks`
>
- `metric.ctr`
>
- `metric.cpc`
>
- `metric.totalCost`
>
- `metric.sales`
>
- `metric.purchases`
>
- `metric.unitsSold`
>
- `metric.roas`

**Filter (limits the report to SD)**

- `adProduct.value = SPONSORED_DISPLAY`

## v3 → v1 field mapping

| **v3 Column (Sponsored_Display_Matched_target)** | **v1 field_id**       | **Role**         | **Notes**                                                                                                                                                                                                                                                                                                                                          |
|--------------------------------------------------|-----------------------|------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Start Date / End Date                            | date.value            | Time dimension   | v3 reports a date-range aggregate using Start Date and End Date columns. v1 always reports daily — set the timeRange on the report request to the desired window and roll up in the warehouse if you need an aggregate row. To preserve v3 shape: GROUP BY campaign.id, target.value, matchedTarget.value and aggregate metrics across the window. |
| Portfolio name                                   | portfolio.name        | Dimension        | Pair with portfolio.portfolioId.                                                                                                                                                                                                                                                                                                                   |
| —                                                | portfolio.portfolioId | Dimension        | Stable join key.                                                                                                                                                                                                                                                                                                                                   |
| Currency                                         | campaign.currencyCode | Dimension        | Pair with budgetCurrency.value.                                                                                                                                                                                                                                                                                                                    |
| Campaign Name                                    | campaign.name         | Dimension        | Pair with campaign.id.                                                                                                                                                                                                                                                                                                                             |
| —                                                | campaign.id           | Dimension        | Stable join key.                                                                                                                                                                                                                                                                                                                                   |
| Targeting                                        | target.value          | Dimension        | The SD targeting expression.                                                                                                                                                                                                                                                                                                                       |
| Matched target                                   | matchedTarget.value   | Dimension        | Direct equivalent — the actual product page where the SD ad served. Tagged as Primary Key in v1. Distinct from target.value: targeting is what you BID on; matched target is the specific page WHERE the impression delivered.                                                                                                                     |
| —                                                | budgetCurrency.value  | Required support | v1 minimal-baseline supporting field.                                                                                                                                                                                                                                                                                                              |
| Impressions                                      | metric.impressions    | Metric           | Direct.                                                                                                                                                                                                                                                                                                                                            |
| Clicks                                           | metric.clicks         | Metric           | Direct.                                                                                                                                                                                                                                                                                                                                            |
| Click-Thru Rate (CTR)                            | metric.ctr            | Metric           | Direct.                                                                                                                                                                                                                                                                                                                                            |
| Cost Per Click (CPC)                             | metric.cpc            | Metric           | Direct.                                                                                                                                                                                                                                                                                                                                            |
| Total advertiser cost                            | metric.totalCost      | Metric           | Slight name variant of v3's 'Spend' column. v1's metric.totalCost is the canonical spend field — validator suggests it as the replacement for any totalAdvertiserCost variant.                                                                                                                                                                     |
| 14 Day Total Sales                               | metric.sales          | Metric           | 14-day window is set on the report request.                                                                                                                                                                                                                                                                                                        |
| Total Return on Advertising Spend (ROAS)         | metric.roas           | Metric           | Direct.                                                                                                                                                                                                                                                                                                                                            |
| 14 Day Total Orders (#)                          | metric.purchases      | Metric           | Equivalent — orders → purchases.                                                                                                                                                                                                                                                                                                                   |
| 14 Day Total Units (#)                           | metric.unitsSold      | Metric           | Direct.                                                                                                                                                                                                                                                                                                                                            |

## Critical differences from the v3 report

| **Change**                                            | **What it means for the request**                                                                                                                                                                                                                                                                                                                                                                                                                                         |
|-------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| v3 reports a date-range aggregate; v1 reports daily   | v3's 'Start Date' and 'End Date' columns indicate the report aggregates the requested window into a single row per (campaign, target, matched target). v1 always reports per-day rows. To reproduce v3 shape, set the timeRange on the report request to the desired window, then GROUP BY (campaign.id, target.value, matchedTarget.value) in the warehouse and aggregate metrics with SUM. ROAS, CTR, CPC need to be re-derived after aggregation (don't average them). |
| 'Total advertiser cost' is metric.totalCost           | Slight naming variant — same metric. v1 standardizes on metric.totalCost across all ad products. Validator-suggested replacement when probing metric.totalAdvertiserCost.                                                                                                                                                                                                                                                                                                 |
| 'Matched target' is matchedTarget.value (Primary Key) | Direct mapping. matchedTarget.value is the actual product page (or audience) where the SD ad delivered an impression. Distinct from target.value (what you bid on) — useful for understanding where SD's audience or category-target matching algorithm placed your ads.                                                                                                                                                                                                  |
| Filter on adProduct.value = SPONSORED_DISPLAY         | Same as the other SD reports.                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| Attribution window leaves the field name              | v3's '14 Day' prefix is gone; window is set on the report request.                                                                                                                                                                                                                                                                                                                                                                                                        |
| No metric.acos field                                  | The v3 report doesn't carry ACOS, so this isn't a column-loss issue here — but if you extend the report, derive ACOS as totalCost / NULLIF(sales, 0).                                                                                                                                                                                                                                                                                                                     |

## Operational notes

-   Aggregation pattern: GROUP BY campaign.id, target.value, matchedTarget.value; SUM(metric.impressions), SUM(metric.clicks), SUM(metric.totalCost), SUM(metric.sales), SUM(metric.purchases), SUM(metric.unitsSold). Then derive: ctr = clicks/NULLIF(impressions,0); cpc = totalCost/NULLIF(clicks,0); roas = sales/NULLIF(totalCost,0).

-   matchedTarget.value cardinality: SD's matched targets can be high-cardinality (one row per ASIN that the audience landed on). The report may produce many rows even for small campaigns. Plan storage accordingly.
