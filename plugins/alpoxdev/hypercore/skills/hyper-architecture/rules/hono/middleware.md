# Middleware

> Middleware rules/hono for request boundaries and shared concerns

---
## Stable Hono 4.13 Baseline

Middleware executes onion-style in registration order: code before `await next()` runs outward-in and code after it runs inward-out. Middleware may early-return a `Response`. Chained `.use()` calls accumulate typed `Variables` for following handlers.

Recommended order is an explicit project contract, commonly request ID/observability, CORS or security headers, authentication, authorization, validation, then handler. Place response mutation after `await next()` only when it is intended to wrap every downstream response.

- Scope middleware with a path or sub-app; do not make feature-only authorization global.
- Use typed `Variables` or `createMiddleware<Env>()` for guaranteed request-scoped values.
- Use global `ContextVariableMap` augmentation only for values truly guaranteed across every consuming app; local typed chaining is safer. This is official guidance, not a Hypercore preference: the Context API documents that `ContextVariableMap` adds types globally to all contexts, regardless of whether the middleware that sets the variable has actually run, so `c.get()` looks type-safe in handlers where the value is `undefined`.
- Never store request state in module globals or reuse `Context` across requests.
- Keep Hono core and middleware package versions compatible, especially for URL-import runtimes such as Deno.

## Core Rule

Middleware is where request-wide concerns become explicit: auth, request IDs, CORS, logging, and context enrichment.

Extract reusable middleware with typed helpers such as `createMiddleware()` when the middleware sets variables or depends on bindings.

## Non-Negotiable Rules

| Check | Rule |
|------|------|
| Middleware order assumed incorrectly | BLOCKED |
| Shared request concern duplicated in handlers | WARNING |
| `c.set()` values used without typed `Variables` | BLOCKED |
| Cross-request state assumed via `Context` | BLOCKED |
| Global `ContextVariableMap` used for values not guaranteed by app-wide middleware | BLOCKED |

## Typed Middleware Pattern

```ts
import { createMiddleware } from 'hono/factory'

import type { AppEnv } from '@/lib/types'

export const authMiddleware = createMiddleware<AppEnv>(async (c, next) => {
  const user = await resolveUser(c.req)
  c.set('user', user)
  await next()
})
```

## Review Checklist

- Registration order is intentional
- Shared concerns are centralized
- Context variables are typed
- Middleware does not become a hidden business-logic layer
- Request-scoped context values are set before handlers that read them

## Sources

> Checked 2026-11-04.

| Claim | Source |
|---|---|
| Registration order, onion execution, typed variable accumulation | [Middleware Guide](https://hono.dev/docs/guides/middleware), [Routing API](https://hono.dev/docs/api/routing) |
| `ContextVariableMap` applying types globally regardless of whether the middleware ran | [Context API](https://hono.dev/docs/api/context) |
