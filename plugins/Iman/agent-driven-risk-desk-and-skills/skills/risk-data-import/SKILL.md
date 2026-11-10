---
name: risk-data-import
description: Turn a caller's CSV, spreadsheet or JSON of positions, P&L, prices or exposures into a Risk Desk request contract, repairing clear format and unit errors and reporting each repair. Use when a user attaches a file and asks for a risk figure, asks how to format their data, or a tool rejected their input. Never invents a missing market value, date, currency, source or rights statement.
---

# Risk data import

The calculation tools validate their input and refuse anything malformed.
This skill turns the caller's own file into the JSON a tool accepts, so the
refusal is about the data and not about the layout.

## Safety boundary

- Use only the file the caller supplied. Never fetch prices, rates, FX or
  any other market data, and never fill a gap from memory.
- Never invent a market value, a price, a P&L observation, a date, a
  currency, an NAV, a `source` or a `data_mode`. A missing required value
  is asked for, by row and column.
- `data_mode` is the caller's declaration (`synthetic` or `user-licensed`).
  Ask for it; do not infer it from the file.
- The file stays on the caller's machine. Write the request next to it or
  where the caller says, and nowhere else.

## Which contract

| the file holds | contract | tool | CLI |
|---|---|---|---|
| positions with market values | PortfolioRequest | `risk_exposure` | `riskdesk exposure --input PATH` |
| positions plus scenario shocks | StressRequest | `risk_stress` | `riskdesk stress --input PATH` |
| a P&L series | TailRequest | `risk_tail`, `risk_tail_models` | `riskdesk tail --input PATH` |
| VaR forecasts beside realised P&L | BacktestRequest | `risk_backtest` | `riskdesk backtest --input PATH` |
| dated price levels per asset | ReplayRequest | `risk_stress_replay` | `riskdesk replay --input PATH` |
| asset returns, one row per period | CovarianceRequest | `risk_covariance` | `riskdesk covariance --input PATH` |
| options and futures with strikes and vols | DerivativesBookRequest | `risk_derivatives_greeks` | `riskdesk derivatives-greeks --input PATH` |
| simulated exposure by date | ExposureProfileRequest | `risk_exposure_profile` | `riskdesk exposure-profile --input PATH` |
| derivative trades in one netting set | SaccrRequest | `risk_saccr` | `riskdesk saccr --input PATH` |
| obligors with exposure, PD and LGD | AsrfRequest | `risk_credit_asrf` | `riskdesk credit-asrf --input PATH` |

Every field, type and constraint is in
[input contracts](../../references/contracts.md). Read it before mapping a
column; do not guess field names. Every request carries `as_of`, `currency`,
`source` and `data_mode`.

## Repairs you may make, and must report

Make a repair only when there is one reading of the value. Report each one
as: row, column, value as found, value as written, and why.

- Thousands separators and currency symbols: `"1,250,000"` or `$1.25m` to
  `1250000`, only when the currency matches the stated `currency`.
- Accounting negatives: `(4,200)` to `-4200`.
- Percent text to a fraction: `-10%` to `-0.10` for a shock, a return, a
  confidence or a volatility. A bare `-10` in a shock column is not
  repaired: it may mean -10% or -1000%; ask.
- Dates to ISO `YYYY-MM-DD`, only when the day and month cannot be swapped
  (`2026-11-04`, `4 Nov 2026`). `04/11/2026` is ambiguous; ask.
- Short names to the contract's literals when they are unambiguous:
  `Call` to `call`, `fut` to `future`, `user licensed` to `user-licensed`.
- Trailing blank rows and a repeated header row are dropped, and the count
  dropped is reported.
- A P&L column whose sign is reversed (losses positive) is negated only
  when the caller confirms that convention. Risk Desk reads positive P&L as
  profit.

## Repairs you must not make

- A blank market value, price, P&L, PD, LGD or exposure. Ask for it. Do not
  drop the row silently, do not write zero, and do not carry the previous
  value forward.
- Values in another currency. Conversion needs an FX rate and a date the
  caller chooses; ask for the converted values.
- An option premium used as a position's market value in a linear book.
  Premium is not delta exposure; route the book to `risk_derivatives_*`.
- Daily P&L offered for a ten-day horizon. Each observation must already
  span `horizon_days`; nothing scales it. Ask which horizon the file is.
- Duplicate position ids. Ask which row is right.

## Workflow

1. Identify the contract from the table above. If the file fits none, say
   so and stop.
2. Map columns to fields. List any required field with no column.
3. Ask once for every missing value and for `as_of`, `currency`, `source`
   and `data_mode` if the file does not state them.
4. Apply only the permitted repairs and list them.
5. Write the request JSON, check it with `scripts/check_artifact.py TOOL
   REQUEST.json` (every field error at once, with its path), then
   run the tool or CLI command on it.
6. If the tool returns a `ValidationError`, quote its message, map it back
   to the row and column, and ask for the corrected value. Do not loosen
   the request to make it pass.
7. Report the result as its own skill says: `degraded` and its reason first,
   then the figures with currency, horizon and sign convention.

## Going deeper

- `reference.md`: which model each tool reads and where it is defined, how
  pydantic reads a converted value, and what a passing check does not prove.
- `workflows/csv-to-request.md`: a positions CSV to a validated request, step by step.
- `scripts/check_artifact.py TOOL REQUEST.json`: validates a converted file
  against the tool's own request model and lists every error. Run it with
  the Python that has riskdesk installed.
