# Experiment Sensitivity Optimization Examples

Examples for improving experiment signal without losing the decision.

## Scenario Examples

### Noisy Revenue Metric

**Situation**: A checkout UX change is expected to reduce form friction, but
purchase revenue is highly variable because a few large orders dominate.

**Better approach**:
- Use successful checkout completion as the primary metric.
- Keep revenue and refund rate as guardrails.
- Consider capping order value in analysis only if the decision is about broad
  conversion behavior rather than high-value order economics.

### Too Many Model Variants

**Situation**: A team wants to A/B test six recommendation models live.

**Problem**:
- Traffic is split across too many variants.
- Some models may have poor offline quality.

**Better approach**:
- Use offline evaluation to remove poor candidates.
- Live test the strongest one or two variants.
- Use `ml-experiment-evaluation` if ranking or model quality is the core issue.

### Historical Behavior Enables CUPED

**Situation**: Users have stable pre-experiment engagement history, and the
outcome is future engagement.

**Better approach**:
- Use pre-treatment engagement as a covariate.
- Validate that the covariate predicts the outcome.
- Document the adjusted and unadjusted readout.

### Small Effect Is Not Worth Detecting

**Situation**: Power analysis shows the team can detect a tiny lift after a long
run, but the lift would not change launch or roadmap decisions.

**Better approach**:
- Revisit practical significance.
- Use a higher meaningful threshold or run a lower-cost exploratory test.
- Avoid spending traffic on evidence that cannot change action.

## Anti-Examples

### "Switch To Clicks Because They Move"

**Problem**: Clicks are sensitive but may not represent the desired outcome.

**Fix**: Use clicks only if they are part of the expected mechanism and pair
them with downstream guardrails.

### "Add CUPED Because It Sounds Advanced"

**Problem**: The team lacks valid historical covariates or implementation
checks.

**Fix**: Keep the analysis simple or collect the data needed for future CUPED.

## Quick Selection Table

| Situation | Better Move |
|-----------|-------------|
| Broad metric too noisy | Use closer metric plus guardrails |
| Outliers dominate | Consider predeclared capping |
| Too many variants | Reduce or prefilter variants |
| Stable historical covariate exists | Consider CUPED/covariate adjustment |
| Effect too small to matter | Revisit MDE and decision threshold |
