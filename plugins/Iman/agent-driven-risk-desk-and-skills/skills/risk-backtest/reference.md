# Reference: VaR and ES backtests, formulas and sources

Code: `src/riskdesk/backtest.py` (`var_backtest`).

## Notation

- X_t: realised P&L on row t, positive is profit. T: number of rows.
- VaR_t, ES_t: forecasts for row t, positive is loss. c: confidence. p = alpha = 1 - c.
- I_t = 1 if X_t + VaR_t < 0 (loss strictly above VaR), else 0. x = sum of I_t.
- xlogy(a, b) = a ln b with 0 ln 0 = 0, so zero counts drop out.

## Kupiec proportion of failures

P. H. Kupiec (1995), "Techniques for verifying the accuracy of risk measurement models",
Journal of Derivatives 3(2), 73-84 (bibliographic; the paper text was not read).

    LR_pof = -2 [ (T - x) ln(1 - p) + x ln p - (T - x) ln(1 - x/T) - x ln(x/T) ]  ~ chi2(1)

Check: equals 2[ln Binom(x; T, x/T) - ln Binom(x; T, p)] from scipy's binomial log pmf for
x = 0, interior values and x = T; under the null with T = 1000, p = 0.05, its rejection rate at
5% over 4000 seeded samples is between 3.5% and 7%.

## Christoffersen independence and conditional coverage

P. F. Christoffersen (1998), "Evaluating interval forecasts", International Economic Review
39(4), 841-862 (bibliographic; the paper text was not read).

On the T - 1 transitions, n_ij counts I_{t-1} = i followed by I_t = j.
pi0 = n01/(n00 + n01), pi1 = n11/(n10 + n11), pi = (n01 + n11)/(T - 1).

    ln L_markov = n00 ln(1 - pi0) + n01 ln pi0 + n10 ln(1 - pi1) + n11 ln pi1
    ln L_iid    = (n00 + n10) ln(1 - pi) + (n01 + n11) ln pi
    ln L_null   = (n00 + n10) ln(1 - p)  + (n01 + n11) ln p
    LR_ind = -2 (ln L_iid  - ln L_markov)  ~ chi2(1)
    LR_cc  = -2 (ln L_null - ln L_markov)  ~ chi2(2)

LR_cc equals LR_pof computed on the T - 1 transition rows plus LR_ind. Checks: each statistic
matches a brute-force product over the transitions; the decomposition holds; five consecutive
exceptions reject independence and evenly spaced ones do not. A tiny negative statistic from
rounding is reported as zero.

## Basel traffic light

Basel Framework, MAR99 "Guidance on use of the internal models approach", version in force
from 1 January 2023 (published 27 March 2020), read on 4 November 2026 at bis.org.

- MAR99.4: one-day risk measures are compared with one-day trading outcomes.
- MAR99.17 and Table 2: for 250 observations at 99% coverage, green 0 to 4 exceptions, amber
  5 to 9, red 10 or more. "For other sample sizes, the amber zone begins at the point where the
  cumulative probability equals or exceeds 95%, and the red zone begins at the point where the
  cumulative probability equals or exceeds 99.99%." The cumulative probability is
  P(Binomial(T, 0.01) <= x).

The current text calls the middle zone amber; the tool uses that word. It reports the zone only
for confidence 0.99 and horizon_days 1, over all T rows supplied, with `amber_from` and
`red_from` for that T. Table 2's multipliers are not reported.

Check: for T = 250 every count 0 to 10 gives Table 2's zone and its cumulative probability to
two decimals (8.11, 28.58, 54.32, 75.81, 89.22, 95.88, 98.63, 99.60, 99.89, 99.97, 99.99).

## Acerbi-Szekely Z2 (ES backtest)

C. Acerbi and B. Szekely (2014), "Backtesting expected shortfall", Risk, December 2014 (MSCI).
The paper text was not read. The statistic is taken from MathWorks Risk Management Toolbox
documentation for `esbacktestbysim` `unconditional`, which cites that paper:

    Z2 = sum_t X_t I_t / (T alpha ES_t) + 1

E[Z2] = 0 when each X_t follows the forecast distribution, since ES_t = -E[X_t I_t]/alpha.
Negative Z2 means understated risk; the test is one sided.

Null distribution. Z2's distribution depends on the forecast distributions, which a VaR and ES
series do not identify. The tool assumes each day's loss is m_t + s_t Y, with Y standard normal
or standard t(nu) as stated in `es_null`. With q_Y the c-quantile of Y and
e_Y = E[Y | Y > q_Y] (normal: phi(q)/alpha; t: g_nu(q)(nu + q^2)/((nu - 1) alpha)):

    s_t = (ES_t - VaR_t)/(e_Y - q_Y),  m_t = VaR_t - s_t q_Y

so the null reproduces both forecasts exactly. It draws 10,000 samples of the whole series
(numpy default_rng(seed)), computes Z2 for each, and reports
p = (1 + #{Z2_sim <= Z2_obs})/(1 + 10,000), with standard error sqrt(p(1 - p)/10,000).
The add-one form keeps a finite simulation from reporting a p-value of exactly zero.
With no exceptions Z2 = 1 and p = 1.

Checks: the mean of Z2 over 4000 samples drawn from the forecast distribution is within 0.03 of
zero; the implied null reproduces VaR and ES; a P&L 1.6 times wider than the forecast gives
p < 0.01 under both nulls; the same seed gives the same result. Measured once, not a test:
200 true-model replications under the t(5) null gave p-values with a Kolmogorov-Smirnov p of
0.38 against uniform.

Not used: the 0.7 and 1.8 zone cut-offs that secondary sources attribute to the paper, because
the paper text was not read.
