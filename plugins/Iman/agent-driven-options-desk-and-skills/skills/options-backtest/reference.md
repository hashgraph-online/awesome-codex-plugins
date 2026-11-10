# Reference: what a result here can and cannot support

## The honesty rule, in full

Underlying closes are real. Option premiums are Black-Scholes values at
trailing realised volatility. There is no spread, no slippage, no
assignment, no early exercise, no borrow cost and no margin. Entry and exit
are priced by the same model, so a backtest here cannot detect any edge
that comes from the market disagreeing with that model. What it measures is
a structure's payoff geometry against real moves.

Volatility for entry pricing comes from the trailing window only. Using the
volatility realised over the holding period would be lookahead and would
make every short premium structure look profitable.

## The statistics

One unit of capital at risk per trade, returns summed rather than
compounded, so the curve and the drawdown are in units of per trade risk.
Compounding would assume the whole account is risked on every trade.

The two-sided block sign-flip randomization test compares absolute means
under independently signed contiguous blocks. Its null requires invariance
under those block flips; a zero mean alone is insufficient.

Signs are flipped a BLOCK at a time, not a trade at a time, and the
bootstrap resamples blocks rather than single trades. The windows overlap:
a thirty day hold entered every five trading days shares twenty-five of its
thirty days with its neighbour, the measured autocorrelation is positive
through lag five and collapses at lag six, and the effective sample is 64
to 88 rather than 233. Flipping trades independently assumes an
independence the data does not have and understates the standard error by
about a factor of two. Correcting it moved four structures on this desk
from below 0.05 to above it, one of them from 0.0005 to 0.148.

The CLI summary carries `overlap_block` when significance is available.
The artifact stores `significance.block` and `interval.block` in available
results. Above one, report that the p-value uses block sign flips and the
trade count is not the count of independent observations.

The moving-block bootstrap resamples non-circular contiguous blocks.
Dependence is retained within blocks and can be lost at block joins.
The schedule-derived length does not guarantee calibrated coverage.
When block length reaches or exceeds the return count, every replicate
is identical and the interval has zero width. Its excludes_zero flag then
cannot support an inference. Neither method adjusts for strategy selection.

The benchmark holds the underlying over the same windows. A structure that
is simply long the market shows the market's drift, and without the
benchmark that drift gets credited to the strategy.

## The caveat that outranks all of them

A p-value is only a p-value for a hypothesis chosen before seeing the data.
A strategy selected because its backtest looked good has already spent its
degrees of freedom, and the number then understates how easily the result
could be chance.

Under thirty trades, decline to draw conclusions.

## Forward testing

Paper. Entry and marks are mid quotes, so a real entry would cross the
spread on every leg. What it removes is hindsight, not cost. A position
with any leg missing from the later chain is reported unmarkable rather
than marked at zero, because a missing wing marked at zero turns a losing
short spread into a full credit win.

## Current summary boundary

The median_return field selects the upper middle observation for an even
sample. It is not the midpoint median in that case. Do not describe it as
the conventional median until the runtime calculation is corrected.
