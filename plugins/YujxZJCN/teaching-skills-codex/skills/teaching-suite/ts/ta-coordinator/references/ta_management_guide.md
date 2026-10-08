# TA Management Guide

Working reference for all `ta-coordinator` agents and for professors reviewing their
drafts. The stance throughout: TAs are apprentice colleagues — most of what goes wrong
in TA teams is ambiguity, not incompetence, and the fixes below are structural before
they are personal. Anything evaluative about a named TA falls under the
person-affecting rule in `ts/shared/checkpoint_protocol.md`.

## The boundary table

The single highest-leverage onboarding artifact. Default starting set — the professor
edits it per course; every decision a TA might face should land in exactly one column.

| TA owns outright | Escalates to the professor |
|------------------|----------------------------|
| Applying the rubric + calibration annotations to submissions | **Regrade requests** — TA collects the student's written rationale and forwards; never re-decides their own grading |
| Applying the *published* late policy (e.g., automatic 48h grace) | **Extensions beyond published policy** — exceptions are personnel-of-the-course decisions |
| Answering content questions in office hours and sections | **Integrity suspicions** — document what was observed, escalate same day; never confront or adjudicate |
| Logistics within their duties (rescheduling their own office hour with notice) | **A distressed student** — warm handoff: tell the professor promptly, point the student to institutional resources; the TA is never the counselor |
| Flagging a submission no rubric descriptor fits (escalate, don't improvise a score) | **Any grade change after release** |
| Routine announcements the professor has approved | **Accommodation matters** — disability accommodations follow institutional procedure, not TA discretion |
|  | **Media, parents, or anyone outside the class asking about a student** — decline + refer (see Privacy below) |

Worked examples beat abstract rules in orientation: "a student emails you asking for
two more days — which row is that?" is worth a page of policy prose.

## Onboarding content checklist

A course-specific handbook (see `ts/ta-coordinator/templates/ta_handbook_template.md`) covers:

- [ ] Course facts: code, title, term, modality, class size, where materials live
- [ ] Each TA's duties and contracted hours ★ `[NEEDS PROFESSOR INPUT]`
- [ ] The boundary table, confirmed by the professor for this course
- [ ] Grading workflow end-to-end: where submissions appear, rubric + annotations
      location, how scores are entered, deadline per assessment
- [ ] Tool access: LMS grader role, gradebook, team channel ★ (institutional — who
      provisions what)
- [ ] Calibration expectations: sessions happen before consequential grading; pre-work
      is part of the job, not extra
- [ ] Communication norms: channels, expected response times, what's urgent
- [ ] Escalation contacts: professor's channel + response window; backup ★
- [ ] Confidentiality briefing (below)
- [ ] Week-1 checklist with owners and dates
- [ ] Development goals: 1–2 things this TA should be able to do by term's end

★ = institution- or contract-specific; defaults to `[NEEDS PROFESSOR INPUT]`.

## The calibration lifecycle across a term

Calibration is not an event; it is a maintenance schedule. The session protocol itself
lives in `ts/assessment-architect/references/rubric_patterns.md` § TA calibration protocol;
`calibration_facilitator_agent` operationalizes it.

1. **Initial norm** — before the first consequential grading of the term, even with
   returning TAs: the course, rubric, or cohort changed even if the people didn't.
2. **Per-new-instrument norm** — every new rubric gets a session before grading opens.
   A team calibrated on essays is not calibrated on lab reports. Shorter is fine
   (30 min, two anchors) when the team is established.
3. **Drift-triggered re-norm** — when `consistency` mode flags it, or when regrade
   requests cluster on one criterion or one grader's batch. Targeted: re-norm the
   specific boundary, not the whole rubric.
4. **Inheritance** — annotations and rulings are logged with the rubric artifact;
   next term's team reads the case law instead of re-litigating it.

## Workload estimation heuristics

Starting constants for `workload_allocator_agent` — every one is shown to the
professor as editable, because disciplines and rubrics vary widely.

| Assessment type | Minutes per submission (experienced TA) | Notes |
|-----------------|------------------------------------------|-------|
| Multiple-choice / auto-scored | 0.5–1 (spot-check + exceptions) | Near-zero if truly auto-graded; budget the exception handling |
| Short-answer quiz | 2–4 | Per quiz, not per question |
| Problem set (worked solutions) | 8–15 | Partial credit drives the spread |
| Lab report | 10–15 | More with code execution or data checks |
| Essay 1500–2500 words, analytic rubric | 15–25 | Written feedback expected pushes the top |
| Project milestone / single-point rubric | 10–20 | Comments are the product |
| Final project or paper, high stakes | 25–40 | Includes defensible margin notes |
| Presentation (live) | runtime + 5 | Scoring during + notes after |

**Multipliers:** novice TA, first grading run of this type — ×1.5–2 (and it drops fast;
re-estimate after their first batch). New rubric, any grader — ×1.3 for the first
batch. Add per-batch overhead (~10%) for entering scores, flagging escalations, and
breaks — humans do not grade at rated speed for four hours.

**Non-grading duties:** office hours and sections at scheduled time + equal prep for
novices (prep falls toward 0.5× as the term runs); meetings at scheduled time;
proctoring at exam time + 30 min.

## Meeting cadence patterns

| Pattern | Use when | Shape |
|---------|----------|-------|
| Weekly 30 min standing | Default for teams ≥2 in active grading weeks | This week's due/grading → calibration needs → escalations → decisions logged |
| Biweekly + async updates | Light-duty weeks, established team | Async written check-in alternates with the live meeting |
| Pre-assessment huddle | The week any major instrument goes live | Allocation confirm + calibration session can replace the regular meeting |
| 1:1 developmental, ~3× per term | Always, alongside the cadence above | Not logistics: the TA's development goals, what they want to try, what's hard |

`meeting` mode builds the agenda from the course's actual week (passport schedule:
what's due, what opens, what's mid-grading) — a standing agenda nobody edits is how
escalations rot. The **decisions log** is the meeting's real output: rulings carry
across the term so week-9 grading honors week-3 decisions.

## Common TA-team failure modes

| Failure | Early sign | Fix |
|---------|-----------|-----|
| **Ambiguous authority** | TAs improvising on extensions/regrades; students getting different answers to the same question | Boundary table read-through with worked examples; re-confirm at the next meeting — this is an onboarding defect, not a TA defect |
| **Rubric drift** | Scores tighten right after norming, spread again weeks later; annotations unread | Drift-triggered re-norm on the specific boundary; distribute annotated rubric v2, not the bare original |
| **Hero TA overload** | One TA answers everything first, absorbs every gap, hours quietly exceed contract | Rebalance by estimated hours; route gaps through allocation, not through whoever responds fastest; check actual hours, not vibes |
| **Ghost TA** | Slow responses, missed deadlines, absent from meetings — often weeks before anyone names it | Early, private, developmental check-in by the professor (often a workload, research-deadline, or personal issue, not defiance); structured evidence if it persists — professor's call throughout |
| **Leniency divergence** | Regrade requests cluster on one grader's batch; one section's grades run high | `consistency` mode: confirm with distributions + a double-grade sample (rule out section differences first); targeted re-norm |
| **Feedback-quality divergence** | Same score, wildly different comment depth across graders; students compare notes | Set a feedback floor in calibration (e.g., "every score below top level cites the rubric row and one location in the work"); add a comment anchor to the session |
| **Mid-stream rubric rewrite** | "Let's just change the descriptor" halfway through grading | Annotations interpret; rewrites stop the line — professor decision with regrade implications stated before anything changes |

## Developmental mentoring notes

TAs are future faculty (or future colleagues elsewhere), and a TA term is often their
only supervised teaching apprenticeship. Cheap, high-yield practices:

- **Name the learning goals in week 1** (handbook development section) and return to
  them in 1:1s — "you wanted to run a section solo; week 6 is a good one."
- **Graduated responsibility**: shadow → co-run → run-with-debrief, for sections,
  office hours, and eventually a guest-taught class if the course allows.
- **Let TAs see the design, not just the labor**: a TA who helps select calibration
  anchors or drafts a rubric row (professor reviews) learns assessment design;
  rotation through duty types is development, not just fairness.
- **Debrief incidents as cases**: a hard office-hours question or a tense student
  email, handled and then discussed for ten minutes, is the curriculum.
- **Write it down**: concrete observations of what a TA did well, recorded in-term,
  are the raw material for honest recommendation letters later (drafted via
  `student-mentor`, evidence-bound as always).

## Privacy and professionalism

TAs see student work, grades, and sometimes personal circumstances. The briefing below
is generic by design — FERPA (US), GDPR-derived rules (EU), PIPL (China), and
institutional policies differ, so the professor must layer the local rules on top:
`[NEEDS PROFESSOR INPUT: institutional student-records policy + any required TA
privacy training]`.

Core briefing content for the handbook:

1. **Student work and grades are confidential.** Discussed only within the teaching
   team, only for teaching purposes. Never with other students, friends, labmates, or
   in any public or semi-public channel.
2. **No grade disclosure outside secure channels.** Grades go through the LMS/gradebook,
   never email-on-request, never posted lists, never read aloud.
3. **Anyone outside the class asking about a student** — parents, employers, other
   students, media — gets a polite decline and a referral to the professor. Even
   confirming that someone is enrolled can be a disclosure.
4. **Examples are anonymized.** Using student work as a class example or calibration
   anchor requires anonymization (and, at many institutions, consent — local rule).
5. **Keep records where the course keeps them.** No grades or student work on personal
   accounts or devices beyond what the institution's tools require.
6. **When in doubt, ask before disclosing.** The recoverable error is the question;
   the unrecoverable one is the disclosure.

Professionalism corollary: TAs hold power over students' grades. Dual relationships
(grading a friend — see the conflict-of-interest screen in allocation), socializing
that compromises impartiality, and any romantic involvement with a student in the
course are escalation matters governed by institutional policy, named plainly in the
handbook rather than left to be discovered.
