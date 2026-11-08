# Database and SQLx Boundary

> Keep persistence behind repositories and a shared, bootstrapped pool

---
## Stable SQLx Baseline

As verified on 2026-11-05, `sqlx` is 0.9.0 and its MSRV is 1.94. The 0.9 line separates runtime and TLS features (`runtime-tokio`, `tls-rustls`, `tls-native-tls`) instead of the old combined names, adds an optional `sqlx.toml` configuration file, and changes query functions to accept `impl SqlSafeStr`, so a dynamically built query needs `AssertSqlSafe`. The repository has moved from the `launchbadge` organization to `transact-rs`; old links redirect.

- Inspect `Cargo.toml`, `Cargo.lock`, the pool builder, the query style, the migrations directory, `.sqlx/` presence, and `DATABASE_URL` sourcing before changing persistence code.
- Decide the query mode once per crate: compile-time checked macros (`query!`, `query_as!`) with `DATABASE_URL` or committed `.sqlx` data, or runtime-checked `query`/`query_as` with explicit row mapping. Do not mix silently.
- The default `max_connections` is 10 and the default `acquire_timeout` is 30 seconds in the 0.9.0 source; these values are not stated in the rendered documentation, so state them as source-derived when reporting.
- A missing row is not an infrastructure failure. Map `sqlx::Error::RowNotFound` deliberately, usually to `404`.
- Build the pool once at bootstrap and store it in `AppState`. Cloning `Pool` is cheap because it is a reference-counted handle; connecting per request is not.
- Keep migrations committed and immutable. Never edit an applied migration or renumber history to make local state pass.
- Select only the columns the contract needs and map them into DTOs. Validate pagination bounds and make ordering deterministic.
- Test constraints, not-found and conflict mapping, rollback behavior, and the pool lifecycle at startup.

## Core Rule

Handlers own transport concerns only: extraction, validation, service calls, and response shaping. Services own use-case orchestration. Repositories own queries. The database boundary owns pool construction, query metadata, and migrations.

A handler importing `sqlx::query!`, `PgPool`, `SqlitePool`, `MySqlPool`, or `sqlx::migrate!` directly is a boundary violation unless the user explicitly asked for official defaults or a tiny proof of concept.

## Approved Placement

```text
src/
├── db/
│   ├── mod.rs
│   └── pool.rs              # pool construction and connection options
├── repositories/
│   └── users.rs             # queries, row mapping, no axum types
├── services/
│   └── users.rs             # transactions, cross-repository workflows
├── routes/
│   └── users/
│       ├── handlers.rs
│       └── dto.rs
└── main.rs                  # creates the pool, calls app(state)

migrations/
└── 20260101000000_create_users.sql
.sqlx/                       # committed when compile-time queries are used
```

- `db/pool.rs` builds the pool from typed configuration and is the only place that knows connection options.
- `repositories/<domain>.rs` owns SQL and maps rows into domain or DTO shapes.
- `services/<domain>.rs` owns transaction boundaries and business decisions.
- `routes/<domain>/` must not import the pool, query macros, or migrations.

## Pool Construction

```rust
use std::time::Duration;

use sqlx::postgres::PgPoolOptions;
use sqlx::PgPool;

pub async fn connect(database_url: &str) -> Result<PgPool, sqlx::Error> {
    PgPoolOptions::new()
        .max_connections(10)
        .min_connections(1)
        .acquire_timeout(Duration::from_secs(5))
        .connect(database_url)
        .await
}
```

- Read the URL from typed configuration, not from a handler.
- Set `acquire_timeout` below the request timeout so a saturated pool produces a fast, deliberate error instead of a hung request.
- Use `connect_lazy` only when startup must not block on the database, and document the failure mode.
- Never log the connection string; it usually contains credentials.

## Query Modes

| Mode | Use when | Requirements |
|---|---|---|
| `query!` / `query_as!` | The team wants compile-time SQL checking | `DATABASE_URL` at build time or committed `.sqlx` data; string-literal SQL |
| `sqlx::query` / `query_as` | Dynamic filters, runtime-built SQL, or no database in CI | Manual row mapping; never interpolate user input into SQL |
| `sqlx::query_as::<_, T>` with `FromRow` | A stable domain row type exists | Column names must match fields |
| `AnyPool` | The driver must be chosen at runtime | Accepts the reduced type coverage; rare in application code |

Offline mode:

1. `cargo install sqlx-cli`
2. With `DATABASE_URL` set and the database migrated: `cargo sqlx prepare` (or `--workspace`)
3. Commit `.sqlx/`
4. Build without `DATABASE_URL`; set `SQLX_OFFLINE=true` when a value might still be present
5. Gate CI with `cargo sqlx prepare --check`

In 0.9, `sqlx::query` takes `impl SqlSafeStr`, implemented for `&'static str` and `AssertSqlSafe`. A runtime-built query must be wrapped deliberately; the wrapper is a review flag, not a license to interpolate user input.

## Transactions

```rust
pub async fn transfer(&self, from: Uuid, to: Uuid, amount: i64) -> Result<(), AppError> {
    let mut tx = self.pool.begin().await?;

    sqlx::query("UPDATE accounts SET balance = balance - $1 WHERE id = $2")
        .bind(amount)
        .bind(from)
        .execute(&mut *tx)
        .await?;

    sqlx::query("UPDATE accounts SET balance = balance + $1 WHERE id = $2")
        .bind(amount)
        .bind(to)
        .execute(&mut *tx)
        .await?;

    tx.commit().await?;
    Ok(())
}
```

- Use an explicit transaction for multi-step writes that must commit or roll back as one unit.
- Put the transaction boundary in the service layer, not the handler.
- Pass `&mut *tx` or a generic executor into repositories that participate in the same transaction.
- A dropped transaction rolls back; relying on that for control flow hides intent, so commit or roll back explicitly.
- Avoid hidden nested transactions. Savepoints exist but should be intentional.

## Schema and Migrations

- `sqlx migrate add <name>` creates `migrations/<timestamp>_<name>.sql`; `-r` creates paired `.up.sql`/`.down.sql` files.
- `sqlx migrate run` applies pending migrations; `sqlx migrate revert` reverts the last one. Both need `DATABASE_URL` or `--database-url`.
- Keep the migrations directory at the workspace root unless the repository configures another source.
- Do not generate, run, or revert migrations from a request handler.
- Do not auto-rename tables, columns, indexes, or migration files as part of a route change.
- If a schema change affects public responses, update DTOs, validation, OpenAPI schemas, and tests in the same change.
- When `sqlx.toml` exists, treat it as the source of truth for query metadata, migration table names, and multi-database settings.

## DTO and Contract Boundary

- Database rows are not API DTOs. Map explicitly, and exclude internal IDs, soft-delete flags, audit columns, and secrets.
- OpenAPI schemas, validation DTOs, and response types should agree after persistence changes.
- Pagination, sorting, filtering, and partial selects belong in the query contract and in the documented parameters.
- Do not expose `sqlx::Error` text to clients; translate it in `AppError`.

## Non-Compliance Signatures

- A handler imports `sqlx::query!`, `PgPool`, `SqlitePool`, `MySqlPool`, or `sqlx::migrate!`
- A handler creates a pool or connection per request
- Repositories take `axum::extract::State` or build HTTP responses
- Migration files are generated but not committed, or the configured directory does not exist
- A service performs multiple dependent writes without a transaction
- Public responses serialize raw rows with internal fields
- `.sqlx/` is missing while `query!` macros are used in CI
- A runtime-built query interpolates user input instead of binding it
- Applied migrations were edited or renumbered

## Auto-Remediation Boundaries

Safe local fixes:

- Move a direct query from a handler into the existing repository for that domain.
- Add a missing repository function for a touched query.
- Replace a per-request pool with the shared `AppState` pool.
- Add DTO mapping for a touched public response when the target shape is clear.
- Add an explicit transaction around a touched multi-step write that already has tests.

Do not auto-apply without explicit justification:

- Switching SQLx for another ORM or driver, or swapping Postgres for another engine.
- Generating, editing, applying, or deleting production migrations.
- Renaming schema tables, columns, indexes, or migration folders.
- Rewriting transaction boundaries without tests.
- Introducing a new database abstraction layer across the crate.

## Review Checklist

- Touched handlers do not import SQLx macros or pool types
- Pool construction is centralized and executed once at startup
- Configuration flows from typed config, not `std::env::var` inside handlers
- Repository functions hide SQL and do not depend on axum types
- The query mode is consistent and `.sqlx` is committed when needed
- Transactions are explicit for multi-step writes
- Migration history is committed and unedited
- DTOs, OpenAPI schemas, and response types agree
- Persistence behavior is covered by the smallest useful repository, service, or request-level test

## Sources

> Checked 2026-11-05.

| Claim | Source |
|---|---|
| SQLx 0.9.0 MSRV 1.94, runtime and TLS feature split, `SqlSafeStr` and `AssertSqlSafe`, `sqlx.toml` | [SQLx CHANGELOG](https://github.com/transact-rs/sqlx/blob/main/CHANGELOG.md) |
| Pool behavior, `acquire_timeout`, `max_connections`, cheap clone | [Pool](https://docs.rs/sqlx/latest/sqlx/struct.Pool.html), [PoolOptions](https://docs.rs/sqlx/latest/sqlx/self/struct.PoolOptions.html), [v0.9.0 options source](https://github.com/transact-rs/sqlx/blob/v0.9.0/sqlx-core/src/pool/options.rs) |
| `query!` and `query_as!` compile-time checks, `DATABASE_URL`, offline mode | [query!](https://docs.rs/sqlx/latest/sqlx/macro.query.html), [query_as!](https://docs.rs/sqlx/latest/sqlx/macro.query_as.html) |
| Migration naming, `migrate run`/`revert`, `prepare --check`, CLI feature names | [sqlx-cli](https://github.com/transact-rs/sqlx/tree/main/sqlx-cli) |
| Transaction begin/commit/rollback and `&mut *tx` executor | [Transaction](https://docs.rs/sqlx/latest/sqlx/struct.Transaction.html) |
