---
name: wallet-lookup
description: Look up any crypto wallet address. Use when the user pastes a wallet address or asks what a wallet holds, what it's worth, how much it has made or lost, how old it is, who funded it, what it has been doing, or whether it belongs to a known trader.
license: MIT
argument-hint: <wallet address>
---

# Look up a wallet

Tell the user who or what this wallet is, what it holds, and what it has done. Use the StalkChain connector. Limit lookups to the chains, information, and credit budget the user approved.

## 1. Identify the chain

- **Solana** addresses are base58, 32–44 characters.
- **EVM** addresses (Ethereum, Base, BNB Chain, Monad, Hyperliquid, Robinhood Chain) are `0x` followed by 40 hex characters. The same address string can appear on multiple EVM chains. Identify accounts by chain and address. An address match alone does not establish common ownership.

## 2. Look it up

Use the cheapest call that answers the question. If the user did not name a chain for an EVM address, ask which chain to check or offer a priced multichain lookup. Before making paid calls, state the selected chains, calls, and estimated total credits, then wait for approval unless the user already approved that scope and budget. Ask again before adding chains, paid checks, or exceeding that budget. Check live pricing first if the connector reports different charges.

**Solana wallet**
1. For profit, win rate, or trade history metrics: `stalkchain_wallet_pnl` with `wallet` (250 credits with `includeHoldings: false`, or 500 when the approved lookup includes current positions).
2. For holdings alone or a USD breakdown that the approved PnL call does not cover: `stalkchain_wallet_portfolio` with `wallet` and `chains: ["solana"]` (250 credits).

**EVM wallet**
1. For holdings or USD value: `stalkchain_wallet_portfolio` with `wallet` and the approved `chains` (250 credits per five chains, so 500 for all seven): holdings and USD value on the selected chains. Use `minValueUsd` to drop dust.
2. If the user wants age or lifetime activity: `stalkchain_wallet_age` with `wallet` and the approved `chains` (500 credits per chain). Treat a new wallet moving large sums as a reason to investigate.
3. If asked what it has been doing, or who funded it: `stalkchain_wallet_transfers` with `wallet` and `chain` (500 credits), newest first. Use `order: "asc"` to inspect the earliest returned transfers. Label the sender of an early inbound transfer a possible funding source unless other evidence establishes the connection.
4. If it trades perps, or the user asks about leverage or positions: `stalkchain_perps_wallet` with `wallet` (250 credits): its Hyperliquid account value, open longs and shorts with liquidation prices, profit by day, week, month and all time, and recent trades.

In Claude and ChatGPT, `stalkchain_wallet_portfolio` shows the user an interactive card. Don't re-list every holding; say what stands out. Where no card appears (a terminal), list the top holdings.

**Is it a known trader?** StalkChain can't look up who owns an arbitrary address: trader search matches names and handles, not wallets. If the user thinks it belongs to a particular trader, ask for the handle, run the **trader-check** skill, and compare the wallets it returns with this address.

## 3. Answer in this shape

**Wallet:** shortened address (`0x1234…abcd`), chain, and the trader's name if known.

**Worth now:** total USD value and its top five holdings.

**Track record:** on Solana, profit, win rate and number of tokens traded; on Hyperliquid, perps profit and open positions, if checked.

**Age and activity:** if checked, report first seen, number of transactions, and relevant caveats.

**Recent activity:** only if transfers were fetched. Summarise the largest moves; don't list everything.

To check how risky the holdings are, offer the **portfolio-review** skill.

## Rules

- A missing value is `null`, never zero. A chain listed under failed chains was not checked; it is not empty.
- Public blockchain data is public, but don't speculate about the real-world identity of a wallet owner beyond what the data shows.
- Keep raw JSON out of the answer. Data, not financial advice.
