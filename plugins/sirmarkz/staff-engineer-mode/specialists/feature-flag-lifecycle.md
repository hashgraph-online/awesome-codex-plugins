---
name: feature-flag-lifecycle
description: "Use when feature flags need lifecycle decisions: expiry, orphan detection, debt scoring, cleanup, or removal"
---

# Feature Flag Lifecycle

## Iron Law

```
EVERY TEMPORARY FLAG HAS A REMOVAL EXPIRY; EVERY LIVE FLAG HAS A SAFE FALLBACK, RESPONSIBILITY, AND REVIEW TRIGGER
```

A temporary flag without a removal expiry and plan becomes orphan debt. Long-lived operational or entitlement controls need a recurring review, tested fallback, and retirement condition even when they have no planned removal date.

## Overview

Produces a flag inventory with category and lifecycle date per flag, an orphan report for stale temporary flags, and a removal plan with rollback for each retiring flag. It distinguishes temporary release or experiment flags from maintained operational and entitlement controls.

**Core principle:** temporary flags are unfinished work and must be removed after their rollout, experiment, or migration. Long-lived controls are maintained production interfaces with review, fallback, test, and retirement obligations.

## When To Use

- The user is deciding how a feature flag should be created, categorized, expired, cleaned up, inventoried, retired, or sunset.
- The user asks to inventory existing flags, assess flag debt, or set removal checks.
- A rollout has completed and the flag that gated it is still live.
- An incident exposed a flag whose intended behavior has no current fallback, review trigger, or removal rule.
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
- Responsibility path per flag, fallback path, and user decision point for removal or renewal.
- Removal expiry for temporary categories; review cadence, next review, and retirement condition for long-lived categories.
- Rollout state: was the flag's launch completed, partially shipped, abandoned, or still ramping.
- Failure behavior: local fallback/default value used if flag evaluation fails, the behavior selected during a flag-service outage, and whether that behavior is safe for production.
- Branch coverage: which code paths execute under each value, whether both branches still have callers, and whether any tests exercise both branches.
- Tenants, locations, cohorts, or accounts pinned to non-default values and the reason for each pin.
- Incident history involving the flag, including any time the kill-switch path was exercised.

## Workflow

1. **Build the inventory.** Reconcile flags discovered in code, in the flag service or config registry, and in environment overrides. A flag that exists in only one of those sources is the first orphan signal.
2. **Classify each flag.** Assign exactly one category: release toggle (turns a shipped feature on), experiment (assigns variants for measurement), operational kill switch (disables a path under load or failure), permission or entitlement (shapes product availability by tenant, plan, or role). A flag that resists classification is itself a finding.
3. **Set the lifecycle by category.** Release toggles get a short removal expiry tied to rollout completion. Experiment flags get a removal expiry tied to the readout and cleanup date. Operational kill switches and permission or entitlement controls may be long-lived; give them a review cadence, next-review date, tested fallback, renewal decision, and retirement condition instead of inventing a removal expiry.
4. **Keep entitlement separate from authorization.** An entitlement flag may shape product availability, but a general or client-visible flag is not authoritative for security-sensitive access. Enforce access server-side from trusted identity and policy, define whether stale or conflicting flag state fails open or closed for the specific capability, and route identity-policy design to `identity-and-secrets`.
5. **Check default-value safety.** Record the local default/fallback value for each flag and the behavior chosen if flag evaluation or the flag service is unavailable. The fallback should select the safest known production behavior, not an accidental SDK or config default.
6. **Check rollout completion.** For each release toggle, confirm the rollout finished, the chosen value is the production default everywhere, and no environment still pins the legacy value without a documented reason.
7. **Detect orphans.** Flag the following as orphans: declared in code but absent from the registry; present in the registry but unreferenced in code; a temporary removal expiry or long-lived review date exceeded with no decision; both branches identical or one branch unreachable; not evaluated in production within a defined freshness window where evaluation telemetry exists.
8. **Map flag-driven branches.** For each retiring flag, list the call sites, the branch each value selects, the tests that exercise each branch, and any config rows or per-tenant overrides that depend on the flag name.
9. **Plan removal.** For each flag scheduled for removal, define: target value (the branch that stays), the order of cleanup (default flip, override sweep, code removal, registry removal, config-row removal), the rollback path if removal regresses behavior, and the verification step that shows no caller still selects the removed branch.
10. **Stage the removal as a change.** Treat flag removal as a production change with separate blast radius and rollback. Use `progressive-delivery` as the internal lens when removal touches a high-impact path.
11. **Score the flag debt.** Produce a scorecard: total flags by category, orphan count, percent of temporary flags past removal expiry, percent of long-lived flags past review, oldest overdue lifecycle date, and temporary-flag removal velocity over the last review period.
12. **Set the standing rule.** Establish temporary-category removal-expiry defaults, long-lived-category review cadence, and the rule that adding a flag requires its category, lifecycle date, responsibility, safe fallback, and retirement condition at creation time.

## Synthesized Default

Treat release, experiment, and migration flags as time-bounded. Operational kill switches and permission or entitlement flags may be long-lived production controls, but they require recurring review, fallback tests, responsibility, and a retirement condition. Entitlement state may shape availability but never replaces trusted server-side authorization for security-sensitive access. Removal is a planned change. Reconcile the authoritative inventory against code and overrides on a defined cadence, and document the behavior when evaluation fails.



## Exceptions

- Long-lived operational kill switches use a review date and recorded rehearsal cadence rather than a removal expiry when the capability remains required.
- Permission or entitlement flags tied to billing, plan, or access may be effectively permanent; they are not orphans when they have review decisions, fallback behavior, test results, and a retirement condition.
- A flag protecting an in-progress migration may stay past its initial expiry with a renewed expiry date and completion condition.
- Emergency kill switches added during an incident may bypass the create-time expiry rule but must be classified, dated, and assigned a safe fallback value within the postmortem follow-up.

## Response Quality Bar

- Lead with the flag inventory, orphan list, removal plan, or flag-debt scorecard requested.
- Cover classification, responsibility, lifecycle date, default-value safety, branch mapping, removal or review decision, and rollback before optional flag-system breadth.
- Make recommendations actionable with per-flag removal expiry or review date, target value, fallback value, outage behavior, removal or renewal step, rollback step, and verification results.
- Name the details to inspect, such as code-search results, flag-registry export, environment overrides, evaluation telemetry where available, and incident history; do not state flag state from prose alone.
- Stay technology-agnostic by default: do not introduce provider, product, framework, database, protocol, or command names unless the user supplied them or explicitly requested tool-specific guidance.
- Stay inside post-rollout flag lifecycle. Route in-flight rollout sequencing, generic dead-code cleanup, experiment analysis, and config-change safety to the responsible specialist.
- Be concise: prefer compact inventory and removal tables over running narrative about flag philosophy.
- Scale the artifact to the request: one flag needs its category, lifecycle date, fallback, responsibility, and removal or review decision; use the full inventory, orphan report, branch map, and debt scorecard only for a broader lifecycle audit.

## Required Outputs

- Output shape: render the matching shared template headings or tables in the reply, or use the same shape.
- Flag inventory with name, category, removal expiry or next-review date, retirement condition, responsibility, declaration site, current value per environment, fallback value, outage behavior, and branch count.
- Orphan report listing flags with missing classification, overdue removal or review, unsafe or undocumented fallback, identical branches, unreachable branch, registry/code mismatch, or stale evaluation.
- Per-flag removal plan with target value, cleanup order, rollback path, and verification step for each flag scheduled for removal.
- Per-tenant, per-location, or per-cohort override list with reason and removal condition for each non-default pin.
- Branch map per retiring flag covering call sites, tests per branch, and dependent config rows.
- Flag-debt scorecard with totals by category, orphan count, temporary flags past removal expiry, long-lived controls past review, oldest overdue lifecycle date, and temporary-flag removal velocity.
- Standing rule: temporary removal-expiry defaults, long-lived review cadence, and the create-time category/lifecycle/responsibility/safe-fallback/retirement rule.
- Entitlement boundary, when applicable: trusted server-side authorization source, stale/conflicting-state posture, and follow-up route to `identity-and-secrets`.
- Follow-up routes to progressive delivery, configuration safety, dependency hygiene, or experimentation as needed.

## Checks Before Moving On

- `flag_inventory_present`: a single inventory reconciles flags found in code, in the registry, and in environment overrides; mismatches are listed.
- `category_assigned`: every live flag has exactly one category from release, experiment, operational kill switch, or permission.
- `lifecycle_and_fallback`: temporary flags have a removal expiry; long-lived controls have a next-review date and retirement condition; every flag has a safe fallback and responsibility.
- `default_value_safety`: every live flag records the fallback/default value used when evaluation fails and the production behavior during a flag-service outage.
- `entitlement_authorization_boundary`: entitlement flags do not authorize security-sensitive access; trusted server-side identity/policy and stale or conflicting state behavior are explicit.
- `orphan_report`: orphan criteria are evaluated and the resulting flags are listed with the matching criterion per flag.
- `removal_plan_per_retiring_flag`: each flag scheduled for removal has target value, cleanup order, rollback path, and verification step.
- `branch_map`: retiring flags have a call-site list and a per-branch test list; unreachable or untested branches are flagged.
- `debt_scorecard`: scorecard covers category totals, orphan count, overdue removal and review percentages, oldest overdue lifecycle date, and temporary-flag removal velocity.

## Red Flags - Stop And Rework

- A temporary flag has no removal expiry, or a long-lived control has no next review and retirement condition.
- A flag has no documented fallback/default value, so a flag-service outage could silently choose the wrong behavior.
- The rollout that created a flag completed months ago but the legacy branch still has callers and the flag is still evaluated in production.
- The flag registry and the code disagree about which flags exist, and reconciliation has no response path.
- An operational kill switch has never been exercised and no rehearsal exists, so its real behavior is unknown.
- Both branches of a flag are identical or one branch is unreachable, and the flag is still evaluated.
- A flag is removed by deleting code without sweeping per-tenant overrides, registry rows, or environment pins.
- New flags are being added without category, responsibility, lifecycle date, retirement condition, or safe fallback at creation.
- A client-visible or general feature flag is treated as authoritative authorization for security-sensitive access.

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
| Applying one expiry rule to every category | Give temporary flags removal dates and long-lived controls review dates, fallback tests, and retirement conditions. |
| Adding temporary flags faster than removing them | Track temporary-flag removal velocity and require a removal expiry at creation. |
