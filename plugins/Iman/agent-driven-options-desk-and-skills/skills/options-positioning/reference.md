# Reference: what the positioning numbers mean

## Gamma exposure

Per one percent move in the underlying, in quote currency:

    gamma * open_interest * multiplier * spot * spot * 0.01

Calls are counted positive and puts negative, which encodes the assumption
that dealers are long calls and short puts against the public. That is the
market convention and it is frequently wrong for a single name, especially
around events and in heavily retail traded tickers. Every wall moves with
that assumption.

Positive net exposure is read as hedging that dampens moves, negative as
hedging that amplifies them. That reading is an interpretation, not a
measurement.

## The walls and the flip

The call wall is the strike with the most positive call gamma, the put wall
the most negative put gamma. The flip is where the cumulative profile
crosses zero. There is often more than one crossing: the headline is the
one nearest spot and the rest are in gamma_flip_all. The cumulative profile
starts at the lowest listed strike rather than at zero, so extending the
strike ladder shifts the whole profile.

## Max pain

The strike at which all open contracts pay out least. It describes where
open interest sits. It is not a forecast, and the evidence that price
gravitates to it is thin. Quote it as a description or not at all.

## Smile geometry

at_iv is the volatility of the nearest listed strike, calls winning a tie.
The 25 delta risk reversal is put volatility minus call volatility, so a
positive number means the downside is bid, which is normal for an index.
The butterfly is the average wing minus the body. Wings must be within 0.10
of the target delta or they are reported absent rather than substituted.

The smile is absent when no graded contracts carry usable volatility.
The risk reversal and butterfly are null when either wing is absent.
A contract's volatility can come from a solved price, an accepted provider value or explicit user input.
Missing two-sided quotes do not by themselves establish which smile fields are unavailable.

Check the returned fields, coverage counts and timestamps before explaining a missing figure.
Report the artifact's degraded reason, including any disagreement with its data.
Without evidence for a session closure or provider problem, leave the cause unknown.

The expected range is spot plus and minus the expected move. It is an
arithmetic band on a lognormal, so it is floored at zero and flagged when
the floor bites.
