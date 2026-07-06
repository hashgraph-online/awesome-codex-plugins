---
name: crawling-a-site
description: >-
  Use when the user wants to follow links across a domain and capture every
  reachable page as Markdown. Covers `crawlberg crawl` with depth, page
  caps, concurrency, rate limiting, domain scoping, robots, and output
  selection.
---

# Crawling a site

Reach for `crawlberg crawl` when one URL is not enough — the user wants
the docs site, the blog, the marketing pages, or the whole domain.

## Quick recipe

```bash
crawlberg crawl https://example.com \
  --depth 3 \
  --max-pages 200 \
  --concurrent 8 \
  --rate-limit 250 \
  --stay-on-domain \
  --respect-robots-txt \
  --format markdown
```

Defaults you should usually override:

- `--depth 2` is shallow — set it explicitly.
- `--max-pages` is unbounded by default; cap it for any unknown site.
- `--concurrent 10` is aggressive for small hosts; drop to 4-8 for
  third-party sites.

## Flag surface

| Flag                    | Default | Purpose                                                    |
| ----------------------- | ------- | ---------------------------------------------------------- |
| `--depth`, `-d`         | `2`     | Maximum hop count from the seed URL.                       |
| `--max-pages`, `-n`     | —       | Hard cap on pages fetched. Set this on any unknown site.   |
| `--concurrent`, `-c`    | `10`    | Parallel in-flight requests.                               |
| `--rate-limit`          | `200`   | Milliseconds between requests to the same origin.          |
| `--stay-on-domain`      | off     | Skip links that leave the seed domain.                     |
| `--respect-robots-txt`  | off     | Honour `robots.txt`. Pass it for any third-party host.     |
| `--proxy`               | —       | HTTP, HTTPS, or SOCKS5 proxy URL.                          |
| `--user-agent`          | —       | Override the request UA. Be honest.                        |
| `--timeout`             | `30000` | Per-request timeout in ms.                                 |
| `--browser-mode`        | `auto`  | `auto`, `always`, `never` — see the headless-fallback skill. |
| `--browser-endpoint`    | —       | External CDP `ws://` URL.                                  |
| `--format`              | `json`  | `json` or `markdown`.                                      |
| `--config`              | —       | Inline JSON or `@file.json` for the full `CrawlConfig`.    |

Multiple seed URLs are accepted positionally — the engine fans out with
`batch_crawl` and aggregates results.

## When to pick which flags

### Docs sites you own

```bash
crawlberg crawl https://docs.example.com \
  --depth 5 --max-pages 1000 --concurrent 16 --rate-limit 100 \
  --stay-on-domain --format markdown > docs.md
```

Higher concurrency and lower rate limits are fine on infrastructure you
control.

### Third-party sites

```bash
crawlberg crawl https://blog.unknown.example \
  --depth 2 --max-pages 50 --concurrent 4 --rate-limit 500 \
  --stay-on-domain --respect-robots-txt --format markdown
```

Stay shallow, cap pages, throttle hard, obey robots.

### Multi-seed batch

```bash
crawlberg crawl \
  https://example.com/blog \
  https://example.com/docs \
  https://example.com/pricing \
  --depth 2 --max-pages 100 --stay-on-domain --format json
```

JSON output for batch is an array of `{ seed_url, result }` entries — each
`result` is a full crawl payload or `{ error: ... }`.

## Output

### Markdown mode

```text
---
URL: https://example.com/page-one
---
# Page One

… markdown content …

---
URL: https://example.com/page-two
---
…
```

### JSON mode

Top-level `CrawlResult` with `pages: [...]`. Each page carries the rendered
Markdown plus metadata, links, images, JSON-LD, and HTTP response info. Read
`result.pages[i].markdown.content` for the Markdown string.

## Politeness checklist

- Pass `--respect-robots-txt` on every third-party crawl.
- Cap `--max-pages` — a runaway BFS can issue tens of thousands of requests.
- Bump `--rate-limit` for hosts that show signs of stress (5xx, slowdowns).
- Identify yourself via `--user-agent crawlberg (contact@example.com)`.

## Common pitfalls

- **No pages returned.** The seed page may be JS-only — the engine falls
  back to headless automatically in `--browser-mode auto`, but `never` mode
  will silently produce an empty crawl. Re-run with `--browser-mode always`
  or check the headless-fallback skill.
- **Crawl leaves the domain.** Pass `--stay-on-domain`. Combine with
  `allow_subdomains: true` in `--config` JSON to include subdomains.
- **Slow crawl.** The default rate limit is 200 ms per origin — multiple
  seed URLs on the same host still share the bucket. Spread seeds across
  hosts or raise `--concurrent` for unrelated origins.
- **Memory growth.** Each page carries full Markdown plus structured data.
  Stream JSON output to a file rather than holding it in memory; set
  `--max-pages` aggressively if downstream cannot keep up.

## When to reach for `map` instead

If the user only needs the list of URLs (sitemap analysis, link planning,
seeding another tool), use `crawlberg map <url>` — it skips rendering and
returns a flat `MapResult` with hundreds of URLs in seconds.
