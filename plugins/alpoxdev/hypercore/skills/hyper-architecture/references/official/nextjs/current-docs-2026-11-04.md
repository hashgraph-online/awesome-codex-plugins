# Current Official Next.js Docs Snapshot — 2026-11-04

> Docs-index-checked official facts for drift-sensitive Next.js architecture decisions. Use this file before older doc maps when cache, prerendering, Proxy, route handler, or Server Action behavior matters.

checked_at: 2026-11-04
last_verified_at: 2026-11-04
library_id: `/vercel/next.js` at `v16.4.5`
source_priority: official Next.js docs read as markdown, backed by the release feed at `https://github.com/vercel/next.js/releases` and canonical `https://nextjs.org/docs/...` pages.

## Contents

- [Release Baseline](#release-baseline)
- [Current Official Facts](#current-official-facts)
- [Architecture Implications](#architecture-implications)
- [Source URLs Checked](#source-urls-checked)
- [Sources](#sources)

## Release Baseline

| Version | Date | Status |
|---|---|---|
| 16.4.5 | 2026-11-03 | Latest stable patch; carries security fixes |
| 16.4.0 | 2026-10-06 | Minor release that recommends Cache Components for every app |
| 16.3.0 | 2026-08-03 | Minor release that introduced Instant Navigations, `io`, `catchError` |
| 16.5.0-canary.40 | canary | Not adopted; canary channel only |

## Current Official Facts

- App Router is built on React Server Components and uses file-system routing with layouts, nested routes, loading states, error handling, and special files such as `page.tsx`, `layout.tsx`, `loading.tsx`, `error.tsx`, `not-found.tsx`, and `route.ts`.
- In App Router, pages and layouts are Server Components by default. Add `'use client'` only at client entry points that need interactivity, browser APIs, or client hooks.
- The optional `src/` directory is a project organization choice, while `app/`, `pages/`, and `public/` have framework-level meanings. Shared folders such as `src/lib` or `src/services` are repo-local conventions, not official Next.js requirement.
- Route groups organize routes without changing URL paths. Private folders such as `_components` or `_lib` opt implementation code out of routing and should be used for segment-local non-routable internals.
- Since Next.js 16.4, the docs recommend Cache Components as the best choice for every App Router app, and new apps created with the recommended `create-next-app` defaults already ship with Cache Components and Partial Prefetching enabled.
- Cache Components is enabled with two flags, `cacheComponents: true` and `partialPrefetching: true`. Leaving `partialPrefetching` unset behaves like `false` and logs a warning; `partialPrefetching` without `cacheComponents` throws at config validation. Both flags become unconditional in the next major release.
- With Cache Components enabled, `dynamic`, `dynamicParams`, `revalidate`, and `fetchCache` route segment options are removed. Remaining options are `dynamicParams` (only without Cache Components), `runtime` (`'edge'` deprecated), `preferredRegion` (deprecated), `maxDuration`, plus `ensureStatic` (`'auto'` default) for pages and layouts.
- `ensureStatic` accepts `'auto' | 'shell' | 'prefetch' | 'navigation' | false`. A layout applies its level to every route below it, a child segment may only be stricter, and parallel slots rendered together must agree.
- `instant` (`v16.3` stable) configures Instant Navigation validation; `prefetch` (`v16.3` stable) configures per-segment prefetching with `'partial'` and `'force-disabled'`. Both require Cache Components and cannot be exported from a Client Component.
- `use cache`, `use cache: remote`, and `use cache: private` are distinct caching directives. `use cache` cannot read `cookies()`, `headers()`, or `searchParams`. `use cache: private` may read them, deduplicates matching calls within one request, keeps the result in client memory for its `stale` window, and stores nothing in a server cache across requests. `use cache: remote` uses a remote handler, does not persist across deploys, and cannot nest with `use cache: private`.
- Pair every cache directive with `cacheLife`; without one the implicit `default` profile applies. A `revalidate` of `0` or `expire` under five minutes excludes the output from prerenders, `stale` under 30 seconds excludes it, and `stale` between 30 seconds and five minutes is prerendered but excluded from the App Shell.
- With Cache Components, prefer `io()` over `connection()`. `io()` suspends during prerendering, so the code after it leaves the static shell while staying cacheable and prefetchable; `connection()` waits for a real user request. `unstable_noStore` remains legacy-only.
- `navigation()` and `prefetch()` (`v16.4`) defer expensive work to a later navigation stage. `navigation()` keeps work out of the App Shell and per-link prefetches, `prefetch()` keeps it out of the App Shell only. Both throw inside `use cache`, `use cache: private`, `after()`, `generateStaticParams`, and Client Components.
- The Edge Runtime is deprecated. Remove the `runtime` export from route files; with Cache Components, remove `runtime = 'nodejs'` as well, because Cache Components requires the Node.js runtime and rejects the `runtime` segment config.
- Server Actions are reachable POST surfaces. Next.js dispatches them one at a time per client, so client-side `Promise.all` does not parallelize them. `updateTag`, `revalidatePath`, `refresh`, cookie mutation, and `redirect` re-render the current route in the same response; `revalidateTag` with a stale-while-revalidate profile does not.
- `updateTag` and `refresh` are Server Action-only. `revalidateTag` works in Server Functions and Route Handlers, cannot run in Client Components or Proxy, and takes a second argument such as `'max'`; the single-argument form is deprecated and behaves like `{ expire: 0 }`.
- `experimental.serverActions` holds `allowedOrigins` and `bodySizeLimit` (1MB default). Origins are compared against `x-forwarded-host` or `host`, `*` matches one label and `**` one or more, and a request with no `Origin` header is allowed with a warning.
- Action IDs rotate at most every 14 days, so a client on an older build can hit "Failed to find Server Action". Keep `NEXT_SERVER_ACTIONS_ENCRYPTION_KEY` stable across instances and prefer rolling deploys.
- `catchError` from `next/error` became stable in `v16.3` and provides component-level error boundaries that cooperate with `redirect()` and `notFound()`; `error.tsx` also receives `retry()`.
- Route Handlers use HTTP method exports such as `GET`, `POST`, `PUT`, `PATCH`, and `DELETE`. With Cache Components, `GET` handlers follow the same prerendering model as UI routes, and `use cache` must live in a helper rather than the handler body.
- `NextResponse.next()` is not valid inside Route Handlers; it belongs to Proxy-style request continuation.
- Next.js 16 deprecates the old `middleware` file convention in favor of `proxy.ts` / `proxy.js`. Proxy can live at the project root or `src/` root, defaults to the Node.js runtime, does not accept a `runtime` config option, should use static narrow matchers, still runs for `_next/data` even when a negative matcher excludes it, and cannot call `revalidateTag`.
- Environment variables are loaded from project-root `.env*` files, not from `src/`. Only `NEXT_PUBLIC_` variables are bundled for browser code, and public values are build-time inlined.
- `next/root-params` (`v16.3`) lets any Server Component read a root-level parameter such as `[lang]`, and a `use cache` key includes only the root params actually read. It is currently limited to Server Components.
- `next upgrade --agent` gives an agent version-specific upgrade guidance, `next dev` writes and maintains a version-matched `AGENTS.md` block, and `experimental.agentUpgrade` defaults to `'security'`.
- `next build` can type-check with the TypeScript 7 CLI (`useTypeScriptCli`), enabled by bumping the project's `typescript` dependency to `^7`.
- React 19.3 adds stable View Transitions, `browser()` in `react-dom`, and direct Context rendering: a Server Component can import and render a Context object from a `'use client'` module without an extra provider component.
- With Cache Components, navigation keeps state through React `<Activity mode="hidden">`: component state survives, effects are cleaned up when a route is hidden and recreated when it becomes visible again.

## Architecture Implications

- Treat `src/lib/<domain>/` and `src/services/<domain-or-provider>/` as Hypercore/repo-local conventions. They are useful for ownership and runtime boundaries but not official Next.js law.
- Do not add new direct leaf files such as `src/lib/foo.ts` or `src/services/foo.ts` in touched shared roots unless the project records an explicit exception.
- Prefer Server Components for initial reads, Server Actions for internal UI writes, Route Handlers for HTTP-native endpoints, and Proxy only for last-resort pre-render interception.
- Cache Components is the recommended default for new work; adoption in an existing app still needs an explicit migration reason and the two-flag config in the same change.
- Do not design client flows that assume parallel Server Action dispatch, and do not treat state preservation across navigation as unmount-based.

## Source URLs Checked

- `https://nextjs.org/docs/llms.txt`
- `https://nextjs.org/blog/next-16-4`
- `https://nextjs.org/blog/next-16-3`
- `https://nextjs.org/docs/app/getting-started/caching`
- `https://nextjs.org/docs/app/api-reference/config/next-config-js/cacheComponents`
- `https://nextjs.org/docs/app/api-reference/config/next-config-js/partialPrefetching`
- `https://nextjs.org/docs/app/api-reference/config/next-config-js/serverActions`
- `https://nextjs.org/docs/app/api-reference/directives/use-cache`
- `https://nextjs.org/docs/app/api-reference/directives/use-cache-remote`
- `https://nextjs.org/docs/app/api-reference/directives/use-cache-private`
- `https://nextjs.org/docs/app/api-reference/functions/cacheLife`
- `https://nextjs.org/docs/app/api-reference/functions/io`
- `https://nextjs.org/docs/app/api-reference/functions/connection`
- `https://nextjs.org/docs/app/api-reference/functions/navigation`
- `https://nextjs.org/docs/app/api-reference/functions/prefetch`
- `https://nextjs.org/docs/app/api-reference/functions/revalidateTag`
- `https://nextjs.org/docs/app/api-reference/functions/updateTag`
- `https://nextjs.org/docs/app/api-reference/functions/refresh`
- `https://nextjs.org/docs/app/api-reference/functions/catchError`
- `https://nextjs.org/docs/app/api-reference/file-conventions/route-segment-config`
- `https://nextjs.org/docs/app/api-reference/file-conventions/route-segment-config/ensureStatic`
- `https://nextjs.org/docs/app/api-reference/file-conventions/route-segment-config/instant`
- `https://nextjs.org/docs/app/api-reference/file-conventions/route-segment-config/prefetch`
- `https://nextjs.org/docs/app/api-reference/file-conventions/route-segment-config/runtime`
- `https://nextjs.org/docs/app/api-reference/file-conventions/route`
- `https://nextjs.org/docs/app/api-reference/file-conventions/proxy`
- `https://nextjs.org/docs/app/guides/server-actions`
- `https://nextjs.org/docs/app/guides/environment-variables`
- `https://nextjs.org/docs/app/guides/data-security`
- `https://nextjs.org/docs/app/api-reference/functions/next-root-params`
- `https://nextjs.org/docs/app/guides/upgrading/agent-upgrade`
- `https://nextjs.org/docs/app/api-reference/config/next-config-js/useTypeScriptCli`
- `https://react.dev/blog/2026/09/09/react-19-3`

## Sources

> Checked 2026-11-04. Every fact above was read from the `nextjs.org/docs` markdown alternate, the release posts, or the React 19.3 post listed under "Source URLs Checked"; the version baseline was confirmed against the npm `latest` tag for `next`.

| Claim | Source |
|---|---|
| The version baseline in "Release Baseline" above | `https://github.com/vercel/next.js/releases` and `https://nextjs.org/docs/llms.txt` (`@doc-version: 16.4.5`) |
| The framework facts in "Current Official Facts" above | the `https://nextjs.org/docs/...` pages listed under "Source URLs Checked" |
| The React behavior in the last two facts | `https://react.dev/blog/2026/09/09/react-19-3` |
| The architecture implications in "Architecture Implications" above | those same official pages; the `src/lib` / `src/services` naming is a Hypercore/repo-local convention, not an official requirement |
