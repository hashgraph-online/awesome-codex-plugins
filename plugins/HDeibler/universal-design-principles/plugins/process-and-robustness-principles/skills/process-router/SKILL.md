---
name: process-router
description: 'Use this skill whenever the question is *how* to design well over time or *how* to make a design that doesn''t break — accessibility, prototyping cadence, MVP scoping, edge cases, performance budget, error handling at scale, design system governance, or any architectural-design question. Trigger on accessibility questions, "is this ready to ship," "what about the edge case where," design reviews, MVP scoping, "we have too many opinions on this." Framework-agnostic. Routes the model to the right process or robustness principle in this plugin.'
---

# Process & robustness — router

This plugin holds the principles that govern *how design happens* and *how it survives contact with reality* — accessibility, iteration loops, edge cases, design-team dynamics, robustness against scale.

## Principles in this plugin

Each principle has its own skill (with sub-aspect skills where useful). Principles marked **[full]** have reference-grade skill files; the rest are planned and will be added in subsequent passes.

### Inclusion

- **`accessibility`** *[full]* — usable by people with the widest possible range of abilities.
  - Sub-skills: `accessibility-perceivable`, `accessibility-operable`, `accessibility-understandable`, `accessibility-robust`.

### Process and iteration

- **`iteration`** — design is a loop, not a waterfall.
- **`prototyping`** — making something concrete reveals what specs cannot.
- **`development-cycle`** — projects move through requirements, design, develop, test phases.
- **`life-cycle`** — products age; design for the whole arc, not just launch.
- **`design-by-committee`** — group consensus produces averaged designs; beware.
- **`not-invented-here`** — reflexive rejection of external solutions costs time and quality.
- **`ockhams-razor`** *(also in cognition)* — among solutions that work, prefer the simplest.

### Robustness and edge cases

- **`factor-of-safety`** — design with margin so normal operation isn't at the edge of failure.
- **`weakest-link`** — chains break at the weakest link; find and reinforce it.
- **`normal-distribution`** — most users cluster around the mean; design for the bulk, accommodate the tails.
- **`scaling-fallacy`** — what works at small scale doesn't necessarily scale.
- **`uncertainty-principle`** — observation changes the observed; instrumentation distorts behavior.
- **`structural-forms`** — load-bearing patterns that distribute stress (mass, frame, shell).

## Heuristic for which to read first

- **Every design task** → `accessibility`. Read it, run the checklist.
- **MVP scoping** → `iteration`, `ockhams-razor`, `factor-of-safety`.
- **"Is this ready to ship?"** → `weakest-link`, `factor-of-safety`, `accessibility`.
- **Design system governance** → `consistency` (cognition), `modularity` (cognition), `life-cycle`.
- **Reviewing scale** → `scaling-fallacy`, `normal-distribution`.
- **Stuck in committee** → `design-by-committee`, `not-invented-here`, `ockhams-razor`.
- **Performance / latency** → `weakest-link`, `factor-of-safety`, `feedback-loop` (interaction).

## Cross-plugin pointers

- For *visual* hierarchy and grouping, see `perception-and-hierarchy-principles`.
- For *learnability*, see `cognition-and-learnability-principles`.
- For *behavior*, see `interaction-and-control-principles`.
- For *aesthetic and tonal* decisions, see `aesthetics-and-emotion-principles`.
