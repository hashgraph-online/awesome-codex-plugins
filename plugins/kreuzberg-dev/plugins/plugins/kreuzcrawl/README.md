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

Install the `kreuzcrawl` CLI:

```bash
brew install kreuzberg-dev/tap/kreuzcrawl
# or
cargo install kreuzcrawl-cli
```

Headless fallback requires Chrome/Chromium on your system. The CLI launches it on demand; skip the binary if you only plan to use `--browser-mode never`.

## Skills shipped

| Skill | Trigger |
|-------|---------|
| **kreuzcrawl** | Crawl, scrape, and convert websites to Markdown using the local kreuzcrawl CLI and its MCP server. Use when the user wants to fetch a page, follow links across a domain, enumerate URLs, or drive a real browser. Covers installation, the subcommands (scrape, crawl, map, interact, mcp, serve), output formats (JSON + Markdown), browser fallback, and when to prefer the MCP server over shelling out. |
| **crawling-a-site** | Use when the user wants to follow links across a domain and capture every reachable page as Markdown. Covers `kreuzcrawl crawl` with depth, page caps, concurrency, rate limiting, domain scoping, robots, and output selection. |
| **scraping-html-to-markdown** | Use when the user wants a single page rendered as clean Markdown plus structured metadata. Covers `kreuzcrawl scrape <url>`, JSON vs Markdown output, what metadata is returned, and how to handle JS-heavy pages. |
| **headless-fallback** | Use when a static fetch returns nothing useful and the page needs a real browser. Covers `--browser-mode auto\|always\|never`, external CDP via `--browser-endpoint`, symptoms of JS-only pages and WAF blocks, and the performance cost. |

## MCP tools

The `kreuzcrawl` MCP server exposes:

- `scrape` — fetch and convert a single URL to Markdown or JSON.
- `crawl` — follow links across a domain, bounded by depth and page count.
- `map` — enumerate URLs from sitemaps and link extraction.
- `interact` — drive a headless browser with click, type, scroll actions.

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
