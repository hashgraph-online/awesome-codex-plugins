# Feature Flag Lifecycle

## Flag Inventory

| Flag | Category | Declaration Site | Expiry | Current Production Value Per Environment | Owner |
| --- | --- | --- | --- | --- | --- |

| Flag | Safe Fallback | Outage Behavior | Branch Count |
| --- | --- | --- | --- |

## Orphan Report

| Flag | Missing Classification? | Past Expiry? | Unsafe Fallback? | Identical Branches? |
| --- | --- | --- | --- | --- |

| Flag | Unreachable Branch? | Stale Evaluation? | Registry/Code Mismatch? | Action |
| --- | --- | --- | --- | --- |

## Overrides

| Flag | Tenant/Cohort/Location | Reason | Removal Condition | Owner |
| --- | --- | --- | --- | --- |

## Branch Map

| Flag | Branch | Call Sites | Tests | Cleanup Step |
| --- | --- | --- | --- | --- |

## Removal Plan

| Flag | Target Value | Cleanup Order | Rollback | Verification |
| --- | --- | --- | --- | --- |

## Standing Rule

- Create-time expiry/category/safe-fallback rule:
- Renewal cadence:
- Orphan detection:

## Flag-Debt Scorecard

| Metric | Current | Target | Action |
| --- | --- | --- | --- |
| Total flags by category |  |  |  |
| Percent past expiry |  |  |  |
| Percent without orphan count |  |  |  |
| Oldest live flag age |  |  |  |
| Removal velocity |  |  |  |
