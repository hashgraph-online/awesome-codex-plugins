# Reference: exposure, leverage and concentration

Code: `src/riskdesk/analytics.py` (`portfolio_exposure`, lines 68-86) and
`src/riskdesk/models.py` (`Position` and `PortfolioRequest`, lines 25-40).
No published source or regulatory constant is used; these are plain sums.

## Contract, as the model enforces it

- Provenance (`models.py:11-15`): `as_of` a date, `currency` three capital
  letters, `source` 1 to 500 characters, `data_mode` `synthetic` or
  `user-licensed`.
- Unknown fields and non-finite numbers are refused (`models.py:7-8`).
- `nav` strictly positive; `positions` 1 to 100,000 (`models.py:33-34`).
- A position has a non-empty `id` and `asset`, a signed `market_value` and
  `instrument_type` exactly `linear` (`models.py:25-29`). Any other type,
  for example `option`, is refused (`tests/test_risk.py:80-82`).
- Position ids are unique (`models.py:36-40`, `tests/test_risk.py:85-87`).

## Notation

- m_p: signed market value of position p, in the stated currency.
- A(p): the asset of position p. NAV: the supplied `nav`.

## Formulas

| output | formula | code |
|---|---|---|
| gross by asset G_a | sum over p with A(p) = a of abs(m_p) | `analytics.py:73` |
| `net_by_asset` N_a | sum over p with A(p) = a of m_p | `analytics.py:74` |
| `gross_exposure` G | sum over a of G_a | `analytics.py:75` |
| `net_exposure` N | sum over a of N_a | `analytics.py:76` |
| `gross_leverage` | G / NAV | `analytics.py:83` |
| `net_leverage` | N / NAV | `analytics.py:84` |
| `gross_shares[a]` | G_a / G, or 0 for every asset when G is 0 | `analytics.py:85` |

Sums use `math.fsum` (`analytics.py:16-24`). G_a is built from position
values, not from the asset's net, so a long and a short in one asset both
add to gross. From these definitions: G >= abs(N), G_a >= abs(N_a), every
share lies in [0, 1], and the shares sum to 1 whenever G > 0. G is 0 only
when every market value is 0. `scripts/check_artifact.py` checks each of
these on a saved result.

Hand check (`tests/test_risk.py:59-65`, `examples/portfolio.json`): A at
600 and B at -200 with NAV 1000 give gross 800, net 400, gross leverage
0.8, net leverage 0.4 and a share of 0.75 for A.

## Envelope

Every result carries `schema_version`, `riskdesk_version`, `method`,
`currency`, `as_of`, `source`, `data_mode`, `input_sha256`, `degraded`,
`degraded_reason`, `assumptions` and `disclaimer` (`analytics.py:27-34`).
`input_sha256` is the SHA-256 of the validated request serialised with
sorted keys (`analytics.py:28-32`), so the same book gives the same hash
(`tests/test_risk.py:96-100`). `portfolio_exposure` passes no warnings to
the envelope (`analytics.py:79-82`), so `degraded` is false on every
result it returns.

The result adds `nav`, `gross_exposure`, `net_exposure`, `gross_leverage`,
`net_leverage`, `net_by_asset` and `gross_shares` (`analytics.py:83-85`).
There is no per-asset gross field; G_a is `gross_shares[a]` times G.

## Refused rather than estimated

- Any contract breach above, with pydantic's message.
- A gross, net or gross leverage that is not finite: `ValueError`
  "aggregated exposure exceeds numerical limits" (`analytics.py:77-78`).
- A sum that overflows the float range: `ValueError` "a sum exceeded
  numerical limits" (`analytics.py:16-24`, `tests/test_risk.py:152-167`).

## Not computed

FX translation, option delta, netting agreements, collateral, margin and
counterparty exposure. The assumptions list in every result says the same
(`analytics.py:80-82`).
