# MySQL and MariaDB

Engine guide for MySQL (InnoDB), Percona Server, and MariaDB, self-hosted or managed (RDS, Aurora MySQL, Cloud SQL, Azure, PlanetScale Vitess). Read it after `rules/engine-detection.md` routes here; for Vitess or PlanetScale, also read the platform section of `engines/distributed-sql.md`. Findings cite the `MY-*` IDs; MariaDB-only rules use `MY-MDB-*`.

## 1. Dated Facts

> Volatile. Checked 2026-11-07 against the MySQL 26.10, 9.7, and 8.4 manuals and the MariaDB release model; recheck when an upgrade decision depends on them.

| Fact | Value |
|---|---|
| Release tracks | LTS (5 years premier plus 3 years extended support) and Innovation (supported only until the next Innovation release) |
| LTS lines | 8.4 LTS and 9.7 LTS; 9.7 is the last sequentially numbered line |
| Version numbering | From July 2026, calendar versions `YY.M.P` (26.7.0 first, 26.10 current Innovation manual); a calendar version does not say whether a release is LTS |
| Upgrade path | LTS to the next LTS only, never skipping one (8.4 to 9.7, not 8.4 to a later calendar LTS); only 9.7 LTS upgrades directly into the first calendar-versioned lineage; Innovation downgrades need a logical dump and load |
| MariaDB | Not version-compatible with MySQL; since 11.3 roughly four releases a year with an LTS about every fourth, maintained 3 years; confirm per series which lines are LTS |

## 2. Types and Keys

| ID | Severity | Rule |
|---|---|---|
| MY-TYP-01 | high | Use `utf8mb4` (server default `utf8mb4_0900_ai_ci` on 8.x) and never the `utf8` alias, which means `utf8mb3` and cannot store 4-byte characters such as emoji. Set the charset explicitly in DDL. |
| MY-TYP-02 | high | Store instants in `DATETIME` holding UTC by convention, or accept `TIMESTAMP`'s session time-zone conversion and its hard stop at `2038-01-19 03:14:07` UTC; never let new columns inherit the 2038 limit unknowingly. |
| MY-TYP-03 | high | Keep strict SQL mode (`STRICT_TRANS_TABLES`) on; without it invalid dates become `0000-00-00` and truncations become warnings. |
| MY-TYP-04 | high | Every InnoDB table declares a short, monotonically increasing primary key (`BIGINT UNSIGNED AUTO_INCREMENT`, or a time-ordered UUID in `BINARY(16)`). The primary key is the clustered index and row order; without one InnoDB uses the first non-null unique key or a hidden 6-byte row ID. |
| MY-TYP-05 | medium | Budget secondary indexes from the primary key width: every secondary index entry carries the full primary key, so a wide or random key inflates every index and scatters inserts. |
| MY-TYP-06 | medium | Use `DECIMAL(p,s)` for money; `FLOAT`/`DOUBLE` are approximate. |
| MY-TYP-07 | low | `ENUM` is safe to extend only by appending values; reordering or inserting renumbers stored values. Prefer a lookup table for sets that change. |
| MY-TYP-08 | medium | MySQL `JSON` is a binary document type; index fields you filter by with a generated column or a functional index (`INDEX ((CAST(doc->>'$.sku' AS CHAR(32))))`). |

## 3. Indexes and Queries

| ID | Severity | Rule |
|---|---|---|
| MY-IDX-01 | medium | Order composite indexes as equality columns first, then one range or sort column; columns after the first range are not used for seeking. |
| MY-IDX-02 | medium | A covering index (all selected columns in the index) avoids the clustered-index lookup; `EXPLAIN` shows `Using index`. |
| MY-IDX-03 | medium | Retire an index by making it `INVISIBLE` first (fast, still maintained, still enforces uniqueness), watch plans and latency, then drop it; primary keys cannot be made invisible. |
| MY-IDX-04 | medium | Read plans with `EXPLAIN FORMAT=TREE` or `EXPLAIN ANALYZE` on a disposable copy; `EXPLAIN ANALYZE` executes the statement. Watch for `type: ALL`, `Using filesort`, and `Using temporary` on hot queries. |
| MY-QRY-01 | medium | Use keyset pagination on deep lists instead of large `OFFSET`. |
| MY-QRY-02 | medium | Under the default `REPEATABLE READ`, range scans in locking reads and updates take gap and next-key locks; index the predicate so `UPDATE ... WHERE` locks a few rows, not a range, and keep those transactions short. |
| MY-QRY-03 | medium | Deadlocks are normal under concurrency: log them (`innodb_print_all_deadlocks`), retry the transaction once, and fix lock order. |
| MY-QRY-04 | low | `INSERT ... ON DUPLICATE KEY UPDATE` and `REPLACE` behave differently: `REPLACE` deletes then inserts, firing delete triggers and cascades. |

## 4. Online Schema Changes

| ID | Severity | Rule |
|---|---|---|
| MY-DDL-01 | high | State the algorithm and lock in every `ALTER TABLE` (`ALGORITHM=INSTANT` or `ALGORITHM=INPLACE, LOCK=NONE`), so the statement fails instead of silently falling back to a blocking copy. `INSTANT` is the default for adding and dropping columns on 8.4. |
| MY-DDL-02 | high | `INSTANT` column changes are capped by row versions (64 per table, 255 from 9.1.0; see `INFORMATION_SCHEMA.INNODB_TABLES.TOTAL_ROW_VERSIONS`) and are unavailable on `ROW_FORMAT=COMPRESSED` tables, tables with a `FULLTEXT` index, and temporary tables; plan a rebuild before the cap. |
| MY-DDL-03 | high | Changing a column's data type rebuilds the table and does not allow concurrent DML; adding or changing the primary key rebuilds it too. Use gh-ost or `pt-online-schema-change` on large hot tables. |
| MY-DDL-04 | high | Every DDL waits for a metadata lock that open transactions on the table hold until they end, and a waiting DDL blocks later queries. Set `lock_wait_timeout` low in migration sessions, check `performance_schema.metadata_locks`, and kill or wait out long transactions first. |
| MY-DDL-05 | high | DDL is not transactional: a multi-statement migration that fails halfway stays half applied. Keep one change per migration and make each statement idempotent where the tool allows. |
| MY-DDL-06 | medium | Adding a secondary index is `INPLACE` with concurrent DML but still waits for transactions on the table to finish before completing. |

## 5. Configuration, Replication, Operations

| ID | Severity | Rule |
|---|---|---|
| MY-CFG-01 | medium | Size `innodb_buffer_pool_size` as the main memory knob on a dedicated host (commonly well over half of RAM) and check the buffer pool hit rate before adding hardware. |
| MY-CFG-02 | high | Keep `innodb_flush_log_at_trx_commit = 1` and `sync_binlog = 1` for systems of record; other values trade the last second of commits for throughput. |
| MY-CFG-03 | medium | Turn on the slow query log and Performance Schema statement digests; review the top digests by total latency. |
| MY-REP-01 | high | Use GTID-based replication (`gtid_mode=ON`, `enforce_gtid_consistency=ON`) and monitor replica lag; long transactions and large DDL replay serially and create lag spikes. |
| MY-REP-02 | high | Back up with a physical tool (Percona XtraBackup, MySQL Enterprise Backup, the clone plugin, or the provider's snapshots) plus binlog retention for point-in-time recovery; `mysqldump` alone does not give PITR on large databases. Restore-test it. |
| MY-SEC-01 | high | Use `caching_sha2_password`, require TLS (`require_secure_transport=ON`), and grant per-schema privileges to application users; never let the application connect as `root`. |

## 6. MariaDB Differences

| ID | Severity | Rule |
|---|---|---|
| MY-MDB-01 | high | MariaDB `JSON` is an alias for `LONGTEXT` with a `JSON_VALID` check: values are stored as text, compared as strings, and duplicate keys keep the first. Do not port MySQL JSON indexing or comparison assumptions. |
| MY-MDB-02 | high | Row-based replication of MySQL `JSON` columns into MariaDB does not work; MariaDB GTIDs use a different format from MySQL GTIDs. |
| MY-MDB-03 | medium | Check feature floors per MariaDB series instead of assuming MySQL parity; instant `ADD COLUMN`, invisible columns, and system-versioned tables have MariaDB-specific rules and limits. |

## 7. Verification Commands

```sql
-- statement hot spots
SELECT digest_text, count_star, sum_timer_wait/1e12 AS total_s, avg_timer_wait/1e9 AS avg_ms
FROM performance_schema.events_statements_summary_by_digest ORDER BY sum_timer_wait DESC LIMIT 20;
-- unused indexes (sys schema)
SELECT * FROM sys.schema_unused_indexes;
-- metadata lock waits
SELECT * FROM performance_schema.metadata_locks WHERE lock_status = 'PENDING';
-- instant-DDL headroom
SELECT name, total_row_versions FROM information_schema.innodb_tables ORDER BY total_row_versions DESC LIMIT 10;
```

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| Calendar versioning, compatibility lineages, LTS and Innovation support, upgrade paths | <https://dev.mysql.com/doc/refman/26.10/en/mysql-releases.html>, <https://dev.mysql.com/doc/refman/8.4/en/mysql-releases.html> |
| `INSTANT` default, row-version cap 64 (255 from 9.1.0), operation table for type and primary key changes | <https://dev.mysql.com/doc/refman/8.4/en/innodb-online-ddl-operations.html> |
| Clustered and secondary index structure, hidden row ID | <https://dev.mysql.com/doc/refman/8.4/en/innodb-index-types.html> |
| `TIMESTAMP` and `DATETIME` ranges and time-zone conversion | <https://dev.mysql.com/doc/refman/8.4/en/datetime.html> |
| `utf8` aliases `utf8mb3`; server default charset and collation | <https://dev.mysql.com/doc/refman/8.4/en/charset-unicode-utf8mb3.html>, <https://dev.mysql.com/doc/refman/8.4/en/charset-server.html> |
| Metadata locks held to transaction end | <https://dev.mysql.com/doc/refman/8.4/en/metadata-locking.html> |
| Invisible index behavior | <https://dev.mysql.com/doc/refman/8.4/en/invisible-indexes.html> |
| Default isolation level and next-key locking | <https://dev.mysql.com/doc/refman/8.4/en/innodb-transaction-isolation-levels.html> |
| MariaDB release model and `JSON` type | <https://mariadb.com/docs/release-notes/community-server/about/release-model>, <https://mariadb.com/docs/server/reference/data-types/string-data-types/json> |
| The rule IDs and severities | this package's chosen design, not a validated optimum |
