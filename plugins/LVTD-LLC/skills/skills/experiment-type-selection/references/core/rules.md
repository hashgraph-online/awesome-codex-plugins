# Experiment Type Selection Rules

Rules for selecting the simplest valid experiment type.

## Core Rules

### 1. Let The Decision Question Choose The Test

Do not start with a favorite methodology. Start with the claim stakeholders
need to make.

### 2. Use Superiority For Upside Claims

Use superiority when the feature should only ship if it improves the primary
metric or produces a clear win.

### 3. Use Non-Inferiority For Safe-Enough Changes

Use non-inferiority when the change has value outside the primary metric and
the key concern is avoiding unacceptable regression.

Examples:
- Reduced engineering cost.
- Required platform migration.
- Accessibility or compliance improvement.
- Operational simplification.

### 4. Use Equivalence Only With A Practical Band

Equivalence needs an acceptable range. If the team cannot say how close is close
enough, the test cannot answer the question.

### 5. Treat More Variants As More Cost

Each extra variant consumes traffic and increases interpretation burden. Use
A/B/n only when each variant isolates a meaningful design choice.

### 6. Add Holdbacks For Time-Dependent Claims

Use holdbacks when short-term A/B results may miss delayed effects, degradation,
or cumulative changes.

## Common Mistakes

| Mistake | Consequence | Better Choice |
|---------|-------------|---------------|
| Using superiority for a required migration | Blocks useful changes without upside expectation | Non-inferiority |
| Calling a flat result "equivalent" without a band | Overstates the evidence | Equivalence with a predefined band |
| Testing many bundled changes | Weak learning about cause | Simpler variants or launch decision only |
| Skipping holdbacks for delayed effects | No long-term counterfactual | Holdback-backed rollout |
