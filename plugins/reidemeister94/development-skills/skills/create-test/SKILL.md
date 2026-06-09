---
name: create-test
description: "Use when user wants to create tests, generate test coverage, audit test quality, find untested code, or improve weak assertions. Use when user says write tests, test coverage, missing tests, or untested code."
argument-hint: "[file-or-directory-or-goal]"
user-invocable: true
allowed-tools: Glob, Grep, Read, Bash, Agent, Edit, Write, AskUserQuestion
---

# Create Test — Intelligent Test Design

ultrathink

Apply [Iron Rules](../../shared/iron-rules.md) — Principle 3 (simplicity: plain pytest before any library; refactor measurably improves a named dimension), Principle 7 (TDD Red → Green → Refactor — tests must find bugs, not just exist), and Principle 8 (no claim without fresh test output).

## Rules (apply to ALL modes)

- **Simplicity first.** Use the simplest approach that catches the bug. Plain pytest + assert before any library. Add a dependency only when the concept cannot be expressed without it.
- **Tests must find bugs, not just exist.** Every test must target a specific failure mode.
- **Test through the public API.** Do not test private/internal functions directly.
- **Strong assertions only.** Never generate `assertNotNull(x)` as sole assertion. Assert specific values, shapes, invariants.
- **Random data over fixed data.** Prefer property-based tests over hardcoded cases. Fixed cases only for boundary values.
- **Fast by default.** Property tests: 100 examples. Parametrize, don't duplicate.
- **Run every test you write.** Never present tests as done without executing them.
- **Never modify source code.** Only create/modify test files, conftest, and fixtures.
- **Match project conventions.** Use existing test directory, naming, markers, fixture patterns.

## Argument Routing

Parse `$ARGUMENTS`:

1. **No arguments** → **Mode A: Strategic Analysis** of the full project
2. **Arguments resolve to existing file(s) or directory** → **Mode B: Targeted Generation** for those paths
3. **Arguments are natural language** (not a valid path) → **Mode A: Strategic Analysis** with `$ARGUMENTS` as the goal. Analysis and recommendations are directed toward achieving that goal.

To distinguish case 2 from 3: use Glob/Bash to check if `$ARGUMENTS` matches existing paths. If yes → Mode B. If no → Mode A with goal.

---

## Mode A: Strategic Analysis

Read `references/explorer-prompt.md`. Spawn an analysis subagent (Agent tool) with its contents as the prompt.

If `$ARGUMENTS` contains a goal (case 3 above), append to the subagent prompt:

```
## USER GOAL
"$ARGUMENTS"
Focus your analysis and recommendations on what is most relevant to this goal.
Prioritize strategies that directly serve this objective.
Explain WHY each recommendation helps achieve the goal.
```

After the subagent returns, display the full analysis inline to the user.

The user will either:
- Select items by number or priority level → run **Mode B** for each selected item
- Ask a follow-up question → answer using the analysis context
- Say "skip" → end

---

## Mode B: Targeted Generation

Read `references/testing-strategies.md` now. Keep its principles active throughout.

### Step 0: Verify Test Infrastructure

1. Identify project language from config files (pyproject.toml, package.json, pom.xml, build.gradle, Package.swift)
2. Check test framework is installed and configured:
   - Python: pytest in requirements/pyproject.toml, `tests/` or `test/` directory
   - TypeScript: vitest/jest in package.json, test script defined
   - Java: JUnit in pom.xml/build.gradle, `src/test/` exists
   - Swift: XCTest/swift-testing target in Package.swift
3. If test framework **missing**: stop and ask — "No test framework detected. Should I set up [pytest/vitest/JUnit] first?"
4. If test directory **missing**: create it following language conventions

### Step 1: Read and Understand

1. Read the target file completely
2. If a directory, read all source files in it
3. Read the **relevant language section** from `references/language-templates.md` (Python, Java, TypeScript, or Swift — not the entire file)
4. For **Python** projects, also consult `../python-dev/patterns.md` (Testing section) for team-canonical patterns: the 4-tier layout (Unit / Golden / E2E Replay / Integration), `asyncio_mode="auto"`, `TestClient(raise_server_exceptions=False)`, autouse `dependency_overrides` reset, and `MagicMock(spec=Class)` + `AsyncMock` conventions.

### Step 2: Implementation Analysis

For each public function/method/endpoint:

**Boundaries:** numeric comparisons → extract thresholds, test N-1/N/N+1. String length limits, array sizes, enum ranges. Type coercion points (int/float, null).

**State space:** if/else chains, switch/match, state machines. Focus on fragile states: error paths, fallbacks, retry, timeout. Which states are NOT reachable from current tests?

**Invariants:** round-trip, idempotence, monotonicity, ordering preservation. Can a simpler reference implementation verify the result? Do aggregation totals match?

**API surface** (endpoints): request/response schemas, status code branches, CRUD lifecycle, error formats.

### Step 3: Strategy Selection

Refer to `references/testing-strategies.md` strategy matrix to select strategies.

If the target involves **refactoring**, also read `references/refactoring-workflow.md`.
If the target involves **regression detection infrastructure**, also read `references/regression-detection.md`.
If the user asks for **TDD / red-green-refactor / test-first**, read `references/tdd-workflow.md` for the vertical-slice loop and "no horizontal slicing" anti-pattern.

| Code characteristic | Primary strategy | Secondary | Reference |
|-------------------|-----------------|-----------|-----------|
| Numeric thresholds | Boundary stress | Property-based | testing-strategies.md #1 |
| Data transformation | Property-based (round-trip, invariant) | Boundary | testing-strategies.md #2 |
| Parser / serializer | Fuzz + property-based | Boundary | testing-strategies.md #2 |
| API endpoint (read) | Golden fixture regression | Boundary | testing-strategies.md #4 |
| API endpoint (write) | CRUD lifecycle | Golden fixture | testing-strategies.md #5 |
| State machine | State transition coverage | Boundary | testing-strategies.md #1 |
| Algorithm / computation | Invariant (reference impl) | Property-based | testing-strategies.md #3 |
| Pure function, few params | Boundary exhaustive | — | testing-strategies.md #1 |
| DB queries / repositories | Real DB integration | Factory fixtures | integration-patterns.md |
| Browser UI / user flows | Playwright E2E | Visual regression | e2e-browser-patterns.md |
| Legacy code, pre-refactoring | Characterization (golden master) | Approval test | refactoring-workflow.md |
| Concurrent / async operations | Concurrency stress | Property-based | testing-strategies.md #10 |
| Microservice boundary | Contract test (Pact) | CRUD lifecycle | testing-strategies.md #11 |
| DB migrations | Up/down verification | Rollback test | integration-patterns.md |
| Migration legacy to new | Live comparison | Characterization | testing-strategies.md #6 |

### Step 4: Generate Tests

Generate the test file. For each test function:

1. **Descriptive name** — describes behavior, not method name
2. **AAA structure** — Arrange, Act, Assert (clearly separated)
3. **Strong assertions** — specific values, check `references/weak-assertion-patterns.md`
4. **Boundary tests** — N-1, N, N+1 at every threshold
5. **Property-based tests** — for data transformations (hypothesis, jqwik, fast-check)
6. **Random stress tests** — for complex logic, verify invariants over many iterations
7. **Error path tests** — invalid inputs, null/empty, type mismatches

For golden fixture / e2e patterns, generate BOTH the capture script and the regression test.

**Apply reference patterns by type:**
- DB integration → `references/integration-patterns.md`
- Playwright E2E → `references/e2e-browser-patterns.md`
- Characterization → `references/refactoring-workflow.md`
- Concurrency → `references/testing-strategies.md` #10 + `references/language-templates.md`
- Contract → `references/language-templates.md` Pact scaffolds

### Step 5: Run and Verify

1. Run generated tests with project's test command
2. Read output completely
3. If tests fail: fix the TEST (not source code), re-run
4. **Mutation check** — for each critical assertion:
   - Temporarily change expected value to something wrong
   - Run test — confirm it FAILS
   - Restore correct assertion
   - If test passes with wrong value → assertion is tautological, rewrite it

### Step 6: Quality Report

```
## Test Generation Report: [target]

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Tests generated | N | — | — |
| Assertion density | X/test | >= 2 | OK/WARN |
| Boundary tests | N | >= 1 per threshold | OK/WARN |
| Property-based tests | N | >= 1 per transform | OK/WARN |
| Weak assertions | N | 0 | OK/WARN |
| Random/fuzz tests | N | >= 1 for complex logic | OK/WARN |
| Integration tests (real DB) | N | >= 1 per repository/query | OK/WARN/N/A |
| E2E browser tests | N | >= 1 per critical flow | OK/WARN/N/A |
| Characterization tests | N | >= 1 per legacy module | OK/WARN/N/A |
| Concurrency tests | N | >= 1 per shared resource | OK/WARN/N/A |

### Strategies Applied
[list each strategy and what it covered]

### NOT Tested (and why)
[Functions/paths deliberately excluded with justification]
```
