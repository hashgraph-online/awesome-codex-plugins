# Go CLI SQL Storage Guidelines

| Situation | Load |
|---|---|
| New local or server-backed storage | `workflows/build-sql-storage.md` |
| Schema or migration change | `workflows/apply-schema-migrations.md` |
| Flaky or incomplete DB tests | `workflows/test-sql-adapter.md` |
| Pool exhaustion or transaction bug | `references/sql-storage/knowledge.md`, `references/sql-storage/rules.md` |
| Custom database value type | `references/sql-storage/examples.md`, `references/sql-storage/rules.md` |
| Parallel CLI invocations share SQLite | `references/sql-storage/sqlite.md`, `workflows/test-sql-adapter.md` |
| Release changes the cache schema | `workflows/apply-schema-migrations.md`, then `go-cli-release-automation` |

## Boundary

- Use `go-cli-application-architecture` for general ports and composition.
- Use `go-idiomatic-api-design` for reusable public types and interfaces.
- Use `go-cli-testing` for overall CLI test layering.
- Use `go-cli-distribution` for cross-compilation and artifact packaging.
- Use `go-cli-release-automation` for tested-byte promotion and rollback gates.
- Use this skill for SQL adapters, pools, transactions, migrations, and real-driver proof.
