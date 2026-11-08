# Apache Cassandra and ScyllaDB

Engine guide for Apache Cassandra and ScyllaDB (self-hosted, Astra, ScyllaDB Cloud, Amazon Keyspaces as a CQL-compatible service). Read it after `rules/engine-detection.md` routes here. Rules apply to both unless marked; ScyllaDB's implementation differs in compaction, indexing, and tooling. Findings cite the `CS-*` IDs.

## 1. Dated Facts

> Volatile. Checked 2026-11-07 against the Cassandra download page, the ScyllaDB version support page, and the ScyllaDB license file; recheck before an adoption or upgrade decision.

| Fact | Value |
|---|---|
| Cassandra current | 5.0 line (5.0.9, 2026-08-07), maintained until the 8.0 release; 4.1 and 4.0 lines also patched; 5.0 needs JDK 17 |
| Cassandra 5.0 additions | Storage-attached indexes (SAI), unified compaction strategy (UCS), trie memtables and SSTables, vector type, dynamic data masking |
| ScyllaDB license | ScyllaDB Software License Agreement v1.1 (updated 2026-04-12): source-available, free use only for entities with no paid relationship with ScyllaDB in the previous 12 months, capped at 10 TB storage and 50 vCPUs across deployments; not open source |
| ScyllaDB releases | Calendar versions `YYYY.N`; supported: 2026.3, 2026.2, 2026.1 LTS, 2025.1 LTS |

## 2. Modeling

| ID | Severity | Rule |
|---|---|---|
| CS-MOD-01 | critical | Design one table per query: the partition key is what the query filters by equality, the clustering columns give the sort and range. Denormalize into several tables instead of joining; there are no joins or cross-partition transactions. |
| CS-MOD-02 | high | Choose a high-cardinality partition key with even traffic; a popular entity as the partition key (a celebrity user's messages) becomes a hot partition. |
| CS-MOD-03 | high | Bound partition size by adding a time bucket to the partition key (`PRIMARY KEY ((user_id, day), event_time)`); unbounded partitions grow slow to read, repair, and compact. Cassandra enforces no size limit by default, so set `partition_size_warn_threshold` and watch `nodetool tablestats`. |
| CS-MOD-04 | medium | Write each table's partition key, clustering order, and the query it serves into the schema review; a query without a table is a missing table, not a missing index. |
| CS-MOD-05 | medium | Updates are upserts resolved last-write-wins per cell by timestamp; keep clocks synchronized and restrict client-supplied timestamps. |
| CS-MOD-06 | low | Use one keyspace per application with `NetworkTopologyStrategy`; `SimpleStrategy` ignores datacenter layout and is not for production. |

## 3. Queries and Indexes

| ID | Severity | Rule |
|---|---|---|
| CS-QRY-01 | high | Treat `ALLOW FILTERING` in application code as a design defect; it scans partitions on the coordinator. |
| CS-QRY-02 | medium | On Cassandra 5.0, prefer SAI over legacy secondary indexes for occasional extra filters (one index per column, a configurable cap per table, roughly 20-35% extra disk); a frequent query still deserves its own table. ScyllaDB secondary indexes are built on materialized views and carry their write cost. |
| CS-QRY-03 | high | Use `IN` on partition keys sparingly and keep batches small and single-partition; multi-partition batches are for atomicity, not speed (default warn 5 KiB, fail 50 KiB). |
| CS-QRY-04 | high | Lightweight transactions (`IF NOT EXISTS`, `IF col = ...`) take several round trips; keep them off hot paths. |
| CS-QRY-05 | medium | Page large reads with the driver's paging state instead of large `LIMIT`s. |

## 4. Consistency and Replication

| ID | Severity | Rule |
|---|---|---|
| CS-CON-01 | high | Writes go to all replicas; the consistency level only sets how many acknowledgments to wait for. For read-your-writes choose read plus write replicas greater than the replication factor (with RF 3, `QUORUM`/`QUORUM`, or `LOCAL_QUORUM` within a datacenter). |
| CS-CON-02 | high | Never use `ANY` where durability matters; it can acknowledge a write held only as a hint. Restrict allowed levels per keyspace with guardrails where available. |
| CS-CON-03 | medium | Run repairs regularly (incremental where supported) within `gc_grace_seconds`; a node down longer than that window can resurrect deleted data. |

## 5. Deletes, Tombstones, Compaction

| ID | Severity | Rule |
|---|---|---|
| CS-TMB-01 | high | Deletes and TTL expiry write tombstones that are purged only after `gc_grace_seconds` (default 10 days) and a compaction covering the shadowed data. Avoid delete-heavy queue or "update by delete then insert" patterns; reads fail past the tombstone failure threshold (default 100,000 per query). |
| CS-TMB-02 | medium | Investigate tombstones with `nodetool tablestats`, tombstone histograms, and `sstableexpiredblockers`. |
| CS-CMP-01 | medium | Cassandra's code default is still size-tiered compaction; on 5.0 set UCS explicitly (the documentation recommends it for most workloads) and pick its scaling parameter for read-heavy, write-heavy, or time-series tables. ScyllaDB has its own compaction strategies; read its documentation instead of assuming Cassandra's. |

## 6. Operations

| ID | Severity | Rule |
|---|---|---|
| CS-OPS-01 | high | Back up with snapshots plus incremental backups or the vendor's backup tool, and restore-test into a separate cluster. |
| CS-OPS-02 | medium | Enable the guardrails that ship disabled (partition size, tombstones, columns per table, page size, `IN` cartesian products) at values the team agrees on. |
| CS-OPS-03 | high | Confirm the ScyllaDB license terms against the organization's commercial relationship and usage before adopting it; the free grant has eligibility and size limits. |

## 7. Verification Commands

```bash
nodetool status                 # ring and node health
nodetool tablestats ks.table    # partition sizes, tombstones, read latency
nodetool tablehistograms ks.table
nodetool compactionstats
cqlsh -e "TRACING ON; SELECT ... ;"   # per-query trace on a disposable cluster
```

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| Cassandra release lines and support | <https://cassandra.apache.org/_/download.html> |
| Cassandra 5.0 new features and JDK 17 | <https://cassandra.apache.org/doc/latest/cassandra/new/index.html> |
| Keyspaces, `NetworkTopologyStrategy`, and DDL rules | <https://cassandra.apache.org/doc/latest/cassandra/developing/cql/ddl.html> |
| Single-partition guarantees, consistency levels, last-write-wins | <https://cassandra.apache.org/doc/latest/cassandra/architecture/dynamo.html> |
| SAI behavior and limits | <https://cassandra.apache.org/doc/latest/cassandra/developing/cql/indexing/sai/sai-faq.html> |
| UCS recommendation and parameters | <https://cassandra.apache.org/doc/latest/cassandra/managing/operating/compaction/ucs.html> |
| Tombstones and `gc_grace_seconds` | <https://cassandra.apache.org/doc/latest/cassandra/managing/operating/compaction/tombstones.html> |
| Batch, tombstone, and guardrail defaults | <https://raw.githubusercontent.com/apache/cassandra/trunk/conf/cassandra.yaml> |
| Size-tiered compaction as the code default | <https://raw.githubusercontent.com/apache/cassandra/trunk/src/java/org/apache/cassandra/schema/CompactionParams.java> |
| ScyllaDB license terms and usage limit | <https://raw.githubusercontent.com/scylladb/scylladb/master/LICENSE-ScyllaDB-Source-Available.md> |
| ScyllaDB supported releases | <https://docs.scylladb.com/stable/versioning/version-support.html> |
| ScyllaDB partition key and query design guidance, secondary indexes on materialized views | <https://docs.scylladb.com/stable/get-started/data-modeling/best-practices.html>, <https://docs.scylladb.com/main/get-started/data-modeling/query-design.html> |
| The rule IDs and severities | this package's chosen design, not a validated optimum |
