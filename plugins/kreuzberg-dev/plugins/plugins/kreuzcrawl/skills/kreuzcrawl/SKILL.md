---
name: kreuzcrawl
description: >-
  Crawl, scrape, and convert websites to Markdown using the local kreuzcrawl
  CLI and its MCP server. Use when the user wants to fetch a page, follow
  links across a domain, enumerate URLs, or drive a real browser. Covers
  installation, the subcommands (scrape, crawl, map, interact, mcp, serve),
  output formats (JSON + Markdown), browser fallback, and when to prefer the
  MCP server over shelling out.
license: MIT
metadata:
  author: kreuzberg-dev
  version: "0.1.0"
  repository: https://github.com/kreuzberg-dev/kreuzcrawl
---

# Kreuzcrawl

Kreuzcrawl is a Rust-native web crawler and scraper. It fetches static HTML
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

The plugin shells out to a `kreuzcrawl` binary on `PATH`. Install one of:

```bash
brew install kreuzberg-dev/tap/kreuzcrawl
# or run without a persistent install (the CLI proxy package self-installs the binary):
npx @kreuzberg/kreuzcrawl-cli --help
uvx --from kreuzcrawl-cli kreuzcrawl --help
# or build from source:
cargo install --git https://github.com/kreuzberg-dev/kreuzcrawl kreuzcrawl-cli --features all
```

The `serve` and `mcp` subcommands are gated behind non-default cargo features
(`api` and `mcp`). The Homebrew tap is built with all features, so both
subcommands work out of the box. A from-source build must pass
`--features mcp` (and `--features api` for `serve`), or `--features all`, to
include them.

Verify:

```bash
kreuzcrawl --version
```

Headless fallback needs Chrome/Chromium reachable locally (`chromiumoxide`
launches it on demand). Skip the install if you only plan to use
`--browser-mode never`.

## Command map

```text
kreuzcrawl scrape <url>     # single page → JSON or Markdown
kreuzcrawl crawl <url...>   # follow links, BFS, depth-bounded
kreuzcrawl map <url>        # enumerate URLs via sitemaps + link extraction
kreuzcrawl interact <url>   # browser actions: click, type, scroll
kreuzcrawl mcp              # MCP server (stdio) — auto-registered (`mcp` feature)
kreuzcrawl serve            # REST API server (`api` feature)
```

Batch behaviour is built into `crawl`: pass multiple seed URLs and the engine
fans out via `batch_crawl` internally.

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

## Scrape a single page

```bash
kreuzcrawl scrape https://example.com --format markdown
```

JSON output (default) carries the rendered Markdown, page metadata
(`PageMetadata`), links by category, images, feeds, JSON-LD blocks, and
HTTP response metadata. Use Markdown output when piping into a file the user
will read.

See the `scraping-html-to-markdown` skill for the full flag surface.

## Crawl a site

```bash
kreuzcrawl crawl https://example.com \
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
kreuzcrawl map https://example.com --limit 500 --search docs --format markdown
```

`map` reads `sitemap.xml` (and nested sitemaps), then falls back to link
extraction from the seed page. It does not render pages — use it to plan a
crawl or to feed URLs into another tool.

## Browser interaction

```bash
kreuzcrawl interact https://example.com \
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
kreuzcrawl mcp
```

`mcp` is a stdio-transport server and takes no arguments. It requires a binary
built with the `mcp` feature (see Installation).

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
