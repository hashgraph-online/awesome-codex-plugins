# Workflow: compare tail models on one P&L history

1. Confirm the input: currency, as-of date, source, data mode, portfolio value, confidence and
   the horizon each P&L sample covers. Confirm the series is in time order, oldest first.
   Do not scale a daily series to a longer horizon.
2. Run `risk_tail_models` (CLI `riskdesk tail-models --input PATH`). A synthetic input that
   already fits the contract: `examples/energy_tail.json`. Expect a few seconds; the GARCH fit
   is a Markov chain sampler.
3. Save the result and run `python3 scripts/check_artifact.py result.json`. Stop on FAIL.
4. Read `degraded_reason` and `unavailable` and say them first.
5. If `garch.converged` is false, say the three GARCH columns are unreliable before quoting them.
6. Present one table: method, VaR, ES, in the stated currency, positive meaning loss.
7. Comment only on what the table shows: which columns are higher, and that the GARCH columns
   react to recent volatility (`sigma_next`) while the others weight all history equally.
   Do not pick a "correct" model from one table; that needs risk-backtest on a forecast record.
