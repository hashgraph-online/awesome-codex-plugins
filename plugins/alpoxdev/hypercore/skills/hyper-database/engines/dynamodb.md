# Amazon DynamoDB

Engine guide for Amazon DynamoDB, including global tables. Read it after `rules/engine-detection.md` routes here. The access-pattern table from `rules/data-modeling.md` §1 is the design input; DynamoDB has no ad hoc query planner to fall back on. Findings cite the `DY-*` IDs.

## 1. Dated Facts

> Volatile. Checked 2026-11-07 against the DynamoDB quotas and constraints pages; recheck before a design depends on a number.

| Fact | Value |
|---|---|
| Item size | 400 KB including attribute names |
| Per-partition ceiling | 3,000 read units and 1,000 write units per second |
| Capacity units | 1 RCU = one strongly consistent read per second of up to 4 KB (two eventually consistent); 1 WCU = one write per second of up to 1 KB |
| Indexes | 5 local secondary indexes per table (cannot be deleted later); 20 global secondary indexes per table by default; vector indexes count against the GSI quota |
| Item collections | Tables with an LSI cap each partition-key value at 10 GB |
| Transactions | Up to 100 unique items and 4 MB per transaction; each item costs a prepare and a commit |
| Batches | `BatchGetItem` up to 100 items, `BatchWriteItem` up to 25 puts or deletes; both can partially succeed |
| Default capacity mode | On-demand |

## 2. Table Design

| ID | Severity | Rule |
|---|---|---|
| DY-MOD-01 | critical | List every access pattern (key condition, sort, filter, page size, rate) before creating a table; each pattern maps to a `GetItem`, a `Query` on the table, or a `Query` on an index. A pattern served only by `Scan` is a design defect. |
| DY-MOD-02 | high | Keep as few tables as the access patterns allow and store related items under one partition key so one `Query` returns them (single-table or few-table design). Separate tables are justified for high-volume time series, very different access patterns, or different operational needs (backup, retention, permissions). |
| DY-MOD-03 | high | Use generic key names (`PK`, `SK`) with typed prefixes (`USER#123`, `ORDER#2026-11-07#456`) when several entity types share a table, and write the key schema down beside the access-pattern table. |
| DY-MOD-04 | medium | Use hierarchical sort keys (`COUNTRY#KR#CITY#SEOUL`) to query at any level with `begins_with` and `between`; keep a `v0` item for the latest version beside history items when versions matter. |
| DY-MOD-05 | high | Keep items well under 400 KB: split large parts into separate items of the same collection, compress, or store the object in S3 and keep its key (and clean up orphans, because there is no cross-store transaction). |
| DY-MOD-06 | medium | Single-table design costs flexibility and analytics: export to an analytics store instead of scanning, and plan a backfill when a new access pattern needs a new key shape. |

## 3. Partition Keys and Throughput

| ID | Severity | Rule |
|---|---|---|
| DY-PK-01 | critical | Choose a partition key with high cardinality and even traffic (user, device, tenant with many tenants); never a status, a date bucket that takes all writes, or a single celebrity entity. |
| DY-PK-02 | high | Do the per-item math: item size rounded up to 4 KB for reads and 1 KB for writes, times the request rate, against the per-partition ceiling. A 20 KB item read strongly costs 5 RCU, so one key tops out near 600 strong reads per second. |
| DY-PK-03 | high | Shard hot write keys with a suffix (random, or calculated from a known attribute so single-item reads still work) and merge the shards on read. |
| DY-PK-04 | medium | Adaptive capacity and burst capacity soften short spikes but do not lift the per-partition ceiling, and adaptive capacity cannot split an item collection on a table with an LSI. |
| DY-PK-05 | medium | When bulk loading, interleave partition keys instead of writing one key's items at a time. |

## 4. Indexes

| ID | Severity | Rule |
|---|---|---|
| DY-IX-01 | high | Default to GSIs; create an LSI only when a strongly consistent alternate sort within the same partition is required and the 10 GB item-collection cap is acceptable, because an LSI can only be created with the table and never removed. |
| DY-IX-02 | medium | Project only the attributes the index's queries return; `ALL` roughly doubles storage and write cost. Projected non-key attributes share a quota of 100 across indexes. |
| DY-IX-03 | medium | Use sparse indexes (write the index key attribute only on items that should appear) to query a subset without a filter. |
| DY-IX-04 | high | A GSI with too little write capacity throttles writes to the base table; size GSI capacity with the table and watch its throttling metrics. GSIs are eventually consistent. |

## 5. Reads, Writes, Transactions

| ID | Severity | Rule |
|---|---|---|
| DY-RW-01 | high | Paginate with `Query`, `Limit`, and `ExclusiveStartKey`; filter expressions run after reading and still consume capacity for every item read. |
| DY-RW-02 | high | Reserve `Scan` for exports and maintenance, with a small `Limit` and its own capacity budget; one scan page can consume a burst of capacity from one partition. |
| DY-RW-03 | high | Use conditional writes (`ConditionExpression` with a version attribute) for optimistic locking and uniqueness; `UpdateItem` on one item is already atomic. |
| DY-RW-04 | high | Use `TransactWriteItems` only for real multi-item invariants; it doubles capacity, cancelled transactions still consume capacity, and stream consumers see the items separately. Use `ClientRequestToken` for idempotent retries. |
| DY-RW-05 | high | Retry `UnprocessedItems` and `UnprocessedKeys` from batch calls with exponential backoff. |
| DY-RW-06 | medium | Global tables resolve conflicts last-writer-wins; optimistic locking does not hold across Regions, and transactions are not atomic across replicas. Route writes for one item to one Region when conflicts matter. |

## 6. TTL, Streams, Operations

| ID | Severity | Rule |
|---|---|---|
| DY-OP-01 | medium | TTL attributes are numbers in Unix epoch seconds; deletion happens within days, not at expiry, so filter expired items in reads. |
| DY-OP-02 | medium | Streams keep records for 24 hours and order them per item only; consumers are idempotent, and the view type cannot change without recreating the stream. |
| DY-OP-03 | high | Turn on point-in-time recovery for tables holding data you cannot rebuild, and restore-test it to a new table. |
| DY-OP-04 | medium | Choose on-demand for unknown or spiky traffic and provisioned with auto scaling for steady traffic; switching to on-demand is limited per day. |
| DY-OP-05 | medium | Collect evidence with `ReturnConsumedCapacity`, CloudWatch throttling metrics, and Contributor Insights for hot keys. |

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| Index quotas, vector index quotas, projected attribute quota, default throughput quotas | <https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/ServiceQuotas.html> |
| Item size, capacity unit sizes, batch and transaction limits, key lengths, mode switching | <https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Constraints.html> |
| Access-pattern-first design and few tables | <https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-general-nosql-design.html>, <https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-table-design.html> |
| Per-partition ceilings and the 20 KB item example | <https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-partition-key-design.html> |
| Write sharding | <https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-partition-key-sharding.html> |
| Sort key hierarchies and version items | <https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-sort-keys.html> |
| LSI permanence, the 10 GB item collection cap, projections | <https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-indexes-general.html> |
| Query versus scan | <https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-query-scan.html> |
| Transaction cost, cancellation, idempotency tokens, isolation | <https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/transaction-apis.html> |
| Optimistic locking and global-table conflict resolution | <https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/BestPractices_ImplementingVersionControl.html> |
| Burst and adaptive capacity | <https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/burst-adaptive-capacity.html> |
| Streams retention and ordering | <https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Streams.html> |
| TTL format and deletion timing | <https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/TTL.html> |
| Capacity modes | <https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/capacity-mode.html> |
| The rule IDs and severities | this package's chosen design, not a validated optimum |
