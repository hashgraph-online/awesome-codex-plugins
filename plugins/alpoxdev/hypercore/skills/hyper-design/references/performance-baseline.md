# Performance and Page Baseline

Read when a page is built for production, when a finding concerns layout shift, slow first paint, or third-party scripts, or when the user asks for a web-quality review. The craft floor (`rules/craft-floor.md` §8) holds the mechanisms every page meets; this file holds the field thresholds and an optional baseline checklist.

## 1. Core Web Vitals

Field data at the 75th percentile of real visits:

| Metric | Good | Needs improvement | Poor |
|---|---|---|---|
| LCP (largest contentful paint) | at most 2.5 s | 2.5-4 s | over 4 s |
| INP (interaction to next paint) | at most 200 ms | 200-500 ms | over 500 ms |
| CLS (cumulative layout shift) | at most 0.1 | 0.1-0.25 | over 0.25 |

- The agent writing a page has no field data. From source alone, name likely causes but never claim a metric passes or fails.
- Measure in order: field data at p75 when it exists (say whether it is page or origin level), then a lab trace with stated conditions, then only the failing metric's causes, then a lab re-run after the fix. A single lab value is never compared with field p75.
- Any number not measured in this run is written `not measured`.

## 2. Mechanisms That Show in Code

| Problem | Fix |
|---|---|
| Media without dimensions shifts the layout (`quality.media-unsized`) | `width` and `height` or `aspect-ratio` on every `img`, `video`, and `iframe`; reserved space for embeds and late banners; overlay a banner instead of inserting it above content |
| The hero image is lazy, a CSS background, or injected by script | An `img` in the HTML with `fetchpriority="high"`, never `loading="lazy"`; lazy-load below the fold only; preload only when a trace shows late discovery |
| Synchronous analytics, chat, or tag-manager script in `<head>` | `defer`, `async`, or load on interaction |
| Late web fonts swap the layout | `font-display: swap` with a metric-matched fallback; ship only the weights used |
| Images in the wrong size or format | Serve AVIF or WebP at the displayed size with `srcset` |

## 3. Optional Page Baseline

Run for a production-ready page or a web-quality review. None of it shows in a screenshot.

- Document: `<!doctype html>` first; `<meta charset="utf-8">` first in `<head>`; viewport `width=device-width, initial-scale=1` with zoom allowed; no duplicate `id`.
- Runtime: no `document.write`, synchronous XHR, or `unload` handler; scroll and touch listeners are `{ passive: true }` unless they call `preventDefault()`; no console errors.
- Security: HTTPS for every resource and no mixed `http://` content; `rel="noopener noreferrer"` on external links that open a new tab; no secret or API key in client code; `textContent` or a sanitizer instead of `innerHTML` or `eval` with untrusted input; subresource integrity on third-party CDN scripts and styles; permission prompts only after a user action.

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| LCP, INP, and CLS thresholds at the 75th percentile | <https://web.dev/articles/vitals> |
| The measurement order, "never claim from source", and the baseline checklist | <https://github.com/miqdadbadjuber/anti-slop> (commit `9504989`, `antislop-ui/references/CORE-WEB-VITALS.md` and `WEB-BASELINE.md`, adapted there from <https://github.com/addyosmani/web-quality-skills>; MIT, Copyright 2026 Miqdad Badjuber and Copyright 2026 Addy Osmani), rewritten for this package |
| `fetchpriority` on the LCP image and not lazy-loading it | <https://web.dev/articles/optimize-lcp> |

### Evidence grade

The thresholds are Google's published definitions and change rarely; browser-specific features (speculation rules, priority hints support) change faster and are left out on purpose.
