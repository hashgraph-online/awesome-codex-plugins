---
name: llm-serving-cost-and-latency
description: "Use when LLM routes need token budgets, latency budgets, cache strategy, fallback behavior, or cost attribution"
---

# LLM Serving Cost And Latency

## Iron Law

```
EVERY LLM-BACKED ROUTE DECLARES A TOKEN BUDGET, A LATENCY BUDGET, AND A DEGRADATION PATH
```

A route without all three is uncontrolled spend and uncontrolled tail. The first cost spike, provider outage, or runaway retry will make that visible at the worst time.

## Overview

Produces a per-route token and latency budget table, a cache strategy spec for prompts, embeddings, and responses, a degradation policy that names the fallback model and the degraded contract, and a cost-attribution model that maps spend to route, feature, and tenant. Refuses to ship an LLM-backed route whose tail latency, retry behavior, or per-call cost is not modeled.

**Core principle:** an LLM call is a remote, expensive, tail-latency-dominated dependency whose unit cost is set per request by the prompt the caller assembles. Treat the prompt, the model tier, the cache, and the fallback as production design choices, not implementation details.

## When To Use

- The user is designing, building, or operating a route, agent, or background job that calls a hosted or self-served language model.
- Spend on model inference is rising faster than traffic and the cause is unclear.
- p95 or p99 latency on an LLM-backed path is unacceptable to users and you is choosing between caching, batching, smaller models, streaming, or removing calls.
- A model provider had an outage or degraded response and the route had no fallback.
- You need a token budget per request before launching a feature that calls the model in a loop, in a tool-use pattern, or per item in a list.
- Prompt cache hit rate, embedding reuse, or response cache invalidation rules need to be defined.
- A retry policy is amplifying token spend on partial failures and needs bounding.
- A multi-tenant or multi-feature workload needs cost attribution because one consumer is hiding behind aggregate spend.

## When Not To Use

- The risk is prompt injection, tool-call exfiltration, retrieval-boundary leakage, or unsafe sinks; use `llm-application-security`.
- The work is dataset construction, graders, regression thresholds, or eval checks; use `llm-evaluation`.
- The model is a custom-trained or fine-tuned production ML model with training/serving skew, drift, and rollback as the dominant concern; use `ml-reliability-and-evaluation`.
- The conversation is generic backend latency, queueing, or saturation with no model-specific behavior; use `performance-and-capacity`.
- The conversation is generic dollar cost without LLM-specific token and tier choices; use `cost-aware-reliability`.
- The conversation is generic remote-call resilience that happens to call a model; use `dependency-resilience` for circuit breakers, timeouts, and idempotency once the LLM-specific budgets and fallback are set here.

## Info To Gather

- Current work phase, next decision, what is known, and assumptions where details are missing.
- Route inventory: each LLM-backed user-facing route, agent loop, and background job, with caller, expected QPS, peak factor, and tier.
- Per-route prompt structure: system prompt size, context inserted per request, retrieved-document size and count, conversation history retained, tool definitions included, and structured-output schema where used.
- Model tier choice per route: which model is the default, which is the fallback or smaller alternative, and whether cascading or routing across tiers is in use.
- Token accounting: input tokens, output tokens, cached or reused tokens, average and tail per request, and whether streaming is used.
- Latency profile: p50, p95, p99 end-to-end, time-to-first-token where streaming, and provider-side latency vs in-process overhead.
- Cache state: prompt-prefix cache, embedding cache, full-response cache, semantic cache, per-tenant scope, TTL, invalidation triggers, and observed hit rates.
- Retry and timeout policy: max retries, backoff, idempotency of the operation, and the per-retry token cost.
- Failure modes observed: provider 5xx, rate limits, partial completions, tool-call malformation, schema-validation failures, and the cost amplification of each.
- Cost data: spend by model, by route, by feature, by tenant where available, and the engineering unit each maps to.
- Degradation expectations: what user contract holds when the primary model is unavailable, slow, or rate-limited, and what the caller is allowed to fall back to.

## Workflow

1. **Enumerate the routes.** List every path where the model is called, including tool-call loops and background jobs. A route you forgot is the route that breaks the cost model.
2. **Set token budgets per route.** Define a per-request input-token cap, an expected output-token cap, and a hard cap that triggers a degraded response. The budget is a contract; the prompt assembler must enforce it.
3. **Set latency budgets per route.** Define p50, p95, and p99 end-to-end targets. For interactive routes, also define a time-to-first-token target if streaming is used. For background jobs, define a wall-clock deadline and a per-item cost ceiling.
4. **Choose the model tier deliberately.** Match the smallest acceptable model to the route's quality bar. State the fallback tier and the conditions that switch to it. Cascading from cheaper to more expensive models is allowed when the cheaper model has a measurable quality threshold; without that threshold, cascading just doubles the cost.
5. **Design the cache layers.** Distinguish prompt-prefix cache (provider-side, depends on stable prefix), embedding cache (deterministic per text plus model version), full-response cache (deterministic per prompt), and semantic cache (lossy, requires confidence threshold and false-hit budget). State scope and invalidation per layer; per-tenant scope is required where prompts contain tenant data.
6. **Bound retries and timeouts.** Set max retries, backoff, and a per-call timeout shorter than the upstream timeout. Confirm the operation is idempotent at the model layer or that retries are guarded by an idempotency key. Compute the worst-case token cost as cost-per-attempt times max attempts; that is the real per-request budget.
7. **Write the degradation policy.** For each route, state what happens when the primary model is unavailable, rate-limited, slower than the latency budget, or returns malformed output. Options include fallback model, cached response, cached approximate response, partial answer with explicit signaling, queued for later, or refused with a defined error contract. Silent fallback that changes user-visible quality without signaling is not allowed.
8. **Decide batching versus streaming.** For interactive routes, streaming usually wins on perceived latency at similar cost. For batch jobs, batching wins on throughput and per-token cost where the provider supports it; deadlines and partial-failure semantics must be explicit.
9. **Bound structured-output cost.** Schema-constrained output and tool calls amplify token cost when the model retries to satisfy a schema. Cap retries, validate cheaply before re-prompting, and treat schema-validation failure as a first-class failure mode with a separate counter.
10. **Attribute cost.** Tag every model call with route, feature, and tenant where applicable. Aggregate spend and tail latency per tag. A cost spike with no per-tag breakdown is a finding by itself.
11. **Add guardrails and alerts.** Alert on per-route token-budget breach, per-tenant cost anomaly, cache-hit-rate regression, fallback rate, retry amplification, and tail-latency regression after a model or prompt change.
12. **Rehearse the degraded path.** Periodically force fallback or refusal in a low-impact environment so the degraded contract is real, not theoretical.

## Synthesized Default

Set per-route token and latency budgets before launch. Choose the smallest acceptable model and a defined fallback. Cache aggressively at the layer that matches the determinism of the call: prompt prefix, embedding, full response, or scoped semantic. Bound retries and structured-output reattempts. Stream for interactivity, batch for throughput. Tag every call for attribution. Always have a degraded path and rehearse it. Treat the prompt assembler as a piece of production code with dedicated budget tests.



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

- A research or eval workload running offline may relax latency budgets if cost and deadline are explicit.
- A safety-critical refusal path (the model is being used as a guardrail) may waive the cheaper-fallback rule because falling back to a weaker model defeats the purpose.
- A high-determinism route may use full-response cache as the primary path and call the model only on cache miss; the budget then governs miss rate, not steady-state spend.
- A regulated workload may forbid certain cache layers because of data-handling constraints; record the exception and the resulting cost impact.
- A first prototype may run with provisional budgets, but the route may not be exposed to production traffic until the budgets, fallback, and attribution are real.

## Response Quality Bar

- Lead with the per-route budget table, cache strategy, degradation policy, or attribution model requested.
- Cover token budget, latency budget, model-tier choice, cache layers, retry and timeout bounds, degradation path, and attribution before optional model breadth.
- Make recommendations actionable with per-route numbers, cache scopes and TTLs, fallback conditions, retry caps, and the alerts that catch regression.
- Name the details to inspect, such as per-route token histograms, latency percentiles, cache hit rates, fallback rate, retry rate, and per-tag spend; do not state a budget without the data behind it.
- Stay technology-agnostic by default: do not introduce provider, product, framework, database, protocol, or command names unless the user supplied them or explicitly requested tool-specific guidance.
- Stay inside model-serving cost and latency. Route prompt-injection and tool-access risk, eval checks, generic backend performance, and generic dollar-cost optimization to the responsible specialist.
- Be concise: prefer compact route, cache, and fallback tables over generic LLM exposition.

## Required Outputs

- Per-route budget table with input-token cap, output-token cap, hard cap action, p50/p95/p99 latency target, and time-to-first-token target where streaming.
- Model-tier matrix per route with primary, fallback, and cascade conditions.
- Cache strategy spec covering prompt-prefix, embedding, full-response, and semantic caches with scope, TTL, invalidation, and observed or target hit rate per layer.
- Retry, timeout, and idempotency policy per route with computed worst-case token cost.
- Degradation policy per route covering primary unavailable, rate-limited, over-budget, and malformed-output cases, with the user-visible contract for each.
- Structured-output and tool-call cost bound: max validation retries, validation strategy, and the failure-mode counter.
- Cost-attribution model mapping spend to route, feature, and tenant, with the engineering unit each tag exposes.
- Alert and guardrail set: token-budget breach, tail-latency regression, cache-hit regression, fallback rate, retry amplification, and per-tenant cost anomaly.
- Rehearsal plan for the degraded path with cadence and verification path.

## Checks Before Moving On

- `token_budget_present`: every LLM-backed route has an input-token cap, an output-token cap, and a defined action when the cap is exceeded.
- `latency_budget_present`: every LLM-backed route has p50/p95/p99 targets and, where streaming, a time-to-first-token target.
- `model_tier_chosen`: every route names a primary model, a fallback model or refusal contract, and any cascade conditions.
- `cache_strategy_specified`: cache layers in use have scope, TTL, invalidation rule, and a target or measured hit rate.
- `retry_bound`: retry count, backoff, timeout, idempotency, and worst-case per-call token cost are computed.
- `degradation_path_specified`: each failure mode (unavailable, rate-limited, over-budget, malformed) has a user-visible contract and is rehearsed.
- `cost_attribution`: every call is tagged by route, feature, and tenant where applicable; spend can be sliced by tag.
- `tail_alerting`: alerts cover token-budget breach, tail-latency regression, cache-hit regression, fallback rate, retry amplification, and per-tenant cost anomaly.

## Red Flags - Stop And Rework

- The route has no input or output token cap and assembles its prompt by appending whatever the caller passes.
- Latency is reported as average only and the tail is not measured.
- A retry storm during a partial provider outage doubled or tripled spend and no retry cap or circuit broke the loop.
- Schema-constrained or tool-call output retries silently until success, with no reattempt cap.
- Cache "works" but hit rate is unmeasured; cost behavior changes when the prompt template is edited and nobody notices.
- The fallback path is documented but has never been exercised; provider failure produces a real outage.
- Spend is reported in aggregate only and per-tenant or per-feature cost cannot be sliced.
- Streaming is used for latency optics but the caller still waits for the full response before rendering.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Picking the largest model by default | Match the smallest acceptable model to the route's quality bar; name the fallback. |
| Treating the prompt as free-form | Cap input tokens at the assembler and reject prompts that exceed the budget. |
| Caching without scope rules | Scope cache by tenant where prompts contain tenant data; state TTL and invalidation. |
| Unbounded retries on schema failures | Cap reattempts; treat schema failure as a counted failure mode. |
| Average-latency budgets | Budget p95 and p99; for interactive paths, also budget time-to-first-token. |
| No degraded contract | Define what the user sees when the primary model is unavailable; rehearse it. |
| Aggregate spend only | Tag every call by route, feature, and tenant; alert on per-tag anomalies. |
| Confusing cache layers | Distinguish prompt-prefix, embedding, full-response, and semantic caches; each has different determinism. |
