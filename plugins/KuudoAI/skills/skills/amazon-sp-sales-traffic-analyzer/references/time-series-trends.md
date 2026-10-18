# Time-series trends (daily Sales & Traffic)

Use only when the artifact is validated as **daily grain** (one or more rows per calendar day). A weekly or monthly period can have a date field without supporting DoD, MA7, weekday/weekend, or seven-day WoW calculations.

## When this section applies

- **Portfolio-by-day:** If rows are ASIN × day, **sum** ordered product sales, sessions, units (and B2B columns if present) **per day** before trend metrics. Document that double-counting is avoided by summing only at ASIN grain then grouping by date.
- **Already portfolio daily:** One row per day — use directly after validating date parsing.

## Prerequisites

- Map **`date`** (or start/end — user may need to derive a single date)
- Map **`ordered_product_sales`** (or equivalent revenue for the trend — name in report)
- Optional: **sessions**, **units**, **unit session %** for parallel trend tables or narrative

## Analysis window

- Default narrative: **last N calendar days** (legacy example **N = 14** — **user overrides**).
- Require **minimum** days for MA/WoW (e.g. **≥ 3** for rolling MA with `min_periods`; **≥ 14** for classic last-7 vs prior-7 WoW). State when the window is shorter.

## Core computations (agent-authored)

1. **Sort** by date ascending; drop rows with invalid dates.
2. **Optional data-quality filter** — e.g. exclude days with **zero sessions** if the user agrees it flags incomplete downloads — **document if applied** (do not apply silently by default).
3. **Day-over-day (DoD):** `pct_change` on revenue (and optionally sessions) × 100.
4. **Moving average:** e.g. **7-day** rolling mean of revenue (`min_periods` 3–7 per user); label **MA7** in output.
5. **Deviation from MA:** `(revenue - MA7) / MA7 * 100` where `MA7 > 0`.
6. **Anomaly flags (tunable):** Default to **±20%** deviation from MA7 unless the user chooses another threshold. Record the selected threshold in the metrics output and report.
7. **Week-over-week (WoW):** If ≥ 14 days in window: sum revenue **last 7** vs **prior 7**; `pct_change`. If < 14 days, compute partial WoW or mark N/A.
8. **Weekday vs weekend:** Classify `dayofweek >= 5` as weekend; compare **average daily revenue** weekend vs weekday; report **gap %** vs weekday average.
9. **Day-of-week pattern:** Mean revenue by `Monday` … `Sunday` (calendar order in table); call out best/worst **day name**.

## Optional B2B on trends

- If **B2B sales** column exists and is summed per day, add **B2B revenue trend** or **B2B share of day** time series in the same section.

## Deliverables (markdown; charts optional)

- **Table:** date, revenue, optional sessions/units, DoD %, MA7, deviation %, anomaly label
- **Summary bullets:** period total, daily average, peak day, trough day, WoW %, weekday vs weekend gap, anomaly count
- **Day-of-week table:** avg revenue per weekday name
- **Charts** (if tooling allows): line chart revenue + MA7; optional bar chart DOW averages — not required for skill compliance

## Pitfalls

- Mixing **currencies** or **marketplaces** in one series without user confirmation.
- Rolling MA on **non-contiguous** dates — consider reindexing to calendar or flag gaps.
- ASIN-level daily file: portfolio trend must **group by date first**.
