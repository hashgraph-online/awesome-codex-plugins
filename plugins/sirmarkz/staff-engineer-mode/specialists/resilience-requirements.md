---
name: resilience-requirements
description: "Use when a feature needs failure-behavior, non-functional targets, and testable acceptance criteria before code"
---

# Resilience Requirements

## Iron Law

```
NO FEATURE STARTS WITHOUT FAILURE BEHAVIOR, NON-FUNCTIONAL TARGETS, AND ACCEPTANCE CRITERIA A TEST CAN CHECK
```

A spec that names only the happy path leaves dependency-loss, malformed-input, overload, and partial-failure behavior undefined, so it is never designed and never tested. That absence is the root of a large share of outages.

## Overview

Produces the resiliency contract of a spec before code exists: non-functional targets, failure and edge and error behavior, abuse and misuse cases, explicit non-goals to bound blast radius, and acceptance criteria a test can check against each failure behavior. It feeds downstream specialists rather than replacing them. It does not own product value, prioritization, or market requirements.

**Core principle:** decide what the system must do when things go wrong before writing the code that assumes they go right.

## When To Use

- A feature or change is being scoped and its failure behavior, non-functional targets, or acceptance criteria are not yet stated.
- A design or review finds that "what happens when the dependency is down or the input is malformed" was never specified.
- A team needs testable acceptance criteria tied to failure behavior, not only to the happy path.
- An idea needs its resiliency contract before `architecture-decisions` shapes the design.

## When Not To Use

- The decision is which architecture or boundary to choose; use `architecture-decisions`.
- The artifact is the reliability target math and budget policy; use `slo-and-error-budgets`.
- The artifact is a threat model or abuse-case-to-control mapping; use `secure-sdlc-and-threat-modeling`.
- The artifact is the test strategy and check placement; use `testing-and-quality-gates`.
- The request is product discovery, prioritization, or market and PM requirements; out of scope.

## Info To Gather

- Current work phase, next decision, what is known, and assumptions where details are missing.
- The user-facing outcome the feature must deliver and the journeys that carry it.
- Dependencies the feature relies on and what each one failing should do to the feature.
- Inputs the feature accepts and the range of malformed, hostile, or out-of-bounds values.
- Load expectations and the behavior required at and beyond the expected peak.
- Existing targets, incidents, and constraints that bound the contract.

## Workflow

1. **State the outcome and journeys.** Write the user-facing result the feature must deliver and the critical journeys that carry it.
2. **Set non-functional targets.** Name availability, latency, durability, and throughput targets to hand to `slo-and-error-budgets`, `high-availability-design`, and `performance-and-capacity`.
3. **Specify failure behavior.** For each dependency, decide what the feature does when it is slow, down, or returns errors: degrade, queue, fail closed, fail open, or fall back.
4. **Enumerate edge and error behavior.** Define behavior for malformed input, empty and boundary values, partial failure, and retries.
5. **List abuse and misuse cases.** Capture hostile and buggy-client cases to hand to `secure-sdlc-and-threat-modeling`.
6. **Bound scope with non-goals.** State what the feature will not do, to limit blast radius and prevent scope creep into untested paths.
7. **Write testable acceptance criteria.** For each behavior above, write a criterion a test can check, and route placement to `testing-and-quality-gates` and intent verification to `agent-pr-review`.

## Synthesized Default

Specify failure behavior, non-functional targets, and acceptance criteria up front, then hand each to its downstream specialist. Keep the spec short; each failure mode needs a defined behavior and a checkable criterion.

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

- Throwaway prototypes may record only the failure behaviors being intentionally ignored and the date they expire.
- Emergency fixes can write the resiliency contract after mitigation, but before expanding scope or treating the fix as complete.
- Product requirements and prioritization remain outside this specialist unless they define engineering failure behavior.

## Response Quality Bar

- Lead with the missing failure behavior, target, non-goal, or acceptance criterion requested.
- Cover critical journeys, non-functional targets, dependency failure behavior, malformed input, abuse cases, non-goals, and testable criteria before optional planning breadth.
- Make recommendations actionable with per-dependency decisions and acceptance criteria a test can check.
- Name the details to inspect, such as feature specs, dependencies, input ranges, traffic expectations, incidents, and existing targets; do not state details you have not seen.
- Stay technology-agnostic by default: do not introduce provider, product, framework, database, protocol, or command names unless the user supplied them or explicitly requested tool-specific guidance.
- Stay inside the resiliency contract of the spec; route architecture choice, target math, threat models, and test strategy when those become the central artifact.

## Required Outputs

- Output shape: render the matching shared template headings or tables in the reply, or use the same shape.
- Outcome and critical-journey statement.
- Non-functional target table: availability, latency, durability, throughput.
- Failure-behavior table: per dependency, the required behavior on slow, down, and error.
- Edge and error-behavior list: malformed input, boundary values, partial failure, retries.
- Abuse and misuse case list for handoff to `secure-sdlc-and-threat-modeling`.
- Explicit non-goals and scope bound.
- Acceptance criteria, one per failure behavior, each checkable by a test.

## Checks Before Moving On

- `failure_behavior`: every named dependency has a defined behavior on slow, down, and error.
- `nonfunctional_targets`: availability, latency, durability, and throughput targets are stated and routed.
- `edge_behavior`: malformed input, boundary values, and partial failure have defined behavior.
- `non_goals`: scope is bounded with explicit non-goals.
- `testable_criteria`: every behavior has an acceptance criterion a test can check.
- `handoffs`: targets, threats, and test placement are routed to their specialists.

## Red Flags - Stop And Rework

- The spec names only the happy path.
- A dependency is used with no stated behavior for its failure.
- Acceptance criteria are aspirations, not checkable conditions.
- Non-functional targets are absent or vague.
- The spec drifts into product prioritization instead of failure behavior.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Specify only what the feature does when it works | Specify what it does when each dependency fails. |
| Leave targets implicit | State availability, latency, durability, throughput and route them. |
| Write untestable acceptance criteria | Make each criterion checkable by a test. |
| Treat this as product requirements | Own the resiliency contract; route value and priority out. |
