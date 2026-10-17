---
name: container-runtime-and-orchestration
description: "Use when workload scheduling, resource limits, probes, drain, or image hardening affect runtime availability"
---

# Container Runtime And Orchestration

## Iron Law

```
NO WORKLOAD GOES TO PRODUCTION WITHOUT RESOURCE BOUNDS, A DRAIN CONTRACT, PROBE SEMANTICS, AND A HARDENED IMAGE
```

A workload with no resource bounds, no graceful-shutdown path, mistuned probes, or a permissive image will fail under scheduling pressure, deploys, or node loss, even when the code is correct.

## Overview

Produces a runtime-posture spec: per-workload resource requests and explicit limit decisions, memory-limit termination and node-pressure eviction behavior, a scheduling and placement plan, lifecycle hooks, node lifecycle handling, and a hardened image and security context. Technology-agnostic: reason about the scheduler, workload, and node as capabilities, not by product name.

**Core principle:** size the workload to its real demand, drain it cleanly on every disruption, and let probes reflect real readiness, so deploys and node churn cost no requests.

## When To Use

- A new or changed workload needs resource requests and limits, and the OOM or eviction behavior of getting them wrong is in question.
- Deploys, node rotation, or autoscaling drop in-flight requests because there is no drain contract.
- Liveness, readiness, or startup probes cause restart loops, premature traffic, or masked failure.
- Init or sidecar ordering, image size, or container security context affects startup or blast radius.

## When Not To Use

- The concern is desired-state representation, drift, or admission policy for these settings; use `infrastructure-and-policy-as-code`.
- The concern is demand modeling, tail latency, or headroom sizing in the abstract; use `performance-and-capacity`.
- The concern is probe design as remote-call failure-mode safety; use `dependency-resilience`.
- The concern is version waves or skew across a fleet upgrade; use `fleet-upgrades`.
- The concern is image provenance, signing, or builder isolation; use `software-supply-chain-security`. Compute-host fault-domain survival goes to `high-availability-design`.

## Info To Gather

- Current work phase, next decision, what is known, and assumptions where details are missing.
- Per-workload memory and CPU demand under normal and peak load, and the limit-versus-request gap.
- Disruption sources: deploy cadence, node rotation, autoscaler add and remove events, preemption, or reclaim.
- Probe definitions and what each one checks: process up, dependencies ready, or real work served.
- Init and sidecar dependencies and their ordering requirements.
- Image base, size, run-as user, filesystem mode, and granted capabilities.

## Workflow

1. **Set resource bounds.** Choose scheduling requests from measured normal and peak demand. Make an explicit per-resource limit decision from the failure behavior you accept: CPU limits can add throttling latency and may be omitted when admission and capacity controls bound use; memory limits provide containment but crossing one terminates the workload. Treat node-pressure eviction as a separate scheduler or host failure, not as memory-limit termination. State how termination and eviction affect in-flight work. Keep secrets and sensitive data out of images and plain environment variables.
2. **Define the drain contract.** On shutdown, stop accepting new work, finish or hand off in-flight work within a deadline, then exit; tie the deadline to the orchestrator termination grace period.
3. **Tune probes to real readiness.** Readiness should test the workload's local ability to accept and serve work, including required local initialization. Include a remote dependency only when the workload cannot provide any useful response without it and the probe design preserves a fleet-capacity floor or documented degraded mode during a shared dependency outage. Liveness restarts only on local deadlock or irrecoverable process failure, never on a slow dependency; startup probes cover cold-start time without masking crashes.
4. **Order init and sidecars.** Make startup and shutdown ordering explicit so a workload never serves before its sidecar is ready or outlives a sidecar it depends on.
5. **Handle node lifecycle.** Define cordon and drain on rotation, and bound autoscaler churn so scale-in does not sever in-flight work; keep a healthy-capacity floor.
6. **Harden the image and context.** Pin a minimal base, run non-root with a read-only root filesystem where feasible, drop unused capabilities, and set a cold-start and image-size budget.
7. **Verify under disruption.** Define a check that a deploy and a node drain complete with zero dropped requests, and that an OOM or eviction degrades within the stated bound.

## Synthesized Default

Set explicit workload bounds, define drain behavior for disruption paths, gate traffic on real readiness, pin a hardened minimal image, and align termination grace with shutdown behavior. A deploy or node drain that drops requests is a defect.

## Exceptions

- Batch or offline workloads may accept interruption only when retry, idempotency, and work-loss bounds are explicit.
- Hardening exceptions need a dated owner, compensating control, and expiry.
- Probe behavior should be simulated when live disruption cannot be ethically or safely run.

## Response Quality Bar

- Lead with the runtime posture, dropped-request risk, probe defect, or hardening gap requested.
- Cover resource bounds, drain, probes, lifecycle ordering, node disruption, image posture, and disruption verification before optional platform breadth.
- Make recommendations actionable with request/limit choices, deadlines, probe thresholds, hardening decisions, and test commands or checks where relevant.
- Name the details to inspect, such as workload definitions, metrics, shutdown hooks, probe behavior, node-drain logs, and image metadata; do not state details you have not seen.
- Stay inside workload runtime availability and hardening; route desired-state policy, capacity modeling, and supply-chain provenance away when they are central.
- Scale the artifact to the request: a narrow resource, drain, probe, or image question needs the decision and its failure test; add the full runtime-posture plan only when the workload or release spans those surfaces.

## Required Outputs

- Output shape: render the matching shared template headings or tables in the reply, or use the same shape.
- Per-workload resource table: measured demand, scheduling request, explicit per-resource limit decision, CPU-throttling behavior, memory-limit termination, and node-pressure eviction behavior.
- Drain contract: shutdown sequence, deadline, and grace-period alignment.
- Probe spec: readiness, liveness, and startup checks with what each verifies and its thresholds.
- Init and sidecar ordering decision.
- Host lifecycle plan: cordon, drain, autoscaler churn bounds, capacity floor.
- Image and security-context posture: base, run-as, filesystem mode, dropped capabilities, size and cold-start budget.
- Disruption verification: a zero-drop deploy and drain check, and a bounded-degradation check for OOM and eviction.

## Checks Before Moving On

- `resource_bounds`: every workload has measured demand, scheduling requests, and explicit limit decisions with stated containment and latency tradeoffs.
- `limit_failure_modes`: CPU-limit throttling, memory-limit termination, and node-pressure eviction are distinguished, and images or environment definitions carry no embedded secrets.
- `drain_contract`: shutdown stops intake, finishes or hands off in-flight work, and fits the grace period.
- `probe_semantics`: readiness reflects local ability to serve; any dependency check preserves a fleet-capacity floor or degraded mode; liveness does not restart on slow dependencies.
- `lifecycle_order`: init and sidecar startup and shutdown ordering is explicit.
- `node_lifecycle`: rotation and autoscaler scale-in preserve a capacity floor and do not sever in-flight work.
- `image_hardening`: minimal base, non-root where feasible, dropped capabilities, size and cold-start budget.
- `disruption_verified`: a deploy and a node drain complete with zero dropped requests under load.

## Red Flags - Stop And Rework

- A workload has no measured demand, scheduling request, or explicit memory-containment decision.
- Readiness depends on a shared remote dependency and can remove the whole fleet during that dependency's outage.
- Deploys or node drains drop in-flight requests and that is treated as normal.
- Liveness probes restart workloads on slow dependencies, amplifying load.
- A container runs as root with a writable root filesystem and full capabilities.
- Sidecar and main-container ordering is undefined.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Treat orchestrator defaults as a posture | Set bounds, grace period, and probe thresholds deliberately. |
| Liveness and readiness check the same thing | Readiness gates traffic; liveness restarts only on deadlock. |
| Ship the build image to production | Pin a minimal hardened runtime image with dropped capabilities. |
| Assume scale-in is free | Drain in-flight work and hold a capacity floor on scale-in. |
