# Agent-authored patterns — v1 MCP CSV (dotted field IDs)

Use this file for reports produced by **`allv1_AdsApiv1CreateReport`** and downloaded via MCP. CSV headers are **exactly** the v1 field IDs from `mcp-workflow.md` (e.g. `searchTerm.value`, `metric.totalCost`). **Do not** use legacy Advertising Console column names (`Customer Search Term`, `7 Day Total Sales`, …) — those are a different export.

## Validate expected headers

```python
import csv

with open(csv_path, encoding="utf-8") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

REQUIRED_V1 = {
    "date.value",
    "searchTerm.value",
    "metric.totalCost",
    "metric.sales",
    "metric.clicks",
    "metric.impressions",
    "metric.purchases",
    "budgetCurrency.value",
}
if not rows:
    raise ValueError("Empty CSV")
missing = REQUIRED_V1 - set(rows[0].keys())
if missing:
    raise ValueError(f"Missing v1 columns: {missing}")
```

## Partition PAT ASINs vs customer queries (`searchTerm.value`)

```python
import re

ASIN = re.compile(r"^B0[A-Z0-9]{8}$")

def is_asin_shaped(v: str) -> bool:
    return bool(ASIN.match(str(v).strip().upper()))

customer_rows = [r for r in rows if not is_asin_shaped(r["searchTerm.value"])]
asin_rows = [r for r in rows if is_asin_shaped(r["searchTerm.value"])]
```

Run gold / rising / **keyword** negatives on **`customer_rows`** only. Summarize **`asin_rows`** under product-targeting / PAT (not keyword negatives).

## Aggregate by search term (v1 metrics)

v1 search-term reports are typically **multi-row per `searchTerm.value`** (date × campaign × ad group). **Always aggregate** before segment rules.

```python
from collections import defaultdict

agg = defaultdict(
    lambda: {
        "metric.totalCost": 0.0,
        "metric.sales": 0.0,
        "metric.clicks": 0,
        "metric.impressions": 0,
        "metric.purchases": 0,
    }
)

for r in customer_rows:
    t = r["searchTerm.value"]
    agg[t]["metric.totalCost"] += float(r["metric.totalCost"] or 0)
    agg[t]["metric.sales"] += float(r["metric.sales"] or 0)
    agg[t]["metric.clicks"] += int(float(r["metric.clicks"] or 0))
    agg[t]["metric.impressions"] += int(float(r["metric.impressions"] or 0))
    agg[t]["metric.purchases"] += int(float(r["metric.purchases"] or 0))

# Derived (after aggregation):
# acos = cost / sales if sales > 0 else None
# cvr = orders / clicks if clicks > 0 else None
```

For **brand/generic** regex and **threshold** application, use the sibling references in this skill ([`agent-codegen-patterns.md`](agent-codegen-patterns.md) Patterns 3–4, [`segment-rules.md`](segment-rules.md), [`threshold-elicitation.md`](threshold-elicitation.md)) — those are format-agnostic; only the **column keys** here are v1-specific.

## Anti-patterns (v1)

- Treating **`metric.cost`**, **`metric.spend`**, **`metric.spendAmount`** as cost — **rejected** by the v1 endpoint; use **`metric.totalCost`**.
- Expecting **`metric.sales7d`**, **`metric.purchases7d`**, or other suffixed attribution fields on this CreateReport path — **not supported** here; use **`metric.sales`** / **`metric.purchases`** and disclose default attribution.
- Expecting **`keyword.text`**, **`keyword.value`**, **`keyword.matchType`** in the export — **not available** as v1 output fields in current catalog for this pattern.
- Renaming v1 headers to legacy “friendly” names before aggregation — breaks the contract and duplicates mapping bugs.
