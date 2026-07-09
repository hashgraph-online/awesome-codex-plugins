# Trustworthy Experiment Insights Examples

Examples for reviewing experiment evidence quality.

## Scenario Examples

### Suspiciously Large Conversion Lift

**Situation**: A small UI copy test reports a conversion lift much larger than
past checkout experiments.

**Credibility checks**:
- Was the experiment stopped early?
- Were many metrics or segments checked?
- Did assignment, exposure, or targeting behave correctly?
- Do similar experiments show comparable lift?

**Likely recommendation**: Replicate or extend before making a high-stakes
decision.

### Flat Result On A Noisy Metric

**Situation**: A feature expected to improve daily engagement shows no movement
in monthly retention.

**Credibility checks**:
- Was the metric too slow or broad for the test window?
- Was the experiment powered for retention?
- Is there a closer behavioral metric with guardrails?

**Likely recommendation**: Do not treat the flat result as proof of no effect;
redesign with better sensitivity.

### Positive Primary Metric, Negative Guardrail

**Situation**: Click-through improves, but user complaints and unsubscribe rate
increase.

**Credibility checks**:
- Are guardrails operationally healthy?
- Is the primary metric too narrow?
- Does the product decision accept this tradeoff?

**Likely recommendation**: Do not ship without resolving the guardrail risk.

### Result Matches Prior Evidence

**Situation**: A feature-level metric improves by a modest amount similar to
several past experiments on the same surface.

**Credibility checks**:
- Are population and metric definitions comparable?
- Did this test meet planned power and duration?
- Are guardrails clean?

**Likely recommendation**: Trust with caveats if the product decision is not
high-risk.

## Anti-Examples

### "P-value Is Below Threshold, Ship"

**Problem**: Ignores practical significance, many comparisons, and operational
validity.

**Fix**: Review health, effect size, prior evidence, and decision risk.

### "No Significant Result, Kill The Idea"

**Problem**: Ignores false negative risk.

**Fix**: Check power, metric sensitivity, duration, and confidence intervals.

## Quick Selection Table

| Evidence Pattern | Better Next Step |
|------------------|------------------|
| Big surprising win | Scrutinize and often replicate |
| Flat underpowered result | Redesign or extend |
| Clean modest result | Trust with caveats |
| Operational anomaly | Investigate before deciding |
| Similar prior results exist | Compare or meta-analyze |
