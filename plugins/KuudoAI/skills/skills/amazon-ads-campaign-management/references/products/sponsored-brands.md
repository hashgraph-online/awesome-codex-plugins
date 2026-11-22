# Sponsored Brands on v1

`adProduct`: `SPONSORED_BRANDS`. Product-scoped schemas: `sbv1_SB*`. Read from the live server on 2026-11-19; when a field you need is not listed here, run `get_schema` on the `sbv1_SB*` tool for that operation.

## Capabilities

| Entity | Query | Create | Update | Delete (archives) |
|---|---|---|---|---|
| Campaign | yes | yes | yes | yes |
| Ad group | yes | yes | name, state, tags | yes |
| Ad (creative) | yes | yes | creative, name, state, tags | yes |
| Target | yes | yes (ad group only) | bid, state | yes |

## Batch and page limits

SB limits are small. Chunk every request.

| Operation | Campaigns | Ad groups | Ads | Targets |
|---|---|---|---|---|
| Create / update / delete per call | **10** | **10** | **10** | 1000 |
| Query `maxResults` (max, default) | 100 | 100 | 100 | 5000 |
| ID filter values per query | **10** campaign IDs, **10** portfolio IDs | 100 | **10** each | 100 each; `keywordFilter` **2** values |

## Campaign

**Create requires:** `adProduct`, `name`, `state` (`ENABLED` | `PAUSED`), `startDateTime`, `marketplaceScope` (`SINGLE_MARKETPLACE`), `budgets`, `costType`.

- `budgets`: exactly one: `budgetType: MONETARY`, `recurrenceTimePeriod: DAILY | LIFETIME`, `budgetValue.monetaryBudgetValue.monetaryBudget.value`. No currency.
- `costType`: `CPC`, `VCPM`, `CPM`, `FIXED_PRICE`. **Required and immutable.** Never default it: ask the user. Legacy SB campaigns were almost always CPC; vCPM is for reach-oriented campaigns.
- `optimizations.goalSettings.kpi`: `CLICKS` | `TOP_OF_SEARCH_IMPRESSION_SHARE`. **Immutable after create.**
- `optimizations.bidSettings.bidStrategy`: `MANUAL` | `SALES_UP_AND_DOWN`.
- `placementBidAdjustments[]` (up to 4): `TOP_OF_SEARCH`, `REST_OF_SEARCH`, `PRODUCT_PAGE`, `HOME_PAGE`. Not supported with `SALES_UP_AND_DOWN`.
- `audienceBidAdjustments` (1); `shopperSegmentBidAdjustments` (2, legacy and marked for deprecation; don't add new ones).
- Optional: `endDateTime`, `portfolioId`, `brandId`, `salesChannel` (`AMAZON` | `OFF_AMAZON`), `siteRestrictions` (`AMAZON_BUSINESS`), `targetedPGDealId`, `autoCreationSettings.autoCreateTargets`, `countries`/`marketplaces` (1 each), `tags` (50).

**Update:** `campaignId` plus `budgets`, `name`, `state`, `startDateTime`, `endDateTime`, `portfolioId`, `optimizations.bidSettings` (strategy and adjustments), `tags`, `targetedPGDealId`.
**Immutable:** `costType`, `goalSettings`, `brandId`, `salesChannel`, `autoCreationSettings`, `siteRestrictions`, `marketplaceScope`. A different cost type or goal means a new campaign.

## Ad group

**Create requires:** `adProduct`, `campaignId`, `name`, `state`. Optional `tags`. **SB ad groups have no bid.** Bids live on targets.

## Ad

`adType: COMPONENT`. **Create requires:** `adGroupId`, `adProduct`, `adType`, `name`, `state`, and `creative.componentCreative` with exactly one of:

| Format (legacy name) | Settings key | Core requirements |
|---|---|---|
| Product collection | `productCollectionSettings` | `brand`, `brandLogos` (1–2), `headlines` (1), `landingPage` (`ASIN_LIST` / `CUSTOM_URL` / `STORE`), up to 3 `products`; optional `customImages` (1–5) |
| Video | `productVideoSettings` | `videos` (1), `landingPage` (`DETAIL_PAGE` / `STORE`), up to 3 `products` |
| Store spotlight | `storeSpotlightSettings` | exactly 3 `cards`, `brand`, `brandLogos` (1), `headlines` (1), `landingPage: STORE` |
| Brand gallery | `brandGallerySettings` | 3–5 `cards`, brand, logo, headline, store landing page |
| Auto collection | `autoCollectionSettings` | `sharedSettings {brand, brandLogos}`, optional `productExclusions` |
| Manual collection | `manualCollectionSettings` | 3–10 `productInclusions`, `landingPage`, `sharedSettings`, `title` |

Creative assets (logos, images, videos) are asset IDs. Creating or uploading them is outside this skill; use `amazon-ads-creative-assets` when available.

## Targets

**Create requires:** `adProduct`, `adGroupId`, `negative`, `state`, `targetType`, `targetDetails`. `bid.bid` is required whenever `bid` is sent.

**SB has no campaign-level targets in v1:** every target, including negatives, belongs to an ad group. A legacy campaign-level SB negative must be recreated in each ad group; tell the user how many targets that produces.

| What the user calls it | `targetType` | `targetDetails` |
|---|---|---|
| Keyword | `KEYWORD` | `keywordTarget {keyword, matchType: BROAD \| PHRASE \| EXACT}` |
| Negative keyword | `KEYWORD`, `negative: true` | `keywordTarget` (`EXACT` or `PHRASE`) |
| ASIN target | `PRODUCT` | `productTarget {product.productId, productIdType: ASIN, matchType: PRODUCT_EXACT}` (only these values) |
| Category or brand target | `PRODUCT_CATEGORY` | `productCategoryTarget.productCategoryRefinement.productCategoryRefinement {productCategoryId, productBrandId, productPriceGreaterThan/LessThan, productRatingGreaterThan/LessThan}` |
| Theme | `THEME` | `themeTarget.matchType`: `KEYWORDS_RELATED_TO_YOUR_BRAND` \| `KEYWORDS_RELATED_TO_YOUR_LANDING_PAGES` |

Legacy SB "expressions" translate as: `asinSameAs` → `PRODUCT` target; `asinCategorySameAs` → `productCategoryId`; `asinBrandSameAs` → `productBrandId`; `asinPriceLessThan`/`GreaterThan` → `productPriceLessThan`/`GreaterThan`; `asinPriceBetween` → both price bounds; `asinReviewRating*` → `productRatingLessThan`/`GreaterThan` (both for a range).

**Update:** `targetId` plus `bid.bid` and `state`. No tags on SB targets.

**Query selectors:** same as SP (`negativeFilter`, `targetTypeFilter`, `adGroupIdFilter`, `campaignIdFilter`, `keywordFilter`), with `matchTypeFilter` limited to `BROAD`, `EXACT`, `PHRASE`, `PRODUCT_EXACT`, `KEYWORDS_RELATED_TO_YOUR_BRAND`, `KEYWORDS_RELATED_TO_YOUR_LANDING_PAGES`. `keywordFilter.include` takes at most 2 values, so look up more keywords by ad group and filter client-side.

## Migrating legacy SB campaigns

The server exposes Amazon's own SB v3 migration job tools (`sb_StartMigrationJob`, `sb_MigrationJobStatus`, `sb_MigrationJobResults`, `sb_MigrationResults`). Starting a migration job is a write that changes campaigns: preview it like any other write, and read results before reporting success.
