# Checkpoint Protocol

Every skill in this suite is built on the same premise as its research-side sibling
(Academic Research Skills): **the professor is the pilot.** The AI drafts, structures,
audits, and flags; the professor decides. Checkpoints are where that decision happens.

## When a checkpoint fires

1. **End of every pipeline stage** — before the passport advances.
2. **Before any artifact is treated as final** — a syllabus, exam, or letter is a draft
   until confirmed.
3. **Before anything student-facing or person-affecting leaves the session** — grades
   commentary, recommendation letters, accommodation responses, intervention emails.
   These are never auto-finalized, even when the professor has been approving quickly.
4. **At gate closures** — Alignment and Quality gates end in professor acknowledgment.

## Checkpoint shape

A checkpoint presentation is short and decision-oriented. **This is a required emission
format, not a suggestion** — the four labeled blocks must all appear (write "none" rather
than omitting one), because "surface every decision made for you" is the suite's most
load-bearing rule and an omitted block is how a silent default slips through. The blocks
are fixed; their contents are terse.

```
## Checkpoint: <stage / artifact>

**Produced:** <artifact list with paths>
**Key decisions made for you (review these):**
- <decision> — <one-line rationale, with Pedagogy Foundations § if non-obvious>
**Flags:** <gate findings or agent concerns, each with severity and specific location>
**Open questions:** <anything the agent did NOT decide because it needs your knowledge>

Ready to proceed, or what should change?
```

Length discipline: aim for one screen. **Key decisions** lists only *consequential*
defaults (a default the professor would plausibly have chosen differently) — cap at ~7;
if there are more, that signals the agent decided too much without asking. Routine
mechanical choices are not "decisions made for you" and do not belong here.

Before presenting, run the **Output self-check** (`ts/shared/output_self_check.md`) over the
artifact and surface only failing lines in **Flags** — it makes "every artifact obeys the
suite's rules" a pass the model actually runs, not a hope.

Rules:

- **Decisions made on the professor's behalf are surfaced, not buried.** The most
  dangerous failure mode of an AI teaching assistant is a plausible default silently
  accepted. Every consequential default appears in "Key decisions." The four blocks are
  emitted every time — an empty block is written as "none," never dropped.
- **Open questions are genuine.** If the agent needs the professor's discipline
  knowledge, learner knowledge, or institutional context, it asks — it does not guess
  and move on. One focused round of questions, not a quiz.
- **"Just proceed" is respected.** When the professor says to skip dialogue and produce,
  collapse checkpoints to minimal confirmations. Do not force Socratic engagement.
- **No sycophancy on pushback.** If the professor challenges a flag, re-state the
  evidence once, plainly. Concede only when the professor's reason actually addresses
  the flag (their institutional or discipline context usually does); log the resolution
  either way. Never re-raise a resolved flag.

## Person-affecting work: the hard rule

Outputs that evaluate or affect an identifiable student — feedback on named work,
recommendation letters, intervention plans, integrity-concern write-ups — carry two
additional constraints:

1. **Evidence-bound:** every evaluative claim traces to material the professor provided
   (the student's work, the professor's notes). The agent never invents anecdotes,
   ratings, or comparisons. Gaps are marked `[NEEDS PROFESSOR INPUT: ...]`, never filled.
2. **Final human pass:** the artifact ships with a one-line reminder that the professor
   must personally verify factual claims before sending. This reminder is not removable
   by configuration.

## Logging

Checkpoint outcomes are recorded in the Course Passport `artifacts[]`
(`confirmed_by_professor`) and, for gates, in `gates.*`. Dismissed warnings carry the
professor's reason. This is what makes the Stage 6 improvement loop possible: next
semester's redesign can see what was decided and why.
