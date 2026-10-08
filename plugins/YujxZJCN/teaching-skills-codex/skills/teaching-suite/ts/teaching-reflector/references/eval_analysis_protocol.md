# Evaluation Analysis Protocol

The full procedure `eval_analyst_agent` executes in `eval-analysis` mode (and
`midcourse_agent` in compressed form). The stance throughout is Pedagogy Foundations
§11: evaluations are biased evidence of student experience, not a measurement of
teaching quality. This protocol exists so the analysis is honest *and* useful — the
caveats are load-bearing, and so are the themes.

## 1. Data hygiene

Run before any coding:

1. **De-identification.** Strip student names/IDs from exports. If a comment names a
   third party (TA, another student), replace with role tags ("[TA]") before the
   comment enters the working set.
2. **Abusive-comment filtering policy.** Comments containing personal abuse, or remarks
   on the professor's appearance, accent, gender, ethnicity, age, or other protected
   characteristics are removed from the coding set and reported as:
   `Filtered: N comments — categories: [appearance ×2, gendered language ×1]`.
   They are never quoted in the report. The professor can explicitly request the raw
   view; offer it without pressure either way. Rationale: these comments are documented
   bias channels (§11), not teaching evidence — but their *count* is reportable
   context, especially for personnel-file framing.
3. **Scope check.** Comments about other courses, the department, or the major are set
   aside into the non-actionable pool immediately (still reported — see §5).

## 2. Coding method

1. **Code book emergence (inductive).** Read all comments once without coding. Then
   code: short descriptive labels grounded in the comments' own language ("homework
   solutions posted late," not "feedback issues"). No preloaded theme list — imported
   themes find themselves whether present or not.
2. **Merge threshold.** A code needs ≥2 comments; below that it goes to a `singletons`
   list, retained because a single *specific, checkable* comment ("the W7 dataset link
   is broken") can be worth more than a theme of vague ones.
3. **Double pass.** After the first full pass the code book has drifted — early
   comments were coded against an immature book. Re-pass all comments against the
   stabilized codes; merge near-duplicates, split overloaded codes.
4. **Prevalence counting.** Per code: `n of N comments` (a comment can carry multiple
   codes; say so in the report header). Prevalence is comment counts, never inflated
   to "students" ("11 comments," not "a quarter of the class" — non-responders exist).
5. **Valence.** Tag each code positive / negative / mixed. Mixed codes ("group project:
   loved by 6, logistics complaints from 5") are often the most informative.
6. **Exemplar quotes.** 1–3 per theme, **verbatim** — exact words, typos included, never
   paraphrased toward comfort or coherence. Trim with `[...]` only for length.

## 3. Scalar rules

1. **N thresholds.**

   | Respondents | Treatment |
   |-------------|-----------|
   | N < 10 | Narrative only; no numeric summary in the report body |
   | 10 ≤ N < 30 | Distributions shown; means labeled "directional at best" |
   | N ≥ 30 | Distributions + means; term-to-term shifts < ~0.3 on a 5-pt scale treated as noise |

2. **Response-rate reporting.** First line of the scalar section: N, enrolled, response
   rate. Below ~50% response, add the self-selection note: responders skew toward
   strong opinions in both directions.
3. **Distribution-first.** Every item shows its response spread (a compact histogram
   row is fine). Means without distributions are not reported.
4. **Ordinal honesty.** Where a mean of Likert responses appears, it is labeled as a
   convention applied to ordinal data (Iron Rule 3). One decimal place maximum; never
   two ("4.17" on N=12 is decimal-point theater).
5. **The §11 caveat block — verbatim, opens every scalar section:**

   > **Reading these numbers honestly:** Student evaluation scores correlate weakly
   > with measured learning and carry documented gender and ethnicity biases (Boring
   > et al., 2016; Uttl et al., 2017). They are evidence of student *experience*, not
   > a measurement of teaching quality. At this sample size (N={{N}}, {{rate}}%
   > response), differences of a few tenths of a point are statistical noise.
   > Comparisons across instructors, or across terms with different cohorts, are not
   > supported by this data. The comment themes above are the actionable signal in
   > this report; the numbers below are context.

   The block is not removable by configuration. Comparative-claim requests (vs a
   colleague, vs last term) proceed only after the professor explicitly acknowledges
   the noise floor; log the acknowledgment.

## 4. Triangulation matrix

Each theme gets checked against whatever else exists, and labeled
**corroborated / contradicted / eval-only**. What each evidence type can and cannot
support:

| Evidence | Can support | Cannot support |
|----------|-------------|----------------|
| Eval comments (coded) | What students experienced; specific fixable irritants | That learning did/didn't happen; instructor quality |
| Eval scalars | Broad satisfaction direction at adequate N | Fine comparisons; anything at small N (§3) |
| Grade / item-level distributions | Where performance broke down, by outcome if blueprinted (§2, §10) | *Why* it broke down; experience claims |
| Attendance / LMS engagement | Behavioral corroboration of engagement themes | Causes; learning |
| Peer-observation notes | What observably happened in N sessions | Generalization beyond observed sessions |
| Prior-term evals | Whether a theme is recurring or cohort-specific | Causal credit for changes (cohorts differ) |

Contradictions are reported as tensions, not resolved by the agent: "9 comments code
*pace too fast*; exam items on those weeks' outcomes had the strongest performance —
possible experience/learning split (desirable difficulty?), professor's call."

## 5. Report structure (`eval_analysis_report.md`)

1. **Header** — course, term, N/enrolled/response rate, evidence sources available
2. **Themes** — ordered by prevalence; each with count, valence, exemplar quotes,
   triangulation label
3. **Scalars** — §11 caveat block, then distribution-first item summaries
4. **Actionable / non-actionable split** — actionable themes (specific, within the
   professor's control) feed §6; non-actionable (workload-of-major, facilities,
   "shouldn't be required") are listed with a routing note (acknowledge in class /
   forward to department / no action), never silently dropped
5. **Filtered-comment count + categories** (per §1.2)
6. **Prioritized changes** — 2–3, per the rubric below
7. **Passport append block** — changes formatted for `iteration_history` with
   `evidence` fields filled, ready for the professor to confirm at the 🧑 checkpoint

## 6. Changes-prioritization rubric

Score each candidate change **high / medium / low** on three axes — no fake numeric
precision:

- **Impact** — how many students, how central to learning outcomes
- **Effort** — professor hours to implement, honestly estimated
- **Confidence-in-evidence** — triangulation label: corroborated > eval-only >
  contradicted (a contradicted theme can still motivate a change, but the report must
  say the evidence is split)

Recommend 2–3 changes, led by high-impact / low-effort / corroborated. More than three
changes per iteration is a redesign — route to `course-designer` (`redesign` mode reads
this report directly). One protected-list question always accompanies the
recommendations: *what does the evidence say is working and must NOT change?* —
improvement loops that only ever subtract working elements are a known failure mode.
