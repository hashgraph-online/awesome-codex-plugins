# Official TanStack, Vite, and React Snapshot — 2026-11-04

- last_verified_at: 2026-11-04
- applies_to: TanStack Router v1, TanStack Query v5, Vite 8.3 current docs, React 19.3 docs
- source_priority: canonical guide/reference pages > official examples > package registry metadata
- refresh_when: any listed package major changes; Router file-routing/plugin APIs change; Query cache/testing APIs change; Tauri changes its static-frontend contract; Vite build/base defaults change

Use this file only for version-sensitive API and runtime facts. Project and user instructions remain authoritative. The Tauri-specific trust and packaging boundary is recorded in `tauri-v2-2026-11-04.md`.

## Contents

- Package Snapshot
- TanStack Router Facts
- TanStack Query Facts
- Vite Facts
- React Facts
- Project-Structure Evidence
- Integration Caveats
- Sources

## Package Snapshot

The following npm `latest` metadata was observed on 2026-11-04, and the `vite` and `@tanstack/react-query` rows were re-checked on 2026-11-07. It is evidence of the registry state, not a dependency-upgrade instruction:

| Package | Observed version | Registry |
|---|---:|---|
| `@tanstack/react-router` | `1.170.46` | <https://registry.npmjs.org/@tanstack/react-router/latest> |
| `@tanstack/router-plugin` | `1.168.48` | <https://registry.npmjs.org/@tanstack/router-plugin/latest> |
| `@tanstack/react-query` | `5.107.1` | <https://registry.npmjs.org/@tanstack/react-query/latest> |
| `@tanstack/zod-adapter` | `1.167.0` | <https://registry.npmjs.org/@tanstack/zod-adapter/latest> |
| `vite` | `8.3.6` | <https://registry.npmjs.org/vite/latest> |
| `@vitejs/plugin-react` | `6.2.1` | <https://registry.npmjs.org/@vitejs/plugin-react/latest> |
| `react` | `19.3.1` | <https://registry.npmjs.org/react/latest> |
| `zod` | `4.6.7` | <https://registry.npmjs.org/zod/latest> |

## TanStack Router Facts

- TanStack Router, not TanStack Query, owns file-based routing. Configure `@tanstack/router-plugin/vite` in the Vite build to discover route files and generate the route tree; Query owns asynchronous data cache and freshness.
- File-based routing is the recommended default. Generated `routeTree.gen.ts` is build output; edit source routes and plugin configuration instead.
- Put `tanstackRouter()` before the React plugin in Vite configuration so route generation precedes the React transform.
- The plugin options in `1.168.48` are `target`, `autoCodeSplitting`, the route directory/token/generated-tree options, and formatting/HMR options. `enableRouteGeneration` was removed and route generation now always runs, so passing it is dead configuration.
- `createRouter` receives the generated route tree. Declaration-merge `Register.router` for application-wide type safety.
- Use `createRootRouteWithContext<T>()` and router context for explicit dependencies such as one `QueryClient` and a narrow desktop API interface. Loaders and `beforeLoad` cannot call React hooks.
- Router loaders receive context, params, validated search dependencies, and an abort controller. Put search values that affect loading in `loaderDeps`.
- `beforeLoad` route guards control navigation UX only. Every Tauri command or remote endpoint must enforce authorization independently.
- Define root pending, error, and not-found UI. Throw `notFound()` only for missing resources; keep permission, command, and network failures as errors.
- Preloading is speculative. Loaders and preloads must not perform writes, prompts, or privileged native side effects.
- With Zod v4, pass the schema directly to `validateSearch`. Zod v3 still needs `zodValidator` from `@tanstack/zod-adapter`; do not mix the two conventions in one route tree.

Sources:

- <https://tanstack.com/router/v1/docs/framework/react/guide/creating-a-router>
- <https://tanstack.com/router/v1/docs/framework/react/guide/router-context>
- <https://tanstack.com/router/v1/docs/framework/react/routing/file-based-routing>
- <https://tanstack.com/router/v1/docs/framework/react/guide/data-loading>
- <https://tanstack.com/router/v1/docs/framework/react/guide/preloading>
- <https://tanstack.com/router/v1/docs/framework/react/guide/not-found-errors>
- <https://tanstack.com/router/v1/docs/framework/react/guide/authenticated-routes>
- <https://tanstack.com/router/latest/docs/framework/react/guide/search-params>
- <https://raw.githubusercontent.com/TanStack/router/main/packages/router-plugin/CHANGELOG.md>

## TanStack Query Facts

- Router's documented Query integration places one `QueryClient` in router context, calls `ensureQueryData(queryOptions)` for critical route data, and reads the same options with `useSuspenseQuery` under `QueryClientProvider`.
- When Query owns freshness, set Router preload stale time to `0` so loaders run and Query decides whether cached data is fresh.
- `ensureQueryData` returns cached data or fetches when absent; stale revalidation is not automatic unless requested. `prefetchQuery` does not throw and is unsuitable as the only critical-loader gate.
- Query keys are top-level serializable arrays and must include every variable used by the query function.
- Query functions must resolve data or throw/reject. They receive an `AbortSignal`, but Tauri `invoke` does not become cancellable merely by receiving that signal; native cancellation needs an explicit cooperative protocol.
- Query data is stale by default and may refetch on mount, focus, and reconnect. Desktop projects must choose `staleTime`, refetch, retry, and invalidation policy intentionally.
- Mutation and fetch filters are narrower than they once were: `status` is no longer accepted by `QueryClient.isMutating`/`useIsMutating`, and `fetchStatus` is no longer accepted by `QueryClient.isFetching`/`useIsFetching`. Filter by the remaining mutation/fetch identity fields instead of relying on status strings.
- Tests should use an isolated QueryClient and disable retries for expected error cases.

Sources:

- <https://tanstack.com/router/v1/docs/framework/react/guide/external-data-loading>
- <https://tanstack.com/query/v5/docs/reference/QueryClient>
- <https://tanstack.com/query/latest/docs/framework/react/guides/important-defaults>
- <https://tanstack.com/query/latest/docs/framework/react/guides/query-keys>
- <https://tanstack.com/query/latest/docs/framework/react/guides/query-functions>
- <https://tanstack.com/query/latest/docs/framework/react/guides/query-cancellation>
- <https://tanstack.com/query/v5/docs/framework/react/guides/testing>
- <https://raw.githubusercontent.com/TanStack/query/main/packages/react-query/CHANGELOG.md>

## Vite Facts

- Only `VITE_`-prefixed environment values are exposed through `import.meta.env` by default; they are strings and must never contain secrets. A project that also exposes a build-tool prefix such as Tauri's `TAURI_ENV_*` widens what reaches the renderer, so treat every added prefix as a public-input decision.
- `base` controls emitted asset URLs. Relative bases are supported for embedded deployments, but the selected value must be verified against Tauri's packaged asset origin and lazy chunks.
- Keep the development server on loopback unless constrained remote-device debugging is required. `strictPort: true` prevents Tauri's fixed `devUrl` from silently pointing at the wrong port. Avoid broad `allowedHosts` or CORS settings.
- Vite transpiles TypeScript but does not type-check it. Run type checking separately.
- Vite's default build target changes with releases and supplies no API polyfills. Choose and test a target against the oldest supported system WebView.
- Vite 8 uses `build.rolldownOptions`; `build.rollupOptions` is a deprecated alias. Vite 8.2 added a top-level `input` option and Vite 8.3 added a top-level `tsconfig` option; both live beside `build`, not inside it. Inspect the installed version before editing bundler options.
- Since Vite 8.2, assets referenced from JavaScript are emitted with `import.meta.ROLLDOWN_FILE_URL_*` URLs. After upgrading, re-check that packaged entry, lazy-chunk, and non-root route asset URLs still resolve from the Tauri asset origin.

Sources:

- <https://vite.dev/guide/env-and-mode>
- <https://vite.dev/config/shared-options#base>
- <https://vite.dev/config/server-options>
- <https://vite.dev/config/build-options#build-target>
- <https://vite.dev/guide/features#transpile-only>
- <https://raw.githubusercontent.com/vitejs/vite/main/packages/vite/CHANGELOG.md>
- <https://vite.dev/blog/announcing-vite8-1>

## React Facts

- A Vite SPA owns one explicit bootstrap with `createRoot`; mount `RouterProvider` beneath the providers it requires.
- Keep `StrictMode` in development. Duplicate Tauri listeners exposed by effect re-runs indicate missing cleanup or non-idempotent setup, not a reason to remove StrictMode.
- Use effects only to synchronize with external systems and always return listener cleanup when registration must be reversed. User-initiated native commands belong in event handlers.
- Pair lazy features with loading and rendering-error UI. Error Boundaries do not catch async callback or event-handler failures; handle command failures on their promise/event path.
- Use `useSyncExternalStore` for a shared mutable external store only with stable subscriptions and cached immutable snapshots.
- React 19.3 integrates the Trusted Types API, so a packaged app can consider `require-trusted-types-for 'script'` in its CSP once every script sink is audited; enabling it without that audit breaks DOM script injection points.
- React 19.3 renders transitions independently instead of entangling them into one render, so re-check pending UI when several transitions overlap. `<ViewTransition />` and `addTransitionType` are stable APIs in this line.

Sources:

- <https://react.dev/reference/react-dom/client/createRoot>
- <https://react.dev/reference/react-dom/client/hydrateRoot>
- <https://react.dev/reference/react/StrictMode>
- <https://react.dev/reference/react/useEffect>
- <https://react.dev/reference/react/lazy>
- <https://react.dev/reference/react/Component#catching-rendering-errors-with-an-error-boundary>
- <https://react.dev/reference/react/useSyncExternalStore>
- <https://raw.githubusercontent.com/facebook/react/main/CHANGELOG.md>

## Project-Structure Evidence

- Tauri's official project structure separates the optional JavaScript project at the repository top level from the Cargo/Tauri project in `src-tauri/`. It documents `tauri.conf.json`, capabilities, icons, `lib.rs`, and the thin desktop `main.rs`; it does not prescribe the React folders below `src/`.
- TanStack Router's file-naming contract assigns routing meaning to `__root`, `$`, `_`, `-`, route groups `(folder)`, `index`, and `route`. In particular, `-` excludes colocated files/folders from route generation, while `(folder)` organizes routes without adding a URL segment.
- React's legacy file-structure FAQ explicitly declines to prescribe one layout, describes grouping by feature/route and by file type as common approaches, recommends avoiding deep nesting, and recommends colocating files that change together. Because that page is legacy, use it only as comparative organization evidence, not as a current React API requirement.
- Redux's current code-structure FAQ recommends feature/domain folders for Redux applications. This skill does not require Redux; it uses the feature-folder result only as comparative support for cohesive `modules/<domain>/` ownership.

Sources:

- <https://v2.tauri.app/start/project-structure/>
- <https://tanstack.com/router/latest/docs/framework/react/routing/file-naming-conventions>
- <https://legacy.reactjs.org/docs/faq-structure.html>
- <https://redux.js.org/faq/code-structure/>

**Derived convention:** keep the official/generated routing surface in `routes/`; add `pages/` for nontrivial screen composition, `modules/` for cohesive domain capabilities, and `components/` only for reused business-agnostic UI. These names and dependency rules/tauri are Hypercore conventions, not vendor mandates. Do not scaffold every layer or combine competing `features/` and `modules/` vocabularies without a repository-specific contract.

## Integration Caveats

- Tauri does not publish an official endorsement of this exact Vite SPA stack. Treat compatibility as an integration that must pass a production build and packaged-WebView smoke test.
- Do not infer Tauri security behavior from TanStack, Vite, or React docs. Use `tauri-v2-2026-11-04.md` for native trust boundaries.
- Do not rename an official fact into a Hypercore convention or vice versa. Directory layout and typed adapter placement remain repository conventions unless official docs say otherwise.

## Sources

> Links checked 2026-11-04.

| Claim | Source |
|---|---|
| Package snapshot versions | The registry URLs in the Package Snapshot table above |
| Router and Query facts | The TanStack source lists in the sections above (`tanstack.com/router/...`, `tanstack.com/query/...`, package CHANGELOGs) |
| Vite facts | The Vite source list in the section above (`vite.dev/...`, Vite CHANGELOG) |
| React facts | The React source list in the section above (`react.dev/...`, React CHANGELOG) |
| Project-structure comparison evidence | <https://v2.tauri.app/start/project-structure/>; <https://legacy.reactjs.org/docs/faq-structure.html>; <https://redux.js.org/faq/code-structure/> |
| The derived `routes/`/`pages/`/`modules/`/`components/` convention | This repository's convention; no external source |
