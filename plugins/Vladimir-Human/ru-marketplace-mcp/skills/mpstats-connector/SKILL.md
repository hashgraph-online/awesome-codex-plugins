---
name: mpstats-connector
description: Use this skill for MPStats sales/stock analytics on a specific Ozon or Wildberries item — per-day sales, current price and stock, FBS/FBO warehouse split, seller/brand identity, and a rolling orders-per-day average. Trigger on "продажи товара на озон", "аналитика ozon sku", "mpstats по артикулу", "продажи за 30 дней", or English equivalents. Requires a paid MPStats account (MPSTATS_MP_AUTH env). Skip raw catalog price checks — use wb_/ozon_ connectors (no account needed).
---

# MPStats Connector

Paid-account sales/stock analytics for Ozon and Wildberries items, via the
MPStats browser-plugin API (`plugin.mpstats.io/pluginapi`). Unlike the
anonymous catalog connectors in this workspace, this one is **optional**: it
needs a paid MPStats account configured as the `MPSTATS_MP_AUTH` env var (the
raw `mp_auth` JWT cookie from a logged-in browser plugin session at
mpstats.io). Without it the server boots cleanly, every tool returns
`auth_missing`, and no other connector is affected — like every source here,
it is a pleasant extra you opt into, not a requirement.

## When to use

- Per-SKU 30-day **sales analytics** — orders graph, price graph, stock graph
- **Current price and stock** for an item (today's reading off the graph tail)
- **Warehouse stock split** — FBS (seller warehouse) vs FBO (marketplace warehouse)
- Seller/brand identity and a rolling **orders-per-day** average
- Sales-trend comparison across several SKUs in one batched call

## When NOT to use

- Bare price/availability checks with no account — use `wb_card` / `ozon_card`.
- Reviews, categories, seller tax identity — MPStats does not surface those; use
  the catalog connectors.
- Search by text or category browsing — MPStats analytics is keyed by SKU, not
  by query.

## Prerequisites

Set `MPSTATS_MP_AUTH` to the raw JWT (no `mp_auth=` prefix, no quotes):

```
export MPSTATS_MP_AUTH='eyJ0eXAiOiJKV1Qi...'   # from a logged-in mpstats.io session
```

Without it, every tool returns an `auth_missing` error (retryable: false) and
the server still boots cleanly. Treat the token as a secret: it identifies a
paid, quota-billed account. Never log it, never commit it.

## Tools available

- `mpstats_item(skus, place, oz_fbs=True)` — per-SKU 30-day analytics. Up to 100
  SKUs per call. Returns, per SKU: `seller`, `seller_id`, `brand`, `stock_now`,
  `price_avg_rub`, `orders_per_day`, `days_on_stocks`, `totals` (orders/sum/
  sum_prev), and four per-day graphs (`orders_graph`, `prices_graph`,
  `count_graph`, `rubrics_graph`).
- `mpstats_warehouses(skus, place)` — per-SKU warehouse stock split: `fbs`
  count, `fbo` total (collapsed from the upstream per-warehouse list), the raw
  `fbo_warehouses` list, and the upstream `last_update` timestamp.

**Not an MCP tool:** `mpstats_selfcheck()` is a tri-state health canary:
`success`, `drift_detected` (reachable but unparseable — code change needed), or
`inconclusive` (transport failure / missing auth — says nothing about the
parsers). It is CLI-only — `marketplace-mcp doctor` runs every connector's canary
at once.

## Marketplace parameter

`place` is `"ozon"` or `"wildberries"`. `oz_fbs` is an Ozon-specific
Fulfilled-by-Seller flag (default true); harmless for wildberries.

## Workflow patterns

**Sales snapshot for one Ozon item by SKU:**
1. `mpstats_item([5107857210], place="ozon")` — current price/stock + 30-day graphs
2. Read `price_avg_rub` and `stock_now` for today; sum `orders_graph` for the
   window total; compare `totals.sum` vs `totals.sum_prev` for trend.

**Compare a basket of SKUs:**
1. `mpstats_item([sku1, sku2, ...], place="ozon")` — batched, request-order
   preserved. A SKU MPStats has no data for surfaces as a `meta.warnings` entry,
   not a silent gap.

**Stock split (where the units physically sit):**
1. `mpstats_item([...], place="ozon")` for `stock_now` (total)
2. `mpstats_warehouses([...], place="ozon")` for the FBS/FBO split and
   `last_update` (when MPStats last refreshed the snapshot).

## Graph semantics (gotchas)

- Graphs are length `days` (default 30), **oldest-first**; the final cell is
  "today". The current price or stock is the last **non-zero** cell.
- Price and stock diverge on an all-zero graph, deliberately. `price_avg_rub`
  becomes `None`, because a false `0.0` would rank a delisted item as the
  cheapest. `stock_now` becomes `0`, because "none in stock" is a real reading.
  An **empty** graph gives `None` for both — that one is genuinely no data.
- A zero cell means **"no data for that day"**, not "the value was zero".
  Sum the graph for a real total; do not read a single cell as the answer.
- `totals.orders` / `totals.sum` are MPStats' own aggregates over the window —
  prefer them over hand-summing unless you need a custom sub-window.
- A missing value is always `None`, never `0`: a zero would rank a dead listing
  as the top seller — the exact bug this connector's parsers exist to prevent.

## Error format

On failure, raises `ToolError` with a JSON body: `{"error": "<code>",
"message": "...", "retryable": <bool>}`. Codes: `auth_missing` (no/expired
token — not retryable), `bad_request` (bad SKU/place), `rate_limited`
(retryable, honours `retry_after_s`), `transport_down`, `parser_drift`
(upstream shape changed — code change needed), `not_found` (no analytics for
any SKU). Partial data (some SKUs missing) stays a success with `meta.warnings`
and `meta.healthy: false` — silence never reads as success here.
## DSH activation

In DeepSeek Harness, the default profile exposes only `compare_prices` and
`compare_sources` through the cheap compare mount. Per-marketplace tools and
`marketplace_sources` require `RU_MARKETPLACE_MCP_FULL=1` and a profile restart;
do not call them in the default mode.
