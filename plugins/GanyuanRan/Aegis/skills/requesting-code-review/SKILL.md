---
name: requesting-code-review
description: Use when explicitly requesting an independent code review, after subagent-driven implementation slices, before merging high-risk work, or when verification finds evidence, baseline, architecture, compatibility, or retirement uncertainty that needs reviewer scrutiny.
---

# Requesting Code Review

Dispatch aegis:code-reviewer subagent to catch issues before they cascade. The reviewer gets precisely crafted context for evaluation — never your session's history. This keeps the reviewer focused on the work product, not your thought process, and preserves your own context for continued work.

This skill is the canonical review-request workflow for method-pack implementation work. Use it to request review only after you have enough evidence, enough context, and a clear authority boundary for what the reviewer is being asked to assess.

**Core principle:** Review early, review often.

## When to Request Review

**Mandatory:**
- After each task in subagent-driven development
- After completing major feature
- Before merge to main

**Optional but valuable:**
- When stuck (fresh perspective)
- Before refactoring (baseline check)
- After fixing complex bug

## Required Outputs

Before you leave this workflow, you must be able to state:

1. **What exact scope is being reviewed**
2. **What plan, requirement, or contract defines success**
3. **What baseline / current authority refs define the expected architecture state**
4. **What fresh evidence already exists**
5. **What compatibility boundary must still hold**
6. **What old owner / fallback / patch stays, shrinks, or retires**
7. **What the reviewer must specifically validate**
8. **Whether the reviewer is providing advisory review only, or also any higher-level merge recommendation**

Review in this method pack is advisory and evidence-oriented. It is not authoritative completion by itself.

## How to Request

**1. Gather minimum review inputs:**

- What was implemented
- What requirement / plan / spec / ADR it should match
- What baseline / current authority docs the diff must align with
- What evidence already exists (tests, commands, logs, screenshots, diff summary)
- What compatibility boundary or risk deserves reviewer attention
- Whether there is any old path, fallback, duplicate owner, or temporary patch that should retire
- Whether the diff contains durable architecture decisions that need ADR
  Auto Backfill or baseline sync findings

If you cannot answer these, stop and gather them before dispatching review.

**2. Get git SHAs:**
```bash
BASE_SHA=$(git rev-parse HEAD~1)  # or origin/main
HEAD_SHA=$(git rev-parse HEAD)
```

**3. Dispatch code-reviewer subagent:**

Use Task tool with aegis:code-reviewer type, fill template at `code-reviewer.md`

**Placeholders:**
- `{WHAT_WAS_IMPLEMENTED}` - What you just built
- `{PLAN_OR_REQUIREMENTS}` - What it should do
- `{EVIDENCE}` - Fresh tests, commands, logs, or verification already available
- `{COMPATIBILITY_BOUNDARY}` - What existing behavior or interfaces must not break
- `{RETIREMENT_NOTES}` - Old owner / fallback / patch / duplicate branch and expected disposition
- `{BASE_SHA}` - Starting commit
- `{HEAD_SHA}` - Ending commit
- `{DESCRIPTION}` - Brief summary

**4. Act on feedback:**
- Fix Critical issues immediately
- Fix Important issues before proceeding
- Note Minor issues for later
- Push back if reviewer is wrong (with reasoning)
- If feedback reveals evidence gaps, run the missing verification instead of arguing from confidence
- If feedback reveals architecture drift or stale logic, decide explicitly whether to repair now or record retirement conditions

## Example

```
[Just completed Task 2: Add verification function]

You: Let me request code review before proceeding.

BASE_SHA=$(git log --oneline | grep "Task 1" | head -1 | awk '{print $1}')
HEAD_SHA=$(git rev-parse HEAD)

[Dispatch aegis:code-reviewer subagent]
  WHAT_WAS_IMPLEMENTED: Verification and repair functions for conversation index
  PLAN_OR_REQUIREMENTS: Task 2 from docs/aegis/plans/deployment-plan.md
  EVIDENCE: pytest tests/index/test_verify.py -v -> 12 passed
  COMPATIBILITY_BOUNDARY: Existing index format and CLI flags must remain stable
  RETIREMENT_NOTES: Legacy repair fallback still exists in old helper; remove once new path covers all four issue types
  BASE_SHA: a7981ec
  HEAD_SHA: 3df7661
  DESCRIPTION: Added verifyIndex() and repairIndex() with 4 issue types

[Subagent returns]:
  Strengths: Clean architecture, real tests
  Issues:
    Important: Missing progress indicators
    Minor: Magic number (100) for reporting interval
  Assessment: Ready to proceed

You: [Fix progress indicators]
[Continue to Task 3]
```

## Integration with Workflows

**Subagent-Driven Development:**
- Review after EACH task
- Catch issues before they compound
- Fix before moving to next task

**Executing Plans:**
- Review after each batch (3 tasks)
- Get feedback, apply, continue

**Ad-Hoc Development:**
- Review before merge
- Review when stuck

## What the Reviewer Must Check

The review request must prompt the reviewer to inspect at least:

- evidence sufficiency
- baseline / current authority alignment
- baseline defect vs architecture drift distinction
- architecture drift or owner duplication
- compatibility boundary
- missing ADR Auto Backfill or baseline sync findings for durable architecture
  decisions
- unverified claims or missing proof
- old logic that should retire, stay temporarily, or converge

If the review only asks “is this code good?”, it is underspecified.

## Red Flags

**Never:**
- Skip review because "it's simple"
- Ignore Critical issues
- Proceed with unfixed Important issues
- Argue with valid technical feedback
- Treat reviewer approval as equivalent to authoritative completion
- Ask for review without sharing what evidence already exists
- Add new logic without telling the reviewer what happens to the old path

**If reviewer wrong:**
- Push back with technical reasoning
- Show code/tests that prove it works
- Request clarification

## Review Boundaries

- Review can recommend merge readiness, residual risk, and follow-up work
- Review cannot grant authoritative completion by itself
- Review should reduce uncertainty, not hide it

See template at: requesting-code-review/code-reviewer.md
