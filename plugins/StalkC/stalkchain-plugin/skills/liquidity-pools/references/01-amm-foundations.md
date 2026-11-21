# AMM foundations: identify the curve before valuing the pool

**Scope / as of:** 2026-10-02. Educational mathematics based on Uniswap v2 (March 2020), v3 (March 2021), the original StableSwap paper (November 2019), and pinned v3-periphery test vectors. Not a description of every AMM or a verified deployment. All prices below are **token1 per token0**, unless explicitly inverted. No keys, RPC, approvals, signing, trades or position changes are implemented or authorized.

## 1. Inventory, invariant, and what an LP actually owns

An AMM holds inventory and applies a trading rule. In the fee-free, two-asset constant-product model, let `x` and `y` be token0 and token1 reserves in whole-token units: `x*y=k`. Selling token0 to the pool increases x and removes y. Uniswap v2 retains the constant-product design. Its fee-adjusted swap check requires the reserve product not to decrease during a swap; deposits and withdrawals change reserves and k separately.[1] **Claims:** `econ-cp-invariant`; document `econ-v2`, §1.

For a proportional full-range position, inventory is a share of pool reserves, not a promise to return the original token quantities. The LVR paper explicitly distinguishes contributed and withdrawn quantities because swaps change inventory.[4] **Claim:** `econ-inventory-change`. A concentrated position is instead specified by a range and liquidity amount; “I own 1% of TVL” is not enough to reconstruct its balances. v3 permits multiple positions with different ranges and its core positions are not represented as a single fungible pool ERC-20.[2] These statements describe economics and protocol design, **not custody or withdrawal authority**: use the liquidity-control reference for the specific position, owner, lock and withdrawal paths.

**Practical identification record:** chain/network; token contract identities and decimals; protocol/version; pool/factory identity; fee configuration; range/ticks; position liquidity; principal balances; accrued fee balances; observed block/time; whether a wrapper owns the underlying position. Without those facts, return a mathematical illustration, not a portfolio valuation.

## 2. Spot price is not average execution price

For `xy=k`, the fee-free marginal token1/token0 price is `P=y/x`, the magnitude of the curve's slope. The v2 paper gives the reserve-ratio marginal price and warns that current pool prices can be manipulated as settlement oracles.[1] **Claims:** `econ-spot`, `econ-oracle-manipulation`.

Derivation for a hypothetical single swap (not a router quote):

```text
fee-free output1 = y - k/(x + input0) = y*input0/(x + input0)
effective input0 = input0*(1-f)
output1 with input fee = y*effective input0/(x + effective input0)
average received price = output1/input0
```

Assumptions: positive reserves; fee `f` retained in this simple CPMM; no transfer tax, rebasing, hooks, protocol-specific rounding, multiple hops, changing state, gas, or external price movement. With fees, post-swap physical reserve x includes the **whole input**, not just effective input; do not use the adjusted input as the stored balance. Equations are algebra derived from the v2 invariant, not execution-code conformance.[1]

Use three distinct terms in research reports:

- **Curve price impact:** deterioration from the chosen initial marginal price caused by this order traversing the curve. State whether fees are included.
- **Quote-to-execution slippage:** difference between an earlier quote and actual execution, potentially caused by state changes or ordering. A slippage tolerance is a transaction constraint, not predicted impact or guaranteed fill.
- **All-in execution cost:** includes fees, routing, gas and other costs relative to a stated independent benchmark. Do not add an impact estimate again if already present in actual output.

These are reporting conventions for this corpus. They prevent a displayed “slippage” percentage from being used without knowing its definition.

### Decimal conversion and token-order inversion

Reserve integers are not whole tokens. For a reserve-ratio CPMM:

```text
human price token1/token0 = (raw1/raw0) * 10**(decimals0-decimals1)
reverse price = 1 / human price
```

The fixture uses raw0=`1000000000000000000`, decimals0=`18`, raw1=`4000000`, decimals1=`6`. Its whole-token reserves are x=1, y=4, so the tested outputs are `4.000000000000` token1/token0 and `0.250000000000` token0/token1. Inverting changes both token labels and, for a range, the order of bounds: `[a,b]` becomes `[1/b,1/a]`. This is dimensional analysis, not a deployment-specific token assumption.

**Do not estimate concentrated-pool spot price from physical token balances.** v3's relevant curve uses virtual reserves inside each range; token balances can also include inactive positions and owed fees.[2] Read its encoded price and token order using the version-specific reference.

## 3. Concentrated liquidity: virtual reserves versus real principal

Let a position have liquidity `L`, lower price `Pa`, upper price `Pb`, and current `P`. Define `a=sqrt(Pa)`, `b=sqrt(Pb)`, `s=sqrt(P)`. In consistent human units, real principal is:

| Price region | token0 quantity x | token1 quantity y |
|---|---|---|
| `P <= Pa` | `L*(1/a - 1/b)` | `0` |
| `Pa < P < Pb` | `L*(1/s - 1/b)` | `L*(s-a)` |
| `P >= Pb` | `0` | `L*(b-a)` |

These are the v3 whitepaper §2 and §6.3 inventory equations expressed using square-root prices. The translated invariant is `(x + L/b)*(y + L*a)=L**2`. Inside the range, virtual reserves `X=L/s`, `Y=L*s` satisfy `X*Y=L**2`, but **X and Y are not withdrawable balances**.[2] **Claims:** `econ-cl-virtual`, `econ-cl-single`; document `econ-v3`, equations 2.2 and 6.29–6.30.

Fixture: `L=12`, `Pa=1`, `Pb=9`.

| P | x token0 | y token1 | Meaning |
|---|---:|---:|---|
| `0.25` | `8` | `0` | Below range, all token0 |
| `1` | `8` | `0` | Lower-bound inventory |
| `4` | `2` | `12` | Inside range |
| `9` | `0` | `24` | Upper-bound inventory |
| `16` | `0` | `24` | Above range, all token1 |

At P=4 the virtual balances are X=6 and Y=24, while real balances are only x=2 and y=12. Upward travel ends with no token0 left at Pb; extrapolating the virtual constant-product reserves beyond Pb invents spendable token0. These are computed fixtures, tested with Decimal; not current token amounts.

Liquidity `L` in this presentation has units `sqrt(token0*token1)`; it is not dollars, share count or TVL. Human-unit L is not the contract raw L when decimals differ. The fixture deliberately avoids ticks and Q64.96 conversion. Boundary **inventory** is continuous, but implementation tick state and direction determine whether liquidity is active exactly at a tick; the equality convention above is not a fee-eligibility oracle.[2]

An out-of-range v3 position earns no further swap fees while inactive; it does not disappear. It can reactivate when price reenters, and a crossed range order can trade back unless removed.[2] **Claims:** `econ-cl-inactive`, `econ-cl-reversal`. Accrued fees and externally funded incentives must be accounted for separately.

### Compare to official tests without pretending to implement Solidity

Pinned `Uniswap/v3-periphery` commit `0682387198a24c7cd63566a2c58398533860a5d1`, `test/LiquidityAmounts.spec.ts`, lines 145–213, provides inside, below, above and boundary vectors.[7] **Claim:** `econ-official-vectors`; document `econ-v3-tests`.

The offline test compares continuous Decimal quantities with those expected integer outputs using floor equality and absolute difference less than one raw unit. For `Pa=100/110`, `Pb=110/100`, the official inside fixture has `P=1`, `L=2148`, expected integer amounts `(99,99)`; below uses `P=99/110`, `L=1048`, `(99,0)`; above uses `P=111/100`, `L=2097`, `(0,199)`.[7] Lower/upper boundary vectors are also checked. **No Hardhat/Solidity suite was executed, and this is not proof of Q96 or protocol-rounding conformance.**

## 4. Stable invariants are a distinct family

Do not use constant-product IL or swap-output formulas merely because a pool contains two tokens. The original StableSwap design deliberately combines a nearly constant-sum region near balance with increasing curvature as inventory becomes imbalanced.[3] **Claims:** `econ-stable-family`, `econ-stable-A`.

In the original paper's notation (visually checked on PDF p5):

```text
A*n**n * sum(x_i) + D = A*D*n**n + D**(n+1)/(n**n * product(x_i))
```

`D` is the invariant balance measure; balances must use the implementation's common precision/rate normalization. Solve D from the initial balances and solve the new balance while preserving the invariant; the paper describes an iterative solution.[3] **Claim:** `econ-stable-solve`. Production variants may change rate handling, amplification scaling, dynamic fees and rounding; the equation is **not** a ready-to-use Curve quoter or a specification for every stable AMM.

Low near-peg impact is purchased with a curve designed for correlated values, not a guarantee the assets remain correlated. The paper itself says a shifted equilibrium places the invariant at a suboptimal operating point.[3] **Claim:** `econ-stable-offpeg`. As an economic implication, a depegging asset can be sold into the pool against the better asset, leaving LPs with deteriorating inventory. Amplification and tight ranges do not create backing, redeemability or solvency. Historical simulated APR in this paper is not evidence of present expected returns.

## 5. TVL versus usable depth

TVL is a valuation of balances under selected marks. Executable depth is directional and size-dependent: what output is available for this input, in this state, within a price/cost bound? Full-range pools already have nonlinear impact; concentrated pools add active-liquidity and tick-boundary changes.[1][2]

The tested CPMM fixture has x=100, y=400 and spot P=4. TVL marked in token1 is `800.000000000000`. Selling 10 token0 produces only `36.363636363636` token1 without fees, an average of `3.636363636364` rather than 4; average impact is `9.090909090909%`. A 0.003 input fee reduces output to `36.264435755206`. The other direction requires its own calculation. “800 TVL” is neither 800 units of sellable token1 nor a promise of execution at spot.

For the concentrated fixture, real balances at P=4 are x=2,y=12 regardless of its larger virtual reserves. Extra TVL in ranges far away does not provide the same local depth as active liquidity. It may become relevant if the trade crosses into those ranges; an honest quote must traverse them rather than assume all TVL is active.[2]

**Minimum evidence for any real depth claim:** block/time, token direction, exact input units, protocol fee/hook/transfer behavior, active liquidity and next boundaries, output and minimum-output assumptions, independent mark source, and stale-state caveat. None of those live observations are supplied by this offline example.

## 6. Reproduce the fixtures

The upstream Decimal script, tests and research reports are not shipped with this plugin; there is no package command to replay them. The formulas, inputs and historical outputs above support independent reproduction. Historical tests used stdlib Decimal precision 60 and ROUND_HALF_EVEN, formatted to 12 decimal places, and rejected binary floats/non-finite inputs. These are inherited research results, not tests run by this release. See [LP economics](06-lp-economics.md) for benchmark and accounting interpretation.

**Acquisition limits:** complete original PDF bytes and complete HTML/text responses are privately preserved and hashed. PDF text has two-column layout and font artifacts; the original PDF controls when text is ambiguous. HTML image content is not reproduced as math evidence. No deployed source matching, wallet verification, tax advice or profitability claim is made.

## Sources

[1] https://app.uniswap.org/whitepaper.pdf — econ-v2
[2] https://app.uniswap.org/whitepaper-v3.pdf — econ-v3
[3] https://curve.fi/files/stableswap-paper.pdf — econ-stable
[4] https://arxiv.org/html/2208.06046v6 — econ-lvr
[7] https://raw.githubusercontent.com/Uniswap/v3-periphery/0682387198a24c7cd63566a2c58398533860a5d1/test/LiquidityAmounts.spec.ts — econ-v3-tests
