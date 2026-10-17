# SQL Storage Knowledge

## Pool Ownership

`*sql.DB` is a concurrency-safe connection pool, not one connection. Open it
once at the composition root, configure it deliberately, inject it into
adapters, and close it during application shutdown. `sql.Open` commonly
validates configuration without establishing connectivity; use a bounded
`PingContext` when startup requires a reachable database.

Pool limits behave like resource semaphores. Code that holds a transaction or
connection while requesting another can deadlock when the pool is exhausted.
Record pool statistics when diagnosing waits.

Classify the data before designing recovery. A reconstructible cache can be
quarantined and rebuilt. Offline edits, queued mutations, or other unique local
state are authoritative and require stronger durability, backup, and recovery.
Do not call authoritative state a cache.

## Transaction Ownership

The use case that requires atomicity owns the transaction boundary. Keep all
operations on the provided `*sql.Tx`; do not accidentally issue part of the
unit through `*sql.DB`. Roll back on every non-commit path and preserve the
primary error while observing commit or rollback failures appropriately.

## Portability

`database/sql` standardizes calls, not SQL dialects, placeholders, DDL,
generated IDs, locking, isolation, or constraint codes. Keep dialect and driver
details inside the adapter.

## Migrations

Embedding migration files makes them available in the binary. It does not
provide ordering, version recording, locking, atomicity, rollback, or
concurrent-start safety. Use a migration ledger and an explicit coordination
policy.

Overlapping old and new CLI processes make schema compatibility part of the
artifact contract. Prefer additive expand-first changes, record supported
reader/writer schema ranges, and make an older binary refuse incompatible
writes. A versioned database filename can be safer for a reconstructible cache.

## Custom Values

`Scanner` must handle documented source types and copy driver-owned byte slices
before retention. `driver.Valuer` must return an allowed value and must not
panic. Its errors are wrapped and remain inspectable with `errors.Is`.

Nullable columns require an explicit domain decision: `sql.Null[T]`, a
compatible concrete nullable type, a pointer where absence is meaningful, or a
query that normalizes null. Do not let scan behavior decide the contract
accidentally.

Parameterized execution—not manually preparing every statement—is the SQL
injection boundary. Drivers may prepare internally. Prepare explicitly for
reuse or driver-specific lifecycle reasons, then close the statement owner.
