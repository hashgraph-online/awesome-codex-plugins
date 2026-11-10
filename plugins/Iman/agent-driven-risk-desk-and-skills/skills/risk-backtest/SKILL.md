---
name: risk-backtest
description: Backtest a supplied VaR forecast series, and optionally an Expected Shortfall series, against realised P&L. Reports exceptions, the Kupiec proportion-of-failures test, the Christoffersen independence and conditional coverage tests, the Basel MAR99 traffic-light zone for one-day 99% VaR, and the Acerbi-Szekely Z2 ES test with a seeded simulated p-value. Use to judge a forecast record, not to compute VaR (use risk-tail).
---

# Risk Backtest

Tool `risk_backtest`, CLI `riskdesk backtest --input PATH`.

## Contract (BacktestRequest)

Provenance fields as in [input contracts](../../references/contracts.md): `as_of`, `currency`,
`source`, `data_mode`. Then:

- `pnl`: realised P&L per period, positive is profit, time order, 2 to 10,000 rows.
- `var`: the VaR forecast for each row, positive is loss, made before that row's P&L was known.
- `confidence` (0 to 1, exclusive), `horizon_days` (positive integer).
- Optional ES test: `expected_shortfall` (same length, each positive and above its VaR), and
  `es_null`: `normal` or `student-t` with `es_null_dof` (above 1). `seed` (default 0).

Unknown fields, non-finite numbers and mismatched lengths are refused.

## Report first

1. `degraded` and `degraded_reason`.
2. Exceptions against expected exceptions (`exceptions`, `expected_exceptions`).
3. The Basel zone if present, or `basel_traffic_light_unavailable` if not.
4. Kupiec, Christoffersen independence, conditional coverage: statistic and p-value each.
5. The ES test, with its null family, simulations, seed and Monte Carlo standard error.

## Sign conventions

An exception is a realised loss strictly greater than VaR: -pnl > var. Z2 is zero in
expectation when the forecasts are right; negative values mean risk was understated, and the
p-value is the left tail.

## What not to claim

- A test that does not reject has not validated the model. Backtests with few expected
  exceptions have little power: say how many were expected.
- The Basel zone is the MAR99 supervisory classification for one-day 99% VaR. It is not a
  capital calculation, and this tool does not report a multiplier.
- The ES p-value is under the stated location-scale null implied by each day's VaR and ES, not
  under the forecaster's own model distribution. Say which null was used.
- Kupiec and Christoffersen p-values are asymptotic chi-square.
- Research output, not a regulatory submission and not investment advice.

## Going deeper

- `reference.md`: formulas, sources with paragraph, and what each check proves.
- `workflows/backtest-a-var-series.md`: step by step.
- `scripts/check_artifact.py`: one line verdict on a saved result.
