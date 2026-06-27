---
name: serving-the-api
description: >-
  Use when the user wants a long-running HTTP service for scrape/crawl/map
  instead of one-shot CLI calls or the MCP server — for example wiring
  crawlberg into other apps over REST. Covers `crawlberg serve`, the
  Firecrawl-v1-compatible endpoints, `--host`/`--port`, and when to prefer it.
---

# Serving the API

`crawlberg serve` starts a long-running REST API server exposing the crawl
engine over HTTP. The endpoints are Firecrawl v1-compatible, so existing
Firecrawl clients and SDKs can point at a local crawlberg instance.

This subcommand requires the binary to be built with the optional `api`
feature (non-default). The Homebrew tap is built with all features, so `serve`
is available there; a from-source build needs
`cargo install --git https://github.com/xberg-io/crawlberg crawlberg-cli --features api`
(or `--features all`) to include it.

## Quick recipe

```bash
crawlberg serve --host 127.0.0.1 --port 3000
```

It logs `Starting REST API server on <host>:<port>` to stderr and blocks until
terminated. Hit `GET /health` to confirm it is up.

## Flags

| Flag     | Default   | Purpose                          |
| -------- | --------- | -------------------------------- |
| `--host` | `0.0.0.0` | Address to bind to.              |
| `--port` | `3000`    | Port to listen on.               |

`serve` does not take the per-request crawl flags — it boots with the default
`CrawlConfig` and accepts per-request options in each HTTP request body.

## Endpoints

Firecrawl v1 surface:

| Method + path             | Purpose                                              |
| ------------------------- | ---------------------------------------------------- |
| `POST /v1/scrape`         | Scrape a single URL (synchronous).                   |
| `POST /v1/crawl`          | Start an asynchronous crawl job → returns a job `id`. |
| `GET /v1/crawl/{id}`      | Poll crawl job status and collect results.           |
| `DELETE /v1/crawl/{id}`   | Cancel a running crawl job.                          |
| `POST /v1/map`            | Discover URLs on a site (synchronous).               |
| `POST /v1/batch/scrape`   | Start an asynchronous batch-scrape job → job `id`.   |
| `GET /v1/batch/scrape/{id}` | Poll batch-scrape job status and results.          |
| `POST /v1/download`       | Download a document from a URL.                      |

Operational:

| Method + path     | Purpose                                  |
| ----------------- | ---------------------------------------- |
| `GET /health`     | Health check (`{ status, version }`).    |
| `GET /version`    | Version information.                     |
| `GET /openapi.json` | OpenAPI schema for the whole surface.  |

Request bodies use `camelCase` fields. Scrape/crawl/map mirror the CLI:
`url`, `formats`, `onlyMainContent`, `includeTags`/`excludeTags`, `timeout`
for scrape; `url`, `maxDepth`, `maxPages`, `includePaths`/`excludePaths` for
crawl; `url`, `limit`, `search` for map. Responses wrap data as
`{ success, data | error }`; async jobs return `{ success, id }` and are polled
for `{ status, total, completed, data, error }`.

## Examples

### Scrape via HTTP

```bash
curl -s http://127.0.0.1:3000/v1/scrape \
  -H 'content-type: application/json' \
  -d '{"url":"https://example.com","formats":["markdown"]}' | jq '.data'
```

### Start a crawl job and poll it

```bash
id=$(curl -s http://127.0.0.1:3000/v1/crawl \
  -H 'content-type: application/json' \
  -d '{"url":"https://example.com","maxDepth":2,"maxPages":100}' | jq -r '.id')

curl -s "http://127.0.0.1:3000/v1/crawl/$id" | jq '{status,completed,total}'
```

### Map URLs

```bash
curl -s http://127.0.0.1:3000/v1/map \
  -H 'content-type: application/json' \
  -d '{"url":"https://example.com","limit":500,"search":"docs"}' | jq '.data'
```

## Operational notes

- The server accepts CORS from any origin and ships **no built-in
  authentication** — do not expose it on a public interface. Bind to
  `127.0.0.1` for local use, or put it behind a reverse proxy / gateway that
  enforces auth and rate limiting before exposing it more widely.
- Request bodies are capped at 10 MB and each request times out after 5
  minutes.
- Crawl and batch-scrape are asynchronous: the POST returns a job `id`
  immediately and you poll the `{id}` endpoint until `status` is `completed`,
  `failed`, or `cancelled`.

## When to run serve vs. CLI vs. MCP

- **CLI** (`scrape`/`crawl`/`map`/`interact`) — one-shot jobs, shell pipelines,
  scripting. No long-running process.
- **MCP** (`crawlberg mcp`) — driving the crawler from an AI agent harness
  (Claude Code, Codex, Cursor, Gemini, opencode). Auto-registered by this
  plugin; prefer it inside an agent.
- **serve** (`crawlberg serve`) — a persistent HTTP service for other
  applications or non-agent clients that speak REST, or when you want
  Firecrawl-v1 compatibility. Choose it when many callers need the crawler
  over the network rather than one agent or one shell.
