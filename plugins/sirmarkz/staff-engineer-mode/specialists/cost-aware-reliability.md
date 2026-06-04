---
name: cost-aware-reliability
description: "Use when cost spikes, unit economics, or spend cuts must preserve reliability and SLO headroom"
---

# FinOps And Cost Aware Reliability

## Iron Law

```
NO COST CUT WITHOUT SLO, HEADROOM, BLAST-RADIUS, AND REGRESSION CHECK
```

If a saving silently consumes reliability margin, it is a risk decision, not an optimization.

## Overview

Cost is an operational signal, but reliability headroom is not waste by default.

**Core principle:** optimize unit economics while preserving explicit reliability, capacity, recovery, and safety targets.

## When To Use

- The user asks about cost/reliability tradeoffs, unit economics, capacity headroom, tagging/allocation, cost regressions, reserved/committed/interruptible capacity mix, or budget-aware reliability.
- A service needs to reduce cost while maintaining an SLO or launch target.
- A cost spike may indicate traffic, inefficiency, abuse, deployment regression, or capacity misconfiguration.
- The user asks how much reliability headroom is justified.

## When Not To Use

- The user asks pure billing support, procurement, contracts, or vendor negotiation; out of scope.
- The main topic is performance/capacity with no cost tradeoff; use `performance-and-capacity` instead.
- The issue is public abuse causing cost; use `edge-traffic-and-ddos-defense` instead too.
- The request is financial reporting not tied to engineering decisions.

## Info To Gather

- Current work phase, next decision, what is known, and assumptions where details are missing.
- External commitment, customer-criticality, SLOs, traffic, capacity model, failover headroom, and degradation behavior.
- Unit metrics: request, tenant, job, dataset, device, model inference, or business transaction.
- Cost allocation: environment, tenant/customer, feature, location, and workload class.
- Scaling policies, reserved/committed/interruptible mix, idle resources, and peak patterns.
- Optimization opportunities with expected savings, engineering effort, reliability risk, owner, status, and actual impact after implementation.
- Data transfer, cross-location replication, telemetry/log volume, managed service overhead, and external traffic costs.
- Recent deploys, traffic changes, incidents, abuse signals, and cost regressions.
- Metered usage, pricing or discount rules, eligibility boundaries, and reconciliation evidence for customer-visible charges.
- Reliability risk tolerance and confirmation path for reducing headroom.

## Workflow

1. **State the reliability constraint.** Identify SLO, capacity headroom, failover target, and recovery requirement before cutting cost.
2. **Define unit cost.** Choose a meaningful engineering unit and map cost to service, feature, tenant, or workload.
3. **Find cost drivers.** Separate traffic growth, inefficient code, overprovisioning, idle capacity, data transfer, cross-location replication, telemetry/log volume, storage growth, retries, and abuse.
4. **Reconcile charge semantics.** For customer-visible billing or allocation, compare metered units to pricing, discount, credit, and eligibility rules before and after cost-system changes.
5. **Protect headroom.** Distinguish waste from required peak, failover, and surge capacity.
6. **Choose optimizations.** Use right-sizing, scheduling, storage lifecycle, caching, batching, data-transfer reduction, telemetry sampling/retention controls, capacity mix, or code efficiency where risk is explicit.
7. **Model commitment risk.** For committed capacity or discounts, state forecast confidence, lock-in window, unused commitment risk, exit path, and what reliability headroom is protected.
8. **Model tradeoffs.** State expected savings, reliability impact, security/operations side effects, blast radius, rollback, and monitoring.
9. **Track opportunities through outcome.** Record expected value, effort, owner, risk, decision, implementation status, and actual savings or reliability impact so optimization work does not become unreviewed cost cutting.
10. **Add guardrails.** Alert on cost regressions, unit-cost anomalies, and reliability signals after changes.
11. **Check continuously.** Treat cost anomalies like operational regressions with post-change verification.

## Synthesized Default

Optimize unit cost with allocation, anomaly detection, right-sizing, and capacity-mix decisions, while preserving SLOs, required headroom, and recovery posture. Reliability-risk tradeoffs must be explicit and user-accepted; cheapest is not automatically cost-optimized.



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

- Non-critical batch or preemptible workloads may use cheaper interruptible capacity if retries, deadlines, and data correctness are safe.
- Emergency cost controls can temporarily degrade non-critical features if user impact and rollback are explicit.
- Regulated, safety-critical, or externally committed systems may keep high headroom even when utilization looks inefficient.
- Public abuse cost spikes should use `edge-traffic-and-ddos-defense` instead.
- Small estates may not justify heavy allocation pipelines; use coarse unit tracking until savings exceed instrumentation cost.

## Response Quality Bar

- Lead with the unit-cost model, cost driver, reliability tradeoff, optimization plan, or anomaly diagnosis requested.
- Cover allocation, unit metrics, driver separation, SLO/headroom preservation, failure-condition capacity, rollback, anomaly monitoring, and refresh cadence before optional FinOps breadth.
- Make recommendations actionable with metrics, savings ranges, risk acceptance using the shared risk-acceptance lifecycle, stop criteria, rollback steps, and post-change checks where relevant.
- Name the details to inspect, such as spend by usage units, traffic, capacity headroom, SLOs, peak/failure demand, deploy markers, anomaly timeline, and retry/abuse signals; do not state details you have not seen.
- Stay technology-agnostic by default: do not introduce provider, product, framework, database, protocol, or command names unless the user supplied them or explicitly requested tool-specific guidance.
- Stay inside cost-aware reliability. Route capacity, edge defense, platform, or data work only when those are the central unresolved risk.
- Be concise: avoid generic cost advice and prefer compact unit-cost, driver, and tradeoff tables.

## Required Outputs

- Output shape: render the matching shared template headings or tables in the reply, or use the same shape.
- Unit-cost model and allocation plan.
- Cost driver analysis.
- Metering and pricing reconciliation plan for customer-visible charges or allocation.
- Data-transfer, telemetry, and cross-location cost assessment where applicable.
- Reliability/headroom tradeoff record.
- Optimization plan with savings estimate, risk, and rollback.
- Optimization opportunity register with owner, expected value, effort, risk, status, and actual-versus-estimated impact.
- Commitment-risk record for reserved, prepaid, interruptible, or long-window capacity decisions.
- Cost anomaly and unit-regression dashboard requirements.
- Refresh cadence for cost signals.
- Follow-up routes to capacity, edge defense, platform, or data skills as needed.

## Checks Before Moving On

- `unit_check`: cost metric maps to an engineering unit and response path.
- `slo_headroom`: SLO, peak, and failure-condition headroom are preserved or risk is accepted.
- `driver_check`: cost drivers are separated before recommending cuts.
- `charge_reconciliation`: metered units, pricing rules, discounts, credits, and eligibility boundaries are reconciled for customer-visible charges or allocation.
- `opportunity_tracking`: optimization recommendations have owner, status, and actual-versus-estimated impact review.
- `rollback_check`: optimization has rollback or mitigation plan.
- `regression_check`: post-change cost and reliability signals are monitored.

## Red Flags - Stop And Rework

- Cost reduction removes failover capacity without changing SLO or accepting risk.
- Only total monthly spend is tracked; no unit metric or response path exists.
- Idle capacity is labeled waste without peak/failure analysis.
- Interruptible capacity is used for work that cannot safely retry.
- Cost anomaly investigation ignores deploys, retries, abuse, and data growth.
- Optimization recommendations are made once and never checked against actual savings, effort, or reliability impact.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Cutting before modeling risk | State SLO, headroom, and failure scenarios first. |
| Optimizing total spend only | Use unit economics tied to engineering responsibility. |
| Treating cost as finance-only | Add operational alerts and regression reviews. |
| Hiding tradeoffs | Record reliability risk and confirmation. |
