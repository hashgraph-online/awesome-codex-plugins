# Route Structure

> Axum route composition rules/axum

---
## Stable axum 0.8 Baseline

As verified on 2026-11-05, axum is 0.8.9 and requires Rust 1.80 or later. Path parameters use `{name}` and wildcards use `{*rest}`; the 0.7 `:name` and `*rest` syntax panics at startup instead of silently changing behavior. Matching is handled by `matchit`, so precedence comes from path specificity, not from the order in which `.route()` was called.

- Keep one `routes()` function per feature returning `Router<AppState>`, and one root composition that merges or nests them.
- Do not assume registration order decides which route wins. Static segments beat parameters, and parameters beat wildcards; verify overlapping routes with a test.
- `nest("/api", router)` prefixes the inner router and keeps the outer state type; the inner router must be `Router<AppState>` when it extracts the shared state.
- `merge(other)` combines paths and fallbacks; use it for sibling feature routers and `nest` for a real prefix boundary.
- `route_service(path, service)` is for an arbitrary tower service; ordinary handlers use `.route()`.
- `fallback(handler)` handles unmatched paths. It is independent of route registration order, but it must exist exactly once at the root unless a nested router intentionally owns its own.
- `method_not_allowed_fallback(handler)` handles a known path with an unsupported method; without it axum returns 405 with an `Allow` header and an empty body.
- `Router::layer` applies to everything added before it, including the fallback; `Router::route_layer` applies only when a route matches. Choose deliberately.
- Keep version prefixes at the composition boundary. Do not repeat `/api/v1` inside every feature module.
- axum 0.8 removed the `Host` extractor to `axum-extra`; do not design host routing around a core import.

## Preferred Small Structure

```text
src/
├── app.rs
├── main.rs
└── routes/
    ├── mod.rs
    ├── health.rs
    └── users.rs
```

## Preferred Large Structure

```text
src/routes/
├── mod.rs              # mount table; no business logic
├── health.rs
├── users/
│   ├── mod.rs          # pub fn routes() -> Router<AppState>
│   ├── handlers.rs
│   ├── dto.rs
│   └── tests.rs
└── billing/
    ├── mod.rs
    ├── handlers.rs
    ├── dto.rs
    └── service.rs
```

`routes/mod.rs` or `app.rs` remains the only mount table. Feature folders own their handler functions, DTOs, and feature-only layers.

## Rules

- `app.rs` or `lib.rs` owns root composition; `main.rs` only bootstraps it
- `routes/mod.rs` is the single obvious mount table
- Prefer feature `routes()` functions merged at the root over one giant `Router::new()` chain
- Use a route folder when a feature needs more than one file
- Single-file routes are acceptable for tiny operational endpoints
- Split a route into a folder when it has two or more handlers, a request DTO, feature middleware, OpenAPI metadata, or service orchestration
- Keep version prefixes at the composition boundary
- Do not import SQLx query macros, pools, or migration helpers from route modules
- Do not import one feature route module from another feature route module
- Register the root fallback once; do not scatter fallbacks across nested routers
- Never rely on call order for path precedence; `matchit` decides, and conflicting routes panic at startup

## Mounting Pattern

```rust
use axum::Router;

use crate::routes::{billing, health, users};
use crate::state::AppState;

pub fn app(state: AppState) -> Router {
    Router::new()
        .merge(health::routes())
        .nest("/api/v1", api_routes())
        .fallback(crate::handlers::not_found)
        .with_state(state)
}

fn api_routes() -> Router<AppState> {
    Router::new()
        .merge(users::routes())
        .merge(billing::routes())
}
```

## Scale-Up Pattern

```rust
// routes/users/mod.rs
use axum::{routing::get, Router};

use crate::state::AppState;

mod handlers;

pub fn routes() -> Router<AppState> {
    Router::new()
        .route("/users", get(handlers::list).post(handlers::create))
        .route("/users/{id}", get(handlers::get).patch(handlers::update))
}
```

```rust
// routes/mod.rs
pub mod billing;
pub mod health;
pub mod users;
```

## Non-Compliance Signatures

- `Router::new()` fragments appear in unrelated files with no single composition function
- A feature module builds its own listener, pool, or tracing subscriber
- Route modules import `sqlx::query!`, `PgPool`, or `sqlx::migrate!`
- Fallbacks are defined in several nested routers with different bodies
- A route file contains DTOs, long handlers, feature layers, and business logic
- Version prefixes are repeated inside every feature instead of defined once
- Registration order is used as an implicit precedence mechanism
- `route_layer` is used where the layer must also cover unmatched paths, or `layer` where it must not

## Review Checklist

- One obvious composition function exists
- Mounting uses `merge` for siblings and `nest` for a real prefix
- The root fallback is defined once and returns the standard error envelope
- Path parameters use `{name}` syntax and overlapping routes are tested
- 405 behavior is either absent by design or handled deliberately
- Large features use sub-app modules, not giant flat files
- Feature boundaries are clear enough that new routes have an obvious home
- Persistence work flows through service/repository boundaries when the route is not trivial
- Route structure still allows `app(test_state)` to be tested without a port

## Sources

> Checked 2026-11-05.

| Claim | Source |
|---|---|
| Path syntax change to `{param}` / `{*wildcard}`, the panic on old syntax, `route_service`, `nest`, `merge`, `fallback`, `method_not_allowed_fallback`, `route_layer` | [axum Router](https://docs.rs/axum/latest/axum/struct.Router.html), [axum 0.8.0 changelog](https://github.com/tokio-rs/axum/blob/main/axum/CHANGELOG.md) |
| `matchit`-based precedence and conflict panics | [axum Router](https://docs.rs/axum/latest/axum/struct.Router.html), [matchit](https://docs.rs/matchit/latest/matchit/) |
| 0.8.9 minimum Rust version 1.80 | [axum 0.8.9 changelog](https://github.com/tokio-rs/axum/blob/main/axum/CHANGELOG.md) |
| `Host` extractor moved to `axum-extra` in 0.8 | [axum 0.8.0 changelog](https://github.com/tokio-rs/axum/blob/main/axum/CHANGELOG.md) |
