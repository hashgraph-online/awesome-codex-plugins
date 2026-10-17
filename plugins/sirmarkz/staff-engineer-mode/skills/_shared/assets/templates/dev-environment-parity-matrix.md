# Development Environment Parity Matrix

## Scope

- Critical workflow:
- Environments compared:
- Production source of truth:

## Required Parity Taxonomy

| Dimension | Must Match | May Diverge With Reason | Forbidden In Non-Prod |
| --- | --- | --- | --- |

## Parity Matrix

| Dimension | Local | CI | Preview/Ephemeral | Staging | Production |
| --- | --- | --- | --- | --- | --- |

| Dimension | Required Parity | Allowed Divergence |
| --- | --- | --- |

## Drift Budget

| Dimension | Budget | Detection Method | Action When Exceeded | Owner |
| --- | --- | --- | --- | --- |

## Drift Detection

| Dimension | Comparison Method | Cadence | Source Of Truth | Change Path |
| --- | --- | --- | --- | --- |

## Ephemeral And Preview Contract

| Dimension | Replicated Or Diverged | Meaning Of Passing Run | Limitation |
| --- | --- | --- | --- |

## Preflight Parity

| Critical Path | Required Result | Intentional Divergence | Meaningful? |
| --- | --- | --- | --- |

## Third-Party Stand-Ins

| Dependency | Stand-In/Sandbox/Production Endpoint | Parity Gaps | Explicit Authority | Constrained Identity | Data Controls | Rate/Side-Effect Bounds | Stop Path | Recovery |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

## Reproduction Protocol

| Failure | Environment Order | Isolation Step | Production Evidence Method | Authority For Active Mutation | Blast-Radius/Data Controls | Stop Criteria | Recovery | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

## Follow-Up Routes

| Gap | Follow-Up Surface | Reason |
| --- | --- | --- |
