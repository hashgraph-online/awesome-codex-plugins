---
name: adaptive-experimentation-strategy
description: Plan adaptive experimentation strategies beyond fixed-horizon A/B tests. Use when evaluating sequential testing, early stopping, multi-armed bandits, Thompson sampling, contextual bandits, dynamic traffic allocation, exploration/exploitation tradeoffs, or readiness for adaptive testing infrastructure.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Adaptive Experimentation Strategy
  category: Product Management
  tags: practical-ab-testing,next-level-ab-testing,ab-testing,experimentation,adaptive-testing
---

# Adaptive Experimentation Strategy

Use this skill to decide whether and how to use adaptive testing strategies
instead of fixed-horizon A/B tests. It covers sequential testing, multi-armed
bandits, Thompson sampling, contextual bandits, exploration/exploitation, and
the data and engineering readiness required to operate them.

## Source Traceability

Primary source: *Next-Level A/B Testing* by Leemay Nassery. Guidance is
transformed and paraphrased from Chapter 7 on adaptive testing, sequential
testing, multi-armed bandits, Thompson sampling, contextual bandits, and
engineering requirements.

Related skills:

- `experiment-type-selection` for choosing simpler experiment types first.
- `ml-experiment-evaluation` for model and ranking evaluation paths.
- `experiment-verification-monitoring` for operational health and alerting.

## Reference Routing

| Need | Read |
|------|------|
| Adaptive testing concepts | `references/core/knowledge.md` |
| Readiness and strategy rules | `references/core/rules.md` |
| Scenario examples | `references/core/examples.md` |
| Step-by-step adaptive readiness plan | `workflows/evaluate-adaptive-strategy.md` |

## Workflow

1. State the decision and why fixed-horizon A/B testing may not be enough.
2. Decide whether the need is early stopping, reward maximization, or
   personalization.
3. Check data freshness, reward definition, dashboards, on-call ownership, and
   rollback controls.
4. Choose sequential testing, bandits, Thompson sampling, contextual bandits, or
   a simpler alternative.
5. Document exploration/exploitation tradeoffs and user/business risk.
6. Define rollout, monitoring, and adoption requirements.

## Output Format

```markdown
# Adaptive Experimentation Recommendation

## Use Case
[What decision or allocation problem motivates adaptive testing.]

## Recommended Strategy
[Do not use adaptive testing | Sequential | Bandit | Thompson sampling | Contextual bandit]

## Readiness
| Requirement | Status | Gap |
|-------------|--------|-----|

## Tradeoffs
- Reward:
- Exploration cost:
- Data freshness:
- Operational risk:

## Rollout Plan
1. [Step]
2. [Step]
3. [Step]
```

## Quality Bar

- Do not recommend adaptive testing just because it is advanced.
- Do not use bandits when the real need is a clean causal estimate.
- Do not use contextual bandits without reliable context features and reward
  measurement.
- Do not ignore production requirements: stale data, bad allocation, and alert
  ownership can break adaptive systems.
