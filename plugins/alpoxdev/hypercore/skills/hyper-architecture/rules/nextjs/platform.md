# Platform and Environment

> `next.config.*`, env handling, route segment config, Proxy, and deployment-sensitive setup.

---

## Environment Variables

- `.env*` files belong at the project root, not inside `src/`.
- Non-`NEXT_PUBLIC_` env vars are server-only.
- `NEXT_PUBLIC_` values are inlined at build time into browser bundles.
- If the client needs runtime values, expose them through a server path instead of pretending they are runtime-public env vars.
- If code outside the Next runtime needs env loading, use `@next/env`.

## Runtime Env Rule

Server code can read runtime env values during dynamic rendering. Do not confuse runtime server env with build-time inlined client env.

## Cache Components and Route Segment Config

- Cache Components is the recommended default since Next.js 16.4. It is enabled with two flags: `cacheComponents: true` and `partialPrefetching: true`. `partialPrefetching` without `cacheComponents` throws at config validation, and leaving `partialPrefetching` unset logs a warning.
- `cacheComponents` is the Next.js 16 unified switch for Cache Components, PPR, `useCache`, and `dynamicIO` behavior.
- When `cacheComponents` is enabled, v16 removes `dynamic`, `dynamicParams`, `revalidate`, and `fetchCache` route segment options; use the Cache Components model instead. `dynamicParams` stays valid in apps that have not enabled Cache Components.
- Current route segment options:

| Option | Type | Default |
|---|---|---|
| `dynamicParams` | `boolean` | `true` |
| `runtime` | `'nodejs' \| 'edge' (deprecated)` | `'nodejs'` |
| `preferredRegion` | `'auto' \| 'global' \| 'home' \| string \| string[] (deprecated)` | `'auto'` |
| `maxDuration` | `number` | Set by deployment platform |
| `ensureStatic` (Cache Components only) | `'auto' \| 'shell' \| 'prefetch' \| 'navigation' \| false` | `'auto'` |

- `ensureStatic` sets the static requirement for the App Shell, per-link prefetch, or complete route. A layout applies its level to every route below it, a child segment may only be stricter, and parallel slots rendered together must agree. `'navigation'` on a dynamic route requires `generateStaticParams`.
- `instant` (v16.3 stable) configures Instant Navigation validation, and `prefetch` (v16.3 stable) configures per-segment prefetching with `'partial'` and `'force-disabled'`. Both require Cache Components and cannot be exported from a Client Component.
- `runtime` defaults to `'nodejs'` and `'edge'` is deprecated. Remove the `runtime` export from route files, including `runtime: 'edge'`; with Cache Components, remove `runtime = 'nodejs'` as well, because Cache Components requires the Node.js runtime and rejects the segment config.
- Deployment platforms may use `maxDuration`; document changes that alter execution limits.

## Proxy

- `proxy.ts` belongs at the project root or `src/` root, next to `app` or `pages`.
- Proxy runs before routes are rendered and represents a network boundary in front of app render code.
- Prefer `redirects`, `rewrites`, headers, cookies, or render-time logic before reaching for Proxy.
- Proxy should have an explicit matcher and narrow scope; without a matcher it runs on every request, including `_next/static`, `_next/image`, and public assets.
- Matcher values must be static constants so Next.js can analyze them at build time.
- Do not rely on shared modules or globals inside Proxy.
- Exclude API routes, metadata, static surfaces, image optimization, and public assets from broad matchers when they should bypass Proxy.
- A negative matcher does not stop Proxy from running for `_next/data` requests.
- `revalidateTag` cannot be called from Proxy.
- Server Functions are POST requests to the route where they are used; matcher changes can silently remove Proxy coverage, so auth/authz must still live inside the Server Function or DAL.

## Important Proxy Note

The old `middleware` file convention is deprecated and has been renamed to `proxy`. Do not add fresh `middleware.ts` files for new work. Use the official `npx @next/codemod@canary middleware-to-proxy .` codemod for migrations when needed. Proxy defaults to the Node.js runtime and rejects a `runtime` config option; setting one throws.

## `next.config.*`

Keep config changes explicit and intentional. Review carefully when changing:

- `typedRoutes`
- `cacheComponents` and `partialPrefetching` (enable together)
- `serverActions` under `experimental`: `allowedOrigins` and `bodySizeLimit`
- `cacheLife` and `cacheHandlers`
- `experimental.authInterrupts` and `experimental.instantInsights`
- route segment config strategy, especially removed v16 options under `cacheComponents`
- redirect and rewrite rules/nextjs
- output and deployment settings

## Server Action Deployment Settings

- `experimental.serverActions.allowedOrigins` compares the `Origin` host against `x-forwarded-host` or `host`. `*` matches one label and `**` matches one or more; ports must be written out, and partial replacement is not supported.
- A request with no `Origin` header at all is allowed through with a warning rather than rejected.
- `experimental.serverActions.bodySizeLimit` defaults to 1MB and applies to the raw request body, including multipart overhead.
- Action IDs rotate at most every 14 days, so keep `NEXT_SERVER_ACTIONS_ENCRYPTION_KEY` stable across instances and prefer rolling deploys.

## Recommended Platform Checks

- Consider `typedRoutes: true` in TypeScript App Router projects where route-safety matters.
- In multi-proxy or reverse-proxy deployments, verify whether Server Action origin configuration is needed.
- Keep deployment-sensitive settings documented in the PR or final report when changed.

## Review Checklist

- `.env*` handling matches Next.js behavior
- Client code sees only `NEXT_PUBLIC_` env vars
- Cache Components and removed v16 route segment config options are not mixed accidentally
- `cacheComponents` and `partialPrefetching` are enabled together
- `runtime` exports are removed rather than set
- Proxy is truly justified, statically matched, and narrowly scoped
- Server Action origin, body-size, and encryption-key settings are deliberate
- `next.config.*` changes are intentional and explained

## Sources

> Checked 2026-11-04 against `https://nextjs.org/docs/app/api-reference/file-conventions/route-segment-config`, `https://nextjs.org/docs/app/api-reference/file-conventions/route-segment-config/ensureStatic`, `https://nextjs.org/docs/app/api-reference/file-conventions/route-segment-config/instant`, `https://nextjs.org/docs/app/api-reference/file-conventions/route-segment-config/prefetch`, `https://nextjs.org/docs/app/api-reference/file-conventions/route-segment-config/runtime`, `https://nextjs.org/docs/app/api-reference/config/next-config-js/cacheComponents`, `https://nextjs.org/docs/app/api-reference/config/next-config-js/partialPrefetching`, `https://nextjs.org/docs/app/api-reference/config/next-config-js/serverActions`, `https://nextjs.org/docs/app/api-reference/file-conventions/proxy`, `https://nextjs.org/docs/app/guides/server-actions`, and `https://nextjs.org/docs/app/guides/environment-variables`. The dated snapshot is `references/official/nextjs/current-docs-2026-11-04.md`.
