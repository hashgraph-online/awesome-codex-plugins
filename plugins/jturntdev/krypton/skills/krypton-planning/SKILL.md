---
name: krypton-planning
description: Use when a user has a feature request, bugfix, refactor, migration, architecture change, or product goal and needs an implementation plan before coding. Use especially when wrong ownership, duplicate paths, stale contracts, weak evidence, or unclear cutover would make plausible agent work dangerous.
---

# Krypton Planning

Krypton Planning turns a request into a goal package that names the outcome, truth owner, contract, cutover, and acceptance evidence before anyone writes code.

## Core Rule

Do not treat a task list as a plan. A Krypton plan is ready only when it answers:

```text
What outcome are we serving?
What current behavior is being replaced, redirected, deleted, or demoted?
Who owns the truth?
What contract crosses the boundary?
What is the smallest high-value slice?
What proves the result from the target person's perspective?
What kill criteria stop duplicate paths from living forever?
```

If ownership, cutover, contract, or evidence is fuzzy, stop and map before planning.

## Workflow

1. Write the outcome contract:

```text
Plan title:
Intent:
Current behavior:
Expected outcome:
Target-perspective output:
Truth owner:
Contract boundary:
Cutover:
Displaced path:
Value density:
Evidence gate:
Acceptance evidence:
Evidence lane:
Kill criteria:
Non-goals:
Risk if wrong:
```

2. Map the architecture slice before tasks:

```text
Files to create:
Files to modify:
Files to avoid:
Source of truth:
Read path:
Write path:
Contract boundary:
Integration points:
Migration/cutover:
Displaced path:
Acceptance evidence gate:
```

For broad or unclear repositories, dispatch a read-only explorer if the harness supports agents. Ask one bounded question, such as "map the source of truth, read/write path, unsafe files, and evidence gate." The execution session should use this map instead of rediscovering the same slice.

3. Save a goal package unless the user gives another location:

```text
docs/goals/<goal-slug>/PLAN.md
docs/goals/<goal-slug>/GOAL.md
docs/goals/<goal-slug>/EVIDENCE.md
```

`PLAN.md` contains the full plan. `GOAL.md` is a short execution prompt that points to the plan instead of copying it. `EVIDENCE.md` starts empty and is filled during execution with the real proof captured from the target perspective.

4. Start `PLAN.md` with this header shape:

```markdown
# [Outcome Title] Implementation Plan

**Intent:** ...
**Current Behavior:** ...
**Expected Outcome:** ...
**Target-Perspective Output:** ...
**Truth Owner:** ...
**Contract Boundary:** ...
**Cutover:** ...
**Displaced Path:** ...
**Value Density:** ...
**Evidence Gate:** ...
**Acceptance Evidence:** ...
**Evidence Lane:** ...
**Kill Criteria:** ...
**Architecture Slice:** ...
**Plan Review Gate:** Requires PRE review before execution.
```

5. Break work into small tasks. Each task names exact files, allowed scope, expected output, verification command, acceptance evidence, and whether it can run in parallel.

6. Run a PRE plan review when possible. Use `plan-reviewer-prompt.md` as the individual prompt template. Do not execute until blocker findings are fixed or explicitly accepted by the user.

## GOAL.md Shape

Use this compact handoff. This is the `/goal` prompt or next-session prompt the operator should paste into Codex or Claude:

```markdown
# Goal: [Outcome Title]

Use Krypton Execution to execute `docs/goals/<goal-slug>/PLAN.md`.

Core rules:
- Treat PLAN.md as the source plan.
- Preserve intent, ownership, contract, cutover, evidence, and kill criteria.
- Do not add a new dominant path without deleting, redirecting, demoting, or shimming the displaced path.
- Capture acceptance evidence from the target perspective and record it in EVIDENCE.md.
- Say "implemented but unproven" if that evidence cannot be captured.
```

## EVIDENCE.md Shape

Create this file with the goal package and update it during execution:

```markdown
# [Outcome Title] Evidence

## Acceptance Evidence

Record the real artifact that proves the outcome from the target perspective.

## Verification

Record the focused check that passed, including the command and relevant output.

## Review Notes

Record reviewer, maintainer, or verifier findings that changed the result.
```
