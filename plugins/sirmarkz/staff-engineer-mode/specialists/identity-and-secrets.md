---
name: identity-and-secrets
description: "Use when designing human or workload access, scopes, credential lifetime, secret storage, or break-glass paths"
---

# Zero Trust Identity And Secrets

## Iron Law

```
NO ACCESS PATH WITHOUT IDENTITY, AUTHORIZATION, CREDENTIAL LIFETIME, AUDIT, AND REVOCATION
```

If credentials cannot be scoped, rotated, audited, or revoked, they should not protect production access.

## Overview

Identity is the control plane for human and workload power.

**Core principle:** authenticate explicitly, authorize least privilege, prefer short-lived credentials, isolate secrets, and audit high-risk actions.

## When To Use

- The user asks about identity, zero trust, service accounts, workload identity, federation, multi-factor access, secrets, keys, encryption, cryptography, or access control.
- A system grants human, service, admin, break-glass, tenant, or cross-environment access.
- Secrets appear in code, logs, CI, images, config, tickets, or operational workflows.
- A design needs key management, credential rotation, audit events, or least-privilege decisions.

## When Not To Use

- The request is general app threat modeling without identity/secrets focus; use `secure-sdlc-and-threat-modeling` instead.
- The main issue is artifact signing or build provenance; use `software-supply-chain-security` instead.
- The main issue is tenant data isolation; use tenant isolation.
- The request is staffing or access-program work without engineering implementation; out of scope.

## Info To Gather

- Current work phase, next decision, what is known, and assumptions where details are missing.
- Human identities, workload identities, roles, privileges, environments, tenants, and admin paths.
- Authentication factors, federation, session lifetime, device/context signals, and step-up requirements.
- Authorization model, permission granularity, default grants, just-in-time elevation, and break-glass process.
- Secrets, tokens, keys, certificates, storage locations, rotation cadence, expiry, and consumers.
- Service-call authentication coverage, credential expiry signals, rotation lead time, and response path when expiry approaches.
- Encryption needs, key responsibility, key separation, data classification, and long-lived confidentiality requirements.
- Activity logs, log retention, alerting, access recertification cadence, and revocation path.

## Workflow

1. **Inventory access paths.** Include humans, services, jobs, automation, support tools, emergency access, and third parties.
2. **Replace network trust.** Base access on identity, context, resource sensitivity, and explicit authorization, not location alone.
3. **Minimize privileges.** Scope permissions by action, resource, tenant, environment, and duration.
4. **Prefer workload identity and short-lived credentials.** Use managed identity where the runtime and resource share a trust domain; use workload identity federation when crossing platforms or organizations; use expiring tokens, rotation, revocation, and expiry signals over static long-lived secrets.
5. **Protect secrets and keys.** Keep them out of source, logs, images, and broad config; separate key administration from data access where risk warrants it.
6. **Design break-glass deliberately.** Require strong authentication, limited duration, justification, audit, and post-use verification.
7. **Use vetted cryptography.** Prefer standard protocols and managed primitives; do not invent algorithms or key-handling schemes.
8. **Audit and verify.** Emit access, privilege change, secret access, key use, and admin events with a user-visible verification path.

## Synthesized Default

Use zero-trust access with explicit identity, least privilege, workload identity for software, federation instead of copied secrets across trust boundaries, short-lived credentials, secure secret storage, strong human authentication, traceable break-glass, and vetted cryptography. Treat access as continuously verifiable, not granted once forever.



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

- Legacy systems may need compensating controls while static credentials are removed; require expiry, and rotation.
- Offline or embedded environments may require longer-lived secrets, but scope and revocation must be explicit.
- Very low-risk internal tools can use simpler access models if production data and privileged operations are absent.
- Long-lived confidentiality may require crypto-agility and post-quantum planning.

## Response Quality Bar

- Lead with the access model, secret-risk decision, migration plan, or blocker list requested.
- Cover identity boundaries, least privilege, credential lifetime, break-glass, audit, and cryptography before optional security breadth.
- Make recommendations actionable with permission scopes, rotation steps, audit events, stop criteria, and migration checks where relevant.
- Name the details to inspect, such as access inventories, service identities, secret locations, key rotation history, audit logs, and break-glass records; do not state details you have not seen.
- Stay technology-agnostic by default: do not introduce provider, product, framework, database, protocol, or command names unless the user supplied them or explicitly requested tool-specific guidance.
- Stay inside identity, secrets, and cryptography. Route privacy, supply-chain, or tenant isolation only when those are the central unresolved risk.
- Be concise: avoid generic zero-trust background and prefer compact access matrices, secret inventories, and migration checklists.

## Required Outputs

- Identity and access model.
- Human/service permission table with least-privilege decisions.
- Secret and key inventory with storage, rotation, expiry, and consumers.
- Authentication coverage and credential-expiry table with lead time, signal, owner path, and response.
- Break-glass and just-in-time access process.
- Audit event and access-recertification requirements.
- Cryptography decision record.
- Migration plan for overbroad or long-lived credentials.

## Checks Before Moving On

- `access_inventory`: human, workload, admin, emergency, and third-party access paths are listed.
- `least_privilege`: permissions are scoped by action/resource/environment/tenant and default-deny is addressed.
- `credential_lifetime`: secrets and tokens have storage, expiry, rotation, and revocation plan.
- `expiry_signal`: credentials, certificates, and tokens that can break production have expiry visibility and response lead time.
- `auth_coverage`: service calls have authentication coverage or an explicit exception with compensating controls.
- `activity_log_check`: high-risk access and privilege changes emit linked activity logs.
- `crypto_check`: cryptographic choices use vetted primitives and key responsibility is defined.

## Red Flags - Stop And Rework

- Production access depends on network location alone.
- Long-lived shared secrets have no rotation plan or check path.
- Break-glass access is permanent or unaudited.
- Secrets can appear in logs, build output, images, or client-visible config.
- Custom cryptography is proposed.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Treating authentication as authorization | Authenticate identity, then authorize specific actions. |
| Sharing service accounts | Use workload identity or distinct scoped credentials. |
| Rotating without revocation | Define detection, revocation, and consumer restart/reload behavior. |
| Logging everything | Audit access without leaking secrets or sensitive data. |
