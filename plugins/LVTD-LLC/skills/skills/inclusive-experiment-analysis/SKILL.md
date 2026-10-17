---
name: inclusive-experiment-analysis
description: Evaluate A/B tests for inclusive product impact across user groups, accessibility needs, device constraints, privacy behavior, bandwidth, geography, and underrepresented segments. Use when checking whether an experiment benefits or harms different user groups, planning segmentation dimensions, auditing test/control balance, interpreting subgroup effects, or reviewing product changes for inclusive experimentation.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Inclusive Experiment Analysis
  category: Product Management
  tags: practical-ab-testing,ab-testing,experimentation,inclusive-design,product-analytics
---

# Inclusive Experiment Analysis

Use this skill to make sure experiment design and readouts consider the range
of users affected by a product change. It focuses on subgroup impact,
accessibility, representation, data dimensions, and unintended harm.

## Source Traceability

Primary source: Practical A/B Testing by Leemay Nassery. Guidance is
transformed and paraphrased from chapter 1 lines 719-912 and related subgroup
analysis context from lines 639-718. Metric and eligibility context comes from
chapter 2 lines 1564-1735.

## Related Advanced Skills

- `trustworthy-experiment-insights`: use when subgroup findings may be
  underpowered, false positives, or false negatives.
- `experiment-verification-monitoring`: use when inclusion risks depend on
  assignment, exposure, device, geography, accessibility, or segment monitoring.
- `adaptive-experimentation-strategy`: use cautiously when contextual bandits or
  personalization could create uneven user impact across groups.

## Reference Routing

| Need | Read |
|------|------|
| Inclusive experiment concepts | `references/core/knowledge.md` |
| Design and analysis rules | `references/core/rules.md` |
| Segment examples | `references/core/examples.md` |
| Review workflow | `workflows/review-inclusive-impact.md` |

## Workflow

1. Identify which user groups could experience the change differently.
2. Choose dimensions that are relevant, ethical, and available.
3. Check test/control balance for important dimensions when possible.
4. Include accessibility, bandwidth, device, privacy, geography, and usage-level
   concerns where relevant.
5. Analyze subgroup outcomes without cherry-picking.
6. Recommend launch, mitigation, follow-up testing, or deeper research.

## Output Format

```markdown
# Inclusive Experiment Review

## Change Under Review
[What is changing and who may be affected.]

## User Dimensions
| Dimension | Why It Matters | Data Available? | Use In Analysis? |
|-----------|----------------|-----------------|------------------|

## Balance And Impact
| Segment | Control | Test | Result | Concern |
|---------|---------|------|--------|---------|

## Risks
- Accessibility:
- Device or bandwidth:
- Privacy or consent:
- Representation:
- Data limitations:

## Recommendation
[Ship | Ship with mitigation | Do not ship | Investigate] because [reason].
```

## Quality Bar

- Do not use sensitive attributes casually; explain why a dimension is needed.
- Do not claim inclusive impact when the data lacks relevant representation.
- Do not average away harm to a meaningful subgroup.
- Pair quantitative subgroup analysis with qualitative or accessibility review
  when metrics cannot capture the risk.
