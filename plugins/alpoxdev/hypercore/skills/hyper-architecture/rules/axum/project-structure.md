# Project Structure and Ownership

> Read this rule for crate or module design, composition ownership, feature growth, workspaces, or structural refactors. Official axum facts are summarized in [`../../references/official/axum/axum-docs.md`](../../references/official/axum/axum-docs.md); the layouts below are Hypercore conventions unless marked otherwise.

## Discovery commands

Run these before choosing a profile, applying a structural change, or reporting on an untouched crate. The target routing decision itself belongs to `rules/stack-detection.md`; this block only collects the facts the structure decision needs.

```bash
# is this an Axum server at all
rg -n '^axum\s*=|axum\s*=\s*\{|axum-extra' Cargo.toml */Cargo.toml
rg -n "use axum::|axum::Router|axum::serve|#\[derive\(.*FromRef" src crates
rg -n "tokio::main|Router::new\(\)|\.with_state\(" src crates
```

```bash
# persistence indicators, when a database is in scope
rg -n 'sqlx|sea-orm|diesel|tokio-postgres' Cargo.toml */Cargo.toml
rg -n "PgPool|MySqlPool|SqlitePool|query!|query_as!|\.begin\(\)|sqlx::migrate" src crates
ls migrations sqlx.toml .sqlx 2>/dev/null
```

```bash
# full-crate inventory for 전체 수정 mode
rg --files -g '*.rs' src crates 2>/dev/null
rg -n "Router::new\(\)|\.route\(|\.nest\(|\.merge\(|\.layer\(|\.route_layer\(|from_fn|with_state|FromRef|Json<|Query<|Path<|validate\(|sqlx::|AppError|IntoResponse|utoipa" src crates
```

If the first block finds nothing, the crate is not an Axum server and the Axum rules do not apply.

## 1. Choose a profile from repository evidence

Inspect the crate layout, binaries, `Cargo.toml` features and dependencies, module tree, composition function, state type, pool construction, migration directory, OpenAPI definition, tests, and current `use` graph. Preserve a coherent brownfield layout unless a touched boundary is unsafe or blocks the requested change.

Use the smallest profile that gives every dependency one clear owner:

| Profile | Use when | Add now |
|---|---|---|
| Compact | A small service with a few routes and little reusable domain or persistence logic | `main.rs`, `app.rs`, flat route modules, `state.rs`, `error.rs` |
| Service | Several domains, contributors, validation, persistence workflows, generated API docs, or background jobs | Domain route modules, service/repository boundaries, `db/`, `openapi.rs`, shared middleware |
| Workspace | Multiple deployables or a library consumed by another crate | Service structure inside the API crate plus a domain/contract crate when justified |

Do not pre-create every directory. Promote a folder or crate only when it has a distinct owner, dependency rule, or build contract. Empty layers and one-function pass-through trait abstractions are not scalability.

## 2. Ownership and dependency direction

```text
bootstrap -> router composition -> route/handler -> service/use case -> repository/client -> database/external system
```

| Concern | Default owner | Must not own |
|---|---|---|
| Runtime startup, listener, signals, tracing init | `main.rs`, `bin/*.rs` | Domain rules/axum or persistence policy |
| Root layers, fallback, version prefix, route mounting | `app.rs` or `lib.rs` composition function | Feature business logic |
| Path/method, extraction, auth gate, response shaping | `routes/<domain>` | SQL, pool creation, migration running |
| Business decisions, multi-step transactions | `services/<domain>` | `axum` extractors, `Json`, `Response`, headers |
| Queries and external SDK adaptation | `repositories/<domain>`, `clients/<provider>` | HTTP response shaping or route registration |
| Pool lifecycle, migrations, SQL schema | `db/`, `migrations/` | Request routing |
| Shared DTOs, utoipa schemas, spec composition | `openapi.rs`, `dto/` | Duplicated per-route schema copies |

Dependencies point downward. Lower layers do not import `axum` transport types. Feature route modules do not import another feature's route module; cross-feature workflows meet in a service or a deliberately shared contract type.

## 3. Compact layout

```text
src/
├── main.rs             # tokio main, config, tracing, pool, serve, shutdown
├── app.rs              # fn app(state: AppState) -> Router
├── state.rs            # #[derive(Clone)] AppState
├── error.rs            # AppError + IntoResponse
└── routes/
    ├── mod.rs
    ├── health.rs
    └── users.rs
```

A compact route may call a small pure helper directly. Add a service or repository only when business decisions, reuse, persistence, transactions, or external SDK behavior justify the boundary.

## 4. Service layout

```text
src/
├── main.rs
├── app.rs              # sole composition function
├── config.rs           # typed, validated configuration
├── state.rs            # AppState: config, pool, clients
├── error.rs
├── telemetry.rs        # tracing subscriber setup
├── middleware/
│   ├── mod.rs
│   ├── auth.rs
│   └── request_id.rs
├── routes/
│   ├── mod.rs          # mount table only
│   ├── health.rs
│   └── users/
│       ├── mod.rs      # routes() -> Router<AppState>
│       ├── handlers.rs
│       ├── dto.rs
│       └── tests.rs
├── services/
│   └── users.rs
├── repositories/
│   └── users.rs
├── clients/
│   └── mail.rs
├── db/
│   └── pool.rs
└── openapi.rs

migrations/
└── 20260101000000_create_users.sql
```

The tree is illustrative; configured binary names, module roots, query metadata (`.sqlx/`), and migration directories win.

## 5. Feature growth thresholds

| Pressure | Structural response |
|---|---|
| One tiny operational endpoint | Keep one route module |
| Validation or several handlers appear | Promote to `routes/<domain>/` and colocate DTOs and handlers |
| Business behavior is reused or independently testable | Add `services/<domain>` following the existing repository pattern |
| Persistence or provider calls appear | Add a repository/client boundary; handlers must not import pools, query macros, or provider SDKs |
| Two domains reuse a transport-agnostic type | Promote that type to a purpose-named module such as `dto/` or `domain/`; do not create a generic `utils/` dumping ground |
| Multiple domains reuse a layer or error mapping | Promote only the reused primitive to `middleware/` or `error.rs` |
| A second crate consumes the contract | Consider a workspace crate; do not expose internal repository modules across crate boundaries |

Do not split by file count alone. A cohesive feature can remain colocated; a large file with mixed transport, business, and persistence ownership must be separated even if used once.

## 6. Composition and type surface

Keep exactly one obvious composition path:

```rust
pub fn app(state: AppState) -> Router {
    Router::new()
        .merge(routes::health::routes())
        .nest("/api/v1", api_routes())
        .layer(tower_http::trace::TraceLayer::new_for_http())
        .fallback(handlers::not_found)
        .with_state(state)
}
```

- Put `/api` and version prefixes at the composition boundary, not inside every feature module.
- Register root layers once, before the fallback.
- Keep `main.rs` thin enough that tests can call `app(test_state)` without binding a port.
- Return `Router<()>` from the composition function after `with_state`; return `Router<AppState>` from feature modules.
- When the OpenAPI definition is generated from the router, compose it from the same route definitions to avoid drift.

## 7. Workspace layout

```text
crates/
├── api/                # binary or lib exposing the Router; owns runtime and implementation
├── domain/             # pure types and rules; no axum, no sqlx
└── persistence/        # SQLx repositories and migrations when independently built
```

Keep `axum`, `tokio`, and `sqlx` major versions aligned across crates; enable workspace dependency inheritance where the repository already does. A consumed library crate must not export secrets, pool internals, or server-only implementation modules.

## 8. Brownfield migration

1. Map actual binaries, composition functions, state wiring, module tree, migrations, and generated metadata.
2. Identify ownership violations and cycles before moving files.
3. Preserve public paths, layer order, error behavior, response shapes, and migration provenance.
4. Move one vertical slice at a time and update `mod` declarations and imports atomically.
5. Run focused route and repository tests after each slice; keep the slice only when behavior and gates pass.
6. Record untouched Hypercore-only drift as backlog when broad movement would exceed the request. Safety, validation, typing, persistence, and runtime-boundary violations in touched code still block.

This is a bounded migration loop: feedback is focused tests plus import-boundary inspection; the guard is unchanged public behavior and contracts; the maximum iterations equal the planned slices; discard or revert a slice that fails its guard before continuing.

## 9. Structural verification

- Confirm one composition function and one place where state is applied.
- Confirm every route has an unambiguous owner and the fallback is last.
- Search handlers for `sqlx::`, `PgPool`, `MySqlPool`, `SqlitePool`, and `migrate!`.
- Search services and repositories for `axum::` extractor or response types.
- Check module declarations, `Cargo.toml` feature flags, and migration paths against configuration.
- Run `cargo check` plus focused route and repository tests for moved modules.
- When OpenAPI is present, verify the generated document still contains representative paths and error shapes.
- Report untested binaries, databases, migrations, or generated artifacts explicitly; do not infer success from file layout alone.

## Sources

> Checked 2026-11-05. No external source outside this package's own references informed this file; official axum behavior is delegated to [`references/official/axum/axum-docs.md`](../../references/official/axum/axum-docs.md), verified 2026-11-05.
