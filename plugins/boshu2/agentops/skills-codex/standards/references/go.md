# Go Standards (Tier 1)

## Target Version

Detect from `go.mod`. Use all features up to and including that version. Never use features from newer versions. Current project target: **Go 1.26**.

## Required

- `gofmt` (automatic)
- `golangci-lint run` passes
- All exported symbols documented

## Error Handling

- Always check errors: `if err != nil`
- Wrap errors with context: `fmt.Errorf("doing X: %w", err)`
- Never `_ = err` without `// nolint:errcheck` comment
- Use `errors.Is(err, target)` instead of `err == target` -- works with wrapped errors (1.13+)
- Use `errors.Join(err1, err2)` to aggregate errors from parallel operations or multi-step cleanup (1.20+)
- Use `context.WithCancelCause` / `context.Cause` to attach error reasons to cancellations (1.20+)

## Common Issues

| Pattern | Problem | Fix |
|---------|---------|-----|
| `%v` for errors | Breaks error chain | Use `%w` |
| `panic()` in library | Crashes caller | Return error |
| Naked goroutine | No error handling | errgroup or channels |
| `interface{}` | Type safety loss | Use `any` (1.18+), generics, or specific types |
| `err == target` | Misses wrapped errors | `errors.Is(err, target)` (1.13+) |
| `atomic.StoreInt32` | Type-unsafe | `atomic.Bool` / `atomic.Int64` / `atomic.Pointer[T]` (1.19+) |
| `for i := 0; i < n; i++` | Verbose | `for i := range n` (1.22+) |
| Manual loop for contains/sort | Error-prone, verbose | `slices.Contains`, `slices.SortFunc` (1.21+) |
| `sync.Once` + closure wrapper | Verbose, easy to misuse | `sync.OnceFunc` / `sync.OnceValue` (1.21+) |

## Interfaces

- Accept interfaces, return structs
- Keep interfaces small (1-3 methods)
- Define interfaces where used, not implemented

## Documentation

- All exported symbols must have godoc comments starting with the symbol name
- Package-level doc in `doc.go` for non-trivial packages
- Include runnable `Example_*` functions in `_test.go` files
- Run `go doc ./...` to verify documentation

## Concurrency

- Always pass `context.Context` as first param
- Use `sync.Mutex` for shared state; use type-safe atomics (`atomic.Bool`, `atomic.Int64`, `atomic.Pointer[T]`) for simple flags/counters (1.19+)
- Prefer channels for communication
- Use `sync.OnceFunc(fn)` instead of `sync.Once` + wrapper; `sync.OnceValue(fn)` when returning a value (1.21+)
- Use `context.AfterFunc(ctx, cleanup)` to register cleanup on cancellation (1.21+)
- Loop variables are safe to capture in goroutines since 1.22 (each iteration gets its own copy)

## Modern Standard Library

### slices package (1.21+)

Prefer `slices` over hand-written loops:

| Function | Replaces |
|----------|----------|
| `slices.Contains(items, x)` | Manual search loop |
| `slices.Index(items, x)` | Manual search loop returning index |
| `slices.IndexFunc(items, fn)` | Manual search loop with predicate |
| `slices.Sort(items)` | `sort.Slice` / `sort.Strings` |
| `slices.SortFunc(items, cmp)` | `sort.Slice` with less function |
| `slices.Max(items)` / `slices.Min(items)` | Manual loop tracking max/min |
| `slices.Reverse(items)` | Manual swap loop |
| `slices.Compact(items)` | Manual dedup of consecutive elements |
| `slices.Clip(s)` | `s[:len(s):len(s)]` to remove excess capacity |
| `slices.Clone(s)` | `append([]T(nil), s...)` |

Iterator consumption (1.23+):

| Function | Usage |
|----------|-------|
| `slices.Collect(iter)` | Build slice from iterator |
| `slices.Sorted(iter)` | Collect and sort in one step |

### maps package (1.21+; Keys/Values return iterators as of 1.23)

| Function | Replaces |
|----------|----------|
| `maps.Clone(m)` | Manual map copy loop |
| `maps.Copy(dst, src)` | Manual map merge loop |
| `maps.DeleteFunc(m, fn)` | Manual delete loop with predicate |
| `maps.Keys(m)` | Manual key collection loop (returns iterator, 1.23+) |
| `maps.Values(m)` | Manual value collection loop (returns iterator, 1.23+) |

### cmp package (1.22+)

- `cmp.Or(a, b, c)` -- returns first non-zero value. Replaces `if x == "" { x = default }` chains:
  ```go
  name := cmp.Or(os.Getenv("NAME"), config.Name, "default")
  ```

### strings / bytes improvements

| Function | Version | Replaces |
|----------|---------|----------|
| `strings.Cut(s, sep)` / `bytes.Cut(b, sep)` | 1.18+ | `Index` + slice arithmetic |
| `strings.CutPrefix(s, prefix)` / `strings.CutSuffix(s, suffix)` | 1.20+ | `HasPrefix` + `TrimPrefix` |
| `strings.Clone(s)` / `bytes.Clone(b)` | 1.20+ | Manual copy (prevents memory leaks from substring references) |

### net/http improvements (1.22+)

Enhanced `ServeMux` with method and path parameters:

```go
mux.HandleFunc("GET /api/users/{id}", func(w http.ResponseWriter, r *http.Request) {
    id := r.PathValue("id")
    // ...
})
```

May eliminate the need for third-party routers for simple APIs.

### Other stdlib

| Function | Version | Replaces |
|----------|---------|----------|
| `fmt.Appendf(buf, fmt, args...)` | 1.19+ | `[]byte(fmt.Sprintf(...))` -- avoids allocation |
| `time.Since(start)` | 1.0+ | `time.Now().Sub(start)` |
| `time.Until(deadline)` | 1.8+ | `deadline.Sub(time.Now())` |
| `errors.Join(err1, err2)` | 1.20+ | Discarding all but the first error (see Error Handling) |
| `reflect.TypeFor[T]()` | 1.22+ | `reflect.TypeOf((*T)(nil)).Elem()` |
| `min(a, b)` / `max(a, b)` | 1.21+ | `if a > b` patterns or custom helpers |
| `clear(m)` / `clear(s)` | 1.21+ | Manual map deletion loop / manual slice zeroing |

## Struct Contract Completeness

When adding fields to a struct, every code path that creates an instance **must** populate them. Partial population creates an inconsistent contract for consumers.

| Anti-Pattern | Problem | Fix |
|--------------|---------|-----|
| New field on struct, some constructors don't set it | Consumers see zero-value for some paths, real value for others | Grep all `StructName{` literals; verify each sets the new field |
| Synthesized instances (e.g., end-of-batch summaries) skip fields | Downstream code assumes all instances have the same shape | Store provenance metadata alongside state so synthesized instances can populate fields from last-seen values |
| Index fields after sort | `EventIndex` points to sorted position, not caller's original position | Wrap items with original index before sorting; emit original index in output |

**Checklist for adding struct fields:**
1. Grep `StructName{` across the package — every literal must set the new field
2. Check factory functions and builder patterns
3. Check synthesized/summary instances created outside the main loop
4. Add a structural assertion test: iterate all output instances, assert new field is non-zero (or document why zero is valid)

## Wire Input Validation

When parsing external JSON/YAML into structs with enum-like fields, **validate against an allowlist** before trusting the value.

```go
// BAD: trust whatever the wire sends
if ev.ErrorClass != "" {
    // use it as-is — "bogus" passes through
}

// GOOD: validate against known values
var validClasses = map[ErrorClass]bool{ ... }
if ev.ErrorClass != "" && !validClasses[ev.ErrorClass] {
    ev.ErrorClass = classify(ev) // reclassify from content
}
```

Also normalize impossible states: if `IsError=false` but `ErrorClass="timeout"`, clear it.

## Testing

### Exact Assertion Rule

**Always assert the exact expected value, never just "not the wrong one."**

```go
// BAD: passes even if classification drifts to a different wrong class
if got == StreamErrorClassRateLimit {
    t.Errorf("should not be rate_limit")
}

// GOOD: pins the exact expected behavior
if got != StreamErrorClassExecutionError {
    t.Errorf("got %q, want execution_error", got)
}
```

This applies to all classifier/enum tests. `!= X` assertions silently pass when the result drifts to a third, equally wrong value.

### Structural Invariant Tests

For structs with required fields, add a sweep test that asserts ALL output instances populate them:

```go
func TestAllViolationsHaveStructuredFields(t *testing.T) {
    // Run through multiple scenarios, collect all violations
    for _, v := range allViolations {
        if v.TeamName == "" && v.Rule != RuleSomeException {
            t.Errorf("violation %+v missing TeamName", v)
        }
        if v.Timestamp.IsZero() {
            t.Errorf("violation %+v missing Timestamp", v)
        }
    }
}
```

### CI-Safe Test Pattern

When testing functions that shell out to external CLIs (`bd`, `ao`, `gh`, etc.), **test the low-level function directly** instead of the wrapper that invokes the CLI. This ensures tests pass in CI where the CLI may not be installed.

```go
// BAD: calls processDiscoveryPhase() which requires bd CLI
func TestGateDiscoveryVerdictC2Event(t *testing.T) {
    processDiscoveryPhase(ctx, root, opts) // fails in CI — bd not available
}

// GOOD: test event shape directly via the underlying function
func TestGateDiscoveryVerdictC2Event(t *testing.T) {
    ev, err := appendRPIC2Event(root, rpiC2EventInput{
        RunID: runID, Phase: 1, Type: "gate.discovery.verdict",
        Message: "Pre-mortem verdict: PASS",
        Details: map[string]any{"verdict": "PASS", "report": "report.md"},
    })
    require.NoError(t, err)
    assert.Equal(t, "gate.discovery.verdict", ev.Type)
}
```

**Rule:** If a function's only untestable part is the external CLI call, extract the testable logic (event emission, state mutation, file I/O) into a separate function and test that.

### Table-Driven Tests

Prefer table-driven tests for functions with multiple input/output cases:

```go
func TestClassifyServeArg(t *testing.T) {
    tests := []struct {
        name      string
        flagRunID string
        args      []string
        wantGoal  string
        wantRunID string
    }{
        {"empty", "", nil, "", ""},
        {"flag run-id", "rpi-abc12345", nil, "", "rpi-abc12345"},
        {"arg goal", "", []string{"fix the bug"}, "fix the bug", ""},
    }
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            goal, runID := classifyServeArg(tt.flagRunID, tt.args)
            assert.Equal(t, tt.wantGoal, goal)
            assert.Equal(t, tt.wantRunID, runID)
        })
    }
}
```

### Test Conventions

- **File naming:** Test files MUST be named `<source>_test.go`. NEVER `cov*_test.go`, `*_extra_test.go`, or other non-standard prefixes. Keep all tests for a source file in one test file.
- **Function naming:** `Test<Uppercase>` (e.g., `TestFoo_Bar`). Go requires uppercase letter after `Test`.
- **No coverage-padding:** Tests that use trivial `!= ""` or `!= nil` assertions solely to inflate coverage are banned. Every test must assert behavioral correctness.
- **No zero-assertion smoke tests:** Every test must have assertions. For print/output functions, use `captureStdout` and assert output contains expected strings.
- **Assert exact expected values:** Use `== expected`, never `!= wrong`. (See Exact Assertion Rule above.)
- **Table-driven tests** preferred for multi-case functions. (See example above.)
- **Test low-level functions directly;** don't depend on external CLIs (`bd`, `ao`) in tests. (See CI-Safe Test Pattern above.)
- **Guard-test fixtures must use the real persisted shape.** Skip/dedup/consumed/idempotency/regression guard tests must round-trip a real persisted sample (production writer → production reader) or assert against a checked-in real example — never a hand-built in-memory constructor that sets a marker at a granularity the on-disk format never emits (e.g. `consumed` at item-level when `next-work.jsonl` marks it at batch-level). A fixture of a shape production can't produce gives a false green (ag-mjlg / PR #652). Full rationale: `test-pyramid.md` → "Fixture Fidelity".
- **Test isolation — restore shared global/process state via `t.Cleanup`.** `cli/cmd/ao` tests share one `rootCmd` + package-global cobra flag vars and run inside the repo tree, so a test that mutates shared state without restoring it leaks into whatever test the `-shuffle=on` order runs next. This is a recurring flake class: goals `goalsMeasureScenariosOnly` cobra-global (`a9dab21c4`), `core.bare` git-env (ek8v), cwd floor (hvb).
  - Set a package-global cobra flag only through a self-cleaning helper, so every set-site auto-restores and no order can leak it:

    ```go
    func setGoalsMeasureScenariosOnly(t *testing.T, v bool) {
        t.Helper()
        old := goalsMeasureScenariosOnly
        goalsMeasureScenariosOnly = v
        t.Cleanup(func() { goalsMeasureScenariosOnly = old })
    }
    ```

  - Scope process state: `t.Chdir(t.TempDir())`, `t.Setenv`, and `git -C <tempRepo>` with `cmd.Dir` set. Never run a state-mutating `git` op against the real repo via an unset `cmd.Dir` / leaked `GIT_DIR`.
  - Find leakers by analysis (grep set-sites for a missing reset), not by chasing reproducing seeds: order-dependent flakes are population+seed-specific, so "couldn't reproduce" ≠ fixed — close on the root (the missing cleanup).
  - The push==CI full race suite runs `-shuffle=on` as the *late* backstop; it is not the primary guard.

### Benchmark Tests (BF7)

Use Go's built-in benchmark support for hot-path functions:

```go
func BenchmarkParseConfig(b *testing.B) {
    input := generateLargeConfig(1000)
    b.ResetTimer()
    for b.Loop() {  // Go 1.24+; use `for i := 0; i < b.N; i++` for older versions
        parseConfig(input)
    }
}
```

Run with: `go test -bench=. -benchmem ./...`

Compare across changes with `benchstat`:
```bash
go test -bench=. -count=10 ./... > old.txt
# ... make changes ...
go test -bench=. -count=10 ./... > new.txt
benchstat old.txt new.txt
```

### Backward Compatibility Tests (BF8)

Maintain golden fixtures in `testdata/compat/`:

```go
func TestBackwardCompat(t *testing.T) {
    fixtures, err := filepath.Glob("testdata/compat/*.json")
    require.NoError(t, err)
    require.NotEmpty(t, fixtures, "compat fixtures must exist")
    for _, f := range fixtures {
        t.Run(filepath.Base(f), func(t *testing.T) {
            data, _ := os.ReadFile(f)
            result, err := ParseConfig(data)
            require.NoError(t, err, "legacy format must still parse")
            assert.NotEmpty(t, result.Name)
        })
    }
}
```

### Regression Tests (BF6)

Name after the bug ID. Reproduce the exact failure:

```go
func TestBug_AG_XYZ_NilMapPanic(t *testing.T) {
    // Regression: processGoals panicked on nil options map (ag-xyz)
    result, err := processGoals(nil)
    require.NoError(t, err)
    assert.Empty(t, result)
}
```

### Security Tests (BF9)

Test path traversal rejection and secrets redaction:

```go
func TestRejectsPathTraversal(t *testing.T) {
    payloads := []string{"../../../etc/passwd", "..\\windows", "foo/../bar"}
    for _, p := range payloads {
        t.Run(p, func(t *testing.T) {
            _, err := LoadConfig(p)
            assert.Error(t, err, "must reject path traversal")
        })
    }
}
```

### Complexity Budget

- **Warn** at cyclomatic complexity 15, **fail** at 25.
- Run `golangci-lint run` to check.

### Before Committing Go Changes

```bash
cd cli && go build ./... && go vet ./... && go test ./...
```

Or equivalently: `cd cli && make build && make test`

## HTTP Handler Security

Go HTTP handlers in this codebase are localhost-only but should still follow defense-in-depth:

| Pattern | Risk | Fix |
|---------|------|-----|
| `innerHTML = userInput` in embedded HTML | XSS | Use DOM construction (`createElement` + `textContent`) |
| `r.URL.Query().Get("param")` used in file paths | Path traversal | Reject `..`, `/`, `\` before use |
| `fmt.Fprintf(w, userInput)` in HTML handler | XSS | Use `html/template` or `text/template` with escaping |
| `filepath.Join(root, userInput)` | Path traversal | Validate input against allowlist pattern (e.g., `regexp`) |
| `Access-Control-Allow-Origin: *` | CORS bypass | Acceptable for localhost-only; restrict for public APIs |

**Query parameter validation pattern:**

```go
param := strings.TrimSpace(r.URL.Query().Get("id"))
if param != "" && (strings.Contains(param, "..") || strings.Contains(param, "/") || strings.Contains(param, "\\")) {
    http.Error(w, "invalid parameter", http.StatusBadRequest)
    return
}
```

**DOM construction instead of innerHTML:**

```javascript
// BAD: innerHTML with user-controlled data
el.innerHTML = '<span>' + userInput + '</span>';

// GOOD: DOM construction
const span = document.createElement('span');
span.textContent = userInput;
el.appendChild(span);
```

## Security-Lint Suppressions (gosec + semgrep)

When a security-lint finding is a false positive on intentional crypto (e.g. SHA-1 used for git object IDs, not as a security primitive), the suppression needs TWO independent annotations on the SAME line. gosec and semgrep run as separate scanners and each ignores the other's directives.

| Scanner | What it ignores | What suppresses it |
|---------|-----------------|--------------------|
| gosec (standalone) | `//nolint:gosec` (golangci-lint-only) | `// #nosec G<NN>` directive, e.g. `// #nosec G401 G505` |
| semgrep | qualified `nosemgrep: <rule-id>` (does NOT suppress) | a **bare** `// nosemgrep` |

Combine both into one comment and place it on **both** the import line and the usage/call site — each is flagged independently:

```go
import (
    "crypto/sha1" // #nosec G505 nosemgrep -- git object IDs are SHA-1 by definition; not a security primitive here.
)

func gitBlobID(content []byte) string {
    h := sha1.New() // #nosec G401 nosemgrep -- git blob IDs are SHA-1; matching git.
    // ...
}
```

The `G<NN>` codes differ by site: G505 flags the `crypto/sha1` import (blocklisted import), G401 flags the `sha1.New()` call (weak crypto primitive). Pass every code that fires on a given line.

Canonical example in this repo: `cli/internal/drrebuild/drrebuild.go`.

## Future Features (Go 1.24+)

This section tracks features by first-supported Go version and can be used to plan future target upgrades.

| Feature | Version | What It Replaces |
|---------|---------|------------------|
| `t.Context()` | 1.24+ | `context.WithCancel(context.Background())` in tests |
| `b.Loop()` | 1.24+ | `for i := 0; i < b.N; i++` in benchmarks |
| `omitzero` JSON tag | 1.24+ | `omitempty` (which fails for `time.Duration`, structs, slices, maps) |
| `strings.SplitSeq` / `FieldsSeq` | 1.24+ | `strings.Split` when iterating (avoids intermediate slice) |
| `wg.Go(fn)` | 1.25+ | `wg.Add(1)` + `go func() { defer wg.Done(); ... }()` |
| `new(val)` | 1.26+ | `x := val; &x` for pointer creation |
| `errors.AsType[T](err)` | 1.26+ | `var target T; errors.As(err, &target)` |
