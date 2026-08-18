---
name: mapping-urls
description: >-
  Use when the user wants the list of URLs on a site rather than the page
  content — sitemap analysis, link planning, or seeding another tool. Covers
  `kreuzcrawl map <url>` with `--limit`, `--search`, robots, output, and how it
  differs from a full crawl.
---

# Mapping URLs

`kreuzcrawl map <url>` discovers the URLs a site exposes without rendering or
extracting any page content. It reads `sitemap.xml` (including nested
sitemaps), then falls back to link extraction from the seed page. Use it to
plan a crawl, audit a site's surface, or feed a URL list into another tool.

## Quick recipe

```bash
kreuzcrawl map https://example.com --limit 500 --search docs --format markdown
```

Markdown output prints one URL per line — convenient to pipe into a file or a
follow-up `crawl`. JSON output (default) returns a structured `MapResult`.

## Flag surface

| Flag                   | Default | Purpose                                                       |
| ---------------------- | ------- | ------------------------------------------------------------- |
| `--limit`              | —       | Maximum number of URLs to return. Unbounded if unset.         |
| `--search`             | —       | Case-insensitive substring filter on discovered URLs.         |
| `--respect-robots-txt` | off     | Honour `robots.txt`. Pass it for any third-party host.        |
| `--format`             | `json`  | `json` (full `MapResult`) or `markdown` (one URL per line).   |
| `--timeout`            | `30000` | Per-request timeout in ms.                                    |
| `--browser-mode`       | `auto`  | `auto`, `always`, `never` — see the headless-fallback skill.  |
| `--browser-endpoint`   | —       | External CDP `ws://` URL.                                     |
| `--config`             | —       | Inline JSON or `@file.json` for the full `CrawlConfig`.       |

`map` takes a single seed URL positionally. There is no `--depth` or
`--max-pages` here — those bound a `crawl`, not a map. Scope is the seed host's
sitemaps plus links found on the seed page; bound the result with `--limit` and
narrow it with `--search`.

## How discovery works

1. Fetch and parse `sitemap.xml`, following nested `<sitemapindex>` entries.
2. If no sitemap (or a thin one), extract links from the seed page's HTML.
3. Apply the `--search` substring filter (case-insensitive), then `--limit`.

No page bodies are rendered, so a map of hundreds of URLs returns in seconds —
far cheaper than crawling. In `--browser-mode auto` the seed fetch still falls
back to headless Chrome if the seed page is a JS shell that hides its links;
pass `--browser-mode never` to keep it static-only.

## Output

### Markdown mode

```text
https://example.com/
https://example.com/docs/
https://example.com/docs/getting-started
https://example.com/blog/post-one
```

### JSON mode

Top-level `MapResult` with a `urls` array; each entry carries the discovered
`url`. Read `result.urls[i].url` for each string when scripting.

```bash
kreuzcrawl map https://example.com --format json | jq -r '.urls[].url'
```

## Common patterns

### Discover then crawl a subsection

```bash
kreuzcrawl map https://example.com --search /docs/ --format markdown > urls.txt
```

Feed the filtered list into a bounded crawl, or scrape individual entries.

### Audit a third-party site politely

```bash
kreuzcrawl map https://unknown.example --respect-robots-txt --limit 200
```

## When to reach for crawl instead

If the user needs the page *content* (Markdown, metadata, tables) rather than
just the URL list, use `kreuzcrawl crawl` — see the `crawling-a-site` skill.
Reach for `map` first when the goal is enumeration, planning, or seeding.
