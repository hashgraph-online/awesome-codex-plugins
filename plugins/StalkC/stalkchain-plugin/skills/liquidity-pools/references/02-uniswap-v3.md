# Uniswap v3: ranges, accounting, position control and oracle limits

## Scope and version

As observed **2026-10-02 UTC**. This is a read-only mechanics reference, not a recommendation to provide liquidity. It combines the March 2021 [v3 whitepaper][wp], current official documentation, and immutable reference-source snapshots:

- `Uniswap/v3-core@d0831dc6b8a318df3872b6d68f6de135c9f3ec29`.
- `Uniswap/v3-periphery@0682387198a24c7cd63566a2c58398533860a5d1`.

These commits are **not asserted to match any deployed bytecode**. No chain, pool, block or position was read from RPC in this lane. Current documentation is evidence of intended/documented behavior, not a live-state verification. Core and periphery audits were preserved as PDFs with page-numbered extracts; an audit is scoped to its own reviewed revision, not automatically the revisions above. Public citations below identify the primary sources; short claim labels are descriptive, not bundled manifest lookups.

## 1. Identify the pool before interpreting a price

The core factory sorts token addresses numerically, so `token0` is not necessarily ETH, the base asset, the token with more decimals, or the ticker shown first by an interface. Within a factory, the token pair and fee identify a pool. Record chain ID, factory, pool address, `token0`, `token1`, both decimal counts, `fee`, `tickSpacing`, and the block used. A fork with familiar function names is not necessarily canonical Uniswap v3.

The constructor in the pinned factory enables `500 → 10`, `3000 → 60`, `10000 → 200` (fee pips → tick spacing). Fee pips have a denominator of 1,000,000: these correspond to 0.05%, 0.30%, 1%. **Do not freeze this constructor list into a universal deployment list.** The owner can enable additional fee/spacing pairs; current official protocol-fee documentation also discusses the 0.01% tier. Read the chosen factory's mapping at the observation block. The same token pair at another tier is another pool with its own liquidity, price and oracle history.

Evidence: `uni-v3-token-order`, `uni-v3-initial-tiers`, `uni-v3-enable-tiers`; [Factory source][factory], document `uni-v3-core-contracts-uniswapv3factory-sol`.

## 2. Decode sqrt price, decimals and ticks

Let `S = sqrtPriceX96`, `d0 = decimals(token0)`, `d1 = decimals(token1)`.

```text
sqrt raw price = S / 2^96
raw price = (S / 2^96)^2                 # raw token1 units / raw token0 units
human token1/token0 = raw price * 10^(d0-d1)
human token0/token1 = 1 / human token1/token0
price at tick i = 1.0001^i                # raw ratio, not decimal-adjusted
```

Use integer or high-precision math; do not square a large `uint160` in an insufficient integer width or a JavaScript Number. The tick is a discretized price index, not a percentage fee and not a token amount. TickMath covers ticks from -887272 to 887272. Its inverse square-root-price domain excludes the maximum ratio. The pool's stored tick can differ from simply re-deriving a tick at an exact crossing boundary; use stored tick for accounting and `sqrtPriceX96` for precise spot-price conversion.

A position's boundaries must be usable multiples of its pool's tick spacing. There are many possible current ticks between usable position boundaries. For spacing 60, flooring tick 100 to a usable boundary yields 60; flooring -1 yields -60, **not 0**. Choose floor/ceil intentionally depending on the desired economic range; blindly rounding both bounds can accidentally narrow or collapse it.

**Executed decimal example:** hypothetical token0 has 18 decimals and token1 has 6. For a human quote of 2000 token1/token0, the computed `S` is `3543191142285914205922034`. Decoding gives `2000.000000000000000000` token1/token0, or `0.000500000000000000` token0/token1 at the displayed precision. Tick 100 implies raw ratio `1.010049662093`. These are illustrative inputs, not a queried market.

Evidence: `uni-v3-q96`, `uni-v3-tick-bounds`; [TickMath][tickmath], document `uni-v3-core-contracts-libraries-tickmath-sol`; [whitepaper][wp] §6.1 and §6.2. Math replay below.

## 3. Liquidity is not deposited token count or TVL

Write `a = sqrt(P_lower)`, `b = sqrt(P_upper)`, `s = sqrt(P)`, and `L` for position liquidity. In consistent raw-token units, ignoring integer rounding:

| Price regime | token0 inventory x | token1 inventory y |
|---|---:|---:|
| `s <= a` | `L(1/a - 1/b)` | `0` |
| `a < s < b` | `L(1/s - 1/b)` | `L(s-a)` |
| `s >= b` | `0` | `L(b-a)` |

At the lower boundary inventory is all token0; at the upper it is all token1. Active-liquidity accounting uses lower-inclusive/upper-exclusive tick intervals; exact crossing direction and stored tick matter at the boundary. Liquidity out of range does not earn swap fees, but previously accrued fees remain separately claimable. Inventory converts continuously while the price traverses a range; returning through it reverses that conversion. A narrow range order is therefore not an irreversible limit order unless its owner subsequently removes the position.

Inside the range, virtual reserves are `L/s` and `L*s`; actual position reserves subtract the boundary offsets. The translated invariant is:

```text
(x + L/b) * (y + L*a) = L^2
```

The whitepaper's equation 2.2 and figures were visually checked against the preserved PDF. Virtual reserves describe local curve depth; they are not spendable assets sitting in the contract. Aggregate ERC20 balances can additionally include inactive positions, accrued fees and protocol fees. Neither aggregate balances nor TVL equal the amount available at a desired execution price.

**Executed illustrative example:** equal-decimal units, `L=1000`, `P_lower=1`, `P_upper=4`:

| Price | token0 | token1 |
|---:|---:|---:|
| 0.81 | 500.000000000 | 0.000000000 |
| 2.25 | 166.666666667 | 500.000000000 |
| 4.84 | 0.000000000 | 1000.000000000 |

At price 2.25, virtual reserves are 666.666666667 token0 and 1500 token1, not the actual 166.666666667 and 500. This continuous-boundary example is pedagogical: price 4 need not be an exactly usable tick. A separate tick-aligned example with spacing 60, ticks `[0,120]`, current tick 60 and `L=1000` produces `2.986382804599` token0 and `3.004354062742` token1. Production amounts must apply protocol rounding in raw units, then decimals.

Evidence: `uni-v3-concentration`, `uni-v3-inventory-regimes`; document `uni-v3-whitepaper`, PDF p.2 §2/§2.1 and p.8 liquidity formulas; [whitepaper][wp]; document `uni-v3-periphery-contracts-libraries-liquidityamounts-sol`, [LiquidityAmounts][amounts].

## 4. Fees: growth, checkpoints and what collect means

For each token, the core tracks global fee growth and outside fee growth at ticks. Inside growth is global growth less growth below the lower boundary and above the upper boundary, with the below/above calculations selected using current tick. **Do not subtract both outside values unconditionally when price is outside the position.** Crossing flips the tick's outside accumulator relative to global growth. The equation and signs were visually checked on whitepaper p.7, equations 6.17–6.21.

Conceptually, earned fees since a position checkpoint are:

```text
floor(L_previous * (feeGrowthInsideNowX128 - feeGrowthInsideLastX128) / 2^128)
```

The subtraction follows the contract's uint256 wraparound semantics. Use the liquidity that was active during that interval, not the newest liquidity amount retroactively. `tokensOwed` is a checkpointed balance, so merely reading it can understate fees not yet crystallized. Fees are not automatically reinvested into `L`: collecting, then increasing liquidity is a separate operation and may change inventory exposure.

Core `collect` transfers previously recorded `tokensOwed`; it does not itself recompute fresh fee growth. Core `burn(lower,upper,0)` is the fee-update “poke” for a nonempty position. The NFT manager's `collect` invokes this poke when it still has liquidity, and then attributes fees to the relevant NFT. NFTs with the same range can share a manager-owned core position, so core storage under the manager is not necessarily one NFT's balance.

**Crucial accounting distinction:** amounts returned by `collect` may contain withdrawn principal previously credited by `burn`, not just swap fee income. A `Collect` event alone is not a realized-profit ledger. Reconstruct deposits, decreases, fee checkpoints, actual transfers and token prices through time.

Executed fee-growth toy: `L=1000`, inside growth increases by `3*2^128`; fees owed are `3000` raw units of that token. This does not imply 3000 human tokens or any annualized yield.

Evidence: `uni-v3-fee-growth`, `uni-v3-core-collect`, `uni-v3-nft-collect-poke`, `uni-v3-fees-not-auto-compound`; [Position library][position], [pool][pool], [NFT manager][nft], [whitepaper][wp] §6.3–§6.4.

### Protocol fees are configuration, not a timeless constant

The pinned core allows token-specific protocol-fee denominators 4 through 10, or zero for disabled. A denominator is a share of the swap fee, not a second fee of that percentage of trade notional. Current official documentation reports protocol fees on selected v3 pools and shows different shares by fee tier. Do not repeat old “all fees go to LPs” material as a current universal truth, or apply the current docs table to an unqueried pool. Read `slot0.feeProtocol`, factory authority and selected network/pool state. The official page's approximate “1/6” headline is not an exact description of every row in its own table.

Evidence: `uni-v3-fee-protocol`, `uni-v3-current-fee-docs`; [core setFeeProtocol][pool]; [current protocol-fee documentation](https://developers.uniswap.org/docs/protocols/protocol-fee/concepts/fees), document `uni-docs-protocols-protocol-fee-concepts-fees`.

## 5. Position operations and the three different meanings of burn

| Operation | Effect | What it does NOT prove |
|---|---|---|
| Core `mint` | Adds liquidity and collects payment through an authenticated integration callback | A permanent lock |
| NFT manager `increaseLiquidity` | Adds exposure to the existing range | That fees compounded automatically |
| Core `burn(lower,upper,amount)` | Removes liquidity and credits token amounts to `tokensOwed` | Destruction of a receipt NFT or permanent lock |
| NFT manager `decreaseLiquidity` | Authorized partial/full removal; invokes core burn and checks minimum amounts/deadline | Immediate payment to the wallet |
| NFT manager `collect` | Transfers owed principal/fees up to maxima | That the full transfer is profit |
| NFT manager `burn(tokenId)` | Destroys a cleared NFT; requires zero liquidity and zero owed balances | Locking funded liquidity |

A standard removable NFT position ordinarily has authorized decrease and collection paths. Ownership, NFT approvals/operators, permit authority, custody contract restrictions, and any manager/wrapper rescue logic determine who can use those paths. An NFT transfer to a contract is not automatically an irrevocable lock. A burn of the underlying ERC20 supply is unrelated to destruction of the LP receipt. An NFT burn event from this manager is evidence the position was cleared first—not evidence its principal remains permanently in the pool.

The core callback must pay amounts owed; the pool checks its balance increases. Integrations must authenticate the actual pool/callback origin and not let an arbitrary caller instruct token payments. Educational guide values such as zero minima are not sensible production slippage protections. A read-only review may identify required calldata, but this reference provides no approval to sign or execute it.

Evidence: `uni-v3-mint-callback`, `uni-v3-burn-credit`, `uni-v3-nft-decrease`, `uni-v3-nft-burn-empty`; [pool][pool], [NFT manager][nft]; documents `uni-v3-core-contracts-uniswapv3pool-sol` and `uni-v3-periphery-contracts-nonfungiblepositionmanager-sol`.

## 6. Oracle observations: useful history, not independent fair value

`observe([lookback,0])` returns tick cumulatives and seconds-per-liquidity cumulatives. The cumulative tick difference divided by elapsed seconds gives a time-weighted arithmetic mean tick; exponentiating the mean tick gives a geometric time-weighted price. It is not the arithmetic mean of spot prices. `OracleLibrary.consult` rounds a negative nonintegral mean tick toward negative infinity. Decimals and quote direction still apply.

Observation capacity must be increased before it can store more history, and new slots only become useful as observations are written. Requesting a time older than the oldest usable observation fails. Increasing capacity now does not backfill historical observations. `secondsPerLiquidity` supports a harmonic-mean liquidity statistic, not time-weighted TVL or guaranteed order-book depth.

Safety checklist:

1. Check the exact pool, earliest observation and usable lookback rather than assuming a standard window exists.
2. Check meaningful liquidity and whether prices were maintained by trading during the period.
3. Distinguish current spot (`slot0`) from a properly computed time-weighted value.
4. Evaluate manipulation cost for the actual pool, duration, neighboring liquidity and external market—not just the nominal window length.
5. Handle stale/absent observations, chain/sequencer assumptions and token anomalies explicitly. Use an independent valuation/risk source where the application requires it.

No TWAP removes depeg, concentrated ownership, toxic order flow or a persistent manipulated market. It averages this pool's historical state, not an independent guarantee of fair value.

Evidence: `uni-v3-observe`, `uni-v3-oracle-rounding`, `uni-v3-oracle-old`, `uni-v3-oracle-capacity`, `uni-v3-oracle-geometric`; [oracle guide](https://developers.uniswap.org/docs/protocols/v3/concepts/price-oracles), document `uni-v3-docs-concepts-price-oracles`; [OracleLibrary][oraclelib], document `uni-v3-core-contracts-libraries-oracle-sol`; [whitepaper][wp] §5.

## 7. Token and economic limits

Official documentation warns standard v3 routers do not support fee-on-transfer tokens. It also warns negative rebases can impose unrecoverable losses on active LPs even though pool creation and swapping can succeed. Mint, freeze, pause, blacklist, upgrade and transfer-hook powers are additional token-specific review questions; a normal-looking pool does not neutralize them. A wrapper/custom router must be audited as new integration risk, not assumed to fix every nonstandard behavior.

Narrower ranges increase local capital efficiency but can become inactive and leave inventory entirely in the depreciating asset. Fees must be evaluated against inventory mark-to-market changes, adverse selection, rebalancing and gas costs. Nothing in these contract mechanics guarantees positive net PnL.

Evidence: `uni-v3-fee-on-transfer`, `uni-v3-negative-rebase`; [token integration issues](https://developers.uniswap.org/docs/protocols/v3/concepts/unsupported-tokens), document `uni-v3-docs-concepts-unsupported-tokens`; economic interpretation follows the inventory formulas, not a performance claim.

## 8. Reproducibility and gaps

The upstream math script and result artifacts are not shipped. The following are historical research outputs, not a command run by this plugin release. Six exact integer outputs reproduce pinned official `SqrtPriceMath.spec.ts` literals:

```text
next sqrt after 0.1 token1 in: 87150978765690771352898345369
next sqrt after 0.1 token0 in: 72025602285694852357767227579
amount0 up/down for sqrt(1) -> sqrt(1.21), L=1e18:
90909090909090910 / 90909090909090909
amount1 up/down: 100000000000000000 / 99999999999999999
```

These are independently executed Python integer formulas compared with official expected literals; **the Solidity/Hardhat suite was not installed or run**. Decimal presentation tolerances are the last displayed digit. Primary test source: `uni-v3-core-test-sqrtpricemath-spec-ts`, claim `uni-v3-fixed-vector`, [immutable test][tests].

Remaining gaps: no deployment bytecode matching, RPC fee/owner/oracle observations, live token-authority review or economic backtest. Extracted PDFs can break symbol order, so rely on inspected page images plus pinned math code for formulas. The source acquisition report records transport failures and recoveries; no claim of exhaustive Uniswap documentation or audit-finding coverage is made.

[wp]: https://app.uniswap.org/whitepaper-v3.pdf
[factory]: https://github.com/Uniswap/v3-core/blob/d0831dc6b8a318df3872b6d68f6de135c9f3ec29/contracts/UniswapV3Factory.sol
[pool]: https://github.com/Uniswap/v3-core/blob/d0831dc6b8a318df3872b6d68f6de135c9f3ec29/contracts/UniswapV3Pool.sol
[tickmath]: https://github.com/Uniswap/v3-core/blob/d0831dc6b8a318df3872b6d68f6de135c9f3ec29/contracts/libraries/TickMath.sol
[position]: https://github.com/Uniswap/v3-core/blob/d0831dc6b8a318df3872b6d68f6de135c9f3ec29/contracts/libraries/Position.sol
[nft]: https://github.com/Uniswap/v3-periphery/blob/0682387198a24c7cd63566a2c58398533860a5d1/contracts/NonfungiblePositionManager.sol
[amounts]: https://github.com/Uniswap/v3-periphery/blob/0682387198a24c7cd63566a2c58398533860a5d1/contracts/libraries/LiquidityAmounts.sol
[oraclelib]: https://github.com/Uniswap/v3-periphery/blob/0682387198a24c7cd63566a2c58398533860a5d1/contracts/libraries/OracleLibrary.sol
[tests]: https://github.com/Uniswap/v3-core/blob/d0831dc6b8a318df3872b6d68f6de135c9f3ec29/test/SqrtPriceMath.spec.ts
