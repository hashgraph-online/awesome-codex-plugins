---
name: repo-harness-assessment
description: Use when evaluating an existing repository's agent-readiness, harness maturity, validation surfaces, source-of-truth docs, evidence artifacts, or next smallest harness improvement.
---

# Repo Harness Assessment

## Overview

Assess how well a repository lets an agent understand rules, make safe changes, verify them, and produce reviewable evidence.

Use this skill to diagnose current harness maturity before proposing changes. For shared vocabulary and neutral artifact names, see `../../references/harness-patterns.md`; when expected harness files are missing, use `references/build-when-missing.md`.

## When To Use

- The user asks what harness pieces a repository is missing.
- You need to compare entrypoints, validation commands, runtime evidence, delivery records, or quality gates across repositories.
- You need to decide whether the next smallest improvement is an entrypoint, validation script, artifact bundle, ledger, contract check, or quality gate.

## Inputs Needed

- Repository root path.
- User scope: whole repository, one surface, docs-only work, runtime behavior, CI, or delivery flow.
- Any expected harness shape or maturity target the user names.

## Execution Order

- First: Read repository entrypoints and source-of-truth files, including `AGENTS.md`, README, architecture/reliability docs, indexes, CI, and scripts.
- Then: Check whether validation, evidence, collaboration records, task/design docs, and commit discipline have mechanical entrypoints.
- Finally: Report maturity, gaps, the smallest useful improvement slice, and what not to build yet.

## Step-by-Step Process

1. Use `rg --files` or `find` to list entrypoint files, docs, scripts, CI, and agent ledger locations.
2. Read the nearest agent instruction file and decide whether it is a high-signal navigation entrypoint rather than a project encyclopedia.
3. Search for `check_repo_harness`, `doctor`, `trace_run`, `quality`, `artifacts/runs`, `agent_chats`, and `tasks.md`.
4. Check for a stable validation matrix: docs, contracts, unit/type/lint, runtime, external-dependency, and CI.
5. Check whether failures can be traced through run IDs, request IDs, logs, screenshots, JSON/JUnit output, PRs, or commits.
6. If a layer is absent, define the minimum bootstrap artifact from `references/build-when-missing.md` before recommending broader work.
7. Compress gaps into no more than three next steps, ordered by value and risk.

## Checks

- File facts: entrypoint files exist and point to each other instead of duplicating drifting rules.
- Structure: there is a clear source of truth, directory boundary model, and no-new-drift rule.
- Validation: there is one local minimum command and one CI gate command.
- Evidence: a failure can be connected to logs, traces, screenshots, or runtime artifacts.
- Overbuild: do not recommend a full platform, broad scaffold, or cross-environment deployment system before the minimum slice is justified.

## Output Format

```markdown
# Repo Harness Assessment

## Detected Mapping
- entrypoint:
- work-state:
- ledger:
- validation:
- runtime-evidence:
- quality:

## Current State
- Agent entrypoint:
- Source-of-truth docs:
- Validation surface:
- Runtime evidence:
- Delivery/ledger:

## Gaps
1.
2.
3.

## Recommended Minimum Slice
- First:
- Then:
- Finally:

## Do Not Build Yet
-

## Validation Needed
-
```

## Common Mistakes

- Reducing harness maturity to "there are tests."
- Reading only README while ignoring scripts, CI, and real artifacts.
- Copying environment variables, ports, accounts, or private workflow details from one implementation into another.
- Producing a long wish list instead of a small, implementable improvement slice.

## Example Prompts

- "Assess what harness pieces this repository is missing."
- "Compare this repository against a mature run-artifact pattern."
- "Can an agent safely take over this project as it stands?"
