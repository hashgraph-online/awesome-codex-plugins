---
name: python-mock-isolation-design
description: "Use Python mocks and fakes as a design tool without losing behavioral confidence. Use when testing external dependencies, choosing monkeypatch versus unittest.mock.patch, isolating slow boundaries, avoiding mock-heavy tests, interpreting mock call assertions, or refactoring toward clearer dependency seams."
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Python Mock Isolation Design
  category: Testing
  tags: python,tdd,testing,mocking,architecture
---

# Python Mock Isolation Design

Use this skill when replacing a dependency in a Python test changes what the test proves. Mocks are useful at slow, nondeterministic, or external boundaries; they become harmful when they replace the behavior the test is supposed to validate.

## Source Traceability

Primary source: Harry Percival, *Test-Driven Development with Python*, 3rd ed. Guidance is transformed and paraphrased from chapters 20, 21, 27, and Appendix A, especially manual monkeypatching, `unittest.mock.patch`, mock coupling, call argument inspection, test isolation, and the architectural route out of mock-heavy suites.

## Workflow

1. Name the boundary.
   - External service, email, clock, filesystem, network, framework adapter, or expensive side effect.
   - If the dependency is local domain logic, prefer real code.

2. Choose the replacement.
   - Use a fake when state and behavior are simple and meaningful.
   - Use `patch` when replacing a collaborator looked up by the module under test.
   - Use monkeypatching sparingly and restore state automatically.
   - Use autospec/spec when interface drift matters.

3. Keep behavior assertions primary.
   - Assert user-visible or domain-visible outcomes first.
   - Assert mock calls only when the interaction is the contract.
   - Inspect call arguments when they clarify the behavior, not as a substitute for it.

4. Watch for design feedback.
   - If setup requires many mocks, the code may have hidden dependencies.
   - If tests break on harmless refactors, the test is too coupled to implementation.
   - Consider introducing a boundary interface, service object, or functional core.

Read [mock-isolation-patterns.md](references/mock-isolation-patterns.md) for replacement choices and smell handling.

## Decision Rules

- Patch where the code under test looks up the dependency.
- Prefer fakes for small stable protocols.
- Use `mock.return_value` and `side_effect` deliberately; do not let default mocks create imaginary object graphs.
- Avoid broad `MagicMock` objects without specs for important interfaces.
- Keep at least one integration or contract test for each important boundary.

## Guardrails

- Do not mock Django settings, HTTP, time, or command output by hand if a framework helper exists; use `django-targeted-mocking` for Django-specific boundaries.
- Do not assert only that a mocked method was called unless that call is the behavior.
- Do not use mocks as the primary strategy for making all tests fast; architecture should carry that work.
- Do not keep mocks that prevent refactoring from changing implementation safely.

## Verification

Before finishing, record:

- Boundary being replaced and why.
- Fake, patch, or real dependency choice.
- Behavior assertion that proves the outcome.
- Mock interaction assertion only when interaction is the contract.
- Integration/contract coverage for the real boundary.
