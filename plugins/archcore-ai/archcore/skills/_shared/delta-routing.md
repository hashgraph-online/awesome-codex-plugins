# Delta Routing — Conductor Contract for Claim-Level Selection

Plugin runtime asset. Loaded by the `plan` skill (`/archcore:plan`) at its Select
step. The context record it reads is defined in `skills/_shared/gate-contract.md`,
section Context resolution. Gate execution, state block, and resume rules:
`skills/_shared/gate-contract.md`. Interview mechanics and the ceiling:
`skills/_shared/elicitation-contract.md`. Capability sizing:
`skills/_shared/capability-granularity.md`. The conductor selects the documents
a change needs and owns every cross-instrument sequence; instruments produce the
documents.

## Vocabulary

One term per concept. Do not introduce synonyms.

- **canon** — the accepted document graph in `.archcore/`, local and global.
- **capability** — one behavior an external consumer relies on, recordable as
  one `spec`; sizing rules in `skills/_shared/capability-granularity.md`.
- **claim** — one unit of intended or observed change: subject and consumer,
  baseline owner, proposed claim, evidence, verification, and one action —
  `create`, `amend`, `retire`, or `none`.
- **claim ledger** — the list of claims of one invocation; the plan records it
  under `## Declared Delta`, and closeout reconciles it.
- **unknown** — one material open question with its kind (`fact`, `choice`,
  `feasibility`, `acceptance`), evidence state (`supported`, `missing`,
  `conflicted`), candidate sources, and next action.
- **hazard** — one evidenced risk: trigger → consequence → required check →
  owner of the check.
- **document need** — a future reader task that no existing document serves.
- **operational procedure** — a human-performed sequence the change introduces:
  install, migrate, operate, or verify steps.

The retired route names (`null`, `decision`, `amendment`, `capability`,
`umbrella`), the size labels `S`–`XL`, and the Δ, Π, M, and R fields are not
computed, printed, or asked.

## Selection

Run after context resolution, before any question and any document creation:

1. Read the claim ledger, unknowns, hazards, authority, and conflicts from the
   context record.
2. IF a claim's owner carries a staleness flag, THEN resolve it through the
   actualize instrument in callable mode (`skills/_shared/tracks/actualize.md`,
   entry `actualize.scope`, pre-filled scope), or mark each dependent claim
   `[assumption]` and continue.
3. IF accepted canon contradicts a claim, THEN report the authority conflict
   before any verdict or write, per `skills/_shared/verdict-contract.md`. An
   extension that contradicts no accepted clause is an `amend` claim on its
   owner, not a conflict.
4. Run the document-need test on each claim with an action other than `none`:
   name the future reader task, the missing content kind, the owning type or
   existing owner, the evidence, and why no existing document holds it. A
   need without a named reader, consumer, or observable use in the request,
   code, or graph fails the test. The result can be zero documents.
5. Merge claims that share one owner and one verification.
6. Map each passing need to an owner per the owner table, then to its
   instrument per the instrument registry.
7. Map each unknown to its next action per the unknown table. A `task-type` or
   `cpat` precedent resolves only the technical unknowns its recorded behavior
   and relevant constraints cover; cite that match. It does not settle a new
   user-owned `choice` without target-specific evidence from the request or
   accepted canon.
8. Map each hazard to its required check; engage a document only when that
   check needs a durable owner.
9. Report the selection line, then execute the instruments in conductor order.

## Owner table

| Observed need | Owner |
|---|---|
| Unsettled concept with a distinct value question | `idea` or a bounded `rnd` |
| Product outcome, beneficiary, or measurable goal beyond one contract | `prd` |
| Depended-on behavior, interface, invariant, or failure response | `spec` — amend the covering `spec` when one exists |
| User path before a covering contract | `journey`; a confirmed example after the contract is a `scenario` |
| Settled choice with alternatives and reasons named in the request or evidence | `adr` |
| Open choice the team still debates | `rfc`, or a bounded `rnd` when evidence is missing |
| Two or more dependent tasks, a coordination need, or a handoff | `plan` |
| A market, business, or user source question | `mrd`, `brd`, or `urd` for that source question only |
| A formal traceability obligation named in the request or accepted canon | only the `brs`, `strs`, `syrs`, or `srs` levels that obligation names |
| A repeatable human operation the work introduces | `guide` |

Selection rules:

1. A `plan` needs no `spec` or `prd`: a non-capability migration with a fixed
   task order receives a `plan` alone.
2. A `prd` is created only for an outcome beyond one contract; a need that fits
   one capability's purpose records in that capability's `spec`.
3. The conductor MUST NOT create an `idea` beside a `prd` in one invocation.
4. A security hazard engages its required check. It engages requirement
   documents only under a named traceability obligation.
5. WHEN the request names alternatives with reasons for a settled choice, the
   conductor MUST create an `adr` through the decision instrument.

## Unknown table

| Unknown | Next action |
|---|---|
| `fact` answerable from the repository, canon, or git | read it; cite the artifact; no question |
| `fact` about the outside world | research instrument |
| `choice` the user owns | interview within the ceiling of `skills/_shared/elicitation-contract.md` |
| `choice` with competing options and missing evidence | decision instrument, or a bounded `rnd` |
| `feasibility` | spike |
| `acceptance` | interview; record the answer under `## Clarifications` |

WHEN two or more unknowns need research, a spike, or a decision, compose one
instrument per kind, ordered cheapest first: conversation, then research, then
spike, then a formal document.

## Instrument registry

| Instrument | Produces | Entry |
|---|---|---|
| concept | `idea` | `skills/_shared/tracks/sdd.md`, gate `sdd.frame` |
| intent | `prd`; `journey` under the illustrate condition | `skills/_shared/tracks/sdd.md`, gate `sdd.require` |
| contract | `spec` | `skills/_shared/tracks/sdd.md`, gate `sdd.design` — once per capability |
| illustrate | `scenario` | `skills/_shared/tracks/sdd.md`, gate `sdd.illustrate` — once per capability, after that capability's `sdd.design` |
| decompose | `plan` | `skills/_shared/tracks/sdd.md`, gate `sdd.decompose` |
| runbook | `guide` | `skills/_shared/tracks/sdd.md`, gate `sdd.runbook` |
| decision | `adr`, `rfc` | `skills/_shared/tracks/decision.md`, gate `decision.classify` |
| research | `research`, `rnd`; optional `evidence` | `skills/_shared/tracks/research.md`, gate `research.frame` |
| spike | timeboxed `rnd` | `skills/_shared/tracks/research.md`, gate `research.spike` |
| describe | `spec`, `doc`, `guide`, `task-type` | `skills/_shared/tracks/describe.md`, gate `describe.read` |
| acquisition | `mrd`, `brd`, `urd` | `skills/_shared/tracks/requirements-cascade.md`, gate `requirements-cascade.mrd` |
| iso links | `brs`, `strs`, `syrs`, `srs` | `skills/_shared/tracks/requirements-cascade.md`, gate `requirements-cascade.brs` |

The research instrument fixes its product by the closing test: a named pending
decision or candidate set to choose between closes on a recommendation (`rnd`);
any other investigation closes on scope coverage (`research`). A request that
leads with the slug `research` asks for the type `research`. Its gather gate may
also produce evidence; one external material supplied to `/archcore:document`
enters gather directly. This is an exception to single-type production. Apply
`skills/_shared/research-compatibility.md` before using new vocabulary.

The decision instrument's `decision.cascade` gate additionally creates its
cascade documents (`rule`, `guide`, `spec`, `plan`, `cpat`) inside the
instrument per its own gate record — a recorded exception to single-type
production, not a `Next:` chain. The intent instrument's `journey` beside the
`prd` under the illustrate condition is a second recorded exception of the same
kind.

**Illustrate condition.** A capability meets it when its claim names a
user-facing surface — a UI, a conversational skill, an operator-facing flow — or
when grounding finds `features/*.feature` or a BDD runner in the test-runner slot
of `skills/_shared/grounding/detect-stack.md`. The conductor reads the claim and
grounding only; it never asks the user whether to illustrate. IF grounding cannot
decide the condition, THEN record it as a `choice` unknown. The condition binds
only when `skills/_shared/actor-subject-compatibility.md` returned `yes`;
otherwise the conductor drops the instrument and reports the required version once.

Sequencing rules:

1. The conductor names each next instrument; a gate's `Next: exit` returns
   control to the conductor.
2. Invoke the concept instrument only for an unsettled concept, never as a
   default first step.
3. Invoke the acquisition instrument only for a market, business, or user
   source question that the request or a gate names.
4. WHEN a spike resolves its question, re-run Selection with the revised claims.
5. WHEN decomposition surfaces a claim outside the ledger, add it, re-report
   the selection line, and continue.
6. WHEN a produced draft fails a blocking exit check, stop at that instrument
   and report per `skills/_shared/gate-contract.md`.
7. WHEN the user declines an offered instrument, record the decline under
   `## Clarifications` of the newest draft and continue the remaining sequence.
8. WHEN a settled decision surfaces inside any instrument, route it through
   the decision instrument before that instrument exits.
9. WHEN the selection produces a `plan`, record the claim ledger in that `plan`
   under a `## Declared Delta` section, one claim per line with its action.
10. WHEN the selection includes a `guide`, state the reader and the step actor
    in the draft.
11. IF an `amend` claim names a capability no `spec` covers, THEN engage the
    describe instrument in callable mode to create the covering `spec` first.
12. IF an instrument's upstream product is missing and its entry condition
    requires it, THEN invoke the producing instrument first.
13. WHEN a capability meets the illustrate condition, sequence `sdd.illustrate`
    directly after that capability's `sdd.design` and before `sdd.decompose`.
14. WHEN a `journey` on the topic exists and no `spec` covers the interaction,
    produce no `scenario`; the routing test between the pair is the covering
    `spec`, not the presence of any `spec`.
15. WHILE the selection has instruments left, keep the `archcore:track` state
    block, with `claims:` and the next instrument's gate, on the newest draft;
    move it at each gate close and remove it when the last instrument closes.
    A blocked gate keeps the block where the selection stopped.

## Selection line

Report one line before invoking any instrument, naming only what changes an
instrument, a check, or a write:

`selection: <instruments in order, or none> — owners: <type → existing or new owner>; checks: <hazard checks or none>; open: <unknowns sent to an instrument or the interview, or none>`

Never ask the user to choose an instrument. Never print a route name or a size
label. A zero-document selection names the next action instead: implement
directly, or the command that records the result later.

## State carrier

Track state stays in the `archcore:track` block per
`skills/_shared/gate-contract.md`, extended on this command with `claims:` after
`gate:`:

```markdown
<!-- archcore:track
track: sdd
gate: sdd.design
claims: create spec csv-export; amend spec export-api §4; none plan
taxonomy: Functional Scope & Behavior
asked: ...
budget: ...
deferred: ...
-->
```

Resume rules on this command:

1. WHEN a resumed block carries the legacy `route:` and `delta:` fields, read
   `delta:` as the claim ledger — `creates` as `create`, `modifies` as
   `amend`, `retires` as `retire`, `decision` as an `adr` need — and ignore
   `route:`; write `claims:` at the next gate close.
2. WHEN a resumed block lacks `claims:` and `delta:`, recompute the claims from
   the recorded gate, the draft, and `## Clarifications`.
3. WHEN the recomputed claims contradict the recorded ones, surface both and
   ask one confirmation question.
4. WHEN the question ceiling exhausts before `choice` unknowns resolve, record
   the remainder under `deferred` per `skills/_shared/elicitation-contract.md`.
