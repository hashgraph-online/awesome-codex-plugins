# Go CLI Process Control Rules

Use these rules when a Go CLI starts, connects, cancels, or tests subprocesses.

## Command Construction

1. **Pass executable and arguments separately.**
   - Do not concatenate untrusted values into a shell command.
   - Do not expect `|`, `>`, `*`, quotes, or `$VAR` to be interpreted by
     `exec.Command`.

2. **Resolve execution context explicitly.**
   - Set `Dir` to the intended working directory.
   - Start from `os.Environ()` when adding environment variables; assigning a
     partial `Env` replaces the inherited environment.
   - Avoid inheriting secrets or interactive settings the child does not need.

3. **Validate dependencies at the boundary.**
   - Use `exec.LookPath` for a required external executable when early,
     actionable failure is valuable.
   - Include the executable and logical step in errors without exposing secrets.

## Completion and Output

4. **Observe both startup and completion.**
   - Call `Run`, `Output`, `CombinedOutput`, or `Start` followed by `Wait`.
   - Never treat `Start` returning nil as proof that the command succeeded.

5. **Choose stream behavior deliberately.**
   - Inject stdout and stderr writers into application logic.
   - Capture only output that must be parsed or returned.
   - Bound potentially large captured output.
   - Keep machine-readable stdout free of logs and diagnostics.

6. **Define success from the child’s real contract.**
   - Check exit status.
   - If a tool signals a condition through output, parse that condition
     explicitly and test empty, valid, malformed, and unexpected output.

7. **Preserve useful failure evidence.**
   - Wrap causes with `%w`.
   - Use `errors.Is` or `errors.As`, not full-string comparison.
   - Retain relevant stderr, but redact credentials and tokens.

## Cancellation and Cleanup

8. **Propagate a caller-owned context.**
   - Accept `context.Context` near the operation boundary.
   - Derive a step timeout from that context rather than starting from
     `context.Background()` deep inside the call tree.

9. **Always release derived contexts.**
   - Call the returned cancellation function, normally with `defer`.
   - Report `context.Canceled` and `context.DeadlineExceeded` distinctly when
     callers can act on the distinction.

10. **Account for descendants.**
    - Verify that cancellation stops helper processes, shells, and pipelines, not
      only the immediate child.
    - Implement and test platform-specific tree control, such as Unix process
      groups or Windows Job Objects; killing only `cmd.Process` is not equivalent.
    - Wait for all started processes and close all owned pipe endpoints.

11. **Make cleanup idempotent and immediate.**
    - Register `t.Cleanup` or `defer` immediately after acquiring a resource.
    - Clean temporary repositories, directories, sockets, and altered process
      state even when an intermediate setup step fails.

## Signals and Pipelines

12. **Turn termination signals into cancellation.**
    - Subscribe only to signals the CLI intends to handle.
    - Stop signal delivery when the lifecycle ends.
    - Stop scheduling steps after cancellation and wait for active work.

13. **Fail pipelines fast by default.**
    - Execute steps in a deterministic order.
    - Return the first failure with its step identity.
    - Do not emit success for steps that did not run.

14. **Wait for every process in an OS pipeline.**
    - Connect streams before starting processes.
    - Close pipe ends in the correct owner.
    - Collect errors from every stage, not only the final consumer.

## Test Isolation

15. **Never exercise real mutable infrastructure by accident.**
    - Use temporary local services or injected fakes.
    - Require explicit opt-in for destructive or remote integration tests.
    - Verify the target path or remote before running commands that mutate it.

16. **Avoid mutable package-level command hooks.**
    - Prefer injecting a runner into the object or function under test.
    - If legacy tests replace a package variable, restore it with cleanup and do
      not run those tests in parallel.

17. **Test lifecycle failures, not only happy paths.**
    - Cover missing executables, invalid directories, non-zero exits, stderr,
      output-defined failures, timeout, caller cancellation, signal shutdown,
      partial pipeline execution, and cleanup.

## Failure Classification and Platform Behavior

18. **Classify process failures by lifecycle stage.**
    - Distinguish lookup, start, nonzero `*exec.ExitError`, cancellation,
      deadline, signal termination, and cleanup failure.
    - Preserve bounded redacted stderr where capture makes it available.

19. **Coordinate manual pipe readers with `Wait`.**
    - Consume `StdoutPipe` and `StderrPipe` concurrently.
    - Finish reads before or in coordination with `Wait`; do not call `Run`
      after taking manual pipe ownership.
    - Avoid waiting before readers drain a chatty child.

20. **Isolate platform process semantics.**
    - Put signal, process-group, executable, and descendant behavior behind
      build-constrained adapters with a stable contract.
    - Verify Windows cancellation separately from Unix signal behavior.
    - Treat `Cmd.String()` as diagnostics only, not replayable shell syntax.

## Exceptions

- A tiny one-shot internal tool may stream directly to `os.Stdout` and
  `os.Stderr`, but injected writers become worthwhile as soon as output is
  tested or reused.
- An explicit shell is appropriate when the shell language itself is required.
  Pin the shell contract, quote inputs safely, and document platform limits.
- Real integration tests are valuable when they run against isolated local
  resources and clean up reliably.

## Quick Reference

| Concern | Required behavior |
|---|---|
| Arguments | Separate argv elements; no accidental shell |
| Status | Wait and inspect the final result |
| Output | Route or capture intentionally |
| Errors | Wrap causes; inspect structurally |
| Timeout | Derive from caller context; cancel |
| Signal | Cancel work, wait, then return failure |
| Pipeline | Deterministic, fail-fast, wait every child |
| Tests | Isolated resources and injected runner |

## Source Traceability

- *Executing External Programs* and *Handling Errors*, Chapter 6, lines
  9075-9374.
- *Handling Output from External Programs*, Chapter 6, lines 9975-10290.
- *Running Commands with Contexts*, Chapter 6, lines 10298-10592.
- *Integration Tests with a Local Git Server*, *Testing Commands with Mock
  Resources*, and *Handling Signals*, Chapter 6, lines 10600-11769.
