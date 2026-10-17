# A/B Test Results Readout Rules

Rules for analyzing and presenting experiment results.

## Core Rules

### 1. Rebuild The Experiment Context First

Before interpreting numbers, restate hypothesis, population, variants, run
window, metrics, and decision rules.

### 2. Check Data Quality Before Calling Results

Verify that:

- Exposure events were logged.
- Users were assigned to only expected variants.
- Metric data exists for control and test.
- Data granularity supports the analysis.
- The run window matches the intended test.

### 3. Interpret Primary And Guardrail Metrics Together

A primary metric win can still be a poor launch if guardrails regress. A flat
primary metric may still be acceptable if the experiment was designed for
non-inferiority or operational benefit.

### 4. Use Subgroups To Explain, Not To Rescue

Segment analysis can reveal important effects, but avoid using many unplanned
segments to manufacture a win.

State whether subgroup analysis was planned or exploratory.

### 5. Investigate Outliers When Averages Look Odd

Check distributions when:

- The average moves but medians or percentiles do not.
- A small user group may dominate behavior.
- The result feels inconsistent with product expectations.

### 6. Make Visualizations Decision-Oriented

Every chart should make one comparison clearer. Label metric role, variant,
segment, and time window.

## Readout Checklist

| Area | Check |
|------|-------|
| Context | Hypothesis and variants restated |
| Validity | Exposure, eligibility, data quality checked |
| Metrics | Primary and guardrails interpreted together |
| Segments | Meaningful subgroup differences noted |
| Visualization | Charts answer decision questions |
| Recommendation | Decision and caveats explicit |
