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
- Runtime config values, input source, schema, required and non-empty fields, allowed values, defaults, invariants, dependency ordering, scheduling or priority class, unsafe values, and unsafe combinations.
- Dormant or not-yet-in-service features present in production binaries, their activation guards, test evidence, and safe disabled behavior.
- Generated or derived config state, producer and receiver validation, accepted-versus-applied status, fanout or pull behavior, last-known-good snapshots, cross-version readers or writers, queues, caches, and client-visible artifacts that may survive rollback.
- Rejected or pending config state, quarantine location, retry behavior, and whether later unrelated changes can carry failed config forward if validation is disabled or bypassed.
- Bulk input semantics: required columns, row identity, duplicate handling, missing values, current-value preconditions, per-tenant caps, and aggregate blast-radius limits.
- Temporary overrides with owner, expiry, validation evidence, cleanup action, and rollback target before cleanup automation can apply or remove them.
- Change path, approval path, user confirmation, preview or dry-run output, execution identity, and change record.
- Tracking or shadow-mode behavior for protection algorithms, throttles, limiters, placement rules, load balancers, and other enforcement config before they affect production requests.
- Blast radius, rollback or disable path, rate limit, lock, retry, and idempotency behavior.
- Operational levers: name, expected effect, activation time, prerequisites, approval gates, safety thresholds, last test, and disable or revert path.
- Change class and confirmation path: low-risk, standard production, or emergency; checks to make before the user proceeds.
- Prior incidents, drift reports, manual overrides, and exception rules.

## Workflow

1. **Classify the surface and change class.** Separate static config, dynamic config, generated changes, scheduled automation, and emergency automation; name the change class as low-risk, standard production, or emergency, with a distinct confirmation path for each class.
2. **Define the contract.** Specify schema, required and non-empty inputs, safe defaults, bounds, invariants, local change path, and incompatible combinations. Missing, blank, or unknown inputs that can mutate or delete production state must fail closed.
3. **Inventory override risk before cleanup.** Find runtime config values, unsafe values, temporary overrides, and stale settings; block cleanup automation when any production-impacting entry lacks owner, expiry, validation evidence, cleanup action, and rollback target.
4. **Record production changes.** For production-impacting changes, including pre-launch production, capture user confirmation, confirmation basis, expected blast radius, and recovery path before execution.
5. **Validate before execution.** Require parse, semantic, dependency, permission, target-scope, and environment checks before production use; for tabular bulk inputs, reject unknown columns, duplicate targets, missing required values, unsafe deltas, and changes above per-tenant caps. Check generated state, producer and receiver-side validation for generated configs, dormant-feature activation guards, current ownership, route or policy scope, version compatibility, scheduling or priority demotions of critical jobs, and minimum healthy capacity where the config can change routing, permissions, or serving eligibility. Quarantine rejected config, make validation gates fail closed, and prove later unrelated changes cannot reintroduce a failed change.
6. **Preview the effect.** Show intended creates, updates, deletes, traffic impact, permission changes, affected systems, unchanged rows, skipped rows, and per-tenant cap violations before apply.
7. **Use tracking before enforcement.** For throttles, limiters, protection algorithms, placement policies, or load-balancing rules, run the new decision logic in tracking or shadow mode against representative production workload before enforcement. Compare predicted actions, false positives, tenant or scale-unit concentration, and downstream service impact before enabling the change.
8. **Prove application state.** Distinguish accepted, persisted, propagated, and serving-applied states for config changes; require an application signal before declaring success when serving systems can accept a config mutation without applying it.
9. **Bound execution.** Use fault-domain-aware batches, locks, rate limits, stop criteria, per-target and aggregate caps, and idempotency for automation that touches shared state. Stagger config fanout, readers, pullers, and processors when simultaneous reloads can overload the source of truth.
10. **Make recovery concrete.** Define rollback, disable, restore, or roll-forward behavior for config, generated changes, and automation side effects; capture previous values in a replayable rollback artifact before mutating state. Include repair of polluted last-known-good state, stale queues, caches, client-held artifacts, and dependent records before promotion resumes.
11. **Prepare operational levers.** For emergency adjustment or recovery levers, state the effect, prerequisites, approval gates, safety thresholds, activation time, last test, and disable or revert path before relying on them. If a lever can be blocked by quota, approval, blast-radius caps, or safety automation, make that block visible in the runbook and exercise the allowed path before an emergency.
12. **Control drift.** Detect unmanaged overrides and stale settings; decide reconcile, exception, or removal.
13. **Close the loop.** Record user confirmation, validation output, preview, execution result, and cleanup for temporary settings.

## Synthesized Default

Use typed config contracts, deterministic validation, effect preview, small fault-domain-aware execution batches, explicit user confirmation for production-impacting work, linked change records, drift checks, and tested recovery paths. Automation should be idempotent by default and should fail closed when it cannot confirm the intended target.



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

- Output shape: render the matching shared template headings or tables in the reply, or use the same shape.
- Configuration or automation safety decision.
- Change class and confirmation path: low-risk, standard production, or emergency, with required checks and decision rationale.
- Production change record with user confirmation, expected effect, blast radius, and recovery results where the change can affect production state.
- Contract: schema, required and non-empty inputs, defaults, invariants, scheduling or priority class, unsafe combinations, allowed overrides, and local change path.
- Dormant-feature guard check with disabled behavior, activation path, test evidence, and rollback or disable action.
- Bulk input contract: required fields, row identity, duplicate behavior, current-value preconditions, per-tenant caps, skipped-row handling, and aggregate limits.
- Runtime config and temporary override inventory with owner, expiry, validation evidence, cleanup action, rollback target, and unsafe values called out.
- Validation and preview check list.
- Rejected-change quarantine and validation-gate integrity check.
- Tracking or shadow-mode comparison for enforcement, throttling, protection, placement, or load-balancing changes.
- Application-state and fanout plan for accepted, persisted, propagated, serving-applied, and simultaneous reload behavior.
- Blast-radius and execution-control plan.
- Recovery plan for rollback, disable, restore, or roll-forward.
- Derived-state cleanup plan for generated records, cached config, queues, last-known-good snapshots, and client-visible artifacts that rollback leaves behind.
- Generated-config boundary check with producer validation, receiver reject behavior, last-known-good restore path, and known corruption forms.
- Operational lever inventory with expected effect, activation time, prerequisites, approval gates, safety thresholds, last test, and disable or revert path.
- Drift detection and exception rules.
- Approval, execution, and cleanup checklist.

## Checks Before Moving On

- `change_class_confirmed`: low-risk, standard production, or emergency class is named with the required checks for that class.
- `change_record`: production-impacting config or automation has linked preview, user confirmation, execution identity, and recovery results.
- `contract_defined`: schema, required and non-empty inputs, defaults, bounds, invariants, and local change path are explicit.
- `preview_checked`: intended production effect is visible before execution.
- `tracking_mode`: enforcement-style config changes compare predicted and actual effects in tracking mode before production enforcement.
- `application_state`: accepted, persisted, propagated, and serving-applied config states are distinguishable where they can diverge.
- `semantic_scope_check`: target scope, ownership, version compatibility, generated state, and minimum healthy capacity are checked beyond syntax.
- `validation_gate_integrity`: rejected or failed config cannot be applied, retried, bundled into a later change, or promoted when validation is disabled or unhealthy.
- `generated_config_boundary`: generated config has producer validation, receiver reject behavior, last-known-good restore path, and coverage for known corrupt output forms.
- `dormant_feature_guard`: config cannot activate not-yet-in-service code unless the disabled behavior, activation guard, test evidence, and disable path are explicit.
- `critical_priority_check`: priority, scheduling, or load-shedding class changes cannot demote critical serving or control-plane dependencies without explicit validation.
- `blast_radius`: affected users, systems, and data are bounded.
- `execution_bounds`: automation that can cross locations, tenants, partitions, deployment units, or config readers has fault-domain-aware batches, aggregate caps, fanout controls, and stop criteria.
- `recovery_path`: rollback, disable, restore, or roll-forward path is defined.
- `rollback_state_cleanup`: rollback accounts for generated records, cached config, queues, last-known-good state, and client-visible artifacts that can outlive the change.
- `lever_ready`: emergency adjustment or recovery levers have named effect, prerequisites, approval gates, safety thresholds, activation path, and disable or revert path.
- `lever_tested`: operational levers have a recent test result or an explicit unknown.
- `change_log`: approval, validation, execution result, and exception state are linked.

## Red Flags - Stop And Rework

- Configuration bypasses validation because it is "not code."
- A later unrelated change can carry a previously rejected config into production.
- Unlaunched production is treated as non-production even though it can affect users, data, credentials, or recovery.
- Automation can delete or mutate shared state without preview.
- A config change is called complete when the control plane accepted it but serving systems have not applied it.
- All readers or processors reload from the config source at once without a cap, jitter, or stop signal.
- Validation proves syntax while target scope, generated state, ownership, or version compatibility remains unchecked.
- Defaults differ by environment without a documented reason.
- Blank or missing inputs silently choose a destructive or time-delayed default.
- Recovery depends on remembering the previous value manually.
- Temporary overrides have no expiry or cleanup action.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Valid syntax as safety | Add semantic, dependency, and blast-radius checks. |
| One giant automation run | Use fault-domain-aware batches, locks, aggregate caps, stop criteria, and idempotency. |
| Silent config drift | Detect, reconcile, or exception-check unmanaged changes. |
| Priority change treated as harmless metadata | Validate critical-job scheduling and load-shedding behavior before apply. |
| Rollback by memory | Record prior state and verify recovery. |
