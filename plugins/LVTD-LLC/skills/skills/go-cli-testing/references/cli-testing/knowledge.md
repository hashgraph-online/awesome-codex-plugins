# Go CLI Testing Knowledge

Core concepts for testing command-line applications at the narrowest useful boundary.

## Behavior Boundaries

A CLI has several observable boundaries. Test each at the cheapest layer that proves the behavior.

| Boundary | Observable behavior | Preferred seam |
|---|---|---|
| Pure logic | Values and errors | Direct function call |
| Command action | stdout, stderr, state changes | Injected streams and dependencies |
| Filesystem | Created, changed, or removed paths | `t.TempDir` and fixture builders |
| Process | arguments, exit status, cancellation | Runner interface or helper process |
| HTTP | request method, path, headers, body, response | `httptest.Server` |
| Repository | domain behavior across storage backends | Small repository interface |
| Executable | parsing, wiring, exit code, OS behavior | Build and invoke the binary |
| Live service | Contract compatibility | Opt-in integration test |

Do not repeat the same assertion at every layer. Unit tests should cover decision
logic and failures; a few integration tests should prove that wiring and external
contracts hold.

## Testable Command Shape

Keep `main` small. Put command behavior in a function that:

- accepts parsed configuration instead of reading global flags;
- accepts `io.Reader` and `io.Writer` values instead of using process globals;
- receives filesystem, clock, process, HTTP, or repository dependencies;
- returns an error or exit-code value instead of calling `os.Exit`.

This creates a seam where tests can supply `strings.Reader`, `bytes.Buffer`,
temporary paths, and fakes. The production entry point supplies `os.Stdin`,
`os.Stdout`, `os.Stderr`, and real adapters.

## Streams as Public Contracts

For a CLI, output is an API. Tests should distinguish:

- **stdout**: successful, pipeable command results;
- **stderr**: diagnostics and warnings;
- **stdin**: scripted or piped input;
- **exit status**: machine-readable success or failure.

Inject streams so tests can assert their content independently. Exact output
assertions are appropriate for stable machine formats and small messages.
Prefer semantic checks for prose whose wording is intentionally flexible.

## Resource Isolation

Tests must not depend on prior runs, a developer's home directory, or shared
services.

- Use `t.TempDir()` for mutable filesystem state.
- Keep immutable fixtures in `testdata/`; Go tooling excludes that directory
  from normal package builds.
- Register cleanup as soon as a resource is created.
- Give every test its own database, repository, server, and environment values.
- Use `t.Setenv` for process environment changes.

Dynamic fixtures suit destructive behavior; checked-in fixtures and golden
files suit stable, complex input or output.

## Test Doubles

Choose the smallest double that models the boundary:

- **Fake**: an in-memory implementation with real behavior, such as a repository.
- **Stub**: returns a predetermined value or error.
- **Spy**: records calls for later assertions.
- **Helper process**: runs the test binary as a controlled child process.
- **Local server**: implements a protocol realistically without a remote network.

Interfaces work best when owned by the consumer and limited to the methods the
command needs. A function field can be enough for a single operation.

## Test Layers

Classify each test on three independent axes:

1. dependency boundary: unit, local integration, or live contract;
2. execution cost: normal or skipped under `testing.Short`;
3. capability/build profile: default or explicit build constraints.

Combining these axes keeps expensive tests visible without making build tags a
substitute for runtime cost or dependency classification. Every build profile
must map to an actual CI lane.

### Unit

Fast, deterministic tests of functions and action handlers. Use table tests for
meaningful input classes, including failure paths.

### Component

Exercise a command action with real parsing or a real local adapter, while
replacing remote or destructive boundaries.

### Executable

Build and run the actual binary to verify argument parsing, stream routing, exit
codes, and platform-specific naming. These tests are slower and should use
isolated working directories.

### Live Integration

Exercise an actual service or operating-system feature only when a local double
cannot establish compatibility. Gate these tests explicitly, use unique data,
and clean up even after partial failure.

## Failure-Oriented Testing

Successful examples are insufficient for CLIs because many important behaviors
occur at boundaries. Deliberately test:

- unreadable input and short or timed-out reads;
- missing files and invalid configuration;
- child-process nonzero exits and cancellation;
- malformed HTTP responses and unavailable servers;
- partial state transitions and failed cleanup;
- wrapped errors with `errors.Is` or typed errors.

Avoid comparing error strings when the program exposes a stable error identity.

## Coverage and Parallel Semantics

Go coverage reports executed statements, not whether assertions proved the
behavior. Name the scope being measured: one package, `./...`, or a broader
`-coverpkg` set. Use uncovered code to discover missing behavior classes after
correctness tests exist.

A parallel subtest pauses at `t.Parallel` and resumes after its parent test
function returns. Sibling parallel subtests can overlap without marking the
parent parallel. A parallel parent additionally permits the entire group to
overlap other parallel top-level tests.

`t.Setenv` and process working-directory changes are incompatible with parallel
tests or parallel ancestors. The race detector reports races only on executed
paths; a clean run is bounded evidence.

Performance benchmarks, allocation measurement, profiles, and statistical
comparison belong to `go-performance-testing`.

For modules declaring Go 1.22 or newer, loop variables declared by a loop are
new per iteration. Older language versions and assignment to predeclared loop
variables retain shared-variable behavior. Determine this from the module or
file language version, not only the installed toolchain.

External `_test` packages prove exported behavior from a consumer's view.
Same-package tests remain useful for justified internal invariants. Prefer
per-test setup and `t.Cleanup`; reserve `TestMain` for expensive package-wide
fixtures whose safe sharing is explicit.

## Specialized Boundaries

- Parser tests use a fresh `FlagSet` or command tree and distinguish help,
  syntax, validation, and effect wiring.
- Inbound HTTP handler and lifecycle tests route to
  `go-http-server-applications`; function-backed `RoundTripper` fakes model
  outbound clients.
- Concurrent lifecycle tests use barriers and deadlines, not sleeps.
- Repository fakes prove consumer behavior; real-driver tests prove SQL,
  constraints, conversions, transactions, and pool behavior.

## Source Traceability

Paraphrased from testing sections of *Powerful Command-Line Applications in
Go*, using normalized source ranges 688–763, 1644–1846, 3006–3559,
4790–5447, 6963–7520, 9382–9610, 10600–11382, 13236–13698,
15665–15884, 17377–17698, 18335–18588, 18982–19465, 20212–20710,
23064–23160, and 24645–24971.
