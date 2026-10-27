# Evidence-conditioned ASIN findings

Use these rules for analysis and supporting records. Present the recommendation using the [seller-answer contract](decision-records.md); include a technical limitation in the main answer only when it changes the decision.

Use [theme analysis](theme-analysis.md) for recurring comparisons and [decision records](decision-records.md) for the action queue. A funnel observation selects where to look; it does not identify the cause. Retrieve available decisive evidence before returning a hold.

| Finding | When it can produce a concrete proposal |
|---|---|
| Recurring localized purchase-per-click gap | Inspect complete relevant listing fields. A specific supported omission/ambiguity may produce one `listing_content_test`; otherwise no edit or one-fact hold. Report uncertainty. |
| Listing contradicts a seller/user-confirmed variant specification | `product_fact_correction` with exact field and before/after, even with thin counts. Catalog disagreement alone yields a one-fact confirmation hold. |
| Low impression share or CTR | Descriptive finding; inspect actual search presentation if available. Do not convert an isolated ratio into a title/image rewrite. A proposal requires a verified information problem and bounded test with the relevant denominator. |
| Weak purchases plus independently verified ASIN delivery defect | A specific operations proposal requires ASIN delivery/availability evidence for the market/time and an actionable correction. Query-wide shipping totals cannot establish this. |
| High event-specific median price and weak purchases | A price test needs matching event/currency/period, comparable products, current offer and profitability constraints. SQP alone supplies none of the latter; return one decisive blocker instead of a generic price investigation. |
| Apparent variant underperformance | A mapping proposal requires actual family relationships and a specific mapping error. Underperformance is not evidence of cannibalization. |

Price, delivery and variant findings are secondary. Preserve legacy conditional diagnostic tags (`seo_update`, `pdp_update`, `price_test`, `shipping_speed_fix`, `variant_mapping_fix`) when appropriate, but a conditional tag is not an action. Only an evidenced defect with a concrete proposal enters the action queue. Do not fabricate peer cohorts or generate a list of possible explanations as the recommendation.

Route user-selected listing work to `amazon-sp-listing-optimizer`, price work to `amazon-sp-repricing`, and Ads work to `amazon-ads-sp-search-term-explorer` when available. If unavailable, provide the reviewable draft; do not claim execution.
