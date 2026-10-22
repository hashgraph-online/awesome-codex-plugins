# Recommendation Letter Guide

Working reference for `recommendation_writer_agent`. Governing rule: the letter is a
set of factual claims under the professor's signature — every claim is collected at
intake, never composed at the keyboard.

## Intake question set

Ask in one focused round; record answers in `intake_record.md` (the letter's evidence
trail).

1. **Relationship:** In what capacity and for how long have you known the student?
   Course(s) with size and the student's grade; research role; advising relationship.
2. **Incidents:** Describe 2–3 specific moments that show what this student is like to
   work with. Push past adjectives — "brilliant" → *what did they do?* A question they
   asked, a problem they solved, a draft they rescued, how they handled being wrong.
3. **Comparative standing:** What comparison are you willing to put your name to?
   ("Top 5% of undergraduates I've taught in 12 years" / "among the better students in
   a strong cohort" / "I can't rank them — I only know their exam work.") The draft
   never exceeds this bracket.
4. **Destination:** Program/job/scholarship, what it selects for, deadline, submission
   format (portal/email/paper), addressee if known.
5. **Reservations:** Anything you'd hesitate to defend if asked directly? (Reservations
   shape what the letter omits — and omissions communicate; see below.)
6. **Logistics:** Has the student waived their right to view the letter? Any
   institutional letterhead/signature requirements?

## Structure norms

1. **Opening:** who the recommender is, in what capacity they know the student, for how
   long, and the headline assessment in one sentence. Readers skim; the first paragraph
   carries the verdict.
2. **Body (1–3 paragraphs):** one quality per paragraph, each anchored to a specific
   incident from intake. Claim → evidence → why it matters for the destination.
3. **Comparative paragraph:** the standing the professor authorized, with its reference
   class stated ("of the ~400 students in my courses over the last decade").
4. **Closing:** strength-calibrated recommendation sentence + invitation to contact.

## Length and strength signaling — what omission communicates

Letters are read against genre expectations; deviations are signals, intended or not:

| Signal | Read as |
|--------|---------|
| Very short letter (≤ half page) for a US PhD application | Weak endorsement, regardless of adjectives used |
| No comparative ranking where the genre expects one | The recommender couldn't honestly rank highly |
| Praise only for diligence/attendance, silence on intellect | Damning with faint praise |
| "Did well in my course" with no incident | The recommender doesn't actually know the student |
| Closing "recommend" vs "recommend strongly/enthusiastically/without reservation" | Readers calibrate on this scale; choose deliberately |

The agent flags any such signal the draft emits, so the professor sends it on purpose
or fixes it — an *accidental* lukewarm signal is the failure; a deliberate one is honest.

## Bias-pattern table (research-documented; flag, professor decides)

| Pattern | Example | Neutral alternative |
|---------|---------|--------------------|
| Doubt-raiser | "While not the most polished presenter, she…" | State the strength directly; cut the unprompted concession, or make it a developmental note with evidence |
| Grindstone vs standout framing | "hardworking, diligent, dependable" (where male peers get "brilliant, incisive") | If the evidence shows insight, say "insightful" with the incident; effort-words only when effort is genuinely the point |
| First-name usage | "Maria is a pleasure to have in class" (vs "Mr. Chen demonstrates…") | Consistent convention: full name once, then surname or consistent first-name for all letters the professor writes |
| Hedging | "I believe she could likely succeed…" | "Her work on X shows she can Y" — or, if the hedge reflects real uncertainty, keep it *knowingly* |
| Personal-life mentions | "a devoted mother who still found time to…" | Cut unless the candidate explicitly wants it; achievement stands without domestic framing |
| Communal vs agentic emphasis | "helpful, kind, a wonderful team member" as the *headline* | Lead with the destination-relevant capability; communal qualities as supporting, evidenced traits |

Flag format in drafts: `[BIAS-CHECK: doubt-raiser — suggested rewrite: "…" — your call]`.
Every flag is a decision returned to the professor, not an auto-correction.

## Decline-gracefully scripts

Offered whenever the honest-letter protocol finds thin evidence. Two registers:

**Redirect (most common):**
> "Thank you for thinking of me. To be the advocate you deserve, a recommender needs
> specific, recent examples of your work, and from one course two years ago I don't
> have enough to write the strong letter this application needs. A letter from
> {{someone who supervised your project / your seminar instructor}} would carry much
> more weight. I'm glad to help you think about who to ask."

**Conditional (when more evidence could exist):**
> "I'd want to write you a strong letter, and right now I only know your exam work.
> If you can share {{your thesis draft / the project repo / your statement of purpose}}
> and we talk for thirty minutes, I'll be able to say something substantive. If the
> deadline doesn't allow that, someone who already knows your work well is the better
> choice."

A truthful decline is kinder than a thin letter the admissions committee will read as
lukewarm.

## Logistics checklist (all professor-input items)

- [ ] Deadline and time zone — `[NEEDS PROFESSOR INPUT]`
- [ ] Submission route: portal link / email / sealed paper — `[NEEDS PROFESSOR INPUT]`
- [ ] Confidentiality waiver: signed/waived? (changes candor calculus; the professor
      should know before drafting) — `[NEEDS PROFESSOR INPUT]`
- [ ] Letterhead and signature requirements — `[NEEDS PROFESSOR INPUT]`
- [ ] Number of programs/letters and any per-program tailoring — `[NEEDS PROFESSOR INPUT]`
- [ ] Final human pass completed: every claim verified against memory and records before
      submission — **non-removable**
