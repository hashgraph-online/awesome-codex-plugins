---
name: service-decommission-and-sunset
description: "Use when a service is being retired and needs ordered teardown, data disposition, and no-resurrection evidence"
---

# Service Decommission And Sunset

## Iron Law

```
NO TEARDOWN WITHOUT ZERO-TRAFFIC PROOF, RETENTION-AND-HOLD-HONORED DATA DISPOSITION, AND A NO-RESURRECTION RECORD
```

A retirement that deletes before proving zero traffic, disposes of data without honoring retention and legal hold, or leaves DNS, certs, and credentials dangling will strand users, breach compliance, or hand an attacker a hijackable name.

## Overview

Produces the terminal-phase teardown program, the counterpart to a launch-readiness review: confirmation of zero live traffic and no remaining consumers, final-data disposition, credential and key and cert revocation, DNS and endpoint and cert reclamation with hijack prevention, ordered infrastructure and pipeline teardown with cost-stop verification, monitoring and on-call removal, and an auditable record that the system is gone and cannot silently resurrect. It owns the ordering, irreversibility gating, and evidence; it routes the front-half drive-off and the destructive primitives out.

**Core principle:** drive consumers off, dispose of data lawfully, reclaim every name and credential, and prove it cannot come back.

## When To Use

- A service or system is being retired and needs an ordered, evidence-backed teardown.
- Final-data disposition must honor retention minimums and active legal holds.
- DNS, endpoints, certs, and credentials must be reclaimed so they cannot be hijacked or silently revived.
- A decommission-readiness record is needed, the terminal-phase counterpart to a go/no-go.

## When Not To Use

- The concern is driving consumers off a system being replaced; use `migration-and-deprecation`.
- The concern is per-mutation execution safety for a single destructive change; use `configuration-and-automation-safety`.
- The concern is infrastructure deletion mechanics in desired state; use `infrastructure-and-policy-as-code`.
- The concern is key or cert revocation lifecycle; use `cryptography-and-key-lifecycle` or `identity-and-secrets`.
- Datastore destructive-change mechanics go to `database-operations`; restore-path concerns go to `backup-and-recovery`.

## Info To Gather

- Current work phase, next decision, what is known, and assumptions where details are missing.
- Remaining traffic and consumers, and how their absence is proven.
- Data the system holds, its retention minimums, and any active legal hold.
- DNS names, endpoints, certs, and credentials the system owns.
- Infrastructure, pipelines, alarms, and on-call rotations tied to the system.
- The ongoing cost the teardown is meant to stop.
- Resurrection vectors: IaC/desired-state definitions, autoscaling or schedulers, and CI/CD pipelines that could recreate the service after teardown.

## Workflow

1. **Prove zero traffic.** Confirm no live traffic and no remaining consumers, with evidence and a watch window, before any destructive step. Require the zero-traffic watch window to span the longest known invocation cycle (batch, cron, quarterly or annual reconciliation, break-glass), not just a short observation window.
2. **Dispose of data lawfully.** Decide archival versus verified destruction per data class, honor retention minimums, and suspend destruction for any class under active legal hold.
3. **Revoke credentials and keys.** Revoke the system's credentials, keys, and certs so they cannot be reused.
4. **Reclaim names and endpoints.** Release or repoint DNS, endpoints, and certs so a later actor cannot claim a dangling name; stage with TTL awareness.
5. **Tear down in order.** Sequence infrastructure and pipeline teardown so dependents go first, and verify the cost the teardown targeted actually stops. Discover and neutralize resurrection vectors (IaC/desired-state, schedulers, CI/CD) so they cannot recreate the service, route the bulk destructive deletes through `configuration-and-automation-safety` guardrails (preview, blast-radius caps, rate limits, fail-closed), and state the data-sanitization level (clear/purge/cryptographic-erase/destroy) with verification.
6. **Remove monitoring and on-call.** Retire alarms, dashboards, and on-call rotations so the system leaves no phantom alerts.
7. **Record no-resurrection.** Produce an auditable record that the system is gone, names and credentials are reclaimed, data was disposed per policy, and nothing can silently revive it.

## Synthesized Default

Prove zero traffic, dispose of data per retention and hold, revoke and reclaim credentials and names, then tear down in dependency order with a no-resurrection record. Use staged, evidence-backed teardown. Dangling names and orphaned credentials are security defects.

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

- Emergency shutdown may disable exposure before all teardown evidence exists, but destructive steps still wait for zero-traffic and data-disposition proof.
- Retention and hold decisions can be externally constrained, but this specialist owns the engineering evidence and ordering.
- Names may remain reserved after shutdown when that is the hijack-prevention control.

## Response Quality Bar

- Lead with the teardown blocker, zero-traffic proof, data-disposition decision, or no-resurrection record requested.
- Cover consumers, data disposition, credentials, names, ordered teardown, monitoring removal, and no-resurrection evidence before optional retirement breadth.
- Make recommendations actionable with evidence windows, revocation lists, DNS and endpoint actions, teardown order, and irreversibility gates.
- Name the details to inspect, such as traffic evidence, consumer inventory, data classes, holds, credentials, names, certs, pipelines, and alarms; do not state details you have not seen.
- Stay technology-agnostic by default: do not introduce provider, product, framework, database, protocol, or command names unless the user supplied them or explicitly requested tool-specific guidance.
- Stay inside terminal service teardown; route consumer migration, mutation safety, desired-state deletion, key lifecycle, and restore concerns when central.

## Required Outputs

- Output shape: render the matching shared template headings or tables in the reply, or use the same shape.
- Zero-traffic and no-consumer proof with a watch window.
- Data-disposition plan per class: archive or destroy, retention honored, legal hold suspends destruction.
- Credential, key, and cert revocation list.
- DNS, endpoint, and cert reclamation plan with hijack prevention.
- Ordered infrastructure and pipeline teardown with cost-stop verification.
- Monitoring and on-call removal list.
- No-resurrection record: auditable evidence the system is gone and cannot revive.

## Checks Before Moving On

- `zero_traffic`: no live traffic and no remaining consumers, with evidence, before destruction.
- `watch_window`: the zero-traffic proof spans the longest known business/invocation cycle.
- `data_disposition`: each data class is archived or destroyed per retention, with legal hold suspending destruction.
- `credential_revocation`: credentials, keys, and certs are revoked.
- `name_reclamation`: DNS, endpoints, and certs cannot be hijacked or silently revived.
- `ordered_teardown`: teardown follows dependency order and the targeted cost stops.
- `monitoring_removed`: alarms and on-call rotations are retired.
- `no_resurrection`: IaC, schedulers, and pipelines are confirmed unable to recreate the service.
- `sanitization_level`: retired data and media state a sanitization level and verification.

## Red Flags - Stop And Rework

- Deletion begins before zero traffic is proven.
- Data under active legal hold is scheduled for destruction.
- DNS names or certs are left dangling and hijackable.
- Credentials and keys outlive the system.
- No record proves the system cannot silently resurrect.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Delete once traffic looks low | Prove zero traffic with a watch window first. |
| Destroy all data on retirement | Honor retention minimums and suspend for legal hold. |
| Leave DNS and certs in place | Reclaim names so they cannot be hijacked. |
| Forget the credentials | Revoke every key, cert, and credential the system held. |
