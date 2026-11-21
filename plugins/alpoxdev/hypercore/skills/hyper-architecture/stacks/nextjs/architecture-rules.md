# Architecture Rules Reference

> Consolidated official-first rule set for Next.js projects, with App Router as the default mode.

Brownfield adoption rule: untouched legacy `pages/` code is not an automatic failure. Safety, boundary, auth, and data-leak issues still block immediately, especially in touched code.

---

## Project Modes

| Mode | Indicators | Enforcement |
|---|---|---|
| App Router | `app/` or `src/app/` | Full skill applies |
| Shared Next.js | `pages/` only | Apply shared platform, env, boundary, and safety rules/nextjs only |
| Mixed | both `app/` and `pages/` | Apply App Router rules/nextjs to touched `app/` code; avoid broad migration unless requested |

---

## Current Official Baselines

Source priority starts with `references/official/nextjs/current-docs-2026-11-04.md`, then `references/official/nextjs/nextjs-docs.md` for the broader doc map. In the latest checked Next.js 16 docs the stable baseline is 16.4.5 (16.4.0 on 2026-10-06, 16.3.0 on 2026-08-03); 16.5 exists only on canary.

- Server Components are the default in App Router; add `'use client'` only at client entry points that need interactivity, browser APIs, or client hooks.
- In modern App Router docs, `fetch` requests are not cached by default, while routes may still be prerendered and HTML cached. Cache intent must be explicit.
- Since Next.js 16.4 the docs recommend Cache Components as the best choice for every App Router app, and new `create-next-app` apps ship with it enabled. Adoption in an existing app still needs an explicit migration reason.
- Cache Components is enabled with `cacheComponents: true` plus `partialPrefetching: true`. Leaving `partialPrefetching` unset logs a warning, and `partialPrefetching` without `cacheComponents` fails config validation.
- `cacheComponents` is the unified v16 switch for PPR, `useCache`, and `dynamicIO`; experimental PPR flags and the `experimental_ppr` segment option are removed.
- With `cacheComponents`, `dynamic`, `dynamicParams`, `revalidate`, and `fetchCache` route segment config options are removed. Remaining options are `runtime` (`'edge'` deprecated), `preferredRegion` (deprecated), `maxDuration`, plus `ensureStatic` for pages and layouts. `dynamicParams` stays available outside Cache Components.
- `use cache` cannot directly read request-time APIs; pass serializable values in. `use cache: private` may read them, deduplicates within one request, keeps a client-memory copy for its `stale` window, and stores nothing server-side across requests. `use cache: remote` is for justified durable shared cache and cannot nest with `use cache: private`.
- Pair every `use cache` scope with `cacheLife`; without one the implicit `default` profile applies.
- With Cache Components, prefer `io()` over `connection()`: `io()` leaves the static shell while staying cacheable and prefetchable, and `connection()` is for work that must wait for a real user request. `unstable_noStore` is legacy-only.
- `navigation()` and `prefetch()` (v16.4) defer expensive work to a later navigation stage; `ensureStatic` (v16.4) requires a static shell, prefetch, or navigation output.
- Edge Runtime is deprecated: remove the `runtime` export, and under Cache Components remove `runtime = 'nodejs'` as well.
- Server Actions are Server Functions invoked from UI/forms/events; treat each one as a reachable POST surface and re-check auth/authz inside it.
- Next.js dispatches Server Actions one at a time per client, so client-side `Promise.all` does not parallelize them. `updateTag`, `revalidatePath`, `refresh`, cookie mutation, and `redirect` re-render the current route in the same response; `revalidateTag` with a stale-while-revalidate profile does not.
- Official data-security guidance recommends a server-only DAL, authorization checks, and minimal DTOs for sensitive data. Server Components may query an ORM/database directly when the boundary is safe, but local architecture can still require a DAL for non-trivial logic.
- `updateTag` is Server Action-only for read-your-own-writes; `revalidateTag` works in Server Functions and Route Handlers and should use a second argument such as `'max'` for stale-while-revalidate. The single-argument form is deprecated. Neither runs in Client Components or Proxy.
- Route Handlers are for HTTP-native endpoints and support standard Web `Request`/`Response` APIs plus method exports. With Cache Components, `GET` handlers follow the same prerendering model as UI routes and `use cache` must live in a helper, not directly in the handler body.
- The old `middleware` convention is deprecated in favor of `proxy.ts`; Proxy is a last-resort network-boundary tool, defaults to Node.js runtime, rejects a `runtime` export, and must use static, narrow matchers.
- `catchError` from `next/error` (stable in v16.3) gives component-level error boundaries that coexist with `redirect()` and `notFound()`.
- With Cache Components, navigation keeps state through React `<Activity mode="hidden">`: state survives, effects are cleaned up while hidden and recreated when visible.
- Drizzle schema/config/migrations and connection lifecycle are independent DB architecture concerns; keep them in `rules/nextjs/db.md`, not hidden inside generic services guidance. Pin `drizzle-orm >= 0.45.2` and run `drizzle-kit check` when several branches touch the schema.

---

## Core Principles

- Follow the official Next.js docs before local taste.
- Default to Server Components and add `'use client'` only at interactive leaves.
- Prefer Server Actions for internal UI mutations and forms.
- Keep privileged data access in server-only modules or a DAL.
- Make cache behavior intentional, not accidental.
- Treat every Server Action as externally reachable and re-authorize inside it.
- Use Route Handlers for HTTP-native concerns, not default internal mutations.
- Use Proxy only when redirects, rewrites, headers, or render-time logic are insufficient.

---

## Layer Taxonomy

| Layer | Classification | Default responsibility |
|---|---|---|
| `app/` or `src/app/` route segments | Official routing surface | UI routes, layouts, special files, segment-local private folders |
| Server Components | Official rendering/data surface | Initial reads, server-rendered UI, direct server-only DAL/ORM calls when safe |
| Client Components and hooks | Official client boundary + Hypercore convention | Interactivity, browser APIs, UI state, client orchestration only |
| Server Actions | Official mutation surface | UI-originated writes with validation, auth/authz, DTO return shaping, freshness |
| Route Handlers | Official HTTP endpoint surface | Webhooks, feeds, CORS, streams, public machine-readable responses |
| `src/modules/<domain>/<feature>/` | Hypercore local convention | Domain feature orchestration, reusable actions/queries/schemas/DTOs |
| `src/services/<domain>/` | Hypercore local convention | Domain service entrypoints in repos that already prefer service naming |
| `src/db/<area>/` | Hypercore local convention | Drizzle schema, client, repositories, migrations, transaction helpers |
| `src/server/<area>/` | Hypercore local convention | Request/session/server runtime utilities |
| `src/integrations/<provider>/` | Hypercore local convention | External SDK clients, webhook schemas, provider-specific mapping |
| `src/config/<area>/` | Hypercore local convention | Env/runtime config, feature flags, deployment config |

Never report `src/modules`, `src/services`, `src/db`, `src/server`, `src/integrations`, or `src/config` as official Next.js requirements. They are Hypercore local folder conventions used to make ownership and runtime boundaries visible.

---

## Forbidden

| Category | Forbidden |
|---|---|
| Routing | `page.tsx` and `route.ts` at the same route segment |
| Client Boundary | Broad top-level `'use client'` without real interaction need |
| Secrets | Private env, DB clients, or server-only modules imported into Client Components |
| Hooks | Client hooks importing Drizzle schema/client, DAL, private env, request APIs, or provider secrets |
| Data Safety | Passing broad raw records from Server Components into Client Components |
| Services | Returning raw DB rows or provider payloads across client-visible boundaries |
| Drizzle | Running migrations from request lifecycle code or hiding schema/config drift |
| Cache Intent | Relying on implicit caching or dynamic rendering without understanding why |
| Cache Components | Reading runtime request APIs inside a `use cache` scope instead of passing serializable inputs; `use cache: private` is the supported escape hatch, but only when refactoring the runtime read out is impractical |
| Cache Components | Adding `unstable_noStore` for new dynamic work instead of `io()` or `connection()` |
| Cache Components | Shipping `cacheComponents: true` without `partialPrefetching` in a new or migrated app |
| Cache Components | Removing content from the static shell with `connection()` when `io()` would do, because `connection()` blocks prefetches |
| Server Actions | Trusting client input, skipping auth/authz, or returning raw internal objects |
| Server Actions | Parallelizing Server Actions from the client with `Promise.all`; dispatch is sequential per client |
| Server Actions | Leaving `NEXT_SERVER_ACTIONS_ENCRYPTION_KEY` unstable across instances in a multi-instance deployment |
| Freshness | Redirecting before necessary revalidation/tag update or omitting freshness entirely |
| Freshness | Assuming `revalidateTag` with a stale-while-revalidate profile re-renders the current route in the action response |
| Route Handlers | Using `route.ts` as default internal RPC when a Server Action or Server Component is right |
| Route Handlers | Using `NextResponse.next()` inside a Route Handler |
| Proxy | Adding `proxy.ts` when `next.config.*` or render-time logic is enough |
| Env Setup | Expecting `.env*` files to load from `src/` |

---

## Required

| Category | Required |
|---|---|
| Validation | Confirm Next.js mode before editing |
| Routing | Place special files in valid route segments |
| Boundaries | Keep Client Components narrow and props serializable |
| Safety | Use `server-only` or an equally clear server boundary for privileged modules |
| Services | Validate, authorize, and shape DTOs in Server Actions or delegated server-only services |
| Hooks | Keep hooks as client orchestration only; do not cross server/data layers |
| DB | Keep Drizzle client/schema/repositories server-only and make `drizzle.config.ts` schema/out explicit |
| Cache | State whether data/UI is uncached, cached with `use cache`, remotely/privately cached, tag-revalidated, path-revalidated, or refreshed |
| Cache | Pair every `use cache` scope with an explicit `cacheLife` profile or inline value |
| Cache | Enable `cacheComponents` and `partialPrefetching` together; `partialPrefetching` alone fails config validation |
| Prerendering | Use `io()` to drop synchronous values from the static shell; reserve `connection()` for work that must wait for a real request |
| Prerendering | Use `navigation()`, `prefetch()`, or `ensureStatic` deliberately when a route needs staged or guaranteed static output |
| Auth | Re-check authentication and authorization inside each Server Action or delegated server-only layer |
| Platform | Keep env handling, route segment config, Proxy, and Next config explicit |
| Platform | Remove `runtime` exports (including `runtime = 'nodejs'` under Cache Components) rather than selecting a runtime |
| Platform | Verify `experimental.serverActions.allowedOrigins` and `bodySizeLimit` for proxied or upload-heavy deployments |
| Errors | Use `catchError` for component-level recovery and `retry()` for re-fetching failed server work |
| Reporting | Label repo-local conventions as conventions, not framework law |
| Shared folders | New touched shared code under `src/modules`, `src/lib`, `src/services`, `src/db`, `src/server`, `src/integrations`, `src/config`, `lib`, or `services` uses nested domain/provider grouping unless an explicit exception is recorded |

---

## Decision Order

1. Is this an App Router surface, legacy Pages Router surface, or mixed repo?
2. Is this code server-only, client-interactive, shared, cached, or request-time dynamic?
3. Does this need HTML/UI rendering, an internal UI mutation, or an HTTP-native endpoint?
4. Should the read be uncached, cached with `use cache`, revalidated by tag/path, or refreshed after mutation?
5. Which navigation stage should carry the work: App Shell, per-link prefetch, navigation, or a real request?
6. Does the change affect deployment-sensitive config such as env, Proxy, runtime, route segment config, or Server Action origins?

Default surface order:

1. Server Components for initial reads and server-rendered UI
2. Server Actions for internal UI writes and forms
3. Route Handlers for HTTP-native endpoints
4. Proxy only when pre-render network-boundary interception is truly required

---

## Rule Files

- `rules/nextjs/project-structure.md` — includes no direct leaf files under touched `src/lib` / `src/services` shared roots
- `rules/nextjs/services.md`
- `rules/nextjs/hooks.md`
- `rules/nextjs/db.md`
- `rules/nextjs/routes.md`
- `rules/nextjs/execution-model.md`
- `rules/nextjs/data-fetching.md`
- `rules/nextjs/server-actions.md`
- `rules/nextjs/route-handlers.md`
- `rules/nextjs/platform.md`
- `references/official/nextjs/current-docs-2026-11-04.md`
- `references/official/nextjs/nextjs-docs.md`
- `references/official/nextjs/drizzle-docs.md`

Read the smallest set that covers the active change, but always start here.
