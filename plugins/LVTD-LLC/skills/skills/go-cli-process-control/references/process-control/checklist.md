# Go CLI Process Control Checklist

Use when implementing or reviewing a Go CLI that runs external programs.

## Before Implementation

- [ ] Confirm an external process is preferable to a stable library or API.
- [ ] Define the executable, argv, working directory, and environment.
- [ ] Define success: exit code, output predicate, resulting state, or all three.
- [ ] Decide whether output is streamed, captured, parsed, or discarded.
- [ ] Identify timeout, cancellation, signal, and descendant-process behavior.
- [ ] Classify the command as read-only, local mutation, or external mutation.

## Command Construction

- [ ] Executable and arguments are passed separately.
- [ ] User input never enters an implicit `sh -c` string.
- [ ] Shell use, if intentional, is documented and inputs are safely handled.
- [ ] `Cmd.Dir` is explicit when relative paths matter.
- [ ] Environment additions preserve required inherited values.
- [ ] Secrets are not included in argv, logs, or returned errors.
- [ ] Missing executables produce an actionable error.

## Streams and Results

- [ ] Every started command is waited on exactly once.
- [ ] stdout and stderr follow the CLI's public output contract.
- [ ] Captured output has a known size bound or streaming parser.
- [ ] Non-zero exit status preserves useful diagnostics.
- [ ] Exit-zero domain failures are parsed and tested.
- [ ] Output write failures are not silently ignored.
- [ ] Error identity is tested with `errors.Is` or `errors.As`.
- [ ] Manual stdout/stderr pipes are drained concurrently.
- [ ] Pipe readers and `Wait` cannot deadlock each other.

## Context and Timeout

- [ ] Public operation accepts a caller context.
- [ ] Step-specific timeout derives from the caller context.
- [ ] Every derived context's cancel function is called.
- [ ] Cancellation and deadline expiration are distinguishable when useful.
- [ ] Cancellation is checked before starting the next workflow step.
- [ ] Child descendants and remote operations have an explicit cleanup plan.
- [ ] A canceled command cannot leave an unreaped process.

## Pipelines

- [ ] Step order is deterministic.
- [ ] Pipeline stops at the first failed prerequisite.
- [ ] Failure reports the logical step and wrapped cause.
- [ ] Success is emitted only after a step completes.
- [ ] Every OS-pipeline stage is started, canceled, and waited correctly.
- [ ] Pipe ends are closed by the correct owner.
- [ ] Errors from all stages are considered.

## Signals and Shutdown

- [ ] Only intended signals are intercepted.
- [ ] Signal registration is stopped when no longer needed.
- [ ] SIGINT/SIGTERM initiates cancellation rather than merely returning.
- [ ] No new work starts after shutdown begins.
- [ ] Active children, goroutines, files, and temporary state are cleaned up.
- [ ] Interrupted work returns a stable non-zero result.
- [ ] A second-signal or forced-exit policy is defined for stuck cleanup.
- [ ] Platform-specific process-group and signal behavior lives behind an adapter.
- [ ] Windows termination and descendant behavior receive target tests.

## Tests

- [ ] Success path checks argv, directory, output, and resulting state.
- [ ] Missing executable and invalid directory are covered.
- [ ] Non-zero exit and stderr are covered.
- [ ] Exit-zero/output-defined failure is covered.
- [ ] Timeout and caller cancellation are covered without long sleeps.
- [ ] Signal shutdown is covered without leaking global signal state.
- [ ] Partial workflow failure proves later steps do not run.
- [ ] Real-command tests use `t.TempDir` or equivalent disposable resources.
- [ ] Remote or destructive tests require explicit isolation or opt-in.
- [ ] Test cleanup is registered immediately and is safe to repeat.
- [ ] Fakes are injected per test; mutable global hooks are restored.
- [ ] Tests that mutate process-global state are not parallelized.
- [ ] Lookup, start, exit, cancellation, timeout, and cleanup are distinct cases.
- [ ] No diagnostic treats `Cmd.String()` as a replayable command.

## Red Flags

Stop and redesign if you find:

- A command assembled by concatenating user input into a shell string.
- `Start` without a guaranteed `Wait`.
- `context.Background()` created deep inside code that already has a caller.
- An unbounded `bytes.Buffer` attached to an untrusted or noisy process.
- Returning on SIGTERM while child processes continue running.
- A test that pushes to a real remote, changes a user repository, or uses live
  credentials.
- Package-global command mocks that leak between subtests.

## Quick Reference

| Aspect | Ideal | Red flag |
|---|---|---|
| Invocation | Explicit argv | Concatenated shell string |
| Completion | Wait and inspect | Fire-and-forget |
| Output | Contract-driven routing | Accidental discard or mixing |
| Cancellation | Caller context propagated | Detached background context |
| Shutdown | Cancel, clean, wait | Return while work continues |
| Tests | Isolated real resource or injected fake | Live mutable dependency |

## Source Traceability

- *Executing External Programs* through *Defining a Pipeline*, Chapter 6, lines
  9075-9826.
- *Handling Output from External Programs* and *Running Commands with
  Contexts*, Chapter 6, lines 9975-10592.
- *Integration Tests with a Local Git Server* and *Testing Commands with Mock
  Resources*, Chapter 6, lines 10600-11375.
- *Handling Signals*, Chapter 6, lines 11383-11769.
