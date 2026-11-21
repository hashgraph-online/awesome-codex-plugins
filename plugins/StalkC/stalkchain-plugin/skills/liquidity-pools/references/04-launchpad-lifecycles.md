# Launchpad lifecycles: identify the era before reasoning about liquidity

> Historical research notes, not live verification by this plugin. Raw RPC/replay artifacts are not shipped. Re-read relevant state before a live conclusion; see the [source index](00-source-index.md).

**Scope / as-of:** public sources and read-only chain observations retrieved 2026-10-02 UTC. Covers pons direct-v3 (including two factory eras), pons v2 curve-to-v4, historical Pump→Raydium, and the pinned Pump/PumpSwap documentation. This is not an audit or a trading recommendation. Source-level statements do not establish deployed-bytecode equivalence.

**Pinned source versions:** Pump public documentation/IDL `cb188ce08b5069196eef1f3e4a0c43b70099793b`; pons repository `44a3db9193c365f6c25cf0d4c2efc396e6de0df5`; historical pons reference `79681ec0c69c72fa7846132ecf324f5a4e1fbd68`. Original pons HTML was retrieved in full because the extractor cut v2 off in the middle of token metadata. The original includes the later fee, pool, audit and support sections. The pons docs did not expose a GitHub backlink in the captured link inventory: the ponsdotdev repository is a strongly corresponding public source, not independently authenticated deployment provenance.

## 1. Do not collapse these into one lifecycle

| Version | Create / early trading | Completion and destination | Liquidity-control model | Claims |
|---|---|---|---|---|
| pons direct-v3 | Fixed-supply token and WETH pool created together; pool trading immediately | Graduation measures paired principal; trading stays in the same pool | Concentrated-liquidity position held by an era-specific locker; fee claims separate | `launch-legacy-same-pool`, `launch-legacy-fee-era` |
| pons v2 | Token supply initially minted to its own quote-asset bonding curve | Curve closes at sellout; staged sweep and v4 pool creation; failed automatic progression can need a permissionless retry | Documented full-range v4 position held permanently by locker, not fungible LP burn | `launch-v2-curve-pool`, `launch-v2-lock-model` |
| Historical Pump | Synthetic/virtual-reserve bonding curve | Deprecated authorized `withdraw` moved completed-curve liquidity for off-chain-server Raydium migration | Historical destination/transaction must be checked; current PumpSwap evidence does not prove an old Raydium pool | `launch-pump-historical-raydium` |
| Pump→PumpSwap | Bonding curve, with account/instruction/quote-asset variations | Permissionless, idempotent `migrate` for completed curves; canonical AMM identity is derived, not guessed from token name | Docs say migration LP shares are burned; independent deposits can issue removable LP shares | `launch-pump-migrate`, `launch-pump-initial-burn`, `launch-pump-later-removable` |

The two pons generations describe distinct mechanisms, not one timeless configuration.[1][2] Pump's migration and AMM descriptions likewise require their own era and pool identity.[6][7]

## 2. pons direct-v3: graduation is not migration

The old documentation explicitly says there is no bonding curve and no migration later. The token's WETH pool is live from creation, and graduation leaves trading in that same pool. This invalidates the blanket statement “all launchpad graduation moves liquidity to a new DEX.”[1]

Within this generation, the docs list an active factory `0xA5aAb3F0c6EeadF30Ef1D3Eb997108E976351feB` and active locker `0x736D76699C26D0d966744cAe304C000d471f7F35`, but legacy factory `0x0c37a24F5D23A486FA692d1500881d698B1F77a4` and legacy locker `0x31ca5E101941A93A7DD6d0497928700625CF54B5` remain relevant to older tokens. Do not resolve an old launch through the newest factory merely because both are “v1.”[1]

The documented reference PONS token `0x39dBED3a2bd333467115dE45665cC57F813C4571` uses pool `0x10CC6BD38112cAc182db90B6a71d8Bb5939526bA`. Its saved launch receipt actually identifies the **legacy** factory, and position `109216` is held by the legacy locker at Robinhood block `78015119`. That is real custody evidence, not a full proof of permanent unwithdrawability; see the control reference and `launch-deployment-pons-legacy`.[1][25]

For a token-specific answer read the token's canonical pool, originating factory launch record, position manager, position ID, locker, actual liquidity, approvals, fee split and graduation status at a named block. Do not hardcode a threshold or creator share from a different era. `launch-legacy-same-pool` and `launch-legacy-owner-live` are the relevant atomic claims.

## 3. pons v2: readiness, swept reserves and pool existence differ

### Normal path

1. Creator chooses token metadata, quote asset and launch configuration; the token supply goes to the curve.
2. Curve trades against the selected quote asset. Pricing includes a phantom quote reserve, whereas `realQuoteReserve()` is physically collected tradable quote net of fees. Never treat the phantom balance as spendable exit liquidity.
3. When sellable supply is exhausted, the curve is ready. The final buy may be clamped/refunded; do not equate requested input with executed input.
4. Graduation moves reserves into the factory (`Swept`), then pool creation registers/initializes the v4 pool and mints its position into the locker (`PoolCreated`).
5. Post-graduation swaps use the pool; fee accounting belongs to the hook/escrow, not an LP withdrawal right.[2][20][23]

Read the launch record rather than assuming ETH, an invariant supply/threshold, or a fixed tick spacing. The documented PoolKey sorts launch token and quote currency, includes the actual fee and tick spacing, and the shared hook. A v4 pool ID is not a separate pool-contract address.[2]

### The sell-availability exception matters

The overview's “you can always sell” is qualified later on the same page: selling to the curve stops once it sells out and reopens in the pool after graduation. Pinned source makes the condition explicit: `if (graduated || readyToGraduate()) revert CurveGraduated();`. A ready launch can therefore have **no working curve sell route while its pool is not yet created**, including a `NotGraduated` record whose preflight prevented sweeping. Do not route a sell just because `graduated()` is false.[2][22]

A failed automatic attempt is a work queue, not evidence of an already existing pool. Read phase, `readyToGraduate()`, curve reserves, actual pool state, and the failure event. An owner-only forced sweep exists in the newer pinned source for a ready launch whose seed is not viable; it rejects a viable seed. That is a narrowly different path from ordinary permissionless graduation.[2][20]

### Recovery is phase-specific, and “refund” is underspecified

The historical reference `rescueLaunch` waits seven days in `Swept`, pays quote to the original deployer, and locks remaining launch supply. Its own comment says this is a reference stand-in and not buyer-fair. The newer pinned `rescueSweptGraduation(token, recipient)` is different: owner-only, nonzero selected recipient, seven-day delay, and transfers both recorded quote and token amounts to that recipient. It is not a proof of proportional buyer refunds.[24][20]

Importantly, the newer rescue function's actual checks are phase, recipient and elapsed time; it does **not** independently rerun a “graduation is impossible” proof. Permissionless seeding during the waiting period is a mitigation described in comments, not equivalent to a cryptographic guarantee that a healthy but unattended swept launch cannot be rescued. This is a scoped source observation, **not** an assertion that this code matches a live deployment or that a live exploit exists.[20]

The pool's permanent-lock claim concerns **successfully graduated position principal**. It does not cover pre-pool swept reserves, accumulated fee buckets or bought-back tokens vesting over five years.[20][21] Curve-fee rescue and hook-fee rescue redistribute fees; they must not be described as a way to withdraw the locked LP position without evidence of such a path.[22][27]

The page's separate “Migration” section concerns migration of an old coin into a replacement via epochs and settlement. Its depositor recovery rules are not automatically the rules for ordinary curve-to-pool graduation rescue.[2]

### Zero PoolKey/LP fee is not zero trading cost

The v4 PoolKey/LP fee is documented as zero, while the hook charges a swap fee and creator tax. Protocol-fee configuration is a separate live check; zero PoolKey/LP fee alone does not exclude it. Pre-graduation fees accrue on the curve; post-graduation fees accrue on the hook until swept. A zero escrow balance can mean unswept fees, not zero earnings. Swap-dependent sweeps require the operator; simple quoted-fee distribution can be available to the creator.[2][27]

Creator fee-recipient transfers and protocol takeovers affect future payouts, not necessarily position custody. Bought-back token supply vests; a name such as `buybackBurnBps` in older interfaces does not establish destruction of supply. Pinned locker source checks `ownerOf(tokenId)` and exposes no principal withdrawal/arbitrary-call function, but deployed-source equivalence is unknown.[2][21][24]

At retrieval the docs say audits remain in progress and public launches are restricted. Treat that as a dated documentation statement, not an assurance about live configuration. We observed newly emitted launch events, which are compatible with whitelisted creation and do not independently prove the public launch gate is open.[2][25]

## 4. Pump: canonical migration is not arbitrary PumpSwap liquidity

The pinned Pump document describes `complete == true` and exhausted real token reserves before `migrate`; the historical `withdraw` migration route to Raydium is disabled according to that document. The current `migrate` destination and account constraints also appear in the pinned Pump IDL. Older examples and old fee-config JSON are not timeless chain measurements.[6][13]

Canonical PumpSwap identity requires:

- Correct Solana cluster/genesis and program `pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA`.
- `pool.creator` equal to the Pump `pool-authority` PDA seeded by the base mint under `6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P`.
- Correct index, base mint and quote mint in the pool PDA; documented canonical migrated index is zero.
- Vault/LP mint identity and, for a migration-specific burn claim, the actual migration transaction and token burn instruction/effects.[7][12][13]

`pool.coin_creator` is a fee beneficiary field, not the canonical-PDA creator. Anyone can create other pools for the same mint, and an arbitrary PumpSwap pool does not inherit canonical migration guarantees.[7][12]

### Burned initial shares and removable later shares coexist

Docs say the PumpSwap LP tokens received from migration are burned. PumpSwap still exposes `deposit` and `withdraw`: independent LPs can add funds and receive shares they can later redeem. Burning initial shares is not burning the reserves, not burning the underlying token supply, and not disabling all future liquidity withdrawals.[6][7]

PumpSwap's `Pool.lp_supply` deliberately preserves accounting supply across direct LP burns; a token mint's current supply can therefore be much smaller. Do not infer a missing reserve or a migration bug merely from that difference. Conversely, a low mint supply alone is not a complete migration-burn proof.[7]

Our canonical sample `GseMAnNDvntR5uFePZ51yZBXzNSn7GdFPkfHwfr6d77J` was derived and checked from actual account bytes. At finalized slot `452528958`, accounting `lp_supply` was `4194352106721`, while the actual LP mint supply was **`919287139`**, not zero. This is direct evidence against describing all LP shares in that pool as burned. The acquisition did not retrieve the original migration/burn transaction, so the initial burn remains documented, not transaction-verified.[26]

### Do not freeze your understanding at the first README example

The same pinned repository contains old fixed-fee sample JSON and newer dynamic fee documents. Canonical pools and noncanonical pools use different fee logic; later changes include custom quote assets, optional account fields, creator fees, holder rewards and deprecated new cashback creation. Decode the applicable account layout and configuration rather than copying a historical percentage.[5][9][11]

A particularly important internal conflict: the PumpSwap page still says virtual quote reserves are “0 on all pools today,” while the README and dedicated September 30 announcement allow **negative signed `i128`** virtual quote reserves. Use `effective_quote_reserves = raw_quote_vault_amount + virtual_quote_reserves`, preserve its sign, and determine the actual value per pool. The announcement states a program nonnegative/overflow guarantee; a documentation guarantee is not independently audited bytecode.[5][7][10]

The sampled pool's virtual reserve was zero, which proves nothing about every other pool. Both Pump and PumpSwap were observed under the upgradeable BPF loader with a non-null ProgramData upgrade authority. A burned LP narrative must not erase upgrade, configuration, creator-fee or trading-disable controls.[26]

### Replayed reserve example (hypothetical, not a chain observation)

Given raw quote vault `100000000000` units and signed virtual reserve `-20000000000`, the documented signed-addition formula gives effective pricing reserve `80000000000` units. The saved offline replay asserts this exact result. This example deliberately uses invented **inputs labeled as hypothetical** to illustrate the formula, not invented fetched data. The sampled real pool above instead has virtual reserve zero.[10]

The upstream replay script is not shipped; independently check the stated signed addition. Historical output was `hypothetical_effective_quote: 80000000000`, not a release-time RPC result. Effective reserves are the pricing input, not a statement that an equally sized order can execute at the marginal spot price.

## 5. Operational answer template

For “can the creator remove liquidity?” return **protocol/version/chain → exact factory/program → pool/position → observation block/slot → principal controller → fee controller → pre-graduation exceptions → upgrade/admin risks → confidence and gaps**. If these are missing, answer unknown rather than treating a generic DEX liquidity tutorial as evidence that this specific launch LP is removable.

Use [liquidity-control verification](05-liquidity-control-verification.md) for the proof checklist. Never translate this research authorization into a swap, approval, withdrawal, signer access or rebalance.

## Sources

[1] https://docs.ponsfamily.com
[2] https://docs.ponsfamily.com/v2
[5] https://raw.githubusercontent.com/pump-fun/pump-public-docs/cb188ce08b5069196eef1f3e4a0c43b70099793b/README.md
[6] https://raw.githubusercontent.com/pump-fun/pump-public-docs/cb188ce08b5069196eef1f3e4a0c43b70099793b/docs/PUMP_PROGRAM_README.md
[7] https://raw.githubusercontent.com/pump-fun/pump-public-docs/cb188ce08b5069196eef1f3e4a0c43b70099793b/docs/PUMP_SWAP_README.md
[9] https://raw.githubusercontent.com/pump-fun/pump-public-docs/cb188ce08b5069196eef1f3e4a0c43b70099793b/docs/FEE_PROGRAM_README.md
[10] https://raw.githubusercontent.com/pump-fun/pump-public-docs/cb188ce08b5069196eef1f3e4a0c43b70099793b/docs/NEGATIVE_VIRTUAL_QUOTE_RESERVES.md
[11] https://raw.githubusercontent.com/pump-fun/pump-public-docs/cb188ce08b5069196eef1f3e4a0c43b70099793b/docs/PUMP_CREATOR_FEE_README.md
[12] https://raw.githubusercontent.com/pump-fun/pump-public-docs/cb188ce08b5069196eef1f3e4a0c43b70099793b/docs/PUMP_SWAP_CREATOR_FEE_README.md
[13] https://raw.githubusercontent.com/pump-fun/pump-public-docs/cb188ce08b5069196eef1f3e4a0c43b70099793b/idl/pump.json
[20] https://raw.githubusercontent.com/ponsdotdev/ponsfamily/44a3db9193c365f6c25cf0d4c2efc396e6de0df5/contractsV2/src/v2/PonsV2LaunchFactory.sol
[21] https://raw.githubusercontent.com/ponsdotdev/ponsfamily/44a3db9193c365f6c25cf0d4c2efc396e6de0df5/contractsV2/src/v2/PonsV2LaunchLocker.sol
[22] https://raw.githubusercontent.com/ponsdotdev/ponsfamily/44a3db9193c365f6c25cf0d4c2efc396e6de0df5/contractsV2/src/v2/PonsV2BondingCurve.sol
[23] https://raw.githubusercontent.com/ponsdotdev/ponsfamily/44a3db9193c365f6c25cf0d4c2efc396e6de0df5/contractsV2/src/v2/PonsV2GraduationExecutor.sol
[24] https://raw.githubusercontent.com/ponsdotdev/ponsfamily/79681ec0c69c72fa7846132ecf324f5a4e1fbd68/contracts/v2/contracts/LaunchFactory.sol
[25] https://rpc.mainnet.chain.robinhood.com
[26] https://api.mainnet-beta.solana.com
[27] https://raw.githubusercontent.com/ponsdotdev/ponsfamily/44a3db9193c365f6c25cf0d4c2efc396e6de0df5/contractsV2/src/v2/hooks/PonsV2MemeHook.sol
