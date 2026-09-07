# Depth modes

Depth changes analysis, never prose volume.

## Lean (default)

Use only the core artifact set. Consolidate requirements, evidence, design,
tests, risks, and ownership. Inspect enough code and docs to remove material
ambiguity. One Codex review. Short sections reference plan IDs instead of
repeating context.

## Standard (explicit only)

Use when the user requests broader analysis. Verify more integration paths,
alternatives, edge cases, migration behavior, and test layers. Add a research,
normalized-spec, TDD, or governance artifact only when separation improves
implementation or review.

## Deep (explicit only)

Use when the user requests maximum scrutiny. Add independent review
perspectives for relevant risks: architecture, security/privacy, data/migration,
operations, product ambiguity, and test feasibility. Record evidence and
tradeoffs for high-impact decisions. Still remove duplication and empty
ceremony.

All modes require:

- stable requirement IDs and measurable acceptance
- exact file and contract ownership
- tests-first section work with runnable commands
- dependency order and shared-file sequencing
- risk mitigation, rollback, and stop conditions where relevant
- source-to-plan-to-section-to-test traceability
