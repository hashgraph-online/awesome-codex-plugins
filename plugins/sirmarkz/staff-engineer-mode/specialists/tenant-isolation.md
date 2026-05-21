---
name: tenant-isolation
description: "Use when multi-tenant systems need tenant context, data partitioning, quotas, cross-tenant tests, or safe telemetry"
---

# Tenant Isolation And Data Protection

## Iron Law

```
NO TENANT-SENSITIVE PATH WITHOUT TENANT CONTEXT, ACCESS BOUNDARY, QUOTA, AUDIT, AND PRIVACY CONTROL
```

If a request or query can lose tenant context, cross-tenant leakage or impact is only a matter of time.

> This skill assumes a multi-tenant deployment serving more than one customer or organization on shared infrastructure. A single-tenant deployment may still need it if PII or privacy domains create internal boundaries; otherwise route privacy work to `privacy-and-data-lifecycle`.

## Overview

Multi-tenancy fails when tenant context is optional.

**Core principle:** carry tenant and data classification through every request, query, log, metric, trace, audit event, quota, and operational workflow.

## When To Use

- The user asks about multi-tenancy, tenant isolation, PII, privacy, noisy neighbors, cross-tenant blast radius, tenant quotas, or tenant-aware logging.
- A service stores, queries, caches, logs, exports, or processes data for multiple customers, organizations, or privacy domains.
- A bug could expose one tenant's data to another or let one tenant consume shared capacity.
- A design needs tenant-aware audit, encryption, retention, deletion, or access controls.

## When Not To Use

- The request is general authentication/authorization without tenant or data boundary concerns; use `identity-and-secrets` instead.
- The request is broad privacy lifecycle, minimization, retention, deletion, or privacy-safe telemetry without tenant-boundary concerns; use `privacy-and-data-lifecycle` instead.
- The main issue is public abuse or DDoS at the edge; use `edge-traffic-and-ddos-defense` instead.
- The work is only supply-chain or artifact integrity; use `software-supply-chain-security` instead.

## Info To Gather

- Current work phase, next decision, what is known, and assumptions where details are missing.
- Tenant model: silo, pool, bridge, organization/account hierarchy, shared services, and administrative boundaries.
- Data classification, PII/sensitive fields, retention, deletion, export, and residency constraints.
- Request, query, cache, event, batch, search, analytics, and support/admin paths that carry tenant data.
- Access controls, tenant context propagation, activity logs, row/object boundaries, and break-glass behavior.
- Quotas, rate limits, concurrency caps, noisy-neighbor risks, and per-tenant isolation needs.
- Admission point for tenant limits, dynamic limit update path, fair-share behavior, and privacy-safe impact scoping.
- Logging, metrics, traces, crash/error reports, and support tooling that may expose sensitive data.

## Workflow

1. **Define tenancy.** State what tenant means, how tenant IDs are assigned, and which resources are tenant-scoped. Define the model: silo means dedicated stack per tenant; pool means shared stack with logical isolation; bridge means shared control plane with tenant-dedicated data or runtime boundaries.
2. **Map tenant context.** Follow tenant context through request handling, storage, caches, events, jobs, logs, metrics, traces, and admin tools.
3. **Choose isolation model.** Use silo, pool, bridge, hybrid, or isolation-group boundaries based on data sensitivity, blast radius, scale, cost, and tenant-specific residency or compliance needs. Isolation groups separate sets of tenants from each other while preserving finer isolation inside each group.
4. **Choose data partitioning.** State whether tenants use separate stores, separate schemas/namespaces, shared schemas with enforced tenant predicates, or tenant-scoped encryption and credentials.
5. **Enforce data boundaries.** Apply tenant filters, scoped credentials, row/object boundaries, query guards, cache-key tenant assertions, and cross-tenant tests.
6. **Control noisy neighbors.** Add per-tenant quotas, rate limits, concurrency caps, and load-shedding rules where shared capacity exists; enforce cheap admission checks before expensive work when possible and define how limits change safely during an event.
7. **Protect privacy surfaces.** Minimize, redact, tokenize, encrypt, or segregate sensitive data in logs, telemetry, exports, and support views.
8. **Handle tenant offboarding.** Propagate deletion and access removal through stores, caches, indexes, derived data, exports, backup expiry, and support tooling.
9. **Audit high-risk access.** Record administrative, support, export, deletion, and cross-tenant operations in tenant-scoped activity logs; define retention long enough for investigation, compliance, and incident investigation.
10. **Verify isolation.** Use tests, probes, reviews, and monitoring for cross-tenant reads/writes and capacity abuse.

## Synthesized Default

Make tenant context mandatory and enforce it at multiple layers: application, data access, cache/event/job processing, audit, and observability. Choose the weakest shared-tenancy model that still satisfies blast-radius and data-boundary requirements, then combine tenant quotas with privacy-aware logging and cross-tenant tests.



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

- Single-tenant deployments can still need this skill when PII, privacy, or data-protection controls are central.
- Stronger silo isolation is warranted for highly sensitive tenants or regulatory boundaries even if cost is higher.
- Shared pooled models are acceptable when tenant context, quotas, and tests are strong enough for the risk.
- Emergency support access may cross normal boundaries only with justification, time limit, audit, and review.

## Response Quality Bar

- Lead with the isolation model, cross-tenant risk, boundary-control plan, or test gap requested.
- Cover tenant context propagation, data access boundaries, cache/event/job paths, quotas, privacy-safe telemetry, support access, and cross-tenant tests before optional tenancy breadth.
- Make recommendations actionable with enforcement layers, query/key rules, quotas, tenant-scoped activity logs with retention, test cases, and stop criteria where relevant.
- Name the details to inspect, such as request flows, schema keys, cache keys, job payloads, event envelopes, support-tool logs, quota metrics, audit retention settings, and cross-tenant test results; do not state details you have not seen.
- Stay technology-agnostic by default: do not introduce provider, product, framework, database, protocol, or command names unless the user supplied them or explicitly requested tool-specific guidance.
- Stay inside tenant isolation and data protection. Route general privacy or identity work only when it materially changes the isolation decision.
- Be concise: avoid generic multi-tenancy background and prefer compact propagation maps and boundary-control tables.

## Required Outputs

- Tenant isolation model and rationale.
- Tenant context propagation map.
- Data partitioning and isolation-group decision when applicable.
- Data classification and sensitive-field handling plan.
- Access, query, cache, event, and job boundary controls.
- Tenant offboarding and deletion propagation plan.
- Noisy-neighbor quota and capacity policy.
- Dynamic tenant-limit update path and privacy-safe impact scoping signals.
- Privacy-safe logging/telemetry/support review.
- Tenant-scoped audit log requirements, including covered events, protected fields, retention period or retention policy, and review responsibility.
- Cross-tenant test requirements, including forced-tenant mismatch, missing-tenant-filter detection, random tenant-ID probes, and cache-key assertions.

## Checks Before Moving On

- `tenant_context`: every request/query/job/event/cache path preserves tenant context or is explicitly tenant-neutral.
- `data_boundary`: data access controls enforce tenant isolation where shared stores exist.
- `privacy_check`: sensitive data handling is defined for logs, traces, metrics, errors, exports, and support tools.
- `quota_check`: shared capacity has tenant-aware quotas or an explicit risk acceptance.
- `early_admission`: tenant or caller limits apply before expensive shared work where feasible.
- `dynamic_limit_path`: emergency or routine limit changes have a safe update, rollback, and verification path.
- `tenant_impact_scope`: tenant impact can be scoped with privacy-safe operational signals.
- `activity_log_check`: tenant-scoped activity logs cover high-risk access and define retention for forensics and incident investigation.
- `cross_tenant_test`: tests or probes cover unauthorized cross-tenant read/write paths.

## Red Flags - Stop And Rework

- Tenant ID is passed as an optional parameter.
- Logs or traces include raw PII or tenant secrets.
- Background jobs process tenant data without tenant-scoped responsibility.
- Shared caches omit tenant from keys.
- Support tools can access tenant data without audit.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Treating tenant isolation as only authz | Enforce tenant context through data, cache, jobs, telemetry, and audit. |
| Ignoring noisy neighbors | Add tenant-aware quotas and saturation signals. |
| Trusting manual review | Add cross-tenant tests and query guards. |
| Logging for convenience | Redact, tokenize, or omit sensitive fields. |
