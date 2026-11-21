# Data Fetching and Caching

> Server-first reads, streaming, Cache Components, cache intent, and freshness rules.

---

## Preferred Read Path

- Fetch initial page data in Server Components when possible.
- Fetch close to the component that needs the data.
- Use parallel fetching for independent reads.
- Stream with `loading.tsx` or `<Suspense>` instead of blocking the whole route unnecessarily.
- Keep privileged reads in a server-only helper or DAL when the pattern repeats.

## Current Runtime Facts

- In current App Router docs, `fetch` requests are not cached by default. Caching is opt-in through `cache: 'force-cache'` or a `use cache` scope.
- A route containing `fetch` can still be prerendered and have its HTML cached, so dynamic/static intent must be explicit.
- `cookies()`, `headers()`, `searchParams`, `params`, `connection()`, and other request-time APIs make the affected work runtime-dependent.
- With Cache Components enabled, uncached runtime data must be isolated behind a `<Suspense>` boundary, kept out of the static shell with `io()`, or explicitly cached with `use cache` where safe.
- `io()` is the standard way to drop a synchronous value such as `new Date()`, `Math.random()`, or a synchronous driver read out of the static shell. It suspends during prerendering, resolves immediately in a real request, inside cached scopes, in the browser, and without Cache Components, and the code after it stays cacheable and prefetchable.
- `connection()` waits for a real user request, so it also blocks prefetches. Reach for it only when rendering must wait for that request; use `io()` otherwise. `unstable_noStore` is legacy-only.
- Identical reads may be memoized in a request tree, but request memoization is not a persistence/cache policy.

## Cache Components and `use cache`

Cache Components is the recommended default for App Router work since Next.js 16.4; new `create-next-app` apps already enable it. Turning it on in an existing app is a deliberate migration, not a drive-by change.

1. Enable both flags in `next.config.*`: `cacheComponents: true` and `partialPrefetching: true`. Leaving `partialPrefetching` unset logs a warning, and setting it without `cacheComponents` fails config validation.
2. Remove `runtime` exports from route files, including `runtime = 'nodejs'`.
3. Mark cacheable pages, components, or async functions with `use cache`.
4. Keep `use cache` inputs and return values serializable according to the relevant React/Next.js serialization rules.
5. Do not read `cookies()`, `headers()`, `searchParams`, or other request-time APIs inside a normal cached scope; read them outside and pass serializable values as arguments.
6. Pair every `use cache` scope with `cacheLife`. Without one, the implicit `default` profile applies and the lifetime is invisible at the call site.
7. Use `cacheTag` for invalidation groups.
8. Use `use cache: remote` only when durable shared cache is worth the storage, latency, and platform cost. Remote entries do not survive a deploy because the cache key includes the build identity.
9. Use `use cache: private` when a cached function must read runtime APIs and refactoring the read outward is impractical. It deduplicates matching calls within one request, keeps a client-memory copy for its `stale` window, and stores nothing in a server cache across requests. It cannot nest with `use cache: remote`.

## Prerendering Thresholds

`cacheLife` values decide where a cached result can be delivered:

| Lifetime | Delivered from |
|---|---|
| `revalidate: 0`, or `expire` under 5 minutes | Request time only; excluded from prerenders as a dynamic hole |
| `stale` under 30 seconds | Excluded from prerenders, because a prefetch would expire before the click |
| `stale` from 30 seconds to under 5 minutes | Included in prerenders but excluded from the App Shell |
| `stale` of 5 minutes or more | Eligible for the static shell and per-link prefetches |

The client enforces a 30-second minimum on `stale`. Calling `revalidateTag`, `revalidatePath`, `updateTag`, or `refresh` from a Server Action clears the whole client cache immediately, bypassing that window.

## Navigation Stages

With Partial Prefetching, a route's server output is produced in stages: the App Shell for a default `<Link>`, an optional per-link prefetch for `<Link prefetch={true}>`, and the navigation itself.

| Tool | Keeps work out of | Requires |
|---|---|---|
| `io()` | The static shell (still cacheable and prefetchable) | `<Suspense>` around the suspending subtree |
| `prefetch()` | The App Shell | Cache Components; Partial Prefetching for any effect |
| `navigation()` | The App Shell and per-link prefetches | Cache Components; Partial Prefetching for any effect |
| `connection()` | Prerendering and prefetching entirely | A real request to resolve |
| `ensureStatic = 'shell' / 'prefetch' / 'navigation'` | Enforces that stage to be static at build time | Cache Components; `generateStaticParams` for `'navigation'` on dynamic routes |

`prefetch()` and `navigation()` throw inside `use cache`, `use cache: private`, `after()`, `generateStaticParams`, and Client Components. A page or layout that also exports the `prefetch` segment config must import the function under another name.

## Cache and Freshness Rules

| Check | Rule |
|---|---|
| Cache behavior is not understood or not documented in the change | BLOCKED |
| Dynamic rendering is triggered accidentally by request-time APIs | BLOCKED |
| `fetch` caching assumes pre-Next.js-16 defaults | BLOCKED |
| `cacheComponents` is enabled but uncached data lacks `use cache`, `io()`, `loading.tsx`, or `<Suspense>` intent | BLOCKED |
| `cacheComponents` is enabled without `partialPrefetching` | BLOCKED |
| A `use cache` scope has no `cacheLife` and the caller cannot state the effective lifetime | BLOCKED |
| `connection()` is used where `io()` would keep the output cacheable and prefetchable | WARNING. `connection()` blocks prefetches |
| `use cache: remote` is used without a cost, durability, or hit-rate justification | BLOCKED |
| `use cache: private` is used without a runtime-read reason, or is nested with `use cache: remote` | BLOCKED |
| New code uses `unstable_noStore` instead of `io()` or `connection()` | BLOCKED unless maintaining legacy code |
| Server read belongs in repeated privileged logic but lives directly in page code | WARNING. Prefer DAL or server-only helper |

## Freshness After Mutations

After a mutation, the UI must have an explicit freshness path:

- `updateTag` for Server Action read-your-own-writes scenarios; the next read, including the re-render in the action's response, waits for fresh data
- `revalidateTag(tag, 'max')` for stale-while-revalidate tag refresh from Server Functions or Route Handlers; avoid the deprecated single-argument form, and use `{ expire: 0 }` when the invalidation comes from a webhook or Route Handler that cannot call `updateTag`
- `revalidatePath` for path-based invalidation
- `refresh` from `next/cache` in a Server Action when the current client router should refetch without tag invalidation
- redirect after freshness work, or another clearly explained strategy

`updateTag`, `revalidatePath`, `refresh`, cookie mutation, and `redirect` re-render the current route inside the same response. `revalidateTag` with a stale-while-revalidate profile does not, so the page picks up the change on a later read.

If `redirect()` is used, perform needed cache invalidation first because code after `redirect()` will not run.

## Streaming Guidance

Use:

- `loading.tsx` for segment-level loading states
- `<Suspense>` for granular streaming near slow or dynamic subtrees
- `io()` when a synchronous read must leave the static shell but should stay cacheable
- `connection()` when a subtree intentionally waits for an incoming request
- promise passing plus React `use()` only when it improves structure and keeps boundaries clear

## Official-First Decision Rule

Prefer:

1. Server Component reads for initial data
2. `use cache` / `cacheTag` / `cacheLife` when data or UI can be safely reused
3. server-only helper or DAL for privileged reads
4. Client-side fetching only for client-driven refresh, polling, or browser-only state

## Review Checklist

- Initial reads happen on the server unless there is a real client-only reason
- Cache Components, `fetch`, and route prerendering assumptions are current-docs compatible
- `cacheComponents` and `partialPrefetching` are enabled together
- Every `use cache` scope states its lifetime
- The chosen navigation stage matches how expensive the work is
- Dynamic rendering triggers are intentional
- Suspense or `loading.tsx` is placed close enough to blocking work
- Mutation freshness is explicit and matches the re-render behavior

## Sources

> Checked 2026-11-04 against `https://nextjs.org/docs/app/getting-started/caching`, `https://nextjs.org/docs/app/api-reference/functions/cacheLife`, `https://nextjs.org/docs/app/api-reference/functions/io`, `https://nextjs.org/docs/app/api-reference/functions/connection`, `https://nextjs.org/docs/app/api-reference/functions/prefetch`, `https://nextjs.org/docs/app/api-reference/functions/navigation`, `https://nextjs.org/docs/app/api-reference/file-conventions/route-segment-config/ensureStatic`, `https://nextjs.org/docs/app/api-reference/directives/use-cache-private`, and `https://nextjs.org/docs/app/api-reference/directives/use-cache-remote`. The dated snapshot is `references/official/nextjs/current-docs-2026-11-04.md`.
