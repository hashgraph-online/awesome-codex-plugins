---
name: django-outside-in-tdd
description: "Drive Django features with outside-in and double-loop TDD: user story, Selenium or functional test, focused Django unit/integration tests, minimal implementation, and refactor. Use when starting or changing Django behavior with tests-first workflow, red/green/refactor, working-state-to-working-state refactors, or deciding which layer should own the next test."
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Django Outside-In TDD
  category: Django
  tags: django,tdd,testing,functional-tests,unit-tests
---

# Django Outside-In TDD

Use this skill when a Django feature should be grown from observable user behavior down into views, forms, models, and helpers. Keep the outer test broad enough to prove user value and the inner tests small enough to keep the red/green loop fast.

## Source Traceability

Primary source: Harry Percival, *Test-Driven Development with Python*, 3rd ed. Guidance is transformed and paraphrased from chapters 1-7, chapter 24, and Appendix A, especially the user-story-to-functional-test flow, double-loop TDD, working-state-to-working-state refactoring, and outside-in development.

## Workflow

1. Start from the user-visible behavior.
   - Write a short user story or acceptance note.
   - Choose one functional test only when the behavior crosses browser, routing, template, persistence, or integration boundaries.

2. Run the outer test and make the failure useful.
   - Confirm the failure is expected and points to the next missing behavior.
   - Improve failure messages before implementation if the failure is vague.

3. Drop into the inner loop.
   - Add the smallest Django test for the next missing component: URL, view, template context, form, model, or helper.
   - Use Django's test client, `RequestFactory`, form instances, or model tests at the narrowest useful boundary.

4. Make the inner test pass with minimal code.
   - Avoid speculative data models, URLs, fields, and abstractions.
   - Keep a scratchpad of next ideas instead of implementing them early.

5. Refactor only on green.
   - Refactor production code first, then test code.
   - Preserve behavior through the existing tests.
   - Return to the outer test to choose the next slice.

Read [patterns.md](references/patterns.md) for layer choices, refactoring rules, and failure-handling patterns.

## Layer Choice

| Signal | Next Test |
| --- | --- |
| User workflow not proven | Functional test |
| URL or redirect missing | URL/view test |
| Template output changed | View/template integration test or HTML parser assertion |
| Validation rule unclear | Form or model test |
| Domain helper emerging | Plain Python unit test |
| Refactor crosses wiring | One integration test plus focused unit tests |

## Guardrails

- Do not write production code before a failing proof unless the task is pure cleanup.
- Do not keep adding Selenium coverage for every branch; promote detailed cases to faster tests.
- Do not test constants or implementation details unless they are the public contract.
- Prefer working state to working state over large rewrites.
- Use existing green tests as a refactoring safety net before changing structure.

## Verification

Before finishing, report:

- Outer behavior covered or intentionally not needed.
- Inner tests added, updated, or reused.
- Red failure or characterization observed before implementation when behavior changed.
- Focused Django test command and result.
- Any deliberate no-test exception with replacement verification.
