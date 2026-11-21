# Errors and Responses

> Centralize HTTP failure handling and preserve response intent

---
## Stable Hono 4.13 Baseline

`app.notFound()` runs only on the top-level app. A child route's `onError` handler takes priority over a parent handler. `HTTPException.getResponse()` does not know headers already accumulated on `Context`.

- Define one public error envelope and map expected domain failures deliberately to literal HTTP statuses.
- Never expose stack traces, SQL, provider payloads, secrets, or raw validation internals.
- Preserve required CORS, request ID, cache, and authentication headers when replacing an error response.
- RPC does not infer global middleware or `onError()` responses automatically; use `ApplyGlobalResponse` when the client contract includes a shared global response.
- Do not use `c.notFound()` as the only typed 404 contract for an RPC route unless `NotFoundResponse` is augmented. Either return a route-local typed JSON variant or declare the module augmentation so `c.notFound()` carries the response type.
- Adding `methodNotAllowed({ app })` turns a wrong-method request on a known path from `404` into `405` with `Allow`. Update the RPC status union, the OpenAPI response list, and any client branch that treated that case as not-found in the same change.
- Test thrown `HTTPException`, unknown error, route-local error handler precedence, top-level 404, wrong-method behavior, and required headers.

## Core Rule

- Expected HTTP failures should use `HTTPException` or one explicit translation layer
- Non-trivial apps should define `app.onError()`
- Preserve context-set headers when rebuilding an error response

## Example

```ts
import { HTTPException } from 'hono/http-exception'

app.onError((err, c) => {
  if (err instanceof HTTPException) {
    const response = err.getResponse()
    c.res.headers.forEach((value, key) => {
      response.headers.set(key, value)
    })
    return response
  }

  return c.json({ message: 'Internal Server Error' }, 500)
})
```

## Typed 404 Pattern

```ts
import { Hono, TypedResponse } from 'hono'

declare module 'hono' {
  interface NotFoundResponse
    extends Response,
      TypedResponse<{ error: string }, 404, 'json'> {}
}

export const app = new Hono()
  .get('/posts/:id', async (c) => {
    const post = await getPost(c.req.param('id'))
    if (!post) {
      return c.notFound()
    }
    return c.json({ post }, 200)
  })
  .notFound((c) => c.json({ error: 'not found' }, 404))

export type AppType = typeof app
```

The augmentation is global to the app's types. Keep it in one module that the exported app type already imports, and make the runtime `.notFound()` handler return the same shape.

## Review Checklist

- Central error translation exists when needed
- Error responses preserve deliberate headers/status
- Expected HTTP errors are not all generic throws
- Typed RPC/public-client 404 behavior is covered by `app.notFound()` or an explicit JSON response contract when clients depend on it
- A typed 404 uses either a route-local `c.json(..., 404)` or a single `NotFoundResponse` augmentation, not both with different shapes
- If `methodNotAllowed()` is enabled, the 405 outcome appears in typed clients and OpenAPI responses

## Sources

> Checked 2026-11-04.

| Claim | Source |
|---|---|
| Top-level `notFound()`, route-level `onError()` priority | [App API](https://hono.dev/docs/api/hono) |
| `HTTPException.getResponse()` and `Context` | [HTTPException API](https://hono.dev/docs/api/exception) |
| `NotFoundResponse` augmentation | [RPC Guide](https://hono.dev/docs/guides/rpc) |
| `methodNotAllowed()` changing 404 into 405 with `Allow` | [Method Not Allowed Middleware](https://hono.dev/docs/middleware/builtin/method-not-allowed) |
