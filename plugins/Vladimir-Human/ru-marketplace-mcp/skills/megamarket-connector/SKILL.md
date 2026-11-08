---
name: megamarket-connector
description: Use this skill when the operator needs Megamarket data — search the catalog or read a product card. Trigger on "мегамаркет", "megamarket", "цена мегамаркет". Always needs the operator's Chrome over CDP (ServicePipe IP block). Skip for non-Megamarket tasks.
---

# Megamarket Connector

Reads Megamarket via its internal mobile JSON API, POSTed from inside the
operator's Chrome over CDP. ServicePipe gates the whole site by IP reputation:
the API returns valid JSON, but the JSON is always the code-7 "отключите VPN"
refusal with your own IP echoed back. Passing the ServicePipe challenge is not
enough on its own: an anonymous browser that has cleared it still reads an empty
`items` list. Real catalog data needs a browser that is actually logged in.

## When to use
- Search the Megamarket catalog by text
- One product's price, old price, availability, rating

## Tools available
- `megamarket_search(query)` — items + total count. price_rub None when absent.
- `megamarket_card(item_id_or_url)` — one product card

**Not an MCP tool:** `megamarket_selfcheck()` is a tri-state canary, where a
code-7 refusal is inconclusive (transport), never drift. It is CLI-only —
`marketplace-mcp doctor` runs every connector's canary at once.

## Gotchas
- A code-7 / VPN-error body is an IP block, not data — the connector maps it to
  transport_down with the fix inline.
- Run megamarket_selfcheck from your Chrome first: these endpoints were probed
  anonymously, and only a challenge-passed session confirms the in-browser shape.
- A missing price is `null`, never `0`: `price_rub: null` means Megamarket had
  no usable price — treat it as no data, never as a free item.
- Prices are address-dependent. `_meta.warnings` carries the address source
  only when it changes what the prices mean: `address_source:profile` (the
  operator's personal default address — personalized prices) or
  `address_source:none` (no delivery address resolved, so no offers are
  deliverable — expect the empty-items symptom). Both mark the response
  `_meta.healthy=false`. The default public city-level source
  (`address_source:suggest` from `MEGAMARKET_ADDRESS`) is the normal healthy
  case: no address warning.

## Privacy: the profile address is opt-in

`MEGAMARKET_USE_PROFILE_ADDRESS` (default `0`) decides whether the connector may
read the private, account-gated `/profileService/address/list` endpoint from the
operator's logged-in Chrome profile, to use the profile's default delivery
address. Off — the default — it is never called: the address comes from the
public suggest endpoint for `MEGAMARKET_ADDRESS` (Москва by default), and prices
are city-level, not personalized. On, the profile's address list, its
default flag and the region are read once per process, prices and availability
match exactly what the operator sees on the site, and the search response
carries `address_source:profile` plus a `profile_address_read` warning in
`_meta.warnings` so the reader knows before quoting a price. The raw addressId
never leaves the process.

Opt in when the operator asks for Megamarket prices "as I see them"; leave it
off for neutral, city-level price research.

## DSH activation

In DeepSeek Harness, the default profile exposes only `compare_prices` and
`compare_sources` through the cheap compare mount. Per-marketplace tools and
`marketplace_sources` require `RU_MARKETPLACE_MCP_FULL=1` and a profile restart;
do not call them in the default mode.
