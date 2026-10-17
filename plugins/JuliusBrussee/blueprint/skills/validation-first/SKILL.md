---
name: validation-first
description: |
  Validation-first design for AI agent output — every spec requirement must be automatically verifiable.
  Covers the 6-gate validation pipeline, phase gates between Hunt phases, merge protocol,
  completion signals, and acceptance criteria design patterns.
  Trigger phrases: "validation gates", "quality gates", "validation-first design",
  "how to validate agent output", "acceptance criteria design"
---

# Validation-First Design

## Core Principle: If an Agent Cannot Validate It, It Will Not Be Met

Every spec requirement must include testable acceptance criteria that an agent can automatically verify. This is not optional — it is the foundation that makes SDD work.

**Why?** AI agents are non-deterministic. Without automated validation, there is no way to know whether an agent's output is correct. Validation gates turn "the agent generated some code" into "the agent generated code that provably meets the specification."

The validation-first rule applies at every level:
- **Spec requirements** must have testable acceptance criteria
- **Plans** must define which gates verify each task
- **Implementation** must pass all applicable gates before being considered complete
- **Iterations** must show measurable progress through gates

---

## The Validation Gate Sequence

Every implementation must pass through six ordered checkpoints. Each successive gate is more expensive to run, so catching failures early saves significant time.

### Gate 1: Compilation Check

**What:** The project compiles/transpiles without errors.

```bash
# Generic pattern — substitute your project's build command
{BUILD_COMMAND}
```

**Why it matters:** If the code does not build, nothing else can be validated. This is the cheapest possible check.

**What it catches:**
- Syntax errors
- Missing imports/dependencies
- Type errors (in typed languages)
- Configuration errors

**Acceptance criteria pattern:**
```markdown
- [ ] `{BUILD_COMMAND}` completes with exit code 0
- [ ] No warnings related to {domain} (warnings in other domains are acceptable)
```

### Gate 2: Isolated Unit Verification

**What:** Unit tests pass on all changed files.

```bash
# Generic pattern
{TEST_COMMAND}

# Or targeted at changed files
{TEST_COMMAND} --filter {changed-files}
```

**Why it matters:** Unit tests verify individual functions and modules in isolation. They are fast, deterministic, and catch logic errors.

**What it catches:**
- Incorrect function behavior
- Edge cases not handled
- Regression from changes to existing code
- Contract violations (wrong return types, missing fields)

**Acceptance criteria pattern:**
```markdown
- [ ] All existing unit tests pass
- [ ] New unit tests cover all acceptance criteria for R{N}
- [ ] No test relies on external services or network access
```

### Gate 3: Cross-Component Integration

**What:** End-to-end and integration tests verify that components work together.

```bash
# Generic pattern
{TEST_COMMAND} --e2e

# Or with a specific test runner
{E2E_TEST_COMMAND}
```

**Why it matters:** Unit tests verify components in isolation. Integration tests verify they work together. Many bugs only appear at integration boundaries.

**What it catches:**
- API contract mismatches between components
- Data flow errors across module boundaries
- Authentication/authorization integration issues
- Database query errors with real (or realistic) data

**Acceptance criteria pattern:**
```markdown
- [ ] User can complete {workflow} end-to-end
- [ ] API endpoint returns correct response for {scenario}
- [ ] Error propagation works correctly from {source} to {destination}
```

### Gate 4: Resource and Speed Benchmarks

**What:** Performance benchmarks pass defined thresholds.

```bash
# Generic pattern
{BENCHMARK_COMMAND}

# Or specific checks
{TEST_COMMAND} --performance
```

**Why it matters:** Functional correctness is necessary but not sufficient. Performance regression can make a feature unusable even if it produces correct output.

**What it catches:**
- Response time regression
- Memory leaks or excessive allocation
- CPU-intensive operations that block the main thread
- Database query performance degradation

**Acceptance criteria pattern:**
```markdown
- [ ] API response time < {N}ms at p95 under {M} concurrent users
- [ ] Page load time < {N}s on simulated 3G connection
- [ ] Memory usage does not exceed {N}MB during {operation}
- [ ] No operation blocks the main thread for > {N}ms
```

**Note:** Not every task needs performance gates. Apply Gate 4 when:
- The spec explicitly defines performance requirements
- The change touches a known hot path
- The feature involves data processing at scale

### Gate 5: Startup Smoke Test

**What:** The application starts successfully and basic smoke tests pass.

```bash
# Generic pattern — start the application
{START_COMMAND}

# Verify it is running
curl -f http://localhost:{PORT}/health

# Or run smoke tests
{SMOKE_TEST_COMMAND}
```

**Why it matters:** Code can build and pass all tests but fail to start. Launch verification catches configuration issues, missing environment variables, port conflicts, and startup race conditions.

**What it catches:**
- Missing environment variables or configuration
- Port conflicts or binding errors
- Startup initialization failures
- Missing runtime dependencies
- Database migration issues

**Acceptance criteria pattern:**
```markdown
- [ ] Application starts with `{START_COMMAND}` and responds to health check
- [ ] Main screen/page renders without errors
- [ ] No error-level entries in application logs during startup
- [ ] Application shuts down gracefully on interrupt signal
```

### Gate 6: Manual Audit

**What:** A human reviews the output for quality, design intent, and requirements that are difficult to automate.

**Why it matters:** Some things cannot be automated — UX quality, architectural elegance, naming consistency, documentation clarity. Gate 6 is where the human acts as the final quality filter.

**What it catches:**
- Subjective quality issues
- Architectural decisions that are technically correct but strategically wrong
- Over-engineering or under-engineering
- Security concerns that automated tools miss
- Requirements that were technically met but miss the spirit of the spec

**How it works in practice:**
1. Agent completes Gates 1-5 and reports results
2. Human reviews the implementation against spec intent
3. Human provides feedback as issues or spec updates
4. If feedback requires code changes, it enters the revision loop:
   - Update specs with the missing requirement
   - Re-run iteration loop
   - Verify the fix emerges from updated specs

**Acceptance criteria pattern:**
```markdown
- [ ] Implementation reviewed by human for spec intent alignment
- [ ] No architectural concerns raised
- [ ] Code style consistent with project conventions
```

---

## Gate Summary Table

| Gate | Purpose | Command Pattern | Typical Duration | Automated? |
|------|---------|----------------|-----------------|------------|
| 1. Compilation | Code compiles cleanly | `{BUILD_COMMAND}` | Seconds | Yes |
| 2. Unit Verification | Individual functions behave correctly | `{TEST_COMMAND}` | Seconds-Minutes | Yes |
| 3. Integration | Modules cooperate as expected | `{E2E_TEST_COMMAND}` | Minutes | Yes |
| 4. Benchmarks | Speed and resource use within budget | `{BENCHMARK_COMMAND}` | Minutes | Yes |
| 5. Smoke Test | Application boots and responds | `{START_COMMAND}` + health check | Seconds | Yes |
| 6. Manual Audit | Meets design intent and quality bar | Human inspection | Variable | No |

> For the full validation gate reference with detailed examples, see `references/validation-gates.md`.

---

## Mapping Spec Requirements to Gates

Every spec requirement must map to at least one validation gate. When writing specs (see `ck:cavekit-writing`), each acceptance criterion should indicate which gate verifies it.

### Mapping Pattern

```markdown
### R1: User Authentication
**Acceptance Criteria:**
- [ ] Valid credentials return session token — **Gate 2** (unit test)
- [ ] Invalid credentials return 401 error — **Gate 2** (unit test)
- [ ] Session token grants access to protected endpoints — **Gate 3** (integration)
- [ ] Login page renders within 2s — **Gate 4** (performance)
- [ ] Application starts with auth module loaded — **Gate 5** (launch)
```

### Unmapped Requirements Are Unvalidated

If a requirement cannot be mapped to any gate, it has one of two problems:
1. **The requirement is too vague** — rewrite it with specific, testable criteria
2. **The validation infrastructure is missing** — add the gate (e.g., if there are no E2E tests, Gate 3 does not exist yet)

Either way, an unmapped requirement will not be reliably met by an agent.

---

## Phase Gates Between Hunt Phases

Phase gates are mandatory verification checkpoints between Hunt phases. They ensure that the output of one phase is solid before the next phase builds on it.

### Phase Gate Definitions

| Transition | Gate Condition | How to Verify |
|------------|---------------|---------------|
| **Spec → Plan** | All domains have specs with testable acceptance criteria | Review cavekit-overview.md; every R{N} has AC items |
| **Plan → Implement** | Plans reference specs, define sequence, include test strategies | Review plan files; every task maps to spec requirements |
| **Implement → Iterate** | Code builds (Gate 1), tests pass (Gate 2), impl tracking is current | Run `{BUILD_COMMAND}` and `{TEST_COMMAND}`; check impl tracking |
| **Iterate → Monitor** | Convergence detected: changes decreasing iteration-over-iteration | Compare diffs across last 3-5 iterations |
| **Monitor → Spec** | Gap found or new requirement identified | Gap analysis identifies unmet acceptance criteria |

### Phase Gate Enforcement

Phase gates are enforced by the iteration loop. When a prompt includes phase gate checks, the agent:

1. Runs the gate check at the end of the phase
2. Reports pass/fail status
3. If the gate fails, the agent does not proceed to the next phase
4. Instead, the agent iterates on the current phase until the gate passes

### Example: Implement → Iterate Gate

```markdown
## Exit Criteria (Phase Gate)
Before reporting completion:
- [ ] `{BUILD_COMMAND}` succeeds with exit code 0
- [ ] `{TEST_COMMAND}` passes with no new failures
- [ ] All files created/modified are listed in impl tracking
- [ ] All dead ends encountered are documented
- [ ] Test health table is updated with current counts
```

---

## Merge Protocol

When working with agent teams (multiple agents dispatched via the Agent tool), the merge protocol ensures that integrating work from different agents does not break validation gates.

### The Protocol

```
Agent A completes work in its isolated branch
Agent B completes work in its isolated branch
Agent C completes work in its isolated branch

Merge sequence (one at a time):
1. Merge Agent A's branch → main
2. Run: {BUILD_COMMAND} → must pass
3. Run: {TEST_COMMAND} → must pass
4. Run: Launch verification → must pass
5. If all pass → proceed
6. If any fail → fix before merging next branch

7. Merge Agent B's branch → main
8. Run: {BUILD_COMMAND} → must pass
9. Run: {TEST_COMMAND} → must pass
10. ...repeat for each agent branch
```

### Why One at a Time?

Merging all agent branches simultaneously and then running tests makes it impossible to determine which merge caused a failure. Merging one at a time with validation between each merge pinpoints failures immediately.

### Merge Protocol Rules

1. **Merge one agent branch at a time** — never batch-merge
2. **Run Gates 1-3 after each merge** — build, unit tests, integration tests
3. **Run Gate 5 after all merges** — launch verification on the fully integrated codebase
4. **Clean up after each merge**: delete the merged branch (`git branch -D <branch>`).
5. **If a merge fails validation,** fix it before proceeding to the next merge

---

## Completion Signals

Completion signals are specific strings that agents emit when all exit criteria for a task or phase are met. They enable automation to detect when an agent is done.

### How Completion Signals Work

1. **The prompt defines the signal:**
   ```markdown
   When ALL exit criteria are met, output exactly:
   <all-tasks-complete>
   ```

2. **The agent emits the signal** after verifying all exit criteria

3. **The iteration loop detects the signal** and stops iterating

### Completion Signal Rules

- The signal must be a **unique string** that would not appear in normal output
- The agent must **verify all exit criteria** before emitting the signal
- The signal should be the **last thing** the agent outputs in a session
- If the agent cannot meet all criteria, it should **not emit the signal** and instead document what is blocking completion

### Example Prompt with Completion Signal

```markdown
## Exit Criteria
Complete all of the following before emitting the completion signal:
- [ ] All T- tasks are DONE or BLOCKED with documented blockers
- [ ] `{BUILD_COMMAND}` succeeds
- [ ] `{TEST_COMMAND}` passes with no new failures
- [ ] Implementation tracking is updated
- [ ] All dead ends are documented

When ALL criteria above are met, output:
<all-tasks-complete>

If you cannot meet all criteria, document what is blocking
and do NOT output the completion signal.
```

---

## Validation-First Design Patterns

### Pattern 1: Test Before Implement

Write or generate tests before implementing the feature. The test defines what "correct" means.

```
1. Read spec requirement R{N} acceptance criteria
2. Generate test cases that verify each criterion
3. Run tests → all fail (RED)
4. Implement the feature
5. Run tests → all pass (GREEN)
6. Refactor if needed
```

This is TDD-within-SDD. See `superpowers:test-driven-development` for the existing TDD skill.

### Pattern 2: Gate Cascade

Run gates in order. If an earlier gate fails, do not run later gates.

```
Gate 1 (Build) → FAIL → fix build errors → retry Gate 1
Gate 1 (Build) → PASS → Gate 2 (Unit Tests)
Gate 2 (Tests) → FAIL → fix failing tests → retry Gate 2
Gate 2 (Tests) → PASS → Gate 3 (Integration)
...
```

Earlier gates are cheaper. Fixing a build error costs seconds. Fixing an integration error costs minutes. Fix cheap problems first.

### Pattern 3: Progressive Gate Depth

Not every iteration needs all gates. Use progressive depth based on the phase:

| Phase | Required Gates | Optional Gates |
|-------|---------------|---------------|
| Early Implement | 1 (Build), 2 (Unit) | — |
| Mid Implement | 1, 2, 3 (Integration) | 4 (Performance) |
| Late Implement | 1, 2, 3, 5 (Launch) | 4 |
| Pre-Release | All 1-6 | — |

### Pattern 4: Regression Prevention

When a gate that previously passed starts failing, treat it as a P0 issue:

1. **Stop forward progress** — do not implement new features
2. **Identify the regression** — which change caused the failure?
3. **Fix the regression** — restore the passing state
4. **Add a test** — ensure this specific regression cannot recur
5. **Backpropagate** — if the regression reveals a spec gap, update the spec

---

## Integration with Other Skills

### With `superpowers:verification-before-completion`

The existing `verification-before-completion` skill provides a general framework for verifying work before marking it done. Validation-first design extends this with the specific 6-gate pipeline and phase gate system used in SDD.

**How they work together:**
- `superpowers:verification-before-completion` ensures the agent checks its work
- `ck:validation-first` defines exactly what checks to run and in what order

### With `ck:cavekit-writing`

Every spec requirement must have acceptance criteria that map to validation gates. The spec-writing skill defines how to write those criteria. Validation-first design defines how to verify them.

### With `ck:impl-tracking`

Validation results are recorded in the implementation tracking document's Test Health table. Gate failures become Issues. Gate-related dead ends are documented in the Dead Ends section.

### With `ck:methodology`

Validation gates operate continuously across all Hunt phases. Phase gates control transitions between phases. The iteration loop uses gate results as convergence signals.

---

## Summary

1. **If an agent cannot validate it, it will not be met** — every requirement needs automated verification
2. **6 gates in order:** Compilation → Unit Verification → Integration → Benchmarks → Smoke Test → Manual Audit
3. **Earlier gates are cheaper** — catch problems at the build stage, not at launch
4. **Every spec requirement maps to at least one gate** — unmapped requirements are unvalidated
5. **Phase gates control Hunt transitions** — do not proceed until the current phase passes its gate
6. **Merge one at a time** — validate between each merge to pinpoint failures
7. **Completion signals enable automation** — agents emit a specific string when all gates pass
8. **Regression is P0** — when a passing gate starts failing, stop and fix before proceeding
