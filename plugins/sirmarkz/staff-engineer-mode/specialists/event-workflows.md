---
name: event-workflows
description: "Use when events, messages, queues, streams, sagas, or workflows need idempotency, retry, DLQ, ordering, or replay"
---

# Event Driven Systems And Workflows

## Iron Law

```
NO EVENT OR WORKFLOW WITHOUT CONTRACT, IDEMPOTENCY, RETRY DECISION, TERMINAL-FAILURE, AND REPLAY POLICY
```

If consumers cannot safely see a message twice or late, the workflow is not production-ready.

## Overview

Asynchronous systems trade call-time coupling for delivery, ordering, replay, and correction obligations.

**Core principle:** assume duplicate, delayed, reordered, and replayed messages unless the design handles those cases explicitly.

## When To Use

- The user asks about events, queues, streams, change capture, transactional outbox, sagas, retries, DLQs, replay, message schemas, or workflow orchestration.
- A design replaces synchronous calls with asynchronous processing.
- A multi-step business process spans services or responsibility boundaries.
- The user asks how to publish state changes reliably.

## When Not To Use

- The design is only synchronous RPC or HTTP call policy; use `dependency-resilience` instead.
- The main question is storage consistency or transaction semantics; use `distributed-data-and-consistency` instead.
- The prompt centers a database or storage boundary where correctness can break; use `distributed-data-and-consistency` instead.
- The work is batch/warehouse freshness and lineage; use `data-pipeline-reliability` instead.
- The issue is cache invalidation only; use `caching-and-derived-data` instead.

## Info To Gather

- Current work phase, next decision, what is known, and assumptions where details are missing.
- Producers, consumers, topics/queues/streams, and event purpose.
- Event type: notification, state transfer, event-sourced fact, command, reply, or workflow step.
- Schema, compatibility rules, required fields, versioning, and responsibility.
- Trigger, subscription, or consumer-runtime compatibility across producer and consumer versions, including disabled, delayed, and replay-after-fix behavior.
- Delivery semantics, ordering needs, partition key, idempotency key, and dedupe window.
- Retry policy, backoff, max attempts, poison-message behavior, terminal-failure disposition, optional quarantine or DLQ handling, and manual repair.
- Queue bounds, age, depth, drain rate, consumer concurrency, and batched-message per-item status.
- Replay needs, retention, correction process, and consumer side effects.
- Notification or external side-effect volume limits, downstream acceptance signals, and reputation or policy thresholds.
- Backlog metrics, processing latency, freshness, consumer lag, and alert thresholds.

## Workflow

1. **Classify the pattern.** Distinguish notification, event-carried state, event sourcing, command, CQRS read model, saga, and workflow orchestration.
2. **Define the contract.** Write schema, meaning, responsibility, trigger/runtime compatibility, and versioning rules before implementation. Add a consumer-driven contract test for event schemas so a lagging consumer cannot be broken by a producer change, and frame the choreography-versus-orchestration choice explicitly (choreography is looser-coupled with no central view; orchestration adds central visibility and a coordinator).
3. **Publish atomically.** Use a durable local transaction plus outbox or equivalent when state change and message publication must agree.
4. **Make consumers idempotent.** Design dedupe, commutative updates, durable processing markers, or safe side effects.
5. **Control retries and terminal failures.** Bound attempts, add backoff and jitter, isolate poison messages, and retry only failed or unknown items in batched work when item status is available. Choose a terminal disposition that preserves the workflow's semantics: quarantine or DLQ, park in the source, stop the partition or workflow, compensate, or discard only when loss is explicitly harmless. A DLQ is optional and can be wrong when moving one item breaks ordering or hides an incomplete workflow; if used, name triage, retention, replay, and responsibility.
6. **Plan ordering and partitioning.** Order only where necessary; choose partition keys that avoid hot partitions and preserve required entity order.
7. **Design replay and correction.** Ensure reprocessing is safe, observable, and can repair bad events or bad consumers.
8. **Bound side effects.** For notifications or other external side effects, validate fanout, acceptance, suppressions, bounce/rejection signals, and user-visible misclassification before increasing volume.
9. **Instrument the flow.** Track enqueue time, age, depth, lag, drain rate, processing errors, consumer concurrency, terminal-disposition volume and age, batched-item status, downstream acceptance, and replay progress.

## Synthesized Default

Use at-least-once delivery with duplicate-safe consumers as the conservative default when the actual boundary is unknown. Use outbox or equivalent for atomic publish, saga or workflow state for multi-step processes, schema compatibility for evolution, durable queueing for rate mismatch, and explicit replay or correction for recovery. Describe guarantees separately for message delivery, handler execution, state commit, and external side effects. A platform may provide an exactly-once guarantee inside one boundary, but it does not automatically make external business effects exactly once.



## Exceptions

- Exactly-once guarantees may be valid for a defined delivery, processing, or state-commit boundary; consumers still need a stated outcome for external side effects and recovery outside that boundary.
- Ordering should be scoped to the smallest entity needed; global ordering is rarely worth the throughput and availability cost.
- Fire-and-forget notifications are acceptable only when loss, duplication, and delay are explicitly harmless.
- Human confirmation workflows may prefer explicit workflow state over event choreography.

## Response Quality Bar

- Lead with the workflow state model, failure handling plan, or blockers.
- Cover idempotency, ordering, retries, poison and terminal-failure handling, compensation, and reconciliation before optional event-system topics.
- Make recommendations actionable with checks, stop conditions, and replay controls where relevant.
- Name the details to inspect, such as event keys, retry counts, duplicate rates, terminal-disposition age, consumer lag, and replay checks; do not state details you have not seen.
- Stay technology-agnostic by default: do not introduce provider, product, framework, database, protocol, or command names unless the user supplied them or explicitly requested tool-specific guidance.
- Stay inside the workflow and event contract. Route broad API or data consistency issues only when material.
- Be concise: avoid generic event-driven background and prefer compact state, retry, and terminal-failure tables.
- Scale the artifact to the request: a narrow consumer or message path needs its contract, delivery boundary, idempotency, retry decision, terminal disposition, and replay behavior; add orchestration, queue, side-effect, and observability modules only when relevant.

## Required Outputs

- Output shape: render the matching shared template headings or tables in the reply, or use the same shape.
- Event/workflow contract and schema compatibility policy.
- Trigger or consumer-runtime compatibility policy, including whether delayed events are replayed, dropped, or require manual repair after a rollback or fix.
- Producer/consumer responsibility matrix.
- Idempotency and duplicate-handling plan.
- Retry, backoff, poison-message, and terminal-failure policy, including quarantine or DLQ only when compatible with ordering and recovery semantics.
- Queue/workflow overload table covering depth, age, drain rate, consumer concurrency, poison path, and batched-item status.
- Notification and external side-effect acceptance checks when the workflow emits user-visible or third-party-visible effects.
- Ordering, partitioning, and hot-key plan.
- Replay, correction, and manual repair plan.
- Observability requirements for age, lag, depth, errors, and replay.

## Checks Before Moving On

- `contract_check`: event meaning, schema, and compatibility rules are documented.
- `consumer_contract`: event schema changes have a consumer-driven contract test; consumers are idempotent under at-least-once delivery.
- `trigger_compatibility`: trigger or consumer-runtime changes define delayed, dropped, replayed, and rollback behavior across versions.
- `idempotency_check`: every consumer side effect is duplicate-safe or explicitly non-retryable.
- `terminal_failure_check`: retry attempts, backoff, poison handling, and terminal disposition are defined; any quarantine or DLQ has responsibility, retention, and replay behavior.
- `queue_bound`: queue depth, age, drain rate, and consumer concurrency have bounds or explicit unknowns.
- `side_effect_bound`: notification and external side-effect volume has acceptance signals, suppression rules, and rollback or throttling criteria.
- `poison_path`: poison item handling, terminal disposition, responsibility, and manual repair path are defined.
- `batch_item_status`: batched work records per-item success, failure, or unknown status before retry.
- `ordering_check`: ordering and partition key choices match the entity semantics.
- `replay_check`: replay/correction path is safe and observable.

## Red Flags - Stop And Rework

- An exactly-once claim does not name whether it covers delivery, handler execution, state commit, or external side effects.
- DLQ exists but draining, replay, or correction has no runbook.
- Events are named after implementation steps rather than durable business facts.
- Schema changes have no compatibility rules.
- Replay would send emails, charge cards, or trigger irreversible actions again.
- Notification volume is changed without downstream acceptance, rejection, suppression, or misclassification monitoring.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Using events to hide coupling | Make responsibility and contract explicit. |
| Adding a DLQ by default | Choose a terminal disposition that preserves ordering and workflow semantics; if using a DLQ, define triage, retention, replay, and discard. |
| Requiring global order | Order only per entity or workflow where needed. |
| Forgetting correction | Plan bad-event and bad-consumer repair from the start. |
