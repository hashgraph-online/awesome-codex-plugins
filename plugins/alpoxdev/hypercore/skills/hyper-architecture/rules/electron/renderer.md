# Renderer: React, Tailwind CSS v4, TanStack Router and Query

> The renderer is a sandboxed web app: React renders it, Tailwind v4 styles it from the renderer build only, TanStack Router routes it with hash or memory history, and TanStack Query caches every IPC read behind one desktop adapter.

Rules are labelled `official` when a page in `references/official/electron/electron-2026-11-08.md` states them, and `hypercore-default` when this package chose the default.

## 1. Bootstrap

- `official` — Mount one `createRoot` in `src/renderer/src/main.tsx`, with `QueryClientProvider` above `RouterProvider`, inside `StrictMode`. Keep `StrictMode` in development: duplicate IPC listeners exposed by effect re-runs mean a missing unsubscribe, not a reason to drop it.
- `hypercore-default` — `src/renderer/src/router.tsx` owns the one `QueryClient`, the one history instance, and the one router; nothing else constructs them.

```tsx
// src/renderer/src/router.tsx
import { QueryClient } from '@tanstack/react-query'
import { createHashHistory, createRouter } from '@tanstack/react-router'
import { routeTree } from './routeTree.gen'
import { desktop } from './platform/desktop'

export const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 30_000, refetchOnWindowFocus: false, networkMode: 'always' } },
})

export const router = createRouter({
  routeTree,
  history: createHashHistory(),
  context: { queryClient, desktop },
  defaultPreloadStaleTime: 0,
})

declare module '@tanstack/react-router' {
  interface Register { router: typeof router }
}
```

## 2. TanStack Router

- `official` — TanStack Router uses browser history by default. Hash history suits environments without a server that rewrites to `index.html`, and memory history keeps the location in memory; pass the instance as `createRouter({ routeTree, history })`.
- `official` — The packaged renderer has no server to rewrite deep paths. Under `file://` a browser-history route such as `/settings` becomes `file:///…/index.html/settings` and breaks on reload or in a new window. Even under a custom protocol, a reload of a deep browser-history path asks the protocol handler for a file that does not exist.
- `hypercore-default` — Use `createHashHistory()` for a single-window app. Use one `createMemoryHistory()` router per tab or pane when the app owns several independent locations (the pattern Cherry Studio ships). Keep browser history only when the `protocol.handle` callback deliberately falls back to `index.html` for unknown paths and that fallback is tested.
- `official` — Configure `tanstackRouter({ target: 'react', autoCodeSplitting: true })` before `@vitejs/plugin-react`, both inside `renderer.plugins`. The plugin resolves `routesDirectory` (default `./src/routes`) and `generatedRouteTree` (default `./src/routeTree.gen.ts`) from the process working directory, not from electron-vite's `renderer.root`, so pass absolute paths such as `join(import.meta.dirname, 'src/renderer/src/routes')`; a missing override fails with `ENOENT … scandir '<repo>/src/routes'`. `routeTree.gen.ts` is generated; edit route files, never the tree.
- `official` — `beforeLoad` guards and redirects control navigation only. Every main-process handler authorizes its own operation, because injected script can call the preload API without visiting the guarded route.
- `official` — Route loaders and preloads are speculative: they must not write, prompt, open dialogs, or trigger native side effects. Put validated search values that change a loader's output in `loaderDeps`, and define `pendingComponent`, `errorComponent`, and `notFoundComponent` for meaningful route hierarchies.

## 3. TanStack Query over IPC

- `hypercore-default` — `src/renderer/src/platform/desktop.ts` is the only renderer file that reads `window.desktop`. It turns each `{ ok: false }` result into a thrown `DesktopError`, so a `queryFn` rejects as Query requires, and it exposes typed methods only.
- `official` — A `queryFn` must resolve data or throw. A query key is a serializable array that contains every input the `queryFn` uses.
- `hypercore-default` — Each domain under `features/<domain>/` defines its `queryOptions` once; the route loader calls `ensureQueryData` with the same options the component reads with `useSuspenseQuery`. Mutations call the desktop adapter and invalidate only the affected keys.
- `official` — Query treats data as stale by default and refetches on mount, window focus, and reconnect; `focusManager` listens for `visibilitychange` in the renderer. In a desktop window every alt-tab can therefore re-run IPC reads. Choose `staleTime` and `refetchOnWindowFocus` per query on purpose instead of leaving the web defaults. When focus refetch is wanted, drive `focusManager.setEventListener` from the `BrowserWindow` `focus` and `blur` events that main pushes through the preload.
- `official` — Query's default `networkMode: 'online'` pauses queries while Chromium reports offline; `'always'` is the documented mode for a `queryFn` that does not need the network. IPC-backed queries use `'always'`; queries that reach a remote API keep `'online'`.
- `official` — Passing the `AbortSignal` to an IPC call does not cancel work in main. Native cancellation needs its own channel (for example a cancel message or a `MessagePort` the main side watches).
- `hypercore-default` — Data that main pushes (file watchers, download progress, update status) reaches Query through a preload `on*` subscription in one effect that calls `queryClient.setQueryData` or `invalidateQueries`, and returns the unsubscribe function. Do not also poll the same data with `refetchInterval`.
- `hypercore-default` — Tests create a fresh `QueryClient` per test with `retry: false` and a fake desktop adapter; they never touch the real `window.desktop`.

## 4. Tailwind CSS v4

- `official` — Install `tailwindcss` and `@tailwindcss/vite`, add `tailwindcss()` to the renderer Vite plugins, and put `@import "tailwindcss";` in the renderer CSS entry. Version 4 needs no `tailwind.config.js` and no PostCSS config; theme values live in CSS with `@theme`, plugins with `@plugin`, and custom variants with `@custom-variant`.
- `official` — The plugin belongs to the renderer build only. In `electron.vite.config.ts` that is `renderer.plugins`; a root-level or `main` plugin never scans the renderer and only slows the Node builds.
- `official` — Automatic source detection skips `.gitignore`d paths and `node_modules`. Register class sources outside the renderer root (a workspace UI package, a `node_modules` component library) with `@source`, and exclude fixtures with `@source not`.
- `official` — Tailwind v4 targets Safari 16.4, Chrome 111, and Firefox 128. Every supported Electron major ships a far newer Chromium, so no v3 compatibility mode or extra PostCSS step is needed.
- `hypercore-default` — Implement dark mode with `@custom-variant dark (&:where(.dark, .dark *));` and a class set on `<html>` from the OS theme that main reports (`nativeTheme`) through the preload, so the window background, title bar, and CSS agree.
- `hypercore-default` — Keep design tokens in one `@theme` block in `main.css`. A shared component library keeps its own CSS and is pulled in with `@source`, not by copying its classes.

## Review gate

1. A renderer file reads `window.desktop` outside `platform/desktop.ts`, or imports `electron` or `node:*`.
2. The router uses browser history while production loads `file://` or a protocol handler with no tested `index.html` fallback.
3. The router plugin follows the React plugin, or either one, or Tailwind, sits outside `renderer.plugins`.
4. More than one `QueryClient` or router exists, or a loader and its component use different query options.
5. A `queryFn` returns an `{ ok: false }` envelope as data instead of throwing.
6. Window-focus refetch policy was left at the web default for queries that call IPC, without a stated reason.
7. A push subscription has no unsubscribe, or pushed data is also polled.
8. `tailwind.config.js` or a PostCSS Tailwind step remains alongside `@tailwindcss/vite` with no migration note.

## Sources

> Checked 2026-11-08.

| Claim | Source |
|---|---|
| Browser, hash, and memory history and passing an instance to `createRouter` | https://tanstack.com/router/latest/docs/framework/react/guide/history-types |
| Router plugin order, `routesDirectory`, and `generatedRouteTree` | https://tanstack.com/router/latest/docs/framework/react/installation/with-vite |
| Loader, preload, guard, and route-state behavior | https://tanstack.com/router/v1/docs/framework/react/guide/data-loading, https://tanstack.com/router/v1/docs/framework/react/guide/authenticated-routes |
| Query defaults, `focusManager`, network modes, query keys, and query functions | https://tanstack.com/query/latest/docs/framework/react/guides/important-defaults, https://tanstack.com/query/latest/docs/reference/focusManager, https://tanstack.com/query/latest/docs/framework/react/guides/network-mode, https://tanstack.com/query/latest/docs/framework/react/guides/query-keys |
| `routesDirectory` resolving from the working directory inside an electron-vite renderer | https://github.com/TanStack/router/issues/1170 |
| Tailwind v4 Vite install, CSS-first configuration, and browser targets | https://tailwindcss.com/docs/installation/using-vite, https://tailwindcss.com/docs/theme, https://tailwindcss.com/docs/compatibility |
| Source detection and `@source` | https://tailwindcss.com/docs/detecting-classes-in-source-files |
| Dark mode custom variant | https://tailwindcss.com/docs/dark-mode |
| `file://` breaking browser-history routes, memory routers per tab, hash history on desktop | surveyed apps: https://github.com/CherryHQ/cherry-studio, https://github.com/chatboxai/chatbox |
| The desktop adapter, envelope-to-throw rule, push-to-cache pattern, and token location | this package's convention, not an official requirement |
