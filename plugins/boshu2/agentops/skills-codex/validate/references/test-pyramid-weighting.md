# AI-Native Test Shape Weighting

> From analysis of 946 council verdicts: unit tests (L0–L1) found zero production bugs. L2+ tests (integration, E2E, smoke) found ALL real bugs.
> Vibe scoring must weight higher-level coverage proportionally. This is the empirical basis for the AI-native test shape (see `skills/standards/references/test-pyramid.md`).

## The Evidence

Across 14,753 analyzed sessions:
- **L0 (build):** Catches syntax errors only. No bugs found that weren't immediately obvious.
- **L1 (unit):** Zero production bugs caught. Useful for regression prevention but NOT for bug discovery.
- **L2 (integration):** Moderate bug discovery. Catches component interaction failures.
- **L3 (E2E/system):** Found the majority of real bugs. Tests full workflows.
- **L4 (smoke/zero-context):** 3–5x more issues found than self-review. Fresh-eye validation is the highest-value test.

## Scoring Weights

When computing the test coverage component of a vibe score:

| Level | Weight | Rationale |
|-------|--------|-----------|
| L0: Build passes | 1x | Table stakes — not a quality signal |
| L1: Unit tests pass | 1x | Regression prevention, not discovery |
| L2: Integration tests pass | 3x | Real interaction bugs caught here |
| L3: E2E tests pass | 5x | Highest bug-discovery rate |
| L4: Smoke/fresh-context | 5x | Catches what familiarity blinds |

## Impact on Vibe Verdicts

### PASS Requirements
- L0 + L1 passing is NECESSARY but NOT SUFFICIENT
- At least one L2+ test must exist for changed code paths
- If L3+ tests exist and pass, this is a strong positive signal

### WARN Triggers
- All tests are L0–L1 only (no integration or higher)
- Changed code paths have no dedicated test at any level
- Test count is high but all tests are trivial assertions (`!= nil`, `!= ""`)

### FAIL Triggers
- L2+ tests exist and are failing
- Changed code has zero test coverage at any level
- Test suite is entirely coverage-padding (no behavioral assertions)

## Recommendations to Judges

When reviewing test coverage in a vibe check:

1. **Count tests by level, not just total.** 50 unit tests and 0 integration tests is worse than 10 unit tests and 5 integration tests.

2. **Check test quality, not just quantity.** Trivial assertions (`!= nil`, `!= ""`) are banned per project rules. Each test must assert behavioral correctness.

3. **Prioritize coverage gaps at L2+.** If suggesting test improvements, suggest integration or E2E tests first, not more unit tests.

4. **Fresh-context validation is high-value.** A zero-context reviewer (different agent, fresh session) catching issues is worth more than the implementer's self-review.

## Integration with /test Skill

When vibe detects insufficient L2+ coverage:
- Recommend running `/test` with explicit level targeting
- Suggest specific integration test scenarios based on changed code paths
- Flag if the project has no integration test infrastructure at all
