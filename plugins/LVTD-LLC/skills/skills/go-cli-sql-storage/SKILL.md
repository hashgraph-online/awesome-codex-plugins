---
name: go-cli-sql-storage
description: Design, implement, test, and ship SQL-backed persistence for Go CLIs using database/sql, explicit pool ownership, bounded startup checks, embedded migrations, transaction boundaries, parameterized queries, adapter error mapping, Scanner and Valuer types, SQLite or server databases, and real-driver integration tests. Use when a Go command stores durable state in SQL, initializes a local database, applies schema changes, or needs safe repository and transaction behavior.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.2.0"
  displayName: Go CLI SQL Storage
  category: Go
  tags: go,golang,cli,sql,database,storage
---

# Go CLI SQL Storage

Treat `*sql.DB` as a long-lived pool owned by the composition root. Keep SQL,
driver behavior, migrations, and sensitive connection details inside adapters.

## Core Workflow

1. Choose the database and driver from workload, platform, and distribution needs.
2. Define domain operations and transaction ownership before repository methods.
3. Open and configure one long-lived pool at the composition root.
4. Verify required startup connectivity with a bounded `PingContext`.
5. Apply versioned migrations using an explicit serialization policy.
6. Implement parameterized queries and map driver errors to stable domain errors.
7. Test consumers with fakes and adapters with the real driver and production schema.
8. Build the final artifact and smoke-test database initialization.

## Read Next

| Task | Load |
|---|---|
| Design storage for a CLI | `guidelines.md`, `workflows/build-sql-storage.md` |
| Add or change migrations | `workflows/apply-schema-migrations.md` |
| Test an adapter | `workflows/test-sql-adapter.md` |
| Review pools, transactions, queries, or conversions | `references/sql-storage/rules.md` |
| Understand driver and pool contracts | `references/sql-storage/knowledge.md` |
| Build a multi-process SQLite cache | `references/sql-storage/sqlite.md` |
| Review patterns | `references/sql-storage/examples.md` |

## Guardrails

- Do not treat `sql.Open` as a connectivity check.
- Do not interpolate untrusted values or identifiers into SQL.
- Do not treat embedded schema text as a migration system.
- Do not expose driver error types as the application contract.
- Do not use a broad repository interface that mirrors an adapter.
- Do not assume an in-memory SQLite database is shared across pooled connections.

## Source Notes

Guidance is transformed and paraphrased from Inanc Gumus, *Go by Example:
Programmer's Guide to Idiomatic and Testable Programs* (Manning, 2025),
Chapter 10. Examples are original.

Nullable values, row lifecycle, and pool guidance also incorporates transformed
material from Teiva Harsanyi, *100 Go Mistakes and How to Avoid Them* (Manning,
2022), Chapter 10.

Book: https://www.manning.com/books/go-by-example

Verify current contracts against https://pkg.go.dev/database/sql,
https://pkg.go.dev/database/sql/driver, and the selected driver's documentation.
For SQLite, also verify https://sqlite.org/wal.html,
https://sqlite.org/lang_transaction.html, and https://sqlite.org/backup.html.
