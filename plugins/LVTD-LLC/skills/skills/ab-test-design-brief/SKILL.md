---
name: ab-test-design-brief
description: Build product A/B test briefs with hypotheses, success metrics, guardrails, baselines, proxy metrics, eligibility, variants, randomization, confidence, and launch criteria. Use when planning an A/B test from a product idea, writing an experiment spec, defining test/control variants, choosing metrics, or checking whether an experiment is ready to run.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: A/B Test Design Brief
  category: Product Management
  tags: practical-ab-testing,ab-testing,experimentation,product-analytics,metrics
---

# A/B Test Design Brief

Use this skill to turn a product change into a decision-ready A/B test brief.
It focuses on experiment anatomy: hypothesis, metrics, baselines, variants,
eligibility, randomization, confidence, and launch criteria.

## Source Traceability

Primary source: Practical A/B Testing by Leemay Nassery. Guidance is
transformed and paraphrased from chapter 2, especially "Creating a Clear
Hypothesis" through "Summarizing the For You A/B Test" in the working text
analysis at lines 1203-1942. Related motivation and variant examples come from
chapter 1 lines 394-718.

## Related Advanced Skills

- `experiment-sensitivity-optimization`: use when the brief is blocked by MDE,
  sample size, noisy metrics, CUPED, capping, or too many variants.
- `experiment-verification-monitoring`: use when the brief needs prelaunch QA,
  canaries, exposure validation, or active experiment health checks.
- `long-term-impact-evaluation`: use when the brief needs delayed or sustained
  impact measurement beyond the initial test window.

## Reference Routing

| Need | Read |
|------|------|
| Concepts and terminology | `references/core/knowledge.md` |
| Design rules and readiness checks | `references/core/rules.md` |
| Brief examples and anti-examples | `references/core/examples.md` |
| Step-by-step brief creation | `workflows/create-ab-test-brief.md` |

## Workflow

1. State the product decision the test must inform.
2. Write a hypothesis with observation, predicted change, audience, and metrics.
3. Choose one primary success metric plus guardrail metrics.
4. Establish the baseline or explain why a proxy metric is being used.
5. Define eligibility, exposure, test variant, and control variant.
6. Choose the randomization unit that preserves a coherent user experience.
7. Record confidence requirements, sample-size assumptions, and launch criteria.

## Output Format

```markdown
# A/B Test Brief

## Decision
[What decision this test will support.]

## Hypothesis
Because [observation], we believe [change] will cause [outcome] for [audience].
We will know this is true when [primary metric] changes without harming [guardrails].

## Metrics
| Metric | Role | Baseline | Target or Concern | Data Source |
|--------|------|----------|-------------------|-------------|

## Variants and Eligibility
- Population:
- Eligibility criteria:
- Exposure event:
- Control:
- Test:
- Randomization unit:

## Confidence Plan
- Minimum detectable effect:
- Sample size or duration:
- Risks to validity:

## Launch Criteria
- Ship if:
- Do not ship if:
- Investigate if:
```

## Quality Bar

- Do not accept a vague "see what happens" experiment.
- Do not let proxy metrics hide missing instrumentation; name the compromise.
- Do not generalize beyond the population that was eligible and exposed.
- Keep variants interpretable: if many things change, the learning becomes weak.
