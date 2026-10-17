---
name: statistical-tools
type: reference
parent_skill: dmaic
author: RBraga01
version: "1.0"
status: approved
created: "2026-06-06"
last_updated: "2026-06-06"
updated_by: migmcc
reviewed_by: RBraga01
license: MIT
---

# Statistical Tools Reference — DMAIC

Tool selection, assumptions, sample size requirements, and software equivalents for DMAIC statistical analysis.
Use alongside the [dmaic](../SKILL.md) skill.

> **Scope:** This document covers the statistical tool reference by DMAIC phase, hypothesis testing assumptions and sample size requirements, MSA requirements before capability studies, Minitab and Excel equivalents for key tests, and the distinction between statistical and practical significance. For the DMAIC phase workflow, gate criteria, and project charter structure, see [dmaic SKILL.md](../SKILL.md).

---

## Tool Reference by DMAIC Phase

### Define Phase Tools

| Tool | Purpose | When to use | Key output |
|---|---|---|---|
| SIPOC | Map Suppliers-Inputs-Process-Outputs-Customers at high level | Always in Define; scopes the process before detailed mapping | Bounded process scope; identified input variables (Xs) and output (Y) |
| Project charter | Document problem, goal, scope, team, business case | Always; the project anchor document | Agreed measurable goal; Champion approval |
| Is/Is-Not | Scope the problem precisely; eliminate hypotheses | When defect is intermittent, batch-specific, or location-specific | Bounded problem scope; eliminated hypotheses |
| VOC → CTQ | Translate customer requirement to measurable characteristic | Always; links project Y to customer value | CTQ definition with specification limits |
| Pareto chart | Identify the vital few defect types or sources | When multiple defect types exist and resource is limited | Ranked contribution of defect categories; identifies where to focus |

### Measure Phase Tools

| Tool | Purpose | When to use | Key output |
|---|---|---|---|
| Gauge R&R (crossed) | Quantify measurement system variation (repeatability + reproducibility) | Before collecting baseline data on any continuous CTQ | %GRR, %Part variation, ndc; accept/reject/improve decision |
| Attribute Agreement Analysis | Assess consistency of attribute (pass/fail, visual) judgements | When CTQ is an attribute characteristic | Kappa statistic; agreement % within and between appraisers |
| Process capability (Cpk, Ppk) | Quantify how well the process meets specification | After MSA passes; with minimum 100 consecutive parts | Cpk, Ppk, PPM estimate; confirmed baseline |
| Control chart (I-MR or Xbar-R) | Assess process stability before capability | Before calculating Cpk — capability is only meaningful for a stable process | Control limits; evidence of statistical control or special causes |
| Multi-Vari chart | Categorise dominant family of variation: positional, cyclical, or temporal | When variation source is unknown; efficient first investigation | Identifies whether to look for positional, part-to-part, or time effects |
| Data collection plan | Define what, how, when, how many to measure | Always before collecting data | Measurement plan with sampling strategy and sample sizes |

### Analyze Phase Tools

| Tool | Purpose | When to use | Key output |
|---|---|---|---|
| Fishbone / Ishikawa | Brainstorm all potential causes across 6M | Always; prevents tunnel vision | Categorised cause list for hypothesis testing |
| 5-Why | Trace a confirmed cause to its systemic root cause | After hypothesis confirmed by data | Systemic root cause with evidence chain |
| Hypothesis test — 2-sample t-test | Compare means of two independent groups | Comparing Shift A vs Shift B; Machine 1 vs Machine 2 | p-value; confidence interval for difference in means |
| Hypothesis test — Paired t-test | Compare two measurements on same sample (before/after, two methods) | Before/after comparison on same parts; gauge comparison | p-value; confidence interval for mean difference |
| Hypothesis test — ANOVA (one-way) | Compare means of three or more groups | Comparing 3+ machines, operators, suppliers, or shifts | p-value; identification of which groups differ (Tukey post-hoc) |
| Hypothesis test — Chi-square | Test association between two categorical variables | Defect type vs. shift; defect vs. supplier; pass/fail vs. line | p-value; observed vs. expected frequency table |
| Correlation (Pearson) | Quantify linear relationship between two continuous variables | When you suspect X and Y move together | Correlation coefficient r; p-value |
| Simple linear regression | Quantify and model the relationship between one X and one Y | When correlation is confirmed and you need the equation Y = f(X) | Regression equation; R²; prediction capability |
| Multiple regression | Model Y as a function of multiple Xs simultaneously | When several Xs are suspected and you need relative contribution | Regression coefficients; R²; residual analysis |
| Box plot | Visualise distribution differences between groups | Comparing groups visually before or alongside hypothesis testing | Visual identification of median, spread, and outliers by group |
| Scatter plot | Explore relationship between two continuous variables | Before correlation or regression | Visual pattern; outlier identification |
| Normal probability plot | Test whether data follows normal distribution (required for many tests) | Before using t-test, ANOVA, or Cpk (which assume normality) | p-value for normality test (Anderson-Darling); visual fit |

### Improve Phase Tools

| Tool | Purpose | When to use | Key output |
|---|---|---|---|
| Solution matrix (impact/effort/risk) | Evaluate and prioritise candidate solutions | When multiple solutions exist; avoids opinion-driven selection | Ranked solution list with scoring rationale |
| Full factorial DOE | Test all combinations of factor levels to find optimal settings | When 2–5 factors, each at 2 levels; effects and interactions needed | Main effects; interaction plots; optimal factor settings |
| Fractional factorial DOE | Screen many factors to identify vital few | When 5+ factors; screening phase before optimisation | Main effects; fractional resolution; directions for full factorial |
| OFAT (One Factor At A Time) | Vary one factor at a time; simple improvement | When only one suspected factor; confirmatory test | Before/after comparison for that factor |
| Pilot confirmation test | Validate solution under production conditions | After DOE identifies optimal settings; before full deployment | Cpk at optimal settings; production-representative validation |
| Mistake-proofing (Poka-yoke) | Eliminate error through physical or design prevention | When root cause is human error or process ambiguity | Error-proofing device, fixture, or system |

### Control Phase Tools

| Tool | Purpose | When to use | Key output |
|---|---|---|---|
| Control chart — I-MR | Monitor individual measurements over time; detect special causes | Low-volume production; destructive testing; one measurement per sample | Control limits; out-of-control signals (Western Electric rules) |
| Control chart — Xbar-R | Monitor subgroup averages and ranges | Moderate volume; can form rational subgroups of 2–5 | Control limits for average and range; process stability |
| Control chart — Xbar-S | Monitor subgroup averages and standard deviations | Subgroup size > 8; better estimate of within-subgroup variation | Control limits; more efficient than R for large subgroups |
| Control chart — p-chart | Monitor proportion defective per subgroup | Attribute data; variable subgroup size | Control limits for proportion defective |
| Control chart — c-chart | Monitor count of defects per unit | Count of defects on a fixed-area or fixed-unit basis | Control limits for defect count |
| Control plan update | Document new controls: what to measure, frequency, reaction plan | Always; every DMAIC project must close with an updated Control Plan | Revised Control Plan with new Xs and Y controls |
| PFMEA update | Reflect new failure modes and controls discovered in project | Always; new controls from Improve must appear in PFMEA | Updated S/O/D ratings; new current controls column entries |

---

## Hypothesis Testing — Assumptions and Sample Size Requirements

### Choosing the right test

```
Data type of Y?
├── Continuous
│   ├── Comparing to a reference value → 1-sample t-test
│   ├── Comparing 2 groups (independent) → 2-sample t-test
│   ├── Comparing 2 measurements on same sample → Paired t-test
│   └── Comparing 3+ groups → One-way ANOVA
│       └── If data is non-normal and n < 30 per group → Kruskal-Wallis
└── Attribute (counts / categories)
    ├── Association between two categorical variables → Chi-square
    ├── Comparing 2 proportions → 2-proportion z-test
    └── Comparing 3+ proportions → Chi-square or logistic regression
```

### Assumptions and what to do when violated

| Test | Assumptions | Check how | If violated |
|---|---|---|---|
| 2-sample t-test | Normality (or n ≥ 30); independence of samples | Anderson-Darling test; Normal probability plot | n < 30 and non-normal → Mann-Whitney U (non-parametric) |
| Paired t-test | Normality of differences; pairs are independent | Histogram and Normal probability plot of differences | Non-normal differences → Wilcoxon signed-rank test |
| One-way ANOVA | Normality within groups; equal variances; independence | Bartlett's test (equal variances); AD test per group | Unequal variances → Welch's ANOVA; non-normal small n → Kruskal-Wallis |
| Chi-square | Expected frequency ≥ 5 in each cell | Inspect contingency table | Low expected counts → Fisher's exact test |
| Pearson correlation | Both variables continuous; linear relationship; no outliers | Scatter plot; normality check | Non-linear → Spearman rank correlation |
| Regression | Linearity; independence of residuals; normality of residuals; homoscedasticity | Residual plots (4-in-1) | Non-linearity → transform Y or X; heteroscedasticity → weighted regression |

### Sample size requirements

| Test | Minimum practical sample | Notes |
|---|---|---|
| 2-sample t-test | 30 per group (60 total) | For detecting a medium effect (d = 0.5) at α = 0.05, power = 0.80 — use power calculator for specific effect size |
| Paired t-test | 30 pairs | Pairs reduce required n vs. 2-sample; use power calculator with expected difference and σ of differences |
| One-way ANOVA | 30 per group | Increases with number of groups; power drops if groups are unequal size |
| Chi-square | All cells expected count ≥ 5 | Total n depends on proportion differences; minimum ~50–100 for 2×2 table |
| Process capability (Cpk) | 100 consecutive units minimum | 30 is the textbook minimum; 100 recommended for confidence interval on Cpk to be narrow enough for decision-making |
| Gauge R&R (crossed) | 10 parts × 3 operators × 2 replicates = 60 measurements minimum | Parts must represent the full range of production variation — not just "good" parts |
| Attribute Agreement Analysis | 50 samples per appraiser × minimum 2 appraisers | Samples must include a representative mix of clear passes, clear fails, and marginal cases |

**General rule for power calculation:**
Before starting data collection, define: expected effect size (what difference matters practically?), acceptable α (typically 0.05), and desired power (typically 0.80). Run a power calculation in Minitab (Stat > Power and Sample Size) or use an online power calculator. Do not collect data and then ask "did we have enough?"

---

## MSA Requirements Before Capability Study

Running a capability study on a poor measurement system produces false Cpk values. MSA is a prerequisite, not optional.

### Gauge R&R acceptance criteria

| %GRR | Decision |
|---|---|
| < 10% | Acceptable — proceed to capability study |
| 10% – 30% | Conditionally acceptable — document risk; marginal parts near the specification limit may be misclassified; improve if feasible |
| > 30% | Not acceptable — fix the measurement system before collecting capability data; Cpk calculated on this data is unreliable |

**Number of distinct categories (ndc):**
- ndc = 1.41 × (Part-to-Part variation / Gauge R&R)
- Minimum ndc = 5 for a measurement system used for process capability
- ndc < 5 means the gauge cannot distinguish between parts well enough for a meaningful Cpk

### What to fix when GRR fails

| Root cause of high %GRR | Corrective action |
|---|---|
| High reproducibility (operator-to-operator) | Standardise measurement method; add fixture; provide training with verification |
| High repeatability (within operator) | Check gauge calibration and condition; reduce environmental influence on measurement; change measurement method |
| Inadequate parts (all similar, not full production range) | Select 10 parts that span from well below to well above the specification — include marginal parts |
| Sample contains measurement outliers | Investigate and exclude documented special cause; re-run study |

### Capability indices — definitions and decision thresholds

| Index | Formula | What it measures | IATF 16949 minimum |
|---|---|---|---|
| Cp | (USL - LSL) / (6σ) | Potential capability — spread relative to tolerance; ignores centering | 1.67 (new processes); 1.33 (established) |
| Cpk | min[(USL - x̄)/3σ, (x̄ - LSL)/3σ] | Actual capability — accounts for both spread and centering | 1.67 (new); 1.33 (established) |
| Pp | (USL - LSL) / (6s) | Performance index — uses overall standard deviation (includes all sources of variation) | 1.67 (new); 1.33 (established) |
| Ppk | min[(USL - x̄)/3s, (x̄ - LSL)/3s] | Actual performance — overall standard deviation; used with short-term data or unstable processes | Same as Cpk thresholds |

**Cpk vs Ppk:** Cpk uses within-subgroup variation (σ from control chart); Ppk uses overall variation (s from all data). If Cpk >> Ppk, the process has significant between-subgroup variation (shifts, drifts). In DMAIC Measure, report both. In DMAIC Control, Cpk from a stable process is the sustained performance indicator.

**Confidence intervals:** A Cpk of 1.33 calculated from 30 parts has a 95% CI of approximately [1.05, 1.61] — potentially below 1.33 at the lower bound. With 100 parts, the CI narrows to approximately [1.18, 1.48]. This is why 100 parts is the recommended minimum for decision-making.

---

## Minitab and Excel Equivalents

### Measure Phase

| Analysis | Minitab path | Excel equivalent | Notes |
|---|---|---|---|
| Gauge R&R (crossed) | Stat > Quality Tools > Gauge Study > Gauge R&R Study (Crossed) | Not available natively — use ANOVA table manually | Excel cannot compute %GRR components reliably; use Minitab or R |
| Process capability (normal) | Stat > Quality Tools > Capability Analysis > Normal | NORM.DIST function for PPM estimate; no built-in Cpk function | Excel: the formula MIN((USL-AVERAGE(data))/(3*STDEV(data)), (AVERAGE(data)-LSL)/(3*STDEV(data))) uses STDEV() — the overall standard deviation — and therefore computes **Ppk**, not Cpk. For true Cpk, σ̂ must be estimated from within-subgroup variation (R̄/d₂ or S̄/c₄); this requires manual calculation or Minitab. |
| Control chart I-MR | Stat > Control Charts > Variables Charts for Individuals > I-MR | No built-in control chart; manual calculation of UCL/LCL possible | Excel: UCL = x̄ + 2.66 × MR̄; LCL = x̄ - 2.66 × MR̄ |
| Control chart Xbar-R | Stat > Control Charts > Variables Charts for Subgroups > Xbar-R | Manual calculation; A2, D3, D4 constants from table | Minitab preferred for automatic rule detection |
| Normal probability plot | Stat > Basic Statistics > Normality Test (Anderson-Darling) | Insert > Chart > Normal probability plot (limited) | Use Minitab; Excel normal plot requires manual quantile calculation |

### Analyze Phase

| Analysis | Minitab path | Excel equivalent | Notes |
|---|---|---|---|
| 2-sample t-test | Stat > Basic Statistics > 2-Sample t | Data > Data Analysis > t-Test: Two-Sample Assuming Unequal Variances | Check "equal variances" assumption first; Minitab tests it automatically |
| Paired t-test | Stat > Basic Statistics > Paired t | Data > Data Analysis > t-Test: Paired Two Sample for Means | Excel requires manual setup of differences column |
| One-way ANOVA | Stat > ANOVA > One-Way | Data > Data Analysis > ANOVA: Single Factor | Minitab adds Tukey post-hoc automatically; Excel does not |
| Chi-square | Stat > Tables > Chi-Square Test for Association | CHISQ.TEST(actual, expected) with manually constructed table | Excel requires manual contingency table; Minitab builds it from raw data |
| Pearson correlation | Stat > Basic Statistics > Correlation | CORREL(array1, array2); PEARSON(array1, array2) | Same result; Excel does not provide p-value directly — use T.DIST.2T(r*SQRT(n-2)/SQRT(1-r^2), n-2) |
| Simple regression | Stat > Regression > Regression > Fit Regression Model | Data > Data Analysis > Regression | Both provide equation and R²; Minitab provides superior residual diagnostics |
| Multi-Vari chart | Stat > Quality Tools > Multi-Vari Chart | Manual pivot chart construction | No Excel equivalent; use Minitab or R |

### Improve Phase

| Analysis | Minitab path | Excel equivalent | Notes |
|---|---|---|---|
| Full factorial DOE | Stat > DOE > Factorial > Create Factorial Design; then Analyze Factorial Design | Not practical in Excel | Minitab required for DOE; R (FrF2 package) is an alternative |
| Fractional factorial DOE | Same as above; select appropriate resolution | Not practical in Excel | Same recommendation |
| Power and sample size | Stat > Power and Sample Size > [test type] | Not built in; use online calculators | G*Power (free) is an Excel-independent alternative |

---

## Statistical Significance vs Practical Significance

This distinction is critical in DMAIC. Statistical significance answers "Is this effect real (not random noise)?". Practical significance answers "Does this effect matter for the process?".

### The problem

With large sample sizes, even trivial differences become statistically significant. With small sample sizes, practically meaningful differences may not reach significance. The p-value alone is not sufficient for a DMAIC decision.

### Framework for evaluating both

| Question | Tool | What it tells you |
|---|---|---|
| Is the effect statistically real? | p-value from hypothesis test (p < 0.05) | The effect is unlikely to be due to random sampling variation |
| How large is the effect? | Effect size (Cohen's d, η², R²) | The magnitude of the difference or relationship |
| Is the effect large enough to matter? | Compare effect size to CTQ specification or business threshold | Whether the finding will produce a meaningful process or cost improvement |
| What is the range of plausible values? | Confidence interval | The precision of the estimate; narrow CI = higher data quality |

### Effect size interpretation (Cohen's conventions)

| Metric | Small | Medium | Large |
|---|---|---|---|
| Cohen's d (t-test) | 0.2 | 0.5 | 0.8 |
| η² (ANOVA) | 0.01 | 0.06 | 0.14 |
| R² (regression) | 0.01 | 0.09 | 0.25 |

These thresholds are conventions, not rules. In manufacturing, a "small" effect may be practically significant if the CTQ tolerance is tight. Define your practical significance threshold before data collection.

### Worked example

A DMAIC project tests whether a new coolant formulation reduces surface roughness (Ra) on a CNC milled part. Specification: Ra ≤ 1.6 µm.

- Current process: Ra mean = 1.42 µm, σ = 0.18 µm
- New coolant: Ra mean = 1.38 µm, σ = 0.17 µm
- 2-sample t-test: n = 200 per group; p = 0.003 — **statistically significant**
- Practical significance: Δ mean = 0.04 µm. The process is already well within specification at 1.42 µm. A 0.04 µm reduction does not meaningfully change Cpk or PPM.
- Cohen's d = 0.04 / 0.175 ≈ 0.23 — small effect
- Decision: Statistically significant but NOT practically significant. Do not implement new coolant for this metric alone — cost and change risk are not justified by a 0.04 µm improvement that does not change conformance rate.

### Decision rules for DMAIC

| Result | Action |
|---|---|
| p < 0.05 AND practical effect size exceeds threshold | Confirmed: this X is a key driver; include in solution |
| p < 0.05 AND practical effect size below threshold | Statistically real but not worth acting on; document and move on |
| p ≥ 0.05 AND practical effect size large | Likely underpowered; collect more data; do not dismiss the X |
| p ≥ 0.05 AND practical effect size small | Confirmed non-significant; eliminate this X from the model |

**Never present a p-value in a DMAIC tollgate without also presenting the effect size and confidence interval.** A p-value without context misleads stakeholders and sponsors.
