---
name: systematic-debugging
description: Use when encountering any bug, test failure, or unexpected behavior. Enforces root-cause investigation before fixes. The Iron Law — no fixes without understanding why.
---

# Systematic Debugging

## The Iron Law

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

Quick patches mask underlying issues. Systematic debugging is FASTER than thrashing.

## The Four Phases (Must Complete in Order)

### Phase 1: Root Cause Investigation (MANDATORY)

1. **Read Error Messages Carefully** — full stack traces, exact line numbers
2. **Reproduce Consistently** — if not reproducible, gather more data before proceeding
3. **Check Recent Changes** — git diff, recent commits, new dependencies
4. **Gather Evidence (Multi-Component Systems)**
   ```
   For EACH component boundary:
   - Log what data enters the component
   - Log what data exits the component
   - Verify environment/config propagation
   Run once to gather evidence showing WHERE it breaks
   ```
5. **Trace Data Flow** — where does the bad value originate? trace backward

### Phase 2: Pattern Analysis

1. Find working examples of similar code in the same codebase
2. Read reference implementations **completely** — don't skim
3. List every difference between working and broken
4. Understand all dependencies and assumptions

### Phase 3: Hypothesis and Testing

1. Form **one** specific hypothesis: "I think X is the root cause because Y"
2. Make the **smallest** possible change to test it
3. One variable at a time — never multiple changes simultaneously
4. Verify: works → Phase 4; doesn't work → form NEW hypothesis

### Phase 4: Implementation

1. Write a failing test case that reproduces the bug (before fixing)
2. Implement the single fix addressing the root cause
3. Verify: test passes, no other tests broken, issue resolved
4. **If 3+ fixes failed** → STOP. Question the architecture.

## When 3+ Fixes Fail

This is an architectural problem, not a surface bug:
- Each fix reveals new coupling/shared state elsewhere
- Fixes require "massive refactoring" to implement
- **Stop and discuss with the human before attempting more fixes**

## Red Flags — Return to Phase 1

- "Quick fix for now, investigate later"
- "Just try changing X and see if it works"
- "I don't fully understand but this might work"
- "One more fix attempt" (after already trying 2+)
- Proposing solutions before tracing data flow

## Real-World Impact

- Systematic: 15-30 minutes to fix, 95% first-time fix rate
- Random fixes: 2-3 hours of thrashing, 40% first-time fix rate
