# Analysis models and how they are misread

Pick the model from the decision question, run the smallest version that answers it, and state what the result can and cannot support. Draft the SQL from the playbooks in `07-playbooks.md` (M1 to M8) or the instructional query named. The quoted names below are Atlas instructional queries (topic `sql_templates`, titled `Use case: …`). Find them by title, since Atlas IDs change with each reindex.

## Time to conversion

Answers: how long, and after how many ad touches, shoppers go from a defined first exposure to purchase.

- Output a distribution with percentiles (median, 75th, 90th) and group comparisons, not just a mean. A long tail of slow buyers drags the mean away from what most shoppers do.
- Fix the ASIN or price band, marketplace, window, and conversion event before comparing groups.
- A long cycle doesn't make a product weak. Price point, replenishment cadence, repeat purchase, media mix, and seasonality all stretch it.
- This is the usual source for an audience lookback. Set the window near the percentile that covers most converters, then check that frequency fatigue and post-return losses don't erase the gain from a longer window.
- Lag measured on attributed events can't exceed the attribution window and counts from the attributed touch, not the first exposure, so it understates long consideration cycles. For replenishable products, the repurchase interval (playbook M4) is often the better window source.
- Playbooks: M1 (lag from ad touch to purchase), M4 (repurchase interval). Instructional queries: "Time to Conversion", "Time to first purchase with extended lookback", "Incremental reach and timing of exposures".

## Path to conversion by campaign group

Answers: which sequences of ad exposure precede purchase.

- Define campaign groups that don't overlap and that a marketer can read, such as awareness, consideration, and conversion, or by ad product. Output paths with reach, conversions, sales, NTB, and the cost basis.
- Appearing early in a path doesn't earn full credit, and appearing last isn't the only contribution.
- Common paths are often just the paths of the highest-reach campaigns. Compare against exclusive reach and frequency before reading a path as a strategy.
- Custom attribution (Markov chains, removal effects, position-based weights) is a modeling choice. Record the algorithm, assumptions, training window, and stability; don't present it as AMC's default output.
- Instructional queries: "Path to conversion by campaign groups", "Compare purchase path of converters versus non-converters", "Custom attribution overview", "Custom attribution - first touch", "Custom attribution - last touch", "Custom attribution - linear", "Custom attribution - position based".

## Ad-type overlap

Answers: whether ad products reach the same shoppers, and how exclusive and combined groups behave.

- Separate exclusive reach from combined reach and compare reach, conversion rate, NTB, cost, and sequence.
- A higher conversion rate in the combined group is the classic trap. Shoppers who see several ad types are usually more engaged to begin with: they searched more, browsed more, and were retargeted more. That is self-selection, not proof of synergy.
- **Pooled marketplaces can manufacture the gap.** If the combined group comes mostly from a high-converting marketplace and the single-channel group from a low-converting one, the pooled comparison mixes a market difference into the channel difference. Illustrative arithmetic: DE converts at 5.0% combined against 4.0% single, and FR at 1.5% against 1.2%, so within each market the combined group converts 1.25 times as well. Take 10,000 shoppers in each market, put 8,000 of DE's in the combined group and 8,000 of FR's in the single group, and the pooled rates become 4.3% against 1.8%, about 2.4 times. The gap can even reverse direction (Simpson's paradox). Report each marketplace first.
- **The group's rate isn't the next dollar's rate.** The combined group's conversion rate describes the shoppers already reached, and they are often the most engaged. Moving budget into a channel buys additional, usually less engaged shoppers at rising cost, so marginal returns fall as spend grows. A budget shift needs the marginal effect, which only a test measures.
- **Check maturity and the window.** Attributed conversions keep arriving after the window closes, and the channels may not have run over the same dates. Compare only matured, matched windows.
- **Check how each group's conversions are credited.** DSP can be credited for purchases after a view, while sponsored ads are mostly credited after a click, so attributed conversions favor groups that include DSP. Compare groups on one definition, such as any brand purchase after first exposure. Results summed across separate AMC instances can't match shoppers between them, so the pooled counts may double count.
- **No "neither" rate.** AMC sees only shoppers who were exposed or who converted, so the purchase rate of shoppers who saw neither channel isn't measurable. A holdout supplies that comparison.
- Validate with a holdout, a geographic or time split, or an Amazon experiment tool before shifting budget.
- A large overlap is a reason to check frequency, marginal reach, and budget skew, not to raise the total budget.
- Playbook: M2 (exposure-group overlap). Instructional queries: "Sponsored ads and DSP overlap", "Sponsored Products and DSP Display overlap", "Sponsored Display and DSP overlap", "Amazon DSP Display, Streaming TV and Sponsored Products 3-way overlap", "Audience overlap analysis".

## Reach and frequency

Answers: how conversion changes with the number of exposures, by audience, ad type, and period.

- Read the frequency distribution and sample size per bucket, not the average frequency.
- Higher buckets hold more engaged shoppers, so conversion rising with frequency is partly selection. Compare adjacent buckets and look for where the marginal gain flattens.
- Look at conversion lag and creative fatigue alongside frequency.
- Treat "raise frequency", "refresh creative", "narrow the audience", and "lengthen the window" as separate experiments.
- A frequency figure from a case study is an `EXTERNAL_BENCHMARK`.
- Instructional queries: "Reach and impression frequency", "Optimal frequency deep dive for on-Amazon and off-Amazon conversions", "Reach penetration within target audience".

## New-to-brand

Answers: how much of the purchasing comes from shoppers new to the brand.

- Confirm Amazon's current NTB definition, the ad types it covers, and its lookback (`CURRENT_POLICY`).
- Report NTB purchases, orders, sales, and share separately. A high share on low volume isn't scale.
- A high NTB share doesn't mean high profit. Pair it with acquisition cost, returns, repeat purchase, and total sales.
- Upper-funnel ads without immediate orders aren't worthless, but a path that includes them isn't evidence of their incremental value either.
- Playbook: M3. Instructional queries: "New-to-brand customers", "New-to-brand purchases", "Campaign performance by user funnel stages".

## High-value segments

Answers: which customers are worth seeding a lookalike from, protecting with retention, or suppressing from acquisition spend.

- Define value from data the instance holds (order count, sales, repeat cadence) over a window long enough for the category's repurchase cycle.
- Report tiers in aggregate. A tier too small to clear the aggregation threshold is too small to activate.
- Instructional queries: "Identify high value customer segments", "Audiences based on high value customer segments", "Customer long term value by exposure group".

## Quick reference

| Model | Required inputs | Compare against | Main misreading |
|---|---|---|---|
| Time to conversion | Start event, end event, duration, conversions | Product, category, period | The average is the answer |
| Path | Ordered touchpoints, shoppers, orders | Exclusive, combined, and sequenced groups | A path shows cause and effect |
| Overlap | Reach, intersection, conversion, by marketplace | Exclusive single-ad-type groups, matured matched windows | Correlation is synergy; the pooled gap is the channel gap |
| Frequency | Frequency bucket, reach, orders | Adjacent buckets | The average frequency is the optimum |
| NTB | NTB orders, sales, shoppers | Overall and historical NTB | Share equals scale or profit |
| High-value | Orders, sales, repeat cadence | Other tiers | Value tier equals incremental response |
