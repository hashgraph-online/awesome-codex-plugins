---
name: database-operations
description: "Use when schema changes, backfills, indexes, destructive queries, query plans, locks, lag, throttles, or aborts matter"
---

# Database Operations And Schema Changes

## Iron Law

```
NO PRODUCTION DATASTORE CHANGE WITHOUT LOCK/LAG ASSESSMENT, THROTTLE, ABORT, AND VERIFICATION
```

If you cannot pause, measure, and verify the change, it should not run against production state.

## Overview

Database changes are production releases with lock, lag, plan, and data-correction risk.

**Core principle:** make schema, index, backfill, and maintenance changes observable, throttleable, verifiable, and reversible or forward-fixable.

## When To Use

- The user asks about online schema changes, index changes, production migrations, backfills, query-plan regressions, locks, replicas, compaction, vacuuming, or data maintenance.
- A data migration can affect latency, availability, data correctness, or rollback.
- A cleanup or destructive change touches production data.
- Query behavior changed after release or index/schema modification.

## When Not To Use

- The question is abstract storage or consistency choice; use `distributed-data-and-consistency` instead.
- The request is primarily about splitting a data model across databases, shards, or mutation boundaries; use `distributed-data-and-consistency` instead.
- The request is general rollout sequencing without database risk; use `progressive-delivery` instead.
- The primary concern is recovery after corruption or destructive change; use `backup-and-recovery` instead.
- The work is warehouse/ETL freshness; use `data-pipeline-reliability` instead.

## Info To Gather

- Current work phase, next decision, what is known, and assumptions where details are missing.
- Datastore type, topology, table/collection size, write rate, read patterns, and critical queries.
- Whether the datastore is on a user-critical path, with failover mode, replica/site dependency behavior, connection or session-establishment limits, metadata/control-plane health, query tail latency, restore readiness, and write behavior during failover.
- Proposed DDL/DML, index, backfill, cleanup, or maintenance operation.
- Source and target versions, replication or change-capture mode, dump/snapshot method, writes during copy, and known engine or dependency defects for data migrations.
- Lock behavior, replication lag, write amplification, query-plan risks, sequence or counter headroom, and operational windows.
- Schema object permissions, grants, and service principals for every reader, writer, and query path affected by the change.
- Backfill batch size, throttle rules, pause/abort controls, checkpointing, and idempotency.
- Verification queries, counts, checksums, invariants, and sampled correctness checks.
- Rollback versus forward-fix options, backup/restore test results, and destructive cleanup delay.
- Monitoring: latency, errors, lock waits, lag, slow queries, saturation, job progress, and user impact.

## Workflow

1. **Classify the change.** Separate additive schema, index, backfill, dual-write, cutover, cleanup, query-plan, and maintenance work.
2. **Assess production risk.** Identify locks, lag, write amplification, query-plan shifts, shard/partition effects, sequence or counter exhaustion, cache churn, metadata/control-plane operations, session establishment, failover interactions, replica or site dependency coupling, and whether user-critical paths depend on the datastore behavior during those conditions.
3. **Use compatibility phases with an explicit copy boundary.** Expand with additive structure that old code tolerates. Deploy mixed-version-compatible readers and writers, then establish dual-write, change capture, or another write-consistency mechanism before or atomically with the backfill snapshot boundary. Run a checkpointed backfill, reconcile all mutations since that boundary, switch reads and new writes in controlled steps, stop old writes, observe, and contract only after no supported version or recovery path needs the old structure. Name the authoritative state in every phase.
4. **Validate schema permissions.** For every changed object, run the old and new read/write/query paths with the production identities that will use them; a schema that exists but denies the caller is still a failed rollout.
5. **Validate data-migration compatibility.** Before moving data between versions, stores, or capture modes, verify source/target version behavior, dump or snapshot consistency, write handling during copy, replication semantics, known defects, and the manual fallback path.
6. **Throttle and checkpoint.** Run in small batches with pause/abort controls, progress tracking, idempotency, and load-sensitive throttles.
7. **Validate data.** Use verification queries, invariant checks, counts, sampling, and reconciliation before declaring completion.
8. **Delay destructive cleanup.** Keep rollback/forward-fix options until telemetry shows the new path is stable.
9. **Monitor during rollout.** Watch user symptoms, query latency, error rate, locks, lag, saturation, and job health.
10. **Document recovery by phase.** For every phase, state pause, rollback, roll-forward, reconciliation, restore, and manual repair options. Test mixed-version behavior and identify the point beyond which reverting code alone cannot restore correctness. Do not label a phase rollback-safe when dual writes, new-only semantics, or irreversible data changes require reconciliation.

## Synthesized Default

Use compatible expand/contract migrations, throttled idempotent backfills, explicit abort criteria, delayed destructive cleanup, and verification queries. Treat database operations as release events with telemetry, user confirmation for risky steps, and rollback checks; include partitioning and shard-map effects when data placement changes.



## Exceptions

- Small low-risk changes may run directly if lock/lag behavior is understood and rollback is simple.
- Destructive changes require backup/restore confidence and delayed cleanup unless data is provably disposable.
- Query-plan regressions may require emergency mitigation before a full migration plan, but details and follow-up remain required.
- Engine-specific mechanisms can be used, but the skill should express the required capability, not prescribe a product.

## Response Quality Bar

- Lead with the migration safety decision, blockers, or execution plan requested.
- Cover locks, query plans, backfill throttling, replication lag, verification, and rollback before optional database topics.
- Make recommendations actionable with checks, stop conditions, and rollback or pause criteria where relevant.
- Name the details to inspect, such as table size, write rate, lock behavior, replica lag, batch metrics, and validation queries; do not state details you have not seen.
- Stay technology-agnostic by default: do not introduce provider, product, framework, database, protocol, or command names unless the user supplied them or explicitly requested tool-specific guidance.
- Stay inside database change execution. Route broader distributed consistency only when semantic consistency is unresolved.
- Be concise: avoid generic database background and prefer compact phased runbooks.
- Scale the artifact to the request: a narrow index, query-plan, or maintenance change needs its risk, throttle, abort, verification, and recovery; add compatibility, copy-boundary, backfill, and cleanup modules only when data or schema moves.

## Required Outputs

- Output shape: render the matching shared template headings or tables in the reply, or use the same shape.
- Database change plan with authoritative state, copy/write-consistency boundary, mixed-version behavior, confirmation points, per-phase recovery, reconciliation, and the point of no simple code rollback.
- Lock, lag, write-amplification, and query-plan risk assessment.
- Critical-path database risk table covering failover, replica or site dependency behavior, connection or session-establishment limits, metadata/control-plane health, query tail latency, restore readiness, and write behavior.
- Data migration compatibility matrix covering source/target versions, capture or dump mode, writes during copy, consistency validation, known defects, and fallback path.
- Schema permission compatibility matrix covering old and new read/write/query paths, caller identity, required grant, and failure response.
- Sequence, counter, identifier, and bounded-column headroom for write paths that can exhaust a stored value.
- Backfill or maintenance runbook with throttle, pause, abort, and checkpointing.
- Verification query/invariant plan.
- Monitoring and alert additions for the change window.
- Rollback or forward-fix decision record.
- Cleanup plan with delay, and check.

## Checks Before Moving On

- `lock_lag_check`: lock behavior, replication lag, and write amplification are assessed.
- `db_critical_path`: database behavior on user-critical paths is assessed for failover, replica or site dependency behavior, connection or session-establishment limits, metadata/control-plane health, query tail latency, restore readiness, and write behavior.
- `migration_compatibility`: source/target versions, capture or dump mode, writes during copy, consistency validation, known defects, and fallback path are checked.
- `schema_permission_compatibility`: changed objects have permission checks for every production reader, writer, and query path.
- `bounded_value_headroom`: sequences, counters, identifiers, and bounded columns on write paths have headroom checks or alerts.
- `throttle_abort`: batch size, throttle, pause, abort, and confirmation point are defined.
- `verification_check`: data correctness verification queries or invariants exist.
- `rollback_check`: each phase has a pause, rollback or forward-fix, reconciliation, and repair path; the plan names when code rollback alone stops being safe.
- `cleanup_delay`: destructive cleanup is delayed until cutover is verified.

## Red Flags - Stop And Rework

- A migration runs as one unbounded transaction or job.
- Data moves while writes continue without proof that the dump, snapshot, or change-capture mode preserves consistency.
- A backfill starts before the write-consistency mechanism or snapshot boundary can account for concurrent mutations.
- A transition is called rollback-safe even though new-only writes or semantics would require reconciliation after code rollback.
- Verification is "job completed" without data correctness checks.
- Destructive cleanup happens before old and new paths have been compared.
- Query plans are assumed unchanged after index/schema changes.
- Schema objects are created or changed without validating grants for the identities that query them.
- Monotonic counters or sequence columns can exhaust silently on a write path.
- A replica, site, or dependency outage restarts writes or readers that should degrade.
- There is no clear pause or abort mechanism.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Treating migrations as developer chores | Treat them as production releases. |
| Backfilling too fast | Throttle by user impact, lag, locks, and saturation. |
| Trusting row counts only | Add invariants, sampling, and reconciliation. |
| Removing old paths immediately | Delay cleanup until rollback is unnecessary. |
