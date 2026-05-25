---
name: dependency-resilience
description: "Use when designing or changing remote calls or queues needing timeouts, retries, idempotency, or overload controls"
---

# Dependency Resilience And Overload

## Iron Law

```
NO REMOTE CALL OR QUEUE WITHOUT TIMEOUT, RETRY, IDEMPOTENCY, AND OVERLOAD POLICY
```

If any dependency can wait forever, retry forever, queue forever, or fail ambiguously, the design is not production-safe.

## Overview

Most cascading failures are dependency failures amplified by callers.

**Core principle:** every remote interaction needs a deadline, retry budget, idempotency story, overload behavior, and observable failure mode.

## When To Use

- The user is designing, building, adding, or modifying RPC, HTTP, database, cache, broker, stream, queue, webhook, or third-party calls.
- The user asks about retries, timeouts, backoff, jitter, circuit breakers, bulkheads, idempotency, backpressure, health checks, or load shedding.
- A service degrades when a dependency is slow, overloaded, unavailable, or returning errors.
- Queue depth, age, retries, or fanout can amplify failures.

## When Not To Use

- The request is only about in-process exceptions or validation.
- The question is where a service, module, or worker boundary should own responsibility; use `architecture-decisions` instead.
- The main question is SLO target policy; use `slo-and-error-budgets` instead.
- The main issue is topology and fault-domain survival; use `high-availability-design` instead.
- The problem is p99 optimization without dependency safety changes; use `performance-and-capacity` instead.

## Info To Gather

- Current work phase, next decision, what is known, and assumptions where details are missing.
- Dependency matrix: caller, callee, operation, protocol, tier, and criticality.
- User impact if the dependency is slow or unavailable, caller-side dependency signals, and startup or scale behavior when runtime dependencies are unavailable.
- End-to-end request deadline, per-hop timeout, connection timeout, and cancellation behavior.
- Retry count, retry locations, backoff, jitter, retryable status codes/errors, adaptive retry budget, and overload signals that stop retries.
- Caller behavior for explicit backpressure or rate-limit responses, split by synchronous request paths and asynchronous workers.
- Mutation idempotency: idempotency key, dedupe window, side effects, and replay behavior.
- Queue limits: max depth, age, drain rate, consumer concurrency, poison message handling, and DLQ policy.
- Overload signals: saturation, errors, latency, admission decisions, rejected work, and load-shed responses.
- Health checks: liveness, readiness, startup, dependency probes, and failure thresholds.

## Workflow

1. **Build the dependency matrix.** Include synchronous and asynchronous dependencies, third parties, control planes, shared infrastructure, user impact if failed, and caller-side metrics for latency, errors, timeouts, retries, and rejected work.
2. **Set the caller deadline.** Define the total time budget from the user's perspective, then allocate per-hop timeouts inside it. Calibrate each per-hop timeout from the downstream's measured tail latency (e.g., p99.9) with a target false-timeout rate ≤0.1%; do not infer timeouts from average latency.
3. **Bound retries.** Retry only when the operation is safe, useful, inside the deadline, jittered, and at one layer only — chained per-layer retries multiply load geometrically (three tries per layer across five layers is 243× load on the deepest dependency). Default to at most one retry on synchronous request-response paths; allow more on asynchronous or batch work with backoff and a dead-letter terminus. Enforce the retry rate with a token-bucket budget that replenishes on healthy responses and drains under systemic failure; do not retry explicit overload signals.
4. **Handle backpressure by caller mode.** Synchronous callers should usually fail fast, degrade, or perform only the already-budgeted retry when a dependency says it is over limit; repeated retries just add latency and tie up local resources. Asynchronous workers may slow consumption, reduce concurrency, or pause until success rates recover, unless backlog age requirements make them behave more like synchronous paths.
5. **Make mutations idempotent.** Require idempotency keys or durable dedupe for retryable writes, webhooks, and queue consumers.
6. **Handle partial batch outcomes.** If a batch call partially succeeds, retry only the failed or unknown items and preserve per-item correlation.
7. **Control queues.** Set max depth, max age, drain-rate alerts, poison handling, and backpressure before backlogs become unrecoverable.
8. **Smooth mismatched rates.** When callers can outpace dependencies, use durable buffering, controlled workers, and rate limits instead of unbounded memory queues. Size each per-dependency thread or connection pool from Little's Law as a starting estimate — `peak accepted TPS × chosen latency-or-timeout-seconds × safety factor` — then verify against pool wait time and saturation rather than treating the formula as definitive.
9. **Design overload response.** Prefer fail-fast, admission control, load shedding, and priority shedding before expensive work starts. When ordering semantics permit, prefer LIFO over FIFO under overload so newer requests are more likely still useful; propagate remaining-deadline hints transitively between hops so downstream services know when to stop. New isolation or admission limits should ship in observe-only mode first to confirm the threshold matches reality, then move to enforcement. Shed requests must remain visible in reject, shed, and error-budget metrics — exclude them only from latency percentiles, otherwise tail regression hides while the system silently fails.
10. **Use circuit breakers carefully.** For limiting retry-induced load, prefer a token-bucket retry budget over a breaker — it bounds aggregate retry rate without modal flapping. If a breaker is needed for primary-call protection, prefer additive-increase / multiplicative-decrease over binary open/closed; binary breakers oscillate under partial failure and add a rarely exercised failure mode. Name the threshold, half-open probe policy, close/recovery condition, and user-visible behavior while open.
11. **Keep health checks local.** Liveness probes must be shallow — no dependency calls — because a liveness probe that calls a shared dependency triggers cascading restarts the moment that dependency slows. Readiness may check immediate dependencies only when that cannot remove all capacity at once. Reserve enough local capacity (or an admission-bypass path) for cheap health-check responses to remain answerable while the rest of the service sheds overload — otherwise the orchestrator marks healthy instances dead during the exact incident the checks are supposed to survive.
12. **Keep startup independent where possible.** A restart, deploy, or scale-out path should not need every runtime dependency to be healthy unless the user-visible behavior, retry policy, and fallback are explicit.

## Synthesized Default

Use bounded timeouts/retries with jitter, idempotent APIs, adaptive retry budgets, rate limiting, queue backpressure, and load shedding as the default. Retry only transient conditions inside the caller deadline and retry budget; do not retry permanent failures, overload signals, or already-successful batch items unless the contract explicitly says to. Treat circuit breakers as an exception mechanism, not the first tool. Avoid fallback unless the fallback is simpler, isolated, capacity-tested, and observably correct under the same dependency failure.



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

- Some read-only idempotent requests can use hedging for tail latency, but only with capacity accounting and duplicate suppression where needed.
- A circuit breaker is appropriate when repeated calls make the outage worse and the open state has a tested user behavior.
- A fallback is acceptable when it is stale, cached, local, or reduced-quality by design, and does not depend on the same failing system.
- Non-critical asynchronous work may be dropped or delayed if loss semantics are explicit.

## Response Quality Bar

- Lead with the dependency risk, timeout/retry budget, overload policy, or failure-mode plan requested.
- For short design answers, still include concrete values or placeholders for per-dependency timeout, retry count/backoff/idempotency, circuit-breaker open/half-open/recovery thresholds, and the degraded user behavior.
- Cover deadlines, retry safety, idempotency, backpressure, load shedding, health checks, fallbacks, and failure tests before optional resilience breadth.
- Make recommendations actionable with thresholds, budgets, queue limits, stop criteria, tests, and rollback or disablement steps where relevant.
- Name the details to inspect, such as dependency p95/p99 latency, error classes, retry counts, queue age, saturation, health-check behavior, and failure-test results; do not state details you have not seen.
- Stay technology-agnostic by default: do not introduce provider, product, framework, database, protocol, or command names unless the user supplied them or explicitly requested tool-specific guidance.
- Stay inside dependency resilience and overload. Route API contract, tenant fairness, or capacity-model work only when it materially blocks the failure-mode decision.
- Be concise: avoid generic retry guidance and prefer compact dependency matrices and budget tables.

## Required Outputs

- Dependency matrix with operation, protocol, criticality, and failure behavior.
- Caller-side dependency signals and startup/scale behavior for unavailable runtime dependencies.
- Timeout/deadline budget table for caller and each dependency.
- Retry policy with backoff, jitter, retryable conditions, overload stop signals, and retry budget.
- Backpressure behavior for explicit rate-limit or overload responses, split by synchronous and asynchronous callers.
- Idempotency and duplicate-handling plan for mutations and consumers.
- Queue/backpressure/load-shedding policy with thresholds.
- Circuit-breaker or fail-fast policy for sustained failures, including open threshold, half-open probe policy, close/recovery condition, and behavior while open.
- Health-check design separating liveness, readiness, startup, and dependency checks.
- Failure-mode tests or experiments for slow, erroring, overloaded, and unavailable dependencies.

## Checks Before Moving On

- `dependency_matrix`: every remote dependency and queue has timeout, retry, and failure behavior.
- `deadline_budget`: per-hop timeouts fit inside the end-to-end caller deadline.
- `retry_safety`: retryable calls, mutations, batch items, and consumers have retry budgets plus idempotency or dedupe behavior.
- `backpressure_mode`: explicit overload responses stop synchronous retry storms and slow asynchronous workers without hiding backlog age.
- `overload_bound`: queues are bounded and overload behavior is observable before saturation cascades.
- `health_check_safety`: health checks cannot remove the whole fleet because a shared dependency is unhealthy.
- `caller_side_signals`: dependency health is visible from the caller side for latency, errors, timeouts, retries, and rejected work.
- `startup_independence`: restart, deploy, or scale-out behavior under dependency unavailability is defined.

## Red Flags - Stop And Rework

- Retrying at client, gateway, service, SDK, and worker layers with no budget.
- Retrying downstream overload signals or already-successful batch items.
- Timeout values are absent, default, infinite, or longer than the caller's deadline.
- A queue has max depth but no max age, drain-rate alert, DLQ, or poison-message policy.
- Health checks call a shared dependency and mark all instances unavailable at once.
- Fallback is more complex than the primary path or shares the same failing dependency.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Adding retries to fix slowness | First set deadlines and understand capacity; retries add load. |
| Treating circuit breakers as magic | Define and test the open, half-open, and recovery behavior. |
| Ignoring idempotency | Make retryable writes duplicate-safe before enabling retries. |
| Letting queues absorb everything | Bound queues and shed, delay, or reject work deliberately. |
