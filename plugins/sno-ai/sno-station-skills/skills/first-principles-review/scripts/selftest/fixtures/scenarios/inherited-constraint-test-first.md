# Inherited constraint scenario

## Scope and Boundary

This is a bounded, non-exhaustive static scenario for an inherited constraint; no reviewed input is edited.

## Research Receipt

`fixtures/target-prd.md:1-12` proposes a queue; provider batching remains unknown.

## True Outcome

Deliver high-priority account notifications reliably.

## Constraint and Assumption Analysis

Privacy retention is a hard constraint. A dedicated queue is an inherited assumption.

## Premise Ledger

The dedicated queue premise is unproven; incumbent comparison requires a production-shaped trial.

## Alternatives

Reuse an incumbent provider batch API; make the smallest viable change with a priority classifier.

## Primary Recommendation

**Disposition:** TEST-FIRST

Run a provider trial before selecting queue architecture.

## Falsifiers

A provider trial cannot meet the documented priority deadline.

## Owner Decisions

No owner decision remains until the trial result exists.

## PRD Handoff

```json
{"true_problem":"Deliver high-priority account notifications reliably.","constraints":[{"claim":"Privacy retention","classification":"hard constraint","evidence":"policy source","state":"evidence-backed"},{"claim":"Dedicated queue","classification":"inherited assumption","evidence":"fixtures/target-prd.md:4-5","state":"unproven"}],"premises":[{"claim":"A dedicated queue is required","state":"unproven","challenge":"incumbent comparison","result":"provider capability remains unknown"}],"selected_direction":{"disposition":"TEST-FIRST","recommendation":"Run a provider trial.","falsifiers":["Provider trial cannot meet the priority deadline."],"split_outcomes":[]},"rejected_alternatives":[{"name":"Dedicated queue","reason":"The requirement is unproven."}],"experiments":["Run a provider trial."],"acceptance_implications":["Record measured priority delivery."],"open_owner_decisions":[],"research_receipt":[{"source":"fixtures/target-prd.md:1-12","finding":"Queue is assumed.","status":"verified"}],"calibration":{"verified_facts":["Privacy retention"],"inferences":["Provider may suffice."],"unknowns":["Provider batching"]}}
```
