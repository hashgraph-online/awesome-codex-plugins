# Go CLI Process Control Patterns

Reusable structures for commands, workflows, cancellation, and tests.

## Pattern: Command Specification Plus Runner

Separate declarative command data from the mechanism that starts processes.

```go
type CommandSpec struct {
	Name   string
	Args   []string
	Dir    string
	Env    []string
	Stdin  io.Reader
	Stdout io.Writer
	Stderr io.Writer
}

type Result struct {
	ExitCode int
}

type Runner interface {
	Run(context.Context, CommandSpec) (Result, error)
}
```

Use this when several commands share execution policy or tests must inspect
commands without launching them.

Benefits:

- Centralized environment, stream, timeout, and error policy.
- Fakes record argv and directory and can write controlled stdout and stderr.

Consideration: expose only options the application needs; mirroring every
`exec.Cmd` field produces a leaky abstraction.

## Pattern: Sequential Fail-Fast Workflow

Run ordered steps, stop at the first failure, and retain step identity.

```go
type Step interface {
	Name() string
	Run(context.Context) error
}

func runAll(ctx context.Context, steps []Step) error {
	for _, step := range steps {
		if err := ctx.Err(); err != nil {
			return err
		}
		if err := step.Run(ctx); err != nil {
			return &StepError{Step: step.Name(), Err: err}
		}
	}
	return nil
}
```

Use for build, test, lint, packaging, or migration workflows where later steps
depend on earlier success.

## Pattern: Bounded Capture

Retain enough diagnostic output without allowing a noisy child to consume
unbounded memory.

```go
type limitedBuffer struct {
	w io.Writer
	n int64
}

func (l *limitedBuffer) Write(p []byte) (int, error) {
	original := len(p)
	if l.n <= 0 {
		return original, nil
	}
	if int64(len(p)) > l.n {
		p = p[:l.n]
	}
	n, err := l.w.Write(p)
	l.n -= int64(n)
	if err != nil {
		return n, err
	}
	return original, nil
}
```

Prefer a tested reusable limiter or streaming parser in production. Use direct
`bytes.Buffer` capture only when output is known to be small.

## Pattern: Context-Owned Process

Tie the immediate child process to the same lifecycle as the CLI operation.

```go
func execute(ctx context.Context, spec CommandSpec) error {
	cmd := exec.CommandContext(ctx, spec.Name, spec.Args...)
	cmd.Dir = spec.Dir
	cmd.Env = append(os.Environ(), spec.Env...)

	if err := cmd.Run(); err != nil {
		if ctxErr := ctx.Err(); ctxErr != nil {
			return ctxErr
		}
		return err
	}
	return nil
}
```

Use for commands that can block on network, locks, user input, or large work.
`exec.CommandContext` does not guarantee descendant cleanup. When the child can
spawn descendants, combine this with a platform adapter for process groups on
Unix and Job Objects or an equivalent owned-tree mechanism on Windows.

## Pattern: Native Process Pipeline

Connect commands without shell parsing.

```go
producer := exec.CommandContext(ctx, "generate", "--json")
consumer := exec.CommandContext(ctx, "validate", "-")

pipe, err := producer.StdoutPipe()
if err != nil { return err }
consumer.Stdin = pipe

if err := consumer.Start(); err != nil { return err }
if err := producer.Run(); err != nil { return err }
if err := consumer.Wait(); err != nil { return err }
```

Production code must also route stderr and ensure a started consumer is reaped
when producer startup or execution fails. For larger pipelines, use a
coordinator that cancels and waits for every started stage.

## Pattern: Isolated Real-Command Test

Exercise the actual executable against disposable local state.

Steps:

1. Check the executable with `exec.LookPath`.
2. Create state with `t.TempDir`.
3. Register cleanup immediately with `t.Cleanup`.
4. Configure local-only endpoints and deterministic identity.
5. Run the command and assert state plus output.
6. Never reuse the user's repository, credentials, or remote.

Use when argv, filesystem behavior, or interoperability with the real tool is
the behavior under test.

## Pattern: Injected Fake

Simulate failures that are slow, rare, unsafe, or unavailable.

Have a fake runner:

- Record `CommandSpec`.
- Return a configured error.
- Write configured stdout and stderr.

Prefer a per-test fake instance over replacing a package-level function.

## Pattern: Signal-to-Context Lifecycle

Unify OS termination with normal cancellation.

1. Create a signal-aware context at the executable boundary.
2. Defer removal of signal handling.
3. Pass the context to all steps.
4. On cancellation, stop scheduling and cancel active subprocesses.
5. Close resources and wait for workers.
6. Map interruption to a stable non-zero CLI result.

## Pattern Selection Guide

| Situation | Pattern |
|---|---|
| Many external commands | Command Specification Plus Runner |
| Ordered automation | Sequential Fail-Fast Workflow |
| Potentially large diagnostics | Bounded Capture |
| Network or blocking command | Context-Owned Process |
| `producer | consumer` semantics | Native Process Pipeline |
| Verify real tool integration | Isolated Real-Command Test |
| Simulate timeout or failure | Injected Fake |
| Graceful Ctrl+C / termination | Signal-to-Context Lifecycle |

## Source Traceability

- *Defining a Pipeline* and *Adding Another Step to the Pipeline*, Chapter 6,
  lines 9611-9967.
- *Handling Output from External Programs* and *Running Commands with
  Contexts*, Chapter 6, lines 9975-10534.
- *Integration Tests with a Local Git Server* and *Testing Commands with Mock
  Resources*, Chapter 6, lines 10600-11375.
- *Handling Signals*, Chapter 6, lines 11383-11769.
