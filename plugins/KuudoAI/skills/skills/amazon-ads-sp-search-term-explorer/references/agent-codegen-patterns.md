# Agent-authored code patterns (search term mining)

These are **format-agnostic helper patterns** — the brand/generic regex helpers (Patterns 3–4), aggregation pattern (Pattern 5), and sufficiency diagnostics (Pattern 6). For the **MCP-specific** parsing (DictReader against v1 dotted headers, required-column check, partition by `searchTerm.value`), see [`agent-codegen-v1.md`](agent-codegen-v1.md) — that's the entrypoint for code generated against an MCP-downloaded CSV.

Patterns 1 and 2 below are kept as a quick reference; on the MCP path the column names are fixed (see [`column-mapping-hints.md`](column-mapping-hints.md)) so a `COLUMN_MAP` lookup is usually unnecessary.

## Pattern 1 — Load and introspect (sanity check)

```python
# After loading rows from the MCP-downloaded CSV:
# print(rows[0].keys())   # confirm v1 dotted headers present
# print(rows[:3])
# print(len(rows))
```

## Pattern 2 — Explicit COLUMN_MAP (only useful when re-mapping for downstream)

The v1 headers (`searchTerm.value`, `metric.totalCost`, etc.) are stable. Use a `COLUMN_MAP` only if the downstream code expects friendlier names:

```python
COLUMN_MAP = {
    "search_term":  "searchTerm.value",
    "cost":         "metric.totalCost",
    "sales":        "metric.sales",
    "clicks":       "metric.clicks",
    "impressions":  "metric.impressions",
    "orders":       "metric.purchases",
}
```

## Pattern 3 — ASIN-shaped "search terms" (product targeting stream)

```python
import re
# Common modern ASIN (10 chars): B0 + 8 alphanumerics — adjust if user catalog differs
ASIN_LIKE = re.compile(r"^B0[A-Z0-9]{8}$")

def is_asin_shaped(term: str) -> bool:
    s = str(term).strip().upper()
    return bool(ASIN_LIKE.match(s))

# df_keyword = df[~df["search_term"].map(is_asin_shaped)]
# df_asin_stream = df[df["search_term"].map(is_asin_shaped)]
```

Document false positives/negatives (e.g. rare codes that look like ASINs).

## Pattern 4 — Brand vs generic (after excluding ASIN-shaped)

Use **token-boundary** matching for `brand_markers` (list of strings). Same idea as word-boundary regex — avoid substring false positives.

```python
import re

def compile_brand_re(markers: list[str]) -> re.Pattern | None:
    if not markers:
        return None
    parts = "|".join(re.escape(m.lower()) for m in markers if m.strip())
    if not parts:
        return None
    return re.compile(rf"\b({parts})\b")

def is_branded(term: str, brand_re: re.Pattern | None) -> bool:
    if not brand_re:
        return False
    return bool(brand_re.search(str(term).lower()))
```

## Pattern 5 — Aggregate duplicate search terms (keyword stream)

```python
# Filter to keyword stream first if default behavior, then:
# groupby search_term, sum cost/sales/clicks/impressions/orders
# acos = cost / sales if sales > 0 else None
```

## Pattern 6 — Sufficiency diagnostics

```python
# After one row per term:
# median_clicks = terms["metric.clicks"].median()
# window_days from the MCP CreateReport request:
# window_days = (datePeriod.endDate - datePeriod.startDate).days + 1
# This is authoritative — date.value is included in the field list but the
# report request period is the source of truth for window length.
```

For **pre-aggregated** files with no daily breakdown, `window_days` is whatever the export represents (e.g. “last 30 days”) — state that explicitly.

## Pattern 7 — Apply filters with named thresholds

```python
# THRESHOLDS = {
#   "gold_acos_ceiling_pct": ...,
#   "negative_min_spend": ...,
#   "negative_min_clicks_strict": ...,
#   "min_window_days_strict_negatives": ...,
#   "median_clicks_floor": 5,
# }
```

## Anti-patterns

- `pd.DataFrame(reports[0]['report_data'])` without proving that structure exists.
- Computing ACoS on a single row before summing when multiple rows share a search term.
- Keyword **negative** recommendations for **ASIN-shaped** “terms.”
- One combined “gold” table with branded and generic — split per skill template.
- Using **legacy Console** column names (`Customer Search Term`, `7 Day Total Sales`, etc.) for an MCP-downloaded CSV — the v1 path emits dotted IDs (`searchTerm.value`, `metric.totalCost`, …). See [`agent-codegen-v1.md`](agent-codegen-v1.md) for the strict DictReader pattern and required-column check.
