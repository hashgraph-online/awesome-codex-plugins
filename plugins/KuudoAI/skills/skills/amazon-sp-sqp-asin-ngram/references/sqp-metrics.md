# SQP scope, counts and derived metrics

Use these rules for analysis and supporting records. Present the recommendation using the [seller-answer contract](decision-records.md); include a technical limitation in the main answer only when it changes the decision.

Use the pinned Amazon schema and reporting documentation in [amazon-sources.md](amazon-sources.md). Preserve raw fields alongside normalized or derived values.

## Scope before arithmetic

- Report type: `GET_BRAND_ANALYTICS_SEARCH_QUERY_PERFORMANCE_REPORT`. Identify ASIN-level rather than brand-level exports; do not mix them.
- Marketplace comes from `reportSpecification.marketplaceIds`, one marketplace per request, not from each source row. Attach it to analysis records. If a CSV omits request metadata, ask for marketplace; currency is not a substitute.
- Periods: `WEEK`, `MONTH`, `QUARTER`. A request covers one complete period; weeks run Sunday–Saturday. Validate dates and use comparable complete periods of the same granularity and marketplace. Do not sum overlapping weekly/monthly data.
- Keep `traffic_scope: sqp_reported_scope`. This is our label for search-results activity as reported, not an Amazon-defined organic/ads split. An independently documented organic-only source may be labeled `organic_only`; SQP alone does not justify it. Never subtract ad-attributed results to manufacture organic counts or mix SQP totals with spend for ACoS/ROAS.
- Identify each analysis row by marketplace, start/end/period, ASIN and original query. Retain source file/report reference and retrieval date. Missing scope permits descriptive inspection, but prevents comparable aggregation or actionable priority until resolved.

## Field mapping

| Source fields | Treatment |
|---|---|
| `searchQueryData.searchQuery`, `searchQueryVolume`, `searchQueryScore` | Original query, search count and reported query score. Carry score unchanged; it is not product organic position. |
| `impressionData.totalQueryImpressionCount`, `asinImpressionCount`, `asinImpressionShare` | Query market count, ASIN count, reported fraction |
| `clickData.totalClickCount`, `asinClickCount`, `asinClickShare` | Same scopes for clicks |
| `cartAddData.totalCartAddCount`, `asinCartAddCount`, `asinCartAddShare` | Same scopes for cart adds; do not drop this funnel stage |
| `purchaseData.totalPurchaseCount`, `asinPurchaseCount`, `asinPurchaseShare` | Same scopes for purchases; not revenue or units sold |
| `totalClickRate`, `totalCartAddRate`, `totalPurchaseRate` within their stage | Preserve reported values and the denominator-conflict note; never inputs to analytical ratios |
| `totalMedian{Click,CartAdd,Purchase}Price`, `asinMedian{Click,CartAdd,Purchase}Price` | Separate by event and scope; retain amount and currency. Compare only matching event/currency/period. |
| `total{SameDay,OneDay,TwoDay}Shipping{Click,CartAdd,Purchase}Count` | Nine query-wide totals, not ASIN distributions. No ASIN shipping diagnosis from them. |

API shares and rates are fractions. Convert explicitly labeled CSV percentages to fractions; ask if units are unclear. Do not assume shipping buckets exhaust all traffic or fabricate a “slower” remainder. Price medians are event-associated observations, not automatically the current offer price. Do not average medians across queries.

## Independent calculations (analyst definitions)

Compute from scoped raw counts, never reported rate fields. Label formulas and denominators in output.

| Derived value | Formula |
|---|---|
| Market clicks/search | total clicks / query volume |
| Market cart-adds/search | total cart adds / query volume |
| Market purchases/search | total purchases / query volume |
| Market CTR | total clicks / total query impressions |
| ASIN CTR | ASIN clicks / ASIN impressions |
| Market purchase-per-click | total purchases / total clicks |
| ASIN purchase-per-click | ASIN purchases / ASIN clicks |
| Relative conversion index | ASIN purchase-per-click / market purchase-per-click |
| ASIN stage share | ASIN stage count / market stage count |
| Click-to-purchase share gap | ASIN click share minus ASIN purchase share, in fraction points |

A zero numerator with a positive denominator is zero. Missing inputs or a zero denominator produce `null` and a reason. Counts must be nonnegative and scopes comparable; quarantine contradictory counts rather than silently replacing them. Reported shares may be displayed when counts are missing, but prefer count-derived shares for calculations and flag material discrepancies. These are event ratios, not distinct-shopper conversion probabilities; neither counts nor ratios prove causation.

Example: volume 1,000; market impressions 5,000, clicks 200, purchases 20; ASIN impressions 500, clicks 40, purchases 2. Market clicks/search = .20, market CTR = .04, ASIN CTR = .08; purchase-per-click = .10 market and .05 ASIN; relative index = .5. If reported click rate is .04, preserve it with the conflict note instead of relabeling it .20.

Peer P25/P50 requires an actual cohort, source, sample size, period and marketplace. Do not synthesize peer distributions from market totals or treat unlike products as peers. Missing peers do not block volume/click prioritization; omit peer claims. Attribution badges state the actual source scope and dates, not an invented universal “short window”.

## Theme comparisons

For multi-query analysis, use [theme-analysis.md](theme-analysis.md): sum raw counts over unique compatible members, recompute ratios, and compare disjoint cohorts. Theme confidence intervals are descriptive binomial approximations with explicit availability limits, not Amazon-provided metrics.
