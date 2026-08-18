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
- Replication topology, acknowledged-write semantics, durable replicated checkpoints, consistency-group boundaries, observed lag and metric freshness, and reconciliation behavior for each stateful store.
- Required RPO per data class and measured recoverable-point evidence from prior failovers or restore checks.
- Control-plane location and whether the data plane can serve without it.
- Existing failover, routing, and DR posture and their tested state.

## Workflow

1. **Decide topology and control-plane boundary.** Choose the region model and state which functions are global control plane versus regional data plane, and the blast radius of losing the control plane.
2. **Map data residency.** For each data class, state which geographies may store and process it and how requests carrying it pin to a compliant region.
3. **Set replication-aware affinity and recovery bounds.** Define read and write region affinity given observed replication state, and pin stateful sessions so a user does not split across regions mid-session. For each data class, distinguish the required RPO, observed lag, lag-metric freshness, latest durable application-consistent replicated checkpoint, acknowledged-write semantics, consistency-group boundary, and the point proven recoverable in a failover or restore check. Treat lag as a directional health signal, not proof of recoverability or data loss. Choose synchronous or asynchronous replication deliberately from latency, availability, and data-loss tradeoffs, then define reconciliation for writes that may be missing or divergent after failover.
4. **Define geo-routing.** State how traffic reaches the right region and what happens when a region is unhealthy.
5. **Write the evacuation runbook.** Define drain, traffic shift, validated cutover, and return-to-normal for losing a region, and who can trigger and abort it.
6. **Bound residency under failover.** Confirm evacuation does not move data into a non-compliant region; define the compliant fallback or the accepted degradation.
7. **Rehearse.** Route the evacuation drill to `resilience-experiments` and record the result and the gaps it found.

## Synthesized Default

Decide topology, residency placement, replication-aware affinity, and a rehearsed evacuation path as one program, then route capacity, consistency, and DR math to their specialists. A rehearsed evacuation runbook with residency bounds is the minimum evidence for an active-active claim.

## Exceptions

- Some systems can accept region-specific degradation when the residency fallback is explicit and user impact is bounded.
- Multi-region control planes are justified only when the added operational complexity is required by the survival target.
- Residency decisions can be constrained by legal requirements, but this specialist owns the engineering placement, routing, and failover controls.

## Response Quality Bar

- Lead with the topology, residency, routing, or evacuation decision requested.
- Cover control-plane boundary, residency map, replication-aware affinity, geo-routing, evacuation, failover residency bounds, and rehearsal before optional regional breadth.
- Make recommendations actionable with placement tables, routing rules, required RPO, durable-checkpoint and metric-freshness evidence, runbook steps, triggers, abort criteria, reconciliation, and rehearsal evidence where relevant.
- Name the details to inspect, such as region list, data classes, replication lag, routing rules, control-plane dependencies, and failover history; do not state details you have not seen.
- Stay technology-agnostic by default: do not introduce provider, product, framework, database, protocol, or command names unless the user supplied them or explicitly requested tool-specific guidance.
- Stay inside the integrated multi-region and residency program; route capacity, consistency, DR restore, and drill execution when those are central.

## Required Outputs

- Output shape: render the matching shared template headings or tables in the reply, or use the same shape.
- Topology and control-plane-versus-data-plane boundary decision with blast radius.
- Data-residency placement map: data class to permitted geographies and request-pinning rule.
- Replication-lag-aware read and write affinity and stateful-session pinning decision.
- Geo-routing decision and unhealthy-region behavior.
- Failover recovery table per cross-region data class: required RPO, acknowledged-write semantics, replication mode, observed lag and freshness, durable application-consistent checkpoint, measured recoverable point, consistency-group boundary, and missing/divergent-write reconciliation.
- Region-evacuation and failover runbook: drain, shift, cutover, return, trigger, abort.
- Residency-under-failover bound: compliant fallback or accepted degradation.
- Evacuation-rehearsal handoff to `resilience-experiments`.

## Checks Before Moving On

- `topology_boundary`: control-plane and data-plane regions and the loss blast radius are explicit.
- `residency_map`: every data class maps to permitted geographies and a request-pinning rule.
- `replication_affinity`: read and write affinity accounts for replication lag; sessions pin to a region.
- `failover_rpo`: every cross-region data class separates required RPO, observed lag, metric freshness, durable application-consistent checkpoint, and measured recoverable point, with acknowledged-write and reconciliation semantics behind the replication choice.
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
- Replication lag is reported as the failover RPO or exact data-loss amount without durable-checkpoint, acknowledged-write, consistency-group, and recoverability evidence.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Call it active-active without rehearsing region loss | Rehearse evacuation and record the gaps. |
| Treat residency as a legal note | Enforce it in placement and request pinning. |
| Ignore replication lag in routing | Pin reads and writes with lag in mind; keep sessions region-stable. |
| Equate lag with recoverability | Measure an application-consistent recoverable point and state metric freshness, write acknowledgement, and reconciliation semantics. |
| Forget the control-plane blast radius | State what fails when the control-plane region is lost. |
