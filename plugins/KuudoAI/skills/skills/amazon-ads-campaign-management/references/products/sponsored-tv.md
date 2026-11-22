# Sponsored TV on v1

`adProduct`: `SPONSORED_TELEVISION` (not `SPONSORED_TV`). Product-scoped schemas: `stv1_ST*`. Read from the live server on 2026-11-19; when a field you need is not listed here, run `get_schema` on the `stv1_ST*` tool for that operation.

## Capabilities

| Entity | Query | Create | Update | Delete |
|---|---|---|---|---|
| Campaign | yes, **state filter only** | yes | yes | **no**; pause instead |
| Ad group | yes | yes | yes | **no**; pause instead |
| Ad (video) | yes | yes | creative (video), name, state | yes (archives) |
| Target | yes, no negative or type filters | yes | **state only** | yes (archives) |

## Batch and page limits

| Operation | Campaigns | Ad groups | Ads | Targets |
|---|---|---|---|---|
| Create per call | 100 | 100 | 100 | 100 |
| Update per call | **5** | 100 | 100 | 100 |
| Delete per call | n/a | n/a | 100 | 100 |
| Query `maxResults` (max) | 1000 | 100 | 100 | 100 |

## Campaign

**Create requires:** `adProduct`, `name`, `state` (`ENABLED` | `PAUSED`), `startDateTime`, `budgets` (exactly one: `MONETARY`, `DAILY`, `budgetValue.monetaryBudgetValue.monetaryBudget.value`).
Optional: `endDateTime`, `countries` and `marketplaces` (multi-valued; AU, BR, CA, DE, ES, FR, GB, IN, IT, JP, MX, SG, US).
Not available: `costType`, `optimizations`, `marketplaceScope`, `tags`, `portfolioId`.

**Query:** only `stateFilter` and paging. There is no `campaignIdFilter` or name filter, so to find one campaign, page through results and match `campaignId` or `name` client-side.

**Update:** `campaignId` plus `budgets`, `name`, `state`, `startDateTime`, `endDateTime`, `countries`, `marketplaces`. Five campaigns per call. `adProduct: SPONSORED_TELEVISION` is accepted but optional on update items; the SP, SB, SD, and DSP update contracts do not list it, so leave it off there.

## Ad group

**Create requires:** `adProduct`, `campaignId`, `name`, `state`. Optional `bid.baseBid`, `bid.defaultBid`, `marketplaces` (within the campaign's).
**Update:** `bid`, `marketplaces`, `name`, `state`.

## Ad

`adType: VIDEO`. **Create requires:** `adGroupId`, `adProduct`, `adType`, `name`, `state`, `creative.videoCreative.streamingTvSettings` with `videos {assetId, assetVersion}`; optional `landingPage` (`OFF_AMAZON_LINK` | `STORE`, `landingPageUrl`) and one product (ASIN or SKU).
**Update:** the video asset, `name`, `state`.

## Targets

**Create requires:** `adProduct`, `adGroupId`, `negative`, `state`, `targetType`, `targetDetails`. No bid field.

| `targetType` | `targetDetails` |
|---|---|
| `AUDIENCE` | `audienceTarget {audienceId.defaultValue, groupId}`. `groupId` must be a numeric string such as `"1"`; a new value starts a new group |
| `LOCATION` | `locationTarget {locationId}` |

**Update:** `state` only. **Query:** `adGroupIdFilter`, `campaignIdFilter`, `targetIdFilter`, `stateFilter`; no negative or type filters, so split client-side.
