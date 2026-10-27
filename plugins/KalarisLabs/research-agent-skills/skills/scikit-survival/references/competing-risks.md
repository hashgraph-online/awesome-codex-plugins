# Competing risks and cumulative incidence

Verified for scikit-survival 0.28.0 on 2026-07-23.

## Estimand

Competing risks are mutually exclusive causes \(J \in \{1,\ldots,K\}\), where the
first observed cause prevents observing the others as first events.

The cause-\(k\) cumulative incidence function (CIF) is:

\[
F_k(t) = P(T \le t, J=k).
\]

It is an absolute cause-specific event probability accounting for all competing
causes. It is not:

- a cause-specific hazard;
- `1 - Kaplan-Meier` after censoring other causes;
- a conditional probability among only those still event-free;
- a causal effect or clinical-utility measure.

The total risk is \(\sum_k F_k(t)\). Its complement is estimated all-cause
event-free survival. Censoring is an observation mechanism, not an additional
event-free state.

## Event coding

The nonparametric CIF API takes two separate arrays:

```python
# event: 0=censored; 1..K=mutually exclusive causes
event = frame["status"].to_numpy(dtype=int)
time = frame["time"].to_numpy(dtype=float)
```

Requirements:

- `event` is integer and non-negative;
- 0 always denotes right-censoring;
- positive codes 1..K are contiguous;
- the data contains observations for every code 1..K;
- `time` is finite and positive;
- event/time lengths match.

Do not pass a boolean `Surv` outcome to
`cumulative_incidence_competing_risks()`. `Surv` intentionally collapses event
status to event versus censoring and loses cause identity.

## Nonparametric CIF API

```python
from sksurv.nonparametric import cumulative_incidence_competing_risks

time_points, cumulative_incidence = (
    cumulative_incidence_competing_risks(event, time)
)
```

Current signature:

```text
cumulative_incidence_competing_risks(
    event,
    time_exit,
    time_min=None,
    conf_level=0.95,
    conf_type=None,
    var_type="Aalen",
)
```

Returns:

- `time_points`: shape `(n_times,)`;
- `cumulative_incidence`: shape `(K + 1, n_times)`;
- row 0: total risk of any cause;
- row `k`: CIF for cause `k`.

```python
total_risk = cumulative_incidence[0]
cause_1 = cumulative_incidence[1]
cause_2 = cumulative_incidence[2]

assert np.allclose(
    total_risk,
    cumulative_incidence[1:].sum(axis=0),
)
```

`time_min` estimates conditionally on surviving at least to that time. This changes
the target population and must not be selected after viewing outcomes.

### Confidence intervals

```python
time_points, cumulative_incidence, confidence_interval = (
    cumulative_incidence_competing_risks(
        event,
        time,
        conf_type="log-log",
        conf_level=0.95,
        var_type="Aalen",
    )
)
```

`confidence_interval` has shape `(K + 1, 2, n_times)`, where axis 1 is lower/upper.
Current variance choices are:

- `"Aalen"`
- `"Dinse"`
- `"Dinse_Approx"`

Pointwise confidence intervals are not simultaneous confidence bands. Sparse
causes and late follow-up can make estimates unstable even when the function
returns a result.

## Built-in competing-risk datasets

```python
from sksurv.datasets import load_bmt, load_cgvhd

X_bmt, y_bmt = load_bmt()       # status codes 0, 1, 2
X_cgvhd, y_cgvhd = load_cgvhd() # status codes 0, 1, 2, 3
```

The first structured field is integer cause status, not boolean. These are real
study datasets distributed for examples. The bundled tests do not use them; they
use synthetic non-clinical outcomes only.

## Why `1 - Kaplan-Meier` is wrong for one cause

If cause 2 prevents cause 1, censoring cause 2 in a Kaplan-Meier curve treats those
subjects as if they could still experience cause 1 later under non-informative
censoring. That counterfactual risk set does not estimate the observed-world
probability \(F_1(t)\) and typically overstates cause-1 probability.

Use CIF for cause-specific absolute probability:

```python
time_points, cif = cumulative_incidence_competing_risks(event, time)
probability_cause_1_by_t = cif[1]
```

Kaplan-Meier remains appropriate for all-cause event-free survival after collapsing
all causes to event, if that is the estimand and censoring assumptions hold.

## Comparing groups

Estimate group-specific curves without fitting preprocessing on the full dataset:

```python
curves = {}
for label in prespecified_groups:
    mask = group == label
    curves[label] = cumulative_incidence_competing_risks(
        event[mask],
        time[mask],
        conf_type="log-log",
    )
```

Plotting pointwise intervals does not test equality. scikit-survival 0.28 does not
provide Gray's test in this API. Do not substitute an ordinary log-rank test:
survival and CIF group hypotheses differ.

Group labels and comparison times should be prespecified. Report at-risk/event
support; late visual separation with few rows can be misleading.

## Cause-specific Cox hazards

For cause \(k\), a cause-specific hazard model encodes that cause as an event and
other causes as censored at their occurrence time:

```python
from sksurv.linear_model import CoxPHSurvivalAnalysis
from sksurv.util import Surv

y_cause_1 = Surv.from_arrays(
    event=(event == 1),
    time=time,
)
cause_1_hazard_model = CoxPHSurvivalAnalysis(alpha=0.1)
cause_1_hazard_model.fit(X_train, y_cause_1_train)
```

This estimates association with the instantaneous cause-specific hazard under a
PH model. Other causes are censored for this hazard likelihood, which is different
from pretending they are independent censoring when estimating absolute CIF.

To derive cause-specific CIF predictions from cause-specific hazards, all modeled
causes must be combined:

\[
F_k(t \mid x) =
\int_0^t S(u^- \mid x)\,dH_k(u \mid x),
\quad
S(t \mid x)=\exp\left[-\sum_j H_j(t \mid x)\right].
\]

Therefore, `1 - cause_1_model.predict_survival_function(...)` is not the cause-1
CIF. A set of separately fitted cause-specific models requires careful joint
integration, common time grids, and external validation.

## Fine-Gray regression

scikit-survival 0.28 does not implement Fine-Gray subdistribution-hazard
regression. Do not invent an import or describe `cumulative_incidence_competing_risks`
as Fine-Gray; it is a nonparametric CIF estimator.

If using another implementation:

- verify it is actively maintained and supports the required censoring/truncation;
- use its official API documentation;
- distinguish subdistribution from cause-specific hazard coefficients;
- keep preprocessing and tuning leakage-safe;
- validate cause-specific absolute probabilities, not only coefficients.

Neither hazard parameterization is universally "better." The estimand determines
the method.

## Prediction evaluation

Standard `concordance_index_ipcw`, `cumulative_dynamic_auc`, and Brier APIs in
scikit-survival are documented for right-censored single-event outcomes. A
competing-risk prediction question needs:

- a named cause;
- a case/control definition at each horizon;
- handling of other causes consistent with that definition;
- cause-specific probability predictions for calibration/Brier evaluation;
- censoring weights fitted on training data;
- evaluation times supported by training follow-up;
- nested tuning or an untouched holdout.

Do not label an all-event C-index as cause-specific discrimination, and do not use
an all-event survival probability as a cause-specific CIF.

## Bundled helper

The helper defaults to deterministic synthetic data:

```bash
python skills/scikit-survival/scripts/competing_risk_cif.py
```

For local CSV:

```bash
python skills/scikit-survival/scripts/competing_risk_cif.py \
  --input competing.csv \
  --event-column status \
  --time-column time \
  --horizons 2,5,10 \
  --confidence \
  --curve-output cif-curves.npz \
  --output cif-summary.json
```

It:

- rejects URLs, symlinks, missing/non-contiguous causes, and invalid times;
- bounds file size and row count;
- verifies that cause-specific rows sum to total CIF;
- writes numeric arrays without pickle;
- reports point estimates at requested horizons;
- makes no network calls.

Use only authorized, de-identified local data. Do not include row-level data or PHI
in reports.

## Reporting checklist

- cause definitions and code mapping;
- censoring definition and follow-up window;
- CIF versus cause-specific or subdistribution hazard estimand;
- number of rows/events for every cause;
- horizon-specific CIF with uncertainty and support;
- whether intervals are pointwise;
- handling of `time_min`, if any;
- competing-risk-specific prediction evaluation;
- no causal or clinical-utility claim from association/probability alone.

## Sources

Official scikit-survival sources checked 2026-07-23:

- [Competing-risks user guide](https://scikit-survival.readthedocs.io/en/stable/user_guide/competing-risks.html)
- [CIF API](https://scikit-survival.readthedocs.io/en/stable/api/generated/sksurv.nonparametric.cumulative_incidence_competing_risks.html)
- [Dataset API](https://scikit-survival.readthedocs.io/en/stable/api/datasets.html)
- [0.24 release notes introducing CIF](https://scikit-survival.readthedocs.io/en/stable/release_notes/v0.24.html)

Primary methods:

- Aalen O. "Nonparametric estimation of partial transition probabilities in
  multiple decrement models." *Annals of Statistics* 6 (1978), 534-545.
  [Project Euclid record](https://projecteuclid.org/journals/annals-of-statistics/volume-6/issue-3/Nonparametric-Estimation-of-Partial-Transition-Probabilities-in-Multiple-Decrement-Models/10.1214/aos/1176344198.full)
- Gray RJ. "A class of K-sample tests for comparing the cumulative incidence of
  a competing risk." *Annals of Statistics* 16 (1988), 1141-1154.
  [doi:10.1214/aos/1176350951](https://doi.org/10.1214/aos/1176350951)
