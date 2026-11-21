---
name: risk-frtb
description: Compute Basel FRTB market risk capital pieces from figures a bank has already produced. It covers the internal models approach (liquidity-adjusted, stress-calibrated Expected Shortfall and IMCC, then aggregate capital with the multiplier, the amber-desk surcharge and RWA), the desk eligibility tests (P&L attribution Spearman and Kolmogorov-Smirnov zones, VaR backtesting exception counts at 97.5% and 99%) and the standardised sensitivities-based method for FX delta and vega. Use it when the user asks for FRTB, MAR21, MAR32 or MAR33 capital, a PLA zone, a backtesting zone or multiplier, or FX SBM capital. It does not estimate ES or VaR from market data, and it is not a regulatory submission.
---

# Risk FRTB

Five functions, each taking a JSON request and returning a result envelope
with `degraded`, `currency`, `as_of`, `source`, `data_mode`, `input_sha256`
and `assumptions`. Read the envelope; do not redo the arithmetic yourself.

| Task | Function | MCP tool, CLI command | Rules |
|---|---|---|---|
| Liquidity-adjusted ES, stress scaling, IMCC | `frtb_imcc` | `risk_frtb_imcc`, `riskdesk frtb-imcc --input PATH` | MAR33.4, MAR33.6, MAR33.15 |
| Aggregate IMA capital, surcharge, RWA | `frtb_ima_capital` | `risk_frtb_ima_capital`, `riskdesk frtb-capital --input PATH` | MAR33.41 to MAR33.46, MAR32.9 |
| P&L attribution test zone | `frtb_pla` | `risk_frtb_pla`, `riskdesk frtb-pla --input PATH` | MAR32.34 to MAR32.42 |
| VaR backtesting counts, desk verdict or bank zone | `frtb_backtest` | `risk_frtb_backtest`, `riskdesk frtb-backtest --input PATH` | MAR32.5, MAR32.9, MAR32.18, MAR32.19 |
| SBM FX delta and vega capital | `frtb_sbm_fx` | `risk_frtb_sbm_fx`, `riskdesk frtb-sbm-fx --input PATH` | MAR21.4, MAR21.6, MAR21.7, MAR21.86 to MAR21.95 |

If no tool is available, say so; never produce a capital figure by hand.

## Contract

Every request carries the provenance fields of the other Risk Desk tools:
`as_of`, `currency` (three upper-case letters), `source`, and `data_mode`
(`synthetic` or `user-licensed`). Unknown fields, non-finite numbers and
wrong lengths are refused with a plain message. Examples of every request
are in `examples/frtb_*.json`.

- `frtb_imcc`: `base_horizon_days` must be 10. `portfolio` and each entry of
  `risk_classes` (`interest_rate`, `equity`, `fx`, `commodity`,
  `credit_spread`) hold three cascades: `reduced_stressed`, `full_current`
  and `reduced_current`. A cascade is five non-negative 10-day ES values,
  ES_T(P, j) for j = 1 to 5. Element 0 is ES over all risk factors; element j
  shocks only the factors whose liquidity horizon is at least 20, 40, 60 and
  120 days. Use 0 where no factor has that horizon.
- `frtb_ima_capital`: latest and 60-day average IMCC and SES, latest and
  12-week average DRC, the bank-wide 99% exception count over 250 days, the
  supervisor's qualitative add-on, each approved desk's standardised charge
  with its PLA zone (`green` or `amber`), SA on the combined green and amber
  positions, SA for out-of-scope desks, and SA for all desks.
- `frtb_pla`: exactly 250 daily `rtpl` and `hpl` values, oldest first.
- `frtb_backtest`: `level` is `desk` or `bank`. Exactly 250 days of `apl`,
  `hpl` and `var_99`, plus `var_975` for a desk and not for the bank. A null
  P&L or VaR is allowed; it counts as an exception.
- `frtb_sbm_fx`: `currency` is the reporting currency. `delta` and `vega` are
  lists of sensitivities in the reporting currency; each vega entry names its
  option maturity, mapped to 0.5, 1, 3, 5 or 10 years.
  `apply_specified_pair_reduction` records the bank's MAR21.88 election. It
  has no default because it is a choice.

## What to report first

1. `degraded` and `degraded_reason`, before any number. The FX SBM result is
   degraded whenever vega is supplied: options also attract curvature
   capital (MAR21.2), and curvature is not computed here.
2. The verdict the user asked about, with its rule: the PLA `zone`, the desk
   `passes`, the bank `zone` and `backtesting_multiplier`, the SBM
   `binding_scenario`, or the `aggregate_capital` and `rwa`.
3. The currency, the as-of date and the horizon: 10-day base ES for IMCC and
   one-day P&L for the tests.
4. The figures that drove it: the floored stress ratio per class, `c_a` and
   which side of its maximum bound it, `k` and the surcharge, the exception
   counts for APL and HPL separately.

## Sign conventions

Capital, ES, VaR, SES, DRC and standardised charges are positive amounts in
the stated currency. P&L is signed: positive is profit. A backtesting
exception is a loss, the negative of P&L, strictly greater than VaR; a loss
equal to VaR is not an exception. Sensitivities are signed and netted per
risk factor before risk weighting.

## What not to claim

- Not a regulatory capital figure. It is arithmetic over caller-supplied
  inputs. The bank's model approval, risk factor eligibility, stress period
  selection and desk structure are outside it.
- Not complete FRTB. Not computed: ES itself, the non-modellable stress
  scenario capital (MAR33.16 to MAR33.17, taken as an input), the default
  risk model (MAR33.18 to MAR33.39, taken as an input), the 10% eligibility
  criterion (MAR32.2), PLA zone transitions over time (MAR32.43 to MAR32.44),
  SBM curvature, the SBM risk classes other than FX, the standardised default
  risk charge, and the residual risk add-on.
- Do not call the FX SBM capital the standardised approach capital. It is the
  FX delta and vega part of the SBM only.
- Two readings are interpretations, and the result says so. The MAR33.6 floor
  at 1 is also applied to each risk-class ratio. The MAR32.19 limits are
  applied as "more than 12" and "more than 30".

## Going deeper

- `reference.md`: every formula, constant and sign, with the paragraph and
  the version of the text read.
- `workflows/ima-capital.md`: from desk ES cascades to RWA.
- `workflows/desk-eligibility.md`: PLA and desk backtesting for one desk.
- `workflows/sbm-fx.md`: FX delta and vega capital.
- `scripts/check_artifact.py`: a one-line verdict on any saved FRTB result.
  It recomputes everything that can be derived inside the result.
