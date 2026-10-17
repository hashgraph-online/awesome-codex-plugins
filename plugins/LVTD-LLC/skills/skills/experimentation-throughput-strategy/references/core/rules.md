# Experimentation Throughput Strategy Rules

Use these rules when choosing how to run more experiments without degrading
evidence quality.

## Core Rules

### 1. Diagnose The Bottleneck Before Changing Strategy

Do not assume traffic is the constraint.

- Map setup, QA, launch, run-time, analysis, and decision delays separately.
- Fix process/tooling bottlenecks before adopting statistically complex methods.
- Use current and upcoming experiment inventory as evidence.

### 2. Isolate Experiments When Interaction Risk Is High

Use isolated tests when overlapping would make the result hard to interpret.

- Same product surface or user journey.
- Same primary metric with plausible combined effects.
- High-stakes product or business decision.
- Regulatory, trust, safety, or user-harm concern.

### 3. Overlap Experiments Only With Explicit Safeguards

Overlapping is a strategy, not a default.

- Capture test metadata: owner, surface, audience, metrics, eligibility, timing.
- Monitor conflicts during launch, not only during analysis.
- Define who can require isolation or restart.

### 4. Preserve Metric Precision When It Matters

Higher throughput is not worth losing decision-quality evidence.

- Use `experiment-sensitivity-optimization` when traffic is scarce but precision
  matters.
- Use directional tests only for low-stakes learning, not high-impact launches.
- Name where the team accepts lower precision.

### 5. Make Capacity Visible

Teams cannot coordinate what they cannot see.

- Show active, scheduled, and recently completed tests.
- Show constrained surfaces, audiences, and metrics.
- Flag conflicts early enough to change launch plans.

## Guidelines

Less strict recommendations:

- Start with a hybrid policy when the organization is new to overlapping tests.
- Use templates for experiment metadata so conflict detection can be automated.
- Review throughput changes after several cycles; the first policy will need
  adjustment.

## Exceptions

- **Exploratory low-stakes tests**: Accept faster, lighter evidence when the goal
  is learning, not launch justification.
- **Emergency fixes**: Prioritize user protection; document why the normal
  scheduling strategy was bypassed.

## Quick Reference

| Rule | Summary |
|------|---------|
| Diagnose first | Know whether the constraint is traffic, tooling, QA, or decisions |
| Isolate risky tests | Protect interpretability when interaction risk is high |
| Safeguard overlaps | Overlap only with metadata, monitoring, and owners |
| Preserve precision | Do not trade away evidence quality for high-stakes decisions |
| Show capacity | Make the experiment pipeline visible |
