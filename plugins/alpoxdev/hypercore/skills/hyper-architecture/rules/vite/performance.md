# Performance

> Measure the production build, import leaf modules instead of barrels, and let Rolldown split chunks from evidence rather than guesswork.

Rules are labelled `official` when an opened page in the dated snapshot states them, and `hypercore-default` when this package chose the default. The order is typical impact, not a measured ranking.

## Measure first

| Goal | Command or tool |
|---|---|
| Production build | `vite build` |
| Inspect the built app | `vite preview` |
| CPU profile of the build | `vite --profile`, which writes a `.cpuprofile` |
| Per-file transform timing | `vite --debug plugin-transform` |
| Bundle composition | a visualizer on the production build |
| Field Core Web Vitals | `useReportWebVitals` or an equivalent RUM hook in the app |
| Lab Core Web Vitals | `lhci autorun` against the production deployment |

`rollup-plugin-visualizer` 7.1.2 declares peers for both `rollup` 2–4 and `rolldown` 1.x, so it can run on Vite 8, but that comes from registry metadata only — no doc page was opened for it, so confirm it against the installed version before relying on the output.

Dev-server numbers and dev-mode renders are not performance evidence. A build-time regression and a runtime regression are different measurements; record which one moved.

## Rules

1. `official` — Avoid barrel files and import the individual modules directly. The official performance guide names this as the main documented build-time cost: a barrel makes every consumer load the whole re-export graph.
2. `official` — Keep explicit file extensions in relative imports, and set `moduleResolution: "bundler"` plus `allowImportingTsExtensions` in tsconfig. The default `resolve.extensions` list is `['.mjs', '.js', '.mts', '.ts', '.jsx', '.tsx', '.json']`, so an extensionless import can cost up to six filesystem checks.
3. `official` — Configure chunking with `build.rolldownOptions.output.codeSplitting.groups`, using `name`, `test`, `priority`, and `minSize`. The object form of `output.manualChunks` is removed and the function form is deprecated; `codeSplitting: true` (the default) already splits automatically, and `false` inlines dynamic imports.
4. `official` — Write `build.rolldownOptions`, not the deprecated `build.rollupOptions` alias, and `optimizeDeps.rolldownOptions` instead of `optimizeDeps.esbuildOptions`. `worker.rollupOptions` maps to `worker.rolldownOptions`, and `build.commonjsOptions` is a no-op.
5. `official` — Set `build.target` explicitly when the project must support browsers below the default `'baseline-widely-available'` set: `chrome111`, `edge111`, `firefox114`, `safari16.4`, `ios16.4`.
6. `official` — Add `server.warmup.clientFiles` for the few slowest dev-server files, identified with `vite --debug plugin-transform`. This is a dev-loop lever; it does not change the production bundle.
7. `official` — Keep `optimizeDeps.holdUntilCrawlEnd` at its default while the dependency scanner is still discovering imports; turn it off only when the scanner already finds everything, because it holds first results until static imports are crawled.
8. `official` — Handle `vite:preloadError` and serve the HTML entry with `Cache-Control: no-cache`. After a redeploy, a stale client importing a deleted chunk throws, and that failure is routinely misread as a performance bug.
9. `official` — Do not present Full Bundle Mode as available. It is experimental; the release post's preliminary figures (about 3× faster dev startup, 40% faster full reloads, 10× fewer network requests) are not a supported default.
10. `official` — Do not set `build.minify: 'esbuild'`; it is deprecated. CSS minification already defaults to `lightningcss`.
11. `official` — For React Compiler on Vite, use `react()` with `babel({ presets: [reactCompilerPreset()] })` from `@rolldown/plugin-babel`, because `@vitejs/plugin-react` 6.0.0 removed the inline `babel` option and dropped Babel as a dependency. Put the compiler first in the Babel pipeline.
12. `official` — Treat `react({ compiler: true })` as experimental. It runs through `oxc-transform-react`, and the plugin marks native React Compiler support experimental. `compiler.reportDiagnostics` is the current option; `compiler.logDiagnostics` is deprecated since 6.1.2.
13. `official` — Never claim React Compiler improves initial load by itself. It targets update performance, memoizes components and hooks only, and does not share memoization across components. Deleting manual `useMemo`/`useCallback`/`memo` is allowed only where the compiler actually runs for that file.
14. `official` — Enable the compiler lint rules (`react-hooks` `recommended`/`recommended-latest`, or oxlint's `react` plugin equivalents) and read a report as "this component will not be optimized". In oxlint, `rules-of-hooks` is in `pedantic`, not `correctness`.
15. `hypercore-default` — Measure with `vite --profile` and a visualizer before adding any `codeSplitting.groups`. Groups are a fix for a measured split problem, not a starting configuration.
16. `hypercore-default` — Gate on LCP ≤ 2.5 s, INP ≤ 200 ms, and CLS ≤ 0.1 at the 75th percentile, reported for mobile and desktop separately, and keep script and image size budgets alongside them in CI.

## Do not

- Open DevTools with "Disable Cache" on while profiling the dev server; it adds a large startup and reload cost that has nothing to do with the code.
- Put expensive work in the `config`, `configResolved`, or `buildStart` plugin hooks; all three are awaited at startup.
- Add a heavy `resolveId`, `load`, or `transform` hook without measuring the per-file cost first.
- Write object-form `manualChunks`, or mix `rollupOptions` into new config.
- Turn off `holdUntilCrawlEnd` before confirming the scanner finds every entry.
- Quote the Rolldown "10–30× faster than Rollup" figure as a project outcome; it is a vendor benchmark from the release post.
- Assume `vite-bundle-visualizer` is validated for Vite 8; only `rollup-plugin-visualizer` carries the `rolldown` peer, and even that is registry metadata.
- Raise `build.target`-era browser support by accident; a lowered target adds transform and polyfill weight that shows up as bundle growth.

## Checklist

- [ ] Baseline recorded from `vite build` output plus a visualizer run and a CWV measurement.
- [ ] No new barrel import in touched code, and relative imports carry explicit extensions.
- [ ] Chunk groups, if any, are justified by a before/after measurement on the production build.
- [ ] Build config uses `rolldownOptions`, `oxc`, and `codeSplitting`; no `manualChunks` object and no `esbuild` minifier.
- [ ] `build.target` matches the browsers the project actually supports.
- [ ] `vite:preloadError` is handled and the HTML entry is served with `Cache-Control: no-cache`.
- [ ] The React Compiler path is named correctly, with the native path marked experimental where it is used.
- [ ] One lever changed per measurement, with the before and after numbers recorded.

## Sources

> Checked 2026-11-07. Facts and URLs below come from the performance research lane's Vite and React Compiler findings; the lane opened each page on 2026-11-07 and its source ids are kept in parentheses.

| Claim | Source |
|---|---|
| `build.target` default, `baseline-widely-available` resolution, deprecated `esbuild` minifier, `lightningcss` CSS default (L-29) | https://vite.dev/config/build-options |
| `rolldownOptions` aliases, removed object-form `manualChunks`, `codeSplitting`, `vite:preloadError`, HTML cache header (L-30) | https://raw.githubusercontent.com/vitejs/vite/main/docs/guide/build.md |
| Barrel files, `resolve.extensions`, explicit extensions, plugin hooks, `server.warmup.clientFiles`, `vite --debug plugin-transform`, `vite --profile` (L-31) | https://raw.githubusercontent.com/vitejs/vite/main/docs/guide/performance.md |
| Vite 8 Rolldown/Oxc single bundler and the vendor build benchmark (L-32) | https://vite.dev/blog/announcing-vite8 |
| `codeSplitting.groups` option shape and global size fallbacks (L-33) | https://rolldown.rs/reference/OutputOptions.codeSplitting.md |
| `optimizeDeps.holdUntilCrawlEnd` and the deprecated `optimizeDeps.disabled` (L-34) | https://raw.githubusercontent.com/vitejs/vite/main/docs/config/dep-optimization-options.md |
| plugin-react 6 Babel removal, native compiler path marked experimental, `reportDiagnostics` replacing `logDiagnostics` (L-35) | https://raw.githubusercontent.com/vitejs/vite-plugin-react/main/packages/plugin-react/CHANGELOG.md |
| React Compiler 1.0 stability, update-performance scope, Meta figures (L-01, L-02) | https://react.dev/blog/2025/10/07/react-compiler-1, https://react.dev/learn/react-compiler/introduction |
| Compiler-first Babel ordering, lint-as-skip semantics, `panicThreshold` (L-03, L-04) | https://react.dev/learn/react-compiler/installation, https://react.dev/reference/react-compiler/configuration |
| Compiler lint rule names and presets (L-65) | https://raw.githubusercontent.com/facebook/react/main/packages/eslint-plugin-react-hooks/README.md |
| oxlint `react` plugin rules and category mapping (L-66) | https://oxc.rs/docs/guide/usage/linter/rules.html |
| Core Web Vitals thresholds at p75, per device class (L-67) | https://web.dev/articles/vitals |
| Lighthouse CI as the CI harness and its budget advice (L-68) | https://raw.githubusercontent.com/GoogleChrome/lighthouse-ci/main/README.md |
| Registry peers for `rollup-plugin-visualizer` and `vite-bundle-visualizer` (L-70, registry metadata only) | https://registry.npmjs.org/{next,vite,expo,expo-router,react-native,hono,oxlint,babel-plugin-react-compiler,eslint-plugin-react-hooks,@vitejs/plugin-react,@tanstack/react-router,@tanstack/react-query,@tanstack/react-start,expo-image}/latest |
