# Current Official Vite + TanStack Router Docs Snapshot — 2026-11-04

> Official documentation facts for drift-sensitive Vite 8 + TanStack Router architecture decisions.

last_verified_at: 2026-11-04
checked_at: 2026-11-04
patch_checked_at: 2026-11-07 (stable_versions `vite` and `@tanstack/react-query`, and the React Compiler native-path status below)
library_ids: `/websites/vite_dev`, `/tanstack/router`
stable_versions: vite 8.3.6, @vitejs/plugin-react 6.2.1, @tanstack/react-router 1.170.46, @tanstack/router-plugin 1.168.48, @tanstack/react-query 5.107.1, @tanstack/router-core 1.171.39, zod 4.6.7
source_priority: official Vite docs, the Vite 8 release posts, the `vitejs/vite` and `vitejs/vite-plugin-react` changelogs, official TanStack Router and TanStack Query docs, and the npm registry.

## Current Official Vite Facts

- Vite 8 uses Rolldown and Oxc based tools instead of esbuild and Rollup. Rolldown is the single bundler for dev dependency optimization and production builds; Oxc handles JavaScript transforms and minification.
- The `esbuild` option is deprecated and converted to the `oxc` option internally. `build.rollupOptions` is a deprecated alias of `build.rolldownOptions`, `worker.rollupOptions` is a deprecated alias of `worker.rolldownOptions`, and `build.commonjsOptions` is a no-op. `optimizeDeps.esbuildOptions` is deprecated in favor of `optimizeDeps.rolldownOptions`.
- The object form of `build.rollupOptions.output.manualChunks` is removed and the function form is deprecated; Rolldown's `output.codeSplitting` replaces both.
- Vite 8 requires Node.js 20.19+ or 22.12+ and is distributed as ESM only.
- `build.target` defaults to the special value `'baseline-widely-available'`, which resolves to `['chrome111', 'edge111', 'firefox114', 'safari16.4', 'ios16.4']` for this major release. Projects that must support older browsers have to set `build.target` explicitly.
- Vite exposes only env variables prefixed with `VITE_` to client-side code through `import.meta.env`; unprefixed values such as `DB_PASSWORD` are not exposed to browser code.
- `import.meta.env` values are strings unless application code parses them.
- Custom Vite env typings can augment `ImportMetaEnv` in a `vite-env.d.ts` file; `vite/client` types provide shims for asset imports, `import.meta.env`, and HMR APIs.
- `loadEnv(mode, process.cwd(), '')` can be used inside `vite.config.*` when config itself needs env values. Loading all env values for config does not mean all values are safe for client code.
- `defineConfig` is the standard Vite config helper. `resolve.alias`, plugins, server options, and build options should remain explicit when architecture depends on them. `resolve.tsconfigPaths` exists (default `false`) but the docs present `resolve.alias` as the cheaper, explicit option.
- `server.forwardConsole` defaults to `true` when an AI coding agent is detected through `@vercel/detect-agent` and `false` otherwise; it forwards browser runtime errors and `console.*` output to the dev server terminal.
- `public/` assets are served as static public assets; application source organization such as `src/lib` or `src/services` is a project convention, not official Vite requirement.

## Current Official @vitejs/plugin-react Facts

- `@vitejs/plugin-react` 6.x declares `vite: ^8.0.0` as a peer dependency, so it cannot run on Vite 7 or earlier.
- Vite 8 handles the React Refresh transform through Oxc, so plugin-react 6 no longer depends on Babel; the plugin's Babel options were removed in 6.0.0.
- Projects that still need Babel transform use `@rolldown/plugin-babel` next to `react()` instead of plugin options.
- React Compiler support is available as `react({ compiler: true })` with `oxc-transform-react` installed, or through `reactCompilerPreset()` with `@rolldown/plugin-babel`.
- The native `compiler` path is **experimental**: the plugin README says so, and as of `@vitejs/plugin-react` 6.2.0 it peers on `oxc-transform-react >=0.152.0 <0.157.0`. Prefer `reactCompilerPreset()` for production until that label changes. (Re-checked 2026-11-07.)
- `compiler.reportDiagnostics` replaces the deprecated `compiler.logDiagnostics` (6.1.2); `refreshInclude` and `refreshExclude` skip Fast Refresh for files that never run in the browser. The plugin's README on `main` still shows `logDiagnostics`, so the changelog is the authority.

## Current Official TanStack Router Facts

- For Vite, the TanStack Router plugin is configured from `@tanstack/router-plugin/vite` and should be placed before `@vitejs/plugin-react` / `react()`.
- Official Vite examples use `tanstackRouter({ target: 'react', autoCodeSplitting: true })` followed by `react()`.
- `@tanstack/router-plugin` 1.168.48 declares a peer dependency of `@tanstack/react-router: ^1.170.46`, so the plugin and the router are upgraded as a pair.
- The plugin enables file-based routing, route tree generation, and route-level code splitting.
- `autoCodeSplitting` defaults to `false`; the next major release (v2) is documented to default it to `true`.
- Generated-route-tree formatting options are documented: `quoteStyle` defaults to `single`, `semicolons` defaults to `false`, and `addExtensions` defaults to `false`.
- `routeTree.gen.ts` is generated from source route files; normal architecture work should fix source routes/config rather than hand-edit generated output, and the file path should be excluded from linters and formatters.
- React router setup imports `routeTree` from `./routeTree.gen`, creates a router with `createRouter({ routeTree, ... })`, and passes it to `RouterProvider`.
- File routes use exported route objects such as `export const Route = createFileRoute(...)({ ... })`.
- Search params should be validated with `validateSearch`. With Zod v4 the schema is passed directly to `validateSearch`, and `.catch()` keeps type inference; with Zod v3, use the `@tanstack/zod-adapter` helpers such as `zodValidator` and `fallback`. The adapter's current peer dependency is `zod: ^3.23.8`, so it does not cover Zod 4 projects.
- `search.strict` (router option, default `false`) removes search params that `validateSearch` does not return.
- Route loaders keep their own cache: default `staleTime` is `0`, preload data is fresh for 30 seconds, `gcTime` and `preloadGcTime` default to 5 minutes, `staleReloadMode` defaults to `'background'`, and `shouldReload` can suppress a reload. When TanStack Query owns the cache, the docs recommend setting `defaultPreloadStaleTime: 0` on the router.
- The loader form documented for TanStack Query is `queryClient.query({ ...queryOptions, staleTime: 'static' })` paired with `useSuspenseQuery`, not `ensureQueryData`.
- `<ScrollRestoration />` still works but is deprecated; the `scrollRestoration` router option remains current.
- `basepath` (router option, default `/`) mounts the router under a subpath.
- From `@tanstack/router-core` 1.171.16 (shipped; latest stable is 1.171.39), `RouterState` no longer includes `loadedAt`, `isTransitioning`, `statusCode`, or `redirect`, `RouteMatch.status` no longer includes `'redirected'`, and `RouterCore` no longer exposes `getMatch()`, `updateMatch()`, or `cancelMatch()`.
- `@tanstack/react-router-ssr-query` 1.167.3 wires SSR streaming through `setupRouterSsrQueryIntegration({ router, queryClient })` and supports `wrapQueryClient: false` to skip its provider wrapper.
- Route loaders are not a private backend boundary. Treat loader code and route modules as client-reachable, and keep secrets, DB clients, filesystem access, and privileged SDKs behind a real backend/API boundary.

## Current Official TanStack Query Facts

- `fetchQuery`, `prefetchQuery`, `ensureQueryData`, and their infinite-query variants are deprecated and will be removed in the next major version.
- `queryClient.query(options)` replaces `fetchQuery`; `queryClient.query({ ...options, staleTime: 'static' })` replaces `ensureQueryData`; `queryClient.infiniteQuery(...)` replaces the infinite variants.
- `query()` disables retries by default (`retry: false`) and rejects with the fetch error; observer-only options such as `enabled`, `refetchOn*`, `throwOnError`, `suspense`, and `placeholderData` are not part of its options.
- `prefetchQuery` migration note: use `queryClient.query(options)` and swallow errors with `.catch(noop)`.
- `staleTime` accepts `number | 'static'`; `'static'` means the data never becomes stale.

## Hypercore Interpretation

- `src/lib/<domain>/` and `src/services/<domain-or-provider>/` are Hypercore/repo-local conventions for ownership and runtime boundaries; they are not official Vite or TanStack Router requirements.
- Do not add new direct leaf files such as `src/lib/foo.ts` or `src/services/foo.ts` in touched shared roots unless an explicit project exception is recorded.
- Prefer Services for public client-side API wrappers in Vite SPAs. Do not introduce TanStack Start server functions (`createServerFn`, `useServerFn`, Start middleware APIs) in this skill.

## Sources

> Checked 2026-11-04; the `vite` and `@tanstack/react-query` version rows and the React Compiler native-path status were re-checked 2026-11-07.

- `https://vite.dev/guide/migration`
- `https://vite.dev/blog/announcing-vite8`
- `https://vite.dev/config/build-options`
- `https://vite.dev/config/shared-options`
- `https://vite.dev/config/server-options`
- `https://vite.dev/guide/env-and-mode`
- `https://raw.githubusercontent.com/vitejs/vite-plugin-react/main/packages/plugin-react/CHANGELOG.md`
- `https://registry.npmjs.org/@vitejs/plugin-react/latest`
- `https://registry.npmjs.org/@tanstack/react-router/latest`
- `https://registry.npmjs.org/@tanstack/router-plugin/latest`
- `https://registry.npmjs.org/@tanstack/react-query/latest`
- `https://registry.npmjs.org/@tanstack/zod-adapter/latest`
- `https://registry.npmjs.org/@tanstack/react-router-ssr-query/latest`
- `https://tanstack.com/router/latest/docs/installation/with-vite`
- `https://tanstack.com/router/latest/docs/api/file-based-routing`
- `https://tanstack.com/router/latest/docs/guide/search-params`
- `https://tanstack.com/router/latest/docs/guide/data-loading`
- `https://tanstack.com/router/latest/docs/guide/external-data-loading`
- `https://tanstack.com/router/latest/docs/guide/scroll-restoration`
- `https://tanstack.com/router/latest/docs/api/router/RouterOptionsType`
- `https://raw.githubusercontent.com/TanStack/router/main/packages/router-core/CHANGELOG.md`
- `https://tanstack.com/query/latest/docs/framework/react/reference/QueryClient`