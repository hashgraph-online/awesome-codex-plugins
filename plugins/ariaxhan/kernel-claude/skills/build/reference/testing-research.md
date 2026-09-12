# Testing Reference: Research & Best Practices

Reference for test strategy, AI-generated test pitfalls, and verification methodology.
Read on demand. Not auto-loaded.

## Sources

CodeRabbit State of AI Code Generation (2025), Qodo State of AI Code Quality (2025),
Parasoft AI testing research (2025), foojay.io AI-driven testing best practices,
World Quality Report 2025-26, DORA Impact of Generative AI (2025), Microsoft QA
engineering prompting guide (2026), Medium/HackerNoon AI test quality analyses,
Meta JiT Testing (Feb 11, 2026), Qodo 2.0 (Feb 4, 2026), State of Testing 2026
(PractiTest Feb 2026), Test Pyramid 2.0 (Frontiers in AI), arXiv 2602.07900
Agent Test Generation (Feb 2026).

---

## The AI Testing Crisis

AI generates tests that look correct but verify nothing meaningful.

Qodo: only 27% of developers not using AI for tests are confident in their suite.
With AI testing, confidence jumps to 61%, but this confidence is often misplaced.

Parasoft (2025): over 50% of AI-generated code samples contain logical or security
flaws even when code "looks correct on the surface."

IBM study: developers tossed 70% of AI-generated tests because they felt "robotic"
with no flow, no intent, no design thinking.

World Quality Report 2025-26: 50% of QA leaders cite "maintenance burden and flaky
scripts" as top challenge with AI test automation.

The core problem: AI generates tests from code, not from requirements. It tests
what the code DOES, not what it SHOULD do. If the code has a bug, the test
validates the bug.

---

## Just-in-Time (JiT) Testing (Meta, Feb 2026)

A fundamentally new approach from Meta:
- Tests generated on-the-fly by LLMs before code lands in production.
- No maintenance required (tests don't persist in codebase).
- Mutation-based: introduces deliberate faults, generates tests to catch them.
- Addresses "agentic development dramatically increases pace of code change."

---

## Test Writing Paradox (arXiv Feb 2026)

Striking finding from arXiv 2602.07900:
- Claude Opus 4.5 writes tests in 83% of tasks (74.4% resolution)
- GPT-5.2 writes tests in 0.6% of tasks (71.8% resolution)
- Only 2.6 percentage point difference in success rate

Test volume does NOT correlate with task success.
"Value-revealing prints consistently outnumber assertions across all models."

---

## The 8 AI Test Anti-Patterns

### 1. Happy Path Only
AI tests the basic success case. Nulls, errors, boundaries, concurrent access
are ignored unless explicitly requested.
Fix: for every test, ask "what's the sad path?" Test failure modes first.

### 2. Weak Assertions
assertNotNull(result) proves the result exists, not that it's correct.
assertTrue(true) is literally useless. assertEquals on the wrong field.
Fix: assert specific values, specific fields, specific state changes.
"What would this assertion catch if the code were wrong?"

### 3. Mock Overuse
AI generates verbose mocks that lock onto implementation details. When you
refactor internals, tests break even though behavior is unchanged.
Studies: LLMs botch mocks 25% of the time, creating integration-test-shaped
unit tests that hit live endpoints or depend on execution order.
Fix: mock at boundaries (external services, databases), not internal functions.
Test behavior at the public interface, not implementation details.

### 4. Implementation Testing (Not Behavior Testing)
AI tests that function X calls function Y with parameter Z. This tests HOW
the code works, not WHAT it does. Any refactor breaks the test.
Fix: test inputs and outputs at the public API boundary. "Given this input,
I expect this output." Implementation is free to change.

### 5. Hallucinated API Calls
AI generates tests referencing functions, methods, or endpoints that don't
exist. The test fails on import/compile, not on logic.
Fix: run every generated test immediately. If it doesn't compile, discard it.

### 6. Outdated Patterns
AI defaults to older framework versions. Appium 2 syntax when Appium 3 is
current. Old Jest patterns. Deprecated assertion libraries.
Fix: specify framework version in test generation prompts. Review imports.

### 7. Flaky Async Tests
AI generates timing-dependent tests for async code. Sometimes pass, sometimes
fail. Thread races, unresolved promises, missing awaits.
Fix: use deterministic async patterns (await, test utilities like waitFor).
Never rely on setTimeout or sleep in tests.

### 8. Missing Edge Cases
AI's biggest blind spot. It doesn't test: empty strings, zero-length arrays,
MAX_INT, negative numbers, unicode, concurrent access, timeout scenarios,
malformed input, missing required fields.
Fix: explicit edge case list for every function. Minimum 3 edge cases per test.

### 9. Print-Over-Assert (NEW 2026)
Agents default to print statements over formal assertions. Only 35-43% are
exact-value checks. Relational/range constraints in single digits.
Fix: Require formal assertions. Suppressing tests reduced tokens 49% with
only 2.6% success drop - focus on quality over quantity.

---

## The Test Pyramid (Still Valid, Despite AI)

Unit tests: fast, isolated, test one function. Bulk of your suite.
Integration tests: test boundaries between components. Database queries,
API calls, service interactions.
E2E tests: test critical user flows. Expensive, slow, few of these.

AI tends to generate unit tests that are actually integration tests (because
they don't mock properly) and E2E tests that are actually smoke tests (because
they only check happy path). Enforce the pyramid consciously.

---

## What to Test (Priority Order)

1. Business logic: the core rules that define correct behavior.
2. Error handling: what happens when things go wrong.
3. Boundary conditions: edges of valid input ranges.
4. State transitions: from one state to another (auth, workflows).
5. Integration points: where your code meets external systems.
6. Regression cases: every bug fix gets a test that would have caught it.

What NOT to test (waste of tokens):
- Getters/setters with no logic
- Framework internals (React renders, Express routing)
- Third-party library behavior (that's their job)
- Implementation details that may change

---

## Test Naming Convention

test_{function}_{scenario}_{expected_result}

Examples:
- test_calculateTax_negativeIncome_returnsZero
- test_fetchUser_invalidId_throws404
- test_parseDate_emptyString_returnsNull

The name IS the specification. If you can't name it clearly, you don't
understand what you're testing.

---

## KERNEL Integration

- Adversary agent: uses this reference to evaluate surgeon's tests.
  "Are assertions specific? Are edge cases covered? Are mocks appropriate?"
- Validator agent: runs test suite as pre-commit gate. No exceptions.
- Surgeon agent: writes tests alongside implementation. Never after.
  Bug fixes MUST include regression test. Feature code MUST include
  at least happy path + 3 edge cases.
- Every test must be independently runnable. No order dependence.
- **2026 Context Priority**: Context gaps cited MORE OFTEN than hallucinations
  (65% vs lower). Missing context is the root cause; hallucinations are symptom.
- **Self-healing tests**: 95% maintenance reduction claimed, but caution:
  may mask genuine product bugs. Use with transparent logging.

---

## Naming Convention — Extended (from SKILL.md 2026-04-27)

Source: https://medium.com/ngconf/create-reliable-unit-tests-with-claude-code-9147d050d557

BDD format: GIVEN/WHEN/SHOULD. Reads as specification, not code description.

```javascript
// POOR: describes implementation
test('validateEmail regex check')

// GOOD: describes behavior
test('GIVEN an email without domain WHEN validated SHOULD return false')
test('GIVEN a valid email WHEN validated SHOULD return true')
```

If a test name can't be written in GIVEN/WHEN/SHOULD form, the test is ambiguous.
`describe()` should be the subject; `it()`/`test()` should be the scenario.

**"Don't modify the tests" instruction**: When asking Claude to fix failing tests, include
"Do not modify the tests — fix the implementation to pass them." Without this, Claude takes
the fastest path to green: weakening assertions or skipping edge cases rather than fixing the bug.

---

## Behavior vs. Implementation — Code Examples (from SKILL.md 2026-04-23)

Source: https://code.claude.com/docs/en/best-practices, https://www.tech-reader.blog/2026/04/the-secret-life-of-claude-code-testing.html

```javascript
// POOR: Tests implementation (breaks on refactor)
test('validateEmail uses regex pattern', () => {
  expect(validateEmail).toHaveBeenCalledWith(expect.stringMatching(/\w+@\w+/));
});

// GOOD: Tests behavior (survives refactor)
test('validateEmail rejects invalid formats', () => {
  expect(validateEmail('user@.com')).toBe(false);
  expect(validateEmail('user@example.com')).toBe(true);
  expect(validateEmail('invalid')).toBe(false);
});
```

---

## Edge Case Discovery — Prompting Patterns (from SKILL.md 2026-04-23)

Source: https://code.claude.com/docs/en/best-practices (QA automation section)

Claude's testing strength is edge case discovery, not boilerplate unit tests.
Prompt explicitly for edge cases rather than asking for generic coverage.

Effective prompt structure:
1. "What edge cases exist for [function]?"
2. Show 2–3 expected edge cases to anchor thinking.
3. "What boundary conditions or interaction effects might break this?"
4. "Generate N test cases covering these scenarios."

Example for validateEmail:
```
"Write tests covering:
- Invalid formats (missing @, missing domain, invalid chars)
- Boundary cases (empty string, very long email, null/undefined)
- Interaction effects (uppercase, spaces, international domains)
- Security cases (SQL injection payloads, newline injection)
Generate 15 cases that would catch a developer who forgot one category."
```

---

## Negative Case Testing (from SKILL.md 2026-05-06)

Source: https://medium.com/@karkeralathesh/the-complete-guide-to-testing-claude-code-skills-with-the-skill-creator-1ae3821bd7b8

Test what code should NOT do. In AI-assisted development, positive-case tests dominate and
negative-case behavior is routinely untested.

Negative cases to add to every test suite:
- Rejection of out-of-scope inputs (tool/function declines gracefully, not crashes)
- Invalid type/shape returns an error, not a corrupted result
- Empty/null/undefined handled at boundary, not propagated
- Security inputs (injection payloads, oversized strings) rejected at entry, not silently processed

**The rejection quality test**: A function that correctly declines invalid input is more
production-grade than one that accepts everything. Test this explicitly.

---

## Browser Verification (from SKILL.md 2026-05-12)

Source: https://code.claude.com/docs/en/best-practices, https://testdino.com/blog/claude-code-with-playwright/

Use browser automation (Playwright + MCP browser tools) to verify UI features before declaring done.
Claude runs the browser, sees console errors, iterates until the feature works end-to-end.
Not a substitute for unit tests — complements them by catching integration failures unit tests can't.

Effective sequence: unit tests (fast feedback) → integration tests (component boundaries) →
browser automation (real user path). Browser tests are slow — reserve for critical user-visible flows only.

---

## Native Code Review Stats — Anthropic (from SKILL.md 2026-05-14)

Source: https://www.infoq.com/news/2026/04/claude-code-review/, https://www.coderabbit.ai/blog/claude-opus-4-7-for-ai-code-review

Anthropic's Code Review feature (launched March 2026) integrates with GitHub and leaves inline
comments automatically on PRs.

Production stats:
- Large PRs (>1000 lines): 84% get findings, avg 7.5 issues flagged
- Small PRs (<50 lines): 31% get findings, avg 0.5 issues
- Average review time: ~20 minutes. Average cost: $15–25/review (token-based)
- Focus: logical errors over style. Opus 4.7 has stronger cross-file reasoning for multi-module issues.

Best ROI: large PRs where human reviewers are most likely to miss cross-file interactions.
Use small PRs strategically to reduce both review time and cost.

---

## Golden Ratio Principle — Coverage Diminishing Returns (from SKILL.md 2026-03-30)

Source: https://code.claude.com/docs/en/best-practices, AI code review research

Test coverage follows diminishing returns past ~80%. Beyond that, invest in:
- Mutation testing (verify your tests actually catch real mutations)
- Property-based testing for complex logic (fast-check, hypothesis)
- Contract tests at service boundaries (Pact, schema mocks)

Coverage % is a vanity metric without mutation score.

---

## Pre-Generation Test Descriptions (from SKILL.md 2026-04-10)

Source: https://code.claude.com/docs/en/best-practices, https://utofa.com/blogs/ai-code-review-2026-best-practices/

When asking Claude to generate code, provide at minimum the test case descriptions (inputs and
expected outputs) BEFORE requesting implementation. This forces behavioral specification first
and prevents tautological tests that just validate what the code does rather than what it should do.

Example:
> "Write validateEmail. Test cases: user@example.com → true, invalid → false, user@.com → false.
> Write the tests first, then implement the function to pass them."

**40-70% of production code is now AI-generated** (industry estimate, 2026). The proportion
of tautological tests in codebases is rising proportionally. Manual review of AI-generated
tests for behavioral correctness is non-optional.

---

## Intent Drift — Verification Checklist (from SKILL.md 2026-05-17)

Source: https://www.kluster.ai/blog/best-code-review-practices, https://brightsec.com/blog/ai-code-review-best-practices-2-0-2026-toolchain/

In 2026 codebases where 40–70% of production code is AI-generated, the failure mode is
**intent drift**: AI correctly implements what it inferred from the prompt, not what the
developer actually needed.

When reviewing AI-generated tests or code, verify against the ORIGINAL intent:
- What prompt or spec drove this generation?
- Does the output match the business requirement, not just the code structure?
- Are edge cases from the spec covered, or only edges visible in the code?

Practical check: read the generation prompt (or ask the author for it), then read the output.
Discrepancies between intent and output are specification bugs, not implementation bugs —
fix the spec before the test.