# Adaptive Experimentation Strategy Examples

Examples for choosing adaptive experimentation methods.

## Scenario Examples

### Early Stop For Clear Winner

**Situation**: A team runs high-volume homepage tests and wants to stop early
when evidence is clear.

**Better approach**:
- Consider sequential testing with planned interim analyses.
- Define stopping rules before launch.
- Keep a maximum duration and guardrails.

### Promotion Allocation During Campaign

**Situation**: A short campaign has several creative variants, and reward during
the campaign matters more than a final clean comparison.

**Better approach**:
- Consider a bandit if reward is measured quickly.
- Monitor exploration cost and guardrails.
- Do not claim the same interpretation as a fixed A/B readout.

### Personalized Recommendation Treatment

**Situation**: Different user contexts likely benefit from different
recommendation strategies.

**Better approach**:
- Consider contextual bandits only if context features are reliable.
- Monitor group-level outcomes and user trust.
- Start with limited exposure and clear rollback criteria.

### Weak Data Infrastructure

**Situation**: Product wants Thompson sampling, but reward data arrives days late
and dashboards are immature.

**Better approach**:
- Do not implement adaptive allocation yet.
- Improve data freshness, monitoring, and ownership first.
- Use fixed-horizon tests or offline evaluation while infrastructure matures.

## Anti-Examples

### "Use A Bandit To Prove Variant B Is Better"

**Problem**: The request asks for a clean causal comparison, not reward
maximization.

**Fix**: Use a standard A/B test or experiment type selection unless dynamic
allocation is the goal.

### "Contextual Bandit Without Context Quality"

**Problem**: Bad or unstable features create misleading personalization.

**Fix**: Validate features, reward, and monitoring before adaptive rollout.

## Quick Selection Table

| Situation | Better Strategy |
|-----------|-----------------|
| Need planned early stopping | Sequential testing |
| Need reward during test | Multi-armed bandit |
| Want Bayesian allocation | Thompson sampling |
| Want personalization by context | Contextual bandit |
| Need clean readout | Fixed experiment design |
