# Reference: formulas, signs, sources and refusals

Read this when a number has to be interpreted or defended. Nothing here is
needed to run a tool. The code is `src/riskdesk/scenarios.py`; every
revaluation goes through the existing linear stress engine
(`riskdesk.analytics.stress_test`).

## Notation and signs

| symbol | meaning | unit |
|---|---|---|
| `w` | net market value per asset, summed over positions in that asset | base currency |
| `s` | shock vector, one simple return per asset | per 1.00, so -0.10 is a 10% fall |
| `P&L` | `w' s`, positive is profit | base currency |
| `loss` | `-P&L`, positive is a loss, negative is a gain | base currency |
| `L` | target loss, strictly positive | base currency |
| `Sigma` | caller's covariance of the simple returns over `horizon_days` | per 1.00 squared |
| `d` | Mahalanobis distance `sqrt(s' Sigma^-1 s)` | dimensionless |
| `Phi` | standard normal distribution function | |

No shock may be below -1: a linear asset cannot lose more than its value.
Every result carries `currency`, `as_of`, `source`, `data_mode`,
`input_sha256`, `degraded`, `degraded_reason` and `assumptions` from the
shared envelope.

## Historical replay

Inputs: the caller's own dated price levels per asset, a window `start` to
`end`, and a measure. Risk Desk ships no prices.

- `end_over_start` (default): `s_i = P_i(end) / P_i(start) - 1`.
- `worst_peak_to_trough` (explicit choice):
  `s_i = min over window dates t of P_i(t) / max(P_i(u), start <= u <= t) - 1`,
  which equals the minimum over all date pairs `t1 <= t2` in the window of
  `P_i(t2) / P_i(t1) - 1`, and is 0 for a series that never falls. The test
  suite checks the running-peak form against that exhaustive pairwise search.

Each asset's series must contain both `start` and `end` exactly. A missing
series or date is an error. There is no interpolation, nearest-date match,
fill or zero. Levels outside the window are ignored. A position whose own
history is unavailable can be mapped to another series through `proxies`;
every proxy is named in `degraded_reason` and the result is degraded.

The peak-to-trough measure takes each asset's worst fall separately. The
falls need not happen on the same dates, and a fall is a gain for a short
position, so the result is not the book's worst loss inside the window.
Returns are price returns of the supplied series; income, carry and
currency translation are excluded unless the series already includes them.

## Scenario library: dates only

The library holds windows and the reason for each date. It holds no
returns. Business-day starts are the last weekday before the event; the
caller's series must contain the date, or the replay refuses it.

| id | start | end |
|---|---|---|
| `lehman-2008` | 2008-09-12 | 2008-10-31 |
| `covid-2020` | 2020-02-19 | 2020-03-23 |
| `uk-gilt-ldi-2022` | 2022-09-22 | 2022-10-14 |

### lehman-2008

Bank for International Settlements, 79th Annual Report 2008/09, 29 June
2009, Chapter II, opening list of the five stages of the crisis,
<https://www.bis.org/publ/arpdf/ar2009e2.htm>. Quoted (read through a web
fetch on 2026-11-04): stage two is "the gradual deterioration in financial
conditions from mid-March to the failure of Lehman Brothers on 15 September
2008;" and stage three runs "from mid-September to late October, a global
loss of confidence, a massive flight to quality".

- Start 2008-09-12, a Friday: the last business day before the failure on
  Monday 15 September 2008.
- End 2008-10-31: the source says "late October" and gives no day. The last
  day of October is this library's convention, not a sourced date. Replay
  with your own end date if your question needs a different one.

### covid-2020

Financial Stability Board, Holistic review of the March market turmoil, 17
November 2020, <https://www.fsb.org/uploads/P171120-2.pdf>. Quoted from the
PDF text:

- Section 2.1: "In the US and continental Europe, stock markets reached
  record highs on 19 February, while other indexes were close to all-time
  highs." Start 2020-02-19.
- Annex 1: the "dash for cash" period ran "approximately 11 March - 23
  March", and "On Monday 23 March the Fed announced extensive additional
  measures to support the economy." Section 2.4: "Global stock markets
  bottomed out between 18 March (Europe) and 23 March (US, China)." End
  2020-03-23.

The start is a US and continental European equity peak. Other markets
peaked on other days; a UK or Asian book may want its own start.

### uk-gilt-ldi-2022

Bank of England, "Bank of England announces gilt market operation", press
release, 28 September 2022,
<https://www.bankofengland.co.uk/news/2022/september/bank-of-england-announces-gilt-market-operation>:
"the Bank will carry out temporary purchases of long-dated UK government
bonds from 28 September" and "Auctions will take place from today until 14
October."

Bank of England Quarterly Bulletin 2023, "Financial stability buy/sell
tools: a gilt market case study",
<https://www.bankofengland.co.uk/quarterly-bulletin/2023/2023/financial-stability-buy-sell-tools-a-gilt-market-case-study>,
section "Context for the Bank's intervention": the stress came "following
the UK Government's fiscal statement of 23 September", with a bid-ask
spread measure that "increased from around 0.5 basis points on 22
September"; section "Outline of the Bank's intervention": "the Bank bought
£19.3 billion of gilts between 28 September and 14 October 2022". Both
Bank of England quotations were read through a web fetch on 2026-11-04.

- Start 2022-09-22, a Thursday: the last business day before the fiscal
  statement of Friday 23 September 2022.
- End 2022-10-14: the last day of the temporary purchases.

## Reverse stress for a linear book

Problem: the most plausible shock that produces loss `L`, where plausible
means close to zero in the metric of the supplied covariance:

    minimise   s' Sigma^-1 s
    subject to w' s = -L

Derivation. With Lagrangian `s' Sigma^-1 s - 2 lambda (w' s + L)`, setting
the gradient to zero gives `Sigma^-1 s = lambda w`, so `s = lambda Sigma w`.
Substituting into the constraint, `lambda w' Sigma w = -L`, so

    s* = -L Sigma w / (w' Sigma w)
    d* = sqrt(s*' Sigma^-1 s*) = L / sqrt(w' Sigma w)

The objective is strictly convex when `Sigma` is positive definite, so this
stationary point is the unique minimum. `sqrt(w' Sigma w)` is reported as
`pnl_standard_deviation`. The closed form needs no matrix inverse.
Tests: a one-asset hand calculation (`s = -L / w`, `d = L / (|w| sigma)`),
revaluation of `s*` to exactly `L`, `d*` against an explicit
`numpy.linalg.inv`, and 2,000 random equal-loss perturbations
(`s* + v`, `w' v = 0`) that are never closer.

Floors. Each shock is bounded below by -1, and by any tighter `floors`
the caller supplies. When `s*` respects every floor it is also the floored
optimum. Otherwise the floored problem

    minimise s' Sigma^-1 s  subject to  w' s = -L,  s_i >= f_i

is solved with `scipy.optimize.minimize(method="SLSQP")`, using the
Cholesky factor of `Sigma` for `Sigma^-1 s`. The result is refused unless
SLSQP reports success and `|w' s + L| <= 1e-7 L`. Its optimality
conditions are `Sigma^-1 s = lambda w + mu` with `mu_i >= 0` on binding
floors and `mu_i = 0` elsewhere; the tests check these, and check a
two-asset case against a 300,001-point grid over the feasible line. The
floored distance is at least `d*`, which is reported as
`unbounded_mahalanobis_distance`. If no short position exists, the largest
reachable loss is `-sum(w_i f_i)`; a larger `L` is refused.

Probability, labelled as an assumption. If `s` were jointly normal with
mean zero and covariance `Sigma`, `w' s` would be normal with standard
deviation `sqrt(w' Sigma w)`, so `P(loss >= L) = Phi(-L / sqrt(w' Sigma w))
= Phi(-d*)`. This is `loss_exceedance_probability_if_normal`. It ignores
floors, fat tails and estimation error in `Sigma`; it is a reference
figure, not an estimate. A seeded 400,000-draw simulation agrees within
four standard errors.

## Scenario scaling

For a scenario `s` with loss `loss(s) = -w' s > 0`, loss is linear in the
shocks, so `k = L / loss(s)` and `loss(k s) = L` exactly. The scaled
scenario keeps the shape of `s`. A scenario that does not lose money, or a
multiple that takes any shock below -1, is refused with the offending
assets named.

## What is refused rather than estimated

- A replay asset with no series, or a series without the exact start or end date.
- Non-positive, infinite or missing price levels.
- A covariance that is not square, not symmetric, not positive definite, or
  not ordered like the named portfolio assets.
- A book with zero P&L variance (for example no net exposure).
- A target loss beyond what the floors allow, and a floor below -100%.
- An SLSQP result that did not converge or does not reach the target loss.
- Any non-finite shock, P&L or distance.

## Not claimed

No window, reverse stress scenario or multiple is a forecast or an event
probability. The normal probability is conditional on an assumption the
data usually violate. No external paper is cited for the reverse stress
formula; it rests on the derivation and tests above.
