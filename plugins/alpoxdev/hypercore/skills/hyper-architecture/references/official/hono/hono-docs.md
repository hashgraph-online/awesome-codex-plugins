# Hono Official Docs Summary

last_verified_at: 2026-11-07

## Contents

- Stable package snapshot
- Confirmed points from official docs
- How this affects the skill
- Sources

## Stable package snapshot

Verified from npm registry metadata and the cited release notes on 2026-11-07. These are evidence snapshots, not automatic upgrade targets.

| Package | Stable | Compatibility observed |
|---|---:|---|
| `hono` | 4.13.17 | Node engine `>=16.9.0` in the core package; registry `latest` is 4.13.17 and 4.13.16 remains the security floor |
| `@hono/node-server` | 2.1.6 | Node `>=20`, Hono `^4 || ^5.0.0-0` |
| `@hono/zod-validator` | 0.9.1 | Hono `>=4.11.2`, Zod `^3.25.0 || ^4.0.0` |
| `@hono/standard-validator` | 0.4.1 | Hono `>=4.11.2`, Standard Schema `^1.0.0` |
| `@hono/zod-openapi` | 1.6.3 | Hono `>=4.10.0`, Zod `^4.0.0` only |
| `@hono/swagger-ui` | 0.6.2 | Hono `>=4.0.0` |
| `hono-openapi` | 1.5.0 | Third-party; Hono `^4.11.2` plus Standard Schema peers |

Sources: [npm registry: hono](https://registry.npmjs.org/hono), [npm registry: `@hono/node-server`](https://registry.npmjs.org/@hono/node-server), [Hono middleware repository](https://github.com/honojs/middleware), [`@hono/node-server`](https://github.com/honojs/node-server), [`hono-openapi`](https://github.com/rhinobase/hono-openapi)

Not adopted: `hono` 5.0.0-rc.1 sits on the `next` tag and `drizzle-orm` 1.0.0-rc.x is a release candidate. Where this skill names a v5 behavior it records a removal that already exists as a v4 deprecation; no release-candidate API is presented as current.

Installed manifests and lockfiles win for implementation. Re-check registry metadata before changing dependencies after the verification date.

Use this reference when the core skill or rule files need an official-doc check.

## Confirmed points from official docs

1. Best practices favor smaller apps and `app.route()` composition, and explicitly say not to make controllers when possible.
Source: [Best Practices](https://hono.dev/docs/guides/best-practices)

2. `createFactory()`, `createHandlers()`, and `createApp()` exist to preserve types when extracting handlers and middleware. `createFactory()` also accepts `defaultAppOptions` and `initApp`.
Source: [Factory Helper](https://hono.dev/docs/helpers/factory)

3. `Context` is instantiated per request. It can hold request-scoped values, headers, and status, and typed `Variables` should be supplied through app generics when using `c.set()` / `c.get()`.
Source: [Context API](https://hono.dev/docs/api/context)

4. Middleware and handlers execute in registration order. Fallback and catch-all placement therefore matters.
Source: [Routing API](https://hono.dev/docs/api/routing), [Middleware Guide](https://hono.dev/docs/guides/middleware)

5. Hono validation is middleware-based. The docs recommend using a third-party validator, and the official ecosystem supports both `@hono/zod-validator` and `@hono/standard-validator`.
Source: [Validation Guide](https://hono.dev/docs/guides/validation)

6. `HTTPException.getResponse()` is not aware of `Context`; if headers were already set on `Context`, a new response must preserve them explicitly.
Source: [HTTPException API](https://hono.dev/docs/api/exception)

7. `testClient()` only infers route types correctly when routes are defined through chained methods directly on the `Hono` instance whose type is exported.
Source: [Testing Helper](https://hono.dev/docs/helpers/testing)

8. Larger-app RPC composition needs care to preserve type inference, and typed clients depend on stable `AppType` or sub-app exports.
Source: [RPC Guide](https://hono.dev/docs/guides/rpc)

9. `app.request()` supports request/response testing, and Hono also provides typed testing helpers for route contracts.
Source: [Testing Guide](https://hono.dev/docs/guides/testing), [Testing Helper](https://hono.dev/docs/helpers/testing)

10. `@hono/zod-openapi` uses `OpenAPIHono`, `createRoute()`, `app.openapi()`, and `app.doc()` / `app.doc31()` to generate OpenAPI documents from route schemas.
Source: [Zod OpenAPI Example](https://hono.dev/examples/zod-openapi), [`@hono/zod-openapi` README](https://github.com/honojs/middleware/tree/main/packages/zod-openapi)

11. `hono-openapi` supports middleware-driven OpenAPI generation with `describeRoute()`, `validator()`, `resolver()`, and `openAPIRouteHandler()` for multiple validator ecosystems. From 1.3.2 a `validator()` route gets a 400 validation response without manual documentation, and 1.4.0 resolves `resolver()` schemas in headers.
Source: [Hono OpenAPI Example](https://hono.dev/examples/hono-openapi), [`hono-openapi` releases](https://github.com/rhinobase/hono-openapi/releases)

12. `@hono/swagger-ui` serves Swagger UI from a Hono route and should point at a generated spec endpoint; it does not generate the spec by itself. 0.6.2 escapes the title and string options embedded in the generated page.
Source: [Swagger UI Example](https://hono.dev/examples/swagger-ui), [`@hono/swagger-ui` README](https://github.com/honojs/middleware/tree/main/packages/swagger-ui)

13. OpenAPI operations should define responses and reusable components explicitly; security schemes belong under `components.securitySchemes`, and examples can be reusable components.
Source: [OpenAPI Specification 3.1.0](https://spec.openapis.org/oas/v3.1.0.html), [Swagger Authentication Docs](https://swagger.io/docs/specification/v3_0/authentication/), [Swagger `$ref` Docs](https://swagger.io/docs/specification/v3_0/using-ref/), [Swagger Examples Docs](https://swagger.io/docs/specification/v3_0/adding-examples/)

14. Hono environment bindings are typed through app generics and accessed with `c.env`. The Cloudflare Workers docs include D1 and other bindings as part of the `Bindings` model, and the Factory Helper docs show an `initApp` example that creates a Drizzle D1 database from `c.env` and stores it in typed `Variables`.
Source: [Context API](https://hono.dev/docs/api/context), [Cloudflare Workers](https://hono.dev/docs/getting-started/cloudflare-workers), [Factory Helper](https://hono.dev/docs/helpers/factory)

15. The root app provides `use`, `route`, `basePath`, `notFound`, and `onError`; `notFound` is called only from the top-level app, while route-level `onError` handlers take priority over a parent handler.
Source: [App API](https://hono.dev/docs/api/hono)

16. Middleware executes in registration order and typed variables accumulate across chained middleware. Shared middleware placement therefore affects both behavior and inferred context.
Source: [Middleware Guide](https://hono.dev/docs/guides/middleware)

17. Hono is Web-Standards based and supports multiple runtimes, while Node.js runs through `@hono/node-server`. A runtime-neutral app plus separate adapter entrypoint is a Hypercore portability convention grounded in those facts, not an official required folder layout.
Source: [Hono repository](https://github.com/honojs/hono), [Node.js Guide](https://hono.dev/docs/getting-started/nodejs), [`@hono/node-server`](https://github.com/honojs/node-server)

18. `hono` 4.13.16 is the security floor. It fixes, in one release, `mount()` / `app.mount()` forwarding a path that bypasses middleware scoped inside the mount prefix, `RegExpRouter` (and therefore the default `SmartRouter`) skipping wildcard middleware for some route patterns and for paths with an encoded line terminator, `validator('form')` skipping `multipart/form-data` validation when extra parameters such as `charset` are present, `css` HTML injection through a closing tag split across template parts, and `csrf()` not checking `text/ping` requests. Custom patterns that can match the empty string, such as `{[0-9]*}`, now throw `UnsupportedPathError`, and build-time `PreparedRegExpRouter` data must be regenerated on upgrade.
Source: [`hono` v4.13.16 release](https://github.com/honojs/hono/releases/tag/v4.13.16)

19. Runtime adapters are separate packages: `@hono/bun`, `@hono/deno`, `@hono/cloudflare-workers`, `@hono/aws-lambda`, `@hono/lambda-edge`, `@hono/netlify`, `@hono/vercel`, and `@hono/service-worker`. `hono/<adapter>` still works in v4 but is deprecated and will be removed in v5. `hono/cloudflare-pages` is deprecated without a replacement package; Cloudflare recommends Workers with static assets.
Source: [`hono` v4.13.10 release](https://github.com/honojs/hono/releases/tag/v4.13.10), [Cloudflare Pages guide](https://hono.dev/docs/getting-started/cloudflare-pages)

20. `app.mount()` is deprecated in v4 and removed in v5. The replacement is the Mount middleware: `import { mount } from 'hono/mount'`, registered as `app.all('/prefix/*', mount(handler))`. The mounted application is called as `handler(request, c.env, c.executionCtx)`, and by default receives a `Request` whose matched path prefix has been removed; `optionHandler` and `replaceRequest` change those arguments and that request.
Source: [App API](https://hono.dev/docs/api/hono), [Mount Middleware](https://hono.dev/docs/middleware/builtin/mount), [`hono` v4.13.13 release](https://github.com/honojs/hono/releases/tag/v4.13.13)

21. `methodNotAllowed({ app })` from `hono/method-not-allowed` returns `405 Method Not Allowed` with an `Allow` header when the path matches a registered route but the method does not. Without this middleware Hono returns `404 Not Found` for that case.
Source: [Method Not Allowed Middleware](https://hono.dev/docs/middleware/builtin/method-not-allowed)

22. The HTTP QUERY method is first-class: `app.query()` registers a handler, the Cache middleware caches QUERY responses with a body digest in the key, ETag handles conditional QUERY requests, and CORS defaults to `GET, HEAD, PUT, POST, DELETE, PATCH, QUERY`. The internal cache key format changed for all methods, including GET: entries are stored under `/.hono/cache?__hono_cache_key=...`, so code that purges by the original URL must be updated.
Source: [`hono` v4.13.0 release](https://github.com/honojs/hono/releases/tag/v4.13.0), [Routing API](https://hono.dev/docs/api/routing)

23. `serveStatic` rejects request paths that still contain `%` after decoding, and `allowPercentInPath: true` restores serving files whose names contain a literal `%`. It also serves only `GET` and `HEAD`, and respects `Accept-Encoding` q-values for precompressed files.
Source: [`hono` v4.13.11 release](https://github.com/honojs/hono/releases/tag/v4.13.11), [`hono` v4.13.14 release](https://github.com/honojs/hono/releases/tag/v4.13.14)

24. `validator('form')` handles `multipart/form-data` with extra parameters from 4.13.16. `@hono/standard-validator` 0.4.0 adds `flattenErrors` for form and field error sorting, and 0.4.1 removes the `cookie` header from the default 400 body of `header` validation.
Source: [`hono` v4.13.16 release](https://github.com/honojs/hono/releases/tag/v4.13.16), [`@hono/standard-validator` releases](https://github.com/honojs/middleware/releases)

25. `getPath()` cannot be combined with `strict: false`; the strict default stays `true`.
Source: [`hono` v4.13.14 release](https://github.com/honojs/hono/releases/tag/v4.13.14)

26. `@hono/zod-openapi` 1.6.x: a JSON or form body whose `Content-Type` matches none of the route's declared media types is rejected with `415 Unsupported Media Type` instead of validating an empty object; `request.body.required` defaults to `false`, so an absent body reaches the handler with `c.req.valid('json')` as `{}`, while `required: true` fails with `400`; `get()`, `post()`, and `use()` return the `Hono` type, so `$()` or `HonoToOpenAPIHono` restores `OpenAPIHono`; `defineOpenAPIRoute()` plus `openapiRoutes([...] as const)` registers batches; `createRoute()` accepts `method: 'query'` from 1.6.0.
Source: [`@hono/zod-openapi` README](https://github.com/honojs/middleware/tree/main/packages/zod-openapi), [`@hono/zod-openapi` releases](https://github.com/honojs/middleware/releases)

27. RPC client pitfalls: path parameters and query values must be passed as `string`; a handler that returns a `.then()` chain directly loses its response type and the client infers `unknown`; `$path()` returns a typed path string without the origin; module augmentation of `NotFoundResponse` lets `c.notFound()` carry a typed 404; compiling a client module with the server app (`hcWithType`) removes per-call type calculation.
Source: [RPC Guide](https://hono.dev/docs/guides/rpc)

28. `ContextVariableMap` adds types globally to all contexts, regardless of whether the middleware that sets the variable has actually run, so `c.get()` can look type-safe while returning `undefined` at runtime. Augmentation is appropriate only for a variable set by app-wide middleware.
Source: [Context API](https://hono.dev/docs/api/context)

29. WebSocket support is built into `@hono/node-server`: install `ws`, create a `WebSocketServer` with `{ noServer: true }`, and pass it to `serve()` as `websocket: { server: wss }` while the route uses `upgradeWebSocket` from `@hono/node-server`. `@hono/node-ws` is deprecated. The package requires Node `>=20`; the Node.js guide page still lists older minimums, so the package manifest wins.
Source: [Node.js Guide](https://hono.dev/docs/getting-started/nodejs), [`@hono/node-server` README](https://github.com/honojs/node-server)

## How this affects the skill

- Hypercore route composition rules/hono are grounded in official `app.route()` and factory guidance.
- Hypercore validation rules/hono should not invent a custom validation surface before checking the existing repo standard, and they inherit the 4.13.16 form-validation floor.
- Hypercore error handling rules/hono must not claim `HTTPException.getResponse()` preserves context-set headers automatically.
- Hypercore testing and RPC rules/hono must protect chained app typing instead of treating detached registration as harmless.
- Hypercore OpenAPI rules/hono should keep runtime validation, typed RPC responses, and generated OpenAPI responses aligned, including the 415 and `body.required` outcomes.
- Swagger UI exposure is a platform/security decision separate from spec generation.
- Large apps should compose route modules, typed clients, and OpenAPI metadata from the same app boundary to avoid drift.
- Database bindings and request-scoped database variables should be typed through `Bindings` / `Variables`, while route modules should stay independent from provider-specific setup.
- Adapter imports belong in `@hono/*` packages, and `app.mount()` migrations belong to the Mount middleware, so neither `hono/<adapter>` nor `app.mount()` is accepted as new code.

## Sources

> Checked 2026-11-07. The `hono` row was refreshed against the npm registry; 4.13.16 stays the documented security floor.

| Claim | Source |
|---|---|
| The package versions and compatibility ranges in the snapshot table above | the npm registry and repository URLs listed beside that table |
| The release-specific behavior in points 18-26 | the `honojs/hono` and `honojs/middleware` release pages linked on each point |
| The official Hono and OpenAPI behavior recorded in points 1-17 and 27-29 | the inline `Source:` links on each numbered point above |
