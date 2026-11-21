# Analytical and Special-Purpose Engines

Engine guide for ClickHouse, time-series extensions, vector search, and search engines. These stores sit beside a system of record; read `rules/data-modeling.md` §6 for the consistency rules every derived store follows. Findings cite the `AN-*` IDs.

> Volatile. Defaults and thresholds below were checked 2026-11-07 against each project's documentation; recheck before a design depends on a number.

## 1. ClickHouse

| ID | Severity | Rule |
|---|---|---|
| AN-CH-01 | high | `ORDER BY` decides on-disk order, compression, and the sparse primary index, and cannot be added later without rebuilding the table. Lead it with low-cardinality columns that queries filter on, then time (often `toDate(ts)`); four or five columns are usually enough. |
| AN-CH-02 | high | Insert in batches (at least 1,000 rows, ideally 10,000 to 100,000) at about one insert per second per table; small frequent inserts create too many parts. When the client cannot batch, use `async_insert=1` with `wait_for_async_insert=1`. |
| AN-CH-03 | high | Avoid `ALTER TABLE ... UPDATE/DELETE` mutations on hot paths; they rewrite whole parts asynchronously and cannot be rolled back. Model changes as inserts with a `ReplacingMergeTree` or `CollapsingMergeTree`, or use lightweight deletes sparingly. |
| AN-CH-04 | medium | Partitioning is for lifecycle (drop or move old data), not query speed; keep the partition key low-cardinality (for example `toStartOfMonth(date)`, well under 1,000 values) or do not partition. |
| AN-CH-05 | medium | Use `LowCardinality(String)` for strings with up to roughly 10,000 distinct values. |
| AN-CH-06 | medium | Retried inserts are deduplicated only when the batch is byte-identical and the table keeps a deduplication window (replicated tables by default). |

## 2. Time-Series in PostgreSQL

| ID | Severity | Rule |
|---|---|---|
| AN-TS-01 | medium | TimescaleDB hypertables partition by time into chunks; size the chunk interval so the active chunk and its indexes fit in memory, and include the time column in unique constraints. Use retention and compression policies instead of row-by-row deletes. |
| AN-TS-02 | low | Without the extension, native range partitioning by time plus `DETACH PARTITION ... CONCURRENTLY` and `DROP` gives the same retention pattern. |

## 3. Vector Search (pgvector and Others)

| ID | Severity | Rule |
|---|---|---|
| AN-VE-01 | high | An approximate index changes results: no index means exact search with perfect recall. Measure recall against exact search on a sample before and after adding HNSW or IVFFlat. |
| AN-VE-02 | high | Filters are applied after the approximate scan, so a selective filter can return far fewer rows than `LIMIT`. Use a B-tree on the filter with exact search for selective filters, partial indexes per hot filter value, partitioning per tenant, or iterative scans where supported. |
| AN-VE-03 | medium | HNSW (defaults `m = 16`, `ef_construction = 64`, query `hnsw.ef_search = 40`) gives better speed and recall at higher build time and memory; IVFFlat needs data loaded first, `lists` near rows/1000 (up to 1M rows) or sqrt(rows) beyond, and `probes` raised from its default of 1. |
| AN-VE-04 | medium | Match the operator to the operator class (`<->` with `vector_l2_ops`, `<#>` with `vector_ip_ops`, `<=>` with `vector_cosine_ops`); a mismatch falls back to a sequential scan. |
| AN-VE-05 | medium | Respect dimension limits (`vector` indexes up to 2,000 dimensions; `halfvec` up to 4,000); larger embeddings need `halfvec`, quantization, or dimension reduction. |
| AN-VE-06 | medium | Build vector indexes after bulk load with `CREATE INDEX CONCURRENTLY`, enough `maintenance_work_mem`, and parallel maintenance workers. |
| AN-VE-07 | medium | One shared vector index across tenants lets one tenant's data degrade another's recall; partition by tenant when isolation matters. |

## 4. Search Engines (Elasticsearch, OpenSearch)

| ID | Severity | Rule |
|---|---|---|
| AN-SE-01 | high | Define explicit mappings in production; existing field mappings cannot change without a reindex. |
| AN-SE-02 | high | Cap dynamic fields (`index.mapping.total_fields.limit`, `dynamic: strict` or `false`) when documents carry user-supplied keys; unbounded mappings exhaust memory. |
| AN-SE-03 | medium | Map a field both as `text` (search) and `keyword` (sort, aggregate, exact filter) when both are needed. |
| AN-SE-04 | medium | The search index is a derived store: rebuildable from the system of record with a reindex job and an alias swap. |

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| Sparse primary index, granules, and key order | <https://clickhouse.com/docs/guides/clickhouse/data-modelling/sparse-primary-indexes> |
| Ordering keys cannot be added later | <https://clickhouse.com/docs/concepts/best-practices/choosing-a-primary-key> |
| Batch sizes, insert rate, async inserts, and deduplication | <https://clickhouse.com/docs/concepts/best-practices/selecting-an-insert-strategy> |
| Mutations rewrite parts | <https://clickhouse.com/docs/concepts/best-practices/avoid-mutations> |
| Partitioning as data management and low partition-key cardinality | <https://clickhouse.com/docs/concepts/best-practices/partitioning-keys> |
| `LowCardinality` thresholds | <https://clickhouse.com/docs/reference/data-types/lowcardinality> |
| Hypertables and chunk sizing | <https://www.tigerdata.com/docs/learn/hypertables/understand-hypertables> |
| pgvector exact search, HNSW and IVFFlat parameters, operators, filtering, dimension limits | <https://github.com/pgvector/pgvector> |
| Elasticsearch mappings, immutability, and mapping explosion | <https://www.elastic.co/docs/manage-data/data-store/mapping> |
| The rule IDs and severities | this package's chosen design, not a validated optimum |
