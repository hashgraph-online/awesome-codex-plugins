# Performance

> Turn on intent preloading, let the router split route components, and keep cache freshness owned by exactly one layer.

Rules are labelled `official` when an opened page in the dated snapshot states them, and `hypercore-default` when this package chose the default. The order is typical impact, not a measured ranking.

## Measure first

| Goal | Command or tool |
|---|---|
| Production build | `vite build` through the Start plugin |
| Production server preview | `vite preview` or the project's production start command |
| Per-file transform timing | `vite --debug plugin-transform` |
| Bundle composition | a Rolldown-compatible visualizer on the production build |
| Navigation and route timing | TanStack Router devtools, plus the Performance panel on the production build |
| Field Core Web Vitals | `useReportWebVitals` or an equivalent RUM hook |
| Lab Core Web Vitals | `lhci autorun` against the production deployment |

Route loaders and preloads fire on the client, so a dev-server number tells you nothing about them. Measure the production build with the production server; a lab Lighthouse run against a dev server is not evidence.

## Rules

1. `official` — Set `defaultPreload: 'intent'` on the router for app-like navigation. The default is `false`, and `'intent'` fires on hover or touch start. Intent and viewport preloading begin after the 50 ms `defaultPreloadDelay`, while touch intent fires immediately.
2. `official` — Set `defaultPreloadStaleTime: 0` whenever TanStack Query owns cache freshness. Preloaded data is otherwise fresh for 30 s, which masks Query's own staleness rules.
3. `official` — Enable `autoCodeSplitting` for route components through the file-based routing plugin rather than hand-splitting loaders. It splits `component`, `errorComponent`, `pendingComponent`, and `notFoundComponent`, and deliberately keeps loaders, validators, `beforeLoad`, context, and links in the critical path, because splitting a loader would add a chunk fetch on top of an existing async boundary.
4. `official` — Prefetch in loaders with `queryClient.query({ ...options, staleTime: 'static' })`. `prefetchQuery`, `fetchQuery`, `ensureQueryData`, and their infinite variants are deprecated and will be removed in the next major version.
5. `official` — Give the server-side `QueryClient` a non-zero default `staleTime` so each prefetch does not have to pass its own.
6. `official` — Use `ssr: 'data-only'` for a route whose component needs browser APIs but whose data is server-fetchable, instead of dropping to `ssr: false`. `'data-only'` still runs `beforeLoad` and `loader` on the server.
7. `official` — Verify `<Scripts />` sits inside the root route's `<body>` before blaming streaming for a hydration failure. Without it the response still completes, but the page cannot hydrate.
8. `official` — Leave `defaultStaleTime` at `0` and set a per-route `staleTime` only for data that is measurably expensive and stable. Loader data is otherwise immediately stale for later reuse, with `gcTime` and `preloadGcTime` at 5 minutes and `staleReloadMode` defaulting to `'background'`.
9. `official` — Leave `defaultPendingMs` (1000) and `defaultPendingMinMs` (500) at their defaults unless a measured flash or delay says otherwise. These control when the pending UI appears and how long it stays, not data freshness.
10. `official` — Streaming SSR is automatic with `defaultStreamHandler` or `renderRouterToStream`; do not add manual streaming plumbing on top of it.
11. `official` — Never claim React Compiler improves initial load by itself. It targets update performance, memoizes components and hooks only, and does not share memoization across components. Deleting manual `useMemo`/`useCallback`/`memo` is allowed only where the compiler actually runs for that file.
12. `official` — Enable the compiler lint rules (`react-hooks` `recommended`/`recommended-latest`, or oxlint's `react` plugin equivalents) and read a report as "this component will not be optimized", never as a build failure. In oxlint, `rules-of-hooks` is in `pedantic`, not `correctness`.
13. `hypercore-default` — Gate on LCP ≤ 2.5 s, INP ≤ 200 ms, and CLS ≤ 0.1 at the 75th percentile, reported for mobile and desktop separately, with script and image size budgets in CI.

## Do not

- Leave `defaultPreload` at `false` and then blame the router for slow navigations.
- Let preloaded data and TanStack Query both decide freshness; one layer owns it.
- Hand-split loaders into their own chunk, or add a chunk fetch in front of an async boundary.
- Write `prefetchQuery`, `fetchQuery`, or `ensureQueryData` into new code.
- Use `ssr: false` where `'data-only'` would keep the server fetch.
- Add streaming wrappers around `defaultStreamHandler`, or chase a hydration failure before checking `<Scripts />`.
- Set a global `staleTime` above `0` to make a number look better; stale data is a correctness decision.
- Quote the 30 s preload freshness default as a performance win; it is a default that has to be reconciled with Query.

## Checklist

- [ ] Baseline recorded from a production build plus a navigation trace and a CWV measurement.
- [ ] `defaultPreload` is `'intent'` for app-like navigation, with the delay left at its default.
- [ ] `defaultPreloadStaleTime` is `0` where TanStack Query owns the cache.
- [ ] `autoCodeSplitting` is on and loaders stay in the critical route config.
- [ ] Loader prefetches use `queryClient.query(...)` with `staleTime: 'static'`, and the server `QueryClient` has a default `staleTime`.
- [ ] Selective SSR uses `'data-only'` where the component needs the browser but the data does not.
- [ ] `<Scripts />` is inside the root route's `<body>`.
- [ ] One lever changed per measurement, with the before and after numbers recorded.

## Sources

> Checked 2026-11-07. Facts and URLs below come from the performance research lane's TanStack findings; the lane opened each page on 2026-11-07 and its source ids are kept in parentheses.

| Claim | Source |
|---|---|
| `defaultPreload`, `'intent'` timing, `defaultPreloadDelay`, `defaultPreloadStaleTime` reconciliation with Query (L-22) | https://tanstack.com/router/latest/docs/guide/preloading.md |
| Router option defaults: `defaultPreload: false`, `defaultPreloadStaleTime` 30 s, `defaultPendingMs` 1000, `defaultPendingMinMs` 500, `staleReloadMode` (L-23) | https://tanstack.com/router/latest/docs/api/router/RouterOptionsType.md |
| `autoCodeSplitting` scope and why loaders stay critical (L-24) | https://tanstack.com/router/latest/docs/guide/code-splitting.md |
| Selective SSR `ssr: true \| false \| 'data-only'` and `defaultSsr` (L-25) | https://tanstack.com/start/latest/docs/framework/react/guide/selective-ssr.md |
| Automatic streaming SSR and the `<Scripts />` hydration requirement (L-26) | https://tanstack.com/router/latest/docs/guide/ssr.md |
| `queryClient.query({ staleTime: 'static' })` prefetch recipe and deprecated prefetch APIs (L-27) | https://tanstack.com/query/latest/docs/framework/react/guides/prefetching.md |
| Loader `staleTime` 0, `gcTime` and `preloadGcTime` 5 minutes, `staleReloadMode` (L-28) | https://tanstack.com/router/latest/docs/guide/data-loading.md |
| React Compiler 1.0 stability, update-performance scope, Meta figures (L-01, L-02) | https://react.dev/blog/2025/10/07/react-compiler-1, https://react.dev/learn/react-compiler/introduction |
| Compiler-first Babel ordering, lint-as-skip semantics, `panicThreshold` (L-03, L-04) | https://react.dev/learn/react-compiler/installation, https://react.dev/reference/react-compiler/configuration |
| Compiler lint rule names and presets (L-65) | https://raw.githubusercontent.com/facebook/react/main/packages/eslint-plugin-react-hooks/README.md |
| oxlint `react` plugin rules and category mapping (L-66) | https://oxc.rs/docs/guide/usage/linter/rules.html |
| Core Web Vitals thresholds at p75, per device class (L-67) | https://web.dev/articles/vitals |
| Lighthouse CI as the CI harness and its budget advice (L-68) | https://raw.githubusercontent.com/GoogleChrome/lighthouse-ci/main/README.md |
