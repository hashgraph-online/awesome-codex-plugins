---
name: ab-test-results-readout
description: Analyze and communicate A/B test results with metric readouts, subgroup analysis, data-quality checks, ad hoc investigation, visualization, and launch recommendations. Use when interpreting experiment results, preparing an A/B test report, explaining flat or mixed results, checking guardrails, segmenting test/control data, or turning experiment data into a product decision.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: A/B Test Results Readout
  category: Product Management
  tags: practical-ab-testing,ab-testing,experimentation,analytics,data-visualization
---

# A/B Test Results Readout

Use this skill to turn experiment data into a clear decision. It emphasizes
metric interpretation, data-quality checks, subgroup analysis, ad hoc analysis,
visualization, and launch recommendations.

## Source Traceability

Primary source: Practical A/B Testing by Leemay Nassery. Guidance is
transformed and paraphrased from chapter 4 lines 2950-3742 and chapter 1 lines
572-718. Metric tradeoff context comes from chapter 2 lines 1296-1472.

## Related Advanced Skills

- `trustworthy-experiment-insights`: use when the readout needs false positive,
  false negative, power, replication, meta-analysis, or suspicious-lift review.
- `experiment-verification-monitoring`: use when result interpretation depends
  on whether assignment, exposure, metrics, canaries, or active monitoring were
  healthy.
- `long-term-impact-evaluation`: use when short-term readout is not enough to
  decide durable product or business impact.

## Reference Routing

| Need | Read |
|------|------|
| Readout concepts | `references/core/knowledge.md` |
| Analysis and reporting rules | `references/core/rules.md` |
| Example readouts | `references/core/examples.md` |
| Step-by-step report workflow | `workflows/prepare-results-readout.md` |

## Workflow

1. Reconstruct the test design: hypothesis, variants, population, and metrics.
2. Verify data quality and whether exposure/eligibility match the brief.
3. Compare primary and guardrail metrics against baseline and decision rules.
4. Run subgroup analysis when averages obscure meaningful differences.
5. Investigate outliers, missing data, or surprising movement.
6. Visualize results so stakeholders can compare control, test, and segments.
7. Recommend ship, stop, iterate, or investigate with caveats.

## Output Format

```markdown
# A/B Test Results Readout

## Executive Decision
[Ship | Stop | Iterate | Investigate] because [reason].

## Test Summary
- Hypothesis:
- Population:
- Control:
- Test:
- Run window:

## Metric Results
| Metric | Role | Control | Test | Change | Interpretation |
|--------|------|---------|------|--------|----------------|

## Segment Findings
| Segment | What changed | Decision impact |
|---------|--------------|-----------------|

## Data Quality Notes
- Eligibility/exposure:
- Missing data:
- Outliers:
- Instrumentation concerns:

## Recommendation
- Decision:
- Rollout conditions:
- Follow-up analysis:
```

## Quality Bar

- Do not hide guardrail regressions behind a primary-metric win.
- Do not overstate subgroup findings; label them exploratory when not
  pre-planned.
- Do not show only averages when the product decision depends on user groups.
- Use charts to clarify comparisons, not to decorate the readout.
