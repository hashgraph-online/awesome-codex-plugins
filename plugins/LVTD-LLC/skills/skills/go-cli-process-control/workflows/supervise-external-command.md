# Supervise an External Command Workflow

Run a child process with deliberate arguments, output, cancellation, and cleanup.

## When to Use

- Wrapping an external executable in a Go CLI.
- Building a process pipeline or streaming adapter.
- Fixing hangs, orphan processes, lost stderr, or incorrect exit handling.

## Prerequisites

- The child executable's argument, output, exit, and signal contract.
- A caller-owned `context.Context`.

**Reference:** `../references/process-control/knowledge.md`

## Workflow Steps

### Step 1: Define the Execution Contract

**Goal:** Remove accidental shell and environment semantics.

- [ ] Pass executable and arguments as separate values.
- [ ] Use a shell only when the shell language itself is required.
- [ ] Set the intended directory and environment explicitly.
- [ ] Decide which output is streamed, captured, bounded, or parsed.

**Reference:** `../references/process-control/rules.md`

### Step 2: Construct an Injectable Runner

**Goal:** Separate application decisions from process mechanics.

- [ ] Accept context and command inputs at the operation boundary.
- [ ] Inject a runner or narrow function where unit tests need control.
- [ ] Validate required executables with an actionable error when appropriate.
- [ ] Preserve separate stdout and stderr behavior.

**Reference:** `../references/process-control/examples.md`

### Step 3: Observe Completion and Failure

**Goal:** Report the child's real terminal result.

- [ ] Use `Run`, `Output`, or `Start` followed by exactly one `Wait`.
- [ ] Inspect nonzero exits structurally and retain relevant stderr.
- [ ] Parse output-defined success or failure explicitly.
- [ ] Wrap causes while redacting secrets.
- [ ] Classify lookup, start, exit, cancellation, timeout, and cleanup separately.
- [ ] Coordinate concurrent pipe readers with `Wait`.
- [ ] Never use `Cmd.String()` as a replay or escaping mechanism.

**Reference:** `../references/process-control/rules.md`

### Step 4: Implement Cancellation and Cleanup

**Goal:** Stop all owned work within a bounded time.

- [ ] Derive timeouts from the caller context and release derived contexts.
- [ ] Verify `exec.Cmd.Cancel` and `WaitDelay` behavior for the pinned Go version.
- [ ] Account for shells, descendants, and every pipeline stage.
- [ ] Close owned pipes and wait for every started process.
- [ ] Make cleanup immediate and idempotent.

**Reference:** `../references/process-control/patterns.md`

### Step 5: Integrate Signals

**Goal:** Convert termination into orderly cancellation.

- [ ] Subscribe only to intended signals.
- [ ] Prefer `signal.NotifyContext` for context-driven shutdown.
- [ ] Call the returned stop function.
- [ ] Stop scheduling work, wait for active work, then return a deliberate status.
- [ ] Select a platform adapter for signals, process groups, and descendant cleanup.
- [ ] Define and test equivalent Windows behavior.

**Reference:** `../references/process-control/patterns.md`

### Step 6: Test Failure Paths

**Goal:** Prove lifecycle correctness, not only successful execution.

- [ ] Cover missing executable, bad directory, nonzero exit, and malformed output.
- [ ] Cover deadline, caller cancellation, and signal shutdown.
- [ ] Verify descendants and pipes do not survive.
- [ ] Run race tests and review against the checklist.

**Reference:** `../references/process-control/checklist.md`

## Quick Checklist

```text
[ ] Arguments and environment are explicit
[ ] Startup and terminal status are both observed
[ ] Output and errors preserve the child contract
[ ] Cancellation reaches descendants and pipelines
[ ] Every started process is waited and every resource cleaned
```

## Common Mistakes

| Mistake | Consequence | Do Instead |
|---|---|---|
| Treating `Start` as success | Later exit failure is lost | Always call and inspect `Wait` |
| Assuming context kills a process tree | Descendants survive | Design and test platform-specific tree cleanup |
| Using `CombinedOutput` indiscriminately | Stream meaning and memory bounds are lost | Route or capture each stream deliberately |

## Exit Criteria

- [ ] The wrapper preserves arguments, streams, status, and useful failure evidence.
- [ ] Cancellation and signals terminate all owned work within a bound.
- [ ] Process, pipe, and temporary-resource cleanup is verified.
- [ ] Lifecycle tests and race checks pass.
