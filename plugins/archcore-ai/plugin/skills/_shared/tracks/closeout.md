# Closeout Track — Verify the Plan, Merge the Canon, Accept the Statuses

Plugin runtime asset. Loaded by the `review` skill — this track's primary
executor — when `/archcore:review` routes closeout-shaped wording ("close out
the feature", "ship the feature", a finished branch to close) here. Gate
record shape, state rules, and execution rules:
`skills/_shared/gate-contract.md`. Interview mechanics and question budget:
`skills/_shared/elicitation-contract.md`. Branch scope:
`skills/_shared/branch-state.md`.

## Track notes

- Gate order: `closeout.verify` → `closeout.merge` → `closeout.accept`.
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
  rejection stays a direct user edit.
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
  plan task and acceptance criterion against the branch diff.
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
- Next: exit — the `review` skill runs the repeated-pattern offer per
  `skills/_shared/tracks/experience.md`.
