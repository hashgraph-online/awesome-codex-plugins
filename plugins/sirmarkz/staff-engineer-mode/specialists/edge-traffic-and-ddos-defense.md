---
name: edge-traffic-and-ddos-defense
description: "Use when public-edge rate limits, bot controls, origin isolation, abuse traffic, or DDoS response need design"
---

# Edge Traffic And Denial-Of-Service Defense

## Iron Law

```
NO PUBLIC EDGE EXPOSURE WITHOUT ORIGIN PROTECTION, RATE POLICY, TELEMETRY, AND RULE ROLLBACK
```

If attackers can bypass the edge and hit origin directly, edge defense is incomplete.

## Overview

Public traffic must be filtered and shaped before abusive load reaches expensive systems.

**Core principle:** layer volumetric, protocol, application, identity, and origin protections with telemetry and reversible rules.

## When To Use

- The user asks about public edge traffic, denial-of-service risk, edge caching, application-layer filtering, bot defense, abuse throttling, origin protection, traffic steering, or edge load shedding.
- Public traffic spikes, abusive clients, or bots threaten availability or cost.
- A service needs rate limits or request filtering before work reaches application dependencies.
- The user asks how to protect origins or global entry points.

## When Not To Use

- The issue is internal service retry/backpressure; use `dependency-resilience` instead.
- The request is normal capacity growth without abusive traffic; use `performance-and-capacity` instead.
- The main topic is application authorization; use `secure-sdlc-and-threat-modeling` or `identity-and-secrets` instead.
- The work is internal service mesh/routing; use `internal-service-networking` instead.

## Info To Gather

- Current work phase, next decision, what is known, and assumptions where details are missing.
- Public endpoints, routes, origins, DNS/traffic steering, identity signals, and bypass paths.
- Traffic patterns, known attacks, request costs, tenant/customer priorities, and false-positive tolerance.
- Existing edge rules, rate limits, bot controls, challenges, allow/deny lists, and emergency controls.
- Origin capacity, dependency limits, caching behavior, and overload thresholds.
- Telemetry: rule ID, action, request ID, route, identity/tenant, status, latency, and origin result.
- Rule responsibility, rollout mode, dry-run capability, expiry, refresh cadence, and rollback path.

## Workflow

1. **Map the edge.** Identify public entry points, origins, bypass paths, and expensive downstream operations.
2. **Separate attack layers.** Distinguish volumetric, protocol, application-layer, credential-stuffing, scraping, and tenant-abuse patterns.
3. **Protect origin.** Restrict direct access, require edge-origin authentication where possible, and remove bypass routes.
4. **Shape traffic early.** Apply rate limits, quotas, challenges, caching, prioritization, and load shedding before expensive work.
5. **Specify rate rules.** For each protected route or route class, name the key, window, threshold, and breach action such as 429, deny, or challenge.
6. **Tune false positives.** Use dry-run or staged enforcement for new rules when possible; define false-positive signals.
7. **Instrument decisions.** Log rule, action, identity, route, request ID, and origin outcome.
8. **Plan emergency controls.** Predefine who can apply broad blocks, how long they last, and how they are checked.
9. **Expire rules.** Temporary mitigations need expiry, rollback, and post-event analysis.

## Synthesized Default

Use layered edge protection: origin isolation, traffic steering, caching where correct, rate limits, bot/abuse controls, DDoS response planning, edge telemetry, staged rule rollout, and reversible emergency mitigations.



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

- During active denial-of-service events, temporary broad blocking may be acceptable if checked and expired quickly.
- Internal-only services can use lighter public-edge controls if no public route exists.
- High-value customers or critical traffic may need priority lanes or separate rate policies.
- Some rules cannot run in dry-run mode; compensate with narrow scope and fast rollback.

## Response Quality Bar

- Lead with the edge risk, denial-of-service or abuse policy, origin-bypass fix, or emergency mitigation requested.
- Cover origin isolation, route cost, identity-aware limits, bot/abuse controls, false-positive handling, edge telemetry, staged enforcement, rollback, and expiry before optional edge breadth.
- Make recommendations actionable with rule scopes, thresholds, dry-run/enforce stages, rollback commands, verification windows, and emergency authority where relevant.
- Include a compact rate-rule table for public APIs: route or route class, identity key (IP/session/user/tenant/API key), window, threshold, breach action, rollout mode, user-confirmed exception, and rollback.
- Name the details to inspect, such as DNS/origin exposure, route inventory, request rates, tenant/user identity, rule logs, false-positive samples, origin saturation, and mitigation history; do not state details you have not seen.
- Stay vendor/product-agnostic, but DO name the standard edge primitives by category: rate-limit breach action (e.g., 429, deny, challenge), bot-detection mechanism (challenge, fingerprint, behavioral, reputation-based) with false-positive handling, origin-shielding mechanism (edge-IP allowlist, signed origin headers, private connectivity, mutual-authentication transport) with a verification step, and load-shedding criteria with priority preservation (e.g., shed unauthenticated/low-priority before authenticated critical).
- Stay inside edge traffic and DDoS defense. Route broader capacity or abuse-product policy only when they materially block defense decisions.
- Be concise: avoid generic DDoS background and prefer compact edge maps, rule tables, and runbooks.

## Required Outputs

- Edge architecture and origin-protection map.
- Denial-of-service, abuse, and rate-limit policy — include a per-route or per-route-class rate-limit table where every row names the identity key, window, threshold, and breach action (429/deny/challenge); each bot control names its mechanism AND false-positive handling; origin-shielding lists a mechanism AND a verification step; load-shedding states criteria AND which traffic is preserved by priority.
- Origin bypass remediation plan.
- False-positive review and rollout plan.
- Edge telemetry and alert requirements.
- Emergency mitigation runbook.
- Rule responsibility, expiry, and rollback plan.

## Checks Before Moving On

- `origin_check`: origins cannot be trivially bypassed from public networks.
- `rate_policy`: rate limits or abuse controls are tied to identity, route cost, and false-positive tolerance.
- `telemetry_check`: edge decisions include rule, action, route, identity/request context, and origin result.
- `rollback_check`: enforcement rules have rollout mode, and rollback path.
- `emergency_check`: broad mitigations have authority, expiry, and verification requirements.

## Red Flags - Stop And Rework

- Public clients can bypass edge controls and hit origin directly.
- Rate limits are global only and hurt good tenants before abusive traffic.
- Emergency block rules have no expiry.
- Edge logs cannot explain why a request was blocked.
- Rules are deployed broadly without rollback or user-confirmed exception.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| One giant block rule | Layer controls and scope them by route/identity/risk. |
| No origin isolation | Make bypass difficult or impossible. |
| Ignoring false positives | Use dry-run, staged enforcement, and review signals. |
| No edge telemetry | Log rule decisions and origin outcomes. |
