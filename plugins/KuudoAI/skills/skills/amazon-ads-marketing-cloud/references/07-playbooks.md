# AMC playbooks

Ready-to-run audience and measurement playbooks. Most are distilled from Amazon's instructional queries (IQs) in Amazon Agent Atlas, named below by title and date; A3, A4, and A6 are built here for patterns no IQ covers by name. The text is written in our own words and the SQL is our own, in the dialect `06-amc-sql-rules.md` describes. Every query passed an AMC dry run on a standard sponsored-ads instance on 2026-10-18.

Use these when Atlas isn't connected. When it is, retrieve the named IQ too: it wins on table and column names, but check it against "Known bugs in Atlas IQs" below before copying its SQL.

## Contents

- How to use a playbook
- Known bugs in Atlas IQs
- Audience playbooks: A1 cart abandoners, A2 repeat detail-page viewers, A3 event-window non-buyers, A4 recent purchasers, A5 repeat and high-value buyers (seeds), A6 lapsed repeat buyers, A7 sponsored ads clickers who didn't buy, A8 bought the main product but not the accessory
- Measurement playbooks: M1 lag to purchase, M2 exposure-group overlap, M3 new-to-brand efficiency, M4 repurchase interval, M5 path to purchase, M6 reach and frequency, M7 first- versus last-touch credit, M8 bid boost performance

## How to use a playbook

- **Fill the placeholders** in braces (`{ASIN_1}`, `{CAMPAIGN_ID_1}`). Where an ASIN list is optional, deleting its CTE and filters covers every tracked ASIN; say which scope you chose.
- **Find campaign IDs with an exploratory query**, grouping `amazon_attributed_events_by_traffic_time` or a traffic table by `campaign` and `campaign_id_string`. Per the IQs, the sponsored ads `campaign_id_string` is the ID shown in the console and can differ from the Ads API campaign ID.
- **Audience playbooks** read `_for_audiences` tables, return only `user_id`, and end with `GROUP BY 1`. Dry-run them wrapped in `SELECT COUNT(DISTINCT user_id) FROM (...)`, and size them with the companion tables before creating anything (`06-amc-sql-rules.md`).
- **Measurement playbooks** never output `user_id`, end with a `HAVING COUNT(DISTINCT user_id) >= 100` floor, and carry letter-prefixed labels so results sort after download. Tables keyed on traffic time (the traffic tables and `amazon_attributed_events_by_traffic_time`) need the run to start at least 14 days after the window ends, or late conversions are missing.
- **Paid features.** Amazon's "Conversions all" reference: `conversions_all_for_audiences` can be used for audience creation without a paid subscription; base `conversions_all` needs one for measurement. From June 1 to December 31, 2026, base `conversions_all` and Amazon's other first-party paid datasets are free to query, but the advertiser still enrolls on the instance's Paid features tab. Without it, use `conversions` and say the result covers ad-exposed shoppers only.
- **Multi-marketplace instances:** add `marketplace_id = {MARKETPLACE_ID}` to each CTE (A8 shows it) or run once per marketplace.
- **Dry-run on the user's instance** before any real run. A pass here proves syntax and the standard schema, not that the instance has the same columns, datasets, or data.

## Known bugs in Atlas IQs

Found while distilling (snapshot of 2026-10-18). If you retrieve one of these IQs, don't copy the flawed part.

| IQ | Problem | What the playbook does |
|---|---|---|
| Audience that added to cart but did not purchase | The paid-feature variant's `HAVING COUNT(DISTINCT event_category) = 1` follows `WHERE event_category = 'website'`, so it's always true and removes no purchasers | A1b excludes purchasers explicitly |
| Audience with multiple detail page views | ASINs written as integers; the two CTEs filter different columns (`tracked_item`, `tracked_asin`) | A2 uses strings and one column |
| Audience that clicked sponsored ads but did not purchase | Says sponsored ads expose no campaign ID (both tables now carry `campaign_id_string`); `NOT IN` against buyers that can include a NULL `user_id` empties the audience; no `GROUP BY` | A7 filters by ID, uses `LEFT JOIN … IS NULL`, groups |
| Introduction to AMC lookalike audiences | The "total purchase amount" option filters summed units, not spend; the multi-item flag is split across subscription and order rows | A5 ranks on `total_product_sales` per user |
| Audiences based on high value customer segments | Two ASIN filters active together | A5 uses one |
| New-to-brand customers | Filters promoted `purchases` but sums `total_*` sales; sums spend after a join that can repeat users | M3 keeps one scope and joins spend at campaign grain |
| Time to Conversion | `AND`/`OR` without outer parentheses skips `purchases > 0` when the campaign filter is left at all campaigns | M1 filters cleanly |
| Path to conversion by campaign groups | The conversion-type parameter can end a buyer's path at a detail page view | M5 anchors paths on the first purchase |
| Reach and impression frequency | The omni-channel version groups by `advertiser`, so cross-channel reach isn't de-duplicated; labels sort as text; click rows create a frequency-0 bucket | M6 drops `advertiser`, filters `impressions > 0`, prefixes labels |
| Custom attribution - first touch, - last touch | The code ranks by recency before click priority, though the comments say clicks come first | M7's last touch ranks clicks first and shows how to reproduce the IQ |
| Analyze Sponsored Products and Sponsored Brands bid boost performance | Pairs in-window traffic with in-window conversions (conversion-time table), missing purchases from late-window clicks | M8 reads the traffic-time table |
| Sponsored ads and DSP overlap | `INNER JOIN` drops exposure groups with no purchasers | M2 uses `LEFT JOIN` |

## Audience playbooks

### A1. Cart abandoners

**Atlas source:** "Use case: Audience that added to cart but did not purchase" (April 2024).
**Use when:** retargeting shoppers who carted an ASIN and haven't bought it since. ASIN conversions only; pixel advertisers need another event.
**Window:** about the consideration cycle (M1). The IQ sets none; the run window bounds it.

```sql
WITH asins (asin) AS (
  VALUES
    ('{ASIN_1}'),
    ('{ASIN_2}')
),
carts AS (
  -- engagement from shoppers our ads reached in the prior 28 days, as in the IQ
  SELECT user_id, MAX(event_dt_utc) AS last_cart_dt
  FROM conversions_for_audiences
  WHERE event_subtype = 'shoppingCart'
    AND tracked_asin IN (SELECT asin FROM asins)
    AND user_id IS NOT NULL
  GROUP BY 1
),
purchases AS (
  -- purchases from any shopper, so organic buyers are excluded too
  SELECT user_id, MAX(event_dt_utc) AS last_purchase_dt
  FROM conversions_all_for_audiences
  WHERE event_subtype = 'order'
    AND tracked_asin IN (SELECT asin FROM asins)
    AND user_id IS NOT NULL
  GROUP BY 1
)
SELECT c.user_id
FROM carts c
LEFT JOIN purchases p ON p.user_id = c.user_id
WHERE p.last_purchase_dt IS NULL
   OR c.last_cart_dt > p.last_purchase_dt
GROUP BY 1
```

**Choices to state:**
- *Purchase scope.* Excluding purchases from `conversions_all_for_audiences` is stronger than the IQ, whose `conversions_for_audiences` exclusion misses buyers without a recent ad exposure. Keep it.
- *Per-ASIN match.* As written, buying any listed ASIN ends retargeting. To keep shoppers who bought a different ASIN, add `tracked_asin` to both CTEs, group by `1, 2`, and join on `user_id` and `tracked_asin`. For the opposite (a sibling purchase ends it), filter `purchases` on the brand's full ASIN list.
- *A1b, cart adders with no ad exposure:* read `carts` from `conversions_all_for_audiences` with `exposure_type = 'non-ad-exposed'`; the rest is unchanged.
- *Column.* Some IQs filter on `tracked_item`, which holds the ASIN for Amazon conversions; use whichever the instance's schema confirms.

### A2. Repeat detail-page viewers who didn't buy

**Atlas source:** "Use case: Audience with multiple detail page views" (July 2023).
**Use when:** several views signal intent, and the user wants viewers who haven't bought. ASIN conversions only.

Set the view floor first with this measurement query, then pick the lowest bucket that still gives a usable size (the IQ settles on 3 or more):

```sql
WITH asins (asin) AS (
  VALUES
    ('{ASIN_1}'),
    ('{ASIN_2}')
),
dpv_per_user AS (
  SELECT user_id, SUM(conversions) AS dpv
  FROM conversions
  WHERE event_subtype = 'detailPageView'
    AND tracked_asin IN (SELECT asin FROM asins)
    AND user_id IS NOT NULL
  GROUP BY 1
)
SELECT
  CASE WHEN dpv >= 5 THEN 'e_5plus' WHEN dpv = 4 THEN 'd_4' WHEN dpv = 3 THEN 'c_3'
       WHEN dpv = 2 THEN 'b_2' ELSE 'a_1' END AS dpv_bucket,
  COUNT(DISTINCT user_id) AS users_in_bucket,
  SUM(dpv) AS dpv_in_bucket
FROM dpv_per_user
GROUP BY 1
HAVING COUNT(DISTINCT user_id) >= 100
```

The buckets count views per user across the listed ASINs, the same way the audience does (the IQ buckets per ASIN, so its floor only approximates the audience). Audience:

```sql
WITH asins (asin) AS (
  VALUES
    ('{ASIN_1}'),
    ('{ASIN_2}')
),
views AS (
  SELECT user_id, MAX(event_dt_utc) AS last_view_dt
  FROM conversions_for_audiences
  WHERE event_subtype = 'detailPageView'
    AND tracked_asin IN (SELECT asin FROM asins)
    AND user_id IS NOT NULL
  GROUP BY 1
  HAVING SUM(conversions) >= {MIN_DPV}
),
purchases AS (
  SELECT user_id, MAX(event_dt_utc) AS last_purchase_dt
  FROM conversions_all_for_audiences
  WHERE event_subtype = 'order'
    AND tracked_asin IN (SELECT asin FROM asins)
    AND user_id IS NOT NULL
  GROUP BY 1
)
SELECT v.user_id
FROM views v
LEFT JOIN purchases p ON p.user_id = v.user_id
WHERE p.last_purchase_dt IS NULL
   OR v.last_view_dt > p.last_purchase_dt
GROUP BY 1
```

Viewers far outnumber cart adders, so expect a bigger, less intent-dense audience; a holdout matters more. The IQ cites a 2023 DSP minimum of 2,000 users; check the current minimum.

### A3. Shoppers our ads reached during an event who didn't buy

**Atlas source:** none by name; built here. Related: "Use case: Seasonal advertising exposure off-peak audience", "Use case: Audiences exposed to sponsored ads campaigns".
**Use when:** retargeting after Prime Day or another event. It pins the event dates in the SQL, because a rolling lookback alone drifts off the event as it refreshes.

```sql
WITH brand_asins (asin) AS (
  VALUES
    ('{ASIN_1}'),
    ('{ASIN_2}')
),
-- brand_campaigns (id) AS (VALUES ('{CAMPAIGN_ID_1}'), ('{CAMPAIGN_ID_2}')),   -- only if the instance holds several brands
reached AS (
  SELECT user_id
  FROM sponsored_ads_traffic_for_audiences
  WHERE event_dt_utc >= CAST('{EVENT_START_UTC}' AS TIMESTAMP)
    AND event_dt_utc <  CAST('{EVENT_END_UTC}' AS TIMESTAMP)
    AND user_id IS NOT NULL
    -- AND clicks > 0                               -- clicked, not just reached
    -- AND ad_product_type = 'sponsored_products'
    -- AND campaign_id_string IN (SELECT id FROM brand_campaigns)   -- instance holds several brands
  GROUP BY 1
  UNION ALL
  -- DSP branch: adds shoppers only on instances with DSP data; drop it otherwise
  SELECT user_id
  FROM dsp_impressions_for_audiences
  WHERE impression_dt_utc >= CAST('{EVENT_START_UTC}' AS TIMESTAMP)
    AND impression_dt_utc <  CAST('{EVENT_END_UTC}' AS TIMESTAMP)
    AND user_id IS NOT NULL
  GROUP BY 1
),
purchases AS (
  SELECT user_id
  FROM conversions_all_for_audiences
  WHERE event_subtype = 'order'
    AND tracked_asin IN (SELECT asin FROM brand_asins)
    AND event_dt_utc >= CAST('{EVENT_START_UTC}' AS TIMESTAMP)
    AND user_id IS NOT NULL
  GROUP BY 1
)
SELECT r.user_id
FROM reached r
LEFT JOIN purchases p ON p.user_id = r.user_id
WHERE p.user_id IS NULL
GROUP BY 1
```

- The run window starts on or before `{EVENT_START_UTC}` and runs to the refresh date, so purchases after the event are excluded on each refresh. For an event months back, check how far the audience tables reach; an older event may need `EXTEND_TIME_WINDOW` or be out of reach.
- With a rolling window, the include empties once the window's start passes the event; that's a natural end, but still set a review date. With a fixed window, purchases after its end are never excluded.
- Every timestamp filter is a `_utc` column against UTC bounds written as `'YYYY-MM-DD HH:MM:SS'`. Mixing in an unsuffixed column (`event_dt`, `impression_dt`) shifts the window by the marketplace's UTC offset.

### A4. Recent purchasers (suppression)

**Atlas source:** none by name; built here.
**Use when:** keeping recent buyers out of acquisition spend. The run window is the protection period, typically the repurchase interval from M4.

```sql
WITH asins (asin) AS (
  VALUES
    ('{ASIN_1}')
)
SELECT user_id
FROM conversions_all_for_audiences
WHERE event_subtype = 'order'
  AND tracked_asin IN (SELECT asin FROM asins)
  AND user_id IS NOT NULL
GROUP BY 1
```

Measure a suppression by the spend it saves and whether conversions held, not by the excluded group's own conversion rate. For bought A but not B, use A8.

### A5. Repeat and high-value buyers (lookalike seed or retention)

**Atlas sources:** "Use case: Introduction to AMC lookalike audiences" (November 2023), "Use case: Identify high value customer segments" (October 2023), "Use case: Audiences based on high value customer segments" (October 2023).
**Use when:** building a lookalike seed, or a retention audience, from buyers who already did what you want more of.

Pick one selector per audience and test the others as separate seeds; blending conditions makes a seed too narrow. Orders and Subscribe & Save subscriptions both count as purchases.

```sql
WITH asins (asin) AS (
  VALUES
    ('{ASIN_1}'),
    ('{ASIN_2}')
),
buyer_stats AS (
  SELECT
    user_id,
    COUNT(DISTINCT event_date_utc) AS purchase_days,
    COUNT(DISTINCT tracked_asin) AS distinct_asins,
    MAX(CASE WHEN event_subtype = 'snsSubscription' THEN 1 ELSE 0 END) AS has_sns,
    SUM(total_product_sales) AS sales
  FROM conversions_all_for_audiences
  -- longer lookback: FROM TABLE(EXTEND_TIME_WINDOW('conversions_all_for_audiences', 'P180D', 'P0D'))
  WHERE event_subtype IN ('order', 'snsSubscription')
    AND tracked_asin IN (SELECT asin FROM asins)
    AND user_id IS NOT NULL
  GROUP BY 1
),
ranked AS (
  SELECT user_id, purchase_days, distinct_asins, has_sns,
    PERCENT_RANK() OVER (ORDER BY sales) AS sales_pct_rank
  FROM buyer_stats
)
SELECT user_id
FROM ranked
WHERE purchase_days >= {MIN_PURCHASE_DAYS}
-- or: sales_pct_rank >= {MIN_PCT_RANK}   (0.70 = top 30%)
-- or: distinct_asins >= 2
-- or: has_sns = 1
GROUP BY 1
```

Choose a value threshold from the band companion (base `conversions_all` needs the paid feature; on `conversions` the bands cover ad-exposed buyers only and the currency floors don't carry over):

```sql
WITH asins (asin) AS (
  VALUES
    ('{ASIN_1}')
),
buyer_sales AS (
  SELECT user_id, SUM(total_product_sales) AS sales
  FROM conversions_all
  WHERE event_subtype IN ('order', 'snsSubscription')
    AND total_product_sales > 0
    AND tracked_asin IN (SELECT asin FROM asins)
    AND user_id IS NOT NULL
  GROUP BY 1
),
ranked AS (
  SELECT user_id, sales, PERCENT_RANK() OVER (ORDER BY sales) AS sales_pct_rank
  FROM buyer_sales
)
SELECT
  CASE
    WHEN sales_pct_rank < 0.50 THEN 'a_p00_to_p50'
    WHEN sales_pct_rank < 0.75 THEN 'b_p50_to_p75'
    WHEN sales_pct_rank < 0.90 THEN 'c_p75_to_p90'
    WHEN sales_pct_rank < 0.95 THEN 'd_p90_to_p95'
    ELSE 'e_p95_to_p100'
  END AS value_band,
  COUNT(DISTINCT user_id) AS buyers,
  SUM(sales) AS sales,
  MIN(sales) AS band_floor_sales
FROM ranked
GROUP BY 1
HAVING COUNT(DISTINCT user_id) >= 100
```

- **Seed size:** 500 to 500,000 users is the hard limit; aim for 1,000 to 450,000, because a refresh fails if the seed drifts outside the limit.
- **Expansion:** levels run from most similar (about 300,000 to 1 million) to most broad (about 900,000 to 10 million), varying by region. Start at balanced. If the lookalike lands at the top of its range, tighten the seed; at the bottom, loosen it or pick a broader level.
- **The model copies the seed.** A seed of cart abandoners finds more cart abandoners, so seed only with shoppers who reached the goal.
- Prefer a percentile threshold to a fixed spend figure, which doesn't travel across categories or currencies. Tied sales share a rank, so a "top 30%" cut can return a little more or less.
- The seed's members already buy. Keep them, or recent purchasers (A4), out of the lookalike's spend with a campaign exclusion, unless the lookalike's settings already exclude the seed.

### A6. Lapsed repeat buyers

**Atlas source:** none by name; extends A5.
**Use when:** winning back shoppers with several purchases in a long lookback but none in the current window. Make the run window as long as the lapse threshold (for example 90 days, past the normal repurchase interval from M4); the extension sets how far back to look for earlier purchases.

```sql
WITH asins (asin) AS (
  VALUES
    ('{ASIN_1}')
),
buyers AS (
  SELECT
    user_id,
    COUNT(DISTINCT event_date_utc) AS purchase_days,
    MAX(event_date_utc) AS last_purchase_date
  FROM TABLE(EXTEND_TIME_WINDOW('conversions_all_for_audiences', 'P180D', 'P0D'))
  WHERE event_subtype = 'order'
    AND tracked_asin IN (SELECT asin FROM asins)
    AND user_id IS NOT NULL
  GROUP BY 1
)
SELECT user_id
FROM buyers
WHERE purchase_days >= {MIN_PURCHASE_DAYS}
  AND last_purchase_date < BUILT_IN_PARAMETER('TIME_WINDOW_START')
GROUP BY 1
```

Check the current maximum `EXTEND_TIME_WINDOW` extension in Atlas before relying on 180 days.

### A7. Sponsored ads clickers who didn't buy

**Atlas source:** "Use case: Audience that clicked sponsored ads but did not purchase" (May 2023).
**Use when:** following up on ad engagement rather than shopping events, typically through DSP or Sponsored Display.

```sql
WITH campaigns (campaign_id) AS (
  VALUES ('{CAMPAIGN_ID_1}'), ('{CAMPAIGN_ID_2}')
),
asins (asin) AS (
  VALUES ('{ASIN_1}'), ('{ASIN_2}')
),
clickers AS (
  SELECT user_id, MAX(event_dt_utc) AS last_click_dt
  FROM sponsored_ads_traffic_for_audiences
  WHERE clicks > 0
    AND ad_product_type = 'sponsored_products'                       -- or omit for all sponsored ads
    AND campaign_id_string IN (SELECT campaign_id FROM campaigns)   -- optional
    AND user_id IS NOT NULL
  GROUP BY 1
),
purchases AS (
  SELECT user_id, MAX(event_dt_utc) AS last_purchase_dt
  FROM conversions_all_for_audiences
  WHERE event_subtype = 'order'
    AND tracked_asin IN (SELECT asin FROM asins)
    AND user_id IS NOT NULL
  GROUP BY 1
)
SELECT c.user_id
FROM clickers c
LEFT JOIN purchases p ON p.user_id = c.user_id
WHERE p.last_purchase_dt IS NULL
   OR c.last_click_dt > p.last_purchase_dt
GROUP BY 1
```

- This excludes anyone who bought the advertised ASINs after their last click, ad-driven or not. When the user means "didn't convert from these ads", use the IQ's attributed-only exclusion instead: a `GROUP BY 1` buyer list from `amazon_attributed_events_by_traffic_time_for_audiences WHERE total_purchases > 0` with the same product and campaign filters, kept out with `LEFT JOIN … WHERE b.user_id IS NULL`.
- Variants the IQ lists: impressions instead of clicks; any mix of `sponsored_products`, `sponsored_brands`, and `sponsored_display`.
- Before building, the IQ suggests checking whether shoppers who saw both sponsored ads and DSP convert better (M2).

### A8. Bought the main product but not the accessory

**Atlas source:** "Use case: Audience who purchased main products but not accessories" (October 2025).
**Use when:** cross-selling complements, add-ons, services, upgrades, or consumables to buyers of a core product. The audience's size shows how far the attach rate could grow.

```sql
WITH main_asins (asin) AS (
  VALUES ('{MAIN_ASIN_1}'), ('{MAIN_ASIN_2}')
),
accessory_asins (asin) AS (
  VALUES ('{ACCESSORY_ASIN_1}'), ('{ACCESSORY_ASIN_2}')
),
main_buyers AS (
  SELECT user_id
  FROM conversions_all_for_audiences
  WHERE marketplace_id = {MARKETPLACE_ID}
    AND tracked_asin IN (SELECT asin FROM main_asins)
    AND total_product_sales > 0
    AND user_id IS NOT NULL
  GROUP BY 1
),
accessory_buyers AS (
  SELECT user_id
  FROM conversions_all_for_audiences
  -- longer exclusion lookback: FROM TABLE(EXTEND_TIME_WINDOW('conversions_all_for_audiences', 'P180D', 'P0D'))
  WHERE marketplace_id = {MARKETPLACE_ID}
    AND tracked_asin IN (SELECT asin FROM accessory_asins)
    AND total_product_sales > 0
    AND user_id IS NOT NULL
  GROUP BY 1
)
SELECT m.user_id
FROM main_buyers m
LEFT JOIN accessory_buyers a ON a.user_id = m.user_id
WHERE a.user_id IS NULL
GROUP BY 1
```

- Timing is ignored on purpose: an accessory bought before or after the main product excludes the shopper. Accessory purchases before the run window are invisible, so extend only the accessory CTE (the commented line).
- `marketplace_id` is an integer. Values the IQ lists: US 1, CA 7, MX 771770, BR 526970, UK 3, DE 4, FR 5, IT 35691, ES 44551, NL 328451, SE 704403121, TR 338851, AE 338801, SA 338811, IN 44571, JP 6, AU 111172.
- Conversions cover ASINs tracked to the instance's campaigns, so buyers of an accessory that was never advertised may not be excluded.

## Measurement playbooks

### M1. Lag from attributed touch to purchase

**Atlas source:** "Use case: Time to Conversion" (November 2021).
**Use when:** setting audience lookbacks (A1, A3), promotion length, or how long to wait before reading results.

```sql
WITH asins (asin) AS (
  VALUES ('{ASIN_1}')
),
lags AS (
  SELECT
    COALESCE(ad_product_type, 'dsp') AS ad_product_type,
    COALESCE(traffic_event_subtype, 'unknown') AS traffic_event_subtype,
    user_id, conversion_event_dt_utc,
    SECONDS_BETWEEN(traffic_event_dt_utc, conversion_event_dt_utc) AS lag_seconds
  FROM amazon_attributed_events_by_conversion_time
  WHERE total_purchases > 0
    AND tracked_asin IN (SELECT asin FROM asins)
    AND user_id IS NOT NULL
),
ranked AS (
  -- one row per purchaser and touch type: the first purchase, from its latest touch
  SELECT
    ad_product_type, traffic_event_subtype, user_id, lag_seconds,
    ROW_NUMBER() OVER (
      PARTITION BY ad_product_type, traffic_event_subtype, user_id
      ORDER BY conversion_event_dt_utc, lag_seconds
    ) AS rn
  FROM lags
),
per_user AS (
  SELECT ad_product_type, traffic_event_subtype, user_id, lag_seconds
  FROM ranked
  WHERE rn = 1
),
group_totals AS (
  SELECT ad_product_type, traffic_event_subtype,
    COUNT(DISTINCT user_id) AS group_purchasers
  FROM per_user
  GROUP BY 1, 2
)
SELECT
  p.ad_product_type,
  p.traffic_event_subtype,
  CASE
    WHEN p.lag_seconds < 3600 THEN 'a_under_1h'
    WHEN p.lag_seconds < 86400 THEN 'b_1h_to_24h'
    WHEN p.lag_seconds < 86400 * 3 THEN 'c_1_to_3_days'
    WHEN p.lag_seconds < 86400 * 7 THEN 'd_3_to_7_days'
    WHEN p.lag_seconds <= 86400 * 14 THEN 'e_7_to_14_days'
    ELSE 'f_check_over_14d_or_null'
  END AS lag_bucket,
  COUNT(DISTINCT p.user_id) AS purchasers,
  MAX(g.group_purchasers) AS group_purchasers,
  ROUND(AVG(p.lag_seconds) / 3600.0, 2) AS avg_lag_hours
FROM per_user p
JOIN group_totals g
  ON p.ad_product_type = g.ad_product_type
 AND p.traffic_event_subtype = g.traffic_event_subtype
GROUP BY 1, 2, 3
HAVING COUNT(DISTINCT p.user_id) >= 100
```

- Reads conversion time so recent traffic has had time to convert. The attributed tables report up to 14 days after the last exposure, which caps the lag.
- The lag counts from the last attributed touch, not the first exposure, so it understates consideration time. For replenishable products, M4 is often the better lookback source.
- Within each ad product and touch type, every purchaser sits in exactly one bucket: the lag from the latest attributed touch to their first purchase. Without that, a shopper with several purchases or touches lands in several buckets and cumulative shares can pass 100%.
- After download, share = `purchasers / group_purchasers`; add the shares in bucket order (`a_` to `e_`) and set the lookback near the bucket where the running share covers most purchasers (a `HYPOTHESIS` to state). A bucket under the 100-user floor drops out but stays in `group_purchasers`, so running shares err low, never above 100%.
- Compare shares within a group, not across groups: a purchaser reached through two channels or touch types counts once in each. View-through and click lags differ, and sponsored ads are mostly click-attributed. The check bucket exposes unexpected values.

### M2. Exposure-group overlap

**Atlas source:** "Use case: Sponsored ads and DSP overlap" (October 2022).
**Use when:** asking whether shoppers who see more ad products buy at higher rates, or how much reach each product adds. Descriptive only; incrementality needs a holdout.

```sql
WITH dsp_campaigns (campaign_id_string) AS (
  VALUES ('{DSP_CAMPAIGN_ID_1}'), ('{DSP_CAMPAIGN_ID_2}')
),
sa_campaigns (campaign_id_string) AS (
  VALUES ('{SA_CAMPAIGN_ID_1}'), ('{SA_CAMPAIGN_ID_2}')
),
exposure AS (
  SELECT user_id, 'dsp' AS channel, MIN(impression_dt_utc) AS first_exposure_dt_utc
  FROM dsp_impressions
  WHERE user_id IS NOT NULL
    AND campaign_id_string IN (SELECT campaign_id_string FROM dsp_campaigns)
  GROUP BY 1, 2
  UNION ALL
  SELECT user_id, ad_product_type AS channel, MIN(event_dt_utc) AS first_exposure_dt_utc
  FROM sponsored_ads_traffic
  WHERE user_id IS NOT NULL
    AND impressions > 0
    AND campaign_id_string IN (SELECT campaign_id_string FROM sa_campaigns)
  GROUP BY 1, 2
),
user_groups AS (
  SELECT
    user_id,
    ARRAY_SORT(COLLECT(DISTINCT channel)) AS exposure_group,
    COUNT(DISTINCT channel) AS ad_types_seen,
    MIN(first_exposure_dt_utc) AS first_exposure_dt_utc
  FROM exposure
  GROUP BY 1
),
buyers AS (
  SELECT
    g.user_id,
    SUM(a.total_purchases) AS purchases,
    SUM(a.total_product_sales) AS sales
  FROM user_groups g
  JOIN amazon_attributed_events_by_traffic_time a ON a.user_id = g.user_id
  WHERE a.total_purchases > 0
    AND a.conversion_event_dt_utc > g.first_exposure_dt_utc
    AND (a.campaign_id_string IN (SELECT campaign_id_string FROM dsp_campaigns)
      OR a.campaign_id_string IN (SELECT campaign_id_string FROM sa_campaigns))
  GROUP BY 1
)
SELECT
  g.exposure_group,
  g.ad_types_seen,
  COUNT(DISTINCT g.user_id) AS reached_users,
  COUNT(DISTINCT b.user_id) AS purchasers,
  SUM(b.purchases) AS purchases,
  SUM(b.sales) AS sales
FROM user_groups g
LEFT JOIN buyers b ON b.user_id = g.user_id
GROUP BY 1, 2
HAVING COUNT(DISTINCT g.user_id) >= 100
```

- Groups are the exclusive set of products each shopper saw (`dsp`, `sponsored_products`, `sponsored_brands`, and so on), so add groups for totals. For a strict two-way read, filter the output to the groups made only of `dsp` and `sponsored_products`.
- Purchases count only after the shopper's first exposure, and only when attributed to the scoped campaigns. Delete the campaign lists and filters to run across all campaigns.
- The IQ expects every ad type to advertise the same products over the same period, with at least a week of overlapping flight. Run 14+ days after the window ends.
- Divide purchasers by reached users after download, per marketplace first; pooled marketplaces can manufacture the gap (`04-analyses-and-misreadings.md`). AMC can't measure shoppers who saw neither channel.

### M3. New-to-brand share, sales, and efficiency by campaign

**Atlas source:** "Use case: New-to-brand customers" (August 2021).
**Use when:** comparing campaigns on acquisition, not just total sales.

```sql
WITH campaigns (campaign_id_string) AS (
  VALUES ('{CAMPAIGN_ID_1}'), ('{CAMPAIGN_ID_2}')
),
campaign_cost AS (
  SELECT campaign_id_string, SUM(spend) / 100000000.0 AS ad_spend, COUNT(DISTINCT user_id) AS reached_users
  FROM sponsored_ads_traffic
  WHERE campaign_id_string IN (SELECT campaign_id_string FROM campaigns)
  GROUP BY 1
  UNION ALL
  SELECT campaign_id_string, SUM(total_cost) / 100000.0 AS ad_spend, COUNT(DISTINCT user_id) AS reached_users
  FROM dsp_impressions
  WHERE campaign_id_string IN (SELECT campaign_id_string FROM campaigns)
  GROUP BY 1
),
buyers AS (
  SELECT campaign_id_string, campaign, user_id,
    MAX(CASE WHEN new_to_brand = TRUE THEN 1 ELSE 0 END) AS is_ntb,
    SUM(total_purchases) AS purchases,
    SUM(new_to_brand_total_purchases) AS ntb_purchases,
    SUM(total_product_sales) AS sales,
    SUM(new_to_brand_total_product_sales) AS ntb_sales
  FROM amazon_attributed_events_by_traffic_time
  WHERE total_purchases > 0
    AND campaign_id_string IN (SELECT campaign_id_string FROM campaigns)
    AND user_id IS NOT NULL
  GROUP BY 1, 2, 3
)
SELECT
  b.campaign, b.campaign_id_string,
  MAX(c.ad_spend) AS ad_spend, MAX(c.reached_users) AS reached_users,
  COUNT(DISTINCT b.user_id) AS purchasers,
  COUNT(DISTINCT CASE WHEN b.is_ntb = 1 THEN b.user_id END) AS ntb_purchasers,
  SUM(b.purchases) AS purchases, SUM(b.ntb_purchases) AS ntb_purchases,
  SUM(b.sales) AS sales, SUM(b.ntb_sales) AS ntb_sales
FROM buyers b
LEFT JOIN campaign_cost c ON c.campaign_id_string = b.campaign_id_string
GROUP BY 1, 2
HAVING COUNT(DISTINCT b.user_id) >= 100
```

- New-to-brand means no purchase from the brand in the previous 365 days. The campaigns must target both new and existing customers, or the share means nothing.
- After download: NTB share = `ntb_purchasers / purchasers`, NTB ROAS = `ntb_sales / ad_spend`, NTB ACOS = `ad_spend / ntb_sales × 100`. Report NTB volume next to the share; a high share on low volume isn't scale.
- Totals include brand halo throughout (`total_*`); use `purchases` and `product_sales` columns for promoted ASINs only. Small campaigns fall under the 100-user floor, so pool them into campaign groups.

### M4. Repurchase interval

**Atlas source:** none by name; built here. Related: "Use case: Time to first purchase with extended lookback".
**Use when:** setting replenishment, suppression, and lapse windows. Run over a long window (12 months).

```sql
WITH asins (asin) AS (
  VALUES
    ('{ASIN_1}')
),
purchase_days AS (
  SELECT user_id, event_date_utc, MIN(event_dt_utc) AS first_dt
  FROM conversions_all          -- base table: needs the paid feature; otherwise conversions (ad-exposed shoppers only)
  WHERE event_subtype = 'order'
    AND tracked_asin IN (SELECT asin FROM asins)
    AND user_id IS NOT NULL
  GROUP BY 1, 2
),
ranked AS (
  SELECT
    user_id,
    first_dt,
    ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY first_dt) AS n
  FROM purchase_days
)
SELECT
  CASE
    WHEN SECONDS_BETWEEN(a.first_dt, b.first_dt) < 86400 * 30 THEN 'a_under_30d'
    WHEN SECONDS_BETWEEN(a.first_dt, b.first_dt) < 86400 * 60 THEN 'b_30_to_60d'
    WHEN SECONDS_BETWEEN(a.first_dt, b.first_dt) < 86400 * 90 THEN 'c_60_to_90d'
    ELSE 'd_90d_plus'
  END AS repurchase_gap,
  COUNT(DISTINCT a.user_id) AS repeat_buyers,
  COUNT(*) AS repurchases
FROM ranked a
INNER JOIN ranked b
  ON b.user_id = a.user_id
 AND b.n = a.n + 1
GROUP BY 1
HAVING COUNT(DISTINCT a.user_id) >= 100
```

On `conversions` the gaps cover ad-exposed shoppers only, so treat the distribution as indicative.

### M5. Path to purchase by campaign group

**Atlas source:** "Use case: Path to conversion by campaign groups" (August 2022).
**Use when:** asking which funnel sequences (awareness first, then conversion) go with higher purchase rates or more new-to-brand buyers. It describes paths; it doesn't show what caused them.

```sql
WITH campaign_groups (campaign_id_string, campaign_group) AS (
  VALUES
    ('{CAMPAIGN_ID_1}', 'a_dsp_awareness'),
    ('{CAMPAIGN_ID_2}', 'b_sb_awareness'),
    ('{CAMPAIGN_ID_3}', 'c_sp_conversion')
),
touches AS (
  SELECT i.user_id, g.campaign_group, i.impression_dt_utc AS touch_dt_utc,
    SUM(i.impressions) AS impressions, SUM(i.total_cost) / 100000 AS cost
  FROM dsp_impressions i
  JOIN campaign_groups g ON g.campaign_id_string = i.campaign_id_string
  WHERE i.user_id IS NOT NULL
  GROUP BY 1, 2, 3
  UNION ALL
  SELECT s.user_id, g.campaign_group, s.event_dt_utc AS touch_dt_utc,
    SUM(s.impressions) AS impressions, SUM(s.spend) / 100000000 AS cost
  FROM sponsored_ads_traffic s
  JOIN campaign_groups g ON g.campaign_id_string = s.campaign_id_string
  WHERE s.user_id IS NOT NULL
  GROUP BY 1, 2, 3
),
buyers AS (
  SELECT a.user_id,
    MIN(a.conversion_event_dt_utc) AS first_purchase_dt_utc,
    SUM(a.total_purchases) AS purchases,
    SUM(a.total_product_sales) AS sales,
    SUM(a.new_to_brand_total_purchases) AS ntb_purchases,
    MAX(CASE WHEN a.new_to_brand = TRUE THEN 1 ELSE 0 END) AS ntb_buyer
  FROM amazon_attributed_events_by_traffic_time a
  JOIN campaign_groups g ON g.campaign_id_string = a.campaign_id_string
  WHERE a.total_purchases > 0
    AND a.user_id IS NOT NULL
  GROUP BY 1
),
pre_purchase AS (
  -- every touch for non-buyers; touches up to the first purchase for buyers
  SELECT t.user_id, t.campaign_group,
    MIN(t.touch_dt_utc) AS first_touch_dt_utc,
    SUM(t.impressions) AS impressions, SUM(t.cost) AS cost
  FROM touches t
  LEFT JOIN buyers b ON b.user_id = t.user_id
  WHERE b.user_id IS NULL
    OR t.touch_dt_utc <= b.first_purchase_dt_utc
  GROUP BY 1, 2
),
ordered AS (
  SELECT user_id, campaign_group, impressions, cost,
    ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY first_touch_dt_utc, campaign_group) AS step
  FROM pre_purchase
),
paths AS (
  SELECT user_id,
    ARRAY_SORT(COLLECT(DISTINCT NAMED_ROW('step', step, 'campaign_group', campaign_group))) AS path,
    MAX(CASE WHEN step = 1 THEN campaign_group END) AS path_start,
    MAX(step) AS path_length,
    SUM(impressions) AS impressions, SUM(cost) AS cost
  FROM ordered
  GROUP BY 1
)
SELECT
  p.path, p.path_start, p.path_length,
  COUNT(DISTINCT p.user_id) AS path_users,
  SUM(p.impressions) AS impressions, SUM(p.cost) AS cost,
  COUNT(DISTINCT b.user_id) AS purchasers,
  SUM(b.purchases) AS purchases, SUM(b.sales) AS sales,
  COUNT(DISTINCT CASE WHEN b.ntb_buyer = 1 THEN b.user_id END) AS ntb_purchasers,
  SUM(b.ntb_purchases) AS ntb_purchases
FROM paths p
LEFT JOIN buyers b ON b.user_id = p.user_id
GROUP BY 1, 2, 3
HAVING COUNT(DISTINCT p.user_id) >= 100
```

- A path records each group's first touch before the first purchase; groups seen only afterward drop out. Keep to about four groups, or paths split below the 100-user floor.
- Only purchases attributed to grouped campaigns count, so a shopper who bought through an ungrouped campaign shows as a non-buyer. Purchase rate (`purchasers / path_users`) and ROAS (`sales / cost`) are computed after download. Run 14+ days after the flight ends.
- Common paths are often just the paths of the highest-reach campaigns; compare with exclusive reach (M2) before reading a path as a strategy.

### M6. Reach and impression frequency

**Atlas source:** "Use case: Reach and impression frequency" (September 2021).
**Use when:** checking over- or under-exposure or setting frequency caps. Define the period deliberately (flight, month, week), because frequency depends on it. Conversions come from the traffic-time attributed table, so run 14+ days after the period ends.

```sql
WITH dsp_campaigns (campaign_id_string) AS (
  VALUES ('{DSP_CAMPAIGN_ID_1}'), ('{DSP_CAMPAIGN_ID_2}')
),
sa_campaigns (campaign_id_string) AS (
  VALUES ('{SA_CAMPAIGN_ID_1}'), ('{SA_CAMPAIGN_ID_2}')
),
stacked AS (
  SELECT user_id, impressions
  FROM dsp_impressions
  WHERE user_id IS NOT NULL
    AND campaign_id_string IN (SELECT campaign_id_string FROM dsp_campaigns)
  UNION ALL
  SELECT user_id, impressions
  FROM sponsored_ads_traffic
  WHERE user_id IS NOT NULL
    AND impressions > 0
    AND campaign_id_string IN (SELECT campaign_id_string FROM sa_campaigns)
),
per_user AS (
  SELECT user_id, SUM(impressions) AS impressions
  FROM stacked
  GROUP BY 1
),
conv AS (
  -- purchases attributed to the same campaigns
  SELECT user_id,
    SUM(total_purchases) AS purchases,
    SUM(total_product_sales) AS sales
  FROM amazon_attributed_events_by_traffic_time
  WHERE user_id IS NOT NULL
    AND total_purchases > 0
    AND (campaign_id_string IN (SELECT campaign_id_string FROM dsp_campaigns)
      OR campaign_id_string IN (SELECT campaign_id_string FROM sa_campaigns))
  GROUP BY 1
)
SELECT
  CASE
    WHEN p.impressions = 1 THEN 'a_1'
    WHEN p.impressions = 2 THEN 'b_2'
    WHEN p.impressions = 3 THEN 'c_3'
    WHEN p.impressions = 4 THEN 'd_4'
    WHEN p.impressions = 5 THEN 'e_5'
    WHEN p.impressions = 6 THEN 'f_6'
    WHEN p.impressions = 7 THEN 'g_7'
    WHEN p.impressions = 8 THEN 'h_8'
    WHEN p.impressions = 9 THEN 'i_9'
    ELSE 'j_10_plus'
  END AS frequency_bucket,
  COUNT(DISTINCT p.user_id) AS users_in_bucket,
  SUM(p.impressions) AS impressions_in_bucket,
  COUNT(DISTINCT c.user_id) AS purchasers_in_bucket,
  SUM(COALESCE(c.purchases, 0)) AS purchases_in_bucket,
  SUM(COALESCE(c.sales, 0)) AS sales_in_bucket
FROM per_user p
LEFT JOIN conv c ON p.user_id = c.user_id
GROUP BY 1
HAVING COUNT(DISTINCT p.user_id) >= 100
```

- Summing impressions per user across channels is what de-duplicates reach. For one channel, delete the other branch and its campaign list in `conv`.
- After download: share of users per bucket, average frequency = total impressions / total users, total reach, and purchase rate per bucket = `purchasers_in_bucket / users_in_bucket`. The bucket where purchase rate stops rising is a candidate cap (a `HYPOTHESIS`, given the next point). Lower the top bucket if most users sit well below 10.
- Purchases are brand-level (`total_purchases`, halo included) and attributed to the listed campaigns only; a shopper who bought through another campaign counts as a non-purchaser here.
- Higher buckets hold more engaged shoppers, so conversion rising with frequency is partly selection (`04-analyses-and-misreadings.md`). Small campaigns lose the high-frequency tail to the 100-user floor.

### M7. First-touch versus last-touch credit by campaign

**Atlas sources:** "Use case: Custom attribution - first touch" and "Use case: Custom attribution - last touch" (February 2022), with "Use case: Custom attribution overview".
**Use when:** asking which campaigns open journeys and which close them. It isn't a path analysis (M5), and it won't match console attribution.

```sql
WITH dsp_campaigns (campaign_id_string) AS (
  VALUES ('{DSP_CAMPAIGN_ID_1}'), ('{DSP_CAMPAIGN_ID_2}')
),
sa_campaigns (campaign) AS (
  -- sponsored ads campaigns by exact name, as the IQs join them
  VALUES ('{SA_CAMPAIGN_NAME_1}'), ('{SA_CAMPAIGN_NAME_2}')
),
credit_rules (ad_product_type, touch_type) AS (
  -- touches that can earn credit; add sponsored ads impressions only on purpose
  VALUES
    ('dsp', 'IMP'), ('dsp', 'CLICK'),
    ('sponsored_products', 'CLICK'),
    ('sponsored_brands', 'CLICK'),
    ('sponsored_display', 'CLICK'),
    ('sponsored_television', 'IMP'), ('sponsored_television', 'CLICK')
),
dsp_events AS (
  -- impressions on placements that aren't view-aware, thinned by view rate as the IQ does
  SELECT user_id, campaign_id_string, campaign, request_tag,
    impression_dt_utc AS touch_dt_utc, 'IMP' AS touch_type, impressions, 0 AS clicks
  FROM TABLE(EXTEND_TIME_WINDOW('dsp_impressions', 'P28D', 'P0D'))
  WHERE user_id IS NOT NULL
    AND campaign_id_string IN (SELECT campaign_id_string FROM dsp_campaigns)
    AND NOT COALESCE(supply_source_is_view_aware, TRUE)
    AND NOT COALESCE(placement_is_view_aware, TRUE)
    AND RANDOM() < COALESCE(placement_view_rate, supply_source_view_rate, 1.0)
  UNION ALL
  -- viewable impressions on view-aware placements
  SELECT user_id, campaign_id_string, campaign, impression_id AS request_tag,
    event_dt_utc AS touch_dt_utc, 'IMP' AS touch_type,
    viewable_impressions + unmeasurable_viewable_impressions AS impressions, 0 AS clicks
  FROM TABLE(EXTEND_TIME_WINDOW('dsp_views', 'P28D', 'P0D'))
  WHERE user_id IS NOT NULL
    AND event_type IN ('VIEW', 'SYNTHETIC_VIEW')
    AND campaign_id_string IN (SELECT campaign_id_string FROM dsp_campaigns)
  UNION ALL
  SELECT user_id, campaign_id_string, campaign, request_tag,
    impression_dt_utc AS touch_dt_utc, 'CLICK' AS touch_type, 0 AS impressions, clicks
  FROM TABLE(EXTEND_TIME_WINDOW('dsp_clicks', 'P28D', 'P0D'))
  WHERE user_id IS NOT NULL
    AND campaign_id_string IN (SELECT campaign_id_string FROM dsp_campaigns)
),
dsp_deduped AS (
  -- one touch per served impression: its click if there was one, else its view
  SELECT user_id, campaign_id_string, campaign, touch_dt_utc, touch_type, impressions, clicks,
    ROW_NUMBER() OVER (
      PARTITION BY user_id, campaign_id_string, request_tag
      ORDER BY CASE WHEN touch_type = 'CLICK' THEN 1 ELSE 2 END, touch_dt_utc DESC
    ) AS keep_rank
  FROM dsp_events
),
traffic AS (
  SELECT user_id, campaign_id_string, campaign, 'dsp' AS ad_product_type,
    touch_dt_utc, touch_type, impressions, clicks
  FROM dsp_deduped
  WHERE keep_rank = 1
  UNION ALL
  SELECT user_id, campaign_id_string, campaign, ad_product_type,
    event_dt_utc AS touch_dt_utc,
    CASE WHEN clicks > 0 THEN 'CLICK' ELSE 'IMP' END AS touch_type,
    impressions, clicks
  FROM TABLE(EXTEND_TIME_WINDOW('sponsored_ads_traffic', 'P28D', 'P0D'))
  WHERE user_id IS NOT NULL
    AND campaign IN (SELECT campaign FROM sa_campaigns)
),
eligible AS (
  SELECT t.user_id, t.campaign_id_string, t.campaign, t.ad_product_type, t.touch_dt_utc,
    CASE WHEN t.touch_type = 'CLICK' THEN 1 ELSE 2 END AS touch_priority
  FROM traffic t
  JOIN credit_rules r ON r.ad_product_type = t.ad_product_type AND r.touch_type = t.touch_type
),
cwr AS (
  SELECT conversion_id, campaign_id_string, campaign, user_id, event_dt_utc,
    conversions, total_units_sold, total_product_sales
  FROM conversions_with_relevance
  WHERE event_category = 'purchase'
    AND user_id IS NOT NULL
),
matched AS (
  SELECT c.conversion_id, c.user_id, e.campaign_id_string, e.campaign, e.ad_product_type,
    e.touch_priority, SECONDS_BETWEEN(e.touch_dt_utc, c.event_dt_utc) AS match_age_s,
    c.conversions, c.total_units_sold, c.total_product_sales
  FROM cwr c
  JOIN eligible e ON e.user_id = c.user_id AND e.campaign_id_string = c.campaign_id_string
  WHERE e.ad_product_type = 'dsp'
  UNION ALL
  SELECT c.conversion_id, c.user_id, e.campaign_id_string, e.campaign, e.ad_product_type,
    e.touch_priority, SECONDS_BETWEEN(e.touch_dt_utc, c.event_dt_utc) AS match_age_s,
    c.conversions, c.total_units_sold, c.total_product_sales
  FROM cwr c
  JOIN eligible e ON e.user_id = c.user_id AND e.campaign = c.campaign
  WHERE e.ad_product_type <> 'dsp'
),
ranked AS (
  SELECT campaign_id_string, campaign, ad_product_type, user_id,
    conversions, total_units_sold, total_product_sales,
    -- first touch: oldest qualifying touch; a click only breaks ties (IQ behavior)
    ROW_NUMBER() OVER (PARTITION BY conversion_id ORDER BY match_age_s DESC, touch_priority ASC) AS first_rank,
    -- last touch: clicks before views, then most recent
    ROW_NUMBER() OVER (PARTITION BY conversion_id ORDER BY touch_priority ASC, match_age_s ASC) AS last_rank
  FROM matched
  WHERE match_age_s BETWEEN 0 AND {LOOKBACK_DAYS} * 86400
),
credited AS (
  SELECT 'a_first_touch' AS model, campaign_id_string, campaign, ad_product_type, user_id,
    conversions, total_units_sold, total_product_sales
  FROM ranked
  WHERE first_rank = 1
  UNION ALL
  SELECT 'b_last_touch' AS model, campaign_id_string, campaign, ad_product_type, user_id,
    conversions, total_units_sold, total_product_sales
  FROM ranked
  WHERE last_rank = 1
),
reach AS (
  SELECT campaign_id_string, campaign,
    COUNT(DISTINCT user_id) AS user_reach,
    SUM(impressions) AS impressions,
    SUM(clicks) AS clicks
  FROM traffic
  GROUP BY 1, 2
)
SELECT
  c.model, c.campaign_id_string, c.campaign, c.ad_product_type,
  r.user_reach, r.impressions, r.clicks,
  COUNT(DISTINCT c.user_id) AS users_that_converted,
  SUM(c.conversions) AS conversions,
  SUM(c.total_units_sold) AS units_sold,
  SUM(c.total_product_sales) AS product_sales
FROM credited c
LEFT JOIN reach r ON r.campaign_id_string = c.campaign_id_string AND r.campaign = c.campaign
GROUP BY 1, 2, 3, 4, 5, 6, 7
HAVING COUNT(DISTINCT c.user_id) >= 100
```

- The run window is conversion time; traffic is read 28 days earlier so older touches can earn credit. `{LOOKBACK_DAYS}` is at most 28 for ASIN conversions (raise `P28D` everywhere only for off-Amazon conversions).
- **This isn't standard attribution.** The 28-day lookback, no competition de-duplication, non-viewable sponsored ads impressions, and halo from relevance all produce more conversions than the console or the `amazon_attributed_*` tables. For the closest match, keep the default credit rules, read last touch, and set `{LOOKBACK_DAYS}` to 14.
- To reproduce the IQ's last touch exactly, order `last_rank` by `match_age_s ASC, touch_priority ASC`.
- The thinning step uses `RANDOM()`, so reruns differ slightly. Sponsored ads campaigns join on name, so duplicate names merge; make them unique. Reach covers the extended window, which inflates the conversion-rate denominator.
- Uses the `conversions_with_relevance` custom attribution source; the IQs note no paid feature for it.

### M8. Sponsored Products and Sponsored Brands bid boost performance

**Atlas source:** "Use case: Analyze Sponsored Products and Sponsored Brands bid boost performance" (December 2024).
**Use when:** checking whether traffic matched to a boosted AMC audience earns better CTR, CVR, and cost per click than unmatched traffic in the same campaigns, before raising or removing a boost.

```sql
WITH boosted_campaigns AS (
  SELECT campaign_id_string
  FROM sponsored_ads_traffic
  WHERE matched_behavior_segment_ids IS NOT NULL
    AND ad_product_type IN ('sponsored_products', 'sponsored_brands')
  GROUP BY 1
),
traffic AS (
  SELECT
    s.campaign, s.campaign_id_string, s.ad_product_type, s.user_id, s.event_id,
    CASE WHEN s.matched_behavior_segment_ids IS NULL THEN 'b_unmatched' ELSE 'a_matched' END AS audience_match,
    COALESCE(s.matched_behavior_segment_ids, 'none') AS matched_segment_ids,
    s.impressions, s.clicks, s.spend
  FROM sponsored_ads_traffic s
  WHERE s.ad_product_type IN ('sponsored_products', 'sponsored_brands')
    AND s.user_id IS NOT NULL
    AND s.campaign_id_string IN (SELECT campaign_id_string FROM boosted_campaigns)
),
purchases_by_event AS (
  SELECT traffic_event_id, SUM(purchases) AS purchases, SUM(product_sales) AS product_sales
  FROM amazon_attributed_events_by_traffic_time
  WHERE campaign_id_string IN (SELECT campaign_id_string FROM boosted_campaigns)
    AND purchases > 0
  GROUP BY 1
)
SELECT
  t.campaign, t.campaign_id_string, t.ad_product_type, t.audience_match, t.matched_segment_ids,
  COUNT(DISTINCT t.user_id) AS reached_users,
  SUM(t.impressions) AS impressions,
  SUM(t.clicks) AS clicks,
  SUM(t.spend) / 100000000 AS spend,
  SUM(COALESCE(p.purchases, 0)) AS purchases,
  SUM(COALESCE(p.product_sales, 0)) AS product_sales
FROM traffic t
LEFT JOIN purchases_by_event p ON p.traffic_event_id = t.event_id
GROUP BY 1, 2, 3, 4, 5
HAVING COUNT(DISTINCT t.user_id) >= 100
```

- Compare matched with unmatched within a campaign, after download (CTR, CVR, CPC, ROAS). Numbers won't match the console, so read relative performance only.
- **Matched isn't causal lift.** Boosted segments are chosen because they convert better, and the boost also wins better placements. A holdout or a boost on/off test isolates the effect (`08-activation-and-testing.md`).
- `purchases` and `product_sales` cover promoted ASINs; use the `total_*` columns to include halo. The segment column is a string that may hold several IDs. On the first real run, confirm `a_matched` shows clicks; if it doesn't, click rows don't carry the segment and every purchase lands in `b_unmatched`.
