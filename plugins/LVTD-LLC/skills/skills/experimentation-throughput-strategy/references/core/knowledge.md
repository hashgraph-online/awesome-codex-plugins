# Experimentation Throughput Strategy Knowledge

Core concepts for increasing experiment rate in a mature product experimentation
program.

## Overview

Experimentation throughput is the rate at which teams can launch, run, analyze,
and decide from experiments. Improving throughput is not the same as launching
more tests at any cost; the goal is faster learning with evidence that remains
trustworthy.

## Key Concepts

### Testing Capacity

**Definition**: The practical limit on how many experiments can run for a given
audience, surface, metric, or time window.

Capacity may be constrained by traffic, engineering setup, QA, analysis, or
organizational coordination.

### Isolated Testing Strategy

**Definition**: Running experiments separately so each result is easier to
attribute to one change.

Isolation is useful when metric precision, strategic stakes, or interaction risk
is high. Its cost is lower throughput.

### Overlapping Testing Strategy

**Definition**: Running multiple experiments at the same time, often on the same
product, when their effects can be treated as sufficiently independent.

Overlapping tests can increase throughput, but require conflict detection,
visibility, and clear rules for handling interaction risk.

### Interaction Effect

**Definition**: A combined effect created by two or more experiments that cannot
be understood by looking at either experiment alone.

Interaction risk rises when tests change the same surface, user journey,
eligibility, or metric.

### Coordination Cost

**Definition**: The time and attention spent deciding which experiments can run,
who owns conflicts, and when decisions can be made.

Coordination cost grows as experiment demand, product complexity, and platform
usage grow.

## Terminology

| Term | Definition |
|------|------------|
| Testing availability | The remaining capacity to run experiments without unacceptable conflicts |
| Experiment queue | Backlog of experiments waiting for setup, capacity, or approval |
| Surface | Product area where users experience the change |
| Conflict dimension | Attribute that can make two tests interfere, such as audience or metric |
| Hybrid strategy | A policy that isolates some tests while allowing low-risk overlaps |

## How It Relates To

- **Experiment verification monitoring**: Throughput only works when active
  tests are observable and misconfigurations are caught early.
- **Experiment sensitivity optimization**: More sensitive metrics can reduce
  traffic needs and ease capacity pressure.
- **A/B testing platform strategy**: Tooling must expose capacity, ownership,
  and conflict metadata if teams are expected to self-serve.

## Common Misconceptions

- **Myth**: More tests automatically mean more learning.
  **Reality**: More low-quality tests can create more ambiguity and rework.
- **Myth**: Overlapping tests are always invalid.
  **Reality**: They can be practical when conflict risk is understood and
  monitored.
- **Myth**: Isolated testing is always safest.
  **Reality**: It can be too slow for low-risk, independent work and can waste
  scarce testing capacity.

## Quick Reference

| Concept | One-Line Summary |
|---------|------------------|
| Capacity | The practical ceiling on experiment volume |
| Isolation | Better attribution, lower rate |
| Overlap | Higher rate, needs safeguards |
| Interaction | Combined effect that threatens interpretation |
| Coordination | Process cost of running experiments across teams |
