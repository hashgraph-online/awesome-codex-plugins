# Liquidity-control verification: ownership is not an economic safety guarantee

> Historical research notes, not live verification by this plugin. Raw RPC/replay artifacts are not shipped. Re-read relevant state before a live conclusion; see the [source index](00-source-index.md).

**Scope / as-of:** 2026-10-02 UTC, public documentation, pinned source inspection and actual read-only JSON-RPC responses. The acquisition is targeted, not an audit, a census of pools, or proof of all historical burns. No keys, signers, transactions or paid endpoints were used. Public source commits are the same as [the lifecycle reference](04-launchpad-lifecycles.md); none was matched to deployed binaries.

## 1. Use a control classification, not a marketing adjective

These are verification labels for a **specific position or identified share tranche**, not labels for every reserve in a market:

| Label | Minimum evidence | Does not establish |
|---|---|---|
| `verified_locked` | Exact chain/factory/pool/position; positive funded liquidity; custody and approvals; deployed locker implementation and all reachable decrease/transfer/arbitrary-call/upgrade/rescue paths checked; applicable duration and exceptions | Price floor, sell availability, safety of token/hook/quote asset, permanence of unrelated positions |
| `verified_burned_lp` | Actual fungible LP mint; migration/deposit shares traced; successful token burn with amount and supply effect; distinguish direct burn from redeem-and-burn | All future LP shares burned, no program upgrade risk, no dumping or adverse price move |
| `removable` | Exact holder/controller has reachable redemption/decrease route and sufficient authority under observed state | The creator owns that route, it will always be enabled, every position is removable |
| `unknown` | Identity, code match, authority paths, funding or history incomplete | A claim of either safety or exploitability |

A repository containing a no-withdrawal locker does not meet `verified_locked` by itself. A fungible LP token burn is different from destroying an empty position token, locking a funded position NFT, sending assets to a zero-looking address, or transferring tokens into a vesting vault. The pons locker and PumpSwap LP-share mechanisms are materially different.[21][6][7]

**This lane does not mark any complete launch-liquidity position `verified_locked` or any migration tranche `verified_burned_lp`.** It verifies narrower observations: addresses have code, program loader/authority state, canonical PDA identity, custody, and LP supply. Keep those useful verified facts instead of inflating them into a global safety conclusion.

## 2. The evidence ladder

1. **Name → identity.** Resolve chain ID/genesis, network, token mint/address, originating factory/program and version. A ticker cannot identify a deployment.
2. **Identity → actual position.** Follow launch/migrate events and registry/PDA constraints into the exact pool, manager, position or LP mint. Check real funded liquidity and reserves, not just an emitted label.
3. **Position → authority.** Check current owner, per-position approval, owner-wide operators/delegates, locker configuration, proxy implementation, program loader and upgrade authority. A zero per-token approval does not rule out an owner-wide operator.
4. **Authority → reachable actions.** Trace decrease, withdraw, transfer, generic execution, emergency rescue, fee collection and upgrades separately. Check whether fees and principal share custody or accounting.
5. **Time → scoped conclusion.** Pin EVM calls to a block, and record its hash. For Solana save response context slots and fetch the corresponding block; `minContextSlot` would be a lower bound, not a historical exact-slot query. Use `getMultipleAccounts` to observe related accounts at one context slot.
6. **Source → deployment.** Reproducible binary/bytecode matching and actual dependency/proxy wiring are a separate gate. Matching function selectors or getters is not a binary match.

This procedure is a research standard. Never call state-changing functions merely to see whether removal works.

## 3. Real Robinhood Chain observations

**Network:** official documentation RPC `https://rpc.mainnet.chain.robinhood.com`, returned chain ID `0x1237` = **4663**. Calls were pinned to block **78015119** (`0x4a66a8f`), hash **`0xccc5a9c336c244b846bf15805926a8f85a828b83e2496b18a10b076c01d0b65d`**.[1][25]

### Legacy direct-v3 reference token

| Field | Observed identity |
|---|---|
| Launch transaction | `0x1f54f25fec2d963dcb338ecb8b46a6eb123198a5c7a746d34cb2dbe78d074af8` |
| Receipt success / original block | `status=0x1`; block `8963150` (`0x88c44e`) |
| Original block hash | `0xd18718d02fe1da449333e477bc588a41e59b1fd169a2b945a14fb17339d684a3` |
| Factory from receipt and launch log | `0x0c37a24f5d23a486fa692d1500881d698b1f77a4` — legacy factory |
| Token | `0x39dBED3a2bd333467115dE45665cC57F813C4571` |
| Pool from launch event | `0x10CC6BD38112cAc182db90B6a71d8Bb5939526bA` |
| Position manager | `0x73991a25C818Bf1f1128dEAaB1492D45638DE0D3` |
| Position ID from launch event | `109216` |
| `ownerOf(109216)` at observation block | `0x31ca5e101941a93a7dd6d0497928700625cf54b5` — legacy locker |
| `getApproved(109216)` | zero address |
| `positions(109216)` | Returned WETH/launch-token identity, fee field, range and nonzero liquidity; raw return preserved |

This supports **custody verified, permanent-lock status unknown**. The current repository's direct-v3 factory is not automatically the bytecode of the old launch factory or its locker. Owner-wide approvals, the old locker code and its full reachable surface were not exhaustively verified.[25]

Provenance: `launch-deployment-pons-legacy`; `launch-rpc-v1-launch-receipt`, `launch-rpc-v1-position-owner`, `launch-rpc-v1-position-position`, `launch-rpc-v1-position-approved`, `launch-rpc-v1legacy-locker`; atomic claim `launch-legacy-owner-live`.

### pons v2 named deployment

The documented factory `0x7eD598BcEf8bd9Edd8C97A195C6d13f40801EC7e`, hook `0xE5e702641Ea86F4ae6cC3cDaeD2B886f976Be044` and locker `0x267444D099b10fB5Ed7c3Cc7B7c767AdcA574952` all returned nonempty runtime code. Factory `locker()` and locker `factory()` returned each other. Their `owner()` getters, including the hook, returned **`0x263ed295dafae1d9aadd6e56c4b6f9f38ee019dd`**. The presence of an administrative owner is not proof that it can withdraw locked principal.[2][25]

A live launch event identified token `0x66a2cf662eab5bb461e99f2667e2ba7859ef05d8` and curve `0xbdcdff4dacc5bab12689b6fa958466cb86226f9d`. Its factory return matches the inspected record shape and shows phase zero (`NotGraduated`); locker `isLocked(token)` returned false and `lockedPositions(token)` returned zero. This token is **not an observed graduated locked-position example**. The locker identifies PositionManager `0x58daec3116aae6d93017baaea7749052e8a04fa7`.[25][31]

A bounded five-chunk scan for the newer source's `PoolGraduated(address,uint256,uint256,uint256)` topic across blocks **78005120–78015119** returned no matching events. This does not mean v2 has no graduated tokens: it is not a full deployment backfill and an unmatched deployment could use a different event ABI. The explorer source-verification endpoint returned HTTP 403; no bypass was attempted. Runtime bytes are saved, but build settings/dependency equivalence and verified deployed source are unresolved.

Provenance: `launch-deployment-pons-v2`; `launch-rpc-code-v2factory`, `launch-rpc-code-v2locker`, `launch-rpc-code-v2hook`, `launch-rpc-v2-sample-*`, `launch-rpc-v2-graduated-logs-*`, `launch-pons-v2-explorer-source`. **Deployed code match: unknown.**

## 4. pons rescue/control map: separate eras and asset buckets

| Surface | Pinned source behavior | What remains unproved |
|---|---|---|
| Old reference `rescueLaunch` | Owner-only; swept-phase seven-day delay; quote to original deployer; remaining launch tokens to locker; explicit not-buyer-fair warning | Whether any deployed factory uses it; whether conditions/funds are reachable for a concrete launch |
| Newer `rescueSweptGraduation` | Owner-only; `Swept`; nonzero owner-selected recipient; elapsed seven days; recorded quote **and tokens** sent to recipient | Deployed bytecode match, actual launch state, which recipient would be selected, any operational refund policy |
| Newer `forceSweptGraduation` | Owner-only; ready `NotGraduated` launch; rejects a seed still judged viable | Deployment match and real preflight outcome |
| Curve `rescueFees` | Factory-gated; pays pending base-fee split and creator tax directly, clearing buckets and buyback earmark | Full deployed asset/accounting behavior |
| Hook `rescuePoolFees` | Owner-only; rescues accrued token-denominated fee buckets with normal recipients, bypasses escrow and buyback swap | Not a demonstrated locked-position principal withdrawal |
| `PonsV2LaunchLocker` | Immutable manager; one-time factory wiring; verifies custody; no withdrawal/arbitrary-call function in inspected source | All deployed code/dependencies/approvals and funded position state |
| Factory helper/forwarder wiring | Executor/deployer setters are one-time; forwarder can be owner-rotated | Actual deployed wiring and privilege implications |

Factory/locker distinctions above are supported by `launch-historical-rescue-recipient`, `launch-current-rescue-authority`, `launch-current-rescue-delay`, `launch-current-rescue-tokens`, `launch-current-force-sweep`, `launch-v2-locker-surface`, `launch-v2-admin-forwarder`.[20][21][24] Fee-bucket recovery is separately supported by `launch-fee-rescue-not-principal` and the curve/hook implementations.[22][27]

**Important limit on the docs' wording:** a seven-day wait and permissionless pool creation provide time to seed; they do not themselves prove impossibility before a rescue. The newer rescue body does not recheck seed viability. Do not repeat “cannot interfere with any viable graduation” as a source-proven invariant. This is a design/trust boundary in inspected source, not a claim of a deployed exploit.[20]

A fee-recipient takeover, a buyback vest release and a liquidity withdrawal are different controls. Creator/protocol fees can remain claimable while the initial position principal is locked. Bought-back supply can vest while original launch liquidity stays locked. Always name the asset bucket.[2][21][27]

## 5. Real Solana observations and canonical sample

**Cluster identity:** `getGenesisHash` returned **`5eykt4UsFv8P8NJdTREpY1vzqKqZKvdpKuc147dw2N9d`** from `https://api.mainnet-beta.solana.com`. This is recorded as mainnet-beta, not inferred from the program address, because the official docs list the same program addresses on devnet too.[6][7][26]

### Program authority is not burned away with LP tokens

Program accounts at finalized context slot **452528125** were executable and owned by `BPFLoaderUpgradeab1e11111111111111111111111`. Their ProgramData headers were read at finalized slot **452528284**, block hash **`5ghZaMhX1uUQsUKn4W7xaDjsAguoXxFg4t7EJ5DMBS5r`**.[26]

| Program | ProgramData | Header last-deployment slot |
|---|---|---|
| Pump `6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P` | `B5MvUwXdiW1NMM6QFFD3ssPKBujD4zMohncbM73Z2BQu` | `449734335` |
| PumpSwap `pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA` | `6naEzKeUuFh1Jeeu51NXQgr5qkXgXtc9WKNct4xynVJc` | `446462733` |

Both decoded ProgramData headers contain a present upgrade authority: **`7gZufwwAo17y5kg8FMyJy2phgpvv9RSdzWtdXiWHjFr8`**. Headers—not full executable binaries—were acquired. No assertion is made about who controls that authority, signer composition, or a deployed binary matching the public IDL.[26]

The program and ProgramData responses are **different context slots**; record that time separation rather than describing them as one atomic historical snapshot. These are `launch-deployment-pump-program` and `launch-deployment-pumpswap-program`.

### Canonical pool and live LP supply

A single `getMultipleAccounts` read observed the pool, LP mint and both vaults at finalized slot **452528958**, block hash **`7PknBDYtE3RmzFhc78DW5sVXm6Ye7HgLs1eu4HzcMBtG`**.[26]

| Field | Value |
|---|---|
| Pool | `GseMAnNDvntR5uFePZ51yZBXzNSn7GdFPkfHwfr6d77J` |
| Base mint | `7LSsEoJGhLeZzGvDofTdNg7M3JttxQqGWNLo6vWMpump` |
| Quote mint | `So11111111111111111111111111111111111111112` |
| Pool creator | `9XDYTfQKwW8sHPqnFdUreMmtmffmkHVPGTNV2e3LKxNW` |
| Canonical derivation | Pump `pool-authority` PDA bump `255`; PumpSwap pool PDA index `0`, bump `254`; both match bytes read |
| LP mint | `6dpnPD6UWDw5hbJEuPQwnCCMba1JYwHANKuL6GQ6otAH` |
| Pool accounting `lp_supply` | `4194352106721` raw LP units |
| Actual LP mint supply | `919287139` raw LP units |
| Base vault amount | `649944714380432` raw base units |
| Quote vault amount | `127438545526` raw quote units |
| Signed virtual quote reserves | `0` for this sample only |

The canonical identity derives from the observed `creator`, index and mints, not the source example alone. PDA re-derivation is reproduced offline against the pinned documented seeds. The LP mint is Token-2022-owned, with mint authority equal to the pool and no freeze authority in the parsed read. Actual nonzero mint supply and a documented withdraw path mean “the original launch LP is burned, so no liquidity can ever be removed” is an invalid generalization.[7][12][26]

**Not verified:** original migration transaction, exact initial burn quantity, full LP-holder inventory, all later deposits/burns/withdrawals, current fee configuration, base-token authorities/extensions, and full program binary behavior. The sample is `canonical_identity_verified`; its initial-burn tranche remains `unknown` at transaction-proof level. Do not compute a supposedly exact locked percentage from accounting-vs-mint supply without tracing the protocol's minimum liquidity and full issuance/redemption history.

Provenance: `launch-deployment-pumpswap-pool`, `launch-rpc-solana-sample-consistent`, `launch-rpc-solana-sample-block`, `launch-rpc-solana-lp-mint`, pinned Pump/PumpSwap IDLs, and the lane's offline replay/observation files.

## 6. Source contradictions that must stay visible

- **pons always-sell language versus closed ready state:** narrower curve section and `sell` guard control; readiness can precede usable pool trading.[2][22]
- **pons old/new rescue recipient:** deployer-only reference return versus owner-selected quote-and-token recovery. Neither establishes buyer-proportional refunds; neither is matched deployment source.[24][20]
- **pons docs versus actual source event schema:** current docs describe `PoolGraduated` semantically; newer source event carries position ID and amounts, while historical reference event carries a pool ID/address. Read the exact ABI of the deployment rather than reusing an event signature across versions.[2][20][24]
- **Pump fixed examples versus evolving fee program:** don't treat old `creator_fee=0` or a fixed LP/protocol split as current fee configuration.[6][9][11]
- **Pump all-zero virtual reserves versus negative-reserve announcement:** preserve signed decoding and read the live pool; the sample's zero is not a universal claim.[5][7][10]

## 7. What locking/burning does not protect against

Even if removal is impossible for the initial position, token holders can sell, inventory can move toward the falling asset, quote assets can freeze/depeg or change transfer behavior, fees can create adverse execution, and program/hook changes or code defects can matter. Locked principal is not a floor under the token price or a guarantee of a working exit. pons itself discloses volatility and quote-asset risks; Pump's admin instructions and actual upgrade authority remain relevant controls.[2][7][26]

Before use, re-read live authorities/configuration and position state. New liquidity added by independent LPs is a separate ownership question. Research approval is not permission to interact with a signer, approve tokens, simulate a funded exploit, remove liquidity, or rebalance.

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
[20] https://raw.githubusercontent.com/ponsdotdev/ponsfamily/44a3db9193c365f6c25cf0d4c2efc396e6de0df5/contractsV2/src/v2/PonsV2LaunchFactory.sol
[21] https://raw.githubusercontent.com/ponsdotdev/ponsfamily/44a3db9193c365f6c25cf0d4c2efc396e6de0df5/contractsV2/src/v2/PonsV2LaunchLocker.sol
[22] https://raw.githubusercontent.com/ponsdotdev/ponsfamily/44a3db9193c365f6c25cf0d4c2efc396e6de0df5/contractsV2/src/v2/PonsV2BondingCurve.sol
[24] https://raw.githubusercontent.com/ponsdotdev/ponsfamily/79681ec0c69c72fa7846132ecf324f5a4e1fbd68/contracts/v2/contracts/LaunchFactory.sol
[25] https://rpc.mainnet.chain.robinhood.com
[26] https://api.mainnet-beta.solana.com
[27] https://raw.githubusercontent.com/ponsdotdev/ponsfamily/44a3db9193c365f6c25cf0d4c2efc396e6de0df5/contractsV2/src/v2/hooks/PonsV2MemeHook.sol
[31] https://raw.githubusercontent.com/ponsdotdev/ponsfamily/44a3db9193c365f6c25cf0d4c2efc396e6de0df5/contractsV2/src/v2/interfaces/ILaunchpadV2.sol
