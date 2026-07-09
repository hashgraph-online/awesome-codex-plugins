---
name: holdback-experiment-design
description: Design degradation holdbacks and long-term cumulative holdbacks for product experiments and feature rollouts. Use when a team needs a long-term counterfactual, wants to measure delayed impact after launch, is worried about metric degradation over time, needs to decide holdback size or duration, or must weigh the user/business cost of withholding a feature.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Holdback Experiment Design
  category: Product Management
  tags: practical-ab-testing,ab-testing,experimentation,holdbacks,product-analytics
---

# Holdback Experiment Design

Use this skill to plan holdbacks that preserve a comparison group after a
feature rollout. Holdbacks are useful when effects may appear later, accumulate,
or degrade after launch.

## Source Traceability

Primary source: Practical A/B Testing by Leemay Nassery. Guidance is
transformed and paraphrased from chapter 3 lines 2487-2836. Experiment-type
context comes from chapter 3 lines 2013-2486.

## Related Advanced Skills

- `long-term-impact-evaluation`: use before detailed holdback design when the
  team should compare holdbacks against post-period analysis, continuous
  monitoring, CLV models, or hybrid methods.
- `trustworthy-experiment-insights`: use when deciding whether long-term or
  holdback evidence is credible enough to drive a product decision.

## Reference Routing

| Need | Read |
|------|------|
| Holdback concepts | `references/core/knowledge.md` |
| Design and cost rules | `references/core/rules.md` |
| Scenario examples | `references/core/examples.md` |
| Step-by-step planning | `workflows/design-holdback.md` |

## Workflow

1. State why short-term A/B evidence is insufficient.
2. Choose degradation or long-term cumulative holdback.
3. Define who remains withheld, for how long, and from what experience.
4. Select long-term metrics and guardrails.
5. Estimate the user, business, and ethical cost of withholding.
6. Define monitoring cadence, exit criteria, and communication plan.

## Output Format

```markdown
# Holdback Plan

## Purpose
[What long-term question this holdback answers.]

## Holdback Type
[Degradation | Long-term cumulative]

## Population And Duration
- Holdback population:
- Rollout population:
- Duration:
- Removal criteria:

## Metrics
| Metric | Role | Readout Cadence | Concern |
|--------|------|-----------------|---------|

## Cost Of Withholding
- User cost:
- Business cost:
- Ethical or trust concern:

## Decision Rules
- Continue holdback if:
- End holdback if:
- Escalate if:
```

## Quality Bar

- Do not create a holdback without a specific long-term question.
- Do not withhold a clearly valuable feature longer than the question requires.
- Do not ignore the opportunity cost to held-back users.
- Monitor guardrails while the holdback is active.
