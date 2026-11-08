# Distributed and Serverless SQL Platforms

Engine guide for platforms that change how a wire-protocol engine behaves: Vitess and PlanetScale, CockroachDB, TiDB, Neon, Supabase, Turso and libSQL, and Cloudflare D1. Read the wire-protocol guide first (`engines/postgres.md`, `engines/mysql.md`, or `engines/sqlite.md`), then only the platform section you detected. Findings cite the `DS-*` IDs.

> Volatile. Platform limits, defaults, and licenses below were checked 2026-11-07 against each vendor's documentation; recheck the live page before a design depends on a number.

## 1. Vitess and PlanetScale (MySQL)

| ID | Severity | Rule |
|---|---|---|
| DS-VT-01 | high | Foreign key constraints work only in unsharded keyspaces and are off by default per database on PlanetScale. A schema that will shard keeps referential integrity in the application, with the indexes the joins need and a batched orphan check. |
| DS-VT-02 | high | Every table needs a unique, non-null key; online schema changes copy rows by it. |
| DS-VT-03 | high | With safe migrations on (the production norm), direct DDL is rejected; changes go branch to deploy request. Plan rollback around the 30-minute revert window after a deploy, not around a `down` migration. |
| DS-VT-04 | high | Instant deployments cannot be reverted and terminate queries holding locks on the table; use them only where both are acceptable. |
| DS-VT-05 | medium | Development branches copy schema, not data; rehearse data-dependent migrations (backfills, new unique keys) on restored data. |
| DS-VT-06 | medium | Check unsupported MySQL features before porting: stored programs, `LOCK TABLES`, and some recursive or `JSON_TABLE` queries. The global time zone is UTC. |
| DS-VT-07 | medium | Choose the sharding key (the Vindex) from the dominant access pattern; queries without it scatter to every shard. |

PlanetScale also runs PostgreSQL products; rules in this section apply to its Vitess (MySQL) product only.

## 2. CockroachDB

| ID | Severity | Rule |
|---|---|---|
| DS-CR-01 | high | The default isolation is `SERIALIZABLE`. Every transaction that can see contention retries on SQLSTATE `40001` (message starting `restart transaction`) with bounded backoff; shrink transactions that fail on commit deadlines instead of retrying them. |
| DS-CR-02 | high | Never key a large table on a monotonically increasing `INT`/`SERIAL` or a timestamp; it creates a single-range hotspot. Use a random UUID, a composite key that leads with a well-distributed column, or a hash-sharded index (`USING HASH`) for sequential columns. |
| DS-CR-03 | medium | CockroachDB documentation recommends UUIDv4 and calls other UUID versions largely untested; this overrides the general UUIDv7 preference (DM-12) on this engine. |
| DS-CR-04 | medium | `READ COMMITTED` exists but does not prevent lost updates; do not switch to it as a performance reflex. |
| DS-CR-05 | medium | Batch large inserts and deletes; use row-level TTL for expiry. |
| DS-CR-06 | high | Self-hosted CockroachDB is source-available under the CockroachDB Software License since the 2024 license change, which retired the free Core edition; check the license terms and telemetry requirements before choosing it. |

## 3. TiDB

| ID | Severity | Rule |
|---|---|---|
| DS-TI-01 | high | Avoid `AUTO_INCREMENT` primary keys on write-heavy tables (hotspot); use `AUTO_RANDOM`. Auto-increment values are unique but allocated in per-server batches, so never treat them as gap-free or ordered. |

## 4. Neon (PostgreSQL)

| ID | Severity | Rule |
|---|---|---|
| DS-NE-01 | high | Serverless and edge code uses the pooled connection string (PgBouncer in transaction mode); migrations, `pg_dump`, logical replication, `LISTEN`, session `SET`, and SQL-level `PREPARE` use the direct connection. |
| DS-NE-02 | medium | The pooler's 10,000 client connections are slots, not concurrency; real concurrency is bounded by `max_connections`, which scales with compute size, per user and database pool. |
| DS-NE-03 | medium | Computes scale to zero after 5 minutes idle by default and wake in a few hundred milliseconds; clients set connect timeouts and retry the first query. |
| DS-NE-04 | medium | Branches are copy-on-write clones with data; use one per preview or test run and delete them. Point-in-time restore is bounded by the configured history window, so set it before you need it. |

## 5. Supabase (PostgreSQL)

| ID | Severity | Rule |
|---|---|---|
| DS-SB-01 | critical | Enable row-level security on every table in an exposed schema; a table there without RLS is readable and writable by any role with a grant. Revoke default grants you do not need from `anon` and `authenticated`. |
| DS-SB-02 | high | Write one policy per operation; `UPDATE` policies need `WITH CHECK` so a user cannot reassign ownership, and an `UPDATE` also needs a `SELECT` policy to match rows. |
| DS-SB-03 | high | Views bypass RLS unless created with `security_invoker = true`. |
| DS-SB-04 | critical | The `service_role` key bypasses RLS; keep it server-side only. |
| DS-SB-05 | medium | Write policies as `using ((select auth.uid()) = user_id)` so the function is evaluated once per statement, and index the policy columns. |
| DS-SB-06 | high | The shared pooler's transaction mode does not support prepared statements; serverless clients use the transaction pooler with `prepare: false` and a pool of one per instance. Direct, session, and pooled backends share one `max_connections` budget with the platform's own services. |
| DS-SB-07 | medium | Test policies as each role (allow and deny for every operation) in the database test suite. |

## 6. Turso, libSQL, and Cloudflare D1 (SQLite)

| ID | Severity | Rule |
|---|---|---|
| DS-D1-01 | high | One D1 database processes queries one at a time; throughput is roughly the inverse of query duration. Scale by many small databases (per tenant or per user), which means migrations run against every database. |
| DS-D1-02 | high | Design inside D1's per-database limits (size, row size, statement size, bound parameters, query duration); check the current limits page. Chunk bulk updates and deletes into batches of about a thousand rows. |
| DS-D1-03 | medium | Use `db.batch()` for multi-statement work; read replicas serve reads only through the Sessions API. |
| DS-TU-01 | medium | Turso embedded replicas read locally and write to the remote primary; only the writer reads its own writes before `sync()`. Never open the replica file while it syncs. |
| DS-TU-02 | medium | Hosted Turso treats `PRAGMA user_version` as read-only and ignores some journal pragmas; track migrations in a table. |

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| Vitess foreign keys only in unsharded keyspaces | <https://planetscale.com/docs/vitess/foreign-key-constraints> |
| Unique non-null key requirement, unsupported features, UTC time zone | <https://planetscale.com/docs/vitess/troubleshooting/mysql-compatibility> |
| Safe migrations reject direct DDL | <https://planetscale.com/docs/vitess/schema-changes/safe-migrations> |
| Deploy requests, the 30-minute revert window, and instant deployments | <https://planetscale.com/docs/vitess/schema-changes/deploy-requests> |
| Branches copy schema only | <https://planetscale.com/docs/vitess/schema-changes/branching> |
| CockroachDB default `SERIALIZABLE` and `READ COMMITTED` behavior | <https://docs.cockroachlabs.com/docs/stable/read-committed> |
| Retry errors use SQLSTATE `40001` | <https://docs.cockroachlabs.com/docs/stable/transaction-retry-error-reference> |
| Sequential keys create hotspots; UUIDv4 recommendation; batching and TTL | <https://docs.cockroachlabs.com/docs/stable/performance-best-practices-overview> |
| Hash-sharded indexes | <https://docs.cockroachlabs.com/docs/stable/hash-sharded-indexes> |
| CockroachDB license change and retirement of Core | <https://www.cockroachlabs.com/blog/enterprise-license-announcement/>, <https://docs.cockroachlabs.com/docs/stable/licensing-faqs> |
| TiDB `AUTO_INCREMENT` hotspots, `AUTO_RANDOM`, and batched allocation | <https://docs.pingcap.com/tidb/stable/auto-increment/> |
| Neon pooling in transaction mode, direct-connection cases, and connection limits | <https://neon.com/docs/connect/connection-pooling> |
| Neon scale to zero after 5 minutes | <https://neon.com/docs/introduction/scale-to-zero> |
| Neon branches and history window | <https://neon.com/docs/introduction/branching> |
| Supabase RLS rules, views, `service_role`, and `auth.uid()` form | <https://supabase.com/docs/guides/database/postgres/row-level-security> |
| Supabase poolers, prepared statements, and the shared connection budget | <https://supabase.com/docs/guides/database/connecting-to-postgres>, <https://supabase.com/docs/guides/database/connecting-to-postgres/pooling-and-limits> |
| D1 single-threaded databases and limits | <https://developers.cloudflare.com/d1/platform/limits/> |
| D1 read replication through the Sessions API | <https://developers.cloudflare.com/d1/best-practices/read-replication/> |
| Turso embedded replicas and hosted limitations | <https://docs.turso.tech/features/embedded-replicas/introduction> |
| The rule IDs and severities | this package's chosen design, not a validated optimum |
