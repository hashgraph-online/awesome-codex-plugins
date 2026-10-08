# Final-Grade Analysis — {{course_code}}: {{course_title}}

**Components & weights:** {{from assessment_plan — id, title, weight%; weights sum to 100}}
**Cohort:** N = {{N}} with all components · {{n_incomplete}} excluded (missing a component, counted separately, not imputed)
**Final-grade formula:** {{weighted sum shown — e.g. "0.25·A1 + 0.20·A2 + 0.30·A3 + 0.25·A4"}}

> **Reading this report honestly:** This describes the **cohort's** grade distribution on
> one gradebook close — aggregates only, no student named. It shows you what setting a
> cutoff or curve *does*; it does not set one. {{#if small_N}}N = {{N}} (< 30): shape is
> indicative only — describe the spread, do not over-read clusters or gaps (sampling
> noise at this size).{{/if}} Per-band cells below ~5 move with one student. The cutoff
> and curve decisions are yours.

## Final-grade distribution

{{Histogram of weighted finals by band — counts, distribution sketch. Show the shape, not
just a mean.}}

| Band | Count | Sketch |
|------|-------|--------|
{{rows — e.g. "[90–100] | 12 | ▰▰▰▰▰▰▱▱▱▱"; precision the data supports, no decimal theater}}

**Mean / median / spread:** {{to supported precision}}
**Shape diagnosis:** {{roughly normal / bimodal / skewed / ceiling-floor — per
references/grade_analysis_guide.md, with the teaching/fairness reading; e.g. "bimodal:
clusters at ~62 and ~88, valley at 70–78 — split cohort, NOT a curving target"}}
**Clusters & gaps:** {{empty ranges and pile-ups; flag any pile-up near a candidate cutoff
— "9 students at 78.x–79.x sit just below a 80 B/A-… line"}}

## What-if cutoff comparator *(options, NOT a decision)*

For each boundary you are weighing, how many students sit in each band and how many move:

| Boundary | Option A | → count | Option B | → count | Students between (count) |
|----------|----------|---------|----------|---------|--------------------------|
{{rows — e.g. "B/A line | 90 | 12 As | 88 | 19 As | 7 (at 88.0–89.4)"; counts only, never names}}

**Near-cutoff fairness note:** {{where a line splits near-identical work; the pile-up that
needs a defensible rationale — natural gap or pre-stated policy, not a round number}}

## What-if curve comparator *(options, NOT a decision)*

Each method side by side with who-moves counts and the tradeoff it carries:

| Method | Effect | Students who move | Tradeoff (whom it helps / leaves) |
|--------|--------|-------------------|-----------------------------------|
{{rows — linear shift / top-anchor scale / flexible cutoffs / drop-lowest / norm-referenced,
per the guide; each with its named tradeoff. No curve is free; none is "recommended".}}

## Fairness & consistency note

{{What could make the same work earn different grades: a heavily-weighted component with a
near-cutoff pile-up; a component whose distribution looks mis-scaled (compressing the
whole final); a curve that helps the top and not the borderline. Criterion-referenced vs
norm-referenced stance stated where a norm-referenced curve is on the table (flag, per
guide).}}

## Proposed passport write-back *(AGGREGATES ONLY — after 🧑 confirmation)*

{{Aggregate evidence line for the Stage-6 loop, handed to iteration_coach — NOT written
here directly. Distribution shape + any pile-up/fairness finding. NO per-student rows, NO
names, NO pseudonyms (PII lint; cohort_analyst privacy mirror).}}

> Example: "A4 final grades: bimodal (clusters ~62/~88); 9-student pile-up at 78–79 just
> below the B/A line — review prerequisite gap and that boundary next term."

---

> ⚠️ **Verify before posting grades (non-removable):** This report shows the consequences
> of cutoff and curve choices on the cohort distribution — it does **not** assign grades.
> Confirm the components and weights match your gradebook, choose the cutoff/curve rule
> yourself (and before this report named who it helps), and check that the same final
> score earns the same grade across every student, with any exception being stated policy.
> The grades, and the rule that sets them, are yours. *(This block is not removable.)*

*🧑 Checkpoint: report reviewed; cutoff/curve is the professor's decision; aggregate-only
write-back confirmed verbatim before any passport write (`ts/shared/checkpoint_protocol.md`).*
