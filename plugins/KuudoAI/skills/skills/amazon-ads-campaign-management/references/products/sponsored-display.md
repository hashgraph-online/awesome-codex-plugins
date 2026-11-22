# Sponsored Display on v1

`adProduct`: `SPONSORED_DISPLAY`. Product-scoped schemas: `sdv1_SD*`. Read from the live server on 2026-11-19; when a field you need is not listed here, run `get_schema` on the `sdv1_SD*` tool for that operation.

## Capabilities

| Entity | Query | Create | Update | Delete (archives) |
|---|---|---|---|---|
| Campaign | yes | yes | yes, including `costType` | yes |
| Ad group | yes | yes | bid, name, kpi, state | yes |
| Ad (creative) | yes, **no ID filters** | yes | creative, state | yes |
| Target | yes, **no negative or type filters** | yes | bid, state | yes |

## Batch and page limits

| Operation | Campaigns | Ad groups | Ads | Targets |
|---|---|---|---|---|
| Create / update / delete per call | 100 | 100 | 100 | 1000 |
| Query `maxResults` (max) | 100 | 100 | 100 | 5000 |

## Query gaps

- **Ads:** the SD query accepts only `adProductFilter`, `maxResults`, `nextToken`. Page through all SD ads and filter by `adGroupId` client-side. Say so when the account is large.
- **Targets:** no `negativeFilter` or `targetTypeFilter`. Filter by `adGroupIdFilter`, `campaignIdFilter`, or `targetIdFilter`, then split negatives and types client-side from each row's `negative` and `targetType`. Don't send the SP selectors for SD: Amazon rejects them (`negativeFilter` returned 400 `FIELD_VALUE_IS_INVALID`, "Negative filter size is invalid, Expected: 0", observed 2026-11-19).

## Campaign

**Create requires:** `adProduct`, `name`, `state` (`ENABLED` | `PAUSED`), `startDateTime`, `marketplaceScope` (`SINGLE_MARKETPLACE`), `budgets`, `costType` (`CPC` | `VCPM`).

- `budgets`: exactly one: `budgetType: MONETARY`, `budgetValue.monetaryBudgetValue.monetaryBudget.value`. The SD schema has **no `recurrenceTimePeriod`** and no currency, while the merged `allv1_*` budget item requires both, so `allv1_CreateCampaign` / `allv1_UpdateCampaign` reject a correct SD budget at MCP validation. Send SD campaign creates and budget updates through `sdv1_SDCreateCampaign` / `sdv1_SDUpdateCampaign` (same endpoint, SD contract). Never add a recurrence or currency to get past the merged schema.
- No `optimizations` object: SD campaigns have no bid strategy or placement adjustments.
- Optional: `endDateTime`, `portfolioId`, `countries`/`marketplaces` (1 each; 21 markets, no IE or ZA), `tags` (50).

**Update:** `campaignId` plus `budgets`, `costType`, `name`, `state`, `startDateTime`, `endDateTime`, `portfolioId`, `tags`. Changing `costType` on a live campaign changes how it is charged; call that out in the preview.

## Ad group

**Create requires:** `adProduct`, `campaignId`, `name`, `state`, `marketplaceScope` (`SINGLE_MARKETPLACE`), `marketplaces` (exactly one, the same as or within the campaign's).
Optional: `bid.defaultBid`, `creativeType` (`IMAGE` | `VIDEO`), `optimization.goalSettings.kpi` (`CLICKS`, `PAGE_VIEWS`, `REACH`, `PURCHASES`, `ADD_TO_CART`, `CHECKOUTS`, `APPLICATIONS`, `CONTACTS`, `LEADS`, `SEARCH`, `SIGN_UP`, `SUBSCRIBE`, `OTHER`). SD ad groups have no tags.
**Update:** `bid.defaultBid`, `name`, `optimization.goalSettings.kpi`, `state`. `creativeType` and marketplaces are immutable.

## Ad

`adType: COMPONENT`. **Create requires:** `adGroupId`, `adProduct`, `adType`, `state`, `creative.componentCreative` with one of:
- `responsiveEcommerceSettings {landingPage: MOMENT | STORE, products (1, ASIN or SKU)}`: the standard product ad.
- `productVideoSettings {landingPage, products (1)}`.
- `assetBasedCreativeSettings.landingPage {OFF_AMAZON_LINK, landingPageUrl}`.

What the update can change inside each creative is not exposed by the schema; update `state` freely, and confirm creative edits with `get_schema` before sending.

## Targets

**Create requires:** `adProduct`, `negative`, `state`, `targetType`, `targetDetails`, and `adGroupId` (or `campaignId` for campaign level). Optional `bid.bid`.

| What the user calls it | `targetType` | `targetDetails` |
|---|---|---|
| Product (ASIN) targeting | `PRODUCT` | `productTarget {product.productId, productIdType: ASIN \| SKU, matchType: PRODUCT_EXACT \| PRODUCT_SIMILAR}` |
| Category targeting | `PRODUCT_CATEGORY` | `productCategoryTarget.productCategoryRefinement.productCategoryRefinement {...}` (category, brand, price, rating, prime, age range) |
| Views / purchases remarketing | `PRODUCT_AUDIENCE` | `productAudienceTarget {asin.defaultValue, event: VIEW \| PURCHASE, lookback: DAYS_7 … DAYS_365, matchType: PRODUCT_EXACT \| PRODUCT_SIMILAR}` |
| Amazon audience | `AUDIENCE` | `audienceTarget {audienceId.defaultValue}` |
| Interest theme | `THEME` | `themeTarget.matchType: INTERESTED_AUDIENCE` |
| Content category | `CONTENT_CATEGORY` | `contentCategoryTarget` |
| Keyword | `KEYWORD` | `keywordTarget {keyword, matchType}` (`nativeLanguageLocale: en_US`) |
| Location | `LOCATION` | `locationTarget {locationId}` |

**Update:** `targetId` plus `bid.bid` and `state`.
