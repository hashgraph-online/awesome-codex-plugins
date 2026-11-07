# Official Next.js Docs Map

> Canonical official doc surfaces this skill depends on. Re-check these when behavior drifts or a rule becomes ambiguous.

Last verified: 2026-11-04 against latest stable Next.js 16.4.5 (`npm dist-tag latest`). 16.4.0 shipped 2026-10-06 and 16.3.0 shipped 2026-08-03; 16.5 exists only on canary.

last_verified_at: 2026-11-04

Reader access rule: when re-checking official docs, prefer the markdown alternate (`https://nextjs.org/docs/...md`) or Jina Reader markdown (`https://r.jina.ai/https://nextjs.org/docs/...`) so agents can inspect the current page text without relying on browser rendering. Keep the canonical URL listed below as the original source URL.

## Contents

- [Core Sources](#core-sources)
- [Drift Watchlist](#drift-watchlist)
- [Interpretation Rules](#interpretation-rules)
- [Sources](#sources)

## Core Sources

- App Router index
  URL: `https://nextjs.org/docs/app`
  Use for: current App Router learning path and official navigation.

- Docs index
  URL: `https://nextjs.org/docs/llms.txt`
  Use for: the authoritative page list and the `@doc-version` marker for the installed docs.

- Project Structure
  URL: `https://nextjs.org/docs/app/getting-started/project-structure`
  Use for: top-level folders, `app` / `pages` / `public` / `src`, route groups, private folders, metadata conventions, and organization strategies.

- File-system Conventions
  URL: `https://nextjs.org/docs/app/api-reference/file-conventions`
  Use for: special files including `page`, `layout`, `loading`, `error`, `not-found`, `forbidden`, `unauthorized`, `route`, `proxy`, metadata files, and route segment config.

- Server and Client Components
  URL: `https://nextjs.org/docs/app/getting-started/server-and-client-components`
  Use for: Server Component default, `'use client'` boundaries, serializable props, provider depth, RSC payload, and `server-only` / `client-only` guidance.

- Server and Client Boundary guide
  URL: `https://nextjs.org/docs/app/guides/server-and-client-boundary`
  Use for: where Server and Client Components run and how the boundary between them behaves.

- Fetching Data
  URL: `https://nextjs.org/docs/app/getting-started/fetching-data`
  Use for: server-first fetching, streaming, `<Suspense>`, preloading, and client fetching boundaries.

- Caching
  URL: `https://nextjs.org/docs/app/getting-started/caching`
  Use for: Cache Components, static shell, runtime API handling, `use cache`, `use cache: private`, `cacheLife`, prerendering thresholds, and prefetch behavior.

- Revalidating
  URL: `https://nextjs.org/docs/app/getting-started/revalidating`
  Use for: time-based and on-demand revalidation entry points.

- Caching and Revalidating (Previous Model)
  URL: `https://nextjs.org/docs/app/guides/caching-without-cache-components`
  Use for: `fetch` cache options, `unstable_cache`, and route segment configs in projects that have not adopted Cache Components.

- How Revalidation Works
  URL: `https://nextjs.org/docs/app/guides/how-revalidation-works`
  Use for: tag system, cache consistency, and multi-instance coordination.

- `use cache`
  URL: `https://nextjs.org/docs/app/api-reference/directives/use-cache`
  Use for: `cacheComponents` requirement, cached scopes, cache keys, serialization constraints, and request-time API restrictions.

- `use cache: private`
  URL: `https://nextjs.org/docs/app/api-reference/directives/use-cache-private`
  Use for: runtime API access inside a cached scope, request-scoped deduplication, client-memory stale window, and static-shell exclusion.

- `use cache: remote`
  URL: `https://nextjs.org/docs/app/api-reference/directives/use-cache-remote`
  Use for: durable shared cache tradeoffs, `cacheHandlers`, cache-key selection, nesting rules/nextjs, and deploy persistence limits.

- `cacheComponents`
  URL: `https://nextjs.org/docs/app/api-reference/config/next-config-js/cacheComponents`
  Use for: the two-flag enablement, the `runtime` export restriction, PPR default behavior, and the `<Activity>` navigation model.

- `partialPrefetching`
  URL: `https://nextjs.org/docs/app/api-reference/config/next-config-js/partialPrefetching`
  Use for: App Shell prefetching, the `cacheComponents` dependency, and per-segment `prefetch` overrides.

- Mutating Data
  URL: `https://nextjs.org/docs/app/getting-started/mutating-data`
  Use for: Server Function mutation flow and the mutation entry points.

- Forms
  URL: `https://nextjs.org/docs/app/guides/forms`
  Use for: Server Actions in forms, `FormData`, validation, pending states, optimistic updates, and `useActionState`.

- Server Actions guide
  URL: `https://nextjs.org/docs/app/guides/server-actions`
  Use for: sequential client dispatch, the single-response data-and-UI model, cache update choice, CSRF and body-size protections, and deployment rotation behavior.

- `use server`
  URL: `https://nextjs.org/docs/app/api-reference/directives/use-server`
  Use for: dedicated action files, inline Server Functions, and auth/authz expectations.

- `serverActions` config
  URL: `https://nextjs.org/docs/app/api-reference/config/next-config-js/serverActions`
  Use for: `experimental.serverActions.allowedOrigins`, wildcard and port matching, the no-`Origin` warning path, and `bodySizeLimit`.

- Route Handlers guide
  URL: `https://nextjs.org/docs/app/getting-started/route-handlers`
  Use for: default caching behavior, the Cache Components `GET` prerendering model, `use cache` helper placement, special metadata handlers, and route resolution.

- Route Handlers API
  URL: `https://nextjs.org/docs/app/api-reference/file-conventions/route`
  Use for: `route.ts`, HTTP method exports, Web Request/Response APIs, cookies/headers, promise-shaped dynamic params, `RouteContext`, CORS, webhooks, streaming, and non-UI responses.

- Route Segment Config
  URL: `https://nextjs.org/docs/app/api-reference/file-conventions/route-segment-config`
  Use for: the current option table, `runtime` and `preferredRegion` deprecations, the `ensureStatic` addition, and the v16 removal of `dynamic`, `dynamicParams`, `revalidate`, and `fetchCache` under `cacheComponents`.

- `ensureStatic`
  URL: `https://nextjs.org/docs/app/api-reference/file-conventions/route-segment-config/ensureStatic`
  Use for: `'auto' | 'shell' | 'prefetch' | 'navigation' | false`, layout inheritance, stricter-only child levels, parallel-slot agreement, and `generateStaticParams` requirements.

- `instant`
  URL: `https://nextjs.org/docs/app/api-reference/file-conventions/route-segment-config/instant`
  Use for: Instant Navigation validation levels, `instant = false` opt-outs, and the Navigation Inspector.

- `prefetch` segment config
  URL: `https://nextjs.org/docs/app/api-reference/file-conventions/route-segment-config/prefetch`
  Use for: per-segment `'partial'` and `'force-disabled'` overrides.

- `runtime`
  URL: `https://nextjs.org/docs/app/api-reference/file-conventions/route-segment-config/runtime`
  Use for: the Edge Runtime deprecation and the Cache Components prohibition on the `runtime` export.

- Proxy
  URL: `https://nextjs.org/docs/app/api-reference/file-conventions/proxy`
  Use for: `proxy.ts`, static matcher placement, negative matching for `_next/static` / `_next/image` / public assets, the `_next/data` exception, the Node.js runtime default, the missing `runtime` option, and Middleware-to-Proxy migration.

- Environment Variables
  URL: `https://nextjs.org/docs/app/guides/environment-variables`
  Use for: `.env*` loading, `NEXT_PUBLIC_`, runtime vs build-time env behavior, and `@next/env`.

- Redirecting
  URL: `https://nextjs.org/docs/app/guides/redirecting`
  Use for: redirect surfaces, Server Action redirects, `next.config.*` redirects, and pre-render redirect strategy.

- Data Security
  URL: `https://nextjs.org/docs/app/guides/data-security`
  Use for: DAL guidance, `server-only`, Server Action security, auth/authz inside actions, and return-value minimization.

- Authentication
  URL: `https://nextjs.org/docs/app/guides/authentication`
  Use for: multi-entry-point auth cautions, Server Action access, Proxy optimistic checks, and route protection patterns.

- Authentication with Cache Components
  URL: `https://nextjs.org/docs/app/guides/authentication-with-cache-components`
  Use for: reading sessions under Cache Components and caching session-derived data.

- Keeping pages static
  URL: `https://nextjs.org/docs/app/guides/keeping-pages-static`
  Use for: worked `ensureStatic` examples per level.

- Optimizing prefetching
  URL: `https://nextjs.org/docs/app/guides/optimizing-prefetching`
  Use for: App Shell versus per-link prefetches and deferring work to a later navigation stage.

- Adopting Partial Prefetching
  URL: `https://nextjs.org/docs/app/guides/adopting-partial-prefetching`
  Use for: incremental `prefetch = 'partial'` adoption and the migration order.

- Instant navigation
  URL: `https://nextjs.org/docs/app/guides/instant-navigation`
  Use for: Navigation Inspector workflow and Playwright regression testing with `@next/playwright`.

- Preserving UI state
  URL: `https://nextjs.org/docs/app/guides/preserving-ui-state`
  Use for: `<Activity>` state retention and which UI patterns reset on navigation.

- Migrating to Cache Components
  URL: `https://nextjs.org/docs/app/guides/migrating-to-cache-components`
  Use for: replacing legacy route segment configs and the runtime/edge removal steps.

- Upgrade with a coding agent
  URL: `https://nextjs.org/docs/app/guides/upgrading/agent-upgrade`
  Use for: `next upgrade --agent`, the versioned `AGENTS.md` block, and agent feedback settings.

- `connection`
  URL: `https://nextjs.org/docs/app/api-reference/functions/connection`
  Use for: waiting for a real user request and the explicit preference for `io()` under Cache Components.

- `io`
  URL: `https://nextjs.org/docs/app/api-reference/functions/io`
  Use for: excluding synchronous values from the static shell while staying cacheable and prefetchable.

- `navigation`
  URL: `https://nextjs.org/docs/app/api-reference/functions/navigation`
  Use for: deferring work past the App Shell and per-link prefetches.

- `prefetch` function
  URL: `https://nextjs.org/docs/app/api-reference/functions/prefetch`
  Use for: deferring work past the App Shell only.

- `cacheLife`
  URL: `https://nextjs.org/docs/app/api-reference/functions/cacheLife`
  Use for: profile values, the prerendering thresholds, and the client-cache stale rule.

- `cacheTag`
  URL: `https://nextjs.org/docs/app/api-reference/functions/cacheTag`
  Use for: tag limits per call and tag-length limits.

- `updateTag`
  URL: `https://nextjs.org/docs/app/api-reference/functions/updateTag`
  Use for: read-your-own-writes expiration from Server Actions.

- `revalidateTag`
  URL: `https://nextjs.org/docs/app/api-reference/functions/revalidateTag`
  Use for: the two-argument profile form, the deprecated single-argument form, and the Client Component / Proxy restriction.

- `refresh`
  URL: `https://nextjs.org/docs/app/api-reference/functions/refresh`
  Use for: refetching the current route's RSC payload from a Server Action.

- `catchError`
  URL: `https://nextjs.org/docs/app/api-reference/functions/catchError`
  Use for: component-level error boundaries that cooperate with `redirect()` and `notFound()`.

- `error.js`
  URL: `https://nextjs.org/docs/app/api-reference/file-conventions/error`
  Use for: segment error boundaries and the `retry()` recovery function.

- `root-params`
  URL: `https://nextjs.org/docs/app/api-reference/functions/next-root-params`
  Use for: reading root-level params such as `[lang]` from any Server Component and contributing them to `use cache` keys.

- `unstable_noStore`
  URL: `https://nextjs.org/docs/app/api-reference/functions/unstable_noStore`
  Use for: legacy maintenance only; current docs route new work to `io()` and `connection`.

- `authInterrupts`
  URL: `https://nextjs.org/docs/app/api-reference/config/next-config-js/authInterrupts`
  Use for: experimental `forbidden` / `unauthorized` enablement and production-risk review.

## Drift Watchlist

Re-check official docs before relying on these behaviors:

- Cache Components recommendation status, the `cacheComponents` + `partialPrefetching` pair, and the planned removal of both flags.
- `use cache`, `use cache: private`, `use cache: remote`, `cacheLife`, `cacheTag`, `updateTag`, `revalidateTag`, `refresh`, and `io()` semantics.
- Route Segment Config availability, including `ensureStatic`, `instant`, `prefetch`, the `runtime` and `preferredRegion` deprecations, and v16 removals under `cacheComponents`.
- Route Handler `GET` caching/prerender behavior and `use cache` helper placement.
- Proxy runtime/platform support, the missing `runtime` option, static matcher behavior, the `_next/data` exception, and Middleware migration guidance.
- Server Action dispatch order, single-response re-render behavior, origin/body-size configuration, and action ID rotation.
- Experimental `authInterrupts`, `forbidden`, and `unauthorized` stability.

## Interpretation Rules

- Prefer latest official docs over stale community habits.
- If a newer Next.js release changes caching, prerendering, Proxy, Route Handler, or Server Action behavior, update the relevant rule file rather than bloating `stacks/nextjs/core.md`.
- When local repo conventions exceed the docs, label them as local conventions in reviews and change reports.
- Treat this file as a doc map, not a replacement for rereading official docs on version-sensitive work.

## Sources

> Checked 2026-11-04. Version baseline confirmed against the npm `latest` tag for `next` (16.4.5) and the release feed; the page list and paths come from `https://nextjs.org/docs/llms.txt`, and each "Use for" scope was read on its canonical page.

| Claim | Source |
|---|---|
| The version baseline and release dates | `https://github.com/vercel/next.js/releases` and `https://www.npmjs.com/package/next` |
| The official Next.js surfaces and their "Use for" scope in "Core Sources" above | the canonical `nextjs.org/docs/...` URL listed with each entry |
| The drift-sensitive behaviors listed in "Drift Watchlist" above | those same canonical URLs plus `references/official/nextjs/current-docs-2026-11-04.md` |
