---
name: high-availability-design
description: "Use when a system must survive loss of a location, deployment unit, partition, shard, tenant, or dependency"
---

# High Availability Design And Validation

## Iron Law

```
NO HA DESIGN WITHOUT A FAULT DOMAIN, SURVIVABILITY TARGET, CAPACITY MODEL, AND TEST PLAN
```

"Multi-location", "multi-fault-domain", and "redundant" are labels. They are not enough by themselves.

## Overview

High availability is the ability to keep serving through expected failures without inventing new operations during the failure. Here, location means a fault-isolated placement boundary such as a site, facility, deployment footprint, or independently operated environment. A fault domain can fail independently; a deployment unit is an operational or rollout boundary; a partition is a data, tenant, or workload slice; a stamp is a repeatable isolated service footprint.

**Core principle:** identify fault domains, bound blast radius, provision enough steady-state capacity, and validate the failure mode before relying on it.

## When To Use

- The user asks whether a system can survive location, deployment-unit, process, host, shard, tenant, or dependency loss.
- A design says it is active-active, active-passive, partitioned, shuffle-sharded, or multi-location.
- A launch or PRR needs HA details.
- The work changes topology, failover, load balancing, placement, or blast radius.

## When Not To Use

- The main question is per-call retries, timeouts, backpressure, or circuit breaking; use `dependency-resilience` instead.
- The main question is restoring corrupted or lost data; use `backup-and-recovery` instead.
- The main question is planning a chaos experiment, game day, or fault injection drill; use `resilience-experiments` instead.
- The work is only unit, integration, or CI testing.
- The request is about generic uptime targets; define SLOs first via `slo-and-error-budgets`.

## Info To Gather

- Current work phase, next decision, what is known, and assumptions where details are missing.
- Service tier, SLOs, critical user journeys, and maximum tolerable interruption.
- Current topology: hosts, deployment units, locations, partitions, shards, queues, load balancers, stores, and control planes.
- Fault domains: process, node, rack, location, deployment unit, administrative boundary, cluster, deployment ring, tenant, data partition, dependency, and operator action.
- Capacity by domain, peak traffic, failover headroom, and dependency quotas.
- Fault-domain independence, per-domain telemetry, data replication model, consistency needs, and any hidden global dependencies.
- Per-domain health signals, traffic shift path, and last validation result for moving traffic away from an unhealthy domain.
- Existing failover tests, incidents, game days, chaos experiments, and rollback procedures.

## Workflow

1. **State the survival target.** Use the form: "survive loss of X while continuing Y, with no manual Z, within SLO W."
2. **Draw the fault-domain map.** Include serving path, data path, control plane, deployment system, identity, config, DNS, observability, and operator access.
3. **Check fault-domain independence.** A serving path scoped to one location, partition, or deployment unit should not require synchronous calls to another independent fault domain or shared global state unless the exception, failure behavior, and customer impact are explicit.
4. **Check static stability and constant-work behavior.** Confirm remaining domains already have enough capacity and quotas during the failure; do not count emergency scaling that depends on the failed domain. Prefer designs where the system does the same work in failure as in success — pre-provisioned headroom over reactive scaling, hedged parallel requests over retry-on-timeout, scheduled credential pushes over fetch-on-demand, heartbeat-based health over dedicated failure probes. Failure-only code paths get little real exercise and are the most common source of latent failure-mode bugs.
5. **Choose topology deliberately.** Decide whether a single-location, location-redundant, multi-location, active-passive, active-active, stamp, or partition model is justified by the survival target.
6. **Bound blast radius.** Use partitions, stamps, shards, shuffle sharding, tenant isolation, or location boundaries when one failure could otherwise affect the whole fleet. Operational actions should not affect multiple independent fault domains at once unless the user explicitly accepts the emergency risk.
7. **Remove hidden coupling.** Find global locks, shared queues, shared caches, control-plane calls, cross-location synchronous writes, centrally coupled config, and externally hosted artifacts in the serving, deploy, scale, and startup paths.
8. **Define failover behavior.** Specify automatic/manual trigger, traffic drain or shift, data consistency, split-brain prevention, client behavior, rollback to normal, and when the shift path was last validated.
9. **Validate safely.** Define the validation objective, then route detailed fault-injection or game-day planning to resilience experiments when that is the main work.

## Synthesized Default

Use fault-domain independence, static stability, and explicit fault-domain isolation as the default. Prefer designs that continue in steady state after a domain loss over designs that require emergency scaling, global control-plane calls, or complex operator choreography. Add partitions, stamps, or shuffle sharding when tenant, shard, or workload blast radius is the real risk.



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

- Active-active multi-location is justified only when serving requirements exceed the complexity cost and data semantics can tolerate the replication model.
- Active-passive, warm standby, or pilot light may be better when RTO/RPO and operational maturity are the true constraints.
- Some internal or low-tier services can document a lower survival target if the SLO and user-confirmed risk decision accept it.
- Chaos experiments must be scoped down or simulated when blast radius cannot be ethically bounded.

## Response Quality Bar

- Lead with the availability decision, survivability target, fault-domain gap, or validation plan requested.
- Cover serving paths, fault domains, static capacity, blast radius, hidden dependencies, failover behavior, data semantics, and validation before optional HA breadth.
- Make recommendations actionable with survival targets, capacity calculations, trigger/authority rules, abort criteria, and validation results where relevant.
- Name the details to inspect, such as topology, traffic split, quotas, shared dependencies, failover drills, capacity under loss, replication behavior, and SLO/RTO/RPO targets; do not state details you have not seen.
- Stay technology-agnostic by default: do not introduce provider, product, framework, database, protocol, or command names unless the user supplied them or explicitly requested tool-specific guidance.
- Stay inside HA design and validation. Route backup/restore, chaos execution, or distributed consistency only when they are central to the decision.
- Be concise: avoid generic active-active discussion and prefer compact fault-domain maps and survivability tables.

## Required Outputs

- Fault-domain inventory and serving-path map.
- Survivability statement using "survive loss of X while continuing Y".
- Capacity and quota model under normal, peak, and failed-domain conditions.
- Fault-domain independence and hidden-coupling exception list.
- Blast-radius analysis and partition/shard/tenant isolation recommendation.
- Hidden dependency and control-plane risk list.
- Failover decision record with trigger, authority, data behavior, and rollback.
- Per-fault-domain health and traffic-shift table with signal, action path, expected capacity, and last validation result.
- Validation plan with scope, abort criteria, telemetry, and details to capture.

## Checks Before Moving On

- `fault_domain_map`: expected failure domains and hidden shared dependencies are enumerated.
- `location_independence`: serving, startup, deploy, scale, and recovery paths avoid synchronous cross-location or globally coupled dependencies, or document the exception and fallback.
- `static_capacity`: remaining domains can serve target traffic after the named failure without emergency scaling.
- `blast_radius_bound`: a single fault cannot exceed the documented partition, tenant, shard, or location impact boundary.
- `failover_behavior`: trigger, authority, data consistency, traffic behavior, and rollback are written down.
- `per_domain_signals`: each critical fault domain has health signals that can identify local impairment.
- `shift_path`: moving traffic away from an unhealthy domain has an automatic or manual path and a last validation result.
- `validation_plan`: failover, game day, or chaos test has scope, abort criteria, telemetry, and check path.

## Red Flags - Stop And Rework

- "We run in two deployment units" is treated as enough to show fault-domain resilience.
- Failover depends on humans discovering the issue and manually changing many systems under pressure.
- Remaining capacity after failure is assumed but not calculated.
- Critical serving calls depend synchronously on a global control plane, config service, or cross-location dependency.
- A deploy, scale-up, startup, or recovery path depends on artifacts or control planes unavailable during the named fault.
- One operational action can damage multiple locations, deployment units, partitions, or shards at once.
- Chaos testing is proposed without blast-radius limits or abort criteria.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Confusing HA with DR | HA keeps serving through expected faults; DR restores after loss or corruption. |
| Counting autoscaling as static capacity | Model capacity already available when the domain fails. |
| Testing only the happy failover path | Test detection, partial failure, rollback, and return-to-normal. |
| Ignoring operator dependencies | Include identity, access, dashboards, deploy, and config systems in the map. |
