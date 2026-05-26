# Optimization Proof Loop

Use this reference when optimization work risks changing behavior or making code harder to maintain.

## Proof Contract

An optimization is acceptable only when all four claims are proven:

1. Same externally visible behavior.
2. Same or better correctness tests.
3. Better target metric under the same scenario.
4. No meaningful regression in readability, memory, latency, or operability.

## Opportunity Matrix

| Opportunity | Evidence needed |
|---|---|
| Hot loop allocation | Allocation profile and benchmark delta. |
| Algorithmic change | Complexity argument plus golden or conformance tests. |
| Caching | Freshness invariant and invalidation test. |
| Concurrency | Race/deadlock evidence and load comparison. |
| I/O batching | Before/after call counts and latency percentiles. |

## Keep Or Revert

Keep the change when improvement exceeds measurement noise and the behavior proof is intact. Revert or file follow-up when the benchmark improves but the proof is incomplete.

---

**Source:** Adapted from an external skill corpus / `extreme-software-optimization`. Pattern-only, no verbatim text.
