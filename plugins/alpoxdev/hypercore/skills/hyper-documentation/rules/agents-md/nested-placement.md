# Nested Placement

**Purpose**: Decide, with recorded measurements, whether a directory earns its own `AGENTS.md`. This is a package heuristic: it orders the decision and never substitutes for reading the repository.

## 1. What the score is

The placement score is a gate that justifies a child file. It is labelled a package heuristic in every report so nobody reads it as a vendor standard. A directory earns a child `AGENTS.md` only when the score says the subtree differs enough to govern on its own. Otherwise the parent covers it.

Never let the score trigger a repository-wide sweep. A bulk hierarchy run still requires an explicit user request; the score only justifies the single child file under review.

## 2. Signals and weights

Measure each signal only when repository evidence supports it. A signal that cannot be measured is `unmeasured`, and `unmeasured` never counts as zero.

| Signal | What to count | Weight |
|---|---|---|
| File count | Source files in the subtree | 2 |
| Subdirectory count | Immediate child directories with shipped code | 2 |
| Code ratio | Share of the subtree that is code rather than docs or data | 2 |
| Unique patterns | Distinct build, test, or convention patterns inside the subtree | 5 |
| Module boundary | A package, workspace, or ownership boundary the subtree crosses | 3 |
| Symbol density | Exports and entry points per file | 1 |
| Exports | Public entry points owned by the subtree | 1 |
| Reference centrality | How much the parent rule and neighboring files point at this subtree | 2 |

Add the weights of the measured signals. Report every `unmeasured` item by name in the run snapshot instead of folding it into the total.

## 3. Thresholds

| Score | Decision |
|---|---|
| Above 15 | The subtree earns a child `AGENTS.md` |
| 8 to 15 | A child file requires a distinct domain difference on top of the score |
| Below 8 | The parent covers the subtree; do not create a child file |

The same score on the same repository MUST NOT produce a different hierarchy between runs. The run snapshot records what was measured so two runs can be compared.

## 4. Depth budget

The depth budget defaults to 3 and limits creation only. A run MUST NOT create a child file deeper than the budget. The budget never deletes deeper existing files; an existing file below the budget stays where it is. Deleting one requires an explicit user request.

## 5. Score evidence row

Each placement decision records the score, the per-signal values, the `unmeasured` items, the depth, and the budget. A placement without those rows is unjustified.

## Sources

> Links checked 2026-11-09. No text or code was copied from the source repository. The mechanism is re-authored in this package's own words.

| Claim | Source |
|---|---|
| The weighted signals, the thresholds above 15 and at 8 to 15, the package-heuristic label, the depth budget default of 3, and the never-delete-below-budget rule in this file | `dbc-hbin/omp-ulw` at commit `74df40f` (2026-11-09); the source repository has no license, so the mechanism was re-authored, not copied |

### Evidence grade

`HEURISTIC` - the score is this package's own decision aid, re-authored from the source above, and not validated against any vendor standard.
