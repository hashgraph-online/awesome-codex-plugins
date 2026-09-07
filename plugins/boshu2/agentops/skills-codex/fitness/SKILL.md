---
name: fitness
description: 'Measure declared project fitness goals Triggers: "fitness", "check project fitness", "measure goals".'
---
# Fitness — read-only goal measurement

Inspect the active goals document and run only the caller-selected measurement,
validation, drift, history, export, or meta-goal command.

Renamed from `goals` (2026-07-29): the semantic skill is `fitness`; the
`ao goals` CLI command family is a separate product surface and keeps its
name. A thin `goals` compatibility alias resolves to this skill.

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
- No subcommand edits the goals source through its own logic. `measure`,
  `drift`, and `export` persist a best-effort JSON snapshot under the fixed
  derived path `.agents/ao/goals/baselines/`. `render --out <file>` writes a
  Gherkin spec to whatever path the caller names — the CLI does not constrain
  it, so never point `--out` at the goals source or any non-derived file.

## Commands

All eight subcommands read the goals source without mutating it. The snapshot
write (fixed derived path) and the `render --out` write (caller-chosen path,
caller's responsibility) are the only side effects.

```bash
ao goals measure --json
ao goals validate --json
ao goals drift
ao goals history
ao goals export
ao goals meta --json
ao goals scenarios
ao goals render          # append --out <file> to write the spec instead of stdout
```

Run the requested command once. Return the command, exit code, goal-level
results, aggregate measurement, missing evidence, and checked/not-checked scope.
Then stop.
