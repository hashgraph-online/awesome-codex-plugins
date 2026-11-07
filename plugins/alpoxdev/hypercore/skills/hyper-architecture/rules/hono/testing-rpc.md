# Testing and RPC

> Protect typed clients and tests from route-shape regressions

---
## Stable Hono 4.13 Baseline

Hono RPC requires TypeScript `strict` on both server and client. Producer and consumer Hono versions must match; version skew can cause excessively deep type instantiation. Large contracts may also degrade editor performance.

- Export `AppType` from the final chained route value, not a later mutated app or partial child.
- Compile and consume declarations or use project references across package boundaries; do not deep-import server implementation.
- Use `ApplyGlobalResponse` for shared global error response typing.
- Use `parseResponse()`, `DetailedError`, `InferRequestType`, and `InferResponseType` where they make client contracts observable.
- Pass path parameters and query values as `string`. `hc` types them as strings even when the server schema coerces numbers, so a literal `id: 1` fails type checking.
- Return `await`ed values or plain promises from handlers, never a `.then()` chain. A handler that returns a `.then()` chain directly loses its response type and the client infers `unknown`.
- Remember that `hc` does not URL-encode path parameter values automatically; encode values or use an explicitly tested regexp route when slashes are allowed.
- Use `$path()` or `$url()` to build a request path from the client instead of assembling strings by hand; both stay typed against the app.
- When the client contract includes a typed 404, either return a route-local `c.json(..., 404)` or augment `NotFoundResponse` so `c.notFound()` carries the response type.
- Use `app.request()` for behavior, `testClient()` for server-side typed ergonomics, and a real `hc` boundary test only when client serialization/base URL behavior matters.
- `testClient()` and route typing require routes defined through chained methods directly on the `Hono` instance; detached registration erases inference.
- Pass runtime bindings as the third argument to `app.request()` and test adapter-specific behavior separately.

## Core Rule

- If the app uses `testClient()` or `hc`, preserve route type inference
- Export `AppType` when `hc` or a shared RPC/client contract depends on the app
- In larger apps, keep sub-app composition typed all the way to the exported surface
- Keep explicit response statuses so typed RPC and generated OpenAPI docs agree

## Example

```ts
export const app = new Hono()
  .get('/search', (c) => {
    const query = c.req.query('q')
    return c.json({ query })
  })

export type AppType = typeof app
```

## Large-App Contract Pattern

```ts
// app.ts
export const app = createApp()
  .route('/users', usersApp)
  .route('/billing', billingApp)

export type AppType = typeof app
```

```ts
// client.ts
import { hc } from 'hono/client'

import type { AppType } from './app'

export const client = hc<AppType>('/api')
```

When client compile time or editor latency becomes the problem, calculate the client type once at compile time instead of on every call site:

```ts
// client.ts
import { hc } from 'hono/client'

import type { AppType } from './app'

const client = hc<AppType>('')
export type Client = typeof client

export const hcWithType = (...args: Parameters<typeof hc>): Client =>
  hc<AppType>(...args)
```

Use `app.request()` for request/response behavior tests, `testClient()` for typed server-side ergonomics, and `hc<AppType>()` for shared client-contract checks.

## Non-Compliance Signatures

- Route registration uses detached mutation that erases chained route types
- `AppType` is exported from a partial sub-app when consumers expect the full API
- Response helpers omit explicit statuses for routes with multiple success or error variants
- A handler returns a `.then()` chain and the client acquires an `unknown` response type
- Client call sites pass numbers or objects for path parameters and query values
- Frontend typed clients import route internals instead of the exported app type
- Generated OpenAPI response schemas disagree with RPC-inferred response variants
- Public clients depend on 404 shape but no `app.notFound()` or explicit JSON response contract is tested

## Review Checklist

- Route types still flow through the exported app
- `testClient()` remains useful after refactors
- `hc<AppType>` or sub-app clients still infer correctly
- Handlers return `await`ed values, not `.then()` chains
- Path and query arguments are strings at the call site
- `AppType` is exported for RPC/client consumers, not merely because a test exists
- Detached registration did not silently erase route typing
- Request-level tests cover changed behavior with `app.request()` or the runtime adapter's equivalent
- Typed client or OpenAPI contract checks are updated when public route shapes change

## Sources

> Checked 2026-11-04. The RPC and testing behavior below comes from the official guide pages; no package version claim is made beyond the Hono 4.13 line.

| Claim | Source |
|---|---|
| `testClient()` requiring chained route definitions on the instance | [Testing Helper](https://hono.dev/docs/helpers/testing) |
| `string` path/query arguments, `.then()` chain type loss, `$path()` / `$url()`, typed `NotFoundResponse`, `hcWithType`, `DetailedError`, version matching | [RPC Guide](https://hono.dev/docs/guides/rpc) |
