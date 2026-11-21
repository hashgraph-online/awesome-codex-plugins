# Reference: request models, how they read values, and what the validator proves

The fields of each contract are in
[input contracts](../../references/contracts.md) and in the models
themselves; they are not restated here. This file says where each model
lives, how pydantic reads a converted value, and what a passing check does
and does not mean.

## Which model a tool reads

Each MCP tool takes one argument, `request`, typed with its model
(`src/riskdesk/server.py:39-204`). `scripts/check_artifact.py` reads that
annotation, so the validator and the tool cannot disagree about the model.

| tool | model | defined at |
|---|---|---|
| `risk_tail`, `risk_tail_models` | TailRequest | `src/riskdesk/models.py:18` |
| `risk_exposure` | PortfolioRequest | `src/riskdesk/models.py:32` |
| `risk_stress` | StressRequest | `src/riskdesk/models.py:48` |
| `risk_backtest` | BacktestRequest | `src/riskdesk/backtest.py:21` |
| `risk_derivatives_greeks` | DerivativesBookRequest | `src/riskdesk/derivatives.py:59` |
| `risk_derivatives_grid` | ScenarioGridRequest | `src/riskdesk/derivatives.py:82` |
| `risk_derivatives_historical` | HistoricalPnlRequest | `src/riskdesk/derivatives.py:99` |
| `risk_covariance` | CovarianceRequest | `src/riskdesk/decomposition.py:36` |
| `risk_var_attribution` | ParametricRequest | `src/riskdesk/decomposition.py:47` |
| `risk_es_attribution` | HistoricalRequest | `src/riskdesk/decomposition.py:63` |
| `risk_factor_exposure` | FactorRequest | `src/riskdesk/decomposition.py:67` |
| `risk_limits` | LimitRequest | `src/riskdesk/limits.py:50` |
| `risk_what_if` | WhatIfRequest | `src/riskdesk/limits.py:166` |
| `risk_liquidity` | LiquidityRequest | `src/riskdesk/liquidity.py:21` |
| `risk_stress_replay` | ReplayRequest | `src/riskdesk/scenarios.py:36` |
| `risk_reverse_stress` | ReverseStressRequest | `src/riskdesk/scenarios.py:157` |
| `risk_scenario_scale` | ScaleRequest | `src/riskdesk/scenarios.py:238` |
| `risk_saccr` | SaccrRequest | `src/riskdesk/counterparty.py:101` |
| `risk_exposure_profile` | ExposureProfileRequest | `src/riskdesk/counterparty.py:307` |
| `risk_credit_asrf` | AsrfRequest | `src/riskdesk/credit.py:47` |
| `risk_credit_copula` | CopulaRequest | `src/riskdesk/credit.py:51` |
| `risk_frtb_imcc` | ImccRequest | `src/riskdesk/frtb.py:64` |
| `risk_frtb_ima_capital` | ImaCapitalRequest | `src/riskdesk/frtb.py:115` |
| `risk_frtb_pla` | PlaRequest | `src/riskdesk/frtb.py:178` |
| `risk_frtb_backtest` | BacktestRequest (FRTB) | `src/riskdesk/frtb.py:213` |
| `risk_frtb_sbm_fx` | FxSbmRequest | `src/riskdesk/frtb.py:280` |

Two models share the name BacktestRequest, which is why the validator
takes a tool name and not a model name. `risk_xva` takes paths, not a
request (`server.py:207-214`), and `risk_scenario_library` and
`risk_desk_status` take nothing. `tests/test_cli.py` (`CASES`, `TOOLS`)
pairs every tool with a shipped example in `examples/`, and every one of
those examples passes the validator; use the matching example as the
template for a conversion.

## Rules every model shares

- All 27 models inherit `Provenance` (`models.py:11-15`): `as_of`,
  `currency` (`^[A-Z]{3}$`), `source` (1 to 500 characters) and
  `data_mode` (`synthetic` or `user-licensed`).
- `StrictModel` (`models.py:7-8`): unknown fields are refused and NaN or
  infinity is refused. Checked on all 27 on 2026-11-04 by reading each
  model's `model_config`.

## How a value is read

Observed on 2026-11-04 with pydantic 2.13.5, on PortfolioRequest and
TailRequest:

| value in the file | field | outcome |
|---|---|---|
| `"2026-11-04"` | `as_of` | accepted |
| `"2026-11-04T00:00:00"` | `as_of` | accepted as that date |
| `"04/11/2026"`, `"4 Nov 2026"` | `as_of` | refused |
| `"1250000"` | `market_value` | accepted as a number |
| `"1,250,000"`, `"(4200)"` | `market_value` | refused |
| `null` | `market_value` | refused |
| NaN | `market_value` | refused |
| `"usd"` | `currency` | refused |
| `"user licensed"` | `data_mode` | refused |
| `"Linear"` | `instrument_type` | refused |
| `10.0` or `"10"` | `horizon_days` (strict integer, `models.py:21`) | refused |
| `"99%"` or `99` | `confidence` | refused |
| `"-4200"` | an entry of `pnl` | accepted as a number |
| a key not in the model | any | refused |

So every repair the skill permits is one the model would otherwise refuse.
A numeric string passes, so write plain JSON numbers anyway; the result
is the same, because the input hash is taken after validation
(`analytics.py:28-32`).

## Reading an error

Each line the validator prints is pydantic's location, message and the
value found. Locations are zero-based list positions: `positions.0` is the
first position. Map them back to the caller's rows through the order in
which the rows were written, counting any header, blank or repeated rows
that were dropped.

Cross-field rules are model validators that run after the fields: unique
position ids (`models.py:36-40`), scenarios naming every asset
(`models.py:51-61`), a covariance that matches its assets
(`scenarios.py:164-175`), and others. They report against `request`, and
only once every field is valid. Observed: a request with a duplicate id
and an unreadable market value reports only the market value. Correct and
re-run until the verdict is OK.

## What OK does not prove

OK means the model accepts the request, which is exactly what the CLI does
first (`cli.py:79`, then for example `analytics.py:69`). Some refusals
happen afterwards, inside the calculation: an asymmetric or not positive
definite covariance (`scenarios.py:182-188`), an implausible liquidation
time (`liquidity.py:57-59`), sums past the float range
(`analytics.py:16-24`). Running the tool is the last check. OK also says
nothing about whether a value is right: a market value in the wrong
currency or a P&L with its sign reversed validates.

## CLI and MCP shapes

The CLI reads the bare request object from `--input` (`cli.py:79`). Over
MCP the same object is the value of the `request` argument, for example
`{"request": {...}}` (`tests/test_interfaces.py:17, 38`).
