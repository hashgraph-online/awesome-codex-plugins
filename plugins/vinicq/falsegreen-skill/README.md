# falsegreen-skill

[![CI](https://github.com/vinicq/falsegreen-skill/actions/workflows/ci.yml/badge.svg)](https://github.com/vinicq/falsegreen-skill/actions/workflows/ci.yml)
[![npm version](https://img.shields.io/npm/v/falsegreen-skill.svg)](https://www.npmjs.com/package/falsegreen-skill)
[![Downloads](https://img.shields.io/npm/dm/falsegreen-skill.svg)](https://www.npmjs.com/package/falsegreen-skill)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![Docs](https://img.shields.io/badge/docs-online-blue.svg)](https://vinicq.github.io/falsegreen-docs/)

**LLM-based semantic analysis for false-positive test detection.** Companion
to [falsegreen](https://github.com/vinicq/falsegreen), the Python static
scanner.

For Python, this skill applies the complete falsegreen catalog directly - all
structural and semantic patterns - via LLM analysis, without requiring the
static scanner to run first. For TypeScript, JavaScript, and Robot Framework it
is the primary detection tool. It is a superset of the three static scanners
(falsegreen, falsegreen-js, robotframework-falsegreen) plus semantic patterns only an LLM
can detect.

**The falsegreen family** (install the one for your stack):

| Tool | Stack | Install | Package |
|---|---|---|---|
| [falsegreen](https://github.com/vinicq/falsegreen) | Python / pytest | `pip install falsegreen` | [PyPI](https://pypi.org/project/falsegreen/) |
| [falsegreen-js](https://github.com/vinicq/falsegreen-js) | JS / TS | `npm i -D falsegreen-js` (`npx falsegreen-js`) | [npm](https://www.npmjs.com/package/falsegreen-js) |
| [robotframework-falsegreen](https://github.com/vinicq/robotframework-falsegreen) | Robot Framework | `pip install robotframework-falsegreen` | [PyPI](https://pypi.org/project/robotframework-falsegreen/) |
| **falsegreen-skill** | semantic LLM pass | `npx falsegreen-skill analyze <path>` | [npm](https://www.npmjs.com/package/falsegreen-skill) |

---

## New here? Start here

This is an LLM skill that reads your tests and flags the false-green ones: tests
that stay green even when the code they cover is wrong. It catches the semantic
cases the static scanners cannot, because it reads the test as text and works
out what the test was meant to prove.

A test like this passes forever, no matter what the code does:

```python
# before - false-green: asserts the mock back to itself
def test_discount(mock_rate):
    mock_rate.return_value = 0.1
    result = apply_discount(100, mock_rate)
    assert result == mock_rate.return_value   # passes for ANY result, even a wrong one
```

The fix is an independent expected value, one the code did not produce:

```python
# after - the test can now fail when apply_discount is wrong
def test_discount():
    result = apply_discount(100, rate=0.1)
    assert result == 90                       # 10% off 100, computed by hand from the spec
```

The skill reads the first version and reports it as a J2 finding (the expected
value is borrowed from the code, not from an independent source) with the line,
the reason, and a fix hint. Three steps to try it:

1. **Install or enable it** for your host - see [Installation](#installation) below.
2. **Point it at a test file** - `npx falsegreen-skill analyze tests/test_discount.py`,
   or, in an editor host, just ask it to "analyze this test for false-positive smells".
3. **Read the finding** - each one names the catalog code, the failed judgment
   (J1-J6), why the test cannot fail, and how to fix it. See
   [Quick example](#quick-example).

For a step-by-step walkthrough of all three modes with runnable examples and
flow diagrams, read the [user guide](docs/user-guide.md). The full catalog, the
judgments, and the per-language reference live in the
[docs site](https://vinicq.github.io/falsegreen-docs/) and in
[reference.md](reference.md). For a visual architecture overview, host and
language routing plus the Mode A/B/C flow diagrams, see
[docs/architecture.md](docs/architecture.md).

---

## Why this exists

A test suite with 100% green tests is not a proof of correctness. It is a
proof that no test failed - which is a different thing. Tests can pass
permanently not because the code is right, but because the test never checks
anything meaningful.

Static analysis tools catch some of these cases. Linters like ruff or
flake8-pytest-style catch syntax-level patterns: a bare `assert True`, a
missing `assert` call, an unreachable block. Mutation testing tools like
mutmut probe whether tests actually fail when the code changes. Both
approaches have limits: linters cannot reason about test intent, and
mutation testing requires the code to run.

This skill fills the gap between linters and mutation testing. It reads the
test as text, reconstructs the intent, and asks six structural questions about
whether the test can actually fail. The questions are derived from the
taxonomy of false-positive test patterns collected in
[CREDITS.md](CREDITS.md).

The core insight: a test is useful if and only if there exists some incorrect
implementation that would cause it to fail. If no such implementation exists,
because the assertion is unreachable, tautological, or verifies the mock
instead of the code, the test is structurally green regardless of whether the
production code is correct.

---

## The methodology

One rule underlies every judgment: a test is useful only if it can fail when
the code breaks.

The six-judgment framework (J1-J6) makes this rule concrete:

| # | Question | Catches |
|---|---|---|
| J1 | Does the assertion run? | Dead assertions, vacuous loops, swallowed failures |
| J2 | Is the expected value from an independent oracle? | Echo mocks, formula re-implementation, spec contradictions |
| J3 | Is the real unit under test, not a mock of it? | Mock-the-SUT, self-confirming literals |
| J4 | Does the assertion verify enough? | Truthiness-only, len > 0, repr coupling, broad raises |
| J5 | Is the test coupled to implementation internals? | Positional mock args, private method testing |
| J6 | Does the test pass in isolation, without ordering? | Shared mutable state, test-order dependency |

A test is flagged HIGH only when the first failed judgment has no plausible
legitimate interpretation. A test is flagged LOW when the smell is likely but
has plausible intent. Everything else is PASS.

**Precision over recall.** One wrong flag on a legitimate test costs more
goodwill than a missed smell. Exemptions are explicit:

- Semantic case 18 requires a cited independent oracle (spec, docstring, API
  contract). Without a citation, do not report case 18.
- Characterization tests - intentionally freezing current behavior - are not
  false positives.
- Boolean predicates (`isinstance`, `.exists()`, `.is_dir()`) are not weak assertions.
- In HTTP/UI layer tests, a truthiness check on a response object means
  "the request succeeded" and is meaningful.

Full protocol: [SKILL.md](SKILL.md).

---

## What it detects

### Python - structural patterns (complete falsegreen catalog)

**Family A - The test never checks anything**

| Code | Pattern | Example |
|---|---|---|
| C1 | Assert inside `if`/`for` that may not run | `if items: assert items[0].valid` when `items` can be `[]` |
| C2 | No assertion at all | test body contains only setup calls |
| C2b | Calls SUT but discards result | `result = process(x)`, result never asserted |
| C3 | Assert inside `try` whose `except` swallows it | `except Exception: pass` catches `AssertionError` |
| C4 | Test function nested inside another function | pytest does not collect inner defs |
| C4b | Test class with `__init__` | pytest skips classes that have `__init__` |
| C20 | Assertion after unconditional `return`/`raise` | dead code, never runs |
| C21 | Every assert is conditional, none runs unconditionally | all asserts inside `if/else` branches |
| CC | Commented-out assertion | `# assert result == 42` |

**Family B - The check is weak or always true**

| Code | Pattern | Example |
|---|---|---|
| C5 | Always-true check | `assert True`, `assert (a, b)` (non-empty tuple) |
| C6 | Truthiness / `len > 0` / substring in `str()` | `assert result`, `assert len(x) > 0` |
| C6b | Positional mock arg via computed index | `call_args.args[expected_args.index("target")]` |
| C7 | Self-comparison | `assert name == name` |
| C8 | Exact float equality | `assert ratio == 3.14159` |
| C9 | `pytest.raises` too broad or no `match=` | `with pytest.raises(Exception)` |
| C11a | Self-confirming literal | `product.price = 100; assert product.price == 100` |
| C13 | Mock assertion uncalled or misspelled | `mock.assert_called_once` (no parens) |
| C13b | `@patch` without `autospec=True` | typos in kwargs pass silently |
| C14 | Golden file written from actual output | first run records any output as truth |
| C16 | Depends on wall clock, random, or `sleep` | `datetime.now()` unfrozen, `time.sleep()` |
| C18 | `str()`/`repr()` comparison | `assert str(user) == "User(Alice, 30)"` |
| C25 | `@pytest.mark.xfail` without `strict=True` | XPASS silently accepted |
| C34 | Suboptimal assertion form | `== True`, `== None`, `not x in y`, `len == 0` |

**Family C - The test checks its own setup**

| Code | Pattern | Example |
|---|---|---|
| C19 | `pytest.raises` wraps multiple calls | setup call inside raises block may be the one that raises |
| C28 | `pytest.raises` binding variable never read | `as exc:` but `exc` never asserted |
| C29 | `os.environ` mutated directly | `os.environ["KEY"] = "x"` without `monkeypatch` |

**Family D - Green depends on outside factors**

| Code | Pattern | Example |
|---|---|---|
| C17 | `pytest.skip()` inside broad `except` | assertion failure silently becomes a skip |
| C23 | Hard-coded absolute or home-relative path | `/home/user/data.csv` |
| C24 | Module-level mutable state shared between tests | `_cache = {}` at module scope |
| C27 | `try/except/pass` instead of `pytest.raises` | both raise and no-raise leave test green |
| C30 | `responses.add()` without activating interceptor | real HTTP goes through |
| C31 | `capsys.readouterr()` result discarded | captured output never asserted |
| C32 | `@pytest.mark.skip` without `reason=` | forgotten skip |
| C35 | `@pytest.mark.flaky` / retry decorator | masks non-determinism |

**Family E - The test checks the wrong thing**

| Code | Pattern | Example |
|---|---|---|
| C33 | sklearn/ML metric computed but not asserted | `accuracy_score(y, y_hat)` result discarded |
| C36 | `pytest.fail()` without reason | CI shows only `FAILED`, no context |
| C37 | Duplicate case in `@pytest.mark.parametrize` | same `(a, b, expected)` tuple appears twice |

### Semantic patterns (all three languages)

Semantic patterns require LLM judgment - no static rule can detect them.

| Case | Pattern |
|---|---|
| 10 | Patches the unit under test (not a dependency) |
| 11 | Asserts the value fed to the mock (echo) |
| 12 | Re-implements the production formula as the expected value |
| 15 | Passes only when another test has already run |
| 18 | Expected value contradicts the spec (freezes a bug as correct) |

The tables above are the most common Python and semantic patterns, not the whole catalog.
The full set is **125 codes**: the Python `C*` series (up to C59), the TS/JS `JS*` series
(up to JS31), the Robot `R*` series (up to R8b), the project-layer `PL*` and diagnostic
`D*`/`M*` codes, and the semantic `S1`-`S18` and `S21` series. Each carries a bad-pattern example and
a clean look-alike in [reference.md](reference.md), the canonical catalog.

---

## Diagnostic and coupling codes (opt-in)

These codes do not create false positives, but they reduce observability and
make failures harder to diagnose. They are OFF by default and can be enabled
per code in `.falsegreen.toml`:

```toml
[tool.falsegreen]
severity = { D1 = "info", D3 = "info", D4 = "info", D5 = "info", D6 = "info", M2 = "info" }
```

| Code | Pattern | Why it matters |
|---|---|---|
| D1 | Assertion Roulette: 2+ asserts without messages | CI output says only the line number, hard to triage |
| D3 | Duplicate Assert: exact same assertion written twice | second assertion adds nothing |
| D4 | Unnamed Parametrize: 3+ cases, no `ids=` | CI shows `test[0]`, `test[1]`, unreadable failure reports |
| D5 | Inline Setup Excess: 5+ setup statements before first assert | test should be split or setup moved to a fixture |
| D6 | Debug Print: `print()` or `pprint()` in test body | suppressed by default, often a forgotten debug statement |
| M2 | Long Test Method: test body over 50 lines | trying to verify too many concerns at once |

---

## What we don't flag (and why)

Measured against the [Open Catalog of Test Smells](https://test-smell-catalog.readthedocs.io/) (517 documented smells), only the false-green slice is in scope. The skill is the broadest of the family - it reads intent - but it is still false-green only. These stay out, on purpose:

- **Brittleness / false-red** (a test that breaks without a real bug): sensitive equality, brittle or fragile assertions. The opposite axis.
- **Hygiene / maintainability**: assertion roulette, magic numbers, long tests. Linter territory (ruff/ESLint/Robocop); a few are surfaced here as opt-in diagnostics.
- **Slow, design, naming, duplication, runtime/culture**: none are about whether the test protects.

The skill carries every structural proxy of the scanners (`C16` for uncontrolled time, `C23` for hard-coded paths, `C24`/`C15` for shared state) plus the semantic patterns no parser sees: negative-only security assertions (`S11`), patching the unit under test (`S12`), and order-dependence across files (`S13`). See [CREDITS.md](CREDITS.md) for the full cross-walk against the literature.

---

## How it compares

**vs. ruff / flake8-pytest-style**

Ruff and flake8-pytest-style catch syntax-level patterns: `assert True`,
`pytest.raises` with no type, magic values in assertions. They are fast and
precise for the patterns they cover - about 8-10 of the 37+ cases in the
falsegreen catalog.

This skill covers all 37+ structural codes and the 5 semantic cases that
require reading the test as a whole - echo mocks, formula re-implementation,
spec contradictions. The two tools are complementary: run the linter for
instant feedback on simple cases, run the skill for semantic judgment on the
rest.

**vs. PyNose / pytest-smell**

PyNose and pytest-smell are the closest research counterparts. Both apply the
classic Palomba 2018 test-smell taxonomy (Assertion Roulette, Duplicate
Assert, General Fixture, etc.). The falsegreen taxonomy is narrower: it
focuses only on patterns that create false-positive green tests, not on
maintainability smells in general.

Where there is overlap (Assertion Roulette = D1, Duplicate Assert = D3),
falsegreen flags them as diagnostic codes - informational, not blocking.
The structural codes unique to falsegreen, 56 of them, cover patterns that
Palomba's taxonomy does not address because they were derived specifically
from studying how green tests hide broken code in CI.

**vs. mutmut / cosmic-ray**

Mutation testing answers the question definitively: change the code, does the
test fail? That is the ground truth. Mutmut and cosmic-ray are accurate for
the programs they can run, but they require an executable environment, a full
test suite, and minutes to hours per run.

This skill is a static pre-flight check. It cannot prove that a test fails
when the code changes - that is mutation testing's job. It can identify, in
seconds, tests that are structurally unable to fail: assertions that never
execute, checks that are always true by construction, mocks that intercept
the function being tested. Think of the skill as a fast filter before the
mutation testing pass.

---

## How to use

## Installation

| Platform | How |
|---|---|
| Claude Code | `/plugin marketplace add vinicq/falsegreen-skill` then `/plugin install falsegreen-skill@falsegreen` |
| Claude.ai / Anthropic API Skills | `npm run build:targets`, then package `dist/claude-agent-skill/` as the standalone skill |
| OpenAI Codex CLI | No single-command install: clone the repo and run `codex` for the full protocol (scoped to the clone), or copy `AGENTS.md` into your own project / `~/.codex/AGENTS.md` for compact review (see [`contexts/codex.md`](contexts/codex.md)) |
| Antigravity CLI (`agy`) | Install as a plugin: `agy plugin install https://github.com/vinicq/falsegreen-skill` (subpath `.antigravity-plugin/`), or open the repo and `agy` discovers the workspace skill at `.agents/skills/falsegreen-skill/SKILL.md`. From Gemini CLI: `agy plugin import gemini` |
| Gemini Agent Skill | workspace skill at `.agents/skills/falsegreen-skill/SKILL.md`, or `npm run build:targets` for `dist/gemini-skill/` |
| Cursor | Copy contents of `contexts/cursor.md` to `.cursor/rules/falsegreen-skill.mdc` |
| CLI | `npx falsegreen-skill analyze tests/test_example.py`, see [docs/cli.md](docs/cli.md) |
| API | Use the defined provider guides in `contexts/claude.md`, `contexts/codex.md`, and `contexts/gemini.md` |

### Skill or static scanner?

Use the static scanner (`falsegreen` for Python, `falsegreen-js`, `robotframework-falsegreen`)
for fast, deterministic checks in CI and pre-commit: it proves what a parser can
see and never needs an API key. Use this skill for the semantic cases a parser
cannot reach - a mock standing in for the unit under test, an expected value
copied from the code, a value that contradicts the spec. The skill is a superset:
it carries every structural code of the three scanners plus the AI-only semantic
patterns. A common setup runs the scanner on every commit and the skill on the
files the scanner cannot fully judge.

### Quick example

Given this test that echoes the mock back to itself:

```python
# tests/test_tax.py
def test_calculate_tax(mock_calc):
    mock_calc.return_value = 0.15
    result = calculate_tax(100, mock_calc)
    assert result == mock_calc.return_value  # J2: asserting the mock, not behavior
```

```bash
export ANTHROPIC_API_KEY=sk-ant-...
npx falsegreen-skill analyze tests/test_tax.py
```

Output:

```
CASE 11 (J2) - HIGH - Python - spec

Test: test_calculate_tax (line 3-6)
Finding: The assertion checks mock_calc.return_value - the same value the
mock was configured to return. This passes for any return value, including
wrong ones.
Evidence:
  mock_calc.return_value = 0.15
  assert result == mock_calc.return_value
Fix hint: Assert against an independently computed expected value, e.g.
assert result == 15.0 for a 15% tax on 100.

SUMMARY
Tests reviewed: 1
Findings: 1 (1 high, 0 low)
Clean: 0
```

### Try it on your test suite

Point the CLI at any test file or directory:

```bash
# single file
npx falsegreen-skill analyze tests/test_orders.py

# multiple files
npx falsegreen-skill analyze tests/test_orders.py tests/test_payments.py

# JSON report for CI, exits 2 if any HIGH finding is present
npx falsegreen-skill analyze tests/test_orders.py --json --fail-on-high

# deep analysis with a stronger model
npx falsegreen-skill analyze tests/test_orders.py --model claude-opus-4-8

# lower temperature for more deterministic output (default is already 0.2)
npx falsegreen-skill analyze tests/test_orders.py --temperature 0.0
```

The skill identifies the language from the file extension. TypeScript and JavaScript work the same way - no extra flags needed.

Full flag reference: [docs/cli.md](docs/cli.md).

---

### Propose a fix and prove it (AI-fix mode, V1)

`analyze` finds a false-green; `fix` proposes a stronger test and proves it before you trust it. It is opt-in, Python/pytest only, and propose-only: it prints a test-file patch but never applies it and never edits your production code.

```bash
# propose a patch for a C2b finding and run the gate against the real SUT
npx falsegreen-skill fix tests/test_discount.py --case C2b --line 14 --sut src/discount.py

# parse + preserve only, no mutation gate (no runnable SUT or a quick pass)
npx falsegreen-skill fix tests/test_discount.py --case C5 --line 9 --cheap

# machine-readable gate verdict (schema/fix-validation.json)
npx falsegreen-skill fix tests/test_discount.py --case C20 --line 22 --sut src/discount.py --json
```

The gate runs three checks on a clean replica: the patch parses, it passes `pytest` against the real code, and it **fails** on a line-scoped mutation of the SUT (a built-in operator on the SUT line; full mutmut integration is deferred to a later version). A patch is accepted only when it both passes on correct code and goes red on the mutant, which is what proves the new assertion catches a bug instead of being a fresh tautology. Without `--sut` it degrades to propose-only and says the fix is unvalidated. The honest limit: the gate proves the fix catches the targeted mutant, not every possible bug. JS/TS/Robot and the deep semantic cases are v2.

---

### Author a test from a spec (authoring mode, Mode B)

The same protocol runs in reverse. Given a spec and the code under test, the skill proposes a
test with an **independent** oracle: an expected value derived from the spec, not read back
from the code. Before writing it, an architect/QA gate (**A0**) runs the review judgments and
the precision rules over the design, so the generated test is one the review pass would accept
rather than a fresh false-green.

Two ways to drive it. In a host (Claude Code, Codex, Gemini, Cursor, plain LLM) ask the skill
to "write a test for this function against this spec" and it elicits the level, language, and
oracle interactively. Or on the CLI, write the answers into a test-spec file
([`schema/test-spec.json`](schema/test-spec.json)) and render one stack, self-checked:

```bash
# render the shipped example spec to a Python test, then run Mode A on the result
falsegreen-skill generate examples/authoring/apply-discount.spec.yaml --lang python
# other stacks from the same spec: --lang typescript | javascript | robot
```

The CLI does not elicit - a spec with no `oracle` is refused, because a test generated from the
code's current output only freezes the bug. See [SKILL.md](SKILL.md), [docs/cli.md](docs/cli.md),
and [docs/decisions/0004-authoring-mode.md](docs/decisions/0004-authoring-mode.md).

---

### Claude Code (primary path)

Add the marketplace and install the plugin:

```
/plugin marketplace add vinicq/falsegreen-skill
/plugin install falsegreen-skill@falsegreen
```

Then invoke the skill with `/falsegreen-skill:falsegreen-skill`, or just attach a
test file and ask for false-positive analysis - the skill triggers on intent.
The skill identifies the language and framework, classifies the test intent,
applies the six-judgment protocol, and reports findings with case numbers,
confidence levels, and fix hints.

For Python, the skill applies the full pattern catalog directly. Optionally,
run the static scanner first to speed up batch analysis:

```bash
pip install falsegreen
falsegreen tests/
```

If you provide the scanner output, the skill uses it as the structural pass
and applies semantic judgment on top. Without it, the skill runs everything.

### Defined API providers

This skill is not tied to Claude. The maintained provider paths are Anthropic,
OpenAI/Codex, Google Gemini, and the configured CLI providers listed in
`providers.md`.

See [providers.md](providers.md) for per-provider invocation code and Cursor setup.

### Cursor

Add `.cursor/rules/falsegreen-skill.mdc` to your project (template in
[providers.md](providers.md)). Open a test file, ask Cursor to analyze it for
false-positive smells, and the J1-J6 protocol runs automatically.

---

## Supported languages and frameworks

| Language | Frameworks |
|---|---|
| Python | pytest, unittest |
| TypeScript | Jest, Vitest, Mocha + Chai, React Testing Library, Vue Test Utils, Angular TestBed |
| JavaScript | Jest, Vitest, Mocha + Chai, Jasmine, React Testing Library |
| Robot Framework | BuiltIn, Collections, SeleniumLibrary, Browser, RequestsLibrary, RESTinstance, DatabaseLibrary, AppiumLibrary |

Gherkin/BDD (Cucumber.js, behave, pytest-bdd) and Tavern are covered as secondary
semantic passes in [reference.md](reference.md).

Frontend component tests - React, Vue, Angular, Svelte - use the same J1-J6
framework as backend tests. The structural failures are identical: a J4 weak
assertion on a rendered component is the same smell as a J4 on a service
method. See the family-based examples under `examples/typescript/` (for instance
`family_a_never_checks.ts`, which carries the Testing Library patterns) for annotated cases.

### Test levels (the pyramid)

The skill detects the test level and reads the oracle in light of it, the step the static
scanners cannot fully do. The level changes what counts as a valid check:

- **Unit:** a function or component with its boundaries doubled. A real assertion on the
  return value is the oracle.
- **Integration (API and database):** API tests (supertest, `httpx`, a framework TestClient,
  Tavern) and database tests against a real datastore. The response or the row IS the
  verification at this level, so the skill does not flag it as a weak check.
- **E2E:** Cypress, Playwright, Selenium, Robot Browser. The presence of a rendered element
  or a page state is a real check here.

The level itself is part of the judgment: a real API or database call inside a test that
claims to be a unit test is a smell (over-mocking inverted, mystery guest), and the skill
says so rather than accepting the level at face value.

### Patterns by test level and scope

The same false-green shape is classified by the level the test runs at: the level is a
per-finding axis (J3), read as unit, integration, or E2E. As the superset of the three
scanners, the skill covers every level and every language, plus the semantic `S1`-`S18` and `S21`
patterns no parser sees. The clusters at each level:

- **Unit:** always-true and self-compare (`C5`/`C7`/`JS30`), no oracle (`C2`/`C2b`), asserts its own double (`JS8`/`JS27`/`C13b`/`S8`), and the semantic `S1`/`S5` (intent mismatch, tests the framework).
- **Integration:** request oracle off (`C9b`), captured log never asserted (`C50`), patching the edge wrong (`S12`/`S18`).
- **E2E:** sleep as synchronization (`C16`), forced green in Robot (`R1`/`R2`/`R4`/`R6`), and the semantic `S1`/`S2` (intent mismatch, irrelevant oracle).

Full matrix on the docs site: [patterns by test level](https://vinicq.github.io/falsegreen-docs/concepts/by-test-level/) and [what we do not flag](https://vinicq.github.io/falsegreen-docs/concepts/what-we-do-not-flag/).

---

## Project layout

```
falsegreen-skill/
  SKILL.md              the skill protocol (language and LLM agnostic)
  AGENTS.md             Codex + Antigravity CLI rule file (auto-parsed at workspace root)
  GEMINI.md             Antigravity CLI rule file (auto-parsed) + legacy Gemini CLI contextFileName / import source
  llm.md                self-contained prompt context used by CLI/API examples
  reference.md          per-language case catalog and framework cues
  providers.md          multi-LLM invocation guide (API snippets)
  CREDITS.md            the research this skill builds on
  gemini-extension.json legacy Gemini CLI manifest (source for `agy plugin import gemini`)
  .antigravity-plugin/  Antigravity CLI (`agy`) plugin manifest + skill (`agy plugin install`)
  .agents/skills/       Antigravity CLI (`agy`) workspace Agent Skill entry point
  .gemini/              legacy Gemini Agent Skill entry point
  .claude-plugin/       Claude Code plugin manifest + marketplace catalog
  .codex-plugin/        Codex CLI plugin manifest
  .agents/plugins/      Codex CLI marketplace catalog
  skills/
    falsegreen-skill/   shared skill entry point (Claude Code + Codex plugins)
  bin/
    falsegreen-llm.js   zero-dependency CLI (npx falsegreen-skill)
  scripts/
    validate-package.mjs validate manifests, frontmatter, and schema naming
    build-targets.mjs    generate standalone Claude/Gemini skill packages
  docs/
    architecture.md     architecture overview + Mermaid flow diagrams
    cli.md              CLI usage guide
    packaging.md        target packaging and release checklist
  schema/
    finding.json        JSON Schema for a single finding
    report.json         JSON Schema for a full report
  contexts/             ready-to-use context files per platform
    claude.md           Claude Code CLI, Claude.ai, Anthropic API
    codex.md            ChatGPT, OpenAI API, structured output, batch
    gemini.md           Google AI Studio, Gemini API, long context
    cursor.md           Cursor IDE, full .cursor/rules/ MDC template
  examples/
    python/
      family_a_never_checks.py       C1, C2, C2b, C3, C4, C4b, C20, C21, CC
      family_b_weak_always_true.py   C5, C6, C6b, C7, C8, C9, C11a, C13, C13b, C14, C16, C18, C25, C34
      family_c_checks_own_setup.py   C19, C28, C29
      family_d_external_state.py     C17, C23, C24, C27, C30, C31, C32, C35
      family_e_wrong_thing.py        C33, C36, C37
      semantic_cases.py              cases 10, 11, 12, 15, 18 (LLM-only)
      diagnostic_codes.py            D1, D3, D4, D5, D6, M2 (opt-in)
    typescript/
    javascript/
```

---

---

## Setup and usage reference

Everything above is the tour. This section is the complete reference: every
install mode, every CLI flag, every provider, and every host, with copy-paste
blocks. Commands and flags here are taken from `bin/falsegreen-llm.js --help`
and the host manifests, so they match the shipped 0.6.x line.

### 1. Install the CLI

The CLI is a zero-dependency Node script. It needs **Node 18 or newer** (the
`engines` floor in `package.json`; it relies on the built-in `fetch`).

```bash
# run once, no install
npx falsegreen-skill analyze tests/test_payment.py

# install globally, then call `falsegreen-skill` anywhere
npm install -g falsegreen-skill
falsegreen-skill analyze tests/test_payment.py

# pin it as a dev dependency in a repo
npm install -D falsegreen-skill
npx falsegreen-skill analyze tests/test_payment.py
```

`falsegreen-skill --version` prints the installed version; `falsegreen-skill --help`
prints the full command and flag list.

### 2. `analyze` - review test files

```
falsegreen-skill analyze <file...> [options]
```

Each file is sent to the provider in its own request. Plain-text output is
printed under a `=== {filename} ===` header per file. With `--json`, each
response is validated against `schema/report.json` and the CLI emits one
aggregate JSON report.

**Full flag reference** (from `--help`):

| Flag | Meaning | Default |
|---|---|---|
| `--provider <name>` | `anthropic`, `openai`, `gemini`, or `openai-compatible` | `anthropic` |
| `--model <model>` | Override the provider default. Required for `openai-compatible` | per provider (below) |
| `--base-url <url>` | API base URL. Required for `openai-compatible` | none |
| `--json` | Validate and output JSON conforming to `schema/report.json` | off |
| `--conventions <file>` | Conventions YAML/text injected per SKILL.md Step 0 | none |
| `--temperature <n>` | Sampling temperature 0.0-1.0. Omitted automatically for OpenAI o-series | `0.2` |
| `--max-tokens <n>` | Max output tokens per request | `4096` |
| `--fail-on-high` | Exit 2 when any HIGH finding is present. Requires `--json` | off |

Default models per provider: `anthropic` -> `claude-sonnet-5`,
`openai` -> `gpt-5`, `gemini` -> `gemini-2.5-flash`. The `openai-compatible`
provider has no default model, so `--model` and `--base-url` are both required.

**Exit codes:**

| Code | Meaning |
|---|---|
| 0 | Analysis completed (findings may still exist; analyze is not a gate by itself) |
| 1 | Error: missing file, missing API key, bad flag, invalid JSON, schema mismatch, non-2xx API response |
| 2 | `--fail-on-high` was set and the JSON report contains at least one HIGH finding |

**Environment variables** (one per provider, read from the environment):

| Variable | Used by |
|---|---|
| `ANTHROPIC_API_KEY` | `--provider anthropic` |
| `OPENAI_API_KEY` | `--provider openai`, and fallback for `openai-compatible` |
| `GEMINI_API_KEY` | `--provider gemini` |
| `FALSEGREEN_API_KEY` | `--provider openai-compatible` (takes precedence over `OPENAI_API_KEY`) |

#### One example per provider

```bash
# Anthropic (default provider)
export ANTHROPIC_API_KEY=sk-ant-...
falsegreen-skill analyze tests/test_payment.py
falsegreen-skill analyze tests/test_payment.py --model claude-opus-4-8   # deep case 18

# OpenAI
export OPENAI_API_KEY=sk-...
falsegreen-skill analyze tests/test_payment.py --provider openai
falsegreen-skill analyze tests/test_payment.py --provider openai --model o3   # reasoning, temperature auto-omitted

# Google Gemini
export GEMINI_API_KEY=...
falsegreen-skill analyze tests/test_payment.py --provider gemini
```

#### openai-compatible: any provider that speaks the OpenAI Chat API

Set `FALSEGREEN_API_KEY` to the provider key, point `--base-url` at the
`/v1` root, and pass the provider's model id. The CLI appends
`/chat/completions` for you.

```bash
# Groq
export FALSEGREEN_API_KEY=gsk_...
falsegreen-skill analyze tests/test_payment.py \
  --provider openai-compatible \
  --base-url https://api.groq.com/openai/v1 \
  --model llama-3.3-70b-versatile

# Nvidia NIM (OpenAI-compatible endpoint)
export FALSEGREEN_API_KEY=nvapi-...
falsegreen-skill analyze tests/test_payment.py --json \
  --provider openai-compatible \
  --base-url https://integrate.api.nvidia.com/v1 \
  --model qwen/qwen3.5-397b-a17b \
  --max-tokens 8192

# Fireworks
export FALSEGREEN_API_KEY=fw_...
falsegreen-skill analyze tests/test_payment.py --json \
  --provider openai-compatible \
  --base-url https://api.fireworks.ai/inference/v1 \
  --model accounts/fireworks/routers/kimi-k2p6-turbo \
  --max-tokens 8192

# Ollama (local - no key needed, any placeholder works)
export FALSEGREEN_API_KEY=ollama
falsegreen-skill analyze tests/test_payment.py \
  --provider openai-compatible \
  --base-url http://localhost:11434/v1 \
  --model qwen2.5-coder:32b

# Alibaba Qwen (DashScope, OpenAI-compatible mode)
export FALSEGREEN_API_KEY=sk-...
falsegreen-skill analyze tests/test_payment.py \
  --provider openai-compatible \
  --base-url https://dashscope-intl.aliyuncs.com/compatible-mode/v1 \
  --model qwen-plus
```

> **Prompt size vs. free tiers.** The system prompt carries the full catalog
> (`llm.md` + `reference.md`), ~33k tokens. Providers with a small per-minute
> token cap on their free tier (e.g. Groq's 12k TPM) reject the request with
> HTTP 413/429. Use a provider whose free or paid tier allows a ~35k-token
> request (Ollama locally, or a large-context model on OpenRouter/NVIDIA/etc.),
> and raise `--max-tokens` if a reasoning model gets cut off mid-report.

Set `--model` to the id your account actually exposes; the CLI passes the
string through unchanged. Reasoning models work with `--json` as of 0.5.2:
the CLI requests native JSON output, strips `<think>`/`<reasoning>` blocks,
and recovers a slashed-key form (`/findings`) some schema-guided decoders
emit. Verbose reasoners spend their output budget on chain-of-thought and can
get cut off mid-JSON; if that happens the CLI says so and points at
`--max-tokens` - raise it (8192 or higher) and retry.

### 3. `fix` - propose a stronger test and prove it (mutation gate)

```
falsegreen-skill fix <test-file> --case <code> --line <n> [options]
```

`analyze` finds a false-green; `fix` proposes a stronger test and runs a local
gate to prove it before you trust it. It is opt-in, **Python/pytest only**, and
**propose-only**: it prints a test-file patch but never applies it and never
edits production code.

**fix flags** (in addition to the provider flags above):

| Flag | Meaning |
|---|---|
| `--case <code>` | Catalog code of the finding to fix. V1 fixable set: `C2b`, `C20`, `C21`, `C5`, `C7` |
| `--line <n>` | Line of the finding in the test file (1-indexed) |
| `--sut <file>` | Production file the test protects. Required for a validated fix |
| `--sut-line <n>` | Line in the SUT to mutate. Defaults to `--line` |
| `--cheap` | Validation tier: parse + preserve only, no mutation gate |

```bash
# propose a patch for a C2b finding and run the full gate against the real SUT
falsegreen-skill fix tests/test_discount.py --case C2b --line 14 \
  --sut src/discount.py --sut-line 12

# parse + preserve only, no mutation gate (no runnable SUT, or a quick pass)
falsegreen-skill fix tests/test_discount.py --case C5 --line 9 --cheap

# machine-readable gate verdict (schema/fix-validation.json)
falsegreen-skill fix tests/test_discount.py --case C20 --line 22 \
  --sut src/discount.py --json
```

**What the gate proves.** On a clean replica it runs three checks: the patch
parses (`py_compile`), it passes `pytest` against the real code (preserve), and
it **fails** on a line-scoped mutation of the SUT (a built-in operator flipped
on the SUT line). A patch is **accepted** only when it passes on correct code
AND goes red on the mutant, which is what shows the new assertion catches a bug
instead of being a fresh tautology. The exit code is 0 on accept, 1 on
reject/unvalidated, so CI can branch on it.

**The honest limit.** Without `--sut` (or with `--cheap`) the gate degrades to
propose-only and labels the fix unvalidated. Even with the gate, it proves the
fix catches the targeted mutant, not every possible bug; full mutmut
integration and the deep semantic cases (10/11/12/18) and JS/TS/Robot fix
paths are deferred to a later version.

### 4. `generate` - author a test from a spec (Mode B)

```
falsegreen-skill generate <spec-file> [--lang <language>] [options]
```

Renders a language-neutral test-spec into a real test, then runs `analyze`
(Mode A) on the result, so a false-green test cannot pass the self-check
undetected. It catches false-green *shapes*; it does not, and cannot on its own,
tell a hand-written wrong oracle from a right one (see the honest limit below).
The spec is a [`schema/test-spec.json`](schema/test-spec.json) file (YAML or
JSON); see [`examples/authoring/`](examples/authoring/) for one spec rendered
into all four stacks. If `--lang` is omitted, the spec's first declared
`languages` entry is used, else Python.

**generate flags** (in addition to the provider flags above):

| Flag | Meaning |
|---|---|
| `--lang <language>` | Target stack: `python`, `typescript`, `javascript`, `tsx`, `jsx`, `robot`. `tsx`/`jsx` cover the React side of the JS/TS family (same JS* catalog). One language per run |

```bash
# render the example spec to a Python test and self-check it
falsegreen-skill generate examples/authoring/apply-discount.spec.yaml --lang python

# same spec, TypeScript; the spec is the single source, re-run per stack
falsegreen-skill generate examples/authoring/apply-discount.spec.yaml --lang typescript

# machine-readable: { language, test, self_check, self_check_passed, self_check_error }
falsegreen-skill generate my-spec.yaml --lang python --json
```

**The oracle is mandatory.** A spec with no `oracle.expected` key is refused
before any API call: a test generated from the code's current output only freezes
the bug (a characterization test). The oracle's *value* is not checked; that is
your responsibility. What the command proves is narrower: the generated test
trips no HIGH false-green finding when Mode A reviews it.

**The self-check is bounded and fails closed.** After generating, the CLI runs
Mode A on the test once, and if it trips a HIGH false-green finding, revises once
and re-checks. The exit code is the CI contract:

| Exit | Meaning |
|---|---|
| 0 | PASSED: the self-check ran and found no HIGH false-green |
| 1 | FAILED: a surviving false-green was confirmed (also used for a bad spec or an API error) |
| 3 | UNVERIFIED: the self-check could not run (small model, provider error). The test is still printed, but it is **not** accepted, so a pipeline never treats an unchecked test as clean |

The self-check is a same-model static review, not an execution: it does not run
the test, confirm it compiles or imports, or verify the oracle value. A
characterization test with a code-derived expected can still pass. Review the
output against your spec.

### 5. Host setup

Each host enables the same J1-J6 protocol; the wiring differs. Steps below come
straight from the manifests (`.claude-plugin/plugin.json`,
`.codex-plugin/plugin.json`, `gemini-extension.json`) and the `contexts/` guides.

#### Claude Code

Add the marketplace, then install the plugin:

```
/plugin marketplace add vinicq/falsegreen-skill
/plugin install falsegreen-skill@falsegreen
```

After install the skill is the namespaced command
`/falsegreen-skill:falsegreen-skill`, and it also triggers on natural-language
intent ("analyze this test for false-positive smells"). Claude Code discovers
test files with its own Glob/Read tools, so you can point it at a directory.
Full guide: [`contexts/claude.md`](contexts/claude.md).

#### OpenAI Codex CLI

Codex has no single-command install for this repo. Clone it and start Codex for
the full protocol - `AGENTS.md` at the root auto-loads as project context and
every relative reference resolves:

```bash
git clone https://github.com/vinicq/falsegreen-skill
cd falsegreen-skill
codex
```

The protocol is scoped to that directory. To run it in your own project instead,
copy `AGENTS.md` into your project (or `~/.codex/AGENTS.md` to load it
everywhere); that gives the compact routine protocol, and for deep look-alike
checks you also bring `reference.md`/`SKILL.md` or work from the clone.

The plugin manifest is `.codex-plugin/plugin.json`, the marketplace catalog
`.agents/plugins/marketplace.json`, the shared skill
`skills/falsegreen-skill/SKILL.md`. Codex has plugin subcommands, but this
repo-is-the-plugin catalog uses a repo-root source that Codex's marketplace
resolver does not accept, so the two paths above are the supported ones (details
in [`contexts/codex.md`](contexts/codex.md)). Codex has a ~32 KiB context
budget; load `AGENTS.md` eagerly (it carries the compact protocol) and pull
`reference.md` or `SKILL.md` on demand. Full guide:
[`contexts/codex.md`](contexts/codex.md).

#### Antigravity CLI (`agy`)

Antigravity is Google's successor to the discontinued Gemini CLI. There are
three ways to enable it.

Install it as a plugin (the `.antigravity-plugin/` bundle stages into
`~/.gemini/antigravity-cli/plugins/`):

```bash
agy plugin install https://github.com/vinicq/falsegreen-skill
```

Or run `agy` inside the repo with no install: it discovers the workspace Agent
Skill at `.agents/skills/falsegreen-skill/SKILL.md` and parses `AGENTS.md` /
`GEMINI.md` at the root as codebase rule files on startup. Either way the skill
is the `/falsegreen-skill` slash command; invoke it or ask in natural language,
for example "analyze tests/ for false-positive smells".

For a self-contained plugin (no repo checkout), run `npm run build:targets` and
install `dist/antigravity-plugin/`. If you still have the old Gemini CLI
extension installed, migrate it with `agy plugin import gemini`, which converts
the legacy `gemini-extension.json` + `GEMINI.md` plugin. Full guide:
[`contexts/gemini.md`](contexts/gemini.md).

#### Cursor

Cursor has no plugin install; it loads project rules. Copy the full MDC
template from [`contexts/cursor.md`](contexts/cursor.md) into
`.cursor/rules/falsegreen-skill.mdc`:

```
.cursor/
  rules/
    falsegreen-skill.mdc
```

The frontmatter globs (`**/test_*.py`, `**/*.test.ts`, `**/*.spec.tsx`,
`**/*.robot`, ...) activate the rule when you open a matching test file. Then
in Cursor Chat ask "analyze this file for false-positive test smells using
falsegreen-skill". `@file` mentions and Composer batch runs work the same way.

#### Plain LLM / raw API

No host needed: paste `SKILL.md` as the system prompt (or first message for
reasoning models that reject a system role) and the test file as the user
message. The full per-language catalog lives in `reference.md` - append it when
you need the JS/Robot codes or the look-alike exemptions, since `SKILL.md`
inlines only the Python catalog. Per-provider SDK snippets (Anthropic, OpenAI,
Gemini, Groq, Qwen via OpenRouter, Kimi) and the case 18 two-pass finder/refuter
procedure are in [`providers.md`](providers.md).

### 5. Configuration

**Conventions file (Step 0).** Declare project-specific context - custom
assertion helpers, layer overrides, excluded codes - so the skill folds them in
before judging. Pass it with `--conventions <file>`:

```yaml
conventions:
  custom_assertion_helpers:
    - conftest.assert_model_valid()
  test_layer_overrides:
    - tests/integration/ is web-layer   # apply the C6 HTTP exemption here
  excluded_codes:
    - C8                                 # project uses Decimal, not float
```

The block extends the look-alike exemptions only; it cannot disable severity.
HIGH findings that survive the exemptions stay HIGH.

**Model selection.** The CLI ships its own defaults (above). The canonical
tier-to-model map for reference and host docs is [`models.yaml`](models.yaml):
the `structural` tier (C-codes, small models fine), the `semantic` tier
(cases 10-15, frontier or 70B+), and the `adversarial` tier (case 18, frontier
with extended reasoning). Nothing loads `models.yaml` at runtime - it keeps the
CLI zero-dependency - so it is documentation, validated against providers before
each release.

**Output schema (J1-J6).** JSON output is governed by two canonical schemas:
[`schema/report.json`](schema/report.json) (the report: `findings`, `summary`,
`language`, `framework`, optional `scan_date`) and
[`schema/finding.json`](schema/finding.json) (each finding: `case`, `judgment`
one of J1-J6, `confidence` HIGH/LOW, `language`, `level` unit/integration/e2e,
`intent`, `test`, `finding`, `evidence`, optional `oracle`, `fix_hint`). The
`oracle` field is required only for semantic case 18. The CLI validates every
`--json` response against these and exits 1 on a mismatch.

**Where the catalog lives.** [`reference.md`](reference.md) is the per-language
case catalog with examples and look-alike exemptions; the structural code list
the scanners share is also mirrored there. The CLI's own prompt is built from
`llm.md` plus `reference.md` at runtime.

### 6. Relationship to the static scanners

This skill is a **superset** of the three static scanners. Each scanner proves
what a parser can see, fast and deterministic, with no API key:
[falsegreen](https://github.com/vinicq/falsegreen) (Python),
[falsegreen-js](https://github.com/vinicq/falsegreen-js) (JS/TS),
[robotframework-falsegreen](https://github.com/vinicq/robotframework-falsegreen)
(Robot). The skill carries every structural code those scanners emit **plus**
the AI-only semantic cases (mock-the-SUT, echo mocks, formula re-implementation,
spec contradictions) that no parser reaches. A common setup runs a scanner on
every commit and the skill on the files the scanner cannot fully judge; for
Python you can also paste the scanner output to the skill so it skips the
structural pass and goes straight to semantic adjudication.

Full catalog, judgments, and per-language reference:
[docs site](https://vinicq.github.io/falsegreen-docs/) and
[reference.md](reference.md).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). The main contribution paths are
language-specific patterns and look-alike examples in `reference.md`.

License: **MIT**, see [LICENSE](LICENSE).

## Contributors ✨

Thanks to the people who keep false-green tests out of real suites ([emoji key](https://allcontributors.org/docs/en/emoji-key)):

<!-- ALL-CONTRIBUTORS-BADGE:START - Do not remove or modify this section -->
[![All Contributors](https://img.shields.io/badge/all_contributors-2-orange.svg?style=flat-square)](#contributors-)
<!-- ALL-CONTRIBUTORS-BADGE:END -->

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tbody>
    <tr>
      <td align="center" valign="top" width="14.28%"><a href="https://vinicq.github.io/md-bridge/"><img src="https://avatars.githubusercontent.com/u/78210890?v=4?s=100" width="100px;" alt="Vinicius Queiroz"/><br /><sub><b>Vinicius Queiroz</b></sub></a><br /><a href="https://github.com/vinicq/falsegreen-skill/commits?author=vinicq" title="Code">💻</a> <a href="https://github.com/vinicq/falsegreen-skill/commits?author=vinicq" title="Documentation">📖</a> <a href="#ideas-vinicq" title="Ideas, Planning, & Feedback">🤔</a> <a href="#maintenance-vinicq" title="Maintenance">🚧</a> <a href="#infra-vinicq" title="Infrastructure (Hosting, Build-Tools, etc)">🚇</a> <a href="https://github.com/vinicq/falsegreen-skill/commits?author=vinicq" title="Tests">⚠️</a> <a href="#research-vinicq" title="Research">🔬</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/homesellerq-coder"><img src="https://avatars.githubusercontent.com/u/294912019?v=4?s=100" width="100px;" alt="Home Seller"/><br /><sub><b>Home Seller</b></sub></a><br /><a href="https://github.com/vinicq/falsegreen-skill/commits?author=homesellerq-coder" title="Code">💻</a> <a href="https://github.com/vinicq/falsegreen-skill/commits?author=homesellerq-coder" title="Documentation">📖</a> <a href="https://github.com/vinicq/falsegreen-skill/commits?author=homesellerq-coder" title="Tests">⚠️</a> <a href="#infra-homesellerq-coder" title="Infrastructure (Hosting, Build-Tools, etc)">🚇</a></td>
    </tr>
  </tbody>
</table>

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

<!-- ALL-CONTRIBUTORS-LIST:END -->

New contributors are added automatically; the table also recognizes non-code work (docs, ideas, infrastructure, tests, research) via the [all-contributors](https://allcontributors.org) spec.
