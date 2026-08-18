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

## Content Moderation And System-Prompt Confidentiality

| Surface | Content Policy And Affected Users | Moderation Applicability Or N/A Rationale | Input/Output Checks | False-Positive/Escalation Behavior | System-Prompt Confidentiality Rule | Verification |
| --- | --- | --- | --- | --- | --- | --- |

## Output Sink Handling

| Sink | Validation | Escaping/Redaction | Downstream Risk | Stop Condition |
| --- | --- | --- | --- | --- |

## Red-Team And Eval Plan

| Scenario | Expected Defense | Regression Check | Owner |
| --- | --- | --- | --- |

## Red-Team Scope Or Risk-Based Skip

| Scope Or Skip Rationale | Attacker Goals/Prohibited Actions | Safety Constraints | Success Criteria | Finding Severity | Retest Criteria | Owner |
| --- | --- | --- | --- | --- | --- | --- |

## Emergency Stop Paths

| Artifact | Disable/Rollback Path | Owner | Verification |
| --- | --- | --- | --- |

## Storage, Logging, And Privacy

| Record Or Data | Reference/Summary/Raw Decision | Minimum Need | Prohibited Fields | Redaction | Access | Retention | Integrity | Disposal |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

## Session Isolation

| Boundary | Leakage Test | Expected Result | Evidence |
| --- | --- | --- | --- |

## Supply-Chain Record

| Artifact | Version | Source | Integrity Check | Eval Result | Rollback Target | Retire By |
| --- | --- | --- | --- | --- | --- | --- |
