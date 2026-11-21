# Uniswap v4: pool identity, hooks, settlement and liquidity control

## Scope and version

Observed **2026-10-02 UTC**. Primary-source mechanics reference, not an execution guide or safety certification. It uses the August 2024 [v4 whitepaper][wp], current official docs and pinned source:

- `Uniswap/v4-core@46c6834698c48bc4a463a86d8420f4eb1d7f3b75`.
- `Uniswap/v4-periphery@9969eec44cfdf07e24b41de47f40276a58401976`.

**No deployed-code matching or RPC verification was performed.** The pinned periphery can contain behavior newer than the periphery at a particular deployment; do not infer chain state from its default branch. Audit PDFs were acquired at these repository revisions, including explicitly draft-named reports and permissioned-pool-specific reports. Their scope and reviewed revisions must be checked before using them to assess a deployment. A core audit is not an audit of arbitrary hooks.

Read [v3 mechanics](02-uniswap-v3.md) for the base concentrated-liquidity formulas. Most of that math remains relevant to a standard v4 concentrated pool, but **custom accounting can change the trade's total economic behavior**.

## 1. Singleton is shared settlement, not one undifferentiated pool

The `PoolManager` singleton holds many pools and provides their accounting and settlement layer. A pool is identified by a key, not by a dedicated v3-style pool contract address. The complete `PoolKey` is:

```text
(currency0, currency1, fee, tickSpacing, hooks)
```

Currencies are sorted numerically and must differ. `PoolId = keccak256(abi.encode(PoolKey))`, hashing five ABI words, not packed address concatenation and not NIST SHA3-256. Fee and tick spacing are separate key fields: v4 does not derive spacing from v3 fee-tier defaults. Dynamic keys have the exact sentinel fee `0x800000`; the current effective fee lives in pool state and is not substituted into the key hash.

For a deployment identity record, capture chain ID + PoolManager address + full PoolKey + PoolId + block hash. The same PoolKey/PoolId on another chain or manager is not the same economic deployment. A token ticker pair alone is inadequate; changing hook, fee or spacing identifies another pool. Initialization fixes the starting sqrt price, so initialization needs appropriate price validation; creating a pool does not prove an independently meaningful market price.

The hook address is fixed in the key, but its internal settings, administrator, dependencies or implementation can still change if that hook was designed that way. “Cannot swap the hook address” and “immutable behavior forever” are different propositions.

Evidence: `uni-v4-key`, `uni-v4-id`, `uni-v4-init-order`, `uni-v4-hook-key-fixed`; documents `uni-v4-core-src-types-poolkey-sol`, `uni-v4-core-src-types-poolid-sol`, `uni-v4-core-src-poolmanager-sol`; [PoolKey][key], [PoolId][id], [PoolManager][manager], [hooks documentation][hookdocs].

## 2. Position identity: core storage, receipt NFT and currency claims

Core liquidity positions are indexed by pool and a hash of **owner, lower tick, upper tick, salt**. Salt distinguishes positions with the same owner/range. Core does not make every liquidity position an ERC721. For `PoolManager.modifyLiquidity`, the core owner is the calling contract (`msg.sender`), often a position manager, not the user's wallet.

The pinned official periphery `PositionManager` mints ERC721 receipt tokens and uses `bytes32(tokenId)` as salt. Its authorization and accounting map the NFT to the manager-owned core position. Other integrations may use different receipts, custody, salts or no NFT at all. Review the actual integration rather than asking only who owns a superficially similar token ID.

A separate concept is PoolManager's **ERC-6909 currency claims**. These represent claims on a currency held by the manager; they are not concentrated-liquidity shares and do not encode a tick range or a share of LP fee growth. Minting these claims debits the caller's currency delta; burning authorized claims credits the delta. Integrators can use claims in settlement without repeatedly transferring the underlying ERC20. Burning a currency claim is not burning LP principal into an inaccessible position.

| Object/action | Meaning |
|---|---|
| Core position key | Manager/owner + ticks + salt within a pool |
| Periphery ERC721 | Receipt/control surface chosen by that periphery |
| ERC-6909 currency claim | Redeemable accounting claim on one currency |
| Manager's `burn(from,id,amount)` | Consumes ERC-6909 currency claims |
| Periphery burn-position action | Removes/destroys a liquidity receipt according to that periphery |

Evidence: `uni-v4-position-key`, `uni-v4-core-modify-owner`, `uni-v4-position-nft-mint`, `uni-v4-position-salt`, `uni-v4-claim-mint`, `uni-v4-claim-burn`; [core Position][position], [PositionManager][positions], [ERC-6909 documentation](https://developers.uniswap.org/docs/protocols/v4/concepts/erc-6909), document `uni-docs-protocols-v4-concepts-erc-6909`.

## 3. Flash accounting: debts must net to zero

A caller enters `PoolManager.unlock(data)`. The manager invokes **that caller's** `unlockCallback`, inside which swaps, liquidity changes and settlement can be composed. Balance-changing operations track transient deltas per account and currency. Negative means the account owes currency to the manager; positive means the manager owes the account. After the callback, the manager checks that the count of nonzero deltas is zero; otherwise the entire transaction reverts. Zero total value in dollars is not enough: every relevant currency/account debt must resolve.

Typical ERC20 settlement sequence is `sync(currency)` **before** transferring payment, then `settle()` or the appropriate `settleFor` path. The manager credits the measured balance increase from its synced reserves. Paying first and syncing afterward is not equivalent. `take` receives a currency credit as an external transfer; claim mint/burn can resolve deltas through internal claims. `clear` intentionally discards an exact positive credit: it is not a generic “fix my unsettled debt” function.

Native ETH is represented by zero-address currency, distinct from WETH. Native settlement uses `msg.value`. The pinned source explicitly recommends syncing even for native settlement to avoid denial-of-service scenarios involving the synced currency state. A native transfer can invoke recipient code; it is not automatically equivalent to an ERC20 transfer or free of reentrancy considerations.

Initialization is not a balance-changing liquidity operation and can occur outside an unlock. Unlock is a transaction-level settlement boundary, not a promise that hook callbacks cannot call other pools or external protocols while an operation is in progress.

**Executed docs-example arithmetic** (deliberately ignores swap fees, rounding and price impact): swap deltas `(-5 USDC,+5 USDT)` then add-liquidity deltas `(-15 USDC,-25 USDT)` gives final deltas `(-20,-20)`. The integrator owes 20 of each; there is no need to transfer the intermediate 5 USDT out and back. The savings come from netting, not the ability to finish with unpaid debt. Real paths with extra currencies, hook obligations or claim usage can require more than the simplified “two transfers” marketing illustration.

Evidence: `uni-v4-unlock-settle`, `uni-v4-settle-balance`, `uni-v4-native-settle`, `uni-v4-clear`, `uni-v4-claim-mint`, `uni-v4-claim-burn`; [PoolManager][manager]; [flash accounting guide](https://developers.uniswap.org/docs/protocols/v4/concepts/flash-accounting), document `uni-v4-docs-concepts-flash-accounting-extract`; [callback guide](https://developers.uniswap.org/docs/protocols/v4/guides/unlock-callback-and-deltas), document `uni-docs-protocols-v4-guides-unlock-callback-and-deltas`.

## 4. Hook permissions: decode the address, then inspect the code

The pinned library examines the **lowest 14 bits** of a hook address. Address flags tell the manager which callback capabilities to use; they are not an audit result, authorization certificate or proof of benign behavior.

| Bit | Flag |
|---:|---|
| 13 / 12 | beforeInitialize / afterInitialize |
| 11 / 10 | beforeAddLiquidity / afterAddLiquidity |
| 9 / 8 | beforeRemoveLiquidity / afterRemoveLiquidity |
| 7 / 6 | beforeSwap / afterSwap |
| 5 / 4 | beforeDonate / afterDonate |
| 3 / 2 | beforeSwapReturnsDelta / afterSwapReturnsDelta |
| 1 / 0 | afterAddLiquidityReturnsDelta / afterRemoveLiquidityReturnsDelta |

Return-delta permission requires the corresponding action flag. A zero-address hook is valid for a static-fee pool, but not for a dynamic-fee pool. A nonzero dynamic-fee hook can be valid even without lifecycle callback bits, because it can update fees through its authorized manager call.

Hook deployment helpers commonly validate declared permissions against address bits, and CREATE2 salt mining can produce the required address. **Do not elevate a base-class helper into a universal core guarantee.** The core uses address bits and validates call responses; it does not prove an arbitrary hook's entire implementation is safe merely because a `getHookPermissions` function reports a struct. At runtime required selectors/response lengths matter. Missing bits can mean code is never called; bad enabled callbacks can make operations revert.

An executed mask example: beforeSwap (bit 7) plus beforeSwapReturnsDelta (bit 3) is `0x88` / decimal `136`. Decode the actual address with `uint160(address) & ((1<<14)-1)`, not with this example suffix. The pinned helper also skips a hook callback when the hook is itself the original caller for that action, so do not build a universal invariant on “every action always invokes my hook.”

For liquidity-control review, remove-liquidity hooks deserve the same attention as swap hooks. They can introduce permission checks, withdrawal fees, dependencies or reverts. Hooks shared across multiple pools must key mutable state correctly and withstand nested calls involving those pools. A global manager lock is not a substitute for reasoning about arbitrary external calls during a callback.

Evidence: `uni-v4-hook-mask`, `uni-v4-return-permission`, `uni-v4-dynamic-needs-hook`, `uni-v4-hook-self-call`; [Hooks.sol][hooks], document `uni-v4-core-src-libraries-hooks-sol`; [IHooks interface][ihooks]. The docs' generic permission-validation wording is interpreted narrowly in light of core source, not as certification.

## 5. Static fees, dynamic LP fees, protocol fees and hook charges

Keep four quantities distinct:

1. **PoolKey fee:** static pips or the dynamic sentinel; part of pool identity.
2. **Effective LP swap fee:** static fee or current/overridden dynamic pips accruing through LP accounting.
3. **Protocol fee:** separately configured by direction under the manager's protocol-fee machinery.
4. **Hook-imposed charge/adjustment:** custom accounting or other hook logic; not necessarily LP revenue.

Static LP fees can range from 0 to 1,000,000 pips. One pip is one hundredth of a basis point (0.0001%). The dynamic sentinel is **exactly** `0x800000`. It is not 8,388,608 fee pips. The dynamic capability is determined by the key and cannot be toggled in place. The pinned LPFeeLibrary initializes a dynamic pool's stored fee at zero; inspect whether a hook updates it on initialization or later.

Two dynamic update routes:

- `updateDynamicLPFee(key,newFee)`: only `key.hooks` may call, and the key must be dynamic. It updates stored pool fee.
- A permitted `beforeSwap` return can override the LP fee for that swap when marked by `0x400000`; the valid fee remains subject to the cap. An override is not necessarily a persistent stored-fee update.

Dynamic LP fees can be as high as 100%. An exact-output swap cannot function with a 100% swap fee in the pinned pool math. Hooks can condition fees on state or caller-related inputs, so a prior quote may not describe an actual transaction's fee. Evaluate worst-case permissions, slippage/deadlines and recipient routing—not only the displayed current percentage. There is no general guarantee that a dynamic model improves LP profitability.

In the pinned v4 protocol library, the per-direction protocol fee cap is 1000 pips (0.1%). It is applied before the LP fee. Combined fee pips are:

```text
protocolPips + lpPips - floor(protocolPips * lpPips / 1_000_000)
```

Executed example: protocol=1000, LP=3000 → combined=3997 pips = **0.3997%**, before any hook charge. This is an arithmetic example, not a deployed pool's configured fee.

**Zero LP fee does not mean free trading.** A hook can charge independently, a protocol fee may apply, and execution still has price impact and gas costs. Also separate LP income from money routed to a hook treasury, launchpad creator or integrator. Do not multiply a nominal pool fee by total volume and call it the LP's net return without accounting for the actual distribution and active-liquidity share.

Evidence: `uni-v4-dynamic-sentinel`, `uni-v4-fee-cap`, `uni-v4-fee-update-authority`, `uni-v4-protocol-fee-combine`, `uni-v4-protocol-fee-cap`, `uni-v4-hook-fees-distinct`; [LPFeeLibrary][lpfee], [ProtocolFeeLibrary][protocolfee], [PoolManager][manager], [Pool math][poolmath], [dynamic-fee docs](https://developers.uniswap.org/docs/protocols/v4/concepts/dynamic-fees), document `uni-v4-docs-concepts-dynamic-fees-extract`.

## 6. Custom accounting is a separate risk surface

Before-swap return deltas can change the amount the concentrated-liquidity engine processes. If the hook absorbs the complete specified amount, remaining core swap amount can be zero; a custom curve or other mechanism may be performing the economics instead of ordinary CL execution. The pinned helper disallows converting exact-input to exact-output (or vice versa) through a return delta, but that check does not certify the hook's pricing or inventory solvency.

After-swap and after-liquidity return deltas can change the caller's outcome where permissions allow. The manager accounts corresponding hook deltas; all obligations must settle by unlock completion. “Deltas net to zero” is an accounting condition, **not a proof that the user received a fair price** or that hook-held external collateral is safe.

For `modifyLiquidity`, core calculates principal and `feesAccrued`, combines them into callerDelta, then permits hook adjustment. A feesAccrued value is not automatically the amount actually paid to a wallet. Follow post-hook deltas, settlement/take/claim actions, recipients and transaction-level transfers. A hook can add withdrawal economics or external-protocol dependencies that are absent from baseline v3 math.

Audit questions:

- Which callbacks and delta-return permissions are actually enabled?
- Can hook governance change fees, allowlists, curve parameters or withdrawal conditions?
- Can implementation/dependencies upgrade while the hook address remains fixed?
- Does hook state isolate each PoolId, position owner, salt and currency?
- What happens on nested same-/cross-pool calls or oracle changes during callbacks?
- Are rounding direction, precision, extreme inputs and zero-liquidity cases tested?
- Can removal fail because an external lending market, token or oracle reverts?
- Who receives additional charges and can principal be diverted through an exceptional path?

Evidence: `uni-v4-before-swap-delta`, `uni-v4-after-liquidity-delta`, `uni-v4-fees-principal-delta`; [Hooks.sol][hooks], [PoolManager][manager]; [custom-accounting guide](https://developers.uniswap.org/docs/protocols/v4/guides/custom-accounting), document `uni-docs-protocols-v4-guides-custom-accounting`; [security framework](https://developers.uniswap.org/docs/protocols/v4/security), document `uni-v4-docs-security-extract`.

## 7. Increase, decrease, collect and burn: do not import v3 semantics blindly

The pinned periphery implements an action-oriented interface composing liquidity changes and settlement. Read its dispatcher, authorization and recipients before deriving control from a function/event name.

- **Add/increase** creates additional liquidity exposure and corresponding obligations. Fees from an existing position can contribute to net deltas, but this is not automatic compounding by merely holding it.
- **Decrease** removes specified liquidity and credits deltas. Pinned code checks minimum output against principal delta rather than letting fees mask principal slippage.
- **Collect fees** uses a decrease with zero liquidity for an existing nonempty position, then takes/resolves the currency credits. A hook can still affect the surrounding economics.
- **Burn position** in this pinned v4 periphery can burn the receipt **and remove nonzero liquidity in the same action**. This is materially different from v3 NFT burn's requirement that liquidity and owed balances already be zero. A burn event does not establish a permanent funded lock in either version.
- **Mint from deltas** in this pinned revision has an explicit code warning: using available credits to determine minted liquidity can admit price manipulation that reduces minted liquidity without triggering the same max-input checks. The source recommends explicit-liquidity mint for that protection. Treat this as a reference-revision warning, not a claim that every deployed manager exposes the exact same implementation.

A read-only principal-control analysis should identify both the NFT holder/approved operator and the integration contract that owns the core position. If the position is held in a locker, inspect its withdrawal, unlock, rescue, migration, approval and upgrade paths. Locked initial launch liquidity does not prevent someone else from minting and later removing an independent position in the same pool.

Evidence: `uni-v4-collect-zero-decrease`, `uni-v4-position-salt`, `uni-v4-burn-removes`, `uni-v4-delta-mint-slippage`; [PositionManager][positions], document `uni-v4-periphery-src-positionmanager-sol`; [fee collection guide](https://developers.uniswap.org/docs/protocols/v4/guides/managing-liquidity/collect-fees), document `uni-v4-docs-guides-managing-liquidity-collect-fees-extract-html`.

## 8. Oracles, token compatibility and security frameworks

Do not expect every v4 pool to expose the v3 built-in oracle/`observe` interface. The whitepaper places oracle functionality among the behaviors hooks can implement. Determine whether this specific pool/hook has an oracle, what observations it stores, what manipulation/staleness assumptions it makes and who can alter it. A v3-style TWAP formula does not magically create history in a v4 pool.

Flash accounting and native-asset support do not make fee-on-transfer, rebasing, callback-bearing, freezable or upgradeable tokens universally safe. Token behavior must fit the exact settlement integration. Hook wrappers and lending deposits add independent custody, redemption and insolvency assumptions. A zero-delta transaction can still involve poor execution, frozen assets or insecure claims outside the manager.

The Uniswap Foundation's security framework is expressly **self-directed and non-certifying**. It supplies risk dimensions and suggested assurance practices; the Foundation does not audit or endorse implementations merely because they use the worksheet. Treat core audits, periphery audits, hook audits, math review, governance review and deployment matching as separate scopes. Draft audit PDFs and old reviewed hashes must not be marketed as a current all-clear.

Evidence: `uni-v4-hooks-oracles`, `uni-v4-security-not-certification`; [whitepaper][wp] p.1; [security framework](https://developers.uniswap.org/docs/protocols/v4/security), document `uni-v4-docs-security-extract`. The framework's incident examples were not independently investigated here and are not used as established exploit findings.

## 9. Practical read-only answer contract

When asked whether a v4 pool is safe, free, locked or removable, report:

1. **Identity:** chain, manager, PoolId and complete PoolKey, observed block/date.
2. **Code:** core/periphery/hook implementation hashes and whether source matches; unknown when unverified.
3. **Principal control:** actual position owner, receipt, salt, approvals, withdrawal hooks and exceptional paths.
4. **Fee control:** effective LP fee, dynamic update authority, protocol config and hook/creator recipients.
5. **Economics:** active range/depth, inventory exposure, total execution costs, not just displayed TVL/APR.
6. **Residual risk:** upgrades, token powers, external dependencies, hook math, MEV and oracle assumptions.
7. **Evidence/unknowns:** primary links, document/claim IDs and what remains unqueried. Never infer a lock solely from a burned receipt or a dead-looking address.

No wallet approval, transaction, paid API, package installation or deployment is authorized by this reference. The upstream math/replay commands and acquisition reports are not shipped. The examples state their inputs and formulas for independent reproduction; their historical outputs do not imply chain execution or tests run by this plugin release.

[wp]: https://app.uniswap.org/whitepaper-v4.pdf
[key]: https://github.com/Uniswap/v4-core/blob/46c6834698c48bc4a463a86d8420f4eb1d7f3b75/src/types/PoolKey.sol
[id]: https://github.com/Uniswap/v4-core/blob/46c6834698c48bc4a463a86d8420f4eb1d7f3b75/src/types/PoolId.sol
[manager]: https://github.com/Uniswap/v4-core/blob/46c6834698c48bc4a463a86d8420f4eb1d7f3b75/src/PoolManager.sol
[position]: https://github.com/Uniswap/v4-core/blob/46c6834698c48bc4a463a86d8420f4eb1d7f3b75/src/libraries/Position.sol
[positions]: https://github.com/Uniswap/v4-periphery/blob/9969eec44cfdf07e24b41de47f40276a58401976/src/PositionManager.sol
[hooks]: https://github.com/Uniswap/v4-core/blob/46c6834698c48bc4a463a86d8420f4eb1d7f3b75/src/libraries/Hooks.sol
[ihooks]: https://github.com/Uniswap/v4-core/blob/46c6834698c48bc4a463a86d8420f4eb1d7f3b75/src/interfaces/IHooks.sol
[lpfee]: https://github.com/Uniswap/v4-core/blob/46c6834698c48bc4a463a86d8420f4eb1d7f3b75/src/libraries/LPFeeLibrary.sol
[protocolfee]: https://github.com/Uniswap/v4-core/blob/46c6834698c48bc4a463a86d8420f4eb1d7f3b75/src/libraries/ProtocolFeeLibrary.sol
[poolmath]: https://github.com/Uniswap/v4-core/blob/46c6834698c48bc4a463a86d8420f4eb1d7f3b75/src/libraries/Pool.sol
[hookdocs]: https://developers.uniswap.org/docs/protocols/v4/concepts/hooks
