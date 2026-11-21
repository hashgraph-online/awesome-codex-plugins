# Community LP playbooks: hypotheses, not verified returns

**As of 2026-10-02.** Scope: public practitioner posts, their quoted articles, and directly linked public tools/documentation. This is a skeptical research synthesis, not a recommendation to open, close, copy or automate a position.

**Evidence boundary.** `community_only` means the source really makes the statement, not that the strategy, profit, issuer rule or deployment has been independently verified. A complete retrieved post is not necessarily a complete thread, article, screenshot or transaction history. `documented` below applies to a tool's published limitations, not proof that its implementation satisfies them. There is no independently executed RPC evidence or reconstructed wallet accounting in this lane. Protocol versions and chain labels are author-attributed unless explicitly identified as a pinned repository version.

## 1. Narrow tokenized-stock/stablecoin range

**Attribution / hypothesis.** [@0xTindorr](https://x.com/i/status/2096186049710199250) describes buying a stock they would willingly hold, pairing it with USDG and supplying a narrow Uniswap range on Robinhood Chain. The intended economic trade is fee collection in exchange for mechanically reducing stock exposure as the stock rises. The author explicitly acknowledges missed upside above the range and says the headline APR will not persist indefinitely. The post does not identify a pool, position, fee tier, hook or protocol version.

**Reported policy and period.** Entry around $594; META range around $560–635; later price around $617; approximately three days of evidence. Claimed fees are 4.7% of starting capital and claimed “IL / rebalancing drag vs simply holding” is 0.7%. Rebalance timing, hedge rules, exit fills, cash additions and token valuation methodology are absent. Do not invent them from the headline.

**Arithmetic check, not a performance audit.** The stated figures imply approximately 571.83% simple annualized gross fee rate, not an exact 600%+ rate. Rounded inputs or a different observation interval could explain this, but neither is supplied. The full stated price interval is approximately 12.63% of the $594 entry price; the upper/lower distances are approximately +6.90%/−5.72%, so the author's “~8% range” is not the straightforward full-width calculation. Fees divided by the claimed relative drag are approximately 6.71, consistent with “almost 7x.” None of these calculations establishes that the fees or drag were measured correctly.

Reproducible diagnostic, using percentage-valued inputs:

```python
from decimal import Decimal as D
print(D('4.7') / D(3) * D(365))
print((D('4.7') - D('0.7')) / D(3) * D(365))
print((D(635) - D(560)) / D(594) * D(100))
print(D('4.7') / D('0.7'))
```

Observed output:

```text
571.8333333333333333333333335
486.6666666666666666666666665
12.62626262626262626262626263
6.714285714285714285714285714
```

The second line is only subtraction and rescaling of the author's two percentages. It is **not** net portfolio APR: the meaning of the benchmark drag is underspecified and operating costs remain unknown. Subtracting a separately measured inventory loss, divergence loss and LVR without reconciling their definitions may double-count the same economic loss.

**Assumptions to test.** Organic volume remains high while price spends enough time in range; fee receipts are attributable to this position; USDG and the tokenized share remain usable at the intended valuation; issuance/redemption, transfer restrictions and market hours do not prevent the planned exit. A willingness to hold a share is not identical to accepting all risks of its onchain representation.

**Failure conditions / counterexamples.** A sustained rally leaves less stock exposure and missed upside; a fall concentrates the position in the falling asset; a gap or token premium reversal can cross the range before fees compensate. Repeated recentralization buys back exposure after price moves and can turn an apparent “take profit” policy into costly chasing. A screenshot cannot exclude these paths.

**Confidence:** good evidence of the author's stated hypothesis; low confidence in repeatable net profitability.

## 2. Flow-driven, multi-range memecoin LP

**Attribution / hypothesis.** [@DankoWeb3](https://x.com/i/status/2097087523688153487) reports +$21,124 realized PnL and 1,622 trades, with a headline starting balance of $1,000. The post describes a workflow, not a complete audited account. A quoted endorsement from another account is not independent corroboration of those returns.

**Entry and selection.** Watch recent Robinhood token launches and five-minute volume, but compare volume with **active liquidity**, not just displayed TVL. Investigate holders, connected wallets and narrative; the author says to skip suspiciously bot-heavy or concentrated flow. Their social/KOL criterion is an author's heuristic, not a security test: popularity and independent beneficial ownership are different questions.

**Range policy.** The author uses Liquidity Ladder to distribute capital among several ranges rather than one spot-centered allocation, describing Bid Ask and Curve options as analogous to Meteora-style strategies. This does not establish that the underlying protocol is Meteora, that a Uniswap pool uses bins, or that distributions have identical mathematical behavior. Record the actual protocol, range boundaries, fee tier and position identities before translating a UI label into mechanics.

**Management and exit.** Exit or reassess when recent volume disappears; sometimes seek fee-tier transitions before flow migrates, sometimes hold for days. These are qualitative observations. No precise occupancy threshold, fee-decay rule, rebalance cost model or stop condition is supplied. Do not backfill a deterministic profitable algorithm from a narrative.

**Costs and failure cases.** Swaps and closing inventory, failed transactions, gas, routing fees, token taxes, hooks and adverse fills belong in the ledger. Fee-tier migration can strand a position in a pool with little flow. Narrow ranges compete with other LPs and may concentrate on the wrong side of a move. Wallet imitation adds observation latency, may omit hedges or other accounts, and selects visible survivors rather than an unbiased cohort.

**Evidence needed before confidence increases.** Position-event history, deposits/withdrawals, collected and uncollected fees, token inventory valued independently, failed/abandoned positions, cash additions, period boundaries and a declared benchmark. “Realized PnL” alone cannot establish total economic return while losing inventory remains open.

**Confidence:** useful research checklist; profitability remains self-reported.

## 3. Very tight bin breakout tactic: an execution-risk example

[@molusol](https://x.com/i/status/2097361368135467139) describes finding heavy volume near a breakout and opening a position of fewer than ten bins, continually claiming/converting fees to SOL and keeping an emergency exit ready. The linked [day-two result](https://x.com/i/status/2097347171271979009) reports +$2.12K, but supplies neither a complete position history nor the promised pinned tutorial. Protocol/version is unspecified in the captured text; SOL denomination and the word “bins” do not uniquely identify a deployment.

The hypothesis is concentrated exposure to a short burst of fee-generating flow. It assumes the operator can detect deterioration and exit faster than the adverse move. The visible range rule says nothing about bin step, price width, amount per bin, slippage or exit liquidity. The same number of bins can represent different price spans under different configurations.

The post's “auto approve” suggestion is **not adopted here**. Human cursor placement is not a guarantee of transaction inclusion, permission validity or an executable sell. A rug, blocked transfer, hook restriction, RPC failure or discontinuous price move may eliminate the exit before a person reacts. Frequent fee conversion also adds execution costs and changes inventory exposure. This is an example of an operationally demanding, potentially catastrophic-risk tactic, not passive income.

**Confidence:** the small captured text supports describing the tactic, not validating it.

## 4. Tokenized-stock premium / market-hour counterexamples

[@osf_rekt](https://x.com/i/status/2094365960576590157) describes a tokenized-AMC premium driven by demand for a meme/stock pair while traditional markets were closed, followed by a premium collapse. The specific minting restrictions, prices and timing are **author claims**, not generalized issuer rules. Do not state that every tokenized stock can only be minted during market hours or that every arbitrageur can access issuance on identical terms.

The useful research question is whether both legs of a pair are independently sound units of account. A meme valued in a premium stock token can show a large dollar move even without equivalent external demand for the underlying share. Monitor both the meme/stock exchange rate and stock-token/reference-market basis, distinguishing stale prices from real executable quotes. A tokenized-stock pool need not contain a useful amount of stock at the current price merely because the pair name includes that stock.

A Chinese-language [@PolarisAspire article](https://x.com/i/status/2069338573992538590), quoted by [Backpack_CN](https://x.com/i/status/2069339467882901597), describes maintaining exchange cash and onchain MU inventory, buying on the exchange while selling onchain and replenishing inventory. It self-reports 1,480+ U profit and names shallow pool depth/slippage as a risk. It is an **arbitrage-counterparty perspective**, not an LP return record. Its language about minimal or zero risk is not adopted: replenishment delays, unhedged inventory, exchange eligibility, hedging costs, failed transfers and converging spreads remain unresolved.

For an LP, such counterparties are a reason to examine who is paying the fees. High volume can come from traders exploiting stale prices or constrained issuance. Fees may accompany adverse inventory selection rather than compensate for it.

**Confidence:** strong motivation for basis and market-hours diligence, not verified facts about any current issuer.

## 5. Creator-tax harvesting is not LP fee performance

[@DidiTrading](https://x.com/i/status/2097271735791857853), quoting [@0xAsta](https://x.com/i/status/2097217545430327626), describes earning approximately 4.75986 NVDA through a 5% creator tax after launching a token. This is presented as harvesting sniper/bot flow. It is not evidence that an independent LP earned that return. Launch factory, version, quote asset, anti-sniping rules, first-launch eligibility and fee recipients would all need separate verification.

Use this as a **counterexample to fee-label confusion**, not a launch recommendation. Creator revenue, protocol revenue, terminal revenue, LP fees and holder distributions are different cash flows. Bot-triggered turnover can make a launch look active while benefiting the creator and leaving outside inventory holders exposed. An LP's rights cannot be inferred from a screenshot of somebody claiming creator fees.

Similarly, [@0xSammy's TAMPONS description](https://x.com/i/status/2096938067340783945) says holders do not own the short or have a claim on its collateral. Fee-funded perp collateral, realized short profit, treasury buybacks, token burns and LP principal are not interchangeable. The [linked Perps Hood page](https://perpshood.fun/coin/0xa3a273b2B389e718c0C490a4BAEE9347cD4a007b) was acquired and displays a graduated v4 pool, a PONS short and a treasury. Those UI labels are not independently verified state or redemption rights. The interface's displayed zero supply burned also does not establish that a described future routing mechanism has ever run.

[@0xIT4I's public essay](https://x.com/i/status/1995884603576648043) criticizes cumulative launchpad and terminal fees. Its historical numerical examples are not current universal rates. The reusable lesson is to allocate every fee layer to its recipient before deriving LP income from gross trading volume.

## 6. Tool-assisted discovery, with explicit coverage limits

- [@wock9000](https://x.com/i/status/2096433162230600019) links **rhpools.lol**. Its acquired page is a search/LP-wallet/pool table shell without usable pool rows; it does not substantiate live depth or PnL. [@ProMint_X](https://x.com/i/status/2096566582759559332) links **robinhoodpools.lol**, which the retrieval tool blocked as a private/internal-address destination. The two spellings are not silently merged. A second shortlink resolves to [Barker Raid](https://app.barker.money/raid/robinhood), whose extracted page explicitly normalizes two-hour fees per day against active liquidity. That rate is not annual realized portfolio return. No wallet connection or configured position was used.
- [Stockyard](https://stockyard.rhps.fun), linked by [@taylor_](https://x.com/i/status/2097332629544538342), has a [pinned README](https://github.com/gtmcknight/stockyard/blob/2de944fa6e6df417c576eecfb0d3cee0cad4e028/README.md). It explains a “parked” filter based on daily turnover and openly describes incomplete aggregator coverage and unpriced discovered pools. The cutoff is an analytical choice, not a theorem that low-turnover liquidity is economically useless. Its explicit out-of-range/one-sided caveats are more useful than interpreting its headline map as every pool on the chain.
- The [Rekt stock monitor](https://mkts.rekt.com/tools/stock-arb), linked by [@RektMkts](https://x.com/i/status/2094426247845539942), redirected to login during direct acquisition. The published premium/discount claim is not revalidated by that redirect. No payment or login was attempted.
- [Canary's author](https://x.com/i/status/2096615702366945625) describes a read-only memory of reserves, deployer activity, fees and phase changes. This is a sensible monitoring hypothesis, but its code/runtime was not exercised, and QUIET/WATCH/LEAVE are tool signals, not guarantees of safety or executable exits.
- [Warden's promotional post](https://x.com/i/status/2096593353517228312) claims trading profits. Its [pinned README](https://github.com/Archive228/warden/blob/247b5a2ddb00eb5e31019fc1080bcc84e8cf8695/README.md) states funded execution was never broadcast in its test environment, model judging remained blocked, and the backtest does not detect rugs. This does not prove the author's separate personal profit claim false; it does prevent interpreting that claim as a validated end-to-end trading result from the published tool. The README's broad Pons lock/safety statements must also defer to versioned official sources and matching deployment evidence. No downloaded commands were run.

A related freshness trap: a public o1 announcement links an Arc anchor, but the acquired rendered documentation describes only Base and Robinhood with an older verification date. Its linked machine-readable deployment JSON was acquired separately and contains Arc with a newer update date. Preserve both snapshots; do not interpret a missing rendered section as proof that the announced factory does not exist. The JSON is still the publisher's observation, not this lane's RPC evidence.

## 7. Agent LP demos do not authorize execution

[@mariorz](https://x.com/i/status/2095662830598885631) describes a $5 SPY/QQQ Uniswap v4 LP built/simulated through Revert MCP and signed through a policy wallet. [Revert's quote](https://x.com/i/status/2095862397885886870) supplies context, not another independent demonstration. The cited material supplies no verified transaction receipt, position identifier, permission policy or post-execution state. Simulation success would not prove economic suitability even if independently reproduced.

The boundary for this knowledge corpus remains **read, compare, explain**. It does not grant an agent a signer, spending policy, approval, deployment mandate or rebalance authority. A research worksheet can identify what needs verification without constructing a transaction.

## 8. Rejected shortcuts and unresolved teachings

The [“impermanent loss irrelevant” post](https://x.com/i/status/2096924763151307034) resolves to a photo, not an accessible full explanation in the retrieved material. Its mechanics remain blocked; do not invent a hedge or infer that IL has disappeared. The [beginner LP thread](https://x.com/i/status/2094407351377723765) has only an introductory sentence and photo link locally. HOOKR, NUKES.FUN and a Robinhood utility roundup have article titles/previews but no matching full local chapters. They do not count as full-text education sources.

[An advertised 1,500% APR](https://x.com/i/status/2099193781295735191) and [Ramses' SPY/ETH volume/fee promotion](https://x.com/i/status/2097316466890535406) are retained as source claims, not proof of profitability. Neither substitutes for position-level inventory and cash-flow accounting.

Three shortlinks in peripheral Arc-OTC discussion returned X unsafe-link-warning destinations. Those warnings were not bypassed. No Telegram group was joined. Similar names alone do not establish community identity.

## Research worksheet before evaluating any playbook

1. **Identity:** chain/network, token contracts, quote-token issuer, factory era, protocol/version, pool/position, fee tier and hook. Missing fields stay unknown.
2. **Hypothesis:** who trades, why they pay fees, why competing LPs have not eliminated the opportunity, and what observable fact would falsify it.
3. **Policy:** exact ranges/bins and their units; permitted observations; entry, exit and rebalance conditions fixed before inspecting outcomes. Separate author-specified rules from analyst-proposed tests.
4. **Accounting:** cash additions and withdrawals; initial/final token quantities; independent prices; collected/uncollected fees; incentive sales; operational costs; total return and a declared hold/cash/hedged benchmark. Avoid double-counting overlapping loss labels.
5. **Counterexamples:** out-of-range trends, premium collapse, depeg, disappearing flow, connected-wallet churn, token restrictions, hook restrictions and failed exits.
6. **Evidence:** period boundaries, complete sample including failures, source provenance, and reproducible transaction or position histories. A favorable screenshot or one profitable day cannot satisfy this gate.
7. **Decision boundary:** publish findings and unknowns. Do not rebalance, approve, sign, buy, launch, connect a wallet or copy a trader under research authorization.

**Bottom line:** the cited material supplies several serious hypotheses and useful warnings, but no independently verified profitable LP strategy. The unresolved-history and missing-media/article gaps are part of the result, not reasons to promote a headline into a certainty.
