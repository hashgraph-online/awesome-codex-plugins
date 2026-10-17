# Go CLI Process Control Knowledge

Core concepts for executing and supervising external programs from a Go CLI.

## Process Model

### Direct execution

`os/exec` starts a program directly. The executable name and each argument are
passed separately; Go does not implicitly invoke a shell.

- Use `exec.Command` for bounded commands that do not need caller cancellation.
- Use `exec.CommandContext` when execution belongs to a request or CLI lifecycle.
- Set `Cmd.Dir` when the child must run relative to a project or workspace.
- Set `Cmd.Env` only when the child needs an environment different from its
  parent.
- Use `exec.LookPath` when the CLI should fail early or skip an integration test
  if an optional executable is unavailable.

Shell syntax such as pipes, redirects, globs, and variable expansion has no
special meaning in an argument slice. Build pipelines with Go streams, or invoke
a shell explicitly only when shell semantics are the intended contract.

### Command lifecycle

An `exec.Cmd` describes one process execution. Configure it before starting it,
then use one of these modes:

| Mode | Behavior |
|---|---|
| `Run` | Start and wait; inherit no output streams unless configured |
| `Output` | Start, wait, and return stdout |
| `CombinedOutput` | Start, wait, and return merged stdout and stderr |
| `Start` + `Wait` | Separate startup from completion for streaming or orchestration |

A command value is single-use. A successful start does not mean successful
completion; `Wait` or a convenience method must observe the final status.

## Exit Status and Errors

Command failure and business-condition failure are distinct:

- A non-zero child exit normally arrives as an `*exec.ExitError`.
- Startup can fail because the executable, directory, or permission is invalid.
- A child may exit zero while its output indicates an unacceptable condition.
- The CLI itself may fail to write status output after the child succeeds.

Wrap errors with operational context while preserving the cause with `%w`.
Typed errors can carry the failed step and support `errors.As`; sentinel errors
can represent broad categories and support `errors.Is`.

Do not classify failures by comparing complete error strings. Preserve both a
stable machine-inspectable identity and a useful human message.

## Streams and Output

`Cmd.Stdin`, `Cmd.Stdout`, and `Cmd.Stderr` define the child's standard streams.
Leaving output streams unset discards child output rather than automatically
forwarding it to the parent terminal.

Choose routing according to the command contract:

- Stream progress to injected `io.Writer` values for interactive commands.
- Capture bounded output when the program must parse it.
- Keep stdout and stderr separate when callers or automation distinguish data
  from diagnostics.
- Avoid unbounded buffering for commands that may emit large output.

Some tools communicate domain state through output even after exit code zero.
Model that output predicate explicitly, such as “any filenames from a formatter
check means the step failed.”

## Sequential Pipelines

Use “pipeline” precisely:

1. a sequential application workflow;
2. an OS process pipeline connected by pipes;
3. an in-process goroutine/channel pipeline.

This skill owns the first two when external processes are involved.
`go-concurrency-pipelines` owns in-process channel topology, backpressure,
worker lifecycle, and iterator-backed streaming.

A process pipeline can be modeled as an ordered collection of steps that share a
small execution contract. Each step owns:

- A stable name for errors and logs.
- Executable and argument vector.
- Working directory and environment.
- Output policy.
- Cancellation or timeout policy.

Sequential pipelines usually fail fast: stop after the first failed step, return
its structured error, and do not report later steps as successful.

OS pipelines are different from workflow pipelines. For `producer | consumer`,
connect the producer's stdout to the consumer's stdin, start consumers before
producers where appropriate, and wait for every process.

## Contexts and Timeouts

Contexts communicate cancellation and deadlines across a call tree. Prefer
accepting a parent `context.Context` from the caller, then derive a timeout only
for the operation that needs one.

Always call the cancellation function returned by `context.WithCancel` or
`context.WithTimeout`, typically with `defer cancel()`. After execution fails,
inspect `ctx.Err()` or use `errors.Is` to distinguish cancellation and deadline
expiration from ordinary process failure.

Cancellation must cover the real process topology. Killing the directly started
process may not automatically clean up descendants or remote work.

## Signals and Graceful Shutdown

SIGINT and SIGTERM commonly mean “stop work and exit cleanly.” Signal handling
should begin cancellation, allow owned resources to close, and return a
non-success status if the requested work did not complete.

Signal delivery is asynchronous. A buffer of one prevents the first notification
from depending on an immediately ready receiver. Stop or cancel signal
registration when it is no longer needed.

The clean architecture is:

1. Convert termination signals into context cancellation.
2. Pass the context through the pipeline and every external command.
3. Stop starting new steps once cancellation is observed.
4. Wait for active work to finish or be terminated.
5. Return an error that identifies interruption.

Merely returning from a signal-selecting function while a worker goroutine and
child process continue is not graceful shutdown.

Any goroutine coordinating process pipe readers inherits the same
cancel-and-join obligation as the processes it supervises.

## Testing Boundaries

Use two complementary strategies:

- Integration tests run real commands against isolated, reproducible resources.
- Unit tests inject a command runner or command factory to simulate success,
  exit failure, output conditions, cancellation, and timeouts.

Keep fixtures under `testdata`, create temporary resources through `testing.T`,
register cleanup immediately, and never point tests at a real remote or mutable
user resource.

## Source Traceability

- *Executing External Programs* and *Handling Errors*, Chapter 6, lines
  9075-9374.
- *Defining a Pipeline* through *Handling Output from External Programs*,
  Chapter 6, lines 9611-10290.
- *Running Commands with Contexts* through *Handling Signals*, Chapter 6, lines
  10298-11769.
- *Wrapping Up*, Chapter 6, lines 11797-11801.
