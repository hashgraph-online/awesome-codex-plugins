# Activation and measurement

## Where an audience goes, and what it does there

AMC audiences surface in DSP and, where the account has it enabled, in the Sponsored Ads console. Check the current console before planning (`CURRENT_POLICY`), because availability varies by advertiser, marketplace, and ad product.

| Channel | Mechanism | Consequence for measurement |
|---|---|---|
| DSP | Direct targeting or exclusion in a line item or ad group | The audience defines who can be reached, so compare against a holdout of the same audience |
| Sponsored Display | Direct audience targeting | Same as DSP |
| Sponsored Products, Sponsored Brands | Audience bid boost: a percentage bid adjustment that applies when an audience member matches the campaign's existing keyword or product targeting | The audience doesn't narrow eligibility. Measure the boost: incremental conversions and profit on boosted traffic against the extra cost per click |

Several bid adjustments can stack (placement, audience, and others). Record every adjustment already on the campaign so the effective bid is known before you propose a new one.

## Before activation

Confirm:

- The audience exists, is the expected size (the sizing companion's estimate before creation, then the size AMC reports after), and shows in the target console.
- For a lookalike, the exclusion that keeps the seed's existing buyers out of its spend is in place, unless the lookalike already excludes the seed.
- The target campaign or line item is eligible for the action.
- How long activation takes to propagate.
- Currency and marketplace match.
- Budget headroom, inventory, creative, and the review date.

A successfully created audience isn't necessarily visible or usable in every ad type.

## One change per action card

Each card makes exactly one change:

- add or remove one audience;
- set one audience bid adjustment;
- exclude one defined group;
- activate one lookalike;
- change one window, refresh cadence, or budget.

Hold campaigns, listings, prices, offers, and other bids as steady as possible during the test, and record what you couldn't control (a competitor's deal, a stockout, a price change).

## Baseline and holdout

- **Baseline:** reach, clicks, detail page views, conversions, NTB, cost, frequency, profit after returns, and inventory use over a comparable recent period.
- **Holdout, strongest first:**
  1. An Amazon experiment or lift-measurement tool, if one is available for the channel.
  2. A randomized split of the audience into an activated group and a held-out group over the same period. A split drawn with `random()` inside an audience query re-draws on every refresh, so shoppers would cross between groups. Use a split that stays fixed per shopper across refreshes (confirm the method with a dry run), or an Amazon tool that holds out for you.
  3. Comparable groups, regions, or time slices.
  4. Before and after the change. This is the weakest design because seasonality, promotions, and competitors all move at once; label conclusions from it as correlational.
- **Data access for the read:** a comparison against purchasers who saw no ads reads base `conversions_all`, which needs AMC's paid feature. Check access before choosing a design that depends on it, and fall back to a design that reads only ad-exposed data if it's missing.
- **Attribution and maturity:** record the conversion definition, NTB definition, and lookback, and the date the data matures. Don't conclude from immature conversions.
- **Lift:** report absolute and relative lift with sample sizes and a confidence interval where the data allows. Write "correlational, not causal" on any result without a holdout.

## Choosing the primary metric

| Goal | Primary metric | Guardrails |
|---|---|---|
| Extend effective reach | Incremental or relevant reach | Frequency, cost, wasted impressions |
| Shorten the decision | Time to conversion distribution, conversion rate | Profit, returns, discount cost |
| Recruit new customers | NTB orders, sales, acquisition cost | Total profit, repeat purchase, inventory |
| Retarget | Conversions, CPA, ROAS against holdout | Frequency fatigue, purchases that would have happened anyway |
| Bid boost | Incremental conversions and profit per extra dollar of CPC | Effective bid after stacking, spend caps |
| Suppress | Spend saved with conversions held | Lost conversions in the excluded group |
| Rebalance budget | Marginal conversions or profit | Overlap, cannibalization, spend caps |

## Stop conditions

Pause and roll back when any of these happen:

- The scope turns out to be wrong (account, marketplace, campaign, or currency mismatch).
- A privacy or eligibility anomaly appears.
- Frequency or spend exceeds its guardrail.
- The change loses money after returns.
- Core inventory runs short.
- The audience size or data coverage shifts enough to distort the test.
- The test is contaminated by another change.

## Review

Record the audience version, query version, run times, activation status changes, original and rollback values, and anything that interfered. On the review date choose:

- `KEEP`: the effect held against the holdout and guardrails.
- `ITERATE`: promising, but change one variable and retest.
- `ROLLBACK`: restore the recorded original values.
- `EXPIRE`: retire the audience so it stops refreshing (a deletion gets its own ask).

Don't leave an audience running past its review date because nobody revisited it.
