---
name: experimentation-and-metric-guardrails
description: "Use when designing A/B tests, holdouts, ramps, or readouts needing decision metrics and guardrails"
---

# Experimentation And Metric Guardrails

## Iron Law

```
NO EXPERIMENT CALL WITHOUT A HYPOTHESIS, A KNOWN EXPOSED POPULATION, GUARDRAIL METRICS, AND A PRE-COMMITTED READOUT RULE
```

The experiment must say what it predicts, record who saw the change (not just who was assigned), name the safety/quality metrics that can block a positive primary result, and commit to the decision rule before reading the result. For a small-project or hand-rolled experiment "known exposed population" can be as simple as "logged-in users on build SHA X after timestamp Y"; the invariant is that you can answer who was affected, not that you have an experimentation platform.

## Overview

Experiments are only useful when assignment, exposure, metrics, and decision rules are trustworthy.

**Core principle:** design experiments with clear hypotheses, stable assignment, reliable exposure logging, predeclared metrics, guardrails, and invalidation checks.

## When To Use

- The user is designing, changing, running, or reading out an experiment, A/B test, holdout, or ramp decision and asks about sample-ratio mismatch, exposure logging, guardrail metrics, or metric trust.
- A product, ranking, pricing, UI, recommendation, or workflow change needs a causal readout rather than only rollout health.
- Experiment results conflict, look too good, lack power, or may be invalid because of logging, assignment, contamination, or metric defects.
- A ramp needs outcome guardrails beyond operational canary checks.

## When Not To Use

- The main question is blast radius, rollback, canary, or operational rollout; use `progressive-delivery` instead.
- The main question is service reliability objectives or alerting policy; use `slo-and-error-budgets` instead.
- The main question is LLM evals or model release checks; use `llm-evaluation` or `ml-reliability-and-evaluation` instead.
- The request is product strategy with no engineering measurement artifact.

## Info To Gather

- Current work phase, next decision, what is known, and assumptions where details are missing.
- Hypothesis, decision to make, target population, unit of assignment, treatment, control, and exposure rule.
- Primary metric, guardrail metrics, diagnostic metrics, minimum detectable effect, required sample size and power, runtime, and stopping rule.
- Assignment implementation, eligibility filters, ramp plan, holdout policy, and contamination risks.
- Exposure logging, event definitions, metric pipelines, missingness, delayed effects, and data-quality checks.
- Segment/slice plan, interaction with other experiments, and decision point.

## Workflow

1. **State the decision.** Define the hypothesis and what action the readout will drive.
2. **Choose assignment unit.** Pick a stable unit that matches the effect being measured and avoids cross-contamination.
3. **Define exposure.** Log when the user or entity could be affected, not only when assignment occurred.
4. **Predeclare metrics and power.** Name primary, guardrail, diagnostic, and segment metrics before reading results. Pre-register the minimum detectable effect, the required sample size and power to detect it, and the fixed analysis and readout plan; an underpowered test is a design blocker, not a caveat.
5. **Check validity.** Test assignment balance, sample-ratio mismatch, missing telemetry, logging defects, and eligibility drift. Use an A/A check (or prior A/A evidence) to validate the assignment, logging, and analysis pipeline before trusting an A/B readout.
6. **Plan interactions and comparisons.** Identify overlapping experiments, long-lived holdouts, novelty/primacy effects, network or interference (spillover) effects, and downstream metric coupling. When evaluating many metrics or slices, control the false-positive rate (pre-registered primary metric plus a correction for the rest) so slice mining does not manufacture significance.
7. **Check ramps.** Combine experiment outcomes with operational guardrails; do not let positive primary metrics hide safety regressions.
8. **Record the decision.** Capture result, caveats, decision, rollback trigger, and follow-up measurement.

## Synthesized Default

Use predeclared hypotheses, stable assignment, exposure-based analysis, primary and guardrail metrics, validity checks, segment readouts, and decision records. Treat metric trust failures as experiment blockers, not as minor caveats after the decision.



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

- Very low-risk copy or layout tests may use simpler analysis if assignment, exposure, and guardrails remain clear.
- Sequential ramps can make decisions before full power when safety or user impact requires it, but must state the weaker inference.
- Long-term effects may need holdouts or delayed readouts before irreversible changes.

## Response Quality Bar

- Lead with the experiment design, validity finding, ramp decision, or metric guardrail requested.
- Cover hypothesis, assignment, exposure, metrics, guardrails, validity checks, slices, interactions, and decision rule before optional statistics detail.
- Make recommendations actionable with metric definitions, stop criteria, invalidation triggers, and readout dates where relevant.
- Name the details to inspect, such as assignment logs, exposure events, metric definitions, balance checks, missingness, segment results, and prior experiment interactions; do not state details you have not seen.
- Stay technology-agnostic by default: do not introduce provider, product, framework, database, protocol, or command names unless the user supplied them or explicitly requested tool-specific guidance.
- Stay inside experimentation and metric trust. Use rollout safety, service SLO, or AI eval skills only when those surfaces drive the decision.
- Be concise: prefer experiment design and readout tables over generic testing background.

## Required Outputs

- Output shape: render the matching shared template headings or tables in the reply, or use the same shape.
- Experiment design with hypothesis, population, assignment unit, treatment, control, and exposure rule.
- Metric map: primary, guardrail, diagnostic, and segment metrics.
- Power analysis: minimum detectable effect, required sample size, runtime, and false-positive control across metrics and slices.
- Validity checks for assignment, sample ratio, telemetry, eligibility, contamination, and missingness.
- Ramp, stop, and readout decision rules.
- Interaction and holdout notes.
- Decision record with caveats and follow-up measurement.

## Checks Before Moving On

- `hypothesis_named`: experiment maps to a clear decision and expected effect.
- `assignment_valid`: unit, eligibility, and balance checks are defined.
- `exposure_logged`: exposure event records who could be affected.
- `guardrails_set`: safety and quality metrics can block a positive primary result.
- `validity_checked`: metric trust failures are checked before readout.
- `power_planned`: minimum detectable effect, required sample size, and runtime are computed before launch.
- `readout_discipline`: the analysis is fixed in advance; any early reading uses a sequential or alpha-spending method; multiple metrics or slices have false-positive control.

## Red Flags - Stop And Rework

- Assignment exists but exposure is not logged.
- Metrics are chosen after the result is known.
- Sample-ratio mismatch is ignored.
- A positive primary metric hides reliability, safety, or accessibility harm.
- The ramp continues after validity checks fail.
- A decision is read before the pre-registered sample size or runtime is reached, with no sequential method.
- Many slices or metrics are mined for significance with no multiple-comparison control.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Rollout health as causal answer | Use assignment, exposure, and readout rules. |
| Result-first metrics | Predeclare metrics and guardrails. |
| Ignoring invalidation | Treat balance and telemetry failures as blockers. |
| Average-only readouts | Check important slices and long-term effects. |
| Underpowered tests | Pre-compute minimum detectable effect, sample size, and power before launch. |
| Peeking until significant | Fix the horizon, or use a sequential / alpha-spending method. |
