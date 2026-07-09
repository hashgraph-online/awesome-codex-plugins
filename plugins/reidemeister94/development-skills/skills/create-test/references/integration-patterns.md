# Integration Patterns — Real Database Testing

Testcontainers setup, asyncpg pool/transaction fixtures, `make_` factory fixtures, and `MagicMock(spec=)` seams are team-canonical — use `../python-dev/patterns.md` (Testing section). This file covers only what is not there: the PostgreSQL isolation decision and migration round-trips.

## PostgreSQL test-isolation decision

The cleanup strategy is dictated by whether the code under test commits and whether the test needs DDL:

```
Does the code under test issue an explicit COMMIT?
├── No  → Transaction rollback (default, fastest: begin per test, rollback on teardown)
└── Yes → Does the test need DDL (ALTER TABLE, CREATE INDEX)?
          ├── No  → TRUNCATE CASCADE all tables in reverse-FK order on teardown
          └── Yes → Template-DB clone: CREATE DATABASE ... TEMPLATE testdb per test (~87ms)
```

Run the Postgres container on tmpfs (`--tmpfs /var/lib/postgresql/data`) — ~23x faster than disk, which is what makes the template-clone path viable.

## Safety guard
Autouse fixture asserting `"test"` or `"localhost"` is in the DB URL, so tests fail fast rather than ever touching a non-test database.

## Migration round-trip (Alembic)
`alembic upgrade head && alembic downgrade base && alembic upgrade head` must succeed = reversible. Also test per-revision `downgrade -1 / upgrade +1`, and that seeded data survives the migration under test.
