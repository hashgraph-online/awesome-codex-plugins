# Implementation Plan Format

`codex-plan.md` should be readable by a fresh implementer.

In `standard` mode it should normally be at least 2,500 words. In `deep` mode
it should normally be at least 5,000 words. This matches the level of detail
expected from strong Deep Trilogy-style artifacts: enough architecture,
contracts, rationale, and test detail that implementation can proceed without
the original conversation.

Recommended sections:

1. Reader note: this plan is self-contained and line-level code is left to
   implementation sections.
2. Context in one page: current system, problem, verified facts, constraints.
3. Goal and non-goals.
4. Architecture at a glance: diagram or layered explanation.
5. Rationale and tradeoffs: why this design, rejected alternatives.
6. Data model and contracts: schemas, payloads, permissions, config, CLI/API.
7. File tree and file-by-file implementation outline.
8. Phase plan: batches, dependencies, parallelization, hard gates.
9. Error handling, concurrency, idempotency, retries, and edge cases.
10. Security, privacy, secrets, data retention, and permissions.
11. Migration, rollout, rollback, and observability.
12. Test strategy: unit/integration/e2e, fixtures, mocks, expected failures.
13. Risks, open questions, and stop-the-line decisions.

Write concrete paths, command names, interfaces, and data shapes. Avoid
large production-code blocks unless a stub or signature removes ambiguity.

The plan should explain why the approach fits the existing codebase. Include
enough source evidence that a reviewer can see what was verified, for example
file paths, function names, route names, schemas, current behavior, and test
commands.
