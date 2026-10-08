# Grade Analysis Guide

Working reference for `grade_analyst_agent` and professors reviewing its reports. Closing
a gradebook is a decision the professor owns; this guide makes the decision *informed* —
it describes distribution shapes, the ethics of setting cutoffs, curving methods and what
each one trades, and the small-N caveats that keep the report honest. Nothing here sets a
grade.

## Reading the distribution: shapes and what they mean

A final-grade distribution is read for *shape* before any cutoff is drawn. The shape is a
teaching and fairness signal, not a curving target.

| Shape | What it looks like | What it often means | What it is NOT |
|-------|-------------------|---------------------|----------------|
| **Roughly normal** | single hump, tapering tails | a spread of mastery on a well-calibrated assessment | proof the grading was "right" |
| **Bimodal** | two clusters with a valley between | a split cohort — prerequisite gap, two prep levels, or a component that split the class | a mandate to curve the lower cluster up |
| **Skewed high / ceiling** | pile-up at the top, short upper tail | assessment too easy to discriminate, or genuine mastery | a reason to manufacture spread by curving down |
| **Skewed low / floor** | pile-up at the bottom | assessment too hard, misaligned, or a teaching gap (Pedagogy Foundations §2) | a student-quality verdict — check the instrument first |
| **Cliffs / gaps** | empty score ranges | natural cluster boundaries — sometimes a *humane* place to put a cutoff | meaningful if N is small (gaps are sampling noise then) |
| **Cutoff pile-up** | many students at e.g. 79.x | a fairness problem in waiting — the cutoff line splits near-identical work | something to hide by rounding silently |

**Bimodality is the highest-value finding.** A mean of 75 hides whether the class is
uniformly at 75 or split 60/90 — utterly different teaching stories, and a curve that
"fixes" the mean can be unjust to both clusters. Name the shape; never let a single number
stand in for it.

## The ethics of setting cutoffs

The cutoff decision is the professor's. The agent's job is to make its consequences
visible and its fairness traps obvious — never to recommend a line.

1. **Criterion-referenced is the default stance.** A grade should mean *this student
   demonstrated this level of mastery of the outcomes* — an absolute standard set before
   grades are seen, not a rank. Norm-referenced grading (grade-on-a-curve to a fixed
   distribution) converts learning into competition and is hard to defend on fairness
   grounds; flag it when a professor asks for it, then comply if confirmed.
2. **Near-cutoff equity.** Work at 89.4 and 90.1 is essentially the same work; a hard line
   between them needs a defensible rationale (a natural gap, a pre-stated policy), not an
   arbitrary round number. Surface every pile-up near a candidate line — this is the most
   common source of a defensible grade dispute.
3. **Set the rule before seeing who it helps.** Choosing a cutoff *to move a specific
   named student* is the bias the whole exercise should prevent. The comparator shows
   counts and bands, never names, precisely so the line is set on the distribution, not on
   individuals.
4. **Consistency across the cohort.** The same final score earns the same grade; any
   exception (a documented late-accommodation, an incomplete) is a stated policy, not an
   ad hoc adjustment at the boundary.
5. **Transparency.** Whatever rule is set, students should be able to see it. A cutoff or
   curve the professor can state plainly is one they can defend.

## Curving methods and their fairness tradeoffs

"Curving" names several different operations with very different fairness profiles. The
comparator shows each side by side with who-moves counts; this table names what each one
*costs*.

| Method | What it does | Helps | Tradeoff / who it leaves |
|--------|-------------|-------|--------------------------|
| **Linear shift (add N points)** | every score +N | everyone equally; preserves rank and gaps | can push a ceiling cluster past 100; does nothing for a *spread* problem |
| **Scale to a top anchor** | multiply so the top score (or a chosen anchor) maps to 100 | the whole class proportionally; rewards relative performance | amplifies gaps — strong students gain more points than weak ones; sensitive to one outlier top score |
| **Flexible cutoffs (move the lines, not the scores)** | lower band boundaries | students just under each line | leaves the *distances* intact; a pile-up just below the new line recreates the same problem |
| **Drop-lowest / best-of** | discard a component or item per a pre-stated policy | students hurt by one bad component | only fair if announced in advance; retroactive use is inconsistent |
| **Norm-referenced (fixed quotas)** | force a set % into each grade | nobody — it caps how many can succeed | converts an absolute standard into a rank; hardest to defend; flag before applying |

**No curve is free.** Every method that helps one part of the distribution does nothing —
or less — for another. The agent names the tradeoff for each; the professor weighs it.
A "fair" curve is one whose rule was set before grades were seen and applies to everyone
the same way.

## Small-N caveats

- **N < 30:** distribution *shape* is unstable — a "bimodal" or "gap" may be sampling
  noise. Label the whole report "indicative only, N=<n>"; describe the spread, don't
  over-interpret the shape.
- **Per-band cells < ~5:** do not report a sub-band count as if precise; small cells move
  with one student.
- **No decimal-point theater.** A mean of 74.83 on N=22 is false precision; report to the
  precision the data supports.
- **Incompletes and missing components** are counted separately and excluded from shape —
  never imputed. State how many there are.

## What the report writes back

Only aggregates: distribution shape, band counts, who-moves *tallies* per candidate
cutoff, and any pile-up/fairness finding. **Never** a per-student row, name, or pseudonym
in `iteration_history`. Per-student matters (a borderline case, a regrade) route to
`student-mentor`, initiated by the professor with the evidence they hold. The mirror is
exact: this skill describes the cohort's grades, never a student's.
