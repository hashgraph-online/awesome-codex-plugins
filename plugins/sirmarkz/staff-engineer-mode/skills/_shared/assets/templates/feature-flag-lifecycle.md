# Feature Flag Lifecycle

## Flag Inventory

| Flag | Category | Lifecycle Date Type | Removal Expiry Or Next Review | Retirement Condition | Declaration Site | Current Production Value Per Environment | Responsibility |
| --- | --- | --- | --- | --- | --- | --- | --- |

| Flag | Safe Fallback | Outage Behavior | Branch Count |
| --- | --- | --- | --- |

## Orphan Report

| Flag | Missing Classification? | Past Removal Or Review? | Unsafe Fallback? | Identical Branches? |
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

- Temporary removal-expiry defaults:
- Long-lived review cadence:
- Create-time category/lifecycle/responsibility/safe-fallback/retirement rule:
- Orphan detection:

## Flag-Debt Scorecard

| Metric | Current | Target | Action |
| --- | --- | --- | --- |
| Total flags by category |  |  |  |
| Orphan count |  |  |  |
| Temporary flags past removal expiry |  |  |  |
| Long-lived controls past review |  |  |  |
| Oldest overdue lifecycle date |  |  |  |
| Temporary-flag removal velocity |  |  |  |
