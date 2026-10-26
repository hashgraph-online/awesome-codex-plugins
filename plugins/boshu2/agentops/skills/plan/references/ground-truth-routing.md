# Optional probes and prototypes

Use this method only when an observation could change a consequential approach
or clarify the caller's reaction to concrete behavior. First inspect existing
evidence: a clear task or an already answered question needs no prototype.

Before running anything, state in the existing intent or handoff:

1. The question and assumption under test, including the accepted behavior that
   must remain true.
2. The discriminator: competing predictions and the observation that would
   distinguish them. A mock-up may elicit a caller preference; it cannot prove
   runtime behavior, durability or integration that it does not exercise.
3. The disposable scope, authorized inputs/destination and real time or cost
   bound. Use the smallest safe construction; do not touch production or widen
   write authority to make a prototype realistic.
4. The stop: sufficient distinguishing evidence, an inaccessible prerequisite,
   no useful new observation, or the existing resource limit. A stopped or
   inconclusive probe leaves the assumption unresolved; it does not justify
   retrying until the preferred answer appears.

Choose relevant ground truth, not a compulsory sequence:

| Question | Useful evidence or discriminator |
|---|---|
| Does an external substrate already provide the needed behavior? | Current vendor documentation and pinned stock behavior; run a vanilla quickstart only when it answers the named uncertainty. Compare proposed additions with native capabilities before rebuilding them. |
| Can the repository's existing approach satisfy the example? | Trace its relevant behavior and try the simplest acceptance-relevant change or test. Retain evidence if it cannot meet the example. |
| Can a new path work end to end? | A walking skeleton through the uncertain boundary, with an observable result. |
| Does a proposed rule or state model hold up in cases hard to judge on paper? | A small pure model (plain functions, a reducer, or an explicit state machine when which actions are legal is in question) kept apart from any display. The caller or a domain expert drives it in domain terms with no setup, from one known starting state, through the ordinary case, a hard edge and an action that should be refused, seeing the labelled state after each step. Rules it confirms still face Implement's checks once moved into the real module. |
| Which interaction does the caller want? | A small concrete mock-up and the caller's response; only the caller settles that preference. |

For a mock-up or model the caller drives or reacts to, keep real whatever is
being judged: a flow or state question needs something they can drive, a
question of finish (palette, type, density) needs that finish, and placement
can stay rough. Disposable work skips tests, abstraction and hardening, never
the judged dimension. Say what to judge and what to ignore. When no available
medium can show that dimension honestly, report the missing capability rather
than offering a stand-in. Before handing it over, look at each option as
rendered, not only that it loaded, and try every interaction you ask the
caller to try; if you cannot see the result, say so.

Return the observation, its source/configuration, limitations, and the decision
or next question it supports. Preserve failed predictions as evidence. If a
documented native path needs a deviation, retain its reason and support in the
existing intent. Keep only decision-relevant details and pointers in the
existing handoff, not the whole experiment transcript. Disposable work is not a
production implementation; retain or remove it under the caller's ownership and
storage policy. New proof uses the existing protected external storage boundary
when applicable. A prototype cannot change intent, authorize implementation or
establish acceptance; promising results still face implementation checks and a
fresh exact-content judgment.

## Reuse after source drift

Before reusing inherited prototype evidence, check the current interface and
environment against the observation's recorded source/configuration; an
unrelated change needs no repeat. If a change could affect the named result,
keep the earlier observation with its context, rerun only the smallest
discriminating probe against the current subject and record the new result in
the existing intent or handoff. If the assumption cannot be checked or rerun,
leave the question unresolved and continue only work that does not rely on it.

## Compare interfaces from the caller's side

Use only when the accepted behavior has materially different plausible
interfaces. Sketch the ordinary caller and one consequential failure case for
at most two alternatives before implementing either. Include setup, required
call order, state ownership and error handling, not just function signatures.
One alternative can keep the existing boundary. Sequential sketches suffice;
this method grants no delegation authority.

Compare which facts each caller must learn, which repeated rule the boundary
owns, and where the next acceptance-relevant change would land. Include the
migration cost for existing callers. Prefer the option that removes concrete
coordination without exporting implementation details. A shorter signature
that makes callers carry hidden ordering or recovery rules is not simpler.
If neither option improves the actual callers, retain the current interface.
Use a bounded probe above only for a difference the sketches cannot settle;
record the chosen tradeoff in the existing intent, not a new design document.
