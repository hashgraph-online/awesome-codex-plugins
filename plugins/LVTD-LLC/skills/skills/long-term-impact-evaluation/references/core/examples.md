# Long-Term Impact Evaluation Examples

Examples for choosing a long-term impact method.

## Scenario Examples

### New Recommendation Experience

**Situation**: A recommendation change improves week-one clicks, but the team
worries it may reduce long-term trust.

**Better approach**:
- Use a holdback if sustained trust and retention are strategic and withholding
  cost is acceptable.
- Otherwise combine post-period retention analysis with continuous monitoring of
  complaints and engagement quality.

### Checkout Feature With Immediate Revenue Lift

**Situation**: A checkout feature increases short-term conversion, and delayed
effects are unlikely.

**Better approach**:
- Continuous monitoring may be enough after rollout.
- Avoid a long-term holdback unless there is a clear delayed-risk hypothesis.

### Subscription Onboarding Change

**Situation**: A new onboarding flow increases activation, but long-term
retention and CLV matter more.

**Better approach**:
- Map activation to retention using historical data.
- Use post-period analysis for retention windows.
- Consider CLV prediction if historical validation is strong.

### Costly Holdback For High-Value Feature

**Situation**: A feature is clearly valuable to users, but the team wants a
six-month holdback by default.

**Better approach**:
- Challenge whether the long-term question justifies withholding.
- Consider shorter holdback, post-period analysis, or monitoring hybrid.
- Use detailed `holdback-experiment-design` only if the counterfactual is worth
  the cost.

## Anti-Examples

### "Monitor Revenue After Launch And Call It Long-Term Impact"

**Problem**: Revenue trends may reflect external factors.

**Fix**: Treat monitoring as detection; use post-period controls, holdbacks, or
models when causal interpretation matters.

### "Always Use A Holdback"

**Problem**: Strong measurement can be too costly or complex for the decision.

**Fix**: Compare methods and choose the simplest credible option.

## Quick Selection Table

| Situation | Better Method |
|-----------|---------------|
| Need strong causal long-term evidence | Holdback |
| Need faster rollout with later readout | Post-period analysis |
| Need anomaly detection | Continuous monitoring |
| Need long-term estimate soon | CLV model with validation |
| Costs and uncertainty are mixed | Hybrid approach |
