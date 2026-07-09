---
name: sqlite-storage
description: Use when a val needs to store structured or relational data. Covers the std/sqlite API, parameterized queries, transactions, and the val-scoped vs organization-scoped database distinction.
triggers: [sqlite, database, sql, persistence, storage, table, query, migration]
---

# SQLite Storage

Val Town provides built-in SQLite via the `std/sqlite` module. Reach for it whenever a val needs relational or structured persistent data. For simple key/value data, prefer `std/blob` instead.

## Basic usage

```ts
import { sqlite } from "https://esm.town/v/std/sqlite/main.ts";

await sqlite.execute(`CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  email TEXT UNIQUE
)`);

await sqlite.execute({
  sql: "INSERT INTO users (name, email) VALUES (?, ?)",
  args: ["Alice", "alice@example.com"],
});

const result = await sqlite.execute("SELECT * FROM users");
// result.rows = [{ id: 1, name: "Alice", email: "alice@example.com" }]
```

## Transactions

Use `sqlite.batch` for atomic multi-statement transactions — all succeed or all roll back:

```ts
await sqlite.batch([
  { sql: "INSERT INTO users (name, email) VALUES (?, ?)", args: ["Bob", "bob@example.com"] },
  { sql: "UPDATE users SET name = ? WHERE id = ?", args: ["Robert", 2] },
]);
```

## Per-val vs organization databases

The import path determines which database you get. Both expose the same `@libsql/client` API (`execute`, `batch`) and return rows as keyed objects (`Record<string, unknown>[]`):

- `std/sqlite/main.ts` — **val-scoped** database, isolated to this val. The default for new vals, and what you almost always want.
- `std/sqlite/global.ts` — **organization-scoped** database, shared across every val owned by the same account. (Your personal account counts as its own organization here, so this database is shared across all of your vals.)

Do not switch an existing val between these import paths — it changes which database the val reads and writes.

## Querying org-owned vals via tools

When using the `sqlite_execute` or `sqlite_batch` tools to query a val owned by an organization (not your personal account), pass the org handle as the `org` parameter so the call hits the right database. Example: `{ sql: "SELECT * FROM users", org: "some-org" }`. This only matters for the tool calls — code inside the val itself reads from its own database automatically.

## Rules

- Always use parameterized queries (the `args` field) for any value derived from user input. Never interpolate strings into SQL.
- Use `CREATE TABLE IF NOT EXISTS` so schema setup is idempotent across val restarts.
- Schema migrations: add new columns with `ALTER TABLE ... ADD COLUMN`. Wrap in `try/catch` if the migration may run against an already-updated table.

## Reference

Full API docs: https://docs.val.town/reference/std/sqlite/usage/
