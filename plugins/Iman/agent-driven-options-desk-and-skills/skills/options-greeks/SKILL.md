---
name: options-greeks
description: Retrieve an approved or user-provided option chain and compute the full first to third order Greek ladder (delta, gamma, vega, theta, rho, lambda, vanna, vomma, charm, veta, speed, zomma, color, ultima, dual delta, dual gamma) for any US listed underlying. Use when the user asks about option Greeks for individual contracts, an option chain, a Greek by strike or expiry, theta decay, vega risk, or how one strike compares with another. For dealer gamma exposure, the walls, the gamma flip or the skew across a whole chain, use options-positioning instead. Not for order placement and not for recommendations.
---

# Option Greeks

Two commands. The first fetches a chain and writes a snapshot, the second
turns that snapshot into a Greek ladder. Both write a schema-validated JSON
artifact and print a JSON summary. Read the summary, cite the artifact path,
and do not re-derive numbers yourself.

## When to use

Use for questions about option pricing sensitivities: what is the delta of a
strike, where gamma peaks, how much theta a position bleeds per day, what
vega exposure looks like across the chain, how implied volatility varies by
strike, or what a specific contract is worth under Black-Scholes-Merton.

Do not use for order placement, position sizing against a live account, or
anything that amounts to a recommendation to trade.

## Execution route

Prefer `option_chain_snapshot` to retrieve the chain and
`option_greeks_ladder` to grade it. Use `option_desk_status` for the
availability check when needed. When the user asks to see a plot or chart,
call `option_plots`. The tool returns PNG images in the conversation. Do not
start the localhost dashboard as a substitute. If the user attached a CSV or
JSON chain, do not ask for the same data again. For a local file, pass its
path as `source_path`. For remote chat, pass its content as `source_data` or
`source_text`. If a matching MCP tool is not available,
use the `optiondesk` commands below. If neither MCP nor the CLI is
available, say that no fresh chain or Greek ladder can be produced; do not
invent figures or present example or remembered values as current.

## User-supplied data

Before you send data to the tool, ask the user to state that private analysis
is permitted. Then set `rights_confirmed` to true and name `data_source`.
The local desk does not gate on that name: any `data_source` is accepted,
so whether that provider's terms allow the analysis is the user's
responsibility (only the hosted service refuses Yahoo, yfinance and
personal Alpha Vantage data).

If the attachment fields are unclear, call `option_snapshot_schema`. Normalize
known column aliases, call or put notation, numeric commas, and clear percentage
units. Report the repairs from `normalization`. Never invent a missing spot,
expiry, strike, option type, quote, timestamp, or source. If a required value
is missing, ask only for that value.

The imported chain becomes a normal Option Desk artifact. Use its path for the
Greek ladder, plots, strategies, positioning, and the local dashboard.

## Data boundary

Use fresh provider data only when the tool reports that access is allowed.
A local Yahoo adapter also requires the personal-use acknowledgement. A
hosted tool must use a provider that is approved for public display, derived
outputs, storage, and MCP delivery. Never bypass a provider refusal. When no
approved tool is available, analyse a snapshot that the user supplied and
had the right to share. Otherwise, state that current figures are unavailable.

## Run it

```
optiondesk chain SPY
optiondesk chain SPY --from-file chain.csv --data-source "broker export" --accept-data-rights
optiondesk greeks
optiondesk plots SPY
```

`chain` takes `--expiry YYYY-MM-DD` (default: nearest listed),
`--dividend-yield` as a decimal, and `--rate` to override the fetched
13-week T-bill rate. `greeks` takes `--snapshot PATH` (default: the most
recent snapshot), `--band` to widen or narrow the strike window around spot
(0.10 by default, 0 keeps every strike) and `--type call|put|both`.

`optiondesk doctor` reports which providers and which analytics engine are
available, and where artifacts are written.

## What comes back

The `greeks` summary carries the artifact path, the number of rows graded,
the skip counts, and an at-the-money sample. The artifact carries one row per
contract with all sixteen Greeks plus price, implied volatility, moneyness
and days to expiry, and a `units` block that states the unit of every field.

## Units, because they are the usual source of a wrong answer

Volatility is per 1.00, so 0.20 means 20 percent. Vega is per 1.00 of
volatility, so divide by 100 for the conventional per-point figure. Theta,
charm, veta and color are all per calendar day of time passing, so theta is
normally negative for a long option. Delta and gamma are per 1.0 of
underlying move.

## Rules you must follow when reporting

Check `degraded` in the artifact meta. When it is true, say so and give the
reason before giving any number.

Contracts with no usable implied volatility are skipped and counted in
`skipped.no_iv`. Never fill in a volatility to make the ladder look
complete, and never present a skipped strike as if it were graded.

Prices here are Black-Scholes-Merton model values computed from delayed
third-party quotes. They are not tradable prices and not fills. Say so when
presenting them.

This is research output, not investment advice, not a recommendation and not
a solicitation. Do not phrase results as what the user should buy or sell.

## Failure modes worth recognising

If the summary reports the analytics engine is missing, the ladder cannot be
computed. Tell the user to install `optiondesk-engine`, which carries the
same noncommercial licence as the rest of the project.

If no provider is available, the message names each candidate and why it was
skipped, which is usually a missing `yfinance` install.

If a snapshot has a `spot_asof` older than the current session, the spot came
from the last settled close, not from today. Quote the date rather than
implying the number is live.

## Reporting rules

These hold for every number this skill produces.

Cite the artifact path when reporting from it. The artifact is the record;
prose is a summary of it, and a number quoted without its source cannot be
checked later.

Read `degraded` before quoting anything. When it is true, say so and give
`degraded_reason` first, in the same breath as the number rather than as a
footnote. Every command carries both fields in the summary it prints, not
only in the artifact.

Do not re-derive numbers yourself. If a figure is not in the artifact, say
it is not there rather than computing a replacement, and never substitute a
default for a value the pipeline refused to produce.

Premiums are model values or mid quotes from delayed third-party data. They
are not fills, and a real entry crosses the spread on every leg.

Never recommend a trade, an entry, an exit or a size. This is research
software and it is not investment advice. Present the analysis and let the
reader decide.
The full terms are in DISCLAIMER.md, which ships beside this skill when it
is installed from a package and sits at the repository root otherwise. The
substance is already above: research software, not advice, modelled numbers
that are not fills.


## What an audit found in these numbers, and what to say about it

An independent verification recomputed all sixteen Greeks for every row of
a live ladder against high-precision finite differences. Worst relative
disagreement was 9.95e-13, and every scaling convention held: theta, charm,
veta and color per calendar day, vega and rho per 1.00 rather than per
point, delta carrying the dividend discount. You can quote these.

Two things worth knowing when a contract is missing.

**A refusal to imply a volatility is now made at the answer, not the
seed.** The solver used to test sensitivity at its 0.30 starting guess and
give up when it was small, which refused deep in the money contracts it
could solve perfectly well: on one live chain that was 41 contracts, and it
was the sole reason the chain was flagged degraded. If you are reading a
chain snapshot written before September 2026, a high provider-volatility
share may be the solver rather than the market.

**The rate and the dividend yield come from the snapshot.** They are not
assumed, and a stated rate of exactly zero is now honoured rather than
being silently replaced by four percent. At the defaults instead of the
measured values, the live at-the-money call moved 4.3 percent in price and
8.1 percent in theta, and vanna changed sign.

## Going deeper

- `reference.md`: every field a row carries with its unit, the two conversions people get wrong, which signs are not invariants, what the model assumes, and what is refused rather than estimated. Read it when a number has to be interpreted or defended.
- `workflows/pull-and-grade.md`: the order to run the commands in and what to check before reporting.
- `scripts/check_artifact.py`: run it against a ladder artifact for a one line verdict. Running it is cheaper than reading the file, since only its output enters the conversation.
