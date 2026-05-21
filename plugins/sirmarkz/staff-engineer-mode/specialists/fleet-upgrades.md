---
name: fleet-upgrades
description: "Use when runtime, platform, framework, client, service, or host upgrades span many versions or rollout waves"
---

# Fleet Upgrades And Version Skew Management

## Iron Law

```
NO FLEET UPGRADE WITHOUT INVENTORY, SUPPORT WINDOW, SKEW POLICY, COMPATIBILITY TESTS, AND ROLLOUT CHECKS
```

If you cannot see what versions exist and what combinations are supported, the upgrade plan is guessing.

## Overview

Fleet upgrades are compatibility projects spread across runtimes, control planes, clients, services, and operators.

**Core principle:** inventory support windows, define allowed skew, test mixed-version compatibility, stage rollout, and keep rollback or roll-forward paths ready.

## When To Use

- The user asks about fleet upgrades, runtime upgrades, platform upgrades, support windows, version skew, end-of-support, or mixed-version rollout.
- Many services, clients, jobs, workers, agents, nodes, or control-plane components must move over time.
- Old and new versions need to coexist safely during rollout.
- An upstream, community, or internal platform support deadline creates production risk.

## When Not To Use

- The work is a routine library update inside one repo; use `dependency-and-code-hygiene` instead.
- The main risk is build artifact reproducibility; use `release-build-reproducibility` instead.
- The main risk is exposed API compatibility; use `api-design-and-compatibility` instead.
- The main task is broad service retirement; use `migration-and-deprecation` instead.

## Info To Gather

- Current work phase, next decision, what is known, and assumptions where details are missing.
- Fleet inventory: components, versions, environments, criticality, support status, and local ownership info when available.
- Baseline runtime or platform drift, defects already fixed in newer baselines but still present in older ones, and exception expiry.
- Version-skew policy, compatibility matrix, upgrade order, and blocked combinations.
- Tests for mixed versions, client/server compatibility, data compatibility, and operational tooling.
- Rollout batches, maintenance windows, traffic exposure, rollback or roll-forward path, and freeze dates.
- Known deprecated features, removed behavior, config changes, and operator runbooks.
- Support-window communication plan: affected components or consumers, deadline, required consumer action, reminder cadence, and user-confirmed follow-up path.
- Exception list, expiry, risk, and compensating controls.

## Workflow

1. **Inventory the fleet.** List versions, support windows, baseline drift, criticality, local ownership info, and unknowns.
2. **Define allowed skew.** State which old/new combinations are supported during rollout and for how long.
3. **Communicate support deadlines.** Tell affected consumers when old versions leave support, what action they must take, and when reminders, follow-up, or enforcement start.
4. **Find breaking changes.** Check behavior, config, interfaces, data formats, tooling, and operational assumptions.
5. **Check compatibility.** Test mixed-version paths, upgrade order, downgrade or roll-forward behavior, and representative workloads.
6. **Batch rollout.** Move low-risk cohorts first, then critical paths with checks, user confirmation, and monitoring.
7. **Manage exceptions.** Track blockers with expiry, risk, compensating control, and the local details needed to close them.
8. **Update operations.** Refresh runbooks, alerts, dashboards, and local operating procedures for the new version.
9. **Close old paths.** Remove compatibility shims, stale versions, and exceptions after adoption is verified; keep baselines current enough that available fixes do not linger unnoticed.

## Synthesized Default

Use a support-window inventory, explicit version-skew policy, compatibility matrix, staged rollout, support-deadline communication plan, exception register, operational runbook update, and retirement check for old versions. Prefer proving mixed-version behavior before the first production batch.



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

- Emergency security upgrades may compress rollout stages, but still need compatibility risk decision, consumer notice if deadlines change, user confirmation, and rollback or roll-forward decision.
- Low-risk internal tools can use lighter checks if they are not production dependencies.
- Some upgrades cannot roll back safely; require stronger preflight tests and roll-forward criteria.

## Response Quality Bar

- Lead with the upgrade plan, skew decision, support-window risk, or blocker list requested.
- Cover inventory, support status, skew policy, compatibility tests, rollout batches, rollback or roll-forward, exceptions, consumer communication, and operations updates before optional detail.
- Make recommendations actionable with dates, checks, batch order, test results, consumer action requirements, and exception expiry where relevant.
- For end-of-support or support-window risk, include a short consumer communication timeline: announcement, deadline, required action from affected components or consumers, reminder cadence, and user-confirmed follow-up date.
- Name the details to inspect, such as version inventory, support deadlines, compatibility matrix, test output, rollout status, communication status, and runbook changes; do not state details you have not seen.
- Stay technology-agnostic by default: do not introduce provider, product, framework, database, protocol, or command names unless the user supplied them or explicitly requested tool-specific guidance.
- Stay inside fleet upgrade and version-skew management. Route dependency hygiene, API compatibility, or deprecation work only when that surface dominates.
- Be concise: prefer upgrade matrices and batch plans over broad migration prose.
- Emit upgrade order as a discrete labeled tier list before the time-phased rollout, not buried inside a weekly schedule.

## Required Outputs

- Fleet inventory with version, criticality, support status, and local ownership info when available.
- Baseline drift table showing current baseline, target baseline, available fixes not yet adopted, and exception expiry.
- Version-skew and compatibility matrix.
- Upgrade order as an explicit tier list (e.g., control plane → data plane / nodes → clients/operators), with one-line rationale per tier and the allowed skew range between tiers stated as a numeric window with breakage criteria.
- End-of-support / support-window communication plan with announcement date, final support date, affected consumers, required consumer action, reminder cadence, and follow-up or enforcement path.
- Rollout batches (waves) with progression criteria per wave.
- Mixed-version test plan and records requirements.
- Rollback or roll-forward plan stating both the procedure and the state-compatibility note (which prior state is restorable, which is not).
- Exception register with expiry, compensating control, and closure note.
- Operations update checklist.
- Old-version retirement check.

## Checks Before Moving On

- `inventory_complete`: supported, unsupported, unknown, and critical versions are visible.
- `baseline_freshness`: baseline drift, available fixes not yet adopted, and exception expiry are visible for maintained components.
- `skew_policy`: allowed mixed-version combinations and duration are explicit.
- `support_comms`: affected consumers, support deadline, required action, reminder cadence, and follow-up date are visible.
- `compatibility_test`: representative old/new paths are tested before broad rollout.
- `rollout_responsibility`: every batch has user confirmation, check, and halt criteria.
- `exception_expiry`: blocked components have risk, compensating control, expiry, and closure note.

## Red Flags - Stop And Rework

- The fleet inventory is based on guesses or stale spreadsheets.
- Old and new versions are assumed compatible without tests.
- Upgrade order ignores clients, jobs, agents, or operational tooling.
- Unsupported versions have no exception expiry, compensating control, or consumer communication deadline.
- Rollback is impossible but roll-forward criteria are not defined.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Version bump as task | Treat it as a compatibility and rollout project. |
| No skew policy | Define supported old/new combinations. |
| Silent support deadline | Announce the deadline, required consumer action, reminders, and enforcement path. |
| Ignoring operators | Update runbooks, alerts, and tooling. |
| Leaving old versions | Add retirement checks and cleanup. |
