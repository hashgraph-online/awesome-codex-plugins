---
name: ab-testing-platform-strategy
description: Plan A/B testing platform strategy, architecture, and build-vs-buy decisions for product engineering teams. Use when deciding whether to build or buy an experimentation platform, scoping feature flagging, targeting, assignment, exposure logging, metrics pipelines, dashboards, governance, or evolving a simple testing setup into a durable platform.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: A/B Testing Platform Strategy
  category: Product Management
  tags: practical-ab-testing,ab-testing,experimentation,platform-engineering,product-analytics
---

# A/B Testing Platform Strategy

Use this skill to decide how an organization should support A/B testing through
platform choices, architecture, ownership, and incremental scope.

## Source Traceability

Primary source: Practical A/B Testing by Leemay Nassery. Guidance is
transformed and paraphrased from chapter 5 lines 3804-4443. Related startup
and "start simple" context comes from preface lines 286-332 and chapter 2 lines
1622-1628.

## Related Advanced Skills

- `experimentation-strategy-roadmap`: use when deciding which platform
  capability to prioritize across rate, quality, cost, usability, and company
  strategy.
- `experimentation-throughput-strategy`: use when the platform needs capacity
  visibility, isolated versus overlapping test policies, or coordination tools.
- `experiment-verification-monitoring`: use when the platform needs QA tooling,
  canaries, A/A tests, active monitoring, leakage checks, or quality metrics.
- `adaptive-experimentation-strategy`: use when considering sequential testing,
  bandits, Thompson sampling, contextual bandits, or dynamic allocation support.

## Reference Routing

| Need | Read |
|------|------|
| Platform concepts and components | `references/core/knowledge.md` |
| Build-vs-buy and scoping rules | `references/core/rules.md` |
| Scenario examples | `references/core/examples.md` |
| Decision workflow | `workflows/decide-platform-strategy.md` |

## Workflow

1. State the experimentation goals and current constraints.
2. Inventory required platform components.
3. Separate must-have launch capability from later platform maturity.
4. Compare build, buy, and hybrid options against team capacity and risk.
5. Plan data, assignment, exposure logging, metrics, and reporting ownership.
6. Define the smallest useful platform and the triggers for expanding it.

## Output Format

```markdown
# A/B Testing Platform Strategy

## Recommendation
[Build | Buy | Hybrid | Start manually] because [reason].

## Current Context
- Team:
- Product surface:
- Experiment volume:
- Data maturity:
- Engineering capacity:

## Required Capabilities
| Capability | Need Now? | Build/Buy/Manual | Owner |
|------------|-----------|------------------|-------|

## Tradeoffs
- Build advantages:
- Build risks:
- Buy advantages:
- Buy risks:
- Hybrid notes:

## Incremental Roadmap
1. Minimum viable experimentation:
2. Reliability and governance:
3. Scale and self-service:
```

## Quality Bar

- Do not recommend building a full platform before the team has proven demand.
- Do not recommend buying without checking integration, data, and governance
  fit.
- Keep data and exposure logging first-class; a platform without trustworthy
  measurement creates false confidence.
- Treat platform scope as evolutionary, not all-or-nothing.
