---
name: goals
description: Measure declared project fitness goals
---
# Goals — read-only fitness measurement

Inspect the active goals document and run only the caller-selected measurement,
validation, drift, history, export, or meta-goal command.

Measurement stays trustworthy only because it cannot mutate what it measures;
the moment a fitness report edits a goal, the next report measures the editor,
not the project.

Named failure mode — **advice creep**: a measurement report that ends with
"you should…" has silently become work selection.

Anti-pattern: padding the report with recommendations to look helpful.
Corrective: return the numbers, the evidence gaps, and checked/not-checked
scope, and let the caller decide.

## Boundary

- Prefer `GOALS.md` when both Markdown and legacy YAML exist.
- Preserve stable directive and gate identities in the report.
- Every measured gate must name its executable check and observed outcome.
- Do not add, remove, prioritize, recommend, apply, prune, migrate, or otherwise
  mutate goals.
- Do not translate a fitness gap into work selection or a next action.

## Read-only commands

```bash
ao goals measure --json
ao goals validate --json
ao goals drift
ao goals history
ao goals export
ao goals meta --json
```

Run the requested command once. Return the command, exit code, goal-level
results, aggregate measurement, missing evidence, and checked/not-checked scope.
Then stop.
