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
3. **Predeclare the decision estimand and populations.** Log assignment and when a unit could be affected. Always estimate assignment-wide policy impact. A triggered population may be the primary high-sensitivity estimand only when the trigger is pre-treatment or counterfactually measurable the same way for treatment and control, without selecting only on treatment-caused exposure. Predeclare its role, inspect the untriggered complement, and translate or dilute the effect to the ship population so the shipping decision is not made from the affected subset alone.
4. **Predeclare metrics and power.** Name primary, guardrail, diagnostic, and segment metrics before reading results. Pre-register the minimum detectable effect, the required sample size and power to detect it, and the fixed analysis and readout plan; an underpowered test is a design blocker, not a caveat.
5. **Check validity.** Test assignment balance, sample-ratio mismatch, missing telemetry, logging defects, and eligibility or trigger drift. Use an A/A check or prior A/A evidence to validate the assignment, logging, and analysis pipeline before trusting an A/B readout.
6. **Plan interactions and comparisons.** Identify overlapping experiments, long-lived holdouts, novelty or primacy effects, interference or spillover, and downstream metric coupling. When evaluating many metrics or slices, control the false-positive rate so slice mining does not manufacture significance.
7. **Check ramps.** Combine experiment outcomes with operational guardrails; do not let positive primary metrics hide safety regressions.
8. **Record the decision.** Capture the predeclared primary estimand, assignment-wide policy impact, any triggered estimate, complement and population translation, caveats, decision, rollback trigger, and follow-up measurement.

## Synthesized Default

Use predeclared hypotheses, stable assignment, a decision-matched estimand, assignment-wide policy impact, carefully defined triggered estimates where counterfactual triggering is valid, primary and guardrail metrics, validity checks, segment readouts, and decision records. Treat metric trust failures as experiment blockers, not as caveats after the decision.



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
- Scale the artifact to the request: a narrow design or readout needs the decision, assignment, predeclared estimand, assignment-wide policy impact, metrics, validity, and rule; add power, interaction, triggered-population, holdout, and ramp modules only when applicable.

## Required Outputs

- Output shape: render the matching shared template headings or tables in the reply, or use the same shape.
- Experiment design with hypothesis, ship population, assignment unit, treatment, control, exposure rule, predeclared decision estimand, and assignment-wide policy-impact population.
- Metric map: primary, guardrail, diagnostic, and segment metrics.
- Power analysis: minimum detectable effect, required sample size, runtime, and false-positive control across metrics and slices.
- Validity checks for assignment, sample ratio, telemetry, eligibility, contamination, and missingness.
- Triggered-analysis plan, when used, with counterfactual trigger validity, untriggered-complement check, and translation to the ship population.
- Ramp, stop, and readout decision rules.
- Interaction and holdout notes.
- Decision record with caveats and follow-up measurement.

## Checks Before Moving On

- `hypothesis_named`: experiment maps to a clear decision and expected effect.
- `assignment_valid`: unit, eligibility, and balance checks are defined.
- `exposure_logged`: exposure event records who could be affected.
- `estimand_valid`: the primary estimand matches the decision; assignment-wide policy impact is retained; a triggered primary is used only with a valid counterfactual trigger, complement check, and ship-population translation.
- `guardrails_set`: safety and quality metrics can block a positive primary result.
- `validity_checked`: metric trust failures are checked before readout.
- `power_planned`: minimum detectable effect, required sample size, and runtime are computed before launch.
- `readout_discipline`: the analysis is fixed in advance; any early reading uses a sequential or alpha-spending method; multiple metrics or slices have false-positive control.

## Red Flags - Stop And Rework

- Assignment exists but exposure is not logged.
- A triggered analysis selects only post-treatment exposed units, has no counterfactual trigger or complement check, or is used to ship without assignment-wide population impact.
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
