# Reference: liquidity formulas and sources

## Notation

| symbol | field | meaning |
|---|---|---|
| V_a | by_asset.gross_value | sum of absolute market values held in asset a |
| ADV_a | average_daily_value | average daily traded value of a, base currency |
| q | participation_rate | fraction of ADV taken per day |
| S_a | mean_relative_spread | mean of (ask - bid) / mid |
| sigma_a | spread_volatility | volatility of the relative spread |
| a | spread_multiplier | scaling factor on spread volatility |

## Days to liquidate and the schedule

Daily capacity c_a = q x ADV_a. Days to liquidate D_a = V_a / c_a.
Held on day d (end of day, d = 0 .. ceil(max D_a)):
H(d) = sum_a max(0, V_a - c_a d). Each asset sells at its capacity until
done; prices stay at as-of values.

Positions in one asset share its volume, so V_a is the sum of absolute
values; a long and a short in the same asset are not crossed internally.

This is the desk's definition (participation-rate liquidation). It uses no
published constant. A liquidation taking more than 3650 days is refused as
a probable unit error, the same ten year bound TailRequest puts on
`horizon_days`.

## Exogenous cost of liquidity

Bangia, A., Diebold, F. X., Schuermann, T. and Stroughair, J. D.,
"Modeling Liquidity Risk, With Implications for Traditional Market Risk
Measurement and Management", NYU Stern working paper 99-062, draft of
21 December 1998, Section III.B "Incorporating Exogenous Liquidity Risk",
equation (4), page 6:

COL = 1/2 [ P_t ( S + a sigma ) ]

"where P_t is today's mid-price for the asset or instrument, S is the
average relative spread (where relative spread ... is defined as
[Ask-Bid]/Mid), sigma is the volatility of relative spread, a is the
scaling factor such that we achieve roughly a 99% probability coverage."

Here P_t is replaced by the mid value of the holding, V_a, so
COL_a = 1/2 V_a (S_a + a sigma_a), and the total is the sum over assets.

The same page reports that "a ranges from 2.0 to 4.5 depending on the
instrument and market in question", because spread distributions are far
from normal. That is an empirical finding for their instruments, not a
default; Risk Desk requires a from the user.

Copy read: https://archive.nyu.edu/bitstream/2451/27135/2/wpa99062.pdf,
6 pages, sha256 f44e2fd64bd071437b1c598068383bbc52c18ef8869611e87594776582ce4ca9.
The same paper is listed by RePEc IDEAS as Wharton Financial Institutions
Center working paper 99-06 (https://ideas.repec.org/p/wop/pennin/99-06.html).

## Liquidity-adjusted VaR

L-VaR = VaR + sum_a COL_a, with VaR the historical VaR of the supplied P&L
(computed by `tail_risk`, identical to `risk_tail`).

Source status: the copy read above ends at page 6 and does not contain the
paper's L-VaR equation. The additive form is confirmed from a secondary
source: Qi, J. and Ng, W. L., "Liquidity Adjusted Intraday Value at Risk",
Proceedings of the World Congress on Engineering 2009, Vol II, London,
pages 1337 to 1343, page 1337: "The LAVaR simply equals the sum of conventional VaR (computed
by mid-price) and the liquidity risk adjusted part (computed by ask-bid
spread)." Any correlation correction the original paper applies to this
sum is not verified and not implemented.

The paper's market VaR is parametric (its equation (3)); here it is
historical. Both P&L and spread statistics must describe the same
horizon; nothing is rescaled.

## Not modelled

Endogenous liquidity (price impact beyond the quoted depth), time-varying
spreads during the liquidation, and the market risk of positions still held
after the VaR horizon. The result names assets whose D_a exceeds the
horizon in `degraded_reason`.
