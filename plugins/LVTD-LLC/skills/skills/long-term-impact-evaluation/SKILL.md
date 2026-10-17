---
name: long-term-impact-evaluation
description: Choose methods for measuring long-term product impact after or beyond an A/B test. Use when comparing long-term holdbacks, post-period analysis, continuous monitoring, CLV models, delayed effects, short-term versus long-term metric tradeoffs, or lower-cost alternatives to long-term holdbacks.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Long-Term Impact Evaluation
  category: Product Management
  tags: practical-ab-testing,next-level-ab-testing,ab-testing,experimentation,holdbacks
---

# Long-Term Impact Evaluation

Use this skill to choose a practical method for measuring product impact beyond
the initial experiment window. It compares long-term holdbacks, post-period
analysis, continuous monitoring, and customer lifetime value models.

## Source Traceability

Primary source: *Next-Level A/B Testing* by Leemay Nassery. Guidance is
transformed and paraphrased from Chapter 8 on long-term impact, short-term and
long-term metric relationships, holdbacks, post-period analysis, continuous
monitoring, and CLV models.

Related skills:

- `holdback-experiment-design` for detailed holdback planning.
- `trustworthy-experiment-insights` for result credibility and false positives.
- `experimentation-strategy-roadmap` for cost, quality, and complexity tradeoffs.

## Reference Routing

| Need | Read |
|------|------|
| Long-term evaluation concepts | `references/core/knowledge.md` |
| Method selection and risk rules | `references/core/rules.md` |
| Scenario examples | `references/core/examples.md` |
| Step-by-step method selection | `workflows/choose-long-term-evaluation.md` |

## Workflow

1. State why short-term experiment metrics are insufficient.
2. Identify the expected time horizon and delayed mechanisms.
3. Compare holdback, post-period analysis, continuous monitoring, and CLV model
   options.
4. Weigh accuracy against user cost, business cost, complexity, and confounding.
5. Choose the simplest method that answers the long-term question.
6. Define metric cadence, interpretation limits, and follow-up decisions.

## Output Format

```markdown
# Long-Term Impact Evaluation Plan

## Long-Term Question
[What delayed or sustained effect must be measured.]

## Recommended Method
[Holdback | Post-period analysis | Continuous monitoring | CLV model | Hybrid]

## Tradeoffs
| Method | Benefit | Cost/Risk | Fit |
|--------|---------|-----------|-----|

## Measurement Plan
- Short-term metric:
- Long-term metric:
- Time horizon:
- Confounders:

## Decision Rules
- Continue measuring if:
- End or revise if:
- Escalate if:
```

## Quality Bar

- Do not create a long-term holdback when a lower-cost method can answer the
  decision well enough.
- Do not use post-period analysis without accounting for external factors such
  as seasonality or campaigns.
- Do not rely on CLV models without naming model drift and behavior-change risk.
- Do not confuse continuous monitoring with causal long-term measurement.
