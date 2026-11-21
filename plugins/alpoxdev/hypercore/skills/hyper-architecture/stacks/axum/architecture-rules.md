# Architecture Rules Reference

> Complete rule set for Axum hypercore projects

Note: some rules/axum below are stricter than axum defaults. They are hypercore team conventions, not universal framework requirements.

Brownfield adoption rule: untouched legacy code may be tracked as migration work instead of an immediate failure if the issue is stylistic or hypercore-specific. Safety, typing, validation, and transport-boundary issues still block immediately, especially in touched code.

---

## Forbidden

| Category | Forbidden |
|----------|-----------|
| Controllers | Introducing controller-style god modules or a trait-per-route abstraction when plain handler functions are enough |
| Routes | Scattered `Router::new()` fragments with no single composition function |
| Order | Registering a fallback before specific routes, or relying on registration order for path precedence without checking matchit specificity |
| Validation | Deserializing a body into a domain type and trusting it without a validation boundary |
| Database | Importing SQLx query macros, pools, or migration helpers directly from handlers |
| Migrations | Running or generating migrations from a request handler or at process start without an explicit policy |
| Typing | `unwrap()` or `expect()` on request-derived data, or untyped `serde_json::Value` crossing into domain logic |
| Errors | Leaking `sqlx::Error`, connection strings, or internal identifiers through the response body |
| OpenAPI | Public route changes without matching utoipa metadata when the repository publishes a spec |
| Platform | Binding a listener, reading secrets, or initializing tracing inside a route module |
| Paths | Rust modules or files named `camelCase` or `kebab-case` (`userProfile.rs`, `create-user.rs`) |
| Rust | `async_trait` on axum 0.8 extractors, `Box<dyn Error>` as a public handler error type, or `unsafe` without a stated invariant |
| Git | AI markers, emojis, multi-line commit messages |

---

## Architecture concern parity

The same architecture concerns apply across this repository's server stacks. In Axum they are owned as follows, so a multi-stack repository gets equivalent gates instead of stack-specific improvisation.

| Concern | Axum owner |
|---|---|
| Runtime edge / bootstrap | `main.rs` (or `bin/*.rs`) with tokio, listener, `axum::serve`, shutdown, tracing |
| Composition root | One `fn app(state) -> Router` or `build_router` function |
| Transport surface | `routes/*` handler functions and extractors |
| Use cases | `services/*` functions or structs |
| Persistence and external clients | `repositories/*`, `clients/*`, `db/*` |
| Contract | `openapi.rs` plus `utoipa` derives on DTOs |
| Error policy | One `AppError` with `IntoResponse` |
| Tests | `tests/*` integration, unit tests beside modules |

A stack translation keeps the concern, not the syntax: Hono middleware becomes tower layers, Hono validators become serde plus a validating extractor, Drizzle repositories become SQLx repositories, and `AppType`-style RPC typing becomes explicit DTO and OpenAPI types.

---

## Layer Architecture

```text
Bootstrap / Runtime Edge
  main.rs -> config, tracing, pool, state, serve, shutdown
       |
       v
Router Composition
  app.rs / lib.rs -> fn app(state: AppState) -> Router
       |
       v
Routes / Handlers / Extractors
  routes/<domain>.rs or routes/<domain>/mod.rs
       |
       v
Services / Use Cases
  services/<domain>.rs -> business decisions, transaction boundaries
       |
       v
Repositories / External Clients / Database Boundary
  repositories/<domain>.rs, clients/<provider>.rs
  db/pool.rs, migrations/
```

**Data flow rules:**
- Transport concerns stay in handlers, extractors, layers, and response shaping.
- Domain logic stays in services/use-cases.
- Storage and SDK logic stays in repositories or clients.
- Pool construction, SQLx query macros, schema ownership, and migration running stay in the database boundary and bootstrap.
- Handlers do not import `sqlx::query!`, `PgPool`, `sqlx::migrate!`, or table/module internals directly.
- Route modules should not grow into controller layers by default.

---

## Project Structure and Scalability

Read [`rules/axum/project-structure.md`](../../rules/axum/project-structure.md) before creating crates or modules, choosing a compact/service/workspace profile, changing ownership boundaries, moving a vertical slice, or designing a workspace.

Critical invariants remain here:

- Keep one composition function returning `Router` and one obvious place where state is applied.
- Dependencies flow from bootstrap to composition, route, service, repository, then database or external system.
- Routes own transport orchestration, not SQL, migrations, provider SDK details, or process startup.
- Lower layers do not import `axum` extractors or response types.
- Grow structure only from observable ownership or dependency pressure; do not pre-create empty layers.
- Preserve public paths, layer order, response shapes, and migration provenance during brownfield moves.
- Keep generated files and configured source, query, and migration roots in their tool-owned locations.

---

## Handler Typing Rules

### Preferred small-module pattern

```rust
pub fn routes() -> Router<AppState> {
    Router::new()
        .route("/users", get(list_users).post(create_user))
}
```

### Preferred extracted-handler pattern

```rust
pub async fn list_users(State(state): State<AppState>) -> Result<Json<Vec<UserDto>>, AppError> {
    let users = state.users.list().await?;
    Ok(Json(users))
}
```

### Core rule

- Handlers are plain `async fn` values; they must be `Send + Sync + 'static` and return an `impl IntoResponse`.
- Extractors run left to right; the single body-consuming extractor is last.
- `State` and `FromRef` substates come before body extractors.
- Return `Result<T, AppError>` rather than panicking or building ad-hoc error responses in handlers.
- Keep request parsing, validation, and service orchestration readable; a handler over ~50 lines usually hides a missing service.

---

## Validation Rules

- Use serde on the transport DTO, and a `validator` derive or an equivalent explicit check when rules/axum exceed type shape.
- Validate before domain logic consumes the payload; domain types should not be constructible from unvalidated input.
- Keep one validation-error envelope. `422 Unprocessable Entity` for semantically invalid input and `400 Bad Request` for malformed syntax are both defensible; pick one policy per API and document it.
- Validate `Path`, `Query`, headers, and multipart input, not only JSON bodies.
- Do not add or swap validation crates merely to match this skill.

## Database / SQLx Rules

- Treat persistence as a separate architecture boundary, not a handler implementation detail.
- Prefer `routes -> services -> repositories -> pool` for non-trivial persisted behavior.
- Use one shared pool created at bootstrap and stored in `AppState`; never connect per request.
- Keep query mode consistent: compile-time checked `sqlx::query!` with `DATABASE_URL` or committed `.sqlx` offline data, or runtime-checked `sqlx::query` with explicit row mapping. Do not mix silently.
- Keep migrations in the configured migrations directory and never edit an applied migration.
- Use explicit transactions for multi-step writes and pass the transaction handle into repositories.
- See `rules/axum/database.md` for detailed SQLx, migration, transaction, DTO, and non-compliance checks.

## OpenAPI / Swagger Rules

- Treat OpenAPI as an API contract, not a decorative docs page.
- Use `utoipa` derives on public DTOs and `#[utoipa::path]` on handlers, composed with `utoipa-axum` `OpenApiRouter` when the repository already uses it.
- Keep the runtime schema and the documented schema aligned; prefer one DTO source.
- Publish one canonical spec endpoint such as `/api-docs/openapi.json`.
- Serve Swagger UI from a separate route such as `/swagger-ui` and protect it according to the environment decision.
- Every documented operation should include a stable `operation_id`, tags, request schema, success responses, expected error responses, and useful examples.
- Put shared schemas, parameters, responses, examples, and security schemes under reusable components.
- Validate or lint the generated spec before publishing or using it for codegen.

---

## Middleware Rules

- axum has no bespoke middleware system; layers are tower services. Understand the order before adding one.
- `.layer()` calls wrap all previously added routes, so the last call is the outermost layer and requests meet it first.
- `ServiceBuilder` composes top to bottom: the first `.layer()` in the builder sees the request first.
- `route_layer` runs only when a route matches; `layer` also runs for unmatched paths. Use `route_layer` when a layer must not observe 404s.
- Shared auth, logging, request IDs, CORS, compression, and timeouts belong in layers.
- Fallible layers need `HandleErrorLayer` above them, because axum expects infallible services.
- State in `from_fn` middleware uses `from_fn_with_state`.
- Request-scoped data goes in request extensions or a typed extractor, never a mutable global.

---

## Error Handling Rules

- Define one `AppError` enum, translate domain and infrastructure errors into it, and implement `IntoResponse` once.
- Keep the public body stable: a machine code, a human message, and optional field errors. Never include SQL text, connection strings, or backtraces.
- Map `sqlx::Error::RowNotFound` deliberately; a missing row is usually `404`, not `500`.
- Add explicit `fallback` and, when the contract needs it, `method_not_allowed_fallback`.
- Log the internal cause with `tracing::error!` while returning the sanitized response.
- Do not `unwrap()` request-derived values; panics inside handlers abort the connection and hide the cause.

---

## Testing Rules

- Test the router directly with `tower::ServiceExt::oneshot`, which needs no port and covers layers and extractors.
- Use `axum-test` `TestServer` when the test benefits from a request builder, cookies, or multipart helpers.
- Use a real database or a transaction-scoped test schema for repository tests; never point tests at production.
- Cover the changed status codes, validation failures, and error envelope.
- Keep one integration test per documented public route family when OpenAPI publishing is part of the repository's contract.

---

## Platform Setup Rules

- Keep listener binding, config loading, tracing setup, pool creation, and graceful shutdown in `main.rs` or `bin/*.rs`.
- Provide state once with `.with_state(state)` and return `Router<()>` from the composition function.
- Use `axum::serve(listener, app).with_graceful_shutdown(...)`; do not hand-roll an HTTP loop.
- Type configuration explicitly and validate it at startup; avoid scattering `std::env::var` across handlers.
- Keep health and readiness endpoints cheap and independent of optional dependencies.
- Do not change async runtime, TLS backend, or deployment manifest inside an architecture review.

---

## Sources

> Checked 2026-11-05. No external source outside this package's own references informed this file; official axum, tower, SQLx, and utoipa behavior is delegated to [`references/official/axum/axum-docs.md`](../../references/official/axum/axum-docs.md), [`references/official/axum/tower-docs.md`](../../references/official/axum/tower-docs.md), [`references/official/axum/sqlx-docs.md`](../../references/official/axum/sqlx-docs.md), and [`references/official/axum/utoipa-docs.md`](../../references/official/axum/utoipa-docs.md), verified 2026-11-05.
