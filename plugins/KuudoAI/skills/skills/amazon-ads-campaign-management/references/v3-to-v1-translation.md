# Translating legacy campaign-management calls to v1

Use this when someone has a legacy request, response handler, or client code (SP v3 `/sp/…`, SB `/sb/…` and `/sb/v4/…`, SD `/sd/…`, DSP `/dsp/…`) and wants the v1 equivalent. v1 targets come from the live product-scoped schemas (2026-11-19). Rows marked **verify** are logical mappings not yet confirmed against a live write: say so when you use them, and confirm with `get_schema` on the product-scoped tool.

## Contents

- [Answering a translation request](#answering-a-translation-request)
- [Endpoint map](#endpoint-map)
- [Campaign fields](#campaign-fields)
- [Ad group and ad fields](#ad-group-and-ad-fields)
- [Keyword and target fields](#keyword-and-target-fields)
- [List-call fields](#list-call-fields)
- [Migrating client code](#migrating-client-code)

## Answering a translation request

1. Identify the exact legacy method and path. "Move our SP integration" is not enough: ask which calls the client makes.
2. Map the endpoint, then each field, from the tables below and the product reference.
3. Add every v1 field the legacy request never carried: `adProduct` / `adProductFilter` always; product-required fields such as SP `marketplaceScope`, `startDateTime`, `autoCreationSettings`, and SB/SD `costType`. An SB `costType` has no safe default: ask.
4. Add the selecting filters that pick the resource on a shared endpoint (for example `negativeFilter` and `targetTypeFilter` on the targets endpoint). Omitting a required field fails with 400; omitting a selector succeeds and returns the wrong rows.
5. List every legacy field with no v1 counterpart as a blocker, and every value that changes form (enum renames, structure changes) as something to verify.
6. Return the v1 request as `execute` code or JSON arguments for the `allv1_*` tool.

## Endpoint map

| Legacy call (SP v3 shown; SB, SD, DSP follow the same resource) | v1 tool | Selecting fields |
|---|---|---|
| `POST /sp/campaigns`, `PUT /sp/campaigns`, `POST /sp/campaigns/list`, `POST /sp/campaigns/delete` | `allv1_CreateCampaign`, `allv1_UpdateCampaign`, `allv1_QueryCampaign`, `allv1_DeleteCampaign`; creates and budget updates use the product-scoped `spv1_SPCreateCampaign` / `spv1_SPUpdateCampaign` (same endpoint) | `adProduct` / `adProductFilter` |
| `…/adGroups…` | `allv1_*AdGroup` | same |
| `…/productAds…` (SP), `/sb/v4/ads/…`, `/sd/productAds` | `allv1_*Ad` | same |
| `…/keywords…` | `allv1_*Target` | `targetType: KEYWORD`, `negative: false` |
| `…/negativeKeywords…` | `allv1_*Target` | `targetType: KEYWORD`, `negative: true`, with `adGroupId` |
| `…/campaignNegativeKeywords…` | `allv1_*Target` | `targetType: KEYWORD`, `negative: true`, `campaignId` only; read back as `targetLevel: CAMPAIGN` |
| `…/targets…` (product, category, auto) | `allv1_*Target` | `targetType: PRODUCT`, `PRODUCT_CATEGORY`, or `THEME` |
| `…/negativeTargets…`, `…/campaignNegativeTargets…` | `allv1_*Target` | `targetType: PRODUCT` or `PRODUCT_CATEGORY`, `negative: true`, at the matching level |
| `/sb/themes…` | `allv1_*Target` | `targetType: THEME` |
| `/dsp/…/adCreatives/associations/adGroups` | `allv1_*AdAssociation` | none |
| Portfolios (`/portfolios`, `/v2/portfolios`) | **No v1 counterpart** | blocker |
| SB v3 campaign migration | `sb_StartMigrationJob` and the related `sb_Migration*` tools | Amazon's own migration job; it's a write |

Legacy `DELETE` (or `…/delete`) archived the entity. v1 delete does the same, irreversibly. Legacy updates that set `state: ARCHIVED` become a v1 delete.

Sponsored Brands has no campaign-level targets in v1. A legacy SB campaign-level negative becomes one negative per ad group.

## Campaign fields

| Legacy (SP v3) | v1 | Note |
|---|---|---|
| `campaignId` | `campaignId` | direct |
| `name` | `name` | direct |
| `state` (`ENABLED`, `PAUSED`, `ARCHIVED`) | `state` (`ENABLED`, `PAUSED`); archive = delete | `ARCHIVED` cannot be written |
| `targetingType: AUTO` / `MANUAL` | `autoCreationSettings.autoCreateTargets: true` / `false` | immutable after create |
| `budget.budget` | `budgets[0].budgetValue.monetaryBudgetValue.monetaryBudget.value` | direct value |
| `budget.budgetType: DAILY` | `budgets[0].budgetType: MONETARY` **and** `recurrenceTimePeriod: DAILY` | `DAILY` is not a `budgetType` in v1 |
| `startDate` / `endDate` (`YYYY-MM-DD`) | `startDateTime` / `endDateTime` (ISO date-time) | `startDateTime` is required on create even when legacy omitted it ("start today") |
| `portfolioId` | `portfolioId` | direct; null clears |
| `dynamicBidding.strategy: LEGACY_FOR_SALES` | `optimizations.bidSettings.bidStrategy: SALES_DOWN_ONLY` | verify |
| `dynamicBidding.strategy: AUTO_FOR_SALES` | `bidStrategy: SALES_UP_AND_DOWN` | verify |
| `dynamicBidding.strategy: MANUAL` / `RULE_BASED` | `MANUAL` / `RULE_BASED` | direct |
| `dynamicBidding.placementBidding[]` | `optimizations.bidSettings.bidAdjustments.placementBidAdjustments[]` | container |
| `placement: PLACEMENT_TOP` | `placement: TOP_OF_SEARCH` | enum renamed |
| `placement: PLACEMENT_PRODUCT_PAGE` | `PRODUCT_PAGE` | enum renamed |
| `placement: PLACEMENT_REST_OF_SEARCH` | `REST_OF_SEARCH` | enum renamed |
| `percentage` | `percentage` | direct |
| `tags` (object of key → value) | `tags` (list of `{key, value}`) | reshaped |
| `servingStatus`, `extendedData.*` | `status.deliveryStatus`, `status.deliveryReasons`, `creationDateTime`, `lastUpdatedDateTime` (read only) | response side; no request counterpart |
| — | `adProduct`, `marketplaceScope: SINGLE_MARKETPLACE` | required in v1 with no legacy source |

SB: legacy `budgetType: DAILY | LIFETIME` → `recurrenceTimePeriod`; `bidOptimization`/`bidding` → `optimizations.bidSettings`; `goal` → `optimizations.goalSettings.kpi`; `costType` → `costType` (required, immutable). SD: `budget` → the SD budget shape (no recurrence); `costType` → `costType`; `tactic` has no campaign field (audience and product targeting moved to targets; **verify** per tactic).

DSP: legacy campaign `startDateTime`/`endDateTime`/budget move into `flights[]`; campaigns and ad groups are created `PAUSED`.

## Ad group and ad fields

| Legacy | v1 | Note |
|---|---|---|
| `adGroupId`, `campaignId`, `name`, `state` | same names | `state` as above |
| SP `defaultBid` | `bid.defaultBid` | SB ad groups have no bid |
| SP product ad `asin` | `creative.productCreative.productCreativeSettings.advertisedProduct {productId, productIdType: ASIN}` | immutable after create |
| SP product ad `sku` | `advertisedProduct {productId, productIdType: SKU}` | sellers use SKU, vendors ASIN |
| — | `adType: PRODUCT_AD` (SP), `COMPONENT` (SB, SD), `VIDEO` (ST) | required, no legacy source |
| SB v4 ad `creative` by ad type (product collection, video, store spotlight, brand video) | `creative.componentCreative.<format>Settings` | see the SB reference |

## Keyword and target fields

| Legacy | v1 | Note |
|---|---|---|
| `keywordId` | `targetId` | direct |
| `keywordText` | `targetDetails.keywordTarget.keyword` | immutable |
| `matchType: BROAD` / `PHRASE` / `EXACT` | `keywordTarget.matchType` same value | immutable |
| `matchType: NEGATIVE_EXACT` / `NEGATIVE_PHRASE` | `keywordTarget.matchType: EXACT` / `PHRASE` with `negative: true` | enum renamed; the negative flag carries the meaning |
| `bid` | `bid.bid` | none on ST or DSP |
| `expression[{type: ASIN_SAME_AS, value}]` | `targetType: PRODUCT`, `productTarget {product.productId, productIdType: ASIN, matchType: PRODUCT_EXACT}` | |
| `ASIN_EXPANDED_FROM` | `productTarget.matchType: PRODUCT_SIMILAR` | verify |
| `ASIN_CATEGORY_SAME_AS` | `targetType: PRODUCT_CATEGORY`, `…productCategoryRefinement.productCategoryRefinement.productCategoryId` | double-nested |
| `ASIN_BRAND_SAME_AS` | `…productCategoryRefinement.productBrandId` | |
| `ASIN_PRICE_LESS_THAN` / `GREATER_THAN` / `BETWEEN` | `productPriceLessThan` / `productPriceGreaterThan` / both | `BETWEEN` splits into two fields |
| `ASIN_REVIEW_RATING_*` | `productRatingLessThan` / `productRatingGreaterThan` / both | |
| `ASIN_IS_PRIME_SHIPPING_ELIGIBLE` | `productPrimeShippingEligible` | |
| `ASIN_AGE_RANGE_SAME_AS`, `ASIN_GENRE_SAME_AS` | `productAgeRangeId`, `productGenreId` | |
| Auto `QUERY_HIGH_REL_MATCHES` | `targetType: THEME`, `themeTarget.matchType: KEYWORDS_CLOSE_MATCH` | |
| Auto `QUERY_BROAD_REL_MATCHES` | `KEYWORDS_LOOSE_MATCH` | |
| Auto `ASIN_SUBSTITUTE_RELATED` | `PRODUCT_SUBSTITUTES` | |
| Auto `ASIN_ACCESSORY_RELATED` | `PRODUCT_COMPLEMENTS` | |
| `expressionType: AUTO` / `MANUAL` | implied by `targetType` (`THEME` vs `PRODUCT`/`PRODUCT_CATEGORY`) | no field |

SB legacy camelCase expressions (`asinSameAs`, `asinCategorySameAs`, …) map the same way; see the SB reference.

## List-call fields

| Legacy | v1 | Note |
|---|---|---|
| — | `adProductFilter {include: [<one product>]}` | required |
| `campaignIdFilter`, `adGroupIdFilter` | same name | product-specific size limits |
| `keywordIdFilter`, `targetIdFilter` | `targetIdFilter` | |
| `stateFilter` | `stateFilter` | values `ENABLED`, `PAUSED`, `ARCHIVED` |
| `nameFilter`, `keywordTextFilter` | `nameFilter` / `keywordFilter {include, queryTermMatchType}` | |
| `matchTypeFilter` (`NEGATIVE_EXACT`…) | `matchTypeFilter` with v1 values plus `negativeFilter` | |
| `maxResults` | `maxResults` | SP ≤1000, others lower; legacy 5000 is rejected |
| `nextToken` | `nextToken` | direct |
| `includeExtendedDataFields` | none; delivery status and timestamps always return | |
| `portfolioIdFilter` | `portfolioIdFilter` (SP, SB, SD campaigns) | |

## Migrating client code

Make the v1 path additive. Keep the working legacy path, add v1 beside it in the layer that already varies by API, and switch between them where the code already chooses endpoints or versions, so the change can be rolled back by configuration. Match the codebase's existing conventions for models, configuration, and tests. For each translated call, test the request body against the product-scoped schema, test the `adProductFilter` and selector fields explicitly, and test the per-item error path. Remove the legacy path only as a separate decision after the v1 path has run in production. Everything generated needs human review before it ships.
