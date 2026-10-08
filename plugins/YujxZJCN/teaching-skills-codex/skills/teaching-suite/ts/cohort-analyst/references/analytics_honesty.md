# Analytics Honesty

The rulebook every cohort-analyst agent works under. Two constraints define this
skill — the privacy architecture (§5) and measurement honesty (§1–§4) — and both
exist because cohort data invites two specific failures: over-reading weak
instruments, and letting analysis about a class quietly become a file about a
person. The stance mirrors Pedagogy Foundations §11: this data is evidence, not
truth, and the caveats are load-bearing.

## 1. What each instrument can and cannot support

Provenance determines decision strength. Classify every dataset against this table
before analyzing it, and state the row in the report header.

| Instrument | What it actually measures | Commonly misread as | Decision strength |
|------------|--------------------------|---------------------|-------------------|
| Ability list of unknown provenance ("the department says these are the levels") | Someone's past judgment, criteria unknown, date unknown | Current measured ability | **Weakest.** Context only; supports no per-concept decision. Ask what produced it; usually the honest answer is "run a diagnostic" |
| Self-report questionnaire (confidence, experience, exposure) | What students *believe and report* about themselves | Measured readiness | **Weak for ability, fair for facts.** Factual items (courses taken, tools used) are usable; confidence items are engagement/calibration signal only (§3) |
| Diagnostic quiz, 5–10 ungraded items | Performance on those k items, on that day, by respondents | A measurement of "what the class knows" | **Moderate — the workhorse.** Supports reteach/activate/skip calls, distractor choices, grouping spread. Does not support syllabus restructuring or any claim about an individual |
| Prior-course grades | Composite past performance against another course's mixed criteria | Per-concept preparation for *this* course | **Weak-to-moderate.** A coarse prior; says nothing about which prerequisite concept is weak — the question calibration actually needs answered |

Two corollaries agents enforce:

- **Decision weight caps.** A finding never supports a decision heavier than its row
  allows. "Open W3 with a 10-minute review" can rest on a 5-item quiz;
  "drop LO4" cannot.
- **A 5-item quiz is a coarse signal.** One or two items per concept flag a concept;
  they do not measure it. Findings are phrased as flags ("transfer on recursion looks
  weak — 31% correct on the one transfer item"), never as measurements ("the class
  has not mastered recursion").

## 2. No prediction, no tracking — the rationale

This skill describes current evidence; it never forecasts an individual student's
future and never produces ability labels that become tracks. The reasons, cited
honestly:

- **Expectation effects.** Teacher expectations can become self-fulfilling (Rosenthal
  & Jacobson, 1968). The effect's *size* is contested — replications and reviews find
  it smaller and more conditional than the legend (Jussim & Harber, 2005) — but the
  risk is asymmetric: a "low-ability" label costs the student if expectations bite
  even weakly, and the label provides no teaching benefit that an unlabeled aggregate
  finding doesn't already provide.
- **Label permanence.** A prediction written down outlives its evidence. A week-0
  snapshot stored as "weak student" follows a person past the point where it was ever
  true — which is why no individual-level fact enters the passport or any state file
  (§5), and why even cohort findings carry their instrument and date.
- **Tracking-harm evidence.** Between-class ability tracking shows, at best, no
  aggregate benefit and documented costs to students placed in low tracks (reduced
  expectations, weaker instruction, near-zero upward mobility between tracks); the
  literature is genuinely contested on magnitude and conditions (Slavin, 1990;
  later reviews find small effects for some forms of grouping). What is *not*
  contested: flexible, temporary, task-specific grouping avoids the documented harms
  while keeping the benefits — which is exactly what `grouping_strategist_agent` is
  constrained to produce (rotation, no public ability ranking, no persistent tiers).

Operationally: a "risk score," "predicted grade," "likely to fail" flag, or a
persistent ability tier is refused in every mode. The honest version of the request
is a current-evidence finding plus a professor-initiated `student-mentor` follow-up.

## 3. Self-report calibration limits

Self-reported ability is not measured ability, and the gap is systematic, not
random: novices over-rate themselves — the Kruger & Dunning (1999) pattern. (Parts
of the original statistical story are contested — regression and better-than-average
artifacts account for some of it — but the operational conclusion survives: the
students least prepared are least able to report it.) Therefore:

- Confidence/self-efficacy items appear in their own labeled section of every report
  and every passport entry; they are never merged into readiness findings.
- The usable signals: *change* in cohort confidence across the term, and the
  *calibration gap* where the same concept has both a measured item and a confidence
  item (high confidence + weak performance = the cohort doesn't know what it doesn't
  know — a real teaching finding, at cohort level).
- "Rate your programming ability 1–5" is not evidence of programming ability. "Have
  you written a program of more than 100 lines?" is evidence of exposure. Prefer
  checkable facts over self-ratings at design time (diagnostic_designer rule).

## 4. Small-N and response-rate rules

| Condition | Treatment |
|-----------|-----------|
| Respondents N < 10 | Narrative findings only; no percentages in the report body ("4 of 7 respondents" reads honestly; "57%" does not) |
| 10 ≤ N < 30 | Counts and percentages shown together; distribution shapes labeled tentatively ("looks bimodal — N too small to be sure") |
| N ≥ 30 | Full treatment; shifts across instruments still described in counts before percentages |
| Response rate < ~70% | Every aggregate carries "respondents only"; the non-respondent note (below) is mandatory |

**Non-respondents are not random.** The known pattern in course-survey and
diagnostic data: non-response skews toward disengaged and struggling students — the
end of the distribution the diagnostic most concerns. A 60%-response diagnostic
showing "the cohort is well prepared" is best read as "the prepared majority of
respondents is well prepared." Reports state this; they never quietly extrapolate
respondent aggregates to the whole class.

## 5. The privacy architecture, operationally

The unit of analysis is the cohort. Concretely:

**May be written to the passport** (and only after the professor confirms the
verbatim block at a checkpoint):

- `learner_profile.cohort_evidence[]` — instrument, date, N, enrollment, response
  rate, key aggregates (distributions, prevalence percentages, heterogeneity
  measures), self-report items flagged as such.
- `learner_profile.known_difficulties[]` — evidence-tagged cohort entries:
  `"Confuses X with Y — 41% chose the X distractor with confident reasoning (W0
  diagnostic, 2026-02-24, N=52)"`. The schema allows additional fields; these are
  the only ones this skill uses.

**May never be written to the passport or any state file:** names, IDs, pseudonym
mappings, per-student rows, per-student scores, any fact phrased about an individual,
any subgroup small enough to identify one (§7). The passport is about the course, not
individuals — the same Iron Rule `student-mentor` runs under.

**Pseudonymization procedure:** before analysis, identifiable rows get session
pseudonyms (S01, S02, …) in row order or shuffled; the mapping is stated once to the
professor and kept by them, outside any artifact. Grouping plans and any in-session
working notes use pseudonyms only.

**Data minimization checklist** (run at every intake):

- [ ] Asked only for the columns the analysis plan needs?
- [ ] Suggested the professor strip names/IDs before sharing the file at all?
- [ ] Confirmed the raw file stays in the professor's storage — nothing copied into
      session artifacts?
- [ ] Confirmed no individual-level question is pending? (If one is, route it to
      `student-mentor` now, not after the analysis tempts everyone.)

## 6. Learning styles: the refusal note

Requests to group, differentiate, or design "for visual/auditory/kinesthetic
learners" (or any style typology) are declined with one line and an alternative:
matching instruction to diagnosed learning styles lacks supporting evidence — the
definitive review found no adequate test of the matching claim that succeeded
(Pashler, McDaniel, Rohrer & Bjork, 2008). Differentiate on **prior knowledge**
instead, which has evidence (expertise-reversal effect, Pedagogy Foundations §9) and
is what this skill's instruments actually measure. Multiple representations for
*everyone* is good practice (UDL, Pedagogy Foundations §7); sorting students by
modality is not.

## 7. Aggregation rules

- **Minimum cell size ~5.** No subgroup statistic is reported from fewer than ~5
  respondents — below that, a "subgroup finding" is a list of identifiable people
  wearing a percentage. Suppress the cell and say why.
- **No identifying intersections.** Cross-tabulations (e.g., background × score band)
  are checked against the cell minimum per cell, not per table.
- Percentages always carry their denominator and its definition (respondents, not
  enrolled).
- Distribution before mean, in every table; a mean without spread is not reported.
- Aggregates are dated and instrument-tagged everywhere they travel — a finding
  separated from its provenance becomes a "fact about the class," which is exactly
  the promotion this file exists to prevent.
