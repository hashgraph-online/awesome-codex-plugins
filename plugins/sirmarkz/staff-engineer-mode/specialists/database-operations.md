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
- Whether the datastore is on a user-critical path, with failover mode, connection limits, query tail latency, restore readiness, and write behavior during failover.
- Proposed DDL/DML, index, backfill, cleanup, or maintenance operation.
- Lock behavior, replication lag, write amplification, query-plan risks, and operational windows.
- Backfill batch size, throttle rules, pause/abort controls, checkpointing, and idempotency.
- Verification queries, counts, checksums, invariants, and sampled correctness checks.
- Rollback versus forward-fix options, backup/restore test results, and destructive cleanup delay.
- Monitoring: latency, errors, lock waits, lag, slow queries, saturation, job progress, and user impact.

## Workflow

1. **Classify the change.** Separate additive schema, index, backfill, dual-write, cutover, cleanup, query-plan, and maintenance work.
2. **Assess production risk.** Identify locks, lag, write amplification, query-plan shifts, shard/partition effects, cache churn, failover interactions, and whether user-critical paths depend on the datastore behavior during those conditions.
3. **Use expand/contract in named phases.** Run schema evolution as four sequential phases — Expand (add the new structure, old code ignores it), Migrate (backfill data into the new structure), Transition (new code reads/writes both), Contract (remove the old structure once nothing references it). Each phase except Contract is rollback-safe on its own: a failed Expand drops the new structure, a failed Migrate leaves the old structure authoritative with the new partially populated, a failed Transition reverts code while the old structure still serves; a failed Contract has already validated everything, so investigate before retrying rather than rolling back.
4. **Throttle and checkpoint.** Run in small batches with pause/abort controls, progress tracking, idempotency, and load-sensitive throttles.
5. **Validate data.** Use verification queries, invariant checks, counts, sampling, and reconciliation before declaring completion.
6. **Delay destructive cleanup.** Keep rollback/forward-fix options until telemetry shows the new path is stable.
7. **Monitor during rollout.** Watch user symptoms, query latency, error rate, locks, lag, saturation, and job health.
8. **Document recovery.** State rollback, forward-fix, restore, and manual repair options before running.

## Synthesized Default

Use compatible expand/contract migrations, throttled idempotent backfills, explicit abort criteria, delayed destructive cleanup, and verification queries. Treat database operations as release events with telemetry, user confirmation for risky steps, and rollback checks; include partitioning and shard-map effects when data placement changes.



## Phase Behavior

- Ideation: identify risks, defaults, unknowns, options, and the next decision before code exists.
- Design: shape the target artifact, tradeoffs, checks, and details to gather.
- Development: guide sequencing, code boundaries, checks, and acceptance criteria.
- Testing: define release-blocking tests, evals, fixtures, and failure probes.
- Release: define rollout, observability, abort, rollback, and readiness details.
- Maintenance: define owners, drift checks, cleanup triggers, and refresh cadence.
- Existing artifact: use current code, docs, telemetry, incidents, or diffs as context for the next engineering decision; do not wait for a finished artifact before guiding design, build, release, or operation.
- Missing details: state assumptions and say what to check next instead of blocking lifecycle guidance.

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

## Required Outputs

- Database change plan with phases, confirmation points, and rollback checks.
- Lock, lag, write-amplification, and query-plan risk assessment.
- Critical-path database risk table covering failover, connection limits, query tail latency, restore readiness, and write behavior.
- Backfill or maintenance runbook with throttle, pause, abort, and checkpointing.
- Verification query/invariant plan.
- Monitoring and alert additions for the change window.
- Rollback or forward-fix decision record.
- Cleanup plan with delay, and check.

## Checks Before Moving On

- `lock_lag_check`: lock behavior, replication lag, and write amplification are assessed.
- `db_critical_path`: database behavior on user-critical paths is assessed for failover, connection limits, query tail latency, restore readiness, and write behavior.
- `throttle_abort`: batch size, throttle, pause, abort, and confirmation point are defined.
- `verification_check`: data correctness verification queries or invariants exist.
- `rollback_check`: rollback or forward-fix path is written before execution.
- `cleanup_delay`: destructive cleanup is delayed until cutover is verified.

## Red Flags - Stop And Rework

- A migration runs as one unbounded transaction or job.
- Verification is "job completed" without data correctness checks.
- Destructive cleanup happens before old and new paths have been compared.
- Query plans are assumed unchanged after index/schema changes.
- There is no clear pause or abort mechanism.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Treating migrations as developer chores | Treat them as production releases. |
| Backfilling too fast | Throttle by user impact, lag, locks, and saturation. |
| Trusting row counts only | Add invariants, sampling, and reconciliation. |
| Removing old paths immediately | Delay cleanup until rollback is no longer needed. |
