# Schema Changes

Use this rule before writing or approving any DDL, migration, backfill, or index build on a table, collection, or key space that holds data. It is engine-neutral; the engine guide names the exact lock or algorithm each statement takes. Findings cite the `SC-*` IDs below.

## 1. Principles

| ID | Severity | Rule |
|---|---|---|
| SC-01 | critical | Never ship a change that breaks the application version currently running. Old and new code must both work during the deploy window: expand first, migrate data, switch code, contract last (parallel change). |
| SC-02 | high | One migration does one kind of thing. Do not mix a schema change, a data backfill, and an index build in one transaction or one file. |
| SC-03 | high | Every DDL on a busy table sets a short lock wait (`lock_timeout`, `lock_wait_timeout`, or the engine's equivalent) and a statement timeout, so it fails fast and retries instead of queueing behind a long transaction and blocking every query after it. |
| SC-04 | high | Backfills run in bounded batches by primary key range, commit per batch, sleep or throttle between batches, and are idempotent and resumable. Never one `UPDATE` over the whole table. |
| SC-05 | high | Every step has a written rollback, or is marked one-way with the data it loses. Dropping a column, a table, or a key family is one-way: take a backup or keep a copy until the next release proves nothing reads it. |
| SC-06 | medium | Generated migrations from an ORM are reviewed as SQL before they run; the tool's output is a draft, not a decision. |
| SC-07 | medium | Rehearse a change that rewrites or scans a large table on a copy with production-like volume, and record the duration. |

## 2. Change Classes

| Class | Examples | Default procedure |
|---|---|---|
| Additive, metadata-only | add a nullable column; add a column with a constant default where the engine stores it as metadata; add a table; create a view | One step; still set the lock timeout (SC-03) |
| Additive, scanning | add `NOT NULL`, a `CHECK`, or a foreign key to existing data; add a unique constraint | Add it unvalidated or as a separate unique index built online, then validate in a second step |
| New required column | add a column that must be `NOT NULL` but has no constant default | Add it nullable (or with a constant default when the engine stores that as metadata), deploy writers that fill it, backfill old rows in batches (SC-04), then add the constraint unvalidated and validate it; one migration file per step, each step its own deploy |
| Index build | create or drop an index | The engine's online build (`CONCURRENTLY`, `ALGORITHM=INPLACE, LOCK=NONE`, background index build); never inside a transaction where the engine forbids it |
| Rewriting | change a column type, add a column whose default is volatile, reorder or recluster | Expand/contract with a new column or table, dual write, backfill, switch, contract; or an online schema-change tool |
| Renaming | rename a column or a table | Expand/contract: add the new name, dual write or a view, backfill, switch readers, drop the old name in a later release |
| Destructive | drop a column, a table, an index used by a query, or a key family | Stop reading and writing it in code first, deploy, wait one release, then drop; confirm no query plan uses a dropped index |
| Data-only | bulk update, delete, or move | Batched backfill (SC-04) with a dry-run count first |

## 3. Expand/Contract Template

1. **Expand**: add the new column, table, index, or key shape. Nothing reads it yet.
2. **Dual write**: the application writes both old and new shapes (or a trigger does, documented as temporary).
3. **Backfill**: copy existing data in batches (SC-04); verify counts and a checksum or sample comparison.
4. **Switch reads**: read from the new shape behind a flag; watch errors and latency.
5. **Stop old writes**: remove writes to the old shape.
6. **Contract**: drop the old shape after a full release cycle with no reads, with a backup if the data is not reproducible.

Each step is its own deploy. Steps 1, 2, and 4 are reversible by code; steps 5 and 6 are the point of no return and are called out in the report.

## 4. NoSQL and Key-Value Changes

| ID | Severity | Rule |
|---|---|---|
| SC-20 | high | Schemaless stores still have a schema in code. Version documents or items (`schemaVersion`) and make readers accept both versions until a backfill finishes. |
| SC-21 | high | Changing a partition, shard, or hash key means a new table or collection and a migration of every item; plan it as expand/contract with dual writes. |
| SC-22 | medium | Changing a Redis or Valkey key format writes the new key, reads new-then-old during a TTL window, and lets old keys expire; never rename keys in place with a scan in production hours. |
| SC-23 | medium | Adding a DynamoDB GSI or a MongoDB index on a large collection backfills in the background and consumes capacity; schedule it and watch throttling or replication lag. |

## 5. Review Checklist

Use [rules/validation.md](validation.md) §3. A change is not safe until every line there is answered.

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| Parallel change (expand, migrate, contract) | <https://martinfowler.com/bliki/ParallelChange.html> |
| Evolutionary database design and migrations as code | <https://martinfowler.com/articles/evodb.html> |
| `lock_timeout` aborts a statement that waits longer than the limit for a lock | <https://www.postgresql.org/docs/current/runtime-config-client.html> |
| `CREATE INDEX CONCURRENTLY` builds without blocking writes and cannot run inside a transaction block | <https://www.postgresql.org/docs/current/sql-createindex.html> |
| MySQL online DDL algorithms and lock clauses | <https://dev.mysql.com/doc/refman/8.4/en/innodb-online-ddl-operations.html> |
| The change classes, IDs, and severities | this package's chosen design, not a validated optimum |
