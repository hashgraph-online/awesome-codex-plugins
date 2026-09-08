# Research Track — Frame, Gather, Conclude

Plugin runtime asset. Executed by `plan` and `document`. Gate execution and
resume rules: `skills/_shared/gate-contract.md`. Interview mechanics:
`skills/_shared/elicitation-contract.md`. Content voice:
`skills/_shared/precision-rules.md`. Engine vocabulary gate:
`skills/_shared/research-compatibility.md`.

## Terms

- Research instrument: this track — the gates `research.frame`,
  `research.gather`, `research.conclude`, and `research.spike`.
- `research` document: the vision document type that records coverage of a
  declared scope. The word `research` in backticks always names this type.
- Investigation: the `research` or `rnd` document the instrument fills.
- Artifact type: the `artifact_type` value recorded in the track state block —
  `research`, `rnd`, or `evidence`.

## Track boundary

A recommendation closes an `rnd`; coverage of a declared scope closes a
`research`. Both belong to vision. An `evidence` records one external material
and belongs to knowledge. Market discovery that feeds an `mrd` → `brd` → `urd`
requirements chain belongs to `skills/_shared/tracks/requirements-cascade.md`.
A proposed technical choice belongs to the decision instrument.

Gate order: `research.frame` → `research.gather` → `research.conclude`.
An explicit `evidence` (`/archcore:document evidence`) enters gather and exits
there. `/archcore:plan research` and `/archcore:document research` enter frame
and select the investigation type by the closing test below; neither command
exposes `rnd` as an entry. `research.spike` remains the conductor's separate
entry for an `empirical` Π source; its code is throwaway.
Spike code MUST NOT merge into the mainline.

Gates check recorded content, not the method the executor used. Scope
(`research`) or Approach (`rnd`) records the method used. Each gate budget is
an expert maximum; auto mode uses the shared ceiling.

## Entry and resumption

1. Apply `skills/_shared/research-compatibility.md` before naming new enums in any MCP call.
2. Check existing documents with `list_documents` and topic search before creating an artifact.
3. On a supported engine, include `research`, `evidence`, `rnd`, `idea`, and `prd` in the duplicate check.
4. On an older engine, use `rnd`, `idea`, and `prd` in the duplicate check.
5. If a result is global, load `skills/_shared/globals.md`.
6. If the request is an explicit `evidence` entry, fix the artifact type to `evidence`, subject to the compatibility fallback.
7. Otherwise, if the request names a pending decision or a set of candidates to choose between, select `rnd`; a supplied report that ends in a recommendation names a pending decision.
8. Otherwise, select `research`. The path name `research` selects this instrument, not the type.
9. Record the artifact type in the artifact's `artifact_type` state field per `skills/_shared/gate-contract.md`.
10. If an existing artifact has no `artifact_type`, derive the artifact type from its filename type.
11. Keep the existing artifact's type on resume; the closing test does not convert an existing `rnd` or `research`.
12. If a complete matching local artifact exists and the request does not ask to redo, refresh, or extend it, exit without writes.
13. If a matching local draft exists, resume it at its earliest unmet check.
14. If the request asks to redo, refresh, or extend a complete matching artifact, resume that artifact at `research.gather` and record the request under Clarifications.

Create each artifact with composed `content`; do not create an empty template
and fill it in a second call. A ready report supplies frame inputs without a
frame interview. An explicit material supplies the frame for standalone
`evidence`; record that fact under Clarifications in the evidence draft.
This entry needs no parent investigation. A global match is read-only
context, never a write target or relation endpoint.

## Evidence writes

A source is a row first: a `research` keeps sources in Sources; an `rnd` keeps
sources under Approach → Inputs. Promote a material to `evidence` only when two
documents rely on it, a contradiction involves it, or a newer material
supersedes it. An explicit `evidence` request is an exception: record that one
material even without a consumer. Raw material stays outside `.archcore/`; store
its locator and extract. After promotion, the source row keeps the external
locator; it does not name the `evidence` document.

Evidence produced during an investigation follows this sequence inside gather:

1. Record the intended evidence path and first relation endpoints in the parent draft's `deferred` state before creating evidence.
2. If the material already has a local evidence document, reuse that document.
3. Otherwise, call `create_document` with type `evidence`, status `draft`, and composed `content`.
4. Check `list_relations` for the intended edge before adding it.
5. If the edge is absent, call `add_relation` with `supports` or `contradicts`, from evidence to the local investigation.
6. If the material replaces another, add `supersedes` from the newer evidence to the older local evidence.
7. After all intended edges succeed, clear their pending entries in the parent draft's single gate-close `update_document`.

Create and first-edge writes belong to the same gather step before gate close.
They are separate MCP calls, not a transaction. Write failure handling:

1. If a write fails, report the error and keep gather open.
2. Preserve successful writes; do not roll them back.
3. On resume, reconcile the pending endpoints against existing documents and relations before retrying.
4. On a missing edge, retry the edge; never create a second evidence document to repair a missing edge.

Standalone evidence follows this sequence:

1. Compose Locator, Extract, and Notes.
2. Call `create_document` with type `evidence`, status `draft`, and that `content`.
3. Include `artifact_type: evidence` and the satisfied frame in the state block of that draft.
4. If the request or context identifies a local consumer, include the intended edges in `deferred` at creation, then follow the relation check and write sequence above.
5. If no consumer is identified, create the draft without an edge, report that fact, and ask no frame question.
6. If an intended edge fails, keep its endpoints in the evidence draft's `deferred` field and leave gather open; the same read-before-retry rule applies.
7. After successful completion, remove the state block at gate close.

Relations are not bound to a category. `supports` points from material to the
statement it backs; `contradicts` points from challenger to disputed statement;
`supersedes` points from replacement to replaced document. Research is never
`implements` or `extends`; use `rnd depends_on research` for an existing
territory that informs a decision-bound investigation. A contradiction remains
unresolved until the disputed document names both materials and its resolution
in prose. Contradiction edges are removed only by an explicit user request,
never by the track.

## Gather delegation

1. The read-only `archcore-auditor` agent MAY collect codebase and `.archcore/` material at `research.gather`; the calling skill passes it the current vocabulary probe result and absolute plugin root.
2. The main thread gathers web material directly with the host's web-fetch capability, composes the draft, conducts any interview, and performs every write.

### gate: research.frame

- Purpose: Fix the investigation's goal and its scope or decision questions.
- Entry conditions:
  - skip_when: a matching local artifact already satisfies this gate's exit checks and the request does not ask to redo, refresh, or extend it; reuse it and continue at gather.
  - The request names the subject under investigation or supplies a ready report.
- Elicitation knobs:
  - trigger: the investigation's goal, closing test, or scope remains unclear after grounding; a ready report can satisfy these inputs.
  - taxonomy: Functional Scope & Behavior, Constraints & Tradeoffs from
    `skills/_shared/coverage-taxonomy.md`.
  - budget: 2
- Produces:
  - type: research or rnd
  - status: draft
  - relations: `related` → an existing local `idea` or `prd` the investigation informs; `rnd depends_on research` when applicable.
- Exit checks:
  - blocking: the state records `artifact_type` matching the filename type.
  - blocking: an rnd draft contains Goal and numbered Questions.
  - blocking: a research draft contains Goal and Scope, including the scope boundaries; Questions is optional.
  - advisory: an rnd Questions section holds at most 5 questions.
- Next: `research.gather`.

### gate: research.gather

- Purpose: Record sourced findings and any reusable materials.
- Entry conditions:
  - skip_when: the local artifact satisfies this gate's exit checks and no intended evidence write or relation remains pending.
  - A research or rnd draft has passed frame, or an explicit evidence request supplies one material.
- Elicitation knobs:
  - trigger: none — the supplied material satisfies standalone evidence framing; investigation gaps are recorded for conclude.
  - taxonomy: none.
  - budget: 0
- Produces:
  - type: evidence — only on promotion or explicit material entry; otherwise no new document
  - status: draft
  - relations: `supports` or `contradicts` → the local investigation; `supersedes` → replaced local evidence; standalone evidence may have none.
- Exit checks:
  - blocking: a research's Sources records its materials, with access dates for web sources.
  - blocking: a research's Scope records the method used; Coverage and Findings distinguish covered scope from evidenced gaps.
  - blocking: an rnd's Approach records the method used and names the sources consulted, with access dates for web sources.
  - blocking: an rnd's Findings answers each question or names consulted sources and the unanswered question.
  - blocking: each evidence draft contains Locator, Extract, and Notes; Locator starts with Address, Access date, Publication date, Publisher lines.
  - blocking: unknown publication dates and publishers use visible placeholders; provenance contains no invented values.
  - blocking: evidence created for an investigation has its first `supports` or `contradicts` edge before gate close.
  - blocking: no intended evidence write or relation remains pending; standalone evidence without an identified consumer needs no edge.
  - advisory: findings follow the evidence and assumption rules in `skills/_shared/precision-rules.md`.
- Next: exit for standalone evidence; otherwise `research.conclude`.

### gate: research.conclude

- Purpose: Complete the scope synthesis or the decision recommendation.
- Entry conditions:
  - skip_when: the artifact satisfies every type-specific exit check below.
  - `research.gather` passed its blocking exit checks for a research or rnd draft.
- Elicitation knobs:
  - trigger: a material scope boundary remains unclear, or rnd findings support competing recommendations; recorded research gaps alone require no interview.
  - taxonomy: Constraints & Tradeoffs, Completion Signals from
    `skills/_shared/coverage-taxonomy.md`.
  - budget: 2
- Produces: none — complete the investigation draft.
- Exit checks:
  - blocking: a research contains Goal, Scope, Coverage, Sources, Findings, Synthesis, and Open Gaps.
  - blocking: research Coverage accounts for the declared scope; Synthesis follows Findings; Open Gaps names the remainder or states none.
  - blocking: an rnd contains Goal, Questions, Approach, Findings, Recommendation, and Next Action.
  - blocking: rnd Recommendation states proceed, refine, defer, or stop and names supporting findings; do not invent a verdict for fallback completion.
  - blocking: rnd Next Action names `/archcore:plan`, `/archcore:document`, or states that no follow-up is needed.
  - advisory: the report lists candidate local relation targets or states that none match.
- Next: exit.

### gate: research.spike

- Purpose: Run a timeboxed empirical probe — answer one question only building
  can answer, then hand the revised Δ back to the conductor.
- Entry conditions:
  - skip_when: existing evidence (code, git history, `.archcore/`, recorded
    measurements) already answers the empirical question.
  - The conductor names the empirical question and the timebox.
- Elicitation knobs:
  - trigger: none — the spike grounds from the probe itself.
  - taxonomy: none.
  - budget: 0
- Produces:
  - type: rnd
  - status: draft
  - relations: `related` → the `idea` or `prd` the spike informs, when one
    exists.
- Exit checks:
  - blocking: the rnd draft holds the sections Goal, Questions, and Findings
    only, with the probe outcome recorded under Findings.
  - blocking: the closing report states the probe outcome and the revised Δ
    handed to the conductor.
  - blocking: no spike code was merged into the mainline; the report names
    where the throwaway code lives or states that it was discarded.
- Next: exit — the conductor re-enters Derivation per
  `skills/_shared/delta-routing.md`.
