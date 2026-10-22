# Synthetic Data Patterns

Working pattern library for `dataset_smith_agent` and the `variant` mode. The governing
rule for every pattern: a planted property exists only if the *intended analysis,
actually executed on the generated data,* recovers it. Generation without recoverability
verification is fabrication with extra steps.

## Planted-effect designs

| Pattern | What you plant | Calibration knobs | Recoverability check |
|---------|----------------|-------------------|----------------------|
| Group difference | Mean shift between groups at a chosen effect size (Cohen's d) | d, group n, within-group SD | Intended test (t/Mann-Whitney) significant at the level the lab expects; estimated d within tolerance of planted d |
| Regression slope | True β on the predictor(s) of interest, noise σ calibrated to a target R² | β, σ (back-solve from target R² and predictor variance), n | Fitted CI contains planted β; achieved R² within band of target |
| Time series | Trend + seasonality + noise (+ optional changepoint) | Trend slope, seasonal amplitude/period, noise SD, changepoint location | Decomposition/fit recovers trend sign and magnitude; changepoint detected within k steps if planted |
| Categorical association | Contingency structure with chosen Cramér's V / odds ratio | Marginals, association strength, n | χ²/Fisher significant as intended; estimated association within tolerance |
| Outliers / influential points | Points placed to be detectable by the taught diagnostic (leverage, Cook's d, IQR rule) | How many, how far, on which variables | The taught diagnostic flags exactly the planted points — no more, no fewer |
| Distribution for goodness-of-fit | Samples from the target distribution (or a deliberate mismatch students must detect) | Distribution, parameters, n | GoF test passes for true fits and fails for planted mismatches at the lab's α |

Composite labs plant several properties in one dataset; verify each independently and
verify they don't interact (a planted outlier can destroy a planted slope — check the
slope *with* the outlier handling the lab teaches, since that's the path students take).

**Power honesty:** choose n and effect size so the intended analysis has high power
(≥ .9) for the planted effect — students should fail by doing the analysis wrong, not by
drawing an unlucky sample. If the lab's *point* is power or null results, plant that
deliberately and say so in ground truth.

## Seeding and per-student variation

- **id → seed mapping**: `seed = H(course_salt + student_id)` with a stable hash;
  mapping and salt documented in `ground_truth.md` only. The professor can regenerate
  any student's exact dataset on demand — essential for grading disputes and defense
  sampling (`ts/shared/ai_era_integrity.md` patterns 3 and 5).
- **What may jitter** (difficulty-preserving): noise realizations, nuisance-parameter
  values within stated ranges, group labels/orderings, cover-story surface values
  (site names, dates), sample composition at fixed n.
- **Jitter ranges preserve difficulty** when: effect detectability stays constant
  (plant the same effect size, not the same raw coefficient, when variances jitter),
  the same diagnostic finds the same planted traps, and no variant crosses a decision
  boundary others don't (e.g., one student's p = .04 vs another's p = .2 on the same
  question is a fairness defect unless the lab is explicitly about sampling
  variability — in which case all students get that experience by design).
- **Per-section variants** (coarser than per-student) use the same machinery with one
  seed per section; cheaper to verify exhaustively.

## What NOT to vary across students

Anything that changes the **required method** or the **work's difficulty class**:

- The analysis the data demands (one student's variant needing a transformation others
  don't = different labs).
- The presence/absence/type of planted traps — every variant has the same confound to
  find, with different surface values.
- Data size by more than a constant factor; missingness *rate* (pattern surface may
  vary); the number of steps to the answer.
- The submission contract or deliverables — variation lives in the data, never in what
  students are asked to do.

## Recoverability verification procedure

1. Generate with the production seed(s).
2. Run the **intended analysis** — the one the handout asks for, at the course's taught
   level, not a stronger method.
3. Check each planted value against its recovery criterion (table above); record
   planted vs recovered, the command, and the date in the verification record.
4. For variants: verify all if N is small; otherwise a stated random sample plus the
   extremes of every jitter range. Then `solution_verifier_agent` independently re-runs
   the analysis on its sample without knowing the planted values — agreement closes
   the loop.
5. Any failure → regenerate with adjusted calibration. Never widen the recovery
   criterion to make a failure pass; that redefines success to fit the defect.

## Realism details

- **Units and magnitudes** from the discipline: reaction times in ms, not seconds with
  six decimals; concentrations in plausible ranges with instrument-realistic rounding.
- **Rounding/precision** to what the cover-story instrument would report — over-precise
  synthetic data is the most common tell, and it teaches bad reporting habits.
- **Missingness** matching how such data actually goes missing (dropout late in
  longitudinal series, sensor gaps in bursts, nonresponse correlated with a covariate
  when the lab teaches MAR/MNAR) — at a rate the taught handling can absorb.
- **ID columns, timestamps, categorical labels** that look like the discipline's real
  exports; no `var1, var2, var3` unless anonymized data is the point.
- **The synthetic label**: when the handout frames data as real-world measurement, the
  data card says "simulated, modeled on <kind of study>". Realism is for practicing
  data hygiene, never for deceiving students about provenance (skill iron rule 6).

## Traps: deliberate vs accidental

**Plant deliberately** (record in ground truth; ensure the handout's task actually
prompts the check that finds them):

- A confound the lab asks students to detect (lurking variable driving a spurious
  effect, resolved by stratification/partial correlation the course taught).
- An influential point that flips a conclusion if not diagnosed.
- A unit inconsistency or duplicated rows when data cleaning is an outcome.

**Audit out accidentally** (run these checks on every generated dataset):

- Spurious significant relationships among filler columns that a reasonable student
  could report as a finding — and be marked wrong for doing the analysis right.
- Unintended outliers from unbounded noise distributions (truncate or re-seed).
- Quasi-identifiers: synthetic "student-like" or "patient-like" records realistic
  enough to be mistaken for real people — keep cover stories plainly fictional.
- An easier shortcut to the planted answer than the intended method (e.g., the answer
  visible in a group-by mean when the lab wants a model) — unless the shortcut is a
  legitimate alternative the grading notes accept.
