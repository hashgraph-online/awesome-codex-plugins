---
name: cryptography-and-key-lifecycle
description: "Use when certificates, signing keys, secrets, algorithms, or crypto material need rotation or migration planning"
---

# Crypto Agility And Cert Lifecycle

## Iron Law

```
EVERY KEY, CERT, AND ALGORITHM HAS AN EXPIRY DATE AND A TESTED REPLACEMENT PATH
```

If a certificate, key, algorithm, or trust root cannot be replaced safely on demand, the system is brittle. "Tested" means the replacement path has been exercised at least once outside an emergency, not just documented.

## Overview

Cryptography fails operationally when keys, certificates, algorithms, and trust roots cannot be inventoried or changed before a deadline.

**Core principle:** keep cryptographic dependencies discoverable, maintained, renewable, replaceable, monitored, and tested before expiry or algorithm transition becomes an incident.

## When To Use

- The user asks about certificate expiry, key rotation, cryptographic algorithm transition, trust-chain changes, renewal automation, or cryptographic agility.
- A service depends on certificates, keys, signing, encryption, trust roots, or cryptographic policies that can expire or become deprecated.
- Rotation, revocation, renewal, or algorithm migration could break clients, jobs, devices, or partner integrations.
- You need checks that cryptographic material is inventoried, expiring, monitored, and replaceable.

## When Not To Use

- The main topic is identity authorization, secret storage, or service access policy; use `identity-and-secrets` instead.
- The main topic is artifact provenance or release signing; use `software-supply-chain-security` instead.
- The main topic is secure design broadly; use `secure-sdlc-and-threat-modeling` instead.
- The request is abstract cryptographic research with no engineering lifecycle decision.

## Info To Gather

- Current work phase, next decision, what is known, and assumptions where details are missing.
- Inventory of certificates, keys, algorithms, trust roots, consumers, expiry dates, and renewal paths.
- Usage context: authentication, encryption, signing, verification, storage, transport, or partner integration.
- Rotation process, automation, manual steps, confirmation, access logs, and emergency revocation path.
- Client and dependency compatibility, trust-store update path, fallback behavior, and rollback or roll-forward limits.
- Monitoring, alert thresholds, test environment coverage, and prior expiry or rotation incidents.
- Deprecation deadline, transition target, exception and compensating controls.

## Workflow

1. **Inventory dependencies.** Find cryptographic material, algorithms, trust roots, consumers, and expiry or deprecation dates.
2. **Classify use.** Separate authentication, confidentiality, integrity, signing, verification, and storage use cases.
3. **Assess agility.** Determine whether each dependency can be renewed, rotated, revoked, or replaced without coordinated outage.
4. **Check compatibility.** Test old/new material and algorithm combinations with representative clients and workloads.
5. **Automate renewal carefully.** Use monitored renewal paths with alerting, audit, and failed-renewal response. Trigger renewal well before expiry — for example, at roughly two-thirds of the credential's lifetime — so that a single failed renewal cycle has time to be detected and retried before the credential expires.
6. **Rotate without coordinated downtime.** Default to a dual-credential overlap sequence: issue the new credential, configure verifiers to accept both old and new, migrate producers and clients to the new credential, verify zero traffic uses the old, then revoke. The verify-zero-old-traffic check is what makes the rotation zero-downtime; rotations that skip it convert routine rotation into an outage.
7. **Plan transitions.** Define overlap, dual support, rollout order, client migration, and retirement checks for deprecated algorithms or trust roots.
8. **Prepare emergency response.** Document revocation, compromise response, rollback or roll-forward, and communication path.
9. **Close exceptions.** Track unsupported material with expiry, risk, and compensating controls.

## Synthesized Default

Use a cryptographic inventory, expiry monitoring, tested rotation, dual-support transition windows, compatibility checks, emergency revocation plan, and exception register. Prefer designs where cryptographic material can be replaced independently of full application redeploys.



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

- Emergency compromise response may skip ordinary rollout windows, but must preserve audit, and recovery results.
- Legacy clients may require overlap windows; keep them time-bound with usage telemetry and migration checks.
- Low-risk development material can use lighter monitoring if isolated from production trust paths.

## Response Quality Bar

- Lead with the lifecycle risk, rotation plan, transition decision, or expiry blocker requested.
- Cover inventory, responsibility, expiry, rotation, compatibility, monitoring, emergency revocation, transition windows, and exceptions before optional cryptographic detail.
- Make recommendations actionable with dates, checks, alert thresholds, compatibility tests, and retirement criteria where relevant.
- Name the details to inspect, such as inventory, expiry data, consumer list, rotation test output, renewal logs, alert rules, and exception records; do not state details you have not seen.
- Stay technology-agnostic by default: do not introduce provider, product, framework, database, protocol, or command names unless the user supplied them or explicitly requested tool-specific guidance.
- Stay inside cryptographic lifecycle. Use identity, supply-chain, or secure-design skills only when those surfaces drive the main decision.
- Be concise: prefer inventory and transition matrices over broad cryptography explanation.

## Required Outputs

- Cryptographic dependency inventory.
- Consumer, expiry, and renewal map.
- Rotation and renewal plan.
- Compatibility and dual-support test plan.
- Algorithm or trust-root transition plan.
- Monitoring and alert policy for expiry and failed renewal.
- Emergency revocation and compromise response.
- Exception register with expiry, and compensating control.

## Checks Before Moving On

- `inventory_owned`: cryptographic material, algorithms, trust roots, consumers, and expiry dates are visible.
- `rotation_test`: renewal, rotation, or replacement is tested for representative consumers.
- `compatibility_window`: old/new compatibility and overlap duration are explicit.
- `expiry_monitoring`: expiry and failed-renewal alerts have a response path.
- `transition_check`: deprecated algorithms or trust roots have migration and retirement criteria.

## Red Flags - Stop And Rework

- Certificates are discovered only when expiry alerts fire.
- A key can be created but not rotated or revoked safely.
- Old and new trust paths are never tested together.
- Manual renewal depends on one person remembering a calendar date.
- Deprecated algorithms remain because clients are unknown.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Inventory only at issuance | Continuously track consumers, and expiry. |
| Rotation without compatibility | Test old/new overlap before rollout. |
| Renewal without alerting | Monitor expiry and failed automation. |
| Permanent exceptions | Require risk, and retirement check. |
