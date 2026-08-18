---
name: scraping-html-to-markdown
description: >-
  Use when the user wants a single page rendered as clean Markdown plus
  structured metadata. Covers `kreuzcrawl scrape <url>`, JSON vs Markdown
  output, what metadata is returned, and how to handle JS-heavy pages.
---

# Scraping HTML to Markdown

`kreuzcrawl scrape <url>` is the right tool when the user has a single
page in mind. It returns Markdown plus a full structured payload (metadata,
links, images, JSON-LD, HTTP response info).

## Quick recipe

```bash
kreuzcrawl scrape https://example.com/article --format markdown
```

JSON form (default) when downstream needs metadata:

```bash
kreuzcrawl scrape https://example.com/article --format json
```

## Flag surface

| Flag                    | Default | Purpose                                                |
| ----------------------- | ------- | ------------------------------------------------------ |
| `--format`              | `json`  | `json` or `markdown`.                                  |
| `--timeout`             | `30000` | Per-request timeout in ms.                             |
| `--proxy`               | —       | HTTP, HTTPS, or SOCKS5 proxy URL.                      |
| `--user-agent`          | —       | Override request UA.                                   |
| `--respect-robots-txt`  | off     | Honour `robots.txt`.                                   |
| `--browser-mode`        | `auto`  | `auto`, `always`, `never` — see headless-fallback skill. |
| `--browser-endpoint`    | —       | External CDP `ws://` URL.                              |
| `--config`              | —       | Inline JSON or `@file.json` for full `CrawlConfig`.    |

## Output shape

### Markdown mode

Prints the rendered Markdown only. Use when piping to a file the user will
read, or when the result becomes LLM context downstream.

### JSON mode

Top-level `PageResult` with:

- `url`, `final_url` (after redirects), `status_code`.
- `markdown`: `{ content, fit_content, warnings }` — `fit_content` is a
  pruned LLM-optimised variant.
- `metadata`: Open Graph, Twitter Card, Dublin Core, article tags, JSON-LD,
  headings (H1–H6), feeds, favicons, hreflang.
- `links`: arrays for `Internal`, `External`, `Anchor`, and `Document`.
- `images`: `<img>`, `<picture>`, `srcset`, `og:image`.
- `tables`: structured table data preserved separately from Markdown.
- `response`: HTTP headers, content type, charset, body size.

Read `result.markdown.content` for the Markdown string when scripting.

## Common pitfalls

### Empty or stub content

Static fetch returned a JS shell. Symptoms in JSON output:

- `markdown.content` is short or only contains nav/footer chrome.
- `markdown.warnings` mentions JS-render-required.
- `metadata.headings` is empty when the page clearly has headings.

Re-run with `--browser-mode always` and see the headless-fallback skill.

### WAF block

`Auto` mode detects 8 WAF vendors and retries through headless Chrome
automatically. If you forced `--browser-mode never`, the WAF response will
fall through. Check `response.status_code` — 403/406/503 with WAF headers
(`server: cloudflare`, `x-amz-cf-id`, etc.) is the giveaway.

### Robots.txt blocking the fetch

If `--respect-robots-txt` is set and the path is disallowed, the scrape
returns an error rather than partial content. Drop the flag only on hosts
you own or have authorisation for.

### Wrong charset

Most pages declare UTF-8. Pages that lie about their charset surface as
mojibake in `markdown.content`. Override via `--config '{"force_encoding":"latin-1"}'`
or similar.

## Examples

### Scrape an article for downstream LLM context

```bash
kreuzcrawl scrape https://blog.example.com/post-123 --format markdown \
  > /tmp/article.md
```

### Scrape with proxy and custom UA

```bash
kreuzcrawl scrape https://example.com \
  --proxy http://proxy.internal:3128 \
  --user-agent "kreuzcrawl (research@example.com)" \
  --format json
```

### Extract just the OG metadata

```bash
kreuzcrawl scrape https://example.com --format json \
  | jq '.metadata | {title: .og.title, description: .og.description, image: .og.image}'
```

## When to reach for crawl or interact instead

- The user wants the whole site, not one page → `crawling-a-site` skill.
- The user needs to click, type, or scroll before extracting → use
  `kreuzcrawl interact` with the action list.
- The user only wants the list of URLs → `kreuzcrawl map`.
