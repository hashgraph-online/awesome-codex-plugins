---
name: experiment-type-selection
description: 'Choose the right product experiment type: superiority, non-inferiority, equivalence, A/B/n, or holdback-backed validation. Use when deciding what kind of A/B test to run, when the question is not simply "is variant better," when validating no degradation, proving similarity, comparing multiple variants, or selecting an experiment design for a mature product.'
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Experiment Type Selection
  category: Product Management
  tags: practical-ab-testing,ab-testing,experimentation,experiment-design,product-analytics
---

# Experiment Type Selection

Use this skill when the experiment question determines the test type. Not every
experiment should be a simple superiority test; some decisions need evidence
that a change is not worse, roughly equivalent, or durable over time.

## Source Traceability

Primary source: Practical A/B Testing by Leemay Nassery. Guidance is
transformed and paraphrased from chapter 3, especially lines 2013-2870. Related
variant design context comes from chapter 1 lines 539-571 and chapter 2 lines
1564-1735.

## Related Advanced Skills

- `experimentation-throughput-strategy`: use when the choice is isolated versus
  overlapping testing or when testing availability constrains the design.
- `adaptive-experimentation-strategy`: use when fixed-horizon A/B testing may be
  replaced by sequential testing, bandits, or contextual bandits.
- `ml-experiment-evaluation`: use when the experiment is evaluating ML models,
  rankers, offline metrics, interleaving, or model filtering.
- `long-term-impact-evaluation`: use when the test type question is really
  about delayed or sustained impact measurement.

## Reference Routing

| Need | Read |
|------|------|
| Test type concepts | `references/core/knowledge.md` |
| Selection rules | `references/core/rules.md` |
| Scenario examples | `references/core/examples.md` |
| Step-by-step selection | `workflows/choose-experiment-type.md` |

## Workflow

1. State the decision question in plain language.
2. Identify whether the team wants to prove improvement, avoid degradation, or
   show practical similarity.
3. Check whether the metric movement must persist after launch.
4. Decide whether multiple variants are necessary and interpretable.
5. Choose the simplest test type that answers the decision question.
6. Document assumptions, risk, and follow-up analysis.

## Output Format

```markdown
# Experiment Type Recommendation

## Decision Question
[What the team needs to learn.]

## Recommended Type
[Superiority | Non-inferiority | Equivalence | A/B/n | Holdback]

## Why This Type Fits
- Goal:
- Metric behavior needed:
- Risk tolerance:
- Time horizon:

## Design Notes
- Primary metric:
- Guardrails:
- Variants:
- Population:
- Follow-up analysis:

## Do Not Use
[Types that would answer the wrong question and why.]
```

## Quality Bar

- Do not default to superiority when the real question is safety or sameness.
- Do not use equivalence unless the team can define an acceptable equivalence
  band.
- Do not recommend many variants unless the user has traffic and the variants
  preserve interpretable learning.
- Use `holdback-experiment-design` for detailed long-term holdback planning.
