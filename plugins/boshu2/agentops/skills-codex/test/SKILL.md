---
name: test
description: "Run test."
---
# Test Skill

> **Quick Ref:** Generate tests, analyze coverage, fill gaps, run TDD loops. Output: passing tests + coverage report in `.agents/test/`.

**YOU MUST EXECUTE THIS WORKFLOW. Do not just describe it.**

Generate real tests, run them, verify they pass, and produce coverage artifacts. Do not output a plan and stop.

## Modes

| Mode | Trigger | What It Does |
|------|---------|--------------|
| `generate` | "generate tests", "write tests", "add tests" | Create tests for existing code |
| `coverage` | "test coverage", "coverage gaps", "missing tests" | Analyze coverage and fill gaps |
| `strategy` | "test strategy", "test architecture" | Recommend test structure and patterns |
| `tdd` | "tdd", "red green refactor" | Red-green-refactor loop for new features |

Default mode is `generate` when unspecified. Detect from user intent.

## Step 0a: Scenarios-First (when the work has acceptance scenarios)

When the task is tied to a bead or `.feature` file, **author tests FORWARD from the Gherkin scenarios** — not backward from a coverage gap. This is the C2 contract (ag-9jle.4): the unit of test authoring is one scenario, one covering test.

1. Read the scenarios: the bead's `## Scenarios` block (`bd show <bead-id>`) or a `.feature` under `skills/<skill>/references/`.
2. For each `Scenario:`, locate or write the test that exercises its `Given/When/Then`. Name it after the behavior.
3. Declare the linkage by adding `@covered-by:<test-path>` (optionally `::<TestName>`) directly above the scenario in its source — so the leaf coverage gate can prove the mapping.
4. Run the leaf coverage gate and require it to pass before considering the slice tested:

```bash
bash scripts/check-bead-scenario-coverage.sh --bead <bead-id> --run      # every scenario -> a PASSING test
bash scripts/check-bead-scenario-coverage.sh skills/<skill>/references/<name>.feature --run
```

A scenario with no covering test is a FAIL — "tests exist" or a coverage percentage is not sufficient. Then continue with coverage gap-fill (Steps 1–5) for everything the scenarios don't reach. When there are no scenarios, skip this step and use the coverage-driven flow below.

## Step 0: Detect Language and Load Standards

Scan the project root for language markers. Stop at the first match:

| Marker File | Language | Test Framework | Coverage Command |
|-------------|----------|----------------|-----------------|
| `go.mod` | Go | `go test` | `go test -coverprofile=coverage.out ./...` |
| `pyproject.toml` or `setup.py` | Python | pytest | `pytest --cov --cov-report=term-missing` |
| `package.json` | JS/TS | jest or vitest | `npx jest --coverage` or `npx vitest run --coverage` |
| `Cargo.toml` | Rust | cargo test | `cargo tarpaulin --out Lcov` |

Load `$standards` for the detected language. Apply all testing conventions from the standards skill (naming, assertion style, structural rules).

**Go-specific rules (from project CLAUDE.md):**
- Test file naming: `<source>_test.go`. NEVER `cov*_test.go` or `*_extra_test.go`.
- Test function naming: `Test<Uppercase>` (e.g., `TestParseConfig_EmptyInput`).
- Prefer table-driven tests for multi-case functions.
- Use `captureStdout` for output functions and assert content.

**Python-specific rules:**
- Use `pytest` with `conftest.py` for shared fixtures.
- Use `@pytest.mark.parametrize` for multi-case functions.
- Type hints on test helpers.

**JS/TS-specific rules:**
- Use `describe`/`it` blocks with clear names.
- Group by function or module under test.
- Mock external services, not internal code.

## Step 1: Analyze Existing Test Coverage

Run the coverage command for the detected language:

```bash
# Go
go test -coverprofile=coverage.out ./... 2>&1 | tee .agents/test/coverage-raw.txt
go tool cover -func=coverage.out > .agents/test/coverage-func.txt

# Python
pytest --cov --cov-report=term-missing --cov-report=json:.agents/test/coverage.json 2>&1 | tee .agents/test/coverage-raw.txt

# JS/TS
npx jest --coverage --coverageReporters=text 2>&1 | tee .agents/test/coverage-raw.txt

# Rust
cargo tarpaulin --out Lcov 2>&1 | tee .agents/test/coverage-raw.txt
```

Parse the output. Build a ranked list of files by coverage percentage (lowest first).

If `$refactor` is available, cross-reference: high-complexity + low-coverage = highest priority targets.

## Step 2: Identify Gaps

From the coverage data, identify:

1. **Untested files** -- source files with no corresponding test file.
2. **Uncovered functions** -- exported/public functions with 0% coverage.
3. **Uncovered branches** -- functions with partial coverage (conditionals, error paths).
4. **Missing edge cases** -- functions that only test the happy path.

Produce a gap list sorted by risk (high complexity + low coverage first):

```
File                        | Coverage | Functions Missing Tests | Risk
----------------------------|----------|------------------------|------
internal/parser/parse.go    | 23%      | ParseConfig, Validate  | HIGH
internal/goals/measure.go   | 45%      | MeasureFitness         | MEDIUM
lib/utils.go                | 89%      | (edge cases only)      | LOW
```

Write gap list to `.agents/test/gaps.md`.

## Step 3: Generate Tests

For each gap (highest risk first), generate tests following language-specific patterns.

If the target needs a specialized test pattern, load the matching reference before writing tests:

- Contract/API/CLI compatibility: [references/conformance-harnesses.md](references/conformance-harnesses.md)
- Parsers, serializers, and untrusted inputs: [references/fuzzing.md](references/fuzzing.md)
- Generated files, snapshots, and rendered output: [references/golden-artifacts.md](references/golden-artifacts.md)
- Metamorphic/invariant-heavy behavior: [references/metamorphic-testing.md](references/metamorphic-testing.md)
- Golden artifact update review: [references/golden-artifact-strategy.md](references/golden-artifact-strategy.md)
- Real databases, services, queues, or APIs where mocks would hide failures: [references/real-service-e2e.md](references/real-service-e2e.md)

### Go: Table-Driven Tests

```go
func TestParseConfig_Variants(t *testing.T) {
    tests := []struct {
        name    string
        input   string
        want    *Config
        wantErr bool
    }{
        {name: "valid minimal", input: `name: foo`, want: &Config{Name: "foo"}},
        {name: "empty input", input: "", want: nil, wantErr: true},
        {name: "invalid yaml", input: `: bad`, want: nil, wantErr: true},
    }
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            got, err := ParseConfig(tt.input)
            if (err != nil) != tt.wantErr {
                t.Errorf("ParseConfig() error = %v, wantErr %v", err, tt.wantErr)
                return
            }
            if !reflect.DeepEqual(got, tt.want) {
                t.Errorf("ParseConfig() = %v, want %v", got, tt.want)
            }
        })
    }
}
```

### Python: Parametrized Tests

```python
@pytest.mark.parametrize("input_val,expected", [
    ("valid", Config(name="valid")),
    ("", None),
    (None, None),
])
def test_parse_config(input_val: str, expected: Config | None) -> None:
    result = parse_config(input_val)
    assert result == expected
```

### JS/TS: Describe Blocks

```typescript
describe("parseConfig", () => {
  it("parses valid input", () => {
    expect(parseConfig("valid")).toEqual({ name: "valid" });
  });

  it("returns null for empty input", () => {
    expect(parseConfig("")).toBeNull();
  });

  it("throws on malformed input", () => {
    expect(() => parseConfig(": bad")).toThrow();
  });
});
```

### Generation Rules

1. **Read the source function first.** Understand inputs, outputs, error conditions, and branches.
2. **Cover every branch.** Each `if`, `switch`, error return, and edge case gets at least one test case.
3. **Assert exact expected values.** Use `== expected`, not `!= nil` or `!= ""`.
4. **Name tests descriptively.** The test name should describe the scenario: `"empty input returns error"`, not `"test1"`.
5. **Test error paths explicitly.** Verify error messages or error types, not just that an error occurred.
6. **One assertion focus per test case.** Each table row or parametrized case tests one specific behavior.

## Step 4: Run Generated Tests

After writing each test file, immediately run it:

```bash
# Go
go test -v -run TestParseConfig ./internal/parser/

# Python
pytest -xvs tests/test_parser.py

# JS/TS
npx jest --verbose tests/parser.test.ts

# Rust
cargo test test_parse_config -- --nocapture
```

**If tests fail:**
1. Read the failure output.
2. Determine if the test is wrong or the code has a bug.
3. If the test is wrong: fix the test assertion or setup.
4. If the code has a bug: report it but fix the test to match current behavior, noting the bug in the output.
5. Re-run until green.

Never commit failing tests (unless in TDD mode, Step red).

## Step 5: Output Coverage Report

Re-run coverage after adding tests:

```bash
# Same commands as Step 1
```

Compare before/after. Write summary to `.agents/test/summary.md`:

```markdown
# Test Generation Summary

**Language:** Go
**Date:** 2026-03-27
**Mode:** generate

## Coverage Delta

| Metric | Before | After | Delta |
|--------|--------|-------|-------|
| Overall | 52.3%  | 71.8% | +19.5% |
| internal/parser | 23.0% | 85.2% | +62.2% |
| internal/goals  | 45.0% | 67.3% | +22.3% |

## Tests Added

- `internal/parser/parse_test.go` -- 12 test cases (3 existing + 9 new)
- `internal/goals/measure_test.go` -- 8 test cases (new file)

## Remaining Gaps

- `internal/render/` -- 34% coverage, complex template logic
- `cmd/root.go` -- integration test needed

## Bugs Found

- `ParseConfig` does not validate empty name field (passes silently)
```

Create `.agents/test/` directory if it does not exist. All artifacts go there.

## TDD Mode

When mode is `tdd`, follow the red-green-refactor cycle:

### Red: Write a Failing Test

1. Understand the feature requirement from the user.
2. Write a test that describes the desired behavior.
3. Run the test -- it MUST fail. If it passes, the test is not testing new behavior.

```bash
# Verify the test fails
go test -v -run TestNewFeature ./...
# Expected: FAIL
```

### Green: Minimal Implementation

4. Write the minimum code to make the test pass. No extra logic, no optimization.
5. Run the test -- it MUST pass now.

```bash
go test -v -run TestNewFeature ./...
# Expected: PASS
```

### Refactor

6. Clean up the implementation. Remove duplication, improve naming, simplify logic.
7. Run ALL tests -- everything must still pass.

```bash
go test ./...
# Expected: all PASS
```

### Repeat

8. Pick the next behavior. Write the next failing test. Continue the cycle.

Log each cycle to `.agents/test/tdd-log.md`:

```markdown
## Cycle 1: Parse empty config returns error
- RED: TestParseConfig_EmptyInput -- FAIL (function not implemented)
- GREEN: Added nil check in ParseConfig -- PASS
- REFACTOR: Extracted validation to validateConfig() -- PASS

## Cycle 2: Parse config validates name field
- RED: TestParseConfig_MissingName -- FAIL (no name validation)
- GREEN: Added name check -- PASS
- REFACTOR: None needed -- PASS
```

## Strategy Mode

When mode is `strategy`, analyze and recommend (no code generation):

1. **Inventory existing tests.** Count test files, test functions, assertion density.
2. **Classify test types.** Unit, integration, end-to-end, benchmark.
3. **Identify structural gaps.** Missing test directories, no CI integration, no fixtures.
4. **Recommend architecture:**
   - Test directory structure matching source layout.
   - Shared fixtures and helpers.
   - Integration test separation (build tags in Go, markers in pytest).
   - CI pipeline integration.
5. **Output to `.agents/test/strategy.md`.**

## What Makes Good Tests vs Bad Tests

### Good Tests

- **Assert behavioral correctness.** Test what the function does, not that it exists.
- **Use exact expected values.** `assert result == Config(name="foo", count=3)` -- verifies the full output.
- **Cover error paths.** Error conditions are where bugs hide. Test them explicitly.
- **Descriptive names.** `TestParseConfig_InvalidYAML_ReturnsError` tells you what broke when it fails.
- **Independent.** Each test runs in isolation. No shared mutable state between tests.
- **Fast.** Unit tests should run in milliseconds. Slow tests get skipped.

### Bad Tests (Banned)

- **Coverage-padding.** Tests that assert `!= nil` or `!= ""` solely to inflate coverage metrics. Every test must assert a specific expected value.
- **Zero-assertion smoke tests.** `func TestFoo(t *testing.T) { Foo() }` -- proves nothing except "doesn't panic."
- **Tautological assertions.** `assert foo(x) == foo(x)` -- tests the test framework, not the code.
- **Implementation-coupled tests.** Tests that break when you refactor internals without changing behavior. Test the interface, not the implementation.
- **Flaky tests.** Tests that depend on timing, network, or ordering. Mock external dependencies. Use deterministic inputs.

If you find existing tests that match the "bad" patterns, flag them in the summary but do not delete them without user confirmation.

## Specialized Test References

- [references/conformance-harnesses.md](references/conformance-harnesses.md) -- Contract, compatibility, schema, and process conformance patterns
- [references/fuzzing.md](references/fuzzing.md) -- Fuzz targets, seed corpora, invariants, and crash triage
- [references/golden-artifacts.md](references/golden-artifacts.md) -- Golden file modes, update discipline, and artifact diff review
- [references/real-service-e2e.md](references/real-service-e2e.md) -- Real-service integration tests with non-production safety gates

## Integration with Other Skills

| Skill | Integration |
|-------|-------------|
| `$standards` | Loaded in Step 0 for language-specific test conventions |
| `$refactor` | Cross-referenced in Step 2 to prioritize high-risk untested code |
| `$validate` | After test generation, run `$validate` to validate overall code quality |
| `$implement` | During implementation, invoke `$test --mode=tdd` for test-first workflow |
| `$review` | Tests generated here help `$review` verify fixes |

## Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--mode` | `generate` | Execution mode: generate, coverage, strategy, tdd |
| `--scope` | `.` | Directory or file to target (e.g., `./internal/parser/`) |
| `--min-coverage` | none | Target coverage percentage; keep generating until met |
| `--dry-run` | off | Show what tests would be generated without writing files |

## Output Artifacts

All artifacts are written to `.agents/test/`:

| File | Contents |
|------|----------|
| `coverage-raw.txt` | Raw coverage tool output |
| `coverage-func.txt` | Per-function coverage breakdown (Go) |
| `coverage.json` | Machine-readable coverage (Python) |
| `gaps.md` | Ranked list of coverage gaps |
| `summary.md` | Before/after coverage delta and test inventory |
| `tdd-log.md` | TDD cycle log (tdd mode only) |
| `strategy.md` | Test architecture recommendations (strategy mode only) |
