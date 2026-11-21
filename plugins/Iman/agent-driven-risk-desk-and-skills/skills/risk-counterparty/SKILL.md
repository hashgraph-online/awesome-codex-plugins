---
name: risk-counterparty
description: Calculate Basel SA-CCR exposure at default for one derivative netting set (CRE52), or summarise a simulated exposure profile such as an ORE netting-set exposure report into peak PFE, EPE, Effective EE and Effective EPE (CRE50, CRE53). Use for regulatory counterparty exposure measures. Not for CVA or other valuation adjustments (use risk-xva), not for portfolio credit loss (use risk-credit), and not for capital requirements or risk weights.
---

# Risk Counterparty

Two tools, both read-only and deterministic.

- `risk_saccr` takes one netting set of trades and returns its SA-CCR exposure at default with
  every intermediate figure: replacement cost, multiplier, add-on per asset class and hedging
  set, and per trade the adjusted notional, supervisory duration, maturity factor, supervisory
  delta and effective notional. CLI: `riskdesk saccr --input PATH`.
- `risk_exposure_profile` takes the rows of one ORE netting-set exposure report (column names
  exactly as ORE writes them) and returns peak PFE, EPE, Effective EE at every date and
  Effective EPE over the first year. CLI: `riskdesk exposure-profile --input PATH`.

Examples: `examples/counterparty_saccr.json` (the Basel CRE99 example 5 portfolio, EAD 1,879)
and `examples/counterparty_profile.json`.

## The contract, in short

Every request carries `as_of`, `currency` (three capital letters), `source` and `data_mode`
(`synthetic` or `user-licensed`). All amounts are in that one currency. Times are in years from
`as_of`. Unknown fields and non-finite numbers are refused.

An SA-CCR trade has `id`, `asset_class` (`interest_rate`, `fx`, `credit`, `equity`,
`commodity`), positive `notional`, signed `market_value` (value to the bank), `maturity` (M),
and `position` (`long` or `short` in the primary risk factor; for an option, long means bought).
What else it needs depends on the class:

| class | hedging_set | reference | start, end | other |
|---|---|---|---|---|
| interest_rate | currency, eg `USD` | none | required (S, E) | |
| fx | pair, eg `EUR/USD` | none | none | |
| credit | none | entity or index name | required (S, E) | `rating` AAA to CCC, or IG or SG with `index: true` |
| equity | none | entity or index name | none | `index: true` for an index |
| commodity | `energy`, `metals`, `agricultural` or `other` | commodity type | none | `electricity: true` for electricity |

`notional` means the trade notional for interest rate and credit, the foreign leg converted to
the request currency for fx, and price times units for equity and commodity. An option adds
`option` (`call` or `put`), `underlying_price`, `strike`, `exercise` (T, years) and, for a
negative-rate interest rate option only, `shift` (lambda).

The netting set adds `netting_set`, `collateral` (C, haircut value of net collateral held,
positive when held) and, when `margined` is true, `threshold`, `minimum_transfer_amount`, `nica`,
`remargining_period_business_days` and `mpor_business_days`. The MPOR must be at least nine
business days plus the remargining period.

An exposure profile has `rows`, at least two, the first at `Time` 0, times strictly increasing,
one netting set, each with non-null, non-negative `BaselEE` and `PFE`.

Never invent a trade term, a rating, a market value, a collateral amount or an exposure row. If
one is missing, ask for that value only.

## What to report first

1. `degraded` and `degraded_reason`, before any number.
2. For SA-CCR: `ead` with the currency, then `replacement_cost`, `multiplier`, `pfe` and
   `addon_by_asset_class`. For a margined set, say whether `cap_applied` is true.
3. For a profile: `effective_epe` and `epe` with `averaging_horizon_years`, then `peak_pfe`
   with its time.
4. The `source`, `as_of` and `input_sha256`, so the figure can be traced.

## Sign conventions

Exposure is a positive amount the bank could lose on counterparty default. `market_value` and
`collateral` are signed from the bank's side: positive value is owed to the bank, positive
collateral is held by the bank. Replacement cost is floored at zero. A negative netting-set
value or excess collateral lowers the multiplier, never the replacement cost below zero. ORE's
`BaselEE` and `PFE` are positive exposures; ORE's `ENE` keeps ORE's own negative sign and is
not used.

## What not to claim

- SA-CCR EAD is a regulatory exposure measure, not a loss forecast, a price or a capital
  requirement. No risk weight is applied.
- This is one bilateral netting set. Basis and volatility hedging sets, CDO tranches, central
  counterparty MPOR floors, the 20-day MPOR cases and multiple netting sets or margin
  agreements are not modelled. Say so if the user's book needs them.
- FX and equity add-ons are partially verified: their constants are checked against CRE52.72,
  but the Basel Framework publishes no worked FX or equity example, so they are checked by hand
  arithmetic only. A result with FX or equity trades says so in its `assumptions`; report it.
- The profile summary is not an IMM EAD. Alpha times Effective EPE needs supervisory approval.
- The figures are only as good as the ORE simulation behind them; a clean summary does not
  validate the ORE calibration.

## Going deeper

- `reference.md`: every formula with its CRE paragraph, every constant from CRE52.72 Table 2,
  the ORE column meanings, and the published examples the tests reproduce.
- `workflows/saccr-ead.md` and `workflows/exposure-profile.md`: step by step.
- `scripts/check_artifact.py RESULT.json`: one-line verdict on a saved result. It recomputes the
  EAD identity, checks multiplier bounds, add-on sums and the Effective EE monotonicity.
