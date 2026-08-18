---
name: mobile-release-engineering
description: "Use when planning mobile rollouts needing staged release, stability checks, offline behavior, or kill switches"
---

# Mobile Release Engineering And Stability

## Iron Law

```
NO BROAD MOBILE ROLLOUT WITHOUT STABILITY BUDGETS, SEGMENTED TELEMETRY, HALT CRITERIA, AND FORWARD-FIX PLAN
```

If the release cannot be halted or repaired under app-store/client constraints, do not widen exposure.

## Overview

Mobile releases are hard to roll back, so stability checks must be conservative before broad rollout.

**Core principle:** use staged rollout, crash/hang budgets, device/OS segmentation, startup/offline checks, privacy-safe telemetry, and forward-fix plans.

## When To Use

- The user is planning, changing, or reviewing a native mobile release train, staged rollout, phased release, crash-free users/sessions, hang rates, startup, offline behavior, mobile telemetry, or app-store release risk.
- A mobile app release could affect stability across devices, OS versions, networks, or app versions.
- A mobile rollout needs thresholds to continue, halt, or forward-fix.
- Client upgrade lag or rollback limits change release strategy.

## When Not To Use

- The request is responsive web or browser performance; use `web-release-gates` instead.
- The issue is backend-only latency or availability; use `performance-and-capacity` or `slo-and-error-budgets` instead.
- The work is mobile product strategy, acquisition, store listing optimization, or UX roadmap.
- The question is general CI check policy without mobile release constraints; use `testing-and-quality-gates` instead.

## Info To Gather

- Current work phase, next decision, what is known, and assumptions where details are missing.
- Platforms, release train, app versions, staged rollout percentages, and store review constraints.
- Stability metrics: crash-free users/sessions, hang rate, startup failures, fatal/non-fatal error rate, and watchdog events.
- Device/OS/app-version/network/account-policy segmentation and known high-risk cohorts.
- Critical journeys, offline behavior, sync/data-loss risk, and backend compatibility.
- UI entry points, feature prominence, deep links, notifications, or defaults that can increase use of an existing path without changing its implementation.
- Backend response normalization, environment target selection, remote config compatibility, local data migrations, and app-version adoption lag that can keep a bad state after a server rollback.
- Telemetry fields, privacy controls, symbolication/deobfuscation, and alerting thresholds.
- Rollback, halt, kill switch, remote config, and forward-fix options.

## Workflow

1. **Define mobile SLIs.** Use crash-free users/sessions, hang rate, startup success, and critical journey success.
2. **Segment the rollout.** Check by platform, app version, device class, OS version, geography/network, account policy, entitlement, or managed cohort where risk warrants it.
3. **Set staged thresholds.** Define metrics and sample-size requirements for each widening step, including client-exposure or UI-prominence changes that can create a backend or feature-usage surge.
4. **Use calibrated stability checks.** Derive crash-free, hang, startup, and journey thresholds from the current release and cohort baselines, user-impact or reliability targets, repair latency, traffic and adoption shape, sample size, and uncertainty. If local budgets are missing, label proposed thresholds and windows as provisional hypotheses and state the evidence needed to replace them; do not copy universal crash-free percentages, relative-regression limits, or fixed bake times across products.
5. **Check compatibility.** Verify backend, API, schema, feature flag, config, and environment-target compatibility with old and new app versions. Include response normalization, stale remote config, client-held state, and local data migrations so server rollback does not hide a client crash or startup loop.
6. **Plan offline and sync behavior.** Test intermittent network, stale config, retry, conflict, and data-loss scenarios.
7. **Protect privacy.** Avoid sensitive data in crash reports, logs, breadcrumbs, and custom keys.
8. **Define halt/repair.** Decide when to halt rollout, disable features, revert server flags, purge or repair client-visible state, or submit a forward fix.
9. **Monitor long tail.** Track old versions and slow adoption after the main rollout completes.

## Synthesized Default

Use staged mobile rollout with crash-free, hang, startup, and critical-journey budgets as release checks. Account for slow upgrade curves and limited rollback by keeping kill switches, compatibility windows, and forward-fix paths ready.



## Exceptions

- Emergency security or compliance fixes may move faster, but staged telemetry and rollback/forward-fix criteria still apply.
- Very small internal distributions can use lighter checks if users and devices are known.
- Some app-store constraints force forward-fix rather than rollback; document this before broad rollout.
- Privacy constraints may limit telemetry detail; preserve enough aggregate signal to detect regressions.

## Response Quality Bar

- Lead with the staged rollout decision, halt criteria, or stability budget requested.
- Cover crash-free, hangs, startup, critical journey, segmentation, and repair path before optional mobile release topics.
- Include numeric stability thresholds, measurement windows, minimum sample or confidence, and their derivation from local baselines and impact tolerances; label unsupported values as provisional hypotheses.
- Make recommendations actionable with checks, stop conditions, and forward-fix or kill-switch actions where relevant.
- Name the details to inspect, such as crash-free sessions/users, OS/device cohorts, sample sizes, app versions, and telemetry readiness; do not state details you have not seen.
- Stay technology-agnostic by default: do not introduce provider, product, framework, database, protocol, or command names unless the user supplied them or explicitly requested tool-specific guidance.
- Stay inside mobile release risk. Mention backend/API/config compatibility only where it affects client rollout safety.
- Be concise: avoid generic mobile-release background and prefer compact rollout tables.

## Required Outputs

- Output shape: render the matching shared template headings or tables in the reply, or use the same shape.
- Mobile release train and staged rollout plan.
- Crash-free users/sessions, hang/ANR, startup, and critical-journey budgets with numeric thresholds, measurement windows, minimum sample or confidence, baseline, impact rationale, and recalibration trigger.
- Device/OS/app-version/account-policy segmentation plan.
- Client-exposure and feature-usage surge check for new entry points, defaults, notifications, or UI prominence changes.
- Backend/API/config compatibility plan.
- Environment target validation for production, pre-production, sandbox, and test backends or dependency tiers.
- Server-client compatibility plan covering response normalization, stale config, client-held state, local migrations, and adoption lag.
- Offline/sync test and telemetry plan.
- Halt, rollback, kill-switch, and forward-fix criteria.
- Privacy-safe mobile telemetry checklist.

## Checks Before Moving On

- `stability_budget`: crash-free, hang, startup, and critical-journey thresholds are derived from local baselines and impact tolerance, with windows, minimum signal, uncertainty, and a recalibration trigger.
- `segment_check`: device, OS, app version, network, account policy, entitlement, and managed-cohort segmentation is considered.
- `compatibility_check`: backend, API, config, and old-version compatibility are addressed.
- `exposure_load_check`: client entry-point, default, notification, or UI-prominence changes have expected usage, backend capacity, and critical-journey failure signals before broad exposure.
- `environment_target_check`: release artifacts point at the intended backend and dependency tiers before broad rollout.
- `server_client_state`: response normalization, stale config, client-held state, local migrations, and adoption lag are covered before broad rollout.
- `halt_fix_check`: rollout halt, kill switch, rollback, or forward-fix path is explicit.
- `privacy_check`: crash/log telemetry avoids sensitive data and has symbolication/debuggability path.

## Red Flags - Stop And Rework

- Release goes to 100 percent before stability metrics have sample size.
- Only aggregate crash rate is watched; device, OS, account-policy, or managed cohorts are ignored.
- Backend changes break older app versions.
- Server rollback is assumed to repair client-held state, local migrations, or cached config without verification.
- Crash reports include sensitive data.
- Release thresholds are copied from another product or generic guidance without local baseline, cohort, sample, uncertainty, or repair-time evidence.
- Rollback is assumed even though client distribution cannot force downgrade.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Treating mobile like web deploys | Account for store review, upgrade lag, and rollback limits. |
| Aggregate stability only | Segment by platform, device, OS, app version, and cohort. |
| Ignoring offline | Test sync, retry, stale config, and conflict behavior. |
| No forward-fix plan | Prepare kill switches, server flags, and patched release path. |
