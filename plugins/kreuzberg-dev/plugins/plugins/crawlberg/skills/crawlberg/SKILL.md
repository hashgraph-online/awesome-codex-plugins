---
name: crawlberg
description: >-
  Crawl, scrape, and convert websites to Markdown using the local crawlberg
  CLI and its MCP server. Use when the user wants to fetch a page, follow
  links across a domain, enumerate URLs, or drive a real browser. Covers
  installation, the subcommands (scrape, crawl, map, interact, batch-scrape,
  batch-crawl, download, citations, version, mcp, serve), output formats
  (JSON + Markdown), browser fallback, and when to prefer the MCP server over
  shelling out.
license: MIT
metadata:
  author: xberg-io
  version: "0.1.0"
  repository: https://github.com/xberg-io/crawlberg
---

# Crawlberg

Crawlberg is a Rust-native web crawler and scraper. It fetches static HTML
with `reqwest`, falls back to headless Chrome when a page needs JS or trips a
WAF, and converts every result to clean Markdown via the built-in
HTML→Markdown engine.

Use this skill when the user wants to:

- Scrape a single URL to Markdown plus structured metadata.
- Crawl a site following links bounded by depth, page count, and concurrency.
- Enumerate URLs from sitemaps without paying for rendering.
- Drive a real browser (click, type, scroll) and capture the resulting DOM.
- Run the same operations from another agent harness via MCP tools.

## Installation

The plugin shells out to a `crawlberg` binary on `PATH`. Install one of:

```bash
brew install xberg-io/tap/crawlberg
# or run without a persistent install (the CLI proxy package self-installs the binary):
npx @xberg-io/crawlberg-cli --help
uvx --from crawlberg-cli crawlberg --help
# or build from source:
cargo install crawlberg-cli --features all
```

The `serve` and `mcp` subcommands are gated behind non-default cargo features
(`api` and `mcp`). The Homebrew tap is built with all features, so both
subcommands work out of the box. A from-source build must pass
`--features mcp` (and `--features api` for `serve`), or `--features all`, to
include them.

Verify:

```bash
crawlberg --version
```

Headless fallback needs Chrome/Chromium reachable locally (`chromiumoxide`
launches it on demand). Skip the install if you only plan to use
`--browser-mode never`.

## Command map

```text
crawlberg scrape <url>          # single page → JSON or Markdown
crawlberg crawl <url...>        # follow links, BFS, depth-bounded
crawlberg map <url>             # enumerate URLs via sitemaps + link extraction
crawlberg interact <url>        # browser actions: click, type, scroll
crawlberg batch-scrape <url...> # scrape many URLs concurrently
crawlberg batch-crawl <url...>  # crawl many seed URLs concurrently
crawlberg download <url>        # download a document, report file metadata
crawlberg citations <input>     # markdown links → numbered citations (text or @file.md)
crawlberg version               # print the crawlberg version as JSON
crawlberg mcp                   # MCP server (stdio) — auto-registered (`mcp` feature)
crawlberg serve                 # REST API server (`api` feature)
```

`crawl` also handles batching implicitly: pass multiple seed URLs and it fans
out via `batch_crawl` internally. The explicit `batch-scrape` and `batch-crawl`
subcommands expose the same concurrency for many independent URLs.

Per-subcommand flags:

| Subcommand     | Positional        | Key flags                                                                                                      |
| -------------- | ----------------- | ------------------------------------------------------------------------------------------------------------- |
| `scrape`       | `<url>`           | `--proxy`, `--user-agent` (plus shared flags below)                                                            |
| `crawl`        | `<url...>`        | `--depth`/`-d` (2), `--max-pages`/`-n`, `--concurrent`/`-c` (10), `--rate-limit` (200), `--stay-on-domain`, `--proxy`, `--user-agent` |
| `map`          | `<url>`           | `--limit`, `--search`                                                                                          |
| `interact`     | `<url>`           | `--actions <json>` (required)                                                                                  |
| `batch-scrape` | `<url...>`        | `--concurrent`/`-c` (10), `--proxy`, `--user-agent`                                                            |
| `batch-crawl`  | `<url...>`        | `--depth`/`-d` (2), `--max-pages`/`-n`, `--concurrent`/`-c` (10), `--rate-limit` (200), `--stay-on-domain`, `--proxy`, `--user-agent` |
| `download`     | `<url>`           | `--max-size`                                                                                                   |
| `citations`    | `<input>`         | none (input is markdown text or `@file.md`)                                                                    |
| `version`      | —                 | none                                                                                                           |
| `serve`        | —                 | `--host` (0.0.0.0), `--port` (3000)                                                                            |
| `mcp`          | —                 | none (stdio transport)                                                                                         |

### Shared flags

| Flag                    | Default  | Notes                                              |
| ----------------------- | -------- | -------------------------------------------------- |
| `--format`              | `json`   | `json` or `markdown`.                              |
| `--timeout`             | `30000`  | Request timeout in milliseconds.                   |
| `--browser-mode`        | `auto`   | `auto`, `always`, or `never`.                      |
| `--browser-endpoint`    | —        | Optional CDP `ws://` or `wss://` URL.              |
| `--respect-robots-txt`  | off      | Pass to obey `robots.txt`.                         |
| `--config <json>`       | —        | Inline JSON or `@file.json` to override defaults.  |

The `--config` flag accepts the full `CrawlConfig` schema. Anything you set
explicitly on the CLI overrides the corresponding JSON field.

These shared flags apply to the crawl/scrape-family subcommands. `--format`,
`--browser-mode`, `--browser-endpoint`, and `--config` cover `scrape`, `crawl`,
`map`, `interact`, `batch-scrape`, and `batch-crawl`; `download` takes
`--timeout`, `--browser-mode`, `--browser-endpoint`, `--max-size`, and
`--config` (no `--format`). `--respect-robots-txt` applies to `scrape`,
`crawl`, `map`, `batch-scrape`, and `batch-crawl`. `citations` and `version`
take no shared flags.

## Scrape a single page

```bash
crawlberg scrape https://example.com --format markdown
```

JSON output (default) carries the rendered Markdown, page metadata
(`PageMetadata`), links by category, images, feeds, JSON-LD blocks, and
HTTP response metadata. Use Markdown output when piping into a file the user
will read.

See the `scraping-html-to-markdown` skill for the full flag surface.

## Crawl a site

```bash
crawlberg crawl https://example.com \
  --depth 3 --max-pages 200 --concurrent 8 --rate-limit 250 \
  --stay-on-domain --respect-robots-txt --format markdown
```

Crawling is BFS by default, bounded by `--depth`, `--max-pages`, and
`--concurrent`. Per-domain politeness is enforced by `--rate-limit`
(milliseconds between requests to the same origin).

See the `crawling-a-site` skill for the recommended defaults and the full
flag surface.

## Map URLs

```bash
crawlberg map https://example.com --limit 500 --search docs --format markdown
```

`map` reads `sitemap.xml` (and nested sitemaps), then falls back to link
extraction from the seed page. It does not render pages — use it to plan a
crawl or to feed URLs into another tool.

## Browser interaction

```bash
crawlberg interact https://example.com \
  --actions '[{"type":"click","selector":"#load-more"},
              {"type":"wait","milliseconds":500},
              {"type":"scrape"}]'
```

Action types are `click`, `type`, `press`, `scroll`, `wait`, `screenshot`,
`executeJs`, and `scrape` (to wait for an element, use `wait` with a
`selector` field). The result wraps the final HTML under
`interaction.final_html`. See the `automating-the-browser` skill for the full
action schema and limits.

## MCP server

When this plugin is installed in a Claude Code / Codex / Cursor / Gemini /
opencode harness, the MCP server is auto-registered:

```text
crawlberg mcp
```

`mcp` is a stdio-transport server and takes no arguments. It requires a binary
built with the `mcp` feature (see Installation).

The server registers nine tools (the same set is served over the Streamable
HTTP transport when running `crawlberg serve`):

| Tool                 | Purpose                                                          | Parameters                                                                                 |
| -------------------- | --------------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| `scrape`             | Scrape one URL to Markdown or JSON (content, metadata, links).  | `url` (required), `format` (`markdown`\|`json`), `use_browser` (bool — force browser)       |
| `crawl`              | Follow links from a URL, bounded by depth/page count.          | `url` (required), `max_depth`, `max_pages`, `format`, `stay_on_domain`                      |
| `map`                | Discover all URLs via links and sitemaps.                      | `url` (required), `limit`, `search`, `respect_robots_txt`                                   |
| `batch_scrape`       | Scrape multiple URLs concurrently.                            | `urls` (required array), `format`, `concurrency`                                            |
| `batch_crawl`        | Crawl multiple seed URLs concurrently.                       | `urls` (required array), `max_depth`, `max_pages`, `format`, `stay_on_domain`, `concurrency` |
| `download`           | Download a document and return file metadata.                | `url` (required), `max_size`                                                                |
| `interact`           | Execute browser actions on a page (mutating/destructive).    | `url` (required), `actions` (required array of action objects)                              |
| `generate_citations` | Rewrite markdown links as numbered citations + reference list. | `markdown` (required)                                                                       |
| `get_version`        | Return the crawlberg library version.                        | none                                                                                        |

Prefer MCP tools over shelling out when both are available:

- Typed schemas surface argument errors before the call.
- Results stream back as structured tool output instead of stdout text.
- No `--format` juggling — the harness pulls whatever shape it needs.

Fall back to the CLI when you need to script a pipeline, capture stderr, or
chain with shell tools.

## Headless fallback

In `--browser-mode auto` (default), the engine:

1. Fetches statically via `reqwest`.
2. Detects WAF blocks (8 vendors) and JS-only shells.
3. Re-fetches through headless Chrome with a real fingerprint when needed.

Force the browser path with `--browser-mode always` when you already know
the page needs JS. Use `--browser-mode never` for hot loops where the cost
of a stray Chrome launch is unacceptable.

Point `--browser-endpoint ws://host:9222/devtools/browser/<id>` at an
already-running Chrome to skip the local launch.

See the `headless-fallback` skill for symptoms, costs, and external-CDP
patterns.

## Output formats

| Mode       | Use when                                                |
| ---------- | ------------------------------------------------------- |
| `json`     | Downstream consumer needs metadata, links, images, etc. |
| `markdown` | Human reader or LLM-context payload.                    |

Markdown output skips metadata. If you need both, run with `--format json`
and read `result.markdown.content`.

## Robots, rate limits, ethics

- `--respect-robots-txt` is off by default; pass it for any crawl on a host
  you do not own.
- The default `--rate-limit 200` already produces a polite cadence; raise it
  for shared hosts.
- Identify the crawler honestly via `--user-agent`. Do not impersonate a
  browser unless the operator has approved it.

## Cross-references

- `skills/crawling-a-site/SKILL.md` — multi-page crawl with depth, page
  caps, concurrency, rate limits, and domain scoping.
- `skills/scraping-html-to-markdown/SKILL.md` — single-page rendering, the
  Markdown output shape, and common pitfalls.
- `skills/mapping-urls/SKILL.md` — `map`: sitemap + link URL discovery,
  filtering, and seeding a crawl.
- `skills/automating-the-browser/SKILL.md` — `interact`: the full scripted
  action schema, limits, and result shape.
- `skills/serving-the-api/SKILL.md` — `serve`: the Firecrawl-v1-compatible
  REST API server and its endpoints.
- `skills/headless-fallback/SKILL.md` — when and how to force the browser
  backend.
