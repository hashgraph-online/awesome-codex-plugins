---
name: risk-limits
description: Check a limit set (gross, net, leverage, an asset's gross share, VaR, Expected Shortfall, a named stress loss) against Risk Desk exposure, tail and stress results, and run a pre-trade what-if that revalues the book with proposed trades and checks the limits after. Use when the user asks whether a book is within its limits, what utilisation is, or what a proposed trade would do to exposure, stress loss, VaR and limits. Not for order placement and not for recommendations.
---

# Risk Limits

Two tools. `risk_limits` reads results that Risk Desk already returned and
grades each limit. `risk_what_if` applies proposed trades to a book,
recomputes exposure (and stress and tail when their inputs are given) with
the same functions as `risk_exposure`, `risk_stress` and `risk_tail`, and
grades the limits on the book after the trades. The CLI equivalents are
`riskdesk limits --input PATH` and `riskdesk what-if --input PATH`.

## Contract

Both requests carry the usual provenance: `as_of`, `currency`, `source`,
`data_mode` ([input contracts](../../references/contracts.md)).

A limit has a unique `name`, a `metric`, a `direction` (`max` or `min`), a
hard `limit` and an optional `warning`. Metrics: `gross_exposure`,
`net_exposure`, `gross_leverage`, `net_leverage`, `gross_share` (needs
`asset`), `var`, `expected_shortfall`, `stress_loss` (needs `scenario`).
For a `max` limit the warning must not exceed the limit; for `min` it must
not be below it.

`risk_limits` takes `limits` and `results`: a mapping with any of
`exposure`, `tail`, `stress`, each the unchanged result of that tool.

`risk_what_if` takes a PortfolioRequest plus `trades` (each `asset`, signed
`market_value_change`, optional `position_id`), and optionally `scenarios`
(must name exactly the assets held after the trades), `asset_returns` with
`confidence` and `horizon_days` (all three together; returns per asset over
the horizon, naming every asset held before or after), and `limits`.

## Report first

1. `degraded` and `degraded_reason`, before any number.
2. `overall_status` and `status_counts`. Overall is the worst of breach,
   warning, not_evaluated, within, so a book with an unevaluated limit is
   never reported as within.
3. Every breach and warning with value, limit and utilisation; then every
   `not_evaluated` limit with its `reason`.
4. For VaR and ES, the `basis` (confidence and horizon) of the value.
5. For a what-if: `change` first, then before and after, then `limits_after`.

## Sign conventions

Loss is positive: `var`, `expected_shortfall` and `stress_loss` are losses,
and a negative value is a gain. Market values and trades are signed; a sale
of a long is a negative change. Utilisation is value divided by limit and
is null for a zero limit or an overflowing ratio. Overflow carries a reason
and degraded status; `status` decides, not utilisation (a `min` limit
is satisfied at utilisation above one when the limit is positive).

## What not to claim

- Do not call a limit within when it was `not_evaluated`. Missing results,
  a missing asset or scenario, an error envelope and a currency mismatch are
  all reported, never skipped.
- A result whose currency differs from the limits is not evaluated. A
  differing as-of date is evaluated and flagged; say both dates.
- A what-if is a revaluation at as-of prices, cash-financed, with no costs,
  no market impact and unchanged NAV. It is not an execution estimate.
- Tail after a trade assumes each linear position's historical P&L scales
  with its value. Say so whenever quoting a what-if VaR or ES.
- Never recommend a trade, size or hedge. This is research output.

## Going deeper

- `reference.md`: every rule, the status logic and the what-if algebra.
- `workflows/check-limits.md` and `workflows/pre-trade-what-if.md`.
- `scripts/check_artifact.py RESULT.json`: re-derives every status and
  utilisation and prints a one line verdict. Works on either tool's result.
