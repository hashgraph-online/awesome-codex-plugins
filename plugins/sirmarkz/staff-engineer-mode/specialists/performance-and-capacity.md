---
name: performance-and-capacity
description: "Use when tail latency, load tests, saturation, capacity, headroom, or peak/failover traffic need analysis"
---

# Capacity Performance And Tail Latency

## Iron Law

```
NO CAPACITY OR PERFORMANCE PLAN WITHOUT A TRAFFIC MODEL, TAIL METRIC, SATURATION SIGNAL, AND LOAD-TEST RESULTS
```

If the answer only says "scale horizontally" or reports averages, it is not enough.

## Overview

Users experience tail latency, not averages.

**Core principle:** model demand, concurrency, queueing, saturation, and fanout, then test to the knee of the curve before production finds it.

## When To Use

- The user asks about p95, p99, p99.9, throughput, QPS, concurrency, queueing, saturation, hot paths, or scaling limits.
- The work is raw concurrent-connection, memory, file-descriptor, or autoscaling headroom without changing connection lifecycle semantics.
- A release caused latency or throughput regression.
- A launch, PRR, or migration needs capacity test results.
- The system needs load, stress, spike, soak, or failure-condition testing.
- Cost is discussed as a capacity/headroom tradeoff rather than a billing support question.

## When Not To Use

- The main problem is retries, timeouts, or dependency failure safety; use `dependency-resilience` instead.
- The main request is public edge abuse, denial-of-service defense, or application-layer filtering; use `edge-traffic-and-ddos-defense` instead.
- The user asks pure billing/procurement questions; out of scope.
- The work is SLO target selection without performance investigation; use `slo-and-error-budgets` instead.
- The regression is explicitly tied to a query plan, index, or schema migration; use `database-operations` instead.
- The request is browser field/lab release checks for a frontend rollout; use `web-release-gates` instead.

## Info To Gather

- Current work phase, next decision, what is known, and assumptions where details are missing.
- User journeys, SLOs, latency percentiles, throughput targets, and acceptable degradation behavior.
- Traffic model: current, peak, forecast, burstiness, tenant skew, payload size, fanout, batch ramp-up rate, and internal or privileged entry points that can bypass public quotas.
- Resource signals: CPU, memory, IO, network, lock contention, connection pools, thread pools, queue depth, queue age, GC, and background or maintenance work that shares serving capacity.
- Load-balancing behavior, locality, shard keys, hot partitions, cache hit rate, and downstream quotas.
- Existing load tests, production incidents, profiling/flame graphs, and regression data.
- Tested breakpoint, startup-to-ready time, recovery time after stress, and profile differences between normal and heavy load.
- Headroom rule, autoscaling, load-balancing, or protection-control behavior under saturation, feedback-amplification risks, static failed-domain capacity, and unit-cost constraints.
- Control-loop input contracts for autoscaling, load-balancing, and protection controls: metric source, unit, labels, filters, missing-data behavior, validation path, and compatibility across changes.
- Capacity-change plan: scale-up batch size, rebalance work, scheduler or allocator processing cost, and rollback path if adding capacity slows the serving path.

## Workflow

1. **Frame the answer before inspection.** Start with a compact provisional check frame: target percentile and boundary; load-test method with scenarios and pass/stop criteria; headroom plus USE signal; overload mechanism and priority; queue-depth or in-flight work metric plus backpressure; hot-path/key hypothesis plus mitigation. Mark unknowns and refine them after investigation.
2. **Define the user-visible target.** Choose p95/p99/p99.9 and throughput targets that map to SLOs or launch requirements.
3. **Build the demand model.** Capture request rate, burstiness, concurrency, fanout, payload, tenant skew, batch or maintenance ramp-up curve, and seasonal peaks.
4. **Apply queueing sanity checks.** Use Little's Law to connect arrival rate, latency, and concurrency; identify queues that can hide saturation.
5. **Find saturation points.** Track RED for services and USE for resources. Include locks, connection pools, thread pools, caches, downstream quotas, automated scaling or protection-control actions, and every internal or external entry point's true serving capacity. Do not let privileged, batch, or maintenance paths ramp faster than the bottleneck dependency can absorb.
6. **Test to the knee.** Run load/stress/spike/soak tests in production-like environments until latency or errors become nonlinear; include representative peak traffic, tenant skew, and background jobs that share serving resources. Record the breakpoint, startup-to-ready time, recovery behavior after stress, and the profile differences that explain bottlenecks.
7. **Protect the system.** Define admission control, load shedding, prioritization, and graceful degradation before saturation.
8. **Budget background work.** Set resource ceilings, scheduling limits, and preemption behavior for maintenance, config-processing, compaction, indexing, and other background paths that can starve foreground requests.
9. **Validate control loops.** Test autoscaling, load-balancing, and protection controls when their input signals are slow, missing, erroring, renamed, relabeled, or rejected by policy validation; confirm the action does not add work to the same saturated path or scale a failing dependency into a feedback loop.
10. **Investigate regressions scientifically.** Compare before/after profiles, deploy markers, dependency metrics, cache behavior, and resource saturation.
11. **Model failed-domain headroom.** For HA requirements, show remaining domains have enough already-available capacity at peak; do not count emergency scaling as the primary recovery mechanism.
12. **Treat capacity changes as load.** When adding, moving, or reserving capacity, model rebalance work, scheduler or allocator processing, and rollout batch size so the expansion itself cannot create a latency incident.
13. **Tie capacity to cost when relevant.** Preserve required headroom and failover capacity; optimize unit economics only after risk is explicit.

## Synthesized Default

Optimize around tail percentiles, saturation, queue age, and headroom rather than averages. Combine tail-at-scale design, SRE golden signals, performance baselines, load-shedding practice, and unit-cost discipline when cost is explicitly part of the reliability tradeoff. Name the static-stability and constant-work patterns as the default for headroom: pre-provision capacity that is already available when a domain fails rather than relying on reactive scaling, and add proactive demand forecasting with provisioning lead-time instead of relying on reactive saturation response.



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

- Batch pipelines may use freshness and completion latency instead of request p99; route to data pipeline reliability when the system is mainly ETL.
- Internal low-impact tools may use lower headroom or follow-up-only alerts when the user accepts the SLO tradeoff.
- Hedged requests can reduce tail latency only when extra load is budgeted and duplicate work is safe.
- Predictive scaling helps predictable demand, but cold-start latency must not sit on a critical synchronous path.

## Response Quality Bar

- Lead with the capacity model, tail-latency diagnosis, load-test plan, or headroom decision requested.
- Cover traffic shape, fanout, tail budgets, saturation signals, load shedding, test results, failure-domain headroom, and cost tradeoffs when relevant before optional performance breadth.
- Make recommendations actionable with thresholds, test scenarios, stop criteria, scaling limits, rollback actions, and regression checks where relevant.
- Name the details to inspect, such as p95/p99 metrics, peak/burst traffic, concurrency, queue age, resource saturation, downstream limits, load-test results, and unit cost; do not state details you have not seen.
- Stay technology-agnostic by default: do not introduce provider, product, framework, database, protocol, or command names unless the user supplied them or explicitly requested tool-specific guidance.
- Stay inside capacity, performance, and tail latency. Route data pipelines, dependency resilience, or FinOps only when they materially change the decision.
- Be concise: avoid generic performance advice and prefer compact capacity models, latency budgets, and test matrices.

## Required Outputs

- Output shape: render the matching shared template headings or tables in the reply, or use the same shape.
Every answer, including narrow regression diagnoses, must state, in this order:

1. **Target at user boundary**: numeric latency/throughput target, percentile (p95/p99/p99.9), and the measurement boundary (edge, gateway, service ingress). Mark unknown explicitly.
2. **Load-test methodology**: name the method (synthetic load, traffic shadow, prod replay), the scenarios (normal/peak/burst/soak), and pass/stop criteria.
3. **Headroom and saturation (USE)**: required headroom percentage and the saturation indicator(s) tracked (utilization, queue depth, queue age, pool wait, drain rate).
4. **Overload behavior**: load-shedding or admission-control mechanism AND which traffic class is preserved by priority.
5. **Queue/backpressure model** for any asynchronous path: queue-depth metric and the backpressure response.
6. **Hot-path / hot-key analysis**: the suspected hot path or hot key and its mitigation.
7. Background-work resource budget where maintenance, config-processing, compaction, indexing, or control work shares foreground serving capacity.
8. Capacity model (normal/peak/burst/failure-domain), capacity-change and rebalance plan, control-loop input contract and behavior under saturation with feedback-amplification guard, latency budget by hop, regression analysis, tested breakpoint, recovery-after-stress result, and cost/headroom tradeoff when cost is in scope.

## Checks Before Moving On

- `tail_metric`: target percentile, window, and journey are stated.
- `traffic_model`: peak, burst, concurrency, fanout, and tenant skew are modeled or marked unknown.
- `saturation_signals`: resource, queue, pool, and downstream saturation metrics are identified.
- `entry_point_limits`: internal, batch, admin, and public entry points enforce steady-state and ramp-rate limits no higher than measured downstream capacity.
- `test_result`: load or regression test has scenario, stop criteria, result, and check path.
- `breakpoint_known`: the nonlinear failure point, or the reason it was not tested, is recorded.
- `background_budget`: shared-capacity background work has resource ceilings, breach actions, and representative peak-load test coverage.
- `headroom_check`: capacity includes peak, resource or dependency limits, and expected failure-domain conditions, with static capacity separated from emergency scaling.
- `capacity_change_load`: capacity additions, reservations, or moves account for rebalance work, scheduler or allocator cost, batch size, and rollback.
- `control_loop_behavior`: autoscaling, load-balancing, and protection controls have input metric contracts, expected actions under saturation, compatibility checks for label/filter changes, cannot amplify the failing path, and cannot reduce serving capacity below the user contract without an explicit overload decision.
- `recovery_after_stress`: recovery time and behavior after stress are measured or explicitly unknown.

## Red Flags - Stop And Rework

- Average latency is used as the primary user-experience metric.
- The plan scales replicas but ignores database, cache, queue, or downstream limits.
- Load tests stop at expected peak and never find the nonlinear point.
- Queue depth is monitored without queue age or drain rate.
- Autoscaling or protection logic uses unhealthy dependency signals in a way that adds work to the saturated path.
- A capacity expansion assumes new headroom is free before measuring rebalance, scheduler, or allocator work.
- Cost cutting removes failover headroom without changing the SLO or accepting risk.
- A single fault-domain or partition recovery plan depends on scaling after the failure rather than preexisting headroom.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Treating CPU as capacity | Include all saturation points: queues, locks, pools, IO, network, and dependencies. |
| Letting internal callers bypass quota | Apply capacity limits at every entry point and size them to the real bottleneck. |
| Reactive scaling as the only plan | Pre-provision static-stability headroom and forecast demand with lead-time. |
| Testing only steady load | Add bursts, soak, failover, cold cache, and dependency-slow scenarios. |
| Letting background work share unlimited serving capacity | Give maintenance and control work explicit resource budgets and preemption behavior. |
| Hiding overload in queues | Track age and drain rate; shed work before recovery becomes impossible. |
| Optimizing p50 | Optimize the percentile users and SLOs experience. |
