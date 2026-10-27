# Krexa limits

Krexa checks these in code on its servers. A prompt cannot change them.

## Limits you set on a deploy

| Limit | Field | What it does |
|---|---|---|
| Max per trade | `maxTradeUsdc` | No single buy above this. |
| Daily budget | `dailyBudgetUsdc` | No more buying after this much in one day. |
| Daily loss cap | `maxDailyLossUsd` | Required. When the day's loss reaches it, the agent stops buying. Sells still run. Money withdrawn that day counts toward it. |
| Stop-loss | `stopLossPercent` | 1 to 50. Checked at each decision; sells when the position is this far below the last buy price. |
| Approve each order | `approvalMode: "approve"` | Off by default (`auto`: trades on its own inside the limits). Only when the user asks: every order waits 15 minutes for the user to approve it on the agent page, then expires. The user can change it on the approval page and on the agent page. |

## Limits Krexa sets

- MCP deploys cover Solana spot, Hyperliquid, Jupiter Perps, Polymarket Perps,
  Polymarket (yes/no markets), and perps in the user's own exchange account
  (`binance-perps`, `bybit-perps`, `okx-perps`, `kraken-perps`, `coinbase-perps`).
  Exchange spot returns `not_supported`.
- A deploy does not need a test. A deep test is recommended: `krexa_deploy_request`
  returns `deepTested` (true only for your own passed deep test on that venue)
  and, when false, says "Not deep-tested". Paper trading still needs a finished
  deep test, because it replays the exact code that test froze. A Solana test
  does not count for another venue; each exchange needs its own.
- Hyperliquid, Jupiter Perps and Polymarket Perps have no per-trade or per-day
  dollar cap. The size is the money in the agent's account times `maxLeverage`;
  the daily loss cap still applies.
- Exchange perps do have dollar caps, enforced on the server: `maxTradeUsdc` is
  the most per order, `dailyBudgetUsdc` is the slice of the account the agent
  trades with, and new positions a day are at most `dailyBudgetUsdc` times
  `maxLeverage`. The agent trades only its own positions, never the user's.
- The exchange key never goes through MCP. With no futures-enabled key for that
  exchange, `krexa_deploy_request` answers `exchangeKey: "missing"` and a
  `nextStep` link; the approval page shows the same step. Never ask for the key.
- Polymarket (yes/no) has no per-trade or per-day dollar cap and no leverage:
  it buys shares with the money in its own wallet. The daily loss cap, the
  stop-loss and per-order approval still apply. It runs only code that its own
  deep backtest on Polymarket gated. If live Polymarket is not open for the
  owner's wallet, the deploy request says so.
- Least funding for a new agent: Solana spot any amount ($5 is fine);
  Hyperliquid $15 and Jupiter Perps $15 (1.5x their $10 smallest order);
  Polymarket $2 (moved to its own Polymarket wallet). Plus 0.01 SOL for fees.
- Tokenized stocks (xStocks such as NVDAx) trade as Solana spot and decide
  once a day. Paper trading does not take them yet.
- Leverage is always 1 for Solana spot and Polymarket. On every perps venue set
  `maxLeverage` (default 2; the user picks, up to the server ceiling named in the tool description; more returns `limit_exceeded`). The approval page shows it, and the
  owner's deploy cannot use more.
- Krexa has a ceiling on max per trade and leverage for MCP deploys. A request
  above it returns `limit_exceeded` with the ceiling.
- The strategy is fixed when the user approves the deploy. Only the owner can
  change it, in the Krexa app.
- Only markets Krexa lists can be traded. Others are refused.

## What the MCP key cannot do

Withdraw, transfer, fund, delete, resume, or raise a limit. Those happen in the
Krexa app, signed by the owner.

## What Krexa does not have (do not claim it)

- A take-profit field. A rule can still exit on a gain if the strategy says so.
- A cap on the number of open positions.
- News-driven triggers.
