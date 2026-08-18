# Test a CLI Command Workflow

Build a layered, isolated test suite around observable command behavior.

## When to Use

- Adding tests for a new or changed Go command.
- Stabilizing flaky tests involving process state or external resources.
- Deciding whether behavior belongs in a unit, integration, or binary test.

## Prerequisites

- The command's input, output, error, and exit contract.
- A seam for invoking command logic or the built executable.

**Reference:** `../references/cli-testing/knowledge.md`

## Workflow Steps

### Step 1: Inventory Observable Behaviors

**Goal:** Turn the command contract into meaningful test cases.

- [ ] List success, empty, invalid, boundary, dependency-failure, and cancellation cases.
- [ ] Mark exact-output compatibility requirements.
- [ ] Identify filesystem, environment, network, process, and clock dependencies.
- [ ] Choose the narrowest boundary that can prove each behavior.
- [ ] Separate parser grammar, runner wiring, and process exit into distinct layers.

**Reference:** `../references/cli-testing/checklist.md`

### Step 2: Isolate Inputs and Effects

**Goal:** Give each test exclusive ownership of mutable resources.

- [ ] Inject arguments, stdin, stdout, stderr, and dependencies.
- [ ] Use `t.TempDir`, `t.Setenv`, `httptest`, and immediate cleanup.
- [ ] Avoid package-global replacements and fixed ports or paths.
- [ ] Do not use `t.Parallel` where process state is shared.
- [ ] Construct a fresh root command and typed configuration for every case.
- [ ] Use a function-backed HTTP transport unless real protocol behavior is under test.
- [ ] Use a real driver and production migrations when SQL adapter behavior is under test.

**Reference:** `../references/cli-testing/rules.md`

### Step 3: Implement Focused Tests

**Goal:** Cover behavior without coupling to implementation structure.

- [ ] Use table rows for distinct behavior classes.
- [ ] Assert stdout and stderr separately.
- [ ] Inspect errors with `errors.Is` or `errors.As`.
- [ ] Mark helpers and keep fatal assertions limited to unsafe continuation.

**Reference:** `../references/cli-testing/examples.md`

### Step 4: Add Boundary Tests Deliberately

**Goal:** Test real integration semantics only where they add confidence.

**If executable behavior matters:**

- [ ] Build or launch a helper process.
- [ ] Assert arguments, exit status, signals, cancellation, and stream routing.

**If a service contract matters:**

- [ ] Use an isolated local server or repository.
- [ ] Assert both the outgoing request and interpreted response.

**If a live dependency is unavoidable:**

- [ ] Require explicit opt-in.
- [ ] Create uniquely named resources and register reversible cleanup first.

**Reference:** `../references/cli-testing/patterns.md`

### Step 5: Run Reliability Checks

**Goal:** Verify that the suite detects races and terminates predictably.

- [ ] Run `go test ./...`.
- [ ] Run the explicit normal and `-short` lanes.
- [ ] Run `go test -race ./...`.
- [ ] Run `go test -shuffle=on` and preserve any reported failure seed.
- [ ] Review coverage scope and assertion quality after correctness tests exist.
- [ ] Run tagged integration profiles uncached when applicable.
- [ ] Replace sleeps with synchronization, deadlines, or fake clocks.
- [ ] Re-run likely flaky cases enough to expose shared state.
- [ ] Run the explicit matrix of supported build-tag or capability profiles.
- [ ] Record profile, tags, selected files, test command, artifact name, smoke
      command, race lane, and supported/unsupported status.
- [ ] Verify selected files with `go list` and intentional unsupported combinations.
- [ ] Smoke-test at least one critical flow from the final artifact.
- [ ] Stop before benchmarking or profiling and route that work to
      `go-performance-testing`.

**Reference:** `../references/cli-testing/checklist.md`

## Quick Checklist

```text
[ ] Behaviors are mapped to the narrowest useful test level
[ ] Every mutable resource is isolated and cleaned up
[ ] Streams, errors, and exit behavior are asserted
[ ] External boundaries are local or explicitly opt-in
[ ] Standard, race, and relevant tagged tests pass
```

## Common Mistakes

| Mistake | Consequence | Do Instead |
|---|---|---|
| Testing internal calls instead of results | Refactors break valid tests | Assert observable behavior |
| Sleeping until asynchronous work "should" finish | Slow, flaky tests | Synchronize or use a fake clock |
| Replacing global dependencies in parallel tests | Cross-test races | Inject dependencies per test |

## Exit Criteria

- [ ] The suite covers success and meaningful failure classes.
- [ ] Tests do not depend on developer data or mutable shared infrastructure.
- [ ] Failures have bounded execution time and actionable evidence.
- [ ] Required standard, race, and integration profiles pass.
- [ ] Every build constraint maps to an executed CI lane.
