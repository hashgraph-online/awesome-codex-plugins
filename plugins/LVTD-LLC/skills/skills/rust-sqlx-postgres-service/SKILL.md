---
name: rust-sqlx-postgres-service
description: Use when adding, changing, testing, or reviewing Postgres persistence in Rust services that use sqlx, especially when designing migrations, query! or query_as! calls, PgPool injection, transactions, compile-time checked SQL, SQLx offline mode, repository boundaries, or database-backed integration tests.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Rust SQLx Postgres Service
  category: Rust
  tags: rust,sqlx,postgres,migrations,persistence
---

# Rust SQLx Postgres Service

Use this skill to make Rust/Postgres changes schema-first, compile-checked, and
testable. Prefer explicit migrations, injected pools, narrow repository
functions, and transaction boundaries that match the business operation.

## Core Workflow

1. Inspect `Cargo.toml`, `migrations/`, `.sqlx/`, `docker-compose.yml`, CI, and
   existing database helper modules before changing code.
2. Design the schema change first. Create or update a migration before writing
   repository code that depends on it.
3. Prefer `sqlx::query!` and `query_as!` for compile-time checked SQL. Use
   dynamic SQL only when the query shape truly changes at runtime.
4. Inject `PgPool`, `PgConnection`, or `Transaction` explicitly. Do not create a
   pool inside handlers or repository functions.
5. Keep repository functions small and named by behavior. Return domain types
   or persistence DTOs instead of leaking raw rows through the app.
6. Use a transaction for multi-step operations that must commit or roll back
   together.
7. Add or update integration tests that run migrations and exercise the public
   behavior when the change affects API semantics.
8. Run the bundled preflight script or the repository's equivalent SQLx/Cargo
   CI commands.

## Migration Rules

Read `references/migration-safety.md` before changing existing tables or data.

Default migration preferences:

- Use additive changes first: new nullable columns, new tables, new indexes.
- Backfill separately from schema creation when a table may be large.
- Add `not null`, uniqueness, and foreign-key constraints only after existing
  data satisfies them.
- Name constraints and indexes deliberately when they will appear in errors or
  operations.
- Keep down migrations if the project uses them; otherwise document rollback
  expectations in the migration review.

## Query Rules

Read `references/sqlx-patterns.md` for SQLx macro, transaction, and offline
mode details.

- Prefer bind parameters over string interpolation.
- Use `fetch_optional` for lookup-by-key operations.
- Use `execute` for inserts/updates where row data is not needed.
- Use `RETURNING` when the caller needs generated IDs or timestamps.
- Check affected row counts for updates and deletes that should target exactly
  one row.
- Map database uniqueness conflicts to domain errors near the repository edge.

## Verification

Run from the Rust project root when the standard SQLx workflow applies:

```bash
path/to/rust-sqlx-postgres-service/scripts/sqlx-preflight.sh
```

The script is conservative: it checks formatting and tests, inspects SQLx
migration state when the CLI and `DATABASE_URL` are available, verifies SQLx
offline metadata with `cargo sqlx prepare --check` when `.sqlx/` or
`DATABASE_URL` is available, and only applies migrations when
`RUST_SQLX_PREFLIGHT_RUN_MIGRATIONS=1` is set.

If the repository has a different CI command, use that command and explain why.

## Reference Files

- `references/sqlx-patterns.md`: `query!`, `query_as!`, pools, transactions,
  feature flags, and offline mode.
- `references/migration-safety.md`: safe migration sequencing and rollout
  checks.
