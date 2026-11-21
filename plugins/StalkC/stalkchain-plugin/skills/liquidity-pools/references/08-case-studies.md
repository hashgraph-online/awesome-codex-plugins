# Applied case studies: identify the mechanism before judging the risk

> Historical research notes, not live verification by this plugin. Raw RPC/replay artifacts are not shipped. Re-read relevant state before a live conclusion; see the [source index](00-source-index.md).

**Research snapshot:** 2026-10-02 UTC. These cases combine documented mechanisms, explicitly hypothetical scenarios, and the narrowly verified chain observations described below. They are not trading recommendations. “Verified” never implies a complete security audit or proof that a repository matches deployed bytecode. Public evidence links and their limits are explained in the [source index](00-source-index.md).

## Case 1 — An ordinary v3 NFT is removable, not permanently locked

**Question:** “I own a normal v3 LP NFT. Is the capital trapped in the pool?”

**Scenario type:** documented reference-code mechanics; no particular live position is asserted here.

**Identity to obtain:** chain, factory, pool, fee/tick spacing, position-manager address, tokenId, token order/decimals and observation block. Check actual NFT ownership and per-token/owner-wide approvals. If a vault or locker owns it, analyze that integration instead of assuming the standard wallet-owned path.

**Documented lifecycle:** mint/increase adds principal; authorized `decreaseLiquidity` calls core burn and credits owed amounts; collect transfers owed principal and fees; NFT `burn(tokenId)` destroys the cleared receipt only after its liquidity and owed balances are zero. An event named Burn at core level means liquidity was removed, not rendered permanently inaccessible.

**Principal controller:** the owner or authorized operator through the applicable manager, subject to its integration rules. **Fee controller:** authorization/recipient rules determine collection; the same transfer can contain withdrawn principal and earned fees, so the transfer amount is not automatically profit.

**Correct conclusion:** baseline reference mechanics include removal. A blanket claim that standard v3 NFTs are locked is incorrect. A claim that this particular deployed NFT is removable still requires identity and authorization checks.

**Residual risks:** out-of-range one-sided inventory, token transfer restrictions, price impact, gas and unfavorable execution. Fees already earned may remain claimable when the position stops earning new fees.

**Evidence:** claims `uni-v3-burn-credit`, `uni-v3-core-collect`, `uni-v3-nft-decrease`, `uni-v3-nft-burn-empty`; [v3 reference §§4–5](02-uniswap-v3.md). Primary source: [pinned NonfungiblePositionManager](https://github.com/Uniswap/v3-periphery/blob/0682387198a24c7cd63566a2c58398533860a5d1/contracts/NonfungiblePositionManager.sol).

## Case 2 — A v4 zero-fee pool with a hook is not necessarily free or ordinary

**Question:** “The pool fee is zero and the position NFT was burned. Does that prove locked liquidity and free swaps?”

**Scenario type:** documented v4 capabilities, not a claim about an unspecified live hook.

**Identity to obtain:** chain + PoolManager + full PoolKey `(currency0,currency1,fee,tickSpacing,hooks)` + PoolId, actual position owner/range/salt and the periphery receipt. There is not necessarily a separate v3-like contract for each pool.

**Mechanics:** distinguish PoolKey fee, effective dynamic LP fee, protocol fee and hook-imposed custom charge. Account/currency deltas must settle at unlock completion, but balanced accounting does not prove fair pricing. A fixed hook address does not prove fixed internal settings or immutable dependencies. Inspect callback bits and the actual hook's owner/upgrade/withdrawal paths.

**Burn distinction:** the pinned v4 periphery can destroy a receipt and remove funded liquidity in the same action. Its burn behavior must not be inferred from v3's empty-NFT precondition. Neither version's NFT burn proves that funded principal remains locked.

**Correct conclusion:** zero core/LP fee is insufficient to characterize total swap cost. A receipt burn is insufficient to characterize principal custody. Unknown hook/deployment behavior stays unknown.

**Evidence:** `uni-v4-hook-fees-distinct`, `uni-v4-fees-principal-delta`, `uni-v4-burn-removes`, `uni-v4-hook-key-fixed`; [v4 reference §§1, 5–7](03-uniswap-v4.md). Primary source: [pinned PositionManager](https://github.com/Uniswap/v4-periphery/blob/9969eec44cfdf07e24b41de47f40276a58401976/src/PositionManager.sol).

## Case 3 — Pump migration-share burning and later LP supply can coexist

**Question:** “Pump migration burns LP shares. Why does its pool still have LP tokens?”

**Scenario type:** official documented migration mechanics plus one canonical-pool observation; original migration/burn transaction not captured.

**Observed identity:** Solana mainnet-beta, canonical PumpSwap pool `GseMAnNDvntR5uFePZ51yZBXzNSn7GdFPkfHwfr6d77J`. The creator PDA and index-zero pool PDA rederived from actual account fields. The pool, LP mint and two vaults were read together at finalized slot **452528958**, with block hash retained in the [control reference](05-liquidity-control-verification.md).

**Observed facts:** the pool-account LP accounting value and actual mint supply differ; actual mint supply is **919287139 raw LP units**, not zero. The offline replay recomputed it from the retained account bytes. This is not a statement about every Pump pool or an independently proven initial burn percentage.

**Interpretation:** official documentation describes burned migration shares and also supports later deposit/withdrawal mechanics. A later liquidity provider can hold a separately issued redeemable share tranche. The initial tranche and all later tranches must not be conflated.

**Additional control fact:** separately captured Pump and PumpSwap ProgramData headers contain a non-null upgrade authority. Those headers and the pool snapshot were obtained at different slots and are not an atomic view. LP-share burning does not erase program-upgrade or token-control risk.

**Correct conclusion:** documented initial-share burning is compatible with later LP shares. This run verifies canonical identity and nonzero supply, **not** the original burn transaction, exact burned percentage, all holder balances or all reachable program behavior. Do not mark the initial tranche `verified_burned_lp` from supply alone.

**Evidence:** `launch-pump-canonical-live`, `launch-pump-nonzero-lp-live`, `launch-pump-upgrade-authority-live`; [control reference §5](05-liquidity-control-verification.md); [pinned PumpSwap documentation](https://raw.githubusercontent.com/pump-fun/pump-public-docs/cb188ce08b5069196eef1f3e4a0c43b70099793b/docs/PUMP_SWAP_README.md).

## Case 4 — pons legacy graduation does not imply migration

**Question:** “The pons token graduated. Which new pool did its liquidity move into?”

**Scenario type:** documented direct-v3 lifecycle plus real legacy-position custody observation.

**Version matters first:** root/direct-v3 documentation describes immediate pool trading and graduation in the same pool. The curve-to-v4 lifecycle belongs to another version. An answer that searches for a migration solely because the UI says graduated starts from the wrong model.

**Observed legacy sample:** position **109216**, pool `0x10CC6BD38112cAc182db90B6a71d8Bb5939526bA`, factory `0x0c37a24f5d23a486fa692d1500881d698b1f77a4`. At Robinhood block **78015119**, the NFT owner was the legacy locker `0x31ca5e101941a93a7dd6d0497928700625cf54b5`; liquidity was nonzero and per-token approval returned zero.

**Correct conclusion:** custody was verified at that block. Permanent-lock status was not fully verified because old locker implementation equivalence, owner-wide operators and complete reachable paths were not established. Current source for a newer factory is not automatically evidence for this legacy factory.

**Principal and fees:** locker custody is a principal-control clue, not proof of all restrictions. A creator's right to fee income is a separate question from its right to principal. Era-specific fee splits/configurations require their own reads.

**Evidence:** `launch-legacy-owner-live`, deployment `launch-deployment-pons-legacy`; [control reference §3](05-liquidity-control-verification.md); [direct-v3 documentation](https://docs.ponsfamily.com/).

## Case 5 — pons v2 readiness can precede usable pool trading

**Question:** “The v2 curve says ready. Can holders always sell until graduation completes?”

**Scenario type:** documentation/source analysis with a non-graduated live sample; no graduated v2 position verified in this acquisition.

**Lifecycle:** create → curve trading → ready/sell closure → swept/pending seed → v4 pool. Version/configuration and exception paths matter. Source checks `graduated || readyToGraduate()` on sells. Merely seeing `graduated=false` is therefore insufficient to promise a working curve sell. Pool creation and successful routing also need confirmation.

**Live scope:** the sampled token `0x66a2cf662eab5bb461e99f2667e2ba7859ef05d8` was not marked locked by its locker at Robinhood block **78015119**. Source-layout decoding showed phase `NotGraduated`. This is not an example proving a graduated permanent lock.

**Rescue caveat:** an older reference returns quote to the original deployer and explicitly warns that this is not a buyer-fair refund implementation. A newer pinned factory instead permits an owner-selected recipient to receive quote and tokens after the swept-state delay. The newer rescue body does not independently recheck seed impossibility; an owner-only force-sweep entry has its own viability guard. These are distinct paths.

**Correct conclusion:** do not repeat “always sell” or “all buyers automatically receive fair refunds” without checking the narrower code/phase conditions. Neither inspected source was matched to deployed bytecode, so the case is **not a demonstrated live exploit**. The unresolved equivalence blocks an unconditional safety assurance, not all useful explanation.

**Evidence:** `launch-v2-sell-gap`, `launch-v2-ready-guard`, `launch-historical-rescue-recipient`, `launch-current-rescue-authority`, `launch-current-rescue-delay`, `launch-current-rescue-tokens`, `launch-v2-phase-live`; [lifecycle reference](04-launchpad-lifecycles.md), [control reference §4](05-liquidity-control-verification.md); [newer pinned factory](https://raw.githubusercontent.com/ponsdotdev/ponsfamily/44a3db9193c365f6c25cf0d4c2efc396e6de0df5/contractsV2/src/v2/PonsV2LaunchFactory.sol).

## Case 6 — A locked launch position says nothing about an independent LP

**Question:** “The launch position is permanently locked. Can liquidity nevertheless decrease?”

**Scenario type:** hypothetical comparison built from the documented independent-position model; not a measured historical withdrawal.

Assume the initial launch position A is validly locked. Another provider later creates independent position B in the same pool. Principal controller, range, salt/tokenId or fungible share ownership for B is separate from A. If B's integration permits authorized removal, its provider can withdraw it without unlocking A. In concentrated liquidity, B may also dominate depth near the current price even when A holds substantial total assets.

**Correct conclusion:** analyze lock coverage by tranche/position and active range. Neither pool-level TVL nor a launchpad lock badge tells you which liquidity can disappear near today's price. Conversely, observing a decrease in aggregate liquidity does not by itself prove the original lock failed: distinguish independent removals, swaps/inventory changes, price movement and actual control of A.

**Evidence:** v3 position/NFT source and v4 owner/ticks/salt model, `uni-v4-position-key`, `uni-v4-position-salt`; [v3 reference](02-uniswap-v3.md), [v4 reference §§2, 7](03-uniswap-v4.md), and canonical Pump example above. No specific future depth is promised.

## Case 7 — High fees do not ensure positive net LP PnL

**Question:** “The position generated impressive fee APR. Was it profitable?”

**Scenario type:** explicitly hypothetical accounting example, with explicitly stated inputs.

Inputs in one numeraire: initial capital 1000; ending principal 900; separately counted fees 60; incentives 20; gas 15; execution costs 10. No external deposits/withdrawals. Costs must not already be included in terminal principal or deducted twice.

```text
net PnL = 900 + 60 + 20 - 1000 - 15 - 10 = -45
```

The upstream Decimal script (not shipped) reported `net_pnl: -45.000000000000`. This is a historical arithmetic example, not a release-time execution result or a strategy's realized record. With external cash flows, benchmark and timing must be explicit; use actual transfer/history data to reconstruct a real position.

**Correct conclusion:** report economic PnL and separately compare to a specified holding/rebalancing benchmark. Do not add IL and LVR as if both were independent realized costs: their benchmark definitions differ. An APR extrapolation from a short interval is not a durable return forecast. Out-of-range periods, tokenized-stock market closures and adverse selection can change the economics.

**Evidence:** [economics reference](06-lp-economics.md), the cited LVR paper and v3 position-value mechanics; all mathematical inputs here are hypothetical and stated.

## Case 8 — A saved strategy is a lead, not measured alpha

**Question:** “A public post reports huge LP returns. Should we copy its ranges?”

**Scenario type:** workflow for evaluating self-reported strategy material, not a recommendation.

Preserve the public wrapper and quoted target separately; quoting an author is not independent corroboration or endorsement. Resolve full article/media/context if available. Record what is actually specified: pair, chain, version, capital, date, fee period, range, rebalances, claimed net/gross PnL, deposits/withdrawals and inventory valuations. Missing fields remain missing.

Evaluate: was the range centered on a stale/closed underlying market? Did reported fees include incentives or creator/hook fees that a normal LP would not earn? Does the result include all costs and losing positions? Are claims backed by wallet/position history rather than a screenshot? Can the reported APR be reproduced from the stated inputs?

**Correct conclusion:** retain the idea as `community_only` until its accounting and mechanism assumptions are independently supported. This is not exhaustive community coverage. Do not claim a community consensus from a handful of public posts.

**Evidence:** [community playbooks](07-community-playbooks.md), with attributable public source links and explicit missing-body/media limits; [freshness and coverage policy](09-freshness-and-conflicts.md).
