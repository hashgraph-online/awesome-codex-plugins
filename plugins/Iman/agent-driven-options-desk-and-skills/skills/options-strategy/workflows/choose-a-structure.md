# Workflow: from a view to a structure

1. Turn the view into one of five directions. If the user gave a price
   target, the expected move decides which: outside the band is extreme,
   inside is mild, close to spot is neutral.
2. `optiondesk strategy --recommend N --vol-view crush|expand|neutral`,
   with N from -2 to +2. Add `--owns-underlying` if they hold the stock,
   `--direction-unknown` if they expect a move but not a direction.
3. Build the top candidates: `optiondesk strategy <name>`.
4. `optiondesk compare` for the whole table at once, ranked.
5. Report the shape, the breakevens, the maximum loss, and the friction
   verdict. Lead with what it costs to be wrong.

## Reporting rules

Never present the ranking as advice. State the criterion and the caveat
that comes with the artifact: a positive expectation here mostly measures
the gap between the model's single volatility and the market's smile.

Quote max_loss before max_gain. The loss is the number that decides
position size.

For a calendar or diagonal, say that the far leg is marked at today's
volatility and that this assumes away part of the trade.
