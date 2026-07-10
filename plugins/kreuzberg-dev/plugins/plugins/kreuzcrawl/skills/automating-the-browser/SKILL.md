---
name: automating-the-browser
description: >-
  Use when extracting a page needs scripted interaction first — click, type,
  press a key, scroll, wait, screenshot, or run JS before capturing the DOM.
  Covers `kreuzcrawl interact <url> --actions` with the real action schema,
  result shape, limits, and external-CDP options.
---

# Automating the browser

`kreuzcrawl interact <url> --actions '[...]'` drives a real headless browser
through an ordered list of actions, then captures the resulting page. Reach for
it when a static scrape is not enough: the content lives behind a "Load more"
button, an infinite scroll, a form submission, or JS that only runs on
interaction.

## Quick recipe

```bash
kreuzcrawl interact https://example.com \
  --actions '[{"type":"click","selector":"#load-more"},
              {"type":"wait","milliseconds":500},
              {"type":"scrape"}]'
```

Actions run in order. The result wraps the final page state under
`interaction` (see Output below).

## Flag surface

| Flag                 | Default | Purpose                                                      |
| -------------------- | ------- | ------------------------------------------------------------ |
| `--actions`          | —       | Required. JSON array of action objects (see below).          |
| `--format`           | `json`  | `json` (full result) or `markdown` (final HTML only).        |
| `--timeout`          | `30000` | Per-request timeout in ms.                                   |
| `--browser-mode`     | `auto`  | `auto`, `always`, `never`. Interaction needs a browser.      |
| `--browser-endpoint` | —       | External CDP `ws://` or `wss://` URL.                        |
| `--config`           | —       | Inline JSON or `@file.json` for the full `CrawlConfig`.      |

There is no `--respect-robots-txt` flag on `interact`; it targets the one URL
you point it at.

## Action schema

Each action is a JSON object tagged by `type` (camelCase). Unknown fields are
rejected, so match the shapes exactly:

| `type`        | Fields                                                          | Notes                                                            |
| ------------- | -------------------------------------------------------------- | --------------------------------------------------------------- |
| `click`       | `selector`                                                     | Click the element matching the CSS selector.                    |
| `type`        | `selector`, `text`                                             | Type `text` into the input matching `selector`.                 |
| `press`       | `key`                                                          | Press a key, e.g. `"Enter"`, `"Tab"`, `"Escape"`.               |
| `scroll`      | `direction` (`"up"`/`"down"`), `selector?`, `amount?`         | Scroll the page, or a scrollable element if `selector` is set.  |
| `wait`        | `milliseconds?`, `selector?`                                   | Wait a fixed time, or until `selector` appears (`selector` wins). |
| `screenshot`  | `fullPage?`                                                    | Capture the viewport, or the full scrollable page if `true`.    |
| `executeJs`   | `script`                                                       | Run arbitrary JS in the page context. Trusted scripts only.     |
| `scrape`      | —                                                             | Capture the current page HTML into the result.                  |

There is no `select` action and no `wait_for_selector` action: to wait for an
element, use `wait` with a `selector` field. Scroll direction is `up` or
`down` only.

### Limits (enforced — exceeding them errors)

- Max 100 actions per call.
- Single `wait`: max 300000 ms; total wait across all `wait` actions: max 300 s.
- `selector` max 4096 bytes; `text` and `executeJs` `script` max 1 MB each.
- `scroll` `amount` max 100000 px (absolute).

## Output

### JSON mode (default)

The result is wrapped under an `interaction` key. It carries the final page
HTML (`interaction.final_html`) and a per-action record under
`interaction.action_results[...]` — including screenshot data and `executeJs`
return values where applicable.

```bash
kreuzcrawl interact https://example.com \
  --actions '[{"type":"type","selector":"#q","text":"rust"},
              {"type":"press","key":"Enter"},
              {"type":"wait","selector":".results"},
              {"type":"scrape"}]' \
  --format json | jq '.interaction.final_html | length'
```

### Markdown mode

Prints `interaction.final_html` directly — the raw final DOM, not converted
Markdown. Use JSON mode and feed `final_html` to a scrape step when you need
clean Markdown.

## Patterns

### Expand lazy content, then capture

```bash
kreuzcrawl interact https://example.com/feed \
  --actions '[{"type":"scroll","direction":"down"},
              {"type":"wait","milliseconds":800},
              {"type":"scroll","direction":"down"},
              {"type":"wait","milliseconds":800},
              {"type":"scrape"}]'
```

### Capture a full-page screenshot after login

```bash
kreuzcrawl interact https://app.example.com \
  --actions '[{"type":"type","selector":"#email","text":"me@example.com"},
              {"type":"type","selector":"#password","text":"..."},
              {"type":"click","selector":"button[type=submit]"},
              {"type":"wait","selector":".dashboard"},
              {"type":"screenshot","fullPage":true}]'
```

Never hardcode credentials — pass them from the environment or a secrets store.

### Point at an external Chrome

```bash
kreuzcrawl interact https://example.com \
  --browser-endpoint ws://browser.internal:9222/devtools/browser/<id> \
  --actions '[{"type":"click","selector":"#go"},{"type":"scrape"}]'
```

See the `headless-fallback` skill for CDP endpoints, wait strategies, and
persistent browser profiles set via `--config`.

## When to reach for scrape or crawl instead

If the page yields its content on a plain fetch (or via `--browser-mode
always`) with no clicking or typing, use `kreuzcrawl scrape` — see
`scraping-html-to-markdown`. Use `interact` only when ordered actions must run
before the content exists.
