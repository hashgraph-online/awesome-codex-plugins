---
name: bug-investigator
description: Use when encountering any bug, test failure, or unexpected behavior during spec-superflow execution, before proposing fixes. Invoked automatically when build-executor hits a blockage.
---

# Bug Investigator

## Bundled runtime

Before executing a CLI line below, replace its leading `SSF` with `node "<plugin-root>/scripts/spec-superflow.mjs"`; `<plugin-root>` is the absolute directory two levels above this file. Never run `SSF` literally or call an `ssf` from `PATH`.

## Workflow routing

A new request follows this file without loading legacy instructions. For an existing change, inspect the recorded state and receipt/plan (available through `SSF workflow show <change-dir> --json` and `SSF execution show <dir> --json` when needed). Current paths are `workflow_variant: direct` with a valid workflow-selection receipt `schema_version: 3`, or `workflow_variant: planned` with an execution plan `schema_version: 2`. Older receipts (schema 1/2), legacy plans and other recorded variants use the matching section of `SSF runtime asset read docs/legacy-workflow.md`; follow that section for this change. A direct variant alone is insufficient: legacy Quick/Hotfix/Lightweight can also record it. The internal `workflow: full` value alone is not a legacy signal. Missing or corrupt state, receipt or a required plan is a recovery problem; preserve evidence rather than reinitialize or downgrade the change.

**Core principle:** Find root cause before attempting fixes. Symptom fixes are failure.

## New direct/planned changes

Investigate in executing without a phase transition or a separate debug ledger: reproduce, trace the root cause, make one focused repair and verify. Keep useful failure evidence in the existing progress entry. Three failures for the same unresolved issue warrant a decision; unrelated findings do not accumulate a shared budget. No task book or subagent is required.

## The Iron Law

No fixes without root cause investigation first. If you haven't completed Phase 1, you cannot propose fixes.

## When to Use

Use for ANY technical issue: test failures, bugs, unexpected behavior, performance problems, build failures, integration issues. Especially when under time pressure, "one quick fix" seems obvious, you've already tried multiple fixes, or you don't fully understand the issue.

Don't skip because issue "seems simple" or you're "in a hurry" — systematic debugging is faster than thrashing.

## The Four Phases

Complete each phase before proceeding.

### Phase 1: Root Cause Investigation

1. **Read error messages carefully**: stack traces, line numbers, file paths, error codes — they often contain the exact solution
2. **Reproduce consistently**: exact steps, every time? If not reproducible → gather more data, don't guess
3. **Check recent changes**: git diff, recent commits, new dependencies, config changes, environment differences
4. **Multi-component systems**: add diagnostic instrumentation at each component boundary. Log what enters and exits each layer. Run once to gather evidence, then analyze which component fails
5. **Trace data flow**: backward tracing — where does the bad value originate? Keep tracing up until you find the source. Fix at source, not symptom

### Phase 2: Pattern Analysis

1. Find working examples of similar code in the same codebase
2. Compare against references — read reference implementation completely
3. Identify every difference between working and broken, however small
4. Understand dependencies: other components, settings, config, environment, assumptions

### Phase 3: Hypothesis and Testing

Scientific method: form a single hypothesis ("I think X is the root cause because Y"), test with the smallest possible change (one variable at a time), verify before continuing. If it didn't work, form a NEW hypothesis — don't add more fixes. When you don't know, say so and ask for help.

### Phase 4: Implementation

1. **Create failing test case** — simplest reproduction, automated if possible. Follow TDD rules from build-executor
2. **Implement single fix** — address root cause, one change at a time, no "while I'm here" improvements
3. **Verify fix** — test passes? no regressions? issue resolved?
4. **If the fix fails**: preserve the evidence, return to Phase 1 and form a new hypothesis. Repeated failures of the same unresolved issue require a concrete decision; unrelated issues do not share an attempt budget.

## Completion

Verify the regression and affected checks, record the outcome in the existing progress entry, then return to build-executor in executing. If evidence points to an environmental or external cause, state what is known and what remains unverified. Resume from that evidence after interruption.
