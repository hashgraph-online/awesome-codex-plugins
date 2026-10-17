
<skill id="testing">

<on_start>
agentdb read-start, past test failures repeat. Detect the framework in use
(check package.json / pyproject) and read 2-3 existing test files for conventions
before writing any. Reference on demand: skills/build/reference/testing-research.md.
</on_start>

## Core Laws

1. TESTS BEFORE CODE. Write the test from the requirement, watch it fail red, then
   implement the minimal code to go green, then refactor while green. Tests written
   after code validate whatever the code already does, bugs included.
2. TEST BEHAVIOR, NOT IMPLEMENTATION. Refactoring must not break tests. Mocking
   internals couples the test to structure and makes it lie.
3. ONE BEHAVIOR PER TEST. If "and" appears in the test name, split it.
4. EDGE CASES FIRST. Empty, null, boundary, concurrent, error paths. The happy path
   is the least valuable test you can write.
5. STRONG ASSERTIONS ONLY. `.toBeTruthy()` catches nothing. Assert specific values.
6. REGRESSION OVER COVERAGE. One test that catches a real bug beats ten that pad
   metrics. Every bug fix gets a test that would have caught it.
7. NEVER `.skip()` or `.only()`. Fix the test or delete it; both become permanent.

## Red-Green-Refactor

1. Write test cases from the requirement (inputs + expected outputs) before any
   implementation exists.
   (gate: suite exits non-zero, the new tests fail red)
2. Implement the minimal code to pass. No anticipatory features.
   (gate: suite exits zero)
3. Refactor while green. Tests still pass after every change.

## Edge-case enumeration

For every non-trivial function, enumerate explicitly:
- Empty / null / undefined inputs
- Boundary values (0, -1, MAX_INT, empty string, oversized input)
- Invalid type or shape: must error, never return a corrupted result
- Security inputs (injection payloads, newline injection): rejected at entry
- Concurrent access or race conditions where applicable
(gate: minimum 3 edge cases per non-trivial function)

## Name tests as specifications

Format: `GIVEN <state> WHEN <action> SHOULD <expected>`
File/function pattern: `test_{function}_{scenario}_{expected}`
If the name cannot be written in that form, the requirement is ambiguous: clarify first.

## Prioritize by risk

Business logic > error handling > boundary conditions > state transitions >
integration points > regression cases. Unit tests are the primary layer; E2E covers
critical user-visible flows only, and flaky tests get fixed or deleted immediately.

## Reviewing generated tests

Before accepting any AI-written test: does the assertion check the right thing, is it
coupled to internals, is state shared between tests, does it test the requirement or
mirror possibly-buggy code? At least one negative/rejection case per test file.

## Exercise the armed path

A green sub-computation is not a green control flow. The recurring failure shape:
the logic passes in isolation while the bug lives in how it is wired (the armed
hook path, the exit code under `set -e`, the runtime type check, setup only the
test harness performs).
- Drive the REAL entry point end-to-end at least once: the wired handler, the
  installed hook, the fresh-checkout runtime, not just the extracted function.
- Echo-test every wrapper/tool parameter once before relying on it: a silently
  dropped param runs defaults while reporting your value.
- Verify reachability, not just correctness: name the live call site that invokes
  the new code. A fully built system with zero call sites is not shipped.
- Test-environment parity: anything the harness sets up (migrations, bindings,
  seeded state), the real runtime must also get, or its absence must be a named,
  loud condition.
- Multi-loader integrations need one real payload fixture per loader. Sharing a
  matcher or entry point does not prove that Claude, Codex, an IDE, or CI sends
  the same field names. Assert both the decision and the non-empty data the
  safety check actually inspected; an armed hook reading an empty field is a
  silent no-op.
- Install and upgrade behavior gets a disposable-copy test: fresh install,
  supported prior-version upgrade, user-owned collision, and rollback from a
  working directory outside the source checkout. Documentation commands must be
  executed verbatim there, not merely found with grep.
- Bound heavyweight verification by time, process count, and memory when the
  runner supports it. Start with the narrow suite, record resource use, then run
  the full suite once. A test command that can freeze the workstation is a
  failed test design even if it eventually turns green.

## Verification Gate

Always provide runnable verification: if you can't verify it, don't ship it. Any
deterministic signal counts (suite exit code, lint report, build failure, fixture
diff). Verify against the original spec, not just the code structure: generated code
implements what was inferred, which is not always what was needed.

<on_complete>
agentdb write-end '{"skill":"testing","tests_added":N,"coverage_delta":"+X%","edge_cases":["list"],"assertions":"strong|weak"}'
</on_complete>

</skill>
