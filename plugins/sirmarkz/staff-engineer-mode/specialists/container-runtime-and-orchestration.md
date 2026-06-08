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

Produces a runtime-posture spec: per-workload resource requests and limits with the OOM and eviction behavior they imply, a scheduling and placement plan, lifecycle hooks, node lifecycle handling, and a hardened image and security context. Technology-agnostic: reason about the scheduler, the workload, and the node as capabilities, not by product name.

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

1. **Set resource bounds.** Choose requests from measured demand and limits from the failure behavior you accept; state what an OOM-kill or eviction does to in-flight work. Distinguish limit failure modes: exceeding a CPU limit throttles (added latency) while exceeding a memory limit terminates the workload (OOM-kill or eviction); set requests and limits accordingly. Keep secrets and sensitive data out of images and out of plain environment variables.
2. **Define the drain contract.** On shutdown, stop accepting new work, finish or hand off in-flight work within a deadline, then exit; tie the deadline to the orchestrator termination grace period.
3. **Tune probes to real readiness.** Readiness gates traffic on dependencies and warm state; liveness restarts only on genuine deadlock, never on slow dependencies; startup probes cover cold-start time without masking crashes.
4. **Order init and sidecars.** Make startup and shutdown ordering explicit so a workload never serves before its sidecar is ready or outlives a sidecar it depends on.
5. **Handle node lifecycle.** Define cordon and drain on rotation, and bound autoscaler churn so scale-in does not sever in-flight work; keep a healthy-capacity floor.
6. **Harden the image and context.** Pin a minimal base, run non-root with a read-only root filesystem where feasible, drop unused capabilities, and set a cold-start and image-size budget.
7. **Verify under disruption.** Define a check that a deploy and a node drain complete with zero dropped requests, and that an OOM or eviction degrades within the stated bound.

## Synthesized Default

Set explicit workload bounds, define drain behavior for disruption paths, gate traffic on real readiness, pin a hardened minimal image, and align termination grace with shutdown behavior. A deploy or node drain that drops requests is a defect.

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

- Batch or offline workloads may accept interruption only when retry, idempotency, and work-loss bounds are explicit.
- Hardening exceptions need a dated owner, compensating control, and expiry.
- Probe behavior should be simulated when live disruption cannot be ethically or safely run.

## Response Quality Bar

- Lead with the runtime posture, dropped-request risk, probe defect, or hardening gap requested.
- Cover resource bounds, drain, probes, lifecycle ordering, node disruption, image posture, and disruption verification before optional platform breadth.
- Make recommendations actionable with request/limit choices, deadlines, probe thresholds, hardening decisions, and test commands or checks where relevant.
- Name the details to inspect, such as workload definitions, metrics, shutdown hooks, probe behavior, node-drain logs, and image metadata; do not state details you have not seen.
- Stay inside workload runtime availability and hardening; route desired-state policy, capacity modeling, and supply-chain provenance away when they are central.

## Required Outputs

- Output shape: render the matching shared template headings or tables in the reply, or use the same shape.
- Per-workload resource bound table: request, limit, OOM and eviction behavior.
- Drain contract: shutdown sequence, deadline, and grace-period alignment.
- Probe spec: readiness, liveness, and startup checks with what each verifies and its thresholds.
- Init and sidecar ordering decision.
- Host lifecycle plan: cordon, drain, autoscaler churn bounds, capacity floor.
- Image and security-context posture: base, run-as, filesystem mode, dropped capabilities, size and cold-start budget.
- Disruption verification: a zero-drop deploy and drain check, and a bounded-degradation check for OOM and eviction.

## Checks Before Moving On

- `resource_bounds`: every workload has a request and a limit, with stated OOM and eviction behavior.
- `limit_failure_modes`: CPU-limit throttling versus memory-limit termination is accounted for, and images/environment carry no embedded secrets.
- `drain_contract`: shutdown stops intake, finishes or hands off in-flight work, and fits the grace period.
- `probe_semantics`: readiness gates on real dependencies; liveness does not restart on slow dependencies.
- `lifecycle_order`: init and sidecar startup and shutdown ordering is explicit.
- `node_lifecycle`: rotation and autoscaler scale-in preserve a capacity floor and do not sever in-flight work.
- `image_hardening`: minimal base, non-root where feasible, dropped capabilities, size and cold-start budget.
- `disruption_verified`: a deploy and a node drain complete with zero dropped requests under load.

## Red Flags - Stop And Rework

- A workload runs with no memory limit or no request.
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
