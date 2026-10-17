---
name: firecrawl-search
description: |
  Web search with full page content extraction. Use this skill whenever the user asks to search the web, find articles, research a topic, look something up, find recent news, discover sources, or says "search for", "find me", "look up", "what are people saying about", or "find articles about". Returns real search results with optional full-page markdown — not just snippets. Provides capabilities beyond default agent web search tools.
---

# firecrawl search

Web search with optional content scraping. Returns search results as JSON, optionally with full page content.

## When to use

- You don't have a specific URL yet
- You need to find pages, answer questions, or discover sources
- First step in the [workflow escalation pattern](../firecrawl-cli/SKILL.md): search → scrape → map → crawl → interact

## Quick start

```bash
# Basic search
firecrawl search "your query" -o .firecrawl/result.json --json

# Search and scrape full page content from results
firecrawl search "your query" --scrape -o .firecrawl/scraped.json --json

# News from the past day
firecrawl search "your query" --sources news --tbs qdr:d -o .firecrawl/news.json --json
```

## Options

| Option                               | Description                                   |
| ------------------------------------ | --------------------------------------------- |
| `--limit <n>`                        | Max number of results                         |
| `--sources <web,images,news>`        | Source types to search                        |
| `--categories <github,research,pdf>` | Filter by category                            |
| `--tbs <qdr:h\|d\|w\|m\|y>`          | Time-based search filter                      |
| `--location`                         | Location for search results                   |
| `--country <code>`                   | Country code for search                       |
| `--scrape`                           | Also scrape full page content for each result |
| `--scrape-formats`                   | Formats when scraping (default: markdown)     |
| `-o, --output <path>`                | Output file path                              |
| `--json`                             | Output as JSON                                |

## Tips

- **`--scrape` fetches full content** — don't re-scrape URLs from search results. This saves credits and avoids redundant fetches.
- Always write results to `.firecrawl/` with `-o` to avoid context window bloat.
- Use `jq` to extract URLs or titles: `jq -r '.data.web[].url' .firecrawl/search.json`
- Naming convention: `.firecrawl/search-{query}.json` or `.firecrawl/search-{query}-scraped.json`

## See also

- [firecrawl-scrape](../firecrawl-scrape/SKILL.md) — scrape a specific URL
- [firecrawl-map](../firecrawl-map/SKILL.md) — discover URLs within a site
- [firecrawl-crawl](../firecrawl-crawl/SKILL.md) — bulk extract from a site
