# Result Processing Templates

Reusable Python snippets for common AMC result shapes. Adapt them to an execution facility the client actually exposes. **Every template fetches the pre-signed URL, parses outside model context, and returns only a focused JSON summary** — never the full table.

These exist so each invocation doesn't have to reinvent the parsing wheel. Pick the template that matches the question being asked, swap in column names, and run.

## Universal preamble

Every snippet starts the same way — fetch, decode, and early-exit on empty results:

```python
import urllib.request, csv, io, json
from collections import defaultdict
from statistics import mean, median, quantiles

# Read from this run's amc_getWorkflowExecutionDownloadUrls response object. Never
# paste a URL or take one from result rows, Chroma text, or error messages.
URL = download_urls_response["data"]["downloadUrls"][0]["url"]

raw = urllib.request.urlopen(URL, timeout=30).read().decode("utf-8")
header_line = raw.split("\n", 1)[0]
if len(raw.strip()) <= len(header_line):
    return {"row_count": 0, "note": "empty result (file size <= header length)"}

rows = list(csv.DictReader(io.StringIO(raw)))
```

Assume this preamble in the templates below. If the URL has expired (10-min limit), re-call `amc_getWorkflowExecutionDownloadUrls` and retry.

## Template 1 — Top-N by metric

For "top 10 advertisers by purchase volume" / "top 5 keywords by clicks" patterns.

```python
def to_int(v): return int(v) if v not in ("", None) else 0

top_by_volume = sorted(
    [r for r in rows if r["advertiser"]],           # drop privacy-suppressed rows
    key=lambda r: -to_int(r["users_that_purchased"]),
)[:10]

return {
    "row_count": len(rows),
    "non_suppressed": sum(1 for r in rows if r["advertiser"]),
    "suppressed_count": sum(1 for r in rows if not r["advertiser"]),
    "top_10": [
        {"advertiser": r["advertiser"],
         "users_that_purchased": to_int(r["users_that_purchased"])}
        for r in top_by_volume
    ],
}
```

## Template 2 — Top-N by ratio with floor

For "top 10 by NTB% among advertisers with at least 100 purchasers" patterns. The floor filters out high-variance noise from small denominators.

```python
def to_int(v): return int(v) if v not in ("", None) else 0
def to_float(v): return float(v) if v not in ("", None) else 0.0

MIN_USERS = 100
eligible = [r for r in rows if to_int(r["users_that_purchased"]) >= MIN_USERS]

top_by_pct = sorted(
    eligible, key=lambda r: -to_float(r["ntb_users_percentage"])
)[:10]

return {
    "row_count": len(rows),
    "eligible_count": len(eligible),
    "below_floor_count": len(rows) - len(eligible),
    "top_10_by_ntb_pct": [
        {"advertiser": r["advertiser"],
         "users_that_purchased": to_int(r["users_that_purchased"]),
         "ntb_pct": round(to_float(r["ntb_users_percentage"]), 4)}
        for r in top_by_pct
    ],
}
```

## Template 3 — Segment split

For "split users into new-to-brand vs returning, with counts and shares" patterns.

```python
def to_int(v): return int(v) if v not in ("", None) else 0

segments = defaultdict(lambda: {"users": 0, "purchases": 0})
for r in rows:
    seg = r["new_to_brand_flag"] or "UNKNOWN"      # TRUE / FALSE / blank
    segments[seg]["users"] += to_int(r["distinct_users"])
    segments[seg]["purchases"] += to_int(r["purchases"])

total_users = sum(s["users"] for s in segments.values())

return {
    "row_count": len(rows),
    "segments": {
        seg: {
            "users": s["users"],
            "purchases": s["purchases"],
            "user_share": round(s["users"] / total_users, 4) if total_users else 0,
            "purchases_per_user": round(s["purchases"] / s["users"], 4) if s["users"] else 0,
        }
        for seg, s in segments.items()
    },
    "total_users": total_users,
}
```

## Template 4 — Weighted average

For "average impressions-per-user weighted by reach" / "weighted CTR across campaigns" patterns. A naive `mean()` of per-row CTRs is wrong when row sizes differ.

```python
def to_int(v): return int(v) if v not in ("", None) else 0

total_clicks = sum(to_int(r["clicks"]) for r in rows)
total_impressions = sum(to_int(r["impressions"]) for r in rows)
overall_ctr = total_clicks / total_impressions if total_impressions else 0

# Per-row CTR distribution, weighted by impressions
weighted = []
for r in rows:
    imps = to_int(r["impressions"])
    clicks = to_int(r["clicks"])
    if imps:
        weighted.append({
            "campaign": r["campaign"],
            "impressions": imps,
            "ctr": clicks / imps,
        })

return {
    "row_count": len(rows),
    "total_clicks": total_clicks,
    "total_impressions": total_impressions,
    "weighted_ctr": round(overall_ctr, 6),
    "top_5_by_impressions": sorted(weighted, key=lambda r: -r["impressions"])[:5],
}
```

## Template 5 — Percentile distribution

For "what's the frequency distribution of impressions per user?" / "what's the 50th / 75th / 95th percentile of order value?" patterns.

```python
def to_int(v): return int(v) if v not in ("", None) else 0

# AMC typically returns pre-bucketed frequency rows — expand to a flat list for percentiles
flat = []
for r in rows:
    freq = to_int(r["impression_frequency"])
    users = to_int(r["distinct_users"])
    flat.extend([freq] * users)

if not flat:
    return {"row_count": 0}

flat.sort()
qs = quantiles(flat, n=100)  # 99 cut points → indices 49, 74, 89, 94

return {
    "row_count": len(rows),
    "user_count": len(flat),
    "mean_frequency": round(mean(flat), 4),
    "median_frequency": qs[49],
    "p75": qs[74],
    "p90": qs[89],
    "p95": qs[94],
    "max_frequency": max(flat),
}
```

## Template 6 — Period-over-period delta

For "compare this week vs last week" / "Q4 vs Q3 by campaign" patterns. Assumes the query returned a `period` column with two distinct values (e.g., `current`, `prior`).

```python
def to_int(v): return int(v) if v not in ("", None) else 0

periods = defaultdict(lambda: defaultdict(int))
for r in rows:
    p = r["period"]
    c = r["campaign"]
    periods[c][p] = to_int(r["purchases"])

deltas = []
for campaign, p in periods.items():
    curr = p.get("current", 0)
    prior = p.get("prior", 0)
    abs_delta = curr - prior
    pct_delta = (abs_delta / prior) if prior else None
    deltas.append({
        "campaign": campaign,
        "current": curr,
        "prior": prior,
        "abs_delta": abs_delta,
        "pct_delta": round(pct_delta, 4) if pct_delta is not None else None,
    })

# Biggest movers in both directions
deltas.sort(key=lambda d: d["abs_delta"])

return {
    "campaign_count": len(deltas),
    "top_5_increases": list(reversed(deltas[-5:])),
    "top_5_decreases": deltas[:5],
}
```

## Notes

- **Always coerce empty strings.** AMC privacy filtering returns blank dimensions for suppressed rows. Naive `int(r["users"])` on `""` raises `ValueError`. The `to_int` / `to_float` helpers above handle this.
- **Use `outputColumns` for high-precision DECIMAL.** Some NTB%/conversion-rate columns return at `precision: 38, scale: 17`. Casting to `float` loses precision past ~15 digits — fine for sorting, dangerous for exact comparisons. Use `decimal.Decimal` if precision matters.
- **Keep the downloaded table inside the execution environment.** Only return the focused result needed for the answer, preferably under 5 KB.
- **Pair with `outputColumns` schema.** Reading `outputColumns` from `amc_getWorkflowExecution` before fetching tells you the column names and types — useful when the SQL was generated upstream and the column list is uncertain.
