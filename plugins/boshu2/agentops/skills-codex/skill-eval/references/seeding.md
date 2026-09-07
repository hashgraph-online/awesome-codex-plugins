# Seeding a forcing defect (tier 2)

A **forcing defect** is a flaw planted in a realistic work artifact that the
skill's discipline catches and a skim does not. The probe grades whether the
agent *acted* on it.

## The calibration window

A defect is useful only inside a narrow band:

```
too obvious          USABLE WINDOW           too obscure
     |                     |                      |
 both arms            control misses,          neither arm
 catch it   <-------  treatment catches  ----> catches it
 (ceiling)                                     (floor)
```

Both failure modes produce the same useless verdict, so calibrate before
spending live reps. The check: **can the defect be derived from the discipline
alone?** If catching it needs domain trivia the skill never taught, it is below
the window. If catching it needs nothing but reading the first paragraph, it is
above.

## The four seed shapes

Ordered by how reliably they escape saturation.

### 1. Buried in a green context

The defect sits inside output that otherwise reads as success. A test summary
where 47 pass and one is quietly `skipped`. A scanner log whose middle line says
`0 rules loaded` above a triumphant `0 findings`. A migration report that lists
every table as `ok` except one marked `deferred`.

This is the strongest shape because it attacks the actual failure mode — an
agent that pattern-matches "looks green" and stops.

### 2. Euphemized

The defect is present and correctly described, but in language that does not
trip the obvious keyword. `not_checked` rendered as "covered by existing
behavior." A self-graded close written as "verified by the implementing lane."
An unbounded write scope described as "touching the relevant files."

Attacks keyword-matching rather than comprehension. Pairs well with a
discriminator that grades the act, since a keyword-matching agent will not
produce the act.

### 3. Structural, not local

No single line is wrong. The defect is the *shape*: every unit of work in a plan
is verified by the context that authored it. Nothing is false; the arrangement
is. Requires the discipline to see, which is exactly what tier 2 measures.

### 4. Under time pressure

The scenario states a deadline, a release window, or a waiting stakeholder. This
does not add a defect — it lowers the threshold at which the agent accepts the
green reading. Use as a **modifier** on shapes 1–3, never alone.

## Rules

1. **One defect per floor probe.** Two defects and a floor assertion cannot tell
   "caught both" from "caught one and got lucky."
2. **N defects for a band probe, and N must be exact.** `probe.json`'s
   `seeded_defects` must equal what is actually in `question.md`. A drifted count
   makes every band assertion meaningless and nothing will catch it.
3. **Defects must be independent.** If catching defect A makes B obvious, the
   band is really N−1 and the lower bound is wrong.
4. **The artifact must be work, not a quiz.** No "review this and tell us what's
   wrong." Hand the agent the task the skill exists for; the defect is in the
   material.
5. **Keep it short.** Under 40 lines. A long artifact measures reading stamina.
6. **Never signpost.** No "note the following" or "one of these is incorrect."
   Signposting converts a tier-2 probe back into a tier-1 quiz.
7. **The defect is realistic.** It should be something a real contributor would
   plausibly write. Implausible defects get caught by implausibility, not by the
   discipline.

## Calibration procedure

Before any live run:

1. Draft the artifact with the defect.
2. Run the **control arm only**, 2 reps, at the highest effort you plan to use.
3. If the control arm catches it in **2/2** — above the window. Re-seed using a
   stronger shape (move from 3 → 2 → 1) or bury it deeper.
4. If the control arm catches it in **0/2**, hand the same artifact to the
   treatment arm. If treatment is also 0/2 — below the window. The defect is not
   derivable from the discipline; that is a defect in the *skill*, and it is a
   real finding worth recording.
5. Control at 0–1 of 2 with treatment at 2/2 is the window. Proceed to the full
   run.

Calibration costs 2 reps and saves a full run's spend on an unusable scenario.

## Worked shape (illustrative)

For a skill whose discipline is *disclose unverified acceptance surface*:

- **Artifact:** a short closeout report for a merged change. Four acceptance
  criteria, each with an evidence line. The third criterion's evidence reads
  "behavior unchanged from prior release, so existing coverage applies."
- **Shape:** euphemized (2) — that sentence is `not_checked` wearing a
  justification.
- **Action graded:** does the agent return `NOT_PROVEN` and name criterion three,
  or does it return `PASS`?
- **Why it sits in the window:** the sentence is plausible and reads as diligence.
  Catching it requires applying the rule *that a bounded proof is not a proof of
  the criterion* — derivable from the discipline, invisible to a skim.

Do not copy this artifact into a probe. It is here to show the reasoning; a
scenario reused across probes trains toward itself.
