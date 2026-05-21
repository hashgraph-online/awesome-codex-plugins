---
name: data-pipeline-reliability
description: "Use when designing or operating batch/streaming pipelines needing freshness SLIs, validation, lineage, or replay"
---

# Data Pipeline Reliability

## Iron Law

```
NO CRITICAL DATASET WITHOUT FRESHNESS SLI, VALIDATION, LINEAGE, AND REPLAY PATH
```

If consumers cannot tell whether data is fresh and correct, the pipeline is not reliable.

## Overview

Critical data pipelines are production systems whose users notice stale, missing, duplicated, or incorrect data.

**Core principle:** define freshness, completeness, correctness, lineage, replay, and recovery as explicit service guarantees.

## When To Use

- The user is designing, building, changing, or operating a batch or streaming pipeline and asks about freshness, correctness, completeness, lineage, missed runs, backfills, data-quality checks, or warehouse/ETL SLAs.
- Dashboards, reports, downstream services, or decisions depend on timely and correct data.
- A pipeline needs replay, reprocessing, backfill, or recovery behavior.
- The user asks how to alert on stalled or stale datasets.

## When Not To Use

- The main issue is model training/serving skew, model evaluation, or model rollback; use `ml-reliability-and-evaluation` instead.
- The request is service-to-service event workflow design; use `event-workflows` instead.
- The work is application database backfill execution; use `database-operations` instead.
- The question is primary data consistency semantics; use `distributed-data-and-consistency` instead.

## Info To Gather

- Current work phase, next decision, what is known, and assumptions where details are missing.
- Pipeline graph, datasets, consumers, schedules, triggers, and dependencies.
- Freshness, completeness, correctness, latency, backlog age, and processing-error expectations.
- Source data contracts, schemas, watermarks, checkpoints, transform versions, and publish criteria.
- Validation checks, data-quality rules, anomaly detection, and known false-positive tolerance.
- Replay/backfill capability, idempotency, side effects, retention, and correction process.
- Lineage, change history, downstream impact, and incident history.

## Workflow

1. **Identify critical datasets.** Name consumers, business use, local responsibility path, and consequence of stale or wrong data.
2. **Define data SLIs.** Use freshness, completeness, correctness, latency, backlog age, and processing errors where relevant.
3. **Map lineage.** Record source, transform version, schedule/watermark, publish step, and downstream consumers.
4. **Check publication.** Validate schema, required fields, ranges, referential integrity, duplicates, and business invariants before publish.
5. **Make replay safe.** Ensure reprocessing is idempotent or explicitly handles duplicates and side effects.
6. **Alert on symptoms.** Trigger urgent alerts or tickets on freshness, backlog, stalled watermarks, and quality failures, not only job failure.
7. **Create recovery runbooks.** Include backfill, replay, quarantine, correction, republish, and consumer notification.
8. **Separate ML concerns.** Route model-specific eval, drift, and training/serving skew to ML systems reliability.

## Synthesized Default

Treat critical pipelines like services: SLI/SLO, validation checks, lineage, idempotent replay, symptom alerts, and recovery runbooks. A successful job is not enough if published data is stale, incomplete, or wrong.



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

- Exploratory datasets may use lighter checks if clearly labeled non-production.
- Some best-effort analytics can use follow-up tickets rather than urgent alerts if consumers accept delay.
- Streaming pipelines may use watermark/backlog SLIs instead of schedule-based freshness.
- Irreversible side effects during replay require quarantine and manual confirmation.

## Response Quality Bar

- Lead with the pipeline reliability target, blocker list, or replay plan requested.
- Cover freshness, completeness, correctness, lineage, replay, and quality checks before optional data-platform breadth.
- Make recommendations actionable with checks, stop conditions, and recovery actions where relevant.
- Name the details to inspect, such as row counts, watermarks, late-event rates, reconciliation checks, and backfill proofs; do not state details you have not seen.
- Stay technology-agnostic by default: do not introduce provider, product, framework, database, protocol, or command names unless the user supplied them or explicitly requested tool-specific guidance.
- Stay inside pipeline reliability unless the prompt explicitly asks for warehouse architecture or ownership controls.
- Be concise: avoid generic data-quality background and prefer compact SLI/check/replay tables.

## Required Outputs

- Pipeline SLI/SLO table.
- Dataset responsibility and lineage map.
- Validation and publish-check plan.
- Replay/backfill/reprocessing runbook.
- Freshness, backlog, error, and quality alert policy.
- Consumer impact and notification plan.
- Recovery test results or test plan.

## Checks Before Moving On

- `freshness_sli`: every critical dataset has freshness or watermark target and measurement source.
- `publish_check`: publish path has data-quality checks and failure behavior.
- `lineage_responsibility`: source, transform, and consumers are recorded.
- `replay_safety`: replay/backfill is idempotent or duplicate/side-effect risk is controlled.
- `recovery_runbook`: stalled, bad, or late data has recovery steps and consumer communication path.

## Red Flags - Stop And Rework

- Alerting only checks whether the job process exited.
- Published data has no validation before consumers read it.
- Backfill can duplicate downstream side effects.
- A dataset used by production decisions has no freshness target, lineage, or replay path.
- Lineage is reconstructed manually during every incident.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Treating data pipelines as cron jobs | Treat them as services with SLIs, validation, and recovery paths. |
| Monitoring runtime only | Monitor freshness, completeness, correctness, and backlog. |
| Backfilling blindly | Make replay idempotent and validate output. |
| Publishing bad data fast | Check publish and quarantine failures. |
