---
name: five-whys
description: Root cause analysis using the Five Whys technique. Use when a bug persists despite surface fixes, a failure recurs, or a process keeps breaking. Ensures the fix targets the root, not the symptom.
---

# Five Whys — Root Cause Analysis

## The Rule

```
DO NOT FIX THE SYMPTOM. FIND THE CAUSE.
```

A fix that doesn't address the root cause is temporary. The cause returns.

## Protocol

### Step 1 — Define the problem precisely

One concrete sentence. Not vague.

| Wrong | Correct |
|-------|---------|
| "The system is slow" | "GET /orders exceeds 3s for 90% of requests in prod since Friday" |
| "Tests fail sometimes" | "test_payment_flow fails in CI roughly 1 in 20 runs with no clear error message" |

### Step 2 — Five Whys cascade

For each answer, ask: **"Why does that happen?"**

Don't stop until you reach something you control — a decision, a process, a line of code, a missing configuration.

```
Problem: Users see another user's data
  Why 1: Cache returns the wrong entry
  Why 2: Cache key does not include user_id
  Why 3: Developer assumed the endpoint was public
  Why 4: No isolation test existed for this endpoint
  Why 5: Code review had no data isolation checklist
  → Root cause: review process missing a security checklist
```

### Step 3 — Validate in reverse

Read the chain bottom-up: "No review checklist → cache key missing user_id → data leak." If the chain holds, the root cause is valid.

### Step 4 — Fix at the root, not the symptom

Fix at the deepest level that is practical to change.

| Fix level | Example | Durability |
|-----------|---------|------------|
| Symptom | Manually flush cache | Hours |
| Proximate cause | Add user_id to cache key | Days |
| Root cause | Add isolation checklist to review | Permanent |

If you can only fix an intermediate level, document the root cause as tracked technical debt with a concrete TODO.

## Branching

A root cause can have multiple branches — explore all before choosing where to fix.

```
Problem: Deploy fails in prod but not in staging
  Branch A: different configuration (env vars, secrets)
  Branch B: prod data has different volume or format
  Branch C: network dependencies only reachable in prod
```

Test each branch independently. Do not assume.

## When to Stop

Stop before the 5th why if you reach a clear, actionable root cause. Stop after the 5th if the chain hasn't converged — there may be multiple independent root causes.

## Output

Document the analysis:

```markdown
**Problem:** [concrete one-liner]
**Root cause:** [deepest level found]
**Fix:** [concrete action with file/component]
**Temporary fix (if needed):** [what you apply now while the real fix is in progress]
**Technical debt:** [what remains unresolved and why]
```

## Integration with A Team

- Run this skill **before** launching the `systematic-debugging` agent — Five Whys defines the investigation scope
- After finding the root cause, use the `tdd-guide` agent to write the test that would have caught it
- If the root cause implies a process change, document the analysis in `DAILY.md`
