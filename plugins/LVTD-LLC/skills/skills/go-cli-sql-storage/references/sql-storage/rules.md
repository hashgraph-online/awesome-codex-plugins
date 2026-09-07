# SQL Storage Rules

## Connections and Queries

- Open one long-lived pool and close it at application shutdown.
- Bound `PingContext`, queries, transactions, and migration operations.
- Do not treat a successful local SQLite ping as proof of schema compatibility,
  writability, integrity, or migration correctness.
- Configure pool limits from workload and driver behavior, then observe them.
- Use context-aware database methods.
- Close `Rows`, inspect `Rows.Err`, and handle scan failures.
- Remember that `QueryRowContext` reports errors at `Scan`.
- Close a newly opened pool when startup ping, configuration, or migration fails.
- Map nullable columns deliberately and gate `sql.Null[T]` on the supported Go version.
- Close explicitly prepared statements according to their owner.

## SQL Safety

- Parameterize values.
- Do not claim explicit `Prepare` is required for injection safety; parameters
  are the boundary and drivers may prepare internally.
- Allowlist dynamic identifiers and sort directions.
- Keep DSNs, credentials, and sensitive arguments out of errors and logs.
- Map documented driver codes to stable domain errors inside the adapter.
- Do not retry mutations without known outcome and idempotency.

## Transactions and Migrations

- Place transaction boundaries at the atomic use case.
- Never mix transactional and pool operations accidentally.
- Version migrations and record applied state.
- Serialize concurrent migration attempts.
- Verify the selected database's DDL transaction behavior.
- Make downgrade and backup expectations explicit.
- Define old/new binary overlap and supported reader/writer schema ranges.
- Do not raw-copy an active WAL database.

## Tests

- Apply the production migration path to the real test database.
- Give every parallel test unique database, file, or schema state.
- Test constraints, no rows, conversion errors, commit, rollback, and cancellation.
- Test nullable scans, `Rows.Err`, statement cleanup, and failed-startup pool cleanup.
- Test pool pressure and transaction behavior with deadlines.
- Run built-binary multi-process tests for shared SQLite files.
- Test interrupted migration, checksum mismatch, newer-schema rejection, and restart.
- Treat repository fakes as consumer tests, not adapter proof.
