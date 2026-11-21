# Reference: SA-CCR and exposure profile formulas

Loaded only when a number has to be interpreted or defended.

Sources, read from bis.org on 4 November 2026:

- CRE52, Standardised approach to counterparty credit risk, version effective 1 January 2023,
  last updated 5 June 2020 (web chapter). Its formulas are images on the web page; they were
  read from those images.
- CRE53, Internal models method for counterparty credit risk, version effective 1 January 2023.
- CRE50, Counterparty credit risk definitions and terminology, version effective
  15 December 2019 (updated for the FAQ of 5 July 2024), chapter PDF.
- CRE99, Application guidance, version effective 1 January 2023, chapter PDF: the SA-CCR
  sample portfolios in CRE99.20 to CRE99.97 and the margin examples in CRE99.98 to CRE99.115.
- BCBS 279, The standardised approach for measuring counterparty credit risk exposures,
  March 2014 (revised April 2014), Annex 4a: the same five sample portfolios.

## Notation

V netting-set value, C haircut value of net collateral held, TH threshold, MTA minimum
transfer amount, NICA net independent collateral amount, M_i maturity, S_i and E_i start and
end of the referenced period, T_i latest exercise date, all in years. d adjusted notional, SD
supervisory duration, MF maturity factor, delta supervisory delta, D = d * MF * delta effective
notional, SF supervisory factor, rho supervisory correlation, sigma supervisory option
volatility, Phi standard normal distribution function.

## SA-CCR (CRE52)

| quantity | formula | paragraph |
|---|---|---|
| EAD | alpha * (RC + PFE), alpha = 1.4 | CRE52.1 |
| RC unmargined | max{V - C; 0} | CRE52.10 |
| RC margined | max{V - C; TH + MTA - NICA; 0} | CRE52.18 |
| margined cap | EAD no higher than the same set calculated unmargined | CRE52.2 |
| PFE | multiplier * AddOn_aggregate | CRE52.20 |
| multiplier | min{1; Floor + (1 - Floor) * exp((V - C) / (2 * (1 - Floor) * AddOn_aggregate))}, Floor = 5% | CRE52.23 |
| aggregate add-on | sum of asset class add-ons, no diversification | CRE52.25 |
| effective notional | D_i = d_i * MF_i * delta_i | CRE52.30 |
| supervisory duration | SD_i = (exp(-0.05 * S_i) - exp(-0.05 * E_i)) / 0.05, floored at ten business days; S_i = 0 once started | CRE52.34 |
| adjusted notional | IR and credit: notional * SD_i; fx: foreign leg in domestic currency; equity and commodity: price * units | CRE52.34 to 52.36 |
| delta, linear | +1 long, -1 short in the primary risk factor | CRE52.39 |
| delta, option | bought call +Phi(d1), sold call -Phi(d1), bought put -Phi(-d1), sold put +Phi(-d1), d1 = (ln(P/K) + 0.5 * sigma^2 * T) / (sigma * sqrt(T)) | CRE52.40 |
| negative rates | P and K both shifted by lambda | CRE52.40 FAQ2 |
| MF unmargined | sqrt(min{M_i; 1 year} / 1 year), M_i floored at ten business days | CRE52.48 |
| MF margined | 3/2 * sqrt(MPOR_i / 1 year) | CRE52.52 |
| MPOR floor | ten business days for daily margining, nine plus the remargining period otherwise | CRE52.50 |
| business days | 250 a year, so ten business days are 10/250 | CRE52.49, CRE52.53 |
| IR buckets | E_i under 1 year, 1 to 5 years, over 5 years | CRE52.57 step 3 |
| IR hedging set | EN = [D1^2 + D2^2 + D3^2 + 1.4 D1 D2 + 1.4 D2 D3 + 0.6 D1 D3]^(1/2), AddOn = 0.5% * EN | CRE52.57 steps 5, 6 |
| FX hedging set | AddOn = 4% * abs(sum of D in the currency pair) | CRE52.59 steps 3, 4 |
| credit, equity | AddOn_entity = SF * sum of D for the entity; AddOn = [(sum rho * AddOn_entity)^2 + sum (1 - rho^2) * AddOn_entity^2]^(1/2) | CRE52.61, CRE52.66 |
| commodity | same single-factor formula per commodity type within each of the four hedging sets, then summed over hedging sets | CRE52.70 |

Bucket boundaries follow the words of CRE52.57 step 3: an end date of exactly one or exactly
five years falls in the middle bucket.

### CRE52.72 Table 2

| asset class | subclass | SF | rho | sigma |
|---|---|---|---|---|
| interest rate | | 0.50% | N/A | 50% |
| foreign exchange | | 4.0% | N/A | 15% |
| credit, single name | AAA | 0.38% | 50% | 100% |
| | AA | 0.38% | 50% | 100% |
| | A | 0.42% | 50% | 100% |
| | BBB | 0.54% | 50% | 100% |
| | BB | 1.06% | 50% | 100% |
| | B | 1.6% | 50% | 100% |
| | CCC | 6.0% | 50% | 100% |
| credit, index | IG | 0.38% | 80% | 80% |
| | SG | 1.06% | 80% | 80% |
| equity, single name | | 32% | 50% | 120% |
| equity, index | | 20% | 80% | 75% |
| commodity | electricity | 40% | 40% | 150% |
| | oil/gas, metals, agricultural, other | 18% | 40% | 70% |

Electricity is a commodity type in the energy hedging set; every other commodity type takes
18% and 70% (CRE52.70 step 4).

### Published examples the tests reproduce

| example | CRE99 | EAD (thousands) |
|---|---|---|
| 1, interest rate swaps and a swaption | CRE99.22 to 99.40 | 569 |
| 2, credit default swaps | CRE99.41 to 99.58 | 381 |
| 3, commodity forwards | CRE99.59 to 99.76 | 5,406 |
| 4, examples 1 and 2 combined | CRE99.77 onward; BCBS 279 Annex 4a | 936 |
| 5, examples 1 and 3, weekly margined | CRE99.82 to 99.97 | 1,879 |

The five margin agreement cases of CRE99.99 to CRE99.115 are reproduced for replacement cost.
Intermediate figures (adjusted notionals, the swaption delta of -0.2694, hedging set add-ons,
multipliers 0.965 and 0.958) are checked too. CRE99 rounds them, so the tests compare at that
rounding.

### Choices the text leaves to the implementer

- The CRE52.2 cap recomputes the netting set with unmargined maturity factors and the
  unmargined replacement cost, keeping the same V and C.
- With an aggregate add-on of zero, PFE is zero and the multiplier is reported as its limit (1
  when V - C is not negative, 5% otherwise).
- The IR hedging set uses the offset formula, the one the published example uses. The no-offset
  alternative of CRE52.57 step 5 is not offered.

## Exposure profile (CRE50, CRE53, ORE)

| quantity | definition | paragraph |
|---|---|---|
| peak exposure | a high percentile of the exposure distribution at a future date | CRE50.27 |
| expected exposure EE_t | mean of the exposure distribution at date t | CRE50.28 |
| Effective EE | Effective EE_tk = max(Effective EE_tk-1, EE_tk); Effective EE_t0 = current exposure | CRE50.29, CRE53.12 |
| EPE | weighted average of EE over the first year, weights dt_k = t_k - t_k-1; over the life of the set if it all matures sooner | CRE50.30 |
| Effective EPE | the same average of Effective EE | CRE50.31, CRE53.13 |

Implemented as EPE = sum_k EE_k * dt_k / t_K and Effective EPE = sum_k EffEE_k * dt_k / t_K,
over grid dates 0 < t_k <= 1 year, where t_K is the last such date. When the grid reaches one
year, t_K = 1 and this is CRE53.13 equation 3 exactly. When the grid ends before one year, the
last date is taken as the maturity of the netting set. When the grid passes one year without a
date at one year, the result is marked degraded and the covered horizon is reported.

ORE columns, from ORE's `ReportWriter::writeNettingSetExposures` and
`NettedExposureCalculator` at the pinned revision `b1f239332fdd51e5c514dd6de34a665fe0ff8326`:

- `NettingSet`, `Date`, `Time` (ActualActual ISDA year fraction from the as-of date; the first
  row is the as-of date at Time 0).
- `EPE`, `ENE`: discounted expected positive and negative exposure. Not used here.
- `PFE`: the configured quantile of the simulated exposure, floored at zero. Used for peak PFE.
- `BaselEE`: `EPE` divided by the base currency discount factor, so undiscounted. Used as EE.
- `ExpectedCollateral`, `BaselEEE`, `TimeWeightedBaselEPE`, `TimeWeightedBaselEEPE`: accepted
  so a report row can be passed as ORE wrote it, counted in the input hash, but not used or
  compared.

ORE's own one-year cut-off is one year plus four days, weekend adjusted; this summary uses
exactly one year, as CRE50.30 states.
