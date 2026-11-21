# Reference: the twenty-three structures and what each needs

## Single expiry

| structure | type | needs | pays when |
|---|---|---|---|
| long_call | debit | strong bullish | a large move up |
| long_put | debit | strong bearish | a large move down |
| bull_call_spread | debit | mild bullish | a normal move up |
| bear_put_spread | debit | mild bearish | a normal move down |
| bull_put_spread | credit | mild bullish to neutral | the price not falling through the short put |
| bear_call_spread | credit | mild bearish to neutral | the price not rising through the short call |
| cash_secured_put | credit | neutral to mild bullish | anything but a large fall |
| covered_call | credit | neutral to mild bullish | sideways, with the underlying held |
| protective_put | debit | either extreme | a fall, while keeping the upside |
| straddle | debit | either extreme | a large move, direction unknown |
| strangle | debit | either extreme | a larger move, more cheaply |
| iron_condor | credit | range bound | the price staying inside the wings |
| iron_butterfly | credit | pinned | the price finishing near one strike |
| long_call_butterfly | debit | pinned | the price finishing near the body |
| ratio_spread | credit | a rise that stops short of the short strikes | the price ending near the short strike, and it loses without limit above |
| broken_wing_butterfly | credit | pinned, with one side you do not fear | the price finishing near the body, with no loss on the unfeared side |
| jade_lizard | credit | neutral to mildly bullish, volatility rich | the price staying above the short put, with no upside risk when the credit exceeds the call width |

## Two expiries

| structure | type | needs | pays when |
|---|---|---|---|
| calendar_spread | debit | the price sitting still | the near leg decays faster than the far, call side |
| calendar_put_spread | debit | the price sitting still | the same trade on the put side, where the skew is usually richer |
| diagonal_spread | debit | a drift toward the short strike | decay plus an upward lean |
| diagonal_put_spread | debit | a drift toward the short strike | decay plus a downward lean |
| ratio_call_diagonal | debit | a rise, without the cap a 1x1 imposes | the back-month longs outrun the fewer front-month shorts |
| ratio_put_diagonal | debit | a fall, without the cap a 1x1 imposes | the back-month longs outrun the fewer front-month shorts |

A calendar's payoff is a curve, not line segments, because the far leg is
still alive when the near one expires. Its maximum gain and loss are found
by scanning a range and are reported with the range that was scanned.

The two ratio diagonals differ from the plain diagonal in one measurable
way rather than in emphasis. A 1x1 diagonal can be too right: past the
short strike the long leg's time value drains against the short's
intrinsic and the position hands profit back. The ratio versions hold more
back-month CONTRACTS than front-month ones, which is what leaves the move
uncapped, and both plans report `delta_ratio` and `giveback` so the
difference can be read rather than believed.

Three checks stand between a caller and a structure that would misdescribe
itself, and they read different things: the contract count, which is the
one that carries the property; the entry-time delta split; and the slope
of the payoff at the edge of the scanned range. An earlier version of this
page credited the delta split alone, which an audit falsified by building
a net short call that satisfied it.

## The five directions

Anchored on the one standard deviation expected move, not on an opinion:
strong bearish and strong bullish sit outside the band, mild bearish, mild
bullish and neutral sit inside it. A spread reaches its maximum on a normal
move; a naked long option needs an extreme one. That is the whole reason a
professional prefers the spread.

## Friction verdicts

ok, under 10 percent of the premium; thin, up to 25 percent, the edge must
be real to survive; untradeable, above that, or a leg quoting wider than 40
percent of its own mid, or a leg with no bid at all. Untradeable structures
are excluded from any ranking.

## Fields that are not numbers

max_gain and max_loss can be the string "unlimited". That is a fact about
the structure. Never render it as a number, and never substitute a large
one.

## Quote coverage and reported Greeks

The spread-cost estimate sums only option legs with bid/ask quotes. A
partially quoted structure can still receive an ok verdict. Check missing
quotes separately and do not present that cost as covering every leg.
Commission counts all option-leg quantities.

The engine netting helper includes veta. The strategy artifact helper
sums eight Greeks and omits veta; report only the fields present.
Single-expiry breakeven roots are rounded to six decimal places.
