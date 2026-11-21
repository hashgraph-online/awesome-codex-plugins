# Server Routes

> TanStack Start server routes are official HTTP endpoints; hypercore reserves them for actual HTTP semantics.

## Rule Classifications

| Rule | Classification | Enforcement |
|---|---|---|
| Server routes defined with `createFileRoute(... )({ server })` | Official | Allowed |
| Simple handlers use `server.handlers`; composed handlers use `createHandlers` | Official | Use the current handler shape |
| Route-level middleware can be declared with `server.middleware` | Official | Apply when all handlers share request behavior |
| Server routes for webhooks/files/health/auth/public machine endpoints | Official + Hypercore convention | Allowed with justification |
| Duplicate route path + HTTP method handlers | Official | Block collisions |
| Internal app RPC implemented as server route | Hypercore convention | Prefer server function |
| Unvalidated request body in server route | Safety policy | Validate before trust |
| Response helpers that silently override the returned response | Official | Block contradictory status/cookie handling |

## Current Server Route Shape

Server routes follow TanStack Router file-route conventions. A route becomes an API route when `createFileRoute(...)(...)` includes a `server` property.

Simple handlers use a `server.handlers` object:

```ts
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/hello')({
  server: {
    handlers: {
      GET: async ({ request }) => {
        return new Response('Hello, World! from ' + request.url)
      },
    },
  },
})
```

When handlers need middleware composition, use the `createHandlers` function form documented by the current server-routes guide. Use `server.middleware` when the same route-level middleware applies to all handlers.

Do not create duplicate methods for the same resolved route path. File-route variants such as `users.ts` and `users.index.ts` can resolve to the same API route; duplicate HTTP methods are invalid. wildcard/splat server routes use the trailing `$` convention, such as `routes/file/$.ts`.

## Response Helper Precedence

Responders written with helpers (`setResponseStatus`, `setResponseHeader`, `setCookie`, `appendResponseHeader`) can silently contradict the `Response` they return or throw. These are blocking checks on touched handlers (Official):

| Pattern | Result | Correct form |
|---|---|---|
| `setResponseStatus(401)` then `return new Response(body, { status: 200 })` | Sends `401`; the helper wins | Pick one channel. Either set the status and return a body-only response, or drop the helper |
| `setResponseHeader('set-cookie', cookie)` | Replaces **every** outgoing cookie, including ones another helper set | `setCookie(...)` for one cookie, or `appendResponseHeader('set-cookie', cookie)` to add |
| `setResponseStatus(204)` / `205` / `304` as a helper on a serialized server-function reply | Ignored | Return a `Response` with that status |
| Helper `Location` on a serialized server-function reply | Never serialized | Use `redirect()` |
| `setResponseStatus` given a code outside `200`-`599` | Ignored, with a non-production warning | Use a real HTTP status |

Request-level facts that catch bad handlers early (Official):

- `getRequestHeader(name)` returns `''` for a header that is present but empty and `undefined` only when it is missing. Do not test with `if (!header)`; check `=== undefined`.
- A path with invalid percent-encoding gets `400 Bad Request` before the server entry or any middleware runs, so handlers never see it.
- `sendContext` is `undefined`, not `{}`, when no function middleware sends context.

Uncaught errors in a Start handler now produce a generic JSON body with status `400`-`599` (`500` by default) and never echo the message or stack. When an endpoint needs a specific error payload, return a `Response` rather than throwing. A thrown `Response` keeps its body and metadata, except that `HEAD` requests and the statuses `204`, `205`, and `304` lose the body.

## Typed Request Context

Registering `server.requestContext` on `@tanstack/react-router`'s `Register` interface types the per-request context that `handler.fetch(request, { context })` receives. Registration types only; it does not create values. The context is visible to global middleware, request and function middleware, server routes, server functions, and the router.

```ts
declare module '@tanstack/react-router' {
  interface Register {
    server: {
      requestContext: { requestId: string }
    }
  }
}
```

## Allowed Uses

Use server routes when the endpoint has HTTP semantics that are not just app-internal RPC:

- Third-party webhooks.
- Auth provider callbacks or required auth endpoints.
- Health/readiness endpoints.
- File upload/download or wildcard HTTP handlers.
- `robots.txt`, `sitemap.xml`, LLMO/metadata endpoints.
- Public machine-readable resources.

## Prefer Server Functions For

- App reads/mutations consumed by React components or route loaders.
- Internal RPC that benefits from end-to-end typing and Start server function middleware.
- Operations that should share TanStack Query invalidation patterns.

## Validation Checklist

- [ ] Every new server route states its HTTP justification.
- [ ] Simple server routes use a `server.handlers` object; composed handlers use the current `createHandlers` function form.
- [ ] `server.middleware` is used only for route-level behavior shared by all handlers.
- [ ] Duplicate route path + HTTP method collisions were checked.
- [ ] Wildcard/splat routes use the trailing `$` file-route convention when needed.
- [ ] Request bodies, params, headers, and client-sent context are validated before trust.
- [ ] Response helpers and returned `Response` objects do not contradict each other, and `set-cookie` uses `setCookie` or `appendResponseHeader`.
- [ ] Internal app RPC uses server functions unless the user explicitly requested HTTP endpoints.
- [ ] Server route middleware is applied at route or handler level where needed.

## Sources

> Sources checked 2026-11-04: <https://tanstack.com/start/latest/docs/framework/react/guide/server-routes.md> (`handlers`, `createHandlers`, route-level `middleware`), <https://tanstack.com/start/latest/docs/framework/react/guide/server-entry-point.md> (error handling, `server.requestContext`), <https://tanstack.com/start/latest/docs/framework/react/migrate-from-release-candidate.md> (response helper precedence, `set-cookie` replacement, error status range). Official TanStack behavior is otherwise delegated to this package's own snapshots: `references/official/tanstack-start/tanstack-start-2026-11-04.md`, `references/official/tanstack-start/tanstack-router-2026-11-04.md`, and `references/official/tanstack-start/current-docs-2026-11-04.md` (official facts verified 2026-11-04). Repository-local links checked 2026-11-04.
