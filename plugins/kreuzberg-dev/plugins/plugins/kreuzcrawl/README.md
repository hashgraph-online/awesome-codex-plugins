# kreuzcrawl

Crawl, scrape, and convert websites to Markdown using the local `kreuzcrawl` CLI in your agent.

<!-- TODO: screenshot -->

## Install

### From the marketplace (recommended)

Pending review for official Claude marketplace.

Self-host:

```text
/plugin marketplace add kreuzberg-dev/plugins
/plugin install kreuzcrawl@kreuzberg
```

### Binary requirement

The MCP server runs through an auto-installing launcher (`scripts/mcp-launch.sh`): on first use it reuses any working `kreuzcrawl` binary already on `PATH`, then tries `npx`/`uvx`, then Homebrew, then a prebuilt download. No manual install is required for MCP.

To install the CLI yourself (recommended for direct CLI use, and reused by the launcher):

```bash
brew install kreuzberg-dev/tap/kreuzcrawl
# or run it without a persistent install (the CLI proxy package self-installs the binary):
npx @kreuzberg/kreuzcrawl-cli --help
uvx --from kreuzcrawl-cli kreuzcrawl --help
# or build from source (the mcp/api subcommands are non-default features):
cargo install --git https://github.com/kreuzberg-dev/kreuzcrawl kreuzcrawl-cli --features all
```

The published npm (`@kreuzberg/kreuzcrawl`) and PyPI (`kreuzcrawl`) packages are language *library* bindings, not the CLI — install via Homebrew or the from-source build above for the `kreuzcrawl` binary.

Headless fallback requires Chrome/Chromium on your system. The CLI launches it on demand; skip the binary if you only plan to use `--browser-mode never`.

## Skills shipped

| Skill | Trigger |
|-------|---------|
| **kreuzcrawl** | Crawl, scrape, and convert websites to Markdown using the local kreuzcrawl CLI and its MCP server. Use when the user wants to fetch a page, follow links across a domain, enumerate URLs, or drive a real browser. Covers installation, the subcommands (scrape, crawl, map, interact, mcp, serve), output formats (JSON + Markdown), browser fallback, and when to prefer the MCP server over shelling out. |
| **crawling-a-site** | Use when the user wants to follow links across a domain and capture every reachable page as Markdown. Covers `kreuzcrawl crawl` with depth, page caps, concurrency, rate limiting, domain scoping, robots, and output selection. |
| **scraping-html-to-markdown** | Use when the user wants a single page rendered as clean Markdown plus structured metadata. Covers `kreuzcrawl scrape <url>`, JSON vs Markdown output, what metadata is returned, and how to handle JS-heavy pages. |
| **mapping-urls** | Use when the user wants the list of URLs on a site rather than the page content — sitemap analysis, link planning, or seeding another tool. Covers `kreuzcrawl map <url>` with `--limit`, `--search`, robots, output, and how it differs from a full crawl. |
| **automating-the-browser** | Use when extracting a page needs scripted interaction first — click, type, press a key, scroll, wait, screenshot, or run JS before capturing the DOM. Covers `kreuzcrawl interact <url> --actions` with the real action schema, result shape, limits, and external-CDP options. |
| **serving-the-api** | Use when the user wants a long-running HTTP service for scrape/crawl/map instead of one-shot CLI calls or the MCP server. Covers `kreuzcrawl serve`, the Firecrawl-v1-compatible endpoints, `--host`/`--port`, and when to prefer it. |
| **headless-fallback** | Use when a static fetch returns nothing useful and the page needs a real browser. Covers `--browser-mode auto\|always\|never`, external CDP via `--browser-endpoint`, symptoms of JS-only pages and WAF blocks, and the performance cost. |

## MCP / CLI

The plugin wires up the `kreuzcrawl` MCP server via `scripts/mcp-launch.sh`, which resolves or installs a version-matched binary, then runs `kreuzcrawl mcp` over stdio. Override binary resolution with `KREUZCRAWL_LAUNCHER=auto|download`.

The MCP server exposes:

- `scrape` — fetch and convert a single URL to Markdown or JSON.
- `crawl` — follow links across a domain, bounded by depth and page count.
- `map` — enumerate URLs from sitemaps and link extraction.
- `interact` — drive a headless browser with click, type, scroll actions.

The CLI offers the same operations plus `serve` (a Firecrawl-v1-compatible REST API server). See the `serving-the-api` skill for when to run the server instead of the CLI or MCP.

## Configuration

Pass flags or use inline JSON via `--config`:

```bash
kreuzcrawl scrape https://example.com \
  --format markdown \
  --browser-mode auto \
  --timeout 30000
```

For complex configs, use JSON:

```bash
kreuzcrawl crawl https://example.com \
  --config '{"depth":3,"max_pages":200,"concurrent":8,"respect_robots_txt":true}'
```

See the `kreuzcrawl` and `crawling-a-site` skills for the full flag surface.

## Examples

Fetch a single page and print Markdown:

```text
kreuzcrawl scrape https://example.com/article --format markdown
```

Crawl a site at depth 3 with rate limiting:

```text
kreuzcrawl crawl https://example.com --depth 3 --max-pages 200 --concurrent 8 --stay-on-domain --format markdown
```

Enumerate URLs from a sitemap:

```text
kreuzcrawl map https://example.com --limit 500
```

## Versioning

The plugin version tracks the marketplace `VERSION` file. See [CHANGELOG.md](../../CHANGELOG.md) for release notes.

## License

MIT.

## See also

- **Marketplace**: [kreuzberg-dev/plugins](https://github.com/kreuzberg-dev/plugins)
- **Upstream**: [kreuzberg-dev/kreuzcrawl](https://github.com/kreuzberg-dev/kreuzcrawl)
- **Sibling plugins**: [kreuzberg](../kreuzberg/README.md), [kreuzberg-cloud](../kreuzberg-cloud/README.md)
