---
name: multi-region-and-data-residency
description: "Use when a system spans regions and needs topology, residency placement, geo-routing, and evacuation runbooks"
---

# Multi-Region And Data Residency

## Iron Law

```
NO MULTI-REGION CLAIM WITHOUT A RESIDENCY MAP, REPLICATION-AWARE ROUTING, AND A REHEARSED EVACUATION RUNBOOK
```

A system called multi-region that has no residency placement map, no replication-lag-aware read and write affinity, and no rehearsed region-evacuation path will lose a region badly and may violate residency constraints while doing it.

## Overview

Produces the integrated cross-region program: the topology and the control-plane-versus-data-plane region boundary, a data-residency placement map, replication-lag-aware read and write region affinity with stateful-session pinning, and region-evacuation and regional-failover runbooks. It owns the integrated artifact and routes the pieces to existing specialists.

**Core principle:** decide where data and traffic may live, how requests pin to a region, and how to evacuate a region before you need to, then rehearse it.

## When To Use

- A system serves from more than one region and needs a topology and control-plane boundary decision.
- Data-residency or sovereignty rules constrain where data classes may be stored or processed.
- Reads and writes must pin to a region with awareness of replication lag, and sessions must stay region-stable.
- A region-evacuation or regional-failover runbook is needed and rehearsed.

## When Not To Use

- The concern is static failover capacity and fault-domain survivability; use `high-availability-design`.
- The concern is DR restore math or corruption and location rebuild; use `backup-and-recovery`.
- The concern is replication and consistency semantics for a single store; use `distributed-data-and-consistency`.
- The concern is internal east-west routing; use `internal-service-networking`.
- Public-edge abuse steering goes to `edge-traffic-and-ddos-defense`; residency-classified personal data handling goes to `privacy-and-data-lifecycle` or `tenant-isolation`; evacuation drills go to `resilience-experiments`.

## Info To Gather

- Current work phase, next decision, what is known, and assumptions where details are missing.
- Regions in scope and the user populations they serve.
- Data classes and the residency or sovereignty rules that bind each one.
- Replication topology and lag between regions for each stateful store.
- Control-plane location and whether the data plane can serve without it.
- Existing failover, routing, and DR posture and their tested state.

## Workflow

1. **Decide topology and control-plane boundary.** Choose the region model and state which functions are global control plane versus regional data plane, and the blast radius of losing the control plane.
2. **Map data residency.** For each data class, state which geographies may store and process it and how requests carrying it pin to a compliant region.
3. **Set replication-aware affinity.** Define read and write region affinity given replication lag, and pin stateful sessions so a user does not split across regions mid-session. State the data-loss bound (RPO) for an unplanned region failover directly from the replication model: asynchronous replication means bounded data loss equal to replication lag at cutover; choose synchronous (latency and availability cost) versus asynchronous (data-loss cost) deliberately per data class.
4. **Define geo-routing.** State how traffic reaches the right region and what happens when a region is unhealthy.
5. **Write the evacuation runbook.** Define drain, traffic shift, validated cutover, and return-to-normal for losing a region, and who can trigger and abort it.
6. **Bound residency under failover.** Confirm evacuation does not move data into a non-compliant region; define the compliant fallback or the accepted degradation.
7. **Rehearse.** Route the evacuation drill to `resilience-experiments` and record the result and the gaps it found.

## Synthesized Default

Decide topology, residency placement, replication-aware affinity, and a rehearsed evacuation path as one program, then route capacity, consistency, and DR math to their specialists. A rehearsed evacuation runbook with residency bounds is the minimum evidence for an active-active claim.

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

- Some systems can accept region-specific degradation when the residency fallback is explicit and user impact is bounded.
- Multi-region control planes are justified only when the added operational complexity is required by the survival target.
- Residency decisions can be constrained by legal requirements, but this specialist owns the engineering placement, routing, and failover controls.

## Response Quality Bar

- Lead with the topology, residency, routing, or evacuation decision requested.
- Cover control-plane boundary, residency map, replication-aware affinity, geo-routing, evacuation, failover residency bounds, and rehearsal before optional regional breadth.
- Make recommendations actionable with placement tables, routing rules, runbook steps, triggers, abort criteria, and rehearsal evidence where relevant.
- Name the details to inspect, such as region list, data classes, replication lag, routing rules, control-plane dependencies, and failover history; do not state details you have not seen.
- Stay technology-agnostic by default: do not introduce provider, product, framework, database, protocol, or command names unless the user supplied them or explicitly requested tool-specific guidance.
- Stay inside the integrated multi-region and residency program; route capacity, consistency, DR restore, and drill execution when those are central.

## Required Outputs

- Output shape: render the matching shared template headings or tables in the reply, or use the same shape.
- Topology and control-plane-versus-data-plane boundary decision with blast radius.
- Data-residency placement map: data class to permitted geographies and request-pinning rule.
- Replication-lag-aware read and write affinity and stateful-session pinning decision.
- Geo-routing decision and unhealthy-region behavior.
- Failover RPO and replication-mode (synchronous vs asynchronous) decision per cross-region data class.
- Region-evacuation and failover runbook: drain, shift, cutover, return, trigger, abort.
- Residency-under-failover bound: compliant fallback or accepted degradation.
- Evacuation-rehearsal handoff to `resilience-experiments`.

## Checks Before Moving On

- `topology_boundary`: control-plane and data-plane regions and the loss blast radius are explicit.
- `residency_map`: every data class maps to permitted geographies and a request-pinning rule.
- `replication_affinity`: read and write affinity accounts for replication lag; sessions pin to a region.
- `failover_rpo`: every cross-region data class states its unplanned-failover data-loss bound and the sync-vs-async replication choice behind it.
- `geo_routing`: routing and unhealthy-region behavior are defined.
- `evacuation_runbook`: drain, shift, cutover, return, trigger, and abort are stated.
- `residency_under_failover`: evacuation cannot move data into a non-compliant region without an accepted decision.
- `rehearsed`: the evacuation path has a drill or a scheduled one.

## Red Flags - Stop And Rework

- A multi-region claim with no rehearsed evacuation runbook.
- Reads and writes split across regions with no replication-lag awareness.
- Residency rules treated as input but never enforced in placement or routing.
- Failover that silently moves regulated data into a non-compliant region.
- The control plane runs in one region and the data plane cannot serve without it.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Call it active-active without rehearsing region loss | Rehearse evacuation and record the gaps. |
| Treat residency as a legal note | Enforce it in placement and request pinning. |
| Ignore replication lag in routing | Pin reads and writes with lag in mind; keep sessions region-stable. |
| Forget the control-plane blast radius | State what fails when the control-plane region is lost. |
