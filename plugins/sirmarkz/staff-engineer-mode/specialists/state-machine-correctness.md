---
name: state-machine-correctness
description: "Use when designing or building state machines, protocols, workflows, or concurrency logic needing invariants"
---

# Systems Correctness And Formal Validation

## Iron Law

```
NO HIGH-STAKES STATE MACHINE WITHOUT MUST-NEVER RULES, MUST-EVENTUALLY RULES, AND COUNTEREXAMPLE CHECKS
```

If you cannot state what must never happen and what must eventually happen, you cannot show that the design handles its critical states.

## Overview

Some bugs are too subtle for example-based tests and too expensive to discover in production.

**Core principle:** express critical correctness properties as invariants, then validate them with the strongest practical combination of model checking, property tests, simulation, fuzzing, runtime checks, and review.

## When To Use

- The user is designing, building, or changing a state machine, protocol, workflow, or concurrency boundary and needs correctness rules before relying on examples.
- The user asks about property-based testing or fuzzing of behavior that crosses a state machine, protocol, concurrency boundary, or trust boundary, where examples cannot cover the input or interleaving space.
- A design includes distributed locks, leader election, consensus, replication, retries with mutation, workflows, money movement, authorization state, or irreversible actions.
- A bug would cause data loss, double execution, cross-tenant access, financial inconsistency, or security boundary failure.
- Tests pass for examples, but concurrency, ordering, timing, crash, or retry interleavings remain uncertain.

## When Not To Use

- The request is normal unit, integration, end-to-end, or CI merge-check design with no state-machine or invariant under test; use `testing-and-quality-gates`.
- The fuzz target is purely a parser, format decoder, or input validator with no protocol or state-machine surface; use `testing-and-quality-gates`.
- The main question is storage choice, database-backed workflow correctness, or consistency semantics; use `distributed-data-and-consistency` unless high-assurance validation of the storage protocol itself is central.
- The main question is retry, timeout, circuit-breaker, or backoff policy rather than correctness of the underlying state machine; use `dependency-resilience`.
- The system is low-risk and ordinary example-based testing is proportional.

## Info To Gather

- Current work phase, next decision, what is known, and assumptions where details are missing.
- State machine, actors, operations, messages, retries, timers, crashes, recovery, and concurrency points.
- Safety properties: what must never happen.
- Liveness properties: what must eventually happen, and under which assumptions.
- Consistency, idempotency, ordering, durability, authorization, and isolation invariants.
- Unknown-outcome cases where a timeout or lost response means the side effect may have succeeded, failed, or not executed.
- Existing tests, fuzzers, simulations, model specs, incident examples, and known counterexamples.
- Mapping from model behavior to implementation code, logs, metrics, and runtime monitors.

## Workflow

1. **Name the critical property.** Write invariants in plain language before choosing tools.
2. **Model unknown outcomes.** Treat timeout, lost response, and interrupted commit paths as explicit `unknown` states, not as ordinary failures. For side-effecting operations, define what a retry, reconciliation, or user response must do when success cannot be proven.
3. **Bound the model.** Include only state, actors, timing, failures, and nondeterminism needed to test the property.
4. **Choose validation strength.** Match the technique to the invariant. Use property-based testing and fuzzing when the invariant is local and the input or interleaving space exceeds what examples cover; use deterministic simulation when timing, scheduling, crash, or retry interleavings dominate; use model checking when the protocol or concurrency interleaving is the source of risk; reserve formal verification for cryptographic, consensus, or safety-critical mechanisms. Move up the validation ladder when the lower technique cannot cover the state space; do not stop at examples for high-stakes invariants. Example-based distributed-boundary matrices, bounded property tests on pure logic, and parser-only fuzzing with no state-machine or invariant under test belong in `testing-and-quality-gates`.
5. **Search for counterexamples.** Treat each failing trace as design feedback, not as a tool nuisance.
6. **Connect model to code.** Record which code paths implement each transition and which tests or monitors check the mapping.
7. **Verify recovery paths.** Include crash, retry, duplicate, reorder, timeout, unknown outcome, partial write, and restart behavior.
8. **Add runtime checks.** Monitor invariants that can be checked in production without leaking sensitive data or harming users.
9. **Re-run on design changes.** Update specs, properties, and generated cases when the protocol or state machine changes.

## Synthesized Default

Use lightweight formal or semi-formal validation for high-stakes stateful behavior. Start with plain-language invariants and counterexample search, then select tools proportional to risk. Do not require formal verification everywhere; require explicit properties where ordinary tests cannot cover the state space.



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

- Full formal verification may be justified for cryptographic, consensus, safety-critical, or cross-tenant isolation mechanisms.
- Property-based tests may be enough when the state space is implementation-local and failure impact is bounded.
- Deterministic simulation is preferable when implementation timing, scheduling, or crash recovery is the main uncertainty.
- Runtime invariant checks may be sampled or delayed when full checking would harm privacy, cost, or latency.

## Response Quality Bar

- Lead with the invariant set, model boundary, counterexample, validation method, or blocker requested.
- Cover safety/liveness properties, state actors, messages, timing, failures, retries, recovery, code mapping, and runtime checks before optional formal-methods breadth.
- Make recommendations actionable with model scope, properties to test, counterexample handling, recovery cases, checks, and stop criteria where relevant.
- Name the details to inspect, such as protocol states, transition rules, failure assumptions, trace logs, property-test results, simulation output, model checker traces, and code links; do not state details you have not seen.
- Stay technology-agnostic by default: do not introduce provider, product, framework, database, protocol, or command names unless the user supplied them or explicitly requested tool-specific guidance.
- Stay inside correctness validation. Route distributed-data consistency, tenant isolation, or cryptography only when those are the central unresolved risk.
- Be concise: avoid generic formal-methods advocacy and prefer compact property lists, model boundaries, and counterexample tables.

## Required Outputs

- Correctness property list with safety and liveness split.
- Unknown-outcome semantics for timeout, lost response, retry, and reconciliation cases.
- State-machine or protocol model boundary.
- Validation method selection and rationale.
- Counterexample log and design changes.
- Code-to-model mapping.
- Recovery/interleaving test plan.
- Runtime invariant or reconciliation plan.

## Checks Before Moving On

- `invariant_list`: critical safety and liveness properties are written in plain, testable language.
- `model_boundary`: actors, state, messages, timing, and failure assumptions are explicit.
- `unknown_outcome`: timeout and lost-response cases define whether the side effect may have happened and how retry or reconciliation stays safe.
- `counterexample_search`: validation attempts to find failing traces, not just confirm expected cases.
- `code_mapping`: each modeled transition maps to implementation code, tests, or runtime checks.
- `recovery_cases`: duplicate, reorder, retry, crash, timeout, and partial-failure cases are covered or explicitly exempted.

## Red Flags - Stop And Rework

- "Exactly once", "no split brain", or "strong consistency" is asserted without invariants.
- Timeout is treated as proof of failure for a side-effecting operation.
- The model omits retries, duplicate messages, crash recovery, or clock assumptions that exist in production.
- Property tests only replay hand-picked examples.
- A counterexample is dismissed because it is unlikely rather than impossible or risk-accepted.
- Runtime behavior cannot be traced back to the model.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Modeling the whole system | Model the smallest state machine that protects the invariant. |
| Confusing tests with properties | Write the rule first, then generate or search cases. |
| Ignoring liveness assumptions | State what timing, retry, and failure assumptions allow progress. |
| Letting specs drift | Update model and invariant checks when implementation changes. |
