# Standard Bayesian Workflow

The eight steps in full, with code: data preparation, model building, prior predictive
check, fitting, diagnostics, posterior predictive check, analyzing results, and
prediction.

## Standard Bayesian Workflow

Follow this workflow for building and validating Bayesian models:

### 1. Data Preparation

```python
import pymc as pm
import arviz as az
import numpy as np

# Load and prepare data
X = ...  # Predictors
y = ...  # Outcomes

# Standardize predictors for better sampling
X_mean = X.mean(axis=0)
X_std = X.std(axis=0)
X_scaled = (X - X_mean) / X_std
```

**Key practices:**
- Standardize continuous predictors (improves sampling efficiency)
- Center outcomes when possible
- Handle missing data explicitly (treat as parameters)
- Use named dimensions with `coords` for clarity

### 2. Model Building

```python
coords = {
    'predictors': ['var1', 'var2', 'var3'],
    'obs_id': np.arange(len(y))
}

with pm.Model(coords=coords) as model:
    # Mutable data container so prediction data can be swapped later
    X_data = pm.Data('X_scaled', X_scaled, dims=('obs_id', 'predictors'))

    # Priors
    alpha = pm.Normal('alpha', mu=0, sigma=1)
    beta = pm.Normal('beta', mu=0, sigma=1, dims='predictors')
    sigma = pm.HalfNormal('sigma', sigma=1)

    # Linear predictor
    mu = alpha + pm.math.dot(X_data, beta)

    # Tie the observed variable's shape to X_data for out-of-sample prediction
    y_obs = pm.Normal('y_obs', mu=mu, sigma=sigma, observed=y, shape=X_data.shape[0], dims='obs_id')
```

**Key practices:**
- Use weakly informative priors (not flat priors)
- Use `HalfNormal` or `Exponential` for scale parameters
- Use named dimensions (`dims`) instead of `shape` when possible
- Use `pm.Data()` for values that will be updated for predictions

### 3. Prior Predictive Check

**Always validate priors before fitting:**

```python
with model:
    prior_pred = pm.sample_prior_predictive(draws=1000, random_seed=42)

# Visualize
az.plot_ppc(prior_pred, group='prior')
```

**Check:**
- Do prior predictions span reasonable values?
- Are extreme values plausible given domain knowledge?
- If priors generate implausible data, adjust and re-check

### 4. Fit Model

```python
with model:
    # Optional: Quick exploration with ADVI
    # approx = pm.fit(n=20000)

    # Full MCMC inference
    idata = pm.sample(
        draws=2000,
        tune=1000,
        chains=4,
        target_accept=0.9,
        random_seed=42,
        idata_kwargs={'log_likelihood': True}  # For model comparison
    )
```

**Key parameters:**
- `draws=2000`: Number of samples per chain
- `tune=1000`: Warmup samples (discarded)
- `chains=4`: Run 4 chains for convergence checking
- `target_accept=0.9`: Higher for difficult posteriors (0.95-0.99)
- Include `log_likelihood=True` for model comparison
- If using PyMC 6 sampler-specific kwargs, avoid deprecated `nuts_sampler_kwargs`; pass explicit NUTS kwargs through `nuts={...}` when needed

### 5. Check Diagnostics

**Use the diagnostic script:**

```python
from scripts.model_diagnostics import check_diagnostics

results = check_diagnostics(idata, var_names=['alpha', 'beta', 'sigma'])
```

**Check:**
- **R-hat < 1.01**: Chains have converged
- **ESS > 400**: Sufficient effective samples
- **No divergences**: NUTS sampled successfully
- **Trace plots**: Chains should mix well (fuzzy caterpillar)

**If issues arise:**
- Divergences → Increase `target_accept=0.95`, use non-centered parameterization
- Low ESS → Sample more draws, reparameterize to reduce correlation
- High R-hat → Run longer, check for multimodality

### 6. Posterior Predictive Check

**Validate model fit:**

```python
with model:
    pm.sample_posterior_predictive(idata, extend_inferencedata=True, random_seed=42)

# Visualize
az.plot_ppc(idata)
```

**Check:**
- Do posterior predictions capture observed data patterns?
- Are systematic deviations evident (model misspecification)?
- Consider alternative models if fit is poor

### 7. Analyze Results

```python
# Summary statistics
print(az.summary(idata, var_names=['alpha', 'beta', 'sigma']))

# Posterior distributions
az.plot_posterior(idata, var_names=['alpha', 'beta', 'sigma'])

# Coefficient estimates
az.plot_forest(idata, var_names=['beta'], combined=True)
```

### 8. Make Predictions

```python
X_new = ...  # New predictor values
X_new_scaled = (X_new - X_mean) / X_std

with model:
    pm.set_data({'X_scaled': X_new_scaled}, coords={'obs_id': np.arange(len(X_new_scaled))})
    post_pred = pm.sample_posterior_predictive(
        idata,
        var_names=['y_obs'],
        predictions=True,
        random_seed=42
    )

# Extract prediction intervals
y_pred_mean = post_pred.predictions['y_obs'].mean(dim=['chain', 'draw'])
y_pred_hdi = az.hdi(post_pred.predictions, var_names=['y_obs'])
```
