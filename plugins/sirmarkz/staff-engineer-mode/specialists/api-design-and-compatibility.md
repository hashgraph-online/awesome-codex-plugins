---
name: api-design-and-compatibility
description: "Use when designing new API contracts, endpoints, SDK surfaces, or changing exposed behavior and client compatibility"
---

# API Design And Compatibility

## Iron Law

```
NO API CONTRACT WITHOUT COMPATIBILITY, ERROR, IDEMPOTENCY, AND EVOLUTION RULES
```

If current or future clients cannot tell what the contract means, how errors behave, whether retries are safe, or how the API can evolve, it is not ready.

## Overview

An API is a long-lived contract with current or future clients, retries, partial failures, and migration lag.

**Core principle:** make contracts explicit, evolvable, retry-safe, observable, and compatible by default.

## When To Use

- The user is designing or changing API behavior, service contracts, operation names, generated-client shape, versioning, compatibility, deprecation, pagination, filtering, batch operations, error models, idempotency, or client migration.
- A new system, service, endpoint, SDK surface, or interservice contract is being built and needs a client-facing contract before launch.
- A change adds, removes, renames, retypes, or changes semantics of fields, operations, defaults, errors, events, or resources exposed to another component or client.
- The user asks whether an endpoint, schema, interface, or service contract can evolve safely.
- A retryable mutating operation needs idempotency behavior.

## When Not To Use

- The data model is purely internal and is not exposed, or planned to be exposed, through an interface.
- The main issue is per-call timeout/retry behavior rather than API contract; use `dependency-resilience` instead.
- The request is broad secure design; use `secure-sdlc-and-threat-modeling` instead unless API contract is central.
- The request is event schema evolution inside an asynchronous workflow; use `event-workflows` instead unless the external API contract is the main surface.

## Info To Gather

- Current work phase, next decision, what is known, and assumptions where details are missing.
- Planned or existing consumers, request-construction surfaces, embedded or legacy runtime constraints, low-traffic entry points, client release cadence, compatibility expectations, and deprecation tolerance.
- For new APIs, intended consumer classes and discovery path; for existing APIs, known consumers and impact signals.
- Operations/resources, generated-client method shape, request builders, request and response fields, forwarded headers or metadata, transport/protocol assumptions, callback/event payloads, status/error semantics, defaults, and side effects.
- Authentication, authorization, rate limits, quotas, tenant context, activity-log needs, and abuse cases.
- High-volume consumer behavior: polling, fanout, bulk read/write needs, low-volume administrative API versus high-volume serving API usage, and quota pressure.
- Aggregated or fanout operations, unavailable-scope behavior, partial-result semantics, and global impact risk from one failed dependency or location.
- Retry behavior, idempotency needs, duplicate suppression, and replay windows.
- Pagination, filtering, ordering, sorting, cursor stability, result metadata accuracy, and consistency expectations.
- Versioning policy, launch evolution rules, migration telemetry where clients already exist, usage by client/version, and existing deprecation process.

## Workflow

1. **Define the contract boundary.** State who consumes the API, whether it is public or interservice, what compatibility promise exists, and which behaviors are observable by clients.
2. **Model operations and resources.** Use customer-domain terms, one clear action per operation, stable resource names, and request/response shapes that generate readable client methods.
3. **Classify the contract surface.** For new APIs, mark each field, operation, error, default, enum, and semantic rule as a launch-time contract commitment. For existing APIs, mark each change as compatible, conditionally compatible, or breaking. When multiple clients, request builders, upload paths, proxies, callback surfaces, embedded runtimes, or low-traffic entry points call the same operation, verify that each surface preserves required fields, forwarded headers or metadata, transport/protocol semantics, conditional fields, defaults, and exclusive option sets.
4. **Prefer additive evolution.** Add optional fields, new operations, new enum values with tolerant readers, and new versions only when needed.
5. **Design error semantics.** Use a small stable error surface with machine-readable categories, typed programmatic fields, human-readable detail, retryability, correlation identifiers, and safe redaction.
6. **Make retries safe.** For mutating operations that clients may retry, require idempotency keys, operation identifiers, or dedupe semantics. Scope dedupe state to the caller and request parameters, expire it deliberately, and ensure duplicate retries create no side effects.
7. **Handle collections deliberately.** Prefer stable cursor-style pagination for mutable collections; define ordering, filtering, empty results, cursor-token expiration, result counts and continuation metadata that match the returned payload, and list item summaries that avoid needless follow-up calls.
8. **Design fanout failure semantics.** For aggregated operations, define whether the API returns partial results, omits unavailable scopes, marks per-scope errors, or fails closed. One unavailable location, shard, tenant, or dependency should not create global unavailability unless the contract explicitly requires all scopes.
9. **Avoid quota-forcing shapes.** When callers need high-volume discovery, audit, or bulk mutation, consider change streams, asynchronous exports, asynchronous bulk operations with per-item results, or local projections so callers do not poll or fan out through a low-volume administrative path. Treat a consumer as high-volume when normal use would exceed a documented per-caller quota or must enumerate every resource on a schedule. Use bulk for one logical operation over a large set; use batch for many independent repetitions of a singular operation.
10. **Bound filters and payloads.** Keep filters explicit, bounded, commutative, and limited to fields the caller may see; define unknown, malformed, duplicate, and over-limit behavior. Publish maxima for variable inputs, payloads, and inner lists at launch.
11. **Isolate malformed requests.** Malformed or unsupported requests should fail for the caller with a stable client-action error and must not poison shared operation state, block unrelated updates, or require broad service recovery.
12. **Shape batch operations intentionally.** Use batch APIs only for repeated same-action work. Shape each item like the singular operation, include per-item correlation, separate successes from errors, define partial-success behavior, and reject whole invalid batches before attempting items.
13. **Plan evolution.** For new APIs, define how the contract can add fields, operations, enum values, limits, and versions later, plus how intended consumers will discover and adopt it. For existing APIs, use telemetry to identify clients, publish deprecation windows, support overlap, and define removal checks.
14. **Check security and abuse.** Include authorization, rate limits, tenant isolation, audit events, and input validation as part of the contract.

## Synthesized Default

Design APIs around domain contracts and generated-client ergonomics, not internal storage shape. Use additive compatibility first and explicit versions only when semantics must break. Mutations that can be retried need idempotency. Lists, filters, batches, and unbounded inputs need explicit limits and stable semantics at launch. Errors should be structured, stable, safe to expose, and tied to retry behavior. New APIs need evolution rules before launch; deprecation requires telemetry, migration support, and a removal check.



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

- Internal APIs with one deployable client may use tighter migration windows, but still need compatibility during rollout.
- A breaking change is acceptable when security, correctness, or unsustainable complexity justifies it and a migration plan exists.
- Cursor pagination may be unnecessary for immutable or tiny bounded collections.
- Protocol-specific conventions may shape syntax, naming style, and transport status, but the compatibility, idempotency, error, and migration rules still apply.

## Response Quality Bar

- Lead with the concrete decision, blocker list, or migration plan requested.
- Cover all compatibility, error, idempotency, and migration risks before optional API topics.
- Make recommendations actionable with checks, stop conditions, and removal criteria where relevant.
- Name the details to inspect, such as client telemetry, version usage, retry behavior, and migration readiness; do not state details you have not seen.
- Stay technology-agnostic by default: do not introduce provider, product, framework, database, protocol, or command names unless the user supplied them or explicitly requested tool-specific guidance.
- Stay inside the API surface. Mention pagination, rate limits, auth, audit, or tenant controls only when the prompt or risk makes them material.
- Be concise: avoid generic API background and prefer compact compatibility matrices or checklists.
- For naming or shape decisions, provide concrete operation/resource names, generated-client ergonomics notes, and compatibility rationale.
- For PR, release-note, or copy-polish requests that hide contract changes, decide safety before wording. If the contract is unsafe, lead with the blocker and give corrected release-note constraints only after the compatibility and idempotency fixes.
- Keep narrow answers bounded to one decision, the material blockers, and the minimum contract changes needed to make the rollout safe.

## Required Outputs

- Output shape: render the matching shared template headings or tables in the reply, or use the same shape.
- API contract decision with planned or existing consumers, compatibility class, and risks.
- Consumer discovery or impact plan: intended consumer classes for new APIs, known-consumer signals for existing APIs, request-construction surfaces that must stay in parity, low-traffic entry points, and embedded or legacy runtime constraints.
- Operation/resource naming decision and generated-client ergonomics notes.
- Compatibility and evolution matrix for each new or changed operation, field, default, enum, event, error, and status behavior.
- Transport, header, metadata, and callback parity check for APIs that pass requests through intermediaries or notify customer handlers.
- Versioning and deprecation plan with launch evolution rules, telemetry where available, and removal checks.
- Error model with retryability, correlation, redaction, and client action.
- Idempotency policy for retryable mutations.
- Pagination, filtering, ordering, result-metadata invariants, bounded-input and malformed-request isolation, fanout partial-failure semantics, batch semantics, bulk semantics, polling-avoidance, and rate-limit policy.
- Security and audit requirements for the exposed surface.

## Checks Before Moving On

- `compatibility_class`: every new contract element is marked as a launch-time commitment, and every contract change is classified as additive, compatible, conditionally compatible, or breaking.
- `metadata_parity`: required transport semantics, headers, auth context, tenant context, request metadata, and callback payload fields survive every intermediary path.
- `operation_shape`: operations have one customer-visible action, stable resource terms, generated-client readability, and explicit side effects.
- `idempotency_policy`: retryable mutations have an idempotency or dedupe design.
- `error_model`: errors define machine code, human detail, retryability, correlation, and safe disclosure.
- `collection_contract`: lists and filters define pagination, ordering, empty results, result-metadata accuracy, field visibility, bounds, token stability, and expiration.
- `malformed_request_isolation`: invalid requests fail for the caller without poisoning shared operation state or blocking unrelated work.
- `batch_semantics`: batch APIs define item limits, item correlation, partial success, per-item errors, and whole-request rejection rules.
- `fanout_degradation`: aggregated operations define unavailable-scope behavior and avoid global failure from one missing location, shard, tenant, or dependency unless explicitly required.
- `quota_avoidance`: consumers whose normal access pattern would exceed a documented per-caller quota or must enumerate every resource on a schedule have a stream, export, bulk, projection, or explicit quota plan before they poll or fan out accidentally.
- `consumer_discovery`: new APIs define intended consumer classes and discovery path; existing APIs identify known consumers, request-construction surfaces, embedded or legacy runtime constraints, low-traffic entry points, or the telemetry gap.
- `evolution_plan`: new APIs have rules for future compatible additions, and deprecation or breaking changes have client usage telemetry and removal criteria.
- `abuse_boundary`: authz, rate limits, tenant context, activity logging, and validation are addressed where relevant.

## Red Flags - Stop And Rework

- "Only internal clients use it" is used to skip compatibility while clients deploy independently.
- A field is repurposed with new semantics instead of adding a new field or version.
- An intermediary strips required headers or callback fields while the upstream mutation still succeeds.
- A proxy, gateway, or runtime upgrade changes transport semantics while request/response schemas stay unchanged.
- A low-traffic entry point or embedded runtime is skipped because mainline clients look healthy.
- Operation names expose implementation steps, combine unrelated actions, or generate confusing client methods.
- Errors are free-form strings with no retryability or client action.
- Mutating operations are retryable but not idempotent.
- A list, filter, fanout, or batch API ships without bounds, collection traversal semantics, or partial-failure behavior.
- Response counts, totals, or continuation metadata can contradict the returned payload without an explicit partial-result signal.
- High-volume clients must poll or fan out through a low-volume administrative path because no stream, export, bulk, or projection option exists.
- Filters expose fields the caller cannot otherwise inspect.
- Deprecation depends on guessing client usage instead of telemetry.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Versioning every change | Prefer additive compatible changes; reserve versions for semantic breaks. |
| Treating generated clients as an afterthought | Decide operation names and shapes as part of the public contract. |
| Treating status codes as the error model | Include stable application error codes and retry guidance. |
| Offset pagination on mutable data | Use stable cursors when inserts/deletes can shift results. |
| Retrofitting bounds after launch | Set list, filter, batch, payload, and processing limits before clients depend on them. |
| Hiding per-item batch failures | Echo request identifiers and separate successes from errors. |
| Solving bulk use cases with retries | Provide stream, export, bulk, or projection contracts where the use case is inherently high volume. |
| Ignoring slow clients | Plan overlap, telemetry, and explicit removal checks. |
