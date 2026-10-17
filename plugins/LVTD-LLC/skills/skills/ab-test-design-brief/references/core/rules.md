# A/B Test Design Brief Rules

Use these rules to write or review an experiment brief.

## Core Rules

### 1. Start With A Decision

State the decision the test must support before choosing metrics.

- Good: "Should we ship the new recommendation module to all eligible users?"
- Weak: "Does the new module work?"

### 2. Write A Complete Hypothesis

Include observation, change, audience, expected outcome, and measurement.

- Avoid "test X to see what happens."
- Tie the prediction to product or user behavior.

### 3. Separate Success Metrics From Guardrails

Pick one primary success metric when possible. Add guardrails for metrics that
must not degrade.

- Success metric: the metric used to call the test.
- Guardrail: the metric that can block launch even when the primary improves.

### 4. Name Metric Compromises

If the ideal metric is missing, document the proxy and why it is usable.

- Note missing instrumentation.
- Note the proxy's known blind spots.
- Prefer user-level or segmentable data when later analysis is likely.

### 5. Define Eligibility Precisely

Specify who can enter the test and when they are counted as exposed.

- Eligibility may depend on geography, device, account status, permissions, or
  feature access.
- Exposure should match meaningful interaction with the tested surface.

### 6. Preserve A Coherent User Experience

Choose a randomization unit that will not confuse users.

- Pageview randomization can work for isolated page changes.
- Session randomization can work for visit-scoped experiences.
- User randomization is safer when consistency across visits matters.

### 7. Do Not Overload Variants

Keep each variant interpretable. When a variant changes many things at once,
the result can still support a launch decision but not precise learning.

## Quick Reference

| Brief Section | Required Check |
|---------------|----------------|
| Hypothesis | Specific audience, change, outcome, metric |
| Metrics | Primary, guardrails, baseline, data source |
| Variants | Control, test, eligibility, exposure |
| Confidence | MDE, duration or sample size, validity risks |
| Decision | Ship, stop, or investigate criteria |
