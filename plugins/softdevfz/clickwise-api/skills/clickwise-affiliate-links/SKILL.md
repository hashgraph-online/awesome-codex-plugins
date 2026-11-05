---
name: clickwise-affiliate-links
description: Find affiliate programs, deals and products with the Clickwise affiliate network and return tracked links ready to share. Use when the user asks which affiliate programs fit a site, app, newsletter or social channel; wants an affiliate or tracked link for a merchant or product; searches products by GTIN or title to publish with affiliate links; or wants a product feed or link cards to monetize an app, store or AI assistant.
---

# Clickwise affiliate links

Clickwise is an affiliate network with a remote MCP server and a REST API. Use the MCP tools when they are connected (server `clickwise` at <https://partners.clickwise.net/api/v1/mcp>). Otherwise call the REST API with `curl`.

## Pick the tool

| The user wants | Without an API key | With an API key (`CLICKWISE_API_KEY`) |
|---|---|---|
| Programs that fit a site or channel | `find_affiliate_programs` (`publisher_url`, `topic`, `country`, `channel`) | same, or `list_my_programs` for approved ones |
| A tracked link to share | `request_tracked_links` (creates a provisional affiliate; email optional) | `create_tracking_links` (`links`: program and optional `landing_url`) |
| Link cards, an HTML embed or a JSON feed | `get_monetization_feed` | `get_product_feed` (`country`, `format`: json, csv, tsv, xml) |
| Products by GTIN or title | `get_catalog_stats` (counts only) | `search_products` (`gtin`, `text`, `brand`, `country`) |
| Current deals and offers | `list_deals`, `get_deal` | same |
| Program news | `list_news`, `get_news` | same |
| Results | — | `get_performance_report`, `list_conversions` |

`tools/list` on the server is the source of truth for tools and arguments.

## REST without MCP

```sh
# Programs that fit a channel, no key
curl -s https://partners.clickwise.net/api/v1/mcp \
  -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"find_affiliate_programs","arguments":{"topic":"running shoes","country":"US","channel":"site"}}}'

# Products by GTIN with your tracked links (key on the server only)
curl -s --get https://partners.clickwise.net/api/v1/publisher/products/lookup/ \
  -H "X-API-Key: $CLICKWISE_API_KEY" --data-urlencode 'gtins=4006381333931' --data-urlencode 'country=DE'
```

OpenAPI 3.1: https://partners.clickwise.net/api/v1/publisher/openapi.json

## Rules

- **Links:** give the user each tracked link (`url`, `cw_link` or the link field the tool returns) exactly as returned. Do not shorten, rewrite, strip parameters from it or link to the merchant directly.
- **Disclosure:** when links go on a page, add `rel="sponsored nofollow noopener"` and a visible affiliate disclosure.
- **Key:** read it from `CLICKWISE_API_KEY`. Never print it, commit it, put it in a URL or ship it to a browser. Keys are requested at <https://partners.clickwise.net/developers/>
- **Access secrets:** `request_tracked_links` and `get_monetization_feed` return an access secret for the provisional profile. Hand it to the user once and tell them to keep it private; it is needed to claim the account and add payout details (`update_profile`).
- **Facts:** report commission rates, terms and availability only as the tools return them. Do not promise earnings or approval.
- **Errors:** read `error.code`; on HTTP 429 wait for `Retry-After`.

Support: partnerships@clickwise.net
