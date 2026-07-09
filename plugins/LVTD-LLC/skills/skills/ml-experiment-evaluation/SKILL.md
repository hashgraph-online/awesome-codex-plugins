---
name: ml-experiment-evaluation
description: Plan evaluation strategies for machine-learning product changes. Use when deciding between offline evaluation, interleaving, online A/B tests, multi-armed bandits, or model filtering for ranking, recommendation, search, personalization, or other ML-powered user experiences.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: ML Experiment Evaluation
  category: Product Management
  tags: practical-ab-testing,next-level-ab-testing,ab-testing,experimentation,machine-learning
---

# ML Experiment Evaluation

Use this skill to choose how to evaluate machine-learning product changes before
they consume live experiment traffic or affect users. It focuses on offline
evaluation, offline-online correlation, interleaving, model filtering, and when
classic A/B testing or adaptive strategies are justified.

## Source Traceability

Primary source: *Next-Level A/B Testing* by Leemay Nassery. Guidance is
transformed and paraphrased from Chapter 4 on offline evaluation, offline-online
correlation, multi-armed bandits, and interleaving for rankers.

Related skills:

- `experiment-sensitivity-optimization` for reducing live variants and traffic.
- `adaptive-experimentation-strategy` for bandits and dynamic allocation.
- `ab-test-design-brief` for standard online A/B test planning.

## Reference Routing

| Need | Read |
|------|------|
| ML evaluation concepts | `references/core/knowledge.md` |
| Selection and validation rules | `references/core/rules.md` |
| Evaluation strategy examples | `references/core/examples.md` |
| Step-by-step evaluation plan | `workflows/choose-ml-evaluation-strategy.md` |

## Workflow

1. State the model change and product decision.
2. Identify the user harm or trust risk if a poor model reaches production.
3. Choose the lowest-cost evaluation that can filter bad candidates.
4. Check offline metrics and whether they correlate with online outcomes.
5. Use interleaving when ranker comparison needs high sensitivity with fewer
   users.
6. Escalate to online A/B testing or adaptive testing only when live evidence is
   needed and infrastructure can support it.

## Output Format

```markdown
# ML Evaluation Strategy

## Model Decision
[What model or ranking decision must be made.]

## Recommended Evaluation Path
[Offline only | Offline then A/B | Interleaving | A/B test | Adaptive strategy]

## Why
- Product risk:
- Offline signal available:
- Online evidence needed:
- Traffic or capacity constraint:

## Metrics
| Metric | Offline/Online | Role | Concern |
|--------|----------------|------|---------|

## Implementation Notes
- Data needed:
- Logging needed:
- Correlation check:
- Rollout guardrails:
```

## Quality Bar

- Do not send poor offline candidates to live users just to get online evidence.
- Do not trust offline metrics until their relationship to online outcomes is
  understood.
- Do not use interleaving unless the product has a ranking or choice context
  where attribution can be logged.
- Do not recommend adaptive methods without checking data freshness,
  observability, and operational ownership.
