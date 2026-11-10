# Reference: contracts, formulas, conventions and sources

Read when a number has to be interpreted or defended. Code:
`src/riskdesk/decomposition.py`. Tests, each against an independent check:
`tests/test_decomposition.py`.

## Notation

- T return rows (scenarios), oldest first; N assets; P positions; K factors.
- r_t: row t of simple asset returns, each spanning `horizon_days`.
- x_j: signed market value of position j in the base currency; a(j) its asset.
- e: net exposure per asset, e_a = sum of x_j over positions with a(j) = a.
- Loss L = -P&L. Loss is positive throughout.
- z = Phi^-1(alpha) and phi are the standard normal quantile and density, alpha the confidence.

## Request contracts

Every request carries `as_of`, `currency` (three capitals), `source`,
`data_mode` (`synthetic` or `user-licensed`). Unknown fields and non-finite
numbers are refused. Results come back through the Risk Desk envelope
(method, currency, as-of, source, data mode, input SHA-256, degraded flag
and reason, assumptions).

| request | fields |
|---|---|
| CovarianceRequest | `assets` (unique), `returns` (T >= 2 rows of N values, each >= -1), `horizon_days`, `method` (`sample`, `ewma`, `ledoit_wolf`), `decay` (required for `ewma` only, 0 < decay < 1) |
| ParametricRequest | `nav`, `positions` (unique ids), `assets`, `covariance` (N x N, symmetric, positive semidefinite, of returns over the horizon), `confidence` (0.5 < confidence < 1, so z > 0), `horizon_days` |
| HistoricalRequest | `nav`, `positions`, `assets`, `returns`, `horizon_days`, `confidence` |
| FactorRequest | `nav`, `positions`, `assets`, `returns`, `horizon_days`, `factors` (unique), `factor_returns` (same T rows, K values each), T > K + 1 |

A position whose asset is absent from `assets` is refused. An asset with no
position has zero exposure.

## Covariance

- Sample: S = (1/(T-1)) sum_t (r_t - rbar)(r_t - rbar)'.
- EWMA: Sigma = sum_t w_t r_t r_t' with w_t = lambda^(T-t) / sum_s lambda^(T-s),
  so the latest row has the largest weight and the weights sum to one. Zero
  mean. Source: RiskMetrics Technical Document, J.P. Morgan and Reuters,
  Fourth Edition, December 1996. Section 5.2.1, Table 5.1 (volatility estimator),
  Eq. [5.1] (the (1 - lambda) approximation of the weight sum) and Eq. [5.2]
  (the finite normalisation used here); Section 5.2.1.1, Table 5.4 and Eq.
  [5.6] (covariance and its recursion); Section 5.3, first paragraph: "In
  practice, when we make volatility and correlation forecasts we set the
  sample mean to zero." The decay is a user input. The document states its
  own choice in Section 5.3.2 and 5.3.2.2: 0.94 for the daily data set and
  0.97 for the monthly data set. Quote that only as RiskMetrics' choice, not
  as a property of the user's data.
- Ledoit-Wolf: scikit-learn `sklearn.covariance.LedoitWolf` (installed 1.9.1),
  default `assume_centered=False`, so data are demeaned and S = X'X/T. The
  estimate is (b^2/d^2) m I + (a^2/d^2) S with m = tr(S)/N,
  d^2 = ||S - mI||^2, b^2 = min((1/T^2) sum_k ||x_k x_k' - S||^2, d^2),
  a^2 = d^2 - b^2, and ||A||^2 = tr(AA')/N. `shrinkage` is b^2/d^2. Source:
  O. Ledoit and M. Wolf, "A Well-Conditioned Estimator for Large-Dimensional
  Covariance Matrices", Definitions 1 and 2, Lemmas 3.2 to 3.5 and Eq. (14)
  (text read from the February 2001 working paper); published in Journal of
  Multivariate Analysis 88(2), February 2004, 365-411 (citation as given in
  the scikit-learn docstring).
- Positive definiteness: smallest eigenvalue > max|eigenvalue| x N x machine
  epsilon, the default rank tolerance in the numpy `matrix_rank` notes. A
  matrix that fails is returned unaltered with `positive_definite: false`,
  `repair: null` and a degraded reason. No repair is applied: clipping
  eigenvalues to zero leaves the matrix singular, and any positive floor
  would be an invented constant. The sample estimate is singular when T <= N
  (demeaning removes one rank) and the zero-mean EWMA estimate when T < N.
- Correlation is null where either volatility is zero.

## Parametric (normal) VaR and ES with Euler allocation

P&L ~ Normal(0, sigma^2), with sigma^2 = e' Sigma e.

- VaR = z sigma. ES = sigma phi(z) / (1 - alpha), which is Eq. (3.10a) of
  Tasche (below) evaluated for the normal: the test integrates Phi^-1 over
  (alpha, 1) by quadrature and matches to 1e-8.
- Euler principle: contribution of position j = x_j d rho / d x_j. Tasche
  Eq. (2.6). For standard-deviation-based measures c sigma, the contribution is
  c cov(X_j, X) / sqrt(var X), Eq. (3.4a). With c = z (VaR) or
  c = phi(z)/(1 - alpha) (ES):
  - marginal_j = c (Sigma e)_a(j) / sigma, per unit of currency;
  - component_j = x_j marginal_j; sum over j = c sigma exactly, since
    e' Sigma e / sigma = sigma;
  - percentage_j = component_j / total.
- Incremental VaR_j = VaR(book) - VaR(book without position j), with the
  reduced variance recomputed in full. Tasche Eq. (2.10) defines this
  quantity and calls it the "marginal risk contribution". Here "marginal"
  means the derivative, as in common desk usage. Incremental VaR does not sum
  to VaR.
- Zero portfolio variance is refused, because the contributions divide by
  sigma.

## Historical-simulation ES with Euler allocation

Scenario losses L_t = -sum_j x_j r_t,a(j). Tail mass m = T(1 - alpha),
computed in decimal arithmetic so that 20 x 0.05 is exactly 1. Rank the
scenarios by L, largest first (stable order). The first floor(m) get weight 1
and the next gets m - floor(m).

- ES = (1/m) sum_t w_t L_(t). This is the plug-in of Eq. (3.10a), and equals
  `risk_tail` (skfolio CVaR) on the same P&L. The test checks seven (T, alpha)
  pairs, including exact-integer tail masses.
- component_j = (1/m) sum_t w_t L_j,(t), the tail-weighted loss of
  position j over the same ranked scenarios. Sum over j = ES exactly.
  Source: Tasche Eq. (3.11a), ES contribution = -E[X_j | X <= -VaR], and
  Section 3.4, which states that substituting the empirical measure gives
  consistent estimators for ES contributions. The test also checks that
  x_j times the bumped-ES slope equals component_j.
- Degraded when m < 20 (the same reporting rule and wording as `risk_tail`)
  and when equal portfolio losses straddle a weight change. In that case the
  ES total is unaffected but the split depends on input order.
- `tail_scenarios` lists each scenario index (0-based row) with its weight and loss.

## Factor exposure

For each asset, OLS with an intercept: r_t,a = alpha_a + beta_a' f_t + eps_t,a
(numpy least squares; the test matches scikit-learn LinearRegression).
A design matrix of less than full rank is refused as collinear.

- Portfolio factor exposure b = B'e, in currency P&L per 1.00 factor return.
  Factor beta = b / NAV.
- Variance split, using T - 1 throughout:
  total = var(P&L) = b' Sigma_F b + e' Sigma_eps e = systematic + idiosyncratic.
  This holds exactly in sample because OLS residuals have zero mean and are
  uncorrelated with the factors. `specific` is the diagonal part
  sum e_a^2 var(eps_a), and `residual_cross` = idiosyncratic - specific is the
  residual covariance between assets. A diagonal factor model would report only
  `specific`.
- r_squared per asset = 1 - var(eps_a)/var(r_a), null for a constant asset.
  This is in sample only.

## Sources, as checked

- Dirk Tasche, "Capital Allocation to Business Units and Sub-Portfolios: the
  Euler Principle", arXiv:0708.2542v3, 22 June 2008. Equations (2.6), (2.10),
  (3.4a), (3.10a), (3.11a) and Section 3.4 were read from the arXiv PDF text.
- RiskMetrics Technical Document, Fourth Edition, 1996, sections listed above,
  read from the PDF text.
- Ledoit and Wolf, as above.
- Hallerbach's decomposition paper is not cited: its text was not checked.
