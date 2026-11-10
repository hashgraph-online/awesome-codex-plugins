# Workflow: backtest a VaR (and ES) forecast series

1. Confirm the record: one row per period in time order, each VaR and ES made before that
   period's P&L, positive meaning loss, all in one currency and one horizon. Ask for any
   missing value; never fill one in.
2. For the ES test, ask which null family to use (`normal`, or `student-t` with a dof). If the
   forecaster's model is known, use its family. Keep `seed` at 0 unless asked.
3. Run `risk_backtest` (CLI `riskdesk backtest --input PATH`). A synthetic input:
   `examples/var_backtest_energy.json`.
4. Save the result and run `python3 scripts/check_artifact.py result.json`. Stop on FAIL.
5. Report, in this order: degraded status, exceptions against expected exceptions, the Basel
   zone or why it is withheld, the three likelihood ratio tests with p-values, then the ES test
   with its null, simulations and seed.
6. Interpret only what rejects. A non-rejection with few expected exceptions is weak evidence;
   say how many were expected.
