---
name: keyword-intelligence
description: When the user wants to analyze keyword performance for an app tracked in ASOScan (real search volume, difficulty, the app's current rank and rank movement, daily rank history, weekly volume/difficulty trends), or live on-demand research for a new term. Also use when the user mentions "how hard is this keyword", "search volume for X", "where do I rank for Y", "is my rank going up or down", "show my rank history", or "research this keyword". For discovering new keywords to target, see keyword-opportunities.
metadata:
  version: 1.3.7
---

# Keyword Intelligence

Turn ASOScan's real keyword data into a clear read on which keywords are worth the
effort and how the app is trending — so you prioritize from numbers, not hunches.

## When to use

- "What's the volume/difficulty of `<keyword>`?"
- "Where does my app rank for `<keyword>`? Is it moving?"
- "Show me my rank history / volume trend for `<keyword>`."
- "Research `<a keyword I don't track yet>`."

## Getting the data (two modes)

Pick the first mode that applies, then follow the steps below.

1. **ASOScan tools are connected** (the ASOScan plugin or connector in ChatGPT or Claude, or any MCP client): use the tool named in the table. Do not ask for an API key and do not run `curl`. Tool results have the same fields as the API responses below, and a list comes back inside `items`. If a tool answers with a message instead of data (reconnect, credits used up, plan limit, "preparing"), pass that message on and stop.
2. **No tools, but you can run shell commands and `ASOSCAN_API_KEY` is set**: make the API call in the table. Base `https://asoscan.com/api/public/v1`, header `Authorization: Bearer $ASOSCAN_API_KEY`, JSON with camelCase fields. Never print the key. Capture the HTTP status and handle errors as described at the bottom.
3. **Neither**: hand off to **asoscan-setup**. It explains how to connect ASOScan in ChatGPT or Claude, or how to create an API key.

ASOScan only sees the apps in the user's own account and the competitors they track. Reads are free; the table below gives the cost of every call that is not (failed calls are always free). Before a call that costs more than 2 API credits, or one that uses AI, tell the user the cost and wait for a yes. Before any call that changes data, ask first.

| Step | Tool (connected) | API call (key) | API credits |
|---|---|---|---|
| Find the app | `list_my_apps` | `GET /apps` | free |
| Tracked keywords | `get_tracked_keywords` | `GET /apps/{id}/keywords?country=&rankWindow=7d` | free |
| Rank history | `get_keyword_rank_history` | `GET /apps/{id}/keywords/{keywordId}/history?days=30` | free |
| Volume and difficulty trend | `get_keyword_metrics_history` | `GET /apps/{id}/keywords/{keywordId}/metrics-history?days=180` | free |
| Live research | `research_keyword` | `GET /apps/{id}/keywords/research?term=&country=` | 8, say the cost first |

## Steps

1. **Find the app** — `GET /apps` → each `{ id, name, platform, storeId, category }`.
   Use the `id`.
2. **Tracked keywords + current state** — `GET /apps/{id}/keywords?country=&rankWindow=7d`
   (free). Each row: `{ id, term, country, rank, rankDelta, rankCheckedAt,
   volume, difficulty, isFavorite }`. `rankWindow` = `1d|7d|30d`. Fetch the list
   once and filter locally. The row's `id` is the `{keywordId}` for history calls.
3. **Rank history** — `GET /apps/{id}/keywords/{keywordId}/history?days=30`
   (free) → `[{ rank, recordedAt }]` (days 1–365).
4. **Volume/difficulty trend** — `GET /apps/{id}/keywords/{keywordId}/metrics-history?days=180`
   (free) → `{ term, country, volume[]{ at, value }, difficulty[]{ at, value } }`.
5. **Live research** (a term not tracked yet) — `GET /apps/{id}/keywords/research?term=…&country=US`
   (**8 credits every time, cache hit or not — reuse your own result instead of
   calling it twice for the same term in one conversation, that bills the user
   again for an answer you already have**; URL-encode the term) → `{ term,
   platform, country, volume, difficulty, competingAppsCount, topApps[] }`. A
   failed lookup is 400 (free).
   For several keyword ideas at once, use `find_keyword_opportunities` (2
   credits, covers many terms in one call) instead of researching them one by
   one, this endpoint is for one specific term the user already has in mind.
6. **Find easier alternatives when a term is hard.** If a researched term is high-volume but
   **high-difficulty** (🟠 Stretch), research AT MOST 2–3 long-tail variants of it, not more — add
   a qualifier such as `<term> games`, `<term> app`, `color <term>`, `best <term>` — via the
   research endpoint (step 5), and surface any that keep useful volume at **lower difficulty**
   (a 🟢 Win-now alternative). Cache each; stop once you have one good alternative or have tried 3,
   whichever comes first — don't keep spending 8-credit calls chasing a better one. This is the
   highest-leverage move for a Stretch term: point the user at a keyword they can realistically win
   instead of one they can't.

## How to read the numbers

- **volume** — relative search demand (higher = more searches); compare within one market.
- **difficulty** — how hard to rank (higher = harder). The prize is
  **high-volume, low-difficulty** terms the app can realistically win.
- **rank + rankDelta** — position (`null` = not ranked) and its change over the
  window. **Positive `rankDelta` = improvement** (toward #1).

| Tier | Signal | Action |
|---|---|---|
| 🟢 Win now | High volume · low difficulty · not ranking well yet | Prioritize in metadata |
| 🟡 Defend | High volume · already top ~10 | Hold; watch rankDelta |
| 🟠 Stretch | High volume · high difficulty | Long game; needs authority |
| ⚪ Low leverage | Low volume | Only if highly relevant |

## Output template

```
### Keyword intelligence — {App} ({country})   ·  credits left: {X-ApiCredits-Remaining}

| Keyword | Volume | Difficulty | Rank | Δ ({window}) | Read |
|---|---|---|---|---|---|
| … | … | … | … | ▲/▼ … | Win now / Defend / … |

**Trends:** {keyword}: rank {from → to} over {N}d; volume {trend}; difficulty {trend}.
**What I'd do:** 1) {specific action tied to a keyword}  2) …
```

Then nudge the next step in ASOScan: track the winners via **keyword-opportunities**
and place them with **metadata-audit**.

## Errors, credits & honesty

- `401` → asoscan-setup · `403` → plan without API access · `402` out of credits
  (read `X-ApiCredits-Remaining`/`-Reset`) · `429` back off · `404` not tracked ·
  `503` API not enabled yet. Reads here are free; live research spends credits on success, failed calls are free.
- Present volume/difficulty as clean numbers — don't label them "estimated" or
  guess their source. Never promise a specific rank.
- Full reference: <https://asoscan.com/api/developers>

## Related

- **keyword-opportunities** — discover *new* keywords worth targeting.
- **keyword-spy** — every keyword an app already ranks for.
- **metadata-audit** — put the winning keywords into the listing.
