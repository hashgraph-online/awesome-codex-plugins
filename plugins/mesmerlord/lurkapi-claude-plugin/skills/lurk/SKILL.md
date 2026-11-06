---
name: lurk
description: Lurk a brand. From just a name or a website, a one-page snapshot of whether it advertises right now on Meta and Google, what its live ads push, and how big it is on Facebook, Instagram and TikTok, in 4 calls (the run behind the LurkAPI dashboard). Use when the user names a company or domain and asks what it is up to, whether it runs ads, how big it is on social, or wants a quick competitor check.
---

# Lurk a brand

One name or website in, one page out: is the brand advertising right now, where, saying what, and how big is its audience. Four calls in two rounds. For a full teardown of the ads afterwards, use the `ad-research` skill.

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

Work out the brand's name (Nike) and its website (nike.com) from what the user gave. If you're unsure of the website, ask, or try `<name>.com` and say so.

**Round 1, both at once:**

1. `facebook_search_companies(query=<name>)` finds the brand's Facebook page. Take the first of `searchResults` unless a later one is clearly the brand: the exact name, `verification` of BLUE_VERIFIED, the most `likes`. Big brands have regional and product pages; name the runner-up if it was close. Keep its `page_id`, `likes` (Facebook followers), `ig_username` and `ig_followers`.
2. `google_company_ads(domain=<website>, region=US)` lists the ads promoting the site on Google Search, YouTube, Maps, Play and Shopping. Read `number_of_ads_estimate`, and from `ads` the `advertiserName`, `format` and `firstShown` of the first few. Anyone advertising the site shows up here, resellers and agencies included; the ads are the brand's own only when `advertiserName` contains its name. Use the brand's home country as `region` when it isn't American.

**Round 2, both at once, as soon as the page is known:**

3. `facebook_company_ads(pageId=<page_id>, status=active, trim=true)` returns the live ads on Facebook and Instagram, most seen first, up to 30. `searchResultsCount` is Meta's estimate of how many are live.
4. `tiktok_profile(handle=<ig_username>)`: brands use the same handle on both far more often than not. Read `stats.followerCount`, `stats.heartCount` and `stats.videoCount`. Check it's really theirs: an account with no bio (`user.signature`), a handful of followers and no videos is a squatter, so say the brand doesn't own the handle. A `not_found` means there's no TikTok under that handle; say so rather than guessing another.

No page found? Skip both round 2 calls, which need it, and say the brand has no Facebook page under that name. No `ig_username`? Skip the TikTok call.

That's the lurk: four calls. Stop there unless the user asks for more; each extra lookup (`instagram_profile`, `youtube_channel`, `linkedin_company`) is one more call.

## Read the ads

From the live Meta ads, find what repeats, not what's listed first:

- **The offer and the angle.** The primary text is `snapshot.body.text` (or `snapshot.cards[].body` for carousels); the headline is `snapshot.title`. Quote real lines.
- **The ads that work.** An ad still running weeks after its `start_date` (Unix seconds) is the best public sign that it pays. A high `collation_count` means many versions of one ad: they're scaling or testing it.
- **Where it sends people.** `snapshot.link_url` and `snapshot.cta_text`.
- **Where it runs.** `publisher_platform`: Facebook, Instagram, Messenger, Threads.

Skip ads whose text holds template tags like `{{product.name}}`: those are catalog ads and say nothing about the brand's message.

## Report

```markdown
## <Brand>, lurked <date>

| | |
| --- | --- |
| Meta ads live | about <n> (Facebook page <name>, <likes> followers) |
| Google ads | about <n>, as <advertiser name>, mostly <format> |
| Instagram | @<handle>, <followers> followers |
| TikTok | @<handle>, <followers> followers, <likes> likes |

**What they're pushing.** 3 to 5 bullets: the offers, products and hooks that repeat in the live ads, each with a quoted line.

**The ad to study.** The longest-running live ad: its copy, how long it has run, where it sends people, and its link (https://www.facebook.com/ads/library/?id=<ad_archive_id>).

**Read.** Two sentences: how hard they're advertising, and where they're strongest.
```

## Pitfalls

- Counts are estimates (Meta's and Google's). Say "about".
- Live doesn't mean winning: only run time hints at that. Spend and results aren't public, except for political ads.
- Google's `region=US` counts only ads shown in the US; ALL counts everywhere.
- The Facebook page search can match a fan page or a namesake. If the followers look wrong for the brand, say so before reading its ads.

<!-- lurkapi:calls -->
## Calls and credits

| Tool | REST path | Credits |
| --- | --- | --- |
| [`facebook_search_companies`](https://lurkapi.com/docs/facebook/search-companies.md) | `/v1/facebook/adLibrary/search/companies` | 1 credit |
| [`google_company_ads`](https://lurkapi.com/docs/google/company-ads.md) | `/v1/google/company/ads` | 1 credit |
| [`facebook_company_ads`](https://lurkapi.com/docs/facebook/company-ads.md) | `/v1/facebook/adLibrary/company/ads` | 1 credit |
| [`tiktok_profile`](https://lurkapi.com/docs/tiktok/profile.md) | `/v1/tiktok/profile` | 1 credit |
| [`instagram_profile`](https://lurkapi.com/docs/instagram/profile.md) | `/v1/instagram/profile` | 1 credit |
| [`youtube_channel`](https://lurkapi.com/docs/youtube/channel.md) | `/v1/youtube/channel` | 1 credit |
| [`linkedin_company`](https://lurkapi.com/docs/linkedin/company.md) | `/v1/linkedin/company` | 1 credit |

Each tool's link opens its docs as markdown: every param and its values, and a real response.
<!-- /lurkapi:calls -->
