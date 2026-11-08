---
name: lamoda-connector
description: Use this skill when the operator needs Lamoda fashion data — search or a product card with sizes. Trigger on "ламода", "lamoda", "кроссовки lamoda". Cards try anonymous GraphQL first, then the operator's Chrome when it is refused; search needs Chrome over CDP. Skip for non-Lamoda tasks.
---

# Lamoda Connector

Two tiers by endpoint. The GraphQL product endpoint is tried over plain anonymous
HTTPS first and, since 2026-10-12 when that started to meet the 307 loop too, through
one in-page POST in the operator's Chrome (`tier_used: graphql_cdp`) — it enriches a SKU you already have with real prices, brand, sizes and
availability. Everything that would find a SKU (search, catalog, HTML) sits
behind the same 307 redirect loop as Ozon, so discovery runs in the operator's
Chrome over CDP.

## When to use
- Search Lamoda by text (CDP tier)
- One product's price, old price, per-size availability (GraphQL: anonymous first, Chrome on refusal)

## Tools available
- `lamoda_search(query)` — tiles from the rendered search page (CDP)
- `lamoda_card(sku_or_url)` — GraphQL enrichment. SKU looks like MP002XM1RMM3;
  URLs carry it lowercased, the connector normalises.

**Not an MCP tool:** `lamoda_selfcheck()` probes both tiers. It is CLI-only —
`marketplace-mcp doctor` runs every connector's canary at once.

## Gotchas
- Lamoda exposes NO ratings anywhere — `rating` is not in the GraphQL schema.
  No review tools exist here by design.
- An empty search with a detected visible challenge returns `challenge_required`;
  it is not cached. Complete the interaction in the connected Chrome profile,
  then retry. Empty extraction without challenge evidence remains parser drift,
  not proof of "no results".
- With `CHROME_CHALLENGE_HANDOFF_S` enabled, `handoff_expires_at` confirms a
  retained search tab. Complete its interaction, then repeat the same query in
  the same MCP session before expiry to read that tab without a new navigation.
- A missing price is `null`, never `0`: `price_rub: null` means Lamoda had no
  usable price — treat it as no data, never as a free item.
## DSH activation

In DeepSeek Harness, the default profile exposes only `compare_prices` and
`compare_sources` through the cheap compare mount. Per-marketplace tools and
`marketplace_sources` require `RU_MARKETPLACE_MCP_FULL=1` and a profile restart;
do not call them in the default mode.
