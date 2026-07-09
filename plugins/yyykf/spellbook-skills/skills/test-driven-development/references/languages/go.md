# TDD in Go

**Load this reference when:** doing TDD in Go. The core skill is language-agnostic; this file adds only Go framework choices, idioms, anti-patterns, and tooling. Generic mock pitfalls live in [../testing-anti-patterns.md](../testing-anti-patterns.md) and are not repeated here.

## Test framework & runner

**Idiomatic approach: the standard-library `testing` package.** Go ships testing as a first-class citizen — a runner (`go test`), the `testing` package, and `go vet` all come with the toolchain. There is no idiomatic reason to reach for an external *framework*. Assertion *helpers* are a separate, contested choice (see anti-patterns). Tests live in `_test.go` files in the same package; functions are `func TestXxx(t *testing.T)`.

```bash
go test ./...                       # whole suite, all packages
go test -run TestParseAmount ./pay  # one test (-run takes a regex) in one package
go test -run TestParseAmount/negative ./pay  # one subtest (slash-separated)
go test -race ./...                 # with the race detector (see Tooling)
go test -v ./pay                    # verbose: show each test/subtest result
```

Plain `go test` is already quiet on green (`ok pkg`) and detailed on red — no quiet flag needed; reach for `-v` only to inspect a specific test, not in the normal loop.

Minimal real failing test (RED) — `pay/amount_test.go`:

```go
package pay

import "testing"

func TestParseAmount(t *testing.T) {
	got, err := ParseAmount("12.50")
	if err != nil {
		t.Fatalf("ParseAmount(\"12.50\") returned error: %v", err)
	}
	if want := 1250; got != want {
		t.Errorf("ParseAmount(\"12.50\") = %d cents, want %d", got, want)
	}
}
```

This fails to **compile** until `ParseAmount` exists — in Go a missing symbol is a build failure, which still counts as a failing test (`go test` reports it red). `t.Errorf` records the failure but continues; `t.Fatalf` stops the current test (it calls `runtime.Goexit`). Standard message form is `got = X, want Y`. ([Go: Add a Test](https://go.dev/doc/tutorial/add-a-test))

## Idioms & conventions

- **Table-driven tests + subtests.** The dominant Go pattern: a slice of cases, one `t.Run` per case. Each subtest gets its own name in failures and is independently selectable with `-run`. ([Go blog: Subtests](https://go.dev/blog/subtests))

  ```go
  func TestParseAmount(t *testing.T) {
  	tests := []struct {
  		name    string
  		in      string
  		want    int
  		wantErr bool
  	}{
  		{name: "whole", in: "12", want: 1200},
  		{name: "cents", in: "12.50", want: 1250},
  		{name: "bad", in: "abc", wantErr: true},
  	}
  	for _, tt := range tests {
  		t.Run(tt.name, func(t *testing.T) {
  			got, err := ParseAmount(tt.in)
  			if (err != nil) != tt.wantErr {
  				t.Fatalf("err = %v, wantErr %v", err, tt.wantErr)
  			}
  			if got != tt.want {
  				t.Errorf("ParseAmount(%q) = %d, want %d", tt.in, got, tt.want)
  			}
  		})
  	}
  }
  ```

  Since **Go 1.22** the loop variable is per-iteration, so the old `tt := tt` capture is no longer needed — even for parallel subtests. This applies to modules whose `go.mod` declares `go 1.22` or newer; on an older go directive, keep the `tt := tt` capture (or raise the directive). ([Go blog: Fixing For Loops in 1.22](https://go.dev/blog/loopvar-preview))

- **`t.Parallel()`** marks a test (or subtest) safe to run concurrently with other parallel tests. Call it at the top of the test body. Use it to surface shared-state bugs (and pair with `-race`). Note: a parent `t.Run` returns only after its parallel children finish.
- **`t.Cleanup(func())`** registers teardown that runs when the test (and its subtests) end, in LIFO order. Prefer it over `defer` for setup helpers, because cleanup registered inside a helper still runs after the calling test completes.
- **`t.Helper()`** marks a function as a test helper, so failure line numbers point at the *caller*, not inside the helper. Put it first in any custom assert/setup helper.
- **`t.Context()`** (Go 1.24+) returns a `context.Context` cancelled just before cleanup — pass it to code under test instead of `context.Background()`. ([testing docs](https://pkg.go.dev/testing#T.Context))
- **`httptest`** for HTTP: `httptest.NewServer(handler)` spins up a real loopback server (test the client against a real socket); `httptest.NewRecorder()` captures a handler's response without a network. Prefer these over mocking `http.Client`. ([httptest docs](https://pkg.go.dev/net/http/httptest))
- **Golden files** for large/structured output: store expected output under `testdata/`, compare against it, and regenerate with a `-update` flag. `testdata/` is ignored by the Go tool. ([Go blog: Subtests — golden files](https://go.dev/blog/subtests))
- **`TestMain(m *testing.M)`** for package-level setup/teardown (one per package). It must call `m.Run()` and exit with its code; otherwise prefer per-test `t.Cleanup`. To run teardown even on panic, wrap so `defer` runs before the exit:

  ```go
  func TestMain(m *testing.M) {
  	os.Exit(run(m)) // run() does setup, defer teardown(), return m.Run()
  }
  ```

  Note `flag.Parse()` has *not* run when `TestMain` is entered. ([testing docs — TestMain](https://pkg.go.dev/testing#hdr-Main))
- **Native fuzzing** (Go 1.18+) complements table tests for parsers/encoders: `func FuzzParseAmount(f *testing.F)` seeds known inputs with `f.Add(...)`, then `f.Fuzz(func(t *testing.T, s string){ ... })` asserts an invariant (e.g. "never panics"). It runs as a normal unit test under `go test`, or as a fuzzer with `go test -fuzz=FuzzParseAmount`; failing inputs are saved to `testdata/fuzz/`. ([Go: Fuzzing tutorial](https://go.dev/doc/tutorial/fuzz))

## Go-specific anti-patterns

Each: ❌ what it is → why it's wrong → ✅ the fix.

- ❌ **Defining an interface just so you can mock a dependency.** A one-method interface created next to its only implementation, solely to inject a generated mock. → Go interfaces belong in the **consumer** package, discovered when a second implementation appears — not minted up front. Premature interfaces ("interface pollution") add indirection and a mock you then test instead of real behavior. → Accept a *small* interface at the consumer only when you genuinely need to swap an implementation; otherwise depend on the concrete type and use a real dependency or `httptest`. "Accept interfaces, return structs." ([Go Code Review Comments — Interfaces](https://go.dev/wiki/CodeReviewComments#interfaces); [100 Go Mistakes #5: Interface pollution](https://100go.co/5-interface-pollution/))
- ❌ **Hardcoding `time.Now()` (or `time.Sleep`) inside the code under test.** → The test can't control or assert on time, so it's either non-deterministic or slow. → Inject a clock — pass a `func() time.Time` (or a small `Clock` interface) so tests supply a fixed time. For *concurrent* time (timeouts, tickers, retries), use **`testing/synctest`** (stable since Go 1.25): `synctest.Test(t, func(t *testing.T){ ... })` runs the body in a "bubble" with a fake clock that only advances when every goroutine is durably blocked, so timeout tests are deterministic and instant. ([Go blog: Testing Time](https://go.dev/blog/testing-time); [synctest docs](https://pkg.go.dev/testing/synctest))
- ❌ **Skipping the table for variant cases** — copy-pasting near-identical `TestFooA`, `TestFooB`, `TestFooC`. → Duplicated setup, easy to forget a case, noisy diffs. → Collapse into one table-driven test with a `name` per row (see Idioms). ([Go blog: Subtests](https://go.dev/blog/subtests))
- ❌ **Calling `t.Setenv` / `t.Chdir` in a parallel test.** → These mutate process-wide state; the `testing` package **panics** if you call them in a test that has called `t.Parallel()` (or has a parallel ancestor), because the value would leak across concurrently-running tests. → Don't mark such tests parallel, or pass the value as a parameter instead of via env/cwd. ([testing docs — T.Setenv](https://pkg.go.dev/testing#T.Setenv))
- ❌ **Sharing mutable state across parallel subtests** (a captured map/slice/struct written from several `t.Run(..., t.Parallel())`). → Data race: results depend on scheduling, and the bug may stay invisible until production. → Give each subtest its own copy, or synchronize; **always run `go test -race`** locally and in CI so the detector catches it. ([Go blog: data race detector](https://go.dev/blog/race-detector))
- ❌ **Letting goroutines leak undetected.** A test starts a goroutine (or the code does) that never exits; `go test` doesn't fail for leaks by default. → Leaks accumulate and cause flaky, slow, or resource-exhausting suites. → Assert no leak with `defer goleak.VerifyNone(t)` (or `goleak.VerifyTestMain` in `TestMain`). ([uber-go/goleak](https://github.com/uber-go/goleak))

## Tooling notes

- **Race detector** — `go test -race ./...`. Instruments memory access to flag data races at runtime; ~2–20x slower and only catches races on code paths actually exercised, so keep tests that hit concurrency. Treat any race report as a failure. ([Go blog: race detector](https://go.dev/blog/race-detector))
- **Coverage** — `go test -cover ./...` for a summary; `go test -coverprofile=cover.out ./... && go tool cover -html=cover.out` for a line-by-line HTML view. Coverage is a smell-detector for *untested* code, not a target to chase.
- **Struct comparison** — prefer **`google/go-cmp`** over `reflect.DeepEqual`: `if diff := cmp.Diff(want, got); diff != "" { t.Errorf("mismatch (-want +got):\n%s", diff) }` prints a readable diff. It is **test-only** (may panic) and, unlike `reflect.DeepEqual`, **panics on unexported fields** unless you opt in with `cmpopts.IgnoreUnexported` or an `Equal` method — a deliberate safety feature. ([go-cmp docs](https://pkg.go.dev/github.com/google/go-cmp/cmp))
- **Assertion libraries — a real community split.** `stretchr/testify` (`assert`/`require`/`suite`/`mock`) is widely used and cuts boilerplate. But the Go team and many maintainers argue against assertion DSLs: they're a sub-language to learn, `require.*` aborts on first failure hiding later info, and plain `if got != want { t.Errorf(...) }` is clearer and idiomatic. Both positions are legitimate. **Recommendation:** follow the existing convention in the codebase rather than mixing styles; for new code, plain `testing` + `go-cmp` is the lowest-dependency default. ([Go wiki: TestComments — assertion libraries](https://go.dev/wiki/TestComments#assert-libraries); [Testify is making your Go tests worse (2026)](https://boldlygo.tech/posts/2026-04-20-testify-is-making-your-go-tests-worse/))
- **Test output / CI** — `gotest.tools/gotestsum` wraps `go test` with readable, CI-friendly output (e.g. JUnit XML) without changing how tests are written. ([gotestsum](https://github.com/gotestyourself/gotestsum))
- **Integration tests** — gate slow/external tests behind `testing.Short()` (`if testing.Short() { t.Skip(...) }`, then `go test -short` to skip them) or a build tag like `//go:build integration`. For real dependencies in a container, `testcontainers-go` spins up databases/queues per test. ([testing docs — Short](https://pkg.go.dev/testing#Short))

## Quick reference

| Need | Use |
|---|---|
| Run all / one test / one subtest | `go test ./...` · `go test -run TestX ./pkg` · `go test -run TestX/case ./pkg` |
| Catch data races | `go test -race ./...` |
| Coverage report | `go test -coverprofile=cover.out ./... && go tool cover -html=cover.out` |
| Many variants of one behavior | Table-driven test + `t.Run(name, ...)` |
| Run subtests concurrently | `t.Parallel()` (pair with `-race`; **no** `tt := tt` needed since Go 1.22) |
| Teardown / accurate failure lines | `t.Cleanup(...)` · `t.Helper()` |
| Test-scoped context | `t.Context()` (Go 1.24+) |
| HTTP under test | `httptest.NewServer` / `httptest.NewRecorder` |
| Controllable time | inject `func() time.Time`; concurrent → `testing/synctest` (Go 1.25+) |
| Compare structs with a diff | `cmp.Diff(want, got)` (test-only; panics on unexported fields) |
| Detect goroutine leaks | `defer goleak.VerifyNone(t)` |
| Skip slow tests | `testing.Short()` + `-short`, or `//go:build integration` |
