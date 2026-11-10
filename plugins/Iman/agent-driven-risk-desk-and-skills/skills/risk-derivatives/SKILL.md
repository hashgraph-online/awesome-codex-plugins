---
name: risk-derivatives
description: Greeks, spot and vol scenario grids, and historical full-revaluation P&L for a book that mixes linear positions with European calls and puts on spot (Black-Scholes-Merton) or futures (Black-76) underlyings. Use when a book holds options and the question is cash delta, gamma, vega, theta or rho exposure, how the book revalues under joint spot and vol shocks, how far delta-gamma is from full revaluation, or VaR and Expected Shortfall of a book with options. Not for American or exotic options, implied volatility solving, or option quotes.
---

# Risk Derivatives

Three functions share one book contract. MCP tools `risk_derivatives_greeks`, `risk_derivatives_grid` and `risk_derivatives_historical`; CLI `riskdesk derivatives-greeks`, `riskdesk derivatives-grid` and `riskdesk derivatives-historical`, each with `--input PATH`.

| question | function | extra input |
|---|---|---|
| exposures now | `book_greeks` | none |
| what if spot and vol jump | `scenario_grid` | `spot_shocks`, `vol_shocks` |
| historical VaR and ES with options | `historical_pnl` | `scenarios`, `horizon_days`, `time_mode`, `confidence`, `portfolio_value` |

## The book contract

Provenance as in [input contracts](../../references/contracts.md): `as_of`, `currency`, `source`, `data_mode`. Then:

- `underlyings`: name to `{price, price_type}`. `price_type` is `spot` (priced with Black-Scholes-Merton) or `future` (Black-76). Options on two futures expiries are two underlyings.
- `positions`: each has a unique `id`, `underlying`, `instrument_type` (`linear` or `option`), signed `quantity` and a required `multiplier`. There is no default multiplier, because a missing 100 is a hundredfold error.
- An option also needs `kind` (`call` or `put`), `strike`, `implied_vol` per 1.00 (0.20, not 20), `rate` continuously compounded per 1.00, and exactly one of `expiry` (a date after `as_of`) or `year_fraction` (ACT/365 years). An option on a spot underlying needs `carry_yield` (dividend or carry, 0 if none). An option on a future must not have one.
- A linear position has no option terms. Its P&L is quantity x multiplier x price change, for spot holdings and futures alike.

Every price is in the stated currency already. No market value is fetched or filled in. If a field is missing, ask for that field.

## What to report first

1. `degraded` and `degraded_reason`, before any number. Only `historical_pnl` can be degraded, and only through `tail_risk`'s small-tail warning.
2. Currency, `as_of`, `source`, `data_mode`. Synthetic examples are not market data.
3. For `historical_pnl`: `time_mode` and `horizon_days`, `scenarios_without_vol_changes`, and `options_settled_within_horizon`. Each one changes what the VaR means.

## Units and signs

| field | unit |
|---|---|
| `cash_delta` | currency per 1.00 relative move: delta x quantity x multiplier x price |
| `cash_gamma_1pct` | change in `cash_delta` for a 1% rise: gamma x quantity x multiplier x price squared / 100 |
| `vega_per_vol_point` | currency for +0.01 of implied vol. The engine's vega is per 1.00, so this divides it by 100 |
| `theta_per_day` | currency as one calendar day passes, the engine's convention. Negative is decay |
| `rho_per_rate_point` | currency for +0.01 of the rate. The engine's rho is per 1.00 |

Positive P&L is profit, and `full_loss` is minus `full_pnl`. The tail block keeps `tail_risk`'s convention: VaR and ES are losses, and a negative value is a gain. Approximation error is approximation minus full revaluation.

## What not to claim

- Totals add the underlyings. Total gamma has no cross-gamma, and total vega means every vol moves by one point together.
- Delta-gamma-vega has no vanna or vomma. A large `delta_gamma_vega_error` is the approximation failing, not a pricing fault.
- Grid cells move every underlying by the same relative shock and every vol by the same absolute shift. They are not correlated scenarios.
- `time_mode: fixed` excludes theta over the horizon. `decay` includes it. Say which one was used.
- An option whose life ends inside the horizon is valued at its undiscounted payoff on the shocked price. It is not rolled.
- Model values are not quotes or fills. European exercise and one flat vol per option are assumed.
- Historical VaR is not a forecast and not risk-neutral valuation. Do not scale a one-day result to ten days.
- Black-76 rho is -t x V with the future held fixed, from the engine's `black76_greeks` (optiondesk-engine commit 4a282d9 or later). See reference.md.

## Going deeper

- `reference.md`: every formula, the engine conventions inherited, Black-76 rho, and the sources.
- `workflows/greeks-to-tail.md`: the order to run the three functions in and what to check.
- `scripts/check_artifact.py`: a one-line verdict on a saved result.
