# Middleware

> Middleware rules/tanstack-start for validation, context propagation, and safe client-to-server data transfer

---

## Rule Classifications

| Rule | Classification | Enforcement |
|---|---|---|
| Request middleware uses `createMiddleware()` by default | Official | Do not force function-only syntax for request middleware |
| Server function middleware uses `createMiddleware({ type: 'function' })` | Official | Block wrong middleware type when `.client(...)`, `.validator(...)`, or server-function-only behavior is used |
| Server function middleware validation uses `.validator(...)` | Official | Block `.inputValidator(...)`, removed in 1.169.0; keep middleware and server-function validation chains conceptually separate |
| `sendContext` is explicit and not automatic | Official | Validate before trust |
| Validate client-provided context server-side | Safety policy | Block unvalidated trust |
| The session principal comes from a server-trusted source, never from `sendContext` | Safety policy | Block authorization decisions taken on client-supplied values |
| Centralize shared auth/logging/tenant logic | Hypercore convention | Warn/fix in touched code |

---

## Core Rule

Middleware is not just for auth. It is the boundary where request context, validation, logging, and server-safe data propagation must be made explicit.

TanStack Start has two middleware types:

- Request middleware: `createMiddleware()` or `createMiddleware({ type: 'request' })`. It runs for server requests, server routes, SSR, and server functions and only has `.server(...)`.
- Server function middleware: `createMiddleware({ type: 'function' })`. It is for `createServerFn` middleware chains and may use `.client(...)`, `.server(...)`, and `.validator(...)`.

---

## Non-Negotiable Rules

| Check | Rule |
|------|------|
| Request middleware written with function-only behavior? | BLOCKED. Use `createMiddleware({ type: 'function' })` |
| Server function middleware validation written as `.inputValidator(...)`? | BLOCKED. The alias was removed from `createMiddleware` in 1.169.0; `.validator(...)` is the only spelling |
| Dynamic data sent from client via `sendContext` and used on the server without validation? | BLOCKED |
| A `sendContext` value treated as authorization because it passed shape validation? | BLOCKED. A parsed identifier is well-formed, not authorized; verify the session principal's access separately |
| Middleware mutates context implicitly instead of returning `next({ context: ... })`? | BLOCKED |
| Shared auth/logging/tenant logic duplicated across handlers instead of middleware? | WARNING. Prefer middleware |

---

## Approved Patterns

- Use `.validator(...)` on server function middleware when the middleware owns data transformation or validation
- Do not conflate middleware `.validator(...)` with server-function `.validator(...)`; they belong to different chain objects even though the method name is the same
- Use `next({ context: { ... } })` to extend context
- Use client middleware `sendContext` only for data that is actually needed on the server
- Validate client-provided `sendContext` on the server before trusting it
- Use `createStart(() => ({ requestMiddleware: [...] }))` in `src/start.ts` for global request middleware
- When the global request middleware array installs CSRF protection, filter it to server functions with `filter: (ctx) => ctx.handlerType === 'serverFn'`. The unfiltered default validates every request the middleware handles, including SSR page requests and server routes
- A route guard is not a data authorization boundary. `beforeLoad` and middleware can keep a user off a page, but anything a server function or server route returns still needs its own check against the session principal

---

## `sendContext` Security Rule

Client context is not automatically trusted. Anything the client can send, the client can lie about, so a value arriving through `sendContext` is client-controlled data no matter how well it is typed.

> **Shape validation is not authorization.** A parsed UUID or number is a well-formed identifier, not an authorized one. (Official)

Safety policy: when the value selects which rows get read or written — a query key, a filter, or a path parameter — verify the session principal's access to it separately, or a logged-in user can rewrite the value in their own request and reach another tenant's data. Derive the session itself from a server-trusted source (a cookie + DB lookup in `authMiddleware`), never from `sendContext`.

Wrong:

```ts
const requestLogger = createMiddleware({ type: 'function' })
  .client(async ({ next, context }) => {
    return next({
      sendContext: {
        workspaceId: context.workspaceId,
      },
    })
  })
  .server(async ({ next, context }) => {
    // Client-controlled: nothing here proves the caller may use this workspace.
    useWorkspace(context.workspaceId)
    return next()
  })
```

Right:

```ts
const authMiddleware = createMiddleware({ type: 'function' }).server(
  async ({ next }) => {
    // Derive the session from a server-trusted source, never from sendContext.
    const session = await db.session.findByToken(getCookie('session'))
    if (!session) throw new Error('Unauthorized')
    return next({ context: { session } })
  },
)

const workspaceGuard = createMiddleware({ type: 'function' })
  .middleware([authMiddleware])
  .client(async ({ next, context }) => {
    return next({
      sendContext: {
        // The client may send this, but it is a hint, never an authorization.
        workspaceId: context.workspaceId,
      },
    })
  })
  .server(async ({ next, context }) => {
    const workspaceId = zodValidator(z.string()).parse(context.workspaceId)
    // Shape-valid is not access-valid: check the session's rights to this workspace.
    await assertWorkspaceAccess(context.session, workspaceId)
    useWorkspace(workspaceId)
    return next()
  })
```

---

## Review Checklist

- Request middleware uses `createMiddleware()` unless function-only features are needed
- Server function middleware uses `createMiddleware({ type: 'function' })`
- Server function middleware uses `.validator(...)` for middleware-owned data validation
- Shared request logic is centralized in middleware
- `sendContext` is minimal and validated on the server
- The session principal is derived from a server-trusted source, never from `sendContext`
- Context extension is explicit and typed

## Sources

> Sources checked 2026-11-04: <https://tanstack.com/start/latest/docs/framework/react/guide/middleware.md> (middleware types, `sendContext`, "shape validation is not authorization", CSRF `filter`, middleware `handlerType`), <https://tanstack.com/start/latest/docs/framework/react/guide/authentication-server-primitives.md> ("A route guard is not a data authorization boundary."), <https://tanstack.com/start/latest/docs/framework/react/migrate-from-release-candidate.md> (`.inputValidator()` removal). Official TanStack behavior is otherwise delegated to this package's own snapshots: `references/official/tanstack-start/tanstack-start-2026-11-04.md`, `references/official/tanstack-start/tanstack-router-2026-11-04.md`, and `references/official/tanstack-start/current-docs-2026-11-04.md` (official facts verified 2026-11-04). Repository-local links checked 2026-11-04.
