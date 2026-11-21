---
name: risk-liquidity
description: Estimate days to liquidate each asset at a participation rate of average daily traded value, the schedule of what is still held by day, the exogenous bid-ask spread cost of liquidation, and liquidity-adjusted VaR after Bangia, Diebold, Schuermann and Stroughair (1999). Use when the user asks how long a book takes to exit, how much is still held after n days, or what the spread adds to VaR. Not for market impact of large orders and not for recommendations.
---

# Risk Liquidity

Use `risk_liquidity`; the CLI equivalent is `riskdesk liquidity --input PATH`.

## Contract

A PortfolioRequest ([input contracts](../../references/contracts.md)) plus:

- `participation_rate`: fraction of average daily traded value the book may
  take each day, above 0 and at most 1.
- `spread_multiplier`: the scaling factor a on spread volatility. A user
  input with no default.
- `liquidity`: for exactly every portfolio asset, `average_daily_value`
  (traded value per day in the base currency, positive),
  `mean_relative_spread` and `spread_volatility` (relative spread is
  (ask - bid) / mid, so 0.002 is 20 basis points).
- Optional, all three together: `pnl`, `confidence`, `horizon_days`, as in
  TailRequest. With them the result includes liquidity-adjusted VaR.

## Report first

1. `degraded` and `degraded_reason`. It names every asset that takes
   longer to exit than the VaR horizon.
2. `max_days_to_liquidate` and the slowest assets from `by_asset`.
3. The schedule at the days the user cares about (`held_value`,
   `held_fraction`).
4. `cost_of_liquidity`, and when present `var` and
   `liquidity_adjusted_var` with `confidence` and `horizon_days`.

## Sign conventions

Cost of liquidity and VaR are losses and positive. Short positions cost
the half spread too: values are absolute. Days are days of average
traded volume, not calendar days.

## What not to claim

- Horizon scaling is never done silently: VaR is at the P&L horizon, the
  spread cost is a one-off exit cost, and neither is rescaled to the
  liquidation period. When an asset takes longer to exit than the horizon,
  say so; the L-VaR does not cover the extra days.
- The spread add-on is exogenous: market-wide spread risk. It is not the
  price impact of selling a large block, which can be far larger.
- The L-VaR here adds the spread cost to historical VaR; the 1999 paper
  used parametric VaR. The spread cost is their equation (4); the plain
  sum with VaR is confirmed only from a secondary source (reference.md).
- Do not present the paper's empirical range for a as a default. Ask the
  user for a, and say what it was.
- Liquidity inputs must be the user's; never invent volumes or spreads.

## Going deeper

- `reference.md`: formulas, the source and page of each, and what is not
  verified from the primary text.
- `workflows/liquidity-report.md`.
- `scripts/check_artifact.py RESULT.json`: re-derives days, the schedule,
  the spread cost and L-VaR, and prints a one line verdict.
