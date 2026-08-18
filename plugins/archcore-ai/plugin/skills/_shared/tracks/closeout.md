# Closeout Track — Verify the Plan, Merge the Canon, Accept the Statuses

Plugin runtime asset. Loaded by the `review` skill — this track's primary
executor — when `/archcore:review` routes closeout-shaped wording ("close out
the feature", "ship the feature", a finished branch to close) here. Gate
record shape, state rules, and execution rules:
`skills/_shared/gate-contract.md`. Interview mechanics and question budget:
`skills/_shared/elicitation-contract.md`. Branch scope:
`skills/_shared/branch-state.md`.

## Track notes

- Gate order: `closeout.verify` → `closeout.merge` → `closeout.accept` →
  `closeout.capture` → `closeout.discharge`.
- Capture and disposal are separate gates on purpose: a declined capture
  leaves a fulfilled plan removable, and a removable plan never forces a
  capture. `closeout.capture` owns no document type of its own — every
  document it creates comes from the instrument it routes to, under that
  instrument's own Produces rules.
- Boundary against the actualize track
  (`skills/_shared/tracks/actualize.md`): actualize detects drift at any
  time; closeout is the completion step for one finished piece of work —
  verify the plan was fulfilled, merge the result into the documents, then
  transition statuses. Drift-shaped wording without a completion signal
  routes to actualize.
- Scope: the `plan` document covering the branch work (matched by topic or
  path references), its `implements` chain one hop (`prd`, `idea`, `rnd`,
  `spec`), plus every document the branch diff references. The `review`
  skill pre-fills the branch boundary per `skills/_shared/branch-state.md`.
- Status rule: this track transitions draft → accepted only, one
  per-document confirmation each; a decline leaves the status unchanged.
  Rejection is not this track's verdict — an `rfc` resolves through
  `decision.resolve` (`skills/_shared/tracks/decision.md`), any other
  rejection stays a direct user edit. A completed `plan` takes no terminal
  status: `closeout.discharge` removes the document instead, because no
  status value in the kernel means "completed and absorbed".
- The executing skill MUST NOT edit a code file on this track.
- Each `budget` knob is the per-gate maximum, reached only in expert
  invocation; in auto mode every question draws from the shared
  per-invocation ceiling in `skills/_shared/elicitation-contract.md`.
  Per-document confirmations follow the `actualize.fix` model —
  confirmations, not budget questions [assumption]. WHEN both a merge update
  and a status transition apply to one document, the executing skill SHOULD
  combine them into one confirmation exchange ("update and accept?"), so a
  document costs at most one exchange per run.

## Track state

[assumption] This track produces no draft artifact, so no `archcore:track`
state block persists between invocations. An interrupted run restarts at
`closeout.verify`; the executing skill MUST NOT re-ask a question or
confirmation already answered earlier in the same invocation. Accepted
answers and confirmations persist only in the running report; the
draft-artifact write-back in `skills/_shared/elicitation-contract.md` does
not apply on this track.

### gate: closeout.verify

- Purpose: Establish that the branch work fulfills the plan — judge every
  plan task and acceptance criterion against the branch diff. WHEN the
  scoped plan carries a `## Declared Delta` section, judge each declared Δ
  entry against the branch diff too. A document-versus-code direction takes
  its label vocabulary from `skills/_shared/verdict-contract.md`.
- Entry conditions:
  - skip_when: the branch scope matches no `plan` document — the merge and
    accept gates run over the diff-matched documents alone.
  - The branch work boundary resolves per `skills/_shared/branch-state.md`.
- Elicitation knobs:
  - trigger: a plan task or acceptance criterion cannot be judged fulfilled
    or unfulfilled from the diff and the codebase.
  - taxonomy: Completion Signals, Functional Scope & Behavior from
    `skills/_shared/coverage-taxonomy.md`.
  - budget: 2
- Produces: none — the per-task verdicts land in the running report.
- Exit checks:
  - blocking: every plan task and acceptance criterion in scope carries one
    verdict — fulfilled, unfulfilled, or not judgeable from the diff; a
    not-judgeable verdict cites the specific check attempted.
  - blocking: every unfulfilled verdict cites its evidence — the missing
    change, the failing check, or the absent file.
  - blocking: WHEN the scoped plan carries a `## Declared Delta` section,
    every declared Δ entry carries one verdict — confirmed by the diff, or
    missing with its evidence; undeclared change found at this gate is
    appended to the report as unplanned Δ.
  - advisory: the report ends with a one-line count summary per verdict.
- Next: `closeout.merge`.

### gate: closeout.merge

- Purpose: Bring the scoped documents up to the implemented reality — merge
  the branch result into the documents that describe it.
- Entry conditions:
  - skip_when: no scoped document's claims diverge from the branch result.
  - The scope — the branch-state boundary plus matched documents — is
    recorded in the running report.
- Elicitation knobs:
  - trigger: a document update awaits its per-document confirmation.
  - taxonomy: Terminology & Consistency, Misc / Placeholders from
    `skills/_shared/coverage-taxonomy.md`. [assumption]
  - budget: 1 question per document awaiting an update [assumption] —
    mirrors the `actualize.fix` per-document confirmation rule.
- Produces: none — the gate updates existing documents via
  `update_document`; it creates no document.
- Exit checks:
  - blocking: every `update_document` call was preceded by the user's
    confirmation of that document's update.
  - blocking: the executing skill modified no code file.
  - advisory: declined updates appear in the final report with their
    divergence evidence.
- Next: `closeout.accept`.

### gate: closeout.accept

- Purpose: Transition the confirmed documents of the completed work from
  draft to accepted.
- Entry conditions:
  - skip_when: no scoped document carries `status: draft`.
  - `closeout.verify` recorded its verdicts, or was skipped with the
    diff-matched scope recorded.
- Elicitation knobs:
  - trigger: a draft document awaits its status confirmation.
  - taxonomy: Completion Signals from `skills/_shared/coverage-taxonomy.md`.
  - budget: 1 question per draft document in scope [assumption] — the offer
    names the document and its verify verdict.
- Produces: none — the gate updates the status field via `update_document`;
  it creates no document.
- Exit checks:
  - blocking: every status transition was confirmed for that specific
    document; a decline leaves the status unchanged.
  - blocking: no status transition targets a document whose recorded verify
    verdict is unfulfilled.
  - blocking: the executing skill modified no code file.
  - advisory: the final report groups documents by transition applied,
    declined, and skipped.
  - advisory: the final report lists each discharge candidate per the
    Discharge report section in this file, or states that no candidate
    exists.
- Next: `closeout.capture`.

### gate: closeout.capture

- Purpose: Route the completed plan's residue to the instrument that owns
  its type, before the plan leaves the corpus.
- Entry conditions:
  - skip_when: the branch scope matches no `plan` document, or the plan
    tasks, the verify report, and the merge report name no residue beyond
    the delivered work itself.
  - `closeout.accept` completed its transitions, or was skipped.
- Elicitation knobs:
  - trigger: a named residue awaits the user's capture offer.
  - taxonomy: Completion Signals, Constraints & Tradeoffs from
    `skills/_shared/coverage-taxonomy.md`.
  - budget: 1 question per named residue [assumption] — mirrors the
    `closeout.merge` and `closeout.accept` per-document confirmation rule.
- Produces:
  - type: `task-type` or `guide` per the actor boundary rule in
    `skills/_shared/tracks/experience.md`; for a settled standard or choice,
    whatever `skills/_shared/tracks/decision.md` (entry `decision.classify`)
    produces, restricted to its standard cascade
  - status: draft
  - relations: per the Produces field of the instrument that ran.
- Exit checks:
  - blocking: every named residue is recorded as routed or declined; a
    decline names its reason and blocks nothing downstream.
  - blocking: every captured residue was named by the plan, the verify
    report, or the merge report; this gate searches for none of its own.
  - blocking: no `spec` and no `plan` was created at this gate — the
    decision instrument's architecture cascade is out of scope here.
  - blocking: the executing skill modified no code file.
  - advisory: a code-pattern residue is left to
    `skills/_shared/tracks/experience.md`, which runs after this track exits.
- Next: `closeout.discharge`.

### gate: closeout.discharge

- Purpose: Remove the completed `plan` from the corpus.
- Entry conditions:
  - skip_when: the branch scope matches no `plan` document; or a plan task or
    acceptance criterion carries a verdict other than fulfilled; or the plan
    file appears in the `uncommitted-changes` block of
    `skills/_shared/branch-state.md`. The gate names the unmet condition in
    the report and exits.
  - `closeout.verify` recorded a verdict for every plan task and acceptance
    criterion in scope.
  - `closeout.capture` recorded an outcome for every named residue, or was
    skipped.
- Elicitation knobs:
  - trigger: a plan awaits its removal confirmation.
  - taxonomy: Completion Signals from `skills/_shared/coverage-taxonomy.md`.
  - budget: 1
- Produces: none — the gate removes a document via `remove_document`; it
  creates none.
- Exit checks:
  - blocking: every `remove_document` call was preceded by the user's
    confirmation naming that specific plan.
  - blocking: `remove_document` targeted only `plan` documents at this gate.
  - blocking: the executing skill modified no code file.
  - advisory: the report names each removed plan, the residue captured at
    `closeout.capture` or its absence, and the commit that still carries the
    removed file.
- Next: exit — the `review` skill runs the repeated-pattern offer per
  `skills/_shared/tracks/experience.md`.

## Discharge report

Report only, `plan` excepted. WHEN `closeout.accept` completes its status
transitions, the executing skill MUST list the discharge candidates in the
final report — the scoped documents whose unique information is absorbed
elsewhere — per these type defaults:

- `spec` and `adr` stay canon; neither is ever a discharge candidate.
- A completed `plan` is never a report candidate: `closeout.capture` routes
  its residue to the owning instrument and `closeout.discharge` removes the
  document, both in the same invocation.
- A `prd` holds until its success metrics verify.
- An `idea` becomes a candidate after `closeout.accept` transitions every
  document that implements it.
- A spike `rnd` keeps only its Findings section.

Only `plan` leaves the corpus on this track, because a completed plan's
statements belong to the `spec` it implements, to the branch commits, and to
whatever `closeout.capture` routed out — nothing unique survives the work.
Every other type keeps its residual value. The `archived` status value does not exist in the kernel;
WHILE that value is absent, the executing skill MUST NOT apply a discharge
transition to a `prd`, an `idea`, or an `rnd`, and the report leaves each such
candidate's status unchanged for the user's later action.
