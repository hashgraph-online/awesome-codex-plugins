---
name: serply-mcp
description: Search Google (web, news, Scholar, Maps, video, jobs), Bing, Amazon and Reddit, or scrape a public URL, through the Serply MCP server bundled with this plugin. Use when the user needs current web results, recent news coverage, academic papers with citation counts, local businesses, Reddit discussion, or the text of a specific page.
license: MIT
metadata:
  author: serply-inc
  version: "1.0"
---

# Searching with the Serply MCP server

This plugin connects Codex to the hosted Serply MCP server at `https://api.serply.io/mcp`. The API key comes from the `SERPLY_API_KEY` environment variable. If the tools are missing or return an authentication error, tell the user to create a key at https://serply.io/mcp (2,500 free credits, no card), export `SERPLY_API_KEY`, and restart Codex.

## Pick the tool by vertical

| Need | Tool | Required argument |
|------|------|-------------------|
| General web results | `google_search` | `query` |
| Recent news coverage | `google_news_search` | `query` |
| Papers, authors, citation counts | `google_scholar_search` | `query` |
| Local businesses and places | `google_maps_search` | `query` |
| Videos | `google_video_search` | `query` |
| Job postings | `google_jobs_search` | `query` |
| A second engine for comparison | `bing_search` | `query` |
| Products and prices | `amazon_product_search` | `query` |
| Text of one known page | `scrape_url` | `url` |
| Reddit posts, threads, users | `reddit_subreddit_posts`, `reddit_post`, `reddit_post_comments`, `reddit_user_posts`, `reddit_subreddit_about` | see the tool schema |

## Query tips

- Google operators pass through in `query`: `site:example.com`, `"exact phrase"`, `-exclude`, `filetype:pdf`, `intitle:`.
- `num` sets the result count where the tool accepts it. Around 10 is the practical ceiling per call; page with `start` on `google_search`.
- `proxy_location` (a country code such as `US`, `GB`, `DE`) localizes results; `device` switches between desktop and mobile results.
- Search results are snippets. When the answer depends on a page's full text, follow up with `scrape_url` on the best one or two links rather than guessing from the snippet.

## Answering

Cite the result URLs you relied on. Say when results were thin or conflicting instead of filling gaps from memory, and state the date context for news queries.
