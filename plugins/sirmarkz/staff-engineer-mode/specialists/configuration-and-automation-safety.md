---
name: configuration-and-automation-safety
description: "Use when one-shot config changes, scripts, cleanup automation, overrides, or drift fixes touch production state"
---

# Configuration And Automation Safety

## Iron Law

```
NO CONFIG OR AUTOMATION CHANGE WITHOUT VALIDATION, PREVIEW, BLAST RADIUS, CONFIRMATION, AND RECOVERY PATH
```

If the change cannot be checked before execution and reversed or contained after failure, it is not safe enough.

## Overview

Configuration and automation can change production faster than ordinary code paths expose.

**Core principle:** treat config, generated changes, and operational automation as production code with explicit schema, preview, user confirmation, and recovery results.

## When To Use

- The user asks about configuration safety, generated changes, operational scripts, bulk automation, feature settings, policy defaults, or config validation.
- A non-code change can alter routing, permissions, capacity, customer experience, data handling, or operational behavior.
- Automation creates, updates, deletes, migrates, or remediates production state.
- A pre-launch or unlaunched production environment can affect real users, data, credentials, capacity, or recovery expectations.
- Configuration drift, copy-paste settings, or untracked overrides are causing incidents.

## When Not To Use

- The main question is production rollout sequencing; use `progressive-delivery` instead.
- The main question is declarative infrastructure, admission, or drift reconciliation; use `infrastructure-and-policy-as-code` instead.
- The main question is dependency cleanup or package updates; use `dependency-and-code-hygiene` instead.
- The request is one-off local scripting with no production or shared-state risk.

## Info To Gather

- Current work phase, next decision, what is known, and assumptions where details are missing.
- Config or automation surface, consumers, environments, affected production state, and local change path.
- Schema, allowed values, defaults, invariants, dependency ordering, and unsafe combinations.
- Change path, approval path, user confirmation, preview or dry-run output, execution identity, and change record.
- Blast radius, rollback or disable path, rate limit, lock, retry, and idempotency behavior.
- Operational levers: name, expected effect, activation time, prerequisites, last test, and disable or revert path.
- Change class and confirmation path: low-risk, standard production, or emergency; checks to make before the user proceeds.
- Prior incidents, drift reports, manual overrides, and exception rules.

## Workflow

1. **Classify the surface and change class.** Separate static config, dynamic config, generated changes, scheduled automation, and emergency automation; name the change class as low-risk, standard production, or emergency, with a distinct confirmation path for each class.
2. **Define the contract.** Specify schema, defaults, bounds, invariants, local change path, and incompatible combinations.
3. **Record production changes.** For production-impacting changes, including pre-launch production, capture user confirmation, confirmation basis, expected blast radius, and recovery path before execution.
4. **Validate before execution.** Require parse, semantic, dependency, permission, and environment checks before production use.
5. **Preview the effect.** Show intended creates, updates, deletes, traffic impact, permission changes, and affected systems before apply.
6. **Bound execution.** Use batches, locks, rate limits, stop criteria, and idempotency for automation that touches shared state.
7. **Make recovery concrete.** Define rollback, disable, restore, or roll-forward behavior for config, generated changes, and automation side effects.
8. **Prepare operational levers.** For emergency adjustment or recovery levers, state the effect, prerequisites, activation time, last test, and disable or revert path before relying on them.
9. **Control drift.** Detect unmanaged overrides and stale settings; decide reconcile, exception, or removal.
10. **Close the loop.** Record user confirmation, validation output, preview, execution result, and cleanup for temporary settings.

## Synthesized Default

Use typed config contracts, deterministic validation, effect preview, small execution batches, explicit user confirmation for production-impacting work, linked change records, drift checks, and tested recovery paths. Automation should be idempotent by default and should fail closed when it cannot confirm the intended target.



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

- Emergency automation may run with fewer pre-change checks when delay is riskier, but it still needs user confirmation, a linked change record, stop criteria, and post-change reconciliation.
- Low-risk local config can use lighter checks if it cannot affect shared systems, sensitive data, or production users.
- Some generated changes are easier to roll forward than roll back; document the recovery decision before execution.

## Response Quality Bar

- Lead with the safety decision, config contract, automation risk, or check matrix requested.
- Name the change class and confirmation path: low-risk changes need local validation results, standard production changes need explicit user confirmation plus preview output, and emergency changes need user confirmation plus post-change reconciliation.
- Cover validation, preview, blast radius, execution controls, drift handling, and recovery before optional automation detail.
- Make recommendations actionable with validation checks, stop criteria, batch size, linked change records, and cleanup where relevant.
- Name the details to inspect, such as schema, preview output, user confirmation, execution logs, drift reports, and rollback checks; do not state details you have not seen.
- Stay technology-agnostic by default: do not introduce provider, product, framework, database, protocol, or command names unless the user supplied them or explicitly requested tool-specific guidance.
- Stay inside config and automation safety. Use rollout, infrastructure policy, or dependency hygiene skills only when that surface is the immediate risk.
- Be concise: prefer compact contract and check tables over generic automation advice.

## Required Outputs

- Configuration or automation safety decision.
- Change class and confirmation path: low-risk, standard production, or emergency, with required checks and decision rationale.
- Production change record with user confirmation, expected effect, blast radius, and recovery results where the change can affect production state.
- Contract: schema, defaults, invariants, unsafe combinations, allowed overrides, and local change path.
- Validation and preview check list.
- Blast-radius and execution-control plan.
- Recovery plan for rollback, disable, restore, or roll-forward.
- Operational lever inventory with expected effect, activation time, prerequisites, last test, and disable or revert path.
- Drift detection and exception rules.
- Approval, execution, and cleanup checklist.

## Checks Before Moving On

- `change_class_confirmed`: low-risk, standard production, or emergency class is named with the required checks for that class.
- `change_record`: production-impacting config or automation has linked preview, user confirmation, execution identity, and recovery results.
- `contract_defined`: schema, defaults, bounds, invariants, and local change path are explicit.
- `preview_checked`: intended production effect is visible before execution.
- `blast_radius`: affected users, systems, and data are bounded.
- `recovery_path`: rollback, disable, restore, or roll-forward path is defined.
- `lever_ready`: emergency adjustment or recovery levers have named effect, prerequisites, activation path, and disable or revert path.
- `lever_tested`: operational levers have a recent test result or an explicit unknown.
- `change_log`: approval, validation, execution result, and exception state are linked.

## Red Flags - Stop And Rework

- Configuration bypasses validation because it is "not code."
- Unlaunched production is treated as non-production even though it can affect users, data, credentials, or recovery.
- Automation can delete or mutate shared state without preview.
- Defaults differ by environment without a documented reason.
- Recovery depends on remembering the previous value manually.
- Temporary overrides have no expiry or cleanup action.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Valid syntax as safety | Add semantic, dependency, and blast-radius checks. |
| One giant automation run | Use batches, locks, stop criteria, and idempotency. |
| Silent config drift | Detect, reconcile, or exception-check unmanaged changes. |
| Rollback by memory | Record prior state and verify recovery. |
