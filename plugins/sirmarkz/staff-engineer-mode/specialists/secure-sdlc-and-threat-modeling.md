---
name: secure-sdlc-and-threat-modeling
description: "Use when features need threat models, trust boundaries, abuse cases, control tests, or residual-risk records"
---

# Secure SDLC And Threat Modeling

## Iron Law

```
NO SECURE DESIGN DECISION WITHOUT TRUST BOUNDARIES, DATA FLOWS, THREATS, CONTROLS, AND TESTS
```

If threats do not map to controls and verification, the decision is not actionable.

## Overview

Produces a trust-boundary and data-flow map, an abuse-case table, a control mapping with verification for each high-risk control, and a residual-risk register with explicit user acceptance and expiry. Residual-risk register fields follow the shared risk-register format and risk-acceptance lifecycle. Refuses to accept controls that cannot be tested, gated, or observed.

**Core principle:** model trust boundaries and abuse cases early, then turn threats into testable controls, explicit checks, and user-accepted residual risk.

## When To Use

- The user asks for threat modeling, secure design, abuse cases, secure SDLC, input validation, authorization decisions, or application security requirements.
- A change crosses trust boundaries, handles sensitive data, exposes an interface, adds privileged operations, or changes operational access.
- A design needs security acceptance criteria before implementation or launch.
- The user asks what attackers can abuse or what controls must exist.

## When Not To Use

- The main topic is build provenance, artifact signing, dependency inventory, or deployment admission; use `software-supply-chain-security` instead.
- The main topic is identity, secrets, cryptography lifecycle, or access lifecycle; use `identity-and-secrets` or `cryptography-and-key-lifecycle` instead.
- The main topic is LLM prompt, tool, or retrieval abuse; use `llm-application-security` instead.
- The request is broad legal/compliance program management; out of scope unless reframed as engineering controls.

## Info To Gather

- Current work phase, next decision, what is known, and assumptions where details are missing.
- Actors, identities, roles, trust boundaries, data flows, assets, and deployment surfaces.
- Data classification, sensitive fields, privacy constraints, logging/telemetry handling, and retention.
- Entry points, APIs, background jobs, admin paths, operational access, and third-party integrations.
- Server-side outbound request paths such as fetchers, webhooks, callbacks, link previews, imports, and URL-based integrations.
- Abuse cases, attacker goals, known vulnerability classes, dependency assumptions, and misuse paths.
- Existing controls, tests, self-checks, scanning results, incidents, and residual risks.

## Workflow

1. **Map the system.** Identify actors, assets, trust boundaries, data flows, privileged paths, and externally reachable surfaces.
2. **Classify data and operations.** Mark sensitive data, destructive operations, admin actions, and integrity-critical decisions.
3. **List abuse cases.** Write what an attacker or malicious/buggy client tries to accomplish and what component might fail.
4. **Apply a threat frame.** Use spoofing, tampering, repudiation, disclosure, denial, privilege elevation, or equivalent categories to avoid blind spots.
5. **Map controls.** Assign authentication, authorization, validation, output handling, rate limits, audit, secrets handling, encryption, and isolation controls.
6. **Constrain outbound requests.** For server-side fetchers, webhooks, callback URLs, or imports, define destination allowlists where feasible, DNS/IP rebinding checks, private and metadata address blocking, redirect policy, egress controls, timeout, size, content-type limits, and audit fields.
7. **Map detection needs.** For high-risk abuse cases, state the detection hypothesis, telemetry or audit data needed, alert or review route, and runbook owner. Route detailed signal design to `observability-and-alerting` when detection coverage is central.
8. **Make controls testable.** Define unit/integration/security tests, self-checks, runtime monitors, or operational checks for each high-risk control.
9. **Record residual risk.** State compensating control, expiry, acceptance condition, and explicit user risk acceptance using the shared risk-register, risk-acceptance, and compensating-control formats.
10. **Route specialized surfaces.** Identity/secrets, supply chain, LLM, tenant isolation, and vulnerability remediation go to their specialist skills when central.

## Synthesized Default

Use lightweight threat modeling tied to secure SDLC checks: trust-boundary map, abuse cases, control mapping, test plan, and residual-risk register using the shared risk-register format and risk-acceptance lifecycle. Prefer controls that are enforced in code, configuration, self-checks, runtime checks, or deployment checks over prose-only rules.



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

- Low-risk internal changes can use a small abuse-case checklist if no trust boundary, data sensitivity, or privileged operation changes.
- High-risk financial, privacy, safety, or admin paths need deeper checks and explicit user risk acceptance using the shared risk-acceptance lifecycle.
- Emergency fixes may document the minimal threat decision first and complete residual-risk mapping immediately after mitigation.
- Legal/compliance requirements can constrain controls, but this skill remains focused on engineering implementation and records.

## Response Quality Bar

- Lead with the threat-model decision, abuse-case table, control gap, or residual-risk register requested.
- Cover trust boundaries, actors, data flows, privileged paths, abuse cases, control mapping, verification, and residual responsibility before optional security breadth.
- Make recommendations actionable with control points, tests or self-checks, stop criteria, compensating controls per the shared compensating-control format, and expiry where relevant.
- Name the details to inspect, such as architecture/data-flow diagrams, auth paths, sensitive data stores, logs, deployment checks, security tests, and runtime checks; do not state details you have not seen.
- Stay technology-agnostic by default: do not introduce provider, product, framework, database, protocol, or command names unless the user supplied them or explicitly requested tool-specific guidance.
- Stay inside secure design and threat modeling. Use identity, supply-chain, tenant, LLM, or vulnerability skills only when the prompt makes that specialist surface central.
- Be concise: avoid generic vulnerability category lists and prefer system-specific abuse-case and control tables.

## Required Outputs

- Output shape: render the matching shared template headings or tables in the reply, or use the same shape.
- Trust-boundary and data-flow map.
- Threat and abuse-case table.
- Security requirements and control mapping.
- Server-side outbound request and egress-control decision where URLs, callbacks, webhooks, or external fetches exist.
- Security detection and audit requirements for high-risk abuse cases.
- Verification plan for controls.
- Residual-risk register with explicit user acceptance and expiry using the shared risk-register format and risk-acceptance lifecycle.
- Sensitive-data and logging decision.
- Follow-up checks for identity, supply-chain, tenant, LLM, or vulnerability work.

## Checks Before Moving On

- `boundary_check`: actors, trust boundaries, data flows, and privileged paths are explicit.
- `threat_coverage`: high-risk abuse cases map to controls.
- `outbound_request_control`: server-side URL fetching and callback paths have destination, redirect, network, timeout, size, and audit controls.
- `detection_route`: high-risk abuse cases define the telemetry, audit event, alert, or review path that would show attempted or successful abuse.
- `verification_check`: every high-risk control has a test, self-check, runtime check, or source to inspect.
- `data_handling`: sensitive data storage, transmission, logging, and retention behavior is addressed.
- `risk_responsibility`: residual risks have explicit user acceptance, expiry, and compensating control using the shared risk-register, risk-acceptance, and compensating-control formats.

## Red Flags - Stop And Rework

- The threat model lists generic vulnerability categories without system-specific abuse cases.
- Controls are stated but not testable.
- Admin or operational access is ignored.
- Sensitive data appears in logs, traces, errors, or analytics without controls.
- Residual risks have no user acceptance or expiry.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Starting from checklists | Start from trust boundaries and abuse cases. |
| Treating security as a final checkpoint | Add controls to requirements, code, tests, release, and operations. |
| Focusing only on external attackers | Include insider, compromised credential, confused deputy, and abusive tenant paths. |
| Leaving controls as prose | Tie controls to tests, checks, or source records. |
