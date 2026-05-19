---
name: tdd
description: Use when implementing or fixing production code with tests.
---
# TDD

**No production code without a failing test first.** Wrote code before the test? Delete it. Rewrite from the test.

RED (fail for the *right reason*) -> GREEN (minimum to pass) -> refactor -> **sync docs** -> commit -> **edit `docs/staging/plans/YYYY-MM-DD-<topic>.md` and change this task's `- [ ]` to `- [x]`. Do not start the next task without this edit.**

**Sync docs** means:
- If staging spec exists (`docs/staging/specs/*.md`): update it to match code reality.
- If no staging spec (small task): update living docs (README, tech-spec, comments) directly.

All tasks `- [x]` and green -> `ship`.

## Don't
- Test passes without the impl (tests nothing).
- Mock the unit under test (tests the mock).
- Assert many behaviors in one test (split).
- Skip "watch it fail" (you don't know what it tests).
- Edit the test to match buggy code (tests the bug).
- Add abstractions not required by the current test.
- Edit files outside the failing test's scope.

Exception - ask user: prototypes, generated code, throwaway scripts.