---
name: feature-flag-lifecycle
description: "Use when feature flags need lifecycle decisions: expiry, orphan detection, debt scoring, cleanup, or removal"
---

# Feature Flag Lifecycle

## Iron Law

```
EVERY LIVE FLAG HAS AN EXPIRY, SAFE FALLBACK, AND REMOVAL PLAN
```

A flag without all three is orphan debt. Orphan flags become dead branches, contradictory defaults, and stale kill switches that nobody dares pull during an incident.

## Overview

Produces a flag inventory with category and expiry per flag, an orphan report for flags whose features no longer exist, and a removal plan with rollback for each retiring flag. Refuses to count a feature as shipped while a flag still controls it.

**Core principle:** every live flag is unfinished work. After a rollout completes, the flag, its branches, and its config rows are decision debt that compounds until someone explicitly removes them.

## When To Use

- The user is deciding how a feature flag should be created, categorized, expired, cleaned up, inventoried, retired, or sunset.
- The user asks to inventory existing flags, assess flag debt, or set removal checks.
- A rollout has completed and the flag that gated it is still live.
- An incident exposed a flag whose intended behavior has no current fallback or removal rule.
- You ask how to stop accumulating flag debt or how to set expiry policy per flag class.
- The agent is being asked to add a new flag and the existing flag inventory and removal pattern need to be checked first.
- A code search reveals branches gated by flags that were not declared in any registry or are not referenced from production config.

## When Not To Use

- A change is mid-rollout and the question is staging, exposure rings, canary metrics, stop criteria, or rollback; use `progressive-delivery`.
- A flag itself is being changed as a configuration value with safety implications; use `configuration-and-automation-safety`.
- Generic dead-code or dependency cleanup with no flag-specific gating; use `dependency-and-code-hygiene`.
- The flag is an A/B experiment treatment under active analysis; use `experimentation-and-metric-guardrails`.
- The change is an org-level rule for AI-assisted code that adds flags it never removes; use `ai-coding-governance`.
- The work is broad release readiness across multiple surfaces; use `production-readiness-review`.

## Info To Gather

- Current work phase, next decision, what is known, and assumptions where details are missing.
- Flag inventory source: code search, flag-service registry, config files, environment overrides, and any per-tenant or per-location overrides.
- Per-flag metadata: name, declaration site, default value, current production value per environment, last evaluation timestamp where available, and number of branches behind the flag.
- Stated category for each flag: release toggle, experiment, operational kill switch, or permission/entitlement.
- Responsibility path per flag, fallback path, and user decision point for removal.
- Expiry policy by category and whether the flag has exceeded it.
- Rollout state: was the flag's launch completed, partially shipped, abandoned, or still ramping.
- Failure behavior: local fallback/default value used if flag evaluation fails, the behavior selected during a flag-service outage, and whether that behavior is safe for production.
- Branch coverage: which code paths execute under each value, whether both branches still have callers, and whether any tests exercise both branches.
- Tenants, locations, cohorts, or accounts pinned to non-default values and the reason for each pin.
- Incident history involving the flag, including any time the kill-switch path was exercised.

## Workflow

1. **Build the inventory.** Reconcile flags discovered in code, in the flag service or config registry, and in environment overrides. A flag that exists in only one of those sources is the first orphan signal.
2. **Classify each flag.** Assign exactly one category: release toggle (turns a shipped feature on), experiment (assigns variants for measurement), operational kill switch (disables a path under load or failure), permission or entitlement (controls access by tenant, plan, or role). A flag that resists classification is itself a finding.
3. **Set expiry by category.** Release toggles default to short expiry tied to rollout completion. Experiment flags default to short expiry tied to readout date. Operational kill switches default to longer expiry but require rehearsal cadence. Permission flags may be long-lived but still need renewal decisions and a safe fallback.
4. **Check default-value safety.** Record the local default/fallback value for each flag and the behavior chosen if flag evaluation or the flag service is unavailable. The fallback should select the safest known production behavior, not an accidental SDK or config default.
5. **Check rollout completion.** For each release toggle, confirm the rollout finished, the chosen value is the production default everywhere, and no environment still pins the legacy value without a documented reason.
6. **Detect orphans.** Flag the following as orphans: declared in code but absent from the registry; present in registry but unreferenced in code; expiry exceeded with no removal action; both branches identical or one branch unreachable; not evaluated in production within a defined freshness window where evaluation telemetry exists.
7. **Map flag-driven branches.** For each retiring flag, list the call sites, the branch each value selects, the tests that exercise each branch, and any config rows or per-tenant overrides that depend on the flag name.
8. **Plan removal.** For each flag scheduled for removal, define: target value (the branch that stays), the order of cleanup (default flip, override sweep, code removal, registry removal, config-row removal), the rollback path if removal regresses behavior, and the verification step that shows no caller still selects the removed branch.
9. **Stage the removal as a change.** Treat flag removal as a production change with separate blast radius and rollback. Use `progressive-delivery` as the internal lens when removal touches a tier-critical path.
10. **Score the flag debt.** Produce a scorecard: total flags by category, percent past expiry, percent without orphan count, oldest live flag age, and removal velocity over the last review period.
11. **Set the standing rule.** Establish per-category expiry defaults, a recurring renewal cadence, and the rule that adding a new flag requires declaring its category, expiry, and safe fallback value at creation time.

## Synthesized Default

Treat flags as time-bounded. Release toggles expire when the rollout completes. Experiment flags expire when the readout is accepted. Operational kill switches and permission flags may live longer but still require recurring renewal decisions. Removal is a planned change, not a cleanup ticket. The inventory is the source of truth and is reconciled against code on a defined cadence. Every flag must also document its fallback/default value and what production behavior occurs if flag evaluation fails.



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

- Long-lived operational kill switches may exceed standard expiry if the disabled path is rehearsed on a recorded cadence.
- Permission or entitlement flags tied to billing, plan, or regulatory access may be effectively permanent; they are not orphans but still need renewal decisions, fallback behavior, and test results.
- A flag protecting an in-progress migration may stay past its initial expiry with a renewed expiry date and completion condition.
- Emergency kill switches added during an incident may bypass the create-time expiry rule but must be classified, dated, and assigned a safe fallback value within the postmortem follow-up.

## Response Quality Bar

- Lead with the flag inventory, orphan list, removal plan, or flag-debt scorecard requested.
- Cover classification, responsibility, expiry, default-value safety, branch mapping, removal sequencing, and rollback before optional flag-system breadth.
- Make recommendations actionable with per-flag expiry, target value, fallback/default value, outage behavior, removal step, rollback step, and verification results.
- Name the details to inspect, such as code-search results, flag-registry export, environment overrides, evaluation telemetry where available, and incident history; do not state flag state from prose alone.
- Stay technology-agnostic by default: do not introduce provider, product, framework, database, protocol, or command names unless the user supplied them or explicitly requested tool-specific guidance.
- Stay inside post-rollout flag lifecycle. Route in-flight rollout sequencing, generic dead-code cleanup, experiment analysis, and config-change safety to the responsible specialist.
- Be concise: prefer compact inventory and removal tables over running narrative about flag philosophy.

## Required Outputs

- Flag inventory with name, category, declaration site, expiry, current production value per environment, fallback/default value if evaluation fails, outage behavior, and branch count.
- Orphan report listing flags with missing classification, exceeded expiry, unsafe or undocumented fallback, identical branches, unreachable branch, registry/code mismatch, or stale evaluation.
- Per-flag removal plan with target value, cleanup order, rollback path, and verification step for each flag scheduled for removal.
- Per-tenant, per-location, or per-cohort override list with reason and removal condition for each non-default pin.
- Branch map per retiring flag covering call sites, tests per branch, and dependent config rows.
- Flag-debt scorecard with totals by category, percent past expiry, percent without orphan count, oldest live flag age, and removal velocity.
- Standing rule: per-category expiry defaults, renewal cadence, and the create-time expiry/category/safe-fallback rule.
- Follow-up routes to progressive delivery, configuration safety, dependency hygiene, or experimentation as needed.

## Checks Before Moving On

- `flag_inventory_present`: a single inventory reconciles flags found in code, in the registry, and in environment overrides; mismatches are listed.
- `category_assigned`: every live flag has exactly one category from release, experiment, operational kill switch, or permission.
- `expiry_and_fallback`: every live flag has a dated expiry and safe fallback; any exception is recorded with renewed date and reason.
- `default_value_safety`: every live flag records the fallback/default value used when evaluation fails and the production behavior during a flag-service outage.
- `orphan_report`: orphan criteria are evaluated and the resulting flags are listed with the matching criterion per flag.
- `removal_plan_per_retiring_flag`: each flag scheduled for removal has target value, cleanup order, rollback path, and verification step.
- `branch_map`: retiring flags have a call-site list and a per-branch test list; unreachable or untested branches are flagged.
- `debt_scorecard`: scorecard covers totals by category, percent past expiry, percent without orphan count, oldest live flag age, and removal velocity.

## Red Flags - Stop And Rework

- A flag has no recorded expiry and no safe fallback, and you treat this as normal.
- A flag has no documented fallback/default value, so a flag-service outage could silently choose the wrong behavior.
- The rollout that created a flag completed months ago but the legacy branch still has callers and the flag is still evaluated in production.
- The flag registry and the code disagree about which flags exist, and reconciliation has no response path.
- An operational kill switch has never been exercised and no rehearsal exists, so its real behavior is unknown.
- Both branches of a flag are identical or one branch is unreachable, and the flag is still evaluated.
- A flag is removed by deleting code without sweeping per-tenant overrides, registry rows, or environment pins.
- New flags are being added by AI coding agents without recording category, expiry, or safe fallback at creation.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Treating "the rollout finished" as cleanup | Removal is a separate planned change with rollback and verification. |
| One global flag bucket | Classify by release, experiment, operational, or permission; each has a different lifecycle. |
| Responsibility is vague | Record the user decision point and the exact removal trigger. |
| Counting flags only in code | Reconcile code, registry, and environment overrides; mismatches are orphans. |
| Ignoring flag-evaluation failure | Record the fallback/default value and confirm outage behavior is safe. |
| Removing the code path but leaving the flag | Sweep registry rows, overrides, and dependent config in the same change. |
| Letting kill switches drift untested | Rehearse the disabled path or downgrade the switch to documented inert. |
| Adding new flags faster than removing them | Track removal velocity in the scorecard and require declared expiry before new-flag creation. |
