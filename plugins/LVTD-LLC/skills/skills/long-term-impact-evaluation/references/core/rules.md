# Long-Term Impact Evaluation Rules

Use these rules when choosing how to measure delayed product impact.

## Core Rules

### 1. Start With The Long-Term Question

Do not choose a method before naming the effect.

- Define the user or business behavior that may appear later.
- Define the expected time horizon.
- Explain why short-term metrics are insufficient.

### 2. Use Holdbacks When Counterfactual Strength Matters

Holdbacks are strongest when the decision requires causal long-term evidence.

- Use `holdback-experiment-design` for detailed planning.
- Estimate user and business cost of withholding.
- Define duration and exit criteria before launch.

### 3. Use Post-Period Analysis When Rollout Speed Matters

Post-period analysis is a middle ground, not a perfect substitute.

- Account for seasonality, campaigns, and product changes.
- Choose comparison windows before analysis.
- Document confounders that limit interpretation.

### 4. Use Continuous Monitoring For Detection

Monitoring is excellent for alerts and trend awareness.

- Do not present monitoring alone as causal proof.
- Pair monitoring with predeclared metrics and thresholds.
- Escalate anomalies into deeper analysis or experiments.

### 5. Use CLV Models With Drift Checks

Predictive models can help when long-term outcomes take too long to observe.

- Validate predictions against historical outcomes.
- Monitor drift after product or market changes.
- Pair predictions with observed long-term metrics when available.

## Guidelines

Less strict recommendations:

- Use hybrid approaches when no single method answers the question well.
- Prefer the lowest-cost method that is credible enough for the decision.
- Keep long-term measurement understandable to product stakeholders.

## Exceptions

- **High-stakes strategy changes**: Prefer stronger counterfactual evidence even
  when it costs more.
- **Low-risk exploratory changes**: Monitoring or post-period analysis may be
  enough.

## Quick Reference

| Rule | Summary |
|------|---------|
| Question first | Define the delayed effect |
| Holdback for causality | Use when counterfactual strength matters |
| Post-period with caveats | Manage confounding explicitly |
| Monitoring for detection | Do not claim causality from trends alone |
| CLV with drift checks | Validate predictions over time |
