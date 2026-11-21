# Route Structure

> Hono route composition rules/hono

---
## Stable Hono 4.13 Baseline

Official Hono routing is registration-ordered. `route()` copies the child app's registered routes into the parent at the call site; grouping order can therefore change behavior. `basePath()` prefixes one app, while the Mount middleware adapts another framework and is not a substitute for typed Hono sub-app composition. `app.mount()` is deprecated in v4 and removed in v5.

- Chain route definitions and `route()` calls when their inferred type feeds `AppType`, `testClient`, or `hc`.
- Register broad parameter, wildcard, fallback, and not-found behavior after specific routes.
- Decide trailing-slash behavior explicitly: Hono strict mode defaults to `true`, and `getPath()` cannot be combined with `strict: false`.
- Keep host-based routing and custom `getPath()` at the app/platform boundary.
- Migrate `app.mount('/prefix', handler)` to `app.all('/prefix/*', mount(handler))` with `mount` from `hono/mount`. The mounted app is called as `handler(request, c.env, c.executionCtx)` and receives a request without the matched prefix unless `optionHandler` or `replaceRequest` overrides it.
- `QUERY` is a first-class method: `app.query()` registers it, and `createRoute({ method: 'query' })` is available in `@hono/zod-openapi` 1.6.0 and later. A QUERY route that returns a cached response must account for the revised cache key.
- Turning on `methodNotAllowed({ app })` changes the contract: a matching path with an unsupported method returns `405` with `Allow` instead of `404`. Update RPC status unions and OpenAPI responses in the same change.
- Test mount prefixes and order after moving a sub-app; visual file layout is not proof of equivalent dispatch.

## Preferred Small Structure

```text
src/
├── app.ts
├── index.ts
├── routes/
│   ├── index.ts
│   ├── health.ts
│   └── users/
│       ├── index.ts
│       ├── handlers.ts
│       ├── schemas.ts
│       └── service.ts
```

## Preferred Large Structure

```text
src/routes/
├── index.ts
├── health.ts
├── users/
│   ├── index.ts
│   ├── routes.ts
│   ├── handlers.ts
│   ├── schemas.ts
│   ├── service.ts
│   └── tests/
└── billing/
    ├── index.ts
    ├── routes.ts
    ├── handlers.ts
    ├── schemas.ts
    ├── middleware.ts
    └── service.ts
```

`routes/index.ts` or `app.ts` remains the only mount table. Feature folders own their local route definitions, handlers, schemas, and feature-only middleware.

## Rules

- `app.ts` owns root app composition
- `routes/index.ts` or `app.ts` is the single obvious mount table
- Prefer sub-apps mounted with `app.route('/users', usersApp)`
- Use a route folder when a feature needs more than one file
- Single-file routes are acceptable for tiny operational endpoints
- Split a route into a folder when it has two or more handlers, any request schema, feature middleware, OpenAPI metadata, or service orchestration
- Keep `basePath()` and API version prefixes at the composition boundary
- Use `app.route()` for Hono sub-apps and the Mount middleware for other frameworks; never add `app.mount()` in new code
- Add a `methodNotAllowed({ app })` middleware only when the app deliberately answers 405, and then update every documented and typed 404 contract
- Do not import database clients, Drizzle schema tables, ORM drivers, or migration helpers from route modules; use services/repositories instead
- Do not import one feature route module from another feature route module
- Keep fallback and catch-all routes last because Hono dispatch follows registration order

## Mounting Pattern

```ts
import { createApp } from '@/lib/create-app'
import { healthApp } from '@/routes/health'
import { usersApp } from '@/routes/users'

export const app = createApp()
  .route('/health', healthApp)
  .route('/users', usersApp)
```

## Scale-Up Pattern

```ts
// routes/users/index.ts
import { createApp } from '@/lib/create-app'

import { createUserHandlers, listUserHandlers } from './handlers'

export const usersApp = createApp()
  .get('/', ...listUserHandlers)
  .post('/', ...createUserHandlers)
```

```ts
// routes/index.ts
import { usersApp } from './users'
import { billingApp } from './billing'

export const routesApp = createApp()
  .route('/users', usersApp)
  .route('/billing', billingApp)
```

## Non-Compliance Signatures

- Route registration is spread across unrelated files with no single mount table
- `app.route()` is absent in a multi-feature app
- Feature route folders import database/SDK clients instead of calling services
- Route handlers create DB connections, Drizzle clients, pools, or migrations directly
- A single route file contains schemas, long handlers, feature middleware, and business logic
- Fallback, `*`, or `/:id` routes appear before more specific routes
- Version prefixes are repeated inside every feature instead of defined once
- `app.mount()` appears in new code, or a mounted foreign app sits where a typed Hono sub-app belongs
- `methodNotAllowed()` is enabled while RPC status unions or OpenAPI responses still assume 404

## Review Checklist

- One obvious composition entry exists
- Route mounting order is intentional
- Fallback routes come last
- Non-Hono mounts use the Mount middleware with a `/*` path, not `app.mount()`
- 405 behavior is either absent by design or reflected in typed and documented responses
- Large features use sub-app folders, not giant flat files
- Feature boundaries are clear enough that new routes have an obvious home
- Persistence work flows through service/repository boundaries when the route is not trivial
- Route structure still preserves typed app inference for tests, RPC, and OpenAPI generation

## Sources

> Checked 2026-11-04.

| Claim | Source |
|---|---|
| Registration order, `route()` copying child routes, strict-mode default | [Routing API](https://hono.dev/docs/api/routing), [App API](https://hono.dev/docs/api/hono) |
| `app.mount()` deprecation and the Mount middleware replacement | [App API](https://hono.dev/docs/api/hono), [Mount Middleware](https://hono.dev/docs/middleware/builtin/mount), [`hono` v4.13.13 release](https://github.com/honojs/hono/releases/tag/v4.13.13) |
| `getPath()` rejection with `strict: false` | [`hono` v4.13.14 release](https://github.com/honojs/hono/releases/tag/v4.13.14) |
| QUERY method, cache key change, and `methodNotAllowed` | [`hono` v4.13.0 release](https://github.com/honojs/hono/releases/tag/v4.13.0), [Method Not Allowed Middleware](https://hono.dev/docs/middleware/builtin/method-not-allowed) |
