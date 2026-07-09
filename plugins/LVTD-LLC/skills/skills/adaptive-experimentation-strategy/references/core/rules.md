# Adaptive Experimentation Strategy Rules

Use these rules before recommending or implementing adaptive testing.

## Core Rules

### 1. Use Adaptive Testing Only For A Specific Need

Do not adopt adaptive methods because they sound advanced.

- Early stopping need: consider sequential testing.
- Reward maximization need: consider bandits.
- Personalization need: consider contextual bandits.
- Clean causal estimate need: prefer standard experiment designs.

### 2. Define Reward And Guardrails Up Front

Adaptive systems optimize what they can measure.

- Choose a reward close enough to the real product goal.
- Add guardrails for user trust, business risk, and reliability.
- Monitor for narrow optimization or harmful side effects.

### 3. Check Data Freshness And Allocation Reliability

Adaptive tests depend on timely data.

- Confirm reward data arrives quickly enough for decisions.
- Confirm allocation updates are applied correctly.
- Alert on stale data, missing data, and allocation anomalies.

### 4. Start With One High-Value Use Case

Adaptive platformization should be earned.

- Pick a use case where adaptive allocation clearly matters.
- Avoid building broad infrastructure before proving value.
- Document learnings before expanding to more teams.

### 5. Assign Operational Ownership

Adaptive systems create production responsibilities.

- Name owners for algorithm behavior, data pipelines, dashboards, and rollback.
- Define on-call expectations for stale data or bad allocation.
- Provide user-friendly tooling before asking teams to self-serve.

## Guidelines

Less strict recommendations:

- Prefer sequential testing before bandits when the team mainly wants early
  stopping.
- Use templates and visualizations to make adaptive methods understandable.
- Compare adaptive benefit against engineering complexity and adoption cost.

## Exceptions

- **Small one-off analysis**: Do not platformize; a standard test may be enough.
- **High-risk user experiences**: Keep tighter controls and slower rollout even
  when adaptive allocation could maximize reward.

## Quick Reference

| Rule | Summary |
|------|---------|
| Specific need | Match method to early stopping, reward, or personalization |
| Reward plus guardrails | Optimize responsibly |
| Fresh data | Adaptive allocation fails with stale signals |
| Prove with one use case | Do not platformize prematurely |
| Name owners | Treat adaptive testing as production infrastructure |
