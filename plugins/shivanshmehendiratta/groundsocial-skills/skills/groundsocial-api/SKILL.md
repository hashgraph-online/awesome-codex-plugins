---
name: groundsocial-api
description: Use when you need public social or web data as JSON - Reddit threads and search, X profiles and posts, TikTok, Instagram and YouTube videos, comments and transcripts, LinkedIn companies, Hacker News, GitHub, Google results, app reviews or any web page as Markdown - and none of the research skills fits. Covers auth, finding the right endpoint, costs, pagination and errors for the Groundsocial API and MCP server.
license: MIT
metadata:
  author: Groundsocial
  homepage: https://groundsocial.dev
  repository: https://github.com/shivanshmehendiratta/groundsocial-skills
  canonical_skill: https://groundsocial.dev/SKILL.md
  requires_env: GROUNDSOCIAL_API_KEY
---

# Groundsocial API

One REST API and MCP server for public data from 80+ platforms (about 590 endpoints). Responses keep each
platform's own JSON shape (Reddit Things and Listings, X API v2 objects, YouTube Data API resources).

- Base URL: `https://api.groundsocial.dev`, auth `Authorization: Bearer $GROUNDSOCIAL_API_KEY`
- MCP: `https://api.groundsocial.dev/mcp` (OAuth 2.1, or the API key as a Bearer token). Tool names are the endpoint
  ids with underscores, e.g. `reddit_search_posts`.
- Read-only. Public, logged-out data only.

## 1. Use what you have

- If `GROUNDSOCIAL_API_KEY` is set, use it. Don't create another account.
- If MCP tools like `reddit_search_posts` are available, call those instead of REST.

## 2. Get a key

- A person: https://groundsocial.dev/app/sign-in?new=1 (email code, 100 free credits, no card).
- An agent on its own:

```bash
curl -X POST https://api.groundsocial.dev/v1/agent/signup -H 'content-type: application/json' \
  -d '{"agent_name":"my-research-agent","purpose":"track discussions about my product"}'
```

  `201` returns `api_key`, `claim_url` and `message_for_human`: store the key, pass the other two to your person and
  never open the claim link yourself. A `428` carries a one-line question in `error.details.challenge`; POST again
  with its `challenge_token` and your `answer`.

## 3. Find the right endpoint (all free, no key needed)

```bash
gs() { curl -sS -G "https://api.groundsocial.dev$1" -H "Authorization: Bearer $GROUNDSOCIAL_API_KEY" "${@:2}"; }

gs /v1/utility/find --data-urlencode "task=comments on a tiktok video"   # ranked endpoints with inputs (* = required)
gs /v1/utility/resolve --data-urlencode "input=https://x.com/jack/status/20"   # which endpoint reads this link
gs /v1/utility/plan --data-urlencode "task=compare two subreddits"       # a chain of calls with a cost estimate
gs /v1/utility/endpoint -d id=reddit.search.posts                        # one endpoint: inputs, example, price
gs /v1/platforms                                                         # every platform, status and price
```

Every endpoint has a page at `https://groundsocial.dev/docs/api/<id with dashes>`, e.g.
`/docs/api/reddit-search-posts`.

## 4. Call it

Path inputs go in the path, other inputs in the query string for GET and in a JSON body for POST:

```bash
gs /v1/reddit/search/posts --data-urlencode "q=mcp server" -d sort=top -d t=week -d limit=25
gs /v1/youtube/videos/dQw4w9WgXcQ/transcript -d language=en
curl -sS -X POST https://api.groundsocial.dev/v1/reddit/subreddits/batch \
  -H "Authorization: Bearer $GROUNDSOCIAL_API_KEY" -H 'content-type: application/json' -d '{"names":["python","rust"]}'
```

Paginate with the cursor in the response (Reddit `data.after`, YouTube `nextPageToken` as `after`, TikTok
`cursor`) until it is empty.

## 5. Costs

One credit is one standard read. Some calls cost more (Reddit search 2, LinkedIn 5); `prism.*` and `search.*`
composites are metered by the work done and usually cost far less than their listed maximum. Every response has
`x-credits-charged` and `x-credits-remaining` headers. Failed calls are refunded.

## 6. Errors

`{"error": {"code", "message", "hint", "retryable", "docs_url", "request_id"}}`. Branch on `code`, follow `hint`,
retry only when `retryable` is true and after `Retry-After`. `402` means credits or a key's spend cap ran out: tell
your person instead of looking for another key. Some endpoints are `beta`; a few X endpoints (search, full replies,
followers) are not switched on and answer `503`, uncharged.

## Research skills in this repo

`brand-mention-scan`, `competitor-social-audit`, `creator-vetting`, `subreddit-research`, `tiktok-trend-scan`,
`youtube-transcript-research`, `comment-mining`.
