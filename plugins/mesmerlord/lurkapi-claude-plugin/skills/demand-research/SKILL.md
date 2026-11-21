---
name: demand-research
description: Check whether people want a product or niche, and what exactly they want, from live public signals. What they type into Google and TikTok Shop, what sells on eBay and at what price, how much attention the topic gets on TikTok and YouTube, what Reddit complains about, and whether the news is picking it up. Use for product validation, niche and keyword research, pricing research, "is there demand for X", or sizing up a category before launching.
---

# Demand research

Is there demand for a product or niche, and what shape does it take: the words buyers search with, what already sells and for how much, how much attention the topic gets, and what people wish existed.

<!-- lurkapi:access -->
## Calling LurkAPI

**With MCP** (the LurkAPI plugin or connector), call the tools by name, like `tiktok_profile`; your client may prefix them (`mcp__plugin_lurkapi_lurkapi__tiktok_profile`). With only `find_endpoints` and `call_endpoint`, run a tool as `call_endpoint` with `endpoint` set to its name and `params` to its arguments. Results come trimmed: no nulls, one URL per image or video. A long result comes in parts: its `_note` gives the `offset` for the next part, which is free.

**Without MCP** (Codex, Cursor, scripts), every tool is `GET https://api.lurkapi.com` plus its path, with the same params as a query string (URL-encoded) and the key from `LURKAPI_API_KEY` in the `x-api-key` header:

```bash
curl -s "https://api.lurkapi.com/v1/tiktok/profile?handle=nike" -H "x-api-key: $LURKAPI_API_KEY"
```

If `LURKAPI_API_KEY` isn't set but `LURKAPI_KEY` is (the name older docs used), use that. Raw answers are big: pipe them through `jq` to keep the fields you need. No key yet? Ask the user to create one at https://lurkapi.com/dashboard (100 free credits on sign-up, then a balance below 25 tops back up to 25 every day) and to set `LURKAPI_API_KEY` in their shell. Never ask for the key in the chat, and never print it.

**Credits.** Each call costs what the table at the end says, `not_found` included; failures on our side (5xx) are free. Every answer carries `credits_remaining`. Before a run of more than 20 calls, check the balance with `account_credit_balance` (free) and tell the user what the run will cost. If a call answers `missing_api_key`, `insufficient_credits` or `signup_required`, stop and pass on what it says.
<!-- /lurkapi:access -->

## Run

Start from a seed: a product or category in plain words ("standing desk", "collagen gummies").

1. **What people search.** `google_autocomplete(query=<seed>)`, then the same with a word after it to open up intent: "<seed> for", "<seed> vs", "best <seed>", "<seed> without". Each answer has up to about 15 `suggestions`; their `value`s are real searches. Add `region` and `language` for another market. Then `tiktok_shop_suggestions(query=<seed>)`: what US shoppers type into TikTok Shop, brand names included, which shows who already owns the category there.
2. **What sells, and for how much.** `ebay_search(query=<seed>, condition=new)`: 60 listings a page with `price`, `sold` (units that listing has sold), `watchers` and `condition`. Rank by `sold` to see what moves; take the price range of the sellers, not of everything listed. If the user names a TikTok Shop store or a competitor's product, `tiktok_shop_products(url=<store url>)` (with `sold_count`, `rating` and `price` per product) or `tiktok_product(url=<product url>)`.
3. **How much attention it gets.** `tiktok_search_keyword(query=<seed>)`: 20 videos with `stats.playCount`; `youtube_search(query=<seed>, uploadDate=this_year, sortBy=popular)`: what got watched this year. Many recent videos with big views means live interest; a few old ones means a niche or a fad that passed.
4. **What people wish existed.** `reddit_search(query=<seed>, timeframe=year)`, then `reddit_post_comments(url=<thread url>, trim=true)` on the two or three most-discussed threads (https://www.reddit.com plus the result's `permalink`). For more depth, use the `reddit-research` skill.
5. **Is it in the news.** `google_news(query=<seed>, date_posted=last-month)`: count the `articles` and read the titles for launches, trends or trouble.

## Budget

A full scan is about 12 calls; eBay pages cost more than most calls (see the table). For a quick yes or no, steps 1 and 2 alone are about 5 calls. To compare several seeds, run step 1 for all of them first and go deep only on the promising ones.

## Read it

- **Demand:** many specific autocompletes (with modifiers like "for", "vs", "without") and recent high-view videos mean people are actively looking.
- **Proven spend:** listings with high `sold` counts at healthy prices mean money already changes hands; many listings with no sales mean supply without demand.
- **Price bands:** cluster what sells into budget, mid and premium, and note where the gaps are.
- **Unmet needs:** the "without", "for" and "vs" suggestions plus Reddit's complaints point at the product to build.
- **Who's there:** brands in TikTok Shop suggestions and top listings; a category with no clear brand is open.

## Report

```markdown
# Demand: <seed>, <date>

**Verdict:** strong / moderate / weak / unclear, in one sentence, with the two strongest signals.

| Signal | What we saw |
| --- | --- |
| Search | <n> Google and <n> TikTok Shop suggestions; the telling ones quoted |
| Sales | eBay: <n> listings sampled, top sellers at $<a>–$<b>, best seller <n> sold |
| Attention | TikTok top videos <views>; YouTube this year <views> |
| Complaints | Reddit themes, with links |
| News | <n> articles in the last month; what they're about |

## How buyers say it
The phrases to target, from autocomplete and Reddit.

## Price bands
## Openings
2 to 4 product or positioning ideas, each tied to the evidence.
```

## Pitfalls

- Autocomplete shows what's searched, not how often. Treat it as wording and intent, not volume.
- eBay's `sold` is per listing and lifetime; it isn't a market total.
- TikTok search ranks by relevance with no date filter: check `createTime` before calling something a trend.
- One market at a time: Google suggestions follow `region` and `language`, TikTok Shop suggestions and eBay are US.

<!-- lurkapi:calls -->
## Calls and credits

| Tool | REST path | Credits |
| --- | --- | --- |
| [`google_autocomplete`](https://lurkapi.com/docs/google/autocomplete.md) | `/v1/google/autocomplete` | 1 credit |
| [`tiktok_shop_suggestions`](https://lurkapi.com/docs/tiktok/shop-suggestions.md) | `/v1/tiktok/shop/search/suggestions` | 1 credit |
| [`ebay_search`](https://lurkapi.com/docs/ebay/search.md) | `/v1/ebay/search` | 2 credits |
| [`tiktok_shop_products`](https://lurkapi.com/docs/tiktok/shop-products.md) | `/v1/tiktok/shop/products` | 1 credit |
| [`tiktok_product`](https://lurkapi.com/docs/tiktok/product.md) | `/v1/tiktok/product` | 1 credit |
| [`tiktok_search_keyword`](https://lurkapi.com/docs/tiktok/search-keyword.md) | `/v1/tiktok/search/keyword` | 1 credit |
| [`youtube_search`](https://lurkapi.com/docs/youtube/search.md) | `/v1/youtube/search` | 1 credit |
| [`reddit_search`](https://lurkapi.com/docs/reddit/search.md) | `/v1/reddit/search` | 1 credit |
| [`reddit_post_comments`](https://lurkapi.com/docs/reddit/post-comments.md) | `/v1/reddit/post/comments` | 1 credit |
| [`google_news`](https://lurkapi.com/docs/google/news.md) | `/v1/google/news` | 1 credit |

Each tool's link opens its docs as markdown: every param and its values, and a real response.
<!-- /lurkapi:calls -->
