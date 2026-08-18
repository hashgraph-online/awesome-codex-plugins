# Go CLI Process Control Examples

Compact, original examples of safe subprocess execution and lifecycle handling.

## Direct Execution

### Before: shell-shaped argument

```go
cmd := exec.Command("git push origin " + branch)
err := cmd.Run()
```

The executable lookup receives the entire string as a program name. If changed
to `sh -c`, the same construction would also make `branch` an injection risk.

### After: explicit argv and context

```go
func push(ctx context.Context, dir, branch string, stderr io.Writer) error {
	cmd := exec.CommandContext(ctx, "git", "push", "origin", branch)
	cmd.Dir = dir
	cmd.Stderr = stderr
	if err := cmd.Run(); err != nil {
		return fmt.Errorf("git push %q: %w", branch, err)
	}
	return nil
}
```

Arguments are unambiguous, the working directory is explicit, diagnostics are
injectable, and cancellation belongs to the caller.

## Output-Defined Failure

```go
func checkFormat(ctx context.Context, dir string) error {
	cmd := exec.CommandContext(ctx, "gofmt", "-l", ".")
	cmd.Dir = dir

	out, err := cmd.Output()
	if err != nil {
		return fmt.Errorf("run gofmt: %w", err)
	}
	if files := strings.TrimSpace(string(out)); files != "" {
		return fmt.Errorf("files require formatting: %s", files)
	}
	return nil
}
```

This separates process failure from the domain rule that non-empty output means
the source tree is not formatted.

## Structured Step Errors

```go
type StepError struct {
	Step string
	Err  error
}

func (e *StepError) Error() string {
	return fmt.Sprintf("%s failed: %v", e.Step, e.Err)
}

func (e *StepError) Unwrap() error { return e.Err }
```

Callers can use `errors.As(err, &stepErr)` to find the failed step and
`errors.Is(err, context.DeadlineExceeded)` to inspect the preserved cause.

## Timeout Derived from the Caller

```go
func runLimited(ctx context.Context, limit time.Duration) error {
	ctx, cancel := context.WithTimeout(ctx, limit)
	defer cancel()

	err := exec.CommandContext(ctx, "worker", "--once").Run()
	if err != nil && ctx.Err() != nil {
		return fmt.Errorf("worker interrupted: %w", ctx.Err())
	}
	if err != nil {
		return fmt.Errorf("worker failed: %w", err)
	}
	return nil
}
```

The operation preserves upstream cancellation and reports why execution ended.

## Signal-Aware Main

```go
func main() {
	ctx, stop := signal.NotifyContext(
		context.Background(),
		os.Interrupt,
		syscall.SIGTERM,
	)
	defer stop()

	if err := run(ctx, os.Stdout, os.Stderr); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
```

`run` and every command it starts must accept the same context. Receiving a
termination signal therefore cancels active work instead of abandoning it.

## Injectable Runner

```go
type Runner interface {
	Run(ctx context.Context, spec CommandSpec) (Result, error)
}

type ExecRunner struct{}

func (ExecRunner) Run(ctx context.Context, spec CommandSpec) (Result, error) {
	cmd := exec.CommandContext(ctx, spec.Name, spec.Args...)
	cmd.Dir, cmd.Stdin = spec.Dir, spec.Stdin
	cmd.Stdout, cmd.Stderr = spec.Stdout, spec.Stderr
	err := cmd.Run()
	return classifyProcessResult(err)
}
```

Production uses `ExecRunner`; tests supply a fake without changing package-level
state.

```go
type fakeRunner struct {
	gotName string
	gotArgs []string
	stdout  string
	stderr  string
	err     error
}

func (f *fakeRunner) Run(_ context.Context, spec CommandSpec) (Result, error) {
	f.gotName = spec.Name
	f.gotArgs = append([]string(nil), spec.Args...)
	_, _ = io.WriteString(spec.Stdout, f.stdout)
	_, _ = io.WriteString(spec.Stderr, f.stderr)
	return Result{}, f.err
}
```

## Reproducible Integration Cleanup

```go
func newTempRemote(t *testing.T) string {
	t.Helper()
	dir := t.TempDir()

	cmd := exec.Command("git", "init", "--bare", dir)
	if out, err := cmd.CombinedOutput(); err != nil {
		t.Fatalf("init temporary remote: %v\n%s", err, out)
	}
	return dir
}
```

`t.TempDir` scopes the resource to the test and guarantees cleanup.

## Source Traceability

- *Executing External Programs* and *Handling Errors*, Chapter 6, lines
  9075-9374.
- *Handling Output from External Programs* and *Running Commands with
  Contexts*, Chapter 6, lines 9975-10534.
- *Integration Tests with a Local Git Server* and *Testing Commands with Mock
  Resources*, Chapter 6, lines 10600-11375.
- *Handling Signals*, Chapter 6, lines 11383-11769.
