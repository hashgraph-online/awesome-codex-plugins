# Research Track — Frame Questions, Gather Evidence, Conclude

Plugin runtime asset. Loaded by the `plan` skill (primary executor) when routing
resolves to the `research` track. Gate execution, state block, and resume rules:
`skills/_shared/gate-contract.md`. Interview mechanics and question ceilings:
`skills/_shared/elicitation-contract.md`. Coverage categories:
`skills/_shared/coverage-taxonomy.md`.

## Track notes

- Gate order: `research.frame` → `research.gather` → `research.conclude`.
- Each `budget` knob states this track's per-gate maximum, reached only in
  expert invocation. Auto mode draws every question from the shared
  per-invocation ceiling in `skills/_shared/elicitation-contract.md`.
- Track boundary: the requirements chain decides, not the subject. Market or
  business discovery that opens a requirements cascade — an `mrd` the `brd`
  and `urd` will build on — belongs to the `requirements-cascade` track's
  sources mode (`skills/_shared/tracks/requirements-cascade.md`). Standalone
  research gathered as evidence, technical or market, with no requirements
  chain intended, produces an `rnd` here; the `plan` skill routes between
  the two.
- The produced `rnd` is one document filled across the gates: `research.frame`
  creates it with Goal and Questions; the later gates complete Approach,
  Findings, Recommendation, and Next Action via the gate-close
  `update_document` call required by `skills/_shared/gate-contract.md`.
- Before the first gate, the `plan` skill calls `list_documents` for the types
  `rnd`, `idea`, and `prd` and checks the topic for duplicates.
- WHEN a check-existing search returns a global document (`source_kind:
  "global"`), the executing skill loads `skills/_shared/globals.md`.
  WHEN no result is global, the gates proceed unchanged.
- A read-only subagent (`archcore-auditor`) MAY collect codebase and
  `.archcore/` evidence at `research.gather`; the main thread gathers web
  evidence directly with whatever web-fetch capability the host provides,
  composes the draft, and conducts any interview, per
  `skills/_shared/elicitation-contract.md`.
- Content voice for the produced document: `skills/_shared/precision-rules.md`
  Rules 1, 3, and 4 — web-sourced claims cite their source and access date;
  claims no source or measurement grounds carry `[assumption]`.

### gate: research.frame

- Purpose: Fix the research goal and the questions the research must answer.
- Entry conditions:
  - skip_when: an `rnd` covering the topic exists in `.archcore/` and the
    request does not ask to redo, refresh, or extend the research.
  - The request names the subject under investigation.
- Elicitation knobs:
  - trigger: the request does not name the questions to answer or the decision
    the research informs.
  - taxonomy: Functional Scope & Behavior, Constraints & Tradeoffs from
    `skills/_shared/coverage-taxonomy.md`.
  - budget: 2
- Produces:
  - type: rnd
  - status: draft
  - relations: `related` → the existing `idea` or `prd` the research informs,
    when one exists.
- Exit checks:
  - blocking: the rnd draft contains the sections Goal and Questions, and the
    Questions section enumerates numbered questions.
  - advisory: the Questions section holds at most 5 questions.
- Next: `research.gather`.

### gate: research.gather

- Purpose: Collect the evidence — sources, measurements, corpus and codebase
  facts — that answers the recorded questions.
- Entry conditions:
  - skip_when: the request or the draft already carries evidence answering
    every recorded question — sources and facts supplied by the user.
  - An rnd draft from `research.frame` exists with Goal and Questions.
- Elicitation knobs:
  - trigger: none — this gate grounds from external sources, the codebase, git
    history, and `.archcore/` search; evidence-gap questions belong to
    `research.conclude`.
  - taxonomy: none.
  - budget: 0
- Produces: none — gathered evidence lands in the draft's Approach and
  Findings sections at the gate close.
- Exit checks:
  - blocking: the draft's Approach section names the method and the sources
    consulted, with access dates for web sources.
  - blocking: the draft's Findings section records at least one evidenced
    finding per recorded question, or names the specific sources consulted
    that failed to answer it and marks the question unanswered.
  - advisory: no finding introduces an ungrounded claim without an
    `[assumption]` marker, per `skills/_shared/precision-rules.md`.
- Next: `research.conclude`.

### gate: research.conclude

- Purpose: Resolve the open questions, state the recommendation, and name the
  next action.
- Entry conditions:
  - skip_when: the draft already carries Recommendation and Next Action
    sections covering every recorded question.
  - `research.gather` passed its blocking exit checks.
- Elicitation knobs:
  - trigger: a recorded question remains unanswered by the evidence, or the
    findings support two or more viable recommendations.
  - taxonomy: Constraints & Tradeoffs, Completion Signals from
    `skills/_shared/coverage-taxonomy.md`.
  - budget: 2
- Produces: none — the gate completes the draft created at `research.frame`.
- Exit checks:
  - blocking: the draft carries the sections Goal, Questions, Approach,
    Findings, Recommendation, and Next Action.
  - blocking: the Recommendation section states one recommendation and names
    the findings that support it.
  - blocking: the Next Action section names the follow-up route —
    `/archcore:plan` to continue into the `sdd` track, `/archcore:document` to
    record the decision — or states that no follow-up is needed.
  - advisory: the closing report lists candidate `add_relation` targets among
    existing `idea`, `prd`, `adr`, and `rfc` documents, or states that none
    match.
- Next: exit.
