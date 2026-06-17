# De-Sloppify Pattern

> Separate cleanup pass after implementation. Two focused agents > one constrained agent.

## Problem

Implementation agents optimize for completeness — they over-generate:
- Unnecessary type-system tests (testing Go's type system, not business logic)
- Redundant nil checks on values that can't be nil
- Console/debug logging left behind
- Commented-out code "just in case"
- Over-defensive error handling for impossible scenarios
- Coverage-padding tests that don't assert behavior

Telling the implementer "don't do X" makes it slower and worse at the main job.

## Solution: Two-Phase Execution

### Phase 1: Implement (no constraints)
The implementation worker focuses purely on making the feature work with full TDD:
```
Implement <issue-description>.
Write tests that verify behavioral correctness.
```

### Phase 2: De-Sloppify (cleanup only)
A separate cleanup worker reviews the implementation output:
```
Review the changes from the previous implementation wave.
Remove ONLY:
- Tests that assert type-system behavior (e.g., "field is not empty string")
- Redundant nil/error checks on values guaranteed by the caller
- Console.log / fmt.Println debugging statements
- Commented-out code blocks
- Coverage-padding tests (trivial != nil or != "" assertions)
- Unused imports or variables

DO NOT:
- Change business logic
- Remove error handling at system boundaries
- Remove tests that assert behavioral correctness
- Add new functionality
```

## Integration with /crank

### Automatic Mode (recommended)
After each implementation wave, crank can optionally run a de-sloppify pass:

```
Wave N: Implement issues [A, B, C]  → /swarm executes
Wave N.5: De-sloppify wave N output → single cleanup worker
Wave N+1: Next implementation wave
```

The de-sloppify wave is lightweight — single worker, no parallelism needed.

### Manual Mode
```bash
/validate --quick recent   # quick check, no agents
# Review findings, then:
# Apply cleanup manually or spawn cleanup worker
```

## What De-Sloppify Catches

| Slop Type | Detection | Example |
|-----------|-----------|---------|
| Type-system tests | Test name contains "Type", asserts only `!= nil` or `!= ""` | `TestFoo_ReturnsNonNil` |
| Debug logging | `fmt.Print`, `console.log`, `print()` in non-test code | `fmt.Println("DEBUG:", value)` |
| Commented code | Blocks of `// old implementation` | Entire functions commented out |
| Dead imports | Imported but unused packages | `"fmt"` when only `log` is used |
| Over-defensive | nil checks after guaranteed-non-nil calls | `if err != nil` after `strings.Join()` |
| Coverage padding | `cov*_test.go` files, trivial assertions | `assert result != nil` |

## Metrics

Track de-sloppify effectiveness:
- Lines removed per wave (target: 5-15% of implementation output)
- False positives (removed something that was needed) — should be <1%
- Time cost (should be <20% of implementation wave time)

If de-sloppify consistently removes >20% of implementation output, the implementation prompt needs tightening.
If it removes <2%, skip de-sloppify for efficiency.
