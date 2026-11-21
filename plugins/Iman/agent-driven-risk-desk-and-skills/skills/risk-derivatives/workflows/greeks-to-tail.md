# Workflow: from book Greeks to tail risk

Run in this order. Each step uses the same book, so a mistake caught in step 1 does not reach step 3.

1. Build the book. Check that every option has its multiplier, the right `price_type` for its underlying, vol per 1.00, and exactly one of `expiry` or `year_fraction`. Ask for any value that is missing. Do not supply one yourself.
2. Run `book_greeks`. Read `by_underlying` before `total`. If the cash delta sign is not what the holder expects, the book is probably wrong (a sign on `quantity`, or put and call swapped). Stop and ask before going further.
3. Run `scenario_grid` with the spot and vol shocks the question needs, for example spot -20% to +20% and vol -5 to +10 points. Report the full-revaluation P&L. Quote `max_abs_delta_gamma_error` and `max_abs_delta_gamma_vega_error` beside it, so the reader can see how far the Greeks alone would mislead.
4. Run `historical_pnl` with scenarios that each span `horizon_days`. Choose `time_mode` deliberately: `decay` to include carry over the horizon, `fixed` for an instantaneous shock. State the choice.
5. Report `degraded` first, then the tail block's VaR and ES as losses in the book currency, with the confidence, horizon and observation count. Name any `options_settled_within_horizon`, and the count of scenarios without vol changes.

## Before reporting

Run `python3 scripts/check_artifact.py RESULT.json` on each saved result. Report FAIL or DEGRADED in the same sentence as any number.
