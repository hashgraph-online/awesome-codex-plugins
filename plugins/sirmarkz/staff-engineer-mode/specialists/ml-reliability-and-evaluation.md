---
name: ml-reliability-and-evaluation
description: "Use when ML model-serving changes or promotions need evals, data validation, drift, skew, rollback, or checks"
---

# ML Systems Reliability And Evaluation

## Iron Law

```
NO MODEL PROMOTION WITHOUT DATA CHECKS, EVAL CHECKS, SERVING MONITORING, AND ROLLBACK
```

Offline accuracy alone is not production readiness. Promote an identifiable artifact, watch serving behavior, check drift and training-serving skew, and keep rollback ready.

## Overview

Production ML reliability is software reliability plus data reliability plus model behavior reliability.

**Core principle:** promote models only when data, features, evals, serving behavior, rollout, monitoring, and rollback are all controlled.

## When To Use

- The user asks about production ML readiness, model serving, training pipelines, eval checks, feature validation, training-serving skew, drift, model rollout, or model rollback.
- A model artifact, feature pipeline, training job, or inference path is changing.
- The user needs to monitor model quality, prediction distribution, data drift, or serving latency.
- A launch or PRR includes ML behavior.

## When Not To Use

- The work is generic warehouse/ETL reliability with no model production concern; use `data-pipeline-reliability` instead.
- The request is broad AI policy or model strategy; out of scope unless framed as production engineering.
- The system is an LLM or agent app with prompt/tool security risk; use `llm-application-security` instead.
- The work is offline experimentation only and will not affect production.

## Info To Gather

- Current work phase, next decision, what is known, and assumptions where details are missing.
- Model use case, user impact, failure consequence, and production criticality.
- Training data, feature definitions, schemas, labels, transform code, and serving data sources.
- Offline eval metrics, acceptance thresholds, slices/cohorts, fairness/safety checks where relevant, and regression history.
- Training-serving consistency checks, feature freshness, null/default behavior, and schema drift.
- Model artifact version, artifact size or storage needs, data version, config, dependencies, and rollout unit.
- Model routing, routing-control-plane health and selection signals, access-control config, artifact deletion or restoration behavior, serving substrate readiness, and serving dependency compatibility.
- Model availability semantics, false-unavailable behavior, and whether critical models roll out in later waves after low-risk exposure.
- Serving SLOs, latency, saturation, fallback behavior, monitoring, and rollback path.
- Drift, quality, feedback, incident, and human-review signals.

## Workflow

1. **Establish a non-ML baseline.** Confirm the system needs ML and has a deterministic fallback or baseline where appropriate.
2. **Validate data and features.** Check schema, ranges, missingness, distributions, freshness, and transform consistency.
3. **Check training-serving skew.** Compare feature generation, preprocessing, defaults, and dependency versions across training and serving.
4. **Define eval checks.** Use offline metrics, slice metrics, regression tests, adversarial/security checks, safety/business constraints, and minimum deltas for promotion.
5. **Version everything.** Link model artifact, code, features, data snapshot, config, eval result, and serving environment.
6. **Validate serving control state.** Check model routing, access-control config, dependency version compatibility, artifact size, storage or provisioning prerequisites, artifact deletion or restoration behavior, serving substrate readiness, and fallback selection before promotion. Verify routing control planes use correctness health for model availability and do not prefer a faster but stale or wrong control plane.
7. **Roll out in stages.** Use shadow, canary, cohort, percentage, or holdback when the rollout can bound risk; monitor serving and model behavior.
8. **Monitor production with thresholds.** Track serving SLOs, prediction distribution, feature drift, data freshness, quality proxies, feedback loops, and capacity or quota saturation; name alert thresholds or rollback triggers for at least two of those signals.
9. **Prepare rollback.** Keep prior artifact/config available and define when to rollback, disable, or route to baseline.

## Synthesized Default

Check ML releases on data validation, eval results, threat-informed failure-mode checks, training-serving consistency, versioned artifacts, progressive rollout, serving SLOs, thresholded drift and serving monitoring, and rollback. Treat model-only evaluation as insufficient for production readiness.



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

- Non-production exploration may use lighter checks if isolated and marked as not for decisions.
- Some models lack immediate ground truth; use proxy metrics, delayed labels, human review, or guardrail metrics.
- High-risk decisions may require human-in-the-loop, additional safety checks, or stricter slice checks.
- Batch scoring may use pipeline freshness and output validation instead of synchronous serving latency.

## Response Quality Bar

- Lead with the launch decision, eval check, or model-risk blocker.
- Cover offline/online evals, guardrails, drift/skew, rollback, and monitoring before optional ML-platform breadth.
- Make recommendations actionable with checks, stop conditions, and rollback or shadow-mode criteria where relevant.
- Name the details to inspect, such as offline metrics, online guardrails, cohort slices, drift signals, and rollback checks; do not state details you have not seen.
- For production monitoring, give thresholded alerts or stop conditions for at least two signals, such as prediction drift, training-versus-serving feature distribution drift, serving latency, data freshness, saturation, or quota exhaustion.
- Stay technology-agnostic by default: do not introduce provider, product, framework, database, protocol, or command names unless the user supplied them or explicitly requested tool-specific guidance.
- Stay inside model-serving reliability and evaluation unless the prompt asks for broader product or research strategy.
- Be concise: avoid generic ML background and prefer compact eval and rollout matrices.

## Required Outputs

- Output shape: render the matching shared template headings or tables in the reply, or use the same shape.
- ML production readiness checklist.
- Data and feature validation plan.
- Training-serving skew review.
- Offline and production eval check plan.
- AI/ML failure-mode and adversarial/security evaluation plan where misuse or dependency manipulation can affect users.
- Versioning and artifact lineage record.
- Serving control-state check for routing, routing-control-plane correctness, access controls, dependency compatibility, artifact size and provisioning prerequisites, artifact deletion or restoration, serving substrate readiness, and fallback selection.
- Model rollout and rollback plan.
- Drift, quality, freshness, serving latency, and capacity/quota monitoring requirements with alert thresholds and response paths.
- Incident path and residual risk notes.

## Checks Before Moving On

- `data_validation`: training and serving data have schema, freshness, distribution, and missingness checks.
- `eval_check`: promotion thresholds, regression checks, and slice criteria are stated.
- `skew_check`: training-serving feature and transform differences are checked.
- `version_lineage`: model, code, data, features, config, and eval result are linked.
- `serving_control_state`: model routing, access-control config, dependency compatibility, artifact size and provisioning prerequisites, artifact deletion or restoration, serving substrate readiness, and fallback selection are verified.
- `routing_control_plane`: model unavailable/deleted states are cross-checked, control-plane selection uses correctness health, and critical models roll out in later waves.
- `monitoring_thresholds`: prediction drift, feature distribution drift, latency, freshness, saturation, or quota signals have alert thresholds and response paths.
- `rollback_check`: prior model or safe fallback is available with trigger criteria.

## Red Flags - Stop And Rework

- Offline aggregate accuracy is the only launch check.
- Feature generation differs between training and serving with no skew check.
- Model artifact cannot be tied to data, code, config, and eval result.
- Serving config can route to a model artifact with missing access, deleted state, incompatible dependencies, or unverified provisioning requirements.
- Routing prefers a low-latency control plane that reports incorrect model availability.
- Rollback requires retraining under incident pressure.
- Drift is monitored without a decision rule, threshold, or response path.
- Serving latency, capacity, or quota risk is discussed without alert thresholds.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Treating ML as only a model file | Include data, features, serving, evals, rollout, and monitoring. |
| Ignoring slices | Evaluate important cohorts and failure-sensitive segments. |
| Waiting for labels only | Use proxy and delayed-quality signals where ground truth lags. |
| No fallback | Keep prior model, rule baseline, or disable path where impact warrants it. |
| Vague monitoring | Add alert thresholds for drift, feature distribution, latency, and capacity or quota signals. |
