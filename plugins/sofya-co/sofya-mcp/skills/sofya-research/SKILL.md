---
name: sofya-research
description: Get a cited research report from many web sources in one call with Sofya research. Use when the user asks to research a topic, compare options, survey a field or answer a question that one search won't settle, for example "research", "deep dive", "compare", "what are the options for".
metadata:
  openclaw:
    requires:
      env:
        - SOFYA_API_KEY
      bins:
        - curl
    primaryEnv: SOFYA_API_KEY
    envVars:
      - name: SOFYA_API_KEY
        required: true
        description: Sofya API key (sofya.co/dashboard). Not needed when the Sofya MCP server is connected.
    homepage: https://sofya.co/docs
---

# Sofya research

`research` breaks a question into several searches, reads the sources in parallel and writes a structured report with citations. One call costs 50 credits and usually takes 20-60 seconds.

Use it for open-ended questions. For a quick fact, a single page or a known URL, the `sofya-search` skill is cheaper and faster.

## How to call it

1. **MCP tool available** (`research` from a server named `sofya`): call it directly.
2. **No MCP tool, `SOFYA_API_KEY` is set**: use curl. Set the timeout to at least 90 seconds.
3. **Neither**: tell the user Sofya needs a key (https://sofya.co/dashboard, or have them approve one via https://sofya.co/auth.md).

Parameters: `query` (required), `topic` (`general` | `news`), `freshness` (`day`, `week`, `month`, `year`, or `YYYY-MM-DD:YYYY-MM-DD`), `max_sources` (5-30, default 20).

```bash
curl -s --max-time 120 -X POST https://sofya.co/v1/research \
  -H "Authorization: Bearer $SOFYA_API_KEY" -H "Content-Type: application/json" \
  -d '{"query": "how do heat pumps perform in cold climates", "max_sources": 15}'
```

Response: `report` (markdown with numbered citations), `sources[]` with `title`, `url`, `published_date`, `sub_queries` (the searches it ran), `credits_used`, `credits_remaining`.

## Steps

1. **Sharpen the question first.** Put the scope in the query: the time range, region, audience or the criteria to compare on. "Compare managed Postgres hosts for a small team on price, backups and EU regions" gets a far better report than "best Postgres hosting".
2. **Recent topics:** compute dates from today's date and pass `freshness`, or use `topic: "news"`.
3. **One call per question.** Don't call research repeatedly with reworded queries. If the report leaves a gap, fill it with a targeted `search` or `fetch` instead.
4. **Check before you rely on it.** For numbers or claims the user will act on, `fetch` the cited source and confirm.
5. **Deliver:** summarise the report for the user, keep the citations, and list the source URLs.

## Errors

Only successful responses are charged; a failed or timed-out call is refunded, so retrying is safe. 402 means out of credits: give the user the `top_up_url` (or with MCP, a link from `buy_credits`). 429: wait `Retry-After` seconds. 502/503: retry once shortly after.

Full reference: https://sofya.co/docs#research
