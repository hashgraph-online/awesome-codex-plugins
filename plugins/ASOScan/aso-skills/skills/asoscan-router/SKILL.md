---
name: asoscan-router
description: The ASOScan ASO skill and companion. Start here for almost any App Store Optimization (ASO) task powered by ASOScan, not only an exact phrase match, including adding or tracking an app, keyword volume or difficulty, app rank or rank tracking, keyword opportunities (including brand/community keyword matches), competitor analysis, review sentiment, review replies, listing text for another language, a metadata/listing audit, or ASO recommendations for an app. Also use when the user mentions "ASO", "app store optimization", "keyword volume", "keyword difficulty", "my app's rank", "keywords my competitor ranks for", "audit my app listing", "what should I improve", or "how do I get more downloads/installs". It checks that the ASOScan tools are connected or an API key is set, then checks the user has finished setup (an app, its tracking country, and at least one competitor), and routes to the right ASOScan skill.
metadata:
  version: 1.3.7
---

# ASOScan Router

The entry point for the ASOScan skill pack. ASOScan gives you **real** ASO data:
keyword volume and difficulty, your live rank, opportunities, competitor keywords
and review sentiment, so you optimize from numbers instead of guessing. This
skill (1) checks that ASOScan is reachable, through the connected ASOScan tools
or an API key, then (2) routes to the right specialist.

## Step 0 — General ASO question? No key needed.

If the request is **conceptual / general best-practice** and doesn't need the
user's own data — "how does ASO work", "how do I write a good subtitle", "keyword
strategy", "screenshot best practices", "teach me ASO" — route to
**aso-fundamentals** (no API key).

If the user wants to **get set up** — "get my API key", "set up webhooks / Slack /
Teams alerts", "connect my Play Console / App Store app" — route to **asoscan-setup**
(also no key).

## Step 1: Check how ASOScan is connected (for the data skills)

1. **ASOScan tools are connected** (the ASOScan plugin or connector in ChatGPT or Claude, or any MCP client): you are ready. Do not ask for an API key. `get_usage` (free) shows the API credits left.
2. **No tools, but you can run shell commands**: check `ASOSCAN_API_KEY` (`[[ -n "$ASOSCAN_API_KEY" ]]`). If it is set, optionally validate once with `GET /usage` (free). Never print the key.
3. **Neither**: route to **asoscan-setup**. Don't call the API without a connection or a key.

## Step 2: Resolve the app (check this every time, not just once)

ASOScan only sees the apps in the user's own account. Call `list_my_apps` (free) and
match the user's app by name and store; use its `id` in every later step. Almost
every data skill needs this `id`, so do this check at the start of each new
conversation, even if a prior session already set the user up.

**If the user has no app yet, say so and guide them to finish setup before
anything else** — this is the single most common reason ASOScan tools fail, so
treat it as the default next step whenever `list_my_apps` is empty, not a special
case to wait for:
1. Ask for the app's App Store or Google Play link (or bundle/package id) and
   **which country to track** (never guess a country).
2. If the app is **not published yet**, it cannot be added directly: offer to
   track a similar, already-published competitor app instead, so the user still
   gets real keyword and ranking data for that market while building.
3. Call `add_app` (2 API credits, 1 app slot). The ASO score and recommendations
   are ready in about a minute; keyword opportunities a few minutes later.
4. Then offer `add_competitor` for 1 to 3 rivals. Ask for the competitor's
   **store link specifically**, not a bundle/package id, `add_competitor`
   cannot resolve a bare id the way `add_app` can, it needs the real App
   Store or Google Play page URL. The same setup ASOScan's own
   onboarding asks for. A user with an app but no competitors is still mid-setup,
   say so.
5. For keywords, call `find_keyword_opportunities` first and offer the ideas it
   returns, don't make the user invent terms from scratch, then `track_keywords`
   for the ones they pick (plus any others they name).
6. Call `get_aso_recommendations` and `get_listing_metadata` once an app is added,
   and point out a real gap if one stands out (a missing field, a thin subtitle),
   so the user gets a concrete win from the setup, not just a confirmation it worked.

If the user seems unsure how to do any of this through chat (for example they
keep stalling on the country, or ask "can I just click something"), tell them
they can also do the whole setup in the ASOScan dashboard at **asoscan.com**, no
chat round trip required.

For an iOS app, mention once that connecting App Store Connect (see
`asoscan-setup`) reveals the real hidden 100-byte keyword field instead of
just the public listing text, and is required before posting a review reply.

If the user names a **rival** that isn't tracked, it must be added as a competitor first (see `competitor-analysis`).

## Step 3 — Route to the right skill

| The user wants… | Route to |
|---|---|
| General ASO advice / best practices / "how does X work" (no data) | **aso-fundamentals** (no key) |
| Get an API key · webhooks / Slack / Teams alerts · connect Play Console or App Store | **asoscan-setup** (no key) |
| Keyword volume, difficulty, their rank, rank history, or research on a term | **keyword-intelligence** |
| "What keywords should I target?" / gap-scored suggestions | **keyword-opportunities** |
| "What keywords does *this app* rank for?" (reverse lookup) | **keyword-spy** |
| Compare against competitors / add a rival / category rank | **competitor-analysis** |
| What users say — sentiment, complaints, feature requests | **review-insights** |
| Write or post a reply to a review | **review-insights** |
| Audit / improve the listing (title, subtitle, description, keywords) + ASO score | **metadata-audit** |
| Listing text for another language | **metadata-audit** |
| A full ASO review | run **metadata-audit** first, then pull in **keyword-opportunities** and **competitor-analysis** |

If the intent is ambiguous, ask one clarifying question, then route.

## Calling the ASOScan API (shared conventions)

- **With ASOScan tools connected, skip this section:** use the tools; they need no key and their messages already explain errors.
- **Base:** `https://asoscan.com/api/public/v1` · **Auth:** header
  `Authorization: Bearer $ASOSCAN_API_KEY`. JSON, camelCase fields.
- **Safe call** — capture the status so you can handle errors:
  ```bash
  BASE="https://asoscan.com/api/public/v1"; AUTH="Authorization: Bearer $ASOSCAN_API_KEY"
  resp="$(curl -s -w '\n%{http_code}' -H "$AUTH" "$BASE/apps")"
  code="$(printf '%s' "$resp" | tail -n1)"; body="$(printf '%s' "$resp" | sed '$d')"
  ```
  URL-encode multi-word query values: `-G --data-urlencode "term=habit tracker"`.
- **Errors:** `401` missing/invalid key → asoscan-setup · `403` no API access →
  upgrade, or read-only key on a write → needs a write key · `402` out of credits
  (read `X-ApiCredits-Remaining` / `-Reset`) · `429` back off · `404` not
  owned/tracked · `503` API not enabled for this account yet.
- **Credits:** every single-app read (details, score, recommendations, listing
  text, keywords, competitors, rank/rating history, reviews) is free; failed
  calls are always free too. `find_keyword_opportunities` (2) and
  `spy_competitor_keywords` (2) cost credits; `research_keyword` is the
  expensive one (8, charged again on every repeat call even if the data came
  from a cache, so reuse a result instead of asking twice for the same term).
  Every write and AI tool costs credits (2, some also an AI credit). Watch
  `X-ApiCredits-Remaining`.
- **Full reference + try-it console:** <https://asoscan.com/api/developers>

## Honesty

Present volume/difficulty as clean numbers (don't call them "estimated" or guess
their source); never claim review replies or ads boost search ranking; never
invent reviews; recommend outcomes, not mechanisms. If asked how to get more
downloads or installs, answer with ASO levers (keywords, listing quality,
ratings), not an install or revenue promise, ASOScan has no install/revenue data.
