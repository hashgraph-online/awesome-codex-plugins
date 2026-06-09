---
name: test-data-engineering
description: "Use when designing fixtures, golden files, or production snapshots needing anonymization, freshness, or drift checks"
---

# Test Data Engineering

## Iron Law

```
NO TEST RELIES ON DATA THE TEST CANNOT REPRODUCE OR RESTORE
```

A green test backed by lost-provenance data does not stand on its own. The next refresh, the next anonymization sweep, or the next schema change will turn it red without any code change.

## Overview

Produces a fixture inventory with scope and regeneration path per fixture, an anonymization policy for any test data sourced from production, a freshness-versus-determinism decision per fixture class, and a drift-detection plan that fires when production data shape diverges from the data the tests run on. Refuses to call a test passing when the data it relies on cannot be reproduced or restored.

**Core principle:** test data is a production artifact. If a fixture cannot be regenerated, anonymized, or restored on demand, the tests that depend on it are an outage waiting for the next refresh.

## When To Use

- The user is designing, changing, or maintaining fixtures, golden files, snapshots, captured production data, or synthetic test data.
- A flaky or order-dependent test is suspected to depend on shared mutable fixture state.
- A test relies on production-sourced data that may contain personal or sensitive information and the anonymization policy is unclear or absent.
- A schema change in production broke a contract test, integration test, or migration that ran on stale fixtures.
- You need to decide between freshly captured production data, snapshotted captures, hand-built fixtures, or synthetic generation for a given test layer.
- A regression appears in production that fixtures did not cover because the fixture predated the data shape that caused it.
- An ML or analytics fixture is drifting from production distribution and graders, thresholds, or correctness checks are losing signal.

## When Not To Use

- The work is overall test strategy, check placement, runtime budgets, or flake policy; use `testing-and-quality-gates`.
- The work is privacy retention, deletion, export, erasure, or data classification across systems; use `privacy-and-data-lifecycle`.
- The work is a producer/consumer schema contract evolution decision; use `data-contracts`.
- The work is a production batch or streaming pipeline's freshness, lineage, or replay; use `data-pipeline-reliability`.
- The work is database migration safety, locks, backfills, or index rollout; use `database-operations`.
- The work is ML model training or serving drift detection on production traffic; use `ml-reliability-and-evaluation`.
- The work is producing eval datasets and graders for an LLM workflow; use `llm-evaluation`.

## Info To Gather

- Current work phase, next decision, what is known, and assumptions where details are missing.
- Fixture inventory source: which test layers (unit, component, contract, integration, end-to-end, performance, security, ML/LLM) hold fixtures, where each fixture lives, and how it is loaded.
- Per-fixture metadata: name, scope (per test, per file, per suite, per process, per environment), generation source (hand-written, synthetic generator, captured production, derived golden), and refresh cadence.
- Production-source captures: which fixtures are captured from production, when each was captured, what fields were included, and what anonymization or redaction was applied.
- Schema versions: production schema version per source, fixture schema version per fixture, and any pinned version skew between them.
- Golden-file inventory: which tests assert against golden outputs and the procedure for regenerating each one.
- Data-shape signals: production distributions for fields the tests rely on (cardinality, nullability, value ranges, categorical sets) and the latest measurements available.
- Privacy classification of any captured data: personal data, sensitive personal data, regulated data, secrets, customer-identifying data.
- Test isolation: whether fixtures are mutated by tests, whether mutations leak across tests, and whether test order affects outcome.
- Restore/reproduce procedure: for each fixture class, the documented steps to recreate it from scratch, and the time those steps take.

## Workflow

1. **Build the fixture inventory.** Reconcile fixtures discovered in the test tree, in CI artifact storage, and in any captured-data store. A fixture in only one of those is the first orphan.
2. **Classify each fixture.** Assign one class: hand-built (small, deterministic), synthetic-generated (programmatic, parameterized), captured (sampled or copied from production), derived golden (the test's expected output), or shared seeded state (a fixture multiple tests depend on).
3. **Decide freshness versus determinism per class.** Hand-built and synthetic fixtures should be deterministic by default; captured fixtures trade determinism for realism and need a refresh policy; derived goldens are deterministic by construction but require a regeneration procedure when behavior intentionally changes; shared seeded state is the most fragile and should be minimized.
4. **Set the scope rule per fixture.** Default to per-test scope. Move to per-file or per-suite scope only when the setup cost demands it and the fixture is read-only. Per-process or per-environment shared state requires explicit isolation guarantees and a teardown command.
5. **Apply the anonymization policy to captured data.** For each captured fixture, identify direct identifiers, quasi-identifiers, sensitive fields, and free-text fields that may carry personal data. Anonymization may require pseudonymization, generalization, suppression, redaction, or synthetic replacement. Hash-only is rarely sufficient because reidentification through quasi-identifiers and timing is common.
6. **Make captures restorable.** For each captured fixture, record source, capture timestamp, anonymization transform, and the procedure to recapture under current schema. A capture without these is unrestorable and must be regenerated or replaced.
7. **Establish drift detection.** For fields the tests rely on, compare production distribution to fixture distribution at a defined cadence. Alert when categorical sets diverge, nullability shifts, value ranges drift, or new required fields appear. Drift is a fixture-staleness signal before it is a test failure.
8. **Generate hard-to-construct data deliberately.** For domains with combinatorial complexity (financial calculations, rare-but-important edge cases, multi-step workflows), use parameterized generators, property-based generation, or scenario builders rather than hand-typing values that age out.
9. **Govern golden files.** State the regeneration procedure, the regeneration check, and the rule for what counts as an intentional change versus an accidental drift. Goldens regenerated without review erase the test's signal.
10. **Cull orphans.** Fixtures with no callers, absent sources, or sources that no longer exist must be removed or given a reproducible generator/restore path. Unrecoverable fixtures become production-critical by accident.
11. **Make findings directly actionable.** Each finding names the fixture path, the affected test path, and the local remediation: anonymize, regenerate, replace with synthetic, narrow scope, or delete.

## Synthesized Default

Prefer synthetic, parameterized fixtures generated at test time. Use captured production data only when realism is required and the anonymization, refresh, and restore procedures are real. Default to per-test scope. Goldens are deterministic by construction and have a documented regeneration procedure. Drift detection compares fixture distributions to production at a defined cadence. Captured data without anonymization or restore procedure is removed.



## Phase Behavior

- Ideation: identify risks, defaults, unknowns, options, and the next decision before code exists.
- Design: shape the target artifact, tradeoffs, checks, and details to gather.
- Development: guide sequencing, code boundaries, checks, and acceptance criteria.
- Testing: define release-blocking tests, evals, fixtures, and failure probes.
- Release: define rollout, observability, abort, rollback, and readiness details.
- Maintenance: define owners, drift checks, cleanup triggers, and refresh cadence.
- Existing artifact: use current code, docs, telemetry, incidents, or diffs as context for the next engineering decision; do not wait for a finished artifact before guiding design, build, release, or operation.
- Missing details: state assumptions and say what to check next instead of blocking lifecycle guidance.

## Exceptions

- Performance and load test fixtures may use captured-shape (size, distribution) without captured content; the realism the test needs is shape, not values.
- Compatibility and replay tests for legacy data may pin a real captured corpus; the corpus must still be anonymized and restorable, and the freshness policy may be paused with a stated reason.
- Property-based generators may be slow on first run; pin a seed for reproducibility and treat the seed as part of the fixture.
- Regulated workloads may forbid certain anonymization techniques because they are reversible under the threat model; record the exception and the resulting test-coverage impact.
- A snapshot/golden may pin third-party output that you do not control; in that case responsibility is "you accept the snapshot until the upstream changes" and the regeneration trigger is upstream-version change.

## Response Quality Bar

- Lead with the fixture inventory, anonymization rule, freshness/determinism decision, drift-detection plan, or golden-file rule requested.
- Cover classification, scope, anonymization, restore procedure, drift detection, and golden regeneration before optional fixture-tooling breadth.
- Make recommendations actionable with per-fixture path, classification, scope, refresh cadence, anonymization transform, restore procedure, and the local fix for each finding.
- Name the details to inspect, such as the fixture inventory, capture timestamps, anonymization transforms, production-distribution measurements, and the regeneration procedure for each golden; do not state restorability without the procedure.
- Stay technology-agnostic by default: do not introduce provider, product, framework, database, protocol, or command names unless the user supplied them or explicitly requested tool-specific guidance.
- Stay inside the data layer of testing. Route check placement and flake policy, privacy program work, schema-contract evolution, pipeline freshness, migration safety, ML drift, and LLM eval datasets to the responsible specialist.
- Be concise: prefer compact inventory and decision tables over generic fixture-management prose.

## Required Outputs

- Output shape: render the matching shared template headings or tables in the reply, or use the same shape.
- Fixture inventory with name, classification, scope, generation source, refresh cadence, and restore procedure per fixture.
- Anonymization policy for captured data covering direct identifiers, quasi-identifiers, sensitive fields, free-text, and the transform applied per field type.
- Freshness-versus-determinism decision per fixture class with the rule that governs each.
- Drift-detection plan listing the fields tracked, the production source, the comparison cadence, the alert threshold, and the local triage procedure for a drift alert.
- Golden-file rule: regeneration procedure, explicit checker, intentional-change-versus-drift rule, and the test path per golden.
- Orphan and responsibility report for fixtures with no callers or no recoverable source, with the remediation per fixture.
- Hard-to-construct data plan: which scenarios use generators, the seed/version policy for reproducibility, and the generator path.
- Restore-and-reproduce procedure per fixture class with documented steps and expected runtime.
- Follow-up routes to test strategy, privacy lifecycle, data contracts, pipeline reliability, database operations, ML reliability, or LLM evaluation as needed.

## Checks Before Moving On

- `fixture_inventory_present`: a single inventory reconciles fixtures across the test tree, CI storage, and any capture store; mismatches are listed.
- `classification_assigned`: every fixture has one class from hand-built, synthetic, captured, derived golden, or shared seeded.
- `scope_documented`: every fixture has a stated scope and shared state has isolation and teardown checks.
- `anonymization_applied`: every captured fixture has an applied anonymization transform sufficient against direct and quasi-identifier reidentification or an explicit recorded exception.
- `restore_procedure`: every fixture has a documented restore-or-regenerate procedure and an estimated runtime.
- `drift_detection_plan`: production-distribution comparison is defined for the fields the tests rely on, with cadence, threshold, and local triage procedure.
- `golden_rule`: each golden file has a regeneration procedure, and intentional-change rule.
- `orphan_culled`: fixtures with no callers or no recoverable source are listed with remediation.

## Red Flags - Stop And Rework

- A fixture exists but no one knows where it came from or how to regenerate it.
- Captured production data is in the test tree with no anonymization beyond field renaming.
- Tests share mutable state and pass only in a specific order.
- Goldens are regenerated automatically when they fail, erasing the test's signal.
- A schema change broke tests because fixtures pinned an obsolete shape and no drift signal fired.
- Anonymization is documented but the transform has not been re-applied since the last production-schema change.
- Hard-to-construct fixtures are hand-typed in many test files, drifting from each other and from production.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Treating fixtures as throwaway test code | Inventory fixtures with classification, and restore procedure. |
| Field-rename as anonymization | Apply transforms against direct and quasi-identifier reidentification; record the policy. |
| Shared mutable seeded state | Default to per-test scope; require isolation and teardown commands for shared state. |
| Auto-regenerating goldens on failure | Require an explicit check for golden regeneration; distinguish intentional change from drift. |
| Capturing once and forgetting | Set a refresh cadence and a recapture procedure tied to schema changes. |
| Hand-typing combinatorial scenarios | Use generators or scenario builders with seeds for reproducibility. |
| No drift signal | Compare fixture distributions to production at a defined cadence with a triage path. |
