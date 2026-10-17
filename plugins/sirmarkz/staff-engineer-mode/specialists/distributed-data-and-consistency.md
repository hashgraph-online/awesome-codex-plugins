---
name: distributed-data-and-consistency
description: "Use when storage choice, database splits, sharding, transactions, consistency, locks, conflicts, or failover matter"
---

# Distributed Data And Consistency

## Iron Law

```
NO READ OR WRITE PATH WITHOUT NAMED CONSISTENCY, CONFLICT, AND FAILOVER BEHAVIOR
```

For each read path and each write path, the design must say which consistency guarantee holds, what happens to a conflicting concurrent write, and what users observe during failover or replication lag. "Eventually consistent" without saying what users see between events, or "transactional" without saying which operations span the boundary, is not a design.

## Overview

Data architecture starts with semantics, not storage brands.

**Core principle:** choose storage, replication, transactions, consistency, and sharding from the correctness guarantees each operation needs.

## When To Use

- The user is designing or changing storage choice, replication, consistency, transactions, sharding, hot keys, data correctness, distributed locks, or data responsibility.
- A service boundary changes who is responsible for mutating data.
- The design needs to choose between strong, eventual, read-your-writes, monotonic, causal, or quorum-style behavior.
- The user asks whether stale reads, duplicate writes, or conflicts are acceptable.
- Time, clock, TTL, lease, ordering, or stored-data semantic quality affects correctness.

## When Not To Use

- The request is only cache TTL, invalidation, stampede, or materialized-view operation; use `caching-and-derived-data` instead.
- The question is online schema/backfill execution; use `database-operations` instead.
- The work is service event choreography; use `event-workflows` instead.
- The request is warehouse/ETL freshness rather than application data correctness; use `data-pipeline-reliability` instead.
- The request is source-of-record lineage or recompute blast radius for reported figures; use `data-lineage-and-provenance`.

## Info To Gather

- Current work phase, next decision, what is known, and assumptions where details are missing.
- Data classes: money, authz, user settings, content, cache, derived state, analytics, notifications, access logs, or ML features.
- Operations: create, update, delete, read, list, search, reconcile, compensate, and repair.
- Correctness expectations: uniqueness, ordering, freshness, read-your-writes, conflict handling, idempotency, and durability.
- Access patterns, read/write volume, fanout, hot keys, tenant/shard routing, and growth forecast.
- Failure modes: partial writes, failover, replication lag, split brain, retries, duplicate leaders, and operator repair.
- Migration constraints, responsibility, change history needs, and backup/restore requirements.
- Clock sources, skew bounds, leap-second and daylight-saving behavior, monotonic versus wall-clock use, lease/TTL windows, scheduler behavior, and logical-clock needs.
- Standing at-rest quality controls: golden records, recurring reconciliation, semantic anomaly detection, and repair ownership for stored business data.

## Workflow

1. **Classify data by consequence.** Financial, authorization, privacy, and audit data usually need stronger guarantees than analytics or derived views.
2. **Write operation semantics.** For each critical operation, define allowed staleness, concurrent-write behavior, idempotency, and durability. First decide whether to prevent or reject conflicts through serialization, conditional writes, compare-and-swap, version preconditions, or retry. When concurrent writes are accepted, choose an explicit resolution rule such as last-writer-wins with its silent-loss risk, a commutative or convergent merge, or an application-level reconciliation. Name the mechanism and assumptions behind each read or session guarantee.
3. **State quorum assumptions.** When using quorum-style reads and writes, record replica-set membership, whether reads and writes contact the same set, acknowledgement and durability semantics, version ordering, concurrent-write resolution, sloppy or hinted quorum behavior, failure assumptions, and repair. `R + W > N` proves intersection only under those assumptions; it does not by itself establish linearizability, read-your-writes, or correct conflict resolution.
4. **Choose consistency deliberately.** Use the weakest guarantee that preserves correctness and user expectation; document the tradeoff.
5. **Choose time and ordering deliberately.** Use monotonic clocks for elapsed time, wall clocks only for human timestamps, explicit skew bounds for leases and TTLs, define leap-second and daylight-saving behavior for schedulers, and use logical clocks where wall-clock ordering is unsafe.
6. **Avoid cross-service transactions.** Prefer local transactions plus outbox, sagas, reconciliation, or compensating actions over distributed two-phase commit.
7. **Plan partitioning early.** Choose shard/tenant keys, hot-key mitigations, locality needs, shard-map responsibility, resharding path, and responsibility boundaries.
8. **Treat locks and leaders as dangerous.** Use well-tested coordination primitives when necessary, and design work to be idempotent under duplicate execution.
9. **Define repair and verification.** Include reconciliation jobs, invariants, audit trails, manual repair safety, and standing data-quality checks that catch semantic drift in stored records.
10. **Route operational changes.** Schema/backfill execution goes to database operations; cache mechanics go to caching.

## Synthesized Default

Default to the simplest storage and consistency model that satisfies operation semantics. Keep data responsibility local where possible, co-locate data that must transact together, use idempotency and durable state transitions, and avoid custom distributed coordination. When weaker consistency is chosen, state exactly what users may observe and how repair works.



## Exceptions

- Financial, authorization, inventory, and destructive operations may require strong consistency or formal modeling.
- High-scale read paths may accept stale or derived reads when user impact and repair are explicit.
- Multi-step workflows across independent mutation boundaries should use sagas or reconciliation rather than pretending one atomic transaction exists.
- Distributed locks are acceptable only with a well-tested primitive, lease semantics, fencing or idempotency, and failure tests.

## Response Quality Bar

- Lead with the consistency decision, tradeoff, or unresolved blocker.
- Cover data semantics, stale-read impact, conflicts, failure behavior, and operational cost before optional distributed-systems breadth.
- Make recommendations actionable with checks, stop conditions, and validation criteria where relevant.
- Name the details to inspect, such as invariants, latency budgets, conflict rates, replication behavior, and failure assumptions; do not state details you have not seen.
- Stay technology-agnostic by default: do not introduce provider, product, framework, database, protocol, or command names unless the user supplied them or explicitly requested tool-specific guidance.
- Stay inside the data consistency decision. Mention caches, workflows, or schema execution only when they materially change semantics.
- Be concise: avoid generic CAP/PACELC exposition and prefer decision matrices.
- Scale the artifact to the request: a narrow operation needs its consistency, concurrency, failover, and repair semantics; add storage, replication, quorum, sharding, time, and standing-quality modules only when the decision depends on them.

## Required Outputs

- Output shape: render the matching shared template headings or tables in the reply, or use the same shape.
- Data classification table.
- Operation-level consistency matrix.
- Storage decision record with rejected alternatives.
- Replication, failover, and conflict-resolution model.
- Conflict strategy covering prevention or rejection (serialization, conditional write, compare-and-swap, version precondition, retry) or an explicit accepted-concurrency resolution rule.
- Quorum assumption record covering membership, replica-set overlap, acknowledgements, durability, version ordering, concurrency, sloppy-quorum behavior, failure assumptions, and repair when a quorum mechanism is used.
- Sharding/hot-key/tenant-routing plan.
- Transaction, outbox, saga, or reconciliation plan.
- Time, clock, leap-second, daylight-saving, lease, TTL, and ordering decision where temporal correctness matters.
- Standing at-rest data-quality control: golden-record resolution, recurring reconciliation, anomaly detection, and repair owner.
- Correctness verification and repair plan.

## Checks Before Moving On

- `semantics_check`: every critical operation has freshness, ordering, idempotency, conflict, and durability semantics.
- `conflict_strategy`: each critical mutation prevents, rejects, retries, or resolves concurrent writes with a named mechanism and user-visible outcome.
- `quorum_assumptions`: any quorum claim states the conditions needed for intersection and does not infer linearizability or session guarantees from `R + W > N` alone.
- `failover_check`: replication-lag and failover behavior is defined for each read/write path, including the data-loss bound and split-brain prevention.
- `consistency_choice`: chosen guarantees are justified by user consequence and failure behavior.
- `responsibility_check`: every data class has an explicit mutation boundary and repair path.
- `partition_check`: shard/tenant key, hot-key risk, and resharding approach are addressed where scale requires it.
- `repair_check`: invariants, reconciliation, change history, or manual repair path exists for known inconsistency modes.
- `clock_ordering`: elapsed-time, wall-clock, skew, leap-second, daylight-saving, lease/TTL, and logical-clock choices are explicit where correctness depends on time.
- `data_quality`: stored business data has reconciliation, golden-record, semantic anomaly, or repair controls when silent drift is plausible.

## Red Flags - Stop And Rework

- Storage is selected before data semantics are written.
- "Eventually consistent" is used without saying what users can observe or how conflicts repair.
- Distributed locks are hand-rolled.
- Hot keys or tenant skew are ignored for a high-scale path.
- Cross-service writes are described as atomic without a mechanism or compensation plan.
- Wall-clock timestamps are used for ordering, leases, TTL expiry, or scheduling without skew, leap-second, daylight-saving, and rollback behavior.
- Stored business data can silently drift wrong with no recurring reconciliation or semantic anomaly control.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| One consistency level for everything | Decide per operation and data class. |
| Using caches to solve semantics | Decide stale-read semantics here, then route cache mechanics. |
| Ignoring repair | Define invariants, reconciliation, audit, and correction paths. |
| Treating sharding as later | At least identify shard keys and hot-key risks early. |
| Trusting wall-clock order | Use monotonic time for durations and logical clocks when ordering must survive skew. |
| Treating stored data quality as a dashboard issue | Define standing reconciliation and repair ownership for semantic correctness. |
