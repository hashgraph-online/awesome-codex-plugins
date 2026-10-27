---
name: pymc
description: Builds, fits, checks, and compares Bayesian models in Python with PyMC and ArviZ. Covers hierarchical (multilevel) models, NUTS MCMC sampling, variational inference (ADVI), prior and posterior predictive checks, convergence diagnostics (R-hat, ESS, divergences), and LOO/WAIC model comparison. Use when writing a PyMC model for regression, count, or binary data. Use when fitting a hierarchical model with partial pooling. Use when diagnosing divergences, low ESS, or high R-hat. Use when comparing candidate models with LOO. Use when choosing priors or running prior predictive checks. Not for non-Bayesian regression; use statsmodels or scikit-learn instead.
license: Apache License, Version 2.0
compatibility: Requires Python 3.12+ and PyMC 6.0.1-compatible dependencies. Install reproducible environments with `uv pip install "pymc[nutpie]==6.0.1"`; optional NumPyro or BlackJAX samplers require separately pinned JAX-compatible dependencies.
allowed-tools: Read Write Edit Bash
metadata:
  version: '1.4'
  category: data-science-and-ml
  maintainer: Kalaris Labs
  tags: Bayesian statistics, MCMC, probabilistic programming, hierarchical models, statistics
---

# PyMC Bayesian Modeling

## Overview

PyMC is a Python library for Bayesian modeling and probabilistic programming. Build, fit, validate, and compare Bayesian models using PyMC's modern API (version 6.x+), including hierarchical models, MCMC sampling (NUTS), variational inference, posterior predictive checks, and model comparison (LOO, WAIC).

## Current Version and Setup

PyMC 6.0.1 is the current stable release as of June 2026. It requires Python 3.12+, uses PyTensor 3 as the computational graph backend, and defaults to compiled backends such as Numba. For reproducible local environments, pin the version:

```bash
uv pip install "pymc[nutpie]==6.0.1"
```

The `nutpie` extra enables the faster Rust/Numba NUTS implementation. If using NumPyro or BlackJAX, install those optional sampler dependencies in the same environment and pin them in the project lockfile.

## When to Use This Skill

This skill should be used when:
- Building Bayesian models (linear/logistic regression, hierarchical models, time series, etc.)
- Performing MCMC sampling or variational inference
- Conducting prior/posterior predictive checks
- Diagnosing sampling issues (divergences, convergence, ESS)
- Comparing multiple models using information criteria (LOO, WAIC)
- Implementing uncertainty quantification through Bayesian methods
- Working with hierarchical/multilevel data structures
- Handling missing data or measurement error in a principled way

## Standard Bayesian Workflow

Never sample first and check later. The eight-step workflow — documented with code in
[references/standard_workflow.md](references/standard_workflow.md) — is:

1. **Data preparation** — including standardizing predictors so priors are interpretable.
2. **Model building** — priors and likelihood in a `pm.Model` context.
3. **Prior predictive check** — confirm the priors imply plausible data *before* fitting.
4. **Fit model** — `pm.sample()` with an explicit seed.
5. **Check diagnostics** — R-hat, ESS, divergences. Divergences invalidate the fit; fix
   the model or reparameterize rather than raising `target_accept` and hoping.
6. **Posterior predictive check** — does the fitted model reproduce the observed data?
7. **Analyze results** — summaries and intervals from the posterior.
8. **Make predictions** — on new data via `pm.set_data` and posterior predictive sampling.

Reusable model structures and model comparison are in
[references/model_patterns.md](references/model_patterns.md).

## Distribution Selection Guide

### For Priors

**Scale parameters** (σ, τ):
- `pm.HalfNormal('sigma', sigma=1)` - Default choice
- `pm.Exponential('sigma', lam=1)` - Alternative
- `pm.Gamma('sigma', alpha=2, beta=1)` - More informative

**Unbounded parameters**:
- `pm.Normal('theta', mu=0, sigma=1)` - For standardized data
- `pm.StudentT('theta', nu=3, mu=0, sigma=1)` - Robust to outliers

**Positive parameters**:
- `pm.LogNormal('theta', mu=0, sigma=1)`
- `pm.Gamma('theta', alpha=2, beta=1)`

**Probabilities**:
- `pm.Beta('p', alpha=2, beta=2)` - Weakly informative
- `pm.Uniform('p', lower=0, upper=1)` - Non-informative (use sparingly)

**Correlation matrices**:
- `pm.LKJCholeskyCov('chol', n=n_vars, eta=2, sd_dist=pm.HalfNormal.dist(1))` - Preferred covariance prior
- `pm.LKJCorr('corr', n=n_vars, eta=2)` - Correlation-only prior; eta=1 uniform, eta>1 prefers identity

### For Likelihoods

**Continuous outcomes**:
- `pm.Normal('y', mu=mu, sigma=sigma)` - Default for continuous data
- `pm.StudentT('y', nu=nu, mu=mu, sigma=sigma)` - Robust to outliers

**Count data**:
- `pm.Poisson('y', mu=lambda)` - Equidispersed counts
- `pm.NegativeBinomial('y', mu=mu, alpha=alpha)` - Overdispersed counts
- `pm.ZeroInflatedPoisson('y', psi=psi, mu=mu)` - Excess zeros
- `pm.HurdleNegativeBinomial('y', psi=psi, mu=mu, alpha=alpha)` - Excess zeros plus overdispersion

**Binary outcomes**:
- `pm.Bernoulli('y', p=p)` or `pm.Bernoulli('y', logit_p=logit_p)`

**Categorical outcomes**:
- `pm.Categorical('y', p=probs)`

**See:** `references/distributions.md` for comprehensive distribution reference

## Sampling and Inference

### MCMC with NUTS

Default and recommended for most models:

```python
idata = pm.sample(
    draws=2000,
    tune=1000,
    chains=4,
    target_accept=0.9,
    random_seed=42
)
```

**Adjust when needed:**
- Divergences → `target_accept=0.95` or higher
- Slow sampling → Use ADVI for initialization
- Discrete parameters → Use `pm.Metropolis()` for discrete vars

### Variational Inference

Fast approximation for exploration or initialization:

```python
with model:
    approx = pm.fit(n=20000, method='advi')

    # Use for initialization
    initvals = approx.sample(return_inferencedata=False)[0]
    idata = pm.sample(initvals=initvals)
```

**Trade-offs:**
- Much faster than MCMC
- Approximate (may underestimate uncertainty)
- Good for large models or quick exploration

**See:** `references/sampling_inference.md` for detailed sampling guide

## Diagnostic Scripts

### Comprehensive Diagnostics

```python
from scripts.model_diagnostics import create_diagnostic_report

create_diagnostic_report(
    idata,
    var_names=['alpha', 'beta', 'sigma'],
    output_dir='diagnostics/'
)
```

Creates:
- Trace plots
- Rank plots (mixing check)
- Autocorrelation plots
- Energy plots
- Local ESS plots
- Summary statistics CSV

### Quick Diagnostic Check

```python
from scripts.model_diagnostics import check_diagnostics

results = check_diagnostics(idata)
```

Checks R-hat, ESS, divergences, and tree depth.

## Common Issues and Solutions

### Divergences

**Symptom:** `idata.sample_stats.diverging.sum() > 0`

**Solutions:**
1. Increase `target_accept=0.95` or `0.99`
2. Use non-centered parameterization (hierarchical models)
3. Add stronger priors to constrain parameters
4. Check for model misspecification

### Low Effective Sample Size

**Symptom:** `ESS < 400`

**Solutions:**
1. Sample more draws: `draws=5000`
2. Reparameterize to reduce posterior correlation
3. Use QR decomposition for regression with correlated predictors

### High R-hat

**Symptom:** `R-hat > 1.01`

**Solutions:**
1. Run longer chains: `tune=2000, draws=5000`
2. Check for multimodality
3. Improve initialization with ADVI

### Slow Sampling

**Solutions:**
1. Use ADVI initialization
2. Reduce model complexity
3. Increase parallelization: `cores=8, chains=8`
4. Use variational inference if appropriate

## Best Practices

### Model Building

1. **Always standardize predictors** for better sampling
2. **Use weakly informative priors** (not flat)
3. **Use named dimensions** (`dims`) for clarity
4. **Non-centered parameterization** for hierarchical models
5. **Check prior predictive** before fitting

### Sampling

1. **Run multiple chains** (at least 4) for convergence
2. **Use `target_accept=0.9`** as baseline (higher if needed)
3. **Include `log_likelihood=True`** for model comparison
4. **Set random seed** for reproducibility

### Validation

1. **Check diagnostics** before interpretation (R-hat, ESS, divergences)
2. **Posterior predictive check** for model validation
3. **Compare multiple models** when appropriate
4. **Report uncertainty** (HDI intervals, not just point estimates)

### Workflow

1. Start simple, add complexity gradually
2. Prior predictive check → Fit → Diagnostics → Posterior predictive check
3. Iterate on model specification based on checks
4. Document assumptions and prior choices

## Resources

This skill includes:

### References (`references/`)

- **`distributions.md`**: Comprehensive catalog of PyMC distributions organized by category (continuous, discrete, multivariate, mixture, time series). Use when selecting priors or likelihoods.

- **`sampling_inference.md`**: Detailed guide to sampling algorithms (NUTS, Metropolis, SMC), variational inference (ADVI, SVGD), and handling sampling issues. Use when encountering convergence problems or choosing inference methods.

- **`workflows.md`**: Complete workflow examples and code patterns for common model types, data preparation, prior selection, and model validation. Use as a cookbook for standard Bayesian analyses.

### Scripts (`scripts/`)

- **`model_diagnostics.py`**: Automated diagnostic checking and report generation. Functions: `check_diagnostics()` for quick checks, `create_diagnostic_report()` for comprehensive analysis with plots.

- **`model_comparison.py`**: Model comparison utilities built on PSIS-LOO ELPD, the only criterion ArviZ 1.x `compare()` ranks on. Functions: `compare_models()`, `check_loo_reliability()`, `model_averaging()`.

### Templates (`assets/`)

- **`linear_regression_template.py`**: Complete template for Bayesian linear regression with full workflow (data prep, prior checks, fitting, diagnostics, predictions).

- **`hierarchical_model_template.py`**: Complete template for hierarchical/multilevel models with non-centered parameterization and group-level analysis.

## Quick Reference

### Model Building
```python
with pm.Model(coords={'var': names}) as model:
    # Priors
    param = pm.Normal('param', mu=0, sigma=1, dims='var')
    # Likelihood
    y = pm.Normal('y', mu=..., sigma=..., observed=data)
```

### Sampling
```python
idata = pm.sample(draws=2000, tune=1000, chains=4, target_accept=0.9)
```

### Diagnostics
```python
from scripts.model_diagnostics import check_diagnostics
check_diagnostics(idata)
```

### Model Comparison
```python
from scripts.model_comparison import compare_models
compare_models({'m1': idata1, 'm2': idata2}, ic='loo')
```

### Predictions
```python
with model:
    pm.set_data({'X_data': X_new})
    pred = pm.sample_posterior_predictive(idata, predictions=True)
```

## Additional Notes

- PyMC integrates with ArviZ for visualization and diagnostics; PyMC 6 / ArviZ 1 use xarray `DataTree` while retaining familiar groups such as `.posterior` and `.posterior_predictive`
- Use `pm.model_to_graphviz(model)` to visualize model structure
- Save results with `idata.to_netcdf('results.nc')`
- Load with `az.from_netcdf('results.nc')`
- For very large models, consider minibatch ADVI or data subsampling

## Agent operating procedure

1. **Check the environment.** Confirm the Python environment and library versions (`python -c "import pkg; print(pkg.__version__)"`) and inspect the data's shape, types and missing values.
2. **Pin down the inputs.** Confirm formats, identifiers and parameters from the data or the user. Ask rather than guess any value that changes the result.
3. **Run a small version first.** Run on a sample or a single fold first and check runtime and memory.
4. **Execute the full task** using the instructions and references above.
5. **Validate the result.** Use held-out data, fixed random seeds and appropriate metrics; check for leakage; report uncertainty (CIs, std over seeds).
6. **Report.** State what was run (versions, commands, parameters), what was checked, and what is still uncertain.

| If this happens | Do this |
|---|---|
| Out-of-memory or very slow execution | Subsample, use chunked or lazy computation, or reduce model size, and tell the user what changed. |
| A function, flag or endpoint in these instructions is missing in the installed version | Check the installed version's own documentation (`help()`, `--help`, official docs), adapt, and tell the user. Never invent an API. |
| A required input, identifier or parameter is ambiguous | Ask the user, or state the assumption explicitly before running. |

**Integrity rules**

- Never fabricate results, parameters, identifiers, citations or statistics. If something cannot be run or verified, say so plainly.
- Never report a metric you did not compute in this session; show the code path that produced every number.
- Treat version-specific details here as possibly outdated: confirm them against the official documentation for the installed version.
- Ask before actions that cost money, consume shared GPUs or cloud quota, touch personal or patient data, or cannot be undone.

## Related skills

- `statistical-analysis`: Guided statistical analysis for research data - test selection, assumption checking, effect sizes, power analysis, Bayesian alternatives, a…
