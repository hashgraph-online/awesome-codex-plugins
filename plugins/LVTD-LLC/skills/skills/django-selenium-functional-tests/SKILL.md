---
name: django-selenium-functional-tests
description: "Design, debug, and maintain Django Selenium functional tests with live server setup, explicit waits, test isolation, page objects, screenshots, CI artifacts, and staging checks. Use when browser tests are flaky, too slow, duplicated, failing in CI, need a page pattern, or should verify a Django user journey end to end."
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Django Selenium Functional Tests
  category: Django
  tags: django,tdd,selenium,functional-tests,testing,browser
---

# Django Selenium Functional Tests

Use Selenium functional tests sparingly and deliberately: they prove that Django, templates, static assets, JavaScript, persistence, and browser behavior work together. Keep them user-facing, isolated, and stable enough to inspire confidence.

## Source Traceability

Primary source: Harry Percival, *Test-Driven Development with Python*, 3rd ed. Guidance is transformed and paraphrased from chapters 1, 2, 4, 6, 13, 22, 23, 25, 26, and Appendix A, especially explicit waits, functional test isolation, page pattern, screenshots, and CI debugging.

## Workflow

1. State the user journey in comments or helper names.
   - Keep test language at the user behavior level.
   - Avoid asserting implementation details unless the browser contract requires them.

2. Use the right server boundary.
   - Use `StaticLiveServerTestCase` when static files matter.
   - Use a staging URL or Docker URL when verifying deployed/container behavior.
   - Keep local and remote setup explicit.

3. Remove timing guesses.
   - Prefer explicit waits for a visible condition, DOM change, URL, or text.
   - Avoid `time.sleep()` except as a temporary debugging probe that is removed.

4. Isolate state.
   - Create per-test data through app APIs, fixtures, management commands, or direct setup helpers.
   - Avoid tests depending on order, prior browser state, or shared accounts.

5. Factor repeated journeys.
   - Start with helper methods.
   - Move to a page pattern when selectors and workflows are repeated enough to obscure intent.

Read [selenium-patterns.md](references/selenium-patterns.md) for wait helpers, page pattern guidance, and CI debugging tactics.

## Debugging Order

1. Reproduce locally with the same browser/headless setting when possible.
2. Capture the current URL, page source, browser logs, and screenshot.
3. Decide whether the failure is timing, selector drift, server error, static asset issue, or data isolation.
4. Add the smallest stable wait or assertion that matches the real condition.
5. Run the single functional test, then the affected functional test file.

## Guardrails

- Do not make Selenium prove every validation branch; faster Django tests should carry detail.
- Do not hide browser failures behind broad retry loops.
- Do not share mutable test accounts across parallel or CI runs.
- Do not assert brittle CSS layout unless layout is the behavior under test.
- Keep screenshots and artifacts for CI failures when they materially reduce diagnosis time.

## Verification

Before finishing, confirm:

- The test names and helpers describe user behavior.
- All waits observe a real condition.
- The test can run alone.
- CI/headless-specific behavior is handled or documented.
- Focused command and result are recorded.
