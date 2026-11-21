---
name: principle-test-behavior-not-implementation
description: Use when writing or changing a test, or deciding whether one should stay. Check what callers can see through the interface they call, so the test breaks when behavior breaks and survives changes to internals alone.
disable-model-invocation: true
---

# Test behavior, not implementation

A test should check results visible to the code's users via the interface they call. It should fail once that visible behavior breaks and stay green when nothing but the internals move.

## When it applies

Writing a test, changing one, or deciding whether to keep one.

## Terms

- **Users**: callers, end users, and other services.
- **Behavior**: whatever users can observe. That covers return values, thrown errors, state they can read back afterwards, and effects on external systems (an outgoing request, a database row, a published message).
- **Implementation**: everything they cannot see, meaning private helpers, the order of internal calls, intermediate data, and which internal component performed the work.

## What to do

1. Run two thought experiments on each test.
   - **Break the behavior.** Return a wrong value, drop an effect, or duplicate one. If the test stays green, it shows nothing. Usual reasons: the assertion is weaker than the contract, the expected value came from the code being tested, the test restates a constant or prompt string without running the code that uses it, or it asserts on data the test built itself.
   - **Restructure the internals** while keeping every observable result. If the test fails, it is pinned to implementation. It will need rewriting on every refactor and catches no bugs.
2. Keep a test only if it catches the first change and tolerates the second. Rewrite or remove the others.
3. To write a good test, exercise the code through the interface its users call, using a concrete input. Work out the expected result by reading the requirement, never by running the code, and assert precisely what the contract guarantees.
4. Let the contract, not assertion style, decide what counts:
   - If the promise is that a request without a valid token never reaches the database, asserting the database client received no query is behavior. Pair it with a positive case where a valid token does produce a query, so the test demonstrably can observe calls.
   - The payload sent to a mocked external service is behavior, because that service receives it. Calling an internal helper is an implementation detail.
   - An empty list is a precise expected value when nothing should match. It is a hollow assertion when the test only needed some result.
   - Callers do not read the exact wording of an error message. They branch on the error type, so the type is the contract. For an auth failure, assert the `Unauthorized` type and the 401 status, not the sentence.
5. A test can pin an invariant rather than a call: for instance, a key required in both of two tables, or a type assertion checked at compile time. Here the invariant is the behavior.

Security tests are where hollow assertions do the most damage. A test named `test_rejects_path_traversal` that sends `../etc/passwd` and asserts "an exception was raised" passes when the code crashes for an unrelated reason. Assert the specific rejection and add a positive case that reads a legitimate file through the same path.

## The failure it prevents

Tests that never catch bugs, tests that break on every refactor, and expected values that confirm themselves.

## Done when

Each kept test passes both thought experiments.

Related: [principle-migrate-callers-then-delete-legacy-apis](../principle-migrate-callers-then-delete-legacy-apis/SKILL.md), [principle-foundational-thinking](../principle-foundational-thinking/SKILL.md), [tdd](../tdd/SKILL.md).
