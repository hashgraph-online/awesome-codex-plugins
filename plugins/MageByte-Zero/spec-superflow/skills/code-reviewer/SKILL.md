---
name: code-reviewer
description: Review completed implementation batches for spec compliance and code quality. Invoke after execution batches complete, before merging, or when a review gate is reached in the workflow.
---

# Code Reviewer

## Bundled runtime

Before executing a CLI line below, replace its leading `SSF` with `node "<plugin-root>/scripts/spec-superflow.mjs"`; `<plugin-root>` is the absolute directory two levels above this file. Never run `SSF` literally or call an `ssf` from `PATH`.

Two responsibilities: reviewing the recorded Git range and acting on findings with technical rigor. Review according to the persisted policy; verify feedback before implementing it.

## Part 1: Requesting Review

**Mandatory**: one whole-range review for Native `final`; one review per planned wave for `wave` and legacy plans. Avoid redundant per-task or final reviews of unchanged evidence.
**Optional**: when stuck, before refactoring, after fixing complex bugs.

### Procedure
1. Get the review range from recorded execution evidence. For final review resolve the base in order: the recorded `state.review_base` start anchor, then the `review_base` in the recorded isolation context, then `git merge-base <target-branch> HEAD` for a legacy/manual branch with an unambiguous target; head is `git rev-parse HEAD`. The CLI verifies this complete range. A failed final review retains the same base across fixes; wave repairs use the prior wave head. For a wave review use the recorded wave-start base. Never substitute `HEAD~1`; it misses earlier commits in multi-commit work.
2. For Native `final`, the current executor reviews the complete diff locally and writes the report; do not dispatch a reviewer subagent. For user-authorized SDD with `wave` review, dispatch at most one reviewer for that wave using `skills/code-reviewer/code-reviewer-prompt.md`. If dispatch is unavailable, review locally.
3. When dispatching, fill only `[DESCRIPTION]`, `[PLAN_OR_REQUIREMENTS]`, `[BASE_SHA]`, `[HEAD_SHA]`, `[WAVE_ID]`, and `[REVIEW_REPORT_FILE]`. Do not send the whole planning bundle.
4. Write a non-empty report at `.superpowers/sdd/reviews/<wave-id>.md`, then record that path with `SSF execution review <change-dir> --wave <wave-id> --base <base-sha> --head <head-sha> --report .superpowers/sdd/reviews/<wave-id>.md --verdict <pass|fail>`.
For schema-2 plans, failed receipts also require `--issue <stable-finding-id>` for the blocking defect being repaired; reuse its ID across retries. Other findings keep their own IDs in the report. Identical failed input cannot consume another attempt.

5. Critical/Important findings require a `fail` receipt, focused repair, one focused re-review, and replacement `pass`. Note Minor for later.
6. At `adjudication-required`, wait for human authorization before another review.

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
Ask only about unclear findings that change a material decision; continue independent, already-understood repairs within scope. Do not turn an unclear optional comment into a global stop.

### Source-Specific Rules

**From user**: Trusted — implement after understanding. Still ask if scope unclear. No performative agreement.

**From external reviewer**: Before implementing, check: technically correct for this codebase? breaks existing functionality? reason for current implementation? works on all platforms? reviewer understands full context? If suggestion seems wrong, push back with technical reasoning.

### When to Push Back
Suggestion breaks existing functionality, reviewer lacks context, violates YAGNI, technically incorrect for this stack, legacy/compatibility reasons, conflicts with user's architectural decisions. Push back with technical reasoning, not defensiveness.

### Implementation Order
1. Clarify only the material uncertainty that blocks a repair
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
| Proceeding without a wave receipt | Record `pass`/`fail` via `SSF execution review` before the next dependent wave |
| Assuming reviewer is right | Check if breaks things |
| Avoiding pushback | Technical correctness > comfort |
| Unclear feedback | Clarify the blocked finding while continuing independent repairs |

## Exception Handling

- **Parse failures**: Report specific file, request regenerated review package
- **Missing files**: Regenerate via `scripts/review-package`. Empty diff = nothing to review
- **User interruption**: Re-read review report on resume, continue from next unreviewed batch
