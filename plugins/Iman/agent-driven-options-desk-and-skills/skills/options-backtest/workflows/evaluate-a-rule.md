# Workflow: judging whether a result means anything

1. `optiondesk backtest SYM STRUCTURE --period 5y`
2. Read in this order: trade count, benchmark, p-value, interval, then the
   headline return. Reversing that order is how a backtest sells itself.
3. If it survives, register it forward: `optiondesk forward open
   --strategy STRUCTURE --thesis "why, in your own words"`.
4. Mark it as new chains arrive: `optiondesk forward mark`.

## The four questions, in order

Are there enough trades. Under thirty, stop.

How does it compare to holding the underlying over the same windows. A
structure that merely tracks the market is not a strategy.

Could chance produce this. Report the block sign-flip symmetry assumption,
block length and strategy-selection caveat. Block boundaries can lose
dependence. A block covering the sample gives no bootstrap variation; its
interval cannot support a conclusion.

What does it cost to be wrong. Maximum drawdown in risk units, and the
worst single trade.

## Never

Never quote a backtest return without the honesty statement. Never call a
result significant on a p-value alone when the rule was chosen after
looking at the data.
