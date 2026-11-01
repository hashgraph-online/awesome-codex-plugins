---
name: refactor-loop
description: "Autonomous /goal loop that refactors a project on every axis without changing its behavior. Start it only when the user names refactor-loop."
argument-hint: "[focus] [branch=...] [limits]"
user-invocable: true
disable-model-invocation: true
---

# Refactor loop

Improve this project on every axis: structure, data model, queries, performance, readability, tests, and docs.
Behavior must stay identical: same outputs, side effects, contracts, and functional logs. Zero regressions. The only exception is a fix for a real bug.
The arguments of the request can set a focus, a branch, or extra limits.

Invoking this skill approves the work below within the [unattended-run limits](../../shared/unattended-runs.md).
Work on a new branch, `refactor/loop-YYYY-MM-DD`, unless the arguments name one. When data matters, use representative dev or staging data.
Keep every external contract: API schemas and fields, CLI output, event and file formats, shared database schemas, config names, and logs that alerts read. Internal names can change.

Fix real bugs and harmful side effects when the evidence proves them. Record each fix with before and after, and demonstrate the correction against the baseline.
When you are not sure it is a bug, record the question with your recommendation and continue independent work.

## Verification first

Before refactoring, agree with the user on the [definition of done](../create-test/SKILL.md#definition-of-done) and a proven [regression gate](../create-test/SKILL.md#regression-gate), as an [autonomous run](../create-test/SKILL.md#autonomous-work) requires.
Start from what the project already has to check regressions. Use `brainstorming` and `create-test` for what is missing.

## Work

Audit from first principles, and challenge the project's patterns and your own assumptions.
Look first at queries and I/O in loops, unnecessary libraries, data models, complexity, blocking work, dead code, bad names, and inaccurate docs.
Back every finding with evidence from the code, real data, logs, or measurements, and check library behavior in the official docs for the installed version.

Rank the backlog by impact. Use `rethink` to challenge the ranking and design choices.
Work in small, verifiable changes, preserving the reasons for non-obvious behavior and useful discoveries in the task records.
Report the result, bugs fixed, verification, and remaining questions against the agreed definition of done.

## Done

The loop is done when, on its last commit:

1. The gate exits 0, and its only differences from the baseline are the recorded bug fixes.
2. The independent review of the whole branch has no open CRITICAL or HIGH finding.
3. A final audit in a fresh context finds no new item of MEDIUM severity or higher, and no backlog item is open.
4. Docs and task records are current, and `git status` is clean.
