---
name: headless-fallback
description: >-
  Use when a static fetch returns nothing useful and the page needs a real
  browser. Covers `--browser-mode auto|always|never`, external CDP via
  `--browser-endpoint`, symptoms of JS-only pages and WAF blocks, and the
  performance cost.
---

# Headless fallback

Some pages are unscrapable without a real browser — SPA shells, infinite
scroll, Cloudflare interstitials, JS-rendered article bodies. Crawlberg
ships with an optional headless-Chrome backend driven by chromiumoxide.

## Modes

```text
--browser-mode auto    # default — try static first, fall back to browser on JS/WAF
--browser-mode always  # skip static, go straight to browser
--browser-mode never   # static only, fail closed
```

### `auto` (default)

The engine fetches statically, then inspects the response. It launches
headless Chrome and re-fetches when it sees:

- WAF responses from one of 8 detected vendors (Cloudflare, Akamai, AWS WAF,
  Imperva, DataDome, PerimeterX, Sucuri, F5).
- SPA shells: `<noscript>` warnings, near-empty `<body>` with heavy JS.
- Heuristic JS-render-required signals.

This is the right default. The browser only spins up when needed.

### `always`

Skip the static probe entirely. Use when:

- The user already told you the page needs JS.
- You are scraping a site you know is React/Vue/Svelte SPA.
- You need `<script>`-emitted state that never lands in static HTML.

```bash
crawlberg scrape https://spa.example.com --browser-mode always --format markdown
```

### `never`

Static only — the browser path is disabled. Use when:

- You are in a hot loop where a stray Chrome launch would blow the budget.
- You are running in a sandbox without a Chrome binary.
- The user explicitly wants only static fetches.

In `never` mode, JS-only pages return empty/stub content. Inspect
`markdown.content` and `markdown.warnings` before treating the result as
final.

## Symptoms that point to headless

In `--browser-mode never` or when you suspect the auto detector missed a
signal:

- `markdown.content` is short, nav-only, or just a loading message.
- `status_code` is 200 but `metadata.headings` is empty on a page that
  clearly has headings.
- `markdown.warnings` mentions JS-render-required or WAF detection.
- 403/406/503 with WAF response headers (`server: cloudflare`,
  `cf-mitigated`, `x-amz-cf-id`, `set-cookie: __cf_bm=…`).

Re-run with `--browser-mode always`. If that succeeds, leave it set for
that host.

## External CDP endpoint

Point at an already-running Chrome (Browserless, Steel, your own) instead
of launching locally:

```bash
crawlberg scrape https://example.com \
  --browser-mode always \
  --browser-endpoint ws://browser.internal:9222/devtools/browser/<id> \
  --format markdown
```

The endpoint must be a WebSocket URL — `ws://` or `wss://`. The CLI
rejects anything else with a clear error.

Use external CDP when:

- You are running in containers or CI without a local Chrome.
- You want a shared, warm browser pool across many crawl jobs.
- You need browser-side residential proxies or stealth configuration the
  local Chrome cannot provide.

## Performance cost

Headless Chrome is expensive relative to a static fetch:

- Cold start: 1-3 seconds the first time it launches.
- Per-page overhead: 500 ms-2 s for `NetworkIdle` wait, plus the page's own
  JS load time.
- Memory: each tab takes 100-300 MB; long crawls should bound
  `--concurrent`.

Mitigations:

- Stay in `--browser-mode auto` — the engine only pays the cost when it
  needs to.
- Use `--browser-endpoint` to share one warm browser across jobs.
- Drop `--concurrent` when you know the crawl will route through Chrome.

## Wait strategies

Pass via `--config` JSON when you need control:

```bash
crawlberg scrape https://example.com --browser-mode always \
  --config '{"browser":{"wait_strategy":{"type":"Selector","selector":".article-body"}}}'
```

Supported strategies:

- `NetworkIdle` (default) — wait until the network goes quiet.
- `Selector` — wait until a CSS selector resolves.
- `Fixed` — wait a fixed duration.

`extra_wait` adds milliseconds on top of the wait strategy if the page
keeps loading content after the primary signal.

## Persistent profiles

```bash
crawlberg scrape https://app.example.com --browser-mode always \
  --config '{"browser_profile":"prod","save_browser_profile":true}'
```

Profile names are path-traversal-validated. Use them to keep cookies,
localStorage, and login state across runs without re-authenticating.
