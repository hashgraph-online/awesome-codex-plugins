---
name: stonkfun-launch-guide
description: Help plan a token launch on StonkFun, the Solana launchpad for tokens paired with tokenized stocks (xStocks) and stablecoins. Use when the user wants to launch a StonkFun token, pick a quote pair, understand bonding-curve pricing or graduation, choose standard or reward mode, see how similar launches did, or check whether their launch went through. Guidance only; the user signs everything.
argument-hint: "[quote pair, e.g. an xStock ticker]"
---

# Plan a StonkFun launch

Help the user decide **what to pair against, how the curve prices it, and how similar launches have done.** Use the StalkChain connector's `stonk_*` tools (250 credits each). This skill only reads data: it never launches, signs or sends anything. The user launches on StonkFun with their own wallet.

## 1. Choose a pair

`stonk_pairs` with `launchable: true` (and `launchLabReady: true` if they'll build a LaunchLab launch themselves): the quote tokens a launch can pair against, with category (xStock, stablecoin) and readiness. If the user named a stock or ticker, find its quote mint here.

## 2. Price the curve

`stonk_launchlab_pricing` with `quoteMint` from step 1: the amount the curve raises, the resulting starting and graduation market caps, and the virtual reserves. Explain these in plain terms: how much has to be bought for the token to graduate, and what market cap that means.

## 3. Learn from similar launches

1. `stonk_stats`: platform totals, graduation thresholds, and how many tokens graduated out of how many launched.
2. `stonk_tokens` with `quoteMint` and `sort: "marketCap"`: how the best launches on the same pair did, and with `sort: "newest"`, how recent ones are doing.
3. `stonk_launches` with `mode` (`standard` or `reward`) and `since`: recent launches in the mode the user is considering.
4. Optional, ask first: `stonk_token_report` with `mint` on one or two comparable launches (about 1,250 credits each) for their burns, fees and rewards. In Claude and ChatGPT it shows a card.

## 4. Standard or reward mode

Reward-mode tokens charge a transfer tax that is paid out to holders; standard tokens don't. Show the trade-off with real numbers from step 3: how reward launches have fared next to standard ones on the same pair.

## 5. After the launch

When the user has a payment signature, `stonk_launch_status` with `paymentSignature` says whether the launch completed. If it is still processing, check again shortly.

## Answer in this shape

**Pair:** the chosen quote token and why it fits, with alternatives.

**Curve:** starting market cap, graduation market cap, and what it takes to get there.

**Benchmarks:** graduation rate, and the typical and best market caps of similar launches.

**Mode:** standard or reward, with the trade-off.

**Checklist:** what the user will do and sign themselves on StonkFun.

Then one line: *"This is data and guidance, not financial advice."*

## Rules

- Never ask for, accept or handle a private key, seed phrase or signed transaction. The user signs everything on StonkFun.
- Never promise a launch will graduate or make money. Past launches are benchmarks, not forecasts.
- A missing value is `null`, never zero. Keep raw JSON out of the answer.
