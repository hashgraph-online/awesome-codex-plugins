---
name: tdd
description: "Trigger: new feature or bug fix. Enforces Red→Green→Refactor. No prod code without failing test first."
---

# TDD — Test-Driven Development

## Iron Law

NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST. Violating the letter of this process is violating the spirit of this process.

## Process

### Red → Green → Refactor

1. **Red**: Write a failing test that describes the desired behavior
   - Test name should read like a spec: `it("returns 401 when token is expired")` (reason: the test name IS your specification — it must communicate intent to future readers)
   - Run the test — confirm it fails for the right reason (reason: a test that fails for the wrong reason gives false confidence)

2. **Green**: Write the minimum code to make the test pass
   - Do not write more than needed — because premature optimization is the root of all evil; make it work first
   - Do not optimize yet — because optimization without a passing test is speculation, not engineering
   - Run the test — confirm it passes (reason: a passing test is the only proof the code works)

3. **Refactor**: Clean up without changing behavior
   - Extract duplicates, rename for clarity, simplify — because readability matters more than cleverness
   - Run tests again — must still pass (reason: refactoring without re-running tests is just renaming bugs)

### Cycle
Repeat for each behavior. One test, one behavior, one cycle — because scope creep in a single test cycle leads to unverified code.

## When to Trigger
- `/go` subagents: always — because autonomous agents without TDD produce unverified code
- New function or method being written
- Bug fix (write regression test first — because a bug that happened once will happen again without a guard)

## Anti-Rationalization

| Excuse | Rebuttal | What to do instead |
|--------|----------|--------------------|
| "This is too simple for tests" | Simple code still breaks. The Beyonce Rule applies: if you liked it, you should have put a test on it. | Write the test anyway — it takes 30 seconds and catches edge cases. |
| "I'll write tests after" | That's documentation, not specification. Tests written after confirm what you built; tests written before define what you should build. | Write the test first. If you can't describe the behavior, you don't understand the requirement. |
| "Tests slow me down" | 15 minutes of TDD saves hours of debugging regression bugs later. | Time the cycle — Red-Green-Refactor is usually faster than debug-after-deploy. |
| "I'll just test manually" | Manual tests don't catch regressions. Automate it once, save hours forever. | Write an automated test that runs on every commit. |
| "The types guarantee correctness" | Types check shape, not logic. `add(a,b)` can still return `a-b`. | Write a test that verifies the actual business rule, not just the type signature. |
| "I need to see the API shape first" | Spike freely, then delete and rebuild test-first. A throwaway spike is research, not implementation. | Spike, discard, then TDD the real implementation from what you learned. |

## Evidence Required

Before claiming TDD is done, show ALL of these:

- [ ] Failing test output (Red phase): the test name and failure message
- [ ] Passing test output (Green phase): `✓` with the same test name
- [ ] Test covers behavior, not implementation (no mocking internals)
- [ ] Refactor step completed OR explicitly noted as unnecessary with reason

**No evidence = not done.** "I wrote tests" without showing output is not TDD.

## Red Flags
- Writing implementation before any test exists
- Test that tests implementation details instead of behavior
- Skipping the refactor step
- Multiple behaviors in one test
