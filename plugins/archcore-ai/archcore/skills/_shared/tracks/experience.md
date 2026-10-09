# Experience Track — Repeated-Pattern Detection and Capture Offer

Plugin runtime asset. Loaded by the `review` skill (`/archcore:review`) when
routing resolves to the `experience` track. Gate records and track state follow
`skills/_shared/gate-contract.md`; interview mechanics follow
`skills/_shared/elicitation-contract.md`.

## Track behavior

- Stages: `experience.detect` → `experience.offer` → exit.
- The whole track is an offer. WHEN reviewed changes repeat an undocumented
  pattern, or change one practice whose lesson transfers beyond this edit, the
  review skill SHOULD offer a `cpat`, `task-type`, or `guide` capture.
- On a branch review, the durable-context selection
  (`skills/_shared/durable-context-selection.md`) runs first. Its preview is
  the capture offer for every pattern it lists, and its omissions stand; this
  track handles only the patterns the selection did not consider.
- The review skill MUST NOT create a document on this track without the user's
  acceptance at `experience.offer`.
- Produced types: `cpat` records a Before/After code-pattern change;
  `task-type` records a typical task pattern; `guide` records a repeatable
  procedure whose step actor is a human.
- Boundary rule — the actor decides the type: a human actor routes to
  `guide`; an agent actor routes to `task-type`.
- Each `budget` knob is the per-gate maximum, reached only in expert
  invocation; in auto mode every question draws from the shared per-invocation
  ceiling in `skills/_shared/elicitation-contract.md`.

## Track state

[assumption] This track creates no draft artifact before acceptance at
`experience.offer` and exits at that gate, so no `archcore:track` state block
persists between invocations. An interrupted run restarts at
`experience.detect`; the review skill MUST NOT re-ask the offer already
answered in the same invocation. WHEN the answer is decline, the review skill
records nothing — the no-write rule of this track overrides the clarification
write-back in `skills/_shared/elicitation-contract.md`.

### gate: experience.detect

- Purpose: Establish that the reviewed changes carry a pattern that no
  `.archcore/` document records.
- Entry conditions:
  - skip_when: the reviewed changes carry no detection signal, a `cpat` or
    `task-type` document already records the pattern, or the durable-context
    selection of this invocation already listed or omitted it — search
    `.archcore/` first, per the Ground first rule in
    `skills/_shared/elicitation-contract.md`.
  - One detection signal is present: the same edit shape appears in two or
    more files or documents of the reviewed diff, with evidence of its reason
    for a `cpat`; or one deliberate change of practice carries evidence of its
    reason and a scope beyond this edit.
  - [assumption] Or: the changes match a pattern previously applied in the
    base (git history) — this file's reading of a recorded-pattern match.
- Elicitation knobs:
  - trigger: none — this gate asks zero questions.
  - taxonomy: none.
  - budget: 0
- Produces: none — `experience.offer` produces the document.
- Exit checks:
  - blocking: the review output names the pattern and its evidence — the
    diff paths that carry it, the matched base pattern, or the recorded reason
    and scope of the changed practice.
- Next: `experience.offer`.

### gate: experience.offer

- Purpose: Offer to record the detected pattern; write it only on acceptance.
- Entry conditions:
  - skip_when: the invocation's question budget is exhausted per
    `skills/_shared/elicitation-contract.md` — exit without writing.
  - `experience.detect` passed its blocking exit check.
- Elicitation knobs:
  - trigger: entry into this gate — the offer is this gate's one question.
    The pattern kind preselects the offered type: a code-pattern change →
    `cpat`; a procedure with an agent actor → `task-type`; a procedure with
    a human actor → `guide`. The question asks accept or decline for the
    preselected type.
  - taxonomy: none.
  - budget: 1
- Produces:
  - type: `cpat`, `task-type`, or `guide`, per the accepted answer
  - status: draft
  - relations: none
- Exit checks:
  - blocking: the recorded answer names accept with `cpat`, accept with
    `task-type`, accept with `guide`, or decline.
  - blocking: WHEN the answer is accept, the document exists with
    `status: draft`.
  - advisory: WHEN the answer is accept, a `cpat` draft body covers What
    Changed, Why, Before, After, Scope; a `task-type` draft body covers
    Context, Steps, Checklist, Pitfalls; a `guide` draft body carries every
    section `skills/_shared/guide-contract.md` requires.
- Next: exit. WHEN the answer is decline, exit without writing.
