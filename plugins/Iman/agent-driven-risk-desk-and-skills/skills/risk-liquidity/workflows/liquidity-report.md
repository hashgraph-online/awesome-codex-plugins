# Workflow: liquidity report

1. Start from the PortfolioRequest of the book.
2. Ask the user for, per asset, average daily traded value in the base
   currency, mean relative spread and spread volatility, and their source
   and window. Never fill these in yourself.
3. Ask for the participation rate and the spread multiplier a. If the user
   wants guidance on a, quote reference.md (the paper's empirical range and
   why it is not a default) and let them choose.
4. If L-VaR is wanted, add `pnl`, `confidence` and `horizon_days`, with the
   P&L at that horizon.
5. Call `risk_liquidity` (or `riskdesk liquidity --input PATH`), then
   `python3 scripts/check_artifact.py RESULT.json`.

## Before reporting

Degraded status first, including any asset slower than the VaR horizon.
Give days to liquidate as days of average traded volume.
Give the spread cost and L-VaR with the multiplier and confidence used.
Say that price impact of large orders is not included.
