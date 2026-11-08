---
name: dns-connector
description: Use this skill when the operator needs DNS-Shop electronics data — search or a product card. Trigger on "днс", "dns-shop", "dns", "ноутбук днс". Always needs the operator's Chrome over CDP (Qrator proof-of-work). Skip for non-DNS tasks.
---

# DNS-Shop Connector

Reads DNS-Shop inside the operator's Chrome over CDP. Qrator's JavaScript
proof-of-work answers every dynamic page with HTTP 401 + a challenge script —
no header trick clears it, but a real Chrome executes it natively. The
connector renders the page and reads the DOM.

## When to use
- Search DNS electronics catalog by text
- One product's price, old price, availability

## Tools available
- `dns_search(query)` — tiles from the rendered search page
- `dns_card(product_url)` — one card. The URL carries `/product/<id>/`, where the
  id is a 16-hex string: `/product/b7a1667f9b19ed20/`. A bare id also works.

**Not an MCP tool:** `dns_selfcheck()` is a tri-state canary. It is CLI-only —
`marketplace-mcp doctor` runs every connector's canary at once.

## A green selfcheck does NOT mean the data is right

This connector is why that sentence appears throughout this repo. In July 2026
the product-id regex was fixed, search began returning 24 links, and
`dns_selfcheck` went green — while **every item still came back with
`title: null` and `price: null`**. The transport was fine; the parser understood
nothing.

`dns_selfcheck` answers one question: did the page load and did the extractor
return a shape. If a number has to be trusted, open the product page in the same
Chrome and read it.

## The price on a DNS tile is not the smallest number on it

Three traps, all confirmed against the live grid on 2026-07-28:

- **An instalment sits next to the price.** A tile showing `58 999 ₽` also shows
  `от 5 751 ₽/ мес.`. Anything that takes the minimum reports the monthly
  payment — a number that validates, looks plausible and is wrong. The extractor
  reads the named price node and skips instalment and bonus nodes.
- **The strikethrough price carries no currency glyph** — `.product-buy__prev`
  renders a bare `54 999`, so a filter keyed on `₽` never sees it.
- **The first product anchor in a tile is the image link**, which has no text.
  Tiles are selected by the exact BEM block `.catalog-product`, never by walking
  up from an anchor.

`price_rub` is `None` when no price could be read — never `0`, never a guess. If
a whole page comes back unpriced the response carries a `no_prices_on_page`
warning: that is drift to investigate, not "free".

## Gotchas
- The first navigation pays the proof-of-work and is slow; later reads on the
  same session are fast.
- Bursts get throttled by Qrator and degrade to `transport_down`. That is
  rate-limiting of the browser, not a parser fault — pace the calls.
- A Qrator page that loads with HTTP 200 answers `challenge_required`: open
  dns-shop.ru in the scraping Chrome, pass the check, retry. It is never cached
  and never returned as a product.
- From a datacenter address the site answers 401, so there is nothing to verify
  there. This connector is only meaningful from the operator's own machine.
## DSH activation

In DeepSeek Harness, the default profile exposes only `compare_prices` and
`compare_sources` through the cheap compare mount. Per-marketplace tools and
`marketplace_sources` require `RU_MARKETPLACE_MCP_FULL=1` and a profile restart;
do not call them in the default mode.
