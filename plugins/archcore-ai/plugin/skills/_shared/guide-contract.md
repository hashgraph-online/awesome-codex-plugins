# Guide Content Contract

Plugin runtime asset. Loaded before composing any `guide`: `plan` (the runbook
instrument at `sdd.runbook`), `document` (the describe track and the decision
track's standard cascade), `review` (the experience offer). Companion to
`skills/_shared/precision-rules.md`.

## What a guide is

An **authored, human-facing procedure**: one named reader performs one task
through explicit steps. A guide exists so the reader completes the task without
re-deriving it from code, chat history, or a teammate. Distinguished from:

- a `task-type` — a recurring task pattern captured from repetition, consumed
  by agents (its Steps seed plan decomposition), not authored for a human
  reader;
- a `doc` — reference material to look up, not a procedure to perform;
- a `rule` — a binding constraint to obey, not a sequence to execute;
- a `spec` — the behavior contract of a subject, not instructions for a person.

**Boundary rule:** the step actor decides the type — a human actor routes to
`guide`, an agent actor routes to `task-type`. Provenance is the tiebreak: a
pattern captured from repetition with an agent consumer stays `task-type` even
when a human could follow its steps.

## When NOT to write a guide

- The procedure's actor is an agent → `task-type`.
- The content is a registry, table, or glossary → `doc`.
- The content constrains behavior ("always X") → `rule`.
- The procedure runs once and holds no reuse value → record it in the PR or
  the plan task; write no guide.

## Mandatory content

1. **Reader and actor line** — one line before Prerequisites naming the
   intended reader, the task the guide supports, and the step actor.
2. **Prerequisites** — what exists or is installed before step 1.
3. **Steps** — numbered; one imperative action per step; a condition precedes
   the step it controls; a warning precedes the hazardous step; commands appear
   exactly as the reader must enter them. Step form:
   `skills/_shared/precision-rules.md` Rule 7 — the procedure profile, no
   modal, at or under 20 words per step.
4. **Verification** — the observable result that tells the reader the task
   worked; state the expected output where a command produces one.
5. **Common Issues** — known failure signs with their causes and corrections.

## Forbidden in the body

- A mandatory action hidden inside a note or an explanation paragraph.
- Narrative modality ("you should probably…") inside a step.
- A section enumerating other `.archcore/` documents — cross-document links
  live in the relation graph (`skills/_shared/precision-rules.md` Rule 5).
  The body MAY cite `@path/to/file`, exact commands, and external authorities.
- Background theory inside the numbered steps — it belongs before or after
  the procedure.

## Enforcement

The Archcore CLI reports the mechanical part in the post-tool-use hook: the
mandatory sections of the `guide` template and the step-form metrics of
precision Rule 7. Whether the named reader is the right one, and whether the
actor boundary against `task-type` was applied, stays with review.
