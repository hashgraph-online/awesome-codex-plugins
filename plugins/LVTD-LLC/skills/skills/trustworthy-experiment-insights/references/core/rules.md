# Trustworthy Experiment Insights Rules

Use these rules when deciding whether experiment evidence is decision-ready.

## Core Rules

### 1. Check Operational Validity First

Do not judge statistical credibility before verifying the experiment ran as
intended.

- Confirm assignment, exposure, treatment, and metric health.
- Review canary or monitoring issues.
- Investigate leakage or interference concerns.

### 2. Treat Surprising Wins As Evidence To Verify

Large or unexpected wins deserve extra scrutiny.

- Compare lift size to similar experiments.
- Check for many comparisons or segment fishing.
- Consider replication or longer duration for high-stakes changes.

### 3. Treat Flat Results As Evidence Quality Questions

A flat result can be meaningful or underpowered.

- Check actual sample and duration against plan.
- Check whether the metric was sensitive to the feature mechanism.
- Check confidence intervals and practical significance, not only p-values.

### 4. Use Meta-Analysis Carefully

Prior experiments can calibrate expectations, but only if comparable.

- Compare population, surface, metric, treatment, and timing.
- Note differences that limit interpretation.
- Use meta-analysis to inform next action, not to force certainty.

### 5. Choose Follow-Up Based On Decision Risk

Not every result needs replication.

- Ship when evidence is credible and decision risk is acceptable.
- Replicate or extend when stakes are high or result risk is high.
- Investigate when operational or analytical anomalies remain.

## Guidelines

Less strict recommendations:

- Keep a repository of comparable experiment results and effect sizes.
- Report credibility caveats in plain language for product stakeholders.
- Use `experiment-sensitivity-optimization` before rerunning an underpowered
  experiment.

## Exceptions

- **Low-stakes directional learning**: A result can guide exploration without
  being launch-ready.
- **User-safety concerns**: Strong negative guardrail movement may require action
  before perfect statistical certainty.

## Quick Reference

| Rule | Summary |
|------|---------|
| Health first | Verify the experiment ran correctly |
| Scrutinize surprises | Big wins may be false positives |
| Investigate flats | Flat results may be false negatives |
| Compare carefully | Meta-analysis needs comparable tests |
| Match action to risk | Replicate when uncertainty and stakes justify it |
