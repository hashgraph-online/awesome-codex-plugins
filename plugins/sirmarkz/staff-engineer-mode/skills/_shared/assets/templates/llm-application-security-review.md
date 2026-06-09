# LLM Application Security Review

## Use And Harm Context

| Item | Decision Or Boundary |
| --- | --- |
| Intended use |  |
| Affected users |  |
| Misuse |  |
| Unacceptable harm |  |
| Escalation/override context |  |

## Trust Boundary Map

| Boundary | Data/Capability Crossing | Threat | Control |
| --- | --- | --- | --- |

## Prompt, Retrieval, Tool, And Output Permissions

| Surface | Allowed Inputs | Allowed Actions | Confirmation | Rate Limit | Audit |
| --- | --- | --- | --- | --- | --- |

## Retrieval And Tenant Boundaries

| Corpus/Index | Tenant Scope | Access Rule | Leakage Test | Rollback |
| --- | --- | --- | --- | --- |

## Input, Feedback, And Output Validation

| Surface | Validation | Rejection/Repair | Downstream Sink |
| --- | --- | --- | --- |

## Output Sink Handling

| Sink | Validation | Escaping/Redaction | Downstream Risk | Stop Condition |
| --- | --- | --- | --- | --- |

## Red-Team And Eval Plan

| Scenario | Expected Defense | Regression Check | Owner |
| --- | --- | --- | --- |

## Emergency Stop Paths

| Artifact | Disable/Rollback Path | Owner | Verification |
| --- | --- | --- | --- |

## Storage, Logging, And Privacy

| Data | Access Rule | Retention | Logging/Redaction |
| --- | --- | --- | --- |

## Session Isolation

| Boundary | Leakage Test | Expected Result | Evidence |
| --- | --- | --- | --- |

## Supply-Chain Record

| Artifact | Version | Source | Integrity Check | Eval Result | Rollback Target | Retire By |
| --- | --- | --- | --- | --- | --- | --- |
