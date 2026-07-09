---
name: experimentation-culture-rollout
description: Roll out an experimentation-friendly culture across product, engineering, data, and leadership teams. Use when introducing A/B testing to an organization, overcoming resistance to experiments, shifting teams away from launch-by-opinion, increasing experiment demand, defining rollout tactics, or creating an experimentation adoption plan.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Experimentation Culture Rollout
  category: Product Management
  tags: practical-ab-testing,ab-testing,experimentation,product-culture,change-management
---

# Experimentation Culture Rollout

Use this skill to help teams adopt A/B testing as a normal product and
engineering practice. The focus is organizational change: resistance,
stakeholder trust, rollout sequencing, education, demand generation, and
operating cadence.

## Source Traceability

Primary source: Practical A/B Testing by Leemay Nassery. Guidance is
transformed and paraphrased from chapter 6 lines 4507-5066, with motivation
from the preface lines 270-280 and chapter 1 lines 1019-1078.

## Related Advanced Skills

- `experimentation-strategy-roadmap`: use when culture rollout must connect to
  platform roadmap priorities, company strategy, and rate-quality-cost tradeoffs.
- `experiment-verification-monitoring`: use when trust problems come from
  invalid experiments, weak QA, missing health checks, or poor monitoring.
- `trustworthy-experiment-insights`: use when stakeholders need help
  understanding whether evidence is credible enough to influence decisions.

## Reference Routing

| Need | Read |
|------|------|
| Culture and adoption concepts | `references/core/knowledge.md` |
| Rollout and resistance rules | `references/core/rules.md` |
| Adoption scenarios | `references/core/examples.md` |
| Step-by-step rollout plan | `workflows/roll-out-experimentation.md` |

## Workflow

1. Identify what resistance is actually about: trust, speed, metrics, ownership,
   platform friction, or fear of failed experiments.
2. Pick a credible first team or product surface.
3. Run early tests that answer real stakeholder questions.
4. Share results as learning, not just wins.
5. Create lightweight templates, office hours, and examples.
6. Expand demand through internal proof and repeatable support.

## Output Format

```markdown
# Experimentation Culture Rollout Plan

## Adoption Goal
[What behavior should change.]

## Current Resistance
| Concern | Who Holds It | Response |
|---------|--------------|----------|

## First Rollout Slice
- Team:
- Product surface:
- First experiment:
- Why this slice:

## Enablement
- Templates:
- Training:
- Office hours:
- Decision cadence:

## Adoption Metrics
| Metric | Target |
|--------|--------|

## Risks
- Cultural:
- Technical:
- Data:
```

## Quality Bar

- Do not treat resistance as ignorance; identify the legitimate concern.
- Do not sell experimentation only as a way to win; emphasize learning and risk
  reduction.
- Do not roll out a process that is heavier than the team's trust in it.
- Use real internal examples as soon as they exist.
