---
name: testing-and-quality-gates
description: "Use when test strategy, merge/release checks, CI budgets, static analysis, mutation tests, flakes, or ratchets matter"
---

# Testing And Quality Checks

## Iron Law

```
EVERY TEST CHECKS A NAMED RISK; EVERY BLOCKING CHECK HAS A FAILURE RESPONSE
```

Tests exist to exercise a specific risk; "we have tests" without naming the risk each test exercises is weak signal. A blocking check without a written failure response teaches people to ignore it. For a solo developer the response can be a single sentence: what the agent should inspect, what command verifies the fix, and when to quarantine or downgrade the check.

## Overview

Quality checks should catch real risk early without turning delivery into ritual.

**Core principle:** place fast, deterministic, high-signal checks before merge; reserve slower or broader checks for the stage where they can show something useful.

## When To Use

- The user asks for test strategy, merge checks, release checks, CI checks, quality standards, test pyramid/trophy, static analysis, coverage policy, or verification requirements.
- You need to decide what must pass before merge, before release, or before launch.
- A legacy codebase needs quality ratchets without stopping all work.
- Existing tests or CI are slow, flaky, low-signal, or ignored.

## When Not To Use

- The user asks about generic review behavior, responsibility routing, or review latency with no merge or release check decision.
- The user asks for canary or production rollout checks; use `progressive-delivery` instead.
- The request is production chaos or failover testing; use `resilience-experiments` or `high-availability-design` instead.
- The question is pure formatting/style enforcement; automate it and keep this skill focused on risk.

## Info To Gather

- Current work phase, next decision, what is known, and assumptions where details are missing.
- Supported behaviors, critical journeys, impact dimensions, risk areas, and recent defect history.
- Existing test inventory: unit/component/contract/integration/end-to-end/performance/security/accessibility/static checks.
- Pre-traffic health checks, critical-path sanity checks, production-like integration checks, synthetic or canary checks, and performance bottleneck tests.
- Distributed edge cases: independent client, network, server, timeout, duplicate, and retry outcomes for request/reply or workflow boundaries.
- CI structure, runtime, flake rate, failure responsibility, required versus advisory checks, and shared test-environment capacity or cleanup health.
- Coverage signal, mutation or fault-injection needs, legacy findings, and known blind spots.
- Release process and where checks can run without excessive feedback delay.

## Workflow

1. **Classify risk.** Identify correctness, compatibility, security, reliability, performance, data, and accessibility risks introduced by the change.
2. **Place tests low.** Prefer the cheapest deterministic check that exercises the behavior; use broader tests only for cross-boundary confidence.
3. **Define a test taxonomy.** Group checks by dependency and runtime cost so fast in-memory/component tests protect merge, deployment tests protect release, and production probes protect rollout.
4. **State suite composition.** For CI reduction, flake cleanup, or suite redesign, include a compact current or target layer mix such as unit/component, contract/integration, and end-to-end counts or ratios, with one rationale tied to speed, determinism, and risk coverage.
5. **Separate check types.** Pre-merge checks should be fast and high-signal; use a default budget such as p95 under 10 minutes for the full pre-merge lane and under 5 minutes for a fast path. Pre-release checks can be broader; production checks belong to rollout.
6. **Check before traffic.** For serving systems, startup/readiness checks and critical-path sanity checks should pass before new capacity accepts real traffic.
7. **Make checks actionable.** Every blocking check needs failure instructions and a path to fix or quarantine.
8. **Validate test infrastructure.** For broad, device, browser, integration, or hosted-environment checks, watch pool capacity, queue time, cleanup of per-test resources, leak symptoms, and infrastructure errors separately from product failures.
9. **Handle flakes as defects.** A flaky blocker teaches people to ignore checks. Fix it, quarantine it, or downgrade it with a dated expiry.
10. **Use ratchets for legacy.** Prevent new critical findings and reduce existing debt over time without requiring impossible cleanup.
11. **Cover distributed failure permutations.** For request/reply, event, or workflow boundaries, test independent outcomes for client, network, server, timeout, duplicate, and retry behavior. Do not collapse them into one "network failed" case. Route stateful protocol invariants and counterexample search to `state-machine-correctness` when example tests cannot cover the interleavings.
12. **Place high-assurance tests deliberately.** Bounded property tests on pure logic and ordinary fuzzing can live in this skill; concurrency/protocol invariants, model checking, deterministic simulation, and counterexample-driven validation route to `state-machine-correctness`.
13. **Choose test data safely.** Use synthetic data for pre-merge by default, anonymized or captured production-like data in controlled release stages, and explicit privacy checks for sensitive fixtures.
14. **Use mutation testing selectively.** Apply it to safety, security, financial, or dense branch logic where coverage percentage is misleading; do not make it a universal check.
15. **Keep style mechanical.** Formatting and simple style should be automated, not debated manually.
16. **Verify the strategy.** Confirm each critical risk has a check, test, check artifact, or explicit exception.

## Synthesized Default

Use a risk-based test strategy with fast deterministic pre-merge checks, focused integration/contract checks for boundaries, static/security analysis in the developer path, and broader release checks only where they add confidence. Push tests left when they can run reliably before merge; push tests right only when production reality is needed. Block on high-signal checks; make low-signal checks advisory until they are trustworthy.



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

- Legacy systems may use non-regression ratchets before enforcing absolute thresholds.
- Flaky tests should not block until fixed or quarantined with clear responsibility.
- Safety-critical, financial, security-sensitive, or data-destructive paths may require deeper verification, formal methods, or simulation.
- Generated or third-party code may use contract and integration checks instead of unit-level responsibility.

## Response Quality Bar

- Lead with the test strategy, check matrix, blocker decision, or quality-risk map requested.
- Cover risk mapping, check stage, failure response, flake policy, static/security checks, and legacy ratchets before optional testing breadth.
- For slow-CI, bypassed-CI, flaky-suite, or suite-redesign prompts, always state the intended test-layer composition as counts or ratios and explain why that mix gives faster, more deterministic signal than the current shape.
- Make recommendations actionable with blocking/advisory status, validation commands, quarantine rules, stop criteria, and rollout of new checks where relevant.
- Name the details to inspect, such as defect history, critical journeys, CI runtime, flake rate, coverage gaps, static findings, and release failure data; do not state details you have not seen.
- Stay technology-agnostic by default: do not introduce provider, product, framework, database, protocol, or command names unless the user supplied them or explicitly requested tool-specific guidance.
- Stay inside verification and quality checks. Route production rollout checks or resilience experiments only when they are the central unresolved risk; generic review workflow has no routed specialist.
- Be concise and prefer compact risk-to-check matrices, but always state: a flake-rate metric paired with a quarantine timer, a coverage metric+target paired with a meaningful-vs-vanity caveat, a CI runtime target paired with how it is measured, and per-layer test ratios with rationale when test composition is in scope.

## Required Outputs

- Output shape: render the matching shared template headings or tables in the reply, or use the same shape.
- Test strategy by risk area and lifecycle stage.
- Check matrix: pre-merge, pre-release, launch, and advisory checks.
- Critical-path sanity and pre-traffic health checks with expected behavior and stop condition.
- Runtime budget for blocking lanes with a measurement source (p95 from CI history, not aspirational), and the action when the budget is exceeded.
- Test composition by layer (unit/component, contract/integration, end-to-end, and specialized checks) with counts or ratios and rationale whenever cutting CI time, handling flakes, or redesigning a suite.
- Distributed-boundary failure matrix for request/reply or workflow edges, covering timeout, unknown result, duplicate, retry, and server-side state safety where relevant.
- Failure response for each blocking check.
- Test infrastructure health for shared environments: capacity, queue time, per-test resource cleanup, leak symptoms, and infrastructure error separation.
- Static analysis, security scanning, and dependency check policy.
- Coverage or mutation policy where it adds useful signal: name the metric, the target, and the meaningful-vs-vanity caveat (changed-code coverage, critical-path coverage).
- Test data sourcing and privacy/sensitivity policy.
- Flake management and quarantine policy: state the flake-rate threshold (e.g. >1% rerun rate) and the quarantine timer (e.g. 24-48h to quarantine or downgrade with expiry).
- Legacy ratchet plan with cadence, target metric, and next reduction step.

## Checks Before Moving On

- `risk_mapping`: every critical risk maps to a test, check artifact, or explicit exception.
- `check_signal`: every blocking check has high signal, and failure response.
- `test_infra_health`: shared test environments expose capacity, cleanup, leak, queue, and infrastructure-error signals before failures are treated as product regressions.
- `flake_policy`: flaky checks have fix, quarantine, downgrade, or expiry decision.
- `stage_fit`: each check runs at the earliest stage where it can check the intended property.
- `critical_path_sanity`: critical user paths have sanity checks that validate behavior and process health.
- `distributed_failure_matrix`: distributed boundaries cover independent client, network, server, timeout, duplicate, and retry outcomes, or route high-stakes invariants to `state-machine-correctness`.
- `pre_traffic_health`: new capacity passes startup/readiness checks before accepting real traffic.
- `promotion_checks`: production-like integration, synthetic, canary, or performance checks stop promotion when critical behavior fails.
- `suite_shape`: test-layer counts or ratios match the risk profile, with most pre-merge confidence coming from cheap deterministic checks and only bounded broad tests blocking.
- `legacy_ratchet`: existing debt has a non-regression rule and reduction plan.

## Red Flags - Stop And Rework

- A slow end-to-end suite is the only meaningful pre-merge check.
- Coverage percentage is treated as quality without behavior/risk mapping.
- Flaky tests are required but failures are routinely rerun until green.
- Static analysis results appear after merge with no local fix path or suppression rule.
- Checks block but no owner can explain what failure means.
- A shared test environment mixes product failures with capacity, cleanup, queue, or infrastructure-health failures.
- Distributed-call tests treat timeout as a simple failed request instead of checking unknown-outcome behavior.
- High-assurance protocol or concurrency validation is treated as ordinary CI without invariants or counterexamples.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Testing implementation shape | Test supported behavior and contracts. |
| Blocking on noisy tools | Start advisory, tune signal, then enforce. |
| One giant quality check | Split by lifecycle stage and risk. |
| Demanding instant legacy perfection | Use ratchets and prevent new debt. |
