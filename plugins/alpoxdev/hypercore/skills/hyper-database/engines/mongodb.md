# MongoDB

Engine guide for MongoDB (self-hosted replica sets and sharded clusters, Atlas). Read it after `rules/engine-detection.md` routes here. Findings cite the `MG-*` IDs.

## 1. Dated Facts

> Volatile. Checked 2026-11-07 against the MongoDB 9.0 and 8.0 release notes and the limits page; recheck before a version decision.

| Fact | Value |
|---|---|
| Current major | 9.0 (9.0.0 on 2026-09-28, 9.0.4 on 2026-10-13); 8.0 still patched (8.0.34 on 2026-10-13) |
| 9.0 changes that affect design | Open multi-document transactions capped by `maxConcurrentMultiDocumentTransactions` (default 10000, error `TooManyOpenTransactions`); a per-operation memory limit of 1 GB or 20% of server memory, whichever is greater |
| 8.0 change | `{w: "majority"}` acknowledges once a majority has durably written the oplog entry, before secondaries apply it |
| Hard limits | Document 16 MiB; nesting depth 100 levels; namespace 255 bytes (235 when sharded) |
| Defaults | Write concern `w: "majority"` (with arbiters it can fall to `w: 1`); read concern `"local"`; driver `maxPoolSize` 100 |

## 2. Modeling

| ID | Severity | Rule |
|---|---|---|
| MG-MOD-01 | high | Model from the queries: data read together is stored together. Do not port a normalized relational schema one table to one collection; count `$lookup` stages per endpoint as the smell. |
| MG-MOD-02 | high | Embed when the child is read and updated with the parent, belongs to it, and is bounded; reference when the child side has high or unbounded cardinality, is written separately in a write-heavy workload, or exists on its own. |
| MG-MOD-03 | critical | Never let an array grow without bound (comments, events, followers in the parent document); it drives documents toward the 16 MiB limit and makes every update rewrite a large document. Move it to a child collection or a bucket, and cap arrays with `$jsonSchema` `maxItems`. |
| MG-MOD-04 | high | Design each invariant to hold inside one document where possible; single-document writes are atomic. Multi-document transactions cost more and are not a substitute for schema design. |
| MG-MOD-05 | medium | Duplicate (extended reference, computed, subset patterns) only data that is immutable or tolerant of staleness, and name what updates the copies. |
| MG-MOD-06 | medium | Use the documented patterns by need: bucket or native time series collections for series data, outlier for a few oversized documents, subset for a hot slice of a large child set, computed for read-heavy aggregates, schema versioning (`schemaVersion` field) for online shape changes, archive for cold data. |
| MG-MOD-07 | high | Enforce the contract with `$jsonSchema` validation (`bsonType` on fields queries depend on, `required`, `maxItems`); roll it out with `validationLevel: "moderate"` and `validationAction: "warn"`, then tighten to `"error"`. While the action is `"warn"`, nothing is rejected, so a `maxItems` cap is not enforced until that switch. |
| MG-MOD-08 | medium | Avoid duplicate field names and top-level field names containing dots that collide with embedded paths. |

## 3. Indexes and Queries

| ID | Severity | Rule |
|---|---|---|
| MG-IDX-01 | high | Order compound index fields by Equality, Sort, Range (ESR). `$ne`, `$nin`, and `$regex` act as range predicates; `$in` with more than 200 values behaves as a range and stops the index from serving the sort. |
| MG-IDX-02 | medium | MongoDB usually uses one index per query (each `$or` branch can use its own); do not rely on index intersection to rescue a missing compound index. |
| MG-IDX-03 | medium | An index serves its own sort direction and the full reverse only; a mixed sort (`{a: 1, b: -1}`) needs an index with that exact pattern. Collation must match between query and index. |
| MG-IDX-04 | medium | Read `explain("executionStats")`: aim for `totalKeysExamined` and `totalDocsExamined` close to `nReturned`; `COLLSCAN` and in-memory `SORT` stages on hot queries are findings. `explain` bypasses the plan cache. |
| MG-IDX-05 | medium | Prefer partial indexes over sparse ones; a partial index is used only when the query predicate implies its filter. Shard key and `_id` indexes cannot be partial. |
| MG-IDX-06 | medium | Every index costs write amplification and memory; audit with `$indexStats` (`accesses.ops` near zero over a full business cycle), hide with `hideIndex`, watch, then drop. A collection with many more than about 20 indexes deserves review. |
| MG-IDX-07 | medium | TTL indexes are single-field; the monitor runs every 60 seconds and removes a bounded batch per pass, so expiry lags. Delete the existing backlog in batches before adding a TTL index to a large collection. |
| MG-IDX-08 | high | Build indexes on large collections in a quiet window and watch replication lag; index builds consume I/O on every member. |

## 4. Transactions, Concerns, Replication

| ID | Severity | Rule |
|---|---|---|
| MG-TX-01 | high | Transactions need a replica set or sharded cluster, finish within the lifetime limit (under one minute by default), and wait at most a few milliseconds for locks; keep them small and retry on transient errors. |
| MG-TX-02 | high | Read-your-writes across members needs causally consistent sessions with `"majority"` read and write concerns; the default `"local"` read concern can return data that is later rolled back. |
| MG-TX-03 | high | Avoid arbiters in replica sets that rely on `w: "majority"`: a primary-secondary-arbiter set needs both data nodes for majority writes. Use three data-bearing members. |
| MG-TX-04 | medium | Set `wtimeout` with any write concern that may be unachievable; without it the write can block indefinitely. Cap long server work with `maxTimeMS`, not a low `socketTimeoutMS`. |

## 5. Sharding

| ID | Severity | Rule |
|---|---|---|
| MG-SH-01 | high | Choose the shard key by cardinality, frequency, and monotonicity: low cardinality caps the number of chunks, a dominant value creates jumbo chunks, and a monotonic key (timestamp, ObjectId, counter) sends every insert to one shard. Hash a monotonic key, and keep the shard key in common query filters to avoid scatter-gather. |
| MG-SH-02 | medium | Measure candidates with `analyzeShardKey` and sampled queries before choosing; prefer `refineCollectionShardKey` (append fields) over `reshardCollection` when a key must change. |
| MG-SH-03 | medium | Always write the shard key fields; documents missing them land in the null range and form a hidden hotspot. |

## 6. Connections and Change Streams

| ID | Severity | Rule |
|---|---|---|
| MG-CN-01 | high | Create one `MongoClient` per process and reuse it; in serverless functions create it outside the handler with a small `maxPoolSize` and `minPoolSize` 0. Server connections add up as pool size times members times application instances. |
| MG-CN-02 | medium | Each open change stream holds a connection; size the pool above the stream count, persist resume tokens, and handle invalidate events. Time series collections do not support change streams. |
| MG-OPS-01 | high | Back up with continuous or snapshot backups (Atlas backups, filesystem snapshots of every replica set and the config servers, or `mongodump` for small sets) and prove them by restoring to a separate deployment (OP-02); `mongodump` alone is not a consistent backup of a sharded cluster under writes. |

## 7. Verification Commands

```javascript
db.orders.find({ tenantId: t, status: "open" }).sort({ createdAt: -1 }).explain("executionStats")
db.orders.aggregate([{ $indexStats: {} }])
db.orders.aggregate([{ $project: { size: { $bsonSize: "$$ROOT" } } }, { $sort: { size: -1 } }, { $limit: 5 }])
db.currentOp({ "secs_running": { $gte: 5 } })
rs.status()   // replication lag and member health
```

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| 9.0 release date, transaction cap, and per-operation memory limit | <https://www.mongodb.com/docs/manual/release-notes/9.0/> |
| 8.0 line and its patch releases | <https://www.mongodb.com/docs/manual/release-notes/8.0/> |
| Document size, nesting depth, and namespace limits | <https://www.mongodb.com/docs/manual/reference/limits/> |
| Data accessed together stored together; embed versus reference criteria | <https://www.mongodb.com/docs/manual/data-modeling/>, <https://www.mongodb.com/docs/manual/data-modeling/best-practices/> |
| Schema design patterns | <https://www.mongodb.com/docs/manual/data-modeling/design-patterns/> |
| Schema validation levels and actions | <https://www.mongodb.com/docs/manual/core/schema-validation/> |
| One index per query | <https://www.mongodb.com/docs/manual/applications/indexes/> |
| ESR guideline, range operators, `$in` threshold | <https://www.mongodb.com/docs/manual/tutorial/equality-sort-range-guideline/> |
| Partial index rules | <https://www.mongodb.com/docs/manual/core/index-partial/> |
| TTL index behavior | <https://www.mongodb.com/docs/manual/core/index-ttl/> |
| Explain output and stages | <https://www.mongodb.com/docs/manual/reference/explain-results/> |
| Write concern defaults, arbiters, and the 8.0 majority change | <https://www.mongodb.com/docs/manual/reference/write-concern/> |
| Read concern default and causal consistency | <https://www.mongodb.com/docs/manual/reference/mongodb-defaults/> |
| Transaction limits and production considerations | <https://www.mongodb.com/docs/manual/core/transactions-production-consideration/> |
| Shard key selection and changing a shard key | <https://www.mongodb.com/docs/manual/core/sharding-choose-a-shard-key/>, <https://www.mongodb.com/docs/manual/core/sharding-shard-key/> |
| Change streams requirements | <https://www.mongodb.com/docs/manual/changestreams/> |
| Connection pool defaults and timeouts | <https://www.mongodb.com/docs/manual/administration/connection-pool-overview/> |
| The rule IDs and severities | this package's chosen design, not a validated optimum |
