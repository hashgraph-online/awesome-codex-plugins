# Diagnostic Design Guide

Practical item craft for ungraded diagnostics and pre-lesson questionnaires — the
working reference for `diagnostic_designer_agent` and the professor reviewing its
drafts. Everything here serves one test: *does this item inform a decision the
professor will actually make?* Graded-instrument craft lives in assessment-architect's
`item_writing_rules.md`; the universal stem/option rules there apply here too — what
changes is the purpose, the stakes, and the length budget.

## 1. The analysis-plan-first discipline

Blueprint-first (Pedagogy Foundations §10), translated for diagnostics: before any
item is drafted, the plan states **item → concept probed → decision it informs**.

| Plan entry | Good | Bad |
|------------|------|-----|
| Decision | "If <50% transfer-correct on pointers, W2 opens with a 15-min worked-example reteach instead of the planned recap slide" | "See where students are on pointers" |

"See where students are" is not a decision — it is curiosity, and curiosity does not
justify ten minutes of 60 students' time. An item that informs no decision is cut at
the plan stage. The plan is also the analysis contract: when results arrive,
`cohort_analyst_agent` computes exactly what the plan promised, which prevents
post-hoc fishing.

## 2. Prerequisite probe patterns

One concept per item, deployed as a **recall + near-transfer pair**:

- **Recall probe** — can they retrieve the fact/definition/procedure? ("What does a
  pointer store?")
- **Near-transfer probe** — can they use it in a slightly new arrangement? ("This
  3-line snippet swaps two pointers — what does it print?")

The pair matters because the two failure patterns demand different responses: recall
weak + transfer weak = never learned or fully decayed → reteach; recall solid +
transfer weak = inert knowledge → activate with worked examples and retrieval
practice (Pedagogy Foundations §5, §9), not a re-lecture they will recognize and
tune out. A diagnostic with recall items only systematically overstates readiness —
the most common diagnostic design defect.

Keep transfer *near*: same concept, new surface. Far-transfer items measure general
problem-solving and produce findings about the wrong thing.

## 3. Two-tier misconception items

Anatomy — two tiers, counted separately:

- **Tier 1 (answer):** an MC item whose distractors encode documented misconceptions
  — from `learner_profile.known_difficulties`, the professor's experience, or
  literature the designer can actually name (`[VERIFY]` otherwise).
- **Tier 2 (reasoning):** "Which best matches your reasoning?" — options mirroring
  tier 1's logic: the correct rationale, each misconception's rationale, and an
  honest "I guessed / not sure" (which makes guessing visible instead of polluting
  the misconception counts).

The combination plain scoring cannot see — **right answer + wrong reasoning** — is
frequently the largest actionable finding: those students pass a recall quiz and
fail the exam.

### Worked example — quantitative (intro statistics)

> **Tier 1.** A fair coin has landed heads 5 times in a row. On the next flip, tails
> is: (a) more likely than heads (b) less likely than heads (c) equally likely ✓
>
> **Tier 2.** Which best matches your reasoning? (1) After so many heads, tails is
> "due" so the results balance out *(gambler's fallacy — the target misconception)*
> (2) Each flip is independent; the coin has no memory ✓ (3) A streak that long means
> the coin must favor heads *(contradicts the stated premise — premise-ignoring
> pattern)* (4) I guessed.

Reportable findings: (c)+(2) mastery; (c)+(1) right answer, wrong reasoning — counted
separately; (a)+(1) confirmed gambler's fallacy.

### Worked example — qualitative (historical methods)

> **Tier 1.** A diary written by an eyewitness to an event, compared with a
> historian's account written 50 years later, is: (a) more reliable (b) less
> reliable (c) not rankable without analyzing each source's purpose, audience, and
> corroboration ✓
>
> **Tier 2.** Which best matches your reasoning? (1) The eyewitness was there, so
> their account is closest to the truth *(proximity-equals-reliability — the target
> misconception)* (2) Reliability depends on how and why a source was produced, not
> only on closeness to the event ✓ (3) Historians are trained to be objective, so
> later accounts are more reliable *(the inverted misconception)* (4) I guessed.

## 4. Background and experience items

Usable when the analysis plan consumes them (a calibration call, a role-based
grouping). Pattern: **checkable facts, not self-ratings in disguise.**

| Good (fact) | Bad (rating wearing a fact's clothes) |
|-------------|---------------------------------------|
| "Which of these courses have you completed? [list]" | "How strong is your math background?" |
| "Have you written a program longer than ~100 lines? (yes/no)" | "Rate your programming ability 1–5" |
| "Which of these tools have you used for a real task? [list]" | "Are you comfortable with spreadsheets?" |

## 5. Self-efficacy items

Optional, useful for the calibration gap (`analytics_honesty.md` §3) — and always
labeled self-report in the instrument's instructor block, the report, and the
passport. Phrasing rules: **concrete task, bounded scope** — "How confident are you
that you could compute a standard deviation by hand right now? (1–5)" — never global
self-assessment ("Are you good at statistics?"), which measures self-image and
demographic confidence patterns more than anything course-relevant. The caveat
travels with the item: novices systematically over-rate; this item measures
confidence, not ability, and its best use is cohort-level change and the
confidence-vs-measured gap.

## 6. What NOT to ask

- **Demographics the analysis doesn't use.** Age, nationality, family background —
  if no plan entry consumes it, it is data collected for nothing and risk stored for
  free (minimization, `analytics_honesty.md` §5).
- **Anything stigmatizing to answer.** Disability or accommodation status (that is
  the institution's confidential channel, not a questionnaire), mental health,
  financial situation, "have you failed this course before."
- **Anything the professor couldn't act on.** If no realistic version of next week
  changes based on the answer, the item is curiosity — cut it.
- **Anything secretly evaluative.** An "ungraded" item the professor privately plans
  to judge individuals by breaks the framing that makes the data honest — and breaks
  it permanently for this cohort.

## 7. Length, timing, and the named-vs-anonymous choice

- **Length: 5–10 minutes, hard ceiling** (roughly 6–12 items). Completion beats
  coverage; fatigue and skipping corrupt the tail items first, silently. Cut by
  analysis-plan priority.
- **Timing:** pre-course diagnostics in the week before or the first meeting;
  pre-lesson questionnaires 2–4 days before the meeting (close enough to be current,
  far enough to calibrate the build).
- **Named vs anonymous — the professor chooses per purpose, tradeoff stated:**
  - *Named* enables individual follow-up (the professor, with the evidence, via
    `student-mentor`) — but suppresses honesty: students hedge what they think might
    be judged. Requires the pseudonymization pass before analysis; cohort findings
    are computed identically.
  - *Anonymous* improves honesty — and caps the analysis at cohort level, which for
    most calibration purposes is all the analysis was ever going to use.
  - The choice and its reason are recorded in the instrument's instructor block.
    Either way, the framing text must be true: never tell students "anonymous" while
    collecting login-linked responses.

## 8. Deployment checklist

- [ ] Analysis plan complete — every item names its decision; every decision has a
      consumer (course-designer / lesson-builder / grouping)
- [ ] Length ≤ 10 minutes at a realistic answering pace (time it, don't estimate it)
- [ ] Ungraded framing text present and true: why honesty helps them, what happens
      to the data, time estimate
- [ ] Named-vs-anonymous chosen, reason recorded, framing text consistent with it
- [ ] Self-efficacy items labeled; "not sure / I guessed" options where guessing
      would pollute counts
- [ ] `[VERIFY]` markers resolved by the professor (misconceptions, domain facts)
- [ ] Channel set (LMS quiz, paper, clickers) and results-export format confirmed —
      an instrument whose results can't be exported can't be analyzed
- [ ] Close-the-loop moment planned: tell students one thing the results changed —
      next instrument's response rate depends on this one visibly mattering
