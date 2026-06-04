---
name: migration-and-deprecation
description: "Use when retiring services, sunsetting APIs, replacing libraries, or migrating many callers with no-new-usage checks"
---

# Large-Scale Change And Service Deprecation

## Iron Law

```
NO DEPRECATION WITHOUT REPLACEMENT, USAGE TELEMETRY, MIGRATION PATH, AND BACKSLIDING CONTROL
```

Warnings without migration machinery are just noise.

## Overview

Removing or replacing a widely used system is a production change spread across many dependents.

**Core principle:** discover real usage, provide a safe replacement, migrate incrementally, prevent new usage, and remove only after usage signals show dependents are gone.

## When To Use

- The user asks to deprecate, sunset, retire, decommission, replace, or remove a service, API family, library, platform, data product, or capability.
- A broad migration crosses many projects, repositories, services, clients, tenants, or runtime dependents.
- A large mechanical change needs staged execution, generated edits, responsibility routing, and non-regression controls.
- New usage must be blocked while old usage is migrated away.

## When Not To Use

- The work is a routine dependency update, package bump, or small codemod; use `dependency-and-code-hygiene` instead.
- The work is API versioning for one service contract; use `api-design-and-compatibility` instead unless cross-system migration dominates.
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
- Domain or DNS surfaces: ownership attribution, zone-file presence in every served environment, registry or nameserver state, direct resolver checks, TTL/cache drain time, and hidden management-plane dependents.
- Advisory versus compulsory policy, enforcement checks, exception process, and communication channel.
- Backsliding prevention: build rules, lint/static checks, visibility controls, change-time warnings, templates, and docs.
- Disable and removal checklist: feature toggles, traffic cutoffs, dark traffic, jobs, support tools, snapshots/exports, code, config, data, credentials, alerts, dashboards, runbooks, costs, and access paths.

## Workflow

1. **Define the end state.** State what is being removed, what replaces it, what remains supported, and why the change is worth doing.
2. **Discover usage.** Combine code search, dependency graph, runtime telemetry, logs, responsibility metadata, and consumer outreach.
3. **Classify dependents.** Separate easy mechanical users, risky dynamic users, abandoned critical paths, and external clients.
4. **Choose migration mode.** Use advisory deprecation for low-risk nudges; use compulsory deadlines when responsibility and enforcement exist.
5. **Provide paved migration.** Supply examples, compatibility shims, codemods, validation commands, and rollback/escape hatches.
6. **Prevent backsliding.** Block or warn on new usage through change-time checks, build visibility, templates, docs, and policy checks.
7. **Migrate in batches.** Move dependents in batches small enough to understand, test, and roll back; include capacity warmup, retry/caching behavior, and backlog-drain checks for each traffic class before moving the next batch. Track progress with objective metrics and verify completion at the same granularity the new code will assume.
8. **Prove mixed-state closure.** Before code, config, or data readers assume the old format/path is gone, show per-consumer or per-object evidence that no mixed old/new state remains; treat failed migration records and "test-only" failures as unknown customer risk until classified.
9. **Disable before delete.** Stop or quarantine old runtime paths, watch for at least one representative business cycle, check dark traffic, jobs, support tools, and alerts, and keep an escape hatch until the old path stays quiet. Before turning down a dependency, prove consumers no longer treat it as required and that traffic will not be deflected away from usable serving paths.
10. **Treat DNS retirement as customer-impacting.** Before changing nameservers, deleting zones, or marking domains unused, verify ownership and zone records across every served environment, resolve the names directly through public or partner resolvers, model TTL/cache recovery time, and keep the prior nameserver state ready for rapid restore.
11. **Retire completely.** Remove runtime paths, data, config, credentials, dashboards, alerts, runbooks, docs, and cost artifacts after usage reaches the removal check; preserve required snapshots/exports with retention, and disposal date.

## Synthesized Default

Treat deprecation as an engineered migration, not an announcement. Use centralized expertise for broad changes, automate repetitive edits, preserve compatibility while dependents move, enforce no-new-usage, and treat final decommissioning as a high-risk production deployment.



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

- Emergency removal may skip normal windows when security or data-loss risk dominates, but needs explicit impact analysis and repair plan.
- External public clients may require longer overlap, stronger telemetry, and contractual support windows.
- Advisory deprecation is acceptable for low-risk cleanup when maintenance cost is small and no deadline is required.
- Abandoned dependents may require a user decision, compatibility shim, or replacement before removal.

## Response Quality Bar

- Lead with the migration plan, deprecation decision, usage inventory, or retirement blocker requested.
- Cover replacement readiness, usage measurement, dependent batching, no-new-usage controls, exception policy, disable-before-delete, and final cleanup before optional change-management breadth.
- Make recommendations actionable with migration batches, validation checks, deadlines, stop criteria, escape hatches, and retirement checks where relevant.
- Name the details to inspect, such as static references, runtime telemetry, dependent replacement examples, block/warn controls, dark-traffic checks, and disposal records; do not state details you have not seen.
- Stay technology-agnostic by default: do not introduce provider, product, framework, database, protocol, or command names unless the user supplied them or explicitly requested tool-specific guidance.
- Stay inside engineered migration and deprecation. Route architecture redesign or vulnerability emergency handling only when those are the central unresolved risk.
- Be concise: avoid generic program-management language and prefer compact inventories, migration batch tables, and retirement checklists.

## Required Outputs

- Output shape: render the matching shared template headings or tables in the reply, or use the same shape.
- Deprecation decision record with replacement, reason, and end state.
- Usage inventory with static and runtime checks.
- Dependent classification and migration batches.
- Migration completion evidence for old/new mixed state at the consumer, tenant, object, or config granularity the retirement depends on.
- Migration guide, examples, validation, and escape hatch.
- Capacity warmup, retry/cache, and backlog-drain checks for the replacement path.
- Backsliding prevention controls.
- Enforcement, exception, and deadline policy.
- Disable-before-delete plan with watch-window results and disposal handling.
- Dependency optionality and staged-turndown check.
- Domain and DNS retirement check with ownership, zone, nameserver, resolver, TTL/cache, and hidden-dependent evidence where applicable.
- Final retirement checklist.

## Checks Before Moving On

- `usage_inventory`: static and runtime usage are measured, or blind spots are named.
- `replacement_ready`: replacement path is documented, supported, and validated for representative dependents, traffic classes, capacity warmup, and backlog drain.
- `migration_batches`: dependents are grouped into maintained, linked, reversible batches.
- `completion_evidence`: old/new mixed state is measured at the granularity required before readers, writers, or configs assume migration completion.
- `backsliding_control`: new usage is blocked, warned, or explicitly exception-checked.
- `dependency_optionality`: retired dependencies are marked optional or removed from fail-closed checks, and turndown is staged with deflection behavior verified.
- `domain_dns_retirement`: domain ownership, zone presence, nameserver state, direct resolver results, TTL/cache recovery, and hidden dependents are checked before DNS changes.
- `retirement_check`: disable-before-delete, watch-window, code, config, data, credentials, alerts, runbooks, docs, and cost artifacts are removed or retained with an explicit reason.

## Red Flags - Stop And Rework

- A deprecation warning has no replacement, deadline, or telemetry.
- New users can still copy old examples and add fresh dependencies.
- Migration success is counted by emails sent rather than usage removed.
- Removal happens before dark traffic, jobs, support tools, and external clients are checked.
- A globally turned-down dependency is still treated as required by a dependent serving path.
- A domain is marked unused because one management tool cannot see its zone file.
- The old system keeps alerts, credentials, and costs after "retirement".

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Announcing instead of migrating | Provide tooling, examples, and maintained batches. |
| Relying only on static search | Add runtime telemetry for dynamic dependents. |
| Ignoring backsliding | Block new usage while old usage is removed. |
| Stopping at code deletion | Retire operational, data, access, and cost surfaces too. |
