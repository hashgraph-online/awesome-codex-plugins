---
name: code-reviewer
description: Review completed implementation batches for spec compliance and code quality. Invoke after execution batches complete, before merging, or when a review gate is reached in the workflow.
---

# Code Reviewer

Two responsibilities: requesting review (dispatching a reviewer subagent) and receiving review (acting on feedback with technical rigor). **Review early, review often. Verify before implementing feedback.**

## Part 1: Requesting Review

**Mandatory after**: each task in SDD, each planned execution wave, each major feature, before merge.
**Optional**: when stuck, before refactoring, after fixing complex bugs.

### Procedure
1. Get SHAs: `BASE_SHA=$(git rev-parse HEAD~1)` and `HEAD_SHA=$(git rev-parse HEAD)`
2. Dispatch `general-purpose` subagent using template at `skills/code-reviewer/code-reviewer-prompt.md`
3. Fill placeholders: `[DESCRIPTION]` (what was built), `[PLAN_OR_REQUIREMENTS]` (contract/spec reference), `[BASE_SHA]`, `[HEAD_SHA]`, `[WAVE_ID]`, and a distinct `[REVIEW_REPORT_FILE]`.
4. Require the reviewer to write a non-empty persisted review report at `[REVIEW_REPORT_FILE]`, then record that exact path in the wave receipt: `npx --yes --package spec-superflow@0.11.0 ssf execution review <change-dir> --wave <id> --base <sha> --head <sha> --report <review-report-path> --verdict <pass|fail>`.
5. Act on feedback: Critical/Important findings require a `fail` receipt, focused repair, re-review, and replacement `pass` receipt before a dependent wave or closing can proceed. Note Minor for later, push back with reasoning if reviewer is wrong.

### Minimality And Scope

For unrequested complexity, cite the missing task requirement and diff line.
Use Important for merge-blocking complexity and Minor for safe,
behavior-neutral redundancy; never score by line count.

## Part 2: Receiving Review Feedback

### The Response Pattern
1. READ feedback without reacting
2. UNDERSTAND and restate requirement
3. VERIFY against codebase reality
4. EVALUATE: technically sound for THIS codebase?
5. RESPOND: technical acknowledgment or reasoned pushback
6. IMPLEMENT: one item at a time, test each

### Severity Levels

| Level | Meaning | Action |
|-------|---------|--------|
| Critical | Bugs, security, data loss, broken functionality | Fix immediately |
| Important | Architecture problems, missing features, poor error handling, test gaps | Fix before next batch |
| Minor | Code style, optimization, documentation polish | Note for later |

### Forbidden Responses
Never: performative agreement ("You're right!", "Great point!"), blind implementation before verification, thanking the reviewer. Instead: restate the requirement, ask clarifying questions, push back with reasoning, or just fix it (actions > words).

### Handling Unclear Feedback
If any item is unclear → STOP. Do not implement anything yet. Ask for clarification on unclear items. Partial understanding = wrong implementation.

### Source-Specific Rules

**From user**: Trusted — implement after understanding. Still ask if scope unclear. No performative agreement.

**From external reviewer**: Before implementing, check: technically correct for this codebase? breaks existing functionality? reason for current implementation? works on all platforms? reviewer understands full context? If suggestion seems wrong, push back with technical reasoning.

### When to Push Back
Suggestion breaks existing functionality, reviewer lacks context, violates YAGNI, technically incorrect for this stack, legacy/compatibility reasons, conflicts with user's architectural decisions. Push back with technical reasoning, not defensiveness.

### Implementation Order
1. Clarify unclear items first
2. Fix blocking issues (breaks, security)
3. Fix simple issues (typos, imports)
4. Fix complex issues (refactoring, logic)
5. Test each fix individually, verify no regressions

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Performative agreement | State requirement or just act |
| Blind implementation | Verify against codebase first |
| Batch without testing | One at a time, test each |
| Proceeding without a wave receipt | Record `pass`/`fail` via `npx --yes --package spec-superflow@0.11.0 ssf execution review` before the next dependent wave |
| Assuming reviewer is right | Check if breaks things |
| Avoiding pushback | Technical correctness > comfort |
| Partial implementation | Clarify all items first |

## Exception Handling

- **Parse failures**: Report specific file, request regenerated review package
- **Missing files**: Regenerate via `scripts/review-package`. Empty diff = nothing to review
- **User interruption**: Re-read review report on resume, continue from next unreviewed batch
