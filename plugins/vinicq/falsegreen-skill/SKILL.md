# falsegreen-skill

**LLM-based semantic analysis for false-positive test detection.** This skill
judges whether a test genuinely verifies correct behavior, across Python,
TypeScript, JavaScript, and Robot Framework - and catches semantic patterns no
static tool can see.

For Python, this skill applies the complete falsegreen catalog directly — all
structural and semantic patterns — without requiring the static scanner to run
first. The companion [falsegreen](https://github.com/vinicq/falsegreen) scanner
is a faster batch alternative for Python; results must be consistent with this
skill. For TypeScript and JavaScript, this skill is the primary detection tool.

Invoke by attaching a test file or pasting a test snippet and asking for
false-positive analysis.

---

## The one rule

A test is useful only if it fails when the code breaks. Every pattern this
skill looks for is a variation on tests that do not fail: tests that pass
while the code is wrong, tests that check the wrong thing, or tests that
borrow correctness from elsewhere.

---

## Three intents, one skill

This is one skill with one source of truth (the J1-J6 judgments and the catalog
in `reference.md`), used in three directions. Pick the intent from what the user asks:

- **Review** an existing test ("analyze / check / is this test real?") -> **Mode A**
  (the Protocol below): detect false-green smells and report them.
- **Create** a test ("write / generate a unit|integration|e2e test for X in
  <language>") -> **Mode B** (Authoring mode, at the end of this file): generate the
  test, then run Mode A on your own output until it is clean.
- **Fix** a finding ("strengthen / repair this false-green test", given a falsegreen
  report) -> **Mode C** (AI-fix mode, after Mode B): propose a strengthened test that
  closes the finding, self-validated with Mode B's machinery, plus the validation
  contract the host runs to confirm it.

Generation does not have its own rules. The test you write must pass the same
J1-J6 it would be judged by, so it is born non-false-green. The developer chooses
the language and the pyramid level; the catalog is the guard either way. The fix
path reuses that same loop: a proposed fix is just an authored test that has to
survive its own review before the host runs the gate.

---

## Protocol

Work through these steps in order. Do not skip steps.

### Step 0 (optional): Load project conventions

If the user supplies a `conventions:` block, incorporate it before applying any judgments.
This block declares project-specific context that affects the look-alike rules.

Example:
```
conventions:
  custom_assertion_helpers:
    - conftest.assert_model_valid()   # wraps assert + validation logic
    - helpers.assert_valid_uuid()
  test_layer_overrides:
    - tests/integration/ is web-layer  # apply C6 HTTP exemption here
  excluded_codes:
    - C8   # project uses Decimal, not float
```

The conventions block does NOT disable severity levels. It only extends the look-alike
exemptions in reference.md. HIGH findings that survive after exemptions are still reported as HIGH.

If no conventions block is provided, proceed directly to Step 1.

### Step 1: Detect language and framework

Identify:
- Language: Python / TypeScript / JavaScript / Robot Framework
- Test framework: pytest / unittest (Python) · Jest / Vitest / Mocha+Chai (TS/JS) ·
  React Testing Library (component render) · Cypress / Playwright (E2E, JS/TS or Python) ·
  Robot Framework (`.robot` / `.resource`, keyword-driven) · Tavern (`*.tavern.yaml`, API) ·
  Gherkin/BDD (`.feature`: Cucumber.js / behave / pytest-bdd)
- Test level — read it from the signals below, do not guess. The level changes what
  counts as a valid oracle.

**How to tell the level.** Read it from the signals; do not guess. Apply this
precedence (strongest signal wins), in order:

1. **A doubled boundary beats an import.** If an interceptor or fake wraps the boundary -
   Python `responses`/`respx`/`requests-mock`/`vcr`/`moto`/`fakeredis`/`mongomock`/`pyfakefs`/
   `unittest.mock`/`monkeypatch`; JS/TS `msw`/`nock`/`fetch-mock`/`axios-mock-adapter`/
   `jest.mock`/`vi.mock`/`aws-sdk-client-mock` - the test is **unit/component** even when a
   real client (`requests`, `axios`, `boto3`, SQLAlchemy) is imported. The mock IS the boundary.
2. **Else a real boundary makes it integration.** A real HTTP client / in-process test client,
   DB driver/ORM, queue, cache, or storage SDK that touches a real (even ephemeral or
   containerized) collaborator.
3. **Else a browser/mobile driver makes it E2E.**
4. **No signal → unit.** Real I/O (disk, clock, network) in a test with no integration signal
   is itself the smell, not the level.

| Signal | Unit (and component) | Integration | E2E |
|---|---|---|---|
| Path / marker | `tests/unit/`, none, co-located `*.test.ts` | `tests/integration/`, `*.int.test.ts`, `@pytest.mark.integration`/`functional`/`db`/`django_db` | `tests/e2e/`, `cypress/e2e/`, `*.e2e-spec.ts`, `*.cy.ts`, `@pytest.mark.e2e`/`acceptance`, `playwright.config` |
| Doubles | mock/patch or intercept the boundary (rule 1) | real client/driver, no double | no double at all |
| Component render | RTL / Vue Test Utils / Angular TestBed / `cy.mount` / Storybook with mocked network, `jsdom`/`happy-dom` - counts as unit for the oracle | — | full app in a real browser |
| API | none, or HTTP intercepted | in-process test client (FastAPI/Starlette `TestClient`, Flask/Django/DRF client, supertest `request(app)`, Nest TestingModule) or a real client to a live URL; gRPC/GraphQL/WebSocket; RequestsLibrary/RESTinstance; asserts status/body | full app behind the browser |
| Database / store | repository or in-memory fake, mocked client | real ORM/driver (SQLAlchemy, Django ORM, Prisma, TypeORM, Drizzle, Knex, psycopg, asyncpg, mongoose, pymongo, redis, ioredis), `testcontainers`, session/transaction; `sqlite :memory:` and `*-memory-server` lean integration | DB reached through the UI |
| Other I/O | mocked (moto / `@mock_aws`, aws-sdk-client-mock) | real queue (Kafka, RabbitMQ, SQS, bullmq), object storage (real S3, or a LocalStack / testcontainers emulator - a real service over the wire, not moto), email/SMTP, subprocess, cache | — |
| UI / browser | none | none | Playwright `page.`/`expect(page)`, Cypress `cy.visit`, WebdriverIO `browser.`, Puppeteer, Selenium `driver.`, Robot SeleniumLibrary/Browser/AppiumLibrary; selectors, navigation |

A `conventions:` block (Step 0) with `test_layer_overrides` wins over all of this. Markers like
`smoke`/`slow`/`asyncio`/`anyio` are level-neutral: do not read a layer from them. When an
explicit marker/path says one level but the test mocks the whole boundary, trust the reality
(rule 1) and note the mismatch. When no signal is present, treat it as unit and say so.

**Robot Framework:** the level is dominated by the imported Library in `*** Settings ***` -
SeleniumLibrary / Browser / AppiumLibrary → E2E; RequestsLibrary / RESTinstance / RPA.HTTP →
API integration; DatabaseLibrary → DB; SSH/FTP/Imap/Process → system integration. Robot suites
are rarely unit. The full per-framework cue list lives in `reference.md`.

**Why the level matters:** in E2E/UI tests the presence of a response, page, or element IS
the assertion at that layer - do not flag it as a weak check (affects C6 and C14). The level
itself can be the smell: a real API or database call inside a test that presents as a unit
test is a mystery-guest / over-mocking-inverted finding (J3/J6), not a valid integration test.

See `reference.md` for framework- and level-detection cues.

### Step 2: Apply the full Python pattern catalog (Python only)

If the language is Python, scan the file against **all** falsegreen patterns
before proceeding to the semantic judgments. These patterns are organized in
`reference.md` under "Python" by family. Apply them in order:

| Family | Codes | What to look for |
|---|---|---|
| A — never checks | C1, C2, C2b, C2c, C3, C4, C4b, C20, C21, C38, C39, C43, C45, C49, C50, C51, C59, CC | assertion unreachable, missing, swallowed, uncollected, name-shadowed, returned-not-asserted, discarded-comparison statement, empty/multi-call raises-warns context, captured log/output never asserted, skipped mid-test, empty parametrize |
| B — weak/always-true | C5, C6, C6b, C6c, C7, C8, C8b, C9, C11a, C13, C13b, C14, C16, C18, C25, C34, C42, C44, C52, C55, C56, C57 | tautology, truthiness-only, self-compare, broad exception, string repr, generator/lambda always truthy, numeric tautology, membership self-confirmation, mock-rooted compare, never-awaited coroutine, unconfigured Mock attribute |
| C — checks own setup | C19, C28, C29, C48 | pytest.raises wraps too much, binding unread, env mutation, test-mode flag flipped then asserted |
| D — external state | C17, C23, C24, C27, C30, C31, C32, C35 | skip-on-failure, hard path, shared mutable, try/pass, flaky |
| E — wrong thing | C33, C36, C37, C41 | metric not asserted, fail without reason, duplicate case, assert on a None-returning mutator |
| Optional / diagnostic (opt-in) | C22, D1, D3, D4, D5, D6, D7, D8, M2 | apply only when user requests diagnostic pass |

Report each structural finding with its code number and confidence level before
proceeding to Steps 3-6.

**Relationship with the falsegreen scanner:** if the user has already run
`falsegreen <file>` and provides its output, use that as the structural pass
result and proceed directly to Step 3 for findings the scanner marked as
needing semantic review. If no scanner output is provided, apply Step 2 fully.

For TypeScript and JavaScript, apply the TS/JS catalog below, then proceed to Step 3.

### Step 2b: Apply the TypeScript / JavaScript pattern catalog (TS/JS only)

The companion static scanner for these languages is
[falsegreen-js](https://github.com/vinicq/falsegreen-js). It shares the C-codes
where the smell is the same concept and adds JS-specific codes. Apply the catalog,
then proceed to Step 3 for the semantic judgments no static pass can make.

**Load `reference.md` first (mandatory for non-Python).** The table below is a
summary. The full JS-series, the Robot R-codes, and the PL config-audit codes are
defined only in `reference.md`. Read the matching language section in full before
judging any TypeScript, JavaScript, or Robot Framework test - do not rely on this
summary table alone. For Python, the structural catalog in Step 2 above is
complete on its own.

**The S-series is separate, and it applies to every language including Python.**
S1-S18 and S21 sit in `reference.md`, in the section
`## Patterns only the semantic pass can catch (AI-only)`, which sits above the
per-language sections, so loading a language section alone skips all of them. Load
that section together with the "Look-alikes - do NOT flag" paragraph that closes
it. When the host budget cannot hold both the semantic
section and a language section, load the two floor fragments instead of the prose:
`fragments/semantic-cases-compact.md` (a row per S-code) plus
`fragments/semantic-exemptions.md` (the same look-alike exemptions, so the floor
needs no `reference.md` read at all). That is about 7.5 KiB against about 13 KiB.
The language section is what you defer and pull per finding, never the semantic
floor.

| Family | Codes | What to look for |
|---|---|---|
| A - never checks | C2, C2b, C21, CC, JS2, JS4, JS6, JS9, JS11 | empty test, no assertion, every assertion conditional, commented-out assertion, `expect()` without a matcher, skipped (`it.skip`/`xit`), empty `describe`, dead literal branch, swallowed `try/catch` |
| B - weak / always-true | C5, C7, C8, C9, C16, C18, JS3 | tautology, self-compare, exact float equality, `toThrow()` with no error type, time/randomness, stringified equality, snapshot-only |
| C - focus / async | JS1, JS5, JS7 | focused test (`it.only`/`fit`), async query/event not awaited, assertion in a non-awaited callback |
| D - duplicate | C37 | duplicate `it.each`/`test.each` case |
| F - query without assert | JS13 | `getBy*`/`queryBy*` query as a loose statement, result never asserted |
| Optional / diagnostic (opt-in) | D1, D3, D4, D6, D7, M2 | maintainability; apply only when the user requests a diagnostic pass |

If the user has run `falsegreen-js <file>` and provides its JSON output, use that as
the structural pass and proceed to Step 3 for findings that need semantic review.
Full TS/JS pattern detail and look-alikes: see `reference.md`.

### Step 2c: Apply the Robot Framework and secondary-language catalogs

For Robot Framework, Gherkin/BDD, and Tavern there is no summary table here: the
full catalog (the Robot R-codes and the shared C-codes, plus the Gherkin/Tavern
secondary passes) lives only in `reference.md`. Load it and apply the matching
language section before Step 3, together with the language-agnostic S-series
described in Step 2b. The companion Robot scanner is
[robotframework-falsegreen](https://github.com/vinicq/robotframework-falsegreen);
the skill mirrors its codes as a superset. If the user has run it and provides
output, use that as the structural pass, then proceed to Step 3.

### Step 3: Classify test intent

Before judging the expected value, classify each test:

| Class | Meaning | Oracle |
|---|---|---|
| **spec/TDD** | the test is the spec; code must match it | the test itself |
| **characterization** | intentionally freezes current behavior | current output is the oracle |
| **regression** | records a known bug fix | the bug report is the oracle |
| **behavior** | verifies a production rule or contract | spec / docstring / types |

A failing TDD test is not a false positive. A labeled characterization
snapshot is not a frozen bug. Misclassifying here causes false alarms.

### Step 4: Apply the six judgments

Judge each test across J1-J6. Flag only the first judgment that fails; do not double-report the same root cause.

**J1: Does the assertion run?**
Does at least one assertion execute when the test is run normally? An
assertion inside a branch that never fires, or after an unconditional return,
passes vacuously.

**J2: Is the expected value from an independent oracle?**
Is the expected value derived from the spec, the API contract, or independent
human judgment, NOT from the current code output? If the test asserts
`result == current_implementation()`, both sides agree on the same wrong
number. An assertion that re-implements the production formula has the same
problem.

**J3: Is the real unit under test?**
Is the test verifying the actual production unit, or a mock of it? Mocking
the function/class under test and then asserting the mock value is not a test
of the production code.

**J4: Does the assertion verify enough, and the right thing?**
Does the assertion check a meaningful property of the result? Checking only
that the result is truthy, or that an exception was raised without verifying
its type, does not protect the behavior being tested.

**J5: Is the test coupled to implementation internals?**
Does the test fail when internals change - private methods, internal state,
call order - even though the public contract still holds?

**J6: Does the test pass in isolation?**
Does the test depend on execution order, shared mutable state, or fixtures set
up by a sibling test? A test that passes only in a specific order is not
reliably testing anything.

**Then screen every S-code, on every file, whatever the language.** S1-S18 and
S21 are part of this step, not a preamble to it: walk them one by one against
`## Patterns only the semantic pass can catch (AI-only)` in `reference.md`, check
each candidate against the look-alike block that closes that section, then move
on. Step 4 is not complete until every S-code has been considered. The S-series
does not belong to Step 2b or 2c, so a Python run that skipped both still runs it
in full.

### Step 5: Adversarial verify for case 18

Case 18 (expected value contradicts what the code should do) is the highest-
stakes finding: it means the test is freezing a bug as "correct". Before
reporting it:

1. Cite the independent oracle: spec, docstring, type annotation, API
   contract, or domain rule. If you cannot cite one, do not report case 18.
2. Run an adversarial check: assume the expected value is correct and argue
   why. If the argument holds, withdraw the finding.
3. Report only when the oracle clearly contradicts the expected value and the
   adversarial argument does not hold.

Never report case 18 based on gut feeling or pattern-matching alone.

### Step 6: Output the report

For each finding, output:

```
{code} ({J}) - {confidence: HIGH | LOW} - {language} - {level: unit|integration|e2e|fixture} - {intent: spec|char|regression|behavior|scaffold}

Test: {function name, line range}
Finding: {one sentence describing what is wrong}
Evidence: {the specific line(s) that triggered this}
Oracle: {for case 18 only: cite the independent oracle}
Fix hint: {where and how to improve the code or test, one sentence}
```

`{code}` is any catalog id: a semantic case (CASE-10/11/12/15/18), a structural C-code (C*),
a JS/TS code (JS*), a Robot code (R*), or a semantic S-code (S*). `{J}` is the judgment that
failed (J1-J6). Intent is the classification from Step 3. Include it in every finding - it is
required for dataset analysis.

The `level` and `intent` axes carry two extra options for non-behavioral findings:

- `level: fixture` (or a `role:` note such as `role: testdata`/`role: example`/`role: perf`)
  for a finding in a file that is data, a shared resource, an example, or a perf fixture rather
  than a behavioral suite - see the Robot file-role look-alikes in `reference.md`.
- `intent: scaffold` for an unimplemented placeholder (an empty stub, a TODO-only body, a
  generated skeleton that was never filled in) where the finding is about the missing
  implementation, not a wrong oracle.

Then a summary block:

```
SUMMARY
Tests reviewed: N
Findings: M (H high, L low)
Clean: N-M
```

Use HIGH only when there is no plausible legitimate interpretation.
Precision over recall: a wrong HIGH finding is worse than a missed LOW one.

### Step 7 (optional): Suggest project conventions

Run this step only when the report contains 3 or more findings of the same code or pattern.

Add a note at the end of the SUMMARY block:

```
Pattern note: {code or pattern} appears {N} times. If intentional in this project,
add it to the conventions: block (Step 0) to suppress future findings.
```

Do not run Step 7 for reports with fewer than 3 findings. Do not call a separate model -
append the note to the existing SUMMARY using what you already know from the analysis.

---

## Case reference (quick lookup)

| Case | Judgment | Name | Caught by |
|---|---|---|---|
| 10 | J3 | Mocks the unit under test | Semantic |
| 11 | J2/J3 | Asserts the value fed to the mock | Semantic |
| 12 | J2 | Re-implements the production formula | Semantic |
| 15 | J6 | Passes only if another test ran first | Semantic |
| 18 | J2 | Expected value contradicts what the code should do | Semantic + adversarial verify |

Structural codes are handled by the static scanners - [falsegreen](https://github.com/vinicq/falsegreen)
for Python (56 C-codes) and [falsegreen-js](https://github.com/vinicq/falsegreen-js)
for TypeScript/JavaScript (shared C-codes plus the JS-series; see reference.md for the full emitted set). This skill adjudicates
scanner findings when review is needed, and handles the same patterns directly for
any language. The five semantic cases above need the LLM regardless of language.

Full case catalog with language examples: see `reference.md`.

---

# Authoring mode (generate tests, not only detect)

Everything above is **analysis mode** (Mode A): given a test, judge it. When the
user asks to **write or create tests** instead, switch to **authoring mode**
(Mode B). The catalog becomes a generation guard: a test you write must pass the
same J1-J6 it would be judged by, so you do not ship a false-green *shape*. The
guard is on the shape, not the oracle's truth: it stops a test built from the
code's current output, but it cannot tell a hand-written wrong oracle from a right
one. That stays the user's responsibility.

Mode B runs two ways. In an editor host (Claude Code, Cursor, Gemini, Codex) it
elicits the missing answers interactively (Steps A0-A1), can render every
requested language in one pass, and repeats the self-check until clean (A4). On
the CLI, `falsegreen-skill generate <spec-file> --lang <language>` renders a
written test-spec - the oracle already supplied in the file - into one language
and self-checks it once (revising once). It does not elicit, so a spec with no
oracle is refused rather than guessed; and when its bounded revision cannot reach
clean it emits the draft with a FAILED/UNVERIFIED verdict and a non-zero exit,
rather than withholding. Use the host path when the oracle still has to be
discovered; use the CLI when it is already written down.

## Step A0: Architect/QA gate (decide before you ask)

Before eliciting anything, run one triage pass. It answers three questions at
once, in a single step - not a separate agent:

- **Should a test be created at all?** If the request names no testable unit or
  behavior, ask for the target instead of guessing. If the user asks for an E2E
  test where a unit test would catch the defect, warn (inverted-pyramid) before
  generating.
- **How many questions are actually needed?** Ask only the Step A1 answers that
  are missing. If the request already carries level + language + oracle + doubles,
  skip straight to Step A2 with zero questions. The oracle is the one answer you
  must have: without it you can only freeze current behavior, the false-green the
  skill exists to prevent.
- **Who decides what?** The architect role owns the pyramid level and its shape;
  the QA role owns the oracle and the doubled boundaries. Same step, one pass.

## Step A1: Ask before you write

Do not generate a test from the code's current output - that produces a
characterization test, which is false-green by design. Ask the user for what only
they can supply:

1. **Which pyramid level?** unit / integration (API or database) / E2E. (If they
   say "all", produce one per level.)
2. **Which language(s) / framework(s)?** Python, TypeScript, JavaScript, Robot -
   or "every stack the project uses".
3. **What behavior, and what is the independent oracle?** the spec, contract, or
   the expected value and where it comes from. This is mandatory: without an
   oracle you can only freeze current behavior.
4. **Which boundaries are doubled?** database, network, clock (unit/integration).

If the user already gave any of these, do not re-ask it.

## Step A2: Build one language-neutral test spec (the single base)

Capture the answers in one canonical spec, independent of language, conforming to
`schema/test-spec.json`:

```yaml
level: unit | integration | e2e
unit: <function / endpoint / page under test>
scenario: <one behavior, stated as a sentence>
arrange: [<preconditions>]
act: <the call or interaction>
oracle:
  source: spec | contract | example
  expected: <value or condition, derived from the source - NOT from the code>
doubles: [database, network, clock]   # only for unit/integration
```

One spec, then rendered into every requested language. The spec is the single
source so the tests stay equivalent across stacks.

**Multiple levels for one feature.** Do not write a single test that "covers all
levels" - that is a category error. Each level tests a different thing with a
different oracle and different doubles. When the user wants unit AND integration
AND E2E, produce **one spec per level** (a small scenario x level matrix):

- unit: the pure logic, boundaries doubled; oracle = return value. Many of these.
- integration: the endpoint/query with a real client or driver, no double on the
  crossed boundary; oracle = status + body, or the row read back. Fewer.
- e2e: the journey through the UI; oracle = visible page state. Very few.

Rules: elicit the oracle per level (it differs); do not repeat the unit-level
assertion at e2e (wrong layer, redundant); respect pyramid shape - if the user
asks for an e2e test where a unit test would catch the defect, say so before
generating (inverted-pyramid warning). A real API/DB call is valid at integration
but is itself a smell at unit (J3/J6).

## Step A3: Emit per language, with the level-appropriate oracle

Render the spec into each framework, using the canonical renders in
`examples/authoring/` (`apply-discount.spec.yaml` rendered to `.py`, `.test.js`,
`.test.ts`, and `.robot`) as the few-shot template for a green-for-real test in
each language. The oracle form depends on the level:

- **unit:** assert the return value / state against `oracle.expected`.
- **integration / API:** assert status AND the response body (not status alone).
- **integration / database:** assert the persisted row, read back independently.
- **E2E:** assert the visible page state / element (presence is the oracle here).

Robot emits a `.robot` test; extract any reusable step into a `.resource`
keyword (never put `*** Test Cases ***` in a `.resource` - that is R3).

## Step A4: Validate the draft with Mode A (close the loop)

This is the unification: do not invent a separate check. **Run Mode A (Steps 1-6)
on the test you just generated**, at its level, as if a developer had handed it to
you for review. Concretely, confirm it trips no catalog code:

- J1: at least one assertion runs unconditionally (no C1/C20/C21/JS9...).
- J2: the expected value comes from the oracle, not the code (no C5/C7/C14/C18).
- J3: the real unit is exercised at the stated level (no over-mock; a real
  API/DB call belongs to integration, not unit).
- J4: the assertion checks the right, specific thing (no C6/C9 weak check).
- J5/J6: not coupled to internals; passes in isolation.

Apply the precision-first rules in `fragments/precision-rules.md` during this
self-review, and use the BAD cases in `examples/<language>/family_*` and
`examples/<language>/semantic_cases.*` as the negative catalog: the generated
test must not resemble any of them.

If the Mode A pass returns any finding, revise the test and run Mode A again. In
a host, repeat until the analysis is clean and only emit a test that passes its
own review - that is what makes generation and validation one skill, not two. The
CLI bounds this to one revision (it is a command, not an agent loop): if the test
still trips a HIGH false-green finding it emits the draft with a FAILED verdict
and exit 1, and if the self-check itself cannot run it reports UNVERIFIED and exit
3. The CLI never presents an unchecked or still-flagged test as verified.

## Step A5: Output

For each generated test, output the language, level, the cited oracle, the test
code, and one line confirming it passes the self-check. End with the canonical
test-spec so the user can regenerate it in another language later.

---

# AI-fix mode (propose a fix, hand the gate to the host)

Mode A judges a test; Mode B writes one. **Mode C** takes a finding from a
falsegreen report and proposes a stronger test that closes it. It reuses Mode B
end to end: a proposed fix is an authored test, so it is generated against the
oracle and self-validated by running Mode A (Steps 1-6) over it until clean.

The boundary is explicit: **the skill proposes the fix and the validation
contract; it does not run the gate.** Proving that the strengthened test fails
when the code breaks is mutation testing's job, and that needs an executable
environment the skill does not have (the skill does not run tests). The host or
developer runs the bidirectional gate; the skill hands them a contract to fill.

## Step C1: Read the finding

Take one finding (`schema/finding.json`): its `case`, `judgment`, `language`,
`level`, the `evidence` lines, and, for case 18, the cited `oracle`. The finding
says what is wrong; the fix has to make the test able to fail on exactly that.

## Step C2: Propose the strengthened test (Mode B machinery)

Derive a `schema/test-spec.json` from the finding and the existing test, then run
Mode B Steps A2-A4 on it. The oracle stays independent of the code (never lift the
expected value from current output, that re-freezes the bug). Strengthen at the
judgment that failed:

- J1 finding (assertion never runs): make at least one assertion run unconditionally.
- J2 finding (expected value from the code): re-derive the expected value from the
  cited oracle.
- J3 finding (mocks the unit under test): exercise the real unit at the stated level.
- J4 finding (weak / always-true check): assert the specific value, not truthiness.
- J5/J6 finding (coupled / order-dependent): make the test pass in isolation.

Run Mode A over the proposal (Step A4). If it trips any catalog code, revise and
re-run until clean. Only propose a test that passes its own review.

## Step C3: Emit the validation contract (the skill stops here)

Alongside the proposed test, emit the gate contract the host will run, conforming
to `schema/fix-validation.json`. The skill fills the `finding` reference and the
intended `tier`; the host fills `clean_replica`, `mutated_replica`, and the
`verdict` after running the gate.

The gate is bidirectional and the rule is fixed: run the strengthened test on a
**clean replica** (must pass) and on a **mutated replica** where the bug class is
reintroduced (must fail). **accept** requires `clean_replica=pass` AND
`mutated_replica=fail`; any other combination is **reject**. A test that still
passes on the mutated replica has not closed the finding. Two cost tiers, host's
choice: `suite-rerun` (rerun the whole suite, cheap and coarse) or
`targeted-mutation` (a focused mutant on the unit, costlier and precise). Tooling
is the host's: mutmut or cosmic-ray for Python, Stryker for JS/TS. The adjudication
rule, the tiers, and the flaky case live in `reference.md` (F7).

This bidirectional gate is the SENTINEL / Pizzini contribution credited in
`CREDITS.md`: a proposed fix must pass the original suite and fail on a mutation
before being accepted.

**The CLI can run this gate locally (V1, Python/pytest only).** In an editor host
the skill proposes and the host runs the gate. The npm CLI adds an opt-in
`falsegreen-skill fix <test-file> --case <code> --line <n> --sut <file>` command
that runs the whole gate on a clean replica: it asks the LLM for a test-file-only
patch, then runs parse (`py_compile`), preserve (`pytest` against the real SUT),
and a line-scoped mutation gate (a built-in operator on the SUT line; full mutmut
integration is deferred to a later version). It never auto-applies the patch and never edits the
SUT. Without `--sut`, or with `--cheap` (parse + preserve only), it degrades to
**propose-only / unvalidated** and labels the output as not proven. V1 fixes the
mechanical findings (C2b/C20/C21/C5/C7); JS/TS/Robot fix paths and the deep
semantic cases (10/11/12/18) are v2. The honest limit holds: the gate proves the
fix catches the targeted mutant, not every possible bug.

## Step C4: Output

Output the finding being fixed, the proposed test (language, level, cited oracle,
code), the line confirming it passes its own Mode A self-check, and the
`schema/fix-validation.json` contract for the host to run. State plainly that acceptance
waits on the host's gate result; the skill does not run it.

---

# Where outputs go

- **Analysis report (Mode A):** printed to the conversation (a host) or stdout
  (the CLI). It is not written to a file by default. The CLI emits text, or
  `--json` (conforming to `schema/report.json`); persist it by redirecting
  (`... --json > report.json`) and wire `--fail-on-high` into CI (exit 2). A
  persisted report is a run artifact: keep it in a gitignored path
  (`.falsegreen/`, `reports/`), never commit it.
- **Generated tests (Mode B):** written into the project's existing test tree by
  level and framework convention - `tests/unit/`, `tests/integration/`,
  `tests/e2e/`, a `*.test.ts` beside the source, a `.robot` suite with shared
  steps in a `.resource`. Propose the path and confirm with the user; never
  invent a new dump location.

---

## Precision-first rules

<!-- fg:precision-rules:start -->
1. Never report case 18 without citing an independent oracle.
2. If a mock replaces a network/disk/time dependency (an edge), it is NOT
   case 10. Case 10 applies only when the mock replaces the unit being tested.
3. A characterization test is not a bug even if the expected value looks wrong.
   Classify first (Step 3) before judging.
4. A test decorated with `@pytest.mark.skip`, `@pytest.mark.xfail(strict=True)`,
   or `@unittest.skip` that has no assertion body is NOT C2/C5. The marker stops
   it from running (skip) or fails it on XPASS (strict xfail). A plain
   `@pytest.mark.xfail` (no `strict=`) is exempt ONLY when the project turns on
   strict xfail globally - `xfail_strict = true` in pytest config (pytest.ini,
   `[tool.pytest.ini_options]`, setup.cfg) or `-o xfail_strict=true` - because the
   marker then inherits strict and an XPASS fails the run. Otherwise a plain xfail
   still executes and an XPASS keeps exit status 0, so a no-assertion test stays
   false-green. Check the pytest config (or a `conventions:` override) first.
5. In web/UI layer tests, a truthiness check on a response or locator object
   is NOT case 6. Presence of a response IS the assertion at that layer.
6. Tests decorated with `@given`, `@hypothesis`, or `@fuzz` that have no
   explicit `assert` are NOT C2. These frameworks generate and check
   assertions internally.
7. `expectTypeOf(v).toEqualTypeOf<T>()` in Vitest is a compile-time type
   assertion. Not C5. Do not flag it.
<!-- fg:precision-rules:end -->

**Tie-break (C9 / C28 / S17, same J4 family).** When more than one of these would fire on the
same `pytest.raises` / `toThrow`, report only the most specific code; do not stack them. A broad
`pytest.raises(Exception)` (or `toThrow()` with no type) that is followed by an assertion on the
bound message - `assert str(exc.value) == ...` / `exc.value.<attr>` - fires NOTHING: the message
assertion narrows the type to the SUT's contract, so C9, C28, and S17 are all satisfied.

**Severity is a ceiling, not a floor.** The severity listed for each code (HIGH / LOW) is the
maximum. Intent classification (Step 3) can only LOWER it - a HIGH code on a deliberate
characterization/spec/scaffold test drops to LOW or is withdrawn. It can never RAISE a code above
its catalog severity.

---

## Multi-agent mode (case 18 deep analysis)

For a case 18 finding that requires high confidence (blocking a deploy,
cited in a report), run a two-pass adversarial check:

**Pass 1 (finder):** Identify the expected value and the oracle. Report
the finding with the cited oracle.

**Pass 2 (refuter):** Given the case 18 finding, argue that the expected
value is actually correct. Consider: is this a characterization test? Is the
oracle you cited authoritative for this specific test? Does the domain have
a convention that makes the expected value correct?

If the refuter provides a plausible argument, downgrade to LOW or withdraw.
Report case 18 HIGH only when the refuter cannot mount a credible defense.

---

## What this skill does not do

- It does not suggest code fixes unless asked.
- It does not run the tests.
- It does not run the AI-fix gate (Mode C) from inside an editor host. It proposes
  the strengthened test and the `schema/fix-validation.json` contract; the host or
  developer runs the test on the clean and mutated replicas (mutmut / cosmic-ray /
  Stryker). The npm CLI is the exception: `falsegreen-skill fix` runs the gate
  locally for Python/pytest (V1), still propose-only and never touching the SUT.
- It does not analyze production code unless the test snippet includes it.
- It does not flag maintainability smells **by default** (bad names, missing
  messages, Eager Test, Lazy Test, long tests). Those are not false-positive risks.
  They are available as an **opt-in diagnostic pass** (codes D1/D3/D4/D5/D6/D7/M2),
  applied only when the user asks for it - mirroring the diagnostic/coupling group
  in falsegreen and falsegreen-js. For a dedicated linter layer, `ruff`'s `PT` rules
  (Python) or eslint-plugin-jest (JS/TS) also cover this ground.
