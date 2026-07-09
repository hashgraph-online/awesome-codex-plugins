---
name: create-test
description: "Use when user wants to create tests, generate test coverage, audit test quality, find untested code, or improve weak assertions. Use when user says write tests, test coverage, missing tests, or untested code."
argument-hint: "[file-or-directory-or-goal]"
user-invocable: true
allowed-tools: Glob, Grep, Read, Bash, Agent, Edit, Write, AskUserQuestion
---

# Create Test — Intelligent Test Design

ultrathink

Apply [Iron Rules](../../shared/iron-rules.md) — Principle 3 (plain pytest before any library), 7 (TDD; tests must find bugs, not just exist), 8 (no claim without fresh test output).

Plus: test through the public API, never the internals; strong assertions only (never `assertNotNull(x)` alone); prefer property-based over hardcoded cases; never modify source code (only test files, conftest, fixtures); match existing project conventions.

## Argument Routing

Parse `$ARGUMENTS`. Use Glob/Bash to check if it matches existing paths:
- **Existing file(s)/directory** → Mode B for those paths
- **Natural-language goal** (not a path) → Mode A with the goal; direct analysis toward it
- **No arguments** → Mode A on the full project

## Mode A: Strategic Analysis

Read `references/explorer-prompt.md`. Spawn an analysis subagent (Agent tool) with its contents as the prompt. If `$ARGUMENTS` carries a goal, append it and instruct the subagent to prioritize strategies serving that objective and explain WHY each helps.

Display the returned analysis inline. The user then selects items (→ Mode B each), asks a follow-up (answer from context), or skips.

## Mode B: Targeted Generation

Read `references/testing-strategies.md`.

### Step 0: Verify Test Infrastructure
Confirm the test framework is installed/configured; if missing, ask before setting up.

### Step 1: Read and Understand
Read the target completely. For **Python**, also consult `../python-dev/patterns.md` (Test taxonomy) for the team-canonical 4-tier layout and pytest/async/mock conventions.

### Step 2: Implementation Analysis
Per public function/method/endpoint, identify: boundaries (every comparison/limit → N-1/N/N+1, type coercion points); state space (branches, error/fallback/retry/timeout paths, states unreachable from current tests); invariants (round-trip, idempotence, monotonicity, ordering; a simpler reference oracle); API surface (schemas, status branches, CRUD lifecycle, error formats).

### Step 3: Strategy Selection

Map each characteristic to a strategy via `references/testing-strategies.md` (canonical selection table). For TDD / test-first, confirm with the user which public-API behaviors matter most before writing — concentrate on critical paths and complex logic, not every edge case.

Also read: `references/refactoring-workflow.md` if refactoring; `references/regression-detection.md` for regression-detection infrastructure.

### Step 4: Generate Tests
Strong assertions only (check `references/weak-assertion-patterns.md`). For golden-fixture / characterization patterns generate BOTH the capture script and the regression test.

### Step 5: Run and Verify
Run, read output, fix the TEST not the source on failure. **Mutation check** each critical assertion: temporarily set the expected value wrong, confirm the test FAILS, restore. A test that passes with a wrong value is tautological — rewrite it.

### Step 6: Report
List strategies applied and what each covered, and the functions/paths deliberately NOT tested with justification.
