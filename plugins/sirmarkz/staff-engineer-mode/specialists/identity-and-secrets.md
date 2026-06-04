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
- Bootstrap identities, first-admin setup, domain or tenant verification order, and alternate admin promotion or recovery path.
- Authorization model, permission granularity, default grants, just-in-time elevation, and break-glass process.
- Identity normalization rules, access-control inheritance, group or role membership propagation, permission cleanup safety, and backfill behavior after rollback.
- Workload or service-identity migrations, including old/new identity overlap, customer-managed target permissions, dry-run authorization checks, and rollback behavior.
- Authorization-data freshness, stale-policy detection, resync time, and serve-or-hold gate after identity or policy-store recovery.
- Authorization decision service capacity, minimum safe task counts, grow/shrink command semantics, review evidence for capacity changes, and fail-closed blast radius.
- Secrets, tokens, keys, certificates, storage locations, owner metadata, delivery interface, rotation cadence, expiry, signer/verifier rollout order, deletion protection, and consumers.
- Service-call authentication coverage, credential expiry signals, rotation lead time, and response path when expiry approaches.
- Authentication dependency cycles where a control plane, identity provider, policy store, or feature-state store depends on another component that also needs it to serve.
- Encryption needs, key responsibility, key separation, data classification, and long-lived confidentiality requirements.
- Activity logs, log retention, alerting, access recertification cadence, and revocation path.

## Workflow

1. **Inventory access paths.** Include humans, services, jobs, automation, support tools, emergency access, and third parties.
2. **Replace network trust.** Base access on identity, context, resource sensitivity, and explicit authorization, not location alone.
3. **Minimize privileges.** Scope permissions by action, resource, tenant, environment, and duration.
4. **Protect bootstrap access.** Verify first-admin, tenant/domain bootstrap, and ownership-verification flows can complete in the required order, and define an audited fallback to promote or recover an administrator without weakening the access model.
5. **Validate permission propagation.** Check normalized identifiers, inherited permissions, nested groups, current-use evidence, propagation queues, and rollback or backfill behavior before access-control cleanup or identity endpoint changes. For service-identity migrations, verify old and new identities can access every customer-managed or cross-boundary target before switching callers.
6. **Gate recovery on fresh authorization state.** After an identity or policy-store outage, hold privileged decisions until policy state is current enough for the access contract, or serve only a documented degraded mode with explicit security impact.
7. **Check authentication dependency cycles.** A critical control plane should not require an identity, policy, or feature-state path that depends on that same control plane to serve. If a cycle exists, define a separate bootstrap trust path, local verification mode, or fail-closed behavior with a tested recovery path.
8. **Guard authorization capacity changes.** Treat capacity for fail-closed authorization decisions as security-critical production state. Define minimum safe capacity, separate grow from shrink operations, require reviewer visibility into the requested change, and test traffic reroute or recovery when the decision service cannot answer.
9. **Prefer workload identity and short-lived credentials.** Use managed identity where the runtime and resource share a trust domain; use workload identity federation when crossing platforms or organizations; use expiring tokens, rotation, revocation, and expiry signals over static long-lived secrets.
10. **Keep signer and verifier state compatible.** For tokens, certificates, and signed credentials, make verifiers accept new material everywhere before signers emit it, preserve old/new overlap, and test cross-region or cross-cluster paths that can mix versions.
11. **Protect secrets and keys.** Keep them out of source, logs, images, and broad config; separate key administration from data access where risk warrants it.
12. **Validate secret delivery contracts.** When a runtime, control plane, or sidecar injects secrets into workloads, test delivery shape, naming, version selection, refresh behavior, multi-secret cases, and rollback from the consumer's perspective before rollout.
13. **Protect secret-bearing resources from cleanup errors.** Before deleting, retiring, or reassigning a resource that stores or authorizes credentials, verify owner metadata, recent and batch usage, dependent integrations, stakeholder review, deletion guard, and restore path.
14. **Design break-glass controls.** Require strong authentication, limited duration, justification, audit, and post-use verification.
15. **Use vetted cryptography.** Prefer standard protocols and managed primitives; do not invent algorithms or key-handling schemes.
16. **Audit and verify.** Emit access, privilege change, secret access, key use, and admin events with a user-visible verification path.

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

- Legacy systems may need compensating controls while static credentials are removed; require expiry and rotation using the shared risk-acceptance lifecycle plus the shared compensating-control format.
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

- Output shape: render the matching shared template headings or tables in the reply, or use the same shape.
- Identity and access model.
- Human/service permission table with least-privilege decisions.
- Bootstrap and first-admin access plan with verification ordering, fallback promotion or recovery, and audit evidence.
- Secret and key inventory with storage, rotation, expiry, and consumers.
- Secret delivery compatibility plan covering delivery interface, consumer contract, refresh behavior, multi-secret cases, rollout probe, and rollback.
- Secret-bearing resource deletion safety plan with owner metadata, usage evidence, dependency review, deletion guard, and restore path.
- Permission propagation and cleanup safety plan with normalized identifiers, inherited grants, current-use checks, queue/backfill behavior, and rollback.
- Service-identity migration plan with old/new identity overlap, target-permission inventory, dry-run authorization check, customer-visible remediation path, and rollback.
- Authorization freshness recovery gate with stale-state signal, resync target, serve/hold decision, and security impact.
- Authorization decision capacity plan with minimum safe capacity, grow/shrink guard, fail-closed impact, and reroute or recovery test.
- Token and signing-key compatibility plan covering verifier-first rollout, old/new overlap, cross-region consistency, and customer-perspective false-denial monitoring.
- Authentication coverage and credential-expiry table with lead time, signal, owner path, and response.
- Authentication dependency-cycle check for control planes and identity, policy, or feature-state stores.
- Break-glass and just-in-time access process.
- Audit event and access-recertification requirements.
- Cryptography decision record.
- Migration plan for overbroad or long-lived credentials.

## Checks Before Moving On

- `access_inventory`: human, workload, admin, emergency, and third-party access paths are listed.
- `least_privilege`: permissions are scoped by action/resource/environment/tenant and default-deny is addressed.
- `bootstrap_access`: first-admin, tenant/domain bootstrap, and ownership-verification flows have ordering, fallback recovery, and audit evidence.
- `permission_propagation`: normalized identifiers, inherited grants, current-use evidence, propagation queues, and backfill or rollback behavior are checked.
- `service_identity_migration`: service-identity changes verify target permissions for old and new identities before switching callers, with rollback and remediation paths.
- `authorization_freshness`: identity or policy-store recovery has a stale-state signal, resync target, and serve-or-hold gate for privileged decisions.
- `authorization_capacity`: fail-closed authorization decisions have minimum safe capacity, capacity-change review evidence, separate grow/shrink operations, and tested reroute or recovery.
- `credential_lifetime`: secrets and tokens have storage, expiry, rotation, and revocation plan.
- `secret_delivery_contract`: secret delivery changes verify consumer-visible shape, naming, refresh, multi-secret behavior, and rollback before rollout.
- `secret_resource_deletion`: resources that store or authorize credentials have owner metadata, usage evidence, dependency review, deletion guard, and restore path before cleanup or retirement.
- `signer_verifier_compatibility`: verifiers receive new key material before signers use it, overlap is explicit, and mixed-version paths are tested.
- `expiry_signal`: credentials, certificates, and tokens that can break production have expiry visibility and response lead time.
- `auth_coverage`: service calls have authentication coverage or an explicit exception with compensating controls using the shared risk-acceptance lifecycle and compensating-control format.
- `auth_dependency_cycle`: critical control planes do not depend on identity, policy, or feature-state paths that require the same control plane to serve, or the separate bootstrap/fail-closed path is tested.
- `activity_log_check`: high-risk access and privilege changes emit linked activity logs.
- `crypto_check`: cryptographic choices use vetted primitives and key responsibility is defined.

## Red Flags - Stop And Rework

- Production access depends on network location alone.
- Long-lived shared secrets have no rotation plan or check path.
- Break-glass access is permanent or unaudited.
- Access cleanup removes inherited, nested, or still-in-use permissions without current-use evidence and rollback.
- Secrets can appear in logs, build output, images, or client-visible config.
- First-admin or ownership-verification flows can leave a new tenant/domain with no usable administrator.
- A resource that stores or authorizes credentials is deleted from stale ownership metadata or lack of recent activity alone.
- A capacity change can shrink a fail-closed authorization decision service below safe serving levels without an explicit guard.
- Custom cryptography is proposed.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Treating authentication as authorization | Authenticate identity, then authorize specific actions. |
| Sharing service accounts | Use workload identity or distinct scoped credentials. |
| Rotating without revocation | Define detection, revocation, and consumer restart/reload behavior. |
| Rotating signers before verifiers | Roll out verification material first, keep old/new overlap, and test mixed-version token paths. |
| Deleting unused-looking credential resources | Verify owners, active use, dependents, deletion guard, and restore path first. |
| Logging everything | Audit access without leaking secrets or sensitive data. |
