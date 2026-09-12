# Ground-truth routing

Loaded by `SKILL.md` at the routing step. Every plan needs a ground truth
outside the planner's own reasoning: classify the work, then name its ground
truth, its control experiment, and its deviation ledger from the matching row.

| Work type | Ground truth | Control experiment | Deviation ledger |
|---|---|---|---|
| Integrate an external substrate, runtime, tracker, or service | the vendor's own docs plus stock behavior | run their vanilla quickstart on pinned versions with zero local code, before designing | each deviation from the documented flow, each justified; and every component you write that has a native counterpart in the substrate |
| Extend this project | the repo's existing patterns and behavior spec | the simplest version that satisfies acceptance, and why it is insufficient | each novelty introduced: new abstraction, dependency, or pattern |
| Greenfield | reference experience and domain prior art | a walking skeleton | each deviation from the boring default, ~one novelty per change |

The Extend row is the repo's default discipline: behavior-first acceptance,
RED -> GREEN, the smallest real change. The Integrate row's mechanics: the
stock-quickstart control run and the deviation ledger from the documented
flow: apply only to integration-class work (adopting or wiring in an
external substrate, runtime, tracker, or service). That row is the one that
is cheap to skip and expensive to have skipped: run the stock control
experiment *before* you design, or you re-plumb what the substrate already
documents and inherit bugs you built yourself.
