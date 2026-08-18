# Delta Routing — Conductor Contract for Route Computation

Plugin runtime asset. Loaded by the `plan` skill (`/archcore:plan`) at its Route
step. Gate execution, state block, and resume rules:
`skills/_shared/gate-contract.md`. Interview mechanics and ceilings:
`skills/_shared/elicitation-contract.md`. Capability sizing:
`skills/_shared/capability-granularity.md`. The conductor computes the route and
owns every cross-instrument sequence; instruments produce the documents.

## Vocabulary

One term per concept. Do not introduce synonyms.

- **canon** — the accepted document graph in `.archcore/`.
- **capability** — one behavior an external consumer relies on, recordable as
  one `spec`; sizing rules in `skills/_shared/capability-granularity.md`.
- **zone** — the canon documents and code areas the request touches.
- **Δ (canon delta)** — five fields derived at Route: `creates`, `modifies`,
  `retires` (capability lists), `decision` (settled-choice delta),
  `intent_gap` (`yes` when the work adds product intent no canon document
  records).
- **Π (gap profile)** — one source per information need: `machine`, `user`,
  `world`, `undecided`, `empirical`.
- **M (maturity)** — one value per zone: `stone` when an accepted document
  covers the zone or a dependent consumes it; `pencil` otherwise.
- **R (risk flags)** — `external-contract`, `data-migration`,
  `security-compliance`, `irreversibility`, `multi-team`.
- **operational procedure** — a human-performed sequence the delta introduces:
  install, migrate, operate, or verify steps.
- **route** — the computed package composition: `null`, `decision`,
  `amendment`, `capability`, `umbrella`.
- **size label** — `S`, `M`, `L`, `XL`; derived from the route table, never
  asked.
- **expert invocation** — the user names a path; computation is bypassed.

## Derivation

Run after grounding, before any question and any document creation:

1. Derive Δ: compare the request's intended end state against the canon and
   the code. List each capability the work creates, modifies, or retires;
   record a settled choice as `decision`; set `intent_gap: yes` when the work
   adds product intent no canon document records.
2. IF a zone document carries a staleness flag, THEN resolve it through the
   actualize instrument in callable mode (`skills/_shared/tracks/actualize.md`,
   entry `actualize.scope`, pre-filled zone scope), or mark each dependent Δ
   entry `[assumption]` and continue.
3. IF grounding cannot settle a Δ field, THEN record it as a `user`-source Π
   need. Do not guess.
4. Derive Π: list the information needs the package's documents require and
   assign each need one source. A `machine` claim cites its artifact — a file
   path, a document, a commit. A matching `task-type` or `cpat` precedent
   de-escalates the needs it covers from `user` to `machine`.
5. Derive M per touched zone and R from the request and the grounding
   evidence. WHEN any touched zone is `stone`, the escalators read M as
   `stone`. Record an R flag per capability when the flag names one
   capability; record it initiative-wide otherwise.
6. Announce the route (format below), then execute the package.

## Route table

Each non-empty Δ field contributes package members; the package is the union
of the matching contributions.

| Δ field | Contribution to the package |
|---|---|
| every capability list empty ∧ `decision: none` ∧ `intent_gap: no` | nothing — no documents beyond the instrument outputs Π engages |
| `decision` non-empty | decision instrument (`adr` / `rfc`) |
| `modifies` non-empty | per modified capability: one code-wrong/spec-wrong verdict against the covering `spec`, per `skills/_shared/verdict-contract.md` |
| `retires` non-empty | per retired capability: a retirement entry reported for closeout discharge |
| `intent_gap: yes` | one `prd` through the intent instrument WHEN the gap names goals or metrics beyond one capability's purpose; a gap that fits one capability's purpose records in that capability's `spec` instead; a product-scale gap engages the acquisition instrument (sequencing rule 3) |
| `creates` = 1 capability | one `spec` + one `plan` |
| `creates` ≥ 2 capabilities | one umbrella `prd` + one `spec` per capability + one `plan` |
| implementation spanning two or more tasks, on a `decision` or `amendment` route | one `plan` through the decompose instrument |

Route name and base size label come from the highest matching line:

| Highest match | Route | Base label |
|---|---|---|
| `creates` ≥ 2 | `umbrella` | L |
| `creates` = 1 | `capability` | M |
| `modifies` or `retires` | `amendment` | S |
| `decision` | `decision` | S |
| `intent_gap` only | `null` — intent recorded, no build package | S |
| nothing | `null` | S |

Escalators, applied after the row match:

- WHEN M is `stone` or R is non-empty, raise the size label one step and name
  the raising flag in the announcement. WHEN iso links engage, raise one
  additional step. Cap the label at `XL`.
- WHEN R carries `security-compliance`, escalate each flagged capability into
  iso links (`requirements-cascade.brs` → `srs`). Do not escalate an
  unflagged capability.
- WHEN a capability's delta introduces an operational procedure, add one
  `guide` to the package through the runbook instrument.
- WHEN R carries `data-migration`, add a migration runbook `guide` to the
  package; drop it only on the user's decline.
- Report `retires` entries for closeout discharge; the conductor performs no
  status transition.

## Π engagement

| Source | Action |
|---|---|
| `machine` | compose without a question; cite the artifact |
| `user` | interview within the ceiling of `skills/_shared/elicitation-contract.md` |
| `world` | research instrument |
| `undecided` | decision instrument |
| `empirical` | spike |

WHEN two or more needs name `world`, `undecided`, or `empirical` sources,
compose one instrument per uncertainty kind — a portfolio, not a funnel —
ordered cheapest kill shot first: conversation, then research, then spike,
then formal document.

## Instrument registry

| Instrument | Produces | Entry |
|---|---|---|
| concept | `idea` | `skills/_shared/tracks/sdd.md`, gate `sdd.frame` |
| intent | `prd` | `skills/_shared/tracks/sdd.md`, gate `sdd.require` |
| contract | `spec` | `skills/_shared/tracks/sdd.md`, gate `sdd.design` — once per capability |
| decompose | `plan` | `skills/_shared/tracks/sdd.md`, gate `sdd.decompose` |
| runbook | `guide` | `skills/_shared/tracks/sdd.md`, gate `sdd.runbook` |
| decision | `adr`, `rfc` | `skills/_shared/tracks/decision.md`, gate `decision.classify` |
| research | `rnd` | `skills/_shared/tracks/research.md`, gate `research.frame` |
| spike | timeboxed `rnd` | `skills/_shared/tracks/research.md`, gate `research.spike` |
| describe | `spec`, `doc`, `guide` | `skills/_shared/tracks/describe.md`, gate `describe.read` |
| acquisition | `mrd`, `brd`, `urd` | `skills/_shared/tracks/requirements-cascade.md`, gate `requirements-cascade.mrd` |
| iso links | `brs`, `strs`, `syrs`, `srs` | `skills/_shared/tracks/requirements-cascade.md`, gate `requirements-cascade.brs` |

The decision instrument's `decision.cascade` gate additionally creates its
cascade documents (`rule`, `guide`, `spec`, `plan`, `cpat`) inside the
instrument per its own gate record — a recorded exception to single-type
production, not a `Next:` chain.

Sequencing rules:

1. The conductor names each next instrument; a gate's `Next: exit` returns
   control to the conductor.
2. Invoke the concept instrument only from the high-uncertainty portfolio,
   never as a default first step.
3. Invoke the acquisition instrument only on a product-scale `intent_gap` or
   an expert invocation.
4. WHEN a spike resolves its question, re-enter Derivation with the revised Δ.
5. WHEN decomposition surfaces a capability outside the declared Δ, revise Δ,
   re-announce, and continue.
6. WHEN a produced draft fails a blocking exit check, stop the route at that
   instrument and report per `skills/_shared/gate-contract.md`.
7. WHEN the user declines an offered instrument, record the decline in the
   route rationale and continue the remaining sequence.
8. WHEN a settled decision surfaces inside any instrument, route it through
   the decision instrument before that instrument exits.
9. WHEN the package produces a `plan`, record the declared Δ and the route
   rationale in that `plan` under a `## Declared Delta` section.
10. WHEN the package includes a `guide`, state the reader and the step actor
    in the draft.
11. IF `modifies` names a capability no `spec` covers, THEN engage the
    describe instrument in callable mode to create the covering `spec` first.
12. IF an instrument's upstream product is missing, THEN invoke the producing
    instrument first.

## Route announcement

Report one line before invoking any instrument:

`route: <route> (size <label>) — Δ: <non-empty fields>; Π: <sources engaged>; M: <pencil or stone>; R: <flags or none>; raised by: <flag or none>; instruments: <ordered list or none>`

Never ask the user to choose a route or a size label. An expert invocation
replaces the announcement with the named path.

## Expert invocation map

| Named | Path |
|---|---|
| `sdd` | full package: intent → contract (per capability) → decompose, at per-gate maxima |
| `sources` | acquisition instrument, entry `requirements-cascade.mrd` |
| `iso` | iso links, entry `requirements-cascade.brs` |
| `research` | research instrument, entry `research.frame` |
| a route name — `null`, `decision`, `amendment`, `capability`, `umbrella` | that route — Derivation still runs to fill Δ; the name fixes the route and the label only |
| a document type the registry lists | the producing instrument's entry gate |

## State carrier

Track state stays in the `archcore:track` block per
`skills/_shared/gate-contract.md`, extended on this command with `route:` and
`delta:` after `gate:`:

```markdown
<!-- archcore:track
track: sdd
gate: sdd.design
route: capability (size M)
delta: creates=[csv-export]; modifies=[]; retires=[]; decision=none; intent_gap=no
taxonomy: Functional Scope & Behavior
asked: ...
budget: ...
deferred: ...
-->
```

Resume rules on this command:

1. WHEN a resumed block lacks `route:`, recompute the route from the recorded
   gate and clarifications.
2. WHEN the computed route contradicts the recorded route, surface both and
   ask one confirmation question.
3. WHEN the question ceiling exhausts before `user` needs resolve, record the
   remainder under `deferred` per `skills/_shared/elicitation-contract.md`.
