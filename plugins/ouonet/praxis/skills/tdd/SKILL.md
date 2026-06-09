---
name: tdd
description: Use when implementing or fixing production code with tests.
---
# TDD

**No production code without a failing test first.** Wrote code before the test? Delete it. Rewrite from the test. Exception — ask user first: prototypes, generated code, throwaway scripts.

RED (fail for the *right reason*) -> GREEN (minimum to pass) -> refactor -> **sync docs** -> commit -> **edit `docs/staging/plans/YYYY-MM-DD-<topic>.md` and change this task's `- [ ]` to `- [x]`. Do not start the next task without this edit.**

**Sync docs** means:
- If staging spec exists (`docs/staging/specs/*.md`): update it to match code reality.
- If no staging spec (small task): update living docs (README, tech-spec, comments) directly.

All tasks `- [x]` and green -> `ship`.

## Refactor

Passing tests are not a quality bar.

`<gate>` Before committing: evaluate the implementation against SOLID principles, design patterns, and clean code. State what you assessed and what (if anything) you improved — or why no changes were needed. `</gate>`

## Don't
- Test passes without the impl (tests nothing).
- Mock the unit under test (tests the mock).
- Assert many behaviors in one test (split).
- Skip "watch it fail" (you don't know what it tests).
- Edit the test to match buggy code (tests the bug).
- Add abstractions not required by the current test (GREEN phase — not refactor).
- Edit files outside the failing test's scope.
- Create ad-hoc summary, notes, or analysis files not defined in the plan or required by a loaded skill.
