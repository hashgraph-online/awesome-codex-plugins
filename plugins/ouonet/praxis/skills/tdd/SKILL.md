---
name: tdd
description: Use when implementing or fixing production code with tests.
---
# TDD

If `topology=multi-module` (triage announcement or coordinator spec/plan declaration), read `../references/multi-module.md`. Run implementation and local acceptance inside the task's registered repository/module. Update that module's spec and plan; update the coordinator only for shared-contract reality or workspace state.

## Acceptance mode

Read the current plan task's `acceptance:` (or equivalent).

**Automated acceptance** (test, command, or script that must fail before the change and pass after):
- **No production code without a failing check first.** Wrote code before the failing check? Delete it. Rewrite from the check.
- RED (fail for the *right reason*) → GREEN (minimum to pass) → refactor → **sync docs** → commit → flip the plan checkbox.

**Manual acceptance** (explicit steps + expected result in the plan — config, docs, infra, prompts, content, or other non-testable deliverables):
- Do **not** invent an automated test solely to satisfy RED-GREEN.
- Perform the manual check; keep the change minimal; run any declared mechanical checks; **sync docs**; commit when appropriate; flip the plan checkbox.

**No acceptance at all** (prototypes, generated code, throwaway scripts only): ask the user before writing production code.

## After green / manual pass

**edit `docs/staging/plans/YYYY-MM-DD-<topic>.md` and change this task's `- [ ]` to `- [x]`. Do not start the next task without this edit.**

**Sync docs** means:
- If staging spec exists (`docs/staging/specs/*.md`): update it to match code reality.
- If no staging spec (small task): update living docs (README, tech-spec, comments) directly.

When local module tasks are complete and green, run the coordinator's cross-module acceptance against the current workspace contents before handing off to `ship`.

For a linked multi-repository change, defer commits until integration passes, then follow the commit protocol in `../references/multi-module.md`. This is the exception to the per-cycle commit order above. If any commit fails, stop at `partial-commit`; never rewrite or discard completed commits automatically.

## Refactor

Passing tests are not a quality bar.

`<gate>` Before committing: (1) run lint/format/typecheck — green if declared; (2) evaluate against `convention`; (3) assess design — coupling, cohesion, abstraction, idiomatic for the stack. State what you ran, assessed, and changed — or why not. See `../references/quality.md`. `</gate>`

## Don't
- Test passes without the impl (tests nothing).
- Mock the unit under test (tests the mock).
- Assert many behaviors in one test (split).
- Skip "watch it fail" when acceptance is automated (you don't know what it tests).
- Edit the test to match buggy code (tests the bug).
- Add abstractions not required by the current acceptance (GREEN phase — not refactor).
- Edit files outside the failing check's scope.
- Create ad-hoc summary, notes, or analysis files not defined in the plan or required by a loaded skill.
