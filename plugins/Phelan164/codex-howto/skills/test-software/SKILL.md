---
name: test-software
description: Design, implement, and evaluate risk-based software tests across unit, integration, contract, end-to-end, and regression layers. Use when adding tests, reproducing bugs, improving coverage, diagnosing flaky tests, or defining a test strategy; do not use to change production behavior unless the user also requests implementation.
---

# Test Software

## Test contract

- Define the behavior, invariant, or defect before selecting a test layer.
- Use the lowest layer that observes the risk without hiding the integration
  boundary under test.
- Test behavior rather than private implementation details.
- Avoid snapshots that hide meaningful assertions.
- Do not mock the component whose integration contract is under test.
- Control time, randomness, concurrency, and external dependencies explicitly.
- Keep fixtures minimal and readable.
- Do not “fix” flaky tests by adding blind retries or sleeps.
- Do not claim a regression test without proving it fails against the broken behavior when feasible.
- Treat tests as potentially state-changing: they may write databases, queues,
  files, snapshots, browsers, or external sandboxes.
- Do not run tests against production, shared customer data, or external
  services without explicit authorization and a verified isolation strategy.
- Stop when the configured test target or cleanup behavior is ambiguous.

## Execute and report

Read [references/test-strategy.md](references/test-strategy.md) when choosing
test layers or specialized methods, investigating flakes, or planning
cross-service coverage.

Build deterministic fixtures, implement the smallest high-value set, and run
focused tests repeatedly before broader required checks. Separate product,
test, and environment failures.

For a strategy request, return:

1. risks in priority order;
2. proposed test layer for each risk;
3. fixtures and dependencies;
4. commands to run;
5. coverage intentionally deferred.

For implementation, report focused and broader checks separately.
