# First-Principles Review

## Scope and Boundary

This is a bounded, non-exhaustive review of `fixtures/target-prd.md`; it does not edit that
target.

## Research Receipt

| Evidence read | Finding | Status |
|---|---|---|
| `fixtures/target-prd.md:1-12` | The proposal assumes a queue and a universal ten-second target. | verified |
| Provider documentation | Batching support is unavailable from local evidence. | unknown |

## True Outcome

Customers need timely, understandable notifications for events that matter; the ten-second
target is an implementation proposal, not the outcome.

## Constraint and Assumption Analysis

| Claim | Classification | Evidence | State |
|---|---|---|---|
| Immediate delivery preference | owner preference | `fixtures/target-prd.md:10` | evidence-backed |
| Provider cannot batch | inherited assumption | `fixtures/target-prd.md:11` | unproven |
| Legal deadline | hard constraint | no supplied source | unproven |

## Premise Ledger

| Premise | State | Challenge | Result |
|---|---|---|---|
| Ten seconds is required for every event | unproven | inversion | falsified for low-priority events |
| A new queue is required | inherited | incumbent comparison | unproven |
| Provider cannot batch | unproven | research receipt inspection | unknown |

## Alternatives

| Alternative | Class | Why it is distinct |
|---|---|---|
| Eliminate low-value notifications | eliminate the need | Removes demand. |
| Use provider scheduling for low priority | reuse incumbent capability | Reuses the incumbent. |

## Primary Recommendation

**Disposition:** REFRAME

Use priority-based delivery: eliminate low-value messages and test provider scheduling before a
queue. The current proposal adds an irreversible worker fleet before the universal latency
premise is proven.

## Falsifiers

Reverse this if a customer-impact study proves low-priority events require ten-second delivery,
or a production-shaped provider trial misses a documented priority deadline.

## Owner Decisions

Open decision: choose the customer-impact threshold for high priority.

## PRD Handoff

```json
{"true_problem":"Deliver timely, understandable notifications for events that matter.","constraints":[{"claim":"Immediate delivery preference","classification":"owner preference","evidence":"fixtures/target-prd.md:10","state":"evidence-backed"},{"claim":"Provider cannot batch","classification":"inherited assumption","evidence":"fixtures/target-prd.md:11","state":"unproven"}],"premises":[{"claim":"Ten seconds is required for every event","state":"unproven","challenge":"inversion","result":"falsified for low-priority events"},{"claim":"A new queue is required","state":"inherited","challenge":"incumbent comparison","result":"unproven"},{"claim":"Provider cannot batch","state":"unproven","challenge":"research receipt inspection","result":"unknown"}],"selected_direction":{"disposition":"REFRAME","recommendation":"Use priority-based delivery before building a queue.","falsifiers":["Customer-impact study requires ten-second low-priority delivery.","Provider trial misses a documented priority deadline."],"split_outcomes":[]},"rejected_alternatives":[{"name":"Dedicated worker fleet","reason":"Adds complexity before the latency premise is proven."}],"experiments":["Measure customer impact by notification priority.","Run a provider scheduling trial."],"acceptance_implications":["Define priority classes and evidence thresholds.","Do not require a worker fleet without experiment evidence."],"open_owner_decisions":["Choose the customer-impact threshold for high priority."],"research_receipt":[{"source":"fixtures/target-prd.md:1-12","finding":"Queue and ten-second target are proposed.","status":"verified"},{"source":"Provider documentation","finding":"Batching support is unavailable from local evidence.","status":"unknown"}],"calibration":{"verified_facts":["The target proposes a queue."],"inferences":["Priority-based delivery may satisfy the outcome."],"unknowns":["Whether the provider supports batching."]}}
```
