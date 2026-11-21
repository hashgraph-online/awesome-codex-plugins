---
name: token-check
description: Check a crypto coin or token before buying it. Use when the user asks whether a coin is safe, legit, a rug, worth buying, who holds it, whether the dev or insiders are selling, whether smart money is in it, or pastes a token address or ticker and wants to know about it.
argument-hint: <token address or ticker>
---

# Check a coin before buying

Answer one question for the user: **what do the facts say about this coin right now?** Use the StalkChain connector. Every lookup spends the user's credits, so start with the cheapest call that can answer and only go deeper when the first results justify it.

## 1. Pin down the token

- A Solana mint is base58, 32–44 characters. An EVM contract is `0x` followed by 40 hex characters.
- If the user gave a ticker or name instead of an address, call `stalkchain_fomo_search` with `q` set to it and `type: "tokens"` (250 credits). If several tokens share the ticker, show the top matches with chain and market cap, and ask which one. Never guess between look-alikes: scam tokens copy popular tickers.

## 2. Run the core checks

**Solana**, cheapest first (in parallel where your client allows):

1. `stalkchain_token_onchain` with `token` (250 credits): true total holder count, whether the liquidity pool is burned, whether mint or freeze authority is still live, top-10 concentration, sniper and insider share, a risk score, and whether it is already flagged as rugged. If it is flagged rugged, say so and ask before spending more.
2. `stalkchain_token_quality` with `token` (250 credits): organic versus total volume. A low organic share means wash trading.
3. `stalkchain_fomo_analyze_token` with `address` (750 credits): buy and sell flow, tracked smart-money holders, and the dev's and insiders' positions in one call.

**EVM chains** (Base, BNB Chain, Ethereum, Monad, Robinhood Chain):

1. `stalkchain_evm_token_check` with `chain` and `token` (250 credits): whether it can be sold (honeypot), buy and sell tax, whether the owner can mint, pause or blacklist, verified code, holder concentration, the creator's past honeypots and locked liquidity, red flags first. If it says honeypot, stop and say so.
2. `stalkchain_fomo_analyze_token` with `address` (750 credits): flow, tracked smart-money holders and the dev's position. Skip it if step 1 already found a honeypot.

Never send a `0x` address to the Solana tools.

In Claude and ChatGPT, `stalkchain_fomo_analyze_token` shows the user an interactive card. Don't re-list its numbers; add what they mean and the verdict. Where no card appears (a terminal), include the key numbers.

## 3. Go deeper only when it matters

- The user mentions a position size, or liquidity looks thin: `stalkchain_token_exit_check` with `token` and `usd` set to their size (500 credits). This quotes what they would really get back on a sale.
- The coin is new (days old), or the dev is unknown: `stalkchain_token_deployer` with `token` (500 credits), which lists everything that wallet launched before and how each one ended.
- Many early wallets, or the launch looks sniped: `stalkchain_token_early_buyers` with `token` on Solana, or `stalkchain_evm_early_buyers` with `chain` and `token` on EVM (500 credits each). Both say whether the first buyers still hold.
- The user wants to know whether the big holders are leaving: `stalkchain_fomo_kol_sell_pressure` with `address` (375 credits).

## 4. Answer in this shape

**Verdict:** one plain sentence, e.g. "Several serious red flags" or "No major red flags found in the data".

**Red flags:** only the ones the data shows. Examples: honeypot or high sell tax, owner can still mint or pause, mint authority still live, LP not burned, dev sold, top 10 hold over 50%, mostly wash volume, deployer has dead launches, heavy sniper share, early buyers already exited.

**Good signs:** for example LP burned, authorities revoked, tracked traders holding, organic volume, buyers outnumbering sellers.

**Smart money:** how many tracked traders hold it and whether they are adding or selling.

**Can you get out?** Only if an exit check was run.

Then one line: *"This is data, not financial advice."*

## Rules

- A missing value is `null`, never zero. Say "not available", never "0".
- "Tracked traders" are a curated set of known traders, not every holder. Say "tracked traders" and keep them apart from total holders.
- An empty dev or insider list means no dev position is known. It does not mean the dev has none, and it is not a safety signal.
- Do not recommend buying or selling. Lay out the facts and let the user decide.
- Keep raw JSON out of the answer. Quote the numbers that matter, with units.
