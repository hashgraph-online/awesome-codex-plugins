# Database Test Isolation

Use this reference when Rust API tests write to a real database.

## Goals

- Tests can run repeatedly without depending on previous runs.
- Tests can run in parallel without corrupting each other.
- Test behavior matches production database semantics closely enough to catch
  query, constraint, transaction, and migration bugs.

## Preferred Pattern: Disposable Logical Database

Use this when the application talks to Postgres through a pool and the test
cannot wrap all queries in a single transaction.

1. Load the normal test configuration.
2. Replace the database name with a unique value, usually a UUID.
3. Connect to the Postgres server without selecting that database.
4. Create the logical database.
5. Connect a pool to the new database.
6. Run migrations.
7. Start the application with that pool or with configuration pointing to that
   database.

This costs more than a transaction rollback, but it keeps API tests simple and
works with connection pools, background tasks, and request handlers that acquire
their own connections.

## Transaction Rollback Pattern

Use this mostly for repository/unit tests where the test controls the exact
connection used by the code under test.

1. Begin a transaction.
2. Pass `&mut Transaction<'_, Postgres>` or a compatible executor into the code.
3. Assert behavior.
4. Roll back at the end of the test.

Avoid this for black-box HTTP tests if the running app obtains connections from
a `PgPool` that the test cannot intercept.

## Migration Rules

- Run migrations in test setup instead of assuming a developer already ran them.
- Keep migrations committed and deterministic.
- Prefer additive migrations for deployed services: add nullable columns first,
  deploy code that writes them, backfill, then add stricter constraints.
- When using `sqlx::migrate!`, keep the migrations path valid from the crate or
  workspace where tests execute.

## Cleanup

Choose one policy and make it explicit:

- Drop the logical database at test teardown when the suite creates many large
  records or runs in shared CI infrastructure.
- Leave disposable databases behind for local speed and post-failure inspection
  when the test Postgres instance is easy to reset.

If cleanup is best-effort, never let cleanup failures hide the original test
failure.

## Common Failure Modes

- A fixed database name makes tests order-dependent.
- A fixed HTTP port makes tests fail when another process is running.
- Migrations are skipped locally and only fail in CI.
- Tests use SQLite while production uses Postgres-specific constraints,
  isolation, JSON, arrays, or enum behavior.
- Test setup uses `.env` values from a developer machine instead of explicit
  test configuration.
