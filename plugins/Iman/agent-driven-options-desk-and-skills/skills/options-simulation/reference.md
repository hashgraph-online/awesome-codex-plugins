# Reference: the model, the diagnostics, and what they permit

## The model

GARCH(1,1) with standardised Student-t innovations:

    r = mu + sigma * z,  z standardised t with nu degrees of freedom
    sigma^2 = omega + alpha * residual^2 + beta * sigma^2

Volatility clusters and the tail is fatter than a normal admits. Estimated
by adaptive random walk Metropolis on the unconditional variance
parameterisation, which reduces the correlation between the level and the
persistence enough to lift effective sample size by a factor of ten or so.

Each simulated path selects a retained parameter draw. The fan includes
parameter uncertainty and conditional shocks; this does not establish
predictive calibration.

## Run time

(draws + burn) x chains iterations, each walking every observation. Pure
Python, single threaded, no progress output.

Measured, 18 core arm64, 1253 observations:

| draws | burn | chains | wall clock |
|---|---|---|---|
| 3000 | 1000 | 2 | about 8 seconds |
| 6000 | 2000 | 4 | about 27 seconds |

That is roughly 1.6 microseconds per iteration-observation on that machine.
Scale it by your own hardware and by your history length. Ten years of
daily data at 6000 draws across four chains is four times the work of the
second row.

The command warns before it starts. Nothing is wrong when it goes quiet.


## Diagnostics, and the gate

converged is true only when split R-hat is below 1.05 and effective sample
size is at least 100 on every parameter, and the sampler actually accepted
proposals. A chain that never moved used to pass; it now fails.

The effective sample size estimator truncates its autocorrelation sum,
which overstates for a badly mixing chain. Below about 30, do not trust the
number itself.

The reported value is the minimum estimate across single chains. That
operation does not remove bias from each truncated estimate or guarantee
a conservative result. Report the implemented diagnostic, not pooled or
tail ESS. The earlier factor-two claim was tied to a past posterior; its
underlying calculation was not reverified in the current math review.

## What the numbers are

Value at risk and expected shortfall are on the underlying's return over
the horizon, using a loss sign convention. Expected shortfall averages the
selected worst tail observations and is at least as large as value at risk.
Equal values can result from one tail observation or repeated values.
An all-gain sample can produce negative loss statistics. Fewer than two
tail observations triggers the insufficient-paths warning.

The code computes tail counts in binary floating-point arithmetic before
flooring. Near integer boundaries, this can select one fewer observation
than the real-arithmetic formula.

They are not drift free. On a live SPY fit the posterior median drift was
about 26 percent a year, so a 30 day value at risk of 3.92 percent sat only
that far below spot while the distance from the median down to the fifth
percentile was 6.98 points. Quote the median return beside the tail figure
or a reader will hear a narrower distribution than the model fitted.

## The comparison that matters

Probability of profit under realised volatility, next to the same
probability under implied. The gap is the market's forecast disagreeing
with the recent past. Neither side is the truth. Report it as a
disagreement, never as an edge.

## There are no antithetic pairs

Paths are independent draws, one posterior parameter set each. Artifacts
written before September 2026 carry `antithetic: true` and it was never
true: of ten thousand pairs, none shared a shock sequence, because the
shocks were drawn inside the sign loop and negating an independent
symmetric draw yields another independent draw. The construction did
nothing, and the test guarding it asserted the flag rather than the
property.

The current implementation uses independent draws. Antithetic partners
could share a parameter draw while preserving marginal parameter
uncertainty, but this implementation does not use that construction.
The relative contribution of parameter and shock uncertainty was not
established by the current review.

If you are reading an older artifact, treat that field as unreliable rather
than as history.

## Horizon, path filtering and sample means

The simulation CLI uses intrinsic option payoff at the requested horizon.
It rebuilds every option leg without its expiry and IV, so calendars and
diagonals lose surviving time value. These are payoff scenarios, not
time-aware marks of the saved plans.

Paths whose log price is non-finite or exceeds 700 are rejected and counted.
Extreme negative log prices can underflow to retained zero prices. These
numerical boundaries affect the retained sample.

For finite degrees of freedom and positive conditional variance,
exponentiated Student-t log returns have infinite untruncated mean price.
A finite sample average cannot establish a finite model expectation for
payoffs with nonzero upper-tail slope. Bounded payoffs avoid this issue;
probabilities and finite quantiles do not require a finite first moment.
The variance prior also uses a reference value estimated from the fitted
returns and is therefore data-dependent.
