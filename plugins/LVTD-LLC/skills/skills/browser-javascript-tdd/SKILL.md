---
name: browser-javascript-tdd
description: "Test-drive browser JavaScript behavior with DOM fixtures, test runners, smoke tests, onload timing, selector refactors, and integration tradeoffs with Selenium or end-to-end tests. Use when adding client-side behavior, debugging DOM tests, choosing between JS unit tests and browser functional tests, or making JavaScript testable without overusing Selenium."
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Browser JavaScript TDD
  category: Testing
  tags: javascript,tdd,testing,browser,frontend
---

# Browser JavaScript TDD

Use this skill when browser-side behavior needs fast feedback before or alongside end-to-end tests. Keep JavaScript unit tests focused on DOM behavior and use broader browser tests only for integration confidence.

## Source Traceability

Primary source: Harry Percival, *Test-Driven Development with Python*, 3rd ed. Guidance is transformed and paraphrased from chapters 17, 25, and Appendix B, especially browser-based Jasmine tests, DOM fixtures, onload timing, selector refactoring, and JavaScript CI integration.

## Workflow

1. Start with the user-visible browser behavior.
   - Decide what the JavaScript owns: DOM update, class toggle, client-side validation, enhancement, or integration hook.
   - Keep server-owned state out of client unit tests.

2. Choose the test boundary.
   - Use JavaScript unit tests for pure functions and DOM manipulation.
   - Use one end-to-end test when Django/server, CSS, and browser wiring must be proven together.
   - Do not use Selenium to exhaustively test JavaScript branches.

3. Build a stable DOM fixture.
   - Include only the markup required by the behavior.
   - Reset global state between tests.
   - Make initialization explicit instead of relying on incidental page load order.

4. Red/green/refactor the JavaScript.
   - First smoke-test the runner.
   - Add a failing DOM behavior test.
   - Implement minimal code.
   - Refactor selectors and initialization while tests are green.

Read [browser-js-patterns.md](references/browser-js-patterns.md) for DOM fixtures, initialization, and CI patterns.

## Decision Rules

- If the behavior is DOM-local, prefer JavaScript tests.
- If the risk is server-client integration, keep a small browser functional test.
- If the code depends on page load timing, expose an initialization function and test it directly.
- If selectors are duplicated across tests and code, introduce named selectors or data attributes deliberately.
- If the test needs CSS behavior, decide whether style is truly the contract or only incidental.

## Guardrails

- Do not let global DOM or event listeners leak between tests.
- Do not test third-party framework behavior.
- Do not hide asynchronous timing with sleeps.
- Do not make JS unit tests pass while the real page never calls the code.

## Verification

Before finishing, record:

- Test runner command and result.
- DOM fixture or setup reset strategy.
- Integration check when the real page wiring changed.
- CI step or artifact change when browser JS tests were added to the pipeline.
