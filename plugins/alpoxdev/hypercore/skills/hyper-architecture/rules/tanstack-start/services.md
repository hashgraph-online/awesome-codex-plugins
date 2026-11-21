# Server Functions and Domain Modules

> Server function API usage, runtime validation, and hypercore layering between routes, modules, lib helpers, integrations, and database access.

## Rule Classifications

| Rule | Classification | Enforcement |
|---|---|---|
| Use `createServerFn` for client-callable server RPC | Official | Required for server RPC |
| Use `.validator(...)` as the only validation API | Official | Block `.inputValidator(...)`; it was removed in 1.169.0 |
| Validate mutation input at runtime | Safety policy | Block POST/PUT/PATCH without validation |
| Handler last in chain | Official/API shape | Block malformed chain |
| Domain module/lib layer for non-trivial logic | Hypercore convention | Apply to touched non-trivial logic |
| Split server function wrappers from server-only helpers | Official + Safety policy | Keep `.functions.ts` and `.server.ts` roles separate |
| No `functions/index.ts` barrel | Hypercore convention + Safety policy | Avoid import-protection/tree-shaking ambiguity |
| Server functions are same-origin app RPC | Official + Safety policy | Use server routes for public/cross-origin HTTP endpoints |

See `references/official/tanstack-start/tanstack-start-2026-11-04.md` for the `.validator()` rule, including the removal of `.inputValidator()` in 1.169.0.

## Canonical Server Function Pattern

```typescript
import { createServerFn } from '@tanstack/react-start'
import { z } from 'zod'

const createUserSchema = z.object({
  email: z.email(),
  name: z.string().min(1),
})

export const createUser = createServerFn({ method: 'POST' })
  .validator(createUserSchema)
  .middleware([authMiddleware])
  .handler(async ({ data, context }) => {
    return createUserMutation({ data, user: context.user })
  })
```

Notes:

- `.validator(...)` is the only spelling. `.inputValidator(...)` was removed from `createServerFn` and `createMiddleware` in 1.169.0 — it no longer resolves, so any occurrence is a broken call and a migration, not legacy debt. (Official)
- `.validator(...)` accepts Zod schemas directly, and a builder carries a single validator — a later `.validator(...)` call replaces the earlier one — while `.middleware([...])` is repeatable and merges with previously supplied middleware. (Official)
- `Method` is exactly `'GET' | 'POST'`; no other verb exists. (Official)
- The `strict` option exists and defaults to `strict: true`. It governs TypeScript-level serialization checks; `strict: false` relaxes only the type checks, not the runtime serialization layer. (Official)
- Middleware and input validation order can vary; `handler` must finish the chain. (Official/API shape)
- If a project-local installed version disagrees, verify with typecheck and record the exception.
- Server functions are same-origin app RPC. Use server routes for public APIs, webhooks, cross-origin endpoints, or raw HTTP semantics under `rules/tanstack-start/server-routes.md`.

## Server Function File Organization

TanStack Start's official guidance presents the `*.functions.ts` (server function wrappers) / `*.server.ts` (server-only helpers) split as "one approach", not a mandate (Official). Hypercore applies this pattern inside route-local `-functions/` exceptions and shared `src/modules/<domain>/<feature>/` nested folders (Hypercore convention).

Route-local exception example:

```text
src/routes/billing/
├── route.tsx
├── index.tsx
├── -hooks/
│   └── use-invoices.ts
└── -functions/
    ├── invoices.functions.ts
    ├── invoices.server.ts
    └── invoices.schemas.ts
```

Default domain module example:

```text
src/modules/billing/invoices/
├── invoices.functions.ts
├── invoices.server.ts
├── invoices.schemas.ts
├── invoices-query-keys.ts
├── hooks/
└── components/
```

Roles:

| File | Importable from | Allowed contents |
|---|---|---|
| `*.functions.ts` | Static imports from loaders, components, hooks, or other server functions | `createServerFn` wrappers, middleware/validator/handler chains |
| `*.server.ts` | Inside `*.functions.ts` handlers or server-only modules | DB, secrets, filesystem, privileged SDKs, internal business logic |
| `*.schemas.ts` / `schemas.ts` | Client and server | Zod schemas, serializable DTOs, constants |
| `*-query-keys.ts` | Client and server | TanStack Query key builders, cache tags |

Rules:

- `.functions.ts` is a naming convention, not an enforced boundary: import protection enforces only the `*.server.*` and `*.client.*` file patterns. (Official)
- Do not dynamically import server functions. Use direct static imports so client-bundle rewrites and import protection remain traceable.
- `*.functions.ts` must not reference server-only helpers from surviving exports outside handlers.
- Do not re-export safe exports and `.server.ts` exports through the same `index.ts` barrel.
- Promote route-local `-functions/` to `src/modules/<domain>/<feature>/` when cross-route reuse, domain nouns, cache/auth, or permission responsibilities appear.
- Shared domain code uses nested domain/feature folders. Do not add new direct leaves such as `src/modules/foo.ts`.
- Keep external provider clients out of domain modules when possible; put them under `src/integrations/<provider>/` or a server-only module.

## Layering

```text
Route / hook / query
  -> routes/<page>/-functions/<resource>.functions.ts
     or src/modules/<domain>/<feature>/<resource>.functions.ts
  -> src/modules/<domain>/<feature>/<resource>.server.ts
  -> src/lib/<domain>/shared helpers, src/db/<domain>/repositories,
     or src/integrations/<provider>/server-only clients
  -> database/ORM client or external SDK
```

- **Safety policy:** routes do not import database/ORM clients directly.
- **Safety policy:** `*.server.ts` or DB/repository imports must not survive in client-reachable files.
- **Hypercore convention:** non-trivial business logic belongs in `modules/<domain>/<feature>/` or domain-specific `lib/<domain>/` folders, not route files.
- **Hypercore convention:** simple CRUD can stay in a server function if extraction would add noise.

## Query and Mutation Pattern

- Reads: use GET server functions when safe and cache semantics are appropriate.
- Mutations: use POST/PUT/PATCH with runtime `.validator(...)`. (Safety policy)
- Client hooks should usually wrap server functions with `useServerFn` and TanStack Query for cache invalidation.
- Loaders may directly call server functions because route lifecycle code is not a React component.
- Auth-required server functions must not rely only on route `beforeLoad`; add middleware or handler-level auth checks to the server function itself.
- CSRF: Start auto-installs `createCsrfMiddleware()` for server functions when `src/start.ts` is ABSENT. Creating `src/start.ts` silently drops that automatic installation, so the file must add `requestMiddleware: [createCsrfMiddleware()]` explicitly, filtered to server functions. (Official + Safety policy)

```ts
// src/start.ts
import { createStart, createCsrfMiddleware } from '@tanstack/react-start'

const csrfMiddleware = createCsrfMiddleware({
  filter: (ctx) => ctx.handlerType === 'serverFn',
})

export const startInstance = createStart(() => ({
  requestMiddleware: [csrfMiddleware],
}))
```

- The `filter` is not optional polish: by default `createCsrfMiddleware()` validates every request the middleware handles, so an unfiltered global install also checks SSR page requests and server routes. The official types expose `filter`, `origin`, `secFetchSite` (default `'same-origin'`), `referer` (default `true`), `allowRequestsWithoutOriginCheck` (default `false`), and `failureResponse` (default `403 Forbidden`); the last three are type-level facts that the guide does not document. (Official)
- GET server functions that depend on user/session/tenant data must not set public cache headers. `public` tells every CDN and proxy between the user and the origin that anybody may be served that response, so one user's authenticated payload gets replayed to the next user. Use `private` and vary on identity, or bypass caching entirely:
  `Cache-Control: private, max-age=60` with `Vary: Cookie, Authorization`, or `no-store` when the response must never be cached. (Official)
- Server function IDs are SHA256 hashes of the function in production, with `_1`/`_2` suffixes on duplicates. `tanstackStart({ serverFns: { generateFunctionId } })` customizes them (experimental). Treat the ID as an internal detail when a log or cache key depends on it. (Official)
- `serverFns.fetch` in `createStart` sets the fetch implementation for server function calls when tests or custom runtimes need it; the call site and middleware can override it. It is a testing seam, not a production routing rule.

## Validation Checklist

- [ ] New mutation server functions have `.validator(...)`.
- [ ] `.inputValidator(` does not appear anywhere; it was removed in 1.169.0 and a hit means broken code.
- [ ] `handler` is last in the chain.
- [ ] Auth-required server functions use middleware or an equivalent checked boundary.
- [ ] `*.functions.ts` and `*.server.ts` are split (a naming convention, not an import-protection rule), and server-only imports do not survive outside recognized boundaries.
- [ ] Server functions are direct static imports, not dynamic imports or mixed-barrel imports.
- [ ] Public/cross-origin/raw HTTP endpoints use server routes, not server functions.
- [ ] A custom `src/start.ts` explicitly adds `requestMiddleware: [createCsrfMiddleware({ filter: (ctx) => ctx.handlerType === 'serverFn' })]`.
- [ ] Routes do not access ORM/database clients directly.
- [ ] Non-trivial logic is delegated to `modules/<domain>/<feature>/` or domain-specific `lib/<domain>/` folders.
- [ ] No `functions/index.ts` barrel export was introduced.

## Sources

> Sources checked 2026-11-04: <https://tanstack.com/start/latest/docs/framework/react/guide/server-functions.md> (same-origin RPC, `Cache-Control` safety), <https://tanstack.com/start/latest/docs/framework/react/guide/middleware.md> (CSRF `filter` and default-validates-every-request behavior), <https://tanstack.com/start/latest/docs/framework/react/migrate-from-release-candidate.md> (`.inputValidator()` removal). Official TanStack behavior is otherwise delegated to this package's own snapshots: `references/official/tanstack-start/tanstack-start-2026-11-04.md`, `references/official/tanstack-start/tanstack-router-2026-11-04.md`, and `references/official/tanstack-start/current-docs-2026-11-04.md` (official facts verified 2026-11-04). Repository-local links checked 2026-11-04.
