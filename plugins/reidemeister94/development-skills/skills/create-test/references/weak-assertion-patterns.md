# Weak Assertion Patterns

When auditing test quality, grep tests for these — each marks a test that runs without verifying anything. Replace with assertions on specific values, shapes, or invariants.

- Sole assertion that only checks existence/type/truthiness/non-empty: `assert x is not None`, `assert x`, `isinstance(x, ...)`, `len(x) > 0`; and the language equivalents — JUnit `assertNotNull` / `assertThat(x).isNotNull()`, vitest/jest `toBeDefined` / `not.toBeNull` / `toBeTruthy`, Swift `XCTAssertNotNil` / `#expect(x != nil)`.
- Tautology: `assert x == x`, `assertEquals(x, x)`, `expect(x).toBe(x)`.
- Unconditional pass: `assert True`, `XCTAssert(true)`.
- Test function with no assertion at all (CRITICAL — proves only that code does not crash).
- Assertions swallowed by `try/except: pass` or `catch { /* ignore */ }` (the failure never surfaces).
- Permanently disabled tests: `pytest.skip()`/`it.skip`/`@Disabled` without a condition or reason.
- `# TODO: add assertions` placeholders.
- Sole snapshot assertion on a large object (`toMatchSnapshot`) — brittle, hides regressions.
