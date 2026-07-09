# Testing Strategies Reference

Canonical strategy-selection map for SKILL.md Step 3. Pick by code characteristic; the named strategies (boundary, property-based, round-trip/invariant, golden fixture, CRUD lifecycle, characterization) are standard practice — apply them as usual. Non-obvious routing and project rules below.

## Route by characteristic

- SQL / ORM / repositories / DB-as-logic, and DB migrations → `integration-patterns.md`
- Legacy code before refactoring (characterization / golden master) → `refactoring-workflow.md`
- Verifying assertions actually catch bugs → mutation check (SKILL.md Step 5)

## Two non-obvious rules

**NEVER substitute SQLite for PostgreSQL.** SQLite accepts strings in integer columns, lacks JSONB, window functions, partial indexes, and row-level locking. Code passes SQLite tests and fails in production.

**Concurrency bugs are non-deterministic.** A test that passes once proves nothing — it must pass ~100x. Use `@settings(max_examples=500)` or explicit loops.

## Flaky-test causes (avoid in generated tests)
Time-dependent logic (inject/mock the clock); unseeded random data; test-ordering dependence (each test sets up its own state); live network calls (mock); hardcoded ports (dynamic assignment); `sleep()` (condition-based waiting); leftover filesystem artifacts (`tmp_path`).
