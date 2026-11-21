# Route Handlers

> When `route.ts` is the right surface and when it is not.

---

## Use Route Handlers For

- webhooks
- feeds
- CORS-sensitive endpoints
- machine-readable public endpoints
- non-UI content such as XML, JSON, or streams
- HTTP-native integrations that need method-level handling, headers, status codes, or raw body access

## Do Not Default To Route Handlers For

- normal internal form mutations that fit Server Actions
- internal UI data reads that can be done in Server Components
- forwarding behavior that belongs in Proxy

If a mutation originates from app UI, assume Server Action first and justify `route.ts` only when HTTP semantics are the actual requirement.

## Current Facts

- Route Handlers are available in the App Router.
- A `route.ts` file supports standard HTTP method exports: `GET`, `POST`, `PUT`, `PATCH`, `DELETE`, `HEAD`, and `OPTIONS`.
- Route Handlers use Web `Request` / `Response` APIs, with `NextRequest` / `NextResponse` when Next.js helpers are needed.
- Dynamic segment `params` are promise-shaped in current App Router examples; await them before use or use the global `RouteContext<'/route/[id]'>` helper for typed params.
- Route Handlers share route segment config, but with `cacheComponents` enabled the v16 removed options (`dynamic`, `dynamicParams`, `revalidate`, `fetchCache`) must not be used, and the `runtime` export must be removed as well.
- Route Handlers are not cached by default in the previous model; only `GET` can opt into caching. Other methods are not cached even when colocated with cached `GET`.
- With Cache Components enabled, `GET` Route Handlers follow the same prerendering model as UI routes: request-time by default, prerenderable when no uncached/runtime data is accessed, and cacheable through helper functions marked `use cache`.

## Hard Rules

| Check | Rule |
|---|---|
| `route.ts` and `page.tsx` placed in the same segment | BLOCKED |
| Route Handler used as default internal RPC for a UI-only flow | BLOCKED unless HTTP semantics are required |
| `NextResponse.next()` used inside a Route Handler | BLOCKED. That behavior belongs in Proxy |
| Route Handler caching assumed from old defaults without checking current behavior | BLOCKED |
| `use cache` placed directly inside a Route Handler body instead of an extracted helper | BLOCKED |
| `params` used synchronously instead of awaited in current App Router Route Handler examples | BLOCKED |
| Custom Route Handler duplicates built-in metadata files such as sitemap, robots, icons, or Open Graph images without need | WARNING/BLOCKED by risk |

## Cache and Freshness

- In the previous caching model, cache `GET` handlers only with explicit route config such as `dynamic = 'force-static'` or another documented strategy.
- With Cache Components enabled, `GET` handlers follow the UI-route prerendering model; put `use cache` in helper functions and use `cacheLife` / `cacheTag` where appropriate.
- For freshness, state whether you use `cacheTag`, `revalidateTag(tag, 'max')`, `revalidateTag(tag, { expire: 0 })` for webhook-like immediate expiry, `revalidatePath`, or another explicit strategy.
- `updateTag` and `refresh` are Server Action-only, so a webhook Route Handler cannot use them. Use `revalidateTag(tag, { expire: 0 })` when the invalidation must be immediate.
- `revalidateTag` cannot be called from Proxy, so cache invalidation that a webhook needs has to run in the handler itself.
- Do not rely on undocumented `GET` caching defaults for correctness-critical endpoints.

## Decision Rule

Choose:

1. Server Component for server-rendered UI reads
2. Server Action for internal UI mutations and forms
3. Route Handler only when the surface is genuinely HTTP-native
4. Proxy only for pre-route request boundary behavior

## Review Checklist

- The endpoint really needs HTTP semantics
- No `page.tsx` conflict exists
- Method exports and request/response handling are explicit
- Current caching behavior is understood and documented
- Proxy-specific behavior is not leaking into the Route Handler

## Sources

> Checked 2026-11-04 against `https://nextjs.org/docs/app/getting-started/route-handlers`, `https://nextjs.org/docs/app/api-reference/file-conventions/route`, `https://nextjs.org/docs/app/api-reference/functions/revalidateTag`, and `https://nextjs.org/docs/app/api-reference/functions/updateTag`. The dated snapshot is `references/official/nextjs/current-docs-2026-11-04.md`.
