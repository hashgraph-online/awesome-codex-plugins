---
name: test-driven-development
description: "Use when implementing a feature, fixing a bug, or changing behavior — write a failing test first, watch it fail, write minimal code to pass, then refactor. Adds Kent Beck's Tidy First (separate structural vs behavioral changes) and a Canon test list. Language-agnostic core; per-language notes under references/languages/. Not for throwaway prototypes, generated code, or pure config changes (ask first)."
---

# Test-Driven Development (TDD)

## Overview

Write the test first. Watch it fail. Write minimal code to pass. Then tidy.

**Core principle:** If you didn't watch the test fail, you don't know if it tests the right thing.

**Announce at start:** "I'm using the test-driven-development skill to drive this change test-first."

This skill is **language-agnostic**. The discipline below holds in every language; concrete framework, runner, and idiom examples live in [references/languages/](references/languages/) — load the one matching your project.

## Prerequisites

- A working test runner for your stack (see the matching `references/languages/<lang>.md`)
- Ability to run a single test and watch its output
- For mocks/test doubles, read [references/testing-anti-patterns.md](references/testing-anti-patterns.md) first

## When to Use

**Always:**
- New features
- Bug fixes
- Refactoring
- Behavior changes

**Exceptions (ask your human partner first):**
- Throwaway prototypes (then throw them away and restart with TDD)
- Generated code
- Pure configuration changes

Thinking "skip TDD just this once"? Stop. That's rationalization.

## The Iron Law

```
NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
```

Wrote code before the test? Delete it. Start over.

**No exceptions:** don't keep it as "reference", don't "adapt" it while writing the test, don't even look at it. Delete means delete. Implement fresh from the test.

## Workflow

### Phase 1: Build a Test List (Canon TDD)

Before writing any test, list the behaviors you need to cover — the basic case plus every variant you can think of ("what if the input is empty? what if the service times out? what if the key is missing?").

- This is **behavioral analysis**, not implementation design.
- Keep the list visible. Add to it whenever you discover a new case mid-cycle.
- Turn **exactly one** item into a concrete test at a time — never convert the whole list up front (reworking speculative tests when an early decision changes is wasted effort).

### Phase 2: Red-Green-Refactor — one list item at a time

```
pick one item  →  RED  →  verify red  →  GREEN  →  verify green  →  REFACTOR  →  back to the list
```

> **Run tests in the quietest mode that still surfaces failures.** Verbose pass logs burn context you don't need — quiet runners stay silent on green and print full detail on red, so you keep the failures without the noise. Switch to verbose (`-v` / `-s` / `--nocapture`) only when isolating one test's output. Per-language quiet flags are in each [`references/languages/<lang>.md`](references/languages/).

#### RED — write one failing test

One behavior, a name that describes that behavior (e.g. `shouldRetryThreeTimesThenSucceed`, not `test1`), real code over mocks. Work backwards from the assertion. See your language file for concrete framework syntax.

#### Verify RED — watch it fail (MANDATORY, never skip)

Run the single test. Confirm:
- It **fails**, not errors (no typos/missing imports)
- It fails for the **expected reason** — the behavior is missing, not the setup is broken

**Test passes already?** You're testing existing behavior. Fix the test.

#### GREEN — minimal code to pass

Write the simplest code that makes this test (and all previous tests) pass. No speculative APIs, no extra options, no "while I'm here" cleanup. YAGNI.

#### Verify GREEN — watch it pass (MANDATORY)

Run the test. Confirm it passes, all previous tests still pass, and output is pristine (no warnings/errors). **Test fails? Fix the code, not the test.**

#### REFACTOR — only on green

Remove duplication, improve names, extract helpers. Keep every test green. Don't add behavior here — that's the next RED.

Then mark the item done and return to the list. Repeat until the list is empty.

### Phase 3: Tidy First — separate structural from behavioral changes

Kent Beck's distinction. Every change is one of two kinds — **never mix them in one commit:**

| Kind | What it is | Reversible? |
|---|---|---|
| **Structural** | Rearranging without changing behavior: rename, extract method, move code, organize imports | Usually yes |
| **Behavioral** | Adding or changing what the system actually does | No |

- When you need both, make the **structural change first**, on green.
- Validate a structural change didn't alter behavior by running the tests **before and after** — they stay green throughout.
- If a change is a tangle of both, untangle it (or redo it) into a structural step then a behavioral step.

### Phase 4: Commit Discipline

Commit only when:
- **All** tests pass and **all** compiler/linter warnings are resolved
- The change is a single logical unit
- The commit message states whether it is **structural** or **behavioral**

Prefer small, frequent commits over large, infrequent ones. (For this repo's commit format, the `git-commit` skill applies — structural vs behavioral maps cleanly onto its `refactor:` vs `feat:`/`fix:` types.)

## Why Test-First (Not Test-After)

Tests written after code pass immediately — and passing immediately proves nothing: they may test the wrong thing, test the implementation instead of behavior, or miss the edge case you forgot. You never saw them catch anything.

Test-after answers "what does this do?" Test-first answers "what *should* this do?" — and forces edge-case discovery *before* you implement. 30 minutes of tests-after gives you coverage but loses the proof the test works.

## Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "Too simple to test" | Simple code breaks. The test takes 30 seconds. |
| "I'll test after" | Tests passing immediately prove nothing. |
| "Tests after achieve the same goals" | Tests-after = "what does this do?" Tests-first = "what should this do?" |
| "Already manually tested" | Ad-hoc ≠ systematic. No record, can't re-run. |
| "Deleting X hours is wasteful" | Sunk cost. Keeping unverified code is the real debt. |
| "Keep it as reference, write tests first" | You'll adapt it. That's testing after. Delete means delete. |
| "Need to explore first" | Fine. Throw away the exploration, restart with TDD. |
| "Hard to test = need to push through" | Hard to test = hard to use. Listen to the test; simplify the design. |
| "TDD will slow me down" | TDD is faster than debugging in production. |
| "This case is different because…" | It isn't. Start over with TDD. |

## Anti-Cheating Checks

Test-first only works if you don't game it. These failures are especially tempting for AI agents under pressure — treat each as a STOP:

- **Deleting or weakening an assertion** to make a test "pass" — make it pass *for real*.
- **Pasting the computed actual value** into the expected slot — that defeats the double-check that gives TDD its value. Derive the expected value independently.
- **Writing a test with no assertion** just for coverage.
- **Mixing refactoring into the green step** — two hats: make it run, *then* make it right.
- **Branching production code on test-only artifacts** (env flags, test IDs) to fake green.

For bug fixes, add at least one test that **reproduces the bug and fails first** — never fix a bug without a failing test that proves the fix.

## Red Flags — STOP and start over

- Code written before the test
- Test passes on the very first run
- Can't explain why the test failed
- "I already manually tested it"
- "It's about the spirit, not the ritual"
- "Keep as reference" / "adapt the existing code"
- Tidied and changed behavior in the same commit
- Edited the test to match the code instead of the code to match the test

## Language-Specific Guidance

The discipline above is the same everywhere. For framework choice, runner commands, idioms, and language-specific anti-patterns, load **only** the file matching your project — and only when you actually need that detail:

| Project language | Read |
|---|---|
| Java | [references/languages/java.md](references/languages/java.md) |
| TypeScript / JavaScript | [references/languages/typescript.md](references/languages/typescript.md) |
| Python | [references/languages/python.md](references/languages/python.md) |
| Go | [references/languages/go.md](references/languages/go.md) |
| Rust | [references/languages/rust.md](references/languages/rust.md) |

No file for your language? The core skill is sufficient — apply the same red-green-refactor and Tidy First discipline with your stack's idiomatic runner.

## Testing Anti-Patterns

When adding mocks or test utilities, read [references/testing-anti-patterns.md](references/testing-anti-patterns.md) — cross-language pitfalls like testing mock behavior instead of real behavior, test-only methods on production classes, and incomplete mocks.

## When Stuck

| Problem | Solution |
|---|---|
| Don't know how to test it | Write the wished-for API in the test first. Ask your human partner. |
| Test is too complicated | The design is too complicated. Simplify the interface. |
| Must mock everything | Code is too coupled. Use dependency injection. |
| Test setup is huge | Extract helpers; if still complex, the design needs simplifying. |

## Verification Checklist

Before marking work complete:

- [ ] Every new behavior has a test
- [ ] Watched each test fail first, for the expected reason
- [ ] Wrote minimal code to pass each test
- [ ] All tests pass; output is pristine (no warnings/errors)
- [ ] Tests use real code (mocks only when unavoidable; see anti-patterns)
- [ ] Edge cases from the test list are covered
- [ ] Structural and behavioral changes are in separate commits

Can't check every box? You skipped TDD. Start over.

## Attribution

- Red-green-refactor discipline, the Iron Law, rationalization/anti-pattern tables, and `testing-anti-patterns.md` are adapted from [superpowers](https://github.com/obra/superpowers) (MIT).
- The Canon test list, Tidy First (structural vs behavioral separation), and commit discipline are from Kent Beck — *Canon TDD* and *Augmented Coding: Beyond the Vibes* (tidyfirst.substack.com).
