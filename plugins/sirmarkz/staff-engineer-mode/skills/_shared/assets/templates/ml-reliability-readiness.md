# ML Reliability Readiness

## Readiness Checklist

| Area | Requirement | Evidence | Gap |
| --- | --- | --- | --- |

## Data And Feature Validation

| Feature/Data | Validation | Drift Signal | Owner |
| --- | --- | --- | --- |

## Training-Serving Skew Review

| Feature Or Transform | Training Source | Serving Source | Skew Check | Gap |
| --- | --- | --- | --- | --- |

## Evaluation Plan

| Eval | Slice | Threshold | Rollback Trigger |
| --- | --- | --- | --- |

## Failure-Mode And Adversarial Evaluation

| Failure Mode | Misuse Or Dependency Manipulation | Eval | Response |
| --- | --- | --- | --- |

## Artifact Lineage

| Artifact | Version | Source | Training Data | Approval |
| --- | --- | --- | --- | --- |

## Serving Control State

| Control Item | Expected State | Failure Mode | Rollback Or Restore Path | Verification |
| --- | --- | --- | --- | --- |

## Serving Deployment Readiness

| Artifact Or Model Class | Size Or Provisioning Need | Serving Substrate | Readiness Signal | Fallback |
| --- | --- | --- | --- | --- |

## Model Routing Control Plane

| Model Or Class | Availability Source | Routing Selection Signal | Critical Rollout Wave | False-Unavailable Check | Verification |
| --- | --- | --- | --- | --- | --- |

## Rollout And Monitoring

| Stage | Quality Signal | Freshness Signal | Latency/Capacity | Rollback |
| --- | --- | --- | --- | --- |

## Incident Path And Residual Risk

| Risk Or Incident Path | Response | Residual Risk | Owner |
| --- | --- | --- | --- |
