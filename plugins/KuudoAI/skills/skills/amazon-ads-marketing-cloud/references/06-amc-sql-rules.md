# AMC SQL rules for audiences and measurement

AMC SQL is a restricted dialect in a privacy clean room, not warehouse SQL. A query that looks right can fail at parse time or come back empty. This file holds the rules that apply to every query: dialect, audience tables and their sizing companions, and how to size and validate an audience. The ready-to-run queries are the playbooks in `07-playbooks.md`. Writing SQL needs no approval; running it does.

## Contents

- Before you adapt a playbook or IQ
- Dialect rules that break first queries
- Audience tables and their sizing companions
- Sizing and validating an audience query

## Before you adapt a playbook or IQ

1. **Pull the matching IQ when Atlas is available.** Search Amazon Agent Atlas (topic `sql_templates`) for the IQ by title and read the whole document, not one search chunk, as `01-atlas-knowledge-base.md` describes. Don't store Atlas IDs; they change with each reindex. Where the retrieved IQ and this file disagree on a table or column, the IQ wins.
2. **Confirm the columns on this instance.** Column names vary by table and change over time. Check them with the instance's data source listing (`amc_listDataSources`) or Atlas's data-source guides (topic `amc`): "Amazon attributed events", "Sponsored ads traffic", "Conversions table", "Conversions all", "Amazon DSP impressions table", "Amazon DSP clicks table", "Amazon Marketing Cloud data sources", "Paid features overview".
3. **Dry-run before any real run.** A dry run validates the SQL without executing it and needs no ask. Real runs, sizing runs included, go through the approval gate (SKILL.md → Guardrails). Itemize every sizing run in one ask.
4. **Mark the draft's status.** Every playbook in `07-playbooks.md` passed an AMC dry run on a standard sponsored-ads instance (2026-10-18). Queries on base `conversions_all` (A5's value bands, M4) were rejected there as expected without the paid feature, and their `conversions` fallbacks passed. In real runs, measurement queries and the `conversions` sizing companion ran and returned their expected columns, and wrapped audience queries were rejected at delivery, as expected. That covers syntax and the standard schema, not this instance's columns or datasets. Say whether the draft has passed a dry run on this instance; until it has, it's a draft, not a verified query.

## Dialect rules that break first queries

- **Rejected:** `SELECT *`, because every table carries non-viewable columns (name the columns), and `GETDATE()` (use `CAST('today' AS DATE)` or `CURRENT_DATE`).
- **Portable forms:** AMC has rejected outer `ORDER BY`, `LIMIT`, `RIGHT JOIN`, and `||`, though all four ran on a standard instance in October 2026. Write the portable form so the query runs on any instance: sort after download (`ORDER BY` inside `OVER (...)` is fine), `ROW_NUMBER()` in a subquery instead of `LIMIT`, `LEFT JOIN` instead of `RIGHT JOIN`, and `CONCAT` instead of `||`.
- **`user_id` is never output by a measurement query.** Join on it, count it with `COUNT(DISTINCT user_id)`, and use it in subqueries, but never put it in the final `SELECT` of a measurement query, and never filter it against literal values (`WHERE user_id IN (111, 222)` is rejected). Audience queries are the one exception: their final `SELECT` returns only `user_id`.
- **Small groups disappear.** Output rows behind fewer than 100 distinct users are suppressed for most columns. Add `HAVING COUNT(DISTINCT user_id) >= 100` to measurement queries so suppressed groups drop at the source. An empty result can mean "too small to show", not zero. Widen the window or the grouping before reading it as a business result.
- **Cost units:** DSP `total_cost` is in millicents (divide by 100,000). Sponsored ads `spend` is in microcurrency (divide by 100,000,000).
- **Time:** the run's time window bounds what every table returns. Filters in the SQL narrow it further but can't reach outside it. Window bounds are full datetimes (`2026-07-08T00:00:00`). Tables carry `_utc` timestamp columns alongside unsuffixed ones that may use another time zone. Use one convention per query. The playbooks use `_utc` columns, with bounds converted from the marketplace's local event dates.
- **Lists:** define ASIN or campaign lists once as a `VALUES` CTE (`WITH asins (asin) AS (VALUES ('B0...'), ('B0...'))`) and filter with `IN (SELECT asin FROM asins)` or a join. Avoid `ARRAY_CONTAINS` filters, which run slower.
- **Parameters:** `CUSTOM_PARAMETER('name')` must also be declared in the workflow's `inputParameters`, or the run is rejected at execution time. `BUILT_IN_PARAMETER('TIME_WINDOW_START')` returns the run's window start.
- **Longer lookbacks in audience queries:** `TABLE(EXTEND_TIME_WINDOW('conversions_all_for_audiences', 'P180D', 'P0D'))` reads that table 180 days further back than the run window. Check the current maximum extension in Atlas before relying on it.
- **Audience query hygiene:** end the query on executable SQL, not a comment line. The audience IQs end with `GROUP BY 1` for this reason.
- **No `NOT IN` against a nullable column.** If the subquery can return a NULL `user_id`, `NOT IN` keeps no rows and the audience comes back empty. Use `LEFT JOIN … WHERE x.user_id IS NULL`, or filter `user_id IS NOT NULL` inside the subquery.
- **One marketplace at a time.** On an instance that spans marketplaces, add `marketplace_id = {MARKETPLACE_ID}` to each CTE, or run once per marketplace; never read a pooled result alone.

## Audience tables and their sizing companions

Audience queries read the `_for_audiences` variant of a table. Size them with the same logic on the companion table. An ordinary workflow that reads `conversions_all_for_audiences` passes a dry run, but its real run is rejected when results are delivered (`Output from 1 data source(s) ('conversions_all_for_audiences') cannot be received by the customer`). The data source listing flags this up front: that table's `outputChannels` entry has `outputAvailable: false`. On a standard instance it was the only `_for_audiences` table flagged, but every audience playbook reads it, so size on the companions.

| Audience query reads | Sizing companion | What it holds |
|---|---|---|
| `conversions_for_audiences` | `conversions` | Conversion events (orders, detail page views, cart adds, and others in `event_subtype`) from shoppers exposed to the advertiser's ads in the previous 28 days |
| `conversions_all_for_audiences` | `conversions_all` | Adds conversions from shoppers with no recent ad exposure (`exposure_type`). Amazon's "Conversions all" reference: audience creation can use it without a paid subscription; sizing or measuring on base `conversions_all` needs the paid feature (free to query June 1 to December 31, 2026, after enrolling on the Paid features tab). |
| `sponsored_ads_traffic_for_audiences` | `sponsored_ads_traffic` | Sponsored Products, Brands, Display, and TV impressions and clicks (`ad_product_type`) |
| `dsp_impressions_for_audiences` | `dsp_impressions` | DSP impressions. Listed even on sponsored-ads-only instances, where queries on it compile but it holds no DSP data. |
| `dsp_clicks_for_audiences` | `dsp_clicks` | DSP clicks. Same condition. |
| `amazon_attributed_events_by_traffic_time_for_audiences` | `amazon_attributed_events_by_traffic_time` | Ad traffic joined to the conversions attributed to it |

Keep the logic identical between the audience query and its companion. Sizing a `conversions_for_audiences` audience on `conversions_all` counts a different population.

## Sizing and validating an audience query

**Sizing companion** (a real run, so it goes through the approval gate). Paste the audience query inside, renaming each `_for_audiences` table to its companion:

```sql
SELECT COUNT(DISTINCT user_id) AS estimated_audience_size
FROM (
  -- audience query here, with every *_for_audiences table renamed to its companion
) audience
```

- Without the paid feature, base `conversions_all` isn't available, and the run is rejected with `Object 'conversions_all' not found`. Size on `conversions` instead, and say the estimate covers ad-exposed shoppers only, so it can miss in either direction.
- A suppressed or empty result means fewer than about 100 users: too small, not zero.
- Below the minimum: widen the window, add ASINs or the brand's catalog, or drop a restriction such as "reached by our ads". Above a seed's upper bound: tighten the condition, for example more purchase days.
- Compare against the bounds: a lookalike seed takes 500 to 500,000 users, and rule-based audiences have a minimum size (check the current figure). The size AMC reports after the audience is created is the authoritative one; the companion is an estimate.

**Dry-run validation** (no ask needed). Wrap the audience query itself, keeping its `_for_audiences` tables, in the same `SELECT COUNT(DISTINCT user_id) FROM (...)` and submit it with `dryRun: true`. That checks tables, columns, and joins without creating anything. Don't follow it with a real run: that's the delivery rejection described above.
