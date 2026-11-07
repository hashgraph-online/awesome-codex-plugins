# Platform Setup

> Vite + TanStack Router project setup rules/vite that architecture reviews should enforce

---

## Vite 8 Toolchain

Vite 8 (current stable 8.3.6) ships Rolldown and Oxc instead of Rollup and esbuild. It requires Node 20.19+ or 22.12+ and is distributed as ESM only.

- Build config uses the new names: `build.rolldownOptions` instead of `build.rollupOptions` (now a deprecated alias), `oxc` instead of `esbuild` (deprecated and auto-converted), `optimizeDeps.rolldownOptions` instead of `optimizeDeps.esbuildOptions`, and Rolldown `output.codeSplitting` where the object form of `output.manualChunks` was removed and the function form is deprecated. `build.commonjsOptions` is a no-op.
- `build.target` defaults to `'baseline-widely-available'`, which resolves to `['chrome111', 'edge111', 'firefox114', 'safari16.4', 'ios16.4']` for this major. A repo that must support older browsers has to set `build.target` explicitly.
- `resolve.tsconfigPaths` exists (default `false`) but the docs present `resolve.alias` as the cheaper explicit option; keep aliases declared in both Vite and TypeScript config.
- `server.forwardConsole` defaults to on when an AI coding agent is detected through `@vercel/detect-agent`; it forwards browser runtime errors and `console.*` output to the dev server terminal.
- Route-level splitting still comes from the router plugin's `autoCodeSplitting`; any manual chunk rule goes through Rolldown `output.codeSplitting`, not `manualChunks`.
- Vite 8.1's experimental bundled dev mode (`experimental.bundledDev: true`) stays off in this skill's guidance; it is opt-in and still carries third-party plugin compatibility risk.

---

## Vite Plugin Rules

For API drift, check `references/official/vite/current-docs-2026-11-04.md` before changing plugin order, env handling, generated route tree paths, or router setup.


```ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { tanstackRouter } from '@tanstack/router-plugin/vite'

export default defineConfig({
  plugins: [
    // tanstackRouter() MUST come before react()
    tanstackRouter({
      target: 'react',
      autoCodeSplitting: true,
    }),
    react(),
  ],
})
```

- Keep `tanstackRouter()` explicit and pass `target: 'react'`
- Enable `autoCodeSplitting: true` so the plugin code-splits route components. The plugin default is `false` and the next major release is documented to default it to `true`, so keep the option explicit in either case.
- Register `tanstackRouter()` before `react()` (incorrect ordering fails silently)
- Do not add duplicate router plugins
- `@vitejs/plugin-react` 6 declares `vite: ^8.0.0` and no longer ships Babel: React Refresh runs through Oxc. A Vite 7 repo stays on plugin-react 5, and a project that still needs Babel transforms adds `@rolldown/plugin-babel` next to `react()` instead of plugin options.
- React Compiler support is `react({ compiler: true })` with `oxc-transform-react` installed, or `reactCompilerPreset()` with `@rolldown/plugin-babel`. Use `compiler.reportDiagnostics` (`logDiagnostics` is deprecated) and `refreshInclude` / `refreshExclude` to skip Fast Refresh for files that never run in the browser.
- `@tanstack/router-plugin` 1.168.x peers on `@tanstack/react-router ^1.170.x`: upgrade the plugin and the router in the same change
- File-convention options that must stay consistent with hypercore folders: `routeFileIgnorePrefix` defaults to `'-'` (this is what excludes `-components/` and `-hooks/` from the route tree); customize `routeToken` / `indexToken` only if the repo declares them in `tsr.config.json`

---

## Generated Files

- `routeTree.gen.ts` is generated output
- Do not hand-edit it
- If routing changes look wrong, fix source routes or router config, then regenerate

If the repo declares `tsr.config.json`, keep the canonical keys explicit so the plugin and CLI agree:

```json
{
  "routesDirectory": "./src/routes",
  "generatedRouteTree": "./src/routeTree.gen.ts"
}
```

Only add `routeToken`, `indexToken`, `routeFilePrefix`, or `routeFileIgnorePrefix` when the repo really customizes them — otherwise rely on the documented defaults.

Generated-tree formatting options are `quoteStyle` (default `single`), `semicolons` (default `false`), and `addExtensions` (default `false`). Whatever the repo picks, exclude the generated route tree path from linters and formatters so the two never fight.

---

## Router Setup

- Keep router wiring explicit in `src/router.tsx`
- Root context setup should be discoverable from router/root-route files
- If the repo adds SSR or manual rendering, prefer a fresh per-request router factory instead of a process-global singleton (a module-level QueryClient leaks data across SSR requests)
- Cite the standard `createRouter` options: `defaultPreload: 'intent'`, `defaultPreloadStaleTime: 0`, `scrollRestoration: true`, and use `Wrap` to mount `QueryClientProvider`
- `scrollRestoration: true` is the option to configure. The `<ScrollRestoration />` component still works but is deprecated.
- `search.strict: true` drops search params that `validateSearch` does not return; set it when stray URL parameters must not reach app state. `rules/vite/routes.md` owns the loader cache defaults (`staleTime`, preload freshness, `gcTime`, `staleReloadMode`, `shouldReload`).
- For a subpath deploy, keep Vite `base` and the router `basepath` aligned (for example `basepath: import.meta.env.BASE_URL`). Aligning the pair is Hypercore guidance; each option is documented separately.
- Read router state from `router.state` (`matches`, `status`, `isLoading`). From `@tanstack/router-core` 1.171.16, `loadedAt`, `isTransitioning`, `statusCode`, and `redirect` are gone from `RouterState`, `match.status` no longer includes `'redirected'`, and `getMatch()`, `updateMatch()`, and `cancelMatch()` no longer exist.

```tsx
// src/router.tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createRouter, RouterProvider } from '@tanstack/react-router'
import { routeTree } from './routeTree.gen'

export const createAppRouter = () => {
  // Fresh QueryClient per request — prevents SSR data leaks
  const queryClient = new QueryClient()

  return createRouter({
    routeTree,
    context: { queryClient },
    defaultPreload: 'intent',
    defaultPreloadStaleTime: 0,
    scrollRestoration: true,
    Wrap: ({ children }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    ),
  })
}

declare module '@tanstack/react-router' {
  interface Register {
    router: ReturnType<typeof createAppRouter>
  }
}
```

- Root route uses the factory pattern with `createRootRouteWithContext<{ queryClient: QueryClient }>()` so the context type is preserved through nested routes
- App entrypoints pass the created router to `RouterProvider`; keep that wiring discoverable instead of hiding router setup behind ad-hoc globals.
- For SSR streaming with TanStack Query, wire `setupRouterSsrQueryIntegration({ router, queryClient })` from `@tanstack/react-router-ssr-query` inside the same factory. The package (1.167.x) peers on `@tanstack/react-router >= 1.170.33` and `@tanstack/react-query >= 5.102.0`, and `wrapQueryClient: false` skips its provider wrapper when the app already mounts `QueryClientProvider` itself.

---

## Route Token And Layout Convention

- TanStack Router supports `route.tsx`, `posts.route.tsx`, and other `routeToken`-based layouts
- Hypercore prefers folder routes with `route.tsx` for shared layout, `beforeLoad`, and shared loader behavior
- If the repo customizes `routeToken` or `indexToken`, keep that config explicit in `tsr.config.json`

---

## Env And Alias Rules

- Public client config must use `import.meta.env.VITE_*`
- Secret values do not belong in client-reachable route code
- Keep path aliases explicit in both Vite config and TypeScript config
- Prefer explicit env typing/runtime validation for non-trivial apps

---

## Review Checklist

- `vite.config.ts` keeps `tanstackRouter()` before `react()`, with `autoCodeSplitting` set explicitly
- `@vitejs/plugin-react` 6 runs on Vite 8, and `@tanstack/router-plugin` is on the same release as `@tanstack/react-router`
- New build config uses `oxc`, `build.rolldownOptions`, and `output.codeSplitting` instead of `esbuild`, `build.rollupOptions`, and `manualChunks`
- `routeTree.gen.ts` is not hand-edited and is excluded from linter and formatter
- Router setup is explicit and not hidden behind ad-hoc globals, with `scrollRestoration` set as an option
- `tsr.config.json`, if present, documents any `routeToken`/`indexToken` customization
- Env and alias setup are explicit

---

## Sources

> The Vite and TanStack Router platform facts stated here (the Rolldown/Oxc option names, the Node and ESM requirements, the `build.target` default, `server.forwardConsole`, `defineConfig`, `tanstackRouter()` before `react()`, the plugin-react 6 peer and Babel removal, `routeTree.gen.ts` as generated output with its formatting options, `createRouter` wired with `routeTree`, `scrollRestoration` and the deprecated `<ScrollRestoration />` component, `search.strict`, `basepath`, the `router.state` surface change, `ImportMetaEnv`/`vite/client`, and `loadEnv`) come from the dated snapshot recorded in `references/official/vite/current-docs-2026-11-04.md`, whose own verification date is 2026-11-04. The repo-shaped config choices and the `base`/`basepath` pairing advice are this package's own guidance. The folder-route and explicit alias/env preferences are Hypercore/repo-local conventions. No page was re-fetched for this file. Rule text and repository-local paths checked 2026-11-04; the `vite 8.3.6` current-stable figure was re-checked against the snapshot on 2026-11-07.
