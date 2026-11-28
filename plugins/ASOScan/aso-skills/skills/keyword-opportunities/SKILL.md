---
name: keyword-opportunities
description: When the user wants the best untapped keywords for an app tracked in ASOScan (gap-scored suggestions ranked by opportunity score, each showing which competitors already rank for the term). Also use when the user mentions "what keywords should I target", "find keyword opportunities", "what am I missing", "keyword gaps vs my competitors", or "suggest keywords to add". Can also start tracking the chosen terms. For validating a specific term's volume/difficulty, see keyword-intelligence.
metadata:
  version: 1.3.7
---

# Keyword Opportunities

Answer "what should I target next?" with ASOScan's pre-computed, opportunity-scored
suggestions, then track the winners, all from real numbers.

## When to use

- "What keywords should I add / target?"
- "Where are my keyword gaps vs competitors?"
- "Suggest high-opportunity keywords for my app."

## Getting the data (two modes)

Pick the first mode that applies, then follow the steps below.

1. **ASOScan tools are connected** (the ASOScan plugin or connector in ChatGPT or Claude, or any MCP client): use the tool named in the table. Do not ask for an API key and do not run `curl`. Tool results have the same fields as the API responses below, and a list comes back inside `items`. If a tool answers with a message instead of data (reconnect, credits used up, plan limit, "preparing"), pass that message on and stop.
2. **No tools, but you can run shell commands and `ASOSCAN_API_KEY` is set**: make the API call in the table. Base `https://asoscan.com/api/public/v1`, header `Authorization: Bearer $ASOSCAN_API_KEY`, JSON with camelCase fields. Never print the key. Capture the HTTP status and handle errors as described at the bottom.
3. **Neither**: hand off to **asoscan-setup**. It explains how to connect ASOScan in ChatGPT or Claude, or how to create an API key.

ASOScan only sees the apps in the user's own account and the competitors they track. Reads are free; the table below gives the cost of every call that is not (failed calls are always free). Before a call that costs more than 2 API credits, or one that uses AI, tell the user the cost and wait for a yes. Before any call that changes data, ask first.

| Step | Tool (connected) | API call (key) | API credits |
|---|---|---|---|
| Find the app | `list_my_apps` | `GET /apps` | free |
| Opportunities | `find_keyword_opportunities` | `GET /apps/{id}/opportunities?country=&limit=50` | 2 |
| Validate a finalist | `research_keyword` | `GET /apps/{id}/keywords/research?term=&country=` | 8, say the cost first |
| Track the picks (changes data) | `track_keywords` | `POST /apps/{id}/keywords` with `{ "terms": [...], "country": "US" }` | 2, ask first |

## Steps

1. **Find the app** — `GET /apps` → use the `id`.
2. **Opportunities** — `GET /apps/{id}/opportunities?country=&limit=50` (**2 credits**,
   limit 1–200). Each row: `{ term, volume, difficulty, opportunityScore,
   competitorRanks[]{ name, rank, isYou } }`. There is **no** "source" field — rank
   by `opportunityScore` and read `competitorRanks` for context (the entry with
   `isYou: true` is the owner; `rank: null` there = you don't rank yet).
3. **(Optional) validate a shortlisted term** — the research call in
   **keyword-intelligence** (8 credits), for a few finalists only.
4. **(Optional) track the picks** — `POST /apps/{id}/keywords` with
   `{ "terms": [...], "country": "US" }` (**2 credits**, needs a **write** key; up
   to 500 terms) → `{ added[], skipped[]{ term, reason } }`.

## How to prioritize

Sort by `opportunityScore`, then sanity-check each candidate:

1. **Relevant?** Would a searcher for this term actually want this app? Drop
   off-topic high-volume terms — irrelevant installs churn.
2. **Winnable?** Is `difficulty` realistic for this app's authority?
3. **A real gap?** In `competitorRanks`, `isYou` has a null/poor rank while rivals
   rank well → the sharpest opportunity.

Group into **Quick wins** (high score, low difficulty, relevant, you don't rank)
and **Watchlist** (promising but harder / needs validation).

## Output template

```
### Keyword opportunities — {App} ({country})   ·  credits left: {remaining}

**Quick wins** (track these)
| Keyword | Volume | Difficulty | Score | You rank? | Rivals ranking |
|---|---|---|---|---|---|
| … | … | … | … | no | Rival A #4, Rival B #9 |

**Watchlist**
| Keyword | Volume | Difficulty | Score | Note |
|---|---|---|---|---|

**Next in ASOScan:** track the quick wins → track_keywords or POST /apps/{id}/keywords,
then place them with `metadata-audit`.
```

If the user approves tracking, call the write endpoint and report `added`/`skipped`.

## Errors, credits & honesty

- `401` → asoscan-setup · `403` = no API access **or** a read-only key on the write
  call (tell them to create a **read + write** key) · `402` out of credits · `429`
  back off · `503` not enabled yet. Opportunities = 2 credits, tracking = 2.
- Present numbers cleanly; never track terms without asking; don't overpromise ranks.
- Full reference: <https://asoscan.com/api/developers>

## Related

- **keyword-intelligence** — validate a shortlisted term.
- **competitor-analysis** — see which competitors drive the gap.
- **metadata-audit** — place the chosen keywords into the listing.
