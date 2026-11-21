# Performance

> Measure the production build first, then move work out of the client bundle, cut image and font weight, and only then touch build parallelism.

Rules here are labelled `official` when an opened page in the dated snapshot states them, and `hypercore-default` when this package chose the default. The rule order is typical impact, which is this package's ordering, not a measured ranking.

## 1. Measure first

Performance work runs on a production build. Dev-server timings and dev-mode renders are not evidence.

| Goal | Command or tool |
|---|---|
| Production build | `astro build` |
| Build phase timing | `astro build --timings` (7.4) |
| Type check before measuring | `astro check` |
| Production preview | `astro preview` |
| Lab Core Web Vitals | `lhci autorun` against `astro preview`, or Lighthouse against the preview URL |
| Field Core Web Vitals | A real-user measurement on the deployed site |
| Bundle composition | The client assets under `dist/_astro/`, plus a bundle visualizer of your choice |

`official` — `astro build --timings` reports build phase timing. Record which number moved: build time, transferred bytes, LCP, INP, or CLS.

## 2. Rules

1. `official` — The default is zero client JavaScript: framework components render to HTML unless a `client:*` directive is present. An island directive is the single biggest lever on transferred bytes, so justify each one.
2. `official` — Use `<Image />` and `<Picture />` from `astro:assets` for content images. `alt` is mandatory, `width`/`height` are inferred for local images, and the output carries `loading="lazy"`, `decoding="async"`, and explicit dimensions that prevent CLS.
3. `official` — Mark the LCP image with `priority`, which adds `loading="eager" decoding="sync" fetchpriority="high"` (5.10+). Do not put `priority` on every image.
4. `official` — Use `layout: 'constrained' | 'full-width' | 'fixed' | 'none'` plus `image.responsiveStyles` and `image.breakpoints` for responsive sets (5.10+). `public/` images are never optimized or made responsive.
5. `official` — Remote image optimization requires `image.domains` or `image.remotePatterns`, and redirect targets must match too.
6. `official` — Self-host fonts through the Fonts API: declare `fonts: [{ provider: fontProviders.local() | fontsource() | google(), name, cssVariable, weights, styles, subsets, fallbacks, formats }]` and emit `<Font cssVariable="..." preload />` from `astro:assets`. Fonts are downloaded, self-hosted, copied to `_astro/fonts`, and served with long-lived caching.
7. `official` — Preload only above-the-fold fonts. A preload on every font competes with the LCP resource.
8. `official` — Turn on `prefetch: true` and add `data-astro-prefetch` to links that lead to the next likely page. Strategies are `tap`, `hover`, `viewport`, and `load`; `prefetchAll: true` prefetches every internal link and `data-astro-prefetch="false"` opts out. Data-saver and slow connections downgrade to `tap`.
9. `official` — Use `<ClientRouter />` from `astro:transitions` only for the features it adds. Browser-native cross-document view transitions need no Astro JavaScript, so a site that only wants page transitions should not ship the router.
10. `official` — `build.inlineStylesheets` accepts `'always' | 'auto' | 'never'` and defaults to `'auto'`, which inlines stylesheets under Vite's 4 kB `assetsInlineLimit`. Measure before forcing `'always'`; it trades requests for HTML weight.
11. `official` — Keep `build.concurrency` at its default of 1. The docs say "In most cases, you should not change the default value of 1", and the option may break in a minor release.
12. `official` — `experimental.parallelPrerender` (7.4) uses multiple CPU cores and is ignored by adapters that prerender themselves (`@astrojs/cloudflare`). Reach for it only when `--timings` shows prerendering dominates the build.
13. `official` — `experimental.incrementalBuild` (7.2) reuses output for unchanged `getStaticPaths` pages that return a `cacheKey`. It helps repeat builds, not first builds.
14. `official` — Route caching needs a provider: `cache: { provider: memoryCache({ max }) }`, then `Astro.cache.set({ maxAge, swr, tags })` or declarative `routeRules`. `memoryCache()` is an LRU for single-instance deployments and adds `X-Astro-Cache: HIT|MISS|STALE`. Using `Astro.cache` without a provider throws "Cache is not enabled."
15. `official` — Astro `<script>` tags are bundled, TypeScript-compiled, deduplicated per page, and inlined when small. `is:inline` opts out, and `define:vars` implies `is:inline`, so a `define:vars` script is not bundled and runs per instance.
16. `hypercore-default` — Record a baseline before the first change: `astro build --timings` plus one Lighthouse run on `astro preview`, mobile and desktop separately. Change one lever per measurement.
17. `hypercore-default` — Gate on LCP ≤ 2.5 s, INP ≤ 200 ms, and CLS ≤ 0.1 at the 75th percentile. Report mobile and desktop as separate numbers.
18. `hypercore-default` — Prefer `client:visible` or `client:idle` over `client:load` for anything below the fold, and `client:only` only for components that cannot render on the server. A directive change is a performance change and needs a before/after number.
19. `hypercore-default` — Prefer a server island over converting a page to on-demand rendering when one fragment is personalized. On-demand rendering adds request-time work the static page did not have.
20. `hypercore-default` — Pair a live collection with route caching. A live collection without caching turns every visitor into an upstream request.

## 3. Island hydration choice

| Symptom | Lever |
|---|---|
| Large transferred JS on a static page | Remove or narrow a `client:*` directive |
| Interaction feels slow on first paint | Keep `client:load` only for the widget that needs it |
| Long main-thread task after load | Move below-the-fold islands to `client:idle` or `client:visible` |
| Framework runtime shipped for static markup | Convert the component to `.astro` |
| Second framework integration with one small widget | Check whether `.astro` covers it before keeping both |

## 4. Do not

- Read performance from a dev server.
- Claim a gain without a before and after number on a production build.
- Put `priority` on every image, or use `public/` images for content that needs optimization.
- Preload every font weight.
- Ship `<ClientRouter />` for a site that only wants native cross-document transitions.
- Change `build.concurrency`, `experimental.parallelPrerender`, and `experimental.incrementalBuild` in one pass.
- Enable `experimental.*` flags without a measured reason and a note that the flag may change in a minor release.
- Treat `memoryCache()` as a multi-instance cache; it is an in-process LRU.

## Checklist

- [ ] Baseline recorded from `astro build --timings` plus one Lighthouse run on `astro preview`.
- [ ] Client bundle inspected for framework JavaScript that no interaction needs.
- [ ] Every `client:*` directive has a reason and the narrowest viable value.
- [ ] Content images use `astro:assets` with dimensions, and exactly one LCP image carries `priority`.
- [ ] Responsive images use `layout` and `image.responsiveStyles`; no `public/` image is expected to be optimized.
- [ ] Fonts come from the Fonts API, and only above-the-fold fonts are preloaded.
- [ ] Prefetch strategy matches the navigation pattern, and view transitions use the router only if its extra features are needed.
- [ ] `build.concurrency` is still 1 unless a measurement says otherwise.
- [ ] Route caching has a provider, and live collections are cached.
- [ ] One lever changed per measurement, with before and after numbers recorded.

## Sources

> Checked 2026-11-07. Facts and URLs come from the Astro research lane, which opened each page on 2026-11-07; lane source ids are kept in parentheses.

| Claim | Source |
|---|---|
| Zero client JS by default; framework components render to HTML without a directive (L-19) | https://docs.astro.build/en/guides/framework-components/ |
| `astro build --timings` (L-28, L-50) | https://docs.astro.build/en/reference/cli-reference/ |
| `<Image />`/`<Picture />`, mandatory `alt`, inferred dimensions, lazy/async defaults (L-20, L-21) | https://docs.astro.build/en/reference/modules/astro-assets/ |
| `priority` attributes for the LCP image (L-21) | https://docs.astro.build/en/reference/modules/astro-assets/ |
| `layout` values, `image.responsiveStyles`, `image.breakpoints`, `public/` exclusion (L-20, L-17) | https://docs.astro.build/en/guides/images/ |
| `image.domains` and `image.remotePatterns` for remote optimization (L-17) | https://docs.astro.build/en/reference/configuration-reference/ |
| Fonts API providers, `<Font cssVariable preload />`, `_astro/fonts` caching (L-24, L-42) | https://docs.astro.build/en/guides/fonts/ |
| Prefetch strategies, `prefetchAll`, opt-out, data-saver downgrade (L-22) | https://docs.astro.build/en/guides/prefetch/ |
| `<ClientRouter />`, `transition:persist`, native cross-document transitions needing no Astro JS (L-23) | https://docs.astro.build/en/guides/view-transitions/ |
| `build.inlineStylesheets` values and the 4 kB `assetsInlineLimit` default (L-17) | https://docs.astro.build/en/reference/configuration-reference/ |
| `build.concurrency` default and the caution against changing it (L-17) | https://docs.astro.build/en/reference/configuration-reference/ |
| `experimental.parallelPrerender` and the Cloudflare adapter exception (L-34, L-50) | https://docs.astro.build/en/reference/experimental-flags/parallel-prerender/ |
| `experimental.incrementalBuild` and `cacheKey` (L-35, L-50) | https://docs.astro.build/en/reference/experimental-flags/incremental-build/ |
| Route caching provider, `routeRules`, `memoryCache()` LRU, `X-Astro-Cache` (L-30, L-31) | https://docs.astro.build/en/guides/caching/ |
| Bundled scripts, `is:inline`, `define:vars` implying inline (L-29, L-58) | https://docs.astro.build/en/guides/client-side-scripts/ |
| Core Web Vitals thresholds at p75, reported per device class | https://web.dev/articles/vitals |
| Lighthouse CI as the lab harness | https://raw.githubusercontent.com/GoogleChrome/lighthouse-ci/main/README.md |
