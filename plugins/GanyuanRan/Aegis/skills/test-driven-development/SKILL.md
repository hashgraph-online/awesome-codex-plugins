---
name: test-driven-development
description: Use when strict TDD is explicitly requested, or when an approved atomic implementation task has already chosen TDD Route strict.
---

# Execute

→ Implementing a feature or bugfix under TDD Route `strict`? → **No production code without a failing test first.**
  Gate: medium/high complexity? → route to brainstorming or writing-plans first.
  Mode: `auto` chooses strict/light/skipped by risk; `off` disables automatic TDD, not completion verification.
  Cycle: RED (write test → watch it fail) → GREEN (minimal code → watch it pass) → REFACTOR (clean up → keep green)
  Regression: shared module → related tests. contract change → producer + consumer. core logic → old + new tests.
  Ripple signal hit → cover producer+consumer or real user path before claiming green.
  GREEN proves the currently expressed behavior slice only.
  GREEN does not by itself prove parent-task acceptance, business-value completion, or final completion.
→ Done when: chosen TDD Route is recorded, strict-route tests pass, TDD preflight gate passed when applicable, pre-edit complexity risk was checked for non-trivial source edits, and `verification-before-completion` has fresh evidence.

# Test-Driven Development (TDD)

## Overview

Write the test first. Watch it fail. Write minimal code to pass.

If you didn't watch the test fail, you don't know if it tests the right thing.

TDD Mode has two values: `auto` and `off`. `auto` lets Aegis choose a
`TDD Route`; `off` disables automatic TDD routing but never disables
`verification-before-completion`.

## When to Use

New features, bug fixes, refactoring, behavior/logic changes, interface/data contract changes, cross-module or shared module changes, core logic refactors.

Exceptions (ask your human partner): throwaway prototypes, generated code, config files, pure docs cleanup, read-only diagnosis, comment-only changes.

## TDD Mode and Route

Before source edits, decide:

```text
TDD Route:
- Mode: auto | off
- Decision: strict | light | skipped
- Reason:
- Verification:
```

In `auto`, use `strict` for behavior, bugfix, contract, shared/core, producer /
consumer, persistence, permission, migration, or meaningful regression risk.
Use `light` for tiny low-risk edits with an obvious readback or command check.
Use `skipped` for read-only, docs-only, generated, throwaway, comment-only, or
environment-bound work where TDD does not fit.

In `off`, do not automatically require TDD. Explicit user/project TDD requests
still apply, and risky work may still justify recommending strict TDD.
`verification-before-completion` still applies before any completion claim.

## Preflight Gate

TDD is the implementation discipline for an approved behavior or atomic task.
It is not a substitute for task routing, product clarification, or planning.

Before writing tests or production code, stop and route to brainstorming or
writing-plans if the current request has any medium- or high-complexity signal:

- multiple files, modules, pages, screens, services, or owners
- user-visible flows such as navigation, onboarding, checkout, lifecycle, or
  recovery paths
- state transitions, routing rules, API or data contracts, compatibility
  boundaries, migrations, permissions, or persistence
- more than one acceptance path or manual/visual verification requirement
- unclear product behavior, competing constraints, or long-running execution

For these tasks, require a baseline read-set, plan, and atomic tasks before TDD.
High-complexity or ambiguous tasks also need a spec/design review before
planning. Only proceed directly with TDD for low-complexity work whose intent,
owner, compatibility boundary, verification path, and slice goal / success
evidence are already clear.

## Pre-Edit Complexity Check

Before production code edits, check whether the intended source edit would add
logic to an overloaded or wrong owner. Tiny edits can keep this to one line.

```text
Pre-Edit Complexity Check:
- Target edit file:
- Existing pressure signal:
- Owner fit:
- Safer edit boundary:
- Decision: edit-in-place | extract helper | add owner file | split task | pause for plan update
```

Pressure signals: 800+ line file, 80+ line block, deep nesting, mixed reasons
to change, generic owner receiving new responsibility, owner mismatch, or new
fallback/adapter/guard paths. If the decision is `pause for plan update`, stop
TDD and return to `writing-plans` or `brainstorming` with the evidence.

When a medium- or high-complexity task needs project records, use configured Aegis workspace support
lazily. Prefer the installed Aegis workspace helper
(`python <aegis-workspace-helper> init --root <target-project-root>`) when it
is available. If the task needs a process trail under `work/`, prefer
`python <aegis-workspace-helper> new-work --root <target-project-root> ...`
so the intent, checkpoint, drift, and evidence paths are indexed and
structurally checkable:

```text
docs/aegis/
  README.md
  INDEX.md
  BASELINE-GOVERNANCE.md
  adr/
  baseline/
  specs/
  plans/
  work/YYYY-MM-DD-<task-slug>/
    10-intent.md
    20-checkpoint.md
    90-evidence.md
    99-reflection.md
```

Do not promote reusable project facts, decisions, specs, or plans into those
directories unless the workflow needs them and no existing project authority
already owns them.

## Red-Green-Refactor

### RED - Write Failing Test

State: input | output | boundary | acceptance criteria. Check existing test coverage first. Write one minimal test showing what should happen.
A minimal test anchors the next behavior slice; it does not by itself define
whole-task completeness unless the parent acceptance is already fully pinned.

<Good>
```typescript
test('retries failed operations 3 times', async () => {
  let attempts = 0;
  const operation = () => {
    attempts++;
    if (attempts < 3) throw new Error('fail');
    return 'success';
  };

  const result = await retryOperation(operation);

  expect(result).toBe('success');
  expect(attempts).toBe(3);
});
```
Clear name, tests real behavior, one thing
</Good>

<Bad>
```typescript
test('retry works', async () => {
  const mock = jest.fn()
    .mockRejectedValueOnce(new Error())
    .mockRejectedValueOnce(new Error())
    .mockResolvedValueOnce('success');
  await retryOperation(mock);
  expect(mock).toHaveBeenCalledTimes(3);
});
```
Vague name, tests mock not code
</Bad>

**Requirements:**
- One behavior
- Clear name
- Real code (no mocks unless unavoidable)
- If a new feature changes user-observable behavior, prefer one minimal
  end-to-end or integration test for the main path before narrower unit tests
- For user-visible work, cover the main journey and the highest-risk experience
  or operational floor before treating unit tests as sufficient
- Add unit tests for core rules, boundary conditions, and error branches

### Verify RED - Watch It Fail

**MANDATORY. Never skip.**

```bash
npm test path/to/test.test.ts
```

Confirm:
- Test fails (not errors)
- Failure message is expected
- Fails because feature missing (not typos)

**Test passes?** You're testing existing behavior. Fix test.

**Test errors?** Fix error, re-run until it fails correctly.

### GREEN - Minimal Code

Write simplest code to pass the test.

<Good>
```typescript
async function retryOperation<T>(fn: () => Promise<T>): Promise<T> {
  for (let i = 0; i < 3; i++) {
    try {
      return await fn();
    } catch (e) {
      if (i === 2) throw e;
    }
  }
  throw new Error('unreachable');
}
```
Just enough to pass
</Good>

<Bad>
```typescript
async function retryOperation<T>(
  fn: () => Promise<T>,
  options?: {
    maxRetries?: number;
    backoff?: 'linear' | 'exponential';
    onRetry?: (attempt: number) => void;
  }
): Promise<T> {
  // YAGNI
}
```
Over-engineered
</Bad>

Don't add features, refactor other code, or "improve" beyond the test.

Fix the real owner of the behavior. Do not add a new fallback, adapter, or
branch unless the debugging or design workflow identifies why it is necessary
and what old path retires.

### Verify GREEN - Watch It Pass

**MANDATORY.**

```bash
npm test path/to/test.test.ts
```

Confirm:
- Test passes
- Other tests still pass
- Output pristine (no errors, warnings)

**Test fails?** Fix code, not test.

**Other tests fail?** Fix now.

### REFACTOR - Clean Up

After green only:
- Remove duplication
- Improve names
- Extract helpers

Keep tests green. Don't add behavior.

### Repeat

Next failing test for next feature.

## Regression Scope

At minimum, run the target test you just changed or added. Broaden regression
based on impact:

- Shared module change -> related module tests
- Interface or data contract change -> producer and consumer tests
- Cross-module behavior change -> integration or end-to-end path
- Core logic refactor -> old behavior regression tests plus new behavior tests
- Ripple Signal Triage fired -> producer+consumer or real user path that proves
  the downstream effect remains bounded

If the current environment cannot run automated tests, state the blocker and provide reproducible manual verification steps.

## Good Tests

| Quality | Good | Bad |
|---------|------|-----|
| **Minimal** | One thing. "and" in name? Split it. | `test('validates email and domain and whitespace')` |
| **Clear** | Name describes behavior | `test('test1')` |
| **Shows intent** | Demonstrates desired API | Obscures what code should do |

## Red Flags - STOP and Start Over

- Code before test
- Test after implementation
- Test passes immediately
- Can't explain why test failed
- Tests added "later"
- Rationalizing "just this once"
- "I already manually tested it"
- "Tests after achieve the same purpose"
- "It's about spirit not ritual"
- "Keep as reference" or "adapt existing code"
- "Already spent X hours, deleting is wasteful"
- "TDD is dogmatic, I'm being pragmatic"
- "This is different because..."

**All of these mean: Delete code. Start over with TDD.**

## Example: Bug Fix

**Bug:** Empty email accepted

**RED**
```typescript
test('rejects empty email', async () => {
  const result = await submitForm({ email: '' });
  expect(result.error).toBe('Email required');
});
```

**Verify RED**
```bash
$ npm test
FAIL: expected 'Email required', got undefined
```

**GREEN**
```typescript
function submitForm(data: FormData) {
  if (!data.email?.trim()) {
    return { error: 'Email required' };
  }
  // ...
}
```

**Verify GREEN**
```bash
$ npm test
PASS
```

**REFACTOR**
Extract validation for multiple fields if needed.

## Verification Checklist

- [ ] Defined input, output, boundaries, compatibility, acceptance criteria
- [ ] Every new function/method has a test that failed first
- [ ] All tests pass, output pristine
- [ ] Regression: shared/contract/core changes ran related tests
- [ ] Ripple signal hit: downstream or real user path covered
- [ ] If automation blocked → blocker + manual steps documented
- [ ] GREEN treated as local behavior proof only, not final completion
- [ ] If `TaskIntentDraft`, parent plan/spec, or `Slice Card` exists, covered and uncovered scope are explicit before any done claim

Can't check all boxes? Start over.

## Exploration and Emergency Exceptions

Exploratory spikes are allowed only as throwaway learning. When the spike ends,
convert confirmed behavior into tests before formal implementation.

Emergency hotfixes may prioritize the smallest safe repair when delay is more
dangerous than incomplete TDD. Record the reason, keep the change narrow, and
add the missing regression test in the same slice or the next nearest slice.

## When Stuck

Don't know how to test → write wished-for API first. Test too complicated → simplify design. Must mock everything → reduce coupling.

## Debugging Integration

Bug found? Write failing test reproducing it. Follow TDD cycle. Never fix bugs without a test.
