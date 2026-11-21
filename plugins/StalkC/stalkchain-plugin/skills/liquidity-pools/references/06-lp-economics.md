# LP economics: income is not performance

**Scope / as of:** 2026-10-02. Educational accounting and risk analysis grounded in Uniswap v2/v3 papers, the original StableSwap paper, Milionis–Moallemi–Roughgarden–Zhang **LVR paper v6** (current version stated May 3, 2026), Uniswap Labs' **September 2022** JIT research, and the captured Ondo Stocks disclosures. No measured portfolio performance, deployed pool state, historical strategy backtest or trading recommendation is supplied. No example script is shipped, and no key access or transaction capability is authorized.

## 1. Choose the question and benchmark first

A useful LP report answers at least three different questions:

1. **Absolute PnL:** how did total economic wealth change in a named numeraire, after external cash flows and costs?
2. **Versus holding:** was LPing better than retaining the initially supplied tokens, marked at the same final prices? This is the relevant static benchmark for divergence loss.
3. **Versus rebalancing:** how did LP execution compare with a self-financing strategy holding the same changing risky-asset inventory but executing trades at an external price? This is the LVR paper's benchmark, not a static hold portfolio.[4]

Never call these interchangeable “yield.” A profitable dollar result can underperform holding a strongly rising asset. A loss versus holding is not necessarily a dollar loss. Fees can be positive while both absolute and benchmark-relative performance are negative. These are accounting consequences of changing the benchmark, not empirical claims of strategy profitability.

## 2. Value inventory before counting income

At observation time t, mark each principal quantity independently: `V_t = q0_t*m0_t + q1_t*m1_t`, with marks in one chosen numeraire. For token1 as numeraire, `V_t=q0_t*P_t+q1_t`. Record mark source, timestamp and whether it is a display mid, external executable bid, stale close or pool spot. The v2 whitepaper warns against naive current pool spot oracles; a manipulated mark can make accounting look profitable without an available exit.[1] **Claim:** `econ-oracle-manipulation`.

Inventory changes are economically real even before tokens are withdrawn: Uniswap's design changes token balances through swaps and range traversal.[2] **Claims:** `econ-cl-single`, `econ-cl-reversal`. “Realized” has several meanings; specify which:

- **Accrued fee quantity:** accounting entitlement, possibly not collected.
- **Collected fee quantity:** moved to a wallet, but still exposed to token price if unsold.
- **Realized sale proceeds:** actual sale cash flows net of execution costs.
- **Unrealized marked inventory:** remaining quantities valued at stated marks.

Do not claim tax realization from this economic terminology. Claimable rewards and fee balances should be valued separately from principal. If a vault auto-compounds, fees may already be in its principal/share value; counting them again overstates returns. v3 itself does not automatically reinvest its separately held fees as liquidity.[2] **Claim:** `econ-cl-fees`.

### A reconciled cash-flow identity

For a single period in one numeraire, define disjoint components:

```text
net PnL = ending principal + fees + incentives + external withdrawals
          - opening capital - external deposits - gas - execution costs
```

This identity assumes principal excludes the separately counted fee/reward assets and costs have **not already reduced** the other fields. If ending wealth already includes collected rewards or net sale proceeds, set overlapping fee/cost lines to zero or use an all-assets wealth ledger instead. External withdrawals here mean capital distributions, not fee collections already in the fees field. Value deposits/withdrawals consistently at their event times; return percentages with material flows need time-weighted or money-weighted methods, not division by an arbitrary final TVL.

**Tested fixture:** opening 1000; ending principal 900; separately valued fees 60; rewards 20; gas 15; separately paid execution cost 10; no external flows. Result: **net PnL = -45.000000000000** numeraire units. The fees-plus-incentives dashboard would show positive income while the full result is negative. With a further deposit of 100 and capital withdrawal of 40, the test yields -105. These are synthetic, explicitly specified accounting inputs, not fabricated observed returns.

**Reconciliation checklist:** include residual dust, escrowed/reward balances, fee collections already sold, native gas inventory, failed transaction costs, wrapper management/performance fees and actual entry/exit/rebalance swaps. Mark illiquid rewards conservatively and expose a zero-reward scenario. Incentive eligibility, vesting and claimability are separate deployment facts not verified in this lane.

## 3. Divergence loss / “impermanent loss”

For an initially equal-value **full-range constant-product** position, no fees or flows, and arbitrage aligning the pool with the external terminal price, let `r=P_end/P_start`. Relative to simply holding the initial quantities:

```text
LP_value / hold_value = 2*sqrt(r)/(1+r)
signed divergence = 2*sqrt(r)/(1+r) - 1
```

Derivation from the invariant: reserve x scales by `1/sqrt(r)` and reserve y by `sqrt(r)`; value the resulting amounts and the unchanged hold amounts at the same final price. This is a mathematical consequence of the constant-product invariant, not a formula valid for every curve.[1] The LVR paper explicitly distinguishes loss versus holding from loss versus rebalancing.[4]

**Tested values:** r=4 produces `-20.000000000000%`; r=0.25 produces the same relative loss; r=1 produces zero. The sign convention here is negative underperformance, whereas some dashboards display a positive “loss magnitude.” “Impermanent” does not promise recovery. If price returns exactly to start under this fee-free fixed-liquidity model, terminal divergence disappears; real fees, rebalances, withdrawals, costs or asset failure need not disappear.

For a finite range, use the piecewise inventory formulas in [AMM foundations](01-amm-foundations.md), preserve initial quantities, and compute the chosen benchmark directly. Applying the full-range formula to a concentrated position, a stable invariant, or a rebalanced strategy gives the wrong answer. Out-of-range inventory remains directional: below the token1/token0 range, principal is all token0; above, all token1.[2] **Claim:** `econ-cl-single`.

**Do not subtract IL twice.** If final principal is already marked from actual quantities, underperformance due to changing inventory is already in the value. “Net PnL minus IL” is generally a duplicate deduction unless it is explicitly a different benchmark decomposition.

## 4. LVR and adverse selection: a different loss mechanism and benchmark

Milionis et al. define a rebalancing strategy that holds the AMM's changing risky-asset quantity but executes the same net trades at CEX prices. The AMM can trade against stale quotes while arbitrageurs use fresher external prices; the paper calls the resulting gap **loss-versus-rebalancing**, LVR.[4] **Claims:** `econ-lvr-benchmark`, `econ-lvr-selection`; document `econ-lvr`, §3, Lemma 2 and Theorem 1.

In the paper's continuous model:

```text
LP PnL = integral x*(P_t) dP_t + fees - LVR
instantaneous LVR rate = (sigma**2 * P**2 / 2) * abs(dx*/dP)
```

The first term is market exposure; fees minus LVR isolates the microstructural component in that model. LVR measures the quality of AMM execution relative to the changing-inventory benchmark, not merely the cost of changing inventory. Selling as prices rise and buying as they fall does not by itself define LVR: the benchmark makes the same inventory changes at different execution prices.[4] **Claim:** `econ-lvr-benchmark`.

Important assumptions are part of the result: continuous external price process, an external reference venue, zero arbitrage fees in the core model so AMM and external prices align, and a frictionless benchmark. Finite blocks, fee bands, jumps, failed transactions, actual hedge costs and hook behavior change realized outcomes. The paper separately discusses empirical discrete approximations; its theorem is not an exact plug-in estimator for every fee-paying deployed pool.[4] **Claim:** `econ-lvr-assumptions`.

### Primary-source numerical replication

For constant product, Example 3 / equation 19 gives instantaneous `LVR_rate/V = sigma**2/8`. With **assumed daily volatility 0.05**, the Decimal script reproduces the paper's **3.125000000000 basis points per day**.[4] **Claims:** `econ-lvr-cp-rate`, `econ-lvr-example`.

This is a rate normalized by contemporaneous marked value, not a guaranteed finite-horizon percentage loss of initial capital. Time units matter: daily sigma implies a daily rate; annual sigma implies an annual rate. Do not insert “5” for “5%,” confuse variance and volatility, or annualize a daily value without stating the horizon and model assumptions.

Concentration increases local inventory sensitivity per unit of actual capital; the paper's range-order example makes LVR/value unbounded in the limiting case of an arbitrarily narrow range around price.[4] **Claim:** `econ-lvr-concentration`. That mathematical limit is not a claim that deployed losses are literally infinite: discrete ticks, finite blocks, fees, competition and bounded inventory matter. It is a warning that capital efficiency is not free risk reduction.

**No double counting:** do not subtract LVR from marked realized PnL as though it were an additional gas bill. Use it as a benchmark decomposition, alongside—not blindly added to—loss versus holding. Without synchronized inventory and independent price histories, report LVR as **unmeasured**, not zero.

## 5. Fees, volatility and range occupancy

Swap fee income is a path-dependent allocation, not simply pool volume times fee tier divided by TVL. v3 only allocates swap fees to liquidity active at the traded price; the JIT research describes fee allocation proportional to supplied liquidity against order flow during the time supplied.[2][6] **Claims:** `econ-cl-inactive`, `econ-jit-share`.

A useful conceptual approximation is:

```text
position fees ≈ sum_over_swap_segments(
    eligible_fee_amount * position_active_L / total_active_L
)
```

It requires per-segment fee eligibility and protocol/hook treatment; raw aggregate volume is insufficient. The exact v3 accounting uses fee growth inside a range, described in its whitepaper, not a time-in-range multiplier alone.[2] Treat incentive emissions as a separate subsidy with its own eligibility, denominator and claim rules.

Track several occupancies rather than a single “uptime” score:

- **Time occupancy:** fraction of observed time in range. Missing observations are unknown, not active.
- **Volume occupancy:** fraction of relevant traded volume occurring while the position was eligible.
- **Fee-weighted participation:** actual share of eligible fees, accounting for changing competing liquidity.
- **Capital occupancy:** how much capital is committed, including idle out-of-range inventory and gas/rebalance reserves.

These are proposed reporting definitions, not assertions that public dashboards expose them. A position can be active most of the time yet miss the swaps generating most fees; frequent rebalancing can increase participation while worsening net results through costs and adverse selection. More volatility can create both fee-paying flow and greater inventory/LVR losses; the LVR formula demonstrates why a fee-only volatility thesis is incomplete.[4]

For evaluating a range policy, predefine entry, range width, observation cadence, rebalance triggers and stopping rules. Compare a fixed-range baseline and a hold benchmark using the same prices and flows. Include adverse regimes and periods without incentives; do not optimize range width on the full sample and present the result as forward evidence. No strategy backtest was run here.

## 6. MEV and JIT: distinguish ordering effects

**JIT** places liquidity immediately before a known swap and removes it immediately after. Uniswap Labs' historical research describes mint → swap → burn, an offsetting hedge elsewhere, and competition for inclusion against other searchers.[6] **Claims:** `econ-jit-definition`, `econ-jit-cost`, `econ-jit-competition`. It is not evidence that JIT accounts for any particular fraction of current flow: the article's sample is from 2021–2022.

Economic implications of that documented mechanism:

- A passive LP's fee share can shrink when new active liquidity arrives just for the swap, even if total pool fee revenue rises.
- A trader may obtain improved depth from JIT; it is not automatically the same as a harmful swap sandwich.
- JIT providers must cover inventory hedging, gas and inclusion competition, not merely collect the displayed pool fee. Positive expected revenue before bidding does not assure inclusion or net profit.[6]

A **swap sandwich** and **back-running arbitrage** are alternative ordering strategies discussed in the article's MEV competition analysis.[6] Do not label every arbitrage, LP mint/burn or price movement a sandwich. For a real incident require ordered transactions, affected swaps, inventory/fee transfers and an explicitly stated counterfactual. For LP economics, observed fees may coexist with adverse selection; a large fee-generating informed trade is not necessarily good flow.

This reference teaches classification and accounting, not transaction construction, private relay use or MEV execution.

## 7. Stablecoin depeg: the failed correlation assumption

StableSwap's paper designs low impact near balance and explicitly acknowledges a suboptimal operating point when price shifts away from equilibrium.[3] **Claims:** `econ-stable-family`, `econ-stable-offpeg`. A stablecoin label is not a payoff guarantee. As a model implication, a pool offering the weak asset near the old relative price permits traders to exchange it for the stronger reserve, changing LP inventory toward the weak asset until the curve reprices or depth is exhausted.

For risk review, distinguish:

1. **Temporary market basis:** price dislocation with uncertain recovery.
2. **Redemption/liquidity restriction:** market price may differ from an inaccessible nominal redemption price.
3. **Backing or issuer impairment:** par can be an invalid valuation, not merely a cheap entry.
4. **Pool or token controls:** pause/freeze/transfer restrictions may block an otherwise plausible exit.

These are diligence scenarios, not claims about a named live stablecoin. Stress both reserves independently against the reporting currency, include correlated failures, and price actual exit size. A fee or incentive stream denominated in the depegging asset may fall in value at the same time as principal. Neither amplification nor concentrating around one restores the peg.

## 8. Tokenized stocks: a 24/7 pool is not a 24/7 hedge

Do not import a specific issuer's rules into another token. In the captured Ondo disclosures, the tokens provide economic exposure but are not the underlying stocks, ETFs or ADRs and do not confer rights to receive those underlying assets.[5] **Claim:** `econ-stock-rights`. Verify the actual instrument, issuer, share multiplier, eligibility, redemption rights and corporate-action treatment before treating one token as one share.

Ondo warns that selected assets can have off-hours availability but lower liquidity, wider spreads, conservative dynamic size limits and rejected quotes, with material token repricing when the underlying primary market reopens.[5] **Claims:** `econ-stock-offhours`, `econ-stock-reopen`. This explicitly defeats two blanket claims: “all stock tokens stop at the close” and “24/7 transferability means unlimited 24/7 hedge liquidity.” No current asset status or spread was requested or measured here.

Its market-data endpoint documentation says its prices are intended for display and advises against using those feeds as an oracle.[8] **Claim:** `econ-stock-display`. This is product-specific documentation captured on the as-of date; re-check before use. No API key was accessed and no market-data API call was made.

**LP risk implications and required observations:**

- A stale close, displayed mid, token secondary-market price, redeemable NAV and size-specific executable hedge are different marks. Keep each timestamp and session status.
- A narrow range around Friday's close can be wrong after news; an informed counterparty may trade before an LP can hedge or an oracle updates. Model price gaps, not only continuous volatility.
- DEX trades can occur while underlying or issuer trading/redemption is restricted. Document which venues and sizes actually remain available; do not assume off-hours inventory can be neutralized.
- Check oracle heartbeat/deviation rules, freshness rejection, fallbacks and pause behavior for the **specific pool/hook**, then test weekend, holiday, halt and reopening scenarios. None of those deployed controls is verified by this lane.
- Corporate actions and changing share multipliers require coherent marks on both token inventory and hedge units. A pool price near the last stock price does not validate the conversion ratio.

These are deductions and a diligence checklist grounded in the disclosed frictions, not a profitable stock-LP playbook. A high APR screenshot without these observations is insufficient evidence.

## 9. APR snapshots versus realized returns

A dashboard can annualize recent fees using current capital. For a window of d days, the reporting convention `simple APR=(window income/capital)*365/d` is an extrapolation, not a promise. Compounded APY adds a reinvestment assumption; it is not interchangeable with APR. State calendar/active days, token and numeraire, capital denominator, protocol/incentive split, fees versus total return, and whether fees were actually realizable.

**Acceptance answer to “a two-day 600% APR proves a good strategy”:** no. Request a reconciled inventory/cash-flow ledger, range and fee-growth history, actual costs and reward liquidity, independent marks, sample dates and missing periods, and hold/rebalancing benchmarks. Label unverified screenshots self-reported. Decline to extrapolate two days into expected annual profit. The LVR paper's distinction between market exposure and fee-minus-adverse-selection performance explains why headline fees alone cannot settle the question.[4]

## 10. Reproducibility and limits

The upstream Decimal script, unit tests and research reports are not shipped. There is no plugin command to run them. The formulas and illustrative inputs are given above for independent reproduction; these historical outputs are not release-time test results.

Exact formatted economics outputs:

```text
il_r4_pct                  -20.000000000000
lvr_daily_bps_sigma_005      3.125000000000
net_pnl                   -45.000000000000
```

The foundations reference explains the formula conventions and precision. Data are **specified illustrative inputs**, not fetched trades. There is no quoter, fee-growth implementation, backtester, oracle, transaction builder or trading engine. Stop at analysis if asked to execute: research approval does not authorize portfolio changes.

**Source limitations:** immutable original PDF/HTML bytes are retained privately with hashes. LVR HTML has the complete paper through its final SQL appendix; a search/extraction service returned an upstream-truncated version, which was not used as evidence. JIT article images were not independently downloaded or interpreted; text claims and no image-derived numerical claims are used. Ondo documentation is mutable and provider-specific. StableSwap and JIT historical examples do not validate current expected returns. No on-chain claim is marked verified.

## Sources

[1] https://app.uniswap.org/whitepaper.pdf — econ-v2
[2] https://app.uniswap.org/whitepaper-v3.pdf — econ-v3
[3] https://curve.fi/files/stableswap-paper.pdf — econ-stable
[4] https://arxiv.org/html/2208.06046v6 — econ-lvr
[5] https://docs.ondo.finance/ondo-stocks/important-notes — econ-ondo
[6] https://blog.uniswap.org/jit-liquidity — econ-jit
[8] https://docs.ondo.finance/api-reference/assets/get-market-data-for-all-supported-assets — econ-ondo-oracle
