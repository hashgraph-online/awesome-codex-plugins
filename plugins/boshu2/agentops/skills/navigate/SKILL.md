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

Pick the next wave (the ready beads run together next) on a bead graph and
keep the graph honest toward its frozen acceptance. The root epic holds
acceptance; each child build bead is one experiment; a decision bead goes to
the resolver it names ([Foggy epics](#foggy-epics)). Navigate picks and
records, and never edits acceptance, dispatches, judges or closes:
[Plan](../plan/SKILL.md) shapes, [Orchestrate](../orchestrate/SKILL.md)
dispatches, native execution (the caller's coding agent and shell) or an
optional [RPI](../rpi/SKILL.md) run builds, [Validate](../validate/SKILL.md)
judges, and Craft Goal owns the prompt and HOLD (the goal's stop on a
declared trigger, so the cause can be examined before more work runs).

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
  a closed prerequisite with missing or stale bytes (the output it claims is
  absent or out of date) is not usable readiness.

## Speak the domain

- **BDD:** each criterion is a Given/When/Then example with an observable
  result. Each bead names the example it moves; a bead that lacks one gets
  Plan before it is built.
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
for alternatives, `discovered-from` for provenance. The tracker owns status and
closing. BD (Beads) is the example; any tracker with status, dependencies and
notes fits. With BD, run `bd context --json` before any write. Beads Viewer
(`bv`) rank is advice; live BD beats it and any saved plan.

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

Hand each build bead to native execution, or to one RPI when the goal or
caller selects it: through Orchestrate or Agent Native when delegation is
authorized, one bead per worker, otherwise the caller's runtime. Its checks
and CI are its result; it gets one fresh, author-distinct Validate only on
[Validate's triggers](../validate/SKILL.md#when-a-fresh-judgment-is-worth-it),
and a repair does not start another. A [decision bead](#foggy-epics) goes to
the resolver it names, never to an implementer; one that needs the caller's
answer goes under decisions in the checkpoint. Done when each picked bead has a
one-line reason and a named handoff.

## 3. Ratchet the graph

Record each result unchanged on its bead: the check facts, and the verdict when
one was obtained. For example
`bd update <id> --append-notes "verdict: FAIL; evidence: <refs>; learned: <decision it changes>"`.
Update its matrix row, then classify each discovery:

| Discovery | Action |
|---|---|
| **necessary-now**: needed for frozen acceptance, within authority and budget | `bd create "<title>" --parent <epic> --deps discovered-from:<id> --acceptance "<example it serves>"` |
| **linked-follow-up**: useful later | note or link it outside the epic; never run it in this goal |
| **HOLD/rescope**: changes acceptance, exceeds authority or budget | HOLD; the goal's breaker (the HOLD triggers its prompt declares) takes over |

A result ratchets when it proves part of acceptance, falsifies a live
hypothesis with discriminating evidence, or resolves an uncertainty so the next
experiment differs; FAIL and NOT_PROVEN can ratchet. Commits, counts, digests,
rewritten plans and red with no new information are churn. Split old defects
from regressions by before/after reproduction or equivalent causal evidence
under the same acceptance; counts, timestamps and new ids prove no cause.
Unknown cause, a reopened finding or recurrence of a closed finding class is
HOLD, not proof the design is wrong. Never downgrade a necessary-now discovery to
a linked follow-up; no wave, helper, retry or compaction resets the goal's budget
totals. Done when every result sits on its bead and every discovery has a class.

## 4. Checkpoint

Append this block to the existing handoff or root epic notes; no new artifact.
Stop after appending it: the goal continues, holds or ends. A one-pass reply
drops the Ratchets, Budget and Helper lines and writes nothing.

```text
Acceptance: <id> <criterion as written>: proven (<check or PASS ref>)
            <id> <criterion as written>: open (<bead title> <id>, or the gap)
Frontier:   <ready beads, by title>
Wave:       <bead title>: <row or uncertainty it serves>; or none: <why>
Ratchets:   <results that changed a decision>; churn: <results that did not>
Fog:        <proposed decision beads>; questions: <not yet beads>; ruled out: <work>; or none
Hygiene:    <one finding per line>, or none
Budget:     <remaining if measured, else unmeasured>
Helper:     <HOLD incident and helper use, or none>; native state: <observed continue/stop>
Next:       <thesis>; decisions: <open questions for the caller>
```

## Foggy epics

When the outcome is clear but the way there is not, the next beads are
decisions, not build slices. Each open question becomes a decision bead whose
answer is a choice, sized to one session, naming how it resolves: a cited
fact (Research), a rough artifact the caller reacts to (Plan's probes and
prototypes), a conversation with the caller (Interview), or a manual step that
only unblocks a decision. Give it the tracker's decision type, never a build or
agent-ready label (with BD, `bd create --type decision`, or
`bd update <id> --type decision --remove-label agent-ready` for a decision
already filed as build work). Plain `bd ready` lists decisions too; pull build
work with `bd ready --parent <epic> --exclude-type decision`. A question that
needs the caller's own answer resolves only with the caller; never answer it
on their behalf, whether by a default, a recommendation or filing it as
ruled-out work.

Track two lists with the root epic: in-scope questions not yet specific
enough to become beads, which graduate as the frontier moves, and work ruled
out by the caller or the epic's non-goals, which does not come back without
the caller. Record each resolved decision as one line plus its bead, not a
restatement. The fog has lifted when no decision stands between the graph and
build beads with acceptance examples; hand those to Plan.

In a one-pass reply, return the proposed decision beads and both lists in the
checkpoint's Fog line and write nothing. In a running goal, create beads and
append notes through step 3, within authority and the declared wave budget;
decision beads count against that budget like any other.

## Hygiene

Report cycles among the epic's beads (`bd dep cycles`, filtered to them),
beads tied to no criterion, `blocks` edges that are not real ordering,
criteria not in Given/When/Then form or with no observable result (an open
decision the caller can settle with Interview; never rewrite one), closed
beads with missing bytes, decision beads typed as build work, and drifted
terms. `bd graph <epic>` shows the shape. Change edges only on the caller's
go-ahead.
