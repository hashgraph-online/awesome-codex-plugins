# Model Evaluation

Use this protocol to decide whether a standalone skill improves frontier-model repository work enough to justify its routing and maintenance cost.

## Conditions

Run each scenario with the same repository fixture, user prompt, permissions, model effort, and time budget.

1. `repo-only`: target repository instructions and native agent capabilities, without this plugin.
2. `compact-suite`: the released Agent Harness Skills version.
3. `candidate`: the proposed skill or wording change.

Run at least two frontier model families when available. Record exact model and agent-runtime versions; do not compare results from silently different tools or permissions.

## Required Scenarios

| Scenario | Required behavior |
| --- | --- |
| Entrypoint drift | Chooses one canonical instruction surface, preserves subtree rules, and proposes a real drift check. |
| Repository boundary | Converts a concrete architecture rule into diff and audit checks without hiding historical debt. |
| Validation surface | Maps existing commands before adding a checker and chooses a minimum gate by change type. |
| Runtime blocker | Links observed behavior to available evidence and distinguishes code, environment, dependency, data, and not-evaluable outcomes. |
| Work state and delivery | Keeps design, current task status, and delivery evidence in distinct authoritative surfaces. |
| Ordinary commit | Follows repository commit rules without loading optional governance or inventing task and ledger files. |

Add project-neutral scenarios when a change targets a narrower behavior, but keep the same scenario across all conditions.

## Scorecard

Score each dimension from `0` to `2`.

| Dimension | 0 | 1 | 2 |
| --- | --- | --- | --- |
| Source-of-truth mapping | Guesses or duplicates truth | Finds some surfaces | Maps owners and avoids duplication |
| Scope safety | Expands or overwrites scope | Mostly scoped | Preserves unrelated work and explicit boundaries |
| Mechanical validation | Gives prose only | Names partial checks | Produces runnable commands, modes, or schemas |
| Evidence quality | Makes unsupported claims | Records partial evidence | Links claims, commands, IDs, artifacts, and blockers |
| Artifact economy | Adds broad scaffolding | Adds some optional files | Reuses existing surfaces and adds only required roles |
| Routing economy | Loads irrelevant guidance | Minor over-trigger | Loads only the owning skill or no skill when appropriate |

Also record total input/output tokens, wall time, tool calls, invalid commands, and any critical failure.

## Retention Decision

Keep or add a standalone skill only when it meets at least one condition without a material regression elsewhere:

- improves its relevant score by at least 10 percent over `repo-only` across the scenario set;
- prevents a repeated critical scope, validation, privacy, or evidence failure;
- supplies a deterministic script, schema, or artifact contract the base model did not produce reliably.

Merge or remove a skill when its benefit is generic advice, its score is indistinguishable from `repo-only`, or a shared reference produces the same result with less routing and context cost.

## Result Record

```markdown
# Model Evaluation Result

- Date:
- Repository fixture and revision:
- Agent runtime and version:
- Model and effort:
- Condition: repo-only | compact-suite | candidate
- Scenario:
- Scores:
- Tokens / wall time / tool calls:
- Critical failures:
- Artifact paths:
- Notes:
```

Do not claim cross-model improvement until all compared conditions have complete result records.
