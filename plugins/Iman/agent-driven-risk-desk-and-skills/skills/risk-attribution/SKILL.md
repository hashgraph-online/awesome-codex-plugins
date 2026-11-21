---
name: risk-attribution
description: Estimate an asset covariance matrix from a supplied return history (sample, EWMA or Ledoit-Wolf), split portfolio VaR and Expected Shortfall into per-position Euler contributions (parametric normal, and historical-simulation ES), give incremental VaR per position, and regress asset returns on supplied factor returns to split portfolio variance into systematic and idiosyncratic parts. Use when the user asks which positions drive the risk, what a position adds to VaR or ES, what the covariance or correlation of a history is, or how much risk is factor risk. For a portfolio VaR or ES total from P&L alone use risk-tail; for gross and net exposure use risk-portfolio; for scenario shocks use risk-stress.
---

# Risk Attribution

Four calculations, each a pure function over supplied data. None fetches
market data. Contracts and every formula, with its source, are in
`reference.md`.

| question | MCP tool | CLI |
|---|---|---|
| covariance, volatility, correlation of a history | `risk_covariance` | `riskdesk covariance --input PATH` |
| which positions drive normal VaR and ES, and what removing one changes | `risk_var_attribution` | `riskdesk var-attribution --input PATH` |
| which positions drive historical ES | `risk_es_attribution` | `riskdesk es-attribution --input PATH` |
| factor betas and systematic versus idiosyncratic variance | `risk_factor_exposure` | `riskdesk factors --input PATH` |

Worked inputs: `examples/decomposition_covariance.json`,
`examples/decomposition_parametric.json`, `examples/decomposition_historical.json`,
`examples/decomposition_factor.json`. All four are synthetic.

## Inputs you must have before calling

Currency, as-of date, source, data mode, and the horizon each return row
spans. Positions are signed market values already in the base currency, each
with `instrument_type: linear`, and each naming an asset that appears in
`assets`. Return rows are simple returns, oldest first, one column per asset.
Never invent a missing return, covariance entry, factor return or decay. If
the user did not give an EWMA decay, ask for it. The tool has no default.

## What to report first

1. `degraded` and `degraded_reason`, before any number.
2. Currency, horizon in days, as-of date, method, and observations used.
3. The total (VaR, ES or variance), then the contributions.

## Sign conventions

Loss is positive. A negative contribution means the position lowers
portfolio risk at the margin: it is a hedge in this book. A percentage
contribution above 100 percent is possible when other positions offset it.
Marginal VaR and ES are per 1 unit of currency added to that position.
Factor exposure is currency P&L per 1.00 (100 percent) factor return.

## What the numbers add up to

Component VaR sums to VaR, component ES sums to ES, percentages sum to one,
and systematic plus idiosyncratic variance equals the sample variance of
portfolio P&L. `scripts/check_artifact.py` checks these sums in one line.
Incremental VaR does not sum to VaR, and is not meant to.

## What not to claim

- Parametric results assume normal P&L with zero mean. They are not
  historical VaR. Quote them as "normal VaR" and do not mix them with
  `risk_tail` figures in one sentence without naming both methods.
- A covariance flagged not positive definite was not repaired. Say so, and
  offer `ledoit_wolf` rather than altering the matrix by hand.
- When historical ES is degraded for a tied tail boundary, the total is
  sound but the split between positions depends on input order.
- R squared and the variance split are in-sample. They are not forecasts,
  and factor betas from a short history are noisy.
- None of this is regulatory capital, a validated model, or advice.

## Going deeper

- `reference.md`: request contracts, every formula and sign convention,
  and the paper or document behind each one with its section and equation.
- `workflows/decompose-portfolio-risk.md`: the order to run the tools in and
  what to check before reporting.
- `scripts/check_artifact.py`: run it on a saved result for a one line
  OK, DEGRADED or FAIL verdict.
