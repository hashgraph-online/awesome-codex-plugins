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

## Info To Gather

- Current work phase, next decision, what is known, and assumptions where details are missing.
- Deprecated thing, replacement, reason, deadline, risk, and support window.
- Static references, runtime calls, traffic, tenants, clients, jobs, dashboards, alerts, docs, and third-party dependents.
- Migration path, compatibility layer, dual-read/write needs, validation checks, and rollback/escape hatch.
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
7. **Migrate incrementally.** Move dependents in batches small enough to understand, test, and roll back; track progress with objective metrics.
8. **Disable before delete.** Stop or quarantine old runtime paths, watch for at least one representative business cycle, check dark traffic, jobs, support tools, and alerts, and keep an escape hatch until the old path stays quiet.
9. **Retire completely.** Remove runtime paths, data, config, credentials, dashboards, alerts, runbooks, docs, and cost artifacts after usage reaches the removal check; preserve required snapshots/exports with retention, and disposal date.

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

- Deprecation decision record with replacement, reason, and end state.
- Usage inventory with static and runtime checks.
- Dependent classification and migration batches.
- Migration guide, examples, validation, and escape hatch.
- Backsliding prevention controls.
- Enforcement, exception, and deadline policy.
- Disable-before-delete plan with watch-window results and disposal handling.
- Final retirement checklist.

## Checks Before Moving On

- `usage_inventory`: static and runtime usage are measured, or blind spots are named.
- `replacement_ready`: replacement path is documented, supported, and validated for representative dependents.
- `migration_batches`: dependents are grouped into maintained, linked, reversible batches.
- `backsliding_control`: new usage is blocked, warned, or explicitly exception-checked.
- `retirement_check`: disable-before-delete, watch-window, code, config, data, credentials, alerts, runbooks, docs, and cost artifacts are removed or retained with an explicit reason.

## Red Flags - Stop And Rework

- A deprecation warning has no replacement, deadline, or telemetry.
- New users can still copy old examples and add fresh dependencies.
- Migration success is counted by emails sent rather than usage removed.
- Removal happens before dark traffic, jobs, support tools, and external clients are checked.
- The old system keeps alerts, credentials, and costs after "retirement".

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Announcing instead of migrating | Provide tooling, examples, and maintained batches. |
| Relying only on static search | Add runtime telemetry for dynamic dependents. |
| Ignoring backsliding | Block new usage while old usage is removed. |
| Stopping at code deletion | Retire operational, data, access, and cost surfaces too. |
