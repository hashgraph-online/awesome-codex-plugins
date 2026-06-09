---
name: validation-harness-design
description: Use when designing repository validation commands, doctor scripts, test matrices, JSON or JUnit outputs, CI gates, smoke checks, or harness command surfaces.
---

# Validation Harness Design

## Overview

Define the smallest repeatable command surface that proves repository changes are safe enough for review.

This skill turns scattered checks into commands agents can run, CI can reuse, and failures can diagnose. For shared harness terms, see `../../references/harness-patterns.md`; when validation commands are absent, use `references/build-when-missing.md`. For setup probes and CI-safe fallbacks, see `references/environment-bootstrap.md`.

## When To Use

- The user wants `check_repo_harness.py`, `doctor.py`, a test matrix, or CI gates.
- Existing validation commands are scattered and agents do not know what to run for docs-only, interface, service, logic, or runtime changes.
- JSON, JUnit, or artifact output is needed.

## Inputs Needed

- Project shape, main surfaces, existing test commands, and CI configuration.
- Change types and the minimum gate for each type.
- Whether runtime, packaged-environment, external-dependency, or manual checks are needed.

## Execution Order

- First: Inventory existing commands and CI to confirm what already works.
- Then: Design a layered validation matrix and unified entrypoint.
- Finally: Output the command table, report formats, CI wiring, and fallback rules.

## Step-by-Step Process

1. Search `package.json`, Makefile, scripts, CI workflows, test directories, and docs.
2. Split validation into repo/docs, contracts, unit/type/lint, runtime, and external-dependency layers.
3. If there is no shared validation entrypoint, bootstrap the minimum command surface from `references/build-when-missing.md`.
4. For each change type, choose the minimum command and escalation condition.
5. Design a unified entrypoint: `check_repo_harness` or `doctor` handles environment/structure, while focused commands test behavior.
6. Design report output: stdout for humans, JSON/JUnit for CI and artifacts.
7. Require skip/fallback reasons; do not describe degraded validation as full validation.

## Checks

- Runnable: commands work in a clean checkout or documented setup.
- Layered: docs-only work does not require heavy runtime checks, and runtime changes do not stop at static checks.
- Output: failures identify case, path, command, and artifact.
- CI: local commands and CI logic are consistent.
- Cost: minimum gates are fast, and heavy gates trigger only on higher-risk changes.

## Output Format

```markdown
# Validation Harness Design

## Detected Mapping
- validation:
- runtime-evidence:
- CI:

## Change-Type Matrix
| Change type | Minimum check | Escalation |
| --- | --- | --- |

## Command Surface
-

## Report Outputs
-

## CI Gates
-

## Fallback / Skip Policy
-
```

## Common Mistakes

- Requiring the heaviest end-to-end check for every change, which causes agents to skip validation.
- Providing only a command list without a change-type matrix.
- Emitting unstable JSON/JUnit output that cannot be aggregated later.
- Omitting fallback records, then claiming a degraded path was full runtime validation.

## Example Prompts

- "Design a check_repo_harness.py command surface for this repo."
- "Design validation commands for docs-only, interface, service, logic, and runtime changes."
- "Organize these tests into a CI gate and test matrix."
