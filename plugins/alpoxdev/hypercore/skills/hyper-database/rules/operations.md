# Operations

Use this rule in operate mode, and in design and choose modes before writing the report's operations section. It is the engine-neutral DBA checklist; each engine guide names the commands, settings, and limits. Findings cite the `OP-*` IDs below.

## 1. Backup and Restore

| ID | Severity | Rule |
|---|---|---|
| OP-01 | critical | A system of record has an RPO and an RTO written down, and a backup method that meets them: continuous archiving or point-in-time recovery for small RPO, snapshots or logical dumps for the rest. |
| OP-02 | critical | Backups are proven only by restores. Restore to a separate target on a schedule (at least quarterly, and after every backup-method change), check row counts or checksums, and record the time it took against the RTO. |
| OP-03 | high | Keep at least one copy outside the primary's account, region, or failure domain, and protect it from deletion by the same credentials that run the database (immutable or separately owned storage). |
| OP-04 | high | Replicas, snapshots of a running volume, and `RAID` are not backups; they replicate deletes and corruption. |
| OP-05 | medium | Logical dumps (`pg_dump`, `mysqldump`, `mongodump`) suit small databases and cross-version moves; large databases need physical or incremental backups with log archiving. |
| OP-06 | medium | A cache that can be rebuilt from the source needs no backup, but it needs a warm-up plan; state which keys are rebuilt and how fast. |

## 2. Replication and Failover

| ID | Severity | Rule |
|---|---|---|
| OP-10 | high | State the topology (single node, primary with replicas, quorum cluster, multi-region) and what a node, zone, or region loss does to reads, writes, and data. |
| OP-11 | high | Asynchronous replication loses the writes not yet replicated on failover; when that is unacceptable, use synchronous or quorum commit and accept its latency. |
| OP-12 | high | Failover is automatic only with a fencing or consensus mechanism that prevents two primaries; otherwise document the manual promotion steps. |
| OP-13 | medium | Monitor replication lag and alert on it; read-your-writes paths do not read from lagging replicas. |
| OP-14 | medium | Drill failover in a non-production environment and record the observed downtime and data loss. |

## 3. Connections

| ID | Severity | Rule |
|---|---|---|
| OP-20 | high | Serverless, edge, and many-instance applications go through a pooler or the provider's pooled endpoint; keep the sum of all pools inside the database's connection limit and size each pool by OP-23. |
| OP-23 | medium | Do the connection math before changing pool settings: server connections = pool size per process x processes (x replica-set members for MongoDB drivers) and must stay below the server limit minus reserved and platform connections. Size each pool from observed concurrency (requests per second x average query time, plus headroom), not from CPU count alone, and confirm with the server's active-connection metrics. |
| OP-21 | medium | Transaction-mode pooling breaks session state (session `SET`, advisory locks held across transactions, `LISTEN`, some prepared-statement modes); run migrations and session-dependent work on a direct connection. |
| OP-22 | medium | Every client sets connect, query, and idle timeouts, and retries only idempotent operations. |

## 4. Security

| ID | Severity | Rule |
|---|---|---|
| OP-30 | critical | No database port is reachable from the public internet without authentication and TLS; bind to private networks and allow-list sources. |
| OP-31 | critical | All application queries use parameterized statements or the driver's binding; no string-built SQL, Mongo filters from raw JSON input, or unescaped Lua/script arguments. |
| OP-32 | high | Separate roles: a migration owner, an application role with only the DML it needs, a read-only role for analytics and support, and no application use of the superuser. |
| OP-33 | high | Credentials live in a secret manager or the platform's secret store, rotate on a schedule and on staff change, and never appear in repository files, logs, or reports. |
| OP-34 | high | Encrypt in transit (TLS with certificate verification) and at rest; classify columns that hold personal or payment data and restrict who can read them. |
| OP-35 | medium | Personal data has a retention period and a deletion path that also covers backups, replicas, caches, and search indexes, or a documented reason it cannot. |
| OP-36 | medium | Audit logging records privileged actions and schema changes. |

## 5. Capacity and Maintenance

| ID | Severity | Rule |
|---|---|---|
| OP-40 | high | Estimate one-year size per table or key family (rows times average row size, plus index size) and keep disk and memory headroom; alert before 80% use. |
| OP-41 | medium | Plan engine housekeeping: PostgreSQL vacuum and wraparound, InnoDB purge and history length, MongoDB and Cassandra compaction, Redis memory fragmentation. |
| OP-42 | medium | Archive or partition data with a retention rule instead of deleting row by row from a hot table. |
| OP-43 | medium | Load-test a design whose access-pattern table predicts a hot spot before launch. |

## 6. Upgrades

| ID | Severity | Rule |
|---|---|---|
| OP-50 | high | Stay on a supported major version; check the engine guide's dated support table and plan the next upgrade before end of life. |
| OP-51 | high | Upgrade with a rehearsal on a restored copy, a read of every intervening release note, a rollback path (a logical-replication or blue-green switch, or a restorable backup taken just before), and an application compatibility test. |
| OP-52 | medium | Apply minor releases promptly; they carry security and data-corruption fixes. |

## 7. Monitoring

| ID | Severity | Rule |
|---|---|---|
| OP-60 | high | Watch the database's golden signals: query latency percentiles, throughput, errors, and saturation (CPU, memory, disk, connections, I/O). |
| OP-61 | medium | Keep a statement-level statistics source on (`pg_stat_statements`, Performance Schema, the profiler, `SLOWLOG`) and review the top statements by total time. |
| OP-62 | medium | Alert on replication lag, disk headroom, connection saturation, lock waits, deadlocks, cache hit ratio drops, evictions, and failed backups. |
| OP-63 | medium | Every alert links a runbook entry: what it means, how to confirm, and the first safe action. |

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| Backups are proven by restores, and data integrity needs defense in depth beyond replication | <https://sre.google/sre-book/data-integrity/> |
| The four golden signals | <https://sre.google/sre-book/monitoring-distributed-systems/> |
| Parameterized queries as the primary SQL injection defense | <https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html> |
| Continuous archiving and point-in-time recovery | <https://www.postgresql.org/docs/current/continuous-archiving.html> |
| The checklist, IDs, and severities | this package's chosen design, not a validated optimum |
