# Errors and warnings

## HTTP status

| Status | Meaning | What to do |
| --- | --- | --- |
| `400` | A parameter is wrong (`error` names it: `INVALID_PARAMS`, `BAD_ADDRESS`, ...) | Fix the request; check addresses and the amount in smallest units |
| `404` | `NOT_A_CONTRACT` / `NOT_A_MINT` on the security check | The address is not a token: find the token again |
| `422` | `INPUT_NOT_SIMULATABLE`: a route exists but the wallet does not hold the input | Ask the user to hold the input first, then quote again |
| `429` | Over the per-minute limit | Wait about a minute (`Retry-After` / `X-RateLimit-Reset`), then retry once |
| `502` | `TRADE_BAD_ANSWER` (Solana) or a provider failure | Quote again; nothing was sent |
| `503` | A lane is not ready (`NOT_READY`, `CHAIN_NOT_ENABLED`, `BUSY`, `*_UNAVAILABLE`) | Try again later. Never read it as "no route" or as a clean safety check |

## `fallbackReason` (EVM quote, when `provider` is not `chord`)

`no_route`, `insufficient_liquidity`: Chord's router found nothing, another aggregator answered (or
none did when `provider` is null). `taxed_token`: the token takes a tax on transfer; say so.
`value_guard`: Chord's route was refused for losing too much value. `engine_error`,
`engine_timeout`, `engine_down`, `route_stale`, `build_failed`, `simulation_failed`,
`chain_not_live`: a temporary problem on Chord's side. The quote from the other provider is still
simulated and usable; tell the user who routes it.

## `warnings` (EVM quote)

- `INSUFFICIENT_BALANCE: ...` the wallet holds less than the input; the simulation was run with the
  input supplied. Do not send: tell the user how much they are short.
- Any other warning: show it to the user word for word in the summary.

## Simulation

- `simulation.ok: true`: the transaction, run from the user's wallet, delivered at least
  `minAmountOut`.
- `false`: it would fail (`revert` / `reason` say why). Do not send. Typical causes: the amount moved,
  the wallet lacks the input or gas, the token blocks transfers.
- `null`: no verdict. Say so, and suggest a smaller test amount first.

## Safety report

- `verdict: avoid`: refuse, and give the first failing check.
- `verdict: caution` or `unknown`, or `partial: true`: list the failing or missing checks and let the
  user decide.
- `verdict: ok`: say the checks passed, not that the token is safe.
