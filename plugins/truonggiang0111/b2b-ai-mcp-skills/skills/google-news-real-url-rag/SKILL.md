---
name: google-news-real-url-rag
description: >-
  Scrape Google News RSS, decode opaque news.google.com/rss/articles/... wrapper
  links into real destination publisher URLs, extract clean LLM/RAG-ready full
  article text, author, and og:image, and auto-tag PR signals (funding, launches,
  layoffs, partnerships, legal, earnings).
---

# Google News Scraper & Real Publisher URL AI Extractor

- **Apify Store:** `https://apify.com/ttyan0111/google-news-ai-article-extractor`
- **Dedicated MCP URL:** `https://mcp.apify.com?actors=ttyan0111/google-news-ai-article-extractor`
- **Pricing:** `$0.004` start + `$1.00/1k` articles + `$1.80/1k` full decoded articles. Zero proxies required.

## Connect via MCP (Claude Code, Cursor, VS Code)

```json
{
  "mcpServers": {
    "google-news-real-url": {
      "url": "https://mcp.apify.com?actors=ttyan0111/google-news-ai-article-extractor"
    }
  }
}
```

## Example Input (Past 7 Days PR / Market Signals)

```json
{
  "queries": ["artificial intelligence startups", "OpenAI funding"],
  "language": "en-US",
  "timeRange": "7d",
  "decodeSourceUrls": true,
  "extractFullArticle": true,
  "maxArticlesPerQuery": 20
}
```

## AI-Agent Workflow

1. Query `ttyan0111--google-news-ai-article-extractor` via MCP or sync REST API.
2. Read Key-Value Store **`RUN_SUMMARY`** for decoded URL success counts and PR signal tag breakdowns (`funding`, `launches`, `layoffs`, `partnerships`, `legal`, `earnings`).
3. Pass `fields=title,publisherName,realUrl,publishedAt,prSignals,agentSummary,articleText` to keep LLM RAG context crisp.
