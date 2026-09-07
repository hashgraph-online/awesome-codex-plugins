# Go CLI Testing Checklist

Use when implementing or reviewing tests for a Go command-line application.

## Test Design

- [ ] Each test names an observable behavior, not an implementation detail.
- [ ] The narrowest layer that proves the behavior is used.
- [ ] Success, empty, invalid, boundary, and dependency-failure cases are covered.
- [ ] Table rows represent distinct behavior classes.
- [ ] Wrapped or typed errors are asserted with `errors.Is` or `errors.As`.
- [ ] Floating-point comparisons use a documented tolerance.

## Command Architecture

- [ ] `main` is limited to parsing, wiring, reporting, and exit selection.
- [ ] Command logic returns errors instead of calling `os.Exit`.
- [ ] Parsed arguments and configuration are passed explicitly.
- [ ] stdin, stdout, and stderr can be injected.
- [ ] Filesystem, clock, process, HTTP, and repository dependencies have narrow seams.
- [ ] Every case constructs a fresh command tree.
- [ ] Every case receives its own typed configuration and dependency bundle.
- [ ] Tests assert the `Execute` error as well as stdout and stderr.

## CLI Contract

- [ ] Successful pipeable output is on stdout.
- [ ] Diagnostics are on stderr.
- [ ] Exit codes are tested at the executable boundary.
- [ ] JSON or other machine output is decoded and asserted semantically.
- [ ] Help, invalid flags, and missing arguments have smoke coverage.
- [ ] Output ordering is deterministic where users or agents depend on it.

## Filesystem and Environment

- [ ] Mutable files live under `t.TempDir()`.
- [ ] Static fixtures live under `testdata/`.
- [ ] Paths are built with `filepath`.
- [ ] Environment changes use `t.Setenv`.
- [ ] Tests do not depend on the user's home, current data, locale, or timezone.
- [ ] Destructive tests verify their target is inside an owned temporary directory.
- [ ] Cleanup is registered immediately after resource creation.

## Helpers and Fixtures

- [ ] Setup and assertion helpers call `t.Helper()`.
- [ ] Helpers create only the state requested by the test.
- [ ] Golden values omit or normalize timestamps, random IDs, and absolute paths.
- [ ] Golden updates require an explicit flag and review.
- [ ] Failed setup stops the test before mutation or assertions.
- [ ] Package-wide `TestMain` is used only when per-test ownership is impractical.
- [ ] `TestMain` preserves `m.Run()` status and always performs teardown.
- [ ] Exported contracts have deliberate external-package coverage.

## Processes

- [ ] External command availability is checked or the command is replaced.
- [ ] Command name, argument boundaries, environment, and working directory are tested.
- [ ] Nonzero exit, stderr, timeout, and cancellation paths are covered.
- [ ] Helper processes are guarded against ordinary test execution.
- [ ] Contexts have deadlines.
- [ ] Injected package-level functions are restored with `t.Cleanup`.
- [ ] Tests that mutate globals are not parallel.

## HTTP and Network

- [ ] Local tests use `httptest` or another owned local server.
- [ ] Client tests assert method, path, query, headers, and body.
- [ ] Server tests include mux/routing when routing behavior matters.
- [ ] Status codes and response bodies are both validated.
- [ ] Response bodies and test servers are closed.
- [ ] Unreachable, malformed, empty, and error responses are covered.
- [ ] Clients and servers have timeouts.
- [ ] Function-backed transports are used when real HTTP semantics are unnecessary.
- [ ] Fake responses have status, headers, request, and a non-nil closable body.

## Repositories and Databases

- [ ] Domain tests target a small repository interface.
- [ ] Every test gets fresh repository state.
- [ ] Real adapter tests exist in addition to in-memory fake tests.
- [ ] Shared behavior is exercised through a conformance suite where practical.
- [ ] Database files, connections, and transactions are cleaned up.

## Integration Tests

- [ ] Live tests are opt-in and clearly tagged.
- [ ] Current build-constraint syntax is used.
- [ ] Required endpoints, tools, credentials, and permissions are documented.
- [ ] Missing prerequisites cause an explained skip, not an ambiguous pass.
- [ ] Created data has a unique identifier.
- [ ] Cleanup is registered before later assertions can fail.
- [ ] Identity is rechecked before destructive mutation.
- [ ] Live runs disable test caching when freshness matters.
- [ ] The suite avoids modifying real user or production data.

## Verification

- [ ] `go test ./...`
- [ ] `go test -race ./...`
- [ ] `go vet ./...` or the repository's standard lint command
- [ ] `go test -count=1 -tags=integration ./...` in the approved environment
- [ ] Relevant OS and architecture jobs run in CI
- [ ] Repeated local runs pass independently and in shuffled order
- [ ] The shuffle seed is retained in CI output and can be replayed.
- [ ] Normal, short, integration, race, shuffle, and supported build-profile
      lanes are explicit.
- [ ] Every supported build-tag or capability profile compiles and runs tests.
- [ ] Final archived or installed artifact behavior receives a smoke test.

## Red Flags

Stop and redesign if:

- a test writes a fixed file in the repository or home directory;
- subtests depend on hidden state established by earlier subtests;
- a live test can delete data it did not create and verify;
- assertions pass only because stdout and stderr were combined;
- a mock duplicates so much protocol logic that it can drift silently;
- sleeps are used as synchronization instead of events, contexts, or eventual checks;
- test code leaves a package-level command function replaced;
- ordinary `go test ./...` contacts the internet or launches desktop UI.

## Streams and Async Behavior

- [ ] Reader contracts are exercised with fragmented, failing, or timed-out input.
- [ ] Writer contracts cover partial or truncated output when material.
- [ ] Asynchronous tests use barriers, controlled clocks, or version-gated
      `testing/synctest` rather than arbitrary sleeps.
- [ ] Every goroutine joins before its test returns.

## Coverage, Parallelism, and Specialized Boundaries

- [ ] Coverage scope is named and covered paths contain meaningful assertions.
- [ ] Each parallel test owns files, ports, databases, fixtures, and mutable state.
- [ ] Parallel tests do not mutate environment or working directory globally.
- [ ] Race results are described as applying to the exercised workload.
- [ ] Parser tests cover help, `--`, operand ordering, defaults, and diagnostics.
- [ ] Streaming HTTP tests cover early EOF, partial body, oversize, close, and cancellation.
- [ ] Concurrency tests cover early stop, blocked downstream, closure, and limits.
- [ ] SQL adapter tests apply production migrations and use the real driver.
- [ ] Benchmarks and profiles are routed to `go-performance-testing`.

## Quick Reference

| Aspect | Ideal | Acceptable | Red flag |
|---|---|---|---|
| State | Per-test owned | Read-only fixture | Shared mutable user state |
| Doubles | Narrow boundary | Local server | Remote service by default |
| Output | Semantic contract | Small exact string | Incidental formatting |
| Timing | Event/deadline based | Bounded polling | Unexplained sleep |
| Integration | Tagged and reversible | Explicit manual run | Automatic destructive call |

## Source Traceability

Synthesized from testing guidance across the book:

- Basic unit and executable testing, normalized lines 688–763 and 1644–1846.
- Golden files, temporary files, and stream injection, normalized lines
  3006–3559.
- Table tests, helpers, filesystem cleanup, and error cases, normalized lines
  4790–5447 and 6963–7520.
- Process setup, local Git, and command doubles, normalized lines 9382–9610 and
  10600–11382.
- CLI actions and HTTP test servers, normalized lines 13236–13698,
  15665–15884, 17377–17698, and 18335–18588.
- Live integration, repositories, and platform-specific tests, normalized lines
  18982–19465, 20212–20710, 23064–23160, and 24645–24971.
