# Performance

> Measure the production build, move static-output work out of the client bundle, and keep cache lifetimes prerender-eligible.

Rules here are labelled `official` when an opened page in the dated snapshot states them, and `hypercore-default` when this package chose the default. Rules are ordered by typical impact, which is this package's ordering, not a measured ranking.

## Measure first

Performance work runs on a production build. Dev-server timings and dev-mode renders are not evidence.

| Goal | Command or tool |
|---|---|
| Production build | `next build` (Turbopack is the default bundler) |
| Type check | `tsc --noEmit`; Turbopack does not type-check |
| Bundle composition | `next analyze`, or `next analyze --output` writing `.next/diagnostics/analyze` |
| Build-time analyzer data | `next build --analyze` |
| Bundle diff between builds | `next analyze export --snapshot <name>` (JSONL, added in 16.4) |
| Field Core Web Vitals | `useReportWebVitals` in the app |
| Lab Core Web Vitals | `lhci autorun` against the production deployment |

`next build` no longer prints JS bundle sizes (removed in 16.0.0), and `@next/bundle-analyzer` remains valid only for Webpack builds. Treat a runtime-config LCP measurement and a lab Lighthouse score as different numbers; record which one moved.

## Rules

1. `official` — Move work that only produces static markup (syntax highlighting, markdown parsing, chart rendering) into a Server Component. The docs' own example switches client-side Prism to server-side Shiki and ships zero client JS for it. `serverExternalPackages` handles packages that should stay unbundled on the server.
2. `official` — Enable `cacheComponents: true` together with `partialPrefetching: true` for new work. Setting `partialPrefetching` without `cacheComponents` fails config validation, and leaving it unset logs a warning.
3. `official` — Remove `experimental.ppr`, the `experimental_ppr` segment export, and every `runtime` segment export (including `runtime = 'nodejs'`) once Cache Components is on. PPR is the default behaviour now, and Cache Components requires the Node.js runtime.
4. `official` — Pair every `use cache` scope with an explicit `cacheLife`, and check the profile against the prerender thresholds before assuming the output is prerendered: `revalidate: 0` or `expire` under 5 minutes becomes a runtime dynamic hole, `stale` under 30 seconds is excluded from prerenders, and `stale` from 30 seconds to 5 minutes is prerendered but excluded from the App Shell. Of the presets only `seconds` trips this.
5. `official` — Keep `use cache` scopes async, and pass `cookies()` and `headers()` values in as arguments instead of reading them inside the cached scope. Outer-scope values a cached function reads become part of the cache key.
6. `official` — Wrap every uncached read or request-time API access in `<Suspense>`, or give the segment a `loading.tsx`, so the shell can prerender. `loading.js` wraps `page.js`, `not-found.js`, and nested layouts, but not `layout.js`, `template.js`, or `error.js` in the same segment; moving a fetch from `layout.js` into `page.js` is what preserves instant navigation.
7. `official` — Set `sizes` on every responsive `next/image`. Without it the browser assumes `100vw` and downloads unnecessarily large files. Default `quality` is 75 and `formats` defaults to `['image/webp']`; add AVIF deliberately.
8. `official` — For the LCP image use `loading="eager"` or `fetchPriority="high"`. `priority` is deprecated in favour of `preload` since Next.js 16, and `preload` is not combined with `loading` or `fetchPriority`.
9. `official` — Serve every font through `next/font` with `display: 'swap'`; it self-hosts and removes the external request. Variable fonts take a weight range such as `'100 900'`.
10. `official` — Keep `next/script` at the default `afterInteractive`, reserve `beforeInteractive` for critical site-wide scripts in the root layout, and never use the `worker` strategy in the App Router.
11. `official` — Use `updateTag` inside Server Actions for read-your-own-writes and `revalidateTag` everywhere else. `updateTag` outside a Server Action is invalid. A stale-data complaint is a cache-freshness defect, not a bundle defect.
12. `official` — Enable `reactCompiler` (stable top-level option since 16.0.0) with `compilationMode: 'annotation'` and `"use memo"` on hot components first. Its stated target is update performance — skipping cascading re-renders and expensive calculations — not initial load. Next.js applies it only to files with JSX or React Hooks, so the build cost stays localized. See the React Compiler rules below.
13. `official` — Do not fetch a Route Handler from a Server Component; it adds a server round trip the component could have made itself.
14. `hypercore-default` — Add packages to `experimental.optimizePackageImports` only after the analyzer shows them as large. The option is still experimental and its default list already covers `lucide-react`, `date-fns`, `lodash-es`, `rxjs`, `@mui/material`, `recharts`, `@headlessui/react`, `react-icons/*`, `@tabler/icons-react`, and `effect`.
15. `hypercore-default` — Ship field Core Web Vitals with `useReportWebVitals` instead of trusting lab-only Lighthouse. Gate on LCP ≤ 2.5 s, INP ≤ 200 ms, and CLS ≤ 0.1 at the 75th percentile, reported for mobile and desktop separately.

### React Compiler

The compiler applies to any React stack here, so these rules hold for this stack too.

- `official` — React Compiler 1.x is stable and production-ready; do not gate adoption behind a beta caveat.
- `official` — Never claim the compiler improves initial load by itself. It memoizes components and hooks, not every function, and memoization is not shared across components.
- `official` — Enable the compiler lint rules (`react-hooks` `recommended`/`recommended-latest`, or the `react` plugin equivalents in oxlint) and read a report as "this component will not be optimized", never as a build failure. In oxlint, `rules-of-hooks` sits in `pedantic`, not `correctness`, so check the selected category.
- `official` — Deleting manual `useMemo`, `useCallback`, or `memo` is allowed only where the compiler actually runs for that file — here, only with `reactCompiler` enabled.
- `official` — Set `panicThreshold: 'none'` in the compiler configuration for production so a component the compiler cannot handle is skipped instead of failing the build.

## Do not

- Read bundle sizes from `next build` output; that display was removed in 16.0.0.
- Add `--webpack` without a Webpack-only feature as the reason.
- Enable `partialPrefetching` alone, or assume a `use cache` scope with a `seconds` profile is prerendered.
- Combine `preload` with `loading="eager"` or `fetchPriority="high"`, or keep the deprecated `priority` prop.
- Drop `sizes` from a responsive image, or serve fonts through an external stylesheet.
- Blame streaming for a hydration failure before checking `<Scripts />` and the Suspense placement.
- Tune `experimental.optimizePackageImports` before the analyzer names an offending package.
- Quote the Meta figures (up to 12% faster loads, 2.5× faster interactions) as a guarantee; they are a vendor report from one deployment.

## Checklist

- [ ] Baseline recorded from a production build with an analyzer export and a CWV measurement.
- [ ] Static-output libraries run on the server, and the client bundle no longer contains them.
- [ ] `cacheComponents` and `partialPrefetching` are both on, with no `ppr` or `runtime` exports left.
- [ ] Every `use cache` scope names a `cacheLife`, and the profile clears the prerender thresholds.
- [ ] Uncached reads sit behind `<Suspense>` or `loading.tsx` in a segment that actually wraps them.
- [ ] The LCP image declares `sizes` and uses `loading`/`fetchPriority` rather than `preload` or `priority`.
- [ ] Fonts come from `next/font`, and scripts stay `afterInteractive` unless root-level critical.
- [ ] One lever changed per measurement, with the before and after numbers recorded on the production build.

## Sources

> Checked 2026-11-07. Facts and URLs below come from the performance research lane's Next.js and React Compiler findings; the lane opened each page on 2026-11-07 and its source ids are kept in parentheses.

| Claim | Source |
|---|---|
| Turbopack is the default bundler and does not type-check (L-06) | https://nextjs.org/docs/app/api-reference/turbopack |
| `next analyze`, `--output`, `next build --analyze`, and the removed bundle-size output (L-07) | https://nextjs.org/docs/app/api-reference/cli/next |
| `cacheComponents` and `partialPrefetching` pairing, PPR removal, runtime export rejection (L-08) | https://nextjs.org/docs/app/api-reference/config/next-config-js/cacheComponents |
| Suspense boundaries, blocking-route insight, prerendering of synchronous work (L-09) | https://nextjs.org/docs/app/getting-started/caching |
| `use cache` async requirement, cache key composition, runtime API rules (L-10) | https://nextjs.org/docs/app/api-reference/directives/use-cache |
| `cacheLife` presets and prerender-eligibility thresholds (L-11) | https://nextjs.org/docs/app/api-reference/functions/cacheLife |
| `updateTag` versus `revalidateTag` (L-13) | https://nextjs.org/docs/app/api-reference/functions/updateTag |
| `priority` deprecation, `sizes`, `quality`, `formats`, image size defaults (L-14) | https://nextjs.org/docs/app/api-reference/components/image |
| `next/font` self-hosting, `display: 'swap'`, weight ranges (L-15) | https://nextjs.org/docs/app/api-reference/components/font |
| `next/script` strategies and the App Router limitation of `worker` (L-16) | https://nextjs.org/docs/app/api-reference/components/script |
| Static-output work moved to Server Components, `serverExternalPackages` (L-17) | https://nextjs.org/docs/app/guides/package-bundling |
| `useReportWebVitals`, parallel fetching, no Route Handler fetch from a Server Component (L-18) | https://nextjs.org/docs/app/guides/production-checklist |
| `optimizePackageImports` experimental status and default list (L-19) | https://nextjs.org/docs/app/api-reference/config/next-config-js/optimizePackageImports |
| `loading.js` coverage and the layout-to-page fetch move (L-20) | https://nextjs.org/docs/app/api-reference/file-conventions/loading |
| `staleTimes` defaults (L-21) | https://nextjs.org/docs/app/api-reference/config/next-config-js/staleTimes |
| `reactCompiler` stable top-level option, SWC pass, annotation mode (L-05) | https://nextjs.org/docs/app/api-reference/config/next-config-js/reactCompiler |
| React Compiler 1.0 stability, Meta figures, update-performance scope (L-01, L-02) | https://react.dev/blog/2025/10/07/react-compiler-1, https://react.dev/learn/react-compiler/introduction |
| Compiler-first Babel ordering, `panicThreshold`, lint-as-skip semantics (L-03, L-04) | https://react.dev/learn/react-compiler/installation, https://react.dev/reference/react-compiler/configuration |
| Compiler lint rule names and presets (L-65) | https://raw.githubusercontent.com/facebook/react/main/packages/eslint-plugin-react-hooks/README.md |
| oxlint `react` plugin rule set and category mapping (L-66) | https://oxc.rs/docs/guide/usage/linter/rules.html |
| Core Web Vitals thresholds at p75, per device class (L-67) | https://web.dev/articles/vitals |
| Lighthouse CI as the CI harness (L-68) | https://raw.githubusercontent.com/GoogleChrome/lighthouse-ci/main/README.md |
