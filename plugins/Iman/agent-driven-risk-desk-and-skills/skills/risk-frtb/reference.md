# Reference: formulas, constants and sources

Source: Basel Committee on Banking Supervision, consolidated Basel Framework,
read at bis.org on 2026-11-04. Versions read:

| Chapter | In force | Published (last update) |
|---|---|---|
| MAR21 Standardised approach: sensitivities-based method | 2023-01-01 | 2026-03-23 |
| MAR32 Internal models approach: backtesting and PLA test | 2023-01-01 | 2020-03-27 |
| MAR33 Internal models approach: capital requirements calculation | 2023-01-01 | 2020-06-05 |

The formulas on bis.org are images. Each one used here was rendered and read
from the image itself, not from a summary.

## IMA: liquidity-adjusted ES (MAR33.4)

T = 10 days. LH_j for j = 1 to 5 is 10, 20, 40, 60 and 120 days (MAR33.4
Table 1).

ES = sqrt( ES_T(P)^2 + sum over j >= 2 of ( ES_T(P, j) * sqrt((LH_j - LH_{j-1}) / T) )^2 )

ES_T(P, j) shocks only the risk factors whose liquidity horizon is at least
LH_j, with all other factors held constant. The input cascade is
[ES_T(P), ES_T(P,2), ES_T(P,3), ES_T(P,4), ES_T(P,5)]. ES is at 97.5%
(MAR33.3). The cascade weights are therefore 1, 1, 2, 2 and 6 on the squared
terms. A book whose factors all have one horizon LH reduces to
ES_T * sqrt(LH / 10); the tests check that closed form for every horizon.
Assigning factors to horizons follows MAR33.12 Table 2, which is the
caller's job.

## IMA: stress calibration (MAR33.6) and IMCC (MAR33.15)

ES = ES_R,S * ES_F,C / ES_R,C. "For the purpose of this calculation, this
ratio is floored at 1" (MAR33.6). Each of the three is a liquidity-adjusted
ES from its own cascade.

IMCC = rho * IMCC(C) + (1 - rho) * sum over i = 1..B of IMCC(C_i), with rho = 0.5
(MAR33.15). IMCC(C) uses the portfolio's ES_R,S, ES_F,C and ES_R,C.
IMCC(C_i) uses the same three for broad risk class i alone, with all other
factors held constant (MAR33.14). The classes are interest rate, equity, FX,
commodity and credit spread.

Interpretation: the floor at 1 is applied to each class ratio as well as the
portfolio ratio. MAR33.15 does not repeat the floor. MAR33.6 states it for
the ES used for capital, and IMCC(C_i) is built from the same ratio. The
MAR33.15 FAQ formulas are stripped from the bis.org page, so they could not
be checked.

## IMA: aggregation (MAR33.41 to MAR33.46)

C_A = max{ IMCC_{t-1} + SES_{t-1} ; m_c * IMCC_avg + SES_avg } (MAR33.41,
averages over the previous 60 days). The multiplier scales the IMCC average
only. The paragraph's prose says "weighted average"; the formula shows an
average. The averages are inputs, so this module takes no position on the
weighting.

m_c = 1.5 plus the backtesting add-on plus any qualitative add-on (MAR33.42).
The backtesting value comes from MAR32.9 Table 1, from the bank-wide 99%
VaR exceptions over 250 observations:

| Exceptions | 0 to 4 | 5 | 6 | 7 | 8 | 9 | 10 or more |
|---|---|---|---|---|---|---|---|
| Zone | green | amber | amber | amber | amber | amber | red |
| Multiplier | 1.50 | 1.70 | 1.76 | 1.83 | 1.88 | 1.92 | 2.00 |

DRC = max(12-week average, most recent) (MAR33.22).

IMA_G,A = C_A + DRC (MAR33.43).

k = 0.5 * (sum of SA_i over amber desks) / (sum of SA_i over green and amber
desks) (MAR33.45).

Capital surcharge = k * max{0, SA_G,A - IMA_G,A} (MAR33.45). It is added
only if at least one desk is amber (MAR33.43); with no amber desk, k is 0.

ACR_total = min{ IMA_G,A + capital surcharge + C_U ; SA_all desks } + max{ 0 ; IMA_G,A - SA_G,A } (MAR33.43)

RWA = 12.5 * capital (MAR33.46).

Refused: an amber desk with positive SA when the desk SA sum is zero, since
k would be undefined. An amber SA of zero gives k = 0.

## Backtesting (MAR32.3 to MAR32.19)

- One-day VaR against actual (APL) and hypothetical (HPL) P&L over 12
  months, "ie 250 trading days" (MAR32.3, MAR32.4).
- Exception: loss greater than VaR. APL and HPL exceptions are counted
  separately and the greater is used. A missing P&L or VaR counts as an
  outlier (MAR32.5 bank-wide, MAR32.18 desk).
- Bank-wide: 99% VaR; zone and multiplier from MAR32.9 Table 1 above.
- Desk: VaR at both 97.5% and 99% (MAR32.18). The desk moves to the
  standardised approach if it "experiences either more than 12 exceptions at
  the 99th percentile or 30 exceptions at the 97.5th percentile" (MAR32.19).
  Applied as: passes when the 99% count is at most 12 and the 97.5% count is
  at most 30. This reads "more than" across both limits. EU CRR Article
  325bf(3), read on gesetze.legal on 2026-11-04, says the same thing in
  German: a desk meets the requirement with no more than 12 exceptions at
  99% and 30 at 97.5% over the preceding 250 business days. That is EU law,
  not BIS text.
- Not applied: disregarding an exception driven by a non-modellable risk
  factor (MAR32.6), which needs a supervisor's non-objection.

## P&L attribution test (MAR32.34 to MAR32.42)

- 250 most recent daily RTPL and HPL observations (MAR32.35).
- Spearman: rank each series (lowest is 1) and take the Pearson correlation
  of the ranks (MAR32.36 to MAR32.38). Ties are not specified by the text;
  scipy `spearmanr` gives tied values their average rank.
- KS: each empirical CDF is 0.004 times the number of observations at or
  below a value. The metric is the largest absolute difference (MAR32.39 to
  MAR32.41). With exactly 250 observations, 0.004 is 1/n, so this equals
  scipy's two-sample KS statistic. The zone is decided on the integer count
  (KS divided by 0.004) so boundaries are exact.
- Zones (MAR32.42 Table 2):

| Zone | Rule |
|---|---|
| green | Spearman above 0.80 and KS below 0.09 (p-value 0.264) |
| red | Spearman below 0.70 or KS above 0.12 (p-value 0.055) |
| amber | neither |

  So Spearman of exactly 0.80 is amber, KS of exactly 0.12 is amber, and
  Spearman of exactly 0.70 is amber.

## SBM: aggregation (MAR21.4, MAR21.6, MAR21.7)

- Net sensitivity per risk factor: s_k (MAR21.4(2)). Weighted sensitivity
  WS_k = s_k * RW_k (MAR21.4(3)).
- Within a bucket (MAR21.4(4)): K_b = sqrt( max(0, sum WS_k^2 + sum over k != l of rho_kl WS_k WS_l) ).
- Across buckets (MAR21.4(5)): S_b = sum of WS_k in b, and the charge is
  sqrt( sum K_b^2 + sum over b != c of gamma_bc S_b S_c ). If the sum under
  the root is negative, use S_b = max(min(sum WS_k, K_b), -K_b) instead
  (MAR21.4(5)(b)). If it is still negative, the result is refused. The text
  gives no further rule.
- Correlation scenarios (MAR21.6): medium uses rho and gamma as specified.
  High multiplies them by 1.25, capped at 100%. Low uses max(2 x rho - 100%,
  75% x rho), and likewise for gamma.
- Total (MAR21.7): for each scenario, sum delta, vega and curvature over the
  risk classes. The capital is the largest of the three scenario totals, not
  the sum of per-component maxima.

## SBM: FX delta (MAR21.86 to MAR21.89)

- One bucket per exchange rate between an instrument's currency and the
  reporting currency (MAR21.86). Each bucket holds one delta factor, so
  K_b = |WS_b|.
- Risk weight 15% (MAR21.87). At the bank's discretion it is divided by
  sqrt(2) for the specified pairs and their first-order crosses (MAR21.88).
  Footnote 22 lists them against USD: EUR, JPY, GBP, AUD, CAD, CHF, MXN, CNY,
  NZD, RUB, HKD, SGD, TRY, KRW, SEK, ZAR, INR, NOK, BRL. Footnote 23 gives
  EUR/AUD as a first-order cross. Implemented as: both currencies of the pair
  are in that list or are USD.
- Across buckets: gamma = 60% (MAR21.89).
- The delta sensitivity definition (MAR21.24) is the caller's job.

## SBM: FX vega (MAR21.14(2), MAR21.91 to MAR21.95)

- Same buckets as delta (MAR21.91). Factors are implied volatilities by
  option maturity, mapped to 0.5, 1, 3, 5 or 10 years (MAR21.14(2)).
- Risk weight 100% (MAR21.92 Table 13: FX, liquidity horizon 40). The table
  states the resulting weight, so the footnote 24 formula is not re-derived.
- Within a bucket (MAR21.94): rho_kl = min( rho_delta * rho_option_maturity ; 1 ),
  with rho_option_maturity = exp(-alpha * |T_k - T_l| / min(T_k, T_l)) and
  alpha = 1% (MAR21.93). rho_delta is the delta correlation between the
  corresponding delta factors. In one FX bucket that is the same exchange
  rate, so it is 1.
- Across buckets: the delta gamma, 60% (MAR21.95).
- The vega sensitivity definition (MAR21.25) is the caller's job.

## Left out, and why

| Piece | Paragraphs | Why |
|---|---|---|
| SBM curvature | MAR21.5, MAR21.96 to MAR21.101 | Not implemented in this pass; the formula images were not all read. FX results with vega are flagged degraded. |
| SBM GIRR, CSR, equity, commodity | MAR21.39 to MAR21.85 | One risk class first, as briefed; FX was completed. |
| Standardised DRC, RRAO | MAR22, MAR23 | Not read. |
| NMRF stress scenario capital | MAR33.16, MAR33.17 | Taken as an input (SES). |
| IMA default risk model | MAR33.18 to MAR33.39 | Taken as an input (DRC). |
| 10% eligibility criterion | MAR32.2 | Needs the full capital split; not computed. |
| PLA zone transitions | MAR32.43, MAR32.44 | Need history across quarters. |
