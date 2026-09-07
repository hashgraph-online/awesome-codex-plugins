# Test strategy

## Choose the lowest reliable layer

| Layer | Best for |
|---|---|
| Unit | Pure logic, state transitions, parsers, and boundary conditions |
| Component | UI behavior and isolated framework components |
| Integration | Database, queue, filesystem, or service adapter behavior |
| Contract | Producer/consumer schemas and public compatibility |
| End-to-end | A small number of critical user journeys |

Use a higher layer only when the lower layer cannot observe the risk.

## Specialized methods

Use these when the risk justifies them; they are not a checklist for every
change.

| Method | Use when | Evidence |
|---|---|---|
| Property-based or fuzz | Input spaces, parsers, serializers, or invariants have many combinations | Minimal failing example plus the preserved property/seed |
| Performance/load | Latency, throughput, saturation, or concurrency limits are part of the contract | Reproducible workload, baseline, percentile results, and environment |
| Soak | Leaks, queue buildup, or degradation appears over time | Duration, resource trend, error rate, and cleanup result |
| Resilience/fault injection | Timeouts, retries, partial failure, failover, or recovery matter | Injected fault, bounded blast radius, observed degradation, and recovery |
| Accessibility | Rendered UI, interaction, focus, announcements, or contrast changes | Automated checks plus keyboard and assistive-technology-aware inspection |
| Mutation | A critical suite may pass without asserting important behavior | Surviving mutations mapped to weak or missing assertions |

Run performance and resilience tests only in an authorized, isolated environment
with explicit limits and cleanup. A local microbenchmark is not proof of
production capacity.

## Bug regression

1. Reduce the failing scenario.
2. Write a test that fails for the right reason.
3. Confirm the failure before implementation when feasible.
4. Apply the fix.
5. Confirm the new test and nearby suite pass.
6. Keep the test focused on the externally visible regression.

## Flaky tests

Classify before changing:

- uncontrolled time or randomness;
- shared mutable state;
- order dependence;
- asynchronous race;
- external service instability;
- resource exhaustion;
- environment mismatch.

Fix the source. Use retries only when the product contract itself includes retry behavior.

## Test quality questions

- Can the test fail for an unrelated reason?
- Does it assert the important result?
- Is setup larger than the behavior under test?
- Are mocks preserving the real contract?
- Would a future refactor keep the test valid?
- Is the failure output useful?

## Coverage

Use line or branch coverage as a signal, not the goal. Prioritize authorization, money, data integrity, concurrency, migrations, and critical workflows even when headline coverage is high.
