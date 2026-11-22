# Sponsored Products on v1

`adProduct`: `SPONSORED_PRODUCTS`. Product-scoped schemas: `spv1_SP*`. Read from the live server on 2026-11-19; when a field you need is not listed here, run `get_schema` on the `spv1_SP*` tool for that operation rather than inferring it from `allv1_*`.

## Capabilities

| Entity | Query | Create | Update | Delete (archives) |
|---|---|---|---|---|
| Campaign | yes | yes | yes | yes |
| Ad group | yes | yes | yes | yes |
| Ad (product ad) | yes | yes | creative (spotlight videos), state, tags | yes |
| Target | yes | yes | bid, state, tags | yes |

## Batch and page limits

| Operation | Campaigns | Ad groups | Ads | Targets |
|---|---|---|---|---|
| Create / update / delete per call | 1000 | 1000 | 1000 | 1000 |
| Query `maxResults` (max, default) | 1000 | 1000 | 1000 | 1000 |
| ID filter values per query | 1000 campaign IDs | 1000 ad group IDs, 100 campaign IDs | 100 each | 100 each |

The merged `allv1_QueryTarget` accepts `maxResults` up to 5000, but Amazon rejects anything above 1000 for SP with a 400 `BAD_REQUEST` (observed 2026-11-19). Send at most 1000.

## Campaign

**Create requires:** `adProduct`, `name`, `state` (`ENABLED` | `PAUSED`), `startDateTime`, `marketplaceScope` (`SINGLE_MARKETPLACE`), `autoCreationSettings.autoCreateTargets` (boolean), `budgets`.

- `budgets`: exactly one item: `budgetType: MONETARY`, `recurrenceTimePeriod: DAILY`, `budgetValue.monetaryBudgetValue.monetaryBudget.value` (number). Do not send a currency; the account's currency applies.
- `autoCreateTargets: true` is an auto-targeting campaign; `false` is manual. There is no `MANUAL`/`AUTO` enum.
- `optimizations.bidSettings.bidStrategy`: `MANUAL`, `RULE_BASED`, `SALES_DOWN_ONLY`, `SALES_UP_AND_DOWN`.
- `optimizations.bidSettings.bidAdjustments.placementBidAdjustments[]` (up to 4, each `placement` + `percentage`): placements `TOP_OF_SEARCH`, `REST_OF_SEARCH`, `PRODUCT_PAGE`, `SITE_AMAZON_BUSINESS`.
- Also available: `audienceBidAdjustments` (1), `creativeBidAdjustments` (up to 2, `SPOTLIGHT`, 0–900), `optimizations.budgetSettings.offAmazonBudgetControlStrategy` (`MAXIMIZE_REACH` | `MINIMIZE_SPEND`), `endDateTime`, `portfolioId`, `siteRestrictions` (`AMAZON_BUSINESS` | `AMAZON_HAUL`), `countries`/`marketplaces` (1 each), `tags` (up to 50 key/value).
- Not available on SP: `costType`, `goalSettings`.

**Update:** `campaignId` plus any of `budgets`, `name`, `state`, `startDateTime`, `endDateTime` (null clears), `portfolioId` (null clears), `optimizations`, `siteRestrictions`, `tags`.
**Immutable after create:** `autoCreationSettings` (auto vs manual), `marketplaceScope`, `countries`, `marketplaces`.

Array fields such as `placementBidAdjustments` and `tags` are most likely replaced, not merged. Send the full intended list: read the current list, apply the change, and send the result.

## Ad group

**Create requires:** `adProduct`, `campaignId`, `name`, `state`, `bid.defaultBid`.
Optional: `adSettings.productAttributeSetRefinementConfigurationId`, `tags`.
**Update:** `adGroupId` plus `bid.defaultBid`, `name`, `state`, `adSettings`, `tags`.

## Ad

`adType: PRODUCT_AD`. **Create requires:** `adGroupId`, `adProduct`, `adType`, `state`, `creative.productCreative.productCreativeSettings.advertisedProduct` with `productId` and `productIdType` (`ASIN` | `SKU`). Optional: `headline`, `spotlightVideos`.

The advertised ASIN or SKU cannot be updated. To change it, create a new ad and pause or archive the old one.

## Targets

**Create requires:** `adProduct`, `negative`, `state`, `targetType`, `targetDetails`, plus `adGroupId` (ad-group level) or `campaignId` alone (campaign level). Optional `bid.bid`, `tags`.

| What the user calls it | `targetType` | `targetDetails` |
|---|---|---|
| Keyword | `KEYWORD` | `keywordTarget {keyword, matchType: BROAD \| PHRASE \| EXACT}` |
| Negative keyword | `KEYWORD`, `negative: true` | `keywordTarget` with `EXACT` or `PHRASE` |
| ASIN target (product targeting) | `PRODUCT` | `productTarget {product.productId, productIdType: ASIN \| SKU, matchType: PRODUCT_EXACT \| PRODUCT_SIMILAR}` |
| Category target | `PRODUCT_CATEGORY` | `productCategoryTarget.productCategoryRefinement.productCategoryRefinement {productCategoryId, productBrandId, productPriceGreaterThan/LessThan, productRatingGreaterThan/LessThan, productPrimeShippingEligible, productAgeRangeId, productGenreId}` |
| Auto-targeting group | `THEME` | `themeTarget.matchType`: `KEYWORDS_CLOSE_MATCH` (close match), `KEYWORDS_LOOSE_MATCH` (loose match), `PRODUCT_SUBSTITUTES` (substitutes), `PRODUCT_COMPLEMENTS` (complements) |
| Other themes | `THEME` | `KEYWORDS_RELATED_TO_GIFTS`, `..._YOUR_BRAND`, `..._YOUR_PRODUCT_CATEGORY`, `..._PEER_BRANDS_PRODUCT_CATEGORY`, `..._PRIME_DAY` |
| Location | `LOCATION` | `locationTarget {locationId}` |

Note the double nesting for category refinements. `nativeLanguageKeyword` with `nativeLanguageLocale: zh_CN` is available for keywords.

The negative keyword match types `EXACT` and `PHRASE` are what SP accepts in practice; the schema lists all three keyword match types, so if the user asks for a broad negative, flag that SP has not historically supported it and let the API decide.

*Observed (2026-11-19):* a query for enabled `BROAD` keyword targets returns rows whose keyword is the literal `(_targeting_auto_)` with no bid. These are not shopper keywords. Leave them out of keyword lists, counts, and edits, and say you did.

**Update:** `targetId` plus `bid.bid` (null likely reverts to the ad group default bid; unverified), `state`, `tags`. Keyword text, match type, target type, and negative flag cannot be changed.

**Query selectors:**

| Want | Filters (always with `adProductFilter: {include: [SPONSORED_PRODUCTS]}`) |
|---|---|
| Keywords in an ad group | `negativeFilter [false]`, `targetTypeFilter [KEYWORD]`, `adGroupIdFilter` |
| Ad-group negative keywords | `negativeFilter [true]`, `targetTypeFilter [KEYWORD]`, `adGroupIdFilter` |
| Campaign negative keywords | `negativeFilter [true]`, `targetTypeFilter [KEYWORD]`, `campaignIdFilter`, then keep rows with `targetLevel: CAMPAIGN` (no level filter exists; campaign-level rows read back with no `adGroupId`) |
| Product and category targets | `targetTypeFilter [PRODUCT, PRODUCT_CATEGORY]` |
| Auto-targeting groups | `targetTypeFilter [THEME]` |
| A keyword by text | `keywordFilter {include: [...], queryTermMatchType: EXACT_MATCH \| BROAD_MATCH}` |
| An ASIN target | `productIdFilter {include: [...], queryTermMatchType}` |

`matchTypeFilter` accepts 14 values: `BROAD`, `EXACT`, `PHRASE`, `PRODUCT_EXACT`, `PRODUCT_SIMILAR`, `PRODUCT_COMPLEMENTS`, `PRODUCT_SUBSTITUTES`, `KEYWORDS_CLOSE_MATCH`, `KEYWORDS_LOOSE_MATCH`, and the five `KEYWORDS_RELATED_TO_*` themes.
