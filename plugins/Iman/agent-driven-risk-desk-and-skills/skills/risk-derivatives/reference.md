# Reference: formulas, conventions and sources

## Notation

S is the underlying price (a spot price, or a futures price F). K is the strike. t is years to expiry, ACT/365: (expiry - as_of) in calendar days / 365. sigma is implied vol per 1.00. r is the continuously compounded rate. q is the continuous carry or dividend yield. n is quantity and m is multiplier, so n x m is units of underlying. N is the standard normal distribution function.

## Pricing, all inside optiondesk_engine 0.3.0

Spot underlying, Black-Scholes-Merton with continuous yield (`bs_price`, `all_greeks`):

    d1 = (ln(S/K) + (r - q + sigma^2/2) t) / (sigma sqrt t),   d2 = d1 - sigma sqrt t
    call = S e^{-qt} N(d1) - K e^{-rt} N(d2)
    put  = K e^{-rt} N(-d2) - S e^{-qt} N(-d1)

Futures underlying, Black-76 (`black76_price`, `black76_greeks`): the same formula with S = F and q = r, so

    call = e^{-rt} (F N(d1) - K N(d2)),   d1 = (ln(F/K) + sigma^2 t / 2) / (sigma sqrt t)

At or after expiry inside a decayed horizon, the engine's `intrinsic(S', K, kind)` gives the payoff: max(S' - K, 0) for a call and max(K - S', 0) for a put.

## Engine conventions inherited, as stated in its source

From `optiondesk_engine/pricing/greeks_full.py` (module docstring) and `black_scholes.py` (module docstring):

- delta and gamma are per 1.0 of underlying price.
- vega is per 1.00 of vol. Risk Desk divides by 100 to report per vol point.
- theta is per calendar day of time passing, so the per-year derivative is divided by 365.
- rho is per 1.00 of rate. Risk Desk divides by 100 to report per rate point.
- An implied vol above 10.0 or a t above 100 years is refused as a unit error.

## Black-76 rho

With the future held fixed, the rate moves only the discount, so

    rho = dV/dr with F fixed = -t V

The engine's `black76_greeks` returns this from optiondesk-engine commit `4a282d9` (2026-11-04). Before that commit it returned `all_greeks`' partial in r with the carry held fixed, which is a different number: at F=100, K=95, t=0.75, sigma=0.3, r=0.05 the call rho was 36.161 against -tV -9.226. Risk Desk used to correct this locally; the one copy is now the engine's. The engine wheel Risk Desk installs is built from that commit and identified by its sha256 in `wheel-hashes.json`, because the version string 0.3.0 was also carried by an earlier build without the fix. `tests/test_derivatives.py` fails two tests (the finite-difference test and the parity test) when run against that earlier build.

## Aggregation

Per underlying u, the engine's `net_greeks` sums each Greek times n x m over the positions on u. A linear position contributes delta 1 and nothing else. Then:

    cash_delta_u         = Delta_u S_u
    cash_gamma_1pct_u    = Gamma_u S_u^2 / 100
    vega_per_vol_point_u = Vega_u / 100
    theta_per_day_u      = Theta_u
    rho_per_rate_point_u = Rho_u / 100

Totals are plain sums over u.

## Scenario grid

For spot shock s (a simple return) and vol shock v (absolute, per 1.00), each underlying moves dS_u = S_u s and each option's vol becomes sigma + v. A vol at or below zero is refused. Time is fixed.

    full  = sum over positions of n m (V(S(1+s), sigma+v) - V(S, sigma))
    DG    = sum over u of Delta_u dS_u + Gamma_u dS_u^2 / 2
    DGV   = DG + sum over u of Vega_u v      (Vega per 1.00)
    error = approximation - full

DG is the second-order Taylor expansion of value in price, so its error is third order in dS. The tests check that doubling the move multiplies the error by 7 to 9 (2^3 = 8).

## Historical P&L

For scenario j with returns r_uj and optional vol changes v_uj:

    P&L_j = sum over positions of n m (V(S_u(1+r_uj), sigma+v_uj, t - h) - V(S_u, sigma, t))

h = 0 when `time_mode` is `fixed`, and h = horizon_days / 365 when it is `decay`. The vector goes unchanged to `riskdesk.analytics.tail_risk` with the request's confidence, horizon and portfolio value. No VaR or ES arithmetic is repeated here.

## Independent checks in the tests

- Every cash Greek, against central finite differences of the revalued book in price, vol, rate and time.
- Put-call parity, in closed form: long call plus short put at one strike is worth n m (S e^{-qt} - K e^{-rt}) on spot and n m e^{-rt} (F - K) on a future. Its gamma and vega are zero, and its Black-76 rho is -t times its value. Its grid and historical P&L are n m S s e^{-qt} under any vol shock.
- The cubic order of the delta-gamma error, and a pure vol shock almost fully explained by vega.
- Settlement: an option whose life ends inside the horizon has P&L equal to payoff minus premium.

## Sources

- F. Black and M. Scholes, "The Pricing of Options and Corporate Liabilities", Journal of Political Economy 81(3), 1973, 637-654.
- R. C. Merton, "Theory of Rational Option Pricing", Bell Journal of Economics and Management Science 4(1), Spring 1973, 141-183, DOI 10.2307/3003143. This is the continuous dividend yield extension.
- F. Black, "The Pricing of Commodity Contracts", Journal of Financial Economics 3(1-2), 1976, 167-179, DOI 10.1016/0304-405X(76)90024-6. This is the option on a future.

The three bibliographic records (volume, issue, pages) were checked on 2026-11-04: Merton and Black against EconPapers/RePEc, and Black-Scholes against a JSTOR-derived record of the University of Chicago Press original. The texts are behind paywalls, so no section or equation number inside any paper is cited. The formulas above are guarded by the closed-form and finite-difference tests, not by a reading of the papers. No regulatory constant is used anywhere in this skill.
