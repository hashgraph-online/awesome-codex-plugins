# Architecture Rules Reference

> Complete rule set for Hono hypercore projects

Note: some rules/hono below are stricter than Hono defaults. They are hypercore team conventions, not universal framework requirements.

Brownfield adoption rule: untouched legacy code may be tracked as migration work instead of an immediate failure if the issue is stylistic or hypercore-specific. Safety, typing, validation, and transport-boundary issues still block immediately, especially in touched code.

---

## Forbidden

| Category | Forbidden |
|----------|-----------|
| Controllers | Introducing controller-heavy classes/files when simple route modules or handler factories are enough |
| Routes | Scattered registration with no clear composition entry |
| Order | Registering fallback/catch-all routes before specific routes |
| Validation | Repeated raw `c.req.json()` parsing in non-trivial handlers |
| Database | Importing DB/ORM clients, Drizzle schema tables, pools, or migration helpers directly from routes/handlers |
| Migrations | Generating, pushing, or running database migrations from request handlers |
| Typing | Untyped `c.set()` / `c.get()` variables across middleware/handlers |
| Errors | Missing central error policy in non-trivial APIs |
| OpenAPI | Public API route changes without matching OpenAPI/Swagger contract updates when the repo publishes docs |
| RPC | Breaking `AppType` / `testClient` / `hc` inference by losing chained types |
| Platform | Mixing runtime adapter/bootstrap code into route modules |
| Paths | camelCase or PascalCase source folders/files (`userProfile.ts`, `createUser.ts`, `routes/UserProfile/`) |
| TypeScript | `any` type, `function` declaration when a const arrow function is appropriate |
| Git | AI markers, emojis, multi-line commit messages |

---

## Layer Architecture

```text
Runtime Edge / Adapter
  index.ts / server.ts / worker.ts
       |
       v
Hono App Composition
  app.ts -> app.route('/users', usersApp)
       |
       v
Route Modules / Handlers
  routes/<domain>/index.ts
       |
       v
Services / Use Cases
  services/<domain>/*.ts
       |
       v
Repositories / External Clients / Database Boundary
  repositories/<domain>/*.ts, clients/*.ts
  database/client.ts, database/schema.ts, drizzle/migrations
```

**Data flow rules:**
- Transport concerns stay in routes, handlers, middleware, and response shaping
- Domain logic stays in services/use-cases
- Storage/SDK logic stays in repositories or clients
- Database connection setup, ORM configuration, schemas, and migrations stay in the database boundary
- Routes do not import database clients, Drizzle table definitions, driver clients, or migration helpers directly
- Route modules should not grow into controller layers by default

---

## Project Structure and Scalability

Read [`rules/hono/project-structure.md`](../../rules/hono/project-structure.md) before creating folders, choosing a compact/product/workspace profile, changing ownership boundaries, moving a vertical slice, or designing a monorepo contract package.

Critical invariants remain here:

- Keep one runtime-neutral app composition surface and one obvious mount table.
- Dependencies flow from runtime entry to app composition, route, service/use case, repository/client, then database/external system.
- Routes own transport orchestration, not ORM queries, migrations, provider SDK details, or runtime startup.
- Lower layers do not import Hono `Context` or raw request/response concerns.
- Grow structure only from observable ownership or dependency pressure; do not pre-create empty layers.
- Preserve public paths, middleware order, `AppType`, OpenAPI output, and migration provenance during brownfield moves.
- Keep generated files and configured source/schema/migration roots in their tool-owned locations.

---

## Handler Typing Rules

### Preferred small-module pattern

```ts
const usersApp = new Hono()
  .get('/', listUsers)
  .post('/', createUser)
```

### Preferred extracted-handler pattern

```ts
const factory = createFactory<Env>()

const handlers = factory.createHandlers(listUsers, createUser)

const usersApp = factory
  .createApp()
  .get('/', ...handlers)
```

### Core rule

- If handlers are extracted, keep typing intact with `createFactory()` / `createHandlers()`
- Type `Bindings` and `Variables` explicitly when middleware or runtime context depends on them
- Keep request parsing, validation, and service orchestration readable

---

## Validation Rules

- Use validator middleware on params, query, headers, form, or json before domain logic consumes them
- Official Hono docs recommend third-party validators for stronger schemas
- Preferred options:
  - `validator()` for narrow built-in checks
  - `@hono/zod-validator` for Zod-based repos
  - `@hono/standard-validator` when the repo already standardizes on Standard Schema libraries
- Keep validation strategy consistent within a feature

## Database / ORM Rules

- Treat persistence as a separate architecture boundary, not a route implementation detail.
- Prefer `routes -> services -> repositories -> database client` for non-trivial persisted behavior.
- Use the runtime-appropriate Drizzle driver or database client; do not hardcode Node-only database setup in edge routes.
- For Cloudflare Workers/D1, database bindings should flow through typed Hono `Bindings` / `c.env`.
- For Node/serverful runtimes, pools and clients should be created at module or bootstrap scope, not per request.
- For serverless runtimes that reuse module scope, keep reusable clients and prepared statements outside handler scope when the provider supports it.
- Keep Drizzle schema and generated migrations in a stable database/migration boundary and review generated SQL before merging.
- Use explicit service-layer transactions for multi-step writes and pass the `tx` handle into repositories.
- See `rules/hono/database.md` for detailed Drizzle, migration, transaction, DTO, and non-compliance checks.

## OpenAPI / Swagger Rules

- Treat OpenAPI as an API contract, not a decorative docs page.
- Use `@hono/zod-openapi` for Zod-first repos or `hono-openapi` when the repo already uses multiple Standard Schema-compatible validators.
- Keep the validation schema and documented schema aligned; prefer one schema source when practical.
- Publish one canonical spec endpoint such as `/doc` or `/openapi.json`.
- Serve Swagger UI from a separate route such as `/ui` and protect it according to the environment and product decision.
- Every documented operation should include stable `operationId`, `tags`, request schema, success responses, expected error responses, and useful examples.
- Put shared schemas, parameters, responses, examples, and security schemes under reusable OpenAPI components.
- In large apps, compose per-feature OpenAPI route metadata at the app boundary instead of manually copying spec fragments.
- Validate or lint the generated spec before publishing or using it for codegen.

---

## Middleware Rules

- Registration order matters; middleware and handlers run in the order they are added
- Shared auth/logging/request-id/CORS concerns belong in middleware
- `Context` is per-request; never treat `c.set()` state as cross-request storage
- Type middleware-provided variables via app/factory generics

---

## Error Handling Rules

- Add a central `app.onError()` policy in non-trivial APIs
- Use `HTTPException` or an equivalent explicit translation path for expected HTTP failures
- When rebuilding responses from `HTTPException`, preserve headers already set on `Context`
- Keep not-found handling compatible with typed RPC when the app exports a client surface

---

## Testing / RPC Rules

- `testClient()` type inference depends on route types flowing through chained app definitions
- `hc<AppType>` and `AppType` exports need stable typed app composition
- In larger applications, split by sub-apps carefully and preserve typed mounting patterns
- Do not casually break route typing with detached registration
- Use request-level tests such as `app.request()` for route behavior and typed clients for contract behavior when the app exposes RPC surfaces
- Keep explicit response statuses so RPC clients and OpenAPI docs agree on status-specific payloads

---

## Platform Setup Rules

- Keep the runtime adapter in `index.ts`, `server.ts`, `worker.ts`, or another edge bootstrap file
- Type environment bindings and config explicitly
- Keep `showRoutes()` and similar dev helpers behind explicit dev-only setup
- Use `basePath()` / version prefixes intentionally, not ad hoc per handler
