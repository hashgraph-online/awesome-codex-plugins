---
name: test
description: Generate tests and coverage plans.
---
# Test Skill

Generate real tests, run them, and leave reproducible coverage or TDD evidence.
Do not stop at a plan unless the requested mode is `strategy`.

## Critical Constraints

- **Why: behavior is the contract.** Derive tests from acceptance scenarios and
  public behavior, not implementation details or coverage percentages alone.
- **Why: prove new behavior.** In TDD mode record a real failing test before the
  minimal implementation; a test that starts green is not RED evidence.
- **Why: avoid false confidence.** Assert exact values, error types/messages,
  and branch outcomes; ban zero-assertion, tautological, and padding tests.
- **Why: keep suites trustworthy.** Tests must be deterministic, isolated, and
  independent of timing, ordering, production services, or mutable shared state.
- **Why: protect user intent.** Report a product bug discovered by a test; do
  not silently change product behavior or delete existing tests without approval.
- **Why: close with proof.** Run the narrow test after each edit, then the
  relevant suite and coverage command before handing work downstream.

## Modes

| Mode | Use when | Required result |
|---|---|---|
| `generate` | writing tests for existing code | passing focused and suite tests |
| `coverage` | finding and filling important gaps | before/after coverage plus tests |
| `tdd` | implementing new behavior test-first | logged RED → green → refactor cycles |
| `strategy` | designing test architecture only | inventory, risks, and recommendations |

Default to `generate`. Flags: `--mode`, `--scope`, `--min-coverage`, and
`--dry-run` narrow the workflow but never weaken its evidence requirements.

## Workflow

### 1. Bind tests to behavior

When a caller-supplied `.feature` file has scenarios, work forward from each
Given/When/Then. Name one covering test after the behavior, and add
`@covered-by:<test-path>[::<TestName>]` above the scenario. Prove the mapping:

```bash
bash scripts/check-scenario-coverage.sh skills/<skill>/references/<name>.feature --run
```

Without scenarios, inventory public behavior, error paths, branches, and edge
cases. Rank gaps by risk: high complexity plus low coverage first.

### 2. Detect the language and baseline

Stop at the first applicable project marker and consult the Standards skill for it:

| Marker | Framework | Baseline command |
|---|---|---|
| `go.mod` | Go test | `go test -coverprofile=coverage.out ./...` |
| `pyproject.toml`, `setup.py` | pytest | `pytest --cov --cov-report=term-missing` |
| `package.json` | Jest/Vitest | `npx jest --coverage` or `npx vitest run --coverage` |
| `Cargo.toml` | cargo test | `cargo tarpaulin --out Lcov` |

Write raw coverage to `.agents/test/coverage-raw.txt`, a ranked gap inventory
to `.agents/test/gaps.md`, and language-native machine output where available.

### 3. Write the smallest valuable tests

Read the target function and its callers before writing tests. Cover every
branch and error return with exact expected results. Use descriptive test names
and one behavioral focus per table row or parameter set.

Load specialized guidance only when its trigger applies:

- API, CLI, schema, or compatibility contracts: [conformance-harnesses.md](references/conformance-harnesses.md)
- Parsers, serializers, or hostile input: [fuzzing.md](references/fuzzing.md)
- Generated output or snapshots: [golden-artifacts.md](references/golden-artifacts.md)
- Invariant-heavy behavior: [metamorphic-testing.md](references/metamorphic-testing.md)
- Real databases, queues, APIs, or services: [real-service-e2e.md](references/real-service-e2e.md)

For golden updates, follow [golden-artifact-strategy.md](references/golden-artifact-strategy.md)
and review the artifact diff; regeneration alone is not acceptance.

### 4. Run RED, green, and refactor checks

In `tdd` mode:

1. Write one behavioral test and run it; require a relevant failure.
2. Implement only enough to pass that test.
3. Refactor under green without changing the test contract.
4. Run the focused test and the relevant suite after each cycle.
5. Append the exact commands and outcomes to `.agents/test/tdd-log.md`.

In other mutating modes, run each new test immediately, then the owning package
or module, then the relevant project suite. A failure caused by a wrong test is
fixed in the test; a product defect is reported explicitly rather than masked.

**Checkpoint:** before coverage measurement, confirm the focused test and the
relevant suite are green and the recorded RED evidence names the intended behavior.

### 5. Measure and hand off

Re-run the baseline coverage command. Summarize before/after coverage, tests
added, remaining high-risk gaps, bugs found, and exact validation commands in
`.agents/test/summary.md`. Supply that evidence to Validate when the test
change accompanies a product slice or is ready for acceptance.

## Language Rules

- **Go:** use `<source>_test.go`, `Test<Uppercase>`, table-driven cases, and
  exact output assertions; never `cov*_test.go` or `*_extra_test.go`.
- **Python:** use pytest fixtures and parametrization; type test helpers.
- **JS/TS:** group `describe`/`it` by public behavior and mock external services,
  not internal implementation.
- **Rust:** prefer focused unit tests plus integration tests at public boundaries;
  keep fixtures deterministic.

## Strategy Mode

Inventory test files, functions, assertion density, unit/integration/e2e split,
fixtures, and CI wiring. Write `.agents/test/strategy.md` with prioritized
structural gaps and a test architecture; do not generate code in this mode.

## Output Specification

- **Artifact directory:** `.agents/test/` plus test files in the target's
  language-native locations.
- **Filename convention:** `coverage-raw.txt`, `coverage-func.txt` or
  `coverage.json`, `gaps.md`, `summary.md`, `tdd-log.md`, and `strategy.md`.
- **Serialization/schema format:** Markdown evidence reports, native coverage
  text/profile formats, and JSON where the coverage tool supports it.
- **Validator command:** run the focused test, relevant suite, coverage command,
  and `bash scripts/check-scenario-coverage.sh ... --run` when scenarios exist.
- **Downstream use:** factual evidence that a caller may supply to Validate.

## Quality Rubric

- Every acceptance scenario maps to a passing behavioral test.
- New behavior has authentic RED evidence before implementation.
- Assertions are exact and cover happy, edge, and error paths.
- Tests are deterministic, isolated, fast at the unit layer, and maintainable.
- Coverage changes prioritize risk and never substitute for behavioral proof.
- Artifacts name the commands, results, remaining gaps, and discovered defects.

## Examples

**Generate mode:** inspect a parser, baseline coverage, add table-driven happy,
malformed, and empty-input cases, run focused plus package tests, then record the
coverage delta and remaining gaps.

**TDD mode:** write `TestParseConfig_MissingName`, capture its failing output,
add the minimum validation, rerun green, refactor, run the full package, and log
the cycle in `tdd-log.md`.

## Troubleshooting

| Problem | Response |
|---|---|
| new test starts green | strengthen it until it proves the missing behavior |
| flaky timing/network test | inject deterministic clocks/data and fake the external boundary |
| coverage rises but risk remains | add behavior and error-path assertions, not padding |
| golden update is large | inspect the diff and split intentional from accidental change |
| product bug discovered | preserve the reproducer, report the bug, and do not mask it |

## References

- [test.feature](references/test.feature) — executable behavior contract
- [conformance-harnesses.md](references/conformance-harnesses.md)
- [fuzzing.md](references/fuzzing.md)
- [golden-artifacts.md](references/golden-artifacts.md)
- [golden-artifact-strategy.md](references/golden-artifact-strategy.md)
- [metamorphic-testing.md](references/metamorphic-testing.md)
- [real-service-e2e.md](references/real-service-e2e.md)
