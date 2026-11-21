# Reference: units, conventions and refusals

Loaded only when a number has to be interpreted or explained. Nothing here
is needed to run a command.

## Every field a ladder row carries

| field | meaning | unit |
|---|---|---|
| price | model value | underlying quote currency |
| delta | dV/dS | per 1.0 of underlying move |
| gamma | d2V/dS2 | delta change per 1.0 of move |
| vega | dV/dsigma | per 1.00 of volatility |
| theta | value change | per calendar day, negative is decay |
| rho | dV/dr | per 1.00 of rate |
| lam | elasticity, delta times spot over value | dimensionless |
| vanna | d2V/dS dsigma | per 1.0 and per 1.00 |
| vomma | d2V/dsigma2, also called volga | per 1.00 squared |
| charm | delta change | per calendar day |
| veta | vega change | per calendar day |
| speed | d3V/dS3 | gamma change per 1.0 of move |
| zomma | dGamma/dsigma | per 1.00 of volatility |
| color | gamma change | per calendar day |
| ultima | d3V/dsigma3 | per 1.00 cubed |
| dual_delta | dV/dK | per 1.0 of strike |
| dual_gamma | d2V/dK2 | per 1.0 of strike squared |
| iv | implied volatility | per 1.00, so 0.20 is 20 percent |
| moneyness | strike over spot | dimensionless |

## The two conversions people get wrong

Vega is per 1.00 of volatility. Divide by 100 for the per-point figure a
trading screen shows. A vega of 70 means 0.70 per volatility point.

Theta, charm, veta and color are per calendar day, not per year and not per
trading day. They are already divided by 365.

## Signs that are not invariants

Theta is normally negative for a long option and is not always: a deep in
the money European put, or a call where the dividend yield exceeds the
rate, can carry positive theta. Charm and color change sign within a single
expiry. Do not extrapolate "negative means decay" from theta to the others.

## What the model assumes

European exercise, continuous dividend yield, ACT/365 time, and each
contract priced at its own stored implied volatility. No early exercise, no
discrete dividends, no borrow cost.

## What is refused rather than estimated

A contract whose price carries no volatility information gets iv null and
is counted in skipped.no_iv. This includes anything dominated by intrinsic
value, where every volatility in the range reprices within tolerance and
the price identifies none of them. The solver returns nothing rather than
its own starting guess, and the ladder skips the contract rather than
inventing a complete and entirely fictional row.

Volatility above 1000 percent or time beyond a century is refused as a unit
error, because those are what a percentage or a day count looks like when
it reaches a function expecting per 1.00 and years.

## IV output precision

The solver tests price residual and identifiability at its internal IV
candidate, then rounds the returned IV to six decimal places. Repricing
that rounded value need not satisfy the original price tolerance.
