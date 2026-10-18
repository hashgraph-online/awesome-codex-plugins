# Sales & traffic report — output template

Markdown-first. Write the final report to `sales_traffic_analysis.md`. Use **N/A (reason)** for missing sections, but populate all available sections with computed values.

## 1) Context and data quality

- Source, date range, marketplace, currency, grain (ASIN/parent/**daily vs snapshot**), row count
- Which key columns were mapped; any columns dropped or unreliable
- If both **static** and **daily trend** views are included, state how totals relate (e.g. trend window vs full file range)

## 2) Daily trends — revenue, traffic, conversion (conditional)

**Include when:** the source is validated as daily grain and the user asked for trends, or the file is explicitly a daily export. A date field on a weekly or monthly row does not make it daily data.

- Analysis window (e.g. last 14 days) and whether portfolio totals are **aggregated by date** from ASIN rows
- Summary: period revenue, daily average, best/worst **calendar days**, WoW change (last 7 vs prior 7) if enough history
- **DoD table** (or compact list): date, revenue, optional sessions, DoD % — with direction called out
- **7-day moving average** of revenue (or user-chosen span); **anomaly days** vs MA using **stated threshold** (e.g. ±20%)
- **Day-of-week pattern:** average revenue by weekday; weekday vs weekend gap %
- Optional: line chart (revenue + MA) and DOW bar chart if the environment supports it
- Optional: parallel trend for **sessions** or **units**; optional **B2B revenue** per day if columns exist

Method details: `references/time-series-trends.md`.

## 3) Portfolio summary — traffic

- Total sessions (and page views if available) — clarify if **full file** or **same window as §2**
- Portfolio **unit session %** or equivalent if provided; else derived units/sessions with caveat
- Optional: buy box % weighted by page views — **state method**

## 4) Portfolio summary — sales

- Ordered product sales (total), units, orders (if available)
- Optional: average selling price proxy (sales/units) with guard for zero units

## 5) B2B and non-B2B (only if B2B fields exist)

- B2B revenue, non-B2B residual (only if `total − B2B` is validated), B2B % of revenue
- B2B units vs non-B2B units if columns support it
- Short interpretation: mix context, **not** a mandate to "go B2B"
- Optional: simple visualization if user requests (pie/bar) — otherwise table is enough
- Optional: tie to **§2** if daily B2B series computed

## 6) ASIN highlights — traffic and conversion

- Top ASINs by **sessions** (or page views) with sales and conversion column
- ASINs with **high sessions, weak unit session %** (or low units/sessions) — candidate merchandising/retail readiness issues
- ASINs with **strong conversion, moderate traffic** — candidate demand drivers

## 7) ASIN highlights — sales

- Top ASINs by revenue and by units
- Optional: Pareto / concentration (top 10% ASINs share of revenue)

## 8) B2B-specific tables (only if B2B columns exist)

- Top ASINs by **B2B revenue** with B2B share %
- **B2B-heavy** ASINs (B2B share above user threshold, e.g. >50%)
- **B2B growth opportunities** — high total revenue but low B2B share (thresholds in `b2b-segments.md`)

## 9) Recommendations

- Mix: short-term **trend/anomaly** follow-ups, traffic/retail, conversion, and **only if applicable** Amazon Business (pricing, quantity tiers, profile)
- Each bullet references metrics from this run
