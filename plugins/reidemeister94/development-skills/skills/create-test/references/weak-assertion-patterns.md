# Weak Assertion Patterns

## Detection Rules

When auditing test quality, search for these patterns. Each indicates a test that exists without testing anything meaningful.

### Python (pytest)

| Pattern | Severity | Why it's weak |
|---------|----------|---------------|
| `assert result is not None` (sole assertion) | HIGH | Proves function returns, not that it's correct |
| `assert result` / `assert bool(result)` (sole) | HIGH | Truthy check — empty list, 0, empty string all fail |
| `assert isinstance(result, ...)` (sole) | MEDIUM | Type check without value verification |
| `assert len(result) > 0` (sole) | MEDIUM | Non-empty but content unchecked |
| Test function with no `assert` statement | CRITICAL | Tests nothing — only that code doesn't crash |
| `assert result == result` | CRITICAL | Tautology — always passes |
| `try: ... except: pass` wrapping assertions | CRITICAL | Swallows assertion failures |
| `# TODO: add assertions` | HIGH | Placeholder that will never be filled |
| `assert True` | CRITICAL | Unconditional pass |
| `pytest.skip()` without condition | MEDIUM | Permanently disabled test |

**Search patterns (regex):**
```
# No assertions in test function
def test_\w+\([^)]*\):[^}]*?(?=def |class |\Z)  # then check no "assert" inside

# Sole not-None assertion
^\s*assert \w+ is not None\s*$

# Tautology
assert (\w+) == \1

# Swallowed assertions
except.*:\s*pass

# Placeholder
assert True
```

### Java (JUnit / AssertJ)

| Pattern | Severity | Why it's weak |
|---------|----------|---------------|
| `assertNotNull(result)` (sole) | HIGH | Null check without value verification |
| `assertTrue(result != null)` (sole) | HIGH | Same as above, worse readability |
| `assertEquals(result, result)` | CRITICAL | Tautology |
| Test method with no assertion | CRITICAL | Tests nothing |
| `@Disabled` without reason | MEDIUM | Permanently disabled |
| `catch (Exception e) { /* ignore */ }` | CRITICAL | Swallows assertion errors |
| `assertThat(result).isNotNull()` (sole) | HIGH | AssertJ not-null only |

### TypeScript (vitest / jest)

| Pattern | Severity | Why it's weak |
|---------|----------|---------------|
| `expect(result).toBeDefined()` (sole) | HIGH | Defined but correct? |
| `expect(result).not.toBeNull()` (sole) | HIGH | Not null but correct? |
| `expect(result).toBeTruthy()` (sole) | HIGH | Truthy is not correct |
| `expect(result).toBe(result)` | CRITICAL | Tautology |
| `it(...)` with no `expect()` | CRITICAL | Tests nothing |
| `it.skip(...)` | MEDIUM | Permanently disabled |
| `expect(result).toMatchSnapshot()` (sole, large object) | MEDIUM | Snapshot tests are brittle and hide regressions |

### Swift (XCTest / swift-testing)

| Pattern | Severity | Why it's weak |
|---------|----------|---------------|
| `XCTAssertNotNil(result)` (sole) | HIGH | Existence without correctness |
| `#expect(result != nil)` (sole) | HIGH | Same for swift-testing |
| Test function with no `XCTAssert*` / `#expect` | CRITICAL | Tests nothing |
| `XCTAssert(true)` | CRITICAL | Unconditional pass |

---

## Quality Scoring

### Assertion Density

```
assertion_density = total_assertions / total_test_functions
```

| Score | Rating | Action |
|-------|--------|--------|
| >= 3.0 | Excellent | No action needed |
| 2.0 - 2.9 | Good | Acceptable |
| 1.0 - 1.9 | Weak | Add invariant/property assertions |
| < 1.0 | Critical | Tests are hollow — rewrite |

### Weak Assertion Ratio

```
weak_ratio = weak_assertions / total_assertions
```

| Score | Rating | Action |
|-------|--------|--------|
| 0.0 | Excellent | No action needed |
| 0.01 - 0.1 | Acceptable | Review flagged assertions |
| 0.1 - 0.3 | Concerning | Replace weak assertions with specific checks |
| > 0.3 | Critical | Most tests prove nothing — rewrite |

### Test Strategy Coverage

For a well-tested module, expect at least:

| Strategy | Minimum | Applies when |
|----------|---------|-------------|
| Boundary tests | 1 per identified threshold | Always for functions with parameters |
| Property-based tests | 1 per data transformation | Functions that transform, compute, or aggregate |
| Invariant tests | 1 per complex algorithm | When simpler reference exists |
| Error path tests | 1 per error branch | Functions with explicit error handling |
| Random stress | 1 per module | Complex logic with many states |

### Overall Quality Score

```
quality = (assertion_density_score * 0.3)
        + ((1 - weak_ratio) * 0.3)
        + (strategy_coverage * 0.4)

Where:
  assertion_density_score = min(1.0, assertion_density / 3.0)
  strategy_coverage = strategies_applied / strategies_applicable
```

| Score | Rating |
|-------|--------|
| >= 0.8 | Strong — tests likely find bugs |
| 0.6 - 0.79 | Adequate — some gaps |
| 0.4 - 0.59 | Weak — tests exist but miss failure modes |
| < 0.4 | Hollow — tests are ritual, not protection |
