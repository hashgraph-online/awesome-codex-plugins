---
name: falsegreen-skill
description: Analyze test files for false-positive smells, meaning tests that pass even when the code breaks. Use when the user asks to review tests for false positives, weak assertions, mock misuse, test smells, or asks whether a test can actually fail. Covers Python (pytest, unittest), TypeScript, JavaScript (Jest, Vitest, Mocha), and Robot Framework.
---

# falsegreen-skill: false-positive test detection

This skill is a thin entry point. Default path: judge from this file. It carries
the protocol summary, the structural code index, the S-series table, and the
look-alike exemptions, which covers a Mode A review of a TypeScript, JavaScript,
or Robot Framework test end to end.

Open a plugin-root file only where this file sends you:

- `../../reference.md` - the full definition or worked example of one specific
  code, after the index below has named it. Read the passage, not the section.
- `../../SKILL.md` - the long-form J1-J6 wording, the Python structural catalog,
  Mode B (authoring), or Mode C (AI-fix). At ~36 KiB on a ~32 KiB host this
  replaces the rest of your context, so it is a decision, not a warm-up read.

Do not open either before reading this file through.

**Mandatory for every language, Python included: load the semantic catalog.** The
S-series (S1-S18, S21) is language-agnostic and lives in `reference.md` under
`## Patterns only the semantic pass can catch (AI-only)`, above the per-language
sections. The root `SKILL.md` names only S3 and S17, so a run that loads a
language section alone never sees the rest. The complete table is in this file
under "Semantic cases", with the look-alike exemptions right after it. Use both:
the S-series without its exemptions produces false positives, which this skill
treats as worse than a miss. `../../reference.md` has the same codes as prose with
examples if a finding needs the long form.

**Mandatory for any non-Python file (JavaScript, TypeScript, Robot Framework,
Gherkin, Tavern): work the structural code index below before you judge.** It
names every code all three scanners emit, so it is what stops a non-Python review
under-detecting. The root `SKILL.md` tables are complete only for Python; for every
other language they are a summary.

Reach for the matching `reference.md` section only when the index has named a
candidate and you need its full definition, and then read that passage, not the
section. On a ~32 KiB host a whole section does not fit beside this file: the TS/JS
section alone is ~19 KiB.

This file is the floor: the structural code index names every code all three
scanners emit, the semantic table carries a row per S-code, and the exemptions
follow it. `../../reference.md` is ~92 KiB, so an eager full read overruns the
budget and truncates mid-file without warning, which is why the order above is
index first and passage second. `../../fragments/precision-rules.md` carries the
precision rules if the host resolves plugin-root paths.

## Structural code index (all three scanners)

Generated from `schema/code-catalog.json` and `schema/scanner-codes.json`, so it
cannot drift. Scanner column: `py` falsegreen, `js` falsegreen-js, `rf`
falsegreen-robot. Severity `-` means no fixed severity. Diagnostic codes
(D-series, M2) are opt-in: apply them only when asked.

One limit worth knowing before you match on a row. A code shared across languages
carries one title here, and for the C-series that title is the Python form. C31 is
the clearest case: the row reads "capsys.readouterr() result discarded", and the
Robot form of the same id is any captured keyword value that is never asserted on.
C3, C9, C23 and C44 reuse ids the same way. Read a shared row as the concept, not
as the syntax to grep for, and pull the language-specific prose when the row is
close but the syntax does not match.

<!-- fg:structural-codes-all:start -->
| Code | Scanner | Severity | What to look for |
|---|---|---|---|
| C1 | py | LOW | Assertion inside conditional or loop that may never run |
| C2 | py/js/rf | HIGH | Test body contains no assertion at all |
| C2b | py/js/rf | LOW | Test calls production code but verifies nothing |
| C2c | py | LOW | Empty `self.subTest(...)` block |
| C3 | py/rf | HIGH | Assert inside try whose except swallows the error |
| C4 | py | HIGH | Test function not collected by pytest |
| C4b | py | LOW | Test class has `__init__` (pytest won't collect it) |
| C5 | py/js/rf | HIGH | Always-true assertion |
| C6 | py/js/rf | LOW | Weak assertion: only checks that something came back |
| C6b | py | LOW | Assertion on positional mock argument via computed index |
| C6c | py | LOW | Mock `call_count` truthiness as the oracle |
| C7 | py/js/rf | HIGH | Self-comparison: both sides are identical |
| C8 | py/js | LOW | Float exact equality |
| C8b | py/js | LOW | Approximate equality with no explicit tolerance |
| C9 | py/js/rf | LOW | pytest.raises too broad |
| C9b | rf | - | RequestsLibrary `expected_status=any` |
| C11a | py/js/rf | LOW | Self-confirming literal: test assigns then asserts the same value |
| C13 | py | HIGH | Mock assertion misspelled or not called |
| C13b | py | LOW | patch() without autospec |
| C14 | py | LOW | Golden file generated from the actual output |
| C16 | py/js/rf | LOW | Result depends on uncontrolled time, randomness, or sleep |
| C17 | py | HIGH | pytest.skip() inside broad except |
| C18 | py/js | LOW | String/repr comparison |
| C19 | py | LOW | pytest.raises wraps more than one call |
| C20 | py/js/rf | HIGH | Assertion after unconditional return/raise/fail |
| C21 | py/js/rf | LOW | Every assertion is inside a conditional; none runs unconditionally |
| C22 | py | OFF | Async test never awaits the unit under test |
| C23 | py/js/rf | LOW | Hard-coded absolute or home-relative file path |
| C24 | py | LOW | Module-level mutable state mutated by test |
| C25 | py | LOW | xfail without strict=True |
| C27 | py | HIGH | try/except/pass around SUT call with no assertion |
| C28 | py | LOW | pytest.raises binding variable never read |
| C29 | py | LOW | os.environ modified directly in test |
| C30 | py | LOW | HTTP mock not activated |
| C31 | py/rf | LOW | capsys.readouterr() result discarded |
| C32 | py/rf | LOW | @pytest.mark.skip without reason |
| C33 | py | LOW | ML metric computed but not asserted |
| C34 | py | LOW | Suboptimal assertion form |
| C35 | py | LOW | Retry/flaky decorator |
| C36 | py | LOW | pytest.fail() without reason |
| C37 | py/js/rf | LOW | Duplicate parametrize case |
| C38 | py | HIGH | Two tests share a name |
| C39 | py | HIGH | Returns a comparison instead of asserting |
| C41 | py | LOW | Assertion on a None-returning mutator |
| C42 | py | HIGH | Assertion on a generator/lambda |
| C43 | py | LOW | Mid-test skip |
| C44 | py/js/rf | HIGH | Numeric tautology |
| C45 | py | HIGH | Empty parametrize |
| C48 | py/js | LOW | Dark patch: flips a test-mode flag then asserts |
| C49 | py | LOW | `pytest.warns`/`assertWarns` wraps more than one call |
| C50 | py | LOW | Captured log never asserted |
| C51 | py | HIGH | Empty-bodied `pytest.raises`/`warns` context |
| C52 | py | LOW | Membership self-confirmation |
| C55 | py | LOW | Assertion compares two mock-rooted values |
| C56 | py | LOW | Sync assert of a never-awaited coroutine |
| C57 | py | LOW | Assertion against an unconfigured Mock attribute |
| C59 | py | HIGH | Bare comparison written as a statement |
| CC | py/js/rf | LOW | Commented-out assert |
| D1 | py/js | LOW | Assertion Roulette: multiple asserts, none with a message |
| D2 | rf | - | Control flow at test level |
| D3 | py/js | LOW | Duplicate Assert: same assertion appears twice |
| D4 | py/js | LOW | Unnamed parametrize cases |
| D5 | py | LOW | Excessive inline setup |
| D6 | py/js | LOW | Debug print in test |
| D7 | js | LOW | Anonymous test: empty or missing description |
| D8 | js | LOW | Magic number in an assertion |
| JS1 | js | HIGH | focused test (`it.only`/`fit`) skips the rest of the suite |
| JS2 | js | HIGH | `expect(x)` with no matcher |
| JS3 | js | LOW | snapshot is the only assertion |
| JS4 | js | LOW | skipped test (`it.skip`/`xit`/`it.todo`) |
| JS5 | js | LOW | async query/event not awaited (`findBy*`/`waitFor`/user-event) |
| JS6 | js | HIGH | empty `describe`/`suite` |
| JS7 | js | LOW | assertion in a non-awaited `setTimeout`/`then` callback |
| JS8 | js | LOW | mocks the unit under test and asserts it directly |
| JS9 | js | HIGH | assertion in a dead literal branch (`if(false)`) |
| JS11 | js | LOW | `try/catch` swallows the assertion |
| JS13 | js | LOW | `queryBy*`/`queryAllBy*` query (returns null when absent) as a loose statement, never asserted - `getBy*`/`getAllBy*`/`findBy*`/`findAllBy*` throw on absence and ARE the assertion |
| JS15 | js | LOW | comparison wrapped in a boolean (`expect(a===b).toBe(true)`) |
| JS17 | js | LOW | commented-out test block (`// it(...)`) |
| JS18 | js | LOW | `done` callback instead of async/await |
| JS21 | js | HIGH | matcher referenced but never called (`expect(x).toBe` with no `()`) |
| JS22 | js | HIGH | empty `it.each`/`test.each` table |
| JS23 | js | HIGH | `expect.assertions(N)` with fewer unconditional reachable `expect()` calls than `N` |
| JS24 | js | LOW | Cypress `cy.get/find/contains` query statement with no `.should`/`.and`/`.then` assertion |
| JS25 | js | HIGH | the only assertion sits inside an array-iterator callback (`forEach`/`map`/`filter`/`some`/`every`/`flatMap`) - runs zero times on an empty collection |
| JS26 | js | LOW | fake timers installed but never advanced (`runAllTimers`/`advanceTimersByTime`/`tick`) - the scheduled callback never fires, so the assertion reads un-mutated state |
| JS27 | js | LOW | `toHaveBeenCalled*` is the sole oracle on a locally-created double - verifies wiring, not behaviour |
| JS29 | js | LOW | `expect(...).resolves`/`.rejects` chain is a bare statement, not awaited or returned - the test finishes green before the matcher settles |
| JS30 | js | HIGH | literal-vs-literal assertion (`expect(2).toBe(3)`, chai `expect(x).to.equal(y)`) - both operands are fixed at parse time |
| JS31 | js | LOW | `try/catch` swallows a possible throw with no assertion on the exception - a unit that stops throwing still passes green |
| M2 | py/js/rf | LOW | Long test method |
| PL1 | py | - | Asserts stripped at runtime |
| PL2 | py | - | Warnings not promoted |
| PL7 | py/js | - | No coverage gate |
| PL8 | py/js | - | Run stops early |
| PL9 | rf | - | Skip-on-failure run option |
| PL10 | js | - | passWithNoTests |
| R1 | rf | - | Forced green |
| R2 | rf | - | Hollow verifier keyword |
| R3 | rf | - | Test Cases in a .resource |
| R4 | rf | - | No Operation only |
| R5 | rf | - | Empty [Template] |
| R6 | rf | - | Should Be True on a string literal |
| R7 | rf | - | Hollow [Template] keyword |
| R8 | rf | - | Verification only in Setup |
| R8b | rf | - | Verification only in Teardown |
<!-- fg:structural-codes-all:end -->

## Semantic cases

Every AI-only S-code, plus the five numbered semantic cases. Complete: this is
what Step 4 screens against.

<!-- fg:semantic-cases-compact:start -->
| Case | Judgment | Severity | Name | Rule |
|---|---|---|---|---|
| 10 | J3 | HIGH | Mocks the unit under test | Patches/mocks the function being tested, then asserts on the mock's return value |
| 11 | J2/J3 | HIGH | Asserts the value fed to the mock | Stubs dependency to return X, then asserts result == X with no real logic in between |
| 12 | J2 | HIGH | Re-implements the production formula | Expected value computed with the same formula as the SUT; both sides agree on the same wrong answer |
| 15 | J6 | HIGH | Passes only if another test ran first | Reads shared mutable state written by a sibling test; fails when run alone |
| 18 | J2 | HIGH | Expected value contradicts what the code should do | Asserts a value the independent oracle says is wrong; requires cited oracle before reporting |
| S1 | J4 | - | Intent mismatch | The name or docstring claims to verify X, the assertion checks Y or a trivial property (`test_applies_discount` that only asserts the call did not raise) |
| S2 | J4 | - | Irrelevant oracle | The assertion checks a property unrelated to the behavior under test: a test of the computed total that only asserts the response is not null |
| S3 | J2 | - | Plausible-but-wrong expected value | The expected constant looks reasonable but contradicts the spec (off-by-one, wrong rounding, wrong sign); derive the correct value from the spec and compare |
| S4 | J4 | - | Oracle cannot distinguish correct from a likely bug | The assertion passes for the right output and for a plausible wrong one: `len(result) == 3` when the suspected bug also yields three items |
| S5 | J3 | - | Tests the framework, not the code | The assertion exercises a language or library guarantee (a dict stores a key, the ORM returns what was just saved) instead of the code under test |
| S6 | J4 | - | Happy-path only against a stated contract | The spec or docstring promises error handling or boundaries, the test covers only the nominal path |
| S7 | J2 | - | Expected lifted from the output | The expected value was copied from a run of the current code (a pasted dict, a captured response), so the test can only confirm the code matches itself |
| S8 | J3 | - | Mock return reaches the assertion through an indirection | The stub's value flows through one or two trivial steps to the assertion, so the test still echoes the stub instead of verifying real behavior |
| S9 | J2 | - | Self-fulfilling arrangement | The test arranges the exact state it then asserts, with no transformation by the unit under test |
| S10 | J4 | - | Asserts the log, not the effect | The only check is that a message was logged, not the state change the message describes |
| S11 | J4 | - | Negative-only assertion on a security filter | A sanitizer, redactor, or auth test asserts only that the bad thing is absent (`"password" not in response`); it passes when the output is empty or dropped, so require a paired positive assertion |
| S12 | J3 | - | Patches core logic instead of an external edge | The test patches a private method or a direct collaborator on the class under test, so the assertion reads the stub, not the unit's own logic; patching a genuine external edge is legitimate |
| S13 | J6 | - | Passes only via shared state a sibling set up | The test relies on module-global, fixture, or hoisted state that another test or an import mutates, so it passes only in a given execution order |
| S14 | J2 | - | Recorded model output as the oracle | Asserts `==` against a snapshotted LLM/model result; green means the model still emits what it once emitted, not that the output is correct |
| S15 | J6 | LOW | Hand-rolled retry/poll loop masking flakiness | Wraps action+assertion in a retry/poll and passes if any attempt succeeds; only the swallow-and-pass form (a retry that re-raises on exhaustion is a sanctioned settle, not S15) |
| S16 | J4 | LOW | Call-verification as the sole oracle | The only check is that a collaborator was called (`assert_called_once`/`toHaveBeenCalled`), with no assertion on the unit's own return value or state |
| S17 | J4 | HIGH | Exception-path oracle blindness | `pytest.raises(Exception)`/`expect(fn).toThrow()` with no type or message on a documented error contract; goes green when the exception came from arrange (typo, missing import, None-deref) and the SUT never reached its raise |
| S18 | J3 | LOW | Contract-impossible stub value | A legitimate edge stub is configured to return a value the real collaborator can never emit (negative price, schema-violating row, `None` where non-null is guaranteed); the SUT handles an unreachable branch while the real defect goes untouched |
| S21 | J2 | LOW | Self-judging LLM/agent assertion | The oracle is a live model call (`judge_llm(...) == "yes"`, embedding-similarity against a model-generated reference, agent grading its own transcript); circular, passes whenever the judge is wrong in the same direction as the SUT |
<!-- fg:semantic-cases-compact:end -->

### Look-alike exemptions for the semantic codes

Check these before reporting any S-code. They override the table above: a pattern
listed here is correct code.

<!-- fg:semantic-exemptions:start -->
Look-alikes - do NOT flag: a deliberately narrow unit test whose scope the spec confirms
(S6 needs a stated broader contract); a constant that the spec genuinely endorses (not S3);
a sanitizer test that already pairs the negative check with a positive one (not S11); a test
of a filter whose contract is to drop the input entirely - a blocklist sanitizer, a
guard that returns empty on a forbidden value, a redactor that suppresses the whole field -
where empty output is the correct behavior, so the negative-only assertion legitimately
passes and a positive "content survived" assertion would contradict the design (not S11); a
mock on a genuine external edge - DB, network, clock (not S12); a `jest.spyOn(instance, 'methodA')` / `vi.spyOn` that stubs a DIFFERENT method than the one under test, to isolate an orchestrator from a sibling sub-unit (the assertion is on the composed result, not the stub) - S12 fires only when the patched symbol is a method of the SUT instance itself or the assertion echoes the stub value (not S12); a constructor-injected or module-level collaborator mock - repository, db, auth, or HTTP client (a clean case-10 external edge, not S12); a stub-config call made on the very library under test - `mockingoose`, `tinyspy`, `jsdom-testing-mocks` - where the mocking library IS the SUT, so the stub setup is production code (not S5/S8/C11a); a test whose shared state is
reset by an autouse/`beforeEach` teardown (not S13); a structural or contract assertion on a
model output - valid JSON, required keys present, a cited source id matches, a refusal on a
banned prompt, a deterministic post-processing step - or a mocked/stubbed model whose return is
fixture data (not S14); a sanctioned async-settling wait - Robot `Wait Until Keyword Succeeds`,
Testing Library `waitFor`/`findBy*`, Playwright/Cypress auto-wait, `await expect(...).toPass()` -
that polls a real settle condition and still fails hard on timeout (not S15); a call-only
assertion where the interaction IS the contract - a fire-and-forget event, an audit-log or
telemetry write, a queue publish - or a `toHaveBeenCalledWith`/`assert_called_once_with` that
pins the specific arguments, or any call-verification paired with an assertion on the SUT's return value or state - S16 requires the call-verification to be the SOLE oracle (not S16); a `pytest.raises(SpecificError, match=...)` bound to the SUT line (not S17); a stub fed a value the collaborator's contract can actually return (not S18); a test under `*.problem.*` / `*.solution.*` / `exercises/` / `katas/` / `playground/` - a teaching or TDD-spec fixture whose expected value is intentional (the exercise IS the spec), not a frozen bug (not case 18, not S3); a deterministic rubric, structural validator, or frozen human-labeled judge set rather than a live model verdict (not S21).
<!-- fg:semantic-exemptions:end -->

## Structural code index (TS/JS, Robot, project layer)

Generated from `schema/code-catalog.json`, so it cannot drift from
`reference.md`. Severity `-` means the code carries no fixed severity.

<!-- fg:structural-codes-compact:start -->
| Code | Severity | What to look for |
|---|---|---|
| **TypeScript / JavaScript** | | 24 codes |
| JS1 | HIGH | focused test (`it.only`/`fit`) skips the rest of the suite |
| JS2 | HIGH | `expect(x)` with no matcher |
| JS3 | LOW | snapshot is the only assertion |
| JS4 | LOW | skipped test (`it.skip`/`xit`/`it.todo`) |
| JS5 | LOW | async query/event not awaited (`findBy*`/`waitFor`/user-event) |
| JS6 | HIGH | empty `describe`/`suite` |
| JS7 | LOW | assertion in a non-awaited `setTimeout`/`then` callback |
| JS8 | LOW | mocks the unit under test and asserts it directly |
| JS9 | HIGH | assertion in a dead literal branch (`if(false)`) |
| JS11 | LOW | `try/catch` swallows the assertion |
| JS13 | LOW | `queryBy*`/`queryAllBy*` query (returns null when absent) as a loose statement, never asserted - `getBy*`/`getAllBy*`/`findBy*`/`findAllBy*` throw on absence and ARE the assertion |
| JS15 | LOW | comparison wrapped in a boolean (`expect(a===b).toBe(true)`) |
| JS17 | LOW | commented-out test block (`// it(...)`) |
| JS18 | LOW | `done` callback instead of async/await |
| JS21 | HIGH | matcher referenced but never called (`expect(x).toBe` with no `()`) |
| JS22 | HIGH | empty `it.each`/`test.each` table |
| JS23 | HIGH | `expect.assertions(N)` with fewer unconditional reachable `expect()` calls than `N` |
| JS24 | LOW | Cypress `cy.get/find/contains` query statement with no `.should`/`.and`/`.then` assertion |
| JS25 | HIGH | the only assertion sits inside an array-iterator callback (`forEach`/`map`/`filter`/`some`/`every`/`flatMap`) - runs zero times on an empty collection |
| JS26 | LOW | fake timers installed but never advanced (`runAllTimers`/`advanceTimersByTime`/`tick`) - the scheduled callback never fires, so the assertion reads un-mutated state |
| JS27 | LOW | `toHaveBeenCalled*` is the sole oracle on a locally-created double - verifies wiring, not behaviour |
| JS29 | LOW | `expect(...).resolves`/`.rejects` chain is a bare statement, not awaited or returned - the test finishes green before the matcher settles |
| JS30 | HIGH | literal-vs-literal assertion (`expect(2).toBe(3)`, chai `expect(x).to.equal(y)`) - both operands are fixed at parse time |
| JS31 | LOW | `try/catch` swallows a possible throw with no assertion on the exception - a unit that stops throwing still passes green |
| **Robot Framework** | | 9 codes |
| R1 | - | Forced green |
| R2 | - | Hollow verifier keyword |
| R3 | - | Test Cases in a .resource |
| R4 | - | No Operation only |
| R5 | - | Empty [Template] |
| R6 | - | Should Be True on a string literal |
| R7 | - | Hollow [Template] keyword |
| R8 | - | Verification only in Setup |
| R8b | - | Verification only in Teardown |
| **Project layer** | | 6 codes |
| PL1 | - | Asserts stripped at runtime |
| PL2 | - | Warnings not promoted |
| PL7 | - | No coverage gate |
| PL8 | - | Run stops early |
| PL9 | - | Skip-on-failure run option |
| PL10 | - | passWithNoTests |
<!-- fg:structural-codes-compact:end -->

## Protocol in one paragraph

A test is useful only if it fails when the code breaks. Detect the language and
framework, classify the test intent (spec, characterization, regression,
behavior), then apply the six judgments: J1 does the assertion run, J2 is the
expected value from an independent oracle, J3 is the real unit under test, J4
does the assertion verify enough, J5 is the test coupled to implementation
internals, J6 does the test pass in isolation. For Python, also run the full
structural catalog (families A-E, the 56 emitted C-codes). Flag only the first failing
judgment per test.

## Non-negotiable rules

- Never report case 18 (expected value contradicts the spec) without citing an
  independent oracle, and always run the adversarial verify pass first.
- Precision over recall: a wrong HIGH finding is worse than a missed LOW one.
- Check the look-alike exemptions in `reference.md` before flagging.

## Output

Use the CASE / SUMMARY format defined in the root `SKILL.md` Step 6:

```
CASE {number} ({J-code}) - {HIGH|LOW} - {language} - {intent}
Test / Finding / Evidence / Oracle (case 18 only) / Fix hint
```
