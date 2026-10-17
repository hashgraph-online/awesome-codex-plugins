# Seeding a forcing defect (tier 2)

A **forcing defect** is a flaw planted in a realistic work artifact that the
skill's discipline catches and a skim does not. The probe grades whether the
agent *acted* on it.

## Diagnostic calibration

A seeded probe can help diagnose headroom. These are possible observations,
not requirements for accepting or retaining a case:

```
too obvious          USABLE WINDOW           too obscure
     |                     |                      |
 both arms            control misses,          neither arm
 catch it   <-------  treatment catches  ----> catches it
 (ceiling)                                     (floor)
```

Ceiling and floor observations limit the question a probe can answer. Calibrate
the discriminator on known transcripts before spending live reps. The check:
**can the defect be derived from the discipline
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

## Optional live development calibration

Use live calibration only inside an already accepted trial/time envelope. It
is development data, counts against the total cap, and does not become a hidden
holdout. Predeclare its stop; do not keep reseeding until treatment wins.

1. Draft the artifact with the defect.
2. If needed for the decision, run a bounded control sample at the deployed
   model and selected effort. Two reps can diagnose a scenario, not prove a rate.
3. If the control catches it in every sampled rep, record the observed ceiling.
   Keep it as an easy regression/cost control when relevant. A new development
   variant is a separate version, not permission to erase an unfavorable case.
4. If the control arm catches it in **0/2**, hand the same artifact to the
   treatment arm. If treatment is also 0/2 — below the window. The defect is not
   showing a positive signal in this sample. Check the discriminator and record
   the floor; do not infer a general defect in the skill from two misses.
5. Report the observed results whether positive, null or adverse. Freeze the
   chosen development cases before any separately authorized comparison.

Count all calibration starts, including failures and treatment calibration;
calibration does not always cost only two reps or guarantee useful separation.

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
