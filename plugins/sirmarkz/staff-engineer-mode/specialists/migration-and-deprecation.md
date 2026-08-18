---
name: migration-and-deprecation
description: "Use when moving many consumers from legacy services, APIs, libraries, or capabilities to replacements with no-new-usage controls"
---

# Large-Scale Migration And Deprecation

## Iron Law

```
NO DEPRECATION WITHOUT REPLACEMENT, USAGE TELEMETRY, MIGRATION PATH, AND BACKSLIDING CONTROL
```

Warnings without migration machinery are just noise.

## Overview

Removing or replacing a widely used system is a production change spread across many dependents.

**Core principle:** discover real usage, provide a safe replacement, migrate incrementally, prevent new usage, prove dependents are gone, and hand terminal teardown to `service-decommission-and-sunset`.

## When To Use

- The user asks to drive consumers off a legacy service, API family, library, platform, data product, or capability and onto a replacement.
- A broad migration crosses many projects, repositories, services, clients, tenants, or runtime dependents.
- A large mechanical change needs staged execution, generated edits, responsibility routing, and non-regression controls.
- New usage must be blocked while old usage is migrated away.

## When Not To Use

- The work is a routine dependency update, package bump, or small codemod; use `dependency-and-code-hygiene` instead.
- The work changes or versions one exposed API contract and needs compatibility or a safe transition for that contract, including clients with separate deployment schedules; use `api-design-and-compatibility` instead.
- The work has reached zero-traffic proof, final data disposition, credential or name reclamation, ordered infrastructure teardown, monitoring removal, or no-resurrection evidence; use `service-decommission-and-sunset` instead.
- The work is database schema/backfill execution; use `database-operations` instead.
- The work is rollout sequencing for an already built change; use `progressive-delivery` instead.
- The work is a runtime, platform, client, service, or host upgrade with
  mixed-version windows or temporary exceptions; use `fleet-upgrades` instead.

## Info To Gather

- Current work phase, next decision, what is known, and assumptions where details are missing.
- Deprecated thing, replacement, reason, deadline, risk, and support window.
- Static references, runtime calls, traffic classes, load shape, tenants, clients, jobs, dashboards, alerts, docs, and third-party dependents.
- Migration path, compatibility layer, dual-read/write needs, per-consumer or per-object completion evidence, validation checks, and rollback/escape hatch.
- Dependency optionality, fail-open or fail-closed behavior, traffic deflection rules, and whether staged turndown can replace global cutoff.
- Domain or DNS surfaces used by consumers: ownership, current and replacement targets, records in each served environment, direct resolution checks, TTL/cache behavior, hidden dependents, reversible cutover, and the terminal assets that must be handed off without deletion.
- Advisory versus compulsory policy, enforcement checks, exception process, and communication channel.
- Backsliding prevention: build rules, lint/static checks, visibility controls, change-time warnings, templates, and docs.
- Drive-off completion and terminal handoff inventory: disabled legacy entry points, dark traffic, jobs, support tools, snapshots or exports still needed for rollback, and residual code, config, data, credentials, names, monitoring, runbooks, costs, or access paths that remain for terminal decommission.

## Workflow

1. **Define the end state.** State what is being removed, what replaces it, what remains supported, and why the change is worth doing.
2. **Discover usage.** Combine code search, dependency graph, runtime telemetry, logs, responsibility metadata, and consumer outreach.
3. **Classify dependents.** Separate easy mechanical users, risky dynamic users, abandoned critical paths, and external clients.
4. **Choose migration mode.** Use advisory deprecation for low-risk nudges; use compulsory deadlines when responsibility and enforcement exist.
5. **Provide paved migration.** Supply examples, compatibility shims, codemods, validation commands, and rollback/escape hatches. Default to expand/contract (parallel-change): add the new path, dual-run and shadow-diff old versus new outputs to prove equivalence, migrate callers, then contract the old path.
6. **Prevent backsliding.** Block or warn on new usage through change-time checks, build visibility, templates, docs, and policy checks.
7. **Migrate in batches.** Move dependents in batches small enough to understand, test, and roll back; include capacity warmup, retry/caching behavior, and backlog-drain checks for each traffic class before moving the next batch. Track progress with objective metrics and verify completion at the same granularity the new code will assume.
8. **Prove mixed-state closure.** Before code, config, or data readers assume the old format/path is gone, show per-consumer or per-object evidence that no mixed old/new state remains; treat failed migration records and "test-only" failures as unknown customer risk until classified.
9. **Disable and observe without terminal deletion.** Stop or quarantine old runtime paths, watch for at least one representative business cycle, check dark traffic, jobs, support tools, and alerts, and keep an escape hatch until the old path stays quiet. Before turning down a dependency, prove consumers no longer treat it as required and that traffic will not be deflected away from usable serving paths.
10. **Treat DNS changes as reversible consumer transitions.** When migration changes a name's target, verify ownership and records across each served environment, resolve the current and replacement targets from representative consumer paths, model TTL/cache behavior, check hidden dependents, and preserve the prior target for rollback. Final record or zone deletion, namespace release, and hijack-prevention evidence belong to `service-decommission-and-sunset`.
11. **Hand off terminal decommission.** Record drive-off completion and the residual code, config, data, credentials, names, infrastructure, pipelines, monitoring, runbooks, costs, and resurrection paths that still exist. Do not perform final disposal, reclamation, ordered teardown, monitoring removal, or cost-stop verification in this specialist.

## Synthesized Default

Treat deprecation as an engineered migration. Use centralized expertise for broad changes, automate repetitive edits, preserve compatibility while dependents move, enforce no-new-usage, prove drive-off, and hand terminal teardown evidence to `service-decommission-and-sunset`.



## Exceptions

- Emergency drive-off or disablement may skip normal windows when security or data-loss risk dominates, but needs explicit impact analysis and repair plan.
- External public clients may require longer overlap, stronger telemetry, and contractual support windows.
- Advisory deprecation is acceptable for low-risk cleanup when maintenance cost is small and no deadline is required.
- Abandoned dependents may require a user decision, compatibility shim, or replacement before legacy-path disablement.

## Response Quality Bar

- Lead with the migration plan, deprecation decision, usage inventory, or drive-off blocker requested.
- Cover replacement readiness, usage measurement, dependent batching, no-new-usage controls, exception policy, disable-and-observe evidence, and the terminal-decommission handoff before optional change-management breadth.
- Make recommendations actionable with migration batches, validation checks, deadlines, stop criteria, escape hatches, and drive-off checks where relevant.
- Name the details to inspect, such as static references, runtime telemetry, dependent replacement examples, block/warn controls, dark-traffic checks, and residual-asset handoff records; do not state details you have not seen.
- Stay technology-agnostic by default: do not introduce provider, product, framework, database, protocol, or command names unless the user supplied them or explicitly requested tool-specific guidance.
- Stay inside engineered migration and deprecation. Route architecture redesign or vulnerability emergency handling only when those are the central unresolved risk.
- Be concise: avoid generic program-management language and prefer compact inventories, migration batch tables, and handoff records.

## Required Outputs

- Output shape: render the matching shared template headings or tables in the reply, or use the same shape.
- Deprecation decision record with replacement, reason, and end state.
- Usage inventory with static and runtime checks.
- Dependent classification and migration batches.
- Migration completion evidence for old/new mixed state at the consumer, tenant, object, or config granularity the drive-off decision depends on.
- Migration guide, examples, validation, and escape hatch.
- Capacity warmup, retry/cache, and backlog-drain checks for the replacement path.
- Backsliding prevention controls.
- Enforcement, exception, and deadline policy.
- Disable-and-observe plan with watch-window results and an escape hatch.
- Dependency optionality and staged-turndown check.
- Domain and DNS transition check with ownership, current and replacement targets, served-environment records, resolver, TTL/cache, hidden-dependent, and rollback evidence where applicable.
- Terminal-decommission handoff with drive-off evidence and an inventory of residual code, config, data, credentials, names, infrastructure, pipelines, monitoring, runbooks, costs, and resurrection paths.

## Checks Before Moving On

- `usage_inventory`: static and runtime usage are measured, or blind spots are named.
- `replacement_ready`: replacement path is documented, supported, and validated for representative dependents, traffic classes, capacity warmup, and backlog drain.
- `migration_batches`: dependents are grouped into maintained, linked, reversible batches.
- `parallel_change`: migration uses expand/contract with dual-run/shadow-diff equivalence evidence before contracting the old path.
- `completion_evidence`: old/new mixed state is measured at the granularity required before readers, writers, or configs assume migration completion.
- `backsliding_control`: new usage is blocked, warned, or explicitly exception-checked.
- `dependency_optionality`: legacy dependencies are marked optional or removed from fail-closed checks, and turndown is staged with deflection behavior verified.
- `domain_dns_transition`: consumer-facing name changes have ownership, current and replacement targets, served-environment records, direct resolver results, TTL/cache behavior, hidden-dependency checks, and rollback; terminal deletion or release is handed off.
- `terminal_handoff`: drive-off completion is proven and residual code, config, data, credentials, names, infrastructure, pipelines, monitoring, runbooks, costs, and resurrection paths are recorded for `service-decommission-and-sunset`; migration performs no final disposition, reclamation, ordered teardown, monitoring removal, or no-resurrection decision.

## Red Flags - Stop And Rework

- A deprecation warning has no replacement, deadline, or telemetry.
- New users can still copy old examples and add fresh dependencies.
- Migration success is counted by emails sent rather than usage removed.
- A legacy path is disabled before dark traffic, jobs, support tools, and external clients are checked.
- A globally turned-down dependency is still treated as required by a dependent serving path.
- A domain is marked unused because one management tool cannot see its records.
- Terminal teardown starts without a drive-off evidence package and residual-asset inventory.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Announcing instead of migrating | Provide tooling, examples, and maintained batches. |
| Relying only on static search | Add runtime telemetry for dynamic dependents. |
| Ignoring backsliding | Block new usage while old usage is removed. |
| Performing terminal teardown inside migration | Hand proven drive-off and residual assets to `service-decommission-and-sunset`. |
