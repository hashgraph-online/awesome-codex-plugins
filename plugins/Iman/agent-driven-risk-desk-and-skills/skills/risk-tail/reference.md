# Reference: tail models, formulas and sources

Code: `src/riskdesk/analytics.py` (`tail_risk`) and `src/riskdesk/tail_models.py` (`tail_models`).

## Notation

- P&L_t: supplied profit and loss, positive is profit. PV: portfolio value.
- r_t = P&L_t / PV. Loss L_t = -r_t. q: confidence, for example 0.99.
- VaR_q: the q-quantile of loss. ES_q = E[L | L >= VaR_q] for a continuous model,
  equivalently (1/(1-q)) times the integral of VaR_u for u from q to 1.
- Every monetary output is the return-unit figure times PV.

## historical (`risk_tail`)

skfolio 1.1.0 `value_at_risk` and `cvar` on r_t. The adapter moves the confidence one float
toward 1 only where (1-q)n is an exact integer, so binary rounding cannot pick the next order
statistic (see `analytics.tail_risk`). `tail_models` calls `tail_risk` for every empirical
column, so all of them share this one quantile rule.

## normal

Maximum likelihood fit to L (scipy `norm.fit`: sample mean, standard deviation with divisor n).

    VaR = m + s z,   z = Phi^-1(q)
    ES  = m + s phi(z) / (1 - q)

Check: ES equals the numerical integral of the fitted quantile function
(`tests/test_var_backtest_models.py`).

## student_t

Maximum likelihood fit of a location-scale Student-t (scipy `t.fit`: dof nu, loc m, scale s).
With x = t_nu^-1(q) and g_nu the standard t density:

    VaR = m + s x
    ES  = m + s g_nu(x) / (1 - q) * (nu + x^2) / (nu - 1),   nu > 1

Derivation: d/dy[(nu + y^2) g_nu(y)] = -(nu - 1) y g_nu(y), so the integral of y g_nu(y) from x
to infinity is g_nu(x)(nu + x^2)/(nu - 1). For nu <= 1 ES is infinite and is not reported.
Check: numerical integration of the fitted density over the tail.

## evt_pot (unconditional peaks over threshold)

Source: A. J. McNeil and R. Frey, "Estimation of tail-related risk measures for heteroscedastic
financial time series: an extreme value approach", Journal of Empirical Finance 7 (2000) 271-300.
Read from the authors' preprint dated 19 June 1999 (Frey's publication page, WU Vienna).

- k = floor(0.10 n) exceedances. The paper fixes k = 100 for windows of n = 1000 (section 2.3,
  and "we always set k = 100" in the section 3 backtests); 0.10 keeps that fraction.
- Threshold u = the (k+1)th largest loss. The k excesses over u are fitted by maximum likelihood
  to a generalised Pareto distribution with shape xi and scale beta (scipy `genpareto`, location 0;
  scipy's shape c is xi).
- Tail estimator, eq. (9): 1 - F(x) = (k/n)(1 + xi (x - u)/beta)^(-1/xi), for x > u.
- Quantile, eq. (10), valid for q > 1 - k/n:

      VaR = u + (beta/xi) [ ((1 - q)/(k/n))^(-xi) - 1 ]      (limit xi -> 0: u - beta ln((1 - q) n/k))

- ES from eq. (14), the GPD mean excess E[W | W > w] = (w + beta)/(1 - xi) for xi < 1, applied to
  the excess over VaR (the preprint's own next equation is cut off at the page; this step is
  reproduced here and checked by integrating the fitted GPD survival function):

      ES = VaR/(1 - xi) + (beta - xi u)/(1 - xi)

- Refused: q <= 1 - k/n or k < 2 (column unavailable), xi >= 1 (ES not reported).
- Flagged: k < 50. Section 2.3: "as long as k is greater than about 50 the method is robust".

Checks: VaR inverts eq. (9) to 1 - q; ES matches numerical integration; across 40 samples of
n = 1000 from t(4) the mean EVT 99% quantile is within 5% of the true t(4) quantile.

## GARCH(1,1)-t (Option Desk)

`optiondesk_engine.simulation.garch.fit_garch_t` with its defaults (2 chains, 3000 draws, 1000
burn-in, seed 11), on r_t:

    r_t = mu + e_t,  e_t = sigma_t z_t,  z_t standardised t(nu)
    sigma_t^2 = omega + alpha e_{t-1}^2 + beta sigma_{t-1}^2,  sigma_1^2 = omega/(1 - alpha - beta)

It refuses fewer than 60 observations; the three GARCH columns are then listed in `unavailable`
with the engine's message. Non-convergence (its R-hat and ESS gate) marks the result degraded.

Point estimate for the two filtered columns: the posterior mean of each parameter. Standardised
residuals z_t = (r_t - mu)/sigma_t; one-step volatility sigma_{T+1} from the same recursion as
`GarchPosterior.last_variance` (checked equal in the tests).

- `filtered_historical`: the empirical estimator on mu + sigma_{T+1} z_t, t = 1..n.
- `garch_evt`: the peaks-over-threshold estimator above on the residual losses -z_t, then
  VaR = -mu + sigma_{T+1} VaR_z and ES = -mu + sigma_{T+1} ES_z. This is McNeil and Frey's
  conditional method, eq. (3), except that the GARCH is Option Desk's Bayesian fit rather than
  their pseudo maximum likelihood.
- `garch_t_monte_carlo`: `simulate_paths(posterior, spot=1, horizon_days=1)` with its defaults
  (20000 paths, seed 23). Each path draws its own posterior parameter set and a t innovation, so
  parameter uncertainty is in this column and not in the two above. With spot 1 and one step,
  log(terminal) = mu + sigma z exactly, which is the simulated r. The empirical estimator then
  reads VaR and ES from those draws.

All three forecast one sample period after the last observation.

## Sources not read

No published source is cited for filtered historical simulation or for the Student-t ES
formula. Both are defined by the formulas above and checked numerically, not by citation.
