# A/B Test Results Readout Examples

## Flat Overall Result With Segment Signal

```markdown
## Executive Decision
Investigate before launch. Overall video plays increased slightly, but subgroup
analysis shows the effect is concentrated among high-consumption users while
low-consumption users are flat.
```

**Why it works**:
- Avoids treating the average as the whole story.
- Explains why a small aggregate movement may still matter.
- Does not overclaim that all users benefited.

## Mixed Metric Result

```markdown
## Executive Decision
Do not launch broadly yet. The test improved click-through rate, but revenue per
visitor declined beyond the agreed guardrail. Product and finance should decide
whether the engagement gain justifies the revenue tradeoff.
```

**Why it works**:
- Names the conflict.
- Escalates to the stakeholders who own the tradeoff.
- Avoids calling the test a simple win.

## Weak Readout

```markdown
The test variant won. Ship it.
```

**Problems**:
- No metric values or confidence.
- No guardrail interpretation.
- No population or run-window context.
- No caveats.

## Visualization Anti-Pattern

```text
One slide contains primary metric, five guardrails, six segments, and three time
series in a single chart.
```

**Problem**: The chart forces stakeholders to decode the analysis instead of
understanding the decision.

**Better**: Use one summary table for all metrics and one chart per important
comparison.
