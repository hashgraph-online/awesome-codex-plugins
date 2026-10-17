# Stabilize Flaky Test Workflow

Replace timing assumptions and shared state with observable, bounded contracts.

## Workflow Steps

### 1. Reproduce

- [ ] Run the narrow test repeatedly with `-count`.
- [ ] Run with race detection and shuffled order.
- [ ] Preserve the command, seed, environment, and first actionable failure.

### 2. Classify

- [ ] Identify arbitrary sleeps, real clocks, shared globals, leaked goroutines,
      unordered output, and external effects.
- [ ] Distinguish production nondeterminism from a test-only race.

### 3. Introduce Control

- [ ] Replace sleeps with barriers, completion channels, or observable state.
- [ ] Inject a per-instance clock when time is a domain dependency.
- [ ] For Go 1.25+, use `testing/synctest` only for suitable isolated
      goroutine/timer behavior.
- [ ] Isolate files, environment, command trees, repositories, and ports.

### 4. Prove Terminal State

- [ ] Bound waits with deadlines.
- [ ] Join all goroutines before test return.
- [ ] Assert success, error, cancellation, and cleanup state explicitly.

### 5. Verify

- [ ] Re-run the original count, race, and shuffle commands.
- [ ] Replay the original failing seed.
- [ ] Run the surrounding package and repository suites.

## Exit Criteria

- [ ] The test has no arbitrary synchronization sleeps.
- [ ] All mutable state is owned by one test.
- [ ] Failure remains bounded and diagnostic.
- [ ] The original reproduction no longer fails.
