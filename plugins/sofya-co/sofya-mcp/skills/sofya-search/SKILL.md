---
name: sofya-search
description: Search the web, read pages and documents as clean markdown, and pull one specific fact out of a page, with Sofya. Use when the user asks to look something up online, needs current information, gives a URL or PDF to read, or wants a price, date, spec or contact from a specific page.
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

# Sofya search, fetch and extract

Sofya is a web search and page reading API with its own search index. Three tools cover most web tasks:

| Tool | Use it for | Cost |
|------|-----------|------|
| `search` | Finding pages. Results include page content, not just snippets. | 1 credit (snippets) or 2 (basic, default). +2 for `include_answer` |
| `fetch` | Reading known URLs as markdown: web pages, PDF, Word, Excel, PowerPoint, EPUB. Up to 10 URLs per call. | 1 credit per URL, failed URLs free |
| `extract` | One answer from one page ("what does the Pro plan cost?"). | 10 credits |

For open-ended questions that need many sources, use the `sofya-research` skill instead.

## Step 1: pick how to call Sofya

1. **MCP tools available** (`search`, `fetch`, `extract` from a server named `sofya`): call them directly. They take the parameters below and return the same JSON as the REST API.
2. **No MCP tools, `SOFYA_API_KEY` is set**: call the REST API with curl (examples below). Base URL `https://sofya.co`.
3. **Neither**: tell the user Sofya needs a key. They can create one at https://sofya.co/dashboard, or you can request one for them to approve by following https://sofya.co/auth.md. Don't fall back to guessing.

Set the HTTP timeout to at least 90 seconds. Search with an answer and extract can take 5-30 seconds.

## Step 2: choose the tool

- Know the URL already? `fetch` it. Don't search for a page you can read directly.
- Need one fact from a long page? `extract` with a clear prompt. It costs more than fetch but returns only the answer.
- Otherwise `search`. Use `search_depth: "snippets"` when you only need titles and links to decide what to read next, `"basic"` (default) when you want page text in the results.
- Several independent lookups: run the searches in parallel rather than one long query.

## Search

Parameters: `query` (required), `search_depth` (`snippets` | `basic`), `max_results` (1-20, default 10), `include_answer` (bool), `topic` (`general` | `news`), `freshness` (`day`, `week`, `month`, `year`, or `YYYY-MM-DD:YYYY-MM-DD`), `include_domains` / `exclude_domains` (bare hostnames like `github.com`, max 10).

```bash
curl -s -X POST https://sofya.co/v1/search \
  -H "Authorization: Bearer $SOFYA_API_KEY" -H "Content-Type: application/json" \
  -d '{"query": "python 3.14 release notes", "max_results": 5}'
```

Response: `results[]` with `title`, `url`, `content`, `description`, `published_date`; plus `answer` (when asked for), `credits_used`, `credits_remaining`. If `relaxed_query` is set, the original query matched nothing and the results answer a looser version of it: say so to the user.

Tips:
- For current events use `topic: "news"` and a `freshness` window, and compute date ranges from today's date.
- To search one site, use `include_domains` rather than writing `site:` into the query.
- Write queries the way the answer would be phrased on a page, not as a question to a chatbot.

## Fetch

Parameters: `urls` (required, max 10), `include_raw_html` (bool, default false).

```bash
curl -s -X POST https://sofya.co/v1/fetch \
  -H "Authorization: Bearer $SOFYA_API_KEY" -H "Content-Type: application/json" \
  -d '{"urls": ["https://example.com/report.pdf"]}'
```

Each result has `success`, `content` (markdown), `title`, `published_time` and `error`. A URL with `success: false` is not charged; report its `error` to the user instead of retrying it unchanged.

## Extract

Parameters: `url` and `prompt` (both required).

```bash
curl -s -X POST https://sofya.co/v1/extract \
  -H "Authorization: Bearer $SOFYA_API_KEY" -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/pricing", "prompt": "list each plan with its monthly price"}'
```

Returns `content` (the answer). If `usage.low_content` is true the page had almost no text, so the answer is empty and only 1 credit was charged.

## Errors

Only successful (2xx) responses are charged, so retrying after an error never double-charges.

| Code | Meaning | What to do |
|------|---------|-----------|
| 401 | Missing or invalid key | Check `SOFYA_API_KEY`. Don't retry. |
| 402 | Out of credits, or the key hit its monthly limit | Give the user the `top_up_url` from the response. With MCP, `buy_credits` returns a payment link (it never charges anything). |
| 422 | Bad parameter, or (extract) the page couldn't be fetched | Fix the request or tell the user. Don't retry as is. |
| 429 | Rate limited | Wait `Retry-After` seconds, then retry. |
| 502, 503 | Temporary | Retry once after a few seconds. |

Always cite the URLs you used in your answer.

Full reference: https://sofya.co/docs. Pricing: https://sofya.co/pricing.
