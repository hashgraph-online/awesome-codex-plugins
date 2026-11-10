# Reference: limit grading and what-if algebra

No regulatory or published constant is used here. Every threshold is the
user's. The rules below are the desk's definitions and are enforced by
`src/riskdesk/limits.py` and its tests.

## Where each metric is read from

| metric | result | field | scope |
|---|---|---|---|
| gross_exposure | exposure | gross_exposure | portfolio |
| net_exposure | exposure | net_exposure | portfolio |
| gross_leverage | exposure | gross_leverage (gross / NAV) | portfolio |
| net_leverage | exposure | net_leverage (net / NAV) | portfolio |
| gross_share | exposure | gross_shares[asset] | asset |
| var | tail | var | portfolio |
| expected_shortfall | tail | expected_shortfall | portfolio |
| stress_loss | stress | scenarios[name == scenario].loss | portfolio |

Nothing is recomputed when grading: the value is the one the tool returned.

## Status

Let v be the value, L the hard limit, W the optional warning.

- max: breach if v > L; else warning if W is set and v >= W; else within.
- min: breach if v < L; else warning if W is set and v <= W; else within.
- not_evaluated, with a reason, when the result, asset or scenario is
  absent, the result is an error envelope, its currency differs from the
  request, the value is not a finite number, or stress scenarios are malformed
  or contain duplicate matches for the requested name.

A value exactly at the hard limit is within (or warning when W = L).
Utilisation u = v / L, null when L = 0 or the ratio overflows. An overflow
preserves the limit status, adds `utilisation_unavailable_reason` to the row
and marks the result degraded.

Overall status is the most severe row under the order
within < not_evaluated < warning < breach.

## Provenance checks

For every supplied result: a different currency blocks its limits; a
different as-of date is flagged; a degraded result passes its reason on.
Any not_evaluated limit also makes the check degraded. Supplied results
containing a non-finite number are refused outright.

## What-if algebra

Positions p with signed values m_p, trades k with changes dm_k.

1. A trade changes the position named by `position_id`, else the single
   position holding its asset, else opens `what-if-<k>`. An asset held in
   several positions without a `position_id` is refused, because adding
   the trade as a separate position would count a sale as extra gross.
2. Exposure, stress and tail are recomputed on the before and after books
   by `portfolio_exposure`, `stress_test` and `tail_risk`.
3. Stress: a scenario must shock every asset held after the trades. For the
   before book, shocks to assets not yet held are dropped; there is no
   position for them to act on, so the result is exact.
4. Tail: with net value per asset N_a and supplied horizon return r_{a,t},
   P&L_t = sum_a N_a r_{a,t}. This is the linear assumption that a
   position's historical P&L scales with its value. VaR and ES are then
   historical, as in `risk_tail`; no square-root-of-time scaling.
5. NAV is unchanged (cash-financed, costless), so leverage after uses the
   same NAV.
6. `change` = after minus before for gross, net, gross and net leverage,
   VaR, ES, and loss per scenario.

## Checks behind these statements

`tests/test_limits.py` checks each status against hand calculation on
`examples/portfolio.json`, the what-if revaluation against hand arithmetic
(gross 800 to 1000, stress loss 20 to 160, VaR 50 to 50 x 5/6), and the
artifact checker against both real and tampered results.
