---
name: navigate
description: 'Pick the next work in an epic or bead graph; closed is not proven. Use when: asked what is next or whether an epic is done.'
practices: [lean-startup, bdd-gherkin, ddd-bounded-context]
hexagonal_role: supporting
consumes: [outer-goal-prompt, goal-acceptance, native-work-state, validation-result]
produces: [native-handoffs]
context_rel: [{kind: customer-of, with: craft-goal}, {kind: supplier-to, with: orchestrate}]
skill_api_version: 1
user-invocable: true
metadata:
  tier: execution
  dependencies: []
  capabilities: [observe_work_graph, select_next_wave, ratchet_work_graph, report_graph_hygiene]
  effects: [update_native_graph]
  canonical_status: canonical
  disposition: keep_strategy
  stability: stable
output_contract: 'wave checkpoint in the existing handoff or root epic: acceptance matrix, frontier, wave and reasons, ratchets and churn, budget, helper use and native state, next thesis, open decisions; a single pass returns it with hygiene findings and writes nothing'
---

# Navigate

Pick the next wave on a bead graph and keep the graph honest toward its frozen
acceptance. The root epic holds acceptance; each child bead is one experiment
with one RPI. Navigate never edits acceptance, dispatches, judges or closes:
Craft Goal owns the prompt and HOLD, [Plan](../plan/SKILL.md) shapes a bead,
[Orchestrate](../orchestrate/SKILL.md) dispatches, RPI runs,
[Validate](../validate/SKILL.md) judges.

**One pass**, when a person asks what is next on an epic: steps 1 and 2 plus
[hygiene](#hygiene), returning the wave in the step 4 shape instead of handing
it off. Write nothing; change edges only on the caller's go-ahead; stop after
one pass. **Each wave of a running goal:** steps 1 to 4.

## Rules that decide the pick

- **Closed is not proven.** Only cited evidence for a criterion proves its row:
  the passing check that exercises it, or the Validate PASS where a fresh read
  was required. Closed status, a merge or an approving note leaves it open.
- **Serve an open row.** Pick only ready beads that serve an open criterion or
  a named blocking uncertainty; a bead tied to none is a hygiene finding.
- **Stay disjoint.** Picked write and generated scopes overlap neither each
  other nor any in-flight bead; an overlapping ready bead waits.
- **Ready is a tracker state.** An empty ready list does not prove completion;
  a closed prerequisite with missing or stale bytes is not usable readiness.

## Speak the domain

- **BDD:** each criterion is a Given/When/Then example with an observable
  result. Each bead names the example it moves; a bead that lacks one gets
  Plan first inside its RPI.
- **DDD:** the root epic defines each domain term once, in one line. Titles,
  examples, code and tests reuse that exact word. A synonym is a hygiene
  finding; [Domain](../domain/SKILL.md) settles disputes.
- Write a bead as its title, then its id: `Locale fallback test (ag-12)`.

## Bead graph contract

Root epic: outcome, acceptance examples, non-goals, authority, domain terms.
Child bead: the question and the criterion or uncertainty it serves; method,
expected observation, falsifier, scope, non-goals; notes enough to resume
after compaction; verdict, evidence refs, learning.

Edges: `parent-child` for membership, `blocks` only for real ordering, `related`
for alternatives, `discovered-from` for provenance. A requested retrospective
never `blocks` code judgment; both stay required.

The tracker owns status and closing. BD is the example; any tracker with
status, dependencies and notes fits. With BD, run `bd context --json` before any
write; BR is a different tool, never a fallback or alias for BD. `bv` rank is advice; live BD beats it and any saved plan.

## 1. Observe

```bash
bd context --json                   # verify the destination first
bd show <epic>                      # outcome, acceptance, domain terms
bd children <epic>                  # direct children only; recurse into child epics
bd ready --parent <epic> --json     # ready frontier across descendants
bd blocked --parent <epic>          # blocked work
bd show <bead>; bd comments <bead>  # prior verdicts and evidence refs
```

Build the acceptance matrix (criterion, evidence, status) under the rules
above; note in-flight beads with their scopes and any result limit you hit.
Done when every criterion has a row and every open row names its bead, blocker
or gap.

## 2. Pick the wave

When every row is proven, or no ready bead serves an open row, pick nothing,
say which, and go to step 4. Otherwise pick the smallest set of ready beads
with the most decision-relevant information that meets the rules above and
fits the declared wave budget; no budget means one bead. Prefer an early
falsifier.

Hand each bead to one RPI: through Orchestrate or Agent Native when delegation
is authorized, one bead per worker, otherwise the caller's runtime. Its checks
and CI are its result; it gets one fresh, author-distinct Validate only when
the caller asks, a mistake cannot be cheaply undone after it lands, or no
deterministic check covers the changed behavior, and a repair does not start
another. Done when each picked bead has a one-line reason and a named handoff.

## 3. Ratchet the graph

Record each result unchanged on its bead: the check facts, and the verdict when
one was obtained. For example
`bd update <id> --append-notes "verdict: FAIL; evidence: <refs>; learned: <decision it changes>"`.
Update its matrix row, then classify each discovery:

| Discovery | Action |
|---|---|
| Needed for frozen acceptance, within authority and budget | `bd create "<title>" --parent <epic> --deps discovered-from:<id> --acceptance "<example it serves>"` |
| Useful later | note or link it outside the epic; never run it in this goal |
| Changes acceptance, exceeds authority or budget | HOLD; the goal's breaker takes over |

A result ratchets when it proves part of acceptance, falsifies a live
hypothesis with discriminating evidence, or resolves an uncertainty so the next
experiment differs; FAIL and NOT_PROVEN can ratchet. Commits, counts, digests,
rewritten plans and red with no new information are churn. Split old defects
from regressions by before/after reproduction or equivalent causal evidence
under the same acceptance; counts, timestamps and new ids prove no cause.
Unknown cause, a reopened finding or recurrence of a closed finding class is
HOLD, not proof the design is wrong. Keep necessary findings necessary; nothing
resets a total. Done when every result sits on its bead and every discovery
has a class.

## 4. Checkpoint

Append this block to the existing handoff or root epic notes; no new artifact.
Stop after appending it: the goal continues, holds or ends. A one-pass reply
uses the same block, writes nothing, and marks Ratchets, Budget and Helper
`n/a`.

```text
Acceptance: <id> <Given/When/Then>: proven (<check or PASS ref>)
            <id> <Given/When/Then>: open (<bead title> <id>, or the gap)
Frontier:   <ready beads, by title>
Wave:       <bead title>: <row or uncertainty it serves>; or none: <why>
Ratchets:   <results that changed a decision>; churn: <results that did not>
Hygiene:    <one finding per line>, or none
Budget:     <remaining if measured, else unmeasured>
Helper:     <HOLD incident and helper use, or none>; native state: <observed continue/stop>
Next:       <thesis>; decisions: <open questions for the caller>
```

## Hygiene

Report cycles among the epic's beads (`bd dep cycles`, filtered to them),
beads tied to no criterion, `blocks` edges that are not real ordering,
criteria with no observable result (an open decision the caller can settle
with Interview; never rewrite one), closed beads with missing bytes and
drifted terms. `bd graph <epic>` shows the shape. Change edges only on the
caller's go-ahead.
