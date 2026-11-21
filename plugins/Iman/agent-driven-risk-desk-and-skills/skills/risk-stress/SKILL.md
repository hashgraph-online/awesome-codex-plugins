---
name: risk-stress
description: Revalue linear positions under explicitly supplied asset-return scenarios, replay a dated historical window from the user's own price data, list the dated scenario library (Lehman 2008, COVID 2020, UK gilt and LDI 2022), find the most plausible shock that produces a target loss (reverse stress) under a supplied covariance, or scale a scenario to a target loss. Use for scenario loss and contribution analysis, "what happens if 2008 repeats", "what move loses us X", and "how far is this scenario from our loss limit". Not for options, credit migration or nonlinear margin calls.
---

# Risk Stress

Five calculations, all for linear positions, all revalued by the same
engine and all returned in the shared envelope (currency, as-of, source,
data mode, input hash, degraded flag and reason, assumptions). Read the
result, cite it, and do not re-derive numbers yourself.

| job | MCP tool | CLI |
|---|---|---|
| revalue supplied scenarios | `risk_stress` | `riskdesk stress --input PATH` |
| replay a dated window from user prices | `risk_stress_replay` | `riskdesk replay --input PATH` |
| list dated historical windows | `risk_scenario_library` | `riskdesk scenarios` |
| reverse stress to a target loss | `risk_reverse_stress` | `riskdesk reverse-stress --input PATH` |
| scale a scenario to a target loss | `risk_scenario_scale` | `riskdesk scale-scenario --input PATH` |

If a tool is not listed by the server, say it is not available rather than
computing the figure yourself.

## Contracts

All requests carry the PortfolioRequest fields in
[input contracts](../../references/contracts.md): `as_of`, `currency`,
`source`, `data_mode`, `nav` and linear `positions`.

- Stress: plus `scenarios`, each naming exactly every portfolio asset,
  including an explicit zero when no change is intended.
- Replay: plus `scenario_name`, `prices` (asset to `{ISO date: positive
  level}`), `start`, `end`, optional `measure` (`end_over_start`, the
  default, or `worst_peak_to_trough`) and optional `proxies` (portfolio
  asset to the name of the series standing in for it). The prices are the
  user's own licensed data; Risk Desk ships none.
- Library: no input. Returns windows with dates, reasons and sources, no
  returns.
- Reverse stress: plus `target_loss` (positive), `horizon_days`, `assets`
  (each portfolio asset once, in covariance order), `covariance` (the
  user's covariance of simple returns over that horizon) and optional
  `floors` (asset to a lowest allowed shock, at least -1).
- Scaling: plus `scenario` (one scenario naming every portfolio asset) and
  `target_loss`.

## What to report first

1. `degraded` and `degraded_reason`, before any number. A replay that used
   a proxy is degraded and the reason names each proxy.
2. The headline: scenario `loss` (positive is a loss, negative a gain) and
   `stressed_nav`, with currency and as-of.
3. For a replay, the window, the measure and any proxies. For reverse
   stress, the `shocks`, `mahalanobis_distance`, `solution` and
   `binding_floors`. For scaling, `multiple`.
4. Position `contributions` when the user asks what drives the loss.

## Sign conventions

Shocks are simple returns per 1.00: -0.10 is a 10% fall. P&L is positive
for a profit; loss is minus P&L. No shock is below -1.

## Rules you must follow when reporting

- A scenario, a replayed window, a reverse stress shock and a multiple are
  not event probabilities. Never present one as a forecast.
- `loss_exceedance_probability_if_normal` holds only if returns were
  jointly normal with mean zero and the supplied covariance. Always say so
  in the same sentence as the number.
- A worst peak-to-trough replay takes each asset's worst fall separately;
  the falls need not coincide and are gains for short positions. Do not
  call it the worst loss the book would have suffered in the window.
- Never fill a missing price, date or series with a guess or a zero. The
  tool refuses; ask the user for the series, or for an explicit proxy.
- The covariance, prices and floors are the user's inputs. Name their
  source; do not describe them as estimated by Risk Desk.
- Do not apply this model to option premium values, credit migration or
  nonlinear margin calls. Route derivative valuation to Option Desk pricing
  or a configured ORE project.
- Research software, not investment advice.

## Going deeper

- `reference.md`: every formula with its derivation, the sign table, the
  source and verbatim quotation for every library date, and what is refused.
- `workflows/replay.md`: replay a library window or the user's own window.
- `workflows/reverse-stress.md`: reverse stress and scenario scaling.
- `scripts/check_artifact.py`: run it on a saved result for a one line
  verdict. It rechecks loss signs, contribution sums, target loss, floors,
  the normal probability and replay levels with the standard library only.
