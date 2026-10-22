# Peer Assessment Guide

Working reference for `group_designer_agent` and professors reviewing graded group work.
A group grade is only defensible if it reflects what each member contributed; peer
assessment is the main instrument for getting there — but it is noisy, gameable, and easy
to misuse. This guide covers what the evidence supports, how a contribution-adjustment
factor works, and the pitfalls that turn peer assessment into a popularity vote.

## Why group grades need help

A pure group grade — every member gets the team's score — measures the *team's* output,
not the *student's* learning, and it systematically advantages free-riders and
disadvantages the conscientious member who carried the work. The individual-accountability
mechanism (an individually-graded component, a contribution log, or a peer-adjusted grade)
is what restores the link between a student's grade and a student's work. Peer assessment
is one such mechanism; it is strongest when combined with at least one other (e.g. an
individual reflection or viva), not relied on alone.

## What the evidence supports (and its limits)

- Peer ratings of contribution **correlate reasonably with instructor judgments** when the
  instrument asks about *observable behaviors* (did this person do their share, meet
  deadlines, communicate) rather than global liking — but the correlation is moderate, not
  high. Treat peer scores as *evidence*, not as ground truth. `[VERIFY: cite the specific
  CATME / peer-assessment validity studies the professor's institution relies on]`
- **Multiple low-stakes rounds beat one high-stakes round.** A mid-project peer check-in
  lets a team correct course (and gives a struggling member a chance to recover) before a
  final rating decides a grade. A single end-of-term rating is both noisier and crueler.
- **Behavioral anchors reduce bias.** A 1–5 scale with no descriptors collects feelings; a
  scale anchored in observable behavior ("attended all meetings and delivered assigned work
  on time" vs "frequently missed meetings or deadlines") collects evidence.
- **Self-rating included** lets the agent and professor see calibration gaps (the member who
  rates themselves far above how teammates rate them).

### CATME-style factors

A widely used contribution framework rates each member (including self) on factors such as:
contributing to the team's work; interacting with teammates; keeping the team on track;
expecting quality; and having relevant knowledge, skills, and abilities. Each factor uses
behavioral-anchor descriptors, not a bare number. The form is confidential to the
professor — teammates' raw ratings are never shown to the rated peer.

## Contribution-adjustment formulas

The point is to translate peer ratings into a *bounded* adjustment of the individual grade,
which the professor reviews before it lands. Two common approaches:

1. **Adjustment factor (individual ÷ team average).**
   - For each student, average the ratings their teammates gave them (optionally including
     self at a discounted weight).
   - Compute the team's average of those per-student averages.
   - `factor = student's average ÷ team average` (1.0 = contributed an average share).
   - `individual grade = group grade × factor`, **capped** (e.g. factor confined to
     0.8–1.2, or whatever the professor sets) so one harsh or generous rater cannot swing
     a grade wildly.
2. **Additive adjustment.** A fixed number of points added or subtracted by rating band
   (e.g. top band +3, bottom band −5) against the group grade — simpler to explain, blunter.

Worked sketch (factor method): group grade 85; a member rated well above teammates gets
factor 1.10 (capped) → 93.5; a member rated well below gets 0.85 → 72.25. The professor
reviews both adjustments against the contribution evidence before either is final.

**The cap is mandatory.** Without it, a single outlier rating (a feud, a friendship bloc)
can dominate. State the cap on the peer-assessment form so students know the rule.

## Pitfalls

| Pitfall | Symptom | Mitigation |
|---------|---------|------------|
| **Popularity vote** | high raters reward likability, not work | behavioral-anchor descriptors; rate factors, not the person |
| **Collusion / reciprocity** | "we all rate each other 5" | confidential ratings; self-rating to expose calibration; instructor evidence (milestone outputs) as a cross-check |
| **Retaliation / feuds** | one member tanked by a bloc | the cap; outlier ratings flagged for professor review, not auto-applied |
| **Bias** | gender/identity bias in contribution ratings | observable behaviors only; the professor reviews every adjustment; aggregate the form across rounds |
| **Free-rider undetected until the end** | no early signal | mid-project peer check-in + a documented contribution trail |
| **Formula-as-verdict** | a grade set by arithmetic, unreviewed | the professor reviews every adjustment; the formula informs, it does not decide |

## What stays with the professor

- The **final grade and every adjustment** — peer assessment is an input the professor
  confirms, never an automated output.
- **Confirmed non-contributor handling** (reduced individual grade per the stated policy,
  removal to an individual deliverable) — and the institutional dispute/escalation
  procedure, which is `[NEEDS PROFESSOR INPUT]`, never invented here.
- Peer ratings are confidential to the professor; raw ratings are never returned to the
  rated student.
