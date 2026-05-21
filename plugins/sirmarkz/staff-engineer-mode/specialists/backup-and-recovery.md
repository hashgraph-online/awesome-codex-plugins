---
name: backup-and-recovery
description: "Use when setting RTO/RPO, backup design, restore tests, or recovery from corruption, deletion, or site loss"
---

# Backup Restore And Disaster Recovery

## Iron Law

```
NO RECOVERY PLAN WITHOUT A TESTED RESTORE AND MEASURED RTO/RPO
```

A successful backup job is not a restore test. Replication is not a backup. Multi-location serving does not show that data can be recovered.

## Overview

Backups do not matter until a restore works.

**Core principle:** define recoverability by RTO/RPO and check it with restore tests under realistic failure scenarios, including destructive operators and corrupted data.

## When To Use

- The user asks about backups, restores, disaster recovery, RTO, RPO, PITR, immutable backups, location recovery, ransomware recovery, or destructive data changes.
- A stateful launch or PRR needs recovery results.
- The system must recover from corrupted rows, accidental deletion, bad migrations, lost keys, location-wide loss, or compromised operators.
- The user asks which DR strategy to use: backup/restore, pilot light, warm standby, or active-active.

## When Not To Use

- The main goal is serving through fault-domain loss without restoring data; use `high-availability-design` instead.
- The request is normal unit/integration testing.
- The issue is online schema/backfill execution before disaster occurs; use `database-operations` instead.
- A live outage needs command, communications, and mitigation; route to `incident-response-and-postmortems` alongside this skill.

## Info To Gather

- Current work phase, next decision, what is known, and assumptions where details are missing.
- Essential and critical data sets, customer journeys, data classification, and deletion/corruption blast radius.
- RTO/RPO expectations by journey, tenant, data class, and regulatory/customer commitment.
- Backup method, cadence, retention, location, encryption, key responsibility, immutability, and access policy.
- Replication topology, lag, consistency model, PITR capability, and location dependencies.
- Restore procedure, last restore test results, restore environment, validation queries, and rehearsal history.
- Destructive scenarios: operator error, ransomware, compromised credentials, bad deploy, bad migration, and key loss.

## Workflow

1. **Classify what must be recovered.** Separate essential user-critical data sets from broader serving availability, durability, correctness, and audit/history requirements.
2. **Set RTO/RPO.** Record maximum tolerable downtime and data loss for each critical journey and data set.
3. **Map backup coverage.** Include data, metadata, schema, config, secrets/keys, object stores, queues, indexes, and derived state.
4. **Check isolation.** Ensure backups and keys survive accidental deletion, malicious operator action, account compromise, and ransomware.
5. **Design restore paths.** Include full restore, partial restore, point-in-time recovery, location rebuild, and corruption repair.
6. **Run a restore check.** Restore into a controlled environment, run correctness checks, measure elapsed time and data loss, and record gaps.
7. **Choose DR posture.** Use backup/restore, pilot light, warm standby, active-passive, or active-active based on RTO/RPO, complexity, cost, data residency, and operations maturity.
8. **Feed findings back.** Create blockers for PRR, platform fixes, runbook updates, and future drills.

## Synthesized Default

Use recent restore tests tied to RTO/RPO as the default. Protect backups and encryption keys in a separate trust and blast-radius boundary. Prefer the simplest DR strategy that meets RTO/RPO and residency constraints; do not choose active-active unless the serving requirement and operational maturity justify the operational cost.



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

- Stateless services may document dependency recovery rather than service-local backups.
- Derived indexes or caches may be rebuilt instead of backed up if rebuild time fits RTO and source data is protected.
- Active-active may be required for very low RTO, but it still needs corruption recovery and backup isolation.
- Emergency data repair during an incident may proceed before full DR analysis, but restore checks and postmortem actions must follow.

## Response Quality Bar

- Lead with the restore readiness decision, DR strategy, RTO/RPO gap, or blocker list requested.
- Cover backup coverage, retention, encryption/key recovery, isolation, restore runbooks, corruption/PITR/partial restore, validation, and remediation before optional DR breadth.
- Make recommendations actionable with commands, prerequisites, checks, stop criteria, measured targets, and remediation deadlines where relevant.
- Name the details to inspect, such as backup job metadata, restore logs, validation queries, key recovery checks, retention settings, immutable storage controls, and measured RTO/RPO; do not state details you have not seen.
- Stay technology-agnostic by default: do not introduce provider, product, framework, database, protocol, or command names unless the user supplied them or explicitly requested tool-specific guidance.
- Stay inside backup, restore, and DR. Route HA serving design or incident repair only when those are the central unresolved risk.
- Be concise: avoid generic DR taxonomy and prefer compact coverage matrices and restore result tables.

## Required Outputs

- DR strategy decision record.
- RTO/RPO table by journey and data set.
- Essential-data coverage table showing source of truth, restore type, validation, and measured result.
- Backup coverage, retention, encryption, key, and immutability matrix.
- Restore runbook with prerequisites, commands, validation, and rollback.
- PITR, partial restore, corruption repair, and location recovery plan.
- Restore test result log with measured RTO/RPO and gaps.
- Remediation backlog for missing coverage or failed restore criteria.

## Checks Before Moving On

- `restore_test`: a recent restore test exists, or its absence is called out as a blocker.
- `essential_data_list`: data needed for user-critical recovery is identified separately from lower-criticality copies.
- `rto_rpo_fit`: measured restore time and data loss meet the stated targets, or exceptions have a user-accepted deadline and verification path.
- `measured_restore`: restore behavior is measured against the stated objective rather than described from intent.
- `coverage_matrix`: critical data, metadata, schema, config, and keys have backup or rebuild coverage.
- `isolation_check`: backups and keys are protected from destructive operator, compromised credential, and ransomware scenarios.
- `validation_queries`: restored data has correctness checks, not just process completion.

## Red Flags - Stop And Rework

- The only support is "backup job succeeded".
- Replication is treated as protection against accidental deletion or corruption.
- Backups and production data are deletable by the same credentials.
- Encryption keys needed for restore are not backed up, recoverable, or separately protected.
- RTO/RPO is copied from a platform default without measuring restore time.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Equating HA with DR | HA keeps serving; DR restores lost or corrupted state. |
| Testing full restore only | Include partial restore, PITR, corruption repair, and location rebuild where relevant. |
| Ignoring derived state | Decide whether indexes, caches, search, and analytics are backed up or rebuilt inside RTO. |
| Treating drills as ritual | Capture measured time, data loss, validation results, and remediation patches. |
