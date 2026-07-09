---
name: test-architecture-strategy
description: "Design a sustainable test architecture using test desiderata, test pyramid tradeoffs, fast and slow test separation, integration boundaries, CI feedback loops, and architecture choices that make code testable. Use when a test suite is too slow, too brittle, too mock-heavy, unclear about unit vs integration coverage, or needs a testing strategy before major growth."
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Test Architecture Strategy
  category: Testing
  tags: tdd,testing,architecture,ci,test-pyramid
---

# Test Architecture Strategy

Use this skill to reason about the shape of a test suite, not one test at a time. The goal is a suite that gives confidence, runs quickly enough for flow, and still catches integration failures at important boundaries.

## Source Traceability

Primary source: Harry Percival, *Test-Driven Development with Python*, 3rd ed. Guidance is transformed and paraphrased from chapter 27 and Appendix A, especially test desiderata, fast/slow test tradeoffs, test pyramid thinking, boundaries, ports and adapters, functional core/imperative shell, and when to rethink architecture.

## Workflow

1. Inventory the current suite.
   - Identify unit, integration, functional/end-to-end, smoke, and manual checks.
   - Capture runtime, flake rate, CI split, and developer feedback path.

2. Classify the pain.
   - Slow feedback.
   - Brittle structure-coupled tests.
   - Mock-heavy tests with low confidence.
   - Missing boundary coverage.
   - Too many end-to-end tests.

3. Choose the target shape.
   - Fast tests for core logic and detailed cases.
   - Integration tests at real boundaries.
   - A small number of end-to-end tests for critical journeys.
   - Production monitoring or smoke checks where tests are not enough.

4. Move one slice at a time.
   - Extract pure logic or service boundaries.
   - Replace exhaustive end-to-end coverage with lower-level tests plus one journey.
   - Add contract or integration checks for external systems.
   - Define a runtime red line before the suite becomes painful.

Read [test-architecture-patterns.md](references/test-architecture-patterns.md) for audit questions, migration patterns, and decision tables.

## Decision Rules

- If tests are slow but valuable, first separate fast local feedback from full CI proof.
- If unit tests require databases or frameworks everywhere, identify pure core logic that can move inward.
- If mocks dominate, use architecture seams rather than more mocks.
- If end-to-end tests cover many detailed branches, demote detailed cases to lower-level tests.
- If integration bugs keep escaping, add boundary tests before deleting broad coverage.

## Guardrails

- Do not chase a textbook test pyramid without respecting the product's real risks.
- Do not delete slow tests until replacement confidence exists.
- Do not make every piece of code "pure" at the cost of framework clarity.
- Do not optimize runtime without measuring.

## Verification

Before finishing, produce:

- Current suite map.
- Pain classification with evidence.
- Target suite shape.
- First migration slice.
- Verification commands or metrics that prove progress.
