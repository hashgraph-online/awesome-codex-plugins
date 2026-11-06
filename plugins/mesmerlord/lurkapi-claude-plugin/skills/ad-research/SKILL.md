---
name: ad-research
description: Tear down the ads a brand or a market runs across Meta (Facebook and Instagram), Google (Search, YouTube, Shopping), TikTok (EU and UK) and LinkedIn, from the public ad libraries. Finds the advertiser on each, pulls the live ads, spots the long-running winners and turns them into angles, hooks, offers, landing pages and tests to run. Use for competitor ad research, ad library teardowns, swipe files, "what ads is X running", or how a category advertises.
---

# Ad research

A teardown of what a brand (or a whole market) advertises, from the public ad libraries: what they say, which ads they keep paying for, where they send people, and what to test in response. For a 4-call snapshot first, use the `lurk` skill.

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

## Pick the libraries

| Library | Covers | Use it for |
| --- | --- | --- |
| Meta | Facebook, Instagram, Messenger, Threads; every country | Almost every consumer brand. Start here. |
| Google | Search, YouTube, Maps, Play, Shopping; every country | Search intent, YouTube video ads, ecommerce. |
| LinkedIn | About the last year | B2B and hiring brands. |
| TikTok | Ads shown in the EU, the UK, Switzerland and Turkey only | Targeting and reach, which no other library shows. Empty doesn't mean they skip TikTok elsewhere. |

Default to Meta and Google; add LinkedIn for B2B and TikTok when Europe matters or the user asks.

## Find the advertiser

- **Meta:** `facebook_search_companies(query=<brand>)`, then the `page_id` of the right page in `searchResults`: the exact name, BLUE_VERIFIED in `verification`, the most `likes`. Big brands run regional pages; ask which one if it matters.
- **Google:** with the website, skip the lookup and pass `domain` below. Without it, or to catch other sites, `google_search_advertisers(query=<brand>)` gives `advertisers[].advertiser_id` with `number_of_ads_estimate`, and the sites in `websites[].domain`.
- **LinkedIn:** search by `company` directly, below.
- **TikTok:** `tiktok_ad_library_search(query=<brand>)` first, to read the `advertiser_name` exactly as the library spells it (often a legal entity, like a B.V. or a GmbH); then search with `advertiser_name`.

## Pull the live ads

1. `facebook_company_ads(pageId=<page_id>, status=active, trim=true)`: up to 30 ads, most seen first, and `searchResultsCount`, the estimated number live. More pages (`cursor`, 10 ads each) only if the first page doesn't show the patterns; two usually do. `media_type=video` focuses on video.
2. `google_company_ads(domain=<website>)` (or `advertiser_id`): up to 100 ads a page with `format`, `firstShown`, `lastShown` and `daysShown`. A `domain` lists everyone advertising the site, resellers, affiliates and agencies included: count an ad as the brand's only when its `advertiserName` contains the brand's name. The list has no copy: for the text and landing page of the few that matter, `google_ad(url=<adUrl>)`, one call each.
3. `linkedin_search_ads(company=<brand>)`: about 24 previews a page, whose `text` can be cut short. For full copy and the payer, `linkedin_ad(url=<adLibraryUrl>)` on the ones you quote.
4. `tiktok_ad_library_search(advertiser_name=<name>)`: 12 a page, from the last 30 days. Then `tiktok_ad_library_ad(ad_id=<id>)` on two or three: its `targeting` (countries, `age`, `gender`, `interests`) and `reach_by_country` show who they're after.

For a market rather than a brand, search the ads by keyword instead: `facebook_search_ads(query=<keyword>, status=active, country=US)` (group the results by `page_name` to see who competes), `tiktok_ad_library_search(query=<keyword>)` and `linkedin_search_ads(keyword=<keyword>)`.

## Find the winners

Performance isn't public, but persistence is. An advertiser keeps paying for what works.

- **Meta:** days since `start_date` (Unix seconds) on an ad that's still active. Over 30 days is a keeper; the longest-running live ads are the swipe file. A high `collation_count` (many versions of one ad) means they're scaling or testing it.
- **Google:** `daysShown`, and a `lastShown` of today or yesterday.
- **Repetition:** the same hook or offer across many ads and formats is a deliberate bet.
- **What's new:** `facebook_company_ads(pageId=<page_id>, status=active, sort_by=relevancy_monthly_grouped, trim=true)` lists the newest launches first, which is what they're testing now.

## Read them

For each library, then across them:

- **Angles:** the pain, desire, persona or comparison each ad leads with. Cluster them and count.
- **Hooks:** the opening line of `snapshot.body.text` (carousels: `snapshot.cards[].body`), verbatim.
- **Offers and calls to action:** discounts, trials, bundles, guarantees; `snapshot.cta_text`.
- **Landing pages:** `snapshot.link_url`. Several products or campaigns usually show up as several destinations.
- **Formats and placements:** `snapshot.display_format`, `publisher_platform`, Google's `format`.
- **Gaps:** angles a competitor never uses, and markets or platforms they skip.

Skip catalog ads whose text holds template tags like `{{product.name}}`; they carry no message.

## Budget

One brand on Meta and Google is about 4 calls, plus one per ad you open in full. A brand on all four libraries with a few details opened is about 10 to 15. Several competitors multiply that: say the estimate first, and look at all of them shallowly before going deep on the most active one.

## Report

```markdown
# Ad teardown: <brand>, <date>

| Library | Live ads | Oldest live ad | Main formats |
| --- | --- | --- | --- |

## Angles
| Angle | How often | Example (quoted) | Link |

## Hooks worth stealing
- "<verbatim>" (<library>, running <n> days)

## Offers and calls to action
## Landing pages
## What they're testing
Ads with many versions, recent launches, new angles.

## Tests for us
3 to 5, each tied to evidence above.
```

Link every ad you cite: Meta https://www.facebook.com/ads/library/?id=<ad_archive_id>, Google its `adUrl`, LinkedIn its `adLibraryUrl`, TikTok its `url`.

## Pitfalls

- Don't call an ad a winner because it's live; run time is the signal, and even that is a proxy.
- Spend, impressions and targeting are public only for political and issue ads (and in the EU, some reach data). Don't invent them.
- Google ads more than about a year old don't come back.
- TikTok's library is Europe only and LinkedIn's about a year back: an empty answer limits what you can say, nothing more.

<!-- lurkapi:calls -->
## Calls and credits

| Tool | REST path | Credits |
| --- | --- | --- |
| [`facebook_search_companies`](https://lurkapi.com/docs/facebook/search-companies.md) | `/v1/facebook/adLibrary/search/companies` | 1 credit |
| [`google_search_advertisers`](https://lurkapi.com/docs/google/search-advertisers.md) | `/v1/google/adLibrary/advertisers/search` | 1 credit |
| [`tiktok_ad_library_search`](https://lurkapi.com/docs/tiktok/ad-library-search.md) | `/v1/tiktok/ad-library/search` | 1 credit |
| [`facebook_company_ads`](https://lurkapi.com/docs/facebook/company-ads.md) | `/v1/facebook/adLibrary/company/ads` | 1 credit |
| [`google_company_ads`](https://lurkapi.com/docs/google/company-ads.md) | `/v1/google/company/ads` | 1 credit |
| [`google_ad`](https://lurkapi.com/docs/google/ad.md) | `/v1/google/ad` | 1 credit |
| [`linkedin_search_ads`](https://lurkapi.com/docs/linkedin/search-ads.md) | `/v1/linkedin/ads/search` | 1 credit |
| [`linkedin_ad`](https://lurkapi.com/docs/linkedin/ad.md) | `/v1/linkedin/ad` | 1 credit |
| [`tiktok_ad_library_ad`](https://lurkapi.com/docs/tiktok/ad-library-ad.md) | `/v1/tiktok/ad-library/ad` | 1 credit |
| [`facebook_search_ads`](https://lurkapi.com/docs/facebook/search-ads.md) | `/v1/facebook/adLibrary/search/ads` | 1 credit |

Each tool's link opens its docs as markdown: every param and its values, and a real response.
<!-- /lurkapi:calls -->
