---
name: repo-harness-assessment
description: Use when evaluating repository agent-readiness, mapping harness roles, choosing the next smallest improvement, or designing and reconciling agent entrypoints such as AGENTS.md, CLAUDE.md, GEMINI.md, Cursor rules, or GitHub instructions.
---

# Repo Harness Assessment

## Overview

Assess how well a repository lets an agent find its rules, make safe changes, verify them, and produce reviewable evidence.

This is the default router for existing repositories. It also owns agent-entrypoint design because entrypoints are the navigation layer of the assessment, not a separate harness system. For shared vocabulary and neutral artifact names, see `../../references/harness-patterns.md`; when expected harness files are missing, use `references/build-when-missing.md`; for canonical entrypoints, mirrors, and drift prevention, use `references/entrypoint-policy.md`.

## When To Use

- The user asks what harness pieces a repository is missing.
- The user wants to create, shrink, reconcile, or diagnose `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, Cursor rules, or GitHub instructions.
- You need to compare entrypoints, validation commands, runtime evidence, delivery records, or quality gates across repositories.
- You need to decide whether the next smallest improvement is an entrypoint, validation script, artifact bundle, ledger, contract check, or quality gate.

## Inputs Needed

- Repository root path.
- User scope: whole repository, one surface, docs-only work, runtime behavior, CI, or delivery flow.
- Any expected harness shape or maturity target the user names.
- Existing agent instruction files and whether mirrors, generation, or subtree overrides are required.

## Execution Order

- First: Read repository entrypoints and source-of-truth files, including agent instructions, README, architecture or reliability docs, indexes, CI, and scripts.
- Then: Map existing surfaces to harness roles and check entrypoint precedence, mirrors, validation, evidence, work state, delivery, contracts, and quality.
- Finally: Report maturity, entrypoint actions, the smallest useful improvement slice, and what not to build yet.

## Step-by-Step Process

1. Use `rg --files` or `find` to list agent instruction files, docs, scripts, CI, work-state surfaces, ledgers, reports, and runtime artifacts.
2. Identify one canonical entrypoint and classify every other agent instruction file as a subtree override, symlink, generated mirror, or short pointer.
3. Keep the root entrypoint to scope, source-of-truth navigation, hard boundaries, and minimum commands; move detailed procedures to linked docs.
4. Map current artifacts to entrypoint, work-state, ledger, contracts, validation, runtime-evidence, and quality roles before proposing new files.
5. Check for a stable validation matrix and whether failures connect to run IDs, request IDs, logs, screenshots, JSON/JUnit output, reviews, or commits.
6. If a required role is absent, define the minimum bootstrap artifact from `references/build-when-missing.md`; do not scaffold optional roles by default.
7. Add a mirror or pointer drift check when multiple agent instruction surfaces must stay aligned.
8. Compress gaps into no more than three next steps, ordered by value and risk.

## Checks

- Entrypoint: an agent can find first-read docs, edit boundaries, and the minimum validation command within one minute.
- Consistency: mirrors cannot silently drift, and instruction precedence is explicit.
- Structure: there is a clear source of truth, directory boundary model, and no-new-drift rule.
- Validation: there is one local minimum command and one CI gate command.
- Evidence: a failure can be connected to logs, traces, screenshots, or runtime artifacts.
- Overbuild: do not recommend a full platform, broad scaffold, or cross-environment deployment system before the minimum slice is justified.

## Output Format

```markdown
# Repo Harness Assessment

## Detected Mapping
- entrypoint:
- mirrors / subtree overrides:
- work-state:
- ledger:
- contracts:
- validation:
- runtime-evidence:
- quality:

## Entrypoint Decision
- canonical file:
- navigation changes:
- drift prevention:

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
- Copying rules into every agent-specific file instead of choosing one canonical source.
- Turning the root entrypoint into a project encyclopedia.
- Copying environment variables, ports, accounts, or private workflow details from one implementation into another.
- Producing a long wish list instead of a small, implementable improvement slice.

## Example Prompts

- "Assess what harness pieces this repository is missing."
- "Reconcile AGENTS.md, CLAUDE.md, and GEMINI.md without duplicating rules."
- "Compare this repository against a mature run-artifact pattern."
- "Can an agent safely take over this project as it stands?"
