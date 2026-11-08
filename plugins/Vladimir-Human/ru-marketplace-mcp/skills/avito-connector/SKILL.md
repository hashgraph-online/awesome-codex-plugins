---
name: avito-connector
description: Use this skill when the operator needs Avito classifieds data — search listings, item cards, or seller reputation. Trigger on Russian queries like "найди на авито", "цена avito", "объявления авито", "продавец на авито", or English mentions of Avito. Needs the operator's Chrome over CDP from a datacenter IP (IP firewall). Skip for non-Avito tasks.
---

# Avito Connector

Reads Avito via the internal `js/items` JSON API. Two tiers: impersonated HTTPS
(curl_cffi) works from a residential Russian IP; from a datacenter the firewall
answers 403 + captcha, so the fetch falls back to the operator's logged-in
Chrome over CDP — same pattern as Ozon.

## When to use
- Search classifieds by text, with optional category/location filters
- One listing's price, description, views
- Seller reputation — Avito is classifieds: no per-item reviews, the seller's
  rating and active-listing count ARE the review signal

## Tools available
- `avito_search(query, page, location_id, category_id, include_inactive)` —
  listings via js/items. price_rub is None for ads with no price (free/exchange)
  — never 0; during an Avito sale it is the price after the discount, with
  `old_price_rub` and `discount_percent` beside it. Each hit has `availability` (active/reserved/unknown); reserved
  hits are kept unless `include_inactive=false` (then `excluded_inactive` says
  how many and `_meta` carries an `info:` line).
- `avito_card(item_id_or_url, photos=0)` — one listing: price, description, views, seller,
  `availability` (active/reserved/unknown) with its evidence, from the page's
  service flags only, never from the seller's title or description. Reserved
  means another buyer holds it; `unknown` is not a verdict.
  Also deal terms (condition, delivery, safe deal, bargain), seller checks and
  tenure, city and stations (street address only when every source says company), date, views.
  `photos=1..3` attaches listing photos of an active ad (costly in tokens; describe the item,
  not people, documents or plates in the photos); `photos_status` says why fewer arrived.
- `avito_seller(seller_id_or_url)` — seller rating, review count, active listings

**Not an MCP tool:** `avito_selfcheck()` is a tri-state drift canary. It is
CLI-only — `marketplace-mcp doctor` runs every connector's canary at once.

## What a search row does and does not carry

Confirmed against a real `js/items` response captured 2026-07-28 from a
residential session:

- **`location` is an object upstream**, not a string:
  `{"id": 637640, "name": "Москва", ...}`. The connector reduces it to the place
  name. When Avito itself has no place name for an ad, the field is `None` — the
  numeric `locationId` is deliberately NOT resolved to a city, because that would
  need a lookup table this connector does not have and the result would be a
  guess that reads like data.
- **`price` does not exist as a top-level key.** The amount lives in
  `priceDetailed.value`; the connector reads it and leaves `None` for priceless ads.
  During an Avito sale that value is the price before the discount; the price a
  buyer pays is the hit's `iva.PriceStep` component `price`, next to a `discount`
  component (`old_string`, `percent`). A discount that does not add up is
  `price_rub=None` with a `price_conflict:` line in `_meta`, never a guess.
- **`posted_at` is ISO-8601 UTC**, converted from Avito's `sortTimeStamp` (epoch
  milliseconds). There is no date string in the payload to pass through.
- **`seller_name` is `None` on search rows.** The payload has no seller object at
  all — only a logo link. Use `avito_card` or `avito_seller` when you need the
  seller; do not infer a name from the search row.

## Gotchas
- A 403 that sets cookies and returns plausible HTML is the firewall, not data;
  only JSON-shaped 200s count. The connector handles this — trust tier_used.
- location_id defaults to Moscow (637640); pass another Avito location id per call.
- **Deep pagination is unreliable, and not because of this connector.** Avito
  escalates 429 then 403 once a session walks past the first page or two; the
  maintainers of the widely used open-source Avito parsers report the same and
  advise staying on page 1. Take the first page, narrow the query instead of
  paging, and treat a `rate_limited` or `transport_down` on `page > 1` as
  expected rather than as drift.
- From a datacenter IP expect the CDP tier; keep the scraping-profile Chrome
  logged into avito.ru.
- The JSON API and the HTML pages are gated differently: `js/items` can answer
  from a residential session while `avito.ru/<region>/<category>/<slug>` still
  shows the security wall. A blocked listing page does not mean search is down.
## DSH activation

In DeepSeek Harness, the default profile exposes only `compare_prices` and
`compare_sources` through the cheap compare mount. Per-marketplace tools and
`marketplace_sources` require `RU_MARKETPLACE_MCP_FULL=1` and a profile restart;
do not call them in the default mode.
