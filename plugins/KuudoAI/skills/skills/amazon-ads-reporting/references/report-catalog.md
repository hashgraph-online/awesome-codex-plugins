# Amazon Ads unified/v1 report catalog

Use this index when a user names a familiar legacy v3 Sponsored Products (SP), Sponsored Brands (SB), or Sponsored Display (SD) report. Match both the ad product and report family. If multiple rows match the wording, list them and ask the user to choose.

The catalog covers 17 reproducible report families and documents one non-reproducible family. Template paths are relative to the skill root. Read the linked mapping reference before returning a body.

## Sponsored Products

| Legacy report | Primary template | Mapping and caveats | Additional requests |
|---|---|---|---|
| SP Campaign | `assets/templates/sp/campaign.json` | `references/reports/sp/campaign.md` | Wrapper; use `assets/templates/sp/campaign__main.json` and optional `assets/templates/sp/campaign__prior_year.json` for year-over-year |
| SP Audience | `assets/templates/sp/audience.json` | `references/reports/sp/audience.md` | None |
| SP Purchased Product | `assets/templates/sp/purchased_product.json` | `references/reports/sp/purchased_product.md` | None |
| SP Targeting | `assets/templates/sp/targeting.json` | `references/reports/sp/targeting.md` | Wrapper; submit `assets/templates/sp/targeting__main.json` and `assets/templates/sp/targeting__top_of_search.json` separately |
| SP Video | `assets/templates/sp/video.json` | `references/reports/sp/video.md` | None |

## Sponsored Brands

| Legacy report | Primary template | Mapping and caveats | Additional requests |
|---|---|---|---|
| SB Campaign | `assets/templates/sb/campaign.json` | `references/reports/sb/campaign.md` | None |
| SB Campaign Placement | `assets/templates/sb/campaign_placement.json` | `references/reports/sb/campaign_placement.md` | None |
| SB Keyword | `assets/templates/sb/keyword.json` | `references/reports/sb/keyword.md` | Wrapper; submit `assets/templates/sb/keyword__main.json` and `assets/templates/sb/keyword__top_of_search.json` separately |
| SB Keyword Placement | `assets/templates/sb/keyword_placement.json` | `references/reports/sb/keyword_placement.md` | None |
| SB Search Term | `assets/templates/sb/search_term.json` | `references/reports/sb/search_term.md` | None |
| SB Search Term Impression Share | `assets/templates/sb/search_term_impression_share.json` | `references/reports/sb/search_term_impression_share.md` | None |
| SB Attributed Purchases | `assets/templates/sb/attributed_purchases.json` | `references/reports/sb/attributed_purchases.md` | None |
| SB Prompts | `assets/templates/sb/prompts.json` | `references/reports/sb/prompts.md` | None |
| SB Category Benchmark | **NOT REPRODUCIBLE** | `references/reports/sb/category_benchmark.md` | Return the documented alternatives; no CreateReport body |

## Sponsored Display

| Legacy report | Primary template | Mapping and caveats | Additional requests |
|---|---|---|---|
| SD Campaign | `assets/templates/sd/campaign.json` | `references/reports/sd/campaign.md` | None |
| SD Advertised Product | `assets/templates/sd/advertised_product.json` | `references/reports/sd/advertised_product.md` | None |
| SD Targeting | `assets/templates/sd/targeting.json` | `references/reports/sd/targeting.md` | None |
| SD Matched Target | `assets/templates/sd/matched_target.json` | `references/reports/sd/matched_target.md` | None |

## Split-report joins

| Report | Reason | Join |
|---|---|---|
| SP Campaign year-over-year | Current and prior-year periods are separate requests | Align the shifted reporting date and join on campaign ID; confirm leap-day behavior |
| SP Targeting with top-of-search impression share | Targeting and impression-share fields use different compatible grains | Join the campaign-grain result to the main result on reporting date and campaign ID; do not sum the repeated share metric |
| SB Keyword with top-of-search impression share | Keyword and impression-share fields use different compatible grains | Join the campaign-grain result to the main result on reporting date and campaign ID; do not sum the repeated share metric |

Each wrapper file has a documentation-only `_comment` plus named CreateReport bodies. The wrapper is not submittable. Extract each named body or use the pre-split files listed above.

## No catalog match

If the user names a different report, state that this package has no validated mapping. If the user instead describes a custom grain and metrics, use [ad-hoc reporting](ad-hoc-reporting.md). Do not infer that an unfamiliar report is equivalent to the nearest catalog row.
