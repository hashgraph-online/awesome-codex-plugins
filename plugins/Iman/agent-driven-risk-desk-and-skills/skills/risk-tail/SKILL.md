---
name: risk-tail
description: Calculate VaR and Expected Shortfall from supplied horizon P&L, either historical only (risk_tail) or side by side under normal, Student-t, extreme value, GARCH filtered historical, GARCH-EVT and GARCH-t Monte Carlo models (risk_tail_models). Use for loss quantiles, tail severity and model comparison, not for counterparty XVA and not for testing a forecast record (use risk-backtest).
---

# Risk Tail

Two tools share the TailRequest contract in [input contracts](../../references/contracts.md).

| tool | CLI | what it returns |
|---|---|---|
| `risk_tail` | `riskdesk tail --input PATH` | historical VaR and ES via skfolio |
| `risk_tail_models` | `riskdesk tail-models --input PATH` | the historical result plus six model estimates of the same quantities |

Require the currency, as-of date, source, data mode, portfolio value, confidence and horizon. Each P&L observation must already cover that horizon. Do not convert daily results to another horizon by silently scaling them. For `risk_tail_models` the P&L must be in time order, oldest first: the GARCH columns depend on order, the others do not.

## Report first

1. `degraded` and `degraded_reason`, before any number.
2. Every entry in `unavailable` with its reason. A missing column is not a zero.
3. Then VaR and ES per method as monetary losses in the stated currency.

`garch.converged` false means the GARCH-t posterior failed Option Desk's split R-hat or effective sample size gate. The result is then degraded and the three GARCH columns must be described as unreliable.

## Sign conventions

Loss is positive. Negative VaR or ES means a gain at that quantile. Values are not floored at zero. Per-method parameters (`mean_loss`, `std_loss`, `loc`, `scale`, `threshold`, `beta`, `sigma_next`) are in units of loss divided by portfolio value; for `garch_evt` the threshold and `beta` are in standardised residual units.

## What not to claim

- None of these is a validated forecast. Disagreement between columns is model risk, not an error to average away. To test a forecast record, use risk-backtest.
- Do not call ES the mean of all losing observations.
- The small-tail warning is a reporting rule, not a confidence test.
- EVT with fewer than 50 exceedances is flagged; do not present it as robust.
- Unconditional EVT and the normal and Student-t fits ignore volatility clustering. The GARCH columns are one sample period ahead of the last observation and say nothing about longer horizons.
- These are research results, not investment advice and not a regulatory capital figure.

## Going deeper

- `reference.md`: every formula, its source, and what is refused.
- `workflows/compare-tail-models.md`: the order to run and read the comparison.
- `scripts/check_artifact.py`: run it on a saved result for a one line verdict.
