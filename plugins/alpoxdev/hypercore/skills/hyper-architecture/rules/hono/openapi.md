# OpenAPI and Swagger

> Treat generated API documentation as a typed contract boundary

---
## Stable Package Baseline

As verified on 2026-11-04: `@hono/zod-openapi` 1.6.3 requires Hono `>=4.10.0` and Zod `^4.0.0` only; `@hono/swagger-ui` 0.6.2 requires Hono `>=4`; third-party `hono-openapi` 1.5.0 requires Hono `^4.11.2` and Standard Schema ecosystem peers. Lockfile and peer compatibility must be checked before choosing a path.

- Prefer `@hono/zod-openapi` for a Zod 4 route-first API. It does not accept Zod 3, unlike `@hono/zod-validator`.
- Preserve an established `hono-openapi` surface rather than migrating generators incidentally; it is third-party, not an official HonoJS package. From 1.3.2 a `validator()` route gets its 400 validation response automatically, so do not document it twice.
- Do not combine undocumented plain `Hono` children and expect `OpenAPIHono` to discover their metadata.
- Schema every actual success and error status. Keep central error envelopes synchronized with runtime and RPC global response types.
- Generate the document in a deterministic check, validate references and unique `operationId` values, and diff the artifact when it is committed.
- Gate spec/UI exposure separately. A hidden UI does not make a public JSON spec private, and Swagger UI does not generate the spec.

## Core Rule

When a Hono API publishes OpenAPI/Swagger docs, route changes must update the generated contract in the same change. The contract must describe the same requests, responses, status codes, security, and examples that the runtime route actually supports.

Database rows are not automatically public API DTOs. If persistence changes affect a documented response, map ORM rows to the public response schema before publishing or codegen.

## Approved Generation Paths

| Repo shape | Preferred path |
|------|------|
| Zod-first routes | `@hono/zod-openapi` with `OpenAPIHono`, `createRoute()`, `app.openapi()`, and `app.doc()` |
| Mixed validator or Standard Schema repos | `hono-openapi` with `describeRoute()`, `resolver()`, `validator()`, and `openAPIRouteHandler()` |
| UI only | `@hono/swagger-ui` mounted against the generated spec endpoint |

Do not switch generators across a whole app unless the user explicitly asked for that migration.

## Folder Structure

```text
src/
├── app.ts
├── openapi/
│   ├── components.ts
│   ├── errors.ts
│   └── registry.ts
└── routes/
    └── users/
        ├── index.ts
        ├── routes.ts
        ├── schemas.ts
        └── handlers.ts
```

- Keep shared components, security schemes, examples, and error envelopes in `src/openapi/` when more than one feature reuses them.
- Keep feature operation metadata near the feature route it documents.
- Compose the canonical spec at the app boundary, not by copying generated fragments by hand.
- Use a stable spec path such as `/doc` or `/openapi.json`.
- Serve Swagger UI from a separate path such as `/ui`, `/docs`, or an admin route.

## Operation Metadata Checklist

Every documented operation should define:

- Stable `operationId`
- Consistent `tags`
- Path params, query params, headers, and request body schemas
- Success responses with status-specific JSON schemas
- Expected error responses such as 400, 401, 403, 404, 409, 422, and 500 when applicable
- Auth requirements through reusable `components.securitySchemes`
- Request and response examples that match the schema
- Deprecation or hide metadata when an endpoint should not be public

## Contract Drift Rules

| Drift | Rule |
|------|------|
| Handler reads validated data not represented in OpenAPI | BLOCKED. Add the request schema or stop documenting the route. |
| OpenAPI lists a response status the handler never returns | WARNING. Fix the handler or docs before codegen/client publication. |
| Handler returns status-specific payloads but docs only show a generic response | WARNING. Add explicit response schemas. |
| OpenAPI response schema exposes raw ORM rows with internal or sensitive fields | BLOCKED. Add DTO mapping and document the public response contract. |
| Shared auth middleware exists but OpenAPI omits security requirements | BLOCKED for public or partner-facing docs. |
| Swagger UI is public by accident | BLOCKED. Add auth/admin/dev gating or document the public-docs decision. |
| Generated spec fails linting or has broken `$ref` values | BLOCKED before publishing. |
| A documented JSON or form body omits `415` while clients can send an undeclared `Content-Type` | WARNING. Document the 415 outcome or narrow the accepted media types. |
| A route declares the body optional but the handler assumes every field exists | BLOCKED. Set `body.required: true` or validate the absent-body case explicitly. |

## Request Body Contract

`@hono/zod-openapi` 1.6.x validates only JSON and form media types. Two behaviors belong in the documented contract:

- A request body whose `Content-Type` matches none of the route's declared media types is rejected with `415 Unsupported Media Type`. Earlier versions validated an empty object instead, so a client that sent the wrong header reached the handler.
- `request.body.required` defaults to `false`. A request with no body reaches the handler and `c.req.valid('json')` is `{}`. Set `required: true` when the body is mandatory; then an absent body fails with `400`.

Declare every accepted media type in `createRoute({ request: { body: { content: { ... } } } })`, and mirror both outcomes in the operation's response list when the client depends on them.

## Large-App Pattern

For `@hono/zod-openapi`, prefer feature-local route definitions and app-level registration. `openapiRoutes()` accepts `defineOpenAPIRoute()` results, which pair a `route` with its `handler`; a bare `createRoute()` object is not registrable this way.

```ts
// routes/users/routes.ts
import { createRoute, defineOpenAPIRoute } from '@hono/zod-openapi'

export const listUsersRoute = defineOpenAPIRoute({
  route: createRoute({
    method: 'get',
    path: '/',
    operationId: 'listUsers',
    tags: ['Users'],
    responses: {
      200: {
        description: 'Users returned',
        content: {
          'application/json': {
            schema: usersResponseSchema,
          },
        },
      },
    },
  }),
  handler: async (c) => {
    return c.json({ users: await listUsers() }, 200)
  },
})

export const userRoutes = [listUsersRoute] as const
```

```ts
// app.ts
const app = new OpenAPIHono()

app.openapiRoutes([...userRoutes, ...billingRoutes] as const)
app.doc('/doc', { openapi: '3.0.0', info: { title: 'API', version: '1.0.0' } })
app.get('/ui', swaggerUI({ url: '/doc' }))
```

When an RPC app grows past a few dozen routes, split it into small `OpenAPIHono` instances and mount them with `.route()`. A long chain of `.openapi()` calls accumulates schema type at every link, so a single giant app slows down `hc` type checking. Routing and OpenAPI output stay the same; only the accumulated type work shrinks.

```ts
const users = new OpenAPIHono().openapi(getUserRoute, getUserHandler)
const posts = new OpenAPIHono().openapi(getPostRoute, getPostHandler)

export const appRoutes = new OpenAPIHono().route('/', users).route('/', posts)
```

`get()`, `post()`, and `use()` return the `Hono` type rather than `OpenAPIHono`, so a chain that mixes them loses `.openapi()`. Wrap the result with `$()` or convert the type with `HonoToOpenAPIHono`.

```ts
import { $, OpenAPIHono } from '@hono/zod-openapi'

const app = $(new OpenAPIHono().use(requestIdMiddleware))
app.openapi(route, handler)
```

For `hono-openapi`, prefer route-local `describeRoute()` metadata and a single app-level `openAPIRouteHandler()` endpoint.

## Version and Package Caveats

- `@hono/zod-openapi` examples commonly show `app.doc()` with OpenAPI 3.0; use `app.doc31()` / `getOpenAPI31Document()` only when the project needs OpenAPI 3.1 output and the toolchain supports it. `getOpenAPI31Document()` takes generator options as its second argument, such as `unionPreferredType: 'oneOf'`.
- `@hono/zod-openapi` peers on Zod `^4.0.0` only. A repo still on Zod 3 must stay on `hono-openapi` or migrate Zod first; the two validators do not share a Zod major.
- `@hono/swagger-ui` serves UI, not the spec generator. Use `url` for one spec and `urls` for multiple specs. 0.6.2 escapes the title and string options it embeds in the page.
- `persistAuthorization`, `remoteAssets.baseUrl`, UI `version`, and custom HTML are deployment/UI knobs, not spec contract knobs.
- Plain `Hono` sub-apps nested under `OpenAPIHono` may not contribute OpenAPI metadata to the generated spec.
- When mounting nested OpenAPI sub-apps, parent `.route()` path params should use Hono `:param` syntax.
- Keep header schema keys lowercase so Hono validators and OpenAPI generators agree.
- `createRoute({ method: 'query' })` is available from 1.6.0; confirm the generated document's consumers accept a QUERY operation before publishing it.

## Review Checklist

- One generator strategy is used consistently
- Spec endpoint and Swagger UI endpoint are separate and intentional
- Route validators and documented schemas share a source or synchronization rule
- JSON and form bodies declare their media types, and 415 is documented where clients can trigger it
- `body.required` matches what the handler assumes
- Middleware chains that return plain `Hono` are wrapped with `$()` or `HonoToOpenAPIHono` before `.openapi()` is used
- Database row shapes are mapped to public DTO schemas before publication
- Reusable schemas, errors, security schemes, parameters, and examples use `components`
- Operation IDs are stable and unique
- Error responses match central error handling
- RPC `AppType`/typed client shapes do not conflict with generated OpenAPI shapes
- Large RPC surfaces are split across mounted `OpenAPIHono` instances when a single chain slows type checking
- CI or local verification lints, bundles, or validates the generated spec before publication

## Sources

> Checked 2026-11-04.

| Claim | Source |
|---|---|
| `@hono/zod-openapi` 1.6.3, `@hono/swagger-ui` 0.6.2, `hono-openapi` 1.5.0 versions and peer ranges | [npm registry: `@hono/zod-openapi`](https://registry.npmjs.org/@hono/zod-openapi), [npm registry: `@hono/swagger-ui`](https://registry.npmjs.org/@hono/swagger-ui), [npm registry: hono-openapi](https://registry.npmjs.org/hono-openapi) |
| 415 on an undeclared media type, `body.required` default, `$()` / `HonoToOpenAPIHono`, `defineOpenAPIRoute` / `openapiRoutes`, mounted-instance type performance, 3.1 generator options | [`@hono/zod-openapi` README](https://github.com/honojs/middleware/tree/main/packages/zod-openapi) |
| QUERY support in `createRoute()`, 415 fix in 1.6.3, type cost reductions in 1.6.1 and 1.6.2 | [`@hono/zod-openapi` releases](https://github.com/honojs/middleware/releases) |
| `hono-openapi` automatic 400 and header `resolver()` support | [`hono-openapi` releases](https://github.com/rhinobase/hono-openapi/releases) |
| Swagger UI escaping in 0.6.2 | [`@hono/swagger-ui` releases](https://github.com/honojs/middleware/releases) |
