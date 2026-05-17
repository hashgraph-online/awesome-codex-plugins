# Testing Strategies Reference

## Strategic Framework — How to Decide What to Test

Before selecting strategies, assess: **what is the cost if this code breaks in production, and what is the cheapest way to prevent it?**

### Risk-Based Prioritization

```
Test Priority = (Blast Radius × Change Frequency × Complexity) / Cost of Test
```

Score each dimension 1-5, sum them. Score >= 12 needs a test. Score >= 15 needs multiple strategies.

### The Testing Trophy (Current Consensus)

The testing pyramid (many unit, few integration, fewer E2E) is outdated. The **Testing Trophy** (Kent Dodds) reflects modern tooling economics:

- **Static analysis** (base) — type checking, linting. Catches typos and basic mistakes.
- **Unit tests** (small) — only for pure functions with complex logic.
- **Integration tests** (LARGEST layer) — components working together. Highest ROI.
- **E2E tests** (top) — few, critical user journeys only.

"The more your tests resemble the way your software is used, the more confidence they can give you." Unit tests can pass while the system is broken. Integration tests catch real failures.

### Effectiveness Data (OOPSLA 2025)

An empirical evaluation of property-based testing across 100 popular Python packages found:
- Property-based tests catch **39.14% of mutations** vs 6.6% for unit tests
- This is a **~6x factor** of effectiveness per test written
- Genuine bugs found in mature, heavily-tested libraries (including NumPy)

**Implication:** for data transformations, algorithms, and invariant-heavy code, property-based tests should be the PRIMARY strategy, not an afterthought.

---

## Core Philosophy

Tests exist for two reasons only: (1) find bugs in code just written, (2) catch regressions in future changes. Everything else is ritual.

### The 9 Principles

1. **Code first, test smart.** Understand the implementation's tensions and fragile points before writing tests. The implementation reveals WHERE bugs will hide — blind test-first misses this.

2. **Test the API, not the internals.** Always test through the public interface. If the implementation changes, tests should still pass.

3. **Test states, not lines.** Code coverage measures lines executed, but bugs live in STATE SPACE. A function with 3 branches and 2 parameters has 12+ states — testing 3 fixed inputs covers a fraction.

4. **Informed black-box.** Use implementation knowledge to craft inputs that stress boundary conditions, but test through the public API. Threshold at 256? Test 255, 256, 257.

5. **Randomize relentlessly.** Fixed test data explores a fixed slice of state space. Random data explores vastly more. Property-based testing with 100 random cases finds bugs that 10 handpicked cases miss.

6. **Bias your randomness.** Pure random data is wasteful. Bias generators toward boundary values, edge cases, and structures your code handles. For a JSON parser: generate mostly-valid JSON with occasional corruption, not random bytes.

7. **Verify invariants, not outputs.** Instead of checking "output == expected_fixed_value", check "output satisfies invariant." Invariants survive implementation changes. Examples: sorted output is still sorted, round-trip encoding/decoding produces the original, aggregated totals match input totals.

8. **Compare against simplicity.** Write a simple, obviously-correct reference implementation inside the test. Run both on the same random inputs. Differences are bugs.

9. **Speed is correctness.** Slow tests don't get run. Tests that don't run don't find bugs. Optimize for fast execution: in-memory over I/O, parallel over sequential, skip unnecessary setup.

---

## Strategy Catalog

### 1. Boundary Stress Testing

**When:** Any function with thresholds, limits, or type boundaries.

**How:**
1. Read the implementation. Find every comparison (`<`, `>`, `<=`, `>=`, `==`, `!=`), every constant, every limit.
2. For each boundary value N: test N-1, N, N+1.
3. For type boundaries: test at min/max of type (0, -1, MAX_INT, empty string, null).
4. For collection sizes: test empty, one element, boundary size, boundary+1.

**Example boundaries to look for:**
- Buffer sizes, page sizes, batch sizes
- Timeout values, retry counts
- String length limits, array capacity
- Enum ranges, status code categories
- Pagination offsets, limit values

### 2. Property-Based Testing

**When:** Data transformations, serialization/deserialization, pure functions, algorithms. OOPSLA 2025 data shows PBT is ~6x more effective than unit tests at catching mutations — prioritize this for any code that transforms data.

**Properties to check:**
- **Round-trip:** encode(decode(x)) == x
- **Idempotence:** f(f(x)) == f(x)
- **Monotonicity:** if x < y then f(x) <= f(y)
- **Preservation:** len(transform(list)) == len(list)
- **Commutativity:** f(a, b) == f(b, a) where expected
- **Associativity:** f(f(a, b), c) == f(a, f(b, c))
- **Invariant maintenance:** sum(input) == sum(output) for redistributions

**Libraries:** hypothesis (Python), jqwik (Java), fast-check (TypeScript), swift-testing macros (Swift)

### 3. Invariant / Reference Implementation Testing

**When:** Complex algorithms where a simpler (slower) implementation can serve as oracle.

**How:**
1. Write a naive, obviously-correct implementation inside the test
2. Generate random inputs
3. Run both implementations on same inputs
4. Assert outputs match

**Examples:**
- Optimized sort vs Python's built-in sort
- Custom hash map vs standard library HashMap
- Optimized query builder vs string concatenation
- Compression: decompress(compress(data)) == data AND len(compressed) <= len(data)

### 4. Golden Fixture Regression Testing

**When:** Data pipelines, computation-heavy services, API endpoints with complex responses.

**Architecture:**
1. **Capture:** Run against real data, serialize inputs + outputs as fixtures (Parquet, JSON)
2. **Regression:** Load fixtures, re-execute, compare against golden baseline
3. **Tolerance:** Approximate comparison for floats, exclude volatile fields (timestamps, IDs)

**Infrastructure:**
- Pytest markers for selective execution (`@pytest.mark.e2e`)
- Root conftest mocking external connectors at collection time
- Parametrized fixtures for multiple configurations
- Computation caching: run expensive ops once, share across tests
- Checkpoints: capture intermediate states, not just final output

**Comparison utilities needed:**
- `normalize(obj)` — sort dicts, scrub volatile fields (timestamps, IDs), round floats, canonical JSON
- `assert_dataframes_equal(actual, expected, tolerance=1e-6, exclude_cols=[...])`
- `diff_report(actual, expected)` — per-row differences for debugging

**Workflow:** first run captures baseline to JSON/YAML files → commit baselines to VCS → subsequent runs diff against baselines → `--force-regen` flag to update baselines when changes are intentional. See `refactoring-workflow.md` for complete implementation.

### 5. E2E API Lifecycle Testing

**When:** REST/GraphQL endpoints, especially write operations.

**Read endpoints:**
- Capture: call endpoint with representative params, save request + response
- Regression: mock DB/service reads to return captured inputs, assert response matches golden

**Write endpoints — full CRUD lifecycle:**
1. Verify clean state (resource doesn't exist)
2. CREATE — assert 201, verify response schema, verify DB state
3. READ — assert created resource matches
4. UPDATE — assert 200, verify changed fields, verify unchanged fields preserved
5. HISTORY — assert audit trail if applicable
6. DELETE — assert 200/204, verify resource removed
7. Verify clean state restored

**Comparison:**
- Normalize responses: sort lists by natural keys, canonical JSON
- Exclude volatile: timestamps, auto-generated IDs, row numbers
- Status code categories: 2xx = success (including 207 multi-status)
- Float tolerance for computed values

### 6. Live Comparison Testing

**When:** Migrating from legacy to new implementation.

**How:**
1. Start both services (legacy on port A, new on port B)
2. Send identical requests to both
3. Normalize both responses
4. Diff — differences are regressions or intentional changes

**Infrastructure:**
- Script to start both services with correct configs
- Known expected differences documented and excluded
- Report: PASS/FAIL per endpoint with diff details

### 7. Real Database Integration Testing

**When:** SQL queries, ORM operations, repositories, data pipelines, or anything where the DB IS the logic (constraints, triggers, stored procedures).

**Core rule:** NEVER substitute SQLite for PostgreSQL in tests. SQLite accepts strings in integer columns, lacks JSONB, window functions, partial indexes, and row-level locking. Code passes SQLite tests and fails in production.

See `integration-patterns.md` for isolation strategies, fixture patterns, Docker Compose templates, and synthetic data generation.

### 8. Browser E2E Testing (Playwright)

**When:** User-facing web applications. Test user-visible behavior, not implementation.

**Three non-negotiable rules:**
1. Semantic locators: `getByRole` > `getByText` > `getByTestId` > never CSS/XPath
2. Web-first assertions: `await expect(loc).toBeVisible()`, never synchronous `isVisible()`
3. Page Object Model with lazy getter locators beyond trivial project size

See `e2e-browser-patterns.md` for POM architecture, locator priority, visual regression, and CI/CD integration.

### 9. Characterization / Approval Testing (Golden Master)

**When:** Legacy code without tests that needs refactoring.

**Core concept:** Capture the ACTUAL behavior of existing code — what it DOES, not what it should do. Any diff after refactoring = behavior changed.

**Process:**
1. **Identify seams** — points to alter behavior without changing source (classes, interfaces, config)
2. **Capture** — exercise code with representative inputs, serialize all outputs
3. **Normalize** — scrub volatile data (timestamps, IDs, random values) for deterministic comparison
4. **Regress** — after refactoring, diff against baseline

**Critical nuance:** Characterization tests capture bugs too. The baseline includes incorrect behavior. Use as a bridge, then replace with behavioral tests once you understand the code.

**Feathers' techniques:** Sprout Method (new logic in isolation, called from legacy), Wrap Method (rename original, wrap with same name), Scratch Refactoring (explore then REVERT ALL). See `refactoring-workflow.md` for full patterns.

### 10. Concurrency & Atomicity Testing

**When:** Async code, shared resources, atomic operations, booking systems, counters, rate limiters.

**Three core patterns:** race condition (concurrent claims on scarce resource — exactly one wins), idempotency (duplicate requests → same result), stress (N concurrent ops maintain invariants). See `language-templates.md` for scaffolds.

**Key rule:** Concurrency bugs are non-deterministic. A test that passes once proves nothing — it must pass 100 times. Use `@settings(max_examples=500)` or explicit loops.

### 11. Contract Testing

**When:** Multiple services communicate via API. Teams deploy independently.

**Consumer-Driven Contracts (Pact):**
1. **Consumer** defines expectations → generates pact files (JSON contracts)
2. **Provider** verifies pact files independently
3. `can-i-deploy` gate prevents incompatible deployments

**Critical anti-pattern:** Over-specifying contracts. If consumer only needs `name`, don't assert on `address` and `phone`. Test the minimum contract.

**Alternative:** OpenAPI schema validation — less powerful than Pact but lower overhead for simple cases.

### 12. Mutation Testing (Test Quality Verification)

**When:** Verifying tests actually catch bugs, not just execute code. Coverage measures execution; mutation testing measures assertion quality.

**How:** Introduce deliberate bugs (mutants) into source code. Tests still pass → tests don't verify that code path.

**Mutation score:**
- 85-90%+: Excellent — strong test suite
- 60-80%: Decent — room for improvement on edge cases
- <60%: Weak — tests verify execution, not correctness

**Primary approach:** manual mutation check — change expected values in assertions, verify tests fail, restore. Zero dependencies, equally effective for targeted verification.

**Optional tool:** mutmut (Python, zero-config) automates this at scale for CI nightly jobs.

**When to apply:** Critical business logic (payments, auth), stable APIs, complex algorithms. Skip for: simple CRUD, trivial getters, prototypes, frequently changing code.

**Practical tip:** Schedule mutation testing as a nightly CI job, not on every commit. Focus on the critical 10-20% of the codebase.

**Lightweight alternative:** If dedicated tools are too heavy, apply the mutation check manually during test generation — temporarily change expected values in assertions, verify tests fail, restore. This achieves the same validation without tooling overhead.

### 13. Flaky Test Prevention

**When:** Any test suite in CI. Flaky tests erode trust until developers ignore failures.

**Common causes and fixes:**

| Cause | Detection | Fix |
|-------|-----------|-----|
| Time-dependent logic | Tests fail near midnight/DST/timezone boundaries | Inject clock: `freezegun` (Python), `jest.useFakeTimers()` (TS) |
| Random data without seed | Unreproducible failures | `factory.random.reseed_random(42)` or `Faker.seed(42)` in conftest |
| Test ordering dependency | Tests pass alone, fail in suite | Run with `pytest-randomly` to detect; fix shared state |
| Network calls in tests | Timeout-dependent failures | Mock with `responses`, `httpx_mock`, or `page.route()` |
| Race conditions in async tests | Intermittent failures under load | Use `asyncio.wait_for` with explicit timeouts, never `asyncio.sleep` |
| Shared mutable state | Test A pollutes state for test B | Function-scoped fixtures with transaction rollback |
| File system artifacts | Leftover files from previous runs | Use `tmp_path` fixture (pytest) or tempdir |

**Prevention checklist for generated tests:**
1. No calls to `time.time()`, `datetime.now()`, or `Date.now()` — inject or mock
2. No hardcoded ports — use dynamic port assignment
3. No `sleep()` — use condition-based waiting or web-first assertions
4. Each test creates its own state — never rely on test execution order
5. Deterministic random seeds for any random data generation

### 14. Database Migration Testing

**When:** Alembic, Flyway, Liquibase, or Prisma migrations — especially when schema changes accompany code changes.

**Test patterns:**
1. **Up/down round-trip:** Apply → verify schema → rollback → verify original restored
2. **Data preservation:** Seed → migrate → verify data correctly transformed
3. **Idempotency:** Applying twice succeeds silently or fails cleanly

**CI step:** `alembic upgrade head && alembic downgrade -1 && alembic upgrade head`. See `integration-patterns.md` for implementation.

---

## Anti-Patterns — What NOT to Generate

| Anti-pattern | Why it's bad | What to do instead |
|---|---|---|
| `assertNotNull(result)` as sole assertion | Proves function returns something, not that it's correct | Assert specific value, shape, or invariant |
| `assertEquals(result, result)` | Tautology — always passes | Assert against independently computed expected value |
| Test with no assertions | Tests that code doesn't crash, nothing else | Add invariant or property assertions |
| Hardcoded input/output pairs only | Tests one state, misses boundary cases | Add property-based tests alongside specific cases |
| Mocking everything | Tests the mocks, not the code | Mock only external boundaries (DB, HTTP, filesystem) |
| Testing private methods | Couples tests to implementation | Test through public API |
| One test per method (happy path) | Misses error paths, boundaries, state interactions | Multiple tests per method: happy, error, boundary, property |
| `try/catch` that swallows assertion errors | Test always passes | Let assertions propagate |
| Tests that depend on execution order | Fragile, non-reproducible | Each test sets up its own state |
| Slow tests without `@pytest.mark.slow` / tag | Block fast feedback loop | Mark slow tests, run separately |
