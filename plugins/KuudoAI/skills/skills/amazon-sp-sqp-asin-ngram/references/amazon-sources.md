# Amazon sources and analytical boundaries

Use these rules for analysis and supporting records. Present the recommendation using the [seller-answer contract](decision-records.md); include a technical limitation in the main answer only when it changes the decision.

Sources inspected 2026-10-20. Read this ledger when explaining provenance or resolving conflicting definitions. Local rules distinguish **Amazon definitions**, **research findings**, and **analyst methods**; the latter are not Amazon recommendations.

| Source | Supported use | Limits |
|---|---|---|
| [SP-API Analytics Reports — Search Query Performance](https://developer-docs.amazon/sp-api/docs/report-type-values-analytics#search-query-performance-report) | Amazon definition: report type, access and request periods | Not an SEO action rulebook |
| [SQP schema, revision c4bf4ff](https://github.com/amzn/selling-partner-api-models/blob/c4bf4ff151a26aae53712143560071c6c18285a2/schemas/reports/sellingPartnerSearchQueryPerformanceReport.json) | Amazon definitions: counts, fractions, scope, event-specific prices, request metadata | Rate descriptions conflict with example arithmetic; preserve that uncertainty |
| [ESCI paper, §1, page 1](https://arxiv.org/pdf/2206.06588v1) | Research definitions: exact, substitute, complement, irrelevant query–product relations | Labels assigned here are analyst/model judgments, not Amazon-provided labels |
| [ESCI dataset, revision 7916cdf](https://github.com/amazon-science/esci-data/tree/7916cdf6ab75a462e77f20ab40428a10923998d5) and [license](https://github.com/amazon-science/esci-data/blob/7916cdf6ab75a462e77f20ab40428a10923998d5/LICENSE) | Optional semantic-matching benchmark; Apache-2.0 data repository | Does not supply seller SQP metrics or validate prioritization thresholds |
| [COSMO paper](https://cdn.amazon.science/19/5d/bde30d0d4019be6421e79e50cda9/cosmo-paper.pdf), Table 2, §3.3, §4 and first-page footnote | Research findings: relations, filtering of intent hypotheses, evaluation and deployment scope | Reported deployment specifically targets search navigation; no seller ranking recipe |
| [Amazon Science explanation](https://www.amazon.science/blog/building-commonsense-knowledge-graphs-to-aid-product-recommendation) | Accessible account of behavior-derived hypotheses and quality filtering | Offline F1 improvement is not seller sales or organic-rank lift |

Full Git revisions: schema `c4bf4ff151a26aae53712143560071c6c18285a2`; dataset `7916cdf6ab75a462e77f20ab40428a10923998d5`. These pins make the reviewed claims reproducible; inspect updates before changing their interpretation. No dataset or upstream code is bundled here.

## Known rate conflict

The schema's rate descriptions name query volume as the denominator. Its example has 15,000 searches, 10,000 impressions, 1,000 clicks and reported click rate 0.1; the example's arithmetic matches impressions. Cart-add and purchase examples have the same discrepancy. Do not silently “repair” a source value or suppress all rows. Display reported rates unchanged with the discrepancy noted. Calculate independent ratios from counts, with explicit numerator and denominator; never feed a reported rate into a derived calculation.

## Our methods

The evidence acquisition workflow, `unknown` relevance state, sufficiency defaults, priority groups, n-gram aggregation and diagnostic tests are analyst methods inspired by the sources. They are not reproductions of Amazon models. COSMO's filtered explanations motivate checking hypotheses, not treating generated use cases as product facts. The papers do not validate seller copy placement, our thresholds, or a causal inference from share changes.
