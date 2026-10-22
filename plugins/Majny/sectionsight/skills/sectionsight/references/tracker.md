# The tracker: k.js

`assets/k.js` is about 44 KB unminified with its comments, about 16 KB
with `gzip -9`, and about 9.5 KB minified (esbuild `--minify`) and gzipped. It
has no dependencies. Two opt-in modules, JavaScript errors and Core Web
Vitals, are built into k.js as two marked sections. Together they add about
1.6 KB with `gzip -9` (0.9 KB minified and gzipped). See "Why the modules
are not separate files". It runs in every evergreen browser. Copy it
into the project unchanged, except for deliberate, documented edits. Minify
it in the site's build if size matters.

## What it measures

| Event (`e`) | When | Data (`d`) |
|---|---|---|
| *(none)* = view | a page view (and a client-side route, and a back/forward cache restore) | `of`: number of sections |
| `read` | a section has had 3 active seconds (once per view) | `s` section key, `n` its index, `of` |
| `time` | on every hide, page leave and route change | `sec` active seconds, `vis` visible seconds, `s` current section, `n` furthest section, `secs` [[section, seconds]…] (max 12), `dn` depth thresholds newly crossed (25/50/75/100), `hb` [from, to] visit-length bucket move; with `data-vitals="on"`, the view's first one also carries `cv` (see "Core Web Vitals") |
| `cta` | a link click | `k` kind, `url` (internal path or external host+path, never an e-mail or phone), `s`, `t` seconds since the view started, `tab` new tab 0/1 |
| `ui` | a click on `[data-kui]` (on a `<details>` marked with it: when it opens, not when it closes), a video starting to play (once) or ending | `k` name, `s` |
| `dead` | a click on a heading, image or `<strong>` that is not a link (max 5 per view) | `s`, `label` tag:text, or only the tag when the text may be personal or the element holds a field |
| `rage` | 3 clicks within 0.8 s on one spot, not on a control (max 3 per view) | `s`, `label` |
| `copy` | copying (max 5 per view) | `kind` email/text, `n` length; **never the text** |
| `print` | printing (once per view) | `s` |
| `goal` | `[data-kgoal]` clicked, or `k:goal` dispatched: once per goal per page load (on a client-routed site that is the visit; on a multi-page site, count conversions per visit from rows, or treat goals as per-page) | `k` name; on a page load that started a visit, also `gr` (the referrer host) and `gu` (the `utm_source`) at the top level, the same values the entry sent, so the collector can count the goal by the entry's source class |
| `form` | a `<form data-kform="contact">` submitted, once per form per view, whether or not the server accepts it | `k` name, `s`; **never a field or its value** |
| `consent` | only with `data-consent-counts="on"`: consent.js showed its banner by itself, or it was accepted, declined or withdrawn; **never carries ids**, in any mode, even after Accept | `k`: `shown`, `accept`, `decline` or `withdraw` |
| `err` | only with `data-errors="on"`: a JavaScript error of the site's own scripts (max 5 per view, each fingerprint once); **never carries ids**, in any mode, with or without consent | `m` the scrubbed message, `f` the file name, `l` line, `c` column, `s` the section current at the time (see "JavaScript errors") |
| `nf` | a view of the 404 page (marked with `data-k404`, see below), once per view, right after the view | `r` where the visitor came from: `internal` (a link on this site, or a client-side route: a broken link on this site), `external` (another site), `none` (typed, bookmarked, or no referrer) |

**Active** means the tab is visible and the visitor gave input (scroll,
pointer, key, touch, wheel, a playing video) in the last 45 s.

**Current section**: the last section to cross a line 40% down the viewport.
At the bottom of the page, it is the last section.

### Visits

- The first view of a page load that starts a visit carries the entry:
  `en: 1`, `r` the referrer **host**, `u` utm source/medium/campaign, `l`
  the language.
- A reload, a back/forward step or a load from a link on the same site
  continues the visit and is not counted again.
- In mode `consent`, the first report that carries ids repeats the entry
  with `en: 2`. Consent usually comes after the first view, so this is how
  the rows get it; the collector does not count it twice.

### The wire format

The tracker POSTs a JSON string to the endpoint. `sendBeacon` sends a string
as `text/plain;charset=UTF-8`, so there is no CORS preflight. It falls back
to `fetch` with `keepalive`.

```json
{ "p": "/pricing", "e": "read", "d": { "s": "plans", "n": 0, "of": 2 },
  "vi": "0123456789abcdef", "v": "fedcba9876543210", "ph": "<recording id>" }
```

- `vi` (visit) and `v` (view) are random 16-hex ids, sent only as `ids` allows.
- `ph` is the PostHog recording id: only with consent, and only when
  PostHog has really shipped a recording.
- Paths are `location.pathname` with any token-like segment replaced by
  `[id]`. Token-like means an e-mail, 9+ digits, 24+ alphanumerics, 12+
  hex, a JWT segment (`eyJ…`), or 10+ characters that mix letters and
  digits (`Xk9fA2bQ7z`, `K7XQ9ZP2LM4R`, `Xk9f-A2bQ-7zPl-M3nR`), 16+
  capitals, or mixed case with many capitals. It is not token-like when
  every part between `-` and `_` reads as a lowercase or capitalised word,
  a number, `v2`, one `h264`/`1080p`/`covid19` among words, or CamelCase
  made of words, acronyms and model numbers beside a real word
  (`best-tools-for-2026`, `iPhone15Pro`, `macOS-Sequoia-15`).
  **No query string is ever sent**; only the three utm values travel, in `u`.
- **What this rule cannot see.** A name slug (`/u/jane-doe`); codes under
  10 characters (`Xk9fA2bQ`, short invite codes); OTPs and ids of 8 digits
  or fewer (the digit rule starts at 9); letter-only codes with few
  capitals; lowercase-letter codes of any length; and some random codes
  that happen to read like words. Measured on random codes: about 6% of
  10-character lowercase-and-digit codes are missed, 2–4.5% of other
  10–12 character codes (base62, nanoid alphabet, capitals and digits),
  and under 1% from 16 characters on. Some names look like codes and become `[id]`
  (`CVE-2024-3094`, `SAP-S4HANA`). The protection for pages whose URL names
  a person or carries a credential is `data-skip` (and the same rule in
  the collector, consent.js and posthog-guard), not this rule.

## Configuration

Set these as `data-*` attributes on the script tag, or as `window.kConfig`
(camelCase) before the script runs when it is bundled.

| Attribute | Default | Meaning |
|---|---|---|
| `data-endpoint` | `/api/k` | The collector, same origin |
| `data-ids` | `consent` | `never` (model A), `consent` (B), `always` (C). Must match the collector |
| `data-consent-key` / `data-consent-value` | `analytics-consent` / `granted` | Where consent.js keeps the answer. `kConfig.consent` may be a function returning true or false instead |
| `data-consent-max-age-days` | `365` | An answer dated (`<key>-at`) older than this counts as none, as in consent.js |
| `data-skip` | — | **One** regex of the private paths (join them with `\|`; never a comma list, since a regex may contain `{1,3}`). No view there, and links to them are reported as `/[private]`. `kConfig.skip` may be an array. Paths are case-sensitive: write `/^\/account(\/|$)/i` (slashes and flags) for a case-insensitive rule, or redirect other spellings to the lowercase path. A rule that does not parse (or a comma list) turns k.js off, with a console warning |
| `data-hosts` | — | Comma-separated hostnames to measure on. Set it in production builds so staging and localhost stay out |
| `data-sections` | `main [data-k]`, else `main > header, main section` | A CSS selector for the sections |
| `data-spa` | `auto` | Follow `history.pushState`/`replaceState`/`popstate`. `off` when the app dispatches `k:route` itself |
| `data-idle-ms` / `data-read-seconds` | `45000` / `3` | Thresholds |
| `data-opt-out-key` / `data-opt-out-param` | `k-off` / `k` | The owner opt-out (`?k=off`) stores the flag; `?k=on` removes it |
| `data-visit-store` | `memory` | `session`: with consent, keep the visit id in sessionStorage until it has been idle for 30 minutes, so a visit spans full page loads (multi-page sites). Must be listed in the privacy text |
| `data-errors` | off | `on`: report the site's own JavaScript errors, scrubbed, as totals only (`err`). `kConfig.errors = true` when bundled |
| `data-vitals` | off | `on`: add Core Web Vitals buckets (LCP, CLS, INP, TTFB) to the view's first `time` report. `kConfig.vitals = true` when bundled |
| `data-consent-counts` | off | `on`: report consent.js's banner events (`consent`), totals only. The collector needs `consentCounts: true` too. The owner decides (`decisions.md`, 4e) |
| `data-strip-utm` | off | `on`: after reading them, remove `utm_*` parameters from the address bar (see "Campaign tags in the address bar") |
| `data-allow-automation` | — | `1` lets it run under `navigator.webdriver`. **Tests only**, never in production |

## JavaScript errors (`data-errors="on"`, off by default)

k.js listens to `error` and `unhandledrejection` and reports an error as an
`err` report, **totals only**: no visit or view id in any mode, before or
after consent, and the collector never makes a row of it. Every other rule
applies: no report on private paths, under GPC/DNT, after `?k=off`, or in
an automated browser.

- **The site's own scripts only.** An error whose file is on another origin
  (a CDN, an extension, an ad), "Script error." (what the browser says for a
  cross-origin script), and an error with no file (code run by `eval` or
  `new Function`, a browser console) are dropped. An unhandled rejection
  counts only when its reason is an `Error` whose stack names a script of
  the site; a rejected string or object has no location and is dropped.
- **The message, scrubbed in the browser** (`scrubError`, and again by the
  collector), in linear time (a test checks that every worst-case 4 KB
  message is scrubbed in under 20 ms):
  - decoded first: percent-escapes, including UTF-8 runs and twice-encoded ones
    (`%2540`), `%u0040`, `&#64;`, and the full-width and small at signs;
  - text in quotes (`"…"`, `'…'`, `` `…` ``, `„…“`, even a quote left open
    to the end) becomes empty quotes;
  - then word by word: `data:` URLs become `<data>`; URLs, `localhost`, IP
    addresses (`10.0.0.12/…`, `[::1]:3000/…`), `host.tld/…` without a
    scheme (including non-ASCII hosts) and any word with `?…=`, `#…=`, `;…=` or
    `&…=` become `<url>`; anything with an `@` (including `jane @ example.com`,
    `jane"@"example.com`, `jane(at)example.com`) `<email>`; any word with a `/` or `\`
    (`users/jane.json`, `./x`, `~/jane/x`, `C:\Users\jane\…`,
    `\\server\share\…`) `<path>`, a stack frame keeping its file name
    and position (`(<path>/app.js:0:0)`); token-like words `<id>` (the
    same `looksPersonal` rule as paths);
  - every digit becomes `0`; all on one line, at most 160 characters (the
    collector keeps 120). Chromium's and WebKit's "Uncaught " and Firefox's
    "uncaught exception: " are dropped, so the engines give the same
    fingerprint. `Cannot read properties of undefined (reading 'name')`
    arrives as `Cannot read properties of undefined (reading '')`.
- **What scrubbing cannot see:** a name or other personal text written into
  a message without quotes. `throw new Error('Payment failed for ' + name)`
  produces the message `Payment failed for Jane Doe`: the quotes are in
  the code, not in the message, so the name **is reported and stored as
  written**, in the counters' sample and wherever the sample is shown.
  Names with letters outside ASCII (`Zoë Müller`, even when they arrive
  percent-encoded), a name in a file name without an `@`
  (`jane-doe.js`), an e-mail spelled out in words, a code under 10
  characters, and a word with `/` that is not a path (`and/or` becomes
  `<path>`, which loses nothing personal) are the same: scrubbing is not
  a guarantee. Do not put personal data in error messages, and read the
  samples (`collector.md`) once after turning this on. Health alerts and
  the weekly digest show an error by fingerprint, file and line only, and its
  message only when the owner sets `showErrorText: true`.
- **The file**: its name only, never the path or query; token-like parts
  and build hashes (letters and digits mixed, 6 or more: Vite's
  `index-BXk3aF9q.js`, webpack's `chunk-9f8e7d6c.js`) become `*`
  (`index-*.js`, so a deploy does not make a new error); a decoded name
  with an e-mail in it (`chunk-jane.doe%40example.com.js`) is reported as
  `(hidden)`; an inline script, or anything that is not a `.js`, `.mjs`,
  `.cjs`, `.jsx`, `.ts` or `.tsx` file (the page itself, even after a
  client-side route), is `(inline)`. Line and column as the browser gives
  them.
- **The section**: the one current when the error happened (`s`), or none.
- **Limits:** at most 5 per page view, each fingerprint (message, file,
  line) once per view. An error thrown before k.js runs is not seen: load
  k.js early (without `defer`, or bundled first) if load-time errors matter.
- **Source maps** are not applied: line and column are those of the served
  (often minified) file. Map them yourself with the build's source map.

**Sending errors to an error tracker** (GlitchTip, Bugsink, Sentry, or
anything that speaks the Sentry protocol) is a separate decision, because
those tools keep a stack trace, the URL and often a user id per event:
**only after consent** (model B), and never from k.js. A recipe, not shipped
code:

1. Load the tool's own browser SDK only after Accept, the way posthog-guard
   loads PostHog (dynamic `import()` in the `onGranted` hook; never on
   private paths; stop it on withdrawal with its `close()`).
2. In its `beforeSend`, drop `request.url`'s query and `request.headers`,
   clean `exception.values[].value` with the same `scrubError`, strip
   `breadcrumbs` (they quote clicked text and URLs) and `user`, and set
   `sendDefaultPii: false`.
3. Point it at a same-origin tunnel (the SDK's `tunnel` option) built like
   `posthog-proxy.mjs`, with a header allowlist.
4. Name the tool as a processor in the privacy text, with what it receives.

k.js's own `err` totals stay as they are either way.

## Core Web Vitals (`data-vitals="on"`, off by default)

k.js observes, with buffered `PerformanceObserver`s from the start:

- **LCP** (Largest Contentful Paint): the last candidate before the page
  was first hidden; its element's section.
- **CLS** (Cumulative Layout Shift): the largest session window of shifts
  without recent input (gaps under 1 s, windows up to 5 s), as web-vitals
  computes it.
- **INP** (Interaction to Next Paint): the **longest** interaction of the
  view (Event Timing entries with an `interactionId`); its target's
  section. (Google's INP is the 98th percentile, which equals the longest
  for views with fewer than 50 interactions.)
- **TTFB**: the navigation's `responseStart`.

They ride once per page view on the view's first `time` report (the first
hide, page leave or route), as **bucket indices**, never raw values, plus
the two sections:

```json
"cv": { "lcp": 2, "lcps": "hero", "cls": 0, "inp": 3, "inps": "pricing", "ttfb": 1 }
```

| Metric | Bucket lower edges | Good / poor (web.dev) |
|---|---|---|
| `lcp` | 0, 1000, 1800, 2500, 3000, 4000, 6000 ms | ≤ 2.5 s / > 4 s |
| `cls` | 0, 0.05, 0.1, 0.15, 0.25 | ≤ 0.1 / > 0.25 |
| `inp` | 0, 100, 200, 350, 500, 1000 ms | ≤ 200 ms / > 500 ms |
| `ttfb` | 0, 200, 500, 800, 1800 ms | ≤ 800 ms / > 1.8 s |

- **Sections, never selectors.** The element is mapped to the section key
  that contains it (`data-k`, else `s<n>`), or `""` when it is outside
  every section (a banner, a header outside `<main>`). No CSS selector,
  text, URL or image address is ever sent.
- **Only the page load's first view.** A client-side route starts a new
  view but not a new load: LCP and TTFB belong to the first view, and the
  load's vitals are sent once, with it. If that first page was private,
  nothing is sent.
- **Back/forward cache:** a restored page counts as a new view;
  it gets no LCP and no TTFB (nothing was loaded), and its CLS and INP start
  again from zero.
- **Prerendered pages** (`activationStart > 0`, or prerendering when k.js
  starts) report no vitals at all.
- **Hidden before paint:** an LCP candidate painted after the page was first
  hidden is ignored (a tab opened in the background).
- **Ids:** none of the vitals ever reach a row. The time report itself
  carries ids as the mode allows (with consent in model B), but the
  collector takes `cv` into the totals only.

**Engine support** (MDN browser-compat-data, checked 2026-10-09; k.js
sends whatever the browser supports and leaves the rest out):

| | Chromium (Chrome, Edge) | Firefox | Safari |
|---|---|---|---|
| LCP (`LargestContentfulPaint`) | 77 | 122 | 26.2 |
| INP (Event Timing with `interactionId`) | 96 | 144 | 26.2 |
| CLS (`LayoutShift`) | 77 | no | no |
| TTFB (Navigation Timing) | yes | yes | yes |

So CLS counts Chromium visitors only, and LCP and INP leave out older
Firefox and Safari: the histograms describe the browsers that can measure,
not everyone. Sources: the
[LargestContentfulPaint](https://developer.mozilla.org/en-US/docs/Web/API/LargestContentfulPaint),
[PerformanceEventTiming](https://developer.mozilla.org/en-US/docs/Web/API/PerformanceEventTiming) and
[LayoutShift](https://developer.mozilla.org/en-US/docs/Web/API/LayoutShift) pages
(their compatibility data, `mdn/browser-compat-data`).

**Reading them**: `collector.md`, "Reading the totals" (p75 per page and
device, and which section is slow). **With Umami as the dashboard:** Umami
3.1 and later can collect web vitals itself, with `data-performance="true"`
on its own tracker script, shown in its Performance tab
([docs](https://docs.umami.is/docs/guides/monitor-web-vitals), checked
2026-10-09). That needs Umami's browser script, which this setup does not
load: `umamiForwarder` runs on the server and forwards no vitals. So with
the forwarder, k.js's vitals are the only ones; if the owner runs Umami's
own script anyway, pick one source per page, and list it in the privacy text.

## Goals by source

A goal on a page load that started a visit resends that entry's referrer
host and `utm_source` (`gr`, `gu`): nothing the first view did not already
send. The collector turns them into one coarse class (`google`, `bing`,
`search`, `ai`, `social`, `newsletter`, `direct`, `other`) and counts
`goalsrc.<goal>.<class>`; the referrer itself is never stored with the
goal. A goal on a page load that continued a visit (a full load on a
multi-page site) carries neither and counts in `goal.<name>` only.

## Consent counts (`data-consent-counts="on"`, off by default)

consent.js dispatches `consent:ui` (`shown` when the banner appears by
itself, once per page load; `accept`; `decline`; `withdraw` when a Decline
withdraws an earlier Accept) and keeps the last few in
`window.__consentUi` for a k.js that starts later. k.js sends each as a
`consent` report with no visit or view id, whatever the mode and the
consent. Under Global Privacy Control or Do Not Track k.js does not run and
consent.js shows no banner, so nothing is sent. Not on private paths. Up
to 4 such reports wait for the page's view to be sent; they are dropped if
the page is private. A withdrawal reloads the page; its report goes out first, by
`sendBeacon`.

## Campaign tags in the address bar (`data-strip-utm="on"`, off by default)

On the page load's first view, after reading `utm_source`, `utm_medium`
and `utm_campaign`, k.js removes every `utm_*` parameter (any case) from
the address bar, so a link the visitor copies, bookmarks or shares does
not pass the tag on. The other parameters stay exactly as written, in
order, and the hash stays. Private paths are never touched (k.js does not
start there).

- **Most sites and routers:** k.js calls the browser's own
  `history.replaceState`, saved before its history patch, with the entry's
  state object (`history.state`) passed back unchanged, and dispatches
  nothing: no `k:route`, no `popstate`, no new view.
- **Next.js App Router** keeps its router tree in `history.state` (`__NA`).
  A URL changed behind its back is written back by the next
  `router.refresh()`, server action or revalidation, and a page rendered
  before hydration that shows search params gets a React hydration error
  (#418). So when k.js sees the App Router (`self.__next_f`, `next.appDir`
  or `__NA` in the state), it waits until the router owns the history
  entry, then calls the current (Next-patched) `history.replaceState(null,
  '', url)`, with the URL recomputed at that moment: Next merges its state
  back and updates `useSearchParams` (components see the `utm_*` values
  disappear). Tested with Next.js 16.4.0 in production and dev builds, with
  k.js loaded by `next/script` `afterInteractive` and `beforeInteractive`,
  a plain `<script defer>` in the head, and `instrumentation-client.ts`: no
  hydration error, `useSearchParams` follows, and `router.refresh()` does
  not bring the tags back. A component that needs the campaign tags itself
  must read them before then (or leave the option off).
- **Next.js Pages Router** keeps the query in its router (`router.query`,
  `asPath`) and in `history.state.as`, and a later shallow
  `router.replace` or a Back step would write the tags back. So when k.js
  sees the Pages Router (the `__NEXT_DATA__` script), it waits until
  `next.router` is ready and calls `next.router.replace(url, url, {
  shallow: true, scroll: false })`, with `url` its own `asPath` (so a
  `basePath` stays out) minus the tags, recomputed at that moment. Tested
  with Next.js 16.4.0, dev and production: the address bar,
  `history.state.as`, `router.query` and `asPath` lose the tags, and a
  shallow replace and Back keep them out. `basePath` and i18n routing were
  not tested.
- **Other routers** that keep their own copy of the query may write it
  back on their next navigation: check the address bar after a
  client-side navigation on the real site.

## Why the modules are not separate files

Both modules are in k.js, off unless their attribute is set:

- **Errors must listen from k.js's first moment.** A second file fetched
  only when enabled starts later and misses exactly the load-time errors
  that matter most.
- **Both use k.js's private state** (the current view, its sections, the
  report path that leaves ids out). A separate file would need that state
  exposed on `window`, a public API any page script could call, plus a
  second request and a second `script-src` entry.
- **The cost is small:** about 0.9 KB minified and gzipped (1.6 KB with
  `gzip -9` on the commented source). When neither is on, the extra code is
  parsed but never runs. A site that minds the bytes can delete the two
  marked sections ("JavaScript errors", "Core Web Vitals") from its copy.

## Marking up the page

- **Names**: `data-k`, `data-kcta`, `data-kgoal` and `k:goal` take
  `^[a-z0-9][a-z0-9_-]{0,23}$` (section keys may use hyphens but not underscores).
  `data-kui` takes `^[a-z0-9][a-z0-9:_-]{0,31}$`. Anything else is dropped
  silently. Names that look personal (the digits of a phone number, a
  token) are dropped too, by k.js and again by the collector: a section key
  falls back to its index (`s2`), a click or goal is not reported.
- **Sections**: `<section data-k="pricing">` with a stable, lowercase key
  (max 24 characters). Without `data-k`, a hero `<header>` inside `<main>` is
  `intro`, and a section's key is its `id`, else its `<h2>` turned into a slug.
  Headings change and ids drift, so `data-k` is better.
- **Link kinds**: `mailto:` is `email` and `tel:`/`sms:` is `phone` (never
  the address). Files are `download`, the same host is `nav`, other hosts
  are `outbound`. `data-kcta="signup"` on the link, or any ancestor, names
  the kind instead.
- **Goals**: `data-kgoal="signup"` on an element. For a form, dispatch
  `k:goal` after the server confirms, not on submit.
- **Forms**: `data-kform="contact"` on the `<form>` counts submit attempts
  (`form.contact` in the totals). Give the goal sent on the server's
  confirmation the same name, and health rule (c2) alerts when submits
  keep coming but none is confirmed: a form whose backend is broken.
- **The 404 page**: put `data-k404` on its `<html>` or `<body>` (or set
  `kConfig.notFound = true` before k.js runs). Its view then also sends an
  `nf` report: the path that was asked for, cleaned like every path
  (token-like segments become `[id]`, **never the query**), and only
  `internal`, `external` or `none` for the referrer, never the referrer
  itself. Every rule still applies: no report on `data-skip` paths, under
  GPC/DNT or after `?k=off`, and ids only as `data-ids` allows. The
  collector keeps per-day counts by path (`collector.md`). Put the marker
  on the 404 template only, never on a page that is merely empty. A
  client-rendered 404 (an SPA's catch-all route) must set the marker
  before k.js sees the route, or set it and dispatch `k:route` after, and
  remove it when the router leaves the page. Use the 404 *template*, not a
  catch-all that answers 200: search engines treat such pages as "soft
  404s".
- **Controls**: `data-kui="faq-shipping"` on accordions, tabs, currency
  toggles and the like.
- **Copy buttons**: `data-kui="copy-snippet"`. A button that uses
  `navigator.clipboard.writeText` fires no `copy` event.
- **Check the rendered HTML, not the JSX.** Component wrappers often drop
  `data-*` props they do not forward.
- **Identity in the page.** Never put a visitor's name or e-mail in a
  heading, `<strong>` or image `alt` inside `<main>`. Dead-click labels come
  from those elements; the collector cuts labels that look personal, but
  names do not always look personal.

## Installing it

**Plain HTML, or any server-rendered site.** Put `k.js` in the public folder:

```html
<script src="/k.js" defer data-ids="consent" data-hosts="example.com,www.example.com"
        data-skip="^/(account|reset)(/|$)"></script>
```

**No `<main>`?** k.js looks for sections in `main`. Without one, set
`data-sections` to the page's own section selector, or the read and
time-per-section reports stay empty.

**Astro**: the same tag in the layout's `<head>`, with `is:inline` so Astro
keeps the attributes and does not bundle it:
`<script is:inline src="/k.js" defer data-ids="never" data-hosts="example.com"></script>`.

**Next.js (App Router)**: `public/k.js`, and in `app/layout.tsx`:

```tsx
import Script from 'next/script';
// inside <body>:
<Script src="/k.js" strategy="afterInteractive" data-ids="consent"
        data-hosts="example.com,www.example.com" data-skip="^/account(/|$)" />
```

Or bundle it so it starts before hydration and sees short visits too. In
`instrumentation-client.ts`:

```ts
(window as any).kConfig = { ids: 'consent', hosts: 'example.com', skip: '^/account(/|$)' };
import('./lib/k.js');
```

Use `next/link` for every internal link on measured pages. A plain `<a>`
does a full load, which resets the tracker's state and, in the default
`memory` mode, a new visit id. With `html { scroll-behavior: smooth }`, add
`data-scroll-behavior="smooth"` to `<html>`. Otherwise Next 16 animates the
scroll after a route, and the new page's depth starts at the old offset.

Client-side routes are followed automatically. For a router that changes
the URL long before the DOM, set `data-spa="off"` and dispatch `k:route`
after the new page renders, e.g. in a component with
`useEffect(() => dispatchEvent(new CustomEvent('k:route', { detail: pathname })), [pathname])`.

**React, Vue or Svelte SPAs (Vite etc.)**: the script tag in `index.html`.
The history patch covers React Router, Vue Router and SvelteKit. A view's
`of` (sections on the page) is counted when the route starts: on the first
load, before the app has mounted, it is 0, and after a client-side route it
may be the previous page's. The `read` and `time` reports look the sections
up again and carry the right `of`; use theirs. Nothing else needs changing.

**Content Security Policy**: for k.js itself, `connect-src 'self'` and
`script-src 'self'` are enough. An inline `window.kConfig` (or consent
config) script needs a nonce or hash in `script-src`, or move it into an
external file. consent.js also injects a `<style>`: see
`references/consent.md` for `style-src`.

## Page API

```js
dispatchEvent(new CustomEvent('k:route', { detail: location.pathname })); // a route k.js could not see
dispatchEvent(new CustomEvent('k:goal', { detail: 'signup' }));            // a confirmed conversion
dispatchEvent(new Event('k:consent'));                                     // consent changed (consent.js does this)
dispatchEvent(new CustomEvent('k:replay', { detail: () => recordingIdOrNull })); // posthog-guard.mjs does this
window.__k?.deleteMyData(); // the visitor's own rows deleted (consent.js's "Delete my visit data" calls it)
window.__k?.canDelete;      // false with data-ids="never" or data-delete="off": consent.js then offers no button
```

`window.__k.deleteMyData()` sends one request, `{"del":"<visit id>"}`, to the
collector (model B; in model C `{"del":"today"}`), forgets the visit id and
returns whether there was one to delete. It never returns the id, so no
other script gets it from this API. That is a convenience, not a wall:
any script on the page can already read k.js's own reports (they carry the
id) by wrapping `sendBeacon`, and with `data-visit-store="session"` the id
sits in sessionStorage. Any script can also call it, which only ever
deletes this visitor's own rows. See `collector.md`, "Deletion".
`data-delete="off"` (or `kConfig.delete = 'off'`) turns it off, for a store
that cannot delete (Analytics Engine) or an owner who does not offer it.

posthog-guard also leaves the getter on `window.__kReplay`, so it does not
matter which of the two starts first. The path in a `k:route` detail is
the one reported (for example, the router's own path), while measurement
(depth, sections) always follows the URL in the address bar.

## When it does not run

It does not run in these cases:

- Global Privacy Control or Do Not Track.
- `navigator.webdriver` (automation).
- A host outside `data-hosts`.
- The owner opt-out (`?k=off`).
- A prerendered page until it is shown.
- A path in `data-skip`.

Lighthouse and PageSpeed Insights set `navigator.webdriver`, so their runs
never see k.js work: a score from them says nothing about its cost. To
measure it, run Lighthouse on a staging copy with `data-allow-automation="1"`
(measured: main-thread work +25 ms on simulated mobile, no blocking time,
CLS 0, scores unchanged). Serve a minified k.js in production (about 9.5 KB
gzipped instead of 16 KB): any minifier works, e.g.
`npx esbuild k.js --minify --outfile=k.min.js`.

Every report goes to the same origin; there is no third-party request.

## Known limits

- **Visit length on multi-page sites.** On a static multi-page site in mode
  `consent` without consent, the visit-length histogram covers the page load
  that started the visit (usually the landing page). Without ids, page loads
  cannot be joined.
- **Sections that never cross the line.** Sections shorter than the gap
  between the 40% line and their neighbours may never become current. Keep
  sections at least a screen tall, or accept it.
- **Long tabs.** A tab left open reports its time when it is finally hidden,
  possibly hours later. The visit builder in `visits.mjs` joins such late
  reports to their visit.
