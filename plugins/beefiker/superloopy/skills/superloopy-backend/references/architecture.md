# Architecture

Use this module to decide boundaries and contracts before choosing implementation details. Preserve the project's stack unless a measured requirement makes it inadequate.

## Discover before designing

Complete project discovery from repository evidence: entry points, instructions, deployment units, dependency conventions, API and event consumers, schema authority, migration history, data ownership, test commands, operational limits, and production-access rules. Mark unknowns explicitly. Do not turn a missing fact into a new framework, database, queue, or cache.

Draw the system boundaries that own authentication, authorization, validation, persistence, side effects, and recovery. A boundary must name its caller, trusted identity, inputs, outputs, failure modes, and data owner. Keep policy enforcement outside model output and outside client-supplied tenant fields.

## Define contracts

For an API contract, define request and response schemas, invariants, authorization, tenant derivation, status or error semantics, compatibility, idempotency, and observability. For an event contract, also define producer, consumer, ordering assumptions, delivery semantics, deduplication identity, schema evolution, poison-message handling, and replay behavior.

Choose the weakest consistency model that still preserves the user-visible invariant. State where a transaction begins and ends; do not imply that a network call, queue publish, and database commit are one atomic unit. For cross-boundary work, use an explicit state machine, durable handoff, or compensation with observable intermediate states.

One typed service boundary in stack-neutral pseudocode:

```text
type RequestContext = { verifiedPrincipal, authorizedTenant }
type ReserveInput = { itemId, quantity, operationId }
type ReserveResult = { reservationId, status, version }
type ReserveError = Unauthorized | Invalid | Conflict | Unavailable { retryable }

reserve(context: RequestContext, input: ReserveInput) -> Result<ReserveResult, ReserveError>:
  authorize(context.verifiedPrincipal, context.authorizedTenant, "inventory.reserve")
  validate(input.quantity > 0)
  within transaction:
    claim = claim_operation_atomically(context.authorizedTenant, input.operationId)
    if claim.alreadyCompleted: return claim.result
    reservation = reserve_if_available(context.authorizedTenant, input.itemId, input.quantity)
    complete_claim(claim, reservation)
  return typed_result(reservation)
```

`claim_operation_atomically` is backed by a uniqueness constraint on tenant plus operation identity, so concurrent requests cannot both pass a check-then-write window. The tenant comes only from verified authorization context, and structured conflicts are distinct from retryable infrastructure failures.

## Supporting mechanisms

- Treat caching as derived state. Define the key's tenant scope, source of truth, freshness tolerance, invalidation trigger, stampede control, sensitive-data handling, and safe behavior during cache failure.
- Treat background work as a durable workflow. Define enqueue ownership, deduplication, retry bounds, timeout, concurrency, dead-letter or terminal state, cancellation, and operator recovery.
- Preserve compatibility across mixed application and schema versions. Prefer additive contract evolution, tolerant readers where safe, staged producer/consumer changes, and explicit removal criteria.
- Select a new stack component only after recording the unmet requirement, current-stack evidence, operational ownership, migration cost, failure model, and validation plan. Popularity alone is not evidence.

Before implementation, the architecture decision must make consistency, transaction, idempotency, cache, background-work, and compatibility assumptions testable.
