# Workflow: pre-trade what-if

1. Start from the PortfolioRequest of the current book.
2. Add `trades`: one entry per proposed change, signed market value in the
   base currency. If the asset sits in more than one position, give the
   `position_id` the trade changes.
3. For stress, add `scenarios` that shock every asset held after the
   trades, including assets the trades open.
4. For tail, add `asset_returns` (one equal-length list per asset held
   before or after, each value a return over the horizon), `confidence`
   and `horizon_days`. Do not supply daily returns for a ten day horizon.
5. Add the `limits` to grade after the trades.
6. Call `risk_what_if` (or `riskdesk what-if --input PATH`), then
   `python3 scripts/check_artifact.py RESULT.json`.

## Before reporting

Lead with degraded status, then `change`, then `limits_after`.
State that the result is a revaluation at as-of prices with unchanged NAV
and no costs, and that tail figures assume P&L scales with position value.
Never present the after book as a recommendation.
