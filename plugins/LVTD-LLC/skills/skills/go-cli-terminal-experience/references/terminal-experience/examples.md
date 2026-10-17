# Terminal Experience Examples

## Explicit Capability Policy

```go
type Mode string

const (
	ModeHuman Mode = "human"
	ModePlain Mode = "plain"
	ModeJSON  Mode = "json"
)

type Capabilities struct {
	StdinTTY  bool
	StdoutTTY bool
	StderrTTY bool
	Color     bool
}
```

Pass `Mode` and `Capabilities` into the runner. Do not let inner packages call
`os.Stdout` or repeat environment detection.

## Per-Stream Detection

```go
func isTerminal(w io.Writer) bool {
	f, ok := w.(*os.File)
	return ok && term.IsTerminal(int(f.Fd()))
}
```

An injected `bytes.Buffer` intentionally returns false. Tests can pass an
explicit capability value when simulating a terminal.

## Unsafe vs Safe Prompting

```go
// Unsafe: blocks agents and CI.
fmt.Fscan(os.Stdin, &answer)

// Safer: policy is explicit.
if !opts.Interactive {
	return errors.New("confirmation required; rerun with --yes")
}
answer, err := prompt.Confirm(ctx, "Delete remote state?")
```

## Structured Renderer

```go
enc := json.NewEncoder(stdout)
enc.SetEscapeHTML(false)
if err := enc.Encode(result); err != nil {
	return fmt.Errorf("write JSON result: %w", err)
}
```

Keep errors returned to the process boundary. Do not print an extra prose
success line after the JSON object.
