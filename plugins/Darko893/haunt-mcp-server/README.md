<div align="center">

<img src="https://hauntapi.com/favicon-192x192.png" width="76" alt="Haunt" />

# Haunt MCP Server

**Web extraction for AI agents.** Give Claude, Cursor, Windsurf, or any MCP client a clean tool that turns any permitted public web page into structured JSON or Markdown from a plain-language prompt, and returns an honest machine-readable failure instead of fabricated data when a page is blocked.

[![npm](https://img.shields.io/npm/v/@hauntapi/mcp-server?color=1f6feb)](https://www.npmjs.com/package/@hauntapi/mcp-server)
[![Glama score](https://glama.ai/mcp/servers/Darko893/mcp-server/badges/score.svg)](https://glama.ai/mcp/servers/Darko893/mcp-server)
[![MCP Registry](https://img.shields.io/badge/MCP-registry-1f6feb)](https://registry.modelcontextprotocol.io)

[Website](https://hauntapi.com) &middot; [Docs](https://hauntapi.com/docs) &middot; [Get a free key](https://hauntapi.com/?utm_source=github&utm_medium=readme&utm_campaign=mcp_server#signup) &middot; [Python SDK](https://github.com/Darko893/hauntapi-python)

</div>

---

Built for agent workflows that need product data, competitor prices, article text, page metadata, small site-wide datasets, lead lists, or research snippets, without brittle CSS selectors. Try it with **no API key** using the `try_demo_extract` tool. Free tier: 1,000 credits a month, no card.

## Quick Start

### 1. Add Haunt to your MCP client

This is the block to copy.

```json
{
  "mcpServers": {
    "haunt": {
      "command": "npx",
      "args": ["-y", "@hauntapi/mcp-server"],
      "env": {
        "HAUNT_API_KEY": "your-api-key"
      }
    }
  }
}
```

Get a free API key, no card needed: https://hauntapi.com/?utm_source=github&utm_medium=readme&utm_campaign=mcp_server#signup

Prefer a CLI? `npx -y --package @hauntapi/cli@latest haunt-cli init` prints the
same block for Claude, Cursor, Windsurf and other MCP clients. It prints config,
it does not edit your files, and it is not itself the server.

### 2. Prove it is wired in, no key needed

Call `try_demo_extract` first. It returns a fixed sample extraction JSON and trace
plus docs, signup, pricing and free-tier links, without using credits.

```text
Use Haunt's try_demo_extract tool and show me the signup and docs links.
```

### 3. Ask for real data

```text
Use Haunt to extract the top five story titles from https://news.ycombinator.com/
```

For Markdown output:

```text
Use Haunt extract_markdown to turn https://fastapi.tiangolo.com/tutorial/ into clean Markdown.
```

Reddit, with no Reddit app and no OAuth:

```text
Use Haunt read_reddit to get the top 10 posts from r/webscraping.
```

Map or crawl a small site:

```text
Use Haunt map_site on https://fastapi.tiangolo.com/ and return the first 100 URLs under /tutorial/.
```

```text
Use Haunt crawl_site on https://fastapi.tiangolo.com/tutorial/ for up to 10 pages. Extract each page title and main summary.
```


## Capability boundaries

Haunt renders pages in a real browser and reads many Cloudflare-protected and bot-walled pages. It does **not** go past login walls, paywalls, or CAPTCHA human-verification pages, and it does not promise universal extraction. Those return a typed failure signal (`login_required`, `captcha_required`, `not_found`, `upstream_fetch_failed`) instead of fabricated data, and a failed read is not charged.

## Tools

### `try_demo_extract`

No-key activation check. Returns a fixed sample extraction JSON/trace, Haunt's demo endpoint, docs, signup, pricing, MCP info route, and free-tier details. Use this first when a user has installed the MCP server but has not added `HAUNT_API_KEY` yet.

### `extract` / `extract_url`

General-purpose extraction from permitted public web pages. `extract` and `extract_url` are aliases so hosted MCP docs and local stdio package users can follow the same wording.

Use it for:

- Product names, prices, stock status, reviews
- Competitor pricing pages
- Directories and lead lists
- Job boards
- Research pages
- Supported permitted public pages where you want clean JSON instead of HTML

It accepts optional `response_format` values: `json` (default), `markdown` / `md`, and `raw_html` / `html`.

### `extract_markdown`

Return clean Markdown from a permitted public page. Use this when the agent or workflow wants readable page text for RAG, notes, docs ingestion, or saving as a `.md` file instead of structured fields.

### `extract_article`

Extract article fields from news, blog, and editorial pages.

Returns title, body text, author, and publish date when available.

### `extract_metadata`

Extract page metadata including title, description, Open Graph tags, Twitter Card tags, canonical URL, and related metadata.

### `map_site`

Discover up to 500 public same-site URLs from robots.txt, sitemaps, and bounded
link traversal. Mapping costs no credits and is available on paid plans.

### `crawl_site`

Discover and apply one prompt and optional JSON Schema across up to 20 public
same-site pages. Complete pages use normal extraction credits; partial and failed
pages cost nothing. Discovery respects robots rules and fetched crawl content is
not stored.

### `read_reddit`

Read Reddit posts or a post's comment thread as structured JSON. No Reddit app, no OAuth, no developer account. Accepts a subreddit URL, a post URL, or shorthand like `r/webdev`. Set `comments` to true to read a thread.

Costs 1 credit, and a blocked read costs nothing.

### `company_profile`

Turn a company website URL into a structured profile: what the company does, its product, and the contact and social details published on the site. Read live from the site rather than a stale third-party database.

Costs no credits.

### `github_repo`

Return normalised metadata for a public GitHub repository: description, stars, forks, language, licence, topics, and last push.

Costs no credits.

### `get_usage`

Check current plan, monthly credit limit, used credits, reserved credits, and remaining credits. Use this after a live extraction to see what was charged.

## Why Haunt

- Reddit posts and comments with no Reddit app, OAuth, or developer account
- Natural-language prompts instead of fragile CSS selectors
- Robots-aware site mapping and bounded multi-page extraction
- Supported fetch paths for JavaScript-heavy pages
- Challenge-aware extraction with machine-readable verification signals (`error_code`, `captcha_provider`, `requires_human_verification`)
- Clean JSON output for agents, databases, and workflows
- Clean Markdown output when the job is page text for agents, RAG, notes, or `.md` files
- Free tier for testing

## Pricing

| Plan | Credits | Price |
|------|---------|-------|
| Free | 1,000/mo | £0 |
| Starter | 10,000/mo | £19/mo |
| Pro | 30,000/mo | £49/mo |
| Scale | 80,000/mo | £99/mo |

Credits are not one-to-one requests. Simple public/non-LLM output usually uses 1 credit, normal structured extraction 2, browser-rendered or authenticated extraction 4, and heavy/screenshot extraction 8. Failed, blocked, login/CAPTCHA, provider, and server failures do not burn credits.

Upgrade: https://hauntapi.com/#pricing

## Links

- Website: https://hauntapi.com
- Docs: https://hauntapi.com/docs
- Get API key: https://hauntapi.com/?utm_source=github&utm_medium=readme&utm_campaign=mcp_server#signup
- GitHub: https://github.com/Darko893/haunt-mcp-server
