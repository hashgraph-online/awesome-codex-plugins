---
name: debugging
description: "Use when fixing bugs, investigating errors, debugging failures, or diagnosing unexpected behavior."
user-invocable: true
allowed-tools: Glob, Grep, Read, Bash, Task, Skill, Edit, Write, AskUserQuestion
---

# Systematic Debugging

Apply [Iron Rules](../../shared/iron-rules.md) — Principle 0 (be critical, don't pander to a wrong hypothesis), Principle 8 (no claim without fresh evidence — every hypothesis tested), Principle 9 (root cause, not symptoms), and the meta-rule (spirit beats letter — *"I'll add logging"* is not investigation) govern every step.

## THE IRON LAW

**NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST.**

Random fixes waste time and create new bugs. Systematic debugging fixes correctly on the first attempt 95% of the time.

---

## Phase 0: ESTABLISH BASELINE

**Run existing test suite first.** Record pass/fail counts. Pre-existing failures are NOT your regressions.

## Phase 1: ROOT CAUSE INVESTIGATION

1. **Read error messages completely** — every line, every stack frame
2. **Reproduce consistently** — exact steps, every time
3. **Check recent changes** — `git diff`, `git log`, new deps, config
4. **Trace data flow backward** — from error to source through call stack
5. **Gather evidence at boundaries** — log at each component boundary

## Phase 2: PATTERN ANALYSIS

1. **Find working examples** — similar code in this codebase that works
2. **Compare completely** — diff against reference implementation
3. **Identify ALL differences**
4. **Understand dependencies** — what assumptions does the working code make?

## Phase 3: HYPOTHESIS & TEST

1. **Form ONE hypothesis:** "X is root cause because Y"
2. **Test minimally** — change one variable at a time
3. **Verify** — does evidence support it?
4. **If wrong:** New hypothesis based on what you learned. No guess-and-check.

## Phase 4: IMPLEMENT FIX

1. **Write failing test** reproducing the bug
2. **Implement single fix** for root cause
3. **Run all tests** — fix works AND nothing else broke
4. **If 3+ attempts failed:** STOP. Question the architecture, not symptoms.

---

## Red Flags — return to Phase 1:

- "Quick fix for now, investigate later"
- "Just try changing X and see"
- "Skip the test, I'll manually verify"
- "It's probably X, let me fix that"
- "One more fix attempt" (after 2+ failed)
- Each fix reveals a new problem elsewhere

## Anti-Rationalization

| Your thought | Reality |
|---|---|
| "I know what's wrong" | If you knew, you wouldn't be debugging. Investigate. |
| "Simple bug" | Simple bugs have simple root causes. Find it first. |
| "Obvious from the error" | Errors describe symptoms, not causes. Trace the data. |
| "I'll add more logging" | That's Step 5 of Phase 1. Do Steps 1-4 first. |

## Integration with Development Workflow

Enhances Phase 1 (Research + Plan) for debugging tasks. After root cause found, continue with the locked plan into Phase 2 (Chronicle) and remaining phases normally.

Standalone (`/debugging`): announce root cause and proposed fix, ask if user wants to proceed with dev workflow.

**Language context:** If a language skill is active, read its `patterns.md` during Phase 1 for team-specific patterns.
