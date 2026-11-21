# PostgreSQL

Engine guide for PostgreSQL, self-hosted or managed (RDS, Cloud SQL, Azure, Neon, Supabase, PlanetScale Postgres, and others), including pgvector, PostGIS, and TimescaleDB. Read it after `rules/engine-detection.md` routes here, together with the engine-neutral rule the mode needs. Findings cite the `PG-*` IDs.

## 1. Dated Facts

> Volatile. Checked 2026-11-07 against <https://www.postgresql.org/support/versioning/>; recheck the live page when an upgrade or end-of-life decision depends on it.

| Fact | Value |
|---|---|
| Support window | Each major version is supported for 5 years after its first release |
| Current major | 18 (first release 2025-09-25, current minor 18.6); 19 was at RC 1 on 2026-10-15 |
| End of life soon | 14 final release 2026-11-12; 13 and older are unsupported |
| PostgreSQL 18 additions that change advice | `uuidv7()`; virtual generated columns are the default; asynchronous I/O (`io_method`); B-tree skip scan; `NOT NULL` constraints can be added `NOT VALID`; `CHECK` and foreign keys can be `NOT ENFORCED`; `initdb` enables data checksums by default; `pg_upgrade` keeps optimizer statistics; MD5 passwords deprecated |

## 2. Types and Keys

| ID | Severity | Rule |
|---|---|---|
| PG-TYP-01 | medium | Use `bigint GENERATED ALWAYS AS IDENTITY` for integer keys, not `serial` (owned-sequence quirks, permission and dump edge cases). |
| PG-TYP-02 | medium | Use `uuid` for UUID keys; on 18+, generate v7 with `uuidv7()` (or in the application) instead of `gen_random_uuid()` for insert-heavy tables. |
| PG-TYP-03 | low | Use `text` (with a `CHECK (length(x) <= n)` when a limit is a business rule) rather than `varchar(n)`; `char(n)` pads and is almost never wanted. |
| PG-TYP-04 | high | Use `timestamptz` for instants, never `timestamp` without time zone for event times. |
| PG-TYP-05 | high | Use `numeric(p,s)` or integer minor units for money; never `money` (locale-dependent) or `float`. |
| PG-TYP-06 | medium | Use `jsonb`, not `json`, for stored documents; index it with a GIN index (`jsonb_path_ops` for containment only) or an expression index on the extracted field you filter by. |
| PG-TYP-07 | low | Prefer a `CHECK` or a lookup table over `CREATE TYPE ... AS ENUM` when values may be removed or reordered; enum values can be added but not dropped. |
| PG-TYP-08 | medium | Do not store large binaries in rows that are read often; TOAST moves large values out of line, but wide rows still cost I/O. Keep files in object storage and the key in the row. |

## 3. Indexes

| ID | Severity | Rule |
|---|---|---|
| PG-IDX-01 | high | Build and drop indexes on live tables with `CREATE INDEX CONCURRENTLY` / `DROP INDEX CONCURRENTLY`, outside a transaction block; a plain `CREATE INDEX` blocks writes until it finishes. A failed concurrent build leaves an `INVALID` index; drop it and retry. Concurrent builds on a partitioned parent are not supported: build on each partition concurrently, then create the parent index `ON ONLY` and attach them. |
| PG-IDX-02 | high | Index every foreign key column that is used for joins or for deletes on the parent; PostgreSQL does not create these automatically. |
| PG-IDX-03 | medium | Order composite B-tree columns as equality filters first, then the range or sort column; match the `ORDER BY` direction for top-N queries. |
| PG-IDX-04 | medium | Use partial indexes for hot subsets (`WHERE status = 'active'`, `WHERE deleted_at IS NULL`) and partial unique indexes for conditional uniqueness. The planner uses one only when the query's `WHERE` provably implies the index predicate; a parameter in place of the literal (`status = $1`) does not match. |
| PG-IDX-05 | medium | Use `INCLUDE` columns for covering index-only scans; index-only scans need a recently vacuumed visibility map. |
| PG-IDX-06 | medium | Pick the type by operator: B-tree for equality and range, GIN for `jsonb`, arrays, and full text, GiST for ranges, geometry, and exclusion constraints, BRIN for very large append-only tables ordered by time, hash only for pure equality. |
| PG-IDX-07 | medium | Find unused and duplicate indexes with `pg_stat_user_indexes.idx_scan = 0` over a full business cycle (and on every replica that serves reads) before dropping them; each index taxes every write and blocks HOT updates on its columns. |
| PG-IDX-08 | low | A function in the `WHERE` clause (`lower(email)`) needs a matching expression index. |

## 4. Queries

| ID | Severity | Rule |
|---|---|---|
| PG-QRY-01 | high | Read plans with `EXPLAIN (ANALYZE, BUFFERS)` on a disposable copy; on any shared database use plain `EXPLAIN`, or wrap a write in `BEGIN; EXPLAIN ANALYZE ...; ROLLBACK;` only with the user's permission. The rollback does not undo sequence increments, triggers that call out (`NOTIFY` is held, but `dblink`, foreign tables, and HTTP extensions are not), or the locks taken while it ran; say so before running it. |
| PG-QRY-02 | medium | In a plan, compare estimated and actual rows; a gap of 10x or more points to stale statistics (`ANALYZE`), correlated columns (`CREATE STATISTICS`), or a non-sargable predicate. |
| PG-QRY-03 | medium | Paginate deep lists with keyset pagination (`WHERE (created_at, id) < ($1, $2) ORDER BY created_at DESC, id DESC LIMIT n`), not large `OFFSET`. |
| PG-QRY-04 | medium | Fix N+1 access with a join, `= ANY($1)` batch lookups, or the ORM's eager loading; detect it as repeated identical statements in `pg_stat_statements` or logs. |
| PG-QRY-05 | medium | Use `INSERT ... ON CONFLICT` for idempotent upserts and `RETURNING` to avoid a second read; on 18+, `RETURNING OLD.*, NEW.*` returns both images. |
| PG-QRY-06 | medium | Use `SELECT ... FOR UPDATE SKIP LOCKED` for job queues in tables; keep the transaction short. |
| PG-QRY-07 | low | Prefer `EXISTS` to `IN (subquery)` with nullable columns, and `NOT EXISTS` to `NOT IN` (which returns no rows when the subquery yields a `NULL`). |

## 5. Schema Changes

| ID | Severity | Rule |
|---|---|---|
| PG-DDL-01 | high | Start every migration session with `SET lock_timeout = '5s'` (or lower) and a `statement_timeout`; most `ALTER TABLE` forms take `ACCESS EXCLUSIVE`, and a waiting `ACCESS EXCLUSIVE` request blocks all later queries on the table. |
| PG-DDL-02 | medium | Adding a column with a constant default is metadata-only (11+); a volatile default (`now()` is stable and fine, `random()` or `gen_random_uuid()` is volatile) rewrites the table. |
| PG-DDL-03 | high | Add a foreign key or `CHECK` as `NOT VALID`, then `VALIDATE CONSTRAINT` in a separate step; validation takes a weaker lock (`SHARE UPDATE EXCLUSIVE`) and does not block writes. |
| PG-DDL-04 | high | To make a column `NOT NULL` on a large table: on 18+, add the `NOT NULL` constraint `NOT VALID` and validate it; on older versions, add `CHECK (col IS NOT NULL) NOT VALID`, validate it, then `SET NOT NULL` (12+ skips the scan when a validated check proves it) and drop the check. |
| PG-DDL-05 | high | Add a unique or primary key constraint on a large table by building the unique index `CONCURRENTLY`, then `ALTER TABLE ... ADD CONSTRAINT ... UNIQUE USING INDEX`. |
| PG-DDL-06 | high | Changing a column type usually rewrites the table and its indexes under `ACCESS EXCLUSIVE`; use expand/contract (`rules/schema-changes.md` §3). Widening `varchar(n)` or dropping its limit is metadata-only. |
| PG-DDL-07 | medium | `CREATE INDEX CONCURRENTLY`, `REINDEX CONCURRENTLY`, and `VACUUM` cannot run inside a transaction; mark those migrations non-transactional in the tool. |
| PG-DDL-08 | medium | Lint migrations with a PostgreSQL migration linter (Squawk or the framework's equivalent) in CI; treat its blocking-lock findings as high. |

## 6. MVCC, Vacuum, and Bloat

| ID | Severity | Rule |
|---|---|---|
| PG-OPS-01 | critical | Watch transaction ID age (`age(datfrozenxid)`, `age(relfrozenxid)`); wraparound forces a shutdown to single-user mode. Alert well before `autovacuum_freeze_max_age`. |
| PG-OPS-02 | high | Kill or prevent long-running transactions and `idle in transaction` sessions (`idle_in_transaction_session_timeout`); they hold back vacuum for the whole cluster, as do abandoned replication slots and prepared transactions. |
| PG-OPS-03 | medium | Tune autovacuum per hot table (`autovacuum_vacuum_scale_factor` lower, `autovacuum_vacuum_cost_limit` higher) instead of disabling it; check `n_dead_tup` and `last_autovacuum` in `pg_stat_user_tables`. |
| PG-OPS-04 | medium | Never use `VACUUM FULL` on a live table (it takes `ACCESS EXCLUSIVE` and rewrites it); use `pg_repack` or a rebuild with expand/contract. |
| PG-OPS-05 | medium | Lower `fillfactor` on update-heavy tables to allow HOT updates, and avoid indexing columns that change often. |

## 7. Connections and Configuration

| ID | Severity | Rule |
|---|---|---|
| PG-CFG-01 | high | Each connection is a process; keep `max_connections` in the hundreds and put PgBouncer or the provider's pooler in front of many clients. In transaction mode, avoid session `SET`, session advisory locks, `LISTEN`, and cross-transaction temp tables. |
| PG-CFG-02 | medium | Start `shared_buffers` near 25% of RAM on a dedicated host, set `effective_cache_size` near 50-75%, and size `work_mem` per sort or hash node times concurrency so it cannot exhaust memory. |
| PG-CFG-03 | medium | Turn on `pg_stat_statements` and slow-statement logging (`log_min_duration_statement`), plus `log_lock_waits` and `auto_explain` sampling on hosts where you can. |
| PG-CFG-04 | medium | Keep `synchronous_commit = on` for systems of record; turning it off risks losing the last commits on a crash, not corruption. |

## 8. Replication, Backup, Upgrade

| ID | Severity | Rule |
|---|---|---|
| PG-REP-01 | high | Use physical streaming replication for HA and read replicas, and logical replication for selective tables, cross-version upgrades, and migrations. Monitor `pg_stat_replication` lag and every slot's retained WAL in `pg_replication_slots`; an inactive slot fills the disk. |
| PG-REP-02 | high | Back up with base backups plus continuous WAL archiving (pgBackRest, Barman, WAL-G, or the provider's PITR) and restore-test them; `pg_dump` alone gives no point-in-time recovery. |
| PG-REP-03 | high | Major upgrades use `pg_upgrade` (`--link` for speed, with a rehearsed rollback) or logical replication to a new cluster; extensions must exist at a compatible version on the target. |
| PG-REP-04 | medium | Logical replication does not carry DDL or sequence values; apply schema changes on both sides and resync sequences at cutover. |

## 9. Security

| ID | Severity | Rule |
|---|---|---|
| PG-SEC-01 | high | Revoke `CREATE` on `public` from `PUBLIC` on clusters created before 15, use per-application roles, and grant DML on specific schemas only; `ALTER DEFAULT PRIVILEGES` for future tables. |
| PG-SEC-02 | high | Use `scram-sha-256` password authentication and TLS (`hostssl` in `pg_hba.conf`); MD5 is deprecated in 18. |
| PG-SEC-03 | critical | For row-level security, `ENABLE` and usually `FORCE ROW LEVEL SECURITY`, write policies for every command, and test them as the application role; table owners and `BYPASSRLS` roles skip policies. |
| PG-SEC-04 | medium | `SECURITY DEFINER` functions set an explicit `search_path`. |

## 10. Extensions

| ID | Severity | Rule |
|---|---|---|
| PG-EXT-01 | medium | pgvector: choose HNSW for recall and latency at the cost of build time and memory, IVFFlat for faster builds on stable data; build after loading data, match the operator class to the distance you query (`vector_cosine_ops`, `vector_l2_ops`, `vector_ip_ops`), and filter carefully because post-filtering can return fewer rows than `LIMIT`. |
| PG-EXT-02 | medium | Declarative partitioning (range by time, list by tenant) helps retention (detach and drop old partitions) and pruning; every unique key must include the partition key, and too many partitions slow planning. |
| PG-EXT-03 | low | Check that the managed service supports an extension at the needed version before designing around it. |

## 11. Verification Commands

```sql
-- statement hot spots
SELECT queryid, calls, total_exec_time, mean_exec_time, rows, query
FROM pg_stat_statements ORDER BY total_exec_time DESC LIMIT 20;
-- unused indexes
SELECT relname, indexrelname, idx_scan, pg_size_pretty(pg_relation_size(indexrelid))
FROM pg_stat_user_indexes WHERE idx_scan = 0 ORDER BY pg_relation_size(indexrelid) DESC;
-- blocking chains
SELECT pid, pg_blocking_pids(pid), wait_event_type, state, now() - xact_start AS xact_age, query
FROM pg_stat_activity WHERE cardinality(pg_blocking_pids(pid)) > 0;
-- wraparound headroom
SELECT datname, age(datfrozenxid) FROM pg_database ORDER BY 2 DESC;
-- server version (PG-DDL-04 and other rules branch on it)
SHOW server_version;
```

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| Version table, support window, and end-of-life dates | <https://www.postgresql.org/support/versioning/> |
| PostgreSQL 18 additions: `uuidv7()`, virtual generated columns by default, AIO, skip scan, `NOT NULL ... NOT VALID`, `NOT ENFORCED`, checksums on by default, MD5 deprecation | <https://www.postgresql.org/docs/release/18.0/> |
| `EXPLAIN ANALYZE` executes the statement | <https://www.postgresql.org/docs/current/sql-explain.html> |
| Lock levels taken by `ALTER TABLE` forms and `VALIDATE CONSTRAINT` | <https://www.postgresql.org/docs/current/sql-altertable.html>, <https://www.postgresql.org/docs/current/explicit-locking.html> |
| `CREATE INDEX CONCURRENTLY` behavior and invalid indexes | <https://www.postgresql.org/docs/current/sql-createindex.html> |
| Transaction ID wraparound and autovacuum | <https://www.postgresql.org/docs/current/routine-vacuuming.html> |
| Practices to avoid (`serial`, `money`, `timestamp`, `char(n)`, `NOT IN`) | <https://wiki.postgresql.org/wiki/Don%27t_Do_This> |
| pgvector index types and operator classes | <https://github.com/pgvector/pgvector> |
| The rule IDs and severities | this package's chosen design, not a validated optimum |
