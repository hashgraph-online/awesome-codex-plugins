# Sponsored Brands Category Benchmark gap

*v3 Sponsored_Brands_Category_benchmark_report has no v1 equivalent (0 of 19 columns fully reproducible)*

Summary — this report is NOT REPRODUCIBLE in v1

**The Sponsored Brands Category Benchmark report is a competitive-intelligence report that compares an advertiser's performance against the bottom-25%, median, and top-25% peer performance within their brand and category. THIS REPORT IS NOT REPRODUCIBLE on the Amazon Ads API v1 cross-product reporting endpoint.**

Of the 19 v3 columns: 1 (Date) maps directly, 4 (Impressions, CTR, ACOS, ROAS) reproduce only your OWN performance — half of each peer comparison — and 14 are not reproducible at all. The two grouping dimensions (Brand, Category) and twelve peer-percentile metrics have no v1 equivalents.

There is no JSON request template for this report — there's no useful subset to query. This document exists to explain the gap and recommend recovery paths.

What the v1 catalog confirms is missing

Validator probes against the v1 catalog returned all of these as UNKNOWN:

-   brand.name, category.name, category.value (no advertiser-level brand or category dimensions)

-   metric.peerImpressions, metric.peerImpressionsTop25, metric.peerImpressionsMedian, metric.peerImpressionsBottom25

-   metric.peerCtr (and any percentile variant)

-   metric.peerAcos (and any percentile variant)

-   metric.peerRoas (and any percentile variant)

Catalog searches for 'peer', 'benchmark', 'percentile' all return zero results. This is not a naming-mismatch issue — competitive benchmarking metrics are simply not exposed in the v1 reporting catalog as of catalog parse 2026-04-18.

The brand and category fields that DO exist in v1 (convertedProduct.brand, convertedProduct.category, convertedProduct.subcategory) are conversion-attribute dimensions: the brand and category of the purchased product, not the advertiser's brand or competitive category. They cannot reproduce the v3 grouping — there is no version of the v3 report that produces meaningful rows when grouped by purchased-product attributes instead of advertiser attributes.

v3 column status

| **v3 Column (Sponsored_Brands_Category_benchmark)** | **v1 field_id**      | **Role**       | **Notes**                                                                                                                                                                                                                              |
|-----------------------------------------------------|----------------------|----------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Date                                                | date.value           | Time dimension | Required time dimension.                                                                                                                                                                                                               |
| Brand                                               | (NOT REPRODUCIBLE)   | —              | v1 has no advertiser-level brand dimension. Validator-confirmed unknown for brand.name. The closest field is convertedProduct.brand, which is the brand of the PURCHASED product (a conversion attribute), not the advertiser's brand. |
| Category                                            | (NOT REPRODUCIBLE)   | —              | v1 has no advertiser-level category dimension. Validator-confirmed unknown for category.name and category.value. Only convertedProduct.category exists, which is the category of the PURCHASED product.                                |
| Impressions                                         | metric.impressions   | Metric         | Direct — but only your own impressions, not your peers'.                                                                                                                                                                               |
| Peer impressions - bottom 25%                       | (NOT REPRODUCIBLE)   | —              | v1 has no peer/benchmark/percentile/quartile metrics for advertiser comparisons. Validator-confirmed unknown for metric.peerImpressions, metric.peerImpressionsBottom25, metric.peerImpressionsMedian, metric.peerImpressionsTop25.    |
| Peer impressions - median                           | (NOT REPRODUCIBLE)   | —              | Same as above.                                                                                                                                                                                                                         |
| Peer impressions - top 25%                          | (NOT REPRODUCIBLE)   | —              | Same as above.                                                                                                                                                                                                                         |
| Click-Thru Rate (CTR)                               | metric.ctr           | Metric         | Direct — but only your own CTR.                                                                                                                                                                                                        |
| Peer CTR - bottom 25%                               | (NOT REPRODUCIBLE)   | —              | v1 has no peer CTR percentiles. Validator-confirmed unknown for metric.peerCtr.                                                                                                                                                        |
| Peer CTR - median                                   | (NOT REPRODUCIBLE)   | —              | Same as above.                                                                                                                                                                                                                         |
| Peer CTR - top 25%                                  | (NOT REPRODUCIBLE)   | —              | Same as above.                                                                                                                                                                                                                         |
| Total ACoS                                          | (derive client-side) | Derived        | totalCost / NULLIF(sales, 0). But this only computes your own ACOS, not the peer comparison.                                                                                                                                           |
| Peer ACOS - top 25%                                 | (NOT REPRODUCIBLE)   | —              | v1 has no peer ACOS percentiles. Validator-confirmed unknown for metric.peerAcos.                                                                                                                                                      |
| Peer ACOS - median                                  | (NOT REPRODUCIBLE)   | —              | Same as above.                                                                                                                                                                                                                         |
| Peer ACOS - bottom 25%                              | (NOT REPRODUCIBLE)   | —              | Same as above.                                                                                                                                                                                                                         |
| Total RoAS                                          | metric.roas          | Metric         | Direct — but only your own ROAS.                                                                                                                                                                                                       |
| Peer ROAS - bottom 25%                              | (NOT REPRODUCIBLE)   | —              | v1 has no peer ROAS percentiles. Validator-confirmed unknown for metric.peerRoas.                                                                                                                                                      |
| Peer ROAS - median                                  | (NOT REPRODUCIBLE)   | —              | Same as above.                                                                                                                                                                                                                         |
| Peer ROAS - top 25%                                 | (NOT REPRODUCIBLE)   | —              | Same as above.                                                                                                                                                                                                                         |

*Red rows are NOT REPRODUCIBLE. Only Date, Impressions, CTR, and ROAS reproduce, and even those expose only the advertiser's own performance — without the peer percentiles, the report's central use case (knowing whether you're top-quartile or bottom-quartile vs peers) cannot be answered.*

Why this report is structurally different from the others in this series

Every other v3 SP/SB report measures a single advertiser's first-party performance. The Category Benchmark report is fundamentally a SECOND-PARTY DATA report — it requires Amazon to aggregate other advertisers' performance into bottom-25% / median / top-25% buckets and serve them back. That second-party aggregation pipeline is what's not exposed via v1's general-purpose reporting endpoint. It might exist as a dedicated benchmarking endpoint or as part of Amazon's Brand Metrics / Brand Health offerings, but those are separate APIs from the Ads v1 reporting catalog.

Recommended recovery paths

-   Continue using the v3 Sponsored Brands Category Benchmark report endpoint until/unless an equivalent appears in v1.

-   Investigate Amazon Brand Analytics — the Brand Health and Top Search Terms dashboards in Seller Central / Vendor Central include peer-percentile views similar in spirit to the Category Benchmark report. Different access path (no API for some of these — UI-only) but covers the same competitive-intelligence use case.

-   Investigate Amazon Marketing Cloud (AMC) — AMC instances can sometimes be subscribed to peer-aggregate insights in the form of Insights Reports. Check whether your AMC instance has access to category-benchmark insights datasets.

-   If the v3 endpoint is being deprecated and no replacement is announced, surface this as a feedback item to your Amazon Ads account team — peer-benchmark reporting is a flagship SB feature and a v1 omission is likely a known gap on Amazon's roadmap.

What this means for ETL design

Do not attempt to build this report on the v1 endpoint. There is no field combination that will produce the v3 output — the validator will accept syntactically valid alternative requests, but they will return either single-advertiser metrics (no peer comparison) or empty/zero rows (when grouping by convertedProduct.brand on a campaign that hasn't converted yet). Both outcomes are misleading downstream consumers who expect peer-percentile shape.

If you have a downstream consumer that depends on this report's columns, the recommendation is to keep the v3 ingest path live, or to flag the consumer that competitive benchmarking is a v1 gap and may need a different upstream source.
