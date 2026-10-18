# Agent-authored code patterns (sales & traffic)

Illustrative. Adapt to pandas, SQL, Polars, etc.

## Introspection

```python
# df.columns, df.head(), df.dtypes, len(df)
# If JSON: walk keys until tabular ASIN rows appear
```

## COLUMN_MAP

```python
COLUMN_MAP = {
    "asin": "...",
    "sessions": "...",
    "page_views": "... or None",
    "ordered_product_sales": "...",
    "units_ordered": "...",
    "orders": "... or None",
    "unit_session_pct": "... or None",
    "buy_box_pct": "... or None",
    "b2b_ordered_product_sales": "... or None",
    "b2b_units_ordered": "... or None",
}
```

## Source routing

- For `GET_SALES_AND_TRAFFIC_REPORT` JSON, use `scripts/compute_metrics.py`; do not recreate its normalization logic.
- For Seller Central CSV/XLSX exports, introspect the headers and build a format-specific `COLUMN_MAP` before calculating.
- For Data Kiosk JSONL/GraphQL results, inspect the selected fields and normalize that schema separately. Do not treat it as Reports API JSON.

For every route, preserve field presence separately from numeric zero. Validate one currency before monetary aggregation and confirm the date grain before running daily calculations.

## Context-bounded analyzer pattern

For large downloaded reports, use a two-step pattern:

1. A local analyzer reads the raw file and writes a compact metrics artifact such as `sales_traffic_metrics.json`.
2. The agent reads or receives only that compact metrics artifact, capped top-N tables, and validation results, then writes `sales_traffic_analysis.md`.

Do not return raw report rows from tool output. Keep top-N tables small by default and expose row counts separately.

## Portable execution rule

Prefer standard-library Python in sandboxes unless third-party packages are confirmed installed. If `pandas`, `numpy`, or another package import fails, remove that dependency and continue with `json`, `csv`, `datetime`, `statistics`, `collections`, and plain lists/dicts. Never stop at a package-install prerequisite when the input file is available and can be processed with the standard library.

## Aggregation

- If **daily ASIN rows**: `groupby(asin).sum()` on additive measures (sessions, sales, units); **do not** sum percentages — recompute or take period-end per user policy (document).

## Portfolio trend (group by date)

When each row is **ASIN × date** and the user wants **portfolio daily revenue**:

```python
# Pseudologic — use real COLUMN_MAP names
# daily = df.groupby(date_col, as_index=False).agg({
#     sales_col: "sum",
#     sessions_col: "sum",
#     units_col: "sum",
# })
# daily = daily.sort_values(date_col).tail(N)  # N from user
# daily["dod_pct"] = daily[sales_col].pct_change() * 100
# daily["ma7"] = daily[sales_col].rolling(7, min_periods=3).mean()
```

See `time-series-trends.md` for MA deviation, WoW, and DOW logic. Do not assume exactly 14 rows — respect user window and `min_periods`.

## Non-B2B residual revenue

```python
# Only if validated:
# non_b2b_sales = total_sales - b2b_sales  # per row or portfolio after sum
```

Require B2B field presence, matching currency and attribution basis, and `0 <= B2B <= total`. Otherwise, do not subtract—flag the data issue and report total and B2B separately.

## Rankings

- `nlargest` / `ORDER BY` for sessions, sales, b2b_sales independently; merge insights in narrative.

## Anti-patterns

- `reports[0]['report_data']` without proof.
- Skipping the whole report when `b2b_sales` column is absent.
- Averaging **unit session %** across ASINs without session weighting.
- Averaging **Buy Box %** across periods without page-view weighting.
