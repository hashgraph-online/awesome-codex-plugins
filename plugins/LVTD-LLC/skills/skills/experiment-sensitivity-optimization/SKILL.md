---
name: experiment-sensitivity-optimization
description: Improve experiment sensitivity and reduce traffic or duration requirements. Use when choosing sensitive metrics, working with minimum detectable effect, reducing variants, applying capping metrics, CUPED, variance reduction, or deciding how to get trustworthy A/B test signal with fewer users.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Experiment Sensitivity Optimization
  category: Product Management
  tags: practical-ab-testing,next-level-ab-testing,ab-testing,experimentation,metrics
---

# Experiment Sensitivity Optimization

Use this skill to redesign an experiment so it can detect meaningful effects
with fewer users, less time, or clearer metrics. It focuses on minimum
detectable effect, metric sensitivity, capping, variant reduction, CUPED, and
variance reduction.

## Source Traceability

Primary source: *Next-Level A/B Testing* by Leemay Nassery. Guidance is
transformed and paraphrased from Chapter 3 on experiment design, sensitive
metrics, minimum detectable effect, capping, reducing variants, and CUPED; and
Chapter 6 on stratified random sampling and covariate adjustments.

Related skills:

- `ab-test-design-brief` for baseline experiment specs.
- `trustworthy-experiment-insights` for judging whether a result is believable.
- `experimentation-throughput-strategy` for capacity and test scheduling.

## Reference Routing

| Need | Read |
|------|------|
| Sensitivity concepts | `references/core/knowledge.md` |
| Metric, variance, and sample-size rules | `references/core/rules.md` |
| Optimization scenarios | `references/core/examples.md` |
| Step-by-step sensitivity review | `workflows/optimize-experiment-sensitivity.md` |

## Workflow

1. State the decision and the smallest practically meaningful effect.
2. Check whether the current primary metric is close enough to the feature's
   mechanism.
3. Reduce unnecessary variants and separate learning tests from launch tests.
4. Consider metric capping, CUPED, stratification, or other variance reduction.
5. Record data prerequisites, risks, and interpretation limits.
6. Update the experiment brief with the revised measurement plan.

## Output Format

```markdown
# Experiment Sensitivity Plan

## Decision
[What the experiment must decide.]

## Current Constraint
[Traffic | Duration | Noisy metric | Too many variants | Weak proxy | Other]

## Recommended Changes
| Change | Why It Helps | Requirement | Risk |
|--------|--------------|-------------|------|

## Metric Plan
- Primary metric:
- More sensitive alternative:
- Guardrails:
- Minimum detectable effect:

## Variance Reduction
- Technique:
- Data needed:
- Validation:

## Interpretation Notes
- What this design can conclude:
- What it cannot conclude:
```

## Quality Bar

- Do not optimize sensitivity by switching to a metric that no longer answers
  the product decision.
- Do not add CUPED, stratification, or capping unless the data requirements and
  interpretation risks are named.
- Do not keep extra variants when they are not needed for the decision.
- Do not treat a smaller detectable effect as useful unless it is practically
  meaningful.
