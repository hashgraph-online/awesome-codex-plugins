# Go CLI Testing Patterns

Reusable patterns and selection guidance for command-line tests.

## Pattern: Functional Core, Command Shell

Keep flag parsing and process termination in a thin shell while testing behavior
through a regular function.

### Structure

```go
func run(ctx context.Context, cfg Config, io IO, deps Deps) error
```

### Use When

- `main` contains decisions or filesystem/network work.
- Tests currently replace `os.Stdout`, `os.Args`, or global flags.
- The command needs both human and structured output.

Do not create a large dependency container for a tiny command. Pass only the
dependencies the behavior actually uses.

## Pattern: Table of Behavioral Equivalence Classes

Exercise branches without repeating setup and assertions.

### Structure

```go
tests := []struct {
	name    string
	input   Input
	want    Output
	wantErr error
}{/* one row per behavior class */}
```

### Use When

- The same operation has meaningful variants.
- Success and failure paths share execution mechanics.

### Considerations

Prefer named fields and descriptive row names. Capture the range variable safely
when supporting older Go versions or when parallelizing subtests.

## Pattern: Parallel Subtest Group

Build immutable shared fixtures in the parent and allocate mutable resources
inside each subtest before calling `t.Parallel`. Do not use process-global
environment or working-directory mutations. Mark the parent parallel only when
the whole group may overlap other top-level tests.

## Pattern: Concurrent Lifecycle Test

Inject work functions and coordinate them with barrier channels. Assert maximum
active work, cancellation, early consumer exit, channel closure, and completion
without asserting incidental schedule order. Run the exercised path under the
race detector.

## Pattern: Parser Harness

Construct fresh parser options and a fresh `FlagSet` or command tree. Capture
parser diagnostics separately. Cover `--`, missing and extra operands, defaults,
help, malformed custom values, and dependency calls.

## Pattern: Real SQL Adapter

Create an isolated database, apply production migrations, exercise the concrete
adapter, and clean up. Use unique files, databases, or schemas under
`t.Parallel`. An in-memory fake remains valuable for consumers but cannot prove
SQL syntax, constraints, driver codes, transactions, or pooling.

## Pattern: Fixture Builder with Owned Cleanup

Create mutable test resources independently for each test.

### Structure

```go
func newWorkspace(t *testing.T, files map[string]string) string {
	t.Helper()
	root := t.TempDir()
	// create requested files beneath root
	return root
}
```

### Use When

- The command writes or deletes files.
- Checked-in fixtures would be mutated.
- Setup is repeated across tests.

### Considerations

Validate joined paths remain under the temporary root when fixture names can
come from test data.

## Pattern: Golden Output

Review a large stable output artifact as a file rather than embedding it in test
code.

### Use When

- Output is HTML, JSON, generated documentation, or a long report.
- A textual diff is useful during review.

### Considerations

Normalize nondeterministic fields first. Make updates opt-in, review golden-file
diffs, and avoid goldens for small values that are clearer inline.

## Pattern: Consumer-Owned Port

Replace one external capability with a fake while keeping domain logic real.

### Structure

```go
type Store interface {
	Load(context.Context, string) (Item, error)
	Save(context.Context, Item) error
}
```

### Use When

- Multiple storage implementations should pass the same behavior suite.
- A remote dependency makes failures slow or irreproducible.

### Considerations

Keep the interface narrow. Run separate adapter contract tests so an in-memory
fake does not conceal real database behavior.

## Pattern: Local Protocol Server

Test a network client or server over a real local protocol connection without a
remote service.

### Use When

- HTTP routing, encoding, headers, or status handling matter.
- A fake client would bypass too much production behavior.

### Considerations

Assert incoming requests inside the handler. Use the server's client and URL;
close the server and all response bodies.

## Pattern: Helper Process

Simulate an executable with controlled stdout, stderr, exit status, delay, or
signal behavior by re-entering the test binary.

### Use When

- The code must exercise `exec.Cmd` itself.
- A runner fake cannot prove cancellation or process semantics.

### Considerations

Guard the helper with an environment variable, pass an unambiguous separator
before simulated arguments, set timeouts, and restore any injected command
factory. Never run these tests in parallel while sharing a package variable.

```go
func TestHelperProcess(t *testing.T) {
	if os.Getenv("GO_HELPER_PROCESS") != "1" {
		return
	}
	args := argsAfter(os.Args, "--")
	runScriptedHelper(args, os.Stdout, os.Stderr) // may call os.Exit
}

cmd := exec.CommandContext(ctx, os.Args[0],
	"-test.run=TestHelperProcess", "--", "stderr=warning", "exit=7")
cmd.Env = append(os.Environ(), "GO_HELPER_PROCESS=1")
```

The parent must assert stdout, stderr, `*exec.ExitError`, cancellation or signal
synchronization, and eventual process completion. Give the helper an explicit
protocol and a hard deadline.

## Pattern: Layered Contract Verification

Use fast local tests continuously and a small live suite to detect external API
drift.

### Structure

1. Unit tests cover formatting, errors, and response interpretation.
2. `httptest` tests validate requests and modeled responses.
3. Tagged live tests verify only the critical contract.

### Considerations

Live tests need unique data, cleanup, credentials supplied outside source,
timeouts, and `-count=1` when a fresh request is required.

## Pattern: Backend Conformance Suite

Run the same behavioral tests against memory, file, and database repositories.

### Structure

```go
func repositoryContract(t *testing.T, open func(*testing.T) Repository) {
	t.Helper()
	// shared create/read/update/delete assertions
}
```

### Considerations

Prefer an explicit conformance function over mutually exclusive test files when
all backends can run cheaply in one invocation.

## Pattern: Function-Backed HTTP Transport

Use a small function type implementing `http.RoundTripper` to inspect a request
and return an exact response without a live server. Include a non-nil closable
body. Prefer `httptest.Server` when redirects, streaming, TLS, or routing matter.

## Pattern: Fresh Command Factory

Construct the root tree, streams, typed settings, and fakes inside each case.
Set arguments and call `ExecuteContext`; assert error plus both streams.

## Pattern: Capability Profile Matrix

Represent supported build tags as a version-controlled table:

| Profile | Tags | Selected files | Test command | Artifact | Smoke command | Support |
|---|---|---|---|---|---|---|
| default | none | inspected with `go list` | `go test ./...` | standard | `tool version` | supported |
| debug | `debug` | inspected with `go list` | `go test -tags=debug ./...` | debug | protected debug probe | internal |

Include intentional unsupported combinations and the expected compile failure.
Add race lanes where behavior or concurrency differs. Run an artifact smoke test
for every supported combination.

## Pattern: Deterministic Asynchronous Test

Prefer an observable barrier or completion channel over sleeping. Bound every
wait with a deadline so a broken test terminates. Inject a per-instance clock
when time is part of application behavior.

For Go 1.25+ projects, consider `testing/synctest` when goroutines and timers
form a self-contained test bubble. Do not assume external network I/O becomes
durably blocked inside that bubble; use ordinary dependency seams for external
effects.

## Pattern: Adversarial Stream

Use `testing/iotest` to exercise stream contracts:

- `iotest.TestReader` for a custom reader implementation;
- `OneByteReader` and `HalfReader` for fragmented reads;
- `ErrReader` and `TimeoutReader` for failures;
- `TruncateWriter` for partial output.

Fragmentation is not a blanket reason to retry. Retryability must be part of
the production stream contract.

## Pattern Selection Guide

| Situation | Pattern |
|---|---|
| Logic trapped in `main` | Functional Core, Command Shell |
| Repeated input variants | Behavioral Equivalence Table |
| Writes or deletes files | Fixture Builder |
| Large deterministic output | Golden Output |
| External storage or command | Consumer-Owned Port |
| HTTP or local protocol | Local Protocol Server |
| Must exercise `exec.Cmd` | Helper Process |
| Remote API may drift | Layered Contract Verification |
| Multiple repositories | Backend Conformance Suite |
| Sleep-based asynchronous test | Deterministic Asynchronous Test |
| Parser assumes full reads or writes | Adversarial Stream |

## Source Traceability

- CLI integration, golden files, and stream interfaces, normalized lines
  1644–1846 and 3006–3559.
- Table tests and helper-created files, normalized lines 4790–5447 and
  6963–7520.
- Local Git and helper-process command tests, normalized lines 9382–9610 and
  10600–11382.
- HTTP server/client doubles and live integration, normalized lines
  15665–15884, 17377–17698, 18335–18588, and 18982–19465.
- Interchangeable repository and platform integration tests, normalized lines
  20212–20710, 23064–23160, and 24645–24971.
