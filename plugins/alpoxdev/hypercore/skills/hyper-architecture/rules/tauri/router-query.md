# Router and Query Boundaries

> Apply this rule when adopting or reviewing TanStack Router file-based routing and TanStack Query in a packaged Tauri v2 frontend. This architecture is a browser-only Vite SPA: read the dated TanStack reference for API facts; this file defines the architecture decision.

## Execution Model

Vite builds the React SPA into static assets, and Tauri packages and loads those assets in its WebView. TanStack Router owns browser navigation and file-based route generation. Configure `@tanstack/router-plugin/vite` before the React plugin so it generates `routeTree.gen.ts` from the route files during development and production builds. TanStack Query owns asynchronous data caching and freshness; it does not provide a file-routing system.
```ts
// vite.config.ts
import { tanstackRouter } from '@tanstack/router-plugin/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [tanstackRouter(), react()],
})
```

TanStack Start is outside this skill's scope. A request for it, including server functions, server routes, middleware, or SSR, MUST be routed to the full-stack architecture workflow rather than added to this packaged Vite SPA.

Native functionality crosses the reviewed desktop API/IPC boundary; remote services use ordinary browser HTTP APIs. Tauri Rust commands retain native authority. Do not treat a Vite module, route, or WebView state as a native trust boundary.

## Router Context Is the Composition Root

Create one module-owned `QueryClient` and one module-owned router for the WebView runtime. Construct neither in routes, components, loaders, query factories, nor render functions. The router context is typed and contains the shared client plus a deliberately narrow desktop API, not the raw Tauri bridge.

```ts
// src/router.tsx
import { QueryClient } from '@tanstack/react-query'
import { createRouter } from '@tanstack/react-router'
import { routeTree } from './routeTree.gen'
import { createDesktopApi } from './platform/desktop-api'

export interface RouterContext {
  queryClient: QueryClient
  desktop: ReturnType<typeof createDesktopApi>
}

export const queryClient = new QueryClient()
const desktop = createDesktopApi()

export const router = createRouter({
  routeTree,
  context: { queryClient, desktop },
  defaultPreloadStaleTime: 0,
})

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}

```

```tsx
// src/main.tsx
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClientProvider } from '@tanstack/react-query'
import { RouterProvider } from '@tanstack/react-router'
import { queryClient, router } from './router'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  </StrictMode>,
)
```

The root route MUST declare that same type with `createRootRouteWithContext<RouterContext>()`. `createDesktopApi()` owns IPC command selection, argument/result validation, and normalized client errors. Tauri runtime authority, capabilities, scopes, and domain authorization remain Rust-side controls. Route files consume only the minimum methods their feature needs. Do not pass `invoke`, `window.__TAURI__`, unrestricted plugin objects, or ambient process state through context.

`src/main.tsx` MUST supply the identical module-owned `QueryClient` and router to `QueryClientProvider` and `RouterProvider`. A second client silently breaks loader-prefetch reuse, invalidation, and test assumptions.

## Query Is the Sole Freshness Owner

A query factory owns each remote or native-backed resource's key, fetcher, and cache policy. Use `queryOptions` so loaders and components use the exact same definition.

```ts
// src/modules/preferences/queries/preferences.queries.ts
import { queryOptions } from '@tanstack/react-query'

export const preferencesOptions = (desktop: DesktopApi) =>
  queryOptions({
    queryKey: ['preferences'],
    queryFn: () => desktop.readPreferences(),
    staleTime: 30_000,
  })
```

```ts
// src/routes/preferences.tsx
export const Route = createFileRoute('/preferences')({
  loader: ({ context }) =>
    context.queryClient.ensureQueryData(preferencesOptions(context.desktop)),
  component: PreferencesPage,
})

function PreferencesPage() {
  const { desktop } = Route.useRouteContext()
  const { data } = useSuspenseQuery(preferencesOptions(desktop))
  return <PreferencesForm preferences={data} />
}
```

Rules:

- `loader` MUST warm the cache with `ensureQueryData`; the component MUST read the same factory with `useSuspenseQuery` (or `useQuery` when the UX intentionally does not suspend).
- Set freshness, retry, garbage collection, refetching, and persistence policy in Query options. Do not duplicate it with route-level timers, component effects, local mirrors, or a nonzero Router preload cache.
- Set `defaultPreloadStaleTime: 0` on the router so Router always re-runs preload work and Query alone decides whether data is fresh.
- A query key contains every input that changes the result. Do not capture such input invisibly in a query function.
- `validateSearch` MUST validate route search input. `loaderDeps` MUST contain every validated search dependency that changes loader output. Use the same dependencies in the query factory/key; route parameter dependencies are already identified by the route match.

The example below assumes Zod v4, where the schema is passed to `validateSearch` directly. A Zod v3 project must wrap the schema in `zodValidator` from `@tanstack/zod-adapter`; do not adopt the direct form on Zod v3, and do not keep both conventions in one route tree.

```ts
import { z } from 'zod'

const documentSearchSchema = z.object({
  revision: z.coerce.number().int().nonnegative().catch(0),
})

export const Route = createFileRoute('/documents/$documentId')({
  validateSearch: documentSearchSchema,
  loaderDeps: ({ search }) => ({ revision: search.revision }),
  loader: ({ context, params, deps }) =>
    context.queryClient.ensureQueryData(
      documentOptions(context.desktop, params.documentId, deps.revision),
    ),
  component: DocumentPage,
})
```

For writes, use a mutation whose function calls the narrow desktop API. On success, invalidate or update only the precise affected query keys through the same context `QueryClient`; do not reload the window or create a second source of truth.

```ts
const mutation = useMutation({
  mutationFn: (input: PreferencesInput) => desktop.writePreferences(input),
  onSuccess: () => queryClient.invalidateQueries({ queryKey: ['preferences'] }),
})
```

## Route States and Guards

Every meaningful route hierarchy MUST make pending, failure, and missing-resource behavior intentional:

- Use `pendingComponent` (and a considered `pendingMs`) for loader-bound navigation; do not leave a blank page.
- Use `errorComponent` for recoverable route/query failures. It must expose a safe retry path and must not disclose native paths, command internals, tokens, or raw Rust errors.
- Use `notFoundComponent` and throw or return Router's not-found result for an absent route resource; an empty success payload is not a substitute for a missing resource.
- Place common state UI at the nearest layout route that can own it, then specialize only where the user needs distinct recovery.

`beforeLoad` and redirects may guard navigation flow, for example an unlocked local workspace or an already-selected profile. They are **not authorization**. A user can call IPC outside the intended route, modify client state, or restore a stale route. Each privileged Tauri command and remote service MUST independently validate input and authorize the operation.

## Review Gate

Reject the proposed implementation or correct it when any condition holds:

1. File-based routes are not generated by `@tanstack/router-plugin/vite`, or the Router plugin is ordered after the React plugin.
2. More than one `QueryClient` or router exists, provider wiring uses a different client/router, raw Tauri bridge access occurs in a route, or freshness logic is duplicated.
3. A query loader/component pair uses different keys or fetchers, or a loader omits a validated search dependency that changes output.
4. Pending, error, or not-found behavior is absent for a meaningful route state.
5. A client-side guard is presented as the authorization control for a native capability.

See [`../../references/official/tauri/tanstack-vite-react-2026-11-04.md`](../../references/official/tauri/tanstack-vite-react-2026-11-04.md) for dated API evidence and [`tauri-ipc.md`](tauri-ipc.md) and [`security.md`](security.md) for command-boundary requirements.

## Sources

> Links checked 2026-11-04.

| Claim | Source |
|---|---|
| Router plugin ordering and file-route generation, typed router context, `defaultPreloadStaleTime`, `validateSearch`/`loaderDeps`, and pending/error/not-found components | [tanstack-vite-react-2026-11-04.md](../../references/official/tauri/tanstack-vite-react-2026-11-04.md); <https://tanstack.com/router/v1/docs/framework/react/guide/data-loading>; <https://tanstack.com/router/v1/docs/framework/react/guide/not-found-errors> |
| Zod v4 passing its schema directly to `validateSearch`, and Zod v3 needing `zodValidator` | <https://tanstack.com/router/latest/docs/framework/react/guide/search-params> |
| `queryOptions`, `ensureQueryData`, `useSuspenseQuery`, query-key inputs, staleness, and invalidation behavior | [tanstack-vite-react-2026-11-04.md](../../references/official/tauri/tanstack-vite-react-2026-11-04.md); <https://tanstack.com/query/v5/docs/reference/QueryClient>; <https://tanstack.com/query/latest/docs/framework/react/guides/query-keys> |
| The packaged static-asset boundary and Rust-side authority for native operations | [tauri-v2-2026-11-04.md](../../references/official/tauri/tauri-v2-2026-11-04.md); <https://v2.tauri.app/security/> |
| Route/page/module ownership, the narrow desktop adapter, and the rule that a client guard is not authorization | This repository's convention and safety policy; no external source |
