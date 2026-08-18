# Go CLI Testing Rules

Actionable rules for reliable, maintainable command tests.

## Core Rules

### 1. Test observable behavior at the narrowest boundary

- Call pure functions directly.
- Test command actions through injected dependencies.
- Build the binary only for behavior that exists at the executable boundary.
- Do not retest a dependency's internal behavior.

### 2. Keep process globals out of command logic

Do not read `os.Args`, global flags, standard streams, environment, or the
current directory deep inside business logic. Parse and resolve them at the
edge, then pass values inward.

### 3. Separate stdout and stderr

Capture each stream independently. Assert that successful data goes to stdout
and diagnostics go to stderr. For agent-facing commands, also assert stable
structured output and exit codes.

### 4. Isolate every mutable resource

- Use `t.TempDir()` instead of fixed temporary paths.
- Use `t.Setenv()` instead of mutating the environment without restoration.
- Start local servers on assigned ports with `httptest`.
- Give database and repository tests independent state.
- Register cleanup immediately with `t.Cleanup`.

Never let a test delete or overwrite developer data.

### 5. Make table rows describe behavior classes

Each row should name a distinct condition: success, empty input, invalid input,
boundary value, dependency failure, or cancellation. Avoid tables that merely
enumerate values without increasing behavioral coverage.

### 6. Mark helpers and fail at the right level

Call `t.Helper()` in setup and assertion helpers. Use `t.Fatal` only when later
assertions cannot run safely; use `t.Error` to report independent failures.

### 7. Assert errors by identity

Use `errors.Is` for sentinel or wrapped errors and `errors.As` for typed errors.
Compare text only when the exact diagnostic is part of the CLI contract.

### 8. Model external commands explicitly

Prefer a small runner interface or injected function. Use a helper process when
you must test `exec.Cmd` behavior such as exit codes, signals, or context
cancellation. Always restore package-level substitutions with `t.Cleanup`.

### 9. Validate both sides of an HTTP contract

For clients, assert method, path, query, headers, and body as well as the
interpreted response. For servers, exercise the real mux with `httptest.Server`
when routing is part of the behavior. Always close response bodies.

### 10. Gate live and platform-dependent tests

Opt-in tests that require a live API, installed command, desktop notification,
specific OS, or destructive operation. State prerequisites clearly and skip
with a reason when they are absent.

- Use environment-gated `t.Skip` when visibility of the skipped test matters.
- Use `testing.Short()` for expensive tests regardless of dependency category.
- Require every build constraint to map to a named CI lane.

### 11. Make live tests uniquely identifiable and reversible

Generate a unique resource name, record the created identifier, verify identity
before mutation, and register best-effort cleanup before continuing the flow.
Do not depend on subtest order without explicit state guards.

### 12. Run the right quality checks

At minimum:

```sh
go test ./...
go test -race ./...
```

For uncached opt-in integration tests:

```sh
go test -count=1 -tags=integration ./...
```

Add fuzzing or platform CI where input parsing or OS behavior warrants it.

### 13. Reconstruct framework and configuration state per test

- Call the real root command factory for each case; never reuse an executed tree.
- Build a typed configuration value per test and pass it through dependencies.
- Avoid shared Viper instances, package-level flag state, and singleton clients.
- Assert the returned `Execute` error, stdout, stderr, and dependency calls.

### 14. Treat build profiles as a matrix

- Compile and test every supported build-tag or capability combination.
- Test safe behavior when a capability is disabled.
- Never treat a build tag as authentication or authorization.
- Smoke-test the final archived binary, not only packages.

## Guidelines

- Prefer one high-value end-to-end flow over many slow binary tests.
- Use golden files for large stable output; provide an explicit update mode.
- Compare floats with a documented tolerance, not direct equality.
- Compare complex values semantically; avoid assertions coupled to field order.
- Use deadlines for network and child-process tests so failures terminate.
- Do not call `t.Parallel()` when tests share global replacements or process state.
- Test adapters separately when multiple implementations satisfy one interface.
- Use `Errorf` when later assertions remain safe; use `Fatalf` only when the
  current test or subtest cannot continue.
- Include the triggering input and `got, want` values in failures.
- Treat each table row as a subtest when independent execution and `-run`
  selection add value.
- Check the language version before adding `tc := tc`; it is redundant for
  variables declared by loops under Go 1.22+ semantics.
- Preserve and replay the seed printed by a failed `-shuffle` run.
- Prefer external-package tests for exported contracts and same-package tests
  only for justified internal invariants.
- Reserve `TestMain` for expensive package-wide fixtures and preserve the
  `m.Run()` exit code through teardown.
- Do not use `T.Setenv` or change the process working directory beneath a
  parallel test or parallel ancestor.
- Distinguish `-parallel` test-binary scheduling from `-p` package concurrency.
- Use coverage to locate unexercised statements, not to claim correctness.
- Route benchmark and profiling work to `go-performance-testing`.
- Apply the production migration path in real SQL-adapter tests.
- Use `httptest.NewRequest` for inbound handlers and a `RoundTripper` fake for
  outbound client behavior.

## Exceptions

- **Tiny one-file utility**: a subprocess test may be cheaper than introducing
  architecture solely for testing, but still isolate files and environment.
- **Generated framework wiring**: test your action functions and one smoke path;
  do not exhaustively retest generated code.
- **Third-party API contract**: retain a small live contract test when local
  fixtures can drift, but keep frequent tests local.
- **User-visible prose**: assert key facts rather than every character unless
  compatibility requires exact output.

## Quick Reference

| Concern | Rule |
|---|---|
| Streams | Inject and assert stdout/stderr separately |
| Files | `t.TempDir`, `testdata`, immediate cleanup |
| Errors | `errors.Is` / `errors.As` |
| Processes | Runner seam or helper process |
| HTTP | `httptest`, assert request and response |
| Integration | Explicit tag, unique data, no cache |
| Concurrency | Race test; avoid shared globals |
| Language invariants | Discover with `go-language-correctness`, prove here |

## Source Traceability

Paraphrased from testing sections in Chapters 1–11, using the normalized source
ranges 688–763, 1644–1846, 3006–3559, 4790–5447, 6963–7520, 9382–9610,
10600–11382, 13236–13698, 15665–15884, 17377–17698, 18335–18588,
18982–19465, 20212–20710, 23064–23160, and 24645–24971.
