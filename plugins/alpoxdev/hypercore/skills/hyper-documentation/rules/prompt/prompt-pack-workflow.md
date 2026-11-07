# Prompt Pack Workflow

**Purpose**: Order the draft, refactor, and version decisions for a prompt artifact. **Read when**: producing or revising one.

## Draft

1. Confirm the prompt will be reused.
2. Identify the operator, target model or agent, task class, and side-effect boundary.
3. Fill the prompt contract before polishing prose.
4. Declare which rules are binding and which are advisory defaults, and where untrusted material enters as data.
5. Add variables and context packet slots before adding examples.
6. Define output schema before writing style guidance. Express the shape in instructions, an example, or a schema, never in a prefilled assistant turn.
7. Keep the contract in the stable prefix and put the date, the current task, and per-turn values in a tail appended last.
8. Add eval cases before optimization claims, each with its own run count and aggregation rule.

## Refactor

1. Preserve current observable behavior unless the user requested a behavior change.
2. Split authority, scope, evidence, and output requirements into separate sections.
3. Delete duplicate or decorative wording.
4. Replace vague quality words with success criteria and verification checks.
5. Move volatile values out of the stable prefix into the tail, and keep one home per rule.
6. Add a version note that states what changed and why.

## Optimize

Record a baseline case, diagnose failures, patch the smallest instruction surface, rerun the same cases with the same judge, and keep only changes that improve the target behavior without breaking safety, source, schema, or guard coverage. Record the model and runtime version, the run count, the grader version, and the cost delta with the result. The candidate may not edit the cases, the judge, the metric, or the guards; shrinking guard coverage while the score rises is a tampering signal.

## Version Note

A version note carries the version, what changed, why, the run count and aggregation used, the grader version, the known remaining risk, and the cost delta when the change touches prompt length or tool surface.

## Sources

> Checked 2026-11-03 against the repository instruction base.

| Claim | Source | Checked |
|---|---|---|
| Draft order, prompt improvement loop, and the version note | `instructions/context-engineering/references/prompt-authoring.md` | 2026-11-03 |
| Stable prefix, volatile tail, and cache boundary placement | `instructions/cache/CACHE.md` | 2026-11-03 |
| Baseline, same-runner rerun, and guard integrity | `instructions/harness-engineering/HARNESS_ENGINEERING.md`, `instructions/autoresearch/references/core-loop.md` | 2026-11-03 |

No external URL is cited in this file; every rule is a restatement of the repository base above.
