---
name: django-test-data
description: Design faster, clearer Django test data and test structure with factories, setUpTestData, SimpleTestCase/TestCase choices, fixture-file cleanup, query optimization, and unit-vs-integration boundaries. Use when Django tests create too much data, rely on slow fixtures, overuse TransactionTestCase, duplicate setup, or need refactoring for speed without losing coverage.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Django Test Data
  category: Django
  tags: django,testing,test-data,factories,pytest
---

# Django Test Data

Most slow Django suites spend time building data they do not need or exercising full request/database paths for behavior that can be tested at a smaller boundary. Use this skill to reduce setup cost while keeping representative integration coverage.

## Refactoring Workflow

1. Map the behavior under test.
   - Identify the smallest useful boundary: function, form, model method, middleware, command helper, view, or full request path.
   - Keep a few integration tests for wiring; move detailed cases to unit tests where the boundary is clean.

2. Choose the fastest test base class.
   - `SimpleTestCase`: no database access.
   - `TestCase`: ordinary database tests with rollback.
   - `TransactionTestCase`: committed transaction behavior only.
   - `LiveServerTestCase`: browser/live-server tests only.

3. Remove broad fixture data.
   - Avoid large fixture files and base classes that always create objects.
   - Build only the data each test or class needs.

4. Use factories deliberately.
   - Start with small factory functions when the domain is simple.
   - Use Factory Boy or Model Bakery when relationships and variants become repetitive.

5. Share class-level data with `setUpTestData`.
   - Use `setUpTestData()` for database objects reused by multiple methods in a `TestCase`.
   - Avoid mutating shared in-memory objects across methods.

6. Optimize database access in test setup and assertions.
   - Use `select_related`, `prefetch_related`, or `bulk_create` where setup/query cost is the bottleneck.
   - Assert query counts for hot paths when performance is part of the contract.

Read [patterns.md](references/patterns.md) for examples and decision details.

## Decision Rules

- If a test does not need the database, use `SimpleTestCase`.
- If only some tests need the database, split them into separate classes.
- If a test requires committed transaction behavior, first check whether `captureOnCommitCallbacks()` or an inner `atomic()` is enough.
- If many tests share expensive objects, use `setUpTestData` instead of `setUp`.
- If fixture files are hard to understand or grow over time, replace them with factories.
- If a test depends on hard-coded auto-increment IDs, fix the assertion rather than enabling `reset_sequences=True`.
- Combine assertions when they describe one behavior produced by one expensive action.

## Common Mistakes

- Testing form validation only through rendered HTML instead of inspecting form errors directly.
- Leaving management-command business logic inside `handle()`, forcing tests through `call_command()`.
- Using `TransactionTestCase` as the default.
- Putting data in a base `TestCase` that only a few subclasses need.
- Treating factories as permission to create a large object graph for every test.
- Mutating objects created by `setUpTestData` and leaking in-memory state to later tests.

## Verification

Before finishing a refactor:

- The old behavior remains covered at the right level.
- Database-using and non-database tests are split where useful.
- Repeated setup moved to `setUpTestData` or factories only where it reduces cost.
- Relevant tests pass individually and as part of their module/class.
