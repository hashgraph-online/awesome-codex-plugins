---
name: trustworthy-experiment-insights
description: Assess whether experiment results are credible enough to influence product decisions. Use when checking false positive or false negative risk, underpowered metrics, suspiciously large lifts, replication needs, meta-analysis, stratified sampling, covariate adjustment, or whether A/B test insights should be trusted.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Trustworthy Experiment Insights
  category: Product Management
  tags: practical-ab-testing,next-level-ab-testing,ab-testing,experimentation,analytics
---

# Trustworthy Experiment Insights

Use this skill to decide whether an experiment result is believable enough to
shape a product or engineering decision. It focuses on false positives, false
negatives, power, replication, meta-analysis, stratified sampling, covariate
adjustment, and suspicious result review.

## Source Traceability

Primary source: *Next-Level A/B Testing* by Leemay Nassery. Guidance is
transformed and paraphrased from Chapter 6 on false positives and negatives,
meta-analysis, metric sensitivity, stratified random sampling, covariate
adjustments, replication, longer runs, and statistical power.

Related skills:

- `ab-test-results-readout` for standard experiment reporting.
- `experiment-sensitivity-optimization` for improving precision before or
  during experiment design.
- `experiment-verification-monitoring` for operational validity checks.

## Reference Routing

| Need | Read |
|------|------|
| Insight-quality concepts | `references/core/knowledge.md` |
| Credibility and follow-up rules | `references/core/rules.md` |
| Result-review scenarios | `references/core/examples.md` |
| Step-by-step credibility review | `workflows/review-experiment-credibility.md` |

## Workflow

1. Confirm the experiment was operationally valid enough to interpret.
2. Check power, practical significance, and whether metrics were underpowered.
3. Look for false positive risk: suspicious lift, many comparisons, early stop,
   weak prior, or contradiction with prior experiments.
4. Look for false negative risk: noisy metrics, small sample, low sensitivity,
   or over-broad metric choice.
5. Compare with similar experiments or run meta-analysis when available.
6. Recommend launch, replicate, extend, investigate, or reject the result.

## Output Format

```markdown
# Experiment Insight Credibility Review

## Result Under Review
[Experiment, metric, observed result, and proposed decision.]

## Credibility Assessment
[Trust | Trust with caveats | Replicate | Extend | Investigate | Do not trust]

## Evidence
| Check | Finding | Risk |
|-------|---------|------|

## Follow-Up
- Replication needed:
- Longer run needed:
- Meta-analysis/comparison:
- Variance reduction opportunity:

## Decision Guidance
[What decision can be made now, and what should wait.]
```

## Quality Bar

- Do not celebrate a result before checking whether it could be a false positive.
- Do not dismiss a flat result before checking power and sensitivity.
- Do not compare against prior experiments without noting differences in
  population, metric, design, and timing.
- Do not use statistical checks to hide operational failures; verify experiment
  health first.
