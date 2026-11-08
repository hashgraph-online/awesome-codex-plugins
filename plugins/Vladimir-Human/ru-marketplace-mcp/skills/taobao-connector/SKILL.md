---
name: taobao-connector
description: Use this skill when the operator needs Taobao marketplace data — search Chinese listings or read an item card. Trigger on Chinese or English queries like "taobao", "淘宝", "найди на таобао", "цена taobao". Always needs the operator's Chrome over CDP (signed mtop API). Skip for non-Taobao tasks.
---

# Taobao Connector

Reads Taobao inside the operator's own Chrome over CDP. The search page is a
client-side React app whose data layer is the signed mtop API — every XHR wants
a `sign` computed from the `_m_h5_tk` cookie, and unsigned probes answer
`FAIL_SYS_TOKEN_EMPTY`. There is no anonymous tier; the site's own JS signs
requests natively in a real browser.

## When to use
- Search Taobao by Chinese or English text
- One item's price, shop, sales label, description images

## Tools available
- `taobao_search(query, page)` — listings. Prices are in YUAN (CNY), never
  converted: price_cny is None when hidden — never 0.
- `taobao_card(item_id_or_url)` — one item card. item ids are 9-13 digit
  strings; pass a bare id or an item.taobao.com URL.

**Not an MCP tool:** `taobao_selfcheck()` is a tri-state canary that renders one
live search page. It is CLI-only — `marketplace-mcp doctor` runs every
connector's canary at once.

## Gotchas
- Prices stay in yuan. Comparing against ruble sources needs an explicit rate;
  a baked-in one would go silently stale.
- A detected login/CAPTCHA wall returns `challenge_required` and
  `requires_user_action=true`. Complete it in the scraping profile before retrying
  the same operation. Failed payloads are not cached; a retry reads the browser
  again. Successful results still use the normal TTL cache.
- With `CHROME_CHALLENGE_HANDOFF_S` enabled, `handoff_expires_at` confirms that
  the challenged search/card tab is retained. Complete its interaction, then
  repeat the same tool arguments in the same MCP session before expiry. No new
  navigation is issued for that resume; expiry never extends on retries.
- The operator's Chrome must be running with CDP (`uvx ru-marketplace-mcp browser start` or `scripts/start_chrome_cdp.sh`; use `uvx ru-marketplace-mcp unblock taobao` to log in).
## DSH activation

In DeepSeek Harness, the default profile exposes only `compare_prices` and
`compare_sources` through the cheap compare mount. Per-marketplace tools and
`marketplace_sources` require `RU_MARKETPLACE_MCP_FULL=1` and a profile restart;
do not call them in the default mode.
