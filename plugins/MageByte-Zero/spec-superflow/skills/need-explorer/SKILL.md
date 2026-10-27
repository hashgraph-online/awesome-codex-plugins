---
name: need-explorer
description: Clarify intent, scope, constraints, and success criteria before artifact creation. Invoke when the request is fuzzy, the user is comparing options, or the workflow needs a stable change definition before writing artifacts.
---

# Need Explorer

## Bundled runtime

Before executing a CLI line below, replace its leading `SSF` with `node "<plugin-root>/scripts/spec-superflow.mjs"`; `<plugin-root>` is the absolute directory two levels above this file. Never run `SSF` literally or call an `ssf` from `PATH`.

## Workflow routing

A new request follows this file without loading legacy instructions. For an existing change, inspect the recorded state and receipt/plan (available through `SSF workflow show <change-dir> --json` and `SSF execution show <dir> --json` when needed). Current paths are `workflow_variant: direct` with a valid workflow-selection receipt `schema_version: 3`, or `workflow_variant: planned` with an execution plan `schema_version: 2`. Older receipts (schema 1/2), legacy plans and other recorded variants use the matching section of `SSF runtime asset read docs/legacy-workflow.md`; follow that section for this change. A direct variant alone is insufficient: legacy Quick/Hotfix/Lightweight can also record it. The internal `workflow: full` value alone is not a legacy signal. Missing or corrupt state, receipt or a required plan is a recovery problem; preserve evidence rather than reinitialize or downgrade the change.

Turn a rough idea into a stable change definition before writing artifacts.

## Primary Goal

Agree on: problem, scope, non-goals, success criteria, whether to split before specification.

## Process

### 1. Inspect Context First

Before asking questions, understand what exists and what constraints are in place.

### 2. One Question at a Time

Ask a single clear question, wait for the answer, digest, then ask the next. Never ask 3+ questions at once. Each answer informs the next question.

### 3. Prefer Multiple-Choice Questions

Present 2-3 options when reasonable answers are finite. This reduces cognitive load and surfaces unconsidered choices.

### 4. Propose 2-3 Approaches with Trade-Offs

For each approach: what it is, upside, downside, best-for. Then **recommend one** and explain why. Never present a single path — always name at least one alternative.

### 5. Finish with a concrete scope

Summarize the problem, scope, non-goals, success criteria and decomposition decision for spec-writer. Reuse decisions already supplied by the user. Resolve missing material decisions, then hand off to spec-writer to draft proposal.md and tasks.md together; the concrete plan has one approval, handled by workflow-start. Exploration does not create a separate approval receipt.

## Completion

Leave a usable change name, problem statement, scope, non-goals, success criteria and decomposition decision. Self-check contradictions and placeholders. Do not implement code during exploration. On interruption, resume from existing decisions and the unanswered question.
